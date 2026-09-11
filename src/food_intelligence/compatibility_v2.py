"""Interpretable, versioned multi-objective compatibility scoring."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .fusion import MultiViewFusion

@dataclass(frozen=True)
class CompatibilityConfig:
    version: str = "compat-v2.0"
    weights: tuple[tuple[str, float], ...] = (
        ("taste_complementarity", 1.0),
        ("odor_complementarity", 1.0),
        ("texture_complementarity", 1.0),
        ("process_compatibility", 1.0),
        ("culinary_cooccurrence", 1.0),
        ("chemical_similarity", 0.25),
        ("redundancy", -0.75),
        ("safety_penalty", -1.0),
    )
    min_known_components: int = 1

    def as_dict(self) -> dict[str, Any]:
        return {"version": self.version, "weights": dict(self.weights), "min_known_components": self.min_known_components}

class CompatibilityV2:
    def __init__(self, config: CompatibilityConfig | None = None):
        self.config = config or CompatibilityConfig()
        self.weights = dict(self.config.weights)

    def score(self, components: dict[str, float | None]) -> dict[str, Any]:
        normalized = dict(components)
        if "safety_penalty" not in normalized and "safety" in normalized:
            normalized["safety_penalty"] = normalized.pop("safety")
        known = {k: float(v) for k, v in normalized.items() if v is not None and k in self.weights}
        if len(known) < self.config.min_known_components:
            return {"score": None, "known_components": tuple(sorted(known)), "missing_components": tuple(k for k in self.weights if k not in known), "config_version": self.config.version}
        # Positive component scores are expected in [0,1]. Negative weights represent penalties.
        numerator = sum(self.weights[k] * max(0.0, min(1.0, v)) for k, v in known.items())
        denom = sum(abs(self.weights[k]) for k in known)
        score = max(0.0, min(1.0, (numerator / denom + 1.0) / 2.0))
        return {"score": round(score, 6), "known_components": tuple(sorted(known)), "missing_components": tuple(k for k in self.weights if k not in known), "components": normalized, "config_version": self.config.version}
