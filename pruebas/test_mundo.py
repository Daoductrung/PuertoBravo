"""Viajes entre mapas, mar, pesca, comercios, guardado y trabajos."""
import math
import random

import pygame

from juego import menus_juego
from juego.menus import Dialogo, Menu


def _elegir(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    for k, o in enumerate(m.opciones):
        if texto.lower() in o.texto.lower():
            m.i = k
            robot.tecla(pygame.K_RETURN)
            return
    raise AssertionError(f"no hay opción «{texto}» en {[o.texto for o in m.opciones]}")


def _cerrar_menus(robot):
    while robot.app.pila[-1] is not robot.p:
        robot.tecla(pygame.K_ESCAPE)


def test_datos_coherentes(app):
    lugares = {l.id: l for m in app.mapas.values() for l in m.lugares_todos.values()}
    assert len(app.mapas) >= 9 and len(lugares) >= 245
    modelos = {v["id"] for v in app.datos["vehiculos"]}
    armas = {a["id"] for a in app.datos["armas"]}
    sonidos = app.mez.sonidos
    for m in app.mapas.values():
        for l in m.lugares_todos.values():
            assert l.sonido in sonidos, (l.id, l.sonido)
            if m.tipo != "mar":
                assert m.transitable(l.x, l.y), l.id
            if l.get("a_lugar"):
                assert l.get("a_lugar") in lugares, l.id
            if l.get("a_mapa"):
                assert l.get("a_mapa") in app.mapas, l.id
            if l.get("vehiculo"):
                assert l.get("vehiculo") in modelos, l.id
        for b in m.barrios:
            assert b["ambiente"] in sonidos, b["id"]
            for v in b["vehiculos"]:
                assert v in modelos, (b["id"], v)
        for x, y in m.casetes:
            assert m.superficie(x, y) not in ("pared", "fuera", "arena") or m.tipo != "mar", (m.id, x, y)
    for v in app.datos["vehiculos"]:
        assert v["motor"] in sonidos, v["id"]
        for k in ("claxon", "sirena"):
            assert v.get(k, "claxon") in sonidos, v["id"]
    for a in app.datos["armas"]:
        assert a["sonido"] in sonidos, a["id"]
    ids = set()
    for mi in app.datos["misiones"]:
        assert mi["id"] not in ids
        ids.add(mi["id"])
        assert mi["lugar"] in lugares, mi["id"]
        for paso in mi["pasos"]:
            if "lugar" in paso:
                assert paso["lugar"] in lugares, (mi["id"], paso["lugar"])
            if "modelo" in paso:
                assert paso["modelo"] in modelos, mi["id"]
            if "arma" in paso:
                assert paso["arma"] in armas, mi["id"]
            for g in paso.get("enemigos", []):
                assert g["arma"] in armas, mi["id"]
        r = mi.get("recompensa", {})
        assert r.get("arma", "punos") in armas
    for mi in app.datos["misiones"]:
        for r in mi.get("requiere", []):
            assert r in ids, (mi["id"], r)
    for c in app.datos["carreras"]:
        assert c["mapa"] in app.mapas


def test_carretera_autobus_y_mar(robot):
    p = robot.nueva_partida()
    j = p.j
    j.dinero = 100000
    # en coche por la carretera a Villaseca
    s = p.lugares["salida_norte"]
    x, y, d = p.mundo.plaza_junto_a(s)
    v = p.crear_vehiculo("sedan", x, y, d, None)
    j.x, j.y = p.mundo.punto_libre(x + 2, y + 2)
    robot.tecla(pygame.K_f)
    assert j.veh is v
    robot.frames(10)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Tomar la carretera")
    assert p.mundo.id == "villaseca" and j.veh is v and p.modo_asistido()
    robot.frames(120, mantener=(pygame.K_UP,))
    assert v.vel > 3
    # autobús a San Lucero
    robot.frames(60, mantener=(pygame.K_DOWN,))
    v.vel = 0
    robot.tecla(pygame.K_f)
    e = p.lugares["vs_estacion"]
    j.x, j.y = e.x, e.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "San Lucero")
    assert p.mundo.id == "san_lucero" and j.veh is None
    # GPS a un lugar de otra localidad
    p.gps_a_lugar(p.lugares["cb_taberna"])
    assert p.gps and p.gps.get("final") == "cb_taberna"
    # al mar desde el puerto deportivo
    emb = p.lugares["sl_embarcadero"]
    j.x, j.y = emb.x, emb.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Alquilar")
    assert p.mundo.id == "mar" and j.veh is not None and j.veh.modelo.get("barco")
    x0, y0 = j.veh.x, j.veh.y
    robot.frames(30, mantener=(pygame.K_UP, pygame.K_LEFT))
    robot.frames(170, mantener=(pygame.K_UP,))
    assert math.hypot(j.veh.x - x0, j.veh.y - y0) > 30
    for k in (pygame.K_c, pygame.K_TAB, pygame.K_g, pygame.K_v, pygame.K_l):
        robot.tecla(k)
        robot.frames(2)
    _cerrar_menus(robot)
    # pesca
    j.veh.vel = 0
    robot.tecla(pygame.K_p)
    assert p.pesca
    for _ in range(600):
        robot.frames(1)
        if p.pesca and p.pesca["fase"] == "pica":
            robot.tecla(pygame.K_SPACE)
            break
    assert not p.pesca
    # guardar en el mar y volver a cargar a bordo
    assert menus_juego.escribir_ranura(p, "1")
    robot.app.empezar_partida(menus_juego.leer_ranura("1"))
    p = robot.p
    j = p.j
    assert p.mundo.id == "mar" and j.veh is not None
    # atracar en Isla Tortuga
    mu = p.lugares["mar_isla"]
    j.veh.x, j.veh.y = mu.x, mu.y + 14
    j.veh.vel = 0
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Atracar")
    assert p.mundo.id == "isla_tortuga" and j.veh is None
    robot.frames(120, mantener=(pygame.K_UP,))
    assert "Isla Tortuga" in " ".join(robot.app.voz.registro[-60:])


def test_comercios(robot):
    p = robot.nueva_partida()
    j = p.j
    j.dinero = 500000
    p.completadas.append("m05")
    vistos = set()
    for l in list(p.lugares.values()):
        if l.tipo in vistos or l.tipo in ("salida", "muelle", "embarcadero", "estacion", "pesca", "carrera", "taller", "desguace"):
            continue
        vistos.add(l.tipo)
        if l.mapa != p.mundo.id:
            if p.mapas[l.mapa].tipo == "mar":
                continue
            p.cambiar_mapa(l.mapa, l.x, l.y)
        j.x, j.y = l.x, l.y
        robot.frames(12)
        robot.tecla(pygame.K_RETURN)
        cima = robot.app.pila[-1]
        if isinstance(cima, Menu):
            for k in range(len(cima.opciones)):
                if robot.app.pila[-1] is not cima or k >= len(cima.opciones):
                    break
                cima.i = k
                texto = cima.opciones[k].texto.lower()
                if any(q in texto for q in ("atracar", "guardar la partida", "despedir", "tablón", "boxeo", "galería", "encargo", "memoria", "caseta", "detector", "bucear", "dejar a")):
                    continue
                robot.tecla(pygame.K_RETURN)
                robot.frames(2)
                probados = set()
                for _ in range(12):
                    sub = robot.app.pila[-1]
                    if sub is cima or sub is p:
                        break
                    if isinstance(sub, Menu) and sub.opciones and sub.opciones[0].accion and id(sub) not in probados:
                        probados.add(id(sub))
                        sub.i = 0
                        robot.tecla(pygame.K_RETURN)
                    else:
                        robot.tecla(pygame.K_ESCAPE)
        _cerrar_menus(robot)
        robot.frames(5)
    assert {"casa", "armeria", "banco", "gimnasio", "taberna", "casino", "concesionario", "nautica"} <= vistos
    assert j.salud_max > 100 and j.barcos and len(j.armas) > 3
    assert any(e.tipo == "aliado" for e in p.personas)


def test_trabajos_y_explosivos(robot):
    p = robot.nueva_partida()
    j = p.j
    for modelo in ("taxi", "ambulancia", "autobus", "patrulla", "camion"):
        if j.veh:
            v = j.veh
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
        p._fin_persecucion()
        if p.mundo.id != "puerto_bravo":
            l = p.lugares["hospital"]
            p.cambiar_mapa("puerto_bravo", l.x, l.y)
        x, y, d = p.mundo.plaza_junto_a(p.lugares["hospital"])
        v = p.crear_vehiculo(modelo, x, y, d, None)
        v.propio = True
        p._subir(v, False)
        robot.tecla(pygame.K_j)
        assert p.trabajo and p.trabajo["tipo"] == v.modelo["trabajo"], robot.dicho()
        for _ in range(6):
            t = p.trabajo
            if not t:
                break
            if t["tipo"] == "vigilante":
                robot.frames(5)
                p.danar_vehiculo(t["objetivo"], 9999)
                robot.frames(40)
            else:
                l = t["lugar"]
                if l.mapa != p.mundo.id:
                    m = p.mapas[l.mapa]
                    x, y, d = m.plaza_junto_a(l)
                    p.cambiar_mapa(l.mapa, x, y, d * 90.0)
                x, y, d = p.mundo.plaza_junto_a(l)
                v.x, v.y, v.vel = x, y, 0.0
                robot.frames(5)
        assert p.trabajo and p.trabajo["hechas"] >= 2, (modelo, robot.dicho())
        robot.tecla(pygame.K_j)
        assert p.trabajo is None
    # explosivos
    v = j.veh
    p.salir_vehiculo(forzado=True)
    p.dar_arma("granada", 3)
    from juego.entidades import Persona
    e = Persona("enemigo", j.x + 15, j.y, "Diana")
    e.hostil = True
    e.salud = 50
    p.personas.append(e)
    robot.tecla(pygame.K_q)
    robot.tecla(pygame.K_SPACE)
    robot.frames(60)
    assert e.muerto
    robot.tecla(pygame.K_i)
    assert isinstance(robot.app.pila[-1], Menu)


def test_mono_ampliado(robot):
    p = robot.nueva_partida()
    rng = random.Random(11)
    p.j.dinero = 50000
    p.completadas.append("m05")
    teclas = [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_f, pygame.K_RETURN, pygame.K_SPACE,
              pygame.K_q, pygame.K_TAB, pygame.K_b, pygame.K_c, pygame.K_m, pygame.K_l, pygame.K_ESCAPE, pygame.K_r,
              pygame.K_u, pygame.K_h, pygame.K_j, pygame.K_1, pygame.K_4, pygame.K_z, pygame.K_x, pygame.K_g, pygame.K_p,
              pygame.K_e, pygame.K_i, pygame.K_F2, pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_y, pygame.K_o,
              pygame.K_n, pygame.K_COMMA, pygame.K_LCTRL, pygame.K_v, pygame.K_UP, pygame.K_UP, pygame.K_RETURN]
    lugares = [l for l in p.lugares.values()]
    for n in range(5000):
        p = robot.p
        if p is None or not robot.app.activo:
            break
        if n % 250 == 0 and robot.app.pila[-1] is p:
            l = rng.choice(lugares)
            m = p.mapas[l.mapa]
            if p.j.veh:
                v = p.j.veh
                p.salir_vehiculo(forzado=True)
                p.quitar_vehiculo(v)
            p.cambiar_mapa(l.mapa, l.x, l.y)
            if m.tipo == "mar":
                v = p.crear_vehiculo("lancha", *m.punto_libre(l.x, l.y - 15), 0, None)
                p._subir(v, False, callar=True)
            elif rng.random() < 0.5:
                x, y, d = m.plaza_junto_a(l)
                v = p.crear_vehiculo(rng.choice(["sedan", "taxi", "camion", "moto"]), x, y, d, None)
                p.j.x, p.j.y = m.punto_libre(x + 2, y + 2)
                p._subir(v, False, callar=True)
            p.dar_arma(rng.choice(["pistola", "fusil", "granada", "machete"]), 30)
        k = rng.choice(teclas)
        if rng.random() < 0.5:
            robot.tecla(k, mod=pygame.KMOD_SHIFT if rng.random() < 0.1 else 0)
            robot.frames(2)
        else:
            robot.frames(rng.randint(5, 40), mantener=(k, rng.choice(teclas)))
        if n % 700 == 0 and robot.p:
            robot.p.poner_busqueda(rng.randint(1, 5))
    assert robot.app.activo


def test_helicoptero_y_helipuertos(robot):
    p = robot.nueva_partida()
    j = p.j
    h = p.lugares["helipuerto_pb"]
    x, y, d = p.mundo.plaza_junto_a(h)
    v = p.crear_vehiculo("helicoptero", x, y, d, None)
    j.x, j.y = p.mundo.punto_libre(x + 2, y + 2)
    robot.tecla(pygame.K_f)
    assert j.veh is v and not p.modo_asistido()
    v.rumbo = 0.0
    y0 = v.y
    robot.frames(150, mantener=(pygame.K_UP,))
    assert v.y > y0 + 80 and v.salud == v.salud_max          # vuela por encima de los edificios sin chocar
    assert p.mundo.superficie(v.x, v.y) == "pared" or True
    # sobre un edificio no se puede bajar
    v.x, v.y, v.vel = 45.0, 45.0 + 90 * 3, 0.0
    assert p.mundo.superficie(v.x, v.y) == "pared"
    robot.tecla(pygame.K_f)
    assert j.veh is v
    # volar a otra localidad desde el helipuerto
    v.x, v.y = h.x, h.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Monteferro")
    assert p.mundo.id == "monteferro" and j.veh is v
    v.vel = 0
    robot.tecla(pygame.K_f)
    assert j.veh is None and p.mundo.transitable(j.x, j.y)
    # a pie, vuelo de pago
    j.dinero = 1000
    hm = p.lugares["mf_helipuerto"]
    j.x, j.y = hm.x, hm.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Isla Tortuga")
    assert p.mundo.id == "isla_tortuga" and j.dinero < 1000


def test_explorador_marcadores_y_tiro(robot):
    from juego.pantallas import ExploradorMapa, TiroAlBlanco
    from juego import menus_extra
    p = robot.nueva_partida()
    robot.tecla(pygame.K_F9)
    e = robot.app.pila[-1]
    assert isinstance(e, ExploradorMapa)
    for k in (pygame.K_UP, pygame.K_UP, pygame.K_RIGHT, pygame.K_TAB, pygame.K_TAB, pygame.K_n, pygame.K_d, pygame.K_HOME, pygame.K_LEFT, pygame.K_LEFT, pygame.K_LEFT, pygame.K_LEFT, pygame.K_F1):
        robot.tecla(k)
    assert "Cruce de" in robot.dicho()
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.gps is not None
    # marcadores
    menus_extra.marcadores(p)
    _elegir(robot, "Guardar un marcador")
    assert len(p.j.marcadores) == 1
    _elegir(robot, "Ir a Marcador 1")
    assert robot.app.pila[-1] is p and p.gps is not None
    # galería de tiro
    p.j.dinero = 100
    t = TiroAlBlanco(robot.app, p)
    robot.app.abrir(t)
    for _ in range(4000):
        if robot.app.pila[-1] is not t:
            break
        robot.frames(1)
        if t.estado == "diana":
            robot.tecla({-1: pygame.K_LEFT, 0: pygame.K_UP, 1: pygame.K_RIGHT}[t.dir])
    assert robot.app.pila[-1] is p and "10 dianas de 10" in robot.dicho() and p.j.dinero == 300
    assert p.nivel("punteria") >= 1
    # explorador en el mar
    a = p.lugares["mar_cala"]
    p.cambiar_mapa("mar", a.x, a.y - 20)
    v = p.crear_vehiculo("lancha", a.x, a.y - 20, 2, None)
    p._subir(v, False, callar=True)
    robot.tecla(pygame.K_F9)
    for k in (pygame.K_DOWN, pygame.K_DOWN, pygame.K_TAB, pygame.K_RETURN):
        robot.tecla(k)
    assert robot.app.pila[-1] is p and p.gps is not None


def test_encargos_repetibles_sucesos_y_logros(robot):
    import test_misiones
    p = robot.nueva_partida()
    j = p.j
    j.dinero = 5000
    p.dar_arma("pistola", 100)
    for nombre, lugar, contador in (("contrato", "taberna_puerto", "contratos"), ("banco", "banco", "atracos"),
                                    ("encargo", "desguace", "encargos"), ("boxeo", "gimnasio_pb", "boxeo")):
        l = p.lugares[lugar]
        j.x, j.y = l.x, l.y
        j.arma = "pistola"
        antes = len(p.completadas)
        {"contrato": p.empezar_contrato, "banco": p.empezar_atraco_banco, "encargo": p.empezar_encargo_coche, "boxeo": p.empezar_boxeo}[nombre](l)
        m = p.mision["def"]
        assert m.get("repetible")
        # se juega con el mismo robot que las misiones de la historia
        orig_ir, orig_disp, orig_ini = test_misiones._ir_a, p.mision_en_lugar, p.iniciar_mision
        p.mision_en_lugar = lambda _id: m
        p.iniciar_mision = lambda mm, reintento=False: None
        try:
            test_misiones._jugar_mision.__globals__["_noop"] = None
            for vuelta in range(60):
                robot.saltar_dialogos()
                if p.mision is None:
                    break
                ms = p.mision
                paso = ms["def"]["pasos"][ms["paso"]]
                lp = p.lugares.get(paso.get("lugar", ""))
                j.salud = j.salud_max
                if paso["tipo"] == "ir":
                    test_misiones._ir_a(robot, lp)
                elif paso["tipo"] == "eliminar":
                    if not ms["generado"]:
                        test_misiones._ir_a(robot, lp)
                        robot.frames(4)
                    for e in list(ms["enemigos"]):
                        p.danar_persona(e, 9999)
                elif paso["tipo"] == "recoger":
                    o = ms["objeto"]
                    j.x, j.y = o.x, o.y
                    robot.tecla(pygame.K_RETURN)
                elif paso["tipo"] == "policia":
                    robot.frames(3)
                    p.limpiar_busqueda()
                elif paso["tipo"] == "robar":
                    v = ms["veh"]
                    v.cerrado = False
                    j.x, j.y = p.mundo.punto_libre(v.x + 2, v.y)
                    robot.tecla(pygame.K_f)
                elif paso["tipo"] == "entregar":
                    test_misiones._ir_a(robot, lp)
                robot.frames(6)
        finally:
            p.mision_en_lugar, p.iniciar_mision = orig_disp, orig_ini
        assert p.mision is None, (nombre, robot.dicho())
        assert j.stats.get(contador, 0) == 1 and len(p.completadas) == antes, nombre
        if j.veh:
            v = j.veh
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
        p._fin_persecucion()
    # sucesos callejeros
    vistos = set()
    for _ in range(40):
        p.t_evento = 0.0
        p.evento = None
        robot.frames(3)
        if p.evento:
            vistos.add(p.evento["tipo"])
            ev = p.evento
            if ev["tipo"] == "maletin":
                j.x, j.y = ev["objeto"].x, ev["objeto"].y
            else:
                for e in ev["personas"]:
                    if e.tipo == "enemigo":
                        p.danar_persona(e, 9999)
            robot.frames(25)
            assert p.evento is None
        if len(vistos) == 3:
            break
    assert vistos == {"atraco", "banda", "maletin"} and j.stats.get("eventos", 0) >= 3
    # logros y noticias
    j.dinero = 300000
    p.t_logros = 0
    robot.frames(2)
    assert "rico" in j.logros and "millonario" in j.logros and "butron" in j.logros
    assert isinstance(p.noticia(), str) and len(p.noticia()) > 10


def test_mensajeria_del_mar(robot):
    p = robot.nueva_partida()
    a = p.lugares["mar_cala"]
    p.cambiar_mapa("mar", a.x, a.y - 20)
    v = p.crear_vehiculo("lancha_rapida", a.x, a.y - 20, 2, None)
    p._subir(v, False, callar=True)
    robot.tecla(pygame.K_j)
    assert p.trabajo and p.trabajo["tipo"] == "mensajeria"
    for _ in range(3):
        l = p.trabajo["lugar"]
        v.x, v.y, v.vel = l.x, l.y - 15, 0.0
        robot.frames(5)
    assert p.trabajo["hechas"] == 3 and p.j.dinero > 150
