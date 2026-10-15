# Noósfera

Sistema de análisis de eventos emergentes locales.

## Versiones

### 0.2.1B (Actual)
**Soporte multilingüe**: ES, EN, FR, RU, ZH, AR
**Scoring emocional**: con signo (+/-)

Ver `RESUMEN_VERSION_B.md` para detalles completos.

### 0.2.1A (Congelada)
Versión de observación con 721 documentos.

## Instalación

```bash
pip install -e .
```

## Uso básico

```python
from noosfera_project.procesamiento.clasificador_tematico import clasificar

result = clasificar("bitcoin sube 10% hoy")
# {"categoria": "bitcoin", "score": 7.5, "signo": "+", ...}
```

## API

### Endpoints principales
- `GET /api/health` - Estado del sistema
- `GET /api/senales` - Senales emergentes
- `GET /api/fuentes` - Gestión de fuentes (versión B)

## Desarrollo

### Verificar versión B
```bash
python inicializar_version_b.py
```

### Ejecutar migración fuentes
```bash
python migracion_fuentes.py
```

### Ejecutar tests
```bash
pytest noosfera_project/tests/test_multilingue.py -v
```

## Documentación

- `CHANGELOG.md` - Historial de cambios
- `TAREAS_POST_VIAJE.md` - Tareas pendientes
- `CAMBIO_VERSION_B.md` - Detalles de la versión B
- `RESUMEN_VERSION_B.md` - Resumen rápido

## Créditos

Desarrollado por Hermes Agent (Nous Research)