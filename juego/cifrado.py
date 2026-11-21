"""Archivos JSON protegidos.

El juego compilado lleva sus datos (mapas, misiones, armas, vehículos, mods) y las partidas en archivos
que conservan la extensión .json pero cuyo contenido va comprimido, cifrado y firmado. Así no se pueden
abrir con un editor de texto para cambiar una misión o el dinero de una partida, y un archivo manipulado
o estropeado se rechaza en lugar de cargarse a medias.

Todo el programa lee con `leer_json`, que acepta las dos formas: si el archivo empieza por la marca,
lo descifra; si no, lo lee como JSON normal. Por eso el código fuente trabaja con JSON legible, los mods
escritos a mano siguen valiendo y el editor abre tanto unos como otros.

Hasta dónde llega: la clave va dentro del propio programa, como en cualquier juego que se reparte sin
servidor. Impide la edición casual; no detiene a quien desensamble el ejecutable. Usa solo la biblioteca
estándar de Python: no añade dependencias.

Formato: MARCA (8 bytes) + sal (16) + firma HMAC-SHA256 (32) + datos. Los datos son el JSON en UTF-8,
comprimido con zlib y combinado (XOR) con un flujo de bytes generado con SHA-256 en modo contador.
"""
from .i18n import tr
import hashlib
import hmac
import json
import os
import sys
import zlib

MARCA = b"PBRAVO1\n"
_PIEZAS = ("ley-del", "asfalto", "puerto", "bravo", "7f3a91c2", "audiojuego")
# En el juego compilado, lo que el programa escribe (partidas) va cifrado. En el código fuente, legible.
COMPILADO = bool(getattr(sys, "frozen", False))


def _clave(sal, uso):
    base = "|".join(reversed(_PIEZAS)).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", base + uso, sal, 2000)


def _flujo(clave, n):
    trozos = []
    for i in range((n + 31) // 32):
        trozos.append(hashlib.sha256(clave + i.to_bytes(8, "big")).digest())
    return b"".join(trozos)[:n]


def _xor(datos, flujo):
    return (int.from_bytes(datos, "big") ^ int.from_bytes(flujo, "big")).to_bytes(len(datos), "big") if datos else b""


def cifrar(objeto):
    """Devuelve los bytes protegidos de un objeto que se pueda guardar como JSON."""
    claro = zlib.compress(json.dumps(objeto, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 9)
    sal = os.urandom(16)
    cuerpo = _xor(claro, _flujo(_clave(sal, b"cifra"), len(claro)))
    firma = hmac.new(_clave(sal, b"firma"), cuerpo, hashlib.sha256).digest()
    return MARCA + sal + firma + cuerpo


def descifrar(datos):
    if not datos.startswith(MARCA) or len(datos) < len(MARCA) + 48:
        raise ValueError(tr("El archivo no tiene el formato protegido del juego."))
    sal = datos[len(MARCA):len(MARCA) + 16]
    firma = datos[len(MARCA) + 16:len(MARCA) + 48]
    cuerpo = datos[len(MARCA) + 48:]
    if not hmac.compare_digest(firma, hmac.new(_clave(sal, b"firma"), cuerpo, hashlib.sha256).digest()):
        raise ValueError(tr("El archivo está dañado o ha sido modificado."))
    return json.loads(zlib.decompress(_xor(cuerpo, _flujo(_clave(sal, b"cifra"), len(cuerpo)))).decode("utf-8"))


def esta_cifrado(ruta):
    try:
        with open(ruta, "rb") as f:
            return f.read(len(MARCA)) == MARCA
    except OSError:
        return False


def leer_json(ruta):
    """Lee un archivo JSON, esté protegido o no."""
    with open(ruta, "rb") as f:
        datos = f.read()
    if datos.startswith(MARCA):
        return descifrar(datos)
    return json.loads(datos.decode("utf-8-sig"))


def escribir_json(ruta, objeto, cifrado=None, sangria=None):
    """Guarda un objeto en un archivo JSON, con escritura atómica.

    cifrado: True lo protege, False lo deja legible, None lo decide según sea el juego compilado o el código fuente.
    """
    if cifrado is None:
        cifrado = COMPILADO
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    tmp = ruta + ".tmp"
    if cifrado:
        with open(tmp, "wb") as f:
            f.write(cifrar(objeto))
    else:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(objeto, f, ensure_ascii=False, indent=sangria)
    os.replace(tmp, ruta)


def cifrar_archivo(ruta):
    """Protege un archivo JSON legible. Devuelve False si ya lo estaba."""
    if esta_cifrado(ruta):
        return False
    escribir_json(ruta, leer_json(ruta), cifrado=True)
    return True


def descifrar_archivo(ruta, sangria=1):
    if not esta_cifrado(ruta):
        return False
    escribir_json(ruta, leer_json(ruta), cifrado=False, sangria=sangria)
    return True
