"""Deja escrito en los archivos de datos el transporte público de cada localidad: las paradas de tranvía con su orden
en la línea, la estación de tren, el aeropuerto y el recorrido de las vías.

    .venv\\Scripts\\python.exe herramientas\\escribir_transporte.py

El juego sabe poner todo eso él solo en una localidad que no lo traiga (así funcionan los mods de terceros que no lo
definen). Pero en los datos que vienen con el juego queda escrito, lugar a lugar, para que se pueda editar con el editor
de mods o a mano: mover una parada, cambiarle el nombre, quitarla, cambiar por dónde van las vías.

No toca lo que ya esté escrito: solo añade lo que falte. Se puede ejecutar las veces que haga falta.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import mundo as M, rutas          # noqa: E402

TIPOS = ("tranvia", "tren", "aeropuerto")


def completar(mapa, lugares_fuera=()):
    """Completa el diccionario de un mapa. Devuelve (lugares nuevos, vías) sin escribir nada.

    `lugares_fuera` son los lugares de ese mapa que el archivo guarda aparte (así los guardan los mods)."""
    if mapa.get("tipo") == "mar" or "avenidas" not in mapa:
        return [], None
    c = dict(mapa)
    c["lugares"] = [dict(l) for l in mapa.get("lugares", [])] + [dict(l) for l in lugares_fuera]
    antes = {l["id"] for l in c["lugares"]}
    M.completar_transporte(c)
    nuevos = [l for l in c["lugares"] if l["id"] not in antes]
    m = M.Mundo(c)
    vias = m.esquinas_de_las_vias() if m.via_nodos else None
    return nuevos, (vias if not mapa.get("vias") else None)


def _linea(l):
    return json.dumps(l, ensure_ascii=False)


def escribir_en_archivo(ruta):
    """Añade a un archivo de mapa del juego base, sin cambiarle el formato, lo que le falte."""
    texto = open(ruta, encoding="utf-8").read()
    mapa = json.loads(texto)
    nuevos, vias = completar(mapa)
    if not nuevos and vias is None:
        return 0, False
    if nuevos:
        ini = texto.index('"lugares": [')
        fin = texto.index("\n  ]", ini)                         # el cierre de la lista de lugares
        texto = texto[:fin] + "".join(",\n    " + _linea(l) for l in nuevos) + texto[fin:]
    if vias is not None:
        ini = texto.index('"lugares": [')
        fin = texto.index("\n  ]", ini) + len("\n  ]")
        texto = texto[:fin] + ",\n  \"vias\": " + json.dumps(vias) + texto[fin:]
    json.loads(texto)                                           # tiene que seguir siendo un JSON válido
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    return len(nuevos), vias is not None


def completar_mod(crudo):
    """Completa los mapas de un mod ya cargado como diccionario. Los lugares nuevos van a su lista de lugares."""
    total = 0
    for mapa in crudo.get("mapas", []):
        fuera = [l for l in crudo.get("lugares", []) if l.get("mapa") == mapa.get("id")]
        nuevos, vias = completar(mapa, fuera)
        for l in nuevos:
            l["mapa"] = mapa["id"]
            crudo.setdefault("lugares", []).append(l)
        if vias is not None:
            mapa["vias"] = vias
        total += len(nuevos)
    return total


if __name__ == "__main__":
    archivos = [os.path.join(rutas.DATOS, "ciudad.json")] + sorted(
        os.path.join(rutas.DATOS, "mapas", f) for f in os.listdir(os.path.join(rutas.DATOS, "mapas")) if f.endswith(".json"))
    for ruta in archivos:
        n, vias = escribir_en_archivo(ruta)
        print(f"  {os.path.basename(ruta)}: {n} lugares añadidos" + (", vías escritas" if vias else ""))
