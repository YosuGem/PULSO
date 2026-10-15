"""Normalización lingüística para lenguaje colectivo."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
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


STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "should", "can", "could",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "you", "your", "he", "she", "his", "her", "not", "no", "yes", "if",
    "then", "than", "so", "as", "by", "from", "about", "into", "over", "after",
}


def _contiene_palabra(t: str, w: str) -> bool:
    """True si w aparece como palabra completa (no como subcadena).

    Fija el bug de bordes: f" {w} " no matchea la primera ni la última
    palabra del texto.
    """
    t = f" {t} "
    pos = t.find(f" {w} ")
    while pos != -1:
        final = pos + len(w) + 1
        if final >= len(t) or not (t[final].isalnum() or t[final] == "_"):
            return True
        pos = t.find(f" {w} ", final)
    return False


def detectar_idioma(texto: str) -> str:
    """Detección básica ES/EN por stopwords y caracteres."""
    t = (texto or "").lower()
    es_chars = sum(1 for c in t if c in "áéíóúñü")
    es_stop = sum(1 for w in STOPWORDS if _contiene_palabra(t, w))
    en_stop = sum(1 for w in STOPWORDS_EN if _contiene_palabra(t, w))
    # Palabras EN claras que no existen en ES
    en_marcas = ["the", "is", "are", "was", "were", "will", "would", "could", "should", "this", "that", "with", "from", "about", "price", "prediction", "war", "elections", "inflation", "record"]
    en_marcas_hit = sum(1 for w in en_marcas if _contiene_palabra(t, w))
    if es_chars > 0 or (es_stop > en_stop and en_marcas_hit == 0):
        return "es"
    if en_stop > 0 or en_marcas_hit > 0:
        return "en"
    return "es"  # default


# Siglas cortas legítimas que el filtro de longitud NO debe descartar.
SIGLAS_CORTAS = {
    "ia", "ai", "ee", "uu", "ue", "bce", "fmi", "onu", "otan", "pib",
    "ipc", "irpf", "iva", "smi", "bc", "boe", "snp", "uk", "us", "eu",
}


def limpiar_por_idioma(texto: str, idioma: str = "es") -> str:
    """Normaliza respetando stopwords del idioma."""
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9áéíóúüñ\s]", " ", texto)
    stop = STOPWORDS if idioma == "es" else STOPWORDS_EN
    # len > 2 descartaba "ia"; se conservan las siglas cortas legitimas.
    tokens_list = [
        tk for tk in texto.split()
        if tk not in stop and (len(tk) > 2 or tk in SIGLAS_CORTAS)
    ]
    return " ".join(tokens_list)


def tokens(texto: str) -> list[str]:
    limpio = limpiar_por_idioma(texto, idioma="es")
    return limpio.split()


@dataclass
class PerfilTemporal:
    etiqueta: str
    documentos: int = 0
    frecuencia: dict[str, int] = field(default_factory=dict)
    textos_crudos: list[str] = field(default_factory=list)

    def add(self, texto: str) -> None:
        self.documentos += 1
        self.textos_crudos.append(texto)
        for token in tokens(texto):
            self.frecuencia[token] = self.frecuencia.get(token, 0) + 1

    def top(self, n: int = 20) -> list[tuple[str, int]]:
        return sorted(self.frecuencia.items(), key=lambda x: (x[1], x[0]), reverse=True)[:n]


def perfiles_por_fuente(documentos: list[dict[str, Any]]) -> dict[str, PerfilTemporal]:
    """Agrupa textos por fuente y devuelve perfiles de frecuencia."""
    perfiles: dict[str, PerfilTemporal] = {}
    for doc in documentos:
        fuente = doc.get("fuente") or "desconocida"
        texto = doc.get("texto") or ""
        if not texto:
            continue
        perfil = perfiles.setdefault(fuente, PerfilTemporal(etiqueta=fuente))
        perfil.add(texto)
    return perfiles


def perfiles_por_dia(documentos: list[dict[str, Any]]) -> dict[str, PerfilTemporal]:
    """Agrupa textos por día (fecha 00:00). Usa 'publicado' o 'creado_en'."""
    perfiles: dict[str, PerfilTemporal] = {}
    for doc in documentos:
        fecha = (doc.get("publicado") or doc.get("creado_en") or "")[:10]
        if not fecha:
            continue
        texto = doc.get("texto") or ""
        if not texto:
            continue
        perfil = perfiles.setdefault(fecha, PerfilTemporal(etiqueta=fecha))
        perfil.add(texto)
    return perfiles


def estadisticas_generales(documentos: list[dict[str, Any]]) -> dict[str, Any]:
    """Devuelve métricas generales del corpus."""
    textos = [doc.get("texto") or "" for doc in documentos if doc.get("texto")]
    num_docs = len(textos)
    num_tokens = sum(len(tokens(t)) for t in textos)
    longitud_media = num_tokens / num_docs if num_docs else 0.0
    todas = Counter()
    for t in textos:
        for tok in tokens(t):
            todas[tok] += 1
    return {
        "documentos": num_docs,
        "tokens_totales": num_tokens,
        "longitud_media": round(longitud_media, 2),
        "top_20": todas.most_common(20),
    }
