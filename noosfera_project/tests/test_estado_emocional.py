"""Tests de estado emocional colectivo (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.estado_emocional import (
    culpabilizacion,
    resignacion_esperanza,
    termometro_amenaza,
)


# ── Termómetro de amenaza ─────────────────────────────────────────────────
def test_amenaza_detecta_miedo():
    docs = [
        "hay un peligro inminente, puede que ocurra una catastrofe, no se si estamos seguros",
        "el miedo al colapso crece, la crisis nos amenaza, nadie sabe que va a pasar",
    ]
    t = termometro_amenaza(docs)
    assert t["amenaza"] > 0
    assert t["miedo"] > 0
    assert t["miedo_instalado"] is True


def test_amenaza_con_control_baja_miedo():
    docs = [
        "podemos controlar la situacion, tenemos un plan para prevenir el riesgo",
        "la solucion existe, podemos gestionar y evitar el peligro",
    ]
    t = termometro_amenaza(docs)
    assert t["control"] > 0
    assert t["miedo_instalado"] is False


# ── Culpabilización ───────────────────────────────────────────────────────
def test_culpabilizacion_gatillo_ira():
    docs = [
        "hay un peligro grave, por culpa del gobierno y los politicos",
        "la crisis es una amenaza, ellos son los responsables de esto",
        "el miedo al colapso, culpa de los bancos y los de arriba",
    ]
    c = culpabilizacion(docs)
    assert c["ratio"] >= 0.5
    assert c["gatillo_ira"] is True


def test_culpabilizacion_sin_culpa_no_dispara():
    docs = ["hay un peligro pero no se de quien es la culpa"]
    c = culpabilizacion(docs)
    assert c["gatillo_ira"] is False


# ── Resignación ↔ esperanza ───────────────────────────────────────────────
def test_esperanza_abre_movilizacion():
    docs = [
        "juntos podemos lograrlo, si se puede, tengo esperanza",
        "unidos vamos a conseguirlo, es posible, hay que construir el cambio",
    ]
    r = resignacion_esperanza(docs)
    assert r["indice"] > 0
    assert r["ventana_movilizacion"] is True


def test_resignacion_cierra_movilizacion():
    docs = [
        "da igual, para que votar, nunca cambia nada",
        "es inutil, siempre igual, ya nada importa",
    ]
    r = resignacion_esperanza(docs)
    assert r["resignacion"] > 0
    assert r["ventana_movilizacion"] is False


def test_vacio():
    assert "sin docs" in termometro_amenaza([])["nota"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
