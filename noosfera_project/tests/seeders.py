"""Seeders de prueba para Noósfera."""

from __future__ import annotations

from datetime import datetime, timedelta

from noosfera_project.servicios.persistencia import guardar_evento


CASOS_PRUEBA = [
    {
        "fuente": "prueba",
        "titulo": "Crisis económica y protestas en Europa con riesgo de recesión",
        "enlace": "https://prueba.local/crisis-europa",
        "publicado": datetime.utcnow().isoformat(),
        "categorias": "economia,protesta",
        "puntuacion": 0.0,
        "procesado": 0,
    },
    {
        "fuente": "prueba",
        "titulo": "Terremoto de magnitud 6.8 y tsunami en isla del Pacífico",
        "enlace": "https://prueba.local/terremoto-pacifico",
        "publicado": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
        "categorias": "geofisica,tsunami",
        "puntuacion": 0.0,
        "procesado": 0,
    },
]


def cargar() -> list[int]:
    ids = []
    for caso in CASOS_PRUEBA:
        ids.append(guardar_evento(caso))
    return ids
