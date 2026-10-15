"""
API REST de fuentes para Noósfera (versión B).

Endpoint /api/fuentes - Gestión de fuentes con metadatos y puntuación.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from noosfera_project.servicios.persistencia import DB_PATH

# Apunta a la MISMA base de datos que el resto del proyecto.
# Antes era ROOT / "noosfera_project" / "eventos.db", lo que duplicaba el
# segmento (noosfera_project/noosfera_project/eventos.db) y apuntaba a un
# archivo inexistente: la API llevaba rota desde que se escribió.
DB_FUENTES = DB_PATH


class FuenteBase(BaseModel):
    nombre: str = Field(..., example="Hacker News")
    url: str = Field(..., example="https://news.ycombinator.com/")
    tipo: str = Field(..., example="rss", literal_values=["rss", "social", "otro"])
    idioma: str = Field(default="es", example="es")
    activo: bool = Field(default=True)


class FuenteCreate(FuenteBase):
    pass


class Fuente(FuenteBase):
    id: int
    score: float = Field(default=0.0, ge=0, le=1)
    ultima_actualizacion: Optional[datetime] = None


def _get_db() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_FUENTES), timeout=20)
    con.row_factory = sqlite3.Row
    _asegurar_tabla(con)
    return con


def _asegurar_tabla(con: sqlite3.Connection) -> None:
    """Crea la tabla `fuentes` si no existe. Idempotente."""
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fuentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            tipo TEXT DEFAULT 'rss',
            idioma TEXT DEFAULT 'es',
            score REAL DEFAULT 0.0,
            ultima_actualizacion TEXT,
            activo INTEGER DEFAULT 1
        )
        """
    )


def crear_api_fuentes() -> FastAPI:
    app = FastAPI(title="Noósfera API - Fuentes", version="0.2.2-dev")

    @app.get("/api/fuentes", response_model=list[Fuente])
    def listar_fuentes(activo: Optional[bool] = None):
        """Listar fuentes con filtro opcional por estado activo."""
        con = _get_db()
        query = "SELECT * FROM fuentes"
        params: list = []
        if activo is not None:
            query += " WHERE activo = ?"
            params.append(1 if activo else 0)
        query += " ORDER BY nombre"
        rows = con.execute(query, params).fetchall()
        con.close()
        return [dict(row) for row in rows]

    @app.get("/api/fuentes/{fuente_id}", response_model=Fuente)
    def obtener_fuente(fuente_id: int):
        """Detalle de una fuente específica."""
        con = _get_db()
        row = con.execute("SELECT * FROM fuentes WHERE id = ?", [fuente_id]).fetchone()
        con.close()
        if not row:
            raise HTTPException(status_code=404, detail="Fuente no encontrada")
        return dict(row)

    @app.post("/api/fuentes", response_model=Fuente, status_code=201)
    def crear_fuente(fuente: FuenteCreate):
        """Crear una nueva fuente."""
        con = _get_db()
        try:
            cursor = con.execute(
                "INSERT INTO fuentes (nombre, url, tipo, idioma, activo, score) VALUES (?, ?, ?, ?, ?, 0.0)",
                [fuente.nombre, fuente.url, fuente.tipo, fuente.idioma, 1 if fuente.activo else 0],
            )
            con.commit()
        except sqlite3.IntegrityError:
            con.close()
            # Nombre duplicado: es un conflicto, no un error del servidor.
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una fuente con el nombre '{fuente.nombre}'",
            )
        fuente_id = cursor.lastrowid
        row = con.execute("SELECT * FROM fuentes WHERE id = ?", [fuente_id]).fetchone()
        con.close()
        return dict(row)

    return app