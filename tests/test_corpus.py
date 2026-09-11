import pytest
from food_intelligence.corpus import *

def r(id, ingredients=('tomato','ginger'), group=None, dataset='ELR-1000', status='ADMITTED'):
    return CorpusRecord(dataset, dataset, id, 'RESEARCH_ONLY', 'high', status, group or id, id, ingredients, 'east', 'as', ('raw',), ('boil',), True, True)

def test_provenance_admission_fails_closed():
    with pytest.raises(ValueError): assert_admitted([r('q', status='QUARANTINED')])

def test_quality_and_pairs_are_deterministic():
    rows=[r('1'), r('2', ingredients=('tomato','cumin'))]
    q=corpus_quality(rows)
    assert q['recipe_count']==2 and q['canonical_recipe_count']==2
    pairs=pairing_baseline(rows)
    assert pairs[0]['co_occurrence']==1
    assert pairs[0]['claim_type']=='SOURCE_DERIVED'

def test_group_leakage_is_impossible():
    rows=[r('a',group='g'),r('b',group='g')]
    splits=leakage_safe_split(rows)
    assert len({x['split'] for x in splits})==1

def test_commercial_contamination_fails_for_research_record():
    result=contamination_audit([r('1')], {'Sangat Food DB'})
    assert result['status']=='FAIL' and result['count']==1

def test_empty_corpus_is_explicit_not_fabricated():
    q=corpus_quality([])
    assert q['recipe_count']==0 and q['canonical_recipe_count']==0
    assert corpus_relative_novelty(('a','b'),[])['label']=='UNKNOWN'
