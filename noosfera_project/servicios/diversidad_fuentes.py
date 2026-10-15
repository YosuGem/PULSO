"""
Diversidad real de fuentes (versión 0.2.2-dev).

Para qué sirve
--------------
Con el dedupe arreglado (UNIQUE(texto_hash, fuente)) ahora se puede medir
algo que antes era imposible: **cuántas fuentes independientes publican el
mismo contenido**.

Esa es la señal más fuerte del sistema. Un tema que aparece en 12 fuentes
distintas está emergiendo; el mismo tema en 1 fuente con 40 mensajes es ruido
de un solo sitio. Antes no se podía distinguir porque el segundo caso ni se
guardaba.

Métricas
--------
- `repeticion`: textos idénticos en >=2 fuentes distintas
- `consenso`: fuentes distintas por texto (distribución)
- `concentracion`: cuánto del total aporta la fuente mayor
- `gini`: desigualdad del reparto entre fuentes
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from noosfera_project.servicios.persistencia import DB_PATH
from noosfera_project.deteccion.temas_excluidos import esta_excluido


def _gini(counts: list[int]) -> float:
    """Coeficiente de Gini (0=perfectamente repartido, 1=una fuente lo domina)."""
    if not counts:
        return 0.0
    n = len(counts)
    s = sum(counts)
    if s == 0:
        return 0.0
    cum = sum(i * c for i, c in enumerate(sorted(counts), 1))
    return round((2 * cum) / (n * s) - (n + 1) / n, 4)


def analizar_diversidad(limite: int = 5000) -> dict[str, Any]:
    """Mide la diversidad real de fuentes sobre el corpus.

    Agrupa por `texto_hash`: cada hash con varias fuentes es un contenido
    que se repite de forma independiente.
    """
    import sqlite3

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT texto_hash, fuente, texto FROM lenguaje_colectivo LIMIT ?",
        (limite,),
    ).fetchall()
    con.close()

    if not rows:
        return {"total": 0}

    # fuentes distintas por cada texto
    fuentes_por_hash: dict[str, set[str]] = defaultdict(set)
    texto_por_hash: dict[str, str] = {}
    for r in rows:
        fuentes_por_hash[r["texto_hash"]].add(r["fuente"])
        texto_por_hash.setdefault(r["texto_hash"], r["texto"] or "")

    total_textos = len(fuentes_por_hash)
    repetidos = {h: f for h, f in fuentes_por_hash.items() if len(f) > 1}

    docs_por_fuente = Counter(r["fuente"] for r in rows)

    # Índice de diversidad: cuántas fuentes sostienen el contenido medio
    diversidades = [len(f) for f in fuentes_por_hash.values()]

    return {
        "total_documentos": len(rows),
        "textos_unicos": total_textos,
        "fuentes_activas": len(docs_por_fuente),
        # Contenido publicado de forma independiente por >=2 fuentes
        "contenido_repetido": len(repetidos),
        "pct_repetido": round(100 * len(repetidos) / total_textos, 1),
        # Máximo de fuentes que sostienen un mismo texto
        "max_fuentes_por_texto": max(diversidades) if diversidades else 0,
        "diversidad_media": round(sum(diversidades) / len(diversidades), 2),
        "gini_fuentes": _gini(list(docs_por_fuente.values())),
        "top_fuentes": docs_por_fuente.most_common(8),
        # Los contenidos más respaldados: la señal más fuerte disponible
        "mas_respaldados": sorted(
            (
                {
                    "texto": texto_por_hash[h][:90],
                    "fuentes": sorted(f),
                    "num_fuentes": len(f),
                }
                for h, f in repetidos.items()
            ),
            key=lambda x: x["num_fuentes"],
            reverse=True,
        )[:10],
    }


def diversidad_por_categoria(limite: int = 5000) -> list[dict[str, Any]]:
    """Diversidad de fuentes desglosada por tema.

    Permite comparar temas con criterio común: no cuántas señales tiene,
    sino cuántas fuentes independientes lo sostienen.
    """
    import sqlite3

    from noosfera_project.procesamiento.clasificador_tematico import clasificar

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT fuente, texto FROM lenguaje_colectivo LIMIT ?",
        (limite,),
    ).fetchall()
    con.close()

    fuentes_por_cat: dict[str, set[str]] = defaultdict(set)
    docs_por_cat: Counter = Counter()

    for r in rows:
        cat = clasificar(r["texto"])["categoria"]
        if esta_excluido(cat) or cat == "undetected":
            continue
        fuentes_por_cat[cat].add(r["fuente"])
        docs_por_cat[cat] += 1

    resultados = []
    for cat, fuentes in fuentes_por_cat.items():
        resultados.append(
            {
                "categoria": cat,
                "documentos": docs_por_cat[cat],
                "fuentes_independientes": len(fuentes),
                # Densidad: proporción de fuentes propias que sostienen el tema
                "densidad": round(docs_por_cat[cat] / len(fuentes), 2),
            }
        )
    return sorted(resultados, key=lambda x: x["fuentes_independientes"], reverse=True)


if __name__ == "__main__":
    import json

    print(json.dumps(analizar_diversidad(), indent=2, ensure_ascii=False))
    print()
    print("Diversidad por categoría:")
    for r in diversidad_por_categoria()[:10]:
        print(f"  {r['categoria']:24} docs={r['documentos']:4} fuentes={r['fuentes_independientes']:3} densidad={r['densidad']}")
