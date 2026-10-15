"""Phase 1F end-to-end contract exit gate.

These tests prove contract interoperability and deterministic software behavior,
not physical or scientific validity.
"""
from __future__ import annotations

from food_intelligence import (
    CONTRACTS_VERSION,
    EvidenceClass,
    EvidenceLedger,
    EvidenceRecord,
    ExperimentProtocol,
    ExperimentRecord,
    ExperimentStatus,
    ExperimentalObservation,
    Hypothesis,
    Intervention,
    ObservationStatus,
    Prediction,
    Quantity,
    WorldComponent,
    WorldState,
    canonical_json,
    stable_id,
    validate_experiment_bundle,
)


def make_bundle():
    initial_state = WorldState(
        state_id="state:turmeric-raw-v1",
        components=(
            WorldComponent(
                component_id="batch:turmeric-01",
                ingredient_id="ingredient:turmeric",
                ingredient_state_id="state:turmeric-raw",
                amount=Quantity(20.0, "g"),
                attributes={"batch": "01"},
            ),
        ),
        conditions={
            "temperature": Quantity(25.0, "degC"),
            "duration": Quantity(0.0, "min"),
        },
        schema_version=CONTRACTS_VERSION,
    )
    intervention = Intervention(
        intervention_id="intervention:heat-01",
        operation="heat",
        target_component_ids=("batch:turmeric-01",),
        parameters={"target_temperature": Quantity(80.0, "degC")},
        preconditions=("batch is present",),
    )
    protocol = ExperimentProtocol(
        protocol_id="protocol:heating-v1",
        name="Controlled turmeric heating",
        version="1.0",
        interventions=(intervention,),
        control_variables=("temperature", "duration"),
        repetitions=2,
    )
    evidence = EvidenceRecord(
        evidence_id="evidence:sim-run-01",
        evidence_class=EvidenceClass.SIMULATED,
        description="Illustrative simulator output for contract integration testing.",
        source_version="simulator-test-v1",
        method="test-fixture",
        limitations=("Synthetic software fixture; not scientific evidence.",),
    )
    hypothesis = Hypothesis(
        hypothesis_id="hypothesis:aroma-signal",
        statement="The simulated aroma signal increases after the heating intervention.",
        target_variable="aroma_signal",
        expected_direction="increase",
        falsification_criterion="The measured signal is not greater than the baseline under the defined protocol.",
        evidence_ids=("evidence:sim-run-01",),
    )
    prediction = Prediction(
        prediction_id="prediction:aroma-signal-01",
        variable="aroma_signal",
        value=0.4,
        unit="relative",
        model_id="test-model",
        model_version="0.0.0-test",
        assumptions=("Synthetic value used only to exercise contract links.",),
    )
    observation = ExperimentalObservation(
        observation_id="observation:aroma-signal-01",
        variable="aroma_signal",
        value=0.35,
        unit="relative",
        status=ObservationStatus.OBSERVED,
        evidence_class=EvidenceClass.SIMULATED,
        method="test-fixture",
        conditions={"temperature": "80 degC"},
    )
    experiment = ExperimentRecord(
        experiment_id="experiment:heating-01",
        protocol_id=protocol.protocol_id,
        initial_state_id=initial_state.state_id,
        status=ExperimentStatus.COMPLETED,
        hypothesis_id=hypothesis.hypothesis_id,
        predictions=(prediction,),
        observations=(observation,),
        world_engine_version="contract-fixture-only",
        started_at="2026-10-15T00:00:00Z",
        completed_at="2026-10-15T00:01:00Z",
    )
    return initial_state, protocol, hypothesis, evidence, experiment


def test_public_contract_api_is_available_from_package_root():
    # This guards the public import boundary while preserving legacy exports.
    from food_intelligence import (
        CompatibilityV2,
        FoodIntelligencePipeline,
        SchemaMigrationRegistry,
        convert_quantity,
        legacy_observation_to_contract,
    )

    assert CONTRACTS_VERSION
    assert all((
        CompatibilityV2,
        FoodIntelligencePipeline,
        SchemaMigrationRegistry,
        convert_quantity,
        legacy_observation_to_contract,
    ))


def test_complete_experiment_bundle_crosses_contract_boundaries():
    state, protocol, hypothesis, evidence, experiment = make_bundle()
    report = validate_experiment_bundle(
        experiment,
        protocols={protocol.protocol_id: protocol},
        world_states={state.state_id: state},
        hypotheses={hypothesis.hypothesis_id: hypothesis},
        evidence_records={evidence.evidence_id: evidence},
    )

    assert report.valid
    assert report.issues == ()
    assert experiment.status is ExperimentStatus.COMPLETED
    assert experiment.predictions[0].value != experiment.observations[0].value
    assert experiment.observations[0].evidence_class is EvidenceClass.SIMULATED
    assert evidence.evidence_class is EvidenceClass.SIMULATED


def test_end_to_end_records_keep_evidence_lineage_auditable():
    _, _, _, evidence, _ = make_bundle()
    ledger = EvidenceLedger()
    ledger.add_record(evidence)

    audit = ledger.audit()
    assert audit.valid
    assert audit.record_count == 1
    assert audit.link_count == 0
    assert not any(issue.severity == "ERROR" for issue in audit.issues)


def test_contract_serialization_and_identifiers_are_repeatable():
    state, protocol, hypothesis, evidence, experiment = make_bundle()
    bundle = {
        "state": state,
        "protocol": protocol,
        "hypothesis": hypothesis,
        "evidence": evidence,
        "experiment": experiment,
    }
    reordered_bundle = {
        "experiment": experiment,
        "evidence": evidence,
        "hypothesis": hypothesis,
        "protocol": protocol,
        "state": state,
    }

    assert canonical_json(bundle) == canonical_json(reordered_bundle)
    assert stable_id("phase1f_bundle", bundle) == stable_id("phase1f_bundle", reordered_bundle)


def test_unknown_initial_condition_survives_the_full_contract_boundary():
    state, protocol, hypothesis, evidence, experiment = make_bundle()
    unknown_state = WorldState(
        state_id="state:unknown-temperature",
        components=state.components,
        conditions={
            "temperature": Quantity(None, "degC"),
            "duration": Quantity(0.0, "min"),
        },
    )
    altered_experiment = ExperimentRecord(
        experiment_id=experiment.experiment_id,
        protocol_id=experiment.protocol_id,
        initial_state_id=unknown_state.state_id,
        status=experiment.status,
        hypothesis_id=experiment.hypothesis_id,
        predictions=experiment.predictions,
        observations=experiment.observations,
        world_engine_version=experiment.world_engine_version,
        started_at=experiment.started_at,
        completed_at=experiment.completed_at,
    )

    report = validate_experiment_bundle(
        altered_experiment,
        protocols={protocol.protocol_id: protocol},
        world_states={unknown_state.state_id: unknown_state},
        hypotheses={hypothesis.hypothesis_id: hypothesis},
        evidence_records={evidence.evidence_id: evidence},
    )
    assert report.valid
    assert unknown_state.conditions["temperature"].value is None
