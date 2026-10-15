"""Visor chat oscuro para Noósfera."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, Request  # type: ignore
    from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore
except Exception as exc:
    logging.warning("visor_chat:11 fallo y se silencio: %s", exc)
    FastAPI = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
ESTILO = """\
:root{--bg:#050505;--panel:#0b0b0b;--text:#e6e6e6;--muted:#9a9a9a;--accent:#ffd54a;--border:#1c1c1c;}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,Roboto,Ubuntu,sans-serif;line-height:1.6}
header{padding:18px 18px 12px;border-bottom:1px solid var(--border);background:#080808;position:sticky;top:0}
h1{margin:0;font-size:22px;letter-spacing:1px}
.meta{color:var(--muted);font-size:12px;margin-top:4px}
.chat{max-width:900px;margin:0 auto;padding:18px 14px 100px}
.msg{background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:12px 14px;margin:10px 0}
.msg.system{background:#0b0b0b}
.msg.user{background:#0d0d0d}
.role{font-size:11px;color:var(--muted);margin-bottom:4px}
.level{border-radius:999px;padding:2px 8px;font-size:11px;color:#050505}
.level.alto{background:#ffd54a}
.level.medio{background:#7dd3fc}
.level.bajo{background:#9a9a9a}
.input{padding:12px 14px;border-top:1px solid var(--border);background:#080808;position:fixed;bottom:0;left:0;right:0}
form{max-width:900px;margin:0 auto;display:flex;gap:8px}
input[type=text]{flex:1;background:#0f0f0f;color:var(--text);border:1px solid var(--border);border-radius:10px;padding:10px 12px;font-size:14px}
button{background:#111;color:var(--text);border:1px solid var(--border);border-radius:10px;padding:10px 12px;cursor:pointer}
button:hover{background:#1a1a1a}
a{color:#9ecbff;word-break:break-all}
"""


def _nivel(ev: dict[str, Any]) -> str:
    nivel = "bajo"
    try:
        from noosfera_project.procesamiento.scoring import calcular_score
        nivel = calcular_score(ev).nivel
    except Exception as exc:
        logging.warning("visor_chat:46 fallo y se silencio: %s", exc)
        pass
    return nivel


def _punt(ev: dict[str, Any]) -> float:
    punt = 0.0
    try:
        from noosfera_project.procesamiento.scoring import calcular_score
        punt = calcular_score(ev).puntuacion
    except Exception as exc:
        logging.warning("visor_chat:56 fallo y se silencio: %s", exc)
        pass
    return round(punt, 4)


def _crear_app() -> Any:
    if FastAPI is None:
        raise RuntimeError("FastAPI no disponible.")

    app = FastAPI(title="Noósfera Visor Chat")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> str:
        eventos: list[dict[str, Any]] = []
        try:
            from noosfera_project.servicios import obtener_eventos_recientes
            eventos = obtener_eventos_recientes(limite=40)
        except Exception as exc:
            logging.warning("visor_chat:73 fallo y se silencio: %s", exc)
            pass
        items = "\n".join(
            f"""<div class=\"msg system\"><div class=\"role\">evento</div><div>{(e.get('titulo') or 'Sin título')}</div><div class=\"role\">{e.get('publicado') or ''} · nivel={_nivel(e)} · punt={_punt(e)}</div></div>"""
            for e in eventos
        )
        return f"""<!DOCTYPE html>
<html lang=\"es\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>Noósfera chat</title>
<style>{ESTILO}</style>
</head>
<body>
<header><h1>Noósfera</h1><div class=\"meta\">Visor tipo chat — alto contraste</div></header>
<div class=\"chat\" id=\"chat\">{items}</div>
<div class=\"input\"><form><input name=\"q\" placeholder=\"Escribe y pulsa enviar para refrescar\" autocomplete=\"off\" /><button>Enviar</button></form></div>
<script>
function refrescar(){{
  fetch('/api/eventos?limite=40').then(r=>r.json()).then(data=>{{
    const box=document.getElementById('chat');
    box.innerHTML='';
    (data.eventos||[]).forEach(ev=>{{
      const div=document.createElement('div');
      div.className='msg system';
      div.innerHTML='<div class=\"role\">evento</div><div>'+(ev.titulo||'Sin título')+'</div><div class=\"role\">'+(ev.publicado||'')+' · nivel='+(ev.nivel||'bajo')+' · punt='+(ev.puntuacion??0)+'</div>';
      box.appendChild(div);
    }});
  }});
}}
document.querySelector('form').addEventListener('submit',e=>{{
  e.preventDefault();
  refrescar();
}});
refrescar();
</script>
</body>
</html>"""

    @app.get("/api/eventos")
    def api_eventos(limite: int = 40) -> JSONResponse:
        try:
            from noosfera_project.servicios import obtener_eventos_recientes
            from noosfera_project.procesamiento.scoring import calcular_score
            eventos = obtener_eventos_recientes(limite=limite)
            payload = []
            for ev in eventos:
                score = calcular_score(ev)
                payload.append(
                    {
                        "id": ev.get("id"),
                        "titulo": ev.get("titulo"),
                        "publicado": ev.get("publicado"),
                        "fuente": ev.get("fuente"),
                        "puntuacion": score.puntuacion,
                        "nivel": score.nivel,
                    }
                )
            return JSONResponse({"eventos": payload})
        except Exception as exc:
            logging.warning("visor_chat:136 fallo y se silencio: %s", exc)
            return JSONResponse({"eventos": [], "error": str(exc)})

    @app.get("/api/chat")
    def api_chat(mensaje: str = "") -> JSONResponse:
        try:
            from noosfera_project.servicios.consultas import responder_consulta
            data = responder_consulta(mensaje or "")
            return JSONResponse(data)
        except Exception as exc:
            logging.warning("visor_chat:145 fallo y se silencio: %s", exc)
            return JSONResponse({"pregunta": mensaje, "respuesta": f"Error interno: {exc}", "resultados": []})

    return app
