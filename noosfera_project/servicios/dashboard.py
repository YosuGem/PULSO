"""Noósfera: dashboard HTML oscuro de alto contraste."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from noosfera_project.servicios.persistencia import obtener_eventos_recientes
from noosfera_project.servicios.predictor_eventos import predecir_siguientes
from noosfera_project.servicios.tema import css_tema, conmutar_tema_js, MIN_FUENTE_PX

BASE_DIR = Path(__file__).resolve().parents[1]

import logging
TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Noósfera — eventos emergentes</title>
<style>
{tema_css}
  :root{--panel:#0b0b0b;--border:#3a3a3a}
  html,body{background:#000;color:#fff}
  /* Accesibilidad: refuerzo de contraste y tamaño bajo preferencia del SO */
  @media (prefers-contrast: more){
    :root{--muted:#ffffff;--border:#5a5a5a;--panel:#000;--text:#ffffff}
    body{font-size:1.05rem}
    .card,.chip,.predicciones{border-width:3px}
    a{text-decoration:underline}
  }
  @media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none!important}}
  a:focus,button:focus,[tabindex]:focus{outline:3px solid var(--focus);outline-offset:2px}
  header{padding:32px 28px 16px;border-bottom:2px solid var(--border);background:linear-gradient(180deg,#0a0a0a,#030303)}
  h1{margin:0;font-size:40px;letter-spacing:1px}
  h2{font-size:24px}
  .meta{color:var(--muted);margin-top:8px;font-size:18px}
  main{padding:24px 28px 80px;max-width:1200px;margin:0 auto}
  .card{background:var(--panel);border:2px solid var(--border);border-radius:14px;padding:20px 20px 16px;margin:16px 0}
  .title{font-size:22px;font-weight:700;margin:0 0 8px}
  .title a{color:var(--text);text-decoration:underline}
  .title a:hover{color:var(--accent)}
  .row{display:flex;flex-wrap:wrap;gap:10px 18px;color:var(--muted);font-size:18px}
  .chip{background:#141414;border:2px solid #2a2a2a;border-radius:999px;padding:6px 12px;color:#e0e0e0;font-size:18px}
  .link{color:#9ecbff;font-size:18px;word-break:break-all}
  .footer{margin-top:40px;color:#aaaaaa;font-size:18px;text-align:center}
  .predicciones{padding:20px;margin:20px 0;border-radius:14px;border:2px solid #3a3a3a;background:#0c0c0c}
  .predicciones h2{margin:0 0 12px;font-size:24px;color:#ffd54a}
  .pred{font-size:18px;margin:8px 0}
  a{word-break:break-all}
.vacio{padding:16px;margin:12px;border:1px solid var(--border,#3a3a3a);border-radius:8px;color:var(--muted,#dcdcdc);font-size:1.05rem}
    </style>
</head>
<body>
  <header role="banner">
    <h1>Noósfera</h1>
    <div class="meta">Actualizado: {actualizado} · Vista: alto contraste</div>
  </header>
  <main role="main">
    <section class="predicciones" aria-label="Predicciones del sistema">
      <h2>Predicciones del sistema</h2>
      {predicciones}
    </section>
    <section aria-label="Eventos emergentes">
      {filas}
    </section>
  </main>
  <div class="footer">Generado localmente</div>
  <script>{conmutador_js}</script>
</body>
</html>
"""


def _tarjeta(ev: dict) -> str:
    titulo = (ev.get("titulo") or "Sin título").replace("<", "&lt;")
    enlace = (ev.get("enlace") or "#").strip()
    fuente = (ev.get("fuente") or "").replace("<", "&lt;")
    publicado = ev.get("publicado") or ""
    categorias = (ev.get("categorias") or "").replace("<", "&lt;")
    categorias_html = "".join(f'<span class="chip">{c}</span>' for c in categorias.split(",") if c)
    return f"""<article class="card">
      <p class="title"><a href="{enlace}" target="_blank" rel="noopener">{titulo}</a></p>
      <div class="row">
        <span class="chip">{fuente}</span>
        <span class="chip">{publicado}</span>
        {categorias_html}
      </div>
      <div class="row" style="margin-top:8px"><a class="link" href="{enlace}" target="_blank" rel="noopener">{enlace}</a></div>
    </article>"""


def _predicciones(limite_predicciones: int = 5) -> str:
    try:
        # La funcion se llama 'predecir_siguientes'. Antes se importaba
        # 'predecir_desde_lenguaje_colectivo', que no existe en este modulo:
        # fallaba siempre y el dashboard mostraba la traza completa, con la
        # ruta del equipo incluida.
        from noosfera_project.servicios.predictor_eventos import (
            predecir_siguientes,
        )
        items = predecir_siguientes(limite=limite_predicciones)
    except Exception as exc:
        # No se muestra el error al usuario: puede contener rutas del sistema
        # y no aporta nada. Se registra para quien mantenga el programa.
        logging.warning("dashboard: no se pudieron cargar predicciones: %s",
                        exc)
        return "<p>Sin predicciones disponibles.</p>"

    if not items:
        return "<p>Sin predicciones disponibles.</p>"

    lineas = []
    for item in items:
        categoria = item.get("categoria", "")
        ocurrencias = item.get("ocurrencias_previas", "?")
        texto = item.get("prediccion", "")
        if categoria:
            texto = f"{categoria} ({ocurrencias} apariciones) — {texto}"
        lineas.append(f"<p class=\"pred\">{texto}</p>")
    return "\n".join(lineas)


def generar_dashboard(ruta_salida: str | Path, limite: int = 80, limite_predicciones: int = 5) -> Path:
    eventos = obtener_eventos_recientes(limite=limite)
    ahora = datetime.utcnow().isoformat()
    # Si la base está vacía el dashboard salía sin ninguna indicación de
    # que no hubiera datos: parecía un informe normal sin contenido. Con
    # este aviso se distingue "no hay eventos" de "el informe falló".
    # No cambia ningún dato ni ninguna puntuación: solo añade un mensaje.
    if not eventos:
        filas = ('<p class="vacio">No hay eventos en la base de datos. '
                 'Ejecuta <code>cli ciclo</code> para ingerir datos.</p>')
    else:
        filas = "\n    ".join(_tarjeta(ev) for ev in eventos)
    predicciones = _predicciones(limite_predicciones=limite_predicciones)
    try:
        from noosfera_project.servicios.evaluacion_fuentes import evaluar
        ev = evaluar()
        fuentes_html = (
            f'<section class="predicciones" aria-label="Evaluación de fuentes">'
            f'<h2>Evaluación de fuentes</h2>'
            f'<p class="pred">Total documentos: {ev.get("total", 0)}</p>'
            f'<p class="pred">Fuentes únicas: {ev.get("num_fuentes", 0)}</p>'
            f'<p class="pred">Independencia: {ev.get("independencia", 0)}</p>'
            f'<p class="pred">Gini distribución: {ev.get("gini", 0)}</p>'
            f'<p class="pred">Reputación (docs útiles): {ev.get("reputacion_docs_utiles", 0)}</p>'
            f'<p class="pred">Persistencia temporal: {ev.get("persistencia_temporal", 0)}</p>'
            f'</section>'
        )
    except Exception as exc:
        logging.warning("dashboard:131 fallo y se silencio: %s", exc)
        fuentes_html = f'<section class="predicciones"><h2>Evaluación de fuentes</h2><p class="pred">No disponible: {exc}</p></section>'
    html = TEMPLATE
    html = html.replace("{tema_css}", css_tema())
    html = html.replace("{conmutador_js}", conmutar_tema_js())
    html = html.replace("{actualizado}", ahora).replace("{filas}", filas).replace("{predicciones}", predicciones)
    html = html.replace("</main>", fuentes_html + "</main>")
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(html, encoding="utf-8")
    return ruta
