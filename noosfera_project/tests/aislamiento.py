"""Aísla la base de datos de las pruebas, para que ninguna escriba en la real.

LO ALCANZAN DOS FICHEROS
    `conftest.py` en la RAÍZ del proyecto cubre **cualquier** fichero de
    prueba del árbol. El de `noosfera_project/tests/` cubre además el caso
    de lanzar las pruebas de esa carpeta por sí solas. Los dos importan
    este módulo, así que la lógica vive en un solo sitio.

EL PROBLEMA
    `persistencia.py` calcula la ruta de la base UNA VEZ, al importar el
    módulo, y la guarda en la constante `DB_PATH`:

        DB_PATH = Path(__file__).resolve().parents[1] / "eventos.db"

    Las funciones `crear_base`, `guardar_evento` y `obtener_eventos_recientes`
    usan siempre esa constante. No aceptan ruta como parámetro. Sin
    aislamiento, cualquier prueba que guarde un evento escribe en la base
    REAL del proyecto, en la carpeta del usuario.

QUÉ HACE
    1. Crea una base temporal vacía.
    2. Apunta `persistencia.DB_PATH` a ella.
    3. Apunta también los módulos que capturaron la ruta por valor,
       incluidos los alias (`api_fuentes` la guarda en DB_PATH y DB_FUENTES).

NO TOCA EL PROGRAMA
    Es un cambio de **pruebas**. `persistencia.py` no se modifica: quien
    use el programa normalmente sigue escribiendo donde siempre.

ESCAPE
    `PULSO_PRUEBAS_SIN_AISLAR=1` desactiva el aislamiento, para cuando
    haga falta depurar contra datos reales a propósito. El test
    `test_la_variable_de_escape_no_esta_activa_en_el_entorno` vigila que
    no esté puesta por descuido.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Raíz del proyecto (dos niveles arriba de noosfera_project/tests/).
RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# Módulos que importaron DB_PATH por valor y hay que reconducir también.
_MODULOS_CON_RUTA = (
    "noosfera_project.servicios.historico_analisis",
    "noosfera_project.servicios.alerta_temprana",
    "noosfera_project.servicios.api_fuentes",
    "noosfera_project.servicios.diversidad_fuentes",
    "noosfera_project.procesamiento.consulta_lenguaje",
    "noosfera_project.rutas",
)

# Nombres alternativos de la misma ruta en esos módulos.
# api_fuentes la guarda en DB_FUENTES además de en DB_PATH: redirigir solo
# uno deja el otro apuntando a la base real.
_ALIAS_DE_RUTA = ("DB_FUENTES",)


def sin_aislar() -> bool:
    """True si alguien pidió expresamente probar contra la base real."""
    return os.environ.get("PULSO_PRUEBAS_SIN_AISLAR") == "1"


def redirigir(nueva: Path) -> list[str]:
    """Apunta a `nueva` todas las rutas conocidas de la base.

    Devuelve la lista de lo que se ha redirigido, para poder comprobar
    después que no queda nada apuntando a la base real.
    """
    from noosfera_project.servicios import persistencia
    persistencia.DB_PATH = nueva
    tocados = ["persistencia.DB_PATH"]

    for nombre in _MODULOS_CON_RUTA:
        try:
            modulo = __import__(nombre, fromlist=["DB_PATH"])
        except Exception:
            continue
        for atributo in ("DB_PATH",) + _ALIAS_DE_RUTA:
            if hasattr(modulo, atributo):
                setattr(modulo, atributo, nueva)
                tocados.append(f"{nombre}.{atributo}")
    return tocados


def rutas_que_apuntan_a(real: Path) -> list[str]:
    """Rutas de módulos ya importados que siguen apuntando a `real`.

    Es la comprobación inversa y la que importa: no pregunta «¿he
    redirigido?» sino «¿queda algo apuntando a la base real?». Recorre
    `sys.modules`, así que también cubre módulos que se añadan en el
    futuro.
    """
    fugas = []
    for nombre_modulo, modulo in sorted(sys.modules.items()):
        if not nombre_modulo.startswith("noosfera_project"):
            continue
        for atributo in ("DB_PATH",) + _ALIAS_DE_RUTA:
            valor = getattr(modulo, atributo, None)
            if isinstance(valor, Path) and valor == real:
                fugas.append(f"{nombre_modulo}.{atributo}")
    return fugas


def aislar() -> Path | None:
    """Crea la base temporal y redirige todo hacia ella.

    Devuelve la ruta de la base aislada, o None si se pidió no aislar.
    """
    if sin_aislar():
        return None

    from noosfera_project.servicios import persistencia
    real = persistencia.DB_PATH

    tmp = Path(tempfile.mkdtemp(prefix="pulso_pruebas_"))
    os.environ["NOOSFERA_HOME"] = str(tmp)
    redirigir(tmp / "eventos.db")
    # La base se crea vacía: algunas suites la dan por existente.
    persistencia.crear_base()

    fugas = rutas_que_apuntan_a(real)
    if fugas:
        print(f"\n⚠️  AVISO: estas rutas siguen apuntando a la base real: "
              f"{fugas}\n    Las pruebas podrían escribir en ella.\n",
              file=sys.stderr)
    return persistencia.DB_PATH
