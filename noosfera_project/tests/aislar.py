"""Aísla la base cuando una suite se lanza a mano, sin pytest.

Las suites que escriben eventos (`integration_smoke`, `scoring_smoke`,
`scoring_test`) llaman a `aislar()` al principio de su bloque `__main__`.
Así, `python noosfera_project/tests/scoring_smoke.py` escribe en una base
temporal y no en la real del usuario.

Cuando esas suites se ejecutan **con pytest**, esto no hace falta: el
`conftest.py` ya aplicó el aislamiento antes de importarlas.

Uso:
    from noosfera_project.tests.aislar import aislar
    aislar()

Para probar contra la base real a propósito:
    PULSO_PRUEBAS_SIN_AISLAR=1 python noosfera_project/tests/scoring_smoke.py

La lógica vive en `aislamiento.py`, compartida con los `conftest.py`, para
que no haya dos copias que se puedan desincronizar.
"""

from __future__ import annotations

from pathlib import Path

from noosfera_project.tests.aislamiento import aislar

__all__ = ["aislar"]


def ruta_aislada() -> Path | None:
    """Atajo para quien quiera solo consultar la ruta en uso."""
    from noosfera_project.servicios import persistencia
    return persistencia.DB_PATH
