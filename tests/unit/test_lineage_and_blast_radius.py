from __future__ import annotations

import json

import pytest

from data_incident_commander.domain.base import canonical_json
from data_incident_commander.domain.blast_radius import calculate_blast_radius
from data_incident_commander.domain.lineage import LineageDirection, traverse_lineage
from data_incident_commander.domain.models import AssetCriticality, LineageEdge, LineageGraph


def _graph(node_factory):
    nodes = [
        node_factory("a"),
        node_factory("b", "dataset"),
        node_factory("c", "dashboard", AssetCriticality.CRITICAL),
        node_factory("d", "model"),
        node_factory("e", "dashboard"),
    ]
    edges = [
        LineageEdge(upstream_id="a", downstream_id="b", evidence_id="e-ab"),
        LineageEdge(upstream_id="b", downstream_id="c", evidence_id="e-bc"),
        LineageEdge(upstream_id="c", downstream_id="a", evidence_id="e-ca"),
        LineageEdge(upstream_id="a", downstream_id="d", evidence_id="e-ad"),
        LineageEdge(upstream_id="d", downstream_id="e", evidence_id="e-de"),
    ]
    return LineageGraph.create(nodes, edges)


def test_graph_deduplicates_edges_and_orders_deterministically(node_factory):
    node_a = node_factory("a")
    nodes = [node_factory("b"), node_a, node_a]
    duplicate = LineageEdge(upstream_id="a", downstream_id="b", evidence_id="first")
    graph = LineageGraph.create(nodes, [duplicate, duplicate])
    assert tuple(node.node_id for node in graph.nodes) == ("a", "b")
    assert graph.edges == (duplicate,)


def test_graph_rejects_conflicting_duplicate_nodes(node_factory):
    with pytest.raises(ValueError, match="conflicting duplicate lineage node"):
        LineageGraph.create(
            [
                node_factory("a", display_name="First"),
                node_factory("a", display_name="Different"),
            ],
            [],
        )


def test_graph_rejects_conflicting_duplicate_edges(node_factory):
    with pytest.raises(ValueError, match="conflicting duplicate lineage edge"):
        LineageGraph.create(
            [node_factory("a"), node_factory("b")],
            [
                LineageEdge(upstream_id="a", downstream_id="b", evidence_id="first"),
                LineageEdge(upstream_id="a", downstream_id="b", evidence_id="different"),
            ],
        )


def test_reordered_equivalent_graph_has_identical_content_and_serialization(node_factory):
    nodes = [node_factory("c"), node_factory("a"), node_factory("b")]
    edges = [
        LineageEdge(upstream_id="b", downstream_id="c", evidence_id="bc"),
        LineageEdge(upstream_id="a", downstream_id="b", evidence_id="ab"),
    ]
    forward = LineageGraph.create(nodes, edges)
    reordered = LineageGraph.create(
        list(reversed(nodes)) + [nodes[0]],
        list(reversed(edges)) + [edges[0]],
    )
    assert forward == reordered
    assert canonical_json(forward) == canonical_json(reordered)


def test_cycle_safe_downstream_traversal(node_factory):
    result = traverse_lineage(_graph(node_factory), "a", LineageDirection.DOWNSTREAM, max_depth=10)
    assert set(result.node_ids) == {"a", "b", "c", "d", "e"}
    assert len(result.node_ids) == 5


def test_depth_limit_marks_truncation(node_factory):
    result = traverse_lineage(_graph(node_factory), "a", LineageDirection.DOWNSTREAM, max_depth=1)
    assert result.node_ids == ("a", "b", "d")
    assert result.truncated is True
    assert result.depth_reached == 1


def test_node_limit_marks_truncation(node_factory):
    result = traverse_lineage(
        _graph(node_factory),
        "a",
        LineageDirection.DOWNSTREAM,
        max_depth=10,
        max_nodes=2,
    )
    assert result.node_ids == ("a", "b")
    assert result.truncated is True


def test_upstream_direction_and_path_reconstruction(node_factory):
    result = traverse_lineage(_graph(node_factory), "e", LineageDirection.UPSTREAM, max_depth=5)
    assert result.paths["a"] == ("e", "d", "a")
    assert result.paths["c"] == ("e", "d", "a", "c")


def test_traversal_mappings_are_immutable_consistent_and_stably_serialized(node_factory):
    result = traverse_lineage(_graph(node_factory), "a", LineageDirection.DOWNSTREAM, max_depth=10)
    with pytest.raises(TypeError):
        result.paths["b"] = ("changed",)
    with pytest.raises(TypeError):
        result.depths["b"] = 99
    assert set(result.paths) == set(result.node_ids)
    assert set(result.depths) == set(result.node_ids)
    assert result.depth_reached == max(result.depths.values())
    serialized = json.loads(canonical_json(result))
    assert serialized["paths"]["b"] == ["a", "b"]
    assert serialized["depths"]["b"] == 1


def test_duplicate_paths_choose_deterministic_shortest_path(node_factory):
    graph = LineageGraph.create(
        [node_factory(item) for item in ("a", "b", "c", "d")],
        [
            LineageEdge(upstream_id="a", downstream_id="b", evidence_id="ab"),
            LineageEdge(upstream_id="a", downstream_id="c", evidence_id="ac"),
            LineageEdge(upstream_id="b", downstream_id="d", evidence_id="bd"),
            LineageEdge(upstream_id="c", downstream_id="d", evidence_id="cd"),
        ],
    )
    result = traverse_lineage(graph, "a", LineageDirection.DOWNSTREAM)
    assert result.paths["d"] == ("a", "b", "d")


def test_blast_radius_separates_direct_and_transitive_and_counts_unique(node_factory):
    result = calculate_blast_radius(_graph(node_factory), "a", max_depth=10)
    assert result.directly_affected_assets == ("b", "d")
    assert result.transitively_affected_assets == ("c", "e")
    assert result.total_affected == 4
    assert result.affected_counts_by_type == {"dashboard": 2, "dataset": 1, "model": 1}
    assert result.critical_assets_affected == ("c",)
    assert "a" not in result.directly_affected_assets + result.transitively_affected_assets


def test_blast_radius_can_explicitly_include_root(node_factory):
    result = calculate_blast_radius(_graph(node_factory), "a", include_root=True, max_depth=10)
    assert result.included_root_asset_id == "a"
    assert result.overall_asset_ids == ("a", "b", "d", "c", "e")
    assert "a" not in result.directly_affected_assets
    assert "a" not in result.transitively_affected_assets
    assert result.directly_affected_assets == ("b", "d")
    assert result.transitively_affected_assets == ("c", "e")
    assert result.total_affected == 4
    assert result.overall_asset_count == 5
    assert result.impact_summary_inputs["direct_count"] == 2
    assert result.impact_summary_inputs["transitive_count"] == 2
    assert result.impact_summary_inputs["total_count"] == 4
    assert result.impact_summary_inputs["overall_count"] == 5
    assert result.impact_summary_inputs["root_included"] is True


def test_blast_radius_excludes_root_by_default(node_factory):
    result = calculate_blast_radius(_graph(node_factory), "a", max_depth=10)
    assert result.included_root_asset_id is None
    assert result.overall_asset_ids == ("b", "d", "c", "e")
    assert result.total_affected == 4
    assert result.overall_asset_count == 4
    assert result.impact_summary_inputs["overall_count"] == 4
    assert result.impact_summary_inputs["root_included"] is False


def test_blast_radius_reports_truncation_and_evidence(node_factory):
    result = calculate_blast_radius(_graph(node_factory), "a", max_depth=1)
    assert result.truncated is True
    assert result.traversal_depth_reached == 1
    assert result.evidence_references == ("e-ab", "e-ad")


def test_blast_radius_mappings_are_immutable_and_serialize_as_objects(node_factory):
    result = calculate_blast_radius(_graph(node_factory), "a", max_depth=10)
    with pytest.raises(TypeError):
        result.affected_counts_by_type["dataset"] = 99
    with pytest.raises(TypeError):
        result.impact_summary_inputs["total_count"] = 99
    serialized = json.loads(canonical_json(result))
    assert serialized["affected_counts_by_type"] == {
        "dashboard": 2,
        "dataset": 1,
        "model": 1,
    }
    assert serialized["impact_summary_inputs"]["total_count"] == 4
