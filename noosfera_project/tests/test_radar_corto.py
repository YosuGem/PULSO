"""Tests del radar de corto plazo (Bloque: detección temprana, 0.2.2-dev)."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, "noosfera_project")

from noosfera_project.servicios.radar_corto import radar, informe

HOY = datetime(2026, 10, 11)


def _doc(fuente: str, texto: str, dias_atras: int) -> dict:
    return {
        "fuente": fuente,
        "texto": texto,
        "publicado": (HOY - timedelta(days=dias_atras)).strftime("%Y-%m-%d"),
    }


def test_nuevo_detectado():
    """Un tema que solo aparece en la ventana reciente es NUEVO."""
    docs = [
        _doc("reddit", "Acampada en la plaza del pueblo", 1),
        _doc("telegram", "Acampada y pancartas", 2),
    ]
    res = radar(docs, ventana_dias=7, hoy=HOY)
    cats = [n["categoria"] for n in res["nuevos"]]
    assert "movilizacion_social" in cats


def test_crecimiento_detectado():
    """Un tema con más volumen reciente que anterior CRECE."""
    docs = [
        _doc("hn", "Robot humanoide en la cadena", 1),
        _doc("hn", "Robotica industrial y cobots", 2),
        _doc("telegram", "Robot colaborativo en la fabrica", 9),
    ]
    res = radar(docs, ventana_dias=7, hoy=HOY)
    cats = [c["categoria"] for c in res["crecen"]]
    assert "robotica" in cats


def test_enfriamiento_detectado():
    """Un tema con más volumen anterior que reciente SE ENFRÍA."""
    docs = [
        _doc("foro", "Hashimoto y tiroides autoinmune", 10),
        _doc("foro", "Fatiga cronica y sindrome postviral", 12),
    ]
    res = radar(docs, ventana_dias=7, hoy=HOY)
    cats = [c["categoria"] for c in res["enfrian"]]
    assert "salud_cronica" in cats


def test_deportes_excluido():
    """Los temas excluidos no aparecen en el radar."""
    docs = [
        _doc("reddit", "Champions del Real Madrid", 1),
        _doc("foro", "Final de la champions", 2),
    ]
    res = radar(docs, ventana_dias=7, hoy=HOY)
    todas = [x["categoria"] for x in res["nuevos"] + res["crecen"] + res["enfrian"]]
    assert "deportes" not in todas


def test_sin_fecha_contado():
    """Documentos sin fecha se cuentan como recientes y se informa."""
    docs = [{"fuente": "x", "texto": "Escasez y falta de stock", "publicado": None}]
    res = radar(docs, ventana_dias=7, hoy=HOY)
    assert res["sin_fecha"] == 1


def test_informe_legible():
    """El informe en texto incluye las secciones esperadas."""
    docs = [
        _doc("reddit", "Acampada en la plaza", 1),
        _doc("hn", "Robot humanoide en la cadena", 1),
    ]
    txt = informe(radar(docs, ventana_dias=7, hoy=HOY))
    assert "RADAR CORTO PLAZO" in txt
    assert "NUEVOS" in txt or "Sin cambios" in txt


def test_ventanas_1_3_7():
    """Ventanas de 1, 3 y 7 días funcionan sin error."""
    docs = [_doc("reddit", "Acampada en la plaza", 0), _doc("hn", "Robot en la cadena", 2)]
    for v in (1, 3, 7):
        res = radar(docs, ventana_dias=v, hoy=HOY)
        assert res["ventana_dias"] == v


def test_ventana_1_dia_detecta_cambio_ayer_hoy():
    """La ventana de 1 día compara hoy contra ayer."""
    docs = [
        _doc("reddit", "Acampada en la plaza del pueblo", 0),
        _doc("telegram", "Manifestacion vecinal", 0),
        _doc("foro", "Fatiga cronica y sindrome postviral", 3),
    ]
    res = radar(docs, ventana_dias=1, hoy=HOY)
    cats = [n["categoria"] for n in res["nuevos"]]
    assert "movilizacion_social" in cats


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
