import threading
import unittest
from http.server import ThreadingHTTPServer

from context_envelope_transport import (
    AsymmetricEnvelopeQueue,
    EnvelopeTransportRequestHandler,
    EnvelopeTransportService,
    send_next_outbound,
)


def context_payload(tag='ctx'):
    return {
        'schema_version': 'pgh.context-envelope/0.1',
        'context_ref': f'pgh://context/{tag}',
        'context_tokens': 2048,
        'privacy_level': 1,
        'required_capabilities': ['reasoning'],
        'expansion_policy': 'selected-adjacent',
    }


class TestContextEnvelopeTransport(unittest.TestCase):
    def test_asymmetric_egress_order_and_ack_remove(self):
        q=AsymmetricEnvelopeQueue('peer-a',joined_peer_ids={'peer-b'},egress_capacity=2,ingress_capacity=5,stream_id='boot-a')
        a=q.put_outbound(context_payload('a'),work_id='w1',model_ref='model-b',destination_peer='peer-b',correlation_id='c1',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
        b=q.put_outbound(context_payload('b'),work_id='w2',model_ref='model-b',destination_peer='peer-b',correlation_id='c2',authorization_ref='pgh://auth/2',pgd_execution_ref='pgd://execution/2')
        self.assertEqual((a['sequence'],b['sequence']),(1,2))
        self.assertEqual(q.get_outbound('peer-b')['envelope_id'],a['envelope_id'])
        with self.assertRaises(ValueError): q.remove_outbound(b['envelope_id'])
        q.remove_outbound(a['envelope_id'])
        self.assertEqual(q.get_outbound('peer-b')['envelope_id'],b['envelope_id'])
        q.remove_outbound(b['envelope_id'])
        self.assertIsNone(q.get_outbound('peer-b'))
        self.assertEqual(q.capacities(),{'egress':2,'ingress':5})

    def test_ingress_buffers_out_of_order_and_rejects_conflicting_replay(self):
        sender=AsymmetricEnvelopeQueue('peer-a',joined_peer_ids={'peer-b'},stream_id='boot-a')
        recv=AsymmetricEnvelopeQueue('peer-b',joined_peer_ids={'peer-a'},stream_id='boot-b')
        one=sender.put_outbound(context_payload('1'),work_id='w1',model_ref='model-b',destination_peer='peer-b',correlation_id='c1',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
        two=sender.put_outbound(context_payload('2'),work_id='w2',model_ref='model-b',destination_peer='peer-b',correlation_id='c2',authorization_ref='pgh://auth/2',pgd_execution_ref='pgd://execution/2')
        recv.put_inbound(two)
        self.assertIsNone(recv.get_inbound('peer-a'))
        recv.put_inbound(one)
        self.assertEqual(recv.get_inbound('peer-a')['sequence'],1)
        recv.remove_inbound(one['envelope_id'])
        self.assertEqual(recv.get_inbound('peer-a')['sequence'],2)
        duplicate=recv.put_inbound(two)
        self.assertFalse(duplicate['inserted'])
        conflict=dict(two); conflict['envelope_id']='different-id'
        with self.assertRaises(ValueError): recv.put_inbound(conflict)

    def test_explicit_join_and_authority_boundary(self):
        q=AsymmetricEnvelopeQueue('peer-a',joined_peer_ids={'peer-b'},stream_id='boot-a')
        with self.assertRaises(PermissionError):
            q.put_outbound(context_payload(),work_id='w',model_ref='m',destination_peer='peer-x',correlation_id='c',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
        frame=q.put_outbound(context_payload(),work_id='w',model_ref='m',destination_peer='peer-b',correlation_id='c',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
        self.assertEqual(frame['transport_authority'],{'queue':'envelope_transport_only','scheduler':False,'lease_grant':False,'admission':False})
        self.assertFalse(any(hasattr(q,x) for x in ('scheduler','lease','admission','execution_queue','runtime_state')))

    def test_http_send_removes_egress_only_after_remote_put_ack(self):
        qa=AsymmetricEnvelopeQueue('peer-a',joined_peer_ids={'peer-b'},stream_id='boot-a')
        qb=AsymmetricEnvelopeQueue('peer-b',joined_peer_ids={'peer-a'},stream_id='boot-b')
        svc=EnvelopeTransportService(qb)
        server=ThreadingHTTPServer(('127.0.0.1',0),EnvelopeTransportRequestHandler)
        server.envelope_transport_service=svc
        t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
        try:
            frame=qa.put_outbound(context_payload(),work_id='w1',model_ref='model-b',destination_peer='peer-b',correlation_id='c1',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
            ack=send_next_outbound(qa,'peer-b',f'http://127.0.0.1:{server.server_port}/rhgd/envelope',timeout=2.0)
            self.assertEqual(ack['envelope_id'],frame['envelope_id'])
            self.assertIsNone(qa.get_outbound('peer-b'))
            received=qb.get_inbound('peer-a')
            self.assertEqual(received['work_id'],'w1')
            self.assertEqual(received['model_ref'],'model-b')
            qb.remove_inbound(received['envelope_id'])
            self.assertIsNone(qb.get_inbound('peer-a'))
        finally:
            server.shutdown(); server.server_close(); t.join(timeout=2)

    def test_failed_send_keeps_envelope_for_retry(self):
        q=AsymmetricEnvelopeQueue('peer-a',joined_peer_ids={'peer-b'},stream_id='boot-a')
        frame=q.put_outbound(context_payload(),work_id='w1',model_ref='model-b',destination_peer='peer-b',correlation_id='c1',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
        with self.assertRaises(Exception):
            send_next_outbound(q,'peer-b','http://127.0.0.1:9/rhgd/envelope',timeout=0.2)
        self.assertEqual(q.get_outbound('peer-b')['envelope_id'],frame['envelope_id'])


if __name__=='__main__':
    unittest.main()
