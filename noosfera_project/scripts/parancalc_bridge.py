"""Puente ParanCalc ↔ Noósfera (preparado, sin ejecutar)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from noosfera_project.servicios.persistencia import crear_base, obtener_eventos_recientes


def _ruta_salida() -> Path:
    """Salida del puente, en la raíz del proyecto.

    Antes apuntaba a una ruta absoluta de la máquina del autor. Ahora se
    deriva del propio fichero para que el puente funcione en cualquier
    máquina.
    """
    raiz = Path(__file__).resolve().parents[2]
    destino = raiz / "intercambio"
    destino.mkdir(parents=True, exist_ok=True)
    return destino / "intercambio_noosfera_paran.txt"


_RUTA_SALIDA = _ruta_salida()


def exportar_eventos_para_paran(limite: int = 50) -> Path:
    """Exporta un listado simple de eventos para usar como entrada en ParanCalc."""
    crear_base()
    eventos = obtener_eventos_recientes(limite=limite)
    lineas = [
        "NOOSFERA -> PARANCALC",
        f"Generado: {datetime.utcnow().isoformat()}",
        "Formato: titulo | publicado | nivel | puntuacion",
        "",
    ]
    for ev in eventos:
        titulo = ev.get("titulo") or ""
        publicado = ev.get("publicado") or ""
        puntuacion = ev.get("puntuacion") or 0
        lineas.append(f"{titulo} | {publicado} | pendiente | {puntuacion}")
    _RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    _RUTA_SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    return _RUTA_SALIDA


if __name__ == "__main__":
    print(exportar_eventos_para_paran())
