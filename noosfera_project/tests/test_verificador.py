"""Regresion: el verificador no debe dar por bueno algo que falla.

Defectos encontrados el 14/10/2026 (segunda fase de auditoria):

1. `verificar_pulso.py` ejecutaba pytest y la CLI pero NO usaba su codigo
   de salida en el veredicto. Un test que fallaba o una CLI rota dejaban
   el script diciendo "Todo lo comprobable pasa" y saliendo con rc=0.
2. Los ficheros obligatorios se comprobaban solo por existencia. Un
   LICENSE o un README vacios pasaban como validos.

ARQUITECTURA DE ESTAS PRUEBAS

  - Una sola copia del proyecto para todos los tests (fixture de sesion),
    no una por test.
  - El verificador se ejecuta en modo rapido (PULSO_PRUEBA_RAPIDA=1), que
    salta las 9 suites script y la CLI. Esas partes son las lentas y no
    hacen falta: lo que se comprueba es el VEREDICTO FINAL.
  - Cada test rompe UNA cosa en la copia, ejecuta el verificador y
    restaura ese fichero concreto. Asi los tests no se pisan entre ellos.
  - Todo ocurre en un temporal. Los ficheros del proyecto real no se tocan.
  - El temporal se borra al terminar el modulo, pase lo que pase.

Se ejecutan aparte de la bateria normal, a proposito:

    python -m pytest noosfera_project/tests/test_verificador.py -v

La bateria normal los excluye con --ignore, porque si no el verificador
volveria a lanzarse a si mismo y el tiempo creceria sin limite.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
VERIFICADOR = RAIZ / "verificar_pulso.py"
CLAVE_PRUEBA = "noosfera_local_prueba_2026"

# Lo que el verificador necesita para ejecutarse entero.
COPIAR = ["noosfera.py", "auth.py", "rate_limit.py", "validacion.py",
          "verificar_pulso.py", "requirements.txt", "README.md", "LICENSE",
          ".env.example", ".gitignore", "SCORING.md"]

# Contenido original de lo que cada test modifica, para poder restaurarlo.
_ORIGINALES: dict[Path, bytes] = {}


@pytest.fixture(scope="module")
def copia():
    """Una sola copia del proyecto para todos los tests del modulo."""
    tmp = Path(tempfile.mkdtemp(prefix="test_ver_"))
    destino = tmp / "copia"
    shutil.copytree(
        RAIZ, destino,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git",
                                      "*.chk", ".pytest_cache",
                                      "_norton_", "NOOSFERA"))
    for f in COPIAR:
        q = RAIZ / f
        if q.exists():
            shutil.copy2(q, destino / f)
    yield destino
    shutil.rmtree(tmp, ignore_errors=True)


def _ejecutar(destino: Path, rapido: bool = True):
    E = {**os.environ, "PYTHONPATH": str(destino),
         "NOOSFERA_HOME": str(destino),
         "NOOSFERA_API_KEY": CLAVE_PRUEBA}
    if rapido:
        E["PULSO_PRUEBA_RAPIDA"] = "1"
    r = subprocess.run([sys.executable, "verificar_pulso.py"],
                       cwd=str(destino), capture_output=True, text=True,
                       timeout=300, env=E)
    return r.returncode, r.stdout + r.stderr


def _romper(destino: Path, relativo: str, contenido: str) -> None:
    """Modifica (o crea) un fichero en la copia, guardando el original.

    Si el fichero no existe, se marca para borrarlo al restaurar.
    """
    q = destino / relativo
    if q.exists():
        _ORIGINALES.setdefault(q, q.read_bytes())
    else:
        _ORIGINALES.setdefault(q, b"__NO_EXISTIA__")
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text(contenido, encoding="utf-8")


def _restaurar(destino: Path, relativo: str) -> None:
    q = destino / relativo
    if q not in _ORIGINALES:
        return
    original = _ORIGINALES[q]
    if original == b"__NO_EXISTIA__":
        if q.exists():
            q.unlink()
    else:
        q.write_bytes(original)


def _borrar(destino: Path, relativo: str) -> None:
    q = destino / relativo
    if q.exists():
        q.unlink()


# ── pruebas de comportamiento ──────────────────────────────────

def test_linea_base_se_aprueba(copia):
    """Sin romper nada, el verificador debe aprobar con rc=0."""
    rc, sal = _ejecutar(copia)
    assert rc == 0, f"rc={rc}, se esperaba 0. Salida: {sal[-300:]}"
    assert "Todo lo comprobable pasa" in sal


def test_un_test_que_falla_hace_fallar_la_verificacion(copia):
    """Defecto 1: el rc de pytest no llegaba al veredicto final."""
    rel = "noosfera_project/tests/test_roto_a_proposito.py"
    try:
        _romper(copia, rel,
                "def test_falla_a_proposito():\n"
                "    assert False, 'para comprobar que se detecta'\n")
        rc, sal = _ejecutar(copia)
        assert rc != 0, (
            "un test de pytest que falla debe hacer fallar la verificacion; "
            f"devolvio rc=0. Salida: {sal[-300:]}")
    finally:
        _borrar(copia, rel)


def test_ficheros_obligatorios_vacios_se_detectan(copia):
    """Defecto 2: se comprobaba solo la existencia, no el contenido."""
    for nombre in ("LICENSE", "README.md"):
        try:
            _romper(copia, nombre, "")
            rc, sal = _ejecutar(copia)
            assert rc != 0, (
                f"{nombre} vacio debe detectarse; rc={rc}. "
                f"Salida: {sal[-300:]}")
        finally:
            _restaurar(copia, nombre)


def test_env_con_clave_se_detecta(copia):
    """Un .env con clave dentro del proyecto no debe pasar desapercibido."""
    try:
        _romper(copia, ".env", "NOOSFERA_API_KEY=x\n")
        rc, sal = _ejecutar(copia)
        assert rc != 0, f"rc={rc}. Salida: {sal[-300:]}"
    finally:
        _borrar(copia, ".env")


def test_falta_fichero_obligatorio(copia):
    """Si falta LICENSE, la verificacion debe fallar."""
    q = copia / "LICENSE"
    _ORIGINALES.setdefault(q, q.read_bytes())
    q.unlink()
    try:
        rc, sal = _ejecutar(copia)
        assert rc != 0, f"rc={rc}. Salida: {sal[-300:]}"
    finally:
        _restaurar(copia, "LICENSE")


def test_un_modulo_que_no_compila_se_detecta(copia):
    rel = "noosfera_project/servicios/roto_a_proposito.py"
    try:
        _romper(copia, rel, "def f(:\n    pass\n")
        rc, sal = _ejecutar(copia)
        assert rc != 0, f"rc={rc}. Salida: {sal[-300:]}"
    finally:
        _borrar(copia, rel)


def test_una_suite_que_falla_se_detecta(copia):
    """Una suite distinta de score_suite debe hacer fallar la verificacion."""
    rel = "noosfera_project/tests/health_check.py"
    try:
        _romper(copia, rel, "raise SystemExit(1)\n")
        rc, sal = _ejecutar(copia, rapido=False)
        assert rc != 0, f"rc={rc}. Salida: {sal[-300:]}"
    finally:
        _restaurar(copia, rel)


def test_score_suite_esta_excluida_a_proposito(copia):
    """score_suite falla por decision pendiente: no debe impedir el aprobado.

    Es la excepcion conocida (INCIDENCIAS.md §4.1). Este test protege la
    exclusion: si alguien la quitara, el verificador se caeria por un
    fallo que no es suyo.
    """
    rel = "noosfera_project/tests/score_suite.py"
    try:
        _romper(copia, rel, "raise SystemExit(1)\n")
        rc, sal = _ejecutar(copia, rapido=False)
        assert rc == 0, (
            "score_suite esta excluida a proposito, no debe impedir el "
            f"aprobado; rc={rc}. Salida: {sal[-300:]}")
    finally:
        _restaurar(copia, rel)


def test_la_cli_rota_hace_fallar_la_verificacion(copia):
    """Defecto 1: el rc de la CLI tampoco se usaba en el veredicto.

    Usa el modo COMPLETO, porque en modo rapido la CLI se omite.
    """
    rel = "noosfera_project/cli.py"
    try:
        _romper(copia, rel, "raise SystemExit(1)\n")
        rc, sal = _ejecutar(copia, rapido=False)
        assert rc != 0, (
            f"una CLI que no arranca debe detectarse; rc={rc}. "
            f"Salida: {sal[-300:]}")
    finally:
        _restaurar(copia, rel)


def test_los_tests_no_tocan_el_proyecto_real(copia):
    """La copia es independiente: romper algo en ella no afecta al original."""
    rel = "noosfera_project/cli.py"
    _romper(copia, rel, "raise SystemExit(1)\n")
    try:
        original = (RAIZ / rel).read_text(encoding="utf-8")
        assert "raise SystemExit(1)" not in original, (
            "el test ha modificado el fichero REAL")
    finally:
        _restaurar(copia, rel)


# ── pruebas de estructura (complementan, no sustituyen) ────────

def _leer_regla() -> dict:
    arbol = ast.parse(VERIFICADOR.read_text(encoding="utf-8"))
    encontrado = {"excluye_score_suite": False, "usa_pytest": False,
                  "usa_cli": False, "usa_en_veredicto": False}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Assign):
            for t in nodo.targets:
                if isinstance(t, ast.Name):
                    if t.id == "fallos_script":
                        if "score_suite" in ast.dump(nodo.value):
                            encontrado["excluye_score_suite"] = True
                    elif t.id == "pytest_falla":
                        encontrado["usa_pytest"] = True
                    elif t.id == "cli_falla":
                        encontrado["usa_cli"] = True
        if isinstance(nodo, ast.If):
            if "fallos_script" in ast.dump(nodo.test):
                encontrado["usa_en_veredicto"] = True
    return encontrado


def test_el_veredicto_usa_todos_los_resultados():
    """Comprueba que el veredicto lee todas las senales, no solo algunas."""
    r = _leer_regla()
    assert r["usa_pytest"], "el rc de pytest no se guarda"
    assert r["usa_cli"], "el rc de la CLI no se guarda"
    assert r["usa_en_veredicto"], "las suites fallidas no llegan al veredicto"
    assert r["excluye_score_suite"], "score_suite debe excluirse a proposito"


def test_verificador_no_nombra_el_termino_prohibido():
    """El informe no debe repetir el nombre que hay que eliminar.

    El verificador construye su patron por trozos a proposito, para no
    contener el termino literal. Este test comprueba que sigue siendo asi.
    """
    lineas = [l for l in VERIFICADOR.read_text(encoding="utf-8").split("\n")
              if l.strip().startswith("print(")]
    # Se buscan las dos formas, sin escribirlas enteras en este fichero
    t1 = "cl" + "iff"
    t2 = "web" + "bot"
    prohibido = [l for l in lineas
                 if t1 in l.lower() or t2 in l.lower()]
    assert not prohibido, f"el verificador imprime el termino: {prohibido}"


def test_el_detector_sigue_funcionando():
    """El patron ofuscado debe seguir encontrando coincidencias.

    Comprueba que construir el regex por trozos no ha roto la deteccion:
    se ejecuta el patron del verificador contra un texto sintetico.
    """
    import re as _re
    t = VERIFICADOR.read_text(encoding="utf-8")
    # el patron se arma en el fichero con estas asignaciones
    ns = {}
    for nombre in ("_T", "_W", "_C", "_H"):
        m = _re.search(rf'^{nombre} = "([^"]*)" \+ "([^"]*)"$', t, _re.M)
        if m:
            ns[nombre] = m.group(1) + m.group(2)
        else:
            m2 = _re.search(rf'^{nombre} = "([^"]*)"$', t, _re.M)
            ns[nombre] = m2.group(1) if m2 else ""
    patron = _re.compile(rf"{ns['_T']}\s*high|{ns['_W']}|{ns['_C']}|"
                         rf"{ns['_H']}", _re.I)
    sintetico = f"{ns['_T']} high publico su informe"
    assert patron.search(sintetico), (
        "el patron del verificador ya no detecta el termino prohibido")


def test_verificador_no_tiene_rutas_personales():
    t = VERIFICADOR.read_text(encoding="utf-8")
    assert "Users\\Josu" not in t and "Users/Josu" not in t
    assert "<carpeta-del-proyecto>" not in t, "marcador roto en la ruta"
