# Estrategas — registro persistente

> Los subagentes mueren al cerrar la sesión (no sobreviven al reinicio del
> PC). Este archivo conserva su conocimiento para no perderlo. Se actualiza
> cada vez que un estratega entrega ideas valiosas. Si en una sesión futura
> se relanza uno, se le pasa este contexto para que "recuerde" lo aprendido.

---

## 1. Estratega de Inteligencia Predictiva (rondas 1 y 2)

**Perfil:** anticipa crisis, giros y movimientos. Indicadores líderes.

**Ronda 1 (implementada en `inteligencia_predictiva.py`):**
- Escalada de tono — queja → agravio → identidad colectiva → movilización.
  El paso de "yo" a "nosotros" precede a la acción.
- Salto colectivo — ratio de docs con "nosotros" vs "yo".
- Co-ocurrencia anómala entre temas — dos temas que nunca se mezclaban
  empiezan a co-aparecer (reencuadre causal).

**Ronda 2 (implementada):**
- Rumorómetro — densidad de rumor = ambigüedad × segunda mano. Preceden
  pánicos y acciones espontáneas.
- Gramática de la acción — la charla pasa de expresar (queja) a planificar
  (logística: "quedamos en", "llevad"). La logística precede a la calle.
- Coalición imposible — fusión de agravios improbables en el mismo post
  (vivienda+corrupción). Sello de coaliciones nuevas.

**Sus ideas NO implementadas (anotadas para más adelante):**
- La frase que se repite (formación de eslogan) — toda ola cristaliza en una
  fórmula ("¡Que se vayan todos!"). Detectar el bautizo del movimiento.
- Lo que no se puede decir (espiral del silencio) — cuando sube el volumen
  pero baja la palabra directa, hay tabú a punto de romperse.
- El eco en otros idiomas (ola transfronteriza) — el salto de idiomas predice
  que lo local se vuelve global.
- El eco unánime (réplica que falta) — tema candente sin la contrarréplica
  esperable = consenso o silenciamiento en formación.
- Extra: la risa antes del grito (aceleración del sarcasmo).
- Extra: inversión epistémica (el tema pasa de preguntas a afirmaciones).

---

## 2. Sociólogo Computacional (ronda 1, en curso)

**Perfil:** movimientos sociales, marcos cognitivos, ciclo de protesta.
Fundamentos: Tilly (repertorios de acción), Tarrow (ciclos de protesta),
Snow (enmarcado diagnóstico-atribución-pronóstico).

*(Pendiente de resultados.)*

---

## 3. Experto en Semántica de Corpus (ronda 1, en curso)

**Perfil:** cambio conceptual, resemantización, marcos semánticos.
Fundamentos: FrameNet, análisis del discurso, WordNet.

*(Pendiente de resultados.)*

---

## 4. Auditor Adversario (rondas 1 y 2)

**Perfil:** encontrar fallos, no confirmar. El más valioso de la sesión.

**Ronda 1 — encontró el fallo CRÍTICO de inversión temporal:**
- `serie()` devolvía `ORDER BY fecha DESC` pero los detectores tratan
  `serie[-1]` como "hoy" → el veredicto salía al revés. Corregido.
- `serie()` no exponía la clave `senal` → los detectores leían 0. Corregido.
- `zscore_diario` devolvía z=5e9 con σ=0. Corregido.
- `corroboracion` mezclaba nombres reales con conteos sintéticos. Corregido.
- `enriquecer_watchlist` tenía la corroboración muerta (clave fantasma). Corregido.

**Ronda 2 (en curso):** auditando la API REST, el pipeline end-to-end y
entradas adversariales a los módulos nuevos.

---

## 5. Ingeniero de Publicación/Empaquetado (rondas 1 y 2)

**Perfil:** llevar el proyecto a paquete instalable y publicable.

**Ronda 2 (aplicada):**
- Política de dependencias: core = stdlib pura (`dependencies = []`), todo lo
  demás en extras (cli, api, rss, pdf, dev, full). Borrados requests y
  dotenv (verificado: no se importan).
- Dashboard web: `/` ahora sirve HTML real, no JSON. `/api/dashboard` para
  consumo programático.
- Limpieza pre-commit: borrar setup.py, carpetas _wb*, .bak, eventos.db, logs.

**Sus recomendaciones pendientes:**
- Mover `import feedparser` dentro de la función en rss.py (degradación
  elegante sin el extra).
- README de publicación (el actual es de desarrollo).
- git init limpio copiando solo lo público.

---

## Regla de conservación

Cuando un estratega entregue ideas valiosas, añadirlas aquí (sección
"implementadas" + "no implementadas"). Al relanzar un estratega en otra
sesión, pegarle su sección como contexto para que continúe desde ahí.
