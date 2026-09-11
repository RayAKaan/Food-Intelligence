"""Deterministic, source-preserving recipe ingestion primitives.

No downloader is included: acquisition is a legal/source decision and raw
snapshots must be supplied by an approved manifest.
"""
from __future__ import annotations
import csv, hashlib, json, re
from dataclasses import dataclass, asdict
from pathlib import Path
from .mvp import parse_ingredient

@dataclass
class NormalizedRecipe:
    recipe_id: str
    source_id: str
    source_record_id: str
    title: str
    description: str = ''
    cuisine: str|None = None
    region: str|None = None
    language: str|None = None
    servings: str|None = None
    raw_ingredients: list[str] = None
    raw_steps: list[str] = None
    prep_time: str|None = None
    cook_time: str|None = None
    total_time: str|None = None
    source_url: str|None = None
    license: str|None = None
    retrieved_at: str|None = None
    source_payload: dict = None
    canonical_recipe_group_id: str|None = None
    duplicate_status: str = 'UNREVIEWED'
    def __post_init__(self):
        self.raw_ingredients=self.raw_ingredients or []
        self.raw_steps=self.raw_steps or []
        self.source_payload=self.source_payload or {}

def norm_text(s):
    return re.sub(r'\s+',' ',str(s or '').casefold().strip())
def tokens(s):
    return set(re.findall(r'[a-z0-9]+',norm_text(s)))
def recipe_fingerprint(r: NormalizedRecipe):
    ingredients='|'.join(sorted(norm_text(x) for x in r.raw_ingredients))
    return hashlib.sha256((norm_text(r.title)+'||'+ingredients).encode()).hexdigest()[:20]
def ingredient_fingerprint(r): return frozenset(norm_text(x) for x in r.raw_ingredients)
def jaccard(a,b):
    if not a and not b: return 0.0
    return len(a&b)/len(a|b) if a|b else 0.0

def map_row(row, source_id, license_name, retrieved_at):
    def first(*keys):
        for k in keys:
            if row.get(k) not in (None,''): return row[k]
        return None
    def split_field(value):
        if not value: return []
        return [x.strip() for x in re.split(r'\s*[,;|]\s*',value) if x.strip()]
    rid=str(first('id','recipe_id','RecipeName','title') or '').strip()
    return NormalizedRecipe(rid,source_id,rid,first('title','RecipeName','name') or rid, first('description','Description') or '',first('cuisine','Cuisine'),first('region','Region','state'),first('language','Language'),first('servings','Servings'),split_field(first('ingredients','Ingredients','TranslatedIngredients')),split_field(first('steps','instructions','Instructions','TranslatedInstructions')),first('prep_time','Prep'),first('cook_time','Cook'),first('total_time','Total'),first('source_url','Source','url'),license_name,retrieved_at,row)

def load_csv(path, source_id, license_name, retrieved_at):
    with open(path,encoding='utf-8-sig',newline='') as f:
        return [map_row(r,source_id,license_name,retrieved_at) for r in csv.DictReader(f)]

def deduplicate(recipes, similarity_threshold=.85):
    groups=[]; out=[]
    for r in recipes:
        exact=None
        for group in groups:
            head=group[0]
            if recipe_fingerprint(r)==recipe_fingerprint(head): exact=group; break
            if norm_text(r.title)==norm_text(head.title) and jaccard(ingredient_fingerprint(r),ingredient_fingerprint(head))>=similarity_threshold: exact=group; break
        if exact is None: groups.append([r]); r.duplicate_status='LIKELY_INDEPENDENT'; r.canonical_recipe_group_id=recipe_fingerprint(r)
        else:
            exact.append(r); r.canonical_recipe_group_id=exact[0].canonical_recipe_group_id
            r.duplicate_status='EXACT_DUPLICATE' if recipe_fingerprint(r)==recipe_fingerprint(exact[0]) else 'NEAR_DUPLICATE'
        out.append(r)
    return out, groups

def quality_report(recipes):
    n=len(recipes) or 1
    def rate(fn): return round(sum(bool(fn(r)) for r in recipes)/n,4)
    return {'raw_recipe_count':len(recipes),'title_completeness':rate(lambda r:r.title),'ingredient_completeness':rate(lambda r:r.raw_ingredients),'instruction_completeness':rate(lambda r:r.raw_steps),'quantity_completeness':rate(lambda r:any(re.search(r'\d',x) for x in r.raw_ingredients)),'cuisine_completeness':rate(lambda r:r.cuisine),'region_completeness':rate(lambda r:r.region),'language_completeness':rate(lambda r:r.language),'source_url_completeness':rate(lambda r:r.source_url),'provenance_completeness':rate(lambda r:r.source_id and r.source_record_id)}

def split_by_group(recipes, seed=17):
    # Deterministic hash split: groups never cross splits.
    result={}
    for r in recipes:
        gid=r.canonical_recipe_group_id or recipe_fingerprint(r)
        h=int(hashlib.sha256(f'{seed}:{gid}'.encode()).hexdigest()[:8],16)/0xffffffff
        result[gid]='test' if h<.2 else 'validation' if h<.3 else 'train'
    return [{'recipe_id':r.recipe_id,'canonical_recipe_group_id':r.canonical_recipe_group_id,'split':result[r.canonical_recipe_group_id]} for r in recipes]

def source_checksum(path):
    h=hashlib.sha256();
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
