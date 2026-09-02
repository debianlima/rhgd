# U-RHGD-09 — freshness de consumidores downstream

Esta unidade transforma em gate mecânico a situação observada após U-RHGD-08: o RHGD fechou o safe point `13b6e0aadcb59902312915130d1bc6cd2bc81fd4`, mas o consumidor PGH **U282** ainda observa `ee24a3916e964c7ec624b666daa035aa6f4e97c5`.

## Regra

Consumidor downstream segue o **safe point fechado** do produtor, não o HEAD de uma unidade do produtor em andamento. O HEAD RHGD observado durante U09 é `6c8b3b83a5a1156bb555608af8821081568e9eb4`, porém o alvo correto para U282 permanece `13b6e0aadcb59902312915130d1bc6cd2bc81fd4`.

## Classificação observada

- consumidor: `debianlima/protocolo-governanca-heterogenea`;
- unidade: `U282-PGH-SUITE-POST-U278-FIXED-POINT-REFRESH`;
- core HEAD observado: `1d26328a34a5dd598cb77b1bd53f470cfea84070`;
- pin RHGD observado: `ee24a3916e964c7ec624b666daa035aa6f4e97c5`;
- classificação: **`BLOCKED_ACTIVE_OWNER_STALE`**;
- owner ativo: `terminal-oracle` até `2026-09-02T05:39:31Z`;
- mutação pelo RHGD: **proibida**.

A ação correta é **não editar** a zona U282. O owner deve reconciliar o novo safe point RHGD dentro da própria unidade, ou após liberar sua zona. Até isso acontecer, `DOWNSTREAM_SYNCHRONIZED=NO` e nenhum fixed point da suíte pode ser apresentado como atual.

## Efeito sobre maturidade

U09 não promove RHGD e não executa rede. `0.0.1 / STANDBY_CANDIDATE` permanece inalterado; discovery vivo, federação real e produção continuam fora do escopo desta unidade.
