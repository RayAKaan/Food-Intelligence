"""End-to-end deterministic query reasoning substrate for Phase 1E."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .compatibility_v2 import CompatibilityV2
from .constraints import ConstraintEngine, ConstraintSet
from .novelty import NoveltyEngine, NoveltySignals
from .pareto import pareto_frontier

@dataclass(frozen=True)
class ReasoningConfig:
    compatibility_weight: float = .85
    novelty_weight: float = .15
    version: str = "reasoning-v1.0"

class FoodReasoner:
    def __init__(self, *, compatibility: CompatibilityV2 | None = None,
                 novelty: NoveltyEngine | None = None,
                 constraints: ConstraintEngine | None = None,
                 config: ReasoningConfig | None = None):
        self.compatibility = compatibility or CompatibilityV2()
        self.novelty = novelty or NoveltyEngine()
        self.constraints = constraints or ConstraintEngine()
        self.config = config or ReasoningConfig()

    def evaluate(self, candidate: dict[str, Any], *, constraints: ConstraintSet | None = None,
                 pair_frequency: float | None = None, set_frequency: float | None = None,
                 cuisine_frequency: float | None = None, recipe_similarity: float | None = None,
                 sensory_distance: float | None = None, molecular_distance: float | None = None,
                 process_novelty: float | None = None) -> dict[str, Any] | None:
        gate = self.constraints.check(candidate["entity_id"], state_id=candidate.get("state_id"),
            processes=set(candidate.get("processes", ())), cuisines=set(candidate.get("cuisines", ())),
            safety_status=candidate.get("safety_status", "UNASSESSED"), constraints=constraints)
        if not gate.allowed: return None
        comp = self.compatibility.score(candidate.get("components", {}))
        nov = self.novelty.score(NoveltySignals(pair_frequency, set_frequency, cuisine_frequency,
                                                recipe_similarity, sensory_distance, molecular_distance,
                                                process_novelty))
        if comp["score"] is None: final = None
        elif nov["score"] is None: final = self.config.compatibility_weight * comp["score"]
        else: final = self.config.compatibility_weight * comp["score"] + self.config.novelty_weight * nov["score"]
        return {"entity_id": candidate["entity_id"], "state_id": candidate.get("state_id"),
                "compatibility": comp, "novelty": nov, "score": None if final is None else round(final, 6),
                "constraint_result": gate, "algorithm_version": self.config.version}

    def rank(self, candidates: list[dict[str, Any]], **kwargs) -> list[dict[str, Any]]:
        rows = [r for c in candidates if (r := self.evaluate(c, **kwargs)) is not None]
        return sorted(rows, key=lambda r: (r["score"] is None, -(r["score"] or 0), r["entity_id"]))

    def frontier(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        usable = []
        for r in rows:
            c = r["compatibility"].get("score")
            n = r["novelty"].get("score")
            if c is not None and n is not None:
                usable.append({**r, "compatibility": c, "novelty": n})
        return pareto_frontier(usable)
