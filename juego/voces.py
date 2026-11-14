"""Voces grabadas para las escenas: si hay una grabación de una frase, suena en lugar de la voz sintética.

Las grabaciones van en data/voces (o en una subcarpeta), en WAV, OGG, FLAC o MP3. Cada archivo se llama
como la misión, el número de paso y el número de frase, empezando en uno y separados por guion bajo:

    oc01_1_2.ogg      misión oc01, paso 1, frase 2

Sirve igual para las misiones del juego que para las de los mods. No hace falta grabarlas todas: las
frases sin archivo las sigue diciendo el lector de pantalla. El editor de mods escribe el guion completo
de un mod, con el nombre de archivo de cada frase, para repartirlo entre quienes vayan a grabar.
"""
import os

from . import registro, rutas

EXT = (".ogg", ".wav", ".flac", ".mp3")
SONIDO = "_voz_escena"            # nombre interno con el que se carga la grabación que suena
_indice = {"t": None, "archivos": {}}


def carpeta():
    """Donde el jugador o el autor de un mod dejan sus grabaciones. Las actualizaciones no la tocan."""
    return os.path.join(rutas.DATA, "voces")


def carpeta_de_serie():
    """Las voces que vienen con el juego. Si el jugador pone una grabación con el mismo nombre en su carpeta, gana la suya."""
    return os.path.join(rutas.DATA, "voces_serie")


def nombre(mision, paso, frase):
    """Nombre de archivo, sin extensión, de una frase: los números empiezan en uno."""
    return f"{mision}_{paso + 1}_{frase + 1}"


def _archivos():
    carpetas = [c for c in (carpeta(), carpeta_de_serie()) if os.path.isdir(c)]
    if not carpetas:
        return {}
    marca = tuple(max(os.path.getmtime(base) for base, _, _ in os.walk(c)) for c in carpetas)
    if _indice["t"] != marca:
        _indice["t"], _indice["archivos"] = marca, {}
        for c in carpetas:                                   # primero las del jugador: tienen preferencia
            for base, _, nombres in os.walk(c):
                for n in nombres:
                    raiz, ext = os.path.splitext(n)
                    if ext.lower() in EXT:
                        _indice["archivos"].setdefault(raiz.lower(), os.path.join(base, n))
    return _indice["archivos"]


def refrescar():
    _indice["t"] = None


def buscar(mision, paso, frase):
    return _archivos().get(nombre(mision, paso, frase).lower())


def de_paso(mision, paso, cuantas):
    """Lista con la grabación de cada frase de un paso de diálogo (None donde no hay). None si no hay ninguna."""
    lista = [buscar(mision, paso, k) for k in range(cuantas)]
    return lista if any(lista) else None


def sonar(app, ruta):
    """Reproduce una grabación por el canal de la interfaz. Devuelve el canal, o None si no se pudo leer."""
    from .sintesis import leer_audio
    try:
        datos = leer_audio(ruta, mono=False)
        if datos.ndim == 1:
            datos = datos.reshape(-1)
    except Exception as e:
        registro.una_vez("voces", "Una voz grabada no se pudo leer", error=type(e).__name__)
        return None
    app.mez.registrar(SONIDO, datos)
    return app.mez.sonar(SONIDO, cat="interfaz")


def guion(misiones, titulo="", existentes=None):
    """Texto del guion de grabación de unas misiones: cada frase con quién la dice y cómo se llama su archivo."""
    existentes = _archivos() if existentes is None else existentes
    lineas = [f"Guion de voces{': ' + titulo if titulo else ''}", "",
              "Graba cada frase en un archivo aparte, en WAV, OGG, FLAC o MP3, con el nombre que se indica,",
              "y deja los archivos en la carpeta data, voces del juego. Las frases sin archivo las dice el lector de pantalla.",
              "Las frases marcadas con la palabra GRABADA ya tienen archivo.", ""]
    total = hechas = 0
    personajes = {}
    for m in misiones:
        cab = False
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            for n, linea in enumerate(paso.get("lineas", [])):
                quien, texto = (linea.get("quien"), linea.get("texto")) if isinstance(linea, dict) else (linea[0], linea[1])
                if not cab:
                    lineas += [f"Misión {m.get('id')}: {m.get('titulo', '')}", ""]
                    cab = True
                arch = nombre(m.get("id"), k, n)
                hecha = arch.lower() in existentes
                total += 1
                hechas += hecha
                personajes[quien] = personajes.get(quien, 0) + 1
                lineas += [f"{arch}{'  GRABADA' if hecha else ''}", f"{quien}: {texto}", ""]
    lineas += [f"Total: {total} frases, {hechas} grabadas.", "",
               "Frases por personaje: " + ", ".join(f"{q} {c}" for q, c in sorted(personajes.items(), key=lambda x: -x[1])) + "."]
    return "\n".join(lineas) + "\n"
