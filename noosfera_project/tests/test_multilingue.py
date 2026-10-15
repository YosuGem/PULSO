"""
Tests multilingüe para Noósfera (versión B).

Verifica soporte ES/EN/FR/RU/ZH/AR.
"""
import pytest
import sys
from pathlib import Path

# Agregar versión B al path

from noosfera_project.procesamiento.normalizacion_multilingue import (
    normalizar,
    detectar_idioma,
    obtener_stopwords,
    STOPWORDS,
)


class TestDeteccionIdioma:
    """Tests para detección automática de idioma."""

    def test_detectar_espanol(self):
        assert detectar_idioma("hola mundo") == "es"
        assert detectar_idioma("el gobierno anuncia") == "es"

    def test_detectar_ingles(self):
        assert detectar_idioma("hello world") == "en"
        assert detectar_idioma("the government announces") == "en"

    def test_detectar_frances(self):
        assert detectar_idioma("le gouvernement annonce") == "fr"
        assert detectar_idioma("bonjour le monde") == "fr"

    def test_detectar_chino(self):
        assert detectar_idioma("你好世界") == "zh"

    def test_detectar_arabe(self):
        assert detectar_idioma("مرحبا بالعالم") == "ar"

    def test_detectar_ruso(self):
        assert detectar_idioma("привет мир") == "ru"


class TestNormalizacion:
    """Tests para normalización multilingüe."""

    def test_normalizar_es(self):
        result = normalizar("La IA va a cambiar el mundo", "es")
        assert "cambiar" in result
        assert "ia" in result

    def test_normalizar_en(self):
        result = normalizar("The AI will change the world", "en")
        assert "camb" in result or "chang" in result or "world" in result

    def test_normalizar_fr(self):
        result = normalizar("L'IA changera le monde", "fr")
        assert len(result) > 0

    def test_normalizar_vacio(self):
        assert normalizar("") == []
        assert normalizar(None) == []

    def test_normalizar_con_stopwords(self):
        # Las stopwords no deben aparecer
        result = normalizar("el la los las un una", "es")
        assert len(result) == 0


class TestStopwords:
    """Tests para stopwords por idioma."""

    def test_stopwords_es_existen(self):
        assert "es" in STOPWORDS
        assert "el" in STOPWORDS["es"]
        assert "la" in STOPWORDS["es"]

    def test_stopwords_en_existen(self):
        assert "en" in STOPWORDS
        assert "the" in STOPWORDS["en"]
        assert "a" in STOPWORDS["en"]

    def test_stopwords_fr_existen(self):
        assert "fr" in STOPWORDS
        assert "le" in STOPWORDS["fr"]
        assert "la" in STOPWORDS["fr"]

    def test_stopwords_ru_existen(self):
        assert "ru" in STOPWORDS
        assert "и" in STOPWORDS["ru"]

    def test_stopwords_zh_existen(self):
        assert "zh" in STOPWORDS
        assert "的" in STOPWORDS["zh"]

    def test_stopwords_ar_existen(self):
        assert "ar" in STOPWORDS
        assert "ال" in STOPWORDS["ar"]


class TestClasificacionMultilingue:
    """Tests para clasificación con texto multilingüe."""

    def test_clasificacion_es(self):
        from noosfera_project.procesamiento.clasificador_tematico import clasificar
        result = clasificar("bitcoin sube 10% hoy")
        assert result["categoria"] == "bitcoin"

    def test_clasificacion_es_con_emocion(self):
        from noosfera_project.procesamiento.clasificador_tematico import clasificar
        result = clasificar("bitcoin sube 10% hoy", emocion=0.8)
        assert result["signo"] == "+"

    def test_clasificacion_sin_emocion(self):
        from noosfera_project.procesamiento.clasificador_tematico import clasificar
        result = clasificar("bitcoin sube 10% hoy", emocion=None)
        assert "score" in result