# Plano de implementação — primeira experiência jogável

Data: **05/11/2026**. Status: **primeira implementação concluída; equilíbrio dos níveis ainda experimental**.
Consulte [Implementação do simulador](implementacao-simulador.md) para evidências e limitações.
Referências: [estado atual](estado-atual.md) e [direção confirmada](simulador-3d.md).
Parâmetros numéricos e controles abaixo são propostas iniciais, sujeitos a teste.

## 1. Resultado esperado

Uma partida totalmente 3D em primeira pessoa, dentro de um galpão. Caixas coloridas
chegam por uma esteira. O jogador pega, transporta, gira, solta ou arremessa as caixas,
organizando pilhas nos retângulos do chão correspondentes às suas cores.

Cada retângulo fica diante de uma porta de galpão fechada. As portas representam docas
de saída para caminhões e integram o cenário e sua colisão. A conclusão da tarefa não
abre portas nem remove caixas para simular carregamento de caminhão.

A partida termina em vitória quando todas as caixas previstas estiverem corretamente
organizadas e estáveis dentro do prazo. Ao acabar o prazo, aparece um resultado com
opções de repetir ou voltar ao menu. Um modo de treino usa a mesma simulação sem prazo.

## 2. Escopo e decisões de implementação

- Python, Pygame e PyOpenGL; aproveitar inicialização de janela, textos e desenho básico.
- Física própria para caixas rígidas: gravidade, movimento linear e angular, contatos,
  atrito, impactos, repouso, empilhamento e arremesso.
- Geometria simples construída por código: piso, paredes, esteira, caixas e portas.
- Até cinco cores identificadas também por letra ou símbolo na caixa, na área e na porta.
- Um galpão, três configurações iniciais de dificuldade e treino.
- Física independente da renderização e testável sem janela.
- Primeiro validar poucas caixas e pilhas de três unidades; ampliar a carga depois da prova física.

O experimento concentra a física em caixas e superfícies rígidas. Modelos deformáveis,
personagens articulados e veículos ficam para futuras decisões. O personagem usará um
controlador de movimento com colisão, sem simulação corporal detalhada.

## 3. Espaço e regras da partida

Organizar o galpão com uma entrada pela esteira em uma parede e docas nas outras paredes.
Cada doca tem retângulo colorido no chão, identificação e porta da mesma categoria.
Reservar circulação suficiente entre a saída da esteira e as áreas de empilhamento.
A esteira terá superfície, laterais e uma área de saída acessível ao jogador.

A cor será um identificador de categoria, separado do valor RGB usado no desenho.
Isso evita comparar cores por ponto flutuante ou misturar regra de jogo com renderização.
Uma caixa não muda de categoria ao ser pega, arremessada ou colocada em outra área.

### Quando uma caixa conta como organizada

1. Sua categoria corresponde à área de destino.
2. A projeção de seus oito vértices no chão cabe integralmente no retângulo, com tolerância numérica pequena.
3. Está apoiada diretamente no chão ou em uma cadeia de caixas organizadas da mesma cor, sem ciclos de apoio.
4. Não está na mão e suas velocidades linear e angular permanecem baixas por um intervalo mínimo.

Proposta inicial: exigir 0,75 segundo de estabilidade. Estar apenas passando sobre a
área durante um arremesso não conta. Uma caixa no topo pode contar sem tocar o piso,
desde que a cadeia de apoio seja válida. Uma caixa de cor errada sob a pilha invalida
essa cadeia de organização, embora o apoio físico continue existindo.

A contagem é recalculada: retirar uma caixa ou derrubar uma pilha pode reduzir o total.
Uma caixa conta uma única vez, identificada por um ID próprio. Exigir dois segundos de
organização completa, após a emissão de todo o lote, para confirmar a vitória.

## 4. Controles propostos

| Entrada | Ação |
| --- | --- |
| WASD | Caminhar, com velocidade diagonal normalizada. |
| Mouse | Olhar ao redor, com limite vertical. |
| E | Pegar a caixa alcançável sob a mira; se já estiver segurando, soltar. |
| Segurar botão esquerdo e soltar | Carregar a força e arremessar a caixa segurada. |
| Segurar botão direito e mover mouse | Girar a caixa segurada; suspender a rotação da câmera durante essa ação. |
| Esc | Pausar, liberar o mouse e abrir opções de retomar, reiniciar e voltar ao menu. |
| F3 | Alternar visualização de volumes de colisão, contatos e informações físicas. |

Uma mira indica o alvo e um aviso mostra a ação disponível. A interface exibe tempo,
caixas recebidas, organizadas e total do lote. A força do arremesso aparece apenas ao carregar.
Perder o foco da janela pausa a partida e libera a captura do mouse.

### Pegar e transportar

Selecionar por raio da câmera, com alcance limitado e teste de obstrução: não pegar
através de uma parede ou de outra caixa. Transportar uma caixa por vez.

Usar um alvo à frente da câmera e uma força de acompanhamento amortecida, limitada.
A caixa continua sendo um corpo dinâmico com colisão. Não escrever sua posição
diretamente a cada quadro. Uma parede pode impedir que ela alcance o alvo. Romper
a interação se a distância exceder um limite seguro, evitando forças crescentes.

Ignorar apenas o contato entre a caixa segurada e o corpo do jogador enquanto necessário;
preservar contatos com cenário e outras caixas. Ao soltar, reativar esse contato quando
os volumes estiverem separados, evitando uma expulsão brusca do jogador.

### Jogar caixas longe

Converter a carga do botão em um impulso único, aplicado na direção da mira. Limitar
tempo de carga, impulso e velocidade. Soltar sem carga produz um lançamento curto.
Aplicar no centro gera translação; um pequeno deslocamento controlado do ponto de
aplicação pode produzir giro. A força de segurar deixa de atuar no mesmo passo.

Uma caixa lançada pode atingir paredes, mover outras caixas e derrubar pilhas. Seu
movimento continua submetido a gravidade, atrito e impactos. Não conceder pontos por
arremesso: ele é uma ferramenta de transporte e de experimentação física.

## 5. Física própria: estratégia incremental

### Dados e convenções

Adotar metros, segundos e quilogramas; eixo Y para cima. Manter posição, orientação,
velocidades linear/angular, massa inversa, inércia inversa, dimensões, atrito e restituição
em `CorpoRigido`. Objetos estáticos têm massa inversa zero. Guardar a orientação com
quaternion e converter para matriz no desenho, com funções matemáticas pequenas e testadas.

Começar com caixas de mesmo tamanho e massa para isolar defeitos. Cor não altera massa.
Incluir massas diferentes nos testes de física antes de expor essa variação ao jogador.

### Tempo da simulação

Usar acumulador e passo físico fixo, inicialmente 1/120 segundo. Eventos geram intenções;
a física consome essas intenções em cada passo. Um arremesso é consumido uma única vez,
mesmo que um quadro execute vários passos físicos.

Limitar a recuperação após travamentos; descartar o acúmulo ao pausar, retomar ou perder
foco. Cronômetro e esteira usam o mesmo tempo simulado para não cobrar tempo que a
simulação descartou. Medir desempenho para evitar lentidão sistemática nessa política.

### Detecção de contatos

1. Filtrar pares por caixas delimitadoras alinhadas aos eixos (AABB); na primeira versão,
   percorrer pares diretamente é suficiente para o orçamento inicial de até 20 caixas.
2. Validar sobreposição de caixas orientadas (OBB) com o teste de eixos separadores (SAT).
3. Gerar normal, profundidade e pontos de contato, distinguindo face-face e aresta-aresta.
4. Manter vários pontos de apoio em contatos de face, necessários à estabilidade das pilhas.

AABB é a primeira prova isolada com caixas sem rotação, e depois permanece como filtro.
A experiência final desta etapa inclui OBB e rotação, para que arremessos e tombamentos
tenham resposta coerente. Piso, paredes e portas podem ser caixas estáticas de espessura finita.

### Resposta física

Integrar velocidades com gravidade e forças; avançar posição e orientação; gerar contatos
e resolver impulsos sequenciais em várias iterações, incluindo velocidade no ponto de
contato, massa e inércia. Tratar o atrito tangencial com limite associado ao impulso normal.

Separar correção de penetração da resposta de impacto, usando tolerância e correção
limitada para não injetar energia excessiva. Suprimir pequenos ressaltos no repouso.
Reutilizar impulsos de contatos persistentes quando necessário para estabilizar pilhas.
Corpos estáticos não recebem deslocamento ou velocidade pela resolução.

Adicionar repouso após um período de baixa velocidade, somente após validar a estabilidade
sem esse recurso. Impactos, manipulação e movimento de apoios devem acordar os corpos.
Repouso não pode ser usado para esconder um erro de contato ou congelar uma pilha no ar.

### Arremessos rápidos e atravessamento

Subdividir o passo conforme deslocamento relativo e rotação, considerando o menor tamanho
dos colisores. Calibrar a velocidade máxima de lançamento e a espessura das paredes com
testes de impacto no pior caso. Passo fixo, sozinho, não garante impedir atravessamento.

Estabelecer um limite de subdivisões e manter as configurações de lançamento dentro do
intervalo validado. Se isso não bastar, implementar detecção contínua para caixas lançadas
antes de liberar mais velocidade. Não prometer colisão contínua geral neste protótipo.

### Esteira

Representar a faixa como superfície de colisão com velocidade tangencial própria.
O atrito no contato tende a levar a caixa à velocidade da faixa; não teletransportar caixas.
Fora da faixa, essa velocidade de superfície deixa de atuar. A borda de saída permite
que caixas caiam sob gravidade quando não estiverem mais apoiadas.

Gerar caixas apenas se o volume de entrada estiver livre. Quando estiver ocupado,
aguardar e manter o lote pendente; não criar corpos sobrepostos nem descartar encomendas.
O jogador pode retirar caixas de qualquer ponto alcançável. A produção tem quantidade
finita por nível e sequência de cores reproduzível para testes.

## 6. Organização do código e didática

Proposta de pacote `deposito/`, criado conforme cada etapa exigir:

| Módulo | Responsabilidade e exemplos de nomes |
| --- | --- |
| `aplicacao.py` | Janela, eventos, estados e loop: `processar_eventos`, `atualizar_partida`. |
| `matematica.py` | Vetores e orientação: `normalizar_vetor`, `girar_vetor`, `integrar_orientacao`. |
| `corpos.py` | Dados de `CorpoRigido`, `Contato` e propriedades físicas das caixas. |
| `colisoes.py` | `calcular_aabb`, `detectar_colisao_caixas`, `gerar_pontos_de_contato`, `intersectar_raio_caixa`. |
| `fisica.py` | `avancar_simulacao`, `aplicar_gravidade`, `resolver_contatos`, `aplicar_impulso`, `corrigir_penetracao`. |
| `jogador.py` | `mover_jogador`, `selecionar_caixa`, `segurar_caixa`, `soltar_caixa`, `arremessar_caixa`. |
| `cenario.py` | Construção e dados de galpão, portas e áreas: `criar_galpao`, `criar_area_de_cor`. |
| `esteira.py` | `atualizar_esteira`, `entrada_esta_livre`, `emitir_proxima_caixa`. |
| `partida.py` | Regras: `validar_apoio`, `caixa_esta_organizada`, `atualizar_objetivo`, `reiniciar_partida`. |
| `niveis.py` | Configurações explícitas: cores, quantidade, prazo e intervalo de chegada. |
| `renderizacao.py` | `desenhar_galpao`, `desenhar_caixa`, `desenhar_interface`, `desenhar_contatos`. |

`main.py` passa a ser uma entrada curta para a nova aplicação quando o ciclo jogável
estiver integrado. Manter a versão atual executável durante o protótipo com uma entrada
separada; Git e o documento histórico preservam a referência para a troca definitiva.

Convenções para a implementação:

- Nomes em português, claros e consistentes, sem abreviações vagas; indicar unidades em constantes.
- Funções com uma responsabilidade, argumentos explícitos e retorno definido.
- `dataclass` e anotações de tipos para estruturas compartilhadas; evitar hierarquias e gerenciadores genéricos.
- Física e regras sem importação de OpenGL/Pygame; desenho consulta o estado, sem alterar regras.
- Constantes numéricas nomeadas para tolerâncias, gravidade, alcance e limites de impulso.
- Docstrings explicando entradas, saídas e convenções; comentários explicando o motivo de fórmulas e decisões.
- Dividir os algoritmos de contato em funções legíveis, sem comprimir fórmulas em expressões extensas.
- Evitar comentar operações óbvias; explicar normal do contato, sinal do impulso e prevenção de instabilidade.

Exemplo do estilo esperado, ainda sem implementação:

```python
def aplicar_impulso(corpo: CorpoRigido, impulso: Vetor3, ponto: Vetor3) -> None:
    """Altera as velocidades do corpo; ponto e impulso usam coordenadas do mundo."""
    # Um impacto fora do centro de massa também provoca rotação.
    # Corpos estáticos têm massa inversa zero e não recebem movimento.
    ...
```

## 7. Etapas e critérios de avanço

| Etapa | Entrega verificável | Critério para avançar |
| --- | --- | --- |
| 1 — Sala e primeira pessoa | Galpão simples, câmera, pausa e movimento com colisão básica. | Caminhar sem atravessar chão e paredes; capturar/liberar mouse corretamente. |
| 2 — Laboratório físico | Queda e contato AABB inicial; depois OBB, giro, atrito e impulsos. | Caixa repousa, impacto fora do centro gira, três caixas empilham e um impacto pode derrubá-las. |
| 3 — Manipulação | Pegar por raio, carregar com contato, girar, soltar e arremessar. | Não pegar através de paredes; carregar não atravessa cenário; arremesso não aplica impulso repetido. |
| 4 — Recebimento e docas | Esteira, geração finita, áreas de até cinco cores e portas. | Caixa é transportada pela faixa, cai na saída e entrada bloqueada não gera sobreposição. |
| 5 — Partida completa | Contagem por cor e apoio, prazo, vitória, derrota, reinício e treino. | Cor errada, caixa voando ou pilha instável não concluem o objetivo; retirar apoio atualiza a contagem. |
| 6 — Dificuldade e validação | Três configurações, interface e verificação local completa. | Concluir uma partida real; validar cinco cores, carga máxima e física em diferentes FPS. |

A primeira prova interativa é o laboratório das etapas 1–3. A primeira experiência
completa de organização exige as seis etapas. Não considerar a tarefa concluída apenas
porque as caixas caem: estabilidade das pilhas e manipulação com colisão são critérios centrais.

## 8. Dificuldade inicial proposta

| Configuração | Cores | Total de caixas | Prazo inicial | Intervalo de emissão |
| --- | --- | --- | --- | --- |
| Treino | 2 | 6 | Sem limite | 6 s |
| Fácil | 2 | 6 | 180 s | 6 s |
| Médio | 3 | 12 | 240 s | 5 s |
| Difícil | 5 | 20 | 300 s | 4 s |

São valores para começar a testar, sem equilíbrio já comprovado. O difícil dispõe de mais
tempo absoluto, mas menos tempo por caixa e maior fluxo. Medir tempo real de transporte,
rotação e empilhamento antes de fixar esses números. Distribuir categorias no lote de
forma que todas as cores ativas apareçam. Dimensões das áreas devem permitir empilhar sem
exigir precisão excessiva. Não alterar gravidade ou precisão da física entre dificuldades.

## 9. Plano de verificação

Testes de lógica com a biblioteca padrão, acrescentados junto ao comportamento:

- Colisão separada, borda em contato, sobreposição, caixas giradas, contato de face e aresta.
- Normal consistente, pontos de apoio válidos e ausência de divisão por zero em eixos paralelos.
- Queda e repouso, impacto entre massas diferentes, atrito e resposta angular fora do centro.
- Impactos sem força externa não criam energia significativa; tratar tolerâncias numericamente.
- Pilha de três caixas por pelo menos 30 segundos simulados, com deriva e penetração limitadas.
- Tombamento com apoio inadequado, despertar ao retirar apoio e colisão após repouso.
- Lançamento máximo contra parede, canto e outra caixa nas configurações suportadas.
- Um impulso por arremesso, seleção bloqueada, transporte contra parede e soltura segura.
- Esteira com entrada ocupada, limite do lote, contato na saída e sequência reproduzível.
- Regra de cor, contenção integral, pilha válida, perda de apoio e ausência de contagem no ar.
- Prazo, pausa, reinício e equivalência aproximada em renderização a 30, 60 e 144 FPS.

Definir tolerâncias de deriva e penetração em metros no teste, após escolher o tamanho
das caixas. Manter ordem de pares estável e sementes fixas; não exigir igualdade exata
de ponto flutuante ou determinismo entre plataformas.

Validar graficamente em sessão local: controles reais, contato visual alinhado à geometria,
portas e retângulos legíveis, cinco cores, carga do arremesso e transições. O modo F3
mostra volumes, normais, pontos de contato, velocidades, corpos ativos e passos físicos.
Medir o desempenho com 20 caixas; 60 FPS é uma meta a verificar no computador de entrega.

## 10. Riscos e decisões de contenção

O principal risco técnico é estabilidade de contatos, especialmente ao carregar e empilhar.
Começar com um laboratório reproduzível, poucas caixas e superfícies simples. Só aumentar
quantidade, velocidade de lançamento e complexidade do cenário após os testes passarem.
Corrigir contato e resolução antes de acrescentar regras de jogo que escondam defeitos.

Não ampliar a implementação para um motor físico genérico. Este plano cobre os corpos
e interações necessários ao depósito. Se a implementação própria não atingir estabilidade,
registrar os casos que falham e revisar a abordagem antes de avançar a dificuldade.

## 11. Referências técnicas consultadas

As referências orientam o experimento; nenhuma dessas bibliotecas será dependência da implementação planejada.

- [Box2D — Simulation](https://box2d.org/documentation/md_simulation.html): referência de passo fixo, subdivisões e reaproveitamento de impulsos. É um motor 2D; seus princípios de integração e solução de contatos exigem adaptação ao 3D.
- [Erin Catto — Modeling and Solving Constraints](https://box2d.org/files/ErinCatto_ModelingAndSolvingConstraints_GDC2009.pdf): referência conceitual para restrições e impulsos sequenciais.
- [Bullet — btBoxBoxDetector.cpp](https://pybullet.org/Bullet/BulletFull/btBoxBoxDetector_8cpp_source.html): referência primária de detecção de contato entre caixas 3D orientadas.

As seis etapas possuem uma primeira implementação. Próximo passo: experimentar uma partida
com controles físicos, ajustar alcance, sensação de peso e tempo dos níveis a partir do uso.
