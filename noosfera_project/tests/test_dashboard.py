"""Tests de accesibilidad del dashboard (Bloque F - F6)."""
from __future__ import annotations
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from noosfera_project.servicios.dashboard import generar_dashboard
from noosfera_project.servicios.tema import MIN_FUENTE_PX
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "dashboard_test.html"

# Selectores que llevan texto al usuario y deben respetar el minimo.
SELECTORES_TEXTO = ["html", "body", ".meta", ".row", ".chip", ".link", ".pred", ".footer"]


def _font_size_de(html: str, selector: str) -> int | None:
    """Devuelve el font-size en px declarado para `selector`, o None."""
    # Acepta "html{font-size:18px}" y "html {font-size: 18px}"
    m = re.search(
        rf"{re.escape(selector)}\s*\{{[^}}]*font-size\s*:\s*(\d+)px",
        html,
    )
    return int(m.group(1)) if m else None


def test_genera_html():
    ruta = generar_dashboard(OUT, limite=10)
    assert ruta.exists()
    html = ruta.read_text(encoding="utf-8")
    # WCAG: lang presente
    assert 'lang="es"' in html
    # Alto contraste: texto blanco sobre negro
    assert "--text:#ffffff" in html or "--text: #ffffff" in html
    # Fuente base >= 18px en el selector html
    base = _font_size_de(html, "html")
    assert base is not None, "no se declara font-size para html"
    assert base >= MIN_FUENTE_PX, f"fuente base {base}px < minimo {MIN_FUENTE_PX}px"
    # ARIA roles
    assert 'role="banner"' in html
    assert 'role="main"' in html
    assert 'aria-label=' in html
    # Foco visible
    assert "outline:3px solid" in html or "outline: 3px solid" in html
    # Conmutador de tema claro/oscuro presente (oscuro por defecto)
    assert "Cambiar tema" in html
    print(f"dashboard: HTML con ARIA + alto contraste + fuente {base}px + conmutador de tema")
    return True


def test_fuentes_minimas_en_selectores():
    """Ningun selector de texto al usuario puede bajar del minimo."""
    ruta = generar_dashboard(OUT, limite=10)
    html = ruta.read_text(encoding="utf-8")
    pequenas = []
    for sel in SELECTORES_TEXTO:
        px = _font_size_de(html, sel)
        if px is not None and px < MIN_FUENTE_PX:
            pequenas.append(f"{sel}={px}px")
    assert not pequenas, f"selectores por debajo de {MIN_FUENTE_PX}px: {pequenas}"
    print(f"accesibilidad: todos los selectores de texto >= {MIN_FUENTE_PX}px")
    return True


if __name__ == "__main__":
    ok = test_genera_html()
    ok &= test_fuentes_minimas_en_selectores()
    if OUT.exists():
        OUT.unlink()
    sys.exit(0 if ok else 1)
