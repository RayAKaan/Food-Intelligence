"""Sequential execution of declared intervention protocols.

This orchestration layer composes the deterministic Phase 2A executor. It does
not simulate food physics and does not produce experimental observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .world_contracts import ExperimentProtocol, WorldState, stable_id
from .world_execution import (
    InterventionEngine,
    TransitionIssue,
    TransitionStatus,
    WorldTransition,
    execute_intervention,
)


class ProtocolExecutionStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ProtocolExecutionReport:
    """Audit record for a sequential protocol execution attempt.

    `final_state` is populated only when every intervention succeeds.
    `last_successful_state` always identifies the last state reached before
    completion or failure, making partial progress explicit rather than hiding
    it or mislabeling it as a completed protocol.
    """

    execution_id: str
    protocol_id: str
    protocol_version: str
    initial_state_id: str
    final_state_id: str | None
    status: ProtocolExecutionStatus
    transitions: tuple[WorldTransition, ...]
    final_state: WorldState | None
    last_successful_state: WorldState
    failed_intervention_id: str | None = None
    issues: tuple[TransitionIssue, ...] = ()
    limitations: tuple[str, ...] = (
        "Sequential deterministic bookkeeping only; no food dynamics or measurements are produced.",
    )

    def __post_init__(self) -> None:
        for name in (
            "execution_id", "protocol_id", "protocol_version", "initial_state_id",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.status is ProtocolExecutionStatus.SUCCEEDED:
            if self.final_state is None or self.final_state_id != self.final_state.state_id:
                raise ValueError("successful protocol execution requires its final state")
            if self.failed_intervention_id is not None or self.issues:
                raise ValueError("successful protocol execution cannot carry failure details")
        else:
            if self.final_state is not None or self.final_state_id is not None:
                raise ValueError("failed protocol execution cannot claim a final state")
            if self.failed_intervention_id is None or not self.issues:
                raise ValueError("failed protocol execution requires failure details")
        if self.last_successful_state.state_id == "":
            raise ValueError("last_successful_state must have a valid ID")
        if self.transitions and self.transitions[-1].status is TransitionStatus.FAILED:
            if self.status is not ProtocolExecutionStatus.FAILED:
                raise ValueError("failed transition requires failed protocol status")


def execute_protocol(
    initial_state: WorldState,
    protocol: ExperimentProtocol,
    *,
    engine: InterventionEngine | None = None,
) -> ProtocolExecutionReport:
    """Execute interventions in declaration order, stopping on first failure.

    Successful intermediate states remain auditable in `transitions` and
    `last_successful_state`. If any intervention fails, `final_state` is
    deliberately None: callers must explicitly decide whether to resume,
    compensate, or discard the partial run. This function does not roll back
    external side effects because the built-in executor has none.
    """
    current_state = initial_state
    transitions: list[WorldTransition] = []
    failed_intervention_id: str | None = None
    issues: tuple[TransitionIssue, ...] = ()
    status = ProtocolExecutionStatus.SUCCEEDED

    for intervention in protocol.interventions:
        next_state, transition = execute_intervention(
            current_state, intervention, engine=engine,
        )
        transitions.append(transition)
        if next_state is None or transition.status is TransitionStatus.FAILED:
            status = ProtocolExecutionStatus.FAILED
            failed_intervention_id = intervention.intervention_id
            issues = transition.issues
            break
        current_state = next_state

    final_state = current_state if status is ProtocolExecutionStatus.SUCCEEDED else None
    final_state_id = final_state.state_id if final_state is not None else None
    execution_payload = {
        "protocol_id": protocol.protocol_id,
        "protocol_version": protocol.version,
        "initial_state_id": initial_state.state_id,
        "status": status.value,
        "transition_ids": tuple(item.transition_id for item in transitions),
        "final_state_id": final_state_id,
        "failed_intervention_id": failed_intervention_id,
        "issues": issues,
    }
    return ProtocolExecutionReport(
        execution_id=stable_id("protocol_execution", execution_payload),
        protocol_id=protocol.protocol_id,
        protocol_version=protocol.version,
        initial_state_id=initial_state.state_id,
        final_state_id=final_state_id,
        status=status,
        transitions=tuple(transitions),
        final_state=final_state,
        last_successful_state=current_state,
        failed_intervention_id=failed_intervention_id,
        issues=issues,
    )
