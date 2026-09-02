#!/usr/bin/env python3
"""Persistent authenticated RHGD ContextEnvelope receiver daemon."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from application_auth import AuthBinding, AuthError, PersistentNonceStore, ReplayError, RequestAuthenticator
from context_envelope_transport import DurableEnvelopeQueue, EnvelopeTransportService, TRANSPORT_PATH
from transport_observability import TransportMetrics

HEALTH_PATH = "/rhgd/health"
METRICS_PATH = "/rhgd/metrics"


def read_state(state_db: Path) -> dict:
    db=sqlite3.connect(f'file:{state_db}?mode=ro',uri=True,timeout=2.0)
    try:
        row=db.execute('SELECT payload,updated_at_ms FROM queue_state WHERE id=1').fetchone()
        if row is None:
            raise ValueError('durable queue state is empty')
        state=json.loads(row[0]); state['persisted_updated_at_ms']=row[1]
        return state
    finally:
        db.close()


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body=json.dumps(payload,sort_keys=True,separators=(',',':')).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type','application/json')
    handler.send_header('Cache-Control','no-store')
    handler.send_header('Content-Length',str(len(body)))
    handler.end_headers(); handler.wfile.write(body)


class AuthenticatedEnvelopeTransportHandler(BaseHTTPRequestHandler):
    server_version='RHGDAuthenticatedEnvelope/1'

    def _auth(self, method: str, body: bytes):
        authenticator=getattr(self.server,'request_authenticator',None)
        metrics=getattr(self.server,'transport_metrics',None)
        if not isinstance(authenticator,RequestAuthenticator):
            raise AuthError('application authenticator unavailable')
        try:
            return authenticator.verify(method,self.path,body,self.headers)
        except ReplayError:
            if isinstance(metrics,TransportMetrics): metrics.record_auth_failure('replay')
            raise
        except AuthError:
            if isinstance(metrics,TransportMetrics): metrics.record_auth_failure('auth')
            raise

    def do_GET(self) -> None:  # noqa: N802
        metrics=getattr(self.server,'transport_metrics',None)
        if isinstance(metrics,TransportMetrics): metrics.record_request()
        if self.path==HEALTH_PATH:
            _json_response(self,200,{'schema_version':'rhgd-health/1','status':'ok'})
            return
        if self.path!=METRICS_PATH:
            self.send_error(404); return
        try:
            self._auth('GET',b'')
            service=getattr(self.server,'envelope_transport_service',None)
            queue=getattr(service,'queue',None)
            if not isinstance(metrics,TransportMetrics): raise ValueError('metrics unavailable')
            _json_response(self,200,metrics.snapshot(queue))
        except AuthError as exc:
            _json_response(self,401,{'error':type(exc).__name__})
        except Exception as exc:
            _json_response(self,503,{'error':type(exc).__name__})

    def do_POST(self) -> None:  # noqa: N802
        metrics=getattr(self.server,'transport_metrics',None)
        if isinstance(metrics,TransportMetrics): metrics.record_request()
        if self.path!=TRANSPORT_PATH:
            self.send_error(404); return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<2 or length>4*1024*1024: raise ValueError('invalid body length')
            body=self.rfile.read(length)
            ident=self._auth('POST',body)
            frame=json.loads(body.decode('utf-8'))
            if frame.get('source_peer')!=ident.peer_id:
                raise PermissionError('authenticated peer does not match envelope source_peer')
            service=getattr(self.server,'envelope_transport_service',None)
            if not isinstance(service,EnvelopeTransportService): raise ValueError('transport service unavailable')
            ack=service.receive(frame)
            if isinstance(metrics,TransportMetrics): metrics.record_transport_status(ack['status'])
            _json_response(self,202,ack)
        except ReplayError as exc:
            _json_response(self,401,{'error':type(exc).__name__})
        except AuthError as exc:
            _json_response(self,401,{'error':type(exc).__name__})
        except PermissionError as exc:
            if isinstance(metrics,TransportMetrics): metrics.record_transport_status('REJECTED')
            _json_response(self,403,{'error':type(exc).__name__})
        except (ValueError,BufferError,json.JSONDecodeError) as exc:
            if isinstance(metrics,TransportMetrics): metrics.record_transport_status('REJECTED')
            _json_response(self,409,{'error':type(exc).__name__})

    def log_message(self, format: str, *args: object) -> None:
        return


def _read_secret_file(path: Path) -> bytes:
    data=path.read_bytes().rstrip(b'\r\n')
    if len(data)<16: raise ValueError('application auth credential must be at least 16 bytes')
    return data


def _parse_auth_binding(spec: str) -> tuple[str,str,Path]:
    parts=spec.split(':',2)
    if len(parts)!=3 or not all(parts): raise ValueError('auth binding must be KEY_ID:PEER_ID:SECRET_FILE')
    return parts[0],parts[1],Path(parts[2])


def main() -> int:
    ap=argparse.ArgumentParser(description='RHGD persistent authenticated EnvelopeTransportQueue daemon')
    sub=ap.add_subparsers(dest='command',required=True)
    sp=sub.add_parser('serve')
    sp.add_argument('--bind',required=True)
    sp.add_argument('--port',type=int,required=True)
    sp.add_argument('--peer-id',required=True)
    sp.add_argument('--joined-peer-id',action='append',required=True)
    sp.add_argument('--state-db',type=Path,required=True)
    sp.add_argument('--auth-state-db',type=Path,required=True)
    sp.add_argument('--auth-binding',action='append',required=True,help='KEY_ID:PEER_ID:SECRET_FILE; secret value is never a CLI argument')
    sp.add_argument('--stream-id',required=True)
    sp.add_argument('--egress-capacity',type=int,default=128)
    sp.add_argument('--ingress-capacity',type=int,default=256)
    sp.add_argument('--max-clock-skew-ms',type=int,default=30000)
    st=sub.add_parser('status'); st.add_argument('--state-db',type=Path,required=True)
    args=ap.parse_args()
    if args.command=='status':
        print(json.dumps(read_state(args.state_db),sort_keys=True)); return 0
    joined=set(args.joined_peer_id)
    bindings={}
    secret_buffers=[]
    for spec in args.auth_binding:
        key_id,peer_id,path=_parse_auth_binding(spec)
        secret=_read_secret_file(path); secret_buffers.append(secret)
        binding=AuthBinding(key_id=key_id,peer_id=peer_id,secret=secret)
        if key_id in bindings: raise ValueError('duplicate auth key id')
        bindings[key_id]=binding
    if {b.peer_id for b in bindings.values()}-joined:
        raise ValueError('auth binding peer must be explicitly joined')
    q=DurableEnvelopeQueue(args.peer_id,joined_peer_ids=joined,state_db=args.state_db,stream_id=args.stream_id,egress_capacity=args.egress_capacity,ingress_capacity=args.ingress_capacity)
    authenticator=RequestAuthenticator(bindings,nonce_store=PersistentNonceStore(args.auth_state_db),joined_peer_ids=joined,max_clock_skew_ms=args.max_clock_skew_ms)
    metrics=TransportMetrics()
    server=ThreadingHTTPServer((args.bind,args.port),AuthenticatedEnvelopeTransportHandler)
    server.envelope_transport_service=EnvelopeTransportService(q)
    server.request_authenticator=authenticator
    server.transport_metrics=metrics
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close(); authenticator.close(); q.close()
        for i in range(len(secret_buffers)): secret_buffers[i]=b''
    return 0


if __name__=='__main__': raise SystemExit(main())
