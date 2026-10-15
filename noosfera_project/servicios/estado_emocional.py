"""
Estado emocional colectivo (0.2.2-dev).

Tres capacidades del psicólogo social computacional, alineadas con el objetivo
de anticipar acción colectiva. La emoción cristaliza en acción: cuando una
 comunidad pasa del miedo a la ira (con un culpable), o de la resignación a
la esperanza, la movilización está cerca.

  1. **Termómetro de amenaza** — miedo colectivo = amenaza percibida − control
     percibido. Miedo instalado y sostenido es el caldo de cultivo.
  2. **Culpabilización** — el gatillo miedo→ira: cuando el miedo busca un
     responsable ("por culpa de"). La ira llega 1-2 días después.
  3. **Eje resignación↔esperanza** — "da igual" vs "podemos". El cruce de
     negativo a positivo con volumen creciente abre la ventana de movilización.

Diseño: stdlib puro. Léxicos por idioma. Bajo acoplamiento: reciben listas de
documentos. Encaja con el pipeline existente (escalada_tono mide la etapa
colectiva; esto mide la emoción de fondo).
Fuente: subagente psicólogo social computacional.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Sequence

from noosfera_project.servicios.inteligencia_predictiva import _contiene_palabra


# ── Léxicos (castellano base; extender por idioma cuando haya datos) ──────
_AMENAZA = {
    "peligro", "amenaza", "miedo", "pánico", "catástrofe", "crisis", "nos van a",
    "puede que", "no sé si", "inseguridad", "riesgo", "temor", "pavor", "pánico",
    "desastre", "colapso", "peligra", "inminente", "grave", "crítico",
}
_CONTROL = {
    "podemos", "controlar", "solución", "medida", "control", "gestionar",
    "resolver", "evitar", "prevenir", "plan", "proteger", "seguro", "tranquilo",
    "manejar", "frenar", "detener",
}
_CULPA = {
    "por culpa de", "ellos son los", "los responsables", "culpa de", "culpables",
    "los políticos", "los de arriba", "el gobierno", "los bancos", "los ricos",
    "son los causantes", "por su culpa", "los culpables", "nos han hecho",
}
_RESIGNACION = {
    "da igual", "para qué", "nunca cambia", "siempre igual", "no sirve de nada",
    "es inútil", "para qué votar", "no tiene sentido", "me rindo", "da lo mismo",
    "siempre será igual", "nunca aprenderán", "esperar lo peor", "ya nada importa",
}
_ESPERANZA = {
    "podemos", "juntos", "propongo", "hay que", "unámonos", "sí se puede",
    "es posible", "tengo esperanza", "confío", "unidos", "lucha", "cambio",
    "mejorar", "avanzar", "construir", "lograremos", "vamos a conseguirlo",
}


def _densidad(texto: str, lexico: set[str]) -> float:
    """Palabras del léxico por cada 100 tokens (normaliza longitud)."""
    if not isinstance(texto, str):
        return 0.0
    tokens = texto.lower().split()
    if not tokens:
        return 0.0
    hits = sum(1 for p in lexico if _contiene_palabra(texto.lower(), p))
    return round(hits / len(tokens) * 100, 3)


# ── 1. Termómetro de amenaza (miedo) ──────────────────────────────────────
def termometro_amenaza(docs: Sequence[str]) -> dict[str, Any]:
    """Miedo colectivo = amenaza − control (por cada 100 tokens).

    Miedo instalado y sostenido es el caldo de cultivo de la acción.
    Si el miedo empieza a bajar mientras sube la culpa, llega la transición
    miedo→ira.
    """
    if not docs:
        return {"amenaza": 0.0, "control": 0.0, "miedo": 0.0, "nota": "sin docs"}
    amenaza = _densidad_media(docs, _AMENAZA)
    control = _densidad_media(docs, _CONTROL)
    miedo = round(amenaza - control, 3)
    return {
        "amenaza": amenaza,
        "control": control,
        "miedo": miedo,
        "miedo_instalado": miedo > 1.0,
        "n_docs": len(docs),
    }


# ── 2. Culpabilización (gatillo miedo→ira) ────────────────────────────────
def culpabilizacion(docs: Sequence[str]) -> dict[str, Any]:
    """Cuántos docs con miedo buscan un responsable.

    ratio = docs con culpa / docs con miedo. Cruzar 0.5 con miedo alto abre
    la ventana de conversión emocional: la ira llega 1-2 días después.
    """
    if not docs:
        return {"ratio": 0.0, "docs_culpa": 0, "docs_miedo": 0, "nota": "sin docs"}
    docs_miedo = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _AMENAZA))
    docs_culpa = sum(
        1 for d in docs
        if isinstance(d, str) and _contiene_alguna(d, _AMENAZA) and _contiene_alguna(d, _CULPA)
    )
    ratio = round(docs_culpa / docs_miedo, 3) if docs_miedo else 0.0
    return {
        "ratio": ratio,
        "docs_culpa": docs_culpa,
        "docs_miedo": docs_miedo,
        "gatillo_ira": ratio >= 0.5 and docs_miedo >= 2,
    }


# ── 3. Eje resignación ↔ esperanza ────────────────────────────────────────
def resignacion_esperanza(docs: Sequence[str]) -> dict[str, Any]:
    """Índice = esperanza − resignación. Cruce a positivo = movilización.

    Cruce del índice de negativo a positivo con volumen creciente abre la
    ventana de movilización. Divergencia (esperanza sube, volumen no) es
    euforia estéril.
    """
    if not docs:
        return {"esperanza": 0.0, "resignacion": 0.0, "indice": 0.0, "nota": "sin docs"}
    esperanza = _densidad_media(docs, _ESPERANZA)
    resignacion = _densidad_media(docs, _RESIGNACION)
    indice = round(esperanza - resignacion, 3)
    return {
        "esperanza": esperanza,
        "resignacion": resignacion,
        "indice": indice,
        "ventana_movilizacion": indice > 0,
    }


# ── Helpers ───────────────────────────────────────────────────────────────
def _densidad_media(docs: Sequence[str], lexico: set[str]) -> float:
    vals = [_densidad(d, lexico) for d in docs if isinstance(d, str)]
    return round(sum(vals) / len(vals), 3) if vals else 0.0


def _contiene_alguna(texto: str, lexico: set[str]) -> bool:
    return any(_contiene_palabra(texto.lower(), p) for p in lexico)


if __name__ == "__main__":
    import json

    miedo_docs = [
        "hay un peligro inminente, puede que ocurra una catastrofe, no se si estamos seguros",
        "el miedo al colapso crece, la crisis nos amenaza, nadie sabe que va a pasar",
        "todo esto es por culpa del gobierno y los politicos, ellos son los responsables",
    ]
    print("AMENAZA:   ", json.dumps(termometro_amenaza(miedo_docs), ensure_ascii=False))
    print("CULPA:     ", json.dumps(culpabilizacion(miedo_docs), ensure_ascii=False))

    esperanza_docs = [
        "juntos podemos lograrlo, si se puede, tengo esperanza",
        "unidos vamos a conseguirlo, es posible, hay que construir el cambio",
        "propongo que nos unamos, si se puede cambiar",
    ]
    print("ESPERANZA: ", json.dumps(resignacion_esperanza(esperanza_docs), ensure_ascii=False))
