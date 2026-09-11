from food_intelligence.representation import Representation, Provenance
from food_intelligence.representation_builder import molecular_representation, semantic_representation
from food_intelligence.retrieval import MultiViewIndex


def p():
    return Provenance("SYNTHETIC_TEST_DATA", "Synthetic fixture", "1", "x",
                      "2026-09-11", "NOT_FOR_RESEARCH", "1", "1", 1.0,
                      "HYPOTHESIS", data_status="SYNTHETIC")


def test_molecular_view_is_searchable_by_set_similarity():
    idx = MultiViewIndex()
    idx.add(molecular_representation("tomato", ["c1", "c2", "c3"], provenance=p()))
    idx.add(molecular_representation("cumin", ["c9", "c10"], provenance=p()))
    q = molecular_representation("q", ["c1", "c2"], provenance=p())
    hits = idx.search("MOLECULAR", q)
    assert hits and hits[0]["entity_id"] == "tomato"
    assert hits[0]["score"] == 2 / 3


def test_semantic_view_is_searchable_by_token_similarity():
    idx = MultiViewIndex()
    idx.add(semantic_representation("ginger", names=["ginger"], roles=["aromatic"], provenance=p()))
    idx.add(semantic_representation("turmeric", names=["turmeric"], roles=["earthy"], provenance=p()))
    q = semantic_representation("q", names=["ginger"], roles=["aromatic"], provenance=p())
    hits = idx.search("SEMANTIC", q)
    assert hits[0]["entity_id"] == "ginger"


def test_mixed_dense_sparse_does_not_impute_grounding():
    idx = MultiViewIndex()
    dense = Representation("a", "TASTE", "explicit", "1", (0.5, None), provenance=p())
    sparse = semantic_representation("b", names=["ginger"], provenance=p())
    idx.add(dense)
    idx.add(sparse)
    q = Representation("q", "TASTE", "explicit", "1", (0.5, None), provenance=p())
    hits = idx.search("TASTE", q)
    assert [h["entity_id"] for h in hits] == ["a"]