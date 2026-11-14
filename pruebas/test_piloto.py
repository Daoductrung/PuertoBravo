"""El piloto del GPS, que lleva el coche solo, comer con la vida realista y el apartado Acerca de."""
import math

import pygame

from juego import VERSION, menus_juego
from juego.menus import Menu


def _al_volante(robot, modelo="utilitario"):
    p = robot.p
    j = p.j
    x, y, rumbo = p.mundo.plaza_aparcamiento(j.x, j.y) if hasattr(p.mundo, "plaza_aparcamiento") else (j.x, j.y, 0)
    v = p.crear_vehiculo(modelo, x, y, rumbo, None)
    p._subir(v, False, callar=True)
    return v


def test_el_piloto_lleva_el_coche_solo_hasta_el_destino(robot):
    p = robot.nueva_partida()
    p.cfg["conduccion"] = "asistida"
    p.cfg["piloto_gps"] = False
    p.cfg["sucesos"] = False
    v = _al_volante(robot)
    robot.frames(10)                                                 # el coche se coloca en su carril
    x0, y0 = v.x, v.y
    destino = max((l for l in p.mundo.lugares.values() if l.tipo in ("banco", "hospital", "taller", "tienda", "farmacia")), key=lambda l: math.hypot(l.x - x0, l.y - y0))
    p.gps_a_lugar(destino, callar=True)
    lejos = math.hypot(destino.x - x0, destino.y - y0)
    assert lejos > 150 and not p.piloto_completo()
    robot.frames(60)
    assert abs(v.vel) < 0.01                                         # sin piloto y sin tocar nada, el coche no avanza
    robot.tecla(pygame.K_y)
    assert p.piloto_completo() and "va solo hasta" in robot.dicho()
    maxima = 0.0
    for _ in range(400):                                             # hasta doscientos segundos de viaje, sin pulsar una tecla
        robot.frames(15)
        maxima = max(maxima, v.vel)
        assert p.j.estrellas == 0
        if not p.gps:
            break
    assert not p.gps, f"no llegó: quedan {math.hypot(destino.x - v.x, destino.y - v.y):.0f} metros. {robot.dicho()[-300:]}"
    assert math.hypot(destino.x - v.x, destino.y - v.y) < 40 and 8 < maxima <= 14.5
    assert v.salud > v.salud_max * 0.9                               # y sin golpes
    robot.frames(90)
    assert abs(v.vel) < 3                                            # al llegar, se va parando
    # el jugador manda siempre: con el freno pisado no acelera, y la tecla Y lo apaga
    p.gps_a_lugar(next(l for l in p.mundo.lugares.values() if l is not destino and math.hypot(l.x - v.x, l.y - v.y) > 150), callar=True)
    robot.frames(60, mantener=(pygame.K_SPACE,))
    assert abs(v.vel) < 1
    robot.tecla(pygame.K_y)
    assert not p.cfg["piloto_gps"] and not p.piloto_completo()


def test_con_vida_realista_se_come_por_hambre(robot):
    p = robot.nueva_partida()
    j = p.j
    comida = p.datos["comidas"][0]
    j.dinero = 500
    j.salud = j.salud_max
    p.cfg["vida_realista"] = False
    menus_juego._comprar_comida(p, comida)()
    assert "No tienes hambre: tu salud está al máximo" in robot.dicho() and j.dinero == 500
    p.cfg["vida_realista"] = True                                    # antes, con la salud entera no dejaba comer aunque tuvieras hambre
    j.hambre = 85.0
    menus_juego._comprar_comida(p, comida)()
    assert j.dinero < 500 and j.hambre <= 40 and "Estás" in robot.dicho()
    j.hambre = 0.0
    dinero = j.dinero
    menus_juego._comprar_comida(p, comida)()
    assert j.dinero == dinero and "Ahora no tienes hambre" in robot.dicho()
    p.cfg["vida_realista"] = False


def test_acerca_de(robot, monkeypatch):
    abiertos = []
    monkeypatch.setattr(menus_juego.os, "startfile", lambda ruta: abiertos.append(ruta), raising=False)
    app = robot.app
    principal = app.pila[-1]
    textos = [o.texto for o in principal.opciones]
    assert textos[-2:] == ["Acerca de", "Salir"]
    principal.i = len(textos) - 2
    robot.tecla(pygame.K_RETURN)
    m = app.pila[-1]
    assert isinstance(m, Menu) and "Acerca de" in m.titulo
    lineas = [o.texto for o in m.opciones]
    assert f"versión {VERSION}" in lineas[0] and "Héctor J. Benítez Corredera" in lineas[1] and "Copyright 2026, Héctor J. Benítez Corredera" in lineas[2] and "MIT" in lineas[2]
    cafe = next(k for k, t in enumerate(lineas) if t == "Invítame a un café si te gusta mi trabajo")
    m.i = cafe
    robot.tecla(pygame.K_RETURN)
    assert abiertos == ["https://www.paypal.com/paypalme/hjbcdonaciones"] and "donaciones" in robot.dicho()
    for texto, trozo in (("Página del proyecto en GitHub", "github.com/hxebolax/PuertoBravo"), ("Avisar de un fallo o proponer una mejora", "/issues"),
                         ("Mastodon del autor", "comunidad.nvda.es"), ("Novedades de esta versión", "novedades.html")):
        m.i = lineas.index(texto)
        robot.tecla(pygame.K_RETURN)
        assert trozo in abiertos[-1]
    robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is principal
