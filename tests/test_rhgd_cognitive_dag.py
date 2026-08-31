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
 def test_commitment_is_deterministic(self):
  w=WorkUnit('x','code',2000); self.assertEqual(signed_payload_stub(w),signed_payload_stub(w))
if __name__=='__main__': unittest.main()
