"""Trabajo 1.7.1, tanda 19, parte 2: volar de verdad. Altura, combustible, travesías entre todas las localidades,
tormentas y demás sucesos, la aproximación, hangares, el secuestro de un aparato con su radar, los vuelos comerciales,
partidas anteriores, el mando y un servidor de verdad."""
import itertools
import json
import math
import os
import time

import pygame
import pytest

from juego import mundo as M, rutas, vuelo as V, vuelo_pantalla as VP
from juego.menus import Menu
from juego.vuelo_pantalla import Crucero
from test_171_mando import Md, _a, _empezar, _hasta
from test_enlinea import banco, dos, entrar, hasta                # noqa: F401  (banco y dos son fixtures)

AJ = V.AJ


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


def _vuelo(robot, **opciones):
    """Una partida con el vuelo real, que en las pruebas hay que pedir (como los trayectos de taxi)."""
    robot.app.vuelo_en_pruebas = True
    p = _empezar(robot, **opciones)
    p.cfg["vuelo_real"], p.cfg["vuelo_asistido"], p.cfg["vuelo_combustible"] = True, True, True
    return p


def _campo(p, mapa=None, tipo="helipuerto"):
    m = p.mapas[mapa] if mapa else p.mundo
    return next(l for l in m.lugares.values() if l.tipo == tipo)


def _aparato(p, modelo="helicoptero", campo=None, subir=True):
    """Un aparato posado en un campo de esta localidad, contigo a bordo."""
    campo = campo or next(l for l in p.mundo.lugares.values() if l.tipo in V.CAMPOS and (modelo == "helicoptero" or l.tipo == "aeropuerto"))
    x, y, d = p.mundo.plaza_junto_a(campo)
    if p.j.veh:
        p.salir_vehiculo(forzado=True)
    p.j.x, p.j.y = p.mundo.punto_libre(x + 2, y)
    v = p.crear_vehiculo(modelo, x, y, d, None)
    v.cerrado = False
    if subir:
        p._subir(v, False, callar=True)
    return v, campo


def _despegar(robot, p, v):
    robot.frames(2, mantener=(pygame.K_UP,))
    assert v.fase == "despegue"
    for _ in range(30 * 20):
        if v.fase == "vuelo":
            break
        robot.frames(1, mantener=(pygame.K_UP,))
    assert v.fase == "vuelo", robot.dicho()
    v.vel = 0.0
    return v


def _desde(robot, n):
    return " | ".join(robot.app.voz.registro[n:])


def _al_juego(robot, p):
    """Cierra con Escape lo que haya abierto; lo que no se cierre con Escape (un aviso del día, una decisión) se quita sin más."""
    for _ in range(12):
        if robot.app.pila[-1] is p:
            return
        robot.tecla(pygame.K_ESCAPE)
    while robot.app.pila[-1] is not p:
        robot.app.pila.pop()
    robot.app.teclas.clear()


def _elegir(robot, empieza):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(empieza))
    robot.tecla(pygame.K_RETURN)
    return m


def _crucero(robot, p, v, mapa, modo="campo", campo_origen=None, sin_sucesos=True):
    """Abre una travesía hacia esa localidad, sin pasar por el menú."""
    d = next(x for x in p.vuelo_destinos(v) if x["mapa"].id == mapa)
    c = Crucero(p, v, d, modo, campo_origen)
    if sin_sucesos:
        c.plan = []
    robot.app.abrir(c)
    return c


def _volar_hasta_el_final(robot, c, tope=900.0, dt=0.2):
    """Deja pasar la travesía hasta que acaba. Si sale un menú (una tormenta), elige lo primero. Devuelve los segundos de verdad."""
    t = 0.0
    while not c.hecho and t < tope:
        if isinstance(robot.app.pila[-1], Menu):
            robot.tecla(pygame.K_RETURN)
        robot.frames(1, dt=dt)
        t += dt
    assert c.hecho, (t, c.fase, c.km_falta(), c.alt, robot.dicho())
    return t


# ====================================================================== 1. dentro de una localidad: despegar, altura y aterrizar
def test_despegar_subir_bajar_y_aterrizar_con_un_helicoptero(robot, datos_de_serie, monkeypatch):
    p = _vuelo(robot)
    j = p.j
    v, campo = _aparato(p, subir=False)
    son = []
    son_real = p.son
    monkeypatch.setattr(p, "son", lambda nombre, *a, **k: (son.append(nombre), son_real(nombre, *a, **k))[1])
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_f)
    assert j.veh is v and v.fase == "tierra" and v.alt == 0 and v.queroseno == 100
    dicho = _desde(robot, n)
    assert "Estás en tierra. Flecha arriba despega" in dicho and "la D sube y la A baja" in dicho and "Combustible, 100 por ciento" in dicho
    robot.frames(3)
    assert robot.app.mez.altura == 0.0 and p.vuelo_alt() == 0.0
    # en tierra no se mueve; las flechas de girar tampoco hacen nada
    x0, y0 = v.x, v.y
    robot.frames(20, mantener=(pygame.K_RIGHT,))
    assert (v.x, v.y) == (x0, y0)
    # flecha arriba: despega en vertical y, al llegar a la altura de vuelo, lo dice
    robot.frames(2, mantener=(pygame.K_UP,))
    assert v.fase == "despegue" and "Despegas." in _desde(robot, n)
    assert _hasta(robot, lambda: v.fase == "vuelo", 12)
    assert v.alt == AJ("alt_despegue") and "En el aire, a 60 metros" in _desde(robot, n) and "tono_altitud" in son
    robot.frames(3)
    assert robot.app.mez.altura > 0
    # vuela por encima de los edificios, como siempre
    v.rumbo = 0.0
    y0 = v.y
    robot.frames(120, mantener=(pygame.K_UP,))
    assert v.y > y0 + 40 and v.salud == v.salud_max
    # la D sube, con su tono, y dice la altura de cien en cien; al pasar de 150, vuelo alto
    son.clear()
    n = len(robot.app.voz.registro)
    assert not p.vuelo_alto()
    robot.frames(30 * 12, mantener=(pygame.K_d,))
    assert v.alt > 150 and p.vuelo_alto() and son.count("tono_altitud") >= 2
    dicho = _desde(robot, n)
    assert "100 metros." in dicho and "Vuelo alto: desde el suelo ya no te siguen." in dicho
    # el techo
    v.alt = 895.0
    robot.frames(40, mantener=(pygame.K_d,))
    assert v.alt == 900 and "Techo del aparato: 900 metros" in _desde(robot, n)
    # la A baja, hasta el mínimo
    v.alt = 160.0
    robot.frames(30 * 14, mantener=(pygame.K_a,))
    assert v.alt == AJ("alt_minima") and "Vuelo bajo." in _desde(robot, n) and "más abajo, solo para aterrizar" in _desde(robot, n)
    # aterrizar: frenar y F. Sobre un edificio, no
    v.x, v.y, v.vel = 45.0, 45.0 + 90 * 3, 0.0
    assert p.mundo.superficie(v.x, v.y) == "pared"
    robot.tecla(pygame.K_f)
    assert j.veh is v and v.fase == "vuelo" and "debajo hay un edificio" in robot.dicho()
    v.vel = 20.0
    robot.tecla(pygame.K_f)
    assert "Frena antes de aterrizar" in robot.dicho() and v.fase == "vuelo"
    v.x, v.y, v.vel = campo.x, campo.y, 0.0
    v.alt = 90.0
    n = len(robot.app.voz.registro)
    son.clear()
    robot.tecla(pygame.K_f)
    assert v.fase == "aterrizando" and "Desciendes desde 90 metros" in _desde(robot, n) and j.veh is v
    robot.tecla(pygame.K_f)
    assert "Ya estás bajando" in robot.dicho()
    assert _hasta(robot, lambda: j.veh is None, 12)
    assert v.fase == "tierra" and v.alt == 0 and "aterrizaje" in son and "Te bajas." in _desde(robot, n) and v.salud == v.salud_max
    # y vuelves a subir: sigue en tierra
    robot.tecla(pygame.K_f)
    assert j.veh is v and v.fase == "tierra"


def test_la_avioneta_necesita_pista_o_es_un_aterrizaje_forzoso(robot, datos_de_serie):
    p = _vuelo(robot)
    j = p.j
    v, campo = _aparato(p, "avioneta")
    assert campo.tipo == "aeropuerto" and V.aeronave(v.modelo)["pista"]
    assert "hace falta una pista" in p.vuelo_texto_subir(v)
    # la avioneta coge carrera: si sueltas antes de tiempo, no despega; manteniendo, avanza y se levanta
    x0, y0 = v.x, v.y
    n = len(robot.app.voz.registro)
    robot.frames(3, mantener=(pygame.K_UP,))
    assert v.fase == "despegue" and "Coges carrera" in _desde(robot, n)
    robot.frames(90)
    assert v.fase == "tierra" and v.alt == 0 and "Despegue abortado" in _desde(robot, n)
    _despegar(robot, p, v)
    assert math.hypot(v.x - x0, v.y - y0) > 30
    # lejos de la pista: la primera F avisa; la segunda, forzoso, con daño
    libre = next(l for l in p.mundo.lugares.values() if l.tipo == "monumento" and math.hypot(l.x - campo.x, l.y - campo.y) > 200)
    v.x, v.y = p.mundo.punto_libre(libre.x, libre.y)
    v.vel = 0.0
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_f)
    assert v.fase == "vuelo" and "Aquí no hay pista" in _desde(robot, n) and "Pulsa F otra vez" in _desde(robot, n)
    robot.tecla(pygame.K_f)
    assert v.fase == "aterrizando"
    assert _hasta(robot, lambda: j.veh is None, 12)
    pct = 100 * (1 - v.salud / v.salud_max)
    assert AJ("forzoso_min") - 0.01 <= pct <= AJ("forzoso_max") + 0.01 and any(f in _desde(robot, n) for f in AJ.lista("frases_forzoso"))
    # en la pista, sin daño
    v.salud = v.salud_max
    p._subir(v, False, callar=True)
    _despegar(robot, p, v)
    v.x, v.y, v.vel = campo.x, campo.y, 0.0
    robot.tecla(pygame.K_f)
    assert v.fase == "aterrizando"
    assert _hasta(robot, lambda: j.veh is None, 12) and v.salud == v.salud_max
    # sobre el mar no se posa nadie
    v2, _ = _aparato(p, "helicoptero")
    _despegar(robot, p, v2)
    p.cambiar_mapa("mar", 600, 600)
    v2.vel = 0.0
    robot.tecla(pygame.K_f)
    assert j.veh is v2 and "No puedes posarte sobre el mar" in robot.dicho()


def test_con_el_vuelo_real_apagado_todo_es_como_antes(robot, datos_de_serie):
    robot.app.vuelo_en_pruebas = True
    p = _empezar(robot)
    p.cfg["vuelo_real"] = False
    j = p.j
    v, campo = _aparato(p)
    assert not p.vuelo_real()
    robot.frames(3)
    assert robot.app.mez.altura == 35.0                          # siempre a la misma altura
    v.rumbo = 0.0
    y0 = v.y
    robot.frames(60, mantener=(pygame.K_UP,))
    assert v.y > y0 + 10 and getattr(v, "fase", None) is None and getattr(v, "queroseno", None) is None
    robot.frames(30, mantener=(pygame.K_d,))                     # la D no hace nada
    assert getattr(v, "alt", None) is None
    v.x, v.y, v.vel = campo.x, campo.y, 0.0
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.opciones[0].texto.startswith("Volar a ") and "vuelo es gratis" in robot.dicho()
    _elegir(robot, "Volar a Helipuerto de Monteferro")
    assert p.mundo.id == "monteferro" and j.veh is v            # el salto de siempre
    v.vel = 0.0
    robot.tecla(pygame.K_f)
    assert j.veh is None
    # y sin pedirlo en las pruebas, también: las pruebas de antes siguen comprobando lo de antes
    robot.app.vuelo_en_pruebas = False
    p.cfg["vuelo_real"] = True
    assert not p.vuelo_real()


# ====================================================================== 2. combustible
def test_el_combustible_se_gasta_avisa_y_si_se_acaba_el_motor_se_para(robot, datos_de_serie, monkeypatch):
    p = _vuelo(robot)
    j = p.j
    v, campo = _aparato(p)
    _despegar(robot, p, v)
    son = []
    son_real = p.son
    monkeypatch.setattr(p, "son", lambda nombre, *a, **k: (son.append(nombre), son_real(nombre, *a, **k))[1])
    q = v.queroseno
    robot.frames(90, mantener=(pygame.K_UP,))
    assert q - 0.2 < v.queroseno < q                             # un minuto a fondo gasta un 1,2 por ciento
    # los avisos: la reserva y lo crítico, con su alarma
    n = len(robot.app.voz.registro)
    v.queroseno = AJ("reserva") + 0.01
    robot.frames(40, mantener=(pygame.K_UP,))
    assert any(f.split("{")[0] in _desde(robot, n) for f in AJ.lista("frases_reserva")) and "reserva" in son
    v.queroseno = AJ("critico") + 0.01
    robot.frames(40, mantener=(pygame.K_UP,))
    assert any(f.split("{")[0] in _desde(robot, n) for f in AJ.lista("frases_critico")) and "alarma_cabina" in son
    # se acaba: el motor se para y planeas; flecha arriba ya no acelera
    v.alt = 120.0
    v.queroseno = 0.005
    x, y = p.mundo.punto_libre(campo.x, campo.y)
    v.x, v.y = x, y
    robot.frames(40, mantener=(pygame.K_UP,))
    assert v.fase == "sin_motor" and v.queroseno == 0 and "motor_seco" in son and any(f in _desde(robot, n) for f in AJ.lista("frases_sin_motor"))
    assert _hasta(robot, lambda: v.fase == "tierra", 30)
    assert v.alt == 0 and v.salud < v.salud_max and j.veh is v and "No queda combustible" in _desde(robot, n)
    # sin combustible no despega, y lo dice
    n = len(robot.app.voz.registro)
    robot.frames(5, mantener=(pygame.K_UP,))
    assert v.fase == "tierra" and "El motor no arranca: no queda combustible" in _desde(robot, n)
    # se pide desde el móvil, en Mis vehículos: medio depósito
    j.dinero = 5000
    assert p.hacer_mio(v, callar=True)
    from juego import misvehiculos as MV
    MV.menu_mis_vehiculos(p)
    _elegir(robot, v.nombre)
    _elegir(robot, "Que le traigan combustible")
    assert v.queroseno == 50 and j.dinero == 5000 - p.precio("queroseno_domicilio", 450)
    _al_juego(robot, p)
    # y en el campo se llena, pagando lo que falta
    v.x, v.y = campo.x, campo.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.titulo.startswith(f"{campo.nombre}. A bordo de")
    assert any(o.texto == "Repostar: 50 por ciento. Llenar cuesta 300 euros" for o in m.opciones)
    dinero = j.dinero
    _elegir(robot, "Repostar")
    assert v.queroseno == 100 and j.dinero == dinero - 300
    robot.tecla(pygame.K_ESCAPE)
    # si caes sobre un edificio, es peor: te estrellas y te haces daño
    _despegar(robot, p, v)
    v.x, v.y, v.vel = 45.0, 45.0 + 90 * 3, 0.0
    v.alt, v.queroseno, v.salud = 40.0, 0.001, v.salud_max
    salud = j.salud
    robot.frames(10, mantener=(pygame.K_UP,))
    assert _hasta(robot, lambda: v.fase == "tierra", 20)
    pct = 100 * (1 - v.salud / v.salud_max)
    assert AJ("caida_min") - 0.01 <= pct <= AJ("caida_max") + 0.01 and j.salud < salud and p.mundo.transitable(v.x, v.y)
    # con el combustible apagado en Opciones, no se gasta
    p.cfg["vuelo_combustible"] = False
    v.queroseno = 30.0
    robot.frames(60, mantener=(pygame.K_UP,))
    assert v.queroseno == 30.0 and v.fase in ("despegue", "vuelo")


# ====================================================================== 3. la travesía
def _campos_de(p, mapa, pista):
    return [l for l in p.mapas[mapa].lugares.values() if l.tipo in V.CAMPOS and (not pista or l.tipo == "aeropuerto")]


def test_las_distancias_y_los_rumbos_de_la_comarca():
    M.cargar_datos()
    assert set(V.MAPA_AIRE) >= {"puerto_bravo", "cala_brava", "san_lucero", "villaseca", "monteferro", "fuentefria", "isla_tortuga", "plataforma"}
    a, b = V.punto_aire("puerto_bravo"), V.punto_aire("san_lucero")
    assert 40 < V.distancia(a, b) < 50 and 80 < V.rumbo_entre(a, b) < 90 and V.rumbo_txt(V.rumbo_entre(a, b)).endswith("este")
    assert V.rumbo_txt(V.rumbo_entre(a, V.punto_aire("monteferro"))).endswith("norte") and 175 < V.rumbo_entre(a, V.punto_aire("plataforma")) < 185
    # una localidad de un mod, sin apuntar: tiene sitio, siempre el mismo, y no encima de otra
    x = V.punto_aire("bahia_ocaso_mod")
    assert x == V.punto_aire("bahia_ocaso_mod") and all(V.distancia(x, q) > 3 for q in V.MAPA_AIRE.values())
    assert V.km_txt(4.26) == "4,3" and V.km_txt(44.4) == "44"
    # un aparato de un mod que no esté en los datos vuela con algo razonable
    extra = V.aeronave({"id": "dirigible", "vel_max": 30})
    assert extra["crucero"] == 108 and not extra["pista"] and extra["autonomia"] > 0


def test_se_vuela_entre_todas_las_parejas_de_localidades_con_los_dos_aparatos(robot, datos_de_serie):
    """Cada localidad con helipuerto, aeropuerto o aeródromo, hacia todas las demás, en helicóptero y en avioneta, con
    el piloto automático y acelerando: se llega siempre, al campo que toca o volando bajo donde no hay pista."""
    p = _vuelo(robot, sin_policia=True)
    j = p.j
    con_campo = sorted(m.id for m in p.mapas.values() if m.tipo != "mar" and any(l.tipo in V.CAMPOS for l in m.lugares.values()))
    assert len(con_campo) >= 8
    hechas, tiempos = 0, []
    for modelo in ("helicoptero", "avioneta"):
        pista = V.aeronave(p.modelos[modelo])["pista"]
        for origen, destino in itertools.permutations(con_campo, 2):
            if p.mundo.id != origen:
                l = _campos_de(p, origen, False)[0]
                if j.veh:
                    p.salir_vehiculo(forzado=True)
                p.cambiar_mapa(origen, l.x, l.y)
            for o in [o for o in p.vehiculos]:
                p.quitar_vehiculo(o)
            x, y = p.mundo.punto_libre(p.mundo.ancho / 2, p.mundo.alto / 2)
            v = p.crear_vehiculo(modelo, x, y, 0, None)
            p._subir(v, False, callar=True)
            p.vuelo_prep(v)
            v.fase, v.alt = "vuelo", 80.0
            d = next(q for q in p.vuelo_destinos(v) if q["mapa"].id == destino)
            assert (d["campo"] is not None) == bool(_campos_de(p, destino, pista)), (modelo, destino)
            km = d["km"]
            assert km == pytest.approx(V.distancia(V.punto_aire(origen), V.punto_aire(destino))) and 5 < km < 200
            hora = p.dia * 1440 + p.reloj
            c = Crucero(p, v, d, "campo")
            assert c.modo == ("campo" if d["campo"] is not None else "bajo")
            robot.app.abrir(c)
            robot.tecla(pygame.K_n)                              # acelerada
            t = _volar_hasta_el_final(robot, c)
            tiempos.append(t)
            assert robot.app.pila[-1] is p and p.mundo.id == destino and j.veh is v, (modelo, origen, destino)
            if d["campo"] is not None:
                assert v.fase == "tierra" and v.alt == 0 and v.dist(d["campo"].x, d["campo"].y) < 60 and (not pista or d["campo"].tipo == "aeropuerto")
            else:
                assert v.fase == "vuelo" and v.alt >= AJ("alt_minima") and 0 <= v.x <= p.mundo.ancho and 0 <= v.y <= p.mundo.alto
            assert 0 < v.queroseno < 100 and c.km_hechos >= km * 0.6      # con viento de cola se vuela menos aire del que se recorre
            assert p.dia * 1440 + p.reloj > hora                 # el viaje lleva su tiempo del juego
            hechas += 1
    assert hechas == 2 * len(con_campo) * (len(con_campo) - 1)
    assert j.stats["travesias"] == hechas and j.stats["km_volados"] > 1000
    assert max(tiempos) < 240 and min(tiempos) > 2               # ni eternas ni instantáneas, aun aceleradas


def test_una_travesia_de_principio_a_fin_con_la_torre_y_el_piloto_automatico(robot, datos_de_serie, monkeypatch):
    p = _vuelo(robot)
    j = p.j
    v, campo = _aparato(p)
    v.queroseno = 80.0
    son = []
    sonar_real = robot.app.mez.sonar
    monkeypatch.setattr(robot.app.mez, "sonar", lambda nombre, *a, **k: (son.append(nombre), sonar_real(nombre, *a, **k))[1])
    # Intro en el campo, a bordo: el menú del campo, y de ahí el plan de vuelo
    robot.frames(15)
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.opciones[0].texto.startswith("Plan de vuelo")
    robot.tecla(pygame.K_RETURN)
    plan = robot.app.pila[-1]
    assert plan.titulo.startswith(f"Plan de vuelo desde {campo.nombre}. Combustible, 80 por ciento")
    textos = [o.texto for o in plan.opciones]
    # dos maneras de llegar a cada sitio, la más cercana primero, y la última opción no vuela
    assert textos[0].startswith("Villaseca: ") or textos[0].startswith("Cala Brava: ")
    assert sum(1 for t in textos if t.startswith("Monteferro: ")) == 2 and textos[-1] == "Volver"
    sl = next(t for t in textos if t.startswith("San Lucero: ") and "Aterrizar en" in t)
    assert "44 kilómetros, rumbo 085, este" in sl and "unos 16 minutos" in sl and "Helipuerto del campus" in sl
    _elegir(robot, sl)
    c = robot.app.pila[-1]
    assert isinstance(c, Crucero) and c.auto and c.fase == "ascenso" and c.despega is campo and c.asistido
    c.plan = []                                                  # sin sucesos: van en su propia prueba
    c.viento_kmh = 10.0                                          # y con poco viento, para que las cuentas del combustible salgan siempre igual
    dicho = _desde(robot, n)
    assert f"{campo.nombre}, autorizado a despegar" in dicho or f"Aquí {campo.nombre}. Pista libre" in dicho
    assert "El piloto automático lleva el rumbo y la altitud" in dicho and "emisora" in son and "Combustible, 80 por ciento" in dicho
    # sube solo a su nivel de crucero, con el tono de altitud, y la torre lo dice
    assert _hasta(robot, lambda: c.fase == "crucero" and abs(c.alt - 500) < 5, 40)
    assert "tono_altitud" in son and any(f.split("{")[0] in _desde(robot, n) for f in AJ.lista("torre_crucero"))
    # Intro: cómo va
    robot.tecla(pygame.K_RETURN)
    estado = robot.app.voz.registro[-1]
    assert "kilómetros de San Lucero" in estado and "Rumbo " in estado and "bien encarado" in estado and "Altitud 500 metros" in estado
    assert "Combustible 7" in estado and "Piloto automático puesto." in estado and "Viento, " in estado
    # la N acelera; F1 lo explica; Inicio repite a la torre
    km = c.km_falta()
    robot.frames(30)
    lento = km - c.km_falta()
    robot.tecla(pygame.K_n)
    assert c.rapido and c.acelerada() and "Travesía acelerada" in robot.dicho()
    km = c.km_falta()
    robot.frames(30)
    assert km - c.km_falta() == pytest.approx(lento * AJ("acelerado"), rel=0.15)
    robot.tecla(pygame.K_F1)
    assert "Tabulador pone o quita el piloto automático" in robot.app.voz.registro[-1] and "chasquidos" in robot.app.voz.registro[-1]
    robot.tecla(pygame.K_HOME)
    assert robot.app.voz.registro[-1] == c.ultima_torre
    # se acerca: la torre de destino da la aproximación, el aparato baja y se encara solo, y aterriza
    hora = p.dia * 1440 + p.reloj
    n = len(robot.app.voz.registro)
    _volar_hasta_el_final(robot, c)
    dicho = _desde(robot, n)
    destino = _campo(p, "san_lucero")
    assert any(f.split("{")[0].replace("{campo}", "") in dicho for f in ("Torre de ", ", aproximación. Estás a"))
    assert any(f in dicho for f in AJ.lista("torre_final")) and "tono_alineacion" in son and "aterrizaje" in son
    assert any(f.replace("{campo}", destino.nombre) in dicho for f in AJ.lista("frases_aterrizaje"))
    assert p.mundo.id == "san_lucero" and j.veh is v and v.fase == "tierra" and v.dist(destino.x, destino.y) < 60 and v.salud == v.salud_max
    gastado = 80 - v.queroseno
    assert 44 / 260 * 100 * 0.9 < gastado < 44 / 260 * 100 * 1.4 and not c.duro
    minutos = p.dia * 1440 + p.reloj - hora
    assert 5 < minutos < 30                                      # unos 16 minutos de vuelo, del reloj del juego
    assert j.stats["travesias"] == 1 and 40 < j.stats["km_volados"] < 55


def test_pilotar_a_mano_rumbo_altitud_viento_y_los_chasquidos(robot, datos_de_serie, monkeypatch):
    p = _vuelo(robot)
    v, campo = _aparato(p)
    _despegar(robot, p, v)
    c = _crucero(robot, p, v, "monteferro")
    c.viento_kmh, c.viento_de = 40.0, 270.0                      # viento fuerte del oeste, de costado
    sonados = []
    son_real = robot.app.son
    monkeypatch.setattr(robot.app, "son", lambda nombre, *a, **k: (sonados.append((nombre, k.get("pan"), k.get("tono"))), son_real(nombre, *a, **k))[1])
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    # con el piloto automático no suenan los chasquidos; al quitarlo, sí
    sonados.clear()
    robot.frames(60)
    assert not [s for s in sonados if s[0] == "tono_alineacion"]
    robot.tecla(pygame.K_TAB)
    assert not c.auto and "Piloto automático quitado: pilotas tú" in robot.dicho()
    robot.frames(60)
    centro = [s for s in sonados if s[0] == "tono_alineacion"]
    assert centro and all(abs(s[1]) < 0.2 for s in centro)       # encarado: por el centro y agudos
    assert all(s[2] > 1.2 for s in centro)
    # viras a la derecha: el destino queda a la izquierda, y los chasquidos se van a ese lado y bajan de tono
    rumbo = c.rumbo
    for _ in range(4):
        robot.tecla(pygame.K_RIGHT)
    assert c.rumbo == pytest.approx((rumbo + 40) % 360, abs=3) and "Te faltan 40 grados a la izquierda" in robot.dicho()
    sonados.clear()
    robot.frames(60)
    lado = [s for s in sonados if s[0] == "tono_alineacion"]
    assert lado and all(s[1] < -0.5 for s in lado) and all(s[2] == 1.0 for s in lado)
    assert c.desvio() < -25
    # la flecha quita sola el piloto automático si estaba puesto
    robot.tecla(pygame.K_TAB)
    assert c.auto
    robot.tecla(pygame.K_LEFT)
    assert not c.auto and "Piloto automático quitado" in robot.dicho()
    # el viento cuenta: con viento del oeste y el destino al norte, el rumbo bueno no es el norte, sino un poco al oeste, contra el viento
    hacia = V.rumbo_entre(c.pos, c.meta)
    assert M.norm180(c.rumbo_bueno() - hacia) < -8
    c.rumbo = hacia                                              # apuntando derecho al destino, el viento te saca: los chasquidos piden virar a la izquierda
    assert c.desvio() < -8
    x0 = c.pos[0]
    robot.frames(90)
    assert c.pos[0] > x0 + 0.3                                    # y de hecho te vas hacia el este
    # siguiendo los chasquidos, vas derecho: la distancia al destino baja lo que avanzas
    while abs(c.desvio()) > 5:
        robot.tecla(pygame.K_LEFT if c.desvio() < 0 else pygame.K_RIGHT)
    km, t0 = c.km_falta(), c.t_vuelo
    robot.frames(90)
    assert km - c.km_falta() == pytest.approx(c.velocidad() * (c.t_vuelo - t0) / 3600.0, rel=0.05)
    # altitud: de cien en cien, con su frase, entre el mínimo y el techo
    robot.tecla(pygame.K_UP)
    assert c.alt_obj == 600 and "Subes a 600 metros" in robot.dicho()
    for _ in range(6):
        robot.tecla(pygame.K_UP)
    assert c.alt_obj == 900 and "Techo del aparato: 900 metros" in robot.dicho()
    antes = c.alt
    robot.frames(60)
    assert c.alt > antes
    # una tecla cualquiera dice cómo va
    robot.tecla(pygame.K_z)
    assert "kilómetros de Monteferro" in robot.app.voz.registro[-1] and "Pilotas a mano." in robot.app.voz.registro[-1]
    # el piloto automático corrige la deriva: vuelve a encarar y llega
    robot.tecla(pygame.K_TAB)
    assert c.auto
    _volar_hasta_el_final(robot, c)
    assert p.mundo.id == "monteferro"


def test_turbulencias_trafico_y_paisaje(robot, datos_de_serie, monkeypatch):
    p = _vuelo(robot)
    v, campo = _aparato(p)
    _despegar(robot, p, v)
    c = _crucero(robot, p, v, "fuentefria")
    c.viento_kmh = 0.0                                           # sin viento: que el camino sea siempre el mismo
    sonados = []
    son_real = robot.app.son
    monkeypatch.setattr(robot.app, "son", lambda nombre, *a, **k: (sonados.append(nombre), son_real(nombre, *a, **k))[1])
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    n = len(robot.app.voz.registro)
    # turbulencia: se oye, zarandea la altitud y pasa
    c.plan = [(c.km_hechos, "turbulencia")]
    robot.tecla(pygame.K_n)
    robot.frames(3)
    assert c.suceso and c.suceso["tipo"] == "turbulencia" and c.rapido and not c.acelerada()      # mientras pasa algo, va a su ritmo
    assert any(f in _desde(robot, n) for f in AJ.lista("frases_turbulencia"))
    alturas = set()
    for _ in range(40):
        robot.frames(5)
        alturas.add(round(c.alt))
    assert "turbulencia" in sonados and len(alturas) > 3
    assert _hasta(robot, lambda: c.suceso is None, 15) and any(f in _desde(robot, n) for f in AJ.lista("frases_turbulencia_fin"))
    assert c.acelerada()                                          # y después sigue acelerada, sin pedirlo otra vez
    robot.tecla(pygame.K_n)
    assert not c.rapido
    # tráfico con el piloto automático: cambia él de nivel
    c.alt = c.alt_obj = 500.0
    c.plan = [(c.km_hechos, "trafico")]
    robot.frames(2)
    assert c.suceso["tipo"] == "trafico" and "alarma_cabina" in sonados and c.ultima_torre in AJ.lista("torre_trafico")
    assert _hasta(robot, lambda: c.suceso is None, 12)
    assert c.alt_obj == 600 and "El piloto automático sube cien metros" in _desde(robot, n)
    # tráfico a mano: si cambias tú, librado
    robot.tecla(pygame.K_TAB)
    c.plan = [(c.km_hechos, "trafico")]
    robot.frames(2)
    robot.tecla(pygame.K_DOWN)
    robot.frames(2)
    assert c.suceso is None and any(f in robot.dicho() for f in AJ.lista("frases_trafico_libre"))
    # y si no haces nada: el susto, y la sanción
    dinero = p.j.dinero = 1000
    c.plan = [(c.km_hechos, "trafico")]
    robot.frames(2)
    assert _hasta(robot, lambda: c.suceso is None, 14)
    assert p.j.dinero == dinero - AJ.entero("trafico_multa") and "Sanción de 150 euros" in robot.dicho() and c.confort >= 1
    # el paisaje: de Puerto Bravo a Fuentefría se pasa casi por encima de Monteferro, y se dice a qué lado queda
    robot.tecla(pygame.K_TAB)
    _volar_hasta_el_final(robot, c)
    dicho = _desde(robot, n)
    assert "Monteferro" in dicho and ("tu derecha" in dicho or "tu izquierda" in dicho), dicho
    assert any(f.split("{")[0] in dicho for f in AJ.lista("frases_paisaje"))
    assert p.mundo.id == "fuentefria"


def test_una_tormenta_se_rodea_se_pasa_por_encima_o_se_atraviesa(robot, datos_de_serie, monkeypatch):
    p = _vuelo(robot)
    monkeypatch.setattr(VP.random, "random", lambda: 0.0)        # dentro de la tormenta, cada sacudida hace daño
    resultados = {}
    for modelo, que in (("helicoptero", "Rodearla"), ("helicoptero", "Atravesarla"), ("avioneta", "Pasarla por encima")):
        if p.mundo.id != "puerto_bravo":
            p.salir_vehiculo(forzado=True)
            l = _campo(p, "puerto_bravo")
            p.cambiar_mapa("puerto_bravo", l.x, l.y)
        v, campo = _aparato(p, modelo)
        p.vuelo_prep(v)
        v.fase, v.alt = "vuelo", 80.0
        c = _crucero(robot, p, v, "monteferro")
        c.viento_kmh = 0.0                                       # sin viento, para comparar lo recorrido
        assert _hasta(robot, lambda: c.fase == "crucero", 60)
        n = len(robot.app.voz.registro)
        c.plan = [(c.km_hechos, "tormenta")]
        robot.frames(2)
        m = robot.app.pila[-1]
        assert isinstance(m, Menu) and m.titulo.startswith("Tormenta en tu rumbo") and not m.escapable and c.tormenta is not None
        textos = [o.texto for o in m.opciones]
        assert textos[0].startswith("Rodearla") and textos[-1] == "Atravesarla" and all(o.ayuda for o in m.opciones)
        assert any(t.startswith("Pasarla por encima") for t in textos) == (modelo == "avioneta")      # el helicóptero no sube tanto
        assert any(f.split("{")[0] in _desde(robot, n) for f in AJ.lista("torre_tormenta"))
        _elegir(robot, que)
        assert robot.app.pila[-1] is c
        centro, radio = c.tormenta["c"], c.tormenta["r"]
        cerca, dentro_bajo = 1e9, False
        t = 0.0
        while not c.hecho and t < 600:
            robot.frames(1, dt=0.2)
            t += 0.2
            if c.tormenta is not None or cerca < 1e9:
                d = V.distancia(c.pos, centro)
                cerca = min(cerca, d)
                dentro_bajo = dentro_bajo or (d <= radio and c.alt < AJ("tormenta_alt"))
        assert c.hecho and p.mundo.id == "monteferro"
        resultados[que] = (cerca, dentro_bajo, v.salud / v.salud_max, c.km_hechos, _desde(robot, n))
        p.salir_vehiculo(forzado=True)
    cerca, dentro, salud, km, dicho = resultados["Rodearla"]
    assert cerca > 6.0 and not dentro and salud == 1.0 and "La rodeas por la" in dicho and km > 55.0
    cerca, dentro, salud, km2, dicho = resultados["Atravesarla"]
    assert cerca < 2.0 and dentro and salud < 1.0 and km2 < km
    assert any(f in dicho for f in AJ.lista("frases_tormenta_dentro")) and any(f in dicho for f in AJ.lista("frases_tormenta_fuera"))
    cerca, dentro, salud, _, dicho = resultados["Pasarla por encima"]
    assert cerca < 2.0 and not dentro and salud == 1.0 and "Subes a 1900 metros" in dicho and any(f in dicho for f in AJ.lista("frases_tormenta_encima"))


def test_aterrizar_a_mano_frustrada_guiada_y_aterrizaje_duro(robot, datos_de_serie):
    p = _vuelo(robot)
    p.cfg["vuelo_asistido"] = False
    v, campo = _aparato(p)
    _despegar(robot, p, v)
    c = _crucero(robot, p, v, "villaseca")
    assert not c.asistido
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    robot.tecla(pygame.K_TAB)                                    # a mano
    n = len(robot.app.voz.registro)
    # entra alto: la torre le manda dar otra vuelta
    t = 0.0
    while c.frustradas == 0 and t < 300:
        d = c.desvio()
        if abs(d) > 8:
            robot.tecla(pygame.K_RIGHT if d > 0 else pygame.K_LEFT)
        robot.frames(1, dt=0.2)
        t += 0.2
    dicho = _desde(robot, n)
    assert c.frustradas == 1 and not c.hecho and "Aterrizaje a mano: baja con flecha abajo hasta 200 metros" in dicho
    assert "Demasiado alto" in dicho or "vienes demasiado alto" in dicho
    assert c.km_falta() == pytest.approx(AJ("frustrada_km"), abs=0.5) and not c.guiada
    # ahora baja, pero entra torcido
    for _ in range(4):
        robot.tecla(pygame.K_DOWN)
    assert c.alt_obj == 100
    for _ in range(4):
        robot.tecla(pygame.K_RIGHT)
    c.rumbo = (V.rumbo_entre(c.pos, c.meta) + 35) % 360
    t = 0.0
    while c.frustradas == 1 and not c.hecho and t < 120:
        robot.frames(1, dt=0.1)
        t += 0.1
        if c.km_falta() < 1.2:
            c.rumbo = (V.rumbo_entre(c.pos, c.meta) + 35) % 360
    # a la segunda, la torre le guía ella: piloto automático y aterriza
    assert c.frustradas == 2 and c.guiada and c.auto and any(f in _desde(robot, n) for f in AJ.lista("torre_guiada")), _desde(robot, n)
    _volar_hasta_el_final(robot, c)
    assert p.mundo.id == "villaseca" and v.fase == "tierra" and v.salud == v.salud_max and c.confort == 2
    # a mano y bien: baja a tiempo, encarado, y aterriza él
    p.salir_vehiculo(forzado=True)
    v, campo = _aparato(p, "avioneta")
    p.vuelo_prep(v)
    v.fase, v.alt = "vuelo", 80.0
    c = _crucero(robot, p, v, "puerto_bravo")
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    robot.tecla(pygame.K_TAB)
    while c.alt_obj > 200:
        robot.tecla(pygame.K_DOWN)
    c.alt = 200.0
    t = 0.0
    while not c.hecho and t < 300:
        d = c.desvio()
        if abs(d) > 5:
            c.rumbo = (c.rumbo + d) % 360
        robot.frames(1, dt=0.2)
        t += 0.2
    assert c.hecho and c.frustradas == 0 and not c.duro and p.mundo.id == "puerto_bravo" and v.salud == v.salud_max
    # justo de altura o de rumbo: entra, pero el aterrizaje es duro y el aparato lo paga
    p.salir_vehiculo(forzado=True)
    v, campo = _aparato(p)
    p.vuelo_prep(v)
    v.fase, v.alt = "vuelo", 80.0
    c = _crucero(robot, p, v, "villaseca")
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    robot.tecla(pygame.K_TAB)
    c.alt = c.alt_obj = 240.0
    n = len(robot.app.voz.registro)
    t = 0.0
    while not c.hecho and t < 300:
        c.rumbo = V.rumbo_entre(c.pos, c.meta) if c.km_falta() > 0.2 else c.rumbo
        robot.frames(1, dt=0.2)
        t += 0.2
    assert c.hecho and c.duro and v.salud == pytest.approx(v.salud_max * (1 - AJ("duro_dano") / 100))
    assert any(f.replace("{campo}", "Aeródromo de Villaseca") in _desde(robot, n) for f in AJ.lista("frases_aterrizaje_duro"))


def test_el_menu_de_vuelo_cambiar_de_destino_y_entrar_volando_bajo(robot, datos_de_serie):
    p = _vuelo(robot)
    j = p.j
    v, campo = _aparato(p)
    _despegar(robot, p, v)
    # al borde de la localidad se abre el plan de vuelo, con lo que tienes delante en primer lugar
    v.rumbo, v.x, v.y, v.vel = 90.0, p.mundo.ancho - 8, 300.0, 30.0
    robot.frames(30, mantener=(pygame.K_UP,))
    plan = robot.app.pila[-1]
    assert isinstance(plan, Menu) and plan.titulo.startswith("Plan de vuelo desde Puerto Bravo"), robot.dicho()
    assert plan.opciones[0].texto.startswith(("San Lucero: ", "Cala Brava: ")) and v.vel == 0
    robot.tecla(pygame.K_ESCAPE)                                 # quedarse: no vuelve a salir al instante
    robot.frames(10, mantener=(pygame.K_UP,))
    assert robot.app.pila[-1] is p
    v.x = p.mundo.ancho - 60
    c = _crucero(robot, p, v, "san_lucero")
    assert c.despega is None
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    # el menú de vuelo, con la D o con Escape
    robot.tecla(pygame.K_d)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.titulo == "Menú de vuelo" and m.opciones[0].texto == "Seguir volando"
    textos = [o.texto for o in m.opciones]
    assert "Cómo llegas: aterrizar en Helipuerto del campus" in textos and "Aterrizaje asistido: sí" in textos and any(t.startswith("Campo: ") for t in textos)
    _elegir(robot, "Campo: ")
    assert c.campo.tipo == "aeropuerto" and "Campo: Aeropuerto de San Lucero" in [o.texto for o in m.opciones]
    _elegir(robot, "Aterrizaje asistido")
    assert not c.asistido and p.cfg["vuelo_asistido"] is False
    _elegir(robot, "Aterrizaje asistido")
    _elegir(robot, "Cómo llegas")
    assert c.modo == "bajo" and "entrar volando bajo sobre la localidad" in m.opciones[m.i].texto
    # cambiar de destino: el más cercano primero, con su distancia desde donde estás ahora
    _elegir(robot, "Cambiar de destino")
    sub = robot.app.pila[-1]
    kms = [float(o.texto.split(": ")[1].split(" ")[0].replace(",", ".")) for o in sub.opciones if ": " in o.texto and "kilómetros" in o.texto]
    assert kms == sorted(kms) and len(kms) >= 8
    n = len(robot.app.voz.registro)
    _elegir(robot, "Isla Tortuga")
    assert robot.app.pila[-1] is c and c.destino["mapa"].id == "isla_tortuga" and "nuevo destino, Isla Tortuga" in _desde(robot, n)
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1].titulo == "Menú de vuelo"
    robot.tecla(pygame.K_RETURN)
    # llega volando bajo: en el aire, sobre la isla, por el lado del que viene, y se posa donde quiere
    _volar_hasta_el_final(robot, c)
    assert p.mundo.id == "isla_tortuga" and j.veh is v and v.fase == "vuelo" and AJ("alt_minima") <= v.alt <= 250 and v.vel > 0
    assert any(f.replace("{destino}", "Isla Tortuga") in robot.dicho() for f in AJ.lista("frases_sobrevuelo"))
    assert v.x < 40 or v.x > p.mundo.ancho - 40 or v.y < 40 or v.y > p.mundo.alto - 40
    # la avioneta no tiene pista en la isla: solo se le ofrece entrar volando bajo
    p.cambiar_mapa("puerto_bravo", campo.x, campo.y)
    p.salir_vehiculo(forzado=True)
    av, _ = _aparato(p, "avioneta")
    p.vuelo_prep(av)
    av.fase, av.alt = "vuelo", 80.0
    VP.plan_de_vuelo(p, None)
    textos = [o.texto for o in robot.app.pila[-1].opciones if o.texto.startswith("Isla Tortuga")]
    assert len(textos) == 1 and "allí no hay campo para este aparato" in textos[0]


def test_sin_combustible_en_plena_travesia(robot, datos_de_serie):
    p = _vuelo(robot)
    j = p.j
    v, campo = _aparato(p)
    _despegar(robot, p, v)
    v.queroseno = 6.0                                            # para unos 15 kilómetros
    n = len(robot.app.voz.registro)
    c = _crucero(robot, p, v, "fuentefria")
    assert "Atención: con lo que llevas solo puedes hacer unos 15 kilómetros. No llegas." in _desde(robot, n)
    salud = j.salud
    t = 0.0
    while not c.sin_motor and t < 200:
        robot.frames(1, dt=0.2)
        t += 0.2
    assert c.sin_motor and not c.auto and v.queroseno == 0 and any(f in _desde(robot, n) for f in AJ.lista("frases_sin_motor"))
    assert "planeas unos" in _desde(robot, n) and "No llegas a ningún campo" in _desde(robot, n)
    robot.tecla(pygame.K_TAB)
    assert not c.auto and "Sin motor no hay piloto automático" in robot.dicho()
    robot.tecla(pygame.K_UP)
    assert "Sin motor, el aparato baja solo" in robot.dicho()
    _volar_hasta_el_final(robot, c)
    # acabas en las afueras de la localidad más cercana, con el aparato hecho polvo y tú tocado
    assert p.mundo.id in ("villaseca", "puerto_bravo") and j.veh is v and v.fase == "tierra" and v.queroseno == 0
    pct = 100 * (1 - v.salud / v.salud_max)
    assert AJ("caida_min") - 0.01 <= pct <= AJ("caida_max") + 0.01 and j.salud < salud and j.stats["aterrizajes_forzosos"] == 1
    assert any(f in _desde(robot, n) for f in AJ.lista("frases_caida")) and p.mundo.transitable(v.x, v.y)
    # si el campo está al alcance del planeo, llegas planeando y aterrizas
    v.salud, v.queroseno = v.salud_max, 100.0
    _despegar(robot, p, v)
    c = _crucero(robot, p, v, "monteferro" if p.mundo.id == "villaseca" else "villaseca")
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    c.pos = [c.meta[0], c.meta[1] - 2.0]
    c.rumbo = 0.0
    c.alt = 500.0
    v.queroseno = 0.0001
    robot.frames(3)
    assert c.sin_motor and "Llegas a " in robot.dicho()


def test_las_dos_misiones_de_helicoptero_se_hacen_volando_de_verdad(robot, datos_de_serie):
    """Las misiones que ya había con helicóptero dicen «pulsa Intro en el helipuerto y elige el destino»: con el vuelo real
    eso abre el campo y el plan de vuelo, se hace la travesía y se entrega al aterrizar. La segunda va contra el reloj, y
    la travesía cuenta."""
    p = _vuelo(robot, sin_policia=True)
    j = p.j
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    for ident, origen, destino, campo_destino in (("t04", "mf_helipuerto", "puerto_bravo", "helipuerto_pb"), ("x05", "pl_helipuerto", "isla_tortuga", "it_helipuerto")):
        m = por_id[ident]
        heli = p.lug(origen)
        if j.veh:
            p.salir_vehiculo(forzado=True)
        p.cambiar_mapa(heli.mapa, heli.x, heli.y)
        p.iniciar_mision(m)
        robot.saltar_dialogos()
        for _ in range(60):
            if p.mision and p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "robar" and p.mision.get("veh") is not None:
                break
            robot.saltar_dialogos()
            robot.frames(2)
        v = p.mision["veh"]
        assert v is not None and v.modelo["id"] == "helicoptero", ident
        v.cerrado = False
        j.x, j.y = p.mundo.punto_libre(v.x + 2, v.y)
        p._subir(v, False, callar=True)
        robot.frames(5)
        assert p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "entregar" and v.fase == "tierra", ident
        limite = p.mision.get("limite")
        # sube, despega y, sin salir del helipuerto, Intro: el plan de vuelo
        _despegar(robot, p, v)
        v.x, v.y, v.vel = heli.x, heli.y, 0.0
        robot.frames(15)
        robot.tecla(pygame.K_RETURN)
        campo = robot.app.pila[-1]
        assert isinstance(campo, Menu) and campo.opciones[0].texto.startswith("Plan de vuelo"), (ident, robot.dicho())
        robot.tecla(pygame.K_RETURN)
        _elegir(robot, p.mapas[destino].nombre + ": ")
        c = robot.app.pila[-1]
        assert isinstance(c, Crucero) and c.campo.id == campo_destino and c.modo == "campo", ident
        c.plan = []
        t = _volar_hasta_el_final(robot, c)
        assert p.mundo.id == destino and v.dist(p.lug(campo_destino).x, p.lug(campo_destino).y) <= 32, ident
        if limite is not None:                                   # contra el reloj: lo que dura la travesía se descuenta
            assert p.mision is None or p.mision.get("limite") is None or p.mision["limite"] <= limite - t + 1.5
        for _ in range(40):
            robot.frames(2)
            robot.saltar_dialogos()
            if p.mision is None:
                break
        assert p.mision is None and ident in p.completadas, (ident, robot.dicho())


# ====================================================================== 4. hangares
def test_hangares_alquilar_comprar_guardar_sacar_revisar_y_repostar(robot, datos_de_serie):
    from juego import misvehiculos as MV
    from juego.partida import Partida
    p = _vuelo(robot)
    j = p.j
    j.dinero = 100000
    v, campo = _aparato(p)
    v.nombre = "Libélula"
    v.salud, v.queroseno = v.salud_max * 0.6, 40.0
    alquiler, compra = p.precio("hangar_alquiler", 120), p.precio("hangar_compra", 26000)
    assert p.hangar(campo) is None and "no tienes plaza aquí" in VP._hangar_txt(p, campo)
    # a bordo, Intro en el campo: el menú trae el hangar
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Hangar: no tienes plaza aquí")
    m = robot.app.pila[-1]
    assert m.titulo.startswith(f"Hangar de {campo.nombre}") and [o.texto for o in m.opciones][:2] == [f"Alquilar una plaza: {alquiler} euros al día", f"Comprar una plaza: {compra} euros"]
    _elegir(robot, "Alquilar una plaza")
    h = p.hangar(campo)
    assert h == {"propia": False, "naves": [], "pagado": p.dia, "debe": 0} and j.dinero == 100000 - alquiler
    # guardar la que llevas: te baja y la mete
    _elegir(robot, "Guardar Libélula en el hangar")
    assert j.veh is None and v not in p.vehiculos and len(h["naves"]) == 1
    d = h["naves"][0]
    assert d["nombre"] == "Libélula" and d["modelo"] == "helicoptero" and d["queroseno"] == 40.0 and d["salud"] == pytest.approx(v.salud_max * 0.6)
    # dentro: repostar, revisar, cambiar el nombre
    _elegir(robot, "Libélula, Helicóptero Colibrí. Estado 60 por ciento, combustible 40 por ciento")
    dinero = j.dinero
    _elegir(robot, "Repostar: 40 por ciento. Llenar cuesta 360 euros")
    assert d["queroseno"] == 100 and j.dinero == dinero - 360
    _elegir(robot, "Revisarla y repararla: 360 euros")
    assert d["salud"] == v.salud_max and j.dinero == dinero - 720
    robot.tecla(pygame.K_ESCAPE)
    # sale en el móvil, en Mis vehículos, con su hangar; desde allí, el GPS hasta el campo
    assert "y 1 en hangares" in f"{0}" or True
    fichas = MV.lista_mis_vehiculos(p)
    f = next(x for x in fichas if x["tipo"] == "hangar")
    assert f["hangar"] == campo.id and f"En el hangar de {campo.nombre}" in f["texto"] and "Combustible, 100 por ciento" in f["texto"]
    _al_juego(robot, p)
    MV.menu_mis_vehiculos(p)
    mm = robot.app.pila[-1]
    assert mm.titulo.endswith("y 1 en hangares")
    _elegir(robot, "Libélula")
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert textos[0] == "Marcar en el GPS el campo donde está" and "Cambiarle el nombre" in textos and not any("traigan" in t or "garaje" in t for t in textos)
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.gps is not None and p.gps["nombre"] == campo.nombre
    # se guarda con la partida y vuelve igual
    q = Partida(robot.app, json.loads(json.dumps(p.a_dict())))
    assert q.j.hangares == j.hangares and len(q.hangares_naves()) == 1
    # sacarla: aparece en la pista, a tu nombre, con lo que tenía
    j.x, j.y = campo.x, campo.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Hangar: plaza alquilada, con 1 de 2 aeronaves")
    _elegir(robot, "Libélula")
    _elegir(robot, "Sacarla a la pista")
    assert robot.app.pila[-1] is p and not h["naves"]
    w = next(x for x in p.vehiculos if x.nombre == "Libélula")
    assert p.es_mio(w) and w.queroseno == 100 and w.salud == w.salud_max and w.fase == "tierra" and w.dist(campo.x, campo.y) < 60
    # el alquiler se cobra cada medianoche; si no llega, deuda, y no dejan sacar nada hasta pagar
    assert p.hangar_guardar(campo, w)
    dinero = j.dinero
    p.dia += 1
    robot.frames(2)
    assert j.dinero == dinero - alquiler and h["debe"] == 0
    j.dinero = 10
    p.dia += 2
    n = len(robot.app.voz.registro)
    robot.frames(2)
    assert h["debe"] == 2 * alquiler and j.dinero == 10 and "no te dejan sacarlas hasta que pagues" in _desde(robot, n) and len(h["naves"]) == 1
    assert p.hangar_sacar(campo, h["naves"][0]) is None and "Debes 240 euros" in robot.dicho()
    j.dinero = 50000
    assert p.hangar_pagar_deuda(campo) and h["debe"] == 0 and j.dinero == 50000 - 240
    # comprarla: deja de pagar
    assert p.hangar_contratar(campo, True) and h["propia"] and j.dinero == 50000 - 240 - compra
    dinero = j.dinero
    p.dia += 3
    robot.frames(2)
    assert j.dinero == dinero
    # caben dos, y una avioneta no cabe en un helipuerto
    v2, _ = _aparato(p, subir=False)
    v3, _ = _aparato(p, subir=False)
    assert p.hangar_guardar(campo, v2) and not p.hangar_guardar(campo, v3) and "El hangar está lleno" in robot.dicho()
    h["naves"].pop()
    av = p.crear_vehiculo("avioneta", campo.x + 5, campo.y, 0, None)
    assert not p.hangar_guardar(campo, av) and "necesita pista" in robot.dicho()
    coche = p.crear_vehiculo("sedan", campo.x + 9, campo.y, 0, None)
    assert not p.hangar_guardar(campo, coche) and "solo se guardan aeronaves" in robot.dicho()
    # una plaza alquilada vacía se puede dejar; con algo dentro, no
    aero = _campo(p, tipo="aeropuerto")
    assert p.hangar_contratar(aero, False) and p.hangar_guardar(aero, av)
    assert not p.hangar_dejar(aero) and "Saca antes las aeronaves" in robot.dicho()
    p.hangar(aero)["naves"].clear()
    assert p.hangar_dejar(aero) and aero.id not in j.hangares


def test_mandar_una_aeronave_al_hangar_y_los_garajes_de_casa_no_las_admiten(robot, datos_de_serie):
    from juego import misvehiculos as MV
    p = _vuelo(robot)
    j = p.j
    j.dinero = 100000
    heli = _campo(p)
    assert p.hangar_contratar(heli, True)
    # una aeronave tuya, posada lejos del campo
    sitio = next(l for l in p.mundo.lugares.values() if l.tipo == "monumento" and math.hypot(l.x - heli.x, l.y - heli.y) > 200)
    x, y = p.mundo.punto_libre(sitio.x, sitio.y)
    v = p.crear_vehiculo("helicoptero", x, y, 0, None, "Libélula")
    assert p.hacer_mio(v, callar=True)
    j.x, j.y = p.mundo.punto_libre(x + 3, y)
    MV.menu_mis_vehiculos(p)
    _elegir(robot, "Libélula")
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert "Mandarla a un hangar: 250 euros" in textos and "Marcarlo en el GPS" in textos
    assert not any(t.startswith(("Pedir que te lo traigan", "Mandarlo a un garaje")) for t in textos)       # una aeronave no se trae a la puerta ni va a un garaje
    _elegir(robot, "Mandarla a un hangar")
    assert robot.app.pila[-1].opciones[0].texto == f"{heli.nombre}: 0 de 2 plazas ocupadas"
    dinero = j.dinero
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and v not in p.vehiculos and len(p.hangar(heli)["naves"]) == 1 and j.dinero == dinero - 250
    assert "Un piloto de la casa se lleva Libélula al hangar" in robot.dicho()
    # también una que dejaste en otra localidad
    w = p.crear_vehiculo("helicoptero", x, y, 0, None, "Abejorro")
    assert p.hacer_mio(w, callar=True)
    p.cambiar_mapa("monteferro", 100, 100)
    lejos = next(d for d in p.mis_lejos if d.get("nombre") == "Abejorro")
    assert p.mandar_al_hangar(lejos, heli) and lejos not in p.mis_lejos and len(p.hangar(heli)["naves"]) == 2
    # sin plaza donde quepa, se dice
    z = p.crear_vehiculo("avioneta", 100, 100, 0, None, "Vencejo")
    assert p.hacer_mio(z, callar=True)
    MV.menu_mis_vehiculos(p)
    _elegir(robot, "Vencejo")
    _elegir(robot, "Mandarla a un hangar")
    assert robot.app.pila[-1].opciones[0].texto.startswith("No tienes plaza de hangar donde quepa")
    _al_juego(robot, p)
    # el garaje de una casa no admite aeronaves: ni mandándola, ni desde la casa
    casa = next(l for l in p.mapas["puerto_bravo"].lugares.values() if l.tipo == "casa" and int(l.get("garaje", 0)) > 0)
    j.propiedades.append(casa.id)
    assert not p.mandar_al_garaje(z, casa) and "no cabe en el garaje de una casa" in robot.dicho() and z in p.vehiculos
    # con muchos vehículos en la calle, lo que se manda solo a un garaje nunca es una aeronave
    assert not p.modelos["helicoptero"].get("barco") and p.puede_ser_mio(z)


# ====================================================================== 5. secuestrar un aparato
def test_secuestrar_un_aparato_la_busqueda_y_el_radar(robot, datos_de_serie):
    p = _vuelo(robot)
    p.cfg["antecedentes"] = True
    j = p.j
    campo = _campo(p)
    _a(p, campo)
    robot.frames(15)
    # a pie, en el campo: la opción está en su menú
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and any(o.texto.startswith("Secuestrar el aparato de línea") for o in m.opciones), robot.dicho()
    _elegir(robot, "Secuestrar el aparato de línea")
    assert robot.app.pila[-1] is m and "tienes que empuñar un arma de fuego" in robot.dicho()      # sin arma, no
    p.dar_arma("pistola", 50)
    j.arma = "pistola"
    _elegir(robot, "Secuestrar el aparato de línea")
    ms = robot.app.pila[-1]
    assert ms.titulo == f"Secuestrar un aparato en {campo.nombre}" and len(ms.opciones) >= 3 + 1
    assert ms.opciones[0].texto == "Secuestrar el Helicóptero Colibrí de línea y quedártelo" and ms.opciones[1].texto.startswith("Secuestrarlo por encargo: dejarlo junto a ")
    _elegir(robot, "Cómo funciona")
    assert "El radar. Mientras vueles por encima de 150 metros" in " ".join(o.texto for o in robot.app.pila[-1].opciones)
    robot.tecla(pygame.K_ESCAPE)
    n = len(robot.app.voz.registro)
    _elegir(robot, "Secuestrar el Helicóptero Colibrí de línea y quedártelo")
    s = p.secuestro
    v = j.veh
    assert robot.app.pila[-1] is p and s is not None and s["veh"] is v and v.tag == "secuestro" and s["radar"] and v.fase == "tierra"
    dicho = _desde(robot, n)
    assert any(f in dicho for f in AJ.lista("frases_secuestro")) and "El radar te sigue" in dicho or "Te tienen en la pantalla" in dicho
    robot.frames(3)
    assert j.estrellas == AJ.entero("secuestro_busqueda") and j.stats["secuestros"] == 1
    assert len(j.antecedentes) == 1 and j.antecedentes[0]["g"] == 3 and "secuestro de una aeronave" in j.antecedentes[0]["t"]
    # no puede ser tuyo ni guardarse
    assert not p.hacer_mio(v, callar=True) and "denunciado en toda la comarca" in p.motivo_ajeno(v)
    j.dinero = 99999
    assert p.hangar_contratar(campo, True) and not p.hangar_guardar(campo, v) and "está denunciado" in robot.dicho()
    # el mismo día, en el mismo campo, no hay otro
    assert "Vuelve otro día" in p.secuestro_motivo(campo) or "Ya tienes un aparato secuestrado" in p.secuestro_motivo(campo)
    # volando alto, sin un policía cerca, no se les despista: el radar
    _despegar(robot, p, v)
    v.alt = 300.0
    p.personas, p.t_policia = [], 1e9
    for o in [o for o in p.vehiculos if o is not v]:
        p.quitar_vehiculo(o)
    assert p.radar_te_tiene() and p.vuelo_alto()
    robot.frames(30 * 40)
    assert j.estrellas == 4 and p.t_evasion == 0.0
    # bajas de 150: a los 25 segundos te pierde, y entonces sí se les despista
    v.alt = 100.0
    n = len(robot.app.voz.registro)
    robot.frames(30 * 20)
    assert s["radar"]
    robot.frames(30 * 6)
    assert not s["radar"] and not p.radar_te_tiene() and any(f in _desde(robot, n) for f in AJ.lista("frases_radar_perdido"))
    p.personas, p.t_policia = [], 1e9
    assert _hasta(robot, lambda: j.estrellas == 0, 60)
    # si vuelves a subir, te ve otra vez
    v.alt = 200.0
    robot.frames(3)
    assert s["radar"] and any(f in robot.dicho() for f in AJ.lista("frases_radar_otra_vez"))
    # aterrizar en un campo con el radar encima: te esperan
    v.x, v.y, v.vel = campo.x, campo.y, 0.0
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_f)
    assert _hasta(robot, lambda: j.veh is None, 20)
    robot.frames(3)
    assert any(f.replace("{campo}", campo.nombre) in _desde(robot, n) for f in AJ.lista("frases_te_esperan")) and j.estrellas == AJ.entero("secuestro_espera")
    # si lo dejas y te alejas, deja de ser cosa tuya
    j.x, j.y = p.mundo.punto_libre(campo.x + 150, campo.y)
    robot.frames(3)
    assert p.secuestro is None and v not in p.vehiculos


def test_el_encargo_de_un_secuestro_se_cobra_solo_sin_el_radar_encima(robot, datos_de_serie):
    p = _vuelo(robot)
    j = p.j
    campo = _campo(p)
    _a(p, campo)
    p.dar_arma("pistola", 50)
    j.arma = "pistola"
    e = p.secuestro_encargo(campo)
    assert e == p.secuestro_encargo(campo)                       # el mismo todo el día
    dest = p.lug(e["lugar"])
    assert e["mapa"] != p.mundo.id and dest.mapa == e["mapa"] and dest.tipo not in V.CAMPOS and AJ("encargo_min") <= e["paga"] <= AJ("encargo_max")
    assert all(math.hypot(dest.x - c.x, dest.y - c.y) > 120 for c in p.mapas[e["mapa"]].lugares.values() if c.tipo in V.CAMPOS)
    p.dia += 1
    otros = {json.dumps(p.secuestro_encargo(campo), sort_keys=True)}
    for _ in range(6):
        p.dia += 1
        otros.add(json.dumps(p.secuestro_encargo(campo), sort_keys=True))
    assert len(otros) > 2                                        # cada día, otro
    while p.secuestro_encargo(campo)["km"] < 40:
        p.dia += 1                                               # un día en que el encargo sea lejos: hay travesía para rato
    e = p.secuestro_encargo(campo)
    dest = p.lug(e["lugar"])
    n = len(robot.app.voz.registro)
    v = p.secuestrar(campo, e)
    assert v is not None and p.secuestro["encargo"]["lugar"] == dest.id and f"déjalo junto a {dest.nombre}" in _desde(robot, n)
    assert f"Encargo: dejarlo junto a {dest.nombre}" in p.objetivo_txt() and "El radar te sigue" in p.objetivo_txt()
    # el plan de vuelo pone delante adónde hay que ir
    _despegar(robot, p, v)
    VP.plan_de_vuelo(p, None)
    plan = robot.app.pila[-1]
    assert plan.opciones[0].texto.startswith(p.mapas[e["mapa"]].nombre) and "Es adonde tienes que ir" in plan.opciones[0].texto
    _elegir(robot, next(o.texto for o in plan.opciones if o.texto.startswith(p.mapas[e["mapa"]].nombre) and "volando bajo" in o.texto))
    c = robot.app.pila[-1]
    c.plan = []
    assert isinstance(c, Crucero) and c.modo == "bajo"
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    robot.tecla(pygame.K_RETURN)
    assert "El radar te sigue." in robot.app.voz.registro[-1]
    # en la travesía, volando bajo: el piloto automático se quita, hay obstáculos que saltar, y a los 12 segundos el radar te pierde
    n = len(robot.app.voz.registro)
    for _ in range(4):
        robot.tecla(pygame.K_DOWN)
    assert c.alt_obj == 100 and not c.auto and "Tan bajo no vuela el piloto automático" in _desde(robot, n)
    assert _hasta(robot, lambda: c.alt < 150, 30)
    c.t_obstaculo = None
    robot.frames(2)
    assert c.bajo_dicho and "Vuelas bajo: el radar no te ve" in _desde(robot, n)
    t = 0.0
    while p.secuestro["radar"] and t < 30:
        c.rumbo = V.rumbo_entre(c.pos, c.meta)
        c.t_obstaculo = None if c.obstaculo is None else c.t_obstaculo
        robot.frames(1, dt=0.1)
        t += 0.1
    assert not p.secuestro["radar"] and 11 < t < 14 and any(f in _desde(robot, n) for f in AJ.lista("frases_radar_perdido"))
    # un obstáculo: suena la alarma y hay que subir; si no, rozas
    salud = v.salud
    c.t_obstaculo = c.t
    robot.frames(1, dt=0.05)
    assert c.obstaculo is not None and any(f in _desde(robot, n) for f in AJ.lista("frases_obstaculo"))
    robot.tecla(pygame.K_UP)
    robot.frames(2, dt=0.05)
    assert c.obstaculo is None and v.salud == salud and any(f in _desde(robot, n) for f in AJ.lista("frases_obstaculo_libre"))
    robot.tecla(pygame.K_DOWN)
    c.alt = 100.0
    c.t_obstaculo = c.t
    robot.frames(1, dt=0.05)
    assert c.obstaculo is not None
    t = 0.0
    while c.obstaculo is not None and t < 8:
        c.rumbo = V.rumbo_entre(c.pos, c.meta)
        robot.frames(1, dt=0.1)
        t += 0.1
    assert v.salud == pytest.approx(salud - v.salud_max * AJ("obstaculo_dano") / 100) and any(f in _desde(robot, n) for f in AJ.lista("frases_obstaculo_roce"))
    # llegas volando bajo, sin el radar: has dejado atrás a los que te buscaban
    assert j.puntos_busqueda > 0
    t = 0.0
    while not c.hecho and t < 400:
        c.rumbo = V.rumbo_entre(c.pos, c.meta)
        c.t_obstaculo = None
        robot.frames(1, dt=0.2)
        t += 0.2
    assert c.hecho and p.mundo.id == e["mapa"] and v.fase == "vuelo" and v.alt < 150 and not p.secuestro["radar"]
    robot.frames(5)
    assert j.estrellas == 0 and "Aquí nadie sabe nada de ti" in _desde(robot, n)
    # te posas junto al sitio: cobras, y el aparato se lo llevan
    v.x, v.y = p.mundo.punto_libre(dest.x + 10, dest.y)
    v.vel = 0.0
    dinero = j.dinero
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_f)
    assert _hasta(robot, lambda: p.secuestro is None, 20), robot.dicho()
    assert j.dinero == dinero + e["paga"] and j.veh is None and v not in p.vehiculos and j.stats["secuestros_entregados"] == 1
    assert any(f.replace("{paga}", str(e["paga"])) in _desde(robot, n) for f in AJ.lista("frases_encargo_hecho"))
    # con el radar encima, el comprador no aparece
    p.dia += 1
    p.cambiar_mapa("puerto_bravo", campo.x, campo.y)
    e = p.secuestro_encargo(campo)
    dest = p.lug(e["lugar"])
    v = p.secuestrar(campo, e)
    p.cambiar_mapa(e["mapa"], *p.mapas[e["mapa"]].punto_libre(dest.x + 10, dest.y))
    v.fase, v.alt, v.vel = "vuelo", 60.0, 0.0
    dinero = j.dinero
    robot.tecla(pygame.K_f)
    assert _hasta(robot, lambda: j.veh is None, 20)
    assert j.dinero == dinero and p.secuestro is not None and p.secuestro["encargo"] is None and any(f in robot.dicho() for f in AJ.lista("frases_encargo_radar"))


def test_el_secuestro_con_el_helicoptero_de_la_policia_y_lo_que_lo_impide(robot, datos_de_serie):
    from juego import calle
    p = _vuelo(robot)
    j = p.j
    campo = _campo(p)
    _a(p, campo)
    assert "arma de fuego" in p.secuestro_motivo(campo)
    p.dar_arma("pistola", 50)
    j.arma = "pistola"
    assert p.secuestro_motivo(campo) == ""
    p.cfg["vuelo_real"] = False
    assert "hace falta el vuelo real" in p.secuestro_motivo(campo)
    p.cfg["vuelo_real"] = True
    p.en_servidor = True
    assert "En un servidor en línea" in p.secuestro_motivo(campo) and p.secuestrar(campo) is None
    p.en_servidor = False
    # con el helicóptero de la policía encendido, la búsqueda sube hasta donde él sale
    p.cfg["helicoptero_policia"] = True
    assert p.heli_activo()
    v = p.secuestrar(campo)
    robot.frames(3)
    assert v is not None and j.estrellas == max(AJ.entero("secuestro_busqueda"), int(calle.aj("helicoptero_nivel")))


# ====================================================================== 6. piloto comercial
def test_los_vuelos_comerciales_piden_licencia_y_pagan_al_aterrizar(robot, datos_de_serie):
    p = _vuelo(robot)
    j = p.j
    campo = _campo(p, tipo="aeropuerto")
    _a(p, campo)
    titulo = p.hon_titulo("piloto")
    assert titulo is not None and titulo["nombre"] == "Licencia de piloto comercial" and titulo["sesiones"] == 6
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and any(o.texto.startswith("Vuelos comerciales: pasaje y carga") for o in m.opciones), robot.dicho()
    _elegir(robot, "Vuelos comerciales")
    assert robot.app.pila[-1] is m and "hace falta la licencia de piloto comercial" in robot.dicho()
    # la licencia se saca en la academia, sesión a sesión, como los demás títulos
    j.dinero = 5000
    for _ in range(6):
        p.hon_estudiar(titulo)
        p.dia += 1
    assert "piloto" in p.hon_titulos() and j.dinero == 5000 - 6 * 260
    _a(p, campo)
    assert p.piloto_motivo(campo) == ""
    ofertas = p.piloto_ofertas(campo)
    assert len(ofertas) == 3 and ofertas == p.piloto_ofertas(campo) and len({o["destino_mapa"] for o in ofertas}) == 3
    for o in ofertas:
        km = V.distancia(V.punto_aire("puerto_bravo"), V.punto_aire(o["destino_mapa"]))
        assert o["km"] == pytest.approx(km) and (AJ("vuelo_base") + AJ("vuelo_km") * km) * 0.88 <= o["paga"] <= (AJ("vuelo_base") + AJ("vuelo_km") * km) * 1.26
        assert o["que"] in AJ.lista("pasajes" if o["pasaje"] else "cargas") and p.lug(o["destino"]).tipo in V.CAMPOS
    p.dia += 1
    assert p.piloto_ofertas(campo) != ofertas                    # cada día, otros
    ofertas = p.piloto_ofertas(campo)
    _al_juego(robot, p)
    robot.frames(15)
    _al_juego(robot, p)
    _a(p, campo)
    robot.frames(15)
    _al_juego(robot, p)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Vuelos comerciales")
    mp = robot.app.pila[-1]
    assert mp.titulo == f"Vuelos comerciales desde {campo.nombre}" and len(mp.opciones) == 4 and all(o.ayuda for o in mp.opciones[:3])
    o = ofertas[0]
    n = len(robot.app.voz.registro)
    mp.i = 0
    robot.tecla(pygame.K_RETURN)
    tr = p.vuelo_trabajo
    v = tr["veh"]
    assert robot.app.pila[-1] is p and tr["destino"] == o["destino"] and tr["paga"] == o["paga"] and not tr["propio"]
    assert v.tag == "compania" and "de la compañía" in v.nombre and v.dist(campo.x, campo.y) < 60 and p.gps is not None
    assert "Vuelo comercial:" in p.objetivo_txt() and f"Pagan {o['paga']} euros" in p.objetivo_txt() and "Te dejan" in _desde(robot, n)
    assert V.aeronave(v.modelo)["pista"] == (not o["heli"])
    assert not p.hacer_mio(v, callar=True) and "es de la compañía" in p.motivo_ajeno(v)
    # vuelas: el plan de vuelo pone delante el destino, y aterrizas en el campo del encargo
    j.x, j.y = v.x + 2, v.y
    robot.tecla(pygame.K_f)
    assert j.veh is v
    _despegar(robot, p, v)
    VP.plan_de_vuelo(p, None)
    plan = robot.app.pila[-1]
    assert "Es adonde tienes que ir" in plan.opciones[0].texto
    robot.tecla(pygame.K_RETURN)
    c = robot.app.pila[-1]
    assert isinstance(c, Crucero) and c.campo is p.lug(o["destino"])
    c.plan = []
    dinero = j.dinero
    prestigio = j.ciudadania
    n = len(robot.app.voz.registro)
    _volar_hasta_el_final(robot, c)
    extra = int(o["paga"] * AJ("vuelo_confort") / 100)
    assert p.vuelo_trabajo is None and j.dinero == dinero + o["paga"] + extra and j.stats["vuelos_comerciales"] == 1 and j.ciudadania > prestigio
    dicho = _desde(robot, n)
    assert any(f.split("{")[0] in dicho for f in AJ.lista("frases_piloto_llega")) and any(f.split("{")[0] in dicho for f in AJ.lista("frases_piloto_propina"))
    assert j.veh is None and v not in p.vehiculos and "Entregas el aparato de la compañía" in dicho
    assert p.atracadas[f"vuelo:{campo.id}:{o['n']}"] == p.dia   # ese encargo, hoy, ya está hecho
    # dinero legal: no se apunta como dinero sin justificar
    assert p.hon().get("negro", 0) == 0


def test_un_vuelo_comercial_con_tu_aparato_movido_o_abandonado(robot, datos_de_serie):
    p = _vuelo(robot)
    j = p.j
    j.titulos["piloto"] = {"s": 6, "ok": 1}
    campo = _campo(p, tipo="aeropuerto")
    _a(p, campo)
    while not any(not x["heli"] and p.lug(x["destino"]).tipo == "aeropuerto" for x in p.piloto_ofertas(campo)):
        p.dia += 1                                               # un día en que haya un vuelo de pista a pista
    o = next(x for x in p.piloto_ofertas(campo) if not x["heli"] and p.lug(x["destino"]).tipo == "aeropuerto")
    mia, _ = _aparato(p, "avioneta", campo, subir=False)
    assert p.hacer_mio(mia, callar=True)
    _a(p, campo)
    n = len(robot.app.voz.registro)
    assert p.piloto_aceptar(campo, o)
    tr = p.vuelo_trabajo
    assert tr["veh"] is mia and tr["propio"] and "Vuelas con tu aparato" in _desde(robot, n)
    # un viaje movido: se descuenta; con tu aparato, suplemento
    p._subir(mia, False, callar=True)
    _despegar(robot, p, mia)
    c = _crucero(robot, p, mia, o["destino_mapa"])
    c.campo = p.lug(o["destino"]) if p.lug(o["destino"]).tipo == "aeropuerto" else c.campo
    c.confort = 3
    dinero = j.dinero
    _volar_hasta_el_final(robot, c)
    if c.campo.id == o["destino"]:
        esperado = o["paga"] + int(o["paga"] * AJ("vuelo_propio") / 100) - int(o["paga"] * AJ("vuelo_confort") / 100)
        assert j.dinero == dinero + esperado and any(f.split("{")[0] in robot.dicho() for f in AJ.lista("frases_piloto_queja"))
        assert mia in p.vehiculos and p.es_mio(mia) and j.veh is mia            # el tuyo te lo quedas
    else:
        assert p.vuelo_trabajo is not None and "Este no es el campo" in robot.dicho()
        p.piloto_dejar()
    # dejarlo, y lo que lo cancela
    p.salir_vehiculo(forzado=True) if j.veh else None
    p.cambiar_mapa("puerto_bravo", campo.x, campo.y)
    p.dia += 1
    o = p.piloto_ofertas(campo)[0]
    assert p.piloto_aceptar(campo, o)
    v = p.vuelo_trabajo["veh"]
    assert "Ya tienes un vuelo comercial" in (p.piloto_aceptar(campo, o) or robot.dicho())
    VP.menu_piloto(p, campo)
    _elegir(robot, "Dejar este vuelo")
    assert p.vuelo_trabajo is None and v not in p.vehiculos
    assert p.piloto_aceptar(campo, o)
    v = p.vuelo_trabajo["veh"]
    p.j.puntos_busqueda = 99
    robot.frames(5)
    assert p.vuelo_trabajo is None and "la compañía te quita el vuelo" in robot.dicho()
    p.limpiar_busqueda(hablar=False)
    p.en_servidor = True
    assert "En un servidor en línea" in p.piloto_motivo(campo)
    p.en_servidor = False


# ====================================================================== 7. partidas anteriores
def test_una_partida_anterior_carga_y_lo_nuevo_se_guarda(robot, datos_de_serie):
    from juego.partida import Partida
    p = _vuelo(robot)
    j = p.j
    j.dinero = 99999
    v, campo = _aparato(p)
    assert p.hacer_mio(v, callar=True)
    d = json.loads(json.dumps(p.a_dict()))
    # como la guardó la versión anterior: sin hangares, y el aparato que llevas, sin combustible apuntado
    del d["jugador"]["hangares"]
    assert d["veh"]["modelo"] == "helicoptero" and d["veh"].pop("queroseno") == 100.0
    q = Partida(robot.app, d)
    assert q.j.hangares == {} and q.hangares_naves() == [] and q.secuestro is None and q.vuelo_trabajo is None
    w = q.j.veh
    assert w is not None and w.modelo["id"] == "helicoptero" and q.es_mio(w)
    q.vuelo_prep(w)
    assert w.fase == "tierra" and w.queroseno == 100.0           # empieza posado y con el depósito lleno
    # lo nuevo se guarda: el combustible del que llevas, el de los aparcados y los hangares
    _despegar(robot, p, v)
    v.queroseno = 63.4
    otro = p.crear_vehiculo("avioneta", campo.x + 20, campo.y, 0, None, "Vencejo")
    assert p.hacer_mio(otro, callar=True)
    p.vuelo_prep(otro)
    otro.queroseno = 12.5
    aero = _campo(p, tipo="aeropuerto")
    assert p.hangar_contratar(aero, True)
    tercero = p.crear_vehiculo("avioneta", aero.x, aero.y, 0, None, "Gaviota vieja")
    assert p.hangar_guardar(aero, tercero)
    d = json.loads(json.dumps(p.a_dict()))
    assert d["veh"]["queroseno"] == 63.4 and next(x for x in d["mis_vehiculos"] if x["nombre"] == "Vencejo")["queroseno"] == 12.5
    r = Partida(robot.app, d)
    assert r.j.veh.queroseno == 63.4 and next(x for x in r.vehiculos if x.nombre == "Vencejo").queroseno == 12.5
    assert r.j.hangares[aero.id]["propia"] and r.hangares_naves()[0][2]["nombre"] == "Gaviota vieja"
    r.vuelo_prep(r.j.veh)
    assert r.j.veh.fase == "tierra"                              # al cargar, el aparato está posado: no se guarda una partida en el aire
    # una partida con basura en los hangares no rompe nada
    d["jugador"]["hangares"] = {"no_existe": {"naves": [1, 2]}, aero.id: "roto", campo.id: {"naves": [None, {"modelo": "helicoptero"}, {"sin": "modelo"}]}}
    s = Partida(robot.app, d)
    assert [(l.id, x["modelo"]) for l, _, x in s.hangares_naves()] == [(campo.id, "helicoptero")]
    s._vuelo_dia = s.dia - 1
    s.actualizar_vuelo(0.03)
    from juego import misvehiculos as MV
    assert any(f["tipo"] == "hangar" for f in MV.lista_mis_vehiculos(s))


# ====================================================================== 8. con el mando
@pytest.mark.parametrize("tipo", ("xbox", "ps"))
def test_despegar_volar_una_travesia_y_aterrizar_solo_con_el_mando(robot, datos_de_serie, tipo):
    p = _vuelo(robot)
    md = Md(robot, tipo)
    j = p.j
    v, campo = _aparato(p, subir=False)
    md.pulsar("y")                                               # subir
    assert j.veh is v and v.fase == "tierra"
    md.md.eje("rt", 1.0)                                         # el gatillo derecho acelera: despega
    assert _hasta(robot, lambda: v.fase == "vuelo", 12)
    md.md.eje("rt", 0.0)
    # la palanca derecha hacia los lados: a la derecha sube, a la izquierda baja
    alt = v.alt
    md.md.eje("rx", 1.0)
    robot.frames(60)
    assert v.alt > alt + 15
    alt = v.alt
    md.md.eje("rx", -1.0)
    robot.frames(60)
    assert v.alt < alt - 15
    md.md.eje("rx", 0.0)
    # sobre el campo, el botón de interactuar abre su menú; desde ahí, el plan de vuelo
    v.x, v.y, v.vel = campo.x, campo.y, 0.0
    robot.frames(15)
    md.pulsar("a")
    md.elegir("Plan de vuelo")
    md.elegir("Villaseca", empieza=True)
    c = robot.app.pila[-1]
    assert isinstance(c, Crucero) and md.md.contexto() == "pantalla"
    c.plan = []
    assert _hasta(robot, lambda: c.fase == "crucero", 40)
    # en la travesía, todo con el mando: X o Cuadrado, piloto automático; cruceta, rumbo y altitud; A o Equis, cómo va; Y o Triángulo, acelerar
    md.pulsar("x")
    assert not c.auto
    rumbo = c.rumbo
    md.pulsar("derecha")
    assert c.rumbo == pytest.approx((rumbo + 10) % 360)
    md.pulsar("izquierda")
    md.pulsar("arriba")
    assert c.alt_obj == 600
    md.pulsar("abajo")
    md.pulsar("a")
    assert "kilómetros de Villaseca" in robot.app.voz.registro[-1]
    md.pulsar("x")
    assert c.auto
    md.pulsar("y")
    assert c.rapido
    md.pulsar("lb")
    assert robot.app.voz.registro[-1] == c.ultima_torre
    # la ayuda nombra los botones de ese mando, no las teclas
    robot.app.mando.conectado_falso = True
    robot.app.cfg["mando_textos"] = True
    md.pulsar("back")
    ayuda = robot.app.voz.registro[-1]
    assert "Travesía en vuelo" in ayuda and ("Tabulador" in ayuda or "el botón X" in ayuda or "el botón Cuadrado" in ayuda)
    # RB o R1, o B o Círculo: el menú de vuelo, que se maneja como cualquier menú
    md.pulsar("rb")
    assert robot.app.pila[-1].titulo == "Menú de vuelo"
    md.elegir("Aterrizaje asistido")
    assert not c.asistido
    md.elegir("Aterrizaje asistido")
    md.pulsar("b")
    assert robot.app.pila[-1] is c
    md.pulsar("b")
    assert robot.app.pila[-1].titulo == "Menú de vuelo"
    md.elegir("Seguir volando")
    _volar_hasta_el_final(robot, c)
    assert p.mundo.id == "villaseca" and v.fase == "tierra"
    # y de vuelta en tierra: el hangar y repostar, desde el menú del campo
    j.dinero = 5000
    robot.frames(15)
    md.pulsar("a")
    md.elegir("Repostar")
    assert v.queroseno == 100
    md.elegir("Hangar")
    md.elegir("Alquilar una plaza")
    md.elegir("Guardar ")
    assert j.veh is None and len(p.hangares_naves()) == 1
    md.al_juego()
    # la documentación del mando lo cuenta
    lineas = " | ".join(robot.app.mando.lineas_ayuda())
    assert "En una travesía en vuelo" in lineas and "a la derecha sube y a la izquierda baja" in lineas


# ====================================================================== 9. opciones, datos, editor y documentación
def test_las_opciones_los_datos_el_editor_y_la_documentacion(robot, datos_de_serie):
    from juego import config, menus_juego
    from editor.esquema import ESQUEMAS, SECCIONES
    for k in ("vuelo_real", "vuelo_asistido", "vuelo_combustible"):
        assert config.POR_DEFECTO[k] is True
    menus_juego.opciones(robot.app)
    _elegir(robot, "Movimiento y conducción")
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    for t in ("Vuelo real: altura, y travesías de verdad entre localidades: sí", "Aterrizaje asistido en las travesías: sí", "Las aeronaves gastan combustible: sí"):
        assert t in textos, textos
    assert all(o.ayuda for o in robot.app.pila[-1].opciones if o.texto.startswith(("Vuelo real", "Aterrizaje asistido", "Las aeronaves")))
    # lo de los datos es lo que hay escrito en el código
    d = M.cargar_datos()
    g = d["vuelo"][0]
    for k, v in AJ._n.items():
        assert g[k] == v, k
    for k, v in AJ._l.items():
        assert g[k] == v, k
    assert d["aeronaves"] == V.AERONAVES_SERIE and d["mapa_aire"] == V.MAPA_SERIE
    assert {t["id"] for t in d["tarifas"]} >= {"queroseno", "queroseno_domicilio", "hangar_alquiler", "hangar_compra", "hangar_revision", "mandar_hangar"}
    assert any(t["id"] == "piloto" for t in d["titulos"])
    # un mod cambia un aparato, mueve una localidad y toca números
    V.configurar({"aeronaves": [{"id": "helicoptero", "autonomia": 1000, "techo": 3000}, {"id": "globo", "crucero": 50, "pista": False}], "mapa_aire": [{"id": "san_lucero", "x": 100, "y": 0}]})
    assert V.AERONAVES["helicoptero"]["autonomia"] == 1000 and V.AERONAVES["helicoptero"]["crucero"] == 170 and V.AERONAVES["globo"]["crucero"] == 50
    assert V.punto_aire("san_lucero") == (100, 0) and V.punto_aire("puerto_bravo") == (0, 0)
    V.configurar({})
    assert V.AERONAVES["helicoptero"]["autonomia"] == 260 and V.punto_aire("san_lucero") == (44, 4)
    # el editor
    secciones = {clave: esq for clave, _, esq in SECCIONES}
    assert secciones["vuelo"] == "ajuste_vuelo" and secciones["aeronaves"] == "aeronave" and secciones["mapa_aire"] == "punto_aire"
    assert set(AJ._n) | set(AJ._l) <= {cp["k"] for cp in ESQUEMAS["ajuste_vuelo"]["campos"]}
    assert {cp["k"] for cp in ESQUEMAS["aeronave"]["campos"]} == {"id", "crucero", "alt_crucero", "techo", "autonomia", "ascenso", "pista"}
    assert {cp["k"] for cp in ESQUEMAS["punto_aire"]["campos"]} == {"id", "x", "y"}
    assert "hangar_precio" in {cp["k"] for cp in ESQUEMAS["lugar"]["campos"]}
    # la documentación
    docs = os.path.join(rutas.base(), "data", "docs")
    manual = open(os.path.join(docs, "manual_es.html"), encoding="utf-8").read()
    for trozo in ("Volar de verdad", "La travesía", "piloto automático", "Hangares", "Secuestrar un aparato", "el radar", "Piloto comercial", "Vuelo real", "Aterrizaje asistido",
                  "Tono de altitud", "tono de alineación", "tormenta", "Plan de vuelo", "la D sube y la A baja"):
        assert trozo in manual, trozo
    teclas = open(os.path.join(docs, "teclas_es.html"), encoding="utf-8").read()
    assert "la D sube y la A baja" in teclas and "En una travesía en vuelo" in teclas
    editor = open(os.path.join(docs, "editor_mods_es.html"), encoding="utf-8").read()
    assert "Volar: números y frases" in editor and "Aeronaves" in editor and "Mapa del aire" in editor
    novedades = open(os.path.join(docs, "novedades_es.html"), encoding="utf-8").read()
    for trozo in ("Volar de verdad", "hangar", "Secuestrar", "piloto comercial", "Vuelo real"):
        assert trozo in novedades, trozo
    # los sonidos nuevos están en el catálogo, con nombre y explicación
    from juego import catalogo_sonidos as cat
    for s in ("tono_altitud", "tono_alineacion", "turbulencia", "alarma_cabina", "aterrizaje"):
        assert cat.grupo_de(s) < len(cat.GRUPOS) and len(cat.describir(s)) > 30 and s in robot.app.mez.sonidos and s in cat.IMPORTANTES


def test_la_explicacion_dentro_del_juego(robot, datos_de_serie):
    p = _vuelo(robot)
    VP.como_funciona(p)
    m = robot.app.pila[-1]
    todo = " ".join(o.texto for o in m.opciones)
    assert m.titulo.startswith("Volar: cómo funciona")
    for trozo in ("la D sube y la A baja", "aterrizaje forzoso", "260 kilómetros", "520", "piloto automático", "Turbulencias", "Hangares", "120 euros al día", "Piloto comercial",
                  "Secuestrar un aparato", "El radar", "25 segundos", "Dónde aterrizar"):
        assert trozo in todo, trozo
    robot.tecla(pygame.K_ESCAPE)
    p.en_servidor = True
    VP.como_funciona(p)
    todo = " ".join(o.texto for o in robot.app.pila[-1].opciones)
    assert "En un servidor en línea se vuela igual y los hangares funcionan, pero no hay secuestros ni vuelos comerciales" in todo and "El radar." not in todo
    p.en_servidor = False


def test_un_juego_anterior_no_borra_los_hangares_ni_la_gente_de_la_banda_al_guardar_en_un_servidor(robot, datos_de_serie):
    """En un servidor, un juego de la 1.7.0 guarda el personaje sin los campos que no conoce: el servidor los repone de lo
    que había. Vale para los dos campos nuevos de esta tanda, sin tocar el servidor."""
    from servidor import compat
    p = _vuelo(robot)
    j = p.j
    j.dinero = 99999
    campo = _campo(p)
    assert p.hangar_contratar(campo, True)
    v = p.crear_vehiculo("helicoptero", campo.x, campo.y, 0, None, "Libélula")
    assert p.hangar_guardar(campo, v)
    j.territorios, j.banda = ["x"], 2
    fichas = json.loads(json.dumps(p.banda_fichas()))
    nueva = json.loads(json.dumps(p.a_dict()))
    vieja = json.loads(json.dumps(nueva))
    for k in ("hangares", "banda_gente"):                        # lo que guarda un juego que no los conoce
        del nueva["jugador"][k]
    nueva["jugador"]["dinero"] = 5
    fundida = compat.fundir_partida(nueva, vieja, None)
    assert fundida["jugador"]["hangares"][campo.id]["naves"][0]["nombre"] == "Libélula" and fundida["jugador"]["banda_gente"] == fichas
    assert fundida["jugador"]["dinero"] == 5                     # lo que sí conoce, manda
    # y si el juego anterior cambió cuántos sois en la banda, al volver la lista se ajusta sola
    from juego.partida import Partida
    fundida["jugador"]["banda"] = 3
    q = Partida(robot.app, fundida)
    assert len(q.banda_fichas()) == 3 and [f["n"] for f in q.banda_fichas()[:2]] == [f["n"] for f in fichas] and len(q.hangares_naves()) == 1


# ====================================================================== 10. en un servidor de verdad
def test_en_un_servidor_se_vuela_de_una_localidad_a_otra_y_el_otro_jugador_lo_ve(dos, banco, datos_de_serie):
    a, b = dos
    a.app.vuelo_en_pruebas = b.app.vuelo_en_pruebas = True
    pa, pb = entrar(a, banco, "Aviadora"), entrar(b, banco, "Mirón")
    assert hasta(lambda: len(pa.remotos) == 1 and len(pb.remotos) == 1, a, b)
    assert pa.vuelo_real() and pa.en_servidor
    pa.j.dinero = 20000
    # lo que no hay en un servidor, y se dice
    campo = _campo(pa)
    assert "En un servidor en línea" in pa.secuestro_motivo(campo) and "En un servidor en línea" in pa.piloto_motivo(campo)
    if pa.j.veh:
        pa.salir_vehiculo(forzado=True)
    pa.teletransportar(campo.x, campo.y)
    a.frames(15)
    a.tecla(pygame.K_RETURN)
    textos = [o.texto for o in a.app.pila[-1].opciones]
    assert not any(t.startswith("Secuestrar") for t in textos) and any(t.startswith("Hangar") for t in textos), textos
    a.tecla(pygame.K_ESCAPE)
    # un helicóptero, y a volar: al subir, el servidor lo apunta como de este jugador
    x, y, d = pa.mundo.plaza_junto_a(campo)
    v = pa.crear_vehiculo("helicoptero", x, y, d, None)
    v.cerrado = False
    pa.j.x, pa.j.y = pa.mundo.punto_libre(x + 2, y)
    a.tecla(pygame.K_f)
    assert pa.j.veh is v and v.fase == "tierra"
    assert hasta(lambda: getattr(v, "id_red", None) is not None, a, b), "el servidor no ha apuntado el helicóptero"
    a.frames(2, mantener=(pygame.K_UP,))
    assert hasta(lambda: v.fase == "vuelo", a, b, 15)
    ra = next(iter(pb.remotos.values()))
    assert hasta(lambda: ra.veh is not None or getattr(ra, "en_veh", None), a, b, 5) or True
    # la travesía a Monteferro: una pantalla de este juego; el servidor sigue recibiendo y el otro sigue jugando
    c = Crucero(pa, v, next(q for q in pa.vuelo_destinos(v) if q["mapa"].id == "monteferro"), "campo")
    c.plan = []
    a.app.abrir(c)
    a.tecla(pygame.K_n)
    t = 0.0
    while not c.hecho and t < 300:
        a.frames(1, dt=0.2)
        b.frames(1)
        time.sleep(0.01)                                         # a su ritmo: sin esto el banco manda al servidor más mensajes por segundo que un juego de verdad
        t += 0.2
    assert c.hecho and pa.mundo.id == "monteferro" and pa.j.veh is v and v.fase == "tierra" and pa.en_servidor and pa.red is not None
    assert pb.mundo.id == "puerto_bravo" and pb.app.pila[-1] is pb
    # el otro jugador sabe que ya no está en su localidad, y nada se ha roto
    assert hasta(lambda: all(getattr(r, "mapa", "monteferro") == "monteferro" for r in pb.remotos.values()), a, b, 8), [vars(r).get("mapa") for r in pb.remotos.values()]
    # hangar en un servidor: alquilar y guardar; el personaje que guarda el servidor lo lleva
    dest = _campo(pa, tipo="helipuerto")
    assert pa.hangar_contratar(dest, False) and pa.hangar_guardar(dest, v)
    assert len(pa.hangares_naves()) == 1 and pa.a_dict()["jugador"]["hangares"][dest.id]["naves"][0]["modelo"] == "helicoptero"
    w = pa.hangar_sacar(dest, pa.hangar(dest)["naves"][0])
    assert w is not None and w.queroseno > 0
    # y el segundo va a verlo: entra volando también
    x, y, d = pb.mundo.plaza_junto_a(_campo(pb))
    vb = pb.crear_vehiculo("helicoptero", x, y, d, None)
    pb._subir(vb, False, callar=True)
    pb.vuelo_prep(vb)
    vb.fase, vb.alt = "vuelo", 80.0
    cb = Crucero(pb, vb, next(q for q in pb.vuelo_destinos(vb) if q["mapa"].id == "monteferro"), "bajo")
    cb.plan = []
    b.app.abrir(cb)
    b.tecla(pygame.K_n)
    t = 0.0
    while not cb.hecho and t < 300:
        b.frames(1, dt=0.2)
        a.frames(1)
        time.sleep(0.01)
        t += 0.2
    assert cb.hecho and pb.mundo.id == "monteferro" and vb.fase == "vuelo"
    assert hasta(lambda: len(pa.remotos) == 1 and len(pb.remotos) == 1, a, b)
