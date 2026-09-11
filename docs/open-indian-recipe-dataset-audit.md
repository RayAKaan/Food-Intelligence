# Open Indian recipe dataset discovery and provenance audit

**Audit date:** 2026-09-11  
**Rule:** a repository or hub label is not accepted as proof of rights over underlying content.

## Summary matrix

| dataset | records | unique_records | license | license_source | creator | original_content_creator | collection_method | source_chain | commercial_use | research_use | redistribution | derivatives | provenance_confidence | technical_quality | regional_coverage | ingredient_quality | instruction_quality | quantity_quality | state_quality | recommendation |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EmTpro01/indian-recipe-cleaned | 6,871 | unknown | no license in current README/API; downstream claim unverified | HF README/API; no license field | EmTpro01 | appears Archana's Kitchen derivative; viewer examples match Archana-style records | uploader dataset; lineage not declared | HF uploader → unknown parent → likely Archana/Kaggle/Mendeley chain | unknown | unknown | unknown | unknown | low | high fields, 3 strings | source labels embedded in records; likely single-site | ingredient strings with quantities | long instructions | mixed quantities | preparation text only | DERIVED_OPEN / LEGAL_REVIEW_REQUIRED |
| ELR-1000 | 1,073 | expected 1,073; verify snapshot | Karya Public License KPL BY-NC-SA-FS 1.0 | repository LICENSE/README and KPL link | Karya/ELR authors | community contributors; 368 rural women and 26 men | community collection with paid contributors and explicit consent | community contributors → Karya collection → ELR release | no; contact Karya | yes for research/noncommercial | gated/HF access and license terms | yes, same license; software system GPL requirement | high | rich multimodal; variable structure | Eastern India, 10 endangered languages | original multilingual ingredient fields | recipe steps text; translated subset | variable, not conventional standardized quantities | cultural/process details, variable | RESEARCH_OPEN + COMMUNITY_CONSENT |
| INDB | 1,014 | source-specific; not audited here | dataset-wide license not found | GitHub/research paper | research team | 490 cookbook + 378 cookbook + 148 web recipes | manually compiled/coded, not a single open source | researchers → cookbooks/websites/external food tables → INDB | unknown | research candidate, source-dependent | source-dependent | source-dependent | medium | very strong quantities/units/nutrients | Indian recipes, source-specific | coded ingredients and food codes | recipe data present | strong for included recipes | cooking methods/nutrient retention, not state-rich | LEGAL_REVIEW_REQUIRED; split by source |
| Sangat Food DB | seed targets 200 dishes | 200 target, current repo scaffold | CC BY-SA 4.0 | repository LICENSE/README | Sangat maintainers/contributors | Sangat household curation; raw macros from IFCT 2017 | direct hand curation from household norms | IFCT 2017 ingredient base + Sangat household averages → JSON dishes | yes, with attribution and share-alike | yes | yes under CC BY-SA | yes, same license; tooling separate MIT | high for repository claims | nutrition/dish metadata; not full recipe corpus | North/West/South/East targets; current seed North | ingredients_summary, not full ingredient lines | no full step instructions | portion-level nutrition, not recipe quantities | low/none | COMMERCIAL_OPEN as nutrition supplement, not recipe corpus |
| INDoRI | 5,187 | unknown | CC BY 4.0 displayed, underlying rights unresolved | Figshare/paper | authors | seven online platforms | web crawling | authors → seven sites → INDoRI | unknown | unknown/research candidate | unknown | unknown | medium-low | structured but access inconsistent | 18 cuisines/regions reported | ingredient lists/network | instructions/metadata reported | unknown | unknown | LEGAL_REVIEW_REQUIRED |
| Indian Food 101 | 255 | about 255 | “Data files © Original Authors” | Kaggle metadata | Neha Prabhavalkar | Wikipedia, Hebbar's Kitchen, Archana's Kitchen acknowledged | mixed compilation | uploader → mixed sources | unknown | unknown | unknown | unknown | low | ingredient/time/region labels; no full instructions | state/region labels | main ingredients | none | none | none | REJECTED for corpus |
| Indian Foods image dataset | 4,770 images | not recipes | CC0 claimed by HF/Kaggle mirror | HF dataset card | Bharat Raghunathan / source Kaggle | source chain not established | image dataset | mirror → Kaggle → unknown | unknown | unknown | unknown | unknown | low | image classification only | dish labels, not recipe regions | none | none | none | none | REJECTED for recipe corpus |
| RecipeDB | 118,171 global | unknown | CC BY-NC-SA 3.0 | paper/site | IIIT Delhi | AllRecipes/Food.com and other sources | aggregated web recipes | RecipeDB → multiple sites | no | yes under terms | restricted/share-alike | noncommercial/share-alike | medium | structured global data | Indian subset unknown | structured aliases | process metadata | variable | variable | RESEARCH_ONLY, not clean/commercial |
| Kaggle Archana mirrors | 6,000–7,000 | unknown | CC0/CC BY claims conflict with source provenance | Kaggle cards | multiple uploaders | Archana's Kitchen | scraped/mirrored | mirror → Kaggle → Archana | not established | not established | not established | not established | low | useful schema | source bias | good raw strings | good instructions | mixed | text only | REJECTED for clean corpus |

## Provenance findings

### EmTpro01

The Hugging Face repository has 6,871 rows and only three fields: `recipe`, `ingredients`, and `instruction`. Its current README contains dataset statistics but no license declaration. The dataset viewer examples include Archana-style recipe names and text such as Masala Karela, Udupi Style Ash Gourd Coconut Curry, and the Archana-style instruction template. No creator statement, collection method, parent dataset, source URLs, or rights grant was found in the repository metadata. A downstream claim of CC-BY-SA-4.0 is not a primary license source. It is therefore a derived/open-claim dataset, not an open dataset.

### ELR-1000

ELR is materially different: the repository states that recipes and recordings were contributed directly by community members, contributors gave explicit consent, and contributors were paid. The repository states 1,073 recipes in ten endangered Indic languages and publishes under KPL BY-NC-SA-FS 1.0. This is a defensible research/community-consent dataset, but it is noncommercial and its KPL includes share-alike and GPL requirements for software systems incorporating the material. HF access requires a token in the repository's quick-start instructions, so no raw snapshot was acquired in this environment.

### INDB

INDB is not one homogeneous rights class. The recipe workbook combines named cookbook sources and 148 online recipes. Nutrient tables also mix ICMR/IFCT, USDA, UK, and other inputs. A future legal audit must separate `ASC`, `BFP`, and `OSR` records rather than admitting the entire workbook under one status.

### Sangat Food DB

Sangat provides the clearest current open commercial rights for a small Indian cooked-dish nutrition dataset: the repository LICENSE and README explicitly grant commercial use under CC BY-SA 4.0, identify Sangat as maintainer, describe household curation, and separate IFCT 2017 raw-ingredient macros from Sangat dish curation. It is currently a seed/scaffold targeting 200 dishes and does not provide full recipe steps or raw ingredient quantities, so it should not be counted as a 200-recipe process corpus.

## Rejected shortcuts

- Kaggle CC0 labels on scraped Archana-derived files were not accepted.
- HF dataset tags were not treated as proof of underlying rights.
- RecipeDB was not treated as commercial-safe because its published license is CC BY-NC-SA.
- Image-only food datasets were not counted as recipe corpora.
