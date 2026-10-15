"""Suite mínima de pruebas corregida para imports desde tests/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from noosfera_project.procesamiento.scoring import calcular_score  # noqa: E402
from noosfera_project.procesamiento.detector import evaluar  # noqa: E402


CASOS_SCORE = [
    (
        {
            "titulo": "Crisis y protestas globales",
            "publicado": "2026-06-16T12:00:00",
            "fuente": "rss",
            "categorias": "protesta,crisis",
        },
        0.4,
    ),
    (
        {
            "titulo": "Nada relevante",
            "publicado": "2026-06-16T12:00:00",
            "fuente": "rss",
            "categorias": "tecnologia",
        },
        0.1,
    ),
]


def ejecutar() -> bool:
    errores = 0
    print("=== Score suite ===")
    for entrada, esperado_min in CASOS_SCORE:
        score = calcular_score(entrada)
        if score.puntuacion < esperado_min:
            print(f"FAIL: {entrada['titulo']} -> {score.puntuacion}")
            errores += 1
        else:
            print(f"OK: {entrada['titulo']} -> {score.puntuacion}")

    print("=== Detector evaluar ===")
    demo = evaluar("Protestas y crisis en la capital por tercera jornada")
    print("coincidencias:", demo.get("coincidencias"))
    if not demo.get("coincidencias"):
        errores += 1

    if errores:
        print(f"Pruebas fallidas: {errores}")
        return False
    print("Pruebas OK")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar() else 1)
