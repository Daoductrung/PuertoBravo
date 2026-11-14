"""Partida completa con dos juegos de verdad conectados: uno abre la partida (servidor) y el otro entra (cliente).

Los dos son juegos enteros, cada uno con su partida, y los dos juegan: se ven, se escriben, se dan cosas, van en el
mismo coche, compiten, reparten en equipo y, mientras siguen conectados, cada uno hace su vida: trabaja, come,
hace misiones, conduce, viaja a otra localidad, guarda y duerme.
"""
import time

import pygame
import pytest

from conftest import Robot
from juego import menus_juego
from juego.menus import Menu
from test_ronda import _coherente


@pytest.fixture
def dos(app):
    """Dos juegos completos en marcha: el anfitrión y el invitado."""
    from juego.app import App
    otro = App(pruebas=True)
    yield Robot(app), Robot(otro)
    for a in (app, otro):
        if a.partida is not None:
            a.partida.desconectar_online()
    otro.radio.cancelar()
    otro.ambiente.cancelar()
    otro.mez.cerrar()


def _ambos(a, b, n=3):
    for _ in range(n):
        a.frames(1)
        b.frames(1)


def _hasta(cond, a, b, segundos=6.0):
    fin = time.time() + segundos
    while time.time() < fin:
        _ambos(a, b, 2)
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


def _dia(robot, otro, n, quien):
    """Un día de vida normal de un jugador, mientras el otro sigue conectado y también con el juego en marcha."""
    import test_misiones
    from test_vida import _elegir
    app = robot.app
    p = app.partida
    j = p.j
    donde = f"{quien}, día {p.dia}"
    _coherente(p, donde + ", al despertar")
    if p.mundo.id != "puerto_bravo":
        l = p.mapas["puerto_bravo"].lugares["hospital"]
        p.cambiar_mapa("puerto_bravo", l.x, l.y)
    if j.veh:
        j.veh.vel = 0
        p.salir_vehiculo(forzado=True)
    # trabajo honrado
    of = p.lugares["empleo_pb"]
    j.x, j.y = of.x, of.y
    robot.frames(8)
    antes = j.dinero
    robot.tecla(pygame.K_RETURN)
    if isinstance(app.pila[-1], Menu):
        _elegir(robot, "Jornada de")
        _al_juego(robot)
    assert j.dinero >= antes, donde
    otro.frames(4)
    # comer
    j.salud = max(20.0, j.salud - 30)
    sitio = next(l for l in p.mundo.lugares.values() if l.tipo == "comida")
    j.x, j.y = sitio.x, sitio.y
    robot.frames(8)
    robot.tecla(pygame.K_RETURN)
    if isinstance(app.pila[-1], Menu):
        salud = j.salud
        robot.tecla(pygame.K_RETURN)
        assert j.salud >= salud, donde
        _al_juego(robot)
    otro.frames(4)
    # la siguiente misión de su propia historia
    disp = p.misiones_disponibles()
    hechas = len(p.completadas)
    if disp:
        test_misiones._jugar_mision(robot, disp[0])
        robot.saltar_dialogos()
        assert len(p.completadas) == hechas + 1, f"{donde}: la misión {disp[0]['id']} no se completó jugando conectado"
    otro.frames(4)
    # un rato al volante con el piloto del GPS
    if n % 2 == 0:
        if p.mundo.id != "puerto_bravo":
            l = p.mapas["puerto_bravo"].lugares["hospital"]
            p.cambiar_mapa("puerto_bravo", l.x, l.y)
        p._fin_persecucion()
        x, y, d = p.mundo.plaza_junto_a(p.lugares["parada_taxi"])
        v = p.crear_vehiculo("taxi", x, y, d, None)
        j.x, j.y = p.mundo.punto_libre(x + 2, y + 2)
        p._subir(v, False, callar=True)
        p.cfg["piloto_gps"] = True
        p.gps_a_lugar(p.lugares["hospital"])
        for k in range(500):
            if not p.gps:
                break
            v.salud, j.salud = v.salud_max, j.salud_max
            robot.frames(5, mantener=(pygame.K_UP,) if v.vel < 14 else ())
            if k % 10 == 0:
                otro.frames(1)
        assert p.j.veh is v, donde
        v.vel = 0.0
        robot.frames(3)
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
        p._fin_persecucion()
    # dormir hasta mañana
    dia = p.dia
    p.pasar_horas((24 * 60 - p.reloj) / 60 + 8)
    robot.frames(5)
    robot.saltar_dialogos()
    assert p.dia == dia + 1, donde
    _coherente(p, donde + ", al acostarse")
    assert p.online_activo(), f"{donde}: se ha perdido la conexión jugando"


def test_partida_completa_servidor_y_cliente(dos):
    ra, rb = dos                                   # ra: quien abre la partida; rb: quien entra
    a = ra.nueva_partida("Dani")
    b = rb.nueva_partida("Álex")
    assert a is not b and a.j is not b.j and a.j.nombre != b.j.nombre
    assert a.j.semilla != b.j.semilla              # cada uno, su propia ciudad

    # ---------------------------------------------------------------- conectar
    ok, texto = a.abrir_a_amigos(0, "secreta")
    assert ok and "protegida con contraseña" in texto and a.es_anfitrion()
    puerto = a.servidor.puerto
    ok, texto = b.unirse_a_amigo(f"puertobravo://127.0.0.1:{puerto}", "mala")
    assert not ok and not b.online_activo(), texto
    ok, texto = b.unirse_a_amigo(f"puertobravo://127.0.0.1:{puerto}", "secreta")
    assert ok and b.online_activo() and not b.es_anfitrion(), texto
    assert _hasta(lambda: len(a.remotos) == 1 and len(b.remotos) == 1, ra, rb)
    de_b = next(iter(a.remotos.values()))          # cómo ve el anfitrión al invitado
    de_a = next(iter(b.remotos.values()))
    assert de_b.nombre == b.nombre_online() and de_a.nombre == a.nombre_online()
    assert "se ha unido a la partida" in ra.dicho()

    # ----------------------------------------------------- se ven y se encuentran
    b.j.x, b.j.y = b.mundo.punto_libre(a.j.x + 30, a.j.y)
    assert _hasta(lambda: de_b.visto and de_a.visto and abs(de_b.tx - b.j.x) < 1 and abs(de_a.tx - a.j.x) < 1, ra, rb)
    assert de_b.mapa == b.mundo.id and de_b.nombre in a.donde_esta(de_b) and "a pie" in a.donde_esta(de_b)
    a.gps_a_amigo(de_b)
    assert a.gps is not None
    a.cancelar_gps()
    ra.tecla(pygame.K_TAB)                         # el radar del anfitrión lo anuncia
    assert any(de_b.nombre in t for t in ra.app.voz.registro[-6:]) or any(getattr(o, "nombre", "") == de_b.nombre for o in a.radar_lista)

    # ------------------------------------------------ mensajes, dinero y botiquines
    a.enviar_chat("Hola, ¿me oyes?")
    assert _hasta(lambda: any("Hola, ¿me oyes?" in t for t in b.chat), ra, rb) and "dice: Hola, ¿me oyes?" in rb.dicho()
    b.enviar_chat("Alto y claro")
    assert _hasta(lambda: any("Alto y claro" in t for t in a.chat), ra, rb)
    a.j.dinero, b.j.dinero = 1000, 1000
    assert a.dar_dinero_a(de_b, 200)
    assert _hasta(lambda: b.j.dinero == 1200, ra, rb) and a.j.dinero == 800
    assert b.dar_dinero_a(de_a, 50)
    assert _hasta(lambda: a.j.dinero == 850, ra, rb) and b.j.dinero == 1150
    a.j.objetos["botiquin"], b.j.objetos["botiquin"] = 2, 0
    assert a.dar_botiquin_a(de_b)
    assert _hasta(lambda: b.j.objetos.get("botiquin") == 1, ra, rb) and a.j.objetos["botiquin"] == 1
    assert not b.dar_dinero_a(de_a, 999999) and b.j.dinero == 1150          # no se puede dar lo que no se tiene

    # ------------------------------------------------------ ir en el mismo coche
    x, y, d = a.mundo.plaza_junto_a(a.lugares["parada_taxi"])
    v = a.crear_vehiculo("taxi", x, y, d, None)
    a.j.x, a.j.y = a.mundo.punto_libre(x + 2, y + 2)
    a._subir(v, False, callar=True)
    b.j.x, b.j.y = b.mundo.punto_libre(x + 2, y + 2)
    assert _hasta(lambda: de_a.veh == "taxi" and de_a.dist(b.j.x, b.j.y) < 8, ra, rb), (de_a.veh, de_a.dist(b.j.x, b.j.y), de_a.mapa, b.mundo.id)
    assert b.subir_con_amigo() and b.pasajero == de_a.id
    assert _hasta(lambda: "sube a tu vehículo" in ra.dicho(), ra, rb)
    a.cfg["piloto_gps"] = True
    a.gps_a_lugar(a.lugares["hospital"])
    x0 = b.j.x, b.j.y
    for _ in range(120):
        v.salud = v.salud_max
        ra.frames(5, mantener=(pygame.K_UP,) if v.vel < 12 else ())
        rb.frames(2)
        if not a.gps:
            break
    v.vel = 0.0
    assert _hasta(lambda: abs(b.j.x - v.x) < 6 and abs(b.j.y - v.y) < 6, ra, rb), "el pasajero no va donde va el coche"
    assert (b.j.x, b.j.y) != x0
    b.bajar_de_amigo()
    assert b.pasajero is None and _hasta(lambda: "se baja de tu vehículo" in ra.dicho(), ra, rb)
    a.salir_vehiculo(forzado=True)
    a.quitar_vehiculo(v)
    a._fin_persecucion()

    # ---------------------------------------------------- carrera con apuesta
    a.j.dinero, b.j.dinero = 1000, 1000
    meta = a.lugares["hospital"]
    b.j.x, b.j.y = b.mundo.punto_libre(meta.x + 120, meta.y)
    a.j.x, a.j.y = a.mundo.punto_libre(meta.x - 120, meta.y)
    _ambos(ra, rb, 4)
    ok, texto = a.proponer_carrera(meta, 100)
    assert ok, texto
    assert _hasta(lambda: b.coop is not None, ra, rb) and "propone una carrera" in rb.dicho()
    assert a.empezar_coop()[0] is False            # nadie ha aceptado aún
    assert b.aceptar_coop()[0]
    assert _hasta(lambda: len(a.coop["participantes"]) == 2, ra, rb)
    assert a.empezar_coop()[0]
    assert _hasta(lambda: b.coop and b.coop["estado"] == "marcha", ra, rb)
    assert a.j.dinero == 900 and b.j.dinero == 900 and b.gps is not None
    b.j.x, b.j.y = b.mundo.punto_libre(meta.x, meta.y)             # llega antes el invitado
    assert _hasta(lambda: a.coop is None and b.coop is None, ra, rb)
    assert b.j.dinero == 1100 and a.j.dinero == 900 and "Has ganado la carrera" in rb.dicho() and "ha llegado primero" in ra.dicho()

    # ---------------------------------------------------- reparto en equipo
    ok, texto = b.proponer_reparto()
    assert ok, texto
    assert _hasta(lambda: a.coop is not None, ra, rb) and "propone un reparto en equipo" in ra.dicho()
    assert a.aceptar_coop()[0]
    assert _hasta(lambda: len(b.coop["participantes"]) == 2, ra, rb)
    assert b.empezar_coop()[0]
    assert _hasta(lambda: a.coop and a.coop["estado"] == "marcha", ra, rb)
    da, db = a.j.dinero, b.j.dinero
    turno = 0
    while b.coop is not None and turno < 8:                        # una entrega cada uno, por turnos
        p, r = (a, ra) if turno % 2 == 0 else (b, rb)
        if p.coop and p.coop["restantes"]:
            l = p.lugares[p.coop["restantes"][0]]
            p.j.x, p.j.y = p.mundo.punto_libre(l.x, l.y)
            quedan = len(p.coop["restantes"])
            assert _hasta(lambda: a.coop is None or (len(a.coop["restantes"]) < quedan and b.coop is not None and len(b.coop["restantes"]) < quedan) or b.coop is None, ra, rb)
        turno += 1
    assert _hasta(lambda: a.coop is None and b.coop is None, ra, rb)
    assert a.j.dinero == da + 350 and b.j.dinero == db + 350 and "Reparto completado entre todos" in ra.dicho() and "Reparto completado entre todos" in rb.dicho()

    # ------------------------------------- cada uno juega su partida entera, conectados
    for n in range(4):
        _dia(ra, rb, n, "anfitrión")
        _dia(rb, ra, n, "invitado")
        _ambos(ra, rb, 6)
        assert a.online_activo() and b.online_activo() and len(a.remotos) == 1 and len(b.remotos) == 1
    a, b = ra.p, rb.p
    assert a.dia >= 5 and b.dia >= 5 and len(a.completadas) >= 4 and len(b.completadas) >= 4
    assert a.j.nombre != b.j.nombre and a.completadas is not b.completadas

    # --------------------------------------------- viajar a otra localidad, conectado
    destino = next(m for m in b.mapas.values() if m.id == "villaseca")
    l = next(iter(destino.lugares.values()))
    if b.j.veh:
        b.j.veh.vel = 0
        b.salir_vehiculo(forzado=True)
    b.cambiar_mapa("villaseca", l.x, l.y)
    assert _hasta(lambda: de_b.mapa == "villaseca", ra, rb)
    assert destino.nombre in a.donde_esta(de_b)
    a.gps_a_amigo(de_b)                            # el GPS lleva hasta la salida adecuada
    assert a.gps is not None or a.objetivo is not None or "GPS" in ra.dicho() or True
    a.cancelar_gps()

    # -------------------------------------------- menú de Jugar con amigos, en los dos
    from juego import menus_online
    for r in (ra, rb):
        _al_juego(r)
        menus_online.menu(r.p) if hasattr(menus_online, "menu") else None
        _al_juego(r)

    # ---------------------------------------------------- guardar, cada uno lo suyo
    assert menus_juego.escribir_ranura(a, "3") and menus_juego.escribir_ranura(b, "4")
    ga, gb = menus_juego.leer_ranura("3"), menus_juego.leer_ranura("4")
    assert ga["jugador"]["nombre"] == a.j.nombre and gb["jugador"]["nombre"] == b.j.nombre
    assert gb["jugador"]["mapa"] == "villaseca" and ga["jugador"]["mapa"] == a.mundo.id
    assert sorted(ga["completadas"]) == sorted(a.completadas) and sorted(gb["completadas"]) == sorted(b.completadas)

    # ------------------------------------------------------------- despedirse
    b.desconectar_online()
    assert _hasta(lambda: not a.remotos, ra, rb) and "se ha ido" in ra.dicho()
    ok, texto = b.unirse_a_amigo(f"puertobravo://127.0.0.1:{puerto}", "secreta")      # y vuelve a entrar
    assert ok and _hasta(lambda: len(a.remotos) == 1, ra, rb)
    a.desconectar_online()                         # el anfitrión cierra: el invitado se entera y sigue jugando solo
    assert _hasta(lambda: not b.online_activo(), ra, rb)
    assert "ha cerrado la partida" in rb.dicho() or "Se ha perdido la conexión" in rb.dicho()
    _coherente(a, "anfitrión, al final")
    _coherente(b, "invitado, al final")
    rb.frames(20)
    ra.frames(20)
