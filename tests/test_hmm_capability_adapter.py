import unittest
from hmm_capability_adapter import executor_profile_from_hmm

def advert(configured,usable):
 return {"schema_version":"hmm-capability-advertisement/1","context_capacity":{"configured_tokens":configured,"usable_tokens":usable},"authority":{"mode":"read_only_advisory","scheduler":False,"lease_grant":False}}
class TestHMMCapabilityAdapter(unittest.TestCase):
 def test_maps_explicit_context_capacity_only(self):
  p=executor_profile_from_hmm(advert(131072,100000),executor_id="gpu-node",reserve_tokens=8000)
  self.assertEqual(p.model_context_capacity,131072); self.assertEqual(p.effective_context_budget,100000); self.assertEqual(p.capability_source,"hmm-capability-advertisement/1")
 def test_rejects_missing_or_authoritative_scheduler_claim(self):
  with self.assertRaises(ValueError): executor_profile_from_hmm({"schema_version":"hmm-capability-advertisement/1","authority":{"mode":"read_only_advisory","scheduler":False,"lease_grant":False}},executor_id="x")
  bad=advert(32000,28000); bad["authority"]["scheduler"]=True
  with self.assertRaises(ValueError): executor_profile_from_hmm(bad,executor_id="x")
 def test_rejects_effective_above_configured(self):
  with self.assertRaises(ValueError): executor_profile_from_hmm(advert(32000,64000),executor_id="x")
if __name__=='__main__': unittest.main()
