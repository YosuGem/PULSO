"""Tests de pesos emocionales (Bloque B - B9)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from noosfera_project.procesamiento.pesos_emocionales import analizar_emocion, etiquetar
from noosfera_project.procesamiento.scoring_emocional import score_combinado, rankear

CASOS = [
    ("El bitcoin será 120.000 sin duda", "positivo_alto", 9.0),
    ("Colapso total, desastre, imposible", "riesgo_alto", 9.0),
    ("Creo que podría subir algo", "debil", 0.0),
    ("Muy probable que caiga la bolsa crisis", "riesgo_alto", 9.0),
    ("Absolutamente seguro ganará sí o sí", "positivo_alto", 9.0),
    ("Probablemente haya inflación", "moderado", None),
    ("Tal vez suba poco", "debil", 0.0),
    ("Definitivamente va a pasar", "positivo_alto", None),
]


def test_analizar():
    fallos = 0
    for texto, esp_tipo, esp_min in CASOS:
        r = analizar_emocion(texto)
        ok_tipo = (
            (esp_tipo == "positivo_alto" and r["signo"] == "positivo" and r["score_emocional"] >= 8.0) or
            (esp_tipo == "riesgo_alto" and r["signo"] == "negativo" and r["score_emocional"] >= 8.0) or
            (esp_tipo == "debil" and r["score_emocional"] < 3.5) or
            (esp_tipo == "moderado" and 3.5 <= r["score_emocional"] < 6.0)
        )
        if not ok_tipo:
            print(f"FAIL: '{texto}' -> score={r['score_emocional']} signo={r['signo']} (esp {esp_tipo})")
            fallos += 1
    print(f"analizar_emocion: {len(CASOS)-fallos}/{len(CASOS)} pass")
    return fallos == 0


def test_etiquetar():
    assert etiquetar(9.0) == "muy_fuerte"
    assert etiquetar(7.0) == "fuerte"
    assert etiquetar(4.0) == "moderado"
    assert etiquetar(1.0) == "debil"
    print("etiquetar: OK")
    return True


def test_scoring_combinado():
    res = [{"coincidencias": 3, "score_emocional": 9.0}, {"coincidencias": 1, "score_emocional": 2.0}]
    out = rankear(res)
    assert out[0]["ranking"] == 1
    assert out[0]["score_combinado"] >= out[1]["score_combinado"]
    print("scoring_combinado/rankear: OK")
    return True


if __name__ == "__main__":
    ok = True
    ok &= test_analizar()
    ok &= test_etiquetar()
    ok &= test_scoring_combinado()
    sys.exit(0 if ok else 1)
