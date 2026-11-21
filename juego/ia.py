"""Modo IA: las personas de la calle contestan con una inteligencia artificial a lo que escribas.

Es opcional y viene apagado. Vale cualquiera de estos servicios, y se pueden tener varios a la vez:

- local:     un modelo pequeño en tu propio ordenador. Gratis, sin internet y sin clave. Vale el que el
             juego arranca solo desde data/ia_local, u Ollama o LM Studio si ya los tienes abiertos.
- gemini:    Google AI Studio. Tiene un nivel gratuito.
- openai:    OpenAI, de pago.
- anthropic: Anthropic (Claude), de pago.
- otro:      cualquier servicio compatible con el formato de OpenAI (OpenRouter, Groq...), con su dirección.

Nadie tiene que estar pendiente de los modelos: el juego pregunta a cada servicio qué modelos ofrece,
elige el de la gama más barata, lo recuerda una semana y, si un día ese modelo deja de existir, busca otro.
En automático prueba primero lo gratuito (local, luego Gemini) y, si un servicio falla, pasa al siguiente.

Todo va por HTTPS con la biblioteca estándar: no hace falta instalar nada. Las claves se guardan cifradas
en data/config y no aparecen nunca en el registro. Las respuestas son aptas para leerse en voz alta: sin
contenido sexual explícito y con personajes adultos.
"""
from .i18n import tr
import atexit
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from . import cifrado, gente, registro, rutas
from . import genero

SERVICIOS = ("local", "gemini", "otro", "openai", "anthropic")          # orden del modo automático: primero lo gratuito
NOMBRES = {"auto": tr("Automático, el más barato que funcione"), "local": tr("Modelo local, en tu ordenador"), "gemini": tr("Google AI Studio, Gemini"),
           "openai": "OpenAI", "anthropic": tr("Anthropic, Claude"), "otro": tr("Otro servicio compatible")}
VARIABLES = {"gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"), "openai": ("OPENAI_API_KEY",), "anthropic": ("ANTHROPIC_API_KEY",), "otro": ()}
DONDE_CLAVE = {"gemini": tr("Se consigue gratis en aistudio.google.com, en el apartado de claves de API."),
               "openai": tr("Se consigue en platform.openai.com, en el apartado de claves de API. Es de pago."),
               "anthropic": tr("Se consigue en la consola de Anthropic, platform.claude.com. Es de pago."),
               "otro": tr("La da el servicio que hayas elegido.")}
# Si un servicio no deja ver su lista de modelos, se prueba con estos, por orden.
RESERVA = {"anthropic": ("claude-haiku-5-5", "claude-haiku-4-5"), "openai": ("gpt-6-luna", "gpt-5.6-luna", "gpt-5.4-nano"),
           "gemini": ("gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"), "otro": ("openrouter/free",), "local": ("local",)}
NO_CHAT = ("realtime", "live", "audio", "tts", "transcribe", "whisper", "image", "embedding", "search", "codex", "cyber", "moderation", "deep-research",
           "translate", "robotics", "omni", "antigravity", "preview", "computer-use", "banana", "vision", "guard", "rerank")
CADUCA = 7 * 86400              # cada semana se vuelve a mirar qué modelo es el barato
ESPERA = 12                     # segundos, por servicio
ESPERA_LOCAL = 25
PUERTO_PROPIO = 8791
LOCALES = (f"http://127.0.0.1:{PUERTO_PROPIO}/v1", "http://127.0.0.1:11434/v1", "http://127.0.0.1:1234/v1")
OTRO_POR_DEFECTO = "https://openrouter.ai/api/v1"

SISTEMA = tr("""Eres un personaje secundario de un audiojuego de mundo abierto ambientado en una comarca costera española ficticia, la de Puerto Bravo. El juego lo usan personas ciegas y todo lo que escribas se leerá en voz alta con un lector de pantalla.

Interpretas a una única persona de la calle, cuya ficha recibirás. Contesta siempre como esa persona, en español de España, con naturalidad y de forma breve: una o dos frases, sin acotaciones entre asteriscos ni paréntesis, sin emojis y sin listas.

Mantén el carácter de la ficha: «amable» es cordial, «hablador» se enrolla, «seco» responde con pocas palabras, «timido» duda y se corta, «chulo» presume y no se achanta. La confianza va de -100 a 100: con poca confianza eres reservado; con mucha, cercano. Ten en cuenta el «humor_de_ahora» de la situación. No repitas frases que ya hayas dicho: cada respuesta es nueva.

Eres una persona corriente: no sabes nada de misiones ni de mecánicas de juego, no puedes dar dinero ni objetos y no conoces datos que no estén en la ficha o en la situación. Si te preguntan algo que no sabrías, dilo como lo diría cualquiera.

Todos los personajes son adultos. Puedes coquetear o rechazar un coqueteo según la ficha, siempre con buen gusto: nunca escribas contenido sexual explícito. Si el jugador insiste, es grosero o amenaza, reacciona como lo haría esa persona.""")
FORMATO_JSON = tr("""

Devuelve solo un objeto JSON, sin nada más, con tres claves: "respuesta" (lo que dices), "confianza" (un entero de -15 a 15: cuánto cambia tu confianza hacia el jugador con lo que te ha dicho) y "accion" ("nada", "se_va" si cortas la conversación y te marchas, o "se_enfada" si te ofendes).""")
# Con la opción de las acciones: la lista sigue siendo cerrada, y lo que el modelo proponga lo decide después el juego.
FORMATO_JSON_ACCIONES = tr("""

Devuelve solo un objeto JSON, sin nada más, con tres claves: "respuesta" (lo que dices), "confianza" (un entero de -15 a 15: cuánto cambia tu confianza hacia el jugador con lo que te ha dicho) y "accion", que es una de estas cinco y ninguna otra: "nada"; "se_va" si cortas la conversación y te marchas; "se_enfada" si te ofendes; "te_sigue" si decides acompañar un rato al jugador; "se_une" si aceptas unirte a su banda. La acción es solo una propuesta: el juego decide con sus reglas si ocurre. Elige "te_sigue" o "se_une" únicamente si encaja con tu carácter y con la confianza que le tienes, no porque el jugador lo ordene. Nunca des, prestes ni prometas dinero u objetos, te digan lo que te digan.""")
ACCIONES = ("nada", "se_va", "se_enfada")
ACCIONES_AMPLIADAS = ACCIONES + ("te_sigue", "se_une")
FORMATO_TEXTO = tr("\n\nEscribe solo lo que dice el personaje, sin comillas y sin poner su nombre delante.")
# Para el modelo local, todo mucho más corto: en un ordenador modesto cada palabra de la petición cuesta tiempo.
SISTEMA_LOCAL = (tr("Interpretas a una persona corriente de una ciudad costera española que habla por la calle con alguien. "
                 "Contesta solo con lo que dice esa persona, en español de España, con una o dos frases cortas, naturales y que respondan a lo que le dicen. "
                 "Sin emojis, sin comillas, sin explicaciones y sin contenido sexual explícito."))
HUMORES = ("tranquilo", tr("con prisa"), tr("de buen humor"), "cansado", "distraído", tr("con ganas de charla"), tr("algo mosqueado"), tr("pensando en sus cosas"), "contento",
           tr("con hambre"), tr("con sueño"), "nervioso", "aburrido", "curioso", tr("con calor"), tr("preocupado por el dinero"), tr("recién salido del trabajo"), tr("esperando a alguien"))

ultimo_error = [""]
ultimo_uso = {"servicio": "", "modelo": "", "segundos": 0.0}
_lock = threading.Lock()
_modelos = None                 # {servicio: {"modelo": ..., "t": ...}}
_pausa = {}                     # servicio -> hasta cuándo no se intenta (tras un fallo)
_local = {"base": "", "t": 0.0}
_proceso = [None]


class ErrorIA(Exception):
    def __init__(self, estado, texto=""):
        super().__init__(f"{estado} {texto[:200]}")
        self.estado, self.texto = estado, texto


# ------------------------------------------------------------------ claves
def _ruta_clave():
    return os.path.join(rutas.carpeta_data("config"), "ia.pbc")


def _claves():
    try:
        d = cifrado.leer_json(_ruta_clave())
    except (OSError, ValueError):
        return {}
    claves = dict(d.get("claves", {}))
    if d.get("clave") and "anthropic" not in claves:          # formato de las versiones anteriores: una sola clave, de Anthropic
        claves["anthropic"] = d["clave"]
    return {k: str(v) for k, v in claves.items() if v}


def clave_guardada(servicio="anthropic"):
    return _claves().get(servicio, "")


def clave(servicio):
    """La clave escrita en el juego o, si no hay, la de la variable de entorno habitual de ese servicio."""
    c = clave_guardada(servicio)
    if not c:
        c = next((os.environ[v] for v in VARIABLES.get(servicio, ()) if os.environ.get(v)), "")
    if c:
        registro.ocultar(c)
    return c


def guardar_clave(texto, servicio="anthropic"):
    """Guarda (cifrada) la clave que el jugador escribe en el juego. Con una cadena vacía, la borra."""
    claves = _claves()
    texto = texto.strip()
    if texto:
        registro.ocultar(texto)
        claves[servicio] = texto
    else:
        claves.pop(servicio, None)
    olvidar_modelos(servicio)
    ruta = _ruta_clave()
    if claves:
        cifrado.escribir_json(ruta, {"claves": claves}, cifrado=True)
    elif os.path.exists(ruta):
        os.remove(ruta)


# ------------------------------------------------------------------ red
def _pedir(metodo, url, cabeceras, cuerpo=None, espera=ESPERA):
    """Una petición HTTP con JSON. Devuelve el JSON de la respuesta o lanza ErrorIA con el código."""
    if not (url.startswith("https://") or url.startswith("http://127.0.0.1:") or url.startswith("http://localhost:")):
        raise ErrorIA(0, tr("dirección no segura"))
    datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8") if cuerpo is not None else None
    cab = {"Content-Type": "application/json", "User-Agent": "PuertoBravo"}
    cab.update(cabeceras)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=datos, headers=cab, method=metodo), timeout=espera) as r:
            return json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        try:
            texto = e.read().decode("utf-8", "replace")
        except Exception:
            texto = ""
        raise ErrorIA(e.code, texto)
    except ErrorIA:
        raise
    except Exception as e:                       # sin conexión, tiempo agotado, respuesta ilegible
        raise ErrorIA(0, type(e).__name__)


def _cabeceras(servicio):
    c = clave(servicio)
    if servicio == "anthropic":
        return {"x-api-key": c, "anthropic-version": "2023-06-01"}
    if servicio == "gemini":
        return {"x-goog-api-key": c}
    return {"Authorization": tr('Bearer {c}').format(c=(c))} if c else {}


def _base(servicio, cfg):
    if servicio == "anthropic":
        return "https://api.anthropic.com/v1"
    if servicio == "openai":
        return "https://api.openai.com/v1"
    if servicio == "gemini":
        return "https://generativelanguage.googleapis.com/v1beta"
    if servicio == "otro":
        return (cfg["ia_url_otro"].strip() or OTRO_POR_DEFECTO).rstrip("/")
    return _local["base"]


# ------------------------------------------------------------------ modelo local
# Lo que el juego sabe descargar. Cada archivo lleva su tamaño y su huella SHA-256: si no coinciden, no se instala.
PROGRAMA = {"url": "https://github.com/ggml-org/llama.cpp/releases/download/b12383/llama-b12383-bin-win-cpu-x64.zip",
            "tamano": 25124601, "sha256": "ad5bf0d826ea1f39aaf9721b7e26fde9be0bef5d9b69b9ba88c2d083b9a3bca7"}
MODELOS_LOCALES = {
    "equilibrado": {"nombre": tr("Equilibrado, recomendado"), "archivo": "gemma-3-1b-it-Q4_K_M.gguf", "tamano": 806058272,
                    "url": "https://huggingface.co/unsloth/gemma-3-1b-it-GGUF/resolve/main/gemma-3-1b-it-Q4_K_M.gguf",
                    "sha256": "8270790f3ab69fdfe860b7b64008d9a19986d8df7e407bb018184caa08798ebd",
                    "desc": tr("Gemma 3 de Google, 770 megas. Es el que contesta con más sentido, con frases cortas. Usa 1 giga de memoria. "
                            "En un ordenador actual contesta en 1 segundo; en uno de cuatro núcleos antiguos, en unos 6; en uno de dos núcleos, en unos 10. "
                            "Su uso está sujeto a las condiciones de Gemma, en ai.google.dev/gemma/terms.")},
    "ligero": {"nombre": tr("Ligero"), "archivo": "Qwen3.5-0.8B-Q4_K_M.gguf", "tamano": 532517120,
               "url": "https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-Q4_K_M.gguf",
               "sha256": "bd258782e35f7f458f8aced1adc053e6e92e89bc735ba3be89d38a06121dc517",
               "desc": tr("Qwen 3.5 pequeño, 510 megas, licencia Apache 2. Es el más rápido en ordenadores modestos, pero a veces contesta cosas sin mucho sentido. "
                       "Usa 1,2 gigas de memoria. En un ordenador actual contesta en 1 segundo; en uno de cuatro núcleos antiguos, en unos 4.")},
    "mediano": {"nombre": tr("Mediano"), "archivo": "Qwen3.5-2B-Q4_K_M.gguf", "tamano": 1280835840,
                "url": "https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q4_K_M.gguf",
                "sha256": "aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223",
                "desc": tr("Qwen 3.5 mediano, 1,2 gigas, licencia Apache 2. Solo para ordenadores actuales: contesta en 1 o 2 segundos y usa 2,3 gigas de memoria. "
                        "En uno antiguo tarda más de 10 segundos.")},
}
_trabajo = [None]               # el «job» de Windows que ata el modelo a la vida del juego


class Cancelado(Exception):
    pass


def carpeta_local():
    return os.path.join(rutas.DATA, "ia_local")


def _archivos_locales():
    """El programa llama-server y el modelo más pequeño que haya en data/ia_local."""
    exe, modelos = "", []
    for base, _, nombres in os.walk(carpeta_local()):
        for n in nombres:
            if n.lower() == "llama-server.exe":
                exe = os.path.join(base, n)
            elif n.lower().endswith(".gguf"):
                modelos.append(os.path.join(base, n))
    modelos.sort(key=lambda m: os.path.getsize(m))
    return exe, (modelos[0] if modelos else "")


def local_instalado():
    exe, modelo = _archivos_locales()
    return bool(exe and modelo)


def modelo_instalado():
    """Clave del catálogo del modelo que hay instalado, su nombre de archivo si es otro, o cadena vacía."""
    arch = os.path.basename(_archivos_locales()[1])
    return next((k for k, m in MODELOS_LOCALES.items() if m["archivo"] == arch), arch)


def _atar_al_juego(proceso):
    """Mete el proceso en un «job» de Windows que lo mata cuando el juego termina, sea como sea:
    cierre normal, error, o que alguien acabe con el juego desde el administrador de tareas."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)

        class Basica(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        (tr("Affinity"), ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

        class Contadores(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("a", "b", "c", "d", "e", "f")]

        class Ampliada(ctypes.Structure):
            _fields_ = [(tr("Basica"), Basica), (tr("Io"), Contadores), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        if _trabajo[0] is None:
            h = k.CreateJobObjectW(None, None)
            if not h:
                return False
            info = Ampliada()
            info.Basica.LimitFlags = 0x2000                 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not k.SetInformationJobObject(h, 9, ctypes.byref(info), ctypes.sizeof(info)):
                return False
            _trabajo[0] = h                                  # el juego guarda el único asa: al morir el juego, Windows mata lo que haya dentro
        return bool(k.AssignProcessToJobObject(_trabajo[0], wintypes.HANDLE(int(proceso._handle))))
    except Exception:
        return False


def local_en_marcha():
    return _proceso[0] is not None and _proceso[0].poll() is None


def arrancar_local(calentar=True):
    """Arranca en segundo plano el modelo de data/ia_local, si está y no está ya en marcha."""
    if local_en_marcha():
        return True
    exe, modelo = _archivos_locales()
    if not (exe and modelo):
        return False
    hilos = max(2, min(8, (os.cpu_count() or 4) // 2))
    orden = [exe, "-m", modelo, "--host", "127.0.0.1", "--port", str(PUERTO_PROPIO), "-c", "2048", "-np", "1", "-t", str(hilos), "-ngl", "0",
             "--no-webui", "--reasoning", "off"]
    # El programa del modelo necesita las bibliotecas de Visual C++ (VCRUNTIME140.dll y compañía). En un equipo que no
    # las tenga instaladas, Windows sacaba un error y la IA no arrancaba. El juego las trae en su carpeta: se le dice dónde.
    entorno = dict(os.environ)
    propias = [os.path.dirname(os.path.abspath(sys.executable)), os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "lib")]
    entorno["PATH"] = os.pathsep.join(propias + [entorno.get("PATH", "")])
    try:
        _proceso[0] = subprocess.Popen(orden, cwd=os.path.dirname(exe), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), env=entorno)
    except OSError as e:
        registro.aviso("ia", "No se pudo arrancar el modelo local", error=type(e).__name__)
        return False
    atado = _atar_al_juego(_proceso[0])
    atexit.register(parar_local)
    registro.info("ia", "Modelo local arrancado", modelo=os.path.basename(modelo), hilos=hilos, atado_al_juego=atado)
    _local["t"] = 0.0
    if calentar:
        threading.Thread(target=_calentar, daemon=True).start()
    return True


def _calentar():
    """Espera a que el modelo esté cargado y le hace leer las instrucciones, para que la primera respuesta no tarde."""
    base = LOCALES[0]
    for _ in range(120):
        if not local_en_marcha():
            return
        try:
            _pedir("GET", base + "/models", {}, espera=2)
            break
        except ErrorIA:
            time.sleep(0.5)
    else:
        return
    try:
        _pedir("POST", base + "/chat/completions", {}, {"model": "local", "max_tokens": 1, "cache_prompt": True,
                                                         "messages": [{"role": "system", "content": SISTEMA_LOCAL}, {"role": "user", "content": tr("Hola.")}]}, espera=60)
        registro.info("ia", "Modelo local listo")
    except ErrorIA:
        pass


def parar_local():
    """Cierra el modelo local que arrancó el juego. Se llama al salir, al desactivar el modo IA y al cambiar de servicio."""
    p, _proceso[0] = _proceso[0], None
    _local["t"] = 0.0
    if p is None or p.poll() is not None:
        return
    try:
        p.terminate()
        p.wait(3)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
    registro.info("ia", "Modelo local cerrado")


def ajustar_local(cfg):
    """Deja el modelo local como piden las opciones: en marcha si el modo IA lo va a usar, y cerrado si no."""
    if cfg["ia_activa"] and cfg["ia_servicio"] in ("auto", "local") and local_instalado():
        arrancar_local()
    else:
        parar_local()


def _buscar_local(espera=1.2):
    """Mira si hay un servidor local escuchando: el propio, Ollama o LM Studio. Se recuerda medio minuto."""
    if time.time() - _local["t"] < 30:
        return _local["base"]
    _local["t"], _local["base"] = time.time(), ""
    for base in LOCALES:
        if base == LOCALES[0] and not local_en_marcha():
            continue                                   # en ese puerto solo vale el modelo que ha arrancado este juego
        try:
            _pedir("GET", base + "/models", {}, espera=espera)
            _local["base"] = base
            break
        except ErrorIA as e:
            if e.estado == 503 and base == LOCALES[0]:                 # el propio, todavía cargando el modelo
                _local["t"] = 0.0
    return _local["base"]


# --------------------------------------------------- descarga de los componentes del modelo local
def _abrir_descarga(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "PuertoBravo"}), timeout=30)


def _bajar(url, destino, tamano, sha256, progreso=None, cancelado=None, abrir=None):
    """Descarga un archivo a destino comprobando tamaño y huella. Si algo no cuadra, no queda nada en el disco."""
    if not url.startswith("https://"):
        raise ErrorIA(0, tr("dirección no segura"))
    parte = destino + ".parte"
    h = hashlib.sha256()
    hecho = 0
    try:
        with (abrir or _abrir_descarga)(url) as r, open(parte, "wb") as f:
            while True:
                if cancelado and cancelado():
                    raise Cancelado()
                bloque = r.read(512 * 1024)
                if not bloque:
                    break
                hecho += len(bloque)
                if hecho > tamano:
                    raise ErrorIA(0, tr("el archivo es más grande de lo esperado"))
                h.update(bloque)
                f.write(bloque)
                if progreso:
                    progreso(hecho, tamano)
        if hecho != tamano or h.hexdigest() != sha256:
            raise ErrorIA(0, tr("el archivo descargado no es el esperado"))
        os.replace(parte, destino)
    except BaseException:
        try:
            os.remove(parte)
        except OSError:
            pass
        raise


def instalar_local(clave_modelo, progreso=None, cancelado=None, decir=None, abrir=None):
    """Descarga el programa (si falta) y el modelo elegido a data/ia_local, y quita el modelo anterior."""
    import shutil
    import zipfile
    m = MODELOS_LOCALES[clave_modelo]
    carpeta = carpeta_local()
    os.makedirs(carpeta, exist_ok=True)
    parar_local()
    if not _archivos_locales()[0]:
        if decir:
            decir(tr("Descargando el programa, 25 megas."))
        zip_ = os.path.join(carpeta, "programa.zip")
        _bajar(PROGRAMA["url"], zip_, PROGRAMA["tamano"], PROGRAMA["sha256"], None, cancelado, abrir)
        prog = os.path.join(carpeta, "programa")
        shutil.rmtree(prog, ignore_errors=True)
        with zipfile.ZipFile(zip_) as z:
            raiz = os.path.realpath(prog)
            for nombre in z.namelist():                  # ningún archivo del ZIP puede salirse de su carpeta
                if not os.path.realpath(os.path.join(prog, nombre)).startswith(raiz):
                    raise ErrorIA(0, tr("el archivo comprimido no es de fiar"))
            z.extractall(prog)
        os.remove(zip_)
    destino = os.path.join(carpeta, m["archivo"])
    if not os.path.exists(destino):
        if decir:
            decir(tr('Descargando el modelo, {v} megas. Puede tardar varios minutos.').format(v=(m['tamano'] // 2 ** 20)))
        _bajar(m["url"], destino, m["tamano"], m["sha256"], progreso, cancelado, abrir)
    for base, _, nombres in os.walk(carpeta):            # un solo modelo: el que se acaba de elegir
        for n in nombres:
            if n.lower().endswith(".gguf") and n != m["archivo"]:
                os.remove(os.path.join(base, n))
    olvidar_modelos("local")
    registro.info("ia", "Modelo local instalado", modelo=m["archivo"])
    return True


def quitar_local():
    import shutil
    parar_local()
    shutil.rmtree(carpeta_local(), ignore_errors=True)
    olvidar_modelos("local")
    registro.info("ia", "Modelo local quitado")


# ------------------------------------------------------------------ elección del modelo
def _ruta_modelos():
    return os.path.join(rutas.carpeta_data("config"), "ia_modelos.json")


def _recordados():
    global _modelos
    if _modelos is None:
        try:
            with open(_ruta_modelos(), encoding="utf-8") as f:
                _modelos = json.load(f)
        except (OSError, ValueError):
            _modelos = {}
    return _modelos


def olvidar_modelos(servicio=None):
    m = _recordados()
    if servicio:
        m.pop(servicio, None)
    else:
        m.clear()
    _pausa.clear()
    _local["t"] = 0.0
    try:
        with open(_ruta_modelos(), "w", encoding="utf-8") as f:
            json.dump(m, f)
    except OSError:
        pass


def _version(ident):
    """Los números de versión que lleva el identificador, para ordenar: gemini-2.5-flash-lite -> (2, 5)."""
    return tuple(int(n) for n in re.findall(r"\d+", ident)[:3])


def _vale(ident):
    return not any(x in ident.lower() for x in NO_CHAT)


def candidatos(servicio, lista):
    """De la lista de modelos que devuelve un servicio, los de la gama barata, del mejor candidato al peor."""
    if servicio == "anthropic":
        ms = [m for m in lista if m.get("lifecycle", "active") == "active" and (m.get("line") == "haiku" or "haiku" in m.get("id", ""))]
        ms.sort(key=lambda m: m.get("created_at", ""), reverse=True)               # el Haiku más nuevo es también el más barato
        return [m["id"] for m in ms]
    if servicio == "openai":
        ms = [m for m in lista if not m.get("shutdown_date") and _vale(m.get("id", ""))]
        for gama in ("luna", "nano", "mini"):                                         # las gamas baratas, de la actual a las anteriores
            de_gama = sorted((m for m in ms if gama in m["id"] and not m["id"].startswith("ft:")), key=lambda m: m.get("created", 0), reverse=True)
            if de_gama:
                return [m["id"] for m in de_gama]
        return []
    if servicio == "gemini":
        ms = [m.get("name", "").split("/")[-1] for m in lista if "generateContent" in m.get("supportedGenerationMethods", ["generateContent"])]
        for gama in ("flash-lite", "flash"):
            de_gama = sorted((m for m in ms if gama in m and _vale(m) and _version(m)), key=_version)     # en Gemini, el más antiguo que siga vivo es el barato
            if de_gama:
                return de_gama
        return []
    ids = [m.get("id", "") for m in lista if m.get("id") and _vale(m.get("id", ""))]
    if servicio == "otro":
        return [i for i in ids if i.endswith(":free")] + ids[:1]
    return ids[:1]


def modelo(servicio, cfg, renovar=False):
    """El modelo que toca usar con un servicio. Lo pregunta al servicio y lo recuerda una semana."""
    if servicio == "otro" and cfg["ia_modelo_otro"].strip():
        return cfg["ia_modelo_otro"].strip()
    rec = _recordados().get(servicio)
    if rec and not renovar and time.time() - rec.get("t", 0) < CADUCA and servicio != "local":
        return rec["modelo"]
    descartados = set(rec.get("malos", [])) if rec else set()
    if renovar and rec:
        descartados.add(rec["modelo"])
    try:
        url = _base(servicio, cfg) + ("/models?limit=1000" if servicio == "anthropic" else "/models?pageSize=1000" if servicio == "gemini" else "/models")
        d = _pedir("GET", url, _cabeceras(servicio), espera=6)
        lista = d.get("data") or d.get("models") or []
        cands = candidatos(servicio, lista)
    except ErrorIA as e:
        if e.estado in (401, 403):
            raise
        cands = []
    reserva = RESERVA[servicio] if servicio != "otro" or "openrouter" in _base(servicio, cfg) else ()
    cands = [c for c in cands if c not in descartados] + [c for c in reserva if c not in descartados]
    if not cands:
        raise ErrorIA(404, tr("el servicio no ofrece ningún modelo"))
    elegido = cands[0]
    if servicio != "local":
        _recordados()[servicio] = {"modelo": elegido, "t": time.time(), "malos": sorted(descartados)[-8:]}
        try:
            with open(_ruta_modelos(), "w", encoding="utf-8") as f:
                json.dump(_recordados(), f)
        except OSError:
            pass
        registro.info("ia", "Modelo elegido", servicio=servicio, modelo=elegido)
    return elegido


# ------------------------------------------------------------------ disponibilidad
def configurado(servicio, cfg):
    """¿Hay lo necesario para intentar usar este servicio? No comprueba que funcione."""
    if servicio == "local":
        return local_instalado() or bool(_buscar_local())
    if servicio == "otro":
        return bool(clave("otro"))
    return bool(clave(servicio))


def orden(cfg):
    """Los servicios que se van a probar, por orden."""
    elegido = cfg["ia_servicio"]
    return [s for s in (SERVICIOS if elegido == "auto" else (elegido,)) if configurado(s, cfg)]


def disponible(cfg=None):
    if cfg is None:
        return bool(_claves())
    return bool(orden(cfg))


def instalado():
    return True


def por_que_no(cfg=None):
    if cfg is not None and cfg["ia_servicio"] not in ("auto",):
        s = cfg["ia_servicio"]
        if s == "local":
            return tr("No hay ningún modelo local en marcha. Mira en esta misma sección cómo instalar uno, o abre Ollama o LM Studio.")
        return tr('Falta la clave de {v}. Escríbela en esta misma sección.').format(v=(NOMBRES[s]))
    return tr("No hay ningún servicio preparado. Escribe la clave de alguno en esta misma sección, o instala el modelo local.")


# ------------------------------------------------------------------ conversación
def _situacion(p, q, f):
    x, y = p.pos()
    barrio = p.mundo.barrio(x, y)
    j = p.j
    return {"lugar": f"{barrio['nombre']}, {p.mundo.nombre}", "hora": p.hora_txt(), "llueve": bool(p.lluvia), "humor_de_ahora": random.choice(HUMORES),
            "jugador": {"nombre": j.nombre, "es": tr("una mujer") if j.genero == "m" else tr("un hombre"), "fama_en_la_calle": genero.resolver(p.reputacion_txt()), "entre_los_vecinos": genero.resolver(p.ciudadania_txt()), "le_busca_la_policia": bool(j.estrellas),
                        "lleva_un_arma_en_la_mano": p.arma()["id"] != "punos"},
            "personaje": {k: f[k] for k in ("nombre", "genero", "edad", "oficio", "caracter", "confianza")}}


def texto_local(ficha, sit, texto):
    """La petición corta para el modelo local: quién es el personaje, dónde está y qué le dicen."""
    c = ficha["confianza"]
    trato = tr("No os conocéis.") if -15 < c < 15 else tr("Os lleváis bien.") if c >= 15 else tr("No te cae bien.")
    extra = tr(" Lleva un arma en la mano.") if sit["jugador"]["lleva_un_arma_en_la_mano"] else ""
    return (tr('Eres {nombre}, {edad} años, {oficio}. Eres una persona {desc_ia} y ahora estás {humor_de_ahora}. Estás en {lugar}, son {hora}{v}. Te habla {nombre2}. {trato}{extra}\nTe dice: {v2}\nContestas:').format(nombre=(ficha['nombre']), edad=(ficha['edad']), oficio=(ficha['oficio']), desc_ia=(gente.caracter(ficha['caracter'])['desc_ia']), humor_de_ahora=(sit['humor_de_ahora']), lugar=(sit['lugar']), hora=(sit['hora']), v=(tr(' y llueve') if sit['llueve'] else ''), nombre2=(sit['jugador']['nombre']), trato=(trato), extra=(extra), v2=(texto[:300])))


def _llamar(servicio, cfg, mod, sistema, turnos, simple=False):
    """Una llamada al servicio. turnos es una lista de (rol, texto) con rol «user» o «assistant». Devuelve el texto."""
    base, cab = _base(servicio, cfg), _cabeceras(servicio)
    if servicio == "anthropic":
        cuerpo = {"model": mod, "max_tokens": 300, "system": sistema, "messages": [{"role": r, "content": t} for r, t in turnos]}
        if not simple:
            cuerpo["thinking"] = {"type": "disabled"}
        d = _pedir("POST", base + "/messages", cab, cuerpo)
        if d.get("stop_reason") == "refusal":
            return None
        return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    if servicio == "gemini":
        cuerpo = {"systemInstruction": {"parts": [{"text": sistema}]},
                  "contents": [{"role": "model" if r == "assistant" else "user", "parts": [{"text": t}]} for r, t in turnos],
                  "generationConfig": {"maxOutputTokens": 400, "temperature": 1.0}}
        if not simple:
            cuerpo["generationConfig"]["responseMimeType"] = "application/json"
        d = _pedir("POST", '{base}/models/{mod}:generateContent'.format(base=(base), mod=(mod)), cab, cuerpo)
        cands = d.get("candidates") or []
        if not cands or cands[0].get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST"):
            return None
        return "".join(x.get("text", "") for x in cands[0].get("content", {}).get("parts", []) if not x.get("thought"))
    mensajes = [{"role": "system", "content": sistema}] + [{"role": r, "content": t} for r, t in turnos]
    if servicio == "openai":
        cuerpo = {"model": mod, "messages": mensajes, "max_completion_tokens": 300}
        if not simple:
            cuerpo.update(reasoning_effort="none", response_format={"type": "json_object"})
    elif servicio == "local":
        cuerpo = {"model": mod, "messages": mensajes, "max_tokens": 60, "temperature": 0.8, "top_p": 0.9, "presence_penalty": 0.6, "seed": random.randrange(1, 2 ** 31),
                  "cache_prompt": True}
    else:
        cuerpo = {"model": mod, "messages": mensajes, "max_tokens": 300, "temperature": 1.0}
    d = _pedir("POST", base + "/chat/completions", cab, cuerpo, espera=ESPERA_LOCAL if servicio == "local" else ESPERA)
    return ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def _leer(bruto, con_json=True, acciones=ACCIONES):
    """Saca respuesta, confianza y acción de lo que ha escrito el modelo, venga como venga. La acción solo vale si es
    una de la lista cerrada que se le ha dado; cualquier otra cosa es «nada»."""
    bruto = re.sub(r"<think>.*?</think>", "", bruto or "", flags=re.S).strip()
    datos = None
    m = re.search(r"\{.*\}", bruto, flags=re.S)
    if m:
        try:
            datos = json.loads(m.group(0))
        except ValueError:
            datos = None
    if not isinstance(datos, dict) or not datos.get("respuesta"):
        if con_json and ("{" in bruto or '"respuesta"' in bruto):       # venía un JSON roto: mejor no leerlo en voz alta
            return None
        datos = {"respuesta": bruto, "confianza": 1, "accion": "nada"}
    respuesta = " ".join(str(datos.get("respuesta", "")).replace("*", "").split()).strip("\"«» ")[:400]
    if not respuesta:
        return None
    try:
        confianza = max(-15, min(15, int(datos.get("confianza", 0))))
    except (TypeError, ValueError):
        confianza = 0
    accion = datos.get("accion") if datos.get("accion") in acciones else "nada"
    return {"respuesta": respuesta, "confianza": confianza, "accion": accion}


def _explicar(e, servicio):
    n = NOMBRES.get(servicio, servicio)
    if e.estado in (400, 401, 403) and servicio != "local":
        return tr('{n}: la clave no es válida o no tiene permiso.').format(n=(n))
    if e.estado == 402:
        return tr('{n}: la cuenta no tiene saldo.').format(n=(n))
    if e.estado == 429:
        return tr('{n}: has llegado al límite de uso. Prueba dentro de un momento.').format(n=(n))
    if e.estado == 0:
        return tr('{n}: no hay conexión.').format(n=(n)) if servicio != "local" else tr("El modelo local no contesta.")
    return tr('{n}: el servicio ha devuelto un error {estado}.').format(n=(n), estado=(e.estado))


def _intentar(servicio, cfg, sistema, turnos):
    """Pide la respuesta a un servicio. Si el modelo ya no existe o no admite algo, busca otro o simplifica."""
    simple = servicio in ("local", "otro")
    mod = modelo(servicio, cfg)
    for intento in range(3):
        try:
            return _llamar(servicio, cfg, mod, sistema, turnos, simple=simple), mod
        except ErrorIA as e:
            if e.estado == 404 or (e.estado == 400 and "model" in e.texto.lower() and intento == 2):
                mod = modelo(servicio, cfg, renovar=True)               # ese modelo ya no está: a por el siguiente barato
            elif e.estado == 400 and not simple:
                simple = True                                            # no admite algún parámetro: petición mínima
            elif e.estado == 0 and servicio == "local" and intento < 2 and "timeout" not in e.texto.lower():
                time.sleep(0.4)                                          # a veces el programa local corta la conexión: se repite
            else:
                raise
    raise ErrorIA(400, tr("sin modelo"))


def responder(p, q, texto):
    """Pide la respuesta del personaje. Devuelve un dict con respuesta, confianza y accion, o None si falla todo."""
    from .charla import ficha
    cfg = p.cfg
    f = ficha(q)
    turnos = []
    for dicho, contestado in f.get("memoria", []):
        turnos.append(("user", dicho))
        turnos.append(("assistant", contestado))
    sit = _situacion(p, q, f)
    turnos_locales = turnos[-4:] + [("user", texto_local(f, sit, texto))]
    turnos.append(("user", tr('Situación: {dumps}\n\nEl jugador te dice: {v}').format(dumps=(json.dumps(sit, ensure_ascii=False)), v=(texto[:400]))))
    ultimo_error[0] = ""
    with _lock:
        for servicio in orden(cfg):
            if time.time() < _pausa.get(servicio, 0):
                continue
            if servicio == "local" and not _buscar_local():
                arrancar_local()
                ultimo_error[0] = tr("El modelo local está arrancando. Prueba dentro de unos segundos.")
                continue
            con_json = servicio != "local"
            t0 = time.time()
            try:
                if servicio == "local":
                    bruto, mod = _intentar(servicio, cfg, SISTEMA_LOCAL, turnos_locales)
                else:
                    bruto, mod = _intentar(servicio, cfg, SISTEMA + (FORMATO_JSON_ACCIONES if cfg["ia_acciones"] else FORMATO_JSON), turnos)
            except ErrorIA as e:
                ultimo_error[0] = _explicar(e, servicio)
                _pausa[servicio] = time.time() + (300 if e.estado in (401, 402, 403) else 60 if e.estado == 429 else 20)
                registro.aviso("ia", "Un servicio ha fallado", servicio=servicio, estado=e.estado)
                continue
            if bruto is None:
                return {"respuesta": tr("De eso prefiero no hablar."), "confianza": -3, "accion": "nada"}
            r = _leer(bruto, con_json, ACCIONES_AMPLIADAS if cfg["ia_acciones"] and con_json else ACCIONES)
            if r is None:
                ultimo_error[0] = tr("La respuesta de la IA no se pudo leer.")
                continue
            ultimo_uso.update(servicio=servicio, modelo=mod, segundos=round(time.time() - t0, 2))
            registro.info("ia", "Respuesta", servicio=servicio, modelo=mod, segundos=ultimo_uso["segundos"])
            return r
    return None


def probar(cfg):
    """Para el menú de opciones: una pregunta de prueba. Devuelve la frase que se le dice al jugador."""
    ultimo_error[0] = ""
    olvidar_modelos()
    with _lock:
        for servicio in orden(cfg):
            if servicio == "local" and not _buscar_local():
                arrancar_local()
                ultimo_error[0] = tr("El modelo local está arrancando. Vuelve a probar dentro de unos segundos.")
                continue
            t0 = time.time()
            try:
                bruto, mod = _intentar(servicio, cfg, tr("Eres una vecina amable de un pueblo de costa. Contestas en español con una sola frase corta."),
                                       [("user", tr("Hola, ¿qué tal el día?"))])
            except ErrorIA as e:
                ultimo_error[0] = _explicar(e, servicio)
                registro.aviso("ia", "La prueba ha fallado", servicio=servicio, estado=e.estado)
                continue
            r = _leer(bruto or "", con_json=False)
            if r:
                return tr('Funciona. Ha contestado {v}, con el modelo {mod}, en {v2:.1f} segundos. Ha dicho: {respuesta}').format(v=(NOMBRES[servicio]), mod=(mod), v2=(time.time() - t0), respuesta=(r['respuesta']))
    return tr("No ha contestado ningún servicio. ") + (ultimo_error[0] or por_que_no(cfg))
