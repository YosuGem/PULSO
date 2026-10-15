"""Exportación JSON con filtros (Bloque G - G1)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB = Path(__file__).resolve().parents[1] / "eventos.db"


def exportar_json(
    limite: int = 200,
    idioma: str | None = None,
    fuente: str | None = None,
    ruta_salida: str | Path | None = None,
) -> dict[str, Any]:
    """Exporta eventos filtrados por idioma/fuente a JSON."""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    sql = (
        "SELECT id, fuente, texto, idioma, publicado, creado_en FROM lenguaje_colectivo "
        "WHERE fuente NOT LIKE '%.md' AND fuente NOT LIKE '%.txt'"
    )
    condiciones = []
    params: list[Any] = []
    if idioma:
        condiciones.append("idioma = ?")
        params.append(idioma)
    if fuente:
        condiciones.append("fuente = ?")
        params.append(fuente)
    if condiciones:
        sql += " AND " + " AND ".join(condiciones)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limite)
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    from noosfera_project.procesamiento.clasificador_tematico import clasificar
    docs = []
    for r in rows:
        d = dict(r)
        d["categoria"] = clasificar(r["texto"])["categoria"]
        docs.append(d)
    if ruta_salida:
        p = Path(ruta_salida)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "documentos": len(docs), "idioma": idioma, "fuente": fuente}


if __name__ == "__main__":
    print(json.dumps(exportar_json(limite=10, idioma="en"), indent=2, ensure_ascii=False))
