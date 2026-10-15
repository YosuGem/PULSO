"""Orquestador del pipeline de detección (Bloque C - Fase 5).

Senal -> Agrupacion -> Hipotesis -> Confianza
"""
from __future__ import annotations

from typing import Any

from noosfera_project.deteccion.senal import extraer_senales
from noosfera_project.deteccion.agrupacion import agrupar
from noosfera_project.deteccion.hipotesis import generar_hipotesis
from noosfera_project.deteccion.confianza import calcular_confianza
from noosfera_project.deteccion.temas_excluidos import excluir_de_grupos



import logging
def ejecutar_pipeline(
    textos: list[dict[str, Any]],
    umbral_grupo: int = 3,
    guardar_historico: bool = True,
) -> dict[str, Any]:
    """Ejecuta las 4 fases y devuelve el resultado completo.

    Las categorías de `temas_excluidos` se siguen detectando —el clasificador
    las necesita para no inundar "undetected"— pero se retiran antes de
    generar hipótesis: no son señales a presentar, son ruido a descartar.

    Con `guardar_historico=True` (por defecto) deja foto del estado en
    `analisis_historico`, lo que permite calcular tendencias entre
    ejecuciones: sin histórico el sistema solo sabe qué es grande ahora,
    no qué está creciendo.
    """
    senales = extraer_senales(textos)
    grupos = agrupar(senales, umbral_coincidencias=umbral_grupo)

    # Separar lo excluido antes de hipotetizar: se cuenta, no se presenta.
    grupos_analizables = excluir_de_grupos(grupos)
    grupos_excluidos = [g for g in grupos if g not in grupos_analizables]

    hipotesis = generar_hipotesis(grupos_analizables)

    resultados = []
    for h in hipotesis:
        conf = calcular_confianza(h)
        h.update(conf)
        resultados.append(h)

    # Ordenar por confianza desc
    resultados.sort(key=lambda x: x.get("confianza", 0), reverse=True)

    if guardar_historico:
        try:
            from noosfera_project.servicios.historico_analisis import guardar_snapshot

            guardar_snapshot(resultados)
        except Exception as exc:
            logging.warning("deteccion/pipeline.py:55 falló y se silenció: %s", exc)
            # El histórico es una mejora, nunca un bloqueo del análisis.
            pass

    return {
        "total_textos": len(textos),
        "total_senales": len(senales),
        "total_grupos": len(grupos),
        "grupos": grupos,
        "total_hipotesis": len(resultados),
        "hipotesis": resultados,
        # Trazabilidad: qué se descartó y por qué regla
        "excluidos": {
            "categorias": sorted({g["categoria"] for g in grupos_excluidos}),
            "grupos": len(grupos_excluidos),
            "senales": sum(g.get("num_senales", 0) for g in grupos_excluidos),
        },
    }


if __name__ == "__main__":
    import sqlite3, json
    from pathlib import Path
    DB = Path(__file__).resolve().parents[1] / "eventos.db"
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, fuente, texto, idioma FROM lenguaje_colectivo LIMIT 200").fetchall()
    conn.close()
    textos = [dict(r) for r in rows]
    out = ejecutar_pipeline(textos)
    print(json.dumps(out, indent=2, ensure_ascii=False)[:2000])
