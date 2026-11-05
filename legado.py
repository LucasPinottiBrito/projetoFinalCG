"""Ponto de entrada: uma janela, menu principal e duas cenas independentes."""

import sys

import pygame
from OpenGL import GL as gl
from OpenGL.error import GLError

import ambiente_3d
import jogo_2d
from desenho import Textos, menu_principal


def criar_janela():
    # Inicializamos apenas vídeo e fontes: este projeto não usa áudio.
    pygame.display.init()
    pygame.font.init()
    # OpenGL 2.1 usa o pipeline fixo, inclusive no contexto legado do macOS.
    # Não pedir perfil Core: glBegin, matrizes e iluminação precisam do legado.
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
    # O buffer de profundidade resolve o que fica na frente no 3D.
    # Dois buffers permitem desenhar um quadro completo antes de exibi-lo.
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    pygame.display.set_mode((jogo_2d.LARGURA, jogo_2d.ALTURA), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Depósito: Desafio das Caixas")
    # O viewport ocupa a janela toda; a cor de limpeza será o fundo dos quadros.
    gl.glViewport(0, 0, jogo_2d.LARGURA, jogo_2d.ALTURA)
    gl.glClearColor(0.045, 0.065, 0.10, 1)
    print("OpenGL:", gl.glGetString(gl.GL_VERSION).decode())
    print("Renderizador:", gl.glGetString(gl.GL_RENDERER).decode())


class Aplicacao:
    # Coordena as telas. As regras do jogo e os dados da câmera ficam em seus
    # próprios módulos; esta classe traduz os eventos do Pygame em ações.
    def __init__(self):
        # 'tela' escolhe menu/2D/3D; jogo.estado controla pausa/vitória/derrota.
        self.tela = "menu"
        self.rodando = True
        self.jogo = jogo_2d.Jogo()
        self.ambiente = ambiente_3d.Ambiente()
        self.textos = Textos()
        self.ignorar_dt = False

    def evento(self, evento):
        # Eventos são ações pontuais: fechar, apertar uma tecla, arrastar ou rolar.
        # O movimento contínuo das teclas mantidas pressionadas fica em atualizar.
        if evento.type == pygame.QUIT:
            self.rodando = False
        elif evento.type == pygame.WINDOWFOCUSLOST:
            # Evita perder vidas enquanto o usuário está em outra janela.
            if self.tela == "2d" and self.jogo.estado == "jogando":
                self.jogo.alternar_pausa()
                self.ignorar_dt = True
        elif evento.type == pygame.KEYDOWN:
            self.tecla(evento.key)
        elif self.tela == "3d":
            # rel contém o deslocamento do mouse desde o último evento.
            # Só giramos com o botão esquerdo pressionado; a rodinha muda o zoom.
            if evento.type == pygame.MOUSEMOTION and evento.buttons[0]:
                self.ambiente.girar(-evento.rel[0] * ambiente_3d.SENSIBILIDADE_MOUSE,
                                    evento.rel[1] * ambiente_3d.SENSIBILIDADE_MOUSE)
            elif evento.type == pygame.MOUSEWHEEL:
                self.ambiente.aproximar(evento.y)

    def tecla(self, tecla):
        # Esc tem prioridade em todas as telas. Ao entrar num modo pelo menu,
        # criamos uma partida ou uma configuração de câmera inicial.
        if tecla == pygame.K_ESCAPE:
            if self.tela == "menu":
                self.rodando = False
            else:
                self.tela = "menu"
            self.ignorar_dt = True
        elif self.tela == "menu":
            if tecla in (pygame.K_1, pygame.K_KP1):
                self.jogo.reiniciar()
                self.tela = "2d"
                self.ignorar_dt = True
            elif tecla in (pygame.K_2, pygame.K_KP2):
                self.ambiente = ambiente_3d.Ambiente()
                self.tela = "3d"
                self.ignorar_dt = True
        elif self.tela == "2d":
            self.tecla_jogo(tecla)
        elif self.tela == "3d":
            if tecla == pygame.K_r:
                self.ambiente.restaurar_camera()
            elif tecla == pygame.K_l:
                self.ambiente.alternar_luz()

    def tecla_jogo(self, tecla):
        # A mesma tecla pode ter funções diferentes conforme o estado.
        # Reiniciar e sair por Q só ficam disponíveis na pausa ou após o resultado.
        estado = self.jogo.estado
        if estado == "jogando" and tecla == pygame.K_p:
            self.jogo.alternar_pausa()
        elif estado == "pausado" and tecla in (pygame.K_p, pygame.K_RETURN):
            self.jogo.alternar_pausa()
        elif estado in ("pausado", "fim", "vitoria"):
            if tecla == pygame.K_r or (estado in ("fim", "vitoria") and tecla == pygame.K_RETURN):
                self.jogo.reiniciar()
            elif tecla == pygame.K_q:
                self.rodando = False
        if estado != self.jogo.estado or tecla == pygame.K_r:
            self.ignorar_dt = True

    def atualizar(self, dt, teclas):
        # Mudanças de tela/pausa descartam o intervalo anterior à transição.
        if self.ignorar_dt:
            self.ignorar_dt = False
            return
        dt = max(0.0, min(dt, jogo_2d.DT_MAXIMO))
        if self.tela == "2d":
            # Subtrair os sentidos produz -1, 0 ou +1 em cada eixo.
            # Teclas opostas se anulam; apertar seta e WASD juntos não acelera.
            horizontal = int(teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) - int(
                teclas[pygame.K_LEFT] or teclas[pygame.K_a])
            vertical = int(teclas[pygame.K_DOWN] or teclas[pygame.K_s]) - int(
                teclas[pygame.K_UP] or teclas[pygame.K_w])
            self.jogo.atualizar(dt, horizontal, vertical)
        elif self.tela == "3d":
            # Ângulos e distância variam por segundo, independentemente do FPS.
            self.ambiente.girar((teclas[pygame.K_RIGHT] - teclas[pygame.K_LEFT])
                                * ambiente_3d.VELOCIDADE_ROTACAO * dt,
                                (teclas[pygame.K_UP] - teclas[pygame.K_DOWN])
                                * ambiente_3d.VELOCIDADE_ROTACAO * dt)
            aproximar = any(teclas[t] for t in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS))
            afastar = teclas[pygame.K_MINUS] or teclas[pygame.K_KP_MINUS]
            self.ambiente.aproximar((int(aproximar) - int(afastar)) * ambiente_3d.VELOCIDADE_ZOOM * dt)

    def desenhar(self):
        # Limpamos tanto as cores quanto as profundidades do quadro anterior.
        # Cada modo prepara sua projeção e os estados OpenGL antes de desenhar.
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        if self.tela == "menu":
            menu_principal(self.textos)
        elif self.tela == "2d":
            jogo_2d.desenhar(self.jogo, self.textos)
        elif self.tela == "3d":
            ambiente_3d.desenhar(self.ambiente, self.textos)


def main():
    app = None
    try:
        criar_janela()
        app = Aplicacao()
        relogio = pygame.time.Clock()
        # Ciclo da aplicação: ler entradas -> atualizar dados -> desenhar -> exibir.
        # tick limita a 60 FPS; a divisão por 1000 converte milissegundos em segundos.
        while app.rodando:
            # tick também é chamado na pausa: nunca acumulamos o tempo do menu.
            dt = relogio.tick(60) / 1000.0
            for evento in pygame.event.get():
                app.evento(evento)
            if not app.rodando:
                break
            app.atualizar(dt, pygame.key.get_pressed())
            app.desenhar()
            pygame.display.flip()  # troca o buffer pronto pelo que está visível
        return 0
    except (pygame.error, GLError) as erro:
        print(f"Não foi possível executar a janela OpenGL: {erro}", file=sys.stderr)
        print("É necessário um ambiente gráfico com OpenGL 2.1 compatível. Consulte o README.", file=sys.stderr)
        return 1
    finally:
        # Excluir texturas enquanto o contexto ainda existe.
        if app is not None:
            app.textos.liberar()
        pygame.quit()


if __name__ == "__main__":
    # Importar este módulo nos testes não inicia o loop nem abre a janela.
    sys.exit(main())
