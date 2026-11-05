"""Parâmetros explícitos da partida; o modelo físico é igual em todos os níveis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Nivel:
    nome: str
    cores: int
    quantidade: int
    prazo: float | None
    intervalo: float


NIVEIS = (
    Nivel("Treino", 2, 6, None, 6),
    Nivel("Fácil", 2, 6, 180, 6),
    Nivel("Médio", 3, 12, 240, 5),
    Nivel("Difícil", 5, 20, 300, 4),
)

# Identidade da categoria não depende dos componentes RGB usados no desenho.
CORES = (
    ("A", "AZUL", (0.16, 0.52, 0.95)),
    ("B", "LARANJA", (1.0, 0.43, 0.12)),
    ("C", "VERDE", (0.29, 0.77, 0.43)),
    ("D", "VIOLETA", (0.66, 0.38, 0.93)),
    ("E", "AMARELO", (0.98, 0.80, 0.19)),
)
