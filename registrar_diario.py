"""
Registro diario del histórico (0.2.2-dev).

Para qué sirve
--------------
La prueba de 7 días necesita un snapshot por día: sin serie temporal no hay
nada que validar. Este script ejecuta el pipeline sobre el corpus y guarda el
snapshot diario en `analisis_historico`. Idempotente: ejecutarlo dos veces el
mismo día no duplica (guarda por fecha).

Está pensado para correr con un cronjob diario:
    pulso-registrar   (o)   py registrar_diario.py

Ciclo de validación que habilita:
    Día 1: registrar → Día 2: registrar + comparar con Día 1 → ...
    Día 7: el radar 1/3/7d ya tiene contra qué comparar.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permitir ejecutar tanto como módulo como script suelto.
# El script vive en la raíz del repo; noosfera_project es un subdirectorio
# de esa misma raíz, así que basta con añadir la carpeta del script.
_raiz = Path(__file__).resolve().parent
if str(_raiz) not in sys.path:
    sys.path.insert(0, str(_raiz))


def main() -> int:
    from noosfera_project.deteccion.pipeline import ejecutar_pipeline
    from noosfera_project.servicios.historico_analisis import guardar_snapshot, resumen
    from noosfera_project.servicios.persistencia import obtener_textos_recientes

    docs = obtener_textos_recientes(limite=2000)
    out = ejecutar_pipeline(docs, guardar_historico=True)
    n = guardar_snapshot(out["hipotesis"])
    r = resumen()
    print(f"Pipeline: {out['total_hipotesis']} hipótesis sobre {out['total_textos']} textos")
    print(f"Snapshot guardado: {n} categorías")
    print(f"Histórico: {r['registros']} registros, {r['categorias']} categorías, {r['dias_medidos']} días medidos")
    if r["dias_medidos"] >= 2:
        print("Ya hay serie temporal: el radar 1/3/7d puede comparar.")
    else:
        print("Primer día registrado. Mañana empezará la comparación.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
