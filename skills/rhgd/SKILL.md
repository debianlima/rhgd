---
name: rhgd-project
versao: 0.0.7
description: Skill de projeto da RHGD Fase 0 para federacao de trabalho cognitivo heterogeneo governado.
tipo_competencia: projeto
---
# RHGD Project Skill

## Missão
Materializar a camada federativa sem duplicar PGD: descobrir capacidades externas, transportar WorkUnits autorizadas, preservar privacidade/proveniência e suportar redução hierárquica.

## Fronteiras
PGA governa; PGH contextualiza/autoriza; PGD agenda/executa; RHGD federa; MSGCD agrega.

## Regra de implementação
Começar por contratos e adapters. Sem blockchain no caminho crítico, sem token na Fase 0, sem segredo no projeto, sem model-parallel remoto como pressuposto.

## 4B/16K
Uma competência detalhada por etapa; microcontexto; saída contratual; memória condensada; expansão selected -> adjacent -> global mediante insuficiência.

## Adapter PGD
`pgd-rhgd-federation/1` é a fronteira federation-facing. RHGD descobre capacidade e transporta WorkUnits autorizadas; PGD mantém admission, fila, lease, scheduler, retry, recovery e estado runtime. `authorization_ref` PGH é obrigatório; lease solicitado não é concessão. Resultado retorna `observed`.

## Matcher federativo — LAT-02
O tipo canônico para escolha de destino é `FederatedDestinationMatcher`: ele filtra e ranqueia destinos federados elegíveis, mas não agenda, enfileira, concede lease, faz admission, retry ou execução. `CognitiveScheduler` permanece somente como alias de compatibilidade para consumidores legados. Gate: contrato TDD vermelho antes da implementação, regressão unitária completa e `NO_SECOND_SCHEDULER`/U-RHGD-07 preservados.

## Redução determinística
Redução hierárquica deve ser independente da ordem de chegada. Canonicalizar identidade textual antes de deduplicar; ordenar conteúdo lógico e provenance por chave estável. `fan_in` pode alterar `depth`, nunca claims/evidence/dissent/sources finais.

## Profundidade derivada
Consumir `hmm-capability-advertisement/1` apenas read-only. Capacidade de contexto deve vir explicitamente declarada; nunca inferir tokens de VRAM/RAM. Custos de níveis vêm do PGH/catálogo. Derivar profundidade pelo orçamento restante; sem custos declarados, retornar `undeclared`.

## Dissenso preservado
Dissenso explícito bloqueia colapso silencioso. Preservar work_id/node_id/confidence de quem sustentou cada dissenso. Não inferir maioria, verdade, oposição semântica ou métrica de concordância sem contrato de stance/classificação.

## Métricas de estrutura de conhecimento
Antes de reorganizar árvore/ontologia, medir. `TREE_LOCALITY` mede acesso cross-subtree; `LEVEL_RECALL` compara recuperação direta e descida sobre o mesmo gold set. Limiar deve ser pré-declarado e resultado experimental não pode ser fabricado por teste unitário.
