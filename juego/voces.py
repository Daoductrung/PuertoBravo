"""Voces grabadas para las escenas: si hay una grabación de una frase, suena en lugar de la voz sintética.

Las grabaciones van en data/voces, en WAV, OGG, FLAC o MP3. Las que trae el juego están en una subcarpeta por
historia. Las del jugador van en data/voces/propias: tienen preferencia y las actualizaciones no las tocan.
Cada archivo se llama
como la misión, el número de paso y el número de frase, empezando en uno y separados por guion bajo:

    oc01_1_2.ogg      misión oc01, paso 1, frase 2

Sirve igual para las misiones del juego que para las de los mods. No hace falta grabarlas todas: las
frases sin archivo las sigue diciendo el lector de pantalla. El editor de mods escribe el guion completo
de un mod, con el nombre de archivo de cada frase, para repartirlo entre quienes vayan a grabar.
"""
import os

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
    """Al arrancar: lleva a data/voces las voces que hayan llegado por el puente y lo borra. Devuelve cuántas ha copiado.

    En una instalación nueva las voces ya están en su sitio y el puente solo se borra. Tras actualizar desde una versión
    anterior, es por aquí por donde llegan. No pisa nada: una grabación que ya exista se deja como está.
    """
    import shutil
    puente = carpeta_puente()
    if not os.path.isdir(puente):
        return 0
    copiadas = 0
    try:
        for base, _, nombres in os.walk(puente):
            destino = os.path.join(carpeta(), os.path.relpath(base, puente))
            for n in nombres:
                if os.path.splitext(n)[1].lower() not in EXT:
                    continue
                if not os.path.exists(os.path.join(destino, n)):
                    os.makedirs(destino, exist_ok=True)
                    shutil.copy2(os.path.join(base, n), os.path.join(destino, n))
                    copiadas += 1
        shutil.rmtree(puente, ignore_errors=True)
    except OSError:
        registro.excepcion("voces", "No se pudieron recoger las voces de la actualización")
        return copiadas
    if copiadas:
        registro.info("voces", "Voces recogidas tras la actualización", cuantas=copiadas)
    refrescar()
    return copiadas


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
                texto = genero.resolver(texto, "h")              # las voces se graban para el protagonista en masculino
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
