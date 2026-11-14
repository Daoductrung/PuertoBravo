"""Rutas del juego. Todo lo que el juego necesita o genera vive en la carpeta data.

data/datos      mapas, lugares, misiones, armas y vehículos (JSON)
data/sonidos    los efectos de sonido, en subcarpetas:
                  por_defecto   los sonidos de serie, un archivo por sonido; si falta alguno, el juego lo vuelve a crear
                  <pack>        cada pack de sonidos alternativo en su carpeta (realista, alternativo...)
data/radio      la música de las emisoras; data/radio/mi_musica es tu propia emisora
data/musica     la música de ambiente, una carpeta por situación
data/config     opciones del juego y asignación de botones del mando
data/partidas   partidas guardadas
data/mods       ampliaciones hechas por los jugadores
data/docs       manuales
"""
import os
import sys


def base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DATA = os.path.join(base(), "data")


def data(*partes):
    return os.path.join(DATA, *partes)


def carpeta_data(*partes):
    r = data(*partes)
    os.makedirs(r, exist_ok=True)
    return r


def carpeta_sonidos():
    """Carpeta de los sonidos por defecto. La primera vez ordena lo que hubiera con la organización antigua:
    los archivos sueltos de data/sonidos pasan a data/sonidos/por_defecto y los packs de data/packs a data/sonidos."""
    import shutil
    raiz = carpeta_data("sonidos")
    dest = os.path.join(raiz, POR_DEFECTO)
    os.makedirs(dest, exist_ok=True)
    try:
        for f in os.listdir(raiz):
            origen = os.path.join(raiz, f)
            if os.path.isfile(origen) and (f.lower().endswith(EXT_AUDIO) or f in ("_version.txt", "_niveles.json")):
                if os.path.exists(os.path.join(dest, f)):
                    os.remove(origen)
                else:
                    shutil.move(origen, os.path.join(dest, f))
        viejos = data("packs")
        if os.path.isdir(viejos):
            for f in os.listdir(viejos):
                if os.path.isdir(os.path.join(viejos, f)) and not os.path.exists(os.path.join(raiz, f)):
                    shutil.move(os.path.join(viejos, f), os.path.join(raiz, f))
            shutil.rmtree(viejos, ignore_errors=True)
    except OSError:
        pass
    return dest


EXT_AUDIO = (".wav", ".ogg", ".flac", ".mp3")
# Extensiones de los archivos protegidos (cifrados) del juego compilado. En el código fuente todo es .json legible.
EXT_DATOS = ".pbd"      # datos del juego: mapas, misiones, armas, vehículos
EXT_MOD = ".pbm"        # mods guardados con el editor
EXT_PARTIDA = ".pbs"    # partidas guardadas
EXT_CONFIG = ".pbc"     # opciones, botones del mando y clave del modo IA


def archivo_config(nombre):
    """Ruta de un archivo de configuración: nombre.pbc (protegido) en el juego compilado, nombre.json en el código fuente.
    Si solo existe el de la otra forma (una configuración de antes de compilar), se devuelve ese para leerlo."""
    from . import cifrado
    carpeta = carpeta_data("config")
    propia = os.path.join(carpeta, nombre + (EXT_CONFIG if cifrado.COMPILADO else ".json"))
    return propia
DATOS = data("datos")
MODS = data("mods")
PACKS = data("sonidos")                       # aquí dentro va una carpeta por pack
POR_DEFECTO = "por_defecto"
SONIDOS = data("sonidos", POR_DEFECTO)        # los sonidos de serie, que el juego regenera si faltan
RADIO = data("radio")
MI_MUSICA = data("radio", "mi_musica")
MUSICA = data("musica")
DOCS = data("docs")
CONFIG = data("config")
