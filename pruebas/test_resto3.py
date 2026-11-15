"""Lo que pidieron los jugadores en el foro y entra en la 1.6.2: territorios con vida, gente en su sitio, y detalles."""
import math

import pygame


def _a_la_partida(app, p):
    while app.pila[-1] is not p:
        app.cerrar(app.pila[-1])


class Azar:
    """Un azar con el resultado escrito de antemano, para probar cada suceso."""

    def __init__(self, tiros, elegir):
        self.tiros, self.elegir = list(tiros), list(elegir)

    def random(self):
        return self.tiros.pop(0)

    def choice(self, lista):
        e = self.elegir.pop(0)
        return e if e in lista else lista[0]


def test_territorios_fama_y_sucesos(robot):
    from juego import menus_extra, sistemas
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    p.cfg["sucesos"] = True
    b0, b1, b2 = [b["id"] for b in p.mundo.barrios[:3]]
    # conquistar da fama: mucha el primero, menos los siguientes
    famas = []
    for b in (b0, b1, b2):
        antes = j.reputacion
        p.mision = {"def": {"id": "conquista", "titulo": "Conquista", "territorio": b, "repetible": True, "pasos": [], "recompensa": {}}, "paso": 0, "enemigos": []}
        p._completar_mision()
        famas.append(j.reputacion - antes)
    assert famas[0] >= 15 and famas[0] > famas[1] > famas[2] > 0 and len(j.territorios) == 3
    # ataque con banda pequeña: queda pendiente y hay que ir
    j.banda = 0
    sistemas.sucesos_territorio(p, Azar([0.0], ["Los Calaveras", "ataque", b1]))
    assert j.amenaza and j.amenaza["territorio"] == b1 and "está atacando" in robot.dicho()
    menus_extra.territorios(p)
    m = app.pila[-1]
    assert m.opciones[0].texto.startswith("Defender ")
    robot.tecla(pygame.K_RETURN)
    assert p.mision and p.mision["def"]["id"] == "defensa" and app.pila[-1] is p
    for paso in p.mision["def"]["pasos"]:
        assert paso["lugar"] in p.lugares
    p.mision["paso"] = len(p.mision["def"]["pasos"]) - 1
    p._siguiente_paso()
    assert j.amenaza is None and b1 in j.territorios and "sigue siendo tuyo" in robot.dicho()
    # ataque sin defender: al vencer el plazo se pierde el barrio
    sistemas.sucesos_territorio(p, Azar([0.0], ["Los Calaveras", "ataque", b2]))
    assert j.amenaza
    p.dia += 1
    sistemas.sucesos_territorio(p, Azar([0.99], []))
    assert j.amenaza is None and b2 not in j.territorios and "se lo ha quedado" in robot.dicho()
    j.territorios.append(b2)
    # con banda grande, la banda lo defiende sola
    j.banda, j.banda_nombre = 5, "Los del Muelle"
    sistemas.sucesos_territorio(p, Azar([0.0, 0.0], ["Los Calaveras", "ataque", b0]))
    assert j.amenaza is None and "los ha echado" in robot.dicho()
    # pacto: se cobra y durante una semana no hay ataques
    sistemas.sucesos_territorio(p, Azar([0.0], ["Los Calaveras", "pacto"]))
    assert j.oferta_pacto and j.oferta_pacto["precio"] == 1500
    menus_extra.territorios(p)
    m = app.pila[-1]
    assert m.opciones[0].texto.startswith("Pacto con")
    dinero = j.dinero
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)
    assert j.dinero == dinero + 1500 and j.pacto_hasta == p.dia + 7 and j.oferta_pacto is None
    _a_la_partida(app, p)
    sistemas.sucesos_territorio(p, Azar([0.0], ["Los Calaveras", "ataque", b0]))
    assert j.amenaza is None
    # la policía: pagar o redada
    sistemas.sucesos_territorio(p, Azar([0.0], ["Los Calaveras", "policia"]))
    assert j.redada and j.redada["precio"] == 750
    j.dinero = 5000
    p.dia += 1
    sistemas.sucesos_territorio(p, Azar([0.99], []))
    assert j.redada is None and j.dinero == 5000 - 900 and "redada" in robot.dicho()
    # se guarda con la partida
    j.redada = {"precio": 100, "dia": p.dia}
    d = p.a_dict()
    app.empezar_partida(d)
    assert app.partida.j.redada == {"precio": 100, "dia": p.dia} and app.partida.j.pacto_hasta == j.pacto_hasta


def test_cosas_del_foro(robot):
    from juego import menus_extra, menus_juego, pantallas
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    # aprender los sonidos: al pulsar Intro solo suena el sonido elegido
    menus_juego.sonidos(app)
    m = app.pila[-1]
    for _ in range(3):
        if any(o.callado for o in m.opciones):
            break
        robot.tecla(pygame.K_RETURN)                                          # entra en un grupo, si los hay
        m = app.pila[-1]
    sonados = []
    original = app.mez.sonar
    app.mez.sonar = lambda n, **k: (sonados.append(n), original(n, **k))[1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.callado)
    robot.tecla(pygame.K_RETURN)
    app.mez.sonar = original
    assert sonados and "menu_ok" not in sonados
    _a_la_partida(app, p)
    # agachado sin darte cuenta: al intentar correr te lo dice, y la V también
    j.agachado = True
    robot.tecla(pygame.K_LSHIFT)
    assert "Estás agachado" in app.voz.registro[-1]
    robot.tecla(pygame.K_v)
    assert "Estás agachado" in app.voz.registro[-1]
    j.agachado = False
    # guardaespaldas: se pueden despedir
    p.crear_aliado()
    p.crear_aliado()
    menus_extra.servicios(p)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Despedir a tus guardaespaldas: llevas 2"))
    robot.tecla(pygame.K_RETURN)
    assert not [e for e in p.personas if e.tipo == "aliado"] and "Despides a tus 2 guardaespaldas" in app.voz.registro[-1]
    _a_la_partida(app, p)
    # vuelo en helicóptero con trayecto
    app.viajes_en_pruebas = True
    llegado = []
    pantallas.viajar(app, 10, lambda: llegado.append(1), destino="San Lucero", vuelo=True)
    v = app.pila[-1]
    assert isinstance(v, pantallas.Viaje) and v.vuelo and "El helicóptero despega" in app.voz.registro[-1] and v.motor.nombre == "motor_helicoptero"
    robot.frames(30 * 11)
    assert llegado and app.pila[-1] is p
    app.viajes_en_pruebas = False


def test_gente_de_la_vida_social_en_su_sitio(robot):
    from juego import menus_juego, sistemas
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    chiri = p.lugares["chiringuito"]
    p.teletransportar(chiri.x, chiri.y)
    assert sistemas.personas_aqui(p, chiri) == []                             # sin el contenido para adultos, nada cambia
    menus_juego.lugar(p, chiri)
    assert not any("está aquí" in o.texto for o in app.pila[-1].opciones)
    _a_la_partida(app, p)
    app.cfg["adultos"] = True
    try:
        assert [x["id"] for x in sistemas.personas_aqui(p, chiri)] == ["lucia"]
        menus_juego.lugar(p, chiri)
        m = app.pila[-1]
        assert m.opciones[0].texto == "Lucía está aquí: acercarte a hablar"
        robot.tecla(pygame.K_RETURN)
        ficha = app.pila[-1]
        assert ficha.titulo == "Lucía" and "lucia" in j.relaciones
        ficha.i = next(k for k, o in enumerate(ficha.opciones) if o.texto.startswith("Proponerle salir contigo"))
        robot.tecla(pygame.K_RETURN)
        a = p.acompanante
        assert a and a["pid"] == "lucia" and app.pila[-1] is p and "se viene contigo" in robot.dicho()
        # te sigue a pie y sube contigo al coche
        x, y = p.pos()
        p.teletransportar(*p.mundo.punto_libre(x + 10, y))
        robot.frames(120)
        assert math.hypot(a["x"] - p.pos()[0], a["y"] - p.pos()[1]) < 4
        v = p.crear_vehiculo("sedan", p.j.x, p.j.y, 0, None)
        p._subir(v, False, callar=True)
        robot.frames(3)
        assert math.hypot(a["x"] - p.pos()[0], a["y"] - p.pos()[1]) < 0.5
        a["metros"] = 399
        v.x += 5
        robot.frames(2)
        assert a["puntos"] >= 1                                               # el paseo cuenta
        p.salir_vehiculo(forzado=True)
        # llevarle a un buen sitio le gusta; dejarle donde estaba termina el paseo
        cine = p.lugares["cine_pb"]
        p.teletransportar(cine.x, cine.y)
        robot.frames(2)
        puntos = a["puntos"]
        menus_juego.lugar(p, cine)
        assert a["puntos"] == puntos + 4 and "le gusta el plan" in robot.dicho()
        _a_la_partida(app, p)
        af = p.relacion("lucia").get("afinidad", 0)
        p.teletransportar(chiri.x, chiri.y)
        robot.frames(2)
        menus_juego.lugar(p, chiri)
        assert p.acompanante is None and "Dejas a Lucía donde estaba" in robot.dicho() and p.relacion("lucia").get("afinidad", 0) > af
        _a_la_partida(app, p)
        assert not sistemas.empezar_paseo(p, sistemas.personas_aqui(p, chiri)[0])      # una vez al día
        # dentro del local también está, como una sala más
        loc = sistemas.Local(p, chiri)
        assert any(isinstance(h[2], tuple) and h[2] == ("persona", "lucia") for h in loc.habitaciones)
    finally:
        app.cfg["adultos"] = False
