"""Hard/soft constraint handling for food-intelligence retrieval."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ConstraintResult:
    allowed: bool
    hard_failures: tuple[str, ...] = ()
    soft_penalties: dict[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()

@dataclass(frozen=True)
class ConstraintSet:
    excluded_entities: frozenset[str] = frozenset()
    required_entities: frozenset[str] = frozenset()
    required_processes: frozenset[str] = frozenset()
    required_cuisine: frozenset[str] = frozenset()
    forbidden_states: frozenset[str] = frozenset()
    allowed_states: frozenset[str] = frozenset()
    safety_required: bool = True
    soft_processes: frozenset[str] = frozenset()

class ConstraintEngine:
    def check(self, entity_id: str, *, state_id: str | None = None,
              processes: set[str] | frozenset[str] = frozenset(),
              cuisines: set[str] | frozenset[str] = frozenset(),
              safety_status: str = "UNASSESSED",
              constraints: ConstraintSet | None = None) -> ConstraintResult:
        c = constraints or ConstraintSet()
        failures: list[str] = []
        reasons: list[str] = []
        if entity_id in c.excluded_entities: failures.append("EXCLUDED_ENTITY")
        if c.required_entities and entity_id not in c.required_entities and entity_id not in c.excluded_entities:
            # required_entities are query-level set constraints and are enforced by the caller;
            # do not reject every candidate when the candidate is merely not the required item.
            pass
        if c.forbidden_states and state_id in c.forbidden_states: failures.append("FORBIDDEN_STATE")
        if c.allowed_states and state_id not in c.allowed_states: failures.append("STATE_NOT_ALLOWED")
        if c.required_processes and not c.required_processes.issubset(set(processes)):
            failures.append("REQUIRED_PROCESS_MISSING")
        if c.required_cuisine and not c.required_cuisine.issubset(set(cuisines)):
            failures.append("REQUIRED_CUISINE_MISSING")
        status = safety_status.upper()
        if c.safety_required and status in {"BLOCKED", "CONTRAINDICATED"}:
            failures.append("HARD_SAFETY_BLOCK")
        elif c.safety_required and status == "UNASSESSED":
            reasons.append("SAFETY_UNASSESSED")
        penalties = {}
        if c.soft_processes:
            missing = c.soft_processes - set(processes)
            if missing: penalties["soft_process"] = len(missing) / len(c.soft_processes)
        return ConstraintResult(not failures, tuple(failures), penalties, tuple(reasons))
