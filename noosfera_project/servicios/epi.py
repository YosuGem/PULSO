"""
Modelo epidémico de ideas (0.2.2-dev).

Aplica la lógica SIR (Susceptibles-Infectados-Recuperados) a la propagación de
temas en los foros. Un tema es una "idea" que infecta a una comunidad:

  - **β (tasa de contagio)** — cuántos docs nuevos lo mencionan cada día.
  - **γ (tasa de olvido)** — cuándo el flujo cae tras el pico (media-vida).
  - **R₀ = β/γ** — número reproductivo. R₀>1 → el tema crece solo; R₀<1 →
    morirá. Es el ranking natural de alertas.
  - **Punto de inflexión** — el codo donde la aceleración cambia de signo:
    la ventana para actuar antes de que el tema sea obvio.

Consume la serie diaria por categoría (la que ya guarda el registro diario),
así que encaja con la infraestructura existente sin tocar la detección.

Diseño: stdlib puro (math). Bajo acoplamiento: `beta`, `gamma`, `r0` e
`inflexion` reciben la serie temporal, no leen la BD.
Fuente: subagente epidemiólogo de la información.
"""

from __future__ import annotations

from typing import Any, Sequence


# ── β: tasa de contagio (docs nuevos por día) ─────────────────────────────
def beta(serie: Sequence[dict[str, Any]]) -> float:
    """Tasa de contagio: incremento medio diario de menciones.

    Sobre la ventana reciente (segunda mitad), mide docs nuevos/día. Con
    escala creciente, β>0 indica fase de crecimiento.
    """
    vals = [float(p.get("senal", 0.0)) for p in serie]
    if len(vals) < 2:
        return 0.0
    reciente = vals[len(vals) // 2:]
    if len(reciente) < 2:
        return 0.0
    incrementos = [reciente[i] - reciente[i - 1] for i in range(1, len(reciente))]
    return round(sum(max(0, d) for d in incrementos) / len(incrementos), 3)


# ── γ: tasa de olvido (media-vida del tema) ───────────────────────────────
def gamma(serie: Sequence[dict[str, Any]]) -> float:
    """Tasa de olvido: inverso de la media-vida.

    Media-vida = días desde el pico hasta que el flujo cae por debajo del 30%
    del pico. γ = 1/media_vida. Si el tema no ha decaído, γ≈0 (persistente).
    """
    vals = [float(p.get("senal", 0.0)) for p in serie]
    if len(vals) < 2:
        return 0.0
    pico = max(vals)
    if pico <= 0:
        return 0.0
    idx_pico = vals.index(pico)
    umbral = pico * 0.3
    for i in range(idx_pico + 1, len(vals)):
        if vals[i] < umbral:
            media_vida = i - idx_pico
            return round(1.0 / media_vida, 3) if media_vida > 0 else 0.0
    return 0.0  # no ha decaído: endémico/persistente


# ── R₀ = β/γ ──────────────────────────────────────────────────────────────
def r0(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Número reproductivo básico de la idea.

    R₀>1 → el tema se sostiene y crece. R₀<1 → morirá solo. Con γ≈0 (no ha
    decaído), R₀ se reporta como alto (crecimiento sin freno conocido).
    """
    b = beta(serie)
    g = gamma(serie)
    if g == 0:
        # Sin decaimiento observado: si además crece, R₀ efectivamente alto.
        r0_val = 99.0 if b > 0 else 1.0
    else:
        r0_val = round(b / g, 2)
    return {
        "beta": b,
        "gamma": g,
        "r0": r0_val,
        "crece_solo": r0_val > 1,
        "morira": r0_val < 1,
    }


# ── Punto de inflexión (codo de contagio) ─────────────────────────────────
def punto_inflexion(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Detecta el codo donde la aceleración cambia de signo.

    Suaviza la serie (media móvil de 3) y busca el máximo de la segunda
    derivada: es el momento de máxima aceleración, la ventana para actuar
    antes de que el tema sea obvio.
    """
    vals = [float(p.get("senal", 0.0)) for p in serie]
    if len(vals) < 3:
        return {"inflexion": None, "aceleracion_max": 0.0, "nota": "serie muy corta"}
    # Suavizado de 3
    suave = [
        (vals[i - 1] + vals[i] + vals[i + 1]) / 3
        for i in range(1, len(vals) - 1)
    ]
    if len(suave) < 3:
        return {"inflexion": None, "aceleracion_max": 0.0, "nota": "serie muy corta"}
    # Segunda derivada
    acels = [suave[i + 1] - 2 * suave[i] + suave[i - 1] for i in range(1, len(suave) - 1)]
    if not acels:
        return {"inflexion": None, "aceleracion_max": 0.0, "nota": "sin aceleración"}
    idx_max = acels.index(max(acels))
    return {
        "inflexion": idx_max + 1,  # posición aproximada en la serie original
        "aceleracion_max": round(max(acels), 3),
        "es_codo": max(acels) > 0,
    }


if __name__ == "__main__":
    import json

    def s(v):
        return [{"senal": x} for x in v]

    print("TEMA EXPLOSIVO [3,5,8,20,45,80]:")
    print("  ", json.dumps(r0(s([3, 5, 8, 20, 45, 80])), ensure_ascii=False))
    print("  ", json.dumps(punto_inflexion(s([3, 5, 8, 20, 45, 80])), ensure_ascii=False))
    print("TEMA QUE MUERE [50,20,10,5,2,1]:")
    print("  ", json.dumps(r0(s([50, 20, 10, 5, 2, 1])), ensure_ascii=False))
