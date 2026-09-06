# U-RHGD-15 — TransportPathEvidence / Netmaker

RHGD passa a aceitar `rhgd-transport-path-evidence/1` como projeção rebuildable de qualidade de caminho. Transportes reconhecidos são `NETMAKER`, `LAN`, `WIREGUARD_DIRECT`, `IPSEC`, `HUB` e `UNKNOWN`. O nome do transporte não recebe prioridade fixa: RTT, banda, perda, MTU e freshness observados geram um pequeno bônus de ranking.

A evidência declara `source_of_truth=false`, `rebuildable=true`, `authority_effect=NONE`, `scheduler=false`, `lease_grant=false`, `assignment=false` e `admission=false`. Portanto uma Netmaker rápida pode melhorar o ranking do `FederatedDestinationMatcher`, mas somente PGD transforma o candidato em assignment/lease/execution.

Evidência stale, rota ausente ou classificação `indisponivel` recebe bônus zero; o ranking histórico continua funcional sem path evidence. Isso preserva compatibilidade e impede que uma rota antiga seja tratada como capacidade viva.

A amostra versionada desta unidade é vetor sintético de gate, não benchmark físico. A rede atual pode produzir evidência observada por probes separados; a U15 homologa o contrato e a integração do matcher, não fabrica throughput.
