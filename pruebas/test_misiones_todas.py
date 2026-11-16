"""La lógica de fallar y reintentar, probada en todas las misiones del juego, una por una.

Dos situaciones por misión:
- te detienen, o pierdes el conocimiento, en el primer tramo de acción: la misión se falla, se puede reintentar desde el
  principio, y al reintentar vuelve a ese tramo sin darse por hecha;
- te detienen cuando ya solo queda la escena final: la misión no se falla y se completa al leerla.
"""
import pygame

from juego.menus import Dialogo, Menu

HABLADOS = ("dialogo", "dar", "decision")


def _limpiar(robot, p):
    for _ in range(40):
        c = robot.app.pila[-1]
        if c is p:
            break
        if isinstance(c, Menu) and not c.escapable:
            c.i = len(c.opciones) - 1
            robot.tecla(pygame.K_RETURN)
        else:
            robot.app.cerrar(c)
    if p.mision:
        p._limpiar_mision()
    p.transicion = False
    p._fin_persecucion()
    p.j.salud = p.j.salud_max
    p.j.dinero = 5000


def _empezar(robot, p, m):
    l = p.lugares[m["lugar"]]
    if p.j.veh:
        v = p.j.veh
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.teletransportar(l.x, l.y)
    p.completadas = [x for x in p.completadas if x != m["id"]]
    p.iniciar_mision(m)


def _escenas(robot, p, parar_en_final=False):
    """Pasa escenas y decisiones. Con parar_en_final, se detiene en la escena tras la que ya no queda nada que hacer."""
    for _ in range(60):
        c = robot.app.pila[-1]
        ms = p.mision
        if ms and parar_en_final and isinstance(c, (Dialogo, Menu)) and c is not p:
            resto = ms["def"]["pasos"][ms["paso"]:]
            if all(q["tipo"] in HABLADOS or not p.cumple_decision(q) for q in resto) and any(
                    q["tipo"] not in HABLADOS for q in ms["def"]["pasos"][:ms["paso"]]):
                return True
        if isinstance(c, Dialogo):
            robot.tecla(pygame.K_ESCAPE)
        elif isinstance(c, Menu) and c is not p and "fallida" not in c.titulo:
            c.i = 0
            robot.tecla(pygame.K_RETURN)
        else:
            return False
    return False


def _tipo(p):
    ms = p.mision
    return ms["def"]["pasos"][ms["paso"]]["tipo"] if ms and 0 <= ms["paso"] < len(ms["def"]["pasos"]) else None


def test_fallar_y_reintentar_en_todas_las_misiones(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.cfg["adultos"] = True
    robot.app.aplicar_adultos()
    malas = []
    probadas = 0
    for m in list(p.datos["misiones"]):
        if m.get("lugar") not in p.lugares or m.get("tutorial"):
            continue
        if not any(q["tipo"] not in HABLADOS for q in m["pasos"]):
            continue                                             # solo escenas: no hay nada que fallar
        for modo in ("detener", "morir"):
            _limpiar(robot, p)
            _empezar(robot, p, m)
            _escenas(robot, p)
            robot.frames(4)
            if not p.mision:
                malas.append((m["id"], modo, "se acaba sola al empezar"))
                continue
            tipo0, paso0 = _tipo(p), p.mision["paso"]
            if l_mapa := p.lugares[m["lugar"]].mapa:
                pass
            p.j.estrellas = 3
            (p.detener(True) if modo == "detener" else p.morir())
            for _ in range(6):
                if isinstance(robot.app.pila[-1], Dialogo):
                    robot.tecla(pygame.K_ESCAPE)
            c = robot.app.pila[-1]
            if not (isinstance(c, Menu) and "fallida" in c.titulo) or p.mision is not None:
                malas.append((m["id"], modo, tipo0, "no sale el menú de misión fallida", getattr(c, "titulo", str(c))[:80]))
                continue
            c.i = next(k for k, o in enumerate(c.opciones) if o.texto.startswith("Reintentar desde el principio"))
            robot.tecla(pygame.K_RETURN)
            _escenas(robot, p)
            robot.frames(20)
            _escenas(robot, p)
            if m["id"] in p.completadas:
                malas.append((m["id"], modo, tipo0, "se da por completada al reintentar"))
            elif not p.mision or p.mision["paso"] != paso0:
                malas.append((m["id"], modo, tipo0, "al reintentar no vuelve al mismo tramo", _tipo(p)))
            probadas += 1
    _limpiar(robot, p)
    assert not malas, malas
    assert probadas > 120


def test_detenido_con_solo_la_escena_final_por_leer_en_todas_las_misiones(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.cfg["adultos"] = True
    robot.app.aplicar_adultos()
    malas = []
    probadas = 0
    for m in list(p.datos["misiones"]):
        if m.get("lugar") not in p.lugares or m.get("tutorial") or m.get("repetible"):
            continue
        pasos = m["pasos"]
        if pasos[-1]["tipo"] != "dialogo" or not any(q["tipo"] not in HABLADOS for q in pasos):
            continue
        _limpiar(robot, p)
        _empezar(robot, p, m)
        en_final = False
        for _ in range(40):                                      # se dan por hechos los tramos de acción, uno a uno
            if _escenas(robot, p, parar_en_final=True):
                en_final = True
                break
            if not p.mision:
                break
            ms = p.mision
            if ms.get("veh") is not None and _tipo(p) == "entregar":
                p.quitar_vehiculo(ms["veh"])
                ms["veh"] = None
                p.gps = None
                p.app.son("llegada")
                p._siguiente_paso()
            else:
                if _tipo(p) == "robar" and ms.get("veh") is not None:
                    p.quitar_vehiculo(ms["veh"])
                    ms["veh"] = None
                if ms.get("veh_objetivo") is not None:
                    p.quitar_vehiculo(ms["veh_objetivo"])
                    ms["veh_objetivo"] = None
                p._paso_hecho()
        if not en_final or not p.mision:
            malas.append((m["id"], "no se llega a la escena final", _tipo(p)))
            continue
        ms = p.mision
        p.j.estrellas = 3
        p.detener(True)
        robot.tecla(pygame.K_ESCAPE)                             # la escena del calabozo
        if p.mision is not ms or any(isinstance(c, Menu) and "fallida" in c.titulo for c in robot.app.pila):
            malas.append((m["id"], "se falla con todo hecho"))
            continue
        _escenas(robot, p)
        if m["id"] not in p.completadas or p.mision is not None:
            malas.append((m["id"], "no se completa tras la escena final"))
        probadas += 1
    _limpiar(robot, p)
    assert not malas, malas
    assert probadas > 60
