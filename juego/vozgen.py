"""Las voces de un personaje hecho por el jugador: se generan en su ordenador, con su nombre.

Las grabaciones que trae el juego llaman al protagonista por el nombre de los cuatro personajes de la lista. A un
personaje propio hay que nombrarle con el nombre que ha escrito el jugador, y eso no se puede traer grabado: lo
genera aquí el motor de voz Phonon, de Gradium, con las mismas voces de los personajes de la historia.

Va en un hilo aparte y sin prisa, para no dar tirones al juego. Lo generado se guarda en data/voces_generadas, en una
carpeta por personaje, así que solo se hace una vez. Mientras una frase no está lista, la dice el lector de pantalla.

El modelo Phonon 40m es de Gradium y tiene licencia CC BY-NC 4.0: uso no comercial, citando a Gradium.
"""
import hashlib
import json
import os
import re
import threading
import time

from . import genero, registro, rutas

PROTA = "Dani"                                   # con este nombre figuran en los datos las frases del protagonista
VOCES_PROTA = ("dani", "alex", "sam", "cris")    # las voces de protagonista que hay, una por personaje de la lista y género
NOMBRE_VOZ = {"dani": "la de Dani", "alex": "la de Álex", "sam": "la de Sam", "cris": "la de Cris"}
_DANI = re.compile(r"\bDani\b")
_estado = {"ok": None, "motivo": ""}
VERSION = 1                                      # cambia si cambia la manera de generar: lo ya generado se rehace


def carpeta_motor():
    return os.path.join(rutas.DATA, "phonon")


def carpeta_generadas():
    return os.path.join(rutas.DATA, "voces_generadas")


def _avx2():
    """El motor necesita un procesador con AVX2. Sin él no se puede ni cargar: se comprueba antes."""
    try:
        import ctypes
        return bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(40))        # PF_AVX2_INSTRUCTIONS_AVAILABLE
    except Exception:
        return True                                  # fuera de Windows no hay esa pregunta: se intenta


def disponible():
    """¿Se pueden generar voces en este equipo? Lo dice una vez y lo recuerda."""
    if _estado["ok"] is None:
        c = carpeta_motor()
        faltan = [n for n in ("config.json", "tokenizer.json", "model.q8.gguf", "reparto.json") if not os.path.exists(os.path.join(c, n))]
        if faltan:
            _estado.update(ok=False, motivo="Esta copia del juego no trae el generador de voces.")
        elif not _avx2():
            _estado.update(ok=False, motivo="El procesador de este equipo no puede con el generador de voces: le falta AVX2.")
        else:
            try:
                import ptts  # noqa: F401
                _estado.update(ok=True, motivo="")
            except Exception as e:
                _estado.update(ok=False, motivo="El generador de voces no se ha podido cargar.")
                registro.una_vez("vozgen", "No se pudo cargar el motor de voz", error=type(e).__name__)
    return _estado["ok"]


def motivo():
    disponible()
    return _estado["motivo"]


def reparto():
    try:
        with open(os.path.join(carpeta_motor(), "reparto.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"personajes": {}, "protagonista": {}}


class Personaje:
    """Lo que hace falta saber del protagonista para darle voz. No guarda nada más."""

    def __init__(self, nombre, apellido="", gen="h", voz="dani", dicho=""):
        self.nombre, self.apellido = str(nombre or ""), str(apellido or "")
        self.genero = gen if gen in genero.GENEROS else "h"
        self.voz = voz if voz in VOCES_PROTA else "dani"
        self.dicho = str(dicho or "").strip()

    @classmethod
    def de_jugador(cls, j):
        return cls(j.nombre, j.apellido, j.genero, getattr(j, "voz", "dani"), getattr(j, "nombre_dicho", ""))

    def clave(self):
        """El nombre de su carpeta: no deja ver cómo se llama."""
        t = "|".join([self.nombre, self.apellido, self.dicho, self.genero, self.voz, str(VERSION)])
        return hashlib.sha1(t.encode("utf-8")).hexdigest()[:16]

    def carpeta(self):
        return os.path.join(carpeta_generadas(), self.clave())

    def texto(self, t):
        """La frase tal como hay que decirla: con su nombre, en su género."""
        t = genero.resolver(t, self.genero)
        nombre = self.dicho or self.nombre
        t = t.replace("Dani Roca", f"{nombre} {self.apellido}".strip())
        return _DANI.sub(nombre, t)


def para_decir(texto):
    """El texto como conviene dárselo al motor: sin comillas ni signos raros, y con pausas claras."""
    t = texto.replace("«", "").replace("»", "").replace(";", ",").replace("...", ".").replace("…", ".").replace("Seisdedos", "Seis Dedos")
    return " ".join(t.split())


def nombra(texto):
    return bool(_DANI.search(texto))


def pendientes(pj, misiones, rep=None):
    """Las frases que hay que generarle a este personaje: las que dicen su nombre. [(ruta, archivo de voz, texto)], en el orden de la historia."""
    rep = rep or reparto()
    out = []
    destino = pj.carpeta()
    for m in misiones:
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            for n, linea in enumerate(paso.get("lineas", [])):
                quien, texto = (linea.get("quien"), linea.get("texto")) if isinstance(linea, dict) else (linea[0], linea[1])
                if not isinstance(texto, str) or not nombra(texto):
                    continue
                voz = rep["protagonista"].get(f"{pj.voz}_{pj.genero}") if quien == PROTA else rep["personajes"].get(quien)
                if not voz:
                    continue
                out.append((os.path.join(destino, f"{m.get('id')}_{k + 1}_{n + 1}.ogg"), voz, pj.texto(texto), str(m.get("id"))))
    return out


def _limpio(pcm, sr):
    import numpy as np
    pcm = np.asarray(pcm, dtype=np.float32)
    fuerte = np.where(np.abs(pcm) > 0.01)[0]
    if len(fuerte):
        pcm = pcm[max(0, fuerte[0] - int(0.05 * sr)):min(len(pcm), fuerte[-1] + int(0.15 * sr))]
    pico = float(np.abs(pcm).max()) if len(pcm) else 0.0
    return pcm * (0.89 / pico) if pico > 0 else pcm


class Generador:
    """El hilo que genera. Hay uno solo para todo el juego."""

    def __init__(self):
        self.cola = []
        self.cerrojo = threading.Lock()
        self.hilo = None
        self.total = 0
        self.hechas = 0
        self.fallos = 0
        self.parar = False
        self.hilos_motor = 2
        self.permitido = lambda: True                # el juego dice aquí si las opciones siguen dejando generar
        self._tts = None
        self._voces = set()

    # ------------------------------------------------------------ lo que se pide
    def pedir(self, pj, misiones, primero=None):
        """Pone a generar lo que le falte a este personaje. Devuelve cuántas frases faltan. `primero`: la misión que corre prisa."""
        if not disponible():
            return 0
        faltan = [f for f in pendientes(pj, misiones) if not self._vale(f)]
        if primero:
            faltan.sort(key=lambda f: f[3] != primero)            # estable: lo de esa misión delante, lo demás en su orden
        cuantas = len(faltan)                         # se cuenta antes de arrancar: el hilo va vaciando la cola
        with self.cerrojo:
            self.cola = list(faltan)
            self.total = cuantas
            self.hechas = 0
            self.parar = False
        if cuantas and (self.hilo is None or not self.hilo.is_alive()):
            self.hilo = threading.Thread(target=self._correr, name="voces", daemon=True)
            self.hilo.start()
        return cuantas

    def priorizar(self, mision):
        with self.cerrojo:
            self.cola.sort(key=lambda f: f[3] != mision)

    def detener(self):
        with self.cerrojo:
            self.cola = []
            self.parar = True

    def activo(self):
        return self.hilo is not None and self.hilo.is_alive()

    def quedan(self):
        with self.cerrojo:
            return len(self.cola)

    # -------------------------------------------------------------- generar
    @staticmethod
    def _marca(f):
        return hashlib.sha1((f[1] + "|" + f[2]).encode("utf-8")).hexdigest()[:12]

    def _vale(self, f):
        """¿Está ya generada esa frase, con ese texto y esa voz?"""
        try:
            with open(f[0] + ".txt", encoding="ascii") as g:
                return g.read().strip() == self._marca(f) and os.path.getsize(f[0]) > 500
        except OSError:
            return False

    def _motor(self):
        if self._tts is None:
            import ptts
            self._hilos_puestos = None
            self._tts = ptts.TTS(carpeta_motor(), lang="es", quant="q8")
            self._voces = set()
        return self._tts

    def sintetizar(self, voz, texto):
        """Una frase, con una voz del reparto. Devuelve (audio, frecuencia)."""
        tts = self._motor()
        if getattr(self, "_hilos_puestos", None) != self.hilos_motor:      # en la pantalla de espera, a toda máquina; jugando, sin estorbar
            self._hilos_puestos = self.hilos_motor
            try:
                import ptts
                ptts.set_num_threads(self.hilos_motor)
            except Exception:
                pass
        if voz not in self._voces:
            tts.add_voice(voz, os.path.join(carpeta_motor(), "voces", voz + ".safetensors"))
            self._voces.add(voz)
        mejor = None
        for semilla in (7, 23, 51):                               # si sale con un ritmo raro es que se ha comido algo o ha metido ruido: otra vez
            pcm = _limpio(tts.synth(para_decir(texto), voice=voz, seed=semilla), tts.sample_rate)
            ritmo = len(texto) / max(0.1, len(pcm) / tts.sample_rate)
            if mejor is None:
                mejor = pcm
            if 7 <= ritmo <= 26:
                return pcm, tts.sample_rate
        return mejor, tts.sample_rate

    def _guardar(self, f):
        import soundfile as sf
        pcm, sr = self.sintetizar(f[1], f[2])
        os.makedirs(os.path.dirname(f[0]), exist_ok=True)
        tmp = f[0] + ".tmp"
        sf.write(tmp, pcm, sr, format="OGG", subtype="VORBIS")
        os.replace(tmp, f[0])                                     # entera o nada: nunca suena una frase a medio escribir
        with open(f[0] + ".txt", "w", encoding="ascii") as g:
            g.write(self._marca(f))

    def _correr(self):
        try:
            from .musica import baja_prioridad
            baja_prioridad()
        except Exception:
            pass
        t0 = time.time()
        while True:
            with self.cerrojo:
                if self.parar or not self.cola:
                    break
                if not self.permitido():                          # se ha quitado en Opciones: se deja de generar en el acto
                    self.cola = []
                    break
                f = self.cola.pop(0)
            try:
                self._guardar(f)
                self.hechas += 1
            except Exception as e:
                self.fallos += 1
                registro.una_vez("vozgen", "Una frase no se pudo generar", error=type(e).__name__)
                if self.fallos >= 5:                              # algo va mal de verdad: no se insiste
                    with self.cerrojo:
                        self.cola = []
                    break
        if self.hechas:
            registro.info("vozgen", "Voces generadas para el personaje propio", cuantas=self.hechas, segundos=round(time.time() - t0))
        self._tts = None                                          # el modelo ocupa memoria: se suelta al terminar
        self._voces = set()


generador = Generador()


def al_jugar(p, primero=None):
    """Al empezar o cargar una partida, y al empezar cada misión: si el personaje es propio, se le van generando sus voces."""
    if p.j.personaje in VOCES_PROTA or not p.cfg["voces_grabadas"] or not p.cfg["voces_propias"] or getattr(p.app, "pruebas", False):
        generador.detener()                          # con las voces quitadas no se genera nada: lo dice el lector
        return 0
    cfg = p.cfg
    generador.permitido = lambda: bool(cfg["voces_grabadas"] and cfg["voces_propias"])
    if primero and generador.activo():
        generador.priorizar(primero)
        return generador.quedan()
    return generador.pedir(Personaje.de_jugador(p.j), p.datos.get("misiones", []), primero)


class Preparando:
    """La pantalla de «cargando» al empezar con un personaje propio: espera a que estén las primeras frases que le
    nombran y va diciendo cómo va. Escape o Intro la saltan: lo que falte lo dice el lector hasta que esté listo."""
    pausa_mundo = True
    PRIMERAS = 4                                 # las frases que le nombran en el primer capítulo

    def __init__(self, app, pj, misiones, al_terminar):
        self.app, self.pj, self.misiones, self.al_terminar = app, pj, misiones, al_terminar
        self.t = 0.0
        self.t_aviso = 0.0
        self.hecho = False
        self.meta = 0

    def al_entrar(self):
        generador.hilos_motor = max(2, (os.cpu_count() or 4) // 2)     # mientras se espera, a toda máquina
        faltan = generador.pedir(self.pj, self.misiones)
        self.meta = min(self.PRIMERAS, faltan)
        if not self.meta:
            return self._fin()
        self.app.decir("Preparando las voces de tu personaje, para que en la historia te llamen por tu nombre. Solo pasa la primera vez. "
                       "Es cosa de unos segundos; pulsa Escape si prefieres empezar ya.", True)

    def _fin(self):
        if self.hecho:
            return
        self.hecho = True
        generador.hilos_motor = 2                    # lo que quede, ya jugando y sin estorbar
        if self in self.app.pila:
            self.app.pila.remove(self)
        self.al_terminar()

    def actualizar(self, dt):
        if self.hecho:
            return
        self.t += dt
        self.t_aviso += dt
        if generador.hechas >= self.meta or not generador.activo() or self.t > 120:
            self.app.son("guardado")
            return self._fin()
        if self.t_aviso >= 5.0:
            self.t_aviso = 0.0
            self.app.son("menu_mover")
            self.app.decir(f"{generador.hechas} de {self.meta}.")

    def tecla(self, ev):
        import pygame
        if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.app.decir("Empiezas ya. Lo que falte se irá preparando mientras juegas.", True)
            self._fin()
        elif ev.key in (pygame.K_F1, pygame.K_UP):
            self.app.decir(f"Preparando las voces de tu personaje: {generador.hechas} de {self.meta}. Escape para empezar ya.", True)


def probar(app, voz, texto, al_terminar=None):
    """Genera una frase suelta y la hace sonar: para oír cómo queda el nombre antes de empezar. No bloquea el juego."""
    if not disponible():
        app.son("error")
        app.decir(motivo(), True)
        return False
    app.decir("Un momento.", True)

    def tarea():
        try:
            import soundfile as sf
            g = Generador()
            g.hilos_motor = max(2, (os.cpu_count() or 4) // 2)
            pcm, sr = g.sintetizar(voz, texto)
            os.makedirs(carpeta_generadas(), exist_ok=True)
            ruta = os.path.join(carpeta_generadas(), "prueba.ogg")
            sf.write(ruta, pcm, sr, format="OGG", subtype="VORBIS")
            app.voz_prueba = ruta                    # la recoge el menú en su siguiente fotograma
        except Exception as e:
            registro.una_vez("vozgen", "La prueba de voz no salió", error=type(e).__name__)
            app.voz_prueba = False
    threading.Thread(target=tarea, name="voz-prueba", daemon=True).start()
    return True
