# Phase 1D — Food Intelligence Representation Layer

## Purpose

Represent food as independent, provenance-aware views rather than collapsing it into one opaque embedding.

Views currently supported by explicit builders:

- semantic
- molecular
- taste
- odor
- texture
- physical

Culinary and process representations remain graph/structured views and are not forced into numeric vectors.

## Missing-data rule

Missing observations remain `None` and are accompanied by an observed mask. Missing is never converted to zero.

## Transformation rule

A transformation record describes a possible state transition. It does not assert that a process causes a chemical or sensory change merely because the process is known. Output state, parameters, and outputs may remain unknown.

Asserted transformations require evidence. Experimentally validated transformations require experimental evidence.

## Data boundary

Synthetic fixture records are allowed for software integration tests only. They must never enter scientific training or evaluation manifests.

## Phase 1D.2 — Unified intelligence pipeline

The representation, transformation, and ranking primitives are now composed by
`food_intelligence.intelligence.FoodIntelligenceEngine`. Candidate ranking keeps
compatibility and novelty separate, applies hard safety blocks before ranking,
and preserves `UNKNOWN` when an indexed corpus is unavailable. This is a
software integration layer only; fixture-derived scores are not scientific
claims.

The engine currently exposes explicit extension points for culinary/process,
texture, molecular, pair-count, and evidence signals. These should be populated
from admitted real data before learned weighting is introduced.
