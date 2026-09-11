"""SQLite local store for reproducible tests; schema mirrors database/schema.sql logically."""
import sqlite3, json
from pathlib import Path
from .core import Resolver
from .mvp import FoodMVP, parse_ingredient

DDL='''
CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY,name TEXT,license TEXT,commercial_status TEXT,retrieved_at TEXT);
CREATE TABLE IF NOT EXISTS ingredients(ingredient_id TEXT PRIMARY KEY,canonical_name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS ingredient_aliases(alias TEXT PRIMARY KEY,ingredient_id TEXT NOT NULL,raw_value TEXT,confidence REAL);
CREATE TABLE IF NOT EXISTS ingredient_states(state_id TEXT PRIMARY KEY,ingredient_id TEXT NOT NULL,state_name TEXT,preparation_method TEXT);
CREATE TABLE IF NOT EXISTS recipes(recipe_id TEXT PRIMARY KEY,title TEXT,cuisine TEXT);
CREATE TABLE IF NOT EXISTS recipe_ingredients(recipe_id TEXT,ordinal INTEGER,raw_value TEXT,ingredient_id TEXT,quantity REAL,unit TEXT,state TEXT,confidence REAL);
CREATE TABLE IF NOT EXISTS recipe_steps(recipe_id TEXT,step_id INTEGER,ordinal INTEGER,raw_text TEXT,process TEXT,temperature REAL,duration REAL,resulting_state TEXT);
CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,source_id TEXT,source_record_id TEXT,evidence_type TEXT,confidence REAL,retrieved_at TEXT);
'''

def create(path='data/food_mvp.sqlite'):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path); con.executescript(DDL); db=FoodMVP()
    for i in db.ingredients:
        con.execute('INSERT OR REPLACE INTO ingredients VALUES (?,?)',(i.id,i.canonical_name))
        for alias in i.aliases|{i.canonical_name}:
            con.execute('INSERT OR REPLACE INTO ingredient_aliases VALUES (?,?,?,?)',(Resolver.normalize(alias),i.id,alias,1.0))
    for r in db.recipes:
        con.execute('INSERT OR REPLACE INTO recipes VALUES (?,?,?)',(r.recipe_id,r.title,r.cuisine))
        for n,raw in enumerate(r.ingredients):
            p=parse_ingredient('1 unit '+raw,db.resolver)
            con.execute('INSERT INTO recipe_ingredients VALUES (?,?,?,?,?,?,?,?)',(r.recipe_id,n,raw,p.canonical_id,p.quantity,p.unit,p.state,p.confidence))
        for step in r.steps:
            con.execute('INSERT INTO recipe_steps VALUES (?,?,?,?,?,?,?,?)',(r.recipe_id,step['order'],step['order'],step['process'],step['process'],step['temperature'],step['duration'],step['resulting_state']))
    con.commit(); return con
