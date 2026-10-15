"""Cross-contract validation and explicit schema migration policy.

This module validates references among canonical world/experiment records. It
does not execute a simulator and does not convert structural validity into
scientific validity.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping

from .units import assert_compatible_units
from .world_contracts import (
    CONTRACTS_VERSION,
    EvidenceRecord,
    ExperimentProtocol,
    ExperimentRecord,
    ExperimentalObservation,
    Hypothesis,
    ObservationStatus,
    WorldState,
)


class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class ContractIssue:
    code: str
    severity: IssueSeverity
    message: str
    subject_id: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise ValueError("issue code and message must be non-empty")
        if not isinstance(self.severity, IssueSeverity):
            raise TypeError("severity must be an IssueSeverity")


@dataclass(frozen=True)
class ContractValidationReport:
    issues: tuple[ContractIssue, ...]

    @property
    def valid(self) -> bool:
        return not any(issue.severity is IssueSeverity.ERROR for issue in self.issues)

    @property
    def errors(self) -> tuple[ContractIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is IssueSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ContractIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is IssueSeverity.WARNING)

    @property
    def info(self) -> tuple[ContractIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is IssueSeverity.INFO)


def validate_experiment_bundle(
    experiment: ExperimentRecord,
    *,
    protocols: Mapping[str, ExperimentProtocol],
    world_states: Mapping[str, WorldState],
    hypotheses: Mapping[str, Hypothesis] | None = None,
    evidence_records: Mapping[str, EvidenceRecord] | None = None,
) -> ContractValidationReport:
    """Validate an experiment against the records it references.

    Missing required references and impossible targets are errors. A completed
    run with no observations and missing optional control context are warnings,
    not proof that the run is scientifically invalid.
    """
    issues: list[ContractIssue] = []
    protocol = protocols.get(experiment.protocol_id)
    state = world_states.get(experiment.initial_state_id)
    hypothesis_map = hypotheses or {}
    evidence_map = evidence_records or {}

    if protocol is None:
        issues.append(ContractIssue(
            "PROTOCOL_NOT_FOUND", IssueSeverity.ERROR,
            f"protocol {experiment.protocol_id!r} is not present in the supplied registry",
            experiment.experiment_id,
        ))
    elif protocol.protocol_id != experiment.protocol_id:
        issues.append(ContractIssue(
            "PROTOCOL_KEY_MISMATCH", IssueSeverity.ERROR,
            "protocol registry key does not match the protocol's own ID",
            experiment.experiment_id,
        ))

    if state is None:
        issues.append(ContractIssue(
            "INITIAL_STATE_NOT_FOUND", IssueSeverity.ERROR,
            f"initial state {experiment.initial_state_id!r} is not present in the supplied registry",
            experiment.experiment_id,
        ))
    elif state.state_id != experiment.initial_state_id:
        issues.append(ContractIssue(
            "STATE_KEY_MISMATCH", IssueSeverity.ERROR,
            "world-state registry key does not match the state's own ID",
            experiment.experiment_id,
        ))

    if experiment.hypothesis_id is not None:
        hypothesis = hypothesis_map.get(experiment.hypothesis_id)
        if hypothesis is None:
            issues.append(ContractIssue(
                "HYPOTHESIS_NOT_FOUND", IssueSeverity.ERROR,
                f"hypothesis {experiment.hypothesis_id!r} is not present in the supplied registry",
                experiment.experiment_id,
            ))
        elif hypothesis.hypothesis_id != experiment.hypothesis_id:
            issues.append(ContractIssue(
                "HYPOTHESIS_KEY_MISMATCH", IssueSeverity.ERROR,
                "hypothesis registry key does not match the hypothesis's own ID",
                experiment.experiment_id,
            ))
        elif evidence_records is not None:
            for evidence_id in hypothesis.evidence_ids:
                if evidence_id not in evidence_map:
                    issues.append(ContractIssue(
                        "HYPOTHESIS_EVIDENCE_NOT_FOUND", IssueSeverity.ERROR,
                        f"hypothesis references unknown evidence {evidence_id!r}",
                        hypothesis.hypothesis_id,
                    ))

    if protocol is not None and state is not None:
        component_ids = {component.component_id for component in state.components}
        for intervention in protocol.interventions:
            for target_id in intervention.target_component_ids:
                if target_id not in component_ids:
                    issues.append(ContractIssue(
                        "INTERVENTION_TARGET_NOT_FOUND", IssueSeverity.ERROR,
                        f"intervention {intervention.intervention_id!r} targets component "
                        f"{target_id!r} absent from initial state {state.state_id!r}",
                        experiment.experiment_id,
                    ))
        condition_names = set(state.conditions)
        for control_name in protocol.control_variables:
            if control_name not in condition_names:
                issues.append(ContractIssue(
                    "CONTROL_VARIABLE_VALUE_MISSING", IssueSeverity.ERROR,
                    f"control variable {control_name!r} has no value in the initial world state",
                    experiment.experiment_id,
                ))

    predictions_by_variable: dict[str, list[Any]] = {}
    for prediction in experiment.predictions:
        predictions_by_variable.setdefault(prediction.variable, []).append(prediction)
    for observation in experiment.observations:
        matching = predictions_by_variable.get(observation.variable, [])
        for prediction in matching:
            if prediction.unit is None or observation.unit is None:
                if prediction.unit != observation.unit:
                    issues.append(ContractIssue(
                        "COMPARISON_UNIT_MISSING", IssueSeverity.WARNING,
                        f"prediction and observation for {observation.variable!r} do not both specify units",
                        experiment.experiment_id,
                    ))
                continue
            try:
                assert_compatible_units(prediction.unit, observation.unit)
            except ValueError as exc:
                if str(exc).startswith("unsupported unit:"):
                    code = "PREDICTION_OBSERVATION_UNIT_UNSUPPORTED"
                    message = str(exc)
                else:
                    code = "PREDICTION_OBSERVATION_UNIT_MISMATCH"
                    message = (
                        f"prediction unit {prediction.unit!r} and observation unit "
                        f"{observation.unit!r} are dimensionally incompatible for "
                        f"{observation.variable!r}"
                    )
                issues.append(ContractIssue(
                    code, IssueSeverity.ERROR, message, experiment.experiment_id,
                ))

        if observation.status is ObservationStatus.OBSERVED and observation.value is None:
            # Normally prevented by the dataclass; retained as a defensive cross-boundary check.
            issues.append(ContractIssue(
                "OBSERVED_VALUE_MISSING", IssueSeverity.ERROR,
                f"observation {observation.observation_id!r} is marked observed without a value",
                experiment.experiment_id,
            ))

    if experiment.status.value == "COMPLETED" and not experiment.observations:
        issues.append(ContractIssue(
            "COMPLETED_WITHOUT_OBSERVATIONS", IssueSeverity.WARNING,
            "experiment is marked completed but contains no observations",
            experiment.experiment_id,
        ))

    if evidence_records is not None:
        for evidence_id, record in evidence_map.items():
            if evidence_id != record.evidence_id:
                issues.append(ContractIssue(
                    "EVIDENCE_KEY_MISMATCH", IssueSeverity.ERROR,
                    "evidence registry key does not match the record's own ID",
                    evidence_id,
                ))
            for parent_id in record.parent_evidence_ids:
                if parent_id not in evidence_map:
                    issues.append(ContractIssue(
                        "PARENT_EVIDENCE_NOT_FOUND", IssueSeverity.ERROR,
                        f"evidence {evidence_id!r} references missing parent {parent_id!r}",
                        evidence_id,
                    ))

    # Deduplicate repeated findings without losing stable ordering.
    unique: dict[tuple[str, str, str, str | None], ContractIssue] = {}
    for issue in issues:
        key = (issue.code, issue.severity.value, issue.message, issue.subject_id)
        unique.setdefault(key, issue)
    return ContractValidationReport(tuple(unique.values()))


Migration = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class SchemaMigrationRegistry:
    """Explicit directed schema migrations; never guesses how data should change.

    A migration is a pure-ish transformation supplied by the caller. Paths are
    selected deterministically by breadth-first search with sorted neighbors.
    The registry intentionally ships with no invented historical migrations.
    """

    def __init__(self, *, current_version: str = CONTRACTS_VERSION) -> None:
        if not current_version.strip():
            raise ValueError("current_version must be non-empty")
        self.current_version = current_version
        self._migrations: dict[tuple[str, str], Migration] = {}

    @property
    def registered_migrations(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._migrations))

    def _neighbors(self, version: str) -> tuple[str, ...]:
        return tuple(sorted(
            target for source, target in self._migrations if source == version
        ))

    def _has_path(self, source: str, target: str) -> bool:
        pending = deque([source])
        visited = {source}
        while pending:
            current = pending.popleft()
            if current == target:
                return True
            for neighbor in self._neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return False

    def register(self, source_version: str, target_version: str, migration: Migration) -> None:
        if not source_version.strip() or not target_version.strip():
            raise ValueError("source and target versions must be non-empty")
        if source_version == target_version:
            raise ValueError("schema migration cannot target its own version")
        if not callable(migration):
            raise TypeError("migration must be callable")
        key = (source_version, target_version)
        if key in self._migrations:
            raise ValueError(f"migration already registered: {source_version}->{target_version}")
        if self._has_path(target_version, source_version):
            raise ValueError("schema migration would create a cycle")
        self._migrations[key] = migration

    def migration_path(self, source_version: str, target_version: str | None = None) -> tuple[tuple[str, str], ...]:
        """Return the deterministic shortest explicit path, or fail closed."""
        target = target_version or self.current_version
        if not source_version.strip() or not target.strip():
            raise ValueError("source and target versions must be non-empty")
        if source_version == target:
            return ()
        pending = deque([(source_version, ())])
        visited = {source_version}
        while pending:
            current, path = pending.popleft()
            for neighbor in self._neighbors(current):
                edge = (current, neighbor)
                next_path = path + (edge,)
                if neighbor == target:
                    return next_path
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append((neighbor, next_path))
        raise ValueError(f"no registered schema migration path: {source_version}->{target}")

    def migrate(
        self,
        payload: Mapping[str, Any],
        source_version: str,
        target_version: str | None = None,
    ) -> dict[str, Any]:
        """Apply each explicitly registered migration without mutating input."""
        current: Mapping[str, Any] = deepcopy(dict(payload))
        for source, target in self.migration_path(source_version, target_version):
            output = self._migrations[(source, target)](deepcopy(dict(current)))
            if not isinstance(output, Mapping):
                raise TypeError(f"migration {source}->{target} must return a mapping")
            current = deepcopy(dict(output))
        return dict(current)
