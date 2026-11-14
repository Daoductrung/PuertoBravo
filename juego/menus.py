"""Menús y diálogos hablados. Todo se maneja con flechas, Intro y Escape."""
import pygame
from . import registro


class Opcion:
    def __init__(self, texto, accion=None, ajuste=None, ayuda=None):
        self._texto = texto
        self.accion = accion
        self.ajuste = ajuste      # función(delta) para opciones que se cambian con izquierda/derecha
        self.ayuda = ayuda

    @property
    def texto(self):
        return self._texto() if callable(self._texto) else self._texto


class Menu:
    pausa_mundo = True

    def __init__(self, app, titulo, opciones, al_cerrar=None, escapable=True, intro=None):
        self.app = app
        self._titulo = titulo
        self._fuente = opciones            # lista o función que devuelve la lista
        self.opciones = []
        self.i = 0
        self.al_cerrar = al_cerrar
        self.escapable = escapable
        self.intro = intro
        self.refrescar(False)

    @property
    def titulo(self):
        return self._titulo() if callable(self._titulo) else self._titulo

    def refrescar(self, hablar=True):
        self.opciones = list(self._fuente() if callable(self._fuente) else self._fuente)
        self.i = max(0, min(self.i, len(self.opciones) - 1))
        if hablar:
            self.leer()

    def al_entrar(self):
        self.refrescar(False)
        partes = [self.titulo]
        if self.intro:
            partes.append(self.intro)
            self.intro = None
        if self.opciones:
            partes.append(f"{self.opciones[self.i].texto}. {self.i + 1} de {len(self.opciones)}")
        self.app.decir(". ".join(partes), True)

    def leer(self):
        if self.opciones:
            self.app.decir(self.opciones[self.i].texto, True)

    def _mover(self, nuevo):
        n = len(self.opciones)
        if n == 0:
            return
        if nuevo < 0 or nuevo >= n:
            self.app.son("menu_borde")
            nuevo %= n
        else:
            self.app.son("menu_mover")
        self.i = nuevo
        self.leer()

    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_DOWN:
            self._mover(self.i + 1)
        elif k == pygame.K_UP:
            self._mover(self.i - 1)
        elif k == pygame.K_HOME:
            self.app.son("menu_mover")
            self.i = 0
            self.leer()
        elif k == pygame.K_END:
            self.app.son("menu_mover")
            self.i = max(0, len(self.opciones) - 1)
            self.leer()
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if not self.opciones:
                return
            o = self.opciones[self.i]
            if o.accion:
                self.app.son("menu_ok")
                o.accion()
            elif o.ajuste:
                self.app.son("menu_ajuste")
                o.ajuste(1)
                self.leer()
            else:
                self.leer()
        elif k in (pygame.K_LEFT, pygame.K_RIGHT):
            if self.opciones and self.opciones[self.i].ajuste:
                self.app.son("menu_ajuste")
                self.opciones[self.i].ajuste(1 if k == pygame.K_RIGHT else -1)
                self.leer()
        elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            if self.escapable:
                self.app.son("menu_atras")
                self.app.cerrar(self)
        elif k == pygame.K_F1:
            if self.opciones and self.opciones[self.i].ayuda:
                self.app.decir(self.opciones[self.i].ayuda, True)
            else:
                self.app.decir("Flechas arriba y abajo para moverte, Intro para elegir, izquierda y derecha para cambiar un valor, Escape para volver.", True)
        elif k == pygame.K_PAGEUP:
            self.app.voz.repasar(-1)
        elif k == pygame.K_PAGEDOWN:
            self.app.voz.repasar(1)
        elif k == pygame.K_PERIOD:
            self.leer()
        else:
            letra = (getattr(ev, "unicode", "") or "").lower()
            if letra and letra.isalnum():
                n = len(self.opciones)
                for d in range(1, n + 1):
                    q = (self.i + d) % n
                    if self.opciones[q].texto.lower().startswith(letra):
                        self.app.son("menu_mover")
                        self.i = q
                        self.leer()
                        break

    def actualizar(self, dt):
        pass

    def cerrado(self):
        if self.al_cerrar:
            self.al_cerrar()


class Dialogo:
    """Escena de texto: Intro avanza, flecha arriba repite, Escape la salta entera."""
    pausa_mundo = True

    def __init__(self, app, lineas, al_terminar=None, voces=None):
        self.app = app
        self.lineas = [tuple(l) for l in lineas]
        self.i = 0
        self.al_terminar = al_terminar
        self.primera = True
        self.voces = voces              # una grabación por frase, o None donde no hay
        self.canal = None

    def _callar_voz(self):
        if self.canal is not None:
            self.canal.parar()
            self.canal = None

    def _decir(self):
        quien, texto = self.lineas[self.i]
        self._callar_voz()
        self.app.son("dialogo")
        extra = ""
        if self.primera:
            extra = " Pulsa Intro para continuar."
            self.primera = False
        frase = (texto if quien == "Narrador" else f"{quien}: {texto}") + extra
        grabada = self.voces[self.i] if self.voces and self.i < len(self.voces) else None
        if grabada and self.app.cfg["voces_grabadas"]:
            from . import voces
            self.canal = voces.sonar(self.app, grabada)
            if self.canal is not None:
                self.app.voz.mostrar(frase)          # la voz es la grabación; el texto va al braille y al historial
                return
        self.app.decir(frase, True)

    def al_entrar(self):
        if self.i < len(self.lineas):
            self._decir()
        else:
            self._fin()

    def _fin(self):
        self._callar_voz()
        self.app.cerrar(self)

    def cerrado(self):
        self._callar_voz()
        if self.al_terminar:
            f = self.al_terminar
            self.al_terminar = None
            f()

    def tecla(self, ev):
        k = ev.key
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_DOWN, pygame.K_RIGHT):
            self.i += 1
            if self.i >= len(self.lineas):
                self._fin()
            else:
                self._decir()
        elif k in (pygame.K_UP, pygame.K_r, pygame.K_PERIOD):
            self._decir()
        elif k == pygame.K_LEFT:
            self.i = max(0, self.i - 1)
            self._decir()
        elif k == pygame.K_ESCAPE:
            self.app.voz.callar()
            self._fin()
        elif k == pygame.K_PAGEUP:
            self.app.voz.repasar(-1)
        elif k == pygame.K_PAGEDOWN:
            self.app.voz.repasar(1)

    def actualizar(self, dt):
        pass


class EntradaTexto:
    """Pide un texto por teclado, diciendo en voz alta cada letra que se escribe.

    Intro acepta, Escape cancela, Retroceso borra, flecha arriba o F1 leen lo escrito y Control V pega.
    Con secreto=True (contraseñas) no se dicen las letras.
    """
    pausa_mundo = True
    cerrado_al_final = True

    def __init__(self, app, titulo, al_aceptar, inicial="", secreto=False, maximo=120, ayuda=None):
        self.app = app
        self.titulo = titulo
        self.al_aceptar = al_aceptar
        self.texto = inicial or ""
        self.secreto = secreto
        self.maximo = maximo
        self.ayuda = ayuda
        self.aceptado = False

    def _leer(self):
        if not self.texto:
            return "Vacío"
        return f"{len(self.texto)} caracteres escritos" if self.secreto else self.texto

    def al_entrar(self):
        with registro.privado():
            self._al_entrar()

    def _al_entrar(self):
        self.app.decir(f"{self.titulo}. Escribe y pulsa Intro. Escape cancela. {self._leer()}", True)

    def tecla(self, ev):
        with registro.privado():               # lo que se escribe y lo que se lee al escribir no se registra
            self._tecla(ev)

    def _tecla(self, ev):
        k = ev.key
        mod = getattr(ev, "mod", 0)
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.aceptado = True
            self.app.son("menu_ok")
            self.app.cerrar(self)
        elif k == pygame.K_ESCAPE:
            self.app.son("menu_atras")
            self.app.decir("Cancelado.", True)
            self.app.cerrar(self)
        elif k == pygame.K_BACKSPACE:
            if self.texto:
                quitada = self.texto[-1]
                self.texto = self.texto[:-1]
                self.app.son("menu_ajuste")
                self.app.decir("Borrado" if self.secreto else f"Borrado {self._nombre(quitada)}", True)
            else:
                self.app.son("menu_borde")
                self.app.decir("Vacío", True)
        elif k in (pygame.K_UP, pygame.K_F1):
            self.app.decir((self.ayuda + " " if self.ayuda and k == pygame.K_F1 else "") + self._leer(), True)
        elif k == pygame.K_v and mod & pygame.KMOD_CTRL:
            try:
                pegado = pygame.scrap.get_text() or ""
            except Exception:
                pegado = ""
            pegado = "".join(c for c in pegado if c.isprintable())
            if pegado:
                self.texto = (self.texto + pegado)[:self.maximo]
                self.app.decir("Pegado. " + self._leer(), True)
            else:
                self.app.son("error")
                self.app.decir("No hay texto en el portapapeles.", True)
        else:
            letra = getattr(ev, "unicode", "") or ""
            if letra and letra.isprintable() and not (mod & (pygame.KMOD_CTRL | pygame.KMOD_ALT) and not (mod & pygame.KMOD_MODE)):
                if len(self.texto) >= self.maximo:
                    self.app.son("menu_borde")
                    return
                self.texto += letra
                self.app.son("menu_mover")
                self.app.decir("asterisco" if self.secreto else self._nombre(letra), True)

    @staticmethod
    def _nombre(c):
        return {" ": "espacio", ".": "punto", ":": "dos puntos", "/": "barra", ",": "coma", "-": "guion", "_": "guion bajo", "@": "arroba",
                "?": "interrogación", "!": "exclamación"}.get(c, f"{c} mayúscula" if c.isupper() else c)

    def actualizar(self, dt):
        pass

    def cerrado(self):
        if self.aceptado and self.al_aceptar:
            f = self.al_aceptar
            self.al_aceptar = None
            f(self.texto)
