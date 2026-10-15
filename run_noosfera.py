"""Noósfera: servidor mínimo de endpoints 8080."""

from __future__ import annotations

import json
import socket
import threading
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from noosfera_project.servicios.persistencia import obtener_eventos_recientes
from noosfera_project.procesamiento.normalizacion import tokens
from noosfera_project.procesamiento.predictor import senales_emergentes
from noosfera_project.procesamiento.consulta_lenguaje import consultar_lenguaje
import urllib.parse


ENDPOINTS = {
    "/api/health": ("application/json; charset=utf-8", b'{"estado":"ok","proyecto":"noosfera"}'),
}


_BODY_HEALTH = b'{"estado":"ok","proyecto":"noosfera"}'


def _obtener_eventos(limite: int = 80):
    return obtener_eventos_recientes(limite=limite)


def _eventos(limite: int) -> bytes:
    docs = _obtener_eventos(limite)
    return json.dumps(docs, ensure_ascii=False, indent=2).encode("utf-8")


def _senales(horizonte: int = 1, limite: int = 10) -> bytes:
    docs = _obtener_eventos(200)
    enriquecidos = []
    for d in docs:
        texto = d.get("texto") or d.get("titulo") or ""
        d["_tokens"] = tokens(texto)
        enriquecidos.append(d)
    senales = senales_emergentes(enriquecidos, horizonte_dias=horizonte * 30)
    items = senales if len(senales) <= limite else senales[:limite]
    payload = [{
        "id": i + 1,
        "etiqueta": s.etiqueta,
        "documentos": s.documentos,
        "frecuencia": s.frecuencia,
        "primera_fecha": s.primera_fecha,
        "ultima_fecha": s.ultima_fecha,
        "tendencia": s.tendencia,
        "horizonte_consultado_dias": horizonte,
    } for i, s in enumerate(items)]
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return body


def _json(body: bytes) -> bytes:
    return b"HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\nConnection: close\r\nContent-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body


def _text(body: bytes, status: str = "200 OK") -> bytes:
    return f"HTTP/1.1 {status}\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _endpoint_head(headers: bytes) -> bytes:
    return b"HTTP/1.1 200 OK\r\n" + headers + b"Connection: close\r\n\r\n"


def servir(conn: socket.socket, addr):
    try:
        conn.settimeout(1)
        data = b""
        while True:
            try:
                chunk = conn.recv(4096)
            except (socket.timeout, OSError):
                break
            if not chunk:
                break
            data += chunk
            if b"\r\n\r\n" in data:
                break
        texto = data.decode("utf-8", errors="ignore")
        if not texto:
            return
        primera = texto.splitlines()[0] if texto.splitlines() else ""
        metodo = primera.split(" ")[0] if " " in primera else ""
        ruta = primera.split(" ")[1] if " " in primera else "/"

        if metodo != "GET":
            conn.sendall(b"HTTP/1.1 405 METHOD NOT ALLOWED\r\nConnection: close\r\n\r\n")
            return

        endpoint = ruta.split("?")[0]

        if endpoint == "/api/health":
            body = b'{"estado":"ok","proyecto":"noosfera"}'
            conn.sendall(_json(body))

        elif endpoint == "/api/eventos":
            raw = ruta.split("?")[1] if "?" in ruta else ""
            limite = 1
            for parte in raw.split("&"):
                if parte.startswith("limite="):
                    try:
                        limite = int(parte.split("=", 1)[1])
                    except ValueError:
                        limite = 1
            body = _eventos(limite)
            conn.sendall(_json(body))

        elif endpoint == "/api/senales":
            horizonte = 1
            limite = 10
            raw = ruta.split("?")[1] if "?" in ruta else ""
            for parte in raw.split("&"):
                if parte.startswith("horizonte="):
                    try:
                        horizonte = int(parte.split("=", 1)[1])
                    except ValueError:
                        horizonte = 1
                if parte.startswith("limite="):
                    try:
                        limite = int(parte.split("=", 1)[1])
                    except ValueError:
                        limite = 10
            body = _senales(horizonte, limite)
            conn.sendall(_json(body))

        elif endpoint == "/api/exportar_json":
            docs = _obtener_eventos(500)
            ruta = ROOT / "exportaciones" / "eventos_export.json"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
            body = json.dumps({"ok": True, "archivo": str(ruta), "documentos": len(docs)}, ensure_ascii=False).encode("utf-8")
            conn.sendall(_json(body))

        elif endpoint == "/api/consultar":
            consulta = ""
            raw = ruta.split("?")[1] if "?" in ruta else ""
            for parte in raw.split("&"):
                if parte.startswith("pregunta="):
                    consulta = urllib.parse.unquote(parte.split("=", 1)[1])
            docs = consultar_lenguaje(consulta, limite=20) if consulta else []
            payload = []
            for d in docs:
                payload.append({
                    "id": d.get("id"),
                    "fuente": d.get("fuente"),
                    "texto": d.get("texto") or "",
                    "publicado": d.get("publicado"),
                    "coincidencias": d.get("coincidencias", 0),
                    "tipo": "lenguaje_colectivo",
                    "similitud": 1.0,
                })
            body = json.dumps({"pregunta": consulta, "total": len(payload), "resultados": payload}, ensure_ascii=False).encode("utf-8")
            conn.sendall(_json(body))

        elif endpoint == "/" or endpoint == "":
            body = json.dumps({"estado": "ok", "proyecto": "noosfera", "endpoints": ["/api/health", "/api/eventos", "/api/senales", "/api/consultar", "/api/exportar_json"]}, ensure_ascii=False).encode("utf-8")
            conn.sendall(_json(body))

        else:
            body = json.dumps({"error": "endpoint no soportado"}).encode("utf-8")
            conn.sendall(_json(body))
    except Exception as exc:
        try:
            import traceback
            (ROOT / 'errores_server.log').write_text(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)), encoding='utf-8')
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
    print(f"Noósfera escuchando en http://localhost:{puerto}", flush=True)
    activo = True
    while activo:
        try:
            conn, addr = srv.accept()
            hilo = threading.Thread(target=servir, args=(conn, addr), daemon=True)
            hilo.start()
        except KeyboardInterrupt:
            activo = False
        except OSError:
            continue
    return 1


if __name__ == "__main__":
    puerto = 8080
    if len(sys.argv) > 1 and sys.argv[1] in {"--server", "-s"}:
        if len(sys.argv) > 2:
            try:
                puerto = int(sys.argv[2])
            except Exception:
                pass
    raise SystemExit(servidor(puerto=puerto))
