"""Scheduler programado para ciclos Noósfera."""

from __future__ import annotations

import logging
import json
from datetime import datetime
from pathlib import Path

try:
    from crontab import CronTab  # type: ignore
    CRONTAB_OK = True
except Exception as exc:
    logging.warning("scheduler:12 fallo y se silencio: %s", exc)
    CRONTAB_OK = False


BASE_DIR = Path(__file__).resolve().parents[1]
ESTADO_PATH = BASE_DIR / "scheduler_estado.json"


def _cargar_estado() -> dict:
    if ESTADO_PATH.exists():
        try:
            return json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logging.warning("scheduler:24 fallo y se silencio: %s", exc)
            pass
    return {"proxima_ejecucion": None, "ultima_ejecucion": None, "errores": []}


def _guardar_estado(estado: dict) -> None:
    ESTADO_PATH.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def marcar_ejecucion(ok: bool, detalle: str = "") -> None:
    estado = _cargar_estado()
    estado["ultima_ejecucion"] = datetime.utcnow().isoformat()
    if ok:
        estado.setdefault("errores", [])
    else:
        errores = estado.setdefault("errores", [])
        errores.append({"momento": datetime.utcnow().isoformat(), "detalle": detalle})
    _guardar_estado(estado)
