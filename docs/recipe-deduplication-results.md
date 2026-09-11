# Recipe deduplication results

No research recipe rows were admitted, so no research deduplication was run. The canonicalization contract is `source_recipe_id -> canonical_recipe_group_id` with statuses `UNIQUE`, `DUPLICATE`, `VARIANT`, or `UNKNOWN`; source rows are never deleted. Commercial Sangat contains one record and therefore has one provisional canonical group, with no duplicate inference.

The implementation uses exact fingerprints first and title-plus-ingredient Jaccard similarity only as a review signal. Near-duplicate grouping must be source-aware before benchmark use.