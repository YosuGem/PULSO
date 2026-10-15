"""
Señal de series cortas (0.2.2-dev).

Complementa `alerta_ampliada.py` con técnicas que funcionan con 3-10 días —
la restricción real del proyecto, donde el histórico apenas arranca. Ninguna
duplica lo que ya existe (radar, CUSUM, z-score, AVS, delta diario).

Cuatro técnicas, de menor a mayor compuesto:

  1. **Rachas / test de signos** — tendencia direccional sin suponer
     normalidad. Inmune a outliers y a la magnitud del ruido, justo lo que
     rompe un z-score con pocos puntos.
  2. **Patrones cualitativos** — la FORMA del arranque (brote vertical, rampa
     sostenida, zigzag) en vez de la magnitud. Reglas legibles y auditables.
  3. **Rotura de récord** — el tema supera por primera vez su propio histórico.
     El caso "emergente desde cero", sin línea base previa.
  4. **Ensemble** — vota las tres anteriores por log-odds. Ninguna dispara
     sola con 3 puntos; el consenso sí.

Diseño: stdlib puro, reciben la serie como parámetro, KISS.
Fuente: subagente científico de datos de series cortas.
"""

from __future__ import annotations

import math
from typing import Any, Sequence


def _senal(v: float) -> int:
    """Signo de la diferencia día a día: +1 sube, -1 baja, 0 plano."""
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


# ── 1. Rachas / test de signos ────────────────────────────────────────────
def rachas(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Cuenta signos de las diferencias y la racha más larga en una dirección.

    Test exacto: bajo azar, una racha de k signos iguales tiene probabilidad
    2/2^k. Con 5 signos del mismo sentido ya es improbable (p≈0.06); con 6,
    p≈0.03. No depende de la magnitud, solo de la dirección.
    """
    valores = [float(p.get("senal", 0.0)) for p in serie]
    if len(valores) < 3:
        return {"direccion": "estable", "racha": 0, "prob": 1.0, "nota": "historia insuficiente"}

    signos = [_senal(valores[i] - valores[i - 1]) for i in range(1, len(valores))]
    # Los signos 0 (día plano) no cuentan como racha
    signos = [s for s in signos if s != 0]
    if not signos:
        return {"direccion": "estable", "racha": 0, "prob": 1.0}

    mejor_dir, mejor_len, cur_dir, cur_len = 0, 0, signos[0], 1
    for s in signos[1:]:
        if s == cur_dir:
            cur_len += 1
        else:
            if cur_len > mejor_len:
                mejor_dir, mejor_len = cur_dir, cur_len
            cur_dir, cur_len = s, 1
    if cur_len > mejor_len:
        mejor_dir, mejor_len = cur_dir, cur_len

    # Probabilidad bajo azar de una racha de esta longitud
    prob = 2.0 / (2 ** mejor_len)
    return {
        "direccion": "subida" if mejor_dir > 0 else ("bajada" if mejor_dir < 0 else "estable"),
        "racha": mejor_len,
        "prob": round(prob, 4),
        "significativo": prob < 0.10,  # umbral laxo: con 3-6 puntos exigir 0.05 es demasiado
    }


# ── 2. Patrones cualitativos ──────────────────────────────────────────────
def patron(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Clasifica la FORMA del arranque, no la magnitud.

    Diferencia un brote vertical (↑↑) de una rampa sostenida (↑ suaves) o un
    zigzag ruidoso (↑↓↑). Reglas legibles: auditables sin ver números.
    """
    valores = [float(p.get("senal", 0.0)) for p in serie]
    if len(valores) < 3:
        return {"forma": "indeterminada", "simbolos": "", "nota": "historia insuficiente"}

    difs = [valores[i] - valores[i - 1] for i in range(1, len(valores))]
    # Símbolos: ↑ si sube, ↓ si baja, 0 si no cambia
    simbolos = "".join("↑" if d > 0 else ("↓" if d < 0 else "0") for d in difs)

    subidas = simbolos.count("↑")
    bajadas = simbolos.count("↓")

    if subidas == len(simbolos) and subidas >= 2:
        forma = "brote vertical" if subidas >= 3 else "escalada limpia"
    elif subidas > bajadas and subidas >= 2:
        forma = "rampa con ruido"
    elif subidas == bajadas and subidas > 0:
        forma = "zigzag"
    elif bajadas > subidas:
        forma = "decaimiento"
    else:
        forma = "plano"

    return {"forma": forma, "simbolos": simbolos, "subidas": subidas, "bajadas": bajadas}


# ── 3. Rotura de récord ───────────────────────────────────────────────────
def records(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Cuenta cuántas veces el valor supera el máximo de todos los anteriores.

    Bajo azar los récords decrecen como 1/n; un exceso indica crecimiento
    real. Natural para temas nuevos sin línea base: el primer valor ya es un
    récord, y una racha de récords es señal de emergencia desde cero.
    """
    valores = [float(p.get("senal", 0.0)) for p in serie]
    if len(valores) < 3:
        return {"records": 0, "ritmo": 0.0, "nota": "historia insuficiente"}

    max_previo = valores[0]
    records = 0
    for v in valores[1:]:
        if v > max_previo:
            records += 1
            max_previo = v

    # Esperados bajo azar: H(n-1) ≈ ln(n). Exceso = records - ln(n-1)
    esperados = math.log(len(valores)) if len(valores) > 1 else 0
    exceso = records - esperados
    return {
        "records": records,
        "esperados": round(esperados, 2),
        "exceso": round(exceso, 2),
        "ritmo": round(records / (len(valores) - 1), 3),
        "anomalo": exceso > 1.0,  # más récords de los que el azar produciría
    }


# ── 4. Ensemble (votación log-odds) ───────────────────────────────────────
def ensemble(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Combina rachas, patrón y récords por log-odds.

    Cada técnica emite un veredicto con su fiabilidad; se suman log-odds
    ponderados. Ninguna dispara sola con 3 puntos; el consenso sí.
    """
    r = rachas(serie)
    p = patron(serie)
    rec = records(serie)

    if "nota" in r and "insuficiente" in r.get("nota", ""):
        return {"veredicto": "indeterminado", "score": 0.0, "votos": 0, "nota": r["nota"]}

    # Log-odds base (fiabilidad previa de cada técnica, calibrada laxa para
    # series cortas). Cada una aporta a favor o en contra de "emergente".
    log_odds = 0.0
    votos = 0

    if r.get("significativo") and r["direccion"] == "subida":
        log_odds += 1.2
        votos += 1
    elif r.get("significativo") and r["direccion"] == "bajada":
        log_odds -= 1.2
        votos += 1

    if p.get("forma") in ("brote vertical", "escalada limpia", "rampa con ruido"):
        log_odds += 0.9
        votos += 1
    elif p.get("forma") in ("decaimiento", "zigzag"):
        log_odds -= 0.6

    if rec.get("anomalo"):
        log_odds += 1.0
        votos += 1

    # Umbral de decisión: consenso (≥2 votos) o señal muy fuerte (≥1.5)
    if log_odds >= 1.5 and votos >= 2:
        veredicto = "emergente"
    elif log_odds >= 1.5 and votos == 1:
        veredicto = "posible"
    elif log_odds <= -1.5:
        veredicto = "decae"
    else:
        veredicto = "estable"

    return {
        "veredicto": veredicto,
        "score": round(log_odds, 3),
        "votos": votos,
        "detalle": {"rachas": r, "patron": p, "records": rec},
    }


if __name__ == "__main__":
    import json

    series = {
        "brote": [3, 3, 8, 20, 45],
        "rampa": [10, 12, 14, 16, 18],
        "ruido": [8, 12, 9, 11, 10],
        "plano": [10, 10, 10, 10, 10],
    }
    for nombre, vals in series.items():
        s = [{"senal": v} for v in vals]
        print(f"{nombre:8} -> {json.dumps(ensemble(s), ensure_ascii=False)}")
