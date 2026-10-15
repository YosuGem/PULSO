"""
Ampliación de alerta temprana (0.2.2-dev).

Complementa `alerta_temprana.py` con tres métodos que ese módulo no cubre:

  1. **Z-score diario** — normaliza el ruido propio de cada categoría, para
     que las de alto volumen no disparen falsas alarmas y las de bajo volumen
     puedan arrancar. Umbral adaptativo por categoría, no fijo.
  2. **Temperatura / aceleración** — no solo si un tema sube, sino si se
     está *acelerando*. Ordena por aceleración.
  3. **Corroboración multi-fuente** — un spike de un solo foro con un hilo
     viral es ruido; solo sube a la lista si ≥2 fuentes lo dicen el mismo día.

Diseño: stdlib puro, módulos que reciben la serie (no leen la BD), KISS.
Se apoya en `alerta_temprana.py` para la parte estadística.

Fuente: subagente ingeniero de detección temprana.
"""

from __future__ import annotations

import math
from typing import Any, Sequence


# ── Estadística (reutiliza el enfoque de alerta_temprana) ─────────────────
def _media(valores: Sequence[float]) -> float:
    return sum(valores) / len(valores) if valores else 0.0


def _desviacion(valores: Sequence[float]) -> float:
    n = len(valores)
    if n < 2:
        return 0.0
    m = _media(valores)
    return math.sqrt(sum((v - m) ** 2 for v in valores) / (n - 1))


# ── 1. Z-score diario ─────────────────────────────────────────────────────
def zscore_diario(serie: Sequence[dict[str, Any]], ventana: int = 5, umbral: float = 2.0) -> dict[str, Any]:
    """Anomalía del último día contra la media/desviación de los `ventana` previos.

    Devuelve z, si es anomalía, y el volumen de hoy (para no alertar con 1 doc).
    """
    valores = [float(p.get("senal", 0.0)) for p in serie]
    if len(valores) < ventana + 1:
        return {"z": 0.0, "anomalia": False, "hoy": valores[-1] if valores else 0, "nota": "historia insuficiente"}
    previos = valores[-(ventana + 1):-1]
    hoy = valores[-1]
    media = _media(previos)
    sigma = _desviacion(previos)
    if sigma <= 0:
        # Ventana previa constante: el z-score no está definido (división por
        # σ=0). Antes devolvía un valor absurdo (5e9) que contaminaba cualquier
        # ordenación por z. Ahora: si hoy rompe la constancia de forma clara
        # (salto real), se marca anomalía por SALTO ABSOLUTO, no por un z
        # inventado (fallo encontrado en auditoría).
        if hoy > media and hoy >= 3:
            return {
                "z": 0.0,
                "anomalia": True,
                "hoy": hoy,
                "media_previa": round(media, 2),
                "nota": "ventana constante: anomalía por salto absoluto",
            }
        return {
            "z": 0.0,
            "anomalia": False,
            "hoy": hoy,
            "media_previa": round(media, 2),
            "nota": "ventana constante, sin variación real",
        }
    z = (hoy - media) / sigma
    return {
        "z": round(z, 3),
        "anomalia": z > umbral and hoy >= 3,  # mínimo 3 docs para no alertar por ruido
        "hoy": hoy,
        "media_previa": round(media, 2),
    }


# ── 2. Temperatura y aceleración ──────────────────────────────────────────
def temperatura(serie: Sequence[dict[str, Any]], ventana: int = 7) -> dict[str, Any]:
    """temperatura = hoy / media(ventana); aceleración = impulso del último día.

    La aceleración es (hoy − ayer) normalizado por la media, no la diferencia
    de temperaturas niveladas: si el escalón lleva varios días, temp_ayer ya
    incluye valores altos y la diferencia se aplana (fallo detectado al
    probar). Aquí mide el impulso del último movimiento contra su propia
    escala, así un tema que sigue subiendo muestra aceleración positiva.
    """
    valores = [float(p.get("senal", 0.0)) for p in serie]
    if len(valores) < 2:
        return {"temperatura": 0.0, "aceleracion": 0.0, "nota": "historia insuficiente"}

    previos = valores[:-1][-ventana:]
    media = _media(previos) if previos else 0.0
    hoy = valores[-1]
    ayer = valores[-2]

    if media <= 0:
        # Tema que arranca de cero: la razón hoy/media no está definida.
        # Se marca como emergencia_desde_cero con temperatura 0.0 (no un
        # valor mágico tipo 99 que parecería una medida real y dispararía
        # "explota" en falso — fallo encontrado en auditoría).
        if hoy > 0:
            # Aceleración sin media previa: se reporta el salto absoluto,
            # no un ratio contra ~0 (que daría billones). El impulso real es
            # el propio salto desde cero.
            return {
                "temperatura": 0.0,
                "aceleracion": float(hoy - ayer),
                "explota": hoy >= 3,  # de cero a ≥3 docs ya es señal real
                "emergencia_desde_cero": True,
            }
        temperatura_hoy = 0.0
    else:
        temperatura_hoy = round(hoy / media, 3)

    # Impulso relativo: cuánto creció el último día respecto a la escala base.
    impulso = (hoy - ayer) / max(media, 1e-9)

    # "Explota" = temperatura alta (muy por encima de su media) Y todavía
    # subiendo. No se exige además un impulso grande: cuando el escalón lleva
    # varios días la media ya está inflada y el impulso relativo se aplasta
    # aunque el tema siga creciendo (fallo detectado al probar con escalón
    # sostenido). La temperatura ya captura el nivel; aquí solo confirmamos
    # dirección.
    explota = temperatura_hoy >= 2.0 and impulso > 0

    return {
        "temperatura": temperatura_hoy,
        "aceleracion": round(impulso, 3),
        "explota": explota,
    }


# ── 3. Corroboración multi-fuente ─────────────────────────────────────────
def corroboracion(entradas: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Un spike sube a la lista solo si ≥2 fuentes REALES distintas lo dicen.

    `entradas`: cada una trae 'fuentes' (lista de nombres reales). NO se mezcla
    con 'num_fuentes' (conteos sintéticos): eso falseaba la cuenta sumando
    nombres reales con placeholders s0..sn (fallo encontrado en auditoría:
    [fuentes:[foroA], num_fuentes:3] daba 4 fuentes cuando había 1 real).

    Solo se cuentan nombres de fuente reales y se desduplican. Si no hay
    nombres, no se puede corroborar (se devuelve False honesto).
    """
    if not entradas:
        return {"corroborado": False, "num_fuentes": 0}
    fuentes: set[str] = set()
    for e in entradas:
        if not isinstance(e, dict):
            continue
        f = e.get("fuentes")
        if f:
            fuentes.update(str(x) for x in f)
    return {"corroborado": len(fuentes) >= 2, "num_fuentes": len(fuentes)}


def enriquecer_watchlist(wl: list[dict[str, Any]], series: dict[str, Sequence[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Añade z-score, temperatura y corroboración a cada fila de la watchlist.

    Consume la salida de `alerta_temprana.watchlist` y las series por categoría.
    Devuelve la misma lista enriquecida (no reordena).
    """
    for f in wl:
        s = series.get(f["categoria"], [])
        z = zscore_diario(s)
        t = temperatura(s)
        # La corroboración se calcula SOLO si el llamador pasó las fuentes
        # reales del día en la fila (clave 'fuentes_hoy', lista de nombres).
        # Antes leía una clave que watchlist nunca producía, así que la
        # corroboración quedaba muerta (siempre False) sin error que lo
        # delatase — fallo de contrato encontrado en auditoría. Si no hay
        # datos de fuentes, se marca no corroborado de forma honesta.
        fuentes_hoy = f.get("fuentes_hoy")
        corr = corroboracion([{"fuentes": fuentes_hoy}] if fuentes_hoy else [])
        f["z"] = z["z"]
        f["z_anomalia"] = z["anomalia"]
        f["temperatura"] = t["temperatura"]
        f["aceleracion"] = t["aceleracion"]
        f["explota"] = t["explota"]
        f["corroborado"] = corr["corroborado"]
    return wl


# ── Validación: eventos plantados ─────────────────────────────────────────
def backtest_sintetico() -> dict[str, Any]:
    """Genera un evento plantado y comprueba que el detector lo pilla.

    Es la única validación que funciona hoy con pocas fechas reales.
    Determinista: mismo resultado siempre.
    """
    from noosfera_project.servicios.alerta_temprana import cusum, delta_diario

    def s(v: list[float]) -> list[dict]:
        return [{"senal": x} for x in v]

    # Evento plantado: estable y de repente explota el día D
    evento = s([5, 5, 5, 5, 5, 25, 30, 35, 40])
    # Control: tema que nunca cambia
    control = s([10] * 9)
    # Ruido: oscila sin tendencia
    ruido = s([8, 12, 9, 11, 10, 9, 12, 8, 11])

    detectado_evento = cusum(evento)["alerta"]
    detectado_control = cusum(control)["alerta"]
    delta_evento = delta_diario(evento)["direccion"]
    z_evento = zscore_diario(evento)["z"]
    temp_evento = temperatura(evento)

    return {
        "evento_plantado_detectado": detectado_evento,
        "control_sin_alerta": not detectado_control,
        "evento_direccion": delta_evento,
        "evento_z": z_evento,
        "evento_temperatura": temp_evento["temperatura"],
        "evento_explota": temp_evento["explota"],
        "recall": 1.0 if detectado_evento else 0.0,
        "falsos_positivos": 1 if detectado_control else 0,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(backtest_sintetico(), indent=2, ensure_ascii=False))
