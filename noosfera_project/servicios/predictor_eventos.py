"""Predictor de eventos emergentes basado en historial persistente."""

from __future__ import annotations

import logging
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

_RUTA_HISTORIAL = Path(__file__).resolve().parent / "historico_eventos.json"


def _parse_fecha(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except Exception as exc:
        logging.warning("predictor_eventos:19 fallo y se silencio: %s", exc)
        return None


def cargar_historico() -> list[dict[str, Any]]:
    if _RUTA_HISTORIAL.exists():
        try:
            datos = json.loads(_RUTA_HISTORIAL.read_text(encoding="utf-8"))
            if isinstance(datos, list):
                return datos
        except Exception as exc:
            logging.warning("predictor_eventos:29 fallo y se silencio: %s", exc)
            pass
    return []


def guardar_historico(eventos: list[dict[str, Any]]) -> None:
    _RUTA_HISTORIAL.write_text(
        json.dumps(eventos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def registrar_evento(evento: dict[str, Any]) -> None:
    historial = cargar_historico()
    historial.append(evento)
    guardar_historico(historial)


def normalizar_categoria(cat: str) -> str:
    cat = cat.strip()
    if not cat:
        return cat
    lower = cat.lower()
    if "fees and rates" in lower or "prices (fares" in lower:
        return "Precios, comisiones y tasas"
    if "oil (petroleum)" in lower or "gasoline" in lower:
        return "Petróleo y gasolina"
    if "attack on iran" in lower:
        return "Ataque a Irán (2026)"
    if "rare-earth" in lower or "rare earth" in lower:
        return "Tierras raras"
    if "supercomputer" in lower:
        return "Supercomputación"
    if "workplace environment" in lower or "workplace hazards" in lower:
        return "Entorno laboral"
    if "markets" in lower or "sell-off" in lower or "tech stocks" in lower:
        return "Mercados financieros"
    return cat


def _categorias_planas(historial: list[dict[str, Any]]) -> list[str]:
    categorias_planas: list[str] = []
    for e in historial:
        c = e.get("categorias") or ""
        partes = [normalizar_categoria(p) for p in c.split(",") if p.strip()]
        categorias_planas.extend(partes)
    return categorias_planas


def _frecuencia_por_categoria(historial: list[dict[str, Any]]) -> dict[str, int]:
    return Counter(_categorias_planas(historial))


def _metadatos_categoria(historial: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    datos: dict[str, dict[str, Any]] = {}
    for e in historial:
        fecha = _parse_fecha(e.get("publicado") or e.get("creado_en"))
        if fecha is None:
            continue
        for parte in [p.strip() for p in (e.get("categorias") or "").split(",") if p.strip()]:
            cat = normalizar_categoria(parte)
            if not cat:
                continue
            actual = datos.setdefault(
                cat,
                {"conteo": 0, "primera_fecha": fecha, "ultima_fecha": fecha, "fechas": []},
            )
            actual["conteo"] += 1
            if fecha < actual["primera_fecha"]:
                actual["primera_fecha"] = fecha
            if fecha > actual["ultima_fecha"]:
                actual["ultima_fecha"] = fecha
            actual["fechas"].append(fecha)
    resultado: dict[str, dict[str, Any]] = {}
    for cat, meta in datos.items():
        fechas = sorted(meta["fechas"])
        primera = meta["primera_fecha"]
        ultima = meta["ultima_fecha"]
        persistencia_dias = max((ultima - primera).days + 1, 1)
        ventana = ultima - timedelta(days=7)
        eventos_7d = sum(1 for f in fechas if f >= ventana)
        velocidad = eventos_7d / max(persistencia_dias, 1)
        resultado[cat] = {
            "conteo": meta["conteo"],
            "primera_fecha": primera,
            "ultima_fecha": ultima,
            "persistencia_dias": persistencia_dias,
            "velocidad_crecimiento": velocidad,
        }
    return resultado


def _detectar_semillas(historial: list[dict[str, Any]], limite: int = 5) -> list[dict[str, Any]]:
    primer_evento: dict[str, dict[str, Any]] = {}
    for e in historial:
        c = e.get("categorias") or ""
        for parte in [p.strip() for p in c.split(",") if p.strip()]:
            primer_evento.setdefault(parte, e)

    semillas = [
        {
            "categoria": cat,
            "titulo_semilla": primer_evento[cat].get("titulo", ""),
            "prediccion": f"Primer evento registrado de: {cat}",
        }
        for cat in list(primer_evento)[:limite]
    ]
    return semillas


def _detectar_ruptura_patron(historial: list[dict[str, Any]], limite: int = 5) -> list[dict[str, Any]]:
    conteo = _frecuencia_por_categoria(historial)
    repetidas = set(conteo.keys())
    registrados: set[str] = set()
    resultados: list[dict[str, Any]] = []
    for e in historial:
        cats = [normalizar_categoria(p.strip()) for p in (e.get("categorias") or "").split(",") if p.strip()]
        nuevas = [c for c in cats if c and c not in repetidas and c not in registrados]
        for cat in nuevas:
            registrados.add(cat)
            resultados.append(
                {
                    "categoria": cat,
                    "titulo": e.get("titulo", ""),
                    "prediccion": f"Nuevo patrón detectado: {cat} no estaba en el histórico",
                }
            )
        if len(resultados) >= limite:
            break
    return resultados


def _correlaciones(historial: list[dict[str, Any]], limite: int = 5) -> list[dict[str, Any]]:
    pares: dict[tuple[str, str], int] = defaultdict(int)
    for e in historial:
        cats = [normalizar_categoria(p.strip()) for p in (e.get("categorias") or "").split(",") if p.strip()]
        limpios = sorted(set(cats))
        for i in range(len(limpios)):
            for j in range(i + 1, len(limpios)):
                pares[(limpios[i], limpios[j])] += 1

    top = sorted(pares.items(), key=lambda x: x[1], reverse=True)[:limite]
    return [
        {
            "categoria_a": a,
            "categoria_b": b,
            "coincidencias": veces,
            "prediccion": f"{a} y {b} aparecen juntas con frecuencia ({veces} veces)",
        }
        for (a, b), veces in top
    ]


def predecir_siguientes(limite: int = 5) -> list[dict[str, Any]]:
    historial = cargar_historico()
    if len(historial) < 3:
        return [{"prediccion": "Insuficiente historial para predecir."}]

    frecuentes = _frecuencia_por_categoria(historial).most_common(limite)
    meta = _metadatos_categoria(historial)
    base: list[dict[str, Any]] = []
    for cat, veces in frecuentes:
        m = meta.get(cat, {})
        persistencia = float(m.get("persistencia_dias", 1))
        velocidad = float(m.get("velocidad_crecimiento", 0.0))
        peso_persistencia = min(persistencia / 30.0, 1.0)
        peso_velocidad = min(velocidad, 1.0)
        puntuacion = round(min(1.0, 0.5 * veces + 0.3 * peso_persistencia + 0.2 * peso_velocidad), 3)
        base.append(
            {
                "categoria": cat,
                "ocurrencias_previas": veces,
                "prediccion": f"Alta probabilidad de repetición en: {cat}",
                "persistencia_dias": int(persistencia),
                "velocidad_crecimiento": round(velocidad, 3),
                "puntuacion": puntuacion,
            }
        )
    return (
        base
        + _detectar_semillas(historial, limite=2)
        + _detectar_ruptura_patron(historial, limite=2)
        + _correlaciones(historial, limite=2)
    )


def predecir_desde_texto(texto: str, limite: int = 3) -> list[dict[str, Any]]:
    historial = cargar_historico()
    if not historial:
        return [{"prediccion": "Historial vacío."}]

    terminos = [t.strip().lower() for t in texto.split() if len(t.strip()) > 3]
    meta = _metadatos_categoria(historial)
    categorias_ordenadas = sorted(meta.items(), key=lambda x: x[1]["conteo"], reverse=True)
    puntuados: list[tuple[str, int]] = []
    for cat, m in categorias_ordenadas:
        cat_l = cat.lower()
        puntos = sum(1 for t in terminos if t in cat_l)
        if puntos:
            puntuados.append((cat, puntos))

    agrupados: dict[str, int] = {}
    for cat, pts in puntuados:
        agrupados[cat] = agrupados.get(cat, 0) + pts

    ordenados = sorted(agrupados.items(), key=lambda x: x[1], reverse=True)[:limite]
    if not ordenados:
        return [{"prediccion": "Sin coincidencias con el historial."}]

    return [
        {
            "categoria": cat,
            "coincidencias": pts,
            "prediccion": f"El término suele asociarse a: {cat}",
        }
        for cat, pts in ordenados
    ]


def sincronizar_historial(limite: int = 200) -> None:
    from noosfera_project.servicios.persistencia import obtener_eventos_recientes

    eventos = obtener_eventos_recientes(limite=limite)
    historial = cargar_historico()
    existentes = {e.get("id") for e in historial if "id" in e}
    nuevos = [ev for ev in eventos if ev.get("id") not in existentes]
    if nuevos:
        historial.extend(nuevos)
        guardar_historico(historial)


if __name__ == "__main__":
    print("Predictor listo.")
