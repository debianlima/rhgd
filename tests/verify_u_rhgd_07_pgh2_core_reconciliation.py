#!/usr/bin/env python3
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'dados/rhgd-0.0.1/U-RHGD-07-pgh2-core-reconciliation.yaml'
DOC=ROOT/'docs/arquitetura/07-pgh2-core-reconciliation.md'

def fail(msg):
    print('RHGD_U07_PGH2_CORE_RECONCILIATION=FAIL',msg)
    raise SystemExit(2)

def main():
    if not DATA.exists(): fail('missing-data')
    if not DOC.exists(): fail('missing-doc')
    d=yaml.safe_load(DATA.read_text(encoding='utf-8'))
    if d.get('schema')!='rhgd-pgh2-core-reconciliation/1': fail('schema')
    if d.get('unit')!='U-RHGD-07-PGH2-CORE-RECONCILIATION': fail('unit')
    refs=d.get('refs') or {}
    expected={
      'PGH':'304b9914ae44b0ac4240d912bd81f7be87d5a708',
      'PGD':'3f7d70e974271a0ee316df9425d5e955225fddd4',
      'PGA':'c151e58adf05339eee7f762fa0a96b401e4b6985',
      'PGD_RUNTIME_SAFE_POINT':'df125bb64069ca87c614587d652c15634264f7bb'
    }
    for k,v in expected.items():
        if refs.get(k)!=v: fail('ref:'+k)
    if refs.get('MSGCD')!='PGH_COMPOSITION_AGGREGATION_NO_FOURTH_AUTHORITY': fail('msgcd')
    boundaries=d.get('authority_boundaries') or {}
    wanted={
      'PGA':'policy_governance_authority',
      'PGH':'semantic_authorization_knowledge_contracts_evidence',
      'PGD':'runtime_scheduler_queue_lease_retry_recovery',
      'RHGD':'federation_discovery_transport_no_second_scheduler',
      'MSGCD':'aggregation_unified_view_no_independent_authority'
    }
    if boundaries!=wanted: fail('authority-boundaries')
    facts=d.get('reconciled_facts') or {}
    if facts.get('pga_standalone_materialized') is not True: fail('pga-materialized')
    if facts.get('pgd_federation_contract')!='pgd-rhgd-federation/1': fail('federation-contract')
    if facts.get('runtime_parallel_prohibited') is not True: fail('parallel-runtime')
    if facts.get('msgcd_standalone_repo_required') is not False: fail('msgcd-repo')
    if facts.get('rhgd_release_state')!='standby_candidate': fail('release-state')
    gates=d.get('gates') or {}
    for k in ('DELTA_INVENTORY','LEARNING_PRESERVED','PGD_REF','PGA_REF','PGH_REF','RUNTIME_SAFE_POINT','MSGCD_BOUNDARY','AUTHORITY_BOUNDARY','NO_DUPLICATE_RUNTIME','NO_SECOND_SCHEDULER','RELEASE_IMMUTABILITY'):
        if gates.get(k)!='PASS': fail('gate:'+k)
    for k in ('RECONCILIATION_CLOSURE','DEPENDENCY_REFERENCES'):
        if gates.get(k) not in ('PENDING','PASS'): fail('gate:'+k)
    comp=yaml.safe_load((ROOT/'competencias.yaml').read_text(encoding='utf-8')) or {}
    ids={x.get('id'):x for x in comp.get('competencias',[])}
    if str(ids.get('github-incremental-reconciliation',{}).get('versao_minima'))!='7': fail('reconciliation-skill-ref')
    if str(ids.get('telemetry-data-visualization',{}).get('versao_minima'))!='2': fail('telemetry-skill-ref')
    text=(ROOT/'estado.md').read_text(encoding='utf-8')
    if 'PGA standalone está materializado' not in text: fail('state-pga')
    if 'MSGCD permanece composição agregadora' not in text: fail('state-msgcd')
    doc=DOC.read_text(encoding='utf-8')
    for marker in ('PGH 2.0','PGD','PGA','RHGD','MSGCD','df125bb64069ca87c614587d652c15634264f7bb','sem segundo scheduler'):
        if marker not in doc: fail('doc:'+marker)
    print('RHGD_U07_PGH2_CORE_RECONCILIATION=PASS')
if __name__=='__main__': main()
