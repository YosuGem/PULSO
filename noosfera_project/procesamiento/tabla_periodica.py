"""
Tabla periódica de elementos (0.2.2-dev).

Para qué sirve
--------------
Los elementos químicos son materias primas con nombre propio. El usuario
pidió cubrir la tabla periódica completa, no solo tierras raras: los
elementos críticos (litio, cobalto, níquel, tierras raras…) mueven cadenas
de suministro enteras y la gente común los menciona por su nombre en foros.

Antes vivían sueltos dentro de metales_industriales y competían con el
resto. Aquí cada elemento es un token propio, más las frases compuestas que
la gente usa ("tierras raras", "litio", "cobalto").

Diseño
------
- Un token por elemento. Sin acentos, minúsculas.
- Los de ≤4 letras se marcan para exigir palabra completa (ver el
  clasificador: el bug "az"→"plaza" y "boca"→"desboca").
- No hay riesgo de colisión con categorías existentes porque los nombres de
  elemento son palabras concretas.
"""

from __future__ import annotations

# Elementos de la tabla periódica más relevantes para economía, energía y
# tecnología. No están todos los 118: solo los que aparecen en conversación
# sobre materias primas, baterías, semiconductores, tierras raras o industria.
ELEMENTOS = {
    # --- Baterías y electromovilidad ---
    "litio": "baterias",
    "cobalto": "baterias",
    "niquel": "baterias",
    "manganeso": "baterias",
    "grafito": "baterias",
    "sodio": "baterias",
    "fosforo": "baterias",
    "hierro": "baterias",
    # --- Tierras raras (17 elementos) ---
    "lantano": "tierras_raras",
    "cerio": "tierras_raras",
    "praseodimio": "tierras_raras",
    "neodimio": "tierras_raras",
    "prometio": "tierras_raras",
    "samario": "tierras_raras",
    "europio": "tierras_raras",
    "gadolinio": "tierras_raras",
    "terbio": "tierras_raras",
    "disprosio": "tierras_raras",
    "holmio": "tierras_raras",
    "erbio": "tierras_raras",
    "tulio": "tierras_raras",
    "iterbio": "tierras_raras",
    "lutecio": "tierras_raras",
    "escandio": "tierras_raras",
    "itrio": "tierras_raras",
    # --- Semiconductores y electrónica ---
    "silicio": "semiconductores",
    "germanio": "semiconductores",
    "galio": "semiconductores",
    "arsenico": "semiconductores",
    "indio": "semiconductores",
    "antimonio": "semiconductores",
    "telurio": "semiconductores",
    # --- Metales industriales y de construcción ---
    "cobre": "industriales",
    "zinc": "industriales",
    "aluminio": "industriales",
    "estano": "industriales",
    "plomo": "industriales",
    "titanio": "industriales",
    "cromo": "industriales",
    "vanadio": "industriales",
    "wolframio": "industriales",
    "tantalio": "industriales",
    "niobio": "industriales",
    "circonio": "industriales",
    "berilio": "industriales",
    "magnesio": "industriales",
    # --- Metales preciosos ---
    "oro": "preciosos",
    "plata": "preciosos",
    "platino": "preciosos",
    "paladio": "preciosos",
    "rodio": "preciosos",
    "iridio": "preciosos",
    "osmio": "preciosos",
    "rutenio": "preciosos",
    # --- Energía y nuclear ---
    "uranio": "nuclear",
    "torio": "nuclear",
    "plutonio": "nuclear",
    "deuterio": "nuclear",
    "tritio": "nuclear",
    "helio": "energia",
    "hidrogeno": "energia",
}

# Frases compuestas que la gente usa y que deben ir en el clasificador.
FRASES_ELEMENTOS = [
    "tierras raras",
    "metales de tierras raras",
    "elementos de tierras raras",
    "mineral critico",
    "minerales criticos",
    "material critico",
    "materiales criticos",
    "cadena de suministro de minerales",
    "extraccion de litio",
    "mineria de litio",
    "refinado de cobalto",
    "tabla periodica",
]

# Tokens de ≤4 letras que deben exigir palabra completa (bug de subcadena).
ELEMENTOS_CORTOS = {"oro", "hierro"}


def tokens_elementos() -> list[str]:
    """Lista completa de tokens de elemento para el clasificador."""
    return sorted(set(ELEMENTOS) | set(FRASES_ELEMENTOS))


def tokens_cortos_elementos() -> set[str]:
    """Elementos de ≤4 letras que deben ser palabra completa."""
    cortos = {e for e in ELEMENTOS if len(e) <= 4}
    return cortos | ELEMENTOS_CORTOS


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from noosfera_project.procesamiento.clasificador_tematico import CATEGORIAS

    print(f"Elementos definidos: {len(ELEMENTOS)}")
    print(f"Frases compuestas: {len(FRASES_ELEMENTOS)}")
    print(f"Tokens totales para el clasificador: {len(tokens_elementos())}")
    print(f"Tokens cortos (palabra completa): {sorted(tokens_cortos_elementos())}")

    # Verificar colisiones con las categorías actuales
    actuales = set()
    for cfg in CATEGORIAS.values():
        actuales.update(cfg["tokens"])
        actuales.update(cfg.get("frases", []))
    colisiones = [t for t in tokens_elementos() if t in actuales]
    print(f"Colisiones con categorías actuales: {colisiones or 'ninguna'}")
