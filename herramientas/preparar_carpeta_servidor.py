"""Prepara la carpeta del servidor dentro del juego compilado, y pone al día la guía del servidor en cada idioma.

    .venv\\Scripts\\python.exe herramientas\\preparar_carpeta_servidor.py --guia
        Reescribe en cada guía del servidor que haya (data\\docs\\servidor_es.html, servidor_en.html...) el apartado de
        las opciones y la lista de órdenes, que salen de la descripción de las opciones (servidor\\opciones.py) y de las
        órdenes del servidor, en el idioma de esa guía. Así ninguna guía se queda atrás.

    .venv\\Scripts\\python.exe herramientas\\preparar_carpeta_servidor.py dist\\PuertoBravo
        Crea dist\\PuertoBravo\\servidor con todo lo que hace falta para montar un servidor de cualquier manera:
        los lanzadores de Windows, el ejemplo de configuración, la guía en cada idioma (documentacion_es.html,
        documentacion_en.html...), y la carpeta otros_sistemas con el código del servidor para Linux, Mac, NAS y
        Raspberry Pi, con un catálogo reducido de cada idioma (solo los textos del servidor), los guiones de arranque, el
        servicio de systemd y los archivos de Docker.

Lo usa compilar.bat. No copia nada personal: ni configuración, ni datos, ni claves.

Los textos de las opciones y de las órdenes se traducen al cargarse los módulos del servidor, así que cada idioma se
genera en un proceso aparte, con la variable PUERTOBRAVO_IDIOMA puesta. El ejemplo de configuración va en español: los
nombres de las opciones son los mismos en todos los idiomas, y quien lo quiera en el suyo lo escribe con --ejemplo.
"""
import ast
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from servidor import idioma, opciones          # noqa: E402
from servidor.nucleo import Servidor           # noqa: E402

DOCS = os.path.join(RAIZ, "data", "docs")
GUIA = os.path.join(DOCS, "servidor_es.html")     # la guía en el idioma de origen
DESPLIEGUE = os.path.join(RAIZ, "servidor", "despliegue")
CARPETA = "servidor"                     # dentro del juego compilado
OTROS = "otros_sistemas"
# Lo que tiene que haber en la carpeta del servidor del juego compilado. Lo comprueba también comprobar_limpio.py.
LANZADORES = ("Panel del servidor.bat", "Servidor por consola.bat", "Parar el servidor.bat",
              "Arrancar con Windows - activar.bat", "Arrancar con Windows - quitar.bat")
GUIONES = ("arrancar.sh", "parar.sh", "reiniciar.sh", "estado.sh", "entrada_docker.sh")
DE_DOCKER = ("Dockerfile", "docker-compose.yml")
CONTENIDO = tuple((n,) for n in LANZADORES) + (("LEEME.txt",), ("servidor.conf.ejemplo",), ("documentacion_es.html",),
                                                (OTROS, "LEEME.txt"), (OTROS, "servidor.conf.ejemplo"), (OTROS, "puertobravo.service"),
                                                (OTROS, "servidor", "__main__.py"), (OTROS, "servidor", "nucleo.py"), (OTROS, "servidor", "opciones.py"),
                                                (OTROS, "servidor", "idioma.py"), (OTROS, "servidor", "mundo.json")) + tuple((OTROS, n) for n in GUIONES + DE_DOCKER)
# Lo que no puede aparecer nunca en la carpeta que se reparte.
PROHIBIDO = ("servidor.conf", "datos_servidor", "datos", "puertobravo.db", "certificado.pem", "llave.pem", "firma_ed25519.key", "registro.txt")
# Lo que se repartía antes y ya no: se quita al preparar, y si sigue ahí, sobra.
VIEJO = ("documentacion.html",)


# ------------------------------------------------------------------ lo generado, en cada idioma
def html_ordenes():
    """La lista de órdenes de administración, tal como las dice el propio servidor."""
    e = html.escape
    return "\n".join(["<ul>"] + ["<li><code>%s</code>: %s.</li>" % (e(o), e(que)) for o, que in Servidor.AYUDA_ORDENES] + ["</ul>"])


def _generado_aqui():
    return {"OPCIONES": opciones.html_opciones(3), "ORDENES": html_ordenes(), "conf": opciones.texto_conf()}


_hechos = {}


def generado(cod):
    """Lo que sale de las opciones y las órdenes en un idioma: el apartado de opciones, la lista de órdenes y el texto de
    servidor.conf. En el idioma de este proceso se hace aquí; en otro, en un proceso aparte con ese idioma."""
    if cod not in _hechos:
        if cod == idioma.actual():
            _hechos[cod] = _generado_aqui()
        else:
            env = dict(os.environ, PUERTOBRAVO_IDIOMA=cod, PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "--generado"], env=env, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                raise RuntimeError("No se han podido generar los textos del servidor en %s: %s" % (cod, (r.stderr or r.stdout).strip()[-500:]))
            _hechos[cod] = json.loads(r.stdout)
    return _hechos[cod]


def idioma_de(ruta):
    """El idioma de una guía, por su nombre: servidor_en.html o documentacion_en.html son inglés. Sin código, español."""
    m = re.search(r"_([a-z]{2,3})\.html$", os.path.basename(ruta))
    return m.group(1) if m else idioma.ORIGEN


def guias(carpeta=DOCS, prefijo="servidor"):
    """Las guías del servidor que hay en una carpeta: {idioma: ruta}."""
    r = {}
    for ruta in sorted(glob.glob(os.path.join(carpeta, prefijo + "_*.html"))):
        if re.fullmatch(prefijo + r"_[a-z]{2,3}\.html", os.path.basename(ruta)):
            r[idioma_de(ruta)] = ruta
    return r


def poner_bloques(texto, cod=idioma.ORIGEN):
    """Devuelve el texto de una guía con los apartados generados al día, en el idioma ``cod``."""
    hecho = generado(cod)
    for nombre in ("OPCIONES", "ORDENES"):
        inicio, fin = "<!-- %s:INICIO -->" % nombre, "<!-- %s:FIN -->" % nombre
        if inicio not in texto or fin not in texto:
            raise ValueError("A la guía del servidor le faltan las marcas %s y %s." % (inicio, fin))
        a, b = texto.index(inicio) + len(inicio), texto.index(fin)
        texto = texto[:a] + "\n" + hecho[nombre] + "\n" + texto[b:]
    return texto


def guia_al_dia(ruta=GUIA):
    """¿Dice la guía lo mismo que las opciones y las órdenes de ahora, en su idioma?"""
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    return poner_bloques(texto, idioma_de(ruta)) == texto


def actualizar_guia(ruta=GUIA):
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    nuevo = poner_bloques(texto, idioma_de(ruta))
    if nuevo != texto:
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(nuevo)
    return nuevo != texto


def actualizar_guias():
    """Pone al día todas las guías del servidor que haya. Devuelve {ruta: si ha cambiado}."""
    return {ruta: actualizar_guia(ruta) for ruta in guias().values()}


def texto_ejemplo():
    """El ejemplo de servidor.conf que se reparte: el de las opciones de ahora, comentado en español."""
    return generado(idioma.ORIGEN)["conf"]


# ------------------------------------------------------------------ el catálogo reducido, para el servidor que va solo
def textos_del_servidor():
    """Los textos españoles que el código del servidor marca con tr() o es()."""
    textos = set()
    for ruta in glob.glob(os.path.join(RAIZ, "servidor", "*.py")):
        with open(ruta, encoding="utf-8") as f:
            arbol = ast.parse(f.read())
        for n in ast.walk(arbol):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("tr", "es") and n.args \
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                textos.add(n.args[0].value)
    return textos


def catalogos_reducidos():
    """{idioma: catálogo} con solo los textos del servidor, de cada idioma que tenga catálogo en el juego."""
    suyos = textos_del_servidor()
    r = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "data", "idiomas", "*", "textos.json"))):
        cod = os.path.basename(os.path.dirname(ruta))
        if cod == idioma.ORIGEN:
            continue
        with open(ruta, encoding="utf-8") as f:
            todo = json.load(f).get("textos") or {}
        r[cod] = {"textos": {k: v for k, v in sorted(todo.items()) if k in suyos}}
    return r


# ------------------------------------------------------------------ la carpeta
def _copiar_texto(origen, destino, fin_de_linea):
    """Copia un archivo de texto con los finales de línea que le tocan: los de Windows o los de Unix."""
    with open(origen, encoding="utf-8") as f:
        texto = f.read()
    with open(destino, "w", encoding="utf-8", newline=fin_de_linea) as f:
        f.write(texto)


def preparar(juego):
    """Crea la carpeta servidor dentro de la carpeta del juego compilado. Devuelve su ruta.

    Las guías salen de las de data\\docs con los apartados generados al día, sin tocar las de data\\docs (eso lo hace
    --guia, que compilar.bat lanza antes de copiar la documentación)."""
    destino = os.path.join(juego, CARPETA)
    # Solo se rehace lo que se reparte: si alguien ya tiene ahí su configuración y sus datos, no se tocan.
    for sobra in LANZADORES + ("LEEME.txt", "servidor.conf.ejemplo") + VIEJO + tuple(os.path.basename(r) for r in glob.glob(os.path.join(destino, "documentacion_*.html"))):
        if os.path.exists(os.path.join(destino, sobra)):
            os.remove(os.path.join(destino, sobra))
    shutil.rmtree(os.path.join(destino, OTROS), ignore_errors=True)
    os.makedirs(os.path.join(destino, OTROS, "servidor"))
    # --- para Windows
    for nombre in LANZADORES:
        shutil.copyfile(os.path.join(DESPLIEGUE, "windows", nombre), os.path.join(destino, nombre))
    _copiar_texto(os.path.join(DESPLIEGUE, "LEEME_servidor.txt"), os.path.join(destino, "LEEME.txt"), "\r\n")
    for ruta in sorted(glob.glob(os.path.join(DESPLIEGUE, "LEEME_servidor_*.txt"))):
        _copiar_texto(ruta, os.path.join(destino, os.path.basename(ruta).replace("LEEME_servidor_", "LEEME_")), "\r\n")
    with open(os.path.join(destino, "servidor.conf.ejemplo"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(texto_ejemplo())
    for cod, ruta in guias().items():
        with open(ruta, encoding="utf-8") as f:
            texto = poner_bloques(f.read(), cod)
        with open(os.path.join(destino, "documentacion_%s.html" % cod), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    # --- para los demás sistemas: el código del servidor, que solo necesita Python, y lo que le acompaña
    otros = os.path.join(destino, OTROS)
    for nombre in sorted(os.listdir(os.path.join(RAIZ, "servidor"))):
        if nombre.endswith(".py") or nombre == "mundo.json":
            if nombre.endswith(".py"):
                _copiar_texto(os.path.join(RAIZ, "servidor", nombre), os.path.join(otros, "servidor", nombre), "\n")
            else:
                shutil.copyfile(os.path.join(RAIZ, "servidor", nombre), os.path.join(otros, "servidor", nombre))
    reducidos = catalogos_reducidos()
    if reducidos:
        os.makedirs(os.path.join(otros, "servidor", "idiomas"))
    for cod, cat in reducidos.items():
        with open(os.path.join(otros, "servidor", "idiomas", cod + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(cat, f, ensure_ascii=False, indent=0)
    for nombre in GUIONES + DE_DOCKER + ("puertobravo.service",):
        _copiar_texto(os.path.join(DESPLIEGUE, nombre), os.path.join(otros, nombre), "\n")
    _copiar_texto(os.path.join(DESPLIEGUE, "LEEME_otros_sistemas.txt"), os.path.join(otros, "LEEME.txt"), "\n")
    for ruta in sorted(glob.glob(os.path.join(DESPLIEGUE, "LEEME_otros_sistemas_*.txt"))):
        _copiar_texto(ruta, os.path.join(otros, os.path.basename(ruta).replace("LEEME_otros_sistemas_", "LEEME_")), "\n")
    with open(os.path.join(otros, "servidor.conf.ejemplo"), "w", encoding="utf-8", newline="\n") as f:
        f.write(texto_ejemplo())
    return destino


def comprobar(juego):
    """Lo que le falta o le sobra a la carpeta del servidor de un juego compilado. Lista vacía si está bien."""
    destino = os.path.join(juego, CARPETA)
    problemas = []
    for partes in CONTENIDO:
        if not os.path.exists(os.path.join(destino, *partes)):
            problemas.append("Falta " + os.path.join(CARPETA, *partes))
    for nombre in VIEJO:
        if os.path.exists(os.path.join(destino, nombre)):
            problemas.append("Sobra %s: la guía va ahora por idiomas, documentacion_es.html, documentacion_en.html..." % os.path.join(CARPETA, nombre))
    for base, dirs, archivos in os.walk(destino):
        for nombre in dirs + archivos:
            if nombre in PROHIBIDO or nombre == "__pycache__" or nombre.lower().endswith((".db", ".pem", ".key", ".pyc")):
                problemas.append("No debe repartirse: " + os.path.relpath(os.path.join(base, nombre), juego))
    for cod in catalogos_reducidos():
        if not os.path.exists(os.path.join(destino, OTROS, "servidor", "idiomas", cod + ".json")):
            problemas.append("Falta " + os.path.join(CARPETA, OTROS, "servidor", "idiomas", cod + ".json"))
    ejemplo = os.path.join(destino, "servidor.conf.ejemplo")
    if os.path.exists(ejemplo):
        with open(ejemplo, encoding="utf-8") as f:
            if f.read() != texto_ejemplo():
                problemas.append("El ejemplo de configuración no es el de las opciones de ahora: " + os.path.join(CARPETA, "servidor.conf.ejemplo"))
    de_data = guias(os.path.join(juego, "data", "docs"))
    for cod in de_data:
        if not os.path.exists(os.path.join(destino, "documentacion_%s.html" % cod)):
            problemas.append("Falta %s: está la guía del servidor en ese idioma en data\\docs." % os.path.join(CARPETA, "documentacion_%s.html" % cod))
    for cod, guia in guias(destino, "documentacion").items():
        nombre = os.path.join(CARPETA, os.path.basename(guia))
        if not guia_al_dia(guia):
            problemas.append("La guía del servidor no está al día con las opciones: " + nombre)
        otra = de_data.get(cod)
        if otra:
            with open(guia, "rb") as a, open(otra, "rb") as b:
                if a.read() != b.read():
                    problemas.append("La guía %s no es la misma que data\\docs\\%s." % (nombre, os.path.basename(otra)))
    return problemas


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generado":       # lo pide generado(), en otro idioma
        sys.stdout.write(json.dumps(_generado_aqui(), ensure_ascii=False))
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--guia":
        for ruta, cambia in actualizar_guias().items():
            print(("Guía del servidor puesta al día: %s" if cambia else "La guía del servidor ya estaba al día: %s") % os.path.basename(ruta))
        sys.exit(0)
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.join("dist", "PuertoBravo")
    if not os.path.isdir(carpeta):
        print("No existe la carpeta " + carpeta)
        sys.exit(1)
    print("Carpeta del servidor preparada en " + preparar(carpeta))
    fallos = comprobar(carpeta)
    for p in fallos:
        print("  " + p)
    sys.exit(1 if fallos else 0)
