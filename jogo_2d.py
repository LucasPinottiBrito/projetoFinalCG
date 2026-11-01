"""Regras do Desafio das Caixas; importar este módulo não exige OpenGL."""

from dataclasses import dataclass
from math import hypot

# Medidas em pixels. A área jogável começa abaixo do cabeçalho da interface.
# Velocidades são em pixels/segundo; os temporizadores usam segundos.
LARGURA, ALTURA = 960, 720
ESQUERDA, TOPO, DIREITA, BASE = 40, 155, 920, 675
TAMANHO_JOGADOR = 36
VELOCIDADE_JOGADOR = 260.0
VIDAS_INICIAIS = 3
PONTOS_POR_ENTREGA = 100
META_ENTREGAS = 5
TEMPO_INVULNERAVEL = 1.0
DT_MAXIMO = 0.05
REAPARECIMENTOS = ((95, 580), (820, 580), (95, 400))


@dataclass
class Retangulo:
    # Dados compartilhados por jogador, obstáculos e áreas de interação.
    # (x, y) é o canto superior esquerdo. dataclass gera o construtor desses dados.
    x: float
    y: float
    largura: float
    altura: float


# Estas áreas fixas são usadas tanto na detecção de entrada quanto no desenho.
COLETA = Retangulo(60, 175, 125, 95)
ENTREGA = Retangulo(775, 555, 125, 100)


@dataclass
class Caixa:
    # Separa a forma visível (retângulo) dos dados que controlam sua trajetória.
    retangulo: Retangulo
    eixo: str
    velocidade: float  # pixels/s; o sinal indica o sentido do movimento
    minimo: float      # limites da coordenada x ou y do canto da caixa
    maximo: float


def mover_caixa(caixa, dt):
    """Mesma reflexão para trajetórias horizontais (x) e verticais (y)."""
    # getattr/setattr leem e escrevem o atributo indicado pelo nome 'x' ou 'y'.
    # Assim, a mesma conta funciona para os dois eixos.
    posicao = getattr(caixa.retangulo, caixa.eixo) + caixa.velocidade * dt
    # Refletimos a distância que passou do limite, em vez de descartá-la.
    # O dt limitado em Jogo.atualizar evita cruzar toda a trajetória num quadro.
    if posicao >= caixa.maximo:
        posicao = 2 * caixa.maximo - posicao
        caixa.velocidade = -abs(caixa.velocidade)
    elif posicao <= caixa.minimo:
        posicao = 2 * caixa.minimo - posicao
        caixa.velocidade = abs(caixa.velocidade)
    setattr(caixa.retangulo, caixa.eixo, posicao)


def colidem(a, b):
    """AABB: há colisão quando os intervalos se sobrepõem nos DOIS eixos.

    Apenas encostar nas bordas não conta como sobreposição.
    """
    return (a.x < b.x + b.largura and a.x + a.largura > b.x
            and a.y < b.y + b.altura and a.y + a.altura > b.y)


class Jogo:
    # Guarda o estado de uma partida. As regras não dependem de janela ou OpenGL,
    # permitindo exercitar movimento, colisões e resultados nos testes de lógica.
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        # Centralizar o estado inicial garante que iniciar e reiniciar façam
        # exatamente a mesma coisa, sem reaproveitar dados da partida anterior.
        self.jogador = Retangulo(*REAPARECIMENTOS[0], TAMANHO_JOGADOR, TAMANHO_JOGADOR)
        # A: superior; B: central; C: inferior, começando no sentido oposto a A.
        # Os limites incluem espaço para a caixa inteira, fora das áreas seguras.
        self.caixas = [
            Caixa(Retangulo(230, 230, 82, 62), "x", 155.0, 230, 735),
            Caixa(Retangulo(450, 335, 70, 70), "y", 115.0, 335, 465),
            Caixa(Retangulo(660, 565, 82, 62), "x", -145.0, 230, 660),
        ]
        self.vidas = VIDAS_INICIAIS
        self.entregas = 0
        self.carregando = False
        self.invulneravel = 0.0
        self.estado = "jogando"

    @property
    def pontos(self):
        # É um valor calculado, acessado como jogo.pontos. Não guardamos um segundo
        # contador que poderia ficar diferente do número de entregas realizadas.
        return self.entregas * PONTOS_POR_ENTREGA

    def alternar_pausa(self):
        # Vitória e derrota não voltam ao jogo por esta função: exigem reinício.
        if self.estado == "jogando":
            self.estado = "pausado"
        elif self.estado == "pausado":
            self.estado = "jogando"

    def reaparecer(self):
        # Testamos a área inteira do jogador contra a posição atual de cada caixa.
        # A primeira candidata livre é escolhida; não dependemos só da posição inicial.
        for x, y in REAPARECIMENTOS:
            candidato = Retangulo(x, y, TAMANHO_JOGADOR, TAMANHO_JOGADOR)
            if not any(colidem(candidato, caixa.retangulo) for caixa in self.caixas):
                self.jogador = candidato
                return
        # A faixa de baixo à esquerda fica fora de todas as trajetórias.
        raise RuntimeError("Nenhuma posição de reaparecimento livre no cenário.")

    def atualizar(self, dt, horizontal=0, vertical=0):
        # Este retorno congela TODA a simulação na pausa, vitória e derrota,
        # inclusive invulnerabilidade e interações nas áreas de coleta/entrega.
        if self.estado != "jogando":
            return
        # Protege contra intervalos enormes após uma interrupção e impede
        # que o contador de invulnerabilidade fique negativo.
        dt = max(0.0, min(dt, DT_MAXIMO))
        self.invulneravel = max(0.0, self.invulneravel - dt)

        # Normalização: a diagonal tem o mesmo módulo de velocidade dos eixos.
        modulo = hypot(horizontal, vertical)
        if modulo:
            self.jogador.x += horizontal / modulo * VELOCIDADE_JOGADOR * dt
            self.jogador.y += vertical / modulo * VELOCIDADE_JOGADOR * dt
        # Limitamos o canto superior esquerdo descontando o tamanho do jogador,
        # para que nem a borda direita nem a inferior ultrapassem o tabuleiro.
        self.jogador.x = max(ESQUERDA, min(self.jogador.x, DIREITA - self.jogador.largura))
        self.jogador.y = max(TOPO, min(self.jogador.y, BASE - self.jogador.altura))

        for caixa in self.caixas:
            mover_caixa(caixa, dt)

        # Usamos as posições já atualizadas. any reúne as três caixas em uma
        # única decisão de dano: mesmo tocando duas, perde-se só uma vida no quadro.
        if self.invulneravel <= 0 and any(
                colidem(self.jogador, caixa.retangulo) for caixa in self.caixas):
            self.vidas -= 1
            self.carregando = False  # a encomenda volta à coleta; entregas permanecem
            self.reaparecer()
            self.invulneravel = TEMPO_INVULNERAVEL
            if self.vidas == 0:
                self.estado = "fim"
            return  # Não coletar nem entregar no quadro em que houve dano.

        # A coleta só ocorre com as mãos vazias. Após entregar, carregando vira
        # False: permanecer na entrega não pode gerar novos pontos sem outra coleta.
        if not self.carregando and colidem(self.jogador, COLETA):
            self.carregando = True
        elif self.carregando and colidem(self.jogador, ENTREGA):
            self.carregando = False
            self.entregas += 1
            if self.entregas == META_ENTREGAS:
                self.estado = "vitoria"


def desenhar(jogo, textos):
    # Importação local mantém as regras testáveis só com a biblioteca padrão.
    from desenho import configurar_2d, retangulo, linha, painel, AMARELO, BRANCO, SUAVE

    # Desenhar apenas consulta o estado: não move objetos nem altera as regras.
    # Primeiro vêm o fundo e o cabeçalho, que ocupa uma faixa fora do tabuleiro.
    configurar_2d()
    retangulo(0, 0, LARGURA, ALTURA, (0.045, 0.065, 0.10))
    textos.escrever("DESAFIO DAS CAIXAS", 40, 26, 30, BRANCO)
    textos.escrever(f"Pontos: {jogo.pontos:05d}   |   Vidas: {jogo.vidas}", 555, 28, 28, AMARELO)
    textos.escrever("Setas / WASD: mover    P: pausar    Esc: menu principal", 40, 77, 23, SUAVE)
    textos.escrever(f"Entregas: {jogo.entregas}/{META_ENTREGAS}", 40, 113, 24, AMARELO)
    objetivo = "Leve à entrega" if jogo.carregando else "Busque uma encomenda"
    textos.escrever(objetivo, 270, 113, 24, BRANCO)

    # Um retângulo maior sob o piso cria a borda; linhas espaçadas formam a grade.
    retangulo(ESQUERDA - 3, TOPO - 3, DIREITA - ESQUERDA + 6, BASE - TOPO + 6, SUAVE)
    retangulo(ESQUERDA, TOPO, DIREITA - ESQUERDA, BASE - TOPO, (0.12, 0.16, 0.20))
    for x in range(ESQUERDA + 40, DIREITA, 40):
        linha(x, TOPO, x, BASE, (0.16, 0.20, 0.24))
    for y in range(TOPO + 40, BASE, 40):
        linha(ESQUERDA, y, DIREITA, y, (0.16, 0.20, 0.24))

    # Áreas coloridas são desenhadas antes dos objetos, para ficarem sob o jogador.
    for area, nome, cor in ((COLETA, "COLETA", (0.25, 0.78, 0.43)),
                            (ENTREGA, "ENTREGA", AMARELO)):
        retangulo(area.x, area.y, area.largura, area.altura, cor)
        retangulo(area.x + 3, area.y + 3, area.largura - 6, area.altura - 6,
                  tuple(c * 0.25 for c in cor))
        textos.escrever(nome, area.x + 12, area.y + 12, 24, cor)

    # A faixa clara lembra uma fita de embalagem; as letras distinguem as caixas.
    for nome, obstaculo in zip("ABC", jogo.caixas):
        caixa = obstaculo.retangulo
        cor = (0.88, 0.22, 0.20) if nome == "A" else (0.60, 0.36, 0.18)
        retangulo(caixa.x, caixa.y, caixa.largura, caixa.altura, cor)
        retangulo(caixa.x + caixa.largura / 2 - 5, caixa.y, 10, caixa.altura, (0.88, 0.66, 0.39))
        textos.escrever(nome, caixa.x + 9, caixa.y + 8, 22, BRANCO)
    # Azul-claro indica proteção temporária sem esconder o jogador da tela.
    jogador = jogo.jogador
    cor = (0.25, 0.62, 1.0) if jogo.invulneravel <= 0 else (0.65, 0.90, 1.0)
    retangulo(jogador.x, jogador.y, jogador.largura, jogador.altura, cor)
    retangulo(jogador.x + 10, jogador.y + 10, 16, 16, (0.10, 0.28, 0.52))

    # Um único booleano define onde está a encomenda: na coleta ou com o jogador.
    x, y = (jogador.x + 9, jogador.y + 9) if jogo.carregando else (COLETA.x + 53, COLETA.y + 53)
    retangulo(x, y, 18, 18, (0.96, 0.84, 0.63))
    retangulo(x + 7, y, 4, 18, (0.58, 0.35, 0.16))

    # O painel vem por último para se sobrepor à cena congelada.
    if jogo.estado == "pausado":
        painel(textos, "JOGO PAUSADO", "A partida está congelada.", [
            "P / Enter — Retomar", "R — Reiniciar", "Esc — Menu principal", "Q — Sair"])
    elif jogo.estado in ("fim", "vitoria"):
        titulo = "Vitória!" if jogo.estado == "vitoria" else "FIM DE JOGO"
        painel(textos, titulo, f"Pontuação final: {jogo.pontos} | Entregas: {jogo.entregas}/{META_ENTREGAS}", [
            "R / Enter — Reiniciar", "Esc — Menu principal", "Q — Sair"])
