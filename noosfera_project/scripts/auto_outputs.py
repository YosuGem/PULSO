"""Modo automático de Noósfera: genera salidas y registra en bitácora sin ciclo RSS."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from noosfera_project.servicios.persistencia import crear_base, obtener_eventos_recientes  # noqa: E402
from noosfera_project.servicios.dashboard import generar_dashboard  # noqa: E402
from noosfera_project.servicios.markdown_dashboard import generar_markdown  # noqa: E402
from noosfera_project.servicios.pdf_dashboard import generar_pdf  # noqa: E402
from noosfera_project.servicios.bitacora import registrar_ciclo  # noqa: E402
from noosfera_project.servicios.evaluacion import registrar_evaluacion  # noqa: E402
from noosfera_project.procesamiento.analisis import resumir_eventos  # noqa: E402


SALIDAS = {
    "html": ROOT / "dashboard/index.html",
    "markdown": ROOT / "dashboard/index_dark.html",
    "pdf": ROOT / "informes/ultimo.pdf",
}


def main() -> int:
    crear_base()
    registrar_ciclo("inicio", "Modo automático iniciado")

    eventos = obtener_eventos_recientes(limite=120)
    resumen = resumir_eventos(eventos)
    registrar_ciclo("analisis", f"total={resumen['total']}")
    registrar_evaluacion(resumen["total"], resumen["alto"], resumen["medio"])

    try:
        generar_dashboard(SALIDAS["html"], limite=80)
    except Exception as exc:
        registrar_ciclo("dashboard_html", str(exc), ok=False)

    try:
        generar_markdown(SALIDAS["markdown"], limite=80)
    except Exception as exc:
        registrar_ciclo("markdown_dashboard", str(exc), ok=False)

    try:
        generar_pdf(SALIDAS["pdf"], limite=60)
    except Exception as exc:
        registrar_ciclo("pdf", str(exc), ok=False)

    registrar_ciclo("fin", "Modo automático finalizado")
    for nombre, ruta in SALIDAS.items():
        print(f"{nombre}: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
