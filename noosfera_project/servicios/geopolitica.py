"""
Geopolítica y seguridad (0.2.2-dev).

Tres capacidades del experto en geopolítica, alineadas con el objetivo de
anticipar giros geopolíticos (sanciones, conflicto, alianza):

  1. **Calentamiento discursivo** — aceleración del tono confrontativo hacia
     un actor. La densidad de términos beligerantes subiendo es el aviso
     antes del hecho noticioso.
  2. **Lexicón de eufemismo** — cuando el lenguaje directo ("invasión") se
     sustituye por eufemismos ("operación especial"), suele anticipar una
     acción oficial encubierta. El eufemismo llega antes que la acción.
  3. **Lengua de ultimátum** — gramática disyuntiva ("o…, o", "última
     oportunidad", condiciones de rendición). Su duplicación anuncia
     negociación o conflicto inminente.

El idioma hace de proxy de país (no hay geografía explícita en el corpus).

Diseño: stdlib puro. Léxicos en castellano (base; extender por idioma).
Bajo acoplamiento: reciben documentos. Reutiliza `_contiene_palabra`.
Fuente: subagente experto en geopolítica y seguridad.
"""

from __future__ import annotations

from typing import Any, Sequence

from noosfera_project.servicios.inteligencia_predictiva import _contiene_palabra


# ── Léxicos (castellano base) ─────────────────────────────────────────────
_BELIGERANTE = {
    "sancion", "sanciones", "sancionar", "embargo", "ultimatum", "ultimátum",
    "amenaza", "advertencia", "represalia", "bloqueo", "injerencia", "presion",
    "presión", "ruptura", "escalada", "enfrentamiento", "conflicto", "guerra",
    "movilizacion", "movilización", "despliegue", "anexion", "anexión",
}
_EUFEMISMO = {
    "operacion especial", "operación especial", "medidas cautelares",
    "restricciones comerciales", "accion preventiva", "acción preventiva",
    "mision de paz", "misión de paz", "intervencion humanitaria", "intervención humanitaria",
    "zona desmilitarizada", "ajuste territorial", "reajuste", "dialogo constructivo",
    "medidas de proteccion", "medidas de protección", "golpe de autoridad",
}
_ULTIMATUM = {
    "o acepta", "o se va", "ultima oportunidad", "última oportunidad",
    "plazo final", "condiciones de rendicion", "condiciones de rendición",
    "o cumple", "o habra", "o habrá", "de lo contrario", "si no acepta",
    "si no cumple", "es la ultima vez", "es la última vez", "o retrocede",
}


def _contiene_alguna(texto: str, lexico: set[str]) -> bool:
    return any(_contiene_palabra(texto.lower(), p) for p in lexico)


def _densidad(docs: Sequence[str], lexico: set[str]) -> float:
    vals = docs or []
    if not vals:
        return 0.0
    n = sum(1 for d in vals if isinstance(d, str) and _contiene_alguna(d, lexico))
    return round(n / len(vals), 3)


# ── 1. Calentamiento discursivo ───────────────────────────────────────────
def calentamiento(docs: Sequence[str]) -> dict[str, Any]:
    """Densidad de términos beligerantes hacia un actor.

    Pendiente sostenida de esta densidad es el aviso antes del hecho
    noticioso. Señal: caldeamiento creciente.
    """
    if not docs:
        return {"beligerancia": 0.0, "n_docs": 0, "nota": "sin docs"}
    d = _densidad(docs, _BELIGERANTE)
    return {
        "beligerancia": d,
        "n_docs": len(docs),
        "caldeado": d >= 0.15,
    }


# ── 2. Lexicón de eufemismo ───────────────────────────────────────────────
def eufemismo(docs: Sequence[str]) -> dict[str, Any]:
    """Ratio eufemismos / (directos + eufemismos).

    Cuando el lenguaje directo se sustituye por eufemismos, suele anticipar
    una acción oficial encubierta. Señal: operación en preparación.
    """
    if not docs:
        return {"ratio": 0.0, "n_docs": 0, "nota": "sin docs"}
    n_euf = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _EUFEMISMO))
    # Directos: términos beligerantes que NO son eufemismo (proxy de "lenguaje crudo")
    n_dir = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _BELIGERANTE))
    total = n_euf + n_dir
    ratio = round(n_euf / total, 3) if total else 0.0
    return {
        "ratio": ratio,
        "n_eufemismos": n_euf,
        "n_directos": n_dir,
        "n_docs": len(docs),
        "operacion_encubierta": ratio >= 0.6 and n_euf >= 2,
    }


# ── 3. Lengua de ultimátum ────────────────────────────────────────────────
def ultimatum(docs: Sequence[str]) -> dict[str, Any]:
    """Densidad de construcciones disyuntivas y marcadores de plazo.

    Su duplicación anuncia negociación o conflicto inminente.
    """
    if not docs:
        return {"ultimatum": 0.0, "n_docs": 0, "nota": "sin docs"}
    d = _densidad(docs, _ULTIMATUM)
    return {
        "ultimatum": d,
        "n_docs": len(docs),
        "discurso_ultimatum": d >= 0.1,
    }


if __name__ == "__main__":
    import json

    cald = [
        "amenazan con sanciones y embargo si no hay acuerdo",
        "la escalada del conflicto avanza, advertencia de represalias",
        "bloqueo e injerencia, movilizacion de tropas cerca de la frontera",
    ]
    print("CALENTAMIENTO:", json.dumps(calentamiento(cald), ensure_ascii=False))

    euf = [
        "es una operacion especial, una mision de paz",
        "medidas cautelares y restricciones comerciales, accion preventiva",
    ]
    print("EUFEMISMO:    ", json.dumps(eufemismo(euf), ensure_ascii=False))

    ult = [
        "o acepta las condiciones o habra represalias",
        "es la ultima oportunidad, si no cumple actuaremos",
    ]
    print("ULTIMATUM:    ", json.dumps(ultimatum(ult), ensure_ascii=False))
