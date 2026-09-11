"""Deterministic, provenance-aware MVP primitives. No LLM or scientific values are invented here."""
from dataclasses import dataclass, field
from math import log1p
from typing import Iterable

@dataclass(frozen=True)
class Evidence:
    source: str
    record_id: str | None
    kind: str = "SOURCE_DERIVED"
    confidence: float = 0.5

@dataclass
class Ingredient:
    id: str
    canonical_name: str
    aliases: set[str] = field(default_factory=set)
    taste: dict[str, float] = field(default_factory=dict)
    odor: dict[str, float] = field(default_factory=dict)
    processes: set[str] = field(default_factory=set)
    evidence: list[Evidence] = field(default_factory=list)

class Resolver:
    def __init__(self, ingredients: Iterable[Ingredient]):
        self.by_alias = {}
        for item in ingredients:
            for name in {item.canonical_name, *item.aliases}:
                self.by_alias[self.normalize(name)] = item

    @staticmethod
    def normalize(text: str) -> str:
        return " ".join(text.casefold().replace("-", " ").split())

    @staticmethod
    def _tokens(text: str) -> frozenset[str]:
        import re
        return frozenset(re.findall(r"[a-z0-9]+", Resolver.normalize(text)))

    def resolve(self, text: str) -> Ingredient | None:
        """Resolve with exact alias lookup, then word-token prefix matching.

        Token matching never fires when the exact lookup already succeeded, and
        it requires every token of the query to be present in the canonical name
        or at least one alias so that partial requests stay conservative.
        """
        exact = self.by_alias.get(self.normalize(text))
        if exact is not None:
            return exact
        q_tokens = self._tokens(text)
        if not q_tokens:
            return None
        best: Ingredient | None = None
        best_key = None
        best_score = 0.0
        for key, item in self.by_alias.items():
            key_tokens = self._tokens(key)
            if key_tokens and q_tokens <= key_tokens:
                score = len(q_tokens) / len(key_tokens)
                if score > best_score:
                    best, best_key, best_score = item, key, score
                elif score == best_score and item.id != best.id and best_key != key:
                    # Ambiguous token match (e.g. "cumin" vs "cumin seed"/"cumin
                    # powder"): multiple distinct entities tie, so do NOT silently
                    # pick one. Preserve uncertainty for the caller.
                    return None
        return best

def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    if not keys: return 0.0
    dot = sum(a.get(k, 0.0)*b.get(k, 0.0) for k in keys)
    na = sum(v*v for v in a.values()) ** .5
    nb = sum(v*v for v in b.values()) ** .5
    return dot/(na*nb) if na and nb else 0.0

def complementarity(a: Ingredient, b: Ingredient, target: dict[str, float]) -> float:
    """Target coverage, not a claim of pleasantness."""
    def coverage(x):
        return sum(min(max(v, 0), max(target.get(k, 0), 0)) for k,v in x.items())
    union = sum(max(target.get(k, 0), 0) for k in target) or 1
    return min(1.0, (coverage(a.taste)+coverage(b.taste))/(2*union))

def compatibility(a: Ingredient, b: Ingredient, target: dict[str,float], known_count: int = 0) -> dict:
    sensory = complementarity(a,b,target)
    redundancy = cosine(a.taste, b.taste)
    process = 1.0 if (a.processes & b.processes) else 0.0
    # Sparse baseline: co-occurrence is only a weak prior and never evidence of causality.
    cooccur = min(1.0, log1p(known_count)/10) if known_count else 0.0
    score = .45*sensory + .20*process + .15*cooccur - .20*redundancy
    return {"score": round(score, 4), "sensory_target_coverage": round(sensory,4),
            "redundancy": round(redundancy,4), "process_compatibility": process,
            "evidence_label": "MODEL_PREDICTION"}

def novelty(pair_count: int, corpus_size: int, recipe_similarity: float = 0.0) -> dict:
    if corpus_size <= 0: return {"score": 0.0, "label": "UNKNOWN"}
    freq = pair_count / corpus_size
    score = max(0.0, min(1.0, 1.0 - freq*10 - recipe_similarity*.5))
    label = "common" if freq >= .01 else "underrepresented" if freq >= .001 else "rare_in_indexed_corpus"
    return {"score": round(score,4), "label": label, "evidence_label": "SOURCE_DERIVED"}
