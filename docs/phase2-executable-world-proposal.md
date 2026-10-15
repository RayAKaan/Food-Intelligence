# Phase 2 Proposal — Executable World State and Intervention Execution

## Objective

Introduce the smallest executable state-transition layer that applies validated interventions to an immutable canonical `WorldState`, returns a new state plus a typed execution report, and preserves the complete before/after relationship. This phase creates execution semantics; it does not yet claim to simulate real food chemistry.

## Non-goals

- No learned dynamics, chemistry solver, reaction kinetics, sensory predictor, or food-safety certification.
- No LLM-selected or free-form Python execution.
- No automatic inference of missing quantities, units, component identities, or preconditions.
- No mutation of the caller's initial state.
- No promotion of synthetic or simulated results to measured evidence.
- No database or durable experiment memory in Phase 2 unless separately scoped and reviewed.

## Proposed API boundary

The names below are proposals, not implemented public APIs.

```python
@dataclass(frozen=True)
class WorldTransition:
    transition_id: str
    initial_state_id: str
    resulting_state_id: str | None
    intervention_id: str
    engine_id: str
    engine_version: str
    status: TransitionStatus
    issues: tuple[TransitionIssue, ...]
    applied_parameters: Mapping[str, Quantity]
    evidence_class: EvidenceClass  # SIMULATED only for this software executor
```

Proposed pure entry point:

```python
execute_intervention(
    initial_state: WorldState,
    intervention: Intervention,
    *,
    engine: InterventionEngine,
) -> tuple[WorldState | None, WorldTransition]
```

The engine interface must be registered and typed. It must not use `eval`, dynamic imports from user input, or arbitrary shell execution. The first implementation should support only a tiny allowlist of deterministic bookkeeping operations (for example, setting a declared condition where unit compatibility is established). A heating intervention must not pretend to compute aroma, chemistry, microbial safety, or texture unless a separately validated dynamics model is explicitly selected.

## Execution semantics

1. Validate the initial state schema version and intervention contract.
2. Verify all target component IDs exist in the supplied state.
3. Check declared preconditions using explicit typed predicates; unknown precondition inputs evaluate to UNKNOWN, not TRUE.
4. Validate parameters against the engine's declared parameter schema and unit dimensions.
5. Apply the operation to a copy/new value; never mutate the initial state or its nested mappings.
6. Return either a complete new state and successful transition record, or no resulting state and a failure report with stable issue codes.
7. Derive the new state ID deterministically from the canonical initial state, intervention, engine identity/version, and applied parameter payload.
8. Preserve parent-state linkage to the initial state. Do not silently discard components, conditions, attributes, uncertainty, or provenance.
9. Record engine identity, version, assumptions, limits, and evidence class in the transition.
10. Do not create experimental observations automatically. Measurement/simulation outputs belong to the later observation contract and must identify their method and evidence class.

## Proposed modules

- `world_state.py`: state integrity helpers and immutable snapshot utilities, only if existing `world_contracts.py` remains a contract-only module.
- `intervention_engine.py`: protocol/interface and deterministic dispatch registry.
- `transition.py`: transition result/status/issue contracts.
- `tests/test_world_transition.py`: operation allowlist, missing target, missing/unknown preconditions, unit mismatch, immutability, stable IDs, deterministic replay, error reporting, unknown-value handling, and malicious operation names.
- `docs/phase2-executable-world-state.md`: supported operations, limitations, and extension policy.

Keep modules consolidated if the implementation is clearer without them; do not split files merely to match this proposal.

## Required tests

- Valid operation returns a new state with correct parent link.
- Initial state and nested mappings remain unchanged after success and failure.
- Missing target, invalid operation, unsupported unit, schema mismatch, and failed precondition fail closed with stable issue codes.
- Unknown values remain unknown and never become zero/default values.
- Same canonical input + engine version produces same transition/state IDs.
- Different engine versions cannot collide when transition semantics differ.
- Unsupported physical outcomes are not generated.
- Every transition records engine/version and the limitations of the selected operation.
- Public exports do not break legacy package imports.
- Full CI and strict audit pass across supported Python versions.

## Phase exit criteria

Phase 2 is complete only when the state transition API is deterministic, immutable at the caller boundary, fully tested, explicit about unsupported physics, and integrated with the canonical contracts. This proves software execution semantics only. Validated food dynamics remains a separate subsequent phase requiring sourced parameters, operating ranges, and comparison with physical measurements.


## Implementation progress (2026-10-15)

- **Phase 2A merged:** deterministic single-intervention execution for the allowlisted `set_condition` bookkeeping operation.
- **Phase 2B in progress:** sequential execution of the interventions declared in an `ExperimentProtocol`, with state chaining, deterministic replay, stop-on-first-failure semantics, and explicit partial-progress reporting.
- Neither increment implements physical food dynamics or generates observations.
