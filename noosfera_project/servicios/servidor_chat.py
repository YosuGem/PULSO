"""Servidor de chat de Pulso.

El chequeo de uvicorn se hace dentro de main() para no abortar la importación.
"""
from __future__ import annotations

import logging
try:
    from noosfera_project.servicios.visor_chat import _crear_app  # noqa: E402
except Exception as exc:  # pragma: no cover - opcional
    logging.warning("servidor_chat:9 fallo y se silencio: %s", exc)
    _crear_app = None
    _ERR = exc
else:
    _ERR = None

try:
    app = _crear_app() if _crear_app is not None else None
except Exception as exc:
    logging.warning("servidor_chat:17 fallo y se silencio: %s", exc)
    app = None
    _ERR = exc


def main(host: str = "127.0.0.1", port: int = 8001) -> None:
    """Levanta el servidor de chat."""
    if app is None:
        print("Visor chat no disponible:", _ERR)
        raise SystemExit(1)
    try:
        import uvicorn
    except ImportError as exc:
        print("Uvicorn no disponible:", exc)
        raise SystemExit(1)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
