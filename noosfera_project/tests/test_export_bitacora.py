"""Comprueba la exportacion de la bitacora de consultas.

NO EJECUTABLE: importa `registrar_consulta` de
`noosfera_project.servicios.bitacora`, pero ese modulo solo define
`registrar_ciclo`. La funcion no existe en el programa.

Verificado el 12 de octubre de 2026:
    grep '^def ' servicios/bitacora.py
      -> _cargar, _guardar, registrar_ciclo

No se ha creado la funcion porque hacerlo seria inventar comportamiento que
el autor no definio. La suite queda documentada y omitida.
"""

from __future__ import annotations

import pytest

pytest.skip(
    "Importa 'registrar_consulta', que no existe en bitacora.py "
    "(solo tiene registrar_ciclo). Defecto del programa original, "
    "pendiente de decision de diseno.",
    allow_module_level=True,
)
