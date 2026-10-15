"""Mejoras y parches sugeridos para VEO."""

from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
VEO_DIR = BASE_DIR / "PULSO" / "VEO" / "VEO_v1.0_reparado" / "veo"
SALIDA = BASE_DIR / "NOOSFERA" / "comparativas" / "veo_mejoras_sugeridas.txt"


MEJORAS = [
    "Hipótesis persistentes en API antes que en CLI.",
    "Validación dual configurable por umbrales.",
    "Dashboard HTML oscuro accesible por `/`.",
    "Log JSON por ciclo en lugar de salida plana.",
    "CLI con grupo `ciclo` para ingesta + informe.",
    "Scoring por recencia y diversidad de fuentes.",
    "Visor chat oscuro como interfaz alternativa.",
]


def sugerir() -> Path:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    lineas = [f"Mejoras sugeridas para VEO ({VEO_DIR})\n"]
    for i, m in enumerate(MEJORAS, start=1):
        lineas.append(f"{i}. {m}")
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    return SALIDA
