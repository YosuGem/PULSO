"""Tests de alerta temprana (0.2.2-dev).

Series sintéticas con patrón de falla conocido, como recomendó el diseño:
escalón, rampa, ruido plano, seno. Cada test fija un comportamiento.
"""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.alerta_temprana import (
    avs,
    cusum,
    delta_diario,
    informe_watchlist,
    watchlist,
)


def _serie(valores: list[float]) -> list[dict]:
    return [{"fecha": f"d{i}", "senal": v} for i, v in enumerate(valores)]


# ── Delta Diario ──────────────────────────────────────────────────────────
def test_delta_subida():
    res = delta_diario(_serie([10, 10, 10, 20]))
    assert res["direccion"] == "subida"
    assert res["delta"] == 10
    assert res["delta_rel"] == pytest.approx(1.0)


def test_delta_bajada():
    res = delta_diario(_serie([20, 20, 20, 5]))
    assert res["direccion"] == "bajada"
    assert res["delta"] == -15


def test_delta_estable():
    res = delta_diario(_serie([10, 10, 10, 10]))
    assert res["direccion"] == "estable"


def test_delta_serie_insuficiente():
    res = delta_diario(_serie([5]))
    assert res["direccion"] == "estable"
    assert "insuficiente" in res["nota"]


# ── AVS (volatilidad) ─────────────────────────────────────────────────────
def test_avs_ruido_alto_vs_plano():
    """Una serie oscilante tiene más AVS que una plana."""
    plano = _serie([10] * 10)
    oscilante = _serie([2, 18, 3, 17, 2, 18, 3, 17, 2, 18])
    assert avs(oscilante) > avs(plano)


def test_avs_plano_es_cero():
    assert avs(_serie([10] * 10)) == 0.0


def test_avs_serie_corta_es_cero():
    assert avs(_serie([10, 12])) == 0.0


# ── CUSUM: deriva vs pico ─────────────────────────────────────────────────
def test_cusum_detecta_escalon_sostenido():
    """Un cambio de régimen sostenido dispara CUSUM."""
    escalon = _serie([5, 5, 5, 5, 5, 15, 15, 15, 15, 15])
    res = cusum(escalon)
    assert res["alerta"] is True
    assert res["direccion"] == "subida"


def test_cusum_ignora_pico_aislado():
    """Un pico de un día no acumula lo suficiente: es ruido, no régimen."""
    pico = _serie([5, 5, 5, 5, 30, 5, 5, 5, 5, 5])
    res = cusum(pico)
    assert res["alerta"] is False


def test_cusum_detecta_bajada_sostenida():
    caida = _serie([20, 20, 20, 20, 20, 5, 5, 5, 5, 5])
    res = cusum(caida)
    assert res["alerta"] is True
    assert res["direccion"] == "bajada"


def test_cusum_plano_no_alerta():
    assert cusum(_serie([10] * 10))["alerta"] is False


# ── Watchlist ─────────────────────────────────────────────────────────────
def test_watchlist_prioriza_volatil_con_deriva():
    """La categoría con deriva sostenida y volumen sube al top."""
    series = {
        "tema_caliente": _serie([5, 5, 5, 5, 5, 20, 20, 25, 30, 35]),
        "tema_tranquilo": _serie([10] * 10),
    }
    wl = watchlist(series)
    assert wl[0]["categoria"] == "tema_caliente"
    assert wl[0]["indice"] > 0


def test_watchlist_excluye_series_cortas():
    series = {"corto": _serie([10, 12])}
    assert watchlist(series) == []


def test_watchlist_vacia_no_rompe():
    assert watchlist({}) == []
    assert "Sin series" in informe_watchlist([])


def test_watchlist_marca_provisional_en_frio():
    """Con pocos días la entrada se marca provisional (revisar a mano)."""
    # MIN_DIAS=3 para entrar a la watchlist; provisional si <5 días.
    series = {"tema": _serie([5, 5, 5, 10])}
    wl = watchlist(series)
    assert wl and wl[0]["provisional"] is True


def test_watchlist_no_provisional_con_historial():
    """Con 5+ días la entrada ya no es provisional."""
    series = {"tema": _serie([5, 5, 5, 5, 5, 10])}
    wl = watchlist(series)
    assert wl and wl[0]["provisional"] is False


def test_informe_watchlist_legible():
    series = {"tema": _serie([5, 5, 5, 20, 20, 25])}
    txt = informe_watchlist(watchlist(series))
    assert "WATCHLIST" in txt
    assert "tema" in txt


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
