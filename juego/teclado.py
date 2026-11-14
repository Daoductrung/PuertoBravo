"""Reasignar las teclas del teclado.

El juego está escrito con unas teclas fijas (C dice dónde estás, F sube al coche...). Aquí se guarda qué tecla
física quiere usar el jugador para cada una. Cambiar una tecla intercambia las dos: si pones «dónde estoy» en la
P, lo que hacía la P pasa a la C, y así ninguna función se queda sin tecla.

La traducción solo se aplica jugando. En los menús, los cuadros de texto y los diálogos, las teclas son las de siempre.
"""
import pygame

NOMBRES = {pygame.K_UP: "flecha arriba", pygame.K_DOWN: "flecha abajo", pygame.K_LEFT: "flecha izquierda", pygame.K_RIGHT: "flecha derecha",
           pygame.K_SPACE: "espacio", pygame.K_TAB: "tabulador", pygame.K_COMMA: "coma", pygame.K_PERIOD: "punto", pygame.K_MINUS: "guion",
           pygame.K_RETURN: "Intro", pygame.K_ESCAPE: "Escape", pygame.K_BACKSPACE: "retroceso", pygame.K_HOME: "inicio", pygame.K_END: "fin",
           pygame.K_PAGEUP: "retroceder página", pygame.K_PAGEDOWN: "avanzar página", pygame.K_INSERT: "insertar", pygame.K_DELETE: "suprimir",
           pygame.K_SEMICOLON: "eñe", pygame.K_QUOTE: "acento", pygame.K_LEFTBRACKET: "acento grave", pygame.K_RIGHTBRACKET: "más",
           pygame.K_BACKSLASH: "ce cedilla", pygame.K_SLASH: "guion", pygame.K_LESS: "menor que"}
# Estas no se pueden cambiar ni usar como destino: son las de salir, aceptar, la ayuda, la marca del registro y los modificadores.
FIJAS = {pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_F1, pygame.K_F12, pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL,
         pygame.K_LALT, pygame.K_RALT, pygame.K_LGUI, pygame.K_RGUI, pygame.K_CAPSLOCK, pygame.K_NUMLOCK, pygame.K_PRINTSCREEN}
ETIQUETAS = {"espacio": pygame.K_SPACE, "tabulador": pygame.K_TAB, "flecha arriba": pygame.K_UP, "flecha abajo": pygame.K_DOWN}


def nombre(k):
    if k in NOMBRES:
        return NOMBRES[k]
    if pygame.K_a <= k <= pygame.K_z or pygame.K_0 <= k <= pygame.K_9:
        return chr(k).upper()
    if pygame.K_F1 <= k <= pygame.K_F12:
        return f"F{k - pygame.K_F1 + 1}"
    try:
        return pygame.key.name(k) or f"tecla {k}"
    except Exception:
        return f"tecla {k}"


def _codigo(etiqueta):
    """El código de tecla de una etiqueta de la ayuda si nombra una sola tecla («C», «F9», «Espacio»); si no, None."""
    e = etiqueta.strip().lower()
    if len(e) == 1 and e.isalnum():
        return ord(e)
    if e.startswith("f") and e[1:].isdigit() and 2 <= int(e[1:]) <= 11:
        return pygame.K_F1 + int(e[1:]) - 1
    return ETIQUETAS.get(e)


def funciones():
    """Las funciones que se pueden cambiar de tecla: (código original, contexto, descripción). Salen de la ayuda del juego."""
    from .ayuda import TECLAS
    titulos = {"general": "En cualquier momento", "pie": "A pie", "coche": "Al volante"}
    vistas, lista = {}, []
    for ctx in ("general", "pie", "coche"):
        for etiqueta, que in TECLAS[ctx]:
            k = _codigo(etiqueta)
            if k is None or k in FIJAS:
                continue
            if k in vistas:                           # la misma tecla hace una cosa a pie y otra al volante: una sola entrada
                n = vistas[k]
                lista[n] = (k, "A pie y al volante", f"{lista[n][1].lower()}, {lista[n][2]}. {titulos[ctx]}, {que}")
            else:
                vistas[k] = len(lista)
                lista.append((k, titulos[ctx], que))
    for k, que in ((pygame.K_UP, "caminar al norte o hacia delante, y acelerar al volante"), (pygame.K_DOWN, "caminar al sur o hacia atrás, y frenar al volante"),
                   (pygame.K_LEFT, "caminar al oeste o girar a la izquierda, e intermitente izquierdo"),
                   (pygame.K_RIGHT, "caminar al este o girar a la derecha, e intermitente derecho"), (pygame.K_SPACE, "atacar o disparar, y freno de mano"),
                   (pygame.K_TAB, "radar"), (pygame.K_w, "escáner: delante. Al volante, la velocidad"), (pygame.K_a, "escáner: izquierda. Al volante, cambiar de carril"),
                   (pygame.K_s, "escáner: detrás"), (pygame.K_d, "escáner: derecha. Al volante, arrimarte a la acera"), (pygame.K_COMMA, "arma siguiente"),
                   (pygame.K_PERIOD, "repetir el último mensaje")):
        if k not in vistas:
            vistas[k] = len(lista)
            lista.append((k, "Movimiento y acciones", que))
    return lista


def _mapa(cfg):
    """{función original: tecla física que la hace}, solo con lo cambiado y saneado."""
    m = {}
    for a, b in dict(cfg["teclas"]).items():
        try:
            a, b = int(a), int(b)
        except (TypeError, ValueError):
            continue
        if a != b and a not in FIJAS and b not in FIJAS:
            m[a] = b
    return m


def traducir(cfg, k):
    """Qué función hace la tecla física k. Sin cambios, ella misma."""
    if not cfg["teclas"]:
        return k
    for funcion, fisica in _mapa(cfg).items():
        if fisica == k:
            return funcion
    return k


def tecla_de(cfg, funcion):
    """Con qué tecla física se hace ahora una función."""
    return _mapa(cfg).get(funcion, funcion)


def cambiar(cfg, funcion, fisica):
    """Pone la función en la tecla física dada e intercambia lo que hubiera allí. Devuelve la función desplazada, o None."""
    if funcion in FIJAS or fisica in FIJAS:
        return None
    m = _mapa(cfg)
    antes = m.get(funcion, funcion)               # la tecla que hacía esta función
    otra = traducir(cfg, fisica)                  # la función que hacía la tecla elegida
    m[funcion] = fisica
    desplazada = None
    if otra != funcion:
        m[otra] = antes
        desplazada = otra
    cfg["teclas"] = {str(a): str(b) for a, b in m.items() if a != b}
    return desplazada


def restablecer(cfg):
    cfg["teclas"] = {}


def cambios(cfg):
    """Frases con lo cambiado, para la ayuda: «La función de la C está ahora en la P»."""
    return [f"Lo que hacía {nombre(a)} se hace ahora con {nombre(b)}" for a, b in sorted(_mapa(cfg).items())]


class Captura:
    """Pantalla que espera a que el jugador pulse la tecla que quiere usar. Escape cancela."""
    pausa_mundo = True

    def __init__(self, app, titulo, al_elegir):
        self.app, self.titulo, self.al_elegir = app, titulo, al_elegir

    def al_entrar(self):
        self.app.decir(f"{self.titulo}. Pulsa la tecla que quieres usar. Escape cancela.", True)

    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            self.app.son("menu_atras")
            self.app.cerrar(self)
            self.app.decir("Cancelado.", True)
            return
        if k in FIJAS:
            self.app.son("error")
            self.app.decir(f"{nombre(k).capitalize()} no se puede usar: está reservada. Pulsa otra, o Escape para cancelar.", True)
            return
        self.app.cerrar(self)
        self.al_elegir(k)

    def actualizar(self, dt):
        pass

    def cerrado(self):
        pass
