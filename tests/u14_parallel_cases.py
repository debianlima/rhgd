#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, threading, time, urllib.error, urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0,str(ROOT))
from application_auth import AuthBinding, AuthError, PersistentNonceStore, ReplayError, RequestAuthenticator, build_auth_headers
from context_envelope_transport import DurableEnvelopeQueue, EnvelopeTransportService
from persistent_envelope_daemon import AuthenticatedEnvelopeTransportHandler
from transport_observability import TransportMetrics

SECRET=b'u14-worker-secret-only-in-memory'
BINDING=AuthBinding('key-a','peer-a',SECRET)
NOW=1_700_000_000_000


def auth(db: Path, *, joined={'peer-a'}, now=NOW, max_skew=5000, bindings=None):
    return RequestAuthenticator(bindings or {'key-a':BINDING},nonce_store=PersistentNonceStore(db),joined_peer_ids=set(joined),clock_ms=lambda:now,max_clock_skew_ms=max_skew)

def headers(body=b'{}', *, method='POST', path='/rhgd/envelope', ts=NOW, nonce='nonce-0123456789', binding=BINDING):
    return build_auth_headers(binding,method,path,body,timestamp_ms=ts,nonce=nonce)

def expect(exc, fn):
    try: fn()
    except exc: return
    raise AssertionError(f'expected {exc.__name__}')

def make_sender(db: Path):
    return DurableEnvelopeQueue('peer-a',joined_peer_ids={'peer-b'},state_db=db,stream_id='send',egress_capacity=4,ingress_capacity=4)

def frame(sender, n=1, source_override=None):
    f=sender.put_outbound({'schema_version':'pgh.context-envelope/0.1','context_ref':f'pgh://u14/{n}','private':'payload-private'},work_id=f'w{n}',model_ref='m',destination_peer='peer-b',correlation_id=f'c{n}',authorization_ref=f'pgh://auth/{n}',pgd_execution_ref=f'pgd://execution/u14/{n}')
    if source_override is not None: f['source_peer']=source_override
    return f

def with_http_case(callback):
    with tempfile.TemporaryDirectory(dir=os.environ.get('RHGD_U14_TMPDIR') or None) as td:
        root=Path(td)
        recv=DurableEnvelopeQueue('peer-b',joined_peer_ids={'peer-a'},state_db=root/'recv.sqlite3',stream_id='recv',egress_capacity=4,ingress_capacity=4)
        au=auth(root/'auth.sqlite3')
        metrics=TransportMetrics()
        server=ThreadingHTTPServer(('127.0.0.1',0),AuthenticatedEnvelopeTransportHandler)
        server.envelope_transport_service=EnvelopeTransportService(recv); server.request_authenticator=au; server.transport_metrics=metrics
        t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
        try: return callback(root,server,recv,au,metrics)
        finally: server.shutdown(); server.server_close(); t.join(timeout=2); au.close(); recv.close()

def request(url, body=None, hdrs=None, method=None):
    req=urllib.request.Request(url,data=body,headers=hdrs or {},method=method)
    try:
        with urllib.request.urlopen(req,timeout=2) as r: return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read().decode())


def run_case(case_id: str) -> str:
    with tempfile.TemporaryDirectory(dir=os.environ.get('RHGD_U14_TMPDIR') or None) as td:
        d=Path(td); body=b'{"x":1}'
        if case_id=='U14-W01':
            a=auth(d/'a.db'); assert a.verify('POST','/rhgd/envelope',body,headers(body)).peer_id=='peer-a'; a.close()
        elif case_id=='U14-W02':
            a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',b'{"x":2}',headers(body))); a.close()
        elif case_id=='U14-W03':
            h=headers(body); h['X-RHGD-Signature']='0'*64; a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,h)); a.close()
        elif case_id=='U14-W04':
            h=headers(body); h['X-RHGD-Key-Id']='unknown'; a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,h)); a.close()
        elif case_id=='U14-W05':
            h=headers(body); h['X-RHGD-Peer-Id']='peer-x'; a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,h)); a.close()
        elif case_id=='U14-W06':
            a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,headers(body,ts=NOW-5001))); a.close()
        elif case_id=='U14-W07':
            a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,headers(body,ts=NOW+5001))); a.close()
        elif case_id=='U14-W08':
            h=headers(body); a=auth(d/'a.db'); a.verify('POST','/rhgd/envelope',body,h); expect(ReplayError,lambda:a.verify('POST','/rhgd/envelope',body,h)); a.close()
        elif case_id=='U14-W09':
            h=headers(body); a=auth(d/'a.db'); a.verify('POST','/rhgd/envelope',body,h); a.close(); a=auth(d/'a.db'); expect(ReplayError,lambda:a.verify('POST','/rhgd/envelope',body,h)); a.close()
        elif case_id=='U14-W10':
            a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/other',body,headers(body))); a.close()
        elif case_id=='U14-W11':
            a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('GET','/rhgd/envelope',body,headers(body))); a.close()
        elif case_id=='U14-W12':
            b2=AuthBinding('key-b','peer-b',b'u14-other-key-only-memory'); a=auth(d/'a.db',joined={'peer-a','peer-b'},bindings={'key-a':BINDING,'key-b':b2}); h=headers(body,binding=b2,nonce='nonce-b-0123456789'); assert a.verify('POST','/rhgd/envelope',body,h).peer_id=='peer-b'; a.close()
        elif case_id=='U14-W13':
            a=auth(d/'a.db',joined={'peer-b'}); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,headers(body))); a.close()
        elif case_id=='U14-W14':
            a=auth(d/'a.db'); a.verify('POST','/rhgd/envelope',body,headers(body)); a.close(); assert SECRET not in (d/'a.db').read_bytes()
        elif case_id=='U14-W15':
            nonce='nonce-plain-012345'; a=auth(d/'a.db'); a.verify('POST','/rhgd/envelope',body,headers(body,nonce=nonce)); a.close(); assert nonce.encode() not in (d/'a.db').read_bytes()
        elif case_id=='U14-W16':
            h=headers(body); del h['X-RHGD-Signature']; a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,h)); a.close()
        elif case_id=='U14-W17': expect(ValueError,lambda:build_auth_headers(BINDING,'POST','/rhgd/envelope',body,timestamp_ms=NOW,nonce='short'))
        elif case_id=='U14-W18':
            b='{"á":1}'.encode(); a=auth(d/'a.db'); assert a.verify('POST','/rhgd/envelope',b,headers(b,nonce='nonce-unicode-12345')).peer_id=='peer-a'; a.close()
        elif case_id=='U14-W19':
            a=auth(d/'a.db'); assert a.verify('POST','/rhgd/envelope',body,headers(body,ts=NOW+5000)).peer_id=='peer-a'; a.close()
        elif case_id=='U14-W20':
            a=auth(d/'a.db'); expect(AuthError,lambda:a.verify('POST','/rhgd/envelope',body,headers(body,ts=NOW-5001))); a.close()
        elif case_id=='U14-W21': m=TransportMetrics(clock_ms=lambda:NOW); m.record_transport_status('ACCEPTED'); assert m.snapshot(None)['counters']['transport_accepted']==1
        elif case_id=='U14-W22': m=TransportMetrics(clock_ms=lambda:NOW); m.record_transport_status('DUPLICATE'); assert m.snapshot(None)['counters']['transport_duplicate']==1
        elif case_id=='U14-W23': m=TransportMetrics(clock_ms=lambda:NOW); m.record_transport_status('ALREADY_CONSUMED'); assert m.snapshot(None)['counters']['transport_already_consumed']==1
        elif case_id=='U14-W24': m=TransportMetrics(clock_ms=lambda:NOW); m.record_auth_failure('bad'); assert m.snapshot(None)['counters']['auth_failure']==1
        elif case_id=='U14-W25': m=TransportMetrics(clock_ms=lambda:NOW); m.record_auth_failure('replay'); assert m.snapshot(None)['counters']['auth_replay']==1
        elif case_id=='U14-W26':
            q=make_sender(d/'q.db'); frame(q); m=TransportMetrics(clock_ms=lambda:NOW); assert m.snapshot(q)['queue_depth']['egress']==1; q.close()
        elif case_id=='U14-W27':
            s=make_sender(d/'s.db'); f=frame(s); r=DurableEnvelopeQueue('peer-b',joined_peer_ids={'peer-a'},state_db=d/'r.db',stream_id='r'); r.put_inbound(f); m=TransportMetrics(clock_ms=lambda:NOW); assert m.snapshot(r)['queue_depth']['ingress']==1; s.close(); r.close()
        elif case_id=='U14-W28':
            q=make_sender(d/'q.db'); frame(q); text=json.dumps(TransportMetrics(clock_ms=lambda:NOW).snapshot(q)); assert 'payload-private' not in text; q.close()
        elif case_id=='U14-W29': text=json.dumps(TransportMetrics(clock_ms=lambda:NOW).snapshot(None)).lower(); assert 'auth_key' not in text and 'signature' not in text
        elif case_id=='U14-W30': a=TransportMetrics(clock_ms=lambda:NOW).snapshot(None)['authority']; assert a=={'queue':'envelope_transport_only','scheduler':False,'lease_grant':False,'admission':False}
        elif case_id=='U14-W31':
            def cb(root,srv,recv,au,m):
                sender=make_sender(root/'send.db'); f=frame(sender); b=json.dumps(f,sort_keys=True,separators=(',',':')).encode(); h=headers(b,nonce='http-valid-123456'); st,x=request(f'http://127.0.0.1:{srv.server_port}/rhgd/envelope',b,h,'POST'); sender.close(); assert st==202 and x['status']=='ACCEPTED'
            with_http_case(cb)
        elif case_id=='U14-W32':
            def cb(root,srv,recv,au,m): st,x=request(f'http://127.0.0.1:{srv.server_port}/rhgd/envelope',b'{}',{'Content-Type':'application/json'},'POST'); assert st==401
            with_http_case(cb)
        elif case_id=='U14-W33':
            def cb(root,srv,recv,au,m):
                sender=make_sender(root/'send.db'); f=frame(sender,source_override='peer-x'); b=json.dumps(f,sort_keys=True,separators=(',',':')).encode(); h=headers(b,nonce='http-peer-123456'); st,x=request(f'http://127.0.0.1:{srv.server_port}/rhgd/envelope',b,h,'POST'); sender.close(); assert st==403
            with_http_case(cb)
        elif case_id=='U14-W34':
            def cb(root,srv,recv,au,m): st,x=request(f'http://127.0.0.1:{srv.server_port}/rhgd/metrics',None,{},'GET'); assert st==401
            with_http_case(cb)
        elif case_id=='U14-W35':
            def cb(root,srv,recv,au,m):
                h=headers(b'',method='GET',path='/rhgd/metrics',nonce='http-metrics-1234'); st,x=request(f'http://127.0.0.1:{srv.server_port}/rhgd/metrics',None,h,'GET'); assert st==200 and x['schema_version']=='rhgd-transport-observability/1' and 'context_envelope' not in json.dumps(x)
            with_http_case(cb)
        elif case_id=='U14-W36':
            s=(ROOT/'deploy/rhgd-envelope.service').read_text(); assert 'Restart=on-failure' in s and 'DynamicUser=yes' in s
        elif case_id=='U14-W37':
            s=(ROOT/'deploy/rhgd-envelope.service').read_text(); assert 'NoNewPrivileges=yes' in s and 'ProtectSystem=strict' in s and 'UMask=0077' in s
        elif case_id=='U14-W38':
            s=(ROOT/'deploy/rhgd-envelope.service').read_text(); assert 'LoadCredential=rhgd_auth_key:/run/rhgd/rhgd_auth_key' in s and SECRET.decode() not in s
        elif case_id=='U14-W39':
            q=make_sender(d/'q.db'); f=frame(q); assert f['pgd_execution_ref']=='pgd://execution/u14/1'; assert q.snapshot_state()['authority']['scheduler'] is False; q.close()
        elif case_id=='U14-W40':
            for p in [ROOT/'contratos/rhgd-0.0.1/application-auth.schema.json',ROOT/'contratos/rhgd-0.0.1/transport-observability.schema.json']:
                schema=json.loads(p.read_text()); jsonschema.Draft202012Validator.check_schema(schema)
        else: raise KeyError(case_id)
    return 'PASS'


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('case_id'); ap.add_argument('--hold-ms',type=int,default=0); args=ap.parse_args()
    start=time.time_ns()//1_000_000
    if args.hold_ms: time.sleep(args.hold_ms/1000)
    try:
        status=run_case(args.case_id); detail='ok'; rc=0
    except Exception as exc:
        status='FAIL'; detail=f'{type(exc).__name__}:{exc}'; rc=2
    end=time.time_ns()//1_000_000
    print(json.dumps({'unit':args.case_id,'telemetria_inicio_ms':start,'status':status,'detail':detail,'telemetria_fim_ms':end,'elapsed_ms':end-start},sort_keys=True))
    return rc
if __name__=='__main__': raise SystemExit(main())
