"""RHGD Fase 0: decomposicao cognitiva e reducao hierarquica, sem model-parallel remoto."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Sequence
import hashlib, json

@dataclass(frozen=True)
class NodeCapability:
    node_id:str; context_tokens:int; trust:float=.5; privacy_level:int=0
    domains:tuple[str,...]=(); available:bool=True; queue_depth:int=0

@dataclass(frozen=True)
class WorkUnit:
    work_id:str; domain:str; context_tokens:int; privacy_level:int=0
    dependencies:tuple[str,...]=(); reduce_group:str="root"; delegation_depth:int=0

@dataclass(frozen=True)
class Assignment:
    work_id:str; node_id:str; score:float

@dataclass(frozen=True)
class CognitiveResult:
    work_id:str; node_id:str; claims:tuple[str,...]; evidence:tuple[str,...]=()
    dissent:tuple[str,...]=(); confidence:float=.5

class CognitiveScheduler:
    """Agenda unidades semanticamente fechadas; nunca fragmenta uma inferencia tensor-a-tensor."""
    def assign(self, units:Sequence[WorkUnit], nodes:Sequence[NodeCapability])->list[Assignment]:
        out=[]
        for w in units:
            eligible=[n for n in nodes if n.available and n.context_tokens>=w.context_tokens and n.privacy_level>=w.privacy_level and (not n.domains or w.domain in n.domains)]
            if not eligible: continue
            def score(n): return n.trust*2 + min(1,n.context_tokens/max(1,w.context_tokens)) - .08*n.queue_depth
            best=max(eligible,key=score); out.append(Assignment(w.work_id,best.node_id,round(score(best),4)))
        return out

class HierarchicalReducer:
    """Reduz resultados preservando proveniencia, evidencia e dissenso."""
    def reduce(self, results:Sequence[CognitiveResult], fan_in:int=4)->dict:
        level=[self._leaf(r) for r in results]; depth=0
        while len(level)>1:
            nxt=[]
            for i in range(0,len(level),fan_in): nxt.append(self._merge(level[i:i+fan_in],depth+1))
            level=nxt; depth+=1
        return level[0] if level else {"claims":[],"evidence":[],"dissent":[],"sources":[],"depth":0}
    @staticmethod
    def _leaf(r): return {"claims":list(r.claims),"evidence":list(r.evidence),"dissent":list(r.dissent),"sources":[{"work_id":r.work_id,"node_id":r.node_id,"confidence":r.confidence}],"depth":0}
    @staticmethod
    def _merge(items,depth):
        def uniq(k): return list(dict.fromkeys(x for item in items for x in item[k]))
        return {"claims":uniq("claims"),"evidence":uniq("evidence"),"dissent":uniq("dissent"),"sources":[x for item in items for x in item["sources"]],"depth":depth}

def signed_payload_stub(obj)->dict:
    """Commitment deterministico; assinatura real pertence ao adaptador de identidade da RHGD."""
    payload=json.dumps(asdict(obj),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return {"sha256":hashlib.sha256(payload).hexdigest(),"payload_bytes":len(payload)}
