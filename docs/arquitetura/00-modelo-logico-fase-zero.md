# RHGD — modelo lógico Fase 0

## Princípio fundador
**Distribuir trabalho semântico antes de distribuir operação numérica.**

A RHGD não implementa model-parallel tensor-a-tensor pela Internet como caminho padrão. PGH decompõe tarefas em unidades cognitivas semanticamente fechadas; PGD mantém DAG, fila, lease, execução e recovery; RHGD descobre/federa executores externos e transporta unidades; PGA governa política/evolução; MSGCD agrega a visão.

## Fluxo
`UserRequest -> ContextPreOrchestrator -> RecursiveCognitiveDAG -> WorkUnit -> CapabilityDiscovery -> PGD lease/execution -> CognitiveResult -> HierarchicalReducer -> OutcomeEvidenceEnvelope -> PGH reconciliation -> local finalization`.

## Objetos Fase 0
- `NodeIdentity`
- `ExecutorCapabilityProfile`
- `ResourceAdvertisement`
- `KnowledgeAdvertisement`
- `SkillAdvertisement`
- `PrivacyClass`
- `TrustProfile`
- `ContextEnvelope`
- `DistributedWorkUnit`
- `ExecutionOffer`
- `ExecutionLease`
- `ExecutionEvidence`
- `CognitiveResult`
- `ReductionEnvelope`
- `HumanPreferenceEvidence`
- `KnowledgeContribution`

## Recursão
WorkUnit pode ser novamente decomposta somente quando o envelope autorizar. A delegação carrega profundidade restante, orçamento, deadline, máximo de nós, escopo de autorização e classe de privacidade. Autoridade nunca cresce por delegação.

## Redução
A redução é hierárquica e contratual. Deve preservar consenso, dissenso, evidência, incerteza e proveniência. Redutor não é mero sumarizador.

## 4B/16K
Executor pequeno recebe uma competência detalhada por vez, contexto da unidade, contrato de saída e memória condensada. Expansão global é solicitada ao pré-orquestrador; catálogo integral não é despejado no prompt.
