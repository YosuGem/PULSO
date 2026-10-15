"""Comprobador de salud de Noósfera."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def salud() -> dict:
    estado = {
        "carpetas_ok": True,
        "feedparser_ok": False,
        "cycle_ok": False,
    }
    req = [
        ROOT / "dashboard",
        ROOT / "informes",
        ROOT / "docs",
        ROOT / "dist",
    ]
    for p in req:
        if not p.exists():
            estado["carpetas_ok"] = False
    try:
        import feedparser  # noqa: E402
        estado["feedparser_ok"] = True
    except Exception:
        estado["feedparser_ok"] = False
    cycle_indicators = [
        ROOT / "eventos.db",
        ROOT / "dashboard" / "index_dark.html",
        ROOT / "noosfera.log",
    ]
    estado["cycle_ok"] = all(p.exists() for p in cycle_indicators)
    return estado


if __name__ == "__main__":
    s = salud()
    print(s)
    sys.exit(0 if all(s.values()) else 2)
