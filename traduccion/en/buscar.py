"""Busca en el catálogo inglés cómo se dice un texto del juego: menús, opciones, nombres.

    python traduccion\\en\\buscar.py "Vida, reputación y consecuencias"      la traducción exacta, o las más parecidas
    python traduccion\\en\\buscar.py --contiene "Mis vehículos"               todas las que contienen ese texto
"""
import difflib
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CAT = json.load(open(os.path.join(AQUI, "en.json"), encoding="utf-8"))["textos"]
NOMBRES = json.load(open(os.path.join(AQUI, "nombres.json"), encoding="utf-8"))
TODO = dict(CAT)
TODO.update(NOMBRES)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args[:1] == ["--contiene"]:
        q = args[1].lower()
        for k, v in TODO.items():
            if q in k.lower() and len(k) < 200:
                print(f"{k!r} => {v!r}")
    else:
        q = " ".join(args)
        if q in TODO:
            print(f"{q!r} => {TODO[q]!r}")
        else:
            for k in difflib.get_close_matches(q, list(TODO), n=8, cutoff=0.6):
                print(f"{k!r} => {TODO[k]!r}")
