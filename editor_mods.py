"""Editor de mods de Puerto Bravo: Ley del Asfalto. Punto de entrada."""
import os
import sys
import traceback

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))


def main():
    try:
        from editor.ventana import ejecutar
        ejecutar()
    except Exception:
        from juego import rutas
        try:
            with open(os.path.join(rutas.carpeta_data(), "error_editor.log"), "a", encoding="utf-8") as f:
                f.write(traceback.format_exc() + "\n")
        except OSError:
            pass
        raise


if __name__ == "__main__":
    main()
