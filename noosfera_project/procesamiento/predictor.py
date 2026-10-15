"""Modelo predictivo tipo predictor sobre lenguaje colectivo."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any


@dataclass
class Senal:
    etiqueta: str
    documentos: int
    frecuencia: int
    primera_fecha: str
    ultima_fecha: str
    tendencia: str


import logging
def _fecha(doc: dict[str, Any]) -> datetime | None:
    val = (doc.get("publicado") or doc.get("creado_en") or "").strip()
    if not val:
        return None
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception as exc:
        logging.warning("predictor:28 fallo y se silencio: %s", exc)
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def calcular_tendencia(conteos_por_fecha: dict[str, int], dias: int = 7) -> str:
    if not conteos_por_fecha:
        return "constante"
    fechas = sorted(conteos_por_fecha)
    if len(fechas) < 2:
        return "constante"
    ultimos = [conteos_por_fecha[f] for f in fechas[-dias:]]
    if len(ultimos) < 2:
        return "constante"
    crecimiento = sum(ultimos[i] >= ultimos[i - 1] for i in range(1, len(ultimos)))
    if crecimiento >= len(ultimos) - 1:
        return "ascendente"
    if crecimiento == 0:
        return "descendente"
    return "volatil"


def senales_emergentes(documentos: list[dict[str, Any]], horizonte_dias: int = 30) -> list[Senal]:
    """Detecta etiquetas (tokens normalizados) con trayectoria temporal reciente."""
    ahora = datetime.now(timezone.utc)
    limite = ahora - timedelta(days=horizonte_dias)
    bucket: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "documentos": 0,
        "frecuencia": 0,
        "conteos_por_fecha": Counter(),
        "primera": None,
        "ultima": None,
    })
    for doc in documentos:
        fecha = _fecha(doc)
        if fecha is None or fecha < limite:
            continue
        fecha_str = fecha.date().isoformat()
        for token in doc.get("_tokens", []) if isinstance(doc.get("_tokens"), list) else []:
            info = bucket[token]
            info["documentos"] += 1
            info["frecuencia"] += 1
            info["conteos_por_fecha"][fecha_str] += 1
            info["ultima"] = fecha_str
            info["primera"] = fecha_str if info["primera"] is None else min(info["primera"], fecha_str)
    resultados = []
    for token, info in bucket.items():
        resultados.append(
            Senal(
                etiqueta=token,
                documentos=info["documentos"],
                frecuencia=info["frecuencia"],
                primera_fecha=info["primera"] or "",
                ultima_fecha=info["ultima"] or "",
                tendencia=calcular_tendencia(dict(info["conteos_por_fecha"])),
            )
        )
    resultados.sort(key=lambda s: (s.frecuencia, s.etiqueta), reverse=True)
    return resultados
