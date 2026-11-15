"""La partida total: con el tiempo acelerado, se usa todo lo que el juego tiene, buscando cualquier cosa que falle.

Completa a las rondas de test_ronda.py (todos los menús y todos los lugares) y a test_misiones.py (todas las
misiones) con lo que ellas no tocan: todos los vehículos y lo que se hace con cada uno, todas las armas y los objetos,
todos los interiores sala por sala, el mar por encima y por debajo, el aire, todos los juegos de mesa hasta el final,
las tres ramas de la historia, y muchos días seguidos con barrios, banda y sucesos.
"""
import math
import random

import pygame

from juego import menus_juego, mesa, sistemas
from juego.menus import Dialogo, Menu, Opcion
from test_ronda import BASURA, _coherente


class Total:
    def __init__(self, robot):
        self.robot, self.app = robot, robot.app
        self.leido = len(robot.app.voz.registro)
        self.cuenta = {}

    @property
    def p(self):
        return self.app.partida

    def suma(self, que, n=1):
        self.cuenta[que] = self.cuenta.get(que, 0) + n

    def voz(self, donde):
        reg = self.app.voz.registro
        for frase in reg[self.leido:]:
            assert isinstance(frase, str) and frase.strip(), f"frase vacía en {donde}"
            assert not BASURA.search(frase), f"frase rara en {donde}: {frase!r}"
        self.leido = len(reg)

    def al_juego(self, donde):
        """Cierra lo que haya abierto hasta volver a la partida. De todo tiene que poderse salir."""
        app = self.app
        for _ in range(60):
            if app.pila and app.pila[-1] is app.partida:
                return
            cima = app.pila[-1]
            if isinstance(cima, Menu) and not cima.escapable:
                cima.i = len(cima.opciones) - 1
                self.robot.tecla(pygame.K_RETURN)
            elif isinstance(cima, Dialogo):
                self.robot.tecla(pygame.K_ESCAPE)
            else:
                self.robot.tecla(pygame.K_ESCAPE)
            self.robot.frames(1)
        assert app.pila and app.pila[-1] is app.partida, f"no se puede volver al juego desde {donde}"

    def sano(self):
        p = self.p
        j = p.j
        j.salud = j.salud_max
        j.dinero = max(j.dinero, 200000)
        j.hambre = j.sueno = 0.0
        if j.estrellas or j.puntos_busqueda:
            p._fin_persecucion()
            j.estrellas, j.puntos_busqueda = 0, 0.0
        p.transicion = False

    def a_pie(self):
        p = self.p
        if p.j.veh:
            v = p.j.veh
            v.vel = 0.0
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
        if getattr(p, "nadando", False):
            p._fin_agua()

    def ir(self, mapa, x, y):
        p = self.p
        self.a_pie()
        if p.mundo.id != mapa:
            p.cambiar_mapa(mapa, x, y)
        p.j.x, p.j.y = p.mundo.punto_libre(x, y) if p.mundo.tipo != "mar" else (x, y)
        self.robot.frames(2)


def _mapa_de_mar(p):
    return next(m for m in p.mapas.values() if m.tipo == "mar")


def test_todos_los_vehiculos_y_todo_lo_que_se_hace_con_ellos(robot):
    p = robot.nueva_partida()
    t = Total(robot)
    app = robot.app
    p.cfg["sucesos"] = False
    mar = _mapa_de_mar(p)
    taller = next(l for l in p.mapas["puerto_bravo"].lugares.values() if l.tipo == "taller")
    usados, trabajos = set(), set()
    for modelo in list(p.modelos.values()):
        p = app.partida
        j = p.j
        t.sano()
        barco = bool(modelo.get("barco"))
        if barco:
            t.ir(mar.id, mar.ancho / 2, mar.alto / 2 + 100)                  # mar abierto, lejos de islas y de los bordes
        else:
            t.ir("puerto_bravo", taller.x, taller.y)
        x, y = p.pos()
        donde = f"vehículo {modelo['id']}"
        if barco:
            v = p.crear_vehiculo(modelo["id"], x, y, 0, None)
        else:
            px, py, d = p.mundo.plaza_junto_a(taller)
            v = p.crear_vehiculo(modelo["id"], px, py, d, None)
        p._subir(v, False, callar=True)
        robot.frames(3)
        assert j.veh is v and v.canal is not None, donde
        # conducir: acelerar, girar, frenar, y todas las teclas del volante
        x0, y0 = v.x, v.y
        robot.frames(75, mantener=(pygame.K_UP,))
        assert math.hypot(v.x - x0, v.y - y0) > 1.0 or abs(v.vel) > 0.5, f"{donde}: no se mueve"
        robot.frames(15, mantener=(pygame.K_LEFT,))
        robot.frames(15, mantener=(pygame.K_RIGHT,))
        for k in (pygame.K_c, pygame.K_v, pygame.K_w, pygame.K_a, pygame.K_d, pygame.K_s, pygame.K_o, pygame.K_n, pygame.K_t, pygame.K_TAB, pygame.K_F2, pygame.K_F2,
                  pygame.K_p, pygame.K_h, pygame.K_r, pygame.K_u, pygame.K_y, pygame.K_e, pygame.K_F1):
            robot.tecla(k)
            robot.frames(1)
            t.al_juego(f"{donde}, tecla {pygame.key.name(k)}")
        robot.frames(40, mantener=(pygame.K_DOWN,))
        robot.frames(10, mantener=(pygame.K_SPACE,))
        _coherente(p, donde)
        # la radio
        if hasattr(app, "radio"):
            for k in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                robot.tecla(k)
        # trabajar con él, si sirve para eso
        if modelo.get("trabajo"):
            v.vel = 0.0
            p.alternar_trabajo()
            if p.trabajo:
                trabajos.add(p.trabajo["tipo"])
                assert p.objetivo_txt(), donde
                robot.frames(90, mantener=(pygame.K_UP,))
                _coherente(p, donde + ", trabajando")
                p.alternar_trabajo()
                assert p.trabajo is None, donde
        # el taller: reparar, pintar y las tres mejoras al máximo, y que se noten
        if not barco and not modelo.get("vuela"):
            v.vel = 0.0
            v.x, v.y = p.mundo.plaza_junto_a(taller)[:2]
            v.salud = v.salud_max * 0.5
            t.sano()
            menus_juego.lugar(p, taller)
            m = app.pila[-1]
            assert isinstance(m, Menu) and m is not p, f"{donde}: el taller no abre"
            for vuelta in range(14):
                m.refrescar(False)
                pendientes = [k for k, o in enumerate(m.opciones) if o.accion and not o.texto.startswith(("Volver", "Recorrer"))]
                if vuelta >= len(pendientes) * 4:
                    break
                for k in pendientes:
                    if app.pila[-1] is not m:
                        break
                    m.i = k
                    robot.tecla(pygame.K_RETURN)
                    while app.pila[-1] is not m and app.pila[-1] is not app.partida:
                        robot.tecla(pygame.K_ESCAPE)
                if app.pila[-1] is not m:
                    break
            assert v.salud >= v.salud_max * 0.99, f"{donde}: el taller no repara"
            assert all(sistemas.nivel(v, cual) == 3 for cual in ("motor", "frenos", "blindaje")), (donde, getattr(v, "mejoras", None))
            assert sistemas.factor_velocidad(v) > 1.0 and sistemas.factor_frenada(v) > 1.0
            t.al_juego(donde + ", taller")
            t.suma("talleres")
        # bajarse y volver a subir con la tecla
        if j.veh is v and not barco and not modelo.get("vuela"):
            v.vel = 0.0
            robot.tecla(pygame.K_f)
            robot.frames(2)
            assert j.veh is None, f"{donde}: no deja bajar"
            robot.tecla(pygame.K_f)
            robot.frames(30)
            t.al_juego(donde + ", al subir")
        t.voz(donde)
        usados.add(modelo["id"])
        t.a_pie()
    assert usados == set(p.modelos) and len(usados) >= 38, sorted(set(p.modelos) - usados)
    assert {"taxi", "ambulancia", "autobus"} <= trabajos and len(trabajos) >= 6, trabajos
    assert t.cuenta["talleres"] >= 25


def test_todas_las_armas_y_todos_los_objetos(robot):
    from juego.entidades import Persona
    p = robot.nueva_partida()
    t = Total(robot)
    app = robot.app
    j = p.j
    p.cfg["sucesos"] = False
    p.cfg["sin_policia"] = True
    plaza = p.lugares["plaza_vieja"]
    t.ir("puerto_bravo", plaza.x, plaza.y)
    for a in p.datos["armas"]:
        t.sano()
        donde = f"arma {a['id']}"
        p.dar_arma(a["id"], 60)
        j.arma = a["id"]
        lejos = 28 if a["tipo"] == "explosivo" else max(1.2, min(a["alcance"] * 0.5, 9))
        e = Persona("enemigo", j.x + lejos, j.y, "Muñeco")
        e.hostil, e.inofensivo, e.salud, e.tag, e.estado = True, True, 100000.0, "mision", "ataca"
        p.personas.append(e)
        p.fijar()
        for _ in range(8):
            j.t_ataque = 0.0
            if a["tipo"] in ("fuego", "explosivo") and j.armas[a["id"]]["cargador"] <= 0:
                p.recargar()
                j.t_ataque = 0.0
            p.atacar()
            robot.frames(4)
        if a["tipo"] == "fuego":
            j.armas[a["id"]]["cargador"] = 0
            j.t_ataque = 0.0
            p.recargar()
            assert j.armas[a["id"]]["cargador"] == p.capacidad(a["id"]) or j.armas[a["id"]]["reserva"] == 0, donde
        robot.tecla(pygame.K_v)
        robot.tecla(pygame.K_i)
        t.al_juego(donde)
        p.personas[:] = [x for x in p.personas if x is not e]
        p.objetivo = None
        robot.frames(40)
        _coherente(p, donde)
        t.voz(donde)
        t.suma("armas")
    assert t.cuenta["armas"] == len(p.datos["armas"]) >= 20
    # elegir arma con los números y con la coma
    for k in list(range(pygame.K_1, pygame.K_9 + 1)) + [pygame.K_COMMA, pygame.K_COMMA]:
        robot.tecla(k)
    # las mejoras de armas en la armería, todas
    arm = p.lugares["armeria_centro"]
    t.ir("puerto_bravo", arm.x, arm.y)
    t.sano()
    menus_juego._armeria(p, arm)
    m = app.pila[-1]
    for _ in range(60):
        m.refrescar(False)
        k = next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Silenciador para", "Cargador ampliado para"))), None)
        if k is None:
            break
        m.i = k
        robot.tecla(pygame.K_RETURN)
        t.sano()
    assert not any(o.texto.startswith(("Silenciador para", "Cargador ampliado para")) for o in m.opciones)
    assert sum(1 for x in j.armas.values() if x.get("ampliado")) >= 8 and sum(1 for x in j.armas.values() if x.get("silenciador")) >= 5
    t.al_juego("armería")
    # los objetos: comprarlos todos y usarlos
    for o in p.datos["objetos"]:
        t.sano()
        op = menus_juego._comprar_objeto(p, o["id"])
        if o["id"] == "chaleco":
            j.blindaje = 0.0
        op.accion()
        t.suma("objetos")
    j.salud = 20.0
    antes = j.objetos.get("botiquin", 0)
    p.usar_botiquin()
    assert j.salud > 20.0 and j.objetos.get("botiquin", 0) == antes - 1 and j.blindaje == 100.0
    # tiempo lento, cobertura, agacharse, correr
    robot.tecla(pygame.K_BACKSPACE)
    robot.frames(20)
    robot.tecla(pygame.K_BACKSPACE)
    robot.tecla(pygame.K_x)
    robot.frames(10, mantener=(pygame.K_UP,))
    robot.tecla(pygame.K_x)
    robot.tecla(pygame.K_x, mod=pygame.KMOD_LSHIFT)
    robot.frames(5)
    p.dejar_cobertura(hablar=False)
    j.agachado = False
    robot.frames(20, mantener=(pygame.K_UP, pygame.K_LSHIFT))
    t.voz("objetos y movimientos")
    _coherente(p, "armas y objetos")
    p.cfg["sin_policia"] = False


def test_todos_los_interiores_sala_por_sala(robot):
    app = robot.app
    app.cfg["adultos"] = True
    app.aplicar_adultos()
    try:
        p = robot.nueva_partida()
        t = Total(robot)
        p.cfg["sucesos"] = False
        tipos, salas, casas = set(), 0, 0
        for mapa in list(p.mapas.values()):
            for l in list(mapa.lugares.values()):
                p = app.partida
                if sistemas.salas_de(l) is None and l.tipo != "casa":
                    continue
                t.sano()
                t.ir(l.mapa, l.x, l.y)
                donde = f"interior de {l.nombre} ({l.tipo})"
                if l.tipo == "casa":
                    if l.id not in p.j.propiedades:
                        p.j.propiedades.append(l.id)
                    pantalla = sistemas.Interior(p, l, {"descansar": lambda: None, "garaje": lambda: None})
                    casas += 1
                else:
                    pantalla = sistemas.Local(p, l)
                app.abrir(pantalla)
                robot.tecla(pygame.K_LEFT)                                    # la pared de un extremo
                assert "Pared" in app.voz.registro[-1], donde
                for n in range(len(pantalla.habitaciones)):
                    if app.pila[-1] is not pantalla:
                        app.abrir(pantalla) if pantalla not in app.pila else None
                    pantalla.i = n
                    robot.tecla(pygame.K_F1)
                    nombre, desc, que = pantalla.habitaciones[n]
                    assert nombre.strip() and desc.strip(), donde
                    if que in ("salir", "mostrador"):
                        continue                                              # esas cierran; se prueban al final
                    robot.tecla(pygame.K_RETURN)
                    robot.frames(1)
                    for _ in range(30):                                       # lo que abra la sala (una ficha, la tragaperras), se cierra
                        if app.pila[-1] is pantalla or pantalla not in app.pila:
                            break
                        c = app.pila[-1]
                        if isinstance(c, Menu) and not c.escapable:
                            c.i = len(c.opciones) - 1
                            robot.tecla(pygame.K_RETURN)
                        else:
                            robot.tecla(pygame.K_ESCAPE)
                    salas += 1
                if pantalla in app.pila:
                    while app.pila[-1] is not pantalla:
                        robot.tecla(pygame.K_ESCAPE)
                    pantalla.i = len(pantalla.habitaciones) - 1
                    robot.tecla(pygame.K_RIGHT)                               # la pared del otro extremo
                    pantalla.i = 0
                    robot.tecla(pygame.K_RETURN)                              # la puerta: salir
                    assert pantalla not in app.pila, f"{donde}: la puerta no saca"
                t.al_juego(donde)
                t.voz(donde)
                tipos.add(l.tipo)
        assert set(sistemas.SALAS) <= tipos | {"proveedor", "club"} or len(tipos) >= 25, sorted(set(sistemas.SALAS) - tipos)
        assert salas > 400 and casas >= 7, (salas, casas)
    finally:
        app.cfg["adultos"] = False
        app.aplicar_adultos()


def test_mar_aire_y_agua(robot):
    p = robot.nueva_partida()
    t = Total(robot)
    app = robot.app
    j = p.j
    p.cfg["sucesos"] = False
    mar = _mapa_de_mar(p)
    # todos los muelles: llegar en barco y atracar; todos los embarcaderos: zarpar
    muelles = [l for l in mar.lugares.values() if l.get("a_mapa") in p.mapas and p.lug(l.get("a_lugar"))]
    assert len(muelles) >= 3
    for l in muelles:
        p = app.partida
        t.sano()
        bx, by = mar.punto_libre(l.x + 30, l.y - 60)
        t.ir(mar.id, bx, by)
        v = p.crear_vehiculo("lancha", bx, by, 0, None)
        p._subir(v, False, callar=True)
        robot.frames(40, mantener=(pygame.K_UP,))
        robot.tecla(pygame.K_p)                                               # pescar
        robot.frames(30)
        robot.tecla(pygame.K_SPACE)
        robot.frames(10)
        t.al_juego(f"pesca junto a {l.nombre}")
        v.x, v.y, v.vel = l.x, l.y, 0.0
        robot.frames(3)
        menus_juego.lugar(p, l)
        m = app.pila[-1]
        if isinstance(m, Menu) and m is not p:
            m.i = 0
            robot.tecla(pygame.K_RETURN)
            robot.frames(3)
        t.al_juego(f"muelle {l.nombre}")
        t.voz(f"muelle {l.nombre}")
        _coherente(app.partida, f"muelle {l.nombre}")
        t.suma("muelles")
    # nadar y bucear en mitad del mar, hasta encontrar algo
    p = app.partida
    j = p.j
    t.ir(mar.id, mar.ancho / 2 - 300, mar.alto / 2 + 150)
    robot.frames(3)
    assert p.nadando
    encontrado = j.stats.get("buceo", 0)
    random.seed(4)
    for _ in range(12):
        p.aguante = 100.0
        robot.tecla(pygame.K_x)
        robot.frames(30 * 20, mantener=(pygame.K_RIGHT,))
        if p.buceando:
            robot.tecla(pygame.K_x)
        robot.frames(30 * 8)
        if j.stats.get("buceo", 0) > encontrado:
            break
    assert j.stats.get("buceo", 0) > encontrado and j.stats.get("metros_nadando", 0) > 15
    t.voz("nadar y bucear")
    # el aire: helicóptero y avioneta, despegar, volar sobre los edificios, y cambiar de localidad desde un helipuerto
    heli = next(l for l in p.mapas["puerto_bravo"].lugares.values() if l.tipo == "helipuerto")
    for modelo in ("helicoptero", "avioneta"):
        p = app.partida
        t.sano()
        t.ir("puerto_bravo", heli.x, heli.y)
        v = p.crear_vehiculo(modelo, heli.x, heli.y, 0, None)
        p._subir(v, False, callar=True)
        x0, y0 = v.x, v.y
        robot.frames(150, mantener=(pygame.K_UP,))
        robot.frames(40, mantener=(pygame.K_UP, pygame.K_RIGHT))
        assert math.hypot(v.x - x0, v.y - y0) > 60 and app.mez.altura > 0, modelo
        for k in (pygame.K_c, pygame.K_v, pygame.K_n, pygame.K_TAB):
            robot.tecla(k)
        v.x, v.y, v.vel = heli.x, heli.y, 0.0
        robot.frames(3)
        menus_juego.lugar(p, heli)
        m = app.pila[-1]
        assert isinstance(m, Menu) and m is not p and "vuelo es gratis" in " ".join(app.voz.registro[-3:]), modelo
        m.i = 0
        robot.tecla(pygame.K_RETURN)
        robot.frames(5)
        t.al_juego(f"vuelo en {modelo}")
        assert app.partida.mundo.id != "puerto_bravo", modelo
        t.voz(f"vuelo en {modelo}")
        _coherente(app.partida, f"vuelo en {modelo}")
    # y de pasajero, con trayecto
    p = app.partida
    t.a_pie()
    t.sano()
    t.ir("puerto_bravo", heli.x, heli.y)
    app.viajes_en_pruebas = True
    menus_juego.lugar(p, heli)
    m = app.pila[-1]
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    robot.frames(30 * 36)
    app.viajes_en_pruebas = False
    t.al_juego("vuelo de pasajero")
    assert app.partida.mundo.id != "puerto_bravo"
    assert t.cuenta["muelles"] == len(muelles)


def test_todos_los_juegos_de_mesa_hasta_el_final(robot):
    p = robot.nueva_partida()
    t = Total(robot)
    app = robot.app
    j = p.j
    azar = random.Random(11)
    resultados = {"domino": set(), "chinos": set(), "siete": set()}
    for ronda in range(25):
        j.dinero = 5000
        m, est = mesa.domino(p, Menu, Opcion, azar=azar)
        m.i = ronda % 2
        robot.tecla(pygame.K_RETURN)
        for _ in range(150):
            if est["fin"]:
                break
            m.refrescar(False)
            ks = [k for k, o in enumerate(m.opciones) if o.texto.startswith(("Poner el", "Robar una ficha"))]
            assert ks, "dominó sin jugada posible"
            m.i = azar.choice(ks)
            robot.tecla(pygame.K_RETURN)
        assert est["fin"]
        resultados["domino"].add("gana" if j.dinero > 5000 else "pierde" if j.dinero < 5000 else "empata")
        app.cerrar(m)
        j.dinero = 5000
        m, est = mesa.chinos(p, Menu, Opcion, azar=azar)
        for _ in range(40):
            m.refrescar(False)
            m.i = azar.randrange(len(m.opciones) - (1 if est["fase"] == "apuesta" else 0))
            robot.tecla(pygame.K_RETURN)
            if est["fase"] == "apuesta" and j.dinero != 5000:
                break
        resultados["chinos"].add("gana" if j.dinero > 5000 else "pierde")
        app.cerrar(m)
        j.dinero = 5000
        m, est = sistemas.siete_y_media(p, Menu, Opcion, azar=azar)
        m.i = ronda % 3
        robot.tecla(pygame.K_RETURN)
        for _ in range(12):
            if est["fin"]:
                break
            m.refrescar(False)
            m.i = 0 if est["mias"] < 5 else 1
            robot.tecla(pygame.K_RETURN)
        assert est["fin"]
        resultados["siete"].add("gana" if j.dinero > 5000 else "pierde")
        app.cerrar(m)
        t.voz(f"juegos de mesa, ronda {ronda}")
    assert resultados["domino"] >= {"gana", "pierde"} and resultados["chinos"] == {"gana", "pierde"} and resultados["siete"] == {"gana", "pierde"}, resultados
    # el casino entero y la feria, pulsándolo todo varias veces
    for tipo in ("casino", "feria", "loteria", "gimnasio", "taberna", "bar"):
        l = next(x for x in p.mapas["puerto_bravo"].lugares.values() if x.tipo == tipo)
        t.ir("puerto_bravo", l.x, l.y)
        for vuelta in range(3):
            t.sano()
            menus_juego.lugar(p, l)
            base = app.pila[-1]
            if not isinstance(base, Menu) or base is p:
                break
            n = len(base.opciones)
            for k in range(n):
                if app.pila[-1] is not base:
                    break
                base.refrescar(False)
                if k >= len(base.opciones) or base.opciones[k].texto.startswith(("Volver", "Salir")):
                    continue
                base.i = k
                robot.tecla(pygame.K_RETURN)
                robot.frames(2)
                for _ in range(8):                                            # dentro de cada juego, unas cuantas jugadas
                    c = app.pila[-1]
                    if c is base or c is app.partida or not isinstance(c, Menu):
                        break
                    c.refrescar(False)
                    c.i = azar.randrange(max(1, len(c.opciones) - 1))
                    robot.tecla(pygame.K_RETURN)
                    robot.frames(3, mantener=(pygame.K_LEFT,))
                    t.sano()
                for _ in range(40):
                    c = app.pila[-1]
                    if c is base or c is app.partida:
                        break
                    if isinstance(c, Menu) and not c.escapable:
                        c.i = len(c.opciones) - 1
                        robot.tecla(pygame.K_RETURN)
                    else:
                        robot.tecla(pygame.K_ESCAPE)
                    robot.frames(2)
            t.al_juego(f"{tipo}, vuelta {vuelta}")
            t.voz(f"{tipo}, vuelta {vuelta}")
            _coherente(app.partida, tipo)
            t.suma("locales_de_juego")
    assert t.cuenta["locales_de_juego"] >= 12


def test_las_tres_ramas_de_la_historia(robot):
    """Se juega la decisión del concejal de las tres maneras, y la misión final de cada una, hasta su final."""
    import test_misiones
    app = robot.app
    finales = set()
    for opcion in range(3):
        while app.pila and len(app.pila) > 1:
            app.cerrar(app.pila[-1])
        if app.partida is not None:
            app.volver_al_menu()
        p = robot.nueva_partida()
        p.cfg["sucesos"] = False
        por_id = {m["id"]: m for m in p.datos["misiones"]}
        p.completadas.append("eo6")
        fd1 = por_id["fd1"]
        l = p.lugares[fd1["lugar"]]
        p.teletransportar(l.x, l.y)
        p.iniciar_mision(fd1)
        for _ in range(12):
            if isinstance(app.pila[-1], Dialogo):
                robot.tecla(pygame.K_ESCAPE)
        menu = app.pila[-1]
        assert isinstance(menu, Menu) and len(menu.opciones) == 3
        robot.tecla(pygame.K_F1)                                              # la explicación de la opción
        menu.i = opcion
        robot.tecla(pygame.K_RETURN)
        robot.saltar_dialogos()
        assert p.decisiones["concejal"]["opcion"] == opcion + 1 and "fd1" in p.completadas
        final = por_id[f"fd{opcion + 2}"]
        assert [m["id"] for m in p.misiones_disponibles() if m["id"].startswith("fd")] == [final["id"]]
        p.j.dinero += 5000
        p.dar_arma("fusil", 400)
        test_misiones._jugar_mision(robot, final)
        assert final["id"] in p.completadas and p.decisiones["_final"]["texto"] == final["final_titulo"]
        assert "Final de la historia" in " ".join(app.voz.registro[-25:])
        finales.add(p.decisiones["_final"]["texto"])
        d = p.a_dict()                                                        # y se guarda y se carga con su final
        app.empezar_partida(d)
        assert app.partida.decisiones["_final"]["texto"] == final["final_titulo"]
    assert len(finales) == 3


def test_muchos_dias_con_barrios_banda_y_sucesos(robot):
    """Cuarenta días seguidos con territorios, banda, sucesos, laboratorio no, y todo lo que pasa a medianoche."""
    p = robot.nueva_partida()
    t = Total(robot)
    app = robot.app
    j = p.j
    p.cfg["sucesos"] = True
    random.seed(21)
    for b in p.mundo.barrios[:4]:
        j.territorios.append(b["id"])
    j.banda, j.banda_nombre = 3, "Los del Muelle"
    vistos = set()
    for dia in range(40):
        p = app.partida
        j = p.j
        t.sano()
        p.pasar_horas(24)
        robot.frames(20)
        t.al_juego(f"día {dia}")
        if j.amenaza:
            vistos.add("ataque")
            if dia % 2 == 0:                                                  # la mitad de las veces se defiende
                mapa = next(m for m in p.mapas.values() if any(b["id"] == j.amenaza["territorio"] for b in m.barrios))
                if p.mundo.id != mapa.id:
                    l0 = next(iter(mapa.lugares.values()))
                    p.cambiar_mapa(mapa.id, l0.x, l0.y)
                sistemas.defender(p)
                if p.mision:
                    for e in list(p.personas):
                        pass
                    p.mision["paso"] = len(p.mision["def"]["pasos"]) - 1
                    p._siguiente_paso()
                    assert j.amenaza is None
        if j.oferta_pacto:
            vistos.add("pacto")
            ops = sistemas.opciones_sucesos(p, Menu, Opcion)
            ops[0].accion()
            c = app.pila[-1]
            c.i = dia % 2
            robot.tecla(pygame.K_RETURN)
            t.al_juego("pacto")
        if j.redada:
            vistos.add("policia")
            if dia % 2:
                next(o for o in sistemas.opciones_sucesos(p, Menu, Opcion) if o.texto.startswith("Arreglar")).accion()
        if not j.territorios:
            j.territorios.append(p.mapas["puerto_bravo"].barrios[0]["id"])
        if j.banda < 2:
            j.banda = 3
        for banda, x in j.rep_bandas.items():
            assert -100 <= x <= 100, (banda, x)
        _coherente(p, f"día {dia}")
        t.voz(f"día {dia}")
    assert p.dia >= 40 and vistos >= {"ataque", "policia"}, vistos
    d = p.a_dict()
    app.empezar_partida(d)
    q = app.partida
    assert q.dia == p.dia and q.j.territorios == j.territorios and q.j.banda == j.banda and q.j.rep_bandas == j.rep_bandas
