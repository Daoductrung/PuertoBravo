"""Protege (o vuelve a dejar legibles) los archivos JSON de una carpeta data.

    .venv\\Scripts\\python.exe herramientas\\cifrar_datos.py dist\\PuertoBravo\\data          protege datos, mods y los JSON de los packs
    .venv\\Scripts\\python.exe herramientas\\cifrar_datos.py dist\\PuertoBravo\\data abrir    los deja otra vez legibles

Lo usa compilar.bat sobre la carpeta compilada. Nunca se ejecuta sobre la carpeta data del proyecto:
el código fuente trabaja siempre con JSON legible.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import cifrado, rutas          # noqa: E402

CARPETAS = ("datos", "mods", "sonidos")      # en sonidos solo hay JSON de apoyo: pack.json y _niveles.json


def _cambiar(f, de, a):
    """Nombre de archivo con la extensión cambiada, respetando el .desactivado final de los mods apagados."""
    cola = ".desactivado" if f.lower().endswith(".desactivado") else ""
    cuerpo = f[:len(f) - len(cola)] if cola else f
    return cuerpo[:-len(de)] + a + cola if cuerpo.lower().endswith(de) else None


def recorrer(data, abrir=False):
    """Protege los JSON de datos y mods y les pone su extensión propia (.pbd y .pbm). Con abrir=True, lo deshace."""
    hechos = 0
    for sub in CARPETAS:
        propia = rutas.EXT_MOD if sub == "mods" else rutas.EXT_DATOS
        de, a = (propia, ".json") if abrir else (".json", propia)
        for base, _, archivos in os.walk(os.path.join(data, sub)):
            for f in archivos:
                nuevo = _cambiar(f, de, a)
                if nuevo is None:
                    continue
                ruta, destino = os.path.join(base, f), os.path.join(base, nuevo)
                if abrir:
                    cifrado.descifrar_archivo(ruta)
                else:
                    cifrado.cifrar_archivo(ruta)
                    cifrado.leer_json(ruta)          # se comprueba que lo que queda se puede volver a leer
                os.replace(ruta, destino)
                hechos += 1
    return hechos


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Indica la carpeta data que quieres proteger.")
    carpeta = os.path.abspath(sys.argv[1])
    if os.path.normcase(carpeta) == os.path.normcase(os.path.abspath(rutas.DATA)):
        sys.exit("Esta es la carpeta data del proyecto: no se protege, el codigo fuente trabaja con JSON legible.")
    n = recorrer(carpeta, abrir="abrir" in sys.argv[2:])
    print(f"  {n} archivos JSON", "legibles de nuevo" if "abrir" in sys.argv[2:] else "protegidos")
