"""Pruebas rápidas de Noósfera.

AISLAMIENTO: este fichero escribe eventos. Cuando se ejecuta con pytest,
`tests/conftest.py` redirige la base a un temporal. Cuando se lanza a mano
(`python tests/scoring_smoke.py`) conftest no interviene, así que el
aislamiento se aplica aquí abajo, en el bloque __main__.

Si necesitas probar contra la base real a propósito, define
PULSO_PRUEBAS_SIN_AISLAR=1.
"""

from __future__ import annotations

from noosfera_project.servicios.persistencia import crear_base, guardar_evento, obtener_eventos_recientes
from noosfera_project.procesamiento.scoring import calcular_score


CASOS = [
    {
        "fuente": "prueba",
        "titulo": "Crisis económica, protestas y riesgo de recesión global",
        "enlace": "https://prueba.local/crisis",
        "publicado": "2026-06-14T10:00:00",
        "categorias": "economia,protesta",
        "puntuacion": 0.0,
        "procesado": 0,
    },
    {
        "fuente": "prueba",
        "titulo": "Nuevo descubrimiento modesto sin señales emergentes",
        "enlace": "https://prueba.local/ciencia",
        "publicado": "2026-06-14T09:00:00",
        "categorias": "ciencia",
        "puntuacion": 0.0,
        "procesado": 0,
    },
    {
        "fuente": "prueba",
        "titulo": "Erupción volcánica, alerta sanitaria y desastre en la isla",
        "enlace": "https://prueba.local/erupcion",
        "publicado": "2026-06-14T08:00:00",
        "categorias": "geofisica,salud",
        "puntuacion": 0.0,
        "procesado": 0,
    },
]


def ejecutar() -> list[dict]:
    crear_base()
    ids = [guardar_evento(c) for c in CASOS]
    eventos = obtener_eventos_recientes(limite=10)
    resultados = []
    for ev in eventos:
        score = calcular_score(ev)
        resultados.append(
            {
                "evento_id": ev.get("id"),
                "titulo": ev.get("titulo"),
                "puntuacion": score.puntuacion,
                "nivel": score.nivel,
                "contexto": score.contexto,
                "factores": score.factores,
            }
        )
    return resultados


if __name__ == "__main__":
    from pprint import pprint
    from noosfera_project.tests.aislar import aislar
    aislar()
    pprint(ejecutar())
