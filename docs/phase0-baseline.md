# Phase 0 — Baseline & Repository Freeze

## Purpose

Phase 0 establishes a reproducible baseline before architectural changes begin. It does not modify food-intelligence behavior. It adds only repository diagnostics and continuous integration.

## Pre-Phase-0 audit

The main branch was inspected directly from repository contents.

| Area | Baseline |
|---|---:|
| Python source modules | 29 |
| Test files | 14 |
| Test functions | 64 |
| GitHub Actions workflows | 0 |
| Runtime third-party imports | 0 detected |
| Python requirement | >=3.10 |

The source tree contains both the newer FoodIntelligencePipeline/CompatibilityV2 path and older fixture/MVP components. That coupling is recorded by the audit and intentionally not changed in Phase 0; it is Phase 1 architecture-consolidation work.

## What this PR adds

- scripts/phase0_audit.py — dependency-free static repository audit.
- .github/workflows/ci.yml — Python 3.10–3.13 matrix, compilation, tests, and CLI smoke tests.
- This baseline document.

## Acceptance criteria

Phase 0 is complete when the PR's CI matrix is green on all supported Python versions and the audit reports the expected repository structure.

No production architecture is intentionally refactored in this phase. This keeps the baseline trustworthy and makes failures attributable to later phases.

## Next phase

Phase 1 will consolidate the production architecture around canonical interfaces and isolate fixture/demo code so that real corpus ingestion can become the production data path.
