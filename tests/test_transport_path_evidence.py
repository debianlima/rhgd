import json, unittest
from pathlib import Path
import jsonschema
from transport_path_evidence import TransportPathEvidence, transport_path_bonus
from rhgd_cognitive_dag import NodeCapability, WorkUnit, FederatedDestinationMatcher
ROOT=Path(__file__).resolve().parents[1]

def ev(node,transport='NETMAKER',rtt=5,bw=800,loss=.1,observed=1000,expires=5000):
    return TransportPathEvidence(f'path:{node}','source',node,transport,observed,expires,'observado','probe:test',True,rtt,bw,loss,1420)

class TestTransportPathEvidence(unittest.TestCase):
    def test_schema_accepts_projection_and_zero_authority(self):
        schema=json.loads((ROOT/'contratos/rhgd-0.0.1/transport-path-evidence.schema.json').read_text())
        jsonschema.validate(ev('n1').as_contract(),schema)
        bad=ev('n1').as_contract(); bad['authority']['scheduler']=True
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(bad,schema)

    def test_fresh_metrics_create_bonus_without_transport_name_preference(self):
        a=transport_path_bonus(ev('a','NETMAKER',rtt=5,bw=900),now_ms=2000)
        b=transport_path_bonus(ev('b','IPSEC',rtt=5,bw=900),now_ms=2000)
        self.assertEqual(a,b); self.assertGreater(a,0)

    def test_stale_or_unavailable_evidence_has_zero_bonus(self):
        self.assertEqual(transport_path_bonus(ev('a',expires=1500),now_ms=2000),0)
        x=ev('a'); x=TransportPathEvidence(**{**x.__dict__,'classification':'indisponivel'})
        self.assertEqual(transport_path_bonus(x,now_ms=2000),0)

    def test_matcher_uses_fresh_path_evidence_only_as_ranking_signal(self):
        nodes=[NodeCapability('slow',131072,.8,2,('docs',)),NodeCapability('fast',131072,.8,2,('docs',))]
        w=[WorkUnit('w','docs',64000,1)]
        m=FederatedDestinationMatcher()
        base=m.match(w,nodes); self.assertEqual(base[0].node_id,'slow')
        paths={'slow':ev('slow','IPSEC',rtt=60,bw=50),'fast':ev('fast','NETMAKER',rtt=4,bw=900)}
        ranked=m.match(w,nodes,path_evidence=paths,now_ms=2000)
        self.assertEqual(ranked[0].node_id,'fast')
        self.assertFalse(any(hasattr(m,x) for x in ('queue','lease','admission','retry','runtime_state')))

    def test_bad_identity_or_metric_rejected(self):
        with self.assertRaises(ValueError): TransportPathEvidence('', 'a','b','NETMAKER',1,2,'observado','x',True).validate()
        with self.assertRaises(ValueError): ev('a',loss=101).validate()

if __name__=='__main__': unittest.main()
