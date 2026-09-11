# Data pipeline specification

`source manifest -> source validation -> license gate -> immutable raw snapshot -> normalization -> resolution -> state extraction -> typed relations -> evidence attachment -> data-quality report -> SQLite/PostgreSQL load -> embeddings -> benchmark split`.

Each run records source version, retrieval date, checksum, processing version, schema version, and code revision. A failed quality check produces a flagged row/report; it does not silently coerce unknown to zero.
