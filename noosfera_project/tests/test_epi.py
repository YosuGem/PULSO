"""Tests del modelo epidémico (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.epi import beta, gamma, punto_inflexion, r0


def _s(v):
    return [{"senal": x} for x in v]


# ── Beta (contagio) ───────────────────────────────────────────────────────
def test_beta_crecimiento_positivo():
    assert beta(_s([3, 5, 8, 20, 45, 80])) > 0


def test_beta_decaimiento_cero():
    """Un tema decayendo no tiene contagio (incrementos negativos → 0)."""
    assert beta(_s([50, 20, 10, 5, 2, 1])) == 0.0


# ── Gamma (olvido) ────────────────────────────────────────────────────────
def test_gamma_decae():
    assert gamma(_s([50, 20, 10, 5, 2, 1])) > 0


def test_gamma_persistente_cero():
    """Un tema que nunca cae es endémico: gamma≈0."""
    assert gamma(_s([5, 8, 20, 45, 80, 90])) == 0.0


# ── R0 ────────────────────────────────────────────────────────────────────
def test_r0_crece_solo():
    r = r0(_s([3, 5, 8, 20, 45, 80]))
    assert r["crece_solo"] is True
    assert r["morira"] is False


def test_r0_morira():
    r = r0(_s([50, 20, 10, 5, 2, 1]))
    assert r["morira"] is True
    assert r["crece_solo"] is False


# ── Punto de inflexión ────────────────────────────────────────────────────
def test_inflexion_detecta_codo():
    p = punto_inflexion(_s([3, 5, 8, 20, 45, 80]))
    assert p["es_codo"] is True
    assert p["aceleracion_max"] > 0


def test_inflexion_serie_corta():
    p = punto_inflexion(_s([5]))
    assert "nota" in p


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
