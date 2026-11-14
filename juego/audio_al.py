"""Motor de sonido envolvente: el mismo mezclador del juego, pero reproduciendo con OpenAL Soft en binaural.

Con auriculares, el binaural permite distinguir de verdad si algo suena delante o detrás, y no solo a izquierda o
derecha. La biblioteca (soft_oal.dll, libre, LGPL) hace la mezcla en código nativo, fuera de Python, así que
tampoco sufre los tirones del motor clásico cuando hay mucho sonido a la vez.

Hereda del mezclador clásico toda la lógica (qué suena, con qué volumen, categorías, atenuación al hablar) y solo
cambia quién pone el sonido en los auriculares: en lugar de mezclar muestras en Python, mantiene una «fuente» de
OpenAL por cada sonido en marcha y la actualiza una vez por fotograma. Si la biblioteca no está o no arranca,
`crear()` devuelve el motor clásico: el juego nunca se queda sin sonido por esto.
"""
import ctypes
import math
import os
import sys

import numpy as np

from . import registro, rutas
from .audio import SR, Mezclador

AL_POSITION, AL_GAIN, AL_PITCH, AL_LOOPING, AL_BUFFER, AL_SOURCE_STATE = 0x1004, 0x100A, 0x1003, 0x1007, 0x1009, 0x1010
AL_PLAYING, AL_PAUSED, AL_ORIENTATION, AL_SOURCE_RELATIVE = 0x1012, 0x1013, 0x100F, 0x202
AL_ROLLOFF_FACTOR, AL_FORMAT_MONO16, AL_FORMAT_STEREO16, AL_NONE = 0x1021, 0x1101, 0x1103, 0
ALC_HRTF_SOFT, ALC_HRTF_STATUS_SOFT, ALC_FREQUENCY = 0x1992, 0x1993, 0x1007
_CATS_MUNDO = ("efectos", "ambiente")


def ruta_dll():
    """Dónde está la biblioteca: junto al ejecutable en el juego compilado, o en terceros en el código fuente."""
    base = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else rutas.base()
    for r in (os.path.join(base, "lib", "soft_oal.dll"), os.path.join(base, "soft_oal.dll"), os.path.join(rutas.base(), "terceros", "openal_soft", "soft_oal.dll")):
        if os.path.exists(r):
            return r
    return ""


def disponible():
    return bool(ruta_dll()) and os.name == "nt"


def _cargar(ruta):
    al = ctypes.CDLL(ruta)
    vp, ci, cu, cf = ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_float
    firmas = {
        "alcOpenDevice": (vp, [ctypes.c_char_p]), "alcCloseDevice": (ctypes.c_char, [vp]), "alcCreateContext": (vp, [vp, ctypes.POINTER(ci)]),
        "alcMakeContextCurrent": (ctypes.c_char, [vp]), "alcDestroyContext": (None, [vp]), "alcGetIntegerv": (None, [vp, ci, ci, ctypes.POINTER(ci)]),
        "alcGetError": (ci, [vp]), "alGetError": (ci, []), "alDistanceModel": (None, [ci]),
        "alGenSources": (None, [ci, ctypes.POINTER(cu)]), "alDeleteSources": (None, [ci, ctypes.POINTER(cu)]),
        "alGenBuffers": (None, [ci, ctypes.POINTER(cu)]), "alDeleteBuffers": (None, [ci, ctypes.POINTER(cu)]),
        "alBufferData": (None, [cu, ci, vp, ci, ci]), "alSourcei": (None, [cu, ci, ci]), "alSourcef": (None, [cu, ci, cf]),
        "alSource3f": (None, [cu, ci, cf, cf, cf]), "alGetSourcei": (None, [cu, ci, ctypes.POINTER(ci)]),
        "alSourcePlay": (None, [cu]), "alSourceStop": (None, [cu]), "alSourcePause": (None, [cu]),
        "alListener3f": (None, [ci, cf, cf, cf]), "alListenerfv": (None, [ci, ctypes.POINTER(cf)]), "alListenerf": (None, [ci, cf]),
    }
    for nombre, (res, args) in firmas.items():
        f = getattr(al, nombre)
        f.restype, f.argtypes = res, args
    return al


class MezcladorAL(Mezclador):
    """El mezclador del juego con salida binaural por OpenAL Soft."""
    envolvente = True

    def __init__(self):
        super().__init__(dispositivo=False)              # sin el flujo de sonido de Python: de la salida se ocupa OpenAL
        self.al = _cargar(ruta_dll())
        self.dev = self.al.alcOpenDevice(None)
        if not self.dev:
            raise OSError("OpenAL no ha podido abrir el dispositivo de sonido")
        atributos = (ctypes.c_int * 3)(ALC_HRTF_SOFT, 1, 0)
        self.ctx = self.al.alcCreateContext(self.dev, atributos)
        if not self.ctx or not self.al.alcMakeContextCurrent(self.ctx):
            self.al.alcCloseDevice(self.dev)
            raise OSError("OpenAL no ha podido crear el contexto de sonido")
        v = ctypes.c_int(0)
        self.al.alcGetIntegerv(self.dev, ALC_HRTF_STATUS_SOFT, 1, ctypes.byref(v))
        self.binaural = v.value == 1
        self.al.alcGetIntegerv(self.dev, ALC_FREQUENCY, 1, ctypes.byref(v))
        self.frecuencia = v.value
        self.al.alDistanceModel(AL_NONE)                 # la distancia la calcula el juego, igual que en el motor clásico
        self._buffers = {}                               # nombre -> (id de buffer, id del array con el que se hizo)
        self._pausados = False
        registro.info("sonido", "Motor de sonido envolvente", binaural="sí" if self.binaural else "no", frecuencia=self.frecuencia)

    # ------------------------------------------------------------------ buffers y fuentes
    def _buffer(self, nombre):
        datos = self.sonidos.get(nombre)
        if datos is None:
            return 0
        hecho = self._buffers.get(nombre)
        if hecho and hecho[1] == id(datos):
            return hecho[0]
        b = ctypes.c_uint(0)
        self.al.alGenBuffers(1, ctypes.byref(b))
        pcm = np.ascontiguousarray(np.clip(datos, -1.0, 1.0) * 32767.0, dtype=np.int16)
        formato = AL_FORMAT_STEREO16 if datos.ndim == 2 else AL_FORMAT_MONO16
        self.al.alBufferData(b.value, formato, pcm.ctypes.data_as(ctypes.c_void_p), pcm.nbytes, SR)
        if hecho:                                        # el sonido ha cambiado (otro pack, otra pista de radio): el viejo sobra
            viejo = ctypes.c_uint(hecho[0])
            self.al.alDeleteBuffers(1, ctypes.byref(viejo))
            self.al.alGetError()                         # si aún lo usa alguna fuente no se borra; no pasa nada
        self._buffers[nombre] = (b.value, id(datos))
        return b.value

    def _crear_fuente(self, c):
        b = self._buffer(c.nombre)
        if not b:
            c.fin = True
            return
        s = ctypes.c_uint(0)
        self.al.alGenSources(1, ctypes.byref(s))
        if self.al.alGetError() or not s.value:          # sin fuentes libres: ese sonido no suena
            c.fin = True
            return
        c._src = s.value
        c._g = 0.0 if c.bucle else None                  # los bucles entran con fundido
        self.al.alSourcei(c._src, AL_BUFFER, b)
        self.al.alSourcei(c._src, AL_LOOPING, 1 if c.bucle else 0)
        self.al.alSourcef(c._src, AL_ROLLOFF_FACTOR, 0.0)
        self._poner(c)
        self.al.alSourcePlay(c._src)

    def _soltar(self, c):
        s = getattr(c, "_src", 0)
        if s:
            self.al.alSourceStop(s)
            u = ctypes.c_uint(s)
            self.al.alDeleteSources(1, ctypes.byref(u))
            c._src = 0
        c.fin = True

    def _poner(self, c):
        """Lleva a la fuente de OpenAL el volumen, el tono y la posición que el juego quiere para este sonido."""
        g = c.vol * self.vols.get(c.cat, 1.0)
        if c.cat in ("ambiente", "musica"):
            g *= self.duck
        ox, oy, _ = self.oyente
        if c.xy is None:
            self.al.alSourcei(c._src, AL_SOURCE_RELATIVE, 1)
            self.al.alSource3f(c._src, AL_POSITION, float(max(-1.0, min(1.0, c.pan))), 0.0, -0.4 if c.pan else 0.0)
        else:
            dx, dy = c.xy[0] - ox, c.xy[1] - oy
            d = math.hypot(dx, dy)
            if d >= c.maxd:
                g = 0.0
            else:
                if d > c.ref:
                    g *= c.ref / (c.ref + 1.2 * (d - c.ref))
                borde = c.maxd * 0.25
                if d > c.maxd - borde:
                    g *= (c.maxd - d) / borde
            self.al.alSourcei(c._src, AL_SOURCE_RELATIVE, 0)
            # el volumen por distancia ya está aplicado: a OpenAL solo le interesa la dirección, así que se le da a un metro
            k = 1.0 / d if d > 1.0 else 1.0
            self.al.alSource3f(c._src, AL_POSITION, float(ox + dx * k), 0.0, float(-(oy + dy * k)))
        if c.parando:
            g = 0.0
        if c._g is None:
            c._g = g
        else:
            c._g += (g - c._g) * (0.5 if g < c._g else 0.3)
        self.al.alSourcef(c._src, AL_GAIN, float(max(0.0, min(4.0, c._g))))
        c.rate += (c.rate_obj - c.rate) * 0.4
        tono = c.rate * self.tono_mundo if c.cat in _CATS_MUNDO else c.rate
        self.al.alSourcef(c._src, AL_PITCH, float(max(0.05, min(8.0, tono))))

    # ------------------------------------------------------------------ interfaz del mezclador
    def sonar(self, nombre, **kw):
        c = super().sonar(nombre, **kw)
        c._src = 0
        c._g = None
        return c

    def actualizar(self):
        with self._lock:
            lista = list(self.canales)
        import time
        objetivo = 0.45 if self.atenuar and time.time() < self.duck_hasta else 1.0
        self.duck += (objetivo - self.duck) * (0.35 if objetivo < self.duck else 0.08)
        ox, oy, rumbo = self.oyente
        r = math.radians(rumbo)
        self.al.alListener3f(AL_POSITION, float(ox), 0.0, float(-oy))
        self.al.alListenerfv(AL_ORIENTATION, (ctypes.c_float * 6)(math.sin(r), 0.0, -math.cos(r), 0.0, 1.0, 0.0))
        self.al.alListenerf(AL_GAIN, float(self.vols["maestro"]))
        estado = ctypes.c_int(0)
        pausar = bool(self.mundo_pausado)
        for c in lista:
            if c.fin:
                if getattr(c, "_src", 0):
                    self._soltar(c)
                continue
            if not getattr(c, "_src", 0):
                self._crear_fuente(c)
                if c.fin:
                    continue
            self._poner(c)
            if c.parando and c._g < 0.01:
                self._soltar(c)
                continue
            if c.cat in _CATS_MUNDO and pausar != self._pausados:
                (self.al.alSourcePause if pausar else self.al.alSourcePlay)(c._src)
            elif not c.bucle and not (pausar and c.cat in _CATS_MUNDO):
                self.al.alGetSourcei(c._src, AL_SOURCE_STATE, ctypes.byref(estado))
                if estado.value not in (AL_PLAYING, AL_PAUSED):
                    self._soltar(c)
        self._pausados = pausar
        with self._lock:
            self.canales = [c for c in self.canales if not c.fin]

    def render(self, n):
        return np.zeros((n, 2), np.float32)              # la mezcla la hace OpenAL; esto solo existe por compatibilidad

    def cerrar(self):
        try:
            with self._lock:
                lista, self.canales = list(self.canales), []
            for c in lista:
                self._soltar(c)
            for b, _ in self._buffers.values():
                u = ctypes.c_uint(b)
                self.al.alDeleteBuffers(1, ctypes.byref(u))
            self._buffers.clear()
            self.al.alcMakeContextCurrent(None)
            self.al.alcDestroyContext(self.ctx)
            self.al.alcCloseDevice(self.dev)
        except Exception:
            pass


def crear(cfg, pruebas=False):
    """El mezclador que toca: el envolvente si el jugador lo ha elegido y este equipo puede; si no, el clásico."""
    if pruebas:
        return Mezclador(dispositivo=False)
    forzado = os.environ.get("PUERTOBRAVO_MOTOR", "")              # para pruebas: «envolvente» o «clasico»
    if (cfg["motor_sonido"] == "envolvente" or forzado == "envolvente") and forzado != "clasico" and not cfg["sonido_mono"]:
        from . import procesador
        if not disponible():
            registro.aviso("sonido", "No está la biblioteca del motor envolvente; se usa el clásico")
        elif not procesador.moderno():
            registro.aviso("sonido", "Procesador antiguo: se usa el motor de sonido clásico")
        else:
            try:
                return MezcladorAL()
            except Exception as e:
                registro.aviso("sonido", "El motor envolvente no ha arrancado; se usa el clásico", error=type(e).__name__)
    return Mezclador(dispositivo=True)
