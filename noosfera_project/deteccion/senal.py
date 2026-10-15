"""Detección de señales del lenguaje colectivo (Bloque C - Fase 1)."""
from __future__ import annotations

from typing import Any

from noosfera_project.procesamiento.clasificador_tematico import clasificar
from noosfera_project.procesamiento.pesos_emocionales import analizar_emocion


def extraer_senales(textos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extrae señales de una lista de textos del corpus.

    Cada señal: categoria, score_emocional, idioma, fuente, texto_id.
    """
    senales: list[dict[str, Any]] = []
    for doc in textos:
        fuente = doc.get("fuente") or ""
        # Defensivo: ignorar documentación del propio proyecto (.md/.txt)
        # para que ningún llamador contamine las señales.
        if fuente.lower().endswith((".md", ".txt")):
            continue
        texto = doc.get("texto") or ""
        if not texto:
            continue
        clas = clasificar(texto)
        emo = analizar_emocion(texto)
        senal = {
            "texto_id": doc.get("id"),
            "fuente": doc.get("fuente"),
            "idioma": doc.get("idioma") or "es",
            "categoria": clas["categoria"],
            "confianza_clasificacion": clas["confianza"],
            "score_emocional": emo["score_emocional"],
            "peso_emocional": emo["peso_emocional"],
            "signo": emo["signo"],
        }
        senales.append(senal)
    return senales
