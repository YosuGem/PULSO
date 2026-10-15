"""Scoring emocional de Pulso.

Reune en un unico modulo dos implementaciones que en el proyecto
original vivian separadas:

  * calcular_score_emocional() y calcular_confianza()
    Procedian de _dev_deteccion/version_B/. Las usa
    procesamiento/clasificador_tematico.py.

  * score_combinado() y rankear()
    Vivian en este mismo fichero. Las usan
    deteccion/hipotesis.py y tests/test_pesos_emocionales.py.

Se han reunido aqui para que noosfera_project/ sea autocontenido y
no necesite importar nada desde fuera del paquete.
"""
from __future__ import annotations

from typing import Any, Optional


"""
scoring_emocional.py — Scoring emocional con signo (versión B).

Mejoras sobre scoring.py:
- Score con signo emocional (+/-)
- Rango: -10 a +10 (negativo a positivo)
- Integración con analyzer emocional
"""
from typing import Optional, Dict, Any

def calcular_score_emocional(
    coincidencia: float = 0.5,
    recencia: float = 0.3,
    diversidad: float = 0.1,
    longitud: float = 0.1,
    emocion_bruta: Optional[float] = None,
    categoria: str = "",
) -> Dict[str, Any]:
    """
    Calcula el score emocional con signo.
    
    Args:
        coincidencia: 0-1 (cuán relevante es el evento)
        recencia: 0-1 (qué tan reciente es)
        diversidad: 0-1 (qué tan diversa es la fuente)
        longitud: 0-1 (qué tan largo es el texto)
        emocion_bruta: -1 a +1 (del analizador emocional)
        categoria: categoría del evento
    
    Returns:
        dict con: score (float), signo (+/-), nivel (muy_bajo/bajo/medio/alto/muy_alto)
    """
    # Peso base por factor
    pesos = {
        "coincidencia": 0.4,
        "recencia": 0.25,
        "diversidad": 0.15,
        "longitud": 0.2,
    }
    
    # Score base (0-1)
    score_base = (
        coincidencia * pesos["coincidencia"] +
        recencia * pesos["recencia"] +
        diversidad * pesos["diversidad"] +
        longitud * pesos["longitud"]
    )
    
    # Aplicar signo emocional
    if emocion_bruta is not None:
        # Emocion bruta: -1 (muy negativo) a +1 (muy positivo)
        # Convertimos a escala -10 a +10
        signo = 1 if emocion_bruta >= 0 else -1
        intensidad = abs(emocion_bruta)
        score_con_signo = score_base * (1 + intensidad) * signo
    else:
        # Por defecto, sin signo emocional claro
        score_con_signo = score_base
        signo = 0
    
    # Normalizar a escala -10 a +10
    score_normalizado = max(-10, min(10, score_con_signo * 10))
    
    # Determinar nivel
    if abs(score_normalizado) <= 2:
        nivel = "muy_bajo"
    elif abs(score_normalizado) <= 4:
        nivel = "bajo"
    elif abs(score_normalizado) <= 6:
        nivel = "medio"
    elif abs(score_normalizado) <= 8:
        nivel = "alto"
    else:
        nivel = "muy_alto"
    
    return {
        "score": round(score_normalizado, 3),
        "signo": "+" if score_normalizado > 0 else "-" if score_normalizado < 0 else "0",
        "nivel": nivel,
        "componentes": {
            "coincidencia": coincidencia,
            "recencia": recencia,
            "diversidad": diversidad,
            "longitud": longitud,
            "emocion_bruta": emocion_bruta,
        }
    }

def calcular_confianza(score: float, emocion: Optional[float] = None) -> float:
    """
    Calcula la confianza en la predicción basada en el score y emoción.
    
    Args:
        score: score calculado (-10 a +10)
        emocion: emoción detectada (-1 a +1)
    
    Returns:
        confianza: 0-1
    """
    # Confianza base por magnitud del score
    confianza_base = min(1.0, abs(score) / 10.0 + 0.3)
    
    # Ajustar por emoción si está disponible
    if emocion is not None:
        # Emoción clara aumenta confianza
        ajuste_emocion = 0.1 if abs(emocion) > 0.5 else 0
        confianza_base += ajuste_emocion
    
    return min(1.0, confianza_base)


PESO_COINCIDENCIA = 0.4
PESO_EMOCIONAL = 0.6


def score_combinado(resultado: dict[str, Any]) -> float:
    """Score 0-10 combinando coincidencias y emoción."""
    coinc = resultado.get("coincidencias", 0)
    # Normalizar coincidencias: asumimos max razonable ~5
    coinc_norm = min(1.0, coinc / 5.0) * 10.0
    emo = resultado.get("score_emocional", 0.0)
    comb = (coinc_norm * PESO_COINCIDENCIA) + (emo * PESO_EMOCIONAL)
    return round(min(10.0, comb), 2)


def rankear(resultados: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Añade 'score_combinado' y 'ranking' a cada resultado, ordenado."""
    for r in resultados:
        r["score_combinado"] = score_combinado(r)
    ordenados = sorted(resultados, key=lambda x: x.get("score_combinado", 0), reverse=True)
    for i, r in enumerate(ordenados, 1):
        r["ranking"] = i
    return ordenados
