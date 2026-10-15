"""Punto de entrada para levantar la API de Pulso si FastAPI está disponible.

El chequeo de dependencias se hace dentro de main(), no al importar el módulo,
para que importar este paquete nunca aborte el proceso.
"""
from __future__ import annotations

import logging
try:
    from noosfera_project.servicios.api_minima import crear_api  # noqa: E402
except Exception as exc:  # pragma: no cover - opcional
    logging.warning("servidor_api:10 fallo y se silencio: %s", exc)
    crear_api = None
    _ERR_API = exc
else:
    _ERR_API = None

try:
    app = crear_api() if crear_api is not None else None
except Exception as exc:  # FastAPI ausente o fallo al construir la app
    logging.warning("servidor_api:18 fallo y se silencio: %s", exc)
    app = None
    _ERR_CONSTRUCCION = exc
else:
    _ERR_CONSTRUCCION = None


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Levanta el servidor. Invocable como entry point o a mano."""
    if app is None:
        print("API mínima no disponible:", _ERR_API or _ERR_CONSTRUCCION)
        raise SystemExit(1)
    try:
        import uvicorn
    except ImportError as exc:
        print("Uvicorn no disponible:", exc)
        raise SystemExit(1)

    # `api_minima` NO comprueba la clave de API en ninguna de sus rutas:
    # responde 200 a cualquiera que llegue al puerto. Mientras eso no se
    # resuelva (ver INCIDENCIAS.md §14.5, decision pendiente del autor),
    # este servidor se limita a escuchar solo en localhost, para que no
    # pueda alcanzarse desde otra maquina.
    #
    # Se rechaza cualquier host que no sea de loopback, aunque se pida
    # por parametro: es mas seguro fallar aqui que abrir el puerto.
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(
            f"Rechazado: api_minima no tiene autenticacion y solo puede\n"
            f"escuchar en localhost. Se pidio '{host}'.\n"
            f"Usa el servidor principal (noosfera.py), que si protege sus\n"
            f"rutas con clave, o resuelve antes la autenticacion de api_minima."
        )
        raise SystemExit(1)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
