"""Explicit adapters between legacy food records and canonical world contracts.

Adapters preserve source IDs and fail closed when a legacy record lacks enough
information for a faithful conversion. They never infer a scientific result.
"""
from __future__ import annotations

from .representation import Observation, Provenance, SensoryProfile
from .transformations import PROCESS_VOCABULARY, normalize_process
from .world_contracts import (
    EvidenceClass,
    EvidenceRecord,
    ExperimentalObservation,
    ObservationStatus,
    stable_id,
)

_LEGACY_EVIDENCE_MAP = {
    "FACT": EvidenceClass.SOURCE_DERIVED,
    "SOURCE_DERIVED": EvidenceClass.SOURCE_DERIVED,
    "INFERENCE": EvidenceClass.INFERRED,
    "MODEL_PREDICTION": EvidenceClass.INFERRED,
    "HYPOTHESIS": EvidenceClass.HYPOTHESIS,
}


def preserve_entity_id(value: str, *, entity_kind: str) -> str:
    """Validate an existing identifier without renaming or normalizing it."""
    if not entity_kind.strip():
        raise ValueError("entity_kind must be non-empty")
    if not value or not value.strip():
        raise ValueError(f"{entity_kind} ID must be non-empty")
    if value != value.strip():
        raise ValueError(f"{entity_kind} ID has surrounding whitespace; migrate explicitly")
    return value


def canonical_state_id(ingredient_id: str, curated_state_label: str) -> str:
    """Derive a stable ID from an ingredient ID and curated state label.

    Use only for a controlled, curated label (for example, raw or ground).
    Existing persisted state IDs should be preserved, not replaced.
    """
    ingredient_id = preserve_entity_id(ingredient_id, entity_kind="ingredient")
    if not curated_state_label or not curated_state_label.strip():
        raise ValueError("curated_state_label must be non-empty")
    label = " ".join(curated_state_label.casefold().replace("-", " ").split())
    return stable_id(
        "ingredient_state",
        {"ingredient_id": ingredient_id, "curated_state_label": label},
    )


def canonical_process_id(legacy_process_id: str) -> str:
    """Use the process vocabulary's normalization without inventing a process."""
    if not legacy_process_id or not legacy_process_id.strip():
        raise ValueError("process ID must be non-empty")
    process_id = normalize_process(legacy_process_id)
    if process_id not in PROCESS_VOCABULARY:
        raise ValueError(f"unknown process ID: {legacy_process_id}")
    return process_id


def legacy_provenance_to_evidence(provenance: Provenance) -> EvidenceRecord:
    """Convert legacy provenance while preserving its evidence boundary."""
    if provenance.data_status == "SYNTHETIC":
        evidence_class = EvidenceClass.SYNTHETIC_FIXTURE
        limitations = (
            "Originated as legacy synthetic data; not scientific or physical evidence.",
        )
    elif provenance.data_status == "MODEL_DERIVED":
        evidence_class = (
            EvidenceClass.HYPOTHESIS
            if provenance.evidence_type == "HYPOTHESIS"
            else EvidenceClass.INFERRED
        )
        limitations = ("Legacy model-derived record; retain model limitations separately.",)
    else:
        try:
            evidence_class = _LEGACY_EVIDENCE_MAP[provenance.evidence_type]
        except KeyError:
            if provenance.evidence_type == "EXPERIMENTALLY_VALIDATED":
                evidence_class = EvidenceClass.MEASURED
            else:
                raise ValueError(
                    f"unsupported legacy evidence type: {provenance.evidence_type}"
                ) from None
        limitations = ()

    if evidence_class in {EvidenceClass.SOURCE_DERIVED, EvidenceClass.MEASURED}:
        if not provenance.source_id or not provenance.source_id.strip():
            raise ValueError("source-derived evidence requires a legacy source_id")
    if evidence_class is EvidenceClass.MEASURED and not provenance.source_record_id:
        raise ValueError(
            "experimentally validated provenance requires source_record_id"
        )

    evidence_id = provenance.evidence_id or stable_id(
        "evidence",
        {
            "source_id": provenance.source_id,
            "source_record_id": provenance.source_record_id,
            "source_version": provenance.source_version,
            "retrieval_date": provenance.retrieval_date,
            "processing_version": provenance.processing_version,
            "mapping_version": provenance.mapping_version,
            "evidence_type": provenance.evidence_type,
            "data_status": provenance.data_status,
        },
    )
    return EvidenceRecord(
        evidence_id=evidence_id,
        evidence_class=evidence_class,
        description=(
            f"Legacy provenance from {provenance.source_name}; "
            f"legacy evidence_type={provenance.evidence_type}; "
            f"confidence={provenance.confidence!r}; "
            f"processing_version={provenance.processing_version}; "
            f"mapping_version={provenance.mapping_version}; "
            f"retrieval_date={provenance.retrieval_date!r}"
        ),
        source_id=provenance.source_id or None,
        source_version=provenance.source_version,
        license_status=provenance.license_status,
        parent_evidence_ids=provenance.parent_evidence_ids,
        limitations=limitations,
        source_record_id=provenance.source_record_id,
    )


def legacy_observation_to_contract(
    observation: Observation,
    *,
    observation_id: str,
    method: str | None = None,
    unit: str | None = None,
    evidence_class: EvidenceClass | None = None,
    source_record_id: str | None = None,
) -> ExperimentalObservation:
    """Convert a legacy observation only when method and evidence are explicit."""
    if not observation_id or not observation_id.strip():
        raise ValueError("observation_id must be non-empty")
    resolved_method = method or observation.measurement_method
    if not resolved_method or not resolved_method.strip():
        raise ValueError(
            "measurement method is missing; supply method rather than inventing one"
        )

    provenance = observation.provenance
    if provenance is not None:
        evidence = legacy_provenance_to_evidence(provenance)
        if evidence_class is not None and evidence_class is not evidence.evidence_class:
            raise ValueError("explicit evidence_class conflicts with legacy provenance")
        resolved_evidence_class = evidence.evidence_class
        resolved_source_record_id = source_record_id or provenance.source_record_id
    else:
        if evidence_class is None:
            raise ValueError("observation without provenance requires evidence_class")
        resolved_evidence_class = evidence_class
        resolved_source_record_id = source_record_id

    if not observation.observed:
        status = ObservationStatus.NOT_MEASURED
        value = None
    else:
        if observation.value is None:
            raise ValueError(
                "legacy observation has observed=True but no value; resolve missingness explicitly"
            )
        status = ObservationStatus.OBSERVED
        value = observation.value

    return ExperimentalObservation(
        observation_id=observation_id,
        variable=observation.descriptor,
        value=value,
        unit=unit,
        status=status,
        evidence_class=resolved_evidence_class,
        method=resolved_method,
        source_record_id=resolved_source_record_id,
        conditions={"legacy_context": observation.context} if observation.context else {},
    )


def legacy_sensory_profile_to_observations(
    profile: SensoryProfile,
    *,
    method_by_modality: dict[str, str] | None = None,
) -> tuple[ExperimentalObservation, ...]:
    """Convert sensory descriptors while keeping modalities and IDs distinct."""
    methods = method_by_modality or {}
    converted: list[ExperimentalObservation] = []
    for modality in ("taste", "odor", "texture", "physical"):
        for item in getattr(profile, modality):
            method = methods.get(modality) or item.measurement_method
            observation_id = stable_id(
                "observation",
                {
                    "ingredient_id": profile.ingredient_id,
                    "state_id": profile.state_id,
                    "modality": modality,
                    "descriptor": item.descriptor,
                },
            )
            converted.append(
                legacy_observation_to_contract(
                    item,
                    observation_id=observation_id,
                    method=method,
                )
            )
    return tuple(converted)
