# Estado — RHGD 0.0.1 — Fase 0

Estado: `STANDBY_CANDIDATE`.

Materializado como repositório-zero local para consolidar arquitetura e políticas antes de qualquer homologação de rede real.

## Dependências normativas
- PGH vivo: `pgh@1.2.0`; U08 consome o safe point fechado U278 `1832fa24375a1e2f3cc207b163f1a42d0acc2042`. U282 permanece owner ativo e não é consumida no meio da unidade.
- PGD: `fa63a046e79e28d512dd901c43629d47a5bdea89`; `pgd-rhgd-federation/1` e `pgd-incremental-information-exchange/1` preservam runtime/assignment/fila/lease/retry/recovery/watermark no PGD.
- PGA: `5d1dfd93b0525db26b44efaea8bdbc56f25c185c`; U08/U09 preservam private-by-default, join explícito, network federation owner RHGD, runtime owner PGD e prioridade sem expansão de autoridade.
- Control Plane: safe point fechado U280 `9408814f4af6b73c743b0dc35661caee0da5adca`; `config/3.0/context-sync.yaml` pinado por hash. U281 permanece owner ativo e não é consumida no meio da unidade.
- MSGCD permanece composição/read-model agregador, não autoridade adicional nem repositório/runtime standalone obrigatório para a fronteira RHGD.

## Não reivindicado
- rede P2P real;
- forks AntSeed/Gensyn/Akash;
- TEE/attestation homologado;
- settlement/blockchain;
- token;
- prova criptográfica completa de inferência;
- produção.

## Próximas unidades
1. capability discovery **vivo** entre ao menos dois peers, com freshness e rejeição de anúncio stale;
2. federação real autenticada preservando assignment/lease/fence PGD de ponta a ponta;
3. reconnect/failure/idempotência e proveniência de resultado observados por canal independente;
4. privacy/join/grants private-by-default em rede real;
5. TEE/attestation somente se virar requisito contratual de produção;
6. adapters upstream somente após licença, pin, contrato e portões próprios;
7. promoção de `STANDBY_CANDIDATE` somente depois dos gates reais de produção.

## U-RHGD-01 — conciliação PGD
- `DELTA_INVENTORY=PASS`.
- `LEARNING_PRESERVED=PASS`.
- `CONTEXT_ENVELOPE_TO_PGD=PASS`.
- `PGH_AUTHORIZATION_REQUIRED=PASS`.
- `RESOURCE_STATE_OWNED_BY_PGD=PASS`.
- `NO_DUPLICATE_PGD_RUNTIME=PASS`.
- `OUTCOME_EVIDENCE_OBSERVED_ONLY=PASS`.
- `CORE_CHANGE_REQUIRED=NO`.
- Skill ativa: `rhgd-project@0.0.6`.
- Próxima frente: capability discovery vivo e Context Envelope por capacidade real do executor; scheduler/lease continuam no PGD.

## U-RHGD-02 — redução determinística
- `REDUCTION_DETERMINISTIC=PASS`.
- `FAN_IN_LOGICAL_INDEPENDENCE=PASS`.
- `PROVENANCE_PRESERVED=PASS`.
- dissenso continua preservado sem interpretação semântica nesta unidade.
- `CORE_CHANGE_REQUIRED=NO`.
- próxima frente: consumir `hmm-capability-advertisement/1` para orçamento/profundidade derivada.

## U-RHGD-03 — profundidade derivada + capability HMM
- `HMM_CAPABILITY_CONSUMED=PASS`.
- `DEPTH_DERIVED=PASS`.
- `NO_HIDDEN_DEPTH_CONSTANT=PASS`.
- `NO_VRAM_TO_TOKEN_GUESS=PASS`.
- `NO_SCHEDULER_DUPLICATION=PASS`.
- U35 histórico preservado; `CORE_CHANGE_REQUIRED=NO`.
- próxima frente: dissenso preservado/medido, sem colapso silencioso.

## U-RHGD-04 — dissenso preservado
- `DISSENT_PRESERVED=PASS`.
- `SILENT_COLLAPSE_BLOCKED=PASS`.
- `DISSENT_PROVENANCE=PASS`.
- redução determinística preservada.
- sem clustering/kappa implícito; `CORE_CHANGE_REQUIRED=NO`.
- próxima frente: medir localidade/recall da árvore sem reestruturar antes da evidência.

## U-RHGD-05 — instrumentos de localidade/recall
- `TREE_LOCALITY_METRIC=PASS`; `LEVEL_RECALL_METRIC=PASS`.
- nenhum rearranjo automático da ontologia.
- campanha quantitativa adiada para host de simulação; `CORE_CHANGE_REQUIRED=NO`.

## U-RHGD-06-SUITE-CONTEXT-RECONCILIATION — unidade aberta
- `telemetria_inicio=2026-09-01T13:53:09Z`; objetivo: atualizar somente a projeção corrente de dependências; pins U-RHGD-01 continuam históricos.

## U-RHGD-06-SUITE-CONTEXT-RECONCILIATION — INTERRUPTED
- `telemetria_fim=2026-09-01T14:04:00Z`; interrupção por repriorização humana explícita para implementar PGD Work Context Broadcast.
- Nenhuma evidência/implementação U06 foi homologada ou publicada; o teste TDD local não versionado foi preservado sem ser tratado como aceite.
- `trabalho_compartilhado` liberado; retomada futura exige nova unidade/safe point e reconciliação dos HEADs.
## U-RHGD-07-PGH2-CORE-RECONCILIATION — gates locais PASS
- PGH=`304b9914ae44b0ac4240d912bd81f7be87d5a708`; PGD=`3f7d70e974271a0ee316df9425d5e955225fddd4`; PGA=`c151e58adf05339eee7f762fa0a96b401e4b6985`.
- Runtime PGD consumido somente no último safe point fechado pré-U260: `df125bb64069ca87c614587d652c15634264f7bb`; U260 ativa não foi consumida nem preemptada.
- `pgd-rhgd-federation/1` preservado; `NO_DUPLICATE_RUNTIME=PASS`; `NO_SECOND_SCHEDULER=PASS`.
- PGA standalone está materializado; estado bootstrap obsoleto corrigido. MSGCD permanece composição agregadora, sem quarta autoridade.
- `repositorio=debianlima/rhgd` materializado; `release_alvo=v0.0.1` continua `standby_candidate`.
- `DELTA_INVENTORY=PASS`; `LEARNING_PRESERVED=PASS`; gates finais de fechamento/catalogação ainda pendentes.

## Fechamento U-RHGD-07
- implementação reconciliada em `5ebf217cdbd24acdbdb8d916e056b11253f0c66b`;
- catálogo do núcleo em `130438da8db2bb10617b6d4bffe05d8678825999`, com `pgd-project@0.2.0` e `rhgd-project@0.0.6`;
- `RECONCILIATION_CLOSURE=PASS`; `DEPENDENCY_REFERENCES=PASS`; `CATALOGO_SKILLS=PASS`; `SYNC_GUARD=PASS`;
- `trabalho_compartilhado` liberado; RHGD permanece `standby_candidate` e nenhuma tag/release foi promovida.

## LAT-02-RHGD-COGNITIVE-SCHEDULER-SEMANTIC-DEBT — PASS
- `FederatedDestinationMatcher` é o tipo canônico; `CognitiveScheduler` é somente alias legado.
- contrato TDD: falhou antes da implementação (`NameError`) e passou depois.
- regressão: `python -m unittest discover -s tests -p test_*.py` = 28/28 PASS.
- `RHGD_U07_PGH2_CORE_RECONCILIATION=PASS`; `RHGD_PROJECT_VERIFY=PASS`; `git diff --check=PASS`.
- `NO_SECOND_SCHEDULER=PASS`; ownership de admission/fila/lease/scheduler/retry/recovery/runtime permanece PGD.
- skill de projeto promovida por evidência local para `rhgd-project@0.0.7`; catálogo deve ser atualizado no mesmo turno antes do fecho recursivo PGH.
- telemetria específica de abertura LAT-02 não foi registrada pelo commit de reserva e não é fabricada retroativamente; a unidade superior PGH U269 possui `telemetria_inicio=2026-09-01T18:00:40Z`.
- `telemetria_fim=2026-09-01T18:05:04Z`; `trabalho_compartilhado` liberado.

## U-RHGD-08-R1-SUITE-PROTOCOL-CONCILIATION — PASS
- contrato estrutural RHGD avançado para `versao_contrato=2`; release permanece `0.0.1 / STANDBY_CANDIDATE` e nenhuma tag foi promovida.
- safe points consumidos: PGH U278 `1832fa24375a1e2f3cc207b163f1a42d0acc2042`; PGD `fa63a046e79e28d512dd901c43629d47a5bdea89`; PGA `5d1dfd93b0525db26b44efaea8bdbc56f25c185c`; Control Plane U280 `9408814f4af6b73c743b0dc35661caee0da5adca` + SHA-256 de `context-sync`.
- owners concorrentes observados e não consumidos: Control Plane U281 e PGH U282. O safe point U280 permaneceu ancestral do HEAD observado e `context-sync` permaneceu byte-idêntico.
- `DELTA_INVENTORY=PASS`; `LEARNING_PRESERVED=PASS`; `AUTHORITY_BOUNDARY=PASS`; `NO_SECOND_SCHEDULER=PASS`; `EXTERNAL_REFS=PASS`; `RHGD_U08_SUITE_PROTOCOL_CONCILIATION=PASS`; U07 histórica PASS; regressão `28/28 PASS`; `RHGD_PROJECT_VERIFY=PASS`.
- catálogo: `rhgd-project@0.0.8` publicado para a **próxima unidade**, com `CATALOGO_SKILLS=PASS`, `SYNC_GUARD=PASS`, `GLOBAL_PGH_SKILL_CANDIDATE_LINES=PASS`; plano congelado desta U08 permaneceu `rhgd-project@0.0.7`.
- aprendizado homologado: capability snapshot (`NodeCapability` em memória ou HMM read-only) não equivale a capability discovery vivo; PGD U14 atravessa zona heterogênea por RHGD sem transferir WCB/runtime/scheduler.
- maturidade: federação contratual `PASS`; matcher determinístico local `PASS_LOCAL`; capability discovery vivo `NOT_VERIFIED`; federação/rede real `NOT_VERIFIED`; produção `BLOCKED`; TEE/attestation e adapters upstream continuam opcionais nesta unidade.
- `RECONCILIATION_CLOSURE=PASS` para o escopo U08 pinado; `DEPENDENCY_REFERENCES=PASS` para as referências consumidas. Owners ativos posteriores não são promovidos silenciosamente.
- `telemetria_inicio=2026-09-02T03:57:59.791622Z`; tokens/custo `indisponivel`; `telemetria_fim` é emitida como último evento executável do turno após publicação do fechamento.
- `trabalho_compartilhado` liberado no commit de fechamento; nenhuma implementação de runtime RHGD foi alterada nesta unidade.
