"""Evidence-preserving multi-view food representation.

This module is deliberately dependency-light. Values are optional, modality
specific, and never imputed to zero. It supports source, synthetic, model, and
hypothetical records without treating them as interchangeable.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date
from math import sqrt
from typing import Any, Iterable

DATA_STATUSES = {"REAL", "SYNTHETIC", "MODEL_DERIVED", "HYPOTHETICAL"}
EVIDENCE_TYPES = {"FACT", "SOURCE_DERIVED", "INFERENCE", "MODEL_PREDICTION", "HYPOTHESIS", "EXPERIMENTALLY_VALIDATED"}
MODALITIES = {"SEMANTIC", "MOLECULAR", "TASTE", "ODOR", "TEXTURE", "PHYSICAL", "CULINARY", "PROCESS"}

@dataclass(frozen=True)
class Provenance:
    source_id: str
    source_name: str
    source_version: str | None
    source_record_id: str | None
    retrieval_date: str | None
    license_status: str
    processing_version: str
    mapping_version: str
    confidence: float | None
    evidence_type: str
    parent_evidence_ids: tuple[str, ...] = ()
    data_status: str = "REAL"
    evidence_id: str | None = None
    def __post_init__(self):
        if self.data_status not in DATA_STATUSES: raise ValueError(self.data_status)
        if self.evidence_type not in EVIDENCE_TYPES: raise ValueError(self.evidence_type)
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence")

@dataclass(frozen=True)
class Compound:
    compound_id: str
    canonical_name: str
    synonyms: tuple[str, ...] = ()
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    structure_identifier: str | None = None
    smiles: str | None = None
    inchi: str | None = None
    inchikey: str | None = None
    chemical_classes: tuple[str, ...] = ()
    provenance: Provenance | None = None

@dataclass(frozen=True)
class CompoundMapping:
    ingredient_id: str
    compound_id: str
    state_id: str | None
    presence: bool | None
    concentration: float | None = None
    concentration_unit: str | None = None
    concentration_basis: str | None = None
    statistic: str | None = None
    analytical_method: str | None = None
    matrix: str | None = None
    relation: str = "COMPOUND_PRESENT"
    provenance: Provenance | None = None
    def __post_init__(self):
        if self.relation not in {"COMPOUND_PRESENT", "SENSORY_RELEVANT", "CAUSALLY_ESTABLISHED"}: raise ValueError(self.relation)

@dataclass(frozen=True)
class Observation:
    descriptor: str
    value: Any = None
    scale: str | None = None
    measurement_method: str | None = None
    context: str | None = None
    observed: bool = True
    provenance: Provenance | None = None
    def __post_init__(self):
        if not self.observed and self.value is not None: raise ValueError("unobserved observation cannot carry a value")

@dataclass(frozen=True)
class SensoryProfile:
    ingredient_id: str
    state_id: str | None
    taste: tuple[Observation, ...] = ()
    odor: tuple[Observation, ...] = ()
    texture: tuple[Observation, ...] = ()
    physical: tuple[Observation, ...] = ()

@dataclass(frozen=True)
class Representation:
    entity_id: str
    representation_type: str
    model: str
    version: str
    vector: tuple[float | None, ...]
    source_features: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: date.today().isoformat())
    data_status: str = "REAL"
    provenance: Provenance | None = None
    def __post_init__(self):
        if self.representation_type not in MODALITIES: raise ValueError(self.representation_type)
        if self.data_status not in DATA_STATUSES: raise ValueError(self.data_status)

@dataclass(frozen=True)
class EvidenceConflict:
    assertion_key: str
    evidence_ids: tuple[str, ...]
    status: str
    preferred_evidence_id: str | None = None
    rationale: str | None = None
    def __post_init__(self):
        if self.status not in {"agreement", "conflict", "uncertain"}: raise ValueError(self.status)

@dataclass(frozen=True)
class Transformation:
    transformation_id: str
    input_state_id: str
    process: str
    output_state_id: str | None
    parameters: dict[str, Any]
    outputs: dict[str, Any]
    provenance: Provenance | None


def assert_no_missing_as_zero(observations: Iterable[Observation]):
    for x in observations:
        if not x.observed and x.value == 0: raise AssertionError("MISSING must not be represented as zero")
    return True

def observed_vector(observations: Iterable[Observation], vocabulary: Iterable[str]):
    by_name = {x.descriptor: x for x in observations}
    values, mask = [], []
    for name in vocabulary:
        x = by_name.get(name)
        values.append(x.value if x and x.observed and isinstance(x.value, (int, float)) else None)
        mask.append(bool(x and x.observed and x.value is not None))
    return tuple(values), tuple(mask)

def masked_cosine(a: Representation, b: Representation):
    pairs = [(x, y) for x, y in zip(a.vector, b.vector) if x is not None and y is not None]
    if not pairs: return None
    dot = sum(x*y for x, y in pairs); na = sqrt(sum(x*x for x, _ in pairs)); nb = sqrt(sum(y*y for _, y in pairs))
    return dot/(na*nb) if na and nb else 0.0

def weighted_jaccard(a: CompoundMapping, b: CompoundMapping):
    # One mapping pair is not a chemical similarity model; collection-level helper follows below.
    return 1.0 if a.compound_id == b.compound_id else 0.0

def molecular_similarity(a: Iterable[str], b: Iterable[str]):
    x, y = set(a), set(b)
    return len(x & y) / len(x | y) if x | y else None

def sensory_complementarity(a: SensoryProfile, b: SensoryProfile, target: dict[str, float]):
    def vals(profile):
        return {x.descriptor: x.value for x in profile.taste + profile.odor if x.observed and isinstance(x.value, (int, float))}
    av, bv = vals(a), vals(b)
    denom = sum(max(v, 0) for v in target.values()) or 1
    coverage = sum(min(max(av.get(k, 0), 0) + max(bv.get(k, 0), 0), max(v, 0)) for k, v in target.items())
    return min(1.0, coverage / denom)

def compatibility_components(*, chemical_similarity=None, sensory_similarity=None, sensory_complementarity_value=None, odor_similarity=None, odor_complementarity=None, culinary_cooccurrence=None, process_compatibility=None, texture_complementarity=None, redundancy=None, safety=None):
    return {"chemical_similarity": chemical_similarity, "sensory_similarity": sensory_similarity, "sensory_complementarity": sensory_complementarity_value, "odor_similarity": odor_similarity, "odor_complementarity": odor_complementarity, "culinary_cooccurrence": culinary_cooccurrence, "process_compatibility": process_compatibility, "texture_complementarity": texture_complementarity, "redundancy": redundancy, "safety": safety}

def explain_compatibility(components: dict[str, Any], evidence: list[Provenance] | None = None):
    known = {k: v for k, v in components.items() if v is not None}
    return {"components": components, "known_component_count": len(known), "evidence": [asdict(x) for x in evidence or []], "confidence": min((x.confidence for x in evidence or [] if x.confidence is not None), default=None), "claim_type": "MODEL_PREDICTION"}
