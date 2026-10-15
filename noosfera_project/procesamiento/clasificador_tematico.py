from __future__ import annotations
import unicodedata
from typing import Any, Optional
import sys
from pathlib import Path

# Importar scoring emocional de la versión B
from noosfera_project.procesamiento.scoring_emocional import (
    calcular_score_emocional,
    calcular_confianza,
)

# Clasificador temático ampliado (Bloque 1 - Sol prioridad #1)
# Categorías core del corpus de Noósfera con pesos por token.

CATEGORIAS = {
    "guerra_ucrania": {
        "tokens": ["ucrania", "rusia", "kiev", "putin", "zelenski", "invasion", "donbas", "kharkiv", "batalla", "frente", "ofensiva", "conflicto", "guerra"],
        "frases": ["frente este", "alto el fuego", "ceasefire"],
        "peso": 1.0,
    },
    "bitcoin": {
        # `mineria` se movió a metales_industriales (sentido literal: extracción
        # de mineral). La minería de bitcoin se captura por "bitcoin" mismo.
        "tokens": ["bitcoin", "btc", "cripto", "blockchain", "ethereum", "satoshi", "wallet", "altcoin", "token", "exchange cripto", "stablecoin", "halving"],
        "frases": ["moneda digital", "activo cripto"],
        "peso": 1.0,
    },
    "elecciones_eeuu": {
        # `congreso`/`senado` ya viven en politica_gobierno y los mundiales en
        # deportes: un token en dos categorías se resuelve por orden de
        # diccionario, que es arbitrario. Detectado por guardian_categorias.
        "tokens": ["ee.uu", "estados unidos", "biden", "trump", "casa blanca", "voto", "capitolio", "us-wahlen", "senat", "abstimmung", "us elections", "midterms", "primarias", "electoral college", "pennsylvania", "arizona", "georgia run-off"],
        "frases": ["estados unidos", "casa blanca", "ee.uu"],
        "peso": 1.0,
    },
    "inflacion_europa": {
        "tokens": ["europa", "inflacion", "bce", "tipos de interes", "euro", "ecb", "draghi", "energia", "ipc", "recesion", "deuda", "estancamiento", "deflacion", "quiebra"],
        "frases": ["tipos de interes", "subida precios", "eurozona"],
        "peso": 1.0,
    },
    "sp500": {
        "tokens": ["s&p", "sp500", "sp 500", "bolsa", "wall street", "nasdaq", "dow", "acciones", "mercado", "ibex"],
        "frases": ["wall street", "renta variable", "cotizacion ibex"],
        "peso": 1.0,
    },
    "inteligencia_artificial": {
        # `robot` se movió a robotica (categoría dedicada); aquí queda la
        # palabra compuesta. Detectado por guardian_categorias.
        "tokens": ["ia", "inteligencia artificial", "ai", "chatgpt", "gpt", "modelo", "algoritmo", "neuronal", "automatizacion", "deep learning"],
        "frases": ["inteligencia artificial", "modelo de lenguaje", "aprendizaje automatico"],
        "peso": 1.0,
    },
    "politica_gobierno": {
        "tokens": ["gobierno", "congreso", "senado", "parlamento", "ministerio", "ley", "reforma", "presidente", "primer ministro", "oposicion", "partido", "votacion", "decreto", "urnas", "campana", "campaña", "legislatura", "diputado", "coalicion", "coalición", "elecciones", "referéndum", "referéndum", "alcalde", "alcaldia", "ayuntamiento", "candidato", "investidura"],
        "frases": ["proyecto de ley", "sede de gobierno", "cambio de gabinete"],
        "peso": 1.0,
    },
    "migracion": {
        "tokens": ["migracion", "migrante", "refugiado", "frontera", "asilo", "exilio", "desplazado", "inmigracion", "extranjero"],
        "frases": ["crisis migratoria", "politica de fronteras", "centro de acogida"],
        "peso": 1.0,
    },
    "clima_medioambiente": {
        "tokens": ["clima", "cambio climatico", "sequia", "inundacion", "terremoto", "huracan", "calentamiento", "medioambiente", "ecologia", "incendio", "tormenta", "ola de calor"],
        "frases": ["cambio climatico", "emergencia climatica", "catastrofe natural"],
        "peso": 1.0,
    },
    "tecnologia_cuantica": {
        "tokens": ["quantum", "cuantica", "cuantico", "qubit", "supercomputacion", "computacion cuantica"],
        "frases": ["computacion cuantica", "ventaja cuantica"],
        "peso": 1.0,
    },
    "energia": {
        # `solar` y `eolica` se movieron a energia_renovable: estaban en las
        # dos categorías y "paneles solares" acaba en la genérica. La regla
        # es que un token vive en UNA sola categoría.
        "tokens": ["petrolero", "gasoducto", "central termica", "combustible fosil", "tarifa luz", "factura electrica", "mercado electrico"],
        "frases": ["factura de la luz", "tarifa electrica", "mercado electrico"],
        "peso": 1.0,
    },
    "deportes": {
        "tokens": ["mundial", "nba", "mlb", "nhl", "nfl", "super bowl", "world series", "stanley cup", "champions league", "champions", "premier league", "baloncesto", "basketball", "lakers", "celtics", "warriors", "dodgers", "yankees", "astros", "oilers", "panthers", "avalanche", "chiefs", "bills", "49ers", "bucks", "real madrid", "manchester city", "barcelona", "mls", "tenis", "wimbledon", "open de", "formula 1", "f1", "gp", "olimpiadas", "jjoo", "atletismo", "ciclismo", "tour de francia", "boxeo", "ufc", "liga", "clasificatoria", "final", "campeon", "campeona", "campeonato", "arsenal", "mclaren", "verstappen", "city", "sevilla", "betis", "espanyol", "tennis", "leverkusen", "chelsea", "liverpool", "united", "atletico", "juventus", "psg", "inter", "napoli", "monaco", "ferrari", "hamilton", "norris", "russell", "sainz", "gasly", "albon", "mercedes", "red bull", "racing", "bayern", "dortmund", "benfica", "porto", "ajax", "feyenoord", "galatasaray", "river", "boca", "flamengo", "palmeiras", "santos", "corinthians", "cruzeiro", "fluminense", "botafogo", "athletic", "villarreal", "valencia", "real sociedad", "celta", "osasuna", "mallorca", "getafe", "girona", "cadiz", "alaves", "rayo", "granada", "valladolid", "zaragoza", "sporting", "braga", "rangers", "celtic", "twente", "utrecht", "az", "espana", "seleccion", "roja", "la roja", "equipo nacional", "coupe du monde", "copa do mundo", "weltmeisterschaft", "les bleus", "equipe de france", "deutsche nationalmannschaft", "selecao", "die mannschaft", "wm"],
        "frases": ["world series", "stanley cup", "super bowl", "champions league", "premier league", "final nba", "final de la nba"],
        "peso": 1.0,
    },
    "ciberseguridad": {
        "tokens": ["ciberseguridad", "ciber", "seguridad", "hacker", "malware", "ransomware", "phishing", "brecha", "vulnerabilidad", "exploit", "firewall", "ddos", "botnet", "criptografia", "cloud", "data", "dataset", "iot", "startup", "open source", "devops", "kubernetes", "docker", "linux", "python", "software", "saas", "servidor", "base de datos", "red", "protocolo", "autenticacion"],
        "frases": ["ciberseguridad", "seguridad informatica", "api cloud"],
        "peso": 1.0,
    },
    "seguridad_orden": {
        "tokens": ["atentado", "alerta", "corte", "rescate", "protesta", "alarma", "accidente", "crisis", "orden publico", "disturbios", "motin", "emergencia", "evacuacion", "explosion", "bomba", "tiroteo", "secuestro", "asalto"],
        "frases": ["orden publico", "estado de alarma"],
        "peso": 1.0,
    },
    # Añadidas en 0.2.2-dev con base en el corpus: epidemia/pandemia (33 docs)
    # caían en clima_medioambiente por "emergencia"/"alerta", y apagón (12) no
    # tenía dónde ir. Sanidad e infraestructura son señales distintas.
    "sanidad": {
        "tokens": ["epidemia", "pandemia", "brote", "contagio", "contagios", "vacuna", "vacunacion", "virus", "hospital", "hospitales", "sistema sanitario", "sanidad", "enfermedad", "muertes", "fallecidos", "cuarentena", "mascarilla", "sintomas", "oms", "salud publica"],
        "frases": ["crisis sanitaria", "salud publica", "sistema sanitario"],
        "peso": 1.0,
    },
    "infraestructura": {
        # `metro` y `tren` pasaron a transporte: un token en dos categorías se
        # lo lleva la más específica. Detectado por guardian_categorias.
        "tokens": ["apagon", "apagones", "electricidad", "suministro", "agua potable", "carretera", "autopista", "puente", "infraestructura", "corte de luz", "desabastecimiento", "colapso energetico", "red electrica"],
        "frases": ["corte de luz", "red electrica", "caida del sistema"],
        "peso": 1.0,
    },
    # ── Materias primas y energía (0.2.2-dev) ──────────────────────────────
    # Pedidas por el usuario. Verificado: ninguna categoría existente las
    # cubre —"el oro y el platino" caía en undetected, "petróleo y gasolina"
    # en la categoría genérica `energia`. Son señales distintas: metal raro,
    # commodity energética y tecnología de suministro no se mueven igual.
    "metales_preciosos": {
        # Los elementos (oro, plata, platino, paladio) se movieron a
        # elementos_criticos, que unifica toda la tabla periódica.
        "tokens": ["metales preciosos", "onza", "lingote", "bullion", "kilate", "refineria de oro"],
        "frases": ["metales preciosos", "precio del oro", "reservas de oro"],
        "peso": 1.0,
    },
    "metales_industriales": {
        # Los elementos (cobre, zinc, aluminio, litio, tierras raras…) se
        # movieron a elementos_criticos.
        "tokens": ["fundicion", "aleacion", "chatarrera", "procesado de metal", "industria metalurgica"],
        "frases": ["industria metalurgica", "fundicion de metales"],
        "peso": 1.0,
    },
    "energia_petroleo_gas": {
        "tokens": ["petroleo", "crudo", "gasolina", "diesel", "gas natural", "barril", "opep", "refineria", "oleoducto", "gnl", "carburante", "combustible"],
        "frases": ["precio del petroleo", "gas natural", "corte de suministro"],
        "peso": 1.0,
    },
    "energia_renovable": {
        # `bateria` se movió a tecnologia_consumo: "bateria de una semana" es
        # autonomía de móvil, no almacenamiento energético. Detectado al probar.
        "tokens": ["panel solar", "solar", "fotovoltaica", "eolica", "aerogenerador", "renovable", "renovables", "almacenamiento energetico", "hidrogeno verde", "biomasa", "geotermica", "autoconsumo"],
        "frases": ["energia renovable", "panel solar", "transicion energetica"],
        "peso": 1.0,
    },
    "semiconductores": {
        "tokens": ["chip", "chips", "semiconductor", "semiconductores", "procesador", "procesadores", "fotonico", "fotonica", "oblea", "litografia", "foundry", "tsmc", "gpu", "cpu"],
        "frases": ["crisis de chips", "procesador fotonico", "cadena de suministro de chips"],
        "peso": 1.0,
    },
    "agricultura": {
        "tokens": ["trigo", "maiz", "cebada", "arroz", "soja", "cosecha", "cereal", "fertilizante", "ganado", "granja", "agricultura", "sequia agricola", "acuerdo granos"],
        "frases": ["cosecha de trigo", "precio de alimentos", "crisis alimentaria"],
        "peso": 1.0,
    },
    # ── Segunda hornada (0.2.2-dev) ────────────────────────────────────────
    # Verificado antes de añadir: 17 de 24 textos de prueba caían en
    # undetected, y había falsos positivos graves —"narcotrafico" iba a
    # ciberseguridad (por el token 'red') y "encuentro diplomatico" a deportes.
    "justicia": {
        "tokens": ["tribunal", "juez", "fiscal", "juicio", "sentencia", "condena", "prision", "imputado", "corrupcion", "soborno", "audiencia", "suprema", "proceso judicial", "recursos"],
        "frases": ["tribunal supremo", "prision provisional", "caso de corrupcion"],
        "peso": 1.0,
    },
    "laboral": {
        "tokens": ["huelga", "sindicato", "sindicatos", "convenio", "salario", "salarios", "despido", "despidos", "paro", "empleo", "reforma laboral", "pension", "pensiones", "negociacion colectiva"],
        "frases": ["huelga general", "reforma laboral", "subida salarial"],
        "peso": 1.0,
    },
    "vivienda": {
        "tokens": ["vivienda", "alquiler", "alquileres", "hipoteca", "inmobiliaria", "casero", "okupa", "desahucio", "urbanismo", "suelo", "promocion inmobiliaria"],
        "frases": ["precio de la vivienda", "burbuja inmobiliaria", "mercado del alquiler"],
        "peso": 1.0,
    },
    "transporte": {
        "tokens": ["aeropuerto", "vuelo", "vuelos", "aerolinea", "aviacion", "pilotos", "autobus", "metro", "ferrocarril", "tren", "taxi", "peaje", "trafico", "congestion", "aviacion civil"],
        "frases": ["huelga de pilotos", "transporte publico", "cierre del espacio aereo"],
        "peso": 1.0,
    },
    "ciencia_espacio": {
        "tokens": ["nasa", "spacex", "telescopio", "webb", "cohete", "satelite", "orbita", "mision espacial", "astronauta", "lanzamiento", "estacion espacial", "marte"],
        "frases": ["mision espacial", "agencia espacial", "lanzamiento del cohete"],
        "peso": 1.0,
    },
    "educacion": {
        "tokens": ["profesor", "profesores", "alumno", "alumnos", "universidad", "selectividad", "beca", "becas", "escuela", "colegio", "educacion", "currículo", "eba", "fp"],
        "frases": ["huelga educativa", "recorte de becas", "sistema educativo"],
        "peso": 1.0,
    },
    "crimen_organizado": {
        "tokens": ["narcotrafico", "mafia", "cocaina", "heroina", "cartel", "extorsion", "blanqueo", "capo", "camello", "aluvion", "banda", "policia judicial"],
        "frases": ["crimen organizado", "red de narcotrafico", "operacion policial"],
        "peso": 1.0,
    },
    "relaciones_internacionales": {
        "tokens": ["otan", "naciones unidas", "onu", "embajada", "embajador", "diplomatico", "diplomacia", "sanciones", "cumbre", "acuerdo bilateral", "tratado", "geopolitica"],
        "frases": ["relaciones internacionales", "acuerdo diplomatico", "sanciones economicas"],
        "peso": 1.0,
    },
    # ── Tercera hornada (0.2.2-dev) ────────────────────────────────────────
    # Medido antes de añadir: 15 de 24 textos de prueba caían en undetected.
    # También aparecieron falsos positivos que estas categorías corrigen:
    # "bateria de una semana" iba a energia_renovable (token 'bateria'),
    # "deficit" a deportes y "turistas" a deportes.
    "cultura": {
        "tokens": ["pelicula", "cine", "festival", "taquilla", "serie", "streaming", "musica", "concierto", "disco", "novela", "libro", "teatro", "videojuego", "gamer", "actor", "director"],
        "frases": ["taquilla de cine", "festival de cine", "plataforma de streaming"],
        "peso": 1.0,
    },
    "religion": {
        "tokens": ["iglesia", "papa", "vaticano", "obispo", "catolico", "musulman", "mezquita", "religion", "religioso", "laicismo", "aborto", "eutanasia", "culto"],
        "frases": ["iglesia catolica", "libertad de culto", "estado laico"],
        "peso": 1.0,
    },
    "biodiversidad": {
        "tokens": ["biodiversidad", "especie", "especies", "lince", "extincion", "reserva marina", "ecosistema", "fauna", "flora", "conservacion", "parque nacional", "deforestacion"],
        "frases": ["perdida de biodiversidad", "especie en peligro", "reserva natural"],
        "peso": 1.0,
    },
    "demografia": {
        "tokens": ["natalidad", "nacimientos", "despoblacion", "envejecimiento", "pensionistas", "emigracion", "censo", "poblacion activa", "esperanza de vida", "pirámide poblacional"],
        "frases": ["tasa de natalidad", "la espana vacia", "envejecimiento de la poblacion"],
        "peso": 1.0,
    },
    "tecnologia_consumo": {
        "tokens": ["smartphone", "movil", "telefono", "app", "aplicacion", "wearable", "tablet", "portatil", "gadget", "descargas", "android", "ios", "bateria"],
        "frases": ["tienda de aplicaciones", "telefono movil", "dispositivo movil"],
        "peso": 1.0,
    },
    "salud_mental": {
        "tokens": ["ansiedad", "depresion", "suicidio", "salud mental", "psicologo", "psiquiatra", "estres", "burnout", "trastorno", "terapia"],
        "frases": ["salud mental", "lista de espera", "trastorno mental"],
        "peso": 1.0,
    },
    "turismo": {
        "tokens": ["turismo", "turista", "turistas", "hotel", "hoteles", "llegadas", "pernoctacion", "vacaciones", "crucero", "alojamiento", "rent a car", "aeropuerto turistico"],
        "frases": ["llegada de turistas", "masificacion turistica", "temporada turistica"],
        "peso": 1.0,
    },
    "deuda_publica": {
        "tokens": ["deuda publica", "prima de riesgo", "deficit", "superavit", "déficit", "bono", "letras del tesoro", "pib", "recaudacion", "presupuestos generales", "tijeretas"],
        "frases": ["deuda publica", "prima de riesgo", "presupuestos generales del estado"],
        "peso": 1.0,
    },
    # ── Cuarta hornada: tecnología de frontera (0.2.2-dev) ─────────────────
    # Propuesta del subagente tecnólogo, filtrada por el guardián.
    # DESCARTADAS por colisión real:
    #   - baterias_almacenamiento: "bateria" vive en tecnologia_consumo y
    #     "almacenamiento energetico" en energia_renovable.
    #   - blockchain_web3: "ethereum"/"wallet"/"token" ya están en bitcoin.
    # Las demás usan compuestos ("coche autonomo", "internet satelital") para
    # no pisar categorías existentes.
    "robotica": {
        "tokens": ["robot", "robots", "robotica", "humanoide", "humanoides", "unitree", "cobot", "exoesqueleto", "automatizacion industrial", "pick and place", "brazo robotico", "robot colaborativo"],
        "frases": ["automatizacion industrial", "robot humanoide", "cadena de montaje"],
        "peso": 1.0,
    },
    "fusion_nuclear": {
        "tokens": ["fusion nuclear", "tokamak", "stellarator", "reactor de fusion", "plasma confinado", "helion", "energia de fusion", "ignicion fusion"],
        "frases": ["fusion nuclear", "reactor de fusion", "energia de fusion"],
        "peso": 1.0,
    },
    "vehiculos_autonomos": {
        # "tesla" suelto excluido a propósito: colisionaría con robotica.
        "tokens": ["coche autonomo", "conduccion autonoma", "robotaxi", "waymo", "autopilot", "lidar", "flota autonoma", "nivel de automatizacion"],
        "frases": ["coche autonomo", "conduccion autonoma", "robotaxi"],
        "peso": 1.0,
    },
    "realidad_extendida": {
        "tokens": ["realidad virtual", "realidad aumentada", "realidad mixta", "metaverso", "vision pro", "gafas inteligentes", "seguimiento ocular", "visor inmersivo", "casco de vr"],
        "frases": ["realidad virtual", "realidad aumentada", "realidad mixta"],
        "peso": 1.0,
    },
    "neurotecnologia": {
        # `chip cerebral` en frases: sin él, "chip" (semiconductores) gana y
        # el implante cerebral se clasifica como hardware.
        "tokens": ["interfaz cerebral", "neuralink", "neurotecnologia", "electroencefalograma", "marcapasos cerebral", "estimulacion cerebral", "implante cerebral", "ondas cerebrales", "neuroestimulador", "chip cerebral"],
        "frases": ["interfaz cerebro computadora", "implante cerebral", "estimulacion cerebral", "chip cerebral"],
        "peso": 1.0,
    },
    "fabricacion_aditiva": {
        "tokens": ["impresion 3d", "impresora 3d", "filamento", "fabricacion aditiva", "resina de impresion", "casa impresa", "prototipado rapido", "fresadora", "repuestos impresos"],
        "frases": ["impresion 3d", "fabricacion aditiva", "prototipado rapido"],
        "peso": 1.0,
    },
    "conectividad_satelital": {
        # "satelite" suelto excluido: vive en ciencia_espacio.
        "tokens": ["internet satelital", "constelacion de satelites", "starlink", "kuiper", "oneweb", "orbita baja", "latencia baja", "antena de bajo coste"],
        "frases": ["internet satelital", "constelacion de satelites", "orbita baja"],
        "peso": 1.0,
    },
    "biotecnologia": {
        # Sin fármacos GLP-1 (ozempic, wegovy): eso es sanidad, no biotec.
        "tokens": ["crispr", "edicion genetica", "terapia genica", "biologia sintetica", "senolitico", "longevidad", "celulas madre", "organo cultivado", "biohacking", "antienvejecimiento"],
        "frases": ["edicion genetica", "terapia genica", "biologia sintetica"],
        "peso": 1.0,
    },
    # ── Quinta hornada: malestar social (0.2.2-dev) ────────────────────────
    # Propuesta del subagente sociólogo. Tokens descartados por colisión:
    # pensiones (laboral), pensionistas (demografia), aborto (religion),
    # protesta (seguridad_orden), huelga (laboral).
    "brecha_generacional": {
        "tokens": ["boomers", "millennial", "millennials", "generacion z", "guerra generacional", "ok boomer", "generacion de cristal", "juventud precaria"],
        "frases": ["guerra generacional", "brecha generacional"],
        "peso": 1.0,
    },
    "desigualdad_social": {
        "tokens": ["desigualdad", "pobreza", "riqueza", "clases sociales", "elitismo", "privilegio", "brecha social", "ricos y pobres", "exclusion social"],
        "frases": ["desigualdad social", "brecha de clase", "concentracion de riqueza"],
        "peso": 1.0,
    },
    "endeudamiento_personal": {
        "tokens": ["prestamo", "prestamos", "deuda personal", "tarjeta de credito", "credito facil", "usura", "prestamo rapido", "minicredito", "aviso de embargo"],
        "frases": ["deuda personal", "tarjeta de credito", "credito facil"],
        "peso": 1.0,
    },
    "genero": {
        # Sin 'aborto' (religion) ni 'violencia de genero' para no pisar.
        "tokens": ["feminismo", "machismo", "patriarcado", "brecha de genero", "brecha salarial", "movimiento feminista", "techo de cristal"],
        "frases": ["movimiento feminista", "brecha salarial", "brecha de genero"],
        "peso": 1.0,
    },
    "discriminacion": {
        # Sin 'xenofobia' ni 'discriminacion' suelta: viven en migracion.
        "tokens": ["racismo", "supremacismo", "insultos racistas", "color de piel", "delito de odio", "delitos de odio", "discurso de odio", "segregacion"],
        "frases": ["discurso de odio", "delito de odio", "supremacismo"],
        "peso": 1.0,
    },
    "libertad_expresion": {
        "tokens": ["censura", "cancelacion", "libertad de expresion", "cancelado", "linchamiento publico", "mordaza", "silencio administrativo", "correccion politica"],
        "frases": ["libertad de expresion", "cultura de la cancelacion", "linchamiento publico"],
        "peso": 1.0,
    },
    "movilizacion_social": {
        # Sin 'protesta' ni 'huelga': viven en seguridad_orden y laboral.
        "tokens": ["manifestacion", "concentracion", "pancarta", "acampada", "cacerolada", "marcha", "asamblea vecinal", "plataforma ciudadana"],
        "frases": ["movilizacion social", "asamblea vecinal", "marcha ciudadana"],
        "peso": 1.0,
    },
    # ── Sexta hornada: economía y mercados (0.2.2-dev) ─────────────────────
    # Propuesta del subagente analista de mercados (verificó contra el
    # clasificador real). Token descartado por colisión:
    #   'tarjeta de credito' vive en endeudamiento_personal.
    # 'yuan' (4 letras) va en TOKENS_CORTOS para exigir palabra completa.
    "banca_credito": {
        "tokens": ["banco", "banca", "banquero", "entidad financiera", "cajero automatico", "deposito bancario", "cuenta corriente", "fuga de depositos", "corralito", "rescate bancario", "banca en la sombra", "sucursal", "credito bancario", "santander", "caixabank", "sabadell", "liquidez bancaria", "comision bancaria"],
        "frases": ["fuga de depositos", "rescate bancario", "entidad financiera"],
        "peso": 1.0,
    },
    "divisas": {
        "tokens": ["dolar", "divisa", "divisas", "tipo de cambio", "devaluacion", "dolarizacion", "cotizacion", "fortaleza del dolar", "reservas de divisas", "eurodolar"],
        "frases": ["tipo de cambio", "fortaleza del dolar", "reservas de divisas"],
        "peso": 1.0,
    },
    "comercio_exterior": {
        # 'cadena de suministro' descartada: ya vive en semiconductores.
        "tokens": ["arancel", "aranceles", "guerra comercial", "exportacion", "exportaciones", "importacion", "importaciones", "balanza comercial", "deficit comercial", "aduana", "contenedor", "contenedores", "flete", "fletes", "naviera", "portacontenedores", "canal de suez", "canal de panama", "cuello de botella", "embargo comercial"],
        "frases": ["guerra comercial", "balanza comercial", "canal de suez"],
        "peso": 1.0,
    },
    "insolvencias": {
        "tokens": ["concurso de acreedores", "insolvencia", "insolvencias", "bancarrota", "suspension de pagos", "moratoria de pagos", "refinanciacion", "reestructuracion", "impago de proveedores", "cierre de fabrica", "acreedores", "expediente de regulacion"],
        "frases": ["concurso de acreedores", "suspension de pagos", "impago de proveedores"],
        "peso": 1.0,
    },
    "materiales_industriales_basicos": {
        # Sin wolframio/antimonio/galio/germanio (metales) ni grafito ni
        # manganeso: viven en elementos_criticos.
        "tokens": ["acero", "hormigon", "cemento", "clinker", "alumina", "chatarra", "celulosa", "pasta de papel", "carton", "polimero", "polimeros", "sosa caustica", "amonio", "fosfato", "potasa", "vidrio"],
        "frases": ["acero y cemento", "pasta de papel", "polimeros industriales"],
        "peso": 1.0,
    },
    "escasez_agua": {
        "tokens": ["embalse", "embalses", "pantano", "restriccion de agua", "restricciones hidricas", "sequia hidrica", "desaladora", "desalacion", "canal de riego", "acuifero", "corte de agua", "falta de agua"],
        "frases": ["restriccion de agua", "sequia hidrica", "nivel de los embalses"],
        "peso": 1.0,
    },
    "burbujas_mercado": {
        "tokens": ["burbuja", "sobrevaloracion", "volatilidad", "capitalizacion bursatil", "apalancamiento", "liquidacion forzosa", "venta en corto", "correccion bursatil", "burbuja financiera", "comprar la caida", "inversor minorista", "margin call"],
        "frases": ["burbuja financiera", "comprar la caida", "liquidacion forzosa"],
        "peso": 1.0,
    },
    "automocion": {
        "tokens": ["automocion", "fabrica de coches", "fabricante de automoviles", "matriculacion", "matriculaciones", "concesionario", "concesionarios", "coche electrico", "plantilla de la fabrica", "produccion de coches", "volkswagen", "stellantis"],
        "frases": ["fabrica de coches", "plantilla de la fabrica", "venta de coches"],
        "peso": 1.0,
    },
    "consumo_minorista": {
        "tokens": ["cesta de la compra", "supermercado", "supermercados", "no llegar a fin de mes", "morosidad", "credito al consumo", "pagar a plazos", "ticket medio", "ventas minoristas", "comercio local", "tienda de barrio", "rebajas", "poder adquisitivo", "ahorro de las familias"],
        "frases": ["cesta de la compra", "no llegar a fin de mes", "poder adquisitivo"],
        "peso": 1.0,
    },
    # ── Séptima hornada: tensión geopolítica (0.2.2-dev) ───────────────────
    # Propuesta del subagente reencuadrado como "análisis de conversación
    # pública": señales observables (cambios de tono, regiones que ganan
    # atención), NO capacidades militares.
    #
    # DESCARTADA 'rutas_maritimas': se solapaba con comercio_exterior
    # (canal de suez, canal de panama, fletes) y transporte (peaje).
    # Tokens descartados por colisión: 'alto el fuego' (guerra_ucrania).
    "estrecho_taiwan": {
        "tokens": ["taiwan", "taipei", "pekin", "kaohsiung", "estrecho de taiwan", "vuelos cancelados", "rutas aereas desviadas", "una sola china", "isla de formosa"],
        "frases": ["estrecho de taiwan", "una sola china", "isla de formosa"],
        "peso": 1.0,
    },
    "mar_sur_china": {
        "tokens": ["filipinas", "vietnam", "manila", "hanoi", "brunei", "malasia", "mar del sur", "spratly", "paracelso", "guardacostas", "permiso de pesca", "choque de barcos"],
        "frases": ["mar del sur", "islas spratly", "islas paracelso"],
        "peso": 1.0,
    },
    "peninsula_coreana": {
        "tokens": ["corea del norte", "corea del sur", "pyongyang", "peninsula coreana", "desertores", "panfletos"],
        "frases": ["corea del norte", "corea del sur", "peninsula coreana"],
        "peso": 1.0,
    },
    "oriente_medio": {
        "tokens": ["israel", "gaza", "franja de gaza", "libano", "beirut", "tel aviv", "rehenes", "espacio aereo cerrado", "vuelos de repatriacion", "alerta en embajadas"],
        "frases": ["franja de gaza", "alto el fuego en oriente", "vuelos de repatriacion"],
        "peso": 1.0,
    },
    "balcanes_kosovo": {
        "tokens": ["kosovo", "serbia", "belgrado", "pristina", "norte de kosovo", "balcanes", "puestos fronterizos", "barricadas", "protestas en el norte"],
        "frases": ["norte de kosovo", "puestos fronterizos", "tension en los balcanes"],
        "peso": 1.0,
    },
    "sahel": {
        # 'uranio' movido a elementos_criticos (es un elemento, no un tema
        # regional: la fricción del uranio en el Sahel se captura por los
        # tokens de la región).
        "tokens": ["burkina faso", "niamey", "bamako", "sahel", "golpe de estado", "grupos armados", "retirada de la mision", "convoyes", "yacimiento de uranio"],
        "frases": ["sahel", "golpe de estado", "retirada de la mision"],
        "peso": 1.0,
    },
    "region_polar": {
        # 'artico' renombrado a region_polar para no solaparse con clima.
        "tokens": ["region polar", "groenlandia", "svalbard", "paso del noreste", "ruta del norte", "mar polar", "rompehielos", "yacimientos polares"],
        "frases": ["paso del noreste", "ruta del norte", "region polar"],
        "peso": 1.0,
    },
    "dedolarizacion": {
        "tokens": ["brics", "dedolarizacion", "moneda comun", "banco de los brics", "comercio sin dolar", "salir del dolar", "facturacion en yuanes"],
        "frases": ["comercio sin dolar", "dedolarizacion", "banco de los brics"],
        "peso": 1.0,
    },
    "cachemira": {
        "tokens": ["cachemira", "nueva delhi", "rio indo", "linea de control", "estatus especial", "toque de queda", "puestos de control"],
        "frases": ["linea de control", "estatus especial", "rio indo"],
        "peso": 1.0,
    },
    # ── Octava hornada: micro-experiencia de la gente común (0.2.2-dev) ────
    # Propuesta del subagente OSINT. Su criterio: el catálogo cubre bien lo
    # macro, pero falla en lo que la gente sufre a diario y rumorea en foros.
    #
    # DESCARTADA 'comercio_global_aranceles': se solapaba con comercio_exterior
    # (arancel, aduana, exportacion, balanza comercial, embargo comercial).
    # Token descartado por colisión: 'cuello de botella' (comercio_exterior).
    "suministros_escasez": {
        # 'mineral critico' movido a elementos_criticos.
        "tokens": ["escasez", "rotura de stock", "estante vacio", "racionamiento", "retraso de entregas", "reventa ilegal", "acaparamiento", "falta de stock", "agotado en tienda", "sin existencias", "desabastecido", "reserva estrategica", "no hay stock"],
        "frases": ["rotura de stock", "falta de stock", "reserva estrategica"],
        "peso": 1.0,
    },
    "salud_cronica": {
        # Distinta de sanidad (institucional) y salud_mental (psicológica):
        # aquí es la dolencia sistémica que la gente cuenta en foros.
        "tokens": ["microbiota", "microbiota intestinal", "autoinmune", "tiroides", "hashimoto", "sindrome metabolico", "resistencia a la insulina", "inflamacion cronica", "fatiga cronica", "sindrome postviral", "disbiosis", "fibromialgia", "colon irritable", "celiaco", "dolor cronico", "salud intestinal", "prebiotico", "probiotico", "medicina preventiva"],
        "frases": ["fatiga cronica", "sindrome postviral", "enfermedad autoinmune"],
        "peso": 1.0,
    },
    "movilidad_urbana": {
        "tokens": ["patinete electrico", "carril bici", "bicicleta compartida", "zona de bajas emisiones", "peatonalizacion", "calle peatonal", "calle tranquila", "contaminacion del aire", "calidad del aire", "boina de contaminacion", "dioxido de nitrogeno", "radar de velocidad", "aparcamiento regulado", "carril bus", "bache en la calle", "acera rota", "cruce peligroso"],
        "frases": ["zona de bajas emisiones", "calidad del aire", "calle peatonal"],
        "peso": 1.0,
    },
    "conectividad_caidas": {
        "tokens": ["fibra optica", "fibra simetrica", "cobertura de datos", "caida de servicio", "saturacion de red", "latencia de red", "portabilidad de linea", "roaming de datos", "torre de antena", "antena de telefonia", "sin senal", "se corto la luz", "sin conexion", "wifi publico", "cobertura 5g", "torre 5g", "antena 5g", "conexion lenta", "se cayo el servicio", "sin cobertura"],
        "frases": ["caida de servicio", "sin cobertura", "cobertura 5g"],
        "peso": 1.0,
    },
    "privacidad_vigilancia": {
        "tokens": ["privacidad digital", "cifrado de extremo a extremo", "vigilancia masiva", "gran hermano", "reconocimiento facial", "rastreo de datos", "identidad digital", "fuga de datos", "perfilado de usuarios", "consentimiento de datos", "anonimato en linea", "rastreo de ubicacion", "publicidad dirigida", "proteccion de datos", "app espia"],
        "frases": ["vigilancia masiva", "fuga de datos", "privacidad digital"],
        "peso": 1.0,
    },
    "precariedad_plataforma": {
        # Complementa laboral (mercado y regulación) con la vivencia del
        # trabajador de plataforma.
        "tokens": ["trabajo de reparto", "economia de encargo", "reparto a domicilio", "falso autonomo", "contrato cero horas", "trabajo precario", "jornada de cuatro dias", "teletrabajo forzoso", "nomina congelada", "trabajo a destajo", "plus de nocturnidad", "baja laboral", "excedencia forzosa", "sobrecarga de trabajo", "acoso laboral", "sueldo congelado", "trabajo extra no pagado", "jornada partida", "trabajador quemado"],
        "frases": ["falso autonomo", "contrato cero horas", "trabajador quemado"],
        "peso": 1.0,
    },
    "mineria_recursos": {
        # El lenguaje de la extracción y sus fricciones, distinto de los
        # metales como commodity.
        "tokens": ["pozo de mina", "refinado de mineral", "escorias mineras", "relave minero", "mina abandonada", "extraccion de mineral", "reserva de mineral", "concesion minera", "cantera", "procesamiento de mineral", "prospeccion minera", "vertido minero", "agua de mina", "mina ilegal", "extraccion informal", "fiebre minera", "yacimiento agotado"],
        "frases": ["mina ilegal", "vertido minero", "yacimiento agotado"],
        "peso": 1.0,
    },
    # ── Novena hornada: tabla periódica (0.2.2-dev) ────────────────────────
    # Petición del usuario: cubrir la tabla periódica completa, no solo
    # tierras raras. Antes los elementos vivían sueltos en metales_preciosos,
    # metales_industriales, semiconductores, materiales_industriales_basicos,
    # sahel y suministros_escasez, y competían con el resto.
    # Aquí se unifican TODOS en una sola categoría con nombre propio.
    # Los 73 tokens vienen de procesamiento/tabla_periodica.py.
    "elementos_criticos": {
        "tokens": [
            # Baterías y electromovilidad
            "litio", "cobalto", "niquel", "manganeso", "grafito", "sodio",
            "fosforo", "hierro",
            # Tierras raras (17)
            "lantano", "cerio", "praseodimio", "neodimio", "prometio",
            "samario", "europio", "gadolinio", "terbio", "disprosio",
            "holmio", "erbio", "tulio", "iterbio", "lutecio", "escandio",
            "itrio",
            # Semiconductores y electrónica
            "silicio", "germanio", "galio", "arsenico", "indio",
            "antimonio", "telurio",
            # Metales industriales
            "cobre", "zinc", "aluminio", "estano", "plomo", "titanio",
            "cromo", "vanadio", "wolframio", "tantalio", "niobio",
            "circonio", "berilio", "magnesio",
            # Metales preciosos
            "oro", "plata", "platino", "paladio", "rodio", "iridio",
            "osmio", "rutenio",
            # Energía y nuclear
            "uranio", "torio", "plutonio", "deuterio", "tritio",
            "helio", "hidrogeno",
            # Frases que la gente usa como una sola unidad. Van como TOKEN
            # (no solo como frase) para que puntúen igual: en empate con
            # "exportacion" la frase perdía por orden de diccionario.
            "tierras raras", "mineral critico", "material critico",
            # "bateria" vive en tecnologia_consumo (autonomía de móvil), pero
            # "baterias de litio" es materia prima: frase propia.
            "bateria de litio", "baterias de litio", "celda de bateria",
        ],
        "frases": [
            "tierras raras",
            "metales de tierras raras",
            "elementos de tierras raras",
            "mineral critico",
            "minerales criticos",
            "material critico",
            "materiales criticos",
            "cadena de suministro de minerales",
            "extraccion de litio",
            "mineria de litio",
            "refinado de cobalto",
            "tabla periodica",
        ],
        "peso": 1.0,
    },
}

UMBRAL = 0.10
PESO_TOKEN = 0.2

# Tokens de 2 letras legitimos (siglas). Para estos se exige palabra completa
# o descartan por substring: "varias" contine "ia" y falseaba inteligencia_artificial.
TOKENS_CORTOS = {
    "ia", "ai",
    # "boca" (Boca Juniors) matcheaba "desboca".
    "boca",
    # "az" (AZ Alkmaar) matcheaba "plaza": falso positivo confirmado.
    "az",
    # "yuan" (4 letras): lo advirtió el subagente de mercados.
    "yuan",
    # Geopolítica: los advirtió el subagente reencuadrado.
    "seul", "iran", "gaza",
    # Elementos de ≤4 letras (tabla_periodica): "oro" y "zinc" son los
    # que han dado falsos positivos por subcadena. El guardián verifica.
    "oro", "zinc", "hierro",
}


def _contiene_palabra(t: str, w: str) -> bool:
    """True si w aparece como palabra completa en t (no como subcadena).

    Fija el falso positivo: "varias" contine "ia", por lo que textos absurdos
    se clasificaban como inteligencia_artificial con score alto.
    """
    t = f" {t} "
    pos = t.find(f" {w} ")
    while pos != -1:
        final = pos + len(w) + 1
        if final >= len(t) or not (t[final].isalnum() or t[final] == "_"):
            return True
        pos = t.find(f" {w} ", final)
    return False


def _coincide(t: str, tok: str) -> bool:
    """Coincidencia de un token contra el texto normalizado.

    Los tokens de TOKENS_CORTOS exigen palabra completa; el resto admite
    substring para capturar variantes ("cripto" en "criptomonedas").

    La lista es explícita, no `len(tok) <= 3`: se probó eso y subía el
    undetected de 5 a 10 porque tokens legítimos de 3 letras ("ley", "red",
    "oro") dejaban de matchear. Solo entran los que han dado falsos
    positivos reales por subcadena.
    """
    if tok in TOKENS_CORTOS:
        return _contiene_palabra(t, tok)
    return tok in t


def _norm(texto: str) -> str:
    # minusculas + quita acentos (bug: 'automatizacion' no matcheaba 'automatización')
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).lower()


def clasificar(texto: str, emocion: Optional[float] = None) -> dict[str, Any]:
    """
    Clasifica texto con scoring emocional.
    
    Args:
        texto: texto a clasificar
        emocion: valor emocional opcional (-1 a +1)
    
    Returns:
        dict con categoria, score, signo, nivel, confianza, tokens
    """
    t = _norm(texto)
    mejores: list[tuple[str, float]] = []
    for cat, cfg in CATEGORIAS.items():
        toks = cfg["tokens"]
        fras = cfg.get("frases", [])
        coin_tok = sum(1 for tok in toks if _coincide(t, tok))
        coin_fra = sum(1 for fr in fras if fr in t)
        if coin_tok or coin_fra:
            # score por tokens (PESO_TOKEN c/u) + 0.15 por frase completa
            score = min(1.0, coin_tok * PESO_TOKEN + 0.15 * coin_fra)
            mejores.append((cat, round(score, 3)))
    mejores.sort(key=lambda x: x[1], reverse=True)

    # NOTA (0.2.2-dev): se probó un desempate por especificidad (ganaba la
    # categoría con menos tokens) y se REVIRTIÓ: no se activaba en los textos
    # multitema reales —"guerra_ucrania" ganaba por score, no por empate— y
    # desplazaba la distribución sin ganar claridad (bitcoin 62→58,
    # sp500 39→52). El scorer por tokens sigue siendo el criterio.
    categoria = mejores[0][0] if mejores and mejores[0][1] >= UMBRAL else "undetected"
    tokens = [tok for tok, _ in sorted(mejores, key=lambda x: x[1], reverse=True)[:5]]
    conf_base = mejores[0][1] if mejores else 0.0
    
    # Calcular scoring emocional con signo
    score_emocional = calcular_score_emocional(
        coincidencia=conf_base,
        recencia=0.5,  # valor por defecto
        diversidad=0.5,  # valor por defecto
        longitud=0.5,  # valor por defecto
        emocion_bruta=emocion,
    )
    
    return {
        "categoria": categoria,
        "score": score_emocional["score"],
        "signo": score_emocional["signo"],
        "nivel": score_emocional["nivel"],
        "confianza": score_emocional["score"],
        "tokens": tokens,
        "componentes": score_emocional["componentes"],
    }
