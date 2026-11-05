"""Galpão, caixas e interface. O desenho apenas consulta a simulação."""

from OpenGL import GL as gl
from OpenGL.GLU import gluLookAt, gluPerspective

from ambiente_3d import FACES
from desenho import AMARELO, BRANCO, SUAVE, configurar_2d, linha, retangulo
from deposito.matematica import Vetor3
from deposito.niveis import CORES, NIVEIS

LARGURA, ALTURA = 960, 720
_lista_cubo = None


def obter_cubo_gl():
    """Compila uma vez a geometria repetida; matrizes e cores continuam por objeto."""
    global _lista_cubo
    if _lista_cubo is None:
        _lista_cubo = gl.glGenLists(1)
        gl.glNewList(_lista_cubo, gl.GL_COMPILE)
        gl.glBegin(gl.GL_QUADS)
        for normal, vertices in FACES:
            gl.glNormal3f(*normal)
            for vertice in vertices:
                gl.glVertex3f(*vertice)
        gl.glEnd()
        gl.glEndList()
    return _lista_cubo


def liberar_recursos():
    global _lista_cubo
    if _lista_cubo is not None:
        gl.glDeleteLists(_lista_cubo, 1)
        _lista_cubo = None


def bloco(centro, metade, cor):
    gl.glPushMatrix()
    gl.glTranslatef(*centro)
    gl.glScalef(*metade)
    gl.glColor3f(*cor)
    gl.glCallList(obter_cubo_gl())
    gl.glPopMatrix()


def escrever_no_mundo(textos, texto, posicao, tamanho=32, cor=BRANCO, escala=0.018, piso=False):
    gl.glPushMatrix()
    gl.glTranslatef(*posicao)
    if piso:
        gl.glRotatef(-90, 1, 0, 0)
    gl.glScalef(escala, -escala, escala)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    textos.escrever(texto, 0, 0, tamanho, cor)
    gl.glDisable(gl.GL_BLEND)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glPopMatrix()


def configurar_camera(partida, menu):
    gl.glClearColor(0.16, 0.20, 0.23, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glDisable(gl.GL_TEXTURE_2D)
    gl.glDisable(gl.GL_BLEND)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gluPerspective(68 if not menu else 57, LARGURA/ALTURA, 0.07, 75)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    if menu:
        gluLookAt(13, 11, 17, 0, 0, -3, 0, 1, 0)
    else:
        origem = partida.jogador.olhos
        destino = origem+partida.jogador.direcao
        gluLookAt(*origem, *destino, 0, 1, 0)
    gl.glEnable(gl.GL_LIGHTING)
    gl.glEnable(gl.GL_LIGHT0)
    gl.glEnable(gl.GL_COLOR_MATERIAL)
    gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
    gl.glEnable(gl.GL_NORMALIZE)
    gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, (0.48, 0.49, 0.51, 1))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, (0.75, 0.73, 0.68, 1))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (2, 9, 3, 1))


def desenhar_area(area, textos):
    letra, nome, cor = CORES[area.categoria]
    x, z = area.centro.x, area.centro.z
    # Superfície levemente elevada para não disputar profundidade com o piso.
    bloco(Vetor3(x, 0.006, z), Vetor3(area.metade_x, 0.006, area.metade_z), tuple(c*0.28+0.12 for c in cor))
    for sinal in (-1, 1):
        bloco(Vetor3(x+sinal*area.metade_x, 0.022, z), Vetor3(0.04, 0.015, area.metade_z), cor)
        bloco(Vetor3(x, 0.022, z+sinal*area.metade_z), Vetor3(area.metade_x, 0.015, 0.04), cor)
    escrever_no_mundo(textos, f"{letra} / {nome}", Vetor3(x-1.15, 0.045, z+0.9), 28, cor, piso=True)
    # Porta de enrolar com nervuras e identificação, sem animação de expedição.
    bloco(Vetor3(x, 1.9, -9.53), Vetor3(1.48, 1.9, 0.04), (0.20, 0.25, 0.29))
    for altura in range(1, 13):
        bloco(Vetor3(x, altura*0.28, -9.475), Vetor3(1.46, 0.012, 0.015), (0.31, 0.37, 0.40))
    bloco(Vetor3(x, 3.95, -9.48), Vetor3(1.5, 0.14, 0.06), cor)
    escrever_no_mundo(textos, f"DOCA {letra}", Vetor3(x-1.1, 3.3, -9.41), 40, cor, 0.020)
    escrever_no_mundo(textos, nome, Vetor3(x-0.75, 2.55, -9.40), 26, SUAVE)


def desenhar_caixa(caixa, textos, organizada):
    gl.glPushMatrix()
    gl.glTranslatef(*caixa.posicao)
    x, y, z = caixa.eixos
    gl.glMultMatrixf((x.x, x.y, x.z, 0, y.x, y.y, y.z, 0, z.x, z.y, z.z, 0, 0, 0, 0, 1))
    letra, _, cor = CORES[caixa.categoria]
    bloco(Vetor3(), caixa.metade, cor)
    h = caixa.metade
    fita = (0.85, 0.78, 0.59)
    bloco(Vetor3(0, h.y+0.003, 0), Vetor3(0.055, 0.004, h.z+0.005), fita)
    bloco(Vetor3(0, 0, h.z+0.003), Vetor3(0.055, h.y, 0.004), fita)
    escrever_no_mundo(textos, letra, Vetor3(-h.x+0.07, 0.22, h.z+0.012), 38, BRANCO, 0.012)
    escrever_no_mundo(textos, letra, Vetor3(-0.18, h.y+0.014, 0.18), 32, BRANCO, 0.012, piso=True)
    if organizada:
        bloco(Vetor3(h.x-0.08, h.y-0.08, h.z+0.012), Vetor3(0.035, 0.035, 0.006), (0.8, 1, 0.8))
    gl.glPopMatrix()


def desenhar_galpao(partida, textos, menu=False):
    for corpo in partida.mundo.corpos:
        if corpo.nome == "teto" and not menu:
            bloco(corpo.posicao, corpo.metade, (0.34, 0.38, 0.38))
        elif corpo.nome in ("piso", "parede", "esteira", "lateral"):
            cor = {"piso": (0.40, 0.43, 0.43), "parede": (0.61, 0.64, 0.63),
                   "esteira": (0.12, 0.16, 0.17), "lateral": (0.58, 0.61, 0.58)}[corpo.nome]
            bloco(corpo.posicao, corpo.metade, cor)
    # Juntas do piso e estrutura do galpão dão escala ao deslocamento.
    gl.glDisable(gl.GL_LIGHTING)
    gl.glColor3f(0.32, 0.36, 0.36)
    gl.glBegin(gl.GL_LINES)
    for i in range(-10, 11, 2):
        gl.glVertex3f(i, 0.015, -9.7); gl.glVertex3f(i, 0.015, 9.7)
        gl.glVertex3f(-10.7, 0.015, i); gl.glVertex3f(10.7, 0.015, i)
    gl.glEnd()
    gl.glEnable(gl.GL_LIGHTING)
    for z in (-8, -2, 4, 9):
        bloco(Vetor3(0, 5.8, z), Vetor3(10.8, 0.12, 0.12), (0.19, 0.25, 0.29))
        for x in (-10.6, 10.6):
            bloco(Vetor3(x, 2.9, z), Vetor3(0.12, 2.9, 0.12), (0.22, 0.28, 0.30))
    for area in partida.areas:
        desenhar_area(area, textos)
    # Riscos na faixa acompanham sua velocidade de superfície, sem mover o colisor.
    fase = (partida.tempo*1.05) % 0.45
    for i in range(12):
        z = 3.13+i*0.45-fase
        if z >= 3.12:
            bloco(Vetor3(0, 0.987, z), Vetor3(0.82, 0.007, 0.018), (0.31, 0.37, 0.35))
    for x in (-0.65, 0.65):
        for z in (3.6, 7.8):
            bloco(Vetor3(x, 0.35, z), Vetor3(0.09, 0.35, 0.09), (0.29, 0.34, 0.34))
    escrever_no_mundo(textos, "RECEBIMENTO", Vetor3(-1.4, 2.5, 8.65), 36, AMARELO)
    for caixa in partida.caixas:
        desenhar_caixa(caixa, textos, caixa in partida.organizadas)


def desenhar_contatos(partida):
    gl.glDisable(gl.GL_LIGHTING)
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glColor3f(0.35, 1, 0.75)
    gl.glBegin(gl.GL_LINES)
    for corpo in partida.caixas+[partida.jogador.corpo]:
        vertices = corpo.vertices()
        for i, a in enumerate(vertices):
            for j, b in enumerate(vertices):
                if j > i and bin(i ^ j).count("1") == 1:
                    gl.glVertex3f(*a); gl.glVertex3f(*b)
    gl.glColor3f(1, 0.30, 0.18)
    for contato in partida.mundo.contatos:
        gl.glVertex3f(*contato.ponto)
        gl.glVertex3f(*(contato.ponto+contato.normal*0.3))
    gl.glEnd()
    gl.glEnable(gl.GL_DEPTH_TEST)


def desenhar_menu(partida, textos):
    configurar_2d()
    retangulo(0, 0, 510, ALTURA, (0.035, 0.06, 0.08, 0.95))
    retangulo(44, 59, 38, 4, AMARELO)
    textos.escrever("SIMULADOR / PRIMEIRA PESSOA", 44, 85, 23, SUAVE)
    textos.escrever("DEPÓSITO", 40, 125, 76)
    textos.escrever("Receba. Separe. Empilhe.", 44, 205, 31, AMARELO)
    textos.escrever("Organize as caixas na área da mesma cor.", 44, 257, 23, SUAVE)
    for i, nivel in enumerate(NIVEIS):
        y = 323+i*57
        textos.escrever(str(i+1), 44, y, 29, AMARELO)
        textos.escrever(nivel.nome, 84, y, 31)
        prazo = "sem prazo" if nivel.prazo is None else f"{int(nivel.prazo)} s"
        textos.escrever(f"{nivel.cores} cores / {nivel.quantidade} caixas / {prazo}", 84, y+29, 19, SUAVE)
    textos.escrever("5  Laboratório de física", 44, 578, 27, AMARELO)
    textos.escrever("Escolha pelo teclado. Esc para sair.", 44, 660, 22, SUAVE)


def desenhar_interface(partida, textos, fps):
    configurar_2d()
    retangulo(20, 18, 330, 86, (0.035, 0.06, 0.08, 0.90))
    textos.escrever("DEPÓSITO / "+partida.nivel.nome.upper(), 36, 31, 24, AMARELO)
    textos.escrever(f"Organizadas  {len(partida.organizadas):02d} / {partida.nivel.quantidade:02d}", 36, 64, 29)
    retangulo(724, 18, 216, 86, (0.035, 0.06, 0.08, 0.90))
    tempo = "TREINO LIVRE" if partida.restante is None else f"{int(partida.restante)//60:02d}:{int(partida.restante)%60:02d}"
    textos.escrever(tempo, 744, 31, 31, AMARELO)
    textos.escrever(f"Recebidas {partida.esteira.emitidas}/{partida.nivel.quantidade}", 744, 72, 21, SUAVE)
    alvo = partida.jogador.selecionar_caixa(partida.mundo)
    segurada = partida.jogador.segurada
    cor = AMARELO if alvo or segurada else BRANCO
    linha(472, 360, 478, 360, cor); linha(482, 360, 488, 360, cor)
    linha(480, 352, 480, 358, cor); linha(480, 362, 480, 368, cor)
    if segurada or alvo:
        caixa = segurada or alvo
        letra, nome, cor_caixa = CORES[caixa.categoria]
        texto = f"E / Soltar {letra} — {nome}" if segurada else f"E / Pegar {letra} — {nome}"
        retangulo(300, 403, 360, 37, (0.035, 0.06, 0.08, 0.8))
        textos.escrever(texto, 320, 412, 23, cor_caixa)
    if partida.jogador.carregando_arremesso:
        retangulo(350, 460, 260, 6, (0.18, 0.24, 0.28))
        retangulo(350, 460, 260*partida.jogador.carga/1.2, 6, AMARELO)
        textos.escrever("Solte para arremessar", 381, 480, 22, AMARELO)
    retangulo(0, 670, 960, 50, (0.035, 0.06, 0.08, 0.9))
    textos.escrever("WASD mover   E pegar / soltar   Esq. arremessar   Dir. girar   Esc pausa", 24, 687, 22, SUAVE)
    if partida.esteira.bloqueada:
        textos.escrever("Entrada ocupada — libere a esteira", 330, 120, 24, AMARELO)
    if partida.depurar:
        textos.escrever(f"F3 / {fps:.0f} FPS / {len(partida.mundo.contatos)} contatos / {partida.mundo.subdivisoes} subpassos", 24, 630, 23, AMARELO)
    if partida.estado != "jogando":
        retangulo(0, 0, 960, 720, (0.015, 0.025, 0.04, 0.82))
        titulo = {"pausado": "PARTIDA PAUSADA", "vitoria": "DEPÓSITO ORGANIZADO", "derrota": "TEMPO ESGOTADO"}[partida.estado]
        textos.escrever(titulo, 160, 235, 49, AMARELO)
        textos.escrever(f"{len(partida.organizadas)} caixas organizadas / {int(partida.tempo)} s", 163, 303, 30)
        acao = {"pausado": "Retomar", "derrota": "Repetir", "vitoria": "Próximo nível"}[partida.estado]
        opcoes = ["Enter / "+acao,
                  "R / Repetir", "M / Menu principal", "Q / Sair"]
        for i, opcao in enumerate(opcoes):
            textos.escrever(opcao, 164, 369+i*43, 27, SUAVE)


def desenhar(partida, textos, menu=False, fps=0):
    configurar_camera(partida, menu)
    desenhar_galpao(partida, textos, menu)
    if partida.depurar and not menu:
        desenhar_contatos(partida)
    if menu:
        desenhar_menu(partida, textos)
    else:
        desenhar_interface(partida, textos, fps)
