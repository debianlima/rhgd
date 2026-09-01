# U-RHGD-07 — reconciliação RHGD com o núcleo PGH 2.0

Esta unidade reconcilia a RHGD candidata com os módulos canônicos do núcleo sem promover release e sem consumir estado transitório de runtime.

## Pins consumidos

- **PGH 2.0**: `304b9914ae44b0ac4240d912bd81f7be87d5a708` — raiz de conhecimento, contratos, evidência e autorização semântica.
- **PGD 1.0**: `3f7d70e974271a0ee316df9425d5e955225fddd4` — runtime, scheduler, queue, lease, retry e recovery.
- **PGA 1.0**: `c151e58adf05339eee7f762fa0a96b401e4b6985` — política, autoridade e governança; sem runtime próprio.
- **runtime PGD canônico**: `df125bb64069ca87c614587d652c15634264f7bb`, último safe point fechado antes da unidade U260 atualmente ativa no control plane.
- **MSGCD**: composição/visão agregadora do PGH; não exige repositório standalone e não se torna quarta autoridade.

## Fronteira reconciliada

**PGA governa; PGH autoriza/contextualiza; PGD agenda/executa; RHGD federa; MSGCD agrega.**

O contrato `pgd-rhgd-federation/1` continua sendo a fronteira federation-facing. RHGD pode descobrir capacidade, selecionar destino federado segundo política recebida e transportar WorkUnits autorizadas. Admission, fila, ResourceLease, ReservationToken, scheduler, retry, recovery e estado runtime continuam no PGD. A RHGD opera **sem segundo scheduler**.

## Deltas corrigidos

O bootstrap RHGD dizia que o PGA standalone ainda não estava materializado. Isso ficou obsoleto: PGA está materializado e reconciliado no head acima. O manifesto também mantinha apenas `repositorio_planejado`; o repositório remoto `debianlima/rhgd` já existe e passa a ser declarado como `repositorio`.

A release RHGD permanece `standby_candidate` em `0.0.1`. Esta unidade não cria tag, não promove release e não altera as tags históricas PGH/PGD/PGA.
