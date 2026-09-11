# Benchmark splits — INDIAN_FOOD_RESEARCH_V1

No real research split exists yet because ELR access is gated and no raw snapshot was acquired. The deterministic implementation in `food_intelligence.corpus.leakage_safe_split` assigns all records sharing a canonical recipe group to one of training, validation, or test using SHA-256 and seed 17. The split manifest must record the exact corpus version, group IDs, seed, parser, normalization, and ontology versions.

Required leakage controls: duplicate groups, near-duplicate groups, copied source records, and source-aware holdouts. A one-record Sangat supplement cannot support a scientific benchmark split.