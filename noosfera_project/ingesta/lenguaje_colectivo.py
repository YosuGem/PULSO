"""Ingesta de lenguaje colectivo no estructurado."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from noosfera_project.servicios.persistencia import (
    crear_base_lenguaje_colectivo,
    guardar_texto_colectivo,
)


BASE_DIR = Path(__file__).resolve().parents[1]

# Extensiones que NO son lenguaje colectivo. La documentación interna del
# proyecto no es voz de gente común: ingesta desde archivo debe rechazarla.
# (Verificado: 3 docs .md del propio proyecto estaban contaminando el corpus.)
EXTENSIONES_EXCLUIDAS = {".md", ".markdown", ".rst", ".txt", ".py", ".json", ".toml", ".yaml", ".yml"}


def _hash(texto: str) -> str:
    return hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]


def es_fuente_valida(ruta: str | Path) -> tuple[bool, str]:
    """Comprueba si un archivo puede ingresar como lenguaje colectivo.

    Devuelve (valido, motivo). Rechaza documentación interna del proyecto.
    """
    extension = Path(ruta).suffix.lower()
    if extension in EXTENSIONES_EXCLUIDAS:
        return False, f"extension excluida ({extension}): no es voz de gente comun"
    return True, ""


def ingestar_texto_plano(fuente: str, texto: str | None, publicado: str | None = None) -> dict:
    """Guarda texto en lenguaje_colectivo evitando duplicados por hash."""
    if not texto or not texto.strip():
        return {"ok": False, "guardados": 0, "hash": None, "fuente": fuente}
    creado = guardar_texto_colectivo(fuente=fuente, texto=texto, publicado=publicado)
    return {"ok": True, "guardados": int(creado is not None), "hash": _hash(texto), "fuente": fuente}


def ingestar_desde_archivo(ruta: str | Path, fuente: str | None = None) -> dict:
    """Importa texto desde un archivo local.

    Rechaza la documentación interna del proyecto (.md, .rst, código, config).
    """
    ruta = Path(ruta).resolve()
    if not ruta.exists():
        return {"ok": False, "error": f"archivo no encontrado: {ruta}"}
    valido, motivo = es_fuente_valida(ruta)
    if not valido:
        return {"ok": False, "error": motivo, "fuente": ruta.name}
    texto = ruta.read_text(encoding="utf-8", errors="ignore")
    fuente = fuente or ruta.name
    return ingestar_texto_plano(fuente=fuente, texto=texto)


def ingestar_desde_json(ruta: str | Path, campos: list[str], campo_fuente: str | None = None) -> dict:
    """Importa desde un array JSON plano de objetos con campos dados.

    `campo_fuente` permite que cada item traiga su propia fuente (autor,
    usuario, subreddit...). Sin el, todos los items comparten el nombre del
    archivo, lo que destruye la medida de diversidad de fuentes: 50 mensajes
    de 50 autores distintos contarían como una sola fuente.
    """
    ruta = Path(ruta).resolve()
    if not ruta.exists():
        return {"ok": False, "error": f"archivo no encontrado: {ruta}"}
    data = json.loads(ruta.read_text(encoding="utf-8", errors="ignore"))
    if not isinstance(data, list):
        raise ValueError("Se esperaba un array JSON")
    guardados = 0
    duplicados = 0
    fuente_base = ruta.name
    for item in data:
        if not isinstance(item, dict):
            continue
        partes = [str(item.get(c) or "") for c in campos]
        texto = " ".join(p.strip() for p in partes if p.strip())
        if not texto:
            continue
        publicado = str(item.get("fecha") or item.get("date") or item.get("publicado") or "")
        fuente = fuente_base
        if campo_fuente:
            fuente = str(item.get(campo_fuente) or "").strip() or fuente_base
        res = ingestar_texto_plano(fuente=fuente, texto=texto, publicado=publicado or None)
        guardados += res.get("guardados", 0)
        if res.get("ok") and not res.get("guardados"):
            duplicados += 1
    return {
        "ok": True,
        "guardados": guardados,
        "duplicados": duplicados,
        "fuente": fuente_base,
    }

