# Indian recipe corpus candidates

**Audit date:** 2026-09-11  
**Decision rule:** a repository-level CC label does not establish rights in scraped recipe text. Underlying publisher terms and source chain are required.

## Candidate matrix

| Candidate | Provider/original source | Scale and fields | Quality/coverage | License and underlying rights | Decision |
|---|---|---|---|---|---|
| 6000+ Indian Food Recipes Dataset v1 | Kanishka Jain / Mendeley; crawled from Archana's Kitchen | publisher reports >6,000; titles, original/translated ingredients, prep/cook/total, servings, cuisine/course/diet, instructions | strong field coverage; English translations plus Hindi originals; single-site bias; translation provenance must be retained | Mendeley page displays CC BY 4.0, but README says content was crawled from Archana's Kitchen and provides no evidence of permission or source-site license. Dataset-level CC BY cannot be assumed to relicense third-party text. | **LEGAL_REVIEW_REQUIRED**; primary research candidate only after permission/rights confirmation |
| Kaggle Indian Food Dataset / Archana derivative | Sukhmandeep Singh Brar / Kaggle; Archana's Kitchen | reports 6,000+ / 6,871; similar fields | useful structured fields; derivative mirrors conflict in count and license claims | Kaggle metadata claims CC0, while its description says source is Archana's Kitchen and a separate derivative is marked unknown. No primary rights chain established. | **REJECTED for current ingestion** |
| GitHub IndianFoodDatasetGeneration | Kanishk Jain; Archana's Kitchen | 6,000+; CSV/XLS and crawler code | reproducible code lineage; no immutable release checksum; scraped source | GitHub README documents crawling but no dataset license or source permission. | **LEGAL_REVIEW_REQUIRED**, not acquired |
| INDoRI | Khanna et al.; seven online platforms | 5,187 recipes, 18 Indian cuisines/regions; ingredients, instructions, cuisine/category/preparation time | best cultural breadth among candidates; paper says crawling and cleaning; ingredient extraction uses stop words; quantities/process detail need audit | Figshare entry displays CC BY 4.0, but paper says recipes were crawled from seven platforms and the public item has been reported as private/inconsistent. Underlying platform rights and exact release need confirmation. | **LEGAL_REVIEW_REQUIRED**; best research-coverage candidate, below 6,000 |
| Indian Nutrient Databank (INDB) | research team; books + 148 online recipes | 1,014 recipes; quantities, units, food codes, serving/nutrient data | high quantity/nutrient structure; too small for target; includes copyrighted books and website records | GitHub exposes code/files but no clear dataset-wide license. Source books and online records have separate rights; USDA/IFCT inputs have separate terms. | **LEGAL_REVIEW_REQUIRED**; useful nutrition/quantity secondary source, not primary recipe corpus |
| Indian Food 101 | Kaggle/commonly mirrored; original provenance unclear | ~255 dishes; ingredient list, diet, times, flavor, course, state, region | useful regional labels but too small | license/source chain not established from primary source in this audit | **REJECTED as primary** |
| Indian Recipes Nutrition & Cooking Method | Kaggle 2026 derivative of two sources | 725 dishes; normalized ingredients/instructions, times, nutrients, cuisine | compact and structured; explicitly mixes one source with unclear license | dataset description says Dataset B has no clear open license and releases combined data for research/education only | **RESEARCH_ONLY / LEGAL_REVIEW_REQUIRED** |
| RISeC | academic GitHub corpus | 260 recipe instruction texts; MIT | high instruction annotation quality, not Indian-specific and not large | repository displays MIT for dataset/code; original CURD/SIMMR lineage should still be checked | **BACKUP for process parser tests only** |

## Research findings

The public Indian recipe ecosystem is dominated by scraped datasets. The most common 6,000–7,000 recipe assets point back to Archana's Kitchen. Multiple mirrors assert CC0 or CC BY, but the source descriptions themselves identify web scraping and do not establish authorization from the publisher. This is a provenance/licensing conflict, not an acceptable basis for silently ingesting or redistributing raw recipes.

INDoRI is more culturally attractive because its paper reports seven source platforms and 18 cuisines, but its count is 5,187 rather than 6,000+ and the public release/permission chain requires confirmation.

## License decision table

| Candidate | Download | Internal storage | Research processing | Publish derived metrics | Redistribute raw/normalized | Commercial use | Train ML | Legal review |
|---|---|---|---|---|---|---|---|---|
| Mendeley 6000+ | yes, page provides download | uncertain pending terms/source permission | possible only under applicable terms | uncertain | no decision | no | no decision | **yes** |
| Kaggle Archana derivative | yes via platform | not approved | not approved | not approved | no | no | no | **yes** |
| INDoRI Figshare | item/download access inconsistent | uncertain | possible only after rights confirmation | uncertain | no decision | no | no decision | **yes** |
| INDB | code/files public | only after source-rights review | research candidate | limited derived statistics may be possible, source-dependent | no | no | no decision | **yes** |
| RISeC | yes | yes under repository terms | yes | yes under MIT terms | likely yes with notice | likely yes | likely yes | source-chain check |

These are engineering classifications, not legal opinions.
