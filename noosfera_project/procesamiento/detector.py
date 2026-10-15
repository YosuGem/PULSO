"""Detección ampliada de eventos emergentes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


STOPWORDS = {
    "el", "la", "de", "en", "y", "a", "los", "del", "se", "las", "un", "por",
    "con", "no", "una", "su", "para", "es", "al", "lo", "como", "mas", "pero",
    "sus", "le", "ya", "o", "fue", "este", "ha", "porque", "esta", "son",
    "entre", "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta", "hay",
    "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les",
    "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mi",
    "antes", "algunos", "que", "unos", "yo", "otro", "otras", "otra", "el",
    "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual",
    "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "te",
}

PATRONES = [
    ("protesta", r"protestas?|manifestaciones?|disturbios?|paro nacional"),
    ("huelga", r"huelga|huelgas|paro laboral"),
    ("crisis", r"crisis|colapso|derrumbes?|quiebras?"),
    ("guerra", r"guerra|conflicto armado|invasiones?|bombardeos?"),
    ("terremoto", r"terremoto|sismo|seismo|movimientos? teluricos?"),
    ("erupcion", r"erupcion|volcan|columna de ceniza"),
    ("tsunami", r"tsunami|maremoto|ola gigante"),
    ("incendio", r"incendio|incendios|fuego forestal|llamas"),
    ("economia", r"economia|recesion|inflacion|bancos?|mercados?|devaluacion"),
    ("salud", r"virus|epidemia|pandemia|hospital|brote sanitario"),
    ("rescate", r"rescate|ayuda humanitaria|evacuacion"),
    ("desastre", r"desastre|emergencia|alerta roja|alerta amarilla"),
]

# Patrones en ingles (el RSS ingesta feeds EN: BBC, NYT, etc.)
PATRONES_EN = [
    ("protesta", r"protest|demonstration|riot|unrest"),
    ("huelga", r"strike|walkout|labour? dispute"),
    ("crisis", r"crisis|collapse|bankrupt|default"),
    ("guerra", r"war|armed conflict|invasion|missile|strike|bombing|offensive"),
    ("terremoto", r"earthquake|quake|seismic|tremor"),
    ("erupcion", r"eruption|volcano|ash plume"),
    ("tsunami", r"tsunami|tidal wave"),
    ("incendio", r"fire|wildfire|blaze|inferno"),
    ("economia", r"economy|recession|inflation|bank|market|stock|gdp|rate"),
    ("salud", r"virus|epidemic|pandemic|hospital|outbreak"),
    ("rescate", r"rescue|evacuation|humanitarian"),
    ("desastre", r"disaster|emergency|red alert"),
]


def limpiar(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", texto)
    return " ".join(t for t in texto.split() if t not in STOPWORDS and len(t) > 2)


@dataclass
class Evento:
    titulo: str
    publicado: str
    fuente: str
    categorias: str = ""
    puntuacion: float = 0.0
    procesado: int = 0
    limpio: str = ""
    coincidencias: list[str] = field(default_factory=list)

    def normalizar(self) -> dict:
        limpio = limpiar(self.titulo)
        coincidencias = []
        for nombre, patron in PATRONES:
            if re.search(patron, limpio):
                coincidencias.append(nombre)
        self.limpio = limpio
        self.coincidencias = coincidencias
        return {
            "titulo": self.titulo,
            "publicado": self.publicado,
            "fuente": self.fuente,
            "categorias": self.categorias or ",".join(coincidencias),
            "limpio": limpio,
            "coincidencias": coincidencias,
        }


def evaluar(texto: str) -> dict:
    import re
    from noosfera_project.procesamiento.idioma import detectar_idioma
    idioma = detectar_idioma(texto)
    base = limpiar(texto)
    patrones = PATRONES_EN if idioma == "en" else PATRONES
    coincidencias = []
    peso = 0.0
    for nombre, patron in patrones:
        veces = len(re.findall(patron, base))
        if veces:
            coincidencias.append(nombre)
            peso += 0.25 * veces
    return {
        "coincidencias": coincidencias,
        "peso": min(peso, 1.0),
        "texto_limpio": base,
        "idioma": idioma,
    }


def extraer_ubicacion(texto: str) -> str:
    # Heurística simple por capitales y países conocidos
    import unicodedata
    base = unicodedata.normalize("NFKD", (texto or "").lower())
    base = "".join(c for c in base if not unicodedata.combining(c))
    posibles = re.findall(
        r"\b(paris|londres|nueva york|tokio|madrid|mexico|brasilia|buenos aires|lima|bogota|santiago|quito|lahore|teheran|tel aviv|beirut|cairo|johannesburgo|sidney|moscu|kiev|pekin|shanghai|hong kong|nueva delhi|karachi|manila|bangkok|estambul|damasco|bagdad|kinshasa|nairobi|addis abeba|accra|dakar|casablanca|tunez|argel|rabat|oslo|estocolmo|helsinki|copenhague|berlin|roma|viena|bruselas|amsterdam|zurich|varsovia|praga|budapest|atenas|lisboa|dublin|edimburgo|cardiff|belfast|manchester|birmingham|boston|chicago|los angeles|san francisco|seattle|miami|toronto|vancouver|montreal|calgary|ottawa|sao paulo|rio de janeiro|montevideo|asuncion|la paz|caracas|arequipa|trujillo|medellin|cali|bucaramanga|cucuta|ibague|manizales|neiva|popayan|sincelejo|valledupar|monteria|cartagena|barranquilla|quibdo|tumaco|pasto|florencia|leticia|tabatinga|caballo|puerto inirida|caceres|tigre|posadas|corrientes|resistencia|parana|santa fe|rosario|cordoba|mendoza|salta|jujuy|tucuman|la rioja|san juan|san luis|neuquen|bariloche|ushuaia|comodoro rivadavia|rawson|viedma|santa rosa|bahia blanca|mar del plata|la plata)\b",
        base,
        flags=re.IGNORECASE,
    )
    if posibles:
        return posibles[0]
    return "desconocida"
