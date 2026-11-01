"""Primitivas OpenGL e um cache limitado para texto feito com Pygame."""

from collections import OrderedDict

import pygame
from OpenGL import GL as gl

from jogo_2d import LARGURA, ALTURA

# Cores RGB usam valores de 0 a 1. Quando houver um quarto valor, ele é o alfa
# (opacidade): 0 é transparente e 1 é opaco.
BRANCO = (0.94, 0.96, 1.0)
SUAVE = (0.66, 0.73, 0.81)
AMARELO = (1.0, 0.77, 0.30)
LIMITE_TEXTURAS = 96


def configurar_2d():
    """Coordenadas em pixels, origem superior esquerda, sem luz/profundidade."""
    # OpenGL mantém seus estados entre chamadas. Desligamos os recursos do 3D
    # para que iluminação, faces descartadas ou profundidade não ocultem a interface.
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glDisable(gl.GL_LIGHT0)
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glDisable(gl.GL_NORMALIZE)
    gl.glDisable(gl.GL_COLOR_MATERIAL)
    gl.glDisable(gl.GL_TEXTURE_2D)
    # Mistura a cor desenhada com a que já está no fundo usando o alfa.
    # É necessária para o painel translúcido e para o contorno suave das letras.
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    # PROJECTION define como coordenadas viram imagem. A ordem ALTURA, 0
    # faz y crescer para baixo, facilitando posicionar textos e retângulos.
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0, LARGURA, ALTURA, 0, -1, 1)
    # MODELVIEW guarda câmera/transformações. A identidade evita herdar as do 3D.
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()


def retangulo(x, y, largura, altura, cor):
    # Uma face preenchida com quatro cantos; sem alfa informado, usamos opacidade 1.
    gl.glColor4f(*cor[:3], cor[3] if len(cor) == 4 else 1.0)
    gl.glBegin(gl.GL_QUADS)
    for px, py in ((x, y), (x + largura, y), (x + largura, y + altura), (x, y + altura)):
        gl.glVertex2f(px, py)
    gl.glEnd()


def linha(x1, y1, x2, y2, cor):
    # Dois vértices formam um segmento, usado para a grade do piso 2D.
    gl.glColor3f(*cor)
    gl.glBegin(gl.GL_LINES)
    gl.glVertex2f(x1, y1)
    gl.glVertex2f(x2, y2)
    gl.glEnd()


class Textos:
    # O Pygame gera os pixels das letras; quem os exibe na janela é o OpenGL.
    # Guardamos fontes e texturas para não recriá-las a cada quadro.
    def __init__(self):
        self.fontes = {}
        self.cache = OrderedDict()

    def escrever(self, conteudo, x, y, tamanho=24, cor=BRANCO):
        # O cache identifica o texto pelo conteúdo e tamanho. A imagem é branca,
        # então pode ser reutilizada com cores diferentes na hora de desenhar.
        chave = (conteudo, tamanho)
        if chave not in self.cache:
            if tamanho not in self.fontes:
                self.fontes[tamanho] = pygame.font.Font(None, tamanho)
            superficie = self.fontes[tamanho].render(conteudo, True, (255, 255, 255))
            largura, altura = superficie.get_size()
            # A imagem é invertida verticalmente para a convenção de texturas GL.
            pixels = pygame.image.tostring(superficie, "RGBA", True)
            textura = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, textura)
            # Filtro linear suaviza a amostragem; CLAMP_TO_EDGE evita repetir a
            # imagem nas bordas. TexImage2D envia os pixels RGBA para a textura.
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, largura, altura, 0,
                            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, pixels)
            self.cache[chave] = (textura, largura, altura)
            # OrderedDict registra a ordem de uso. Ao atingir o limite,
            # removemos a menos usada recentemente e liberamos sua memória gráfica.
            if len(self.cache) > LIMITE_TEXTURAS:
                _, antigo = self.cache.popitem(last=False)
                gl.glDeleteTextures([antigo[0]])
        self.cache.move_to_end(chave)
        textura, largura, altura = self.cache[chave]
        # Aplicamos a textura a um retângulo do tamanho do texto.
        # (u, v) percorre a imagem de 0 a 1; (px, py) posiciona os cantos na tela.
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, textura)
        gl.glColor3f(*cor)
        gl.glBegin(gl.GL_QUADS)
        for u, v, px, py in ((0, 1, x, y), (1, 1, x + largura, y),
                              (1, 0, x + largura, y + altura), (0, 0, x, y + altura)):
            gl.glTexCoord2f(u, v)
            gl.glVertex2f(px, py)
        gl.glEnd()
        # Deixar a textura ligada afetaria os próximos retângulos de cor sólida.
        gl.glDisable(gl.GL_TEXTURE_2D)

    def liberar(self):
        # Deve ser chamada antes de fechar a janela, enquanto o contexto GL existe.
        if self.cache:
            gl.glDeleteTextures([item[0] for item in self.cache.values()])
            self.cache.clear()


def painel(textos, titulo, subtitulo, opcoes):
    # Desenha por cima da cena: escurece o fundo, cria o cartão e lista as opções.
    # Apenas apresenta o menu; main.py interpreta as teclas e muda o estado.
    retangulo(0, 0, LARGURA, ALTURA, (0.01, 0.02, 0.04, 0.78))
    retangulo(220, 177, 520, 386, (0.08, 0.11, 0.16))
    retangulo(220, 177, 6, 386, AMARELO)
    textos.escrever(titulo, 260, 216, 38, AMARELO)
    textos.escrever(subtitulo, 260, 273, 24, SUAVE)
    for i, opcao in enumerate(opcoes):
        textos.escrever(opcao, 260, 333 + i * 46, 28)


def menu_principal(textos):
    # A mesma projeção e os mesmos utilitários servem ao menu, ao jogo e ao HUD 3D.
    configurar_2d()
    retangulo(0, 0, LARGURA, ALTURA, (0.045, 0.065, 0.10))
    textos.escrever("COMPUTAÇÃO GRÁFICA / PYTHON + OPENGL", 80, 85, 24, SUAVE)
    textos.escrever("DEPÓSITO", 80, 152, 72)
    textos.escrever("Desafio das Caixas", 83, 227, 40, AMARELO)
    textos.escrever("Complete cinco entregas no 2D. Explore as formas e a luz no 3D.", 83, 293, 26, SUAVE)
    for i, opcao in enumerate(("1 — Iniciar jogo 2D", "2 — Explorar ambiente 3D", "Esc — Sair")):
        retangulo(80, 365 + i * 73, 800, 57, (0.10, 0.14, 0.19))
        textos.escrever(opcao, 103, 380 + i * 73, 30)
    textos.escrever("Escolha uma opção pelo teclado.", 83, 634, 23, SUAVE)
