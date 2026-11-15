"""Mezclador de audio 3D propio.

Cada sonido se coloca alrededor del oyente con panorama de potencia constante,
diferencia de tiempo entre oídos, atenuación por distancia y un filtro que
apaga los sonidos que quedan detrás o lejos. Todo se mezcla con numpy y sale
por sounddevice, de modo que también se puede variar el tono (motores, sirenas).
"""
import math
import threading
import time

import numpy as np
from . import registro

SR = 44100
ITD_MAX = 28.0      # muestras de retardo máximo entre oídos
PAD = 32


def apagar(x, corte=900.0):
    """Versión apagada de un sonido (pasa bajos por FFT)."""
    n = len(x)
    if n < 8:
        return x.copy()
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = 1.0 / (1.0 + (f / corte) ** 2)
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n, axis=0).astype(np.float32)


class Canal:
    """Un sonido en reproducción."""

    def __init__(self):
        self.nombre = ""
        self.datos = None
        self.apag = None
        self.largo = 0
        self.pos = 0.0
        self.rate = 1.0
        self.rate_obj = 1.0
        self.bucle = False
        self.vol = 1.0
        self.cat = "efectos"
        self.xy = None          # posición en el mundo o None si es 2D
        self.pan = 0.0
        self.ref = 5.0
        self.maxd = 70.0
        self.gl = self.gr = 0.0
        self.gl_obj = self.gr_obj = 0.0
        self.dl = self.dr = 0.0
        self.dl_obj = self.dr_obj = 0.0
        self.muf = self.muf_obj = 0.0
        self.parando = False
        self.fin = False
        self.estereo = False
        self.nuevo = True
        self.alto = 0.0         # altura sobre el suelo, en metros (solo la usa el motor envolvente)
        self.eco = False        # que le afecte el eco del lugar aunque no sea un efecto del mundo

    def mover(self, x, y):
        self.xy = (x, y)

    def tono(self, r):
        self.rate_obj = max(0.05, float(r))

    def volumen(self, v):
        self.vol = max(0.0, float(v))

    def parar(self):
        self.parando = True

    @property
    def activo(self):
        return not self.fin and not self.parando


class Mezclador:
    def __init__(self, dispositivo=True, bloque=1024):
        self.sonidos = {}
        self._var = {}
        self.canales = []
        self._lock = threading.Lock()
        self._ar = np.arange(8192 + PAD, dtype=np.float64)
        self.oyente = (0.0, 0.0, 0.0)
        self.vols = {"maestro": 0.8, "efectos": 1.0, "ambiente": 0.6, "musica": 0.5, "interfaz": 0.8}
        self.mundo_pausado = False
        self.entorno = "calle"      # dónde está el oyente: decide el eco en el motor envolvente
        self.altura = 0.0           # altura del oyente sobre el suelo: en helicóptero, lo demás suena por debajo
        self.mono = False           # los dos oídos oyen lo mismo: para quien oye por uno solo
        self.atenuar = True         # bajar el ambiente y la música mientras habla la voz
        self.duck = 1.0             # cuánto están bajados ahora mismo (1 = nada)
        self.duck_hasta = 0.0
        self.tono_mundo = 1.0       # multiplica el tono de todos los sonidos del mundo (efectos de sustancias)
        self.stream = None
        self.error = None
        if dispositivo:
            self._abrir(bloque)

    def _abrir(self, bloque):
        """Abre la salida de audio: primero WASAPI (unos 20 ms de latencia) y, si falla, la de por defecto."""
        try:
            import sounddevice as sd
        except Exception as e:
            self.error = str(e)
            return
        intentos = []
        try:
            for h in sd.query_hostapis():
                if "WASAPI" in h["name"] and h["default_output_device"] >= 0:
                    intentos.append((h["default_output_device"], sd.WasapiSettings(auto_convert=True), 512))
        except Exception:
            pass
        intentos.append((None, None, bloque))
        for dispositivo, extra, tam in intentos:
            try:
                self.stream = sd.OutputStream(samplerate=SR, channels=2, dtype="float32", blocksize=tam,
                                              callback=self._cb, latency="low", device=dispositivo, extra_settings=extra)
                self.stream.start()
                self.error = None
                return
            except Exception as e:  # sin tarjeta de sonido: el juego sigue, mudo
                self.error = str(e)
                self.stream = None
                registro.aviso("sonido", "No se pudo abrir la salida de sonido con esta configuración", error=e, bloque=tam, exclusivo=bool(extra))

    # ---------------------------------------------------------------- sonidos
    def registrar(self, nombre, datos):
        self.sonidos[nombre] = np.ascontiguousarray(datos, dtype=np.float32)
        for k in [k for k in list(self._var) if k[0] == nombre]:
            self._var.pop(k, None)

    def _variante(self, nombre, bucle, apagado):
        clave = (nombre, bucle, apagado)
        v = self._var.get(clave)
        if v is None:
            d = self.sonidos[nombre]
            if apagado:
                d = apagar(d)
            if bucle:
                v = np.concatenate([d, d[:2]])
            else:
                v = np.concatenate([d, np.zeros((2,) + d.shape[1:], np.float32)])
            self._var[clave] = v
        return v

    def duracion(self, nombre):
        d = self.sonidos.get(nombre)
        return 0.0 if d is None else len(d) / SR

    # ------------------------------------------------------------ reproducir
    def sonar(self, nombre, vol=1.0, tono=1.0, bucle=False, xy=None, pan=0.0,
              ref=5.0, maxd=70.0, cat="efectos"):
        c = Canal()
        d = self.sonidos.get(nombre)
        if d is None:
            registro.sonido_falta(nombre)
            c.fin = True
            return c
        registro.sonido(nombre)
        with self._lock:
            if len(self.canales) >= 56 and not bucle and cat != "interfaz":
                c.fin = True
                return c
        c.nombre = nombre
        c.estereo = d.ndim == 2
        c.largo = len(d)
        c.datos = self._variante(nombre, bucle, False)
        if xy is not None and not c.estereo:
            c.apag = self._variante(nombre, bucle, True)
        c.rate = c.rate_obj = max(0.05, float(tono))
        c.bucle = bucle
        c.vol = vol
        c.cat = cat
        c.xy = xy
        c.pan = pan
        c.ref = ref
        c.maxd = maxd
        self._calcular(c)
        c.gl, c.gr, c.dl, c.dr, c.muf = c.gl_obj, c.gr_obj, c.dl_obj, c.dr_obj, c.muf_obj
        if bucle:
            c.gl = c.gr = 0.0      # los bucles entran con fundido
        with self._lock:
            self.canales.append(c)
        return c

    def situar_oyente(self, x, y, rumbo):
        self.oyente = (x, y, rumbo)

    def hablando(self, texto):
        """La voz va a decir algo: durante lo que tarde, el ambiente y la música bajan para que se entienda."""
        self.duck_hasta = max(self.duck_hasta, time.time() + min(9.0, 0.7 + len(str(texto)) / 15.0))

    def _calcular(self, c):
        g = c.vol * self.vols.get(c.cat, 1.0)
        if c.cat in ("ambiente", "musica"):
            g *= self.duck
        if c.xy is None:
            p = max(-1.0, min(1.0, c.pan))
            a = (p + 1.0) * math.pi / 4.0
            if c.estereo:
                c.gl_obj = g * min(1.0, 1.0 - p)
                c.gr_obj = g * min(1.0, 1.0 + p)
            else:
                c.gl_obj = g * math.cos(a) * 1.3
                c.gr_obj = g * math.sin(a) * 1.3
            c.dl_obj = c.dr_obj = 0.0
            c.muf_obj = 0.0
            return
        ox, oy, rumbo = self.oyente
        dx = c.xy[0] - ox
        dy = c.xy[1] - oy
        d = math.hypot(dx, dy)
        if d >= c.maxd:
            c.gl_obj = c.gr_obj = 0.0
            return
        if d > c.ref:
            g *= c.ref / (c.ref + 1.2 * (d - c.ref))
        borde = c.maxd * 0.25
        if d > c.maxd - borde:
            g *= (c.maxd - d) / borde
        if d < 0.5:
            p = 0.0
            detras = 0.0
        else:
            rel = math.radians(math.degrees(math.atan2(dx, dy)) - rumbo)
            p = math.sin(rel)
            detras = max(0.0, -math.cos(rel))
            cerca = min(1.0, d / 2.0)
            p *= cerca
            detras *= cerca
        a = (p + 1.0) * math.pi / 4.0
        g *= 1.0 - 0.3 * detras
        c.gl_obj = g * math.cos(a) * 1.3
        c.gr_obj = g * math.sin(a) * 1.3
        c.dl_obj = ITD_MAX * p if p > 0 else 0.0
        c.dr_obj = -ITD_MAX * p if p < 0 else 0.0
        c.muf_obj = min(0.95, 0.7 * detras + 0.45 * min(1.0, d / c.maxd))

    def actualizar(self):
        """Recalcula la posición relativa de todos los sonidos. Una vez por fotograma."""
        with self._lock:
            self.canales = [c for c in self.canales if not c.fin]
            lista = list(self.canales)
        objetivo = 0.45 if self.atenuar and time.time() < self.duck_hasta else 1.0
        self.duck += (objetivo - self.duck) * (0.35 if objetivo < self.duck else 0.08)      # baja rápido y vuelve despacio
        for c in lista:
            self._calcular(c)

    def parar_todo(self, cats=("efectos", "ambiente")):
        with self._lock:
            for c in self.canales:
                if c.cat in cats:
                    c.parando = True

    # ----------------------------------------------------------------- mezcla
    def _leer(self, d, idx, L, bucle):
        if bucle:
            idx = np.mod(idx, L)
        else:
            idx = np.clip(idx, 0.0, float(L))
        i0 = idx.astype(np.int64)
        fr = (idx - i0).astype(np.float32)
        if d.ndim == 2:
            fr = fr[:, None]
        a = d[i0]
        return a + (d[i0 + 1] - a) * fr

    def render(self, n):
        mix = np.zeros((n, 2), np.float32)
        with self._lock:
            lista = list(self.canales)
        rampa = self._ar[:n].astype(np.float32) / max(1, n)
        for c in lista:
            if c.fin:
                continue
            if self.mundo_pausado and c.cat in ("efectos", "ambiente"):
                continue
            c.rate += (c.rate_obj - c.rate) * 0.4
            r = c.rate * self.tono_mundo if c.cat in ("efectos", "ambiente") else c.rate
            L = c.largo
            gl1, gr1 = (0.0, 0.0) if c.parando else (c.gl_obj, c.gr_obj)
            if c.gl < 1e-4 and c.gr < 1e-4 and gl1 < 1e-4 and gr1 < 1e-4 and not c.parando:
                # No se oye (está lejos o con el volumen a cero): avanza sin gastar cálculo. Con muchas sirenas y motores, esto es lo que evita los tirones.
                c.pos += n * r
                if c.bucle:
                    c.pos %= L
                elif c.pos >= L:
                    c.fin = True
                c.dl, c.dr, c.muf = c.dl_obj, c.dr_obj, c.muf_obj
                continue
            if c.estereo or c.xy is None:
                idx = c.pos + self._ar[:n] * r
                s = self._leer(c.datos, idx, L, c.bucle)
                if c.estereo:
                    mix[:, 0] += s[:, 0] * (c.gl + (gl1 - c.gl) * rampa)
                    mix[:, 1] += s[:, 1] * (c.gr + (gr1 - c.gr) * rampa)
                else:
                    mix[:, 0] += s * (c.gl + (gl1 - c.gl) * rampa)
                    mix[:, 1] += s * (c.gr + (gr1 - c.gr) * rampa)
            else:
                idx = c.pos + (self._ar[:n + PAD] - PAD) * r
                s = self._leer(c.datos, idx, L, c.bucle)
                if c.muf > 0.02 or c.muf_obj > 0.02:
                    sm = self._leer(c.apag, idx, L, c.bucle)
                    m = np.empty(n + PAD, np.float32)
                    m[:PAD] = c.muf
                    m[PAD:] = c.muf + (c.muf_obj - c.muf) * rampa
                    s = s + (sm - s) * m
                base = s[PAD:]
                if c.dl > 0.01 or c.dl_obj > 0.01:
                    q = PAD + self._ar[:n] - (c.dl + (c.dl_obj - c.dl) * rampa)
                    izq = np.interp(q, self._ar[:n + PAD], s)
                else:
                    izq = base
                if c.dr > 0.01 or c.dr_obj > 0.01:
                    q = PAD + self._ar[:n] - (c.dr + (c.dr_obj - c.dr) * rampa)
                    der = np.interp(q, self._ar[:n + PAD], s)
                else:
                    der = base
                mix[:, 0] += izq * (c.gl + (gl1 - c.gl) * rampa)
                mix[:, 1] += der * (c.gr + (gr1 - c.gr) * rampa)
                c.dl, c.dr, c.muf = c.dl_obj, c.dr_obj, c.muf_obj
            c.gl, c.gr = gl1, gr1
            c.pos += n * r
            if c.bucle:
                c.pos %= L
            elif c.pos >= L:
                c.fin = True
            if c.parando and gl1 == 0.0:
                c.fin = True
        mix *= self.vols["maestro"]
        if self.mono:
            m = mix.mean(axis=1)
            mix[:, 0] = m
            mix[:, 1] = m
        np.tanh(mix, out=mix)
        return mix

    def _cb(self, salida, frames, tiempo, estado):
        try:
            salida[:] = self.render(frames)
        except Exception:
            salida.fill(0)

    def cerrar(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
