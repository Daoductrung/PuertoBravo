"""Partida a ocho: ocho juegos completos a la vez, uno de ellos abre la partida y hace de servidor.

Todos juegan: se ven, hablan, se pasan dinero, compiten en una carrera de ocho, hacen un reparto entre todos y,
sin dejar de estar conectados, cada uno hace su día de trabajo, come y cumple una misión de su propia historia.
Un noveno no cabe; uno se va, a otro lo expulsan y, al final, el anfitrión cierra.
"""
import time

import pygame
import pytest

from conftest import Robot
from juego import red
from juego.menus import Menu
from test_ronda import _coherente

N = 8


@pytest.fixture
def ocho(app):
    from juego.app import App
    apps = [app] + [App(pruebas=True) for _ in range(N - 1)]
    yield [Robot(x) for x in apps]
    for x in apps:
        if x.partida is not None:
            x.partida.desconectar_online()
    for x in apps[1:]:
        x.radio.cancelar()
        x.ambiente.cancelar()
        x.mez.cerrar()


def _todos(robots, n=2):
    for _ in range(n):
        for r in robots:
            r.frames(1)


def _hasta(cond, robots, segundos=10.0):
    fin = time.time() + segundos
    while time.time() < fin:
        _todos(robots, 2)
        if cond():
            return True
        time.sleep(0.01)
    return False


def _al_juego(robot):
    for _ in range(30):
        if robot.app.pila[-1] is robot.p:
            return
        robot.saltar_dialogos()
        if robot.app.pila[-1] is not robot.p:
            robot.tecla(pygame.K_ESCAPE)


def test_partida_a_ocho_con_un_servidor(ocho):
    import test_misiones
    from test_vida import _elegir
    robots = ocho
    personajes = ["Dani", "Álex", "Sam", "Cris"]
    ps = []
    for k, r in enumerate(robots):
        r.app.cfg["red_nombre"] = f"Jugador{k + 1}"
        ps.append(r.nueva_partida(personajes[k % 4]))
    assert len({p.j.semilla for p in ps}) == N                     # ocho partidas, ocho ciudades distintas
    anfitrion = ps[0]
    ok, texto = anfitrion.abrir_a_amigos(0, "")
    assert ok and "sin contraseña" in texto
    puerto = anfitrion.servidor.puerto
    for p in ps[1:]:
        ok, texto = p.unirse_a_amigo(f"puertobravo://127.0.0.1:{puerto}")
        assert ok, texto
        _todos(robots, 1)
    assert _hasta(lambda: all(len(p.remotos) == N - 1 for p in ps), robots), [len(p.remotos) for p in ps]
    for p in ps:
        assert sorted(x.nombre for x in p.remotos.values()) == sorted(f"Jugador{k + 1}" for k in range(N) if ps[k] is not p)
    assert len(anfitrion.servidor.lista()) == N

    # un noveno no cabe
    extra = red.Cliente()
    ok, motivo = extra.conectar("127.0.0.1", puerto, "Noveno", "", intentos=1)
    assert not ok and motivo, motivo
    extra.cerrar()

    # --------------------------------------------------------- todos se ven
    base = anfitrion.lugares["plaza_mayor"]
    for k, p in enumerate(ps):
        p.j.x, p.j.y = p.mundo.punto_libre(base.x + 6 * k, base.y)
    assert _hasta(lambda: all(x.visto and x.mapa == "puerto_bravo" for p in ps for x in p.remotos.values()), robots)

    def como_ve(p, k):
        return next(x for x in p.remotos.values() if x.nombre == f"Jugador{k + 1}")
    assert _hasta(lambda: all(abs(como_ve(ps[0], k).tx - ps[k].j.x) < 1 for k in range(1, N)), robots)
    assert "Jugador8" in ps[3].donde_esta(como_ve(ps[3], 7))

    # ----------------------------------------------- un mensaje llega a los siete
    ps[5].enviar_chat("¿Estamos todos?")
    assert _hasta(lambda: all(any("¿Estamos todos?" in t for t in p.chat) for p in ps), robots)
    assert all("Jugador6 dice: ¿Estamos todos?" in r.dicho() for k, r in enumerate(robots) if k != 5)

    # ------------------------------------------- el dinero solo le llega a quien va
    for p in ps:
        p.j.dinero = 1000
    assert ps[2].dar_dinero_a(como_ve(ps[2], 6), 300)
    assert _hasta(lambda: ps[6].j.dinero == 1300, robots)
    _todos(robots, 4)
    assert [p.j.dinero for p in ps] == [1000, 1000, 700, 1000, 1000, 1000, 1300, 1000]

    # --------------------------------------------------- carrera de ocho
    for p in ps:
        p.j.dinero = 1000
    meta = anfitrion.lugares["hospital"]
    for k, p in enumerate(ps):
        p.j.x, p.j.y = p.mundo.punto_libre(meta.x + 150 + 4 * k, meta.y)
    _todos(robots, 4)
    ok, texto = ps[4].proponer_carrera(ps[4].lugares["hospital"], 100)          # la propone un invitado, no el anfitrión
    assert ok, texto
    assert _hasta(lambda: all(p.coop is not None for p in ps), robots)
    for k, p in enumerate(ps):
        if k != 4:
            assert p.aceptar_coop()[0]
    assert _hasta(lambda: len(ps[4].coop["participantes"]) == N, robots)
    assert ps[4].empezar_coop()[0]
    assert _hasta(lambda: all(p.coop and p.coop["estado"] == "marcha" for p in ps), robots)
    assert all(p.j.dinero == 900 for p in ps)
    ps[7].j.x, ps[7].j.y = ps[7].mundo.punto_libre(meta.x, meta.y)
    assert _hasta(lambda: all(p.coop is None for p in ps), robots)
    assert [p.j.dinero for p in ps] == [900] * 7 + [1700]
    assert "Has ganado la carrera" in robots[7].dicho() and all("Jugador8 ha llegado primero" in r.dicho() for r in robots[:7])

    # --------------------------------------------- reparto entre los ocho
    ok, texto = anfitrion.proponer_reparto()
    assert ok, texto
    assert _hasta(lambda: all(p.coop is not None for p in ps), robots)
    for p in ps[1:]:
        assert p.aceptar_coop()[0]
    assert _hasta(lambda: len(anfitrion.coop["participantes"]) == N, robots)
    assert anfitrion.empezar_coop()[0]
    assert _hasta(lambda: all(p.coop and p.coop["estado"] == "marcha" for p in ps), robots)
    antes = [p.j.dinero for p in ps]
    for k in (1, 3, 5, 7):                                           # cuatro entregas, cada una la hace uno distinto
        p = ps[k]
        assert p.coop is not None and p.coop["restantes"]
        quedan = len(p.coop["restantes"])
        l = p.lugares[p.coop["restantes"][0]]
        p.j.x, p.j.y = p.mundo.punto_libre(l.x, l.y)
        assert _hasta(lambda: all(q.coop is None or len(q.coop["restantes"]) < quedan for q in ps), robots)
    assert _hasta(lambda: all(p.coop is None for p in ps), robots)
    assert [p.j.dinero - a for p, a in zip(ps, antes)] == [650] * N    # cobran todos, también los que no entregaron
    assert all("Reparto completado entre todos" in r.dicho() for r in robots)

    # ----------------------- cada uno hace su día: trabajo, comida y una misión propia
    for k, r in enumerate(robots):
        p = r.p
        j = p.j
        quien = f"Jugador{k + 1}"
        of = p.lugares["empleo_pb"]
        j.x, j.y = of.x, of.y
        r.frames(8)
        dinero = j.dinero
        r.tecla(pygame.K_RETURN)
        if isinstance(r.app.pila[-1], Menu):
            _elegir(r, "Jornada de")
            _al_juego(r)
        assert j.dinero > dinero, quien
        sitio = next(l for l in p.mundo.lugares.values() if l.tipo == "comida")
        j.salud = 40.0
        j.x, j.y = sitio.x, sitio.y
        r.frames(8)
        r.tecla(pygame.K_RETURN)
        if isinstance(r.app.pila[-1], Menu):
            r.tecla(pygame.K_RETURN)
            assert j.salud > 40.0, quien
            _al_juego(r)
        disp = p.misiones_disponibles()
        assert disp, quien
        test_misiones._jugar_mision(r, disp[0])
        r.saltar_dialogos()
        assert len(p.completadas) == 1, f"{quien}: la misión no se completó jugando a ocho"
        dia = p.dia
        p.pasar_horas((24 * 60 - p.reloj) / 60 + 8)
        r.frames(4)
        r.saltar_dialogos()
        assert p.dia == dia + 1
        _coherente(p, quien)
        _todos(robots, 2)
        assert all(q.online_activo() for q in ps), f"alguien ha perdido la conexión mientras jugaba {quien}"
    assert _hasta(lambda: all(len(p.remotos) == N - 1 for p in ps), robots)

    # ------------------------------------------ uno se va, a otro lo expulsan
    ps[3].desconectar_online()
    resto = [p for k, p in enumerate(ps) if k != 3]
    assert _hasta(lambda: all(len(p.remotos) == N - 2 for p in resto), robots)
    assert "Jugador4 se ha ido" in robots[0].dicho()
    ident = como_ve(anfitrion, 6).id
    assert anfitrion.servidor.expulsar(ident)
    assert _hasta(lambda: not ps[6].online_activo(), robots) and "te ha sacado de la partida" in robots[6].dicho()
    quedan = [p for k, p in enumerate(ps) if k not in (3, 6)]
    assert _hasta(lambda: all(len(p.remotos) == N - 3 for p in quedan), robots)
    # ahora hay sitio: el que se fue vuelve a entrar
    ok, texto = ps[3].unirse_a_amigo(f"puertobravo://127.0.0.1:{puerto}")
    assert ok, texto
    assert _hasta(lambda: len(anfitrion.remotos) == N - 2, robots)

    # ------------------------------------------------- el anfitrión cierra
    anfitrion.desconectar_online()
    assert _hasta(lambda: not any(p.online_activo() for p in ps), robots)
    for k, r in enumerate(robots):
        r.frames(10)                                                 # y todos siguen jugando solos
        _coherente(r.p, f"Jugador{k + 1}, al final")
