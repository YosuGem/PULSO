"""
Termómetro regulatorio (0.2.2-dev).

Tres capacidades del experto en derecho, alineadas con el objetivo de
anticipar respuestas regulatorias o legales del estado:

  1. **Juridificación léxica** — el tema migra del lenguaje coloquial al
     jurídico ("derechos", "ilegal", "violación") sin que nadie lo traduzca.
     Es el último escalón antes de la intervención: la controversia ya está
     enmarcada en términos que un tribunal o legislador entiende.
  2. **Analogía regulatoria** — la gente propone resolver el tema importando
     un marco existente ("como con el tabaco", "igual que los cinturones").
     La sociedad hace el trabajo de redacción antes que el legislador.
  3. **Déficit de vigilancia** — impunidad subjetiva ("nadie controla",
     "no hay quien verifique"). Cuando la gente cree que no hay vigilancia
     eficaz, sube el coste político de no regular.

Diseño: stdlib puro. Léxicos en castellano (base; extender por idioma cuando
haya datos). Bajo acoplamiento: reciben documentos. Reutiliza
`_contiene_palabra` (matching por palabra, sin subcadenas).
Fuente: subagente experto en derecho y regulación.
"""

from __future__ import annotations

from typing import Any, Sequence

from noosfera_project.servicios.inteligencia_predictiva import _contiene_palabra


# ── Léxicos (castellano base) ─────────────────────────────────────────────
_JURIDICO = {
    "derecho", "derechos", "ilegal", "legal", "denunciable", "proteger",
    "violacion", "violación", "protegido", "normativa", "ley", "legislar",
    "regulacion", "regulación", "delito", "constitucion", "constitución",
    "amparo", "recurrir", "tribunal", "sentencia", "juridico", "jurídico",
}
_ANALOGIA = {
    "como con", "como se hizo con", "igual que con", "al estilo de",
    "lo mismo que con", "como cuando", "igual que cuando", "tal y como",
    "como hicieron con", "siguiendo el ejemplo de", "a imagen de",
}
_VIGILANCIA_AUSENTE = {
    "nadie controla", "no hay quien", "no pasa nada", "no se vigila",
    "impune", "impunidad", "sin control", "nadie vigila", "no hay inspeccion",
    "no hay inspección", "denuncias y nada", "no se sanciona", "sin consecuencia",
    "mira hacia otro lado", "no hay consecuencias",
}


def _contiene_alguna(texto: str, lexico: set[str]) -> bool:
    return any(_contiene_palabra(texto.lower(), p) for p in lexico)


# ── 1. Juridificación léxica ──────────────────────────────────────────────
def juridificacion(docs: Sequence[str]) -> dict[str, Any]:
    """Proporción de docs que enmarcan el tema en términos legales.

    Es el último escalón antes de la intervención: cuando el tema se formula
    como cuestión de derechos/legalidad, el legislador o el tribunal ya tienen
    un marco sobre el que actuar.
    """
    if not docs:
        return {"juridificacion": 0.0, "n_docs": 0, "nota": "sin docs"}
    n = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _JURIDICO))
    prop = round(n / len(docs), 3)
    return {
        "juridificacion": prop,
        "n_juridicos": n,
        "n_docs": len(docs),
        "listo_para_norma": prop >= 0.2,
    }


# ── 2. Analogía regulatoria ───────────────────────────────────────────────
def analogia_regulatoria(docs: Sequence[str]) -> dict[str, Any]:
    """Proporción de docs que proponen importar un marco existente.

    "Como con el tabaco", "igual que los cinturones": la gente ya ha escrito
    el borrador. Señal de propuesta legislativa lista para copiar.
    """
    if not docs:
        return {"analogia": 0.0, "n_docs": 0, "nota": "sin docs"}
    n = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _ANALOGIA))
    prop = round(n / len(docs), 3)
    return {
        "analogia": prop,
        "n_analogias": n,
        "n_docs": len(docs),
        "borrador_en_calle": prop >= 0.1,
    }


# ── 3. Déficit de vigilancia ──────────────────────────────────────────────
def deficit_vigilancia(docs: Sequence[str]) -> dict[str, Any]:
    """Proporción de docs que expresan impunidad subjetiva.

    "Nadie controla", "no hay quien verifique". Cuando la gente cree que no
    hay vigilancia eficaz, sube el coste político de no regular. Clásico
    precursor de agencias y fiscalización.
    """
    if not docs:
        return {"vigilancia": 0.0, "n_docs": 0, "nota": "sin docs"}
    n = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _VIGILANCIA_AUSENTE))
    prop = round(n / len(docs), 3)
    return {
        "vigilancia": prop,
        "n_vigilancia": n,
        "n_docs": len(docs),
        "costo_politico_alto": prop >= 0.1,
    }


if __name__ == "__main__":
    import json

    juridico_docs = [
        "esto es ilegal, vulnera nuestros derechos, hay que denunciarlo",
        "es una violacion de la ley, protejamos nuestros derechos",
    ]
    print("JURIDIFICACION:", json.dumps(juridificacion(juridico_docs), ensure_ascii=False))

    analogia_docs = [
        "deberian regularlo como con el tabaco",
        "igual que hicieron con los cinturones de seguridad",
    ]
    print("ANALOGIA:      ", json.dumps(analogia_regulatoria(analogia_docs), ensure_ascii=False))

    vigilancia_docs = [
        "nadie controla nada, no hay quien verifique, todo impune",
        "denuncias y nada, no pasa nada, sin consecuencia",
    ]
    print("VIGILANCIA:    ", json.dumps(deficit_vigilancia(vigilancia_docs), ensure_ascii=False))
