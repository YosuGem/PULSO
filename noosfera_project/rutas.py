"""
Rutas portables de Noósfera (0.2.2-dev).

Para qué sirve
--------------
El programa debe correr igual en Windows y Linux, instalado con pip o
ejecutado desde el código fuente, sin que importe desde qué carpeta se
lanza. Las rutas relativas al cwd (`dashboard/index.html`) rompen en cuanto
se instala el paquete: el cwd es donde está el usuario, no donde están los
datos.

Orden de resolución de la raíz de datos:

  1. Variable de entorno `NOOSFERA_HOME` (para quien quiera elegir sitio).
  2. `~/.noosfera` (Path.home(), igual en Windows y Linux). Es el destino
     correcto para datos de usuario.
  3. Solo como último recurso, la carpeta del paquete (modo "ejecutar desde
     el código fuente", donde hoy vive la base de datos).

Nunca se usa `Path(__file__).parent` para datos escribibles cuando el
paquete está instalado: eso apuntaría a site-packages, de solo lectura.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path


def raiz_datos() -> Path:
    """Raíz donde vive la base de datos y los artefactos del programa."""
    env = os.environ.get("NOOSFERA_HOME")
    if env:
        ruta = Path(env).expanduser()
        ruta.mkdir(parents=True, exist_ok=True)
        return ruta

    hogar = Path.home() / ".noosfera"
    try:
        hogar.mkdir(parents=True, exist_ok=True)
        return hogar
    except OSError:
        # Sin home escribible: caer a la carpeta del paquete (modo fuente)
        paquete = Path(__file__).resolve().parent.parent
        paquete.mkdir(parents=True, exist_ok=True)
        return paquete


# Raíz calculada una vez (el entorno no cambia en una ejecución).
RAIZ = raiz_datos()

DB_PATH = RAIZ / "eventos.db"
LOG_PATH = RAIZ / "noosfera.log"
DASHBOARD_DIR = RAIZ / "dashboard"
INFORMES_DIR = RAIZ / "informes"


def asegurar_dirs() -> None:
    """Crea las carpetas de salida si no existen."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    INFORMES_DIR.mkdir(parents=True, exist_ok=True)


def rutas_salida() -> dict[str, str]:
    """Rutas de artefactos como strings, listas para pasar a los generadores."""
    asegurar_dirs()
    return {
        "dashboard_html": str(DASHBOARD_DIR / "index.html"),
        "dashboard_md": str(DASHBOARD_DIR / "index_dark.html"),
        "informe_pdf": str(INFORMES_DIR / "ultimo.pdf"),
    }


if __name__ == "__main__":
    print(f"Raíz de datos: {RAIZ}")
    for k, v in rutas_salida().items():
        print(f"  {k}: {v}")
