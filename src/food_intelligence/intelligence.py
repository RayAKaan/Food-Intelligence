"""Unified deterministic food-intelligence pipeline.

This module composes state, sensory, molecular, culinary/process and novelty
signals without turning any missing signal into a zero or a positive claim.
It is intentionally deterministic and evidence-aware; it does not generate
scientific facts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from math import log1p
from typing import Any, Iterable

from .representation import (
    Observation, Provenance, SensoryProfile, Representation,
    molecular_similarity, sensory_complementarity,
    compatibility_components, explain_compatibility,
)
from .retrieval import MultiViewIndex
from .transformations import default_process_catalog


@dataclass(frozen=True)
class Candidate:
    entity_id: str
    state_id: str | None
    taste: SensoryProfile
    odor: SensoryProfile
    compounds: tuple[str, ...] = ()
    semantic: Representation | None = None
    molecular: Representation | None = None
    culinary_roles: frozenset[str] = frozenset()
    processes: frozenset[str] = frozenset()
    safety_status: str = "UNASSESSED"
    evidence: tuple[Provenance, ...] = ()


@dataclass(frozen=True)
class CandidateRequest:
    target: dict[str, float] = field(default_factory=dict)
    required_processes: frozenset[str] = frozenset()
    excluded_entities: frozenset[str] = frozenset()
    max_results: int = 10
    novelty_weight: float = 0.15
    compatibility_weight: float = 0.85


class FoodIntelligenceEngine:
    """Compose representations into a reproducible ranking pipeline."""

    def __init__(self, candidates: Iterable[Candidate] = ()):
        self.candidates = {c.entity_id: c for c in candidates}
        self.index = MultiViewIndex()
        for candidate in self.candidates.values():
            for rep in (candidate.semantic, candidate.molecular):
                if rep is not None:
                    self.index.add(rep)

    def _safety_gate(self, candidate: Candidate) -> tuple[bool, str]:
        if candidate.safety_status.upper() in {"BLOCKED", "CONTRAINDICATED"}:
            return False, "HARD_SAFETY_BLOCK"
        return True, candidate.safety_status.upper()

    @staticmethod
    def _process_score(candidate: Candidate, required: frozenset[str]) -> float | None:
        if not required:
            return None
        known = {p for p in candidate.processes if p in default_process_catalog()}
        return len(known & set(required)) / len(required)

    @staticmethod
    def _novelty(pair_count: int, corpus_size: int) -> dict[str, Any]:
        if corpus_size <= 0:
            return {"score": None, "label": "UNKNOWN", "reason": "no indexed corpus"}
        freq = pair_count / corpus_size
        score = max(0.0, min(1.0, 1.0 - freq * 10.0))
        if freq >= .01:
            label = "common"
        elif freq >= .001:
            label = "underrepresented"
        else:
            label = "rare_in_indexed_corpus"
        return {"score": round(score, 4), "label": label, "frequency": freq}

    def rank(self, request: CandidateRequest, *, corpus_size: int = 0,
             pair_counts: dict[str, int] | None = None) -> list[dict[str, Any]]:
        pair_counts = pair_counts or {}
        rows: list[dict[str, Any]] = []
        for candidate in self.candidates.values():
            if candidate.entity_id in request.excluded_entities:
                continue
            allowed, safety = self._safety_gate(candidate)
            if not allowed:
                continue

            sensory = sensory_complementarity(candidate.taste, candidate.odor, request.target)
            odor_values = {
                o.descriptor: o.value for o in candidate.odor.odor
                if o.observed and isinstance(o.value, (int, float))
            }
            target_total = sum(max(v, 0.0) for v in request.target.values()) or 1.0
            odor_cover = sum(min(max(odor_values.get(k, 0.0), 0.0), max(v, 0.0))
                             for k, v in request.target.items()) / target_total
            process = self._process_score(candidate, request.required_processes)
            molecular = None
            if candidate.compounds:
                # Candidate self-similarity is deliberately not used as a score;
                # molecular overlap belongs in pairwise ranking when a query entity exists.
                molecular = {"compound_count": len(candidate.compounds)}

            novelty = self._novelty(pair_counts.get(candidate.entity_id, 0), corpus_size)
            compat_known = [sensory, odor_cover]
            if process is not None:
                compat_known.append(process)
            compatibility_score = sum(compat_known) / len(compat_known)
            novelty_score = novelty["score"]
            if novelty_score is None:
                final = request.compatibility_weight * compatibility_score
            else:
                final = (request.compatibility_weight * compatibility_score +
                         request.novelty_weight * novelty_score)

            components = compatibility_components(
                sensory_complementarity_value=sensory,
                odor_complementarity=odor_cover,
                process_compatibility=process,
                chemical_similarity=None,
                culinary_cooccurrence=None,
                texture_complementarity=None,
                redundancy=None,
                safety=None if safety == "UNASSESSED" else safety,
            )
            rows.append({
                "entity_id": candidate.entity_id,
                "state_id": candidate.state_id,
                "score": round(final, 6),
                "compatibility": explain_compatibility(components, list(candidate.evidence)),
                "novelty": novelty,
                "safety": safety,
                "molecular_context": molecular,
                "claim_status": "MODEL_PREDICTION",
            })
        return sorted(rows, key=lambda r: (-r["score"], r["entity_id"]))[:request.max_results]


def profile_from_row(row: dict[str, Any], provenance: Provenance) -> SensoryProfile:
    taste = tuple(Observation(k, v, "fixture_0_1", "constructed", "fixture", True, provenance)
                  for k, v in row.get("taste", {}).items())
    odor = tuple(Observation(k, v, "fixture_0_1", "constructed", "fixture", True, provenance)
                 for k, v in row.get("odor", {}).items())
    texture = tuple(Observation(k, v, "fixture_0_1", "constructed", "fixture", True, provenance)
                   for k, v in row.get("texture", {}).items())
    return SensoryProfile(row["id"], row.get("state"), taste=taste, odor=odor, texture=texture)
