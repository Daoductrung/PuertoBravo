"""Editor de mods de Puerto Bravo: Ley del Asfalto. Punto de entrada."""
import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))


def main():
    from juego import procesador, registro
    registro.iniciar("editor")
    if not procesador.preparar():
        procesador.avisar_incompatible(registro)
        registro.cerrar()
        return
    registro.escribir_sistema([])
    try:
        from editor.ventana import ejecutar
        registro.info("editor", "Se abre el editor de mods")
        ejecutar()
        registro.cerrar()
    except Exception:
        registro.excepcion("editor", "El editor se ha cerrado por un error")
        registro.cerrar()
        raise


if __name__ == "__main__":
    main()
