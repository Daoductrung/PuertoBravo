"""Tranvía por la ciudad, tren entre localidades, aeropuerto, y las encrucijadas con consecuencias que duran."""
import math

import pygame

from juego import menus_juego, menus_lugares as ml, pantallas
from juego.menus import Dialogo, Menu


def _al_juego(app):
    for _ in range(60):
        if app.pila[-1] is app.partida:
            return
        c = app.pila[-1]
        if isinstance(c, Menu) and not c.escapable:
            c.i = len(c.opciones) - 1
            app.inyectar(pygame.K_RETURN)
        else:
            app.inyectar(pygame.K_ESCAPE)
    assert app.pila[-1] is app.partida


def test_cada_localidad_tiene_su_transporte(robot):
    p = robot.nueva_partida()
    for m in p.mapas.values():
        tipos = [l.tipo for l in m.lugares.values()]
        por_tierra = "salida" in tipos and m.tipo != "mar"
        ciudad = m.tipo == "ciudad"
        assert (tipos.count("tren") == 1) == por_tierra, m.id                 # estación de tren donde se llega por tierra
        assert (tipos.count("aeropuerto") == 1) == ciudad, m.id               # aeropuerto en las ciudades
        paradas = [l for l in m.lugares.values() if l.tipo == "tranvia"]
        assert (len(paradas) >= len(m.barrios)) == ciudad and (ciudad or not paradas), m.id
        if ciudad:
            assert {m.barrio(l.x, l.y)["id"] for l in paradas} == {b["id"] for b in m.barrios}, m.id      # hay parada en todos los barrios
            a = next(l for l in m.lugares.values() if l.tipo == "aeropuerto")
            bi, bj = m.bloque(a.x, a.y)
            assert bi in (0, m.NX - 2) and bj in (0, m.NY - 2), (m.id, bi, bj)                            # en una esquina: las afueras
        for l in m.lugares.values():
            if l.tipo in ("tranvia", "tren", "aeropuerto"):
                assert m.transitable(l.x, l.y) and l.sonido == "lugar_" + l.tipo and l.desc
                assert not [o for o in m.lugares.values() if o is not l and math.hypot(o.x - l.x, o.y - l.y) < 9], l.id   # no pisa a otro lugar
        nombres = [l.nombre for l in paradas]
        assert len(nombres) == len(set(nombres)), m.id
    # un mod que trae su propia parada, o que no quiere transporte, manda
    from juego import mundo as M
    c = {"id": "x", "nombre": "X", "tipo": "ciudad", "avenidas": ["a", "b", "c"], "calles": ["1", "2", "3"], "barrios": [{"id": "b", "nombre": "B", "i": [0, 1], "j": [0, 1]}],
         "lugares": [{"id": "mia", "nombre": "Mi parada", "tipo": "tranvia", "bloque": [0, 0], "lado": "S"}, {"id": "s", "nombre": "Salida", "tipo": "salida", "bloque": [1, 1], "lado": "N"}]}
    M.completar_transporte(c)
    assert [l["id"] for l in c["lugares"] if l["tipo"] == "tranvia"] == ["mia"] and any(l["tipo"] == "tren" for l in c["lugares"])
    c2 = dict(c, lugares=[], transporte=False)
    M.completar_transporte(c2)
    assert c2["lugares"] == []


def test_tranvia_por_la_ciudad(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    linea = ml.linea_tranvia(p)
    assert len(linea) == 16
    a, b = linea[0], linea[5]
    assert [x.id for x in ml.recorrido_tranvia(p, a, b)] == [x.id for x in linea[1:6]]
    assert len(ml.recorrido_tranvia(p, a, linea[-1])) == 1                    # por el lado corto de la línea
    assert not any(x is a for x in ml.recorrido_tranvia(p, a, b))
    # desde una parada: el menú ofrece todas las demás, de la más cercana a la más lejana
    p.teletransportar(a.x, a.y)
    menus_juego.lugar(p, a)
    m = app.pila[-1]
    assert isinstance(m, Menu) and len([o for o in m.opciones if o.texto.startswith("Ir a ")]) == 15 and ": 1 parada, 2 euros" in m.opciones[0].texto
    assert p.interior is None                                                 # es un sitio al aire libre
    # viaje con trayecto: anuncia cada parada y te deja en la elegida
    app.viajes_en_pruebas = True
    k = next(n for n, o in enumerate(m.opciones) if ": 3 paradas" in o.texto)
    destino_txt = m.opciones[k].texto.split("Ir a ")[1].split(":")[0]
    dinero = j.dinero
    m.i = k
    sonidos = []
    original = app.mez.sonar
    app.mez.sonar = lambda n, **kw: (sonidos.append(n), original(n, **kw))[1]
    robot.tecla(pygame.K_RETURN)
    v = app.pila[-1]
    assert isinstance(v, pantallas.LineaTranvia) and len(v.paradas) == 3 and j.dinero == dinero - 2 and "Subes al tranvía" in app.voz.registro[-1]
    robot.tecla(pygame.K_c)
    assert "Próxima parada" in app.voz.registro[-1]
    reloj = p.reloj
    robot.frames(30 * 45)
    app.mez.sonar = original
    assert app.pila[-1] is p and "tranvia" in sonidos and sonidos.count("tranvia_campana") >= 3
    final = next(x for x in linea if x.nombre.endswith(destino_txt))
    assert math.hypot(j.x - final.x, j.y - final.y) < 3 and f"Te bajas del tranvía en {destino_txt}" in robot.dicho() and p.reloj != reloj
    assert sum(1 for f in app.voz.registro[-12:] if "Próxima parada:" in f) >= 2          # ha anunciado las de en medio
    # bajarte antes: Intro durante el viaje te deja en la próxima
    menus_juego.lugar(p, final)
    m = app.pila[-1]
    m.i = len([o for o in m.opciones if o.texto.startswith("Ir a ")]) - 1    # la más lejana
    robot.tecla(pygame.K_RETURN)
    v = app.pila[-1]
    assert len(v.paradas) >= 6
    primera = v.paradas[0]
    robot.tecla(pygame.K_RETURN)
    assert "Te bajas en la próxima" in app.voz.registro[-1]
    robot.frames(30 * 9)
    assert app.pila[-1] is p and math.hypot(j.x - primera.x, j.y - primera.y) < 3
    # sin trayecto, llegas al momento
    app.viajes_en_pruebas = False
    menus_juego.lugar(p, primera)
    m = app.pila[-1]
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is p and j.stats["tranvias"] == 3
    # con la policía detrás, o en coche, no
    j.estrellas = 1
    menus_juego.lugar(p, primera)
    assert app.pila[-1] is p and "no abre las puertas" in app.voz.registro[-1]
    j.estrellas = 0
    # en un pueblo no hay tranvía
    assert ml.linea_tranvia(p, "villaseca") == []


def test_tren_entre_localidades(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    j.dinero = 5000
    saltos = {mid: p.saltos_por_tierra("puerto_bravo", mid) for mid in p.mapas}
    assert saltos["puerto_bravo"] is None and saltos["mar"] is None and saltos["isla_tortuga"] is None and saltos["plataforma"] is None
    assert saltos["villaseca"] == 1 and saltos["monteferro"] == 2 and saltos["fuentefria"] == 3
    est = p.lugares["puerto_bravo_tren"]
    p.teletransportar(est.x, est.y)
    menus_juego.lugar(p, est)
    m = app.pila[-1]
    textos = [o.texto for o in m.opciones if o.texto.startswith("Tren a ")]
    assert len(textos) == sum(1 for s in saltos.values() if s) and textos[0].endswith(": 22 euros")         # las vecinas primero, y más baratas
    assert not any("Isla" in t or "Plataforma" in t for t in textos) and any("Fuentefría: 46 euros" in t for t in textos)
    # la estación de autobuses ya solo vende autobuses
    bus = p.lugares["estacion_pb"]
    assert est.id != bus.id and math.hypot(est.x - bus.x, est.y - bus.y) > 10
    # viaje con trayecto a una localidad lejana
    app.viajes_en_pruebas = True
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Tren a Fuentefría"))
    sonidos = []
    original = app.mez.sonar
    app.mez.sonar = lambda n, **kw: (sonidos.append(n), original(n, **kw))[1]
    robot.tecla(pygame.K_RETURN)
    v = app.pila[-1]
    assert isinstance(v, pantallas.Viaje) and v.medio == "tren" and v.total == 55.0 and "El tren sale de la estación" in app.voz.registro[-1]
    robot.frames(30 * 56)
    app.mez.sonar = original
    assert app.pila[-1] is p and p.mundo.id == "fuentefria" and "tren_silbato" in sonidos and "tren" in sonidos and j.dinero == 5000 - 46
    llegada = p.lugares["fuentefria_tren"]
    assert math.hypot(j.x - llegada.x, j.y - llegada.y) < 3 and "El tren te deja en Estación de tren de Fuentefría" in robot.dicho()
    # y la vuelta, llegando ya con Intro
    menus_juego.lugar(p, llegada)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Tren a Puerto Bravo"))
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)
    app.viajes_en_pruebas = False
    assert p.mundo.id == "puerto_bravo" and j.stats["trenes"] == 2
    menus_juego.lugar(p, bus)
    assert all(o.texto.startswith(("Autobús a ", "Volver")) for o in app.pila[-1].opciones)
    _al_juego(app)


def test_aeropuerto(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    j.dinero = 10000
    aer = p.lugares["puerto_bravo_aeropuerto"]
    p.teletransportar(aer.x, aer.y)
    menus_juego.lugar(p, aer)
    m = app.pila[-1]
    textos = [o.texto for o in m.opciones]
    vuelos = [t for t in textos if t.startswith("Vuelo a ")]
    assert len(vuelos) == 3 and all(": 180 euros" in t for t in vuelos)       # a las otras tres ciudades
    assert "Alquilar una avioneta: 600 euros" in textos and "Alquilar un helicóptero: 900 euros" in textos
    # vuelo de pasajeros con trayecto: despegue, cabina, y aterrizas en el otro aeropuerto
    app.viajes_en_pruebas = True
    sonidos = []
    original = app.mez.sonar
    app.mez.sonar = lambda n, **kw: (sonidos.append(n), original(n, **kw))[1]
    m.i = next(k for k, t in enumerate(textos) if t.startswith("Vuelo a San Lucero"))
    robot.tecla(pygame.K_RETURN)
    v = app.pila[-1]
    assert isinstance(v, pantallas.Viaje) and v.medio == "avion" and "El avión acelera por la pista y despega" in app.voz.registro[-1]
    robot.frames(30 * 46)
    app.mez.sonar = original
    app.viajes_en_pruebas = False
    assert p.mundo.id == "san_lucero" and "avion_despegue" in sonidos and "avion" in sonidos and j.dinero == 10000 - 180 and j.stats["vuelos"] == 1
    dest = p.lugares["san_lucero_aeropuerto"]
    assert math.hypot(j.x - dest.x, j.y - dest.y) < 3 and "Aterrizas en el Aeropuerto de San Lucero" in robot.dicho()
    # alquilar una avioneta: te espera en la pista, te subes y vuelas con ella a otro aeropuerto o a un helipuerto
    menus_juego.lugar(p, dest)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Alquilar una avioneta"))
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is p and j.dinero == 10000 - 180 - 600 and p.gps
    avioneta = next(x for x in p.vehiculos if x.modelo["id"] == "avioneta")
    assert avioneta.dist(dest.x, dest.y) < 40 and not avioneta.cerrado
    menus_juego.lugar(p, dest)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Alquilar una avioneta"))
    robot.tecla(pygame.K_RETURN)
    assert "Ya tienes uno esperando" in app.voz.registro[-1] and j.dinero == 10000 - 780          # no te cobran dos veces
    _al_juego(app)
    p._subir(avioneta, False, callar=True)
    robot.frames(60, mantener=(pygame.K_UP,))
    avioneta.x, avioneta.y, avioneta.vel = dest.x, dest.y, 0.0
    robot.frames(2)
    menus_juego.lugar(p, dest)
    m = app.pila[-1]
    textos = [o.texto for o in m.opciones]
    assert any("Aeropuerto de Puerto Bravo" in t for t in textos) and any("Helipuerto" in t for t in textos) and "vuelo es gratis" in " ".join(app.voz.registro[-3:])
    m.i = next(k for k, t in enumerate(textos) if "Aeropuerto de Puerto Bravo" in t)
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert p.mundo.id == "puerto_bravo" and j.veh is not None and j.veh.modelo["id"] == "avioneta"
    # y el helicóptero de alquiler
    v = j.veh
    v.vel = 0.0
    p.salir_vehiculo(forzado=True)
    p.quitar_vehiculo(v)
    p.teletransportar(aer.x, aer.y)
    menus_juego.lugar(p, aer)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Alquilar un helicóptero"))
    robot.tecla(pygame.K_RETURN)
    assert any(x.modelo["id"] == "helicoptero" for x in p.vehiculos)
    # con la policía detrás no se vuela; en coche hay que bajarse
    j.estrellas = 2
    menus_juego.lugar(p, aer)
    assert app.pila[-1] is p and "control de seguridad" in app.voz.registro[-1]
    j.estrellas = 0
    # el helipuerto, de pasajero, sigue yendo solo a helipuertos
    heli = next(l for l in p.mundo.lugares.values() if l.tipo == "helipuerto")
    p.teletransportar(heli.x, heli.y)
    menus_juego.lugar(p, heli)
    assert not any("Aeropuerto" in o.texto for o in app.pila[-1].opciones)
    _al_juego(app)


def _decidir(robot, ident, opcion):
    """Empieza la misión de la encrucijada y elige la opción dada (empezando en cero)."""
    app = robot.app
    p = app.partida
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    m = por_id[ident]
    l = p.lugares[m["lugar"]]
    if p.mundo.id != l.mapa:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.teletransportar(l.x, l.y)
    p.iniciar_mision(m)
    for _ in range(12):
        if isinstance(app.pila[-1], Dialogo):
            robot.tecla(pygame.K_ESCAPE)
    menu = app.pila[-1]
    assert isinstance(menu, Menu) and not menu.escapable, ident
    menu.i = opcion
    robot.tecla(pygame.K_RETURN)
    robot.saltar_dialogos()
    assert ident in p.completadas
    return por_id


def test_encrucijadas_con_consecuencias_que_duran(robot):
    import test_misiones
    app = robot.app
    # Villaseca: defender la cooperativa te hace socio, y cobras cada medianoche para siempre
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.completadas += ["v04", "s06"]
    por_id = _decidir(robot, "vd1", 0)
    assert p.decisiones["cooperativa"]["renta"] == 150 and "150 euros cada medianoche" in robot.dicho()
    disp = {m["id"] for m in p.misiones_disponibles()}
    assert "vd2" in disp and "vd3" not in disp
    dinero = p.j.dinero
    assert p.rentas_decisiones() == 150 and p.j.dinero == dinero + 150
    p.pasar_horas(24)                                                         # y a medianoche llega solo
    assert p.j.dinero >= dinero + 300
    p.dar_arma("fusil", 300)
    test_misiones._jugar_mision(robot, por_id["vd2"])
    assert p.decisiones["_final"]["texto"] == "Villaseca sigue siendo del pueblo"
    # San Lucero: quedarte con el negocio da renta y Los Lagartos pasan a ser tuyos
    _decidir(robot, "sd1", 1)
    assert p.decisiones["trono"]["renta"] == 400 and p.rep_banda("Los Lagartos") == 60
    disp = {m["id"] for m in p.misiones_disponibles()}
    assert "sd3" in disp and "sd2" not in disp and "sd4" not in disp
    assert p.rentas_decisiones() == 550                                       # se suman las dos
    test_misiones._jugar_mision(robot, por_id["sd3"])
    assert "sd3" in p.completadas
    # el diario lo cuenta, y se guarda con la partida
    robot.tecla(pygame.K_m)
    movil = app.pila[-1]
    movil.i = next(k for k, o in enumerate(movil.opciones) if o.texto.startswith("Diario"))
    robot.tecla(pygame.K_RETURN)
    textos = [o.texto for o in app.pila[-1].opciones]
    assert any("Te deja 150 euros cada medianoche" in t for t in textos) and any("Te deja 400 euros cada medianoche" in t for t in textos)
    _al_juego(app)
    d = p.a_dict()
    app.empezar_partida(d)
    assert app.partida.rentas_decisiones() == 550
    # las otras ramas: vender, y llevar los libros a la policía
    app.volver_al_menu()
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.completadas += ["v04", "s06"]
    dinero = p.j.dinero
    por_id = _decidir(robot, "vd1", 1)
    assert p.j.dinero == dinero + 12000 and "renta" not in p.decisiones["cooperativa"]
    assert {"vd3"} == {m["id"] for m in p.misiones_disponibles() if m["id"] in ("vd2", "vd3")}
    test_misiones._jugar_mision(robot, por_id["vd3"])
    assert p.decisiones["_final"]["texto"] == "Villaseca, vendida"
    _decidir(robot, "sd1", 2)
    assert {"sd4"} == {m["id"] for m in p.misiones_disponibles() if m["id"] in ("sd2", "sd3", "sd4")}
    p.dar_arma("fusil", 300)
    test_misiones._jugar_mision(robot, por_id["sd4"])
    assert p.decisiones["_final"]["texto"] == "San Lucero, por lo legal" and p.rentas_decisiones() == 0


def test_ramas_de_bahia_del_ocaso(robot):
    import test_misiones
    app = robot.app
    for opcion, final, renta in ((0, "ocs7", 0), (1, "ocs8", 300)):
        if app.partida is not None:
            app.volver_al_menu()
        p = robot.nueva_partida()
        p.cfg["sucesos"] = False
        por_id = {m["id"]: m for m in p.datos["misiones"]}
        ocs6 = por_id["ocs6"]
        k = next(n for n, x in enumerate(ocs6["pasos"]) if x["tipo"] == "decision")
        p.completadas += ocs6.get("requiere", [])
        l = p.lugares[ocs6["lugar"]]
        p.cambiar_mapa(l.mapa, l.x, l.y)
        p.mision = {"def": ocs6, "paso": k - 1, "veh": None, "enemigos": [], "objeto": None, "limite": None, "generado": False, "recogido": False,
                    "restos": None, "avisos": set(), "quedan": None, "copia": p.j.a_dict(), "reloj": p.reloj, "dia": p.dia}
        p._siguiente_paso()
        menu = app.pila[-1]
        assert isinstance(menu, Menu) and len(menu.opciones) == 2
        menu.i = opcion
        robot.tecla(pygame.K_RETURN)
        robot.saltar_dialogos()
        assert "ocs6" in p.completadas and p.decisiones["oc_nombre"].get("renta", 0) == renta
        ramas = {m["id"] for m in p.misiones_disponibles() if m["id"] in ("ocs7", "ocs8")}
        assert ramas == {final}
        p.dar_arma("fusil", 300)
        test_misiones._jugar_mision(robot, por_id[final])
        assert final in p.completadas and p.decisiones["_final"]["texto"] == por_id[final]["final_titulo"]
