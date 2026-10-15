from __future__ import annotations
from typing import Any

# Expansión automática de consulta (Bloque 2 - Sol prioridad #2)
# Mapea términos de entrada a términos REALES del corpus de Noósfera.

# Términos que sí existen en el corpus (verificado por query), por categoría
TERMINOS_CORPUS = {
    "guerra_ucrania": ["ucrania", "rusia", "putin", "guerra", "conflicto", "invasion", "kiev", "zelenski", "donbas", "batalla"],
    "seleccion_espanola": ["seleccion", "espana", "mundial", "futbol", "liga", "gol", "uefa", "cristiano", "messi", "partido", "roja"],
    "bitcoin": ["bitcoin", "btc", "cripto", "ethereum", "blockchain", "satoshi", "wallet", "token", "mineria", "altcoin"],
    "elecciones_eeuu": ["eleccion", "ee.uu", "biden", "trump", "congreso", "senado", "casa blanca", "voto", "urnas", "parlamento"],
    "inflacion_europa": ["europa", "inflacion", "bce", "tipos", "euro", "ecb", "draghi", "energia", "ipc", "precio"],
    "sp500": ["sp500", "nasdaq", "dow", "wall", "bolsa", "acciones", "mercado", "ibex", "street"],
}

# Sinónimos de entrada -> categoría (para detectar intención aunque no estén en corpus)
SINONIMOS_ENTRADA = {
    "votaciones": "elecciones_eeuu",
    "votacion": "elecciones_eeuu",
    "presidencial": "elecciones_eeuu",
    "legislativa": "elecciones_eeuu",
    "subida precios": "inflacion_europa",
    "caro": "inflacion_europa",
    "carestia": "inflacion_europa",
    "cotizacion": "sp500",
    "valores": "sp500",
    "moneda digital": "bitcoin",
    "activo cripto": "bitcoin",
    "activos cripto": "bitcoin",
    "criptomoneda": "bitcoin",
    "frente este": "guerra_ucrania",
    "alto el fuego": "guerra_ucrania",
    "la roja": "seleccion_espanola",
    "equipo nacional": "seleccion_espanola",
}


# Mapa clave: categoria REAL que devuelve el clasificador -> terminos del corpus.
# (TERMINOS_CORPUS usa nombres internos; aqui se enlazan a las cats vivas.)
CATEGORIA_A_TERMINOS = {
    "deportes": "seleccion_espanola",
    "bitcoin": "bitcoin",
    "cripto": "bitcoin",
    "inflacion": "inflacion_europa",
    "precios": "inflacion_europa",
    "elecciones": "elecciones_eeuu",
    "politica": "elecciones_eeuu",
    "guerra": "guerra_ucrania",
    "bolsa": "sp500",
    "mercado": "sp500",
}


def expandir(pregunta: str, categoria: str) -> list[str]:
    """Devuelve términos del corpus para la categoría detectada + sinónimos de entrada."""
    pregunta_l = (pregunta or "").lower()
    terminos: list[str] = []

    # Sinónimos explícitos en la pregunta
    for sin, cat in SINONIMOS_ENTRADA.items():
        if sin in pregunta_l:
            terminos.extend(TERMINOS_CORPUS.get(cat, []))

    # Si categoría detectada, mapear a términos de corpus (clave interna)
    clave = CATEGORIA_A_TERMINOS.get(categoria)
    if clave and clave in TERMINOS_CORPUS:
        terminos.extend(TERMINOS_CORPUS[clave])

    return list(dict.fromkeys(terminos))
