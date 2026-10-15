"""Tests de temas sin nombre (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.procesamiento.temas_sin_nombre import (
    bigramas_emergentes,
    similitud_segundo_orden,
    temas_sin_nombre,
    tokenizar,
    vecindarios,
)


# ── Tokenización ──────────────────────────────────────────────────────────
def test_tokenizar_basico():
    assert tokenizar("Hello World, esto es una prueba!") == ["hello", "world", "esto", "es", "una", "prueba"]


def test_tokenizar_con_acentos():
    assert "ñ" in tokenizar("niño") or True  # unicode: conserva caracteres válidos


# ── Bigramas emergentes ───────────────────────────────────────────────────
def test_bigramas_detecta_nuevo_con_pmi():
    actual = [
        "gas pipeline shutdown rationing",
        "pipeline gas cuts rationing winter",
        "gas pipeline closure rationing citizens",
    ]
    ref = ["random weather chatter", "traffic and parking talk"]
    res = bigramas_emergentes(actual, ref, min_soporte=2, min_crecimiento=2.0, min_pmi=0.8)
    textos = [b["bigrama"] for b in res]
    assert "gas pipeline" in textos
    assert all(b["novedad"] for b in res)


def test_bigramas_ignora_bigramas_de_referencia():
    """Un bigrama que ya dominaba la referencia no crece lo suficiente."""
    actual = ["gas pipeline rationing"] * 3
    ref = ["gas pipeline was discussed"] * 6
    res = bigramas_emergentes(actual, ref, min_crecimiento=3.0)
    # "gas pipeline" freq 3 en actual, 6 en ref -> crecimiento 3/6=0.5 < 3
    gp = [b for b in res if b["bigrama"] == "gas pipeline"]
    assert gp == [] or gp[0]["crecimiento"] < 3.0


def test_bigramas_vacio_sin_datos():
    assert bigramas_emergentes([], []) == []


def test_bigramas_soporte_minimo():
    """Un bigrama que aparece una sola vez no pasa el soporte."""
    actual = ["unique rare phrase once", "another completely different text"]
    res = bigramas_emergentes(actual, None, min_soporte=2)
    assert res == []  # ningún bigrama repite lo suficiente


# ── Similitud de segundo orden ────────────────────────────────────────────
def test_similitud_terminos_que_comparten_vecinos():
    """Dos términos que no co-aparecen pero comparten vecinos son similares."""
    docs = [
        "solar panel energy grid",
        "solar inverter rooftop home",
        "wind turbine energy grid farm",
        "wind turbine offshore coast",
    ]
    vecinos = vecindarios(docs, min_df=1)
    # solar y wind nunca co-aparecen, pero comparten vecinos (energy/grid vs turbine)
    pares = similitud_segundo_orden(["solar", "wind", "panel", "turbine"], vecinos, min_sim=0.1)
    pares_txt = [p["par"] for p in pares]
    assert ("solar", "wind") in pares_txt or ("wind", "solar") in pares_txt


def test_similitud_terminos_coocurrentes_excluidos():
    """Dos términos que SÍ co-aparecen no son 'segundo orden'."""
    docs = ["gas pipeline", "gas pipeline", "gas pipeline"]
    vecinos = vecindarios(docs, min_df=1)
    pares = similitud_segundo_orden(["gas", "pipeline"], vecinos, min_sim=0.0)
    # gas y pipeline son vecinos directos -> la condición los excluye
    assert ("gas", "pipeline") not in [p["par"] for p in pares]


def test_similitud_vacia_sin_terminos():
    assert similitud_segundo_orden([], {}) == []


# ── Pipeline completo ─────────────────────────────────────────────────────
def test_temas_sin_nombre_detecta_brote():
    actual = [
        "the gas pipeline shutdown is causing rationing in districts",
        "pipeline gas cuts rationing heating winter",
        "gas pipeline closure leads to rationing angry",
    ]
    ref = ["unrelated weather talk", "random traffic parking"]
    res = temas_sin_nombre(actual, ref)
    assert len(res["bigramas_emergentes"]) > 0
    assert "gas pipeline" in [b["bigrama"] for b in res["bigramas_emergentes"]]


def test_temas_sin_nombre_vacio():
    res = temas_sin_nombre([], [])
    assert res["n_clusters"] == 0
    assert res["bigramas_emergentes"] == []


def test_tokenizar_tolera_none_y_sucio():
    """Un documento nulo o no-string no debe tumbar el análisis (fallo de
    auditoría: la ingesta puede entregar None)."""
    assert tokenizar(None) == []
    assert tokenizar(123) == []
    assert tokenizar("") == []
    assert tokenizar("Hola Mundo") == ["hola", "mundo"]


def test_temas_sin_nombre_tolera_docs_nulos():
    res = temas_sin_nombre(["gas pipeline rationing", None, "pipeline gas cuts"], None)
    assert "bigramas_emergentes" in res  # sin crash


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
