"""Construção do galpão. O desenho e a física usam as mesmas dimensões."""

from dataclasses import dataclass

from deposito.corpos import CorpoRigido
from deposito.matematica import Vetor3


@dataclass(frozen=True)
class AreaDeCor:
    categoria: int
    centro: Vetor3
    metade_x: float = 1.45
    metade_z: float = 1.65

    def contem_caixa(self, caixa):
        return all(abs(p.x-self.centro.x) <= self.metade_x+0.005
                   and abs(p.z-self.centro.z) <= self.metade_z+0.005 for p in caixa.vertices())


def criar_galpao(quantidade_cores):
    corpos = [
        CorpoRigido(Vetor3(0, -0.3, 0), Vetor3(11, 0.3, 10), 0, nome="piso"),
        CorpoRigido(Vetor3(0, 3, -10), Vetor3(11, 3, 0.25), 0, nome="parede"),
        CorpoRigido(Vetor3(0, 3, 10), Vetor3(11, 3, 0.25), 0, nome="parede"),
        CorpoRigido(Vetor3(-11, 3, 0), Vetor3(0.25, 3, 10), 0, nome="parede"),
        CorpoRigido(Vetor3(11, 3, 0), Vetor3(0.25, 3, 10), 0, nome="parede"),
        CorpoRigido(Vetor3(0, 6.15, 0), Vetor3(11, 0.15, 10), 0, nome="teto"),
    ]
    areas = [AreaDeCor(i, Vetor3((i-(quantidade_cores-1)/2)*3.8, 0, -7.6))
             for i in range(quantidade_cores)]
    for area in areas:
        corpos.append(CorpoRigido(Vetor3(area.centro.x, 1.9, -9.66), Vetor3(1.5, 1.9, 0.08),
                                 0, area.categoria, "porta"))
    return corpos, areas
