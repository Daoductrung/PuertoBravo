"""Lo pedido en el hilo tras el anuncio de la 1.7.3: la reconquista apagada se respeta, la vida social respeta la
atracción y deja quitar personas del móvil, el contrato lleva al trabajo, el historial no se llena con los menús, Escape
corta una descarga aunque la red no conteste, y la patrulla y la ambulancia no rodean una manzana para siempre."""
import random
import time

import pygame

from juego import i18n, sistemas


class _Azar:
    """Un azar que siempre deja pasar el suceso y elige un ataque."""
    def random(self):
        return 0.0

    def choice(self, lista):
        return "ataque" if "ataque" in lista else lista[0]


def test_con_la_reconquista_apagada_nadie_ataca_tus_barrios(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = True
    j = p.j
    j.territorios = [next(b["id"] for b in p.mundo.barrios)]
    p.cfg["reconquista"] = "apagado"
    for _ in range(30):
        sistemas.sucesos_territorio(p, azar=_Azar())
    assert j.amenaza is None
    # con la reconquista en marcha, los asaltos los lleva ella; y sin ninguna de las dos cosas, como siempre
    p.cfg["reconquista"] = "normal"
    p.rec_activa = lambda: False
    j.banda = 0
    sistemas.sucesos_territorio(p, azar=_Azar())
    assert j.amenaza is not None


def test_la_vida_social_respeta_la_atraccion_y_deja_quitar_personas(robot):
    from juego import menus_adultos as MA
    p = robot.nueva_partida()
    app = robot.app
    personas = {x["id"]: x for x in p.dato_adulto("personas")}
    assert personas["andres"]["genero"] == "h" and personas["lucia"]["genero"] == "m"
    p.cfg["atraccion"] = "mujeres"
    MA.vida_social(p)
    m = app.pila[-1]
    textos = " | ".join(o.texto for o in m.opciones)
    assert "Andrés" not in textos and "Ibai" not in textos
    assert sum(1 for o in m.opciones if o.texto.startswith("Alguien a quien no conoces")) == 4      # Lucía, Noa, Valeria y Sole
    app.cerrar(m)
    # a quien ya conoces y no te atrae, solo amistad: ni gestos ni pedirle que sea tu pareja
    p.relacion("andres")
    MA.vida_social(p, directo="andres")
    f = app.pila[-1]
    tf = [o.texto for o in f.opciones]
    assert "Pedirle que sea tu pareja" not in tf and "Darle un beso" not in tf and "Quitar a Andrés de tu móvil" in tf
    # quitarlo del móvil, y recuperarlo al final de la lista
    f.i = tf.index("Quitar a Andrés de tu móvil")
    robot.tecla(pygame.K_RETURN)
    assert "andres" in p.j.ocultos_social and "ya no sale en tu móvil" in robot.dicho()
    while len(app.pila) > 1 and app.pila[-1] is not p:
        app.cerrar(app.pila[-1])
    MA.vida_social(p)
    m = app.pila[-1]
    assert not any("Andrés" in o.texto for o in m.opciones)
    assert m.opciones[-2].texto == "Personas que has quitado de tu móvil: 1"
    m.i = len(m.opciones) - 2
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)
    assert "andres" not in p.j.ocultos_social and "vuelve a salir" in robot.dicho()
    # con todos, sale todo el mundo; y una persona de un mod sin género sale para cualquiera
    p.cfg["atraccion"] = "todos"
    assert MA.te_atrae(p, personas["andres"]) and MA.te_atrae(p, {"id": "x"})


def test_el_contrato_lleva_a_hacer_un_turno(robot):
    from juego import menus_honrado as MH
    p = robot.nueva_partida()
    c = next(c for c in p.hon_empleos() if any(x.startswith("jornada:") for x in c.get("cuenta") or []))
    ops = MH.opciones_ir_a_trabajar(p, c)
    assert ops and ops[0].texto.startswith("Ir a hacer un turno:") and "oficina de empleo" in ops[0].texto
    p.gps = None
    ops[0].accion()
    assert p.gps is not None and "Allí, en el menú de la oficina" in robot.dicho()
    destino = p.lug(p.gps["lugar"]) if isinstance(p.gps, dict) and "lugar" in p.gps else None
    assert destino is None or destino.tipo == "empleo"


def test_el_historial_no_guarda_lo_que_se_lee_en_los_menus(robot):
    from juego.menus import Menu, Opcion
    app = robot.app
    app.cfg["historial_menus"] = False
    antes = len(app.voz.historial)
    m = Menu(app, "Un menú de prueba", [Opcion("Primera"), Opcion("Segunda")])
    app.abrir(m)
    robot.tecla(pygame.K_DOWN)
    assert len(app.voz.historial) == antes
    app.decir("Compras un bocadillo.")                       # lo que pasa sí entra
    assert app.voz.historial[-1] == "Compras un bocadillo."
    app.cfg["historial_menus"] = True
    robot.tecla(pygame.K_UP)
    assert app.voz.historial[-1].startswith("Primera")
    app.cerrar(m)
    app.cfg["historial_menus"] = False


def test_escape_corta_la_espera_aunque_la_red_no_conteste():
    from juego.menus_actualizar import Tarea

    class App:
        pruebas = False
        pila = []

        def decir(self, t, *a):
            pass

        def son(self, *a, **k):
            pass

        def cerrar(self, x):
            pass
    fin = {}

    def colgada(tarea):
        time.sleep(5)                                        # la red no contesta: el trozo no llega
        return "tarde"
    t = Tarea(App(), "Descargando", colgada, lambda r, e: fin.update(r=r, e=e))
    t.actualizar(0)

    class Ev:
        key = pygame.K_ESCAPE
    t.tecla(Ev())
    for _ in range(30):
        t.actualizar(0.1)
        if fin:
            break
    assert fin and fin["r"] is None and type(fin["e"]).__name__ == "Cancelado"


def test_la_policia_y_la_ambulancia_no_rodean_la_manzana_para_siempre(robot):
    p = robot.nueva_partida()

    class V:
        pass
    v = V()
    p.t = 0.0
    assert not p.no_se_acerca(v, 50.0, 60)                  # se está acercando
    p.t = 3.0
    assert not p.no_se_acerca(v, 45.0, 60)
    p.t = 9.0
    assert p.no_se_acerca(v, 45.5, 60)                      # cinco segundos sin acercarse, y ya cerca: se baja
    w = V()
    p.t = 0.0
    p.no_se_acerca(w, 200.0, 60)
    p.t = 10.0
    assert not p.no_se_acerca(w, 200.0, 60)                 # lejos: sigue buscando el camino


def test_las_novedades_solo_en_espanol_e_ingles():
    original = i18n.actual
    try:
        for cod, esperado in (("es", "es"), ("en", "en"), ("vi", "en"), ("pt", "en")):
            i18n.actual = lambda c=cod: c
            assert i18n.idioma_novedades() == esperado
    finally:
        i18n.actual = original
    random.seed(0)
