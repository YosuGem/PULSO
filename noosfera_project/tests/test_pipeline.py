"""Tests de integración del pipeline de detección (Bloque C - C10)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from noosfera_project.deteccion.pipeline import ejecutar_pipeline
from noosfera_project.deteccion.senal import extraer_senales
from noosfera_project.deteccion.agrupacion import agrupar
from noosfera_project.deteccion.hipotesis import generar_hipotesis
from noosfera_project.deteccion.confianza import calcular_confianza

SAMPLE = [
    {"id": 1, "fuente": "reddit", "idioma": "es", "texto": "Bitcoin será 120.000 sin duda lo tengo clarísimo"},
    {"id": 2, "fuente": "hackernews", "idioma": "es", "texto": "Colapso total desastre imposible en bolsa"},
    {"id": 3, "fuente": "reddit", "idioma": "es", "texto": "Muy probable que caiga la bolsa crisis inminente"},
    {"id": 4, "fuente": "telegram", "idioma": "es", "texto": "La selección española ganará el mundial absolutamente seguro"},
    {"id": 5, "fuente": "reddit", "idioma": "en", "texto": "Bitcoin price prediction 2026 experts say 120k"},
]


def test_senal():
    s = extraer_senales(SAMPLE)
    assert len(s) == 5
    assert s[0]["categoria"] == "bitcoin"
    assert s[0]["score_emocional"] >= 8.0
    print("extraer_senales: OK")
    return True


def test_agrupar():
    s = extraer_senales(SAMPLE)
    g = agrupar(s, umbral_coincidencias=1)
    cats = {grp["categoria"] for grp in g}
    assert "bitcoin" in cats
    print(f"agrupar: {len(g)} grupos, cats={cats}")
    return True


def test_hipotesis():
    s = extraer_senales(SAMPLE)
    g = agrupar(s, umbral_coincidencias=1)
    h = generar_hipotesis(g)
    assert len(h) == len(g)
    assert all("texto" in x for x in h)
    print(f"generar_hipotesis: {len(h)} hipótesis")
    return True


def test_confianza():
    h = {"categoria": "bitcoin", "num_senales": 10, "score_medio": 9.0, "fuentes": ["a", "b", "c"]}
    c = calcular_confianza(h)
    assert c["confianza"] > 0.5
    h2 = {"categoria": "undetected", "num_senales": 100, "score_medio": 0.1, "fuentes": ["x"]}
    c2 = calcular_confianza(h2)
    assert c2["confianza"] < calcular_confianza({"categoria": "bitcoin", "num_senales": 100, "score_medio": 0.1, "fuentes": ["x"]})["confianza"]
    print("calcular_confianza: OK")
    return True


def test_pipeline():
    out = ejecutar_pipeline(SAMPLE, umbral_grupo=1)
    assert out["total_textos"] == 5
    assert out["total_senales"] == 5
    assert out["total_hipotesis"] >= 1
    assert "hipotesis" in out
    print(f"pipeline: {out['total_hipotesis']} hipótesis generadas")
    return True


if __name__ == "__main__":
    ok = True
    ok &= test_senal()
    ok &= test_agrupar()
    ok &= test_hipotesis()
    ok &= test_confianza()
    ok &= test_pipeline()
    sys.exit(0 if ok else 1)
