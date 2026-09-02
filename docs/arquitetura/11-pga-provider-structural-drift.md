# U-RHGD-11 — drift estrutural do provider PGA

A U11 trata um caso diferente de U09. Aqui o provider **PGA** avançou de `5d1dfd93…` para `871f0294…`, mas os contratos e dados realmente consumidos pelo RHGD permaneceram byte-idênticos.

## Classificação

`HEAD_DRIFT_CONTRACTS_IDENTICAL`.

A unidade PGA que produziu o avanço foi **U-PGA-10**, uma reconciliação de fechamento estrutural. O delta do provider ficou limitado a:

- `dados/telemetria-unidades.jsonl`;
- `estado.md`;
- `manifesto.yaml`;
- `tests/verify_project.py`.

Os contratos `network-service-agents` e `deterministic-priority-policy`, assim como suas evidências U-PGA-08/U-PGA-09, mantiveram o mesmo hash SHA-256 antes e depois.

## Regra de consumo

O RHGD não deve tratar qualquer avanço de HEAD como mudança semântica. A validade semântica acompanha a identidade dos **artefatos efetivamente consumidos**, desde que a unidade prove também que nenhum caminho semântico relevante mudou e que o commit anterior é ancestral do novo.

Isso não reescreve U08: a evidência histórica continua pinada ao commit observado naquela unidade. Uma unidade futura pode usar o HEAD PGA `871f0294…` porque os artefatos consumidos permanecem idênticos.

A regra é fail-closed: se qualquer hash ou caminho de rede/prioridade divergir, `FUNCTIONAL_RECONCILIATION_REQUIRED` deixa de ser `NO` e uma nova reconciliação funcional precisa ser aberta.

## Autoridade e maturidade

A fronteira permanece: PGA governa política/prioridade e não runtime; RHGD federa e não agenda. A U11 não cria scheduler, não executa rede e não promove `0.0.1 / STANDBY_CANDIDATE`.
