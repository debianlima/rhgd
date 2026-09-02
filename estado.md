# Estado — 2026-09-02 — contrato v8

Release: `0.0.1 / STANDBY_CANDIDATE`.

## Decisões vigentes
- Fronteira da suíte: PGA governa política/prioridade; PGH contextualiza/autoriza; PGD agenda/executa; RHGD federa/distribui; MSGCD agrega.
- PGA standalone está materializado como protocolo/política sem runtime próprio.
- MSGCD permanece composição agregadora/unified view, sem autoridade runtime independente.
- `ExecutionQueue` pertence exclusivamente ao PGD: admission, assignment, lease/fence, scheduler, retry/recovery e runtime state não são autoridade RHGD.
- `EnvelopeTransportQueue` pertence ao RHGD: lanes ingress/egress independentes, ordem por peer/stream, buffer de reordenação, `put/get/remove`, ACK e retenção para retry de transporte.
- `EnvelopeTransportQueue` durável usa estado local transacional; no receptor, `put_inbound` precisa persistir antes do ACK. Configuração persistida divergente falha fechado.
- Na janela ACK-remoto/remoção-local, restart do emissor pode reter o envelope; retry idêntico vira `DUPLICATE`. Após consumo persistido, replay idêntico após restart vira `ALREADY_CONSUMED`; replay conflitante é rejeitado.
- Todo frame RHGD exige `authorization_ref` PGH e `pgd_execution_ref` emitido por `pgd-rhgd-federation/1`; RHGD não cria execution ref, lease ou assignment.
- Capability discovery vivo usa explicit join, `boot_id`, sequência monotônica, TTL e rejeição stale/replay; anúncio permanece read-only.
- Provider HEAD drift sem mudança dos artefatos consumidos, com ancestry e ausência de path semântico alterado, não exige reconciliação funcional.
- Consumidores downstream seguem o último safe point fechado; owner ativo stale é detectado e não é preemptado.
- Rede permanece private-by-default com adesão explícita; anúncio/envelope nunca carregam segredo operacional.
- Evidência histórica é imutável e deve ser replayada no snapshot que a produziu.

## Decisões superadas
- “RHGD não possui fila” foi substituído por `ExecutionQueue=PGD` e `EnvelopeTransportQueue=RHGD`.
- O item intermediário `pgd_assignment_ref` foi substituído por `pgd_execution_ref`, campo federation-facing realmente exposto pelo PGD.
- A fila U12 puramente em memória foi superada pela opção U13 durável; a semântica de transporte permanece a mesma.

## Decisões humanas pendentes
- Nenhuma para a U-RHGD-13.

## Decisões fechadas nesta emenda
- `DurableEnvelopeQueue` persiste estado RHGD em SQLite `WAL + synchronous=FULL` antes de confirmar mutações.
- Restart/reconnect real foi homologado nos dois sentidos da overlay: pendente sobrevive ao restart, retry vira `DUPLICATE`, sequência seguinte permanece ordenada e replay consumido vira `ALREADY_CONSUMED`.

## Pendências técnicas não humanas
- Power-loss/hard-crash de máquina: `NOT_VERIFIED`; U13 provou restart de processo e reconexão real.
- Daemon supervisionado/persistente de produção: `NOT_VERIFIED`; existe daemon executável, mas não foi instalado como serviço permanente.
- Autenticação própria de aplicação dos endpoints RHGD: `NOT_IMPLEMENTED`; a prova usa autenticação da overlay WireGuard.
- Coleta automática de capabilities reais de produção: `NOT_VERIFIED`; U12 usou valores `test_declared`.
- Fence/lease PGD observado end-to-end durante execução real de modelo: `NOT_VERIFIED`.
- Observabilidade independente de produção: `NOT_VERIFIED`.
- Produção: `BLOCKED` até os gates anteriores serem homologados.
- PGH core U282 permanece externo, `BLOCKED_EXTERNAL_SAFE_POINT`, ainda pinando RHGD antigo e sob `terminal-oracle`; sua zona não foi tocada.

## Trabalho compartilhado
- `manifesto.yaml.trabalho_compartilhado`: vazio após o fechamento da U-RHGD-13.

## Competências ativas nesta unidade
- `rhgd-project@0.0.12` — versão congelada usada para gerar/homologar U13.
- `desenvolvedor-de-software@15`.
- `github-incremental-reconciliation@7`.
- `governanca-ontologica-de-skills@1.0.5`.
- `telemetry-data-visualization@2`.
- `distributed-agent-control@1` — restart, replay, idempotência e fencing de estado distribuído.
- `network-ssh-operations@1` — rota/porta/overlay/rollback da homologação real.

## Competências instaladas para unidades futuras
- `rhgd-project@0.0.13` — persistência antes do ACK e reconnect/replay idempotente; commit `9e45a709dc500945536f54d2a659456b858de84b`.
- Catálogo sincronizado em `021d5a28dab09fc99aeebc9e096f08ad41a2086e`.

## Falhas de portão por tipo de entrada
- `backend-integracao`: 1 TDD red esperado por ausência de `DurableEnvelopeQueue`; depois 42/42 testes verdes.
- `rede/homologacao`: nenhuma falha final; listeners efêmeros e regra runtime-only foram removidos e os dois ambientes terminaram `INTEGRO`.
- `reconciliacao`: nenhuma divergência local restante; U282 continua pendência externa sob owner próprio.

## Divergências da última reconciliação
- corrigidas: skill `0.0.12 -> 0.0.13`, catálogo/índice atualizados e U13 fixada em evidência hashada; nenhuma regra/serviço temporário permaneceu.
- pendentes de autorização: nenhuma no RHGD.
- `DELTA_INVENTORY=PASS`; `LEARNING_PRESERVED=PASS`; `RECONCILIATION_CLOSURE=PASS`; `DEPENDENCY_REFERENCES=PASS`.

## Homologação U-RHGD-13
- implementação durável: `631eca6d89888ff1cdd0c88025f0bfbd291d5ea0`.
- evidência de restart/reconnect: `152901345be7d514dbfcb87b1db47820e64300cb`.
- WireGuard→IPsec: `1` inicialmente `ACCEPTED`, após restart/retry `DUPLICATE`; `2` `ACCEPTED`; após consumo+restart, `1,2` = `ALREADY_CONSUMED`.
- IPsec→WireGuard: mesma sequência e os mesmos estados de idempotência.
- sender e receiver preservaram ordem `1,2`; próxima sequência do emissor após restart = `3`.
- IDs enviados por cada peer são exatamente os IDs consumidos pelo outro; `pgd_execution_ref` permaneceu estável.
- `TEMP_NETWORK_CHANGE_ROLLBACK=PASS`; WireGuard `INTEGRO`; IPsec `INTEGRO`.
- U13 PASS; U12 PASS; U11 PASS; U09 PASS; U08 histórico PASS; U07 PASS; unitários `42/42 PASS`; `RHGD_PROJECT_VERIFY=PASS`.

## Entradas aceitas
- `1-65`.

## Próxima unidade
- U-RHGD-14: autenticação de aplicação + daemon supervisionado/observabilidade, mantendo explicit join, persist-before-ACK e nenhuma autoridade de execução RHGD.
