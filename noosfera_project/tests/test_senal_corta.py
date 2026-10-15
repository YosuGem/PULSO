"""Tests de señal de series cortas (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.senal_corta import ensemble, patron, rachas, records


def _s(v: list[float]) -> list[dict]:
    return [{"senal": x} for x in v]


# ── Rachas / signos ───────────────────────────────────────────────────────
def test_rachas_subida_sostenida():
    r = rachas(_s([10, 12, 14, 16, 18]))
    assert r["direccion"] == "subida"
    assert r["racha"] == 4


def test_rachas_bajada():
    r = rachas(_s([20, 18, 15, 12, 10]))
    assert r["direccion"] == "bajada"
    assert r["racha"] == 4


def test_rachas_zigzag_no_significativo():
    r = rachas(_s([10, 12, 10, 12, 10]))
    assert r["significativo"] is False


def test_rachas_corta_insuficiente():
    r = rachas(_s([10, 12]))
    assert "insuficiente" in r["nota"]


# ── Patrón ────────────────────────────────────────────────────────────────
def test_patron_brote_vertical():
    p = patron(_s([5, 25, 60, 120]))
    assert p["forma"] == "brote vertical"
    assert "↑" in p["simbolos"]


def test_patron_zigzag():
    p = patron(_s([10, 15, 12, 17, 14]))
    assert p["forma"] == "zigzag"


def test_patron_plano():
    p = patron(_s([10, 10, 10, 10]))
    assert p["forma"] == "plano"


def test_patron_decaimiento():
    p = patron(_s([30, 25, 20, 15, 10]))
    assert p["forma"] == "decaimiento"


# ── Récords ───────────────────────────────────────────────────────────────
def test_records_brote_anomalo():
    r = records(_s([3, 3, 8, 20, 45]))
    assert r["records"] == 3
    assert r["anomalo"] is True


def test_records_plano_no_anomalo():
    r = records(_s([10, 10, 10, 10, 10]))
    assert r["records"] == 0
    assert r["anomalo"] is False


# ── Ensemble ──────────────────────────────────────────────────────────────
def test_ensemble_brote_emergente():
    e = ensemble(_s([3, 3, 8, 20, 45]))
    assert e["veredicto"] in ("emergente", "posible")
    assert e["votos"] >= 2


def test_ensemble_plano_estable():
    e = ensemble(_s([10, 10, 10, 10, 10]))
    assert e["veredicto"] == "estable"
    assert e["score"] == 0.0


def test_ensemble_ruido_no_dispara():
    """El ruido no debe disparar el ensemble (pocos falsos positivos)."""
    e = ensemble(_s([8, 12, 9, 11, 10]))
    assert e["veredicto"] in ("estable", "posible")
    # No debe ser emergente solo por ruido
    assert e["veredicto"] != "emergente"


def test_ensemble_corto_insuficiente():
    e = ensemble(_s([10, 12]))
    assert e["veredicto"] == "indeterminado"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
