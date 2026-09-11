from food_intelligence.mvp import FoodMVP, parse_ingredient

def test_quantity_and_state_are_preserved():
    db=FoodMVP(); p=parse_ingredient('2 tbsp finely chopped fresh ginger',db.resolver)
    assert p.quantity==2 and p.unit=='tbsp' and p.state=='chopped' and p.freshness=='fresh'
    assert p.canonical_id=='ginger' and p.raw_value.startswith('2 tbsp')

def test_fraction_and_range_quantities_parse():
    db=FoodMVP()
    p=parse_ingredient('1/2 cup crushed garlic',db.resolver)
    assert p.quantity==0.5 and p.unit=='cup' and p.state=='crushed' and p.canonical_id=='garlic'
    p=parse_ingredient('1 1/2 tsp roasted cumin seed',db.resolver)
    assert p.quantity==1.5 and p.canonical_id=='cumin'
    p=parse_ingredient('1-2 tbsp turmeric',db.resolver)
    assert p.quantity==1.5 and p.canonical_id=='turmeric'
    p=parse_ingredient('to taste black pepper',db.resolver)
    assert p.quantity is None and p.canonical_id=='black pepper'

def test_modifier_noise_resolves_to_identity():
    db=FoodMVP()
    p=parse_ingredient('1 whole dried chili',db.resolver)
    assert p.canonical_id=='chili'
    p=parse_ingredient('2 red onions',db.resolver)
    assert p.canonical_id=='onion'

def test_distinct_state_entities_are_not_collapsed():
    db=FoodMVP()
    powder=parse_ingredient('2 tsp mango powder',db.resolver)
    raw=parse_ingredient('1 raw mango',db.resolver)
    assert powder.canonical_id=='mango powder'
    assert raw.canonical_id=='mango'

def test_pipeline_has_uncertainty_and_validation():
    out=FoodMVP().generate(['tomato','coconut','black cardamom','sesame','ginger','tamarind'],{'smoky':.8,'creamy':.8,'savory':.8,'citrus':.7})
    assert len(out['resolved_entities'])==6
    assert out['validation']['status']=='PASS'
    assert out['validation']['claim_status']['novelty']=='INFERRED'
    assert all(c['compatibility']['evidence_label']=='MODEL_PREDICTION' for c in out['candidates'])

def test_unknown_is_not_zero():
    step=FoodMVP().recipes[0].steps[0]
    assert step['temperature'] is None and step['duration'] is None
