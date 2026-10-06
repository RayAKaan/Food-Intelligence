# Phase 0 — Baseline & Repository Freeze

## Phase 0A — Repository Inventory

### Purpose

Phase 0A establishes a machine-readable inventory of the repository before any production architecture is changed. The inventory is intentionally static: it does not import application code, modify runtime behavior, or infer scientific validity.

The audit records:

- production Python modules and their public classes/functions;
- test files and test-function count;
- documentation, data, experiment, benchmark, database, and workflow footprint;
- PostgreSQL schema table inventory;
- important repository paths;
- fixture/synthetic data paths;
- detected runtime imports outside the standard-library allowlist;
- direct production coupling to FoodMVP.

Run it with:

```bash
python scripts/phase0_audit.py
```

or write the machine-readable report:

```bash
python scripts/phase0_audit.py --output /tmp/phase0a-inventory.json
```

### Baseline observed from main

The repository currently contains:

| Area | Baseline |
|---|---:|
| Python source modules | 29 |
| Test files | 14 |
| Test functions | 64 |
| GitHub Actions workflows before Phase 0 | 0 |
| Runtime third-party imports detected | 0 |
| Python requirement | >=3.10 |

The source tree contains both the newer intelligence/retrieval path and older fixture/MVP components. The inventory deliberately records that coexistence rather than changing it.

### Architecture-relevant inventory

The repository currently has explicit surfaces for:

- canonical food entities and provenance;
- ingestion and corpus handling;
- retrieval and query planning;
- graph construction;
- molecular/sensory representations;
- compatibility and novelty;
- constraints and safety;
- benchmarks and evaluation;
- experiments;
- PostgreSQL/pgvector schema;
- SQLite/local reproducibility;
- fixture and synthetic data.

The inventory also identifies the schema tables declared in database/schema.sql, allowing later phases to compare runtime models against the intended persistence model.

### Known boundary

Phase 0A is an inventory, not an architecture refactor.

In particular, it does not:

- remove FoodMVP;
- select a new canonical model;
- migrate storage;
- replace compatibility implementations;
- load a real corpus;
- change scientific scoring behavior.

Those decisions belong to Phase 1 and later gates.

## Phase 0A acceptance criteria

Phase 0A is complete when:

1. the repository can be inventoried without importing application dependencies;
2. production modules and tests are enumerated;
3. important data/documentation/experiment surfaces are enumerated;
4. the database schema is inventoried;
5. fixture/synthetic boundaries are explicitly visible;
6. legacy FoodMVP coupling is measurable;
7. the inventory runs successfully in CI.

## Relationship to PR #1

PR #1 establishes the initial Phase 0 CI and baseline. This PR extends the same dependency-free audit rather than introducing a second audit mechanism.

## Next

After Phase 0A, Phase 0B freezes the executable test baseline, followed by Phase 0C/0D/0E work for CI, architecture snapshot, and reproducibility.
