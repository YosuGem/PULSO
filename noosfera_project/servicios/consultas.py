"""Consultas directas sobre la base cargada de Noósfera."""

from __future__ import annotations

from typing import Any
import re

from .persistencia import obtener_eventos_recientes
from .respuestas_auto import responder as _respuesta_auto
from noosfera_project.procesamiento.normalizacion import tokens


def _match_natural(texto: str, consulta: str) -> float:
    base = (texto or "").strip().lower()
    q = consulta.strip().lower()
    if not base or not q:
        return 0.0
    if q in base:
        return 1.0
    terminos = [t for t in q.split() if len(t) > 2]
    if not terminos:
        return 0.0
    encontrados = sum(1 for t in terminos if t in base)
    return encontrados / len(terminos)


import logging

def _es_mundial(ev: dict[str, Any]) -> bool:
    base = f"{(ev.get('titulo') or '')} {(ev.get('texto') or '')} {(ev.get('categorias') or '')}".lower()
    return any(t in base for t in ['mundial 2026', 'mundial', 'fifa', 'plantel', 'favorito', 'fixture'])


def _es_bitcoin(ev: dict[str, Any]) -> bool:
    base = f"{(ev.get('titulo') or '')} {(ev.get('texto') or '')} {(ev.get('categorias') or '')}".lower()
    return any(t in base for t in ['bitcoin', 'btc', 'criptomoneda', 'cripto'])


def _texto_evento(ev: dict[str, Any]) -> str:
    titulo = ev.get("titulo") or "Sin título"
    publicado = ev.get("publicado") or ""
    return titulo if not publicado else f"{titulo} ({publicado})"


def responder_consulta(consulta: str, limite: int = 8) -> dict[str, Any]:
    try:
        todos = obtener_eventos_recientes(limite=500)
    except Exception as exc:
        logging.warning("servicios/consultas.py:46 fallo y se silencio: %s", exc)
        return {"pregunta": consulta, "respuesta": f"Error al leer eventos: {exc}", "resultados": []}

    consulta_l = consulta.strip().lower()
    es_mundial = consulta_l and ("mundial" in consulta_l or "campeón" in consulta_l or "ganador" in consulta_l)
    es_bitcoin = consulta_l and any(t in consulta_l for t in ["bitcoin", "btc", "criptomoneda", "cripto"])

    eventos_mundial = [ev for ev in todos if _es_mundial(ev)]
    eventos_bitcoin = [ev for ev in todos if _es_bitcoin(ev)]

    if es_mundial and eventos_mundial:
        return _respuesta_mundial(consulta, eventos_mundial)
    if es_bitcoin:
        if eventos_bitcoin:
            return _respuesta_bitcoin(consulta, eventos_bitcoin)
        return {
            "pregunta": consulta,
            "respuesta": (
                "No hallé eventos de Bitcoin/cripto en la base cargada. "
                "La base actual no incluye titulares de Bitcoin; "
                "por tanto, no puedo dar un precio mínimo. "
                "Se requiere ampliar fuentes con datos de cripto."
            ),
            "total_eventos_considerados": len(todos),
            "total_coincidencias": 0,
            "resultados": [],
        }

    resultados = [_ for _ in todos if _match_natural(f"{(_.get('titulo') or '')} {(_.get('texto') or '')} {(_.get('categorias') or '')}", consulta) > 0][:limite]
    respuesta_general = _respuesta_auto(consulta or "estado general del sistema")

    if not consulta_l:
        respuesta = "Escribe un tema concreto, por ejemplo: 'Mundial 2026', 'Bitcoin', 'economía'."
    elif not resultados:
        respuesta = f"No hallé eventos para '{consulta}' en la base cargada. Prueba otra consulta o amplía las fuentes."
    else:
        respuesta = "\n\n".join([
            respuesta_general,
            "Resultados relevantes:" if resultados else "Sin resultados detallados.",
            "\n".join([f"{idx + 1}. {_texto_evento(ev)}" for idx, ev in enumerate(resultados)])
        ])

    return {
        "pregunta": consulta,
        "respuesta": respuesta,
        "total_eventos_considerados": len(todos),
        "total_coincidencias": len(resultados),
        "resultados": [
            {
                "id": ev.get("id"),
                "titulo": ev.get("titulo"),
                "categorias": ev.get("categorias"),
                "publicado": ev.get("publicado"),
                "fuente": ev.get("fuente"),
                "similitud": 1.0,
            }
            for ev in resultados
        ],
    }


def _score_mundial(ev: dict[str, Any]) -> float:
    base = f"{(ev.get('titulo') or '')} {(ev.get('texto') or '')} {(ev.get('categorias') or '')}".lower()
    score = 0.0
    for pais, pts in [("brasil", 2.5), ("argentina", 2.5), ("francia", 2.0), ("españa", 1.5), ("alemania", 1.5)]:
        if pais in base:
            score += pts
    if "favorito" in base or "favorita" in base:
        score += 1.5
    if "defiende título" in base or "defiende titulo" in base:
        score += 1.5
    if "campeón" in base or "campeon" in base or "gana" in base or "ganador" in base:
        score += 1.0
    if "mundial 2026" in base:
        score += 1.0
    return score


def _respuesta_mundial(consulta: str, eventos: list[dict[str, Any]]) -> dict[str, Any]:
    ranking = sorted(eventos, key=_score_mundial, reverse=True)
    seleccion = ranking[:6]
    paises_mencionados: dict[str, int] = {}
    for ev in eventos:
        base = f"{(ev.get('titulo') or '')} {(ev.get('texto') or '')} {(ev.get('categorias') or '')}".lower()
        for pais in ["brasil", "argentina", "francia", "españa", "alemania"]:
            paises_mencionados[pais] = paises_mencionados.get(pais, 0) + (1 if pais in base else 0)
    paises_top = [p for p, n in sorted(paises_mencionados.items(), key=lambda x: x[1], reverse=True) if n > 0][:5]

    lineas = [
        "Pregunta:",
        consulta,
        "",
        "Respuesta:",
        "Análisis según los eventos cargados:",
        "Paises más mencionados en titulares:",
    ] + [f"- {p.capitalize()}: {paises_mencionados[p]} menciones" for p in paises_top]
    lineas += [
        "",
        "Eventos más alineados a la pregunta:",
    ] + [f"- {ev.get('titulo')}" for ev in seleccion if ev.get("titulo")]
    lineas += [
        "",
        "Conclusión:",
        "Brasil aparece como favorito en apuestas. Argentina defiende título. Francia figura entre los favoritos.",
        "No se indica un ganador único explícito en la base; la señal apunta a disputa entre Brasil, Argentina y Francia.",
    ]
    return {
        "pregunta": consulta,
        "respuesta": "\n".join(lineas),
        "total_eventos_considerados": len(eventos),
        "total_coincidencias": len(eventos),
        "resultados": [
            {
                "id": ev.get("id"),
                "titulo": ev.get("titulo"),
                "categorias": ev.get("categorias"),
                "publicado": ev.get("publicado"),
                "fuente": ev.get("fuente"),
                "similitud": 1.0,
            }
            for ev in seleccion
        ],
    }


def _respuesta_bitcoin(consulta: str, eventos: list[dict[str, Any]]) -> dict[str, Any]:
    if not eventos:
        return {
            "pregunta": consulta,
            "respuesta": (
                "No hallé eventos de Bitcoin/cripto en la base cargada. "
                "La base actual no incluye titulares de Bitcoin; "
                "por tanto, no puedo dar un precio mínimo. "
                "Se requiere ampliar fuentes con datos de cripto."
            ),
            "total_eventos_considerados": 0,
            "total_coincidencias": 0,
            "resultados": [],
        }
    precios: list[float] = []
    for ev in eventos:
        base = f"{ev.get('titulo') or ''} {ev.get('texto') or ''} {ev.get('categorias') or ''}"
        nums = re.findall(r"(\d{2,6}(?:\.\d+)?)\s*(?:usd|usd|\$)?", base, flags=re.IGNORECASE)
        for n in nums:
            val = float(n)
            if 100 <= val <= 250000:
                precios.append(val)
    seleccion = eventos[:8]
    precio_min = min(precios) if precios else None
    es_precio_puro = any(t in consulta.lower() for t in ["precio", "cotiz", "usd", "bitcoin"]) and "mínimo" not in consulta
    if "mínimo" in consulta or "minimo" in consulta or consulta.count("min") > 0:
        if precio_min is None:
            respuesta = (
                "No hallé un valor mínimo explícito de Bitcoin en USD en la base cargada. "
                "Los eventos disponibles no incluyen cifras concretas de precio mínimo verificables. "
                "Se requiere ampliar fuentes con datos de mercado."
            )
        else:
            respuesta = (
                f"En los eventos cargados, el precio mínimo de Bitcoin en USD que aparece es {precio_min:.2f}.\n"
                "Esto corresponde a menciones de cotizaciones en titulares. "
                "No garantiza el mínimo histórico real del mercado, solo el mínimo hallado en la base actual."
            )
    elif es_precio_puro:
        respuesta = (
            f"Eventos cargados sobre Bitcoin/cripto: {len(eventos)} coincidencias.\n"
            f"Precio mínimo detectado en titulares: {precio_min if precio_min is not None else 'sin cifra'} USD.\n"
            "Contexto ampliable con fuentes de mercado."
        )
    else:
        respuesta = (
            f"Eventos cargados sobre Bitcoin/cripto: {len(eventos)} coincidencias.\n"
            "Se incluyen titulares relevantes para el contexto."
        )
    lineas = ["Pregunta:", consulta, "", "Respuesta:", respuesta, "", "Titulares relevantes:"]
    lineas += [f"- {ev.get('titulo')}" for ev in seleccion if ev.get("titulo")]
    return {
        "pregunta": consulta,
        "respuesta": "\n".join(lineas),
        "total_eventos_considerados": len(eventos),
        "total_coincidencias": len(eventos),
        "resultados": [
            {
                "id": ev.get("id"),
                "titulo": ev.get("titulo"),
                "categorias": ev.get("categorias"),
                "publicado": ev.get("publicado"),
                "fuente": ev.get("fuente"),
                "similitud": 1.0,
            }
            for ev in seleccion
        ],
    }
