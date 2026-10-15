# Phase 1F — Canonical Contract Exit Gate

## Status

Implementation candidate on `phase1f/contract-exit-gate`. This report records the intended exit criteria and the evidence required to mark them complete. The PR must not be treated as approved until GitHub Actions passes on the PR head and the changes are reviewed.

## Scope

Phase 1 defines a canonical vocabulary for the future Computational Food World. It is not a food simulator, a validated chemistry model, or a claim that the current food-pairing outputs are scientifically accurate.

The canonical contract surface currently comprises:

- `world_contracts.py`: versioned world snapshots, material components, quantities, interventions, protocols, hypotheses, predictions, observations, evidence records, experiment lifecycle records, canonical JSON, and stable IDs;
- `contract_adapters.py`: explicit legacy-to-canonical conversion that preserves IDs and fails closed when a faithful conversion is not possible;
- `units.py` and `measurement.py`: registered dimensions/conversions and measurement metadata;
- `evidence_ledger.py`: provenance lineage and contradiction links without automatic truth resolution;
- `cross_contracts.py`: reference/invariant validation and explicit schema migration paths.

## Invariants to preserve

1. Unknown values remain unknown; they are never silently converted to zero.
2. A prediction is not an observation.
3. A simulated result is not a physical measurement.
4. Hypotheses remain falsifiable claims, not established facts.
5. Measured/source-derived evidence requires source identity and source-record lineage as enforced by the contract.
6. Experiments reference an explicit initial state and protocol.
7. Failed, censored, unmeasured, negative, and contradictory results remain representable.
8. Stable IDs use canonical serialization, not runtime-dependent hashes.
9. Unit compatibility is checked explicitly; unsupported units fail closed.
10. Schema migrations are explicit, reviewed functions; no historical transformation is guessed.
11. Synthetic fixtures test software wiring only and must not be reported as scientific evidence.
12. Structural validation does not establish causality, predictive accuracy, food safety, or external validity.

## Exit-gate coverage

The Phase 1F integration tests exercise the package-root public import boundary, complete state → protocol/intervention → hypothesis/prediction/observation → evidence-reference validation, evidence-ledger audit, deterministic serialization/IDs, and preservation of an unknown environmental value.

Existing focused tests continue to own detailed unit, uncertainty, adapter, evidence-lineage, schema-migration, and cross-contract edge cases. CI remains the authoritative verification environment for the pull request; no local test run is claimed by this document.

## Known limitations and blockers

- The observation contract does not yet have a first-class evidence-record ID field. A consumer must not infer a direct observation/evidence link from matching descriptions or IDs. Add this only with a reviewed schema change and migration policy.
- The evidence ledger is in-memory. Durable experimental memory and atomic writes are a later phase.
- The canonical world state is a snapshot contract, not an executable state-transition engine.
- Intervention records describe intent; they do not apply physical or simulated changes.
- No food-dynamics solver has been validated against physical measurements.
- The repository's synthetic fixture is small and not a substitute for an admitted, rights-reviewed, reproducible real-food corpus.
- There is no scientific basis yet to claim validated sensory, aroma, texture, compatibility, safety, or recipe outcome prediction.
- Existing legacy systems are not all proven migrated to this contract boundary; Phase 1 completion here means the canonical contract layer is ready for the next implementation phase, not that every legacy runtime path has been replaced.

## Acceptance checklist

- [ ] Phase 1F integration tests pass on all configured Python versions.
- [ ] Full CI, strict Phase 0 audit, compilation, complete test suite, and CLI smoke checks pass.
- [ ] Public imports remain backward compatible.
- [ ] Canonical serialization and stable IDs are deterministic.
- [ ] Phase 2 interface proposal is reviewed before simulator implementation.
- [ ] No claim of scientific validity is made based solely on software tests.

## Handoff

The next phase is Phase 2: executable world state and intervention application. It must build on the contracts without putting domain-specific equations into the contract layer, without mutating the caller's initial snapshot, and without manufacturing observations or evidence.
