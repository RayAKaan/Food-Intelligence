# Dataset registry

This is the auditable source register. Counts are release-dependent; values below are reported figures from the linked source or literature, not assumed current totals. `commercial_status` is a build gate, not legal advice.

| name | URL | records/scale | format/API | coverage | license/status | MVP |
|---|---|---:|---|---|---|---|
| FoodOn | https://foodon.org/ | >9k food products | OWL/OBO, PURL | global food ontology | CC BY 4.0; attribution | adopt |
| USDA FDC | https://fdc.nal.usda.gov/download-datasets | 600k+ foods | CSV/JSON/API | composition/nutrients | public-domain/USDA terms; verify release | adopt |
| FooDB | https://foodb.ca/ | ~9.5k foods/~10.9k compounds in cited use | CSV/JSON/XML/SQL | food chemistry | CC BY-NC 4.0; permission for commercial | research only |
| FlavorDB2 | https://cosylab.iiitd.edu.in/flavordb2/ | 25,595 molecules/936 ingredients | JSON/MOL/SDF | flavor descriptors/thresholds | CC BY-NC-SA 3.0 | research only |
| Pyrfume | https://pyrfume.org/ | >40 datasets | GitHub/Python/R/REST | olfaction | non-commercial except source-specific | research only |
| Open Food Facts | https://world.openfoodfacts.org/data | global product DB | dump/API/Parquet | packaged foods | ODbL; images CC BY-SA | isolate |
| Phenol-Explorer | http://phenol-explorer.eu/downloads | 502 polyphenols/452 foods; >37k points (reported) | Access/download | polyphenols/process retention | commercial redistribution requires permission | research only |
| FEMA library | https://www.femaflavor.org/flavor-library | 3,000+ flavor ingredients cited in public material | web reference | flavor safety/use conditions | source terms; intended use limited | reference only |
| RecipeDB | https://cosylab.iiitd.edu.in/recipedb | 118,171 recipes/23,548 ingredients | web resource | global recipes | CC BY-NC-SA 3.0 | benchmark only |
| Recipe1M+ | https://im2recipe.csail.mit.edu/ | ~1M recipes/images | gated download | global web recipes | research/non-commercial terms | benchmark only |
| Indian 6000+ | https://data.mendeley.com/datasets/xsphgmmh7b/1 | >6,000 | CSV/XLS | Indian recipes from Archana’s Kitchen | catalog says CC BY 4.0; audit source/crawl rights | candidate |

## Indian recipe candidates added in execution milestone

See `docs/indian-recipe-corpus-candidates.md` and the machine-readable registry for Mendeley 6000+, INDoRI, INDB, and RISeC. All Indian candidates are currently `LEGAL_REVIEW_REQUIRED`; none is in `research_allowed` or `commercial_candidate`.
