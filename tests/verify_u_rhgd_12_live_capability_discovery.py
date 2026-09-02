#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
import jsonschema, yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from live_capability_discovery import CapabilityAnnouncer, READ_ONLY_AUTHORITY
SCHEMA=ROOT/'contratos/rhgd-0.0.1/live-capability-discovery.schema.json'
DATA=ROOT/'dados/rhgd-0.0.1/U-RHGD-12-live-capability-discovery.yaml'
DOC=ROOT/'docs/arquitetura/12-live-capability-discovery.md'
def fail(x): print('RHGD_U12_LIVE_CAPABILITY_DISCOVERY=FAIL',x); raise SystemExit(2)
def main():
    for p in (SCHEMA,DATA,DOC):
        if not p.exists(): fail('missing:'+str(p.relative_to(ROOT)))
    schema=json.loads(SCHEMA.read_text(encoding='utf-8')); jsonschema.Draft202012Validator.check_schema(schema)
    sample=CapabilityAnnouncer('peer-test',{'source':'test_declared'},ttl_ms=2000,clock_ms=lambda:1700000000000,boot_id='boot-test').snapshot()
    jsonschema.validate(sample,schema)
    d=yaml.safe_load(DATA.read_text(encoding='utf-8'))
    if d.get('schema')!='rhgd-live-capability-discovery-evidence/1': fail('schema')
    if d.get('unit')!='U-RHGD-12-LIVE-CAPABILITY-DISCOVERY-CONTRACT': fail('unit')
    if d['release']!={'version':'0.0.1','state':'standby_candidate','promoted':False}: fail('release')
    if d['execution']['kind']!='real_two_peer_overlay_test' or d['execution']['capability_values']!='test_declared': fail('execution')
    peers=d['peers']
    if len(peers)!=2 or {p['logical_id'] for p in peers}!={'peer-a','peer-b'}: fail('peers')
    obs=d['observations']
    for k in ('peer_a_discovers_peer_b','peer_b_discovers_peer_a'):
        if obs[k]['sequences']!=[1,2] or obs[k]['monotonic'] is not True: fail(k)
    if obs['stale_snapshot_rejected_after_ttl'] is not True: fail('stale')
    if obs['authority']!=READ_ONLY_AUTHORITY: fail('authority')
    sec=d['security_boundary']
    if sec['explicit_join_required'] is not True or sec['network_peer_authentication']!='wireguard-overlay': fail('security')
    if sec['application_layer_authentication']!='NOT_IMPLEMENTED': fail('app-auth-claim')
    if d['cleanup']!={'peer_a_listener_stopped':True,'peer_b_listener_stopped':True,'temporary_firewall_rules_removed':True,'peer_a_environment_verifier':'PASS','peer_b_environment_verifier':'PASS'}: fail('cleanup')
    m=d['maturity']
    if m['live_capability_discovery_mechanism']!='PASS' or m['two_real_peers']!='PASS' or m['production']!='BLOCKED': fail('maturity')
    gates=d['gates']
    for k in ('TWO_REAL_PEERS','BIDIRECTIONAL_DISCOVERY','MONOTONIC_SEQUENCE','TTL_STALE_REJECTION','EXPLICIT_JOIN','NO_SCHEDULER_AUTHORITY','TEMP_NETWORK_CHANGE_ROLLBACK','LIVE_DISCOVERY_MECHANISM'):
        if gates.get(k)!='PASS': fail('gate:'+k)
    if gates.get('PRODUCTION')!='BLOCKED': fail('production')
    text=DOC.read_text(encoding='utf-8')
    for marker in ('dois peers reais','sequence','stale','WireGuard','produção continua `BLOCKED`'):
        if marker not in text: fail('doc:'+marker)
    print('RHGD_U12_LIVE_CAPABILITY_DISCOVERY=PASS')
if __name__=='__main__': main()
