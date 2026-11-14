"""Puerto Bravo: Ley del Asfalto. Punto de entrada."""
import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def main():
    from juego import procesador, registro
    registro.iniciar("juego")
    # Antes de cargar nada más: elegir la biblioteca de cálculo que este procesador puede usar.
    if not procesador.preparar():
        procesador.avisar_incompatible(registro)
        registro.cerrar()
        return 3
    registro.info("arranque", "Biblioteca de cálculo elegida", **procesador.resumen())
    try:
        from juego.app import App
        app = App()
    except Exception:
        registro.excepcion("arranque", "El juego no ha podido arrancar")
        registro.cerrar()
        raise
    app.bucle()
    return 0


if __name__ == "__main__":
    sys.exit(main())
