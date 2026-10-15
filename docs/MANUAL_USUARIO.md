# Noósfera — Manual de usuario

**Qué es, por qué existe, qué idea hay detrás y cómo se usa.**

Este manual explica la *intención* del programa, no su código. Está pensado
para dos públicos a la vez: **personas** que quieran entender y usar el
programa, y **agentes** (otros programas de IA) que necesiten operarlo. Cuando
algo solo aplica a un grupo, está marcado.

---

## 1. Qué es Noósfera

Noósfera es un sistema que **escucha a la gente común** —foros, redes,
agregadores— y detecta los **temas que están empezando a hervir** antes de que
los medios de comunicación tradicionales se hagan eco.

No predice el futuro ni lee la mente. Hace algo más modesto y más útil:
**mide el pulso de la conversación colectiva** y avisa de qué temas están
subiendo, cuáles se enfrían y en qué dirección se mueve el sentimiento de la
gente.

Funciona en local, en tu propia máquina, con una base de datos propia. No
depende de servicios de pago ni de conectarse a la nube.

---

## 2. Por qué se creó — la idea

La génesis del proyecto es una observación simple:

> Los grandes temas que mueven el mundo —una crisis, un movimiento, una
> tecnología— casi nunca empiezan en los medios. Empiezan en las
> conversaciones de gente corriente. Primero unos pocos hablan de algo en un
> foro. Luego más gente lo repite. La idea **cuaja** en la comunidad. Solo
> cuando ya es imparable, los medios lo cuentan.

Para cuando un tema sale en el telediario, el momento de detectarlo a tiempo
ya pasó. Noósfera intenta acortar ese desfase: **escuchar el rumor de base,
no el eco de los medios.**

### La teoría detrás (la intención, no el código)

Noósfera se apoya en unas pocas ideas que guían todo su diseño:

1. **La voz de la gente común es la señal.** No los medios, no las
   instituciones. Los foros y redes donde la gente habla sin filtro.
2. **Lo que se repite, crece.** Un tema emergente se reconoce porque cada vez
   más gente usa las mismas palabras y frases. La repetición compartida es la
   huella de una idea que cuaja.
3. **El tiempo importa más que el volumen absoluto.** No importa si un tema
   tiene 50 mensajes; importa si **hoy** tiene más que **ayer**. El cambio en
   el tiempo es la señal, no el tamaño.
4. **La comunidad es diversa o no es comunidad.** Si un tema solo lo repite
   una persona o un único foro, es ruido. Si salta de un foro a otro, de un
   idioma a otro, es que algo real está pasando.
5. **La discusión con desacuerdo tiene fuerza.** Un tema sobre el que todo el
   mundo está de acuerdo no engancha. Un tema que divide a la gente en dos
   bandos es que ha tocado algo importante.
6. **Mejor avisar pronto que avisar perfecto.** Es preferible detectar un
   tema cuando aún es pequeño y arriesgarse a un falso positivo, que
   confirmarlo cuando ya es obvio para todos.

Estas seis ideas son el "por qué" de cada herramienta del programa. Cuando
entiendas estas seis, entiendes Noósfera.

---

## 3. Qué contiene (a grandes rasgos)

Noósfera es un conjunto de piezas que se encadenan:

```
Escucha foros/redes  →  Clasifica por tema  →  Agrupa  →  Mide cambios en
                                                                el tiempo
                                                                     ↓
                              Avisos: qué sube, qué baja, qué se polariza,
                              qué está empezando sin nombre todavía
```

Las piezas principales:

- **Ingesta:** recoge conversaciones de muchas fuentes (Reddit, Hacker News,
  Telegram, Lemmy, forococches, y más verificadas en varios idiomas).
- **Clasificador temático:** ordena cada conversación en una de las ~79
  categorías (política, energía, tecnología, cripto, justicia, etc.).
- **Histórico:** guarda una foto diaria de cuánto se habla de cada tema.
- **Detección de cambios:** compara hoy contra ayer y contra la semana para
  ver qué temas suben, bajan o aparecen.
- **Alerta temprana:** una capa de herramientas estadísticas que distingue
  un cambio real de un pico de un día, y prioriza qué vigilar.
- **Detección de temas sin nombre:** busca combinaciones de palabras que
  empiezan a repetirse antes de que exista una categoría para ellas.
- **Polarización:** mide si un tema divide a la gente (a favor / en contra) y
  si se está propagando de una comunidad a otra.
- **API y paneles:** expone todo lo anterior para que lo consulten personas
  o agentes.

---

## 4. Cómo se usa — para personas

El programa se maneja por comandos. Los tres esenciales:

```bash
noosfera init        # crea la base de datos (solo la primera vez)
noosfera estado      # te dice cómo está el sistema ahora
noosfera servidor    # levanta el panel web en http://127.0.0.1:8000
```

### Dónde guarda tus datos

Todo vive en una carpeta tuya, no en la del programa:

- Por defecto: `~/.noosfera/` (tu carpeta personal, funciona igual en
  Windows, Linux y Mac).
- Si prefieres otro sitio, define la variable de entorno `NOOSFERA_HOME`.

Así puedes instalar, actualizar o borrar el programa sin perder tus datos.

### Los avisos que te da

Cuando consultas el panel o la API, verás avisos en estas formas:

| Aviso | Significa |
|---|---|
| **NUEVO** | Un tema apareció hoy que ayer no estaba. |
| **CRECE** | Un tema que ya existía está subiendo de volumen. |
| **SE ENFRÍA** | Un tema estaba activo y ahora baja. |
| **DERIVA (CUSUM)** | Un cambio sostenido, no un pico de un día. Confianza alta. |
| **VOLÁTIL (AVS)** | Un tema que cambia mucho; conviene vigilarlo a diario. |
| **POLARIZADO** | El tema divide a la gente en dos bandos. Tiene fuerza. |
| **SIN NOMBRE** | La gente repite una idea nueva que aún no tiene categoría. |
| **CRECE / MUERE / LATENTE** | Predicción de hacia dónde va el tema. |

**Regla de oro para leer los avisos:** "NUEVO" y "CRECE" te dicen *qué pasó*.
"DERIVA" y "VOLÁTIL" te dicen *en qué confiar*. "POLARIZADO" y "SIN NOMBRE"
te dicen *dónde mirar antes que los demás*.

### Accesibilidad

El panel usa **modo oscuro por defecto**, alto contraste y letras grandes,
pensado para leerse con facilidad incluso con problemas de vista. La
detección nunca depende solo de un color: cada estado lleva también un
símbolo.

---

## 5. Cómo se usa — para agentes

Un agente puede operar Noósfera entero sin leer el código fuente. Todo pasa
por la API y por la línea de comandos.

### Ubicación de datos (para configurar)

- Variable de entorno `NOOSFERA_HOME`: carpeta raíz de datos.
- Base de datos: `$NOOSFERA_HOME/eventos.db` (SQLite).
- Paneles: `$NOOSFERA_HOME/dashboard/`.

### Línea de comandos (salida estable)

```
noosfera init        → crea la BD, imprime la ruta
noosfera estado      → imprime conteo de eventos y niveles
noosfera ciclo       → ingesta + regenera paneles + PDF
noosfera servidor    → levanta la API en 127.0.0.1:8000
noosfera --version   → versión instalada
```

### API REST (JSON estable)

| Endpoint | Qué devuelve |
|---|---|
| `GET /health` | estado del servicio |
| `GET /api/hipotesis` | hipótesis emergentes por categoría |
| `GET /api/temas` | temas detectados |
| `GET /api/tendencias` | tendencias por categoría |
| `GET /api/radar?ventana=1` | cambios en 1 día (hoy vs ayer) |
| `GET /api/radar?ventana=3` | cambios en 3 días |
| `GET /api/radar?ventana=7` | cambios en 7 días |
| `GET /api/watchlist` | temas a vigilar, priorizados |
| `GET /api/vigia` | watchlist enriquecida (z-score, temperatura) |
| `GET /api/backtest` | validación del detector (recall, falsos positivos) |
| `GET /api/senal-corta` | veredicto con pocos días de historial |
| `GET /api/fuentes` | gestión de fuentes de ingesta |

La `ventana` del radar acepta 1, 3, 7, 14 o 30 días.

### Buenas prácticas para un agente

- Empieza por `GET /health` para confirmar que el servicio está vivo.
- Usa `GET /api/radar?ventana=1` para el cambio intradía; `ventana=7` para la
  perspectiva semanal.
- `GET /api/backtest` te dice si el detector es fiable *ahora mismo* con los
  datos que tiene. Compruébalo antes de confiar en una alerta.
- Respeta `NOOSFERA_HOME` si está definido; no asumas rutas.

---

## 6. Preguntas frecuentes

**¿Necesita internet para funcionar?**
Para ingerir conversaciones nuevas, sí. Pero el análisis de lo ya guardado
funciona sin conexión.

**¿De dónde saca las conversaciones?**
Solo de foros, redes y agregadores donde habla gente común. **Nunca** de
medios de comunicación tradicionales ni de instituciones. Esa es una regla
inquebrantable del proyecto: los medios cuentan lo que ya pasó; Noósfera
quiere lo que está pasando.

**¿Por qué una categoría se llama "deportes" pero nunca aparece en los avisos?**
Los deportes están excluidos del análisis a propósito. Se detectan (para que
no inunden el ruido) pero se apartan de los avisos, por decisión del proyecto.

**¿Cuánta historia necesita para ser útil?**
Con 3-5 días ya funciona la capa de "señal corta". Con más días, las
herramientas estadísticas (volatilidad, deriva) se vuelven más precisas. Está
diseñado para dar aunque con pocos datos.

**¿Es fiable al 100%?**
No, y no pretende serlo. Es un sistema de *aviso temprano*, no de verdad
revelada. Te dice dónde mirar. La decisión final es tuya.

---

## 7. En una frase

> **Noósfera toma el pulso de lo que la gente común habla en comunidad, y te
> avisa de qué temas están empezando a mover el mundo antes de que los medios
> se enteren.**

---

*Manual de usuario · versión 0.2.2-dev · Apache License 2.0*
