"""Generación de hipótesis desde grupos de señales (Bloque C - Fase 3)."""
from __future__ import annotations

from typing import Any

# Plantillas de hipótesis por categoría (ES)
PLANTILLAS = {
    "bitcoin": "Señales de lenguaje colectivo apuntan a movimiento significativo en Bitcoin (score {score}, sesgo {signo})",
    "guerra_ucrania": "El conflicto en Ucrania muestra señales de intensificación/desescalada según el corpus (score {score}, sesgo {signo})",
    "deportes": "Expectativa colectiva deportiva: {score} de intensidad emocional, sesgo {signo}, {num} menciones",
    "elecciones_eeuu": "Señales electorales en EE.UU. con {num} menciones, intensidad {score}, sesgo {signo}",
    "inflacion_europa": "Presión inflacionaria en Europa detectada con score {score} y sesgo {signo}",
    "sp500": "Mercado (S&P 500) con señales de {signo} según {num} aportes, score {score}",
    "undetected": "Tema no clasificado con {num} señales y score {score}",
}


def generar_hipotesis(grupos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Genera hipótesis legibles desde grupos de señales."""
    from noosfera_project.procesamiento.scoring_emocional import score_combinado
    hipotesis: list[dict[str, Any]] = []
    for g in grupos:
        cat = g["categoria"]
        plantilla = PLANTILLAS.get(cat, PLANTILLAS["undetected"])
        texto = plantilla.format(
            score=g["score_medio"],
            signo=g["signo_dominante"],
            num=g["num_senales"],
        )
        # Score combinado (emoción + volumen) como lente adicional a 'confianza'
        sc = score_combinado({
            "coincidencias": g["num_senales"],
            "score_emocional": g["score_medio"],
        })
        hipotesis.append({
            "categoria": cat,
            "idioma": g["idioma"],
            "texto": texto,
            "score_medio": g["score_medio"],
            "score_combinado": sc,
            "num_senales": g["num_senales"],
            "num_negativas": g.get("num_negativas", 0),
            "riesgo": g.get("riesgo", 0.0),
            "signo": g["signo_dominante"],
            "fuentes": g["fuentes"],
        })
    return hipotesis
