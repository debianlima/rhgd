# U-RHGD-04 — dissenso preservado

O RHGD já transportava `dissent`, mas a saída não distinguia “resultado com discordância” de “resultado pronto para colapso”. U-RHGD-04 torna essa diferença contratual.

Se qualquer nó declara dissenso, `collapse_allowed=false` e `resolution_status=DISSENT_PRESERVED`. Cada dissenso conserva `work_id`, `node_id`, `confidence` e identidade canônica. A ordenação continua independente de ordem de chegada e fan-in.

Esta unidade não interpreta linguagem natural como voto, verdade, maioria ou oposição semântica. Kappa/alpha e clustering só entram após contrato explícito de stance/classificação e conjunto de validação.
