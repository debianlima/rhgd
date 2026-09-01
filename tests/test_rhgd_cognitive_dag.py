import unittest
from rhgd_cognitive_dag import *
class TestRHGD(unittest.TestCase):
 def test_4b_16k_semantic_units_are_schedulable(self):
  nodes=[NodeCapability('4b-a',16384,.8,2,('code',)),NodeCapability('big',131072,.7,2,('science',))]
  units=[WorkUnit('w1','code',7000,1),WorkUnit('w2','science',32000,1)]
  a=CognitiveScheduler().assign(units,nodes); self.assertEqual([(x.work_id,x.node_id) for x in a],[('w1','4b-a'),('w2','big')])
 def test_privacy_blocks_ineligible_remote(self):
  self.assertEqual(CognitiveScheduler().assign([WorkUnit('secret','code',4000,4)],[NodeCapability('public',16000,.9,2,('code',))]),[])
 def test_reduce_preserves_dissent_and_provenance(self):
  rs=[CognitiveResult('a','n1',('A',),('E1',),(),.8),CognitiveResult('b','n2',('A',),('E2',),('B pode ser melhor',),.9)]
  x=HierarchicalReducer().reduce(rs,fan_in=2); self.assertIn('B pode ser melhor',x['dissent']); self.assertEqual(len(x['sources']),2); self.assertEqual(x['claims'],['A'])

 def test_reduction_is_order_independent(self):
  import itertools,json,hashlib
  rs=[
   CognitiveResult('w1','n1',('Alpha','Beta'),('E1',),(),.8),
   CognitiveResult('w2','n2',(' beta ','Gamma'),('E2',),('Delta',),.7),
   CognitiveResult('w3','n3',('ALPHA',),('E3','E1'),(' epsilon ',),.9),
   CognitiveResult('w4','n4',('Zeta',),(),('DELTA',),.6),
  ]
  hashes=set()
  for perm in itertools.permutations(rs):
   x=HierarchicalReducer().reduce(perm,fan_in=2)
   logical={k:x[k] for k in ('claims','evidence','dissent','sources')}
   hashes.add(hashlib.sha256(json.dumps(logical,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
  self.assertEqual(len(hashes),1)
 def test_reduction_logical_content_is_fan_in_independent(self):
  rs=[CognitiveResult(str(i),f'n{i}',(f'C{i%3}',),(f'E{i%2}',),(f'D{i%2}',),.5+i/100) for i in range(9)]
  outs=[]
  for fan in (2,3,4,8):
   x=HierarchicalReducer().reduce(rs,fan_in=fan); outs.append({k:x[k] for k in ('claims','evidence','dissent','sources')})
  self.assertTrue(all(x==outs[0] for x in outs[1:]))
 def test_normalization_deduplicates_without_losing_determinism(self):
  rs=[CognitiveResult('a','n1',('Árvore   B+',),(),(),.5),CognitiveResult('b','n2',('ÁRVORE B+',),(),(),.5)]
  x=HierarchicalReducer().reduce(rs,fan_in=2); self.assertEqual(len(x['claims']),1)
 def test_dissent_blocks_silent_collapse_and_keeps_supporter(self):
  rs=[CognitiveResult('w1','n1',('A',),('e1',),(),.8),CognitiveResult('w2','n2',('A',),('e2',),('B pode ser melhor',),.7)]
  x=HierarchicalReducer().reduce(rs,fan_in=2)
  self.assertFalse(x['collapse_allowed']); self.assertEqual(x['resolution_status'],'DISSENT_PRESERVED')
  self.assertEqual(len(x['dissent_records']),1); self.assertEqual(x['dissent_records'][0]['node_id'],'n2'); self.assertEqual(x['dissent_records'][0]['work_id'],'w2')
 def test_no_dissent_remains_collapsible(self):
  rs=[CognitiveResult('w1','n1',('A',),(),(),.8),CognitiveResult('w2','n2',('A',),(),(),.7)]
  x=HierarchicalReducer().reduce(rs,fan_in=2); self.assertTrue(x['collapse_allowed']); self.assertEqual(x['resolution_status'],'NO_DISSENT_DECLARED')
 def test_dissent_metadata_is_order_and_fanin_independent(self):
  import itertools,json,hashlib
  rs=[CognitiveResult('w1','n1',('A',),(),('D1',),.8),CognitiveResult('w2','n2',('A',),(),(' d1 ',),.7),CognitiveResult('w3','n3',('A',),(),('D2',),.9)]
  hashes=set()
  for fan in (2,3):
   for perm in itertools.permutations(rs):
    x=HierarchicalReducer().reduce(perm,fan_in=fan)
    logical={k:x[k] for k in ('dissent','dissent_records','collapse_allowed','resolution_status')}
    hashes.add(hashlib.sha256(json.dumps(logical,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
  self.assertEqual(len(hashes),1)
 def test_commitment_is_deterministic(self):
  w=WorkUnit('x','code',2000); self.assertEqual(signed_payload_stub(w),signed_payload_stub(w))
if __name__=='__main__': unittest.main()
