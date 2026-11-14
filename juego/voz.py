"""Salida de voz y braille mediante el lector de pantalla (NVDA, JAWS...) o SAPI."""
from collections import deque

from . import registro


class Voz:
    def __init__(self, sapi=False, muda=False):
        self.historial = deque(maxlen=300)
        self.cursor = 0
        self.muda = muda
        self.salida = None
        self.registro = []          # usado por las pruebas
        if not muda:
            self._iniciar(sapi)

    def _iniciar(self, sapi):
        try:
            if sapi:
                from accessible_output2.outputs.sapi5 import SAPI5
                self.salida = SAPI5()
            else:
                from accessible_output2.outputs.auto import Auto
                self.salida = Auto()
        except Exception:
            registro.excepcion("voz", "No se pudo abrir la salida de voz")
            self.salida = None

    def cambiar(self, sapi):
        self._iniciar(sapi)

    def decir(self, texto, interrumpir=False, guardar=True):
        """Dice un texto. Los avisos del juego no interrumpen; los menús sí."""
        if not texto:
            return
        texto = str(texto)
        registro.voz(texto)
        if guardar:
            self.historial.append(texto)
            self.cursor = len(self.historial) - 1
        if self.muda:
            self.registro.append(texto)
            if len(self.registro) > 2000:
                del self.registro[:1000]
            return
        if self.salida is None:
            return
        try:
            self.salida.speak(texto, interrupt=interrumpir)
            try:
                self.salida.braille(texto)
            except Exception:
                pass
        except Exception:
            pass

    def mostrar(self, texto):
        """Para cuando suena una voz grabada: el texto no se lee, pero va al braille, al historial y al registro."""
        texto = str(texto)
        registro.voz(texto)
        self.historial.append(texto)
        self.cursor = len(self.historial) - 1
        if self.muda:
            self.registro.append(texto)
            return
        self.callar()
        if self.salida is not None:
            try:
                self.salida.braille(texto)
            except Exception:
                pass

    def callar(self):
        if self.salida is not None and not self.muda:
            try:
                self.salida.speak("", interrupt=True)
            except Exception:
                pass

    def repasar(self, delta):
        """Recorre el historial de mensajes (delta -1 anterior, +1 siguiente, 0 repetir)."""
        if not self.historial:
            self.decir("No hay mensajes.", True, False)
            return
        self.cursor = max(0, min(len(self.historial) - 1, self.cursor + delta))
        self.decir(self.historial[self.cursor], True, False)

    def ultimo(self):
        return self.historial[-1] if self.historial else ""
