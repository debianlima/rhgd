# U-RHGD-12 — capability discovery vivo

A U12 substitui a lacuna observada em U08: `NodeCapability` em memória continua válido como snapshot local, mas agora existe um mecanismo vivo de anúncio/consulta entre peers explicitamente aderidos.

## Contrato

`rhgd-live-capability/1` publica somente observação read-only: identidade lógica do peer/boot, `sequence`, `issued_at_ms`, `expires_at_ms`, capabilities declaradas e a fronteira `scheduler=false`, `lease_grant=false`, `assignment=false`.

A sequência cresce a cada leitura. Snapshot expirado é rejeitado. Replay/regressão de sequência no mesmo boot é rejeitado. Peer não aderido explicitamente é rejeitado pelo registry.

## Homologação em dois peers reais

O mecanismo foi executado nos perfis `terminal-wireguard` e `terminal-ipsec` sobre a overlay WireGuard real. Cada lado observou o outro com sequências `1 -> 2`, TTL de 2 s e autoridade read-only. Um snapshot capturado foi reutilizado depois do TTL e rejeitado como stale.

A abertura necessária no firewall do peer IPsec foi runtime-only, restrita ao peer de teste e às portas de laboratório, com timeout; foi removida ao final e o verificador residente voltou a `INTEGRO`.

## Limite da prova

Os valores anunciados foram `test_declared`, não coleta automática de GPU/model/runtime de produção. A overlay fornece autenticação de peer no transporte WireGuard, mas o endpoint RHGD ainda não possui autenticação própria de aplicação nem serviço persistente. Portanto `LIVE_DISCOVERY_MECHANISM=PASS`, mas produção continua `BLOCKED`.
