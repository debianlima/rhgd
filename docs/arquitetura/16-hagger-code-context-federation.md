# U-RHGD-16 — Hagger Code Context Federation

A RHGD não se torna dona do Code-Graph-RAG e não cria um segundo runtime de execução. O PGH continua dono do contexto/skills; Git continua fonte executável; PGD continua dono de assignment, `ExecutionQueue`, lease, scheduler, retry e recovery. A RHGD recebe um `code_context_ref` já limitado pelo PGH, materializa uma consulta Hagger read-only quando o provider local está disponível e transporta o resultado no `ContextEnvelope` existente.

Fluxo:

`GitHub/ref -> SHA imutável -> índice Hagger por commit -> code_context_ref -> RHGD HaggerCodeContextAdapter -> subgrafo/snippet -> ContextEnvelope -> EnvelopeTransportQueue -> agente`

O adapter aceita somente `file://` dentro do `index_root` configurado e as operações `summary`, `resolve`, `definition`, `callers`, `callees`, `importers`, `implementors`, `overrides` e `tests-reaching`. A chamada ao query adapter usa argv, `shell=False`, stdin fechado, timeout e limite de saída. `write_file`, shell arbitrário, replace, rename, wipe/reset e Cypher arbitrário não entram na capability RHGD.

A resposta Hagger é aceita somente se `repo_ref`, `source_commit`, provider/version/commit, `manifest_sha256` e `source_dirty=false` corresponderem ao `code_context_ref`. Divergência é fail-closed; RHGD não substitui erro por contexto vazio.

O payload materializado usa `rhgd-hagger-code-context/1` e fixa `effect=NONE`, `scheduler=false`, `lease_grant=false`, `assignment=false`, `admission=false`, `source_authority=git` e `mutable_tools=disabled`. Ao anexá-lo a um `pgh.context-envelope/*`, a `EnvelopeTransportQueue` continua com a sua autoridade histórica `envelope_transport_only`; nenhum campo concede execução.

## Gate observado U16

Na WIN110, o provider pinado `code-graph-rag v0.0.932@dee19db154e14e3a4d87589523068a066ac9f109` operou em modo offline protobuf. O branch GitHub `debianlima/pgh-desktop:pgh-3.0-desktop-candidate` resolveu para `d41977485e289b4f2c219bb2bd6fd9939850ca97`, exatamente o commit do índice. O índice tinha 1.948 nós, 5.913 relações e cobertura C++ de 69 módulos. `source.tools.Tools.toolDefinitions` resolveu para `tools.cpp:179-421`; callers foram recuperados estruturalmente e o `code_context_ref` foi produzido com ferramentas mutáveis desabilitadas.

Esta homologação cobre a biblioteca/adapter e transporte de contexto. Ela não promove novo daemon RHGD, não altera o estado `STANDBY_CANDIDATE` e não transforma Hagger em scheduler/authority.
