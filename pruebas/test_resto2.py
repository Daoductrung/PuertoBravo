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
    assert p.corriendo_ahora() and "Correr" in app.voz.registro[-1]
    y0 = p.j.y
    robot.frames(30, mantener=(pygame.K_UP,))
    rapido = p.j.y - y0
    robot.tecla(pygame.K_LSHIFT)
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
