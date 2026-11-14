"""Soporte de mando: Xbox, PlayStation (DualShock 4 y DualSense) y compatibles.

Se usa la API de mandos de SDL (pygame._sdl2.controller), que da la misma
disposición de botones a todos los mandos conocidos. El mando se traduce a las
mismas teclas que el teclado, así que todo lo que se puede hacer con el teclado
se puede hacer con el mando, y los dos se pueden usar a la vez.

La asignación de botones se guarda en data/config/mando.json y se puede cambiar
desde Opciones, Mando.
"""
import json
import math
import os

import pygame

from . import rutas

BOTONES_SDL = {0: "a", 1: "b", 2: "x", 3: "y", 4: "back", 5: "guide", 6: "start", 7: "l3", 8: "r3", 9: "lb", 10: "rb",
               11: "arriba", 12: "abajo", 13: "izquierda", 14: "derecha", 15: "misc", 20: "touchpad"}
EJES_SDL = {0: "lx", 1: "ly", 2: "rx", 3: "ry", 4: "lt", 5: "rt"}
ORDEN_BOTONES = ["a", "b", "x", "y", "lb", "rb", "lt", "rt", "l3", "r3", "arriba", "abajo", "izquierda", "derecha", "back", "start", "touchpad", "misc"]

NOMBRES = {
    "xbox": {"a": "A", "b": "B", "x": "X", "y": "Y", "lb": "LB", "rb": "RB", "lt": "gatillo izquierdo", "rt": "gatillo derecho",
             "l3": "pulsar la palanca izquierda", "r3": "pulsar la palanca derecha", "arriba": "cruceta arriba", "abajo": "cruceta abajo",
             "izquierda": "cruceta izquierda", "derecha": "cruceta derecha", "back": "botón Vista", "start": "botón Menú",
             "touchpad": "panel táctil", "misc": "botón Compartir", "guide": "botón Xbox"},
    "ps": {"a": "Equis", "b": "Círculo", "x": "Cuadrado", "y": "Triángulo", "lb": "L1", "rb": "R1", "lt": "L2", "rt": "R2",
           "l3": "L3, pulsar la palanca izquierda", "r3": "R3, pulsar la palanca derecha", "arriba": "cruceta arriba", "abajo": "cruceta abajo",
           "izquierda": "cruceta izquierda", "derecha": "cruceta derecha", "back": "botón Crear o Share", "start": "botón Options",
           "touchpad": "panel táctil", "misc": "botón del micrófono", "guide": "botón PlayStation"},
}

K = pygame
S = pygame.KMOD_SHIFT
# acción: (descripción, tecla, modificador, se mantiene pulsada)
ACCIONES = {
    "nada": ("sin asignar", None, 0, False),
    "interactuar": ("interactuar: entrar, empezar misión, recoger, hablar", K.K_RETURN, 0, False),
    "vehiculo": ("subir a un vehículo o bajarte", K.K_f, 0, False),
    "atacar": ("atacar o disparar", K.K_SPACE, 0, True),
    "fijar": ("fijar al enemigo más cercano", K.K_q, 0, False),
    "recargar": ("recargar el arma", K.K_r, 0, False),
    "agacharse": ("agacharte o levantarte", K.K_x, 0, False),
    "arma_sig": ("arma siguiente", K.K_COMMA, 0, False),
    "arma_ant": ("arma anterior", K.K_COMMA, S, False),
    "armas": ("lista de armas", K.K_i, 0, False),
    "botiquin": ("usar un botiquín", K.K_z, 0, False),
    "donde": ("dónde estoy", K.K_c, 0, False),
    "estado": ("estado: salud, dinero y arma", K.K_v, 0, False),
    "radar_sig": ("radar: siguiente", K.K_TAB, 0, False),
    "radar_ant": ("radar: anterior", K.K_TAB, S, False),
    "baliza_radar": ("GPS hacia lo último que dijo el radar", K.K_b, 0, False),
    "gps": ("repetir la indicación del GPS", K.K_g, 0, False),
    "objetivo": ("objetivo de la misión", K.K_o, 0, False),
    "describir": ("descripción del lugar", K.K_n, 0, False),
    "rumbo": ("hacia dónde miro, con tono del norte", K.K_k, 0, False),
    "hora": ("hora y tiempo", K.K_t, 0, False),
    "movil": ("abrir el móvil", K.K_m, 0, False),
    "lugares": ("lista de lugares", K.K_l, 0, False),
    "mapa": ("explorador de mapa", K.K_F9, 0, False),
    "pausa": ("menú de pausa", K.K_ESCAPE, 0, False),
    "ayuda": ("ayuda de teclas y botones", K.K_F1, 0, False),
    "atracar": ("atracar a un peatón", K.K_e, 0, False),
    "gritar": ("gritar", K.K_h, 0, False),
    "acelerar": ("acelerar", K.K_UP, 0, True),
    "frenar": ("frenar y marcha atrás", K.K_DOWN, 0, True),
    "freno_mano": ("freno de mano", K.K_SPACE, 0, True),
    "claxon": ("claxon", K.K_h, 0, False),
    "radio": ("emisora siguiente", K.K_r, 0, False),
    "radio_off": ("apagar la radio", K.K_r, S, False),
    "media_vuelta": ("media vuelta", K.K_u, 0, False),
    "disparar_veh": ("disparar desde el vehículo", K.K_LCTRL, 0, True),
    "trabajo": ("empezar o terminar un trabajo con el vehículo", K.K_j, 0, False),
    "piloto": ("piloto del GPS", K.K_y, 0, False),
    "paseo": ("caminar solo siguiendo el GPS", K.K_u, 0, False),
    "hablar": ("hablar con la persona de al lado", K.K_j, 0, False),
    "especial": ("pescar en el mar, o sirena en vehículos de emergencias", K.K_p, 0, False),
    "velocidad": ("decir la velocidad", K.K_w, 0, False),
}

POR_DEFECTO = {
    "pie": {"a": "interactuar", "b": "agacharse", "x": "recargar", "y": "vehiculo", "lb": "arma_ant", "rb": "arma_sig",
            "lt": "fijar", "rt": "atacar", "l3": "gps", "r3": "botiquin", "arriba": "donde", "abajo": "estado",
            "izquierda": "radar_ant", "derecha": "radar_sig", "back": "movil", "start": "pausa", "touchpad": "mapa", "misc": "objetivo"},
    "coche": {"a": "interactuar", "b": "freno_mano", "x": "claxon", "y": "vehiculo", "lb": "fijar", "rb": "disparar_veh",
              "lt": "frenar", "rt": "acelerar", "l3": "media_vuelta", "r3": "trabajo", "arriba": "donde", "abajo": "estado",
              "izquierda": "radar_ant", "derecha": "radar_sig", "back": "movil", "start": "pausa", "touchpad": "mapa", "misc": "objetivo"},
}
MENU = {"a": K.K_RETURN, "b": K.K_ESCAPE, "start": K.K_ESCAPE, "y": K.K_F1, "x": K.K_PERIOD, "lb": K.K_PAGEUP, "rb": K.K_PAGEDOWN,
        "arriba": K.K_UP, "abajo": K.K_DOWN, "izquierda": K.K_LEFT, "derecha": K.K_RIGHT}
PANTALLA = {"a": K.K_RETURN, "b": K.K_ESCAPE, "start": K.K_ESCAPE, "x": K.K_TAB, "y": K.K_n, "lb": K.K_HOME, "rb": K.K_d, "back": K.K_F1,
            "arriba": K.K_UP, "abajo": K.K_DOWN, "izquierda": K.K_LEFT, "derecha": K.K_RIGHT}
PALANCAS_AYUDA = {
    "pie": ["Palanca izquierda: caminar; empujada a fondo, correr", "Palanca derecha: escáner direccional, dice qué hay hacia donde la muevas"],
    "coche": ["Palanca izquierda a los lados: intermitente en conducción asistida, o volante en conducción libre, en barcos y en helicópteros",
              "Palanca derecha a los lados: cambiar de carril para adelantar", "Palanca derecha arriba: emisora siguiente",
              "Palanca derecha abajo: pescar en el mar, o sirena en vehículos de emergencias"],
    "menu": ["En los menús: cruceta o palanca izquierda para moverte", "A o Equis para elegir", "B o Círculo para volver",
             "Y o Triángulo para la ayuda de la opción", "X o Cuadrado para repetir", "LB y RB, o L1 y R1, para repasar los mensajes anteriores"],
}


class Mando:
    ZONA = 0.35

    def __init__(self, app):
        self.app = app
        self.ctrl = None
        self.modulo = None
        self.tipo = "xbox"
        self.nombre = ""
        self.simulado = False
        self.ejes = {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "lt": 0.0, "rt": 0.0}
        self.pulsados = set()
        self.mis_teclas = set()
        self.flick = {}             # estado de los «toques» de palanca
        self.t_rep = 0.0
        self.rep_tecla = None
        self.mapa = {c: dict(m) for c, m in POR_DEFECTO.items()}
        self._cargar_mapa()
        try:
            from pygame._sdl2 import controller
            controller.init()
            self.modulo = controller
            for i in range(controller.get_count()):
                if controller.is_controller(i):
                    self.conectar(i, anunciar=False)
                    break
        except Exception:
            self.modulo = None

    # ------------------------------------------------------------ asignación
    def _archivo(self):
        propio = rutas.archivo_config("mando")
        if not os.path.exists(propio):                    # botones guardados con la otra forma
            base = os.path.splitext(propio)[0]
            for ext in (".json", rutas.EXT_CONFIG):
                if os.path.exists(base + ext) and not getattr(self, "_guardando", False):
                    return base + ext
        return propio

    def _cargar_mapa(self):
        try:
            from . import cifrado
            d = cifrado.leer_json(self._archivo())
            for c in self.mapa:
                for b, a in d.get(c, {}).items():
                    if b in ORDEN_BOTONES and a in ACCIONES:
                        self.mapa[c][b] = a
        except (OSError, ValueError):
            pass

    def guardar_mapa(self):
        if self.app.pruebas:
            return
        try:
            from . import cifrado
            cifrado.escribir_json(rutas.archivo_config("mando"), self.mapa, sangria=2)
        except OSError:
            pass

    def restablecer(self):
        self.mapa = {c: dict(m) for c, m in POR_DEFECTO.items()}
        self.guardar_mapa()

    def nombre_boton(self, b):
        return NOMBRES[self.tipo].get(b, b)

    # --------------------------------------------------------------- conexión
    @property
    def conectado(self):
        return self.simulado or self.ctrl is not None

    def conectar(self, indice, anunciar=True):
        if self.modulo is None or self.ctrl is not None:
            return
        try:
            self.ctrl = self.modulo.Controller(indice)
            self.nombre = str(self.ctrl.name or "mando")
        except Exception:
            self.ctrl = None
            return
        n = self.nombre.lower()
        self.tipo = "ps" if any(x in n for x in ("ps3", "ps4", "ps5", "dualshock", "dualsense", "playstation", "sony", "wireless controller")) else "xbox"
        if anunciar:
            self.app.son("notificacion")
            self.app.decir(f"Mando conectado: {self.nombre}. En cualquier momento, la ayuda dice qué hace cada botón.")

    def desconectar(self, anunciar=True):
        if self.ctrl is None:
            return
        self.ctrl = None
        self._soltar_todo()
        if anunciar:
            self.app.son("menu_atras")
            self.app.decir("Mando desconectado. Puedes seguir con el teclado.")

    def _soltar_todo(self):
        for k in self.mis_teclas:
            self.app.teclas.discard(k)
        self.mis_teclas.clear()
        self.pulsados.clear()
        for e in self.ejes:
            self.ejes[e] = 0.0
        self.flick.clear()

    # --------------------------------------------------------------- vibración
    def vibrar(self, grave, agudo, ms):
        if not self.app.cfg["mando_vibracion"] or self.ctrl is None:
            return
        try:
            f = max(0.2, min(1.0, float(self.app.cfg["vibracion_fuerza"])))
            self.ctrl.rumble(max(0.0, min(1.0, grave * f)), max(0.0, min(1.0, agudo * f)), int(ms))
        except Exception:
            pass

    # ---------------------------------------------------------------- contexto
    def contexto(self):
        from .menus import Dialogo, Menu
        from .partida import Partida
        if not self.app.pila:
            return "menu"
        cima = self.app.pila[-1]
        if isinstance(cima, Partida):
            return "coche" if cima.j.veh else "pie"
        if isinstance(cima, (Menu, Dialogo)):
            return "menu"
        return "pantalla"

    def _tecla(self, key, mod=0):
        self.app.evento_tecla(_Ev(key, mod))
        self.app.teclas.discard(key)

    # ------------------------------------------------------------------ eventos
    def evento(self, ev):
        """Procesa un evento de pygame. Devuelve True si era del mando."""
        t = ev.type
        if t == pygame.CONTROLLERDEVICEADDED:
            self.conectar(ev.device_index)
        elif t == pygame.CONTROLLERDEVICEREMOVED:
            self.desconectar()
        elif t == pygame.CONTROLLERBUTTONDOWN:
            self.boton(BOTONES_SDL.get(ev.button), True)
        elif t == pygame.CONTROLLERBUTTONUP:
            self.boton(BOTONES_SDL.get(ev.button), False)
        elif t == pygame.CONTROLLERAXISMOTION:
            self.eje(EJES_SDL.get(ev.axis), ev.value / 32767.0)
        else:
            return False
        return True

    def eje(self, nombre, valor):
        if nombre not in self.ejes:
            return
        valor = max(-1.0, min(1.0, valor))
        antes = self.ejes[nombre]
        self.ejes[nombre] = valor
        if nombre in ("lt", "rt"):              # los gatillos se tratan como botones
            if antes < 0.3 <= valor:
                self.boton(nombre, True)
            elif antes >= 0.15 > valor:
                self.boton(nombre, False)

    def boton(self, b, abajo):
        if b is None:
            return
        ctx = self.contexto()
        if not abajo:
            self.pulsados.discard(b)
            return
        self.pulsados.add(b)
        if ctx == "menu":
            k = MENU.get(b)
            if k:
                self._tecla(k)
            return
        if ctx == "pantalla":
            k = PANTALLA.get(b)
            if k:
                self._tecla(k)
            return
        accion = self.mapa[ctx].get(b, "nada")
        p = self.app.pila[-1]
        if ctx == "coche":
            if accion == "interactuar" and p.pesca:
                self._tecla(K.K_SPACE)              # con la caña echada, el botón de interactuar tira del sedal
                return
            if accion == "claxon" and p.j.veh and p.j.veh.modelo.get("sirena"):
                accion = "especial"
        _, key, mod, _ = ACCIONES[accion]
        if key is not None:
            self.app.evento_tecla(_Ev(key, mod))
            self.app.teclas.discard(key)

    # ------------------------------------------------------------- por fotograma
    def _toque(self, clave, valor, tecla_neg, tecla_pos, umbral=0.6):
        """Convierte un movimiento de palanca en una sola pulsación (hasta que vuelve al centro)."""
        est = self.flick.get(clave, 0)
        nuevo = -1 if valor <= -umbral else 1 if valor >= umbral else 0 if abs(valor) < 0.3 else est
        if nuevo != est:
            self.flick[clave] = nuevo
            if nuevo:
                self._tecla(tecla_neg if nuevo < 0 else tecla_pos)
            return nuevo
        return 0

    def actualizar(self, dt):
        if not self.conectado:
            return
        app = self.app
        ctx = self.contexto()
        lx, ly, rx, ry = self.ejes["lx"], -self.ejes["ly"], self.ejes["rx"], -self.ejes["ry"]     # arriba positivo
        quiero = set()
        if ctx in ("menu", "pantalla"):
            # palanca izquierda como cruceta, con repetición al mantenerla
            d = None
            if abs(ly) >= 0.6 and abs(ly) >= abs(lx):
                d = K.K_UP if ly > 0 else K.K_DOWN
            elif abs(lx) >= 0.6:
                d = K.K_RIGHT if lx > 0 else K.K_LEFT
            if d is None:
                self.rep_tecla = None
            elif d != self.rep_tecla:
                self.rep_tecla = d
                self.t_rep = 0.45
                self._tecla(d)
            else:
                self.t_rep -= dt
                if self.t_rep <= 0 and d in (K.K_UP, K.K_DOWN):
                    self.t_rep = 0.14
                    self._tecla(d)
        elif ctx == "pie":
            p = app.pila[-1]
            mag = math.hypot(lx, ly)
            if p.cfg["movimiento"] == "brujula":
                if mag >= self.ZONA:
                    ang = math.degrees(math.atan2(lx, ly)) % 360
                    sector = int((ang + 22.5) // 45) % 8
                    if sector in (7, 0, 1):
                        quiero.add(K.K_UP)
                    if sector in (1, 2, 3):
                        quiero.add(K.K_RIGHT)
                    if sector in (3, 4, 5):
                        quiero.add(K.K_DOWN)
                    if sector in (5, 6, 7):
                        quiero.add(K.K_LEFT)
            else:
                if ly >= self.ZONA:
                    quiero.add(K.K_UP)
                elif ly <= -self.ZONA:
                    quiero.add(K.K_DOWN)
                self._toque("giro", lx, K.K_LEFT, K.K_RIGHT)
            if mag >= 0.92:
                quiero.add(K.K_LSHIFT)
            # palanca derecha: escáner direccional
            if abs(ry) >= abs(rx):
                self._toque("ry", ry, K.K_s, K.K_w)
                self._toque("rx", 0.0, K.K_a, K.K_d)
            else:
                self._toque("rx", rx, K.K_a, K.K_d)
                self._toque("ry", 0.0, K.K_s, K.K_w)
        elif ctx == "coche":
            p = app.pila[-1]
            if p.modo_asistido():
                self._toque("lx", lx, K.K_LEFT, K.K_RIGHT)
            else:
                if lx <= -self.ZONA:
                    quiero.add(K.K_LEFT)
                elif lx >= self.ZONA:
                    quiero.add(K.K_RIGHT)
            if rx <= -0.5:
                quiero.add(K.K_a)
            elif rx >= 0.5:
                quiero.add(K.K_d)
            if abs(ry) > abs(rx):
                n = self._toque("vry", ry, K.K_p, K.K_r)
        # botones que se mantienen (acelerar, frenar, disparar...)
        if ctx in ("pie", "coche"):
            for b in self.pulsados:
                accion = self.mapa[ctx].get(b, "nada")
                _, key, mod, mantener = ACCIONES[accion]
                if mantener and key is not None:
                    quiero.add(key)
        for k in self.mis_teclas - quiero:
            app.teclas.discard(k)
        for k in quiero:
            app.teclas.add(k)
        self.mis_teclas = quiero

    # -------------------------------------------------------------------- ayuda
    def lineas_ayuda(self, contextos=("pie", "coche", "menu")):
        titulos = {"pie": "Mando, a pie", "coche": "Mando, al volante", "menu": "Mando"}
        out = []
        for c in contextos:
            if c in self.mapa:
                for b in ORDEN_BOTONES:
                    a = self.mapa[c].get(b, "nada")
                    if a != "nada":
                        out.append(f"{titulos[c]}. {self.nombre_boton(b).capitalize()}: {ACCIONES[a][0]}.")
            for linea in PALANCAS_AYUDA.get(c, []):
                out.append(f"{titulos[c]}. {linea}.")
        return out


class _Ev:
    def __init__(self, key, mod=0):
        self.key = key
        self.mod = mod
        self.unicode = ""
