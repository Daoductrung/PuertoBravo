"""1.7.4: la ranura es la partida (issue 19). El guardado automático, el rápido y el de un cierre inesperado van a la
ranura de la partida que juegas y nunca pisan la de otro personaje; antes de escribir encima, lo que había queda como
copia anterior; una partida nueva toma la primera ranura libre; y con la opción apagada, todo va como antes."""
import os
import shutil

from juego import menus_juego as MJ, rutas


def _limpio():
    shutil.rmtree(rutas.data(MJ.CARPETA), ignore_errors=True)


def _nombre(r, anterior=False):
    d = MJ.leer_ranura(r, anterior)
    return d and d["jugador"]["dinero"]


def test_cada_partida_guarda_en_su_ranura_y_no_pisa_la_de_otra(robot):
    _limpio()
    app = robot.app
    app.cfg["guardado_por_ranura"] = True
    a = robot.nueva_partida()
    a.j.dinero = 111
    MJ.autoguardar(a)                                     # sin ranura aún: toma la primera libre
    assert a.ranura == "1" and _nombre("1") == 111 and "ranura 1" in robot.dicho()
    assert MJ.leer_ranura("auto") is None and MJ.leer_ranura("rapido") is None
    a.j.dinero = 112
    MJ.guardado_rapido(a)
    assert _nombre("1") == 112 and _nombre("1", anterior=True) == 111       # lo de antes queda como copia anterior
    # otro personaje: su guardado va a otra ranura, y la de A sigue intacta
    app.volver_al_menu()
    b = robot.nueva_partida()
    b.j.dinero = 222
    MJ.autoguardar(b)
    assert b.ranura == "2" and _nombre("2") == 222 and _nombre("1") == 112
    # el cierre inesperado, también a su ranura
    b.j.dinero = 223
    assert MJ.guardar_por_si_acaso(b)
    assert _nombre("2") == 223 and _nombre("2", anterior=True) == 222
    # al cargar A, sus guardados vuelven a la 1
    assert MJ.cargar(app, "1")
    a2 = app.partida
    assert a2.ranura == "1" and a2.id_partida == a.id_partida
    a2.j.dinero = 113
    MJ.autoguardar(a2)
    assert _nombre("1") == 113 and _nombre("2") == 223
    # si en su ranura has guardado a mano otra partida, el automático no la pisa: va a una libre
    assert MJ.escribir_ranura(b, "1")
    assert b.ranura == "1"
    a2.j.dinero = 114
    MJ.autoguardar(a2)
    assert a2.ranura == "3" and _nombre("3") == 114 and _nombre("1") == 223


def test_la_copia_anterior_se_carga_y_sigue_en_su_ranura(robot):
    _limpio()
    app = robot.app
    app.cfg["guardado_por_ranura"] = True
    p = robot.nueva_partida()
    p.j.dinero = 500
    assert MJ.escribir_ranura(p, "4")
    p.j.dinero = 600
    assert MJ.escribir_ranura(p, "4")
    assert os.path.isdir(os.path.join(rutas.data(MJ.CARPETA), MJ.ANTERIORES))
    MJ.menu_cargar(app)
    textos = [o.texto for o in app.pila[-1].opciones]
    assert not any(t.startswith(("Guardado automático", "Guardado rápido")) for t in textos)        # los compartidos, solo si los hay
    assert sum(1 for t in textos if t.startswith("Ranura ")) == 10
    assert any(t.startswith("Copia anterior de la ranura 4") for t in textos)
    app.cerrar(app.pila[-1])
    assert MJ.cargar(app, "4", anterior=True)
    q = app.partida
    assert q.j.dinero == 500 and q.ranura == "4"
    MJ.autoguardar(q)
    assert _nombre("4") == 500 and _nombre("4", anterior=True) == 600       # deshacer se puede deshacer


def test_una_ranura_de_antes_sin_identidad_sigue_siendo_de_quien_la_carga(robot):
    _limpio()
    app = robot.app
    app.cfg["guardado_por_ranura"] = True
    p = robot.nueva_partida()
    p.j.dinero = 700
    d = p.a_dict()                                        # una partida guardada con la 1.7.3: sin id_partida ni ranura
    d["fecha"], d["resumen"] = "01/11/2026 10:00", "x"
    MJ.cifrado.escribir_json(MJ._archivo("2"), d)
    assert MJ.cargar(app, "2")
    q = app.partida
    q.j.dinero = 701
    MJ.autoguardar(q)
    assert q.ranura == "2" and _nombre("2") == 701


def test_sin_ranuras_libres_y_con_la_opcion_apagada(robot):
    _limpio()
    app = robot.app
    app.cfg["guardado_por_ranura"] = True
    otra = robot.nueva_partida()
    for r in MJ.NUMERADAS:
        assert MJ.escribir_ranura(otra, r)
    app.volver_al_menu()
    p = robot.nueva_partida()
    p.j.dinero = 900
    MJ.autoguardar(p)
    assert _nombre("auto") == 900 and "No queda ninguna ranura libre" in robot.dicho()
    # con la opción apagada, como antes de la 1.7.4: los archivos compartidos
    _limpio()
    app.cfg["guardado_por_ranura"] = False
    p.ranura = None
    p.j.dinero = 901
    MJ.autoguardar(p)
    MJ.guardado_rapido(p)
    assert _nombre("auto") == 901 and _nombre("rapido") == 901 and all(MJ.leer_ranura(r) is None for r in MJ.NUMERADAS)
    app.cfg["guardado_por_ranura"] = True
    _limpio()
