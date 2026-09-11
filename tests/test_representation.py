import pytest
from food_intelligence.representation import *
from food_intelligence.retrieval import MultiViewIndex
from food_intelligence.synthetic import demonstrate

def p(status='REAL', evidence='SOURCE_DERIVED', sid='x'):
    return Provenance(sid, sid, '1', 'r1', '2026-09-11', 'research_only', 'p1', 'm1', .8, evidence, data_status=status)

def test_compound_provenance_and_missing_identifier():
    c=Compound('c1','unknown compound',provenance=p())
    assert c.smiles is None and c.provenance.source_id=='x'
    m=CompoundMapping('i','c1',None,True,provenance=p())
    assert m.relation=='COMPOUND_PRESENT'

def test_missing_is_not_zero():
    x=Observation('odor',None,observed=False,provenance=p())
    assert_no_missing_as_zero([x])
    with pytest.raises((AssertionError, ValueError)): Observation('odor',0,observed=False,provenance=p())

def test_conflict_is_preserved():
    a=EvidenceConflict('i:odor',('e1','e2'),'conflict',rationale='different matrices')
    assert a.status=='conflict' and len(a.evidence_ids)==2

def test_molecular_not_compatibility():
    assert molecular_similarity(['same'],['same'])==1
    c=compatibility_components(chemical_similarity=1.0, culinary_cooccurrence=0.0)
    assert c['chemical_similarity']==1 and c['culinary_cooccurrence']==0

def test_representation_and_retrieval_are_separate():
    idx=MultiViewIndex(); idx.add(Representation('a','MOLECULAR','explicit','1',(1.,0.),data_status='SYNTHETIC',provenance=p('SYNTHETIC','HYPOTHESIS','SYNTHETIC_TEST_DATA')))
    q=Representation('q','MOLECULAR','explicit','1',(1.,0.),data_status='SYNTHETIC',provenance=p('SYNTHETIC','HYPOTHESIS','SYNTHETIC_TEST_DATA'))
    assert idx.search('MOLECULAR',q)[0]['entity_id']=='a'

def test_synthetic_demo_has_boundary_notice():
    out=demonstrate(); assert out['data_status']=='SYNTHETIC'; assert 'SYNTHETIC' in out['notice']; assert out['results'][0]['novelty']['label']=='UNKNOWN'

def test_transformation_unknowns_allowed():
    t=Transformation('t1','garlic/raw','fry','garlic/fried',{'temperature':None,'duration':None},{'odor_change':None},p('SYNTHETIC','HYPOTHESIS','SYNTHETIC_TEST_DATA'))
    assert t.parameters['temperature'] is None
