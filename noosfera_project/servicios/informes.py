"""Generacion de informes PDF estilo Noosfera."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

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
    logging.warning("informes:19 fallo y se silencio: %s", exc)
    pass


def generar_informe(ruta_salida: str | Path) -> Path | None:
    eventos = obtener_eventos_recientes(limite=50)
    if not eventos:
        raise RuntimeError("No hay eventos para el informe.")

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if not REPORTLAB_OK:
        raise RuntimeError("ReportLab no disponible.")

    doc = SimpleDocTemplate(str(ruta), pagesize=A4, title="Noosfera informe")
    estilo_titulo = ParagraphStyle("titulo", fontSize=18, leading=22, spaceAfter=10)
    estilo_meta = ParagraphStyle("meta", fontSize=10, leading=13, spaceAfter=12)
    estilo_encabezado = ParagraphStyle("encabezado", fontSize=14, leading=18, spaceAfter=8)

    elementos = [
        Paragraph("Noosfera — informe de eventos emergentes", estilo_titulo),
        Paragraph(f"Generado: {datetime.utcnow().isoformat()}", estilo_meta),
        Paragraph(f"Eventos incluidos: {len(eventos)}", estilo_meta),
        Paragraph("Detalle", estilo_encabezado),
    ]

    tabla = [["#", "Fuente", "Titulo", "Publicado", "Puntuacion"]]
    for idx, ev in enumerate(eventos, start=1):
        titulo = (ev.get("titulo") or "")[:100]
        tabla.append(
            [
                str(idx),
                ev.get("fuente") or "",
                titulo,
                ev.get("publicado") or "",
                str(ev.get("puntuacion") or ""),
            ]
        )

    tabla_obj = Table(tabla, colWidths=[1 * cm, 3.5 * cm, 9.5 * cm, 3.5 * cm, 1.5 * cm])
    tabla_obj.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e5e7eb")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elementos.append(tabla_obj)
    doc.build(elementos)
    return ruta
