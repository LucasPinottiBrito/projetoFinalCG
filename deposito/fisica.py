"""Integração e impulsos sequenciais. Nenhuma função depende de OpenGL."""

from math import ceil, sqrt

from deposito.colisoes import aabbs_sobrepostos, calcular_aabb, detectar_colisao_caixas
from deposito.corpos import aplicar_impulso
from deposito.matematica import Vetor3, integrar_orientacao

GRAVIDADE = Vetor3(0, -9.81, 0)
PASSO_FISICO = 1 / 120
ITERACOES_CONTATO = 10
VELOCIDADE_MAXIMA = 14.0
GIRO_MAXIMO = 12.0


def velocidade_no_ponto(corpo, ponto):
    return corpo.velocidade + corpo.velocidade_angular.produto_vetorial(ponto-corpo.posicao)


def calcular_massa_efetiva(corpo, ponto, direcao):
    """Inclui o braço de alavanca: o mesmo impulso também gasta energia girando."""
    braco = ponto-corpo.posicao
    rotacao = corpo.aplicar_inercia_inversa(braco.produto_vetorial(direcao))
    return corpo.massa_inversa + rotacao.produto_vetorial(braco).produto_escalar(direcao)


def aplicar_impulso_par(contato, impulso):
    aplicar_impulso(contato.a, -impulso, contato.ponto)
    aplicar_impulso(contato.b, impulso, contato.ponto)


def resolver_contato(contato):
    a, b, normal, ponto = contato.a, contato.b, contato.normal, contato.ponto
    relativa = velocidade_no_ponto(b, ponto)-velocidade_no_ponto(a, ponto)
    massa = calcular_massa_efetiva(a, ponto, normal)+calcular_massa_efetiva(b, ponto, normal)
    if massa < 1e-10:
        return
    impulso = (contato.velocidade_restituicao-relativa.produto_escalar(normal))/massa
    anterior = contato.impulso_normal
    # Contato pode empurrar, mas nunca puxar um corpo de volta para a superfície.
    contato.impulso_normal = max(0, anterior+impulso)
    aplicar_impulso_par(contato, normal*(contato.impulso_normal-anterior))

    relativa = (velocidade_no_ponto(b, ponto)+b.superficie
                -velocidade_no_ponto(a, ponto)-a.superficie)
    tangente = relativa-normal*relativa.produto_escalar(normal)
    if tangente.comprimento() < 1e-8:
        return
    direcao = tangente.normalizado()
    massa_tangente = calcular_massa_efetiva(a, ponto, direcao)+calcular_massa_efetiva(b, ponto, direcao)
    candidato = contato.impulso_atrito-direcao*(tangente.comprimento()/massa_tangente)
    limite = sqrt(a.atrito*b.atrito)*contato.impulso_normal
    novo = candidato.limitado(limite)
    aplicar_impulso_par(contato, novo-contato.impulso_atrito)
    contato.impulso_atrito = novo


def corrigir_penetracao(contatos):
    """Uma correção por par; não multiplicar a correção pelo número de pontos."""
    if not contatos:
        return
    contato = max(contatos, key=lambda item: item.penetracao)
    a, b = contato.a, contato.b
    excesso = min(0.08, max(0, contato.penetracao-0.002))
    soma = a.massa_inversa+b.massa_inversa
    if soma:
        correcao = contato.normal*(excesso*0.55/soma)
        a.posicao -= correcao*a.massa_inversa
        b.posicao += correcao*b.massa_inversa


class MundoFisico:
    def __init__(self, corpos=None):
        self.corpos = list(corpos or [])
        self.contatos = []
        self.pares_ignorados = set()
        self.subdivisoes = 1
        self.cache_contatos = {}

    def acordar_grupo(self, corpo):
        """Um impacto ou apoio retirado desperta toda a pilha conectada."""
        pendentes, vistos = [corpo], set()
        while pendentes:
            atual = pendentes.pop()
            if atual in vistos or not atual.massa:
                continue
            vistos.add(atual)
            atual.dormindo = False
            atual.estavel_por = 0
            for contato in self.contatos:
                if contato.a is atual and contato.b.massa:
                    pendentes.append(contato.b)
                elif contato.b is atual and contato.a.massa:
                    pendentes.append(contato.a)

    def detectar_contatos(self):
        limites = {corpo: calcular_aabb(corpo) for corpo in self.corpos}
        contatos, grupos, cache = [], [], {}
        for i, a in enumerate(self.corpos):
            for b in self.corpos[i+1:]:
                if not (a.massa or b.massa) or frozenset((a, b)) in self.pares_ignorados:
                    continue
                if not aabbs_sobrepostos(limites[a], limites[b]):
                    continue
                chave = a, b
                assinatura = a.posicao, a.orientacao, b.posicao, b.orientacao
                anterior = self.cache_contatos.get(chave)
                if anterior and assinatura == anterior[0]:
                    grupo = anterior[1]
                else:
                    grupo = detectar_colisao_caixas(a, b)
                cache[chave] = assinatura, grupo
                if grupo:
                    if a.massa and a.dormindo and ((b.massa and not b.dormindo) or b.velocidade.comprimento() > 0.1 or b.superficie.comprimento() > 0):
                        self.acordar_grupo(a)
                    if b.massa and b.dormindo and ((a.massa and not a.dormindo) or a.velocidade.comprimento() > 0.1 or a.superficie.comprimento() > 0):
                        self.acordar_grupo(b)
                    grupos.append(grupo)
                    contatos.extend(grupo)
        self.cache_contatos = cache
        return contatos, grupos

    def atualizar_repouso(self, dt, dinamicos):
        apoiados = set()
        for _ in range(len(dinamicos)+1):
            for contato in self.contatos:
                inferior, superior = (contato.a, contato.b) if contato.normal.y > 0.7 else (contato.b, contato.a)
                if abs(contato.normal.y) > 0.7 and (not inferior.massa or inferior in apoiados):
                    if not inferior.superficie.comprimento():
                        apoiados.add(superior)
        for corpo in dinamicos:
            if corpo.dormindo and corpo not in apoiados:
                self.acordar_grupo(corpo)
            if corpo.velocidade.comprimento() < 0.10 and corpo.velocidade_angular.comprimento() < 0.10:
                corpo.estavel_por += dt
            else:
                corpo.estavel_por = 0
        # Dormir só grupos inteiros; uma caixa ativa não pode sustentar outra congelada.
        restantes = set(dinamicos)
        while restantes:
            grupo, pendentes = set(), [restantes.pop()]
            while pendentes:
                corpo = pendentes.pop()
                if corpo in grupo:
                    continue
                grupo.add(corpo)
                restantes.discard(corpo)
                for contato in self.contatos:
                    if contato.a is corpo and contato.b.massa:
                        pendentes.append(contato.b)
                    elif contato.b is corpo and contato.a.massa:
                        pendentes.append(contato.a)
            if all(c in apoiados and c.estavel_por > 1.5 for c in grupo):
                for corpo in grupo:
                    corpo.dormindo = True
                    corpo.velocidade = Vetor3()
                    corpo.velocidade_angular = Vetor3()

    def avancar(self, dt, antes_do_passo=None):
        """Subdivide movimentos rápidos; a força de interação é reaplicada por subpasso."""
        dinamicos = [corpo for corpo in self.corpos if corpo.massa]
        deslocamento = max((corpo.velocidade.comprimento()
                            +corpo.velocidade_angular.comprimento()*corpo.metade.comprimento()
                            for corpo in dinamicos if not corpo.dormindo), default=0)*dt
        menor = min((min(corpo.metade) for corpo in dinamicos), default=0.4)
        self.subdivisoes = max(1, min(8, ceil(deslocamento/max(0.04, menor*0.4))))
        passo = dt/self.subdivisoes
        for _ in range(self.subdivisoes):
            if antes_do_passo:
                antes_do_passo(passo)
            for corpo in dinamicos:
                if corpo.dormindo:
                    continue
                corpo.velocidade = ((corpo.velocidade+GRAVIDADE*passo)*(1-0.025*passo)).limitado(VELOCIDADE_MAXIMA)
                corpo.velocidade_angular = (corpo.velocidade_angular*(1-0.10*passo)).limitado(GIRO_MAXIMO)
                corpo.posicao += corpo.velocidade*passo
                corpo.orientacao = integrar_orientacao(corpo.orientacao, corpo.velocidade_angular, passo)
                corpo.atualizar_eixos()
            self.contatos, grupos = self.detectar_contatos()
            ativos = [contato for contato in self.contatos
                      if (contato.a.massa and not contato.a.dormindo)
                      or (contato.b.massa and not contato.b.dormindo)]
            for contato in ativos:
                contato.impulso_normal = 0
                contato.impulso_atrito = Vetor3()
                relativa = velocidade_no_ponto(contato.b, contato.ponto)-velocidade_no_ponto(contato.a, contato.ponto)
                aproximacao = relativa.produto_escalar(contato.normal)
                # Ressaltos minúsculos no repouso mantêm pilhas vibrando indefinidamente.
                contato.velocidade_restituicao = -min(contato.a.restituicao, contato.b.restituicao)*aproximacao if aproximacao < -1 else 0
            for _ in range(ITERACOES_CONTATO):
                for contato in ativos:
                    resolver_contato(contato)
            for grupo in grupos:
                if any((c.a.massa and not c.a.dormindo) or (c.b.massa and not c.b.dormindo) for c in grupo):
                    corrigir_penetracao(grupo)
        self.atualizar_repouso(dt, dinamicos)
