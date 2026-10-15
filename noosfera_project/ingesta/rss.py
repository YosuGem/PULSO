"""Ingesta de feeds RSS y registro de eventos."""

from __future__ import annotations

import hashlib
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

import feedparser
import socket

from noosfera_project.servicios.persistencia import guardar_evento
from noosfera_project.ingesta.canales import FEED_URLS
from noosfera_project.procesamiento.detector import evaluar as evaluar_detector
from noosfera_project.procesamiento.scoring import calcular_score

BASE_DIR = Path(__file__).resolve().parents[1]
FEED_TIMEOUT = 20
FEED_MAX_BYTES = 4 * 1024 * 1024


import logging
def _hash(texto: str) -> str:
    return hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]


def _normalizar_fecha(entrada) -> str | None:
    if getattr(entrada, "published_parsed", None):
        try:
            return datetime(*entrada.published_parsed[:6]).isoformat()
        except Exception as exc:
            logging.warning("rss:32 fallo y se silencio: %s", exc)
            pass
    if getattr(entrada, "updated_parsed", None):
        try:
            return datetime(*entrada.updated_parsed[:6]).isoformat()
        except Exception as exc:
            logging.warning("rss:37 fallo y se silencio: %s", exc)
            pass
    return datetime.utcnow().isoformat()


def ingestar_fuentes(fuentes: Iterable[str] | None = None) -> dict:
    fuentes = list(fuentes or FEED_URLS)
    resultado = {"fuentes_procesadas": 0, "eventos_guardados": 0, "errores": []}
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(FEED_TIMEOUT)
    try:
        for url in fuentes:
            try:
                fuente = feedparser.parse(
                    url,
                    response_headers={"Content-Length": str(FEED_MAX_BYTES)},
                )
                if getattr(fuente, "bozo", False) and not getattr(fuente, "entries", []):
                    raise ValueError(fuente.get("bozo_exception", "feed inválido"))
                resultado["fuentes_procesadas"] += 1
            except Exception as exc:
                logging.warning("rss:60 fallo y se silencio: %s", exc)
                resultado["errores"].append({"fuente": url, "error": str(exc)})
                continue

            for entrada in fuente.entries[:25]:
                titulo = getattr(entrada, "title", "") or ""
                enlace = getattr(entrada, "link", "") or ""
                publicado = _normalizar_fecha(entrada) or ""
                categorias = ",".join(
                    getattr(t, "term", "") for t in getattr(entrada, "tags", [])[:4]
                )
                clave = _hash(f"{url}|{titulo}|{publicado}")
                deteccion = evaluar_detector(titulo)
                categorias = categorias or ",".join(deteccion.get("coincidencias", []))
                score = calcular_score(
                    {
                        "titulo": titulo,
                        "categorias": categorias,
                        "publicado": publicado,
                        "fuente": url,
                    }
                )
                evento = {
                    "fuente": url,
                    "titulo": titulo,
                    "enlace": enlace,
                    "publicado": publicado,
                    "categorias": categorias,
                    "puntuacion": score.puntuacion,
                    "procesado": 1,
                }
                try:
                    guardar_evento(evento)
                    resultado["eventos_guardados"] += 1
                except Exception as exc:
                    logging.warning("rss:97 fallo y se silencio: %s", exc)
                    resultado["errores"].append({"entrada": clave, "error": str(exc)})
    finally:
        try:
            socket.setdefaulttimeout(old_timeout)
        except Exception as exc:
            logging.warning("rss:100 fallo y se silencio: %s", exc)
            pass
    return resultado
