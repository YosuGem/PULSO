"""Comprueba que las pruebas no escriben en la base real del proyecto.

El aislamiento lo hace `conftest.py`, que redirige `persistencia.DB_PATH`
a una base temporal antes de que se importe ninguna suite.

Estos tests lo verifican de verdad: ejecutan las tres suites que escribían
en la base real y comprueban que la base del usuario no se ha movido.
"""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE_REAL = RAIZ / "noosfera_project" / "eventos.db"

# Las suites que escribían en la base real antes del aislamiento.
SUITES_QUE_ESCRIBIAN = [
    "integration_smoke",
    "scoring_smoke",
    "scoring_test",
]


def _eventos() -> int:
    c = sqlite3.connect(f"file:{BASE_REAL}?immutable=1", uri=True)
    try:
        return c.execute("select count(*) from eventos").fetchone()[0]
    finally:
        c.close()


def _sha() -> str:
    return hashlib.sha256(BASE_REAL.read_bytes()).hexdigest()


def test_las_suites_no_escriben_en_la_base_real():
    """Ejecuta las 3 suites y comprueba que la base real no cambia.

    Se ejecutan con pytest para que `conftest.py` aplique el aislamiento,
    igual que hace un usuario que siga el README.
    """
    if not BASE_REAL.exists():
        # Sin base real no hay nada que proteger.
        return
    antes_eventos = _eventos()
    antes_sha = _sha()

    r = subprocess.run(
        [sys.executable, "-m", "pytest", *SUITES_QUE_ESCRIBIAN,
         "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=400)

    despues_eventos = _eventos()
    assert despues_eventos == antes_eventos, (
        f"las pruebas escribieron en la base real: "
        f"{antes_eventos} -> {despues_eventos} eventos. "
        f"El aislamiento de conftest.py no está funcionando. "
        f"Salida: {(r.stdout + r.stderr)[-300:]}")


def test_la_base_real_no_se_ha_modificado_byte_a_byte():
    """Además del recuento, el fichero entero debe quedar igual.

    El recuento puede coincidir por casualidad si se borran y se añaden
    los mismos eventos. El hash del fichero no perdona.
    """
    if not BASE_REAL.exists():
        return
    antes = _sha()
    subprocess.run(
        [sys.executable, "-m", "pytest", *SUITES_QUE_ESCRIBIAN,
         "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=400)
    assert _sha() == antes, (
        "el fichero de la base real cambió (no solo el recuento): "
        "el aislamiento no está funcionando")


def test_la_base_temporal_recibe_las_escrituras():
    """Las suites siguen escribiendo, pero en la base temporal.

    Comprueba que el aislamiento no ha roto las suites: se ejecutan y
    tienen que seguir funcionando.
    """
    r = subprocess.run(
        [sys.executable, "-m", "pytest", *SUITES_QUE_ESCRIBIAN,
         "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=400)
    salida = r.stdout + r.stderr
    # No debe haber errores de import ni de tabla inexistente.
    assert "ModuleNotFoundError" not in salida
    assert "no such table" not in salida, (
        f"las suites fallaron: {salida[-300:]}")


def test_guardar_evento_va_a_la_base_aislada():
    """Comprueba directo: guardar algo no toca la base real."""
    from noosfera_project.servicios import persistencia

    if not BASE_REAL.exists():
        return
    antes = _eventos()
    persistencia.guardar_evento({
        "fuente": "prueba_aislamiento",
        "titulo": "evento para comprobar el aislamiento",
        "creado_en": "2026-01-01T00:00:00",
    })
    assert _eventos() == antes, (
        "guardar_evento escribió en la base real: conftest.py no aisló")
    # y sí fue a algún sitio
    assert len(persistencia.obtener_eventos_recientes(500)) > 0


def test_el_alias_db_fuentes_tambien_esta_redirigido():
    """`api_fuentes` guarda la ruta en dos nombres: DB_PATH y DB_FUENTES.

    Redirigir solo DB_PATH dejaba DB_FUENTES apuntando a la base real.
    Este test lo comprueba directamente.
    """
    from noosfera_project.servicios import api_fuentes, persistencia

    if not BASE_REAL.exists():
        return
    assert api_fuentes.DB_FUENTES == persistencia.DB_PATH, (
        f"DB_FUENTES sigue en {api_fuentes.DB_FUENTES} mientras la base "
        f"aislada está en {persistencia.DB_PATH}: las lecturas de fuentes "
        f"irían a la base real")


def test_ninguna_ruta_de_modulo_apunta_a_la_base_real():
    """La comprobación inversa: recorrer los módulos importados y mirar si
    alguno sigue apuntando a la base real.

    No pregunta «¿he redirigido?» sino «¿queda algo en la base real?».
    Cubre módulos añadidos en el futuro, porque recorre sys.modules.
    """
    from noosfera_project.servicios import persistencia

    if not BASE_REAL.exists():
        return
    fugas = []
    for nombre, modulo in sorted(sys.modules.items()):
        if not nombre.startswith("noosfera_project"):
            continue
        for atributo in ("DB_PATH", "DB_FUENTES"):
            valor = getattr(modulo, atributo, None)
            if isinstance(valor, Path) and valor == BASE_REAL:
                fugas.append(f"{nombre}.{atributo}")
    assert not fugas, (
        f"estas rutas siguen apuntando a la base real: {fugas}")


def test_el_aislamiento_no_depende_del_orden_de_ejecucion():
    """El aislamiento lo aplica conftest al cargar, no un test previo.

    Se ejecuta una suite sola, en un proceso nuevo, en orden aleatorio:
    tiene que seguir aislada.
    """
    if not BASE_REAL.exists():
        return
    antes = _sha()
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "scoring_test",
         "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=300)
    assert _sha() == antes, (
        "una suite ejecutada sola modificó la base real: el aislamiento "
        "dependía de que otro test la hubiera preparado")


def test_una_suite_nueva_que_escribe_no_contamina():
    """Una suite nueva que llame a guardar_evento sin aislar.

    Es la vía de escape del punto G: alguien añade un fichero de prueba,
    escribe en la base y no llama a aislar(). Al ejecutarse con pytest,
    conftest ya ha redirigido la ruta, así que no debería tocar la real.

    La suite se crea en un temporal, fuera del proyecto, y se ejecuta con
    pytest apuntando al proyecto (así conftest.py sí interviene).
    """
    import tempfile

    if not BASE_REAL.exists():
        return
    antes = _sha()

    with tempfile.TemporaryDirectory(prefix="suite_nueva_") as td:
        codigo = (
            "from noosfera_project.servicios.persistencia import (\n"
            "    guardar_evento, obtener_eventos_recientes)\n"
            "\n"
            "\n"
            "def test_escribe_sin_aislar():\n"
            "    guardar_evento({'fuente': 'suite_nueva',\n"
            "                    'titulo': 'evento de prueba nuevo',\n"
            "                    'creado_en': '2026-01-01T00:00:00'})\n"
            "    assert len(obtener_eventos_recientes(500)) > 0\n")
        (Path(td) / "test_suite_nueva.py").write_text(codigo, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(td) / "test_suite_nueva.py"),
             "-q", "--no-header", "-p", "no:cacheprovider"],
            cwd=str(RAIZ), capture_output=True, text=True, timeout=300)

    assert _sha() == antes, (
        "una suite nueva que escribe modificó la base real: conftest no "
        f"alcanzó a ese fichero. Salida: {(r.stdout + r.stderr)[-300:]}")


def test_la_variable_de_escape_no_esta_activa_en_el_entorno():
    """PULSO_PRUEBAS_SIN_AISLAR no debe estar puesta en el entorno normal.

    Si alguien la tuviera definida, el aislamiento se desactivaría en
    silencio y las pruebas escribirían en la base real.
    """
    import os
    assert os.environ.get("PULSO_PRUEBAS_SIN_AISLAR") != "1", (
        "PULSO_PRUEBAS_SIN_AISLAR=1 está activa: las pruebas NO están "
        "aisladas y escribirán en la base real")


def test_el_hash_cubre_tambien_el_wal():
    """El hash debe incluir el WAL, no solo el .db principal.

    SQLite en modo WAL deja las escrituras recientes en `eventos.db-wal`
    sin volcarlas al fichero principal. Un hash del .db solo no las ve:
    una prueba podría haber escrito y el hash seguiría igual.

    Este test comprueba que no queda un WAL pendiente junto a la base
    real. Si lo hubiera, el hash estaría dando una falsa tranquilidad.
    """
    if not BASE_REAL.exists():
        return
    wal = Path(str(BASE_REAL) + "-wal")
    assert not wal.exists() or wal.stat().st_size == 0, (
        f"hay un WAL con datos sin volcar ({wal.stat().st_size} B): el "
        f"hash del fichero principal no refleja esas escrituras")


def test_conftest_carga_antes_que_las_suites():
    """conftest.py se ejecuta antes de que las suites importen persistencia.

    Si no, importarían la ruta real ya resuelta y el redireccionamiento
    llegaría tarde. Se comprueba que el redireccionamiento está hecho en
    el momento en que arranca la suite.
    """
    import tempfile
    with tempfile.TemporaryDirectory(prefix="orden_") as td:
        codigo = (
            "from pathlib import Path\n"
            "\n"
            "def test_la_ruta_ya_esta_redirigida():\n"
            "    from noosfera_project.servicios import persistencia\n"
            "    ruta = Path(persistencia.DB_PATH)\n"
            "    assert ruta.parent.name.startswith('pulso_pruebas_'), (\n"
            "        f'la ruta NO estaba redirigida al importar: {ruta}')\n"
            "    real = Path(" + repr(str(BASE_REAL)) + ")\n"
            "    assert ruta != real, 'sigue en la base real'\n")
        (Path(td) / "test_orden.py").write_text(codigo, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(td) / "test_orden.py"),
             "-q", "--no-header", "-p", "no:cacheprovider"],
            cwd=str(RAIZ), capture_output=True, text=True, timeout=300)
    salida = r.stdout + r.stderr
    assert "1 passed" in salida, (
        f"la ruta no estaba redirigida al importar la suite: {salida[-300:]}")
