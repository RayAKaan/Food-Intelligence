from food_intelligence.core import *
def test_state_safe_alias_resolution():
    x=Ingredient('cumin_seed','cumin seed',{'jeera'})
    y=Ingredient('cumin_powder','cumin powder',{'ground cumin'})
    r=Resolver([x,y])
    assert r.resolve('JEERA').id=='cumin_seed'
    assert r.resolve('cumin powder').id=='cumin_powder'
    assert r.resolve('cumin') is None

def test_novelty_is_corpus_relative():
    assert novelty(120,6000)['label']=='common'
    assert novelty(1,6000)['label']=='rare_in_indexed_corpus'

def test_compatibility_is_explainable():
    a=Ingredient('a','a',taste={'sour':1},processes={'reduce'})
    b=Ingredient('b','b',taste={'smoky':1},processes={'reduce'})
    out=compatibility(a,b,{'sour':1,'smoky':1})
    assert 0 <= out['score'] <= 1
    assert out['evidence_label']=='MODEL_PREDICTION'
