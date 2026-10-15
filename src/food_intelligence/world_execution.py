"""Deterministic, deliberately limited world-state intervention execution.

This module applies only explicit bookkeeping operations. It does not model
heating, chemistry, sensory outcomes, microbial growth, or food safety.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .units import assert_compatible_units, convert_quantity
from .world_contracts import (
    CONTRACTS_VERSION,
    EvidenceClass,
    Intervention,
    Quantity,
    WorldState,
    stable_id,
)


class TransitionStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class TransitionIssue:
    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise ValueError("transition issue code and message must be non-empty")


@dataclass(frozen=True)
class WorldTransition:
    """Auditable result of one attempted state transition."""

    transition_id: str
    initial_state_id: str
    resulting_state_id: str | None
    intervention_id: str
    engine_id: str
    engine_version: str
    status: TransitionStatus
    issues: tuple[TransitionIssue, ...]
    applied_parameters: Mapping[str, Quantity]
    evidence_class: EvidenceClass = EvidenceClass.SIMULATED
    limitations: tuple[str, ...] = (
        "Deterministic bookkeeping executor only; no food dynamics are simulated.",
    )

    def __post_init__(self) -> None:
        for name in (
            "transition_id", "initial_state_id", "intervention_id",
            "engine_id", "engine_version",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.status is TransitionStatus.SUCCEEDED and self.resulting_state_id is None:
            raise ValueError("successful transition requires resulting_state_id")
        if self.status is TransitionStatus.FAILED and self.resulting_state_id is not None:
            raise ValueError("failed transition cannot claim a resulting state")
        if self.evidence_class is not EvidenceClass.SIMULATED:
            raise ValueError("world executor transitions must remain SIMULATED")
        object.__setattr__(self, "applied_parameters", dict(self.applied_parameters))


@dataclass(frozen=True)
class InterventionEngine:
    """Identity/version for the built-in allowlisted deterministic executor.

    Operation semantics are defined in this module, not loaded from input.
    Adding a new operation requires a reviewed code change and tests.
    """

    engine_id: str = "food-intelligence.bookkeeping"
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not self.engine_id.strip() or not self.version.strip():
            raise ValueError("engine_id and version must be non-empty")


def _precondition_result(
    expression: str, state: WorldState
) -> tuple[bool | None, TransitionIssue | None]:
    """Evaluate the tiny, explicit predicate grammar; None means UNKNOWN."""
    if expression.startswith("component_exists:"):
        component_id = expression.removeprefix("component_exists:")
        if not component_id.strip():
            return None, TransitionIssue("PRECONDITION_INVALID", "component_exists requires an ID")
        return (
            any(component.component_id == component_id for component in state.components),
            None,
        )
    if expression.startswith("condition_known:"):
        name = expression.removeprefix("condition_known:")
        if not name.strip():
            return None, TransitionIssue("PRECONDITION_INVALID", "condition_known requires a name")
        quantity = state.conditions.get(name)
        if quantity is None or quantity.value is None:
            return None, None
        return True, None
    return None, TransitionIssue(
        "PRECONDITION_UNSUPPORTED",
        f"unsupported precondition syntax: {expression!r}",
    )


def execute_intervention(
    initial_state: WorldState,
    intervention: Intervention,
    *,
    engine: InterventionEngine | None = None,
) -> tuple[WorldState | None, WorldTransition]:
    """Execute one allowlisted operation without mutating the initial state.

    Supported operation:
      - set_condition: parameters must contain a non-empty string condition
        and a unit-bearing Quantity value. The condition must already exist;
        values are converted to its declared unit.

    Preconditions are restricted to component_exists:<id> and
    condition_known:<name>. Unknown condition values fail closed.
    """
    selected_engine = engine or InterventionEngine()
    issues: list[TransitionIssue] = []
    applied: dict[str, Quantity] = {}
    result_state: WorldState | None = None

    if initial_state.schema_version != CONTRACTS_VERSION:
        issues.append(TransitionIssue(
            "SCHEMA_VERSION_UNSUPPORTED",
            f"state schema {initial_state.schema_version!r} is not supported by "
            f"executor contract {CONTRACTS_VERSION!r}",
        ))

    component_ids = {component.component_id for component in initial_state.components}
    for target_id in intervention.target_component_ids:
        if target_id not in component_ids:
            issues.append(TransitionIssue(
                "TARGET_COMPONENT_NOT_FOUND",
                f"target component {target_id!r} does not exist in state {initial_state.state_id!r}",
            ))

    for expression in intervention.preconditions:
        result, issue = _precondition_result(expression, initial_state)
        if issue is not None:
            issues.append(issue)
        elif result is None:
            issues.append(TransitionIssue(
                "PRECONDITION_UNKNOWN",
                f"precondition {expression!r} could not be established from known state",
            ))
        elif not result:
            issues.append(TransitionIssue(
                "PRECONDITION_FAILED",
                f"precondition {expression!r} is false for the initial state",
            ))

    proposed_condition: str | None = None
    proposed_value: Quantity | None = None
    if intervention.operation != "set_condition":
        issues.append(TransitionIssue(
            "OPERATION_UNSUPPORTED",
            f"operation {intervention.operation!r} is not in the executor allowlist",
        ))
    else:
        condition = intervention.parameters.get("condition")
        value = intervention.parameters.get("value")
        if not isinstance(condition, str) or not condition.strip():
            issues.append(TransitionIssue(
                "PARAMETER_INVALID", "set_condition requires a non-empty string condition",
            ))
        elif not isinstance(value, Quantity):
            issues.append(TransitionIssue(
                "PARAMETER_INVALID", "set_condition requires a unit-bearing Quantity value",
            ))
        else:
            proposed_condition = condition
            proposed_value = value
            existing = initial_state.conditions.get(condition)
            if existing is None:
                issues.append(TransitionIssue(
                    "CONDITION_NOT_FOUND",
                    f"condition {condition!r} is not declared in the initial state",
                ))
            else:
                try:
                    assert_compatible_units(value.unit, existing.unit)
                    proposed_value = convert_quantity(value, existing.unit)
                    applied[condition] = proposed_value
                except ValueError as exc:
                    issues.append(TransitionIssue("PARAMETER_UNIT_INVALID", str(exc)))

    if not issues and proposed_condition is not None and proposed_value is not None:
        new_conditions = dict(initial_state.conditions)
        new_conditions[proposed_condition] = proposed_value
        state_payload = {
            "initial_state": initial_state,
            "intervention": intervention,
            "engine_id": selected_engine.engine_id,
            "engine_version": selected_engine.version,
            "applied_parameters": applied,
        }
        resulting_state_id = stable_id("world_state", state_payload)
        result_state = WorldState(
            state_id=resulting_state_id,
            components=initial_state.components,
            conditions=new_conditions,
            schema_version=initial_state.schema_version,
            parent_state_id=initial_state.state_id,
        )
        status = TransitionStatus.SUCCEEDED
    else:
        status = TransitionStatus.FAILED
        applied = {}
        resulting_state_id = None

    transition_payload = {
        "initial_state_id": initial_state.state_id,
        "intervention": intervention,
        "engine_id": selected_engine.engine_id,
        "engine_version": selected_engine.version,
        "status": status,
        "resulting_state_id": resulting_state_id,
        "issues": tuple(issues),
        "applied_parameters": applied,
    }
    transition = WorldTransition(
        transition_id=stable_id("world_transition", transition_payload),
        initial_state_id=initial_state.state_id,
        resulting_state_id=resulting_state_id,
        intervention_id=intervention.intervention_id,
        engine_id=selected_engine.engine_id,
        engine_version=selected_engine.version,
        status=status,
        issues=tuple(issues),
        applied_parameters=applied,
    )
    return result_state, transition
