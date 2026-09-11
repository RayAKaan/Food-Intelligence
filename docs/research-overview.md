# Research report: computational food intelligence (Phase 1)

**Research date:** 2026-09-11 (Asia/Calcutta)  
**Scope:** Indian cuisine, 300–500 canonical ingredients, >=6,000 recipes where rights permit.

## 1. Executive summary

The project is worth pursuing as a **measurable research program**, not yet as a broad consumer product. The field already demonstrates recipe mining, molecular food-pairing, knowledge graphs, and LLM recipe generation. The defensible gap is narrower: a traceable, state-aware representation that keeps taste, odor, mouthfeel, process, and novelty separate, then validates predictions in controlled cooking experiments. The MVP should test whether this representation beats recipe-only and LLM-only baselines on constrained retrieval, held-out pairing prediction, and evidence-grounded generation.

The biggest practical blocker is licensing, not modeling. Recipe1M+, RecipeDB, FooDB, FlavorDB2, Pyrfume, and Phenol-Explorer should not be silently mixed into a commercial training corpus: several are research-only, non-commercial, share-alike, or require permission. Build an auditable research snapshot and a separate clean-room/commercial track.

## 2. State of the field

Computational gastronomy has established ingredient–recipe and ingredient–compound graphs, food-pairing indices, embeddings, and creative search. RecipeDB reports 118,171 recipes and 23,548 ingredients; FlavorDB2 reports 25,595 flavor molecules and 936 natural ingredients; Pyrfume aggregates more than 40 olfactory datasets. These resources support retrieval and hypothesis generation, but not a unified, validated model of cooking transformations. Shared compounds are not a sufficient theory of compatibility: cuisines can exhibit contrasting pairing signatures, and sensory perception is context-dependent.

**Bottom line:** existing work makes the proposed retrieval/graph baseline feasible; it also means “AI discovers novel pairings” is not differentiation by itself.

## 3. Existing systems and competitors

| System | What it does | Data/representation | Gap relative to this project |
|---|---|---|---|
| FlavorDB/FlavorDB2 | Flavor molecules, descriptors, food associations | compound/food tables | No complete process-state model; NC-SA terms |
| RecipeDB | Structured recipes linked to nutrition/flavor | recipe/ingredient/process metadata | License is CC BY-NC-SA; not commercial default |
| FoodOn | Food ontology and identifiers | OWL/OBO classes and relations | Ontology, not a predictive culinary model |
| FoodKG/RecipeKG | Knowledge graphs for recipes, nutrition, health | RDF/graph | Mostly recommendation/health, not sensory transformation |
| Foodpairing | Commercial aroma pairing and product/NPD intelligence | proprietary analyzed products + ML | Strong commercial incumbent; public methods/data limited |
| IBM Chef Watson | Historical cognitive cooking experiment | recipes, chemistry, chef curation | Demonstrated concept; no current open transformation platform |
| Samsung Food | 160k+ recipe personalization, planning, connected appliances | product/recipe/user context | Consumer workflow, not molecular/sensory science |
| Kitchenette / RecipeMT | Learned pairing/recipe ideation research | recipe co-occurrence + flavor features | Useful baselines; novelty and validation remain limited |

**Required differentiation:** process-aware food states, provenance, uncertainty, controlled experiment loop, and benchmarked novelty—not merely LLM output.

## 4–7. Dataset inventory, licensing, overlap, quality

| Source | Best use | Evidence/scale | License posture | MVP decision |
|---|---|---:|---|---|
| FoodOn | canonical food/process identifiers | >9,000 food products; CC BY 4.0 | commercially usable with attribution | **Adopt** |
| USDA FoodData Central | composition/nutrients and identifiers | 600k+ foods, multiple data types | US public-domain/CC0-style access; verify each export | **Adopt, cite** |
| FooDB | food–compound links, structures, concentrations | ~9,461 foods, ~10,898 compounds in cited 2023 use | CC BY-NC 4.0 / commercial permission required | **Research quarantine** |
| FlavorDB2 | flavor molecules, descriptors, thresholds, ingredient links | 25,595 molecules; 936 natural ingredients | CC BY-NC-SA 3.0 | **Research quarantine** |
| Pyrfume | olfactory perception and odor descriptors | >40 datasets | non-commercial except source-specific permissions | **Research quarantine** |
| Open Food Facts | packaged foods, allergens, labels | global, crowdsourced; bulk exports | ODbL database; images CC BY-SA | **Optional; isolate ODbL** |
| Phenol-Explorer | polyphenol composition and processing retention | 502 polyphenols/452 foods; >37k points in v1 | public resource; commercial redistribution requires permission | **Research quarantine** |
| FEMA Flavor Ingredient Library | safety/regulatory reference | ~3,000+ flavor ingredients cited by FEMA/FDA material | terms and intended-use limits must be checked; not a blanket safety approval | **Reference only; no bulk assumption** |
| RecipeDB | structured recipes/flavor/nutrition | 118,171 recipes | CC BY-NC-SA 3.0 | **Research benchmark only** |
| Recipe1M+ | recipe/image research benchmark | ~1M recipes | research/non-commercial terms | **Research benchmark only** |
| 6,000+ Indian recipes (Mendeley/Archana’s Kitchen crawl) | Indian recipe baseline | 6,000+ | CC BY 4.0 as catalogued; source-site rights and crawl terms still audit | **Candidate; verify provenance** |
| Kaggle Indian recipe derivatives | convenience | variable | often unknown | **Reject until rights proven** |
| FoodKG/RecipeKG | graph design and benchmark ideas | Recipe1M/Allrecipes-derived | source-specific; often non-commercial/unclear | **Do not redistribute by default** |

### Overlap and quality findings

- FDC, FooDB, FlavorDB2 and FoodOn overlap in food identity but use different granularities: raw material vs processed product vs ingredient entity vs molecular occurrence. Do not deduplicate by string alone.
- Recipe datasets duplicate source recipes, rewrite units, omit quantities, and confuse ingredient state with identity. Deduplicate by normalized ingredient multiset + title + instruction similarity; retain source versions.
- Molecular occurrence does not imply aroma causality or concentration above sensory threshold. Preserve concentration basis, analytical method, matrix, and source.
- Odor datasets are molecule-centric and perceptual; they do not directly describe cooked dishes.
- Indian coverage is uneven by region, language, diaspora source, vegetarian bias, and web availability. Report coverage, not representativeness.

### Licensing rule
Maintain two manifests: `research_allowed` and `commercial_candidate`. A source is never “commercially usable” merely because it is downloadable. Human legal review is required for ambiguous source-site crawls, database sui generis rights, and dataset combinations.

## 8. Proposed ontology

Core entities: `Ingredient`, `IngredientState`, `Food`, `Compound`, `ChemicalClass`, `TasteDescriptor`, `OdorDescriptor`, `TextureDescriptor`, `PhysicalProperty`, `Recipe`, `RecipeStep`, `Process`, `Transformation`, `Cuisine`, `Region`, `SensoryProfile`, `Source`, `Evidence`, `Experiment`, `ModelPrediction`.

Relations are typed and bitemporal where practical: `contains`, `has_state`, `contributes_to_taste`, `contributes_to_odor`, `used_in`, `has_step`, `uses_process`, `transforms`, `pairs_with`, `similar_to`, `complements`, `common_in`, `substitutes_for`, `belongs_to`. Every assertion carries source, source record, retrieval date, license, confidence, evidence type, and transformation history.

Taste and odor remain separate. Texture is state- and condition-dependent. A missing datum is null, never zero.

## 9. Database architecture

**MVP:** PostgreSQL + pgvector in production; SQLite locally for tests and demos. Use relational tables for facts and provenance, JSONB for source-specific payloads, typed edges for the graph, and vector rows keyed by representation type/version. PostgreSQL avoids a second system while joins, filters, provenance, and vectors are small. Qdrant is the first migration candidate if filtered vector scale or operational isolation justifies it; Neo4j is deferred because a graph database adds operational and licensing complexity before graph workloads are proven.

Core tables: `ingredients`, `ingredient_aliases`, `ingredient_states`, `compounds`, `ingredient_compounds`, `sensory_descriptors`, `ingredient_sensory`, `recipes`, `recipe_ingredients`, `recipe_steps`, `processes`, `transformations`, `edges`, `sources`, `evidence`, `embeddings`, `experiments`, `predictions`.

## 10. Embedding architecture

Start with explicit features and one semantic baseline, not seven opaque vectors. Maintain separate representations:

1. semantic: names, aliases, culinary roles;
2. molecular: compound presence/weighted occurrence;
3. taste: ordinal/continuous evidence-backed profile;
4. odor: descriptor profile;
5. texture/physical: state and process conditioned;
6. culinary/process: recipes, steps, cuisines, operations.

Benchmark each alone, concatenated with calibrated scaling, late-fusion rank aggregation, and structured retrieval. Embeddings are retrieval aids, never the source of truth.

## 11. Compatibility strategy

Use a multi-objective score with interpretable components:

`compatibility = sensory_complementarity + culinary_cooccurrence + process_compatibility + texture_complementarity - redundancy - safety_penalty`

Chemical similarity is a feature, not a positive assumption. Estimate complementarity from descriptor targets and held-out recipe edges; report confidence intervals and evidence class. Start with PMI/NPMI and cosine/weighted Jaccard; only add learned models after leakage-safe benchmarks.

## 12. Novelty strategy

Novelty is corpus-relative. Calculate: pair/set frequency, held-out recipe similarity, cuisine-conditional rarity, process novelty, and sensory-space distance. Label outputs `common`, `underrepresented`, `rare_in_indexed_corpus`, or `hypothesis_of_novelty`; never “unprecedented”. Apply a plausibility floor and a safety gate so random combinations do not win.

## 13. MVP architecture and end-to-end path

Input parser → alias/state resolver → structured retrieval → molecular/sensory/odor retrieval → recipe graph → candidate generator → compatibility + novelty scorer → process template → validator → evidence-grounded LLM response. The initial candidate generator is constrained beam search over ingredient graph neighbors plus complementary descriptors. LLM generation is last and receives only structured evidence and uncertainty labels.

## 14. Implementation plan

1. Freeze source manifests and licenses.
2. Build canonical ingredient vocabulary for 300–500 Indian ingredients.
3. Ingest one legally usable Indian recipe corpus and create held-out splits.
4. Add FDC/FoodOn identifiers; keep restricted molecular/sensory sources in research-only schema.
5. Implement entity resolution with state-aware aliases and review queues.
6. Parse recipes into ingredient/operation/state graphs with explicit unknowns.
7. Add deterministic compatibility and novelty baselines.
8. Add semantic and structured retrieval behind one interface.
9. Build validation and evidence ledger.
10. Benchmark, analyze failures, and only then train learned models or integrate an LLM.

## 15. Benchmark methodology

Tasks: ingredient alias resolution, recipe retrieval, held-out pair prediction, sensory-target retrieval, constraint satisfaction, novelty ranking, process validity, and evidence attribution. Splits must be source/time/cuisine-aware to reduce leakage. Report Precision@k, Recall@k, MRR/NDCG, calibration, constraint pass rate, hallucination rate, unsupported-claim rate, novelty-at-plausibility frontier, and human pairwise preference on a small blinded test.

Baselines: LLM-only, recipe retrieval, single vector, structured SQL, graph-only, hybrid graph+vector, multi-view fusion. Statistical reporting: bootstrap confidence intervals, paired tests where appropriate, and ablations for molecular/sensory/process features.

## 16. Major risks

| Risk | Severity | Mitigation |
|---|---|---|
| incompatible/unclear data licenses | Critical | source manifests, quarantine, legal review |
| ingredient/state ambiguity | Critical | canonical IDs, state nodes, review queue |
| false novelty from incomplete corpus | Critical | corpus-relative wording, multi-source search |
| chemistry ≠ compatibility | Critical | separate evidence types; human tests |
| sparse/matrix-dependent sensory data | High | uncertainty and concentration context |
| missing temperature/time/process parameters | High | explicit unknowns, process templates, experiments |
| recipe duplication and web bias | High | dedupe, source stratification, coverage report |
| unsafe suggestions/allergens | Critical | hard safety gate; domain review |
| texture prediction weakness | High | ordinal state features; defer numeric claims |
| LLM hallucination | High | structured output, citation/evidence validator |
| evaluation subjectivity | High | pairwise protocols and preregistration |

## 17. Commercial opportunities

Near term: B2B culinary R&D/ingredient ideation and an evidence-backed food intelligence API are more defensible than a generic B2C recipe app. The moat would be proprietary process-state and controlled sensory data. Public data should support prototypes; commercial deployment should rely on permissively licensed data, licensed datasets, and original experiments.

## 18. Scientific opportunities

The strongest research contribution is a benchmarked, provenance-aware representation for ingredient-state + process → sensory hypothesis. Priority experiments: roasting/frying/fermentation grids with mass, moisture, color, texture, odor and sensory ratings; then learn transformations only when the data supports them.

## 19. Recommendation

**Proceed, with a narrowed research thesis.** Do not promise a computational chef or novelty claims in Phase 1. Proceed only if the team commits to licensing separation, state-aware ontology, leakage-safe evaluation, and experimental validation. A 6–8 week pilot should be able to falsify the hypothesis with a small corpus before expanding to 500 ingredients.

## 20. Phase 2 gate

Advance only if the hybrid representation materially improves at least two of: held-out pairing prediction, sensory-target retrieval, constraint satisfaction, evidence grounding, or novelty-at-plausibility frontier over the strongest baseline, with no critical safety or licensing failure.

### Key sources

FoodOn: https://foodon.org/ · FDC: https://fdc.nal.usda.gov/ · FooDB: https://foodb.ca/about · FlavorDB2: https://cosylab.iiitd.edu.in/flavordb2/faq · Pyrfume: https://pmc.ncbi.nlm.nih.gov/articles/PMC11557823/ · RecipeDB: https://academic.oup.com/database/article/doi/10.1093/database/baaa077/6006228 · Open Food Facts: https://world.openfoodfacts.org/data · Phenol-Explorer: http://phenol-explorer.eu/downloads · Food pairing review: https://www.ias.ac.in/public/Volumes/jbsc/047/00/0012.pdf · Kitchenette: https://www.ijcai.org/proceedings/2019/0822.pdf · pgvector: https://www.postgresql.org/about/news/pgvector-080-released-2952/
