"""Traduz eventos do Pygame em intenções e coordena as telas do simulador."""

import sys

import pygame
from OpenGL import GL as gl
from OpenGL.error import GLError

from desenho import Textos
from deposito.corpos import CorpoRigido
from deposito.matematica import Quaternion, Vetor3
from deposito.niveis import NIVEIS, Nivel
from deposito.partida import Partida
from deposito.renderizacao import ALTURA, LARGURA, desenhar, liberar_recursos


def criar_janela():
    pygame.display.init()
    pygame.font.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    pygame.display.set_mode((LARGURA, ALTURA), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Depósito — Simulador 3D")
    gl.glViewport(0, 0, LARGURA, ALTURA)


class Aplicacao:
    def __init__(self):
        self.textos = Textos()
        self.partida = Partida(NIVEIS[3])
        self.menu = True
        self.rodando = True
        self.fps = 0
        self.ignorar_dt = True
        self.sincronizar_mouse()

    def sincronizar_mouse(self):
        capturar = not self.menu and self.partida.estado == "jogando"
        pygame.event.set_grab(capturar)
        pygame.mouse.set_visible(not capturar)
        pygame.mouse.get_rel()

    def iniciar(self, indice):
        self.partida = Partida(NIVEIS[indice])
        self.menu = False
        self.ignorar_dt = True
        self.sincronizar_mouse()

    def abrir_laboratorio(self):
        self.partida = Partida(Nivel("Laboratório", 2, 0, None, 6))
        self.partida.laboratorio = True
        self.partida.depurar = True
        for i in range(3):
            caixa = CorpoRigido(Vetor3(0, 0.42+i*0.85, 0), Vetor3(0.42, 0.42, 0.42), categoria=0)
            self.partida.caixas.append(caixa)
        self.partida.caixas.append(CorpoRigido(Vetor3(2, 2.6, -1), Vetor3(0.42, 0.42, 0.42), categoria=1,
                                              orientacao=Quaternion.de_eixo_angulo(Vetor3(1, 0, 1), 0.4)))
        self.partida.mundo.corpos.extend(self.partida.caixas)
        self.partida.jogador.corpo.posicao = Vetor3(2.4, 0.85, 3)
        self.partida.jogador.azimute = -0.55
        self.menu = False
        self.ignorar_dt = True
        self.sincronizar_mouse()

    def repetir(self):
        if self.partida.laboratorio:
            self.abrir_laboratorio()
        else:
            self.partida.reiniciar()
        self.ignorar_dt = True
        self.sincronizar_mouse()

    def tecla(self, tecla):
        if self.menu:
            if tecla in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                self.iniciar(tecla-pygame.K_1)
            elif tecla == pygame.K_5:
                self.abrir_laboratorio()
            elif tecla == pygame.K_ESCAPE:
                self.rodando = False
            return
        partida = self.partida
        if tecla == pygame.K_ESCAPE:
            partida.alternar_pausa()
            self.ignorar_dt = True
        elif tecla == pygame.K_F3:
            partida.depurar = not partida.depurar
        elif partida.estado == "jogando":
            if tecla == pygame.K_e:
                partida.jogador.interagir(partida.mundo)
        elif tecla == pygame.K_r:
            self.repetir()
        elif tecla == pygame.K_m:
            self.menu = True
        elif tecla == pygame.K_q:
            self.rodando = False
        elif tecla == pygame.K_RETURN:
            if partida.estado == "pausado":
                partida.alternar_pausa()
                self.ignorar_dt = True
            elif partida.estado == "vitoria":
                indice = NIVEIS.index(partida.nivel)
                self.iniciar(min(3, indice+1))
            else:
                self.repetir()
        self.sincronizar_mouse()

    def evento(self, evento):
        if evento.type == pygame.QUIT:
            self.rodando = False
        elif evento.type == pygame.KEYDOWN:
            self.tecla(evento.key)
        elif evento.type == pygame.WINDOWFOCUSLOST:
            if not self.menu and self.partida.estado == "jogando":
                self.partida.alternar_pausa()
                self.ignorar_dt = True
                self.sincronizar_mouse()
        elif not self.menu and self.partida.estado == "jogando":
            jogador = self.partida.jogador
            if evento.type == pygame.MOUSEMOTION:
                if evento.buttons[2] and jogador.segurada:
                    jogador.girar_caixa(*evento.rel)
                else:
                    jogador.olhar(*evento.rel)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if jogador.segurada:
                    jogador.carregando_arremesso = True
                    jogador.carga = 0
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                jogador.arremessar_caixa()

    def atualizar(self, dt, teclas):
        if self.ignorar_dt:
            self.ignorar_dt = False
            return
        if self.menu:
            return
        estado_anterior = self.partida.estado
        frente = int(teclas[pygame.K_w])-int(teclas[pygame.K_s])
        lado = int(teclas[pygame.K_d])-int(teclas[pygame.K_a])
        self.partida.atualizar(dt, frente, lado)
        if self.partida.estado != estado_anterior:
            self.sincronizar_mouse()

    def desenhar(self):
        desenhar(self.partida, self.textos, self.menu, self.fps)


def main():
    app = None
    try:
        criar_janela()
        app = Aplicacao()
        relogio = pygame.time.Clock()
        while app.rodando:
            dt = relogio.tick(60)/1000
            for evento in pygame.event.get():
                app.evento(evento)
            if not app.rodando:
                break
            app.atualizar(dt, pygame.key.get_pressed())
            app.fps = relogio.get_fps()
            app.desenhar()
            pygame.display.flip()
        return 0
    except (pygame.error, GLError) as erro:
        print(f"Falha ao abrir ou desenhar o simulador OpenGL 2.1: {erro}", file=sys.stderr)
        return 1
    finally:
        if app is not None:
            app.textos.liberar()
            liberar_recursos()
        if pygame.display.get_init():
            pygame.event.set_grab(False)
        pygame.quit()
