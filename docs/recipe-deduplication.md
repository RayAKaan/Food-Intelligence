# Recipe deduplication

The real-corpus pipeline retains every source row and assigns a `canonical_recipe_group_id`. It uses normalized title plus ingredient multiset for exact groups, then title-conditioned ingredient Jaccard similarity for near duplicates. Instruction similarity and source metadata are reserved for the next pass. Rows are classified as `EXACT_DUPLICATE`, `NEAR_DUPLICATE`, `VARIANT`, or `LIKELY_INDEPENDENT`; no source record is deleted.
