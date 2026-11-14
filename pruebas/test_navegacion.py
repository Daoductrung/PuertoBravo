"""Comprueba que un jugador que solo sigue el GPS y la baliza llega a su destino."""
import math
import random

import pygame


def _seguir_a_pie(robot, destino, segundos=400):
    p = robot.p
    j = p.j
    p.gps_a_lugar(destino)
    for _ in range(int(segundos * 6)):
        if not p.gps:
            return True
        ruta = p.gps["ruta"]
        bx, by = ruta[0]
        if len(ruta) > 1:
            bx += 7.5 if j.x >= bx else -7.5
            by += 7.5 if j.y >= by else -7.5
        dx, dy = bx - j.x, by - j.y
        teclas = []
        if abs(dx) > 1.0:
            teclas.append(pygame.K_RIGHT if dx > 0 else pygame.K_LEFT)
        if abs(dy) > 1.0:
            teclas.append(pygame.K_UP if dy > 0 else pygame.K_DOWN)
        j.salud = 100
        robot.frames(5, mantener=tuple(teclas) + (pygame.K_LSHIFT,))
    return False


def test_gps_a_pie(robot):
    p = robot.nueva_partida()
    p.cfg["semaforos"] = False
    rng = random.Random(4)
    for mapa, pares in (("puerto_bravo", 6), ("san_lucero", 3), ("villaseca", 2), ("isla_tortuga", 2), ("monteferro", 3), ("fuentefria", 2), ("plataforma", 1)):
        ls = [l for l in p.mapas[mapa].lugares.values()]
        for _ in range(pares):
            a, b = rng.sample(ls, 2)
            if p.mundo.id != mapa:
                p.cambiar_mapa(mapa, a.x, a.y)
            p.j.x, p.j.y = a.x, a.y
            for v in list(p.vehiculos):          # sin tráfico: aquí solo se prueba la ruta
                if v.ia == "trafico":
                    p.quitar_vehiculo(v)
            p._fin_persecucion()
            assert _seguir_a_pie(robot, b), f"no llega de {a.id} a {b.id}: está a {math.hypot(p.j.x - b.x, p.j.y - b.y):.0f} m. {robot.dicho()}"


def _conducir(robot, destino, segundos=240):
    p = robot.p
    v = p.j.veh
    p.gps_a_lugar(destino)
    for _ in range(int(segundos * 6)):
        if not p.gps:
            return True
        d = math.hypot(destino.x - v.x, destino.y - v.y)
        v.salud = v.salud_max
        p.j.salud = 100
        if d < 45 and v.vel > 6:
            robot.frames(5, mantener=(pygame.K_DOWN,))
        elif v.vel < (7 if d < 60 else 16):
            robot.frames(5, mantener=(pygame.K_UP,))
        else:
            robot.frames(5)
    return False


def test_gps_al_volante_con_piloto(robot):
    p = robot.nueva_partida()
    p.cfg["piloto_gps"] = True
    rng = random.Random(9)
    for mapa, viajes in (("puerto_bravo", 6), ("san_lucero", 3), ("villaseca", 2), ("monteferro", 3)):
        m = p.mapas[mapa]
        ls = [l for l in m.lugares.values() if "xy" not in l.d]
        a = rng.choice(ls)
        if p.j.veh:
            v = p.j.veh
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
        if p.mundo.id != mapa:
            p.cambiar_mapa(mapa, a.x, a.y)
        x, y, d = m.plaza_junto_a(a)
        v = p.crear_vehiculo("sedan", x, y, d, None)
        p.j.x, p.j.y = m.punto_libre(x + 2, y + 2)
        p._subir(v, False)
        for _ in range(viajes):
            b = rng.choice([l for l in ls if math.hypot(l.x - v.x, l.y - v.y) > 150])
            for o in list(p.vehiculos):
                if o is not v:
                    p.quitar_vehiculo(o)
            p.plazas_usadas.update(pl["id"] for pl in m.aparcados)
            p._fin_persecucion()
            assert _conducir(robot, b), f"no llega a {b.id}: está a {math.hypot(v.x - b.x, v.y - b.y):.0f} m, rumbo {v.rumbo}. {robot.dicho()}"


def test_gps_en_el_mar(robot):
    p = robot.nueva_partida()
    a = p.lugares["mar_cala"]
    p.cambiar_mapa("mar", a.x, a.y - 20)
    v = p.crear_vehiculo("lancha_rapida", a.x, a.y - 20, 2, None)
    v.rumbo = 180.0
    p._subir(v, False, callar=True)
    b = p.lugares["mar_bajo"]
    p.gps_a_lugar(b)
    for _ in range(3000):
        if not p.gps:
            break
        ruta = p.gps["ruta"]
        desv = (math.degrees(math.atan2(ruta[0][0] - v.x, ruta[0][1] - v.y)) - v.rumbo + 180) % 360 - 180
        teclas = [pygame.K_UP] if math.hypot(b.x - v.x, b.y - v.y) > 60 or v.vel < 3 else []
        if abs(desv) > 6:
            teclas.append(pygame.K_RIGHT if desv > 0 else pygame.K_LEFT)
        v.salud = v.salud_max
        robot.frames(3, mantener=tuple(teclas))
    assert math.hypot(b.x - v.x, b.y - v.y) < 40, robot.dicho()


def test_caminar_solo_siguiendo_el_gps(robot):
    """Lo que piden en los foros: marcar un destino y que el personaje vaya andando él solo."""
    p = robot.nueva_partida()
    j = p.j
    for v in list(p.vehiculos):
        if v.ia == "trafico":
            p.quitar_vehiculo(v)
    p.cancelar_gps()
    robot.tecla(pygame.K_u)                                   # sin destino, avisa
    assert "marca antes un destino" in robot.dicho() and not getattr(p, "paseo_auto", False)
    m = p.mundo
    destino = max((l for l in m.lugares.values() if "xy" not in l.d), key=lambda l: -abs(math.hypot(l.x - j.x, l.y - j.y) - 300))
    p.gps_a_lugar(destino)
    robot.tecla(pygame.K_u)
    assert p.paseo_auto and "Caminas solo" in robot.dicho()
    x0, y0 = j.x, j.y
    robot.frames(60)
    assert math.hypot(j.x - x0, j.y - y0) > 3                  # anda sin tocar nada
    robot.frames(10, mantener=(pygame.K_UP,))                 # una flecha lo detiene
    assert not p.paseo_auto and "Dejas de caminar solo" in robot.dicho()
    robot.tecla(pygame.K_u)
    for _ in range(3000):
        if not p.gps:
            break
        j.salud = 100
        for v in list(p.vehiculos):
            if v.ia == "trafico":
                p.quitar_vehiculo(v)
        p._fin_persecucion()
        robot.frames(5, mantener=(pygame.K_LSHIFT,))          # con Mayúsculas, corre
    assert not p.gps and math.hypot(j.x - destino.x, j.y - destino.y) < 25, robot.dicho()
    robot.frames(3)
    assert not p.paseo_auto
