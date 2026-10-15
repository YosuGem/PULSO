"""
Guardián de consistencia del clasificador (0.2.2-dev).

Para qué sirve
--------------
Ampliar categorías es fácil; ampliarlas **sin romper las existentes** es lo
difícil. El fallo real que ya ocurrió: `energia` y `energia_renovable`
compartían los tokens `solar` y `eolica`, así que "paneles solares" seguía
cayendo en la categoría genérica y la nueva no servía para nada.

Este módulo lo detecta antes de que llegue al corpus.

Reglas que verifica
-------------------
1. Un token vive en UNA sola categoría (si no, el empate lo resuelve el
   orden del diccionario, que es arbitrario).
2. Ninguna categoría se queda sin tokens.
3. Ninguna frase vive en dos categorías.

Uso:
    python -m noosfera_project.procesamiento.guardian_categorias
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from noosfera_project.procesamiento.clasificador_tematico import CATEGORIAS


def tokens_duplicados() -> dict[str, list[str]]:
    """Tokens presentes en más de una categoría.

    Devuelve {token: [categorias...]} solo para los que están duplicados.
    """
    duplicados: dict[str, list[str]] = defaultdict(list)
    for cat, cfg in CATEGORIAS.items():
        for tok in cfg["tokens"]:
            if cat not in duplicados[tok]:
                duplicados[tok].append(cat)
    return {t: cats for t, cats in duplicados.items() if len(cats) > 1}


def frases_duplicadas() -> dict[str, list[str]]:
    """Frases presentes en más de una categoría."""
    duplicados: dict[str, list[str]] = defaultdict(list)
    for cat, cfg in CATEGORIAS.items():
        for fr in cfg.get("frases", []):
            if cat not in duplicados[fr]:
                duplicados[fr].append(cat)
    return {f: cats for f, cats in duplicados.items() if len(cats) > 1}


def categorias_vacias() -> list[str]:
    """Categorías sin tokens (no pueden clasificar nada)."""
    return [cat for cat, cfg in CATEGORIAS.items() if not cfg.get("tokens")]


def revisar() -> dict[str, Any]:
    """Revisión completa. Devuelve el informe de consistencia."""
    return {
        "total_categorias": len(CATEGORIAS),
        "tokens_duplicados": tokens_duplicados(),
        "frases_duplicadas": frases_duplicadas(),
        "categorias_vacias": categorias_vacias(),
    }


def es_consistente() -> bool:
    """True si el clasificador pasa todas las reglas."""
    r = revisar()
    return not (r["tokens_duplicados"] or r["frases_duplicadas"] or r["categorias_vacias"])


def proponer_dueno(token: str) -> str:
    """Ante un token duplicado, sugiere qué categoría debería quedárselo.

    Criterio: la categoría más específica —la que tiene menos tokens—, porque
    un token raro dentro de una categoría pequeña es más informativo que uno
    genérico dentro de una categoría amplia.
    """
    dups = tokens_duplicados()
    if token not in dups:
        return ""
    return min(dups[token], key=lambda c: len(CATEGORIAS[c]["tokens"]))


if __name__ == "__main__":
    r = revisar()
    print(f"Categorías: {r['total_categorias']}")
    if r["tokens_duplicados"]:
        print("\nTOKENS DUPLICADOS (deben vivir en una sola categoría):")
        for tok, cats in sorted(r["tokens_duplicados"].items()):
            print(f"  '{tok}' -> {cats}   (sugerido: {proponer_dueno(tok)})")
    if r["frases_duplicadas"]:
        print("\nFRASES DUPLICADAS:")
        for fr, cats in sorted(r["frases_duplicadas"].items()):
            print(f"  '{fr}' -> {cats}")
    if r["categorias_vacias"]:
        print(f"\nCATEGORÍAS VACÍAS: {r['categorias_vacias']}")
    if es_consistente():
        print("\n✅ Clasificador consistente.")
