import json
from pathlib import Path

import pytest

from food_intelligence.ingest_pipeline import (
    ManifestRecord,
    run_ingestion,
    status_without_snapshot,
    verify_checksum,
)
from food_intelligence.ingestion import source_checksum


TEST_CSV = """RecipeName,Ingredients,Instructions,Cuisine,Servings
"Tomato Dal","tomato,tamarind,lentil,ginger,cumin",boil then temper,Indian,4
Coconut Chutney,"coconut,sesame,ginger,chili",grind and blend,Indian,2
"Smoky Tomato Curry","tomato,onion,garlic,black cardamom,cumin",fry and simmer,Indian,6
"""

RAGGED_CSV = """RecipeName,Ingredients
"Tomato Dal",tomato,tamarind,lentil
"""


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    p = tmp_path / "snapshot"
    p.mkdir()
    (p / "recipes.csv").write_text(TEST_CSV, encoding="utf-8")
    return p


def make_manifest(expected_checksum: str | None = None, **overrides) -> ManifestRecord:
    kwargs = dict(
        dataset_name="TEST_DATASET",
        source_id="test-source",
        source_url="https://example.invalid/test",
        version="TEST-0",
        license="TEST_LICENSE",
        admission_status="PENDING_REVIEW",
        expected_checksum=expected_checksum,
        research_status="PENDING_REVIEW",
        commercial_status="BLOCKED",
    )
    kwargs.update(overrides)
    return ManifestRecord(**kwargs)


def test_snapshot_missing_fails_closed(tmp_path: Path):
    m = make_manifest()
    with pytest.raises(FileNotFoundError) as e:
        run_ingestion(tmp_path / "does_not_exist.csv", m, tmp_path / "out")
    assert "snapshot not present" in str(e.value)


def test_checksum_mismatch_fails_closed(snapshot_dir: Path, tmp_path: Path):
    snap = snapshot_dir / "recipes.csv"
    wrong = source_checksum(__file__)
    with pytest.raises(ValueError):
        run_ingestion(snap, make_manifest(expected_checksum=wrong), tmp_path / "out")


def test_overflow_rows_fail_closed_instead_of_silently_dropping(tmp_path: Path):
    p = tmp_path / "ragged.csv"
    p.write_text(RAGGED_CSV, encoding="utf-8")
    with pytest.raises(ValueError) as e:
        run_ingestion(p, make_manifest(), tmp_path / "out")
    assert "overflow" in str(e.value)


def test_incomplete_manifest_fails_closed(tmp_path: Path):
    m = ManifestRecord(dataset_name="x", source_id=None, source_url=None, version=None, license=None, admission_status=None)
    with pytest.raises(ValueError):
        run_ingestion(tmp_path / "x.csv", m, tmp_path / "out")


def test_full_ingestion_path_works_end_to_end(snapshot_dir: Path, tmp_path: Path):
    snap = snapshot_dir / "recipes.csv"
    checksum = source_checksum(snap)
    out = run_ingestion(snap, make_manifest(expected_checksum=checksum), tmp_path / "out")

    assert out["data_status"] == "REAL_PENDING_REVIEW"
    assert out["snapshot"]["checksum"]["verified"] is True
    assert out["snapshot"]["schema"]["matched_schema"] == "archana_style"
    assert out["ingestion"]["recipe_count_after_dedup"] == 3
    assert out["ingestion"]["duplicate_rate"] == 0.0
    assert out["resolution"]["resolution_rate"] > .5
    assert out["quality"]["recipe_count"] == 3
    assert set(out["splits"]["group_summary"]) == {"train", "validation", "test"}
    assert out["pair_statistics"]["pair_count"] >= 3
    assert out["frozen_manifest_path"].endswith("corpus_manifest.json")
    assert out["contamination"]["status"] == "FAIL"
    assert out["contamination"]["count"] == 3


def test_frozen_manifest_contains_locking_columns(snapshot_dir: Path, tmp_path: Path):
    snap = snapshot_dir / "recipes.csv"
    out = run_ingestion(snap, make_manifest(expected_checksum=source_checksum(snap)), tmp_path / "out")
    frozen = json.loads(Path(out["frozen_manifest_path"]).read_text(encoding="utf-8"))
    assert frozen["snapshot_sha256"] == source_checksum(snap)
    assert frozen["license"] == "TEST_LICENSE"
    assert frozen["record_count"] == 3


def test_status_without_snapshot_is_honest():
    s = status_without_snapshot(make_manifest())
    assert s["status"] == "BLOCKED_SNAPSHOT_MISSING"
    assert s["data_status"] == "NO_ADMITTED_REAL_RECIPE_CORPUS"
    assert s["ingested_records"] == 0
    assert s["ingestion_ready"] is True


def test_verify_checksum_missing_file():
    assert verify_checksum(Path("nope.csv"), "abc")["verified"] is False