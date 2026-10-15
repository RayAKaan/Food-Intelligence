"""Tests for cross-contract integrity and explicit schema migration."""
from __future__ import annotations

import pytest

from food_intelligence.cross_contracts import (
    ContractValidationReport,
    IssueSeverity,
    SchemaMigrationRegistry,
    validate_experiment_bundle,
)
from food_intelligence.world_contracts import (
    EvidenceClass,
    EvidenceRecord,
    ExperimentProtocol,
    ExperimentRecord,
    ExperimentStatus,
    ExperimentalObservation,
    Intervention,
    ObservationStatus,
    Prediction,
    Quantity,
    WorldComponent,
    WorldState,
)


def base_state() -> WorldState:
    return WorldState(
        "state-1",
        (
            WorldComponent(
                "batch-1", "turmeric", "turmeric-raw", Quantity(20, "g")
            ),
        ),
        {"temperature": Quantity(25, "degC"), "duration": Quantity(0, "min")},
    )


def base_protocol(*, target="batch-1", controls=("temperature",)) -> ExperimentProtocol:
    return ExperimentProtocol(
        "protocol-1",
        "Controlled heating",
        "1",
        (
            Intervention(
                "intervention-1", "heat", (target,),
                {"temperature": Quantity(80, "degC")},
            ),
        ),
        control_variables=controls,
    )


def base_experiment(**overrides) -> ExperimentRecord:
    values = {
        "experiment_id": "experiment-1",
        "protocol_id": "protocol-1",
        "initial_state_id": "state-1",
        "status": ExperimentStatus.COMPLETED,
        "predictions": (
            Prediction("prediction-1", "aroma_signal", 0.4, "relative", "model", "1"),
        ),
        "observations": (
            ExperimentalObservation(
                "observation-1", "aroma_signal", 0.35, "relative",
                ObservationStatus.OBSERVED, EvidenceClass.SIMULATED, "simulator-v1",
            ),
        ),
        "completed_at": "2026-10-15T10:00:00Z",
    }
    values.update(overrides)
    return ExperimentRecord(**values)


def test_valid_bundle_has_no_issues() -> None:
    report = validate_experiment_bundle(
        base_experiment(),
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
    )
    assert isinstance(report, ContractValidationReport)
    assert report.valid
    assert report.issues == ()


def test_missing_protocol_and_initial_state_are_errors() -> None:
    report = validate_experiment_bundle(
        base_experiment(),
        protocols={},
        world_states={},
    )
    assert not report.valid
    assert {x.code for x in report.errors} == {
        "PROTOCOL_NOT_FOUND", "INITIAL_STATE_NOT_FOUND"
    }


def test_protocol_targets_must_exist_in_initial_state() -> None:
    report = validate_experiment_bundle(
        base_experiment(),
        protocols={"protocol-1": base_protocol(target="missing-batch")},
        world_states={"state-1": base_state()},
    )
    assert not report.valid
    assert "INTERVENTION_TARGET_NOT_FOUND" in {x.code for x in report.errors}


def test_control_variables_need_initial_values_for_reproducibility() -> None:
    report = validate_experiment_bundle(
        base_experiment(),
        protocols={"protocol-1": base_protocol(controls=("temperature", "humidity"))},
        world_states={"state-1": base_state()},
    )
    assert "CONTROL_VARIABLE_VALUE_MISSING" in {x.code for x in report.errors}


def test_incompatible_prediction_and_observation_units_are_rejected() -> None:
    experiment = base_experiment(
        predictions=(
            Prediction("p1", "temperature", 80, "degC", "thermal-model", "1"),
        ),
        observations=(
            ExperimentalObservation(
                "o1", "temperature", 353.15, "K", ObservationStatus.OBSERVED,
                EvidenceClass.SIMULATED, "simulator",
            ),
        ),
    )
    compatible = validate_experiment_bundle(
        experiment,
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
    )
    assert compatible.valid

    incompatible_experiment = base_experiment(
        predictions=(Prediction("p2", "temperature", 80, "degC", "model", "1"),),
        observations=(
            ExperimentalObservation(
                "o2", "temperature", 80, "g", ObservationStatus.OBSERVED,
                EvidenceClass.SIMULATED, "simulator",
            ),
        ),
    )
    incompatible = validate_experiment_bundle(
        incompatible_experiment,
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
    )
    assert not incompatible.valid
    assert "PREDICTION_OBSERVATION_UNIT_MISMATCH" in {
        x.code for x in incompatible.errors
    }


def test_missing_unit_on_comparison_is_warning_not_silent_conversion() -> None:
    experiment = base_experiment(
        predictions=(Prediction("p1", "temperature", 80, None, "model", "1"),),
        observations=(
            ExperimentalObservation(
                "o1", "temperature", 80, "degC", ObservationStatus.OBSERVED,
                EvidenceClass.SIMULATED, "simulator",
            ),
        ),
    )
    report = validate_experiment_bundle(
        experiment,
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
    )
    assert report.valid
    assert "COMPARISON_UNIT_MISSING" in {x.code for x in report.warnings}


def test_completed_without_observations_is_a_warning() -> None:
    experiment = base_experiment(observations=())
    report = validate_experiment_bundle(
        experiment,
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
    )
    assert report.valid
    assert "COMPLETED_WITHOUT_OBSERVATIONS" in {x.code for x in report.warnings}


def test_hypothesis_and_evidence_references_are_checked() -> None:
    from food_intelligence.world_contracts import Hypothesis

    hypothesis = Hypothesis(
        "h1", "Heating changes aroma", "aroma_signal", "increase",
        "A replicated estimate is non-positive", evidence_ids=("missing-evidence",),
    )
    report = validate_experiment_bundle(
        base_experiment(hypothesis_id="h1"),
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
        hypotheses={"h1": hypothesis},
        evidence_records={},
    )
    assert "HYPOTHESIS_EVIDENCE_NOT_FOUND" in {x.code for x in report.errors}


def test_evidence_registry_keys_and_parent_references_are_checked() -> None:
    record = EvidenceRecord(
        "derived", EvidenceClass.INFERRED, "Derived claim",
        parent_evidence_ids=("missing-parent",),
    )
    report = validate_experiment_bundle(
        base_experiment(),
        protocols={"protocol-1": base_protocol()},
        world_states={"state-1": base_state()},
        evidence_records={"wrong-key": record},
    )
    assert {"EVIDENCE_KEY_MISMATCH", "PARENT_EVIDENCE_NOT_FOUND"} <= {
        x.code for x in report.errors
    }


def test_schema_registry_uses_explicit_deterministic_shortest_path() -> None:
    registry = SchemaMigrationRegistry(current_version="3")
    registry.register("1", "2", lambda data: {**data, "version": 2})
    registry.register("2", "3", lambda data: {**data, "version": 3})
    registry.register("1", "3", lambda data: {**data, "version": 3, "direct": True})
    assert registry.migration_path("1") == (("1", "3"),)
    source = {"value": 5}
    assert registry.migrate(source, "1") == {"value": 5, "version": 3, "direct": True}
    assert source == {"value": 5}
    assert registry.migrate(source, "3") == source


def test_schema_registry_fails_closed_without_migration_and_rejects_cycles() -> None:
    registry = SchemaMigrationRegistry(current_version="3")
    registry.register("1", "2", lambda data: data)
    with pytest.raises(ValueError, match="no registered schema migration path"):
        registry.migrate({"x": 1}, "1")
    with pytest.raises(ValueError, match="cycle"):
        registry.register("2", "1", lambda data: data)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("1", "2", lambda data: data)


def test_schema_migration_must_return_a_mapping() -> None:
    registry = SchemaMigrationRegistry(current_version="2")
    registry.register("1", "2", lambda data: ["not", "a", "mapping"])
    with pytest.raises(TypeError, match="must return a mapping"):
        registry.migrate({"x": 1}, "1")


def test_schema_registry_rejects_blank_versions_and_invalid_migrations() -> None:
    with pytest.raises(ValueError, match="current_version"):
        SchemaMigrationRegistry(current_version=" ")
    registry = SchemaMigrationRegistry()
    with pytest.raises(ValueError, match="non-empty"):
        registry.register(" ", "2", lambda data: data)
    with pytest.raises(ValueError, match="own version"):
        registry.register("1", "1", lambda data: data)
    with pytest.raises(TypeError, match="callable"):
        registry.register("1", "2", None)
