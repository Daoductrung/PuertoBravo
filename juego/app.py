"""Aplicación: ventana, bucle principal y pila de pantallas."""
import os
import sys
import traceback

import pygame

from . import NOMBRE, VERSION, rutas
from . import menus_juego, mundo, packs, sintesis
from .audio import Mezclador
from .config import Config
from .mando import Mando
from .musica import MusicaAmbiente, Radio
from .voz import Voz


class EventoFalso:
    def __init__(self, key, mod=0, unicode=""):
        self.key = key
        self.mod = mod
        self.unicode = unicode


class App:
    def __init__(self, pruebas=False):
        self.pruebas = pruebas
        self.cfg = Config(os.path.join(rutas.DATA, "config_pruebas.json") if pruebas else None)
        if pruebas:
            from .config import POR_DEFECTO
            self.cfg.v = dict(POR_DEFECTO)
            self.cfg.guardar = lambda: None
        self.voz = Voz(self.cfg["voz_sapi"], muda=pruebas)
        self.mez = Mezclador(dispositivo=not pruebas)
        self.aplicar_volumenes()
        self.pila = []
        self.teclas = set()
        self.activo = True
        self.partida = None
        self.pantalla = None
        self.fuente = None
        self.fuente_g = None
        pygame.init()
        if not pruebas:
            self.pantalla = pygame.display.set_mode((900, 420))
            pygame.display.set_caption(NOMBRE)
            pygame.key.set_repeat(0)
            self.fuente = pygame.font.SysFont("segoeui,arial", 26)
            self.fuente_g = pygame.font.SysFont("segoeui,arial", 38, bold=True)
            self._dibujar("Cargando sonidos...")
            self.voz.decir(f"{NOMBRE}. Cargando, espera un momento.", True)
        self.info_sonidos = packs.cargar(self.mez, self.cfg)
        self.radio = Radio(self.mez, rutas.carpeta_data("radio"))
        self.ambiente = MusicaAmbiente(self.mez, rutas.carpeta_data("musica"))
        self.datos = mundo.cargar_datos()
        self.mapas = mundo.crear_mapas(self.datos)
        self.mundo = self.mapas.get("puerto_bravo") or next(iter(self.mapas.values()))
        self.aplicar_adultos()
        self.reloj = pygame.time.Clock()
        self.mando = Mando(self)
        if self.mez.error and not pruebas:
            self.voz.decir("Aviso: no se ha podido abrir la tarjeta de sonido. El juego funcionará sin audio.")
        for e in self.datos["errores_mods"]:
            self.voz.decir("Error en un mod: " + e)
        menus_juego.principal(self)

    # ------------------------------------------------------------------ audio
    def aplicar_volumenes(self):
        for k in ("maestro", "efectos", "ambiente", "musica", "interfaz"):
            self.mez.vols[k] = self.cfg["vol_" + k]

    def son(self, nombre, **kw):
        kw.setdefault("cat", "interfaz")
        return self.mez.sonar(nombre, **kw)

    def decir(self, texto, interrumpir=False):
        self.voz.decir(texto, interrumpir)

    def recargar_sonidos(self):
        """Vuelve a cargar los sonidos: tras elegir otro pack o cambiar el igualado de volumen."""
        self.info_sonidos = packs.cargar(self.mez, self.cfg)
        return self.info_sonidos

    def aplicar_adultos(self):
        """Muestra u oculta en todos los mapas los lugares del contenido para adultos."""
        for m in self.mapas.values():
            m.filtrar(self.cfg["adultos"])
        p = getattr(self, "partida", None)
        if p is not None:
            p.reconstruir_lugares()

    def _musica(self, dt):
        """Decide qué música de ambiente toca: ninguna si suena la radio del vehículo."""
        deseada = None
        if self.cfg["musica_ambiente"]:
            p = self.partida
            if p is None or p not in self.pila:
                deseada = "menu"
            elif not (p.j.veh and self.radio.id_actual() != "apagada"):
                deseada = p.estado_musica()
        self.ambiente.actualizar(dt, deseada, self.cfg["vol_ambiente_musical"] * 0.7)
        self.radio.actualizar(dt)

    def vibrar(self, grave, agudo, ms):
        self.mando.vibrar(grave, agudo, ms)

    # ------------------------------------------------------------------- pila
    def abrir(self, pantalla):
        self.pila.append(pantalla)
        self.teclas.clear()
        pantalla.al_entrar()

    def cerrar(self, pantalla=None):
        if not self.pila:
            return
        if pantalla is None:
            pantalla = self.pila[-1]
        if pantalla not in self.pila:
            return
        era_cima = self.pila[-1] is pantalla
        self.pila.remove(pantalla)
        self.teclas.clear()
        cima = self.pila[-1] if self.pila else None
        if hasattr(pantalla, "cerrado"):
            pantalla.cerrado()
        if era_cima and self.pila and self.pila[-1] is cima:
            cima.al_entrar()

    def empezar_partida(self, guardado, personaje=None):
        from .partida import Partida
        if self.partida:
            self.partida.silenciar()
        self.pila.clear()
        self.partida = Partida(self, guardado, personaje)
        self.mez.mundo_pausado = False
        self.pila.append(self.partida)
        if guardado:
            self.son("guardado")
            p = self.partida
            self.decir(f"Partida cargada. {p.mundo.describir(p.j.x, p.j.y)}. Son las {p.hora_txt()}. {p.objetivo_txt()}", True)
        self.partida.al_entrar()

    def volver_al_menu(self):
        if self.partida:
            self.partida.silenciar()
        self.partida = None
        self.pila.clear()
        self.cfg.guardar()
        menus_juego.principal(self)

    def salir(self):
        self.activo = False

    # ------------------------------------------------------------------ bucle
    def evento_tecla(self, ev):
        self.teclas.add(ev.key)
        if self.pila:
            self.pila[-1].tecla(ev)

    def paso(self, dt):
        if self.pila:
            cima = self.pila[-1]
            self.mez.mundo_pausado = getattr(cima, "pausa_mundo", True)
            self.mando.actualizar(dt)
            cima.actualizar(dt)
            if self.partida is not None:
                self.partida.red_paso(dt)          # los amigos conectados siguen oyéndote aunque tengas un menú abierto
            self._musica(dt)
        self.mez.actualizar()

    def inyectar(self, key, mod=0, unicode="", soltar=True):
        """Simula una pulsación (pruebas automáticas)."""
        self.evento_tecla(EventoFalso(key, mod, unicode))
        if soltar:
            self.teclas.discard(key)

    def _dibujar(self, forzar=None):
        if not self.pantalla:
            return
        self.pantalla.fill((0, 0, 0))
        self.pantalla.blit(self.fuente_g.render(NOMBRE, True, (255, 220, 0)), (20, 14))
        texto = forzar or self.voz.ultimo()
        y = 80
        palabras = texto.split(" ")
        linea = ""
        for w in palabras:
            if self.fuente.size(linea + " " + w)[0] > 860:
                self.pantalla.blit(self.fuente.render(linea, True, (255, 255, 255)), (20, y))
                y += 32
                linea = w
                if y > 380:
                    break
            else:
                linea = (linea + " " + w).strip()
        if linea and y <= 380:
            self.pantalla.blit(self.fuente.render(linea, True, (255, 255, 255)), (20, y))
        pygame.display.flip()

    def bucle(self):
        ultimo = None
        try:
            while self.activo:
                dt = self.reloj.tick(60) / 1000.0
                for ev in pygame.event.get():
                    if self.mando.evento(ev):
                        continue
                    if ev.type == pygame.QUIT:
                        self.activo = False
                    elif ev.type == pygame.KEYDOWN:
                        self.evento_tecla(ev)
                    elif ev.type == pygame.KEYUP:
                        self.teclas.discard(ev.key)
                    elif ev.type in (pygame.WINDOWFOCUSLOST,):
                        self.teclas.clear()
                self.paso(dt)
                if self.voz.ultimo() != ultimo:
                    ultimo = self.voz.ultimo()
                    self._dibujar()
        except Exception:
            self._registrar_error()
        finally:
            self.cerrar_todo()

    def _registrar_error(self):
        texto = traceback.format_exc()
        try:
            with open(rutas.data("error.log"), "a", encoding="utf-8") as f:
                f.write(texto + "\n")
        except OSError:
            pass
        if self.partida and not self.partida.mision:
            try:
                menus_juego.escribir_ranura(self.partida, "auto")
            except Exception:
                pass
        self.voz.decir("Ha ocurrido un error inesperado y el juego debe cerrarse. Tu partida se ha guardado automáticamente. Los detalles están en el archivo error punto log de la carpeta data.", True)
        pygame.time.wait(6000)

    def cerrar_todo(self):
        self.cfg.guardar()
        for cargador in (self.radio, self.ambiente):       # si aún están cargando música, se paran antes de cerrar
            try:
                cargador.cancelar()
            except Exception:
                pass
        self.mez.cerrar()
        pygame.quit()
