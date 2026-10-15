"""Analizador avanzado de eventos emergentes."""

from __future__ import annotations

import logging
from typing import Any


def _score_ev(ev):
    try:
        from noosfera_project.procesamiento.scoring import calcular_score
        return calcular_score(ev)
    except Exception as exc:
        logging.warning("analisis:12 fallo y se silencio: %s", exc)
        class _Fallback:
            puntuacion = 0.0
            nivel = "bajo"
            factores = {}
        return _Fallback()


def resumir_eventos(eventos: list[dict[str, Any]]) -> dict[str, Any]:
    resumen = {
        "total": len(eventos),
        "alto": 0,
        "medio": 0,
        "bajo": 0,
        "top": [],
        "factores_frecuentes": {},
    }
    puntuaciones = []
    for ev in eventos:
        score = _score_ev(ev)
        nivel = score.nivel
        if nivel == "alto":
            resumen["alto"] += 1
        elif nivel == "medio":
            resumen["medio"] += 1
        else:
            resumen["bajo"] += 1
        resumen["top"].append(
            {
                "id": ev.get("id"),
                "titulo": ev.get("titulo"),
                "puntuacion": score.puntuacion,
                "nivel": nivel,
            }
        )
        puntuaciones.append(score.puntuacion)
        for factor, valor in score.factores.items():
            resumen["factores_frecuentes"][factor] = (
                resumen["factores_frecuentes"].get(factor, 0.0) + valor
            )
    resumen["top"] = sorted(resumen["top"], key=lambda x: x["puntuacion"], reverse=True)[:20]
    resumen["media"] = round(sum(puntuaciones) / len(puntuaciones), 4) if puntuaciones else 0.0
    return resumen
