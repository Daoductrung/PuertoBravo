"""Lo que completa la 1.6.2: vigilar, carrera con rivales, teclas en los menús, tutoriales, interiores de locales y eco."""
import math

import pygame

from juego.menus import Dialogo, Menu


def _empezar(robot, ident):
    p = robot.p
    m = next(x for x in p.datos["misiones"] if x["id"] == ident)
    l = p.lugares[m["lugar"]]
    p.cambiar_mapa(l.mapa, l.x, l.y)
    p.cfg["sucesos"] = False
    p.iniciar_mision(m)
    robot.saltar_dialogos()
    paso = m["pasos"][p.mision["paso"]]
    ini = p.lugares[paso["lugar"]] if paso.get("lugar") else None
    if ini is not None:
        if ini.mapa != p.mundo.id:
            p.cambiar_mapa(ini.mapa, ini.x, ini.y)
        p.teletransportar(*p.mundo.punto_libre(ini.x + 10, ini.y))
        robot.frames(3)
    return p, m


def test_vigilar_un_lugar(robot):
    robot.nueva_partida()
    p, m = _empezar(robot, "eo5")
    vg = p.mision["vigia"]
    assert vg["dentro"] and "Estás en tu puesto" in robot.dicho() and "Te quedan" in p.objetivo_txt()
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append(n), original(n, **k))[1]
    robot.frames(30 * 20)
    p.son = original
    assert "puerta_entrar" in sonidos and "paso_npc" in sonidos and vg["rondas"] >= 1          # se oye lo que pasa y la ronda
    assert p.mision is not None                                                                 # quieto no te ven
    robot.frames(30 * 32)
    assert "Has contado tres entregas" in robot.dicho() and isinstance(robot.app.pila[-1], Dialogo)
    robot.saltar_dialogos()
    assert "eo5" in p.completadas
    # moverte de pie cuando pasa la ronda: te ven
    p.completadas.remove("eo5")
    p, m = _empezar(robot, "eo5")
    vg = p.mision["vigia"]
    vg["t_ronda"] = 0.0
    robot.frames(30 * 5)
    assert vg["ronda"] is not None
    robot.frames(40, mantener=(pygame.K_UP,))
    assert p.mision is None and "Te han visto moverte" in robot.app.pila[-1].titulo
    robot.app.cerrar(robot.app.pila[-1])
    # agachado sí puedes moverte
    p, m = _empezar(robot, "eo5")
    vg = p.mision["vigia"]
    p.j.agachado = True
    vg["t_ronda"] = 0.0
    robot.frames(30 * 5)
    robot.frames(20, mantener=(pygame.K_UP,))
    assert p.mision is not None
    # irte del puesto: fallas
    l = p.lugares["ferry"]
    p.teletransportar(*p.mundo.punto_libre(l.x + 90, l.y))
    robot.frames(30 * 8)
    assert p.mision is None and "Has dejado el puesto" in robot.app.pila[-1].titulo


def test_carrera_con_rivales(robot):
    robot.nueva_partida()
    p, m = _empezar(robot, "eo6")
    paso = next(x for x in m["pasos"] if x["tipo"] == "carrera")
    robot.frames(5)
    assert "necesitas un vehículo" in robot.dicho() and p.mision["carrera"]["fase"] == "ir"
    v = p.crear_vehiculo("deportivo", p.j.x, p.j.y, 0, None)
    p._subir(v, False, callar=True)
    robot.frames(5)
    ca = p.mision["carrera"]
    assert ca["fase"] == "cuenta" and len(ca["rivales"]) == 2 and "En la salida" in robot.dicho()
    robot.frames(30 * 4)
    assert ca["fase"] == "corre" and all(r["canal"] is not None for r in ca["rivales"]) and p.gps
    assert "Vas tercero de 3" in robot.dicho() and "Vas por el punto 1 de 3" in p.objetivo_txt()
    s0 = ca["rivales"][0]["s"]
    robot.frames(60)
    assert ca["rivales"][0]["s"] > s0 + 10                                   # los rivales corren
    # pasar por los puntos antes que ellos: ganas
    for ident in paso["puntos"]:
        l = p.lugares[ident]
        v.x, v.y = p.mundo.punto_libre(l.x + 5, l.y)
        v.vel = 0.0
        robot.frames(3)
    assert "Has ganado la carrera" in robot.dicho()
    assert all(r["canal"] is None for r in ca["rivales"])                    # los motores de los rivales se callan
    robot.saltar_dialogos()
    assert "eo6" in p.completadas
    # si te quedas parado, gana un rival
    p.completadas.remove("eo6")
    p, m = _empezar(robot, "eo6")
    v = p.crear_vehiculo("deportivo", p.j.x, p.j.y, 0, None)
    p._subir(v, False, callar=True)
    robot.frames(30 * 5)
    ca = p.mision["carrera"]
    for r in ca["rivales"]:
        r["s"] = ca["cum"][-1] - 20
    robot.frames(30 * 5)
    assert p.mision is None and "Ha ganado el coche" in robot.app.pila[-1].titulo


def test_teclas_en_los_menus_y_mayusculas(robot):
    from juego import teclado
    app = robot.app
    cfg = app.cfg
    teclado.restablecer(cfg)
    cfg["teclas_menus"] = False
    robot.nueva_partida()
    teclado.cambiar(cfg, pygame.K_DOWN, pygame.K_k)
    robot.tecla(pygame.K_ESCAPE)
    menu = app.pila[-1]
    assert isinstance(menu, Menu)
    i0 = menu.i
    robot.tecla(pygame.K_k)
    assert menu.i == i0                                                       # sin la opción, en los menús no vale
    cfg["teclas_menus"] = True
    robot.tecla(pygame.K_k)
    assert menu.i == i0 + 1                                                   # con ella, sí
    robot.tecla(pygame.K_ESCAPE)
    # al escribir, las teclas son las normales
    from juego.menus import EntradaTexto
    escrito = []
    app.abrir(EntradaTexto(app, "Prueba", escrito.append))
    robot.tecla(pygame.K_k, unicode="k")
    robot.tecla(pygame.K_RETURN)
    assert escrito == ["k"]
    # la Mayúsculas izquierda se puede mover: la tecla nueva hace de Mayúsculas
    assert pygame.K_LSHIFT in [k for k, _, _ in teclado.funciones()] and pygame.K_RSHIFT in teclado.FIJAS
    teclado.cambiar(cfg, pygame.K_LSHIFT, pygame.K_z)
    assert teclado.traducir(cfg, pygame.K_z) == pygame.K_LSHIFT
    assert teclado.modificadores(cfg, 0, {pygame.K_LSHIFT}) & pygame.KMOD_SHIFT
    assert not teclado.modificadores(cfg, pygame.KMOD_LSHIFT, set()) & pygame.KMOD_SHIFT     # la Mayúsculas física ya no lo es
    vistos = []
    p = app.partida
    original = p.tecla
    p.tecla = lambda ev: (vistos.append((ev.key, ev.mod)), original(ev))[1]
    app.inyectar(pygame.K_z, soltar=False)
    app.inyectar(pygame.K_TAB)
    p.tecla = original
    app.teclas.clear()
    assert vistos[-1][0] == pygame.K_TAB and vistos[-1][1] & pygame.KMOD_SHIFT               # Z más Tabulador es Mayúsculas Tabulador
    teclado.restablecer(cfg)
    cfg["teclas_menus"] = False


def test_tutoriales_nuevos(robot):
    p = robot.nueva_partida()
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    for ident in ("tut01", "tut02", "tut03", "tut04", "tut05"):
        m = por_id[ident]
        assert m["tutorial"] and m["capitulo"] == 0 and m["lugar"] in p.lugares
        assert not any(x.get("limite") or x.get("busqueda") for x in m["pasos"])
        for x in m["pasos"]:
            assert not x.get("lugar") or x["lugar"] in p.lugares
            for g in x.get("enemigos", []):
                assert g.get("inofensivo")                                    # nada de un tutorial ataca
    assert p.misiones_disponibles()[0]["id"] == "m01"                         # la historia sigue yendo primero
    # el de combate: los muñecos no atacan, no llaman a la policía y se pueden tumbar
    p, m = _empezar(robot, "tut02")
    robot.frames(5)
    assert "bate" in p.j.armas and p.mision["generado"] and len(p.mision["enemigos"]) == 1
    e = p.mision["enemigos"][0]
    assert e.inofensivo and e.hostil
    salud = p.j.salud
    p.teletransportar(e.x + 1, e.y)
    robot.frames(30 * 6)
    assert p.j.salud == salud and not e.muerto                               # ni se mueve ni pega
    p.delito(5, "prueba", siempre=True)
    assert p.j.estrellas == 0 and p.j.puntos_busqueda == 0
    p.danar_persona(e, 500)
    robot.frames(5)
    robot.saltar_dialogos()
    robot.frames(5)
    assert "pistola" in p.j.armas and len(p.mision["enemigos"]) == 2
    for e in p.mision["enemigos"]:
        p.danar_persona(e, 500)
    robot.frames(5)
    robot.saltar_dialogos()
    assert "tut02" in p.completadas and p.j.estrellas == 0
    # desde la 1.7.1, el de los trabajos y el del mar no se completan con llegar a un sitio: comprueban lo que haces
    # (se juegan enteros en test_171_tanda5). Y el de los amigos ya no es una misión: es una explicación del móvil
    assert [x["que"] for x in por_id["tut03"]["pasos"] if x["tipo"] == "practica"] == ["trabajar", "servicio"]
    assert [x["que"] for x in por_id["tut04"]["pasos"] if x["tipo"] == "practica"] == ["zarpar", "timon", "atracar"]
    assert not any(x["tipo"] in ("ir", "entregar") for ident in ("tut03", "tut04") for x in por_id[ident]["pasos"])
    assert por_id["tut05"].get("explicacion") and all(x["tipo"] == "dialogo" for x in por_id["tut05"]["pasos"])


def test_recorrer_un_local(robot):
    from juego import menus_juego, sistemas
    p = robot.nueva_partida()
    app = robot.app
    for tipo in sistemas.SALAS:                                               # todas las salas están bien formadas
        salas = sistemas.SALAS[tipo]
        assert salas[0][2] == "salir" and any(s[2] == "mostrador" for s in salas) and len(salas) >= 3
        assert all(s[2] in sistemas.QUE_HACE for s in salas)                  # cada sala hace algo que el juego sabe hacer y explicar
    bar = p.lugares["bar_gaviota"]
    p.teletransportar(bar.x, bar.y)
    menus_juego.lugar(p, bar)
    m = app.pila[-1]
    assert isinstance(m, Menu)
    textos = [o.texto for o in m.opciones]
    assert "Recorrer el local por dentro" in textos and textos.index("Recorrer el local por dentro") < len(textos) - 1 or textos[-1].startswith("Recorrer")
    assert textos.count("Recorrer el local por dentro") == 1
    m.refrescar(False)
    assert [o.texto for o in m.opciones].count("Recorrer el local por dentro") == 1
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Recorrer el local por dentro")
    robot.tecla(pygame.K_RETURN)
    loc = app.pila[-1]
    assert isinstance(loc, sistemas.Local) and "por dentro" in robot.dicho() and app.mez.entorno == "interior"
    robot.tecla(pygame.K_RIGHT)
    assert app.voz.registro[-1].startswith("La barra.")
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_RETURN)
    assert app.voz.registro[-1].startswith("Pones el oído.")
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_RIGHT)
    animo = p.j.animo
    robot.tecla(pygame.K_RETURN)
    assert p.j.animo >= animo and "Te lavas la cara" in app.voz.registro[-1]
    robot.tecla(pygame.K_RIGHT)
    assert "Pared" in app.voz.registro[-1]
    robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is m                                                  # vuelves al menú del bar
    # en el mostrador, Intro también vuelve al menú
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Recorrer el local por dentro")
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is m
    # un lugar al aire libre no tiene interior
    assert sistemas.salas_de(p.lugares["plaza_vieja"]) is None


def test_eco_segun_el_lugar_y_altura(robot):
    from juego import audio_al
    assert audio_al.entorno_de("amb_campo") == "abierto" and audio_al.entorno_de("amb_industrial") == "industrial"
    assert audio_al.entorno_de("amb_montana") == "montana" and audio_al.entorno_de("lo_que_sea") == "calle"
    for nombre, (cuanto, cola, brillo, primeras, tardias) in audio_al.ENTORNOS.items():
        assert 0 <= cuanto <= 1 and 0.1 <= cola <= 20 and 0 <= brillo <= 1 and 0 <= primeras <= 3.16 and 0 <= tardias <= 10, nombre
    assert set(audio_al.DE_AMBIENTE.values()) <= set(audio_al.ENTORNOS)
    p = robot.nueva_partida()
    robot.frames(3)
    mez = robot.app.mez
    assert mez.entorno in audio_al.ENTORNOS and mez.altura == 0.0
    v = p.crear_vehiculo("helicoptero", p.j.x, p.j.y, 0, None)
    p._subir(v, False, callar=True)
    robot.frames(3)
    assert mez.altura > 0                                                     # volando, el mundo suena por debajo
    c = mez.sonar("claxon", xy=(p.j.x + 5, p.j.y))
    assert c.alto == 0.0 and c.eco is False
    assert "eco_lugares" in robot.app.cfg.datos if hasattr(robot.app.cfg, "datos") else robot.app.cfg["eco_lugares"] is True


def test_misiones_nuevas_bien_formadas(robot):
    p = robot.nueva_partida()
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    for ident, tipo in {"eo5": "vigilar", "eo6": "carrera", "ocs5": "vigilar", "ocs6": "carrera"}.items():
        m = por_id[ident]
        paso = next(x for x in m["pasos"] if x["tipo"] == tipo)
        assert paso["lugar"] in p.lugares and paso.get("texto")
        puntos = [p.lugares[q] for q in paso.get("puntos", [])]
        assert all(q.mapa == p.lugares[paso["lugar"]].mapa for q in puntos)            # la carrera no sale de su localidad
        if tipo == "carrera":
            assert len(puntos) >= 2 and 1 <= paso["rivales"] <= 4
            l = p.lugares[paso["lugar"]]
            largo = 0.0
            x, y = l.x, l.y
            mundo = p.mapas[l.mapa]
            for q in puntos:
                for pt in mundo.ruta(x, y, q.x, q.y):
                    largo += math.hypot(pt[0] - x, pt[1] - y)
                    x, y = pt
            assert largo > 300, (ident, largo)                                          # un recorrido de verdad
    from editor import esquema
    tipos = [t for t, _ in esquema.TIPOS_PASO]
    assert "vigilar" in tipos and "carrera" in tipos
