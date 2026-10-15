"""Tests unitarios de detección de idioma (Bloque A - A11)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from noosfera_project.procesamiento.idioma import detectar_idioma, limpiar_por_idioma, idiomas_soportados

CASOS = [
    ("Bitcoin precio 2026", "es"),
    ("Bitcoin price 2026", "en"),
    ("Bitcoin prix 2026", "fr"),
    ("Der Bitcoin Preis 2026", "de"),
    ("O preco do Bitcoin 2026", "pt"),
    ("Guerra en Ucrania", "es"),
    ("Guerre en Ukraine", "fr"),
    ("Krieg in der Ukraine", "de"),
    ("Guerra na Ucrania", "pt"),
    ("Elecciones en Estados Unidos", "es"),
    ("US elections 2026", "en"),
    ("Elections americaines 2026", "fr"),
    ("US-Wahlen 2026", "de"),
    ("Eleicoes americanas 2026", "pt"),
    ("Inflacion en Europa", "es"),
    ("Inflation in Europe", "en"),
    ("Inflation en Europe", "fr"),
    ("Inflation in Europa", "en"),
    ("Inflacao na Europa", "pt"),
    ("Mercado de valores", "es"),
    ("Stock market", "en"),
    ("Marche boursier", "fr"),
    ("Aktienmarkt", "de"),
    ("Mercado de acoes", "pt"),
    ("Seleccion española mundial", "es"),
    ("Spanish national team", "en"),
    ("Equipe de France mondial", "fr"),
    ("Deutsche Nationalmannschaft Weltmeisterschaft", "de"),
    ("Selecao brasileira copa", "pt"),
    ("Criptomonedas al alza", "es"),
    ("Cryptocurrencies rising", "en"),
    ("Cryptomonnaies en hausse", "fr"),
    ("Kryptowahrungen steigen", "de"),
    ("Criptomoedas em alta", "pt"),
    ("La economia crece", "es"),
    ("The economy grows", "en"),
    ("L'economie prospère", "fr"),
    ("Die Wirtschaft wachst", "de"),
    ("A economia cresce", "pt"),
    ("Noticias del dia", "es"),
    ("News of the day", "en"),
]


def test_detectar():
    fallos = 0
    for texto, esp in CASOS:
        det = detectar_idioma(texto)
        if det != esp:
            print(f"FAIL: '{texto}' -> {det} (esp {esp})")
            fallos += 1
    print(f"detectar_idioma: {len(CASOS)-fallos}/{len(CASOS)} pass")
    return fallos == 0


def test_limpiar():
    # Limpieza debe respetar stopwords del idioma
    es = limpiar_por_idioma("El bitcoin sube el precio", "es")
    assert "el" not in es.split(), f"stopword ES no eliminada: {es}"
    en = limpiar_por_idioma("The bitcoin price rises", "en")
    assert "the" not in en.split(), f"stopword EN no eliminada: {en}"
    print("limpiar_por_idioma: OK")
    return True


def test_idiomas_soportados():
    sup = idiomas_soportados()
    assert set(sup) == {"es", "en", "fr", "de", "pt"}, f"idiomas incorrectos: {sup}"
    print("idiomas_soportados: OK")
    return True


if __name__ == "__main__":
    ok = True
    ok &= test_detectar()
    ok &= test_limpiar()
    ok &= test_idiomas_soportados()
    sys.exit(0 if ok else 1)
