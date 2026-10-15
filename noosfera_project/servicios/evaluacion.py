"""Evaluación básica de Noósfera para medir aciertos."""

from __future__ import annotations

import logging
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
EVALUACION_PATH = BASE_DIR / "evaluacion.json"


def _cargar() -> dict:
    if EVALUACION_PATH.exists():
        try:
            return json.loads(EVALUACION_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logging.warning("evaluacion:17 fallo y se silencio: %s", exc)
            pass
    return {"ciclos": []}


def _guardar(estado: dict) -> None:
    EVALUACION_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def registrar_evaluacion(eventos_totales: int, eventos_alto: int, eventos_medio: int) -> dict:
    estado = _cargar()
    entrada = {
        "momento": datetime.utcnow().isoformat(),
        "eventos_totales": eventos_totales,
        "eventos_alto": eventos_alto,
        "eventos_medio": eventos_medio,
        "tasa_alto": round((eventos_alto / eventos_totales), 4) if eventos_totales else 0.0,
    }
    estado.setdefault("ciclos", []).append(entrada)
    _guardar(estado)
    return entrada
