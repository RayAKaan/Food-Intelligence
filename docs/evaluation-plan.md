# Evaluation plan

## Formal hypotheses

H0: adding structured, provenance-aware food views does not improve a predefined benchmark composite over the strongest simpler baseline.

H1: it improves at least two primary tasks—held-out pairing prediction, sensory-target retrieval, constraint satisfaction, evidence grounding, or novelty-at-plausibility—without a critical safety/licensing failure.

“Material improvement” is defined before the real run as a statistically reliable improvement against the paired baseline with non-overlapping bootstrap uncertainty at the chosen confidence level, plus a practically meaningful error reduction agreed in the experiment preregistration. No threshold is asserted from the synthetic fixture.

## Leakage controls

Use recipe-family/source grouping, ingredient-pair holdouts, temporal/source splits where available, and deduplicate before splitting. Never split near-duplicate recipe text across train/test.

## Baselines

LLM-only, lexical/recipe retrieval, semantic-only, structured-only, graph-only, hybrid, and multi-view. Report P@k, Recall@k, MRR, NDCG, constraint pass rate, unsupported-claim rate, and novelty-at-plausibility.
