from food_intelligence.constraints import ConstraintEngine, ConstraintSet
from food_intelligence.compatibility_v2 import CompatibilityV2
from food_intelligence.reasoning import FoodReasoner
from food_intelligence.pareto import pareto_frontier

def test_hard_constraints_block_and_unknown_safety_is_not_blocked():
    e=ConstraintEngine()
    c=ConstraintSet(excluded_entities=frozenset({"x"}), required_processes=frozenset({"fry"}))
    assert not e.check("x", processes={"fry"}, constraints=c).allowed
    assert e.check("y", processes={"fry"}, constraints=c).allowed
    assert "SAFETY_UNASSESSED" in e.check("y", processes={"fry"}, constraints=c).reasons

def test_compatibility_v2_reports_missing_components():
    r=CompatibilityV2().score({"taste_complementarity":.8,"odor_complementarity":None})
    assert r["score"] is not None
    assert "odor_complementarity" in r["missing_components"]

def test_reasoner_blocks_safety_and_keeps_unknown_novelty():
    rr=FoodReasoner().evaluate({"entity_id":"x","components":{"taste_complementarity":.8},"safety_status":"BLOCKED"})
    assert rr is None
    rr=FoodReasoner().evaluate({"entity_id":"y","components":{"taste_complementarity":.8},"safety_status":"UNASSESSED"})
    assert rr["score"] is not None and rr["novelty"]["label"] == "UNKNOWN"

def test_pareto_frontier_prefers_non_dominated_rows():
    rows=[{"entity_id":"a","compatibility":.9,"novelty":.2},{"entity_id":"b","compatibility":.8,"novelty":.8},{"entity_id":"c","compatibility":.7,"novelty":.1}]
    assert {x["entity_id"] for x in pareto_frontier(rows)} == {"a","b"}
