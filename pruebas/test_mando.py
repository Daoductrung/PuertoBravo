"""Mando (simulado), nuevas actividades y estructura de la carpeta data."""
import math
import os

import pygame

from juego import rutas
from juego.menus import Dialogo, Menu


def test_carpeta_data(app):
    for sub in ("datos", "sonidos", "radio", "config", "docs", "mods"):
        assert os.path.isdir(rutas.data(sub)), sub
    wavs = [f for f in os.listdir(rutas.SONIDOS) if f.endswith(".wav")]
    assert len(wavs) >= 170
    assert set(os.path.splitext(f)[0] for f in wavs) <= set(app.mez.sonidos)
    app.radio.esperar()
    for e in app.radio.emisoras:
        if "estilo" in e:
            assert app.radio.pistas[e["id"]] and all(os.path.exists(r) for r in app.radio.pistas[e["id"]]), e["id"]
    assert not os.path.exists(os.path.join(rutas.base(), "cache"))


def test_sonido_sustituido_y_emisora_nueva(app):
    """Un WAV puesto por el jugador sustituye al original, y un archivo nuevo en radio es una emisora más."""
    import numpy as np
    from juego import sintesis
    from juego.audio import Mezclador
    from juego.musica import Radio
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = os.path.join(tmp, "sonidos")
        m = Mezclador(dispositivo=False)
        S = sintesis.cargar(m, carpeta)
        assert os.path.exists(os.path.join(carpeta, "claxon.wav"))
        import soundfile as sf
        sf.write(os.path.join(carpeta, "claxon.wav"), np.zeros((22050, 2), dtype="float32") + 0.25, 22050)      # estéreo y a otra frecuencia
        os.remove(os.path.join(carpeta, "baliza.wav"))
        m2 = Mezclador(dispositivo=False)
        S2 = sintesis.cargar(m2, carpeta)
        assert S2["claxon"].ndim == 1 and abs(len(S2["claxon"]) - 44100) < 10 and abs(float(S2["claxon"].mean()) - 0.25) < 0.01
        assert "baliza" in S2 and os.path.exists(os.path.join(carpeta, "baliza.wav"))       # el borrado se regenera
        radio = os.path.join(tmp, "radio")
        os.makedirs(radio)
        sf.write(os.path.join(radio, "mi_emisora_pirata.wav"), np.zeros((4410, 2), dtype="float32"), 44100)
        r = Radio(m2, radio)
        r.esperar()
        nombres = [e["nombre"] for e in r.emisoras]
        assert "Mi emisora pirata" in nombres
        txt = r.sintonizar(nombres.index("Mi emisora pirata"))
        r.esperar()                                         # la canción se carga en segundo plano
        assert "pirata" in txt.lower() and r.canal is not None


def test_mando_en_menus_y_a_pie(robot):
    app = robot.app
    md = app.mando
    md.simulado = True
    menu = app.pila[-1]
    assert isinstance(menu, Menu) and md.contexto() == "menu"
    i0 = menu.i
    md.boton("abajo", True); md.boton("abajo", False)
    assert menu.i == i0 + 1
    md.eje("ly", 1.0); robot.frames(1); md.eje("ly", 0.0); robot.frames(1)      # palanca hacia abajo
    assert menu.i == i0 + 2
    md.boton("arriba", True); md.boton("arriba", False)
    md.boton("arriba", True); md.boton("arriba", False)
    assert menu.i == i0
    # nueva partida con el botón A, diálogos con B
    menu.i = next(k for k, o in enumerate(menu.opciones) if o.texto == "Nueva partida")
    md.boton("a", True); md.boton("a", False)
    for _ in range(10):
        cima = app.pila[-1]
        if isinstance(cima, Dialogo):
            md.boton("b", True); md.boton("b", False)
        elif isinstance(cima, Menu):
            cima.i = 0 if "personaje" in str(cima.titulo) else len(cima.opciones) - 1
            md.boton("a", True); md.boton("a", False)
        else:
            break
    p = app.partida
    assert app.pila[-1] is p and md.contexto() == "pie"
    # caminar con la palanca izquierda: derecha es este
    x0 = p.j.x
    md.eje("lx", 0.6)
    robot.frames(40)
    andado = p.j.x - x0
    assert andado > 2
    md.eje("lx", 1.0)
    x1 = p.j.x
    robot.frames(40)
    assert p.j.x - x1 > andado * 1.5            # a fondo, corre
    md.eje("lx", 0.0)
    robot.frames(2)
    x2 = p.j.x
    robot.frames(10)
    assert p.j.x == x2 and pygame.K_RIGHT not in app.teclas
    # cruceta: dónde estoy, radar; palanca derecha: escáner
    n = len(app.voz.registro)
    md.boton("arriba", True); md.boton("arriba", False)
    md.boton("derecha", True); md.boton("derecha", False)
    md.eje("ry", -1.0); robot.frames(1); md.eje("ry", 0.0); robot.frames(1)       # palanca derecha arriba: mirar al norte
    dicho = " | ".join(app.voz.registro[n:])
    assert "Calle Mayor" in dicho and "Al norte" in dicho and " de " in dicho
    # pausa con Start y volver con B
    md.boton("start", True); md.boton("start", False)
    assert isinstance(app.pila[-1], Menu)
    md.boton("b", True); md.boton("b", False)
    assert app.pila[-1] is p


def test_mando_al_volante_y_reasignar(robot):
    app = robot.app
    md = app.mando
    md.simulado = True
    p = robot.nueva_partida()
    robot.frames(30)
    v = min((v for v in p.vehiculos if v.ia == "aparcado"), key=lambda v: v.dist(p.j.x, p.j.y))
    v.cerrado = False
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 2, v.y)
    md.boton("y", True); md.boton("y", False)          # Y o Triángulo: subir
    assert p.j.veh is v and md.contexto() == "coche"
    for o in list(p.vehiculos):
        if o is not v:
            p.quitar_vehiculo(o)
    p.plazas_usadas.update(pl["id"] for pl in p.mundo.aparcados)
    md.eje("rt", 1.0)                                   # gatillo derecho: acelerar
    robot.frames(60)
    assert v.vel > 4
    md.eje("lx", 1.0); robot.frames(1); md.eje("lx", 0.0); robot.frames(1)        # toque a la derecha: intermitente
    assert v.giro == 1
    md.eje("rt", 0.0)
    md.eje("lt", 1.0)                                   # gatillo izquierdo: frenar
    robot.frames(90)
    md.eje("lt", 0.0)
    robot.frames(2)
    assert abs(v.vel) < 7 and pygame.K_UP not in app.teclas and pygame.K_DOWN not in app.teclas
    v.vel = 0.0
    md.boton("y", True); md.boton("y", False)
    assert p.j.veh is None
    # reasignar: A a pie pasa a ser «estado»
    md.mapa["pie"]["a"] = "estado"
    n = len(app.voz.registro)
    md.boton("a", True); md.boton("a", False)
    assert "Salud" in " ".join(app.voz.registro[n:])
    md.restablecer()
    assert md.mapa["pie"]["a"] == "interactuar"
    ayuda = md.lineas_ayuda()
    assert len(ayuda) > 30 and any("Gatillo derecho" in t for t in ayuda)
    md.tipo = "ps"
    assert any("Triángulo" in t for t in md.lineas_ayuda())
    from juego import menus_extra
    menus_extra.opciones_mando(app)
    assert isinstance(app.pila[-1], Menu) and len(app.pila[-1].opciones) >= 7


def test_perro_territorios_bolsa_y_minijuegos(robot):
    from juego import menus_extra
    from juego.pantallas import BuscaTesoro, SimonSonoro
    from juego.entidades import Persona
    p = robot.nueva_partida()
    j = p.j
    j.dinero = 100000
    # perro
    j.perro = "Canela"
    d = p.crear_perro()
    robot.frames(60, mantener=(pygame.K_RIGHT, pygame.K_LSHIFT))
    assert d.dist(j.x, j.y) < 12
    e = Persona("enemigo", j.x + 15, j.y, "Matón")
    e.hostil = True
    p.personas.append(e)
    robot.frames(40)
    assert "gruñe" in robot.dicho()
    p.personas.remove(e)
    robot.tecla(pygame.K_y)
    assert p.gps is not None and "olfateado" in robot.dicho()
    # bolsa
    antes = dict(j.bolsa)
    p.mover_bolsa()
    assert len(j.bolsa) == 5 and j.bolsa != antes
    menus_extra.bolsa(p)
    m = robot.app.pila[-1]
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)
    assert j.acciones.get("naviera") == 10 and j.dinero < 100000
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    # territorio: se juega la conquista entera
    b = p.mundo.barrios[2]
    p.empezar_conquista(b)
    for _ in range(40):
        if p.mision is None:
            break
        ms = p.mision
        paso = ms["def"]["pasos"][ms["paso"]]
        l = p.lugares[paso["lugar"]]
        j.salud = j.salud_max
        if not ms["generado"]:
            j.x, j.y = l.x, l.y
            robot.frames(4)
        for en in list(ms["enemigos"]):
            p.danar_persona(en, 9999)
        robot.frames(6)
    assert p.mision is None and b["id"] in j.territorios
    p._fin_persecucion()
    dinero = j.dinero
    p.ingresos_territorios()
    assert j.dinero == dinero + 300
    # memoria de sonidos: el robot repite cinco rondas
    s = SimonSonoro(robot.app, p)
    robot.app.abrir(s)
    teclas = {0: pygame.K_UP, 1: pygame.K_RIGHT, 2: pygame.K_DOWN, 3: pygame.K_LEFT}
    for _ in range(6000):
        if robot.app.pila[-1] is not s:
            break
        robot.frames(1)
        if s.estado == "turno":
            if len(s.sec) > 5:
                robot.tecla(teclas[(s.sec[s.pos] + 1) % 4])        # falla a propósito
            else:
                robot.tecla(teclas[s.sec[s.pos]])
    assert robot.app.pila[-1] is p and j.stats.get("simon") == 5
    # tesoro: va directo
    t = BuscaTesoro(robot.app, p, True)
    robot.app.abrir(t)
    while t.x != t.tx:
        robot.tecla(pygame.K_RIGHT if t.tx > t.x else pygame.K_LEFT)
    while t.y != t.ty:
        robot.tecla(pygame.K_UP if t.ty > t.y else pygame.K_DOWN)
    robot.frames(30)
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and j.stats.get("tesoros") == 1


def test_bombero_grua_y_mensajero(robot):
    p = robot.nueva_partida()
    j = p.j
    for modelo, tipo in (("bomberos", "bomberos"), ("grua", "grua"), ("scooter", "paqueteria")):
        if j.veh:
            v = j.veh
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
        x, y, d = p.mundo.plaza_junto_a(p.lugares["hospital"])
        v = p.crear_vehiculo(modelo, x, y, d, None)
        p._subir(v, False, callar=True)
        robot.tecla(pygame.K_j)
        assert p.trabajo and p.trabajo["tipo"] == tipo, robot.dicho()
        for _ in range(4):
            l = p.trabajo["lugar"]
            x, y, d = p.mundo.plaza_junto_a(l)
            v.x, v.y, v.vel = x, y, 0.0
            robot.frames(190 if tipo == "bomberos" else 5)
        assert p.trabajo["hechas"] >= 2, (tipo, robot.dicho())
        robot.tecla(pygame.K_j)
        assert p.trabajo is None
