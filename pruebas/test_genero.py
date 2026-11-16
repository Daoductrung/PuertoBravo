"""El protagonista puede ser hombre o mujer, y uno hecho por quien juega.

Pedido en el foro: los diálogos trataban siempre al protagonista en masculino, y solo se podía elegir entre personajes
ya hechos. Ahora se elige cómo te hablan, las frases que cambian llevan las dos formas entre corchetes, y hay un menú
para crear tu propio personaje.
"""
import glob
import json
import os
import re

import pygame

from juego import genero, registro, rutas, vida
from juego.menus import EntradaTexto, Menu

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUELTA = re.compile(r"\[[^\[\]]*\|[^\[\]]*\]")


def _opcion(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    for k, o in enumerate(m.opciones):
        if texto.lower() in o.texto.lower():
            m.i = k
            return o
    raise AssertionError(f"no hay opción «{texto}» en {[o.texto for o in m.opciones]}")


def _elegir(robot, texto):
    _opcion(robot, texto)
    robot.tecla(pygame.K_RETURN)


def _escribir(robot, texto):
    assert isinstance(robot.app.pila[-1], EntradaTexto), robot.dicho()
    for c in texto:
        robot.tecla(pygame.K_a, unicode=c)
    robot.tecla(pygame.K_RETURN)


def _textos(o, salida):
    if isinstance(o, dict):
        for v in o.values():
            _textos(v, salida)
    elif isinstance(o, list):
        for v in o:
            _textos(v, salida)
    elif isinstance(o, str):
        salida.append(o)
    return salida


def test_las_marcas_se_resuelven_segun_el_genero():
    try:
        assert genero.poner("m") == "m"
        assert genero.resolver("Bienvenid[o|a] al balneario.") == "Bienvenida al balneario."
        assert genero.resolver("Tú eres [el sobrino|la sobrina] de Encarna.") == "Tú eres la sobrina de Encarna."
        assert genero.resolver("Buen[|a] vecin[o|a], conductor[|a].") == "Buena vecina, conductora."
        assert genero.poner("h") == "h"
        assert genero.resolver("Buen[|a] vecin[o|a], conductor[|a].") == "Buen vecino, conductor."
        assert genero.resolver("Quiet[o|a] o agachad[o|a].", "m") == "Quieta o agachada."          # también pidiéndolo a mano
        # lo que no es una marca no se toca
        for t in ("Sin marcas.", "Una lista [a, b] y una barra | suelta.", "Corchetes [vacíos] aquí.", "", None, 7):
            assert genero.resolver(t) == t
        assert genero.poner("raro") == "h" and genero.poner(None) == "h"               # ante la duda, como estaba escrito todo
        assert genero.marcas("Hij[o|a], ven.") == [("o", "a")]
    finally:
        genero.poner("h")


def test_los_datos_no_dejan_marcas_a_medias():
    """Todas las frases de los datos y de los mods quedan limpias en los dos géneros, y hay frases marcadas donde hacían falta."""
    archivos = sorted(glob.glob(os.path.join(rutas.DATOS, "*.json"))) + sorted(glob.glob(os.path.join(rutas.DATOS, "mapas", "*.json")))
    archivos += sorted(glob.glob(os.path.join(RAIZ, "data", "mods", "*.json")))
    marcadas = 0
    for ruta in archivos:
        for t in _textos(json.load(open(ruta, encoding="utf-8")), []):
            marcadas += len(genero.marcas(t))
            for g in genero.GENEROS:
                limpio = genero.resolver(t, g)
                assert not SUELTA.search(limpio), (os.path.basename(ruta), t)
                assert "  " not in limpio.strip() or "  " in t, (os.path.basename(ruta), t)
    assert marcadas >= 30, marcadas
    principal = open(os.path.join(rutas.DATOS, "misiones.json"), encoding="utf-8").read()
    assert "[Así que tú eres el sobrino de Encarna. O la sobrina.|" in principal and "Hij[o|a], ¿tú con qué" in principal
    # y en el código: ninguna marca rota en las cadenas del juego
    for ruta in glob.glob(os.path.join(RAIZ, "juego", "*.py")):
        if os.path.basename(ruta) == "genero.py":
            continue
        for trozo in re.findall(r"\[[^\[\]\n\"']*\|[^\[\]\n\"']*\]", open(ruta, encoding="utf-8").read()):
            assert trozo.count("|") == 1, (os.path.basename(ruta), trozo)


def test_dani_en_femenino(robot):
    p = robot.nueva_partida("Dani", genero="m")
    j = p.j
    assert (j.personaje, j.nombre, j.genero) == ("dani", "Dani", "m") and genero.actual == "m"
    # la historia le habla en femenino
    m03 = next(m for m in p.datos["misiones"] if m["id"] == "m03")
    for quien, frase in m03["pasos"][0]["lineas"]:
        p.decir(p.txt(frase))
    dicho = " ".join(robot.app.voz.registro[-8:])
    assert "tú eres la sobrina de Encarna. O el sobrino." in dicho and "[" not in dicho and "|" not in dicho
    m15 = next(m for m in p.datos["misiones"] if m["id"] == "m15")
    p.decir(next(f for q, f in m15["pasos"][0]["lineas"] if "te crees" in f))
    assert robot.app.voz.registro[-1].startswith("Hija, ¿tú con qué")
    # y el juego también: el historial y lo que se repasa llevan ya la forma buena
    p.decir("Estás agachad[o|a]: caminas despacio.")
    assert robot.app.voz.registro[-1] == "Estás agachada: caminas despacio." and robot.app.voz.historial[-1] == "Estás agachada: caminas despacio."
    robot.app.voz.mostrar("Bienvenid[o|a] a Puerto Bravo.")
    assert robot.app.voz.historial[-1] == "Bienvenida a Puerto Bravo."
    j.ciudadania = 20
    p.decir(p.ciudadania_txt())
    assert robot.app.voz.registro[-1] == "eres una vecina más"
    assert genero.resolver(p._carrera_puesto_txt({"puesto": 0, "rivales": [1, 2]})) == "Vas primera de 3."
    from juego.trabajos import NOMBRE_TRABAJO
    assert genero.resolver(NOMBRE_TRABAJO["ambulancia"]) == "conductora de ambulancia" and genero.resolver(vida.RANGOS[2]) == "veterana"
    # las voces grabadas valen también en femenino: cada frase tiene la suya
    p.cfg["voces_grabadas"] = True
    assert p.voces_activas()
    from juego import voces
    assert voces.forma("Encarna", "Bienvenid[o|a].", "dani", "m") == "@m" and voces.forma("Encarna", "Bienvenid[o|a].", "dani", "h") == ""
    # se guarda y se recupera con la partida
    d = json.loads(json.dumps(p.a_dict()))
    assert d["jugador"]["genero"] == "m"
    genero.poner("h")
    robot.app.empezar_partida(d)
    assert robot.p.j.genero == "m" and genero.actual == "m"
    # una partida de antes de la 1.6.3 no lo tenía: sigue en masculino, como estaba
    d["jugador"].pop("genero")
    robot.app.empezar_partida(d)
    assert robot.p.j.genero == "h" and genero.actual == "h"


def test_en_masculino_todo_sigue_igual(robot):
    p = robot.nueva_partida("Sam")
    assert p.j.genero == "h" and genero.actual == "h"
    m03 = next(m for m in p.datos["misiones"] if m["id"] == "m03")
    p.decir(p.txt(m03["pasos"][0]["lineas"][1][1] if "sobrino" in m03["pasos"][0]["lineas"][1][1] else next(f for q, f in m03["pasos"][0]["lineas"] if "Encarna" in f)))
    assert robot.app.voz.registro[-1] == "Así que tú eres el sobrino de Encarna. O la sobrina. Con este ruido no me entero de nada."
    j = p.j
    j.ciudadania = 90
    p.decir(p.ciudadania_txt())
    assert robot.app.voz.registro[-1] == "eres un ciudadano ejemplar"


def test_un_personaje_con_el_genero_fijo_no_pregunta(robot):
    robot.app.datos["personajes"].append({"id": "zz_zoe", "nombre": "Zoe", "apellido": "Prueba", "genero": "m", "pesca": 2, "desc": "De prueba."})
    try:
        p = robot.nueva_partida("Zoe", genero="h")          # aunque el robot quisiera masculino, no hay pregunta
        assert (p.j.nombre, p.j.genero, p.nivel("pesca")) == ("Zoe", "m", 2) and genero.actual == "m"
        # y por código tampoco se le cambia
        p.aplicar_personaje({"id": "zz_zoe", "genero": "h"})
        assert p.j.genero == "m"
    finally:
        robot.app.datos["personajes"][:] = [x for x in robot.app.datos["personajes"] if x["id"] != "zz_zoe"]
        genero.poner("h")
    # los personajes de los mods de ejemplo lo llevan escrito, y el editor lo ofrece
    con = 0
    for ruta in glob.glob(os.path.join(RAIZ, "data", "mods", "*.json")):
        for pj in json.load(open(ruta, encoding="utf-8")).get("personajes", []):
            assert pj.get("genero") in genero.GENEROS, (os.path.basename(ruta), pj["nombre"])
            con += 1
    assert con >= 11
    for pj in json.load(open(os.path.join(rutas.DATOS, "personajes.json"), encoding="utf-8"))["personajes"]:
        assert "genero" not in pj and not re.search(r"\b(Equilibrado|Sobrino|Nacido)\b", pj["desc"])        # los cuatro de siempre valen para él y para ella
    from editor import esquema
    campo = next(c for c in esquema.ESQUEMAS["personaje"]["campos"] if c["k"] == "genero")
    assert [o[0] for o in campo["ops"]] == ["h", "m"] and not campo.get("req")


def test_volver_desde_la_pregunta_no_empieza_nada(robot):
    _elegir(robot, "Nueva partida")
    _elegir(robot, "Álex")
    m = robot.app.pila[-1]
    assert "te hablen con Álex" in m.titulo and [o.texto for o in m.opciones] == ["En masculino", "En femenino", "Volver"]
    robot.tecla(pygame.K_ESCAPE)
    assert "Elige tu personaje" in robot.app.pila[-1].titulo and robot.app.partida is None
    _elegir(robot, "Álex")
    _elegir(robot, "En femenino")
    robot.saltar_dialogos()
    p = robot.p
    assert (p.j.nombre, p.j.genero, p.nivel("conduccion")) == ("Álex", "m", 5)
    genero.poner("h")


def test_crear_tu_propio_personaje(robot):
    app = robot.app
    _elegir(robot, "Nueva partida")
    _elegir(robot, "Crear tu propio personaje")
    m = app.pila[-1]
    assert m.titulo == "Crea tu personaje"
    # sin nombre no se empieza
    _elegir(robot, "Empezar la partida")
    assert app.partida is None and "Falta el nombre" in app.voz.registro[-1]
    _elegir(robot, "Nombre")
    _escribir(robot, "lía3 ")
    assert app.pila[-1] is m and "Nombre: Lía" in _opcion(robot, "Nombre").texto          # sin números y con mayúscula
    _elegir(robot, "Apellido")
    _escribir(robot, "del Mar")
    assert "Apellido: Del Mar" in _opcion(robot, "Apellido").texto
    # cómo le hablan: se cambia con las flechas
    o = _opcion(robot, "Te hablan")
    assert o.texto == "Te hablan en masculino"
    robot.tecla(pygame.K_RIGHT)
    assert _opcion(robot, "Te hablan").texto == "Te hablan en femenino"
    # ocho niveles a repartir, cinco como mucho en una habilidad
    _opcion(robot, "Conducción")
    for _ in range(7):
        robot.tecla(pygame.K_RIGHT)
    assert "Conducción: nivel 5. Quedan 3" in _opcion(robot, "Conducción").texto
    _opcion(robot, "Pesca")
    for _ in range(6):
        robot.tecla(pygame.K_RIGHT)
    assert "Pesca: nivel 3. Quedan 0" in _opcion(robot, "Pesca").texto
    _opcion(robot, "Puntería")
    robot.tecla(pygame.K_RIGHT)
    assert "Puntería: nivel 0" in _opcion(robot, "Puntería").texto                          # no quedan
    _opcion(robot, "Pesca")
    robot.tecla(pygame.K_LEFT)
    _opcion(robot, "Puntería")
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_LEFT)
    robot.tecla(pygame.K_LEFT)                                                             # por debajo de cero tampoco
    assert "Puntería: nivel 0. Quedan 1" in _opcion(robot, "Puntería").texto
    # la ventaja de salida
    _opcion(robot, "Ventaja de salida")
    assert "Ninguna" in _opcion(robot, "Ventaja de salida").texto
    robot.tecla(pygame.K_RIGHT)
    assert "Ahorros" in _opcion(robot, "Ventaja de salida").texto and "ochocientos euros" in _opcion(robot, "Ventaja de salida").texto
    # con niveles sin repartir avisa una vez
    _elegir(robot, "Empezar la partida")
    assert app.partida is None and "Te quedan 1 niveles" in app.voz.registro[-1]
    _elegir(robot, "Empezar la partida")
    robot.saltar_dialogos()
    p = robot.p
    j = p.j
    assert (j.personaje, j.nombre, j.apellido, j.genero) == ("propio", "Lía", "Del Mar", "m") and genero.actual == "m"
    assert (p.nivel("conduccion"), p.nivel("pesca"), p.nivel("punteria"), p.nivel("resistencia")) == (5, 2, 0, 0)
    assert j.dinero == 800 and j.objetos["botiquin"] == 1 and j.salud == j.salud_max == 100
    # la historia usa su nombre y su género
    assert p.txt("Tú eres Dani. Dani Roca, ¿no?") == "Tú eres Lía. Lía Del Mar, ¿no?"
    eo1 = next(m for m in p.datos["misiones"] if m["id"] == "eo1")
    p.decir(p.txt(next(f for q, f in eo1["pasos"][0]["lineas"] if "Encarna" in f)))
    assert app.voz.registro[-1].startswith("Tú eres Lía, la sobrina de Encarna.")
    from juego import voces
    assert voces.forma("Encarna", "Tú eres Dani.", j.personaje, j.genero, j.voz) is None       # su nombre no puede venir grabado: se le genera
    # un nombre escrito por quien juega no va al registro de la sesión
    assert "Lía" in registro._ocultos and "Del Mar" in registro._ocultos
    # y todo se conserva al guardar y cargar
    d = json.loads(json.dumps(p.a_dict()))
    genero.poner("h")
    app.empezar_partida(d)
    j = robot.p.j
    assert (j.personaje, j.nombre, j.apellido, j.genero) == ("propio", "Lía", "Del Mar", "m") and genero.actual == "m" and robot.p.nivel("conduccion") == 5
    genero.poner("h")


def test_el_personaje_propio_no_puede_hacer_trampas():
    pj = vida.personaje_propio("  <b>ana-maría</b>99  ", "", "x", {"conduccion": 9, "punteria": 9, "resistencia": 9, "pesca": 9}, "no existe")
    assert pj["nombre"] == "Bana-maríab"                                                    # solo letras, espacios y guiones
    assert all(c.isalpha() or c in " -'" for c in pj["nombre"]) and len(pj["nombre"]) <= vida.MAX_NOMBRE
    assert pj["genero"] == "h" and pj["apellido"] == ""
    assert sum(pj.get(h, 0) for h in vida.HAB_NOMBRE) == vida.PUNTOS and max(pj.get(h, 0) for h in vida.HAB_NOMBRE) == vida.MAX_NIVEL
    assert "dinero" not in pj and "arma" not in pj and pj["botiquines"] == 1                # una ventaja que no existe no da nada
    assert vida.personaje_propio("", "", "m")["nombre"] == "Dani"                           # sin nombre, el de siempre
    assert vida.limpiar_nombre("x" * 80) == "X" + "x" * (vida.MAX_NOMBRE - 1) and vida.limpiar_nombre("123") == ""
    # las ventajas, una sola y como las de los personajes de la lista
    assert [v[0] for v in vida.VENTAJAS][:2] == ["ninguna", "ahorros"] and len({v[0] for v in vida.VENTAJAS}) == len(vida.VENTAJAS) >= 5
    fuerte = vida.personaje_propio("Eva", "Ruiz", "m", {"resistencia": 3}, "fortaleza")
    assert fuerte["salud_max"] == 120 and fuerte["botiquines"] == 2 and fuerte["resistencia"] == 3 and fuerte["genero"] == "m"


def test_el_personaje_propio_en_la_partida(robot):
    robot.nueva_partida()
    app = robot.app
    app.empezar_partida(None, personaje=vida.personaje_propio("Eva", "", "m", {"punteria": 4}, "navaja"))
    robot.saltar_dialogos()
    p = robot.p
    j = p.j
    assert (j.nombre, j.apellido, j.genero, p.nivel("punteria")) == ("Eva", "", "m", 4) and "navaja" in j.armas and j.objetos["botiquin"] == 2
    assert p.txt("Dani Roca al aparato.") == "Eva al aparato."                              # sin apellido no queda un hueco
    from juego import menus_vida
    menus_vida.carrera(p)
    assert app.pila[-1].opciones[0].texto.startswith("Eva. Día")
    app.cerrar()
    # lo que se le cuenta a un modelo de conversación también lo sabe
    from juego import ia
    f = {"nombre": "Paco", "genero": "h", "edad": 50, "oficio": "tendero", "caracter": "amable", "confianza": 10}
    sit = ia._situacion(p, None, f)
    assert sit["jugador"]["es"] == "una mujer" and "[" not in json.dumps(sit, ensure_ascii=False)
    genero.poner("h")
