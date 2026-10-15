"""Generación de informe PDF oscuro para Noósfera."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Sequence

from noosfera_project.servicios.persistencia import obtener_eventos_recientes

REPORTLAB_OK = False
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle

    REPORTLAB_OK = True
except Exception as exc:
    logging.warning("pdf_dashboard:20 fallo y se silencio: %s", exc)
    pass


def _estilos() -> dict | None:
    if not REPORTLAB_OK:
        return None
    return {
        "titulo": ParagraphStyle("titulo", fontSize=18, leading=22, spaceAfter=10),
        "meta": ParagraphStyle("meta", fontSize=10, leading=13, spaceAfter=12),
        "encabezado": ParagraphStyle("encabezado", fontSize=14, leading=18, spaceAfter=8),
    }


def generar_pdf(ruta_salida: str | Path, limite: int = 60) -> Path:
    estilos = _estilos()
    eventos = obtener_eventos_recientes(limite=limite)
    if not eventos:
        raise RuntimeError("No hay eventos para el PDF.")

    # Fallback sin dependencia externa: si ReportLab no esta, exporta un
    # .txt con el mismo contenido en vez de tumbar todo el ciclo.
    if estilos is None:
        ruta = Path(ruta_salida)
        if ruta.suffix.lower() == ".pdf":
            ruta = ruta.with_suffix(".txt")
        lineas = ["Noósfera — informe de eventos emergentes",
                  f"Generado: {datetime.utcnow().isoformat()}",
                  f"Eventos incluidos: {len(eventos)}", "", "Detalle:"]
        for idx, ev in enumerate(eventos, start=1):
            lineas.append(
                f"{idx}. [{ev.get('fuente') or ''}] {ev.get('titulo') or ''} "
                f"({ev.get('publicado') or ''}) p={ev.get('puntuacion') or ''}"
            )
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return ruta

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(ruta), pagesize=A4, title="Noósfera")
    elementos = [
        Paragraph("Noósfera — informe de eventos emergentes", estilos["titulo"]),
        Paragraph(f"Generado: {datetime.utcnow().isoformat()}", estilos["meta"]),
        Paragraph(f"Eventos incluidos: {len(eventos)}", estilos["meta"]),
        Paragraph("Detalle", estilos["encabezado"]),
    ]

    filas: list[Sequence[str]] = [["#", "Fuente", "Título", "Publicado", "Puntuación"]]
    for idx, ev in enumerate(eventos, start=1):
        titulo = str(ev.get("titulo") or "")[:100]
        filas.append(
            [
                str(idx),
                str(ev.get("fuente") or ""),
                titulo,
                str(ev.get("publicado") or ""),
                str(ev.get("puntuacion") or ""),
            ]
        )

    tabla = Table(filas, colWidths=[1 * cm, 3.5 * cm, 9.5 * cm, 3.5 * cm, 1.5 * cm])
    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0f0f0f")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e5e5e5")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elementos.append(tabla)
    doc.build(elementos)
    return ruta
