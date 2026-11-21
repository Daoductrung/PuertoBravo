"""Opciones, Registro para informar de fallos: dónde está, qué contiene y cómo enviarlo."""
from .i18n import tr
import os

from . import registro
from .menus import Menu, Opcion

DONDE_ENVIAR = "https://github.com/hxebolax/PuertoBravo/issues"


def opciones(app):
    def carpeta():
        return registro.carpeta_sesion()

    def donde():
        c = carpeta()
        if not c:
            app.decir(tr("En esta sesión no hay registro: no se ha podido escribir en la carpeta data."), True)
            return
        app.decir(tr('El registro de esta sesión está en la carpeta data, logs, {basename}. Se guardan las cinco últimas sesiones, cada una en su carpeta con la fecha y la hora; las más antiguas se borran solas.').format(basename=(os.path.basename(c))), True)

    def abrir(ruta):
        def f():
            if not ruta() or not os.path.isdir(ruta()):
                app.son("error")
                app.decir(tr("Esa carpeta no existe todavía."), True)
                return
            try:
                os.startfile(ruta())
                app.decir(tr("Carpeta abierta en el Explorador de Windows."), True)
            except OSError:
                app.son("error")
                app.decir(tr("No se pudo abrir la carpeta."), True)
        return f

    def marcar():
        registro.marca()
        app.son("guardado")
        app.decir(tr("Marca añadida al registro de la sesión."), True)

    m = Menu(app, tr("Registro para informar de fallos"), [
        Opcion(tr("Dónde está el registro de esta sesión"), donde,
               ayuda=tr("Te dice en qué carpeta se está guardando el registro de esta sesión y cuántas sesiones se conservan.")),
        Opcion(tr("Abrir la carpeta de esta sesión"), abrir(carpeta), ayuda=tr("Abre en el Explorador de Windows la carpeta con el registro de esta sesión.")),
        Opcion(tr("Abrir la carpeta con todas las sesiones"), abrir(registro.carpeta_logs), ayuda=tr("Cada sesión tiene su carpeta, con la fecha y la hora en el nombre.")),
        Opcion(tr("Qué contiene y qué no"), lambda: app.decir(
            tr("Contiene la versión del juego y de Windows, el lector de pantalla, el sonido, los mods, tus opciones de juego, las pantallas que abres, "
            "las teclas que pulsas jugando, lo que el juego dice, el estado de la partida cada pocos segundos, y los errores. "
            "No contiene nada de lo que escribes en los cuadros de texto, ni mensajes del chat, ni contraseñas o claves, ni tu nombre o el de tus amigos, "
            "ni direcciones de internet, ni tu usuario de Windows, ni las rutas de tus carpetas, ni los nombres de tu música, ni tus partidas. "
            "Son archivos de texto: puedes leerlos antes de enviarlos."), True),
               ayuda=tr("Te lee lo que se apunta en el registro y lo que nunca se apunta, para que sepas qué envías.")),
        Opcion(tr("Cómo enviar un fallo"), lambda: app.decir(
            tr("Cierra el juego. Entra en la carpeta data, logs, y busca la carpeta de la sesión en la que falló: lleva la fecha y la hora en el nombre. "
            "Comprímela en un ZIP: en el Explorador, menú contextual, Enviar a, Carpeta comprimida. "
            "Envíala, contando qué estabas haciendo, a través de la página de incidencias del proyecto en GitHub, o por Mastodon, a arroba HXeBoLaX en comunidad punto nvda punto es."), True),
               ayuda=tr("Te lee los pasos para comprimir la carpeta de la sesión que falló y dónde mandarla.")),
        Opcion(tr("Poner una marca ahora"), marcar, ayuda=tr("Deja una señal en el registro para indicar que en este momento ha pasado algo raro. Jugando se hace con F12.")),
        Opcion(tr("Volver"), lambda: app.cerrar(m)),
    ])
    app.abrir(m)
