# Data-model compatibility assessment — 2026-09-11

## Current data model

The MVP has `Ingredient`, `Evidence`, resolver aliases, fixture `Recipe` objects with free ingredient strings and minimal step dictionaries, a SQLite loader, and a PostgreSQL schema. It already represents null process parameters and exposes corpus-relative novelty.

## Required real-data model

Real corpus ingestion requires source-level recipe IDs, raw text retention, source/license metadata, recipe groups, typed ingredient rows with quantity/unit/state, source-specific payloads, review queue records, and leakage-safe split IDs. It also needs deterministic deduplication and quality metrics.

## Changes required

- added generic CSV normalization and state/quantity parsing interfaces;
- added recipe fingerprint/grouping and leakage-safe source/group split utilities;
- added data-quality reporting and review-item emission;
- added explicit legal gate that rejects `LEGAL_REVIEW_REQUIRED` sources from the commercial manifest;
- retained the existing fixture and resolver interfaces;
- did not add a graph database, LLM, molecular mappings, or web scraper.
