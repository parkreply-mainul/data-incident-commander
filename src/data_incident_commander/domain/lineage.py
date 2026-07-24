"""Cycle-safe deterministic lineage traversal."""

from __future__ import annotations

from collections import deque
from enum import Enum
from typing import Mapping

from pydantic import Field, field_serializer, field_validator

from .base import StrictModel, freeze_mapping, thaw_mapping
from .models import LineageEdge, LineageGraph


class LineageDirection(str, Enum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"


class TraversalResult(StrictModel):
    root_id: str
    direction: LineageDirection
    node_ids: tuple[str, ...]
    edges: tuple[LineageEdge, ...]
    paths: Mapping[str, tuple[str, ...]]
    depths: Mapping[str, int]
    depth_reached: int = Field(ge=0)
    truncated: bool

    @field_validator("paths", "depths")
    @classmethod
    def mappings_are_immutable(cls, value: Mapping[str, object]) -> Mapping[str, object]:
        return freeze_mapping(value)

    @field_serializer("paths", "depths")
    def serialize_mappings(self, value: Mapping[str, object]) -> dict[str, object]:
        return thaw_mapping(value)


def traverse_lineage(
    graph: LineageGraph,
    root_id: str,
    direction: LineageDirection,
    *,
    max_depth: int = 3,
    max_nodes: int = 100,
) -> TraversalResult:
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    if max_nodes < 1:
        raise ValueError("max_nodes must be at least one")
    node_ids = {node.node_id for node in graph.nodes}
    if root_id not in node_ids:
        raise ValueError(f"unknown root node: {root_id}")

    adjacency: dict[str, list[tuple[str, LineageEdge]]] = {node_id: [] for node_id in node_ids}
    for edge in graph.edges:
        if direction is LineageDirection.DOWNSTREAM:
            adjacency[edge.upstream_id].append((edge.downstream_id, edge))
        else:
            adjacency[edge.downstream_id].append((edge.upstream_id, edge))
    for neighbors in adjacency.values():
        neighbors.sort(key=lambda item: (item[0], item[1].identity))

    visited = {root_id}
    paths = {root_id: (root_id,)}
    depths = {root_id: 0}
    selected_edges: dict[tuple[str, str], LineageEdge] = {}
    queue: deque[str] = deque([root_id])
    truncated = False

    while queue:
        current = queue.popleft()
        current_depth = depths[current]
        neighbors = adjacency[current]
        if current_depth >= max_depth:
            if any(neighbor not in visited for neighbor, _ in neighbors):
                truncated = True
            continue
        for neighbor, edge in neighbors:
            if neighbor in visited:
                continue
            if len(visited) >= max_nodes:
                truncated = True
                continue
            visited.add(neighbor)
            depths[neighbor] = current_depth + 1
            paths[neighbor] = paths[current] + (neighbor,)
            selected_edges[edge.identity] = edge
            queue.append(neighbor)

    ordered_nodes = tuple(sorted(visited, key=lambda node: (depths[node], node)))
    ordered_paths = {node: paths[node] for node in ordered_nodes}
    ordered_depths = {node: depths[node] for node in ordered_nodes}
    return TraversalResult(
        root_id=root_id,
        direction=direction,
        node_ids=ordered_nodes,
        edges=tuple(selected_edges[key] for key in sorted(selected_edges)),
        paths=ordered_paths,
        depths=ordered_depths,
        depth_reached=max(depths.values(), default=0),
        truncated=truncated,
    )
