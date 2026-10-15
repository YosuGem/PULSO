"""Noosfera CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich import print as rprint

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from noosfera_project.ingesta.canales import FEED_URLS, EMERGENTE_KEYWORDS  # noqa: E402
from noosfera_project.servicios.persistencia import crear_base, guardar_evento, obtener_eventos_recientes  # noqa: E402


@click.group()
def cli() -> None:
    """Noosfera - Analisis de eventos emergentes."""


@cli.command()
def init() -> None:
    rprint("[bold green]Inicializando base de datos...[/bold green]")
    ruta = crear_base()
    rprint(f"Base creada en: {ruta}")


@cli.command()
def fuentes() -> None:
    rprint("[bold]Fuentes RSS configuradas:[/bold]")
    for url in FEED_URLS:
        rprint(f"  - {url}")


if __name__ == "__main__":
    cli()
