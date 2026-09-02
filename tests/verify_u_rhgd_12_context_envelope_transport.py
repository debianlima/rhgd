#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import jsonschema, yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from context_envelope_transport import AsymmetricEnvelopeQueue, TRANSPORT_AUTHORITY
SCHEMA=ROOT/'contratos/rhgd-0.0.1/context-envelope-transport.schema.json'
DATA=ROOT/'dados/rhgd-0.0.1/U-RHGD-12-context-envelope-transport.yaml'
DOC=ROOT/'docs/arquitetura/12-context-envelope-transport.md'
LEX=ROOT/'lexico.yaml'
BOUNDARY_DOCS=[ROOT/'docs/arquitetura/00-modelo-logico-fase-zero.md',ROOT/'docs/arquitetura/01-fronteiras-pgh-pgd-pga-msgcd-rhgd.md',ROOT/'docs/politicas/00-politicas-consolidadas.md']
PGD_CONTRACT='contratos/pgd-1.0/rhgd-federation.schema.json'
PGD_HASH='3135f6cee8de163d55c9782b1b1de300359a0e2936f79f2a243a03941fefdc52'
def fail(x): print('RHGD_U12_CONTEXT_ENVELOPE_TRANSPORT=FAIL',x); raise SystemExit(2)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--suite-root',type=Path); args=ap.parse_args()
    for p in (SCHEMA,DATA,DOC,LEX,*BOUNDARY_DOCS):
        if not p.exists(): fail('missing:'+str(p.relative_to(ROOT)))
    schema=json.loads(SCHEMA.read_text(encoding='utf-8')); jsonschema.Draft202012Validator.check_schema(schema)
    q=AsymmetricEnvelopeQueue('a',joined_peer_ids={'b'},egress_capacity=2,ingress_capacity=5,stream_id='s',clock_ms=lambda:1700000000000)
    frame=q.put_outbound({'schema_version':'pgh.context-envelope/0.1'},work_id='w',model_ref='m',destination_peer='b',correlation_id='c',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
    jsonschema.validate(frame,schema)
    if frame['transport_authority']!=TRANSPORT_AUTHORITY: fail('authority')
    d=yaml.safe_load(DATA.read_text(encoding='utf-8'))
    if d.get('schema')!='rhgd-context-envelope-transport-evidence/1': fail('schema')
    if d['human_decision']['observed_in_conversation'] is not True: fail('human-decision')
    if set(d['authority_boundary']['PGD']) < {'ExecutionQueue','assignment_authority','lease','scheduler'}: fail('pgd-boundary')
    if set(d['authority_boundary']['RHGD']) < {'EnvelopeTransportQueue','put_envelope','get_envelope','ack_remove_envelope'}: fail('rhgd-boundary')
    tc=d['transport_contract']
    if tc['pgd_execution_ref_required'] is not True or tc['execution_authority']!='NONE': fail('transport-contract')
    if tc['pgd_provider_contract']!='pgd-rhgd-federation/1' or tc['pgd_provider_contract_sha256']!=PGD_HASH: fail('pgd-provider-ref')
    if d.get('implementation_commit')!='397e03821954ebeb88780b6658efec95ecb095b7': fail('implementation-commit')
    nt=d['network_test']
    if nt.get('homologation')!='v2_provider_aligned_execution_ref': fail('homologation')
    expected_hashes={
      'wireguard_sender':'b2897f3e99d4d7b4d14d9842f8f25133a08fc80d1169d9e8d3ddfd340d9886d4',
      'wireguard_receiver':'952137f7ad51bce3dd5a062bf1a4244b9f6831c18df31bc055f6b21d31220fe2',
      'ipsec_sender':'efffdd5a6c5b7d8c2c722c18ba02a6c1bb79078648a5be95b408cb4f764693e9',
      'ipsec_receiver':'a1d39604078fa74e46f79a144c87ad02e54a9b18ea2c4c8dc164228a245c8a60',
    }
    if nt.get('evidence_sha256')!=expected_hashes: fail('evidence-hashes')
    dirs=nt['directions']
    if len(dirs)!=2: fail('directions')
    expected_ids=[
      ['76420dbb2e187c633a5d6381889dc38f71b5d0ff9b2eaddcdd206696ef3e9388','acd6d12a7469e5b3055035356e500c9d602db2b29a39d9a3624e483b1098cc1e'],
      ['73596613b5b54e63f11706c8f136a1c019f60736bc92a78dbcdf588dad12f296','20fff05b6509ab408ba9aae5b11b661e2d3387c9ea33ea9fe7f484d0733077fc'],
    ]
    for i,x in enumerate(dirs):
        if x['sent_sequences']!=[1,2] or x['received_sequences']!=[1,2]: fail('order')
        if x['ack_statuses']!=['ACCEPTED','ACCEPTED']: fail('ack')
        if x['envelope_ids']!=expected_ids[i]: fail('envelope-ids')
        if len(x.get('pgd_execution_refs',[]))!=2 or not all(v.startswith('pgd://execution/') for v in x['pgd_execution_refs']): fail('execution-refs')
        if x['egress_empty_after_ack_remove'] is not True or x['ingress_empty_after_get_remove'] is not True: fail('remove')
        if x['sender_capacities']['egress']==x['sender_capacities']['ingress']: fail('sender-not-asymmetric')
    gates=d['gates']
    for k in ('HUMAN_QUEUE_DECISION','ASYMMETRIC_QUEUE','BIDIRECTIONAL_TRANSPORT','ORDER_PRESERVED','ACK_BEFORE_EGRESS_REMOVE','INGRESS_GET_REMOVE','EXPLICIT_JOIN','PGD_EXECUTION_REF_REQUIRED','PGD_PROVIDER_CONTRACT','CROSS_PEER_IDENTITY_MATCH','NO_PGD_EXECUTION_QUEUE_DUPLICATION','NO_LEASE_MINT','NO_SCHEDULER_AUTHORITY','TEMP_NETWORK_CHANGE_ROLLBACK'):
        if gates.get(k)!='PASS': fail('gate:'+k)
    if gates.get('PRODUCTION')!='BLOCKED': fail('production')
    lex=yaml.safe_load(LEX.read_text(encoding='utf-8'))['termos']
    if 'ExecutionQueue' not in lex or 'EnvelopeTransportQueue' not in lex or 'PGDExecutionRef' not in lex: fail('lexicon')
    for p in BOUNDARY_DOCS:
        text=p.read_text(encoding='utf-8')
        if 'EnvelopeTransportQueue' not in text or 'ExecutionQueue' not in text: fail('boundary-doc:'+p.name)
    text=DOC.read_text(encoding='utf-8')
    for marker in ('put_outbound','get_inbound','remove_inbound','ACK','fila de transporte','fila de execução','pgd_execution_ref'):
        if marker not in text: fail('doc:'+marker)
    if args.suite_root:
        import hashlib
        pgd=args.suite_root/'pgd'/PGD_CONTRACT
        if not pgd.exists(): fail('missing-pgd-provider-contract')
        if hashlib.sha256(pgd.read_bytes()).hexdigest()!=PGD_HASH: fail('pgd-provider-hash')
        provider=json.loads(pgd.read_text(encoding='utf-8'))
        response=(provider.get('properties') or {}).get('response',{}).get('properties',{})
        if 'execution_ref' not in response: fail('pgd-execution-ref-missing')
        request=(provider.get('properties') or {}).get('request',{}).get('properties',{})
        if 'assignment_ref' in request or 'pgd_assignment_ref' in json.dumps(provider): fail('invented-assignment-ref')
        print('PGD_EXECUTION_REF_PROVIDER_CONTRACT=PASS')
    print('RHGD_U12_CONTEXT_ENVELOPE_TRANSPORT=PASS')
if __name__=='__main__': main()
