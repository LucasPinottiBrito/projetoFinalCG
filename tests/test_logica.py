"""Testes sem janela, Pygame ou OpenGL: python -m unittest discover -s tests -v."""

from copy import deepcopy
from math import hypot
import unittest
from unittest.mock import patch

from jogo_2d import (Jogo, Retangulo, colidem, ESQUERDA, TOPO, DIREITA, BASE,
                     DT_MAXIMO, TEMPO_INVULNERAVEL, REAPARECIMENTOS,
                     COLETA, ENTREGA, META_ENTREGAS, PONTOS_POR_ENTREGA, mover_caixa)
from ambiente_3d import (Ambiente, CAIXAS, FACES, DISTANCIA_MINIMA, DISTANCIA_MAXIMA,
                         ELEVACAO_MINIMA, ELEVACAO_MAXIMA)


class TesteJogo(unittest.TestCase):
    def test_aabb(self):
        a = Retangulo(0, 0, 10, 10)
        for b, esperado in [(Retangulo(9, 9, 4, 4), True),
                             (Retangulo(2, 2, 2, 2), True),
                             (Retangulo(11, 0, 2, 2), False),
                             (Retangulo(0, 11, 2, 2), False),
                             (Retangulo(10, 0, 2, 2), False)]:
            with self.subTest(b=b):
                self.assertEqual(colidem(a, b), esperado)
                self.assertEqual(colidem(b, a), esperado)

    def test_limites_do_jogador(self):
        jogo = Jogo()
        for x, y, dx, dy, esperado in [
            (ESQUERDA, TOPO, -1, -1, (ESQUERDA, TOPO)),
            (DIREITA - 36, BASE - 36, 1, 1, (DIREITA - 36, BASE - 36))]:
            jogo.jogador.x, jogo.jogador.y = x, y
            jogo.atualizar(0.05, dx, dy)
            self.assertEqual((jogo.jogador.x, jogo.jogador.y), esperado)

    def test_diagonal_e_limite_de_dt(self):
        reto, diagonal, lento = Jogo(), Jogo(), Jogo()
        x, y = reto.jogador.x, reto.jogador.y
        reto.atualizar(DT_MAXIMO, 1, 0)
        diagonal.atualizar(DT_MAXIMO, 1, 1)
        lento.atualizar(10, 1, 0)
        self.assertAlmostEqual(reto.jogador.x - x,
                               hypot(diagonal.jogador.x - x, diagonal.jogador.y - y))
        self.assertEqual(reto.jogador, lento.jogador)
        self.assertEqual(reto.pontos, lento.pontos)

    def test_tres_caixas_movem_e_refletem_nas_extremidades(self):
        jogo = Jogo()
        self.assertEqual([c.eixo for c in jogo.caixas], ["x", "y", "x"])
        self.assertGreater(jogo.caixas[0].velocidade, 0)
        self.assertLess(jogo.caixas[2].velocidade, 0)
        antes = deepcopy(jogo.caixas)
        jogo.atualizar(0.05)
        for caixa, anterior in zip(jogo.caixas, antes):
            self.assertAlmostEqual(getattr(caixa.retangulo, caixa.eixo),
                                   getattr(anterior.retangulo, caixa.eixo) + anterior.velocidade * 0.05)
            for posicao, sentido in [(caixa.maximo - 1, 1), (caixa.minimo + 1, -1)]:
                setattr(caixa.retangulo, caixa.eixo, posicao)
                caixa.velocidade = abs(caixa.velocidade) * sentido
                mover_caixa(caixa, 0.05)
                self.assertLess(caixa.velocidade * sentido, 0)
                self.assertGreaterEqual(getattr(caixa.retangulo, caixa.eixo), caixa.minimo)
                self.assertLessEqual(getattr(caixa.retangulo, caixa.eixo), caixa.maximo)

    def test_trajetorias_inteiras_fora_das_areas_seguras(self):
        jogo = Jogo()
        for caixa in jogo.caixas:
            # O retângulo varrido cobre TODA a trajetória, não só uma amostra.
            varrido = deepcopy(caixa.retangulo)
            setattr(varrido, caixa.eixo, caixa.minimo)
            if caixa.eixo == "x":
                varrido.largura += caixa.maximo - caixa.minimo
            else:
                varrido.altura += caixa.maximo - caixa.minimo
            for area in (COLETA, ENTREGA, jogo.jogador):
                self.assertFalse(colidem(varrido, area))
            self.assertGreaterEqual(varrido.x, ESQUERDA)
            self.assertGreaterEqual(varrido.y, TOPO)
            self.assertLessEqual(varrido.x + varrido.largura, DIREITA)
            self.assertLessEqual(varrido.y + varrido.altura, BASE)

    def test_dano_das_tres_caixas_e_reaparecimento(self):
        for indice in range(3):
            jogo = Jogo()
            caixa = jogo.caixas[indice].retangulo
            jogo.jogador.x, jogo.jogador.y = caixa.x, caixa.y
            jogo.atualizar(0.01)
            self.assertEqual(jogo.vidas, 2)
            self.assertEqual(jogo.invulneravel, TEMPO_INVULNERAVEL)
            self.assertFalse(any(colidem(jogo.jogador, c.retangulo) for c in jogo.caixas))

    def test_invulnerabilidade_e_novo_dano_apos_expirar(self):
        jogo = Jogo()
        caixa = jogo.caixas[1].retangulo
        jogo.jogador.x, jogo.jogador.y = caixa.x, caixa.y
        jogo.atualizar(0.01)
        for _ in range(19):
            jogo.jogador.x, jogo.jogador.y = caixa.x, caixa.y
            jogo.atualizar(0.05)
        self.assertEqual(jogo.vidas, 2)
        jogo.atualizar(0.05)
        self.assertEqual(jogo.vidas, 1)

    def test_reaparecimento_escolhe_posicao_livre(self):
        jogo = Jogo()
        jogo.caixas[0].retangulo.x, jogo.caixas[0].retangulo.y = REAPARECIMENTOS[0]
        jogo.reaparecer()
        self.assertEqual((jogo.jogador.x, jogo.jogador.y), REAPARECIMENTOS[1])

    def test_pausa_congela_todo_o_estado(self):
        for area, carregando in ((COLETA, False), (ENTREGA, True)):
            jogo = Jogo()
            jogo.jogador.x, jogo.jogador.y = area.x, area.y
            jogo.carregando = carregando
            jogo.invulneravel = 0.7
            jogo.alternar_pausa()
            antes = deepcopy(vars(jogo))
            for _ in range(100):
                jogo.atualizar(1, 1, 1)
            self.assertEqual(vars(jogo), antes)
            jogo.alternar_pausa()
            jogo.atualizar(0.02)
            self.assertAlmostEqual(jogo.invulneravel, 0.68)
            self.assertEqual(jogo.carregando, not carregando)
            self.assertEqual(jogo.entregas, int(carregando))
            for caixa, anterior in zip(jogo.caixas, antes['caixas']):
                self.assertAlmostEqual(getattr(caixa.retangulo, caixa.eixo),
                                       getattr(anterior.retangulo, caixa.eixo) + anterior.velocidade * 0.02)

    def test_tempo_nao_da_pontos_e_movimento_independe_dos_quadros(self):
        resultados = []
        for fps in (30, 60, 144):
            jogo = Jogo()
            for _ in range(fps * 3):
                jogo.atualizar(1 / fps)
            self.assertEqual(jogo.pontos, 0)
            resultados.append([getattr(c.retangulo, c.eixo) for c in jogo.caixas])
        for resultado in resultados[1:]:
            for posicao, referencia in zip(resultado, resultados[0]):
                self.assertAlmostEqual(posicao, referencia)

    def test_coleta_uma_unica_encomenda(self):
        jogo = Jogo()
        jogo.jogador.x, jogo.jogador.y = COLETA.x, COLETA.y
        for _ in range(30):
            jogo.atualizar(0.05)
            self.assertTrue(jogo.carregando)
            self.assertEqual((jogo.entregas, jogo.pontos), (0, 0))
        jogo.reaparecer()
        jogo.atualizar(0.05)
        self.assertTrue(jogo.carregando)

    def test_entrega_unica_e_sem_encomenda_nao_pontua(self):
        jogo = Jogo()
        for numero in range(3):
            jogo.jogador.x, jogo.jogador.y = ENTREGA.x, ENTREGA.y
            for _ in range(30):
                jogo.atualizar(0.05)
            self.assertEqual((jogo.entregas, jogo.pontos), (numero, numero * PONTOS_POR_ENTREGA))
            self.assertFalse(jogo.carregando)
            # Voltar à coleta disponibiliza exatamente mais uma entrega.
            jogo.jogador.x, jogo.jogador.y = COLETA.x, COLETA.y
            jogo.atualizar(0.05)
            self.assertTrue(jogo.carregando)
            jogo.jogador.x, jogo.jogador.y = ENTREGA.x, ENTREGA.y
            jogo.atualizar(0.05)
            self.assertEqual(jogo.entregas, numero + 1)
            self.assertFalse(jogo.carregando)

    def test_colisao_no_transporte_preserva_entregas_e_devolve_encomenda(self):
        jogo = Jogo()
        jogo.entregas = 2
        jogo.carregando = True
        caixa = jogo.caixas[0].retangulo
        jogo.jogador.x, jogo.jogador.y = caixa.x, caixa.y
        jogo.atualizar(0.05)
        self.assertEqual((jogo.vidas, jogo.entregas, jogo.pontos), (2, 2, 200))
        self.assertFalse(jogo.carregando)
        jogo.jogador.x, jogo.jogador.y = COLETA.x, COLETA.y
        jogo.atualizar(0.05)
        self.assertTrue(jogo.carregando)

    def test_quadro_com_dano_nao_coleta_nem_entrega(self):
        for area in (COLETA, ENTREGA):
            jogo = Jogo()
            jogo.carregando = True
            jogo.entregas = 2
            caixa = jogo.caixas[0].retangulo
            jogo.jogador.x, jogo.jogador.y = caixa.x, caixa.y
            # Mesmo reaparecendo numa área de interação, o quadro termina no dano.
            with patch('jogo_2d.REAPARECIMENTOS', ((area.x, area.y),)):
                jogo.atualizar(0.05)
            self.assertEqual((jogo.vidas, jogo.entregas), (2, 2))
            self.assertFalse(jogo.carregando)

    def test_vitoria_congela_e_reinicio_restaura_tudo(self):
        jogo = Jogo()
        for numero in range(1, META_ENTREGAS + 1):
            jogo.jogador.x, jogo.jogador.y = COLETA.x, COLETA.y
            jogo.atualizar(0.05)
            jogo.jogador.x, jogo.jogador.y = ENTREGA.x, ENTREGA.y
            jogo.atualizar(0.05)
            self.assertEqual(jogo.pontos, numero * PONTOS_POR_ENTREGA)
            self.assertEqual(jogo.estado, "vitoria" if numero == META_ENTREGAS else "jogando")
        antes = deepcopy(vars(jogo))
        jogo.alternar_pausa()  # não pode reativar uma partida encerrada
        jogo.atualizar(10, 1, 1)
        self.assertEqual(vars(jogo), antes)
        jogo.reiniciar()
        self.assertEqual(vars(jogo), vars(Jogo()))

    def test_fim_de_jogo_e_reinicio(self):
        jogo = Jogo()
        for _ in range(3):
            jogo.invulneravel = 0
            caixa = jogo.caixas[1].retangulo
            jogo.jogador.x, jogo.jogador.y = caixa.x, caixa.y
            jogo.atualizar(0.05)
        self.assertEqual((jogo.vidas, jogo.estado), (0, "fim"))
        antes = deepcopy(vars(jogo))
        jogo.atualizar(1, 1, 1)
        self.assertEqual(vars(jogo), antes)
        jogo.caixas[0].velocidade *= -1
        jogo.reiniciar()
        self.assertEqual(vars(jogo), vars(Jogo()))


class TesteAmbiente(unittest.TestCase):
    def test_limites_camera_luz_e_restauracao(self):
        ambiente = Ambiente()
        ambiente.girar(800, -800)
        ambiente.aproximar(800)
        self.assertEqual((ambiente.elevacao, ambiente.distancia), (ELEVACAO_MINIMA, DISTANCIA_MINIMA))
        self.assertGreater(ambiente.posicao_camera()[1], 0)
        ambiente.girar(0, 800)
        ambiente.aproximar(-800)
        self.assertEqual((ambiente.elevacao, ambiente.distancia), (ELEVACAO_MAXIMA, DISTANCIA_MAXIMA))
        luz_inicial = ambiente.luz
        for _ in range(3):
            ambiente.alternar_luz()
        self.assertEqual(ambiente.luz, luz_inicial)
        ambiente.restaurar_camera()
        self.assertEqual(ambiente.posicao_camera(), Ambiente().posicao_camera())

    def test_cinco_caixas_separadas_e_normais_para_fora(self):
        self.assertEqual(len(CAIXAS), 5)
        bases = [Retangulo(p[0] - d[0] / 2, p[1] - d[2] / 2, d[0], d[2]) for p, d, _ in CAIXAS]
        for i, base in enumerate(bases):
            self.assertFalse(any(colidem(base, outra) for outra in bases[i + 1:]))
        for normal, vertices in FACES:
            u = [vertices[1][i] - vertices[0][i] for i in range(3)]
            v = [vertices[2][i] - vertices[0][i] for i in range(3)]
            produto = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0])
            self.assertGreater(sum(produto[i] * normal[i] for i in range(3)), 0)


if __name__ == "__main__":
    unittest.main()
