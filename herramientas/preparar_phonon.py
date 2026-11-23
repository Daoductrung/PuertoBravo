"""Prepara data/phonon: lo que el juego necesita para generar las voces de un personaje hecho por el jugador.

    .venv\\Scripts\\python.exe herramientas\\preparar_phonon.py [carpeta del modelo] [reparto_final.json]

Deja en data/phonon:
  config.json, tokenizer.json, model.q8.gguf   el modelo Phonon 40m multilingüe de Gradium, en su versión ligera
  voces/                                       la voz de cada personaje que nombra al protagonista, y las ocho del protagonista
  reparto.json                                 qué archivo de voz lleva cada uno
  LICENCIA.txt                                 la licencia del modelo: CC BY-NC 4.0

El modelo pesa 95 megas y no se guarda en git: se copia de la carpeta que se indique (por defecto, la de Fonaria).
Las voces y el reparto sí se guardan. Una voz mezclada es la media de dos del catálogo de Gradium.
"""
import glob
import json
import os
import re
import shutil
import struct
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_args = sys.argv[1:]
IDIOMA = "es"
if "--idioma" in _args:                              # --idioma en: las voces de otro idioma, de reparto_en.json, en
    i = _args.index("--idioma")                      # data/phonon/voces_en y reparto_en.json; el modelo es el mismo
    IDIOMA = _args[i + 1]
    del _args[i:i + 2]
DESTINO = os.path.join(RAIZ, "data", "phonon")
VOCES = "voces" if IDIOMA == "es" else "voces_" + IDIOMA                 # las de otro idioma, aparte: voces_en, reparto_en.json
REPARTO_SALIDA = "reparto.json" if IDIOMA == "es" else f"reparto_{IDIOMA}.json"
MODELO = _args[0] if len(_args) > 0 else r"D:\Antigravity\PhononAndroid\modelo"
REPARTO = _args[1] if len(_args) > 1 else os.path.join(RAIZ, "adjuntos", "voces_phonon", "reparto_final.json" if IDIOMA == "es" else f"reparto_{IDIOMA}.json")
DANI = re.compile(r"\bDani\b")


def leer_voz(ruta):
    with open(ruta, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        cab = json.loads(f.read(n))
        datos = f.read()
    clave = next(k for k in cab if k != "__metadata__")
    a, b = cab[clave]["data_offsets"]
    return clave, np.frombuffer(datos[a:b], dtype=np.float32).reshape(cab[clave]["shape"]).copy()


def escribir_voz(ruta, clave, tensor):
    cab = json.dumps({clave: {"dtype": "F32", "shape": list(tensor.shape), "data_offsets": [0, tensor.nbytes]}}, separators=(",", ":")).encode()
    cab += b" " * ((8 - len(cab) % 8) % 8)
    with open(ruta, "wb") as f:
        f.write(struct.pack("<Q", len(cab)))
        f.write(cab)
        f.write(tensor.astype(np.float32).tobytes())


def quienes_le_nombran():
    out = set()
    for f in sorted(glob.glob(os.path.join(RAIZ, "data", "datos", "*.json")) + glob.glob(os.path.join(RAIZ, "data", "mods", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for m in (d.get("misiones", []) if isinstance(d, dict) else []):
            for paso in m.get("pasos", []):
                if paso.get("tipo") == "dialogo":
                    out |= {q for q, t in paso.get("lineas", []) if DANI.search(t) and q != "Dani"}
    return out


def main():
    os.makedirs(os.path.join(DESTINO, VOCES), exist_ok=True)
    apk = os.path.join(MODELO, "apk", "modelo")
    for n in (("config.json", "tokenizer.json", "model.q8.gguf") if IDIOMA == "es" else ()):     # otro idioma usa el de data/phonon
        origen = next((p for p in (os.path.join(apk, n), os.path.join(MODELO, n)) if os.path.exists(p)), None)
        if origen is None:
            if os.path.exists(os.path.join(DESTINO, n)):        # sin la carpeta del modelo, pero data/phonon ya lo tiene: vale
                print("No está", n, "en", MODELO, "- se usa el que ya hay en data/phonon.")
                continue
            print("FALTA", n, "en", MODELO, "y tampoco está en data/phonon")
            return 1
        if not os.path.exists(os.path.join(DESTINO, n)) or os.path.getsize(os.path.join(DESTINO, n)) != os.path.getsize(origen):
            shutil.copy2(origen, os.path.join(DESTINO, n))
    if not os.path.exists(REPARTO):
        print("No está el reparto (", REPARTO, "): se dejan las voces que ya hubiera.")
        return 0
    rep = json.load(open(REPARTO, encoding="utf-8"))
    salida = {"personajes": {}, "protagonista": {}}

    def poner(nombre_archivo, esp):
        ruta = os.path.join(DESTINO, VOCES, nombre_archivo + ".safetensors")
        clave, t = leer_voz(os.path.join(MODELO, "voces", esp["id"] + ".safetensors"))
        if esp["tipo"] == "mezcla":
            _, b = leer_voz(os.path.join(MODELO, "voces", esp["con_id"] + ".safetensors"))
            t = t * (1 - esp["parte"]) + b * esp["parte"]
        escribir_voz(ruta, clave, t)

    for k, esp in rep["protagonista"].items():
        poner("prota_" + k, esp)
        salida["protagonista"][k] = "prota_" + k
    try:                                             # quien ya tenía archivo lo conserva: si cambiara de nombre, a los jugadores se les
        with open(os.path.join(DESTINO, REPARTO_SALIDA), encoding="utf-8") as f:      # volverían a generar frases que ya tienen hechas
            antes = {q: a for q, a in json.load(f).get("personajes", {}).items() if re.fullmatch("voz_[0-9]+", str(a))}
    except (OSError, ValueError):
        antes = {}
    quienes = sorted(quienes_le_nombran())
    ocupados = {antes[q] for q in quienes if q in antes}
    n = 0
    for quien in quienes:
        esp = rep["personajes"].get(quien)
        if esp is None:
            print("sin voz en el reparto:", quien)
            continue
        archivo = antes.get(quien)
        while archivo is None:
            n += 1
            if "voz_%02d" % n not in ocupados:
                archivo = "voz_%02d" % n
        poner(archivo, esp)
        salida["personajes"][quien] = archivo
    sobran = set(os.listdir(os.path.join(DESTINO, VOCES))) - {v + ".safetensors" for v in list(salida["personajes"].values()) + list(salida["protagonista"].values())}
    for s in sobran:
        os.remove(os.path.join(DESTINO, VOCES, s))
    with open(os.path.join(DESTINO, REPARTO_SALIDA), "w", encoding="utf-8", newline="\n") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1, sort_keys=True)
    lic = os.path.join(os.path.dirname(MODELO), "docs", "LICENCIA-MODELO.txt")
    if os.path.exists(lic) and IDIOMA == "es":
        shutil.copy2(lic, os.path.join(DESTINO, "LICENCIA.txt"))
    print(os.path.relpath(os.path.join(DESTINO, VOCES), RAIZ), "listo:", len(salida["personajes"]), "voces de personajes y", len(salida["protagonista"]), "del protagonista")
    return 0


if __name__ == "__main__":
    sys.exit(main())
