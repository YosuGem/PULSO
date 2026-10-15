"""
Radar de corto plazo (0.2.2-dev).

Para qué sirve
--------------
Modo de prueba y detección a ventana corta: 3 o 7 días. El histórico normal
guarda una foto por día y compara el último contra el anterior. El radar hace
algo distinto y complementario: parte el corpus en una ventana reciente y una
anterior y responde tres preguntas que un sistema de eventos emergentes debe
poder contestar en días, no en meses:

  1. ¿Qué tema es NUEVO? (aparece en la ventana reciente y no en la anterior)
  2. ¿Qué tema CRECE?     (sube su volumen respecto a la ventana anterior)
  3. ¿Qué tema se ENFRÍA? (baja o desaparece)


Sirve para dos cosas:
  - Probar el programa a corto plazo sin esperar meses: se ejecuta, se ve
    qué detecta en 3 o 7 días, y se comprueba si las detecciones tienen
    sentido. Es la única forma de validar cuando no hay tiempo para una
    observación larga.
  - Detectar temas emergentes antes que los medios: lo que crece o aparece
    en una ventana corta es exactamente la señal temprana.

Diseño
------
- Sin dependencias nuevas: solo sqlite3 y el clasificador existente.
- Bajo acoplamiento: recibe los documentos (no lee la BD directamente) para
  poder probarlo con datos sintéticos.
- Respeta temas_excluidos.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from noosfera_project.deteccion.temas_excluidos import esta_excluido


def _fecha(doc: dict[str, Any]) -> datetime | None:
    """Fecha del documento: 'publicado' o 'creado_en'.

    Normaliza a datetime naive (sin zona horaria): algunos 'creado_en'
    vienen con offset (+00:00) y comparar naive contra aware revienta.
    """
    for campo in ("publicado", "creado_en"):
        valor = doc.get(campo)
        if not valor:
            continue
        texto = str(valor)
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(texto[:26], fmt)
            except ValueError as exc:
                logging.warning("servicios/radar_corto.py:57 fallo y se silencio: %s", exc)
                continue
        try:
            dt = datetime.fromisoformat(texto[:26])
            return dt.replace(tzinfo=None)
        except Exception as exc:
            logging.warning("servicios/radar_corto.py:60 falló y se silenció: %s", exc)
            continue
    return None


def radar(docs: list[dict[str, Any]], ventana_dias: int = 7, hoy: datetime | None = None) -> dict[str, Any]:
    """Analiza el corpus partido en ventana reciente vs anterior.

    `docs` debe traer 'texto' y una fecha ('publicado' o 'creado_en').
    Devuelve nuevos, crecimiento, enfriamiento y el detalle por categoría.
    """
    from noosfera_project.procesamiento.clasificador_tematico import clasificar

    hoy = hoy or datetime.now()
    corte = hoy - timedelta(days=ventana_dias)

    recientes: Counter = Counter()
    anteriores: Counter = Counter()
    fuentes_recientes: dict[str, set] = {}
    fuentes_anteriores: dict[str, set] = {}
    sin_fecha = 0

    for d in docs:
        texto = d.get("texto") or ""
        if not texto:
            continue
        fecha = _fecha(d)
        cat = clasificar(texto)["categoria"]
        if esta_excluido(cat) or cat == "undetected":
            continue
        fuente = d.get("fuente") or "?"
        if fecha is None:
            # Sin fecha no se puede ubicar en una ventana: se cuenta como
            # reciente para no perder la señal, pero se informa.
            sin_fecha += 1
            recientes[cat] += 1
            fuentes_recientes.setdefault(cat, set()).add(fuente)
            continue
        if fecha >= corte:
            recientes[cat] += 1
            fuentes_recientes.setdefault(cat, set()).add(fuente)
        else:
            anteriores[cat] += 1
            fuentes_anteriores.setdefault(cat, set()).add(fuente)

    categorias = set(recientes) | set(anteriores)

    nuevos, crecen, enfrian, estables = [], [], [], []
    for cat in categorias:
        rec = recientes.get(cat, 0)
        ant = anteriores.get(cat, 0)
        delta = rec - ant
        entrada = {
            "categoria": cat,
            "recientes": rec,
            "anteriores": ant,
            "delta": delta,
            "fuentes_recientes": len(fuentes_recientes.get(cat, set())),
        }
        if ant == 0 and rec > 0:
            nuevos.append(entrada)
        elif delta > 0:
            crecen.append(entrada)
        elif delta < 0:
            enfrian.append(entrada)
        else:
            estables.append(entrada)

    # Orden: lo que más crece primero; en nuevos, por volumen reciente.
    nuevos.sort(key=lambda x: x["recientes"], reverse=True)
    crecen.sort(key=lambda x: x["delta"], reverse=True)
    enfrian.sort(key=lambda x: x["delta"])  # más negativo primero

    return {
        "ventana_dias": ventana_dias,
        "corte": corte.date().isoformat(),
        "hoy": hoy.date().isoformat(),
        "total_recientes": sum(recientes.values()),
        "total_anteriores": sum(anteriores.values()),
        "sin_fecha": sin_fecha,
        "nuevos": nuevos,
        "crecen": crecen,
        "enfrian": enfrian,
        "estables": len(estables),
    }


def informe(res: dict[str, Any]) -> str:
    """Texto legible del resultado del radar."""
    lineas = [
        f"RADAR CORTO PLAZO — ventana {res['ventana_dias']} días",
        f"  corte: {res['corte']}   recientes: {res['total_recientes']}   anteriores: {res['total_anteriores']}",
    ]
    if res["sin_fecha"]:
        lineas.append(f"  (avisos: {res['sin_fecha']} documentos sin fecha, contados como recientes)")

    if res["nuevos"]:
        lineas.append("\n  NUEVOS (no estaban en la ventana anterior):")
        for n in res["nuevos"][:10]:
            lineas.append(f"    + {n['categoria']:24} {n['recientes']:4} docs, {n['fuentes_recientes']} fuentes")
    if res["crecen"]:
        lineas.append("\n  CRECEN:")
        for n in res["crecen"][:10]:
            lineas.append(f"    ^ {n['categoria']:24} {n['anteriores']}->{n['recientes']} ({n['delta']:+d})")
    if res["enfrian"]:
        lineas.append("\n  SE ENFRIAN:")
        for n in res["enfrian"][:10]:
            lineas.append(f"    v {n['categoria']:24} {n['anteriores']}->{n['recientes']} ({n['delta']:+d})")
    if not (res["nuevos"] or res["crecen"] or res["enfrian"]):
        lineas.append("\n  Sin cambios entre ventanas.")
    return "\n".join(lineas)


if __name__ == "__main__":
    import sqlite3
    import sys
    from pathlib import Path

    RUTA = Path(__file__).resolve().parents[1] / "eventos.db"
    if not RUTA.exists():
        print("Sin base de datos.")
        sys.exit(1)
    conn = sqlite3.connect(str(RUTA))
    conn.row_factory = sqlite3.Row
    docs = [dict(r) for r in conn.execute("SELECT fuente, texto, publicado, creado_en FROM lenguaje_colectivo")]
    conn.close()
    for v in (3, 7):
        print(informe(radar(docs, ventana_dias=v)))
        print()
