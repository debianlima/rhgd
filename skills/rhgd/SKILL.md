---
name: rhgd-project
versao: 0.0.11
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

## Conciliação da suíte — U-RHGD-08
`pgd-incremental-information-exchange/1` atravessa zona heterogênea por referência/federação RHGD, mas WCB, assignment, fila, lease, retry, watermark e runtime continuam PGD. `pga-network-service-agents/1` fixa rede privada por padrão, join explícito e dois papéis efêmeros; RHGD é owner da federação de rede, enquanto a materialização/execução desses agentes permanece no PGD. `pga-deterministic-priority-policy/1` não concede autoridade nem preempção. `NodeCapability` em memória e advertisement HMM read-only são capability snapshots, **não prova de capability discovery vivo**. Gate: `tests/verify_u_rhgd_08_suite_protocol_conciliation.py`; produção permanece bloqueada até discovery vivo, rede autenticada e fences end-to-end serem observados.

## Freshness downstream — U-RHGD-09
Consumidores downstream seguem o **último safe point fechado** do RHGD, nunca o HEAD de uma unidade RHGD ainda em curso. Se um consumidor mantém pin anterior enquanto possui `trabalho_compartilhado` ativo, classificar `BLOCKED_ACTIVE_OWNER_STALE`: detectar e registrar, mas não editar a zona do owner e não declarar fixed point atual. A prova deve reconstruir o estado pelo commit observado do consumidor para continuar auditável depois que o owner avançar. Gate: `tests/verify_u_rhgd_09_downstream_consumer_freshness.py`.

## Freshness de provider — U-RHGD-11
Avanço de HEAD do provider não implica reconciliação funcional do RHGD por si só. Para classificar `HEAD_DRIFT_CONTRACTS_IDENTICAL`, provar simultaneamente: commit anterior ancestral do novo; hashes dos artefatos realmente consumidos idênticos antes/depois; nenhum path semântico consumido alterado; fronteira de autoridade preservada. Evidência histórica anterior não é reescrita. Se qualquer hash/path semântico divergir, fail-closed e abrir reconciliação funcional. Gate: `tests/verify_u_rhgd_11_pga_provider_structural_drift.py`.

## Discovery vivo e transporte de ContextEnvelope — U-RHGD-12
Capability discovery vivo usa peer explicitamente aderido, `boot_id`, sequência monotônica, TTL e rejeição de stale/replay; anúncio continua read-only (`scheduler=false`, `lease_grant=false`, `assignment=false`). Teste real bidirecional em dois peers da overlay passou; capability values eram `test_declared`, serviço persistente/app-auth/reconnect de produção continuam não homologados.

A palavra **fila** é ambígua e deve ser qualificada: `ExecutionQueue` (WorkUnit/admission/assignment/lease/scheduler/retry/recovery) é exclusivamente PGD. `EnvelopeTransportQueue` é RHGD e controla distribuição de `ContextEnvelope` entre works/modelos com lanes ingress/egress independentes, sequência por peer, buffering de reordenação, `put/get/remove` e ACK antes da remoção do egress. Cada frame exige `authorization_ref` PGH e `pgd_assignment_ref`; RHGD nunca minta lease nem assignment. Gates: `tests/verify_u_rhgd_12_live_capability_discovery.py` e `tests/verify_u_rhgd_12_context_envelope_transport.py`.

## Redução determinística
Redução hierárquica deve ser independente da ordem de chegada. Canonicalizar identidade textual antes de deduplicar; ordenar conteúdo lógico e provenance por chave estável. `fan_in` pode alterar `depth`, nunca claims/evidence/dissent/sources finais.

## Profundidade derivada
Consumir `hmm-capability-advertisement/1` apenas read-only. Capacidade de contexto deve vir explicitamente declarada; nunca inferir tokens de VRAM/RAM. Custos de níveis vêm do PGH/catálogo. Derivar profundidade pelo orçamento restante; sem custos declarados, retornar `undeclared`.

## Dissenso preservado
Dissenso explícito bloqueia colapso silencioso. Preservar work_id/node_id/confidence de quem sustentou cada dissenso. Não inferir maioria, verdade, oposição semântica ou métrica de concordância sem contrato de stance/classificação.

## Métricas de estrutura de conhecimento
Antes de reorganizar árvore/ontologia, medir. `TREE_LOCALITY` mede acesso cross-subtree; `LEVEL_RECALL` compara recuperação direta e descida sobre o mesmo gold set. Limiar deve ser pré-declarado e resultado experimental não pode ser fabricado por teste unitário.
