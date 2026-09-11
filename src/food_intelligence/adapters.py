"""Replaceable, non-downloading source adapter contract.

Adapters are intentionally stubs until source terms and versions are approved.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .representation import Provenance

@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    source_name: str
    source_version: str | None
    url: str
    license_status: str
    research_status: str
    commercial_status: str
    retrieval_date: str | None = None

class SourceAdapter:
    spec: SourceSpec
    def discover(self) -> dict[str, Any]: return {"source_id": self.spec.source_id, "status": "METADATA_ONLY"}
    def validate(self, payload=None) -> bool: return True
    def retrieve(self, destination=None):
        raise PermissionError(f"Acquisition for {self.spec.source_id} requires an approved source-specific implementation and authorization")
    def parse(self, payload): raise NotImplementedError
    def normalize(self, records): return records
    def map(self, records): raise NotImplementedError
    def emit(self, records): return records

class MetadataOnlyAdapter(SourceAdapter):
    def __init__(self, spec): self.spec = spec
    def parse(self, payload): return payload
    def map(self, records): return records

SOURCE_SPECS = {
    "FoodOn": SourceSpec("foodon", "FoodOn", None, "https://foodon.org/", "CC BY 4.0", "allowed_pending_version", "allowed_pending_version"),
    "FDC": SourceSpec("fdc", "USDA FoodData Central", None, "https://fdc.nal.usda.gov/", "USDA release terms", "allowed_pending_release", "allowed_pending_release"),
    "FooDB": SourceSpec("foodb", "FooDB", None, "https://foodb.ca/", "CC BY-NC 4.0", "research_only", "blocked"),
    "FlavorDB2": SourceSpec("flavordb2", "FlavorDB2", None, "https://cosylab.iiitd.edu.in/flavordb2/", "CC BY-NC-SA 3.0", "research_only", "blocked"),
    "Pyrfume": SourceSpec("pyrfume", "Pyrfume", None, "https://pyrfume.org/", "source-dependent/noncommercial", "research_only", "blocked"),
    "Phenol-Explorer": SourceSpec("phenol-explorer", "Phenol-Explorer", None, "http://phenol-explorer.eu/downloads", "commercial redistribution requires permission", "research_only", "blocked"),
    "FEMA": SourceSpec("fema-flavor-library", "FEMA Flavor Ingredient Library", None, "https://www.femaflavor.org/", "terms/source-dependent", "pending_review", "pending_review"),
}

def adapters():
    return {k: MetadataOnlyAdapter(v) for k, v in SOURCE_SPECS.items()}
