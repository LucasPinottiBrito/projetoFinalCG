"""Emissão finita; o transporte acontece pelo atrito com a faixa móvel."""

from deposito.colisoes import aabbs_sobrepostos, calcular_aabb
from deposito.corpos import CorpoRigido
from deposito.matematica import Vetor3


class Esteira:
    def __init__(self, nivel):
        self.nivel = nivel
        self.emitidas = 0
        self.espera = 0.0
        self.bloqueada = False
        self.faixa = CorpoRigido(Vetor3(0, 0.8, 5.8), Vetor3(0.85, 0.18, 2.7), 0,
                                 nome="esteira", superficie=Vetor3(0, 0, -1.05), atrito=0.9)
        self.laterais = [CorpoRigido(Vetor3(x, 1.12, 5.8), Vetor3(0.08, 0.20, 2.7),
                                     0, nome="lateral") for x in (-0.95, 0.95)]

    def atualizar(self, dt, mundo, caixas):
        if self.emitidas >= self.nivel.quantidade:
            self.bloqueada = False
            return
        self.espera = max(0, self.espera-dt)
        if self.espera > 0:
            return
        candidata = CorpoRigido(Vetor3(0, 1.46, 7.9), Vetor3(0.42, 0.42, 0.42),
                                categoria=self.emitidas % self.nivel.cores,
                                nome=f"caixa {self.emitidas+1}")
        limites = calcular_aabb(candidata)
        self.bloqueada = any(aabbs_sobrepostos(limites, calcular_aabb(caixa), 0.1) for caixa in caixas)
        if self.bloqueada:
            return
        caixas.append(candidata)
        mundo.corpos.append(candidata)
        self.emitidas += 1
        self.espera = self.nivel.intervalo
