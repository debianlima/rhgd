# Estado — RHGD 0.0.1 — Fase 0

Estado: `STANDBY_CANDIDATE`.

Materializado como repositório-zero local para consolidar arquitetura e políticas antes de qualquer homologação de rede real.

## Dependências normativas
- PGH 1.2 oficial + candidato PGH 2.0 como fonte de fronteiras em estudo.
- PGD standalone ainda não materializado no momento deste bootstrap; control-plane é evidência de implementação da linhagem PGD.
- PGA standalone ainda não materializado no momento deste bootstrap; handoff PGA no PGH é fonte de fronteira.
- MSGCD é visão agregadora, não autoridade adicional.

## Não reivindicado
- rede P2P real;
- forks AntSeed/Gensyn/Akash;
- TEE/attestation homologado;
- settlement/blockchain;
- token;
- prova criptográfica completa de inferência;
- produção.

## Próximas unidades
1. contratos JSON Schema dos objetos Fase 0;
2. adapter PGH ContextEnvelope -> PGD WorkUnit;
3. capability discovery mock/determinístico;
4. redução hierárquica com preservação de dissenso;
5. threat model e privacy gates;
6. adapters experimentais upstream somente após licença/pin/gates;
7. decisão de repositório remoto e publicação.
