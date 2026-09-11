# Evidence model

Every assertion has two orthogonal labels: `data_status` (`REAL`, `SYNTHETIC`, `MODEL_DERIVED`, `HYPOTHETICAL`) and `evidence_type` (`FACT`, `SOURCE_DERIVED`, `INFERENCE`, `MODEL_PREDICTION`, `HYPOTHESIS`, `EXPERIMENTALLY_VALIDATED`). Missing values are NULL/unknown. Provenance includes source, record, retrieval date, license, processing/mapping versions, confidence, and parent evidence IDs. Conflicts are retained rather than overwritten.
