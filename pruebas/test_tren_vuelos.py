"""Vías de tren que cruzan cada localidad, con trenes que pasan y se oyen, y vuelos a los pueblos y a las islas."""
import glob
import json
import math
import os

import pygame

from juego import menus_extra, menus_lugares, pantallas, rutas, transporte
from juego import mundo as M
from juego.menus import Menu

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ir_a(robot, mapa):
    p = robot.p
    p.cfg["sucesos"] = False
    if p.mundo.id != mapa:
        m = p.mapas[mapa]
        p.cambiar_mapa(mapa, *m.punto_libre(m.ancho / 2, m.alto / 2))
    robot.frames(2)
    return p.mundo


def test_todas_las_estaciones_tienen_su_via(robot):
    p = robot.nueva_partida()
    con = 0
    for m in p.mapas.values():
        est = next((l for l in m.lugares_todos.values() if l.tipo == "tren"), None) if m.tipo != "mar" else None
        if est is None:
            assert getattr(m, "tren_largo", 0.0) == 0.0 or m.tipo == "mar"
            continue
        con += 1
        assert m.tren_eje in ("H", "V") and m.tren_largo > 100, m.id
        ax, ay = m.tren_punto(m.tren_parada)
        assert math.hypot(ax - est.x, ay - est.y) < 16, (m.id, math.hypot(ax - est.x, ay - est.y))      # el andén está junto a la estación
        assert m.en_via_tren(ax, ay) and m.sobre_vias(ax, ay) in ("via", "via_tren")
        assert not m.en_via_tren(ax + 9, ay + 9)
        assert m.tren_donde()
    assert con >= 10
    # queda escrito en los datos, del juego y de los mods, para poder cambiarlo
    archivos = [os.path.join(rutas.DATOS, "ciudad.json")] + sorted(glob.glob(os.path.join(rutas.DATOS, "mapas", "*.json")))
    for ruta in archivos:
        d = json.load(open(ruta, encoding="utf-8"))
        if any(l.get("tipo") == "tren" for l in d.get("lugares", [])):
            assert d.get("tren_eje") in ("H", "V") and isinstance(d.get("tren_n"), int), os.path.basename(ruta)
    for ruta in glob.glob(os.path.join(RAIZ, "data", "mods", "*.json")):
        d = json.load(open(ruta, encoding="utf-8"))
        for mapa in d.get("mapas", []):
            if any(l.get("tipo") == "tren" and l.get("mapa") == mapa["id"] for l in d.get("lugares", [])):
                assert mapa.get("tren_eje") in ("H", "V"), (os.path.basename(ruta), mapa["id"])


def test_la_via_se_puede_escribir_a_mano():
    base = json.load(open(os.path.join(rutas.DATOS, "mapas", "villaseca.json"), encoding="utf-8"))
    c = dict(base, tren_eje="V", tren_n=1)
    m = M.Mundo(c)
    assert (m.tren_eje, m.tren_n) == ("V", 1) and m.tren_largo == m.alto and m.en_via_tren(1 * M.B, m.alto / 2) and m.avenidas[1] in m.tren_donde()
    m = M.Mundo(dict(base, tren_eje="V", tren_n=99))                 # un número imposible: se pone delante de la estación
    assert m.tren_eje == base["tren_eje"] and m.tren_n == base["tren_n"]
    sin = dict(base, transporte=False, lugares=[l for l in base["lugares"] if l["tipo"] != "tren"])
    m = M.Mundo(sin)
    assert m.tren_largo == 0.0 and not m.en_via_tren(10, 10) and m.tren_donde() == ""      # sin estación no hay vía
    from editor import esquema
    campos = {c["k"] for c in esquema.ESQUEMAS["mapa"]["campos"]}
    assert {"tren_eje", "tren_n", "vias"} <= campos
    assert any(c["k"] == "aerodromo" for c in esquema.ESQUEMAS["lugar"]["campos"])


def test_el_tren_pasa_para_en_la_estacion_y_se_oye(robot):
    p = robot.nueva_partida()
    m = _ir_a(robot, "villaseca")
    ax, ay = m.tren_punto(m.tren_parada)
    p.teletransportar(*m.fuera_de_la_via(ax, ay))                   # en la acera, junto al andén
    robot.frames(2)
    assert p.tren is None
    t = transporte.lanzar_tren(p, 1)
    assert t is not None and t["s"] < 0
    visto = {"canal": False, "parado": False, "silbatos": 0, "cerca": 9999.0}
    for _ in range(4000):
        robot.frames(1)
        t = p.tren
        if t is None:
            break
        visto["canal"] = visto["canal"] or t["canal"] is not None
        visto["parado"] = visto["parado"] or t["parado"]
        if t["canal"] is not None:
            visto["cerca"] = min(visto["cerca"], math.hypot(t["canal"].x - p.j.x, t["canal"].y - p.j.y) if hasattr(t["canal"], "x") else 0.0)
    assert p.tren is None, "el tren no llega a salir de la localidad"
    assert visto["canal"] and visto["parado"]                       # se le ha oído y ha parado en el andén
    assert p.j.salud == p.j.salud_max                               # en la acera no pasa nada
    # y sin que nadie lo lance, pasa solo cada cierto tiempo
    p.t_tren = 0.5
    robot.frames(30)
    assert p.tren is not None
    # al cambiar de localidad, se calla
    canal = None
    for _ in range(600):
        robot.frames(1)
        if p.tren and p.tren["canal"] is not None:
            canal = p.tren["canal"]
            break
    _ir_a(robot, "puerto_bravo")
    assert p.tren is None and (canal is None or canal.fin)


def test_pisar_la_via_avisa_y_el_tren_arrolla(robot):
    p = robot.nueva_partida()
    p.cfg["anunciar_superficie"] = True
    m = _ir_a(robot, "villaseca")
    # un punto de la vía lejos del andén, hacia el este
    s = m.tren_parada + 90 if m.tren_parada + 90 < m.tren_largo - 5 else m.tren_parada - 90
    vx, vy = m.tren_punto(s)
    p.teletransportar(*m.fuera_de_la_via(vx, vy))
    robot.frames(3)
    p.j.x, p.j.y = vx, vy
    robot.frames(3)
    assert any(t == "Vías del tren." for t in robot.app.voz.registro[-4:]), robot.dicho()
    salud = p.j.salud
    sentido = 1 if s > m.tren_parada else -1
    t = transporte.lanzar_tren(p, sentido)
    t["s"], t["ha_parado"] = s - sentido * 125, True                # ya ha pasado la estación y viene de frente
    avisado = False
    for _ in range(400):
        robot.frames(1)
        avisado = avisado or any("¡Viene el tren" in x for x in robot.app.voz.registro[-3:])
        if p.j.salud < salud:
            break
    assert avisado, robot.dicho()
    assert p.j.salud <= salud - 30 and not m.en_via_tren(p.j.x, p.j.y), (p.j.salud, robot.dicho())
    assert any("arrollado el tren" in x for x in robot.app.voz.registro[-6:])
    # si te apartas a tiempo, no pasa nada
    p.j.salud = p.j.salud_max
    p.j.x, p.j.y = vx, vy
    t = transporte.lanzar_tren(p, sentido)
    t["s"], t["ha_parado"] = s - sentido * 125, True
    for _ in range(40):
        robot.frames(1)
    p.j.x, p.j.y = m.fuera_de_la_via(vx, vy)
    for _ in range(400):
        robot.frames(1)
    assert p.j.salud == p.j.salud_max


def _opciones(robot):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    return m, [o.texto for o in m.opciones]


def test_aerodromos_en_los_pueblos_y_vuelos_a_todas_partes(robot):
    p = robot.nueva_partida()
    p.j.dinero = 5000
    robot.app.viajes_en_pruebas = True                              # con su trayecto, como lo vive quien juega
    p.cfg["viajes_trayecto"] = True
    pueblos = [m for m in p.mapas.values() if m.tipo == "pueblo" and any(l.tipo == "salida" for l in m.lugares.values())]
    assert len(pueblos) >= 3
    for m in pueblos:
        a = [l for l in m.lugares.values() if l.tipo == "aeropuerto"]
        assert len(a) == 1 and a[0].get("aerodromo") and a[0].nombre.startswith("Aeródromo"), m.id
    for m in p.mapas.values():
        if m.tipo == "ciudad":
            assert [bool(l.get("aerodromo")) for l in m.lugares.values() if l.tipo == "aeropuerto"] == [False], m.id
    # desde el aeropuerto de la ciudad: avión a las ciudades, avioneta a los pueblos, helicóptero a las islas
    _ir_a(robot, "puerto_bravo")
    aer = next(l for l in p.mundo.lugares.values() if l.tipo == "aeropuerto")
    menus_lugares.aeropuerto(p, aer)
    m, textos = _opciones(robot)
    assert any(t.startswith("Vuelo a San Lucero") for t in textos)
    assert any(t.startswith("Avioneta de línea a Villaseca") for t in textos) and any(t.startswith("Avioneta de línea a Cala Brava") for t in textos)
    assert any(t.startswith("Helicóptero de línea a") and "Isla Tortuga" in t for t in textos), textos
    assert not any("Helicóptero de línea" in t and "San Lucero" in t for t in textos)          # a donde hay pista se va en avión
    assert any(t.startswith("Alquilar un helicóptero") for t in textos)
    dinero = p.j.dinero
    m.i = next(k for k, t in enumerate(textos) if t.startswith("Avioneta de línea a Villaseca"))
    robot.tecla(pygame.K_RETURN)
    assert isinstance(robot.app.pila[-1], pantallas.Viaje) and "La avioneta carretea" in robot.app.voz.registro[-1]
    robot.frames(5)
    robot.tecla(pygame.K_RETURN)
    robot.frames(5)
    assert p.mundo.id == "villaseca" and p.j.dinero == dinero - 120 and "Aeródromo de Villaseca" in robot.dicho()
    # desde el aeródromo del pueblo: avionetas a todas partes, helicóptero a las islas, y solo se alquilan avionetas
    aerod = next(l for l in p.mundo.lugares.values() if l.tipo == "aeropuerto")
    assert math.hypot(aerod.x - p.j.x, aerod.y - p.j.y) < 30
    menus_lugares.aeropuerto(p, aerod)
    m, textos = _opciones(robot)
    assert any(t.startswith("Avioneta de línea a Puerto Bravo") for t in textos) and any(t.startswith("Avioneta de línea a Fuentefría") or t.startswith("Avioneta de línea a Fuentefria") for t in textos), textos
    assert not any(t.startswith("Vuelo a ") for t in textos) and not any(t.startswith("Alquilar un helicóptero") for t in textos)
    assert any(t.startswith("Alquilar una avioneta") for t in textos)
    m.i = next(k for k, t in enumerate(textos) if t.startswith("Helicóptero de línea a") and "Isla Tortuga" in t)
    robot.tecla(pygame.K_RETURN)
    robot.frames(5)
    robot.tecla(pygame.K_RETURN)
    robot.frames(5)
    assert p.mundo.id == "isla_tortuga"
    # y desde el helipuerto de la isla, de pasajero, se vuelve también a los pueblos
    heli = next(l for l in p.mundo.lugares.values() if l.tipo == "helipuerto")
    menus_extra.helipuerto(p, heli)
    m, textos = _opciones(robot)
    assert any("Aeródromo de Villaseca" in t for t in textos) and any("Puerto Bravo" in t for t in textos), textos
    assert not any("Aeropuerto de Puerto Bravo" in t for t in textos)                          # en la ciudad aterriza en su helipuerto
    m.i = next(k for k, t in enumerate(textos) if "Aeródromo de Cala Brava" in t)
    robot.tecla(pygame.K_RETURN)
    robot.frames(5)
    robot.tecla(pygame.K_RETURN)
    robot.frames(5)
    assert p.mundo.id == "cala_brava"


def test_en_autobus_se_oye_pasar_un_tren_junto_a_la_carretera(robot):
    robot.nueva_partida()
    app = robot.app
    llegado = []
    v = pantallas.Viaje(app, 30.0, lambda: llegado.append(1), autobus=True, destino="San Lucero")
    v.con_tren, v.tren_en = True, 0.2
    app.abrir(v)
    oido = False
    for _ in range(30 * 20):
        robot.frames(1)
        oido = oido or (v.tren_paso is not None and v.tren_paso["canal"] is not None and v.tren_paso["canal"].nombre == "tren")
    assert oido and any("Un tren alcanza al autobús" in t for t in app.voz.registro[-12:])
    assert v.tren_paso["canal"] is None                              # ya ha pasado
    for _ in range(30 * 14):
        robot.frames(1)
    assert llegado == [1]
    # en taxi por la ciudad, en tren o en avión, no
    for kw in ({}, {"medio": "tren"}, {"vuelo": True}):
        assert not pantallas.Viaje(app, 30.0, lambda: None, destino="x", **kw).con_tren
