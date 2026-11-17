"""Servidor en línea de Puerto Bravo: punto de entrada del ejecutable de consola de Windows."""
import os
import sys

if getattr(sys, "frozen", False):
    # En el juego compilado, todo lo del servidor vive en la carpeta servidor, junto al juego: la configuración, los
    # datos y las copias. Así queda junto y aparte, y las actualizaciones del juego no lo tocan.
    _carpeta = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "servidor")
    os.makedirs(_carpeta, exist_ok=True)
    os.chdir(_carpeta)

if __name__ == "__main__":
    from servidor.__main__ import main
    sys.exit(main())
