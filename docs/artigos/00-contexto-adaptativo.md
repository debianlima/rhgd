# Inteligência Artificial que sabe quanto consegue pensar

## Contexto adaptativo para agentes grandes e pequenos

Uma IA não deve carregar todas as competências disponíveis a cada mensagem. O PGH organiza conhecimento como ontologia navegável e seleciona o menor contexto suficiente. Um pré-orquestrador classifica mensagem, intenção, fase, competências e ferramentas e cruza isso com a capacidade real do executor.

A seleção possui escape progressivo: `selected -> adjacent -> global`. Capacidade nominal não é orçamento efetivo: contexto carregado, reserva de saída, concorrência, RAM/VRAM e pressão do runtime reduzem o que pode ser usado com segurança.

O `Context Envelope` transporta tarefa, papel, competências, ferramentas, orçamento, evidências e política de expansão. Em executores grandes, o mesmo agente pode trocar chapéus sequencialmente mantendo memória compartilhada. Em um 4B/16K, cada etapa recebe microcontexto, produz artefato condensado e libera contexto antes da próxima competência.

O princípio é preservar o mesmo protocolo intelectual em hardware diferente: modelos pequenos pagam com mais etapas; modelos grandes mantêm mais memória e fazem menos transições. Em ambos os casos, carregar competência detalhada sob demanda reduz ruído e mantém a possibilidade de expansão quando a seleção inicial for insuficiente.
