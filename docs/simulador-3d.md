# Nova direção — Simulador de organização de depósito 3D

Registro iniciado em **05/11/2026**. Status: **primeira experiência implementada**.
Este documento registra decisões de produto. O que foi entregue e suas limitações estão
em [Implementação do simulador](implementacao-simulador.md).
O ponto de partida está em [Estado atual](estado-atual.md).

## Decisões confirmadas pelo usuário

| Tema | Direção confirmada |
| --- | --- |
| Experiência | Jogo simulador de organização de depósito totalmente em 3D. |
| Tecnologia | Manter Python e OpenGL. |
| Perspectiva e interação | Primeira pessoa, pegando e empilhando caixas. |
| Simulação | Experimentar implementação própria de colisões e respostas físicas. |
| Progressão | Ter níveis de dificuldade. |
| Eixo principal da dificuldade | Prazos e maior volume de entregas. |
| Recebimento | As caixas chegam por uma esteira. |
| Organização | Empilhar caixas dentro de retângulos no chão da mesma cor; até cinco cores. |
| Cenário | Cada área de organização tem uma porta de galpão representando uma futura saída para caminhão. A porta é cenográfica. |
| Interação adicional | Poder jogar caixas longe, com arremesso e consequências físicas. |

O [plano da primeira experiência jogável](plano-primeira-experiencia.md) propõe manter
Pygame e o renderizador OpenGL existente como base, implementando a física em Python.
Isso é uma escolha para o experimento, sem afirmar que uma biblioteca seja proibida pela disciplina.

## Proposta de ciclo de jogo — em discussão

Receber caixas pela esteira → identificar a cor → transportar ou arremessar em primeira pessoa
→ posicionar e empilhar no retângulo da mesma cor → concluir a organização dentro do prazo
→ receber uma avaliação e avançar para o próximo nível.

O fluxo confirmado é receber e organizar caixas. As portas sugerem uma expedição futura,
mas a passagem das caixas para caminhões não integra essa experiência.

Prazos e volume de entregas serão os eixos centrais da dificuldade. Números de caixas,
tempos, quantidade de níveis, critérios de aprovação e ritmo de chegada ainda não foram
definidos. O tempo deve ser calibrado depois de existir uma tarefa jogável de referência.

## Física: escopo proposto para discussão

"Física completa" é uma intenção confirmada, mas ainda não uma especificação fechada.
Para um simulador de caixas, a proposta inicial é trabalhar com corpos rígidos:

| Comportamento proposto | Resultado observável esperado |
| --- | --- |
| Gravidade e apoio | Uma caixa solta cai e repousa sobre o chão, uma prateleira ou outra caixa. |
| Colisão entre caixas e cenário | Caixas encontram barreiras físicas em pisos, paredes, prateleiras e outros volumes. |
| Massa, inércia e impactos | Colisões podem deslocar e girar caixas conforme suas propriedades físicas. |
| Atrito e restituição | Caixas deslizam, desaceleram e reagem aos contatos de maneira consistente. |
| Empilhamento | Pilhas apoiadas permanecem estáveis; posicionamentos inadequados podem tombar. |
| Manipulação com colisão | Pegar e transportar uma caixa preserva sua interação com o cenário. |
| Colisão do jogador | O movimento em primeira pessoa respeita chão, paredes e objetos. |

Deformação de embalagens, quebra, líquidos e simulação detalhada das mãos não foram
solicitados como comportamentos específicos nem aprovados como parte do escopo.
O significado de "mostrar colisões" também precisa ser alinhado: consequências visíveis
na partida, visualização técnica dos volumes de colisão, ou ambos.

O experimento será feito programando a detecção e a resposta física. O plano delimita
corpos rígidos em forma de caixas e validação incremental de empilhamento e arremesso.

## Decisões ainda abertas

1. **Manipulação:** sensação de peso, força máxima do arremesso e sensibilidade da rotação.
2. **Prazo:** o plano propõe derrota com opção de repetir e modo de treino sem cronômetro.
3. **Equilíbrio:** tempos, volumes e intervalos de chegada precisam ser calibrados jogando.
4. **Colisões visíveis:** o plano propõe consequências físicas e uma visualização técnica opcional.
5. **Entrega:** prazo acadêmico, desempenho esperado e estilo visual final.

## Sequência de trabalho sugerida — ainda não aprovada

1. **Protótipo físico:** uma sala 3D, câmera em primeira pessoa, colisão do jogador,
   algumas caixas com gravidade e interação de pegar, girar, soltar e empilhar.
2. **Primeira tarefa completa:** uma regra de destino, recepção de caixas, validação de
   organização e conclusão de uma sessão, com pausa e reinício.
3. **Dificuldade:** prazos, volumes de entregas e progressão entre níveis, calibrados
   usando a tarefa completa.
4. **Apresentação e robustez:** retorno visual das ações, acabamento do depósito,
   validação gráfica local, testes de estabilidade física e documentação atualizada.

A proposta começa pelo empilhamento e pela manipulação porque são essenciais à nova
experiência e precisam funcionar antes de calibrar cronômetros e quantidade de caixas.

## Evidências esperadas para o primeiro protótipo — propostas

- Caminhar e olhar ao redor sem atravessar paredes ou cair através do piso.
- Pegar uma caixa próxima e soltá-la sem atravessar obstáculos durante o transporte.
- Soltar uma caixa no ar e observar queda, impacto e repouso.
- Empilhar caixas e distinguir apoio estável de uma pilha desequilibrada.
- Observar deslocamento e rotação causados por impactos entre caixas.
- Pausar e retomar sem avanço da física nem salto dos objetos.
- Reiniciar e restaurar o cenário sem corpos físicos duplicados.
- Verificar a simulação sob diferentes frequências de renderização.

Essas verificações complementariam os testes atuais. Os 18 testes existentes validam
a versão anterior e não comprovam os sistemas físicos futuros.

## Histórico de alinhamento

| Data | Registro |
| --- | --- |
| 05/11/2026 | Solicitada documentação do estado atual em `/docs` e evolução para simulador de organização de depósito inteiramente 3D, com colisões, física e dificuldade. |
| 05/11/2026 | Confirmado manter Python e OpenGL. |
| 05/11/2026 | Confirmada visão em primeira pessoa para pegar e empilhar caixas. |
| 05/11/2026 | Confirmados prazos e maior volume de entregas como eixo da dificuldade. |
| 05/11/2026 | Definidos esteira, empilhamento em áreas da mesma cor, até cinco cores, portas cenográficas e arremesso de caixas. |
| 05/11/2026 | Solicitado plano com física própria, código limpo, nomes didáticos e comentários explicativos. |
