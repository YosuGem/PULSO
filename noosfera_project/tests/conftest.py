"""Aislamiento de las pruebas de esta carpeta.

La lógica está en `aislamiento.py`, compartida con el `conftest.py` de la
raíz del proyecto. Los dos hacen lo mismo; tenerlo también aquí cubre el
caso de lanzar solo esta carpeta (`pytest noosfera_project/tests/`).

La raíz del proyecto tiene su propio `conftest.py`, que cubre cualquier
fichero de prueba del árbol. Este es el respaldo para cuando se ejecuta
esta carpeta por separado.
"""

from __future__ import annotations

import pytest

from noosfera_project.tests import aislamiento

# Se aísla al cargar el fichero, es decir, antes de que pytest importe las
# suites. Si no, importarían `persistencia` con la ruta real ya resuelta y
# el redireccionamiento llegaría tarde.
_BASE_AISLADA = aislamiento.aislar()


@pytest.fixture(scope="session")
def base_aislada():
    """La ruta de la base temporal que están usando las pruebas."""
    return _BASE_AISLADA
