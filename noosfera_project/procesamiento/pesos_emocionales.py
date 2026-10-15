"""Sistema de pesos emocionales (Bloque B - según SISTEMA_PESOS_EMOCIONALES.md).

Cuantifica la fuerza de cada texto del lenguaje colectivo por intensidad emocional.
Score normalizado 0-10 para ranking de escenarios probables.
"""
from __future__ import annotations

import re
from typing import Any

# Léxico emocional base (español). Cada entrada: (patron, peso, tipo)
CERTEZA = {
    "será": 4, "seguro": 3, "claramente": 3, "definitivamente": 4, "sin duda": 4,
    "absolutamente": 4, "estoy seguro": 3, "lo tengo clarísimo": 3, "no me cabe duda": 3,
    "va a pasar": 4, "sí o sí": 4, "va a": 1, "van a": 1, "tiene que": 1,
    "ganará": 3, "ganara": 3,
    # Marcadores de certeza de la plantilla real del lenguaje colectivo
    "se confirma que": 4, "es obvio que": 3, "se avecina": 3, "va a explotar": 4,
    "garantizado": 4, "fijo": 3, "al 100": 3, "al cien": 3, "dicen que": 2,
    "tengo la sensacion de": 1, "tengo la sensación de": 1, "empieza a sonar": 2,
    "empiezo a ver": 2, "ojo con": 1, "nadie lo menciona pero": 2, "creo que": 1,
}

PROBABILIDAD_ALTA = {
    "probablemente": 2, "muy probable": 2, "alta probabilidad": 2,
    "lo más probable": 2, "altas probabilidades": 2, "probable": 2,
}

CARGA_NEGATIVA = {
    "crisis": -3, "baja": -3, "caída": -3, "caida": -3, "caiga": -3, "caer": -3,
    "baje": -3, "bajar": -3, "desastre": -3, "colapso": -3,
    "no creo": -3, "dudo": -3, "imposible": -3, "catástrofe": -3, "catastrofe": -3,
    "hundimiento": -3, "quiebra": -3, "inflación": -3, "inflacion": -3,
    # Marcadores de duda/negación y riesgo de la plantilla real
    "no creo que": -3, "no me cuadra": -2, "no cuela que": -2, "me temo que": -3,
    "me juego que": -2, "nos van a colar": -2, "hay algo raro con": -2,
    "recesion": -3, "recesión": -3, "guerra": -2, "conflicto": -2, "atentado": -3,
    "explosion": -3, "explosión": -3, "emergencia": -3, "alerta": -2, "protesta": -2,
    "apagon": -2, "apagón": -2, "inundacion": -2, "inundación": -2, "accidente": -2,
    "rescate": -2, "corte": -2, "deuda": -2, "default": -3, "burbuja": -2, "crash": -3,
}

INTENSIFICADORES = {
    "muy": 1.5, "mucho": 1.5, "bastante": 1.5, "extremadamente": 1.5,
    "poco": 0.5, "algo": 0.5, "tal vez": 0.5, "quizás": 0.5, "quizas": 0.5,
}

DESEO_VS_HECHO = {
    "creo que": 0.7, "opino que": 0.7, "me gustaría": 0.7, "me gustaria": 0.7,
    "espero que": 0.8, "ojalá": 0.7, "ojala": 0.7,
}

# Marcadores de concreción numérica (refuerzan certeza)
CONCRECION = {
    "120.000": 2, "120000": 2, "100.000": 2, "100000": 2, "150.000": 2, "150000": 2,
}

ETIQUETAS = [
    (8.0, "muy_fuerte"),
    (6.0, "fuerte"),
    (3.5, "moderado"),
    (0.0, "debil"),
]


def _contar(texto_l: str, dicc: dict[str, float]) -> tuple[float, list[str]]:
    total = 0.0
    activos: list[str] = []
    for patron, peso in dicc.items():
        n = texto_l.count(patron)
        if n:
            total += n * peso
            activos.extend([patron] * n)
    return total, activos


def analizar_emocion(texto: str) -> dict[str, Any]:
    """Devuelve score emocional (0-10), etiqueta y parámetros activados."""
    # Filtrar ruido: lineas de documentación/markdown (# titulo) no son señal
    texto_l = (texto or "").lower()
    if texto_l.lstrip().startswith("#"):
        return {
            "score_emocional": 0.0,
            "peso_emocional": "debil",
            "score_bruto": 0.0,
            "parametros_utilizados": [],
            "signo": "neutro",
        }

    score_c, act_c = _contar(texto_l, CERTEZA)
    score_n, act_n = _contar(texto_l, CARGA_NEGATIVA)
    score_conc, act_conc = _contar(texto_l, CONCRECION)
    _, act_p = _contar(texto_l, PROBABILIDAD_ALTA)

    # Intensificadores y probabilidad AMPLIFICAN la magnitud (no suman signo opuesto)
    _, act_i = _contar(texto_l, INTENSIFICADORES)
    mult = 1.0
    for patron in act_p:
        mult *= 1.4  # cada marca de probabilidad amplifica x1.4
    for patron in act_i:
        mult *= INTENSIFICADORES[patron]
    mult = min(mult, 4.0)  # cap para evitar explosión

    _, act_d = _contar(texto_l, DESEO_VS_HECHO)
    mult_deseo = 1.0
    for patron in act_d:
        mult_deseo *= DESEO_VS_HECHO[patron]
    mult_deseo = min(mult_deseo, 1.0)  # solo reduce

    # Carga direccional: certeza/concreción positivas, carga negativa negativa
    base = score_c + score_conc + score_n
    score_bruto = base * mult * mult_deseo

    # Normalizar a 0-10 (asumiendo max ~ +9 bruto => 10)
    score_norm = max(0.0, min(10.0, abs(score_bruto)))
    if score_bruto < 0:
        # Negativo: invertir para que "riesgo alto" puntúe alto
        score_norm = max(0.0, min(10.0, -score_bruto))

    etiqueta = "debil"
    for umbral, etq in ETIQUETAS:
        if score_norm >= umbral:
            etiqueta = etq
            break

    parametros = []
    parametros.extend(act_c)
    parametros.extend(act_p)
    parametros.extend(act_n)
    parametros.extend(act_conc)
    parametros.extend(act_i)
    parametros.extend(act_d)

    return {
        "score_emocional": round(score_norm, 2),
        "peso_emocional": etiqueta,
        "score_bruto": round(score_bruto, 2),
        "parametros_utilizados": parametros,
        "signo": "negativo" if score_bruto < 0 else "positivo",
    }


def etiquetar(score: float) -> str:
    for umbral, etq in ETIQUETAS:
        if score >= umbral:
            return etq
    return "debil"
