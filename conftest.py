"""Aislamiento de las pruebas para todo el proyecto.

Vive en la RAÍZ a propósito: así cubre cualquier fichero de prueba del
árbol, no solo los de `noosfera_project/tests/`. Un `conftest.py` en la
raíz se carga antes de que pytest importe ningún test de cualquier
subcarpeta.

La lógica está en `noosfera_project/tests/aislamiento.py`, compartida con
el `conftest.py` de esa carpeta, para que no haya dos copias que se puedan
desincronizar.

Con esto, un fichero de prueba nuevo —en la raíz, en `docs/`, donde sea—
que llame a `guardar_evento` sin preocuparse del aislamiento escribe en la
base temporal, no en la real.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from noosfera_project.tests import aislamiento  # noqa: E402

# Se aísla al cargar el fichero, es decir, antes de que pytest importe los
# tests. Si no, importarían `persistencia` con la ruta real ya resuelta y
# el redireccionamiento llegaría tarde.
_BASE_AISLADA = aislamiento.aislar()


@pytest.fixture(scope="session")
def base_aislada():
    """La ruta de la base temporal que están usando las pruebas."""
    return _BASE_AISLADA
