# FUENTES DE INGESTA — catálogo y reglas

**Rama:** 0.2.2-dev · **Fecha:** 11/10/2026

## Regla de alcance (inquebrantable)

Solo **voz de gente común** en foros, redes, imageboards y agregadores.

**PROHIBIDO:**
- Medios de comunicación tradicionales (prensa, TV, agencias, periódicos).
- Organizaciones/instituciones (NASA, USGS, gobiernos).
- Cualquier fuente con API de pago o key de terceros.

Si una fuente mezcla foro con contenido editorial, se ingieren **solo las
secciones de foro**.

## Fuentes activas (ya integradas en el corpus)

| Fuente | Idioma | Tipo |
|---|---|---|
| Reddit (varios subs) | EN/ES | Red/agregador |
| Hacker News | EN | Agregador técnico |
| Telegram | ES/EN | Red/mensajería |
| Lemmy | ES/EN | Fediverso |
| forocoches | ES | Foro |
| Foros NBA/MLB/F1/EPL/Wimbledon/UCL/NHL/NFL | EN/ES | Foros deportivos |

## Fuentes candidatas verificadas (11/10/2026)

Todas verificadas en vivo por el subagente cazador **y confirmadas de forma
independiente** (respuesta 200, sin API key, sin violar reglas de alcance).

| Fuente | URL | Idioma | Cómo se lee | Nota |
|---|---|---|---|---|
| **Pikabu** | pikabu.ru | Ruso | RSS `pikabu.ru/xmlfeeds.php?cmd=popular` | Agregador estilo Reddit ruso. Encoding windows-1251. |
| **DTF** | dtf.ru | Ruso | RSS `dtf.ru/rss/all` | Comunidad técnica/juegos (tipo Habr). |
| **2ch.hk** | 2ch.hk | Ruso | JSON `2ch.hk/b/index.json` | Imageboard ruso, lo más crudo. Boards `/b`, `/news`… |
| **TabNews** | tabnews.com.br | Portugués (BR) | RSS `tabnews.com.br/recentes/rss` | Comunidad de devs/emprendedores brasileños. |
| **Jeuxvideo.com** | jeuxvideo.com | Francés | RSS `jeuxvideo.com/rss/rss.xml` | Foro más grande de Francia. **Solo secciones de foro** (también tiene editorial). |
| **mstdn.jp** | mstdn.jp | Japonés | API `mstdn.jp/api/v1/timelines/public` | Instancia Mastodon pública japonesa. |
| **Lobsters** | lobste.rs | Inglés (técnico) | RSS `lobste.rs/rss` | Agregador técnico tipo HN pero más nicho. Usar RSS (el HTML tiene anti-bot). |
| **Linux.org.ru** | linux.org.ru | Ruso | Scraping HTML / feeds por foro | Foro técnico Unix de nicho. |

### Bonus (alternativas anglo ya conocidas)

- Reddit multilengüe vía `.rss` (r/de, r/france, r/brasil) — 200 sin key.
- `a.4chan.org/pol/catalog.json` — 200, altavoz anglo (ruidoso).

## Nota de implementación

`mstdn.social` (inglés) devolvió 422 con el User-Agent por defecto; se
resuelve con un UA real de navegador. Las instancias del fediverso se leen
por su API pública `/api/v1/timelines/public`.

Para añadir una fuente nueva hay que: (1) verificar que responde sin key,
(2) confirmar que es voz de gente común y no medio/institución, (3) añadirla
al conector de ingesta respetando el encoding (pikabu es windows-1251).

## Pendiente

Ninguna de estas fuentes está **conectada** al pipeline todavía: están
verificadas y documentadas, listas para integrarse. La integración requiere
decidir encoding por fuente y el módulo lector de cada formato (RSS/JSON/
API Mastodon), que es trabajo de la fase de ingesta.
