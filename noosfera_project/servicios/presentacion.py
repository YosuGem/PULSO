"""
Presentación accionable de las salidas de PULSO (0.2.2-dev).

Para qué sirve
--------------
Los scores crudos (0.73, 14 apariciones) no dicen a un humano NO técnico
qué hacer. Este módulo traduce los números a significado y acción:

  1. **Semáforo textual** — CRÍTICO / VIGILAR / RUIDO con palabra + icono +
     color. NUNCA solo color (accesibilidad: daltonismo). El usuario con
     problemas oculares lee el icono o la palabra, no depende del tono.
  2. **Resumen en una línea** — conclusión primero, datos después. Orden de
     lectura inverso al de un analista.
  3. **Resumen accionable en texto plano** — copiar y pegar en cualquier
     chat o correo. Es el caso de uso real de "gente común".
  4. **Delta vs ayer** — "▲ +9 vs ayer". El cerebro lee cambios, no valores.

Un único generador (`resumen_accionable`) es la fuente de verdad: lo consumen
el dashboard HTML, el markdown y el .txt para que no se desincronicen.

Diseño: stdlib puro. Sin tocar el pipeline. Respeta el sistema de accesibilidad
ya conseguido (alto contraste, fuentes grandes, símbolos además de color).
Fuente: subagente diseñador de producto/UX.
"""

from __future__ import annotations

from typing import Any, Sequence


# ── 1. Semáforo textual ───────────────────────────────────────────────────
# Nunca solo color: cada nivel lleva palabra + icono. El icono Unicode es
# redundante al color para que un daltónico o alguien en alto contraste no
# pierda la información.
_NIVELES = {
    "critico": {"icono": "🔴", "palabra": "CRÍTICO", "accion": "actuar hoy"},
    "vigilar": {"icono": "🟡", "palabra": "VIGILAR", "accion": "revisar en 24h"},
    "ruido": {"icono": "🟢", "palabra": "RUIDO", "accion": "sin acción"},
}


def semaforo(score: float, umbral_critico: float = 0.7, umbral_vigilar: float = 0.4) -> dict[str, str]:
    """Traduce un score 0-1 a un nivel accionable con palabra + icono.

    Devuelve {nivel, icono, palabra, accion, etiqueta}. La `etiqueta` es la
    forma compacta lista para mostrar: "🔴 CRÍTICO — actuar hoy".
    """
    if score >= umbral_critico:
        nivel = "critico"
    elif score >= umbral_vigilar:
        nivel = "vigilar"
    else:
        nivel = "ruido"
    info = _NIVELES[nivel]
    return {
        "nivel": nivel,
        "icono": info["icono"],
        "palabra": info["palabra"],
        "accion": info["accion"],
        "etiqueta": f"{info['icono']} {info['palabra']} — {info['accion']}",
    }


# ── 4. Delta vs ayer ──────────────────────────────────────────────────────
def delta(hoy: float, ayer: float | None) -> str:
    """'▲ +9 vs ayer' / '▼ -3 vs ayer' / '= igual' / '— sin referencia'.

    La flecha es el símbolo redundante al color (accesibilidad).
    """
    if ayer is None:
        return "— sin referencia"
    d = hoy - ayer
    if d > 0:
        return f"▲ +{_fmt(d)} vs ayer"
    if d < 0:
        return f"▼ {_fmt(d)} vs ayer"
    return "= igual"


def _fmt(n: float) -> str:
    """Formatea un número sin decimales innecesarios."""
    if isinstance(n, float) and not n.is_integer():
        return f"{n:.1f}"
    return str(int(n))


# ── 2 + 5. Resumen accionable en texto plano ──────────────────────────────
def resumen_accionable(
    hipotesis: Sequence[dict[str, Any]],
    top: int = 10,
) -> str:
    """Texto plano con las secciones ACTÚA HOY / VIGILA / RUIDO.

    Es la fuente de verdad para las tres vistas (HTML, markdown, .txt). Un
    humano lo copia y pega en un chat. Sin datos nuevos: solo reordena y
    traduce lo que el pipeline ya produce.
    """
    if not hipotesis:
        return "PULSO — sin señales que informar hoy.\n"

    # Clasificar cada hipótesis por su confianza
    actua: list[str] = []
    vigila: list[str] = []
    ruido: list[str] = []
    for h in hipotesis:
        cat = h.get("categoria", "?")
        conf = float(h.get("confianza", 0.0) or 0.0)
        n = h.get("num_senales") or h.get("documentos") or h.get("total_documentos") or 0
        etiqueta = semaforo(conf)["etiqueta"]
        linea = f"  {etiqueta}  {cat} (confianza {conf:.2f}, {n} señales)"
        if conf >= 0.7:
            actua.append(linea)
        elif conf >= 0.4:
            vigila.append(linea)
        else:
            ruido.append(linea)

    salida = ["PULSO — qué vigilar hoy", ""]

    salida.append("ACTÚA HOY")
    salida.extend(actua[:top] or ["  (nada crítico)"])
    salida.append("")

    salida.append("VIGILA ESTA SEMANA")
    salida.extend(vigila[:top] or ["  (nada en vigilancia)"])
    salida.append("")

    if ruido:
        salida.append("RUIDO (sin acción)")
        salida.extend(ruido[:top])
        salida.append("")

    return "\n".join(salida)


def frase_llana(categoria: str, confianza: float, documentos: int = 0) -> str:
    """Una línea en lenguaje llano sobre un veredicto.

    Conclusión primero: 'Podría pasar: X. Llevamos N conversaciones viéndolo.'
    """
    if documentos and documentos > 1:
        return f"Podría pasar: {categoria}. Llevamos {documentos} conversaciones distintas viéndolo."
    return f"Podría pasar: {categoria} (señal temprana, confianza {confianza:.0%})."


if __name__ == "__main__":
    # Demostración
    demo = [
        {"categoria": "politica_gobierno", "confianza": 0.82, "documentos": 132},
        {"categoria": "ciberseguridad", "confianza": 0.57, "documentos": 45},
        {"categoria": "vivienda", "confianza": 0.31, "documentos": 12},
    ]
    print(resumen_accionable(demo))
    print("SEMÁFORO:")
    for s in (0.85, 0.55, 0.2):
        print(f"  score {s} -> {semaforo(s)['etiqueta']}")
    print("DELTA:")
    print(f"  {delta(14, 5)} | {delta(3, 10)} | {delta(7, 7)} | {delta(5, None)}")
