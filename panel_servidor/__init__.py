"""Panel del servidor en línea de Puerto Bravo: una ventana para llevar el servidor sin usar la consola.

El servidor es el mismo que arranca por consola (el paquete ``servidor``); aquí solo está la ventana, hecha con
wxPython y con los controles accesibles del editor de mods (``editor.accesibilidad``).
"""
from juego.i18n import tr
import os
import sys

NOMBRE = tr("Panel del servidor de Puerto Bravo")
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


def abierto_sin_activar():
    """¿Ha pedido quien abre el panel que su ventana no se active? Es lo que hace la actualización del juego cuando lo
    vuelve a abrir (minimizado y sin activar), y también un acceso directo de Windows puesto en «minimizada». Entonces el
    panel no debe coger el foco: se lo quitaría al juego, y quien usa lector de pantalla se quedaría en una ventana
    minimizada. Se le pregunta a Windows cómo se arrancó este programa."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        class Arranque(ctypes.Structure):                    # STARTUPINFOW
            _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                        ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD), ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                        ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD), ("dwFillAttribute", wintypes.DWORD),
                        ("dwFlags", wintypes.DWORD), ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                        ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]
        info = Arranque()
        info.cb = ctypes.sizeof(info)
        ctypes.windll.kernel32.GetStartupInfoW(ctypes.byref(info))
        # STARTF_USESHOWWINDOW, y una de las maneras de mostrarse sin activarse: SW_SHOWNOACTIVATE, SW_SHOWMINNOACTIVE o SW_SHOWNA
        return bool(info.dwFlags & 1) and info.wShowWindow in (4, 7, 8)
    except Exception:
        return False


def ruta_documentacion():
    """La guía del servidor, donde esté: junto al servidor o con el resto de la documentación del juego."""
    from juego import i18n
    base = carpeta_programa()
    cod = i18n.actual()
    for partes in (("servidor", f"documentacion_{cod}.html"), ("servidor", "documentacion_es.html"), ("data", "docs", f"servidor_{cod}.html"),
                   ("data", "docs", "servidor_es.html")):
        ruta = os.path.join(base, *partes)
        if os.path.exists(ruta):
            return ruta
    return None
