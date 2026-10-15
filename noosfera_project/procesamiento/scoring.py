"""Scoring avanzado con pesos aprendidos automáticamente."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noosfera_project.servicios.ml_pesos import cargar_pesos


@dataclass
class Score:
    puntuacion: float = 0.0
    nivel: str = "bajo"
    contexto: str = ""
    factores: dict = None  # type: ignore

    def __post_init__(self) -> None:
        if self.factores is None:
            self.factores = {}


import logging
def calcular_score(evento: dict, ahora: datetime | None = None) -> Score:
    pesos = cargar_pesos()
    titulo = evento.get("titulo") or ""
    categorias = evento.get("categorias") or ""
    publicado = evento.get("publicado") or ""
    texto = (evento.get("texto") or "")
    combinado = f"{titulo} {categorias} {texto}".lower()

    factores: dict[str, float] = {}

    pesos_categorias = pesos.get("categorias", {}) or {}
    for token, peso in pesos_categorias.items():
        if token in combinado:
            factores[f"cat_{token}"] = float(peso)

    recencia = _peso_recencia(publicado, ahora)
    diversidad = 0.1
    longitud = min(len((titulo + " " + texto).split()) / 20.0, 1.0)
    carga_emocional = min(len(factores) / 6.0, 1.0)

    score = 0.0
    score += pesos.get("coincidencia", 0.45) * sum(factores.values())
    score += pesos.get("recencia", 0.25) * recencia
    score += pesos.get("diversidad", 0.15) * diversidad
    score += pesos.get("longitud", 0.15) * longitud
    score += 0.10 * carga_emocional

    nivel = "bajo"
    if score >= 0.75:
        nivel = "alto"
    elif score >= 0.50:
        nivel = "medio"

    return Score(
        puntuacion=round(score, 4),
        nivel=nivel,
        contexto=_generar_contexto(factores),
        factores=factores,
    )


def _peso_recencia(publicado: str, ahora: datetime | None = None) -> float:
    try:
        pub = datetime.fromisoformat(publicado.replace("Z", "+00:00"))
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        ahora = ahora or datetime.now(timezone.utc)
        horas = max((ahora - pub).total_seconds() / 3600.0, 0.0)
        if horas <= 72:
            return 1.0
        if horas <= 168:
            return 0.7
        if horas <= 720:
            return 0.4
        return 0.1
    except Exception as exc:
        logging.warning("scoring:80 fallo y se silencio: %s", exc)
        return 0.2


def _generar_contexto(factores: dict) -> str:
    if not factores:
        return "Sin señales destacadas."
    return " | ".join(sorted(factores.keys()))
