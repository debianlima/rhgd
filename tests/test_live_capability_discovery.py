import json
import threading
import time
import unittest
from http.server import ThreadingHTTPServer

from live_capability_discovery import (
    CapabilityAnnouncer,
    CapabilityRegistry,
    CapabilityRequestHandler,
    fetch_capability,
    validate_capability_snapshot,
)


class TestLiveCapabilityDiscovery(unittest.TestCase):
    def test_announcer_emits_monotonic_sequence_and_fresh_ttl(self):
        now=[1_700_000_000_000]
        a=CapabilityAnnouncer(
            peer_id='peer-a',
            capabilities={'context_tokens':4096,'privacy_level':1,'domains':['code'],'source':'test_declared'},
            ttl_ms=5000,
            clock_ms=lambda: now[0],
            boot_id='boot-a',
        )
        x=a.snapshot(); now[0]+=25; y=a.snapshot()
        self.assertEqual(x['schema_version'],'rhgd-live-capability/1')
        self.assertEqual((x['sequence'],y['sequence']),(1,2))
        self.assertEqual(x['expires_at_ms']-x['issued_at_ms'],5000)
        self.assertEqual(x['authority'],{'mode':'read_only_advisory','scheduler':False,'lease_grant':False,'assignment':False})

    def test_validation_rejects_expired_future_and_authority_claims(self):
        now=1_700_000_000_000
        def snap():
            return CapabilityAnnouncer('peer-a',{'source':'test_declared'},ttl_ms=1000,clock_ms=lambda:now,boot_id='boot-a').snapshot()
        validate_capability_snapshot(snap(),now_ms=now)
        expired=snap(); expired['expires_at_ms']=now-1
        with self.assertRaises(ValueError): validate_capability_snapshot(expired,now_ms=now)
        future=snap(); future['issued_at_ms']=now+5001; future['expires_at_ms']=now+6001
        with self.assertRaises(ValueError): validate_capability_snapshot(future,now_ms=now,max_clock_skew_ms=5000)
        authoritative=snap(); authoritative['authority']['scheduler']=True
        with self.assertRaises(ValueError): validate_capability_snapshot(authoritative,now_ms=now)

    def test_registry_is_explicit_join_and_rejects_replay_or_sequence_regression(self):
        now=[1_700_000_000_000]
        reg=CapabilityRegistry(joined_peer_ids={'peer-a'},clock_ms=lambda:now[0])
        a=CapabilityAnnouncer('peer-a',{'source':'test_declared'},ttl_ms=1000,clock_ms=lambda:now[0],boot_id='boot-a')
        first=a.snapshot(); reg.ingest(first)
        with self.assertRaises(ValueError): reg.ingest(first)
        second=a.snapshot(); reg.ingest(second)
        outsider=CapabilityAnnouncer('peer-b',{'source':'test_declared'},ttl_ms=1000,clock_ms=lambda:now[0],boot_id='boot-b').snapshot()
        with self.assertRaises(PermissionError): reg.ingest(outsider)
        now[0]+=1001
        self.assertEqual(reg.active(),{})

    def test_http_endpoint_returns_live_capability_not_static_snapshot(self):
        announcer=CapabilityAnnouncer('peer-http',{'source':'test_declared','domains':['test']},ttl_ms=3000,boot_id='boot-http')
        server=ThreadingHTTPServer(('127.0.0.1',0),CapabilityRequestHandler)
        server.capability_announcer=announcer
        t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}/rhgd/capability'
            a=fetch_capability(url,timeout=2.0)
            b=fetch_capability(url,timeout=2.0)
            self.assertEqual(a['peer_id'],'peer-http')
            self.assertGreater(b['sequence'],a['sequence'])
            self.assertGreaterEqual(b['issued_at_ms'],a['issued_at_ms'])
        finally:
            server.shutdown(); server.server_close(); t.join(timeout=2)


if __name__=='__main__':
    unittest.main()
