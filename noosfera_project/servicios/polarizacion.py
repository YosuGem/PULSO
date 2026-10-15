"""
Polarización y propagación (0.2.2-dev).

Dos capacidades que el subagente experto en dinámica de grupo propuso, pero
**ajustadas a los datos que el sistema realmente tiene**.

Ajuste importante
-----------------
El subagente asumía autores por post y score emocional guardados. Verificado:
el corpus NO tiene campo de autor ni score emocional (solo id, fuente, texto,
hash, fechas, idioma). Por eso NO se implementaron las técnicas que dependen
de autores (VEL, RET, SEG). En su lugar:

  1. **Polarización por léxico** — un léxico pro/contra en castellano sobre el
     propio texto (que sí tenemos). Calcula el índice de bimodalidad: ¿el tema
     se parte en dos facciones o hay una sola voz?
  2. **Propagación cruzada entre fuentes (XSRC)** — cuántas fuentes distintas
     hablan del tema por día. El salto de comunidad a comunidad es el sello de
     que algo va a mainstream. Funciona con el campo `fuente` que sí existe.
  3. **Veredicto compuesto** — combina polarización + propagación + volumen en
     crece/muere/latente.

Cuando se añada el campo autor al corpus, se pueden sumar VEL/RET/SEG encima
de esto sin tocar la base.

Diseño: stdlib puro. Bajo acoplamiento: reciben listas de documentos.
Fuente: subagente experto en dinámica de grupo (ajustado a datos reales).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Sequence


# ── Léxico pro/contra (castellano, sin acentos) ───────────────────────────
PRO = {
    "apoyo", "apoyo", "bueno", "buena", "mejor", "mejora", "excelente", "genial",
    "favor", "acuerdo", "si", "positivo", "beneficio", "ventaja", "necesario",
    "correcto", "bien", "gran", "gran", "claro", "razon", "logico", "oportunidad",
    "solucion", "avance", "progreso", "exito", "funciona", "util", "vale",
}
CONTRA = {
    "malo", "mala", "peor", "empeora", "terrible", "horrible", "contra", "desacuerdo",
    "no", "negativo", "problema", "desventaja", "inutil", "incorrecto", "fatal",
    "error", "fallo", "fracaso", "crisis", "peligro", "riesgo", "mentira", "robo",
    "estafa", "injusto", "absurdo", "verguenza", "basura", "destruye", "ruina",
    # Ampliado en auditoría: negativos claros que faltaban.
    "desastre", "desastroso", "catastrofe", "desgracia", "lamentable", "penoso",
    "deplorable", "intolerable", "insostenible", "insoportable", "asco", "mierda",
    "muertos", "muertes", "victimas", "tragedia", "caos", "colapso", "desplome",
    "estafadores", "corruptos", "corrupcion", "delincuentes", "criminales",
}
NEUTRO_UMBRAL = 1  # por debajo de esto se considera neutro


def _signo_texto(texto: str) -> int:
    """+1 si el texto tiene más léxico pro, -1 si contra, 0 si equilibrado.

    Tolera `None` y no-strings (devuelve 0 = neutro): un documento nulo de la
    ingesta no debe tumbar el análisis (fallo encontrado en auditoría).
    """
    if not isinstance(texto, str):
        return 0
    palabras = set(texto.lower().replace(".", " ").replace(",", " ").split())
    pro = len(palabras & PRO)
    contra = len(palabras & CONTRA)
    if pro - contra >= NEUTRO_UMBRAL:
        return 1
    if contra - pro >= NEUTRO_UMBRAL:
        return -1
    return 0


# ── 1. Polarización (bimodalidad) ─────────────────────────────────────────
def polarizacion(docs: Sequence[str]) -> dict[str, Any]:
    """Índice de polarización: ¿el tema se parte en dos facciones?

    p_pro / p_con / p_neu sobre el léxico. Polarizado si ambas facciones
    tienen peso real (≥25% cada una) y el índice min/max se acerca a 1.
    """
    if not docs:
        return {"indice": 0.0, "polarizado": False, "p_pro": 0.0, "p_con": 0.0, "nota": "sin docs"}

    signos = [_signo_texto(d) for d in docs]
    n = len(signos)
    p_pro = sum(1 for s in signos if s > 0) / n
    p_con = sum(1 for s in signos if s < 0) / n

    # Índice de bimodalidad: min/max (1 = facciones equilibradas)
    if p_pro == 0 and p_con == 0:
        indice = 0.0
    else:
        indice = min(p_pro, p_con) / max(p_pro, p_con, 1e-9)

    # Polarizado = facciones equilibradas Y ambas con peso real
    polarizado = p_pro >= 0.25 and p_con >= 0.25 and indice >= 0.5

    return {
        "indice": round(indice, 3),
        "polarizado": polarizado,
        "p_pro": round(p_pro, 3),
        "p_con": round(p_con, 3),
        "n_docs": n,
    }


# ── 2. Propagación cruzada entre fuentes (XSRC) ───────────────────────────
def propagacion_fuentes(docs_por_dia: Sequence[Sequence[dict[str, Any]]]) -> dict[str, Any]:
    """Cuántas fuentes distintas hablan del tema, por día.

    `docs_por_dia`: lista de días; cada día es una lista de dicts con 'fuente'.
    El salto de comunidad a comunidad es el sello de crecimiento a mainstream.
    """
    fuentes_por_dia = []
    for dia in docs_por_dia:
        # Tolera documentos None o sin campo 'fuente' (fallo de auditoría).
        fuentes = {
            d.get("fuente", "?")
            for d in dia
            if isinstance(d, dict) and d.get("fuente")
        }
        fuentes_por_dia.append(len(fuentes))

    if len(fuentes_por_dia) < 2:
        return {"fuentes_hoy": fuentes_por_dia[0] if fuentes_por_dia else 0,
                "fuentes_ayer": 0, "salto": 0, "crece": False, "nota": "necesita 2+ días"}

    hoy, ayer = fuentes_por_dia[-1], fuentes_por_dia[-2]
    salto = hoy - ayer
    return {
        "fuentes_hoy": hoy,
        "fuentes_ayer": ayer,
        "salto": salto,
        "crece": hoy >= 2 and salto > 0,  # ≥2 fuentes y sumando
        "max_fuentes": max(fuentes_por_dia),
    }


def entropia_fuentes(docs: Sequence[dict[str, Any]]) -> float:
    """Entropía de la distribución de posts entre fuentes.

    Alta = el tema se reparte entre muchas comunidades (mainstream).
    Baja = todo sale de 1-2 fuentes (burbuja).
    """
    cont = Counter(
        d.get("fuente", "?")
        for d in docs
        if isinstance(d, dict) and d.get("fuente")
    )
    n = sum(cont.values())
    if n == 0 or len(cont) <= 1:
        return 0.0
    return round(-sum((c / n) * math.log2(c / n) for c in cont.values()), 3)


# ── 3. Veredicto compuesto (crece / muere / latente) ──────────────────────
def veredicto(
    docs: Sequence[str],
    docs_por_dia: Sequence[Sequence[dict[str, Any]]],
) -> dict[str, Any]:
    """Combina polarización, propagación y volumen en crece/muere/latente.

    Votación ponderada (log-odds), coherente con el ensemble de señal corta.
    """
    pol = polarizacion(docs)
    prop = propagacion_fuentes(docs_por_dia)
    entr = entropia_fuentes([d for dia in docs_por_dia for d in dia])

    score = 0.0
    motivos = []

    # Volumen por día (¿crece o decrece?)
    volumen = [len(dia) for dia in docs_por_dia]
    if len(volumen) >= 2:
        if volumen[-1] > volumen[-2]:
            score += 1.0
            motivos.append("volumen sube")
        elif volumen[-1] < volumen[-2]:
            score -= 1.0
            motivos.append("volumen baja")

    # Propagación entre fuentes
    if prop.get("crece"):
        score += 1.5
        motivos.append("salta a más fuentes")
    elif prop.get("fuentes_hoy", 0) <= 1 and len(docs) >= 3:
        score -= 0.5
        motivos.append("confinado a una fuente")

    # Polarización moderada empuja (combustible de discusión)
    if pol["polarizado"]:
        score += 1.0
        motivos.append("polarizado (debate activo)")

    # Entropía alta = se reparte entre comunidades
    if entr >= 1.5:
        score += 0.5
        motivos.append("repartido entre comunidades")

    if score >= 2.0:
        v = "crece"
    elif score <= -1.5:
        v = "muere"
    else:
        v = "latente"

    return {
        "veredicto": v,
        "score": round(score, 2),
        "motivos": motivos,
        "polarizacion": pol,
        "propagacion": prop,
        "entropia_fuentes": entr,
    }


if __name__ == "__main__":
    # Demostración: tema polarizado que salta a más fuentes (crece)
    docs = [
        "esto es un gran avance, muy necesario",
        "que no, es un desastre absoluto",
        "apoyo totalmente, es la solucion",
        "falso, es una estafa peligrosa",
        "bueno pero con riesgos",
    ]
    por_dia = [
        [{"fuente": "foroA"}, {"fuente": "foroA"}],
        [{"fuente": "foroA"}, {"fuente": "reddit"}],
        [{"fuente": "foroA"}, {"fuente": "reddit"}, {"fuente": "mastodon"}],
    ]
    import json

    print(json.dumps(veredicto(docs, por_dia), indent=2, ensure_ascii=False))
