"""RHGD asymmetric transport queues for PGH ContextEnvelope.

The queue owned here is a *transport* queue: it orders and buffers envelopes
between explicitly joined peers/models. PGD remains the sole owner of the
execution queue, admission, assignment decision, leases, scheduler and runtime.
An outbound envelope therefore requires a pre-existing ``pgd_assignment_ref``.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections import defaultdict
from http.server import BaseHTTPRequestHandler
from typing import Callable, Mapping
from urllib.request import Request, urlopen

SCHEMA_VERSION = "rhgd-context-envelope-transport/1"
ACK_SCHEMA_VERSION = "rhgd-context-envelope-ack/1"
TRANSPORT_PATH = "/rhgd/envelope"
TRANSPORT_AUTHORITY = {
    "queue": "envelope_transport_only",
    "scheduler": False,
    "lease_grant": False,
    "admission": False,
}


def _clock_ms() -> int:
    return time.time_ns() // 1_000_000


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def validate_transport_frame(frame: Mapping[str, object]) -> dict:
    if not isinstance(frame, Mapping):
        raise ValueError("transport frame must be an object")
    x = dict(frame)
    if x.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported transport frame schema")
    for key in (
        "envelope_id", "correlation_id", "work_id", "model_ref", "source_peer",
        "destination_peer", "stream_id", "authorization_ref", "pgd_assignment_ref",
    ):
        _require_text(key, x.get(key))
    sequence = x.get("sequence")
    issued = x.get("issued_at_ms")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    if not isinstance(issued, int) or isinstance(issued, bool) or issued < 0:
        raise ValueError("issued_at_ms must be a non-negative integer")
    envelope = x.get("context_envelope")
    if not isinstance(envelope, Mapping):
        raise ValueError("context_envelope must be an object")
    if not isinstance(envelope.get("schema_version"), str) or not envelope["schema_version"].startswith("pgh.context-envelope/"):
        raise ValueError("context_envelope schema is not PGH ContextEnvelope")
    if x.get("transport_authority") != TRANSPORT_AUTHORITY:
        raise ValueError("transport authority boundary violated")
    return x


class AsymmetricEnvelopeQueue:
    """Independent egress/ingress lanes with deterministic per-peer ordering.

    ``put_outbound`` allocates a monotonically increasing transport sequence.
    ``get_outbound`` peeks the head. ``remove_outbound`` is allowed only for the
    head after an ACK. Inbound frames may arrive reordered; they are buffered,
    but ``get_inbound`` exposes only the next expected sequence. This is not a
    PGD execution queue and contains no claim/lease/scheduler state.
    """

    def __init__(
        self,
        local_peer_id: str,
        *,
        joined_peer_ids: set[str],
        egress_capacity: int = 128,
        ingress_capacity: int = 256,
        stream_id: str | None = None,
        clock_ms: Callable[[], int] = _clock_ms,
    ) -> None:
        self.local_peer_id = _require_text("local_peer_id", local_peer_id)
        self.joined_peer_ids = frozenset(_require_text("joined_peer_id", x) for x in joined_peer_ids)
        if egress_capacity < 1 or ingress_capacity < 1:
            raise ValueError("queue capacities must be positive")
        self.egress_capacity = int(egress_capacity)
        self.ingress_capacity = int(ingress_capacity)
        self.stream_id = stream_id or str(uuid.uuid4())
        self.clock_ms = clock_ms
        self._egress: dict[str, list[dict]] = defaultdict(list)
        self._egress_next: dict[str, int] = defaultdict(lambda: 1)
        self._egress_index: dict[str, str] = {}
        self._ingress: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
        self._ingress_expected: dict[tuple[str, str], int] = defaultdict(lambda: 1)
        self._ingress_stream_for_peer: dict[str, str] = {}
        self._ingress_index: dict[str, tuple[str, str, int]] = {}

    def capacities(self) -> dict[str, int]:
        return {"egress": self.egress_capacity, "ingress": self.ingress_capacity}

    def _total_egress(self) -> int:
        return sum(len(x) for x in self._egress.values())

    def _total_ingress(self) -> int:
        return sum(len(x) for x in self._ingress.values())

    def put_outbound(
        self,
        context_envelope: Mapping[str, object],
        *,
        work_id: str,
        model_ref: str,
        destination_peer: str,
        correlation_id: str,
        authorization_ref: str,
        pgd_assignment_ref: str,
    ) -> dict:
        destination_peer = _require_text("destination_peer", destination_peer)
        if destination_peer not in self.joined_peer_ids:
            raise PermissionError("destination peer is not explicitly joined")
        if self._total_egress() >= self.egress_capacity:
            raise BufferError("egress envelope queue is full")
        _require_text("work_id", work_id)
        _require_text("model_ref", model_ref)
        _require_text("correlation_id", correlation_id)
        _require_text("authorization_ref", authorization_ref)
        _require_text("pgd_assignment_ref", pgd_assignment_ref)
        if not isinstance(context_envelope, Mapping):
            raise ValueError("context_envelope must be an object")
        schema = context_envelope.get("schema_version")
        if not isinstance(schema, str) or not schema.startswith("pgh.context-envelope/"):
            raise ValueError("context_envelope schema is not PGH ContextEnvelope")
        sequence = self._egress_next[destination_peer]
        self._egress_next[destination_peer] += 1
        issued = int(self.clock_ms())
        identity = "\x1f".join((self.local_peer_id, destination_peer, self.stream_id, str(sequence), work_id, correlation_id))
        envelope_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        frame = {
            "schema_version": SCHEMA_VERSION,
            "envelope_id": envelope_id,
            "correlation_id": correlation_id,
            "work_id": work_id,
            "model_ref": model_ref,
            "source_peer": self.local_peer_id,
            "destination_peer": destination_peer,
            "stream_id": self.stream_id,
            "sequence": sequence,
            "issued_at_ms": issued,
            "authorization_ref": authorization_ref,
            "pgd_assignment_ref": pgd_assignment_ref,
            "context_envelope": dict(context_envelope),
            "transport_authority": dict(TRANSPORT_AUTHORITY),
        }
        validate_transport_frame(frame)
        self._egress[destination_peer].append(frame)
        self._egress_index[envelope_id] = destination_peer
        return dict(frame)

    def get_outbound(self, destination_peer: str) -> dict | None:
        lane = self._egress.get(destination_peer) or []
        return dict(lane[0]) if lane else None

    def remove_outbound(self, envelope_id: str) -> dict:
        destination = self._egress_index.get(envelope_id)
        if destination is None:
            raise KeyError("unknown outbound envelope")
        lane = self._egress[destination]
        if not lane or lane[0]["envelope_id"] != envelope_id:
            raise ValueError("cannot remove outbound envelope out of order")
        frame = lane.pop(0)
        del self._egress_index[envelope_id]
        return dict(frame)

    def put_inbound(self, frame: Mapping[str, object]) -> dict:
        x = validate_transport_frame(frame)
        if x["destination_peer"] != self.local_peer_id:
            raise PermissionError("envelope destination is not this peer")
        source = x["source_peer"]
        if source not in self.joined_peer_ids:
            raise PermissionError("source peer is not explicitly joined")
        stream = x["stream_id"]
        active_stream = self._ingress_stream_for_peer.get(source)
        if active_stream is None:
            self._ingress_stream_for_peer[source] = stream
        elif active_stream != stream:
            old_key = (source, active_stream)
            if self._ingress.get(old_key):
                raise ValueError("cannot switch peer stream while prior stream has pending envelopes")
            self._ingress_stream_for_peer[source] = stream
        key = (source, stream)
        seq = x["sequence"]
        expected = self._ingress_expected[key]
        if seq < expected:
            return {"inserted": False, "status": "ALREADY_CONSUMED", "envelope_id": x["envelope_id"], "sequence": seq}
        existing = self._ingress[key].get(seq)
        if existing is not None:
            if existing["envelope_id"] == x["envelope_id"] and existing == x:
                return {"inserted": False, "status": "DUPLICATE", "envelope_id": x["envelope_id"], "sequence": seq}
            raise ValueError("conflicting envelope for transport sequence")
        if self._total_ingress() >= self.ingress_capacity:
            raise BufferError("ingress envelope queue is full")
        self._ingress[key][seq] = x
        self._ingress_index[x["envelope_id"]] = (source, stream, seq)
        return {"inserted": True, "status": "ACCEPTED", "envelope_id": x["envelope_id"], "sequence": seq}

    def get_inbound(self, source_peer: str) -> dict | None:
        stream = self._ingress_stream_for_peer.get(source_peer)
        if stream is None:
            return None
        key = (source_peer, stream)
        expected = self._ingress_expected[key]
        frame = self._ingress[key].get(expected)
        return dict(frame) if frame is not None else None

    def remove_inbound(self, envelope_id: str) -> dict:
        loc = self._ingress_index.get(envelope_id)
        if loc is None:
            raise KeyError("unknown inbound envelope")
        source, stream, seq = loc
        key = (source, stream)
        if seq != self._ingress_expected[key]:
            raise ValueError("cannot remove inbound envelope out of order")
        frame = self._ingress[key].pop(seq)
        del self._ingress_index[envelope_id]
        self._ingress_expected[key] += 1
        return dict(frame)


class EnvelopeTransportService:
    def __init__(self, queue: AsymmetricEnvelopeQueue) -> None:
        self.queue = queue

    def receive(self, frame: Mapping[str, object]) -> dict:
        result = self.queue.put_inbound(frame)
        return {
            "schema_version": ACK_SCHEMA_VERSION,
            "envelope_id": result["envelope_id"],
            "sequence": result["sequence"],
            "status": result["status"],
        }


class EnvelopeTransportRequestHandler(BaseHTTPRequestHandler):
    server_version = "RHGDEnvelopeTransport/1"

    def do_POST(self) -> None:  # noqa: N802
        if self.path != TRANSPORT_PATH:
            self.send_error(404)
            return
        service = getattr(self.server, "envelope_transport_service", None)
        if not isinstance(service, EnvelopeTransportService):
            self.send_error(503)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 4 * 1024 * 1024:
                raise ValueError("invalid body length")
            frame = json.loads(self.rfile.read(length).decode("utf-8"))
            ack = service.receive(frame)
            body = json.dumps(ack, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(202)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, PermissionError, BufferError, json.JSONDecodeError) as exc:
            body = json.dumps({"error": type(exc).__name__, "detail": str(exc)}, separators=(",", ":")).encode("utf-8")
            self.send_response(409 if isinstance(exc, (BufferError, ValueError)) else 403)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def send_next_outbound(
    queue: AsymmetricEnvelopeQueue,
    destination_peer: str,
    url: str,
    *,
    timeout: float = 2.0,
) -> dict | None:
    frame = queue.get_outbound(destination_peer)
    if frame is None:
        return None
    payload = json.dumps(frame, sort_keys=True, separators=(",", ":")).encode("utf-8")
    request = Request(url, data=payload, method="POST", headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 202:
            raise ValueError(f"envelope transport returned HTTP {response.status}")
        ack = json.loads(response.read().decode("utf-8"))
    if ack.get("schema_version") != ACK_SCHEMA_VERSION:
        raise ValueError("invalid envelope ACK schema")
    if ack.get("envelope_id") != frame["envelope_id"] or ack.get("sequence") != frame["sequence"]:
        raise ValueError("ACK does not match outbound envelope")
    if ack.get("status") not in {"ACCEPTED", "DUPLICATE", "ALREADY_CONSUMED"}:
        raise ValueError("receiver did not accept envelope")
    queue.remove_outbound(frame["envelope_id"])
    return ack
