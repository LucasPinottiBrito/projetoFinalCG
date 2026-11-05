"""Primeira pessoa e manipulação física, sem dependências de entrada ou desenho."""

from math import cos, sin

from deposito.colisoes import (aabbs_sobrepostos, calcular_aabb, detectar_colisao_caixas,
                               intersectar_raio_caixa)
from deposito.corpos import CorpoRigido, aplicar_impulso
from deposito.matematica import Quaternion, Vetor3


class Jogador:
    def __init__(self):
        self.corpo = CorpoRigido(Vetor3(2.8, 0.85, 7.6), Vetor3(0.28, 0.85, 0.28), 0, nome="jogador")
        self.azimute = -1.0
        self.elevacao = -0.18
        self.segurada = None
        self.orientacao_alvo = Quaternion()
        self.carga = 0.0
        self.carregando_arremesso = False
        self.ignoradas = set()

    @property
    def olhos(self):
        return self.corpo.posicao+Vetor3(0, 0.73, 0)

    @property
    def direcao(self):
        return Vetor3(sin(self.azimute)*cos(self.elevacao), sin(self.elevacao),
                      -cos(self.azimute)*cos(self.elevacao))

    def olhar(self, dx, dy):
        self.azimute += dx*0.0025
        self.elevacao = max(-1.35, min(1.35, self.elevacao-dy*0.0025))

    def girar_caixa(self, dx, dy):
        if self.segurada:
            giro = Quaternion.de_eixo_angulo(Vetor3(0, 1, 0), dx*0.008)
            lateral = Vetor3(cos(self.azimute), 0, sin(self.azimute))
            giro = Quaternion.de_eixo_angulo(lateral, dy*0.008)*giro
            self.orientacao_alvo = (giro*self.orientacao_alvo).normalizado()

    def selecionar_caixa(self, mundo):
        alvo, distancia = None, 3.3
        for corpo in mundo.corpos:
            if corpo is self.corpo:
                continue
            alcance = intersectar_raio_caixa(self.olhos, self.direcao, corpo, distancia)
            if alcance is not None and alcance < distancia:
                distancia, alvo = alcance, corpo
        return alvo if alvo is not None and alvo.massa else None

    def interagir(self, mundo):
        if self.segurada:
            self.soltar_caixa()
            return
        caixa = self.selecionar_caixa(mundo)
        if caixa:
            self.segurada = caixa
            self.orientacao_alvo = caixa.orientacao
            caixa.estavel_por = 0
            caixa.dormindo = False
            self.ignoradas.add(caixa)
            mundo.pares_ignorados.add(frozenset((caixa, self.corpo)))

    def soltar_caixa(self):
        self.segurada = None
        self.carga = 0
        self.carregando_arremesso = False

    def arremessar_caixa(self):
        if not self.segurada or not self.carregando_arremesso:
            return
        caixa = self.segurada
        caixa.dormindo = False
        direcao = (self.direcao+Vetor3(0, 0.12, 0)).normalizado()
        impulso = direcao*(5+19*min(1, self.carga/1.2))
        # Pequeno braço de alavanca torna o giro visível sem aleatoriedade.
        aplicar_impulso(caixa, impulso, caixa.posicao+Vetor3(0, 0.07, 0))
        caixa.estavel_por = 0
        self.soltar_caixa()

    def atualizar_interacao(self, dt, mundo):
        for caixa in tuple(self.ignoradas):
            if caixa is not self.segurada and not detectar_colisao_caixas(self.corpo, caixa):
                mundo.pares_ignorados.discard(frozenset((caixa, self.corpo)))
                self.ignoradas.remove(caixa)
        if not self.segurada:
            return
        caixa = self.segurada
        lateral = Vetor3(cos(self.azimute), 0, sin(self.azimute))
        alvo = self.olhos+self.direcao*1.9+lateral*0.30+Vetor3(0, -0.12, 0)
        deslocamento = alvo-caixa.posicao
        if deslocamento.comprimento() > 3.5:
            self.soltar_caixa()
            return
        # Mola amortecida: a caixa mantém contatos ao tentar acompanhar a mão.
        aceleracao = (deslocamento*95-caixa.velocidade*18+Vetor3(0, 9.81, 0)).limitado(85)
        caixa.velocidade += aceleracao*dt
        conjugado = Quaternion(caixa.orientacao.w, -caixa.orientacao.x,
                               -caixa.orientacao.y, -caixa.orientacao.z)
        erro = self.orientacao_alvo*conjugado
        sinal = 1 if erro.w >= 0 else -1
        torque = Vetor3(erro.x, erro.y, erro.z)*(sinal*60)-caixa.velocidade_angular*10
        caixa.velocidade_angular += torque.limitado(45)*dt
        caixa.estavel_por = 0
        if self.carregando_arremesso:
            self.carga = min(1.2, self.carga+dt)

    def mover(self, dt, frente, lado, mundo):
        direcao = Vetor3(sin(self.azimute), 0, -cos(self.azimute))*frente
        direcao += Vetor3(cos(self.azimute), 0, sin(self.azimute))*lado
        deslocamento = direcao.limitado(1)*(3.8*dt)
        anterior = self.corpo.posicao
        # Deslizar por eixo permite caminhar junto a paredes sem prender o controle.
        for movimento in (Vetor3(deslocamento.x, 0, 0), Vetor3(0, 0, deslocamento.z)):
            self.corpo.posicao += movimento
            for obstaculo in mundo.corpos:
                if obstaculo is self.corpo or obstaculo in self.ignoradas:
                    continue
                if not aabbs_sobrepostos(calcular_aabb(self.corpo), calcular_aabb(obstaculo)):
                    continue
                contatos = detectar_colisao_caixas(self.corpo, obstaculo)
                if not contatos:
                    continue
                contato = max(contatos, key=lambda c: c.penetracao)
                if contato.penetracao > 0.001 and abs(contato.normal.y) < 0.7:
                    self.corpo.posicao -= contato.normal*(contato.penetracao+0.001)
        self.corpo.velocidade = (self.corpo.posicao-anterior)/dt if dt else Vetor3()
