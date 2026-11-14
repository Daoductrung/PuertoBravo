"""Mejoras de la 1.6.2: ambientes en estéreo, sonido mono, atenuación al hablar, zonas, menús, puntos de control y tutorial."""
import os
import time

import numpy as np
import pygame

from juego import packs, sintesis
from juego.audio import Mezclador
from juego.menus import Dialogo, Menu
from juego.misiones import paso_seguro


def _tono(segundos, hz, sr, canales=1, fase=0.0):
    t = np.arange(int(sr * segundos)) / sr
    a = (0.4 * np.sin(2 * np.pi * hz * t + fase)).astype(np.float32)
    return a if canales == 1 else np.stack([a, (0.4 * np.sin(2 * np.pi * hz * 1.5 * t)).astype(np.float32)], axis=1)


def test_los_ambientes_se_quedan_en_estereo_y_lo_demas_en_mono(tmp_path):
    import soundfile as sf
    assert sintesis.es_fondo("amb_ciudad") and sintesis.es_fondo("lluvia") and not sintesis.es_fondo("motor_coche") and not sintesis.es_fondo("paso_acera0")
    sf.write(str(tmp_path / "amb_ciudad.wav"), _tono(2.0, 300, 44100, canales=2), 44100)
    sf.write(str(tmp_path / "claxon.wav"), _tono(0.5, 300, 44100, canales=2), 44100)
    amb = sintesis.leer_audio(str(tmp_path / "amb_ciudad.wav"), mono=not sintesis.es_fondo("amb_ciudad"))
    cla = sintesis.leer_audio(str(tmp_path / "claxon.wav"), mono=not sintesis.es_fondo("claxon"))
    assert amb.shape == (88200, 2) and cla.shape == (22050,)
    assert not np.allclose(amb[:, 0], amb[:, 1])                       # los dos canales siguen siendo distintos
    # un ambiente demasiado largo se recorta, y uno mono se queda mono
    sf.write(str(tmp_path / "largo.wav"), _tono(4.0, 200, 22050, canales=2), 22050)
    assert len(sintesis.leer_audio(str(tmp_path / "largo.wav"), mono=False, maximo=2)) == 88200
    sf.write(str(tmp_path / "mono.wav"), _tono(1.0, 200, 44100), 44100)
    assert sintesis.leer_audio(str(tmp_path / "mono.wav"), mono=False).ndim == 1
    # el mezclador lo reproduce en estéreo, y el igualado de volumen no lo aplana
    mez = Mezclador(dispositivo=False)
    mez.registrar("amb_ciudad", packs.igualar(amb, (0.2, 0.3)))
    mez.sonar("amb_ciudad", bucle=True, cat="ambiente")
    for _ in range(40):
        mez.actualizar()
        salida = mez.render(1024)
    assert salida.shape == (1024, 2) and not np.allclose(salida[:, 0], salida[:, 1]) and np.abs(salida).max() > 0.01


def test_convertir_la_frecuencia_no_estropea_el_sonido(tmp_path):
    import soundfile as sf
    sf.write(str(tmp_path / "a48.wav"), _tono(1.0, 9000, 48000), 48000)          # un agudo, que es lo que más sufría
    d = sintesis.leer_audio(str(tmp_path / "a48.wav"))
    assert abs(len(d) - 44100) <= 1
    espectro = np.abs(np.fft.rfft(d[2000:-2000] * np.hanning(len(d) - 4000)))
    pico = int(np.argmax(espectro))
    hz = pico * 44100 / (len(d) - 4000)
    assert abs(hz - 9000) < 5
    resto = np.delete(espectro, range(pico - 30, pico + 31))
    assert resto.max() < espectro[pico] / 300                                     # nada de ecos ni tonos fantasma


def test_sonido_mono_y_bajar_el_ambiente_al_hablar():
    mez = Mezclador(dispositivo=False)
    mez.registrar("amb_x", _tono(2.0, 300, 44100, canales=2))
    mez.registrar("golpe_x", _tono(2.0, 500, 44100))
    amb = mez.sonar("amb_x", bucle=True, cat="ambiente")
    for _ in range(60):
        mez.actualizar()
        mez.render(512)
    normal = amb.gl_obj
    mez.mono = True
    s = mez.render(512)
    assert np.allclose(s[:, 0], s[:, 1])
    mez.mono = False
    efecto = mez.sonar("golpe_x", bucle=True, cat="efectos")
    mez.hablando("Una frase de unas cuantas palabras para que dure un poco.")
    for _ in range(40):
        mez.actualizar()
    assert amb.gl_obj < normal * 0.6 and mez.duck < 0.6                           # el ambiente baja...
    assert efecto.gl_obj > 0.3                                                    # ...y los efectos no
    mez.duck_hasta = time.time() - 1
    for _ in range(200):
        mez.actualizar()
    assert abs(amb.gl_obj - normal) < 0.02                                        # y al callar vuelve
    mez.atenuar = False
    mez.hablando("Otra frase.")
    for _ in range(40):
        mez.actualizar()
    assert mez.duck > 0.98


def test_la_voz_avisa_al_mezclador_y_los_menus_dicen_la_posicion(robot):
    app = robot.app
    app.aplicar_volumenes()
    antes = app.mez.duck_hasta = 0.0
    app.decir("Hola, esto es una prueba.")
    assert app.mez.duck_hasta > antes and app.voz.al_hablar is not None
    m = app.pila[-1]
    assert isinstance(m, Menu)
    app.cfg["menu_posicion"] = False
    robot.tecla(pygame.K_DOWN)
    assert " de " not in app.voz.registro[-1]
    app.cfg["menu_posicion"] = True
    robot.tecla(pygame.K_DOWN)
    assert app.voz.registro[-1].endswith(f". {m.i + 1} de {len(m.opciones)}")
    app.cfg["menu_posicion"] = False


def test_cada_barrio_se_describe_la_primera_vez(robot):
    p = robot.nueva_partida()
    j = p.j
    p.cfg["anunciar_barrios"] = p.cfg["describir_zonas"] = True
    otro = next(b for b in p.mundo.barrios if b["id"] != p.mundo.barrio(*p.pos())["id"] and b["id"] not in j.barrios_vistos)
    origen = p.pos()
    cx, cy = (otro["i"][0] + 0.5) * 90, (otro["j"][0]) * 90 + 3

    def ir(x, y):
        p.teletransportar(x, y)
        p.barrio_act = "de_donde_vengo"            # el teletransporte no anuncia el barrio; caminar, sí
        robot.frames(4)
    ir(cx, cy)
    assert f"Entras en {otro['nombre']} por primera vez. {otro['descripcion']}" in robot.dicho()
    ir(*origen)
    n = len(robot.app.voz.registro)
    ir(cx, cy)
    nuevas = " | ".join(robot.app.voz.registro[n:])
    assert f"Entras en {otro['nombre']}." in nuevas and "por primera vez" not in nuevas


def test_puntos_de_control(robot):
    pasos = [{"tipo": "dialogo"}, {"tipo": "ir"}, {"tipo": "robar"}, {"tipo": "policia"}, {"tipo": "entregar"}, {"tipo": "eliminar"}]
    assert [paso_seguro(pasos, k) for k in range(6)] == [True, True, True, False, False, True]      # con el vehículo de la misión a medias, no
    p = robot.nueva_partida()
    m = next(x for x in p.datos["misiones"] if x["id"] == "oc09")           # diálogo, eliminar, recoger, diálogo
    l = p.lugares[m["lugar"]]
    p.cambiar_mapa(l.mapa, l.x, l.y)
    p.iniciar_mision(m)
    robot.saltar_dialogos()
    assert p.mision["paso"] == 1 and "control" not in p.mision              # el primer tramo es el principio: aún no hay punto de control
    p._siguiente_paso()                                                      # acabas con los enemigos y pasas al tramo de recoger
    assert p.mision["paso"] == 2 and p.mision["control"]["paso"] == 2
    dinero = p.j.dinero
    p.j.dinero += 777                                                        # algo que pasa después del punto de control
    p.fallar_mision("Has muerto.")
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu) and menu.opciones[0].texto == "Reintentar desde el último punto de control"
    menu.i = 0
    robot.tecla(pygame.K_RETURN)
    assert p.mision and p.mision["def"]["id"] == "oc09" and p.mision["paso"] == 2 and p.j.dinero == dinero
    assert "Vuelves al último punto de control" in robot.dicho() and p.mundo.id == l.mapa
    # una misión que falla en su primer tramo solo ofrece empezar de nuevo
    p.abandonar_mision()
    m2 = next(x for x in p.datos["misiones"] if x["id"] == "m01")
    p.iniciar_mision(m2)
    robot.saltar_dialogos()
    p.fallar_mision("Prueba.")
    assert robot.app.pila[-1].opciones[0].texto.startswith("Reintentar desde el principio")


def test_tutorial_jugable(robot):
    p = robot.nueva_partida()
    tut = next(m for m in p.datos["misiones"] if m["id"] == "tut01")
    assert tut in p.misiones_disponibles() and p.misiones_disponibles()[0]["id"] == "m01"
    tipos = [x["tipo"] for x in tut["pasos"]]
    assert tipos == ["dialogo", "ir", "dialogo", "ir", "dialogo", "robar", "entregar", "dialogo"]
    assert not any(x.get("limite") or x.get("enemigos") or x.get("busqueda") for x in tut["pasos"])          # no se puede fallar
    texto = " ".join(t for x in tut["pasos"] if x["tipo"] == "dialogo" for _, t in x["lineas"])
    for tecla in ("tecla C", "pulsa U", "Tabulador", "pulsa B", "W, A, S y D", "pulsa F", "pulsa la Y", "F1"):
        assert tecla in texto, tecla
    assert p.lugares[tut["lugar"]].mapa == "puerto_bravo" and p.datos["capitulos"]["0"] == "Aprender a jugar"
    p.iniciar_mision(tut)
    assert isinstance(robot.app.pila[-1], Dialogo)


def test_reparto_tarde_no_cierra_el_juego(robot):
    """Fallo real de la 1.6.0: al llegar tarde con un paquete, el juego se cerraba al fotograma siguiente."""
    p = robot.nueva_partida()
    j = p.j
    p.cfg["sucesos"] = False
    v = p.crear_vehiculo("moto", j.x, j.y, 0, None)
    p._subir(v, False, callar=True)
    p.alternar_trabajo()
    t = p.trabajo
    assert t and t["tipo"] == "paqueteria" and t["limite"] is not None
    t["limite"] = 0.05
    robot.frames(30)
    assert p.trabajo is not None and p.trabajo["limite"] is None and "ya no tiene propina" in robot.dicho()
    robot.frames(60)                                                    # antes, aquí saltaba el error
    assert robot.app.pila[-1] is p


def test_ningun_trabajo_se_rompe_con_el_tiempo_agotado_o_sin_limite(robot):
    """Lo mismo, para todos los oficios al volante: ni sin tiempo límite ni con el tiempo pasado puede fallar nada."""
    from juego.trabajos import _agotado, _resto
    assert not _agotado({"limite": None}) and _agotado({"limite": -1}) and not _agotado({"limite": 5}) and not _agotado({})
    assert _resto({"limite": None}) == 0 and _resto({"limite": -3}) == 0 and _resto({"limite": 7}) == 7
    p = robot.nueva_partida()
    j = p.j
    p.cfg["sucesos"] = False
    vistos = set()
    for modelo in p.datos["vehiculos"] if isinstance(p.datos["vehiculos"], list) else p.datos["vehiculos"].values():
        tipo = modelo.get("trabajo")
        if not tipo or tipo in vistos or modelo.get("barco") or modelo.get("vuela"):
            continue
        vistos.add(tipo)
        for limite in (None, -1.0, 0.02):
            v = p.crear_vehiculo(modelo["id"], j.x, j.y, 0, None)
            p._subir(v, False, callar=True)
            p.alternar_trabajo()
            if p.trabajo:
                p.trabajo["limite"] = limite
                robot.frames(25)
                if p.trabajo:
                    p.terminar_trabajo("")
            if j.veh:
                p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
            p.limpiar_busqueda()
            assert robot.app.pila[-1] is p, (tipo, limite)
    assert {"taxi", "ambulancia", "autobus", "paqueteria", "bomberos", "grua"} <= vistos


def test_todos_los_menus_tienen_como_volver(robot):
    """Cualquier menú del que se sale con Escape tiene también una opción para volver, al final."""
    from juego import menus_extra, menus_juego
    from juego.menus import SALIDAS
    app = robot.app
    menus_extra.opciones_mando(app)
    m = app.pila[-1]
    assert m.titulo == "Mando" and m.opciones[-1].texto == "Volver"
    n = len(app.pila)
    m.i = len(m.opciones) - 1
    robot.tecla(pygame.K_RETURN)
    assert len(app.pila) == n - 1
    # todas las secciones de Opciones, y lo que cuelga de ellas
    menus_juego.opciones(app)
    raiz = app.pila[-1]
    revisados = 0
    for k in range(len(raiz.opciones)):
        raiz.i = k
        antes = len(app.pila)
        if raiz.opciones[k].accion is None:
            continue
        robot.tecla(pygame.K_RETURN)
        while len(app.pila) > antes:
            cima = app.pila[-1]
            if isinstance(cima, Menu) and cima.escapable:
                assert cima.opciones[-1].texto.startswith(SALIDAS) or cima.opciones[-2].texto.startswith(SALIDAS), cima.titulo
                revisados += 1
            robot.tecla(pygame.K_ESCAPE)
            if app.pila[-1] is cima:
                app.cerrar(cima)
    assert revisados >= 8
    # un menú con su propia salida no recibe otra
    app.abrir(Menu(app, "Prueba", [Opcion_("Una cosa"), Opcion_("No, dejarlo como está")]))
    assert [o.texto for o in app.pila[-1].opciones] == ["Una cosa", "No, dejarlo como está"]
    app.cerrar(app.pila[-1])


from juego.menus import Opcion as Opcion_  # noqa: E402


def test_reasignar_teclas_del_teclado(robot):
    from juego import menus_juego, teclado
    app = robot.app
    cfg = app.cfg
    teclado.restablecer(cfg)
    funs = teclado.funciones()
    codigos = [k for k, _, _ in funs]
    assert len(codigos) == len(set(codigos)) and len(funs) >= 35 and pygame.K_c in codigos and pygame.K_UP in codigos and pygame.K_F9 in codigos
    assert not set(codigos) & teclado.FIJAS
    p = robot.nueva_partida()
    robot.tecla(pygame.K_c)
    donde = app.voz.registro[-1]
    assert teclado.cambiar(cfg, pygame.K_c, pygame.K_p) == pygame.K_p       # «dónde estoy» pasa a la P, y lo de la P a la C
    assert teclado.traducir(cfg, pygame.K_p) == pygame.K_c and teclado.traducir(cfg, pygame.K_c) == pygame.K_p and teclado.traducir(cfg, pygame.K_v) == pygame.K_v
    n = len(app.voz.registro)
    robot.tecla(pygame.K_p)
    assert app.voz.registro[-1] == donde and len(app.voz.registro) == n + 1
    # las teclas mantenidas también: correr hacia el norte con otra tecla
    teclado.cambiar(cfg, pygame.K_UP, pygame.K_i)
    y0 = p.j.y
    app.inyectar(pygame.K_i, soltar=False)                                # la tecla física entra por donde entran las de verdad
    robot.frames(30)
    app.teclas.discard(pygame.K_UP)
    assert p.j.y > y0 + 0.5
    # en los menús las teclas son las de siempre
    robot.tecla(pygame.K_ESCAPE)
    menu = app.pila[-1]
    assert isinstance(menu, Menu)
    i0 = menu.i
    robot.tecla(pygame.K_DOWN)
    assert menu.i == i0 + 1
    robot.tecla(pygame.K_ESCAPE)
    # la ayuda dice las teclas del jugador, y las reservadas no se pueden tocar
    menus_juego.ayuda_teclas(app, "todo")
    textos = [o.texto for o in app.pila[-1].opciones]
    assert any(t.startswith("Tecla cambiada. Lo que hacía C se hace ahora con P") for t in textos)
    assert any(t.startswith("En cualquier momento. P: dónde estoy") for t in textos)
    app.cerrar(app.pila[-1])
    assert teclado.cambiar(cfg, pygame.K_c, pygame.K_ESCAPE) is None and teclado.cambiar(cfg, pygame.K_F1, pygame.K_q) is None
    # el menú: elegir función, pulsar tecla, y restablecer
    menus_juego.opciones_teclado(app)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if ". V:" in o.texto)
    robot.tecla(pygame.K_RETURN)
    assert isinstance(app.pila[-1], teclado.Captura)
    robot.tecla(pygame.K_F12)                                               # reservada: avisa y sigue esperando
    assert isinstance(app.pila[-1], teclado.Captura)
    robot.tecla(pygame.K_g)
    assert app.pila[-1] is m and teclado.tecla_de(cfg, pygame.K_v) == pygame.K_g and teclado.tecla_de(cfg, pygame.K_g) == pygame.K_v
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Restablecer las teclas originales")
    robot.tecla(pygame.K_RETURN)
    assert cfg["teclas"] == {} and teclado.traducir(cfg, pygame.K_p) == pygame.K_p
    app.cerrar(m)


def test_la_policia_da_tiempo_y_no_llega_en_tropel(robot):
    """A pie hay tiempo de reaccionar, las patrullas tienen un tope por nivel y no se acumulan."""
    from juego.combate import PATRULLAS, UMBRAL
    p = robot.nueva_partida()
    j = p.j
    p.cfg["sucesos"] = False
    p.cfg["dificultad"] = "normal"

    def patrullas():
        return sum(1 for v in p.vehiculos if v.ia == "policia" and not v.muerto)
    for v in [v for v in p.vehiculos if v.ia == "policia"]:
        p.quitar_vehiculo(v)
    j.puntos_busqueda = UMBRAL[0]
    robot.frames(30 * 5)                                         # cinco segundos después del delito, a pie
    assert j.estrellas == 1 and patrullas() == 0
    robot.frames(30 * 6)
    assert patrullas() == 1                                      # llega una, no cuatro
    for nivel in (2, 3, 4, 5):
        j.puntos_busqueda = UMBRAL[nivel - 1]
        for _ in range(40):
            p.t_evasion = 0.0                                    # como si no dejaran de verte
            robot.frames(30)
            j.salud = j.salud_max
            assert patrullas() <= PATRULLAS[nivel], (nivel, patrullas())
        assert patrullas() <= PATRULLAS[nivel]
    assert PATRULLAS[1] == 1 and PATRULLAS[2] == 1 and PATRULLAS[5] == 4
    # las sirenas se reparten el volumen
    sirenas = sorted(v.sirena.vol for v in p.vehiculos if v.ia == "policia" and v.sirena is not None)
    assert len(sirenas) < 2 or sirenas[0] < 0.8


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
        p.teletransportar(*p.mundo.punto_libre(ini.x + 10, ini.y))
        robot.frames(3)
    return p, m


def test_seguir_a_alguien_de_oido(robot):
    robot.nueva_partida()
    p, m = _empezar(robot, "ocs1")
    o = p.mision["movil"]
    assert o["nombre"] == "el contable" and len(o["ruta"]) >= 2 and "va a" in p.objetivo_txt()
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append(n), original(n, **k))[1]
    robot.frames(60)
    assert "paso_npc" in sonidos                                   # se le oye andar
    p.son = original
    # pegarte a él: te descubre
    p.teletransportar(o["x"] + 2, o["y"])
    robot.frames(70)
    assert p.mision is None and "se ha dado cuenta" in robot.app.pila[-1].titulo
    robot.app.cerrar(robot.app.pila[-1])
    # quedarte muy atrás: lo pierdes
    p, m = _empezar(robot, "ocs1")
    o = p.mision["movil"]
    o["espera"] = 0
    p.teletransportar(*p.mundo.punto_libre(o["x"] + 80, o["y"]))
    robot.frames(30 * 11)
    assert p.mision is None and "Has perdido de vista" in robot.app.pila[-1].titulo


def test_escoltar_y_sigilo(robot):
    robot.nueva_partida()
    p, m = _empezar(robot, "ocs2")
    e = p.mision["escolta"]
    assert not e["contigo"]
    p.teletransportar(e["x"] + 2, e["y"])
    robot.frames(5)
    assert e["contigo"] and "va contigo" in robot.dicho() and p.gps
    x0, y0 = p.pos()
    p.teletransportar(*p.mundo.punto_libre(x0 + 9, y0))
    robot.frames(90)
    assert __import__("math").hypot(e["x"] - p.pos()[0], e["y"] - p.pos()[1]) < 4      # te sigue
    p.abandonar_mision()
    # sigilo: de pie y corriendo te oyen; agachado y despacio, no
    p, m = _empezar(robot, "ocs3")
    g = p.mision["guardias"][0]
    assert len(p.mision["guardias"]) == 3 and "vigilantes" in p.objetivo_txt()
    p.j.agachado = True
    p.teletransportar(g["x"] + 4, g["y"])
    robot.frames(10)
    assert p.mision is not None                                    # a cuatro metros, agachado, no te oye
    p.j.agachado = False
    robot.frames(10)
    assert p.mision is None and "te ha oído" in robot.app.pila[-1].titulo


def test_pack_envolvente(app):
    """El pack nuevo trae ambientes en estéreo, no toca la orientación y el juego lo carga."""
    import json
    from juego import catalogo_sonidos as cat, packs, rutas
    carpeta = os.path.join(rutas.carpeta_sonidos(), "envolvente") if os.path.isdir(os.path.join(rutas.carpeta_sonidos(), "envolvente")) \
        else os.path.join(rutas.DATA, "sonidos", "envolvente")
    assert os.path.isdir(carpeta)
    meta = json.load(open(os.path.join(carpeta, "pack.json"), encoding="utf-8"))
    assert meta["nombre"] == "Envolvente" and meta["ambientes_en_estereo"] == 11 and "CC0" in meta["licencia"]
    nombres = {os.path.splitext(f)[0] for f in os.listdir(carpeta) if f.endswith((".wav", ".ogg", ".flac", ".mp3"))}
    realista = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(os.path.dirname(carpeta), "realista")) if f.endswith(".wav")}
    assert nombres == realista and len(nombres) == 223          # los mismos archivos que los demás packs
    serie = os.path.join(os.path.dirname(carpeta), "por_defecto")
    orientacion = {k for k, g in enumerate(cat.GRUPOS) if g[0] in ("Orientación y GPS", "Localizadores", "Firmas de los lugares")}
    vistos = 0
    for n in nombres:                                   # los de orientación son, byte a byte, los de serie
        if cat.grupo_de(n) in orientacion:
            vistos += 1
            assert open(os.path.join(carpeta, n + ".wav"), "rb").read() == open(os.path.join(serie, n + ".wav"), "rb").read(), n
    assert vistos >= 40
    creditos = open(os.path.join(carpeta, "CREDITOS.txt"), encoding="utf-8-sig").read()
    for n in ("amb_ciudad", "amb_playa", "amb_noche", "lluvia"):
        assert n in nombres and n + ":" in creditos
    anterior = app.cfg["pack_sonidos"]
    app.cfg["pack_sonidos"] = "envolvente"
    try:
        info = app.recargar_sonidos()
        assert info["pack"] == "envolvente" and info["del_pack"] > 150
        amb = app.mez.sonidos["amb_ciudad"]
        assert amb.ndim == 2 and amb.shape[1] == 2 and 40 * 44100 < len(amb) <= 90 * 44100
        assert not np.allclose(amb[:, 0], amb[:, 1]) and 0.03 < float(np.sqrt((amb ** 2).mean())) < 0.25
        assert app.mez.sonidos["claxon"].ndim == 1                   # lo que tiene posición sigue en mono
        principio, final = amb[:2000], amb[-2000:]
        assert abs(float(final[-1].mean()) - float(principio[0].mean())) < 0.2      # el bucle no da un chasquido
    finally:
        app.cfg["pack_sonidos"] = anterior
        app.recargar_sonidos()


def test_motor_de_sonido_con_respaldo(monkeypatch):
    """El motor envolvente solo se usa si se ha elegido y se puede; en cualquier otro caso, el clásico, sin fallar."""
    from juego import audio_al, procesador
    creados = []

    class Clasico:
        def __init__(self, dispositivo=True):
            creados.append(("clasico", dispositivo))

    class Envolvente:
        def __init__(self):
            creados.append(("envolvente",))
    monkeypatch.setattr(audio_al, "Mezclador", Clasico)
    monkeypatch.setattr(audio_al, "MezcladorAL", Envolvente)
    monkeypatch.setattr(procesador, "moderno", lambda ins=None: True)
    monkeypatch.setattr(audio_al, "disponible", lambda: True)
    monkeypatch.delenv("PUERTOBRAVO_MOTOR", raising=False)
    cfg = {"motor_sonido": "clasico", "sonido_mono": False}
    audio_al.crear(cfg, pruebas=True)
    audio_al.crear(cfg)
    cfg["motor_sonido"] = "envolvente"
    audio_al.crear(cfg)
    assert creados == [("clasico", False), ("clasico", True), ("envolvente",)]
    creados.clear()
    cfg["sonido_mono"] = True                                  # con sonido mono, el clásico
    audio_al.crear(cfg)
    cfg["sonido_mono"] = False
    monkeypatch.setattr(procesador, "moderno", lambda ins=None: False)      # procesador antiguo: el clásico
    audio_al.crear(cfg)
    monkeypatch.setattr(procesador, "moderno", lambda ins=None: True)
    monkeypatch.setattr(audio_al, "disponible", lambda: False)              # falta la biblioteca: el clásico
    audio_al.crear(cfg)
    monkeypatch.setattr(audio_al, "disponible", lambda: True)

    class Roto:
        def __init__(self):
            raise OSError("no arranca")
    monkeypatch.setattr(audio_al, "MezcladorAL", Roto)                      # no arranca: el clásico
    audio_al.crear(cfg)
    assert creados == [("clasico", True)] * 4
    assert os.path.exists(audio_al.ruta_dll()) and audio_al.MezcladorAL is Roto
