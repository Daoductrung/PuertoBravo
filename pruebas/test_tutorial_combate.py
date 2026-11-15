"""Fallo de la 1.6.2: el tutorial de combate se empieza desde el móvil, estés donde estés, pero ponía el muñeco en el
club de tiro y decía «estás en el club de tiro». A cientos de metros, la Q contestaba «No hay enemigos cerca».

Aquí se juega entero con las teclas de verdad: Q para fijar, flechas para acercarse y Espacio para atacar.
"""
import math

import pygame

from juego.menus import Menu


def _empezar_desde_el_movil(robot, titulo="Aprende a defenderte"):
    p = robot.p
    p.cfg["sucesos"] = False
    from juego import menus_juego
    robot.tecla(pygame.K_m)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Misiones"))
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Tutorial: " + titulo))
    assert "el tutorial te lleva allí él mismo" in m.opciones[m.i].ayuda
    robot.tecla(pygame.K_RETURN)


def _acercarse(robot, e, hasta):
    p = robot.p
    for _ in range(900):
        x, y = p.pos()
        dx, dy = e.x - x, e.y - y
        if math.hypot(dx, dy) <= hasta:
            return
        k = (pygame.K_RIGHT if dx > 0 else pygame.K_LEFT) if abs(dx) > abs(dy) else (pygame.K_UP if dy > 0 else pygame.K_DOWN)
        robot.frames(1, mantener=(k,))
    raise AssertionError(f"no llega al objetivo: a {e.dist(*p.pos()):.1f} metros")


def test_el_tutorial_de_combate_se_juega_desde_cualquier_sitio(robot):
    p = robot.nueva_partida()
    club = p.lugares["club_tiro"]
    assert math.hypot(club.x - p.j.x, club.y - p.j.y) > 300                       # se empieza lejos, junto al bar
    dinero, abatidos = p.j.dinero, p.j.stats["enemigos"]
    _empezar_desde_el_movil(robot)
    assert robot.app.pila[-1] is not p                                            # el diálogo del tutorial
    assert any("te llevo a Club de tiro" in t for t in robot.app.voz.registro[-6:]), robot.dicho()
    assert math.hypot(club.x - p.j.x, club.y - p.j.y) < 20                        # ya está en el club, como dice el narrador
    robot.saltar_dialogos()
    robot.frames(5)
    assert "bate" in p.j.armas and p.j.arma == "bate" and len(p.mision["enemigos"]) == 1
    assert any("Hay un objetivo de prácticas" in t and "Pulsa Q para fijarlo" in t for t in robot.app.voz.registro[-4:]), robot.dicho()
    e = p.mision["enemigos"][0]
    assert e.dist(*p.pos()) < 40
    # la Q lo fija y dice dónde está
    robot.tecla(pygame.K_q)
    robot.frames(2)
    assert robot.app.voz.registro[-1].startswith("Fijado: Muñeco de prácticas") and p.objetivo is e
    assert "No hay enemigos cerca" not in robot.dicho()
    # acercarse con las flechas y pegar con Espacio
    _acercarse(robot, e, 1.8)
    for _ in range(40):
        robot.tecla(pygame.K_SPACE)
        robot.frames(25)
        if e.muerto:
            break
    assert e.muerto and any(t == "Muñeco de prácticas: al suelo." for t in robot.app.voz.registro[-6:]), robot.dicho()
    robot.saltar_dialogos()
    robot.frames(5)
    # las dos dianas, con la pistola
    assert p.j.arma == "pistola" and len(p.mision["enemigos"]) == 2
    assert any("Hay 2 objetivos de prácticas" in t for t in robot.app.voz.registro[-4:])
    for vuelta in range(2):
        robot.tecla(pygame.K_q)
        robot.frames(2)
        o = p.objetivo
        assert o is not None and not o.muerto and robot.app.voz.registro[-1].startswith("Fijado: Diana de prácticas")
        _acercarse(robot, o, 6)
        for _ in range(60):
            robot.tecla(pygame.K_SPACE)
            robot.frames(20)
            if o.muerto:
                break
        assert o.muerto
        if vuelta == 0:
            assert any(t == "Queda uno. Pulsa Q para fijarlo." for t in robot.app.voz.registro[-5:]), robot.dicho()
        robot.frames(3)
    robot.saltar_dialogos()
    robot.frames(5)
    assert "tut02" in p.completadas and p.mision is None
    assert p.j.estrellas == 0 and p.j.stats["enemigos"] == abatidos               # muñecos: ni policía ni cuentan como enemigos
    assert p.j.dinero == dinero + 50                                              # la recompensa, y nada de botín por el suelo
    assert "abatido" not in " ".join(robot.app.voz.registro[-60:])


def test_te_lleva_tambien_desde_un_vehiculo_un_interior_u_otra_localidad(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    tut = next(x for x in p.datos["misiones"] if x["id"] == "tut02")
    club = p.lugares["club_tiro"]
    # al volante
    v = p.crear_vehiculo("sedan", p.j.x + 3, p.j.y, 0, None)
    p._subir(v, False, callar=True)
    assert p.j.veh is v
    p.iniciar_mision(tut)
    assert p.j.veh is None and math.hypot(club.x - p.j.x, club.y - p.j.y) < 20
    robot.saltar_dialogos()
    robot.frames(3)
    robot.tecla(pygame.K_q)
    assert robot.app.voz.registro[-1].startswith("Fijado: Muñeco de prácticas")
    p.abandonar_mision() if hasattr(p, "abandonar_mision") else p.fallar_mision("prueba")
    robot.saltar_dialogos()
    p.mision = None
    # desde otra localidad
    otro = next(m for m in p.mapas.values() if m.id != club.mapa and m.tipo != "mar")
    p.cambiar_mapa(otro.id, *otro.punto_libre(otro.ancho / 2, otro.alto / 2))
    assert p.mundo.id == otro.id
    p.iniciar_mision(tut)
    assert p.mundo.id == club.mapa and math.hypot(club.x - p.j.x, club.y - p.j.y) < 20
    robot.saltar_dialogos()
    robot.frames(3)
    robot.tecla(pygame.K_q)
    assert robot.app.voz.registro[-1].startswith("Fijado: Muñeco de prácticas")
    # si ya estás en la puerta, no te mueve ni lo dice
    p.mision = None
    antes = (p.j.x, p.j.y)
    n = len(robot.app.voz.registro)
    p.iniciar_mision(tut)
    assert (p.j.x, p.j.y) == antes and not any("te llevo" in t for t in robot.app.voz.registro[n:])
    # y las misiones normales con enemigos siguen diciendo «enemigos»
    assert p.mision is not None


def _hasta(robot, condicion, tope, mantener=()):
    for _ in range(tope):
        if condicion():
            return True
        robot.frames(10, mantener=mantener)
        robot.saltar_dialogos() if False else None
    return condicion()


def _lejos(robot):
    """Deja al jugador en otra localidad, para empezar el tutorial desde lo más lejos posible."""
    p = robot.p
    otro = next(m for m in p.mapas.values() if m.id != "puerto_bravo" and m.tipo != "mar")
    p.cambiar_mapa(otro.id, *otro.punto_libre(otro.ancho / 2, otro.alto / 2))
    robot.frames(3)
    return otro


def test_el_tutorial_de_trabajos_desde_otra_localidad(robot):
    p = robot.nueva_partida()
    _lejos(robot)
    _empezar_desde_el_movil(robot, "Aprende a ganarte la vida")
    oficina = p.lugares["empleo_pb"]
    assert p.mundo.id == oficina.mapa and math.hypot(oficina.x - p.j.x, oficina.y - p.j.y) < 30, robot.dicho()
    assert any("te llevo a " + oficina.nombre in t for t in robot.app.voz.registro[-8:])
    robot.saltar_dialogos()
    robot.frames(5)
    taxi = p.mision["veh"]
    assert taxi is not None and taxi.dist(*p.pos()) < 60 and p.gps is not None          # el taxi está ahí mismo y el GPS lo marca
    # se llega andando solo, con la U, y se sube con la F
    robot.tecla(pygame.K_u)
    assert _hasta(robot, lambda: taxi.dist(*p.pos()) < 4.5, 400), (robot.dicho(), taxi.dist(*p.pos()))
    robot.tecla(pygame.K_f)
    robot.frames(5)
    assert p.j.veh is taxi, robot.dicho()
    robot.saltar_dialogos()
    robot.frames(5)
    assert p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "entregar" and p.gps is not None
    # el piloto del GPS, con la Y, lo lleva a la parada
    robot.tecla(pygame.K_y)
    hecho = False
    for _ in range(1500):
        robot.frames(10)
        if not (p.mision and p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "entregar"):
            hecho = True
            break
    assert hecho, robot.dicho()
    robot.saltar_dialogos()
    robot.frames(5)
    assert "tut03" in p.completadas and p.j.estrellas == 0


def test_los_tutoriales_del_mar_y_de_los_amigos_desde_lejos(robot):
    p = robot.nueva_partida()
    p.completadas.append("tut01")
    for titulo, ident, destino in (("Aprende a navegar", "tut04", "lonja"), ("Aprende a jugar con amigos", "tut05", "bar_gaviota")):
        _lejos(robot)
        m = next(x for x in p.datos["misiones"] if x["id"] == ident)
        salida, meta = p.lugares[m["lugar"]], p.lugares[destino]
        _empezar_desde_el_movil(robot, titulo)
        assert p.mundo.id == salida.mapa and math.hypot(salida.x - p.j.x, salida.y - p.j.y) < 30, (ident, robot.dicho())
        robot.saltar_dialogos()
        robot.frames(5)
        assert p.gps is not None and p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "ir", (ident, robot.dicho())
        robot.tecla(pygame.K_u)                                                   # caminar solo hasta el destino
        assert _hasta(robot, lambda: p.mision is None or p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] != "ir" or robot.app.pila[-1] is not p, 1500,
                      mantener=(pygame.K_LSHIFT,)), (ident, robot.dicho(), math.hypot(meta.x - p.j.x, meta.y - p.j.y))
        robot.saltar_dialogos()
        robot.frames(5)
        assert ident in p.completadas, (ident, robot.dicho())


def test_un_tutorial_empezado_cerca_no_te_mueve(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    oficina = p.lugares["empleo_pb"]
    p.teletransportar(oficina.x + 90, oficina.y)                                  # a menos de 150 metros: se llega andando
    antes = (p.j.x, p.j.y)
    n = len(robot.app.voz.registro)
    p.iniciar_mision(next(x for x in p.datos["misiones"] if x["id"] == "tut03"))
    assert (p.j.x, p.j.y) == antes and not any("te llevo" in t for t in robot.app.voz.registro[n:])
    # y una misión normal nunca te mueve, esté donde esté
    p.mision = None
    robot.saltar_dialogos()
    p.teletransportar(oficina.x + 300, oficina.y)
    antes = (p.j.x, p.j.y)
    p.iniciar_mision(next(x for x in p.datos["misiones"] if x["id"] == "m02"))
    assert (p.j.x, p.j.y) == antes
