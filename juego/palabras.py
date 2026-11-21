"""Red de seguridad de la traducción: palabras sueltas en español que se cuelan en una frase de otro idioma.

El código usa muchas palabras sueltas a la vez como identificador y como texto: los días de la semana, los puntos
cardinales, los grados («rápida», «fuerte»), las unidades («ración», «días»)... No se pueden envolver en tr() sin romper
las comparaciones, así que alguna acaba dicha en español dentro de una frase en inglés («Head este.»).

Al decir algo en un idioma que no es el español, pulir() cambia cada palabra suelta en minúscula que esté en la lista de
ese idioma (data/idiomas/<código>/palabras.json, {palabra española: traducción}) y en el catálogo como palabra sola. Solo
palabras enteras, en minúscula y de tres letras o más: los nombres propios van con mayúscula y no se tocan.
"""
import json
import os
import re

from . import i18n

_cache = {"idioma": None, "mapa": {}}
_PALABRA = re.compile(r"(?<![\wáéíóúñü'-])([a-záéíóúñü]{3,})(?![\wáéíóúñü'-])")


def _mapa():
    cod = i18n.actual()
    if _cache["idioma"] == cod:
        return _cache["mapa"]
    mapa = {}
    if cod != i18n.ORIGEN:
        try:
            with open(os.path.join(i18n.carpeta(cod), "textos.json"), encoding="utf-8") as f:
                textos = json.load(f).get("textos", {})
        except (OSError, ValueError, AttributeError):
            textos = {}
        for es, otro in textos.items():                    # las palabras sueltas del catálogo: «nunca», «fácil»...
            if isinstance(otro, str) and re.fullmatch(r"[a-záéíóúñü]{3,}", es) and otro and otro != es:
                mapa[es] = otro
        try:
            with open(os.path.join(i18n.carpeta(cod), "palabras.json"), encoding="utf-8") as f:
                mapa.update({k: v for k, v in json.load(f).items() if isinstance(v, str) and v and k != v})
        except (OSError, ValueError, AttributeError):
            pass
        ingles = set()                                     # una palabra que también es del idioma no se toca: «media», «once»
        for otro in textos.values():                       # (solo las que van en minúscula: los nombres propios no cuentan)
            if isinstance(otro, str):
                ingles.update(re.findall(r"(?<![A-Za-z])[a-z]+(?![A-Za-z])", otro))
        mapa = {k: v for k, v in mapa.items() if k not in ingles}
    _cache.update(idioma=cod, mapa=mapa)
    return mapa


def pulir(texto):
    """El texto con las palabras sueltas en español cambiadas por las del idioma del juego. En español, tal cual."""
    if not isinstance(texto, str) or not texto or i18n.es_origen():
        return texto
    mapa = _mapa()
    if not mapa:
        return texto
    return _PALABRA.sub(lambda m: mapa.get(m.group(1), m.group(1)), texto)
