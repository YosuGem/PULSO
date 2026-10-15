"""Motor de aprendizaje automático simple para Noósfera."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_RUTA = Path(__file__).resolve().parent / "ml_pesos.json"


import logging
def cargar_pesos() -> dict[str, float]:
    if _RUTA.exists():
        try:
            datos = json.loads(_RUTA.read_text(encoding="utf-8"))
            if "pesos" in datos:
                return datos["pesos"]
        except Exception as exc:
            logging.warning("ml_pesos:19 fallo y se silencio: %s", exc)
            pass
    return {
        "coincidencia": 0.45,
        "recencia": 0.25,
        "diversidad": 0.15,
        "longitud": 0.15,
    }


def guardar_pesos(pesos: dict[str, float]) -> None:
    _RUTA.parent.mkdir(parents=True, exist_ok=True)
    _RUTA.write_text(json.dumps({"pesos": pesos}, ensure_ascii=False, indent=2), encoding="utf-8")


def ajustar_pesos_por_acierto(feedback: dict[str, float], tasa: float = 0.05) -> dict[str, float]:
    pesos = cargar_pesos()
    for clave, delta in feedback.items():
        if clave in pesos:
            pesos[clave] = max(0.05, min(0.8, pesos[clave] + tasa * delta))
    guardar_pesos(pesos)
    return pesos
