"""Consulta directa a lenguaje_colectivo por palabras clave."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from noosfera_project.servicios.persistencia import DB_PATH, _conexion
from noosfera_project.procesamiento.clasificador_tematico import clasificar
from noosfera_project.procesamiento.expansion_consulta import expandir


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    partes = [p for p in texto.split() if len(p) >= 2 and not p.isdigit()]
    return " ".join(partes)


def _ejecutar_consulta(terminos: list[str], likes: list[str], limite: int, min_coinc: int | None = None, idioma: str | None = None) -> list[dict[str, Any]]:
    # Usar los patrones LIKE recibidos (incluye sinónimos). Si vacío, nada que buscar.
    if not likes:
        return []
    patrones = [v.strip("%").lower() for v in likes]
    params: list[str] = list(likes)
    where = " OR ".join("lower(texto) LIKE ?" for _ in likes)
    if idioma:
        where = f"({where}) AND idioma = ?"
        params = params + [idioma]

    sql = f"""
        SELECT id, fuente, texto, publicado, creado_en, idioma
        FROM lenguaje_colectivo
        WHERE {where}
    """

    if min_coinc is None:
        min_coinc = max(1, (len(terminos) + 1) // 2)

    with _conexion() as conn:
        filas = conn.execute(sql, params).fetchall()

    resultados: list[dict[str, Any]] = []
    for fila in filas:
        fila = dict(fila)
        texto = fila["texto"] or ""
        texto_l = _normalizar(texto)
        # Coincidencias: cuántos patrones (término o sinónimo) aparecen en el texto
        coincidencias = sum(1 for p in patrones if p and p in texto_l)
        if coincidencias < min_coinc:
            continue
        entrada = {
            "id": fila["id"],
            "fuente": fila["fuente"],
            "texto": texto,
            "publicado": fila.get("publicado"),
            "creado_en": fila.get("creado_en"),
            "idioma": fila.get("idioma"),
            "coincidencias": coincidencias,
        }
        # Bloque B: peso emocional por resultado
        from noosfera_project.procesamiento.pesos_emocionales import analizar_emocion
        emo = analizar_emocion(texto)
        entrada["score_emocional"] = emo["score_emocional"]
        entrada["peso_emocional"] = emo["peso_emocional"]
        entrada["parametros_emocionales"] = emo["parametros_utilizados"]
        resultados.append(entrada)

    ordenados = sorted(resultados, key=lambda x: x.get("coincidencias", 0), reverse=True)
    return ordenados[:limite]


def consultar_lenguaje(pregunta: str, limite: int = 20, idioma: str | None = None) -> list[dict[str, Any]]:
    if idioma is None:
        from noosfera_project.procesamiento.idioma import detectar_idioma
        idioma = detectar_idioma(pregunta)
    normalizada = _normalizar(pregunta)
    terminos = list(dict.fromkeys(normalizada.split()))
    if not terminos:
        return []

    # Clasificación temática (Bloque 1 - Sol #1)
    clasificacion = clasificar(pregunta)
    categoria = clasificacion.get("categoria", "undetected")

    sinonimos = {
        "champion": ["champion", "campeon", "campeonato", "campeones"],
        "campeon": ["champion", "campeon", "campeonato", "campeones"],
        "campeonato": ["champion", "campeon", "campeonato", "campeones"],
        "campeones": ["champion", "campeon", "campeonato", "campeones"],
        "finales": ["finales", "final"],
        "final": ["finales", "final"],
        "world": ["world", "mundial"],
        "mundial": ["world", "mundial"],
        "series": ["series", "serie"],
        "league": ["league", "liga", "premier", "premiere"],
        "liga": ["league", "liga", "premier", "premiere"],
        "premier": ["premier", "premiere"],
        "formula": ["formula", "f1"],
        "f1": ["formula", "f1"],
        "eleccion": ["eleccion", "votacion", "presidencial", "legislativa", "votaciones", "estados unidos", "ee.uu"],
        "votacion": ["eleccion", "votacion", "presidencial", "legislativa", "votaciones"],
        "votaciones": ["eleccion", "votacion", "presidencial", "legislativa", "votaciones"],
        "estados": ["estados unidos", "ee.uu", "eleccion", "votacion", "congreso"],
        "unidos": ["estados unidos", "ee.uu", "eleccion", "votacion"],
        "inflacion": ["inflacion", "caro", "carestia", "ipc", "precio", "subida precios", "precios"],
        "precio": ["inflacion", "caro", "carestia", "ipc", "precio", "subida precios"],
        "caro": ["inflacion", "caro", "carestia", "ipc", "precio", "subida precios"],
        "bolsa": ["bolsa", "mercado", "cotizacion", "valores", "renta variable", "ibex", "cotizacion ibex"],
        "cotizacion": ["bolsa", "mercado", "cotizacion", "valores", "renta variable", "ibex"],
        "ibex": ["bolsa", "mercado", "cotizacion", "valores", "renta variable", "ibex"],
        "bitcoin": ["bitcoin", "cripto", "moneda digital", "activo cripto", "token", "blockchain"],
        "cripto": ["bitcoin", "cripto", "moneda digital", "activo cripto", "token"],
        "moneda": ["bitcoin", "cripto", "moneda digital", "activo cripto"],
        "digital": ["bitcoin", "cripto", "moneda digital", "activo cripto"],
        "ucrania": ["ucrania", "rusia", "frente este", "alto el fuego", "ceasefire", "conflicto"],
        "rusia": ["ucrania", "rusia", "frente este", "alto el fuego", "ceasefire", "conflicto"],
        "frente": ["ucrania", "rusia", "frente este", "alto el fuego", "ceasefire", "conflicto"],
        "espana": ["espana", "la roja", "equipo nacional", "clasificatoria"],
    }

    variantes_por_termino = []
    for t in terminos:
        variantes = sinonimos.get(t, [t])
        variantes_por_termino.append(variantes)

    likes = [f"%{v}%" for variantes in variantes_por_termino for v in variantes]

    terminos_consulta = list(terminos)
    resultados = _ejecutar_consulta(terminos_consulta, likes, limite, idioma=idioma)

    # Expansión automática (Bloque 2 - Sol #2): si 0 resultados, ampliar por categoría
    if not resultados and categoria != "undetected":
        expandidos = expandir(pregunta, categoria)
        exp_likes = [f"%{v}%" for v in expandidos]
        resultados = _ejecutar_consulta(expandidos, exp_likes, limite, min_coinc=1, idioma=idioma)

    if not resultados and len(terminos_consulta) > 1:
        for fallback in [terminos_consulta[:1], terminos_consulta[-1:]]:
            resultados = _ejecutar_consulta(fallback, likes, limite, idioma=idioma)
            if resultados:
                break
    return resultados
