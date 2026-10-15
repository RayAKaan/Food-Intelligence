"""Measurement metadata and safe unit conversion for experimental observations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from .units import assert_compatible_units, convert_quantity
from .world_contracts import ExperimentalObservation, Quantity, UncertaintyEstimate


CALIBRATION_STATUSES = frozenset({
    "CALIBRATED", "NOT_CALIBRATED", "NOT_APPLICABLE", "UNKNOWN",
})


@dataclass(frozen=True)
class MeasurementMetadata:
    """Context required to interpret a measurement and its detection limits."""

    method: str
    replicate_count: int = 1
    instrument_id: str | None = None
    calibration_id: str | None = None
    calibration_status: str = "UNKNOWN"
    detection_limit: Quantity | None = None
    quantification_limit: Quantity | None = None
    sample_matrix: str | None = None
    sampling_method: str | None = None
    measured_at: str | None = None
    uncertainty: UncertaintyEstimate | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.method.strip():
            raise ValueError("measurement method must be non-empty")
        if self.replicate_count < 1:
            raise ValueError("replicate_count must be positive")
        if self.calibration_status not in CALIBRATION_STATUSES:
            raise ValueError(f"unsupported calibration status: {self.calibration_status}")
        if self.measured_at is not None:
            try:
                datetime.fromisoformat(self.measured_at.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("measured_at must be an ISO-8601 timestamp") from None
        if self.detection_limit is not None and self.quantification_limit is not None:
            assert_compatible_units(
                self.detection_limit.unit, self.quantification_limit.unit
            )
            detection = self.detection_limit
            quantification = self.quantification_limit
            if detection.value is not None and quantification.value is not None:
                converted = convert_quantity(quantification, detection.unit)
                if converted.value < detection.value:
                    raise ValueError("quantification_limit cannot be below detection_limit")


def convert_observation_unit(
    observation: ExperimentalObservation, target_unit: str
) -> ExperimentalObservation:
    """Return a copy of a numeric observation expressed in another compatible unit.

    Non-observed records keep their missing value. Categorical observations,
    unknown units, and dimensionally incompatible conversions fail explicitly.
    """
    if observation.unit is None:
        raise ValueError("observation has no unit to convert")
    assert_compatible_units(observation.unit, target_unit)
    if observation.value is None:
        return ExperimentalObservation(
            observation_id=observation.observation_id,
            variable=observation.variable,
            value=None,
            unit=target_unit,
            status=observation.status,
            evidence_class=observation.evidence_class,
            method=observation.method,
            source_record_id=observation.source_record_id,
            uncertainty=convert_quantity(
                Quantity(None, observation.unit, observation.uncertainty), target_unit
            ).uncertainty,
            conditions=observation.conditions,
        )
    if isinstance(observation.value, bool) or not isinstance(observation.value, (int, float)):
        raise ValueError("only numeric observations can be converted between units")
    if not math.isfinite(observation.value):
        raise ValueError("observation value must be finite")
    converted = convert_quantity(
        Quantity(float(observation.value), observation.unit, observation.uncertainty),
        target_unit,
    )
    return ExperimentalObservation(
        observation_id=observation.observation_id,
        variable=observation.variable,
        value=converted.value,
        unit=converted.unit,
        status=observation.status,
        evidence_class=observation.evidence_class,
        method=observation.method,
        source_record_id=observation.source_record_id,
        uncertainty=converted.uncertainty,
        conditions=observation.conditions,
    )
