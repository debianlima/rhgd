"""Métricas puras para validar localidade da árvore e recall multi-nível. Sem I/O e sem reestruturação automática."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence

@dataclass(frozen=True)
class AccessedNode:
    node_id:str
    path:tuple[str,...]

def tree_locality(nodes:Sequence[AccessedNode], *, subtree_depth:int=1)->dict:
    if subtree_depth < 1: raise ValueError("subtree_depth must be >= 1")
    pairs=max(0,len(nodes)-1); cross=0
    def prefix(n): return n.path[:subtree_depth]
    for a,b in zip(nodes,nodes[1:]):
        if prefix(a)!=prefix(b): cross+=1
    return {"transitions":pairs,"cross_subtree":cross,"cross_subtree_rate":(cross/pairs if pairs else 0.0),"subtree_depth":subtree_depth}

def recall(gold:Iterable[str], retrieved:Iterable[str])->float:
    g=set(gold); r=set(retrieved)
    if not g: return 1.0
    return len(g & r)/len(g)

def level_recall(*, gold_leaf_ids:Iterable[str], direct_retrieved:Iterable[str], descent_retrieved:Iterable[str])->dict:
    direct=recall(gold_leaf_ids,direct_retrieved); descent=recall(gold_leaf_ids,descent_retrieved)
    return {"direct_recall":direct,"descent_recall":descent,"delta_direct_minus_descent":direct-descent}
