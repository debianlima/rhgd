"""Application-layer authentication for RHGD transport requests.

Secrets are supplied to this module only as bytes at runtime. The persistent
replay store records key ids and SHA-256 nonce digests, never secret material.
"""
from __future__ import annotations

import hashlib
import hmac
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

AUTH_SCHEMA_VERSION = "rhgd-application-auth/1"
REQUIRED_HEADERS = (
    "x-rhgd-key-id",
    "x-rhgd-peer-id",
    "x-rhgd-timestamp-ms",
    "x-rhgd-nonce",
    "x-rhgd-body-sha256",
    "x-rhgd-signature",
)


class AuthError(ValueError):
    pass


class ReplayError(AuthError):
    pass


@dataclass(frozen=True)
class AuthBinding:
    key_id: str
    peer_id: str
    secret: bytes

    def __post_init__(self) -> None:
        if not self.key_id or not self.peer_id:
            raise ValueError("key_id and peer_id must be non-empty")
        if not isinstance(self.secret, bytes) or len(self.secret) < 16:
            raise ValueError("secret must be at least 16 bytes")


@dataclass(frozen=True)
class AuthIdentity:
    key_id: str
    peer_id: str


def _clock_ms() -> int:
    return time.time_ns() // 1_000_000


def _headers_lower(headers: Mapping[str, object]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in headers.items():
        out[str(key).lower()] = str(value)
    return out


def _body_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical_request(
    method: str,
    path: str,
    key_id: str,
    peer_id: str,
    timestamp_ms: int,
    nonce: str,
    body_sha256: str,
) -> bytes:
    return "\n".join(
        (method.upper(), path, key_id, peer_id, str(int(timestamp_ms)), nonce, body_sha256)
    ).encode("utf-8")


def build_auth_headers(
    binding: AuthBinding,
    method: str,
    path: str,
    body: bytes,
    *,
    timestamp_ms: int | None = None,
    nonce: str,
) -> dict[str, str]:
    ts = _clock_ms() if timestamp_ms is None else int(timestamp_ms)
    if not isinstance(nonce, str) or not (12 <= len(nonce) <= 128):
        raise ValueError("nonce length must be 12..128")
    body_hash = _body_sha256(body)
    canonical = canonical_request(method, path, binding.key_id, binding.peer_id, ts, nonce, body_hash)
    signature = hmac.new(binding.secret, canonical, hashlib.sha256).hexdigest()
    return {
        "X-RHGD-Key-Id": binding.key_id,
        "X-RHGD-Peer-Id": binding.peer_id,
        "X-RHGD-Timestamp-Ms": str(ts),
        "X-RHGD-Nonce": nonce,
        "X-RHGD-Body-SHA256": body_hash,
        "X-RHGD-Signature": signature,
    }


class PersistentNonceStore:
    def __init__(self, state_db: str | Path, *, retention_ms: int = 300_000, clock_ms: Callable[[], int] = _clock_ms) -> None:
        if retention_ms < 1:
            raise ValueError("retention_ms must be positive")
        self.state_db = Path(state_db)
        self.state_db.parent.mkdir(parents=True, exist_ok=True)
        self.retention_ms = int(retention_ms)
        self.clock_ms = clock_ms
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(self.state_db), timeout=5.0, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS used_nonce ("
            "key_id TEXT NOT NULL, nonce_sha256 TEXT NOT NULL, expires_at_ms INTEGER NOT NULL, "
            "PRIMARY KEY(key_id, nonce_sha256))"
        )
        self._db.commit()

    def check_and_record(self, key_id: str, nonce: str, *, now_ms: int | None = None) -> None:
        if not key_id or not nonce:
            raise AuthError("key id and nonce required")
        now = int(self.clock_ms()) if now_ms is None else int(now_ms)
        digest = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        expires = now + self.retention_ms
        with self._lock:
            try:
                self._db.execute("BEGIN IMMEDIATE")
                self._db.execute("DELETE FROM used_nonce WHERE expires_at_ms <= ?", (now,))
                self._db.execute(
                    "INSERT INTO used_nonce(key_id,nonce_sha256,expires_at_ms) VALUES(?,?,?)",
                    (key_id, digest, expires),
                )
                self._db.commit()
            except sqlite3.IntegrityError as exc:
                self._db.rollback()
                raise ReplayError("nonce replay rejected") from exc
            except Exception:
                self._db.rollback()
                raise

    def close(self) -> None:
        with self._lock:
            db = getattr(self, "_db", None)
            if db is not None:
                db.execute("PRAGMA wal_checkpoint(FULL)")
                db.close()
                self._db = None


class RequestAuthenticator:
    def __init__(
        self,
        bindings: Mapping[str, AuthBinding],
        *,
        nonce_store: PersistentNonceStore,
        joined_peer_ids: set[str],
        clock_ms: Callable[[], int] = _clock_ms,
        max_clock_skew_ms: int = 30_000,
    ) -> None:
        self.bindings = dict(bindings)
        self.nonce_store = nonce_store
        self.joined_peer_ids = frozenset(joined_peer_ids)
        self.clock_ms = clock_ms
        self.max_clock_skew_ms = int(max_clock_skew_ms)
        if self.max_clock_skew_ms < 0:
            raise ValueError("max_clock_skew_ms must be non-negative")
        for key_id, binding in self.bindings.items():
            if key_id != binding.key_id:
                raise ValueError("binding map key must equal binding.key_id")

    def verify(self, method: str, path: str, body: bytes, headers: Mapping[str, object]) -> AuthIdentity:
        h = _headers_lower(headers)
        missing = [name for name in REQUIRED_HEADERS if not h.get(name)]
        if missing:
            raise AuthError("missing authentication headers")
        key_id = h["x-rhgd-key-id"]
        peer_id = h["x-rhgd-peer-id"]
        binding = self.bindings.get(key_id)
        if binding is None:
            raise AuthError("unknown key id")
        if peer_id != binding.peer_id:
            raise AuthError("peer/key binding mismatch")
        if peer_id not in self.joined_peer_ids:
            raise AuthError("peer is not explicitly joined")
        try:
            timestamp_ms = int(h["x-rhgd-timestamp-ms"])
        except ValueError as exc:
            raise AuthError("timestamp must be an integer") from exc
        now = int(self.clock_ms())
        if abs(timestamp_ms - now) > self.max_clock_skew_ms:
            raise AuthError("request timestamp outside allowed clock window")
        nonce = h["x-rhgd-nonce"]
        if not (12 <= len(nonce) <= 128):
            raise AuthError("nonce length invalid")
        body_hash = _body_sha256(body)
        if not hmac.compare_digest(h["x-rhgd-body-sha256"], body_hash):
            raise AuthError("body hash mismatch")
        canonical = canonical_request(method, path, key_id, peer_id, timestamp_ms, nonce, body_hash)
        expected = hmac.new(binding.secret, canonical, hashlib.sha256).hexdigest()
        signature = h["x-rhgd-signature"]
        if len(signature) != 64 or not hmac.compare_digest(signature, expected):
            raise AuthError("signature mismatch")
        # Record only after all cryptographic/binding checks pass, and do so atomically.
        self.nonce_store.check_and_record(key_id, nonce, now_ms=now)
        return AuthIdentity(key_id=key_id, peer_id=peer_id)

    def close(self) -> None:
        self.nonce_store.close()
