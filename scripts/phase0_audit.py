#!/usr/bin/env python3
"""Deterministic, dependency-free Phase 0 repository and readiness audit.

This script performs static inspection only: it never imports application modules,
executes project code, accesses the network, or modifies production data.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

INVENTORY_DIRS = (
    "src", "tests", "docs", "data", "database", "experiments",
    "benchmarks", "scripts", ".github/workflows",
)
REQUIRED_PATHS = (
    "pyproject.toml", "README.md", "src/food_intelligence", "tests",
    ".github/workflows/ci.yml", "scripts/phase0_audit.py",
)
PYTHON_AREAS = ("src", "tests", "scripts")


def parse_python(path: Path) -> ast.AST | None:
    """Parse a Python file without importing or executing it."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return None


def python_files(root: Path, areas: tuple[str, ...] = PYTHON_AREAS) -> list[Path]:
    files: list[Path] = []
    for area in areas:
        directory = root / area
        if directory.exists():
            files.extend(directory.rglob("*.py"))
    return sorted(set(path for path in files if path.is_file()))


def count_test_functions(files: list[Path]) -> int:
    count = 0
    for path in files:
        if not path.name.startswith("test_"):
            continue
        tree = parse_python(path)
        if tree is None:
            continue
        count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return count


def relative_files(root: Path, directory: str) -> list[str]:
    path = root / directory
    if not path.exists():
        return []
    return sorted(
        item.relative_to(root).as_posix()
        for item in path.rglob("*")
        if item.is_file()
    )


def imported_roots(files: list[Path]) -> tuple[set[str], list[str]]:
    imports: set[str] = set()
    parse_errors: list[str] = []
    for path in files:
        tree = parse_python(path)
        if tree is None:
            parse_errors.append(path.as_posix())
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.add(node.module.split(".")[0])
    return imports, sorted(parse_errors)


def module_inventory(root: Path) -> list[dict[str, Any]]:
    source = root / "src/food_intelligence"
    result: list[dict[str, Any]] = []
    for path in sorted(source.glob("*.py")):
        tree = parse_python(path)
        classes: list[str] = []
        functions: list[str] = []
        if tree is not None:
            classes = sorted(
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            )
            functions = sorted(
                node.name for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not node.name.startswith("_")
            )
        result.append({
            "path": path.relative_to(root).as_posix(),
            "module": path.stem,
            "classes": classes,
            "public_functions": functions,
        })
    return result


def schema_tables(root: Path) -> list[str]:
    schema = root / "database/schema.sql"
    if not schema.exists():
        return []
    text = schema.read_text(encoding="utf-8")
    return sorted(set(re.findall(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)",
        text,
        flags=re.IGNORECASE,
    )))


def food_mvp_coupling(files: list[Path]) -> dict[str, int]:
    counts = {
        "explicit_imports": 0,
        "parse_ingredient_references": 0,
        "files_with_food_mvp_reference": 0,
    }
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        counts["explicit_imports"] += (
            text.count("from .mvp import FoodMVP")
            + text.count("from food_intelligence.mvp import FoodMVP")
        )
        counts["parse_ingredient_references"] += text.count("parse_ingredient")
        if "FoodMVP" in text:
            counts["files_with_food_mvp_reference"] += 1
    return counts


def build_report(root: Path) -> dict[str, Any]:
    area_files = {area: relative_files(root, area) for area in INVENTORY_DIRS}
    all_python = python_files(root)
    _, parse_errors = imported_roots(all_python)
    source = root / "src/food_intelligence"
    source_files = sorted(source.glob("*.py")) if source.exists() else []
    source_imports, _ = imported_roots(source_files)
    tests = root / "tests"
    test_files = sorted(tests.rglob("test_*.py")) if tests.exists() else []
    fixture_paths = sorted(
        path for path in area_files.get("data", [])
        if any(word in path.lower() for word in ("fixture", "synthetic", "candidate", "sample"))
    )
    required_paths = {path: (root / path).exists() for path in REQUIRED_PATHS}
    third_party = sorted(
        name for name in source_imports
        if name not in sys.stdlib_module_names and name not in {"food_intelligence"}
    )
    pyproject = root / "pyproject.toml"
    project_text = pyproject.read_text(encoding="utf-8") if pyproject.exists() else ""
    requirement = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', project_text)
    checks = {
        "required_paths_present": all(required_paths.values()),
        "production_modules_present": bool(source_files),
        "test_files_present": bool(test_files),
        "ci_workflow_present": (root / ".github/workflows/ci.yml").is_file(),
        "python_syntax_clean": not parse_errors,
    }
    return {
        "phase": "0",
        "repository": "RayAKaan/Food-Intelligence",
        "audit_version": 2,
        "python_requires": requirement.group(1) if requirement else None,
        "inventory": {
            "source_modules": len(source_files),
            "test_files": len(test_files),
            "test_functions": count_test_functions(test_files),
            "files_by_area": {area: len(files) for area, files in area_files.items()},
            "schema_tables": schema_tables(root),
        },
        "source_modules": module_inventory(root),
        "test_files": [path.relative_to(root).as_posix() for path in test_files],
        "files_by_area": area_files,
        "required_paths": required_paths,
        "checks": checks,
        "parse_errors": parse_errors,
        "external_runtime_imports": third_party,
        "fixture_or_synthetic_paths": fixture_paths,
        "production_fixture_coupling": food_mvp_coupling(source_files),
        "interpretation": {
            "synthetic_data_is_scientific_evidence": False,
            "external_imports_are_automatically_approved": False,
            "food_mvp_coupling_is_automatically_a_failure": False,
            "note": (
                "This is a static inventory and readiness gate, not proof of scientific validity. "
                "Reported architecture debt requires deliberate review."
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="also write the JSON report to this path")
    parser.add_argument(
        "--strict", action="store_true",
        help="exit non-zero if a required baseline/readiness check fails",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    report = build_report(root)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if args.strict and not all(report["checks"].values()):
        failed = [name for name, passed in report["checks"].items() if not passed]
        print("Phase 0 strict audit failed: " + ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
