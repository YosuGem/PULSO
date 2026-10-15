"""Hoja de ruta de Noósfera."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from noosfera_project.ingesta.canales import FEED_URLS, EMERGENTE_KEYWORDS
from noosfera_project.ingesta.rss import ingestar_fuentes
from noosfera_project.procesamiento.senal import detectar, extraer_contexto
from noosfera_project.servicios.persistencia import (
    crear_base,
    guardar_analisis,
    guardar_evento,
    obtener_eventos_recientes,
)

BASE_DIR = Path(__file__).resolve().parent


def ciclo_basico() -> None:
    crear_base()
    if not FEED_URLS:
        print("Sin fuentes configuradas (FEED_URLS vacio). No hay eventos que ingerir.")
        return
    procesadas = ingestar_fuentes()
    eventos = obtener_eventos_recientes(limite=5)
    print(f"Fuentes procesadas: {procesadas.get('fuentes_procesadas', 0)}")
    print(f"Eventos recientes: {len(eventos)}")


if __name__ == "__main__":
    ciclo_basico()
