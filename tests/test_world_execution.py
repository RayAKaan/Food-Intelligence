"""Tests for the Phase 2A deterministic world-transition boundary."""
from __future__ import annotations

from dataclasses import replace

import pytest

from food_intelligence.world_contracts import (
    CONTRACTS_VERSION,
    EvidenceClass,
    Intervention,
    Quantity,
    WorldComponent,
    WorldState,
    canonical_json,
)
from food_intelligence.world_execution import (
    InterventionEngine,
    TransitionStatus,
    execute_intervention,
)


def initial_state(*, temperature=25.0, temperature_unit="degC", schema_version=CONTRACTS_VERSION):
    return WorldState(
        state_id="state:initial",
        components=(
            WorldComponent(
                component_id="batch:one",
                ingredient_id="ingredient:turmeric",
                ingredient_state_id="state:turmeric-raw",
                amount=Quantity(20.0, "g"),
                attributes={"source": "fixture", "tags": ["initial"]},
            ),
        ),
        conditions={
            "temperature": Quantity(temperature, temperature_unit),
            "duration": Quantity(0.0, "min"),
            "humidity": Quantity(None, "%"),
        },
        schema_version=schema_version,
    )


def intervention(*, operation="set_condition", condition="temperature", value=None, preconditions=()):
    return Intervention(
        intervention_id="intervention:set-temperature",
        operation=operation,
        target_component_ids=("batch:one",),
        parameters={
            "condition": condition,
            "value": value if value is not None else Quantity(80.0, "degC"),
        },
        preconditions=tuple(preconditions),
    )


def issue_codes(transition):
    return {issue.code for issue in transition.issues}


def test_set_condition_returns_new_state_and_parent_link():
    state = initial_state()
    result, transition = execute_intervention(
        state,
        intervention(preconditions=("component_exists:batch:one",)),
    )

    assert result is not None
    assert transition.status is TransitionStatus.SUCCEEDED
    assert transition.resulting_state_id == result.state_id
    assert result.parent_state_id == state.state_id
    assert result.conditions["temperature"] == Quantity(80.0, "degC")
    assert result.components == state.components
    assert transition.evidence_class is EvidenceClass.SIMULATED
    assert transition.engine_id and transition.engine_version
    assert transition.limitations


def test_temperature_unit_is_converted_to_existing_condition_unit():
    state = initial_state(temperature=298.15, temperature_unit="K")
    result, transition = execute_intervention(
        state, intervention(value=Quantity(80.0, "degC"))
    )

    assert transition.status is TransitionStatus.SUCCEEDED
    assert result is not None
    assert result.conditions["temperature"].unit == "K"
    assert result.conditions["temperature"].value == pytest.approx(353.15)


def test_success_and_failure_do_not_mutate_initial_state_or_nested_mappings():
    state = initial_state()
    before = canonical_json(state)
    result, success = execute_intervention(state, intervention())
    assert result is not None
    assert success.status is TransitionStatus.SUCCEEDED
    assert canonical_json(state) == before
    assert state.components[0].attributes == {"source": "fixture", "tags": ["initial"]}

    failed_result, failure = execute_intervention(
        state, intervention(operation="run arbitrary code")
    )
    assert failed_result is None
    assert failure.status is TransitionStatus.FAILED
    assert canonical_json(state) == before


def test_unknown_condition_precondition_fails_closed():
    state = initial_state()
    result, transition = execute_intervention(
        state,
        intervention(preconditions=("condition_known:humidity",)),
    )

    assert result is None
    assert transition.status is TransitionStatus.FAILED
    assert "PRECONDITION_UNKNOWN" in issue_codes(transition)


def test_false_component_precondition_fails_closed():
    result, transition = execute_intervention(
        initial_state(),
        intervention(preconditions=("component_exists:missing",)),
    )
    assert result is None
    assert "PRECONDITION_FAILED" in issue_codes(transition)


@pytest.mark.parametrize(
    ("operation", "expected_code"),
    [
        ("heat", "OPERATION_UNSUPPORTED"),
        ("__import__('os').system('echo unsafe')", "OPERATION_UNSUPPORTED"),
    ],
)
def test_unknown_and_malicious_operation_names_are_never_executed(operation, expected_code):
    result, transition = execute_intervention(
        initial_state(), intervention(operation=operation)
    )
    assert result is None
    assert expected_code in issue_codes(transition)


def test_missing_target_fails_without_result_state():
    bad = Intervention(
        intervention_id="intervention:missing-target",
        operation="set_condition",
        target_component_ids=("batch:missing",),
        parameters={"condition": "temperature", "value": Quantity(80, "degC")},
    )
    result, transition = execute_intervention(initial_state(), bad)
    assert result is None
    assert "TARGET_COMPONENT_NOT_FOUND" in issue_codes(transition)


def test_missing_condition_and_invalid_parameters_fail_closed():
    missing, missing_transition = execute_intervention(
        initial_state(), intervention(condition="unregistered-condition")
    )
    assert missing is None
    assert "CONDITION_NOT_FOUND" in issue_codes(missing_transition)

    invalid, invalid_transition = execute_intervention(
        initial_state(),
        Intervention(
            intervention_id="intervention:bad-value",
            operation="set_condition",
            target_component_ids=("batch:one",),
            parameters={"condition": "temperature", "value": 80},
        ),
    )
    assert invalid is None
    assert "PARAMETER_INVALID" in issue_codes(invalid_transition)


def test_dimensionally_incompatible_and_unsupported_units_fail_closed():
    incompatible, incompatible_transition = execute_intervention(
        initial_state(), intervention(value=Quantity(2.0, "g"))
    )
    assert incompatible is None
    assert "PARAMETER_UNIT_INVALID" in issue_codes(incompatible_transition)

    unsupported, unsupported_transition = execute_intervention(
        initial_state(), intervention(value=Quantity(2.0, "mystery-unit"))
    )
    assert unsupported is None
    assert "PARAMETER_UNIT_INVALID" in issue_codes(unsupported_transition)


def test_unknown_values_are_not_defaulted_or_overwritten_without_explicit_action():
    state = initial_state()
    assert state.conditions["humidity"].value is None
    result, transition = execute_intervention(
        state,
        Intervention(
            intervention_id="intervention:set-humidity",
            operation="set_condition",
            target_component_ids=("batch:one",),
            parameters={"condition": "humidity", "value": Quantity(55.0, "%")},
            preconditions=("component_exists:batch:one",),
        ),
    )
    assert transition.status is TransitionStatus.SUCCEEDED
    assert result is not None
    assert result.conditions["humidity"].value == 55.0
    assert state.conditions["humidity"].value is None


def test_unsupported_schema_version_fails_closed():
    state = initial_state(schema_version="99.0")
    result, transition = execute_intervention(state, intervention())
    assert result is None
    assert "SCHEMA_VERSION_UNSUPPORTED" in issue_codes(transition)


def test_replay_is_deterministic_and_engine_version_participates_in_identity():
    state = initial_state()
    action = intervention()
    result1, transition1 = execute_intervention(state, action)
    result2, transition2 = execute_intervention(state, action)
    assert result1 is not None and result2 is not None
    assert result1.state_id == result2.state_id
    assert transition1.transition_id == transition2.transition_id

    _, transition3 = execute_intervention(
        state, action, engine=InterventionEngine(version="1.0.1")
    )
    assert transition3.transition_id != transition1.transition_id
    assert transition3.resulting_state_id != transition1.resulting_state_id


def test_transition_contract_rejects_claimed_physical_evidence():
    from food_intelligence.world_execution import WorldTransition

    with pytest.raises(ValueError, match="SIMULATED"):
        WorldTransition(
            transition_id="t",
            initial_state_id="s1",
            resulting_state_id="s2",
            intervention_id="i",
            engine_id="e",
            engine_version="1",
            status=TransitionStatus.SUCCEEDED,
            issues=(),
            applied_parameters={},
            evidence_class=EvidenceClass.MEASURED,
        )
