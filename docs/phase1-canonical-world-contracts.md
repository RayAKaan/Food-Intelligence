# Phase 1 — Canonical Scientific World Contracts

## Purpose

Define stable, validated contracts shared by the future world state, intervention API, dynamics engine, experiment runner, observation system, experimental memory, and AI scientist. This phase defines the language and invariants of experimentation; it does not implement a simulator or claim scientific prediction.

## Subphase plan

### 1A — Experimental record primitives (current PR)
- Define typed world snapshots and components with explicit ingredient/state references.
- Define unit-bearing quantities and preserve unknown values as \`None\`, never zero.
- Define interventions, protocols, controlled variables, and repetitions.
- Define falsifiable hypotheses, model predictions, and experimental observations as distinct records.
- Distinguish measured, source-derived, simulated, inferred, and hypothetical evidence.
- Define experiment lifecycle states and required completion/failure details.
- Add deterministic canonical JSON and namespaced SHA-256 IDs.
- Add unit tests for validation, provenance boundaries, unknown values, and deterministic IDs.

### 1B — Canonical entity reconciliation
- Audit existing ingredient, compound, state, sensory, process, transformation, and provenance types.
- Map existing records to canonical identifiers without duplicating domain models.
- Define explicit state identity and ingredient-to-state relationships.
- Add adapters with round-trip tests and preserve existing public APIs during migration.

### 1C — Units, values, and uncertainty
- Establish unit conventions and conversion boundaries; never compare incompatible units silently.
- Define unknown, not measured, censored, failed, and observed values consistently.
- Define uncertainty and measurement metadata rules for numeric and categorical observations.
- Add dimensional and validation tests.

### 1D — Provenance and evidence contracts
- Standardize source identity/version, source record, license status, method, conditions, parent evidence, and limitations.
- Separate measured observations from simulator outputs and model inferences at every boundary.
- Define contradiction and evidence-link semantics without silently selecting a preferred claim.

### 1E — Cross-contract invariants and compatibility
- Validate references between world states, interventions, protocols, experiments, predictions, and observations.
- Define schema versioning and compatibility/migration policy.
- Add property-based or table-driven invariant tests using existing dependencies where possible.
- Verify legacy API compatibility and prohibit unreviewed production-path migration.

### 1F — Phase exit gate
- Document final contracts, examples, invariants, and unresolved limitations.
- Verify full CI, public imports, deterministic serialization, and compatibility.
- Produce a reviewed Phase 2 interface proposal for executable world state and intervention execution.

## Current implementation boundary

The 1A contracts are deliberately dependency-light and do not run equations, mutate a simulator, persist experiments, or infer scientific outcomes. The current repository already contains related concepts in \`representation.py\` and \`transformations.py\`; 1B will reconcile them instead of creating parallel ingredient/compound models.

## Non-negotiable invariants

1. Unknown is not zero.
2. A prediction is not an observation.
3. A simulated observation is not a physical measurement.
4. A hypothesis is not an established fact.
5. Measured/source-derived claims require a source record.
6. Every experiment refers to an explicit initial world state and versioned protocol.
7. Failed and negative experiments remain representable.
8. Deterministic IDs are based on canonical serialization, not runtime hashes.
9. Scientific claims remain limited to the evidence and operating range that support them.
10. No dataset is admitted solely because it is publicly reachable; rights and permitted uses must be reviewed.

## Phase 1 exit criteria

Phase 1 is complete when the domain entities and experimental lifecycle use one canonical, versioned contract system; existing representations have explicit adapters; invariants are tested; provenance and uncertainty survive round trips; and the contract boundary is ready for the Phase 2 executable world state. A passing test suite proves software behavior, not scientific validity.

## Canonical roadmap execution note

The 1A–1F labels in this document refer specifically to the canonical-contract roadmap. Some older repository documents named `phase1e-*` describe the earlier retrieval/reasoning prototype increment; those files are historical implementation notes and are not substitutes for this roadmap's cross-contract validation gate. The current 1E implementation and scope are documented in `docs/phase1-contract-invariants.md`.


## Phase 1F exit-gate implementation

The current exit-gate candidate adds `tests/test_phase1f_exit_gate.py`, `docs/phase1f-exit-gate.md`, and `docs/phase2-executable-world-proposal.md`. The integration test exercises the package-root public imports, a complete canonical experiment bundle, evidence-ledger audit, deterministic serialization and IDs, and preservation of unknown environmental values. CI on the PR head is still required before Phase 1 can be marked passed.

Phase 1 completion is a software contract boundary only. It does not mean legacy runtime paths have all been migrated, that a dynamics engine exists, or that the current system has scientific predictive validity. The Phase 2 proposal defines the next scope: immutable state transitions and fail-closed intervention execution, without unsupported physics or automatic observation creation.
