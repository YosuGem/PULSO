"""Motor de detección de eventos emergentes."""

from __future__ import annotations

import re
from typing import Any

PATRONES_EMERGENTES = [
    r"crisis(?: de| en)?(?: \w+){0,5}",
    r"protestas?(?: en| contra)?(?: \w+){0,5}",
    r"terremoto(?:\s+\d+(?:[.,]\d+)?){0,2}",
    r"erupci[oó]n(?:\s+\w+){0,3}",
    r"tsunami",
    r"huelga(?: general| de)?(?: \w+){0,3}",
    r"ataque(?:s)?(?: \w+){0,3}",
    r"derrame(?: de| en)?(?: \w+){0,3}",
    r"ciberataque(?:s)?(?: \w+){0,3}",
    r"alerta sanitaria(?: de)?(?: \w+){0,3}",
    r"restricciones?(?: de| en)?(?: \w+){0,3}",
    r"desastre(?:s)?(?: en| de)?(?: \w+){0,3}",
    r"emergencia(?: sanitaria| climatica| civil)?(?: \w+){0,3}",
    r"impacto global(?: \w+){0,3}",
    r"recesi[oó]n",
    r"default(?: soberano| de)?(?: \w+){0,3}",
    r"colapso(?: de| en)?(?: \w+){0,3}",
    r"inundaci[oó]n(?: \w+){0,3}",
    r"incendio(?:s)?(?: en| de)?(?: \w+){0,3}",
    r"explos[ió]n(?: \w+){0,3}",
    r"epidemia(?: de)?(?: \w+){0,3}",
    r"pandemia(?: de)?(?: \w+){0,3}",
    r"guerra(?: civil| comercial)?(?: \w+){0,3}",
    r"tensi[oó]n(?: en| entre)?(?: \w+){0,3}",
    r"sanciones?(?: de| contra)?(?: \w+){0,3}",
    r"embargo(?: a| contra)?(?: \w+){0,3}",
    r"disrupci[oó]n(?:\s+\w+){0,3}",
]

# Pesos de cada patrón emergente (alineados en orden a PATRONES_EMERGENTES).
# Patrones de mayor gravedad (guerra, colapso, pandemia, recesión...) pesan más.
PESOS_EMERGENTES = [
    0.15, 0.25, 0.1, 0.1, 0.05, 0.2, 0.3, 0.15, 0.2, 0.1,
    0.1, 0.2, 0.15, 0.25, 0.35, 0.3, 0.2, 0.1, 0.15, 0.2,
    0.15, 0.25, 0.4, 0.2, 0.2, 0.15, 0.2,
]


def detectar(texto: str) -> dict[str, Any]:
    limpio = (texto or "").lower()
    hallazgos: list[str] = []
    for patron in PATRONES_EMERGENTES:
        if re.search(patron, limpio):
            hallazgos.append(patron)
    # Similitud léxica: suma SOLO los pesos de los patrones que REALMENTE
    # coincidieron (hallazgos), no la lista completa. Así una coincidencia
    # trivial no pesa igual que una crítica (corregido: antes sumaba fija).
    similitud = 0.0
    if hallazgos:
        for i, patron in enumerate(PATRONES_EMERGENTES):
            if patron in hallazgos:
                similitud += PESOS_EMERGENTES[i]
    return {
        "coincidencias": hallazgos,
        "puntos": len(hallazgos),
        "nivel": ("alto" if len(hallazgos) >= 6 else "medio" if len(hallazgos) >= 3 else "bajo") if hallazgos else "bajo",
        "similitud_lexica": round(similitud, 4),
    }


def extraer_contexto(texto: str, contexto_max: int = 160) -> str:
    candidatos = re.findall(r"(?:en|desde)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)?)", texto or "")
    for candidato in candidatos[:3]:
        if 2 <= len(candidato.split()) <= 6:
            return candidato.title()
    fragmento = (texto or "").strip().replace("\n", " ")
    return fragmento[:contexto_max] + "..." if len(fragmento) > contexto_max else fragmento
