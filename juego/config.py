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
    "tutorial_visto": False,
    "radar_filtro": "todo",
    "emisora": 1,
}

OPCIONES = {
    "movimiento": ["brujula", "giro"],
    "conduccion": ["asistida", "libre"],
    "punteria": ["completa", "manual"],
    "dificultad": ["facil", "normal", "dificil"],
    "direcciones": ["cardinal", "reloj", "relativa"],
    "radar_filtro": ["todo", "lugares", "vehiculos", "personas", "objetos"],
}


class Config:
    def __init__(self, archivo=None):
        self.archivo = archivo or os.path.join(rutas.carpeta_data("config"), "config.json")
        self.v = {k: (dict(v) if isinstance(v, dict) else v) for k, v in POR_DEFECTO.items()}
        self.cargar()

    def cargar(self):
        try:
            with open(self.archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
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
            tmp = self.archivo + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.v, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.archivo)
        except OSError:
            pass

    def __getitem__(self, k):
        return self.v[k]

    def __setitem__(self, k, val):
        self.v[k] = val
