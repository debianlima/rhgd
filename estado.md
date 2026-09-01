# Estado — RHGD 0.0.1 — Fase 0

Estado: `STANDBY_CANDIDATE`.

Materializado como repositório-zero local para consolidar arquitetura e políticas antes de qualquer homologação de rede real.

## Dependências normativas
- PGH 1.2 oficial + candidato PGH 2.0 como fonte de fronteiras em estudo.
- PGD standalone está materializado; U-PGD-05 publicou `pgd-rhgd-federation/1` em `abf929598c1eeb50fa09c90c3f039d4bc8bb1f79`. A implementação estável de referência permanece `pgh-distributed-session-control-plane:v2.3.2`.
- PGA standalone ainda não materializado no momento deste bootstrap; handoff PGA no PGH é fonte de fronteira.
- MSGCD é visão agregadora, não autoridade adicional.

## Não reivindicado
- rede P2P real;
- forks AntSeed/Gensyn/Akash;
- TEE/attestation homologado;
- settlement/blockchain;
- token;
- prova criptográfica completa de inferência;
- produção.

## Próximas unidades
1. contratos JSON Schema dos objetos Fase 0;
2. adapter PGH ContextEnvelope -> PGD WorkUnit — MATERIALIZADO em U-RHGD-01;
3. capability discovery mock/determinístico;
4. redução hierárquica com preservação de dissenso;
5. threat model e privacy gates;
6. adapters experimentais upstream somente após licença/pin/gates;
7. decisão de repositório remoto e publicação.

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
