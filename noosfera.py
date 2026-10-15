"""Noósfera: entrada oficial única y punto de entrada estable."""

from __future__ import annotations

import json
import logging
import socket
import sys
import threading
import traceback
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from noosfera_project.servicios.persistencia import (
    obtener_eventos_recientes,
)
from noosfera_project.procesamiento.normalizacion import tokens
from noosfera_project.procesamiento.predictor import senales_emergentes
from noosfera_project.procesamiento.consulta_lenguaje import consultar_lenguaje
from auth import authorized
from rate_limit import check as rate_ok
from validacion import (
    limpiar_pregunta,
    normalizar_eventos_params,
    normalizar_senales_params,
    normalizar_consultar_params,
    normalizar_exportar_params,
)
from server.health import estado as health_estado

LOG = logging.getLogger("noosfera.server")
LOG_PATH = ROOT / "errores_server.log"
DB_PATH = ROOT / "noosfera_project" / "eventos.db"


def _init_log() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        filename=str(LOG_PATH),
        encoding="utf-8",
    )


def _safe_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _responder(conn: socket.socket, status: str, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    cabecera = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: application/json; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode("utf-8")
    conn.sendall(cabecera + body)


def _parse_query(ruta: str) -> dict[str, str]:
    if "?" not in ruta:
        return {}
    _, raw = ruta.split("?", 1)
    out: dict[str, str] = {}
    for parte in raw.split("&"):
        if "=" in parte:
            clave, valor = parte.split("=", 1)
            out[clave] = urllib.parse.unquote(valor)
    return out


def _eventos_recientes(conn: socket.socket, ruta: str) -> None:
    try:
        params = normalizar_eventos_params(_parse_query(ruta))
        docs = obtener_eventos_recientes(limite=params["limite"])
        _responder(conn, "200 OK", docs)
    except Exception as exc:
        LOG.error("eventos: %s", traceback.format_exc())
        _responder(conn, "500 INTERNAL SERVER ERROR", {"error": "Fallo interno en eventos."})


def _senales(conn: socket.socket, ruta: str) -> None:
    try:
        params = normalizar_senales_params(_parse_query(ruta))
        horizonte = params["horizonte"]
        limite = params["limite"]
        tema_filtro = params.get("tema")
        docs = obtener_eventos_recientes(200)
        enriquecidos = []
        for d in docs:
            texto = d.get("texto") or d.get("titulo") or ""
            d["_tokens"] = tokens(texto)
            enriquecidos.append(d)
        senales = senales_emergentes(enriquecidos, horizonte_dias=horizonte * 30)
        payload = [
            {
                "id": i + 1,
                "etiqueta": s.etiqueta,
                "documentos": s.documentos,
                "frecuencia": s.frecuencia,
                "primera_fecha": s.primera_fecha,
                "ultima_fecha": s.ultima_fecha,
                "tendencia": getattr(s, "tendencia", ""),
                "horizonte_consultado_dias": horizonte,
            }
            for i, s in enumerate(senales[:limite])
        ]
        if tema_filtro:
            tema_filtro = tema_filtro.lower()
            payload = [
                p
                for p in payload
                if tema_filtro
                in (json.dumps(p, ensure_ascii=False)).lower()
            ]
        _responder(conn, "200 OK", payload)
    except Exception as exc:
        LOG.error("senales: %s", traceback.format_exc())
        _responder(conn, "500 INTERNAL SERVER ERROR", {"error": "Fallo interno en senales."})


def _consultar(conn: socket.socket, ruta: str) -> None:
    try:
        params = normalizar_consultar_params(_parse_query(ruta))
        consulta = params["pregunta"]
        if not consulta:
            _responder(conn, "400 BAD REQUEST", {"error": "Falta parametro 'pregunta'."})
            return
        docs = consultar_lenguaje(consulta, limite=20)
        payload = []
        for d in docs:
            payload.append(
                {
                    "id": d.get("id"),
                    "fuente": d.get("fuente"),
                    "texto": d.get("texto") or "",
                    "publicado": d.get("publicado"),
                    "coincidencias": d.get("coincidencias", 0),
                    "tipo": d.get("tipo", "desconocido"),
                    "similitud": 1.0,
                }
            )
        _responder(conn, "200 OK", {"pregunta": consulta, "total": len(payload), "resultados": payload})
    except Exception as exc:
        LOG.error("consultar: %s", traceback.format_exc())
        _responder(conn, "500 INTERNAL SERVER ERROR", {"error": "Fallo interno en consulta."})


def _exportar(conn: socket.socket, ruta: str) -> None:
    try:
        params = normalizar_exportar_params(_parse_query(ruta))
        from noosfera_project.servicios.exportar import exportar_json
        ruta_exp = ROOT / "exportaciones" / "eventos_export.json"
        resultado = exportar_json(
            limite=params["limite"],
            idioma=params.get("idioma"),
            fuente=params.get("fuente"),
            ruta_salida=ruta_exp,
        )
        _responder(conn, "200 OK", resultado)
    except Exception as exc:
        LOG.error("exportar: %s", traceback.format_exc())
        _responder(conn, "500 INTERNAL SERVER ERROR", {"error": "Fallo interno en exportacion."})


def _autorizado(auth_header):
    """(True, None) si autorizado; (False, msg) si no.

    Captura RuntimeError de auth (clave no configurada) -> 401, no 500.
    """
    try:
        if authorized(auth_header):
            return True, None
    except RuntimeError as exc:
        return False, f"auth no disponible: {exc}"
    return False, "token invalido"


def atender(conn: socket.socket, addr) -> None:
    try:
        conn.settimeout(5)
        datos = b""
        while True:
            try:
                trozo = conn.recv(4096)
            except (socket.timeout, OSError):
                break
            if not trozo:
                break
            datos += trozo
            if b"\r\n\r\n" in datos:
                break

        texto = datos.decode("utf-8", errors="ignore")
        if not texto:
            return

        primera = texto.splitlines()[0] if texto.splitlines() else ""
        partes = primera.split(" ")
        metodo = partes[0] if partes else ""
        ruta = partes[1] if len(partes) > 1 else "/"

        if metodo != "GET":
            conn.sendall(b"HTTP/1.1 405 METHOD NOT ALLOWED\r\nConnection: close\r\n\r\n")
            return

        endpoint = ruta.split("?")[0]
        auth_header = None
        for linea in texto.splitlines()[1:]:
            if linea.lower().startswith("authorization:"):
                auth_header = linea.split(":", 1)[1].strip()
                break

        if endpoint == "/api/health":
            _responder(conn, "200 OK", health_estado(DB_PATH))
        elif endpoint == "/api/eventos":
            ok, _ = rate_ok()
            if not ok:
                conn.sendall(b"HTTP/1.1 429 Too Many Requests\r\nRetry-After: 60\r\nConnection: close\r\n\r\n")
                return
            ok_auth, _ = _autorizado(auth_header)
            if not ok_auth:
                conn.sendall(b"HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n")
                return
            _eventos_recientes(conn, ruta)
        elif endpoint == "/api/senales":
            ok, _ = rate_ok()
            if not ok:
                conn.sendall(b"HTTP/1.1 429 Too Many Requests\r\nRetry-After: 60\r\nConnection: close\r\n\r\n")
                return
            ok_auth, _ = _autorizado(auth_header)
            if not ok_auth:
                conn.sendall(b"HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n")
                return
            _senales(conn, ruta)
        elif endpoint == "/api/consultar":
            ok, _ = rate_ok()
            if not ok:
                conn.sendall(b"HTTP/1.1 429 Too Many Requests\r\nRetry-After: 60\r\nConnection: close\r\n\r\n")
                return
            ok_auth, _ = _autorizado(auth_header)
            if not ok_auth:
                conn.sendall(b"HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n")
                return
            _consultar(conn, ruta)
        elif endpoint == "/api/exportar_json":
            ok, _ = rate_ok()
            if not ok:
                conn.sendall(b"HTTP/1.1 429 Too Many Requests\r\nRetry-After: 60\r\nConnection: close\r\n\r\n")
                return
            ok_auth, _ = _autorizado(auth_header)
            if not ok_auth:
                conn.sendall(b"HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n")
                return
            _exportar(conn, ruta)
        elif endpoint == "/api/fuentes":
            ok, _ = rate_ok()
            if not ok:
                conn.sendall(b"HTTP/1.1 429 Too Many Requests\r\nRetry-After: 60\r\nConnection: close\r\n\r\n")
                return
            ok_auth, _ = _autorizado(auth_header)
            if not ok_auth:
                conn.sendall(b"HTTP/1.1 401 Unauthorized\r\nConnection: close\r\n\r\n")
                return
            from noosfera_project.servicios.evaluacion_fuentes import evaluar
            _responder(conn, "200 OK", evaluar())
        elif endpoint in ("/", ""):
            _responder(
                conn,
                "200 OK",
                {
                    "estado": "ok",
                    "proyecto": "noosfera",
                    "endpoints": [
                        "/api/health",
                        "/api/eventos",
                        "/api/senales",
                        "/api/consultar",
                        "/api/exportar_json",
                        "/api/fuentes",
                    ],
                },
            )
        else:
            _responder(conn, "404 NOT FOUND", {"error": "endpoint no soportado"})
    except Exception as exc:
        LOG.error("request: %s", traceback.format_exc())
        try:
            conn.sendall(b"HTTP/1.1 500 INTERNAL SERVER ERROR\r\nConnection: close\r\n\r\n")
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def servidor(puerto: int = 8080) -> int:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", puerto))
    srv.listen(20)
    LOG.info("Noosfera escuchando en http://localhost:%d", puerto)
    print(f"Noósfera escuchando en http://localhost:{puerto}", flush=True)
    activo = True
    while activo:
        try:
            conn, addr = srv.accept()
            hilo = threading.Thread(target=atender, args=(conn, addr), daemon=True)
            hilo.start()
        except KeyboardInterrupt:
            activo = False
        except OSError:
            continue
    return 1


if __name__ == "__main__":
    puerto = 8080
    _init_log()
    if len(sys.argv) > 1 and sys.argv[1] in {"--server", "-s"}:
        if len(sys.argv) > 2:
            puerto = _safe_int(sys.argv[2], 8080)
    raise SystemExit(servidor(puerto=puerto))
