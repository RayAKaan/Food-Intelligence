"""Phase 1C tests for unit conversion, uncertainty, and measurement metadata."""
from __future__ import annotations

import math

import pytest

from food_intelligence.measurement import MeasurementMetadata, convert_observation_unit
from food_intelligence.units import (
    assert_compatible_units,
    convert_quantity,
    convert_value,
    normalize_quantity,
    unit_dimension,
)
from food_intelligence.world_contracts import (
    EvidenceClass,
    ExperimentalObservation,
    ObservationStatus,
    Quantity,
    UncertaintyEstimate,
)


def test_mass_and_volume_conversions_are_dimensional() -> None:
    assert convert_value(1250, "mg", "g") == pytest.approx(1.25)
    assert convert_value(1.5, "L", "mL") == pytest.approx(1500)
    with pytest.raises(ValueError, match="incompatible units"):
        convert_value(1, "g", "mL")


def test_temperature_conversion_handles_affine_offsets() -> None:
    assert convert_value(100, "degC", "degF") == pytest.approx(212)
    assert convert_value(32, "degF", "degC") == pytest.approx(0)
    assert convert_value(0, "degC", "K") == pytest.approx(273.15)


def test_uncertainty_bounds_convert_with_offsets_but_stddev_does_not() -> None:
    quantity = Quantity(
        100,
        "degC",
        UncertaintyEstimate(
            method="replicate_sd",
            standard_deviation=2,
            lower_bound=96,
            upper_bound=104,
            sample_size=5,
        ),
    )
    converted = convert_quantity(quantity, "degF")
    assert converted.value == pytest.approx(212)
    assert converted.uncertainty is not None
    assert converted.uncertainty.standard_deviation == pytest.approx(3.6)
    assert converted.uncertainty.lower_bound == pytest.approx(204.8)
    assert converted.uncertainty.upper_bound == pytest.approx(219.2)
    assert converted.uncertainty.sample_size == 5


def test_unknown_quantity_remains_unknown_after_unit_conversion() -> None:
    converted = convert_quantity(Quantity(None, "mg"), "g")
    assert converted.value is None
    assert converted.unit == "g"


def test_normalization_uses_canonical_base_unit() -> None:
    normalized = normalize_quantity(Quantity(1000, "mg"))
    assert normalized.unit == "kg"
    assert normalized.value == pytest.approx(0.001)
    assert unit_dimension("degC") == "temperature"


def test_unknown_units_and_non_finite_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="unsupported unit"):
        convert_value(1, "scoop", "g")
    with pytest.raises(ValueError, match="finite"):
        convert_value(math.inf, "g", "kg")
    with pytest.raises(ValueError, match="unsupported unit"):
        assert_compatible_units("score", "made_up_unit")


def test_measurement_metadata_validates_replicates_calibration_and_timestamp() -> None:
    with pytest.raises(ValueError, match="replicate_count"):
        MeasurementMetadata("GC-MS", replicate_count=0)
    with pytest.raises(ValueError, match="calibration status"):
        MeasurementMetadata("GC-MS", calibration_status="MAYBE")
    with pytest.raises(ValueError, match="ISO-8601"):
        MeasurementMetadata("GC-MS", measured_at="yesterday")
    metadata = MeasurementMetadata(
        "GC-MS", replicate_count=3, calibration_status="CALIBRATED",
        measured_at="2026-10-15T10:30:00+00:00",
    )
    assert metadata.replicate_count == 3


def test_detection_and_quantification_limits_must_have_compatible_ordered_units() -> None:
    with pytest.raises(ValueError, match="incompatible units"):
        MeasurementMetadata(
            "assay",
            detection_limit=Quantity(1, "mg"),
            quantification_limit=Quantity(2, "mL"),
        )
    with pytest.raises(ValueError, match="below detection_limit"):
        MeasurementMetadata(
            "assay",
            detection_limit=Quantity(5, "mg"),
            quantification_limit=Quantity(2, "mg"),
        )
    valid = MeasurementMetadata(
        "assay",
        detection_limit=Quantity(1, "mg"),
        quantification_limit=Quantity(0.002, "g"),
    )
    assert valid.quantification_limit is not None


def test_observation_conversion_preserves_identity_evidence_and_uncertainty() -> None:
    observation = ExperimentalObservation(
        observation_id="obs-1",
        variable="temperature",
        value=100.0,
        unit="degC",
        status=ObservationStatus.OBSERVED,
        evidence_class=EvidenceClass.MEASURED,
        method="thermocouple",
        source_record_id="lab-run-1",
        uncertainty=UncertaintyEstimate("instrument", standard_deviation=1.0),
        conditions={"medium": "oil"},
    )
    converted = convert_observation_unit(observation, "degF")
    assert converted.observation_id == observation.observation_id
    assert converted.source_record_id == observation.source_record_id
    assert converted.evidence_class is EvidenceClass.MEASURED
    assert converted.value == pytest.approx(212)
    assert converted.uncertainty is not None
    assert converted.uncertainty.standard_deviation == pytest.approx(1.8)
    assert converted.conditions == {"medium": "oil"}


def test_observation_conversion_rejects_missing_units_categorical_and_incompatible() -> None:
    base = dict(
        observation_id="obs-2",
        variable="aroma",
        status=ObservationStatus.OBSERVED,
        evidence_class=EvidenceClass.SIMULATED,
        method="model-v1",
    )
    with pytest.raises(ValueError, match="no unit"):
        convert_observation_unit(ExperimentalObservation(value=0.5, unit=None, **base), "score")
    with pytest.raises(ValueError, match="numeric"):
        convert_observation_unit(ExperimentalObservation(value="smoky", unit="score", **base), "score")
    with pytest.raises(ValueError, match="incompatible units"):
        convert_observation_unit(ExperimentalObservation(value=0.5, unit="score", **base), "g")


def test_non_observed_numeric_value_stays_missing_during_conversion() -> None:
    observation = ExperimentalObservation(
        observation_id="obs-3",
        variable="temperature",
        value=None,
        unit="degC",
        status=ObservationStatus.NOT_MEASURED,
        evidence_class=EvidenceClass.SIMULATED,
        method="not-run",
    )
    converted = convert_observation_unit(observation, "degF")
    assert converted.value is None
    assert converted.unit == "degF"
    assert converted.status is ObservationStatus.NOT_MEASURED
