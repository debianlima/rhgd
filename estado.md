# Estado — 2026-09-02 — contrato v8

Release: `0.0.1 / STANDBY_CANDIDATE`.

## Decisões vigentes
- Fronteira da suíte: PGA governa política/prioridade; PGH contextualiza/autoriza; PGD agenda/executa; RHGD federa/distribui; MSGCD agrega.
- PGA standalone está materializado como protocolo/política sem runtime próprio.
- MSGCD permanece composição agregadora/unified view, sem autoridade runtime independente.
- `ExecutionQueue` pertence exclusivamente ao PGD: admission, assignment, lease/fence, scheduler, retry/recovery e runtime state não são autoridade RHGD.
- `EnvelopeTransportQueue` pertence ao RHGD e permanece somente fila de transporte: ingress/egress, ordem por peer/stream, persist-before-ACK, retry e idempotência.
- Todo frame RHGD exige `authorization_ref` PGH e `pgd_execution_ref` já emitido por `pgd-rhgd-federation/1`; RHGD não cria execution ref, lease ou assignment.
- Autenticação de aplicação usa HMAC-SHA256 vinculada a método/path/key/peer/timestamp/nonce/body; peer precisa estar explicitamente aderido.
- Anti-replay é persistente, mas persiste somente `SHA256(nonce)`; segredo e nonce em claro não entram no banco.
- Observabilidade de transporte expõe somente contadores, queue depth e timestamps; payload, assinatura e segredo não entram nas métricas; `/rhgd/metrics` exige autenticação.
- Definição systemd endurecida prova configuração de supervisão, não runtime persistente observado. `LIVE_SUPERVISED_SERVICE_RUNTIME=NOT_OBSERVED` até uma unidade de deploy/runtime real.
- Paralelismo do harness U14 é capacidade do executor de teste, não scheduler RHGD.
- Capability discovery vivo mantém explicit join, sequência monotônica, TTL e rejeição stale/replay; anúncio permanece read-only.
- Consumidores downstream seguem o último safe point fechado; evidência histórica permanece imutável.

## Decisões superadas
- “RHGD não possui fila” foi substituído por `ExecutionQueue=PGD` e `EnvelopeTransportQueue=RHGD`.
- `pgd_assignment_ref` foi substituído por `pgd_execution_ref` federation-facing.
- A fila U12 em memória foi superada pela U13 durável, preservando a mesma semântica de autoridade.
- “autenticação própria de aplicação NOT_IMPLEMENTED” foi superada pela U14: app-auth e anti-replay estão homologados.
- “observabilidade independente NOT_VERIFIED” foi superada pela U14 no escopo de métricas de transporte autenticadas/payload-free.

## Decisões humanas pendentes
- Nenhuma para U-RHGD-14.

## Decisões fechadas nesta emenda
- HMAC-SHA256 + explicit join + anti-replay persistente foram homologados sem persistência de segredo/nonce em claro.
- `/rhgd/envelope` e `/rhgd/metrics` foram exercitados com autenticação; mismatch de peer/source foi rejeitado.
- Métricas bounded/payload-free e autoridade `scheduler=false`, `lease_grant=false`, `admission=false` foram preservadas.
- `deploy/rhgd-envelope.service` foi homologado como definição endurecida de supervisão; runtime systemd real não foi inferido.
- Campanha `U14-W01..U14-W40` passou 40/40 com 4 slots físicos e `max_parallel_observed=4`.

## Pendências técnicas não humanas
- Power-loss/hard-crash de máquina: `NOT_VERIFIED`; U13 provou restart de processo/reconnect, não perda abrupta de host.
- Runtime systemd persistente real: `NOT_OBSERVED`; a U14 homologou daemon em processo de teste e definição do unit file.
- Coleta automática de capabilities reais de produção: `NOT_VERIFIED`; U12 usou valores `test_declared`.
- Fence/lease PGD observado end-to-end durante execução real de modelo: `NOT_VERIFIED`.
- Produção RHGD permanece `BLOCKED` enquanto os gates de runtime real acima não forem homologados.
- PGH U282 permanece unidade externa a ser reconciliada contra este novo safe point RHGD.

## Trabalho compartilhado
- `manifesto.yaml.trabalho_compartilhado`: vazio após o fechamento U-RHGD-14.

## Competências ativas nesta unidade
- `rhgd-project@0.0.13` — versão congelada usada para gerar/executar a campanha U14.
- `desenvolvedor-de-software@15`.
- `github-incremental-reconciliation@7`.
- `governanca-ontologica-de-skills@1.0.5`.
- `telemetry-data-visualization@2`.
- `distributed-agent-control@1` — auth/replay/persistência/fencing de fronteira distribuída.

## Competências instaladas para unidades futuras
- `rhgd-project@0.0.14` — aprendizado homologado U14 sobre app-auth, métricas payload-free e distinção supervisão definida vs runtime observado; commit `4032c6458429ec2c44bcf12286f976a8896d467c`.
- Catálogo sincronizado em `97e5b5f500299421e07b7e3ea79e5950c9881f98`.

## Falhas de portão por tipo de entrada
- `estrutura`: três artefatos U14 declarados estavam ausentes; materializados e o `RHGD_PROJECT_VERIFY` voltou a PASS.
- `reconciliacao`: nenhuma divergência RHGD restante após skill `0.0.13 -> 0.0.14` e catálogo sincronizado.
- `runtime-producao`: não executado nesta unidade; registrado explicitamente como `NOT_OBSERVED`, sem promoção indevida.

## Divergências da última reconciliação
- corrigidas: entradas 66–76 auditadas; verificador/evidência/documentação U14 materializados; skill 0.0.14 publicada; catálogo atualizado.
- pendentes de autorização: nenhuma no RHGD.
- `DELTA_INVENTORY=PASS`; `LEARNING_PRESERVED=PASS`; `RECONCILIATION_CLOSURE=PASS`; `DEPENDENCY_REFERENCES=PASS`.

## Homologação U-RHGD-14
- implementação/testes base: `c5113356e47e24ba2f2bcb34b02aa892cbc8b76e`.
- artefatos de fechamento: `82945163762f2352a52b6bb58ae87fcdbda8aa51`.
- aprendizado Project-Skill: `4032c6458429ec2c44bcf12286f976a8896d467c` (`rhgd-project@0.0.14`).
- catálogo: `97e5b5f500299421e07b7e3ea79e5950c9881f98`.
- app-auth/observabilidade focal: 5/5 PASS.
- campanha paralela: 40/40 PASS, 4 slots, zero falhas.
- regressão RHGD: 47/47 PASS.
- `RHGD_U14_APP_AUTH_SUPERVISION_OBSERVABILITY=PASS`; `RHGD_PROJECT_VERIFY=PASS`.
- `SUPERVISION_DEFINITION=PASS`; `LIVE_SUPERVISED_SERVICE_RUNTIME=NOT_OBSERVED`; `PRODUCTION=BLOCKED`.

## Entradas aceitas
- `1-76`.

## Próxima unidade
- Nenhuma nova entrada RHGD declarada após 76. Retornar ao fecho recursivo PGH U282 e consumir este safe point RHGD; qualquer novo trabalho RHGD exige nova entrada/reserva.
