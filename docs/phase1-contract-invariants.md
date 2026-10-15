# Phase 1E — Cross-contract invariants and schema compatibility

## Goal

Connect the Phase 1A–1D records into a validated experimental bundle. Structural consistency is necessary for reproducibility but is not evidence that a scientific model is accurate.

## Implemented

- \`validate_experiment_bundle\` checks protocol and initial-state references.
- It checks intervention target component IDs against the initial world state.
- It requires declared control variables to have explicit values in the initial state.
- It validates hypothesis references and referenced evidence IDs when an evidence registry is supplied.
- It checks prediction/observation unit dimensions for variables measured by both.
- It reports missing comparison units and completed experiments without observations as warnings.
- It checks evidence registry key consistency and parent references.
- Validation results use stable issue codes and ERROR/WARNING/INFO severities.
- \`SchemaMigrationRegistry\` applies only explicitly registered transformations, finds deterministic shortest migration paths, rejects cycles and duplicate edges, and never mutates the caller's input mapping.

## Failure policy

- Missing protocol, initial state, hypothesis, intervention target, control value, or referenced evidence is an error.
- Dimensional disagreement between a prediction and an observation is an error; numeric values are not automatically converted during validation.
- Missing comparison units and completed experiments without observations are warnings.
- A warning does not invalidate a report. Any error makes \`report.valid\` false.
- No migration path means migration fails closed. The registry does not invent conversions for old schemas.

## Limits and follow-up

- The validation function does not run a physical simulator, prove causality, certify food safety, or establish scientific validity.
- The current observation contract does not carry a direct evidence-record ID. Source record IDs and hypothesis evidence references are checked, but a first-class observation-to-evidence link remains a potential schema improvement.
- Evidence lineage cycles and link semantics remain the responsibility of \`EvidenceLedger\`; durable persistence is out of scope.
- The registry contains no built-in historical schema migrations until a specific migration is reviewed and tested.
- A later phase must add durable experiment memory and state-transition execution without bypassing these invariants.

## Verification

CI must pass across Python 3.10–3.13, including the strict Phase 0 audit, complete tests, compile checks, and CLI smoke tests. These checks establish software behavior only.
