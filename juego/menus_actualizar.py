"""Menú de actualizaciones y aviso al arrancar."""
import os
import sys
import threading

import pygame

from . import VERSION, actualizador as A, registro
from .menus import EntradaTexto, Menu, Opcion

TEXTO_FUENTE = {"servidor": "el servidor del juego", "github": "GitHub", "ambas": "las dos, el servidor del juego y GitHub", "personalizada": "una dirección personalizada"}


class Tarea:
    """Pantalla de espera: hace un trabajo largo sin congelar el juego. Escape lo cancela."""
    pausa_mundo = True

    def __init__(self, app, titulo, trabajo, al_terminar):
        self.app = app
        self.titulo = titulo
        self.trabajo = trabajo                # función(tarea) -> resultado
        self.al_terminar = al_terminar        # función(resultado, error)
        self.cancelada = False
        self.avisos = []                      # textos que el trabajo quiere que se digan
        self.resultado = None
        self.error = None
        self.hecho = False
        self.hilo = None
        self.t_eco = 0.0
        self.estado = ""                      # cuánto lleva, dicho en una frase: lo pone el trabajo y se oye al pulsar una tecla
        self.fondo = False                    # se puede dejar en segundo plano y seguir jugando
        self.en_fondo = False

    def al_entrar(self):
        self.app.decir(self.titulo + ". Espera. Cualquier tecla dice cuánto lleva. Escape cancela."
                       + (" Con la B se queda en segundo plano y sigues con lo que estabas." if self.fondo else ""), True)

    def decir(self, texto):
        self.avisos.append(texto)

    def _correr(self):
        try:
            self.resultado = self.trabajo(self)
        except Exception as e:               # el error se cuenta al jugador en el hilo principal
            self.error = e
        self.hecho = True

    def tecla(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self.cancelada = True
            self.app.decir("Cancelando.", True)
        elif ev.key == pygame.K_b and self.fondo and not self.hecho and self.hilo is not None and not self.app.pruebas:
            self.en_fondo = True
            self.app.cerrar(self)
            if not hasattr(self.app, "tareas_fondo"):
                self.app.tareas_fondo = []
            self.app.tareas_fondo.append(self)
            self.app.son("notificacion")
            self.app.decir(self.titulo + ": sigue en segundo plano. Te aviso cuando termine.", True)
        else:
            self.app.decir(f"{self.titulo}. {self.estado or 'Espera.'}", True)

    def paso_fondo(self):
        """Lo llama el juego en cada vuelta mientras la tarea sigue en segundo plano. True cuando ha terminado."""
        self.avisos.clear()                    # en segundo plano no se va cantando el avance: se pregunta, o se espera al final
        if not self.hecho:
            return False
        self.al_terminar(self.resultado, self.error)
        return True

    def actualizar(self, dt):
        if self.hilo is None:
            if self.app.pruebas:
                self.hilo = True
                self._correr()
            else:
                self.hilo = threading.Thread(target=self._correr, daemon=True)
                self.hilo.start()
        while self.avisos:
            self.app.decir(self.avisos.pop(0))
        if not self.hecho:
            self.t_eco += dt
            if self.t_eco >= 4.0:             # un tictac suave: sigue trabajando
                self.t_eco = 0.0
                self.app.son("menu_mover", vol=0.3)
            return
        self.app.cerrar(self)
        self.al_terminar(self.resultado, self.error)


def _abrir(app):
    """Con qué se abre la red. En las pruebas automáticas nunca se sale a internet."""
    propio = getattr(app, "act_abrir", None)
    if propio is not None:
        return propio
    if app.pruebas:
        def sin_red(url, tiempo=0):
            raise OSError("sin red en las pruebas")
        return sin_red
    return None


def buscar(app, al_no_haber=None):
    cfg = app.cfg

    def trabajo(tarea):
        return A.comprobar(cfg["act_fuente"], cfg["act_url"], abrir=_abrir(app), claves=getattr(app, "act_claves", None))

    def fin(info, error):
        registro.info("actualizar", "Búsqueda de versión nueva", fuente=cfg["act_fuente"], encontrada=getattr(info, "version", "ninguna"),
                      error=f"{type(error).__name__}: {error}" if error is not None else "ninguno")
        if error is not None:
            app.son("error")
            app.decir(str(error) if isinstance(error, A.ErrorActualizacion) else "No se pudo comprobar si hay una versión nueva.", True)
        elif info is None:
            app.son("guardado")
            app.decir(f"Tienes la última versión, la {VERSION}.", True)
        else:
            ofrecer(app, info)
    app.abrir(Tarea(app, f"Buscando actualizaciones en {TEXTO_FUENTE[cfg['act_fuente']]}", trabajo, fin))


def ofrecer(app, info):
    megas = max(1, round(info.tamano / (1024 * 1024)))

    def novedades():
        app.decir(info.novedades or "Esta versión no trae notas.", True)

    def instalar():
        if not A.puede_instalar():
            app.son("error")
            app.decir("Estás jugando desde el código fuente: la versión nueva solo se instala sola en el juego compilado.", True)
            return
        falta = "" if app.pruebas and not hasattr(app, "act_libre") else A.problema_para_descargar(info, libre=getattr(app, "act_libre", None))
        if falta:                                                # no va a caber: mejor saberlo antes de descargar nada
            registro.aviso("actualizar", "No hay sitio en el disco para descargar la versión nueva", version=info.version)
            app.son("error")
            app.decir(falta, True)
            return
        app.cerrar(m)
        descargar(app, info)
    m = Menu(app, f"Hay una versión nueva, la {info.version}. Tienes la {VERSION}", [
        Opcion("Leer las novedades", novedades),
        Opcion(f"Descargar e instalar ahora, {megas} megas", instalar,
               ayuda="Descarga la versión nueva, comprueba que es auténtica, cierra el juego, lo actualiza y lo vuelve a abrir. Tus partidas, tus opciones, tu música y tus mods no se tocan."),
        Opcion("Ahora no", lambda: app.cerrar(m)),
    ])
    app.son("evento")
    app.abrir(m)


def megas(n):
    return f"{n / 2 ** 20:.0f}".replace(".", ",")


def texto_progreso(hecho, total):
    """«42 por ciento: 180 de 430 megas.» Lo que se oye al pulsar una tecla durante una descarga."""
    if not total:
        return f"{megas(hecho)} megas descargados."
    return f"{int(100 * hecho / total)} por ciento: {megas(hecho)} de {megas(total)} megas."


def descargar(app, info):
    estado = {"cuarto": 0, "tarea": None}

    def trabajo(tarea):
        estado["tarea"] = tarea

        def progreso(hecho, total):
            tarea.estado = texto_progreso(hecho, total)
            cuarto = int(4 * hecho / max(1, total))
            if cuarto > estado["cuarto"] and cuarto < 4:
                estado["cuarto"] = cuarto
                tarea.decir(f"{cuarto * 25} por ciento.")
        ruta = A.descargar(info, progreso=progreso, cancelado=lambda: tarea.cancelada, abrir=_abrir(app))
        tarea.estado = "Descarga comprobada. Preparando la instalación."
        tarea.decir("Descarga comprobada. Preparando la instalación.")
        nueva = A.extraer(ruta, os.path.join(A.carpeta_trabajo(), "nueva"))
        try:
            os.remove(ruta)
        except OSError:
            pass
        return A.escribir_instalador(nueva, version=info.version)

    def fin(bat, error):
        registro.info("actualizar", "Descarga de la versión nueva", version=info.version, megas=info.tamano // 2 ** 20,
                      error=f"{type(error).__name__}: {error}" if error is not None else "ninguno")
        if error is not None:
            if not isinstance(error, A.Cancelado):
                app.son("error")
            A.limpiar()
            app.decir(str(error) if isinstance(error, A.ErrorActualizacion) else "No se pudo preparar la actualización.", True)
            return
        if getattr(estado["tarea"], "en_fondo", False):          # se descargó mientras jugabas: se instala cuando tú digas
            app.act_lista = (bat, info.version)
            app.son("guardado")
            app.decir(f"La versión {info.version} ya está descargada. Para instalarla, entra en Opciones, Actualizaciones, Instalar la versión descargada. "
                      "El juego se cerrará, se actualizará y volverá a abrirse solo.")
            return
        _instalar(app, bat)
    app.act_version = info.version
    t = Tarea(app, f"Descargando la versión {info.version}", trabajo, fin)
    t.fondo = True
    app.abrir(t)


def _instalar(app, bat):
    # Antes de cerrar: lo que haría fallar la instalación (otro programa del juego abierto, poco sitio en el disco, una carpeta
    # en la que no se puede escribir). Si hay algo, se dice, la descarga se guarda y se instala cuando esté arreglado.
    comprobar = getattr(app, "act_comprobar", None) or (None if app.pruebas else A.problemas_para_instalar)
    try:
        problemas = comprobar(os.path.join(os.path.dirname(bat), "nueva")) if comprobar else []
    except Exception:
        registro.excepcion("actualizar", "No se pudo comprobar si la actualización se puede instalar")
        problemas = []
    if problemas:
        app.act_lista = (bat, getattr(app, "act_version", "") or "nueva")
        registro.aviso("actualizar", "La actualización no se instala todavía", motivos=" | ".join(problemas))
        app.son("error")
        app.decir("Todavía no se puede instalar. " + " ".join(problemas) + " Cuando esté arreglado, entra en Opciones, Actualizaciones, "
                  "Instalar la versión descargada. La descarga no se pierde.", True)
        return
    if True:
        p = app.partida
        if p is not None and not p.mision:
            try:
                from . import menus_juego
                menus_juego.escribir_ranura(p, "auto")
            except Exception:
                pass
        app.son("guardado")
        app.decir("Todo listo. El juego se cierra, se actualiza y vuelve a abrirse solo en unos segundos.", True)
        try:
            from . import vozgen
            vozgen.parar_prueba()                                # el proceso que prueba el motor de voz es el propio programa: no puede quedarse abierto
        except Exception:
            pass
        if not app.pruebas:
            pygame.time.wait(4500)
            A.lanzar_instalador(bat)
        app.salir()


def opciones(app):
    cfg = app.cfg

    def fuente(d):
        i = A.FUENTES.index(cfg["act_fuente"]) if cfg["act_fuente"] in A.FUENTES else 0
        cfg["act_fuente"] = A.FUENTES[(i + d) % len(A.FUENTES)]

    def auto(d):
        cfg["act_auto"] = not cfg["act_auto"]

    def direccion():
        def hecho(t):
            t = t.strip()
            if t:
                try:
                    A.comprobar_url(t)
                except A.ErrorActualizacion as e:
                    app.son("error")
                    app.decir(str(e), True)
                    return
            cfg["act_url"] = t
            app.decir("Dirección guardada." if t else "Dirección borrada.", True)
        app.abrir(EntradaTexto(app, "Dirección personalizada del archivo version punto json", hecho, inicial=cfg["act_url"], maximo=300,
                               ayuda="La dirección completa, que empiece por https, del archivo version.json. Puedes pegarla con Control V. Sirva de donde sirva, la versión tiene que ir firmada por quien publica el juego."))

    def instalar_lista():
        lista = getattr(app, "act_lista", None)
        if lista:
            app.act_lista = None
            _instalar(app, lista[0])

    def fallo():
        app.decir(app.act_fallo + " El detalle está en la carpeta de registros, en el archivo actualizacion punto log: se llega desde Opciones, Registro para informar de fallos, Abrir la carpeta con todas las sesiones.", True)

    m = Menu(app, "Actualizaciones", ([
        Opcion(f"Instalar la versión descargada, la {app.act_lista[1]}", instalar_lista,
               ayuda="Ya está descargada y comprobada. El juego guarda la partida, se cierra, se actualiza y vuelve a abrirse solo en unos segundos.")] if getattr(app, "act_lista", None) else []) + ([
        Opcion("Por qué falló la última actualización", fallo,
               ayuda="Lo que dejó apuntado el instalador: en qué paso falló, con qué archivo y qué hacer para que la próxima vez salga bien.")] if getattr(app, "act_fallo", None) else []) + [
        Opcion(f"Versión instalada: {VERSION}", lambda: app.decir(f"Tienes la versión {VERSION}.", True)),
        Opcion("Buscar actualizaciones ahora", lambda: buscar(app)),
        Opcion(lambda: f"Buscar al arrancar el juego: {'sí' if cfg['act_auto'] else 'no'}", ajuste=auto,
               ayuda="Al abrir el juego mira si hay una versión nueva y te avisa. No descarga ni instala nada sin que tú lo pidas."),
        Opcion(lambda: f"Actualizar desde: {TEXTO_FUENTE[cfg['act_fuente']]}", ajuste=fuente,
               ayuda="Con las flechas izquierda y derecha eliges de dónde se buscan y se descargan las versiones: el servidor del juego, GitHub, las dos o una dirección que escribas tú. "
                     "Con las dos, se usa la versión más nueva y, si una falla, la otra. Venga de donde venga, solo se instala una versión firmada por quien publica el juego."),
        Opcion(lambda: "Dirección personalizada: " + (cfg["act_url"] or "ninguna"), direccion, ayuda="Solo se usa si eliges actualizar desde una dirección personalizada. Intro para escribirla."),
        Opcion("Volver", lambda: app.cerrar(m)),
    ], al_cerrar=cfg.guardar)
    app.abrir(m)


# ------------------------------------------------------------------ al arrancar
def al_arrancar(app):
    """Tras actualizar, lo dice y limpia. Si está activado, busca una versión nueva sin molestar."""
    if A.ARG_TRAS_ACTUALIZAR in sys.argv or "--actualizacion-fallida" in sys.argv:
        A.limpiar_registro_instalador()                          # el instalador apunta rutas completas: se dejan en el nombre del archivo,
        registro._sanear(A.ruta_registro_instalador())           # y lo demás se limpia como el resto del registro
    if A.ARG_TRAS_ACTUALIZAR in sys.argv:
        A.limpiar()
        registro.info("actualizar", "Primera sesión tras actualizar", version=VERSION)
        app.decir(f"Juego actualizado a la versión {VERSION}. Las novedades están en el manual.")
    elif "--actualizacion-fallida" in sys.argv:
        A.limpiar()
        motivo = A.motivo_del_fallo()
        registro.aviso("actualizar", "La actualización anterior falló y se restauró la versión que había", dicho=motivo, **{k: v for k, v in A.leer_registro_instalador().items() if v and k != "existe"})
        app.act_fallo = motivo
        app.son("error")
        app.decir(f"La actualización no se pudo instalar y se ha dejado la versión que tenías, la {VERSION}. {motivo} "
                  "Lo tienes otra vez en Opciones, Actualizaciones, y el detalle está en la carpeta de registros, en el archivo actualizacion punto log.")
    app.act_aviso = None
    if app.pruebas or not app.cfg["act_auto"]:
        return

    def mirar():
        try:
            app.act_aviso = A.comprobar(app.cfg["act_fuente"], app.cfg["act_url"])
            registro.info("actualizar", "Comprobación al arrancar", fuente=app.cfg["act_fuente"], encontrada=getattr(app.act_aviso, "version", "ninguna"))
        except Exception as e:
            registro.info("actualizar", "Comprobación al arrancar sin resultado", fuente=app.cfg["act_fuente"], motivo=f"{type(e).__name__}: {e}")
            app.act_aviso = None             # sin conexión o sin fuente: al arrancar no se molesta con errores
    threading.Thread(target=mirar, daemon=True).start()


def paso(app):
    """Llamado en cada vuelta del bucle: da el aviso cuando la búsqueda del arranque encuentra algo."""
    info = getattr(app, "act_aviso", None)
    if info is None or app.partida is not None or len(app.pila) != 1:
        return
    app.act_aviso = None
    app.son("evento")
    app.decir(f"Hay una versión nueva del juego, la {info.version}. Para instalarla entra en Opciones, Actualizaciones.")
