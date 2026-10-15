# Phase 1D — Provenance and Evidence Contracts

## Objective

Make provenance a first-class, queryable contract across imported sources, measured observations, simulated outputs, model inferences, and derived records. Evidence must be traceable without promoting synthetic/model-derived information into measurements or silently resolving disagreement.

## Implemented in this subphase

- Extend canonical \`EvidenceRecord\` with explicit method, conditions, observation time, source URI, content hash, source version, source record ID, license status, parent evidence IDs, and limitations.
- Add a dependency-free \`EvidenceLedger\` for indexing records and typed relationships.
- Support \`SUPPORTS\`, \`CONTRADICTS\`, \`DERIVED_FROM\`, \`CORROBORATES\`, and \`DUPLICATES\` relationships.
- Validate link endpoints and detect derivation cycles.
- Preserve contradictions as explicit links; do not select a preferred claim automatically.
- Audit incomplete source metadata and missing lineage references.
- Keep the ledger in-memory only; durable persistence belongs to the experimental-memory phase.
- Add regression tests for source requirements, metadata warnings, lineage traversal, cycle prevention, and contradiction preservation.

## Evidence classes and interpretation

- \`MEASURED\`: a recorded observation tied to a source record. The class alone does not prove instrument calibration or experimental quality.
- \`SOURCE_DERIVED\`: a claim transcribed or derived from a named source.
- \`SIMULATED\`: output of a declared computational engine.
- \`INFERRED\`: output of a reasoning/model process.
- \`HYPOTHESIS\`: a proposition awaiting a discriminating test.
- \`SYNTHETIC_FIXTURE\`: generated test material; not scientific or physical evidence.

Evidence class describes origin, not truth. Source version, license status, method, conditions, and limitations should be captured when applicable. Missing metadata is reported rather than invented. Source rights must be reviewed separately from technical availability.

## Lineage semantics

A record's \`parent_evidence_ids\` lists the records it depends on. A \`DERIVED_FROM\` link uses the child as the source endpoint and the parent as the target endpoint. Derivation lineage must be acyclic. Support, contradiction, corroboration, and duplicate links do not imply derivation and may form cycles.

## Explicit limitations

- The ledger is an in-memory index and is not a database or immutable audit log.
- It does not independently verify citations, source licenses, hashes, measurements, or model correctness.
- Metadata completeness warnings are not proof that evidence is invalid; they identify gaps requiring review.
- Contradictions remain visible but are not adjudicated by an automated truth-ranking system.
- A passing test suite validates software invariants, not scientific claims.

## Exit criteria

- Source-derived and measured records retain source identity and record identity.
- Evidence relationships have typed semantics and valid endpoints.
- Derivation lineage is acyclic and traceable.
- Contradictory evidence can coexist without silent deletion or ranking.
- Missing metadata is visible and does not get fabricated.
- Full CI and legacy adapter tests pass across the supported Python matrix.
