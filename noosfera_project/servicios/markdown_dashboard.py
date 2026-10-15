"""Generación de informe Markdown en modo oscuro."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from noosfera_project.servicios.persistencia import obtener_eventos_recientes
from noosfera_project.procesamiento.analisis import resumir_eventos
from noosfera_project.servicios.tema import css_tema, conmutar_tema_js

# Tema compartido (oscuro por defecto, claro seleccionable, minimo 18px).
# Las clases propias de este informe se ajustan al mismo minimo.
ESTILO = """
<style>
""" + css_tema() + """
import logging
  html,body{background:#050505;color:#ececec;font-family:Segoe UI,Roboto,Ubuntu,sans-serif;line-height:1.6;}
header{border-bottom:1px solid var(--border);padding:18px 12px;background:#080808;}
h1{margin:0;font-size:26px;letter-spacing:1px;}
.meta{color:var(--muted);font-size:18px;margin-top:4px;}
section{padding:14px 12px 20px;max-width:1100px;margin:0 auto;}
article{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:14px 16px;margin:10px 0;}
.titulo{font-size:18px;font-weight:700;}
.titulo a{color:var(--text);text-decoration:none;}
.titulo a:hover{color:var(--accent);}
.fila{display:flex;flex-wrap:wrap;gap:8px 14px;color:var(--muted);font-size:18px;}
.chip{background:#0f0f0f;border:1px solid #1a1a1a;border-radius:999px;padding:3px 9px;color:#c8c8c8;font-size:18px;}
a{word-break:break-all;}
.resumen{margin-top:6px;font-size:18px;color:#c6c6c6;}
.estadistica{display:inline-block;background:#0b0b0b;border:1px solid #1c1c1c;border-radius:12px;padding:10px 12px;margin:6px 6px 0 0;min-width:110px;color:#cfcfcf;font-size:18px;}
.estadistica b{display:block;font-size:20px;color:#ffd54a;}
.predicciones{padding:14px 12px 20px;max-width:1100px;margin:0 auto;}
.prediccion-item{background:#0b0b0b;border:1px solid #1c1c1c;border-radius:10px;padding:8px 12px;margin:6px 0;color:#cfcfcf;font-size:18px;}
</style>
"""


def _tarjeta(ev: dict) -> str:
    titulo = (ev.get("titulo") or "Sin título").replace("<", "&lt;")
    enlace = (ev.get("enlace") or "#").strip()
    fuente = (ev.get("fuente") or "").replace("<", "&lt;")
    publicado = ev.get("publicado") or ""
    categorias = (ev.get("categorias") or "").replace("<", "&lt;")
    chips = "".join(f'<span class="chip">{c}</span>' for c in categorias.split(",") if c)
    return f"""\
<article>
  <p class="titulo"><a href="{enlace}" target="_blank" rel="noopener">{titulo}</a></p>
  <div class="fila">
    <span class="chip">{fuente}</span>
    <span class="chip">{publicado}</span>
    {chips}
  </div>
</article>
"""


def _predicciones(limite: int = 5) -> str:
    try:
        from noosfera_project.servicios.predictor_eventos import predecir_siguientes

        items = predecir_siguientes(limite=limite)
    except Exception as exc:
        logging.warning("markdown_dashboard:62 fallo y se silencio: %s", exc)
        return f"<p class='prediccion-item'>No se pudieron cargar predicciones: {exc}</p>"
    if not items:
        return "<p class='prediccion-item'>Sin predicciones disponibles.</p>"
    lineas = []
    for item in items:
        categoria = item.get("categoria", "")
        ocurrencias = item.get("ocurrencias_previas", item.get("coincidencias", "?"))
        texto = item.get("prediccion", "")
        if categoria:
            texto = f"{categoria} ({ocurrencias} apariciones) — {texto}"
        lineas.append(f"<p class='prediccion-item'>{texto}</p>")
    return "\n".join(lineas)


def generar_markdown(ruta_salida: str | Path, limite: int = 80) -> Path:
    eventos = obtener_eventos_recientes(limite=limite)
    ahora = datetime.utcnow().isoformat()
    try:
        resumen = resumir_eventos(eventos)
    except Exception as exc:
        logging.warning("markdown_dashboard:82 fallo y se silencio: %s", exc)
        resumen = {"total": len(eventos), "alto": 0, "medio": 0, "bajo": 0}

    tarjetas = "\n".join(_tarjeta(ev) for ev in eventos)
    predicciones = _predicciones(limite=5)
    conmutador_js = conmutar_tema_js()

    estad = "\n".join(
        f'<div class="estadistica"><b>{resumen.get(k,0)}</b>{k.capitalize()}</div>'
        for k in ["total", "alto", "medio", "bajo"]
    )

    html = f"""\
<!DOCTYPE html>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Noósfera — informe</title>
{ESTILO}
<header>
  <h1>Noósfera</h1>
  <div class="meta">Actualizado: {ahora} · Modo alto contraste</div>
</header>
<section>
  <div>{estad}</div>
</section>
<section class="predicciones">
  <div class="resumen"><b>Predicciones del sistema</b></div>
  {predicciones}
</section>
<main>
  {tarjetas}
</main>
  <script>{conmutador_js}</script>
"""
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(html, encoding="utf-8")
    return ruta
