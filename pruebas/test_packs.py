"""Packs de sonidos, igualado de volumen y ajuste de cada sonido."""
import json
import os
import shutil

import numpy as np
import pygame
import pytest

from juego import packs, rutas, sintesis
from juego.menus import Menu

SR = sintesis.SR


def _tono(amplitud, segundos=0.6, hz=440):
    t = np.arange(int(SR * segundos)) / SR
    return (amplitud * np.sin(2 * np.pi * hz * t)).astype(np.float32)


@pytest.fixture
def pack_prueba():
    ruta = os.path.join(packs.carpeta_packs(), "_prueba")
    shutil.rmtree(ruta, ignore_errors=True)
    os.makedirs(ruta)
    sintesis.escribir_wav(os.path.join(ruta, "claxon.wav"), _tono(0.01))          # casi inaudible
    sintesis.escribir_wav(os.path.join(ruta, "paso_acera0.wav"), _tono(0.99, 0.1))   # atronador
    sintesis.escribir_wav(os.path.join(ruta, "sonido_nuevo_de_mod.wav"), _tono(0.3))
    json.dump({"nombre": "Pack de prueba", "descripcion": "Para las pruebas", "volumenes": {"claxon": 0.5}}, open(os.path.join(ruta, "pack.json"), "w", encoding="utf-8"))
    yield "_prueba"
    shutil.rmtree(ruta, ignore_errors=True)


def test_medir_e_igualar():
    ref = [0.2, 0.5]
    for amplitud in (0.005, 0.1, 0.9):
        d = packs.igualar(_tono(amplitud), ref)
        assert abs(packs.nivel(d) - 0.2) < 0.01
    # un sonido con mucho silencio alrededor se mide por su tramo fuerte
    largo = np.concatenate([np.zeros(SR * 2, np.float32), _tono(0.5, 0.4), np.zeros(SR * 2, np.float32)])
    assert packs.nivel(largo) > 0.3
    # nunca satura: un chasquido muy corto no puede subir sin límite
    clic = np.zeros(SR, np.float32)
    clic[100:110] = 0.5
    assert packs.pico(packs.igualar(clic, [0.3, 0.6])) <= 0.981


def test_pack_se_carga_igualado(app, pack_prueba):
    refs = packs.referencias(packs.carpeta_defecto())
    original = app.mez.sonidos["claxon"].copy()
    otro = app.mez.sonidos["motor_coche"].copy()
    assert any(p["id"] == pack_prueba and p["nombre"] == "Pack de prueba" and p["n"] == 3 for p in packs.listar())
    app.cfg["pack_sonidos"] = pack_prueba
    info = app.recargar_sonidos()
    assert info["pack"] == pack_prueba and info["del_pack"] == 3
    claxon = app.mez.sonidos["claxon"]
    assert len(claxon) != len(original)                                          # es el del pack
    assert abs(packs.nivel(claxon) - refs["claxon"][0] * 0.5) < refs["claxon"][0] * 0.06      # igualado, y luego el 0,5 del pack.json
    paso = app.mez.sonidos["paso_acera0"]
    assert abs(packs.nivel(paso) - refs["paso_acera0"][0]) < refs["paso_acera0"][0] * 0.06
    assert np.array_equal(app.mez.sonidos["motor_coche"], otro)                  # lo que el pack no trae no cambia
    assert "sonido_nuevo_de_mod" in app.mez.sonidos
    # sin igualar, entra tal cual
    app.cfg["igualar_volumen"] = False
    app.recargar_sonidos()
    assert packs.pico(app.mez.sonidos["paso_acera0"]) > 0.9
    # volver al original
    app.cfg["igualar_volumen"] = True
    app.cfg["pack_sonidos"] = ""
    app.recargar_sonidos()
    assert np.array_equal(app.mez.sonidos["claxon"], original)
    # un pack que ya no existe no rompe nada
    app.cfg["pack_sonidos"] = "no_existe"
    assert app.recargar_sonidos()["del_pack"] == 0


def test_sonido_sustituido_a_mano_se_iguala(app):
    carpeta = packs.carpeta_defecto()
    ruta = os.path.join(carpeta, "gaviota.wav")
    copia = open(ruta, "rb").read()
    refs = packs.referencias(carpeta)
    try:
        sintesis.escribir_wav(ruta, _tono(0.02, 1.0))
        info = app.recargar_sonidos()
        assert info["igualados"] >= 1
        assert abs(packs.nivel(app.mez.sonidos["gaviota"]) - refs["gaviota"][0]) < refs["gaviota"][0] * 0.06
    finally:
        open(ruta, "wb").write(copia)
    assert app.recargar_sonidos()["igualados"] == 0                              # los originales no se tocan


def _ir(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu)
    m.i = next(k for k, o in enumerate(m.opciones) if texto.lower() in o.texto.lower())
    return m


def test_elegir_pack_y_ajustar_un_sonido_en_opciones(robot, pack_prueba):
    app = robot.app
    from juego import menus_juego
    menus_juego.opciones(app)
    _ir(robot, "Sonido y música")
    robot.tecla(pygame.K_RETURN)
    m = _ir(robot, "Pack de sonidos")
    assert "por defecto" in m.opciones[m.i].texto
    visto = set()
    for _ in range(len(packs.listar()) + 1):
        robot.tecla(pygame.K_RIGHT)
        visto.add(app.cfg["pack_sonidos"])
    assert pack_prueba in visto and "" in visto and app.cfg["pack_sonidos"] == ""
    while app.cfg["pack_sonidos"] != pack_prueba:
        robot.tecla(pygame.K_RIGHT)
    assert "Pack de prueba, 3 sonidos" in m.opciones[m.i].texto and app.info_sonidos["pack"] == pack_prueba
    while app.cfg["pack_sonidos"]:
        robot.tecla(pygame.K_LEFT)
    # ajustar un sonido concreto
    _ir(robot, "Ajustar el volumen de cada sonido")
    robot.tecla(pygame.K_RETURN)
    _ir(robot, "Vehículos")
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.ayuda and "Archivo claxon." in o.ayuda)
    antes = packs.nivel(app.mez.sonidos["claxon"])
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_RIGHT)
    assert app.cfg["vol_sonidos"]["claxon"] == 1.2 and "120 por ciento" in m.opciones[m.i].texto
    assert abs(packs.nivel(app.mez.sonidos["claxon"]) / antes - 1.2) < 0.02
    robot.tecla(pygame.K_RETURN)                                                 # Intro lo hace sonar, no lo cambia
    assert app.cfg["vol_sonidos"]["claxon"] == 1.2
    app.recargar_sonidos()                                                       # el ajuste sobrevive a una recarga
    assert abs(packs.nivel(app.mez.sonidos["claxon"]) / antes - 1.2) < 0.02
    robot.tecla(pygame.K_LEFT)
    robot.tecla(pygame.K_LEFT)
    assert "claxon" not in app.cfg["vol_sonidos"]
    assert abs(packs.nivel(app.mez.sonidos["claxon"]) / antes - 1.0) < 0.02
    app.cfg["vol_sonidos"].clear()
    app.cfg.guardar()


def test_los_packs_instalados_son_validos(app):
    """Cada archivo de cada pack de data/packs es un sonido del juego, se lee y queda al nivel del original."""
    refs = packs.referencias(packs.carpeta_defecto())
    assert not any(p["id"] == rutas.POR_DEFECTO for p in packs.listar())
    assert not [f for f in os.listdir(rutas.PACKS) if f.lower().endswith(rutas.EXT_AUDIO)], "en data/sonidos solo debe haber subcarpetas"
    for pk in packs.listar():
        if pk["id"].startswith("_"):
            continue
        ruta = os.path.join(packs.carpeta_packs(), pk["id"])
        app.cfg["pack_sonidos"] = pk["id"]
        info = app.recargar_sonidos()
        assert info["del_pack"] == pk["n"] > 0
        assert set(packs._archivos(ruta)) == set(refs), f"{pk['id']} no trae todos los sonidos del juego"
        for nombre in packs._archivos(ruta):
            assert nombre in refs, f"{pk['id']}: {nombre} no es un sonido del juego"
            d = app.mez.sonidos[nombre]
            r = packs.nivel(d) / refs[nombre][0]
            assert 0.78 < r < 1.28 or (r <= 1.0 and packs.pico(d) > 0.95), f"{pk['id']}/{nombre}: nivel {r:.2f}"
            if sintesis.es_bucle(nombre):
                assert len(d) >= SR * 0.3, f"{pk['id']}/{nombre}: bucle demasiado corto"
            else:
                assert abs(float(d[-1])) < 0.2 and abs(float(d[0])) < 0.2, f"{pk['id']}/{nombre}: empieza o acaba con chasquido"
        assert os.path.exists(os.path.join(ruta, "CREDITOS.txt"))
    app.cfg["pack_sonidos"] = ""
    app.recargar_sonidos()
