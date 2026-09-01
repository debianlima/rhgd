import unittest
from context_preorchestrator import ContextPreOrchestrator, ContextCandidate, ExecutorProfile
from rhgd_cognitive_dag import WorkUnit
from pgd_federation_adapter import build_pgd_federation_payload, PGD_OWNS, RHGD_OWNS

class TestPGDFederationAdapter(unittest.TestCase):
    def setUp(self):
        router=ContextPreOrchestrator([ContextCandidate('project','project_skill',('software_engineering',),1200,1.0)])
        self.env=router.build('implementar software e testes',ExecutorProfile('node-1',model_context_capacity=16384))
        self.work=WorkUnit('WU-1','software-engineering',8000,privacy_level=2)

    def payload(self):
        return build_pgd_federation_payload(
            self.env,self.work,request_id='REQ-1',correlation_id='CORR-1',
            authorization_ref='pgh://auth/1',context_ref='pgh://context/1',
            idempotency_key='WU-1/rev1',expected_output_schema_ref='pgh://result/1',
            requested_lease_seconds=900,required_capabilities=('reasoning','structured-output'),
            remaining_depth=2,max_nodes=8)

    def test_contract_identity_and_authorization(self):
        p=self.payload()
        self.assertEqual(p['schema_version'],'pgd-rhgd-federation/1')
        self.assertEqual(p['request']['authorization_ref'],'pgh://auth/1')
        self.assertEqual(p['request']['context_envelope']['schema_version'],'pgh.context-envelope/0.1')

    def test_pgd_keeps_runtime_authority(self):
        p=self.payload()
        self.assertEqual(p['runtime_mapping']['pgd_owns'],PGD_OWNS)
        self.assertEqual(p['runtime_mapping']['rhgd_owns'],RHGD_OWNS)
        for forbidden in ('scheduler','lease','queue','admission'):
            self.assertNotIn(forbidden,p['runtime_mapping']['rhgd_owns'])

    def test_lease_is_request_not_grant(self):
        p=self.payload()
        self.assertEqual(p['request']['work_unit']['requested_lease_seconds'],900)
        self.assertIsNone(p['response']['lease_ref'])

    def test_result_is_observed(self):
        self.assertEqual(self.payload()['response']['outcome_classification'],'observed')

    def test_invalid_authority_or_budget_fails_closed(self):
        with self.assertRaises(ValueError):
            build_pgd_federation_payload(self.env,self.work,request_id='R',correlation_id='C',authorization_ref='',context_ref='X',idempotency_key='I',expected_output_schema_ref='S',requested_lease_seconds=10)
        with self.assertRaises(ValueError):
            build_pgd_federation_payload(self.env,self.work,request_id='R',correlation_id='C',authorization_ref='A',context_ref='X',idempotency_key='I',expected_output_schema_ref='S',requested_lease_seconds=0)

if __name__=='__main__': unittest.main()
