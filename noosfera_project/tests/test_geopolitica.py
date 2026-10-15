"""Tests de geopolítica (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.geopolitica import calentamiento, eufemismo, ultimatum


# ── Calentamiento discursivo ──────────────────────────────────────────────
def test_calentamiento_detecta_beligerancia():
    docs = [
        "amenazan con sanciones y embargo si no hay acuerdo",
        "la escalada del conflicto avanza, advertencia de represalias",
    ]
    c = calentamiento(docs)
    assert c["beligerancia"] > 0.5
    assert c["caldeado"] is True


def test_calentamiento_neutro():
    docs = ["hoy hace buen dia", "me gusta el cafe de la manana"]
    c = calentamiento(docs)
    assert c["caldeado"] is False


# ── Eufemismo ─────────────────────────────────────────────────────────────
def test_eufemismo_operacion_encubierta():
    docs = [
        "es una operacion especial, una mision de paz",
        "medidas cautelares y restricciones comerciales, accion preventiva",
    ]
    e = eufemismo(docs)
    assert e["n_eufemismos"] >= 2
    assert e["operacion_encubierta"] is True


def test_eufemismo_sin_eufemismos():
    docs = ["el partido de futbol acabo en empate"]
    e = eufemismo(docs)
    assert e["operacion_encubierta"] is False


# ── Ultimátum ─────────────────────────────────────────────────────────────
def test_ultimatum_discurso():
    docs = [
        "o acepta las condiciones o habra represalias",
        "es la ultima oportunidad, si no cumple actuaremos",
    ]
    u = ultimatum(docs)
    assert u["ultimatum"] > 0.5
    assert u["discurso_ultimatum"] is True


def test_ultimatum_no_dispara():
    docs = ["podemos dialogar y llegar a un acuerdo tranquilo"]
    u = ultimatum(docs)
    assert u["discurso_ultimatum"] is False


def test_vacio():
    assert "sin docs" in calentamiento([])["nota"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
