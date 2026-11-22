"""Componentes: lo que se actualiza aparte del juego, sin esperar a una versión nueva.

Idiomas, voces, documentación, packs de sonidos, mods y lo que venga después se publican como componentes sueltos, cada
uno con su número de versión. El juego los busca en la misma fuente que las actualizaciones (Opciones, Actualizaciones:
el servidor del juego, GitHub, las dos o una dirección personalizada) y los instala sin cerrarse.

Cómo funciona:
1. Se lee componentes/componentes.json, junto al version.json de cada fuente (en GitHub, componentes.json en la
   publicación fija «componentes»).
   Va FIRMADO con la misma clave que las versiones del juego: sin firma válida no se instala nada.
2. Cada componente dice su identificador (idioma-en, voces-en, docs-en, pack-retro, mod-valdeolmos...), su tipo, su
   versión, su ZIP con tamaño y SHA-256, y la versión mínima del juego que necesita.
3. Un componente solo puede escribir en las carpetas de su tipo: un idioma, en data/idiomas y en los documentos de ese
   idioma; un pack, en data/sonidos; un mod, en data/mods... Cualquier otra ruta en el ZIP hace que se rechace entero.
4. Lo instalado se apunta en data/componentes.json: qué versión de cada uno. Así se sabe qué hay nuevo.
5. Nunca toca partidas, opciones, tu música ni tus grabaciones propias.
"""
import json
import os
import shutil
import urllib.parse
import zipfile

from . import VERSION, actualizador as A, rutas
from .i18n import es, tr

ARCHIVO = "componentes.json"
ARCHIVO_SERIE = "componentes_de_serie.json"     # los que trae el juego, con su versión: los escribe la compilación
CARPETA_WEB = "componentes"                       # en el servidor, junto a version.json: componentes/componentes.json y sus ZIP
URL_SERVIDOR = A.URL_SERVIDOR.rsplit("/", 1)[0] + f"/{CARPETA_WEB}/{ARCHIVO}"
TAG_GITHUB = "componentes"
URL_GITHUB = f"https://github.com/{A.REPOSITORIO_GITHUB}/releases/download/{TAG_GITHUB}/{ARCHIVO}"
MAX_COMPONENTE = 2 * 1024 ** 3
MAX_MIEMBROS = 100000

# Dónde puede escribir cada tipo de componente, relativo a la carpeta del juego.
TIPOS = {
    "idioma": ("data/idiomas/", "data/docs/"),
    "voces": ("data/voces/", "data/phonon/"),
    "documentacion": ("data/docs/",),
    "sonidos": ("data/sonidos/",),
    "mod": ("data/mods/", "data/idiomas/", "data/voces/"),      # el mod, su traducción a cada idioma y sus voces
    "musica": ("data/musica/",),
    "radio": ("data/radio/",),
}
# Lo que dice el menú de cada componente que el juego trae de serie, para que se sepa qué es en cualquier idioma. Se escribe
# en español y herramientas/publicar_componentes.py lo pone en el manifiesto en cada idioma que tiene catálogo («nombres» y
# «descripciones»): así lo entiende también un juego anterior, que lee el nombre y la descripción tal como llegan.
# {idioma} es el nombre del idioma en el de quien lee; la descripción de un pack o de un mod sale de sus datos.
DESCRIPCIONES = {
    "idioma": es("El juego entero en {idioma}: los menús, la historia, los lugares, los objetos, las teclas, el editor de mods y el panel "
                 "del servidor. Después de instalarlo, elígelo en Opciones, Idioma: se aplica al volver a abrir el juego."),
    "voces": es("Las voces grabadas de las escenas de la historia en {idioma}. Sin ellas, las escenas las dice tu lector de pantalla."),
    "documentacion": es("El manual y las demás guías en {idioma}, puestas al día sin esperar a una versión nueva del juego."),
    "sonidos": es("{descripcion} Se elige en Opciones, Sonido y música, Pack de sonidos, y se oye al momento."),
    "mod": es("{descripcion} Se carga solo al abrir el juego. Para quitarlo, desactívalo en Opciones, Mods, o en el editor de mods con Control M."),
}

NOMBRE_TIPO = {"idioma": tr("Idiomas"), "voces": tr("Voces"), "documentacion": tr("Documentación"), "sonidos": tr("Packs de sonidos"), "mod": tr("Mods"),
               "musica": tr("Música de ambiente"), "radio": tr("Radio")}


class Componente:
    def __init__(self, d, url_manifiesto, fuente):
        self.id = str(d["id"])
        self.tipo = str(d["tipo"])
        from . import i18n                                          # el nombre y la descripción, en el idioma del juego si los trae
        cod = i18n.actual()
        self.nombre = str((d.get("nombres") or {}).get(cod) or d.get("nombre") or self.id)
        self.descripcion = str((d.get("descripciones") or {}).get(cod) or d.get("descripcion") or "")
        self.version = int(d["version"])
        self.archivo = str(d["file"])
        self.sha256 = str(d["sha256"]).lower()
        self.tamano = int(d["size"])
        self.requiere = str(d.get("requiere_juego") or "0")
        self.borra = [str(x) for x in (d.get("borra") or [])]       # lo que una versión anterior traía y esta ya no
        junto = urllib.parse.urljoin(url_manifiesto, urllib.parse.quote(self.archivo))
        principal = str(d.get("url") or "")
        espejo = str((d.get("espejos") or {}).get("github") or "")
        orden = [espejo or junto, principal] if fuente == "github" else [junto, principal, espejo] if fuente == "personalizada" else [principal or junto, espejo]
        self.urls = []
        for u in orden:
            if u and u not in self.urls:
                try:
                    A.comprobar_url(u)
                    self.urls.append(u)
                except A.ErrorActualizacion:
                    pass
        if self.tipo not in TIPOS or os.path.basename(self.archivo) != self.archivo or not self.archivo.lower().endswith(".zip"):
            raise A.ErrorFirma(tr("Un componente no es válido: {id}.").format(id=self.id))
        if len(self.sha256) != 64 or not 0 < self.tamano <= MAX_COMPONENTE or not self.urls:
            raise A.ErrorFirma(tr("Un componente no es válido: {id}.").format(id=self.id))

    @property
    def tipo_txt(self):
        return tr(NOMBRE_TIPO.get(self.tipo, self.tipo))


def _leer(nombre, clave):
    try:
        with open(rutas.data(nombre), encoding="utf-8") as f:
            d = json.load(f)
        return {str(k): int(v) for k, v in (d.get(clave) or {}).items()}
    except (OSError, ValueError, AttributeError, TypeError):
        return {}


def instalados(solo_propios=False):
    """La versión de cada componente que hay: la más alta entre lo que trae el juego de serie y lo instalado después."""
    propios = _leer(ARCHIVO, "instalados")
    if solo_propios:
        return propios
    r = _leer(ARCHIVO_SERIE, "de_serie")
    for k, v in propios.items():
        r[k] = max(v, r.get(k, 0))
    return r


def _apuntar(cid, version):
    d = {"instalados": instalados(solo_propios=True)}
    if version is None:
        d["instalados"].pop(cid, None)
    else:
        d["instalados"][cid] = int(version)
    tmp = rutas.data(ARCHIVO + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, rutas.data(ARCHIVO))


def fuentes(fuente, url_personalizada=""):
    if fuente == "github":
        return [("github", URL_GITHUB)]
    if fuente == "ambas":
        return [("servidor", URL_SERVIDOR), ("github", URL_GITHUB)]
    if fuente == "personalizada":
        url = str(url_personalizada or "").strip()
        if not url:
            raise A.ErrorActualizacion(tr("Has elegido una dirección personalizada, pero no has escrito ninguna. Escríbela en Opciones, Actualizaciones."))
        A.comprobar_url(url)
        return [("personalizada", urllib.parse.urljoin(url, f"{CARPETA_WEB}/{ARCHIVO}"))]
    return [("servidor", URL_SERVIDOR)]


def consultar(fuente="servidor", url_personalizada="", abrir=None, claves=None):
    """Los componentes publicados: {id: Componente}, el de versión más alta de cada uno entre las fuentes."""
    abrir = abrir or A.abrir_red
    todos, errores = {}, []
    for nombre, url in fuentes(fuente if fuente in A.FUENTES else "servidor", url_personalizada):
        try:
            m = A._leer_manifiesto(url, A.NOMBRE_FUENTE[nombre], abrir)
            A.verificar_firma(m, claves)
            for d in m.get("componentes") or []:
                try:
                    c = Componente(d, url, nombre)
                except (KeyError, TypeError, ValueError, A.ErrorActualizacion):
                    continue
                if c.id not in todos or c.version > todos[c.id].version:
                    todos[c.id] = c
        except A.ErrorActualizacion as e:
            errores.append(e)
        except ValueError as e:
            errores.append(A.ErrorFirma(str(e)))
    if not todos and errores:
        raise errores[0]
    return todos


def novedades(publicados):
    """Los que se pueden instalar o actualizar con este juego: [(Componente, versión instalada o 0)]."""
    hay = instalados()
    r = []
    for c in publicados.values():
        if A.clave_version(VERSION) < A.clave_version(c.requiere):
            continue
        if c.version > hay.get(c.id, 0):
            r.append((c, hay.get(c.id, 0)))
    return sorted(r, key=lambda x: (x[0].tipo, x[0].nombre))


def _comprobar_zip(z, tipo):
    permitidas = TIPOS[tipo]
    miembros = z.infolist()
    if len(miembros) > MAX_MIEMBROS:
        raise A.ErrorFirma(tr("El componente es demasiado grande."))
    for m in miembros:
        nombre = m.filename.replace("\\", "/")
        partes = [p for p in nombre.split("/") if p]
        if nombre.startswith("/") or ":" in nombre or ".." in partes or (m.external_attr >> 16) & 0o170000 == 0o120000:
            raise A.ErrorFirma(tr("El componente contiene rutas no permitidas. No se instala."))
        if not m.is_dir() and not any(nombre.startswith(p) for p in permitidas):
            raise A.ErrorFirma(tr("El componente intenta escribir fuera de su sitio. No se instala."))
        if any(x in partes for x in A.INTOCABLES):
            raise A.ErrorFirma(tr("El componente intenta tocar tus datos personales. No se instala."))
    return miembros


def instalar(c, progreso=None, cancelado=None, abrir=None):
    """Descarga, comprueba e instala un componente. Devuelve la frase para decir."""
    class _Info:
        archivo, sha256, tamano, urls = c.archivo, c.sha256, c.tamano, c.urls
    carpeta = os.path.join(A.carpeta_trabajo(), "componentes")
    ruta = A.descargar(_Info, carpeta, progreso=progreso, cancelado=cancelado, abrir=abrir)
    raiz = os.path.realpath(rutas.base())
    try:
        with zipfile.ZipFile(ruta) as z:
            miembros = _comprobar_zip(z, c.tipo)
            for m in miembros:
                partes = [p for p in m.filename.replace("\\", "/").split("/") if p]
                destino = os.path.realpath(os.path.join(raiz, *partes))
                if not destino.startswith(raiz + os.sep):
                    raise A.ErrorFirma(tr("El componente contiene rutas no permitidas. No se instala."))
                if m.is_dir():
                    os.makedirs(destino, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                tmp = destino + ".nuevo"
                with z.open(m) as origen, open(tmp, "wb") as f:
                    shutil.copyfileobj(origen, f, 1024 * 1024)
                os.replace(tmp, destino)
    except zipfile.BadZipFile:
        raise A.ErrorFirma(tr("El componente está dañado.")) from None
    except OSError as e:
        raise A.error_de_disco(e, tr("instalar el componente")) from e
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass
    for b in c.borra:                                              # lo que esta versión ya no trae, dentro de su sitio
        b = b.replace("\\", "/")
        if ".." in b or not any(b.startswith(p) for p in TIPOS[c.tipo]):
            continue
        r = os.path.realpath(os.path.join(raiz, *b.split("/")))
        if r.startswith(raiz + os.sep) and os.path.isfile(r):
            try:
                os.remove(r)
            except OSError:
                pass
    _apuntar(c.id, c.version)
    return tr("{nombre} instalado, versión {version}.").format(nombre=c.nombre, version=c.version)


def reinicio_necesario(c):
    """Un idioma o unas voces del idioma en uso se notan al reiniciar; lo demás, al momento o al volver a abrirlo."""
    return c.tipo in ("idioma", "voces")
