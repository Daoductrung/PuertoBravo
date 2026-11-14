"""Protege (o vuelve a dejar legibles) los archivos JSON de una carpeta data.

    .venv\\Scripts\\python.exe herramientas\\cifrar_datos.py dist\\PuertoBravo\\data          protege datos y mods
    .venv\\Scripts\\python.exe herramientas\\cifrar_datos.py dist\\PuertoBravo\\data abrir    los deja otra vez legibles

Lo usa compilar.bat sobre la carpeta compilada. Nunca se ejecuta sobre la carpeta data del proyecto:
el código fuente trabaja siempre con JSON legible.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import cifrado, rutas          # noqa: E402

CARPETAS = ("datos", "mods")


def recorrer(data, abrir=False):
    hechos = 0
    for sub in CARPETAS:
        for base, _, archivos in os.walk(os.path.join(data, sub)):
            for f in archivos:
                if f.lower().endswith((".json", ".json.desactivado")):
                    ruta = os.path.join(base, f)
                    hechos += bool(cifrado.descifrar_archivo(ruta) if abrir else cifrar_archivo_seguro(ruta))
    return hechos


def cifrar_archivo_seguro(ruta):
    cambiado = cifrado.cifrar_archivo(ruta)
    cifrado.leer_json(ruta)                  # se comprueba que lo que queda se puede volver a leer
    return cambiado


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Indica la carpeta data que quieres proteger.")
    carpeta = os.path.abspath(sys.argv[1])
    if os.path.normcase(carpeta) == os.path.normcase(os.path.abspath(rutas.DATA)):
        sys.exit("Esta es la carpeta data del proyecto: no se protege, el codigo fuente trabaja con JSON legible.")
    n = recorrer(carpeta, abrir="abrir" in sys.argv[2:])
    print(f"  {n} archivos JSON", "legibles de nuevo" if "abrir" in sys.argv[2:] else "protegidos")
