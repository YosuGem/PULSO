"""Tests de polarización y propagación (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.polarizacion import (
    entropia_fuentes,
    polarizacion,
    propagacion_fuentes,
    veredicto,
)


# ── Polarización ──────────────────────────────────────────────────────────
def test_polarizacion_balanceada():
    docs = [
        "esto es un gran avance, muy necesario",
        "que no, es un desastre absoluto",
        "apoyo totalmente, es la solucion",
        "falso, es una estafa peligrosa",
    ]
    p = polarizacion(docs)
    assert p["polarizado"] is True
    assert p["indice"] >= 0.5


def test_polarizacion_unanimidad():
    docs = [
        "esto es bueno, gran avance",
        "excelente solucion, apoyo",
        "muy bueno, necesario",
    ]
    p = polarizacion(docs)
    assert p["polarizado"] is False  # una sola voz


def test_polarizacion_vacia():
    p = polarizacion([])
    assert p["polarizado"] is False
    assert "sin docs" in p["nota"]


# ── Propagación entre fuentes ─────────────────────────────────────────────
def test_propagacion_salta_a_mas_fuentes():
    por_dia = [
        [{"fuente": "foroA"}],
        [{"fuente": "foroA"}, {"fuente": "reddit"}],
    ]
    p = propagacion_fuentes(por_dia)
    assert p["fuentes_hoy"] == 2
    assert p["salto"] == 1
    assert p["crece"] is True


def test_propagacion_confinado_no_crece():
    por_dia = [
        [{"fuente": "foroA"}, {"fuente": "foroA"}],
        [{"fuente": "foroA"}, {"fuente": "foroA"}],
    ]
    p = propagacion_fuentes(por_dia)
    assert p["fuentes_hoy"] == 1
    assert p["crece"] is False


def test_propagacion_un_dia_insuficiente():
    p = propagacion_fuentes([[{"fuente": "foroA"}]])
    assert "necesita 2+ días" in p["nota"]


# ── Entropía de fuentes ───────────────────────────────────────────────────
def test_entropia_burbuja_baja():
    docs = [{"fuente": "A"}] * 5 + [{"fuente": "A"}]
    assert entropia_fuentes(docs) == 0.0  # una sola fuente


def test_entropia_repartida_alta():
    docs = [{"fuente": f} for f in "ABCD"]
    e = entropia_fuentes(docs)
    assert e >= 1.5  # repartida entre 4 fuentes


# ── Veredicto compuesto ───────────────────────────────────────────────────
def test_veredicto_crece():
    docs = [
        "gran avance necesario", "desastre absoluto",
        "apoyo la solucion", "estafa peligrosa",
    ]
    por_dia = [
        [{"fuente": "A"}], [{"fuente": "A"}, {"fuente": "B"}],
        [{"fuente": "A"}, {"fuente": "B"}, {"fuente": "C"}],
    ]
    v = veredicto(docs, por_dia)
    assert v["veredicto"] == "crece"


def test_veredicto_muere():
    docs = ["bueno", "malo"]
    por_dia = [
        [{"fuente": "A"}, {"fuente": "B"}, {"fuente": "C"}],
        [{"fuente": "A"}],
    ]
    v = veredicto(docs, por_dia)
    assert v["veredicto"] in ("muere", "latente")


def test_veredicto_vacio():
    v = veredicto([], [[{"fuente": "A"}], [{"fuente": "A"}]])
    assert v["veredicto"] in ("muere", "latente")


# ── Robustez: documentos nulos / sucios (fallos de auditoría) ─────────────
def test_polarizacion_tolera_documento_nulo():
    """Un documento None de la ingesta no debe tumbar el análisis."""
    p = polarizacion(["gran avance", None, "desastre total"])
    assert p["n_docs"] == 3
    assert p["polarizado"] is True


def test_propagacion_tolera_documento_nulo():
    p = propagacion_fuentes([[{"fuente": "A"}, None], [{"fuente": "A"}, {"fuente": "B"}]])
    assert p["fuentes_hoy"] == 2
    assert p["crece"] is True


def test_entropia_tolera_documento_sucio():
    docs = [{"fuente": "A"}, None, {}, {"fuente": "B"}]
    e = entropia_fuentes(docs)
    assert e > 0  # cuenta solo los docs válidos


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
