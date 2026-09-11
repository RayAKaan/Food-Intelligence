"""Representation-agnostic retrieval and late fusion."""
from __future__ import annotations
from typing import Any
from .representation import Representation, masked_cosine


def _set_similarity(query: Representation, candidate: Representation) -> float | None:
    """Jaccard over token/compound features for non-numeric representations.

    Semantic (``tokens``) and molecular (``compounds``) views are represented
    as sets, not dense vectors; cosine over an empty vector is undefined.
    Missing features on either side stay missing (None) rather than ground to
    zero, preserving the project's explicit-missingness rule.
    """
    def feats(rep: Representation) -> set[str]:
        raw = rep.source_features
        if "compounds" in raw:
            return set(raw["compounds"])
        if "tokens" in raw:
            return set(raw["tokens"])
        return set()

    a, b = feats(query), feats(candidate)
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def _similarity(query: Representation, candidate: Representation) -> float | None:
    if query.vector and candidate.vector:
        return masked_cosine(query, candidate)
    if query.vector or candidate.vector:
        # One side dense, the other sparse: no shared numerical basis.
        return None
    return _set_similarity(query, candidate)


class MultiViewIndex:
    def __init__(self): self._data = {}
    def add(self, rep: Representation): self._data.setdefault(rep.representation_type, {})[rep.entity_id] = rep
    def search(self, representation_type, query: Representation, k=10):
        rows=[]
        for entity, rep in self._data.get(representation_type, {}).items():
            score=_similarity(query, rep)
            if score is not None: rows.append({"entity_id":entity,"representation_type":representation_type,"score":score,"model":rep.model,"version":rep.version,"provenance":rep.provenance})
        return sorted(rows,key=lambda x:(-x["score"],x["entity_id"]))[:k]
    def late_fuse(self, query_by_view: dict[str, Representation], weights=None, k=10):
        weights = weights or {v:1.0 for v in query_by_view}
        scores={}; evidence={}
        for view, query in query_by_view.items():
            for row in self.search(view,query,k=100):
                scores[row["entity_id"]]=scores.get(row["entity_id"],0)+weights.get(view,1.0)*row["score"]
                evidence.setdefault(row["entity_id"],[]).append(row)
        return [{"entity_id":e,"score":s,"views":evidence[e]} for e,s in sorted(scores.items(),key=lambda x:(-x[1],x[0]))[:k]]

def fusion_strategies():
    return ["semantic_only","structured_only","semantic_molecular","semantic_sensory","semantic_odor","semantic_molecular_sensory_odor","late_fusion","weighted_rank_fusion"]
