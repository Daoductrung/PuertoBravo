"""Publica una versión del juego para el actualizador.

    .venv\\Scripts\\python.exe herramientas\\publicar.py clave
        Crea, UNA sola vez, el par de claves de firma. La privada queda en herramientas\\claves, que no se
        sube al repositorio. Imprime la pública, que va en CLAVES_PUBLICAS de juego\\actualizador.py.

    .venv\\Scripts\\python.exe herramientas\\publicar.py publicar [carpeta_de_destino]
        Con el juego ya compilado en dist\\PuertoBravo: comprueba que está limpio, lo comprime en
        PuertoBravo_v<versión>.zip, escribe version.json con su tamaño, su SHA-256 y las novedades, lo firma,
        lo verifica y copia los dos archivos a la carpeta de destino (la carpeta web de tu servidor).
        Sin destino en la orden, se lee de publicar_destino.txt, en la raíz del proyecto (no va al repositorio).
        Los mismos dos archivos son los que se suben a la release de GitHub, con la etiqueta v<versión>.

    .venv\\Scripts\\python.exe herramientas\\publicar.py verificar ruta\\version.json

    Con la orden prueba en lugar de publicar, lo mismo pero en la subcarpeta pruebas del destino y con la dirección de esa
    subcarpeta: para probar que una versión se actualiza bien antes de publicarla. La versión publicada no se toca.

La clave privada no debe estar nunca en el repositorio ni en el servidor. Guarda una copia fuera del equipo:
sin ella no se pueden publicar versiones que acepten los juegos ya repartidos.
"""
import base64
import datetime
import html
import json
import os
import re
import shutil
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from juego import VERSION, actualizador as A, ed25519          # noqa: E402

CLAVES = os.path.join(RAIZ, "herramientas", "claves")
PRIVADA = os.path.join(CLAVES, "firma_ed25519.key")
DIST = os.path.join(RAIZ, "dist", "PuertoBravo")
SALIDA = os.path.join(RAIZ, "dist", "publicar")
SUB_PRUEBAS = "pruebas"            # subcarpeta del servidor para probar una actualización antes de publicarla


def crear_clave():
    if os.path.exists(PRIVADA):
        raise SystemExit(f"Ya existe {PRIVADA}. No se sobrescribe: con ella se firmaron las versiones repartidas.")
    os.makedirs(CLAVES, exist_ok=True)
    with open(os.path.join(CLAVES, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("# Clave privada de firma: nunca al repositorio ni al servidor.\n*\n")
    semilla = os.urandom(32)
    with open(PRIVADA, "w", encoding="ascii") as f:
        f.write(semilla.hex() + "\n")
    return ed25519.publica(semilla).hex()


def leer_privada():
    with open(PRIVADA, encoding="ascii") as f:
        semilla = bytes.fromhex(f.read().strip())
    if len(semilla) != 32:
        raise SystemExit("La clave privada no es válida.")
    return semilla


def firmar(manifiesto, semilla):
    manifiesto.pop(A.CAMPO_FIRMA, None)
    manifiesto[A.CAMPO_FIRMA] = base64.b64encode(ed25519.firmar(semilla, A.serializar_canonico(manifiesto))).decode("ascii")
    return manifiesto


def apartado_novedades(cod="es"):
    """El título y el HTML del primer apartado de data/docs/novedades_<cod>.html, o None si no hay."""
    try:
        with open(os.path.join(RAIZ, "data", "docs", f"novedades_{cod}.html"), encoding="utf-8") as f:
            pagina = f.read()
    except OSError:
        return None
    m = re.search(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|</body>)", pagina, re.S)
    return (m.group(1), m.group(2)) if m else None


def novedades(cod="es"):
    """El primer apartado de data/docs/novedades_<cod>.html, en texto. Vacío si ese idioma no tiene novedades."""
    apartado = apartado_novedades(cod)
    if not apartado:
        return ""
    cuerpo = re.sub(r"</(li|p|h3)>", "\n", apartado[1])
    texto = html.unescape(re.sub(r"<[^>]+>", "", apartado[0] + ".\n" + cuerpo))
    return recortar_novedades([l.strip() for l in texto.splitlines() if l.strip()], cola=COLAS.get(cod, COLAS["en"]))


def idiomas_con_novedades():
    """Los códigos de idioma que tienen su data/docs/novedades_<cod>.html, el español primero."""
    cods = sorted(f[len("novedades_"):-len(".html")] for f in os.listdir(os.path.join(RAIZ, "data", "docs"))
                  if re.fullmatch(r"novedades_[a-z]{2,3}\.html", f))
    return sorted(cods, key=lambda c: c != "es")


def notas_github(cods=None):
    """Las notas de la release de GitHub en Markdown, con lo nuevo de la versión en cada idioma que lo tenga: así quien
    no lee español encuentra las suyas. publicar() las deja junto al ZIP, en notas_github.md."""
    partes = []
    for cod in cods or idiomas_con_novedades():
        apartado = apartado_novedades(cod)
        if not apartado:
            continue
        md = apartado[1]
        md = re.sub(r"<h3[^>]*>(.*?)</h3>", lambda m: "\n### " + " ".join(m.group(1).split()) + "\n", md, flags=re.S)
        md = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: "- " + " ".join(m.group(1).split()) + "\n", md, flags=re.S)
        md = re.sub(r"<p[^>]*>(.*?)</p>", lambda m: "\n" + " ".join(m.group(1).split()) + "\n", md, flags=re.S)
        md = html.unescape(re.sub(r"<[^>]+>", "", md))
        md = re.sub(r"\n[ \t]+", "\n", md)
        md = re.sub(r"(?<=\n)\n+(?=- )", "", "\n" + md)[1:]       # los puntos de una lista, seguidos, sin línea en blanco
        md = re.sub(r"\n{3,}", "\n\n", md).strip()
        partes.append(f"## {TITULO_NOTAS.get(cod, html.unescape(apartado[0]))}\n\n{md}\n")
    return "\n".join(partes)


NOVEDADES_MAX = 6000
# Lo que se dice cuando no caben todas las novedades, en cada idioma; un idioma sin la suya usa la inglesa.
COLAS = {
    "es": "Hay más: la lista completa está en el menú principal del juego, en Acerca de, Novedades de esta versión.",
    "en": "There is more: the full list is in the game's main menu, in About, What's new in this version.",
}
TITULO_NOTAS = {"es": "Novedades (español)", "en": "What's new (English)"}


def recortar_novedades(lineas, tope=NOVEDADES_MAX, cola=COLAS["es"]):
    """El resumen de novedades que viaja con la versión: cada línea es un punto, y solo entran puntos completos. Si no
    caben todos, se corta al final del último que quepa (nunca a mitad de palabra) y se dice dónde está el resto."""
    entero = "\n".join(lineas)
    if len(entero) <= tope:
        return entero
    dentro, largo = [], len(cola)
    for l in lineas:
        if largo + len(l) + 1 > tope:
            break
        dentro.append(l)
        largo += len(l) + 1
    return "\n".join(dentro + [cola])


def comprimir(carpeta, destino):
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base, dirs, archivos in os.walk(carpeta):
            dirs.sort()
            for f in sorted(archivos):
                ruta = os.path.join(base, f)
                rel = os.path.relpath(ruta, carpeta).replace(os.sep, "/")
                sin_comprimir = f.lower().endswith((".mp3", ".ogg", ".zip", ".png", ".jpg"))
                z.write(ruta, rel, zipfile.ZIP_STORED if sin_comprimir else zipfile.ZIP_DEFLATED)


def publicar(destino=None, dist=DIST, prueba=False):
    """Con prueba=True, la versión va a la subcarpeta pruebas del servidor: la versión publicada no se toca, y solo la ve
    el juego al que se le haya dicho que se actualice desde ahí (herramientas/apuntar_a_pruebas.py)."""
    from herramientas import comprobar_limpio
    if destino is None:
        try:
            with open(os.path.join(RAIZ, "publicar_destino.txt"), encoding="utf-8-sig") as f:
                destino = f.read().strip().strip('"')
        except OSError:
            destino = ""
    if not os.path.isfile(os.path.join(dist, A.EJECUTABLE)):
        raise SystemExit("No hay juego compilado. Ejecuta antes compilar.bat")
    fallos = comprobar_limpio.comprobar(dist)
    if fallos:
        raise SystemExit("La compilación no está limpia:\n  " + "\n  ".join(fallos))
    semilla = leer_privada()
    publica = ed25519.publica(semilla).hex()
    if publica not in A.CLAVES_PUBLICAS:
        raise SystemExit("La clave pública de tu clave privada no está en CLAVES_PUBLICAS de juego\\actualizador.py:\n  " + publica)
    os.makedirs(SALIDA, exist_ok=True)
    nombre = f"{A.NOMBRE_APP}_v{VERSION}.zip"
    ruta_zip = os.path.join(SALIDA, nombre)
    print(f"Comprimiendo {dist} ...")
    comprimir(dist, ruta_zip)
    base_servidor = A.URL_SERVIDOR.rsplit("/", 1)[0] + "/" + (SUB_PRUEBAS + "/" if prueba else "")
    manifiesto = firmar({
        "version": VERSION, "file": nombre, "sha256": A.sha256_de(ruta_zip), "size": os.path.getsize(ruta_zip),
        "url": base_servidor + nombre,
        "espejos": {} if prueba else {"github": f"https://github.com/{A.REPOSITORIO_GITHUB}/releases/download/v{VERSION}/{nombre}"},
        "fecha": datetime.date.today().isoformat(), "novedades": novedades(),
        # Desde la 1.7.3 cada juego lee las de su idioma; los anteriores solo conocen "novedades", en español.
        "novedades_por_idioma": {cod: novedades(cod) for cod in idiomas_con_novedades()},
    }, semilla)
    if prueba and destino:
        destino = os.path.join(destino, SUB_PRUEBAS)
        os.makedirs(destino, exist_ok=True)
    ruta_json = os.path.join(SALIDA, "version.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(manifiesto, f, indent=4, ensure_ascii=False)
        f.write("\n")
    problemas = verificar(ruta_json)
    if problemas:
        raise SystemExit("La versión recién firmada no pasa la verificación:\n  " + "\n  ".join(problemas))
    print(f"Listo en {SALIDA}: {nombre} ({manifiesto['size'] // (1024 * 1024)} MB) y version.json, firmado.")
    if destino:
        if not os.path.isdir(destino):
            raise SystemExit(f"No existe la carpeta de destino: {destino}")
        shutil.copy2(ruta_zip, os.path.join(destino, nombre))             # primero el ZIP: version.json nunca apunta a algo que falta
        shutil.copy2(ruta_json, os.path.join(destino, "version.json"))
        print(f"Publicado en {destino}")
    else:
        print("No hay carpeta de destino: copia tú los dos archivos al servidor.")
    if prueba:
        print("Es una versión de prueba: la publicada no se ha tocado. Dirección para probarla:", base_servidor + "version.json")
    else:
        notas = os.path.join(SALIDA, "notas_github.md")
        with open(notas, "w", encoding="utf-8", newline="\n") as f:
            f.write(notas_github())
        print(f"Para GitHub: crea la release v{VERSION} con esos mismos dos archivos y, como notas, notas_github.md, que trae")
        print("lo nuevo en cada idioma:")
        print(f'  gh release create v{VERSION} "{ruta_zip}" "{ruta_json}" --title "Puerto Bravo {VERSION}" --notes-file "{notas}"')
    return ruta_zip, ruta_json


def verificar(ruta_json):
    with open(ruta_json, encoding="utf-8") as f:
        m = json.load(f)
    problemas = []
    try:
        A.verificar_firma(m)
    except A.ErrorActualizacion as e:
        problemas.append(str(e))
    ruta_zip = os.path.join(os.path.dirname(os.path.abspath(ruta_json)), str(m.get("file", "")))
    if os.path.isfile(ruta_zip):
        if os.path.getsize(ruta_zip) != m.get("size"):
            problemas.append("El tamaño del ZIP no coincide.")
        if A.sha256_de(ruta_zip) != m.get("sha256"):
            problemas.append("El SHA-256 del ZIP no coincide.")
    else:
        problemas.append("No está el ZIP junto a version.json.")
    return problemas


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else ""
    if orden == "clave":
        print("Clave privada creada en", PRIVADA)
        print("Clave pública, para CLAVES_PUBLICAS de juego\\actualizador.py:")
        print("  " + crear_clave())
    elif orden == "publicar":
        publicar(sys.argv[2] if len(sys.argv) > 2 else None)
    elif orden == "prueba":
        publicar(sys.argv[2] if len(sys.argv) > 2 else None, prueba=True)
    elif orden == "verificar" and len(sys.argv) > 2:
        fallos_ = verificar(sys.argv[2])
        print("\n".join(fallos_) if fallos_ else "Firma y archivo correctos.")
        sys.exit(1 if fallos_ else 0)
    else:
        print(__doc__)
