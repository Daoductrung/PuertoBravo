"""Puerto Bravo: Ley del Asfalto. Punto de entrada."""
import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def main():
    from juego import registro
    registro.iniciar("juego")
    try:
        from juego.app import App
        app = App()
    except Exception:
        registro.excepcion("arranque", "El juego no ha podido arrancar")
        registro.cerrar()
        raise
    app.bucle()


if __name__ == "__main__":
    main()
