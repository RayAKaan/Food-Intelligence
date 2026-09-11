"""Structured query planning and end-to-end deterministic retrieval."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .graph import FoodKnowledgeGraph
from .representation import Representation, SensoryProfile, molecular_similarity
from .retrieval import MultiViewIndex

@dataclass(frozen=True)
class FoodQuery:
    seed_entities: tuple[str, ...] = ()
    seed_states: tuple[str, ...] = ()
    target: dict[str, float] = field(default_factory=dict)
    required_processes: frozenset[str] = frozenset()
    required_cuisine: frozenset[str] = frozenset()
    excluded_entities: frozenset[str] = frozenset()
    required_entities: frozenset[str] = frozenset()
    max_hops: int = 2
    top_k: int = 10
    novelty_weight: float = 0.15
    compatibility_weight: float = 0.85

@dataclass(frozen=True)
class QueryPlan:
    views: tuple[str, ...]
    graph_relations: frozenset[str]
    hard_filters: tuple[str, ...]

class QueryPlanner:
    def plan(self, query: FoodQuery) -> QueryPlan:
        views = ["SEMANTIC"]
        relations = {"PAIRS_WITH", "COMPLEMENTS", "SIMILAR_TO", "SUBSTITUTES_FOR"}
        if query.target: views += ["TASTE", "ODOR"]; relations |= {"HAS_TASTE", "HAS_ODOR"}
        if query.required_processes: views.append("PROCESS"); relations |= {"HAS_STATE", "USES_PROCESS", "TRANSFORMS_TO"}
        if query.required_cuisine: views.append("CULINARY"); relations |= {"USED_IN", "BELONGS_TO", "COMMON_IN"}
        if len(query.seed_entities) > 0: views.append("MOLECULAR"); relations.add("HAS_COMPOUND")
        views = tuple(dict.fromkeys(views))
        filters = ["excluded_entities", "safety"]
        if query.required_processes: filters.append("process")
        if query.required_cuisine: filters.append("cuisine")
        if query.required_entities: filters.append("required_entities")
        return QueryPlan(views, frozenset(relations), tuple(filters))

class FoodRetriever:
    def __init__(self, graph: FoodKnowledgeGraph, index: MultiViewIndex):
        self.graph, self.index = graph, index

    def candidates(self, query: FoodQuery) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for seed in query.seed_entities + query.seed_states:
            for hit in self.graph.traverse(seed, max_hops=query.max_hops):
                entity = hit["entity_id"]
                if entity in query.excluded_entities or entity in query.seed_entities: continue
                row = out.setdefault(entity, {"entity_id": entity, "paths": [], "graph_score": 0.0})
                row["paths"].append(hit["path"])
                row["graph_score"] = max(row["graph_score"], self.graph.path_score(hit["path"]))
        return out

    def retrieve(self, query: FoodQuery, query_by_view: dict[str, Representation] | None = None) -> list[dict[str, Any]]:
        rows = self.candidates(query)
        if query_by_view:
            for view, rep in query_by_view.items():
                for hit in self.index.search(view, rep, k=max(100, query.top_k * 10)):
                    entity = hit["entity_id"]
                    if entity in query.excluded_entities: continue
                    row = rows.setdefault(entity, {"entity_id": entity, "paths": [], "graph_score": 0.0})
                    row.setdefault("view_scores", {})[view] = hit["score"]
        for row in rows.values():
            vals = list(row.get("view_scores", {}).values())
            row["retrieval_score"] = (sum(vals) / len(vals) if vals else row["graph_score"])
            row["path_count"] = len(row["paths"])
        return sorted(rows.values(), key=lambda x: (-x["retrieval_score"], x["entity_id"]))[:query.top_k]
