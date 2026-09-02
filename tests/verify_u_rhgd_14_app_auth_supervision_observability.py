#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
import jsonschema, yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
DATA=ROOT/'dados/rhgd-0.0.1/U-RHGD-14-app-auth-supervision-observability.yaml'
DOC=ROOT/'docs/arquitetura/14-app-auth-supervision-observability.md'
AUTH=ROOT/'contratos/rhgd-0.0.1/application-auth.schema.json'
OBS=ROOT/'contratos/rhgd-0.0.1/transport-observability.schema.json'
UNIT_TEST=ROOT/'tests/test_application_auth_observability.py'

def fail(x): print('RHGD_U14_APP_AUTH_SUPERVISION_OBSERVABILITY=FAIL',x); raise SystemExit(2)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    for p in (DATA,DOC,AUTH,OBS,UNIT_TEST):
        if not p.exists(): fail('missing:'+str(p.relative_to(ROOT)))
    for p in (AUTH,OBS): jsonschema.Draft202012Validator.check_schema(json.loads(p.read_text(encoding='utf-8')))
    d=yaml.safe_load(DATA.read_text(encoding='utf-8'))
    if d.get('schema')!='rhgd-u14-app-auth-supervision-observability-evidence/1': fail('schema')
    if d.get('unit')!='U-RHGD-14-PARALLEL-40-WORK-UNITS-ORCHESTRATION': fail('unit')
    if d.get('implementation_commit')!='c5113356e47e24ba2f2bcb34b02aa892cbc8b76e': fail('implementation_commit')
    ex=d['execution']
    if (ex['case_start'],ex['case_end'],ex['selected_units'],ex['passed'],ex['failed'])!=(1,40,40,40,0): fail('parallel-counts')
    if ex['physical_slots']!=4 or ex['max_parallel_observed']!=4: fail('parallel-bound')
    wus=d['work_units']
    if len(wus)!=40 or [x['unit'] for x in wus] != [f'U14-W{i:02d}' for i in range(1,41)] or any(x['status']!='PASS' for x in wus): fail('work-units')
    auth=d['application_auth']
    for k in ('explicit_peer_join_required','body_hash_bound','method_path_timestamp_nonce_bound','persistent_anti_replay','nonce_persisted_as_sha256_only','multiple_keys_supported'):
        if auth.get(k) is not True: fail('auth:'+k)
    if auth.get('secret_persisted') is not False: fail('secret-persistence')
    ob=d['observability']
    if ob.get('payload_in_metrics') is not False or ob.get('secret_in_metrics') is not False or ob.get('authenticated_metrics_endpoint') is not True: fail('observability-boundary')
    if d['authority']!={'queue':'envelope_transport_only','scheduler':False,'lease_grant':False,'admission':False}: fail('authority')
    sup=d['supervision']
    if sup.get('definition')!='systemd' or sup.get('restart')!='on-failure' or sup.get('dynamic_user') is not True: fail('supervision')
    if sup.get('live_supervised_service_runtime')!='NOT_OBSERVED': fail('runtime-overclaim')
    gates=d['gates']
    for k in ('APPLICATION_AUTH','PERSISTENT_ANTI_REPLAY','NO_SECRET_PERSISTENCE','OBSERVABILITY','PAYLOAD_FREE_METRICS','AUTHENTICATED_METRICS','SUPERVISION_DEFINITION','PARALLEL_40','PHYSICAL_SLOT_BOUND','PGD_EXECUTION_REF_PRESERVED','NO_SECOND_SCHEDULER'):
        if gates.get(k)!='PASS': fail('gate:'+k)
    if gates.get('LIVE_SUPERVISED_SERVICE_RUNTIME')!='NOT_OBSERVED' or gates.get('PRODUCTION')!='BLOCKED': fail('maturity')
    for rel,expected in d['source_sha256'].items():
        p=ROOT/rel
        if not p.exists() or sha(p)!=expected: fail('hash:'+rel)
    # Execute the five focused unit tests as an independent gate.
    spec=importlib.util.spec_from_file_location('u14_unit',UNIT_TEST); m=importlib.util.module_from_spec(spec); sys.modules['u14_unit']=m; spec.loader.exec_module(m)
    import unittest
    suite=unittest.defaultTestLoader.loadTestsFromModule(m); result=unittest.TextTestRunner(stream=sys.stderr,verbosity=0).run(suite)
    if not result.wasSuccessful() or result.testsRun!=5: fail('focused-unit-tests')
    text=DOC.read_text(encoding='utf-8')
    for marker in ('HMAC-SHA256','40/40 PASS','scheduler=false','LIVE_SUPERVISED_SERVICE_RUNTIME=NOT_OBSERVED','produção permanece `BLOCKED`'):
        if marker not in text: fail('doc:'+marker)
    print('RHGD_U14_APP_AUTH_SUPERVISION_OBSERVABILITY=PASS')
if __name__=='__main__': main()
