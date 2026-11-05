"""Provas físicas e regras do simulador, executáveis sem janela ou dependências."""

from math import pi
import unittest

from deposito.colisoes import detectar_colisao_caixas, intersectar_raio_caixa
from deposito.corpos import CorpoRigido, aplicar_impulso
from deposito.fisica import MundoFisico, PASSO_FISICO
from deposito.matematica import Quaternion, Vetor3
from deposito.niveis import NIVEIS, Nivel
from deposito.partida import Partida


def criar_caixa(x=0, y=0.42, z=0, categoria=0):
    return CorpoRigido(Vetor3(x, y, z), Vetor3(0.42, 0.42, 0.42), categoria=categoria)


def criar_piso():
    return CorpoRigido(Vetor3(0, -0.3, 0), Vetor3(12, 0.3, 12), 0, nome="piso")


def simular(mundo, segundos):
    for _ in range(round(segundos/PASSO_FISICO)):
        mundo.avancar(PASSO_FISICO)


class TesteMatematicaEContatos(unittest.TestCase):
    def test_rotacao_preserva_comprimento_e_ortogonalidade(self):
        caixa = criar_caixa()
        caixa.orientacao = Quaternion.de_eixo_angulo(Vetor3(1, 2, 3), 0.8)
        caixa.atualizar_eixos()
        for eixo in caixa.eixos:
            self.assertAlmostEqual(eixo.comprimento(), 1)
        self.assertAlmostEqual(caixa.eixos[0].produto_escalar(caixa.eixos[1]), 0)

    def test_separacao_borda_face_e_normal(self):
        a, b = criar_caixa(), criar_caixa(x=2)
        self.assertFalse(detectar_colisao_caixas(a, b))
        b.posicao = Vetor3(0.84, 0.42, 0)
        contatos = detectar_colisao_caixas(a, b)
        self.assertEqual(len(contatos), 4)
        self.assertTrue(all(c.normal.x > 0.99 for c in contatos))
        self.assertTrue(all(c.penetracao < 1e-8 for c in contatos))

    def test_caixas_rotacionadas_e_arestas(self):
        a, b = criar_caixa(), criar_caixa(x=0.6, y=0.8, z=0.3)
        b.orientacao = Quaternion.de_eixo_angulo(Vetor3(1, 1, 0.4), pi/4)
        b.atualizar_eixos()
        contatos = detectar_colisao_caixas(a, b)
        self.assertTrue(contatos)
        self.assertTrue(all(abs(c.normal.comprimento()-1) < 1e-7 for c in contatos))
        b.posicao = Vetor3(3, 3, 3)
        self.assertFalse(detectar_colisao_caixas(a, b))

    def test_raio_e_obstrucao(self):
        partida = Partida(NIVEIS[0])
        jogador = partida.jogador
        caixa = criar_caixa()
        caixa.posicao = jogador.olhos+jogador.direcao*2
        partida.mundo.corpos.append(caixa)
        self.assertIs(jogador.selecionar_caixa(partida.mundo), caixa)
        parede = CorpoRigido(jogador.olhos+jogador.direcao, Vetor3(1, 1, 0.1), 0)
        partida.mundo.corpos.append(parede)
        self.assertIsNone(jogador.selecionar_caixa(partida.mundo))
        self.assertIsNone(intersectar_raio_caixa(Vetor3(10, 1, 0), Vetor3(0, 1, 0), caixa, 3))


class TesteFisica(unittest.TestCase):
    def test_queda_repouso_e_estatico_imovel(self):
        piso, caixa = criar_piso(), criar_caixa(y=3)
        mundo = MundoFisico([piso, caixa])
        simular(mundo, 4)
        self.assertAlmostEqual(caixa.posicao.y, 0.42, delta=0.025)
        self.assertLess(caixa.velocidade.comprimento(), 0.06)
        self.assertEqual(piso.posicao, Vetor3(0, -0.3, 0))

    def test_pilha_por_trinta_segundos_e_despertar_sem_apoio(self):
        piso = criar_piso()
        caixas = [criar_caixa(y=0.42+i*0.85) for i in range(3)]
        mundo = MundoFisico([piso, *caixas])
        simular(mundo, 30)
        for i, caixa in enumerate(caixas):
            self.assertAlmostEqual(caixa.posicao.y, 0.42+i*0.84, delta=0.045)
            self.assertLess(abs(caixa.posicao.x), 0.15)
            self.assertTrue(caixa.dormindo)
        mundo.corpos.remove(caixas[0])
        simular(mundo, 2)
        self.assertLess(caixas[2].posicao.y, 1.5)

    def test_impulso_fora_do_centro_e_massas(self):
        a, b = criar_caixa(), criar_caixa(x=3)
        b.massa = 4
        impulso = Vetor3(4, 0, 0)
        aplicar_impulso(a, impulso, a.posicao+Vetor3(0, 0.2, 0))
        aplicar_impulso(b, impulso, b.posicao)
        self.assertAlmostEqual(a.velocidade.x, 2)
        self.assertAlmostEqual(b.velocidade.x, 1)
        self.assertGreater(a.velocidade_angular.comprimento(), 0)
        self.assertEqual(b.velocidade_angular, Vetor3())

    def test_impacto_transfere_movimento_e_nao_cria_energia(self):
        a, b = criar_caixa(x=-0.8, y=4), criar_caixa(x=0.8, y=4)
        a.velocidade = Vetor3(6, 0, 0)
        mundo = MundoFisico([a, b])
        simular(mundo, 0.2)
        self.assertGreater(b.velocidade.x, 1)
        energia_x = sum(c.massa*c.velocidade.x**2/2 for c in (a, b))
        self.assertLessEqual(energia_x, 36.1)

    def test_atrito_freia_deslizamento(self):
        caixa = criar_caixa()
        caixa.velocidade = Vetor3(3, 0, 0)
        simular(MundoFisico([criar_piso(), caixa]), 3)
        self.assertLess(abs(caixa.velocidade.x), 0.1)

    def test_arremesso_maximo_nao_atravessa_parede(self):
        caixa = criar_caixa(x=-2, y=2)
        caixa.velocidade = Vetor3(14, 0, 0)
        parede = CorpoRigido(Vetor3(0, 3, 0), Vetor3(0.08, 3, 3), 0)
        mundo = MundoFisico([criar_piso(), parede, caixa])
        simular(mundo, 1)
        self.assertLess(caixa.posicao.x, -0.2)

    def test_impacto_desperta_e_derruba_pilha(self):
        caixas = [criar_caixa(y=0.42+i*0.85) for i in range(3)]
        mundo = MundoFisico([criar_piso(), *caixas])
        simular(mundo, 3)
        aplicar_impulso(caixas[1], Vetor3(14, 0, 0), caixas[1].posicao)
        simular(mundo, 2)
        self.assertGreater(abs(caixas[1].posicao.x), 1)
        self.assertLess(caixas[2].posicao.y, 1.7)


class TestePartida(unittest.TestCase):
    def test_teto_impede_arremesso_para_fora_do_galpao(self):
        partida = Partida(NIVEIS[0])
        caixa = criar_caixa(8, 2, 0)
        caixa.velocidade = Vetor3(8, 11, 0)
        partida.mundo.corpos.append(caixa)
        for _ in range(360):
            partida.mundo.avancar(PASSO_FISICO)
            self.assertLess(caixa.posicao.y, 6)
            self.assertLess(abs(caixa.posicao.x), 11)

    def test_jogador_respeita_parede_e_velocidade_diagonal(self):
        partida = Partida(NIVEIS[0])
        jogador = partida.jogador
        jogador.corpo.posicao = Vetor3(8, .85, 0)
        jogador.azimute = pi/2
        for _ in range(120):
            jogador.mover(PASSO_FISICO, 1, 0, partida.mundo)
        self.assertLess(jogador.corpo.posicao.x, 10.5)
        jogador.corpo.posicao = Vetor3(4, .85, 0)
        inicio = jogador.corpo.posicao
        jogador.mover(.01, 1, 1, partida.mundo)
        self.assertAlmostEqual((jogador.corpo.posicao-inicio).comprimento(), .038)

    def test_caixa_segurada_colide_com_parede_e_rotaciona(self):
        partida = Partida(NIVEIS[0])
        jogador = partida.jogador
        jogador.corpo.posicao = Vetor3(9.1, .85, 0)
        jogador.azimute = pi/2
        jogador.elevacao = 0
        caixa = criar_caixa(9.95, 1.3, 0)
        partida.caixas.append(caixa)
        partida.mundo.corpos.append(caixa)
        jogador.segurada = caixa
        orientacao_inicial = caixa.orientacao
        jogador.girar_caixa(40, 25)
        for _ in range(180):
            partida.mundo.avancar(PASSO_FISICO,
                                   lambda dt: jogador.atualizar_interacao(dt, partida.mundo))
        self.assertLess(caixa.posicao.x, 10.5)
        self.assertNotEqual(caixa.orientacao, orientacao_inicial)
        self.assertGreater(caixa.posicao.y, .2)

    def test_esteira_transporta_e_lote_e_finito(self):
        partida = Partida(Nivel("teste", 2, 2, None, 0.2))
        partida.esteira.atualizar(0.01, partida.mundo, partida.caixas)
        caixa = partida.caixas[0]
        z_inicial = caixa.posicao.z
        for _ in range(360):
            partida.atualizar(PASSO_FISICO)
        self.assertLess(caixa.posicao.z, z_inicial-1)
        self.assertEqual(len(partida.caixas), 2)
        self.assertEqual([c.categoria for c in partida.caixas], [0, 1])

    def test_entrada_bloqueada_nao_sobrepoe_nem_perde_caixa(self):
        partida = Partida(NIVEIS[0])
        bloqueio = criar_caixa(y=1.46, z=7.9)
        partida.caixas.append(bloqueio)
        partida.esteira.atualizar(1, partida.mundo, partida.caixas)
        self.assertTrue(partida.esteira.bloqueada)
        self.assertEqual(partida.esteira.emitidas, 0)
        partida.caixas.remove(bloqueio)
        partida.esteira.atualizar(1, partida.mundo, partida.caixas)
        self.assertEqual(partida.esteira.emitidas, 1)

    def test_arremesso_e_consumido_uma_vez(self):
        partida = Partida(NIVEIS[0])
        jogador = partida.jogador
        caixa = criar_caixa()
        jogador.segurada = caixa
        jogador.carregando_arremesso = True
        jogador.carga = 1.2
        jogador.arremessar_caixa()
        velocidade = caixa.velocidade
        jogador.arremessar_caixa()
        self.assertEqual(caixa.velocidade, velocidade)
        self.assertIsNone(jogador.segurada)
        self.assertGreater(velocidade.comprimento(), 5)

    def test_organizar_exige_cor_contencao_estabilidade_e_apoio(self):
        partida = Partida(NIVEIS[0])
        area = partida.areas[0]
        caixa = criar_caixa(area.centro.x, 0.42, area.centro.z)
        partida.caixas = [caixa]
        partida.mundo.corpos.append(caixa)
        simular(partida.mundo, 2)
        self.assertIn(caixa, partida.calcular_organizadas())
        caixa.categoria = 1
        self.assertNotIn(caixa, partida.calcular_organizadas())
        caixa.categoria = 0
        caixa.posicao = area.centro+Vetor3(1.4, 0.42, 0)
        self.assertNotIn(caixa, partida.calcular_organizadas())
        caixa.posicao = area.centro+Vetor3(0, 3, 0)
        caixa.estavel_por = 0
        self.assertNotIn(caixa, partida.calcular_organizadas())

    def test_pilha_conta_e_cor_errada_na_base_invalida(self):
        partida = Partida(NIVEIS[0])
        area = partida.areas[0]
        caixas = [criar_caixa(area.centro.x, .42+i*.85, area.centro.z) for i in range(3)]
        partida.caixas = caixas
        partida.mundo.corpos.extend(caixas)
        simular(partida.mundo, 3)
        self.assertEqual(len(partida.calcular_organizadas()), 3)
        caixas[0].categoria = 1
        self.assertEqual(len(partida.calcular_organizadas()), 0)

    def test_pausa_reinicio_derrota_e_cinco_cores(self):
        partida = Partida(Nivel("teste", 5, 5, 0.1, 1))
        partida.alternar_pausa()
        partida.atualizar(1, 1, 1)
        self.assertEqual(partida.tempo, 0)
        self.assertFalse(partida.caixas)
        partida.alternar_pausa()
        partida.atualizar(0.1)
        partida.atualizar(0.02)
        self.assertEqual(partida.estado, "derrota")
        partida.reiniciar()
        self.assertEqual(len(partida.areas), 5)
        self.assertFalse(partida.caixas)
        self.assertEqual(partida.estado, "jogando")

    def test_vitoria_exige_todo_lote_e_estabilidade_final(self):
        partida = Partida(Nivel("teste", 1, 1, 20, 1))
        area = partida.areas[0]
        caixa = criar_caixa(area.centro.x, 0.42, area.centro.z)
        partida.caixas = [caixa]
        partida.mundo.corpos.append(caixa)
        partida.esteira.emitidas = 1
        for _ in range(480):
            partida.atualizar(PASSO_FISICO)
        self.assertEqual(partida.estado, "vitoria")
        tempo = partida.tempo
        partida.atualizar(0.1)
        self.assertEqual(partida.tempo, tempo)

    def test_tempo_e_resultado_independem_do_fps(self):
        resultados = []
        for fps in (30, 60, 144):
            partida = Partida(NIVEIS[0])
            for _ in range(fps):
                partida.atualizar(1/fps)
            resultados.append((partida.tempo, partida.caixas[0].posicao))
        for tempo, posicao in resultados[1:]:
            self.assertAlmostEqual(tempo, resultados[0][0])
            self.assertLess((posicao-resultados[0][1]).comprimento(), 1e-8)


if __name__ == "__main__":
    unittest.main()
