from food_intelligence.core import Resolver, Ingredient, novelty


def test_resolver_exact_alias_is_priority():
    x = Ingredient('cumin_seed', 'cumin seed', {'jeera'})
    y = Ingredient('cumin_powder', 'cumin powder', {'ground cumin'})
    r = Resolver([x, y])
    assert r.resolve('JEERA').id == 'cumin_seed'


def test_resolver_preserves_ambiguity():
    x = Ingredient('cumin_seed', 'cumin seed', {'jeera'})
    y = Ingredient('cumin_powder', 'cumin powder', {'ground cumin'})
    r = Resolver([x, y])
    assert r.resolve('cumin') is None


def test_resolver_token_prefix_subset_is_unique():
    single = Ingredient('black_cardamom', 'black cardamom')
    fresh = Ingredient('coriander', 'coriander', {'dhania'})
    r = Resolver([single, fresh])
    assert r.resolve('black').id == 'black_cardamom'
    assert r.resolve('cardamom').id == 'black_cardamom'
    assert r.resolve('dhania').id == 'coriander'


def test_resolver_tie_returns_none_not_first():
    a = Ingredient('a', 'ginger root')
    b = Ingredient('b', 'ginger powder')
    r = Resolver([a, b])
    assert r.resolve('ginger') is None


def test_resolver_unknown_stays_unknown():
    r = Resolver([Ingredient('tomato', 'tomato', {'tamatar'})])
    assert r.resolve('shimla mirch') is None


def test_novelty_labels_are_bounded_and_corpus_relative():
    assert novelty(0, 100)['label'] == 'rare_in_indexed_corpus'
    assert novelty(0, 100)['score'] == 1.0
    assert novelty(100, 100)['score'] == 0.0
    assert 0 <= novelty(50, 1000)['score'] <= 1