"""Leakage-aware benchmark and ablation harness for the deterministic substrate.

All bundled data are synthetic software fixtures. Results are regression checks,
not scientific claims.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Iterable
from .mvp import FoodMVP

@dataclass(frozen=True)
class RetrievalCase:
    query_target: dict[str, float]
    expected: frozenset[str]
    blocked: frozenset[str] = frozenset()


def recall_at_k(predicted: Iterable[str], expected: Iterable[str], k: int = 5) -> float:
    """Set-based recall@k: fraction of relevant items recovered in top-k."""
    gold = set(expected)
    if not gold: return 1.0
    return len(gold & set(list(predicted)[:k])) / len(gold)


def reciprocal_rank(predicted: Iterable[str], expected: Iterable[str]) -> float:
    gold = set(expected)
    for i, item in enumerate(predicted, 1):
        if item in gold: return 1.0 / i
    return 0.0


def ndcg_at_k(predicted: Iterable[str], expected: Iterable[str], k: int = 5) -> float:
    import math
    gold = set(expected)
    if not gold: return 1.0
    vals = [1.0 / math.log2(i + 2) for i, item in enumerate(list(predicted)[:k]) if item in gold]
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(k, len(gold))))
    return sum(vals) / ideal if ideal else 0.0


def leakage_audit(train_ids: Iterable[str], test_ids: Iterable[str]) -> dict:
    a, b = set(train_ids), set(test_ids)
    overlap = sorted(a & b)
    return {"passed": not overlap, "overlap": overlap, "train_size": len(a), "test_size": len(b)}


def run_fixture_benchmark() -> dict:
    db = FoodMVP()
    cases = [
        RetrievalCase({"sour": .8, "smoky": .8}, frozenset({"tamarind", "black cardamom"})),
        RetrievalCase({"nutty": .8, "citrus": .4}, frozenset({"sesame", "ginger"})),
        RetrievalCase({"creamy": .6, "sour": .8}, frozenset({"coconut", "tamarind"})),
        RetrievalCase({"earthy": .8, "spicy": .5}, frozenset({"cumin", "chili"})),
        RetrievalCase({"sweet": .5, "floral": .6}, frozenset({"green cardamom", "jaggery"})),
        RetrievalCase({"pungent": .8, "sulfurous": .7}, frozenset({"garlic", "mustard seed"})),
        RetrievalCase({"herbal": .8, "citrus": .3}, frozenset({"coriander", "curry leaf"})),
        RetrievalCase({"woody": .7, "spicy": .5}, frozenset({"cinnamon", "clove"})),
        RetrievalCase({"umami": .6, "sour": .5}, frozenset({"tomato", "tamarind"})),
        RetrievalCase({"roasted": .6, "nutty": .5}, frozenset({"peanut", "sesame"})),
        RetrievalCase({"caramelized": .6, "sweet": .4}, frozenset({"jaggery"})),
    ]
    rows=[]
    for case in cases:
        structured=[x["name"] for x in db.retrieve(case.query_target,set(),5,"structured")]
        semantic=[x["name"] for x in db.retrieve(case.query_target,set(),5,"semantic")]
        hybrid=[x["name"] for x in db.retrieve(case.query_target,set(),5,"hybrid")]
        rows.append({
            "target": case.query_target, "expected": sorted(case.expected),
            "structured": structured, "semantic": semantic, "hybrid": hybrid,
            "structured_recall@5": recall_at_k(structured, case.expected),
            "semantic_recall@5": recall_at_k(semantic, case.expected),
            "hybrid_recall@5": recall_at_k(hybrid, case.expected),
            "structured_mrr": reciprocal_rank(structured, case.expected),
            "semantic_mrr": reciprocal_rank(semantic, case.expected),
            "hybrid_mrr": reciprocal_rank(hybrid, case.expected),
            "structured_ndcg@5": ndcg_at_k(structured, case.expected),
            "semantic_ndcg@5": ndcg_at_k(semantic, case.expected),
            "hybrid_ndcg@5": ndcg_at_k(hybrid, case.expected),
        })
    return {
        "experiment_id": "phase1e_fixture_benchmark_v3",
        "data_status": "SYNTHETIC",
        "warning": "Synthetic regression fixture only; no scientific generalization.",
        "leakage_audit": leakage_audit([r.recipe_id for r in db.recipes[:len(db.recipes)//2]], [r.recipe_id for r in db.recipes[len(db.recipes)//2:]]),
        "metrics": {
            "structured_mean_recall@5": sum(r["structured_recall@5"] for r in rows)/len(rows),
            "semantic_mean_recall@5": sum(r["semantic_recall@5"] for r in rows)/len(rows),
            "hybrid_mean_recall@5": sum(r["hybrid_recall@5"] for r in rows)/len(rows),
            "structured_mean_mrr": sum(r["structured_mrr"] for r in rows)/len(rows),
            "semantic_mean_mrr": sum(r["semantic_mrr"] for r in rows)/len(rows),
            "hybrid_mean_mrr": sum(r["hybrid_mrr"] for r in rows)/len(rows),
            "structured_mean_ndcg@5": sum(r["structured_ndcg@5"] for r in rows)/len(rows),
            "semantic_mean_ndcg@5": sum(r["semantic_ndcg@5"] for r in rows)/len(rows),
            "hybrid_mean_ndcg@5": sum(r["hybrid_ndcg@5"] for r in rows)/len(rows),
        },
        "cases": rows,
    }


def run() -> dict: return run_fixture_benchmark()

if __name__ == "__main__": print(json.dumps(run(), indent=2))
