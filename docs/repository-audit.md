# Repository audit — 2026-09-11

## Current architecture

Before execution this repository contained documentation, a small dataclass-based scoring module, a CLI demo, and three unit tests. It had no database, ingestion pipeline, source registry, manifests, benchmark harness, API, CI, or Docker configuration.

## Current capabilities

- provenance-shaped `Evidence` records;
- deterministic alias resolution;
- basic taste target coverage, cosine redundancy, process compatibility, and corpus-relative novelty;
- seed demonstration for the requested ingredients;
- 6 passing tests after execution expansion;
- JSON dataset registry and license manifests;
- PostgreSQL/pgvector logical schema;
- structured MVP pipeline and synthetic benchmark fixture.

## Reusable code

`core.py` is reusable as a deterministic scoring kernel. `mvp.py` is intentionally a fixture-backed reference pipeline; it must not be mistaken for an ingestion result. Documentation and manifests are reusable.

## Technical debt and limitations

- no real licensed recipe snapshot is loaded;
- seed sensory values are hypotheses used only for wiring tests;
- no molecular adapter is loaded;
- no true embeddings or pgvector runtime is present;
- no LLM integration is present by design;
- benchmark values are not scientific results;
- safety data is unassessed;
- recipe parser is deliberately minimal;
- no CI configuration yet.

## Recommended modifications

1. Keep deterministic core and retrieval interfaces stable.
2. Add SQLite loader and data-quality checks before adapters.
3. Add one approved recipe snapshot and leakage-aware split.
4. Add source-specific adapters behind manifests.
5. Add real benchmark labels and bootstrap confidence intervals.

## Do not build yet

Do not build a frontend, agents, mobile application, graph database, large model, physics simulator, or automatic web scraper. Do not add restricted data to a commercial artifact.
