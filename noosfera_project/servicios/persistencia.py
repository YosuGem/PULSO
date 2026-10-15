"""Servicios de persistencia y logs para Noósfera."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "eventos.db"
LOG_PATH = Path(__file__).resolve().parents[1] / "noosfera.log"
_SQLITE_TIMEOUT = 20


def _conexion(path: Path | None = None):
    ruta = path or DB_PATH
    conn = sqlite3.connect(
        ruta,
        check_same_thread=False,
        timeout=_SQLITE_TIMEOUT,
    )
    conn.row_factory = sqlite3.Row
    return conn

import logging

def crear_base() -> Path:
    """Crea la base y las tablas base si no existen y devuelve la ruta."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conexion() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fuente TEXT,
                titulo TEXT NOT NULL,
                enlace TEXT,
                publicado TEXT,
                categorias TEXT,
                puntuacion REAL,
                procesado INTEGER DEFAULT 0,
                creado_en TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analisis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evento_id INTEGER,
                resumen TEXT,
                categorias_sugeridas TEXT,
                detectado INTEGER DEFAULT 0,
                creado_en TEXT NOT NULL,
                FOREIGN KEY(evento_id) REFERENCES eventos(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lenguaje_colectivo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fuente TEXT NOT NULL,
                texto TEXT NOT NULL,
                texto_hash TEXT NOT NULL,
                publicado TEXT,
                creado_en TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_lenguaje_colectivo_hash ON lenguaje_colectivo(texto_hash)"
        )
        # Nota: no se indexa la tabla 'eventos'. El codigo original creaba
        # un indice UNIQUE sobre una columna que el CREATE TABLE no declara
        # ('texto_hash' en unas versiones, 'clave' en otras), lo que rompia
        # crear_base() con "no such column" segun que base de datos hubiera
        # en disco. Verificado: ninguna consulta del proyecto usa esa columna,
        # asi que el indice no aportaba nada. El dedupe real se hace sobre
        # lenguaje_colectivo(texto_hash), que si existe y si se indexa.
    return DB_PATH


def _log(mensaje: str) -> None:
    try:
        linea = f"{datetime.utcnow().isoformat()} {mensaje}\n"
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(linea)
    except Exception as exc:
        logging.warning("persistencia:86 fallo y se silencio: %s", exc)
        pass


def _puntuacion_valida(valor: Any) -> float | None:
    """Devuelve la puntuacion solo si es un numero real utilizable.

    No inventa ni impone un rango (0-1 u otro): eso no esta definido en el
    contrato del proyecto y es decision del autor. Solo rechaza lo que NO
    es un numero real, porque SQLite lo guardaria como texto en una columna
    REAL y eso corrompe el scoring en silencio.

    Rechaza: texto, NaN, +Infinity, -Infinity.
    Acepta: cualquier otro numero, incluidos negativos o mayores que 1,
    porque el rango esperado no esta documentado (ver INCIDENCIAS.md §4.1).
    """
    if valor is None:
        return None
    if isinstance(valor, bool):        # bool es subclase de int en Python
        return None
    if not isinstance(valor, (int, float)):
        return None
    numero = float(valor)
    if numero != numero or numero in (float("inf"), float("-inf")):
        return None
    return numero


def guardar_evento(evento: dict[str, Any]) -> int:
    with _conexion() as conn:
        conn.execute(
            """
            INSERT INTO eventos (fuente, titulo, enlace, publicado, categorias, puntuacion, procesado, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evento.get("fuente"),
                evento.get("titulo"),
                evento.get("enlace"),
                evento.get("publicado"),
                evento.get("categorias"),
                _puntuacion_valida(evento.get("puntuacion")),
                1 if evento.get("procesado") else 0,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        evento_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    _log(f"EVENTO_GUARDADO id={evento_id} fuente={evento.get('fuente')}")
    return evento_id


def guardar_analisis(analisis: dict[str, Any]) -> int:
    with _conexion() as conn:
        conn.execute(
            """
            INSERT INTO analisis (evento_id, resumen, categorias_sugeridas, detectado, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                analisis.get("evento_id"),
                analisis.get("resumen"),
                analisis.get("categorias_sugeridas"),
                1 if analisis.get("detectado") else 0,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        analisis_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    _log(f"ANALISIS_GUARDADO id={analisis_id} evento_id={analisis.get('evento_id')}")
    return analisis_id


def _limite_seguro(limite: Any, por_defecto: int = 100) -> int:
    """Normaliza el limite de una consulta.

    Contrato: el limite es cuantos registros se quieren como maximo.
    Un valor negativo no tiene sentido con ese significado, y en SQLite
    `LIMIT -1` significa 'sin limite', es decir, devuelve TODAS las filas.
    Eso es lo contrario de lo que pide quien llama.

    Regla:
      - None o no entero  -> valor por defecto
      - negativo          -> 0 (no se pidio ninguno)
      - 0                 -> 0
      - positivo          -> ese valor
    """
    if limite is None:
        return por_defecto
    try:
        n = int(limite)
    except (TypeError, ValueError):
        return por_defecto
    return max(n, 0)


def obtener_eventos_recientes(limite: int = 100) -> list[dict[str, Any]]:
    with _conexion() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM eventos ORDER BY creado_en DESC LIMIT ?",
            (_limite_seguro(limite),),
        ).fetchall()
    return [dict(r) for r in rows]


def obtener_analisis_recientes(limite: int = 100) -> list[dict[str, Any]]:
    with _conexion() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM analisis ORDER BY creado_en DESC LIMIT ?", (int(limite),)
        ).fetchall()
    return [dict(r) for r in rows]


def crear_base_lenguaje_colectivo() -> Path:
    with _conexion() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lenguaje_colectivo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fuente TEXT NOT NULL,
                texto TEXT NOT NULL,
                texto_hash TEXT NOT NULL,
                publicado TEXT,
                creado_en TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_lenguaje_colectivo_hash ON lenguaje_colectivo(texto_hash)"
        )
    return DB_PATH


def guardar_texto_colectivo(fuente: str, texto: str, publicado: str | None = None) -> int | None:
    import hashlib

    texto_hash = hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]
    with _conexion() as conn:
        try:
            conn.execute(
                """
                INSERT INTO lenguaje_colectivo (fuente, texto, texto_hash, publicado, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fuente,
                    texto,
                    texto_hash,
                    publicado,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            texto_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            return texto_id
        except sqlite3.IntegrityError as exc:
            logging.warning("servicios/persistencia.py:201 fallo y se silencio: %s", exc)
            return None


def obtener_textos_recientes(limite: int = 100) -> list[dict[str, Any]]:
    with _conexion() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM lenguaje_colectivo ORDER BY creado_en DESC LIMIT ?", (int(limite),)
        ).fetchall()
    return [dict(r) for r in rows]