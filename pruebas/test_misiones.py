"""Juega todas las misiones del juego de principio a fin (con atajos) para validar datos y motor."""
import math

import pygame

from juego.menus import Dialogo, Menu


def _ir_a(robot, l):
    """Coloca al jugador junto a un lugar, cambiando de mapa (y de vehículo) si hace falta."""
    p = robot.p
    j = p.j
    destino = p.mapas[l.mapa]
    if destino.tipo == "mar":
        if p.mundo.id != "mar":
            if j.veh:
                v = j.veh
                p.salir_vehiculo(forzado=True)
                p.quitar_vehiculo(v)
            p.cambiar_mapa("mar", l.x, l.y - 30)
        if not j.veh:
            v = p.crear_vehiculo("lancha", l.x, l.y - 30, 0, None)
            p._subir(v, False, callar=True)
        j.veh.x, j.veh.y = destino.punto_libre(l.x, l.y - 12)
        j.veh.vel = 0
        return
    if p.mundo.id != l.mapa:
        if j.veh and (p.mundo.tipo == "mar" or j.veh.modelo.get("barco")):
            v = j.veh
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
        if j.veh:
            x, y, d = destino.plaza_junto_a(l)
            p.cambiar_mapa(l.mapa, x, y, d * 90.0)
        else:
            p.cambiar_mapa(l.mapa, l.x, l.y)
    if j.veh and j.veh.modelo.get("vuela"):
        j.veh.x, j.veh.y, j.veh.vel = l.x, l.y, 0.0
    elif j.veh:
        x, y, d = p.mundo.plaza_junto_a(l)
        j.veh.x, j.veh.y, j.veh.vel = x, y, 0.0
    else:
        j.x, j.y = l.x, l.y


def _jugar_mision(robot, m):
    p = robot.p
    j = p.j
    j.salud = j.salud_max
    if j.veh:
        v = j.veh
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
    _ir_a(robot, p.lugares[m["lugar"]])
    robot.frames(15)
    assert p.mision_en_lugar(m["lugar"]) is not None or m.get("tutorial"), f"{m['id']}: no disponible"      # los tutoriales se empiezan desde el móvil
    p.iniciar_mision(m)
    for vuelta in range(400):
        robot.saltar_dialogos()
        if p.mision is None:
            break
        assert p.mision["def"]["id"] == m["id"]
        ms = p.mision
        paso = ms["def"]["pasos"][ms["paso"]]
        tipo = paso["tipo"]
        l = p.lugares.get(paso.get("lugar", ""))
        j.salud = j.salud_max
        if tipo == "ir":
            _ir_a(robot, l)
        elif tipo == "robar":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(3)
            v = ms["veh"]
            assert v is not None, f"{m['id']}: no se creó el vehículo"
            v.cerrado = False
            j.x, j.y = p.mundo.punto_libre(v.x + 2, v.y)
            robot.tecla(pygame.K_f)
            assert j.veh is v, f"{m['id']}: no pudo subir. {robot.dicho()}"
        elif tipo == "entregar":
            assert j.veh is ms["veh"]
            _ir_a(robot, l)
        elif tipo == "eliminar":
            if not ms["generado"]:
                _ir_a(robot, l)
                robot.frames(4)
            assert ms["generado"], f"{m['id']}: no aparecen enemigos. {robot.dicho()}"
            for e in list(ms["enemigos"]):
                p.danar_persona(e, 9999)
        elif tipo == "recoger":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(3)
            o = ms["objeto"]
            assert o is not None, f"{m['id']}: no hay objeto"
            if j.veh and p.mundo.tipo != "mar":
                v = j.veh
                p.salir_vehiculo(forzado=True)
            if j.veh:
                j.veh.x, j.veh.y = o.x, o.y
            else:
                j.x, j.y = o.x, o.y
            robot.tecla(pygame.K_RETURN)
        elif tipo == "seguir":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(3)
            o = ms["movil"]
            o["espera"], o["i"] = 0, len(o["ruta"])                  # el seguido llega a su destino...
            o["x"], o["y"] = o["ruta"][-1]
            p.teletransportar(*p.mundo.punto_libre(o["x"] + 14, o["y"]))    # ...y tú detrás, a buena distancia
        elif tipo == "escoltar":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(3)
            e = ms["escolta"]
            j.x, j.y = e["x"], e["y"]
            robot.frames(3)
            assert e["contigo"], f"{m['id']}: no se une. {robot.dicho()}"
            _ir_a(robot, p.lugares[paso["destino"]])
            e["x"], e["y"] = p.pos()
        elif tipo == "sigilo":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(2)
            for g in ms["guardias"]:
                g["x0"] += 60                                          # los vigilantes, lejos
            if j.veh:
                p.salir_vehiculo(forzado=True)
            j.agachado = True
            j.x, j.y = l.x, l.y
        elif tipo == "ruta":
            for ident in paso["puntos"][ms.get("ruta_i", 0):]:
                _ir_a(robot, p.lugares[ident])
                if j.veh:
                    j.veh.vel = 0
                robot.frames(4)
        elif tipo == "vigilar":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(2)
            if j.veh:
                p.salir_vehiculo(forzado=True)
            j.x, j.y = p.mundo.punto_libre(l.x + 8, l.y)
            robot.frames(3)
            assert ms["vigia"]["dentro"], f"{m['id']}: no entra en el puesto"
            ms["vigia"]["t"] = float(paso.get("segundos", 45)) - 0.2        # el tiempo de espera, de golpe
        elif tipo == "carrera":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(2)
            if not j.veh:
                v = p.crear_vehiculo("deportivo", j.x, j.y, 0, None)
                p._subir(v, False, callar=True)
            j.veh.x, j.veh.y = p.mundo.punto_libre(l.x + 5, l.y)
            j.veh.vel = 0
            robot.frames(30 * 4)
            assert ms["carrera"]["fase"] == "corre", f"{m['id']}: la carrera no arranca"
            for ident in paso["puntos"]:
                q = p.lugares[ident]
                j.veh.x, j.veh.y = p.mundo.punto_libre(q.x + 5, q.y)
                j.veh.vel = 0
                robot.frames(3)
        elif tipo == "policia":
            robot.frames(3)
            assert j.estrellas >= 1
            p.limpiar_busqueda()
        elif tipo == "perseguir":
            if ms.get("pendiente"):
                _ir_a(robot, l)
                robot.frames(3)
            vo = ms.get("veh_objetivo")
            assert vo is not None, f"{m['id']}: no hay vehículo objetivo"
            robot.frames(10)
            p.danar_vehiculo(vo, 99999)
            robot.frames(30)
        robot.frames(6)
    assert p.mision is None, f"{m['id']} atascada en el paso {p.mision['paso']}: {robot.dicho()}"
    assert m["id"] in p.completadas, f"{m['id']} no se completó: {robot.dicho()}"


def test_todas_las_misiones(robot):
    p = robot.nueva_partida()
    total = sum(1 for m in p.datos["misiones"] if not m.get("adultos"))
    assert total >= 50 and not p.modo_adulto()
    for _ in range(total + 2):
        disp = p.misiones_disponibles()
        if not disp:
            break
        _jugar_mision(robot, disp[0])
        assert robot.app.pila[-1] is p or isinstance(robot.app.pila[-1], (Dialogo, Menu))
        robot.saltar_dialogos()
    # Una partida solo recorre una rama de cada decisión: las misiones de las otras ramas no le salen nunca.
    otras_ramas = [m["id"] for m in p.datos["misiones"] if m.get("si_clave") and not p.cumple_decision(m)]
    faltan = [m["id"] for m in p.datos["misiones"] if m["id"] not in p.completadas and not m.get("adultos") and m["id"] not in otras_ramas]
    assert not faltan, f"faltan: {faltan}"
    assert len(p.completadas) == total - len(otras_ramas) and len(otras_ramas) == 6
    assert set(p.decisiones) >= {"concejal", "cooperativa", "trono", "oc_nombre", "_final"}          # ha pasado por las cuatro encrucijadas
    assert p.j.dinero > 100000
    assert any(b["modelo"] == "lancha_rapida" for b in p.j.barcos)


def test_fallo_y_reintento(robot):
    p = robot.nueva_partida()
    m = p.misiones_disponibles()[0]
    _ir_a(robot, p.lugares[m["lugar"]])
    p.iniciar_mision(m)
    robot.saltar_dialogos()
    assert p.mision is not None
    p.danar_jugador(9999, None)
    assert isinstance(robot.app.pila[-1], Dialogo)
    robot.tecla(pygame.K_RETURN)
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu) and "fallida" in menu.titulo
    menu.i = 0
    robot.tecla(pygame.K_RETURN)
    robot.saltar_dialogos()
    assert p.mision is not None and p.mision["def"]["id"] == m["id"]
    assert p.j.salud == p.j.salud_max
