from food_intelligence.intelligence import FoodIntelligenceEngine, Candidate, CandidateRequest, profile_from_row
from food_intelligence.representation import Provenance
from food_intelligence.synthetic import load_fixture


def p(entity):
    return Provenance("SYNTHETIC_TEST_DATA", "Synthetic fixture", "1", entity,
                      "2026-09-11", "NOT_FOR_RESEARCH", "fixture-1", "fixture-1",
                      1.0, "HYPOTHESIS", data_status="SYNTHETIC")


def candidates():
    rows = load_fixture()["ingredients"]
    out = []
    for row in rows:
        pr = p(row["id"])
        prof = profile_from_row(row, pr)
        out.append(Candidate(row["id"], row.get("state"), prof, prof,
                             tuple(row.get("compounds", [])),
                             culinary_roles=frozenset(),
                             processes=frozenset({"fry", "roast"}),
                             evidence=(pr,)))
    return out


def test_unified_engine_is_deterministic_and_excludes_candidates():
    engine = FoodIntelligenceEngine(candidates())
    req = CandidateRequest(target={"sour": 1.0, "smoky": 1.0},
                           excluded_entities=frozenset({"tomato"}), max_results=4)
    a = engine.rank(req)
    b = engine.rank(req)
    assert a == b
    assert len(a) == 4
    assert all(x["entity_id"] != "tomato" for x in a)


def test_missing_novelty_does_not_become_zero():
    engine = FoodIntelligenceEngine(candidates())
    row = engine.rank(CandidateRequest(target={"sour": 1.0}, max_results=1))[0]
    assert row["novelty"]["label"] == "UNKNOWN"
    assert row["novelty"]["score"] is None


def test_hard_safety_block_is_never_ranked():
    cs = candidates()
    blocked = cs[0]
    cs[0] = Candidate(blocked.entity_id, blocked.state_id, blocked.taste, blocked.odor,
                      blocked.compounds, safety_status="BLOCKED", evidence=blocked.evidence)
    engine = FoodIntelligenceEngine(cs)
    rows = engine.rank(CandidateRequest(target={"sour": 1.0}, max_results=20))
    assert blocked.entity_id not in {r["entity_id"] for r in rows}
