# Phase 2B — Sequential Protocol Execution

## Goal

Compose the Phase 2A single-intervention executor into a deterministic, auditable sequence following the intervention order declared by an `ExperimentProtocol`.

## Public API

- `execute_protocol(initial_state, protocol, engine=None)`
- `ProtocolExecutionStatus`: `SUCCEEDED` or `FAILED`
- `ProtocolExecutionReport`: execution identity, protocol/version, ordered transition records, final state when fully successful, last successful state, and failure details.

## Semantics

- Interventions execute in declaration order against the latest successful state.
- Execution stops at the first failed intervention. Later interventions are not attempted.
- Each transition's initial state must equal the preceding successful state ID.
- `final_state` is populated only when the complete protocol succeeds.
- On failure, `final_state` and `final_state_id` are null; `last_successful_state` makes partial progress explicit.
- An empty protocol is a deterministic no-op and returns the unchanged state.
- The input state is not mutated; deterministic replay depends on canonical inputs and engine version.
- All transition evidence remains `SIMULATED`; no observations or physical outcomes are generated.

## Scope boundary

This is sequencing/orchestration, not transaction rollback, physical simulation, measurement, or durable storage. The current allowlisted executor only performs explicit `set_condition` bookkeeping. A failed sequence does not claim the earlier successful in-memory transitions never happened; it exposes the last successful state for a caller to inspect and decide how to proceed.

## Verification

`tests/test_protocol_execution.py` covers ordered execution, state lineage, failure stop behavior, partial-progress reporting, empty protocols, deterministic replay, engine-version identity, and unknown-precondition handling. Passing tests establish software behavior only.
