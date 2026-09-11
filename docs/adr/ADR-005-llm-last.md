# ADR-005: LLM generation occurs after structured retrieval

## Decision
The LLM receives candidates, states, constraints, process templates, evidence labels, and uncertainty. It cannot create source facts; post-generation validation checks claims and constraints.
