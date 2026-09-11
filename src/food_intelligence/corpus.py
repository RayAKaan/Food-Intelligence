"""Small, provenance-first real-corpus utilities.

The module deliberately accepts records only when an admitted manifest says so.
It does not download data, infer missing facts, or turn co-occurrence into
sensory/causal claims.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from math import log
from typing import Iterable
import hashlib

@dataclass(frozen=True)
class CorpusRecord:
    dataset: str
    source_id: str
    source_record_id: str
    license_status: str
    provenance_confidence: str
    admission_status: str
    canonical_recipe_group_id: str | None = None
    title: str | None = None
    ingredients: tuple[str, ...] = ()
    region: str | None = None
    language: str | None = None
    ingredient_states: tuple[str, ...] = ()
    processes: tuple[str, ...] = ()
    quantities_present: bool = False
    has_instructions: bool = False

    def to_dict(self):
        return asdict(self)

def assert_admitted(records: Iterable[CorpusRecord], allowed_status="ADMITTED"):
    records = list(records)
    bad = [r.source_record_id for r in records if r.admission_status != allowed_status]
    if bad:
        raise ValueError(f"non-admitted records supplied: {bad}")
    return records

def canonical_groups(records):
    groups = defaultdict(list)
    for r in records:
        groups[r.canonical_recipe_group_id or f"{r.dataset}:{r.source_record_id}"].append(r)
    return groups

def corpus_quality(records: Iterable[CorpusRecord]):
    rows = list(records); n = len(rows)
    denom = n or 1
    groups = canonical_groups(rows)
    ingredients = {x for r in rows for x in r.ingredients}
    states = {x for r in rows for x in r.ingredient_states}
    processes = {x for r in rows for x in r.processes}
    return {
        "recipe_count": n,
        "canonical_recipe_count": len(groups),
        "ingredient_count": len(ingredients),
        "canonical_ingredient_count": len(ingredients),
        "ingredient_state_count": len(states),
        "process_count": len(processes),
        "duplicate_rate": round(1 - len(groups) / denom, 4),
        "quantity_completeness": round(sum(r.quantities_present for r in rows) / denom, 4),
        "instruction_completeness": round(sum(r.has_instructions for r in rows) / denom, 4),
        "state_completeness": round(sum(bool(r.ingredient_states) for r in rows) / denom, 4),
        "process_completeness": round(sum(bool(r.processes) for r in rows) / denom, 4),
        "region_completeness": round(sum(bool(r.region) for r in rows) / denom, 4),
        "language_completeness": round(sum(bool(r.language) for r in rows) / denom, 4),
    }

def pair_counts(records: Iterable[CorpusRecord], cuisine=None, region=None):
    pairs = Counter(); recipes = 0
    for r in records:
        if cuisine and r.dataset != cuisine: continue
        if region and r.region != region: continue
        recipes += 1
        xs = sorted(set(r.ingredients))
        for i, a in enumerate(xs):
            for b in xs[i + 1:]: pairs[(a, b)] += 1
    return pairs, recipes

def npmi(pair_count, a_count, b_count, recipe_count, smoothing=0.5):
    if recipe_count <= 0: return None
    p_ab = (pair_count + smoothing) / (recipe_count + smoothing * 2)
    p_a = (a_count + smoothing) / (recipe_count + smoothing * 2)
    p_b = (b_count + smoothing) / (recipe_count + smoothing * 2)
    pmi = log(p_ab / (p_a * p_b))
    return round(pmi / (-log(p_ab)), 6) if p_ab < 1 else 1.0

def pairing_baseline(records: Iterable[CorpusRecord], top_k=100, min_pair_count=1):
    rows = list(records); pairs, n = pair_counts(rows)
    ingredient_counts = Counter(x for r in rows for x in set(r.ingredients))
    out = []
    for (a, b), count in pairs.items():
        if count < min_pair_count: continue
        out.append({"ingredient_a": a, "ingredient_b": b, "co_occurrence": count,
                    "recipe_count": n, "pmi_npmi": npmi(count, ingredient_counts[a], ingredient_counts[b], n),
                    "evidence_source": sorted({f"{r.dataset}:{r.source_record_id}" for r in rows if a in r.ingredients and b in r.ingredients}),
                    "claim_type": "SOURCE_DERIVED"})
    return sorted(out, key=lambda x: (-x["co_occurrence"], x["ingredient_a"], x["ingredient_b"]))[:top_k]

def corpus_relative_novelty(candidate, records):
    rows = list(records); pairs, n = pair_counts(rows)
    pair = tuple(sorted(candidate))
    count = pairs.get(pair, 0)
    if n == 0: return {"label": "UNKNOWN", "pair_frequency": 0, "indexed_recipe_count": 0}
    label = "COMMON" if count / n >= .01 else "UNDERREPRESENTED" if count else "RARE_IN_INDEXED_CORPUS"
    return {"label": label, "pair_frequency": round(count / n, 6), "indexed_recipe_count": n,
            "claim_type": "SOURCE_DERIVED"}

def leakage_safe_split(records, seed=17):
    result = []
    for r in records:
        group = r.canonical_recipe_group_id or f"{r.dataset}:{r.source_record_id}"
        bucket = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()[:8], 16) / 0xffffffff
        split = "test" if bucket < .2 else "validation" if bucket < .3 else "training"
        result.append({"dataset": r.dataset, "source_record_id": r.source_record_id,
                       "canonical_recipe_group_id": group, "split": split})
    return result

def contamination_audit(records: Iterable[CorpusRecord], commercial_datasets):
    bad = [r.to_dict() for r in records if r.dataset not in set(commercial_datasets)]
    return {"status": "FAIL" if bad else "PASS", "count": len(bad), "contaminating_records": bad}
