"""Emisoras de radio: música generada por un pequeño secuenciador.

Cada emisora es un bucle estéreo compuesto al vuelo a partir de una semilla.
Además, cualquier archivo de audio que el jugador deje en la carpeta
radio_usuario se convierte en la emisora «Mi música».
"""
import math
import os
import random
import threading

import numpy as np

SR = 44100
PI2 = 2 * np.pi
VERSION = 2

EMISORAS = [
    {"id": "apagada", "nombre": "Radio apagada"},
    {"id": "bravo", "nombre": "Bravo FM, rock de carretera", "estilo": "rock", "bpm": 124, "semilla": 11, "tono": 40},
    {"id": "latina", "nombre": "Onda Caribe, ritmos latinos", "estilo": "latino", "bpm": 94, "semilla": 23, "tono": 45},
    {"id": "neon", "nombre": "Neón 84, sintetizadores", "estilo": "synth", "bpm": 108, "semilla": 37, "tono": 42},
    {"id": "calma", "nombre": "Radio Bahía, música tranquila", "estilo": "calma", "bpm": 78, "semilla": 51, "tono": 48},
    {"id": "usuario", "nombre": "Mi música"},
    {"id": "hierro", "nombre": "Radio Hierro, rock duro de Monteferro", "estilo": "rock", "bpm": 142, "semilla": 77, "tono": 38},
    {"id": "club", "nombre": "Lucero Club, electrónica", "estilo": "synth", "bpm": 126, "semilla": 91, "tono": 45},
    {"id": "tropical", "nombre": "Costa Tropical, verbena", "estilo": "latino", "bpm": 108, "semilla": 63, "tono": 43},
    {"id": "noticias", "nombre": "El Faro Noticias, la actualidad de la comarca"},
]


def _hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _t(d):
    return np.arange(int(SR * d)) / SR


def _lp(x, hi, orden=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    return np.fft.irfft(X / (1.0 + (f / hi) ** orden), len(x))


def _env(d, a, tau):
    t = _t(d)
    return np.minimum(1.0, t / a) * np.exp(-t / tau)


def _bombo(d=0.3):
    t = _t(d)
    f = 45 + 110 * np.exp(-t / 0.03)
    return np.sin(PI2 * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def _caja(rng, d=0.25, tau=0.07):
    n = rng.standard_normal(int(SR * d))
    X = np.fft.rfft(n)
    f = np.fft.rfftfreq(len(n), 1.0 / SR)
    r = (f / 900) ** 2
    n = np.fft.irfft(X * r / (1 + r), len(n))
    return (n * 0.5 + 0.5 * np.sin(PI2 * 190 * _t(d))) * _env(d, 0.001, tau)


def _plato(rng, d=0.06, tau=0.015):
    n = rng.standard_normal(int(SR * d))
    X = np.fft.rfft(n)
    f = np.fft.rfftfreq(len(n), 1.0 / SR)
    r = (f / 6000) ** 4
    return np.fft.irfft(X * r / (1 + r), len(n)) * _env(d, 0.001, tau)


def _sierra(f, d, desaf=0.0):
    t = _t(d)
    x = 2 * ((f * t) % 1.0) - 1
    if desaf:
        x = x + 2 * ((f * (1 + desaf) * t) % 1.0) - 1 + 2 * ((f * (1 - desaf) * t) % 1.0) - 1
    return x


def _piano(f, d):
    t = _t(d)
    x = np.sin(PI2 * f * t) + 0.4 * np.sin(PI2 * 2 * f * t) * np.exp(-t / 0.3) + 0.15 * np.sin(PI2 * 3 * f * t) * np.exp(-t / 0.15)
    return x * _env(d, 0.004, d * 0.45)


def _poner(dest, x, i, g=1.0):
    if i >= len(dest):
        return
    n = min(len(x), len(dest) - i)
    dest[i:i + n] += x[:n] * g


def componer(estilo, bpm, semilla, tono):
    """Devuelve un bucle estéreo (N, 2) float32 de 8 compases."""
    rng = np.random.default_rng(semilla)
    paso = 60.0 / bpm / 4.0                  # semicorchea
    n_paso = int(round(paso * SR))
    compases = 8
    total = n_paso * 16 * compases
    bat = np.zeros(total)
    bajo = np.zeros(total)
    arm = np.zeros(total)
    mel = np.zeros(total)
    progresiones = {
        "rock": [(0, "m"), (8, "M"), (3, "M"), (10, "M")],
        "latino": [(0, "m"), (5, "m"), (10, "M"), (3, "M")],
        "synth": [(0, "m"), (8, "M"), (5, "m"), (7, "m")],
        "calma": [(0, "M7"), (9, "m7"), (5, "M7"), (7, "7")],
    }
    acordes = {"m": (0, 3, 7), "M": (0, 4, 7), "M7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "7": (0, 4, 7, 10)}
    prog = progresiones[estilo]
    escala = (0, 2, 4, 7, 9) if estilo == "calma" else (0, 3, 5, 7, 10)
    bombo, caja, plato = _bombo(), _caja(rng), _plato(rng)
    plato_ab = _plato(rng, 0.25, 0.08)
    nota_ant = 2
    for c in range(compases):
        raiz, tipo = prog[c % len(prog)]
        base = tono + raiz
        inicio = c * 16 * n_paso
        relleno = (c % 4 == 3)
        for s in range(16):
            i = inicio + s * n_paso
            # ------------------------------------------------------ batería
            if estilo == "rock":
                if s in (0, 8) or (s == 10 and c % 2):
                    _poner(bat, bombo, i, 1.0)
                if s in (4, 12):
                    _poner(bat, caja, i, 0.8)
                if s % 2 == 0:
                    _poner(bat, plato, i, 0.35)
                if relleno and s >= 12:
                    _poner(bat, caja, i, 0.5 + 0.1 * (s - 12))
            elif estilo == "latino":
                if s % 4 == 0:
                    _poner(bat, bombo, i, 1.0)
                if s in (3, 6, 11, 14):
                    _poner(bat, caja, i, 0.6)
                if s % 2 == 1:
                    _poner(bat, plato, i, 0.3)
            elif estilo == "synth":
                if s % 4 == 0:
                    _poner(bat, bombo, i, 1.0)
                if s in (4, 12):
                    _poner(bat, _caja(rng, 0.4, 0.14), i, 0.7)
                if s % 4 == 2:
                    _poner(bat, plato_ab, i, 0.25)
            else:
                if s in (0, 10):
                    _poner(bat, bombo, i, 0.7)
                if s in (4, 12):
                    _poner(bat, plato_ab, i, 0.2)
                if s % 4 == 2:
                    _poner(bat, plato, i, 0.2)
            # --------------------------------------------------------- bajo
            f = _hz(base - 12)
            if estilo == "rock" and s % 2 == 0:
                _poner(bajo, _lp(_sierra(f, paso * 1.8), 500) * _env(paso * 1.8, 0.005, 0.2), i, 0.7)
            elif estilo == "latino" and s in (0, 3, 6, 8, 11, 14):
                ff = f * (1.5 if s in (6, 14) else 1)
                _poner(bajo, np.sin(PI2 * ff * _t(paso * 2.5)) * _env(paso * 2.5, 0.005, 0.18), i, 0.9)
            elif estilo == "synth":
                ff = f * (2 if s % 4 == 2 else 1)
                _poner(bajo, _lp(_sierra(ff, paso * 0.9), 700) * _env(paso * 0.9, 0.003, 0.09), i, 0.6)
            elif estilo == "calma" and s in (0, 6, 8):
                _poner(bajo, np.sin(PI2 * f * _t(paso * 5)) * _env(paso * 5, 0.01, 0.4), i, 0.8)
            # ------------------------------------------------------ armonía
            notas = [base + n for n in acordes[tipo]]
            if estilo == "rock" and s in (0, 3, 6, 8, 11, 14):
                d = paso * 2.6
                x = sum(np.sign(np.sin(PI2 * _hz(n) * _t(d))) for n in (base, base + 7, base + 12))
                _poner(arm, _lp(x, 1800) * _env(d, 0.004, 0.18), i, 0.16)
            elif estilo == "latino" and s in (2, 5, 10, 13):
                for n in notas:
                    _poner(arm, _piano(_hz(n + 12), paso * 2), i, 0.18)
            elif estilo == "synth" and s == 0:
                d = paso * 16
                x = sum(_sierra(_hz(n), d, 0.006) for n in notas)
                e = np.minimum(1, _t(d) / 0.2) * np.minimum(1, (d - _t(d)) / 0.3)
                _poner(arm, _lp(x, 1400) * e, i, 0.06)
            elif estilo == "calma" and s in (0, 8):
                for k, n in enumerate(notas):
                    _poner(arm, _piano(_hz(n + 12), paso * 9), i + k * 500, 0.16)
            # ------------------------------------------------------- melodía
            prob = {"rock": 0.3, "latino": 0.45, "synth": 0.5, "calma": 0.22}[estilo]
            if c >= 2 and (s % 2 == 0 or estilo in ("latino", "synth")) and rng.random() < prob:
                nota_ant = int(np.clip(nota_ant + rng.integers(-2, 3), 0, 9))
                m = tono + 12 + 12 * (nota_ant // 5) + escala[nota_ant % 5]
                d = paso * float(rng.choice([1.5, 2, 3]))
                if estilo == "synth":
                    x = _lp(_sierra(_hz(m), d, 0.004), 2600) * _env(d, 0.006, 0.2)
                    g = 0.1
                elif estilo == "rock":
                    x = _lp(np.tanh(3 * np.sin(PI2 * _hz(m) * _t(d))), 2400) * _env(d, 0.006, 0.25)
                    g = 0.16
                elif estilo == "latino":
                    x = np.sin(PI2 * _hz(m + 12) * _t(d)) * _env(d, 0.002, 0.09)
                    g = 0.28
                else:
                    x = _piano(_hz(m + 12), d * 2)
                    g = 0.2
                _poner(mel, x, i, g)
    centro = bat * 0.55 + bajo * 0.4
    eco = np.roll(mel, n_paso * 3) * 0.35
    izq = centro + arm * 1.0 + mel * 0.8 + eco * 0.3
    der = centro + np.roll(arm, 300) * 1.0 + mel * 0.6 + eco
    st = np.stack([izq, der], axis=1)
    st = np.tanh(st * (0.9 / max(1e-6, np.max(np.abs(st)))) * 1.3)
    return st.astype(np.float32)


EXT = (".wav", ".ogg", ".flac", ".mp3")


# Toda la música se lleva al mismo nivel al cargarla, venga de donde venga: así una canción tuya,
# una pieza generada con una IA y la música de serie suenan igual de fuertes, y lo único que manda
# es el volumen que elijas en Opciones.
NIVEL_RADIO = 0.15        # nivel medio (RMS) al que queda cada canción de la radio
# Una canción larga no se carga entera: una hora de música son más de siete gigas de memoria mientras se prepara,
# y eso deja colgado el ordenador. A partir de cinco minutos se lee y suena por tramos de un minuto, uno tras otro.
LARGA = 300.0             # segundos a partir de los cuales una canción se toca por tramos
TROZO = 60.0              # lo que dura cada tramo
SOLAPE = 0.25             # los tramos se pisan un cuarto de segundo, fundidos, para que no se note la costura
MAX_PIEZA = 600.0         # la música de ambiente se corta a los diez minutos
NIVEL_AMBIENTE = 0.11     # y cada pieza de música de ambiente


def nivel_musica(d):
    """Nivel medio de una pista, sin contar los silencios ni los pasajes muy flojos."""
    x = np.asarray(d, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    bloque = int(0.4 * SR)
    n = len(x) // bloque
    if n < 2:
        return float(np.sqrt(np.mean(x * x))) if len(x) else 0.0
    e = np.mean(x[:n * bloque].reshape(n, bloque) ** 2, axis=1)
    fuertes = e[e > e.max() * 0.01]                 # se descartan los bloques 20 dB por debajo del más fuerte
    return float(np.sqrt(fuertes.mean())) if len(fuertes) else 0.0


def normalizar_musica(d, objetivo):
    nv = nivel_musica(d)
    if nv < 1e-5:
        return d
    g = objetivo / nv
    pico = float(np.max(np.abs(d))) * g
    if pico > 0.98:
        g *= 0.98 / pico
    return (d * g).astype(np.float32)


class Radio:
    """Gestiona las emisoras. La música vive en data/radio.

    - Cada emisora de serie tiene su nombre de archivo: bravo, latina, neon... Todas las canciones cuyo
      archivo se llame así, o así seguido de guion bajo y lo que sea (bravo.mp3, bravo_1.mp3, bravo_2.ogg),
      son de esa emisora: suenan al azar y, al acabar una, entra otra distinta.
    - Si una emisora no tiene ningún archivo, el juego compone su música original y la guarda.
    - Cualquier otro archivo de audio que se deje en data/radio es una emisora nueva.
    - La carpeta data/radio/mi_musica es la emisora «Mi música», que va pasando sus canciones.

    Las canciones no se cargan todas al arrancar: se lee solo la que va a sonar, en segundo plano,
    para que dé igual cuántas haya y lo largas que sean.
    """

    def __init__(self, mezclador, carpeta):
        self.mez = mezclador
        self.carpeta = carpeta
        self.usuario = os.path.join(carpeta, "mi_musica")
        self.listas = set()
        self.canal = None
        self.actual = 0
        self.pistas_usuario = []
        self.pista_idx = 0
        self.cancelado = False
        self.pistas = {}            # emisora de serie -> lista de archivos
        self.memoria = {}           # emisora compuesta que no se pudo guardar en disco -> datos
        self.ultima = {}
        self.sonando = None
        self.t_fin = 0.0
        self.pendiente = False
        self._pedido = 0
        self._listo = None
        self._larga = None           # la canción larga que suena por tramos: {"ruta", "trozo", "total", "g"}
        self._prox = None            # el tramo siguiente, ya leído: (pedido, número de tramo, datos)
        self._leyendo = False
        self._nombre_pista = ""
        self._cargador = None
        os.makedirs(self.usuario, exist_ok=True)
        fijas = [e for e in EMISORAS if "estilo" in e]
        ids = sorted((e["id"] for e in fijas), key=len, reverse=True)
        self.pistas = {i: [] for i in ids}
        extras = []
        for f in sorted(os.listdir(carpeta)):
            nombre, ext = os.path.splitext(f)
            if ext.lower() not in EXT:
                continue
            emisora = next((i for i in ids if nombre == i or nombre.startswith(i + "_")), None)
            if emisora:
                self.pistas[emisora].append(os.path.join(carpeta, f))
            else:
                extras.append({"id": "extra_" + nombre, "nombre": nombre.replace("_", " ").capitalize(), "archivo": os.path.join(carpeta, f)})
        self.emisoras = ([e for e in EMISORAS if e["id"] == "apagada"] + fijas + extras +
                         [e for e in EMISORAS if e["id"] in ("usuario", "noticias")])
        self._hilo = threading.Thread(target=self._preparar, daemon=True)
        self._hilo.start()

    def _preparar(self):
        from .sintesis import escribir_wav
        for e in self.emisoras:
            if self.cancelado:
                return
            if "estilo" not in e:
                continue
            if not self.pistas[e["id"]]:
                datos = componer(e["estilo"], e["bpm"], e["semilla"], e["tono"])
                ruta = os.path.join(self.carpeta, e["id"] + ".wav")
                try:
                    escribir_wav(ruta, datos)
                    self.pistas[e["id"]].append(ruta)
                except Exception:
                    self.memoria[e["id"]] = datos
                    self.pistas[e["id"]].append("memoria:" + e["id"])
            self.listas.add(e["id"])
        self._buscar_usuario()

    def _buscar_usuario(self):
        try:
            self.pistas_usuario = sorted(os.path.join(self.usuario, f) for f in os.listdir(self.usuario)
                                         if os.path.splitext(f)[1].lower() in EXT)
        except OSError:
            self.pistas_usuario = []

    def esperar(self):
        """Espera a que estén listas las emisoras y, si hay una canción cargándose, a que empiece a sonar."""
        self._hilo.join()
        if self._cargador is not None:
            self._cargador.join()
            self.actualizar(0.0)

    def cancelar(self):
        """Deja de cargar y espera a que los hilos terminen lo que tengan a medias. Para cerrar el programa."""
        self.cancelado = True
        self._pedido += 1
        self._hilo.join(10)
        if self._cargador is not None:
            self._cargador.join(10)

    def id_actual(self):
        return self.emisoras[self.actual % len(self.emisoras)]["id"]

    def nombre(self, i=None):
        return self.emisoras[(self.actual if i is None else i) % len(self.emisoras)]["nombre"]

    def apagar(self):
        self._pedido += 1                # lo que se estuviera cargando ya no interesa
        self.pendiente = False
        self.sonando = None
        self._larga = None
        self._prox = None
        if self.canal is not None:
            self.canal.parar()
            self.canal = None

    def _elegir(self, ident):
        todas = self.pistas.get(ident, [])
        ops = [p for p in todas if p != self.ultima.get(ident)] or todas
        ruta = random.choice(ops)
        self.ultima[ident] = ruta
        return ruta

    def _rota(self):
        """¿Hay más de una canción en lo que suena? Entonces, al acabar una entra otra."""
        ident = self.id_actual()
        if ident == "usuario":
            return len(self.pistas_usuario) > 1
        return len(self.pistas.get(ident, [])) > 1

    def _pedir(self, ruta):
        """Carga una canción en segundo plano. Empieza a sonar en cuanto está lista."""
        from .sintesis import leer_audio
        self._pedido += 1
        n = self._pedido
        self.pendiente = True

        def cargar():
            larga = None
            try:
                if ruta.startswith("memoria:"):
                    datos = self.memoria.get(ruta[8:])
                    datos = normalizar_musica(datos, NIVEL_RADIO) if datos is not None and len(datos) > 100 else None
                else:
                    from .sintesis import duracion_audio
                    dur = duracion_audio(ruta)
                    if dur > LARGA:                  # larga: solo el primer tramo, y la ganancia para toda la canción
                        larga = {"ruta": ruta, "trozo": 0, "total": max(1, int(math.ceil(dur / TROZO))), "g": self._ganancia_larga(ruta, dur)}
                        datos = self._leer_trozo(larga, 0)
                    else:
                        datos = leer_audio(ruta, mono=False)
                        datos = normalizar_musica(datos, NIVEL_RADIO) if datos is not None and len(datos) > 100 else None
            except Exception:
                datos, larga = None, None
            self._listo = (n, datos, ruta, larga)
        self._cargador = threading.Thread(target=cargar, daemon=True)
        self._cargador.start()

    # ------------------------------------------------------------- canciones largas, por tramos
    def _ganancia_larga(self, ruta, dur):
        """El volumen de una canción larga se decide con ocho muestras de cinco segundos repartidas por toda ella,
        para que todos los tramos suenen al mismo nivel sin tener que leerla entera."""
        from .sintesis import leer_audio
        niveles, pico = [], 0.0
        for k in range(8):
            try:
                m = leer_audio(ruta, mono=False, desde=dur * (k + 0.5) / 8.0, maximo=5.0)
            except Exception:
                continue
            if len(m) > 100:
                niveles.append(nivel_musica(m))
                pico = max(pico, float(np.max(np.abs(m))))
        niveles = [x for x in niveles if x > 1e-5]
        if not niveles:
            return 1.0
        g = NIVEL_RADIO / (sum(niveles) / len(niveles))
        return g * 0.98 / (pico * g) if pico * g > 0.98 else g

    def _leer_trozo(self, larga, k):
        """Lee del disco solo el tramo k, ya nivelado y con los fundidos de sus extremos."""
        from .sintesis import leer_audio
        d = leer_audio(larga["ruta"], mono=False, desde=k * TROZO, maximo=TROZO + SOLAPE)
        if d is None or len(d) < 100:
            return None
        d = np.clip(d * larga["g"], -1.0, 1.0).astype(np.float32)
        n = min(int(SOLAPE * SR), len(d) // 2)
        rampa = np.linspace(0.0, 1.0, n, dtype=np.float32)
        if d.ndim == 2:
            rampa = rampa[:, None]
        if k > 0:
            d[:n] *= rampa                               # entra fundiéndose con el final del tramo anterior
        if k < larga["total"] - 1 and len(d) >= int(TROZO * SR):
            d[-n:] *= rampa[::-1]                        # y sale fundiéndose con el principio del siguiente
        return d

    def _pedir_trozo(self, k):
        """Lee en segundo plano el tramo siguiente, con un minuto de margen."""
        larga, pedido = self._larga, self._pedido
        if larga is None or self._leyendo:
            return
        self._leyendo = True

        def leer():
            try:
                d = self._leer_trozo(larga, k)
            except Exception:
                d = None
            if pedido == self._pedido:
                self._prox = (pedido, k, d)
            self._leyendo = False
        self._lector = threading.Thread(target=leer, daemon=True)
        self._lector.start()

    def _tocar(self, datos, bucle, tras=None):
        """Hace sonar unos datos. Los tramos alternan entre dos nombres: uno entra mientras el otro aún se apaga.
        Con `tras`, entra alineado con ese canal, muestra a muestra, para que la costura no se oiga."""
        nombre = "radio_pista_b" if self._nombre_pista == "radio_pista" else "radio_pista"
        self._nombre_pista = nombre
        self.mez.registrar(nombre, datos)
        if tras is not None:
            self.canal = self.mez.encadenar(tras, nombre, TROZO * SR, bucle=bucle, cat="musica")
        else:
            self.canal = self.mez.sonar(nombre, bucle=bucle, cat="musica")
        self.t_fin = len(datos) / SR

    def actualizar(self, dt):
        """Se llama en cada fotograma: arranca la canción recién cargada y pasa a la siguiente cuando acaba una."""
        listo = self._listo
        if listo is not None:
            self._listo = None
            n, datos, ruta, larga = listo
            if n == self._pedido and self.pendiente:
                self.pendiente = False
                if self.canal is not None:
                    self.canal.parar()
                    self.canal = None
                self._larga, self._prox = None, None
                if datos is None:
                    self._siguiente()                    # archivo ilegible: se prueba con otro
                else:
                    self._larga = larga
                    self._tocar(datos, bucle=larga is None and not self._rota())
                    self.sonando = ruta
                    if larga is not None and larga["total"] > 1:
                        self._pedir_trozo(1)
            return
        if self.canal is None or self.pendiente:
            return
        larga = self._larga
        if larga is not None:
            ultimo = larga["trozo"] >= larga["total"] - 1
            por_donde = self.mez.posicion(self.canal)    # se va por lo que de verdad ha sonado, no por el reloj
            if not ultimo and (por_donde >= TROZO * SR or self.canal.fin):       # toca empalmar con el tramo siguiente
                prox = self._prox
                if prox is not None and prox[0] == self._pedido and prox[1] == larga["trozo"] + 1:
                    self._prox = None
                    if prox[2] is None:                  # el archivo se acaba antes de lo que decía: se da por terminado
                        larga["trozo"] = larga["total"] - 1
                    else:
                        larga["trozo"] += 1
                        self._tocar(prox[2], bucle=False, tras=self.canal)       # el canal anterior termina solo, fundido
                        if larga["trozo"] < larga["total"] - 1:
                            self._pedir_trozo(larga["trozo"] + 1)
                elif not self._leyendo:
                    self._pedir_trozo(larga["trozo"] + 1)        # no estaba pedido: se pide; habrá un silencio corto
            elif ultimo and self.canal.fin:
                if self._rota():
                    self._siguiente()
                else:
                    self._pedir(larga["ruta"])           # una sola canción larga: vuelve a empezar
            return
        if self._rota():
            self.t_fin -= dt
            if self.t_fin <= 1.0:
                self._siguiente()

    def _siguiente(self):
        ident = self.id_actual()
        if ident == "usuario" and self.pistas_usuario:
            self.pista_idx += 1
            self._pedir(self.pistas_usuario[self.pista_idx % len(self.pistas_usuario)])
        elif len(self.pistas.get(ident, [])) > 1:
            self._pedir(self._elegir(ident))

    def sintonizar(self, i):
        """Pone la emisora i. Devuelve el texto a anunciar."""
        self.actual = i % len(self.emisoras)
        self.apagar()
        e = self.emisoras[self.actual]
        if e["id"] in ("apagada", "noticias"):
            return e["nombre"]
        if e["id"] == "usuario":
            self._buscar_usuario()
            if not self.pistas_usuario:
                return "Mi música: la carpeta data, radio, mi_musica está vacía. Copia en ella tus canciones."
            ruta = self.pistas_usuario[self.pista_idx % len(self.pistas_usuario)]
            self._pedir(ruta)
            return "Mi música: " + os.path.splitext(os.path.basename(ruta))[0].replace("_", " ")
        if "archivo" in e:
            self._pedir(e["archivo"])
            return e["nombre"]
        if e["id"] not in self.listas:
            return e["nombre"] + ". Sintonizando, espera un momento."
        self._pedir(self._elegir(e["id"]))
        return e["nombre"]

    def siguiente_pista(self):
        if self.id_actual() == "usuario" and self.pistas_usuario:
            self.pista_idx += 1
            ruta = self.pistas_usuario[self.pista_idx % len(self.pistas_usuario)]
            if self.canal is not None:
                self.canal.parar()
                self.canal = None
            self._pedir(ruta)
            return "Mi música: " + os.path.splitext(os.path.basename(ruta))[0].replace("_", " ")
        return None

    def reanudar(self):
        if self.canal is None and not self.pendiente and self.id_actual() not in ("apagada", "noticias"):
            return self.sintonizar(self.actual)
        return None


# ---------------------------------------------------------------------------
# Música de ambiente: suena de fondo mientras exploras y calla cuando pones la radio
# ---------------------------------------------------------------------------
# Cada situación tiene varias piezas. Se elige una al azar y, cuando termina, entra otra distinta.
AMBIENTES = {
    "exploracion": ("De día, explorando con calma", [
        (52, 5, [(0, "M7"), (9, "m7"), (5, "M7"), (7, "7")]), (55, 6, [(0, "M7"), (4, "m7"), (9, "m7"), (5, "M7")]),
        (50, 7, [(0, "M7"), (7, "7"), (9, "m7"), (5, "M7")]), (57, 8, [(0, "m7"), (5, "7"), (10, "M7"), (3, "M7")])]),
    "noche": ("De noche", [
        (45, 17, [(0, "m7"), (8, "M7"), (3, "M7"), (10, "7")]), (43, 18, [(0, "m7"), (5, "m7"), (8, "M7"), (7, "7")]),
        (47, 19, [(0, "m7"), (10, "M7"), (8, "M7"), (0, "m7")])]),
    "mar": ("En el mar", [
        (50, 29, [(0, "M7"), (5, "M7"), (9, "m7"), (5, "M7")]), (48, 30, [(0, "M7"), (7, "7"), (5, "M7"), (0, "M7")]),
        (53, 31, [(0, "M7"), (9, "m7"), (2, "m7"), (7, "7")])]),
    "tension": ("Con la policía detrás o enemigos cerca", [
        (43, 41, [(0, "m"), (1, "M"), (0, "m"), (10, "m")]), (45, 42, [(0, "m"), (8, "M"), (0, "m"), (7, "M")]),
        (41, 43, [(0, "m"), (3, "M"), (1, "M"), (0, "m")])]),
    "menu": ("En el menú principal", [
        (48, 53, [(0, "m7"), (5, "m7"), (10, "M7"), (3, "M7")]), (50, 54, [(0, "M7"), (9, "m7"), (5, "M7"), (7, "7")]),
        (46, 55, [(0, "m7"), (8, "M7"), (10, "M7"), (7, "7")]), (53, 56, [(0, "M7"), (4, "m7"), (5, "M7"), (7, "7")])]),
}
SR_MUSICA = 22050       # la música de ambiente es grave y suave: a media frecuencia ocupa la mitad y suena igual


def _circular(dest, x, i, g=1.0):
    """Suma x en dest empezando en i y dando la vuelta, para que el bucle empalme."""
    n = len(dest)
    i %= n
    primera = min(len(x), n - i)
    dest[i:i + primera] += x[:primera] * g
    if primera < len(x):
        resto = x[primera:primera + n]
        dest[:len(resto)] += resto * g


def componer_ambiente(tipo, variante=0):
    """Pieza estéreo (N, 2) float32 de música de ambiente, pensada para repetirse sin cortes."""
    tono, semilla, prog = AMBIENTES[tipo][1][variante % len(AMBIENTES[tipo][1])]
    rng = np.random.default_rng(semilla)
    acordes = {"m": (0, 3, 7), "M": (0, 4, 7), "M7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "7": (0, 4, 7, 10)}
    dur_acorde = 7.0 if tipo != "tension" else 4.8
    total = int(SR * dur_acorde * len(prog))
    izq = np.zeros(total)
    der = np.zeros(total)
    d = dur_acorde + 3.0
    t = _t(d)
    env = np.minimum(1, t / 2.2) * np.minimum(1, (d - t) / 2.6)
    for k, (raiz, tipo_ac) in enumerate(prog):
        i = int(k * dur_acorde * SR)
        notas = [tono + raiz + n for n in acordes[tipo_ac]]
        pad_i = np.zeros(len(t))
        pad_d = np.zeros(len(t))
        for n in notas:
            f = _hz(n)
            pad_i += np.sin(PI2 * f * 0.997 * t + rng.uniform(0, PI2)) + 0.4 * np.sin(PI2 * f * 2.003 * t)
            pad_d += np.sin(PI2 * f * 1.003 * t + rng.uniform(0, PI2)) + 0.4 * np.sin(PI2 * f * 1.997 * t)
        bajo = np.sin(PI2 * _hz(tono + raiz - 12) * t) * 1.2
        lfo = 0.8 + 0.2 * np.sin(PI2 * 0.13 * t + k)
        _circular(izq, (pad_i + bajo) * env * lfo, i, 0.11)
        _circular(der, (pad_d + bajo) * env * lfo, i, 0.11)
        if tipo == "tension":
            paso = dur_acorde / 8
            for s_ in range(8):
                pulso = np.sin(PI2 * _hz(tono + raiz - 24) * _t(0.4)) * _env(0.4, 0.004, 0.12)
                _circular(izq, pulso, i + int(s_ * paso * SR), 0.5)
                _circular(der, pulso, i + int(s_ * paso * SR), 0.5)
                if s_ in (3, 7) or (variante % 2 and s_ == 5):
                    tom = np.sin(PI2 * np.cumsum(70 + 60 * np.exp(-_t(0.5) / 0.05)) / SR) * np.exp(-_t(0.5) / 0.18)
                    _circular(izq, tom, i + int(s_ * paso * SR), 0.35)
                    _circular(der, tom, i + int((s_ * paso + 0.02) * SR), 0.35)
        else:
            for _ in range(3 if tipo != "menu" else 6):
                n = int(rng.choice(notas)) + 12 * int(rng.integers(1, 3))
                nota = _piano(_hz(n), 3.5) * 0.9
                pos = i + int(rng.uniform(0.3, dur_acorde - 0.5) * SR)
                pan = rng.uniform(0.25, 0.75)
                _circular(izq, nota, pos, 0.13 * (1 - pan) * 2)
                _circular(der, nota, pos, 0.13 * pan * 2)
    st = np.stack([_lp(izq, 3200), _lp(der, 3200)], axis=1)
    st = np.tanh(st * (0.55 / max(1e-6, np.max(np.abs(st)))) * 1.2)
    return st.astype(np.float32)


class MusicaAmbiente:
    """Música de fondo según la situación.

    Vive en data/musica, con una carpeta por situación (menu, exploracion, noche, mar, tension).
    Cada archivo de una carpeta es una pieza: se usan todas las que haya, se llamen como se llamen;
    se empieza por una al azar y, cuando termina, entra otra distinta.

    Al arrancar solo se hace la lista de piezas. Cada pieza se lee cuando le toca sonar, en segundo plano,
    y se suelta de la memoria cuando deja de sonar: da igual cuántas haya y lo largas que sean.
    """

    def __init__(self, mezclador, carpeta):
        self.mez = mezclador
        self.carpeta = carpeta
        self.pistas = {k: [] for k in AMBIENTES}      # situación -> [(nombre de sonido, duración, archivo)]
        self.rutas = {}            # nombre de sonido -> archivo (None si se compuso en memoria)
        self.listas = set()
        self.canales = {}          # nombre de sonido -> [canal, volumen, situación]
        self.cargando = {}         # nombre de sonido -> hilo que lo está leyendo
        self.actual = None         # situación que suena
        self.pista = None
        self.ultima = {}
        self.t_pista = 0.0
        self.cancelado = False
        os.makedirs(carpeta, exist_ok=True)
        self._hilo = threading.Thread(target=self._preparar, daemon=True)
        self._hilo.start()

    def _preparar(self):
        import soundfile as sf
        for nombre in AMBIENTES:
            if self.cancelado:
                return
            sub = os.path.join(self.carpeta, nombre)
            os.makedirs(sub, exist_ok=True)
            marca = os.path.join(sub, "_originales.txt")
            if not os.path.exists(marca):
                # primera vez: se componen las piezas de serie
                for v in range(len(AMBIENTES[nombre][1])):
                    ruta = os.path.join(sub, f"{nombre}_{v + 1}.wav")
                    if not any(os.path.exists(os.path.join(sub, f"{nombre}_{v + 1}{ext}")) for ext in EXT):
                        try:
                            sf.write(ruta, componer_ambiente(nombre, v)[::2], SR_MUSICA, subtype="PCM_16")
                        except Exception:
                            pass
                try:
                    open(marca, "w", encoding="utf-8").write("Piezas de serie creadas. Si borras este archivo, se vuelven a crear las que falten.")
                except OSError:
                    pass
            for f in sorted(os.listdir(sub)):
                if os.path.splitext(f)[1].lower() in EXT:
                    ruta = os.path.join(sub, f)
                    try:
                        dur = float(sf.info(ruta).duration)
                    except Exception:
                        continue
                    if dur > 0.05:
                        clave = f"musica_{nombre}_{os.path.splitext(f)[0]}"
                        if clave not in self.rutas:
                            self.rutas[clave] = ruta
                            self.pistas[nombre].append((clave, dur, ruta))
            if not self.pistas[nombre]:
                clave = f"musica_{nombre}_base"
                datos = normalizar_musica(componer_ambiente(nombre, 0), NIVEL_AMBIENTE)
                self.mez.registrar(clave, datos)
                self.rutas[clave] = None
                self.pistas[nombre].append((clave, len(datos) / SR, None))
            self.listas.add(nombre)

    def esperar(self):
        self._hilo.join()

    def cancelar(self):
        """Deja de preparar piezas y espera a que los hilos terminen lo que tengan a medias. Para cerrar el programa."""
        self.cancelado = True
        self._hilo.join(10)
        for h in list(self.cargando.values()):
            h.join(10)

    def esperar_carga(self):
        """Espera a que termine de leerse la pieza que esté a medias."""
        for h in list(self.cargando.values()):
            h.join()

    def cargar_ahora(self, clave):
        """Lee una pieza y la deja lista para sonar, ya nivelada."""
        from .sintesis import leer_audio
        ruta = self.rutas.get(clave)
        if clave in self.mez.sonidos or not ruta:
            return clave in self.mez.sonidos
        try:
            datos = leer_audio(ruta, mono=False, maximo=MAX_PIEZA)       # una pieza de ambiente más larga se corta: no se carga entera
        except Exception:
            return False
        if len(datos) < 1000 or self.cancelado:
            return False
        self.mez.registrar(clave, normalizar_musica(datos, NIVEL_AMBIENTE))
        return True

    def _pedir(self, clave):
        if clave in self.mez.sonidos or clave in self.cargando:
            return

        def cargar():
            try:
                self.cargar_ahora(clave)
            finally:
                self.cargando.pop(clave, None)
            if clave != self.pista and clave not in self.canales:
                self._soltar(clave)              # mientras se leía ya se pidió otra: esta no llega a sonar
        h = threading.Thread(target=cargar, daemon=True)
        self.cargando[clave] = h
        h.start()

    def _limpiar(self):
        """Suelta las piezas cargadas que ni suenan ni van a sonar."""
        for clave, ruta in list(self.rutas.items()):
            if ruta and clave in self.mez.sonidos and clave != self.pista and clave not in self.canales and clave not in self.cargando:
                self._soltar(clave)

    def _soltar(self, clave):
        """Una pieza que ya no suena deja de ocupar memoria."""
        if self.rutas.get(clave) and clave != self.pista:
            self.mez.sonidos.pop(clave, None)
            for k in [k for k in list(self.mez._var) if k[0] == clave]:      # copia: lo puede estar tocando otro hilo
                self.mez._var.pop(k, None)

    def volumen_actual(self):
        return self.canales[self.pista][1] if self.pista in self.canales else 0.0

    def _otra(self, situacion):
        ops = [p for p in self.pistas[situacion] if p[0] != self.ultima.get(situacion)] or self.pistas[situacion]
        clave, dur, _ = random.choice(ops)
        self.ultima[situacion] = clave
        self.pista = clave
        # una pieza corta se repite hasta sumar cerca de un minuto; una canción larga suena una vez entera
        self.t_pista = dur * max(1, round(55.0 / dur))
        self._limpiar()
        self._pedir(clave)

    def actualizar(self, dt, deseada, volumen):
        """deseada: situación cuya música debe sonar, o None para silencio. Hace fundidos suaves."""
        if deseada is not None and deseada not in self.listas:
            deseada = None
        if deseada != self.actual:
            self.actual = deseada
            self.pista = None
            if deseada is not None:
                self._otra(deseada)
            else:
                self._limpiar()
        elif deseada is not None:
            self.t_pista -= dt
            if self.t_pista <= 0:
                self._otra(deseada)          # se acabó la pieza: entra otra
        if self.pista and self.pista not in self.canales and self.pista in self.mez.sonidos:
            self.canales[self.pista] = [self.mez.sonar(self.pista, bucle=True, cat="musica", vol=0.0), 0.0, self.actual]
        for clave in list(self.canales):
            canal, vol, _ = self.canales[clave]
            objetivo = volumen if clave == self.pista else 0.0
            paso = dt / (2.5 if objetivo > vol else 1.5)
            vol = min(objetivo, vol + paso) if objetivo > vol else max(objetivo, vol - paso)
            self.canales[clave][1] = vol
            canal.volumen(vol)
            if vol <= 0.0 and clave != self.pista:
                canal.parar()
                del self.canales[clave]
                self._soltar(clave)

    def callar(self):
        for canal, _, _ in self.canales.values():
            canal.parar()
        self.pista = None
        self.actual = None
        for clave in list(self.canales):
            del self.canales[clave]
        self._limpiar()
