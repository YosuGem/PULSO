"""Explorador de descubrimiento autónomo (Bloque E).

Detecta temas emergentes no cubiertos por las 6 categorías core y sugiere
nuevas categorías desde clusters de señales no clasificadas.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from noosfera_project.procesamiento.clasificador_tematico import clasificar, CATEGORIAS
from noosfera_project.deteccion.pipeline import ejecutar_pipeline

# Palabras que indican tema emergente (no en categorías core)
MARCAS_EMERGENTE = [
    "ia", "inteligencia artificial", "robot", "quantum", "cuántica", "clima",
    "sequia", "inundacion", "terremoto", "virus", "pandemia", "vacuna",
    "energia", "nuclear", "petroleo", "migracion", "refugiados", "protesta",
    "huelga", "elecciones", "gobierno", "congreso", "senado", "banco central",
    "inflation", "recession", "stagflation", "supply chain", "chip", "semiconductor",
]


def explorar(textos: list[dict[str, Any]], umbral_no_clasificado: int = 10) -> dict[str, Any]:
    """Analiza corpus y reporta temas no cubiertos y emergentes."""
    no_clasificados = []
    categorias: Counter = Counter()
    marcas_encontradas: Counter = Counter()
    for t in textos:
        txt = (t.get("texto", "") or "").lower()
        cat = clasificar(t.get("texto", ""))
        categorias[cat["categoria"]] += 1
        if cat["categoria"] == "undetected":
            no_clasificados.append(t)
        # Substring sobre el texto completo (no solo tokens) para marcas multi-palabra
        for marca in MARCAS_EMERGENTE:
            if marca in txt:
                marcas_encontradas[marca] += 1

    # Sugerir nuevas categorías SOLO desde marcas NO cubiertas por las actuales.
    #
    # Antes se excluía cualquier marca que apareciera como token de una categoría
    # existente, pero "ia" y "clima" SÍ son tokens de inteligencia_artificial y
    # clima_medioambiente. El explorador se canibalizaba: todo lo emergente ya
    # estaba catalogado, así que nunca sugería nada.
    #
    # Criterio actual: una marca es sugerible si el corpus tiene textos SIN
    # clasificar (no_clasificados > 0) o si la marca no es un token propio de
    # ninguna categoría. Es decir, se sugiere el tema aunque la palabra exista
    # como token, porque lo relevante es si ya hay una categoría que lo cubra
    # con nombre propio, no si la palabra suelta aparece en su lista.
    nombres_categorias = {k.lower() for k in CATEGORIAS.keys()}
    tokens_ocupados = set()
    for cfg in CATEGORIAS.values():
        tokens_ocupados.update(t.lower() for t in cfg["tokens"])
    tokens_ocupados.update(nombres_categorias)

    hay_sin_clasificar = len(no_clasificados) > 0
    sugerencias = [
        {"tema_sugerido": m, "frecuencia": c}
        for m, c in marcas_encontradas.most_common(10)
        if c >= 1 and (m.lower() not in tokens_ocupados or hay_sin_clasificar)
    ]

    total = len(textos)
    pct_no_clas = round(100 * len(no_clasificados) / total, 1) if total else 0.0

    return {
        "total_textos": total,
        "no_clasificados": len(no_clasificados),
        "pct_no_clasificado": pct_no_clas,
        "categorias_unicas": len(categorias),
        "distribucion_categorias": dict(categorias.most_common()),
        "temas_emergentes_detectados": len(marcas_encontradas),
        "sugerencias_categoria": sugerencias,
        "necesita_nueva_categoria": (
            len(no_clasificados) >= umbral_no_clasificado
            or len(sugerencias) >= 1
        ),
    }


def descubrir_desde_pipeline(textos: list[dict[str, Any]]) -> dict[str, Any]:
    """Usa el pipeline de detección para alimentar hipótesis de temas nuevos."""
    out = ejecutar_pipeline(textos, umbral_grupo=3)
    grupos_undetected = [
        g for g in out["grupos"]
        if g["categoria"] == "undetected" and g["num_senales"] >= 5
    ]
    return {
        "hipotesis_generadas": out["total_hipotesis"],
        "grupos_sin_clasificar": len(grupos_undetected),
        "grupos": grupos_undetected[:5],
    }


if __name__ == "__main__":
    import sqlite3, json
    from pathlib import Path
    DB = Path(__file__).resolve().parents[1] / "eventos.db"
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, fuente, texto, idioma FROM lenguaje_colectivo").fetchall()
    conn.close()
    textos = [dict(r) for r in rows]
    print(json.dumps(explorar(textos), indent=2, ensure_ascii=False))
