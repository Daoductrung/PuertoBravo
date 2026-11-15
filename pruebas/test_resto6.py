"""Contenido para adultos que ahora se juega: la noche paso a paso y el laboratorio."""
import random

import pygame

from juego.menus import Dialogo, Menu


def _cerrar_todo(app, p):
    while app.pila[-1] is not p:
        app.cerrar(app.pila[-1])


def test_la_noche_paso_a_paso(robot):
    from juego import laboratorio as L
    p = robot.nueva_partida()
    app = robot.app
    app.cfg["adultos"] = True
    try:
        assert L.ritmo_de("Lucía", 1) in L.RITMOS and len({L.ritmo_de("Lucía", d) for d in range(3)}) == 3      # cambia de un día a otro
        for texto, opciones in L.MOMENTOS:
            assert len(opciones) == 3
        # escuchar y acertar: sintonía alta
        resultado = []
        n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
        n.ritmo = "lento"
        n.empezar()
        for _ in range(12):
            m = app.pila[-1]
            if isinstance(m, Dialogo):
                break
            assert isinstance(m, Menu) and not m.escapable
            robot.tecla(pygame.K_ESCAPE)
            assert app.pila[-1] is m                                          # de la escena no se sale a medias
            m.i = next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Poner música", "Acariciarle despacio", "Preguntarle", "Ir despacio"))), 0)
            robot.tecla(pygame.K_RETURN)
        assert isinstance(app.pila[-1], Dialogo) and "Se apaga la luz" in app.voz.registro[-1]
        robot.tecla(pygame.K_RETURN)                                          # la segunda frase: cómo ha ido
        robot.tecla(pygame.K_RETURN)
        assert resultado and resultado[0] >= 0.99
        texto = " ".join(app.voz.registro[-14:])
        assert "Despacio. Hoy quiero que dure." in texto and "se recuerdan" in texto
        # ir más deprisa de lo que quiere: te pide que esperes, y parar a preguntar es lo que vale
        resultado.clear()
        n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
        n.ritmo = "lento"
        n.empezar()
        m = app.pila[-1]
        m.i = 1                                                               # besarle antes de que diga nada
        robot.tecla(pygame.K_RETURN)
        m = app.pila[-1]
        assert "Espera" in m.titulo or "Un momento" in m.titulo
        assert [o.texto for o in m.opciones] == ["Parar, y preguntarle si está bien", "Bajar el ritmo sin decir nada"]
        robot.tecla(pygame.K_RETURN)
        assert n.puntos == 1.0 and "Paras." in app.pila[-1].titulo
        _cerrar_todo(app, p)
        # no escuchar: sintonía baja
        resultado.clear()
        n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
        n.ritmo = "lento"
        n.empezar()
        for _ in range(14):
            m = app.pila[-1]
            if isinstance(m, Dialogo):
                break
            m.i = 1 if len(m.opciones) == 2 else next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Besarle antes", "Abrazarle fuerte", "Con prisa"))), 1)
            robot.tecla(pygame.K_RETURN)
        robot.saltar_dialogos()
        assert resultado and resultado[0] < 0.5
        # en el juego: la noche por pasos da más o menos ánimo según cómo haya ido; con la opción quitada, va como antes
        animo = p.j.animo = 30.0
        p.encuentro("Lucía", "romantico", "tu casa")
        assert isinstance(app.pila[-1], Menu)
        robot.saltar_dialogos()
        assert p.j.animo > animo and p.j.stats.get("noches", 0) == 1
        app.cfg["noche_por_pasos"] = False
        p.encuentro("Lucía", "romantico", "tu casa")
        assert isinstance(app.pila[-1], Dialogo)
        robot.saltar_dialogos()
        assert p.j.stats["noches"] == 2
        # nada de lo que se dice es explícito
        todo = " ".join(t for t, ops in L.MOMENTOS for t in [t] + [o[0] + o[2] for o in ops]).lower()
        for palabra in ("sexo", "desnud", "pene", "vagina", "pezon", "orgasm", "follar", "penetr"):
            assert palabra not in todo
    finally:
        app.cfg["adultos"] = False
        app.cfg["noche_por_pasos"] = True


class Fijo:
    """Un azar que no se mueve: la deriva siempre hacia arriba y ningún suceso."""

    def __init__(self, tiro=0.99):
        self.tiro = tiro

    def choice(self, lista):
        return lista[-1]

    def random(self):
        return self.tiro

    def uniform(self, a, b):
        return a


def test_laboratorio(robot):
    from juego import laboratorio as L, menus_adultos, menus_juego
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    casa = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and l.id != "casa_abuela")
    j.propiedades.append(casa.id)
    j.dinero = 50000
    assert L.opciones_casa(p, casa, Menu, menus_juego.Opcion) == []           # sin el contenido para adultos no existe
    app.cfg["adultos"] = True
    app.aplicar_adultos()
    try:
        ops = L.opciones_casa(p, casa, Menu, menus_juego.Opcion)
        assert len(ops) == 1 and ops[0].texto.startswith("Montar un laboratorio")
        ops[0].accion()
        assert casa.id in j.laboratorios and j.dinero == 50000 - L.PRECIO_LAB
        # el material se compra en los proveedores
        o = L.opcion_proveedor(p, menus_juego.Opcion)
        o.accion()
        o.accion()
        assert j.material == 2 and "Tienes 2" in o.texto
        prov = p.lugares.get("trastienda")
        if prov is not None:
            p.teletransportar(prov.x, prov.y)
            menus_adultos.proveedor(p, prov)
            assert any(x.texto.startswith("Material de laboratorio") for x in app.pila[-1].opciones)
            _cerrar_todo(app, p)
        # sin material no se trabaja
        cristal = next(s for s in p.dato_adulto("sustancias") if s["id"] == "cristal")
        # una tanda bien llevada: corriges la deriva y sacas muchas unidades
        j.material = 1
        c = L.Coccion(p, casa, cristal, azar=Fijo())
        app.abrir(c)
        for _ in range(int(L.DURA * 30) + 5):
            if c.hecho:
                break
            (app.teclas.add if c.valor < -0.05 else app.teclas.discard)(pygame.K_UP)
            (app.teclas.add if c.valor > 0.05 else app.teclas.discard)(pygame.K_DOWN)
            app.paso(1 / 30)
        app.teclas.clear()
        assert c.hecho and c.bien > 0.8 * L.DURA and j.sustancias.get("cristal", 0) >= 14 and "Una tanda limpia" in robot.dicho()
        assert app.pila[-1] is p and j.stats["fabricado"] >= 14
        # dejarlo irse arriba: arde, pierdes el laboratorio y viene la policía
        c = L.Coccion(p, casa, cristal, azar=Fijo(0.0))
        c.deriva = 0.4
        app.abrir(c)
        salud = j.salud
        for _ in range(int(L.DURA * 30) + 5):
            if c.hecho:
                break
            c.deriva = 0.4
            app.paso(1 / 30)
        assert c.hecho and casa.id not in j.laboratorios and j.salud < salud and "arde" in robot.dicho() and (j.puntos_busqueda > 0 or j.estrellas > 0)
        # abandonar con Escape echa a perder la tanda
        j.laboratorios.append(casa.id)
        antes = j.sustancias.get("cristal", 0)
        c = L.Coccion(p, casa, cristal, azar=Fijo())
        app.abrir(c)
        robot.tecla(pygame.K_ESCAPE)
        assert c.hecho and j.sustancias.get("cristal", 0) == antes and "a medias" in app.voz.registro[-1]
        # está en el menú de la casa, y se guarda con la partida
        j.material = 3
        p.teletransportar(casa.x, casa.y)
        menus_juego._casa(p, casa)
        assert any(o.texto == "Entrar en el laboratorio" for o in app.pila[-1].opciones)
        _cerrar_todo(app, p)
        d = p.a_dict()
        app.empezar_partida(d)
        assert app.partida.j.laboratorios == [casa.id] and app.partida.j.material == 3
    finally:
        app.cfg["adultos"] = False
        app.aplicar_adultos()
