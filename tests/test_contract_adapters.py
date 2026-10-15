"""Phase 1B regression tests for legacy/canonical contract reconciliation."""
import pytest

from food_intelligence.contract_adapters import (
    canonical_process_id,
    canonical_state_id,
    legacy_observation_to_contract,
    legacy_provenance_to_evidence,
    legacy_sensory_profile_to_observations,
    preserve_entity_id,
)
from food_intelligence.representation import Observation, Provenance, SensoryProfile
from food_intelligence.world_contracts import EvidenceClass, ObservationStatus


def provenance(*, evidence_type="SOURCE_DERIVED", data_status="REAL", source_record_id="row-7"):
    return Provenance(
        source_id="dataset-a",
        source_name="Dataset A",
        source_version="v2",
        source_record_id=source_record_id,
        retrieval_date="2026-10-15",
        license_status="reviewed",
        processing_version="p1",
        mapping_version="m1",
        confidence=0.8,
        evidence_type=evidence_type,
        data_status=data_status,
        evidence_id=None,
    )


def test_existing_entity_ids_are_preserved_without_renaming():
    assert preserve_entity_id("ingredient:turmeric", entity_kind="ingredient") == "ingredient:turmeric"
    with pytest.raises(ValueError, match="surrounding whitespace"):
        preserve_entity_id(" turmeric ", entity_kind="ingredient")


def test_curated_state_ids_are_deterministic_and_ingredient_scoped():
    assert canonical_state_id("turmeric", "Raw") == canonical_state_id("turmeric", " raw ")
    assert canonical_state_id("turmeric", "raw") != canonical_state_id("ginger", "raw")
    assert canonical_state_id("turmeric", "raw") != canonical_state_id("turmeric", "ground")


def test_process_id_adapter_uses_existing_process_normalization():
    assert canonical_process_id("Deep Fry") == "deep_fry"
    assert canonical_process_id("shallow-fry") == "shallow_fry"
    with pytest.raises(ValueError, match="non-empty"):
        canonical_process_id("  ")
    with pytest.raises(ValueError, match="unknown process"):
        canonical_process_id("teleport")


def test_legacy_source_provenance_preserves_source_record_and_parents():
    legacy = provenance()
    evidence = legacy_provenance_to_evidence(legacy)
    assert evidence.evidence_class is EvidenceClass.SOURCE_DERIVED
    assert evidence.source_id == "dataset-a"
    assert evidence.source_record_id == "row-7"
    assert evidence.license_status == "reviewed"


def test_legacy_synthetic_fixture_is_not_promoted_to_scientific_evidence():
    evidence = legacy_provenance_to_evidence(
        provenance(evidence_type="SOURCE_DERIVED", data_status="SYNTHETIC", source_record_id=None)
    )
    assert evidence.evidence_class is EvidenceClass.SYNTHETIC_FIXTURE
    assert "not scientific or physical evidence" in evidence.limitations[0]


def test_experimentally_validated_provenance_requires_source_record():
    with pytest.raises(ValueError, match="source_record_id"):
        legacy_provenance_to_evidence(
            provenance(evidence_type="EXPERIMENTALLY_VALIDATED", source_record_id=None)
        )


def test_legacy_observation_conversion_preserves_unknown_as_not_measured():
    legacy = Observation(
        descriptor="aroma_intensity",
        value=None,
        observed=False,
        measurement_method="sensory_panel",
        provenance=provenance(),
    )
    converted = legacy_observation_to_contract(legacy, observation_id="obs-1")
    assert converted.status is ObservationStatus.NOT_MEASURED
    assert converted.value is None
    assert converted.method == "sensory_panel"


def test_legacy_observation_refuses_ambiguous_missingness_and_missing_method():
    with pytest.raises(ValueError, match="observed=True but no value"):
        legacy_observation_to_contract(
            Observation("odor", value=None, observed=True, provenance=provenance()),
            observation_id="obs-2",
            method="panel",
        )
    with pytest.raises(ValueError, match="method is missing"):
        legacy_observation_to_contract(
            Observation("odor", value=0.5, provenance=provenance()),
            observation_id="obs-3",
        )


def test_observation_without_provenance_requires_explicit_evidence_class():
    legacy = Observation("viscosity", value=2.0, observed=True, measurement_method="viscometer")
    with pytest.raises(ValueError, match="requires evidence_class"):
        legacy_observation_to_contract(legacy, observation_id="obs-4")
    converted = legacy_observation_to_contract(
        legacy,
        observation_id="obs-4",
        evidence_class=EvidenceClass.SIMULATED,
        unit="Pa.s",
    )
    assert converted.evidence_class is EvidenceClass.SIMULATED
    assert converted.value == 2.0
    assert converted.unit == "Pa.s"


def test_sensory_profile_keeps_modalities_separate():
    source = provenance()
    profile = SensoryProfile(
        ingredient_id="ginger",
        state_id="ginger:raw",
        taste=(Observation("pungent", 0.7, measurement_method="panel", provenance=source),),
        odor=(Observation("pungent", 0.6, measurement_method="panel", provenance=source),),
    )
    converted = legacy_sensory_profile_to_observations(profile)
    assert len(converted) == 2
    assert {x.variable for x in converted} == {"pungent"}
    assert len({x.observation_id for x in converted}) == 2
