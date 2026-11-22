"""El género del protagonista en los textos.

Las frases que cambian según el protagonista sea hombre o mujer llevan una marca entre corchetes con las dos formas
separadas por una barra: primero la masculina y luego la femenina.

    Bienvenid[o|a] al balneario.          ->  Bienvenido / Bienvenida
    Tú eres [el sobrino|la sobrina].      ->  el sobrino / la sobrina
    Buen[|a] vecin[o|a].                  ->  Buen vecino / Buena vecina

Vale igual en los datos (misiones, mods, descripciones) que en los textos del código, y se resuelve en un solo sitio:
justo antes de decir, mostrar o registrar el texto.
"""
from .i18n import tr
import re

GENEROS = ("h", "m")
NOMBRES = {"h": tr("en masculino"), "m": tr("en femenino")}
_MARCA = re.compile(r"\[([^\[\]|]*)\|([^\[\]|]*)\]")
_MARCA_ROBUSTA = re.compile(r"\[([^\[\]]+)\]")

actual = "h"          # el de la partida en curso


def poner(g):
    """Fija el género de la partida en curso. Cualquier valor raro se toma como masculino, que es como estaba escrito todo."""
    global actual
    actual = g if g in GENEROS else "h"
    return actual


def resolver(texto, g=None):
    """Deja en el texto la forma que corresponde al género del protagonista."""
    if not isinstance(texto, str) or "|" not in texto:
        return texto
    g = actual if g is None else g
    def _elegir(m):
        contenido = m.group(1)
        if "|" not in contenido:
            return m.group(0)
        partes = contenido.split("|")
        return partes[-1] if g == "m" else partes[0]
    return _MARCA_ROBUSTA.sub(_elegir, texto)


def marcas(texto):
    """Las marcas de género que hay en un texto, para el editor y las pruebas."""
    return _MARCA.findall(texto) if isinstance(texto, str) else []
