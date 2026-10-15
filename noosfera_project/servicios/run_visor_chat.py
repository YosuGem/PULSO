"""Lanzador del visor chat con rutas correctas."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import uvicorn  # noqa: E402
except Exception as exc:
    print("Uvicorn no disponible:", exc)
    raise SystemExit(1)

# Evitar caché de módulo y recargar el visor tras cada cambio
import importlib  # noqa: E402

from noosfera_project.servicios import visor_chat as _visor_chat_mod

importlib.reload(_visor_chat_mod)

import logging
_app_factory = _visor_chat_mod._crear_app

# Preferir la app actualizada aunque el módulo reporte FastAPI=False en carga cacheada
if getattr(_visor_chat_mod, "FastAPI", None) is None:  # pragma: no cover
    try:
        from fastapi import FastAPI  # type: ignore  # noqa: E402
        _visor_chat_mod.FastAPI = FastAPI
    except Exception as exc:
        logging.warning("run_visor_chat:28 fallo y se silencio: %s", exc)
        pass

app = _app_factory()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
