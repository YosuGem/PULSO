"""Tests de alerta ampliada (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.alerta_ampliada import (
    backtest_sintetico,
    corroboracion,
    enriquecer_watchlist,
    temperatura,
    zscore_diario,
)


def _s(v: list[float]) -> list[dict]:
    return [{"senal": x} for x in v]


# ── Z-score ───────────────────────────────────────────────────────────────
def test_zscore_detecta_anomalia():
    # Serie con variación real: último punto muy por encima de media/sigma
    z = zscore_diario(_s([5, 8, 6, 9, 7, 50]), ventana=5)
    assert z["z"] > 2.0
    assert z["anomalia"] is True


def test_zscore_ventana_constante_salto_absoluto():
    """Con ventana previa constante el z no está definido (σ=0). Antes daba
    z=5e9 absurdo. Ahora: salto real claro se marca anomalía sin inventar z
    (fallo de auditoría)."""
    z = zscore_diario(_s([0, 0, 0, 0, 0, 5]), ventana=5)
    assert z["z"] == 0.0
    assert z["anomalia"] is True
    assert "salto absoluto" in z["nota"]


def test_zscore_ventana_constante_sin_variacion():
    """Si hoy no rompe la constancia, no es anomalía."""
    z = zscore_diario(_s([0, 0, 0, 0, 0, 1]), ventana=5)
    assert z["z"] == 0.0
    assert z["anomalia"] is False


def test_zscore_no_alerta_con_poco_volumen():
    # Aunque z sea alto, 1 solo doc no alerta (ruido)
    z = zscore_diario(_s([0, 0, 0, 0, 0, 1]), ventana=5)
    assert z["anomalia"] is False


def test_zscore_estable_no_alerta():
    z = zscore_diario(_s([10, 10, 10, 10, 10, 10]), ventana=5)
    assert z["anomalia"] is False


# ── Temperatura / aceleración ─────────────────────────────────────────────
def test_temperatura_explota():
    t = temperatura(_s([5, 5, 5, 5, 5, 25, 30, 35, 40]), ventana=7)
    assert t["temperatura"] >= 2.0
    assert t["explota"] is True


def test_temperatura_estable():
    t = temperatura(_s([10] * 9), ventana=7)
    assert t["temperatura"] == pytest.approx(1.0, abs=0.01)
    assert t["explota"] is False


def test_aceleracion_positiva_en_escalon():
    t = temperatura(_s([5, 5, 5, 5, 5, 25, 30]), ventana=7)
    assert t["aceleracion"] > 0


def test_temperatura_desde_cero_no_valor_magico():
    """Un tema que arranca de cero NO debe reportar temperatura 99 (fallo
    encontrado en auditoría: parecía medida real y disparaba 'explota' en
    falso). Debe marcarse como emergencia desde cero."""
    t = temperatura(_s([0, 0, 0, 0, 0, 5]), ventana=7)
    assert t["temperatura"] == 0.0
    assert t.get("emergencia_desde_cero") is True
    assert t["explota"] is True  # de cero a 5 sí es señal
    assert t["aceleracion"] == 5.0  # salto absoluto, no un ratio astronómico


def test_temperatura_desde_cero_bajo_umbral():
    """De cero a 1 doc no es 'explota' (demasiado poco)."""
    t = temperatura(_s([0, 0, 0, 0, 0, 1]), ventana=7)
    assert t["explota"] is False


# ── Corroboración ─────────────────────────────────────────────────────────
def test_corroboracion_una_fuente_no_alcanza():
    assert corroboracion([{"fuentes": ["foroX"]}])["corroborado"] is False


def test_corroboracion_dos_fuentes_alcanza():
    r = corroboracion([{"fuentes": ["foroX", "reddit"]}])
    assert r["corroborado"] is True
    assert r["num_fuentes"] == 2


def test_corroboracion_vacio():
    assert corroboracion([])["corroborado"] is False


def test_corroboracion_no_mezcla_num_fuentes():
    """No debe contar nombres reales junto a conteos sintéticos (fallo de
    auditoría: [fuentes:[foroA], num_fuentes:3] daba 4 fuentes cuando
    realmente hay 1 sola)."""
    r = corroboracion([{"fuentes": ["foroA"]}, {"num_fuentes": 3}])
    assert r["num_fuentes"] == 1
    assert r["corroborado"] is False


def test_corroboracion_desduplica_misma_fuente():
    """La misma fuente en varios docs cuenta una sola vez."""
    r = corroboracion([{"fuentes": ["foroA"]}, {"fuentes": ["foroA"]}])
    assert r["num_fuentes"] == 1
    assert r["corroborado"] is False


def test_enriquecer_corroboracion_solo_con_fuentes_reales():
    """La corroboración se activa solo si la fila trae 'fuentes_hoy' real
    (fallo de contrato: antes leía una clave inexistente y quedaba muerta)."""
    wl = [{"categoria": "t", "indice": 1.0, "fuentes_hoy": ["foroA", "reddit"]}]
    series = {"t": _s([5, 5, 5, 5, 5, 25])}
    out = enriquecer_watchlist(wl, series)
    assert out[0]["corroborado"] is True

    wl2 = [{"categoria": "t", "indice": 1.0}]  # sin fuentes_hoy
    out2 = enriquecer_watchlist(wl2, series)
    assert out2[0]["corroborado"] is False


# ── Enriquecer watchlist ──────────────────────────────────────────────────
def test_enriquecer_anade_campos():
    wl = [{"categoria": "t", "indice": 1.0}]
    series = {"t": _s([5, 5, 5, 5, 5, 25, 30])}
    out = enriquecer_watchlist(wl, series)
    assert "z" in out[0] and "temperatura" in out[0] and "aceleracion" in out[0]
    assert "corroborado" in out[0]


# ── Backtest sintético ────────────────────────────────────────────────────
def test_backtest_detecta_evento_y_ignora_control():
    r = backtest_sintetico()
    assert r["evento_plantado_detectado"] is True
    assert r["control_sin_alerta"] is True
    assert r["recall"] == 1.0
    assert r["falsos_positivos"] == 0
    assert r["evento_explota"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# ── Inversión temporal (fallo crítico de auditoría) ───────────────────────
def _leer_fuente_historico() -> str:
    from pathlib import Path

    ruta = Path(__file__).resolve().parent.parent / "servicios" / "historico_analisis.py"
    return ruta.read_text(encoding="utf-8")


def test_serie_orden_ascendente():
    """serie() debe devolver los puntos ASCENDENTES: los detectores tratan
    serie[-1] como 'hoy'. Antes usaba ORDER BY fecha DESC e invertía el
    veredicto en cuanto había 2+ fechas (fallo crítico)."""
    src = _leer_fuente_historico()
    # La query de serie() es la que filtra por categoría; verificamos ESE
    # fragmento (el docstring menciona DESC solo para explicar el fallo).
    lineas = src.splitlines()
    idx = next(
        i for i, ln in enumerate(lineas)
        if "FROM analisis_historico WHERE categoria" in ln
    )
    query_real = lineas[idx]
    assert "ASC" in query_real, "la query de serie() debe ordenar ASC"
    assert "DESC" not in query_real, "la query de serie() no debe ordenar DESC"


def test_serie_expone_clave_senal():
    """Cada punto debe traer 'senal' (conteo del día) que es lo que leen los
    detectores; antes solo traía 'documentos' y todo leía 0."""
    src = _leer_fuente_historico()
    assert '"senal"' in src or "'senal'" in src
