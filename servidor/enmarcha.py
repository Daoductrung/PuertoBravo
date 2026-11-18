"""La ficha de un servidor en marcha: qué programa es, con qué argumentos se arrancó y dónde tiene sus datos.

La deja el propio servidor (el de consola y el panel) al arrancar, y la borra al salir. Sirve para una sola cosa: que
la actualización del juego en Windows sepa qué servidores hay abiertos en su carpeta, pueda pedirles que paren con
orden (dejándoles el archivo de órdenes en su carpeta de datos) y los vuelva a arrancar igual al terminar.

Solo se escribe en el juego compilado, dentro de su carpeta servidor, en la subcarpeta en_marcha: un archivo por
proceso. No lleva nada personal más allá de las rutas del propio programa, y no sale del equipo.
"""
import json
import os
import sys
import time

CARPETA = "en_marcha"
_mia = [None]            # la ruta de la ficha de este proceso, si se ha escrito


def carpeta(programa=None):
    """Dónde van las fichas. Solo existe en el juego compilado (o donde digan las pruebas con la variable de entorno
    PUERTOBRAVO_EN_MARCHA): un servidor arrancado desde el código, en Linux o en un NAS, no deja ficha."""
    if programa:
        return os.path.join(programa, "servidor", CARPETA)
    forzada = os.environ.get("PUERTOBRAVO_EN_MARCHA")
    if forzada:
        return forzada
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "servidor", CARPETA)
    return None


def sesion_de_windows():
    """El número de sesión de Windows de este proceso: 0 es la de los servicios. None si no se puede saber."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        n = ctypes.c_ulong(0)
        if ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(n)):
            return int(n.value)
    except Exception:
        pass
    return None


def anotar(tipo, datos, conf=None, args=None, activo=True, donde=None):
    """Escribe (o pone al día) la ficha de este proceso. ``tipo`` es «consola» o «panel»; ``activo``, si el servidor está
    en marcha ahora mismo (en el panel puede estar parado). Devuelve la ruta, o None si aquí no se dejan fichas."""
    donde = donde or carpeta()
    if not donde:
        return None
    ficha = {"pid": os.getpid(), "tipo": tipo, "exe": os.path.abspath(sys.executable), "args": list(sys.argv[1:] if args is None else args),
             "cwd": os.getcwd(), "datos": os.path.abspath(datos), "conf": os.path.abspath(conf) if conf else "", "activo": bool(activo),
             "sesion": sesion_de_windows(), "inicio": int(time.time())}
    try:
        os.makedirs(donde, exist_ok=True)
        ruta = os.path.join(donde, "%d.json" % os.getpid())
        with open(ruta + ".tmp", "w", encoding="utf-8") as f:
            json.dump(ficha, f, ensure_ascii=False)
        os.replace(ruta + ".tmp", ruta)
    except OSError:
        return None
    _mia[0] = ruta
    return ruta


def quitar():
    """Borra la ficha de este proceso: ha terminado."""
    ruta, _mia[0] = _mia[0], None
    if ruta:
        try:
            os.remove(ruta)
        except OSError:
            pass


def leer(donde):
    """Las fichas que hay en una carpeta, sin comprobar si sus procesos siguen vivos."""
    fichas = []
    try:
        nombres = sorted(os.listdir(donde))
    except OSError:
        return fichas
    for n in nombres:
        if not n.endswith(".json"):
            continue
        try:
            with open(os.path.join(donde, n), encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("pid"), int):
                fichas.append(d)
        except (OSError, ValueError):
            continue
    return fichas
