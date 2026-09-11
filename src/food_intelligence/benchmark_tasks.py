"""Additional Phase 1E benchmark tasks beyond sensory-target retrieval.

Covered tasks:
  - alias resolution (Hindi/regional -> canonical id)
  - ingredient-state resolution (state preserved, identity stable)
  - constraint pass rate (hard blocks are never ranked; unknown safety is not a block)
  - held-out pair prediction (pair co-occurrence baseline vs model)
  - process validity (fail-closed transformation validation)

All inputs are synthetic fixtures. Results are regression evidence only.
"""
from __future__ import annotations
from dataclasses import dataclass

from .mvp import FoodMVP, parse_ingredient
from .transformations import instantiate, validate_transformation, default_process_catalog


@dataclass(frozen=True)
class AliasCase:
    alias: str
    expected: str
    must_preserve_state: tuple[str, str] | None = None  # (raw, expected_state)


ALIAS_CASES = [
    AliasCase("jeera", "cumin"),
    AliasCase("imli", "tamarind"),
    AliasCase("haldi", "turmeric"),
    AliasCase("rai", "mustard seed"),
    AliasCase("sarso", "mustard seed"),
    AliasCase("kadi patta", "curry leaf"),
    AliasCase("tej patta", "bay leaf"),
    AliasCase("adrak", "ginger"),
    AliasCase("lahsun", "garlic"),
    AliasCase("methi", "fenugreek"),
    AliasCase("kasoori methi", "fenugreek"),
    AliasCase("saunf", "fennel"),
    AliasCase("laung", "clove"),
    AliasCase("dalchini", "cinnamon"),
    AliasCase("choti elaichi", "green cardamom"),
    AliasCase("badi elaichi", "black cardamom"),
    AliasCase("kali mirch", "black pepper"),
    AliasCase("amchur", "mango powder"),
    AliasCase("nariyal tel", "coconut oil"),
    AliasCase("sarson ka tel", "mustard oil"),
    # Ambiguity must be preserved, never silently resolved.
    AliasCase("cardamom", "__AMBIGUOUS__"),
    AliasCase("mustard", "__AMBIGUOUS__"),
    # Unknown spellings must stay unresolved rather than invent an identity.
    AliasCase("fire roast", "__UNRESOLVABLE__"),
    AliasCase("lahsuna", "__UNRESOLVABLE__"),
]


def run_alias_benchmark() -> dict:
    db = FoodMVP()
    rows = []
    for case in ALIAS_CASES:
        p = parse_ingredient(case.alias, db.resolver)
        resolved = p.canonical_id is not None
        if case.expected == "__AMBIGUOUS__":
            correct = resolved is False and p.resolution_method == "unresolved"
        elif case.expected == "__UNRESOLVABLE__":
            correct = resolved is False
        else:
            correct = p.canonical_id == case.expected
        rows.append({
            "alias": case.alias,
            "expected": case.expected,
            "resolved": resolved,
            "resolved_id": p.canonical_id,
            "resolution_method": p.resolution_method,
            "correct": correct,
            "confidence": p.confidence,
        })
    resolved_count = sum(r["resolved"] for r in rows)
    correct_count = sum(r["correct"] for r in rows)
    return {
        "experiment_id": "phase1e_alias_benchmark_v1",
        "data_status": "SYNTHETIC",
        "warning": "Alias fixtures are hand-curated; real corpora will surface unknown spellings.",
        "total": len(rows),
        "resolved": resolved_count,
        "resolution_rate": round(resolved_count / len(rows), 4),
        "correct": correct_count,
        "accuracy": round(correct_count / len(rows), 4),
        "cases": rows,
    }


def run_state_resolution_benchmark() -> dict:
    """Verify that identity persists across states while the state itself is preserved."""
    db = FoodMVP()
    cases = [
        ("ginger", None),
        ("2 tbsp chopped ginger", "chopped"),
        ("crushed ginger", "crushed"),
        ("fresh fenugreek", None),
    ]
    rows = []
    for raw, expected_state in cases:
        p = parse_ingredient(raw, db.resolver)
        rows.append({
            "raw": raw,
            "resolved_id": p.canonical_id,
            "state": p.state,
            "expected_state": expected_state,
            "state_correct": p.state == expected_state,
            "identity_correct": p.canonical_id is not None,
        })
    identity_ok = sum(r["identity_correct"] for r in rows)
    state_ok = sum(r["state_correct"] for r in rows)
    return {
        "experiment_id": "phase1e_state_resolution_benchmark_v1",
        "data_status": "SYNTHETIC",
        "total": len(rows),
        "identity_preserved_rate": round(identity_ok / len(rows), 4),
        "state_preserved_rate": round(state_ok / len(rows), 4),
        "cases": rows,
    }


def run_constraint_benchmark() -> dict:
    """Constraint pass rate: hard blocks rejected, unknown safety not blocked."""
    from .constraints import ConstraintEngine, ConstraintSet
    engine = ConstraintEngine()
    cases = [
        {"entity": "blocked_ing", "safety": "BLOCKED", "pass_expected": False},
        {"entity": "contra_ing", "safety": "CONTRAINDICATED", "pass_expected": False},
        {"entity": "assessed_safe", "safety": "SAFE", "pass_expected": True},
        {"entity": "unknown_safety", "safety": "UNASSESSED", "pass_expected": True},
    ]
    rows = []
    for c in cases:
        result = engine.check(c["entity"], processes={"fry"}, safety_status=c["safety"])
        rows.append({
            "entity": c["entity"],
            "safety": c["safety"],
            "allowed": result.allowed,
            "pass_expected": c["pass_expected"],
            "hard_failures": list(result.hard_failures),
            "reasons": list(result.reasons),
            "correct": result.allowed == c["pass_expected"],
        })
    correct = sum(r["correct"] for r in rows)
    return {
        "experiment_id": "phase1e_constraint_benchmark_v1",
        "data_status": "SYNTHETIC",
        "total": len(rows),
        "pass_rate": round(correct / len(rows), 4),
        "cases": rows,
    }


def run_process_validity_benchmark() -> dict:
    """Fail-closed process validation on the transformation vocabulary."""
    from .transformations import TransformationRecord
    catalog = default_process_catalog()
    valid_unknown_ok = instantiate("ginger", "ginger/raw", "fry",
                                   parameters={"temperature": None, "duration": None})
    # Construct invalid records directly: instantiate() already fails closed,
    # so validating records with an unknown process or an unsupported status
    # must also reject them.
    invalid = validate_transformation(TransformationRecord(
        "bad", "ginger", "ginger/raw", "not_a_real_process", "ginger/fried"))
    asserted_without_evidence = validate_transformation(TransformationRecord(
        "bad2", "ginger", "ginger/raw", "fry", "ginger/fried",
        status="EXPERIMENTALLY_VALIDATED"))
    rows = [
        {"case": "valid_unknown_ok", "valid": validate_transformation(valid_unknown_ok).valid,
         "expected": True},
        {"case": "unknown_process_fails", "valid": not invalid.valid, "expected": True},
        {"case": "asserted_needs_evidence", "valid":
         not asserted_without_evidence.valid, "expected": True},
    ]
    correct = sum(r["valid"] == r["expected"] for r in rows)
    return {
        "experiment_id": "phase1e_process_validity_benchmark_v1",
        "data_status": "SYNTHETIC",
        "vocabulary_size": len(catalog),
        "total": len(rows),
        "pass_rate": round(correct / len(rows), 4),
        "cases": rows,
    }


def run_heldout_pair_benchmark(seed: int = 17) -> dict:
    """Held-out pair prediction baseline: co-occurrence model trained on a
    leave-one-recipe-out split, then measured on the held-out recipe."""
    import random
    from collections import Counter, defaultdict
    db = FoodMVP()
    recipes = list(db.recipes)
    rng = random.Random(seed)
    rng.shuffle(recipes)
    split = int(len(recipes) * 0.7)
    train, test = recipes[:split], recipes[split:]

    def ids_of(r):
        return sorted({x for x in (db.resolver.resolve(i).id for i in r.ingredients) if x})

    train_pairs = Counter()
    for r in train:
        xs = ids_of(r)
        for i, a in enumerate(xs):
            for b in xs[i + 1:]:
                train_pairs[(a, b)] += 1

    predicted_pairs = {k: v for k, v in train_pairs.most_common(5)}
    hits, total = 0, 0
    for r in test:
        xs = ids_of(r)
        for i, a in enumerate(xs):
            for b in xs[i + 1:]:
                total += 1
                if (a, b) in predicted_pairs or (b, a) in predicted_pairs:
                    hits += 1

    # A co-occurrence baseline must always predict the pairs it has seen.
    recall = hits / total if total else 0.0
    return {
        "experiment_id": "phase1e_heldout_pair_baseline_v1",
        "data_status": "SYNTHETIC",
        "warning": "Co-occurrence is a baseline, not a causal or sensory claim.",
        "train_recipes": len(train),
        "test_recipes": len(test),
        "held_out_pairs": total,
        "recall@5_of_seen": round(recall, 4),
        "split_seed": seed,
    }


def run_all_tasks() -> dict:
    return {
        "alias": run_alias_benchmark(),
        "state_resolution": run_state_resolution_benchmark(),
        "constraints": run_constraint_benchmark(),
        "process_validity": run_process_validity_benchmark(),
        "held_out_pair_prediction": run_heldout_pair_benchmark(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_all_tasks(), indent=2))