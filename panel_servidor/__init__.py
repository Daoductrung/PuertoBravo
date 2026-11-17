"""Panel del servidor en línea de Puerto Bravo: una ventana para llevar el servidor sin usar la consola.

El servidor es el mismo que arranca por consola (el paquete ``servidor``); aquí solo está la ventana, hecha con
wxPython y con los controles accesibles del editor de mods (``editor.accesibilidad``).
"""
import os
import sys

NOMBRE = "Panel del servidor de Puerto Bravo"
CONF = "servidor.conf"


def carpeta_programa():
    """La carpeta donde está el programa: la del ejecutable compilado o, en desarrollo, la del proyecto."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carpeta_servidor():
    """Donde viven la configuración y los datos del servidor.

    En el juego compilado es la carpeta ``servidor``, junto al juego: todo lo del servidor queda junto y aparte, y las
    actualizaciones del juego no lo tocan. En desarrollo es la carpeta del proyecto, como siempre."""
    base = carpeta_programa()
    if getattr(sys, "frozen", False):
        base = os.path.join(base, "servidor")
        os.makedirs(base, exist_ok=True)
    return base


def situarse():
    """Deja el programa trabajando en la carpeta del servidor: las rutas de la configuración parten de ella."""
    os.chdir(carpeta_servidor())


def ruta_documentacion():
    """La guía del servidor, donde esté: junto al servidor o con el resto de la documentación del juego."""
    base = carpeta_programa()
    for partes in (("servidor", "documentacion.html"), ("data", "docs", "servidor.html")):
        ruta = os.path.join(base, *partes)
        if os.path.exists(ruta):
            return ruta
    return None
