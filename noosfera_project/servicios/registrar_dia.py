#!/usr/bin/env python3
"""
Mantiene vivo el histórico de análisis (0.2.2-dev).

Para qué sirve
--------------
La persistencia del análisis solo es útil si se ejecuta de forma continua.
Este script hace una cosa: ejecutar el pipeline sobre el corpus y dejar la
foto del día en `analisis_historico`.

Idempotente: ejecutarlo dos veces el mismo día no duplica nada (la clave es
fecha+categoría). Seguro para cron.

Uso:
    py noosfera_project/servicios/registrar_dia.py
    py noosfera_project/servicios/registrar_dia.py --fecha 2026-10-12
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Registra el snapshot diario del análisis.")
    parser.add_argument("--fecha", help="Fecha ISO (YYYY-MM-DD). Por defecto, hoy.")
    parser.add_argument("--limite", type=int, default=2000, help="Docs a analizar.")
    args = parser.parse_args()

    from noosfera_project.deteccion.pipeline import ejecutar_pipeline
    from noosfera_project.servicios.historico_analisis import (
        guardar_snapshot,
        resumen,
        tendencias,
    )
    from noosfera_project.servicios.persistencia import obtener_textos_recientes

    docs = obtener_textos_recientes(limite=args.limite)
    if not docs:
        print("Sin documentos que analizar.")
        return 1

    salida = ejecutar_pipeline(docs, guardar_historico=False)

    # Guardar con la fecha indicada (o la de hoy, dentro de guardar_snapshot)
    if args.fecha:
        escritas = guardar_snapshot(salida["hipotesis"], fecha=args.fecha)
    else:
        escritas = guardar_snapshot(salida["hipotesis"])

    print(f"Documentos analizados: {salida['total_textos']}")
    print(f"Hipótesis: {salida['total_hipotesis']}")
    print(f"Excluidos: {salida['excluidos']['categorias']} ({salida['excluidos']['senales']} señales)")
    print(f"Registros guardados: {escritas}")

    estado = resumen()
    print(f"Histórico: {estado['registros']} registros, "
          f"{estado['categorias']} categorías, "
          f"{estado['dias_medidos']} días medidos")

    tend = tendencias()
    if tend:
        print("\nTendencias:")
        for t in tend[:5]:
            print(f"  {t['categoria']:24} {t['direccion']:6} "
                  f"docs {t['delta_docs']:+d}  conf {t['delta_confianza']:+.3f}")
    else:
        print("\nSin tendencias todavía (se necesitan al menos 2 días).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
