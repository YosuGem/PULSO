"""Tests del termómetro regulatorio (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.regulatorio import (
    analogia_regulatoria,
    deficit_vigilancia,
    juridificacion,
)


# ── Juridificación léxica ─────────────────────────────────────────────────
def test_juridificacion_listo_para_norma():
    docs = [
        "esto es ilegal, vulnera nuestros derechos, hay que denunciarlo",
        "es una violacion de la ley, protejamos nuestros derechos",
    ]
    j = juridificacion(docs)
    assert j["juridificacion"] > 0.5
    assert j["listo_para_norma"] is True


def test_juridificacion_coloquial_no_dispara():
    docs = ["esto esta muy mal, no me gusta nada", "que desastre de situacion"]
    j = juridificacion(docs)
    assert j["listo_para_norma"] is False


# ── Analogía regulatoria ──────────────────────────────────────────────────
def test_analogia_borrador_en_calle():
    docs = [
        "deberian regularlo como con el tabaco",
        "hay que hacer lo mismo que con los cinturones",
    ]
    a = analogia_regulatoria(docs)
    assert a["analogia"] > 0
    assert a["borrador_en_calle"] is True


def test_analogia_sin_marco():
    docs = ["esto esta muy mal", "no se que hacer"]
    a = analogia_regulatoria(docs)
    assert a["borrador_en_calle"] is False


# ── Déficit de vigilancia ─────────────────────────────────────────────────
def test_vigilancia_costo_politico_alto():
    docs = [
        "nadie controla nada, no hay quien verifique, todo impune",
        "denuncias y nada, no pasa nada, sin consecuencia",
    ]
    v = deficit_vigilancia(docs)
    assert v["vigilancia"] > 0.5
    assert v["costo_politico_alto"] is True


def test_vigilancia_no_dispara():
    docs = ["hay inspecciones frecuentes y sanciones efectivas"]
    v = deficit_vigilancia(docs)
    assert v["costo_politico_alto"] is False


def test_vacio():
    assert "sin docs" in juridificacion([])["nota"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
