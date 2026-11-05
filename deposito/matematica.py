"""Matemática 3D independente da janela. Ângulos internos usam radianos."""

from dataclasses import dataclass
from math import cos, sin, sqrt


@dataclass(frozen=True, slots=True)
class Vetor3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, outro):
        return Vetor3(self.x + outro.x, self.y + outro.y, self.z + outro.z)

    def __sub__(self, outro):
        return Vetor3(self.x - outro.x, self.y - outro.y, self.z - outro.z)

    def __neg__(self):
        return self * -1

    def __mul__(self, escalar):
        return Vetor3(self.x * escalar, self.y * escalar, self.z * escalar)

    __rmul__ = __mul__

    def __truediv__(self, escalar):
        return self * (1 / escalar)

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def produto_escalar(self, outro):
        return self.x * outro.x + self.y * outro.y + self.z * outro.z

    def produto_vetorial(self, outro):
        return Vetor3(self.y * outro.z - self.z * outro.y,
                      self.z * outro.x - self.x * outro.z,
                      self.x * outro.y - self.y * outro.x)

    def comprimento(self):
        return sqrt(self.produto_escalar(self))

    def normalizado(self):
        tamanho = self.comprimento()
        return self / tamanho if tamanho > 1e-10 else Vetor3()

    def limitado(self, maximo):
        tamanho = self.comprimento()
        return self * (maximo / tamanho) if tamanho > maximo else self


EIXOS = (Vetor3(1, 0, 0), Vetor3(0, 1, 0), Vetor3(0, 0, 1))


@dataclass(frozen=True, slots=True)
class Quaternion:
    """Orientação unitária; evita singularidades durante giros das caixas."""

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __mul__(self, outro):
        a, b, c, d = self.w, self.x, self.y, self.z
        e, f, g, h = outro.w, outro.x, outro.y, outro.z
        return Quaternion(a*e-b*f-c*g-d*h, a*f+b*e+c*h-d*g,
                          a*g-b*h+c*e+d*f, a*h+b*g-c*f+d*e)

    def normalizado(self):
        tamanho = sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)
        return Quaternion(self.w/tamanho, self.x/tamanho, self.y/tamanho, self.z/tamanho)

    def girar_vetor(self, vetor):
        parte = Vetor3(self.x, self.y, self.z)
        dobro = parte.produto_vetorial(vetor) * 2
        return vetor + dobro * self.w + parte.produto_vetorial(dobro)

    @classmethod
    def de_eixo_angulo(cls, eixo, angulo):
        vetor = eixo.normalizado() * sin(angulo / 2)
        return cls(cos(angulo / 2), *vetor)


def integrar_orientacao(orientacao, velocidade_angular, dt):
    """Aplica um giro no mundo, mantendo o quaternion normalizado."""
    angulo = velocidade_angular.comprimento() * dt
    if angulo < 1e-10:
        return orientacao
    giro = Quaternion.de_eixo_angulo(velocidade_angular, angulo)
    return (giro * orientacao).normalizado()
