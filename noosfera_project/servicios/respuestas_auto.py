"""Respuestas automáticas para el visor chat."""

from __future__ import annotations

CASOS = [
    {
        "claves": ["crisis", "protesta", "huelga", "guerra"],
        "respuesta": "Señal emergente detectada: crisis/protesta/huelga/guerra.",
    },
    {
        "claves": ["terremoto", "erupcion", "tsunami", "incendio"],
        "respuesta": "Señal geofísica detectada: terremoto/erupción/tsunami/incendio.",
    },
    {
        "claves": ["economia", "mercado", "recesion", "inflacion", "bancos"],
        "respuesta": "Señal económica detectada: mercado/recesión/inflación/bancos.",
    },
    {
        "claves": ["salud", "virus", "epidemia", "pandemia", "hospital"],
        "respuesta": "Señal sanitaria detectada: virus/epidemia/pandemia/hospital.",
    },
]


def responder(texto: str) -> str:
    t = texto.lower()
    for caso in CASOS:
        if any(c in t for c in caso["claves"]):
            return caso["respuesta"]
    return "Sin señal emergente clara en la consulta."
