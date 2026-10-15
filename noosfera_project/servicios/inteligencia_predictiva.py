"""
Capacidades de inteligencia predictiva (0.2.2-dev).

Dos capacidades nuevas, alineadas con el objetivo de anticipar cambios
grandes, ajustadas a los datos que el sistema tiene (texto, fuente, fecha,
idioma — SIN autores).

  1. **Escalada de tono** — mide en qué etapa emocional está un tema:
     queja individual → agravio compartido → identidad colectiva ("nosotros")
     → movilización ("hay que", "organizar", "basta"). El paso de "yo" a
     "nosotros" y la aparición de verbos de acción preceden a la acción real.
     Con 4 fechas se mide la DISTRIBUCIÓN de etapas ahora; el cruce de
     umbral en el tiempo se activa cuando haya serie de semanas.

  2. **Co-ocurrencia anómala entre temas** — cuando dos temas que nunca se
     mezclaban empiezan a aparecer juntos en los mismos posts, suele preceder
     un cambio de marco (reencuadre causal). Es distinta a la co-ocurrencia
     de PALABRAS dentro de un tema (temas_sin_nombre): aquí es entre temas.

Diseño: stdlib puro. Bajo acoplamiento: reciben listas de documentos.
Fuente: subagente estratega de inteligencia predictiva (ajustado a datos
reales; sin autores no se implementaron las técnicas de voces/geografía).
"""

from __future__ import annotations

import math
import re as _re
from collections import Counter, defaultdict
from typing import Any, Sequence


# ── Léxicos por etapa emocional (castellano) ──────────────────────────────
ETAPA_QUEJA = {
    "yo", "mi", "me", "mio", "mia", "estoy", "tengo", "siento",
    "queja", "problema", "mal", "harto", "hartazgo", "injusto", "cabreo",
    "indignante", "verguenza", "no aguanto", "desespero",
}
ETAPA_AGRAVIO = {
    "nos", "nosotros", "nuestro", "nuestra", "comunidad", "vecinos", "gente",
    "todos", "pais", "trabajadores", "jovenes", "mayores", "afectados",
    "compartimos", "sufrimos", "padecemos", "agravio", "colectivo",
}
ETAPA_MOVILIZACION = {
    "hay que", "organizar", "organizarse", "movilizar", "manifestacion",
    "protesta", "basta", "unamos", "union", "luchar", "reclamar", "exigir",
    "convocar", "plataforma", "reunion", "accion", "actuar", "despertar",
    "ya basta", "levantarse", "pelear",
}


def _contiene_palabra(texto: str, palabra: str) -> bool:
    """¿Está `palabra` como PALABRA en `texto`? (no como subcadena).

    `palabra in texto` da falsos positivos: "cortar" dentro de "recortar",
    "sistema" dentro de "ecosistema" o "sistematico". Usa límites de palabra
    `\\b`, soportando frases multi-palabra. Fallo encontrado en auditoría.
    """
    return _re.search(rf"\b{_re.escape(palabra)}\b", texto) is not None


def _contar_etapas(texto: str) -> dict[str, int]:
    """Cuenta palabras clave de cada etapa en un texto.

    Usa matching por PALABRA (`\\b`), no por subcadena: con `p in t`, la
    palabra "yo" contaba como queja dentro de "mayores", y una frase neutra
    se clasificaba con señal emocional falsa (fallo encontrado en auditoría).
    """
    if not isinstance(texto, str):
        return {"queja": 0, "agravio": 0, "movilizacion": 0}
    t = texto.lower()
    return {
        "queja": sum(1 for p in ETAPA_QUEJA if _re.search(rf"\b{_re.escape(p)}\b", t)),
        "agravio": sum(1 for p in ETAPA_AGRAVIO if _re.search(rf"\b{_re.escape(p)}\b", t)),
        "movilizacion": sum(1 for p in ETAPA_MOVILIZACION if _re.search(rf"\b{_re.escape(p)}\b", t)),
    }


def _etapa_dominante(conteos: dict[str, int]) -> str:
    """Etapa con más presencia; si todas cero, 'sin_senal'."""
    if sum(conteos.values()) == 0:
        return "sin_senal"
    # Ponderación: la movilización pesa más que el agravio, y este más que
    # la queja (escala de intensidad creciente).
    pesos = {"queja": 1, "agravio": 2, "movilizacion": 3}
    puntuado = {k: v * pesos[k] for k, v in conteos.items()}
    return max(puntuado, key=puntuado.get)


# ── 1. Escalada de tono ───────────────────────────────────────────────────
def escalada_tono(docs: Sequence[str]) -> dict[str, Any]:
    """Distribución de etapas emocionales de un conjunto de textos.

    Devuelve el % de docs en cada etapa y la etapa dominante. Un tema donde
    domina 'movilizacion' está más caliente que uno donde domina 'queja'.
    """
    if not docs:
        return {"etapas": {}, "dominante": "sin_senal", "nota": "sin docs"}

    contador: Counter[str] = Counter()
    for d in docs:
        contador[_etapa_dominante(_contar_etapas(d))] += 1

    n = len(docs)
    etapas = {e: round(contador.get(e, 0) / n, 3) for e in ("queja", "agravio", "movilizacion")}
    dominante = max(etapas, key=etapas.get) if any(etapas.values()) else "sin_senal"

    # Nivel de calor: movilizacion pesa doble (precede a la acción)
    calor = round(etapas["movilizacion"] * 2 + etapas["agravio"], 3)

    return {
        "etapas": etapas,
        "dominante": dominante,
        "calor": calor,
        "n_docs": n,
        "escalando": etapas["movilizacion"] >= 0.15 or calor >= 0.5,
    }


def salto_colectivo(docs: Sequence[str]) -> dict[str, Any]:
    """Mide el paso de "yo" a "nosotros": indicador de que una queja
    individual se está convirtiendo en identidad colectiva.

    ratio = docs con léxico de agravio/nosotros / docs con léxico de queja/yo.
    > 1 significa que la gente ya habla en plural (señal de escalada).
    """
    queja = agravio = 0
    for d in docs:
        c = _contar_etapas(d)
        if c["queja"] > 0:
            queja += 1
        if c["agravio"] > 0:
            agravio += 1
    ratio = round(agravio / max(queja, 1), 3)
    return {
        "docs_yo": queja,
        "docs_nosotros": agravio,
        "ratio_nosotros_yo": ratio,
        "colectivizando": ratio > 1.0,
    }


# ── 2. Co-ocurrencia anómala entre temas ──────────────────────────────────
def coocurrencia_temas(
    docs: Sequence[dict[str, Any]],
    min_pmi: float = 0.1,
) -> list[dict[str, Any]]:
    """Detecta pares de temas que co-aparecen más de lo esperado.

    `docs`: cada uno con 'categorias' (lista de temas asignados al post).
    PMI(A,B) = log( P(A,B) / (P(A)·P(B)) ). Una arista con PMI alto entre dos
    temas que "no deberían" mezclarse sugiere un reencuadre causal.

    `min_pmi` bajo (0.1): con corpus pequeño el PMI rara vez supera 0.5; un
    umbral alto filtra todo. Lo que realmente importa es que sea POSITIVO
    (co-aparecen más de lo que el azar dicta) y ordenar por fuerza.
    """
    pares = Counter()
    cat_a = Counter()
    n_docs = 0
    for d in docs:
        if not isinstance(d, dict):
            continue
        cats = d.get("categorias") or []
        # Un string en vez de lista partiría en caracteres ('d','v','g'...)
        # generando pares basura (fallo de auditoría). Solo aceptamos listas.
        if not isinstance(cats, (list, tuple)):
            n_docs += 1
            continue
        if len(cats) < 2:
            if len(cats) == 1:
                cat_a[cats[0]] += 1
            n_docs += 1
            continue
        cats = sorted(set(cats))
        for i, a in enumerate(cats):
            cat_a[a] += 1
            for b in cats[i + 1:]:
                pares[(a, b)] += 1
        n_docs += 1

    if n_docs == 0:
        return []

    aristas = []
    for (a, b), co in pares.items():
        # PMI con suavizado
        p_ab = co / n_docs
        p_a = cat_a[a] / n_docs
        p_b = cat_a[b] / n_docs
        if p_a <= 0 or p_b <= 0:
            continue
        pmi = math.log((p_ab + 0.01) / (p_a * p_b + 0.01))
        if pmi >= min_pmi:
            aristas.append({
                "par": (a, b),
                "coocurrencias": co,
                "pmi": round(pmi, 3),
            })
    aristas.sort(key=lambda x: x["pmi"] * x["coocurrencias"], reverse=True)
    return aristas


# ══════════════════════════════════════════════════════════════════════════
# Ronda 2 del estratega predictivo (3 sensores con más margen de anticipación)
# ══════════════════════════════════════════════════════════════════════════

# ── 1. Rumorómetro (densidad de rumor: importancia × ambigüedad) ──────────
_VERBOS_SEGUNDA_MANO = {
    "dice que", "segun", "según", "he oido", "he oído", "parece que",
    "un amigo", "me han dicho", "comentan que", "se comenta", "cuentan que",
    "rumorea", "dicen", "aparentemente", "al parecer",
}
# Marcadores de dato concreto (números, fechas, enlaces) — lo que baja la ambigüedad
_NUMERO = _re.compile(r"\d")
_ENLACE = _re.compile(r"https?://|www\.")


def rumorometro(docs: Sequence[str]) -> dict[str, Any]:
    """Densidad de rumor: R = importancia (volumen) × ambigüedad.

    Los rumores explotan cuando algo importa mucho y nadie tiene datos
    fiables (Allport & Postman). Preceden pánicos y acciones espontáneas.
    - ambigüedad = 1 − proporción de docs con datos concretos (número/enlace)
    - segunda_mano = docs con verbos de reporte indirecto / total
    """
    if not docs:
        return {"ambiguedad": 0.0, "segunda_mano": 0.0, "rumor": 0.0, "nota": "sin docs"}
    con_dato = 0
    segunda = 0
    for d in docs:
        if not isinstance(d, str):
            continue
        if _NUMERO.search(d) or _ENLACE.search(d):
            con_dato += 1
        t = d.lower()
        if any(_contiene_palabra(t, v) for v in _VERBOS_SEGUNDA_MANO):
            segunda += 1
    n = len(docs)
    ambiguedad = round(1 - (con_dato / n), 3)
    prop_segunda = round(segunda / n, 3)
    rumor = round(ambiguedad * prop_segunda, 3)
    return {
        "ambiguedad": ambiguedad,
        "segunda_mano": prop_segunda,
        "rumor": rumor,
        "construyendo_relato": rumor >= 0.25,
        "n_docs": n,
    }


# ── 2. Gramática de la acción (expresivo → logístico) ─────────────────────
_LEXICO_LOGISTICO = {
    "llevad", "llevar", "traed", "traer", "compartid", "compartir", "alguien sabe",
    "donde", "cuando", "que hora", "punto de encuentro", "nos vemos", "quedaamos",
    "convocar", "organizar", "lista", "apuntarse", "confirmad", "avisad",
    "hay que ir", "traer", "reunion", "asamblea", "comision",
}


def gramatica_accion(docs: Sequence[str]) -> dict[str, Any]:
    """Mide si la charla pasa de expresar (queja) a planificar (logística).

    La logística (puntos de encuentro, "llevad", "quedamos") precede a la
    calle. Distinto de escalada_tono (que mide afecto): aquí es modalidad
    sintáctica expresivo→instrumental.
    """
    if not docs:
        return {"logistico": 0.0, "expresivo": 0.0, "razon": 0.0, "nota": "sin docs"}
    log = expr = 0
    for d in docs:
        if not isinstance(d, str):
            continue
        t = d.lower()
        if any(_contiene_palabra(t, v) for v in _LEXICO_LOGISTICO):
            log += 1
        # expresivo = queja o agravio (reutiliza el léxico de etapas)
        c = _contar_etapas(d)
        if c["queja"] > 0 or c["agravio"] > 0:
            expr += 1
    n = len(docs)
    prop_log = round(log / n, 3)
    prop_expr = round(expr / n, 3)
    razon = round(prop_log / max(prop_expr, 1e-9), 3)
    return {
        "logistico": prop_log,
        "expresivo": prop_expr,
        "razon": razon,
        "organizandose": prop_log >= 0.15,
        "n_docs": n,
    }


# ── 3. Coalición imposible (lift intra-documento) ─────────────────────────
def coaliciones(docs: Sequence[dict[str, Any]], min_lift: float = 1.2) -> list[dict[str, Any]]:
    """Detecta fusiones improbables de agravios en el MISMO documento.

    Distinto de `coocurrencia_temas` (que mira co-ocurrencia global): aquí
    exigimos co-mención intra-documento con lift alto —el sello de una
    coalición nueva (ecologistas+obreros; vivienda+corrupción).

    `docs`: cada uno con 'categorias' (lista de temas del post).

    `min_lift` 1.2 (no 3.0): un par que SIEMPRE va junto (nunca se ve por
    separado, el caso de una coalición perfecta) da lift = P(ambos)/(Pa·Pb),
    y cuando ambos se reparten igual llega como máximo a ~1.33. Un umbral de
    3 buscaría pares imposibles en corpus pequeño; 1.2 ya indica atracción
    real sobre el azar (>1 significa que co-aparecen más de lo independiente).
    """
    ambos = Counter()
    cat_a = Counter()
    n = 0
    for d in docs:
        if not isinstance(d, dict):
            continue
        cats = d.get("categorias") or []
        # Igual que en coocurrencia_temas: un string partiría en caracteres.
        if not isinstance(cats, (list, tuple)):
            n += 1
            continue
        cats = sorted(set(cats))
        n += 1
        for c in cats:
            cat_a[c] += 1
        for i, a in enumerate(cats):
            for b in cats[i + 1:]:
                ambos[(a, b)] += 1
    if n == 0:
        return []
    coaliciones_out = []
    for (a, b), co in ambos.items():
        if co < 2:
            continue
        # lift intra-documento = P(ambos juntos) / (P(a)·P(b))
        p_ambos = co / n
        p_a = cat_a[a] / n
        p_b = cat_a[b] / n
        if p_a <= 0 or p_b <= 0:
            continue
        lift = p_ambos / (p_a * p_b)
        if lift >= min_lift:
            coaliciones_out.append({
                "par": (a, b),
                "co_menciones": co,
                "lift": round(lift, 2),
            })
    coaliciones_out.sort(key=lambda x: x["lift"], reverse=True)
    return coaliciones_out


# ══════════════════════════════════════════════════════════════════════════
# Sociólogo computacional (ronda 1): brecha de agencia + repertorio de acción
# ══════════════════════════════════════════════════════════════════════════

# ── 4. Brecha de agencia (Gamson: injusticia + adversario − agencia) ──────
_INDIGNACION = {
    "injusto", "injusticia", "indignante", "inaceptable", "verguenza",
    "escandalo", "abusivo", "intolerable", "bochornoso", "lamentable",
}
_ADVERSARIO = {
    "el gobierno", "los politicos", "la banca", "los bancos", "las electricas",
    "los empresarios", "el sistema", "la casta", "los de arriba", "el establishment",
    "los bancos", "los especuladores", "los de siempre",
}
_AGENCIA = {
    "podemos", "es posible", "si nos organizamos", "juntos podemos", "somos capaces",
    "podemos cambiar", "hay salida", "podemos parar", "podemos evitarlo", "tenemos fuerza",
    "podemos ganar", "si nos unimos", "lo conseguiremos", "podemos lograrlo",
}


def brecha_agencia(docs: Sequence[str]) -> dict[str, Any]:
    """Brecha de agencia (Gamson): el marco de injusticia enciende cuando tiene
    indignación + adversario + agencia. Lo que suele faltar es la agencia.

    brecha = (indignación × adversario) − agencia.
    Brecha alta = frustración acumulada sin salida: el tema está pre-encendido
    y cualquier chispa prende acción masiva. Salto de agencia = último
    precursor de la movilización.
    """
    if not docs:
        return {"indignacion": 0.0, "adversario": 0.0, "agencia": 0.0, "brecha": 0.0, "nota": "sin docs"}
    ind = adv = ag = 0
    for d in docs:
        if not isinstance(d, str):
            continue
        t = d.lower()
        if any(_contiene_palabra(t, v) for v in _INDIGNACION):
            ind += 1
        if any(_contiene_palabra(t, v) for v in _ADVERSARIO):
            adv += 1
        if any(_contiene_palabra(t, v) for v in _AGENCIA):
            ag += 1
    n = len(docs)
    prop_ind = round(ind / n, 3)
    prop_adv = round(adv / n, 3)
    prop_ag = round(ag / n, 3)
    brecha = round(prop_ind * prop_adv - prop_ag, 3)
    return {
        "indignacion": prop_ind,
        "adversario": prop_adv,
        "agencia": prop_ag,
        "brecha": brecha,
        "pre_encendido": brecha >= 0.15,  # mucha injusticia, poca agencia
        "n_docs": n,
    }


# ── 5. Repertorio de acción (Tilly/Tarrow) ────────────────────────────────
_REP_SIMBOLICO = {
    "firmar", "compartir", "difundir", "manifestarse", "hashtag", "tuitear",
    "poner un lazo", "vela", "minuto de silencio", "concentracion",
}
_REP_CONFRONTACIONAL = {
    "ocupar", "bloquear", "cortar", "huelga", "boicot", "rodeado", "acampar",
    "sentada", "tumbar", "impedir", "sabotaje", "escrache", "rodear",
}
_REP_INSTITUCIONAL = {
    "recurrir", "querella", "denuncia formal", "demanda judicial", "recurso",
    "via judicial", "abogado", "tribunal", "contencioso", "reclamacion oficial",
}


def repertorio_accion(docs: Sequence[str]) -> dict[str, Any]:
    """Mide el REPERTORIO de acción que la gente nombra (Tilly/Tarrow).

    Lo que anticipa el giro no es el tono (ya implementado) sino qué acciones
    propone la gente: simbólica (firmar, compartir), confrontacional (ocupar,
    bloquear, huelga) o institucional (recurrir, querella).
    - Una categoría confrontacional NUEVA en un tema antes simbólico = escalada.
    - Diversidad cayendo mientras el volumen crece = simplificación.
    """
    if not docs:
        return {"simbolico": 0.0, "confrontacional": 0.0, "institucional": 0.0, "nota": "sin docs"}
    sim = conf = inst = 0
    for d in docs:
        if not isinstance(d, str):
            continue
        t = d.lower()
        if any(_contiene_palabra(t, v) for v in _REP_SIMBOLICO):
            sim += 1
        if any(_contiene_palabra(t, v) for v in _REP_CONFRONTACIONAL):
            conf += 1
        if any(_contiene_palabra(t, v) for v in _REP_INSTITUCIONAL):
            inst += 1
    n = len(docs)
    prop = {
        "simbolico": round(sim / n, 3),
        "confrontacional": round(conf / n, 3),
        "institucional": round(inst / n, 3),
    }
    categorias_activas = sum(1 for v in prop.values() if v > 0)
    dominante = max(prop, key=prop.get)
    return {
        **prop,
        "categorias_activas": categorias_activas,
        "dominante": dominante,
        "escalada": prop["confrontacional"] >= 0.15,
        "n_docs": n,
    }


if __name__ == "__main__":
    import json

    # Demostración: tema en escalada
    docs_escalada = [
        "yo estoy harto de esta situacion",
        "nosotros los vecinos no aguantamos mas, hay que organizarnos",
        "es una injusticia, compartimos el agravio",
        "basta ya, hay que movilizarse y convocar una manifestacion",
        "yo tengo un problema con esto",
    ]
    print("ESCALADA:", json.dumps(escalada_tono(docs_escalada), ensure_ascii=False))
    print("SALTO:   ", json.dumps(salto_colectivo(docs_escalada), ensure_ascii=False))

    # Co-ocurrencia entre temas
    docs_temas = [
        {"categorias": ["vivienda", "jubilacion"]},
        {"categorias": ["vivienda", "jubilacion"]},
        {"categorias": ["vivienda", "jubilacion"]},
        {"categorias": ["energia"]},
        {"categorias": ["vivienda"]},
    ]
    print("COOCURRENCIA:", json.dumps(coocurrencia_temas(docs_temas), ensure_ascii=False))

    # Ronda 2: rumorómetro, gramática de la acción, coaliciones
    docs_rumor = [
        "segun he oido parece que va a pasar algo, dicen que",
        "un amigo me ha dicho que comentan que habra problemas",
        "al parecer se comenta que el gobierno prepara algo",
    ]
    print("RUMOROMETRO:", json.dumps(rumorometro(docs_rumor), ensure_ascii=False))

    docs_logistica = [
        "quedamos en el punto de encuentro, llevad pancartas",
        "alguien sabe donde es la asamblea? avisad a todos",
        "hay que organizarse, compartid la convocatoria",
    ]
    print("GRAMATICA: ", json.dumps(gramatica_accion(docs_logistica), ensure_ascii=False))

    docs_coalicion = [
        {"categorias": ["vivienda", "corrupcion"]},
        {"categorias": ["vivienda", "corrupcion"]},
        {"categorias": ["vivienda", "corrupcion"]},
        {"categorias": ["ecologia"]},
    ]
    print("COALICIONES:", json.dumps(coaliciones(docs_coalicion), ensure_ascii=False))

    # Sociólogo: brecha de agencia + repertorio
    docs_frustracion = [
        "es una injusticia inaceptable, la culpa es del gobierno y los politicos",
        "que verguenza, los bancos y los de arriba nos hunden, es un escandalo",
        "indignante, el sistema nos roba pero no podemos hacer nada",
    ]
    print("AGENCIA:  ", json.dumps(brecha_agencia(docs_frustracion), ensure_ascii=False))

    docs_repertorio = [
        "hay que ocupar la plaza y bloquear el acceso",
        "convoquemos una huelga y boicot a sus productos",
        "vamos a acampar y rodear el edificio",
    ]
    print("REPERTORIO:", json.dumps(repertorio_accion(docs_repertorio), ensure_ascii=False))
