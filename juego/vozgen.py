"""Las voces de un personaje hecho por el jugador: se generan en su ordenador, con su nombre.

Las grabaciones que trae el juego llaman al protagonista por el nombre de los cuatro personajes de la lista. A un
personaje propio hay que nombrarle con el nombre que ha escrito el jugador, y eso no se puede traer grabado: lo
genera aquí el motor de voz Phonon, de Gradium, con las mismas voces de los personajes de la historia.

El motor es código nativo y exigente: pide un procesador con AVX2, FMA y F16C, y si algo no le gusta puede cerrar el
programa de golpe, sin dar un error que se pueda atrapar. Por eso va con red de seguridad:

1. Antes de nada se miran las tres capacidades del procesador.
2. La primera vez, el motor se prueba en un proceso aparte (el propio juego, lanzado con --probar-motor-voz): carga el
   modelo y dice una frase corta. Si ese proceso se cae, el juego ni se entera: solo ve que no terminó bien.
3. El resultado se recuerda en data/voces_generadas/motor_probado.json, y se vuelve a probar si cambia la versión del
   juego o cambian los archivos del motor.
4. Si aun así el juego se cierra dos veces seguidas mientras carga el motor, deja de intentarlo.

Cuando no se puede, el juego sigue y las frases las dice el lector de pantalla.

Va en un hilo aparte y sin prisa, para no dar tirones al juego. Lo generado se guarda en data/voces_generadas, en una
carpeta por personaje, así que solo se hace una vez. Mientras una frase no está lista, la dice el lector de pantalla.

El modelo Phonon 40m es de Gradium y tiene licencia CC BY-NC 4.0: uso no comercial, citando a Gradium.
"""
from .i18n import tr
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time

from . import genero, registro, rutas

PROTA = tr("Dani")                                       # con este nombre figuran en los datos las frases del protagonista
VOCES_PROTA = ("dani", "alex", "sam", "cris")    # las voces de protagonista que hay, una por personaje de la lista y género
NOMBRE_VOZ = {"dani": tr("la de Dani"), "alex": tr("la de Álex"), "sam": tr("la de Sam"), "cris": tr("la de Cris")}
_DANI = re.compile(r"\bDani\b")
_estado = {"ok": None, "motivo": ""}
VERSION = 1                                      # cambia si cambia la manera de generar: lo ya generado se rehace


PILA_HILO = 64 * 1024 * 1024                         # el motor de voz y el codificador Vorbis gastan mucha pila


def hilo_con_pila(objetivo, nombre, args=()):
    """Un hilo con pila holgada. En el juego compilado los hilos nacen con la pila de serie de Windows (1 MB), y el
    generador de voces la desbordaba al guardar una frase: Windows cerraba el juego sin dar tiempo a avisar."""
    with _cerrojo_pila:
        antes = threading.stack_size()
        try:
            threading.stack_size(PILA_HILO)
        except (ValueError, RuntimeError):
            pass
        try:
            h = threading.Thread(target=objetivo, args=args, name=nombre, daemon=True)
            h.start()
        finally:
            try:
                threading.stack_size(antes)
            except (ValueError, RuntimeError):
                pass
    return h


def escribir_ogg(ruta, pcm, sr):
    """Guarda una frase en OGG Vorbis a trozos: el codificador, con todo el audio de una vez, gasta mucha más pila."""
    import soundfile as sf
    canales = 1 if getattr(pcm, "ndim", 1) == 1 else pcm.shape[1]
    with sf.SoundFile(ruta, "w", samplerate=sr, channels=canales, format="OGG", subtype="VORBIS") as f:
        for k in range(0, len(pcm), 8192):
            f.write(pcm[k:k + 8192])


_cerrojo_pila = threading.Lock()


def carpeta_motor():
    return os.path.join(rutas.DATA, "phonon")


def idioma():
    """El idioma en que se generan las voces: el del juego, si hay voces para él (data/phonon/voces_en...); si no, español."""
    from . import i18n
    cod = i18n.actual()
    return cod if cod == "es" or os.path.exists(os.path.join(carpeta_motor(), f"reparto_{cod}.json")) else None


def carpeta_voces_motor():
    """Las voces del generador para el idioma del juego: data/phonon/voces las españolas; voces_en, las inglesas..."""
    cod = idioma() or "es"
    return os.path.join(carpeta_motor(), "voces" if cod == "es" else "voces_" + cod)


def carpeta_generadas():
    return os.path.join(rutas.DATA, "voces_generadas")


ARG_PRUEBA = "--probar-motor-voz"                # el juego, lanzado con esto, solo prueba el motor y termina
TIEMPO_PRUEBA = 240                              # segundos: en un equipo lento, cargar el modelo y decir una frase tarda
ARCHIVOS_MOTOR = ("config.json", "tokenizer.json", "model.q8.gguf", "reparto.json")
NECESARIAS = ("AVX2", "FMA", "F16C")             # lo que el motor pide al procesador, según su documentación
PROBANDO = tr("El generador de voces se está comprobando en este equipo. Solo pasa la primera vez y tarda unos segundos: prueba otra vez enseguida.")
_prueba = {"hilo": None, "proc": None, "al_saber": []}
_cerrojo = threading.Lock()


def capacidades():
    """Qué tiene el procesador de lo que pide el motor: {"AVX2": sí o no, "FMA": ..., "F16C": ...}. None en la que no se sepa."""
    caps = dict.fromkeys(NECESARIAS)
    try:
        import ctypes
        caps["AVX2"] = bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(40))        # PF_AVX2_INSTRUCTIONS_AVAILABLE
    except Exception:
        pass                                         # fuera de Windows no hay esa pregunta
    try:                                             # Windows no sabe decir FMA ni F16C: lo sabe la biblioteca de cálculo, que ya está cargada
        try:
            from numpy._core._multiarray_umath import __cpu_features__ as cpu
        except ImportError:
            from numpy.core._multiarray_umath import __cpu_features__ as cpu
        for nombre, clave in (("AVX2", "AVX2"), ("FMA", "FMA3"), ("F16C", "F16C")):
            if clave in cpu:                          # si las dos fuentes opinan, hace falta que las dos digan que sí
                caps[nombre] = bool(cpu[clave]) and caps[nombre] is not False
    except Exception:
        pass
    return caps


def _avx2():
    """Se conserva por compatibilidad: ¿tiene AVX2? Si no se sabe, se toma como que sí."""
    return capacidades()["AVX2"] is not False


def firma_motor():
    """Una huella de los archivos del motor (el modelo y la biblioteca nativa), sin cargarlos: si cambian, hay que volver a probar."""
    partes = []
    carpetas = [carpeta_motor()]
    try:
        import importlib.util
        spec = importlib.util.find_spec("ptts")       # busca el paquete sin ejecutarlo
        carpetas += list(spec.submodule_search_locations or []) if spec else []
    except Exception:
        pass
    for c in carpetas:
        try:
            for n in sorted(os.listdir(c)):
                r = os.path.join(c, n)
                if os.path.isfile(r) and (c != carpetas[0] or n in ARCHIVOS_MOTOR):
                    partes.append(f"{n}:{os.path.getsize(r)}")
        except OSError:
            pass
    return hashlib.sha1("|".join(partes).encode("utf-8")).hexdigest()[:16]


def ruta_recuerdo():
    return os.path.join(carpeta_generadas(), "motor_probado.json")


def leer_recuerdo():
    """Lo que se sabe de la última prueba del motor, si vale todavía: misma versión del juego y mismos archivos del motor."""
    from . import VERSION as JUEGO
    try:
        with open(ruta_recuerdo(), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict) or d.get("juego") != JUEGO or d.get("motor") != firma_motor() or not isinstance(d.get("ok"), bool):
        return None
    return d


def guardar_recuerdo(ok, motivo_="", codigo=0, a_medias=0):
    from . import VERSION as JUEGO
    try:
        os.makedirs(carpeta_generadas(), exist_ok=True)
        tmp = ruta_recuerdo() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"juego": JUEGO, "motor": firma_motor(), "ok": bool(ok), "motivo": motivo_, "codigo": codigo, "a_medias": int(a_medias)}, f, ensure_ascii=False)
        os.replace(tmp, ruta_recuerdo())
    except OSError:
        pass                                         # sin sitio donde apuntarlo, se probará otra vez la próxima


def orden_prueba():
    """Cómo se lanza el proceso de prueba: el propio juego con un argumento. Compilado, es PuertoBravo.exe; desde el código, python main.py."""
    if getattr(sys, "frozen", False):
        return [sys.executable, ARG_PRUEBA, carpeta_motor()]
    return [sys.executable, os.path.join(rutas.base(), "main.py"), ARG_PRUEBA, carpeta_motor()]


def prueba_en_este_proceso(carpeta=None):
    """Lo que hace el proceso de prueba: cargar el motor y decir una frase corta. Devuelve el código con el que termina:
    0 si todo va bien, 10 si el motor no carga, 11 si no genera. Si el motor se cae de golpe, no devuelve nada: el
    proceso muere, y eso es justo lo que el juego quiere saber sin morir él."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(0x8003)   # que Windows no saque un cuadro de error si este proceso se cae
    except Exception:
        pass
    carpeta = carpeta or carpeta_motor()
    try:
        from . import procesador
        if not procesador.preparar():
            return 10
        import ptts
    except BaseException:
        return 10
    try:
        tts = ptts.TTS(carpeta, lang="es", quant="q8")
        voces = sorted(n for n in os.listdir(os.path.join(carpeta, "voces")) if n.endswith(".safetensors"))
        voz = os.path.splitext(voces[0])[0]
        tts.add_voice(voz, os.path.join(carpeta, "voces", voces[0]))
        pcm = tts.synth(tr("Hola."), voice=voz, seed=7)
        return 0 if len(pcm) > 1000 else 11
    except BaseException:
        return 11


def _ejecutar_prueba(orden, tiempo):
    """Lanza el proceso de prueba y espera. Devuelve su código de salida, o None si no terminó a tiempo."""
    entorno = dict(os.environ)
    try:
        from . import procesador
        if procesador.estado["numpy"] in ("antigua", "oficial"):
            entorno["PUERTOBRAVO_NUMPY"] = procesador.estado["numpy"]      # la misma biblioteca de cálculo que usa el juego
    except Exception:
        pass
    banderas = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    proc = subprocess.Popen(orden, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=banderas, env=entorno,
                            cwd=os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else rutas.base())
    _prueba["proc"] = proc
    try:
        return proc.wait(timeout=tiempo)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(10)
        return None
    finally:
        _prueba["proc"] = None


def _motivo_de(codigo):
    if codigo == 0:
        return ""
    if codigo is None:
        return tr("El generador de voces tarda demasiado en este equipo.")
    if codigo == 10:
        return tr("El generador de voces no se ha podido cargar en este equipo.")
    if codigo == 11:
        return tr("El generador de voces ha cargado, pero no ha conseguido generar una frase en este equipo.")
    return tr("El generador de voces no funciona en este equipo: al probarlo aparte, se ha cerrado de golpe.")


SE_REPETIRA = tr(" Las frases que te nombran las dirá el lector de pantalla. Se volverá a probar cuando actualices el juego.")


def probar_motor(ejecutar=None):
    """Prueba el motor en un proceso aparte y apunta el resultado. Devuelve True si funciona. Tarda: no llamar desde el hilo del juego."""
    ejecutar = ejecutar or _ejecutar_prueba
    t0 = time.time()
    try:
        codigo = ejecutar(orden_prueba(), TIEMPO_PRUEBA)
    except Exception as e:                           # ni siquiera se pudo lanzar el proceso
        registro.una_vez("vozgen", "No se pudo lanzar la prueba del motor de voz", error=type(e).__name__)
        _estado.update(ok=False, motivo=tr("El generador de voces no se ha podido probar en este equipo.") + SE_REPETIRA)
        return False                                 # no se apunta: puede ser pasajero, se intentará la próxima vez
    ok = codigo == 0
    texto = _motivo_de(codigo)
    guardar_recuerdo(ok, texto, -1 if codigo is None else codigo)
    (registro.info if ok else registro.aviso)("vozgen", tr("Prueba del motor de voz en un proceso aparte"), resultado="bien" if ok else "mal",
                                              codigo=tr("sin terminar") if codigo is None else hex(codigo & 0xFFFFFFFF), segundos=round(time.time() - t0, 1))
    _estado.update(ok=ok, motivo="" if ok else texto + SE_REPETIRA)
    return ok


def _hilo_prueba(ejecutar=None):
    try:
        probar_motor(ejecutar)
    finally:
        with _cerrojo:
            _prueba["hilo"] = None
            avisar, _prueba["al_saber"] = _prueba["al_saber"], []
        for f in avisar:                             # quien preguntó mientras se probaba, ya puede seguir
            try:
                f(bool(_estado["ok"]))
            except Exception:
                registro.excepcion("vozgen", "Fallo al seguir tras la prueba del motor de voz")


def probando():
    return _prueba["hilo"] is not None


def cuando_se_sepa(f):
    """Llama a f(funciona) en cuanto se sepa si el motor vale. Si ya se sabe, ahora mismo."""
    with _cerrojo:
        if _prueba["hilo"] is not None:
            _prueba["al_saber"].append(f)
            return
    if _estado["ok"] is not None:
        f(bool(_estado["ok"]))


def parar_prueba():
    """Al cerrar el juego o antes de actualizarlo: el proceso de prueba no puede quedarse abierto, que es el propio programa."""
    proc = _prueba["proc"]
    with _cerrojo:
        _prueba["al_saber"] = []
    if proc is not None:
        try:
            proc.kill()
        except Exception:
            pass


def disponible(esperar=False, ejecutar=None):
    """¿Se pueden generar voces en este equipo? Lo que se puede saber al momento, se dice al momento y se recuerda. Si hay
    que probar el motor, se prueba en segundo plano y mientras tanto la respuesta es que no (con `esperar`, se aguarda al resultado)."""
    if _estado["ok"] is None and not probando():
        c = carpeta_motor()
        caps = capacidades()
        faltan = [n for n in NECESARIAS if caps[n] is False]
        rec = None
        if any(not os.path.exists(os.path.join(c, n)) for n in ARCHIVOS_MOTOR):
            _estado.update(ok=False, motivo=tr("Esta copia del juego no trae el generador de voces."))
        elif idioma() is None:
            _estado.update(ok=False, motivo=tr("El generador de voces aún no tiene voces en este idioma."))
        elif faltan:
            _estado.update(ok=False, motivo=tr("El procesador de este equipo no puede con el generador de voces: le falta ") + tr(" y ").join(faltan) + ".")
            registro.una_vez("vozgen", "El procesador no tiene lo que pide el motor de voz", faltan=", ".join(faltan))
        else:
            rec = leer_recuerdo()
            if rec is None:                           # nunca se ha probado con esta versión: a probarlo, aparte
                with _cerrojo:
                    _prueba["hilo"] = hilo_con_pila(_hilo_prueba, "voz-comprobar", (ejecutar,))
            elif rec["ok"] and int(rec.get("a_medias", 0)) >= 2:
                _estado.update(ok=False, motivo=tr("Las dos últimas veces, el juego se cerró mientras cargaba el generador de voces, así que se ha desactivado en este equipo.") + SE_REPETIRA)
                registro.una_vez("vozgen", "Motor de voz desactivado: el juego se cerró dos veces mientras lo cargaba")
            else:
                _estado.update(ok=rec["ok"], motivo="" if rec["ok"] else str(rec.get("motivo", "")) + SE_REPETIRA)
    hilo = _prueba["hilo"]
    if esperar and hilo is not None:
        hilo.join()
    return bool(_estado["ok"])


def motivo():
    disponible()
    return PROBANDO if probando() else _estado["motivo"]


def _carga_a_medias(delta):
    """Apunta que el juego va a cargar el motor (delta 1) o que ya lo ha cargado y ha generado (delta 0: a cero). Si el
    juego se cierra de golpe entre una cosa y otra, queda apuntado, y a la segunda no se vuelve a intentar."""
    rec = leer_recuerdo()
    if rec is None or not rec["ok"]:
        return
    n = int(rec.get("a_medias", 0)) + 1 if delta else 0
    if n != int(rec.get("a_medias", 0)):
        guardar_recuerdo(True, "", 0, n)


def reparto():
    cod = idioma() or "es"
    try:
        with open(os.path.join(carpeta_motor(), "reparto.json" if cod == "es" else f"reparto_{cod}.json"), encoding="utf-8") as f:
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
        if (idioma() or "es") != "es":                    # cada idioma, sus frases aparte
            t += "|" + idioma()
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
                if quien == PROTA:
                    voz = rep["protagonista"].get(f"{pj.voz}_{pj.genero}")
                else:                                           # en otro idioma el nombre viene traducido: el reparto va por el español
                    from . import i18n
                    voz = rep["personajes"].get(quien) or rep["personajes"].get(i18n.original(quien))
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
            self.hilo = hilo_con_pila(self._correr, "voces")
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
            _carga_a_medias(1)                        # si el juego se cierra de golpe aquí dentro, queda apuntado
            import ptts
            self._hilos_puestos = None
            self._tts = ptts.TTS(carpeta_motor(), lang=idioma() or "es", quant="q8")
            self._voces = set()
            self._estrenado = False
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
            tts.add_voice(voz, os.path.join(carpeta_voces_motor(), voz + ".safetensors"))
            self._voces.add(voz)
        mejor = None
        for semilla in (7, 23, 51):                               # si sale con un ritmo raro es que se ha comido algo o ha metido ruido: otra vez
            pcm = _limpio(tts.synth(para_decir(texto), voice=voz, seed=semilla), tts.sample_rate)
            ritmo = len(texto) / max(0.1, len(pcm) / tts.sample_rate)
            if not getattr(self, "_estrenado", True):                 # ha cargado y ha generado: el motor va bien dentro del juego
                self._estrenado = True
                _carga_a_medias(0)
            if mejor is None:
                mejor = pcm
            if 7 <= ritmo <= 26:
                return pcm, tts.sample_rate
        return mejor, tts.sample_rate

    def _guardar(self, f):
        pcm, sr = self.sintetizar(f[1], f[2])
        os.makedirs(os.path.dirname(f[0]), exist_ok=True)
        tmp = f[0] + ".tmp"
        escribir_ogg(tmp, pcm, sr)
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
    pj, misiones = Personaje.de_jugador(p.j), p.datos.get("misiones", [])
    n = generador.pedir(pj, misiones, primero)
    if not n and probando():                         # el motor se está probando aparte: en cuanto se sepa que vale, se empieza
        cuando_se_sepa(lambda ok: ok and generador.permitido() and generador.pedir(pj, misiones, primero))
    return n


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
        self.app.decir(tr("Preparando las voces de tu personaje, para que en la historia te llamen por tu nombre. Solo pasa la primera vez. "
                       "Es cosa de unos segundos; pulsa Escape si prefieres empezar ya."), True)

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
            self.app.decir(tr('{hechas} de {meta}.').format(hechas=(generador.hechas), meta=(self.meta)))

    def tecla(self, ev):
        import pygame
        if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.app.decir(tr("Empiezas ya. Lo que falte se irá preparando mientras juegas."), True)
            self._fin()
        elif ev.key in (pygame.K_F1, pygame.K_UP):
            self.app.decir(tr('Preparando las voces de tu personaje: {hechas} de {meta}. Escape para empezar ya.').format(hechas=(generador.hechas), meta=(self.meta)), True)


def probar(app, voz, texto, al_terminar=None):
    """Genera una frase suelta y la hace sonar: para oír cómo queda el nombre antes de empezar. No bloquea el juego."""
    if not disponible():
        app.son("menu_borde" if probando() else "error")
        app.decir(motivo(), True)
        return False
    app.decir(tr("Un momento."), True)

    def tarea():
        try:
            g = Generador()
            g.hilos_motor = max(2, (os.cpu_count() or 4) // 2)
            pcm, sr = g.sintetizar(voz, texto)
            os.makedirs(carpeta_generadas(), exist_ok=True)
            ruta = os.path.join(carpeta_generadas(), "prueba.ogg")
            escribir_ogg(ruta, pcm, sr)
            app.voz_prueba = ruta                    # la recoge el menú en su siguiente fotograma
        except Exception as e:
            registro.una_vez("vozgen", "La prueba de voz no salió", error=type(e).__name__)
            app.voz_prueba = False
    hilo_con_pila(tarea, "voz-prueba")
    return True
