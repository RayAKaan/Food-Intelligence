# Computational Food Intelligence — Research foundation

This repository is a research prototype for a computational food world, not a recipe chatbot. It implements a provenance-first canonical model for ingredients, compounds, sensory attributes, recipes, processes, compatibility, and novelty, with SQLite for local reproducibility and a PostgreSQL/pgvector migration path.

## Current status

- Research-first audit completed for the initial source shortlist.
- Canonical ontology and provenance rules documented.
- A dependency-light, deterministic scoring baseline implemented.
- Canonical experiment contracts, evidence lineage, units, deterministic state transitions, and sequential protocol execution implemented.
- A first responsive Digital Kitchen frontend prototype is available in `app/`.
- No scientific claim is promoted to fact without a source record.
- The frontend is not yet connected to the Python research core or a food-dynamics simulator.

## Digital Kitchen prototype

Open `app/index.html` in a browser, or run:

```bash
python -m http.server 4173 --directory app
```

Visit `http://localhost:4173`. The prototype includes an ingredient bench, creative-direction workspace, research-brief capture, and AI-researcher panel. It is a frontend prototype only: no LLM, persistent storage, scientific solver, or validated simulation is connected yet. See [app/README.md](app/README.md).

## Quick start — Python research core

```bash
python -m pytest -q
python -m food_intelligence.cli demo
```

The demo intentionally returns a hypothesis and evidence ledger, not a claim that a dish is unprecedented or delicious.

## Execution commands

```bash
python -m pytest -q
python -m food_intelligence demo
python -m food_intelligence benchmark
python -m food_intelligence tasks
python -m food_intelligence evaluate
python -m food_intelligence ingest-status
```

The package installs editable (`pip install -e .`) and is runnable as `python -m food_intelligence ...` or via the `food` console script. `food demo` runs the deterministic evidence pipeline; its seed corpus is a software fixture only. The benchmark output is explicitly non-scientific until a licensed, deduplicated recipe corpus replaces the fixture.

## Real-corpus ingestion

The dataset admission audited every candidate Indian recipe corpus and found none with confirmed underlying-content rights. **No admitted real recipe snapshot is present in this environment** — `food ingest-status` reports the exact blocker and per-dataset admission status from `data/manifests/`.

Once an authorized, checksum-pinned snapshot is supplied, the deterministic pipeline runs the whole path and freezes a versioned manifest:

```bash
python -m food_intelligence ingest --snapshot <file.csv> --manifest <record.json> --output-dir <out>
```

The pipeline refuses to ingest when any of these gates fail (fail-closed):

- snapshot file missing (`BLOCKED_SNAPSHOT_MISSING`),
- SHA-256 does not match the manifest's pinned digest,
- manifest record lacks source/license/admission fields,
- a CSV row has more fields than its header (silent data loss by `csv.DictReader` is blocked).

A successful run emits `ingestion_report.json` and a frozen `corpus_manifest.json` (checksums, versions, license, record count). Any research corpus is flagged as `REAL_PENDING_REVIEW` and its contamination audit reports how it must stay out of the commercial path. Synthetic and real records are never mixed.

## Unified intelligence pipeline

`FoodIntelligenceEngine` composes state/sensory/process/novelty signals into a deterministic candidate ranking interface. It is fail-closed for hard safety blocks and keeps unknown novelty distinct from a measured low score. The current fixture remains synthetic and is not evidence of food quality or novelty.

## Remaining scientific/product gaps

No physical food-dynamics simulator, validated sensory predictor, end-to-end AI scientist, persistent experiment memory, or commercial dataset redistribution is implemented. Public datasets with non-commercial or unclear terms remain quarantined from any commercial build. The next product work is to connect the UI to stable API contracts; the next scientific work is to build and validate narrowly scoped dynamics models.
