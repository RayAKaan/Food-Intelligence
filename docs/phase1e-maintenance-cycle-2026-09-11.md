# Phase 1E — Autonomous maintenance cycle report (2026-09-11)

Scope: audit-and-strengthen pass over the Phase 1E MVP plus the first
deterministic real-corpus ingestion pipeline. All local work completed with no
genuine engineering blocker; the scientific-data blocker stands unchanged.

## Inspected

- All 26 package source modules, tests, fixture, schema, and all manifests under
  `data/manifests/`.
- Candidate Indian recipe datasets: INDB, Indian 6000+ Recipes (Mendeley),
  Kaggle mirrors, INDoRI, ELR-1000, RISeC, RecipeDB, Recipe1M+, EmTpro01.

## Changed

- `core.py`: removed shadowed `log1p` (import `math.log1p`), dropped unused `log`;
  `Resolver` now does token-subset matching and returns `None` on ties (ambiguity
  preserved, e.g. `cardamom`, `mustard` stay unresolved).
- `mvp.py`: removed dead `if False` branch; removed unused `compatibility`
  import; added `_sensory()` merging taste+odor (retrieval previously scored
  only odor); strengthened `_parse_quantity` (fractions, mixed numbers, ranges,
  `to taste`); added `_strip_modifiers` fallback and `whole`-unit fix.
- `ingestion.py`: `jaccard([],[])` now returns `0.0` (was `1.0`).
- `storage.py`: imports moved to top.
- `__init__.py`: wildcard import replaced with explicit exports; new modules
  exported; `__version__ = "0.1.0"`.
- `__main__.py`: added so `python -m food_intelligence` works.
- `pyproject.toml`: setuptools build system, console script `food`, package
  discovery under `src/`, test paths.
- `retrieval.py`: set-based Jaccard similarity so semantic/molecular views are
  searchable; dense-vs-sparse returns `None` (no faux grounding).
- `benchmark.py` / `evaluation.py`: 3 -> 11 fixture cases, hybrid mode, NDCG.
- `cli.py`: added `ingest` and `ingest-status` subcommands; UTF-8 BOM-safe
  manifest reading.
- `ingestion_manifest.json`: pipeline version 0.2.0 plus validated capability
  and fail-closed gates.
- `README.md`: new commands and real-corpus ingestion section.

## Added

- `benchmark_tasks.py`: alias (24 cases), state-resolution, constraint,
  process-validity, held-out pair baseline, `run_all_tasks()`.
- `ingest_pipeline.py`: `ManifestRecord`, checksum verification, CSV shape gate,
  schema detection, row mapping, resolution, dedup, provenance, quality, pairs,
  splits, frozen `corpus_manifest.json`, `status_without_snapshot`.
- Tests: `test_resolver.py`, `test_benchmark_tasks.py`, `test_retrieval_sets.py`,
  `test_ingest_pipeline.py`; extended `test_mvp.py`.

## Removed

- Dead `if False` branch; unused imports (`log`, `compatibility`).

## Results

- Tests: 64 passing (was 38).
- Fixture benchmark (synthetic): recall@5 = 0.909, MRR = 0.955, NDCG@5 :
  structured 0.876 / semantic 0.866 / hybrid 0.876 (was recall 0.667 on 3 cases).
- Tasks: alias accuracy 1.0 (resolution_rate 0.833), state/constraints/process
  validity 1.0, held-out pair baseline recall@5-of-seen 0.0161 (honest null).
- Package installs editable; runs without `PYTHONPATH`.
- Ingestion pipeline validated end-to-end on a tagged test snapshot: checksum
  gate, `archana_style` schema at 1.0 confidence, 100% resolution, frozen
  manifest emitted; column-overflow rejection demonstrated.

## Claims supported

- Pipeline mechanics, determinism, fail-closed admission gates, and regression
  health are demonstrated.
- No scientific food-intelligence claim is made: all performance evidence is
  `SYNTHETIC`, and the ingredient sensory fixture remains `EVIDENCE: HYPOTHESIS`.

## Blockers

- `NO_ADMITTED_REAL_RECIPE_CORPUS` unchanged: every Indian recipe candidate has
  unverified underlying-content rights, non-commercial terms, or gated access;
  no raw snapshot was acquired. `food ingest-status` reports this precisely.
  The ingestion pipeline is ready and documented to run the moment an
  authorized, checksum-pinned snapshot is supplied.

## Next actions

- Acquire an authorized ELR (or equivalent) research snapshot, record its exact
  revision and SHA-256, then run `food ingest` and the planned experiment
  reports (parser, canonicalization, split, quality, coverage, pairing,
  retrieval, resolution).
- Initialize git for reproducibility (repo is currently unversioned).
- Optionally seed a commercial-safe nutrition supplement (Sangat Food DB terms).