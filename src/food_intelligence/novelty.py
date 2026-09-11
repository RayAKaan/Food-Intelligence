"""Corpus-relative novelty independent from compatibility."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class NoveltySignals:
    pair_frequency: float | None = None
    set_frequency: float | None = None
    cuisine_frequency: float | None = None
    recipe_similarity: float | None = None
    sensory_distance: float | None = None
    molecular_distance: float | None = None
    process_novelty: float | None = None

class NoveltyEngine:
    def score(self, signals: NoveltySignals) -> dict:
        vals = [v for v in (signals.pair_frequency, signals.set_frequency, signals.cuisine_frequency) if v is not None]
        if not vals:
            return {"score": None, "label": "UNKNOWN", "evidence_label": "MODEL_PREDICTION"}
        freq = min(vals)
        rarity = max(0.0, min(1.0, 1.0 - freq * 10.0))
        distances = [v for v in (signals.sensory_distance, signals.molecular_distance, signals.process_novelty) if v is not None]
        score = rarity if not distances else 0.7 * rarity + 0.3 * (sum(distances) / len(distances))
        if freq >= .01: label = "common"
        elif freq >= .001: label = "underrepresented"
        else: label = "rare_in_indexed_corpus"
        return {"score": round(score, 6), "label": label, "signals": signals.__dict__, "evidence_label": "MODEL_PREDICTION"}
