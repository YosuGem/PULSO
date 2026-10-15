_MAX_PREGUNTA = 800
_MAX_LIMITE = 200
_MAX_HORIZONTE = 12
_MAX_EXPORTAR = 500

def sanitizar_enteros(valor, default, minimo, maximo):
    if valor is None:
        return default
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return default
    return max(minimo, min(maximo, n))

def limpiar_pregunta(pregunta: str) -> str:
    if pregunta is None:
        return ''
    p = str(pregunta).strip()
    return p[:_MAX_PREGUNTA]

def normalizar_eventos_params(params: dict) -> dict:
    limite = sanitizar_enteros(params.get('limite'), 10, 1, _MAX_LIMITE)
    return {'limite': limite}

def normalizar_senales_params(params: dict) -> dict:
    horizonte = sanitizar_enteros(params.get('horizonte'), 1, 1, _MAX_HORIZONTE)
    limite = sanitizar_enteros(params.get('limite'), 10, 1, _MAX_LIMITE)
    tema_filtro = params.get('tema')
    if tema_filtro is not None:
        tema = str(tema_filtro).strip()[:255]
    else:
        tema = None
    return {'horizonte': horizonte, 'limite': limite, 'tema': tema}

def normalizar_consultar_params(params: dict) -> dict:
    return {'pregunta': limpiar_pregunta(params.get('pregunta'))}

def normalizar_exportar_params(params: dict) -> dict:
    limite = sanitizar_enteros(params.get('limite'), 500, 1, _MAX_EXPORTAR)
    idioma = params.get('idioma')
    if idioma is not None:
        idioma = str(idioma).strip()[:8]
    fuente = params.get('fuente')
    if fuente is not None:
        fuente = str(fuente).strip()[:64]
    return {'limite': limite, 'idioma': idioma, 'fuente': fuente}
