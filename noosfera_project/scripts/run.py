"""Script de ejecucion principal ciclica."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from noosfera_project.servicios.persistencia import crear_base  # noqa: E402


def main() -> int:
    crear_base()
    print("Noosfera lista. Proximamente: ingesta y analisis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
