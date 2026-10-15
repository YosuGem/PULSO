"""Cálculo de confianza por hipótesis (Bloque C - Fase 4)."""
from __future__ import annotations

from typing import Any

# Factores de confianza.
#
# El score_medio del corpus real está entre 2.3 y 4.3 sobre 10: casi no
# varía. Con PESO_SCORE=0.4 ese factor dominaba el resultado y todas las
# hipótesis quedaban en la misma horquilla (0.458-0.476), sin discriminar.
# Se rebalancea hacia volumen y diversidad de fuentes, que es lo que
# realmente distingue una señal consolidada de una anécdota.
PESO_NUM_SENALES = 0.40  # más señales = más confianza
PESO_SCORE = 0.20       # score emocional: aporta, pero no domina
PESO_DIV_FUENTES = 0.20  # más fuentes distintas = más confianza
PESO_RIESGO = 0.20      # riesgo alto (muchas señales negativas) reduce la confianza

# Escala de saturación: a cuántas señales/fuentes se considera el factor "lleno".
# Con 50 señales de máximo, una hipótesis con 10 nunca podía pasar de 0.2 en
# ese factor, por lo que la confianza quedaba estancada en "media".
# El tope se pone por encima del rango real del corpus (max observado: 125
# señales, 10 fuentes) para que el volumen sí distinga entre hipótesis.
MAX_SENALES = 125
MAX_FUENTES = 10

# Punto de partida del factor: evita que 1 señal compita como 10.
# Sin esto, el orden por confianza lo marcaba el ruido de las señales escasas.
MIN_SENALES = 3
MIN_FUENTES = 2


def _factor(valor: float, minimo: float, maximo: float) -> float:
    """Factor 0-1 con saturación logarítmica entre `minimo` y `maximo`.

    Escala logarítmica, no lineal: con saturación lineal (max=10) una
    hipótesis con 10 señales y otra con 125 daban el mismo factor, y la
    confianza dejaba de discriminar entre lo minoritario y lo masivo.
    """
    import math

    if valor <= 0:
        return 0.0
    if valor <= minimo:
        # Por debajo del mínimo, proporcional y penalizado
        return round(0.5 * (valor / minimo), 3)
    if valor >= maximo:
        return 1.0
    tramo = math.log(valor / minimo) / math.log(maximo / minimo)
    return round(0.5 + 0.5 * tramo, 3)


def calcular_confianza(hipotesis: dict[str, Any], max_senales: int = MAX_SENALES, max_fuentes: int = MAX_FUENTES) -> dict[str, Any]:
    """Devuelve confianza 0-1 y etiqueta (baja/media/alta) para una hipótesis."""
    num = hipotesis.get("num_senales", 0)
    score = hipotesis.get("score_medio", 0.0)
    fuentes = len(hipotesis.get("fuentes", []))
    riesgo = hipotesis.get("riesgo", 0.0)

    f_num = _factor(num, MIN_SENALES, max_senales)
    f_score = min(1.0, score / 10.0)
    f_fuentes = _factor(fuentes, MIN_FUENTES, max_fuentes)

    # Penalizar categoria "undetected" (ruido no clasificado)
    penalizacion = 0.5 if hipotesis.get("categoria") == "undetected" else 1.0

    confianza = (
        (f_num * PESO_NUM_SENALES + f_score * PESO_SCORE + f_fuentes * PESO_DIV_FUENTES)
        * (1 - PESO_RIESGO * riesgo)
        * penalizacion
    )
    confianza = round(confianza, 3)

    if confianza >= 0.6:
        etiqueta = "alta"
    elif confianza >= 0.35:
        etiqueta = "media"
    else:
        etiqueta = "baja"

    return {
        "confianza": confianza,
        "nivel": etiqueta,
        "factores": {
            "num_senales": round(f_num, 3),
            "score": round(f_score, 3),
            "diversidad_fuentes": round(f_fuentes, 3),
            "riesgo": round(riesgo, 3),
        },
    }
