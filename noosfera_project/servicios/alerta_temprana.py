"""
Alerta temprana (0.2.2-dev).

Para qué sirve
--------------
El radar dice qué cambió en una ventana. Estas herramientas responden tres
preguntas que el radar no puede:

  1. **Delta Diario** — ¿qué cambió HOY respecto a AYER, y cuánto en términos
     relativos? Es el ticker.
  2. **AVS** — ¿qué temas son estructuralmente volátiles y merecen vigilancia
     diaria frente a los que solo merecen semanal?
  3. **CUSUM** — ¿esto es un pico de un día (ruido) o un cambio de régimen
     real (el tema arranca de verdad)? Acumula deriva en una dirección.
  4. **Watchlist** — una sola lista accionable: qué vigilar mañana.

Arranque en frío
----------------
Con pocos días de historia la desviación típica no es fiable. Se aplica
*shrinkage*: la varianza muestral se encoge hacia la varianza previa del
sistema (media de las varianzas de todas las categorías), y los umbrales se
escalan por raíz de n. Resultado: menos falsas alarmas los primeros días,
detección que se afina sola con el tiempo.

Diseño
------
- Solo stdlib: sin numpy. Estadísticas acumuladas.
- Bajo acoplamiento: `delta_diario`, `avs`, `cusum` y `watchlist` reciben la
  serie como lista de dicts, no leen la base de datos. Así se pueden probar
  con series sintéticas.
- `watchlist_desde_bd` es el adaptador que lee el histórico real.

Fuente del diseño: subagente ingeniero de alerta temprana.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Sequence

# ── Parámetros del sistema (no por dato) ──────────────────────────────────
VENTANA_AVS = 14          # días para calcular volatilidad relativa
KAPPA = 3                 # fuerza del shrinkage hacia la varianza previa
MIN_DIAS = 3              # días mínimos para considerar una serie
K_CUSUM = 0.5             # holgura de deriva tolerada (en fracciones de sigma)
H_CUSUM = 4.0             # umbral de decisión CUSUM (en fracciones de sigma)
UMBRAL_SUBIDA = 0.25      # Δrel a partir del cual se considera subida
PESO_AVS = 0.4            # peso de la volatilidad en la watchlist
PESO_DELTA = 0.4          # peso del delta diario en la watchlist
PESO_CUSUM = 0.2          # peso de la deriva en la watchlist
TOP_WATCHLIST = 10


# ── Estadística básica (stdlib) ───────────────────────────────────────────
def _media(valores: Sequence[float]) -> float:
    return sum(valores) / len(valores) if valores else 0.0


def _varianza_muestral(valores: Sequence[float]) -> float:
    """Varianza muestral (n-1). 0.0 si no hay suficientes datos."""
    n = len(valores)
    if n < 2:
        return 0.0
    m = _media(valores)
    return sum((v - m) ** 2 for v in valores) / (n - 1)


def _sigma_encogida(valores: Sequence[float], previa: float) -> float:
    """Sigma con shrinkage hacia la varianza previa del sistema.

    sigma² = (n·sigma_muestral² + kappa·previa²) / (n + kappa)
    """
    n = len(valores)
    if n == 0:
        return previa
    muestral = _varianza_muestral(valores)
    previa2 = previa * previa
    encogida = (n * muestral + KAPPA * previa2) / (n + KAPPA)
    return math.sqrt(max(encogida, 0.0))


def _normalizar(valores: Sequence[float]) -> list[float]:
    """Escala a [0,1] por el máximo. Todos cero si el máximo es cero."""
    mx = max(valores) if valores else 0.0
    if mx <= 0:
        return [0.0] * len(valores)
    return [v / mx for v in valores]


# ── 1. Delta Diario ───────────────────────────────────────────────────────
def delta_diario(serie: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Compara el último valor contra el anterior de una categoría.

    `serie`: [{"fecha": ..., "senal": float}, ...] ordenada por fecha.
    Devuelve direccion (subida/baja/estable), delta, delta_rel y nivel.
    """
    if len(serie) < 2:
        return {"direccion": "estable", "delta": 0.0, "delta_rel": 0.0, "nota": "serie insuficiente"}
    hoy = float(serie[-1].get("senal", 0.0))
    ayer = float(serie[-2].get("senal", 0.0))
    delta = hoy - ayer
    delta_rel = delta / max(abs(ayer), 1e-9)
    if delta_rel >= UMBRAL_SUBIDA:
        direccion = "subida"
    elif delta_rel <= -UMBRAL_SUBIDA:
        direccion = "bajada"
    else:
        direccion = "estable"
    return {
        "direccion": direccion,
        "delta": round(delta, 3),
        "delta_rel": round(delta_rel, 3),
        "hoy": hoy,
        "ayer": ayer,
    }


# ── 2. Volatilidad adaptativa (AVS) ───────────────────────────────────────
def avs(serie: Sequence[dict[str, Any]], previa_sigma: float = 0.0) -> float:
    """Volatilidad relativa: sigma / max(mu, eps) sobre la ventana reciente.

    Con shrinkage hacia `previa_sigma` (sigma del sistema) para no disparar
    falsas alarmas con pocos días.
    """
    valores = [float(p.get("senal", 0.0)) for p in serie[-VENTANA_AVS:]]
    if len(valores) < MIN_DIAS:
        return 0.0
    sigma = _sigma_encogida(valores, previa_sigma)
    mu = _media(valores)
    return round(sigma / max(mu, 1e-9), 3)


# ── 3. CUSUM: deriva real vs pico ─────────────────────────────────────────
def cusum(serie: Sequence[dict[str, Any]], previa_sigma: float = 0.0) -> dict[str, Any]:
    """Acumula desviaciones en una dirección y declara cambio de régimen.

    Un pico aislado nunca acumula lo suficiente; una tendencia sostenida sí.
    Devuelve si hay alerta, en qué dirección, y cuántos días lleva acumulando
    (la convicción).
    """
    valores = [float(p.get("senal", 0.0)) for p in serie]
    if len(valores) < MIN_DIAS:
        return {"alerta": False, "direccion": None, "dias_acumulando": 0, "acumulado": 0.0}

    # Línea base y sigma de la PRIMERA MITAD de la serie (la ventana previa
    # estable), no de toda la serie: si el cambio ya está en la serie, incluirla
    # infla sigma y el umbral CUSUM se vuelve inalcanzable — fallo de diseño
    # detectado al probar con un escalón. La mitad inicial es el "régimen
    # anterior" contra el que medimos la deriva.
    mitad = max(len(valores) // 2, MIN_DIAS)
    previos = valores[:mitad]
    base = _media(previos)
    sigma = _sigma_encogida(previos, previa_sigma)
    if sigma <= 0:
        sigma = max(abs(base) * 0.1, 1e-9)

    k = K_CUSUM * sigma
    h = H_CUSUM * sigma

    s_pos = 0.0
    s_neg = 0.0
    racha_pos = racha_neg = mejor_pos = mejor_neg = 0
    for x in valores:
        s_pos = max(0.0, s_pos + (x - base - k))
        s_neg = max(0.0, s_neg - (x - base + k))
        if s_pos > 0:
            racha_pos += 1
            mejor_pos = max(mejor_pos, racha_pos)
        else:
            racha_pos = 0
        if s_neg > 0:
            racha_neg += 1
            mejor_neg = max(mejor_neg, racha_neg)
        else:
            racha_neg = 0

    if s_pos > h:
        return {"alerta": True, "direccion": "subida", "dias_acumulando": mejor_pos,
                "acumulado": round(s_pos, 3), "umbral": round(h, 3)}
    if s_neg > h:
        return {"alerta": True, "direccion": "bajada", "dias_acumulando": mejor_neg,
                "acumulado": round(s_neg, 3), "umbral": round(h, 3)}
    return {"alerta": False, "direccion": None,
            "dias_acumulando": max(mejor_pos, mejor_neg),
            "acumulado": round(max(s_pos, s_neg), 3), "umbral": round(h, 3)}


# ── 6. Watchlist priorizada ───────────────────────────────────────────────
def watchlist(series: dict[str, Sequence[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Índice compuesto por categoría: qué vigilar mañana.

    índice = 0.4·AVS + 0.4·|Δrel| + 0.2·CUSUM_activo
    """
    if not series:
        return []

    # Varianza previa del sistema para el shrinkage (arranque en frío)
    varianzas = [_varianza_muestral([float(p.get("senal", 0.0)) for p in s]) for s in series.values()]
    previa_sigma = math.sqrt(_media(varianzas)) if varianzas else 0.0

    filas = []
    for cat, serie in series.items():
        if len(serie) < MIN_DIAS:
            continue
        a = avs(serie, previa_sigma)
        d = delta_diario(serie)
        c = cusum(serie, previa_sigma)
        filas.append({
            "categoria": cat,
            "avs": a,
            "delta_rel": abs(d["delta_rel"]),
            "direccion": d["direccion"],
            "cusum": c["alerta"],
            "cusum_dir": c["direccion"],
            "dias": len(serie),
            "provisional": len(serie) < 5,  # arranque en frío: revisar a mano
        })

    if not filas:
        return []

    # Normalizar cada componente sobre el conjunto para que los pesos signifiquen
    n_avs = _normalizar([f["avs"] for f in filas])
    n_delta = _normalizar([f["delta_rel"] for f in filas])
    for f, na, nd in zip(filas, n_avs, n_delta):
        f["indice"] = round(PESO_AVS * na + PESO_DELTA * nd + (PESO_CUSUM if f["cusum"] else 0.0), 3)
        motivos = []
        if f["cusum"]:
            motivos.append(f"deriva sostenida ({f['cusum_dir']})")
        # Solo mencionar el pico si el delta normalizado es alto; "estable"
        # con índice alto ya no se presenta como paradoja "pico estable".
        if nd >= 0.5 and f["direccion"] != "estable":
            motivos.append(f"pico {f['direccion']}")
        if na >= 0.5:
            motivos.append("estructuralmente volátil")
        f["motivo"] = ", ".join(motivos) or "sin anomalía destacable"

    filas.sort(key=lambda x: x["indice"], reverse=True)
    return filas[:TOP_WATCHLIST]


# ── Adaptador a la base de datos ──────────────────────────────────────────
def series_desde_bd(limite_por_cat: int = 60) -> dict[str, list[dict[str, Any]]]:
    """Lee el histórico real y lo convierte en series por categoría."""
    from noosfera_project.servicios.historico_analisis import serie

    from noosfera_project.servicios.historico_analisis import resumen
    cats = _categorias_historicas()
    return {cat: serie(cat, limite_por_cat) for cat in cats}


def _categorias_historicas() -> list[str]:
    """Categorías presentes en analisis_historico."""
    import sqlite3

    from noosfera_project.servicios.persistencia import DB_PATH

    conn = sqlite3.connect(str(DB_PATH))
    try:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT categoria FROM analisis_historico ORDER BY categoria"
        )]
    finally:
        conn.close()


def watchlist_desde_bd() -> list[dict[str, Any]]:
    """Watchlist calculada sobre el histórico real."""
    return watchlist(series_desde_bd())


def informe_watchlist(filas: list[dict[str, Any]]) -> str:
    """Texto legible de la watchlist."""
    lineas = ["WATCHLIST — qué vigilar", ""]
    if not filas:
        lineas.append("  Sin series suficientes (se necesitan 3+ días por categoría).")
        return "\n".join(lineas)
    for i, f in enumerate(filas, 1):
        marca = " (provisional)" if f.get("provisional") else ""
        lineas.append(
            f"  {i:2}. {f['categoria']:24} índice={f['indice']:.3f} "
            f"avs={f['avs']:.2f} Δ={f['direccion']:6} "
            f"cusum={'sí' if f['cusum'] else 'no'}{marca}"
        )
        lineas.append(f"      motivo: {f['motivo']}")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(informe_watchlist(watchlist_desde_bd()))
