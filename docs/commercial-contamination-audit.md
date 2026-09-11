# Commercial contamination audit

The automated rule is simple: every commercial record must have a dataset in the commercial manifest and no dependency on research-only sources. `food_intelligence.corpus.contamination_audit` fails closed when any record falls outside the allowed commercial dataset set.

Current result: PASS for the one recorded Sangat file. ELR-1000, RecipeDB, FooDB, FlavorDB2, Pyrfume, INDB candidates, Archana-derived material, INDoRI, and EmTpro01 are excluded from the commercial track.