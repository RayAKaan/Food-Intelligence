"""Tests for canonical Computational Food World contracts."""
from __future__ import annotations

import math

import pytest

from food_intelligence.world_contracts import (
    EvidenceClass,
    EvidenceRecord,
    ExperimentRecord,
    ExperimentStatus,
    ExperimentalObservation,
    ExperimentProtocol,
    Intervention,
    ObservationStatus,
    Quantity,
    UncertaintyEstimate,
    WorldComponent,
    WorldState,
    canonical_json,
    stable_id,
)


def component(component_id: str = "batch-1") -> WorldComponent:
    return WorldComponent(
        component_id=component_id,
        ingredient_id="turmeric",
        ingredient_state_id="turmeric-raw",
        amount=Quantity(20.0, "g"),
    )


def test_unknown_quantity_is_not_zero() -> None:
    unknown = Quantity(None, "mg")
    assert unknown.value is None
    assert unknown.is_known is False
    assert Quantity(0.0, "mg").is_known is True


def test_quantity_rejects_non_finite_values_and_empty_units() -> None:
    with pytest.raises(ValueError, match="finite"):
        Quantity(math.nan, "g")
    with pytest.raises(ValueError, match="unit"):
        Quantity(1.0, " ")


def test_uncertainty_checks_bounds_and_confidence() -> None:
    with pytest.raises(ValueError, match="lower_bound"):
        UncertaintyEstimate("interval", lower_bound=4, upper_bound=2)
    with pytest.raises(ValueError, match="confidence_level"):
        UncertaintyEstimate("bootstrap", confidence_level=1.0)


def test_world_state_requires_unique_component_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        WorldState("state-1", (component(), component()), {"temperature": Quantity(25, "degC")})


def test_world_state_preserves_missing_environment_condition() -> None:
    state = WorldState(
        "state-1",
        (component(),),
        {"temperature": Quantity(None, "degC")},
    )
    assert state.conditions["temperature"].value is None


def test_intervention_requires_target_and_unique_targets() -> None:
    with pytest.raises(ValueError, match="target"):
        Intervention("i1", "heat", (), {"temperature": 100})
    with pytest.raises(ValueError, match="unique"):
        Intervention("i1", "heat", ("batch-1", "batch-1"), {"temperature": 100})


def test_protocol_requires_positive_repetitions() -> None:
    with pytest.raises(ValueError, match="positive"):
        ExperimentProtocol("p1", "heat test", "1", (), repetitions=0)


def test_measured_observation_requires_source_record() -> None:
    with pytest.raises(ValueError, match="source_record_id"):
        ExperimentalObservation(
            "o1", "aroma_intensity", 0.4, "score",
            ObservationStatus.OBSERVED, EvidenceClass.MEASURED, "sensory_panel",
        )


def test_simulated_and_measured_observations_are_distinct() -> None:
    simulated = ExperimentalObservation(
        "o-sim", "volatile_release", 0.7, "relative",
        ObservationStatus.OBSERVED, EvidenceClass.SIMULATED, "model-v1",
    )
    measured = ExperimentalObservation(
        "o-meas", "volatile_release", 0.6, "relative",
        ObservationStatus.OBSERVED, EvidenceClass.MEASURED, "GC-MS",
        source_record_id="lab-run-22",
    )
    assert simulated.evidence_class is EvidenceClass.SIMULATED
    assert measured.evidence_class is EvidenceClass.MEASURED


def test_non_observed_result_cannot_carry_a_value() -> None:
    with pytest.raises(ValueError, match="cannot carry a value"):
        ExperimentalObservation(
            "o1", "odor", 0, "score",
            ObservationStatus.NOT_MEASURED, EvidenceClass.MEASURED, "panel",
            source_record_id="run-1",
        )


def test_measured_evidence_requires_a_source() -> None:
    with pytest.raises(ValueError, match="source_id"):
        EvidenceRecord("e1", EvidenceClass.MEASURED, "Measured result")


def test_experiment_lifecycle_requires_completion_or_failure_details() -> None:
    with pytest.raises(ValueError, match="completed_at"):
        ExperimentRecord("x1", "p1", "s1", ExperimentStatus.COMPLETED)
    with pytest.raises(ValueError, match="failure_reason"):
        ExperimentRecord("x2", "p1", "s1", ExperimentStatus.FAILED)


def test_canonical_json_and_stable_ids_ignore_mapping_insertion_order() -> None:
    left = {"temperature": 100, "medium": {"water": 0.2, "oil": 0.8}}
    right = {"medium": {"oil": 0.8, "water": 0.2}, "temperature": 100}
    assert canonical_json(left) == canonical_json(right)
    assert stable_id("world", left) == stable_id("world", right)
    assert stable_id("world", left) != stable_id("protocol", left)


def test_stable_id_rejects_invalid_namespace_and_length() -> None:
    with pytest.raises(ValueError, match="namespace"):
        stable_id(" ", {"a": 1})
    with pytest.raises(ValueError, match="length"):
        stable_id("world", {"a": 1}, length=4)


def test_canonical_json_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        canonical_json({"value": math.inf})
