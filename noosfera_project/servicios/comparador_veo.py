"""Comparador Noósfera vs VEO."""

from __future__ import annotations

import json
from pathlib import Path


_BASE = Path(__file__).resolve().parents[2]  # raiz NOOSFERA (.../NOOSFERA)
_NOOSFERA = _BASE
_VEO = _BASE.parent / "VEO"
_SALIDA = _NOOSFERA / "docs" / "comparativa_noosfera_vs_veo.json"


def _resumen(ruta: Path) -> dict:
    datos = {
        "existe": ruta.exists(),
        "archivos_python": 0,
        "tiene_persistencia": False,
        "tiene_scoring": False,
        "tiene_dashboard_oscuro": False,
        "tiene_pdf_dashboard": False,
        "tiene_visor_chat": False,
    }
    if not ruta.exists():
        return datos
    for p in ruta.rglob("*.py"):
        datos["archivos_python"] += 1
        nombre = p.name.lower()
        if "persistencia.py" in nombre:
            datos["tiene_persistencia"] = True
        if "scoring.py" in nombre:
            datos["tiene_scoring"] = True
        if "dashboard.py" in nombre or "markdown_dashboard.py" in nombre:
            datos["tiene_dashboard_oscuro"] = True
        if "pdf_dashboard.py" in nombre:
            datos["tiene_pdf_dashboard"] = True
        if "visor_chat.py" in nombre:
            datos["tiene_visor_chat"] = True
    return datos


def generar_comparativa() -> dict:
    noosfera = _resumen(_NOOSFERA / "noosfera_project")
    veo = _resumen(_VEO)
    resultado = {
        "noosfera": noosfera,
        "veo": veo,
        "diferencias": noosfera["archivos_python"] - veo["archivos_python"],
        "noosfera_gap_oscuro": _delta_noosfera(noosfera),
    }
    _SALIDA.parent.mkdir(parents=True, exist_ok=True)
    _SALIDA.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return resultado


def _delta_noosfera(info: dict) -> list[str]:
    delta = []
    if info["tiene_scoring"]:
        delta.append("scoring_avanzado")
    if info["tiene_dashboard_oscuro"]:
        delta.append("dashboard_oscuro")
    if info["tiene_visor_chat"]:
        delta.append("visor_chat")
    return delta or ["sin_delta_registrado"]
