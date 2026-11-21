"""Idiomas del servidor: lo que lee quien lo administra va en su idioma; lo que oyen los jugadores, siempre en español.

En un mismo servidor juega gente de idiomas distintos, así que el servidor no traduce nada de lo que manda a los
jugadores: lo manda en español, el idioma de origen del juego, y el juego de cada uno lo dice en el suyo (busca el
texto en su catálogo, y si el texto lleva huecos, como «%s compra %s, en %s.», lo reconoce por su plantilla). Por eso
hay dos marcas:

- ``es("...")``: un texto para los jugadores. No hace nada: solo lo señala, para que entre en los catálogos de idiomas y
  el juego lo encuentre. Lo que lleva huecos se rellena con ``%`` y nunca se parte en trozos sumados.
- ``tr("...")``: un texto para quien administra (la consola, el registro, la ayuda de las órdenes, las opciones y los
  comentarios de servidor.conf). Sale en el idioma del servidor.

Qué idioma tiene el servidor, por este orden:

1. la variable de entorno PUERTOBRAVO_IDIOMA;
2. si el servidor va dentro del panel (en el mismo programa que el juego), el idioma del juego;
3. la opción «idioma» de servidor.conf;
4. con «auto», que es lo de serie, el del sistema: si es español, o no se sabe, español; si es otro y hay catálogo para
   él, ese; si no, inglés.

Los catálogos se buscan primero en la carpeta idiomas, junto a este archivo (la copia para Linux, Mac y NAS lleva ahí
uno reducido, solo con los textos del servidor), y luego en los del juego, data/idiomas/<código>/textos.json, cuando el
servidor va con el juego compilado o con el código del proyecto.

El idioma se decide la primera vez que hace falta un texto: antes de que se carguen las opciones y la ayuda de las
órdenes, que se escriben al importar sus módulos. Este módulo no usa nada del juego: el servidor funciona solo.
"""
import json
import os
import sys

ORIGEN = "es"
AQUI = os.path.dirname(os.path.abspath(__file__))
VARIABLE = "PUERTOBRAVO_IDIOMA"

# Cómo se llama cada idioma en su propia lengua, por su código.
NOMBRES = {"es": "Español", "en": "English", "it": "Italiano", "fr": "Français", "pt": "Português", "de": "Deutsch", "ca": "Català",
           "eu": "Euskara", "gl": "Galego", "nl": "Nederlands", "pl": "Polski"}

_estado = {"idioma": None, "textos": {}}


def es(texto):
    """Un texto para los jugadores. Sale tal cual, en español: lo traduce el juego de cada uno."""
    return texto


def _bases_del_juego():
    """Las carpetas donde puede estar el juego: la del proyecto (servidor/..), la del juego compilado (lib/servidor/../..)
    y la del ejecutable."""
    bases = [os.path.dirname(AQUI), os.path.dirname(os.path.dirname(AQUI))]
    if getattr(sys, "frozen", False):
        bases.insert(0, os.path.dirname(os.path.abspath(sys.executable)))
    return bases


def ruta_catalogo(cod):
    """Dónde está el catálogo de un idioma: el reducido, junto al servidor, o el del juego. None si no hay."""
    junto = os.path.join(AQUI, "idiomas", cod + ".json")
    if os.path.isfile(junto):
        return junto
    for base in _bases_del_juego():
        ruta = os.path.join(base, "data", "idiomas", cod, "textos.json")
        if os.path.isfile(ruta):
            return ruta
    return None


def disponibles():
    """Los idiomas que hay: {código: nombre}. El español siempre; los demás, los que tienen catálogo."""
    cods = set()
    try:
        cods |= {n[:-5] for n in os.listdir(os.path.join(AQUI, "idiomas")) if n.endswith(".json")}
    except OSError:
        pass
    for base in _bases_del_juego():
        try:
            carpeta = os.path.join(base, "data", "idiomas")
            cods |= {c for c in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, c, "textos.json"))}
        except OSError:
            pass
    r = {ORIGEN: NOMBRES[ORIGEN]}
    for c in sorted(cods - {ORIGEN}):
        r[c] = NOMBRES.get(c, c)
    return r


def idioma_del_sistema():
    """El código de dos letras del idioma del sistema, en minúsculas. Cadena vacía si no se sabe (o es «C» o «POSIX»)."""
    if os.name == "nt":
        try:
            import ctypes
            import locale
            nombre = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
            if nombre:
                return nombre.split("_")[0].lower()
        except Exception:
            pass
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        valor = os.environ.get(var, "").strip()
        if valor:
            cod = valor.split(":")[0].replace("-", "_").split("_")[0].split(".")[0].lower()
            return "" if cod in ("c", "posix") else cod[:3]
    try:
        import locale
        nombre = locale.getlocale()[0] or ""
        cod = nombre.replace("-", "_").split("_")[0].lower()
        return "" if cod in ("c", "posix") else cod[:3]
    except Exception:
        return ""


def _del_juego():
    """Si el servidor va en el mismo programa que el juego (el panel del servidor), el idioma del juego."""
    m = sys.modules.get("juego.i18n")
    if m is None:
        return ""
    try:
        return str(m.actual() or "")
    except Exception:
        return ""


def _es_el_servidor():
    """¿Este programa es el propio servidor, arrancado por consola (python -m servidor o el ejecutable del servidor)?"""
    prog = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
    if os.path.basename(prog) == "__main__.py" and os.path.basename(os.path.dirname(prog)).lower() == "servidor":
        return True
    exe = os.path.basename(sys.executable).lower()
    return bool(getattr(sys, "frozen", False) and "servidor" in exe and "panel" not in exe)


def _de_la_configuracion():
    """La opción «idioma» de servidor.conf, leída como la lee el servidor, sin cargar nada más. Vacío si no está."""
    rutas = []
    if _es_el_servidor():
        rutas += [a for a in sys.argv[1:] if not a.startswith("--")][:1]
        for a in sys.argv[1:]:                                  # también vale --idioma=en
            if a.lower().startswith("--idioma="):
                return a.split("=", 1)[1].strip().lower()
    rutas.append("servidor.conf")
    for ruta in rutas:
        try:
            with open(ruta, "rb") as f:
                bruto = f.read()
        except OSError:
            continue
        try:
            texto = bruto.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = bruto.decode("latin-1")
        for linea in texto.splitlines():
            linea = linea.strip()
            if linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            if k.strip().lower() == "idioma":
                return v.strip().lower()
        return ""
    return ""


def elegir():
    """El idioma que toca, según el orden de arriba."""
    hay = disponibles()
    pedido = (os.environ.get(VARIABLE) or _del_juego() or _de_la_configuracion() or "auto").strip().lower()
    if pedido != "auto":
        return pedido if pedido in hay else ORIGEN
    sistema = idioma_del_sistema()
    if not sistema or sistema == ORIGEN:
        return ORIGEN
    if sistema in hay:
        return sistema
    return "en" if "en" in hay else ORIGEN


def cargar(cod=None):
    """Fija el idioma del servidor y carga su catálogo. Sin código, lo elige solo. Devuelve el que queda.

    Los textos que ya se escribieron al importar los módulos (las opciones, la ayuda de las órdenes) no cambian: el
    idioma se decide una vez, al arrancar."""
    cod = (cod or elegir()).strip().lower()
    textos = {}
    if cod != ORIGEN:
        ruta = ruta_catalogo(cod)
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            textos = {k: v for k, v in (d.get("textos", d) or {}).items() if isinstance(v, str) and v and not k.startswith("_")}
        except (OSError, TypeError, ValueError, AttributeError):
            cod = ORIGEN
    _estado.update(idioma=cod, textos=textos)
    return cod


def actual():
    if _estado["idioma"] is None:
        cargar()
    return _estado["idioma"]


def tr(texto):
    """Un texto para quien administra, en el idioma del servidor. Si no está en el catálogo, en español."""
    if _estado["idioma"] is None:
        cargar()
    if not _estado["textos"] or not isinstance(texto, str):
        return texto
    return _estado["textos"].get(texto, texto)
