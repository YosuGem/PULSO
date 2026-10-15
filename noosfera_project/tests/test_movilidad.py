"""Tests de movilidad (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.movilidad import (
    balanza_movilidad,
    indicador_expulsion,
    lenguaje_emergencia,
)


# ── Indicador de expulsión ────────────────────────────────────────────────
def test_expulsion_detecta_presion_salida():
    docs = [
        "me quiero ir de este pais, estoy harto, quiero sacar la visa",
        "busco futuro fuera, me piro en cuanto pueda",
    ]
    e = indicador_expulsion(docs)
    assert e["expulsion"] > 0.5
    assert e["presion_salida"] is True


def test_expulsion_sin_senal():
    docs = ["hoy hace buen dia", "me gusta mi barrio"]
    e = indicador_expulsion(docs)
    assert e["presion_salida"] is False


# ── Lenguaje de emergencia ────────────────────────────────────────────────
def test_emergencia_detecta_crisis():
    docs = [
        "los inmigrantes son una invasion, una avalancha",
        "es un desembarco, oleada imparable de inmigrantes",
    ]
    e = lenguaje_emergencia(docs)
    assert e["emergencia"] > 0.5
    assert e["crisis_inminente"] is True


def test_emergencia_sin_lexico_belico():
    """'Llegan personas' sin léxico bélico NO es emergencia."""
    docs = ["llegan muchas personas a vivir al barrio", "los inmigrantes buscan trabajo"]
    e = lenguaje_emergencia(docs)
    assert e["crisis_inminente"] is False


# ── Balanza ───────────────────────────────────────────────────────────────
def test_balanza_predominio_salida():
    docs = ["me quiero ir", "me piro de aqui"]
    b = balanza_movilidad(docs)
    assert b["predominio"] == "salida"


def test_balanza_predominio_llegada():
    docs = ["los inmigrantes llegan al barrio", "muchos inmigrantes buscan trabajo"]
    b = balanza_movilidad(docs)
    assert b["predominio"] == "llegada"


def test_vacio():
    assert "sin docs" in indicador_expulsion([])["nota"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
