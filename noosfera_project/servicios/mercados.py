"""
Mercados y estrés económico (0.2.2-dev).

Tres capacidades del estratega de mercados financieros, alineadas con el
objetivo de anticipar giros financieros y crisis:

  1. **Gramática de la capitulación** — el giro de comprar a salir ("recortar
     pérdidas", "salir como sea" vs "comprar ahora"). El cruce de curvas
     salida>entrada tras fase alcista = capitulación; tras fase neutra = pánico.
  2. **Sobreextensión de certeza** — narrativa separándose de los hechos
     ("seguro que va a subir" vs "los datos dicen que subió un X%"). Euforia
     narrativa: el precio se desconecta de la realidad.
  3. **Deriva de subsistencia** — estrés económico real en la gente ("no me
     llega", "he recortado") ANTES de que sea oficial. Adelanta 1-2 trimestres
     a la crisis declarada.

Diseño: stdlib puro. Léxicos en castellano (base; extender por idioma cuando
haya datos). Bajo acoplamiento: reciben documentos. Reutiliza
`_contiene_palabra` (matching por palabra, sin subcadenas).
Fuente: subagente estratega de mercados financieros.
"""

from __future__ import annotations

from typing import Any, Sequence

from noosfera_project.servicios.inteligencia_predictiva import _contiene_palabra


# ── Léxicos (castellano base) ─────────────────────────────────────────────
_ENTRADA = {
    "entrar", "entrando", "comprar", "comprando", "subirme", "sumarme", "largar",
    "invertir", "inversion", "inversión", "alcista", "va a subir", "comprar ahora",
    "yo entro", "todo dentro",
}
_SALIDA = {
    "salir", "saliendo", "recortar perdidas", "recortar pérdidas", "vender", "vendiendo",
    "sacarme", "sacarlo", "salir como sea", "ya no aguanto", "me salgo", "fuera",
    "liquidar", "capitular", "bajista", "va a caer", "retirar",
}
_CERTEZA = {
    "seguro que", "sin duda", "imposible que", "va a subir", "garantizado",
    "es un hecho", "no hay duda", "definitivamente", "claro que si", "claro que sí",
    "obvio que", "sin lugar a dudas", "va a explotar", "si o si", "sí o sí",
}
_VERIFICACION = {
    "los datos", "segun los datos", "según los datos", "el informe", "las cifras",
    "el ano pasado", "el año pasado", "subio un", "subió un", "bajo un", "bajó un",
    "la estadistica", "la estadística", "fuentes oficiales", "el estudio",
}
_SUBSISTENCIA = {
    "no me llega", "he recortado", "tengo que elegir entre pagar", "a fin de mes",
    "no puedo pagar", "he dejado de comprar", "no hay para comida", "apretado",
    "estirado", "no llego a fin de mes", "recortando gastos", "vendiendo cosas",
    "empenar", "empeñar", "devolviendo recibos", "impagable",
}


def _contiene_alguna(texto: str, lexico: set[str]) -> bool:
    return any(_contiene_palabra(texto.lower(), p) for p in lexico)


def _contar(texto: str, lexico: set[str]) -> int:
    return sum(1 for p in lexico if _contiene_palabra(texto.lower(), p))


# ── 1. Gramática de la capitulación ───────────────────────────────────────
def capitulacion(docs: Sequence[str]) -> dict[str, Any]:
    """Cruce de curvas salida vs entrada.

    salida>entrada tras fase alcista = capitulación (probable suelo); tras
    fase neutra = pánico de fondo (no de techo).
    """
    if not docs:
        return {"entrada": 0.0, "salida": 0.0, "flujo": "neutro", "nota": "sin docs"}
    ent = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _ENTRADA))
    sal = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _SALIDA))
    p_ent = round(ent / len(docs), 3)
    p_sal = round(sal / len(docs), 3)
    if p_sal > p_ent and p_sal > 0.05:
        flujo = "capitulacion"
    elif p_ent > p_sal and p_ent > 0.05:
        flujo = "entrada"
    else:
        flujo = "neutro"
    return {"entrada": p_ent, "salida": p_sal, "flujo": flujo, "n_docs": len(docs)}


# ── 2. Sobreextensión de certeza ──────────────────────────────────────────
def sobreextension_certeza(docs: Sequence[str]) -> dict[str, Any]:
    """Ratio certeza/verificación. Narrativa separándose de los hechos.

    Ratio subiendo sin aumento de hechos verificables = euforia narrativa, el
    precio desconectado de la realidad.
    """
    if not docs:
        return {"certeza": 0.0, "verificacion": 0.0, "ratio": 0.0, "nota": "sin docs"}
    cert = _contar_promedio(docs, _CERTEZA)
    verif = _contar_promedio(docs, _VERIFICACION)
    # Sin hechos verificables, el ratio certeza/verificación no está definido
    # (división por ~0 daría billones). Se marca euforia narrativa y se reporta
    # el ratio como 0.0 con la bandera, no un número absurdo (fallo de
    # división por cero, patrón ya corregido en zscore_diario).
    euforia = cert > 0 and verif == 0
    ratio = 0.0 if verif == 0 else round(cert / verif, 3)
    return {
        "certeza": cert,
        "verificacion": verif,
        "ratio": ratio,
        "euforia_narrativa": euforia,
        "n_docs": len(docs),
    }


# ── 3. Deriva de subsistencia ─────────────────────────────────────────────
def deriva_subsistencia(docs: Sequence[str]) -> dict[str, Any]:
    """Estrés económico real en la gente, antes de que sea oficial.

    Adelanta 1-2 trimestres a la crisis declarada. Se mide en TODOS los temas,
    no solo financieros: "no me llega", "he recortado", "a fin de mes".
    """
    if not docs:
        return {"subsistencia": 0.0, "n_docs": 0, "nota": "sin docs"}
    n = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _SUBSISTENCIA))
    prop = round(n / len(docs), 3)
    return {
        "subsistencia": prop,
        "n_subsistencia": n,
        "n_docs": len(docs),
        "estres_extendido": prop >= 0.15,
    }


def _contar_promedio(docs: Sequence[str], lexico: set[str]) -> float:
    vals = [_contar(d, lexico) for d in docs if isinstance(d, str)]
    return round(sum(vals) / len(vals), 3) if vals else 0.0


# ══════════════════════════════════════════════════════════════════════════
# Ronda 2 del estratega de economía conductual (las 4 más robustas con corpus
# pequeño: conteos puros, ratios relativos, nunca umbrales absolutos)
# ══════════════════════════════════════════════════════════════════════════
_APALANCAMIENTO = {
    "a credito", "endeudado", "apalancado", "prestamo", "préstamo", "margen",
    "hipotecar", "hipoteca", "todo a una", "aposte todo", "empenado", "empeñado",
    "dinero prestado", "vendido para invertir",
}
_EUFORIA = {
    "no puede fallar", "garantizado", "imposible que baje", "boom asegurado",
    "seguro que sube", "sin riesgo", "si o si sube", "sí o sí sube",
    "a la luna", "forrado", "rico seguro", "no hay quien me pare",
}
_DUDA = {"quizas", "quizá", "quizás", "no se", "no sé", "riesgo", "puede que", "tal vez"}
_ANCLAJE = {
    "lo compre a", "lo compré a", "me costo", "me costó", "estoy en perdidas",
    "estoy en pérdidas", "cuando vuelva a", "venderia por encima", "vendería por encima",
    "mi precio de entrada",
}
_DESANCLAJE = {"vendo lo que sea", "ya da igual", "lo que me den", "salgo ya", "vendo ya"}
_EXPECTATIVA = {
    "va a subir", "recuperacion", "recuperación", "remontara", "remontará",
    "rebotara", "rebotará", "volvera a", "volverá a",
}
_DIFICULTAD = {"he perdido", "no llego", "no puedo pagar", "perdi", "perdí", "arruinado", "sin ahorros"}


def apalancamiento_minorista(docs: Sequence[str]) -> dict[str, Any]:
    """Endeudamiento para apostar (burbujas 1929/2008, meme stocks 2021).

    Densidad de léxico de apalancamiento. Señal: euforia apalancada, fase
    tardía de ciclo, alto riesgo de giro violento.
    """
    if not docs:
        return {"apalancamiento": 0.0, "n_docs": 0, "nota": "sin docs"}
    n = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _APALANCAMIENTO))
    prop = round(n / len(docs), 3)
    return {
        "apalancamiento": prop,
        "n_docs": len(docs),
        "euforia_apalancada": prop >= 0.1,
    }


def euforia_colectiva(docs: Sequence[str]) -> dict[str, Any]:
    """Omnipotencia verbal + desaparición de la duda (techo de ciclo).

    indice = euforia − duda. Señal: el discurso ha perdido toda capacidad de
    sorpresa; el giro llega cuando la duda es socialmente impensable.
    """
    if not docs:
        return {"euforia": 0.0, "duda": 0.0, "indice": 0.0, "nota": "sin docs"}
    n_euf = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _EUFORIA))
    n_duda = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _DUDA))
    p_euf = round(n_euf / len(docs), 3)
    p_duda = round(n_duda / len(docs), 3)
    return {
        "euforia": p_euf,
        "duda": p_duda,
        "indice": round(p_euf - p_duda, 3),
        "techo_ciclo": p_euf > 0 and p_euf - p_duda >= 0.1,
    }


def anclaje_precio(docs: Sequence[str]) -> dict[str, Any]:
    """Anclaje al precio de compra personal (aversión a la pérdida).

    Saturación de anclaje = resistencia a vender acumulada (frena caídas,
    acumula presión); el primer spike de desanclaje preavisa capitulación.
    """
    if not docs:
        return {"anclaje": 0.0, "desanclaje": 0.0, "nota": "sin docs"}
    n_anc = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _ANCLAJE))
    n_des = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _DESANCLAJE))
    p_anc = round(n_anc / len(docs), 3)
    p_des = round(n_des / len(docs), 3)
    return {
        "anclaje": p_anc,
        "desanclaje": p_des,
        "resistencia_vendedora": p_anc > p_des and p_anc >= 0.1,
        "desanclaje_incipiente": n_des > 0 and n_anc > 0,
    }


def brecha_expectativas(docs: Sequence[str]) -> dict[str, Any]:
    """Divergencia entre optimismo declarado y experiencia material.

    gap = expectativa − dificultad. Gap alto = discurso sin respaldo
    material; colapso del gap a negativo = giro real inminente.
    """
    if not docs:
        return {"expectativa": 0.0, "dificultad": 0.0, "gap": 0.0, "nota": "sin docs"}
    n_exp = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _EXPECTATIVA))
    n_dif = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _DIFICULTAD))
    p_exp = round(n_exp / len(docs), 3)
    p_dif = round(n_dif / len(docs), 3)
    return {
        "expectativa": p_exp,
        "dificultad": p_dif,
        "gap": round(p_exp - p_dif, 3),
        "discurso_sin_respaldo": p_exp > 0 and p_dif == 0,
    }


if __name__ == "__main__":
    import json

    capitulacion_docs = [
        "voy a salir como sea, ya no aguanto, recortar perdidas",
        "me salgo, vendiendo todo, sacarme de esta",
    ]
    print("CAPITULACION:", json.dumps(capitulacion(capitulacion_docs), ensure_ascii=False))

    euforia_docs = [
        "seguro que va a subir, sin duda, garantizado",
        "obvio que va a explotar, si o si, es un hecho",
    ]
    print("CERTEZA:     ", json.dumps(sobreextension_certeza(euforia_docs), ensure_ascii=False))

    subsistencia_docs = [
        "no me llega a fin de mes, he recortado gastos",
        "he dejado de comprar, no puedo pagar el alquiler",
    ]
    print("SUBSISTENCIA:", json.dumps(deriva_subsistencia(subsistencia_docs), ensure_ascii=False))

    # Ronda 2: economía conductual
    apalancamiento_docs = [
        "he pedido un prestamo para meter todo a una, endeudado",
        "hipoteque para invertir, apalancado al maximo",
    ]
    print("APALANCAMIENTO:", json.dumps(apalancamiento_minorista(apalancamiento_docs), ensure_ascii=False))

    euforia_docs2 = [
        "esto no puede fallar, garantizado, imposible que baje",
        "boom asegurado, forrado, a la luna",
    ]
    print("EUFORIA:    ", json.dumps(euforia_colectiva(euforia_docs2), ensure_ascii=False))

    anclaje_docs = [
        "lo compre a 100, cuando vuelva a ese precio vendo",
        "estoy en perdidas, mi precio de entrada fue alto",
    ]
    print("ANCLAJE:    ", json.dumps(anclaje_precio(anclaje_docs), ensure_ascii=False))

    brecha_docs = ["va a subir, recuperacion, remontara pronto", "espero que rebotara"]
    print("BRECHA:     ", json.dumps(brecha_expectativas(brecha_docs), ensure_ascii=False))
