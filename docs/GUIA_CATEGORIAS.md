# AMPLIACIÓN DE CATEGORÍAS — método y estado

**Rama:** 0.2.2-dev · **Fecha:** 11/10/2026

## Por qué existe este documento

Ampliar categorías es fácil. Ampliarlas **sin romper las que ya funcionan** es
lo difícil, y ya ocurrió una vez: `energia` y `energia_renovable` compartían
los tokens `solar` y `eolica`, así que "paneles solares" seguía cayendo en la
categoría genérica y la nueva no servía de nada.

## El guardián (obligatorio antes y después de cada cambio)

```bash
py -m noosfera_project.procesamiento.guardian_categorias
```

Verifica tres reglas:

1. **Un token vive en UNA sola categoría.** Si se duplica, el empate lo
   resuelve el orden del diccionario, que es arbitrario.
2. **Ninguna categoría se queda sin tokens.**
3. **Ninguna frase vive en dos categorías.**

Si falla, dice qué token y sugiere qué categoría debería quedárselo (la más
específica, la que tiene menos tokens).

## Método para añadir una categoría

**1. Probar antes de añadir.** Escribir 3-5 frases reales del tema y ver
dónde caen hoy. Si caen bien, no hace falta la categoría.

```python
from noosfera_project.procesamiento.clasificador_tematico import clasificar
clasificar("El oro y el platino suben por la demanda industrial")
```

**2. Añadir con tokens que no existan en otra categoría.**

**3. Ejecutar el guardián.** Si marca duplicados, resolverlos: el token se
queda en la categoría más específica.

**4. Verificar regresión.** Las frases nuevas deben caer en su categoría y el
corpus no debe moverse:

```bash
py -m pytest noosfera_project/tests/ -q
```

## Estado actual: 38 categorías

### Cobertura verificada (textos de prueba)

| Área | Casos correctos |
|---|---|
| Materias primas (oro, cobre, petróleo, solar, chips, trigo) | 6/6 |
| Segunda hornada (justicia, laboral, vivienda, transporte, ciencia, educación, crimen, RRII) | 8/8 |
| Tercera hornada (cultura, biodiversidad, demografía, tech consumo, salud mental, turismo, deuda) | 7/7 |
| **Total** | **21/21** |

### Catálogo

**Núcleo original (14):** deportes ⛔, politica_gobierno, ciberseguridad,
bitcoin, seguridad_orden, inflacion_europa, sp500, guerra_ucrania,
inteligencia_artificial, clima_medioambiente, elecciones_eeuu, migracion,
tecnologia_cuantica, energia

**Materias primas y energía (6):** metales_preciosos, metales_industriales,
energia_petroleo_gas, energia_renovable, semiconductores, agricultura

**Sociedad e infraestructura (10):** sanidad, infraestructura, justicia,
laboral, vivienda, transporte, ciencia_espacio, educacion, crimen_organizado,
relaciones_internacionales

**Tercera hornada (8):** cultura, religion, biodiversidad, demografia,
tecnologia_consumo, salud_mental, turismo, deuda_publica

**Cuarta hornada — tecnología de frontera (8):** robotica, fusion_nuclear,
vehiculos_autonomos, realidad_extendida, neurotecnologia,
fabricacion_aditiva, conectividad_satelital, biotecnologia

**Quinta hornada — malestar social (8):** brecha_generacional,
desigualdad_social, endeudamiento_personal, genero, discriminacion,
libertad_expresion, movilizacion_social

**Sexta hornada — economía y mercados (9):** banca_credito, divisas,
comercio_exterior, insolvencias, materiales_industriales_basicos,
escasez_agua, burbujas_mercado, automocion, consumo_minorista

**Séptima hornada — tensión geopolítica (9):** estrecho_taiwan,
mar_sur_china, peninsula_coreana, oriente_medio, balcanes_kosovo, sahel,
region_polar, dedolarizacion, cachemira

**Octava hornada — micro-experiencia común (7):** suministros_escasez,
salud_cronica, movilidad_urbana, conectividad_caidas,
privacidad_vigilancia, precariedad_plataforma, mineria_recursos

⛔ = excluida del análisis (`deteccion/temas_excluidos.py`)

**Analizables: 77**

**Total: 78 categorías** (eran 14 al abrir la rama 0.2.2-dev)

## Concurso de subagentes — balance

5 subagentes con perfiles distintos propusieron ampliaciones. Todas se
integraron **solo** tras pasar el guardián y la regresión.

| Subagente | Propuso | Aceptadas | Rechazadas por colisión |
|---|---|---|---|
| Tecnología de frontera | 10 | 8 | baterias_almacenamiento, blockchain_web3 |
| Sociología | 8 | 8 (1 renombrada) | 5 tokens: pensiones, huelga, aborto, protesta, pensionistas |
| Mercados | 9 | 9 | 1 token: tarjeta de credito |
| Geopolítica | 10 | 9 (1 renombrada) | rutas_maritimas, alto el fuego |
| OSINT general | 8 | 7 | comercio_global_aranceles, cuello de botella |

**De 14 a 78 categorías en una sola sesión.**

### Las ideas que más valor de los subagentes

- **`consumo_minorista`** (mercados): "no llegar a fin de mes", la voz de la
  gente común en estado puro. Las estadísticas oficiales llegan 2-3 meses
  después.
- **`precariedad_plataforma`** (OSINT): "falso autónomo", "trabajador
  quemado". La vivencia laboral antes que la regulación.
- **`endeudamiento_personal`** (sociología): distinto de deuda_publica. Una
  familia ahogada en un préstamo rápido no es la prima de riesgo.
- **`escasez_agua`** (mercados): el agua como commodity ignorado.
- **Señales propuestas por el geopolítico** (pendientes de implementar):
  dispersión por subforos y cambio de registro (de ironía a urgencia) como
  marcadores de escalada, mejores que el volumen bruto.

## Duplicados heredados resueltos

| Token | Estaba en | Resuelto |
|---|---|---|
| `congreso`, `senado` | elecciones_eeuu + politica_gobierno | politica_gobierno |
| `copa do mundo`, `coupe du monde`, `weltmeisterschaft` | elecciones_eeuu + deportes | deportes |
| `mineria` | bitcoin + metales_industriales | metales_industriales |
| `red electrica` | energia + infraestructura | infraestructura |
| `metro`, `tren` | infraestructura + transporte | transporte |
| `solar`, `eolica` | energia + energia_renovable | energia_renovable |
| `app` | ciberseguridad + tecnologia_consumo | tecnologia_consumo |
| `bateria` | energia_renovable + tecnologia_consumo | tecnologia_consumo |

## Falsos positivos por subcadena corregidos

| Síntoma | Causa | Arreglo |
|---|---|---|
| "varias" clasificado como IA | token `ia` hacía substring | palabra completa |
| "desboca" clasificado como deportes | token `boca` (Boca Juniors) | palabra completa |
| "batería de una semana" → renovables | token `bateria` ambiguo | movido a tecnologia_consumo |

**Lección:** se probó exigir palabra completa a *todos* los tokens de ≤3
letras y se **revirtió**: subía el `undetected` de 5 a 10 porque tokens
legítimos como `ley`, `red` y `oro` dejaban de matchear. La lista
`TOKENS_CORTOS` es explícita y solo entra lo que ha dado un falso positivo
real.

## Próximos candidatos (por explorar)

- **Deporte excluido pero presente**: 208 docs, 29% del corpus
- **Áreas sin cubrir**: derecho/constitución, pensiones en detalle,
  ciberguerra, deepfakes, vivienda turística, agua/sequía como tema propio
