"""La música: se usan todas las pistas que haya en cada carpeta y todas quedan al mismo nivel."""
import os
import random

import numpy as np
import soundfile as sf

from juego import musica
from juego.audio import Mezclador

SR = 44100


def _cancion(ruta, amplitud, segundos=3.0, hz=220):
    t = np.arange(int(SR * segundos)) / SR
    d = amplitud * np.sin(2 * np.pi * hz * t)
    sf.write(ruta, np.stack([d, d], axis=1).astype("float32"), SR)


def test_todas_las_pistas_de_cada_carpeta_entran_y_quedan_niveladas(tmp_path):
    carpeta = str(tmp_path / "musica")
    for situacion in musica.AMBIENTES:
        os.makedirs(os.path.join(carpeta, situacion))
        open(os.path.join(carpeta, situacion, "_originales.txt"), "w").write("x")      # sin piezas de serie: solo las nuestras
        _cancion(os.path.join(carpeta, situacion, f"{situacion}_5.wav"), 0.9)          # atronadora
        _cancion(os.path.join(carpeta, situacion, "una mia cualquiera.wav"), 0.004)    # casi inaudible
        _cancion(os.path.join(carpeta, situacion, f"{situacion}_27.wav"), 0.2, hz=330)
    mez = Mezclador(dispositivo=False)
    amb = musica.MusicaAmbiente(mez, carpeta)
    amb.esperar()
    assert not [c for c in mez.sonidos if c.startswith("musica_")]        # al arrancar no se carga ninguna: solo se hace la lista
    for situacion in musica.AMBIENTES:
        claves = [p[0] for p in amb.pistas[situacion]]
        assert len(claves) == 3 and f"musica_{situacion}_{situacion}_5" in claves, claves
        for c in claves:
            assert amb.cargar_ahora(c)
            assert abs(musica.nivel_musica(mez.sonidos[c]) - musica.NIVEL_AMBIENTE) < 0.01, c
            amb._soltar(c)
    assert not [c for c in mez.sonidos if c.startswith("musica_")]
    # la rotación pasa por todas, sin repetir la misma dos veces seguidas
    random.seed(4)
    vistas, anterior = set(), None
    for _ in range(40):
        amb._otra("exploracion")
        assert amb.pista != anterior
        anterior = amb.pista
        vistas.add(amb.pista)
    assert len(vistas) == 3
    amb.esperar_carga()
    amb.callar()
    assert not [c for c in mez.sonidos if c.startswith("musica_")]        # las pedidas que no llegaron a sonar se han soltado
    # suena la que toca y, al cambiar de situación, la anterior se suelta de la memoria
    amb.actualizar(0.1, "exploracion", 0.5)
    for h in list(amb.cargando.values()):
        h.join()
    for _ in range(40):
        amb.actualizar(0.1, "exploracion", 0.5)
    sonaba = amb.pista
    assert sonaba in amb.canales and amb.volumen_actual() > 0.3
    amb.actualizar(0.1, "noche", 0.5)
    for h in list(amb.cargando.values()):
        h.join()
    for _ in range(60):
        amb.actualizar(0.1, "noche", 0.5)
    assert amb.pista in amb.canales and sonaba not in amb.canales and sonaba not in mez.sonidos
    amb.callar()
    assert not [c for c in mez.sonidos if c.startswith("musica_")]


def test_la_radio_tambien_se_nivela(tmp_path):
    carpeta = str(tmp_path / "radio")
    os.makedirs(os.path.join(carpeta, "mi_musica"))
    for e in musica.EMISORAS:
        if "estilo" in e:
            _cancion(os.path.join(carpeta, e["id"] + ".wav"), 0.95 if e["id"] == "bravo" else 0.01)
    _cancion(os.path.join(carpeta, "emisora_nueva.wav"), 0.6)
    _cancion(os.path.join(carpeta, "mi_musica", "tema.wav"), 0.02)
    mez = Mezclador(dispositivo=False)
    radio = musica.Radio(mez, carpeta)
    radio.esperar()
    assert "radio_pista" not in mez.sonidos                              # nada cargado hasta que se sintoniza
    for ident in [e["id"] for e in radio.emisoras if "estilo" in e] + ["extra_emisora_nueva", "usuario"]:
        radio.sintonizar(next(k for k, e in enumerate(radio.emisoras) if e["id"] == ident))
        radio.esperar()
        assert radio.canal is not None, ident
        assert abs(musica.nivel_musica(mez.sonidos["radio_pista"]) - musica.NIVEL_RADIO) < 0.012, ident
    radio.apagar()


def test_varias_canciones_por_emisora(tmp_path):
    """bravo.wav, bravo_1.wav y bravo_otra.wav son tres canciones de Bravo FM, no tres emisoras."""
    carpeta = str(tmp_path / "radio")
    os.makedirs(os.path.join(carpeta, "mi_musica"))
    for e in musica.EMISORAS:
        if "estilo" in e:
            _cancion(os.path.join(carpeta, e["id"] + ".wav"), 0.2, 2.5)
    _cancion(os.path.join(carpeta, "bravo_1.wav"), 0.2, 2.5, hz=330)
    _cancion(os.path.join(carpeta, "bravo_otra.wav"), 0.2, 2.5, hz=440)
    mez = Mezclador(dispositivo=False)
    radio = musica.Radio(mez, carpeta)
    radio.esperar()
    assert len(radio.pistas["bravo"]) == 3 and len(radio.pistas["calma"]) == 1
    assert not [e for e in radio.emisoras if e["id"].startswith("extra_")]          # ninguna aparece como emisora aparte
    radio.sintonizar(next(k for k, e in enumerate(radio.emisoras) if e["id"] == "bravo"))
    radio.esperar()
    vistas = {radio.sonando}
    for _ in range(12):                                                  # dejamos pasar canciones: van rotando sin repetir la misma seguida
        anterior = radio.sonando
        for _ in range(40):
            radio.actualizar(0.1)
            if radio.pendiente:
                break
        radio.esperar()
        assert radio.canal is not None and radio.sonando != anterior
        vistas.add(radio.sonando)
    assert len(vistas) == 3
    # una emisora con una sola canción la repite en bucle, sin recargarla
    radio.sintonizar(next(k for k, e in enumerate(radio.emisoras) if e["id"] == "calma"))
    radio.esperar()
    for _ in range(60):
        radio.actualizar(0.1)
    assert not radio.pendiente and radio.canal is not None
    radio.apagar()
    assert radio.canal is None


def test_normalizar_no_satura_ni_toca_el_silencio():
    clic = np.zeros((SR * 2, 2), np.float32)
    clic[1000:1040] = 0.5
    assert float(np.abs(musica.normalizar_musica(clic, 0.15)).max()) <= 0.981
    nada = np.zeros((SR, 2), np.float32)
    assert musica.normalizar_musica(nada, 0.15) is nada
