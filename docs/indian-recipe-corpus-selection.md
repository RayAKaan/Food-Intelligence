# Indian recipe corpus selection

## Scoring framework

Scores are ordinal decision aids, not legal conclusions: legal confidence 30%, provenance 15%, completeness 15%, ingredient/state usefulness 15%, cultural coverage 10%, deduplication/reproducibility 10%, scale 5%.

| Candidate | Legal confidence | Provenance | Completeness | Cultural coverage | Scale | Decision score | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Mendeley 6000+ / Archana derivative | 1/5 | 3/5 | 4/5 | 2/5 | 5/5 | 2.45/5 | LEGAL_REVIEW_REQUIRED |
| INDoRI | 2/5 | 3/5 | 3/5 | 5/5 | 4/5 | 2.90/5 | LEGAL_REVIEW_REQUIRED |
| INDB | 2/5 | 4/5 | 5/5 | 3/5 | 1/5 | 2.85/5 | LEGAL_REVIEW_REQUIRED |
| RISeC | 4/5 | 4/5 | 4/5 | 1/5 | 1/5 | 3.40/5 | not suitable Indian primary |

## Current selection

- **PRIMARY_CORPUS:** none approved for ingestion.
- **PRIMARY RESEARCH CANDIDATE:** Mendeley 6000+ only after rights confirmation from Mendeley contributor and/or Archana's Kitchen.
- **SECONDARY RESEARCH CANDIDATE:** INDoRI after confirmation of the exact Figshare release and source permissions.
- **BACKUP:** INDB for a smaller, quantity-rich Indian recipe benchmark after source-rights review.

## Stop decision

No candidate currently passes the legal gate for a reproducible raw-text corpus. The project must not download and process scraped recipe text into the repository as if it were commercially usable. The 6,000 target is therefore **not satisfied**.

The smallest unblock is written permission or a licensed export from the source publishers. If permission is obtained, acquire one immutable snapshot and use the existing ingestion pipeline. If permission is not obtained, use INDB/INDoRI only under an approved research agreement and report the reduced scope.
