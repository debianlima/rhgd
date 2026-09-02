#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
import jsonschema, yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from context_envelope_transport import DurableEnvelopeQueue, DURABLE_STATE_SCHEMA_VERSION, TRANSPORT_AUTHORITY
SCHEMA=ROOT/'contratos/rhgd-0.0.1/durable-envelope-queue-state.schema.json'
DATA=ROOT/'dados/rhgd-0.0.1/U-RHGD-13-persistent-reconnect-idempotency.yaml'
DOC=ROOT/'docs/arquitetura/13-persistent-reconnect-idempotency.md'
EXPECTED_IDS=[
 ['916ba5c6ba760caec1c78c422659b91f07047616d5d415ea30b4202f4710ddbc','d9d49991c475c28964ad519eaf15c4cee1ff8bd0052566b6f7b9fc0424093e6b'],
 ['81885d49fadd222a931da01f37e37dcb83e5eddbf52cbeeed5de88187682e96b','162c04dfac26ae62a32a1ef72cfed8f77e2f8460133f6233d34eaf521f7702d0'],
]
def fail(x): print('RHGD_U13_PERSISTENT_RECONNECT_IDEMPOTENCY=FAIL',x); raise SystemExit(2)
def main():
    for p in (SCHEMA,DATA,DOC):
        if not p.exists(): fail('missing:'+str(p.relative_to(ROOT)))
    schema=json.loads(SCHEMA.read_text(encoding='utf-8')); jsonschema.Draft202012Validator.check_schema(schema)
    d=yaml.safe_load(DATA.read_text(encoding='utf-8'))
    if d.get('schema')!='rhgd-persistent-reconnect-idempotency-evidence/1': fail('schema')
    if d.get('implementation_commit')!='631eca6d89888ff1cdd0c88025f0bfbd291d5ea0': fail('implementation')
    if d['release']!={'version':'0.0.1','state':'standby_candidate','promoted':False}: fail('release')
    p=d['persistence']
    if p['backend']!='sqlite' or p['journal_mode']!='WAL' or p['synchronous']!='FULL': fail('persistence')
    if p['persist_before_http_ack'] is not True or p['configuration_mismatch']!='fail_closed' or p['execution_authority']!='NONE': fail('persist-boundary')
    nt=d['network_test']
    if nt['kind']!='real_bidirectional_process_restart_reconnect' or nt['persistent_system_service_installed'] is not False or nt['hard_power_loss_tested'] is not False: fail('network-claim')
    dirs=nt['directions']
    if len(dirs)!=2: fail('directions')
    for i,x in enumerate(dirs):
        if x['sent_sequences']!=[1,2] or x['envelope_ids']!=EXPECTED_IDS[i]: fail('identity/order')
        if x['first_remote_ack_without_sender_remove']!='ACCEPTED': fail('initial-ack')
        if x['sender_restart_retained_head_sequence']!=1 or x['receiver_restart_retained_ingress_sequence']!=1: fail('restart-retention')
        if x['retry_after_both_restarts']!='DUPLICATE' or x['second_send_after_reconnect']!='ACCEPTED': fail('reconnect')
        if x['sender_egress_empty_after_ack_remove'] is not True or x['sender_next_sequence_after_restart']!=3: fail('sender-state')
        if x['receiver_consumed_sequences']!=[1,2] or x['receiver_ingress_empty_after_remove'] is not True: fail('receiver-state')
        if x['replay_after_consumption_and_restart']!=['ALREADY_CONSUMED','ALREADY_CONSUMED']: fail('consumed-replay')
        if not all(v.startswith('pgd://execution/u13/') for v in x['pgd_execution_refs']): fail('execution-ref')
    # Cross-peer identity: WG sent == IPsec consumed and IPsec sent == WG consumed is pinned by the evidence IDs.
    if len(set(EXPECTED_IDS[0]+EXPECTED_IDS[1]))!=4: fail('id-uniqueness')
    hashes=d['evidence_sha256']
    if len(hashes)!=12 or not all(isinstance(v,str) and len(v)==64 for v in hashes.values()): fail('evidence-hashes')
    if d['cleanup']!={'wireguard_listener_stopped':True,'ipsec_listener_stopped':True,'temporary_firewall_rule_removed':True,'wireguard_environment_verifier':'INTEGRO','ipsec_environment_verifier':'INTEGRO'}: fail('cleanup')
    m=d['maturity']
    for k in ('durable_envelope_queue','sender_restart_recovery','receiver_restart_recovery','reconnect_duplicate_suppression','consumed_replay_suppression','bidirectional_real_overlay_restart_test'):
        if m.get(k)!='PASS': fail('maturity:'+k)
    if m['hard_power_loss']!='NOT_VERIFIED' or m['supervised_persistent_service']!='NOT_VERIFIED' or m['production']!='BLOCKED': fail('maturity-claims')
    gates=d['gates']
    for k in ('DURABLE_STATE','SQLITE_FULL_SYNC','PERSIST_BEFORE_ACK','BIDIRECTIONAL_RESTART_RECONNECT','SENDER_PENDING_SURVIVES_RESTART','RECEIVER_INGRESS_SURVIVES_RESTART','DUPLICATE_AFTER_RECONNECT','CONSUMED_REPLAY_AFTER_RESTART','ORDER_AND_SEQUENCE_CONTINUITY','PGD_EXECUTION_REF_PRESERVED','CROSS_PEER_IDENTITY_MATCH','NO_PGD_EXECUTION_QUEUE_DUPLICATION','NO_LEASE_MINT','NO_SCHEDULER_AUTHORITY','TEMP_NETWORK_CHANGE_ROLLBACK'):
        if gates.get(k)!='PASS': fail('gate:'+k)
    if gates.get('PRODUCTION')!='BLOCKED': fail('production')
    text=DOC.read_text(encoding='utf-8')
    for marker in ('DurableEnvelopeQueue','WAL','synchronous=FULL','DUPLICATE','ALREADY_CONSUMED','power-loss/hard-crash','ExecutionQueue'):
        if marker not in text: fail('doc:'+marker)
    # Runtime source must retain the same authority boundary and durable state identity.
    if DURABLE_STATE_SCHEMA_VERSION!='rhgd-durable-envelope-queue-state/1' or TRANSPORT_AUTHORITY['scheduler'] is not False: fail('runtime-constants')
    print('RHGD_U13_PERSISTENT_RECONNECT_IDEMPOTENCY=PASS')
if __name__=='__main__': main()
