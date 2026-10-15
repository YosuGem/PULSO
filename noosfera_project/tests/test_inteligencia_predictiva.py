"""Tests de inteligencia predictiva (0.2.2-dev)."""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.inteligencia_predictiva import (
    brecha_agencia,
    coaliciones,
    coocurrencia_temas,
    escalada_tono,
    gramatica_accion,
    repertorio_accion,
    rumorometro,
    salto_colectivo,
)


# ── Escalada de tono ──────────────────────────────────────────────────────
def test_escalada_detecta_movilizacion():
    docs = [
        "basta ya, hay que movilizarse y convocar la manifestacion",
        "organizemos la protesta, hay que actuar",
        "hay que exigir nuestros derechos ya basta",
    ]
    e = escalada_tono(docs)
    assert e["etapas"]["movilizacion"] > 0.5
    assert e["dominante"] == "movilizacion"
    assert e["escalando"] is True


def test_escalada_detecta_queja_individual():
    docs = [
        "yo estoy harto, tengo un problema",
        "a mi me pasa lo mismo, estoy indignado",
        "yo siento que es injusto para mi",
    ]
    e = escalada_tono(docs)
    assert e["etapas"]["queja"] > 0.3


def test_escalada_vacia():
    e = escalada_tono([])
    assert e["dominante"] == "sin_senal"
    assert "sin docs" in e["nota"]


def test_escalada_tolera_none():
    e = escalada_tono(["hay que organizarnos", None])
    assert e["n_docs"] == 2  # no crashea


# ── Salto colectivo (yo → nosotros) ───────────────────────────────────────
def test_salto_colectivo_plural_domina():
    docs = [
        "nosotros los vecinos no aguantamos mas",
        "compartimos el agravio, es colectivo",
        "nuestra comunidad sufra esto",
    ]
    s = salto_colectivo(docs)
    assert s["colectivizando"] is True
    assert s["ratio_nosotros_yo"] > 1.0


def test_salto_individual_domina():
    docs = ["yo tengo un problema", "a mi me pasa", "yo estoy harto"]
    s = salto_colectivo(docs)
    assert s["colectivizando"] is False


# ── Co-ocurrencia entre temas ─────────────────────────────────────────────
def test_coocurrencia_detecta_arista():
    docs = [
        {"categorias": ["vivienda", "jubilacion"]},
        {"categorias": ["vivienda", "jubilacion"]},
        {"categorias": ["vivienda", "jubilacion"]},
        {"categorias": ["energia"]},
        {"categorias": ["vivienda"]},
    ]
    aristas = coocurrencia_temas(docs)
    pares = [tuple(a["par"]) for a in aristas]
    assert ("jubilacion", "vivienda") in pares or ("vivienda", "jubilacion") in pares


def test_coocurrencia_vacia():
    assert coocurrencia_temas([]) == []


def test_coocurrencia_tolera_docs_sucios():
    docs = [None, {"categorias": ["a", "b"]}, {}, {"categorias": ["a", "b"]}]
    aristas = coocurrencia_temas(docs)
    assert isinstance(aristas, list)  # sin crash


# ── Ronda 2: rumorómetro, gramática de la acción, coaliciones ─────────────
def test_rumorometro_detecta_relato_sin_fuente():
    docs = [
        "segun he oido parece que va a pasar algo, dicen que",
        "un amigo me ha dicho que comentan que habra problemas",
        "al parecer se comenta que el gobierno prepara algo",
    ]
    r = rumorometro(docs)
    assert r["ambiguedad"] > 0.8  # sin datos concretos
    assert r["segunda_mano"] > 0.8  # todo en segunda mano
    assert r["construyendo_relato"] is True


def test_rumorometro_datos_concretos_bajan_ambiguedad():
    docs = [
        "el informe de 2024 en https://ejemplo.gob confirma 3 casos",
        "segun el boletin 123 publicado el 5 de marzo hay 45 afectados",
    ]
    r = rumorometro(docs)
    assert r["ambiguedad"] == 0.0  # todos tienen datos


def test_rumorometro_vacio():
    r = rumorometro([])
    assert "sin docs" in r["nota"]


def test_gramatica_detecta_organizacion():
    docs = [
        "quedamos en el punto de encuentro, llevad pancartas",
        "alguien sabe donde es la asamblea? avisad a todos",
        "hay que organizarse, compartid la convocatoria",
    ]
    g = gramatica_accion(docs)
    assert g["logistico"] > 0.8
    assert g["organizandose"] is True


def test_gramatica_queja_no_es_organizacion():
    docs = ["yo estoy harto de esta injusticia", "queja constante, problema tras problema"]
    g = gramatica_accion(docs)
    assert g["organizandose"] is False


def test_coaliciones_detecta_fusion():
    docs = [
        {"categorias": ["vivienda", "corrupcion"]},
        {"categorias": ["vivienda", "corrupcion"]},
        {"categorias": ["vivienda", "corrupcion"]},
        {"categorias": ["ecologia"]},
    ]
    coal = coaliciones(docs)
    pares = [tuple(c["par"]) for c in coal]
    assert ("corrupcion", "vivienda") in pares or ("vivienda", "corrupcion") in pares


def test_coaliciones_vacia():
    assert coaliciones([]) == []


# ── Sociólogo: brecha de agencia + repertorio de acción ───────────────────
def test_brecha_agencia_pre_encendido():
    """Indignación alta + adversario claro + poca agencia = frustración sin
    salida (Gamson). El tema está pre-encendido."""
    docs = [
        "es una injusticia inaceptable, la culpa es del gobierno y los politicos",
        "que verguenza, los bancos nos hunden, es un escandalo",
        "indignante, el sistema nos roba pero no podemos hacer nada",
    ]
    b = brecha_agencia(docs)
    assert b["indignacion"] > 0.8
    assert b["adversario"] > 0.8
    assert b["brecha"] > 0.3
    assert b["pre_encendido"] is True


def test_brecha_agencia_con_salida():
    """Cuando hay agencia ("podemos cambiarlo"), la brecha baja: el tema
    tiene salida, no está frustrado."""
    docs = [
        "es una injusticia pero podemos cambiarlo si nos organizamos",
        "somos capaces, juntos podemos parar esta verguenza del gobierno",
    ]
    b = brecha_agencia(docs)
    assert b["agencia"] > 0.5
    assert b["pre_encendido"] is False


def test_repertorio_detecta_escalada():
    docs = [
        "hay que ocupar la plaza y bloquear el acceso",
        "convoquemos una huelga y boicot a sus productos",
        "vamos a acampar y rodear el edificio",
    ]
    r = repertorio_accion(docs)
    assert r["confrontacional"] > 0.8
    assert r["dominante"] == "confrontacional"
    assert r["escalada"] is True


def test_repertorio_simbolico_no_es_escalada():
    docs = [
        "vamos a firmar la peticion y compartir el hashtag",
        "difundid el tuit y poner un lazo, concentracion pacifica",
    ]
    r = repertorio_accion(docs)
    assert r["dominante"] == "simbolico"
    assert r["escalada"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# ── Matching por palabra, no subcadena (fallo de auditoría) ───────────────
def test_lexicos_no_matchean_subcadenas():
    """'cortar' no debe disparar en 'recortar', 'sistema' en 'ecosistema',
    'segun' en 'segunnormativa'. Fallo de auditoría: matching por subcadena
    falseaba los veredictos de repertorio, brecha de agencia y rumorómetro."""
    assert repertorio_accion(["hay que recortar gastos"])["confrontacional"] == 0.0
    assert brecha_agencia(["el sistematico analisis del ecosistema"])["adversario"] == 0.0
    assert rumorometro(["elindicebajosegunnormativa"])["segunda_mano"] == 0.0


def test_lexicos_detectan_palabras_reales():
    """Las palabras reales SÍ se detectan tras el fix."""
    assert repertorio_accion(["hay que cortar el trafico"])["confrontacional"] > 0
    assert brecha_agencia(["el sistema nos hunde"])["adversario"] > 0
