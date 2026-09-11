from food_intelligence import (
    FoodKnowledgeGraph, GraphNode, GraphEdge, MultiViewIndex,
    FoodIntelligencePipeline, FoodQuery, PipelineConfig,
)
from food_intelligence.benchmark import recall_at_k, leakage_audit


def test_pipeline_composes_graph_constraints_scoring_and_frontier():
    g = FoodKnowledgeGraph()
    for n in ["seed", "a", "b", "blocked"]:
        g.add_node(GraphNode(n, "Ingredient"))
    g.add_edge(GraphEdge("seed", "PAIRS_WITH", "a", .9))
    g.add_edge(GraphEdge("seed", "PAIRS_WITH", "b", .8))
    g.add_edge(GraphEdge("seed", "PAIRS_WITH", "blocked", .99))
    meta = {
        "a": {"processes": {"fry"}, "compatibility_components": {"taste_complementarity": .9}, "safety_status": "UNASSESSED"},
        "b": {"processes": {"fry"}, "compatibility_components": {"taste_complementarity": .8}, "safety_status": "UNASSESSED"},
        "blocked": {"processes": {"fry"}, "compatibility_components": {"taste_complementarity": 1.0}, "safety_status": "BLOCKED"},
    }
    p = FoodIntelligencePipeline(g, MultiViewIndex(), meta)
    result = p.run(FoodQuery(seed_entities=("seed",), required_processes=frozenset({"fry"}), top_k=3))
    ids = [r["entity_id"] for r in result.candidates]
    assert ids == ["a", "b"]
    assert all("constraint_result" in r for r in result.candidates)
    assert result.algorithm_version == "pipeline-v1.0"


def test_recall_is_true_set_recall_and_leakage_audit():
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, 3) == 1.0
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, 2) == .5
    assert leakage_audit(["r1", "r2"], ["r3"])['passed']
    assert not leakage_audit(["r1", "r2"], ["r2", "r3"])['passed']
