"""Detección y normalización de idioma multi-clase (Bloque A).

Idiomas soportados: es, en, fr, de, pt.
Heurística: marcas léxicas + stopwords + caracteres específicos.
"""
from __future__ import annotations

from typing import Any

STOPWORDS = {
    "es": {
        "el", "la", "de", "en", "y", "a", "los", "del", "se", "las", "un", "por",
        "con", "no", "una", "su", "para", "es", "al", "lo", "como", "mas", "pero",
        "sus", "le", "ya", "o", "fue", "este", "ha", "porque", "esta", "son",
        "entre", "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta", "hay",
        "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les",
        "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mi",
    },
    "en": {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
        "with", "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "should", "can", "could",
        "this", "that", "these", "those", "it", "its", "they", "them", "their",
        "we", "you", "your", "he", "she", "his", "her", "not", "no", "yes", "if",
        "then", "than", "so", "as", "by", "from", "about", "into", "over", "after",
    },
    "fr": {
        "le", "la", "les", "de", "des", "du", "et", "est", "une", "un", "en", "que",
        "qui", "dans", "pour", "avec", "au", "aux", "sur", "par", "pas", "son", "sa",
        "ces", "ce", "cette", "ils", "elles", "nous", "vous", "leur", "oui", "non",
        "mais", "donc", "car", "comme", "vers", "entre", "sans", "pourquoi", "quand",
    },
    "de": {
        "der", "die", "das", "und", "ist", "ein", "eine", "in", "den", "von", "zu",
        "mit", "auf", "fur", "nicht", "sein", "ihre", "einen", "dem", "werden", "aus",
        "er", "es", "sie", "ich", "wir", "ihr", "auch", "als", "an", "nach", "bei",
        "um", "sondern", "oder", "aber", "doch", "war", "wird", "hat", "haben",
    },
    "pt": {
        "o", "a", "os", "as", "de", "da", "do", "e", "é", "um", "uma", "no", "na",
        "em", "que", "para", "com", "por", "se", "nao", "sao", "dos", "das", "este",
        "esta", "um", "você", "ele", "ela", "nos", "eles", "elas", "sim", "nao",
        "mas", "como", "quando", "onde", "porque", "pelos", "pelas", "aos", "ate",
    },
}

# Marcas léxicas que no existen en otros idiomas (palabras claras)
MARCAS = {
    "es": ["bitcoin", "precio", "elecciones", "inflacion", "mercado", "seleccion", "mundial", "cripto", "bolsa", "economia", "crisis", "guerra", "ucrania"],
    "en": ["bitcoin", "price", "war", "us", "inflation", "market", "world", "crypto", "ukraine", "prediction", "economy", "stock", "grows", "rising", "team", "national", "earthquake", "tsunami", "strike", "fire", "offensive", "russia", "trump", "election"],
    "fr": ["bitcoin", "prix", "guerre", "elections", "inflation", "marche", "monde", "crypto", "ukraine", "prediction", "equipe", "france", "economie", "hausse", "croist"],
    "de": ["bitcoin", "preis", "krieg", "wahlen", "inflation", "markt", "welt", "krypto", "ukraine", "prognose", "aktienmarkt", "wirtschaft", "wachst", "steigen", "nationalmannschaft"],
    "pt": ["bitcoin", "preco", "guerra", "ucrania", "eleicoes", "inflacao", "mercado", "mundo", "cripto", "previsao", "selecao", "acoes", "economia", "cresce", "alta", "criptomoedas"],
}

CARACTERES = {
    "es": "áéíóúñü",
    "fr": "àâçéèêëîïôùûüÿñ",
    "de": "äöüß",
    "pt": "áâãçéêíóôõúüñ",
    "en": "",
}


def detectar_idioma(texto: str) -> str:
    """Detección multi-clase ES/EN/FR/DE/PT."""
    t = (texto or "").lower()
    tl = f" {t} "

    # Conteo de características por idioma
    scores: dict[str, int] = {}
    for lang in ("es", "en", "fr", "de", "pt"):
        score = 0
        # Stopwords
        score += sum(1 for w in STOPWORDS[lang] if f" {w} " in tl)
        # Marcas léxicas
        score += 2 * sum(1 for w in MARCAS[lang] if f" {w} " in tl or f"{w} " in t)
        # Caracteres específicos
        score += 3 * sum(1 for c in t if c in CARACTERES[lang])
        scores[lang] = score

    # Ordenar por score
    ordenado = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    mejor_lang, mejor_score = ordenado[0]

    # Si hay empate o score 0, default es
    if mejor_score == 0:
        return "es"
    # Si el segundo está cerca (dentro de 1), preferir ES por ser corpus base
    # EXCEPTO si el mejor idioma tiene marca léxica clara (score >= 2)
    if ordenado[1][1] >= mejor_score - 1 and mejor_lang != "es":
        if mejor_score >= 2:
            return mejor_lang
        return "es"
    return mejor_lang


def limpiar_por_idioma(texto: str, idioma: str = "es") -> str:
    """Normaliza respetando stopwords del idioma detectado o forzado."""
    import re
    if idioma not in STOPWORDS:
        idioma = detectar_idioma(texto)
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9áéíóúñüàâçèêëîïôùûÿäöüßãõ\s]", " ", texto)
    stop = STOPWORDS.get(idioma, STOPWORDS["es"])
    tokens = [tk for tk in texto.split() if tk not in stop and len(tk) > 2]
    return " ".join(tokens)


def idiomas_soportados() -> list[str]:
    return ["es", "en", "fr", "de", "pt"]
