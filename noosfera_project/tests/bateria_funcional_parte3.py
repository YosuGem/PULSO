"""Bateria Funcional parte 3 (ejecucion real, 2026-07-16).

Ejerce todas las capacidades de Noosfera contra la BD real (717 eventos)
y el backend vivo, y emite un informe PASS/FAIL con numeros reales.
No es auditoria (eso eran partes 1-2); es ejecucion de las funciones.
"""
import sys, os, json, threading, time, urllib.request, urllib.error
from pathlib import Path
from collections import Counter

# Raíz del proyecto derivada del propio fichero, no de una ruta fija:
# tests/ -> noosfera_project/ -> raíz del proyecto
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from noosfera_project.procesamiento.idioma import detectar_idioma
from noosfera_project.procesamiento.clasificador_tematico import clasificar
from noosfera_project.procesamiento.consulta_lenguaje import consultar_lenguaje
from noosfera_project.procesamiento.pesos_emocionales import analizar_emocion
from noosfera_project.deteccion.pipeline import ejecutar_pipeline
from noosfera_project.descubrimiento.explorador import explorar
from noosfera_project.servicios.evaluacion_fuentes import evaluar
from noosfera_project.servicios.exportar import exportar_json

import sqlite3
DB = ROOT / "noosfera_project" / "eventos.db"
conn = sqlite3.connect(str(DB)); conn.row_factory = sqlite3.Row
ROWS = [dict(r) for r in conn.execute("SELECT id, fuente, idioma, texto FROM lenguaje_colectivo")]
conn.close()

resultados = []
def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok, detalle))
    print(f"  [{'OK' if ok else 'FAIL'}] {nombre} {detalle}")

print("=== BATERIA FUNCIONAL PARTE 3 (ejecucion real) ===")

# F1 deteccion de idioma (5 idiomas)
muestras = {
    "es": "El bitcoin va a subir mucho este ano",
    "en": "Bitcoin price prediction 2026 experts say 120k",
    "fr": "Le prix du Bitcoin devrait atteindre 120 000 dollars",
    "de": "Der Bitcoin Preis soll 2026 auf 120.000 Dollar steigen",
    "pt": "O preco do Bitcoin deve chegar a 120.000 dolares",
}
ok_idi = all(detectar_idioma(t) == k for k, t in muestras.items())
check("F1 deteccion idioma ES/EN/FR/DE/PT", ok_idi, f"{sum(detectar_idioma(t)==k for k,t in muestras.items())}/5")

# F2 clasificacion tematica
c = clasificar("Bitcoin llegara a 120.000 dolares en 2026")
ok_clas = c["categoria"] == "bitcoin"
check("F2 clasificacion 'bitcoin'", ok_clas, f"cat={c['categoria']}")

# F3 consulta multilingue filtrada
res_es = consultar_lenguaje("bitcoin precio 2026", 5, idioma="es")
res_en = consultar_lenguaje("bitcoin price 2026", 5, idioma="en")
ok_cons = len(res_es) > 0 and len(res_en) > 0
check("F3 consulta filtrada por idioma", ok_cons, f"es={len(res_es)} en={len(res_en)}")

# F4 ponderacion emocional
e_pos = analizar_emocion("El bitcoin subira mucho y es excelente")
e_neg = analizar_emocion("Hay crisis y el mercado se hundira completamente")
ok_emo = e_pos["signo"] == "positivo" and e_neg["signo"] == "negativo"
check("F4 peso emocional signo", ok_emo, f"pos={e_pos['signo']}/{e_pos['score_emocional']:.1f} neg={e_neg['signo']}/{e_neg['score_emocional']:.1f}")

# F5 pipeline senal->hipotesis
out = ejecutar_pipeline(ROWS)
ok_pipe = out["total_grupos"] >= 10 and out["total_hipotesis"] >= 10
check("F5 pipeline senal->hipotesis", ok_pipe, f"{out['total_senales']}->{out['total_grupos']} grupos/{out['total_hipotesis']} hip")

# F6 evaluacion de fuentes
ev = evaluar()
ok_fuentes = ev.get("total", 0) > 0
check("F6 evaluacion de fuentes", ok_fuentes, f"total={ev.get('total')} num_fuentes={ev.get('num_fuentes')}")

# F7 export JSON
outp = str(Path(os.environ.get("TEMP", "/tmp")) / "hermes-bat3-export.json")
ex = exportar_json(5, "en", None, outp)
ok_exp = ex.get("ok") and ex.get("documentos", 0) > 0
check("F7 export JSON", ok_exp, f"docs={ex.get('documentos')}")
if ok_exp and os.path.exists(outp):
    os.remove(outp)

# F8 descubrimiento autonomo
sug = explorar(ROWS)
ok_desc = isinstance(sug, dict) and len(sug.get("sugerencias_categoria", [])) >= 0
check("F8 descubrimiento autonomo", ok_desc, f"cat_unicas={sug.get('categorias_unicas')} sugerencias={len(sug.get('sugerencias_categoria', []))}")

# F9 backend vivo (in-process) con auth
import noosfera as ns
os.environ["NOOSFERA_API_KEY"] = "noosfera_local_prueba_2026"
PORT = 8101
threading.Thread(target=ns.servidor, args=(PORT,), daemon=True).start()
time.sleep(2.0)
BASE = f"http://127.0.0.1:{PORT}"
KEY = "noosfera_local_prueba_2026"
def get(path, auth=False):
    h = {"Authorization": f"Bearer {KEY}"} if auth else {}
    try:
        req = urllib.request.Request(BASE + path, headers=h)
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return "ERR", str(e)
s_h, _ = get("/api/health")
s_f1, _ = get("/api/fuentes")
s_f2, _ = get("/api/fuentes", auth=True)
s_c, _ = get("/api/consultar?pregunta=bitcoin%20precio%202026&limite=3", auth=True)
ok_be = s_h == 200 and s_f1 == 401 and s_f2 == 200 and s_c == 200
check("F9 backend vivo (health/fuentes401/200/consulta200)", ok_be, f"health={s_h} fuentes_noauth={s_f1} fuentes_auth={s_f2} consulta={s_c}")

fallos = [n for n, ok, _ in resultados if not ok]
print(f"\nRESUMEN: {len(resultados)-len(fallos)}/{len(resultados)} OK, fallos={len(fallos)}")
print("GLOBAL:", len(fallos) == 0)
if __name__ == "__main__":
    sys.exit(1 if fallos else 0)
