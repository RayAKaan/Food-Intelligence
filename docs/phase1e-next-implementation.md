# Phase 1E next implementation

This increment adds the deterministic reasoning substrate above graph and multi-view retrieval.

## Components
- `constraints.py`: explicit hard gates and soft penalties; unknown safety remains distinct from a hard block.
- `compatibility_v2.py`: versioned, interpretable multi-objective compatibility configuration with explicit missing components.
- `reasoning.py`: combines constraint gating, compatibility, novelty, evidence-bearing outputs, and deterministic ranking.
- `pareto.py`: compatibility/novelty Pareto frontier.

## Research boundary
No new scientific observations are fabricated. Missing evidence remains missing. Safety `UNASSESSED` is not treated as safe certification. Novelty remains corpus-relative and becomes `UNKNOWN` without frequency evidence.

## Next gate
Integrate this substrate with the graph retriever so that candidate generation, hard filtering, process constraints, compatibility, novelty, and frontier selection execute from a single `FoodQuery` path. Then add leakage-aware end-to-end synthetic benchmarks and ablations before learned models.
