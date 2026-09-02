# Estado — 2026-09-02 — contrato v7

Release: `0.0.1 / STANDBY_CANDIDATE`.

## Decisões vigentes
- Fronteira da suíte: PGA governa política/prioridade; PGH contextualiza/autoriza; PGD agenda/executa; RHGD federa/distribui; MSGCD agrega.
- PGA standalone está materializado como protocolo/política sem runtime próprio.
- MSGCD permanece composição agregadora/unified view, sem autoridade runtime independente.
- `ExecutionQueue` pertence exclusivamente ao PGD: admission, assignment, lease/fence, scheduler, retry/recovery e runtime state não são autoridade RHGD.
- `EnvelopeTransportQueue` pertence ao RHGD: lanes ingress/egress independentes, ordem monotônica por peer/stream, buffer de reordenação, `put/get/remove`, ACK e retenção para retry de transporte.
- Todo frame RHGD de `ContextEnvelope` exige `authorization_ref` PGH e `pgd_execution_ref` emitido por `pgd-rhgd-federation/1`; RHGD não cria execution ref, lease ou assignment.
- Capability discovery vivo RHGD usa explicit join, `boot_id`, sequência monotônica, TTL e rejeição de stale/replay; advertisement é read-only e não confere scheduler/lease/assignment.
- `FederatedDestinationMatcher` escolhe destino federado elegível, mas não é scheduler; `CognitiveScheduler` permanece apenas alias legado.
- Provider HEAD drift sem mudança nos artefatos consumidos, com ancestry e ausência de path semântico alterado, não exige reconciliação funcional; divergência falha fechado.
- Consumidores downstream seguem o último safe point fechado, não HEAD em curso. Owner ativo stale é detectado e não é preemptado.
- Rede permanece private-by-default com adesão explícita; anúncio nunca carrega segredo.
- Evidência histórica é imutável e deve ser replayada no snapshot que a produziu.

## Decisões superadas
- A formulação genérica “RHGD não possui fila” foi substituída por duas classes: `ExecutionQueue=PGD` e `EnvelopeTransportQueue=RHGD`.
- O item intermediário U12 `pgd_assignment_ref` foi substituído por `pgd_execution_ref`, campo federation-facing realmente exposto pelo contrato PGD.

## Decisões humanas pendentes
- Nenhuma para a U-RHGD-12.

## Decisões fechadas nesta emenda
- O operador decidiu que RHGD distribui contexto entre works/modelos e controla ordem e fila assimétrica de envio/recebimento, incluindo colocar, obter, confirmar e retirar envelopes, sem assumir scheduler/lease PGD.

## Pendências técnicas não humanas
- Coleta automática de capabilities reais de produção: `NOT_VERIFIED`; a homologação U12 usou valores `test_declared`.
- Autenticação própria de aplicação dos endpoints RHGD: `NOT_IMPLEMENTED`; a prova atual usa autenticação da overlay WireGuard.
- Serviço/daemon persistente: `NOT_VERIFIED`.
- Reconnect/failover real com idempotência após reinício de processo: `NOT_VERIFIED`.
- Fence/lease PGD observado end-to-end durante execução real de modelo: `NOT_VERIFIED`.
- Produção: `BLOCKED` até os gates anteriores e observabilidade independente serem homologados.
- PGH core U282 permanece externo ao RHGD, `BLOCKED_EXTERNAL_SAFE_POINT`, ainda pinando o snapshot RHGD antigo; sua zona pertence ao owner ativo e não é alterada aqui.

## Trabalho compartilhado
- `manifesto.yaml.trabalho_compartilhado`: vazio após o fechamento da U-RHGD-12.

## Competências ativas nesta unidade
- `rhgd-project@0.0.10` — versão congelada usada para gerar/homologar a U12.
- `desenvolvedor-de-software@15` — método de trabalho de projeto.
- `github-incremental-reconciliation@7` — reconciliação incremental/release.
- `governanca-ontologica-de-skills@1.0.5` — atualização governada de skill/catálogo.
- `telemetry-data-visualization@2` — macro global de telemetria.
- `distributed-agent-control@1` — TTL/stale/replay/idempotência de integração distribuída.
- `network-ssh-operations@1` — rota/porta/peer/rollback da homologação de rede.

## Competências instaladas para unidades futuras
- `rhgd-project@0.0.12` — substitui `0.0.11`; aprende discovery vivo e `EnvelopeTransportQueue`, usando `pgd_execution_ref` provider-backed.
- Catálogo sincronizado em `77761f2ac7ec3452cfb5c8d69c1d7e58027d760a`.

## Falhas de portão por tipo de entrada
- `backend-integracao`: 2 TDD reds esperados por módulo ausente e 1 divergência de provider-ref detectada/corrigida (`pgd_assignment_ref` -> `pgd_execution_ref`).
- `rede/homologacao`: 1 race de startup de listener e 1 listener externo transitório `18762`; nenhum estado persistente foi alterado e ambos os baselines terminaram `INTEGRO`.
- `reconciliacao-historica`: 1 tentativa de checkout completo bloqueada por espaço; replay refeita com clones locais `--shared` mínimos e PASS.

## Divergências da última reconciliação
- corrigidas: evidência U12 e Project-Skill substituíram `pgd_assignment_ref` por `pgd_execution_ref`; skill avançou `0.0.11 -> 0.0.12`; catálogo e hash canônico foram atualizados; listener transitório `18762` desapareceu sem intervenção; regras/listeners temporários U12 foram removidos.
- pendentes de autorização: nenhuma no repositório RHGD. O U282 externo continua sob owner próprio e não é tocado.
- `DELTA_INVENTORY=PASS`; `LEARNING_PRESERVED=PASS`.

## Homologação U-RHGD-12
- discovery bidirecional real em dois peers da overlay: PASS; sequência `1 -> 2`; TTL/stale rejection: PASS.
- transporte bidirecional real de dois `ContextEnvelope` por sentido: PASS; ordem `1,2`; ACK antes de remover egress: PASS; get/remove ingress: PASS.
- capacidades assimétricas homologadas: `2/5`, `3/7` e `5/3`.
- `PGD_EXECUTION_REF_PROVIDER_CONTRACT=PASS`; hash `pgd-rhgd-federation/1` = `3135f6cee8de163d55c9782b1b1de300359a0e2936f79f2a243a03941fefdc52`.
- evidência provider-aligned: `e729bac705a59bcb8ac9ff9e2e2360673aec4322`.
- implementação provider-aligned: `397e03821954ebeb88780b6658efec95ecb095b7`.
- Project-Skill produzida para a próxima unidade: `rhgd-project@0.0.12`, commit `98f44fb812e4726d12a3c7bb154c15048eee91e0`.
- U11 PASS; U09 PASS; U08 replay histórico PASS; U07 PASS; unitários `37/37 PASS`; `RHGD_PROJECT_VERIFY=PASS`.

## Entradas aceitas
- `1-59`.

## Próxima unidade
- U-RHGD-13: persistência + reconnect/idempotência real do `EnvelopeTransportQueue`, preservando `pgd_execution_ref`, explicit join e nenhuma autoridade de execução RHGD.
