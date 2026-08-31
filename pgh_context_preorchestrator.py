"""PGH resource-aware context pre-orchestrator candidate U-239."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping, Sequence
import re, time

@dataclass(frozen=True)
class ExecutorProfile:
    executor_id: str
    executor_class: str = "virtual_remote"
    model_context_capacity: int = 16384
    effective_context_budget: int | None = None
    loaded_tokens: int = 0
    reserve_tokens: int = 3072
    active_sessions: int = 1
    capability_source: str = "unknown"
    confidence: float = .5
    def usable_tokens(self):
        ceiling=min(self.model_context_capacity,self.effective_context_budget or self.model_context_capacity)
        pressure=max(.35,1.0-.08*max(0,self.active_sessions-1))
        return max(1024,int((ceiling-self.loaded_tokens-self.reserve_tokens)*pressure))

@dataclass(frozen=True)
class ContextCandidate:
    id: str; kind: str; domains: tuple[str,...]; estimated_tokens: int
    priority: float=.5; summary: str=""

@dataclass(frozen=True)
class MessageClassification:
    domains: tuple[str,...]; intent: str; confidence: float; keywords: tuple[str,...]

@dataclass
class ContextEnvelope:
    version: str; classification: MessageClassification; executor: ExecutorProfile
    strategy: str; token_budget: int; selected: list[ContextCandidate]
    suggested_next: list[ContextCandidate]; expansion_policy: dict; generated_at: int
    def to_dict(self): return asdict(self)

DEFAULT_DOMAIN_TERMS: Mapping[str,tuple[str,...]]={
 "algorithm_design":("algoritmo","algorithm","otimizacao","otimização","optimization","heuristica"),
 "software_engineering":("codigo","código","code","implementar","implement","python","teste","test"),
 "performance":("desempenho","performance","benchmark","latencia","latência","memoria","memória","vram","ram"),
 "documentation":("documentar","documentacao","documentação","artigo","relatorio","relatório","abnt"),
 "agent_orchestration":("agente","agent","bot","orquestr","work virtual","skill","competencia","competência"),
 "context_management":("contexto","context","ontologia","ontology","arvore","árvore","catalogo","catálogo"),
 "runtime_inference":("ollama","sglang","modelo","inferencia","inferência","llm","gpu")}

class ContextPreOrchestrator:
    def __init__(self,candidates:Sequence[ContextCandidate],domain_terms=None):
        self.candidates=list(candidates); self.domain_terms=domain_terms or DEFAULT_DOMAIN_TERMS
    def classify(self,message):
        n=re.sub(r"\s+"," ",message.casefold()); hits=[]; found=set()
        for domain,terms in self.domain_terms.items():
            score=sum(1 for term in terms if term in n)
            found.update(term for term in terms if term in n)
            if score: hits.append((domain,score))
        hits.sort(key=lambda x:(-x[1],x[0])); domains=tuple(x[0] for x in hits[:4]) or ("general",)
        total=sum(x[1] for x in hits); confidence=min(.98,.45+.09*total) if total else .35
        intent="implement" if any(x in n for x in ("implementar","implement","codigo","código","code")) else "analyze" if any(x in n for x in ("analisar","analyze","avaliar","compare")) else "execute"
        return MessageClassification(domains,intent,confidence,tuple(sorted(found))[:16])
    def _rank(self,c):
        wanted=set(c.domains); ranked=[]
        for item in self.candidates:
            score=item.priority+1.25*len(wanted.intersection(item.domains))
            if item.kind=="project_skill": score+=.35
            ranked.append((score,item))
        return sorted(ranked,key=lambda x:(-x[0],x[1].estimated_tokens,x[1].id))
    @staticmethod
    def strategy_for(p):
        usable=p.usable_tokens(); ratio=usable/max(1,p.model_context_capacity)
        if p.model_context_capacity>=100000 and ratio>=.65: return "sequential_hats_wide_memory"
        if usable<=10000 or p.model_context_capacity<=20000: return "microcontext_serial"
        return "selective_branches"
    def build(self,message,profile):
        c=self.classify(message); budget=profile.usable_tokens(); strategy=self.strategy_for(profile)
        selection_budget=max(768,int(budget*(.34 if strategy=="microcontext_serial" else .48)))
        selected=[]; deferred=[]; used=0
        for _,item in self._rank(c):
            relevant=bool(set(item.domains).intersection(c.domains))
            if not relevant and c.confidence>=.60: deferred.append(item); continue
            if used+item.estimated_tokens<=selection_budget: selected.append(item); used+=item.estimated_tokens
            else: deferred.append(item)
        return ContextEnvelope("pgh.context-envelope/0.1",c,profile,strategy,budget,selected,deferred[:8],{
          "default":"local_first","levels":["selected","adjacent","global_catalog"],
          "global_catalog":"request" if strategy=="microcontext_serial" else "allowed",
          "trigger":"missing_skill_or_tool|insufficient_evidence|scope_limitation_detected",
          "instruction":"Se o pacote nao contiver competencia, ferramenta ou evidencia suficiente, solicite ramos adjacentes; se continuar insuficiente, solicite o catalogo global."},int(time.time()))
