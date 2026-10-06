#!/usr/bin/env python3
"""Phase 0A repository inventory.

This audit is intentionally dependency-free. It inventories repository structure
without importing application code or changing runtime behavior.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


STDLIB_IMPORTS = {
    "__future__", "argparse", "ast", "collections", "contextlib", "csv",
    "dataclasses", "datetime", "enum", "itertools", "json", "math", "os",
    "pathlib", "random", "re", "sqlite3", "statistics", "sys", "typing",
    "uuid",
}

INVENTORY_DIRS = (
    "src",
    "tests",
    "docs",
    "data",
    "database",
    "experiments",
    "benchmarks",
    "scripts",
    ".github/workflows",
)


def parse_python(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def count_tests(path: Path) -> int:
    count = 0
    for file in sorted(path.glob("test_*.py")):
        tree = parse_python(file)
        if tree is None:
            continue
        count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return count


def imported_names(path: Path) -> set[str]:
    names: set[str] = set()
    for file in sorted(path.rglob("*.py")):
        tree = parse_python(file)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
    return names


def relative_files(root: Path, directory: str, pattern: str = "*") -> list[str]:
    path = root / directory
    if not path.exists():
        return []
    return sorted(
        str(item.relative_to(root))
        for item in path.rglob(pattern)
        if item.is_file()
    )


def schema_tables(root: Path) -> list[str]:
    schema = root / "database/schema.sql"
    if not schema.exists():
        return []
    text = schema.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z_][a-zA-Z0-9_]*)", text)))


def source_module_inventory(root: Path) -> list[dict[str, object]]:
    src = root / "src/food_intelligence"
    modules: list[dict[str, object]] = []
    for path in sorted(src.glob("*.py")):
        tree = parse_python(path)
        classes: list[str] = []
        functions: list[str] = []
        if tree is not None:
            classes = sorted(
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            )
            functions = sorted(
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not node.name.startswith("_")
            )
        modules.append({
            "path": str(path.relative_to(root)),
            "module": path.stem,
            "classes": classes,
            "public_functions": functions,
        })
    return modules


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    src = root / "src/food_intelligence"
    tests = root / "tests"
    workflows = root / ".github/workflows"

    source_files = sorted(src.glob("*.py"))
    test_files = sorted(tests.glob("test_*.py"))
    production_text = "\n".join(
        p.read_text(encoding="utf-8") for p in source_files
    )

    files_by_area = {
        directory: relative_files(root, directory)
        for directory in INVENTORY_DIRS
    }

    fixture_markers = sorted(
        path
        for path in files_by_area.get("data", [])
        if any(token in path.lower() for token in ("fixture", "synthetic", "candidate"))
    )

    report = {
        "phase": "0A",
        "repository": "RayAKaan/Food-Intelligence",
        "python_requires": ">=3.10",
        "inventory": {
            "source_modules": len(source_files),
            "test_files": len(test_files),
            "test_functions": count_tests(tests),
            "documentation_files": len(files_by_area["docs"]),
            "data_files": len(files_by_area["data"]),
            "experiment_files": len(files_by_area["experiments"]),
            "benchmark_files": len(files_by_area["benchmarks"]),
            "workflow_files": len(files_by_area[".github/workflows"]),
            "database_files": len(files_by_area["database"]),
            "schema_tables": schema_tables(root),
        },
        "source_modules": source_module_inventory(root),
        "test_files": [str(p.relative_to(root)) for p in test_files],
        "workflow_files": files_by_area[".github/workflows"],
        "important_paths": {
            "pyproject.toml": (root / "pyproject.toml").exists(),
            "README.md": (root / "README.md").exists(),
            "database/schema.sql": (root / "database/schema.sql").exists(),
            "src/food_intelligence": src.exists(),
            "tests": tests.exists(),
        },
        "fixture_or_synthetic_paths": fixture_markers,
        "external_runtime_imports": sorted(imported_names(src) - STDLIB_IMPORTS),
        "production_fixture_coupling": {
            "food_mvp_imports": production_text.count("from .mvp import FoodMVP")
            + production_text.count("from food_intelligence.mvp import FoodMVP")
        },
    }

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
