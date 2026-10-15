"""Evaluación de fuentes (Bloque D - ampliado con persistencia y Gini).

Mide diversidad, independencia (Gini), reputación y persistencia temporal.
Persiste resultados en tabla `fuentes_evaluadas`.

REGLA: NO hay whitelist de "fuentes conocidas". Los medios de comunicacion
y organizaciones (periódicos, televisiones, agencias) ESTAN FUERA del
programa (no son voz de gente comun). La reputacion se mide por utilidad
graduada real, no por una lista fija de medios.
"""
from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

DB = Path(__file__).resolve().parents[1] / "eventos.db"


def _gini(counts: list[int]) -> float:
    """Coeficiente de Gini de una distribución de conteos (0=igual, 1=desigual)."""
    if not counts:
        return 0.0
    n = len(counts)
    s = sum(counts)
    if s == 0:
        return 0.0
    sorted_c = sorted(counts)
    cum = 0
    for i, c in enumerate(sorted_c, 1):
        cum += i * c
    # Fórmula Gini
    return round((2 * cum) / (n * s) - (n + 1) / n, 4)


def _utilidad_por_fuente(rows: list[sqlite3.Row]) -> Counter:
    """Cuenta docs de cada fuente que caen en categoría REAL (no undetected)."""
    from noosfera_project.procesamiento.clasificador_tematico import clasificar
    util = Counter()
    for r in rows:
        if clasificar(r["texto"])["categoria"] != "undetected":
            util[r["fuente"]] += 1
    return util


def evaluar() -> dict[str, Any]:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    # Filtrar documentacion filtrada en el corpus (nombres de archivo .md/.txt)
    rows = conn.execute(
        "SELECT fuente, idioma, publicado, creado_en, texto FROM lenguaje_colectivo "
        "WHERE fuente NOT LIKE '%.md' AND fuente NOT LIKE '%.txt'"
    ).fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return {"total": 0}

    fuentes = Counter(r["fuente"] for r in rows)
    num_fuentes = len(fuentes)

    # Independencia: 1 - (max_count / total)
    max_count = max(fuentes.values())
    independencia = round(1.0 - (max_count / total), 3)

    # Gini real de distribución
    gini = _gini(list(fuentes.values()))

    # Reputación graduada: fracción de docs de la fuente que caen en categoría REAL
    # (no undetected) -> señal útil, no depende de whitelist estático
    util_por_fuente = _utilidad_por_fuente(rows)
    reputacion_media = round(
        sum(util_por_fuente[f] / n for f, n in fuentes.items()) / num_fuentes, 3
    ) if num_fuentes else 0.0

    # Persistencia: docs con fecha válida (no solo la de ingesta de muestra)
    con_fecha = sum(1 for r in rows if r["publicado"] or (r["creado_en"] or "")[:10] != "2026-07-16")
    persistencia = round(con_fecha / total, 3)

    return {
        "total": total,
        "num_fuentes": num_fuentes,
        "top_fuentes": fuentes.most_common(5),
        "independencia": independencia,
        "gini": gini,
        "reputacion_docs_utiles": reputacion_media,
        "persistencia_temporal": persistencia,
        "idiomas": dict(Counter(r["idioma"] for r in rows if r["idioma"])),
    }


def persistir() -> int:
    """Calcula evaluación y la guarda en tabla `fuentes_evaluadas` (una fila por fuente).

    Usa UPSERT (INSERT OR REPLACE por fuente) para no duplicar filas en ejecuciones repetidas.
    """
    from datetime import datetime
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    # Recrear tabla con esquema actual (fuente como PK) para no acumular esquemas viejos
    conn.execute("DROP TABLE IF EXISTS fuentes_evaluadas")
    conn.execute(
        """
        CREATE TABLE fuentes_evaluadas (
            fuente TEXT PRIMARY KEY,
            num_docs INTEGER,
            reputacion REAL,
            evaluado_en TEXT NOT NULL
        )
        """
    )
    ts = datetime.utcnow().isoformat()
    rows = conn.execute(
        "SELECT fuente, COUNT(*) c FROM lenguaje_colectivo "
        "WHERE fuente NOT LIKE '%.md' AND fuente NOT LIKE '%.txt' GROUP BY fuente"
    ).fetchall()
    # Leer textos para calcular utilidad (reputación graduada) por fuente
    conn2 = sqlite3.connect(DB)
    conn2.row_factory = sqlite3.Row
    textos = conn2.execute(
        "SELECT fuente, texto FROM lenguaje_colectivo "
        "WHERE fuente NOT LIKE '%.md' AND fuente NOT LIKE '%.txt'"
    ).fetchall()
    conn2.close()
    util = _utilidad_por_fuente(textos)
    count = 0
    for r in rows:
        repu = round(util[r[0]] / r[1], 3) if r[1] else 0.0
        conn.execute(
            "INSERT OR REPLACE INTO fuentes_evaluadas (fuente, num_docs, reputacion, evaluado_en) "
            "VALUES (?,?,?,?)",
            (r[0], r[1], repu, ts),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


if __name__ == "__main__":
    import json
    print(json.dumps(evaluar(), indent=2, ensure_ascii=False))
    n = persistir()
    print(f"Persistidas {n} fuentes en fuentes_evaluadas")
