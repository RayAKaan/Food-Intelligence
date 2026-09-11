"""Synthetic integration demonstration; never a scientific benchmark."""
from __future__ import annotations
import json
from pathlib import Path
from .representation import Provenance, Observation, SensoryProfile, molecular_similarity, sensory_complementarity, compatibility_components, explain_compatibility

FIXTURE_ID = "SYNTHETIC_TEST_DATA"

def load_fixture(path=None):
    path = path or Path(__file__).parents[2] / "data/fixtures/synthetic_representation_fixture.json"
    return json.loads(Path(path).read_text())

def _prov(source_record_id):
    return Provenance(FIXTURE_ID, "Synthetic representation fixture", "1", source_record_id, "2026-09-11", "NOT_FOR_RESEARCH", "fixture-1", "fixture-1", 1.0, "HYPOTHESIS", data_status="SYNTHETIC")

def demonstrate(target_names=None):
    data = load_fixture(); rows = {x["id"]: x for x in data["ingredients"]}
    target_names = target_names or ["tomato", "coconut", "black_cardamom", "sesame", "ginger", "tamarind"]
    target = {"smoky": 1.0, "creamy": 1.0, "umami": 1.0, "citrus": 1.0}
    target_compounds = set(c for n in target_names for c in rows[n]["compounds"])
    results = []
    for name, row in rows.items():
        if name in target_names: continue
        taste = tuple(Observation(k, v, "synthetic_0_1", "constructed", "fixture", True, _prov(name)) for k,v in row["taste"].items())
        odor = tuple(Observation(k, v, "synthetic_0_1", "constructed", "fixture", True, _prov(name)) for k,v in row["odor"].items())
        profile = SensoryProfile(name, row["state"], taste=taste, odor=odor)
        odor_support = sum(min(row["odor"].get(k, 0), v) for k,v in target.items()) / sum(target.values())
        comp = compatibility_components(chemical_similarity=molecular_similarity(target_compounds, row["compounds"]), sensory_complementarity_value=sensory_complementarity(profile, profile, target), odor_complementarity=odor_support, culinary_cooccurrence=None, process_compatibility=None, texture_complementarity=None, safety=None)
        results.append({"ingredient": name, "state": row["state"], "molecular_representation": row["compounds"], "taste_representation": row["taste"], "odor_representation": row["odor"], "texture_representation": row["texture"], "process_representation": {"status":"UNKNOWN"}, "compatibility": explain_compatibility(comp, [_prov(name)]), "novelty": {"label":"UNKNOWN","reason":"no real indexed recipe corpus"}, "provenance": "SYNTHETIC_TEST_DATA", "uncertainty": "HYPOTHESIS"})
    return {"notice":"THIS IS A SYNTHETIC SOFTWARE-INTEGRATION DEMONSTRATION.", "data_status":"SYNTHETIC", "query":{"ingredients":target_names,"target":target}, "results":sorted(results, key=lambda x: (-(x["compatibility"]["components"]["odor_complementarity"] or 0), x["ingredient"]))}
