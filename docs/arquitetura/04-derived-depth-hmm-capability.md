# U-RHGD-03 — profundidade derivada por capacidade real

O RHGD consome `hmm-capability-advertisement/1` somente como projeção read-only. O adapter exige `context_capacity.configured_tokens` e usa `usable_tokens`/`effective_budget_tokens` quando declarados. Ele recusa anúncios que reivindiquem scheduler ou lease.

A profundidade de navegação não é mais uma constante universal na linha viva: o PGH/catálogo fornece custos estimados por nível e o RHGD desce enquanto o custo cumulativo do próximo nível cabe no orçamento selecionável do executor. Sem custos declarados, a profundidade fica `undeclared`; não há fallback inventado.

VRAM, RAM, NVMe, bandwidth e latency permanecem dados físicos para resource planning. RHGD não os transforma em tokens.

U35 continua histórico: seu `18K` permanece o máximo de uma subcamada no contrato daquela unidade, não é reescrito. U-RHGD-03 apenas adiciona adaptação viva downstream.
