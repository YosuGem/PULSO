"""Servicios completos de Noósfera."""

from __future__ import annotations

from .persistencia import (
    crear_base,
    guardar_analisis,
    guardar_evento,
    obtener_analisis_recientes,
    obtener_eventos_recientes,
)
from .pdf_dashboard import generar_pdf
from .dashboard import generar_dashboard
from .markdown_dashboard import generar_markdown
from .scheduler import marcar_ejecucion
from .bitacora import registrar_ciclo
from .evaluacion import registrar_evaluacion
from .api_minima import crear_api
from .visor_chat import _crear_app as crear_visor_chat_app
from .comparador import comparar_estructuras
from .mejoras_veo import sugerir as sugerir_mejoras_veo

import logging
try:  # noqa: E402
    from .servidor_api import app as api_app  # noqa: E402
except Exception as exc:
    logging.warning("__init__:25 fallo y se silencio: %s", exc)
    api_app = None  # type: ignore

__all__ = [
    "crear_base",
    "guardar_evento",
    "guardar_analisis",
    "obtener_eventos_recientes",
    "obtener_analisis_recientes",
    "generar_pdf",
    "generar_dashboard",
    "generar_markdown",
    "registrar_ciclo",
    "registrar_evaluacion",
    "marcar_ejecucion",
    "crear_api",
    "crear_visor_chat_app",
    "comparar_estructuras",
    "sugerir_mejoras_veo",
    "api_app",
]

