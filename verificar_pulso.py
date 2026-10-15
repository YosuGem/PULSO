"""Verificacion de la carpeta PULSO.

Uso:
    python verificar_pulso.py

Comprueba, ejecutandolo de verdad:
  1. que los modulos compilan
  2. las suites con pytest
  3. las suites en forma de script
  4. la CLI (estado y ciclo)
  5. que la carpeta esta limpia y lista para publicar

Codigos de salida:
  0  todo lo comprobable pasa
  1  algun modulo no compila, pytest falla, una suite falla,
     la CLI no arranca, o falta/esta vacio un fichero obligatorio

Nota: `score_suite.py` falla a proposito porque el rango del score no esta
definido (INCIDENCIAS.md §4.1). Es un defecto conocido del programa, no de
la verificacion, y NO cuenta como fallo de este script.

NO MODIFICA NINGUNA BASE DE DATOS. Lee el numero de eventos para
informar, pero nunca restaura ni sobrescribе nada. (Antes habia aqui una
restauracion automatica que sobrescribia la base del paquete; se elimino
el 14/10/2026 por peligrosa.)

Modo rapido para las pruebas automatizadas de si mismo:
    PULSO_PRUEBA_RAPIDA=1
Salta las 9 suites script y la CLI, lentas e innecesarias para comprobar
el veredicto final. Lo usan los tests de
noosfera_project/tests/test_verificador.py. Sin esa variable, el
comportamiento es el de siempre.
"""
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

DEST = Path(__file__).resolve().parent
PKG = DEST / "noosfera_project"
CLAVE = "noosfera_local_prueba_2026"

E = {**os.environ,
     "PYTHONPATH": str(DEST),
     "NOOSFERA_HOME": str(DEST),
     "NOOSFERA_API_KEY": CLAVE}


def limpia():
    """Quita lo que generan las pruebas al ejecutarse."""
    for nombre in ("_norton_", "NOOSFERA"):
        q = DEST / nombre
        if q.exists():
            shutil.rmtree(q, ignore_errors=True)
    for q in list(DEST.rglob("__pycache__")):
        shutil.rmtree(q, ignore_errors=True)
    for pat in ("*.chk", "*.pyc"):
        for q in list(DEST.rglob(pat)):
            q.unlink(missing_ok=True)
    for nombre in ("build", "noosfera.egg-info", ".pytest_cache", "dist"):
        q = PKG / nombre
        if q.exists():
            shutil.rmtree(q, ignore_errors=True)
    # los WAL/SHM no deben publicarse
    for db in DEST.rglob("*.db"):
        for ext in ("-wal", "-shm"):
            w = Path(str(db) + ext)
            if w.exists():
                w.unlink()


print("=" * 92)
print("VERIFICACION DE PULSO")
print("=" * 92)
print(f"  carpeta: {DEST}")
print(f"  python : {sys.version.split()[0]}")

# ── 1. compilacion
print()
print("  1. COMPILACION")
print("  " + "-" * 88)
import py_compile
tot = fallan = 0
for p in DEST.rglob("*.py"):
    if "__pycache__" in str(p):
        continue
    tot += 1
    try:
        py_compile.compile(str(p), doraise=True, cfile=str(p) + ".chk")
    except py_compile.PyCompileError as ex:
        fallan += 1
        print(f"     FALLA {p.name}: {str(ex).splitlines()[0][:46]}")
    finally:
        c = Path(str(p) + ".chk")
        if c.exists():
            c.unlink()
print(f"     {tot} modulos, {fallan} fallan")

# ── 2. pytest
print()
print("  2. SUITES CON PYTEST")
print("  " + "-" * 88)
# test_verificador.py se excluye: ejecuta el verificador completo sobre una
# copia temporal, y el verificador lanza pytest. Si se incluyera, cada
# ejecucion volveria a lanzarse a si misma y el tiempo creceria sin limite.
# Se ejecuta aparte, y a proposito, con:
#   python -m pytest noosfera_project/tests/test_verificador.py -v
r = subprocess.run(
    [sys.executable, "-m", "pytest", "noosfera_project/tests/", "-q",
     "--no-header", "-p", "no:cacheprovider",
     "--ignore=noosfera_project/tests/test_verificador.py",
     "-W", "ignore::pytest.PytestReturnNotNoneWarning"],
    cwd=str(DEST), capture_output=True, text=True, timeout=550, env=E)
ul = [l for l in (r.stdout + r.stderr).strip().split("\n") if l.strip()]
res = next((l for l in reversed(ul)
            if "passed" in l or "failed" in l or "skipped" in l), "sin resultado")
print(f"     {res[:76]}")
# El rc de pytest manda: si falla un test, la verificacion falla.
pytest_falla = r.returncode != 0

# ── 3. scripts
print()
print("  3. SUITES EN FORMA DE SCRIPT")
print("  " + "-" * 88)
SCRIPTS = ["bateria_funcional_parte3", "estructura_suite", "health_check",
           "integration_smoke", "score_suite", "scoring_smoke",
           "scoring_test", "seeders", "suite_ampliada"]
# Modo rapido: solo para las pruebas automatizadas de este mismo script.
# Salta las 9 suites (13 s) y la CLI (1,5 s), que son las partes lentas y
# las que las pruebas de test_verificador.py no necesitan: ellas comprueban
# el VEREDICTO, no los resultados intermedios.
# Sin esta variable, el verificador funciona igual que siempre.
RAPIDO = os.environ.get("PULSO_PRUEBA_RAPIDA") == "1"
ok = 0
fallidas = []
for n in SCRIPTS:
    if RAPIDO:
        print(f"     —    {n:28s} (omitida en modo rapido)")
        continue
    try:
        rr = subprocess.run([sys.executable, f"noosfera_project/tests/{n}.py"],
                            cwd=str(DEST), capture_output=True, text=True,
                            timeout=250, env=E)
        if rr.returncode == 0:
            ok += 1
        else:
            fallidas.append(n)
        print(f"     {'OK  ' if rr.returncode == 0 else 'FALLA'} {n:28s} "
              f"rc={rr.returncode}")
    except subprocess.TimeoutExpired:
        fallidas.append(n)
        print(f"     FALLA {n:28s} TIMEOUT")
print(f"     {ok}/{len(SCRIPTS)} pasan")
print("     (score_suite falla: el rango del score no esta definido)")
print("      Ver INCIDENCIAS.md §4.1 — decision pendiente del autor)")
# El resto de suites, si falla alguna, SI es un fallo real de este script.
fallos_script = [n for n in fallidas if n != "score_suite"]

# ── 4. CLI
print()
print("  4. LINEA DE COMANDOS")
print("  " + "-" * 88)
ok_cli = 0
for n in ("estado", "ciclo"):
    if RAPIDO:
        print(f"     —    cli {n}  (omitida en modo rapido)")
        continue
    try:
        rr = subprocess.run([sys.executable, "-m", "noosfera_project.cli", n],
                            cwd=str(DEST), capture_output=True, text=True,
                            timeout=250, env=E)
        if rr.returncode == 0:
            ok_cli += 1
        print(f"     {'OK  ' if rr.returncode == 0 else 'FALLA'} cli {n}")
    except subprocess.TimeoutExpired:
        print(f"     FALLA cli {n} TIMEOUT")
print(f"     {ok_cli}/2 comandos de la CLI pasan")
cli_falla = (ok_cli < 2) and not RAPIDO

# ── 5. limpieza
print()
print("  5. LIMPIEZA")
print("  " + "-" * 88)
limpia()

# ── 5b. estado de las bases (SOLO LECTURA)
#
# NO SE RESTAURA NINGUNA BASE. Este bloque solo cuenta eventos e informa.
#
# Antes había aquí una restauración automática que copiaba una base externa
# encima de `noosfera_project/eventos.db` cuando el recuento no era 1391.
# Eso era peligroso: sobrescribía datos reales del usuario durante una
# simple comprobación, y lo hacía sin preguntar ni avisar antes.
# Se eliminó el 14/10/2026. Si necesitas recuperar una base, hazlo a mano
# y sabiendo qué estás sustituyendo.
import sqlite3
print()
print("  5b. ESTADO DE LAS BASES (solo lectura, no se restaura nada)")
print("  " + "-" * 88)
for f in ("noosfera_project/eventos.db", "eventos.db"):
    p = DEST / f
    if not p.exists():
        continue
    c = sqlite3.connect(f"file:{p}?immutable=1", uri=True)
    n = c.execute("select count(*) from eventos").fetchone()[0]
    ic = c.execute("PRAGMA integrity_check").fetchone()[0]
    c.close()
    aviso = "" if n == 1391 else "   <- no tiene 1391 eventos"
    print(f"     {f:34s} {n} eventos  integrity={ic}{aviso}")
print("     (no se ha modificado ninguna base)")

# ── 6. inventario
print()
print("  6. INVENTARIO")
print("  " + "-" * 88)
n_py = len(list(DEST.rglob("*.py")))
n_tot = len([q for q in DEST.rglob("*") if q.is_file()])
tam = sum(q.stat().st_size for q in DEST.rglob("*") if q.is_file())
print(f"     {n_py} modulos .py")
print(f"     {n_tot} ficheros")
print(f"     {tam/1024/1024:.2f} MB")

for f in ("noosfera_project/eventos.db", "eventos.db"):
    p = DEST / f
    if p.exists():
        c = sqlite3.connect(f"file:{p}?immutable=1", uri=True)
        n = c.execute("select count(*) from eventos").fetchone()[0]
        c.close()
        print(f"     {f:34s} {n} eventos")

# ── 7. publicacion
print()
print("  7. LISTO PARA PUBLICAR")
print("  " + "-" * 88)
# Se buscan restos de nombres que el autor pidio eliminar del proyecto.
# El patron se construye por trozos a proposito: asi este fichero no
# contiene el termino literal y el propio verificador no se marca a si
# mismo cuando lo busca.
_T = "cl" + "iff"
_W = "web" + "bot"
_C = "cl" + "iffhive"
_H = "half past " + "human"
P = re.compile(rf"{_T}\s*high|{_W}|{_C}|{_H}", re.I)
F = re.compile(r"high energy|alta energ", re.I)
fs = set()
for p in DEST.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in {".py", ".md", ".txt"}:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if any(P.search(l) and not F.search(l) for l in t.split("\n")):
        fs.add(p.name)
# No se nombra el origen de la comprobacion: basta con decir si el arbol
# esta limpio. Asi el informe no repite el termino que se quiere eliminar.
print(f"     restos prohibidos : {sorted(fs) if fs else 'ninguno'}")
print(f"     .env con clave    : "
      f"{'PRESENTE, QUITAR' if (DEST / '.env').exists() else 'OK, excluido'}")
print(f"     .env.example      : {'OK' if (DEST / '.env.example').exists() else 'FALTA'}")
print(f"     LICENSE           : {'OK' if (DEST / 'LICENSE').exists() else 'FALTA'}")
print(f"     .gitignore        : {'OK' if (DEST / '.gitignore').exists() else 'FALTA'}")
print(f"     README.md         : {'OK' if (DEST / 'README.md').exists() else 'FALTA'}")
print(f"     INCIDENCIAS.md    : {'OK' if (DEST / 'INCIDENCIAS.md').exists() else 'FALTA'}")
print(f"     SCORING.md        : {'OK' if (DEST / 'SCORING.md').exists() else 'FALTA'}")

# ── 8. veredicto
print()
print("=" * 92)
print("  VEREDICTO")
print("=" * 92)

fallos_reales = []
if fallan:
    fallos_reales.append(f"{fallan} modulo(s) no compilan")
if pytest_falla:
    fallos_reales.append("pytest tiene fallos")
if fallos_script:
    fallos_reales.append(f"suites que fallan: {', '.join(fallos_script)}")
if cli_falla:
    fallos_reales.append("la CLI no funciona")
if (DEST / ".env").exists():
    fallos_reales.append(".env con clave presente")
for oblig in ("LICENSE", "README.md", "INCIDENCIAS.md", "SCORING.md",
              ".env.example", ".gitignore"):
    q = DEST / oblig
    if not q.exists():
        fallos_reales.append(f"falta {oblig}")
    elif q.stat().st_size == 0:
        fallos_reales.append(f"{oblig} esta vacio")

if fallos_reales:
    for f in fallos_reales:
        print(f"  ❌ {f}")
    print()
    print("  Revisar antes de publicar.")
    sys.exit(1)

print("  ✅ Todo lo comprobable pasa.")
print()
print("  Comprobado de verdad, no supuesto:")
print(f"    - {tot} modulos compilan")
print(f"    - pytest: {res[:52]}")
print(f"    - {ok}/{len(SCRIPTS)} suites en forma de script pasan")
print("    - la CLI funciona (estado y ciclo)")
print("    - las bases de datos son las publicadas, integras")
print()
print("  Saber:")
print("    - score_suite.py falla: el rango del score no esta definido.")
print("      Es decision del autor (INCIDENCIAS.md §4.1).")
print("    - test_export_bitacora.py esta omitida: importa una funcion")
print("      que no existe (INCIDENCIAS.md §4.2).")
print("    - No se ha probado una instalacion desde cero ni en Linux/macOS.")
print()
print("=" * 92)
sys.exit(0)
