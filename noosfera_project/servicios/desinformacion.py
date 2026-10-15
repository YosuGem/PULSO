"""
Detección de desinformación y astroturfing (0.2.2-dev).

Para qué sirve
--------------
PULSO escucha "voz de gente común". Pero parte de lo que parece gente común
puede ser manipulación orquestada (astroturfing): cuentas coordinadas que
simulan consenso espontáneo. Si el programa no puede distinguir la voz
genuina de la fabricada, un tema "emergente" puede ser una campaña falsa.

Tres detectores que miden ESTRUCTURA DE CONTENIDO (no timing, porque el
corpus tiene pocas fechas):

  1. **Plantilla de copia** — mensajes con el mismo "esqueleto" (stopwords y
     tokens frecuentes iguales, los raros reemplazados por _). Un esqueleto
     compartido por ≥4 textos = cluster astroturf.
  2. **Amplificación simétrica** — el mismo argumento parafraseado en varias
     fuentes (similitud de bigramas 0.3-0.7: ni copia exacta ni coincidencia).
     Mide consenso fabricado.
  3. **Eco prestado** — testimonios personales genéricos ("a mi hijo le pasó")
     sin anclas de realidad (nombres, lugares, fechas). La firma del
     astroturfing: anécdotas intercambiables.

Diseño: stdlib puro (re, collections, statistics). Bajo acoplamiento: reciben
listas de documentos. Reutiliza la normalización existente.
Fuente: subagente experto en desinformación y guerra cognitiva.
"""

from __future__ import annotations

import re
from collections import Counter
from itertools import combinations
from typing import Any, Sequence


# ── Normalización de tokens ───────────────────────────────────────────────
_TOKEN = re.compile(r"[a-záéíóúüñ0-9]+")
_ARTICULOS = {"el", "la", "los", "las"}  # artículos a ignorar para esqueleto


def _tokens(texto: str) -> list[str]:
    if not isinstance(texto, str):
        return []
    toks = _TOKEN.findall(texto.lower())
    return [t for t in toks if t not in _ARTICULOS]  # filtrar artículos


def _esqueleto(tokens: list[str], frecuencia_min: int = 2, corpus_freq: Counter | None = None) -> tuple:
    """Reemplaza tokens raros por '_'. Lo que queda es la plantilla.

    Los tokens con frecuencia < frecuencia_min (en el doc o en el corpus) se
    consideran raros → '_'. El esqueleto son los tokens frecuentes (stopwords
    incluidas, que son justo la estructura).

    `frecuencia_min` = 2 (no 3): con corpus pequeño (pocos docs), umbral 3
    marca casi todo como raro y el esqueleto pierde la estructura. En corpus
    grande conviene subirlo para que solo la estructura real sobreviva.
    """
    if corpus_freq is None:
        freq = Counter(tokens)
    else:
        freq = corpus_freq
    return tuple(t if freq.get(t, 0) >= frecuencia_min else "_" for t in tokens)


# ── 1. Plantilla de copia (esqueletos idénticos) ──────────────────────────
def plantillas(docs: Sequence[str], min_cluster: int = 4) -> list[dict[str, Any]]:
    """Agrupa textos por esqueleto idéntico. Clusters grandes = astroturf.

    Un esqueleto compartido por ≥min_cluster textos es un cluster sospechoso:
    la misma estructura con palabras intercambiadas.
    """
    docs_validos = [d for d in docs if isinstance(d, str) and d.strip()]
    if len(docs_validos) < min_cluster:
        return []
    corpus_freq: Counter = Counter()
    for d in docs_validos:
        corpus_freq.update(set(_tokens(d)))

    esqueletos: dict[tuple, list[int]] = {}
    for i, d in enumerate(docs_validos):
        esq = _esqueleto(_tokens(d), corpus_freq=corpus_freq)
        if len(esq) >= 4:  # esqueletos muy cortos no significan nada
            esqueletos.setdefault(esq, []).append(i)

    clusters = []
    for esq, idxs in esqueletos.items():
        if len(idxs) >= min_cluster:
            clusters.append({
                "esqueleto": " ".join(esq),
                "n_textos": len(idxs),
                "indices": idxs,
            })
    clusters.sort(key=lambda x: x["n_textos"], reverse=True)
    return clusters


# ── 2. Amplificación simétrica (paráfrasis multi-fuente) ──────────────────
def _bigramas(tokens: list[str]) -> set:
    return set(zip(tokens, tokens[1:]))


def amplificacion(docs: Sequence[str], min_sim: float = 0.3, max_sim: float = 0.7) -> list[dict[str, Any]]:
    """Detecta el mismo argumento parafraseado (similitud de bigramas).

    Pares con similitud en [min_sim, max_sim]: ni copia exacta (=plantilla) ni
    independientes (=coincidencia). Mide consenso fabricado. Limitado a una
    muestra para no ser O(n²) caro.
    """
    docs_validos = [d for d in docs if isinstance(d, str) and d.strip()]
    muestra = docs_validos[:200]  # límite de rendimiento
    bigramas = [_bigramas(_tokens(d)) for d in muestra]
    pares = []
    for i, j in combinations(range(len(muestra)), 2):
        a, b = bigramas[i], bigramas[j]
        if not a or not b:
            continue
        jaccard = len(a & b) / len(a | b)
        if min_sim <= jaccard <= max_sim:
            pares.append({"par": (i, j), "similitud": round(jaccard, 3)})
    pares.sort(key=lambda x: x["similitud"], reverse=True)
    return pares[:20]


# ── 3. Eco prestado (testimonios huecos) ──────────────────────────────────
_PRIMERA_PERSONA = {"yo", "mi", "me", "conmigo", "mio", "mía"}
_VERBOS_EXPERIENCIA = {
    "vivi", "viví", "pase", "pasé", "vi", "vio", "paso", "pasó", "vivia",
    "vivía", "sufri", "sufrí", "tuve", "recibi", "recibí", "conoci", "conocí",
}
# Anclas de realidad: mayúsculas no iniciales (nombres propios), dígitos (fechas/cifras)
_MAYUSCULA_INTERNA = re.compile(r"(?<!^)(?<!\. )\b[A-ZÁÉÍÓÚÑ][a-záéíóúüñ]+")
_DIGITO = re.compile(r"\d")


def eco_prestado(docs: Sequence[str]) -> dict[str, Any]:
    """Testimonios personales sin anclas de realidad.

    "A mi hijo le pasó" sin nombres, lugares ni fechas = anécdota
    intercambiable, firma del astroturfing. El contenido orgánico suele tener
    detalles concretos.
    """
    if not docs:
        return {"testimonios_huecos": 0.0, "n_docs": 0, "nota": "sin docs"}
    n_huecos = 0
    for d in docs:
        if not isinstance(d, str):
            continue
        toks = set(_tokens(d))
        # ¿tiene primera persona + verbo de experiencia?
        personal = bool(toks & _PRIMERA_PERSONA)
        experiencia = any(_contiene_palabra_real(d, v) for v in _VERBOS_EXPERIENCIA)
        # ¿carece de anclas de realidad? (sin nombres propios internos ni dígitos)
        sin_nombre = not _MAYUSCULA_INTERNA.search(d)
        sin_numero = not _DIGITO.search(d)
        if personal and experiencia and sin_nombre and sin_numero:
            n_huecos += 1
    prop = round(n_huecos / len(docs), 3)
    return {
        "testimonios_huecos": prop,
        "n_huecos": n_huecos,
        "n_docs": len(docs),
        "posible_astroturf": prop >= 0.15,
    }


def _contiene_palabra_real(texto: str, palabra: str) -> bool:
    return bool(re.search(rf"\b{re.escape(palabra)}\b", texto.lower()))


if __name__ == "__main__":
    import json

    astro = [
        "como vecino me preocupa mucho este tema porque es importante para todos",
        "como ciudadano me preocupa mucho este asunto porque es clave para el pais",
        "como padre me preocupa mucho esta situacion porque afecta a las familias",
        "como contribuyente me preocupa mucho el asunto porque es vital para españa",
        "a mi hijo le paso algo parecido y fue terrible",
        "a mi hija le paso una situacion similar y fue horrible",
    ]
    print("PLANTILLAS:  ", json.dumps(plantillas(astro), ensure_ascii=False))
    print("AMPLIFICACION:", json.dumps(amplificacion(astro), ensure_ascii=False))
    print("ECO PRESTADO:", json.dumps(eco_prestado(astro), ensure_ascii=False))
