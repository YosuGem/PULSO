"""
Temas emergentes sin nombre (0.2.2-dev).

Detecta que la gente empieza a hablar de algo NUEVO antes de que exista una
categoría para ello. El clasificador actual necesita que el tema ya tenga
nombre; este módulo encuentra el tema mientras aún no lo tiene, por la
repetición de combinaciones de palabras y por la estructura de co-ocurrencias.

Tres piezas (el stacking mínimo que se auto-refuerza):

  1. **Bigramas emergentes** — combinaciones de palabras que empiezan a
     repetirse hoy y no existían antes. Filtro de novedad léxica + PMI para
     separar "frase que va cuajando" de bigrama casual.
  2. **Similitud de segundo orden** — gente describiendo lo mismo con
     vocabulario distinto. A y B nunca co-aparecen en el mismo doc, pero
     comparten vecinos. Jaccard sobre los conjuntos de vecinos.
  3. **Clustering union-find** — agrupa los términos similares en "temas sin
     nombre". Cada cluster es un concepto que la gente repite sin acuñar.

Regla de corpus pequeño: siempre crecimiento RELATIVO contra la ventana de
referencia, nunca umbrales absolutos — con pocas fechas es lo único fiable.

Diseño: stdlib puro (re, collections, math, itertools). Bajo acoplamiento:
reciben listas de documentos, no leen la BD.
Fuente: subagente semantista computacional.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any, Iterable, Sequence


# ── Tokenización ──────────────────────────────────────────────────────────
_TOKEN = re.compile(r"[a-záéíóúüñ0-9]+")


def tokenizar(texto: str) -> list[str]:
    """Tokens en minúsculas, sin acentos perdidos (unicode simple).

    Tolera `None` y no-strings: los devuelve como lista vacía en vez de
    lanzar AttributeError. Un documento nulo que llegue de la ingesta no debe
    tumbar el análisis (fallo encontrado en auditoría).
    """
    if not isinstance(texto, str):
        return []
    return _TOKEN.findall(texto.lower())


def _bigramas(tokens: Sequence[str]) -> list[tuple[str, str]]:
    return list(zip(tokens, tokens[1:]))


# ── 1. Bigramas emergentes (crecimiento + PMI) ────────────────────────────
def bigramas_emergentes(
    docs_actual: Sequence[str],
    docs_referencia: Sequence[str] | None = None,
    min_soporte: int = 2,
    min_crecimiento: float = 2.0,
    min_pmi: float = 0.8,
) -> list[dict[str, Any]]:
    """Bigramas que crecen respecto a la referencia y tienen PMI alto.

    - crecimiento: f_actual / max(f_referencia, 1)
    - PMI(a,b) = log( c(a,b)·N / (c(a)·c(b)) ) con suavizado

    `min_pmi` bajo (0.8): con textos cortos (3-5 palabras) el PMI de
    cualquier bigrama es pequeño porque N es tiny; un umbral de 2-3 solo
    aplica a corpus grande. El filtro de novedad + crecimiento es el que
    realmente separa la señal del ruido aquí, el PMI es un empujón.
    """
    tok_actual = [tokenizar(d) for d in docs_actual]
    N_actual = sum(len(t) for t in tok_actual)

    cont_bg = Counter()
    cont_un = Counter()
    for toks in tok_actual:
        cont_bg.update(_bigramas(toks))
        cont_un.update(set(toks))  # df por documento

    cont_bg_ref = Counter()
    if docs_referencia:
        for d in docs_referencia:
            cont_bg_ref.update(_bigramas(tokenizar(d)))

    candidatos = []
    for bg, freq in cont_bg.items():
        if freq < min_soporte:
            continue
        a, b = bg
        crecimiento = freq / max(cont_bg_ref.get(bg, 0), 1)
        if crecimiento < min_crecimiento:
            continue
        # PMI con suavizado (soporte bajo)
        ca = cont_un.get(a, 0)
        cb = cont_un.get(b, 0)
        if ca == 0 or cb == 0:
            continue
        pmi = math.log(((freq + 0.1) * N_actual) / ((ca + 0.1) * (cb + 0.1)))
        if pmi < min_pmi:
            continue
        # Novedad: el bigrama no existía (o era raro) en la referencia
        novedad = cont_bg_ref.get(bg, 0) == 0
        candidatos.append({
            "bigrama": f"{a} {b}",
            "frecuencia": freq,
            "crecimiento": round(crecimiento, 2),
            "pmi": round(pmi, 3),
            "novedad": novedad,
        })

    candidatos.sort(key=lambda x: x["pmi"] * x["crecimiento"], reverse=True)
    return candidatos


# ── 2. Similitud de segundo orden ─────────────────────────────────────────
def vecindarios(docs: Sequence[str], min_df: int = 2) -> dict[str, set[str]]:
    """Grafo de co-ocurrencia: término -> conjunto de términos vecinos.

    Dos términos son vecinos si co-aparecen en el mismo documento.
    """
    vecinos: dict[str, set[str]] = defaultdict(set)
    df = Counter()
    for d in docs:
        toks = set(tokenizar(d))
        df.update(toks)
        for t in toks:
            vecinos[t].update(toks)
    # Cada término no es vecino de sí mismo; filtro por df mínimo
    return {
        t: (v - {t})
        for t, v in vecinos.items()
        if df[t] >= min_df
    }


def similitud_segundo_orden(
    terminos: Iterable[str],
    vecinos: dict[str, set[str]],
    min_sim: float = 0.3,
) -> list[dict[str, Any]]:
    """Pares de términos que nunca co-aparecen pero comparten vecinos.

    Jaccard: |N(A)∩N(B)| / |N(A)∪N(B)|. Alerta si ≥ min_sim.
    """
    terminos = [t for t in terminos if t in vecinos]
    pares = []
    for i, a in enumerate(terminos):
        for b in terminos[i + 1:]:
            na, nb = vecinos.get(a, set()), vecinos.get(b, set())
            union = na | nb
            if not union:
                continue
            inter = na & nb
            jaccard = len(inter) / len(union)
            if jaccard >= min_sim and a not in nb:  # no co-aparecen directamente
                pares.append({
                    "par": (a, b),
                    "similitud": round(jaccard, 3),
                    "vecinos_compartidos": len(inter),
                })
    pares.sort(key=lambda x: x["similitud"], reverse=True)
    return pares


# ── 3. Clustering union-find ──────────────────────────────────────────────
def _union_find(pares: Sequence[dict[str, Any]]) -> list[set[str]]:
    """Agrupa pares similares en clusters (componentes conexos)."""
    padre: dict[str, str] = {}

    def encontrar(x: str) -> str:
        while padre.get(x, x) != x:
            padre[x] = padre.get(padre[x], padre[x])
            x = padre[x]
        return x

    def unir(a: str, b: str) -> None:
        ra, rb = encontrar(a), encontrar(b)
        if ra != rb:
            padre[ra] = rb

    for p in pares:
        a, b = p["par"]
        padre.setdefault(a, a)
        padre.setdefault(b, b)
        unir(a, b)

    clusters: dict[str, set[str]] = defaultdict(set)
    for t in padre:
        clusters[encontrar(t)].add(t)
    return [c for c in clusters.values() if len(c) >= 2]


def temas_sin_nombre(
    docs_actual: Sequence[str],
    docs_referencia: Sequence[str] | None = None,
    min_df: int = 2,
    min_sim: float = 0.15,
) -> dict[str, Any]:
    """Pipeline completo: bigramas emergentes + similitud + clusters.

    Devuelve los candidatos a tema (clusters de términos que la gente usa
    junto sin que exista categoría) con su evidencia (bigramas y PMI).

    `min_sim` bajo (0.15) por defecto: con corpus pequeño (pocos docs) los
    pares rara vez superan 0.3 de Jaccard; el umbral debe adaptarse al tamaño
    o la similitud de segundo orden nunca agrupa nada.
    """
    bigramas = bigramas_emergentes(docs_actual, docs_referencia)
    vecinos = vecindarios(docs_actual, min_df=min_df)

    # Términos candidatos: los que aparecen en los bigramas emergentes
    terminos = set()
    for b in bigramas:
        terminos.update(b["bigrama"].split())
    # Añadir términos de los clusters por vecindad
    pares = similitud_segundo_orden(terminos, vecinos, min_sim=min_sim) if terminos else []
    clusters = _union_find(pares)

    return {
        "bigramas_emergentes": bigramas[:20],
        "pares_similares": pares[:20],
        "clusters": [sorted(c) for c in clusters],
        "n_clusters": len(clusters),
    }


if __name__ == "__main__":
    # Demostración con texto sintético: dos temas sin nombre
    actual = [
        "the gas pipeline shutdown is causing rationing in several districts",
        "pipeline gas cuts rationing heating complaints this winter",
        "gas pipeline closure leads to rationing citizens angry",
        "new photonic processor chips replace silicon in datacenters",
        "photonic processor outperforms silicon chips in benchmarks",
        "photonic chips silicon replacement datacenter speed test",
    ]
    referencia = [
        "unrelated chatter about weather and holidays",
        "random discussion on traffic and parking",
    ]
    import json

    print(json.dumps(temas_sin_nombre(actual, referencia), indent=2, ensure_ascii=False))
