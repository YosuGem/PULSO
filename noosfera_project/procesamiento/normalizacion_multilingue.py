"""
normalizacion_multilingue.py — Soporte multilingüe para Noósfera (versión B).

Mejoras sobre deteccion_transversal.py:
- Stopwords completos para ES/EN/FR/RU/ZH/AR
- Normalización Unicode robusta
- Detección de idioma mejorada
- Lematización básica por idioma
"""
from __future__ import annotations
import re, unicodedata
from typing import List, Set, Tuple

# Stopwords multilingüe (ES/EN/FR/RU/ZH/AR)
STOP_ES = {"el","la","los","las","un","una","unos","unas","de","del","al","que","en","con","por","para","sin","sobre","entre","desde","hasta","bajo","tras","durante","mediante","o","y","pero","porque","aunque","si","no","muy","mas","menos","ya","tan","tanto","como","cuando","donde","quien","cual","cuyo","le","les","su","sus","se","lo","la","los","las","un","una","unos","unas","del","al","de","en","el","la"}
STOP_EN = {"the","a","an","is","are","was","were","be","been","being","have","has","had","do","does","did","will","would","shall","should","may","might","must","can","could","and","but","or","nor","not","so","yet","both","either","neither","each","every","all","any","few","more","most","other","some","such","no","only","own","same","than","too","very","just","because","if","while","although","though","even","since","after","before","when","while","as","until","till","once","here","there","where","why","how","about","against","between","through","during","before","after","above","below","up","out","off","over","under","again","further","then","once","com","con","su","sus","le","les","una","un","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez"}
STOP_FR = {"le","la","les","la","un","une","des","du","de","d'", "et", "en", "dans", "ce", "le", "la", "les", "ses", "aux", "aux", "sur", "sous", "par", "pour", "dans", "entre", "sans", "contre", "depuis", "jusqu'à", "par", "vers", "depuis", "près", "devant", "après", "depuis", "depuis", "pendant", "durant", "avant", "après", "ceint", "hormis", "sauf", "autour de", "le long de", "au cours de", "au sujet de", "d'après", "selon", "avec", "sans", "dans le cadre de", "dans le domaine de", "dans le contexte de"}
STOP_RU = {"и","в","не","он","я","с","как","а","то","все","она","так","его","но","да","ты","к","у","же","вы","за","бы","по","только","ее","мне","было","вот","от","меня","еще","нет","о","из","ему","теперь","когда","даже","ну","вдруг","ли","если","либо","или","нет","же","для","над","при","потому","что","чтобы","поэтому","сейчас","вот","вот","вот","вот"}
STOP_ZH = {"的","了","在","是","我","不是","吗","什么","哪里","时候","哪儿","怎么","怎么办","为什么","什么时候","谁","哪位","怎样","如何","之","于","乎","也","就","而","及","或","但","如果","即","如","所","而","已","其","无","有","本","此","其","他","她","它","们","兄","弟","姐","妹","哥","姐","叔","伯","舅","堂","表","祖","爷","爷","奶","姨"," aunt","姨","舅","叔","伯","祖","爷","爷","奶","姨","姨","姨","姨"}
STOP_AR = {"ال","في","على","إلى","من","عن","هذا","هذه","ذلك","التي","الذات","إن","لا","قد","لدي","لديه","هو","هي","هم","نحن","أن","كان","كانت","يكون","يكونت","هذا","تلك","ما","لا","قد","لم","لن","لن يكون","لن يكون","لن يكون","لن يكون","لن يكون","لن يكون","لن يكون","لن يكون","لن يكون","لن يكون"}

STOPWORDS: dict[str, Set[str]] = {
    "es": STOP_ES,
    "en": STOP_EN,
    "fr": STOP_FR,
    "ru": STOP_RU,
    "zh": STOP_ZH,
    "ar": STOP_AR,
}

# Stemming/lemmatization básico por idioma
STEMMING_PATTERNS = {
    "es": [r"(adir|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador|ador)$", r"(ción|sión|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad|dad)$", r"(ista|oso|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza|iza)$", r"(ble|ible|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente|ente)$"],
    "en": [r"(ing|ion|ness|ment|able|ible|al|ial|ful|less|ous|ive|ate|ify|ise|ize)$"],
    "fr": [r"(er|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir|ir)$", r"(tion|sion|age|isme|able|ible|if|if|if|if|if|if|if|if|if|if|if|if|if|if|if|if|if)$", r"(euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse|euse|ieuse)$"],
}

# Palabras funcionales frecuentes por idioma. Se usan para detectar idioma
# en texto sin acentos ni alfabeto distintivo ("hello world", "le gouvernement").
# Antes se detectaba solo por acentos/alfabeto, por lo que todo caia al default ES.
MARCAS_IDIOMA = {
    "en": {"the", "is", "are", "was", "were", "will", "would", "could", "should",
           "this", "that", "with", "from", "about", "have", "has", "been", "and",
           "not", "you", "they", "their", "what", "when", "how", "world", "hello",
           "government", "announces", "price", "market", "elections", "inflation"},
    "fr": {"le", "la", "les", "des", "du", "une", "est", "sont", "avec", "dans",
           "pour", "sur", "qui", "que", "aux", "ce", "cette", "par", "plus",
           "gouvernement", "annonce", "monde", "bonjour", "prix", "marche",
           "guerre", "elections", "inflation", "europe"},
    "es": {"el", "la", "los", "las", "un", "una", "de", "del", "que", "en", "con",
           "por", "para", "es", "son", "como", "mas", "pero", "gobierno", "mundo",
           "hola", "precio", "mercado", "guerra", "elecciones", "inflacion"},
}

# Siglas cortas legitimas que el filtro len>=3 descartaba ("ia").
SIGLAS_CORTAS = {
    "ia", "ai", "ee", "uu", "ue", "bce", "fmi", "onu", "otan", "pib", "ipc",
    "irpf", "iva", "smi", "uk", "us", "eu", "boe", "ocde",
}


def _contiene_palabra(t: str, w: str) -> bool:
    """True si w aparece como palabra completa (matchea tambien en los bordes)."""
    t = f" {t} "
    pos = t.find(f" {w} ")
    while pos != -1:
        final = pos + len(w) + 1
        if final >= len(t) or not (t[final].isalnum() or t[final] == "_"):
            return True
        pos = t.find(f" {w} ", final)
    return False


def detectar_idioma(texto: str) -> str:
    """Detecta el idioma del texto por alfabeto, acentos y palabras funcionales."""
    if not texto: return "es"
    t = texto.lower()
    # 1. Alfabetos distintivos (mas fiable, va primero)
    if re.search(r"[\u4e00-\u9fff]", t): return "zh"
    if re.search(r"[\u0600-\u06ff]", t): return "ar"
    if re.search(r"[\u0400-\u04ff]", t): return "ru"
    # 2. Puntuacion por idioma (menos ambigua que los acentos)
    if "'" in t or "’" in t: return "fr"
    if "¿" in t or "¡" in t: return "es"
    # 3. Palabras funcionales: cubre texto sin acentos ("hello world")
    #    Se puntuan todos los idiomas y gana el que mas marcas tenga.
    #    Las marcas se solapan entre idiomas, asi que se compara el conteo.
    mejor, mejor_n = "es", 0
    for idioma, marcas in MARCAS_IDIOMA.items():
        n = sum(1 for w in marcas if _contiene_palabra(t, w))
        if n > mejor_n:
            mejor, mejor_n = idioma, n
    if mejor_n > 0:
        return mejor
    # 4. Acentos como ultimo recurso
    if any(c in t for c in "ñáíóú"): return "es"
    if any(c in t for c in "èêëàâùûôîïç"): return "fr"
    return "es"  # default

def normalizar(texto: str, idioma: str = None) -> List[str]:
    """Normaliza texto para un idioma específico o detectado automáticamente."""
    if not texto: return []
    t = (texto or "").lower()
    # Normalización Unicode NFKD (descompone acentos)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    # Elimina caracteres especiales pero conserva unicode
    t = re.sub(r"[^a-z0-9\u0600-\u06ff\u4e00-\u9fff\u0400-\u04ff\s]", " ", t)
    # Detectar idioma si no se especifica
    if idioma is None: idioma = detectar_idioma(t)
    # Obtener stopwords del idioma
    stops = STOPWORDS.get(idioma, STOPWORDS["es"])
    # Tokenizar
    tokens = t.split()
    # Filtrar
    result = []
    for tok in tokens:
        tok = tok.strip()
        # len>=3 descartaba "ia"; se conservan las siglas cortas legitimas.
        if (len(tok) >= 3 or tok in SIGLAS_CORTAS) and tok not in stops and not tok.isdigit():
            # Aplicar stemming básico
            for pat in STEMMING_PATTERNS.get(idioma, []):
                tok = re.sub(pat, "", tok)
            if tok: result.append(tok)
    return result

def obtener_stopwords(idioma: str = "es") -> Set[str]:
    """Devuelve los stopwords para un idioma."""
    return STOPWORDS.get(idioma, STOPWORDS["es"])