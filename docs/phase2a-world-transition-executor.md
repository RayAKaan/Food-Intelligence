# Phase 2A — Deterministic World Transitions

## Scope

This increment introduces an executable transition boundary on top of the canonical Phase 1 contracts. It is intentionally a bookkeeping executor, not a food-physics simulator.

## Public API

- \`InterventionEngine\`: engine identity and version; operation implementations are defined in reviewed code.
- \`execute_intervention(initial_state, intervention, engine=None)\`: returns a new \`WorldState\` and \`WorldTransition\` on success, or \`None\` and a failed transition report.
- \`WorldTransition\`, \`TransitionStatus\`, and \`TransitionIssue\`: deterministic, typed audit records.

## Supported operation

Only \`set_condition\` is supported. Its parameters are:

- \`condition\`: a condition name that already exists in the initial state;
- \`value\`: a canonical \`Quantity\`.

The supplied quantity must have a registered unit compatible with the existing condition's unit. It is converted to the condition's existing unit. This operation records an explicitly requested bookkeeping change; it does not imply that heating, mixing, or another physical process would cause that condition to change.

## Preconditions

The initial grammar supports only:

- \`component_exists:<component-id>\`
- \`condition_known:<condition-name>\`

Unknown condition values return a \`PRECONDITION_UNKNOWN\` failure. Unsupported predicate syntax fails closed. There is no expression evaluation, dynamic import, shell execution, or user-supplied handler loading.

## Failure policy

Failures return no resulting state and stable issue codes. A failed operation never returns a partially updated state. Unsupported schema versions, absent targets/conditions, malformed parameters, unsupported operations, unknown preconditions, and incompatible/unsupported units fail closed.

## State and identity guarantees

- The caller's initial state is not mutated.
- The output state preserves the original components, schema version, and untouched conditions.
- The output state's \`parent_state_id\` references the input state.
- Resulting-state and transition IDs are derived from canonical payloads, including engine identity/version.
- Every transition remains \`SIMULATED\` evidence and carries explicit limitations.
- No experimental observation is generated.

## Explicit non-goals

No heat transfer, reaction kinetics, phase changes, volatile release, sensory prediction, microbial growth, nutritional prediction, or safety certification is implemented. A successful transition means only that the supported bookkeeping operation was applied consistently.

## Verification

\`tests/test_world_execution.py\` covers success, unit conversion, immutability, unknown values, precondition handling, target/condition errors, unsupported operations and units, schema mismatch, deterministic replay, engine-version identity, and the simulation-only evidence boundary. Full CI remains the verification authority; software tests do not validate physical food dynamics.
