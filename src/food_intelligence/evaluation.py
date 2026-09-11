"""Phase 1E evaluation, ablation, failure-analysis, and readiness gates.

This module is deliberately usable with synthetic fixtures now and authorized
real snapshots later. It refuses to label synthetic metrics as scientific.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, math, random
from typing import Callable, Iterable, Sequence

from .benchmark import RetrievalCase, recall_at_k, reciprocal_rank, ndcg_at_k, leakage_audit
from .mvp import FoodMVP
from .corpus import CorpusRecord, corpus_quality, contamination_audit

@dataclass(frozen=True)
class MetricCI:
    estimate: float
    lower: float
    upper: float
    n: int
    bootstrap_samples: int


def bootstrap_ci(values: Sequence[float], *, seed: int = 17, samples: int = 2000, alpha: float = .05) -> MetricCI:
    vals = [float(v) for v in values]
    if not vals:
        return MetricCI(0.0, 0.0, 0.0, 0, 0)
    if len(vals) == 1:
        x = vals[0]; return MetricCI(x, x, x, 1, 0)
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        draw = [vals[rng.randrange(len(vals))] for _ in vals]
        means.append(sum(draw) / len(draw))
    means.sort()
    lo = means[max(0, int((alpha / 2) * len(means)) - 1)]
    hi = means[min(len(means) - 1, int((1 - alpha / 2) * len(means)))]
    return MetricCI(sum(vals)/len(vals), lo, hi, len(vals), samples)


def paired_bootstrap_delta(a: Sequence[float], b: Sequence[float], *, seed: int = 17, samples: int = 2000) -> MetricCI:
    if len(a) != len(b) or not a:
        raise ValueError("paired bootstrap requires equal non-empty sequences")
    deltas = [float(x) - float(y) for x, y in zip(a, b)]
    return bootstrap_ci(deltas, seed=seed, samples=samples)


def _fixture_cases() -> list[RetrievalCase]:
    return [
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


def run_ablation() -> dict:
    db = FoodMVP()
    modes = ("structured", "semantic", "hybrid")
    per_mode = {}
    for mode in modes:
        recalls=[]; mrrs=[]; ndcgs=[]
        for case in _fixture_cases():
            pred=[x["name"] for x in db.retrieve(case.query_target, set(), 5, mode)]
            recalls.append(recall_at_k(pred, case.expected))
            mrrs.append(reciprocal_rank(pred, case.expected))
            ndcgs.append(ndcg_at_k(pred, case.expected))
        per_mode[mode] = {
            "recall@5": asdict(bootstrap_ci(recalls)),
            "mrr": asdict(bootstrap_ci(mrrs)),
            "ndcg@5": asdict(bootstrap_ci(ndcgs)),
            "case_values": {"recall@5": recalls, "mrr": mrrs, "ndcg@5": ndcgs},
        }
    deltas = {}
    for metric in ("recall@5", "mrr", "ndcg@5"):
        structured = per_mode["structured"]["case_values"][metric]
        semantic = per_mode["semantic"]["case_values"][metric]
        hybrid = per_mode["hybrid"]["case_values"][metric]
        deltas[metric] = {
            "hybrid_minus_structured": asdict(paired_bootstrap_delta(hybrid, structured)),
            "hybrid_minus_semantic": asdict(paired_bootstrap_delta(hybrid, semantic)),
        }
    return {
        "experiment_id": "phase1e_ablation_fixture_v1",
        "data_status": "SYNTHETIC",
        "scientific_claims_allowed": False,
        "warning": "Fixture ablation is regression evidence only; it does not establish real-world superiority.",
        "models": per_mode,
        "paired_deltas": deltas,
    }


def failure_analysis(cases: Iterable[RetrievalCase] | None = None, *, mode: str = "hybrid") -> dict:
    db = FoodMVP(); cases = list(cases or _fixture_cases())
    failures=[]
    categories={"missed_relevant":0,"empty_gold":0,"blocked_or_excluded":0,"fully_recovered":0}
    for case in cases:
        pred=[x["name"] for x in db.retrieve(case.query_target, set(), 5, mode)]
        missed=sorted(set(case.expected)-set(pred))
        if not case.expected:
            categories["empty_gold"] += 1
        elif missed:
            categories["missed_relevant"] += 1
            failures.append({"target":case.query_target,"expected":sorted(case.expected),"predicted":pred,"missed":missed})
        else:
            categories["fully_recovered"] += 1
        blocked=sorted(set(case.blocked)&set(pred))
        if blocked:
            categories["blocked_or_excluded"] += len(blocked)
    return {"data_status":"SYNTHETIC","mode":mode,"categories":categories,"failures":failures,"count":len(cases)}


def real_corpus_readiness(records: Iterable[CorpusRecord], *, commercial_datasets: Iterable[str] = ()) -> dict:
    rows=list(records)
    quality=corpus_quality(rows)
    contamination=contamination_audit(rows, commercial_datasets) if commercial_datasets else {"status":"NOT_RUN","count":0}
    checks={
        "has_admitted_records": bool(rows),
        "has_multiple_recipes": len(rows) >= 2,
        "has_instructions": quality["instruction_completeness"] > 0,
        "has_ingredients": quality["ingredient_count"] > 0,
        "no_duplicate_groups_only": quality["canonical_recipe_count"] >= 2 if rows else False,
        "commercial_contamination": contamination.get("status") != "FAIL",
    }
    return {"data_status":"REAL" if rows else "NO_REAL_DATA","quality":quality,"checks":checks,"ready_for_scientific_benchmark":all(checks.values())}


def research_readiness_gate(*, real_records: Iterable[CorpusRecord], synthetic_ablation: dict, critical_safety_failure: bool=False, licensing_failure: bool=False) -> dict:
    real=list(real_records)
    blockers=[]
    if not real: blockers.append("NO_ADMITTED_REAL_RECIPE_CORPUS")
    if licensing_failure: blockers.append("LICENSING_FAILURE")
    if critical_safety_failure: blockers.append("CRITICAL_SAFETY_FAILURE")
    if not synthetic_ablation.get("scientific_claims_allowed") is False:
        blockers.append("SYNTHETIC_CLAIM_BOUNDARY_MISSING")
    return {
        "gate": "PHASE_1E_RESEARCH_READINESS",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "real_recipe_count": len(real),
        "scientific_claims_allowed": bool(real) and not blockers,
        "next_required_action": "Acquire an authorized, versioned, checksum-pinned research recipe snapshot" if not real else "Run leakage-safe real benchmark and blinded human evaluation",
    }


def run_full_evaluation() -> dict:
    from .benchmark import run_fixture_benchmark
    benchmark=run_fixture_benchmark()
    ablation=run_ablation()
    failures=failure_analysis()
    gate=research_readiness_gate(real_records=[], synthetic_ablation=ablation)
    return {
        "experiment_id":"phase1e_full_evaluation_v1",
        "data_status":"SYNTHETIC_PLUS_CORPUS_STATUS",
        "benchmark":benchmark,
        "ablation":ablation,
        "failure_analysis":failures,
        "readiness_gate":gate,
    }
