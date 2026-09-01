"""Adapter read-only de hmm-capability-advertisement/1 para ExecutorProfile RHGD."""
from __future__ import annotations
from context_preorchestrator import ExecutorProfile

def executor_profile_from_hmm(advertisement:dict, *, executor_id:str, executor_class:str="model_runtime", loaded_tokens:int=0, reserve_tokens:int=3072, active_sessions:int=1)->ExecutorProfile:
    if advertisement.get("schema_version") != "hmm-capability-advertisement/1":
        raise ValueError("unsupported HMM capability schema")
    authority=advertisement.get("authority") or {}
    if authority.get("mode") != "read_only_advisory" or authority.get("scheduler") is not False or authority.get("lease_grant") is not False:
        raise ValueError("HMM advertisement authority boundary is not read-only")
    cc=advertisement.get("context_capacity") or {}
    configured=cc.get("configured_tokens")
    effective=cc.get("usable_tokens", cc.get("effective_budget_tokens"))
    if not isinstance(configured,int) or configured < 1024:
        raise ValueError("context_capacity.configured_tokens is required")
    if effective is not None and (not isinstance(effective,int) or effective < 1024 or effective > configured):
        raise ValueError("context capacity effective/usable limit is invalid")
    return ExecutorProfile(
        executor_id=executor_id, executor_class=executor_class,
        model_context_capacity=configured, effective_context_budget=effective,
        loaded_tokens=loaded_tokens, reserve_tokens=reserve_tokens,
        active_sessions=active_sessions,
        capability_source="hmm-capability-advertisement/1", confidence=.9)
