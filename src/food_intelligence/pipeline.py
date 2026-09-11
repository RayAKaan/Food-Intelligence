"""Executable end-to-end deterministic Food Intelligence pipeline.

The pipeline is deliberately data-source agnostic and can run on synthetic fixtures
or authorized snapshots. It never treats missing evidence as negative evidence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable

from .query import FoodQuery, QueryPlanner, FoodRetriever
from .graph import FoodKnowledgeGraph
from .retrieval import MultiViewIndex
from .constraints import ConstraintEngine, ConstraintSet
from .compatibility_v2 import CompatibilityV2
from .novelty import NoveltyEngine, NoveltySignals
from .pareto import pareto_frontier

@dataclass(frozen=True)
class PipelineConfig:
    version: str = "pipeline-v1.0"
    retrieval_pool: int = 100
    novelty_weight: float = .15
    compatibility_weight: float = .85

@dataclass(frozen=True)
class PipelineResult:
    query: FoodQuery
    plan: Any
    candidates: tuple[dict[str, Any], ...]
    frontier: tuple[dict[str, Any], ...]
    algorithm_version: str

class FoodIntelligencePipeline:
    def __init__(self, graph: FoodKnowledgeGraph, index: MultiViewIndex,
                 metadata: dict[str, dict[str, Any]] | None = None,
                 *, planner: QueryPlanner | None = None,
                 config: PipelineConfig | None = None):
        self.graph = graph
        self.index = index
        self.metadata = metadata or {}
        self.planner = planner or QueryPlanner()
        self.config = config or PipelineConfig()
        self.retriever = FoodRetriever(graph, index)
        self.constraints = ConstraintEngine()
        self.compatibility = CompatibilityV2()
        self.novelty = NoveltyEngine()

    def run(self, query: FoodQuery, *, query_by_view: dict[str, Any] | None = None,
            novelty_signals: dict[str, NoveltySignals] | None = None) -> PipelineResult:
        plan = self.planner.plan(query)
        raw = self.retriever.retrieve(query, query_by_view=query_by_view)
        cset = ConstraintSet(
            excluded_entities=query.excluded_entities,
            required_entities=query.required_entities,
            required_processes=query.required_processes,
            required_cuisine=query.required_cuisine,
        )
        novelty_signals = novelty_signals or {}
        scored: list[dict[str, Any]] = []
        for row in raw[:self.config.retrieval_pool]:
            eid = row["entity_id"]
            meta = self.metadata.get(eid, {})
            gate = self.constraints.check(
                eid,
                state_id=meta.get("state_id"),
                processes=set(meta.get("processes", ())),
                cuisines=set(meta.get("cuisines", ())),
                safety_status=meta.get("safety_status", "UNASSESSED"),
                constraints=cset,
            )
            if not gate.allowed:
                continue
            components = dict(meta.get("compatibility_components", {}))
            # Retrieval evidence is informative but is never silently converted to
            # a chemistry/sensory observation.
            components.setdefault("culinary_cooccurrence", meta.get("culinary_cooccurrence"))
            components.setdefault("process_compatibility", meta.get("process_compatibility"))
            components.setdefault("redundancy", meta.get("redundancy"))
            components.setdefault("safety_penalty", meta.get("safety_penalty"))
            comp = self.compatibility.score(components)
            nov = self.novelty.score(novelty_signals.get(eid, NoveltySignals()))
            if comp["score"] is None:
                final = None
            elif nov["score"] is None:
                final = self.config.compatibility_weight * comp["score"]
            else:
                final = self.config.compatibility_weight * comp["score"] + self.config.novelty_weight * nov["score"]
            scored.append({
                **row,
                "metadata": meta,
                "constraint_result": gate,
                "compatibility": comp,
                "novelty": nov,
                "score": None if final is None else round(final, 6),
                "evidence": tuple(meta.get("evidence", ())),
                "algorithm_version": self.config.version,
            })
        scored.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0), x["entity_id"]))
        scored = scored[:query.top_k]
        frontier_rows = []
        for r in scored:
            c = r["compatibility"].get("score"); n = r["novelty"].get("score")
            if c is not None and n is not None:
                frontier_rows.append({**r, "compatibility": c, "novelty": n})
        frontier = pareto_frontier(frontier_rows)
        return PipelineResult(query, plan, tuple(scored), tuple(frontier), self.config.version)
