from food_intelligence.ingestion import *
from food_intelligence.mvp import FoodMVP

def test_mapping_preserves_raw_and_unknowns():
    r=map_row({'RecipeName':'Test','Ingredients':'2 tbsp chopped ginger, handful sesame','Instructions':'Fry until golden','Cuisine':'Karnataka'},'src','CC BY 4.0','2026-09-11')
    assert r.raw_ingredients[0]=='2 tbsp chopped ginger'
    q=quality_report([r]); assert q['quantity_completeness']==1.0 and q['region_completeness']==0.0

def test_dedup_groups_without_deleting_source_rows():
    a=map_row({'id':'a','title':'Dal','ingredients':'lentil,onion','instructions':'boil'},'s','x','d')
    b=map_row({'id':'b','title':'Dal','ingredients':'lentil,onion','instructions':'simmer'},'s2','x','d')
    rows,groups=deduplicate([a,b]); assert len(rows)==2 and len(groups)==1 and rows[1].canonical_recipe_group_id==rows[0].canonical_recipe_group_id

def test_group_split_no_group_leakage():
    a=map_row({'id':'a','title':'Dal','ingredients':'lentil','instructions':'boil'},'s','x','d'); b=map_row({'id':'b','title':'Dal','ingredients':'lentil','instructions':'boil'},'s2','x','d')
    rows,_=deduplicate([a,b]); splits=split_by_group(rows); assert len({x['split'] for x in splits})==1
