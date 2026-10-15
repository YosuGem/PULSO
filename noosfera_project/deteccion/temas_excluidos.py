"""
Temas excluidos del análisis (versión 0.2.2-dev).

Para qué sirve
--------------
Algunas categorías existen en el clasificador por necesidad técnica, no por
interés del análisis. `deportes` es el caso claro: se añadió porque, sin ella,
el 58% del corpus caía en "undetected" (ver STATUS_2026-07-16, Paso 2: los 418
undetected eran 95% predicciones deportivas).

Si se elimina la categoría, ese bloque vuelve a inundar el "sin clasificar" y
tapa lo demás. La solución correcta es seguir detectándola —así el clasificador
sabe descartarla— pero excluirla de las hipótesis, el ranking y los informes.

Regla
-----
Una categoría excluida se sigue calculando, pero no se presenta. El sistema la
usa para saber qué ignorar, no para decirte qué mirar.
"""

from __future__ import annotations

# Categorías detectadas por el clasificador pero fuera del análisis.
# Editable sin tocar código: basta añadir o quitar nombres de aquí.
TEMAS_EXCLUIDOS: set[str] = {
    "deportes",
}


def esta_excluido(categoria: str) -> bool:
    """True si la categoría está excluida del análisis."""
    return (categoria or "").strip().lower() in TEMAS_EXCLUIDOS


def filtrar_excluidos(items: list[dict], clave: str = "categoria") -> list[dict]:
    """Devuelve los items cuya categoría no está excluida."""
    return [it for it in items if not esta_excluido(it.get(clave, ""))]


def excluir_de_grupos(grupos: list[dict]) -> list[dict]:
    """Quita los grupos de temas excluidos."""
    return filtrar_excluidos(grupos, "categoria")
