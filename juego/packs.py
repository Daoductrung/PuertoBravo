"""Packs de sonidos e igualado de volumen.

Todos los sonidos viven en data/sonidos, cada juego de sonidos en su subcarpeta:

    data/sonidos/por_defecto   los de serie; el juego los genera y repone el que falte o se borre
    data/sonidos/realista      un pack
    data/sonidos/mi_pack       otro pack

Un pack es una carpeta con archivos de audio que se llaman igual que los sonidos del juego
(claxon.wav, paso_acera0.ogg...). No hace falta que los traiga todos: los que falten suenan con
el sonido por defecto. Puede llevar un archivo pack.json opcional:

    {"nombre": "Realista", "autor": "...", "licencia": "CC0", "descripcion": "...",
     "igualar": true, "volumenes": {"claxon": 0.8}}

Igualado de volumen: las grabaciones vienen cada una a un volumen distinto. El juego sabe lo fuerte
que suena cada sonido original (data/sonidos/por_defecto/_niveles.json) y, al cargar un sonido cambiado, sea de
un pack o un archivo sustituido a mano en por_defecto, lo lleva a ese mismo nivel. Así un pack no
puede dejar los pasos más fuertes que los disparos ni una baliza inaudible.
Encima de eso, el jugador puede subir o bajar cada sonido desde Opciones (cfg["vol_sonidos"]).
"""
import json
import os

import numpy as np

from . import cifrado, rutas, sintesis

SR = sintesis.SR
VENTANA = int(0.3 * SR)
AJUSTE_MIN, AJUSTE_MAX = 0.3, 2.0


def nivel(d):
    """Lo fuerte que suena: la media cuadrática del tramo de 0,3 segundos más intenso.

    Medir solo el tramo más fuerte hace que un disparo con mucha cola o una grabación con silencio
    alrededor no salgan perjudicados frente a un sonido compacto.
    """
    d = np.asarray(d, dtype=np.float64)
    if d.ndim > 1:
        d = d.mean(axis=1)
    n = len(d)
    if n == 0:
        return 0.0
    if n <= VENTANA:
        return float(np.sqrt(np.mean(d * d)))
    c = np.concatenate(([0.0], np.cumsum(d * d)))
    salto = VENTANA // 4
    sumas = c[VENTANA::salto] - c[:-VENTANA:salto]
    return float(np.sqrt(max(0.0, sumas.max()) / VENTANA))


def pico(d):
    return float(np.max(np.abs(d))) if len(d) else 0.0


def igualar(d, ref):
    """Devuelve el sonido llevado al nivel de referencia, sin dejar que sature."""
    nv = nivel(d)
    if nv < 1e-6 or not ref or ref[0] < 1e-6:
        return d
    g = ref[0] / nv
    p = pico(d) * g
    if p > 0.98:
        g *= 0.98 / p
    return (d * g).astype(np.float32)


def referencias(carpeta, originales=None):
    """Nivel y pico de cada sonido original. Se calcula una vez y se guarda en _niveles.json."""
    datos = _leer(carpeta, "_niveles")
    if datos and datos.get("version") == sintesis.VERSION_CACHE and datos.get("niveles"):
        return datos["niveles"]
    originales = originales or sintesis.generar()
    niveles = {k: [round(nivel(v), 6), round(pico(v), 6)] for k, v in originales.items()}
    try:
        cifrado.escribir_json(os.path.join(carpeta, "_niveles" + (rutas.EXT_DATOS if cifrado.COMPILADO else ".json")), {"version": sintesis.VERSION_CACHE, "niveles": niveles})
    except OSError:
        pass
    return niveles


def carpeta_packs():
    rutas.carpeta_sonidos()
    return rutas.PACKS


def carpeta_defecto():
    return rutas.carpeta_sonidos()


def _leer(carpeta, base):
    """Lee carpeta/base.json o carpeta/base.pbd (la forma protegida del juego compilado). None si no hay o no vale."""
    for ext in (".json", rutas.EXT_DATOS):
        ruta = os.path.join(carpeta, base + ext)
        if os.path.exists(ruta):
            try:
                d = cifrado.leer_json(ruta)
                return d if isinstance(d, dict) else None
            except (OSError, ValueError):
                continue
    return None


def _meta(ruta):
    return _leer(ruta, "pack") or {}


def _archivos(ruta):
    out = {}
    try:
        for f in sorted(os.listdir(ruta)):
            nombre, ext = os.path.splitext(f)
            if ext.lower() in rutas.EXT_AUDIO and nombre not in out:
                out[nombre] = os.path.join(ruta, f)
    except OSError:
        pass
    return out


def listar():
    """Packs instalados: lista de dicts con id, nombre, descripcion y número de sonidos."""
    out = []
    base = carpeta_packs()
    for d in sorted(os.listdir(base)):
        ruta = os.path.join(base, d)
        if not os.path.isdir(ruta) or d == rutas.POR_DEFECTO:
            continue
        n = len(_archivos(ruta))
        if n:
            m = _meta(ruta)
            out.append({"id": d, "nombre": str(m.get("nombre") or d.replace("_", " ")), "descripcion": str(m.get("descripcion") or ""), "n": n})
    return out


def _lector(archivo, ref, vol_pack, vol_jugador):
    """La función que lee un ambiente largo cuando hace falta, con los mismos ajustes que si se cargara al arrancar."""
    def leer():
        d = sintesis.leer_audio(archivo, mono=False, maximo=sintesis.MAX_FONDO)
        if ref is not None:
            d = igualar(d, ref)
        try:
            d = d * float(vol_pack)
        except (TypeError, ValueError):
            pass
        if isinstance(vol_jugador, (int, float)):
            d = d * max(AJUSTE_MIN, min(AJUSTE_MAX, float(vol_jugador)))
        return d
    return leer


def cargar(mez, cfg):
    """Carga los sonidos del juego, el pack elegido encima y los ajustes del jugador.

    Devuelve un dict con lo que ha hecho: {"pack": id o "", "del_pack": n, "igualados": n}.
    """
    carpeta = carpeta_defecto()
    S = sintesis.cargar(mez, carpeta)
    hacer = bool(cfg["igualar_volumen"])
    refs = referencias(carpeta) if hacer else {}
    info = {"pack": "", "del_pack": 0, "igualados": 0}
    diferidos = {}
    if hacer:
        for nombre, d in list(S.items()):
            ref = refs.get(nombre)
            if ref and ref[0] > 1e-6:
                r = nivel(d) / ref[0]
                if r < 0.8 or r > 1.25:               # más de dos decibelios de diferencia: es un sonido cambiado
                    S[nombre] = igualar(d, ref)
                    info["igualados"] += 1
    pack = cfg["pack_sonidos"]
    ruta = os.path.join(carpeta_packs(), pack) if pack else ""
    if pack and pack != rutas.POR_DEFECTO and os.path.isdir(ruta):
        m = _meta(ruta)
        vol = m.get("volumenes") if isinstance(m.get("volumenes"), dict) else {}
        for nombre, archivo in _archivos(ruta).items():
            fondo = sintesis.es_fondo(nombre)
            if fondo and nombre in S and os.path.getsize(archivo) > 200000:
                # Un ambiente largo: no se carga hasta que suene. Once a la vez son unos doscientos megas de memoria.
                diferidos[nombre] = _lector(archivo, refs.get(nombre) if hacer and m.get("igualar", True) else None,
                                            vol.get(nombre, 1.0), cfg["vol_sonidos"].get(nombre))
                info["del_pack"] += 1
                continue
            try:
                d = sintesis.leer_audio(archivo, mono=not fondo, maximo=sintesis.MAX_FONDO if fondo else None)
            except Exception:
                continue
            if len(d) <= 8:
                continue
            if hacer and m.get("igualar", True) and nombre in refs:
                d = igualar(d, refs[nombre])
                info["igualados"] += 1
            try:
                d = d * float(vol.get(nombre, 1.0))
            except (TypeError, ValueError):
                pass
            S[nombre] = d
            info["del_pack"] += 1
        info["pack"] = pack
    for nombre, f in cfg["vol_sonidos"].items():
        if nombre in S and isinstance(f, (int, float)):
            S[nombre] = S[nombre] * max(AJUSTE_MIN, min(AJUSTE_MAX, float(f)))
    for k, v in S.items():
        mez.registrar(k, v)
    mez.diferidos.clear()
    mez._dif_estado.clear()
    for k, leer in diferidos.items():
        mez.diferir(k, leer)
    info["bajo_demanda"] = len(diferidos)
    return info


def ajustar(mez, cfg, nombre, delta):
    """Sube o baja un sonido concreto un diez por ciento. Devuelve el ajuste nuevo."""
    viejo = float(cfg["vol_sonidos"].get(nombre, 1.0))
    nuevo = round(max(AJUSTE_MIN, min(AJUSTE_MAX, viejo + 0.1 * delta)), 1)
    if nuevo != viejo and nombre in mez.sonidos:
        mez.registrar(nombre, mez.sonidos[nombre] * (nuevo / viejo))
        if abs(nuevo - 1.0) < 0.01:
            cfg["vol_sonidos"].pop(nombre, None)
        else:
            cfg["vol_sonidos"][nombre] = nuevo
    return nuevo
