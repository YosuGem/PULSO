"""CLI de Noósfera."""

from __future__ import annotations

import json

import click

from noosfera_project.servicios.persistencia import crear_base, obtener_eventos_recientes
from noosfera_project.ingesta.rss import ingestar_fuentes
from noosfera_project.servicios.dashboard import generar_dashboard
from noosfera_project.servicios.pdf_dashboard import generar_pdf
from noosfera_project.servicios.markdown_dashboard import generar_markdown
from noosfera_project.procesamiento.analisis import resumir_eventos
from noosfera_project.servicios.comparador_veo import generar_comparativa
from noosfera_project.rutas import rutas_salida


@click.group()
@click.version_option(version="0.2.2-dev", prog_name="pulso")
def cli() -> None:
    """Pulso — toma el pulso a lo que la gente común dice, antes que los medios."""


@cli.command()
def init() -> None:
    """Crea la base de datos."""
    ruta = crear_base()
    click.echo(f"Base lista en: {ruta}")


@cli.command()
def estado() -> None:
    """Muestra resumen del estado del sistema."""
    # Sin base de datos, obtener_eventos_recientes lanzaba
    # "no such table: eventos" con la traza completa. Quien descarga el
    # proyecto y ejecuta 'estado' lo primero veia eso.
    # Se crea la base si falta, igual que hace 'ciclo'.
    crear_base()
    eventos = obtener_eventos_recientes(limite=20)
    resumen = resumir_eventos(eventos)
    click.echo(f"Eventos totales: {resumen['total']}")
    click.echo(f"Alto: {resumen['alto']} | Medio: {resumen['medio']} | Bajo: {resumen['bajo']}")
    if eventos:
        click.echo("Top:")
        for ev in eventos[:5]:
            titulo = ev.get("titulo") or ""
            click.echo(f"- {titulo[:90]}")
    else:
        click.echo("(sin eventos: ejecuta 'cli ciclo' para ingerir datos)")


@cli.command()
def competir() -> None:
    """Genera la comparativa Noósfera vs VEO."""
    resultado = generar_comparativa()
    click.echo(json.dumps(resultado, ensure_ascii=False, indent=2))


@cli.command()
def ciclo() -> None:
    """Ejecuta un ciclo completo: ingesta + dashboards + PDF."""
    # Garantiza que las tablas existen antes de leer o escribir.
    # crear_base() es idempotente (CREATE TABLE IF NOT EXISTS), así que
    # llamarla siempre es seguro y evita el error
    # "sqlite3.OperationalError: no such table: eventos"
    # cuando alguien ejecuta 'ciclo' sin haber hecho 'init' antes.
    crear_base()
    click.echo("Iniciando ciclo Noósfera...")
    resultado = ingestar_fuentes()
    click.echo(f"Fuentes: {resultado['fuentes_procesadas']}")
    click.echo(f"Eventos nuevos: {resultado['eventos_guardados']}")
    if resultado["errores"]:
        click.echo(f"Errores: {len(resultado['errores'])}")

    rutas = rutas_salida()
    generar_dashboard(rutas["dashboard_html"], limite=80)
    generar_markdown(rutas["dashboard_md"], limite=80)
    # El PDF exige que haya al menos un evento. Con la base vacia lanza
    # RuntimeError, asi que se avisa en lugar de dejar la traza completa.
    try:
        generar_pdf(rutas["informe_pdf"], limite=60)
    except RuntimeError as exc:
        click.echo(f"Aviso: no se genero el PDF ({exc}).")
    click.echo("Dashboard, Markdown y PDF actualizados.")
    click.echo(f"  dashboard: {rutas['dashboard_html']}")
    click.echo(f"  informe:   {rutas['informe_pdf']}")


if __name__ == "__main__":
    cli()
