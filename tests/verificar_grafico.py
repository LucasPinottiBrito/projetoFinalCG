"""Verificação opcional com contexto OpenGL real e eventos simulados.

Execute da pasta do projeto: python tests/verificar_grafico.py
Gera capturas em capturas/. Não substitui experimentar mouse/teclado físicos.
"""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from OpenGL import GL as gl
from legado import Aplicacao, criar_janela
from desenho import LIMITE_TEXTURAS
from jogo_2d import COLETA, ENTREGA, Jogo, META_ENTREGAS


def verificar():
    app = None
    pasta = Path(__file__).resolve().parents[1] / "capturas"
    pasta.mkdir(exist_ok=True)
    try:
        criar_janela()
        app = Aplicacao()

        def quadro(nome=None):
            pygame.event.pump()
            app.desenhar()
            gl.glFinish()
            assert gl.glGetError() == gl.GL_NO_ERROR
            if nome:
                pixels = gl.glReadPixels(0, 0, 960, 720, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
                superficie = pygame.image.fromstring(bytes(pixels), (960, 720), "RGBA", True)
                pygame.image.save(superficie, str(pasta / (nome + ".png")))
            pygame.display.flip()

        def tecla(tecla):
            app.evento(pygame.event.Event(pygame.KEYDOWN, key=tecla))

        def atualizar(dt=0.05, *pressionadas):
            teclas = defaultdict(int, {t: 1 for t in pressionadas})
            app.atualizar(dt, teclas)

        def entrar(area):
            app.jogo.jogador.x, app.jogo.jogador.y = area.x, area.y
            atualizar()

        quadro("menu")
        tecla(pygame.K_1)
        atualizar()  # descarta o intervalo da transição
        x = app.jogo.jogador.x
        caixas = deepcopy(app.jogo.caixas)
        atualizar(0.05, pygame.K_RIGHT)
        assert app.jogo.jogador.x > x
        assert all(c.retangulo != antes.retangulo for c, antes in zip(app.jogo.caixas, caixas))
        for _ in range(60):
            atualizar()
        assert app.jogo.pontos == 0
        quadro("jogo_2d")
        entrar(COLETA)
        assert app.jogo.carregando
        atualizar(0.05, pygame.K_RIGHT)
        quadro("transporte")
        tecla(pygame.K_p)
        antes = deepcopy(vars(app.jogo))
        for _ in range(10):
            atualizar(1, pygame.K_LEFT)
        assert vars(app.jogo) == antes
        quadro("pausa")
        tecla(pygame.K_RETURN)
        atualizar()
        atualizar()
        assert app.jogo.caixas != antes["caixas"]
        entrar(ENTREGA)
        assert (app.jogo.entregas, app.jogo.pontos, app.jogo.carregando) == (1, 100, False)
        for _ in range(10):
            atualizar()
        assert app.jogo.entregas == 1
        quadro("entrega")
        for vida in (2, 1, 0):
            entrar(COLETA)
            assert app.jogo.carregando
            app.jogo.invulneravel = 0
            entrar(app.jogo.caixas[1].retangulo)
            assert app.jogo.vidas == vida
            assert not app.jogo.carregando and app.jogo.pontos == 100
            if vida == 2:
                quadro("colisao")
        assert app.jogo.estado == "fim"
        quadro("fim_de_jogo")
        tecla(pygame.K_r)
        assert vars(app.jogo) == vars(Jogo())
        atualizar()
        for _ in range(META_ENTREGAS):
            entrar(COLETA)
            entrar(ENTREGA)
        assert app.jogo.estado == "vitoria" and app.jogo.pontos == 500
        antes = deepcopy(vars(app.jogo))
        atualizar(1, pygame.K_LEFT)
        assert vars(app.jogo) == antes
        quadro("vitoria")
        tecla(pygame.K_RETURN)
        assert vars(app.jogo) == vars(Jogo())
        atualizar()
        tecla(pygame.K_p)
        tecla(pygame.K_r)
        assert vars(app.jogo) == vars(Jogo())
        # As mesmas opções do fim de jogo também estão disponíveis na vitória.
        app.jogo.estado = "vitoria"
        tecla(pygame.K_r)
        assert vars(app.jogo) == vars(Jogo())
        app.jogo.estado = "vitoria"
        tecla(pygame.K_q)
        assert not app.rodando
        app.rodando = True
        tecla(pygame.K_ESCAPE)
        assert app.tela == "menu"
        tecla(pygame.K_1)
        assert vars(app.jogo) == vars(Jogo())
        tecla(pygame.K_ESCAPE)
        tecla(pygame.K_2)
        atualizar()
        for nome in ("media", "forte", "fraca"):
            quadro("deposito_3d_" + nome)
            tecla(pygame.K_l)
        inicial = app.ambiente.posicao_camera()
        app.evento(pygame.event.Event(pygame.MOUSEMOTION, rel=(220, 35), buttons=(1, 0, 0)))
        app.evento(pygame.event.Event(pygame.MOUSEWHEEL, y=2))
        assert app.ambiente.posicao_camera() != inicial
        quadro("deposito_3d_mouse")
        anterior = app.ambiente.posicao_camera()
        atualizar(0.05, pygame.K_LEFT, pygame.K_EQUALS)
        assert app.ambiente.posicao_camera() != anterior
        tecla(pygame.K_r)
        assert app.ambiente.posicao_camera() == inicial
        app.ambiente.girar(150, 0)
        quadro("deposito_3d_paredes")
        # Alternância repetida detecta vazamento de estado de luz/profundidade.
        for _ in range(6):
            tecla(pygame.K_ESCAPE)
            quadro()
            tecla(pygame.K_1)
            quadro()
            tecla(pygame.K_ESCAPE)
            tecla(pygame.K_2)
            quadro()
        # Exercita descarte de textos variáveis sem crescimento infinito.
        tecla(pygame.K_ESCAPE)
        tecla(pygame.K_1)
        for i in range(110):
            app.textos.escrever(f"Teste do cache: {i}", 40, 113)
            quadro()
        assert len(app.textos.cache) <= LIMITE_TEXTURAS
        app.evento(pygame.event.Event(pygame.QUIT))
        assert not app.rodando
        print("OK: renderização, controles simulados, transições e cache limitado.")
        print("Capturas:", pasta)
    finally:
        if app:
            app.textos.liberar()
        pygame.quit()


if __name__ == "__main__":
    verificar()
