"""Canonical contracts for an executable Computational Food World.

These records describe states and experiments; they do not simulate behavior.
Unknown values remain unknown, and predictions remain distinct from observations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping

CONTRACTS_VERSION = "1.0"


class EvidenceClass(str, Enum):
    MEASURED = "MEASURED"
    SOURCE_DERIVED = "SOURCE_DERIVED"
    SIMULATED = "SIMULATED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"


class ExperimentStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ObservationStatus(str, Enum):
    OBSERVED = "OBSERVED"
    NOT_MEASURED = "NOT_MEASURED"
    CENSORED = "CENSORED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class UncertaintyEstimate:
    """An uncertainty estimate with its method explicitly identified."""
    method: str
    standard_deviation: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    confidence_level: float | None = None
    sample_size: int | None = None

    def __post_init__(self) -> None:
        if not self.method.strip():
            raise ValueError("uncertainty method must be non-empty")
        for name in ("standard_deviation", "lower_bound", "upper_bound"):
            value = getattr(self, name)
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite when supplied")
        if self.standard_deviation is not None and self.standard_deviation < 0:
            raise ValueError("standard_deviation cannot be negative")
        if self.lower_bound is not None and self.upper_bound is not None:
            if self.lower_bound > self.upper_bound:
                raise ValueError("lower_bound cannot exceed upper_bound")
        if self.confidence_level is not None and not 0 < self.confidence_level < 1:
            raise ValueError("confidence_level must be between 0 and 1")
        if self.sample_size is not None and self.sample_size < 1:
            raise ValueError("sample_size must be positive")


@dataclass(frozen=True)
class Quantity:
    """A unit-bearing value; value=None means unknown, never zero."""
    value: float | None
    unit: str
    uncertainty: UncertaintyEstimate | None = None

    def __post_init__(self) -> None:
        if not self.unit.strip():
            raise ValueError("quantity unit must be non-empty")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError("quantity value must be finite when supplied")

    @property
    def is_known(self) -> bool:
        return self.value is not None


@dataclass(frozen=True)
class WorldComponent:
    """A material component in a particular ingredient state."""
    component_id: str
    ingredient_id: str
    ingredient_state_id: str
    amount: Quantity
    attributes: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name in ("component_id", "ingredient_id", "ingredient_state_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.amount.value is not None and self.amount.value < 0:
            raise ValueError("component amount cannot be negative")
        object.__setattr__(self, "attributes", dict(self.attributes or {}))


@dataclass(frozen=True)
class WorldState:
    """Versioned snapshot of a simulated food system at a point in time."""
    state_id: str
    components: tuple[WorldComponent, ...]
    conditions: Mapping[str, Quantity]
    schema_version: str = CONTRACTS_VERSION
    parent_state_id: str | None = None

    def __post_init__(self) -> None:
        if not self.state_id.strip() or not self.schema_version.strip():
            raise ValueError("state_id and schema_version must be non-empty")
        ids = [item.component_id for item in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("component_id values must be unique within a world state")
        if any(not key.strip() for key in self.conditions):
            raise ValueError("condition names must be non-empty")
        object.__setattr__(self, "conditions", dict(self.conditions))


@dataclass(frozen=True)
class Intervention:
    """A proposed state change, not a claim about its outcome."""
    intervention_id: str
    operation: str
    target_component_ids: tuple[str, ...]
    parameters: Mapping[str, Any]
    preconditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.intervention_id.strip() or not self.operation.strip():
            raise ValueError("intervention_id and operation must be non-empty")
        if not self.target_component_ids or any(not x.strip() for x in self.target_component_ids):
            raise ValueError("an intervention must target non-empty component IDs")
        if len(set(self.target_component_ids)) != len(self.target_component_ids):
            raise ValueError("target component IDs must be unique")
        if any(not key.strip() for key in self.parameters):
            raise ValueError("parameter names must be non-empty")
        object.__setattr__(self, "parameters", dict(self.parameters))


@dataclass(frozen=True)
class ExperimentProtocol:
    """Versioned plan for a controlled, reproducible experiment."""
    protocol_id: str
    name: str
    version: str
    interventions: tuple[Intervention, ...]
    control_variables: tuple[str, ...] = ()
    repetitions: int = 1
    notes: str | None = None

    def __post_init__(self) -> None:
        for name in ("protocol_id", "name", "version"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.repetitions < 1:
            raise ValueError("repetitions must be positive")
        ids = [item.intervention_id for item in self.interventions]
        if len(ids) != len(set(ids)):
            raise ValueError("intervention IDs must be unique within a protocol")
        if any(not x.strip() for x in self.control_variables):
            raise ValueError("control variable names must be non-empty")


@dataclass(frozen=True)
class Hypothesis:
    """A falsifiable claim to investigate, not an established fact."""
    hypothesis_id: str
    statement: str
    target_variable: str
    expected_direction: str
    falsification_criterion: str
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("hypothesis_id", "statement", "target_variable", "falsification_criterion"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.expected_direction not in {"increase", "decrease", "no_change", "unknown"}:
            raise ValueError("expected_direction must be increase, decrease, no_change, or unknown")


@dataclass(frozen=True)
class Prediction:
    """A model's expected outcome, explicitly separate from an observation."""
    prediction_id: str
    variable: str
    value: Any
    unit: str | None
    model_id: str
    model_version: str
    uncertainty: UncertaintyEstimate | None = None
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("prediction_id", "variable", "model_id", "model_version"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("prediction value must be finite when numeric")
        if self.unit is not None and not self.unit.strip():
            raise ValueError("unit must be non-empty when supplied")


@dataclass(frozen=True)
class ExperimentalObservation:
    """Outcome returned by a measurement or simulation procedure."""
    observation_id: str
    variable: str
    value: Any
    unit: str | None
    status: ObservationStatus
    evidence_class: EvidenceClass
    method: str
    source_record_id: str | None = None
    uncertainty: UncertaintyEstimate | None = None
    conditions: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ObservationStatus):
            raise TypeError("status must be an ObservationStatus")
        if not isinstance(self.evidence_class, EvidenceClass):
            raise TypeError("evidence_class must be an EvidenceClass")
        for name in ("observation_id", "variable", "method"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.status is not ObservationStatus.OBSERVED and self.value is not None:
            raise ValueError("non-observed results cannot carry a value")
        if self.status is ObservationStatus.OBSERVED and self.value is None:
            raise ValueError("observed results must carry a value")
        if self.evidence_class in {EvidenceClass.MEASURED, EvidenceClass.SOURCE_DERIVED}:
            if not self.source_record_id:
                raise ValueError("measured/source-derived observations require source_record_id")
        if self.unit is not None and not self.unit.strip():
            raise ValueError("unit must be non-empty when supplied")
        object.__setattr__(self, "conditions", dict(self.conditions or {}))


@dataclass(frozen=True)
class EvidenceRecord:
    """Provenance record for an observation, claim, or derived result."""
    evidence_id: str
    evidence_class: EvidenceClass
    description: str
    source_id: str | None = None
    source_version: str | None = None
    license_status: str | None = None
    parent_evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    source_record_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_class, EvidenceClass):
            raise TypeError("evidence_class must be an EvidenceClass")
        if not self.evidence_id.strip() or not self.description.strip():
            raise ValueError("evidence_id and description must be non-empty")
        if self.evidence_class in {EvidenceClass.MEASURED, EvidenceClass.SOURCE_DERIVED}:
            if not self.source_id:
                raise ValueError("measured/source-derived evidence requires source_id")


@dataclass(frozen=True)
class ExperimentRecord:
    """Persistable link between a protocol, initial state, predictions, and results."""
    experiment_id: str
    protocol_id: str
    initial_state_id: str
    status: ExperimentStatus
    hypothesis_id: str | None = None
    predictions: tuple[Prediction, ...] = ()
    observations: tuple[ExperimentalObservation, ...] = ()
    world_engine_version: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ExperimentStatus):
            raise TypeError("status must be an ExperimentStatus")
        for name in ("experiment_id", "protocol_id", "initial_state_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.status is ExperimentStatus.COMPLETED and self.completed_at is None:
            raise ValueError("completed experiments require completed_at")
        if self.status is ExperimentStatus.FAILED and not self.failure_reason:
            raise ValueError("failed experiments require failure_reason")
        pids = [item.prediction_id for item in self.predictions]
        oids = [item.observation_id for item in self.observations]
        if len(pids) != len(set(pids)):
            raise ValueError("prediction IDs must be unique within an experiment")
        if len(oids) != len(set(oids)):
            raise ValueError("observation IDs must be unique within an experiment")


def _jsonable(value: Any) -> Any:
    """Convert supported values to deterministic JSON-compatible values."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite floats cannot be serialized deterministically")
        return value
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Serialize supported values deterministically for reproducible records."""
    return json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    )


def stable_id(namespace: str, payload: Any, *, length: int = 24) -> str:
    """Return a deterministic namespaced ID for a canonical JSON payload."""
    if not namespace.strip():
        raise ValueError("namespace must be non-empty")
    if length < 8 or length > 64:
        raise ValueError("length must be between 8 and 64")
    digest = hashlib.sha256(
        (namespace.strip() + "\n" + canonical_json(payload)).encode("utf-8")
    ).hexdigest()
    return f"{namespace.strip()}_{digest[:length]}"
