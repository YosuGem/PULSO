"""Tests de presentación accionable (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.presentacion import delta, frase_llana, resumen_accionable, semaforo


# ── Semáforo textual ──────────────────────────────────────────────────────
def test_semaforo_critico():
    s = semaforo(0.85)
    assert s["nivel"] == "critico"
    assert "🔴" in s["etiqueta"] and "CRÍTICO" in s["etiqueta"]


def test_semaforo_vigilar():
    s = semaforo(0.55)
    assert s["nivel"] == "vigilar"
    assert "🟡" in s["etiqueta"] and "VIGILAR" in s["etiqueta"]


def test_semaforo_ruido():
    s = semaforo(0.2)
    assert s["nivel"] == "ruido"
    assert "🟢" in s["etiqueta"]


def test_semaforo_nunca_solo_color():
    """Accesibilidad: cada nivel lleva palabra E icono, no solo color."""
    for score in (0.9, 0.5, 0.1):
        s = semaforo(score)
        assert s["palabra"] in s["etiqueta"]  # hay texto
        assert s["icono"] in s["etiqueta"]  # hay símbolo redundante


# ── Delta vs ayer ─────────────────────────────────────────────────────────
def test_delta_sube():
    assert "▲" in delta(14, 5) and "+9" in delta(14, 5)


def test_delta_baja():
    assert "▼" in delta(3, 10) and "-7" in delta(3, 10)


def test_delta_igual():
    assert delta(7, 7) == "= igual"


def test_delta_sin_referencia():
    assert "sin referencia" in delta(5, None)


# ── Resumen accionable ────────────────────────────────────────────────────
def test_resumen_secciones():
    demo = [
        {"categoria": "politica", "confianza": 0.82, "documentos": 132},
        {"categoria": "vivienda", "confianza": 0.31, "documentos": 12},
    ]
    txt = resumen_accionable(demo)
    assert "ACTÚA HOY" in txt
    assert "VIGILA ESTA SEMANA" in txt
    assert "politica" in txt


def test_resumen_vacio():
    assert "sin señales" in resumen_accionable([])


def test_frase_llana_con_documentos():
    f = frase_llana("politica", 0.8, documentos=132)
    assert "Podría pasar" in f and "132" in f


def test_resumen_usa_num_senales():
    """El campo real del pipeline es num_senales; el resumen debe leerlo."""
    txt = resumen_accionable([{"categoria": "politica", "confianza": 0.8, "num_senales": 42}])
    assert "42 señales" in txt
    assert "0 conversaciones" not in txt


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
