import json
import tempfile
import time
import unittest
from pathlib import Path

from application_auth import (
    AuthBinding,
    AuthError,
    PersistentNonceStore,
    ReplayError,
    RequestAuthenticator,
    build_auth_headers,
)
from context_envelope_transport import DurableEnvelopeQueue
from transport_observability import TransportMetrics


class TestApplicationAuth(unittest.TestCase):
    def setUp(self):
        self.secret=b'u14-test-secret-only-in-memory'
        self.binding=AuthBinding(key_id='key-a',peer_id='peer-a',secret=self.secret)

    def auth(self, db, now=1_700_000_000_000):
        return RequestAuthenticator(
            {'key-a':self.binding},
            nonce_store=PersistentNonceStore(db),
            joined_peer_ids={'peer-a'},
            clock_ms=lambda:now,
            max_clock_skew_ms=5000,
        )

    def test_valid_signature_and_nonce_record(self):
        with tempfile.TemporaryDirectory() as td:
            now=1_700_000_000_000; body=b'{"x":1}'
            headers=build_auth_headers(self.binding,'POST','/rhgd/envelope',body,timestamp_ms=now,nonce='nonce-0123456789')
            a=self.auth(Path(td)/'auth.sqlite3',now)
            ident=a.verify('POST','/rhgd/envelope',body,headers)
            self.assertEqual((ident.key_id,ident.peer_id),('key-a','peer-a'))
            a.close()

    def test_tamper_wrong_key_peer_path_method_timestamp_and_replay_rejected(self):
        mutations=['body','signature','key','peer','path','method','stale','future']
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                now=1_700_000_000_000; body=b'{"x":1}'; method='POST'; path='/rhgd/envelope'
                ts=now
                if mutation=='stale': ts=now-5001
                if mutation=='future': ts=now+5001
                headers=build_auth_headers(self.binding,method,path,body,timestamp_ms=ts,nonce='nonce-0123456789')
                b=body; m=method; p=path
                if mutation=='body': b=b'{"x":2}'
                elif mutation=='signature': headers['X-RHGD-Signature']='0'*64
                elif mutation=='key': headers['X-RHGD-Key-Id']='unknown'
                elif mutation=='peer': headers['X-RHGD-Peer-Id']='peer-x'
                elif mutation=='path': p='/rhgd/other'
                elif mutation=='method': m='GET'
                a=self.auth(Path(td)/'auth.sqlite3',now)
                with self.assertRaises(AuthError): a.verify(m,p,b,headers)
                a.close()
        with tempfile.TemporaryDirectory() as td:
            now=1_700_000_000_000; body=b'{}'; db=Path(td)/'auth.sqlite3'
            headers=build_auth_headers(self.binding,'POST','/rhgd/envelope',body,timestamp_ms=now,nonce='nonce-0123456789')
            a=self.auth(db,now); a.verify('POST','/rhgd/envelope',body,headers); a.close()
            a=self.auth(db,now)
            with self.assertRaises(ReplayError): a.verify('POST','/rhgd/envelope',body,headers)
            a.close()

    def test_secret_not_persisted_and_multiple_keys_supported(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'auth.sqlite3'; now=1_700_000_000_000
            b2=AuthBinding(key_id='key-b',peer_id='peer-b',secret=b'other-memory-secret')
            store=PersistentNonceStore(db)
            a=RequestAuthenticator({'key-a':self.binding,'key-b':b2},nonce_store=store,joined_peer_ids={'peer-a','peer-b'},clock_ms=lambda:now)
            h=build_auth_headers(b2,'POST','/rhgd/envelope',b'{}',timestamp_ms=now,nonce='nonce-b-0123456789')
            self.assertEqual(a.verify('POST','/rhgd/envelope',b'{}',h).peer_id,'peer-b'); a.close()
            raw=db.read_bytes()
            self.assertNotIn(self.secret,raw); self.assertNotIn(b'other-memory-secret',raw)


class TestTransportMetrics(unittest.TestCase):
    def test_snapshot_counters_depth_and_no_payload_or_secret(self):
        with tempfile.TemporaryDirectory() as td:
            q=DurableEnvelopeQueue('a',joined_peer_ids={'b'},state_db=Path(td)/'q.sqlite3',stream_id='s',egress_capacity=2,ingress_capacity=3)
            q.put_outbound({'schema_version':'pgh.context-envelope/0.1','private':'must-not-leak'},work_id='w',model_ref='m',destination_peer='b',correlation_id='c',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
            m=TransportMetrics(clock_ms=lambda:1_700_000_000_000)
            m.record_transport_status('ACCEPTED'); m.record_auth_failure('bad_signature')
            snap=m.snapshot(q)
            self.assertEqual(snap['counters']['transport_accepted'],1)
            self.assertEqual(snap['counters']['auth_failure'],1)
            self.assertEqual(snap['queue_depth'],{'egress':1,'ingress':0})
            text=json.dumps(snap,sort_keys=True)
            self.assertNotIn('must-not-leak',text); self.assertNotIn('secret',text.lower())
            q.close()

    def test_duplicate_consumed_and_replay_counters(self):
        m=TransportMetrics(clock_ms=lambda:1)
        m.record_transport_status('DUPLICATE'); m.record_transport_status('ALREADY_CONSUMED'); m.record_auth_failure('replay')
        snap=m.snapshot(None)
        self.assertEqual(snap['counters']['transport_duplicate'],1)
        self.assertEqual(snap['counters']['transport_already_consumed'],1)
        self.assertEqual(snap['counters']['auth_replay'],1)


if __name__=='__main__': unittest.main()
