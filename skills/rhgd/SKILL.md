---
name: rhgd-project
versao: 0.0.3
description: Skill de projeto da RHGD Fase 0 para federacao de trabalho cognitivo heterogeneo governado.
tipo_competencia: projeto
---
# RHGD Project Skill

## Missão
Materializar a camada federativa sem duplicar PGD: descobrir capacidades externas, transportar WorkUnits autorizadas, preservar privacidade/proveniência e suportar redução hierárquica.

## Fronteiras
PGA governa; PGH contextualiza/autoriza; PGD agenda/executa; RHGD federa; MSGCD agrega.

## Regra de implementação
Começar por contratos e adapters. Sem blockchain no caminho crítico, sem token na Fase 0, sem segredo no projeto, sem model-parallel remoto como pressuposto.

## 4B/16K
Uma competência detalhada por etapa; microcontexto; saída contratual; memória condensada; expansão selected -> adjacent -> global mediante insuficiência.

## Adapter PGD
`pgd-rhgd-federation/1` é a fronteira federation-facing. RHGD descobre capacidade e transporta WorkUnits autorizadas; PGD mantém admission, fila, lease, scheduler, retry, recovery e estado runtime. `authorization_ref` PGH é obrigatório; lease solicitado não é concessão. Resultado retorna `observed`.

## Redução determinística
Redução hierárquica deve ser independente da ordem de chegada. Canonicalizar identidade textual antes de deduplicar; ordenar conteúdo lógico e provenance por chave estável. `fan_in` pode alterar `depth`, nunca claims/evidence/dissent/sources finais.
