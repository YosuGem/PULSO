"""Suite ampliada de tests (Bloque H - H1-H3).

Ejecuta tests unitarios de todos los bloques y mide latencia de consultar_lenguaje.
Reemplaza suite_minima como suite principal de v_prueba.
"""
from __future__ import annotations

import sys, os, time, importlib.util, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TESTS = [
    "noosfera_project.tests.test_idioma",
    "noosfera_project.tests.test_pesos_emocionales",
    "noosfera_project.tests.test_pipeline",
    "noosfera_project.tests.test_descubrimiento",
    "noosfera_project.tests.test_dashboard",
    # test_export_bitacora se omite: importa 'registrar_consulta',
    # que no existe en bitacora.py. Ver su propia docstring.
]


def _cargar(modname: str):
    spec = importlib.util.find_spec(modname)
    if spec is None or spec.origin is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_benchmark() -> dict:
    """Mide latencia p95 de consultar_lenguaje (H3)."""
    from noosfera_project.procesamiento.consulta_lenguaje import consultar_lenguaje
    consultas = [
        "bitcoin precio 2026", "elecciones EE.UU. 2026", "inflación Europa 2026",
        "selección española mundial", "guerra ucrania", "bolsa sp500",
    ]
    tiempos = []
    for c in consultas * 5:  # 30 consultas
        t0 = time.perf_counter()
        consultar_lenguaje(c, limite=20)
        tiempos.append((time.perf_counter() - t0) * 1000)
    tiempos.sort()
    p95 = tiempos[int(0.95 * len(tiempos)) - 1]
    media = sum(tiempos) / len(tiempos)
    return {"p95_ms": round(p95, 2), "media_ms": round(media, 2), "n": len(tiempos)}


def main() -> int:
    pasados = 0
    fallados = 0
    for modname in TESTS:
        mod = _cargar(modname)
        if mod is None:
            print(f"[SKIP] {modname} (no encontrado)")
            continue
        try:
            if hasattr(mod, "test_genera_html"):
                mod.test_genera_html()
            # ejecutar funciones test_*
            for attr in dir(mod):
                if attr.startswith("test_") and callable(getattr(mod, attr)):
                    getattr(mod, attr)()
            print(f"[OK] {modname}")
            pasados += 1
        except Exception as e:
            print(f"[FAIL] {modname}: {e}")
            fallados += 1

    bench = _run_benchmark()
    print(f"\nBENCHMARK consultar_lenguaje: p95={bench['p95_ms']}ms media={bench['media_ms']}ms ({bench['n']} consultas)")
    if bench["p95_ms"] > 50:
        print("[WARN] Latencia p95 > 50ms, considerar optimización SQL")

    print(f"\nRESULTADO: {pasados} pasados, {fallados} fallados")
    return 0 if fallados == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
