#!/usr/bin/env python3
"""Persistent RHGD ContextEnvelope receiver daemon for EnvelopeTransportQueue."""
from __future__ import annotations

import argparse
import json
import sqlite3
from http.server import ThreadingHTTPServer
from pathlib import Path

from context_envelope_transport import (
    DurableEnvelopeQueue,
    EnvelopeTransportRequestHandler,
    EnvelopeTransportService,
)


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


def main() -> int:
    ap=argparse.ArgumentParser(description='RHGD persistent EnvelopeTransportQueue daemon')
    sub=ap.add_subparsers(dest='command',required=True)
    sp=sub.add_parser('serve')
    sp.add_argument('--bind',required=True)
    sp.add_argument('--port',type=int,required=True)
    sp.add_argument('--peer-id',required=True)
    sp.add_argument('--joined-peer-id',action='append',required=True)
    sp.add_argument('--state-db',type=Path,required=True)
    sp.add_argument('--stream-id',required=True)
    sp.add_argument('--egress-capacity',type=int,default=128)
    sp.add_argument('--ingress-capacity',type=int,default=256)
    st=sub.add_parser('status')
    st.add_argument('--state-db',type=Path,required=True)
    args=ap.parse_args()
    if args.command=='status':
        print(json.dumps(read_state(args.state_db),sort_keys=True))
        return 0
    q=DurableEnvelopeQueue(
        args.peer_id,
        joined_peer_ids=set(args.joined_peer_id),
        state_db=args.state_db,
        stream_id=args.stream_id,
        egress_capacity=args.egress_capacity,
        ingress_capacity=args.ingress_capacity,
    )
    server=ThreadingHTTPServer((args.bind,args.port),EnvelopeTransportRequestHandler)
    server.envelope_transport_service=EnvelopeTransportService(q)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close(); q.close()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
