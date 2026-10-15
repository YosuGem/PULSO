"""Validación de estructura de Noósfera."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUERIDOS = [
    ROOT / "noosfera_project",
    ROOT / "noosfera_project" / "ingesta",
    ROOT / "noosfera_project" / "procesamiento",
    ROOT / "noosfera_project" / "servicios",
    ROOT / "noosfera_project" / "scripts",
    ROOT / "noosfera_project" / "tests",
    ROOT / "dashboard",
    ROOT / "informes",
    ROOT / "docs",
]


def revisar() -> bool:
    faltan = [str(p) for p in REQUERIDOS if not p.exists()]
    if faltan:
        print("Estructura incompleta. Faltan:")
        for f in faltan:
            print(f"- {f}")
        return False
    print("Estructura completa.")
    return True


if __name__ == "__main__":
    sys.exit(0 if revisar() else 1)
