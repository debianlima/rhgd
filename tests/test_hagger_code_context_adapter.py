from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jsonschema

from context_envelope_transport import AsymmetricEnvelopeQueue, TRANSPORT_AUTHORITY, validate_transport_frame
from hagger_code_context_adapter import (
    ALLOWED_OPERATIONS,
    FEDERATION_AUTHORITY,
    HaggerCodeContextAdapter,
    HaggerRuntime,
    attach_hagger_context,
    validate_code_context_ref,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contratos" / "rhgd-0.0.1" / "hagger-code-context.schema.json"
COMMIT = "1" * 40
PROVIDER_COMMIT = "2" * 40
MANIFEST = "3" * 64
SYMBOL = "source.pkg.Module.fn"


def code_ref(index_dir: Path) -> dict:
    return {
        "repo_ref": "owner/repo",
        "commit_sha": COMMIT,
        "provider": "code-graph-rag",
        "alias": "hagger",
        "provider_version": "0.0.932",
        "provider_commit": PROVIDER_COMMIT,
        "index_ref": index_dir.resolve().as_uri(),
        "manifest_sha256": MANIFEST,
        "source_authority": "git",
        "mutable_tools": "disabled",
        "operations": ["definition", "callers"],
        "required_symbols": [SYMBOL],
    }


def query_payload(operation: str = "definition") -> dict:
    return {
        "ok": True,
        "operation": operation,
        "provenance": {
            "repo_ref": "owner/repo",
            "source_commit": COMMIT,
            "provider": "code-graph-rag",
            "provider_version": "0.0.932",
            "provider_commit": PROVIDER_COMMIT,
            "manifest_sha256": MANIFEST,
            "source_dirty": False,
        },
        "result": {"status": "ok", "node": {"id": SYMBOL, "path": "pkg.py", "start_line": 10, "end_line": 20}},
    }


class TestHaggerCodeContextAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index_root = self.root / "indexes"
        self.index_dir = self.index_root / "owner_repo" / COMMIT
        self.index_dir.mkdir(parents=True)
        self.provider_root = self.root / "provider"
        self.provider_root.mkdir()
        self.provider_python = self.provider_root / "python.exe"
        self.query_adapter = self.root / "query.py"
        self.provider_python.write_bytes(b"")
        self.query_adapter.write_text("# fake\n", encoding="utf-8")
        self.runtime = HaggerRuntime(
            provider_python=self.provider_python,
            query_adapter=self.query_adapter,
            provider_root=self.provider_root,
            index_root=self.index_root,
        )
        self.adapter = HaggerCodeContextAdapter(self.runtime)

    def tearDown(self):
        self.tmp.cleanup()

    def test_query_is_read_only_argv_and_schema_valid(self):
        completed = subprocess.CompletedProcess([], 0, json.dumps(query_payload()), "")
        with patch("hagger_code_context_adapter.subprocess.run", return_value=completed) as run:
            out = self.adapter.query(code_ref(self.index_dir), "definition", symbol=SYMBOL)
        kwargs = run.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[0], str(self.provider_python))
        self.assertIn("--expected-commit", cmd)
        self.assertIn(COMMIT, cmd)
        self.assertNotIn("write_file", cmd)
        self.assertEqual(out["authority"], FEDERATION_AUTHORITY)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.validate(out, schema)

    def test_mutable_or_ungranted_operation_is_rejected(self):
        bad = code_ref(self.index_dir)
        bad["mutable_tools"] = "enabled"
        with self.assertRaises(PermissionError):
            validate_code_context_ref(bad)
        with self.assertRaises(PermissionError):
            self.adapter.query(code_ref(self.index_dir), "write_file", symbol=SYMBOL)
        with self.assertRaises(PermissionError):
            self.adapter.query(code_ref(self.index_dir), "callees", symbol=SYMBOL)

    def test_symbol_scope_and_index_root_are_fail_closed(self):
        with self.assertRaises(PermissionError):
            self.adapter.query(code_ref(self.index_dir), "definition", symbol="source.other.fn")
        outside = self.root / "outside"
        outside.mkdir()
        bad = code_ref(self.index_dir)
        bad["index_ref"] = outside.as_uri()
        with self.assertRaises(PermissionError):
            self.adapter.query(bad, "definition", symbol=SYMBOL)

    def test_stale_query_provenance_is_rejected(self):
        payload = query_payload()
        payload["provenance"]["source_commit"] = "4" * 40
        completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
        with patch("hagger_code_context_adapter.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(ValueError, "source_commit"):
                self.adapter.query(code_ref(self.index_dir), "definition", symbol=SYMBOL)

    def test_materialized_context_crosses_existing_transport_without_authority_growth(self):
        completed = subprocess.CompletedProcess([], 0, json.dumps(query_payload()), "")
        with patch("hagger_code_context_adapter.subprocess.run", return_value=completed):
            materialized = self.adapter.query(code_ref(self.index_dir), "definition", symbol=SYMBOL)
        envelope = attach_hagger_context(
            {"schema_version": "pgh.context-envelope/0.1", "context_ref": "pgh://context/u16"},
            materialized,
        )
        q = AsymmetricEnvelopeQueue("peer-a", joined_peer_ids={"peer-b"}, stream_id="u16", clock_ms=lambda: 1)
        frame = q.put_outbound(
            envelope,
            work_id="work-u16",
            model_ref="agent-b",
            destination_peer="peer-b",
            correlation_id="corr-u16",
            authorization_ref="pgh://auth/u16",
            pgd_execution_ref="pgd://execution/u16",
        )
        validate_transport_frame(frame)
        self.assertEqual(frame["transport_authority"], TRANSPORT_AUTHORITY)
        self.assertEqual(frame["context_envelope"]["code_context"]["authority"], FEDERATION_AUTHORITY)
        for forbidden in ("scheduler", "lease", "assignment", "execution_queue"):
            self.assertFalse(hasattr(self.adapter, forbidden))

    def test_allowlist_is_exactly_read_only_contract(self):
        self.assertEqual(
            ALLOWED_OPERATIONS,
            {
                "summary", "resolve", "definition", "callers", "callees",
                "importers", "implementors", "overrides", "tests-reaching",
            },
        )


if __name__ == "__main__":
    unittest.main()
