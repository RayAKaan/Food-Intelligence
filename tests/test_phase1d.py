from food_intelligence.representation import Observation, Provenance
from food_intelligence.representation_builder import build_explicit_representation, semantic_representation, molecular_representation
from food_intelligence.transformations import instantiate, validate_transformation, transition_template

def prov(status="SYNTHETIC", evidence="HYPOTHESIS"):
    return Provenance("fixture", "fixture", "1", "x", "2026-09-11", "NOT_FOR_RESEARCH", "1", "1", .5, evidence, data_status=status)

def test_explicit_view_preserves_missing_mask():
    rep, mask = build_explicit_representation("x", "TASTE", [Observation("sweet", .5, provenance=prov())], provenance=prov())
    assert rep.vector[0] == .5
    assert rep.vector[1] is None
    assert mask[0] and not mask[1]

def test_semantic_and_molecular_views_do_not_fake_numeric_vectors():
    s = semantic_representation("x", names=["ginger"], roles=["aromatic"], provenance=prov())
    m = molecular_representation("x", ["c1", "c2"], {"c1": .7}, provenance=prov())
    assert s.source_features["tokens"] == ("aromatic", "ginger")
    assert m.source_features["weights"] == {"c1": .7}
    assert m.vector == ()

def test_transformation_validation_is_fail_closed():
    t = instantiate("ginger", "ginger/raw", "fry", parameters={"temperature": None, "duration": None})
    v = validate_transformation(t)
    assert v.valid and "output_state_unknown" in v.warnings
    bad = transition_template("ginger", "ginger/raw", "fry")
    assert bad["validation"]["valid"] is True
