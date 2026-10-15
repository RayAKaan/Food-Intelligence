"""Provenance-aware evidence ledger and lineage validation.

The ledger stores claims and their relationships without treating source
presence as scientific truth. Contradictions are preserved, never auto-resolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .world_contracts import EvidenceClass, EvidenceRecord, stable_id


class EvidenceRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    DERIVED_FROM = "DERIVED_FROM"
    CORROBORATES = "CORROBORATES"
    DUPLICATES = "DUPLICATES"


@dataclass(frozen=True)
class EvidenceLink:
    """A typed relationship between two evidence records."""
    source_evidence_id: str
    relation: EvidenceRelation
    target_evidence_id: str
    rationale: str | None = None
    link_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_evidence_id.strip() or not self.target_evidence_id.strip():
            raise ValueError("evidence link endpoints must be non-empty")
        if self.source_evidence_id == self.target_evidence_id:
            raise ValueError("evidence cannot link to itself")
        if not isinstance(self.relation, EvidenceRelation):
            raise TypeError("relation must be an EvidenceRelation")
        if self.rationale is not None and not self.rationale.strip():
            raise ValueError("rationale must be non-empty when supplied")
        if self.link_id is None:
            object.__setattr__(
                self,
                "link_id",
                stable_id(
                    "evidence_link",
                    {
                        "source": self.source_evidence_id,
                        "relation": self.relation.value,
                        "target": self.target_evidence_id,
                        "rationale": self.rationale,
                    },
                ),
            )


@dataclass(frozen=True)
class EvidenceIssue:
    code: str
    severity: str
    message: str
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in {"INFO", "WARNING", "ERROR"}:
            raise ValueError("severity must be INFO, WARNING, or ERROR")


@dataclass(frozen=True)
class EvidenceAudit:
    record_count: int
    link_count: int
    issues: tuple[EvidenceIssue, ...]

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "ERROR" for issue in self.issues)

    @property
    def warnings(self) -> tuple[EvidenceIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "WARNING")


class EvidenceLedger:
    """In-memory evidence index with referential and lineage checks.

    This is a contract-level component, not durable storage. Persisting the
    ledger belongs to the experimental-memory phase.
    """

    def __init__(self) -> None:
        self.records: dict[str, EvidenceRecord] = {}
        self.links: dict[str, EvidenceLink] = {}

    def _parent_map(
        self,
        *,
        extra_record: EvidenceRecord | None = None,
        extra_link: EvidenceLink | None = None,
    ) -> dict[str, set[str]]:
        records = dict(self.records)
        if extra_record is not None:
            records[extra_record.evidence_id] = extra_record
        links = dict(self.links)
        if extra_link is not None and extra_link.relation is EvidenceRelation.DERIVED_FROM:
            links[extra_link.link_id or ""] = extra_link

        parents: dict[str, set[str]] = {key: set() for key in records}
        for evidence_id, record in records.items():
            parents[evidence_id].update(
                parent_id for parent_id in record.parent_evidence_ids if parent_id in records
            )
        for link in links.values():
            if link.relation is EvidenceRelation.DERIVED_FROM:
                if link.source_evidence_id in records and link.target_evidence_id in records:
                    parents[link.source_evidence_id].add(link.target_evidence_id)
        return parents

    @staticmethod
    def _has_cycle(parents: dict[str, set[str]]) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for parent in parents.get(node, ()):
                if visit(parent):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in parents if node not in visited)

    def add_record(self, record: EvidenceRecord) -> None:
        """Add a record idempotently; reject ID collisions and lineage cycles."""
        existing = self.records.get(record.evidence_id)
        if existing is not None:
            if existing != record:
                raise ValueError(f"evidence ID collision: {record.evidence_id}")
            return
        if any(parent == record.evidence_id for parent in record.parent_evidence_ids):
            raise ValueError("evidence cannot derive from itself")
        parents = self._parent_map(extra_record=record)
        if self._has_cycle(parents):
            raise ValueError(f"evidence lineage cycle: {record.evidence_id}")
        self.records[record.evidence_id] = record

    def add_link(self, link: EvidenceLink) -> None:
        """Add a relationship after validating both endpoints and lineage."""
        if link.source_evidence_id not in self.records:
            raise KeyError(f"unknown source evidence: {link.source_evidence_id}")
        if link.target_evidence_id not in self.records:
            raise KeyError(f"unknown target evidence: {link.target_evidence_id}")
        link_id = link.link_id or ""
        existing = self.links.get(link_id)
        if existing is not None:
            if existing != link:
                raise ValueError(f"evidence link ID collision: {link_id}")
            return
        if link.relation is EvidenceRelation.DERIVED_FROM:
            parents = self._parent_map(extra_link=link)
            if self._has_cycle(parents):
                raise ValueError("DERIVED_FROM link would create a lineage cycle")
        self.links[link_id] = link

    def lineage(self, evidence_id: str) -> tuple[str, ...]:
        """Return transitive ancestors in deterministic order; exclude the record itself."""
        if evidence_id not in self.records:
            raise KeyError(f"unknown evidence: {evidence_id}")
        parents = self._parent_map()
        found: set[str] = set()
        pending = list(parents.get(evidence_id, ()))
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found.add(current)
            pending.extend(parents.get(current, ()))
        return tuple(sorted(found))

    def related(
        self,
        evidence_id: str,
        *,
        relation: EvidenceRelation | None = None,
    ) -> tuple[EvidenceLink, ...]:
        if evidence_id not in self.records:
            raise KeyError(f"unknown evidence: {evidence_id}")
        return tuple(
            sorted(
                (
                    link for link in self.links.values()
                    if evidence_id in {link.source_evidence_id, link.target_evidence_id}
                    and (relation is None or link.relation is relation)
                ),
                key=lambda link: link.link_id or "",
            )
        )

    def audit(self) -> EvidenceAudit:
        """Report missing metadata and broken lineage without inventing values."""
        issues: list[EvidenceIssue] = []
        for evidence_id, record in sorted(self.records.items()):
            source_based = record.evidence_class in {
                EvidenceClass.MEASURED, EvidenceClass.SOURCE_DERIVED
            }
            if source_based and not record.source_version:
                issues.append(EvidenceIssue(
                    "SOURCE_VERSION_MISSING", "WARNING",
                    "Source version is not recorded.", evidence_id,
                ))
            if source_based and not record.license_status:
                issues.append(EvidenceIssue(
                    "LICENSE_STATUS_MISSING", "WARNING",
                    "License status is not recorded; use must not be assumed permitted.",
                    evidence_id,
                ))
            if record.evidence_class is EvidenceClass.MEASURED and not record.method:
                issues.append(EvidenceIssue(
                    "MEASUREMENT_METHOD_MISSING", "WARNING",
                    "Measurement method is not recorded.", evidence_id,
                ))
            if record.evidence_class is EvidenceClass.MEASURED and not record.observed_at:
                issues.append(EvidenceIssue(
                    "OBSERVATION_TIME_MISSING", "WARNING",
                    "Observation timestamp is not recorded.", evidence_id,
                ))
            for parent_id in record.parent_evidence_ids:
                if parent_id not in self.records:
                    issues.append(EvidenceIssue(
                        "PARENT_EVIDENCE_MISSING", "ERROR",
                        f"Referenced parent evidence does not exist: {parent_id}",
                        evidence_id,
                    ))
        for link in self.links.values():
            if link.source_evidence_id not in self.records or link.target_evidence_id not in self.records:
                issues.append(EvidenceIssue(
                    "LINK_ENDPOINT_MISSING", "ERROR",
                    "Evidence link references a missing record.", link.source_evidence_id,
                ))
        if self._has_cycle(self._parent_map()):
            issues.append(EvidenceIssue(
                "LINEAGE_CYCLE", "ERROR",
                "Evidence derivation lineage contains a cycle.",
            ))
        return EvidenceAudit(len(self.records), len(self.links), tuple(issues))

    def contradiction_pairs(self) -> tuple[EvidenceLink, ...]:
        """Return recorded contradictions; do not choose a winning claim."""
        return tuple(
            sorted(
                (link for link in self.links.values()
                 if link.relation is EvidenceRelation.CONTRADICTS),
                key=lambda link: link.link_id or "",
            )
        )


__all__ = [
    "EvidenceAudit",
    "EvidenceIssue",
    "EvidenceLedger",
    "EvidenceLink",
    "EvidenceRelation",
]
