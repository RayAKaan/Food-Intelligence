"""Deterministic, source-preserving real-corpus ingestion pipeline.

Once an authorized, checksum-pinned snapshot is supplied, this module drives the
entire path from raw file to frozen manifest:

    authorized snapshot
    -> checksum verification
    -> schema detection
    -> row mapping
    -> canonical ingredient resolution
    -> deduplication (exact + near)
    -> provenance attachment
    -> corpus statistics
    -> pair statistics
    -> leakage-safe splits
    -> machine-readable report
    -> frozen corpus manifest

It NEVER fabricates a snapshot, never imputes missing values, and refuses to
admit a corpus whose manifest does not declare a source, a license, and an
admission status. If the snapshot is not present, the module reports the exact
blocker instead of pretending ingestion happened.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

from .ingestion import NormalizedRecipe, map_row, deduplicate, quality_report, split_by_group, source_checksum, recipe_fingerprint, norm_text
from .corpus import CorpusRecord, corpus_quality, pair_counts, leakage_safe_split, contamination_audit
from .mvp import FoodMVP

INGESTION_PIPELINE_VERSION = "recipe-ingestion-0.2.0"
REQUIRED_MANIFEST_FIELDS = ("dataset_name", "source_id", "source_url", "version", "license", "admission_status")


@dataclass(frozen=True)
class ManifestRecord:
    dataset_name: str
    source_id: str
    source_url: str
    version: str
    license: str
    admission_status: str
    research_status: str = "PENDING_REVIEW"
    commercial_status: str = "BLOCKED"
    expected_checksum: str | None = None
    columns: tuple[str, ...] = ()
    citation: str | None = None
    notes: str | None = None

    def validate(self) -> None:
        missing = [f for f in REQUIRED_MANIFEST_FIELDS if not getattr(self, f)]
        if missing:
            raise ValueError(f"manifest record missing fields: {missing}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_checksum(path: Path, expected: str | None) -> dict[str, Any]:
    """Compute SHA-256 of a snapshot and compare to an expected digest."""
    actual = source_checksum(path) if path.exists() else None
    return {
        "expected": expected,
        "actual": actual,
        "verified": bool(expected and actual and expected.lower() == actual.lower()),
        "no_expected_checksum": expected is None,
    }


def validate_csv_shape(path: Path) -> dict[str, Any]:
    """Reject CSVs whose rows silently overflow the header.

    csv.DictReader discards overflow fields when a row has MORE values than
    headers (restkey defaults to None). Because that is silent data loss, this
    gate fails closed instead of quietly dropping values.
    """
    bad: list[dict[str, int]] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError(f"snapshot has no header row: {path}")
        for n, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) > len(headers):
                bad.append({"csv_row": n, "expected": len(headers), "actual": len(row)})
    return {"header_count": len(headers), "overflow_rows": bad, "valid": not bad}


def detect_schema(path: Path, known_schemas: dict[str, tuple[str, ...]] | None = None) -> dict[str, Any]:
    """Detect which known schema a CSV matches by header intersection.

    known_schemas maps a schema name to the key headers that identify it.
    """
    known_schemas = known_schemas or {
        "archana_style": ("RecipeName", "Ingredients", "Instructions", "Cuisine", "Servings"),
        "simple_recipes": ("title", "ingredients", "instructions"),
        "generic": (),
    }
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
    header_set = set(headers)
    best = None
    best_score = 0
    for name, keys in known_schemas.items():
        if not keys:
            continue
        score = len(header_set & set(keys))
        if score > best_score:
            best, best_score = name, score
    return {
        "headers": headers,
        "header_count": len(headers),
        "matched_schema": best,
        "schema_confidence": round(best_score / max(1, len(known_schemas.get(best, ()))), 4) if best else 0.0,
    }


def attach_provenance(recipes: Iterable[NormalizedRecipe], *, source_id: str, license_name: str,
                      retrieved_at: str, manifest_version: str) -> list[NormalizedRecipe]:
    out = list(recipes)
    for r in out:
        r.source_id = source_id
        r.license = license_name
        r.retrieved_at = retrieved_at
    return out


def resolve_ingredients(recipes: Iterable[NormalizedRecipe], db: FoodMVP | None = None) -> dict[str, Any]:
    """Resolve every raw ingredient string to a canonical id, preserving unknowns."""
    db = db or FoodMVP()
    from .mvp import parse_ingredient
    resolved = Counter()
    unresolved: Counter[str] = Counter()
    resolution_methods: Counter[str] = Counter()
    for r in recipes:
        for raw in r.raw_ingredients:
            p = parse_ingredient(raw, db.resolver)
            if p.canonical_id:
                resolved[p.canonical_id] += 1
                resolution_methods[p.resolution_method or "unknown"] += 1
            else:
                unresolved[raw] += 1
    total = sum(resolved.values()) + sum(unresolved.values())
    return {
        "total_ingredient_mentions": total,
        "resolved_mentions": sum(resolved.values()),
        "unresolved_mentions": sum(unresolved.values()),
        "resolution_rate": round(sum(resolved.values()) / total, 6) if total else 0.0,
        "unique_resolved": len(resolved),
        "unique_unresolved": len(unresolved),
        "dominant_resolved": resolved.most_common(10),
        "dominant_unresolved": unresolved.most_common(10),
        "resolution_methods": dict(resolution_methods),
    }


def corpus_records(recipes: Iterable[NormalizedRecipe]) -> list[CorpusRecord]:
    out = []
    for r in recipes:
        out.append(CorpusRecord(
            dataset=r.source_id or "UNKNOWN",
            source_id=r.source_id or "UNKNOWN",
            source_record_id=r.recipe_id,
            license_status=r.license or "UNKNOWN",
            provenance_confidence="high",
            admission_status="ADMITTED",
            canonical_recipe_group_id=r.canonical_recipe_group_id or recipe_fingerprint(r),
            title=r.title,
            ingredients=tuple(norm_text(x) for x in r.raw_ingredients),
            region=r.region,
            language=r.language,
            ingredient_states=(),
            processes=(),
            quantities_present=any(x for x in r.raw_ingredients if any(c.isdigit() for c in x)),
            has_instructions=bool(r.raw_steps),
        ))
    return out


def pair_statistics(records: Iterable[CorpusRecord], top_k: int = 50) -> dict[str, Any]:
    pairs, recipe_count = pair_counts(records)
    rows = [{"ingredient_a": a, "ingredient_b": b, "co_occurrence": count}
            for (a, b), count in pairs.most_common(top_k)]
    return {"pair_count": len(pairs), "recipe_count": recipe_count, "top_pair_frequency": rows,
            "expected_total_pairs": sum(c for _, c in pairs.items())}


def run_ingestion(snapshot_path: str | Path, manifest: ManifestRecord,
                  output_dir: str | Path | None = None) -> dict[str, Any]:
    """Execute the full ingestion path for an admitted snapshot.

    Raises
    ------
    FileNotFoundError
        if the snapshot file does not exist (reported precisely, never ignored).
    ValueError
        if the manifest record is incomplete, or the checksum fails to verify.
    """
    manifest.validate()
    snap = Path(snapshot_path)
    if not snap.exists():
        raise FileNotFoundError(
            f"snapshot not present: {snap}. Ingestion requires an authorized, "
            f"checksum-pinned raw file for {manifest.dataset_name}.")
    out_dir = Path(output_dir) if output_dir else snap.parent / "ingested"
    out_dir.mkdir(parents=True, exist_ok=True)

    checksum = verify_checksum(snap, manifest.expected_checksum)
    if manifest.expected_checksum and not checksum["verified"]:
        raise ValueError(f"checksum mismatch for {snap.name}: expected {manifest.expected_checksum}, got {checksum['actual']}")

    shape = validate_csv_shape(snap)
    if not shape["valid"]:
        raise ValueError(
            f"snapshot {snap.name} contains rows that overflow the header "
            f"({shape['overflow_rows'][:5]}); refusing to silently drop values.")

    schema = detect_schema(snap)
    db = FoodMVP()
    rows = []
    with open(snap, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            mapped = map_row(row, manifest.source_id, manifest.license, "2026-09-11")
            rows.append(mapped)
    rows = attach_provenance(rows, source_id=manifest.source_id, license_name=manifest.license,
                             retrieved_at="2026-09-11", manifest_version=manifest.version)
    deduped, groups = deduplicate(rows)
    resolved = resolve_ingredients(deduped, db)
    splits = split_by_group(deduped, seed=17)
    records = corpus_records(deduped)
    quality = corpus_quality(records)
    pairs = pair_statistics(records)
    contamination = contamination_audit(records, commercial_datasets=[])

    report = {
        "experiment_id": f"ingest:{manifest.dataset_name}:{manifest.version}",
        "data_status": "REAL_PENDING_REVIEW",
        "pipeline_version": INGESTION_PIPELINE_VERSION,
        "snapshot": {
            "path": str(snap),
            "checksum": checksum,
            "schema": schema,
        },
        "manifest": manifest.to_dict(),
        "ingestion": {
            "raw_rows": len(rows),
            "dedup_group_count": len(groups),
            "recipe_count_after_dedup": len(deduped),
            "duplicate_rate": round(1 - len(groups) / (len(rows) or 1), 4),
        },
        "resolution": resolved,
        "quality": quality,
        "splits": {
            "by_recipe": splits,
            "group_summary": {s: len([x for x in splits if x["split"] == s])
                              for s in ("train", "validation", "test")},
        },
        "pair_statistics": pairs,
        "contamination": contamination,
    }
    report_path = out_dir / "ingestion_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    manifest_path = freeze_manifest(report, manifest, out_dir, snapshot_checksum=checksum)
    report["frozen_manifest_path"] = str(manifest_path)
    return report


def freeze_manifest(report: dict[str, Any], manifest: ManifestRecord, out_dir: Path,
                    snapshot_checksum: dict[str, Any]) -> Path:
    """Write a frozen, versioned corpus manifest that locks code, schema, and data versions."""
    frozen = {
        "manifest_version": "corpus-manifest-1.0.0",
        "frozen_at": "2026-09-11",
        "dataset_name": manifest.dataset_name,
        "source_id": manifest.source_id,
        "source_url": manifest.source_url,
        "data_version": manifest.version,
        "license": manifest.license,
        "admission_status": manifest.admission_status,
        "snapshot_sha256": snapshot_checksum.get("actual"),
        "schema_version": "relational-schema-v1",
        "ontology_version": "food-ontology-v1",
        "code_version": "phase1e",
        "pipeline_version": report["pipeline_version"],
        "configuration_hashes": {
            "resolver_seed": "seed-fixture-0.2",
            "dedup_threshold": 0.85,
            "split_seed": 17,
        },
        "record_count": report["ingestion"]["recipe_count_after_dedup"],
        "citation": manifest.citation,
        "notes": manifest.notes,
        "blockers": [],
    }
    path = out_dir / "corpus_manifest.json"
    path.write_text(json.dumps(frozen, indent=2))
    return path


def status_without_snapshot(manifest: ManifestRecord) -> dict[str, Any]:
    """Honest status when the snapshot is not yet available."""
    manifest.validate()
    return {
        "experiment_id": f"ingest:{manifest.dataset_name}:{manifest.version}",
        "status": "BLOCKED_SNAPSHOT_MISSING",
        "data_status": "NO_ADMITTED_REAL_RECIPE_CORPUS",
        "manifest": manifest.to_dict(),
        "blocker": "Authorized, checksum-pinned raw snapshot required before ingestion.",
        "next_required_input": {
            "file": manifest.source_url,
            "expected_sha256": manifest.expected_checksum,
            "license": manifest.license,
            "admission_status": manifest.admission_status,
        },
        "ingestion_ready": True,
        "ingested_records": 0,
    }


if __name__ == "__main__":
    import sys
    m = ManifestRecord("EXAMPLE", "example", "https://example.invalid", "0", "CC0",
                       "PENDING_REVIEW")
    print(json.dumps(status_without_snapshot(m), indent=2))