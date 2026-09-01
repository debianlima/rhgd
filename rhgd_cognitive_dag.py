"""RHGD Fase 0: decomposicao cognitiva e reducao hierarquica, sem model-parallel remoto."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Sequence
import hashlib, json, re, unicodedata

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

class FederatedDestinationMatcher:
    """Seleciona destinos federados elegíveis; não agenda, enfileira, concede lease nem executa WorkUnits."""
    def match(self, units:Sequence[WorkUnit], nodes:Sequence[NodeCapability])->list[Assignment]:
        out=[]
        for w in units:
            eligible=[n for n in nodes if n.available and n.context_tokens>=w.context_tokens and n.privacy_level>=w.privacy_level and (not n.domains or w.domain in n.domains)]
            if not eligible: continue
            def score(n): return n.trust*2 + min(1,n.context_tokens/max(1,w.context_tokens)) - .08*n.queue_depth
            best=max(eligible,key=score); out.append(Assignment(w.work_id,best.node_id,round(score(best),4)))
        return out

    def assign(self, units:Sequence[WorkUnit], nodes:Sequence[NodeCapability])->list[Assignment]:
        """Compatibilidade de API: ``assign`` apenas calcula destino; ownership operacional continua no PGD."""
        return self.match(units,nodes)

# Compatibilidade histórica: consumidores podem importar o símbolo antigo sem reintroduzir
# semântica de scheduler no RHGD. O tipo canônico permanece FederatedDestinationMatcher.
CognitiveScheduler = FederatedDestinationMatcher

class HierarchicalReducer:
    """Reduz resultados preservando proveniencia, evidencia e dissenso."""
    def reduce(self, results:Sequence[CognitiveResult], fan_in:int=4)->dict:
        level=[self._leaf(r) for r in results]; depth=0
        while len(level)>1:
            nxt=[]
            for i in range(0,len(level),fan_in): nxt.append(self._merge(level[i:i+fan_in],depth+1))
            level=nxt; depth+=1
        return level[0] if level else {"claims":[],"evidence":[],"dissent":[],"dissent_records":[],"sources":[],"collapse_allowed":True,"resolution_status":"NO_DISSENT_DECLARED","depth":0}
    @classmethod
    def _leaf(cls,r):
        records=[]
        for raw in r.dissent:
            canon=cls._canonical_text(raw)
            records.append({"dissent":str(raw),"canonical":canon,"work_id":r.work_id,"node_id":r.node_id,"confidence":float(r.confidence)})
        records.sort(key=lambda x:(hashlib.sha256(x["canonical"].encode("utf-8")).hexdigest(),x["work_id"],x["node_id"],x["confidence"],x["dissent"].encode("utf-8")))
        present=bool(records)
        return {"claims":list(r.claims),"evidence":list(r.evidence),"dissent":list(r.dissent),"dissent_records":records,"sources":[{"work_id":r.work_id,"node_id":r.node_id,"confidence":r.confidence}],"collapse_allowed":not present,"resolution_status":"DISSENT_PRESERVED" if present else "NO_DISSENT_DECLARED","depth":0}
    @staticmethod
    def _canonical_text(value:str)->str:
        value=unicodedata.normalize("NFKC",str(value))
        value=re.sub(r"\s+"," ",value).strip()
        return value.casefold()
    @classmethod
    def _stable_texts(cls,items,key):
        chosen={}
        for item in items:
            for raw in item[key]:
                canon=cls._canonical_text(raw)
                digest=hashlib.sha256(canon.encode("utf-8")).hexdigest()
                rank=(digest,canon)
                candidate=str(raw)
                prev=chosen.get(rank)
                if prev is None or candidate.encode("utf-8") < prev.encode("utf-8"):
                    chosen[rank]=candidate
        return [chosen[k] for k in sorted(chosen)]
    @staticmethod
    def _stable_sources(items):
        uniq={}
        for item in items:
            for source in item["sources"]:
                key=(str(source.get("work_id","")),str(source.get("node_id","")),float(source.get("confidence",0.0)))
                uniq[key]={"work_id":key[0],"node_id":key[1],"confidence":key[2]}
        return [uniq[k] for k in sorted(uniq)]
    @classmethod
    def _stable_dissent_records(cls,items):
        uniq={}
        for item in items:
            for rec in item.get("dissent_records",()):
                canon=cls._canonical_text(rec.get("dissent",rec.get("canonical","")))
                key=(hashlib.sha256(canon.encode("utf-8")).hexdigest(),str(rec.get("work_id","")),str(rec.get("node_id","")),float(rec.get("confidence",0.0)))
                candidate={"dissent":str(rec.get("dissent","")),"canonical":canon,"work_id":key[1],"node_id":key[2],"confidence":key[3]}
                prev=uniq.get(key)
                if prev is None or candidate["dissent"].encode("utf-8") < prev["dissent"].encode("utf-8"):
                    uniq[key]=candidate
        return [uniq[k] for k in sorted(uniq)]
    @classmethod
    def _merge(cls,items,depth):
        records=cls._stable_dissent_records(items)
        present=bool(records)
        return {"claims":cls._stable_texts(items,"claims"),"evidence":cls._stable_texts(items,"evidence"),"dissent":cls._stable_texts(items,"dissent"),"dissent_records":records,"sources":cls._stable_sources(items),"collapse_allowed":not present,"resolution_status":"DISSENT_PRESERVED" if present else "NO_DISSENT_DECLARED","depth":depth}

def signed_payload_stub(obj)->dict:
    """Commitment deterministico; assinatura real pertence ao adaptador de identidade da RHGD."""
    payload=json.dumps(asdict(obj),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return {"sha256":hashlib.sha256(payload).hexdigest(),"payload_bytes":len(payload)}
