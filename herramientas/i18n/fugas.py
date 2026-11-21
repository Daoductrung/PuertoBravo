"""Busca español que se haya colado en un texto que debería estar en otro idioma: un documento traducido, lo que dice el
juego jugando en inglés...

    python herramientas\\i18n\\fugas.py data\\docs\\teclas_en.html [más archivos]     dice las frases sospechosas de cada uno

Una frase es sospechosa si tiene varias palabras que solo son españolas (de, que, los, para, con...) o letras que el
inglés no usa (ñ, á, ¿...). Lo que va entre <code> y <pre>, las rutas y los nombres propios del juego no cuentan: son
nombres de verdad que no se traducen. Sirve como aviso, no como sentencia: las frases que salen hay que mirarlas.
"""
import html
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PALABRAS = {"el", "los", "las", "del", "que", "para", "con", "por", "una", "uno", "unos", "unas", "pero", "como", "más", "muy", "está", "están",
            "hay", "tiene", "tienes", "puedes", "cuando", "donde", "sin", "también", "ya", "esto", "este", "esta", "eso", "ese", "esa", "su", "sus",
            "tu", "tus", "te", "se", "lo", "le", "les", "al", "pulsa", "elige", "volver", "juego", "partida", "ahora", "nada", "algo", "dinero"}
RARAS = re.compile(r"[ñÑáéíóúÁÉÍÓÚ¿¡]")


def _propios():
    """Nombres propios del juego que no se traducen: los del glosario cuya traducción es la misma."""
    try:
        d = json.load(open(os.path.join(RAIZ, "traduccion", "en", "nombres.json"), encoding="utf-8"))
        return {k for k, v in d.items() if k == v} | {"Puerto Bravo: Ley del Asfalto", "Ley del Asfalto"}
    except (OSError, ValueError):
        return set()


PROPIOS = _propios()


def limpiar_html(t):
    t = re.sub(r"<(code|pre|kbd)\b[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    return html.unescape(t)


def sospechosa(frase):
    f = frase
    for p in PROPIOS:
        if p in f:
            f = f.replace(p, " ")
    f = re.sub(r"\S*[\\/]\S*", " ", f)                       # rutas: data\voces\propias
    f = re.sub(r"«[^»]*»", " ", f)                            # lo citado entre comillas españolas suele ser un nombre
    mayus = r"[A-ZÁÉÍÓÚÑ][\wáéíóúñü]*"
    f = re.sub(mayus + r"(?:\s+(?:del|de la|de las|de los|de|y)\s+" + mayus + r")+", " ", f)    # «Calle del Cauce», «Paseo de las Palmeras»
    f = re.sub(r"\b" + mayus, " ", f)                                                         # y los demás nombres propios, con mayúscula
    palabras = re.findall(r"[a-záéíóúñü]+", f.lower())
    if not palabras:
        return False
    esp = sum(1 for p in palabras if p in PALABRAS)
    return esp >= 2 or (esp >= 1 and len(palabras) <= 4) or bool(RARAS.search(f))


def frases(texto):
    for linea in texto.splitlines():
        for trozo in re.split(r"(?<=[.:;!?])\s+", linea.strip()):
            if trozo and re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{2}", trozo):
                yield trozo


def fugas(texto, es_html=False):
    if es_html:
        texto = limpiar_html(texto)
    return [f for f in frases(texto) if sospechosa(f)]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    total = 0
    for ruta in sys.argv[1:]:
        t = open(ruta, encoding="utf-8").read()
        malas = fugas(t, ruta.lower().endswith(".html"))
        total += len(malas)
        print(f"{ruta}: {len(malas)} frases sospechosas")
        for m in malas[:60]:
            print("   ", m[:200])
    sys.exit(1 if total else 0)
