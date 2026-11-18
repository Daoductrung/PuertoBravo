"""Panel del servidor en línea de Puerto Bravo: punto de entrada del programa con ventana.

Arranca y administra el mismo servidor que servidor_main.py lleva por consola, pero desde una ventana accesible.
"""
import sys


def main():
    from panel_servidor import situarse
    situarse()                                   # servidor.conf y los datos, en la carpeta del servidor
    from panel_servidor.ventana import ejecutar
    ruta = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    ejecutar(ruta, arrancar="--arrancar" in sys.argv[1:])


if __name__ == "__main__":
    main()
