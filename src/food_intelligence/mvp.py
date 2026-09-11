"""Small, deterministic Phase 1 executable MVP.

The seed corpus is a software fixture, not a scientific dataset. It exists to
exercise the pipeline until a licensed Indian recipe snapshot is selected.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re, json
from collections import Counter, defaultdict
from .core import Ingredient, Evidence, Resolver, novelty

PROCESSES = ('boil','simmer','steam','poach','blanch','roast','toast','bake','grill','fry','deep_fry','shallow_fry','saute','temper','reduce','caramelize','brown','ferment','pickle','grind','blend','emulsify','whip','knead','rest','marinate','cure','dehydrate','smoke')

@dataclass
class ParsedIngredient:
    raw_value: str
    normalized_value: str|None
    canonical_id: str|None
    state: str|None
    freshness: str|None
    quantity: float|None
    unit: str|None
    resolution_method: str
    confidence: float

_STATE_WORDS = ('raw','chopped','sliced','diced','crushed','ground','roasted','fried','pureed','dehydrated','fermented')
_MODIFIER_WORDS = ('whole','dried','fresh','red','green','yellow','white','black','seed','seeds','powder','grounded','toasted','brown','young','ripe','greenleaf')

def _clean_name(text: str) -> str:
    text = re.sub(r"\b(to taste|as needed|optional|fresh|finely|roughly|chopped|sliced|diced|crushed|ground|roasted|fried)\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ,.-")
    return text.casefold()

def _strip_modifiers(name: str) -> str:
    """Best-effort removal of colour/state/preparation noise (identity-only fallback).

    Applied only as a fallback chain in parse_ingredient so that ``dried chili``
    resolves to ``chili`` without collapsing genuine states such as ``chili
    powder`` when those are distinct registered entities. Distinct entities are
    registered under their own canonical names, so an exact or subset match on
    the full name always wins first.
    """
    return re.sub(r"\b(" + "|".join(_MODIFIER_WORDS) + r")\b", " ", name)

_FRACTION = r"(?:(\d+)\s+)?(\d+)/(\d+)"
_QUANTITY = rf"(?:(\d+(?:\.\d+)?)|{_FRACTION})"

def _parse_quantity(raw: str) -> tuple[float | None, str | None, str]:
    """Extract leading quantity, unit, and the remaining ingredient text.

    Handles ``2 tbsp``, ``1/2 cup``, ``1 1/2 tsp``, ``1.5 tsp``, ``1-2 tbsp``
    and ``to taste``. Returns (quantity, unit, remaining_text). Missing values
    stay None.
    """
    mixed = r"(?P<whole>\d+)\s+(?P<num>\d+)/(?P<den>\d+)"
    simple = r"(?P<num2>\d+)/(?P<den2>\d+)"
    decimal = r"(?P<dec>[\d.]+)"
    range_ = r"(?P<lo>[\d.]+)-(?P<hi>[\d.]+)"
    qty_pattern = rf"(?:(?:{mixed}|{simple}|{range_}|{decimal})+?)"
    m = re.match(rf"^\s*(?P<q>{qty_pattern})\s*(?P<unit>[a-zA-Z]+)?\s+(?P<rest>.*)", raw)
    if m:
        qty_text = m.group("q").strip()
        unit = m.group("unit")
        rest = m.group("rest")
        qty = _quantity_value(qty_text)
        if unit and unit.casefold() == "whole":
            unit = None
        return qty, unit.casefold() if unit else None, rest
    m = re.match(r"^\s*to taste\s+(.*)", raw, flags=re.I)
    if m:
        return None, None, m.group(1)
    return None, None, raw

_VULGAR = {"\u00bc": .25, "\u00bd": .5, "\u00be": .75}

def _quantity_value(text: str) -> float | None:
    """Convert a quantity token like '2', '1/2', '1 1/2', '1.5', '1-2', or '\u00bd' to float."""
    text = text.strip()
    for ch, val in _VULGAR.items():
        if ch in text:
            if len(text.strip()) == 1:
                return val
            # e.g. "1 1/2" using a vulgar fraction after a whole number
            head = text.replace(ch, "").strip().replace(" ", "")
            if head:
                try:
                    return float(head) + val
                except ValueError:
                    return None
    spaced = text.split()
    if len(spaced) == 2:
        whole, frac = spaced[0], spaced[1]
        if "/" in frac:
            try:
                n, d = frac.split("/")
                return float(whole) + float(n) / float(d)
            except (ValueError, ZeroDivisionError):
                pass
    if "/" in text:
        parts = text.split("/")
        if len(parts) == 2:
            try:
                return float(parts[0]) / float(parts[1])
            except (ValueError, ZeroDivisionError):
                return None
    parts = text.split("-")
    if len(parts) == 2:
        try:
            lo, hi = float(parts[0]), float(parts[1])
            return (lo + hi) / 2
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None

def parse_ingredient(raw: str, resolver: Resolver) -> ParsedIngredient:
    quantity, unit, text = _parse_quantity(raw)
    lower = text.casefold()
    states = [s for s in _STATE_WORDS if re.search(rf'\b{s}\b', lower)]
    state = states[-1] if states else None
    freshness = 'fresh' if re.search(r'\bfresh\b', lower) else None
    name = _clean_name(text)
    stripped_clean = re.sub(r'\s+', ' ', _strip_modifiers(name)).strip()
    item = (resolver.resolve(name)
            or resolver.resolve(re.sub(r'\b(seed|seeds|powder)\b','',name).strip())
            or (resolver.resolve(stripped_clean) if stripped_clean and stripped_clean != name else None))
    return ParsedIngredient(raw, name, item.id if item else None, state, freshness, quantity, unit, 'exact_alias' if item else 'unresolved', 1.0 if item else 0.0)

@dataclass
class Recipe:
    recipe_id: str
    title: str
    ingredients: list[str]
    steps: list[dict]
    cuisine: str = 'Indian'

class FoodMVP:
    def __init__(self):
        self.ingredients = self._seed_ingredients()
        self.resolver = Resolver(self.ingredients)
        self.recipes = self._seed_recipes()
        self.pair_counts = Counter()
        for r in self.recipes:
            ids = sorted({self.resolver.resolve(x).id for x in r.ingredients if self.resolver.resolve(x)})
            for i,a in enumerate(ids):
                for b in ids[i+1:]: self.pair_counts[(a,b)] += 1

    @staticmethod
    def _seed_ingredients():
        """Expanded Indian-cuisine fixture.

        Sensory profiles are fixture hypotheses (EVIDENCE: HYPOTHESIS, confidence 0.1).
        No data here should be treated as ground-truth food science.
        """
        rows = [
          ('tomato', ['tomatoes'], {'sour':.5,'umami':.4,'sweet':.2}, {'green':.5,'fruity':.4}, ['reduce','roast']),
          ('coconut', ['coconut','coconut milk'], {'sweet':.4,'umami':.1}, {'nutty':.7,'creamy':.6}, ['blend','reduce']),
          ('black cardamom', ['black cardamom','badi elaichi','kali elaichi'], {'bitter':.2}, {'smoky':.8,'camphoraceous':.5}, ['toast','smoke']),
          ('sesame', ['sesame','til'], {'umami':.3,'bitter':.2}, {'nutty':.8,'roasted':.5}, ['toast','grind']),
          ('ginger', ['ginger','adrak'], {'pungent':.7}, {'citrus':.3,'spicy':.7}, ['fry','grind']),
          ('tamarind', ['tamarind','imli'], {'sour':.8,'sweet':.2}, {'fruity':.4}, ['reduce','blend']),
          ('onion', ['onion','onions','pyaz'], {'sweet':.4,'umami':.2}, {'sulfurous':.4,'caramelized':.4}, ['fry','brown']),
          ('garlic', ['garlic','lahsun'], {'pungent':.6}, {'sulfurous':.7,'roasted':.3}, ['fry','roast']),
          ('cumin', ['cumin','jeera'], {'bitter':.2}, {'earthy':.7,'roasted':.4}, ['toast','temper']),
          ('chili', ['chili','chilli','red chili','lal mirch'], {'pungent':.8}, {'spicy':.8,'fruity':.2}, ['fry','toast']),
          ('coriander', ['coriander','dhania'], {'sweet':.2}, {'citrus':.4,'herbal':.7}, ['grind','toast']),
          ('lentil', ['lentil','dal'], {'umami':.4}, {'earthy':.3}, ['boil','simmer']),
          ('green cardamom', ['green cardamom','elaichi','choti elaichi'], {'sweet':.3,'bitter':.1}, {'floral':.6,'menthol':.4}, ['toast','grind']),
          ('turmeric', ['turmeric','haldi'], {'bitter':.3}, {'earthy':.7,'woody':.3}, ['toast','temper']),
          ('mustard seed', ['mustard seed','rai','sarson','sarso'], {'pungent':.5}, {'spicy':.4,'nutty':.3}, ['temper','fry']),
          ('asafoetida', ['asafoetida','hing'], {'pungent':.6}, {'sulfurous':.5,'umami':.2}, ['temper']),
          ('yogurt', ['yogurt','dahi','curd'], {'sour':.6,'umami':.2}, {'fermented':.5,'creamy':.4}, ['blend']),
          ('mango', ['mango','raw mango'], {'sour':.7,'sweet':.4}, {'fruity':.6}, ['dry','grind']),
          ('fenugreek', ['fenugreek','fenugreek leaf','methi','kasoori methi'], {'bitter':.4}, {'herbal':.5,'maple':.3}, ['temper','grind']),
          ('curry leaf', ['curry leaf','kadi patta'], {'bitter':.1}, {'herbal':.7,'citrus':.3}, ['temper']),
          ('bay leaf', ['bay leaf','tej patta','bay'], {'bitter':.1}, {'herbal':.5,'woody':.3}, ['simmer','toast']),
          ('mustard oil', ['mustard oil','sarson ka tel'], {'pungent':.5}, {'spicy':.4}, ['temper','fry']),
          ('ghee', ['ghee','clarified butter'], {'umami':.2}, {'creamy':.5,'nutty':.3}, ['fry','temper']),
          ('coconut oil', ['coconut oil','nariyal tel'], {}, {'creamy':.4}, ['fry','temper']),
          ('jaggery', ['jaggery','gur'], {'sweet':.7}, {'caramelized':.6,'smoky':.2}, ['reduce']),
          ('black pepper', ['black pepper','kali mirch'], {'pungent':.6}, {'spicy':.5,'woody':.3}, ['grind','temper']),
          ('fennel', ['fennel','saunf'], {'sweet':.3}, {'anise':.7,'herbal':.4}, ['grind','temper']),
          ('clove', ['clove','laung'], {'pungent':.5}, {'spicy':.7,'woody':.4}, ['toast','grind']),
          ('cinnamon', ['cinnamon','dalchini'], {'sweet':.2}, {'woody':.6,'sweet':.4}, ['toast','grind']),
          ('mango powder', ['mango powder','amchur'], {'sour':.6}, {'fruity':.5}, ['grind']),
          ('peanut', ['peanut','peanuts','groundnut','moongphali'], {'umami':.2,'sweet':.1}, {'nutty':.7,'roasted':.4}, ['roast','fry','grind']),
        ]
        return [Ingredient(k,k,set(a),t,o,set(p),[Evidence('seed-fixture',k,'HYPOTHESIS',.1)]) for k,a,t,o,p in rows]

    @staticmethod
    def _seed_recipes():
        """Expanded synthetic recipe corpus.
        Every recipe is a software fixture, NOT a claim of real-world food quality.
        """
        common = [
          ('r01','Tomato Tamarind Dal',['tomato','tamarind','lentil','ginger','cumin'],['boil','temper','simmer']),
          ('r02','Coconut Sesame Chutney',['coconut','sesame','ginger','chili'],['toast','grind','blend']),
          ('r03','Smoky Tomato Curry',['tomato','onion','garlic','black cardamom','cumin'],['fry','toast','simmer']),
          ('r04','Tamarind Lentil Stew',['tamarind','lentil','onion','cumin'],['boil','temper','simmer']),
          ('r05','Coconut Tomato Curry',['coconut','tomato','ginger','cumin'],['fry','blend','simmer']),
          ('r06','Sesame Tomato Chutney',['sesame','tomato','ginger','chili'],['toast','grind','blend']),
          ('r07','Black Cardamom Dal',['black cardamom','lentil','onion','ginger'],['toast','boil','simmer']),
          ('r08','Coconut Tamarind Stew',['coconut','tamarind','lentil','chili'],['blend','simmer']),
          ('r09','Green Cardamom Rice',['green cardamom','cumin','ginger','ghee'],['temper','simmer']),
          ('r10','Turmeric Garlic Curry',['turmeric','garlic','onion','mustard seed','curry leaf'],['fry','temper','simmer']),
          ('r11','Fenugreek Paratha Dough',['fenugreek','green cardamom','ghee'],['knead','fry']),
          ('r12','Tamarind Rice Bowl',['tamarind','mustard seed','curry leaf','peanut','cumin','fenugreek'],['temper','fry']),
          ('r13','Black Pepper Rasam',['black pepper','tamarind','mustard seed','asafoetida','curry leaf'],['temper','simmer']),
          ('r14','Bay Leaf Pilaf',['bay leaf','cinnamon','clove','green cardamom','cumin','onion'],['temper','simmer']),
          ('r15','Yogurt Spiced Curry',['yogurt','cumin','turmeric','garlic','ginger','chili'],['temper','simmer']),
          ('r16','Jaggery Coconut Sweet',['jaggery','coconut','sesame','green cardamom'],['blend','reduce']),
          ('r17','Smoky Eggplant Mash',['tomato','onion','garlic','chili','cumin','mustard seed'],['roast','fry','temper']),
          ('r18','Fennel Clove Chai',['fennel','clove','cinnamon','ginger'],['boil','simmer']),
        ]
        return [Recipe(i,t,x,[{'order':n+1,'process':p,'temperature':None,'duration':None,'resulting_state':None} for n,p in enumerate(s)]) for i,t,x,s in common]

    def resolve_query(self, values: list[str]) -> list[ParsedIngredient]:
        return [parse_ingredient(x,self.resolver) for x in values]

    def _sensory(self, item: Ingredient) -> dict[str, float]:
        """Merged taste+odor sensory map.

        The MVP scores targets against whatever sensory observations exist,
        regardless of the modality boundary, because a query such as
        ``{"sour": 0.8}`` must be able to retrieve tamarind via its *taste*
        profile and saffron via its *odor* profile. Both are explicit
        observations; neither is treated as a causal claim.
        """
        merged: dict[str, float] = {}
        for src in (item.taste, item.odor):
            for k, v in src.items():
                merged[k] = max(merged.get(k, 0.0), float(v))
        return merged

    def retrieve(self, target: dict[str,float], query_ids: set[str], k=5, mode='hybrid'):
        out=[]
        for item in self.ingredients:
            if item.id in query_ids: continue
            smell = self._sensory(item)
            sensory = sum(min(smell.get(x,0),v) for x,v in target.items()) / (sum(target.values()) or 1)
            recipe_count=sum(1 for r in self.recipes if item.canonical_name in r.ingredients)
            structured = sensory + (0.2 if recipe_count else 0)
            score = structured if mode in ('structured','hybrid') else sensory
            out.append({'ingredient_id':item.id,'name':item.canonical_name,'score':round(score,4),'sensory_evidence':item.odor,'recipe_count':recipe_count,'evidence_label':'HYPOTHESIS'})
        return sorted(out,key=lambda x:(-x['score'],x['name']))[:k]

    def generate(self, values, target, avoid_reproduction=True):
        parsed=self.resolve_query(values); resolved=[p for p in parsed if p.canonical_id]
        ids={p.canonical_id for p in resolved}; candidates=[]
        for item in self.ingredients:
            if item.id in ids: continue
            smell = self._sensory(item)
            best=sum(min(smell.get(x,0),v) for x,v in target.items())/(sum(target.values()) or 1)
            comp={'score':round(best,4),'evidence_label':'MODEL_PREDICTION','sensory_target_coverage':round(best,4),'redundancy':0.0,'process_compatibility':0.0}
            known=sum(1 for r in self.recipes if item.canonical_name in r.ingredients and any(x in r.ingredients for x in ids))
            reference=next(iter(ids)) if ids else None
            pair_key=tuple(sorted((item.id,reference))) if reference else None
            pair_count=self.pair_counts.get(pair_key,0) if pair_key else 0
            nov=novelty(pair_count,len(self.recipes))
            candidates.append({'ingredient':item.canonical_name,'ingredient_id':item.id,'compatibility':comp,'novelty':nov,'known_pair_count':known})
        candidates.sort(key=lambda x:(-(x['compatibility']['score'] + .25*x['novelty']['score']),x['ingredient']))
        selected=candidates[:2]
        return {'intent':{'ingredients':values,'target':target,'avoid_reproduction':avoid_reproduction},'resolved_entities':[asdict(x) for x in parsed],'candidates':selected,'process_proposal':[{'process':'toast','parameters':{'temperature':None,'duration':None,'medium':'dry pan'},'evidence_type':'HYPOTHESIS'},{'process':'blend','parameters':{'temperature':None,'duration':None},'evidence_type':'HYPOTHESIS'},{'process':'reduce','parameters':{'temperature':None,'duration':None},'evidence_type':'HYPOTHESIS'}],'known_recipe_matches':self._known_matches(ids),'validation':self.validate(parsed,selected),'evidence_ledger':[{'claim':'Seed sensory profiles are fixture hypotheses','evidence_type':'HYPOTHESIS','source':'seed-fixture','confidence':.1},{'claim':'Novelty labels are relative to the indexed fixture corpus','evidence_type':'SOURCE_DERIVED','source':'pair_counts'}]}

    def _known_matches(self, ids):
        return [{'recipe_id':r.recipe_id,'title':r.title,'overlap':len(ids & {self.resolver.resolve(x).id for x in r.ingredients if self.resolver.resolve(x)})} for r in self.recipes if len(ids & {self.resolver.resolve(x).id for x in r.ingredients if self.resolver.resolve(x)})>=2]

    @staticmethod
    def validate(parsed, candidates):
        issues=[]
        unresolved=[p.raw_value for p in parsed if not p.canonical_id]
        if unresolved: issues.append({'severity':'error','type':'unresolved_ingredient','values':unresolved})
        if not candidates: issues.append({'severity':'error','type':'no_candidate'})
        return {'status':'FAIL' if issues else 'PASS','issues':issues,'claim_status':{'scientific_evidence':'UNCERTAIN','novelty':'INFERRED','safety':'UNASSESSED'}}
