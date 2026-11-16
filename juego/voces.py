"""Voces grabadas para las escenas: si hay una grabación de una frase, suena en lugar de la voz sintética.

Las grabaciones van en data/voces, en WAV, OGG, FLAC o MP3. Las que trae el juego están en una subcarpeta por
historia. Las del jugador van en data/voces/propias: tienen preferencia y las actualizaciones no las tocan.
Cada archivo se llama
como la misión, el número de paso y el número de frase, empezando en uno y separados por guion bajo:

    oc01_1_2.ogg      misión oc01, paso 1, frase 2

Las frases que dependen de quién sea el protagonista tienen varias grabaciones: detrás del nombre llevan una arroba
y a quién van (oc01_1_2@alex.ogg, oc01_1_2@m.ogg, oc01_1_2@alex_m.ogg). Las de un personaje hecho por el jugador
que dicen su nombre se generan en su equipo (juego/vozgen.py) y van aparte, en data/voces_generadas.

Sirve igual para las misiones del juego que para las de los mods. No hace falta grabarlas todas: las
frases sin archivo las sigue diciendo el lector de pantalla. El editor de mods escribe el guion completo
de un mod, con el nombre de archivo de cada frase, para repartirlo entre quienes vayan a grabar.
"""
import os
import re

from . import genero, registro, rutas

EXT = (".ogg", ".wav", ".flac", ".mp3")
SONIDO = "_voz_escena"            # nombre interno con el que se carga la grabación que suena
_indice = {"t": None, "archivos": {}}


PROPIAS = "propias"


def carpeta():
    """Todas las voces: las que trae el juego, en una subcarpeta por historia, y las del jugador."""
    return os.path.join(rutas.DATA, "voces")


def carpeta_propias():
    """Donde el jugador o el autor de un mod dejan sus grabaciones. Las actualizaciones no la tocan, y ganan a las de serie."""
    return os.path.join(carpeta(), PROPIAS)


def carpeta_puente():
    """Copia de las voces del juego que viaja dentro de data/datos solo para quien actualiza desde la 1.6.0 o la 1.6.1.

    El actualizador de aquellas versiones tenía escrito que la carpeta «voces» no se toca nunca, porque entonces era solo
    del jugador. Así que no copia data/voces, y las voces nuevas no llegarían. data/datos, en cambio, sí la copia entera.
    """
    return os.path.join(rutas.DATA, "datos", "voces_puente")


def recoger_puente():
    """Al arrancar: lleva a data/voces las voces que trae esta versión y borra el puente. Devuelve cuántas ha puesto.

    Las voces del juego viajan dentro de data/datos, en la carpeta voces_puente, y es aquí donde se colocan: así llegan
    igual a una instalación nueva que a quien actualiza desde cualquier versión. Sustituyen a las de la versión anterior:
    cada grabación nueva pisa a la vieja del mismo nombre, y de las carpetas de las historias se quitan las que esta
    versión ya no trae. Las grabaciones del jugador, en la carpeta propias o sueltas, no se tocan.
    """
    import shutil
    puente = carpeta_puente()
    if not os.path.isdir(puente):
        return 0
    puestas = quitadas = 0
    try:
        for base, _, nombres in os.walk(puente):
            rel = os.path.relpath(base, puente)
            if rel.split(os.sep)[0].lower() == PROPIAS:
                continue
            destino = os.path.join(carpeta(), rel) if rel != "." else carpeta()
            nuevas = {n.lower() for n in nombres if os.path.splitext(n)[1].lower() in EXT}
            if not nuevas:
                continue
            os.makedirs(destino, exist_ok=True)
            if rel != ".":                                   # la carpeta de una historia: fuera lo que ya no viene
                for n in os.listdir(destino):
                    if os.path.splitext(n)[1].lower() in EXT and n.lower() not in nuevas and os.path.isfile(os.path.join(destino, n)):
                        os.remove(os.path.join(destino, n))
                        quitadas += 1
            for n in nombres:
                if os.path.splitext(n)[1].lower() in EXT:
                    os.replace(os.path.join(base, n), os.path.join(destino, n))
                    puestas += 1
        shutil.rmtree(puente, ignore_errors=True)
    except OSError:
        registro.excepcion("voces", "No se pudieron recoger las voces de la actualización")
        return puestas
    if puestas:
        registro.info("voces", "Voces de esta versión colocadas", cuantas=puestas, quitadas=quitadas)
    refrescar()
    return puestas


def limpiar_antigua():
    """Hasta la 1.6.1 las voces del juego iban en data/voces_serie. Ya no se usa: si queda de una versión anterior, se borra."""
    vieja = os.path.join(rutas.DATA, "voces_serie")
    if os.path.isdir(vieja):
        import shutil
        shutil.rmtree(vieja, ignore_errors=True)
        registro.info("voces", "Borrada la carpeta de voces de una versión anterior")
        return True
    return False


def nombre(mision, paso, frase):
    """Nombre de archivo, sin extensión, de una frase: los números empiezan en uno."""
    return f"{mision}_{paso + 1}_{frase + 1}"


def _archivos():
    raiz_voces = carpeta()
    if not os.path.isdir(raiz_voces):
        return {}
    bases = [(base, nombres) for base, _, nombres in os.walk(raiz_voces)]
    marca = (carpeta_propias(), max(os.path.getmtime(base) for base, _ in bases))
    if _indice["t"] != marca:
        _indice["t"], _indice["archivos"] = marca, {}
        propias = os.path.normcase(carpeta_propias())

        def orden(par):                                      # primero las del jugador, luego las sueltas, luego las de serie
            b = os.path.normcase(par[0])
            return (0 if b.startswith(propias) else 1 if b == os.path.normcase(raiz_voces) else 2, b)
        for base, nombres in sorted(bases, key=orden):
            for n in sorted(nombres):
                raiz, ext = os.path.splitext(n)
                if ext.lower() in EXT:
                    _indice["archivos"].setdefault(raiz.lower(), os.path.join(base, n))
    return _indice["archivos"]


def refrescar():
    _indice["t"] = None


def buscar(mision, paso, frase, forma=""):
    return _archivos().get((nombre(mision, paso, frase) + forma).lower())


# Las frases que dependen de quién sea el protagonista se graban en varias formas. El nombre del archivo lleva detrás:
#   nada          la de siempre: Dani, en masculino
#   @alex         le llaman por otro nombre
#   @m            le hablan en femenino
#   @alex_m       depende de las dos cosas, o la dice el propio protagonista con su voz
PROTA = "Dani"                                       # con este nombre figuran en los datos las frases del protagonista
PERSONAJES = ("dani", "alex", "sam", "cris")         # los que tienen sus frases grabadas
_DANI = re.compile(r"\bDani\b")


def depende(quien, texto):
    """De qué depende cómo hay que decir una frase: (dice su nombre, cambia con el género, la dice el protagonista)."""
    return bool(_DANI.search(texto)), bool(genero._MARCA.search(texto)), quien == PROTA


def forma(quien, texto, personaje="dani", gen="h", voz="dani"):
    """Lo que lleva detrás el archivo de esta frase para este protagonista. None si no puede venir grabada: a un personaje
    hecho por el jugador, las frases que dicen su nombre hay que generárselas."""
    nombra, cambia, prota = depende(quien, texto)
    propio = personaje not in PERSONAJES
    if propio and nombra:
        return None
    if prota or (nombra and cambia):
        p = (voz if voz in PERSONAJES else "dani") if propio else personaje     # el personaje propio habla con la voz que eligió
        return "" if (p, gen) == ("dani", "h") else f"@{p}_{gen}"
    if nombra:
        return "" if personaje == "dani" else f"@{personaje}"
    if cambia:
        return "" if gen == "h" else "@m"
    return ""


def formas(quien, texto):
    """Todas las formas en que se graba una frase para los personajes de la lista: [(lo que lleva detrás, personaje, género)]."""
    vistas, out = set(), []
    for p in PERSONAJES:
        for g in genero.GENEROS:
            f = forma(quien, texto, p, g)
            if f not in vistas:
                vistas.add(f)
                out.append((f, p, g))
    return out


def de_dialogo(mision, paso, lineas, j):
    """La grabación de cada frase de un paso de diálogo para este protagonista (None donde no hay). None si no hay ninguna."""
    lista, generadas = [], None
    for n, linea in enumerate(lineas):
        quien, texto = (linea.get("quien"), linea.get("texto")) if isinstance(linea, dict) else (linea[0], linea[1])
        f = forma(quien, texto, j.personaje, j.genero, getattr(j, "voz", "dani"))
        if f is not None:
            lista.append(buscar(mision, paso, n, f))
            continue
        if generadas is None:                                # las de su nombre: las que se le hayan generado ya
            from . import vozgen
            generadas = vozgen.Personaje.de_jugador(j).carpeta()
        ruta = os.path.join(generadas, nombre(mision, paso, n) + ".ogg")
        lista.append(ruta if os.path.exists(ruta) and os.path.exists(ruta + ".txt") else None)
    return lista if any(lista) else None


def de_paso(mision, paso, cuantas):
    """Lista con la grabación de cada frase de un paso de diálogo (None donde no hay). None si no hay ninguna."""
    lista = [buscar(mision, paso, k) for k in range(cuantas)]
    return lista if any(lista) else None


def sonar(app, ruta):
    """Reproduce una grabación por el canal de la interfaz. Devuelve el canal, o None si no se pudo leer."""
    from .sintesis import leer_audio
    try:
        datos = leer_audio(ruta, mono=False, maximo=180)          # una frase no dura tres minutos: si el archivo es enorme, se corta
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
              "Las frases marcadas con la palabra GRABADA ya tienen archivo.",
              "El archivo sin nada detrás es para el protagonista Dani en masculino. Las frases que le nombran, que cambian",
              "si es hombre o mujer, o que dice él mismo, tienen más formas: se indican debajo de cada una.", ""]
    total = hechas = 0
    personajes = {}
    for m in misiones:
        cab = False
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            for n, linea in enumerate(paso.get("lineas", [])):
                quien, texto = (linea.get("quien"), linea.get("texto")) if isinstance(linea, dict) else (linea[0], linea[1])
                texto = genero.resolver(texto, "h")              # las voces se graban para el protagonista en masculino
                if not cab:
                    lineas += [f"Misión {m.get('id')}: {m.get('titulo', '')}", ""]
                    cab = True
                arch = nombre(m.get("id"), k, n)
                hecha = arch.lower() in existentes
                total += 1
                hechas += hecha
                personajes[quien] = personajes.get(quien, 0) + 1
                lineas += [f"{arch}{'  GRABADA' if hecha else ''}", f"{quien}: {texto}"]
                otras = [x for x in formas(quien, linea.get("texto") if isinstance(linea, dict) else linea[1]) if x[0]]
                if otras:                                        # cambia según quién sea el protagonista: sus otras formas
                    lineas.append("  Esta frase cambia con el protagonista. Para que suene con todos, grábala también así:")
                    for suf, pj, g in otras:
                        hecha2 = (arch + suf).lower() in existentes
                        lineas.append(f"  {arch}{suf}{'  GRABADA' if hecha2 else ''}: con {pj.capitalize()}, {genero.NOMBRES[g]}")
                lineas.append("")
    lineas += [f"Total: {total} frases, {hechas} grabadas.", "",
               "Frases por personaje: " + ", ".join(f"{q} {c}" for q, c in sorted(personajes.items(), key=lambda x: -x[1])) + "."]
    return "\n".join(lineas) + "\n"
