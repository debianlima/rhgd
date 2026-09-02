"""Bounded, payload-free observability for RHGD envelope transport."""
from __future__ import annotations

import threading
import time
from typing import Callable

OBS_SCHEMA_VERSION = "rhgd-transport-observability/1"


def _clock_ms() -> int:
    return time.time_ns() // 1_000_000


class TransportMetrics:
    def __init__(self, *, clock_ms: Callable[[], int] = _clock_ms) -> None:
        self.clock_ms = clock_ms
        self._lock = threading.Lock()
        self._counters = {
            "requests_total": 0,
            "transport_accepted": 0,
            "transport_duplicate": 0,
            "transport_already_consumed": 0,
            "auth_failure": 0,
            "auth_replay": 0,
            "transport_rejected": 0,
        }
        self._last_activity_ms = 0

    def _inc(self, key: str) -> None:
        with self._lock:
            self._counters[key] += 1
            self._last_activity_ms = int(self.clock_ms())

    def record_request(self) -> None:
        self._inc("requests_total")

    def record_transport_status(self, status: str) -> None:
        mapping = {
            "ACCEPTED": "transport_accepted",
            "DUPLICATE": "transport_duplicate",
            "ALREADY_CONSUMED": "transport_already_consumed",
        }
        self._inc(mapping.get(status, "transport_rejected"))

    def record_auth_failure(self, reason: str) -> None:
        self._inc("auth_replay" if reason == "replay" else "auth_failure")

    def snapshot(self, queue: object | None) -> dict:
        with self._lock:
            counters = dict(self._counters)
            last_activity = self._last_activity_ms
        egress = ingress = 0
        if queue is not None:
            state = queue.snapshot_state()
            egress = len(state.get("egress", []))
            ingress = len(state.get("ingress", []))
        return {
            "schema_version": OBS_SCHEMA_VERSION,
            "observed_at_ms": int(self.clock_ms()),
            "last_activity_ms": last_activity,
            "counters": counters,
            "queue_depth": {"egress": egress, "ingress": ingress},
            "authority": {
                "queue": "envelope_transport_only",
                "scheduler": False,
                "lease_grant": False,
                "admission": False,
            },
        }
