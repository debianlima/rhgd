"""RHGD -> PGD federation adapter.

Builds the logical pgd-rhgd-federation/1 payload without owning admission,
queue, lease, scheduler, retry, recovery or runtime state.
"""
from __future__ import annotations
from dataclasses import asdict
from context_preorchestrator import ContextEnvelope
from rhgd_cognitive_dag import WorkUnit

PGD_FEDERATION_SCHEMA = "pgd-rhgd-federation/1"
STABLE_RUNTIME_RELEASE = "v2.3.2"
STABLE_RUNTIME_COMMIT = "cfd68602a4491d61658f564b86d550f4b498f06f"
PGD_OWNS = ["admission", "queue", "lease", "scheduler", "retry", "recovery", "runtime_state"]
RHGD_OWNS = ["capability_discovery", "federation_transport", "interdomain_provenance"]


def _expansion_policy(envelope: ContextEnvelope) -> str:
    levels = tuple(envelope.expansion_policy.get("levels", ()))
    if "global_catalog" in levels:
        return "selected-adjacent-global"
    if "adjacent" in levels:
        return "selected-adjacent"
    return "selected"


def build_pgd_federation_payload(
    envelope: ContextEnvelope,
    work: WorkUnit,
    *,
    request_id: str,
    correlation_id: str,
    authorization_ref: str,
    context_ref: str,
    idempotency_key: str,
    expected_output_schema_ref: str,
    requested_lease_seconds: int,
    required_capabilities: tuple[str, ...] = (),
    deadline: str | None = None,
    remaining_depth: int | None = None,
    max_nodes: int | None = None,
) -> dict:
    """Map PGH context + RHGD WorkUnit to the PGD federation contract.

    `requested_lease_seconds` is a request, never a lease grant. The returned
    structure contains no PGD scheduler/queue mutation and no authority growth.
    """
    required_strings = {
        "request_id": request_id,
        "correlation_id": correlation_id,
        "authorization_ref": authorization_ref,
        "context_ref": context_ref,
        "idempotency_key": idempotency_key,
        "expected_output_schema_ref": expected_output_schema_ref,
    }
    for name, value in required_strings.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")
    if requested_lease_seconds < 1:
        raise ValueError("requested_lease_seconds must be >= 1")
    if work.context_tokens < 1:
        raise ValueError("work.context_tokens must be >= 1")
    if work.privacy_level not in range(5):
        raise ValueError("work.privacy_level must be between 0 and 4")

    decomposition = {}
    if remaining_depth is not None:
        if remaining_depth < 0:
            raise ValueError("remaining_depth must be >= 0")
        decomposition["remaining_depth"] = remaining_depth
    if max_nodes is not None:
        if max_nodes < 1:
            raise ValueError("max_nodes must be >= 1")
        decomposition["max_nodes"] = max_nodes

    work_unit = {
        "work_id": work.work_id,
        "domain": work.domain,
        "idempotency_key": idempotency_key,
        "expected_output_schema_ref": expected_output_schema_ref,
        "requested_lease_seconds": requested_lease_seconds,
        "deadline": deadline,
    }
    if decomposition:
        work_unit["decomposition"] = decomposition

    return {
        "schema_version": PGD_FEDERATION_SCHEMA,
        "request": {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "authorization_ref": authorization_ref,
            "context_envelope": {
                "schema_version": envelope.version,
                "context_ref": context_ref,
                "context_tokens": work.context_tokens,
                "privacy_level": work.privacy_level,
                "required_capabilities": list(dict.fromkeys(required_capabilities)),
                "expansion_policy": _expansion_policy(envelope),
            },
            "work_unit": work_unit,
        },
        "runtime_mapping": {
            "stable_release": STABLE_RUNTIME_RELEASE,
            "stable_commit": STABLE_RUNTIME_COMMIT,
            "message_schema": "pgh-message/1",
            "delivery_semantics": "at-least-once+idempotency+ack+lease",
            "pgd_owns": PGD_OWNS.copy(),
            "rhgd_owns": RHGD_OWNS.copy(),
        },
        "response": {
            "status": "ADMITTED",
            "execution_ref": "pgd://pending",
            "lease_ref": None,
            "outcome_evidence_ref": None,
            "retryable": False,
            "outcome_classification": "observed",
        },
    }


def federation_input_fingerprint(envelope: ContextEnvelope, work: WorkUnit) -> dict:
    """Safe, non-secret structural input projection for audit/debugging."""
    return {
        "context_version": envelope.version,
        "strategy": envelope.strategy,
        "token_budget": envelope.token_budget,
        "selected_ids": [x.id for x in envelope.selected],
        "work": asdict(work),
    }
