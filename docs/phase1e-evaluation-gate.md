# Phase 1E Evaluation and Research-Readiness Gate

## Purpose

This gate separates software/regression evidence from scientific evidence. The bundled fixture is synthetic and cannot establish real-world food-intelligence performance.

## Implemented evaluation

- leakage-aware retrieval benchmark
- Recall@K, MRR, NDCG
- deterministic bootstrap confidence intervals
- paired bootstrap deltas for ablations
- structured vs semantic vs hybrid ablation
- failure categorization
- real-corpus quality/readiness checks
- licensing contamination gate
- explicit research-readiness gate

## Required real-data gate

Scientific benchmarking remains **BLOCKED** until an authorized, versioned, checksum-pinned research recipe snapshot is admitted. Repository labels or downstream license claims are not sufficient evidence of rights.

## Promotion criteria

Phase 1E may advance only after:

1. an authorized real recipe corpus is admitted;
2. canonical recipe groups and leakage-safe splits are frozen;
3. benchmark metrics are computed on the held-out real data;
4. ablations compare the hybrid system against strong simpler baselines;
5. uncertainty intervals and paired comparisons are reported;
6. failures are manually reviewed and categorized;
7. no critical licensing or safety failure exists;
8. improvements satisfy the project's predefined advancement gate.

## CLI

`python -m food_intelligence.cli evaluate`

The current output is explicitly synthetic plus corpus-status information.
