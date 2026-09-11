# Canonical ontology

Identifiers are UUIDs internally, with external CURIEs retained. State is first-class: `tomato`, `tomato_paste`, and `tomato_raw` must not be merged.

## Evidence model

Every assertion has `source_id`, `source_record_id`, `retrieved_at`, `license_snapshot`, `evidence_type` (`FACT`, `SOURCE_DERIVED`, `INFERENCE`, `MODEL_PREDICTION`, `HYPOTHESIS`, `EXPERIMENTALLY_VALIDATED`), `confidence`, and `derivation_json`.

## Core relationship examples

- ingredient `HAS_STATE` ingredient_state
- ingredient_state `CONTAINS` compound (with basis and concentration)
- compound `CONTRIBUTES_TO` taste/odor descriptor (with evidence)
- recipe `USES` ingredient_state
- recipe `HAS_STEP` recipe_step
- recipe_step `USES_PROCESS` process
- process `TRANSFORMS` input_state → output_state
- ingredient `PAIRS_WITH` ingredient (edge_type-specific; never collapse similarity and complementarity)
