"""Transport-path evidence for RHGD destination matching; never an execution authority."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

TRANSPORTS={"NETMAKER","LAN","WIREGUARD_DIRECT","IPSEC","HUB","UNKNOWN"}
CLASSIFICATIONS={"observado","derivado","estimado","indisponivel"}

@dataclass(frozen=True)
class TransportPathEvidence:
    path_id:str
    source_peer:str
    destination_peer:str
    transport:str
    observed_at_ms:int
    expires_at_ms:int
    classification:str
    source_ref:str
    route_observed:bool
    rtt_ms:float|None=None
    bandwidth_mib_s:float|None=None
    packet_loss_pct:float|None=None
    mtu:int|None=None

    def validate(self)->"TransportPathEvidence":
        if not self.path_id or not self.source_peer or not self.destination_peer or not self.source_ref:
            raise ValueError("transport path identity/source required")
        if self.transport not in TRANSPORTS:
            raise ValueError("unsupported transport")
        if self.classification not in CLASSIFICATIONS:
            raise ValueError("invalid classification")
        if self.observed_at_ms < 0 or self.expires_at_ms <= self.observed_at_ms:
            raise ValueError("invalid path evidence freshness")
        if self.rtt_ms is not None and self.rtt_ms < 0: raise ValueError("invalid rtt")
        if self.bandwidth_mib_s is not None and self.bandwidth_mib_s < 0: raise ValueError("invalid bandwidth")
        if self.packet_loss_pct is not None and not 0 <= self.packet_loss_pct <= 100: raise ValueError("invalid loss")
        if self.mtu is not None and self.mtu < 576: raise ValueError("invalid mtu")
        return self

    def fresh(self, now_ms:int)->bool:
        self.validate()
        return self.route_observed and self.observed_at_ms <= int(now_ms) <= self.expires_at_ms and self.classification != "indisponivel"

    def as_contract(self)->dict[str,Any]:
        self.validate()
        return {
            "schema_version":"rhgd-transport-path-evidence/1","path_id":self.path_id,"source_peer":self.source_peer,"destination_peer":self.destination_peer,
            "transport":self.transport,"observed_at_ms":self.observed_at_ms,"expires_at_ms":self.expires_at_ms,"classification":self.classification,"source_ref":self.source_ref,"route_observed":self.route_observed,
            "metrics":{"rtt_ms":self.rtt_ms,"bandwidth_mib_s":self.bandwidth_mib_s,"packet_loss_pct":self.packet_loss_pct,"mtu":self.mtu},
            "projection":{"source_of_truth":False,"rebuildable":True},
            "authority":{"effect":"NONE","scheduler":False,"lease_grant":False,"assignment":False,"admission":False},
        }

def transport_path_bonus(evidence:TransportPathEvidence|None, *, now_ms:int)->float:
    """Small evidence-derived ranking signal. No transport name receives a hardcoded preference."""
    if evidence is None or not evidence.fresh(now_ms):
        return 0.0
    observed=[]
    if evidence.rtt_ms is not None:
        observed.append(0.45/(1.0 + float(evidence.rtt_ms)/20.0))
    if evidence.bandwidth_mib_s is not None:
        observed.append(0.45*min(1.0,float(evidence.bandwidth_mib_s)/1000.0))
    if evidence.packet_loss_pct is not None:
        observed.append(-0.40*min(1.0,float(evidence.packet_loss_pct)/5.0))
    if evidence.mtu is not None:
        observed.append(0.05*min(1.0,float(evidence.mtu)/1500.0))
    return round(sum(observed),6) if observed else 0.0
