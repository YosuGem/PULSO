"""Comparador de estructura entre Noósfera y VEO.

Las rutas se derivan del propio fichero en lugar de usar una profundidad fija,
para que el modulo funcione independientemente de dónde esté instalado el
proyecto. VEO es un proyecto hermano opcional: si no existe, la comparación
degrada en lugar de fallar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Raíz de este proyecto: .../<proyecto>
# servicios/ -> noosfera_project/ -> <raíz>
BASE_DIR = Path(__file__).resolve().parents[2]
NOOSFERA_DIR = BASE_DIR

# VEO es opcional. Se busca en el directorio padre del proyecto.
_VEO_CANDIDATOS = [
    BASE_DIR.parent / "VEO" / "VEO_v1.0_reparado" / "veo",
    BASE_DIR.parent / "VEO",
    BASE_DIR / "VEO",
]
VEO_DIR = next((p for p in _VEO_CANDIDATOS if p.exists()), _VEO_CANDIDATOS[0])


def _ruta_salida(nombre: str) -> Path:
    ruta = NOOSFERA_DIR / "comparativas" / f"{nombre}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def comparar_estructuras() -> dict[str, Any]:
    noosfera = _resumen_estructura(NOOSFERA_DIR)
    veo = _resumen_estructura(VEO_DIR)
    resultado = {
        "noosfera": noosfera,
        "veo": veo,
        "veo_disponible": VEO_DIR.exists(),
        "diferencias": {
            "noosfera_tiene_dashboard_html": noosfera.get("tiene_dashboard_html") and not veo.get("tiene_dashboard_html"),
            "noosfera_tiene_pdf_dashboard": noosfera.get("tiene_pdf_dashboard") and not veo.get("tiene_pdf_dashboard"),
            "veo_tiene_api_servidor": veo.get("api_server") and not noosfera.get("api_server"),
            "veo_tiene_servidor_api": veo.get("api_server") and not noosfera.get("api_server"),
        },
    }
    _ruta_salida("estructuras").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def _resumen_estructura(ruta: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "tiene_persistencia_sqlite": False,
        "tiene_api_minima": False,
        "tiene_dashboard_html": False,
        "tiene_pdf_dashboard": False,
        "tiene_visor_chat": False,
        "tiene_scoring": False,
        "api_server": False,
    }
    if not ruta.exists():
        return info
    # Solo se recorre el paquete, no directorios generados ni datos.
    raiz_pkg = ruta / "noosfera_project"
    objetivo = raiz_pkg if raiz_pkg.exists() else ruta
    ignorar = {"__pycache__", ".git", "node_modules", ".venv", "venv",
               "dist", "build", ".pytest_cache", "datos", "auditorias"}
    for p in objetivo.rglob("*"):
        if any(parte in ignorar for parte in p.parts):
            continue
        nombre = p.name.lower()
        if nombre == "persistencia.py":
            info["tiene_persistencia_sqlite"] = True
        if nombre == "api_minima.py":
            info["tiene_api_minima"] = True
        if nombre == "dashboard.py":
            info["tiene_dashboard_html"] = True
        if nombre in {"pdf_dashboard.py", "markdown_dashboard.py"}:
            info["tiene_pdf_dashboard"] = True
        if nombre == "visor_chat.py":
            info["tiene_visor_chat"] = True
        if nombre == "scoring.py":
            info["tiene_scoring"] = True
        if nombre == "api_server.py":
            info["api_server"] = True
    return info
