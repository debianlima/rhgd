import tempfile
import unittest
from pathlib import Path

from context_envelope_transport import DurableEnvelopeQueue, send_next_outbound


def ctx(tag='ctx'):
    return {
        'schema_version':'pgh.context-envelope/0.1',
        'context_ref':f'pgh://u13/{tag}',
        'context_tokens':2048,
        'privacy_level':1,
        'required_capabilities':['reasoning'],
        'expansion_policy':'selected-adjacent',
    }


def make_queue(db: Path, local='peer-a', joined=None, stream='boot-a', egress=3, ingress=5):
    return DurableEnvelopeQueue(
        local,
        joined_peer_ids=set(joined or {'peer-b'}),
        state_db=db,
        stream_id=stream,
        egress_capacity=egress,
        ingress_capacity=ingress,
    )


class TestPersistentEnvelopeTransport(unittest.TestCase):
    def test_outbound_survives_restart_and_sequence_continues(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'q.sqlite3'
            q=make_queue(db)
            one=q.put_outbound(ctx('1'),work_id='w1',model_ref='m',destination_peer='peer-b',correlation_id='c1',authorization_ref='pgh://auth/1',pgd_execution_ref='pgd://execution/1')
            two=q.put_outbound(ctx('2'),work_id='w2',model_ref='m',destination_peer='peer-b',correlation_id='c2',authorization_ref='pgh://auth/2',pgd_execution_ref='pgd://execution/2')
            q.close()
            q=make_queue(db)
            self.assertEqual(q.get_outbound('peer-b')['envelope_id'],one['envelope_id'])
            q.remove_outbound(one['envelope_id'])
            q.close()
            q=make_queue(db)
            self.assertEqual(q.get_outbound('peer-b')['envelope_id'],two['envelope_id'])
            q.remove_outbound(two['envelope_id'])
            three=q.put_outbound(ctx('3'),work_id='w3',model_ref='m',destination_peer='peer-b',correlation_id='c3',authorization_ref='pgh://auth/3',pgd_execution_ref='pgd://execution/3')
            self.assertEqual(three['sequence'],3)
            q.close()

    def test_inbound_and_consumed_replay_survive_restart(self):
        with tempfile.TemporaryDirectory() as td:
            sender_db=Path(td)/'sender.sqlite3'; recv_db=Path(td)/'recv.sqlite3'
            sender=make_queue(sender_db)
            recv=make_queue(recv_db,local='peer-b',joined={'peer-a'},stream='boot-b')
            frame=sender.put_outbound(ctx('x'),work_id='w',model_ref='m',destination_peer='peer-b',correlation_id='c',authorization_ref='pgh://auth/x',pgd_execution_ref='pgd://execution/x')
            recv.put_inbound(frame); recv.close()
            recv=make_queue(recv_db,local='peer-b',joined={'peer-a'},stream='boot-b')
            self.assertEqual(recv.get_inbound('peer-a')['envelope_id'],frame['envelope_id'])
            recv.remove_inbound(frame['envelope_id']); recv.close()
            recv=make_queue(recv_db,local='peer-b',joined={'peer-a'},stream='boot-b')
            replay=recv.put_inbound(frame)
            self.assertEqual(replay['status'],'ALREADY_CONSUMED')
            conflict=dict(frame); conflict['envelope_id']='f'*64
            with self.assertRaises(ValueError): recv.put_inbound(conflict)
            recv.close(); sender.close()

    def test_failed_send_remains_pending_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'q.sqlite3'
            q=make_queue(db)
            frame=q.put_outbound(ctx('retry'),work_id='w',model_ref='m',destination_peer='peer-b',correlation_id='c',authorization_ref='pgh://auth/retry',pgd_execution_ref='pgd://execution/retry')
            with self.assertRaises(Exception):
                send_next_outbound(q,'peer-b','http://127.0.0.1:9/rhgd/envelope',timeout=0.2)
            q.close()
            q=make_queue(db)
            self.assertEqual(q.get_outbound('peer-b')['envelope_id'],frame['envelope_id'])
            q.close()

    def test_persisted_configuration_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'q.sqlite3'
            q=make_queue(db,egress=3,ingress=5); q.close()
            with self.assertRaises(ValueError):
                make_queue(db,egress=9,ingress=5)
            with self.assertRaises(ValueError):
                make_queue(db,joined={'peer-c'})

    def test_snapshot_is_canonical_and_contains_no_execution_authority(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'q.sqlite3'
            q=make_queue(db)
            snap=q.snapshot_state()
            self.assertEqual(snap['schema_version'],'rhgd-durable-envelope-queue-state/1')
            self.assertEqual(snap['authority'],{'queue':'envelope_transport_only','scheduler':False,'lease_grant':False,'admission':False})
            self.assertEqual(snap['joined_peer_ids'],['peer-b'])
            self.assertNotIn('lease',snap)
            self.assertNotIn('assignment',snap)
            q.close()


if __name__=='__main__':
    unittest.main()
