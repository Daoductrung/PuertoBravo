"""Menús y diálogos hablados. Todo se maneja con flechas, Intro y Escape."""
import pygame


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

    def __init__(self, app, lineas, al_terminar=None):
        self.app = app
        self.lineas = [tuple(l) for l in lineas]
        self.i = 0
        self.al_terminar = al_terminar
        self.primera = True

    def _decir(self):
        quien, texto = self.lineas[self.i]
        self.app.son("dialogo")
        extra = ""
        if self.primera:
            extra = " Pulsa Intro para continuar."
            self.primera = False
        self.app.decir((texto if quien == "Narrador" else f"{quien}: {texto}") + extra, True)

    def al_entrar(self):
        if self.i < len(self.lineas):
            self._decir()
        else:
            self._fin()

    def _fin(self):
        self.app.cerrar(self)

    def cerrado(self):
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
