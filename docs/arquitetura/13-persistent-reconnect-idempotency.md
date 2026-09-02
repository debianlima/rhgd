# U-RHGD-13 — persistência, reconnect e idempotência de ContextEnvelope

A U13 torna durável a `EnvelopeTransportQueue` introduzida na U12 sem alterar a fronteira de autoridade: `ExecutionQueue`, admission, assignment, lease/fence e scheduler continuam PGD.

## Persistência

`DurableEnvelopeQueue` usa SQLite local com `journal_mode=WAL` e `synchronous=FULL`. O estado persistido contém exclusivamente o estado de transporte: lanes egress/ingress, próxima sequência, stream ativo, envelopes pendentes e identidade das sequências já consumidas. A configuração (`local_peer_id`, explicit joins, capacidades e `stream_id`) faz parte do snapshot e divergência ao reabrir falha fechado.

Toda mutação é persistida antes de retornar. No receptor isso significa: `put_inbound` conclui a transação antes de `EnvelopeTransportService.receive()` produzir o ACK HTTP. Se a persistência falhar, o estado em memória volta ao snapshot anterior e o ACK não é emitido como sucesso.

## Restart/reconnect idempotente

O caso crítico testado nos dois sentidos foi:

1. emissor faz `put_outbound(sequence=1)` em storage durável;
2. receptor persiste o frame e responde `ACCEPTED`;
3. o teste deliberadamente não executa `remove_outbound`, representando a janela em que o ACK remoto chegou mas o emissor ainda mantém o envelope;
4. emissor e receptor são reiniciados, cada um reabrindo o mesmo SQLite;
5. o emissor reenvia `sequence=1`; receptor responde `DUPLICATE`, sem nova inserção;
6. egress remove `sequence=1` após o ACK e envia `sequence=2`, que recebe `ACCEPTED`;
7. receptor entrega/retira `1,2` em ordem e persiste as identidades consumidas;
8. após novo restart, replay de `1,2` retorna `ALREADY_CONSUMED`.

Isso foi executado WireGuard→IPsec e IPsec→WireGuard. Os IDs enviados por cada lado são exatamente os IDs consumidos pelo outro, e `pgd_execution_ref` atravessa todos os restarts sem ser reemitido ou recriado pelo RHGD.

## O que a prova não afirma

Os restarts foram de processo e reconexão real na overlay. A U13 não afirma power-loss/hard-crash de máquina, não instala daemon supervisionado de produção, não adiciona autenticação própria de aplicação e não prova lease/fence PGD durante execução real de modelo. Esses itens continuam gates separados antes de produção.
