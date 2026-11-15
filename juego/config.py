"""Opciones del juego: JSON con valores por defecto y escritura atómica."""
import json
import os

from . import rutas

POR_DEFECTO = {
    "vol_maestro": 0.8,
    "vol_efectos": 1.0,
    "vol_ambiente": 0.6,
    "vol_musica": 0.5,
    "vol_interfaz": 0.8,
    "musica_ambiente": True,
    "vol_ambiente_musical": 0.6,
    "pack_sonidos": "",            # subcarpeta de data/sonidos; vacío = los sonidos por defecto
    "igualar_volumen": True,       # lleva los sonidos cambiados al nivel de los originales
    "vol_sonidos": {},             # ajuste del jugador por sonido: nombre -> factor
    "adultos": False,
    "movimiento": "brujula",       # brujula | giro
    "conduccion": "asistida",      # asistida | libre
    "punteria": "completa",        # completa | manual
    "dificultad": "normal",        # facil | normal | dificil
    "direcciones": "cardinal",     # cardinal | reloj | relativa
    "anunciar_cruces": True,
    "anunciar_lugares": True,
    "anunciar_barrios": True,
    "anunciar_superficie": False,
    "piloto_gps": False,
    "frenada_auto": True,
    "sucesos": True,
    "mando_vibracion": True,
    "invulnerable": False,
    "sin_policia": False,
    "baliza": True,
    "gps_voz": True,
    "sonar": True,
    "semaforos": True,
    "localizador": True,
    "voz_sapi": False,
    "voz_velocidad": 0,            # con la voz de Windows: de -10 a 10
    "voz_tono": 0,                 # de -10 a 10
    "voz_volumen": 100,            # de 0 a 100
    "detalle_voz": "normal",       # cuánto explica el juego al hablar: mucho, normal o poco
    "vol_senales": 1.0,            # volumen propio de balizas, radar, tonos de puntería y sonidos de los lugares
    "red_upnp": True,              # al abrir tu partida, intentar abrir el puerto del router automáticamente
    "mod_enemigos": False,         # modificador: los enemigos aguantan la mitad más
    "mod_policia": False,          # modificador: los delitos cuentan la mitad más
    "mod_dinero": False,           # modificador: las misiones pagan la mitad
    "noche_por_pasos": True,       # contenido para adultos: la noche con alguien se juega paso a paso
    "multas": True,                # con poca búsqueda, al cogerte puedes pagar la multa o intentar un soborno
    "aviso_acierto": True,         # un toque y una vibración cuando das en el blanco
    "correr_alternar": False,      # correr con una pulsación de Mayúsculas en vez de mantenerla
    "tutorial_visto": False,
    "radar_filtro": "todo",
    "emisora": 1,
    "ia_activa": False,            # modo IA al hablar con la gente
    "ia_servicio": "auto",         # auto | local | gemini | otro | openai | anthropic
    "ia_url_otro": "",             # dirección de un servicio compatible con OpenAI; vacío = OpenRouter
    "ia_modelo_otro": "",          # modelo de ese servicio; vacío = lo elige el juego
    "teclas_menus": False,         # las teclas cambiadas valen también en los menús y los diálogos
    "teclas": {},                  # teclas cambiadas: función original -> tecla física
    "viajes_trayecto": True,       # en taxi y autobús se oye el trayecto durante un rato; con no, se llega al momento
    "motor_sonido": "clasico",
    "eco_lugares": True,           # con el motor envolvente, cada sitio tiene su eco: calle, nave, interior, campo     # clasico | envolvente (binaural con OpenAL Soft; se aplica al abrir el juego)
    "sonido_mono": False,          # los dos oídos oyen lo mismo
    "atenuar_al_hablar": True,     # bajar ambiente y música mientras habla la voz
    "describir_zonas": True,       # la primera vez que entras en un barrio, lo describe
    "menu_posicion": False,        # decir «3 de 9» al moverse por los menús
    "vibracion_fuerza": 1.0,       # intensidad de la vibración del mando, de 0.2 a 1
    "voces_grabadas": True,        # en las escenas, usar las voces grabadas que haya en data/voces
    "atraccion": "todos",          # contenido para adultos: quién te atrae
    "mi_genero": "x",              # contenido para adultos: cómo te ven los demás (x = no dicho)
    "vida_realista": False,        # hambre y sueño
    "red_nombre": "",              # cómo te ven tus amigos; vacío = el nombre de tu personaje
    "red_puerto": 47810,
    "red_ultima": "",              # última dirección a la que te uniste
    "act_auto": True,              # buscar una versión nueva al arrancar (solo avisa)
    "act_fuente": "servidor",      # servidor | github | ambas | personalizada
    "act_url": "",                 # dirección de version.json para la fuente personalizada
}

OPCIONES = {
    "movimiento": ["brujula", "giro"],
    "conduccion": ["asistida", "libre"],
    "punteria": ["completa", "manual"],
    "dificultad": ["facil", "normal", "dificil"],
    "direcciones": ["cardinal", "reloj", "relativa"],
    "radar_filtro": ["todo", "lugares", "vehiculos", "personas", "objetos"],
    "atraccion": ["todos", "mujeres", "hombres"],
    "mi_genero": ["x", "h", "m"],
    "act_fuente": ["servidor", "github", "ambas", "personalizada"],
    "motor_sonido": ["clasico", "envolvente"],
    "ia_servicio": ["auto", "local", "gemini", "otro", "openai", "anthropic"],
}


class Config:
    def __init__(self, archivo=None):
        self.archivo = archivo or rutas.archivo_config("config")
        self.v = {k: (dict(v) if isinstance(v, dict) else v) for k, v in POR_DEFECTO.items()}
        self.cargar()

    def cargar(self):
        try:
            from . import cifrado
            origen = self.archivo
            if not os.path.exists(origen):                # opciones guardadas con la otra forma (antes o después de compilar)
                base = os.path.splitext(origen)[0]
                origen = next((base + e for e in (".json", rutas.EXT_CONFIG) if os.path.exists(base + e)), origen)
            datos = cifrado.leer_json(origen)
            for k, val in datos.items():
                if k in POR_DEFECTO and isinstance(val, type(POR_DEFECTO[k])):
                    self.v[k] = val
                elif k in POR_DEFECTO and isinstance(POR_DEFECTO[k], float) and isinstance(val, (int, float)):
                    self.v[k] = float(val)
            for k, ops in OPCIONES.items():
                if self.v[k] not in ops:
                    self.v[k] = POR_DEFECTO[k]
        except (OSError, ValueError):
            pass

    def guardar(self):
        try:
            from . import cifrado
            cifrado.escribir_json(self.archivo, self.v, sangria=2)          # protegido en el juego compilado
        except OSError:
            pass

    def __getitem__(self, k):
        return self.v[k]

    def __setitem__(self, k, val):
        self.v[k] = val
