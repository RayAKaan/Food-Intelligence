# INDB source-level review

The public INDB repository README identifies three recipe groups:

| prefix | source | count | current decision |
|---|---|---:|---|
| ASC | *The Art & Science of Cooking*, 5th ed. | 490 | cookbook-derived; rights not granted by repository; quarantine |
| BFP | *Basic Food Preparation: A Complete Manual*, 4th ed. | 378 | cookbook-derived; rights not granted by repository; quarantine |
| OSR | open online recipes, with `recipe_links.xlsx` | 148 recipes / 150 links reported | source-by-source review required; do not assume “open source” means commercially or research licensed |

The repository makes code and files publicly available, but its README does not establish a single license for the underlying cookbook recipe text or the OSR source pages. Public availability is not treated as permission to redistribute or train on all fields. Until source-level rights are documented, all three groups remain quarantined. The ingredient/nutrient tables also carry separate upstream dependencies, including ICMR-NIN, UK COFID, USDA, and nutrient-retention tables; these must not be conflated with recipe-text rights.

Next review action: inspect `recipe_links.xlsx` row-by-row, identify each OSR host and license/terms, and create a source-specific admission list. ASC and BFP require publisher/rightsholder analysis or a permission grant before recipe text is admitted.
