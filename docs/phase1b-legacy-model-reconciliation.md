# Phase 1B — Legacy Model Reconciliation

## Goal

Connect existing food-domain records to the Phase 1A canonical experimental contracts without replacing public types prematurely or making incompatible concepts look equivalent.

## Implemented in this subphase

- Preserve existing ingredient, compound, and persisted state IDs exactly; reject IDs with surrounding whitespace instead of silently rewriting references.
- Derive deterministic ingredient-state IDs only from an ingredient ID and a curated state label. Existing persisted IDs must not be regenerated.
- Normalize legacy process names using the existing process normalization and reject names outside the existing process vocabulary.
- Convert legacy provenance into canonical evidence records while retaining source ID, source-record ID, version, license status, parent evidence, confidence context, and processing/mapping version context.
- Add a dedicated `SYNTHETIC_FIXTURE` evidence class so generated fixtures cannot be mistaken for measured, source-derived, or simulator evidence.
- Convert legacy observations only when method and evidence classification are available; reject ambiguous `observed=True, value=None` records rather than guessing what missingness means.
- Convert legacy sensory profiles into deterministic observation IDs while keeping modality in identity, so identical descriptors in taste and odor do not collide.
- Require measured evidence to retain a source-record ID.
- Export adapters from the package API and cover conversion invariants with regression tests.

## Deliberately not coerced

- A legacy `Compound` is not a `WorldComponent`: the former describes a chemical entity, while the latter is material in an ingredient state with an amount.
- A `TransformationRecord` is not an `Intervention`: a transformation record describes a declared input/process/output relation, while an intervention is a proposed operation targeting an actual component in a world state.
- A graph edge is not a physical law. Existing graph relationships remain descriptive unless supported by a separately validated dynamics model.
- A model prediction is not a measurement. Legacy `MODEL_PREDICTION` records are mapped to `INFERRED`, not to `SIMULATED`.
- Synthetic fixture provenance is explicitly marked as `SYNTHETIC_FIXTURE`; this label is software/data origin, not scientific evidence.

These distinctions avoid lossy conversions and preserve the existing public API until a later phase defines explicit state-transition and dynamics contracts.

## Validation expectations

- Existing test suite and CLI smoke checks remain green.
- New tests cover stable IDs, process normalization and rejection, source provenance, synthetic fixture boundaries, missing-value handling, and sensory modality identity.
- CI across Python 3.10–3.13 is required before merge.

## Remaining Phase 1 work

1. Phase 1C — units, missingness, and uncertainty conventions.
2. Phase 1D — common provenance/evidence semantics and contradiction handling.
3. Phase 1E — cross-contract references and compatibility guarantees.
4. Phase 1F — full Phase 1 exit gate.

Passing software tests establishes adapter behavior only; it does not validate a scientific hypothesis or dynamics model.
