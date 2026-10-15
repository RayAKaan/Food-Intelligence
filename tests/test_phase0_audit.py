"""Regression tests for the dependency-free Phase 0 repository audit."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "phase0_audit.py"


def run_audit(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AUDIT), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_phase0_audit_is_deterministic_and_machine_readable() -> None:
    first = run_audit()
    second = run_audit()

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout
    report = json.loads(first.stdout)
    assert report["phase"] == "0"
    assert report["repository"] == "RayAKaan/Food-Intelligence"
    assert report["inventory"]["source_modules"] > 0
    assert report["inventory"]["test_files"] > 0
    assert report["source_modules"]
    assert report["required_paths"]["scripts/phase0_audit.py"] is True


def test_phase0_strict_gate_passes_for_repository_baseline() -> None:
    result = run_audit("--strict")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert all(report["checks"].values())
    assert report["parse_errors"] == []


def test_phase0_audit_can_write_report_to_requested_path(tmp_path: Path) -> None:
    destination = tmp_path / "audit" / "report.json"
    result = run_audit("--strict", "--output", str(destination))
    assert result.returncode == 0, result.stderr
    assert destination.is_file()
    assert json.loads(destination.read_text(encoding="utf-8")) == json.loads(result.stdout)
