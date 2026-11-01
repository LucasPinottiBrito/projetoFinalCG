"""Câmera orbital e depósito com cinco caixas, usando o pipeline fixo."""

from math import cos, sin, radians

# Ângulos em graus; distância em unidades do mundo 3D, não em pixels.
# Os limites mantêm a câmera acima do piso e evitam zoom exagerado.
ANGULO_INICIAL = 35.0
ELEVACAO_INICIAL = 32.0
DISTANCIA_INICIAL = 19.0
ELEVACAO_MINIMA, ELEVACAO_MAXIMA = 12.0, 75.0
DISTANCIA_MINIMA, DISTANCIA_MAXIMA = 10.0, 27.0
VELOCIDADE_ROTACAO = 65.0
VELOCIDADE_ZOOM = 8.0
SENSIBILIDADE_MOUSE = 0.35
# Cada opção associa o nome mostrado na interface à intensidade da luz difusa.
LUZES = (("Fraca", 0.22), ("Média", 0.55), ("Forte", 0.95))

# (x, z), (largura, altura, profundidade), cor. O piso é y = 0.
CAIXAS = (
    ((-3.5, -2.7), (1.7, 1.8, 1.7), (0.85, 0.48, 0.22)),
    ((0.0, -2.9), (1.6, 2.3, 1.6), (0.35, 0.65, 0.82)),
    ((3.4, -2.5), (1.8, 1.4, 1.7), (0.72, 0.36, 0.26)),
    ((-2.5, 1.4), (1.9, 1.3, 1.8), (0.55, 0.72, 0.40)),
    ((2.0, 1.6), (1.7, 1.7, 1.7), (0.87, 0.69, 0.30)),
)

# Cada face tem quatro vértices anti-horários vistos por fora e uma normal.
# A normal aponta perpendicularmente para fora da face e orienta a iluminação.
# Reutilizamos este cubo base para todas as caixas, alterando escala e posição.
FACES = (
    ((0, 0, 1), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))),
    ((0, 0, -1), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1))),
    ((1, 0, 0), ((1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1))),
    ((-1, 0, 0), ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1))),
    ((0, 1, 0), ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1))),
    ((0, -1, 0), ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1))),
)


class Ambiente:
    # Guarda apenas câmera e luz. A geometria é fixa e independe da partida 2D.
    def __init__(self):
        self.luz = 1
        self.restaurar_camera()

    def restaurar_camera(self):
        # R restaura o enquadramento, mas preserva a intensidade de luz escolhida.
        self.angulo = ANGULO_INICIAL
        self.elevacao = ELEVACAO_INICIAL
        self.distancia = DISTANCIA_INICIAL

    def girar(self, horizontal, vertical):
        # O módulo permite dar voltas completas; a elevação fica limitada para
        # não atravessar o piso nem virar a câmera de cabeça para baixo.
        self.angulo = (self.angulo + horizontal) % 360
        self.elevacao = max(ELEVACAO_MINIMA, min(ELEVACAO_MAXIMA, self.elevacao + vertical))

    def aproximar(self, quantidade):
        # Quantidade positiva reduz a distância ao alvo; negativa afasta.
        self.distancia = max(DISTANCIA_MINIMA, min(DISTANCIA_MAXIMA, self.distancia - quantidade))

    def alternar_luz(self):
        # Ao passar da última opção, o resto da divisão retorna ao índice zero.
        self.luz = (self.luz + 1) % len(LUZES)

    def posicao_camera(self):
        # sin/cos recebem radianos. A elevação determina a altura e o raio da
        # projeção horizontal; o ângulo distribui esse raio entre os eixos x e z.
        a, e = radians(self.angulo), radians(self.elevacao)
        # Conversão esférica -> cartesiana, em torno do alvo (0, 0.8, 0).
        return (self.distancia * cos(e) * sin(a),
                0.8 + self.distancia * sin(e),
                self.distancia * cos(e) * cos(a))


def face(normal, vertices):
    # Importação local permite testar a câmera e os dados geométricos sem OpenGL.
    from OpenGL import GL as gl
    gl.glBegin(gl.GL_QUADS)
    # A normal informada vale para os quatro vértices desta face plana.
    gl.glNormal3f(*normal)
    for vertice in vertices:
        gl.glVertex3f(*vertice)
    gl.glEnd()


def cubo(posicao, dimensoes, cor):
    from OpenGL import GL as gl
    # Salvamos a matriz da câmera para que a transformação desta caixa não
    # altere as seguintes. PopMatrix recupera essa matriz ao terminar.
    gl.glPushMatrix()
    # O cubo base vai de -1 a +1. Primeiro escala, depois translada no mundo.
    # A composição das matrizes aplica a escala antes da translação ao vértice,
    # embora Translate apareça primeiro. Centro em altura/2 apoia a base no piso.
    gl.glTranslatef(posicao[0], dimensoes[1] / 2, posicao[1])
    gl.glScalef(*(d / 2 for d in dimensoes))
    gl.glColor3f(*cor)
    for normal, vertices in FACES:
        face(normal, vertices)
    gl.glPopMatrix()


def configurar_3d(ambiente):
    from OpenGL import GL as gl
    from OpenGL.GLU import gluPerspective, gluLookAt
    from jogo_2d import LARGURA, ALTURA

    # Reconfiguramos os estados a cada desenho, inclusive depois de exibir menus.
    # A cena usa superfícies opacas com cor sólida, sem texturas.
    gl.glDisable(gl.GL_BLEND)
    gl.glDisable(gl.GL_TEXTURE_2D)
    # O teste de profundidade mantém a superfície mais próxima em cada pixel,
    # independentemente da ordem em que as caixas são desenhadas.
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDepthFunc(gl.GL_LESS)
    # Descartamos o verso das faces. CCW identifica a frente pela ordem
    # anti-horária dos vértices; isso também permite enxergar por trás das paredes.
    gl.glEnable(gl.GL_CULL_FACE)
    gl.glCullFace(gl.GL_BACK)
    gl.glFrontFace(gl.GL_CCW)
    # LIGHTING ativa o cálculo de luz, e LIGHT0 habilita a fonte usada aqui.
    # COLOR_MATERIAL permite que glColor defina a cor ambiente/difusa dos objetos.
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_LIGHT0)
    gl.glEnable(gl.GL_COLOR_MATERIAL)
    gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
    # Escalas não uniformes alteram o comprimento das normais: renormalizar.
    gl.glEnable(gl.GL_NORMALIZE)
    gl.glShadeModel(gl.GL_FLAT)
    # A perspectiva diminui objetos distantes: campo vertical de 48 graus,
    # proporção da janela e planos de corte próximo/distante em 0,1 e 80.
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gluPerspective(48, LARGURA / ALTURA, 0.1, 80.0)
    # LookAt recebe posição da câmera, alvo e direção 'para cima' (eixo y).
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    gluLookAt(*ambiente.posicao_camera(), 0, 0.8, 0, 0, 1, 0)
    # A luz ambiente evita faces totalmente pretas. A difusa varia com L e com
    # a orientação das faces; o componente especular está zerado (sem brilho).
    intensidade = LUZES[ambiente.luz][1]
    gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, (0.20, 0.20, 0.20, 1))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, (0, 0, 0, 1))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, (intensidade,) * 3 + (1,))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, (0, 0, 0, 1))
    # Definida depois da câmera: a luz permanece fixa no mundo, não na tela.
    # O último valor 1 indica uma fonte pontual, posicionada em (2, 8, 5).
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (2, 8, 5, 1))


def desenhar(ambiente, textos):
    from OpenGL import GL as gl
    from desenho import configurar_2d, retangulo, AMARELO, SUAVE

    configurar_3d(ambiente)
    # O piso está no plano xz (y = 0) e sua normal aponta para cima.
    gl.glColor3f(0.40, 0.44, 0.49)
    face((0, 1, 0), ((-6, 0, 5), (6, 0, 5), (6, 0, -5), (-6, 0, -5)))
    # As paredes são planos orientados para dentro. O descarte de faces externas
    # deixa ver o interior ao orbitar por trás, sem esconder as cinco caixas.
    gl.glColor3f(0.53, 0.59, 0.65)
    face((0, 0, 1), ((-6, 0, -5), (6, 0, -5), (6, 3.6, -5), (-6, 3.6, -5)))
    gl.glColor3f(0.44, 0.50, 0.57)
    face((1, 0, 0), ((-6, 0, 5), (-6, 0, -5), (-6, 3.6, -5), (-6, 3.6, 5)))
    for posicao, dimensoes, cor in CAIXAS:
        cubo(posicao, dimensoes, cor)

    # A interface usa coordenadas de tela e não recebe iluminação nem participa
    # do teste de profundidade, mantendo as instruções legíveis sobre a cena.
    configurar_2d()
    retangulo(0, 0, 960, 122, (0.035, 0.05, 0.08, 0.94))
    textos.escrever("DEPÓSITO 3D", 30, 18, 32)
    textos.escrever(f"L — Luz: {LUZES[ambiente.luz][0]}", 660, 22, 26, AMARELO)
    textos.escrever("Arraste com o botão esquerdo / Setas: girar", 30, 61, 23, SUAVE)
    textos.escrever("Rodinha / + (=) / -: aproximar e afastar", 30, 90, 23, SUAVE)
    textos.escrever("R — Restaurar câmera", 660, 61, 23, SUAVE)
    textos.escrever("Esc — Menu principal", 660, 90, 23, SUAVE)
    # A interface usa projeção própria; restabelecemos explicitamente o 3D.
    configurar_3d(ambiente)
