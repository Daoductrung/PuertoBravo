"""Junta los trozos traducidos de las guías y deja cada una en data/docs/<guía>_<idioma>.html.

    python herramientas\\i18n\\juntar_docs.py               el inglés
    python herramientas\\i18n\\juntar_docs.py --idioma fr   otro idioma

Las guías se traducen a trozos (traduccion\\<idioma>\\docs\\partes, cortados por encabezados, y traducidos en
traduccion\\<idioma>\\docs\\hechos con el mismo nombre). Antes de escribir, comprueba que cada guía traducida tiene las
mismas etiquetas, en el mismo orden, que la española: si falta un párrafo o una lista, lo dice y no la escribe.
"""
import glob
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETIQUETA = re.compile(r"<(/?)([a-zA-Z0-9]+)")


def etiquetas(t):
    return [(a, b.lower()) for a, b in ETIQUETA.findall(t)]


def main(args):
    cod = args[args.index("--idioma") + 1] if "--idioma" in args else "en"
    base = os.path.join(RAIZ, "traduccion", cod, "docs")
    guias = sorted({re.sub(r"_\d+\.html$", "", os.path.basename(f)) for f in glob.glob(os.path.join(base, "partes", "*.html"))})
    if "--guia" in args:                                             # solo esa: las demás pueden llevar retoques hechos después a mano
        guias = [args[args.index("--guia") + 1]]
    fallos = 0
    for g in guias:
        partes = sorted(glob.glob(os.path.join(base, "partes", f"{g}_[0-9][0-9].html")))
        hechos = [os.path.join(base, "hechos", os.path.basename(p)) for p in partes]
        faltan = [os.path.basename(h) for h in hechos if not os.path.exists(h)]
        if faltan:
            print(f"{g}: faltan trozos por traducir: {', '.join(faltan)}")
            fallos += 1
            continue
        texto = "".join(open(h, encoding="utf-8").read().replace("\r\n", "\n") for h in hechos)
        origen = open(os.path.join(RAIZ, "data", "docs", f"{g}_es.html"), encoding="utf-8").read().replace("\r\n", "\n")
        if etiquetas(texto) != etiquetas(origen):
            a, b = etiquetas(origen), etiquetas(texto)
            i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
            print(f"{g}: las etiquetas no cuadran con la española (la {i}: {a[i:i + 3]} frente a {b[i:i + 3]}). No se escribe.")
            fallos += 1
            continue
        destino = os.path.join(RAIZ, "data", "docs", f"{g}_{cod}.html")
        with open(destino, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(texto)
        print(f"{g}: escrita {os.path.relpath(destino, RAIZ)}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
