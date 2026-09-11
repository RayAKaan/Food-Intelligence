# Phase 1E implementation

Phase 1E establishes the deterministic retrieval/reasoning substrate without an LLM.

## Components
- `graph.py`: typed provenance-aware graph with traversal and path confidence.
- `query.py`: structured `FoodQuery`, query planner, graph + multi-view retrieval.
- `fusion.py`: explicit late fusion that excludes missing modalities from denominators.
- `novelty.py`: corpus-relative novelty signals independent from compatibility.

## Contract
Retrieval is recall-oriented; ranking remains a separate concern. Graph paths and per-view scores are retained as inspectable evidence. Missing observations are never converted to zero.

## Research boundary
No unauthorized source acquisition, no scientific claims from synthetic fixtures, and no LLM generation are introduced by this phase.

## Verification
32 tests pass, including the Phase 1E graph, planner, retrieval, missing-view fusion, and unknown-novelty tests.
