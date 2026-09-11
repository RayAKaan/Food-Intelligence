"""Typed, provenance-aware knowledge graph primitives for Food Intelligence."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any, Iterable
from .representation import Provenance

ALLOWED_RELATIONS = {
    "HAS_STATE", "HAS_COMPOUND", "HAS_TASTE", "HAS_ODOR", "HAS_TEXTURE",
    "HAS_PHYSICAL", "USED_IN", "USES_PROCESS", "TRANSFORMS_TO", "PAIRS_WITH",
    "SIMILAR_TO", "COMPLEMENTS", "SUBSTITUTES_FOR", "BELONGS_TO", "COMMON_IN",
}

@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    relation: str
    target_id: str
    confidence: float | None = None
    evidence: tuple[Provenance, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if self.relation not in ALLOWED_RELATIONS:
            raise ValueError(f"unknown relation: {self.relation}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence")

class FoodKnowledgeGraph:
    def __init__(self):
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._out = defaultdict(list)
        self._in = defaultdict(list)

    def add_node(self, node: GraphNode) -> None:
        existing = self.nodes.get(node.node_id)
        if existing and existing.node_type != node.node_type:
            raise ValueError(f"node type conflict: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise KeyError("both edge endpoints must exist")
        # Preserve distinct evidence, but collapse exact structural duplicates.
        for i, old in enumerate(self.edges):
            if (old.source_id, old.relation, old.target_id) == (edge.source_id, edge.relation, edge.target_id):
                confs = [x for x in (old.confidence, edge.confidence) if x is not None]
                best = max(confs) if confs else None
                merged_ev = tuple(dict.fromkeys((*old.evidence, *edge.evidence)))
                merged_attrs = {**old.attributes, **edge.attributes}
                merged = GraphEdge(old.source_id, old.relation, old.target_id, best, merged_ev, merged_attrs)
                self.edges[i] = merged
                self._out[old.source_id] = [e for e in self._out[old.source_id] if e is not old]
                self._in[old.target_id] = [e for e in self._in[old.target_id] if e is not old]
                self._out[merged.source_id].append(merged); self._in[merged.target_id].append(merged)
                return
        self.edges.append(edge); self._out[edge.source_id].append(edge); self._in[edge.target_id].append(edge)

    def neighbors(self, node_id: str, *, relation: str | None = None, direction: str = "out") -> list[GraphEdge]:
        if direction not in {"out", "in"}: raise ValueError(direction)
        edges = self._out[node_id] if direction == "out" else self._in[node_id]
        return [e for e in edges if relation is None or e.relation == relation]

    def traverse(self, start_id: str, *, max_hops: int = 2, relations: set[str] | None = None) -> list[dict[str, Any]]:
        if start_id not in self.nodes: return []
        seen = {start_id}; frontier = [(start_id, 0, ())]; results = []
        while frontier:
            current, depth, path = frontier.pop(0)
            if depth >= max_hops: continue
            for edge in self.neighbors(current):
                if relations and edge.relation not in relations: continue
                nxt = edge.target_id
                edge_path = (*path, edge)
                results.append({"entity_id": nxt, "depth": depth + 1, "path": edge_path})
                if nxt not in seen:
                    seen.add(nxt); frontier.append((nxt, depth + 1, edge_path))
        return results

    def path_score(self, path: Iterable[GraphEdge]) -> float:
        vals = [e.confidence for e in path if e.confidence is not None]
        if not vals: return 0.0
        score = 1.0
        for v in vals: score *= v
        return score ** (1 / len(vals))
