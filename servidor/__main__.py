"""Arranque del servidor en línea de Puerto Bravo.

    python -m servidor                      con servidor.conf de la carpeta actual, si existe
    python -m servidor mi_servidor.conf     con otro archivo de configuración
    python -m servidor --ejemplo            escribe un servidor.conf de ejemplo y sale
    python -m servidor --comprobar          revisa servidor.conf, dice lo que no vale y sale
    python -m servidor --opciones           dice todas las opciones, con su explicación, y sale
    python -m servidor --parar              para con orden el servidor que está en marcha con esa configuración
    python -m servidor --puerto=47821       cualquier opción se puede dar también así, sin tocar el archivo

Mientras funciona, se le pueden escribir órdenes: ayuda las dice todas.
"""
import asyncio
import os
import signal
import sys
import threading
import time

from . import opciones
from .nucleo import CONFIG, Servidor, leer_config

# El ejemplo de servidor.conf sale de la descripción de las opciones: no se escribe a mano, y así no se queda atrás.
EJEMPLO = opciones.texto_conf()


# Para parar con orden un servidor que no tiene consola delante (una tarea programada, un servicio): basta con dejar
# este archivo en su carpeta de datos. El servidor lo ve, lo borra, avisa a los jugadores, lo guarda todo y sale.
ARCHIVO_PARAR = "parar.txt"


def _hora():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def pedir_parada(cfg, espera=20.0):
    """Pide a un servidor en marcha que pare, dejándole el archivo de parada. Devuelve si lo ha recogido."""
    ruta = os.path.join(cfg["datos"], ARCHIVO_PARAR)
    if not os.path.isdir(cfg["datos"]):
        print("No existe la carpeta de datos «%s»: ahí no hay ningún servidor que parar." % cfg["datos"])
        return False
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("parar\n")
    fin = time.time() + espera
    while time.time() < fin:
        if not os.path.exists(ruta):
            print("El servidor ha recogido la orden: avisa a los jugadores, lo guarda todo y se para.")
            return True
        time.sleep(0.5)
    try:
        os.remove(ruta)
    except OSError:
        pass
    print("Nadie ha recogido la orden: no parece que haya un servidor en marcha con esa carpeta de datos.")
    return False


def _vigilar_cierre_de_consola(parar, parado):
    """En Windows, cerrar la ventana de la consola, cerrar la sesión o apagar el equipo también paran el servidor con
    orden: se avisa, se guarda todo y se sale, en vez de cortarlo en seco. Devuelve algo que hay que conservar."""
    if os.name != "nt":
        return None
    try:
        import ctypes

        @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
        def manejador(tipo):
            if tipo in (2, 5, 6):                # cerrar la ventana, cerrar la sesión, apagar el equipo
                parar()
                parado.wait(4.5)                 # Windows da unos cinco segundos antes de cortar
                return 1
            return 0
        ctypes.windll.kernel32.SetConsoleCtrlHandler(manejador, 1)
        return manejador
    except Exception:
        return None


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    ruta = next((a for a in args if not a.startswith("--")), "servidor.conf")
    if "--ejemplo" in args:
        if os.path.exists(ruta):
            print("Ya hay un %s en esta carpeta. No lo toco." % os.path.basename(ruta))
            return 1
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(EJEMPLO)
        print("Escrito %s. Ábrelo con un editor de texto, cámbialo a tu gusto y arranca el servidor." % os.path.basename(ruta))
        return 0
    if "--opciones" in args:
        print(EJEMPLO)
        return 0
    avisos = []
    cfg = leer_config(ruta, avisos)
    for a in args:                                           # también valen opciones sueltas: --puerto=47821
        if a.startswith("--") and "=" in a:
            k, v = a[2:].split("=", 1)
            k = k.strip().lower()
            if k in CONFIG:
                valor, error = opciones.validar_valor(k, v)
                if error:
                    avisos.append("--%s: %s. No se le hace caso." % (k, error))
                else:
                    cfg[k] = valor
            else:
                avisos.append("--%s: no existe ninguna opción con ese nombre." % k)
    if "--parar" in args:
        return 0 if pedir_parada(cfg) else 1
    if "--comprobar" in args:
        if not os.path.exists(ruta):
            print("No hay ningún archivo %s. Con --ejemplo se escribe uno." % ruta)
            return 1
        for a in avisos:
            print(a)
        print("La configuración tiene %d problemas." % len(avisos) if avisos else "La configuración está bien.")
        return 1 if avisos else 0
    try:
        srv = Servidor(cfg)
    except Exception as e:                                   # la carpeta de datos no se puede crear, la base está dañada...
        print("No se puede arrancar con la carpeta de datos «%s»: %s: %s" % (cfg["datos"], type(e).__name__, e))
        return 2
    srv.ruta_conf = os.path.abspath(ruta) if os.path.exists(ruta) else None
    srv.log = lambda t: print("%s  %s" % (_hora(), t), flush=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for a in avisos:
        srv.log("Configuración: " + a)
    try:
        loop.run_until_complete(srv.iniciar())
    except OSError as e:
        print("No se pudo abrir el puerto %s: %s. Puede que el servidor ya esté en marcha, o que otro programa use ese puerto." % (cfg["puerto"], e))
        return 2
    except RuntimeError as e:
        print(str(e))
        return 2
    if not os.path.exists(ruta):
        srv.log("No hay archivo de configuración: uso los valores de serie. Con --ejemplo se escribe uno.")
    srv.log("Datos del mundo: versión %s, huella %s. %d localidades." % (srv.mundo.get("version"), srv.mundo.get("huella"), len(srv.mundo["mapas"])))
    tope = int(srv.cfg["max_jugadores"])
    srv.log("Caben %s." % (("%d jugadores a la vez" % tope) if tope > 0 else "todos los jugadores que entren: no hay límite"))
    if srv.huella_cert:
        srv.log("Huella del certificado: %s" % srv.huella_cert)
    srv.log("Escribe ayuda para ver las órdenes.")

    def consola():
        try:
            for linea in sys.stdin:
                linea = linea.strip()
                if linea:
                    loop.call_soon_threadsafe(lambda t=linea: print(srv.orden(t), flush=True))
        except Exception:
            pass
    threading.Thread(target=consola, daemon=True).start()

    def parar(*_):
        loop.call_soon_threadsafe(lambda: loop.create_task(srv.detener()))
    parado = threading.Event()
    _vigilancia = _vigilar_cierre_de_consola(parar, parado)      # hay que conservar la referencia mientras funcione
    for s in (signal.SIGINT, getattr(signal, "SIGTERM", None), getattr(signal, "SIGBREAK", None)):
        if s is not None:
            try:
                signal.signal(s, parar)
            except (ValueError, OSError):
                pass

    archivo_parar = os.path.join(srv.cfg["datos"], ARCHIVO_PARAR)
    try:
        os.remove(archivo_parar)                             # una orden de parar que quedó de otra vez no cuenta
    except OSError:
        pass

    async def esperar():
        while srv.activo:
            await asyncio.sleep(0.5)
            if os.path.exists(archivo_parar):                # alguien ha pedido parar con --parar
                try:
                    os.remove(archivo_parar)
                except OSError:
                    pass
                srv.log("Se ha pedido parar el servidor.")
                await srv.detener()
        for _ in range(100):                                 # hasta que termine de guardar
            if srv.detenido:
                break
            await asyncio.sleep(0.1)
    try:
        loop.run_until_complete(esperar())
    except KeyboardInterrupt:
        loop.run_until_complete(srv.detener())
    print("%s  Servidor parado. Todo guardado." % _hora(), flush=True)
    parado.set()
    if _vigilancia is not None:                              # ya no hay nada que vigilar: se retira
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleCtrlHandler(_vigilancia, 0)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
