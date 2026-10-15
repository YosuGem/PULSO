"""Bitácora de ciclo Noósfera para continuidad."""

from __future__ import annotations

import logging
import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BITACORA_PATH = BASE_DIR / "bitacora_ciclos.json"
_BITACORA_LOCK = str(BITACORA_PATH) + ".lock"


def _cargar() -> dict:
    if BITACORA_PATH.exists():
        try:
            return json.loads(BITACORA_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logging.warning("bitacora:19 fallo y se silencio: %s", exc)
            pass
    return {"ciclos": []}


def _guardar(estado: dict) -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = BITACORA_PATH.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_path.replace(BITACORA_PATH)


def registrar_ciclo(etapa: str, detalle: str = "", ok: bool = True) -> None:
    fd = os.open(_BITACORA_LOCK, os.O_CREAT | os.O_RDWR)
    try:
        # fcntl solo existe en Linux y macOS. En Windows no está, así que se
        # comprueba antes de usarlo: si no está, se escribe sin bloqueo en
        # lugar de fallar con ModuleNotFoundError.
        try:
            import fcntl
        except ImportError:
            fcntl = None

        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            estado = _cargar()
            entrada = {
                "momento": datetime.utcnow().isoformat(),
                "etapa": etapa,
                "detalle": detalle,
                "ok": ok,
            }
            estado.setdefault("ciclos", []).append(entrada)
            _guardar(estado)
        finally:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
