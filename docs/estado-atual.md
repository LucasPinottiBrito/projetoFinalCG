# Estado atual — Depósito: Desafio das Caixas

Data do levantamento: **05/11/2026**. Referência do código: commit **471c1e0**.
Levantamento baseado na leitura dos quatro módulos principais, documentação e testes.
Este documento descreve a versão anterior à transformação em simulador totalmente 3D.

## Proposta e tecnologias

Projeto acadêmico de Computação Gráfica em Python com duas experiências independentes:
um jogo 2D de coleta e entrega e uma cena 3D explorável de um depósito.

- Dependências fixadas: Pygame 2.6.1 e PyOpenGL 3.1.10.
- OpenGL 2.1 com pipeline fixo, primitivas em modo imediato e matrizes tradicionais.
- Pygame administra janela, eventos, relógio e rasterização das fontes; OpenGL exibe geometria e textos.
- Janela fixa de 960 × 720; loop limitado a uma frequência desejada de 60 FPS.
- Sem modelos, texturas ou fontes externas obrigatórias, banco de dados ou serviços de rede.
- Entrada da aplicação: `python main.py`.

## Experiência existente

### Menu

`1` inicia uma nova partida 2D, `2` abre a cena 3D e `Esc` encerra.
Retornar a um modo pelo menu restaura seu estado inicial. Fechar a janela encerra a aplicação.

### Jogo 2D

O jogador é um quadrado azul movido por setas ou WASD. A coleta verde fica no canto
superior esquerdo; a entrega amarela, no inferior direito. Entrar nessas áreas coleta
ou entrega automaticamente uma encomenda. O jogador transporta apenas uma por vez.

Cada entrega vale 100 pontos. Cinco entregas, ou 500 pontos, encerram a partida com
vitória. O tempo não gera pontos e permanecer na entrega sem encomenda não pontua.

Três caixas se movem em trajetórias fixas: A e C horizontalmente, B verticalmente.
Cada uma reflete seu movimento ao atingir os próprios limites. Suas trajetórias não
atravessam a coleta, a entrega ou a posição inicial do jogador.

O jogador começa com três vidas. A colisão com uma caixa:

1. Retira uma vida e devolve a encomenda em transporte à coleta.
2. Preserva as entregas e a pontuação já conquistadas.
3. Reposiciona o jogador em uma posição livre e concede um segundo de invulnerabilidade.
4. Encerra a partida em derrota se as vidas chegarem a zero.

`P` pausa ou retoma. Perder o foco da janela também pausa. Na pausa, `Enter` retoma,
`R` reinicia, `Esc` retorna ao menu e `Q` encerra. Em vitória ou derrota, `R` ou `Enter`
reiniciam, `Esc` retorna ao menu e `Q` encerra.

Pausa, vitória e derrota congelam toda a simulação, incluindo a invulnerabilidade.
Reiniciar restaura vidas, posições, sentidos das caixas, pontuação e encomenda.

### Cena 3D

Cinco paralelepípedos de cores e dimensões diferentes estão apoiados em um piso com
duas paredes. A geometria é estática e não compartilha o estado da partida 2D.

- Arrastar com o botão esquerdo ou usar setas gira uma câmera orbital.
- Rodinha e `+`/`=`/`-` aproximam ou afastam a câmera.
- `L` alterna iluminação média, forte e fraca.
- `R` restaura a câmera, preservando a luz escolhida; `Esc` retorna ao menu.
- Elevação limitada a 12–75 graus; distância limitada a 10–27 unidades.

Não existe personagem caminhando pelo depósito, manipulação de caixas, gravidade,
colisão 3D ou resposta física entre objetos.

## Arquitetura

| Arquivo | Responsabilidade atual |
| --- | --- |
| [main.py](../main.py) | Criação da janela, classe `Aplicacao`, eventos, atualização, troca de telas e encerramento. |
| [jogo_2d.py](../jogo_2d.py) | Dados `Retangulo` e `Caixa`, classe `Jogo`, colisão AABB, movimento, regras e desenho do jogo. |
| [ambiente_3d.py](../ambiente_3d.py) | Classe `Ambiente`, câmera orbital, geometria das cinco caixas, normais e iluminação. |
| [desenho.py](../desenho.py) | Projeção ortográfica, retângulos, linhas, menus, painéis e cache de textos. |
| [tests/test_logica.py](../tests/test_logica.py) | 18 testes de lógica e geometria, executáveis sem dependências gráficas. |
| [tests/verificar_grafico.py](../tests/verificar_grafico.py) | Verificação com contexto OpenGL real, eventos simulados e geração de capturas. |
| [requirements.txt](../requirements.txt) | Versões das duas dependências de execução. |
| [capturas/](../capturas/) | Imagens existentes do menu, jogo e cena 3D. |

O fluxo principal é: ler eventos → atualizar estado → desenhar → trocar buffers.
`Aplicacao.tela` seleciona `menu`, `2d` ou `3d`; `Jogo.estado` seleciona `jogando`,
`pausado`, `fim` ou `vitoria`. Importar os módulos não abre a janela.

As regras 2D e os dados matemáticos 3D podem ser importados sem Pygame ou OpenGL.
As funções de desenho desses módulos carregam as dependências gráficas localmente.

## Movimento, colisões e renderização

O deslocamento depende de velocidade × tempo decorrido. A direção do jogador é
normalizada para evitar vantagem na diagonal. O intervalo é limitado a 0,05 segundo,
descartando o excesso em travamentos. Transições de tela e pausa descartam um intervalo
para evitar saltos ao retomar.

A colisão 2D usa sobreposição de retângulos alinhados aos eixos (AABB). Apenas encostar
nas bordas não conta como colisão. A verificação ocorre após o movimento de cada quadro.
Sua consequência é uma regra de dano e reaparecimento, sem cálculo de forças ou impulsos.

O 2D usa projeção ortográfica. O 3D usa perspectiva de 48 graus, câmera orbital orientada
por `gluLookAt`, teste de profundidade, descarte de faces traseiras, normais e luz pontual.
Cada caixa deriva de um cubo transformado por escala e translação. A interface sobreposta
ao 3D usa temporariamente a projeção 2D.

Textos são rasterizados pelo Pygame e enviados a texturas OpenGL. O cache mantém no máximo
96 entradas e libera as texturas removidas e as restantes no encerramento.

## Verificação e limites da evidência

Em 05/11/2026, nesta sessão Windows, foi executado:

```powershell
python -B -m unittest discover -s tests -v
```

Resultado: **18 testes aprovados**. A cobertura inclui colisões, limites, movimento,
trajetórias, áreas seguras, dano, proteção, coleta, entrega, pausa, vitória, derrota,
reinício, limites da câmera e orientação das faces.

A aplicação gráfica e o script de integração **não foram executados neste levantamento**.
Portanto, o resultado acima não confirma renderização, entradas reais ou compatibilidade
gráfica neste computador. As capturas existentes não são evidência de uma nova execução.

O README registra testes gráficos anteriores em macOS, datados de 01/11/2026. Esse registro
é histórico e não substitui uma validação gráfica local.

## Limitações atuais relevantes para a evolução

- O jogo é 2D; o depósito 3D é uma demonstração separada e estática.
- Não há motor de física, corpos rígidos, gravidade, atrito, empilhamento ou colisões 3D.
- Não há câmera em primeira pessoa nem sistema de pegar, carregar, girar e soltar objetos.
- Dificuldade fixa, sem níveis, prazos, fluxo de encomendas ou regras de organização espacial.
- Não há persistência de partidas ou pontuação.
- Janela fixa e renderização tradicional, sem sombras projetadas ou materiais avançados.
- As colisões discretas atuais não constituem uma base pronta para física de corpos 3D.

O projeto já oferece referências úteis para loop de aplicação, estados, controles,
pausa, interface e testes. A simulação física e as regras de organização do depósito
precisarão de uma nova implementação compatível com a direção registrada a seguir.
