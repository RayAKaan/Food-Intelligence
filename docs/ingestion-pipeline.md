# Real-corpus ingestion pipeline

`raw immutable snapshot -> source parser -> field mapping -> raw-field preservation -> quantity/unit/state parsing -> deterministic alias resolution -> review queue -> recipe fingerprints/groups -> quality report -> canonical outputs -> source/group/pair splits -> SQLite/PostgreSQL load`.

The first implementation is in `src/food_intelligence/ingestion.py`. It deliberately has no blind downloader or scraper. Acquisition requires a manifest with an explicit legal status.
