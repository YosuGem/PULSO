"""Noósfera: núcleo y punto de entrada principal."""

from __future__ import annotations

import datetime
from pathlib import Path

from noosfera_project.servicios.persistencia import crear_base, guardar_evento, guardar_analisis, obtener_eventos_recientes
from noosfera_project.procesamiento.senal import detectar, extraer_contexto
from noosfera_project.ingesta.canales import FEED_URLS, EMERGENTE_KEYWORDS


BASE_DIR = Path(__file__).resolve().parent


def ciclo_basico() -> None:
    crear_base()
    ahora = datetime.datetime.utcnow().isoformat()
    marcas = [
        {
            "fuente": url,
            "titulo": f"Feed sin procesar ahora: {url}",
            "enlace": url,
            "publicado": ahora,
            "categorias": "pendiente",
            "puntuacion": 0.0,
            "procesado": 0,
        }
        for url in FEED_URLS[:2]
    ]
    ids_eventos = [guardar_evento(m) for m in marcas]
    for idx, ev in enumerate(marcas):
        texto = ev.get("titulo", "")
        hallazgo = detectar(texto)
        analisis = {
            "evento_id": ids_eventos[idx],
            "resumen": extraer_contexto(texto),
            "categorias_sugeridas": ",".join(EMERGENTE_KEYWORDS[:3]),
            "detectado": 1 if hallazgo["coincidencias"] else 0,
        }
        guardar_analisis(analisis)
    eventos = obtener_eventos_recientes(limite=5)
    print(f"Eventos guardados: {len(eventos)}")


if __name__ == "__main__":
    ciclo_basico()
