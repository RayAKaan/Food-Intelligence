# Phase 0 — Repository Baseline and Research Specification

## Purpose

Phase 0 establishes a reproducible starting point before production architecture changes. It inventories the repository, verifies executable checks, documents the current architecture, records research and reproducibility constraints, and defines the entry gate for Phase 1. It does not claim scientific validity or implement the food-world simulator.

## Subphases

- **0A — Repository inventory:** deterministic static inventory of modules, functions, tests, data, docs, schema, workflows, imports, and fixture coupling.
- **0B — Executable baseline:** run compilation, existing tests, and supported CLI smoke tests.
- **0C — CI verification:** enforce the baseline on Python 3.10–3.13.
- **0D — Architecture snapshot:** document overlapping production paths and gaps between existing scoring/graph components and an executable world.
- **0E — Reproducibility and evidence audit:** define provenance, licensing, model/data versioning, and measured-vs-simulated-vs-inferred boundaries.
- **0F — Phase 1 entry gate:** verify that the inventory, tests, CI, architecture risks, and research specification are recorded.

## Running the audit

Static inventory:

\`\`\`bash
python scripts/phase0_audit.py
\`\`\`

Strict readiness gate and machine-readable report:

\`\`\`bash
python scripts/phase0_audit.py --strict --output phase0-audit.json
\`\`\`

The audit uses static AST parsing and does not import or execute production modules. It reports syntax errors, required paths, production imports, module/test inventory, schema tables, fixture-like data paths, and direct FoodMVP coupling. Its counts are generated from the checkout and must not be copied manually into this document.

## Existing architecture summary

The repository contains modules for ingestion, corpus handling, representations, graph construction, retrieval, compatibility, novelty, constraints, orchestration, evaluation, synthetic benchmarks, and storage. A PostgreSQL schema and tests are present.

The source tree also contains newer intelligence/retrieval components alongside older fixture/MVP components. The static audit reports this coupling but does not treat its existence as an automatic CI failure: the coupling is a known migration task, not something Phase 0 should silently refactor.

## Scientific limitations recorded at baseline

- A simulator must not be assumed to exist merely because graph edges or process abstractions exist.
- Compatibility scoring is not proof of physical or chemical causality.
- Synthetic fixtures and synthetic benchmark results are not scientific evidence.
- Candidate source metadata does not imply data access or redistribution permission.
- Measured, simulated, and inferred outcomes must remain distinguishable.
- Missing data must not be treated as zero.
- No scientific capability is accepted without an appropriate evaluation method and documented operating limits.

## CI baseline

CI must install the package and pytest, compile source, run the strict static audit, run the full test suite, and execute the existing CLI smoke tests across Python 3.10, 3.11, 3.12, and 3.13.

The Phase 0 audit tests verify that the report is machine-readable and deterministic, that the strict gate passes for a valid repository, and that report-file output matches standard output.

## Exit criteria

Phase 0 is complete only when all of the following are true:

1. Inventory output is deterministic and valid JSON.
2. Strict baseline checks pass.
3. The existing test suite and CLI smoke tests pass in the CI matrix.
4. Architecture risks and known fixture coupling are documented.
5. The research specification and evidence-integrity rules are committed.
6. Phase 1 is scoped around canonical scientific world contracts, with no unreviewed production-path migration bundled into Phase 0.

## Next phase

**Phase 1 — Canonical Scientific World Contracts.** Define typed contracts for world states, ingredients, compounds, processes, interventions, experiments, observations, provenance, and uncertainty before implementing world dynamics.
