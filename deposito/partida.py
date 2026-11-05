"""Regras de organização: contatos sustentam pilhas e a cor determina o destino."""

from deposito.cenario import criar_galpao
from deposito.esteira import Esteira
from deposito.fisica import MundoFisico, PASSO_FISICO
from deposito.jogador import Jogador


class Partida:
    def __init__(self, nivel):
        self.nivel = nivel
        self.laboratorio = False
        self.reiniciar()

    def reiniciar(self):
        corpos, self.areas = criar_galpao(self.nivel.cores)
        self.esteira = Esteira(self.nivel)
        self.jogador = Jogador()
        corpos += [self.esteira.faixa, *self.esteira.laterais, self.jogador.corpo]
        self.mundo = MundoFisico(corpos)
        self.caixas = []
        self.organizadas = set()
        self.estado = "jogando"
        self.tempo = 0.0
        self.acumulador = 0.0
        self.conclusao_por = 0.0
        self.depurar = False

    @property
    def restante(self):
        return None if self.nivel.prazo is None else max(0, self.nivel.prazo-self.tempo)

    def alternar_pausa(self):
        if self.estado in ("jogando", "pausado"):
            self.estado = "pausado" if self.estado == "jogando" else "jogando"
            self.acumulador = 0
            self.jogador.carregando_arremesso = False
            self.jogador.carga = 0

    def calcular_organizadas(self):
        candidatas = {caixa for caixa in self.caixas if caixa is not self.jogador.segurada
                      and caixa.estavel_por >= 0.75
                      and self.areas[caixa.categoria].contem_caixa(caixa)}
        apoios = {caixa: set() for caixa in candidatas}
        for contato in self.mundo.contatos:
            a, b = contato.a, contato.b
            if contato.normal.y > 0.7 and b in candidatas:
                apoios[b].add(a)
            elif contato.normal.y < -0.7 and a in candidatas:
                apoios[a].add(b)
        validas = set()
        # Crescer a partir do piso elimina ciclos e exige uma cadeia até o chão.
        for _ in range(len(candidatas)):
            novas = {caixa for caixa in candidatas-validas
                     if any(apoio.nome == "piso" or (apoio in validas and apoio.categoria == caixa.categoria)
                            for apoio in apoios[caixa])}
            if not novas:
                break
            validas.update(novas)
        return validas

    def atualizar_objetivo(self, dt):
        self.organizadas = self.calcular_organizadas()
        if self.laboratorio:
            return
        completo = self.esteira.emitidas == self.nivel.quantidade and len(self.organizadas) == self.nivel.quantidade
        self.conclusao_por = self.conclusao_por+dt if completo else 0
        if self.conclusao_por >= 2:
            self.estado = "vitoria"
        elif self.restante is not None and self.restante <= 0:
            self.estado = "derrota"

    def atualizar(self, dt, frente=0, lado=0):
        if self.estado != "jogando":
            return
        # Até 12 passos recuperam um quadro lento; o excesso não cobra o prazo.
        self.acumulador += max(0, min(dt, 0.1))
        while self.acumulador+1e-10 >= PASSO_FISICO and self.estado == "jogando":
            self.acumulador -= PASSO_FISICO
            self.tempo += PASSO_FISICO
            self.jogador.mover(PASSO_FISICO, frente, lado, self.mundo)
            self.esteira.atualizar(PASSO_FISICO, self.mundo, self.caixas)
            self.mundo.avancar(PASSO_FISICO,
                               lambda passo: self.jogador.atualizar_interacao(passo, self.mundo))
            self.atualizar_objetivo(PASSO_FISICO)
