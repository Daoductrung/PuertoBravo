import os
import shutil
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ.setdefault("PUERTOBRAVO_IDIOMA", "es")          # las pruebas, en el idioma de origen: el inglés tiene las suyas
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import pytest

os.startfile = lambda *a, **k: None      # las pruebas no abren el navegador ni carpetas

from juego import menus_juego, rutas
from juego.i18n import tr


@pytest.fixture
def app():
    menus_juego.CARPETA = "partidas_pruebas"
    shutil.rmtree(rutas.data("partidas_pruebas"), ignore_errors=True)
    from juego.app import App
    a = App(pruebas=True)
    yield a
    a.radio.cancelar()         # los hilos que cargan la música deben parar antes de cerrar: si no, el intérprete puede caerse al salir
    a.ambiente.cancelar()
    a.mez.cerrar()
    shutil.rmtree(rutas.data("partidas_pruebas"), ignore_errors=True)


class Robot:
    """Maneja el juego como lo haría una persona: teclas y fotogramas."""

    def __init__(self, app):
        self.app = app

    @property
    def p(self):
        return self.app.partida

    def tecla(self, k, mod=0, unicode=""):
        self.app.inyectar(k, mod, unicode)

    def frames(self, n=1, mantener=(), dt=1 / 30):
        for _ in range(n):
            for k in mantener:
                self.app.teclas.add(k)
            self.app.paso(dt)
            self.app.mez.render(256)
        for k in mantener:
            self.app.teclas.discard(k)

    def saltar_dialogos(self, tope=40):
        from juego.menus import Dialogo, Menu
        for _ in range(tope):
            cima = self.app.pila[-1]
            if isinstance(cima, Dialogo):
                self.tecla(pygame.K_ESCAPE)
            elif isinstance(cima, Menu) and not cima.escapable and cima is not self.app.pila[0]:
                cima.i = len(cima.opciones) - 1
                self.tecla(pygame.K_RETURN)
            else:
                return

    def nueva_partida(self, personaje="Dani", genero="h"):
        from juego.menus import Menu
        m = self.app.pila[-1]
        assert isinstance(m, Menu)
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto in ("Nueva partida", tr("Nueva partida")))
        self.tecla(pygame.K_RETURN)
        cima = self.app.pila[-1]
        if isinstance(cima, Menu) and cima.titulo in ("Elige tu personaje", tr("Elige tu personaje")):
            cima.i = next((k for k, o in enumerate(cima.opciones) if o.texto.startswith(personaje)), 0)
            self.tecla(pygame.K_RETURN)
            cima = self.app.pila[-1]
            if isinstance(cima, Menu) and cima.titulo.startswith(tr("¿Cómo quieres que te hablen{v}?").split("{")[0]):          # los personajes sin género fijo lo preguntan
                cima.i = 1 if genero == "m" else 0
                self.tecla(pygame.K_RETURN)
        self.saltar_dialogos()
        assert self.app.pila[-1] is self.p
        return self.p

    def dicho(self):
        return " | ".join(self.app.voz.registro[-40:])


@pytest.fixture
def robot(app):
    return Robot(app)
