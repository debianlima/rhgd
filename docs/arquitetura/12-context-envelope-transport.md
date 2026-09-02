# U-RHGD-12 — distribuição de ContextEnvelope e fila assimétrica

A decisão humana desta unidade corrige a ambiguidade histórica do termo **fila**.

- **ExecutionQueue**: fila de execução de WorkUnit, admission, assignment, lease, retry/recovery e scheduler. Continua exclusivamente **PGD**.
- **EnvelopeTransportQueue**: fila de transporte de `ContextEnvelope` entre peers/works/modelos. É responsabilidade **RHGD**.

Portanto `NO_DUPLICATE_PGD_RUNTIME` não significa “RHGD não pode enfileirar nada”; significa “RHGD não pode criar uma segunda ExecutionQueue”.

## Fluxo conciliado

```text
PGH cria/autoriza ContextEnvelope
        |
        v
PGD confirma assignment/lease/fence de execução
        |
        | pgd_assignment_ref
        v
RHGD EnvelopeTransportQueue EGRESS
  put -> ordem monotônica por peer -> get/peek
        |
        | transporte federado
        v
RHGD EnvelopeTransportQueue INGRESS
  buffer de reordenação -> get -> modelo/work -> remove
        |
        v
resultado/envelope de retorno faz o caminho inverso
```

A retirada do egress só ocorre depois de ACK remoto. Falha de envio mantém o envelope para retry. No ingress, frames fora de ordem ficam bufferizados e só o próximo `sequence` esperado é entregue; a remoção ocorre após o consumidor local obter o envelope.

Cada frame exige `authorization_ref` PGH e `pgd_assignment_ref`. RHGD não cria assignment, não concede lease e não decide admission. A fila controla **ordem de transporte**, não ordem de execução.

## Assimetria

Ingress e egress possuem capacidades independentes por nó. Na homologação real foram usados deliberadamente pares diferentes (`2/5`, `3/7` e `5/3`) para provar que envio e recebimento não dependem de uma fila simétrica única.

## Homologação real

Dois `ContextEnvelope` foram enviados em cada sentido sobre a overlay real. Nos dois sentidos:

1. `put_outbound` criou sequências `1,2`;
2. o peer remoto respondeu `ACK ACCEPTED` para `1,2`;
3. o emissor removeu cada item somente após o ACK;
4. o receptor observou `1,2` na mesma ordem;
5. o receptor executou `get_inbound` e `remove_inbound` e terminou com ingress vazio.

Isso prova o mecanismo de distribuição/ordenação/put/get/remove. Ainda não prova daemon persistente, reconnect real com processo reiniciado nem fence PGD end-to-end em execução de modelo; esses gates permanecem abertos antes de produção.
