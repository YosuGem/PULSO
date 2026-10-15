"""CLI de Noósfera: puntos de entrada principales."""

from __future__ import annotations

import click

from noosfera_project.servicios.persistencia import (
    crear_base,
    obtener_eventos_recientes,
)
from noosfera_project.ingesta.rss import ingestar_fuentes
from noosfera_project.servicios.dashboard import generar_dashboard
from noosfera_project.servicios.pdf_dashboard import generar_pdf


@click.group()
def cli() -> None:
    """Noósfera — análisis de eventos emergentes."""


@cli.command()
def init() -> None:
    """Inicializa la base de datos."""
    ruta = crear_base()
    click.echo(f"Base inicializada en: {ruta}")


@cli.command()
def status() -> None:
    """Muestra eventos recientes."""
    eventos = obtener_eventos_recientes(limite=20)
    click.echo(f"Eventos recientes: {len(eventos)}")
    for ev in eventos[:10]:
        titulo = ev.get("titulo") or ""
        fuente = ev.get("fuente") or ""
        punt = ev.get("puntuacion") or 0
        click.echo(f"- [{fuente}] {titulo[:90]} | punt={punt}")


@cli.command()
def ciclo() -> None:
    """Ejecuta un ciclo completo: ingesta, dashboard y PDF."""
    click.echo("Iniciando ciclo Noósfera...")
    resultado = ingestar_fuentes()
    click.echo(f"Fuentes procesadas: {resultado['fuentes_procesadas']}")
    click.echo(f"Eventos guardados: {resultado['eventos_guardados']}")
    if resultado["errores"]:
        click.echo(f"Errores: {len(resultado['errores'])}")
    ruta_html = generar_dashboard("dashboard/index.html")
    click.echo(f"Dashboard HTML: {ruta_html}")
    try:
        ruta_pdf = generar_pdf("informes/ultimo.pdf")
        click.echo(f"PDF: {ruta_pdf}")
    except Exception as exc:
        click.echo(f"PDF omitido: {exc}")


if __name__ == "__main__":
    cli()
