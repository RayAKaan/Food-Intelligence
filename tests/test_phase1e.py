from food_intelligence.graph import GraphNode, GraphEdge, FoodKnowledgeGraph
from food_intelligence.query import FoodQuery, QueryPlanner, FoodRetriever
from food_intelligence.retrieval import MultiViewIndex
from food_intelligence.fusion import MultiViewFusion
from food_intelligence.novelty import NoveltyEngine, NoveltySignals

def graph():
    g=FoodKnowledgeGraph()
    for n in [GraphNode("a","Ingredient"),GraphNode("b","Ingredient"),GraphNode("c","Compound")]: g.add_node(n)
    g.add_edge(GraphEdge("a","PAIRS_WITH","b",.8))
    g.add_edge(GraphEdge("a","HAS_COMPOUND","c",.9))
    return g

def test_graph_traversal_and_evidence_score():
    g=graph(); r=g.traverse("a",max_hops=1)
    assert {x["entity_id"] for x in r}=={"b","c"}
    assert g.path_score(r[0]["path"]) == .8

def test_query_planner_adds_only_relevant_views():
    p=QueryPlanner().plan(FoodQuery(seed_entities=("a",), target={"earthy":1}, required_processes=frozenset({"frying"})))
    assert "TASTE" in p.views and "PROCESS" in p.views and "PHYSICAL" not in p.views

def test_retriever_preserves_graph_paths():
    g=graph(); r=FoodRetriever(g, MultiViewIndex()).retrieve(FoodQuery(seed_entities=("a",),top_k=5))
    assert r[0]["entity_id"] in {"b","c"} and r[0]["path_count"] >= 1

def test_fusion_does_not_impute_missing():
    x=MultiViewFusion({"taste":2,"odor":1}).fuse({"taste":.8,"odor":None,"texture":None})
    assert x.score == .8 and x.known_views == ("taste",) and "odor" in x.missing_views

def test_novelty_unknown_without_corpus():
    x=NoveltyEngine().score(NoveltySignals())
    assert x["score"] is None and x["label"] == "UNKNOWN"
