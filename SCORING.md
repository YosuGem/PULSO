# El sistema de puntuación (scoring)

> **El nombre del programa es Pulso.** Véase `HISTORIA_Y_ORIGEN_DEL_PROYECTO.md`.

**Fuente:** `noosfera_project/procesamiento/scoring.py`, líneas 25-99.
**Estado:** la fórmula **no se ha modificado**. Este documento la describe tal
como está en el código.

---

## 1. La fórmula que hay realmente en el código

```python
L26  pesos      = cargar_pesos()
L27  titulo     = evento.get("titulo") or ""
L28  categorias = evento.get("categorias") or ""
L29  publicado  = evento.get("publicado") or ""
L30  texto      = evento.get("texto") or ""
L31  combinado  = f"{titulo} {categorias} {texto}".lower()

L36  pesos_categorias = pesos.get("categorias", {}) or {}
L37  for token, peso in pesos_categorias.items():
L38      if token in combinado:
L39          factores[f"cat_{token}"] = float(peso)          # pesos aprendidos

L43  peso_cat_base = pesos.get("categoria_base", 0.30)      # default 0.30
L44  cats = [c.strip() for c in str(categorias).split(",") if c.strip()]
L45  for c in cats:
L46      factores.setdefault(f"cat_{c}", peso_cat_base)      # NO sobrescribe

L49-56 try: carga = float(analizar_emocion(titulo)["score_emocional"])
         except Exception: carga = 0.0
L53-54   if carga: factores["emocional"] = carga

L58  recencia   = _peso_recencia(publicado, ahora)
L59  diversidad = min(len(cats)/4.0, 1.0) if cats else 0.1
L60  longitud   = min(len((titulo+" "+texto).split())/20.0, 1.0)
L61  carga_norm = min(carga/3.0, 1.0)

L64  score  = pesos.get("coincidencia", 0.45) * sum(factores.values())
L65  score += pesos.get("recencia",    0.25) * recencia
L66  score += pesos.get("diversidad",  0.15) * diversidad
L67  score += pesos.get("longitud",    0.15) * longitud
L68  score += pesos.get("emocional",   0.10) * carga_norm

L70-74 nivel = "bajo" (<0.50) | "medio" (<0.75) | "alto"
L77  return round(score, 4)
```

---

## 2. Terminología: tres cosas distintas

Conviene no confundirlas, porque el código hace tres operaciones diferentes.

| concepto | qué es | operación |
|---|---|---|
| **Coeficiente** | `pesos.get('coincidencia'\|'recencia'\|…)` | **multiplica** a su término |
| **Factor** | cada valor dentro del dict `factores` | se **suman** entre sí |
| **Término** | `coeficiente × factor` | los cinco términos se **suman** |

Los cinco términos:

| término | expresión | naturaleza |
|---|---|---|
| **T1** | `coincidencia × Σ(factores)` | suma de factores de categoría **más** el emocional |
| **T2** | `recencia × recencia` | discreta, por tramos horarios |
| **T3** | `diversidad × diversidad` | cuenta **elementos**, no únicos |
| **T4** | `longitud × longitud` | continua |
| **T5** | `emocional × carga_norm` | continua |

---

## 3. Los factores que intervienen

### 3.1 `Σ(factores)` — suma de factores de categoría

Tres fuentes se suman en el mismo dict:

1. **Pesos aprendidos** (L39): por cada token de `pesos["categorias"]` que aparezca en el texto.
2. **`categoria_base`** por categoría real (L46): `pesos.get("categoria_base", 0.30)`, por defecto **0.30**. `setdefault` implica que un duplicado **no** vuelve a sumar.
3. **Carga emocional** (L54): `factores["emocional"] = carga`, solo si `carga > 0`.

**Consecuencia importante:** el emocional está **dentro** de `Σ(factores)`, así
que se multiplica por `coincidencia` (0.45) en L64.

### 3.2 Factor emocional — entra dos veces

| por dónde | efecto |
|---|---|
| L54, dentro de `Σ(factores)` | multiplicado por `coincidencia` (0.45) |
| L68, como término T5 | `0.10 × min(carga/3, 1)` |

Aporte emocional total: `0.45·c + 0.10·min(c/3, 1)`

Rango de `carga`: `score_emocional ∈ [0, 10]`, declarado en el docstring de
`pesos_emocionales.analizar_emocion`.

### 3.3 Recencia (T2)

`_peso_recencia`, L84-99:

| condición | valor |
|---|---|
| `horas ≤ 72` | 1.0 |
| `horas ≤ 168` | 0.7 |
| `horas ≤ 720` | 0.4 |
| resto | 0.1 |
| fecha inválida o vacía | 0.2 (rama `except`) |
| **fecha futura** | **1.0** ← ver §6.2 |

### 3.4 Diversidad (T3)

```python
L59  diversidad = min(len(cats) / 4.0, 1.0) if cats else 0.1
```

`len(cats)` cuenta **elementos**, no valores únicos. `cats` (L44) hace `strip()`
pero **no elimina duplicados**.

### 3.5 Longitud (T4)

```python
L60  longitud = min(len((titulo + " " + texto).split()) / 20.0, 1.0)
```

Número de palabras entre título y texto, dividido por 20, saturado a 1.0.

---

## 4. Los pesos

Configuración medida en `ml_pesos.json`:

```json
{
  "pesos": {
    "coincidencia": 0.45,
    "recencia": 0.25,
    "diversidad": 0.15,
    "longitud": 0.15
  }
}
```

| coeficiente | valor | por defecto en código |
|---|---|---|
| `coincidencia` | 0.45 | 0.45 |
| `recencia` | 0.25 | 0.25 |
| `diversidad` | 0.15 | 0.15 |
| `longitud` | 0.15 | 0.15 |
| `emocional` | **ausente del JSON** | 0.10 (lo pone el código) |
| `categoria_base` | **ausente del JSON** | 0.30 |

**La suma de coeficientes es 1.10**, no 1.00. Eso implica que, si los cinco
factores valieran 1.0 simultáneamente, el score sería 1.10 > 1.0.

Pero la suma 1.10 es secundaria frente al problema real: **el término
dominante es `coincidencia × Σ(factores)`, y `Σ(factores)` no está normalizado**.

---

## 5. Lo verificado por ejecución

Todos estos valores se obtuvieron ejecutando `calcular_score` sobre una copia,
con `ahora` fijo para que el resultado sea determinista.

### 5.1 Crecimiento con el número de categorías

Entrada: `titulo=''`, `categorias='c0,c1,…'`, `publicado='2026-01-01'`, `texto=''`

| n categorías | `Σ(factores)` | score | nivel |
|---|---|---|---|
| 1 | 0.30 | 0.1975 | bajo |
| 4 | 1.20 | 0.7150 | medio |
| 8 | 2.40 | 1.2550 | alto |
| 64 | 19.20 | 8.8150 | alto |
| 1000 | 300.00 | **135.1750** | alto |

Con `titulo='Crisis'` (carga emocional 3.0):

| n | `Σ(factores)` | score |
|---|---|---|
| 1 | 3.30 | 1.6550 |
| 1000 | 303.00 | **136.6325** |

### 5.2 El término `K`

Definido como `K = score − coincidencia·Σ(factores) = T2 + T3 + T4 + T5`.

| variable | dominio | mínimo |
|---|---|---|
| `rec` | `{1.0, 0.7, 0.4, 0.1, 0.2}` | 0.1 |
| `div` | `min(n_elem/4, 1)` o 0.1 si vacío | 0.0 |
| `lon` | `min(palabras/20, 1)` | 0.0 |
| `carga_norm` | `min(c/3, 1)` | 0.0 |

```
K mín = 0.25·0.1 = 0.025
K máx = 0.25·1.0 + 0.15·1.0 + 0.15·1.0 + 0.10·1.0 = 0.65
```

**Verificado en 11 combinaciones de entrada**, todas dentro de `[0.025, 0.65]`.
El caso «todo al máximo» dio exactamente **0.6500**.

**Importante:** este rango es válido **para la configuración actual de pesos y
para entradas válidas**. No es una propiedad del código: si cambian los
coeficientes del JSON, `K` cambia.

### 5.3 Categorías duplicadas

| entrada | claves en `factores` | `div` | score |
|---|---|---|---|
| `Deportes` | `['cat_Deportes']` | 0.25 | 0.2050 |
| `Deportes,Deportes` | `['cat_Deportes']` | 0.50 | 0.2425 |
| `Deportes×3` | `['cat_Deportes']` | 0.75 | 0.2800 |
| `Deportes×4` | `['cat_Deportes']` | 1.00 | 0.3175 |
| `a,b,c,d` | 4 claves distintas | 1.00 | 0.7225 |
| `deportes,Deportes` | `cat_Deportes` **y** `cat_deportes` | 0.50 | 0.3775 |

**Incoherencia interna demostrada:** `factores` cuenta únicos (`setdefault`
colapsa duplicados), pero `diversidad` cuenta elementos (`len(cats)`). Con 1 y
con 4 elementos las claves de `factores` son idénticas, y aun así el score pasa
de 0.2050 a 0.3175. **El mismo contenido categórico da scores distintos.**

Además, la diferencia de mayúsculas genera **dos claves distintas**, inflando
`Σ(factores)`.

### 5.4 `categoria_base` extremo

Entrada: `titulo='Crisis'`, `categorias='economia'`, `publicado=hoy`,
`categoria_base=100`

| término | cálculo | aporte |
|---|---|---|
| coincidencia | `0.45 × (100.0 + 3.0)` | **46.3500** |
| recencia | `0.25 × 1.0` | 0.2500 |
| diversidad | `0.15 × 0.25` | 0.0375 |
| longitud | `0.15 × 0.05` | 0.0075 |
| emocional | `0.10 × 1.0` | 0.1000 |
| **suma** | | **46.7450** |

El valor 100 es **333 veces** el default 0.30, y el término de coincidencia es
el **99.2 %** del score final.

### 5.5 Pesos negativos

| pesos | score |
|---|---|
| `coincidencia=-1.0`, publicado vacío | **−3.1050** |
| `coincidencia=-1.0`, publicado enero | **−3.1300** |
| `coincidencia=-1.0`, publicado hoy | **−2.9050** |
| `coincidencia=-1.0`, `titulo='Noticia'`, enero | **−0.2225** |
| `categoria_base=-50` | **−22.4225** |

**Todos clasificados `bajo` sin señalarlo.**

---

## 6. Comportamiento ante entradas adversariales

### 6.1 Pesos malformados

| peso | resultado |
|---|---|
| texto (`"alto"`) | **TypeError**: `can't multiply sequence by non-int of type 'float'` |
| `null` | **TypeError**: `unsupported operand type(s) for *: 'NoneType' and 'float'` |
| lista | **TypeError**: ídem |
| negativo | aceptado → score negativo |
| enorme (`1e9`) | aceptado → score **300000000.0775** |
| desconocido | **ignorado correctamente** (comportamiento adecuado) |
| ausente | usa el valor por defecto |

**No hay validación de tipo ni de rango en `cargar_pesos()`.**

### 6.2 Fechas futuras

```python
L90  horas = max((ahora - pub).total_seconds() / 3600.0, 0.0)
L91  if horas <= 72: return 1.0
```

El intervalo negativo se clampea a 0.0 con `max(…, 0.0)`. Como `0.0 ≤ 72`,
devuelve `1.0`.

**Una noticia fechada en 2030 recibe la misma recencia máxima que una recién
publicada.** Verificado con +1 año y +10 años.

### 6.3 Tipos inesperados en el evento

| campo | valor | resultado |
|---|---|---|
| `titulo` | `42` | **TypeError** |
| `titulo` | `["a"]` | **TypeError** |
| `texto` | `7` | **TypeError** |
| `texto` | `{}` | **TypeError** |
| `categorias` | `["a", 1, None]` | claves `cat_['a'`, `cat_1`, `cat_None]` |
| `evento` | `{}` | 0.065 (correcto) |
| todos los campos | `None` | 0.065 (correcto) |

### 6.4 Configuración corrupta

`ml_pesos.json` con JSON inválido → `cargar_pesos` captura y devuelve los
valores por defecto **en silencio**, sin log. Score 0.2125 sin ningún aviso.

---

## 7. Discrepancias entre expectativa y resultado

| expectativa razonable | resultado real |
|---|---|
| El score está en `[0, 1]` (lo sugieren los umbrales 0.50/0.75) | **No.** Llega a 136.63 y puede ser negativo |
| Categorías repetidas no deberían cambiar el score | **Lo cambian**: 0.2050 → 0.3175 |
| Una fecha futura no debería puntuar como reciente | **Puntúa como reciente**: recencia 1.0 |
| Un peso negativo debería rechazarse | **Se acepta**: score negativo clasificado `bajo` |
| Una configuración corrupta debería avisar | **Se silencia** |
| El score 0.2425 debería corresponder al evento Brasil almacenado | El Brasil almacenado tiene **0.8**; 0.2425 pertenece a otro registro |

---

## 8. La decisión pendiente: el rango del score

### 8.1 Qué se sabe

**No existe documentación que establezca el rango.** No aparece en docstrings,
comentarios, README, `pyproject.toml`, `ESPECIFICACION_TECNICA.json` ni en
ningún documento de `docs/`.

**Evidencia indirecta de que la intención era `[0, 1]`:** los umbrales
`0.50` y `0.75` de L70-74 solo tienen sentido en esa escala.

**Pero el código no lo garantiza**, y de hecho lo incumple de forma medible.

### 8.2 Las alternativas

No se impone ninguna. Son opciones para que el autor decida:

| opción | qué habría que cambiar | consecuencia |
|---|---|---|
| **A. Score en `[0,1]`** | Normalizar `Σ(factores)` (p. ej. dividir por el número de factores) y validar pesos en `cargar_pesos()` | Los umbrales 0.50/0.75 pasarían a ser válidos. Es la opción coherente con el diseño actual |
| **B. Score en `[0,10]`** | Reescalar los umbrales a 5.0 y 7.5 | Coherente con `scoring_emocional` de `_dev_deteccion/version_B`, que usa escala 0-10 |
| **C. Sin cota, umbrales relativos** | Calcular umbrales por percentiles del corpus | Requiere calibración con datos reales; más trabajo |

### 8.3 Consecuencias de no decidir

1. **No se puede corregir INC-05** (score sin cota). Normalizar exige saber a qué rango.
2. **No se puede validar el rango de los pesos** sin saber el rango del score.
3. **Las 8 pruebas RT-16 a RT-25 quedan «pendientes de decisión»**: su veredicto depende de esta elección.
4. **La clasificación `bajo`/`medio`/`alto` no es interpretable.** Con score 135.18, la etiqueta `alto` no aporta información.
5. **Los scores persistidos en las BBDD no son comparables entre sí** si provienen de configuraciones de pesos distintas.

### 8.4 Lo que NO se ha hecho

- **No** se ha modificado la fórmula.
- **No** se ha normalizado ningún resultado.
- **No** se ha introducido ningún límite arbitrario.
- **No** se han cambiado los pesos.
- **No** se ha alterado ningún dato histórico para que cuadre.

---

## 9. Resumen de resultados reproducibles

| magnitud | valor | condiciones |
|---|---|---|
| Score, 1 categoría, sin emocional | 0.1975 | `titulo=''`, enero |
| Score, 1000 categorías, sin emocional | 135.1750 | ídem |
| Score, 1000 categorías, con emocional | 136.6325 | `titulo='Crisis'` |
| `K` mínimo observado | 0.0400 | sin categorías |
| `K` máximo observado | 0.6500 | todo al máximo |
| `K` habitual (n≥4) | 0.1750 | `div` saturada |
| `categoria_base=100` | 46.7450 | `titulo='Crisis'`, hoy |
| `coincidencia=1e9` | 300000000.0775 | 1 categoría |
| `coincidencia=-1.0` | −3.1050 a −0.2225 | según fecha y título |
| Duplicados 1 → 4 elementos | 0.2050 → 0.3175 | mismos factores |
| Score evento Brasil (fórmula actual) | 0.2425 | calculado, **no persistido** |
| Score evento Brasil (persistido) | 0.8 | valor literal de siembra |

---

## 10. Hallazgo de la revisión final: el término principal está desconectado

Este apartado se añadió al comprobar la **calidad** de los resultados, no
solo que la fórmula se ejecutara. Es el hallazgo más importante de todo el
documento.

### 10.1 Lo que pasa

El código necesita cinco pesos. El fichero `servicios/ml_pesos.json` trae
cuatro:

| peso | ¿en el fichero? |
|---|---|
| `coincidencia` | ✅ 0,45 |
| `recencia` | ✅ 0,25 |
| `diversidad` | ✅ 0,15 |
| `longitud` | ✅ 0,15 |
| **`categorias`** | ❌ **NO EXISTE** |

`scoring.py` hace `pesos.get("categorias", {})`. Al no estar, recibe un
diccionario **vacío**. Por tanto `Σ(factores)` vale siempre **0**, y el
término que más pesa en la fórmula —el 45 %— **nunca aporta nada**.

### 10.2 Consecuencia medida

Recalculados **los 1.391 eventos reales** con el código actual:

| | |
|---|---|
| Score mínimo | 0,0625 |
| Score máximo | **0,1675** |
| Media | 0,1175 |
| Mediana | 0,1225 |
| En nivel `bajo` | **1.391 de 1.391 — el 100 %** |
| En nivel `medio` (≥ 0,50) | **0** |
| En nivel `alto` (≥ 0,75) | **0** |

Ningún evento real se acerca al umbral. El rango útil del score, con la
configuración actual, es **[0,0625 , 0,1675]**, muy lejos de [0,50 , 0,75].

### 10.3 Una crisis y una receta puntúan igual

| entrada | score | nivel |
|---|---|---|
| «Crisis económica global con protestas masivas» | 0,3325 | bajo |
| «Receta de tortilla de patatas» | **0,3250** | bajo |

Diferencia: **0,0075**. Al no haber pesos de categorías, lo único que
distingue las dos entradas es la longitud del texto y los acentos.

### 10.4 Tres síntomas, una sola causa

Lo que parecían tres defectos separados es el mismo:

1. `score_suite.py` espería 0,4 y obtiene 0,07.
2. Una crisis y una receta puntúan igual.
3. El campo `factores` del `Score` llega siempre vacío (el código lo
   construye, lo usa para calcular, y no lo devuelve).

### 10.5 Lo que no se ha hecho

**No se ha tocado nada.** Arreglarlo exigiría una de estas dos cosas, y ambas
son decisión del autor:

- **Escribir los pesos de categorías** que faltan en `ml_pesos.json`
  (qué palabra vale cuánto).
- **Rebajar los umbrales** a la escala real de la fórmula (0,50 → ~0,12).

Mientras no se decida, el scoring ejecuta sin errores pero **no ordena nada
por importancia**, que era su finalidad.
