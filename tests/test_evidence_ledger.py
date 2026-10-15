"""Tests for provenance and evidence lineage invariants."""
import pytest

from food_intelligence.evidence_ledger import (
    EvidenceLedger,
    EvidenceLink,
    EvidenceRelation,
)
from food_intelligence.world_contracts import EvidenceClass, EvidenceRecord


def evidence(
    evidence_id: str,
    *,
    evidence_class: EvidenceClass = EvidenceClass.SIMULATED,
    parents: tuple[str, ...] = (),
    **kwargs,
) -> EvidenceRecord:
    defaults = {
        "source_id": None,
        "source_version": None,
        "license_status": None,
        "source_record_id": None,
        "method": None,
        "conditions": {},
        "observed_at": None,
        "source_uri": None,
        "content_hash": None,
    }
    defaults.update(kwargs)
    return EvidenceRecord(
        evidence_id=evidence_id,
        evidence_class=evidence_class,
        description=f"Evidence {evidence_id}",
        parent_evidence_ids=parents,
        **defaults,
    )


def test_add_record_is_idempotent_but_rejects_id_collision() -> None:
    ledger = EvidenceLedger()
    record = evidence("e1")
    ledger.add_record(record)
    ledger.add_record(record)
    assert len(ledger.records) == 1
    with pytest.raises(ValueError, match="ID collision"):
        ledger.add_record(EvidenceRecord("e1", EvidenceClass.SIMULATED, "different claim"))


def test_source_based_evidence_requires_source_identity() -> None:
    with pytest.raises(ValueError, match="source_id"):
        evidence("measured-1", evidence_class=EvidenceClass.MEASURED)


def test_measured_evidence_requires_source_record_identity() -> None:
    with pytest.raises(ValueError, match="source_record_id"):
        evidence(
            "measured-1",
            evidence_class=EvidenceClass.MEASURED,
            source_id="lab",
        )


def test_audit_warns_when_source_metadata_is_incomplete() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(
        evidence(
            "measurement",
            evidence_class=EvidenceClass.MEASURED,
            source_id="lab",
            source_record_id="run-3",
        )
    )
    audit = ledger.audit()
    assert audit.valid
    assert {
        "SOURCE_VERSION_MISSING",
        "LICENSE_STATUS_MISSING",
        "MEASUREMENT_METHOD_MISSING",
        "OBSERVATION_TIME_MISSING",
    } <= {issue.code for issue in audit.warnings}


def test_complete_measured_evidence_has_no_metadata_warnings() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(
        evidence(
            "measurement",
            evidence_class=EvidenceClass.MEASURED,
            source_id="lab",
            source_version="instrument-method-v2",
            license_status="internal_authorized",
            source_record_id="run-3",
            method="GC-MS",
            observed_at="2026-10-15T10:00:00Z",
            conditions={"matrix": "heated oil"},
        )
    )
    assert ledger.audit().warnings == ()


def test_missing_parent_is_reported_as_error() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(evidence("derived", parents=("missing-parent",)))
    audit = ledger.audit()
    assert not audit.valid
    assert any(issue.code == "PARENT_EVIDENCE_MISSING" for issue in audit.issues)


def test_parent_lineage_is_transitive_and_deterministic() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(evidence("raw"))
    ledger.add_record(evidence("cleaned", parents=("raw",)))
    ledger.add_record(evidence("feature", parents=("cleaned",)))
    assert ledger.lineage("feature") == ("cleaned", "raw")


def test_parent_lineage_cycle_is_rejected() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(evidence("a", parents=("b",)))
    with pytest.raises(ValueError, match="lineage cycle"):
        ledger.add_record(evidence("b", parents=("a",)))


def test_derived_from_link_cycle_is_rejected() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(evidence("a"))
    ledger.add_record(evidence("b"))
    ledger.add_link(EvidenceLink("a", EvidenceRelation.DERIVED_FROM, "b"))
    with pytest.raises(ValueError, match="cycle"):
        ledger.add_link(EvidenceLink("b", EvidenceRelation.DERIVED_FROM, "a"))


def test_contradictory_evidence_is_preserved_without_auto_resolution() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(evidence("study-a"))
    ledger.add_record(evidence("study-b"))
    link = EvidenceLink(
        "study-a", EvidenceRelation.CONTRADICTS, "study-b",
        rationale="Opposing outcomes under apparently similar conditions.",
    )
    ledger.add_link(link)
    assert ledger.contradiction_pairs() == (link,)
    assert ledger.related("study-a", relation=EvidenceRelation.CONTRADICTS) == (link,)


def test_links_require_existing_endpoints() -> None:
    ledger = EvidenceLedger()
    ledger.add_record(evidence("present"))
    with pytest.raises(KeyError, match="unknown target"):
        ledger.add_link(EvidenceLink("present", EvidenceRelation.SUPPORTS, "absent"))


def test_self_links_are_invalid() -> None:
    with pytest.raises(ValueError, match="cannot link to itself"):
        EvidenceLink("same", EvidenceRelation.CONTRADICTS, "same")
