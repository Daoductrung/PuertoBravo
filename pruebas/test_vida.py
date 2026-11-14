"""Personajes, vida honrada, interiores, sonidos de todo y documentación al día."""
import os
import re

import pygame

from juego import ayuda, catalogo_sonidos, rutas
from juego.menus import Menu


def _elegir(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    for k, o in enumerate(m.opciones):
        if texto.lower() in o.texto.lower():
            m.i = k
            robot.tecla(pygame.K_RETURN)
            return
    raise AssertionError(f"no hay opción «{texto}» en {[o.texto for o in m.opciones]}")


def test_elegir_personaje(robot):
    p = robot.nueva_partida("Sam")
    j = p.j
    assert (j.nombre, j.apellido) == ("Sam", "Ferrer") and j.salud_max == 120 and p.nivel("punteria") == 4 and "navaja" in j.armas
    assert p.txt("Así que tú eres Dani. Dani Roca, ¿no?") == "Así que tú eres Sam. Sam Ferrer, ¿no?"
    # la historia usa su nombre
    m = p.misiones_disponibles()[0]
    bar = p.lugares[m["lugar"]]
    j.x, j.y = bar.x, bar.y
    robot.frames(10)
    p.iniciar_mision(m)
    dicho = " ".join(robot.app.voz.registro[-3:])
    assert "¡Sam!" in dicho and "Dani" not in dicho
    # otro personaje
    robot.app.volver_al_menu()
    p2 = robot.nueva_partida("Álex")
    assert p2.j.nombre == "Álex" and p2.nivel("conduccion") == 5 and p2.j.objetos["ganzua"] == 3
    robot.app.volver_al_menu()
    p3 = robot.nueva_partida("Cris")
    assert p3.j.dinero == 800 and p3.ciudadania_txt() == "los vecinos te aprecian"


def test_vida_honrada(robot):
    p = robot.nueva_partida()
    j = p.j
    c0 = j.ciudadania
    of = p.lugares["empleo_pb"]
    j.x, j.y = of.x, of.y
    robot.frames(12)
    robot.tecla(pygame.K_RETURN)
    assert p.interior is not None                      # dentro del local suena su ambiente
    dinero = j.dinero
    _elegir(robot, "Jornada de camarero")
    assert j.dinero > dinero and j.ciudadania > c0 and j.jornada_dia == p.dia
    _elegir(robot, "Jornada de reponedor")             # solo una al día
    assert "Hoy ya has trabajado" in robot.dicho()
    _elegir(robot, "Oficio de taxista")
    assert robot.app.pila[-1] is p and p.gps is not None and p.interior is None
    # ascensos: ocho servicios de taxi
    x, y, d = p.mundo.plaza_junto_a(p.lugares["parada_taxi"])
    v = p.crear_vehiculo("taxi", x, y, d, None)
    p._subir(v, False, callar=True)
    robot.tecla(pygame.K_j)
    for _ in range(40):
        if p.servicios_de("taxi") >= 8:
            break
        l = p.trabajo["lugar"]
        x, y, d = p.mundo.plaza_junto_a(l)
        v.x, v.y, v.vel = x, y, 0.0
        robot.frames(5)
    assert p.rango("taxi") == 1 and "Ascenso" in " ".join(robot.app.voz.registro[-40:]) and p.mult_trabajo("taxi") > 1.1
    robot.tecla(pygame.K_j)
    v.vel = 0
    robot.tecla(pygame.K_f)
    # curso y voluntariado
    j.dinero = 2000
    ac = p.lugares["autoescuela"]
    j.x, j.y = ac.x, ac.y
    robot.frames(12)
    nivel = p.nivel("conduccion")
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Curso de conducción")
    assert p.nivel("conduccion") > nivel and j.dinero == 1750
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    ong = p.lugares["comedor_social"]
    j.x, j.y = ong.x, ong.y
    robot.frames(12)
    robot.tecla(pygame.K_RETURN)
    antes = j.ciudadania
    _elegir(robot, "Donar 500")
    _elegir(robot, "voluntariado")
    assert j.ciudadania > antes + 10
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    # los delitos bajan el prestigio
    antes = j.ciudadania
    p.delito(4, "prueba", siempre=True)
    assert j.ciudadania < antes
    from juego import menus_vida
    menus_vida.carrera(p)
    assert any("Taxista oficial" in o.texto for o in robot.app.pila[-1].opciones)


def test_horas_del_dia_suenan(robot):
    p = robot.nueva_partida()
    sonados = []
    orig = p.mez.sonar
    p.mez.sonar = lambda nombre, **kw: (sonados.append(nombre), orig(nombre, **kw))[1]
    p.reloj = 6 * 60 + 59.9
    robot.frames(10)
    p.reloj = 20 * 60 + 59.9
    robot.frames(10)
    p.reloj = 23 * 60 + 59.95
    robot.frames(10)
    assert {"gallo", "buho", "campanadas"} <= set(sonados)
    assert "Amanece." in robot.app.voz.registro and "Anochece." in robot.app.voz.registro


def test_todo_sonido_usado_existe(app):
    """Ningún sonido que nombre el código falta en el juego, y todos están en la guía de sonidos."""
    existentes = set(app.mez.sonidos)
    usados = set()
    raiz = os.path.join(rutas.base(), "juego")
    patron = re.compile(r'''(?:\.son|\.sonar)\(\s*["']([a-z0-9_]+)["']''')
    for f in os.listdir(raiz):
        if f.endswith(".py"):
            texto = open(os.path.join(raiz, f), encoding="utf-8").read()
            usados |= set(patron.findall(texto))
    usados = {s for s in usados if not s.endswith("_") and s != "radio_pista"}      # prefijos de nombres compuestos y la pista de radio, que se carga al vuelo
    faltan = sorted(s for s in usados if s not in existentes)
    assert not faltan, faltan
    assert len(usados) > 100
    # los que nombran los datos: sonido de cada lugar, arma, vehículo, sustancia...
    en_datos = set()

    def recorrer(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str) and k in ("sonido", "motor", "claxon", "son", "sonido_disparo", "disparo"):
                    en_datos.add(v)
                else:
                    recorrer(v)
        elif isinstance(d, list):
            for v in d:
                recorrer(v)
    recorrer(app.datos)
    for mundo in app.datos.get("mapas", {}).values() if isinstance(app.datos.get("mapas"), dict) else []:
        recorrer(mundo)
    faltan = sorted(s for s in en_datos if s not in existentes)
    assert not faltan, faltan
    assert len(en_datos) > 20, en_datos
    # cada sonido tiene su descripción propia en el catálogo de la guía
    sin_describir = sorted(s for s in existentes if not s.startswith(("radio_", "musica_")) and catalogo_sonidos.describir(s) == "Sonido del juego.")
    assert not sin_describir, sin_describir
    # y los del glosario del juego existen
    assert not [s for s, _, _ in ayuda.SONIDOS if s not in existentes]


def test_todas_las_teclas_estan_documentadas(app):
    """Cada tecla que atiende el juego aparece en la ayuda (y por tanto en el manual, que se genera de ella)."""
    raiz = os.path.join(rutas.base(), "juego")
    texto = open(os.path.join(raiz, "partida.py"), encoding="utf-8").read() + open(os.path.join(raiz, "conduccion.py"), encoding="utf-8").read()
    teclas = set(re.findall(r"k == pygame\.K_([a-zA-Z0-9_]+)", texto)) | set(re.findall(r"pygame\.K_([a-z])\b", texto))
    documentadas = " ".join(t for grupo in ayuda.TECLAS.values() for t, _ in grupo).lower()
    descripciones = " ".join(d for grupo in ayuda.TECLAS.values() for _, d in grupo).lower()
    nombres = {"ESCAPE": "escape", "TAB": "tabulador", "RETURN": "intro", "KP_ENTER": "intro", "SPACE": "espacio", "COMMA": "coma", "PERIOD": "punto",
               "PAGEUP": "re pág", "PAGEDOWN": "av pág", "LCTRL": "control", "RCTRL": "control", "UP": "flecha", "DOWN": "flecha", "LEFT": "flecha", "RIGHT": "flecha",
               "LSHIFT": "mayúsculas", "RSHIFT": "mayúsculas"}
    faltan = []
    for t in sorted(teclas):
        nombre = nombres.get(t, t.lower())
        if nombre.startswith("f") and nombre[1:].isdigit():
            ok = nombre in documentadas
        elif len(nombre) == 1:
            ok = re.search(rf"(^|[\s,]){nombre}([\s,]|$)", documentadas) is not None
        else:
            ok = nombre in documentadas or nombre in descripciones
        if not ok:
            faltan.append(t)
    assert not faltan, faltan
