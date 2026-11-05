# Primeira implementação do simulador

Data: 05/11/2026. Entrada atual: `python main.py`.

## Experiência entregue

Galpão 3D com câmera em primeira pessoa, esteira que emite um lote finito de caixas,
até cinco áreas retangulares por cor e portas de doca cenográficas. Caixas podem ser
pegas, transportadas, giradas, soltas e arremessadas. Uma mola amortecida mantém a
caixa perto da mão preservando a colisão contra o cenário. O arremesso usa carga
limitada e um impulso único aplicado fora do centro para produzir giro.

Treino e três dificuldades usam as configurações propostas no plano. A organização
exige categoria correta, todos os vértices dentro da área, estabilidade por 0,75 s e
cadeia de contatos de apoio até o piso. Cor errada na base invalida a cadeia.
Concluir o lote por dois segundos confirma vitória; esgotar o prazo gera derrota.
O jogador pode repetir, avançar após vitória, voltar ao menu ou sair. A dificuldade
mais alta pode ser repetida após a conclusão. Não é obrigatório que todas as caixas
estejam em uma única pilha; caixas individualmente apoiadas também podem contar.

O laboratório do menu permite observar três caixas empilhadas, uma caixa em queda,
contatos, impactos e arremessos sem prazo ou objetivo. F3 também funciona nos níveis.

## Estrutura e decisões

O pacote `deposito/` segue os módulos e nomes do plano: matemática, corpos, colisões,
física, jogador, cenário, esteira, partida, níveis, renderização e aplicação. A lógica
não importa dependências gráficas. `main.py` apenas inicia a aplicação. O ponto de
entrada anterior foi preservado em `legado.py`; seus testes gráficos importam essa entrada.

- Unidades: metros, segundos e quilogramas; Y cresce para cima.
- Passo físico de 1/120 s, com subdivisões adicionais conforme movimento linear e angular.
- AABB filtra pares e SAT testa caixas orientadas. Faces são recortadas para gerar
  pontos de apoio distribuídos; contatos de aresta usam pontos próximos em segmentos.
- Impulsos sequenciais resolvem velocidade linear/angular, restituição e atrito.
  A correção de penetração é limitada e aplicada uma vez por par.
- Pilhas inteiras em repouso podem dormir. Contatos inalterados são reutilizados;
  impactos, manipulação ou perda de apoio despertam os corpos conectados.
- Impulsos de contatos ativos são recalculados a cada passo. Não há reaproveitamento
  dos valores de impulso entre passos (warm starting).
- A esteira é um colisor estático com velocidade tangencial de superfície. O atrito
  transporta caixas; uma entrada obstruída aguarda sem perder itens do lote.
- O jogador é um colisor controlado, com movimento horizontal e deslizamento por eixo.
  Não pula nem sobe nas caixas. A caixa segurada ignora temporariamente apenas seu contato
  com o jogador; ao separar os volumes após a soltura, esse contato é restaurado.
- Gravidade e precisão da física são iguais em todos os níveis. Cor não altera massa.
- O teto fecha o volume físico para que arremessos altos não percam caixas fora do galpão.
  O menu oculta o teto para apresentar uma visão em corte do depósito.
- Física, esteira e prazo usam o mesmo tempo simulado. Após travamentos, no máximo
  0,1 s por quadro é recuperado; o excesso é descartado. Pausar limpa o acumulador.
- Geometria repetida usa uma display list OpenGL; textos usam o cache existente.
  Os recursos são liberados antes de destruir o contexto gráfico.

## Evidências de verificação

Os **40 testes sem janela** incluem a versão anterior e o novo simulador. Cobrem matemática,
contatos orientados, impacto, massa, atrito, pilha por 30 segundos simulados, despertar
ao retirar apoio, tombamento após impacto, lançamento a 14 m/s contra parede e retenção pelo teto, seleção
obstruída, transporte contra parede, giro, esteira, regras de organização, pausa,
reinício, vitória, derrota e equivalência aproximada a 30/60/144 FPS de renderização.

O script `tests/verificar_simulador.py` também foi executado com contexto OpenGL real
no Windows, Python 3.11.9, Pygame 2.6.1 e PyOpenGL 3.1.10. O driver informou OpenGL 4.6
e Intel UHD Graphics. Foram exercitados eventos simulados de pegar, carregar, arremessar,
pausar, retomar, perder foco, reiniciar, trocar de modo e fechar.

Capturas do menu, recebimento, manipulação, arremesso, pausa, laboratório e cinco cores
estão em `capturas/simulador/`, junto de `verificacao.json`, que registra a medição da
última execução. Houve inspeção visual das capturas. Esses eventos não substituem um
ensaio de usabilidade com teclado e mouse físicos durante uma partida inteira.

## Limitações e próximos ajustes

- Física de caixas rígidas é experimental, sem detecção contínua geral. Velocidade
  linear é limitada a 14 m/s, angular a 12 rad/s e subdivisão a oito. Paredes e caixas
  têm espessura finita. Alterar esses parâmetros exige repetir testes de atravessamento.
- O desempenho depende da quantidade de contatos ativos. A medição com 20 caixas em
  repouso aproxima-se de 60 FPS neste computador; muitas caixas ativas em contato
  simultâneo podem reduzir bastante a velocidade. A meta não é garantida em toda cena.
- O orçamento inicial é de 20 caixas. O filtro percorre pares diretamente; não há
  estrutura espacial para centenas de objetos. Pilhas altas e situações extremas
  ainda exigem investigação específica.
- Os testes comprovam casos definidos, não precisão física geral ou conservação exata
  de energia. Amortecimento, limites de velocidade e repouso priorizam a experiência.
- A interface usa janela fixa de 960 × 720 e pipeline OpenGL tradicional. Sem sombras
  projetadas, modelos externos, áudio, salvamento ou expedição real para caminhões.
- Dificuldade, tempo e força de arremesso precisam de calibração jogando. Não há dano
  por impacto, fragilidade, limite de altura da pilha ou exigência de empilhar todo o lote.
- Em caso de instabilidade, usar F3 e o laboratório para registrar posição, contato e
  sequência de ações, antes de ajustar tolerâncias ou aumentar iterações.
