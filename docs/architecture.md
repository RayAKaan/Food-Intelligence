# Phase 1 executable architecture

## Boundary

Phase 1 is a reproducible research engine with a SQLite local backend and a PostgreSQL/pgvector production schema. It includes canonical identities, state-aware aliases, structured recipe/process records, typed evidence, deterministic retrieval/scoring, novelty labels, validation, benchmark runners, and a CLI. It excludes a large LLM, frontend, crawler, physics simulation, and automatic commercial use of restricted data.

## Runtime path

`query -> intent parser -> Resolver -> structured retrieval -> typed evidence -> candidate scoring -> novelty -> process template -> validator -> report`

The LLM is an optional final renderer. The deterministic path is the source of truth.
