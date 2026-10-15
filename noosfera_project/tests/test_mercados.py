"""Tests de mercados (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.mercados import (
    capitulacion,
    deriva_subsistencia,
    sobreextension_certeza,
)


# ── Capitulación ──────────────────────────────────────────────────────────
def test_capitulacion_detecta_salida():
    docs = [
        "voy a salir como sea, ya no aguanto, recortar perdidas",
        "me salgo, vendiendo todo, sacarme de esta",
    ]
    c = capitulacion(docs)
    assert c["salida"] > c["entrada"]
    assert c["flujo"] == "capitulacion"


def test_capitulacion_detecta_entrada():
    docs = ["voy a comprar ahora, todo dentro, subirme", "entrando, alcista, comprando"]
    c = capitulacion(docs)
    assert c["flujo"] == "entrada"


# ── Sobreextensión de certeza ─────────────────────────────────────────────
def test_certeza_euforia_narrativa():
    docs = [
        "seguro que va a subir, sin duda, garantizado",
        "obvio que va a explotar, si o si, es un hecho",
    ]
    c = sobreextension_certeza(docs)
    assert c["certeza"] > 0
    assert c["verificacion"] == 0
    assert c["euforia_narrativa"] is True


def test_certeza_ratio_no_astronomico():
    """Sin verificación, el ratio NO debe ser un número absurdo (fallo de
    división por cero, patrón corregido de zscore)."""
    c = sobreextension_certeza(["seguro que va a subir"])
    assert c["ratio"] == 0.0  # no 4e9
    assert c["euforia_narrativa"] is True


def test_certeza_con_verificacion():
    docs = ["los datos dicen que subio un 5 por ciento, segun el informe"]
    c = sobreextension_certeza(docs)
    assert c["verificacion"] > 0
    assert c["euforia_narrativa"] is False


# ── Deriva de subsistencia ────────────────────────────────────────────────
def test_subsistencia_estres_extendido():
    docs = [
        "no me llega a fin de mes, he recortado gastos",
        "he dejado de comprar, no puedo pagar el alquiler",
    ]
    d = deriva_subsistencia(docs)
    assert d["subsistencia"] > 0.5
    assert d["estres_extendido"] is True


def test_subsistencia_sin_estres():
    docs = ["hoy hace buen dia", "me gusta mi trabajo"]
    d = deriva_subsistencia(docs)
    assert d["estres_extendido"] is False


def test_vacio():
    assert "sin docs" in capitulacion([])["nota"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
