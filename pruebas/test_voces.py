"""Voces grabadas en las escenas y el mod grande de Bahía del Ocaso."""
import os

import numpy as np
import pygame

from juego import voces
from juego.menus import Dialogo
from juego.sintesis import escribir_wav


def _grabar(carpeta, nombre, segundos=0.3):
    os.makedirs(carpeta, exist_ok=True)
    t = np.arange(int(44100 * segundos)) / 44100
    escribir_wav(os.path.join(carpeta, nombre + ".wav"), (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32))
    voces.refrescar()


def test_voces_grabadas_en_un_dialogo(robot, monkeypatch, tmp_path):
    carpeta = str(tmp_path / "voces")
    monkeypatch.setattr(voces, "carpeta", lambda: carpeta)
    voces.refrescar()
    assert voces.de_paso("oc01", 0, 3) is None                       # sin carpeta no pasa nada
    _grabar(os.path.join(carpeta, "bahia"), "OC01_1_2")              # vale en subcarpetas y sin mirar mayúsculas
    lista = voces.de_paso("oc01", 0, 3)
    assert lista[0] is None and lista[1].endswith("OC01_1_2.wav") and lista[2] is None
    app = robot.app
    app.cfg["voces_grabadas"] = True
    d = Dialogo(app, [("Custodia", "Primera."), ("Custodia", "Segunda."), ("Narrador", "Tercera.")], voces=lista)
    app.abrir(d)
    assert d.canal is None and "Custodia: Primera." in app.voz.registro[-1]          # sin grabación: lector de pantalla
    robot.tecla(pygame.K_RETURN)
    assert d.canal is not None and d.canal.activo and app.voz.registro[-1] == "Custodia: Segunda."   # suena la grabación; el texto queda para braille e historial
    canal = d.canal
    robot.tecla(pygame.K_RETURN)
    assert canal.parando and d.canal is None and app.voz.registro[-1] == "Tercera."  # al avanzar, la grabación se corta
    robot.tecla(pygame.K_LEFT)
    assert d.canal is not None                                                         # y al volver atrás, suena otra vez
    app.cfg["voces_grabadas"] = False                                                  # con la opción apagada, siempre el lector
    robot.tecla(pygame.K_UP)
    assert d.canal is None
    app.cfg["voces_grabadas"] = True
    robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is not d
    # un archivo que no es audio no rompe la escena
    with open(os.path.join(carpeta, "oc01_1_1.ogg"), "wb") as f:
        f.write(b"esto no es un ogg")
    voces.refrescar()
    d = Dialogo(app, [("Custodia", "Primera.")], voces=voces.de_paso("oc01", 0, 1))
    app.abrir(d)
    assert d.canal is None and "Custodia: Primera." in app.voz.registro[-1]
    robot.tecla(pygame.K_ESCAPE)


def test_guion_de_voces(monkeypatch, tmp_path):
    carpeta = str(tmp_path / "voces")
    monkeypatch.setattr(voces, "carpeta", lambda: carpeta)
    _grabar(carpeta, "x1_1_1")
    misiones = [{"id": "x1", "titulo": "Prueba", "pasos": [
        {"tipo": "dialogo", "lineas": [["Ana", "Hola."], ["Narrador", "Silencio."]]}, {"tipo": "ir", "lugar": "a"},
        {"tipo": "dialogo", "lineas": [{"quien": "Ana", "texto": "Adiós."}]}]}, {"id": "x2", "titulo": "Sin diálogo", "pasos": [{"tipo": "ir"}]}]
    g = voces.guion(misiones, "Mi mod")
    assert "x1_1_1  GRABADA\nAna: Hola." in g and "x1_1_2\nNarrador: Silencio." in g and "x1_3_1\nAna: Adiós." in g
    assert "x2" not in g and "Total: 3 frases, 1 grabadas." in g and "Ana 2" in g


def test_la_mision_usa_las_voces(robot, monkeypatch, tmp_path):
    carpeta = str(tmp_path / "voces")
    monkeypatch.setattr(voces, "carpeta", lambda: carpeta)
    _grabar(carpeta, "oc01_1_1")
    p = robot.nueva_partida()
    m = next(x for x in p.datos["misiones"] if x["id"] == "oc01")
    p.iniciar_mision(m)
    d = robot.app.pila[-1]
    assert isinstance(d, Dialogo) and d.voces and d.voces[0] and d.canal is not None
    assert robot.app.voz.registro[-1].startswith("Custodia: ¿Vienes por el anuncio?")
    robot.tecla(pygame.K_ESCAPE)
    # con la opción apagada, la escena la lee el lector, como siempre. El personaje ya no las apaga: cada uno tiene las suyas
    assert p.voces_activas()
    p.j.personaje = "sam"
    assert p.voces_activas()
    p.j.personaje = "dani"
    p.cfg["voces_grabadas"] = False
    assert not p.voces_activas()
    p.cfg["voces_grabadas"] = True


def test_bahia_del_ocaso(robot):
    p = robot.nueva_partida()
    m = p.mapas["bahia_ocaso"]
    assert m.tipo == "ciudad" and m.nombre == "Bahía del Ocaso" and len(m.barrios) == 6 and len(m.lugares) >= 50
    tipos = {l.tipo for l in m.lugares.values()}
    assert {"hospital", "comisaria", "banco", "taller", "armeria", "estacion", "salida", "embarcadero", "helipuerto", "casa", "empleo"} <= tipos
    for i in range(m.NX - 1):                                     # todas las manzanas tienen barrio
        for j in range(m.NY - 1):
            assert (i, j) in m._barrio_de
    ms = [x for x in p.datos["misiones"] if x["id"].startswith("oc")]
    historia = [x for x in ms if x["capitulo"] in (40, 41, 42, 43)]
    assert len(historia) == 21 and len(ms) == 34
    ids = {x["id"] for x in p.datos["misiones"]}
    for x in ms:                                                  # la cadena de la historia no tiene eslabones sueltos
        assert set(x["requiere"]) <= ids
    assert p.mapas["puerto_bravo"].lugares["pb_salida_ocaso"].d["a_mapa"] == "bahia_ocaso"
    assert {"oc_cisterna", "oc_rebajado", "oc_ranchera", "oc_vigia", "oc_lanchon"} <= set(p.datos["vehiculos"] if isinstance(p.datos["vehiculos"], dict) else {v["id"] for v in p.datos["vehiculos"]})
    # se llega por carretera y se pueden conquistar sus barrios
    l = m.lugares["oc_garaje"]
    p.cambiar_mapa("bahia_ocaso", l.x, l.y)
    assert p.mundo.id == "bahia_ocaso" and p.mundo.barrio(*p.pos())["id"] == "oc_cauce"
    robot.frames(30)


def test_voces_de_serie_y_preferencia_del_jugador(monkeypatch, tmp_path):
    """El juego trae voces para Bahía del Ocaso; si el jugador pone la suya con el mismo nombre, gana la suya."""
    voces.refrescar()
    de_serie = voces.buscar("oc01", 0, 0)
    assert de_serie and os.path.join("voces", "bahia_del_ocaso_es") in de_serie
    import json
    from juego import cifrado, rutas
    mod = cifrado.leer_json(os.path.join(rutas.MODS, "bahia_del_ocaso.json"))
    frases = sum(len(p["lineas"]) for m in mod["misiones"] for p in m["pasos"] if p["tipo"] == "dialogo")
    con_voz = sum(1 for m in mod["misiones"] for k, p in enumerate(m["pasos"]) if p["tipo"] == "dialogo" for n in range(len(p["lineas"])) if voces.buscar(m["id"], k, n))
    assert frases >= 107 and con_voz >= 100
    from juego.sintesis import leer_audio
    assert len(leer_audio(de_serie, mono=False)) > 44100                      # se puede leer y dura más de un segundo
    from juego import actualizador
    propia = voces.carpeta_propias()
    assert propia.endswith(os.path.join("voces", "propias")) and "propias" in actualizador.INTOCABLES and "voces" not in actualizador.INTOCABLES
    import shutil
    try:
        _grabar(propia, "oc01_1_1")
        voces.refrescar()
        assert voces.buscar("oc01", 0, 0).startswith(propia) and os.path.join("voces", "bahia_del_ocaso_es") in voces.buscar("oc01", 0, 1)
    finally:
        shutil.rmtree(propia, ignore_errors=True)
    # la carpeta de las versiones anteriores ya no se usa: si queda, se borra al arrancar
    vieja = os.path.join(rutas.DATA, "voces_serie")
    assert not os.path.isdir(vieja) and not voces.limpiar_antigua()
    os.makedirs(vieja)
    open(os.path.join(vieja, "x.ogg"), "wb").close()
    assert voces.limpiar_antigua() and not os.path.isdir(vieja)
    voces.refrescar()


def test_bahia_del_ocaso_se_usa_todo(robot):
    """En la ciudad nueva: se conduce cada vehículo, se dispara cada arma, se come cada plato y el piloto la cruza solo."""
    import math
    p = robot.nueva_partida()
    j = p.j
    m = p.mapas["bahia_ocaso"]
    garaje = m.lugares["oc_garaje"]
    p.cambiar_mapa("bahia_ocaso", garaje.x, garaje.y)
    p.cfg["sucesos"] = False
    for modelo in ("oc_cisterna", "oc_rebajado", "oc_ranchera", "oc_vigia"):
        v = p.crear_vehiculo(modelo, j.x, j.y, 0, None)
        p._subir(v, False, callar=True)
        x0, y0 = v.x, v.y
        robot.frames(90, mantener=(pygame.K_UP,))
        assert math.hypot(v.x - x0, v.y - y0) > 8 and v.vel > 3, modelo
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
    for arma, balas in (("oc_llave", 0), ("oc_remachadora", 16), ("oc_garrafa", 2)):
        p.dar_arma(arma, balas)
        assert arma in j.armas
        j.arma = arma
        p.atacar()
        robot.frames(20)
    from juego import menus_juego
    j.dinero = 500
    for nombre in ("Espeto de sardinas", "Cocido del comedor", "Limonada con hielo"):
        j.salud = 20
        menus_juego._comprar_comida(p, next(c for c in p.datos["comidas"] if c["nombre"] == nombre))()
        assert j.salud > 20
    assert {c["id"] for c in p.datos["carreras"]} >= {"oc_c1", "oc_c2", "oc_c3"}
    # el piloto del GPS cruza la ciudad de punta a punta sin tocar una tecla
    p.limpiar_busqueda()
    v = p.crear_vehiculo("oc_rebajado", j.x, j.y, 0, None)
    p._subir(v, False, callar=True)
    p.cfg["conduccion"], p.cfg["piloto_gps"] = "asistida", True
    destino = m.lugares["oc_armeria"]
    p.gps_a_lugar(destino, callar=True)
    for _ in range(500):
        robot.frames(15)
        if not p.gps:
            break
    assert not p.gps and math.hypot(destino.x - v.x, destino.y - v.y) < 40, robot.dicho()[-300:]
    p.cfg["piloto_gps"] = False


def test_las_voces_de_la_version_llegan_por_el_puente_y_sustituyen_a_las_anteriores(monkeypatch, tmp_path):
    """Las voces viajan dentro de data/datos y el juego, al arrancar, las pone en su sitio: pisan a las de la versión
    anterior, se quitan las que ya no vienen, no se tocan las del jugador y el puente se borra."""
    from juego import actualizador
    datos = str(tmp_path / "data")
    monkeypatch.setattr(voces, "carpeta", lambda: os.path.join(datos, "voces"))
    monkeypatch.setattr(voces, "carpeta_puente", lambda: os.path.join(datos, "datos", "voces_puente"))
    assert voces.recoger_puente() == 0                                        # sin puente no pasa nada
    puente = voces.carpeta_puente()
    for sub, nombre in (("historia_principal", "m01_1_1"), ("historia_principal", "m01_1_2"), ("bahia_del_ocaso", "oc01_1_1")):
        os.makedirs(os.path.join(puente, sub), exist_ok=True)
        open(os.path.join(puente, sub, nombre + ".ogg"), "wb").write(b"nueva")
    open(os.path.join(puente, "historia_principal", "m01_1_1@alex.ogg"), "wb").write(b"nueva para alex")
    os.makedirs(os.path.join(datos, "voces", "bahia_del_ocaso"))
    open(os.path.join(datos, "voces", "bahia_del_ocaso", "oc01_1_1.ogg"), "wb").write(b"la de la version anterior")
    open(os.path.join(datos, "voces", "bahia_del_ocaso", "oc99_1_1.ogg"), "wb").write(b"de una frase que ya no existe")
    os.makedirs(os.path.join(datos, "voces", "propias"))
    open(os.path.join(datos, "voces", "propias", "m01_1_1.ogg"), "wb").write(b"del jugador")
    open(os.path.join(datos, "voces", "suelta_1_1.ogg"), "wb").write(b"suelta del jugador")
    os.makedirs(os.path.join(datos, "voces", "mi_mod"))
    open(os.path.join(datos, "voces", "mi_mod", "mm_1_1.ogg"), "wb").write(b"de un mod del jugador")
    assert voces.recoger_puente() == 4
    assert not os.path.isdir(puente)                                          # el puente no deja rastro
    assert open(os.path.join(datos, "voces", "historia_principal", "m01_1_1.ogg"), "rb").read() == b"nueva"
    assert open(os.path.join(datos, "voces", "historia_principal", "m01_1_1@alex.ogg"), "rb").read() == b"nueva para alex"
    assert open(os.path.join(datos, "voces", "bahia_del_ocaso", "oc01_1_1.ogg"), "rb").read() == b"nueva"        # la nueva pisa a la vieja
    assert not os.path.exists(os.path.join(datos, "voces", "bahia_del_ocaso", "oc99_1_1.ogg"))                    # y la que ya no viene, fuera
    assert open(os.path.join(datos, "voces", "propias", "m01_1_1.ogg"), "rb").read() == b"del jugador"
    assert os.path.exists(os.path.join(datos, "voces", "suelta_1_1.ogg")) and os.path.exists(os.path.join(datos, "voces", "mi_mod", "mm_1_1.ogg"))
    voces.refrescar()
    assert voces.buscar("m01", 0, 0).endswith(os.path.join("propias", "m01_1_1.ogg"))        # y la del jugador sigue mandando
    assert voces.recoger_puente() == 0
    # el nombre del puente no choca con nada de lo que el actualizador antiguo dejaba sin tocar
    antiguas = ("partidas", "config", "mi_musica", "actualizacion", "logs", "ia_local", "voces")
    assert "voces_puente" not in antiguas and "datos" not in antiguas and "voces_puente" not in actualizador.INTOCABLES
