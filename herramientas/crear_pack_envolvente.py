"""Monta el pack de sonidos «envolvente»: los del pack realista más ambientes grabados en estéreo, sin tocar la orientación.

    .venv\\Scripts\\python.exe herramientas\\crear_pack_envolvente.py

- Lleva los mismos archivos que los demás packs: todos los sonidos del juego.
- Parte de los del pack realista, salvo los de orientación (GPS, radar, semáforos, localizadores y firmas de los
  lugares), que se copian tal cual de los sonidos de serie: son la base de la accesibilidad y no deben cambiar.
- Añade encima las grabaciones de adjuntos\\packs\\fuentes_envolvente (ambientes en estéreo y algún sonido suelto),
  que deben ser de dominio público o CC0. De dónde sale cada una queda escrito en el propio pack.

Las grabaciones se recortan a un minuto como mucho, se les quita el salto al repetirse (el final se funde con el
principio), se igualan de volumen y se guardan en OGG. Se puede repetir las veces que haga falta.
"""
import json
import os
import shutil
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from juego import catalogo_sonidos as cat, sintesis          # noqa: E402

FUENTES = os.path.join(RAIZ, "adjuntos", "packs", "fuentes_envolvente")
BASE = os.path.join(RAIZ, "data", "sonidos", "realista")
DESTINO = os.path.join(RAIZ, "data", "sonidos", "envolvente")
ORIENTACION = ("Orientación y GPS", "Localizadores", "Firmas de los lugares")
MAXIMO = 60.0            # segundos
FUNDIDO = 2.5            # segundos que se solapan el final y el principio de un ambiente
NIVEL = 0.10             # volumen medio (RMS) al que se dejan los ambientes
EXT = (".wav", ".ogg", ".flac", ".mp3")


SERIE = os.path.join(RAIZ, "data", "sonidos", "por_defecto")
_INDICES = {k for k, g in enumerate(cat.GRUPOS) if g[0] in ORIENTACION}


def es_orientacion(nombre):
    return cat.grupo_de(nombre) in _INDICES


def bucle(d, sr):
    """Hace que el ambiente se repita sin salto: funde el último tramo con el primero."""
    n = int(FUNDIDO * sr)
    if len(d) < 4 * n:
        return d
    rampa = np.linspace(0.0, 1.0, n, dtype=np.float32)
    if d.ndim == 2:
        rampa = rampa[:, None]
    cuerpo = d[:-n].copy()
    cuerpo[:n] = d[:n] * rampa + d[-n:] * (1.0 - rampa)
    return cuerpo


def preparar(ruta, nombre):
    import soundfile as sf
    fondo = sintesis.es_fondo(nombre)
    d = sintesis.leer_audio(ruta, mono=not fondo, maximo=MAXIMO + FUNDIDO if fondo else 12.0)
    d = d - d.mean(axis=0)
    if fondo:
        d = bucle(d, sintesis.SR)
        rms = float(np.sqrt(np.mean(d.astype(np.float64) ** 2))) or 1.0
        d = d * (NIVEL / rms)
    pico = float(np.max(np.abs(d))) or 1.0
    if pico > 0.95 or not fondo:
        d = d * (0.95 / pico) if pico > 0.95 else d * min(1.0, 0.9 / pico)
    salida = os.path.join(DESTINO, nombre + ".ogg")
    d = d.astype(np.float32)
    # Por trozos: escribir un OGG largo de una sola vez hace caerse a la biblioteca de audio.
    with sf.SoundFile(salida, "w", samplerate=sintesis.SR, channels=1 if d.ndim == 1 else 2, format="OGG", subtype="VORBIS") as f:
        for i in range(0, len(d), 22050):
            f.write(d[i:i + 22050])
    return {"canales": 1 if d.ndim == 1 else 2, "segundos": round(len(d) / sintesis.SR, 1)}


def crear():
    shutil.rmtree(DESTINO, ignore_errors=True)
    os.makedirs(DESTINO)
    copiados = 0
    for f in sorted(os.listdir(BASE)):
        nombre, ext = os.path.splitext(f)
        if ext.lower() in EXT:
            # los de orientación, siempre los de serie; el resto, los del pack realista
            origen = os.path.join(SERIE, f) if es_orientacion(nombre) and os.path.exists(os.path.join(SERIE, f)) else os.path.join(BASE, f)
            shutil.copy2(origen, os.path.join(DESTINO, f))
            copiados += 1
    fuentes = {}
    ruta_fuentes = os.path.join(FUENTES, "fuentes.json")
    if os.path.exists(ruta_fuentes):
        fuentes = json.load(open(ruta_fuentes, encoding="utf-8"))
    nuevos = {}
    if os.path.isdir(FUENTES):
        for f in sorted(os.listdir(FUENTES)):
            nombre, ext = os.path.splitext(f)
            if ext.lower() not in EXT or es_orientacion(nombre):
                continue
            for viejo in EXT:                                   # la grabación nueva sustituye a la del pack de partida
                if os.path.exists(os.path.join(DESTINO, nombre + viejo)):
                    os.remove(os.path.join(DESTINO, nombre + viejo))
            nuevos[nombre] = preparar(os.path.join(FUENTES, f), nombre)
    creditos = ["SONIDOS DEL PACK ENVOLVENTE", "",
                "Los sonidos de este pack son de dominio público o tienen licencia CC0: se pueden usar, cambiar y repartir sin pedir permiso.",
                "Parte de ellos vienen del pack realista del juego, montado con sonidos libres de kenney.nl y opengameart.org.",
                "Las grabaciones añadidas en este pack son estas:", ""]
    for nombre in sorted(nuevos):
        f = fuentes.get(nombre, {})
        creditos.append(f"{nombre}: {f.get('titulo_original', 'sin título')}, de {f.get('autor', 'autor desconocido')}. Licencia {f.get('licencia', 'CC0')}. {f.get('pagina', '')}".rstrip())
    with open(os.path.join(DESTINO, "CREDITOS.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(creditos) + "\n")
    estereo = sum(1 for v in nuevos.values() if v["canales"] == 2)
    meta = {"nombre": "Envolvente",
            "descripcion": "Los sonidos del pack realista, con ambientes de barrio grabados en estéreo. Los sonidos de orientación son los de serie.",
            "licencia": "CC0, dominio público", "sonidos": copiados, "ambientes_en_estereo": estereo,
            "autor": "Montado para Puerto Bravo con sonidos libres. El detalle está en CREDITOS.txt", "igualar": False}
    json.dump(meta, open(os.path.join(DESTINO, "pack.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return copiados, nuevos


if __name__ == "__main__":
    copiados, nuevos = crear()
    print(f"Pack envolvente: {copiados} sonidos del pack realista y {len(nuevos)} grabaciones nuevas.")
    for nombre, v in sorted(nuevos.items()):
        print(f"  {nombre}: {'estéreo' if v['canales'] == 2 else 'mono'}, {v['segundos']} s")
    if not nuevos:
        print("  No hay grabaciones nuevas en adjuntos\\packs\\fuentes_envolvente: el pack sería igual que el realista.")
