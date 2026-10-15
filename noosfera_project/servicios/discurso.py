"""
Análisis del discurso y lingüística de corpus (0.2.2-dev).

Tres capacidades del experto en lingüística, alineadas con el objetivo de
detectar el giro antes de que nadie lo nombre:

  1. **Frame shifting** — el mismo tema se reencuadra (seguridad ↔ economía ↔
     moral). Cuando cambia el marco dominante, anticipa el giro de narrativa.
  2. **Nominalización vs verbalización** — el concepto se congela en sustantivo
     ("la inmigración", depersonaliza, institucionaliza) o revive en verbo
     ("despiden", devuelve agencia popular). Marca la fase del ciclo.
  3. **Metáfora dominante** — una metáfora coloniza un tema ("la inflación
     habla en metáforas de guerra"). Predice el guion de respuesta social.

Las 4 capacidades restantes del experto (resemantización, polarización
semántica, tecnicismo filtrándose, eufemización) requieren series semanales
largas (vectores de contexto, deriva temporal) que el corpus aún no tiene con
1 fecha; quedan anotadas para cuando el registro diario acumule semanas.

Diseño: stdlib puro. Léxicos semilla en castellano (base; extender por idioma).
Bajo acoplamiento: reciben documentos. Reutiliza `_contiene_palabra`.
Fuente: subagente experto en lingüística de corpus.
"""

from __future__ import annotations

from typing import Any, Sequence

from noosfera_project.procesamiento.temas_sin_nombre import tokenizar
from noosfera_project.servicios.inteligencia_predictiva import _contiene_palabra


# ── 1. Marcos semánticos (frame shifting) ─────────────────────────────────
_MARCO_SEGURIDAD = {
    "amenaza", "peligro", "proteger", "invasion", "invasión", "seguridad",
    "defender", "riesgo", "vulnerable", "blindar", "escudo", "frontera",
}
_MARCO_ECONOMIA = {
    "coste", "costo", "producir", "pagar", "precio", "mercado", "economia",
    "economía", "dinero", "gasto", "inversion", "inversión", "riqueza", "deuda",
}
_MARCO_MORAL = {
    "justo", "justicia", "deber", "digno", "dignidad", "etico", "ético",
    "correcto", "bien", "mal", "derechos", "respeto", "solidaridad", "honesto",
}
_MARCOS = {
    "seguridad": _MARCO_SEGURIDAD,
    "economia": _MARCO_ECONOMIA,
    "moral": _MARCO_MORAL,
}


def frame_shifting(docs: Sequence[str]) -> dict[str, Any]:
    """Distribución de marcos semánticos sobre un tema.

    Cuando el marco dominante cambia (economía→seguridad, o a moral),
    anticipa el giro de narrativa y de política.
    """
    if not docs:
        return {"marcos": {}, "dominante": "sin_senal", "nota": "sin docs"}
    conteos: dict[str, int] = {m: 0 for m in _MARCOS}
    for d in docs:
        if not isinstance(d, str):
            continue
        t = d.lower()
        for marco, lex in _MARCOS.items():
            if any(_contiene_palabra(t, p) for p in lex):
                conteos[marco] += 1
    n = len(docs)
    marcos = {m: round(c / n, 3) for m, c in conteos.items()}
    dominante = max(marcos, key=marcos.get) if any(marcos.values()) else "sin_senal"
    return {"marcos": marcos, "dominante": dominante, "n_docs": n}


# ── 2. Nominalización vs verbalización ────────────────────────────────────
_SUFIJOS_NOMINALES = ("cion", "ciones", "miento", "mientos", "aje", "ajes", "ismo", "ismos", "idad", "idades")
# Verbos en infinitivo y formas personales comunes (proxy de agencia verbal)
_SUFIJO_VERBAL = ("ar", "er", "ir")


def _es_nominalizacion(token: str) -> bool:
    return token.endswith(_SUFIJOS_NOMINALES) and len(token) > 5


def _es_verbo(token: str) -> bool:
    # Heurística simple: infinitivo o forma verbal frecuente terminada en -ar/-er/-ir
    # o desinencias verbales comunes. Solo como proxy (sin analizador morfológico).
    return token.endswith(_SUFIJO_VERBAL) and len(token) > 3


def nominalizacion(docs: Sequence[str]) -> dict[str, Any]:
    """Ratio nominalizaciones/verbos. Institucionalización vs agencia popular.

    Nominalización creciente = tema institucionalizándose (burocratización);
    verbalización creciente = recuperación de agencia popular.
    """
    if not docs:
        return {"nominalizacion": 0.0, "verbalizacion": 0.0, "ratio": 0.0, "nota": "sin docs"}
    from noosfera_project.procesamiento.normalizacion import tokenizar

    n_nom = n_ver = 0
    for d in docs:
        if not isinstance(d, str):
            continue
        for tok in tokenizar(d):
            if _es_nominalizacion(tok):
                n_nom += 1
            elif _es_verbo(tok):
                n_ver += 1
    total = n_nom + n_ver
    p_nom = round(n_nom / total, 3) if total else 0.0
    p_ver = round(n_ver / total, 3) if total else 0.0
    return {
        "nominalizacion": p_nom,
        "verbalizacion": p_ver,
        "ratio": round(n_nom / max(n_ver, 1), 3),
        "institucionalizando": p_nom > p_ver and n_nom >= 3,
        "n_docs": len(docs),
    }


# ── 3. Metáfora dominante ─────────────────────────────────────────────────
_MET_GUERRA = {
    "batalla", "guerra", "enemigo", "frente", "lucha", "combate", "arma",
    "ejercito", "ejército", "victoria", "derrota", "cruzada", "trinchera",
}
_MET_ENFERMEDAD = {
    "virus", "contagio", "enfermedad", "cura", "epidemia", "sintoma", "síntoma",
    "vacuna", "infeccion", "infección", "patogeno", "patógeno", "brotes",
}
_MET_AGUA = {
    "ola", "marea", "riada", "torrente", "desborde", "desbordar", "inundacion",
    "inundación", "flujo", "goteo", "tsunami", "cauce",
}
_MET_CUERPO = {
    "tumor", "herida", "cancer", "cáncer", "sangrado", "dolor", "organo",
    "órgano", "tejido", "cicatriz", "paralisis", "parálisis", "corazon",
}
_METAFORAS = {
    "guerra": _MET_GUERRA,
    "enfermedad": _MET_ENFERMEDAD,
    "agua": _MET_AGUA,
    "cuerpo": _MET_CUERPO,
}


def metafora_dominante(docs: Sequence[str]) -> dict[str, Any]:
    """Detecta qué dominio fuente (guerra/enfermedad/agua/cuerpo) coloniza el tema.

    La metáfora dominante predice el guion de respuesta social: un tema
    enmarcado como guerra pide un enemigo; como enfermedad, una cura.
    """
    if not docs:
        return {"metaforas": {}, "dominante": "sin_senal", "nota": "sin docs"}
    conteos: dict[str, int] = {m: 0 for m in _METAFORAS}
    for d in docs:
        if not isinstance(d, str):
            continue
        t = d.lower()
        for met, lex in _METAFORAS.items():
            if any(_contiene_palabra(t, p) for p in lex):
                conteos[met] += 1
    n = len(docs)
    metaforas = {m: round(c / n, 3) for m, c in conteos.items()}
    dominante = max(metaforas, key=metaforas.get) if any(metaforas.values()) else "sin_senal"
    return {"metaforas": metaforas, "dominante": dominante, "n_docs": n}


if __name__ == "__main__":
    import json

    guerra_docs = [
        "hay que ganar esta batalla contra el enemigo, es una guerra",
        "la lucha en el frente, el combate, somos un ejercito",
    ]
    print("FRAME:      ", json.dumps(frame_shifting(guerra_docs), ensure_ascii=False))

    nom_docs = [
        "la reestructuracion de la inmigracion y la flexibilizacion",
        "despiden, recortan, congelan las pensiones",
    ]
    print("NOMINALIZ:  ", json.dumps(nominalizacion(nom_docs), ensure_ascii=False))

    enf_docs = [
        "el virus de la inflacion contagia la economia, es una epidemia",
        "necesitamos una cura, el brote se propaga",
    ]
    print("METAFORA:   ", json.dumps(metafora_dominante(enf_docs), ensure_ascii=False))
