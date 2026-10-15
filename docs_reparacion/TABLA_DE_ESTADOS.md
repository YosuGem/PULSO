# TABLA DE ESTADOS DE PULSO

**Fecha:** 13 de octubre de 2026
**Carpeta:** `<carpeta-del-proyecto>`

48 comprobaciones. Cada una dice si se ejecuto de verdad, si fallo,
si no se pudo comprobar o si espera una decision del autor.

| # | aspecto | estado | evidencia (comando / prueba) |
|---|---|---|---|
| 1 | Compilacion de los 130 modulos | **VERIFICADO** | `python -m compileall` -> 0 fallos |
| 2 | Import de los 6 paquetes | **VERIFICADO** | import real de cada uno |
| 3 | API arranca (uvicorn real) | **VERIFICADO** | servidor levantado, `/health` -> 200 |
| 4 | API: las 4 rutas | **VERIFICADO** | `/health`, `/`, `/api/senales`, `/api/exportar_json` -> 200 |
| 5 | API: metodo incorrecto | **VERIFICADO** | `POST /health` -> 405 |
| 6 | API: ruta inexistente | **VERIFICADO** | `/no-existe` -> 404 |
| 7 | API: parametro no numerico | **VERIFICADO** | `/api/senales?limite=abc` -> 422 |
| 8 | API: autenticacion del servidor principal | **VERIFICADO** | `noosfera.py --server`: sin clave -> **401**, con clave -> 200 |
| 9 | API: autenticacion de `api_minima` | **FALLIDO** | entra **sin clave** (200). No es el servidor de los lanzadores |
| 10 | API: las lecturas no modifican datos | **VERIFICADO** | 1.391 eventos y 717 textos antes y despues |
| 11 | API: detener y rearrancar | **VERIFICADO** | puerto liberado, rearranca |
| 12 | CLI: comandos principales | **VERIFICADO** | `estado`, `ciclo`, `init`, `competir` -> rc=0 |
| 13 | CLI: distingue exito de fallo | **VERIFICADO** | valido rc=0, invalido rc=2 con mensaje claro |
| 14 | CLI: argumentos desconocidos | **VERIFICADO** | rc=2 con `No such command/option` |
| 15 | CLI: sin base de datos | **VERIFICADO** | rc=0, la crea si hace falta |
| 16 | CLI: sin `ml_pesos.json` | **VERIFICADO** | rc=0, sigue en silencio (poco recomendable) |
| 17 | Lanzadores | **VERIFICADO** | `.bat` y `.sh` citan 0 ficheros inexistentes |
| 18 | `iniciar_noosfera.bat` arranca | **VERIFICADO** | servidor arriba en el puerto 8080 |
| 19 | `iniciar_noosfera.sh` | **PARCIAL** | sintaxis bash correcta; no ejecutado en Linux |
| 20 | Recorrido completo sin variables de entorno | **VERIFICADO** | 12/12 pasos en carpeta limpia |
| 21 | Suites con pytest | **VERIFICADO** | **199 passed, 1 skipped** |
| 22 | Suites en forma de script | **VERIFICADO** | 8/9 pasan; `score_suite` falla (rango sin definir) |
| 23 | Bateria funcional | **VERIFICADO** | 9/9 con servidor real y autenticacion |
| 24 | Informe PDF | **VERIFICADO** | `%PDF` valido, 2 paginas |
| 25 | Informe Markdown | **FALLIDO** | no se genera; el comando dice que si |
| 26 | Informes no acumulan ficheros | **VERIFICADO** | sobrescribe |
| 27 | Clasificacion tematica | **VERIFICADO** | 9/10 casos correctos |
| 28 | Clasificacion con negacion | **FALLIDO** | «no hay crisis» cuenta «crisis» |
| 29 | Clasificacion con sentido figurado | **FALLIDO** | «crisis de identidad` -> orden publico |
| 30 | Deteccion de senales | **VERIFICADO** | detecta crisis real, ignora texto neutro |
| 31 | Deteccion de idioma (3 versiones) | **FALLIDO** | 2/5, 2/5 y 3/5 aciertos |
| 32 | Scoring | **FALLIDO** | los 1.391 eventos caen en «bajo» (max 0,1675) |
| 33 | `guardar_evento` no deduplica | **FALLIDO** | el mismo evento 3 veces -> 3 filas |
| 34 | `NOOSFERA_HOME` no redirige datos | **FALLIDO** | `persistencia` usa la ruta del paquete |
| 35 | Base bloqueada | **PARCIAL** | no revienta, pero tampoco avisa |
| 36 | JSON de pesos corrupto | **PARCIAL** | no revienta, sigue en silencio |
| 37 | Base de datos publicada | **VERIFICADO** | SHA-256 identico al original, integrity ok |
| 38 | Instalacion desde cero | **NO VERIFICADO** | no hay maquina vacia |
| 39 | Linux y macOS | **NO VERIFICADO** | solo inspeccion del codigo |
| 40 | `crontab` / planificador | **NO VERIFICADO** | el modulo no esta instalado |
| 41 | Rango y pesos del scoring | **PENDIENTE DEL AUTOR** | falta `categorias` o bajar umbrales |
| 42 | Puntuaciones historicas | **PENDIENTE DEL AUTOR** | difieren de la formula actual |
| 43 | Deteccion de idioma: cual se queda | **PENDIENTE DEL AUTOR** | 3 implementaciones |
| 44 | Licencia | **PENDIENTE DEL AUTOR** | el fichero dice Apache-2.0, no confirmado |
| 45 | Unificar los dos servidores | **PENDIENTE DEL AUTOR** | uno valida clave, el otro no |
| 46 | El Markdown debe existir | **PENDIENTE DEL AUTOR** | decidir si se escribe o se quita el mensaje |
| 47 | Los 14 `except` silenciosos | **PENDIENTE DEL AUTOR** | valores por defecto que parecen reales |
| 48 | Duplicados en `eventos` | **PENDIENTE DEL AUTOR** | anadir UNIQUE cambia el comportamiento |

---

## Como leer esta tabla

- **VERIFICADO**: se ejecuto y el resultado es el dicho.
- **PARCIAL**: se comprobo algo, pero no todo lo que implicaria.
- **FALLIDO**: se ejecuto y el comportamiento no es el correcto.
- **NO VERIFICADO**: no hay entorno para comprobarlo.
- **PENDIENTE DEL AUTOR**: corregirlo exige decidir, no arreglar.
