"""Agrupación de señales por tema + idioma (Bloque C - Fase 2)."""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def agrupar(senales: list[dict[str, Any]], umbral_coincidencias: int = 3) -> list[dict[str, Any]]:
    """Agrupa señales por (categoria, idioma) y calcula intensidad del grupo.

    Devuelve grupos con: categoria, idioma, num_senales, score_medio, signo_dominante.
    """
    grupos_raw: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for s in senales:
        key = (s.get("categoria", "undetected"), s.get("idioma", "es"))
        grupos_raw[key].append(s)

    grupos: list[dict[str, Any]] = []
    for (cat, idioma), lista in grupos_raw.items():
        # Filtrar ruido: "undetected" requiere al menos 5 señales para ser grupo
        if cat == "undetected" and len(lista) < 5:
            continue
        scores = [s["score_emocional"] for s in lista]
        score_medio = sum(scores) / len(scores)
        # Signo dominante: cuenta positivos vs negativos
        pos = sum(1 for s in lista if s["signo"] == "positivo")
        neg = sum(1 for s in lista if s["signo"] == "negativo")
        signo_dom = "positivo" if pos >= neg else "negativo"
        # Riesgo: fraccion de senales negativas (alerta real, no se diluye en el promedio)
        riesgo = round(neg / len(lista), 3) if lista else 0.0
        # Filtrar grupos triviales (ruido): requerir volumen suficiente Y
        # alguna señal real (emoción >=1.0, riesgo >0 o volumen grande).
        # Evita colar fragmentos size-3 con score=0 y riesgo=0 (ruido puro).
        if len(lista) >= umbral_coincidencias and (
            score_medio >= 1.0 or riesgo > 0.0 or len(lista) >= 5
        ):
            grupos.append({
                "categoria": cat,
                "idioma": idioma,
                "num_senales": len(lista),
                "num_negativas": neg,
                "score_medio": round(score_medio, 2),
                "signo_dominante": signo_dom,
                "riesgo": riesgo,
                "fuentes": sorted({s["fuente"] for s in lista if s["fuente"]}),
            })
    # Ordenar por número de señales desc
    grupos.sort(key=lambda g: g["num_senales"], reverse=True)
    return grupos
