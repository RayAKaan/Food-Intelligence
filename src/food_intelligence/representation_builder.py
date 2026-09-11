"""Build explicit multi-view representations without fabricating missing data."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable
from .representation import Observation, Representation, Provenance, observed_vector

@dataclass(frozen=True)
class ViewSpec:
    representation_type: str
    vocabulary: tuple[str, ...]
    model: str = "explicit_features"
    version: str = "1"

DEFAULT_VIEWS = {
    "TASTE": ViewSpec("TASTE", ("sweet", "sour", "salty", "bitter", "umami", "pungent")),
    "ODOR": ViewSpec("ODOR", ("fruity", "floral", "herbal", "earthy", "roasted", "smoky", "sulfurous", "spicy", "citrus", "nutty", "camphoraceous", "caramelized")),
    "TEXTURE": ViewSpec("TEXTURE", ("hardness", "crispness", "chewiness", "viscosity", "fibrousness", "creaminess")),
    "PHYSICAL": ViewSpec("PHYSICAL", ("moisture", "density", "particle_size", "water_activity", "melting_point")),
}


def build_explicit_representation(entity_id: str, representation_type: str, observations: Iterable[Observation],
                                  *, provenance: Provenance | None = None, view_specs=None) -> tuple[Representation, tuple[bool, ...]]:
    specs = view_specs or DEFAULT_VIEWS
    if representation_type not in specs:
        raise ValueError(f"no explicit vocabulary for {representation_type}")
    spec = specs[representation_type]
    values, mask = observed_vector(observations, spec.vocabulary)
    rep = Representation(entity_id, representation_type, spec.model, spec.version, values,
                         source_features={"vocabulary": spec.vocabulary, "observed_mask": mask},
                         data_status=(provenance.data_status if provenance else "REAL"), provenance=provenance)
    return rep, mask


def semantic_representation(entity_id: str, *, names: Iterable[str], roles: Iterable[str] = (),
                            provenance: Provenance | None = None) -> Representation:
    features = tuple(sorted({x.casefold().strip() for x in (*names, *roles) if x and x.strip()}))
    return Representation(entity_id, "SEMANTIC", "token_set", "1", tuple(),
                          source_features={"tokens": features},
                          data_status=(provenance.data_status if provenance else "REAL"), provenance=provenance)


def molecular_representation(entity_id: str, compound_ids: Iterable[str], weights: dict[str, float] | None = None,
                              provenance: Provenance | None = None) -> Representation:
    weights = weights or {}
    compounds = tuple(sorted(set(compound_ids)))
    return Representation(entity_id, "MOLECULAR", "compound_weight_map", "1", tuple(),
                          source_features={"compounds": compounds, "weights": {k: weights[k] for k in compounds if k in weights}},
                          data_status=(provenance.data_status if provenance else "REAL"), provenance=provenance)
