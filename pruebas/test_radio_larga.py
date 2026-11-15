"""Fallo real de la 1.6.2: una grabación de una hora en «Mi música» colgaba el juego y el ordenador entero.

La radio cargaba la canción entera en memoria: unos 128 megas de pico por cada minuto de audio. Una hora eran más de
siete gigas. Ahora las canciones largas se leen y suenan por tramos de un minuto.
"""
import os
import tracemalloc

import numpy as np
import soundfile as sf

from juego import musica, sintesis
from juego.audio import SR, Mezclador
from juego.musica import Radio


def _grabar(ruta, minutos, hz=220.0, sr=48000):
    """Un archivo largo y pequeño en disco: un tono continuo, para poder comprobar que no hay cortes."""
    n = sr * 10
    with sf.SoundFile(ruta, "w", samplerate=sr, channels=2, format="OGG", subtype="VORBIS") as f:
        for k in range(int(minutos * 6)):
            t = (np.arange(n) + k * n) / sr
            bloque = np.stack([0.3 * np.sin(2 * np.pi * hz * t), 0.3 * np.sin(2 * np.pi * hz * t)], axis=1).astype(np.float32)
            for i in range(0, n, 24000):
                f.write(bloque[i:i + 24000])


def _radio(tmp_path, archivos):
    carpeta = str(tmp_path / "radio")
    os.makedirs(os.path.join(carpeta, "mi_musica"))
    for nombre, minutos in archivos:
        _grabar(os.path.join(carpeta, "mi_musica", nombre), minutos)
    m = Mezclador(dispositivo=False)
    r = Radio(m, carpeta)
    r.esperar()
    return m, r, next(k for k, e in enumerate(r.emisoras) if e["id"] == "usuario")


def _esperar_carga(r):
    for _ in range(400):
        if r._listo is not None or not r.pendiente:
            break
        r._cargador.join(0.05)
    r.actualizar(0.0)


def test_leer_solo_un_tramo_de_un_archivo(tmp_path):
    ruta = str(tmp_path / "tres.ogg")
    _grabar(ruta, 3)
    assert abs(sintesis.duracion_audio(ruta) - 180.0) < 0.5 and sintesis.duracion_audio(str(tmp_path / "no_existe.ogg")) == 0.0
    entero = sintesis.leer_audio(ruta, mono=False)
    assert abs(len(entero) / SR - 180.0) < 0.5
    tramo = sintesis.leer_audio(ruta, mono=False, desde=60.0, maximo=10.0)
    assert abs(len(tramo) / SR - 10.0) < 0.05 and tramo.ndim == 2
    assert np.allclose(tramo[2000:4000], entero[60 * SR + 2000:60 * SR + 4000], atol=0.02)          # es el mismo sonido
    assert len(sintesis.leer_audio(ruta, mono=True, desde=175.0, maximo=60.0)) / SR < 5.5          # pedir de más no falla
    assert sintesis.MAX_EFECTO == 60


def test_una_hora_de_radio_no_llena_la_memoria(tmp_path):
    m, r, usuario = _radio(tmp_path, [("una_hora.ogg", 62)])
    tracemalloc.start()
    texto = r.sintonizar(usuario)
    assert texto.startswith("Mi música: una hora")
    _esperar_carga(r)
    actual, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert r.canal is not None and not r.canal.fin and r._larga is not None and r._larga["total"] == 62
    assert pico < 400 * 1048576, f"pico de {pico // 1048576} megas"            # antes: unos 8000
    assert actual < 120 * 1048576, f"quedan {actual // 1048576} megas"
    assert abs(len(m.sonidos[r._nombre_pista]) / SR - (musica.TROZO + musica.SOLAPE)) < 0.1      # en memoria, un minuto
    nivel = musica.nivel_musica(m.sonidos[r._nombre_pista][SR:-SR])
    assert abs(nivel - musica.NIVEL_RADIO) < 0.03                              # y al nivel de las demás canciones
    r.apagar()
    assert r._larga is None and r._prox is None


def test_la_cancion_larga_suena_seguida_sin_cortes(tmp_path):
    m, r, usuario = _radio(tmp_path, [("siete.ogg", 7)])
    m.vols["maestro"], m.vols["musica"] = 1.0, 1.0
    r.sintonizar(usuario)
    _esperar_carga(r)
    assert r._larga["total"] == 7 and r._larga["trozo"] == 0
    paso = 2048
    dt = paso / SR
    oido, tramos = [], [0]
    for k in range(int(7.3 * 60 / dt)):
        if r.pendiente and r._listo is None:
            r._cargador.join(2)
        lector = getattr(r, "_lector", None)
        if r._leyendo and lector is not None:
            lector.join(2)
        r.actualizar(dt)
        bloque = m.render(paso)
        oido.append(float(np.sqrt(np.mean(bloque[:, 0].astype(np.float64) ** 2))))
        if r._larga is not None and r._larga["trozo"] != tramos[-1]:
            tramos.append(r._larga["trozo"])
        if len(tramos) > 7:
            break
    assert tramos[:8] == [0, 1, 2, 3, 4, 5, 6, 0], tramos                      # todos los tramos, en orden, y al acabar vuelve a empezar
    oido = np.array(oido[20:int(6.9 * 60 / dt)])                               # sin el arranque ni el final
    medio = float(np.median(oido))
    assert medio > 0.05
    assert oido.min() > 0.8 * medio and oido.max() < 1.2 * medio, (oido.min() / medio, oido.max() / medio)       # ni huecos ni golpes en las costuras
    m.actualizar()                                                             # el juego lo hace en cada fotograma
    assert len([c for c in m.canales if not c.fin]) <= 2                       # los tramos ya tocados no se quedan sonando


def test_las_canciones_normales_siguen_como_siempre(tmp_path):
    m, r, usuario = _radio(tmp_path, [("a_corta.ogg", 1), ("b_larga.ogg", 6)])
    r.sintonizar(usuario)
    _esperar_carga(r)
    assert r._larga is None and abs(len(m.sonidos[r._nombre_pista]) / SR - 60.0) < 0.5      # la corta, entera
    texto = r.siguiente_pista()
    assert texto == "Mi música: b larga"
    _esperar_carga(r)
    assert r._larga is not None and r._larga["total"] == 6                     # la larga, por tramos
    texto = r.siguiente_pista()
    _esperar_carga(r)
    assert texto == "Mi música: a corta" and r._larga is None and r._prox is None
