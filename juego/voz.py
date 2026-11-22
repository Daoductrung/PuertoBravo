"""Salida de voz y braille mediante el lector de pantalla (NVDA, JAWS...) o SAPI."""
from .i18n import tr
import re
from collections import deque

from . import genero, palabras, registro


# Con poco detalle se quitan las frases que solo explican qué tecla pulsar: quien ya conoce el juego no las necesita.
_INSTRUCCION = re.compile(tr(r"^(Pulsa |Usa las flechas|Abre el móvil|Con la tecla|Intro para|Escape para|Flechas |F1 |Cámbialo|Elige |Para |Puedes |Recuerda)"), re.I)


def resumir(texto):
    """El mismo mensaje sin las frases de instrucciones. Si todo eran instrucciones, se deja como estaba."""
    partes = re.split(r"(?<=[.!?])\s+", texto)
    quedan = [f for f in partes if not _INSTRUCCION.match(f)]
    return " ".join(quedan) if quedan else texto


class Voz:
    def __init__(self, sapi=False, muda=False):
        self.historial = deque(maxlen=300)
        self.cursor = 0
        # Aparte, solo lo que dicen los demás jugadores y el servidor (chat, avisos, quién entra y sale): se repasa con
        # Mayúsculas Re Pág y Av Pág sin que se mezcle con las teclas y los menús.
        self.mensajes = deque(maxlen=100)
        self.cursor_msj = 0
        self.muda = muda
        self.salida = None
        self.registro = []          # usado por las pruebas
        self.al_hablar = None       # función(texto): el juego baja el ambiente mientras se habla
        self.detalle = "normal"     # mucho, normal o poco
        self.sapi = sapi
        self._ajustes = (0, 0, 100)
        if not muda:
            self._iniciar(sapi)

    def _iniciar(self, sapi):
        try:
            if sapi:
                from accessible_output2.outputs.sapi5 import SAPI5
                self.salida = SAPI5()
                self.sapi = True
                self.ajustar_sapi(*self._ajustes)
            else:
                from accessible_output2.outputs.auto import Auto
                self.salida = Auto()
                self.sapi = False
        except Exception:
            registro.excepcion("voz", "No se pudo abrir la salida de voz")
            self.salida = None

    def cambiar(self, sapi):
        self._iniciar(sapi)

    def ajustar_sapi(self, velocidad, tono, volumen):
        """Velocidad, tono y volumen de la voz de Windows. Con un lector de pantalla no hace nada: eso se ajusta en el lector."""
        self._ajustes = (velocidad, tono, volumen)
        s = self.salida
        if not self.sapi or s is None or self.muda:
            return
        for poner, valor, minimo, maximo in ((getattr(s, "set_rate", None), velocidad, -10, 10), (getattr(s, "set_pitch", None), tono, -10, 10),
                                             (getattr(s, "set_volume", None), volumen, 0, 100)):
            try:
                if poner is not None:
                    poner(max(minimo, min(maximo, int(valor))))
            except Exception:
                pass

    def decir(self, texto, interrumpir=False, guardar=True):
        """Dice un texto. Los avisos del juego no interrumpen; los menús sí."""
        if not texto:
            return
        texto = genero.resolver(str(texto))          # «Bienvenid[o|a]» queda como le corresponde al protagonista
        texto = palabras.pulir(texto)                # en otro idioma, ninguna palabra suelta en español
        if self.detalle == "poco":
            texto = resumir(texto)
        registro.voz(texto)
        if self.al_hablar is not None:
            self.al_hablar(texto)
        if guardar:
            self._guardar(texto)
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
        texto = genero.resolver(str(texto))
        texto = palabras.pulir(texto)
        registro.voz(texto)
        self._guardar(texto)
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

    def _guardar(self, texto):
        """Un mensaje al historial. Con la opción de seguir al final (la de siempre), el repaso salta a él; si no, y
        estabas repasando, te quedas en el mismo mensaje."""
        al_final = self.cursor >= len(self.historial) - 1
        lleno = len(self.historial) == self.historial.maxlen
        self.historial.append(texto)
        cfg = getattr(self, "cfg", None)
        if al_final or cfg is None or cfg["historial_al_final"]:
            self.cursor = len(self.historial) - 1
        elif lleno:
            self.cursor = max(0, self.cursor - 1)               # el más antiguo se ha ido: el tuyo está un puesto antes

    def apuntar_mensaje(self, texto):
        """Un mensaje de otro jugador o del servidor, a su historial aparte. Se dice como siempre; esto solo lo guarda."""
        if not texto:
            return
        texto = palabras.pulir(genero.resolver(str(texto)))
        al_final = self.cursor_msj >= len(self.mensajes) - 1
        self.mensajes.append(texto)
        if al_final:
            self.cursor_msj = len(self.mensajes) - 1

    def repasar_mensajes(self, delta):
        """Mayúsculas Re Pág, Av Pág y punto: el anterior, el siguiente o el último de los mensajes de los jugadores y del
        servidor. Lo que se dice al repasar no entra en ningún historial."""
        if not self.mensajes:
            self.decir(tr("Todavía no hay mensajes de otros jugadores ni del servidor."), True, False)
            return
        if delta == 0:
            self.cursor_msj = len(self.mensajes) - 1
            self.decir(tr("Último mensaje. ") + self.mensajes[self.cursor_msj], True, False)
            return
        nuevo = self.cursor_msj + delta
        if nuevo < 0 or nuevo >= len(self.mensajes):
            self.decir((tr("Primer mensaje. ") if nuevo < 0 else tr("Último mensaje. ")) + self.mensajes[self.cursor_msj], True, False)
            return
        self.cursor_msj = nuevo
        self.decir(self.mensajes[nuevo], True, False)

    def repasar_extremo(self, al_final):
        """Control Re Pág y Control Av Pág: el primer mensaje del historial, o el último."""
        if not self.historial:
            self.decir(tr("No hay mensajes."), True, False)
            return
        self.cursor = len(self.historial) - 1 if al_final else 0
        self.decir((tr("Último. ") if al_final else tr("Primero. ")) + self.historial[self.cursor], True, False)

    def repasar(self, delta):
        """Recorre el historial de mensajes (delta -1 anterior, +1 siguiente, 0 repetir)."""
        if not self.historial:
            self.decir(tr("No hay mensajes."), True, False)
            return
        self.cursor = max(0, min(len(self.historial) - 1, self.cursor + delta))
        self.decir(self.historial[self.cursor], True, False)

    def ultimo(self):
        return self.historial[-1] if self.historial else ""
