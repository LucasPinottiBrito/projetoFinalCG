"""SAT para caixas orientadas, recorte de faces e seleção por raio."""

from math import inf

from deposito.corpos import Contato
from deposito.matematica import EIXOS, Vetor3

TOLERANCIA_CONTATO = 0.008


def calcular_aabb(corpo):
    raio = Vetor3(*(corpo.raio_projetado(eixo) for eixo in EIXOS))
    return corpo.posicao - raio, corpo.posicao + raio


def aabbs_sobrepostos(limites_a, limites_b, margem=TOLERANCIA_CONTATO):
    return all(a0 <= b1 + margem and b0 <= a1 + margem
               for a0, a1, b0, b1 in zip(*limites_a, *limites_b))


def recortar_poligono(vertices, normal, limite):
    """Mantém o lado interno de um plano: normal · ponto <= limite."""
    if not vertices:
        return []
    resultado = []
    anterior = vertices[-1]
    distancia_anterior = normal.produto_escalar(anterior) - limite
    for atual in vertices:
        distancia = normal.produto_escalar(atual) - limite
        if (distancia <= 0) != (distancia_anterior <= 0):
            fracao = distancia_anterior / (distancia_anterior - distancia)
            resultado.append(anterior + (atual - anterior) * fracao)
        if distancia <= 0:
            resultado.append(atual)
        anterior, distancia_anterior = atual, distancia
    return resultado


def pontos_da_face(corpo, indice, sinal):
    outros = [i for i in range(3) if i != indice]
    centro = corpo.posicao + corpo.eixos[indice] * (tuple(corpo.metade)[indice] * sinal)
    u, v = (corpo.eixos[i] * tuple(corpo.metade)[i] for i in outros)
    return [centro-u-v, centro+u-v, centro+u+v, centro-u+v]


def contatos_de_face(referencia, incidente, indice, normal):
    """Recorta a face incidente pelas quatro laterais da face de referência."""
    indice_incidente = max(range(3), key=lambda i: abs(incidente.eixos[i].produto_escalar(normal)))
    sinal = -1 if incidente.eixos[indice_incidente].produto_escalar(normal) > 0 else 1
    pontos = pontos_da_face(incidente, indice_incidente, sinal)
    metades = tuple(referencia.metade)
    for i in range(3):
        if i == indice:
            continue
        eixo = referencia.eixos[i]
        for sentido in (-1, 1):
            lateral = eixo * sentido
            limite = lateral.produto_escalar(referencia.posicao) + metades[i]
            pontos = recortar_poligono(pontos, lateral, limite)
    plano = normal.produto_escalar(referencia.posicao) + metades[indice]
    contatos = []
    for ponto in pontos:
        profundidade = plano - normal.produto_escalar(ponto)
        if profundidade >= -TOLERANCIA_CONTATO:
            contatos.append((ponto + normal * (profundidade * 0.5), max(0, profundidade)))
    # Os extremos do polígono dão apoio distribuído, sem exceder oito contatos.
    return contatos


def ponto_suporte(corpo, direcao):
    resultado = corpo.posicao
    for eixo, metade in zip(corpo.eixos, corpo.metade):
        resultado += eixo * (metade if eixo.produto_escalar(direcao) >= 0 else -metade)
    return resultado


def segmento_suporte(corpo, indice, direcao):
    centro = corpo.posicao
    for i, (eixo, metade) in enumerate(zip(corpo.eixos, corpo.metade)):
        if i != indice:
            centro += eixo * (metade if eixo.produto_escalar(direcao) >= 0 else -metade)
    raio = corpo.eixos[indice] * tuple(corpo.metade)[indice]
    return centro-raio, centro+raio


def pontos_proximos_segmentos(p, q, r, s):
    """Menor distância entre duas arestas finitas, incluindo extremidades."""
    u, v, w = q-p, s-r, p-r
    a, b, c = u.produto_escalar(u), u.produto_escalar(v), v.produto_escalar(v)
    d, e = u.produto_escalar(w), v.produto_escalar(w)
    divisor = a*c-b*b
    t = max(0, min(1, (b*e-c*d)/divisor)) if divisor > 1e-10 else 0
    j = (b*t+e)/c
    if j < 0:
        j, t = 0, max(0, min(1, -d/a))
    elif j > 1:
        j, t = 1, max(0, min(1, (b-d)/a))
    return p+u*t, r+v*j


def detectar_colisao_caixas(a, b):
    """Testa 3 eixos de A, 3 de B e 9 produtos vetoriais (SAT 3D)."""
    deslocamento = b.posicao-a.posicao
    candidatos = [(eixo, "a", i, 0) for i, eixo in enumerate(a.eixos)]
    candidatos += [(eixo, "b", i, 0) for i, eixo in enumerate(b.eixos)]
    candidatos += [(u.produto_vetorial(v), "aresta", i, j)
                   for i, u in enumerate(a.eixos) for j, v in enumerate(b.eixos)]
    menor, escolhido = inf, None
    for eixo, tipo, i, j in candidatos:
        comprimento = eixo.comprimento()
        if comprimento < 1e-7:
            continue  # Arestas paralelas não definem um eixo separador novo.
        eixo = eixo / comprimento
        profundidade = a.raio_projetado(eixo)+b.raio_projetado(eixo)-abs(deslocamento.produto_escalar(eixo))
        if profundidade < -TOLERANCIA_CONTATO:
            return []
        # Pequena preferência por faces evita alternância numérica face/aresta.
        custo = profundidade + (0.002 if tipo == "aresta" else 0)
        if custo < menor:
            menor = custo
            normal = eixo if deslocamento.produto_escalar(eixo) >= 0 else -eixo
            escolhido = normal, tipo, i, j, profundidade
    normal, tipo, i, j, profundidade = escolhido
    if tipo == "a":
        pontos = contatos_de_face(a, b, i, normal)
    elif tipo == "b":
        pontos = contatos_de_face(b, a, i, -normal)
    else:
        pa, pb = pontos_proximos_segmentos(*segmento_suporte(a, i, normal),
                                          *segmento_suporte(b, j, -normal))
        pontos = [((pa+pb)*0.5, max(0, profundidade))]
    return [Contato(a, b, normal, ponto, profundidade) for ponto, profundidade in pontos]


def intersectar_raio_caixa(origem, direcao, corpo, alcance):
    """Método das faixas no espaço local; retorna distância ou None."""
    origem_local = corpo.mundo_para_local(origem)
    inicio, fim = 0.0, alcance
    for eixo, coordenada, metade in zip(corpo.eixos, origem_local, corpo.metade):
        componente = direcao.produto_escalar(eixo)
        if abs(componente) < 1e-9:
            if abs(coordenada) > metade:
                return None
            continue
        t0, t1 = (-metade-coordenada)/componente, (metade-coordenada)/componente
        inicio, fim = max(inicio, min(t0, t1)), min(fim, max(t0, t1))
        if inicio > fim:
            return None
    return inicio
