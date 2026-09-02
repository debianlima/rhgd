# Fronteiras normativas da metacamada

| Camada | Possui | Não possui |
|---|---|---|
| PGA | política, autoridade, prioridade estratégica, evolução de GovernedObject, snapshots imutáveis | worker, heartbeat, fila, lease, scheduler |
| PGH | KnowledgeObject, competência, contexto, proveniência, autorização semântica, evidência | scheduler, ResourceLease, estado vivo |
| PGD | WorkSession, DAG, `ExecutionQueue`/TaskQueue, ResourcePool/Lease, worker, heartbeat, retry, relocation, Outcome/Efficacy | expansão de autoridade, homologação automática de conhecimento |
| RHGD | federação P2P, anúncio/descoberta de capacidade, `EnvelopeTransportQueue` ingress/egress, ordem/ACK/replay de ContextEnvelope, transporte interdomínio, confiança/attestation, adapters de mercado/settlement | política organizacional, homologação cognitiva, `ExecutionQueue` PGD, lease ou scheduler duplicado |
| MSGCD | visão agregada/painel | autoridade independente |

Regra de composição: **PGA governa; PGH autoriza e contextualiza; PGD agenda/executa; RHGD federa; MSGCD agrega.**

RHGD deve permanecer uma extensão federativa e não um segundo PGD. Se uma função já pertence ao runtime PGD (`ExecutionQueue`, lease, retry, scheduler), RHGD referencia o contrato PGD. `EnvelopeTransportQueue` é RHGD: controla put/get/remove, ordem e ACK do transporte, sem criar assignment ou autoridade de execução.
