# Depósito: Desafio das Caixas

> Documento histórico da versão 2D + cena 3D. Para executá-la, use `python legado.py`
> no lugar de `python main.py`. As referências a `main.py` abaixo descrevem a versão
> anterior. O simulador atual está documentado em [README.md](README.md).

Projeto acadêmico de Computação Gráfica em Python, com uma janela de 960 × 720 e duas partes independentes. Toda a geometria e a interface são desenhadas com **OpenGL**. O Pygame cria a janela, lê os eventos, controla o relógio e gera as imagens dos textos.

## Visão geral

No **jogo 2D**, mova o quadrado azul, busque uma encomenda na **COLETA verde, no canto superior esquerdo**, e leve-a à **ENTREGA amarela, no canto inferior direito**. Basta entrar nas áreas: a coleta e a entrega são automáticas. Você carrega uma encomenda por vez, desenhada sobre o jogador. Cada entrega vale **100 pontos** e disponibiliza outra encomenda na coleta. Complete **cinco entregas (500 pontos)** para vencer. Não há pontos por tempo, e ficar na entrega sem encomenda não pontua.

Desvie das três caixas móveis: **A** percorre a região superior na horizontal, **B** a região central na vertical e **C** a região inferior na horizontal, começando no sentido contrário a A. Cada uma inverte o sentido nos próprios limites. As trajetórias ficam fora da coleta, da entrega e da posição inicial do jogador.

Você começa com três vidas. Uma batida retira uma vida, devolve a encomenda à coleta e faz o jogador reaparecer em um lugar livre, azul-claro e protegido por um segundo. Pontos e entregas concluídas são preservados. Vitória ou perda das três vidas congela a partida e abre opções para reiniciar, voltar ao menu e sair.

No **depósito 3D**, explore cinco caixas de tamanhos e cores diferentes sobre um piso, com duas paredes formando um canto. Gire a câmera, aproxime a visão e compare três intensidades de iluminação. Essa cena não continua a simulação do jogo.

![Jogo 2D](capturas/jogo_2d.png)

![Depósito 3D](capturas/deposito_3d_media.png)

## Instalação e execução

São necessárias apenas as dependências de `requirements.txt`: Pygame 2.6.1 e PyOpenGL 3.1.10. Use uma sessão gráfica local com suporte ao **OpenGL 2.1 / pipeline fixo**. Não é necessário instalar GLUT, NumPy, modelos, fontes ou texturas externas. Depois da instalação, o programa funciona sem internet.

### Neste computador, com o ambiente já preparado

```bash
cd "/Users/caiotoscano/Documents/Computação Gráfica/ProjetoFinal"
source .venv/bin/activate
python main.py
```

### Instalação nova no macOS ou Linux

Abra o terminal na pasta `ProjetoFinal` e execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Instalação nova no Windows (PowerShell)

Abra o terminal na pasta `ProjetoFinal` e execute:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

No Prompt de Comando, a ativação é `.venv\Scripts\activate.bat`. Se o PowerShell bloquear o script de ativação, use diretamente o Python do ambiente, sem mudar a política do sistema:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Para sair do ambiente virtual no terminal: `deactivate`. Ao copiar o projeto para outra máquina, recrie `.venv`; ambientes virtuais não são portáveis.

### Testes

Com o terminal na pasta do projeto:

```bash
python -m unittest discover -s tests -v
```

Esses testes usam apenas a biblioteca padrão: não abrem janela nem precisam de Pygame ou PyOpenGL instalados.

Verificação gráfica opcional, com as dependências instaladas e uma sessão gráfica disponível:

```bash
python tests/verificar_grafico.py
```

Esse comando abre uma janela por um breve período, exercita os controles com eventos simulados, verifica transições e salva/substitui as imagens de `capturas/`. Não precisa ser executado para jogar. Os testes usam `assert`; execute sem a opção `-O` do Python.

## Controles

No menu principal: **1** inicia uma partida nova, **2** abre o depósito 3D e **Esc** sai. As opções também aceitam 1 e 2 do teclado numérico. Fechar a janela encerra o programa em qualquer tela.

### Jogo 2D

| Tecla | Ação |
| --- | --- |
| Setas ou WASD | Mover o jogador, inclusive na diagonal |
| P | Pausar ou retomar |
| Enter, na pausa | Retomar |
| R, na pausa, derrota ou vitória | Reiniciar com três vidas, zero pontos e zero entregas |
| Enter, na derrota ou vitória | Reiniciar |
| Esc | Voltar ao menu principal |
| Q, na pausa, derrota ou vitória | Sair do programa |

A partida também pausa quando a janela perde o foco. Retome com P ou Enter. Na pausa ficam congelados jogador, três caixas, invulnerabilidade e processamento de coleta/entrega. Reiniciar restaura as posições e sentidos iniciais, as três vidas e a encomenda na coleta, sem pontos nem entregas acumuladas.

### Ambiente 3D

| Entrada | Ação |
| --- | --- |
| Arrastar com o botão esquerdo | Girar horizontal e verticalmente |
| Setas esquerda/direita | Girar horizontalmente |
| Setas cima/baixo | Aumentar/diminuir a elevação |
| Rodinha para cima/baixo | Aproximar/afastar |
| + ou = | Aproximar; também aceita + do teclado numérico |
| - | Afastar; também aceita - do teclado numérico |
| L | Alternar luz: média → forte → fraca → média |
| R | Restaurar a câmera inicial; mantém a luz escolhida |
| Esc | Voltar ao menu principal |

Ao entrar novamente no 3D, câmera e luz voltam aos valores iniciais. A tecla `=` é uma alternativa para teclados nos quais `+` depende de Shift.

## Organização

| Arquivo | Responsabilidade |
| --- | --- |
| `main.py` | Inicialização, loop principal, eventos e troca de telas |
| `jogo_2d.py` | Retângulos, colisões, regras, pontuação e desenho 2D |
| `ambiente_3d.py` | Caixas, normais, piso, paredes, câmera e iluminação |
| `desenho.py` | Projeção ortográfica, primitivas, menus e texto com cache |
| `tests/test_logica.py` | 18 testes de regras e geometria sem janela |
| `tests/verificar_grafico.py` | Integração com contexto OpenGL real e capturas |
| `requirements.txt` | Duas dependências de execução com versões fixadas |
| `capturas/` | Imagens produzidas pela verificação gráfica |

Os exercícios existentes na pasta superior, incluindo `teste.py`, foram preservados. Nenhum módulo abre uma janela ao ser importado: o ponto de entrada é o bloco `if __name__ == "__main__"` de `main.py`.

## Relação com o enunciado

O documento de referência é `Projeto.pdf`, fornecido para consulta. As escolhas de tema, controles e organização seguem o pedido de implementação.

| Requisito do professor | Como o projeto atende | Arquivo e função responsáveis |
| --- | --- | --- |
| Python e OpenGL no 2D | Retângulos, linhas e interface renderizados por OpenGL | `desenho.py`: `retangulo`, `linha`; `jogo_2d.py`: `desenhar` |
| Jogo com pelo menos quatro objetos | Jogador e três caixas móveis, além da encomenda e áreas demarcadas | `jogo_2d.py`: `Jogo.reiniciar`, `desenhar` |
| Um objeto movido pelo tempo | Três caixas avançam automaticamente e refletem nos limites próprios | `jogo_2d.py`: `mover_caixa`, `Jogo.atualizar` |
| Outro objeto movido pelo teclado | Setas/WASD movimentam o quadrado azul | `main.py`: `Aplicacao.atualizar`; `jogo_2d.py`: `Jogo.atualizar` |
| Pontuação visível | Cem pontos por entrega, com meta de cinco entregas | `jogo_2d.py`: `Jogo.pontos`, `Jogo.atualizar`, `desenhar` |
| Colisão com penalidade | AABB retira uma vida, devolve a encomenda à coleta, reposiciona e dá proteção temporária | `jogo_2d.py`: `colidem`, `Jogo.atualizar`, `Jogo.reaparecer` |
| Respeitar limites da janela | Toda a extensão do jogador e das três caixas fica na área delimitada | `jogo_2d.py`: `mover_caixa`, `Jogo.atualizar` |
| Menu para iniciar, pausar e desligar | Menu principal, painel de pausa e opções de saída | `desenho.py`: `menu_principal`, `painel`; `main.py`: `Aplicacao.tecla`, `Aplicacao.tecla_jogo` |
| Ambiente 3D em Python/OpenGL com cinco objetos | Cinco paralelepípedos, além de piso e duas paredes | `ambiente_3d.py`: `CAIXAS`, `cubo`, `desenhar` |
| Variações de luminosidade | L muda a intensidade difusa de uma fonte de luz real | `ambiente_3d.py`: `Ambiente.alternar_luz`, `configurar_3d` |
| Diferentes ângulos de visualização | Câmera orbital com ângulo horizontal e elevação | `ambiente_3d.py`: `Ambiente.girar`, `Ambiente.posicao_camera` |
| Mouse/teclado, rotações e aproximações | Arrastar/setas giram; rodinha e +/=/- mudam a distância | `main.py`: `Aplicacao.evento`, `Aplicacao.atualizar`; `ambiente_3d.py`: `Ambiente.aproximar` |

## Explicação dos conceitos

### Loop principal e delta time

Em `main.main`, o laço lê eventos, atualiza o estado, desenha a tela e troca os buffers. `Clock.tick(60)` limita a frequência desejada a 60 quadros por segundo e informa o intervalo desde o quadro anterior. Dividir por 1.000 converte milissegundos em segundos.

O movimento é `deslocamento = velocidade × dt`. O jogador anda a 260 pixels por segundo; as caixas A, B e C, a 155, 115 e 145. Cada `Caixa` guarda seu retângulo, eixo, velocidade com sinal e limites. `mover_caixa` usa esses dados para mover e refletir qualquer uma das três, sem repetir a lógica. `Jogo.atualizar` divide a direção do jogador pelo seu comprimento, calculado por `hypot`, para impedir que a diagonal seja mais rápida. O `dt` é limitado a 0,05 segundo para evitar saltos em travamentos. Nesse caso extremo, a simulação descarta o excesso: não tenta recuperar o tempo perdido.

### Colisão AABB, vidas e invulnerabilidade

Cada `Retangulo` guarda posição, largura e altura. `colidem` verifica se os intervalos ocupados pelos dois retângulos se sobrepõem em **x e y ao mesmo tempo**. Encostar exatamente na borda não conta como colisão.

Uma colisão reduz uma vida e chama `Jogo.reaparecer`, que escolhe a primeira posição livre de uma pequena lista. A mesma função `colidem` verifica tanto as batidas quanto a segurança do reaparecimento. `invulneravel` recebe um segundo e diminui apenas durante a partida. Enquanto for positivo, novas colisões não retiram vidas; o jogador fica azul-claro para mostrar essa condição. Isso impede que uma batida retire várias vidas em quadros consecutivos.

Ao receber dano, `carregando` volta a `False`, devolvendo a encomenda à coleta. `entregas` não muda. Um `return` encerra a atualização naquele quadro antes de verificar coleta ou entrega, inclusive se o reaparecimento estivesse dentro de uma dessas áreas.

### Pausa, pontuação e reinício

`Jogo.estado` pode ser `jogando`, `pausado`, `fim` (derrota) ou `vitoria`. `Jogo.atualizar` retorna imediatamente quando não está jogando. Assim, nenhum objeto, ponto, temporizador ou interação de coleta/entrega avança. O menu principal também não chama essa atualização.

`carregando` é um booleano: entrar na coleta sem encomenda o torna verdadeiro; entrar na entrega com encomenda o torna falso e incrementa `entregas`. Isso impede contar repetidamente uma entrega enquanto o jogador permanece na área. A colisão AABB também detecta a entrada nessas duas áreas. `Jogo.pontos` calcula `entregas × PONTOS_POR_ENTREGA`, sem acumulador de tempo. Ao chegar a `META_ENTREGAS`, o estado muda para `vitoria`.

O relógio da aplicação continua sendo consultado na pausa e o intervalo de uma transição é descartado, evitando um salto ao retomar. `Jogo.reiniciar` restaura todos os valores, incluindo posições e velocidades iniciais das três caixas, entregas e estado da encomenda.

### Projeção ortográfica e perspectiva

`desenho.configurar_2d` usa `glOrtho`: x cresce para a direita e y para baixo, em uma área lógica de 960 × 720. Distâncias não mudam com a profundidade. Isso facilita desenhar o tabuleiro e colocar textos em posições fixas.

`ambiente_3d.configurar_3d` usa `gluPerspective`, com campo de visão de 48 graus e planos de corte em 0,1 e 80 unidades. Objetos distantes parecem menores, produzindo a sensação de profundidade. A interface 3D troca temporariamente para a projeção ortográfica e depois restabelece os estados 3D. Cada cena configura iluminação, profundidade, transparência e textura explicitamente.

### Transformações das caixas

`ambiente_3d.cubo` parte de um cubo com coordenadas entre -1 e +1. `glScalef` aplica metade das dimensões desejadas. `glTranslatef` coloca o centro na posição escolhida, com y igual à metade da altura: a base fica exatamente em y = 0, apoiada no piso.

Embora a translação apareça antes da escala no código, a composição da matriz aplica a escala ao vértice antes da translação. `glPushMatrix` e `glPopMatrix` isolam cada caixa, para que sua transformação não afete a próxima.

### Câmera orbital

`Ambiente.posicao_camera` converte distância, ângulo horizontal e elevação em coordenadas cartesianas usando seno e cosseno. `gluLookAt` coloca a câmera nessa posição e a orienta para o alvo `(0, 0.8, 0)`.

A elevação fica entre 12 e 75 graus e a distância entre 10 e 27 unidades. Esses limites mantêm a câmera acima do piso e fora das caixas, sem permitir um afastamento excessivo. `R` restaura o enquadramento que mostra as cinco caixas.

### Normais e iluminação

Uma normal é um vetor perpendicular à superfície. A lista `FACES` define os quatro vértices e a normal de cada face. A iluminação compara a direção da normal com a direção da luz: faces voltadas para a fonte recebem mais iluminação difusa.

`GL_NORMALIZE` mantém as normais com comprimento unitário após as escalas não uniformes das caixas. `GL_COLOR_MATERIAL` faz as cores definidas no código participarem da iluminação. Há uma contribuição ambiente de 0,20 e uma fonte pontual cuja intensidade difusa alterna entre 0,22, 0,55 e 0,95. A luz é posicionada depois de configurar a câmera, ficando fixa no mundo. O fundo não muda ao apertar L.

### Profundidade e paredes

`GL_DEPTH_TEST` compara a profundidade dos fragmentos para mostrar a superfície mais próxima em cada pixel, mesmo que as caixas sejam desenhadas em outra ordem. O buffer de profundidade é limpo a cada quadro.

As paredes são planos orientados para dentro, com os vértices em sentido anti-horário quando vistos do interior. `GL_CULL_FACE` descarta seus lados externos. Ao orbitar por trás, a parede externa desaparece e permite enxergar as caixas. É uma simplificação deliberada, não uma parede transparente.

### Texto e recursos

`Textos.escrever` usa a fonte padrão incluída no Pygame, transforma sua superfície em textura RGBA e a aplica a um quadrilátero OpenGL. A inversão vertical dos pixels e as coordenadas de textura mantêm as letras na orientação correta. A mistura de transparência preserva as bordas suavizadas.

Fontes são reutilizadas por tamanho. O cache guarda até 96 textos e reutiliza o mesmo texto enquanto o conteúdo não mudar. Quando o limite é atingido, a textura menos recentemente usada é excluída com `glDeleteTextures`. No encerramento, `Textos.liberar` remove as texturas restantes antes de fechar o contexto.

## Roteiro de apresentação: aproximadamente dez minutos

| Tempo | Demonstração e explicação |
| --- | --- |
| 0:00–1:00 | Apresente o tema, as duas partes e o uso de Python, Pygame e OpenGL. |
| 1:00–2:15 | Inicie o 2D, mostre as três caixas móveis, colete uma encomenda e entregue para ganhar 100 pontos. Explique a meta de cinco entregas. |
| 2:15–3:15 | Encoste em uma caixa durante o transporte: mostre perda de vida, reaparecimento, devolução da encomenda e preservação das entregas anteriores. |
| 3:15–4:00 | Pause, observe a pontuação congelada, retome e reinicie pelo menu de pausa. |
| 4:00–5:00 | Abra o 3D, conte as cinco caixas e aponte piso e paredes como elementos adicionais. |
| 5:00–6:30 | Gire com mouse e setas, aproxime pela rodinha, alterne as três luzes e restaure a câmera. |
| 6:30–9:30 | Mostre `main.main`, `colidem`, `Jogo.atualizar`, `cubo` e `configurar_3d`. Explique dt, pausa, projeção, normais e profundidade com a cena como exemplo. |
| 9:30–10:00 | Mostre os testes e conclua relacionando as demonstrações aos requisitos. |

Para experimentar, suba até a coleta verde e leve a encomenda à entrega amarela, desviando das caixas. Para demonstrar uma batida, entre na trajetória da caixa B, na região central. Para reiniciar sem esperar o fim, use **P e depois R**. Ensaie a apresentação: a documentação serve de apoio, não precisa ser lida integralmente.

## Verificação realizada em 01/11/2026

Ambiente efetivamente utilizado: **macOS 27.0.1, ARM64, Apple M4, Python 3.9.6, Pygame 2.6.1, SDL 2.28.4 e PyOpenGL 3.1.10**. O contexto informou `OpenGL 2.1 Metal - 91.7`.

| Verificação | Resultado |
| --- | --- |
| 18 testes `unittest` | Aprovados: AABB, limites, diagonal, dt, três trajetórias e reflexões, áreas seguras, dano/proteção, reaparecimento, coleta única, entrega única, transporte com dano, pausa, vitória, derrota, reinício e câmera/geometria |
| Compilação dos quatro módulos | Aprovada; cache direcionado à pasta temporária local |
| `python -m pip check` | Nenhuma dependência quebrada |
| Integração com OpenGL real | Aprovada; sem erros GL nas verificações de quadro |
| Controle por eventos simulados | Três caixas, coleta/transporte/entrega, pausa/retomada, dano com encomenda, derrota, cinco entregas, vitória e opções de reinício/menu/saída aprovados; testes 3D preservados e aprovados |
| Troca repetida de cenas e cache | Seis ciclos menu/2D/3D aprovados; 110 textos variáveis mantiveram o limite de 96 texturas |
| Inspeção das imagens | Capturas atualizadas do 2D, encomenda no jogador, entrega, pausa, derrota e vitória inspecionadas; capturas 3D já verificadas na versão anterior |
| Interação pela janela | Coleta pelo teclado, transporte, entrega de 100 pontos, permanência sem nova pontuação, pausa/retomada e reinício conferidos nesta revisão; controles 3D conferidos na versão anterior |
| Encerramento | Q na pausa encerrou com código 0 nesta revisão; evento de fechamento aprovado na integração. Botão de fechar já conferido na versão anterior |

As capturas incluem `menu.png`, `jogo_2d.png`, `transporte.png`, `entrega.png`, `colisao.png`, `pausa.png`, `fim_de_jogo.png`, `vitoria.png` e imagens do 3D com luz fraca, média, forte e câmera alterada. As sequências completas até derrota e vitória foram validadas por lógica e integração, com inspeção das capturas resultantes. `ambiente_3d.py` e `requirements.txt` permaneceram inalterados nesta revisão.

## Limitações e diagnóstico

- O jogo tem dificuldade fixa e trajetórias previsíveis, sem fases, perseguição ou colisão entre obstáculos. Existem corredores seguros para desviar; ficar parado não gera pontos nem conclui a meta.
- Colisões são discretas, por quadro, sem física realista. As velocidades atuais e o limite de dt evitam atravessar os obstáculos; aumentos grandes de velocidade exigiriam rever essa lógica.
- O 3D é uma cena independente e estática, sem colisão de câmera, sombras projetadas, materiais avançados ou modelos externos. Em ângulos rasantes algumas caixas podem encobrir outras; R retorna ao enquadramento de demonstração.
- A janela tem tamanho fixo e não há tratamento especial de alta densidade de pixels. Em telas Retina, o sistema pode ampliar a imagem lógica.
- Windows, Linux, outros drivers e todos os layouts de teclado **não foram verificados**. Os comandos de instalação são fornecidos, mas não representam garantia de compatibilidade nesses ambientes.
- É necessário um contexto compatível com OpenGL tradicional. Sessões sem interface gráfica, drivers sem esse suporte ou ambientes restritos podem impedir a janela. Na implementação, a primeira execução restrita abortou; a execução na sessão gráfica local funcionou. Se ocorrer, execute pelo terminal local e verifique o suporte gráfico da máquina. Os testes de lógica continuam disponíveis sem janela.
- Neste ambiente, PyOpenGL emite uma mensagem de que o módulo opcional NumPy não está presente e usa o suporte da biblioteca padrão. Isso não impediu renderização nem testes; NumPy não é dependência deste projeto.

Não há persistência de pontuação. Ao sair ou iniciar novamente pelo menu, a partida anterior é descartada.
