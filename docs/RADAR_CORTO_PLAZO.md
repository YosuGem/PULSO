# RADAR DE CORTO PLAZO — prueba y detección temprana

**Rama:** 0.2.2-dev · **Fecha:** 11/10/2026

## Para qué existe

El histórico normal (`analisis_historico`) guarda una foto por día y compara
el último contra el anterior. Sirve, pero **necesita días acumulados**.

El radar responde otra necesidad: **validar el programa a corto plazo**
(3 o 7 días) sin esperar meses, y detectar temas emergentes antes que los
medios. Parte el corpus en ventana reciente vs anterior y dice tres cosas:

| Señal | Qué significa |
|---|---|
| **NUEVO** | El tema aparece en la ventana reciente y no existía en la anterior |
| **CRECE** | Sube su volumen respecto a la ventana anterior |
| **SE ENFRÍA** | Baja o desaparece respecto a la ventana anterior |

Es la única forma de probar el sistema cuando no hay tiempo para una
observación larga: se ejecuta, se ve qué detecta en 3 o 7 días, y se
comprueba si las detecciones tienen sentido.

## Cómo se usa

### CLI (para prueba manual)

```bash
py noosfera_project/servicios/radar_corto.py
```

Ejecuta el radar con ventana de 3 y 7 días sobre el corpus real y lo imprime
en texto legible.

### API (para prueba diaria automatizada)

```
GET /api/radar?ventana=1    ← hoy vs ayer (cambio intradía)
GET /api/radar?ventana=3
GET /api/radar?ventana=7
GET /api/radar?ventana=14
GET /api/radar?ventana=30
```

Ventana inválida devuelve 400. Respuesta JSON con `nuevos`, `crecen`,
`enfrian` y los totales.

**Ventana de 1 día:** compara hoy contra ayer. Es la escala de los temas que
giran en horas —política internacional, decisiones de bancos centrales,
sanciones, elecciones— donde 3-7 días es demasiado lento.

### Como módulo (para pruebas con datos propios)

```python
from noosfera_project.servicios.radar_corto import radar, informe

docs = [{"fuente": "reddit", "texto": "...", "publicado": "2026-10-10"}, ...]
res = radar(docs, ventana_dias=7)
print(informe(res))
```

## Verificación

- **7/7 tests** en `noosfera_project/tests/test_radar_corto.py`
- Suite completa: **45 passed** (38 + 7 nuevos)
- API verificada en vivo: 200 en ventanas válidas, 400 en ventana inválida
- Deportes queda excluido del radar (respeta `temas_excluidos`)
- Documentos sin fecha se cuentan como recientes y se informan en `sin_fecha`

## Limitación honesta

El corpus actual tiene fechas de julio de 2026 y hoy es octubre, así que todo
cae fuera de la ventana de 7 días: el radar sobre el corpus real solo muestra
"se enfría". **Esto es correcto, no un fallo** — es lo que pasa con data vieja.
La prueba real de que detecta NUEVOS y CRECIMIENTO está en los tests con datos
sintéticos de 1-9 días de antigüedad.

Cuando entre data fresca de foros/redes con fechas de 3-7 días, el radar
empezará a mostrar temas nuevos y en crecimiento de forma natural.

## Relación con el resto

- **`historico_analisis`**: tendencias entre ejecuciones del pipeline (largo plazo)
- **`radar_corto`**: qué cambia en 3-7 días (validación rápida y detección temprana)

Son complementarios. El radar es la herramienta para la semana de prueba; el
histórico es para la operación continuada.
