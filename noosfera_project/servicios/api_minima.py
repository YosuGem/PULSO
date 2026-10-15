"""API REST mínima de Noósfera."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from noosfera_project.servicios.persistencia import (
    crear_base_lenguaje_colectivo,
    obtener_textos_recientes,
)
from noosfera_project.procesamiento.normalizacion import tokens
from noosfera_project.procesamiento.predictor import senales_emergentes

import logging
try:
    from fastapi import FastAPI  # type: ignore
    from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore
    _FastAPIAvailable = True
except Exception as exc:
    logging.warning("api_minima:20 fallo y se silencio: %s", exc)
    FastAPI = None  # type: ignore
    _FastAPIAvailable = False
    JSONResponse = None  # type: ignore
    HTMLResponse = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PATH = ROOT / "dashboard/index_dark.html"


def _serializable(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: getattr(obj, k) for k in obj.__dataclass_fields__}
    return obj


def crear_api() -> Any:
    if FastAPI is None:
        raise RuntimeError("FastAPI/Starlette no disponibles.")

    app = FastAPI(title="Noósfera API", version="0.2.0")

    @app.get("/health")
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @app.get("/")
    def home() -> JSONResponse:
        if DASHBOARD_PATH.exists():
            return JSONResponse({"dashboard": str(DASHBOARD_PATH), "html": DASHBOARD_PATH.read_text(encoding="utf-8")})
        return JSONResponse({"error": "No hay dashboard generado aún."})

    @app.get("/api/senales")
    def api_senales(horizonte: int = 30, limite: int = 100) -> JSONResponse:
        docs = obtener_textos_recientes(limite=limite)
        enriquecidos = []
        for d in docs:
            texto = d.get("texto") or ""
            d["_tokens"] = tokens(texto)
            enriquecidos.append(d)
        senales = senales_emergentes(enriquecidos, horizonte_dias=max(horizonte, 1))
        return JSONResponse([_serializable(s) for s in senales])

    @app.get("/api/exportar_json")
    def api_exportar_json(limite: int = 500) -> JSONResponse:
        docs = obtener_textos_recientes(limite=limite)
        ruta = ROOT / "exportaciones" / "lenguaje_colectivo_export.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return JSONResponse({"ok": True, "archivo": str(ruta), "documentos": len(docs)})

    return app
