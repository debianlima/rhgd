# U-RHGD-02 — redução hierárquica determinística

A redução anterior preservava a primeira ocorrência via `dict.fromkeys`, tornando a saída dependente da ordem de chegada. Em rede heterogênea, ordem de chegada não é identidade semântica.

U-RHGD-02 canonicaliza texto com Unicode NFKC, whitespace normalizado e casefold; usa SHA-256 da forma canônica como chave estável; escolhe representante textual deterministicamente; ordena claims/evidence/dissent pela identidade estável; e ordena provenance de sources por `work_id,node_id,confidence`.

A propriedade homologada é sobre o conteúdo lógico (`claims`, `evidence`, `dissent`, `sources`). `depth` continua descrevendo a forma física da árvore e pode variar com `fan_in`.

Esta unidade não interpreta dissenso nem calcula concordância. Ela apenas garante reprodutibilidade da redução.
