# ADR-001: PostgreSQL + pgvector, SQLite local

## Context
Facts require joins, provenance, constraints, and typed edges; the MVP has no demonstrated need for a separate graph/vector service.

## Options
PostgreSQL+pgvector, Qdrant+Postgres, Neo4j, document DB.

## Decision
Use SQLite for zero-dependency reproducible tests and PostgreSQL+pgvector for production. Keep a retrieval interface.

## Consequences
Fast local setup and one production system. A migration to Qdrant is permitted only after filtered-vector benchmarks demonstrate material benefit.
