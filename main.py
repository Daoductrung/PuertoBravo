"""Puerto Bravo: Ley del Asfalto. Punto de entrada."""
import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


_UNICA = None


def ya_abierto():
    """¿Hay otro Puerto Bravo abierto? En Windows, con un cerrojo con nombre. Las copias de pruebas pueden abrir varios."""
    global _UNICA
    if sys.platform != "win32":
        return False
    from juego import enlinea
    if enlinea.varias_instancias():
        return False
    try:
        import ctypes
        k = ctypes.windll.kernel32
        _UNICA = k.CreateMutexW(None, False, "PuertoBravoLeyDelAsfalto")
        if k.GetLastError() == 183:                      # ya existía
            ctypes.windll.user32.MessageBoxW(None, "Puerto Bravo ya está abierto. Solo se puede abrir una vez.", "Puerto Bravo", 0x40)
            return True
    except Exception:
        pass
    return False


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--probar-motor-voz":
        # El juego se lanza a sí mismo así para probar el motor de voz en un proceso aparte: si el motor se cae de golpe,
        # se cae este proceso y no el juego. No abre ventana, ni registro, ni cuenta como «ya abierto».
        from juego import vozgen
        os._exit(vozgen.prueba_en_este_proceso(sys.argv[2] if len(sys.argv) > 2 else None))
    if len(sys.argv) > 2 and sys.argv[1] == "--relanzar-servidores":
        # Lo llama el instalador al terminar de actualizar: vuelve a arrancar los servidores en línea que había abiertos
        # antes, según la nota que dejó el juego. No abre ventana ni registro, ni cuenta como «ya abierto».
        from juego import actualizador
        actualizador.relanzar_servidores(sys.argv[2])
        os._exit(0)
    if ya_abierto():
        return 4
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
