"""Dados físicos das caixas. Dimensões em metros, massa em quilogramas."""

from dataclasses import dataclass, field
from itertools import product

from deposito.matematica import EIXOS, Quaternion, Vetor3


@dataclass(eq=False)
class CorpoRigido:
    posicao: Vetor3
    metade: Vetor3
    massa: float = 2.0
    categoria: int = -1
    nome: str = "caixa"
    orientacao: Quaternion = field(default_factory=Quaternion)
    velocidade: Vetor3 = field(default_factory=Vetor3)
    velocidade_angular: Vetor3 = field(default_factory=Vetor3)
    atrito: float = 0.65
    restituicao: float = 0.10
    superficie: Vetor3 = field(default_factory=Vetor3)
    estavel_por: float = 0.0
    dormindo: bool = False
    eixos: tuple = field(init=False)

    def __post_init__(self):
        if min(self.metade) <= 0 or self.massa < 0:
            raise ValueError("Dimensões positivas e massa não negativa são necessárias.")
        self.atualizar_eixos()

    @property
    def massa_inversa(self):
        return 1 / self.massa if self.massa else 0.0

    def atualizar_eixos(self):
        self.eixos = tuple(self.orientacao.girar_vetor(eixo) for eixo in EIXOS)

    def aplicar_inercia_inversa(self, vetor):
        if not self.massa:
            return Vetor3()
        x, y, z = self.metade
        # Para um bloco, Ixx = massa * (altura² + profundidade²) / 12.
        inversas = (3/(self.massa*(y*y+z*z)), 3/(self.massa*(x*x+z*z)),
                    3/(self.massa*(x*x+y*y)))
        resultado = Vetor3()
        for eixo, inversa in zip(self.eixos, inversas):
            resultado += eixo * (vetor.produto_escalar(eixo) * inversa)
        return resultado

    def raio_projetado(self, direcao):
        return sum(abs(eixo.produto_escalar(direcao))*metade
                   for eixo, metade in zip(self.eixos, self.metade))

    def local_para_mundo(self, local):
        return self.posicao + sum((eixo * valor for eixo, valor in zip(self.eixos, local)), Vetor3())

    def mundo_para_local(self, ponto):
        deslocamento = ponto - self.posicao
        return Vetor3(*(deslocamento.produto_escalar(eixo) for eixo in self.eixos))

    def vertices(self):
        return [self.local_para_mundo(Vetor3(*(s*h for s, h in zip(sinais, self.metade))))
                for sinais in product((-1, 1), repeat=3)]


@dataclass
class Contato:
    """A normal aponta de A para B; impulso positivo afasta B de A."""

    a: CorpoRigido
    b: CorpoRigido
    normal: Vetor3
    ponto: Vetor3
    penetracao: float
    impulso_normal: float = 0.0
    impulso_atrito: Vetor3 = field(default_factory=Vetor3)
    velocidade_restituicao: float = 0.0


def aplicar_impulso(corpo, impulso, ponto):
    """Aplica um impacto único; fora do centro ele também provoca rotação."""
    if not corpo.massa:
        return
    corpo.dormindo = False
    corpo.velocidade += impulso * corpo.massa_inversa
    torque = (ponto - corpo.posicao).produto_vetorial(impulso)
    corpo.velocidade_angular += corpo.aplicar_inercia_inversa(torque)
