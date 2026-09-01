# RHGD → PGD federation adapter

A unidade U-RHGD-01 materializa a fronteira operacional já prevista na Fase 0: `ContextEnvelope -> WorkUnit -> PGD`.

O adapter não implementa scheduler, fila, admission, lease, retry ou recovery. Ele transforma contexto autorizado e uma WorkUnit em `pgd-rhgd-federation/1`, publicado pelo PGD em `abf929598c1eeb50fa09c90c3f039d4bc8bb1f79`.

`authorization_ref` e `context_ref` são obrigatórios. O primeiro prova que a federação não cria autoridade; o segundo evita copiar contexto inteiro como identidade. `requested_lease_seconds` é intenção e somente o PGD pode conceder lease. O resultado volta como evidência `observed` e só o PGH pode homologá-lo como conhecimento.

A implementação estável mapeada continua `pgh-distributed-session-control-plane:v2.3.2` (`cfd68602a4491d61658f564b86d550f4b498f06f`). A candidata 3.0 não é autoridade desta unidade.

Nenhum delta de Core foi necessário: o PGH/U45 já representa autorização, referência viva e reconciliação incremental suficientes para esta fronteira.
