# Benchmark specification

| Task | Input | Ground truth | Primary metrics | leakage control |
|---|---|---|---|---|
| alias resolution | raw ingredient phrase | canonical id/state | accuracy, macro-F1 | held-out aliases |
| recipe retrieval | query entities/targets | relevant recipe set | P@k, Recall@k, MRR, NDCG | recipe-family grouping |
| pairing prediction | one ingredient + held-out pair | held-out co-occurrence/labels | PR-AUC, Recall@k | pair holdout |
| sensory retrieval | target descriptors | annotated matches | NDCG, calibration | source/cuisine split |
| constraints | ingredients + forbidden/required | valid outputs | pass rate | fixed cases |
| novelty ranking | candidate set | corpus frequency + expert label | frontier, pairwise agreement | indexed-corpus declaration |
| evidence attribution | claim | source/evidence class | accuracy, unsupported rate | claim-level split |
| process validity | recipe graph | expert/grammar rules | valid-step rate | template holdout |

The synthetic fixture only tests code paths. No benchmark score is publishable until a licensed corpus and preregistered split replace it.
