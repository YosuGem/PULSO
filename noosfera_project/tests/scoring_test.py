"""Scoring mejorado y validación."""

from __future__ import annotations

from noosfera_project.servicios.persistencia import guardar_evento, obtener_eventos_recientes
from noosfera_project.procesamiento.scoring import calcular_score


CASOS = [
    {
        "titulo": "Crisis económica, protestas y riesgo de recesión global",
        "categorias": "economia,protesta",
        "cuerpo": "",
        "id": 1,
    },
    {
        "titulo": "Nuevo descubrimiento modesto sin señales emergentes",
        "categorias": "ciencia",
        "cuerpo": "",
        "id": 2,
    },
    {
        "titulo": "Erupción volcánica, alerta sanitaria y desastre en la isla",
        "categorias": "geofisica,salud",
        "cuerpo": "",
        "id": 3,
    },
]


def ejecutar() -> list[dict]:
    guardados = []
    for caso in CASOS:
        guardados.append(guardar_evento(caso))
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
