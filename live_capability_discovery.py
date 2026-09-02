"""RHGD live capability discovery over explicitly joined HTTP endpoints.

This module exposes read-only capability observations. It does not schedule,
assign, queue, grant leases, mutate PGD runtime state, or infer capabilities.
"""
from __future__ import annotations

import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Mapping
from urllib.request import Request, urlopen

SCHEMA_VERSION = "rhgd-live-capability/1"
CAPABILITY_PATH = "/rhgd/capability"
READ_ONLY_AUTHORITY = {
    "mode": "read_only_advisory",
    "scheduler": False,
    "lease_grant": False,
    "assignment": False,
}


def _clock_ms() -> int:
    return time.time_ns() // 1_000_000


class CapabilityAnnouncer:
    def __init__(
        self,
        peer_id: str,
        capabilities: Mapping[str, object],
        *,
        ttl_ms: int = 5_000,
        clock_ms: Callable[[], int] = _clock_ms,
        boot_id: str | None = None,
    ) -> None:
        if not peer_id or not isinstance(peer_id, str):
            raise ValueError("peer_id must be a non-empty string")
        if not isinstance(capabilities, Mapping):
            raise TypeError("capabilities must be a mapping")
        if ttl_ms <= 0 or ttl_ms > 60_000:
            raise ValueError("ttl_ms must be in 1..60000")
        self.peer_id = peer_id
        self.capabilities = dict(capabilities)
        self.ttl_ms = int(ttl_ms)
        self.clock_ms = clock_ms
        self.boot_id = boot_id or str(uuid.uuid4())
        self._sequence = 0

    def snapshot(self) -> dict:
        self._sequence += 1
        issued = int(self.clock_ms())
        return {
            "schema_version": SCHEMA_VERSION,
            "peer_id": self.peer_id,
            "boot_id": self.boot_id,
            "sequence": self._sequence,
            "issued_at_ms": issued,
            "expires_at_ms": issued + self.ttl_ms,
            "capabilities": dict(self.capabilities),
            "authority": dict(READ_ONLY_AUTHORITY),
        }


def validate_capability_snapshot(
    snapshot: Mapping[str, object],
    *,
    now_ms: int | None = None,
    max_clock_skew_ms: int = 5_000,
    max_ttl_ms: int = 60_000,
) -> dict:
    if not isinstance(snapshot, Mapping):
        raise ValueError("snapshot must be an object")
    x = dict(snapshot)
    if x.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported capability schema")
    for key in ("peer_id", "boot_id"):
        if not isinstance(x.get(key), str) or not x[key]:
            raise ValueError(f"{key} must be a non-empty string")
    seq = x.get("sequence")
    issued = x.get("issued_at_ms")
    expires = x.get("expires_at_ms")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        raise ValueError("sequence must be a positive integer")
    if not isinstance(issued, int) or isinstance(issued, bool):
        raise ValueError("issued_at_ms must be an integer")
    if not isinstance(expires, int) or isinstance(expires, bool):
        raise ValueError("expires_at_ms must be an integer")
    if expires <= issued or expires - issued > max_ttl_ms:
        raise ValueError("invalid capability TTL")
    now = _clock_ms() if now_ms is None else int(now_ms)
    if issued > now + max_clock_skew_ms:
        raise ValueError("capability issued too far in the future")
    if expires <= now:
        raise ValueError("capability snapshot is stale")
    caps = x.get("capabilities")
    if not isinstance(caps, Mapping):
        raise ValueError("capabilities must be an object")
    authority = x.get("authority")
    if authority != READ_ONLY_AUTHORITY:
        raise ValueError("capability authority boundary is not read-only")
    return x


class CapabilityRegistry:
    """Stores observations only from peer ids explicitly joined by policy."""

    def __init__(self, joined_peer_ids: set[str], *, clock_ms: Callable[[], int] = _clock_ms) -> None:
        self.joined_peer_ids = frozenset(joined_peer_ids)
        self.clock_ms = clock_ms
        self._latest: dict[str, dict] = {}

    def ingest(self, snapshot: Mapping[str, object]) -> dict:
        now = int(self.clock_ms())
        x = validate_capability_snapshot(snapshot, now_ms=now)
        peer_id = x["peer_id"]
        if peer_id not in self.joined_peer_ids:
            raise PermissionError("peer is not explicitly joined")
        previous = self._latest.get(peer_id)
        if previous:
            if x["boot_id"] == previous["boot_id"]:
                if x["sequence"] <= previous["sequence"]:
                    raise ValueError("replayed or regressed capability sequence")
            elif x["issued_at_ms"] < previous["issued_at_ms"]:
                raise ValueError("older peer boot advertisement rejected")
        self._latest[peer_id] = x
        return x

    def active(self) -> dict[str, dict]:
        now = int(self.clock_ms())
        return {
            peer_id: dict(snapshot)
            for peer_id, snapshot in self._latest.items()
            if snapshot["expires_at_ms"] > now
        }


class CapabilityRequestHandler(BaseHTTPRequestHandler):
    server_version = "RHGDLiveCapability/1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        if self.path != CAPABILITY_PATH:
            self.send_error(404)
            return
        announcer = getattr(self.server, "capability_announcer", None)
        if not isinstance(announcer, CapabilityAnnouncer):
            self.send_error(503)
            return
        body = json.dumps(announcer.snapshot(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def fetch_capability(url: str, *, timeout: float = 2.0, now_ms: int | None = None) -> dict:
    req = Request(url, headers={"Accept": "application/json", "Cache-Control": "no-cache"})
    with urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"capability endpoint returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    return validate_capability_snapshot(payload, now_ms=now_ms)


def serve(bind: str, port: int, announcer: CapabilityAnnouncer) -> None:
    server = ThreadingHTTPServer((bind, port), CapabilityRequestHandler)
    server.capability_announcer = announcer
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()


def _main() -> int:
    ap = argparse.ArgumentParser(description="RHGD live capability discovery")
    sub = ap.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("serve")
    sp.add_argument("--bind", required=True)
    sp.add_argument("--port", type=int, required=True)
    sp.add_argument("--peer-id", required=True)
    sp.add_argument("--capabilities-json", required=True)
    sp.add_argument("--ttl-ms", type=int, default=5000)
    sp.add_argument("--boot-id")
    fp = sub.add_parser("fetch")
    fp.add_argument("--url", required=True)
    fp.add_argument("--timeout", type=float, default=2.0)
    args = ap.parse_args()
    if args.command == "serve":
        capabilities = json.loads(args.capabilities_json)
        announcer = CapabilityAnnouncer(args.peer_id, capabilities, ttl_ms=args.ttl_ms, boot_id=args.boot_id)
        serve(args.bind, args.port, announcer)
        return 0
    print(json.dumps(fetch_capability(args.url, timeout=args.timeout), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
