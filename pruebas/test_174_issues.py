"""1.7.4: lo pedido en las issues 23 (el desguace y las mejoras) y 24 (la lista de lugares, de más cerca a más lejos)."""
import math

import pygame

from juego import desguace as D, sistemas
from juego.menus import Menu


def _desguace(p):
    return next(x for x in p.mundo.lugares.values() if x.tipo == "desguace")


def _coche(p, l, modelo="sedan"):
    v = p.crear_vehiculo(modelo, l.x + 4, l.y, 0, "aparcado")
    v.cerrado = False
    return v


def test_lo_robado_se_paga_como_robado_y_lo_mejorado_es_tuyo(robot):
    p = robot.nueva_partida()
    l = _desguace(p)
    v = _coche(p, l)
    p._subir(v, True, callar=True)                            # robado de la calle: ahora sí lo sabe el desguace
    assert v.robado and D.robado(v)
    entero = int(D.valor(v) * (0.3 + 0.7 * v.salud / v.salud_max))
    assert D.precio(p, v) == int(entero * D.AJ("robado_pct") / 100)
    # se guarda con la partida
    d = p._ficha_garaje(v)
    assert d["robado"] is True and p._veh_de_dict(d).robado is True
    # al mejorarlo en un taller pasa a ser tuyo, y el desguace te devuelve parte de las mejoras
    cual = next(iter(sistemas.MEJORAS))
    p.j.dinero = 100000
    ops = sistemas.opciones_taller(p, v, __import__("juego.menus", fromlist=["Opcion"]).Opcion)
    next(o for o in ops if o.accion).accion()
    assert sistemas.nivel(v, cual) == 1 or any(sistemas.nivel(v, k) == 1 for k in sistemas.MEJORAS)
    assert not v.robado and not D.robado(v)
    pagado = D.gastado_en_mejoras(v)
    assert pagado > 0
    estado = 0.3 + 0.7 * v.salud / v.salud_max
    assert D.precio(p, v) == int((D.valor(v) + pagado * D.AJ("mejoras_pct") / 100) * estado)


def test_las_mejoras_suman_y_cada_nivel_cuesta_lo_suyo(robot):
    p = robot.nueva_partida()
    v = _coche(p, _desguace(p))
    v.propio = True
    sin = D.precio(p, v)
    k = next(iter(sistemas.MEJORAS))
    sistemas.poner(v, {k: 3})
    assert D.gastado_en_mejoras(v) == sistemas.MEJORAS[k]["precio"] * (1 + 2 + 3)
    assert D.precio(p, v) > sin


def test_el_autobus_vale_como_chatarra_y_lo_oficial_y_lo_alquilado_no_se_compran(robot):
    p = robot.nueva_partida()
    l = _desguace(p)
    bus = _coche(p, l, "autobus")
    bus.propio = True
    assert D.precio(p, bus) > 0                                # antes, «ni regalado»
    patrulla = _coche(p, l, "patrulla")
    patrulla.propio = True
    motivo = D.por_que_no(patrulla)
    assert D.precio(p, patrulla) == 0 and ("oficial" in motivo or "coche patrulla" in motivo), motivo
    taxi = _coche(p, l, "taxi")
    taxi.propio, taxi.alquilado = True, True
    assert D.precio(p, taxi) == 0 and "alquilado" in D.por_que_no(taxi)
    # el menú lo dice antes de elegir
    from juego import menus_juego
    p.j.veh = patrulla
    p.j.x, p.j.y = patrulla.x, patrulla.y
    menus_juego._desguace(p, l)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and "aquí no lo compran" in m.opciones[0].texto


def test_la_lista_de_lugares_se_ordena_por_cercania_y_el_tabulador_lo_cambia(robot):
    p = robot.nueva_partida()
    p.cfg["orden_lugares"] = "cercania"
    from juego import menus_juego
    menus_juego.lista_lugares(p)
    robot.app.pila[-1].i = 0                                   # Todos los lugares
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    x, y = p.pos()
    nombres = [o.texto for o in m.opciones if not o.texto.startswith("Volver")]
    lugares = sorted(p.mundo.lugares.values(), key=lambda l: math.hypot(l.x - x, l.y - y))
    assert nombres[0].startswith(lugares[0].nombre) and nombres[-1].startswith(lugares[-1].nombre)
    robot.tecla(pygame.K_TAB)
    assert p.cfg["orden_lugares"] == "alfabetico" and "En orden alfabético" in robot.dicho()
    nombres = [o.texto for o in m.opciones if not o.texto.startswith("Volver")]
    assert nombres[0].lower() <= nombres[-1].lower()
    robot.tecla(pygame.K_TAB)
    assert p.cfg["orden_lugares"] == "cercania" and "De más cerca a más lejos" in robot.dicho()
    p.cfg["orden_lugares"] = "alfabetico"


def test_el_boton_vista_del_mando_cambia_el_orden_en_los_menus():
    from juego import mando
    assert mando.MENU["back"] == pygame.K_TAB
