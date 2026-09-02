# U-RHGD-14 — autenticação de aplicação, supervisão e observabilidade

A U14 fecha as lacunas de autenticação de aplicação e observabilidade identificadas após U12/U13 sem alterar a fronteira de autoridade: RHGD continua transportando `ContextEnvelope`; PGD continua dono de `ExecutionQueue`, admission, lease, scheduler e runtime.

## Autenticação de aplicação

O transporte usa HMAC-SHA256 com `key_id`/peer explicitamente aderido e assinatura vinculada a método, path, timestamp, nonce e SHA-256 do corpo. Janela de relógio é limitada e replay é rejeitado por `PersistentNonceStore`. O banco persiste somente o SHA-256 do nonce; segredo e nonce em claro não são persistidos. Múltiplas chaves são suportadas e peer não aderido é rejeitado.

Os testes cobrem adulteração de body/assinatura/key/peer/path/method, timestamps stale/future, replay no mesmo processo e após reopen do banco, ausência de header, unicode e limite exato da janela temporal.

## Observabilidade

`TransportMetrics` publica somente contadores limitados, profundidade `egress`/`ingress`, timestamps e a fronteira `queue=envelope_transport_only`, `scheduler=false`, `lease_grant=false`, `admission=false`. Payload de `ContextEnvelope`, assinatura e segredo não entram no snapshot.

O endpoint `/rhgd/metrics` exige autenticação de aplicação. A campanha observou `401` sem autenticação e `200` com autenticação válida. O POST autenticado `/rhgd/envelope` respondeu `202/ACCEPTED`; mismatch entre peer autenticado e `source_peer` foi rejeitado com `403`.

## Supervisão

`deploy/rhgd-envelope.service` define reinício `on-failure`, `DynamicUser=yes`, `NoNewPrivileges=yes`, `ProtectSystem=strict`, `UMask=0077` e injeção do segredo por `LoadCredential`. O valor do segredo não aparece no unit file nem no projeto.

Esta unidade prova a **definição supervisionada e o daemon em processo de teste**, não uma instalação systemd de produção. Portanto `SUPERVISION_DEFINITION=PASS`, mas `LIVE_SUPERVISED_SERVICE_RUNTIME=NOT_OBSERVED` e produção permanece `BLOCKED` até uma unidade específica de deploy/runtime observar o serviço persistente real.

## Campanha paralela de 40 subunidades

A campanha final executou `U14-W01..U14-W40` em processos isolados, com `physical_slots=4`, `max_parallel_observed=4`, 40/40 PASS e zero falhas. Ela cobre auth/anti-replay, persistência segura, contadores e queue depth, endpoints HTTP, hardening do unit file, preservação de `pgd_execution_ref`, schemas e `NO_SECOND_SCHEDULER`.

Resultado observado: `PARALLEL_40=PASS`, `PHYSICAL_SLOT_BOUND=PASS`, `APPLICATION_AUTH=PASS`, `OBSERVABILITY=PASS`, `NO_SECOND_SCHEDULER=PASS`.

A evidência canônica está em `dados/rhgd-0.0.1/U-RHGD-14-app-auth-supervision-observability.yaml`.
