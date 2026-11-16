"""Servidor en línea de Puerto Bravo: punto de entrada del ejecutable de Windows."""
import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

if __name__ == "__main__":
    from servidor.__main__ import main
    sys.exit(main())
