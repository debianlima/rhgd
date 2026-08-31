# Fronteiras normativas da metacamada

| Camada | Possui | Não possui |
|---|---|---|
| PGA | política, autoridade, prioridade estratégica, evolução de GovernedObject, snapshots imutáveis | worker, heartbeat, fila, lease, scheduler |
| PGH | KnowledgeObject, competência, contexto, proveniência, autorização semântica, evidência | scheduler, ResourceLease, estado vivo |
| PGD | WorkSession, DAG, TaskQueue, ResourcePool/Lease, worker, heartbeat, retry, relocation, Outcome/Efficacy | expansão de autoridade, homologação automática de conhecimento |
| RHGD | federação P2P, anúncio/descoberta de capacidade, transporte interdomínio, confiança/attestation, adapters de mercado/settlement | política organizacional, homologação cognitiva, scheduler duplicado |
| MSGCD | visão agregada/painel | autoridade independente |

Regra de composição: **PGA governa; PGH autoriza e contextualiza; PGD agenda/executa; RHGD federa; MSGCD agrega.**

RHGD deve permanecer uma extensão federativa e não um segundo PGD. Se uma função já pertence a PGD (fila, lease, retry, scheduler), RHGD referencia o contrato PGD.
