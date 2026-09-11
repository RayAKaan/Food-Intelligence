"""State/process transformation primitives.

Transformations are executable *records*, not claims that cooking causes a
particular sensory or chemical change. Unknown parameters and outputs remain
unknown until supported by evidence or experiments.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable
from .representation import Provenance

PROCESS_VOCABULARY = frozenset({
    "boil", "simmer", "steam", "poach", "blanch", "roast", "toast", "bake",
    "grill", "fry", "deep_fry", "shallow_fry", "saute", "temper", "reduce",
    "caramelize", "brown", "ferment", "pickle", "grind", "blend", "emulsify",
    "whip", "knead", "rest", "marinate", "cure", "dehydrate", "smoke",
})

PARAMETER_KEYS = frozenset({
    "temperature", "duration", "medium", "water", "fat", "oxygen", "pH",
    "pressure", "agitation", "particle_size", "humidity", "salt",
})

@dataclass(frozen=True)
class ProcessSpec:
    process_id: str
    name: str
    family: str
    requires: tuple[str, ...] = ()
    optional_parameters: tuple[str, ...] = tuple(sorted(PARAMETER_KEYS))

@dataclass(frozen=True)
class TransformationRecord:
    transformation_id: str
    ingredient_id: str
    input_state_id: str
    process_id: str
    output_state_id: str | None
    parameters: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[Provenance, ...] = ()
    status: str = "HYPOTHESIS"

    def __post_init__(self):
        if self.status not in {"HYPOTHESIS", "SOURCE_DERIVED", "EXPERIMENTALLY_VALIDATED", "MODEL_PREDICTION"}:
            raise ValueError(self.status)

@dataclass(frozen=True)
class TransformationValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    claim_status: str


def normalize_process(value: str) -> str:
    return value.casefold().strip().replace(" ", "_").replace("-", "_")


def validate_transformation(t: TransformationRecord, process_catalog: dict[str, ProcessSpec] | None = None) -> TransformationValidation:
    catalog = process_catalog or default_process_catalog()
    errors: list[str] = []
    warnings: list[str] = []
    process = normalize_process(t.process_id)
    if process not in catalog:
        errors.append(f"unknown_process:{t.process_id}")
    for key in t.parameters:
        if key not in PARAMETER_KEYS:
            errors.append(f"unknown_parameter:{key}")
    if not t.input_state_id:
        errors.append("missing_input_state")
    if not t.ingredient_id:
        errors.append("missing_ingredient")
    if t.output_state_id is None:
        warnings.append("output_state_unknown")
    if not t.evidence:
        warnings.append("no_evidence")
    if t.status in {"SOURCE_DERIVED", "EXPERIMENTALLY_VALIDATED"} and not t.evidence:
        errors.append("evidence_required_for_asserted_transformation")
    if t.status == "EXPERIMENTALLY_VALIDATED" and not any(p.evidence_type == "EXPERIMENTALLY_VALIDATED" for p in t.evidence):
        errors.append("experimental_status_without_experimental_evidence")
    return TransformationValidation(not errors, tuple(errors), tuple(warnings), t.status)


def instantiate(ingredient_id: str, input_state_id: str, process_id: str, *, output_state_id: str | None = None,
                parameters: dict[str, Any] | None = None, outputs: dict[str, Any] | None = None,
                evidence: Iterable[Provenance] = (), status: str = "HYPOTHESIS", transformation_id: str | None = None) -> TransformationRecord:
    pid = normalize_process(process_id)
    t = TransformationRecord(transformation_id or f"{ingredient_id}:{input_state_id}:{pid}", ingredient_id,
                             input_state_id, pid, output_state_id, parameters or {}, outputs or {}, tuple(evidence), status)
    result = validate_transformation(t)
    if not result.valid:
        raise ValueError("invalid transformation: " + ", ".join(result.errors))
    return t


def default_process_catalog() -> dict[str, ProcessSpec]:
    families = {
        "boil":"aqueous_heat", "simmer":"aqueous_heat", "steam":"aqueous_heat", "poach":"aqueous_heat", "blanch":"aqueous_heat",
        "roast":"dry_heat", "toast":"dry_heat", "bake":"dry_heat", "grill":"dry_heat", "fry":"fat_heat",
        "deep_fry":"fat_heat", "shallow_fry":"fat_heat", "saute":"fat_heat", "temper":"fat_heat", "reduce":"concentration",
        "caramelize":"browning", "brown":"browning", "ferment":"biological", "pickle":"acid_salt", "grind":"mechanical",
        "blend":"mechanical", "emulsify":"mechanical", "whip":"mechanical", "knead":"mechanical", "rest":"holding",
        "marinate":"diffusion", "cure":"salt_sugar", "dehydrate":"water_removal", "smoke":"smoke_heat",
    }
    return {name: ProcessSpec(name, name, family) for name, family in families.items()}


def transition_template(ingredient_id: str, input_state_id: str, process_id: str, output_state_id: str | None = None) -> dict[str, Any]:
    """Return a safe process template with unknown scientific outputs."""
    t = instantiate(ingredient_id, input_state_id, process_id, output_state_id=output_state_id)
    return {**asdict(t), "validation": asdict(validate_transformation(t))}
