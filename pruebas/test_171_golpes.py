"""Trabajo 1.7.1, tanda 19, parte 1: golpes preparados. Cada uno de tu banda con su papel (conductor, vigilante, escolta,
el de la caja y tirador), las cinco fases habladas, la caja que tarda en abrirse, lo que puede salir mal, el reparto, y
que sin banda, sin prepararlo o en un servidor todo sigue como estaba."""
import json
import math
import os

import pygame
import pytest

from juego import golpes as GO, mundo as M, rutas, sistemas
from juego.combate import UMBRAL
from juego.entidades import Persona
from juego.menus import Menu
from test_171_mando import Md, _a, _empezar, _hasta


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


def _banda(p, n=5, **attrs):
    """Una banda de n, todos a tu lado, con las aptitudes que se digan (las demás, 60)."""
    j = p.j
    j.territorios = [b["id"] for b in p.mundo.barrios[:5]]
    j.banda_nombre = "Los Mirlos"
    j.banda = n
    j.banda_gente = []
    for f in p.banda_fichas():
        f.update({"punteria": 60, "conduccion": 60, "nervios": 60, "lealtad": 60})
        f.update(attrs)
    num, _ = sistemas.llamar(p)
    assert num == n
    return list(p.banda_fichas())


def _armado(p):
    p.dar_arma("pistola", 200)
    p.j.arma = "pistola"


def _plan(fichas, dentro="caja", huida="conducir", modelo=None, **papeles):
    """Un plan: papel=índice de la ficha."""
    return {"papeles": {str(fichas[k]["id"]): pid for pid, k in papeles.items()}, "yo": {"dentro": dentro, "huida": huida}, "veh_id": None, "modelo": modelo}


def _sin_azar(monkeypatch, **fallos):
    """El sorteo de lo que sale mal, a mano: nada, salvo lo que se pida."""
    def sortear(self, g):
        g["heroe"], g["alarma_antes"], g["evitado"] = fallos.get("heroe"), fallos.get("alarma_antes"), dict(fallos.get("evitado", {"heroe": False, "alarma": False}))
        g["fallos"].update({k: v for k, v in fallos.items() if k not in ("heroe", "alarma_antes", "evitado")})
    monkeypatch.setattr(GO.Golpes, "_golpe_sortear", sortear)


def _local(p, tipo):
    return next(l for l in p.mundo.lugares.values() if l.tipo == tipo)


def _desde(robot, n):
    return " | ".join(robot.app.voz.registro[n:])


def _abrir_caja(robot, p, tope=60.0):
    """Va a la caja, pulsa Intro y espera a que se abra."""
    o = p.mision["objeto"]
    assert o is not None
    p.j.x, p.j.y = o.x, o.y
    robot.tecla(pygame.K_RETURN)
    assert p.mision["abriendo"] is not None, robot.dicho()
    assert _hasta(robot, lambda: p.mision is None or p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] != "recoger", tope), robot.dicho()


def _matar_guardias(robot, p):
    assert _hasta(robot, lambda: p.mision.get("generado"), 5)
    for e in list(p.mision["enemigos"]):
        e.salud = 0
        e.muerto = True
    assert _hasta(robot, lambda: p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "recoger", 5), robot.dicho()


def _huir(robot, p):
    """Te pierdes de vista hasta que dejan de buscarte."""
    p.personas = [q for q in p.personas if q.tipo != "policia"]
    for v in [v for v in p.vehiculos if v.ia == "policia"]:
        p.quitar_vehiculo(v)
    p.limpiar_busqueda(hablar=False)
    robot.frames(3)


# ====================================================================== 1. la gente de la banda, uno por uno
def test_cada_uno_de_la_banda_tiene_nombre_y_aptitudes_que_se_guardan(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    j.territorios = [b["id"] for b in p.mundo.barrios[:4]]
    j.banda_nombre = "Los Mirlos"
    j.banda = 3                                                  # como una partida anterior: solo sabía cuántos erais
    assert j.banda_gente == []
    fichas = p.banda_fichas()
    assert len(fichas) == 3 and len({f["n"] for f in fichas}) == 3 and len({f["id"] for f in fichas}) == 3
    a, b = GO.AJ.entero("atributo_min"), GO.AJ.entero("atributo_max")
    for f in fichas:
        assert all(a <= f[k] <= b for k in ("punteria", "conduccion", "nervios")) and 0 < f["lealtad"] <= 100 and f["exp"] == 0
    # no son todos iguales: hay variación
    vistas = set()
    for _ in range(12):
        vistas.add(tuple(p._ficha_banda()[k] for k in ("punteria", "conduccion", "nervios")))
    assert len(vistas) > 6
    # se guardan y vuelven idénticos
    d = json.loads(json.dumps(p.a_dict()))
    from juego.partida import Partida
    q = Partida(robot.app, d)
    assert q.j.banda_gente == fichas and q.banda_fichas() == fichas
    # reclutar pagando añade a uno con nombre, y lo dice
    j.dinero = 5000
    ok, frase = sistemas.reclutar(p)
    assert ok and j.banda == 4 and len(p.banda_fichas()) == 4 and p.banda_fichas()[-1]["n"] in frase
    # al llamarlos, cada uno llega con su nombre
    n, _ = sistemas.llamar(p)
    assert n == 4
    nombres = sorted(e.nombre for e in sistemas.miembros_presentes(p))
    assert nombres == sorted(f"{f['n']}, de Los Mirlos" for f in p.banda_fichas())
    # si matas a uno de los tuyos, se borra ese y no otro
    p.cfg["fuego_amigo"] = True
    e = sistemas.miembros_presentes(p)[1]
    quien = p.banda_ficha(e.bid)["n"]
    p.danar_persona(e, 999)
    assert j.banda == 3 and quien not in [f["n"] for f in p.banda_fichas()] and len(p.banda_fichas()) == 3
    # si no llega para pagar, se va el último; y sin territorios, todos
    j.dinero = 0
    sistemas.paga(p)
    assert j.banda == 2 and len(p.banda_fichas()) == 2
    j.territorios = []
    sistemas.paga(p)
    assert j.banda == 0 and p.banda_fichas() == []
    # una lista con basura en una partida guardada no rompe nada
    j.territorios, j.banda, j.banda_gente = ["x"], 2, [None, {"n": ""}, {"n": "Rosa", "punteria": "mucha"}, 7]
    fichas = p.banda_fichas()
    assert len(fichas) == 2 and fichas[0]["n"] == "Rosa" and fichas[0]["punteria"] == 50


def test_el_reclutado_de_la_calle_entra_con_su_nombre_y_su_caracter(robot, datos_de_serie):
    from juego.charla import ficha
    p = _empezar(robot)
    j = p.j
    j.territorios = [b["id"] for b in p.mundo.barrios[:3]]
    j.reputacion, j.dinero = 80, 5000
    q = Persona("civil", j.x + 2, j.y)
    p.personas.append(q)
    f = ficha(q)
    f.update(edad=30, confianza=90, caracter="chulo")
    ok, frase = p.reclutar_persona(q)
    assert ok, frase
    mia = p.banda_fichas()[-1]
    assert mia["n"] == f["nombre"] and q.bid == mia["id"] and mia["lealtad"] == 95 and mia["nervios"] == 81 and q.nombre.startswith(f["nombre"])
    assert [e for e, x in p.banda_ligar() if x is mia] == [q]


# ====================================================================== 2. el menú
def test_el_menu_de_preparar_reparte_los_papeles_y_dice_el_reparto(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 3)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    for e in sistemas.miembros_presentes(p):
        e.x, e.y = p.j.x + 2, p.j.y
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    textos = [o.texto for o in m.opciones]
    assert any(t.startswith("Atracar este local") for t in textos) and any(t.startswith("Preparar el golpe con tu banda") for t in textos)
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Preparar el golpe"))
    robot.tecla(pygame.K_RETURN)
    pm = robot.app.pila[-1]
    assert pm.titulo.startswith(f"Preparar el golpe: {far.nombre}. Tienes al lado a 3 de Los Mirlos")
    textos = [o.texto for o in pm.opciones]
    assert textos[0].startswith("Cómo funciona esto") and all(any(t.startswith(f["n"] + ": sin papel") for t in textos) for f in fichas)
    assert "Tú, dentro: abres tú la caja" in textos and "Tú, en la huida: conduces tú" in textos and any(t.startswith("Reparto: nadie tiene papel") for t in textos)
    assert not any(t.startswith("Vehículo de la huida") for t in textos)
    # sin papeles no empieza
    pm.i = next(k for k, o in enumerate(pm.opciones) if o.texto.startswith("Empezar"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is pm and "Nadie tiene papel todavía" in robot.dicho() and p.mision is None
    # cubrir pide alguien en la caja; ir de pasajero, un conductor
    for texto, aviso in (("Tú, dentro", "Para cubrir tiene que haber alguien que abra la caja"), ("Tú, en la huida", "Para ir de pasajero tiene que haber conductor")):
        pm.i = next(k for k, o in enumerate(pm.opciones) if o.texto.startswith(texto))
        robot.tecla(pygame.K_RETURN)
        assert aviso in robot.dicho()

    def dar(k, papel_nombre):
        pm.i = next(i for i, o in enumerate(pm.opciones) if o.texto.startswith(fichas[k]["n"] + ":"))
        robot.tecla(pygame.K_RETURN)
        sub = robot.app.pila[-1]
        assert sub.titulo.startswith(f"Papel de {fichas[k]['n']}") and len(sub.opciones) == len(GO.PAPELES) + 2
        assert all(o.ayuda for o in sub.opciones[:len(GO.PAPELES) + 1])
        sub.i = next(i for i, o in enumerate(sub.opciones) if o.texto.startswith(papel_nombre))
        robot.tecla(pygame.K_RETURN)
        assert robot.app.pila[-1] is pm
    dar(0, "Conductor")
    dar(1, "El de la caja")
    dar(2, "Conductor")                                          # el papel pasa al tercero: el primero se queda sin él
    pm.refrescar(False)
    textos = [o.texto for o in pm.opciones]
    assert f"{fichas[0]['n']}: sin papel, viene contigo" in textos and f"{fichas[2]['n']}: conductor" in textos and f"{fichas[1]['n']}: el de la caja" in textos
    assert any(t.startswith("Vehículo de la huida") for t in textos)
    assert any(t.startswith("Reparto: tu gente se lleva el 20 por ciento y tú el 80. Hoy, de unos ") for t in textos)
    for texto, queda in (("Tú, dentro", "Tú, dentro: cubres a quien abre la caja"), ("Tú, en la huida", "Tú, en la huida: vas de pasajero")):
        pm.i = next(k for k, o in enumerate(pm.opciones) if o.texto.startswith(texto))
        robot.tecla(pygame.K_RETURN)
        assert pm.opciones[pm.i].texto == queda
    # el vehículo: los de la banda y, si hay uno tuyo cerca, el tuyo
    mio = p.crear_vehiculo("sedan", p.j.x + 8, p.j.y, 1, None, "Rayo")
    assert p.hacer_mio(mio, callar=True)
    pm.i = next(k for k, o in enumerate(pm.opciones) if o.texto.startswith("Vehículo de la huida"))
    robot.tecla(pygame.K_RETURN)
    sub = robot.app.pila[-1]
    assert sub.opciones[0].texto.startswith("Rayo, que está a") and any("de Los Mirlos" in o.texto for o in sub.opciones)
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is pm and "Vehículo de la huida: Rayo" in robot.dicho()
    # la explicación está, y cuenta los cinco papeles con sus partes
    pm.i = 0
    robot.tecla(pygame.K_RETURN)
    ex = robot.app.pila[-1]
    todo = " ".join(o.texto for o in ex.opciones)
    for x in GO.PAPELES:
        assert x["nombre"] in todo and f"Se lleva el {int(x['parte'])} por ciento del botín" in todo
    assert "entrada, control, caja, salida y huida" in todo and "En un servidor en línea" in todo
    robot.tecla(pygame.K_ESCAPE)
    # y empieza con ese plan
    pm.i = next(k for k, o in enumerate(pm.opciones) if o.texto.startswith("Empezar"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.golpe is not None and p.mision["def"]["golpe"]["yo"] == {"dentro": "cubrir", "huida": "pasajero"}
    assert {r["efecto"] for r in p.golpe["papeles"].values()} == {"conductor", "caja"} and p.golpe["veh"] is mio


# ====================================================================== 3. un golpe entero, de la entrada a la huida
def test_un_golpe_entero_a_un_local_sin_guardia_con_sus_cinco_fases_y_el_reparto(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 5)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    j = p.j
    dinero = j.dinero
    botin = p.caja_de_local(far)["dinero"]
    n = len(robot.app.voz.registro)
    son = []
    son_real = p.son
    monkeypatch.setattr(p, "son", lambda nombre, *a, **k: (son.append(nombre), son_real(nombre, *a, **k))[1])
    assert p.atracar_local(far, _plan(fichas, conductor=0, vigilante=1, escolta=2, caja=3, tirador=4, modelo="sedan"))
    g = p.golpe
    assert g is not None and p.mision["def"]["id"] == "atraco_local" and j.dinero == dinero        # la caja ya no se vacía en el acto
    assert [x["tipo"] for x in p.mision["def"]["pasos"]] == ["recoger", "policia"] and p.mision["def"]["pasos"][0]["tarda"] >= GO.AJ("caja_min")
    dicho = _desde(robot, n)
    assert "Fase uno, entrada" in dicho and f"{fichas[1]['n']}, por la radio:" in dicho and f"{fichas[0]['n']}, por la radio:" in dicho and "emisora" in son
    # el conductor espera en la puerta con el motor en marcha; el vigilante, en su esquina
    v = g["veh"]
    assert v is not None and v.tag == "banda" and v.canal is not None and v.en_marcha and v.dist(far.x, far.y) < 40 and "Conducirás tú" in dicho
    robot.frames(180)
    vig = next(r["persona"] for r in g["papeles"].values() if r["efecto"] == "vigilante")
    assert vig.puesto is not None and vig.dist(*vig.puesto) < 3 and vig.dist(*p.pos()) > 8
    assert "Fase dos, control" in _desde(robot, n) and g["fase"] == "control"
    # la caja: hay que ir, pulsar Intro y esperar; con el de la caja va más deprisa
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    robot.tecla(pygame.K_RETURN)
    ab = p.mision["abriendo"]
    base = p.mision["def"]["pasos"][0]["tarda"]
    assert ab is not None and o in p.objetos and ab["total"] == pytest.approx(base * (1 - 0.5 * 0.6))      # 60 de nervios: un 30 por ciento menos
    assert "Fase tres" in _desde(robot, n) and g["fase"] == "caja"
    robot.frames(30)
    assert ab["canal"] is not None and "ganzua" in son and 0.9 < ab["t"] < 1.1
    # si te apartas, se para, y lo dice quien la abre; al volver, sigue
    j.x += 12
    robot.frames(30)
    t = ab["t"]
    assert ab["pausa"] and ab["canal"] is None
    robot.frames(30)
    assert ab["t"] == t
    j.x, j.y = o.x, o.y
    robot.frames(3)
    assert not ab["pausa"] and "Sigue abriéndose" in _desde(robot, n)
    assert "Se está abriendo: faltan unos" in p.objetivo_txt() and "Golpe preparado, fase 3 de 5: la caja" in p.objetivo_txt()
    assert _hasta(robot, lambda: p.mision["paso"] == 1, 30), robot.dicho()
    dicho = _desde(robot, n)
    assert "Va por la mitad" in dicho or "Ya cede" in dicho
    assert "¡Abierta!" in dicho or "¡Ya está!" in dicho
    # salida: salta la alarma, el vigilante dice cuánto falta y la policía aún no ha llegado
    assert "Fase cuatro, salida" in dicho and g["alarma"] is not None and not g["llegado"] and j.estrellas == 0 and j.puntos_busqueda == 0
    espera = g["llegan"] - g["alarma"]
    assert espera == pytest.approx(GO.AJ("vigilante_retraso") * (0.5 + 0.75 * 0.6))
    assert p.mision["policia_en"] is not None and "La policía tarda aún unos" in p.objetivo_txt()
    robot.frames(90)
    assert p.mision is not None and j.estrellas == 0                                           # no se da por despistada antes de que llegue
    # subes al coche de la huida: motor en marcha (no suena el arranque) y ventaja del conductor
    son.clear()
    j.x, j.y = v.x + 2, v.y
    robot.tecla(pygame.K_f)
    assert j.veh is v and "arranque" not in son
    robot.frames(2)
    assert g["subido"] and g["llegan"] - g["alarma"] == pytest.approx(espera + GO.AJ("conductor_ventaja") * (0.5 + 0.75 * 0.6)) and "Ventaja: la policía tardará" in _desde(robot, n)
    # llega la policía: cae la búsqueda y empieza la huida
    assert _hasta(robot, lambda: g["llegado"], 60)
    robot.frames(3)
    nivel = p.caja_de_local(far)["busqueda"]
    assert j.estrellas == nivel and p.mision["policia_en"] is None and "Fase cinco, huida" in _desde(robot, n)
    dicho = _desde(robot, n)
    assert any(f in dicho for f in ("¡Ya se oyen las sirenas!", "Vienen por la avenida")) and any(f in dicho for f in ("¡Ya están aquí!", "¡Policía en la puerta!"))
    # el tirador dispara a los que os siguen
    pat = p.crear_vehiculo("patrulla", v.x - 20, v.y, v.dir, "policia")
    pat.hostil = True
    salud = pat.salud
    monkeypatch.setattr(GO.random, "random", lambda: 0.0)
    for _ in range(200):
        robot.frames(1)
        pat.x, pat.y = v.x - 20, v.y
        if pat.salud < salud:
            break
    monkeypatch.undo()
    _sin_azar(monkeypatch)
    assert pat.salud < salud and "disparo_pistola" in son and g.get("tirador_aciertos", 0) >= 1
    # despistas a la policía: reparto, experiencia y lealtad
    _huir(robot, p)
    assert _hasta(robot, lambda: p.mision is None, 10), robot.dicho()
    assert p.golpe is None
    partes = [int(botin * x / 100) for x in (10, 8, 8, 10, 8)]
    assert j.dinero == dinero + botin - sum(partes)
    dicho = _desde(robot, n)
    assert "Reparto:" in dicho or "Cada uno lo suyo:" in dicho
    assert all(f"{f['n']}, {e} euros" in dicho for f, e in zip(fichas, partes))
    assert all(f["exp"] == 1 and f["lealtad"] == 60 + GO.AJ.entero("lealtad_exito") for f in p.banda_fichas())
    assert j.stats["golpes_preparados"] == 1 and p.atracadas[far.id] == p.dia
    # el coche de la banda sigue contigo mientras vas en él, y los tuyos vuelven a seguirte
    assert j.veh is v and all(getattr(e, "puesto", None) is None for e in p.personas)


def test_con_guardia_el_escolta_y_cubrir_mientras_otro_abre_la_caja(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch, evitado={"heroe": True, "alarma": True})
    p = _empezar(robot)
    fichas = _banda(p, 2)
    _armado(p)
    arm = _local(p, "armeria")
    _a(p, arm)
    n = len(robot.app.voz.registro)
    assert p.atracar_local(arm, _plan(fichas, dentro="cubrir", escolta=0, caja=1))
    g = p.golpe
    assert [x["tipo"] for x in p.mision["def"]["pasos"]] == ["eliminar", "recoger", "policia"] and g["cubrir"] and g["guardias"]
    assert "Fase dos, control" in _desde(robot, n)                 # va delante del texto del paso de los guardias
    _matar_guardias(robot, p)
    # no hace falta tocar la caja: la abre él mientras estés a menos de 25 metros
    o = p.mision["objeto"]
    p.j.x, p.j.y = p.mundo.punto_libre(o.x + 12, o.y)
    assert _hasta(robot, lambda: p.mision.get("abriendo") is not None, 3), robot.dicho()
    dicho = _desde(robot, n)
    assert any(f.split("{")[0] in dicho for f in GO.AJ.lista("radio_caja_empieza")) and "Empiezas a abrir" not in dicho
    # el escolta avisa de lo que ha evitado
    assert _hasta(robot, lambda: p.mision["paso"] == 2, 40), robot.dicho()
    dicho = _desde(robot, n)
    assert any(f in dicho for f in GO.AJ.lista("radio_escolta_heroe")) and any(f in dicho for f in GO.AJ.lista("radio_escolta_alarma"))
    # sin vigilante, la policía llega en el acto
    robot.frames(3)
    assert g["llegado"] and p.j.estrellas == p.caja_de_local(arm)["busqueda"]
    # si te alejas más de la cuenta mientras abre, se planta
    _huir(robot, p)
    assert _hasta(robot, lambda: p.mision is None, 10)


def test_lejos_de_quien_abre_la_caja_se_planta(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 1)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    n = len(robot.app.voz.registro)
    assert p.atracar_local(far, _plan(fichas, dentro="cubrir", caja=0))
    assert _hasta(robot, lambda: p.mision.get("abriendo") is not None, 3)
    ab = p.mision["abriendo"]
    p.j.x, p.j.y = p.mundo.punto_libre(p.j.x + 60, p.j.y)
    robot.frames(10)
    assert ab["pausa"] and any(f in _desde(robot, n) for f in GO.AJ.lista("radio_caja_solo"))


# ====================================================================== 4. lo que vale cada uno
def test_cada_uno_rinde_segun_lo_que_vale_y_lo_que_ha_aprendido(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 2)
    assert p.aptitud({"nervios": 40, "exp": 0}, "nervios") == pytest.approx(0.40)
    assert p.aptitud({"nervios": 40, "exp": 2}, "nervios") == pytest.approx(0.46)
    assert p.aptitud({"nervios": 40, "exp": 50}, "nervios") == pytest.approx(0.55)      # la experiencia tiene tope
    assert p.aptitud({"nervios": 99, "exp": 5}, "nervios") == 1.0 and p.aptitud({"nervios": 0}, "nervios") == 0.05
    _armado(p)
    far = _local(p, "farmacia")
    tiempos, esperas = {}, {}
    for nervios in (20, 90):
        _a(p, far)
        for f in fichas:
            f["nervios"] = nervios
        p.atracadas.clear()
        p.j.locales_vetados.clear()
        assert p.atracar_local(far, _plan(fichas, caja=0, vigilante=1))
        o = p.mision["objeto"]
        p.j.x, p.j.y = o.x, o.y
        robot.tecla(pygame.K_RETURN)
        tiempos[nervios] = p.mision["abriendo"]["total"] / p.mision["def"]["pasos"][0]["tarda"]
        assert _hasta(robot, lambda: p.mision["paso"] == 1, 40)
        esperas[nervios] = p.golpe["llegan"] - p.golpe["alarma"]
        p.abandonar_mision()
        assert p.golpe is None
    assert tiempos[20] == pytest.approx(0.9) and tiempos[90] == pytest.approx(0.55)
    assert esperas[90] > esperas[20] * 1.5 and esperas[20] == pytest.approx(22 * (0.5 + 0.75 * 0.2))


# ====================================================================== 5. lo que puede salir mal
def test_los_nervios_el_que_llega_tarde_el_herido_el_detenido_y_el_que_delata(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch, caja="nervios", conductor="tarde", vigilante="dormido", vigilante_detenido=True, escolta=1.0)
    GO.AJ.n["tarde_min"] = GO.AJ.n["tarde_max"] = 3.0            # que el conductor llegue antes de que dé tiempo a despistar a nadie
    p = _empezar(robot)
    p.cfg["antecedentes"] = True
    fichas = _banda(p, 4, lealtad=20)
    _armado(p)
    arm = _local(p, "armeria")
    _a(p, arm)
    j = p.j
    n = len(robot.app.voz.registro)
    assert p.atracar_local(arm, _plan(fichas, conductor=0, vigilante=1, escolta=2, caja=3))
    g = p.golpe
    assert g["veh"] is None and g["tarde"] is not None and any(f in _desde(robot, n) for f in GO.AJ.lista("radio_conductor_tarde"))
    # al escolta lo hieren en el tiroteo: fuera del golpe y de baja unos días
    assert _hasta(robot, lambda: p.mision.get("generado"), 5)
    assert _hasta(robot, lambda: g["heridos"], 5), robot.dicho()
    herido = fichas[2]
    assert g["heridos"] == [herido["n"]] and p.dia < herido["baja"] <= p.dia + GO.AJ.entero("herido_dias_max") and "Estará de baja" in _desde(robot, n)
    assert not any(getattr(e, "bid", None) == herido["id"] for e in p.personas) and "Está de baja, herido" in p.ficha_banda_txt(herido)
    _matar_guardias(robot, p)
    # al de la caja le pueden los nervios: tarda más que tú solo
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    robot.tecla(pygame.K_RETURN)
    assert p.mision["abriendo"]["total"] == pytest.approx(p.mision["def"]["pasos"][1]["tarda"] * 1.4)
    assert any(f in _desde(robot, n) for f in GO.AJ.lista("radio_caja_nervios"))
    assert _hasta(robot, lambda: p.mision["paso"] == 2, 60)
    # el vigilante no avisa: la policía llega ya; a él lo cogen y, con poca lealtad, da tu nombre
    robot.frames(3)
    dicho = _desde(robot, n)
    nivel = p.caja_de_local(arm)["busqueda"]
    assert g["llegado"] and any(f in dicho for f in GO.AJ.lista("radio_vigilante_falla"))
    assert g["detenidos"] == [fichas[1]["n"]] and j.banda == 3 and fichas[1]["n"] not in [f["n"] for f in p.banda_fichas()]
    assert any(f.replace("{nombre}", fichas[1]["n"]) in dicho for f in GO.AJ.lista("frases_delata"))
    assert j.estrellas == nivel + 1 and j.stats["banda_delaciones"] == 1 and len(j.antecedentes) == 1 and "señalado por un detenido" in j.antecedentes[0]["t"]
    # el conductor llega con retraso, cuando ya ha saltado todo
    assert g["veh"] is None
    assert _hasta(robot, lambda: g["veh"] is not None, 40), robot.dicho()
    assert any(f in _desde(robot, n) for f in GO.AJ.lista("radio_conductor_llega"))
    # al acabar: el detenido no cobra; el herido sí
    dinero, botin = j.dinero, g["botin"]
    _huir(robot, p)
    assert _hasta(robot, lambda: p.mision is None, 10)
    assert j.dinero == dinero + botin - int(botin * 0.10) - int(botin * 0.08) - int(botin * 0.10)
    assert "cobra igual, pero no podrá trabajar" in _desde(robot, n)
    # el herido no acude ni se puede llevar a otro golpe hasta que se cure
    assert herido["id"] not in [f["id"] for _, f in p.golpe_presentes()]
    num, frase = sistemas.llamar(p)
    assert num == 0 and "Falta uno, que está de baja, curándose" in frase and herido["id"] not in [getattr(e, "bid", None) for e in sistemas.miembros_presentes(p)]
    p.dia = herido["baja"] + 1
    num, _ = sistemas.llamar(p)
    assert num == 1 and herido["id"] in [f["id"] for _, f in p.golpe_presentes()]


def test_un_detenido_leal_no_delata_y_un_heroe_y_la_alarma_antes_de_tiempo(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch, vigilante_detenido=True, heroe=0.1, alarma_antes=0.25)
    p = _empezar(robot)
    fichas = _banda(p, 1, lealtad=90)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    j = p.j
    n = len(robot.app.voz.registro)
    assert p.atracar_local(far, _plan(fichas, vigilante=0))
    g = p.golpe
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    robot.tecla(pygame.K_RETURN)
    assert p.mision["abriendo"]["total"] == pytest.approx(p.mision["def"]["pasos"][0]["tarda"])      # sin el de la caja, lo que diga el local
    # un héroe: alguien que te ataca mientras abres
    assert _hasta(robot, lambda: g.get("heroe_persona") is not None, 5)
    h = g["heroe_persona"]
    assert h.hostil and h in p.personas and any(f in _desde(robot, n) for f in GO.AJ.lista("frases_heroe"))
    h.muerto = True
    # la alarma salta antes de acabar: la policía ya viene mientras sigues con la caja
    assert _hasta(robot, lambda: g["alarma"] is not None, 5)
    assert p.mision["paso"] == 0 and any(f in _desde(robot, n) for f in GO.AJ.lista("frases_alarma"))
    assert _hasta(robot, lambda: g["llegado"], 60)
    robot.frames(3)
    dicho = _desde(robot, n)
    assert j.banda == 0 and any(f.replace("{nombre}", fichas[0]["n"]) in dicho for f in GO.AJ.lista("frases_no_delata"))
    assert j.estrellas == p.caja_de_local(far)["busqueda"] and j.stats.get("banda_delaciones", 0) == 0 and not j.antecedentes


def test_si_el_golpe_fracasa_pierden_confianza_y_el_reintento_lo_repite(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 2, lealtad=10)
    fichas[1]["lealtad"] = 4
    _armado(p)
    arm = _local(p, "armeria")
    _a(p, arm)
    j = p.j
    assert p.atracar_local(arm, _plan(fichas, conductor=0, caja=1, modelo="sedan"))
    v = p.golpe["veh"]
    assert v is not None
    n = len(robot.app.voz.registro)
    p.fallar_mision("Te han cogido.")
    assert p.golpe is None and v not in p.vehiculos and j.stats["golpes_fallidos"] == 1
    assert j.banda == 1 and [f["lealtad"] for f in p.banda_fichas()] == [4]             # uno se queda sin confianza y se va
    assert any(f.replace("{nombre}", fichas[1]["n"]) in _desde(robot, n) for f in GO.AJ.lista("frases_se_va"))
    # reintentar: vuelves a como estabas al empezar, con los dos, y el golpe se monta otra vez
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.titulo.startswith("Misión fallida")
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Reintentar desde el principio"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.golpe is not None and j.banda == 2 and [f["lealtad"] for f in p.banda_fichas()] == [10, 4]
    assert p.golpe["veh"] is not None and p.golpe["botin"] == p.mision["def"]["recompensa"]["dinero"]
    p.abandonar_mision()
    assert p.golpe is None


def test_de_pasajero_conduce_el_conductor_y_baja_un_nivel_si_ya_te_buscan(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 1, conduccion=100)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    j = p.j
    mio = p.crear_vehiculo("sedan", j.x + 8, j.y, 1, None, "Rayo")
    assert p.hacer_mio(mio, callar=True)
    mio.id_golpe = mio.id
    plan = _plan(fichas, huida="pasajero", conductor=0)
    plan["veh_id"] = mio.id
    n = len(robot.app.voz.registro)
    assert p.atracar_local(far, plan)
    g = p.golpe
    assert g["veh"] is mio and g["veh_tuyo"] and p.chofer and p.chofer["veh"] is mio and p.chofer["nombre"].startswith(fichas[0]["n"]) and "Irás de pasajero" in _desde(robot, n)
    _abrir_caja(robot, p)
    robot.frames(3)
    assert g["llegado"] and j.estrellas == 2                       # sin vigilante: ya te buscan
    monkeypatch.setattr(GO.random, "random", lambda: 0.0)
    j.x, j.y = mio.x + 2, mio.y
    robot.tecla(pygame.K_f)
    robot.frames(2)
    assert j.veh is mio and p.chofer_conduce() and j.estrellas == 1 and j.puntos_busqueda == UMBRAL[0]
    dicho = _desde(robot, n)
    assert "Nivel de búsqueda 1" in dicho and p.gps is not None and "pone rumbo a" in dicho
    # acabado el golpe, tu vehículo sigue siendo tuyo y el conductor sigue de chófer hasta que lo despidas
    _huir(robot, p)
    assert _hasta(robot, lambda: p.mision is None, 10)
    assert mio in p.vehiculos and p.es_mio(mio) and p.chofer is not None and p.despedir_chofer(callar=True) and j.veh is mio


# ====================================================================== 6. bancos y proveedores
def test_el_banco_y_el_proveedor_tambien_se_preparan(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot, adultos=True)
    fichas = _banda(p, 2)
    _armado(p)
    banco = _local(p, "banco")
    _a(p, banco)
    for e in sistemas.miembros_presentes(p):
        e.x, e.y = p.j.x + 2, p.j.y
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Preparar el golpe con tu banda"))
    robot.tecla(pygame.K_RETURN)
    pm = robot.app.pila[-1]
    assert pm.titulo.startswith("Preparar el golpe al banco")
    pm.i = next(i for i, o in enumerate(pm.opciones) if o.texto.startswith(fichas[0]["n"] + ":"))
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_DOWN)                                   # el segundo papel: vigilante
    robot.tecla(pygame.K_RETURN)
    pm.i = next(k for k, o in enumerate(pm.opciones) if o.texto.startswith("Empezar el golpe al banco"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.golpe is not None and p.mision["def"]["id"] == "atraco_banco", robot.dicho()
    assert p.mision["def"]["pasos"][1]["tarda"] == 26 and p.atracadas["banco:" + banco.id] == p.dia
    _matar_guardias(robot, p)
    _abrir_caja(robot, p, 60)
    assert p.golpe["alarma"] is not None and not p.golpe["llegado"]
    assert _hasta(robot, lambda: p.golpe["llegado"], 60)
    dinero, botin = p.j.dinero, p.golpe["botin"]
    _huir(robot, p)
    assert _hasta(robot, lambda: p.mision is None, 10)
    assert p.j.dinero == dinero + botin - int(botin * 0.08) and p.j.stats["atracos"] == 1
    # el proveedor: su menú también lo ofrece, y el asalto preparado no trae policía, como el de siempre
    prov = _local(p, "proveedor")
    _a(p, prov)
    sistemas.llamar(p)
    assert p.asaltar_proveedor(prov, _plan(p.banda_fichas(), escolta=0, caja=1))
    assert p.golpe is not None and [x["tipo"] for x in p.mision["def"]["pasos"]] == ["eliminar", "recoger"] and p.mision["def"]["pasos"][1]["tarda"] == 14
    _matar_guardias(robot, p)
    _abrir_caja(robot, p, 40)
    assert _hasta(robot, lambda: p.mision is None, 5)
    assert p.golpe is None and p.j.stats["asaltos_proveedor"] == 1 and p.j.estrellas == 0
    from juego import menus_adultos
    _a(p, prov)
    p.j.proveedores.clear()
    robot.tecla(pygame.K_RETURN)
    assert any(o.texto.startswith("Preparar el golpe con tu banda") for o in robot.app.pila[-1].opciones), robot.dicho()
    assert menus_adultos


# ====================================================================== 7. nada es obligatorio
def test_sin_banda_o_sin_preparar_el_atraco_es_el_de_siempre(robot, datos_de_serie):
    p = _empezar(robot)
    _armado(p)
    j = p.j
    far = _local(p, "farmacia")
    _a(p, far)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert not any("Preparar el golpe" in o.texto for o in m.opciones)          # sin banda ni se ofrece
    dinero = j.dinero
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Atracar este local"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and j.dinero > dinero and p.mision is None and p.golpe is None      # en el acto, como siempre
    # con banda, sin prepararlo: igual
    _banda(p, 2)
    p.limpiar_busqueda(hablar=False)
    tienda = _local(p, "tienda")
    _a(p, tienda)
    dinero = j.dinero
    assert p.atracar_local(tienda) and j.dinero > dinero and p.mision is None and p.golpe is None
    # y con guardia, sin prepararlo: la caja se coge al tocarla y la policía cae al momento
    p.limpiar_busqueda(hablar=False)
    arm = _local(p, "armeria")
    _a(p, arm)
    assert p.atracar_local(arm) and p.golpe is None
    assert "tarda" not in p.mision["def"]["pasos"][1]
    _matar_guardias(robot, p)
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    robot.tecla(pygame.K_RETURN)
    assert p.mision["recogido"] and p.mision.get("abriendo") is None
    robot.frames(3)
    assert p.mision["paso"] == 2 and j.estrellas == p.caja_de_local(arm)["busqueda"] and p.mision["policia_en"] is None
    # el banco sin preparar tampoco cambia
    p.abandonar_mision()
    p.limpiar_busqueda(hablar=False)
    banco = _local(p, "banco")
    _a(p, banco)
    p.empezar_atraco_banco(banco)
    assert p.golpe is None and "tarda" not in p.mision["def"]["pasos"][1] and "golpe" not in p.mision["def"]


def test_en_un_servidor_y_con_amigos_no_se_preparan_golpes_y_se_dice(robot, datos_de_serie):
    p = _empezar(robot)
    _banda(p, 2)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    p.en_servidor = True
    assert "En un servidor en línea los golpes no se preparan con la banda" in p.golpe_bloqueo()
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and any(o.texto.startswith("Atracar este local") for o in m.opciones) and not any("Preparar el golpe" in o.texto for o in m.opciones)
    n = len(robot.app.voz.registro)
    GO.preparar(p, far, lambda plan: False)
    assert robot.app.pila[-1] is m and "En un servidor en línea los golpes no se preparan" in _desde(robot, n)
    robot.tecla(pygame.K_ESCAPE)
    p.en_servidor = False
    assert p.golpe_bloqueo() == ""
    p.j.banda = 0
    assert "necesitas gente en tu banda" in p.golpe_bloqueo()


# ====================================================================== 8. los datos, el editor y la documentación
def test_los_papeles_los_numeros_y_las_frases_salen_de_los_datos(robot, datos_de_serie, monkeypatch):
    d = M.cargar_datos()
    assert [x["id"] for x in d["papeles_golpe"]] == ["conductor", "vigilante", "escolta", "caja", "tirador"] and d["golpes"][0]["id"] == "general"
    assert [x["id"] for x in GO.PAPELES] == [x["id"] for x in d["papeles_golpe"]]
    # lo de los datos es lo que hay escrito en el código, para que quitar la sección no cambie nada
    for x, serie in zip(d["papeles_golpe"], GO.PAPELES_SERIE):
        assert {k: x[k] for k in ("id", "nombre", "efecto", "atributo", "parte", "desc")} == serie
    g = d["golpes"][0]
    for k, v in GO.AJ._n.items():
        assert g[k] == v, k
    for k, v in GO.AJ._l.items():
        assert g[k] == v, k
    # un mod cambia un papel, añade otro y toca números y frases
    d2 = json.loads(json.dumps({k: d[k] for k in ("golpes", "papeles_golpe")}))
    d2["papeles_golpe"] = [dict(d2["papeles_golpe"][1], nombre="Aguador", parte=25), {"id": "segundo", "nombre": "Segundo tirador", "efecto": "tirador", "atributo": "punteria", "parte": 5, "desc": "Otro que dispara."},
                           {"id": "malo", "nombre": "No vale", "efecto": "volar"}]
    d2["golpes"][0].update(vigilante_retraso=100, reparto_tope=20, frases_salida=["Fuera todos."])
    GO.configurar(d2)
    GO.AJ.configurar(d2)
    assert [x["id"] for x in GO.PAPELES] == ["vigilante", "segundo"] and GO.papel("vigilante")["nombre"] == "Aguador"
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    fichas = _banda(p, 2)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    n = len(robot.app.voz.registro)
    assert p.atracar_local(far, _plan(fichas, vigilante=0, segundo=1))
    _abrir_caja(robot, p)
    g = p.golpe
    assert g["llegan"] - g["alarma"] == pytest.approx(100 * (0.5 + 0.75 * 0.6)) and "Fuera todos." in _desde(robot, n)
    # el reparto respeta el tope: 25 y 5 son 30, pero el tope es 20
    lista, neto = p.golpe_reparto(3000)
    assert [e for _, _, e in lista] == [500, 100] and neto == 2400 and lista[0][1] == "Aguador"
    p.abandonar_mision()
    # sin la sección, los de serie
    GO.configurar({})
    assert [x["id"] for x in GO.PAPELES] == ["conductor", "vigilante", "escolta", "caja", "tirador"]


def test_un_paso_de_cualquier_mision_puede_tardar_en_abrirse_y_retrasar_a_la_policia(robot, datos_de_serie):
    """Lo que usan los golpes vale para las misiones de los mods: «tarda» en un paso de recoger y «retraso» en uno de policía."""
    p = _empezar(robot)
    far = _local(p, "farmacia")
    _a(p, far)
    j = p.j
    p._empezar_repetible({"id": "prueba_caja", "titulo": "La caja fuerte", "lugar": far.id,
                          "pasos": [{"tipo": "recoger", "lugar": far.id, "objeto": "La caja fuerte", "texto": "Ábrela.", "tarda": 3},
                                    {"tipo": "policia", "nivel": 2, "texto": "Lárgate.", "retraso": 2}], "recompensa": {"dinero": 10}})
    assert "Tarda en abrirse" in p.objetivo_txt()
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_RETURN)
    assert not p.mision["recogido"] and "Empiezas a abrir: La caja fuerte. Tardará unos 3 segundos" in _desde(robot, n)
    robot.tecla(pygame.K_RETURN)                                 # otra vez Intro: dice cuánto falta, no la coge
    assert not p.mision["recogido"] and "Se está abriendo: faltan unos" in _desde(robot, n)
    robot.frames(60)
    assert p.mision["paso"] == 0 and "Va por la mitad" in _desde(robot, n)
    robot.frames(40)
    assert p.mision["paso"] == 1 and "Tienes: La caja fuerte" in _desde(robot, n)
    assert j.estrellas == 0 and p.mision["policia_en"] is not None and "La policía tardará unos 2 segundos en llegar" in _desde(robot, n)
    robot.frames(45)
    assert p.mision is not None and j.estrellas == 0
    robot.frames(30)
    assert j.estrellas == 2 and p.mision["policia_en"] is None
    # si fallas con la caja a medias, el sonido se calla
    p.abandonar_mision()
    p.limpiar_busqueda(hablar=False)
    p._empezar_repetible({"id": "prueba_caja", "titulo": "La caja fuerte", "lugar": far.id,
                          "pasos": [{"tipo": "recoger", "lugar": far.id, "objeto": "La caja fuerte", "texto": "Ábrela.", "tarda": 30}], "recompensa": {}})
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    robot.tecla(pygame.K_RETURN)
    robot.frames(5)
    canal = p.mision["abriendo"]["canal"]
    assert canal is not None
    paradas = []
    canal.parar = lambda: paradas.append(1)
    p.abandonar_mision()
    assert paradas and o not in p.objetos


def test_el_editor_cubre_los_golpes_y_la_documentacion_los_cuenta():
    from editor.esquema import ESQUEMAS, SECCIONES
    secciones = {clave: esq for clave, _, esq in SECCIONES}
    assert secciones["golpes"] == "ajuste_golpes" and secciones["papeles_golpe"] == "papel_golpe"
    claves = {cp["k"] for cp in ESQUEMAS["ajuste_golpes"]["campos"]}
    assert set(GO.AJ._n) | set(GO.AJ._l) <= claves
    assert {cp["k"] for cp in ESQUEMAS["papel_golpe"]["campos"]} == {"id", "nombre", "efecto", "atributo", "parte", "desc"}
    paso = {cp["k"] for cp in ESQUEMAS["paso"]["campos"]}
    assert {"tarda", "retraso"} <= paso
    docs = os.path.join(rutas.base(), "data", "docs")
    manual = open(os.path.join(docs, "manual.html"), encoding="utf-8").read()
    for trozo in ("Golpes preparados", "Preparar el golpe con tu banda", "conductor", "vigilante", "escolta", "el de la caja", "tirador", "Las cinco fases", "Entrada: cada uno va a su sitio",
                  "Tu gente, uno por uno"):
        assert trozo in manual, trozo
    editor = open(os.path.join(docs, "editor_mods.html"), encoding="utf-8").read()
    assert "Golpes preparados" in editor and "Papeles de un golpe" in editor
    novedades = open(os.path.join(docs, "novedades.html"), encoding="utf-8").read()
    assert "golpe" in novedades.lower() and "papel" in novedades.lower()


# ====================================================================== 9. con el mando
@pytest.mark.parametrize("tipo", ("xbox", "ps"))
def test_preparar_y_dar_un_golpe_solo_con_el_mando(robot, datos_de_serie, monkeypatch, tipo):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    md = Md(robot, tipo)
    fichas = _banda(p, 2)
    _armado(p)
    far = _local(p, "farmacia")
    _a(p, far)
    j = p.j
    for e in sistemas.miembros_presentes(p):
        e.x, e.y = j.x + 2, j.y
    md.pulsar("a")
    md.elegir("Preparar el golpe con tu banda")
    md.elegir(fichas[0]["n"] + ":", empieza=True)
    md.elegir("El de la caja", empieza=True)
    md.elegir(fichas[1]["n"] + ":", empieza=True)
    md.elegir("Vigilante", empieza=True)
    md.pulsar("y")                                               # Y o Triángulo: la ayuda de la opción
    md.elegir("Empezar el golpe")
    assert robot.app.pila[-1] is p and p.golpe is not None
    o = p.mision["objeto"]
    j.x, j.y = o.x, o.y
    md.pulsar("a")                                               # interactuar: empieza a abrir la caja
    assert p.mision["abriendo"] is not None
    assert _hasta(robot, lambda: p.mision["paso"] == 1, 30)
    md.pulsar("misc")                                            # el objetivo: en qué fase va
    assert "Golpe preparado, fase 4 de 5: salida" in robot.dicho()
    assert _hasta(robot, lambda: p.golpe["llegado"], 40)
    _huir(robot, p)
    assert _hasta(robot, lambda: p.mision is None, 10) and p.golpe is None
    # y Tu gente y la explicación, desde el móvil
    md.pulsar("back")
    md.elegir("Territorios")
    md.elegir("Tu banda")
    md.elegir("Tu gente, uno por uno")
    assert robot.app.pila[-1].opciones[0].texto.startswith(fichas[0]["n"] + ": puntería")
    md.pulsar("b")
    md.elegir("Cómo funcionan los golpes preparados")
    assert robot.app.pila[-1].titulo.startswith("Golpes preparados: cómo funciona")
    md.al_juego()


# ====================================================================== 10. partidas antiguas
def test_una_partida_anterior_carga_y_puede_preparar_golpes(robot, datos_de_serie, monkeypatch):
    _sin_azar(monkeypatch)
    p = _empezar(robot)
    j = p.j
    j.territorios = [b["id"] for b in p.mundo.barrios[:3]]
    j.banda, j.banda_nombre = 2, "Los Mirlos"
    d = json.loads(json.dumps(p.a_dict()))
    del d["jugador"]["banda_gente"]                              # como la guardó la 1.7.0
    from juego.partida import Partida
    q = Partida(robot.app, d)
    robot.app.partida = q
    robot.app.pila[-1:] = [q]
    assert q.j.banda == 2 and q.j.banda_gente == [] and q.golpe is None
    n, _ = sistemas.llamar(q)
    assert n == 2 and len(q.banda_fichas()) == 2
    _armado(q)
    far = _local(q, "farmacia")
    _a(q, far)
    assert q.atracar_local(far, _plan(q.banda_fichas(), caja=0))
    assert q.golpe is not None
    # un golpe en curso no se guarda: al cargar, la misión no está y el golpe tampoco
    d2 = json.loads(json.dumps(q.a_dict()))
    r = Partida(robot.app, d2)
    assert r.golpe is None and r.mision is None and len(r.j.banda_gente) == 2
    q.abandonar_mision()
    assert math.isfinite(q.j.dinero)
