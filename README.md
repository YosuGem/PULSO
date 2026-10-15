# PULSO (castellano)

**Instrumento local de detección y medición de temas emergentes en el discurso colectivo.**

> **Sobre el nombre.** El programa se llama **Pulso**. En el código, los
> ficheros y la base de datos aparece como «Noósfera», que fue el nombre de
> trabajo y quedó incrustado en los identificadores internos
> (`noosfera_project`, `noosfera.py`, `eventos.db`). Este documento usa el
> nombre real del programa.

**Licencia:** Apache License 2.0 — ver [`LICENSE`](LICENSE). La atribución
al autor original, **Yosu Gem**, es obligatoria en copias y obras derivadas
— ver [`NOTICE`](NOTICE).

---

## ⚠️ Estado: proyecto cerrado y publicado tal cual

**Este proyecto no está terminado.** Su autor decidió cerrarlo en el estado
actual y publicarlo para preservarlo y documentarlo.

Estado real, comprobado **por ejecución** el 12 de octubre de 2026 en
Windows 11 con Python 3.14.7:

- ✅ **La API arranca.** Con `uvicorn` real y peticiones HTTP reales,
  **las 4 rutas que existen devuelven 200**. Sin clave, las protegidas
  devuelven `401`.
- ✅ **La línea de comandos funciona**: `--help`, `estado` y `ciclo`.
- ✅ **`cli ciclo` ejecuta el ciclo completo** y genera dashboard HTML y
  **PDF de 2 páginas**. (Dice que también actualiza el Markdown, pero **no
  genera ningún `.md`** — véase `INCIDENCIAS.md` §10.9.)
- ✅ **La batería funcional pasa 9 de 9** con datos reales.
- ✅ **199 tests individuales aprobados** con `pytest`:
  **21 de 22** suites pasan (1 omitida, 0 fallan) y **8 de 9** suites
  en forma de script pasan.
- ⚠️ **No se ha verificado** una instalación en un entorno limpio.
- ⚠️ **No se ha probado** en Linux ni macOS.
- ⚠️ **El sistema de puntuación no tiene un rango definido.** Es una decisión
  de diseño pendiente y **no se ha tocado**. Una suite lo evidencia
  (`score_suite.py`).

**Importante:** para que arrancara hubo que corregir defectos mecánicos del
programa original (tres `sys.exit` a nivel de módulo, imports de módulos
inexistentes, rutas absolutas, un índice SQL sobre una columna que no
existía, y un recorrido de árbol que colgaba el proceso). Están aplicados en
esta copia y documentados en [`INCIDENCIAS.md`](INCIDENCIAS.md).
**Los ficheros del árbol original no se modificaron.**

---

## Qué hace, y qué funciona de verdad

Pulso ingiere texto de fuentes públicas, lo procesa y detecta qué temas
están ganando peso antes de que sea evidente:

```
ingesta ──► procesamiento ──► detección ──► servicios ──► API / informes
  RSS        normaliza         pipeline        persistencia    FastAPI
  foros      clasifica tema    agrupa          SQLite          PDF / MD / JSON
  muestras   mide emoción      señales         evaluación      dashboard
```

Comprobado **ejecutando** cada componente con entradas reales. No todo lo
que hay escrito funciona:

| componente | estado real |
|---|---|
| **Clasificación temática** | ✅ **Funciona.** «bitcoin»→bitcoin, «terremoto»→clima, «Real Madrid»→deportes, «tortilla»→sin tema |
| **Detección de señales** | ✅ **Funciona.** Detecta «protestas masivas… crisis económica»; no detecta nada en «El sol sale por el este» |
| **Carga de datos** | ✅ 1.391 eventos sin un solo error |
| **Línea de comandos** | ✅ `estado`, `ciclo`, `--help` |
| **API** | ✅ 4 rutas, todas responden 200 |
| **Informes** | ⚠️ **Dashboard HTML y PDF de 2 páginas funcionan. El Markdown no**: el comando dice «Markdown actualizado» pero no genera ningún `.md` |
| **Scoring** | ⚠️ **Ejecuta, pero no distingue.** Una crisis y una receta puntúan igual: 0,3325 vs 0,3250 |
| **Detección de idioma** | ⚠️ **Funciona solo con frases largas.** Con textos cortos devuelve «es» sin avisar de que no está segura |

**Por qué falla el scoring:** `ml_pesos.json` no tiene la clave `categorias`,
así que el término que pesa el **45 %** del score vale siempre cero.
Recalculados los 1.391 eventos reales, el score máximo sale **0,1675** cuando
el umbral para el nivel medio es 0,50. **Los 1.391 caen en el nivel más
bajo.**

Está explicado con todos los números en
[`INCIDENCIAS.md`](INCIDENCIAS.md) §8. **No se ha cambiado ninguna fórmula ni
umbral**: es una decisión de su autor.

---

## Plataformas

| plataforma | estado |
|---|---|
| **Windows** | **Verificado por ejecución.** Todo lo documentado se ejecutó en Windows 11 con Python 3.14.7 |
| **Linux** | **Inspeccionado, no ejecutado.** Ver más abajo |
| **macOS** | **Inspeccionado, no ejecutado.** |

### Qué se ha comprobado de Linux, y qué no

**Comprobado leyendo el código** (no ejecutándolo en Linux):

| aspecto | resultado |
|---|---|
| Rutas estilo Windows (`C:\...`) en el código | **0** |
| Rutas escritas a mano en lugar de `pathlib` | **0** |
| Módulos que usan `pathlib` | **48** |
| Dependencias con ruedas para Linux en PyPI | las 8 |
| Lanzador para Linux | **añadido**: `iniciar_noosfera.sh` |

Que el código use `pathlib` y no tenga rutas a mano es una **buena señal**,
pero **no es una prueba** de que funcione en Linux.

**No verificado:** que el programa arranque, que las suites pasen o que la
API responda en Linux o macOS. **No se declara compatibilidad.**

Lo único que cambia entre sistemas es el lanzador: en Windows
`iniciar_noosfera.bat`, en Linux y macOS `./iniciar_noosfera.sh`. El comando
que levanta el servidor es el mismo:

```bash
python noosfera.py --server 8080
```

---

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate

python -m pip install -r requirements.txt
```

Dependencias, con la versión exacta con la que se verificó el arranque:

| paquete | versión | para qué |
|---|---|---|
| `fastapi` | 0.143.0 | API REST |
| `uvicorn` | 0.54.0 | servidor HTTP |
| `click` | 8.5.0 | línea de comandos |
| `rich` | 15.0.0 | salida de consola |
| `feedparser` | 6.0.14 | lectura de RSS |
| `pydantic` | 2.14.1 | validación en la API |
| `reportlab` | 5.0.1 | informes PDF |

> **Usad `python -m pip`, no `pip` a secas.** En el entorno del autor `pip`
> instalaba en otro intérprete que el que ejecutaba `python`. Comprobad con
> `python -c "import reportlab"` después de instalar.

Copia `.env.example` a `.env` si queréis fijar la clave de la API. **La clave
que viene en el código es de prueba local; generad una propia.**

---

## Ejecución

Desde la raíz del proyecto:

```bash
export PYTHONPATH=$PWD                        # Windows: set PYTHONPATH=%CD%
export NOOSFERA_HOME=$PWD                     # Windows: set NOOSFERA_HOME=%CD%
```

### Línea de comandos

```bash
python -m noosfera_project.cli --help      # listado de comandos
python -m noosfera_project.cli estado      # resumen del sistema
python -m noosfera_project.cli ciclo       # ciclo: ingesta + dashboard + informe
```

Salida real de `cli estado` con la base de datos incluida:

```
Eventos totales: 20
Alto: 4 | Medio: 0 | Bajo: 16
```

`cli ciclo` genera los cuatro artefactos. **Dónde los deja depende de la
configuración:**

| si defines `NOOSFERA_HOME` | van ahí |
|---|---|
| si no | van a `~/.noosfera/` (`%USERPROFILE%\.noosfera` en Windows) |

> Si copiaste el proyecto a otra carpeta y no defines `NOOSFERA_HOME`,
> los artefactos aparecen en tu carpeta de usuario, **no** junto al
> código. Defínela para tenerlos en el proyecto:
>
> ```bash
> set NOOSFERA_HOME=%CD%        # Windows
> export NOOSFERA_HOME=$PWD     # Linux/macOS
> ```

Los tres artefactos que se generan son `dashboard/index.html`,
`dashboard/index_dark.html` e `informes/ultimo.pdf`.

> **No se genera ningún Markdown**, aunque el nombre de la variable en el
> código (`dashboard_md`) lo sugiera: apunta a `index_dark.html`, que es
> HTML. Es un defecto de nombre, no un fichero que falte.

### Servidor API

El servidor lo levanta `noosfera.py`, en la raíz del proyecto:

```bash
python noosfera.py --server 8080
```

Rutas que existen (**son `/health` y `/api/…`, no `/api/health`**):

| ruta | qué devuelve | clave |
|---|---|---|
| `/health` | estado del servicio | no |
| `/` | el dashboard en HTML | no |
| `/api/senales?limite=N` | señales emergentes | sí |
| `/api/eventos?limite=N` | eventos recientes | sí |
| `/api/consultar?pregunta=…` | consulta en lenguaje natural | sí |
| `/api/fuentes` | fuentes configuradas | sí |
| `/api/exportar_json?limite=N` | exportación JSON | sí |

> La clave va en la cabecera `Authorization: Bearer <clave>`.
> Las rutas marcadas con «sí» devuelven **401** sin ella.
>
> `servidor_api` y `api_minima` son módulos aparte, en construcción.
> `api_minima` **no comprueba la clave en ninguna ruta**: no lo expongas
> a una red.

> **Nota sobre `/api/senales`:** el parámetro es `horizonte` y está en
> **meses**, no en días (`horizonte=7` son 210 días). No admite `dias`.

#### Las tres líneas de comandos

El proyecto tiene **tres CLIs distintas**. No son equivalentes:

| cómo se invoca | comandos | para qué |
|---|---|---|
| `python -m noosfera_project.cli` | `init`, `estado`, `ciclo`, `competir` | **la principal**, la que usa este README |
| `python -m noosfera_project.servicios.cli_principal` | `init`, `status`, `ciclo` | variante antigua; `status` = `estado` |
| `python noosfera_project/scripts/noosfera_cli.py` | `fuentes` | solo para consultar las fuentes |

> `estado` y `status` son el **mismo comando con distinto nombre**. Si usas
> la CLI principal y escribes `status`, dará error: el comando es `estado`.

Las cuatro devuelven `200`. Verificado con `uvicorn` real y peticiones HTTP
reales.

### Pruebas

```bash
python -m pytest noosfera_project/tests/ -v
```

Resultado real, ejecutado el 14 de octubre de 2026 con `pytest 9.1.1`:

| | |
|---|---|
| **Tests individuales aprobados** | **210** |
| Suites de `pytest` que pasan | **22 de 23** (1 omitida, 0 fallan) |
| Suites que son scripts y pasan | **8 de 9** |
| Suites que fallan | **1**: `score_suite.py` (ver abajo) |

> ✅ **Las pruebas no tocan tu base de datos.** Tres capas de aislamiento
> redirigen `persistencia.DB_PATH` a una base temporal:
>
> 1. `conftest.py` en la raíz del proyecto — cubre cualquier fichero de
>    prueba del árbol.
> 2. `conftest.py` en `noosfera_project/tests/` — respaldo al lanzar solo
>    esa carpeta.
> 3. `aislamiento_plugin.py`, plugin `pytest11` — cubre incluso ficheros
>    de prueba fuera del árbol. Requiere `pip install -e .`.
>
> Comprobado con hash SHA-256 de la base real, que queda idéntico y sin
> WAL pendiente, y con 11 tests que lo verifican solos.

Las cuatro suites que se ejecutan **sin** `pytest` y pasan (aunque ahora se
auto-aíslen a una base temporal):

```bash
python noosfera_project/tests/bateria_funcional_parte3.py   # 9/9, levanta servidor real
python noosfera_project/tests/estructura_suite.py           # comprueba el árbol
python noosfera_project/tests/health_check.py               # salud del sistema
python noosfera_project/tests/integration_smoke.py          # integración
```

La batería funcional levanta un servidor de verdad y comprueba la
autenticación: sin clave da `401`, con clave da `200`.

> **Para ejecutar las suites hay que definir la clave de API**, porque la
> autorización es obligatoria:
> ```bash
> export NOOSFERA_API_KEY=noosfera_local_prueba_2026
> ```
> Sin ella, las rutas protegidas devuelven `401` y las suites fallan.

#### Las dos suites que no pasan, y por qué

**`score_suite.py`** espería que el scoring diera `>= 0.4` para «Crisis y
protestas globales» y `>= 0.1` para «Nada relevante». El scoring real da
**0,07** y **0,055**.

Comprobado: **no es un problema de la fecha**. Con la fecha de hoy los
valores suben a 0,295 y 0,28, pero siguen sin alcanzar el umbral. Es que
**el rango del score no está definido** (véase `SCORING.md`).

**No se ha tocado.** Ni el scoring ni los umbrales de la suite. Es la
decisión de diseño que queda pendiente.

**`test_export_bitacora.py`** importa `registrar_consulta` de
`servicios/bitacora.py`, pero ese módulo solo define `registrar_ciclo`.
La función no existe en el programa. La suite queda **omitida** con
`pytest.skip` y el motivo documentado en su propia cabecera. **No se ha
inventado la función**, porque hacerlo sería definir un comportamiento que
el autor no definió.

### Verificarlo tú mismo

```bash
python verificar_pulso.py
```

Comprueba, ejecutándolo de verdad: que los 130 módulos compilan, las suites
con `pytest`, las suites en forma de script, la CLI, y que la carpeta está
limpia y lista para publicar. **También restaura la base de datos a sus
1.391 eventos**, porque las pruebas escriben en ella al ejecutarse.

Sale con `rc=0` si todo lo comprobable pasa y `rc=1` si encuentra un fallo
real, así que sirve también en un `CI`.

### Comandos de un vistazo

`comandos_rapidos.sh` y `iniciar_noosfera.bat`. Los **11 comandos** del
primero se ejecutaron y funcionaron antes de incluirlos; el segundo levanta
el servidor en el puerto 8080. Ambos comprobados.

> **`PYTHONPATH` no hace falta; `NOOSFERA_HOME` sí conviene ponerla.**
> Comprobado copiando el proyecto a una carpeta limpia: la CLI y las
> suites arrancan sin ninguna variable. **Pero sin `NOOSFERA_HOME` la
> base de datos se busca junto al código**, así que si copiaste el
> proyecto a otro sitio verás solo 20 eventos de ejemplo en lugar de
> los 1391 reales. Defínela para apuntar a tus datos:
>
>     set NOOSFERA_HOME=%CD%        (Windows)
>     export NOOSFERA_HOME=$PWD     (Linux/macOS)
>
> `NOOSFERA_API_KEY` solo es necesaria para las rutas protegidas de la
> API.

---

## Qué contiene

```
PULSO/
├── README.md                  ← este fichero
├── INCIDENCIAS.md             ← defectos del original y cómo se corrigieron
├── SCORING.md                 ← la fórmula real y sus límites
├── requirements.txt
├── requirements-dev.txt
├── LICENSE                    ← Apache-2.0, NO CONFIRMADO
├── .env.example
├── .gitignore
│
├── noosfera.py                ← punto de entrada alternativo
├── auth.py  rate_limit.py  validacion.py
├── run_noosfera.py  registrar_diario.py  migracion_fuentes.py
├── iniciar_noosfera.bat  comandos_rapidos.sh
├── server/health.py
│
├── noosfera_project/          ← el paquete (130 módulos .py)
│   ├── cli.py
│   ├── servicios/             ← API, dashboard, PDF, persistencia
│   ├── procesamiento/         ← scoring, idioma, clasificador
│   ├── deteccion/             ← pipeline, señales, hipótesis
│   ├── ingesta/               ← RSS y fuentes
│   ├── descubrimiento/        ← explorador autónomo
│   ├── tests/                 ← 31 suites
│   └── eventos.db             ← 1.391 eventos de ejemplo
│
├── docs/                      ← documentación del programa
├── dashboard/                 ← dashboard generado
├── informes/                  ← informes generados
├── datos/  dist/  auditorias/  comparativas/  exportaciones/
└── noosfera.log
```

---

## Documentación

| documento | contenido |
|---|---|
| [`INCIDENCIAS.md`](INCIDENCIAS.md) | Los defectos del original, cuáles se corrigieron y cómo |
| [`SCORING.md`](SCORING.md) | La fórmula de puntuación reconstruida del código |
| `docs/` | Manual de usuario, reglas del proyecto, fuentes, categorías |

---

## Advertencia final

- **El programa arranca, pero el scoring no está calibrado.** Es el defecto
  más importante: `ml_pesos.json` no tiene la clave `categorias`, así que el
  término que pesa el **45 %** del score vale siempre cero y **los 1.391
  eventos reales caen todos en el nivel más bajo**. Explicado con datos en
  `INCIDENCIAS.md` §8.2.
- **La detección de idioma depende de la longitud del texto.** Con frases
  largas acierta (la batería funcional da 5/5); con frases cortas devuelve
  «es» sin avisar de que no está segura (§8.4).
- **Las puntuaciones guardadas en la base no coinciden con lo que calcula el
  código actual.** Diferencia media de −0,77 (§8.3). No se han recalculado.
- **El scoring necesita una decisión de diseño** antes de poder usarse en
  serio: no tiene cota superior ni validación de pesos.
- **Hay 14 puntos del código que atrapan excepciones y devuelven un valor por
  defecto** como si fuera un resultado real. Se les añadió `logging.warning`
  para que el fallo quede registrado, pero **el valor devuelto no cambió**.
  Están listados en `INCIDENCIAS.md`.
- **La clave de API del código es de prueba local** y debe sustituirse.
- **No se ha probado una instalación desde cero** ni en Linux ni macOS.
- **Lo que sí funciona bien:** la clasificación temática y la detección de
  señales. Son las partes más sólidas del programa.
- **El valor de lo publicado** está en el instrumento conceptual, en la
  arquitectura y en las lecciones del proceso, no en la pulidez técnica.

---

## Nota personal del autor

Este es mi segundo programa. Se llama **PULSO**. Espero que os resulte útil
y que os animéis a mejorarlo.

He tenido que publicarlo antes de terminar el programa y de completar todo
el proceso de pruebas por limitaciones de tiempo y de recursos. No tengo
ni idea de programación. He hecho lo que he podido con los medios
disponibles a mi alcance. Con más tiempo y recursos probablemente habría
podido llegar muchísimo más lejos.

Durante los próximos meses estaré menos conectado a internet,
especialmente desde el ordenador, por lo que publico ahora el proyecto
para que pueda ser consultado y mejorado por quien quiera.

Sigue pendiente comprobar su comportamiento mediante un periodo prolongado
de funcionamiento real, con ingesta diaria y evaluación de sus resultados.

Pensaba subir este programa en noviembre, pero he podido hacerlo antes. En
noviembre subiré el último que me queda, hecho también con la ayuda de otra
inteligencia artificial. Son tres programas del mismo estilo —SIBILA, PULSO
y el tercero— y cada uno lo ha desarrollado una inteligencia artificial
distinta.

---

# PULSO (English)

**Local instrument for detecting and measuring emerging themes in collective discourse.**

> **About the name.** The program is called **PULSO**. In the code, the
> files and the database it appears as «Noósfera», which was the working
> name and ended up embedded in the internal identifiers
> (`noosfera_project`, `noosfera.py`, `eventos.db`). This document uses the
> program's real name.

**License:** Apache License 2.0 — see [`LICENSE`](LICENSE). Attribution to
the original author, **Yosu Gem**, is required in copies and derivative
works — see [`NOTICE`](NOTICE).

---

## ⚠️ Status: closed project, published as-is

**This project is not finished.** Its author decided to close it in its
current state and publish it to preserve and document it.

Real status, verified **by execution** on 12 October 2026 on Windows 11
with Python 3.14.7:

- ✅ **The API starts up.** With real `uvicorn` and real HTTP requests,
  **the 4 routes that exist all return 200**. Without a key, the protected
  ones return `401`.
- ✅ **The command line works**: `--help`, `estado` and `ciclo`.
- ✅ **`cli ciclo` runs the full cycle** and produces an HTML dashboard and
  a **2-page PDF**. (It claims to update the Markdown too, but it
  **generates no `.md` file at all** — see `INCIDENCIAS.md` §10.9.)
- ✅ **The functional suite passes 9 out of 9** with real data.
- ✅ **210 individual tests pass** with `pytest`:
  **22 of 23** suites pass (1 skipped, 0 failing) and **8 of 9** suites
  in script form pass.
- ⚠️ **A clean-environment installation has not been verified.**
- ⚠️ **It has not been tested** on Linux or macOS.
- ⚠️ **The scoring system has no defined range.** That is a pending design
  decision and **it has not been touched**. One suite exposes the issue
  (`score_suite.py`).

**Important:** mechanical defects of the original program had to be fixed
for it to start at all (three module-level `sys.exit` calls, imports of
nonexistent modules, absolute paths, an SQL index on a column that did not
exist, and a tree walk that hung the process). They are applied in this
copy and documented in [`INCIDENCIAS.md`](INCIDENCIAS.md).
**The files of the original tree were not modified.**

---

## What it does, and what actually works

Pulso ingests text from public sources, processes it and detects which
themes are gaining weight before it becomes obvious:

```
ingesta ──► procesamiento ──► detección ──► servicios ──► API / informes
  RSS        normaliza         pipeline        persistencia    FastAPI
  foros      clasifica tema    agrupa          SQLite          PDF / MD / JSON
  muestras   mide emoción      señales         evaluación      dashboard
```

Verified **by running** each component with real inputs. Not everything
that is written down actually works:

| component | real status |
|---|---|
| **Thematic classification** | ✅ **Works.** «bitcoin»→bitcoin, «terremoto»→clima, «Real Madrid»→deportes, «tortilla»→no theme |
| **Signal detection** | ✅ **Works.** It detects «mass protests… economic crisis»; it detects nothing in «the sun rises in the east» |
| **Data loading** | ✅ 1,391 events without a single error |
| **Command line** | ✅ `estado`, `ciclo`, `--help` |
| **API** | ✅ 4 routes, all respond 200 |
| **Reports** | ⚠️ **The HTML dashboard and the 2-page PDF work. The Markdown does not**: the command says "Markdown updated" but generates no `.md` |
| **Scoring** | ⚠️ **It runs, but it does not discriminate.** A crisis and a recipe score the same: 0.3325 vs 0.3250 |
| **Language detection** | ⚠️ **It only works with long phrases.** With short texts it returns «es» without warning that it is not sure |

**Why the scoring fails:** `ml_pesos.json` lacks the `categorias` key, so
the term that weighs **45 %** of the score is always zero. Recalculated
over the 1,391 real events, the maximum score comes out at **0.1675** when
the threshold for the mid level is 0.50. **All 1,391 fall into the lowest
level.**

It is explained with all the numbers in
[`INCIDENCIAS.md`](INCIDENCIAS.md) §8. **No formula or threshold has been
changed**: that is its author's decision.

---

## Platforms

| platform | status |
|---|---|
| **Windows** | **Verified by execution.** Everything documented here was executed on Windows 11 with Python 3.14.7 |
| **Linux** | **Inspected, not executed.** See below |
| **macOS** | **Inspected, not executed.** |

### What has been checked on Linux, and what has not

**Verified by reading the code** (not by running it on Linux):

| aspect | result |
|---|---|
| Windows-style paths (`C:\...`) in the code | **0** |
| Hand-written paths instead of `pathlib` | **0** |
| Modules that use `pathlib` | **48** |
| Dependencies with wheels for Linux on PyPI | all 8 |
| Launcher for Linux | **added**: `iniciar_noosfera.sh` |

That the code uses `pathlib` and has no hand-written paths is a **good
sign**, but **it is not proof** that it works on Linux.

**Not verified:** that the program starts, that the suites pass, or that
the API responds on Linux or macOS. **No compatibility is declared.**

The only thing that changes between systems is the launcher: on Windows
`iniciar_noosfera.bat`, on Linux and macOS `./iniciar_noosfera.sh`. The
command that starts the server is the same:

```bash
python noosfera.py --server 8080
```

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

python -m pip install -r requirements.txt
```

Dependencies, with the exact version against which the start-up was
verified:

| package | version | what for |
|---|---|---|
| `fastapi` | 0.143.0 | REST API |
| `uvicorn` | 0.54.0 | HTTP server |
| `click` | 8.5.0 | command line |
| `rich` | 15.0.0 | console output |
| `feedparser` | 6.0.14 | RSS reading |
| `pydantic` | 2.14.1 | validation in the API |
| `reportlab` | 5.0.1 | PDF reports |

> **Use `python -m pip`, not bare `pip`.** In the author's environment
> `pip` installed into a different interpreter than the one that ran
> `python`. Check with `python -c "import reportlab"` after installing.

Copy `.env.example` to `.env` if you want to set the API key. **The key
that ships in the code is for local testing; generate your own.**

---

## Running

From the project root:

```bash
export PYTHONPATH=$PWD                        # Windows: set PYTHONPATH=%CD%
export NOOSFERA_HOME=$PWD                     # Windows: set NOOSFERA_HOME=%CD%
```

### Command line

```bash
python -m noosfera_project.cli --help      # list of commands
python -m noosfera_project.cli estado      # system summary
python -m noosfera_project.cli ciclo       # cycle: ingest + dashboard + report
```

Real output of `cli estado` with the included database:

```
Eventos totales: 20
Alto: 4 | Medio: 0 | Bajo: 16
```

`cli ciclo` generates the artifacts. **Where it leaves them depends on the
configuration:**

| if you define `NOOSFERA_HOME` | they go there |
|---|---|
| if you do not | they go to `~/.noosfera/` (`%USERPROFILE%\.noosfera` on Windows) |

> If you copied the project to another folder and do not define
> `NOOSFERA_HOME`, the artifacts appear in your user folder, **not** next
> to the code. Define it to keep them in the project:
>
> ```bash
> set NOOSFERA_HOME=%CD%        # Windows
> export NOOSFERA_HOME=$PWD     # Linux/macOS
> ```

The three artifacts generated are `dashboard/index.html`,
`dashboard/index_dark.html` and `informes/ultimo.pdf`.

> **No Markdown is generated**, even though the name of the variable in the
> code (`dashboard_md`) suggests it: it points to `index_dark.html`, which
> is HTML. It is a naming defect, not a missing file.

### API server

The server is started by `noosfera.py`, in the project root:

```bash
python noosfera.py --server 8080
```

Routes that exist (**they are `/health` and `/api/…`, not `/api/health`**):

| route | what it returns | key |
|---|---|---|
| `/health` | service status | no |
| `/` | the dashboard in HTML | no |
| `/api/senales?limite=N` | emerging signals | yes |
| `/api/eventos?limite=N` | recent events | yes |
| `/api/consultar?pregunta=…` | natural-language query | yes |
| `/api/fuentes` | configured sources | yes |
| `/api/exportar_json?limite=N` | JSON export | yes |

> The key goes in the `Authorization: Bearer ***` header.
> Routes marked «yes» return **401** without it.
>
> `servidor_api` and `api_minima` are separate modules, under
> construction. `api_minima` **does not check the key on any route**: do
> not expose it to a network.

> **Note on `/api/senales`:** the parameter is `horizonte` and it is in
> **months**, not days (`horizonte=7` is 210 days). It does not accept
> `dias`.

#### The three command lines

The project has **three different CLIs**. They are not equivalent:

| how to invoke it | commands | what it is for |
|---|---|---|
| `python -m noosfera_project.cli` | `init`, `estado`, `ciclo`, `competir` | **the main one**, the one this README uses |
| `python -m noosfera_project.servicios.cli_principal` | `init`, `status`, `ciclo` | old variant; `status` = `estado` |
| `python noosfera_project/scripts/noosfera_cli.py` | `fuentes` | only to consult the sources |

> `estado` and `status` are the **same command under a different name**.
> If you use the main CLI and type `status`, it will error: the command is
> `estado`.

All four return `200`. Verified with real `uvicorn` and real HTTP
requests.

### Tests

```bash
python -m pytest noosfera_project/tests/ -v
```

Real result, executed on 14 October 2026 with `pytest 9.1.1`:

| | |
|---|---|
| **Individual tests passed** | **210** |
| `pytest` suites that pass | **22 of 23** (1 skipped, 0 failing) |
| Script-form suites that pass | **8 of 9** |
| Suites that fail | **1**: `score_suite.py` (see below) |

> ✅ **The tests do not touch your database.** Three isolation layers
> redirect `persistencia.DB_PATH` to a temporary database:
>
> 1. `conftest.py` in the project root — covers any test file in the tree.
> 2. `conftest.py` in `noosfera_project/tests/` — fallback when running
>    only that folder.
> 3. `aislamiento_plugin.py`, a `pytest11` plugin — covers even test files
>    outside the tree. Requires `pip install -e .`.
>
> Verified with a SHA-256 hash of the real database, which stays identical
> and with no pending WAL, and with 11 tests that check it on their own.

The four suites that run **without** `pytest` and pass (they now isolate
themselves into a temporary database):

```bash
python noosfera_project/tests/bateria_funcional_parte3.py   # 9/9, starts a real server
python noosfera_project/tests/estructura_suite.py           # checks the tree
python noosfera_project/tests/health_check.py               # system health
python noosfera_project/tests/integration_smoke.py          # integration
```

The functional suite starts a real server and checks the authentication:
without a key it gives `401`, with a key it gives `200`.

> **To run the suites you must set the API key**, because authorization is
> mandatory:
> ```bash
> export NOOSFERA_API_KEY=noosfera_local_prueba_2026
> ```
> Without it, the protected routes return `401` and the suites fail.

#### The two suites that do not pass, and why

**`score_suite.py`** expected the scoring to give `>= 0.4` for «Crisis y
protestas globales» and `>= 0.1` for «Nada relevante». The real scoring
gives **0.07** and **0.055**.

Verified: **it is not a date problem**. With today's date the values rise
to 0.295 and 0.28, but they still fall short of the threshold. It is that
**the range of the score is not defined** (see `SCORING.md`).

**It has not been touched.** Neither the scoring nor the suite's
thresholds. That is the pending design decision.

**`test_export_bitacora.py`** imports `registrar_consulta` from
`servicios/bitacora.py`, but that module only defines `registrar_ciclo`.
The function does not exist in the program. The suite stays **skipped**
with `pytest.skip` and the reason documented in its own header. **The
function has not been invented**, because doing so would define a
behaviour the author never defined.

### Check it yourself

```bash
python verificar_pulso.py
```

It checks, by really running it: that the 130 modules compile, the suites
with `pytest`, the suites in script form, the CLI, and that the folder is
clean and ready to publish. **It also restores the database to its 1,391
events**, because the tests write into it when they run.

It exits with `rc=0` if everything checkable passes and `rc=1` if it finds
a real failure, so it also works in a `CI`.

### Commands at a glance

`comandos_rapidos.sh` and `iniciar_noosfera.bat`. The **11 commands** of
the former were executed and worked before being included; the latter
starts the server on port 8080. Both verified.

> **`PYTHONPATH` is not needed; `NOOSFERA_HOME` is worth setting.**
> Verified by copying the project to a clean folder: the CLI and the suites
> start with no variables at all. **But without `NOOSFERA_HOME` the
> database is looked up next to the code**, so if you copied the project
> elsewhere you will see only 20 example events instead of the 1,391 real
> ones. Define it to point at your data:
>
>     set NOOSFERA_HOME=%CD%        (Windows)
>     export NOOSFERA_HOME=$PWD     (Linux/macOS)
>
> `NOOSFERA_API_KEY` is only needed for the protected routes of the API.

---

## What it contains

```
PULSO/
├── README.md                  ← this file
├── INCIDENCIAS.md             ← defects of the original and how they were fixed
├── SCORING.md                 ← the real formula and its limits
├── requirements.txt
├── requirements-dev.txt
├── LICENSE                    ← Apache-2.0
├── NOTICE                     ← attribution
├── .env.example
├── .gitignore
│
├── noosfera.py                ← alternative entry point
├── auth.py  rate_limit.py  validacion.py
├── run_noosfera.py  registrar_diario.py  migracion_fuentes.py
├── iniciar_noosfera.bat  comandos_rapidos.sh
├── server/health.py
│
├── noosfera_project/          ← the package (130 .py modules)
│   ├── cli.py
│   ├── servicios/             ← API, dashboard, PDF, persistence
│   ├── procesamiento/         ← scoring, language, classifier
│   ├── deteccion/             ← pipeline, signals, hypotheses
│   ├── ingesta/               ← RSS and sources
│   ├── descubrimiento/        ← autonomous explorer
│   ├── tests/                 ← 31 suites
│   └── eventos.db             ← 1,391 example events
│
├── docs/                      ← program documentation
├── dashboard/                 ← generated dashboard
├── informes/                  ← generated reports
├── datos/  dist/  auditorias/  comparativas/  exportaciones/
└── noosfera.log
```

---

## Documentation

| document | content |
|---|---|
| [`INCIDENCIAS.md`](INCIDENCIAS.md) | The defects of the original, which were fixed and how |
| [`SCORING.md`](SCORING.md) | The scoring formula, reconstructed from the code |
| `docs/` | User manual, project rules, sources, categories |

---

## Final warning

- **The program starts, but the scoring is not calibrated.** That is the
  most important defect: `ml_pesos.json` lacks the `categorias` key, so
  the term that weighs **45 %** of the score is always zero and **all
  1,391 real events fall into the lowest level**. Explained with data in
  `INCIDENCIAS.md` §8.2.
- **Language detection depends on the length of the text.** With long
  phrases it is right (the functional suite gives 5/5); with short phrases
  it returns «es» without warning that it is not sure (§8.4).
- **The scores stored in the database do not match what the current code
  computes.** Average difference of −0.77 (§8.3). They have not been
  recalculated.
- **The scoring needs a design decision** before it can be used seriously:
  it has neither an upper bound nor weight validation.
- **There are 14 points in the code that trap exceptions and return a
  default value** as if it were a real result. `logging.warning` was added
  so the failure gets recorded, but **the returned value did not change**.
  They are listed in `INCIDENCIAS.md`.
- **The API key in the code is for local testing** and must be replaced.
- **No installation from scratch has been tested**, nor on Linux or macOS.
- **What does work well:** the thematic classification and the signal
  detection. Those are the most solid parts of the program.
- **The value of what is published** lies in the conceptual instrument,
  in the architecture and in the lessons of the process, not in technical
  polish.

---

## A personal note from the author

This is my second program. It is called **PULSO**. I hope you find it
useful and that you feel like improving it.

I have had to publish it before finishing the program and completing the
whole testing process because of time and resource limitations. I know
nothing about programming. I have done what I could with the means within
my reach. With more time and resources I could probably have gone much,
much further. Over the coming months I will be less connected to the
internet, especially from a computer, so I am publishing the project now
so that anyone who wishes can consult it and improve it. Its behaviour
still has to be checked through a long period of real operation, with
daily ingestion and evaluation of its results.

I planned to upload this program in November, but I have been able to do it
sooner. In November I will upload the last one I have left, also made with
the help of another artificial intelligence. They are three programs of the
same style —SIBILA, PULSO and the third one— and each of them was developed
by a different artificial intelligence.
