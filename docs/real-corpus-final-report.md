# Real corpus milestone final report — 2026-09-11

## Decision

**The milestone is not yet scientifically complete.** The execution strategy and corpus tracks are operational, but the research benchmark is blocked on authorized ELR-1000 access. No questionable web crawl, synthetic fixture, or unverifiable recipe mirror was admitted.

## A. What was admitted?

- `INDIAN_FOOD_RESEARCH_V1`: no raw records yet; ELR-1000 is a gated candidate, not falsely counted as admitted.
- `INDIAN_FOOD_COMMERCIAL_V1`: one Sangat Food DB cooked-dish nutrition record, admitted as a supplement.
- `INDIAN_FOOD_QUARANTINE_V1`: metadata only for ELR pending access, EmTpro01, INDoRI, Archana-derived sources, and INDB source groups.

## B–L. Current measured counts

| requested metric | research V1 | commercial V1 |
|---|---:|---:|
| real recipes / records | 0 | 1 dish metadata record |
| canonical recipes | 0 | 1 |
| canonical ingredients | 0 | 0 recipe-structured |
| ingredient states | 0 | 0 |
| processes | 0 | 0 |
| regions | none admitted | North (one record) |
| languages | none admitted | Hindi/English labels in source record |
| duplicate percentage | not estimable | 0% |
| quantity percentage | not estimable | 0% |
| process-information percentage | not estimable | 0% |
| ingredient-state percentage | not estimable | 0% |

These zeros are an access/admission result, not a claim that ELR has no such fields.

## M. Unresolved

1. ELR file access requires Hugging Face authentication and acceptance of contact-sharing conditions; no authorized credentials were available.
2. INDB ASC/BFP/OSR source rights remain separate and unresolved.
3. No ELR checksum, parser run, canonicalization run, or benchmark split can be recorded before acquisition.

## N. Benchmarks now possible

The implementation is ready for held-out ingredient-pair prediction, recipe retrieval, ingredient resolution, culinary graph construction, and corpus-relative novelty once an admitted research snapshot has records. The one-record Sangat supplement is not sufficient to run them scientifically.

## O. Not yet supportable

No claims about sensory compatibility, chemical compatibility, deliciousness, culinary representativeness, or general Indian cuisine are supportable. No real pairing/retrieval metrics are reported.

## P. Next acquisition

Obtain an authorized, exact ELR-1000 snapshot; retain the accepted terms, revision, retrieval date, checksum, and original language/source metadata. Then review INDB `recipe_links.xlsx` row-by-row, beginning with OSR records, without admitting ASC/BFP or any source without rights evidence.

## Decision gate

A–E (pairing, retrieval, resolution, graph, novelty): **not yet passed**. Minimum missing data is one authorized, versioned recipe snapshot with record-level provenance—preferably ELR-1000—not an arbitrary increase to 6,000 rows.
