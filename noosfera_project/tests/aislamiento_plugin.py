"""Plugin de pytest que aísla la base de datos en TODA ejecución.

POR QUÉ EXISTE ESTE FICHERO
    Un `conftest.py` solo se aplica a los tests que están **dentro** de su
    carpeta o por debajo. Un fichero de prueba que viva fuera del árbol
    del proyecto —en un temporal, en otra carpeta— no lo carga, y entonces
    escribe en la base REAL. Se comprobó: un test en `%TEMP%` dejó la ruta
    apuntando a `noosfera_project/eventos.db`.

    Un plugin registrado con el punto de entrada `pytest11` se carga
    **siempre**, esté donde esté el fichero de prueba. Es la única forma
    de cubrir esa vía de escape.

CÓMO SE ACTIVA
    El paquete declara en `pyproject.toml`:

        [project.entry-points.pytest11]
        pulso_aislamiento = "noosfera_project.tests.aislamiento:plugin"

    Con eso instalado (`pip install -e .`), cualquier `pytest` que se
    ejecute en este entorno arranca aislado.

    Si el proyecto **no** está instalado como paquete, el plugin no se
    registra y el aislamiento lo siguen dando los dos `conftest.py`
    (raíz y `noosfera_project/tests/`), que cubren los tests de dentro
    del árbol — que es donde vive la batería del proyecto.

QUÉ HACE
    Redirige `persistencia.DB_PATH` (y sus alias) a una base temporal,
    antes de que se importe ningún test. No toca el programa: es solo
    para pruebas.

ESCAPE
    `PULSO_PRUEBAS_SIN_AISLAR=1` desactiva el aislamiento.
"""

from __future__ import annotations

from noosfera_project.tests import aislamiento

# Se aísla al importar el plugin, es decir, en el arranque de pytest y
# antes de que cualquier fichero de prueba pueda importar `persistencia`.
_BASE_AISLADA = aislamiento.aislar()


def pytest_configure(config):
    """Deja rastro en la cabecera de pytest de dónde está la base."""
    if _BASE_AISLADA is not None:
        print(f"\n  pruebas aisladas — base temporal: {_BASE_AISLADA}\n")


# pytest reconoce el plugin por este nombre de módulo.
plugin = _BASE_AISLADA
