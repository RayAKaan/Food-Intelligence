"""Pareto frontier utilities for compatibility-versus-novelty tradeoffs."""
from __future__ import annotations
from typing import Iterable

def dominates(a: dict, b: dict, objectives=("compatibility", "novelty")) -> bool:
    av = [a.get(k) for k in objectives]; bv = [b.get(k) for k in objectives]
    if any(x is None or y is None for x, y in zip(av, bv)): return False
    return all(x >= y for x, y in zip(av, bv)) and any(x > y for x, y in zip(av, bv))

def pareto_frontier(rows: Iterable[dict], objectives=("compatibility", "novelty")) -> list[dict]:
    data = list(rows)
    return [r for i, r in enumerate(data) if not any(j != i and dominates(other, r, objectives) for j, other in enumerate(data))]
