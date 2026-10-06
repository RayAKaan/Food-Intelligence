#!/usr/bin/env python3
"""Phase 0 repository audit."""
from __future__ import annotations
import argparse, ast, json
from pathlib import Path

def count_tests(path: Path) -> int:
    count = 0
    for file in sorted(path.glob("test_*.py")):
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        except SyntaxError:
            continue
        count += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_") for n in ast.walk(tree))
    return count

def imported_names(path: Path) -> set[str]:
    names: set[str] = set()
    for file in sorted(path.rglob("*.py")):
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
    return names

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    src, tests, workflows = root/"src"/"food_intelligence", root/"tests", root/".github"/"workflows"
    source_files, test_files = sorted(src.glob("*.py")), sorted(tests.glob("test_*.py"))
    production_text = "\n".join(p.read_text(encoding="utf-8") for p in source_files)
    report = {
        "phase": "0",
        "repository": "RayAKaan/Food-Intelligence",
        "python_requires": ">=3.10",
        "source_modules": len(source_files),
        "test_files": len(test_files),
        "test_functions": count_tests(tests),
        "workflow_files": sorted(str(p.relative_to(root)) for p in workflows.glob("*.yml")) + sorted(str(p.relative_to(root)) for p in workflows.glob("*.yaml")),
        "external_runtime_imports": sorted(imported_names(src) - {
            "__future__","argparse","ast","collections","contextlib","csv","dataclasses","datetime","enum",
            "itertools","json","math","os","pathlib","random","re","sqlite3","statistics","sys","typing","uuid"
        }),
        "production_fixture_coupling": {
            "food_mvp_imports": production_text.count("from .mvp import FoodMVP") + production_text.count("from food_intelligence.mvp import FoodMVP")
        },
        "required_paths": {
            "pyproject.toml": (root/"pyproject.toml").exists(),
            "README.md": (root/"README.md").exists(),
            "src/food_intelligence": src.exists(),
            "tests": tests.exists()
        }
    }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
