"""El servidor, en su propio hilo, para que la ventana no se quede nunca esperando.

El servidor funciona con asyncio en un hilo aparte. La ventana no toca nada suyo directamente: le pide las cosas con
``pedir`` (que las ejecuta dentro del hilo del servidor y avisa con el resultado) y lee ``foto``, un resumen que el
propio servidor deja preparado cada segundo.

Este módulo no usa wxPython: se puede probar sin ventanas. Quien lo usa decide cómo llevar los avisos a la interfaz
(la ventana lo hace con ``wx.CallAfter``).
"""
import asyncio
import os
import threading
import time

from servidor import copias, opciones
from servidor.nucleo import Servidor

PARADO, ARRANCANDO, EN_MARCHA, PARANDO = "parado", "arrancando", "en_marcha", "parando"
TEXTO_ESTADO = {PARADO: "Parado", ARRANCANDO: "Arrancando", EN_MARCHA: "En marcha", PARANDO: "Parando"}


class Motor:
    def __init__(self, ruta_conf, registrar=None, avisar=None):
        """``registrar(texto)`` recibe cada línea del registro. ``avisar(que, dato)`` recibe los cambios:
        ("estado", nuevo estado) y ("error", explicación). Las dos se llaman desde el hilo del servidor."""
        self.ruta_conf = os.path.abspath(ruta_conf)
        self.registrar = registrar or (lambda texto: None)
        self.avisar = avisar or (lambda que, dato: None)
        self.estado = PARADO
        self.foto = None                         # el último resumen del servidor, o None si está parado
        self.srv = None
        self.loop = None
        self.hilo = None
        self.cfg = {}                            # la configuración con la que está en marcha
        self._candado = threading.Lock()
        self._parado = threading.Event()
        self._parado.set()
        self.ultimo_error = ""

    # ----------------------------------------------------------- configuración
    def leer_config(self):
        """La configuración del archivo, ya comprobada: (opciones, avisos)."""
        return opciones.leer(self.ruta_conf)

    def guardar_config(self, cfg):
        """Escribe servidor.conf, comentado. Devuelve los problemas que tuviera lo pedido."""
        return opciones.guardar(self.ruta_conf, cfg)

    def _resolver(self, cfg):
        """Las rutas de la configuración parten de la carpeta donde está servidor.conf, se abra el panel desde donde se abra."""
        cfg = dict(cfg)
        base = os.path.dirname(self.ruta_conf)
        for clave in ("datos", "certificado", "llave"):
            if cfg.get(clave) and not os.path.isabs(str(cfg[clave])):
                cfg[clave] = os.path.join(base, str(cfg[clave]))
        return cfg

    def carpeta_datos(self, cfg=None):
        return os.path.abspath(self._resolver(cfg or self.leer_config()[0])["datos"])

    def aplicar_config(self, cfg, al_terminar=None):
        """Aplica al servidor en marcha lo que se puede cambiar sin reiniciar. El resultado, por ``al_terminar``:
        (opciones aplicadas, opciones que esperan al reinicio)."""
        return self.pedir(lambda srv: srv.aplicar_config(self._resolver(cfg)), al_terminar)

    # ------------------------------------------------------------------ estado
    def _poner_estado(self, estado):
        self.estado = estado
        if estado == PARADO:
            self._parado.set()
        else:
            self._parado.clear()
        self.avisar("estado", estado)

    def _linea(self, texto):
        self.registrar("%s  %s" % (time.strftime("%H:%M:%S"), texto))

    def en_marcha(self):
        return self.estado == EN_MARCHA

    def esperar_parado(self, segundos=20):
        """Espera a que el servidor esté parado del todo. Para cerrar el programa y para las pruebas: la ventana no la usa
        en el hilo de la interfaz salvo al cerrar."""
        return self._parado.wait(segundos)

    # ---------------------------------------------------------------- arrancar
    def arrancar(self):
        """Arranca el servidor con lo que diga servidor.conf. Vuelve enseguida: el resultado llega por ``avisar``."""
        with self._candado:
            if self.estado != PARADO:
                return False
            self._poner_estado(ARRANCANDO)
        cfg, avisos = self.leer_config()
        self.hilo = threading.Thread(target=self._correr, args=(cfg, avisos), name="servidor", daemon=True)
        self.hilo.start()
        return True

    def _correr(self, cfg, avisos):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        srv = None
        try:
            cfg = self._resolver(cfg)
            srv = Servidor(cfg)
            srv.ruta_conf = self.ruta_conf if os.path.exists(self.ruta_conf) else None
            srv.log = self._linea
            for a in avisos:
                self._linea("Configuración: " + a)
            loop.run_until_complete(srv.iniciar())
        except Exception as e:
            if srv is not None:
                try:
                    srv.alm.cerrar()
                except Exception:
                    pass
            if isinstance(e, OSError):
                texto = ("No se ha podido abrir el puerto %s: %s. Puede que el servidor ya esté en marcha en otra ventana, "
                         "o que otro programa esté usando ese puerto." % (cfg.get("puerto"), e))
            elif isinstance(e, RuntimeError):
                texto = str(e)
            else:
                texto = "El servidor no ha podido arrancar: %s: %s" % (type(e).__name__, e)
            self.ultimo_error = texto
            self._linea(texto)
            loop.close()
            self.avisar("error", texto)
            self._poner_estado(PARADO)
            return
        self.srv, self.loop, self.cfg = srv, loop, cfg
        self.foto = srv.resumen()
        self._linea("Datos del mundo: versión %s, huella %s. %d localidades." % (srv.mundo.get("version"), srv.mundo.get("huella"), len(srv.mundo["mapas"])))
        if srv.huella_cert:
            self._linea("Huella del certificado: %s" % srv.huella_cert)
        self._poner_estado(EN_MARCHA)

        async def vigilar():
            while srv.activo:                    # una foto por segundo, para que la ventana no tenga que preguntar
                self.foto = srv.resumen()
                await asyncio.sleep(1.0)
            for _ in range(200):                 # alguien lo ha mandado parar: se espera a que termine de guardar
                if srv.detenido:
                    break
                await asyncio.sleep(0.1)
        try:
            loop.run_until_complete(vigilar())
        except Exception as e:
            self._linea("El servidor se ha parado por un error: %s: %s" % (type(e).__name__, e))
            try:
                loop.run_until_complete(srv.detener())
            except Exception:
                pass
        finally:
            try:
                pendientes = [t for t in asyncio.all_tasks(loop) if not t.done()]
                for t in pendientes:
                    t.cancel()
                if pendientes:
                    loop.run_until_complete(asyncio.gather(*pendientes, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            loop.close()
            self.srv, self.loop, self.foto = None, None, None
            self._linea("Servidor parado. Todo guardado.")
            self._poner_estado(PARADO)

    # ------------------------------------------------------------------- parar
    def parar(self, motivo="Quien administra el servidor lo ha parado."):
        """Para el servidor con orden: avisa a los jugadores y lo guarda todo. Vuelve enseguida."""
        with self._candado:
            if self.estado != EN_MARCHA or self.loop is None:
                return False
            self._poner_estado(PARANDO)
        srv, loop = self.srv, self.loop
        try:
            loop.call_soon_threadsafe(lambda: loop.create_task(srv.detener(motivo)))
        except RuntimeError:
            return False
        return True

    # ------------------------------------------------------------------ pedir
    def pedir(self, funcion, al_terminar=None):
        """Ejecuta ``funcion(servidor)`` dentro del hilo del servidor. Cuando acaba llama a ``al_terminar(resultado, error)``,
        también desde ese hilo. Si el servidor no está en marcha, ``al_terminar(None, "parado")`` al momento."""
        srv, loop = self.srv, self.loop
        if srv is None or loop is None or self.estado != EN_MARCHA:
            if al_terminar:
                al_terminar(None, "parado")
            return False

        def ejecutar():
            try:
                resultado, error = funcion(srv), None
            except Exception as e:
                resultado, error = None, "%s: %s" % (type(e).__name__, e)
            if al_terminar:
                al_terminar(resultado, error)
        try:
            loop.call_soon_threadsafe(ejecutar)
        except RuntimeError:
            if al_terminar:
                al_terminar(None, "parado")
            return False
        return True

    def orden(self, texto, al_terminar=None):
        """Una orden de las de la consola: jugadores, aviso, expulsar, vetar, invitar, guardar, copia..."""
        return self.pedir(lambda srv: srv.orden(texto), al_terminar)

    # ------------------------------------------------- copias, con él parado
    def copia_parado(self):
        """Copia de seguridad con el servidor parado. Devuelve la ruta. Se llama desde un hilo de trabajo, no desde la interfaz."""
        return copias.hacer(self.carpeta_datos(), conf=self.ruta_conf if os.path.exists(self.ruta_conf) else None)

    def restaurar(self, ruta_zip, con_conf=False):
        """Restaura una copia. El servidor tiene que estar parado. Se llama desde un hilo de trabajo."""
        if self.estado != PARADO:
            raise RuntimeError("Para restaurar una copia hay que parar antes el servidor.")
        return copias.restaurar(ruta_zip, self.carpeta_datos(), conf=self.ruta_conf, con_conf=con_conf)
