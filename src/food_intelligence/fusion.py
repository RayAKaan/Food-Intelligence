"""Explicit multi-view fusion; missing modalities remain missing."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FusionResult:
    score: float | None
    known_views: tuple[str, ...]
    missing_views: tuple[str, ...]
    per_view: dict[str, float]

class MultiViewFusion:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or {}

    def fuse(self, scores: dict[str, float | None]) -> FusionResult:
        known = {k: float(v) for k, v in scores.items() if v is not None}
        missing = tuple(k for k, v in scores.items() if v is None)
        if not known: return FusionResult(None, (), missing, {})
        weighted = sum(known[k] * self.weights.get(k, 1.0) for k in known)
        denom = sum(self.weights.get(k, 1.0) for k in known)
        return FusionResult(weighted / denom if denom else None, tuple(known), missing, known)
