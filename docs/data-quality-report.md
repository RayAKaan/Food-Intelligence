# Data-quality report

## Status: BLOCKED BEFORE REAL INGESTION

No candidate recipe corpus was placed in `data/raw/` because the public license labels conflict with the documented scraped-source lineage. Therefore no real-corpus record counts, duplicate rates, resolution rates, or completeness statistics may be reported.

The quality report implementation exists in `src/food_intelligence/ingestion.py` and will emit:

- record counts;
- field completeness;
- quantity and unit coverage;
- instruction/process coverage;
- provenance coverage;
- unresolved mappings;
- duplicate groups;
- cuisine/region/language coverage.

The synthetic fixture remains only a regression test and is excluded from real-corpus claims.
