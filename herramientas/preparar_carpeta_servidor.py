"""Prepara la carpeta del servidor dentro del juego compilado, y pone al día la guía del servidor.

    .venv\\Scripts\\python.exe herramientas\\preparar_carpeta_servidor.py --guia
        Reescribe en data\\docs\\servidor.html el apartado de las opciones y la lista de órdenes, que salen de la
        descripción de las opciones (servidor\\opciones.py) y de las órdenes del servidor. Así la guía nunca se queda atrás.

    .venv\\Scripts\\python.exe herramientas\\preparar_carpeta_servidor.py dist\\PuertoBravo
        Crea dist\\PuertoBravo\\servidor con todo lo que hace falta para montar un servidor de cualquier manera:
        los lanzadores de Windows, el ejemplo de configuración, la guía, y la carpeta otros_sistemas con el código del
        servidor para Linux, Mac, NAS y Raspberry Pi, los guiones de arranque, el servicio de systemd y los archivos de Docker.

Lo usa compilar.bat. No copia nada personal: ni configuración, ni datos, ni claves.
"""
import html
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from servidor import opciones          # noqa: E402
from servidor.nucleo import Servidor   # noqa: E402

GUIA = os.path.join(RAIZ, "data", "docs", "servidor.html")
DESPLIEGUE = os.path.join(RAIZ, "servidor", "despliegue")
CARPETA = "servidor"                     # dentro del juego compilado
OTROS = "otros_sistemas"
# Lo que tiene que haber en la carpeta del servidor del juego compilado. Lo comprueba también comprobar_limpio.py.
LANZADORES = ("Panel del servidor.bat", "Servidor por consola.bat", "Parar el servidor.bat",
              "Arrancar con Windows - activar.bat", "Arrancar con Windows - quitar.bat")
GUIONES = ("arrancar.sh", "parar.sh", "estado.sh", "entrada_docker.sh")
DE_DOCKER = ("Dockerfile", "docker-compose.yml")
CONTENIDO = tuple((n,) for n in LANZADORES) + (("LEEME.txt",), ("servidor.conf.ejemplo",), ("documentacion.html",),
                                                (OTROS, "LEEME.txt"), (OTROS, "servidor.conf.ejemplo"), (OTROS, "puertobravo.service"),
                                                (OTROS, "servidor", "__main__.py"), (OTROS, "servidor", "nucleo.py"), (OTROS, "servidor", "opciones.py"),
                                                (OTROS, "servidor", "mundo.json")) + tuple((OTROS, n) for n in GUIONES + DE_DOCKER)
# Lo que no puede aparecer nunca en la carpeta que se reparte.
PROHIBIDO = ("servidor.conf", "datos_servidor", "datos", "puertobravo.db", "certificado.pem", "llave.pem", "firma_ed25519.key", "registro.txt")


def html_ordenes():
    """La lista de órdenes de administración, tal como las dice el propio servidor."""
    e = html.escape
    return "\n".join(["<ul>"] + ["<li><code>%s</code>: %s.</li>" % (e(o), e(que)) for o, que in Servidor.AYUDA_ORDENES] + ["</ul>"])


BLOQUES = (("OPCIONES", lambda: opciones.html_opciones(3)), ("ORDENES", html_ordenes))


def poner_bloques(texto):
    """Devuelve el texto de la guía con los apartados generados al día."""
    for nombre, generar in BLOQUES:
        inicio, fin = "<!-- %s:INICIO -->" % nombre, "<!-- %s:FIN -->" % nombre
        if inicio not in texto or fin not in texto:
            raise ValueError("A la guía del servidor le faltan las marcas %s y %s." % (inicio, fin))
        a, b = texto.index(inicio) + len(inicio), texto.index(fin)
        texto = texto[:a] + "\n" + generar() + "\n" + texto[b:]
    return texto


def guia_al_dia(ruta=GUIA):
    """¿Dice la guía lo mismo que las opciones y las órdenes de ahora?"""
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    return poner_bloques(texto) == texto


def actualizar_guia(ruta=GUIA):
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    nuevo = poner_bloques(texto)
    if nuevo != texto:
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(nuevo)
    return nuevo != texto


def _copiar_texto(origen, destino, fin_de_linea):
    """Copia un archivo de texto con los finales de línea que le tocan: los de Windows o los de Unix."""
    with open(origen, encoding="utf-8") as f:
        texto = f.read()
    with open(destino, "w", encoding="utf-8", newline=fin_de_linea) as f:
        f.write(texto)


def preparar(juego):
    """Crea la carpeta servidor dentro de la carpeta del juego compilado. Devuelve su ruta."""
    destino = os.path.join(juego, CARPETA)
    # Solo se rehace lo que se reparte: si alguien ya tiene ahí su configuración y sus datos, no se tocan.
    for sobra in LANZADORES + ("LEEME.txt", "servidor.conf.ejemplo", "documentacion.html"):
        if os.path.exists(os.path.join(destino, sobra)):
            os.remove(os.path.join(destino, sobra))
    shutil.rmtree(os.path.join(destino, OTROS), ignore_errors=True)
    os.makedirs(os.path.join(destino, OTROS, "servidor"))
    # --- para Windows
    for nombre in LANZADORES:
        shutil.copyfile(os.path.join(DESPLIEGUE, "windows", nombre), os.path.join(destino, nombre))
    _copiar_texto(os.path.join(DESPLIEGUE, "LEEME_servidor.txt"), os.path.join(destino, "LEEME.txt"), "\r\n")
    with open(os.path.join(destino, "servidor.conf.ejemplo"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(opciones.texto_conf())
    actualizar_guia()
    shutil.copyfile(GUIA, os.path.join(destino, "documentacion.html"))
    # --- para los demás sistemas: el código del servidor, que solo necesita Python, y lo que le acompaña
    otros = os.path.join(destino, OTROS)
    for nombre in sorted(os.listdir(os.path.join(RAIZ, "servidor"))):
        if nombre.endswith(".py") or nombre == "mundo.json":
            if nombre.endswith(".py"):
                _copiar_texto(os.path.join(RAIZ, "servidor", nombre), os.path.join(otros, "servidor", nombre), "\n")
            else:
                shutil.copyfile(os.path.join(RAIZ, "servidor", nombre), os.path.join(otros, "servidor", nombre))
    for nombre in GUIONES + DE_DOCKER + ("puertobravo.service",):
        _copiar_texto(os.path.join(DESPLIEGUE, nombre), os.path.join(otros, nombre), "\n")
    _copiar_texto(os.path.join(DESPLIEGUE, "LEEME_otros_sistemas.txt"), os.path.join(otros, "LEEME.txt"), "\n")
    with open(os.path.join(otros, "servidor.conf.ejemplo"), "w", encoding="utf-8", newline="\n") as f:
        f.write(opciones.texto_conf())
    return destino


def comprobar(juego):
    """Lo que le falta o le sobra a la carpeta del servidor de un juego compilado. Lista vacía si está bien."""
    destino = os.path.join(juego, CARPETA)
    problemas = []
    for partes in CONTENIDO:
        if not os.path.exists(os.path.join(destino, *partes)):
            problemas.append("Falta " + os.path.join(CARPETA, *partes))
    for base, dirs, archivos in os.walk(destino):
        for nombre in dirs + archivos:
            if nombre in PROHIBIDO or nombre == "__pycache__" or nombre.lower().endswith((".db", ".pem", ".key", ".pyc")):
                problemas.append("No debe repartirse: " + os.path.relpath(os.path.join(base, nombre), juego))
    ejemplo = os.path.join(destino, "servidor.conf.ejemplo")
    if os.path.exists(ejemplo):
        with open(ejemplo, encoding="utf-8") as f:
            if f.read() != opciones.texto_conf():
                problemas.append("El ejemplo de configuración no es el de las opciones de ahora: " + os.path.join(CARPETA, "servidor.conf.ejemplo"))
    guia = os.path.join(destino, "documentacion.html")
    if os.path.exists(guia):
        if not guia_al_dia(guia):
            problemas.append("La guía del servidor no está al día con las opciones: " + os.path.join(CARPETA, "documentacion.html"))
        otra = os.path.join(juego, "data", "docs", "servidor.html")
        if os.path.exists(otra):
            with open(guia, "rb") as a, open(otra, "rb") as b:
                if a.read() != b.read():
                    problemas.append("La guía de la carpeta del servidor no es la misma que la de data\\docs.")
    return problemas


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--guia":
        print("Guía del servidor puesta al día." if actualizar_guia() else "La guía del servidor ya estaba al día.")
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
