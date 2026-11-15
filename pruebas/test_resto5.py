"""Decisiones con consecuencias, relación con las bandas y finales distintos."""
import pygame

from juego.menus import Dialogo, Menu


def _llegar_a_la_decision(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.completadas.append("eo6")
    m = next(x for x in p.datos["misiones"] if x["id"] == "fd1")
    assert m in p.misiones_disponibles()
    l = p.lugares[m["lugar"]]
    p.teletransportar(l.x, l.y)
    p.iniciar_mision(m)
    for _ in range(12):                                     # pasa el diálogo, sin tocar el menú de la decisión
        if isinstance(robot.app.pila[-1], Dialogo):
            robot.tecla(pygame.K_ESCAPE)
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu) and not menu.escapable and len(menu.opciones) == 3 and "pruebas contra el concejal" in menu.titulo
    return p, menu


def _elegir(robot, menu, n):
    menu.i = n
    robot.tecla(pygame.K_RETURN)
    robot.saltar_dialogos()


def test_decision_honrada_y_su_final(robot):
    p, menu = _llegar_a_la_decision(robot)
    fama = p.j.reputacion
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is menu                                         # de una decisión no se sale sin elegir
    _elegir(robot, menu, 0)
    assert p.decisiones["concejal"]["opcion"] == 1 and p.j.reputacion == fama + 6 + 2 and "fd1" in p.completadas
    disponibles = {m["id"] for m in p.misiones_disponibles()}
    assert "fd2" in disponibles and "fd3" not in disponibles and "fd4" not in disponibles      # la historia se bifurca
    # el final queda apuntado y sale en el diario
    fd2 = next(x for x in p.datos["misiones"] if x["id"] == "fd2")
    p.mision = {"def": fd2, "paso": len(fd2["pasos"]), "enemigos": []}
    p._completar_mision()
    assert p.decisiones["_final"]["texto"].startswith("Final honrado") and "Final de la historia" in robot.dicho()
    robot.tecla(pygame.K_m)
    movil = robot.app.pila[-1]
    movil.i = next(k for k, o in enumerate(movil.opciones) if o.texto.startswith("Diario"))
    robot.tecla(pygame.K_RETURN)
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert any(t.startswith("Decisión: Dárselas a la redactora") for t in textos) and any(t.startswith("Decisión: Final honrado") for t in textos)
    # se guarda y se carga con la partida
    d = p.a_dict()
    robot.app.empezar_partida(d)
    q = robot.app.partida
    assert q.decisiones["concejal"]["opcion"] == 1 and "fd3" not in {m["id"] for m in q.misiones_disponibles()}


def test_decision_del_dinero(robot):
    p, menu = _llegar_a_la_decision(robot)
    dinero, fama = p.j.dinero, p.j.reputacion
    _elegir(robot, menu, 1)
    assert p.j.dinero == dinero + 20000 and p.j.reputacion < fama + 3
    disponibles = {m["id"] for m in p.misiones_disponibles()}
    assert "fd3" in disponibles and "fd2" not in disponibles and "fd4" not in disponibles


def test_decision_de_la_calle_y_relacion_con_las_bandas(robot):
    from juego import menus_extra, sistemas
    from juego.entidades import Persona
    p, menu = _llegar_a_la_decision(robot)
    _elegir(robot, menu, 2)
    assert p.rep_banda("Los Calaveras") == 60 and p.rep_banda_txt(60) == "sois aliados" and "Los Calaveras: sois aliados" in robot.dicho()
    assert "fd4" in {m["id"] for m in p.misiones_disponibles()}
    # los Calaveras de la calle ya no te atacan... mientras no les toques
    e = Persona("banda", p.j.x + 6, p.j.y, "Calavera")
    e.hostil, e.estado, e.activo, e.avisado, e.arma, e.salud = True, "ataca", True, True, "pistola", 500.0
    e.t_disparo = 0.1
    p.personas.append(e)
    salud = p.j.salud
    robot.frames(30 * 4)
    assert p.j.salud == salud and not getattr(e, "provocado", False)
    p.danar_persona(e, 10)
    assert e.provocado
    # matar a uno de los suyos empeora la relación
    antes = p.rep_banda("Los Calaveras")
    p.danar_persona(e, 5000)
    assert p.rep_banda("Los Calaveras") == antes - 4
    # una banda que te respeta no ataca tus barrios; el menú de territorios dice cómo te llevas con cada una
    p.j.territorios.append(p.mundo.barrios[0]["id"])
    p.cfg["sucesos"] = True

    class Azar:
        def random(self):
            return 0.0

        def choice(self, lista):
            return "Los Calaveras" if "Los Calaveras" in lista else lista[0]
    sistemas.sucesos_territorio(p, Azar())
    assert p.j.amenaza is None
    p.j.rep_bandas["Los Lagartos"] = -45.0
    assert p.rep_banda_txt(-45) == "van a por ti" and p.rep_banda_txt(0) == "ni amigos ni enemigos"
    menus_extra.territorios(p)
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert any("Cómo te llevas con las bandas" in t and "Los Lagartos, van a por ti" in t for t in textos)


def test_pasos_condicionados_y_repetir_no_cambia_lo_decidido(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    m = {"id": "zz1", "titulo": "Prueba", "lugar": "periodico", "requiere": [], "pasos": [
        {"tipo": "decision", "clave": "zz", "pregunta": "¿A o B?", "opciones": [{"texto": "A", "dinero": 100}, {"texto": "B", "dinero": -50, "dice": "Has elegido B."}]},
        {"tipo": "dialogo", "si_clave": "zz", "si_opcion": 1, "lineas": [["Narrador", "Rama A."]]},
        {"tipo": "dialogo", "si_clave": "zz", "si_opcion": 2, "lineas": [["Narrador", "Rama B."]]}], "recompensa": {}}
    dinero = p.j.dinero
    p.iniciar_mision(m)
    menu = robot.app.pila[-1]
    menu.i = 1
    robot.tecla(pygame.K_RETURN)
    assert p.decisiones["zz"] == {"opcion": 2, "texto": "B", "mision": "zz1"} and p.j.dinero == dinero - 50 and "Has elegido B." in robot.dicho()
    d = robot.app.pila[-1]
    assert isinstance(d, Dialogo) and "Rama B." in robot.app.voz.registro[-1]          # se salta la rama que no toca
    robot.saltar_dialogos()
    assert "zz1" in p.completadas
    # al repetirla, elegir otra cosa no cambia la historia ni vuelve a dar dinero
    dinero = p.j.dinero
    p.iniciar_mision(m, repeticion=True)
    menu = robot.app.pila[-1]
    menu.i = 0
    robot.tecla(pygame.K_RETURN)
    robot.saltar_dialogos()
    assert p.decisiones["zz"]["opcion"] == 2 and p.j.dinero == dinero
    # el editor conoce el paso y avisa de lo que falta
    from editor import esquema
    assert "decision" in [t for t, _ in esquema.TIPOS_PASO] and "opcion_decision" in esquema.ESQUEMA if hasattr(esquema, "ESQUEMA") else True


def test_las_tres_ramas_estan_bien_formadas(robot):
    p = robot.nueva_partida()
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    fd1 = por_id["fd1"]
    dec = next(x for x in fd1["pasos"] if x["tipo"] == "decision")
    assert dec["clave"] == "concejal" and len(dec["opciones"]) == 3 and all(o.get("ayuda") and o.get("dice") for o in dec["opciones"])
    finales = set()
    for n, ident in enumerate(("fd2", "fd3", "fd4"), 1):
        m = por_id[ident]
        assert m["si_clave"] == "concejal" and m["si_opcion"] == n and m["requiere"] == ["fd1"] and len(m["final"]) > 80
        finales.add(m["final_titulo"])
        assert m["lugar"] in p.lugares
        for paso in m["pasos"]:
            for clave in ("lugar", "destino"):
                assert not paso.get(clave) or paso[clave] in p.lugares, (ident, paso[clave])
            for q in paso.get("puntos", []):
                assert q in p.lugares
    assert len(finales) == 3 and p.datos["capitulos"]["12"] == "La decisión"
