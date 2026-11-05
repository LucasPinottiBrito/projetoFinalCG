"""Integração gráfica: eventos, OpenGL real, capturas e desempenho observado.

Execute da raiz: .venv/Scripts/python.exe tests/verificar_simulador.py
"""

from collections import defaultdict
from pathlib import Path
import json
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from OpenGL import GL as gl

from deposito.aplicacao import Aplicacao, criar_janela
from deposito.corpos import CorpoRigido
from deposito.matematica import Vetor3
from deposito.niveis import NIVEIS, Nivel
from deposito.partida import Partida
from deposito.renderizacao import liberar_recursos


def verificar():
    app = None
    pasta = Path("capturas/simulador")
    pasta.mkdir(parents=True, exist_ok=True)
    try:
        criar_janela()
        app = Aplicacao()
        def quadro(nome):
            pygame.event.pump()
            app.desenhar()
            gl.glFinish()
            assert gl.glGetError() == gl.GL_NO_ERROR
            pixels = gl.glReadPixels(0, 0, 960, 720, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
            imagem = pygame.image.fromstring(bytes(pixels), (960, 720), "RGBA", True)
            pygame.image.save(imagem, str(pasta / (nome+".png")))
            pygame.display.flip()

        def tecla(codigo):
            app.evento(pygame.event.Event(pygame.KEYDOWN, key=codigo))

        quadro("menu")
        tecla(pygame.K_1)
        teclas = defaultdict(int)
        app.atualizar(1/60, teclas)
        for _ in range(240):
            app.atualizar(1/120, teclas)
        assert app.partida.esteira.emitidas == 1
        quadro("recebimento")
        jogador = app.partida.jogador
        # Cenário controlado exercita os eventos reais sem depender de mouse físico.
        caixa = CorpoRigido(jogador.olhos+jogador.direcao*2, Vetor3(.42, .42, .42), categoria=0)
        app.partida.caixas.append(caixa)
        app.partida.mundo.corpos.append(caixa)
        tecla(pygame.K_e)
        assert jogador.segurada is caixa
        for _ in range(60):
            app.atualizar(1/120, teclas)
        quadro("segurando")
        app.evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))
        for _ in range(60):
            app.atualizar(1/120, teclas)
        quadro("arremesso")
        app.evento(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
        assert jogador.segurada is None and caixa.velocidade.comprimento() > 2
        tecla(pygame.K_ESCAPE)
        assert app.partida.estado == "pausado"
        tempo = app.partida.tempo
        app.atualizar(0.1, teclas)
        assert app.partida.tempo == tempo
        quadro("pausa")
        tecla(pygame.K_RETURN)
        assert app.partida.estado == "jogando"
        app.evento(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        assert app.partida.estado == "pausado"
        tecla(pygame.K_r)
        assert not app.partida.caixas and app.partida.tempo == 0
        tecla(pygame.K_ESCAPE)
        tecla(pygame.K_m)
        assert app.menu
        tecla(pygame.K_5)
        assert app.partida.laboratorio
        for _ in range(300):
            app.partida.atualizar(1/120)
        quadro("laboratorio")
        app.iniciar(3)
        # Vinte caixas separadas testam o orçamento máximo sem obstruir a entrada.
        partida = app.partida
        partida.esteira.emitidas = NIVEIS[3].quantidade
        for i in range(20):
            caixa = CorpoRigido(Vetor3(-7+(i%5)*3.4, .42, -6+(i//5)*2.4),
                                Vetor3(.42, .42, .42), categoria=i%5)
            partida.caixas.append(caixa)
            partida.mundo.corpos.append(caixa)
        inicio = perf_counter()
        for _ in range(240):
            partida.atualizar(1/120)
        aquecimento = perf_counter()-inicio
        inicio = perf_counter()
        for _ in range(60):
            partida.atualizar(1/60)
            app.desenhar()
            pygame.display.flip()
        custo = (perf_counter()-inicio)/60
        quadro("cinco_cores")
        # Um lote completo em duas pilhas passa pela física e pela regra de vitória.
        app.partida = Partida(NIVEIS[1])
        partida_completa = app.partida
        partida_completa.esteira.emitidas = 6
        for i in range(6):
            categoria, altura = i % 2, i // 2
            area = partida_completa.areas[categoria]
            caixa = CorpoRigido(Vetor3(area.centro.x, .42+altura*.85, area.centro.z),
                                Vetor3(.42, .42, .42), categoria=categoria)
            partida_completa.caixas.append(caixa)
            partida_completa.mundo.corpos.append(caixa)
        for _ in range(600):
            partida_completa.atualizar(1/120)
        assert partida_completa.estado == "vitoria"
        quadro("vitoria")
        tecla(pygame.K_RETURN)
        assert app.partida.nivel == NIVEIS[2]
        app.partida = Partida(Nivel("Prazo de teste", 2, 6, .05, 1))
        app.partida.atualizar(.1)
        assert app.partida.estado == "derrota"
        quadro("derrota")
        resultado = {"OpenGL": gl.glGetString(gl.GL_VERSION).decode(),
                     "renderizador": gl.glGetString(gl.GL_RENDERER).decode(),
                     "aquecimento_20_caixas_s": round(aquecimento, 3),
                     "quadro_20_caixas_ms": round(custo*1000, 2),
                     "corpos_em_repouso": sum(c.dormindo for c in partida.caixas),
                     "capturas": str(pasta)}
        (pasta/"verificacao.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
        app.evento(pygame.event.Event(pygame.QUIT))
        assert not app.rodando
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    finally:
        if app:
            app.textos.liberar()
            liberar_recursos()
        if pygame.display.get_init():
            pygame.event.set_grab(False)
        pygame.quit()


if __name__ == "__main__":
    verificar()
