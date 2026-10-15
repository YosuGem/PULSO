"""
Histórico de análisis (0.2.2-dev).

Para qué sirve
--------------
El sistema solo sabía decir "este tema es grande ahora". No podía decir
"este tema está creciendo", que es la pregunta central de un detector de
eventos emergentes: lo grande ya se ve, lo que crece todavía no.

Cada ejecución del pipeline guarda una foto del estado. Comparando fotos
consecutivas se obtiene la tendencia, que es la señal que antes no existía.

Diseño
------
- Tabla `analisis_historico` en la propia BD: una fila por (fecha, categoría).
- Idempotente por (fecha, categoria): reejecutar el mismo día no duplica.
- Bajo acoplamiento: quien llama al pipeline decide cuándo guardar.
- Sin dependencias nuevas: solo sqlite3.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noosfera_project.servicios.persistencia import DB_PATH


def _conexion(ruta: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(ruta or DB_PATH), timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def asegurar_tabla(conn: sqlite3.Connection | None = None) -> None:
    """Crea la tabla de histórico si no existe. Idempotente."""
    propia = conn is None
    conn = conn or _conexion()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analisis_historico (
                fecha TEXT NOT NULL,
                categoria TEXT NOT NULL,
                documentos INTEGER NOT NULL,
                fuentes_independientes INTEGER NOT NULL,
                confianza REAL NOT NULL,
                nivel TEXT NOT NULL,
                score_medio REAL NOT NULL,
                riesgo REAL NOT NULL,
                creado_en TEXT NOT NULL,
                PRIMARY KEY (fecha, categoria)
            )
            """
        )
        conn.commit()
    finally:
        if propia:
            conn.close()


def guardar_snapshot(hipotesis: list[dict[str, Any]], fecha: str | None = None) -> int:
    """Guarda una foto del estado actual. Devuelve filas escritas.

    Idempotente: reejecutar el mismo día actualiza, no duplica.
    """
    asegurar_tabla()
    fecha = fecha or datetime.now(timezone.utc).date().isoformat()
    ahora = datetime.now(timezone.utc).isoformat()
    conn = _conexion()
    try:
        escritas = 0
        for h in hipotesis:
            conn.execute(
                """
                INSERT OR REPLACE INTO analisis_historico
                (fecha, categoria, documentos, fuentes_independientes,
                 confianza, nivel, score_medio, riesgo, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fecha,
                    h.get("categoria", ""),
                    int(h.get("num_senales", 0)),
                    len(h.get("fuentes", []) or []),
                    float(h.get("confianza", 0.0)),
                    h.get("nivel", ""),
                    float(h.get("score_medio", 0.0)),
                    float(h.get("riesgo", 0.0)),
                    ahora,
                ),
            )
            escritas += 1
        conn.commit()
        return escritas
    finally:
        conn.close()


def tendencias(ventana_dias: int = 30, categoria: str | None = None) -> list[dict[str, Any]]:
    """Calcula la tendencia por categoría comparando el histórico.

    Devuelve, para cada categoría con al menos 2 fechas:
    - `delta_docs`, `delta_confianza`: variación última vs anterior
    - `direccion`: 'sube' | 'baja' | 'estable'
    - `racha`: cuántas mediciones consecutivas van en la misma dirección
    """
    asegurar_tabla()
    conn = _conexion()
    try:
        query = "SELECT * FROM analisis_historico"
        params: list[Any] = []
        if categoria:
            query += " WHERE categoria = ?"
            params.append(categoria)
        query += " ORDER BY categoria, fecha"
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    por_cat: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        por_cat.setdefault(r["categoria"], []).append(r)

    resultados = []
    for cat, serie in por_cat.items():
        if len(serie) < 2:
            continue
        ultima, anterior = serie[-1], serie[-2]
        delta_docs = ultima["documentos"] - anterior["documentos"]
        delta_conf = round(ultima["confianza"] - anterior["confianza"], 3)

        # Rachas: cuántas mediciones seguidas suben o bajan
        racha_subiendo = 0
        for i in range(len(serie) - 1, 0, -1):
            if serie[i]["documentos"] > serie[i - 1]["documentos"]:
                racha_subiendo += 1
            else:
                break

        resultados.append(
            {
                "categoria": cat,
                "fecha_anterior": anterior["fecha"],
                "fecha_ultima": ultima["fecha"],
                "docs_anterior": anterior["documentos"],
                "docs_ultima": ultima["documentos"],
                "delta_docs": delta_docs,
                "delta_confianza": delta_conf,
                "confianza_ultima": ultima["confianza"],
                "direccion": "sube" if delta_docs > 0 else ("baja" if delta_docs < 0 else "estable"),
                "racha_subiendo": racha_subiendo,
                "mediciones": len(serie),
            }
        )

    # Lo que más crece primero: es la señal que interesa
    resultados.sort(key=lambda x: (x["delta_docs"], x["delta_confianza"]), reverse=True)
    return resultados


def serie(categoria: str, limite: int = 60) -> list[dict[str, Any]]:
    """Serie temporal completa de una categoría, para graficar y analizar.

    Devuelve los puntos en orden ASCENDENTE (el más antiguo primero, el más
    reciente al final) porque todos los detectores (delta_diario, cusum,
    rachas, records, temperatura, ensemble) tratan `serie[-1]` como "hoy".
    Antes usaba `ORDER BY fecha DESC`, que invertía el veredicto en cuanto
    había 2+ fechas (fallo crítico encontrado en auditoría).

    Cada punto expone la clave `senal` (conteo de documentos del día) que es
    lo que consumen los detectores; se conserva también `documentos` por
    compatibilidad.
    """
    asegurar_tabla()
    conn = _conexion()
    try:
        rows = conn.execute(
            "SELECT fecha, documentos, fuentes_independientes, confianza, nivel "
            "FROM analisis_historico WHERE categoria = ? ORDER BY fecha ASC LIMIT ?",
            (categoria, limite),
        ).fetchall()
    finally:
        conn.close()
    puntos = []
    for r in rows:
        d = dict(r)
        d["senal"] = d.get("documentos") or 0
        puntos.append(d)
    return puntos


def resumen() -> dict[str, Any]:
    """Resumen del histórico: cobertura y rango temporal."""
    asegurar_tabla()
    conn = _conexion()
    try:
        filas = conn.execute("SELECT COUNT(*) n FROM analisis_historico").fetchone()["n"]
        fechas = conn.execute(
            "SELECT MIN(fecha) primera, MAX(fecha) ultima, COUNT(DISTINCT fecha) dias "
            "FROM analisis_historico"
        ).fetchone()
        cats = conn.execute("SELECT COUNT(DISTINCT categoria) n FROM analisis_historico").fetchone()["n"]
    finally:
        conn.close()
    return {
        "registros": filas,
        "categorias": cats,
        "primera_fecha": fechas["primera"],
        "ultima_fecha": fechas["ultima"],
        "dias_medidos": fechas["dias"],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(resumen(), indent=2, ensure_ascii=False))
    for t in tendencias()[:10]:
        print(f"  {t['categoria']:24} {t['direccion']:6} docs {t['delta_docs']:+d}  conf {t['delta_confianza']:+.3f}")
