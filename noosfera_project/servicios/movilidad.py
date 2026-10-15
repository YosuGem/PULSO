"""
Migración y movilidad (0.2.2-dev).

Tres capacidades del experto en migración, alineadas con el objetivo de
anticipar giros de movilidad y tensiones sociales:

  1. **Indicador de expulsión** — intención declarada de irse ("me voy",
     "quiero irme", "sacar la visa"). Un éxodo potencial se anuncia en la
     conversación antes que en los datos oficiales.
  2. **Lenguaje de emergencia** — la migración de vocabulario de descriptivo
     ("llegan personas") a bélico ("invasión", "avalancha", "desembarco").
     Este cambio de marco precede al endurecimiento de política de movilidad.
  3. **Balanza llegada↔salida** — si un tema de movilidad es de atracción o
     de expulsión. El cruce del ratio inversa el flujo percibido.

Diseño: stdlib puro. Léxicos en castellano (base; extender por idioma cuando
haya datos suficientes en cada uno). Bajo acoplamiento: reciben documentos.
Reutiliza `_contiene_palabra` (matching por palabra, sin subcadenas).
Fuente: subagente experto en migración y demografía.
"""

from __future__ import annotations

from typing import Any, Sequence

from noosfera_project.servicios.inteligencia_predictiva import _contiene_palabra


# ── Léxicos (castellano base) ─────────────────────────────────────────────
_EXPULSION = {
    "me voy", "me quiero ir", "quiero irme", "sacarme la visa", "sacar la visa",
    "estoy harto de este pais", "estoy harto de este país", "me marcho", "me piro",
    "fuera de aqui", "fuera de aquí", "emigrar", "emigracion", "emigración",
    "largarme", "buscar futuro fuera", "no hay futuro aqui", "no hay futuro aquí",
}
_LLEGADA = {
    "inmigrante", "inmigrantes", "inmigracion", "inmigración", "migrante", "migrantes",
    "llegan personas", "vienen a vivir", "recien llegados", "recién llegados",
    "pateras", "cayucos", "solicitar asilo", "papeles", "regularizacion", "regularización",
    "extranjeros", "refugiados", "asilo",
}
_EMERGENCIA = {
    "invasion", "invasión", "avalancha", "desembarco", "ola imparable", "asalto",
    "hordas", "oleada", "inundacion de", "plaga", "se nos echan encima",
    "nos invaden", "estamos invadidos", "efecto llamada desbordado",
}


def _contiene_alguna(texto: str, lexico: set[str]) -> bool:
    return any(_contiene_palabra(texto.lower(), p) for p in lexico)


# ── 1. Indicador de expulsión ─────────────────────────────────────────────
def indicador_expulsion(docs: Sequence[str]) -> dict[str, Any]:
    """Proporción de docs con intención declarada de irse del territorio.

    Un éxodo potencial se anuncia en la conversación antes que en los datos
    oficiales. Señal: presión de salida emergente.
    """
    if not docs:
        return {"expulsion": 0.0, "n_docs": 0, "nota": "sin docs"}
    n = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _EXPULSION))
    prop = round(n / len(docs), 3)
    return {
        "expulsion": prop,
        "n_expulsion": n,
        "n_docs": len(docs),
        "presion_salida": prop >= 0.1,
    }


# ── 2. Lenguaje de emergencia ─────────────────────────────────────────────
def lenguaje_emergencia(docs: Sequence[str]) -> dict[str, Any]:
    """Proporción de docs de movilidad que usan léxico bélico/de emergencia.

    El paso de "llegan personas" a "invasión/avalancha" es un cambio de marco
    que precede al endurecimiento de política de movilidad o a brotes de
    conflicto. Señal: enmarque de crisis inminente.
    """
    if not docs:
        return {"emergencia": 0.0, "n_docs": 0, "nota": "sin docs"}
    movilidad = [d for d in docs if isinstance(d, str) and _contiene_alguna(d, _LLEGADA)]
    if not movilidad:
        return {"emergencia": 0.0, "n_docs": 0, "n_movilidad": 0, "nota": "sin docs de movilidad"}
    emergencia = sum(1 for d in movilidad if _contiene_alguna(d, _EMERGENCIA))
    ratio = round(emergencia / len(movilidad), 3)
    return {
        "emergencia": ratio,
        "n_emergencia": emergencia,
        "n_movilidad": len(movilidad),
        "n_docs": len(docs),
        "crisis_inminente": ratio >= 0.3,
    }


# ── 3. Balanza llegada ↔ salida ───────────────────────────────────────────
def balanza_movilidad(docs: Sequence[str]) -> dict[str, Any]:
    """Ratio llegada/salida. >1 = tema de atracción; <1 = de expulsión.

    El cruce del ratio en pocas fechas indica un cambio de percepción
    colectiva o de política, antes de los datos oficiales.
    """
    if not docs:
        return {"ratio": 0.0, "llegada": 0, "salida": 0, "nota": "sin docs"}
    llegada = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _LLEGADA))
    salida = sum(1 for d in docs if isinstance(d, str) and _contiene_alguna(d, _EXPULSION))
    ratio = round(llegada / max(salida, 1), 3)
    return {
        "ratio": ratio,
        "llegada": llegada,
        "salida": salida,
        "predominio": "llegada" if ratio > 1 else ("salida" if ratio < 1 else "equilibrio"),
    }


if __name__ == "__main__":
    import json

    expulsion_docs = [
        "me quiero ir de este pais, estoy harto, quiero sacar la visa",
        "busco futuro fuera, me piro en cuanto pueda",
    ]
    print("EXPULSION:  ", json.dumps(indicador_expulsion(expulsion_docs), ensure_ascii=False))

    emergencia_docs = [
        "los inmigrantes son una invasion, una avalancha que nos invade",
        "es un desembarco, oleada imparable, estamos invadidos",
    ]
    print("EMERGENCIA: ", json.dumps(lenguaje_emergencia(emergencia_docs), ensure_ascii=False))

    print("BALANZA:    ", json.dumps(balanza_movilidad(expulsion_docs + emergencia_docs), ensure_ascii=False))
