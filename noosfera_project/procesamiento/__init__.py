"""Procesamiento: detección, scoring y análisis."""

from __future__ import annotations

from .detector import evaluar as detectar_evento_emergente, extraer_ubicacion
from .senal import detectar, extraer_contexto
from .scoring import Score as EventoScore, calcular_score
from .analisis import resumir_eventos

__all__ = [
    "detectar_evento_emergente",
    "extraer_ubicacion",
    "detectar",
    "extraer_contexto",
    "EventoScore",
    "calcular_score",
    "resumir_eventos",
]
