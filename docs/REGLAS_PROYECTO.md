# REGLAS_PROYECTO.md — Noósfera (LEER ANTES DE CUALQUIER ACCIÓN)

> Documento único de reglas. Revisar OBLIGATORIAMENTE antes de cada acción
> (cron cada hora fuerza la lectura + autochequeo). Si una acción viola
> alguna regla, NO se ejecuta hasta confirmar con el usuario.
> Fuente de verdad: STATUS_2026-07-16_FINAL.md (Paso 31, 37, 39) + directivas
> del usuario. No inventar reglas: estas son las confirmadas por el proyecto.

## 1. VERSION Y CONGELACIÓN (duro)
- Versión de cierre dictada por el usuario: **0.2.1A** (nunca 0.3.0, nunca
  otra). En disco = 0.2.1A; PEP 440 normaliza a 0.2.1a0 pero el nombre
  visible del programa es 0.2.1A.
- Noósfera 0.2.1A está **CONGELADA**: no se toca `noosfera_project/` (consultas.py,
  api_minima.py, comparador_veo.py, eventos.db, pyproject.toml, CHANGELOG).
- Cualquier corrección a 0.2.1A requiere dictado EXPLÍCITO del usuario
  ("nada de parches, versión nueva limpia con número nuevo"). Si no hay
  dictado, se documenta como hallazgo, no se parchea.
- Empaquetado wheel: BLOQUEADO salvo decisión del usuario. Mientras tanto,
  versión en disco 0.2.1A, NO empaquetado.

## 2. ALCANCE DE FUENTES (duro — STATUS Paso 31)
- **SOLO** redes sociales / foros / gente común (gente común, sin filtro experto).
- **PROHIBIDO**: cualquier medio oficial (BBC, prensa, TV, REUTERS, NYT, CNN,
  Spiegel, Zeit, Tagesschau, Folha, Estadão, G1, GE, etc.). Wikipedia y
  PubMed también fuera de alcance (académico, no gente común).
- **GDELT**: SOLO utilidad de VERIFICACIÓN DE FECHAS. NUNCA fuente de ingesta.
- Fuentes válidas actuales (verificadas red real): Hacker News, Reddit vía
  Lemmy/lemmit.online, Telegram, Lemmy (6 instancias), 4chan, Mastodon
  (hashtags ES/EN), Discourse, Matrix, Stack Exchange, PeerTube (solo
  comentarios).
- Las 3 fuentes prohibidas viven en `_dev_deteccion/fuera_alcance/` como
  referencia; NO se cablean, NO ingieren.

## 3. DONDE TRABAJAR (separación estricta)
- Código nuevo / experimentos post-observación: en `_dev_deteccion/` y
  `_preparacion_post/`. NUNCA dentro de `noosfera_project/`.
- Pruebas de ingesta: SIEMPRE sobre COPIA (`_preparacion_post/eventos_limpio.db`),
  nunca sobre `noosfera_project/eventos.db` (debe quedar en 721 filas).
- `noosfera_project/eventos.db` = 721 docs (718 reales + 3 .md internos).
  Verificar con `SELECT COUNT(*) FROM lenguaje_colectivo` == 721 tras cada
  experimento. Si baja de 721, es corrupción → restaurar.

## 4. VERIFICACIÓN (duro — "evidencia real, no afirmar completado sin ejecución")
- Toda afirmación de "funciona" debe venir de ejecución REAL (exit code
  visible, red real), no de intuición.
- Verificaciones ad-hoc en `%TEMP%/hermes-*.py`; tras correr, BORRAR el
  script y confirmar `QUEDAN_TEMP=0`.
- No confundir "ad-hoc verification" con "suite green": los scripts son
  temporales por diseño; la evidencia es el exit code + la salida real.
- `test_dev_deteccion.py` debe quedar EXIT=0 (regresión).

## 5. FORMATO DE SALIDA (duro — memoria del usuario)
- Fechas SIEMPRE en formato **DD/MM/YYYY** en JSON, CSV, MD, informes.
- Comunicación en español.

## 6. AUTONOMÍA (directiva del usuario)
- "Sigue adelante por donde puedas": dentro del alcance (reglas 1-3), puedo
  buscar fuentes nuevas, herramientas, flancos abiertos sin preguntar.
- FUERA de autonomía (requiere confirmación): tocar 0.2.1A, empaquetar,
  parchear versión numerada, añadir medios, borrar corpus.

## 7. CHECKLIST RÁPIDO ANTES DE CADA ACCIÓN
- [ ] ¿Toca `noosfera_project/`? → NO (salvo dictado).
- [ ] ¿Ingeriría en `eventos.db` original? → NO, usar copia.
- [ ] ¿La fuente es medio oficial / Wikipedia / PubMed? → NO.
- [ ] ¿GDELT como fuente? → NO, solo fechas.
- [ ] ¿Seré capaz de verificar con exit code real? → SI o no ejecutar.
- [ ] ¿Formato fecha DD/MM/YYYY? → SI.
- [ ] ¿Temp limpio tras prueba? → SI (QUEDAN_TEMP=0).
