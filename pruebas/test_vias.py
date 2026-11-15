"""Las vías del tranvía y lo que circula por ellas, y la comprobación a pie de todas las paradas, estaciones y aeropuertos."""
import math

import pygame

from juego import menus_juego, mundo as M, transporte
from juego.menus import Menu


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


def test_las_vias_estan_bien_tendidas(robot):
    p = robot.nueva_partida()
    for m in p.mapas.values():
        if m.tipo == "mar":
            continue
        linea = m.linea_tranvia()
        if m.tipo != "ciudad":
            assert not m.vias and m.via_largo == 0 and not m.en_via(50, 0), m.id        # en los pueblos y las islas no hay vías
            continue
        assert len(linea) >= len(m.barrios) and m.via_largo > 1500 and len(m.vias) >= 20, m.id
        # el circuito es continuo, va siempre por el centro de la calzada y se cierra sobre sí mismo
        anterior = m.via_punto(0)
        for s in range(2, int(m.via_largo) + 3, 2):
            x, y = m.via_punto(s)
            assert math.hypot(x - anterior[0], y - anterior[1]) < 2.5, (m.id, s)
            assert m.en_via(x, y) and m.superficie(x, y) == "calzada", (m.id, s)
            anterior = (x, y)
        assert math.hypot(anterior[0] - m.via_punto(0)[0], anterior[1] - m.via_punto(0)[1]) < 3, m.id
        # cada parada tiene su punto de vía cerca, y la acera no es vía
        for l in linea:
            s = m.via_marca(l)
            assert s is not None and math.hypot(m.via_punto(s)[0] - l.x, m.via_punto(s)[1] - l.y) < 45, l.id
            assert not m.en_via(l.x, l.y) and m.superficie(l.x, l.y) == "acera", l.id
        # las vías tienen anchura: metro y medio a cada lado del eje, y no más
        x, y = m.via_punto(40)
        horizontal = abs(m.via_punto(41)[0] - x) > 0.5
        lado = (0, 1) if horizontal else (1, 0)
        assert m.en_via(x + lado[0] * 1.2, y + lado[1] * 1.2) and not m.en_via(x + lado[0] * 3, y + lado[1] * 3), m.id
        ax, ay = m.fuera_de_la_via(x, y)
        assert m.superficie(ax, ay) == "acera" and not m.en_via(ax, ay), m.id
    assert M.SUPERFICIE_TXT["via"] == "vías del tranvía"


def test_cruzar_las_vias_a_pie(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    m = p.mundo
    p.cfg["anunciar_superficie"] = True
    p.tranvias = []
    p._transporte_mapa = m.id                                 # sin tranvías, para cruzar tranquilo
    x, y = m.via_punto(40)
    horizontal = abs(m.via_punto(41)[0] - x) > 0.5
    # desde la acera, cruzando la calle de lado a lado
    j.x, j.y = (x, y - 8.0) if horizontal else (x - 8.0, y)
    robot.frames(3)
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append(n), original(n, **k))[1]
    n0 = len(app.voz.registro)
    robot.frames(230, mantener=(pygame.K_UP if horizontal else pygame.K_RIGHT,))             # unos veinte metros: de acera a acera
    p.son = original
    dicho = app.voz.registro[n0:]
    orden = [f for f in dicho if f in ("Calzada.", "Vías del tranvía.", "Acera.")]
    assert orden[:4] == ["Calzada.", "Vías del tranvía.", "Calzada.", "Acera."], orden          # se avisa al entrar y al salir de las vías
    pasos = [s for s in sonidos if s.startswith("paso_")]
    assert any(s.startswith("paso_via") for s in pasos) and any(s.startswith("paso_calzada") for s in pasos) and any(s.startswith("paso_acera") for s in pasos), pasos
    assert "paso_via0" in app.mez.sonidos and "paso_via1" in app.mez.sonidos
    # en coche no se anuncia nada al pasar por encima
    v = p.crear_vehiculo("sedan", x, y, 0, None)
    p._subir(v, False, callar=True)
    n0 = len(app.voz.registro)
    robot.frames(10)
    assert "Vías del tranvía." not in app.voz.registro[n0:]


def test_el_tranvia_circula_y_se_oye_desde_la_calle(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    m = p.mundo
    p.cfg["sucesos"] = False
    robot.frames(2)
    assert len(p.tranvias) == 3 and p._transporte_mapa == m.id                # tres tranvías repartidos por los cuatro kilómetros de línea
    separacion = sorted(t["s"] for t in p.tranvias)
    assert separacion[1] - separacion[0] > 1000
    # avanza por la vía, para en cada parada y toca la campana
    t = p.tranvias[0]
    marca = m.via_marcas[1]
    t["s"] = marca - 30.0
    t["espera"] = 0.0
    px, py = m.via_punto(marca - 10)
    lado = m.fuera_de_la_via(px, py)
    j.x, j.y = lado                                                           # en la acera, viéndolo venir
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append((n, k.get("xy"))), original(n, **k))[1]
    robot.frames(15)
    assert t["canal"] is not None and t["canal"].nombre == "tranvia" and t["canal"].xy is not None
    x1 = t["canal"].xy
    robot.frames(30)
    assert t["canal"].xy != x1                                                # el sonido se mueve con él
    robot.frames(30 * 4)
    assert abs(t["s"] - marca) < 0.01 and t["espera"] > 0                     # parado en la parada
    assert any(n == "tranvia_campana" and xy is not None for n, xy in sonidos)
    salud = j.salud
    robot.frames(30 * 6)
    assert t["s"] > marca and j.salud == salud                                # ha arrancado otra vez, y en la acera no te pasa nada
    p.son = original
    # lejos no se oye: el canal se suelta
    j.x, j.y = m.punto_libre(*m.via_punto(t["s"] + m.via_largo / 2))
    for otro in p.tranvias:
        otro["s"] = t["s"] + 5 * (otro["numero"])
    robot.frames(5)
    assert all(o["canal"] is None for o in p.tranvias)
    # en medio de la vía con el tranvía viniendo: campana y aviso; si no te apartas, te arrolla y te saca
    t["s"] = marca + 200.0
    t["espera"] = 0.0
    for otro in p.tranvias[1:]:
        otro["s"] = t["s"] + m.via_largo / 2
    j.x, j.y = m.via_punto(t["s"] + 40.0)
    assert m.en_via(j.x, j.y)
    n0 = len(app.voz.registro)
    campanas = []
    p.son = lambda n, **k: (campanas.append(n), original(n, **k))[1]
    robot.frames(60)
    assert any("¡Viene el tranvía" in f for f in app.voz.registro[n0:]) and campanas.count("tranvia_campana") >= 2
    j.salud = salud = 100.0
    robot.frames(30 * 5)
    p.son = original
    assert j.salud < salud and not m.en_via(j.x, j.y) and any("Te ha arrollado el tranvía" in f for f in app.voz.registro[n0:])
    assert m.superficie(j.x, j.y) == "acera"
    # si te apartas a tiempo, no pasa nada
    t["s"] = marca + 600.0
    t["espera"] = 0.0
    j.x, j.y = m.via_punto(t["s"] + 40.0)
    j.salud = 100.0
    robot.frames(30)
    j.x, j.y = m.fuera_de_la_via(j.x, j.y)
    robot.frames(30 * 5)
    assert j.salud == 100.0
    # al cambiar de localidad, los tranvías de la anterior se callan y salen los de la nueva; en un pueblo, ninguno
    l = p.mapas["san_lucero"].lugares["sl_fuente"]
    p.cambiar_mapa("san_lucero", l.x, l.y)
    robot.frames(2)
    assert p._transporte_mapa == "san_lucero" and len(p.tranvias) >= 1 and all(o["s"] < p.mundo.via_largo for o in p.tranvias)
    l = p.mapas["villaseca"].lugares["vs_fuente"]
    p.cambiar_mapa("villaseca", l.x, l.y)
    robot.frames(2)
    assert p.tranvias == []


def test_subir_al_tranvia_que_circula(robot):
    from juego import menus_lugares as ml
    p = robot.nueva_partida()
    app = robot.app
    m = p.mundo
    robot.frames(2)
    linea = ml.linea_tranvia(p)
    a = linea[0]
    p.teletransportar(a.x, a.y)
    menus_juego.lugar(p, a)
    menu = app.pila[-1]
    menu.i = 2
    destino = menu.opciones[2].texto.split("Ir a ")[1].split(":")[0]
    robot.tecla(pygame.K_RETURN)
    final = next(x for x in linea if x.nombre.endswith(destino))
    assert app.pila[-1] is p and math.hypot(p.j.x - final.x, p.j.y - final.y) < 3
    cerca = min(p.tranvias, key=lambda t: abs(t["s"] - m.via_marca(final)))
    assert abs(cerca["s"] - m.via_marca(final)) < 0.01 and not any(t["a_bordo"] for t in p.tranvias)       # tu tranvía está en la parada donde bajas
    robot.frames(30 * 6)
    assert cerca["s"] > m.via_marca(final)                                    # y sigue su camino


def test_tren_y_avion_se_oyen_desde_la_calle(robot):
    p = robot.nueva_partida()
    robot.frames(2)
    est = p.lugares["puerto_bravo_tren"]
    aer = p.lugares["puerto_bravo_aeropuerto"]
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append((n, k.get("xy"))), original(n, **k))[1]
    p.j.x, p.j.y = p.mundo.punto_libre(est.x + 20, est.y)
    p.t_tren = 0.01
    robot.frames(3)
    assert ("tren_silbato", (est.x, est.y)) in sonidos and ("tren", (est.x, est.y)) in sonidos and len(p._sonidos_transporte) == 1
    robot.frames(30 * 10)
    assert p._sonidos_transporte == []                                        # el tren pasa y se va
    p.j.x, p.j.y = p.mundo.punto_libre(aer.x + 30, aer.y)
    p.t_avion = 0.01
    robot.frames(3)
    assert ("avion_despegue", (aer.x, aer.y)) in sonidos
    # lejos de la estación no suena nada
    sonidos.clear()
    lejos = max(p.mundo.lugares.values(), key=lambda l: math.hypot(l.x - est.x, l.y - est.y))
    p.j.x, p.j.y = lejos.x, lejos.y
    assert math.hypot(lejos.x - est.x, lejos.y - est.y) > 260
    p.t_tren = 0.01
    robot.frames(3)
    p.son = original
    assert not any(n == "tren_silbato" for n, _ in sonidos)


def test_recorrer_a_pie_todas_las_paradas_estaciones_y_aeropuertos(robot):
    """Verificación de verdad: en cada localidad, también en las de los mods, se va andando con el GPS hasta cada parada de
    tranvía, cada estación de tren y cada aeropuerto; se comprueba que se llega, que el juego lo anuncia y que se abre."""
    p = robot.nueva_partida()
    app = robot.app
    p.cfg["sucesos"] = False
    p.cfg["anunciar_lugares"] = True
    visitados = {"tranvia": 0, "tren": 0, "aeropuerto": 0}
    metros = 0.0
    for mapa in list(p.mapas.values()):
        if mapa.tipo == "mar":
            continue
        destinos = [l for l in mapa.lugares.values() if l.tipo in ("tranvia", "tren", "aeropuerto")]
        if not destinos:
            continue
        salida = next(iter(mapa.lugares.values()))
        p.cambiar_mapa(mapa.id, salida.x, salida.y)
        p.tranvias = []                                                       # sin tranvías circulando: aquí se prueba el camino
        p._transporte_mapa = mapa.id
        for l in sorted(destinos, key=lambda l: (l.tipo, l.id)):
            p = app.partida
            j = p.j
            j.salud = j.salud_max
            j.estrellas, j.puntos_busqueda = 0, 0.0
            j.hambre = j.sueno = 0.0
            # se empieza en la esquina de un cruce a dos manzanas, para que haya que andar, doblar y cruzar
            ci = int(round(l.x / M.B)) + (-2 if l.x > mapa.ancho / 2 else 2)
            cj = int(round(l.y / M.B)) + (-1 if l.y > mapa.alto / 2 else 1)
            ci, cj = max(0, min(mapa.NX - 1, ci)), max(0, min(mapa.NY - 1, cj))
            ox = ci * M.B + (7.5 if ci < mapa.NX - 1 else -7.5)
            oy = cj * M.B + (7.5 if cj < mapa.NY - 1 else -7.5)
            assert mapa.superficie(ox, oy) == "acera", (l.id, ox, oy)
            p.teletransportar(ox, oy)
            robot.frames(2)
            _al_juego(app)
            inicio = math.hypot(l.x - ox, l.y - oy)
            assert inicio > 60, l.id
            ruta = mapa.ruta(ox, oy, l.x, l.y)
            assert ruta and math.hypot(ruta[-1][0] - l.x, ruta[-1][1] - l.y) < 2, l.id            # el GPS sabe llegar hasta su puerta
            p.gps_a_lugar(l)
            assert p.gps is not None, l.id
            p.alternar_paseo()
            n0 = len(app.voz.registro)
            for _ in range(600):
                robot.frames(10)
                if app.pila[-1] is not p:
                    _al_juego(app)
                if math.hypot(j.x - l.x, j.y - l.y) < 2.5 or not getattr(p, "paseo_auto", False):
                    break                                                     # el paseo te deja en la puerta
            llegada = math.hypot(j.x - l.x, j.y - l.y)
            assert llegada < 9, f"{l.id}: el paseo se queda a {llegada:.0f} metros. {app.voz.registro[-3:]}"
            metros += inicio
            robot.frames(15)
            assert p.lugar_cercano(16) is l, l.id                             # es el lugar que tienes delante
            assert any(l.nombre in f for f in app.voz.registro[n0:]), f"{l.id}: no se anuncia al llegar"
            assert mapa.superficie(j.x, j.y) in ("acera", "plaza", "hierba", "arena", "muelle"), (l.id, mapa.superficie(j.x, j.y))
            # y con Intro se abre lo que toca
            p.parar_paseo()
            robot.tecla(pygame.K_RETURN)
            menu = app.pila[-1]
            assert isinstance(menu, Menu) and menu is not p and l.nombre in menu.titulo, l.id
            esperado = {"tranvia": "Ir a ", "tren": "Tren a ", "aeropuerto": "Vuelo a "}[l.tipo]
            assert any(o.texto.startswith(esperado) for o in menu.opciones), (l.id, [o.texto for o in menu.opciones][:3])
            _al_juego(app)
            # está en la lista de lugares y en el radar
            assert l.id in p.lugares and l in [x for x in p.mundo.lugares.values()]
            visitados[l.tipo] += 1
    assert visitados == {"tranvia": 44, "tren": 10, "aeropuerto": 4}, visitados
    assert metros > 6000


def test_el_transporte_esta_escrito_en_los_datos_y_se_puede_editar(robot):
    """Paradas, estaciones, aeropuertos y vías están en los archivos de datos, lugar a lugar, y cambiarlos cambia el juego."""
    import glob
    import json
    import os
    from juego import rutas
    # en los datos del juego base
    for ruta in [os.path.join(rutas.DATOS, "ciudad.json")] + sorted(glob.glob(os.path.join(rutas.DATOS, "mapas", "*.json"))):
        c = json.load(open(ruta, encoding="utf-8"))
        if c.get("tipo") == "mar":
            continue
        antes = json.dumps(c, sort_keys=True)
        tipos = [l["tipo"] for l in c["lugares"]]
        if c.get("tipo", "ciudad") == "ciudad":
            assert tipos.count("tranvia") >= len(c["barrios"]) and tipos.count("aeropuerto") == 1 and len(c["vias"]) >= 4, ruta
            ordenes = sorted(l["orden"] for l in c["lugares"] if l["tipo"] == "tranvia")
            assert ordenes == list(range(1, len(ordenes) + 1)), ruta
        if "salida" in tipos:
            assert tipos.count("tren") == 1, ruta
        M.completar_transporte(c)
        assert json.dumps(c, sort_keys=True) == antes, f"{ruta}: al cargarlo, el juego todavía le añade cosas"      # no queda nada por poner
    # y en los mods
    for ruta in sorted(glob.glob(os.path.join(rutas.MODS, "*.json"))):
        d = json.load(open(ruta, encoding="utf-8"))
        for c in d.get("mapas", []):
            if c.get("tipo") == "mar":
                continue
            lugares = c.get("lugares", []) + [l for l in d.get("lugares", []) if l.get("mapa") == c["id"]]
            tipos = [l["tipo"] for l in lugares]
            if c.get("tipo", "ciudad") == "ciudad":
                assert tipos.count("tranvia") >= len(c["barrios"]) and tipos.count("aeropuerto") == 1 and len(c["vias"]) >= 4, (ruta, c["id"])
            assert tipos.count("tren") == (1 if "salida" in tipos else 0), (ruta, c["id"])
    # editar: cambiar el orden, cambiar las vías y quitar paradas se nota en el juego
    c = json.load(open(os.path.join(rutas.DATOS, "mapas", "san_lucero.json"), encoding="utf-8"))
    original = M.Mundo(json.loads(json.dumps(c)))
    paradas = [l for l in c["lugares"] if l["tipo"] == "tranvia"]
    a, b = paradas[0], paradas[1]
    a["orden"], b["orden"] = b["orden"], a["orden"]
    cambiado = M.Mundo(json.loads(json.dumps(c)))
    assert [l.id for l in cambiado.linea_tranvia()] != [l.id for l in original.linea_tranvia()]
    c["vias"] = [[0, 0], [3, 0], [3, 3], [0, 3]]                              # vías nuevas: un cuadrado
    cuadrado = M.Mundo(json.loads(json.dumps(c)))
    assert cuadrado.via_largo == 12 * M.B and cuadrado.vias != original.vias and len(cuadrado.esquinas_de_las_vias()) == 4
    assert cuadrado.en_via(1.5 * M.B, 0) and not cuadrado.en_via(1.5 * M.B, 2 * M.B)
    for l in cuadrado.linea_tranvia():
        assert cuadrado.via_marca(l) is not None                             # cada parada para en el punto de vía más cercano
    c["lugares"] = [l for l in c["lugares"] if l["tipo"] != "tranvia" or l is a or l is b]
    c.pop("vias")
    dos = M.Mundo(json.loads(json.dumps(c)))
    assert len(dos.linea_tranvia()) == 2 and dos.via_largo > 0               # el juego no repone las paradas que has quitado
    c["lugares"] = [l for l in c["lugares"] if l["tipo"] not in ("tranvia", "tren", "aeropuerto")]
    c["transporte"] = False
    nada = M.Mundo(json.loads(json.dumps(c)))
    assert not any(l.tipo in ("tranvia", "tren", "aeropuerto") for l in nada.lugares.values()) and nada.via_largo == 0
    # el editor conoce los campos y avisa de lo que está mal
    from editor import esquema, modelo
    campos_mapa = [cp["k"] for cp in esquema.ESQUEMAS["mapa"]["campos"]]
    campos_lugar = [cp["k"] for cp in esquema.ESQUEMAS["lugar"]["campos"]]
    assert "vias" in campos_mapa and "transporte" in campos_mapa and "orden" in campos_lugar and "cruce_via" in esquema.ESQUEMAS
    mod = modelo.Mod.desde_crudo(json.load(open(os.path.join(rutas.MODS, "bahia_del_ocaso.json"), encoding="utf-8")))
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    assert not errores and not avisos, (errores, avisos)
    mapa = mod.secciones["mapas"][0]
    assert mapa.get("vias") and len(mapa["vias"]) >= 4
    buenas = list(mapa["vias"])
    mapa["vias"] = buenas + [{"a": 99, "b": 0}]
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    assert any("no existe" in e and "vías" in e for e in errores)
    mapa["vias"] = [{"a": 0, "b": 0}, {"a": 1, "b": 0}]                       # vías que no pasan cerca de las paradas
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    assert not errores and any("metros de las vías" in x for x in avisos)
