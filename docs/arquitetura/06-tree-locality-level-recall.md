# U-RHGD-05 — instrumentos TREE_LOCALITY e LEVEL_RECALL

Esta unidade não reorganiza a ontologia e não executa campanha estatística. Ela homologa instrumentos puros para medir duas hipóteses: se itens usados em sequência permanecem na mesma subárvore e se recuperação direta em níveis indexados recupera folhas conhecidas melhor/pior que a descida hierárquica.

`TREE_LOCALITY` mede transições cross-subtree em profundidade declarada. `LEVEL_RECALL` usa o mesmo gold set para direct retrieval e descent retrieval. Limiar e corpus devem ser declarados antes da campanha. A execução quantitativa pertence ao host de simulação autorizado.
