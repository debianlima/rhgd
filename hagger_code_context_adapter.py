"""RHGD read-only adapter for PGH Hagger/Code-Graph-RAG code context.

RHGD materializes and transports context only. It does not schedule work, mint
leases, assign workers, mutate source, or inherit mutating provider tools.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlparse
import json
import os
import re
import subprocess

SCHEMA_VERSION = "rhgd-hagger-code-context/1"
ALLOWED_OPERATIONS = frozenset(
    {
        "summary",
        "resolve",
        "definition",
        "callers",
        "callees",
        "importers",
        "implementors",
        "overrides",
        "tests-reaching",
    }
)
FEDERATION_AUTHORITY = {
    "effect": "NONE",
    "scheduler": False,
    "lease_grant": False,
    "assignment": False,
    "admission": False,
    "source_authority": "git",
    "mutable_tools": "disabled",
}
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_sha(name: str, value: object, pattern: re.Pattern[str]) -> str:
    text = _require_text(name, value).lower()
    if not pattern.fullmatch(text):
        raise ValueError(f"{name} has invalid digest format")
    return text


def validate_code_context_ref(value: Mapping[str, object]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("code_context_ref must be an object")
    ref = dict(value)
    for key in (
        "repo_ref",
        "commit_sha",
        "provider",
        "alias",
        "provider_version",
        "provider_commit",
        "index_ref",
        "manifest_sha256",
        "source_authority",
        "mutable_tools",
    ):
        _require_text(key, ref.get(key))
    ref["commit_sha"] = _require_sha("commit_sha", ref["commit_sha"], _SHA40)
    ref["provider_commit"] = _require_sha(
        "provider_commit", ref["provider_commit"], _SHA40
    )
    ref["manifest_sha256"] = _require_sha(
        "manifest_sha256", ref["manifest_sha256"], _SHA256
    )
    if ref["provider"] != "code-graph-rag" or ref["alias"] != "hagger":
        raise ValueError("unsupported code-context provider")
    if ref["source_authority"] != "git":
        raise ValueError("source authority must remain git")
    if ref["mutable_tools"] != "disabled":
        raise PermissionError("mutable Hagger tools must remain disabled")
    operations = ref.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("operations must be a non-empty list")
    if any(not isinstance(x, str) or x not in ALLOWED_OPERATIONS for x in operations):
        raise PermissionError("code_context_ref grants a non-read-only operation")
    ref["operations"] = list(dict.fromkeys(operations))
    symbols = ref.get("required_symbols", [])
    if not isinstance(symbols, list) or any(
        not isinstance(x, str) or not x.strip() for x in symbols
    ):
        raise ValueError("required_symbols must be a list of non-empty strings")
    ref["required_symbols"] = list(dict.fromkeys(symbols))
    return ref


def _file_uri_path(index_ref: str) -> Path:
    parsed = urlparse(index_ref)
    if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
        raise ValueError("RHGD Hagger adapter accepts only local file:// index_ref")
    raw = unquote(parsed.path)
    if os.name == "nt" and re.match(r"^/[A-Za-z]:/", raw):
        raw = raw[1:]
    return Path(raw)


@dataclass(frozen=True)
class HaggerRuntime:
    provider_python: Path
    query_adapter: Path
    provider_root: Path
    index_root: Path
    timeout_seconds: float = 45.0
    max_output_bytes: int = 1024 * 1024


class HaggerCodeContextAdapter:
    def __init__(self, runtime: HaggerRuntime) -> None:
        self.runtime = runtime

    def _index_dir(self, ref: Mapping[str, object]) -> Path:
        path = _file_uri_path(str(ref["index_ref"])).resolve()
        root = self.runtime.index_root.resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise PermissionError("index_ref is outside the configured Hagger index root") from exc
        if not path.is_dir():
            raise FileNotFoundError("Hagger index directory is unavailable")
        return path

    def query(
        self,
        code_context_ref: Mapping[str, object],
        operation: str,
        *,
        symbol: str | None = None,
        source_root: str | Path | None = None,
        limit: int = 50,
        definition_context: int = 2,
        tests_max_depth: int = 8,
    ) -> dict[str, Any]:
        ref = validate_code_context_ref(code_context_ref)
        if operation not in ALLOWED_OPERATIONS:
            raise PermissionError("operation is not in the PGH Hagger read-only allowlist")
        if operation not in ref["operations"]:
            raise PermissionError("operation was not granted by code_context_ref")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("limit must be an integer from 1 to 50")
        if operation != "summary":
            symbol = _require_text("symbol", symbol)
            required = ref["required_symbols"]
            if required and symbol not in required:
                raise PermissionError("symbol was not granted by code_context_ref")
        elif symbol is not None:
            raise ValueError("summary does not accept a symbol")

        index_dir = self._index_dir(ref)
        for name, path in (
            ("provider_python", self.runtime.provider_python),
            ("query_adapter", self.runtime.query_adapter),
            ("provider_root", self.runtime.provider_root),
        ):
            if not Path(path).exists():
                raise FileNotFoundError(f"{name} is unavailable")

        cmd = [
            str(self.runtime.provider_python),
            str(self.runtime.query_adapter),
            "--index-dir",
            str(index_dir),
            "--expected-commit",
            ref["commit_sha"],
            "--limit",
            str(limit),
        ]
        if source_root is not None:
            cmd.extend(["--source-root", str(Path(source_root).resolve())])
        cmd.append(operation)
        if symbol is not None:
            cmd.append(symbol)
        if operation == "definition":
            if not 0 <= definition_context <= 20:
                raise ValueError("definition_context must be from 0 to 20")
            cmd.extend(["--context", str(definition_context)])
        if operation == "tests-reaching":
            if not 1 <= tests_max_depth <= 16:
                raise ValueError("tests_max_depth must be from 1 to 16")
            cmd.extend(["--max-depth", str(tests_max_depth)])

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.runtime.provider_root) + os.pathsep + env.get(
            "PYTHONPATH", ""
        )
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["GIT_TERMINAL_PROMPT"] = "0"
        completed = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.runtime.timeout_seconds,
            check=False,
            shell=False,
            env=env,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Hagger query failed with rc={completed.returncode}")
        if len(completed.stdout.encode("utf-8")) > self.runtime.max_output_bytes:
            raise ValueError("Hagger query output exceeded the RHGD context bound")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("Hagger query did not return JSON") from exc
        return self._materialize(ref, operation, symbol, payload)

    @staticmethod
    def _materialize(
        ref: Mapping[str, object],
        operation: str,
        symbol: str | None,
        payload: Mapping[str, object],
    ) -> dict[str, Any]:
        if not isinstance(payload, Mapping) or payload.get("ok") is not True:
            raise ValueError("Hagger query payload is not successful")
        if payload.get("operation") != operation:
            raise ValueError("Hagger query operation mismatch")
        provenance = payload.get("provenance")
        if not isinstance(provenance, Mapping):
            raise ValueError("Hagger query provenance is absent")
        expected = {
            "repo_ref": ref["repo_ref"],
            "source_commit": ref["commit_sha"],
            "provider": ref["provider"],
            "provider_version": ref["provider_version"],
            "provider_commit": ref["provider_commit"],
            "manifest_sha256": ref["manifest_sha256"],
        }
        for key, value in expected.items():
            if provenance.get(key) != value:
                raise ValueError(f"Hagger query provenance mismatch: {key}")
        if provenance.get("source_dirty") is not False:
            raise ValueError("Hagger query source must be clean")
        if "result" not in payload:
            raise ValueError("Hagger query result is absent")
        query = {"operation": operation}
        if symbol is not None:
            query["symbol"] = symbol
        return {
            "schema_version": SCHEMA_VERSION,
            "code_context_ref": dict(ref),
            "query": query,
            "provenance": dict(provenance),
            "result": payload["result"],
            "authority": dict(FEDERATION_AUTHORITY),
        }


def attach_hagger_context(
    context_envelope: Mapping[str, object], materialized: Mapping[str, object]
) -> dict[str, Any]:
    if not isinstance(context_envelope, Mapping):
        raise ValueError("context_envelope must be an object")
    schema = context_envelope.get("schema_version")
    if not isinstance(schema, str) or not schema.startswith("pgh.context-envelope/"):
        raise ValueError("context_envelope schema is not PGH ContextEnvelope")
    if materialized.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("materialized Hagger context schema mismatch")
    if materialized.get("authority") != FEDERATION_AUTHORITY:
        raise ValueError("Hagger federation authority boundary violated")
    out = dict(context_envelope)
    out["code_context_ref"] = dict(materialized["code_context_ref"])
    out["code_context"] = dict(materialized)
    return out
