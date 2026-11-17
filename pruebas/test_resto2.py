"""Segunda tanda de lo que completa la 1.6.2: señales, puntería, voz, y lo que venga detrás."""
import pygame

from juego.menus import Menu


def test_volumen_de_las_senales_de_ayuda(robot):
    app = robot.app
    mez = app.mez
    assert mez.sonar("baliza", cat="interfaz").senal and mez.sonar("radar", cat="interfaz").senal and mez.sonar("tono_objetivo").senal
    assert mez.sonar("lugar_bar").senal and not mez.sonar("claxon").senal and not mez.sonar("menu_ok").senal
    app.cfg["vol_senales"] = 0.5
    app.aplicar_volumenes()
    assert mez.vols["senales"] == 0.5
    c, d = mez.sonar("baliza", cat="interfaz"), mez.sonar("menu_ok", cat="interfaz")
    mez._calcular(c)
    mez._calcular(d)
    assert abs(max(c.gl_obj, c.gr_obj) - 0.5 * max(d.gl_obj, d.gr_obj)) < 1e-6      # la señal, a la mitad; lo demás, igual
    app.cfg["vol_senales"] = 1.0
    app.aplicar_volumenes()


def test_aviso_al_acertar_y_correr_sin_mantener(robot):
    p = robot.nueva_partida()
    app = robot.app
    vib = []
    app.vibrar = lambda *a: vib.append(a)
    from juego.entidades import Persona
    e = Persona("enemigo", p.j.x + 3, p.j.y, "Matón")
    e.hostil, e.salud, e.inofensivo, e.tag = True, 5000.0, True, "mision"
    p.personas.append(e)
    p.dar_arma("pistola", 200)
    p.elegir_arma(list(p.orden_armas).index("pistola")) if hasattr(p, "orden_armas") and p.j.arma != "pistola" else None
    p.j.arma = "pistola"
    p.fijar()
    assert vib and vib[-1][2] <= 100                                         # al fijar, un toque en el mando
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append((n, k.get("tono"))), original(n, **k))[1]
    for _ in range(12):
        p.j.t_ataque = 0
        p.j.armas["pistola"]["cargador"] = 5
        p.atacar()
    p.son = original
    assert ("tono_objetivo", 2.0) in sonidos and any(v == (0.15, 0.8, 90) for v in vib)
    app.cfg["aviso_acierto"] = False
    sonidos.clear()
    p.son = lambda n, **k: (sonidos.append((n, k.get("tono"))), original(n, **k))[1]
    for _ in range(12):
        p.j.t_ataque = 0
        p.j.armas["pistola"]["cargador"] = 5
        p.atacar()
    p.son = original
    app.cfg["aviso_acierto"] = True
    assert ("tono_objetivo", 2.0) not in sonidos
    # correr con una pulsación
    assert not p.corriendo_ahora()
    app.cfg["correr_alternar"] = True
    robot.tecla(pygame.K_LSHIFT)
    robot.frames(1)                                               # cambia al soltarla, no al pulsarla
    assert p.corriendo_ahora() and "Correr" in app.voz.registro[-1]
    y0 = p.j.y
    robot.frames(30, mantener=(pygame.K_UP,))
    rapido = p.j.y - y0
    robot.tecla(pygame.K_LSHIFT)
    robot.frames(1)
    assert not p.corriendo_ahora()
    y0 = p.j.y
    robot.frames(30, mantener=(pygame.K_UP,))
    assert rapido > 1.5 * (p.j.y - y0) > 0
    app.cfg["correr_alternar"] = False


def test_detalle_de_voz_y_voz_de_windows(robot):
    from juego import voz
    app = robot.app
    assert voz.resumir("Farmacia Luna. Pulsa Intro para entrar.") == "Farmacia Luna."
    assert voz.resumir("Pulsa Intro para continuar.") == "Pulsa Intro para continuar."      # nunca deja un mensaje vacío
    assert voz.resumir("Misión completada: El recado. Recompensa: 300 euros.") == "Misión completada: El recado. Recompensa: 300 euros."
    app.cfg["detalle_voz"] = "poco"
    app.decir("Has llegado. Pulsa F para subir.")
    assert app.voz.registro[-1] == "Has llegado."
    app.cfg["detalle_voz"] = "mucho"
    from juego import menus_juego
    menus_juego.opciones(app)
    m = app.pila[-1]
    assert isinstance(m, Menu)
    robot.tecla(pygame.K_DOWN)
    o = m.opciones[m.i]
    assert o.ayuda and o.ayuda in app.voz.registro[-1]                       # con mucho detalle, la explicación va detrás
    app.cfg["detalle_voz"] = "normal"
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_UP)
    assert o.ayuda not in app.voz.registro[-1]
    app.cerrar(m)

    class Falsa:
        def __init__(self):
            self.puesto = {}

        def set_rate(self, v):
            self.puesto["velocidad"] = v

        def set_pitch(self, v):
            self.puesto["tono"] = v

        def set_volume(self, v):
            self.puesto["volumen"] = v
    v = voz.Voz(muda=True)
    v.muda, v.sapi, v.salida = False, True, Falsa()
    v.ajustar_sapi(25, -3, 140)
    assert v.salida.puesto == {"velocidad": 10, "tono": -3, "volumen": 100}       # dentro de los límites
    v.sapi = False
    v.salida.puesto.clear()
    v.ajustar_sapi(1, 1, 1)
    assert v.salida.puesto == {}                                                  # con lector de pantalla no toca nada
    for clave in ("voz_velocidad", "voz_tono", "voz_volumen", "vol_senales", "aviso_acierto", "correr_alternar", "detalle_voz"):
        assert clave in app.cfg.datos if hasattr(app.cfg, "datos") else app.cfg[clave] is not None


def test_formato_de_las_partidas_guardadas(robot):
    import pytest
    from juego import partida as P
    p = robot.nueva_partida()
    d = p.a_dict()
    assert d["version"] == P.FORMATO == 3 and "momento" in d and d["fallos"] == {} and d["decisiones"] == {}
    vieja = {k: v for k, v in d.items() if k not in ("fallos", "decisiones", "saltadas", "momento")}
    vieja["version"] = 2
    vieja["jugador"] = {k: v for k, v in d["jugador"].items() if k not in ("rep_bandas", "foco")}
    nueva = P.migrar(vieja)
    assert nueva["version"] == 3 and nueva["fallos"] == {} and nueva["jugador"]["rep_bandas"] == {} and vieja["version"] == 2
    sin_numero = dict(vieja)
    sin_numero.pop("version")
    assert P.migrar(sin_numero)["version"] == 3
    assert set(P.CONVERSIONES) == set(range(2, P.FORMATO))                    # hay conversión para cada formato anterior
    futura = dict(d, version=P.FORMATO + 1)
    with pytest.raises(P.PartidaMasNueva):
        P.migrar(futura)
    # una partida más nueva no se carga ni rompe nada: se avisa y sigues donde estabas
    antes = robot.app.partida
    robot.app.empezar_partida(futura)
    assert robot.app.partida is antes and "versión más nueva" in robot.app.voz.registro[-1] and robot.app.pila[-1] is antes
    # una vieja sí se carga, convertida
    robot.app.empezar_partida(vieja)
    assert robot.app.partida is not antes and robot.app.partida.fallos == {} and robot.app.partida.j.rep_bandas == {}


def test_saltar_repetir_diario_y_resumen(robot):
    import time
    from juego import menus_juego
    p = robot.nueva_partida()
    app = robot.app
    p.cfg["sucesos"] = False
    m = next(x for x in p.datos["misiones"] if x["id"] == "m01")
    assert "Todavía no has hecho ninguna misión" in p.resumen_historia() and m["titulo"] in p.resumen_historia()
    # fallar tres veces deja saltarse la misión
    for n in range(3):
        p.iniciar_mision(m)
        robot.saltar_dialogos()
        if p.mision is None:
            break
        p.fallar_mision("Prueba.")
        menu = app.pila[-1]
        textos = [o.texto for o in menu.opciones]
        assert ("Saltarte esta misión" in textos) == (n == 2), (n, textos)
        if n < 2:
            app.cerrar(menu)
    assert p.fallos["m01"] == 3
    dinero = p.j.dinero
    menu.i = textos.index("Saltarte esta misión")
    robot.tecla(pygame.K_RETURN)
    assert "m01" in p.completadas and "m01" in p.saltadas and p.j.dinero == dinero and "m01" not in p.fallos and p.mision is None
    assert "Llevas 1 misión de la historia" in p.resumen_historia()
    # el diario la muestra como saltada y deja repetirla, sin recompensa
    robot.tecla(pygame.K_m)
    movil = app.pila[-1]
    movil.i = next(k for k, o in enumerate(movil.opciones) if o.texto.startswith("Diario"))
    robot.tecla(pygame.K_RETURN)
    diario = app.pila[-1]
    assert diario.opciones[0].texto.startswith("Llevas 1 misión")
    diario.i = next(k for k, o in enumerate(diario.opciones) if o.texto.startswith(m["titulo"]) and "saltada" in o.texto)
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)                                              # sí, repetirla
    robot.saltar_dialogos()
    assert p.mision is not None and p.mision["repeticion"] and app.pila[-1] is p
    n_hechas, dinero = len(p.completadas), p.j.dinero
    p.mision["paso"] = len(m["pasos"]) - 1
    p._siguiente_paso()
    robot.saltar_dialogos()
    assert p.mision is None and len(p.completadas) == n_hechas and p.j.dinero == dinero and "Has repetido" in robot.dicho()
    # al volver tras varios días, el juego recuerda por dónde ibas
    d = p.a_dict()
    d["momento"] = time.time() - 5 * 86400
    app.empezar_partida(d)
    p = app.partida
    assert p.resumen_pendiente and p.saltadas == ["m01"]
    robot.frames(80)
    assert not p.resumen_pendiente and "Hace días que no jugabas" in robot.dicho()
    d["momento"] = time.time()
    app.empezar_partida(d)
    assert not app.partida.resumen_pendiente


def test_mejoras_de_armas(robot):
    from juego import menus_juego
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    p.dar_arma("pistola", 100)
    j.dinero = 10000
    arm = p.lugares["armeria_centro"]
    p.teletransportar(arm.x, arm.y)
    menus_juego._armeria(p, arm)
    m = app.pila[-1]
    textos = [o.texto for o in m.opciones]
    assert any(t.startswith("Silenciador para Pistola") for t in textos) and any(t.startswith("Cargador ampliado para Pistola") for t in textos)
    base = p.armas_d["pistola"]["cargador"]
    assert p.capacidad("pistola") == base
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Cargador ampliado para Pistola"))
    robot.tecla(pygame.K_RETURN)
    assert j.armas["pistola"]["ampliado"] and p.capacidad("pistola") == int(base * 1.5)
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Silenciador para Pistola"))
    robot.tecla(pygame.K_RETURN)
    assert j.armas["pistola"]["silenciador"] and not any(o.texto.startswith(("Silenciador para Pistola", "Cargador ampliado para Pistola")) for o in m.opciones)
    app.cerrar(m)
    # recargar llena hasta la capacidad ampliada
    j.arma = "pistola"
    j.armas["pistola"]["cargador"] = 0
    p.recargar()
    assert j.armas["pistola"]["cargador"] == int(base * 1.5)
    # con silenciador el disparo no hace ruido: nadie huye ni llama a la policía
    ruidos = []
    p._ruido_disparo = lambda x, y: ruidos.append(1)
    j.t_ataque = 0
    p.atacar()
    assert not ruidos
    j.armas["pistola"]["silenciador"] = False
    j.t_ataque = 0
    p.atacar()
    assert ruidos
    # las mejoras se guardan con la partida
    j.armas["pistola"]["silenciador"] = True
    d = p.a_dict()
    app.empezar_partida(d)
    assert app.partida.j.armas["pistola"]["silenciador"] and app.partida.capacidad("pistola") == int(base * 1.5)


def test_tiempo_lento_y_cobertura(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    reloj = p.reloj
    robot.frames(60)
    normal = p.reloj - reloj
    robot.tecla(pygame.K_BACKSPACE)
    assert p.lento and "Tiempo lento" in app.voz.registro[-1]
    reloj, foco = p.reloj, j.foco
    robot.frames(60)
    assert 0.3 * normal < p.reloj - reloj < 0.5 * normal and j.foco < foco - 20      # el mundo va más despacio y gasta concentración
    assert app.mez.tono_mundo < 0.8
    robot.frames(30 * 5)
    assert not p.lento and j.foco < 10 and "Se te acaba la concentración" in robot.dicho()
    robot.tecla(pygame.K_BACKSPACE)
    assert not p.lento and "Te falta concentración" in app.voz.registro[-1]
    robot.frames(30 * 12)
    assert j.foco > 15 and app.mez.tono_mundo == 1.0
    robot.tecla(pygame.K_BACKSPACE)
    robot.tecla(pygame.K_BACKSPACE)
    assert not p.lento and "Tiempo normal" in app.voz.registro[-1]
    # cobertura: hace falta algo detrás de lo que ponerse
    libre = None
    for dx in range(0, 60, 3):
        x, y = j.x + dx, j.y
        if p.mundo.transitable(x, y):
            p.teletransportar(x, y)
            if p._hay_parapeto() is None:
                libre = (x, y)
                break
    for v in list(p.vehiculos):
        if v.dist(j.x, j.y) < 6:
            p.quitar_vehiculo(v)
    if libre:
        robot.tecla(pygame.K_x, mod=pygame.KMOD_LSHIFT)
        assert p.cubierto is None and "no hay nada tras lo que cubrirte" in app.voz.registro[-1]
    p.crear_vehiculo("sedan", j.x + 2, j.y, 0, "aparcado")
    robot.tecla(pygame.K_x, mod=pygame.KMOD_LSHIFT)
    assert p.cubierto and j.agachado and "A cubierto" in app.voz.registro[-1]
    assert "Estás a cubierto" in (p.estado() or app.voz.registro[-1])
    app.cfg["dificultad"] = "normal"
    j.salud, j.blindaje = 100.0, 0.0
    p.danar_jugador(20, (j.x + 5, j.y))
    con = 100.0 - j.salud
    p.dejar_cobertura()
    j.salud = 100.0
    p.danar_jugador(20, (j.x + 5, j.y))
    sin = 100.0 - j.salud
    assert 0 < con < 0.4 * sin                                              # a cubierto llega mucho menos daño
    # moverse saca de la cobertura
    j.salud = 100.0
    p.alternar_cobertura()
    assert p.cubierto
    j.agachado = False
    robot.frames(30, mantener=(pygame.K_LEFT,))
    assert p.cubierto is None


def test_multa_o_soborno(robot, monkeypatch):
    import random
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    p.dar_arma("pistola", 50)
    j.dinero = 2000
    j.estrellas = 1
    j.puntos_busqueda = 1.5
    multa = p.coste_multa()
    assert multa == 150 + 100
    p.detener()
    m = app.pila[-1]
    assert isinstance(m, Menu) and not m.escapable and m.opciones[0].texto.startswith("Pagar la multa") and not p.transicion
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is p and j.dinero == 2000 - multa and j.estrellas == 0 and "pistola" in j.armas and j.stats["detenciones"] == 0
    # soborno que sale bien, y soborno que sale mal
    j.estrellas, j.puntos_busqueda, j.dinero = 2, 5.0, 2000
    monkeypatch.setattr(random, "random", lambda: 0.0)
    p.detener()
    m = app.pila[-1]
    m.i = 1
    robot.tecla(pygame.K_RETURN)
    assert j.estrellas == 0 and "pistola" in j.armas and 0 < 2000 - j.dinero < p.coste_multa() + 400
    j.estrellas, j.puntos_busqueda, j.dinero = 1, 1.5, 2000
    monkeypatch.setattr(random, "random", lambda: 0.999)
    p.detener()
    m = app.pila[-1]
    m.i = 1
    robot.tecla(pygame.K_RETURN)
    monkeypatch.undo()
    robot.frames(30 * 8)
    robot.saltar_dialogos()
    assert j.stats["detenciones"] == 1 and "pistola" not in j.armas          # te detienen igualmente
    # con mucha búsqueda, sin dinero o con la opción quitada, no hay trato
    for estrellas, dinero, opcion in ((3, 5000, True), (1, 10, True), (1, 5000, False)):
        robot.frames(30 * 8)
        robot.saltar_dialogos()
        p.transicion = False
        j.estrellas, j.dinero = estrellas, dinero
        app.cfg["multas"] = opcion
        antes = j.stats["detenciones"]
        p.detener()
        assert j.stats["detenciones"] == antes + 1, (estrellas, dinero, opcion)
    app.cfg["multas"] = True
