"""Suite mínima automática de Noósfera."""

from __future__ import annotations

import socket
import threading
import time
import urllib.parse
import urllib.request

import pytest

HOST = "127.0.0.1"
PORT = 18765


def _ensure_server() -> None:
    # Clave de prueba local para que la autorizacion obligatoria
    # de auth.py pueda validar las peticiones de la suite.
    import os
    os.environ.setdefault("NOOSFERA_API_KEY",
                         "noosfera_local_prueba_2026")
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1].parent
    spec = importlib.util.spec_from_file_location("noosfera_server_tests", root / "noosfera.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    srv = threading.Thread(target=mod.servidor, args=(PORT,), daemon=True)
    srv.start()
    for _ in range(80):
        try:
            with socket.create_connection((HOST, PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError(f"Noósfera no arrancó en {HOST}:{PORT}")


@pytest.fixture(scope="session", autouse=True)
def _levantar_servidor():
    _ensure_server()
    yield


def _get(path: str) -> tuple[int, bytes]:
    url = f"http://{HOST}:{PORT}{path}"
    # La API exige autorizacion obligatoria (auth.py). Sin la clave, todas
    # las rutas protegidas devuelven 401. Esta suite no la enviaba y por eso
    # fallaba: era un defecto de la prueba, no del programa.
    import os
    clave = os.environ.get("NOOSFERA_API_KEY", "")
    headers = {"Authorization": f"Bearer {clave}"} if clave else {}
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _status_es(path: str, esperado: int) -> None:
    status, _ = _get(path)
    assert status == esperado, f"{path} => {status}, esperado {esperado}"


def test_health_ok():
    _status_es("/api/health", 200)


def test_eventos_ok():
    _status_es("/api/eventos?limite=1", 200)


def test_senales_ok():
    _status_es("/api/senales?horizonte=1&limite=1", 200)


def test_consultar_sin_pregunta_falla_400():
    _status_es("/api/consultar", 400)


def test_consultar_inexistente_no_500():
    _status_es("/api/consultar?pregunta=zzzzz_no_existe_zzzzz", 200)


def test_endpoint_desconocido_404():
    _status_es("/no-existe", 404)


def test_root_ok():
    _status_es("/", 200)


def test_exportar_ok():
    _status_es("/api/exportar_json?limite=1", 200)
