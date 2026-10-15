"""Tests de descubrimiento autónomo (Bloque E - E5)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from noosfera_project.descubrimiento.explorador import explorar, descubrir_desde_pipeline

SAMPLE = [
    {"id": 1, "fuente": "reddit", "idioma": "es", "texto": "La ia va a cambiar todo el mundo laboral"},
    {"id": 2, "fuente": "hackernews", "idioma": "es", "texto": "El clima está colapsando por la sequía extrema en el sur"},
    {"id": 3, "fuente": "reddit", "idioma": "es", "texto": "Bitcoin será 120.000 sin duda lo tengo clarísimo"},
    {"id": 4, "fuente": "telegram", "idioma": "es", "texto": "Hay protesta masiva contra el gobierno por la inflación"},
    {"id": 5, "fuente": "reddit", "idioma": "es", "texto": "Texto sin sentido claro sobre cosas varias"},
]


def test_explorar():
    out = explorar(SAMPLE)
    assert out["total_textos"] == 5
    assert "ia" in [s["tema_sugerido"] for s in out["sugerencias_categoria"]]
    assert "clima" in [s["tema_sugerido"] for s in out["sugerencias_categoria"]]
    print(f"explorar: {out['no_clasificados']} no clasificados, sugerencias={out['sugerencias_categoria']}")
    return True


def test_descubrir_pipeline():
    out = descubrir_desde_pipeline(SAMPLE)
    assert "hipotesis_generadas" in out
    print(f"descubrir_pipeline: {out['hipotesis_generadas']} hipótesis")
    return True


if __name__ == "__main__":
    ok = True
    ok &= test_explorar()
    ok &= test_descubrir_pipeline()
    sys.exit(0 if ok else 1)
