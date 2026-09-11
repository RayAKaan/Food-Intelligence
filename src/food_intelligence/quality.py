from .ingestion import NormalizedRecipe

def review_unresolved(recipes, resolver):
    out=[]
    for r in recipes:
        for raw in r.raw_ingredients:
            p=__import__('food_intelligence.mvp',fromlist=['parse_ingredient']).parse_ingredient(raw,resolver)
            if not p.canonical_id:
                out.append({'record_id':r.source_record_id,'field':'ingredient','raw_value':raw,'candidate_mappings':[],'confidence':0.0,'reason':'no deterministic alias','resolution_status':'PENDING'})
    return out

def contamination_report(records, commercial_source_ids):
    bad=[{'recipe_id':r.recipe_id,'source_id':r.source_id,'license':r.license} for r in records if r.source_id not in commercial_source_ids]
    return {'status':'FAIL' if bad else 'PASS','commercial_source_ids':sorted(commercial_source_ids),'contaminating_records':bad,'count':len(bad)}
