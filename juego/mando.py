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
    "cruce": ("siguiente cruce: qué calle viene y a cuántos metros", K.K_n, S, False),
    "necesidades": ("hambre, sed, sueño e higiene", K.K_v, S, False),
    "mi_vehiculo": ("dónde está mi vehículo, y marcarlo en el GPS", K.K_l, S, False),
    "mirar_jugador": ("cómo va vestido el jugador de al lado", K.K_j, S, False),
    "quitar_gps": ("cancelar el GPS", K.K_g, S, False),
    "walkman": ("reproductor con auriculares: encender y emisora siguiente", K.K_r, S, False),
    "rendirse": ("rendirte ante la policía: levantar las manos", K.K_h, S, False),
    "menu_acciones": ("menú de acciones: todo lo que no tiene botón propio, como dar el alto, gritar, atracar, cubrirte, el tiempo lento, los canales de rol o tu perro", None, 0, False),
}
# El botón que, mantenido, convierte a los demás en una segunda función: Vista en Xbox, Crear o Share en PlayStation.
# Pulsado y soltado solo, hace lo suyo (de serie, abrir el móvil).
COMBINAR = "back"

POR_DEFECTO = {
    "pie": {"a": "interactuar", "b": "agacharse", "x": "recargar", "y": "vehiculo", "lb": "arma_ant", "rb": "arma_sig",
            "lt": "fijar", "rt": "atacar", "l3": "gps", "r3": "botiquin", "arriba": "donde", "abajo": "estado",
            "izquierda": "radar_ant", "derecha": "radar_sig", "back": "movil", "start": "pausa", "touchpad": "mapa", "misc": "objetivo"},
    "coche": {"a": "interactuar", "b": "freno_mano", "x": "claxon", "y": "vehiculo", "lb": "fijar", "rb": "disparar_veh",
              "lt": "frenar", "rt": "acelerar", "l3": "media_vuelta", "r3": "trabajo", "arriba": "donde", "abajo": "estado",
              "izquierda": "radar_ant", "derecha": "radar_sig", "back": "movil", "start": "pausa", "touchpad": "mapa", "misc": "objetivo"},
    # segundas funciones: manteniendo el botón de combinar y pulsando otro
    "pie_combo": {"a": "paseo", "b": "hablar", "x": "baliza_radar", "y": "mi_vehiculo", "lb": "rumbo", "rb": "hora", "lt": "rendirse", "rt": "menu_acciones", "l3": "quitar_gps", "r3": "armas",
                  "arriba": "cruce", "abajo": "necesidades", "izquierda": "lugares", "derecha": "walkman", "start": "ayuda", "misc": "mirar_jugador",
                  "touchpad": "mirar_jugador"},
    "coche_combo": {"a": "piloto", "b": "velocidad", "x": "gps", "y": "objetivo", "lb": "baliza_radar", "rb": "rumbo", "lt": "rendirse", "rt": "menu_acciones", "l3": "quitar_gps", "r3": "hora",
                    "arriba": "cruce", "abajo": "necesidades", "izquierda": "radio_off", "derecha": "radio", "start": "ayuda", "misc": "lugares",
                    "touchpad": "lugares"},
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
             "Y o Triángulo para la ayuda de la opción", "X o Cuadrado para repetir", "LB y RB, o L1 y R1, para repasar los mensajes anteriores",
             "En la pantalla de espera de un servidor: A o Equis repite cómo va, B o Círculo deja de esperar, e Y o Triángulo lo explica",
             "Recorriendo una tienda de comida por dentro: X o Cuadrado dice lo que llevas en la cesta. En cada pasillo, A o Equis, o cruceta derecha, echa el producto a la cesta, y cruceta izquierda lo devuelve",
             "Para escribir un texto con el mando: cruceta arriba y abajo recorren las letras, cruceta derecha escribe la letra elegida y cruceta izquierda borra la última. "
             "LB o L1 pone un espacio. RB o R1 cambia entre minúsculas, mayúsculas, números y signos. X o Cuadrado pasa por las frases o los nombres propuestos, si los hay. "
             "Y o Triángulo lee lo escrito. A o Equis acepta y B o Círculo cancela"],
}
# Lo que hacen las palancas, dicho como teclas: esas teclas ya tienen su forma de hacerse con el mando.
PALANCAS = {"pie": {K.K_UP, K.K_DOWN, K.K_LEFT, K.K_RIGHT, K.K_LSHIFT, K.K_w, K.K_a, K.K_s, K.K_d},
            "coche": {K.K_LEFT, K.K_RIGHT, K.K_a, K.K_d, K.K_p, K.K_r}}
C = pygame.KMOD_CTRL
# El menú de acciones: lo que el mando no tiene en un botón. Se abre con el botón de combinar y el gatillo derecho.
# (frase, tecla, modificador, dónde vale: pie, coche o ambos, condición, explicación, se queda abierto)
MENU_ACCIONES = [
    ("Dar el alto a los sospechosos", K.K_h, 0, "pie", "policia", "De servicio como policía, das el alto a quien tengas cerca. A quien se rinde se le esposa con el botón de interactuar, a su lado.", False),
    ("Gritar para espantar a los peatones", K.K_h, 0, "pie", "sin_placa", "Un grito: los peatones de alrededor se apartan.", False),
    ("Hablar en personaje, para quien está cerca", K.K_F10, S, "ambos", "servidor", "En un servidor con canales de rol: lo que dice tu personaje. Lo oye solo quien está cerca.", False),
    ("Describir lo que hace tu personaje", K.K_F10, C, "ambos", "servidor", "En un servidor con canales de rol: cuentas una acción, y los que están cerca oyen tu nombre y lo que haces.", False),
    ("Escribir un mensaje a los demás jugadores", K.K_F10, 0, "ambos", "online", "Jugando con amigos o en un servidor: un mensaje que se lee en voz alta a los demás.", False),
    ("Cómo va vestido el jugador de al lado, y su ficha", K.K_j, S, "pie", "online", "Dice la ropa del jugador más cercano y, en un servidor con canales de rol, su ficha si la ha escrito.", False),
    ("Sacar a otro jugador de su vehículo", K.K_f, S, "pie", "servidor", "En un servidor: tiene que ir despacio y estar a tu lado.", False),
    ("Atracar al peatón que tienes al lado", K.K_e, 0, "pie", None, "Con un arma en la mano.", False),
    ("Ponerte a cubierto, o salir", K.K_x, S, "pie", None, "Tras una pared o un vehículo parado. A cubierto te alcanzan mucho menos; si te mueves, sales.", False),
    ("Tiempo lento: ponerlo o quitarlo", K.K_BACKSPACE, 0, "ambos", None, "Todo va más despacio mientras te quede concentración.", False),
    ("Fijar a cualquiera, no solo a los enemigos", K.K_q, S, "ambos", None, "Recorre a todos los que hay cerca, también a quien no te ha atacado.", False),
    ("Lista de armas", K.K_i, 0, "ambos", None, "Abre la lista de tus armas para elegir una.", False),
    ("Usar un botiquín", K.K_z, 0, "ambos", None, None, False),
    ("Tus sustancias", K.K_z, S, "ambos", "adultos", None, False),
    ("Tu perro: que busque por el olfato", K.K_y, 0, "pie", "perro", "Busca el objeto más cercano y te lo marca en el GPS.", False),
    ("Tu perro: su menú", K.K_y, S, "pie", "perro", "Cómo está, acariciarlo, darle de comer, mandarlo a casa o llamarlo.", False),
    ("Enderezar el vehículo hacia el punto cardinal más cercano", K.K_e, 0, "coche", "libre", "Solo en conducción libre.", False),
    ("Pescar en el mar, o sirena en vehículos de emergencias", K.K_p, 0, "ambos", "mar_o_sirena", "Cuando oigas que pican, tira del sedal con el botón de atacar o el de interactuar.", False),
    ("Objetivo de la misión o del trabajo", K.K_o, 0, "ambos", None, None, False),
    ("Lista de lugares, para marcar un destino", K.K_l, 0, "ambos", None, None, False),
    ("Explorador de mapa", K.K_F9, 0, "ambos", None, "Recorre la localidad con un cursor, cruce a cruce, sin mover al personaje.", False),
    ("Descripción del lugar o del barrio en el que estás", K.K_n, 0, "ambos", None, None, False),
    ("Dónde está tu vehículo, y marcarlo en el GPS", K.K_l, S, "ambos", None, "El último que has usado. Si tienes más, están en el móvil, en Mis vehículos.", False),
    ("Dónde estoy, con las coordenadas", K.K_c, S, "ambos", None, None, False),
    ("Cambiar el filtro del radar", K.K_F6, 0, "ambos", None, "Todo, solo lugares, solo vehículos, solo personas o solo objetos.", False),
    ("Repetir el último mensaje", K.K_PERIOD, 0, "ambos", None, "Para repasar los anteriores, en este menú o en cualquier otro: LB y RB, o L1 y R1.", False),
    ("Cambiar entre conducción asistida y libre", K.K_F2, 0, "ambos", None, None, False),
    ("Cambiar el movimiento a pie entre brújula y giros", K.K_F3, 0, "ambos", None, None, False),
    ("Baliza sonora del GPS: ponerla o quitarla", K.K_F4, 0, "ambos", None, None, False),
    ("Guardado rápido", K.K_F5, 0, "ambos", None, "Fuera de las misiones.", False),
    ("Bajar la música", K.K_F7, 0, "ambos", None, "Cada pulsación la baja un poco. El menú no se cierra.", True),
    ("Subir la música", K.K_F8, 0, "ambos", None, "Cada pulsación la sube un poco. El menú no se cierra.", True),
    ("Poner una marca en el registro de la sesión", K.K_F12, 0, "ambos", None, "Para cuando notes algo raro: quien revise el registro sabrá en qué momento fue.", False),
]
# Lo que sale en la ayuda de teclas y no necesita botón, con el porqué. Lo vigila una prueba: una tecla nueva tiene que
# tener botón, combinación o sitio en el menú de acciones, o estar aquí con su razón.
SIN_BOTON = {
    "Números del 1 al 9": "las armas se eligen con arma siguiente y arma anterior, o en la lista de armas",
    "Re Pág y Av Pág": "los mensajes anteriores se repasan con LB y RB, o L1 y R1, dentro de cualquier menú, también en el de acciones",
    "Frenada automática": "no es una tecla: es una ayuda de la conducción asistida",
    "Helicóptero": "no es una tecla: explica cómo se pilota, con lo mismo que un barco",
    "En el mar": "no es una tecla: explica cómo se llevan los barcos",
}
# Teclas de la ayuda general que solo valen a pie, con el porqué: no hace falta que estén en el mando al volante.
SOLO_A_PIE = {"Mayúsculas F": "al volante esa tecla te baja del vehículo; sacar a otro jugador del suyo se hace a pie"}
# En las pantallas que se recorren, teclas que con el mando llegan como otra: la C de la cesta es X o Cuadrado, que allí es Tabulador.
ALIAS_PANTALLA = {K.K_c: K.K_TAB}


def _condicion(p, cual):
    """¿Tiene sentido ofrecer ahora esa acción del menú de acciones?"""
    j = p.j
    if cual == "policia":
        return bool(p.de_servicio())
    if cual == "sin_placa":
        return not p.de_servicio()
    if cual == "servidor":
        return bool(getattr(p, "en_servidor", False))
    if cual == "online":
        return bool(p.online_activo())
    if cual == "adultos":
        return bool(p.modo_adulto())
    if cual == "perro":
        return bool(j.perro)
    if cual == "libre":
        return not p.modo_asistido()
    if cual == "mar_o_sirena":
        return p.mundo.tipo == "mar" or bool(j.veh and j.veh.modelo.get("sirena"))
    return True


def acciones_de(p):
    """Las entradas del menú de acciones que valen ahora mismo: según vayas a pie o en un vehículo, y según lo que haya."""
    ctx = "coche" if p.j.veh else "pie"
    out = []
    for e in MENU_ACCIONES:
        try:
            vale = e[3] in ("ambos", ctx) and _condicion(p, e[4])
        except Exception:
            vale = e[3] in ("ambos", ctx)
        if vale:
            out.append(e)
    return out


def menu_acciones(app):
    """El menú de acciones del mando: cada cosa que con el teclado es una tecla y en el mando no tiene botón."""
    from .menus import Menu, Opcion
    p = app.pila[-1]

    def hacer(key, mod, queda):
        def f():
            if queda:                                            # el menú sigue abierto: la tecla va derecha a la partida
                p.tecla(_Ev(key, mod))
                return
            app.cerrar(menu)
            app.evento_tecla(_Ev(key, mod))
            app.teclas.discard(key)
        return f
    ops = [Opcion(frase, hacer(key, mod, queda), ayuda=ayuda) for frase, key, mod, _, _, ayuda, queda in acciones_de(p)]
    menu = Menu(app, "Acciones", ops, intro="Lo que no tiene botón propio en el mando")
    app.abrir(menu)


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
        self._combinar_pendiente = False     # el botón de combinar está pulsado y aún no se sabe si es para una combinación
        self._combinar_usado = False
        self._de_combo = set()               # botones pulsados como segunda función: no cuentan como la primera hasta soltarlos
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

    def textos(self, texto):
        """Con un mando conectado, y si la opción está puesta, las teclas que nombra una frase se dicen como botones."""
        if not self.conectado or not self.app.cfg["mando_textos"]:
            return texto
        p = getattr(self.app, "partida", None)
        try:
            return textos_mando(texto, self.mapa, self.tipo, "coche" if p is not None and p.j.veh else "pie")
        except Exception:
            return texto

    def nombre_boton(self, b):
        return NOMBRES[self.tipo].get(b, b)

    def habla_botones(self):
        """¿Hay que decir botones en vez de teclas? Con un mando conectado y la opción puesta."""
        return self.conectado and bool(self.app.cfg["mando_textos"])

    def boton_pantalla(self, key, tecla, tabla=None):
        """Cómo se dice, en una pantalla del juego, la tecla que hace algo: su nombre o, jugando con mando, el botón
        que hace lo mismo allí, con el nombre de ese mando («el botón X», «el botón Cuadrado»)."""
        if self.habla_botones():
            b = next((b for b in ORDEN_BOTONES if (tabla or PANTALLA).get(b) == key), None)
            if b is not None:
                return _frase_boton(self.tipo, b)
        return tecla

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
            b = next((b for b in ORDEN_BOTONES if self.mapa["pie_combo"].get(b) == "menu_acciones"), None)
            self.app.decir(f"Mando conectado: {self.nombre}. En cualquier momento, la ayuda dice qué hace cada botón."
                           + (f" Lo que no tiene botón propio está en el menú de acciones: {_frase(self.tipo, '+' + b)}." if b else ""))

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
            self._de_combo.discard(b)
            if b == COMBINAR and self._combinar_pendiente:
                # Soltado sin haber pulsado nada más: hace lo suyo. Si entre medias se usó para una combinación, nada.
                self._combinar_pendiente = False
                if ctx in ("pie", "coche") and not self._combinar_usado:
                    self._accion(self.mapa[ctx].get(b, "nada"), ctx)
            return
        self.pulsados.add(b)
        if ctx in ("pie", "coche"):
            if b == COMBINAR:
                self._combinar_pendiente, self._combinar_usado = True, False
                return
            if COMBINAR in self.pulsados and self._combinar_pendiente:
                self._combinar_usado = True
                self._de_combo.add(b)                            # mientras siga pulsado no cuenta como su función normal
                self._accion(self.mapa[ctx + "_combo"].get(b, "nada"), ctx)
                return
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
        self._accion(self.mapa[ctx].get(b, "nada"), ctx)

    def _accion(self, accion, ctx):
        p = self.app.pila[-1]
        if accion == "menu_acciones":
            menu_acciones(self.app)
            return
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
                if b in self._de_combo or (b == COMBINAR and self._combinar_pendiente):
                    continue
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
            if c + "_combo" in self.mapa:
                mod = self.nombre_boton(COMBINAR).capitalize()
                vistas = set()
                for b in ORDEN_BOTONES:
                    a = self.mapa[c + "_combo"].get(b, "nada")
                    if a != "nada" and b != COMBINAR and (a, b in ("touchpad", "misc")) not in vistas:
                        vistas.add((a, b in ("touchpad", "misc")))
                        out.append(f"{titulos[c]}. {mod}, mantenido, más {self.nombre_boton(b)}: {ACCIONES[a][0]}.")
        return out


class _Ev:
    def __init__(self, key, mod=0):
        self.key = key
        self.mod = mod
        self.unicode = ""
        self.mando = True                # viene del mando: no pasa por el cambio de teclas del teclado, y en un cuadro de texto mueve la rueda de letras


# ------------------------------------------------------------- las teclas, dichas como botones
# Con un mando conectado, lo que el juego cuenta («pulsa Q para fijarlo») se dice con el botón que hace eso mismo.
_TECLAS_TXT = {"intro": K.K_RETURN, "espacio": K.K_SPACE, "tabulador": K.K_TAB, "escape": K.K_ESCAPE, "f1": K.K_F1, "f9": K.K_F9,
               "coma": K.K_COMMA, "control": K.K_LCTRL}
# Cuando una tecla hace dos cosas, según vayas a pie o en un vehículo, la frase dice cuál de las dos es.
_PISTAS = {"freno_mano": "freno de mano", "atacar": "dispar|atac|golpe|pega", "recargar": "recarg", "radio": "emisora|radio", "claxon": "claxon|pita",
           "gritar": "grit", "media_vuelta": "media vuelta", "paseo": "camina|pasea|paseo", "trabajo": "trabajo|turno|servicio",
           "hablar": "habl|charl|convers", "interactuar": ""}
_BOTON_SOLO = ("a", "b", "x", "y", "lb", "rb")


def _frase_boton(tipo, b):
    """«el botón A», «el gatillo derecho», «la cruceta arriba»: el botón, con su artículo."""
    n = NOMBRES[tipo].get(b, b)
    if b in ("lt", "rt"):
        return ("el " + n) if tipo == "xbox" else ("el botón " + n)
    if b in ("arriba", "abajo", "izquierda", "derecha"):
        return "la " + n
    if b in ("l3", "r3"):
        return "la palanca " + ("izquierda" if b == "l3" else "derecha") + " pulsada"
    if b in ("back", "start", "misc", "guide"):
        return "el " + n
    if b == "touchpad":
        return "el panel táctil"
    return "el botón " + n


def _boton_de(mapa, key, mod, contexto, frase, tipo):
    """El botón que hace lo mismo que esa tecla. None si ninguno, o si no se sabe cuál de sus dos usos es."""
    acciones = [a for a, d in ACCIONES.items() if d[1] == key and (d[2] & S) == (mod & S) and a != "nada"]
    if not acciones:
        return None
    if len(acciones) > 1:
        f = frase.lower()
        con_pista = [a for a in acciones if _PISTAS.get(a) and __import__("re").search(_PISTAS[a], f)]
        if len(con_pista) == 1:
            acciones = con_pista
    orden = [contexto, "coche" if contexto == "pie" else "pie"] if len(acciones) == 1 else [contexto]
    for c in orden:
        for b in ORDEN_BOTONES:
            if mapa.get(c, {}).get(b) in acciones:
                return b
        if c == contexto:                                        # sin botón propio, su combinación: «+botón»
            for b in ORDEN_BOTONES:
                if b != COMBINAR and not (b == "touchpad" and tipo == "xbox") and mapa.get(c + "_combo", {}).get(b) in acciones:
                    return "+" + b
    return None


def _frase(tipo, b):
    """Un botón o una combinación («+botón»), dichos con su artículo."""
    if b.startswith("+"):
        return f"{_frase_boton(tipo, COMBINAR)} mantenido más {_frase_boton(tipo, b[1:])}"
    return _frase_boton(tipo, b)


def textos_mando(texto, mapa, tipo="xbox", contexto="pie"):
    """Cambia en una frase las teclas por los botones del mando que hacen lo mismo. Lo que no tiene botón se deja como está,
    porque el teclado sigue funcionando con el mando conectado."""
    import re
    if not texto or not isinstance(texto, str):
        return texto

    def una_frase(frase):
        def tecla_de(nombre):
            n = nombre.lower()
            if n in _TECLAS_TXT:
                return _TECLAS_TXT[n]
            if len(n) == 1 and n.isalpha():
                return getattr(K, "K_" + n, None)
            return None

        def cambia(m):
            verbo, mayus, nombre = m.group("verbo"), m.group("mayus"), m.group("tecla")
            key = tecla_de(nombre)
            if key is None:
                return m.group(0)
            b = _boton_de(mapa, key, S if mayus else 0, contexto, frase, tipo)
            if b is None:
                return m.group(0)
            return f"{verbo} {_frase(tipo, b)}"

        # «pulsa Q», «con la X», «con la tecla J», «Pulsa Mayúsculas Y», «tecla M»
        frase = re.sub(r"(?P<verbo>\b(?:[Pp]uls(?:a|ar|as|ando|es|ada)|[Cc]on|[Uu]sa|[Mm]antén(?: pulsad[ao])?|[Tt]oca))"
                       r" (?:(?:la|el) )?(?:tecla )?(?P<mayus>Mayúsculas (?:más |\+ )?(?:la )?)?"
                       r"(?P<tecla>Intro|Espacio|Tabulador|Escape|Control|F1|F9|coma|[A-ZÑ])(?![\wáéíóúñ])", cambia, frase)

        def suelta(m):                                           # «pulsa Espacio para disparar y R para recargar»
            key = tecla_de(m.group("tecla"))
            b = _boton_de(mapa, key, 0, contexto, frase, tipo) if key is not None else None
            return m.group(0) if b is None else f"{m.group(1)} {_frase(tipo, b)} para"
        frase = re.sub(r"(?<![\wáéíóúñ])(y|o|ni) (?:la )?(?P<tecla>Intro|Espacio|Tabulador|Escape|Control|[A-ZÑ]) para(?![\wáéíóúñ])", suelta, frase)

        def solo_tecla(m):                                       # «la tecla M abre el móvil»
            key = tecla_de(m.group("tecla"))
            b = _boton_de(mapa, key, 0, contexto, frase, tipo) if key is not None else None
            if b is None:
                return m.group(0)
            f = _frase(tipo, b)
            return f[0].upper() + f[1:] if m.group(0)[0].isupper() else f
        frase = re.sub(r"\b(?:[Ll]a|[Ee]l) tecla (?P<tecla>Intro|Espacio|Tabulador|Escape|Control|F1|F9|[A-ZÑ])(?![\wáéíóúñ])", solo_tecla, frase)
        # las flechas son la palanca izquierda; en un vehículo, arriba y abajo son los gatillos
        f = frase.lower()
        acel = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "acelerar"), None)
        fren = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "frenar"), None)
        if acel and re.search(r"aceler", f):
            frase = re.sub(r"\b(?:la )?flecha (?:de )?arriba\b", _frase_boton(tipo, acel), frase)
        if fren and re.search(r"fren|marcha atrás", f):
            frase = re.sub(r"\b(?:la )?flecha (?:de )?abajo\b", _frase_boton(tipo, fren), frase)
        frase = re.sub(r"\blas flechas izquierda y derecha\b", "la palanca izquierda a los lados", frase)
        frase = re.sub(r"\b(?:la )?flecha (?:de )?arriba\b", "la palanca izquierda hacia delante", frase)
        frase = re.sub(r"\b(?:la )?flecha (?:de )?abajo\b", "la palanca izquierda hacia atrás", frase)
        frase = re.sub(r"\b[Ll]as flechas\b", lambda m: ("L" if m.group(0)[0] == "L" else "l") + "a palanca izquierda", frase)
        frase = re.sub(r"\b([Cc])on flechas\b", r"\1on la palanca izquierda", frase)
        frase = re.sub(r"\b([Mm])antén Mayúsculas\b", lambda m: ("E" if m.group(1) == "M" else "e") + "mpuja a fondo la palanca izquierda", frase)
        return frase

    return "".join(una_frase(t) for t in re.split(r"(?<=[.!?:;])(\s+)", texto))
