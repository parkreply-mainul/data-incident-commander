"""Deterministic downstream impact calculation."""

from __future__ import annotations

from collections import Counter

from .lineage import LineageDirection, traverse_lineage
from .models import AssetCriticality, BlastRadiusResult, LineageGraph


def calculate_blast_radius(
    graph: LineageGraph,
    root_asset_id: str,
    *,
    max_depth: int = 3,
    max_nodes: int = 100,
    include_root: bool = False,
) -> BlastRadiusResult:
    traversal = traverse_lineage(
        graph,
        root_asset_id,
        LineageDirection.DOWNSTREAM,
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
    assets = {node.node_id: node.asset for node in graph.nodes}
    affected = [node_id for node_id in traversal.node_ids if node_id != root_asset_id]
    affected = sorted(set(affected), key=lambda item: (traversal.depths.get(item, 0), item))

    direct = tuple(node_id for node_id in affected if traversal.depths.get(node_id, 0) == 1)
    transitive = tuple(node_id for node_id in affected if traversal.depths.get(node_id, 0) > 1)
    counts = Counter(assets[node_id].asset_type for node_id in affected)
    critical = tuple(
        node_id
        for node_id in affected
        if assets[node_id].criticality is AssetCriticality.CRITICAL
    )
    dashboard_models = sum(
        count for asset_type, count in counts.items() if asset_type.lower() in {"dashboard", "model"}
    )
    return BlastRadiusResult(
        root_asset_id=root_asset_id,
        included_root_asset_id=root_asset_id if include_root else None,
        directly_affected_assets=direct,
        transitively_affected_assets=transitive,
        affected_counts_by_type=dict(sorted(counts.items())),
        critical_assets_affected=critical,
        traversal_depth_reached=traversal.depth_reached,
        truncated=traversal.truncated,
        evidence_references=tuple(sorted({edge.evidence_id for edge in traversal.edges})),
        impact_summary_inputs={
            "direct_count": len(direct),
            "transitive_count": len(transitive),
            "total_count": len(affected),
            "critical_count": len(critical),
            "dashboard_model_count": dashboard_models,
            "overall_count": len(affected) + int(include_root),
            "root_included": include_root,
            "truncated": traversal.truncated,
        },
    )
