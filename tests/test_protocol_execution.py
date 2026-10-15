"""Tests for sequential protocol execution over the Phase 2A executor."""
from __future__ import annotations

from food_intelligence import (
    ExperimentProtocol,
    Intervention,
    Quantity,
    WorldComponent,
    WorldState,
    canonical_json,
)
from food_intelligence.protocol_execution import (
    ProtocolExecutionStatus,
    execute_protocol,
)
from food_intelligence.world_execution import InterventionEngine, TransitionStatus


def state() -> WorldState:
    return WorldState(
        "state:initial",
        (WorldComponent("batch:one", "turmeric", "turmeric-raw", Quantity(20, "g")),),
        {
            "temperature": Quantity(25, "degC"),
            "duration": Quantity(0, "min"),
            "humidity": Quantity(None, "%"),
        },
    )


def set_condition(intervention_id: str, condition: str, value: Quantity) -> Intervention:
    return Intervention(
        intervention_id=intervention_id,
        operation="set_condition",
        target_component_ids=("batch:one",),
        parameters={"condition": condition, "value": value},
        preconditions=("component_exists:batch:one",),
    )


def test_protocol_executes_in_order_and_chains_parent_states():
    initial = state()
    protocol = ExperimentProtocol(
        "protocol:two-steps",
        "Two explicit condition updates",
        "1",
        (
            set_condition("step:temperature", "temperature", Quantity(80, "degC")),
            set_condition("step:duration", "duration", Quantity(5, "min")),
        ),
    )

    report = execute_protocol(initial, protocol)

    assert report.status is ProtocolExecutionStatus.SUCCEEDED
    assert len(report.transitions) == 2
    assert all(item.status is TransitionStatus.SUCCEEDED for item in report.transitions)
    assert report.transitions[0].initial_state_id == initial.state_id
    assert report.transitions[1].initial_state_id == report.transitions[0].resulting_state_id
    assert report.final_state is not None
    assert report.final_state.parent_state_id == report.transitions[0].resulting_state_id
    assert report.final_state.conditions["temperature"] == Quantity(80, "degC")
    assert report.final_state.conditions["duration"] == Quantity(5, "min")
    assert report.final_state_id == report.final_state.state_id
    assert report.last_successful_state == report.final_state
    assert report.failed_intervention_id is None
    assert canonical_json(initial) == canonical_json(state())


def test_failure_stops_sequence_and_reports_last_successful_state():
    initial = state()
    protocol = ExperimentProtocol(
        "protocol:failure",
        "Stop after unsupported operation",
        "1",
        (
            set_condition("step:temperature", "temperature", Quantity(80, "degC")),
            Intervention("step:unsupported", "simulate_reaction", ("batch:one",), {}),
            set_condition("step:duration", "duration", Quantity(5, "min")),
        ),
    )

    report = execute_protocol(initial, protocol)

    assert report.status is ProtocolExecutionStatus.FAILED
    assert len(report.transitions) == 2
    assert report.transitions[0].status is TransitionStatus.SUCCEEDED
    assert report.transitions[1].status is TransitionStatus.FAILED
    assert report.failed_intervention_id == "step:unsupported"
    assert report.final_state is None
    assert report.final_state_id is None
    assert report.last_successful_state.conditions["temperature"] == Quantity(80, "degC")
    assert report.last_successful_state.conditions["duration"] == Quantity(0, "min")
    assert report.issues == report.transitions[-1].issues
    assert "OPERATION_UNSUPPORTED" in {issue.code for issue in report.issues}


def test_first_step_failure_keeps_initial_state_as_last_successful():
    initial = state()
    protocol = ExperimentProtocol(
        "protocol:first-fails",
        "First step fails",
        "1",
        (Intervention("bad", "heat", ("batch:one",), {}),),
    )

    report = execute_protocol(initial, protocol)

    assert report.status is ProtocolExecutionStatus.FAILED
    assert report.last_successful_state == initial
    assert report.transitions[0].initial_state_id == initial.state_id
    assert report.final_state is None


def test_empty_protocol_is_deterministic_no_op():
    initial = state()
    protocol = ExperimentProtocol("protocol:empty", "Baseline/no-op", "1", ())
    first = execute_protocol(initial, protocol)
    second = execute_protocol(initial, protocol)

    assert first.status is ProtocolExecutionStatus.SUCCEEDED
    assert first.transitions == ()
    assert first.final_state == initial
    assert first.final_state_id == initial.state_id
    assert first.execution_id == second.execution_id


def test_protocol_replay_and_engine_version_are_deterministic():
    initial = state()
    protocol = ExperimentProtocol(
        "protocol:repeat",
        "Repeatable protocol",
        "1",
        (set_condition("step:temperature", "temperature", Quantity(80, "degC")),),
    )

    one = execute_protocol(initial, protocol, engine=InterventionEngine(version="1.0.0"))
    two = execute_protocol(initial, protocol, engine=InterventionEngine(version="1.0.0"))
    changed_engine = execute_protocol(
        initial, protocol, engine=InterventionEngine(version="1.1.0"),
    )

    assert one.execution_id == two.execution_id
    assert one.final_state_id == two.final_state_id
    assert one.execution_id != changed_engine.execution_id
    assert one.final_state_id != changed_engine.final_state_id


def test_unknown_condition_is_not_used_as_a_default_in_sequence():
    initial = state()
    protocol = ExperimentProtocol(
        "protocol:unknown",
        "Unknown precondition",
        "1",
        (
            Intervention(
                "step:requires-humidity",
                "set_condition",
                ("batch:one",),
                {"condition": "temperature", "value": Quantity(80, "degC")},
                preconditions=("condition_known:humidity",),
            ),
        ),
    )

    report = execute_protocol(initial, protocol)
    assert report.status is ProtocolExecutionStatus.FAILED
    assert report.transitions[0].status is TransitionStatus.FAILED
    assert "PRECONDITION_UNKNOWN" in {issue.code for issue in report.issues}
