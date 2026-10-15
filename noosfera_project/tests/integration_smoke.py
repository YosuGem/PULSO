"""Modo pruebas y empaquetado rápido para Noósfera."""

from __future__ import annotations

import sys
from pathlib import Path

# La raíz del proyecto tiene que estar en sys.path para poder importar el
# paquete. Sin esto, ejecutar este fichero directamente falla con
# ModuleNotFoundError salvo que PYTHONPATH apunte a la raíz.
_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from noosfera_project.servicios.persistencia import crear_base, guardar_evento, obtener_eventos_recientes
from noosfera_project.procesamiento.scoring import calcular_score
from noosfera_project.servicios.comparador import comparar_estructuras
from noosfera_project.servicios.mejoras_veo import sugerir
from noosfera_project.ingesta.canales import FEED_URLS


BASE_DIR = Path(__file__).resolve().parents[1]


def ejecutar() -> dict:
    crear_base()
    salida = {
        "eventos_guardados": 0,
        "comparativa": None,
        "mejoras_veo": None,
        "feed_urls": FEED_URLS,
    }
    for url in FEED_URLS[:2]:
        guardar_evento({
            "fuente": url,
            "titulo": f"Feed objetivo: {url}",
            "enlace": url,
            "publicado": "",
            "categorias": "objetivo",
            "puntuacion": 0.0,
            "procesado": 0,
        })
        salida["eventos_guardados"] += 1
    eventos = obtener_eventos_recientes(limite=20)
    salida["top_scores"] = []
    for ev in eventos:
        score = calcular_score(ev)
        salida["top_scores"].append({
            "titulo": ev.get("titulo"),
            "nivel": score.nivel,
            "puntuacion": score.puntuacion,
        })
    salida["comparativa"] = comparar_estructuras()
    salida["mejoras_veo"] = str(sugerir())
    return salida


if __name__ == "__main__":
    from pprint import pprint
    from noosfera_project.tests.aislar import aislar
    aislar()
    pprint(ejecutar())
