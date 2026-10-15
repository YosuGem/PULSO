"""Fuentes de entrada para Noósfera.

REGLA: SOLO contenido de redes sociales / foros / gente comun (estilo
lo que piensa la gente comun, sin filtrar).
MEDIOS OFICIALES FUERA (BBC, NYT, CNN, periodico, TV, Reuters...).
ORGANIZACIONES tipo NASA / USGS TAMBIEN FUERA: no son voz de gente comun,
son instituciones. Solo senal de personas reales.
"""

FEED_URLS = []  # sin fuentes RSS: el modulo de eventos se alimenta de redes/foros via lenguaje_colectivo

# Palabras clave para filtrar senales emergentes
EMERGENTE_KEYWORDS = [
    "crisis",
    "protesta",
    "terremoto",
    "erupción",
    "tsunami",
    "huelga",
    "ataque",
    "derrame",
    "ciberataque",
    "alerta sanitaria",
    "restricciones",
    "desastre",
    " emergencia",
    "impacto global",
    "recesión",
    "default",
    "colapso",
]
