"""Trabajo 1.7.1, tanda 9: la reconquista. Jugando sin conexión, las bandas vencidas se rehacen e intentan recuperar tus
barrios: cuándo empieza, cómo crecen, a dónde van, cómo te enteras, cómo se defiende, qué se pierde y cómo se previene."""
import json
import os
import random

import pygame
import pytest

from juego import config, gente as G, mundo as M, pactos as PA, reconquista as RQ, rutas, sintesis
from juego.menus import Menu

AJ = RQ.AJ
LEALES = "Los Calaveras"            # la banda del barrio del puerto, según los datos


@pytest.fixture
def datos_de_serie():
    """Deja los números y las frases como vienen en los datos, por si una prueba los ha cambiado."""
    yield
    M.cargar_datos()


class _Azar:
    """Un azar que no lo es: siempre lo primero y siempre lo más bajo."""

    def random(self):
        return 0.0

    def choice(self, lista):
        return lista[0]

    def uniform(self, a, b):
        return a

    def randint(self, a, b):
        return a


class _Medio(_Azar):
    """Ni suerte ni desgracia: el punto medio de todo."""

    def uniform(self, a, b):
        return (a + b) / 2.0

    def random(self):
        return 0.99


def _empezar(robot, nivel="normal", **opciones):
    p = robot.nueva_partida()
    for k, v in dict(sucesos=False, patrullas_calle=False, ambulancias=False, charla_peatones="nada", reconquista=nivel, **opciones).items():
        p.cfg[k] = v
    p.t_evento = 1e9
    _vaciar(p)
    return p


def _vaciar(p):
    for v in [v for v in p.vehiculos if v is not p.j.veh]:
        p.quitar_vehiculo(v)
    p.personas = []
    p.t_poblar = 1e9


def _oir(p):
    sonados = []
    original = p.son

    def son(nombre, xy=None, **kw):
        sonados.append(nombre)
        return original(nombre, xy=xy, **kw)
    p.son = son
    return sonados


def _texto(o):
    return o.texto() if callable(o.texto) else o.texto


def _opcion(m, contiene):
    return next(o for o in m.opciones if contiene in _texto(o))


def _elegir(robot, contiene):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if contiene in _texto(o))
    robot.tecla(pygame.K_RETURN)
    return m


def _cerrar_menus(robot):
    while robot.app.pila[-1] is not robot.p:
        robot.app.cerrar(robot.app.pila[-1])


def _ciudad(p, mapa="puerto_bravo"):
    """Te quedas con todos los barrios de una ciudad."""
    for b in p.mapas[mapa].barrios:
        if b["id"] not in p.j.territorios:
            p.j.territorios.append(b["id"])
    return [b["id"] for b in p.mapas[mapa].barrios]


def _en_marcha(p, mapa="puerto_bravo"):
    """Todos los barrios de una ciudad, el aviso ya dado y la calma pasada: la reconquista, funcionando."""
    barrios = _ciudad(p, mapa)
    p.reconquista_revisar()
    r = p.rec()
    r["calma"] = p.dia - 1
    for n in G.nombres_bandas():
        p.rec_banda(n).update(fuerza=0.0, umbral=50.0)
    return r, barrios


def _a_barrio(p, bid, dentro=True):
    """Lleva al jugador, a pie, a un punto de ese barrio (o a uno de otro)."""
    if p.j.veh:
        p.salir_vehiculo(forzado=True)
    for l in p.mundo.lugares.values():
        if (p.mundo.barrio(l.x, l.y)["id"] == bid) == dentro and l.tipo not in ("salida", "embarcadero"):
            x, y = p.mundo.punto_libre(l.x + 3, l.y)
            if (p.mundo.barrio(x, y)["id"] == bid) == dentro:
                p.j.x, p.j.y = x, y
                return l
    raise AssertionError(bid)


def _asalto(p, bid, bandas=(LEALES,), fuerza=50.0, estado="en_curso", horas=12.0, dia=None, sabido=0):
    mapa, b = p.rec_buscar(bid)
    a = {"barrio": bid, "nombre": b["nombre"], "mapa": mapa.id, "ciudad": mapa.nombre, "bandas": list(bandas), "fuerza": float(fuerza),
         "dia": p.dia if dia is None else dia, "hora": 12, "motivo": "antiguo", "estado": estado, "sabido": 3 if estado == "en_curso" else sabido,
         "quedan": horas * 60.0, "plazo": horas * 60.0, "gracia": False, "avisos": []}
    p.rec()["asalto"] = a
    return a


def _ganar_guerra(robot, p, tope=40):
    """Tumba oleada tras oleada hasta que la pelea se acaba."""
    for _ in range(tope):
        g = p.guerra
        if not g:
            return True
        if any(not e.muerto for e in g["vivos"]):
            for v in list(g["veh"]):
                if getattr(v, "pasajeros", None):
                    p.bajar_enemigos(v)
            for e in list(g["vivos"]):
                if not e.muerto:
                    p.danar_persona(e, 9999)
            robot.frames(2)
        else:
            g["t"] = 0.0
            robot.frames(2)
    return p.guerra is None


# ====================================================================== cuándo empieza
def test_empieza_al_conquistar_el_ultimo_barrio_con_dias_de_calma_y_un_aviso(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    son = _oir(p)
    barrios = [b["id"] for b in p.mundo.barrios]
    # con pocos barrios no pasa nada, ni se crea estado
    j.territorios = barrios[:3]
    p.reconquista_revisar()
    for _ in range(5):
        p.dia += 1
        p.dia_reconquista()
    assert p.rec_fase() == "" and not p.rec_activa() and not j.reconquista.get("v") and "amenaza_barrio" not in son
    # con muchos sin tenerlos todos: la versión suave, con su aviso
    assert len(barrios) > AJ.entero("suave_barrios")
    j.territorios = barrios[:AJ.entero("suave_barrios")]
    p.reconquista_revisar()
    r = p.rec()
    assert p.rec_fase() == "suave" and r["fase"] == "suave" and r["visto"] and "amenaza_barrio" in son
    assert AJ("calma_min") <= r["calma"] - p.dia <= AJ("calma_max")
    dicho = robot.dicho()
    assert f"Tienes ya {AJ.entero('suave_barrios')} barrios" in dicho and "Defensa de tus barrios" in dicho and "Opciones, La calle" in dicho and "de calma" in dicho
    # al conquistar el último de la ciudad: calma otra vez, y ya en serio. El aviso largo no se repite
    n = len(robot.app.voz.registro)
    del son[:]
    p.dia += 10
    j.territorios = list(barrios)
    p.reconquista_revisar()
    assert r["fase"] == "plena" and AJ("calma_min") <= r["calma"] - p.dia <= AJ("calma_max")
    nuevo = " | ".join(robot.app.voz.registro[n:])
    assert "Has conquistado todos los barrios de Puerto Bravo" in nuevo and "de calma" in nuevo and "informantes" not in nuevo
    p.reconquista_revisar()
    assert len(robot.app.voz.registro) == n + 1                    # y no lo repite
    # durante la calma, nadie crece ni trama nada
    for nombre in G.nombres_bandas():
        p.rec_banda(nombre)["fuerza"] = 10.0
    calma = r["calma"]
    while p.dia < calma:
        p.dia += 1
        p.dia_reconquista()
        assert r["asalto"] is None and all(p.rec_banda(x)["fuerza"] == 10.0 for x in G.nombres_bandas())
    p.dia += 1
    p.dia_reconquista()
    assert all(p.rec_banda(x)["fuerza"] > 10.0 for x in G.nombres_bandas())
    # con todas las ciudades, la fase más alta
    for m in p.mapas.values():
        if m.tipo == "ciudad":
            _ciudad(p, m.id)
    assert p.rec_fase() == "mundo"
    # y se llega también jugando: el juego lo mira solo cada poco
    p.cfg["reconquista"] = "normal"
    j.reconquista.clear()
    j.territorios = list(barrios)
    robot.frames(80)
    assert j.reconquista.get("fase") == "plena" and j.reconquista["visto"]


def test_una_partida_antigua_que_ya_lo_tenia_todo_carga_con_calma_y_un_aviso_una_sola_vez(robot, datos_de_serie):
    from juego.partida import Partida
    p = _empezar(robot)
    _ciudad(p)
    p.dia = 40
    d = json.loads(json.dumps(p.a_dict()))
    d["jugador"].pop("reconquista", None)                         # como la guardó una versión anterior
    p2 = Partida(robot.app, d)
    assert p2.j.reconquista == {} and p2._rec_cargada and p2.dia == 40
    n = len(robot.app.voz.registro)
    p2.reconquista_revisar()
    r = p2.rec()
    assert r["fase"] == "plena" and r["calma"] == 40 + AJ.entero("calma_carga") and r["visto"] and r["asalto"] is None
    dicho = " | ".join(robot.app.voz.registro[n:])
    assert "desde esta versión" in dicho and "Defensa de tus barrios" in dicho and f"{AJ.entero('calma_carga')} días de calma" in dicho
    assert all(p2.rec_barrio(b)["lealtad"] == AJ("lealtad_inicial") and p2.rec_barrio(b)["guardia"] == 0 for b in p2.j.territorios)
    # se guarda ya avisada: al volver a cargar no lo repite ni vuelve a empezar la calma
    p2.dia = 50
    d2 = json.loads(json.dumps(p2.a_dict()))
    p3 = Partida(robot.app, d2)
    n = len(robot.app.voz.registro)
    p3.reconquista_revisar()
    assert not p3._rec_cargada and p3.rec()["calma"] == 43 and len(robot.app.voz.registro) == n
    # una partida antigua sin barrios no avisa de nada
    d["jugador"]["territorios"] = []
    p4 = Partida(robot.app, d)
    p4.reconquista_revisar()
    assert not p4._rec_cargada and not p4.j.reconquista.get("v")


# ====================================================================== bandas que se rehacen
def test_la_fuerza_de_las_bandas_crece_cada_dia_segun_la_intensidad(robot, datos_de_serie):
    p = _empezar(robot)
    r, barrios = _en_marcha(p)
    AJ.n["umbral_min"] = AJ.n["umbral_max"] = 1000                 # que nadie llegue a atacar: aquí solo se mira crecer
    for n in G.nombres_bandas():
        p.rec_banda(n)["umbral"] = 1000.0
    crecido = {}
    for nivel in ("tranquilo", "normal", "duro"):
        p.cfg["reconquista"] = nivel
        for n in G.nombres_bandas():
            p.rec_banda(n).update(fuerza=0.0, moral=0.0)
        rng = random.Random(5)
        for _ in range(6):
            p.dia += 1
            p.dia_reconquista(rng)
        fuerzas = [p.rec_banda(n)["fuerza"] for n in G.nombres_bandas()]
        ritmo = AJ(f"ritmo_{nivel}") / 100.0
        assert all(6 * AJ("crece_min") * ritmo - 0.5 <= f <= 6 * AJ("crece_max") * ritmo + 0.5 for f in fuerzas), (nivel, fuerzas)
        assert len(set(fuerzas)) > 1                               # con azar: no todas igual
        crecido[nivel] = sum(fuerzas)
    assert crecido["tranquilo"] < crecido["normal"] < crecido["duro"]
    # quien te paga tributo no se rehace; la desmantelada, tampoco; con tregua, o si te respeta, a medias; con moral, más deprisa
    p.cfg["reconquista"] = "normal"
    bandas = G.nombres_bandas()
    for n in bandas:
        p.rec_banda(n).update(fuerza=0.0, moral=0.0)
    p.j.tributos[bandas[0]] = {"euros": 100, "hasta": p.dia + 50}
    p.rec_banda(bandas[1])["fuera"] = p.dia + 50
    p.rec_banda(bandas[2])["tregua"] = p.dia + 50
    p.rec_banda(bandas[3])["moral"] = 50.0
    PA.AJ.n["tregua_rompe_prob"] = 0
    p.dia += 1
    p.dia_reconquista(_Medio())
    f = [p.rec_banda(n)["fuerza"] for n in bandas]
    medio = (AJ("crece_min") + AJ("crece_max")) / 2.0
    assert f[0] == 0 and f[1] == 0 and f[2] == pytest.approx(medio / 2, abs=0.1) and f[4] == pytest.approx(medio, abs=0.1) and f[3] > f[4] * 1.3
    # en la fase suave, a medio gas; con todas las ciudades, algo más
    p.j.territorios = barrios[:AJ.entero("suave_barrios")]
    p.reconquista_revisar()
    p.rec_banda(bandas[4])["fuerza"] = 0.0
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert r["fase"] == "suave" and p.rec_banda(bandas[4])["fuerza"] == pytest.approx(medio * AJ("suave_ritmo") / 100.0, abs=0.1)
    # la fuerza no pasa de 100
    p.rec_banda(bandas[4])["fuerza"] = 99.0
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert p.rec_banda(bandas[4])["fuerza"] == 100.0


def test_a_que_barrio_van_su_antiguo_barrio_el_peor_defendido_el_mas_abandonado_o_el_mas_rentable(robot, datos_de_serie):
    p = _empezar(robot)
    r, barrios = _en_marcha(p)
    j = p.j
    AJ.n["peso_azar"] = 0
    # su antiguo barrio: el puerto es de Los Calaveras en los datos
    mapa, b, motivo = p.rec_elegir_objetivo(LEALES, _Azar())
    assert b["id"] == "puerto" and motivo == "antiguo" and p.rec_origen(b, mapa) == LEALES
    # y el que una banda te quitó y recuperaste, de esa banda
    otro = next(x for x in barrios if x != "puerto")
    p.rec_barrio(otro)["de"] = "Los Cuervos"
    assert p.rec_elegir_objetivo("Los Cuervos", _Azar())[1]["id"] == otro
    p.rec_barrio(otro)["de"] = ""
    # sin antiguo barrio que valga: el más abandonado
    AJ.n["peso_antiguo"] = 0
    dejado = barrios[2]
    p.rec_barrio(dejado)["lealtad"] = 5.0
    mapa, b, motivo = p.rec_elegir_objetivo(LEALES, _Azar())
    assert b["id"] == dejado and motivo == "abandono"
    p.rec_barrio(dejado)["lealtad"] = AJ("lealtad_inicial")
    # el peor defendido: todos con guardia y refuerzos menos uno
    for x in barrios:
        p.rec_barrio(x).update(guardia=3, refuerzo=3)
    flojo = barrios[1]
    p.rec_barrio(flojo).update(guardia=0, refuerzo=0)
    mapa, b, motivo = p.rec_elegir_objetivo(LEALES, _Azar())
    assert b["id"] == flojo and motivo == "defensa" and p.rec_defensa(flojo) < p.rec_defensa(barrios[0])
    # el más rentable: aquel en el que tienes negocios
    for x in barrios:
        p.rec_barrio(x).update(guardia=0, refuerzo=0)
    AJ.n["peso_defensa"] = AJ.n["peso_abandono"] = 0
    negocio = next(l for l in p.mundo.lugares.values() if l.tipo == "negocio" and int(l.get("ingresos", 0)) > 0)
    rico = p.mundo.barrio(negocio.x, negocio.y)["id"]
    j.propiedades.append(negocio.id)
    mapa, b, motivo = p.rec_elegir_objetivo(LEALES, _Azar())
    assert b["id"] == rico and motivo == "rentable" and p.rec_renta(b, mapa) == p.precio("tributo_territorio", 300) + int(negocio.get("ingresos", 0))
    # con azar, no siempre el mismo
    M.cargar_datos()
    AJ.n["peso_azar"] = 200
    rng = random.Random(3)
    assert len({p.rec_elegir_objetivo(LEALES, rng)[1]["id"] for _ in range(40)}) > 2


def test_una_banda_con_fuerza_bastante_prepara_un_asalto_y_solo_uno(robot, datos_de_serie):
    p = _empezar(robot)
    r, barrios = _en_marcha(p)
    AJ.n["alianza_prob"] = 0
    AJ.n["crece_min"] = AJ.n["crece_max"] = 0.001
    p.rec_banda(LEALES).update(fuerza=70.0, umbral=50.0)
    p.rec_banda("Los Cuervos").update(fuerza=60.0, umbral=50.0)
    hoy = p.dia + 1
    p.dia = hoy
    p.dia_reconquista(_Azar())
    a = r["asalto"]
    assert a and a["estado"] == "prepara" and a["bandas"] == [LEALES] and a["barrio"] == "puerto" and a["motivo"] == "antiguo"
    assert a["dia"] - hoy == AJ.entero("prepara_min") and AJ("hora_min") <= a["hora"] <= AJ("hora_max") and a["plazo"] == AJ("plazo_normal") * 60
    assert a["fuerza"] == pytest.approx(70.0 * AJ("fuerza_normal") / 100.0, abs=0.5)
    # mientras se prepara uno, nadie prepara otro
    p.dia += 1
    p.dia_reconquista(_Azar())
    assert r["asalto"] is a
    # un pacto de paz de los de siempre, o el descanso, también lo impiden
    r["asalto"] = None
    p.j.pacto_hasta = p.dia + 3
    p.dia += 1
    p.dia_reconquista(_Azar())
    assert r["asalto"] is None
    p.j.pacto_hasta = 0
    r["descanso"] = p.dia + 2
    p.dia += 1
    p.dia_reconquista(_Azar())
    assert r["asalto"] is None
    p.dia += 2
    p.dia_reconquista(_Azar())
    assert r["asalto"] is not None
    # la intensidad cambia el plazo y la fuerza con la que llegan
    for nivel in ("tranquilo", "duro"):
        r["asalto"], r["descanso"] = None, 0
        p.cfg["reconquista"] = nivel
        p.rec_banda(LEALES).update(fuerza=70.0, umbral=50.0)
        p.dia += 1
        p.dia_reconquista(_Azar())
        assert r["asalto"]["plazo"] == AJ(f"plazo_{nivel}") * 60 and r["asalto"]["fuerza"] == pytest.approx(70.0 * AJ(f"fuerza_{nivel}") / 100.0, abs=1.0)
    assert AJ("plazo_tranquilo") > AJ("plazo_normal") > AJ("plazo_duro") and AJ("descanso_tranquilo") > AJ("descanso_normal") > AJ("descanso_duro")


# ====================================================================== avisos
def _planear(p, r, informantes=0, lealtad=None, prepara=3):
    r["asalto"], r["descanso"], r["informantes"] = None, 0, informantes
    AJ.n["prepara_min"] = AJ.n["prepara_max"] = prepara
    AJ.n["alianza_prob"] = 0
    AJ.n["crece_min"] = AJ.n["crece_max"] = 0.001
    p.rec_banda(LEALES).update(fuerza=70.0, umbral=50.0)
    if lealtad is not None:
        p.rec_barrio("puerto")["lealtad"] = lealtad
    for bid in p.j.territorios:
        p.rec_barrio(bid)["pisado"] = p.dia + 100                 # que la lealtad no baje sola durante la prueba
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    return r["asalto"], n


def robot_voz(p):
    return p.app.voz.registro


def _desde(p, n):
    return " | ".join(robot_voz(p)[n:])


def test_los_avisos_dependen_de_los_informantes_y_de_la_lealtad_del_barrio(robot, datos_de_serie):
    p = _empezar(robot)
    r, barrios = _en_marcha(p)
    p.j.dinero = 10 ** 6
    son = _oir(p)
    # con los mejores informantes: mensaje al móvil en cuanto lo deciden, con todo
    a, n = _planear(p, r, informantes=3, lealtad=10)
    dicho = _desde(p, n)
    assert a["sabido"] == 3 and LEALES in dicho and "El Puerto" in dicho and "dentro de 3 días" in dicho and f"las {a['hora']}" in dicho
    assert str(int(a["fuerza"])) in dicho and "Quieren recuperar el que fue su barrio" in dicho and "amenaza_barrio" in son
    assert p.rec_amenaza_txt("puerto").startswith(f"{LEALES} lo asaltará dentro de 3 días")
    # de nivel 2: chivatazo dos días antes, con la banda y el barrio, sin la hora
    a, n = _planear(p, r, informantes=2, lealtad=10)
    assert a["sabido"] == 0 and LEALES not in _desde(p, n)
    assert p.rec_amenaza_txt("puerto").startswith("alta")           # pero mirar, se puede mirar siempre: algo se nota
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    dicho = _desde(p, n)
    assert a["sabido"] == 2 and LEALES in dicho and "El Puerto" in dicho and "dentro de 2 días" in dicho and "hacia las" not in dicho
    assert p.rec_amenaza_txt("puerto") == f"{LEALES} prepara un asalto para dentro de 2 días"
    # de nivel 1: el rumor, un día antes, con el barrio y sin la banda
    a, n = _planear(p, r, informantes=1, lealtad=10)
    p.dia += 1
    p.dia_reconquista(_Azar())
    assert a["sabido"] == 0
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    dicho = _desde(p, n)
    assert a["sabido"] == 1 and "El Puerto" in dicho and "mañana" in dicho and LEALES not in dicho
    # sin informantes y con el barrio descuidado: nada hasta el mismo día, y entonces, a veces, un rumor vago
    AJ.n["rumor_prob"] = 100
    a, n = _planear(p, r, informantes=0, lealtad=10)
    for _ in range(2):
        p.dia += 1
        p.dia_reconquista(_Azar())
    assert a["sabido"] == 0 and "El Puerto" not in _desde(p, n) and "rumorea" not in _desde(p, n)
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    dicho = _desde(p, n)
    assert a["dia"] == p.dia and a["sabido"] == 0 and "alguna banda prepara algo" in dicho and "El Puerto" not in dicho and LEALES not in dicho
    # o ni eso
    AJ.n["rumor_prob"] = 0
    a, n = _planear(p, r, informantes=0, lealtad=10)
    for _ in range(3):
        p.dia += 1
        p.dia_reconquista(_Medio())
    assert a["dia"] == p.dia and _desde(p, n) == ""
    # pero al empezar el asalto te enteras SIEMPRE, con su sonido, quién, dónde y cuánto tiempo tienes
    del son[:]
    p.reloj = a["hora"] * 60.0 - 1.0
    n = len(robot_voz(p))
    robot.frames(90)
    dicho = _desde(p, n)
    assert a["estado"] == "en_curso" and a["sabido"] == 3 and "amenaza_barrio" in son
    assert LEALES in dicho and "El Puerto" in dicho and f"Tienes {AJ.entero('plazo_normal')} horas" in dicho and "envía a tu gente" in dicho and "Si no haces nada, lo pierdes" in dicho
    assert p.rec_amenaza_txt("puerto").startswith("¡asalto en curso")
    assert p.objetivo_txt().startswith(f"{LEALES} está asaltando El Puerto. Te quedan {AJ.entero('plazo_normal')} horas")       # la tecla O
    assert "lo está asaltando" in p.barrio_dueno_txt(next(b for b in p.mundo.barrios if b["id"] == "puerto"))
    # sin pagar a nadie: un barrio que te es leal te avisa él. Con 75 de lealtad, como el chivatazo; con 50, como el rumor
    for bid in barrios:
        p.rec_barrio(bid)["lealtad"] = 100.0
    a, n = _planear(p, r, informantes=0, lealtad=80)
    assert a["barrio"] == "puerto"
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    assert p.rec_calidad_aviso("puerto") == 2 and a["sabido"] == 2 and LEALES in _desde(p, n)
    p.rec_barrio("puerto")["lealtad"] = 55
    assert p.rec_calidad_aviso("puerto") == 1
    # contratar informantes con el asalto ya preparado te lo cuenta en el acto
    a, n = _planear(p, r, informantes=0, lealtad=10)
    dinero = p.j.dinero
    for _ in range(3):
        p.rec_informantes(1)
    assert r["informantes"] == 3 and a["sabido"] == 3 and p.j.dinero == dinero - 3 * AJ.entero("informante_coste")


# ====================================================================== el asalto
def test_un_asalto_se_defiende_en_persona_por_oleadas_aunque_el_modo_de_guerra_este_apagado(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    assert p.cfg["guerra_calle"] is False and not p.guerra_activa()
    j.banda, j.banda_nombre = 2, "Los Mirlos"
    p.rec_banda(LEALES).update(fuerza=50.0, derrotas=0)
    a = _asalto(p, "puerto", fuerza=50.0)
    son = _oir(p)
    _a_barrio(p, "puerto", dentro=False)
    robot.frames(10)
    assert p.guerra is None                                        # fuera del barrio no empieza nada
    _a_barrio(p, "puerto")
    quedan = a["quedan"]
    robot.frames(5)
    g = p.guerra
    oleadas, base = p.rec_plan_persona()
    assert g and g["rec"] and g["tipo"] == "defensa" and g["barrio"] == "puerto" and g["banda"] == LEALES and g["total"] == oleadas == AJ.entero("oleadas") and g["base"] == base
    assert "Defiendes El Puerto" in p.objetivo_txt()
    assert sum(1 for e in p.personas if e.tipo == "aliado" and getattr(e, "de_banda", False)) == 2      # tu banda acude
    robot.frames(60)
    assert a["quedan"] == quedan - 5 / 30 / 2 or a["quedan"] > quedan - 0.2      # mientras peleas, el plazo no corre
    dinero, rep, lealtad = j.dinero, j.reputacion, p.rec_barrio("puerto")["lealtad"]
    assert _ganar_guerra(robot, p)
    assert r["asalto"] is None and "puerto" in j.territorios and "barrio_defendido" in son
    assert j.stats["asaltos_rechazados"] == 1 and j.stats["defensas"] == 1 and j.dinero >= dinero + AJ("premio_defensa") and j.reputacion >= rep
    assert p.rec_barrio("puerto")["lealtad"] == min(100, lealtad + AJ("lealtad_defensa"))
    b = p.rec_banda(LEALES)
    assert b["fuerza"] == pytest.approx(50.0 * AJ("fuerza_tras_perder") / 100.0, abs=0.2) and b["derrotas"] == 1 and b["moral"] < 0
    assert AJ("descanso_normal") <= r["descanso"] - p.dia <= AJ("descanso_normal") + AJ("descanso_azar")
    assert "sigue siendo tuyo" in robot.dicho()
    # con más fuerza vienen más oleadas, y con buena defensa en el barrio, menos gente en cada una
    _asalto(p, "puerto", fuerza=95.0)
    assert p.rec_plan_persona() == (AJ.entero("oleadas") + 1, AJ.entero("oleada_base"))
    _asalto(p, "puerto", fuerza=30.0)
    p.rec_barrio("puerto").update(guardia=3, refuerzo=3)
    assert p.rec_plan_persona() == (AJ.entero("oleadas"), AJ.entero("oleada_base") - 1)
    p.cfg["reconquista"] = "duro"
    assert p.rec_plan_persona()[1] == AJ.entero("oleada_base")
    p.cfg["reconquista"] = "normal"
    # si te vas del barrio en mitad, la pelea se pierde pero el asalto sigue: se puede volver
    p.rec_barrio("puerto").update(guardia=0, refuerzo=0)
    a = _asalto(p, "puerto", fuerza=50.0)
    p.t_guerra_enfria = -99
    robot.frames(5)
    assert p.guerra and p.guerra["rec"]
    p.guerra_retirada()
    assert p.guerra is None and r["asalto"] is a and "puerto" in j.territorios and "envía a tu gente" in robot.dicho()
    robot.frames(10)
    assert p.guerra is None                                        # no vuelve a empezar al instante
    p.t_guerra_enfria = -99
    robot.frames(5)
    assert p.guerra and _ganar_guerra(robot, p) and r["asalto"] is None and "puerto" in j.territorios


def test_enviar_a_tu_gente_el_resultado_se_calcula_y_se_cuenta_con_sus_numeros(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    son = _oir(p)
    # sin asalto, o sin banda, no hay a quién enviar
    assert p.rec_enviar_gente()[0] is False
    a = _asalto(p, "puerto", fuerza=60.0)
    hecho, texto = p.rec_enviar_gente()
    assert not hecho and "No tienes a nadie" in texto and r["asalto"] is a
    # con gente: defensa del barrio más lo que suma cada uno, contra su fuerza, y la suerte
    j.banda, j.banda_nombre = 5, "Los Mirlos"
    base = p.rec_defensa("puerto")
    assert base == pytest.approx(AJ("lealtad_inicial") / 100 * AJ("defensa_lealtad") + 5 * AJ("defensa_banda"))
    poder = base + 5 * AJ("envio_banda")
    assert p.rec_posibilidades() == pytest.approx(RQ.probabilidad(poder - 60.0, AJ("envio_azar")))
    hecho, texto = p.rec_enviar_gente(_Medio())
    assert hecho and r["asalto"] is None and "puerto" in j.territorios and "barrio_defendido" in son
    for trozo in (f"una fuerza de 60", f"Tu defensa suma {int(round(poder))}", f"{int(round(base))} del barrio", "de los 5 que envías", "La suerte", f"Resultado: {int(round(poder))} contra 60"):
        assert trozo in texto, (trozo, texto)
    assert j.stats["asaltos_rechazados"] == 1 and j.stats.get("defensas", 0) == 0 and j.banda == 5
    assert texto.split(".")[0] in robot.dicho()
    # con poca gente contra muchos: se pierde, y se dice igual de claro
    del son[:]
    j.banda = 1
    a = _asalto(p, "puerto", fuerza=120.0)
    rep = j.reputacion
    AJ.n["baja_prob"] = 100
    hecho, texto = p.rec_enviar_gente(_Azar())
    assert hecho and "puerto" not in j.territorios and j.barrios_banda["puerto"] == LEALES and "barrio_perdido" in son and j.banda == 0
    assert "cae uno de los tuyos" in texto and "contra" in texto and j.reputacion <= rep and j.stats["barrios_perdidos"] == 1
    assert "Puedes reconquistarlo" in robot.dicho()
    # las posibilidades que dice el menú salen de la misma cuenta
    assert RQ.probabilidad(0, 15) == 0.5 and RQ.probabilidad(30, 15) == 1.0 and RQ.probabilidad(-30, 15) == 0.0 and 0.5 < RQ.probabilidad(10, 15) < 1.0
    ganadas = 0
    rng = random.Random(11)
    for _ in range(400):
        ganadas += 20 + rng.uniform(-15, 15) >= 10 + rng.uniform(-15, 15)
    assert abs(ganadas / 400 - RQ.probabilidad(10, 15)) < 0.08


def test_si_no_haces_nada_el_barrio_se_pierde_salvo_que_aguante_la_guardia(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    son = _oir(p)
    _a_barrio(p, "puerto", dentro=False)
    p.rec_banda(LEALES).update(fuerza=60.0, moral=0.0, derrotas=2)
    p.rec_barrio("puerto")["refuerzo"] = 2
    a = _asalto(p, "puerto", fuerza=60.0, horas=3.0)
    j.reputacion = 20.0
    # avisa cuando quedan dos horas y cuando queda media
    a["quedan"] = 120.2
    robot.frames(30)
    assert "2h" in a["avisos"] and "Quedan 2 horas para que El Puerto caiga" in robot.dicho()
    a["quedan"] = 30.2
    robot.frames(30)
    assert "30m" in a["avisos"]
    a["quedan"] = 0.2
    robot.frames(30)
    assert r["asalto"] is None and "puerto" not in j.territorios and j.barrios_banda["puerto"] == LEALES and "barrio_perdido" in son
    assert j.reputacion == 20.0 - AJ("fama_perdida") and "Nadie ha defendido El Puerto" in robot.dicho() and "Pierdes los" in robot.dicho()
    # la banda que gana se crece: conserva parte de su fuerza, gana moral y se le perdona una derrota
    b = p.rec_banda(LEALES)
    assert b["fuerza"] == pytest.approx(60.0 * AJ("fuerza_tras_ganar") / 100.0, abs=0.2) and b["moral"] == AJ("moral_gana") and b["derrotas"] == 1
    assert r["fase"] == "suave" and r["descanso"] > p.dia            # ya no tienes la ciudad entera
    st = p.rec_barrio("puerto")
    assert st["guardia"] == 0 and st["refuerzo"] == 1 and st["de"] == LEALES
    # el barrio es ahora de esa banda, se dice así, y se reconquista por la vía de siempre
    puerto = next(x for x in p.mundo.barrios if x["id"] == "puerto")
    assert p.banda_de_barrio(puerto) == LEALES and LEALES in p.barrio_dueno_txt(puerto)
    p.empezar_conquista(puerto)
    assert p.mision and p.mision["def"]["id"] == "conquista" and p.mision["def"]["banda"] == LEALES
    p.abandonar_mision()
    # con guardia fija y sin hacer nada: la guardia defiende sola, y se cuenta con números
    j.territorios.append("puerto")
    j.barrios_banda.pop("puerto", None)
    p.reconquista_revisar()
    r["calma"] = 0
    p.rec_barrio("puerto").update(guardia=3, refuerzo=3)
    AJ.n["envio_azar"] = 0
    del son[:]
    a = _asalto(p, "puerto", fuerza=30.0, horas=0.001)
    robot.frames(30)
    assert r["asalto"] is None and "puerto" in j.territorios and "barrio_defendido" in son and "defiende sola la guardia" in robot.dicho()
    a = _asalto(p, "puerto", fuerza=90.0, horas=0.001)
    robot.frames(30)
    assert "puerto" not in j.territorios and "defiende sola la guardia" in robot.dicho()


def test_ni_dormir_ni_una_mision_te_hacen_perder_un_barrio_de_golpe(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    _a_barrio(p, "puerto", dentro=False)
    AJ.n["crece_min"] = AJ.n["crece_max"] = 0.001
    gracia = AJ("gracia_horas") * 60.0
    # dormir ocho horas con doce por delante: pasan, sin más
    a = _asalto(p, "puerto", horas=12.0)
    p.pasar_horas(8, dormir=True)
    assert a["quedan"] == pytest.approx(4 * 60.0) and not a["gracia"]
    p.pasar_horas(0.5)                                             # un rato corto (un trayecto) pasa sin más, y no gasta el margen
    assert a["quedan"] == pytest.approx(3.5 * 60.0) and not a["gracia"]
    # dormir otra vez: tu gente aguanta, y al despertar te quedan unas horas, no cero. Se dice
    a["quedan"] = 6 * 60.0
    p.pasar_horas(8, dormir=True)
    assert a["quedan"] == gracia and a["gracia"] and "tu gente ha aguantado en El Puerto" in robot.dicho() and "puerto" in j.territorios
    robot.frames(5)
    assert r["asalto"] is a and "puerto" in j.territorios
    # pero solo una vez: si vuelves a dormirte, se acabó
    p.pasar_horas(8, dormir=True)
    assert a["quedan"] < 0 and "puerto" in j.territorios             # nada se pierde dentro del sueño...
    robot.frames(5)
    assert r["asalto"] is None and "puerto" not in j.territorios      # ...sino al despertar
    # un asalto que empieza mientras duermes (o en el hospital o el calabozo): al volver tienes al menos esas horas
    j.territorios.append("puerto")
    j.barrios_banda.pop("puerto", None)
    p.reconquista_revisar()
    r["calma"] = 0
    p.reloj = 23 * 60.0
    a = _asalto(p, "puerto", estado="prepara", dia=p.dia + 1, horas=AJ("plazo_normal"))
    a["hora"] = 2
    r["descanso"] = p.dia + 30
    p.pasar_horas(30)                                              # día y pico: el asalto empezó hace 27 horas
    assert a["estado"] == "prepara" and "puerto" in j.territorios
    robot.frames(3)
    assert a["estado"] == "en_curso" and a["quedan"] == pytest.approx(gracia, abs=1.0) and a["gracia"] and "Empezó mientras no estabas" in robot.dicho()
    # en mitad de una misión, el plazo no corre, y un asalto no empieza
    quedan = a["quedan"]
    p.iniciar_mision(dict(next(m for m in p.datos["misiones"] if m["id"] == "m01"), requiere=[]))
    robot.saltar_dialogos()
    assert p.mision
    robot.frames(120)
    p.pasar_horas(3)
    assert a["quedan"] == quedan
    b2 = dict(a, estado="prepara", dia=p.dia, hora=0)
    r["asalto"] = b2
    robot.frames(30)
    assert b2["estado"] == "prepara"
    p.abandonar_mision()
    robot.saltar_dialogos()
    _cerrar_menus(robot)
    robot.frames(5)
    assert b2["estado"] == "en_curso"


def test_dos_bandas_se_alian_para_un_golpe_grande_y_se_anuncia(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    AJ.n["alianza_prob"] = 100
    AJ.n["crece_min"] = AJ.n["crece_max"] = 0.001
    j.dinero = 10 ** 6
    r["informantes"] = 3
    p.rec_banda(LEALES).update(fuerza=70.0, umbral=50.0)
    p.rec_banda("Los Cuervos").update(fuerza=40.0)
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    a = r["asalto"]
    aliada = a["bandas"][1]
    assert len(a["bandas"]) == 2 and a["bandas"][0] == LEALES and aliada != LEALES
    assert a["fuerza"] == pytest.approx(70.0 + p.rec_banda(aliada)["fuerza"] * AJ("alianza_suma") / 100.0, abs=0.5)
    assert aliada in _desde(p, n) and ("aliado" in _desde(p, n) or "alianza" in _desde(p, n))
    # una banda sin fuerza bastante no vale de aliada
    r["asalto"], r["descanso"] = None, 0
    for nombre in G.nombres_bandas():
        p.rec_banda(nombre).update(fuerza=5.0)
    p.rec_banda(LEALES).update(fuerza=70.0, umbral=50.0)
    p.dia += 1
    p.dia_reconquista(_Azar())
    assert r["asalto"]["bandas"] == [LEALES]
    # el asalto de una alianza: se anuncia con las dos, trae una oleada más, y cada oleada es de una de las bandas
    p.rec_banda(aliada).update(fuerza=40.0, derrotas=0)
    p.rec_banda(LEALES).update(fuerza=50.0, derrotas=0)
    a = _asalto(p, "puerto", bandas=(LEALES, aliada), fuerza=50.0, estado="prepara")
    a["hora"] = 0
    n = len(robot_voz(p))
    _a_barrio(p, "puerto", dentro=False)
    robot.frames(3)
    assert a["estado"] == "en_curso" and LEALES in _desde(p, n) and aliada in _desde(p, n)
    assert p.rec_plan_persona()[0] == AJ.entero("oleadas") + 1
    _a_barrio(p, "puerto")
    robot.frames(5)
    g = p.guerra
    assert g and g["bandas"] == [LEALES, aliada]
    vistas = set()
    for _ in range(60):
        if not p.guerra:
            break
        vivos = [e for e in p.guerra["vivos"] if not e.muerto]
        if vivos:
            vistas.add(vivos[0].banda)
            for e in vivos:
                p.danar_persona(e, 9999)
        else:
            p.guerra["t"] = 0.0
        robot.frames(2)
    assert p.guerra is None and vistas == {LEALES, aliada} and "puerto" in j.territorios
    # al perder, las dos encajan la derrota
    assert p.rec_banda(LEALES)["derrotas"] == 1 and p.rec_banda(aliada)["derrotas"] == 1


# ====================================================================== defensa preventiva
def test_guardias_refuerzos_informantes_e_inversion_cuestan_y_suben_la_defensa(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    j.dinero = 20000
    bid = "puerto"
    d0 = p.rec_defensa(bid)
    # guardia fija: se paga el primer día al contratar, sube la defensa y tiene un tope
    for k in range(1, AJ.entero("guardia_max") + 1):
        assert "Contratado" in p.rec_guardia(bid, 1) and p.rec_barrio(bid)["guardia"] == k
    assert j.dinero == 20000 - 3 * AJ.entero("guardia_coste") and p.rec_defensa(bid) == pytest.approx(d0 + 3 * AJ("defensa_guardia"))
    assert "ya tiene" in p.rec_guardia(bid, 1) and p.rec_barrio(bid)["guardia"] == 3
    assert "Despides" in p.rec_guardia(bid, -1) and p.rec_barrio(bid)["guardia"] == 2
    # refuerzos: pago único, cada nivel más caro
    dinero = j.dinero
    assert p.rec_precio_refuerzo(bid) == AJ.entero("refuerzo_precio")
    p.rec_reforzar(bid)
    assert p.rec_precio_refuerzo(bid) == 2 * AJ.entero("refuerzo_precio")
    p.rec_reforzar(bid)
    p.rec_reforzar(bid)
    assert p.rec_barrio(bid)["refuerzo"] == 3 and j.dinero == dinero - 6 * AJ.entero("refuerzo_precio") and p.rec_precio_refuerzo(bid) == 0
    assert "al máximo" in p.rec_reforzar(bid)
    # informantes: por niveles
    for k in range(1, 4):
        assert f"nivel {k}" in p.rec_informantes(1)
    assert "No hay más" in p.rec_informantes(1) and r["informantes"] == 3
    p.rec_informantes(-1)
    assert r["informantes"] == 2
    # cada medianoche cobran guardias e informantes
    PA.AJ.n["tregua_rompe_prob"] = 0
    dinero = j.dinero
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert j.dinero == dinero - 2 * AJ.entero("guardia_coste") - 2 * AJ.entero("informante_coste") and "Pagas" in robot.dicho()
    # sin dinero: primero se van los informantes, luego los guardias, y en el barrio sienta mal
    j.dinero = 2 * AJ.entero("guardia_coste")
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert r["informantes"] == 0 and p.rec_barrio(bid)["guardia"] == 2 and j.dinero == 0 and "informantes" in robot.dicho()
    lealtad = p.rec_barrio(bid)["lealtad"]
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert p.rec_barrio(bid)["guardia"] == 0 and p.rec_barrio(bid)["lealtad"] == lealtad - AJ("lealtad_impago") and "se marchan" in robot.dicho()
    # si no llega para pagar a tu banda, también se nota en los barrios
    from juego import sistemas
    j.banda, j.banda_nombre, j.dinero = 2, "Los Mirlos", 0
    otra = p.rec_barrio(barrios[0])["lealtad"]
    sistemas.paga(p)
    assert j.banda == 1 and p.rec_barrio(barrios[0])["lealtad"] == otra - AJ("lealtad_impago")
    # y la gente de tu banda cuenta en la defensa de todos tus barrios
    j.banda = 0
    sin = p.rec_defensa(barrios[0])
    j.banda = 4
    assert p.rec_defensa(barrios[0]) == pytest.approx(sin + 4 * AJ("defensa_banda"))


def test_la_lealtad_baja_por_descuido_con_avisos_y_sube_al_visitar_defender_o_invertir(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    AJ.n["umbral_min"] = AJ.n["umbral_max"] = 1000
    for n in G.nombres_bandas():
        p.rec_banda(n)["umbral"] = 1000.0
    PA.AJ.n["tregua_rompe_prob"] = 0
    son = _oir(p)
    _a_barrio(p, "puerto", dentro=False)
    aqui = p.mundo.barrio(*p.pos())["id"]
    inicial = AJ("lealtad_inicial")
    for b in barrios:
        p.rec_barrio(b).update(lealtad=inicial, pisado=p.dia, visita=p.dia)
    # los primeros días sin pisarlo no pasa nada
    for _ in range(AJ.entero("lealtad_dias")):
        p.dia += 1
        p.dia_reconquista(_Medio())
    assert p.rec_barrio("puerto")["lealtad"] == inicial
    # después baja cada día; con guardia fija, la mitad
    assert barrios[0] == "puerto"
    p.rec_barrio(barrios[1])["guardia"] = 1
    j.dinero = 100000
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert p.rec_barrio("puerto")["lealtad"] == inicial - AJ("lealtad_baja") and p.rec_barrio(barrios[1])["lealtad"] == inicial - AJ("lealtad_baja") / 2
    # antes de que baje demasiado, avisa: una vez al cruzar cada listón, con el nombre del barrio
    p.rec_barrio(barrios[1])["guardia"] = 0
    for b in barrios:
        p.rec_barrio(b)["lealtad"] = 90.0
    p.rec_barrio("puerto")["lealtad"] = AJ("lealtad_aviso") + 1
    n = len(robot_voz(p))
    p.dia += 1
    p.dia_reconquista(_Medio())
    dicho = _desde(p, n)
    assert "El Puerto" in dicho and any(f.split("{")[0] in dicho for f in AJ.lista("frases_lealtad_aviso")) and dicho.count("El Puerto") == 1
    n = len(robot_voz(p))
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert "El Puerto" not in _desde(p, n)                          # no lo repite cada noche
    p.rec_barrio("puerto")["lealtad"] = AJ("lealtad_grave") + 1
    n = len(robot_voz(p))
    del son[:]
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert "El Puerto" in _desde(p, n) and "amenaza_barrio" in son and any(f.split("{")[0] in _desde(p, n) for f in AJ.lista("frases_lealtad_grave"))
    # nunca baja de cero, y por sí sola no te quita el barrio
    p.rec_barrio("puerto")["lealtad"] = 1.0
    for _ in range(4):
        p.dia += 1
        p.dia_reconquista(_Medio())
    assert p.rec_barrio("puerto")["lealtad"] == 0.0 and "puerto" in j.territorios
    # un barrio descuidado se defiende peor, y es el que eligen
    assert p.rec_defensa("puerto") < p.rec_defensa(barrios[1])
    # visitarlo: la primera vez de cada día sube; y pisarlo para la cuenta de días
    _a_barrio(p, "puerto")
    robot.frames(70)
    st = p.rec_barrio("puerto")
    assert st["lealtad"] == AJ("lealtad_visita") and st["pisado"] == p.dia
    robot.frames(70)
    assert st["lealtad"] == AJ("lealtad_visita")                    # una vez al día
    p.dia += 1
    robot.frames(70)
    assert st["lealtad"] == 2 * AJ("lealtad_visita")
    # invertir en el barrio: una vez al día
    dinero = j.dinero
    assert "Lealtad del barrio" in p.rec_invertir("puerto") and st["lealtad"] == 2 * AJ("lealtad_visita") + AJ("lealtad_inversion") and j.dinero == dinero - AJ.entero("inversion_precio")
    assert "Hoy ya has puesto dinero" in p.rec_invertir("puerto") and j.dinero == dinero - AJ.entero("inversion_precio")
    # defenderlo es lo que más une
    antes = st["lealtad"]
    _asalto(p, "puerto", fuerza=1.0)
    j.banda = 3
    p.rec_enviar_gente(_Medio())
    assert st["lealtad"] == antes + AJ("lealtad_defensa")
    assert aqui != "puerto"


def test_una_tregua_se_pacta_dura_unos_dias_y_se_puede_romper(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    j.dinero = 50000
    AJ.n["crece_min"] = AJ.n["crece_max"] = 0.001
    AJ.n["alianza_prob"] = 0
    b = p.rec_banda(LEALES)
    b.update(fuerza=70.0, umbral=50.0)
    assert p.tregua_motivo(LEALES) == ""
    si, euros, dias, frase = p.oferta_tregua(LEALES)
    assert si and euros >= 50 and PA.AJ("tregua_dias_min") <= dias <= PA.AJ("tregua_dias_max") and LEALES in frase and str(euros) in frase
    assert p.oferta_tregua(LEALES)[1] == euros                     # el mismo día, la misma cifra
    b["fuerza"] = 10.0
    assert p.oferta_tregua(LEALES)[1] < euros                      # a una banda deshecha le sale más barato
    b["fuerza"] = 70.0
    j.rep_bandas[LEALES] = -80.0
    assert p.oferta_tregua(LEALES)[0] is False                     # con quien te la tiene jurada no hay tregua
    j.rep_bandas[LEALES] = 0.0
    # estaban preparando un asalto: con la tregua, lo dejan
    a = _asalto(p, "puerto", estado="prepara", dia=p.dia + 2)
    assert p.pactar_tregua(LEALES, euros, dias) and j.dinero == 50000 - euros and b["tregua"] == p.dia + dias
    assert r["asalto"] is None and "lo dejan" in robot.dicho() and LEALES not in p._rec_listas()
    assert "Ya tienes una tregua" in p.tregua_motivo(LEALES) and "en tregua contigo" in p.rec_banda_txt(LEALES)
    hasta, b["tregua"] = b["tregua"], 0                            # y tras una respuesta hay que esperar unos días para volver a tratarlo
    assert "ya te contestó" in p.tregua_motivo(LEALES)
    b["tregua"] = hasta
    # mientras dura, esa banda no prepara nada, aunque le sobre fuerza
    PA.AJ.n["tregua_rompe_prob"] = 0
    for nombre in G.nombres_bandas():
        if nombre != LEALES:
            p.rec_banda(nombre)["fuerza"] = 0.0
    for _ in range(dias):
        p.dia += 1
        p.dia_reconquista(_Azar())
        assert r["asalto"] is None
    # se acaba el día acordado, y se dice
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    assert b["tregua"] == 0 and any(f.split("{")[0] in _desde(p, n) for f in PA.AJ.lista("frases_tregua_hecho") + AJ.lista("frases_tregua_fin"))
    assert r["asalto"] is not None and r["asalto"]["bandas"] == [LEALES]
    # la rompen ellos: se avisa, y no pueden golpear al día siguiente
    r["asalto"], r["descanso"] = None, 0
    j.tratos.clear()
    b["tregua"] = p.dia + 8
    PA.AJ.n["tregua_rompe_prob"] = 100
    son = _oir(p)
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    assert b["tregua"] == 0 and "amenaza_barrio" in son and any(f.split("{")[0] in _desde(p, n) for f in AJ.lista("frases_tregua_rota"))
    assert r["asalto"] is None and r["descanso"] >= p.dia + 2
    assert p.fuerza_propia() >= 30 and p.tregua_rompe_prob() == 100
    j.territorios = barrios[:1]                                    # y si pesas poco, el doble de fácil
    assert p.fuerza_propia() < 30 and p.tregua_rompe_prob() == 200
    j.territorios = list(barrios)
    # la rompes tú: un golpe a su escondite
    PA.AJ.n["tregua_rompe_prob"] = 0
    b.update(tregua=p.dia + 8, fuerza=70.0, golpe=-99)
    rep = p.rep_banda(LEALES)
    assert p.empezar_golpe(LEALES) and b["tregua"] == 0 and p.rep_banda(LEALES) == rep - 15 and "rompes la tregua" in robot.dicho()
    p.abandonar_mision()
    # desde el menú: la mesa, con aceptar, regatear y dejarlo
    j.tratos.clear()
    _cerrar_menus(robot)
    PA.menu_tregua(p, "Los Cuervos")
    mesa = robot.app.pila[-1]
    assert [_texto(x).split(":")[0] for x in mesa.opciones] == ["Aceptar", "Pedir una rebaja", "Dejarlo"]
    _elegir(robot, "Aceptar")
    assert p.rec_banda("Los Cuervos")["tregua"] > p.dia
    _cerrar_menus(robot)
    # y está también en Negociar con las bandas
    PA.menu_pactos(p)
    textos = [_texto(x) for x in robot.app.pila[-1].opciones]
    assert any(t.startswith("Tregua con Los Cuervos en vigor") for t in textos) and any(t.startswith(f"Pactar una tregua con {LEALES}") for t in textos)
    assert all(x.ayuda for x in robot.app.pila[-1].opciones[:-1])
    _cerrar_menus(robot)


def test_el_golpe_preventivo_hunde_a_una_banda_y_a_la_tercera_la_desmantela(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    son = _oir(p)
    b = p.rec_banda(LEALES)
    # una banda deshecha no tiene ni escondite
    b.update(fuerza=5.0, derrotas=0)
    assert "no tiene ni escondite" in p.golpe_motivo(LEALES) and not p.empezar_golpe(LEALES)
    j.estrellas = 1
    b["fuerza"] = 80.0
    assert "policía" in p.golpe_motivo(LEALES)
    j.estrellas = 0
    # preparaban un asalto: el golpe lo suspende
    _asalto(p, "puerto", estado="prepara", dia=p.dia + 2)
    assert p.golpe_motivo(LEALES) == "" and p.empezar_golpe(LEALES)
    ms = p.mision
    assert ms and ms["def"]["id"] == "golpe_preventivo" and LEALES in ms["def"]["titulo"] and ms["def"]["pasos"][0]["tipo"] == "eliminar"
    assert all(LEALES in g["tipo"] for paso in ms["def"]["pasos"] for g in paso.get("enemigos", []))
    dinero = j.dinero
    for _ in range(4):                                             # se juega entera, sea de la manera que sea
        ms = p.mision
        if not ms:
            break
        paso = ms["def"]["pasos"][ms["paso"]]
        l = p.lugares[paso["lugar"]]
        p.j.x, p.j.y = p.mundo.punto_libre(l.x + 3, l.y)
        robot.frames(4)
        if paso["tipo"] == "eliminar":
            for v in list(ms.get("veh_enemigos", [])):
                if getattr(v, "pasajeros", None):
                    p.bajar_enemigos(v)
            for e in list(ms["enemigos"]):
                p.danar_persona(e, 9999)
        else:
            o = ms["objeto"]
            p.j.x, p.j.y = o.x, o.y
            robot.tecla(pygame.K_RETURN)
        robot.frames(6)
        robot.saltar_dialogos()
    assert p.mision is None and b["fuerza"] == pytest.approx(80.0 * (1 - AJ("golpe_quita") / 100.0), abs=0.2) and b["derrotas"] == 1 and b["golpe"] == p.dia
    assert r["asalto"] is None and j.dinero >= dinero + AJ("golpe_paga") and j.stats["golpes_preventivos"] == 1 and "barrio_defendido" in son
    assert any(f.split("{")[0] in robot.dicho() for f in AJ.lista("frases_golpe_suspende"))
    # no se puede repetir contra la misma banda hasta pasados unos días
    b["fuerza"] = 80.0
    assert "se ha escondido bien" in p.golpe_motivo(LEALES)
    # cada vez, de una manera
    variantes = set()
    for k in range(40):
        p.dia += AJ.entero("golpe_espera")
        b["fuerza"] = 30.0 + (k % 3) * 30
        assert p.empezar_golpe(LEALES)
        variantes.add(p.mision["def"]["variante"])
        assert 3 <= sum(g["n"] for paso in p.mision["def"]["pasos"] for g in paso.get("enemigos", [])) <= 7
        p.abandonar_mision()
    assert {"directo", "vigias", "arsenal"} <= variantes
    # a la tercera derrota, desmantelada una temporada larga: ni crece ni ataca, y se dice hasta cuándo
    b.update(fuerza=60.0, derrotas=AJ.entero("derrotas_desmantela") - 1, moral=0.0)
    _asalto(p, "puerto", fuerza=10.0)
    j.banda = 6
    p.rec_enviar_gente(_Medio())
    assert AJ("desmantela_min") <= b["fuera"] - p.dia <= AJ("desmantela_max") and b["fuerza"] == 0 and b["derrotas"] == 0
    assert any(f.split("{")[0] in robot.dicho() for f in AJ.lista("frases_desmantelada")) and "desmantelada hasta el día" in p.rec_banda_txt(LEALES)
    assert LEALES not in p._rec_listas() and "desmantelada" in p.golpe_motivo(LEALES) and "desmantelada" in p.tregua_motivo(LEALES)
    r["descanso"] = 0
    AJ.n["crece_min"] = AJ.n["crece_max"] = 5
    PA.AJ.n["tregua_rompe_prob"] = 0
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert b["fuerza"] == 0
    # pasada la temporada, vuelve
    p.dia = b["fuera"] + 1
    p.dia_reconquista(_Medio())
    assert b["fuerza"] > 0


def test_siempre_queda_alguna_amenaza_llega_una_banda_forastera(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    AJ.n["forastera_prob"] = 100
    PA.AJ.n["tregua_rompe_prob"] = 0
    son = _oir(p)
    # con las bandas de la comarca en pie y poco tiempo, no viene nadie
    p.dia += 1
    p.dia_reconquista(_Medio())
    assert p.rec_nombres() == G.nombres_bandas()
    # desmanteladas casi todas: llega gente de fuera, con nombre propio, y se anuncia
    for nombre in G.nombres_bandas()[:-1]:
        p.rec_banda(nombre)["fuera"] = p.dia + 60
    p.dia += 1
    n = len(robot_voz(p))
    p.dia_reconquista(_Azar())
    nombres = p.rec_nombres()
    assert len(nombres) == len(G.nombres_bandas()) + 1
    fora = nombres[-1]
    assert fora in AJ.lista("forasteras") and r["bandas"][fora]["forastera"] and r["bandas"][fora]["fuerza"] >= AJ("forastera_fuerza") and fora in _desde(p, n)
    assert "amenaza_barrio" in son and "banda forastera" in p.rec_banda_txt(fora)
    # solo una a la vez
    p.dia += 1
    p.dia_reconquista(_Azar())
    assert len(p.rec_nombres()) == len(G.nombres_bandas()) + 1
    # ataca como las demás, y si gana se queda con el barrio y se llama por su nombre
    r["asalto"], r["descanso"] = None, 0
    _a_barrio(p, "puerto", dentro=False)
    a = _asalto(p, barrios[1], bandas=(fora,), fuerza=90.0, horas=0.001)
    robot.frames(30)
    b1 = next(x for x in p.mundo.barrios if x["id"] == barrios[1])
    assert barrios[1] not in j.territorios and p.banda_de_barrio(b1) == fora and fora in p.barrio_dueno_txt(b1)
    p.empezar_conquista(b1)                                         # y se le reconquista por la vía de siempre
    assert p.mision and p.mision["def"]["banda"] == fora
    p.abandonar_mision()
    # se puede pactar con ella y golpear su escondite
    j.dinero = 50000
    assert p.tregua_motivo(fora) == "" and p.oferta_tregua(fora)[0]
    r["bandas"][fora]["fuerza"] = 60.0
    assert p.golpe_motivo(fora) == ""
    # vencida varias veces, se marcha para siempre... y con el tiempo vendrá otra
    j.territorios.append(barrios[1])
    p.reconquista_revisar()                                        # recuperar el último barrio da calma otra vez; aquí se salta
    r["calma"] = 0
    r["bandas"][fora]["derrotas"] = AJ.entero("derrotas_desmantela") - 1
    _asalto(p, barrios[1], bandas=(fora,), fuerza=5.0)
    j.banda = 6
    p.rec_enviar_gente(_Medio())
    assert fora not in r["bandas"] and any(f.split("{")[0] in robot.dicho() for f in AJ.lista("frases_forastera_fin"))
    r["asalto"], r["descanso"] = None, 0
    p.dia += 1
    p.dia_reconquista(_Azar())
    otra = [x for x in p.rec_nombres() if x not in G.nombres_bandas()]
    assert len(otra) == 1 and otra[0] != fora


# ====================================================================== opción, intensidades, servidor
def test_la_opcion_de_serie_normal_y_apagada_no_ocurre_nada(robot, datos_de_serie):
    from juego import menus_extra, menus_juego, sistemas
    assert config.POR_DEFECTO["reconquista"] == "normal" and config.OPCIONES["reconquista"] == ["apagado", "tranquilo", "normal", "duro"] == list(RQ.NIVELES)
    p = _empezar(robot, nivel="apagado")
    j = p.j
    barrios = _ciudad(p)
    j.banda = 0
    # apagada: ni estado, ni aviso, ni asaltos; los ataques de siempre siguen como antes
    n = len(robot_voz(p))
    robot.frames(80)
    for _ in range(40):
        p.dia += 1
        p.dia_reconquista()
    assert p.rec_nivel() == "" and not p.rec_activa() and not j.reconquista.get("v") and _desde(p, n) == ""
    p.cfg["sucesos"] = True
    sistemas.sucesos_territorio(p, _Azar())
    assert j.amenaza and j.amenaza["banda"] == G.nombres_bandas()[0]
    j.amenaza = None
    menus_extra.territorios(p)
    textos = [_texto(o) for o in robot.app.pila[-1].opciones]
    assert not any("Defensa de tus barrios" in t or "Lealtad" in t for t in textos)
    _cerrar_menus(robot)
    assert "no está en marcha" in p.tregua_motivo(LEALES)
    # encendida: los asaltos los lleva la reconquista, y los ataques sueltos de siempre no salen (nunca dos a la vez)
    p.cfg["reconquista"] = "normal"
    assert p.rec_activa()
    sistemas.sucesos_territorio(p, _Azar())
    assert j.amenaza is None
    # con pocos barrios, todo como siempre
    j.territorios = barrios[:2]
    assert not p.rec_activa()
    sistemas.sucesos_territorio(p, _Azar())
    assert j.amenaza is not None
    j.amenaza = None
    # si se apaga con un asalto en curso, se queda parado: no corre el plazo ni se pierde nada
    j.territorios = list(barrios)
    p.reconquista_revisar()
    a = _asalto(p, "puerto", horas=0.001)
    p.cfg["reconquista"] = "apagado"
    _a_barrio(p, "puerto", dentro=False)
    robot.frames(60)
    assert p.rec()["asalto"] is a and "puerto" in j.territorios
    # en Opciones, en La calle, con sus cuatro valores y su explicación
    p.cfg["reconquista"] = "normal"
    _cerrar_menus(robot)
    menus_juego.opciones(robot.app)
    _elegir(robot, "La calle")
    calle = robot.app.pila[-1]
    o = _opcion(calle, "Las bandas intentan reconquistar tus barrios")
    assert _texto(o).endswith(": normal") and len(o.ayuda) > 300 and "Defensa de tus barrios" in o.ayuda and "servidor" in o.ayuda
    calle.i = calle.opciones.index(o)
    vistos = []
    for _ in range(4):
        robot.tecla(pygame.K_RIGHT)
        vistos.append(robot.app.cfg["reconquista"])
    assert vistos == ["duro", "apagado", "tranquilo", "normal"]
    robot.tecla(pygame.K_LEFT)
    assert robot.app.cfg["reconquista"] == "tranquilo" and "tranquilo" in _texto(o)
    robot.app.cfg["reconquista"] = "normal"


def test_en_un_servidor_y_jugando_con_amigos_no_ocurre(robot, datos_de_serie):
    from juego import menus_extra
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    p.rec_banda(LEALES).update(fuerza=90.0, umbral=50.0)
    a = _asalto(p, "puerto", horas=0.001)
    foto = json.dumps(j.reconquista, sort_keys=True)
    _a_barrio(p, "puerto", dentro=False)

    class _Red:
        conectado = True
        id = 1

        def enviar(self, *a, **k):
            pass

        def recibir(self):
            return []

        def cerrar(self):
            pass
    for caso in ("servidor", "amigos"):
        if caso == "servidor":
            p.en_servidor = True
        else:
            original = p.online_activo
            p.online_activo = lambda: True
        assert p.rec_nivel() == "" and not p.rec_activa(), caso
        for _ in range(10):
            p.dia_reconquista()
        p.actualizar_reconquista(5.0)
        p.rec_pasar_horas(40)
        assert json.dumps(j.reconquista, sort_keys=True) == foto and "puerto" in j.territorios, caso
        assert RQ.opciones_territorios(p, None) == ([], []) and p.rec_enviar_gente()[0] in (True, False)
        j.reconquista.clear()
        j.reconquista.update(json.loads(foto))
        j.territorios = list(barrios)
        j.barrios_banda.pop("puerto", None)
        if caso == "servidor":
            p.en_servidor = False
        else:
            p.online_activo = original
    assert p.rec_nivel() == "normal"
    # y el menú de Territorios de un servidor no lo ofrece
    p.en_servidor = True
    assert "Las treguas son cosa" in p.tregua_motivo(LEALES)
    p.en_servidor = False


# ====================================================================== guardado
def test_todo_el_estado_se_guarda_y_se_carga_con_la_partida(robot, datos_de_serie):
    from juego import menus_juego
    from juego.partida import Partida
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    j.dinero = 30000
    p.rec_guardia("puerto", 1)
    p.rec_guardia("puerto", 1)
    p.rec_reforzar(barrios[1])
    p.rec_informantes(1)
    p.rec_barrio(barrios[2])["lealtad"] = 33.0
    p.rec_banda(LEALES).update(fuerza=61.5, moral=12.0, derrotas=2, tregua=p.dia + 4)
    p.rec_banda("Los Cuervos").update(fuera=p.dia + 20)
    r["bandas"]["La Marea Negra"] = {"fuerza": 30.0, "moral": 0.0, "derrotas": 0, "fuera": 0, "tregua": 0, "golpe": -99, "umbral": 50.0, "forastera": True}
    a = _asalto(p, barrios[1], bandas=("Los Lagartos", "Los Barrenos"), fuerza=77.0, horas=5.5)
    r["descanso"], r["calma"] = p.dia + 3, p.dia - 1
    p._rec_parte("Una prueba.")
    foto = json.loads(json.dumps(j.reconquista))
    # por el archivo de verdad
    d = json.loads(json.dumps(p.a_dict()))
    p2 = Partida(robot.app, d)
    assert p2.j.reconquista == foto and not p2._rec_cargada
    assert p2.rec_barrio("puerto")["guardia"] == 2 and p2.rec_barrio(barrios[1])["refuerzo"] == 1 and p2.rec()["informantes"] == 1 and p2.rec_barrio(barrios[2])["lealtad"] == 33.0
    assert p2.rec_banda(LEALES)["tregua"] == p.dia + 4 and p2.rec_banda("Los Cuervos")["fuera"] == p.dia + 20 and "La Marea Negra" in p2.rec_nombres()
    a2 = p2.rec()["asalto"]
    assert a2 == a and a2 is not a and p2.rec_amenaza_txt(barrios[1]).startswith("¡asalto en curso de Los Lagartos y Los Barrenos")
    # una partida anterior, sin nada de esto, carga con los valores de serie
    d.pop("jugador")
    d["jugador"] = {k: v for k, v in json.loads(json.dumps(p.j.a_dict())).items() if k != "reconquista"}
    d["jugador"]["territorios"] = ["puerto"]
    p3 = Partida(robot.app, d)
    assert p3.j.reconquista == {} and p3.rec_fase() == "" and p3.rec_barrio("puerto") == {"lealtad": float(AJ("lealtad_inicial")), "guardia": 0, "refuerzo": 0, "pisado": p3.dia, "visita": 0, "inversion": 0, "de": ""}
    # y lo que guarda es JSON liso
    assert json.loads(json.dumps(p3.j.reconquista)) == p3.j.reconquista


# ====================================================================== menús, F1 y mando
def test_territorios_dice_el_estado_de_cada_barrio_y_abre_la_defensa_con_ayuda_en_todo(robot, datos_de_serie):
    from juego import menus_extra
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    j.dinero, j.banda, j.banda_nombre = 30000, 2, "Los Mirlos"
    menus_extra.territorios(p)
    m = robot.app.pila[-1]
    textos = [_texto(o) for o in m.opciones]
    propios = [t for t in textos if ": es tuyo." in t]
    assert len(propios) == len(barrios) and all("Lealtad" in t and "defensa" in t and "Amenaza: " in t for t in propios)
    o = _opcion(m, "Defensa de tus barrios")
    assert "nivel normal" in _texto(o) and len(o.ayuda) > 150
    assert all(x.ayuda for x in m.opciones if ": es tuyo." in _texto(x))
    _elegir(robot, "Defensa de tus barrios")
    d = robot.app.pila[-1]
    assert d.titulo == "Defensa de tus barrios" and all(x.ayuda for x in d.opciones[:-1])
    textos = [_texto(x) for x in d.opciones]
    assert textos[0].startswith("Reconquista, nivel normal") and sum(1 for t in textos if ", en Puerto Bravo: lealtad" in t) == len(barrios)
    assert any(t.startswith("Informantes: nivel 0 de 3") for t in textos) and sum(1 for t in textos if any(t.startswith(b + ":") for b in G.nombres_bandas())) == len(G.nombres_bandas())
    # F1 en la primera lo explica todo; Intro también lo dice
    d.i = 0
    robot.tecla(pygame.K_F1)
    assert "en persona" in robot.dicho() and "envía a tu gente" in robot.dicho() and "informantes" in robot.dicho().lower()
    robot.tecla(pygame.K_RETURN)
    assert "Nunca hay dos asaltos a la vez" in robot.dicho()
    # un barrio: guardia, refuerzo, invertir y GPS
    _elegir(robot, "El Puerto, en Puerto Bravo")
    mb = robot.app.pila[-1]
    assert "Lealtad" in mb.titulo and "Amenaza" in mb.titulo and all(x.ayuda for x in mb.opciones[:-1])
    _elegir(robot, "Guardia fija")
    assert p.rec_barrio("puerto")["guardia"] == 1 and "Guardia fija: 1 de 3" in _texto(mb.opciones[0])
    _elegir(robot, "Reforzar el barrio")
    assert p.rec_barrio("puerto")["refuerzo"] == 1
    _elegir(robot, "Invertir en el barrio")
    assert p.rec_barrio("puerto")["lealtad"] > AJ("lealtad_inicial")
    _elegir(robot, "Marcarlo en el GPS")
    assert robot.app.pila[-1] is p and p.gps is not None
    # informantes y partes
    RQ.menu_reconquista(p)
    d = robot.app.pila[-1]
    _elegir(robot, "Informantes: nivel 0")
    assert r["informantes"] == 1
    _elegir(robot, "Bajar un nivel de informantes")
    assert r["informantes"] == 0
    p._rec_parte("Chivatazo de prueba.")
    _elegir(robot, "Últimos partes")
    assert "Chivatazo de prueba" in robot.dicho()
    # una banda: golpe y tregua
    _elegir(robot, LEALES + ":")
    mban = robot.app.pila[-1]
    assert [_texto(x).split(" ")[0] for x in mban.opciones[:2]] == ["Dar", "Pactar"] and all(x.ayuda for x in mban.opciones[:2])
    p.rec_banda(LEALES)["fuerza"] = 60.0
    _elegir(robot, "Dar un golpe")
    assert p.mision and p.mision["def"]["id"] == "golpe_preventivo" and robot.app.pila[-1] is p
    p.abandonar_mision()
    _cerrar_menus(robot)
    # con un asalto en curso: arriba del todo en Territorios, y dentro, ir en persona o enviar a tu gente
    a = _asalto(p, "puerto", fuerza=20.0)
    _a_barrio(p, "puerto", dentro=False)
    menus_extra.territorios(p)
    m = robot.app.pila[-1]
    assert _texto(m.opciones[0]).startswith("¡Asalto a El Puerto!") and "Quedan 12 horas" in _texto(m.opciones[0]) and m.opciones[0].ayuda
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    d = robot.app.pila[-1]
    textos = [_texto(x) for x in d.opciones]
    assert textos[1].startswith("Asalto a El Puerto: ir en persona") and textos[2].startswith("Enviar a tu gente a defender El Puerto: unas ") and "de cada 10" in textos[2]
    _elegir(robot, "Asalto a El Puerto: ir en persona")
    assert robot.app.pila[-1] is p and p.gps is not None and "la defensa empieza en cuanto entres" in robot.dicho()
    RQ.menu_reconquista(p)
    _elegir(robot, "Enviar a tu gente")
    assert r["asalto"] is None and "Resultado:" in robot.dicho()
    _cerrar_menus(robot)


def test_todo_se_alcanza_con_el_mando(robot, datos_de_serie):
    """Con un mando: abrir el móvil, llegar a Territorios, a la defensa, contratar un guardia y enviar a la gente. Sin teclado."""
    p = _empezar(robot)
    j = p.j
    r, barrios = _en_marcha(p)
    j.dinero, j.banda, j.banda_nombre = 30000, 6, "Los Mirlos"
    _a_barrio(p, "puerto", dentro=False)
    a = _asalto(p, "puerto", fuerza=10.0)
    app = robot.app
    md = app.mando
    md.simulado = True

    def pulsar(boton):
        md.boton(boton, True)
        md.boton(boton, False)

    def hasta(contiene):
        m = app.pila[-1]
        assert isinstance(m, Menu), m
        for _ in range(len(m.opciones) + 1):
            if contiene in _texto(m.opciones[m.i]):
                return m
            pulsar("abajo")
        raise AssertionError((contiene, [_texto(o) for o in m.opciones]))
    assert md.contexto() == "pie"
    pulsar("back")                                                 # el móvil
    assert isinstance(app.pila[-1], Menu)
    hasta("Territorios")
    pulsar("a")
    m = hasta("¡Asalto a El Puerto!")
    assert m.i == 0
    hasta("Defensa de tus barrios")
    pulsar("a")
    d = app.pila[-1]
    assert d.titulo == "Defensa de tus barrios"
    hasta("El Puerto, en Puerto Bravo")
    pulsar("a")
    hasta("Guardia fija")
    pulsar("a")
    assert p.rec_barrio("puerto")["guardia"] == 1
    pulsar("b")                                                    # atrás
    assert app.pila[-1] is d
    hasta("Informantes")
    pulsar("a")
    assert r["informantes"] == 1
    for _ in range(len(d.opciones)):
        if "Enviar a tu gente" in _texto(d.opciones[d.i]):
            break
        pulsar("arriba")
    assert "Enviar a tu gente" in _texto(d.opciones[d.i])
    pulsar("a")
    assert r["asalto"] is None and "puerto" in j.territorios and "Resultado:" in robot.dicho()
    while app.pila[-1] is not p:
        pulsar("b")
    assert md.contexto() == "pie"
    assert a["estado"] == "en_curso"


# ====================================================================== muchos días seguidos
RITMO = {}


def _simular(robot, nivel, dias=60, semilla=1):
    """Sesenta días acelerados con todos los barrios de una ciudad y decisiones al azar. Devuelve lo que ha pasado."""
    random.seed(semilla * 1000 + len(nivel))
    p = _empezar(robot, nivel=nivel)
    j = p.j
    barrios = _ciudad(p)
    j.dinero, j.banda, j.banda_nombre = 60000, 3, "Los Mirlos"
    p.reconquista_revisar()
    r = p.rec()
    cuenta = {"asaltos": 0, "defendidos": 0, "perdidos": 0, "alianzas": 0, "inicios": [], "golpes": 0, "treguas": 0, "reconquistados": 0, "calma": r["calma"] - p.dia}
    visto = None
    dia0 = p.dia
    for _ in range(dias * 4):                                      # de seis en seis horas
        p = robot.app.partida
        j.salud = j.salud_max
        j.estrellas, j.puntos_busqueda = 0, 0.0
        j.dinero = max(j.dinero, 20000)
        if p.guerra:
            p.guerra_retirada()
        if p.mundo.barrio(*p.pos())["id"] in j.territorios and r["asalto"]:
            _a_barrio(p, r["asalto"]["barrio"], dentro=False)      # no se queda a vivir en el barrio asaltado
        _vaciar(p)
        p.pasar_horas(6)
        robot.frames(3)
        a = r["asalto"]
        # decisiones al azar del día a día
        cual = random.random()
        mios = [b for b in barrios if b in j.territorios]
        if cual < 0.05 and mios:
            p.rec_guardia(random.choice(mios), random.choice((1, 1, -1)))
        elif cual < 0.08 and mios:
            p.rec_reforzar(random.choice(mios))
        elif cual < 0.12:
            p.rec_informantes(random.choice((1, -1)))
        elif cual < 0.20 and mios:
            _a_barrio(p, random.choice(mios))
            robot.frames(70)
        elif cual < 0.23 and mios:
            p.rec_invertir(random.choice(mios))
        elif cual < 0.26:
            banda = random.choice(p.rec_nombres())
            if not p.tregua_motivo(banda):
                si, euros, d, _f = p.oferta_tregua(banda)
                if si and p.pactar_tregua(banda, euros, d):
                    cuenta["treguas"] += 1
                else:
                    p._apuntar_trato(banda, "tregua")
        elif cual < 0.29:
            banda = random.choice(p.rec_nombres())
            if p.empezar_golpe(banda):
                cuenta["golpes"] += 1
                if random.random() < 0.4:
                    p.mision["def"]["al_completar"]()
                p.abandonar_mision()
                robot.saltar_dialogos()
                _cerrar_menus(robot)
        elif cual < 0.33:
            perdidos = [b for b in barrios if b not in j.territorios]
            if perdidos:                                           # lo reconquista por la vía normal
                j.territorios.append(perdidos[0])
                j.barrios_banda.pop(perdidos[0], None)
                cuenta["reconquistados"] += 1
        a = r["asalto"]
        if a and a["estado"] == "en_curso" and a is not visto:
            visto = a
            cuenta["asaltos"] += 1
            cuenta["alianzas"] += len(a["bandas"]) > 1
            cuenta["inicios"].append(p.dia)
            bid = a["barrio"]
            que = random.choice(("persona", "gente", "nada", "nada"))
            if que == "persona":
                _a_barrio(p, bid)
                p.t_guerra_enfria = -99
                robot.frames(5)
                assert p.guerra and p.guerra["rec"], (nivel, p.dia)
                if random.random() < 0.8:
                    assert _ganar_guerra(robot, p)
                else:
                    p.guerra_retirada()
                    _a_barrio(p, bid, dentro=False)
            elif que == "gente":
                p.rec_enviar_gente()
        if visto is not None and r["asalto"] is not visto and visto.get("contado") is None:
            visto["contado"] = True
            if visto["barrio"] in j.territorios:
                cuenta["defendidos"] += 1
            else:
                cuenta["perdidos"] += 1
        # nada se sale de sus márgenes
        for st in r["barrios"].values():
            assert 0 <= st["lealtad"] <= 100 and 0 <= st["guardia"] <= AJ("guardia_max") and 0 <= st["refuerzo"] <= AJ("refuerzo_max")
        for b in r["bandas"].values():
            assert 0 <= b["fuerza"] <= 100 and -50 <= b["moral"] <= 100 and b["derrotas"] >= 0
        assert 0 <= r["informantes"] <= AJ("informante_max") and j.dinero >= 0 and j.banda >= 0
        assert not (r["asalto"] and j.amenaza)                     # nunca dos asaltos a la vez
        assert json.loads(json.dumps(j.reconquista)) == j.reconquista
    cuenta["dias"] = p.dia - dia0
    cuenta["quedan"] = sum(1 for b in barrios if b in j.territorios)
    cuenta["barrios"] = len(barrios)
    return cuenta


@pytest.mark.parametrize("semilla", [1, 2, 3])
@pytest.mark.parametrize("nivel", ["tranquilo", "normal", "duro"])
def test_sesenta_dias_acelerados_con_decisiones_al_azar(robot, datos_de_serie, nivel, semilla):
    c = _simular(robot, nivel, semilla=semilla)
    RITMO[nivel, semilla] = c
    print(f"\nRITMO {nivel} {semilla}: {c}")
    assert c["dias"] == 60
    # hay asaltos, pero con medida: entre uno y otro pasan al menos los días de descanso y los de preparación
    tope = {"tranquilo": 6, "normal": 9, "duro": 14}[nivel]
    assert 1 <= c["asaltos"] <= tope, c
    huecos = [b - a for a, b in zip(c["inicios"], c["inicios"][1:])]
    assert all(h >= AJ.entero(f"descanso_{nivel}") + AJ.entero("prepara_min") for h in huecos), (huecos, c)
    assert c["inicios"][0] >= 1 + c["calma"] + AJ.entero("prepara_min")      # nunca durante la calma
    assert c["defendidos"] + c["perdidos"] in (c["asaltos"], c["asaltos"] - 1)
    assert c["perdidos"] <= c["asaltos"] and c["quedan"] >= 1               # jugando al azar se pierden, pero nunca todo de golpe


def test_el_ritmo_crece_con_la_intensidad(robot, datos_de_serie):
    """Sin que el jugador haga nada (ni defender ni prevenir), en 60 días: cuántos asaltos salen con cada intensidad."""
    cuentas = {}
    for nivel in ("tranquilo", "normal", "duro"):
        total = 0
        for semilla in range(3):
            rng = random.Random(semilla)
            p = _empezar(robot, nivel=nivel) if semilla == 0 and nivel == "tranquilo" else robot.p
            p.cfg["reconquista"] = nivel
            j = p.j
            j.reconquista.clear()
            j.barrios_banda.clear()
            j.territorios = []
            j.tratos.clear()
            barrios = _ciudad(p)
            for m in p.mapas.values():
                if m.tipo == "ciudad":
                    _ciudad(p, m.id)                                # todas las ciudades: lo más que puede apretar
            j.dinero, j.banda = 10 ** 7, 0
            p.reconquista_revisar()
            r = p.rec()
            for _ in range(60):
                p.dia += 1
                p.reloj = 0.0
                for b in list(j.territorios):
                    p.rec_barrio(b)["pisado"] = p.dia            # como si los pisara todos: aquí se mide solo el ritmo
                p.dia_reconquista(rng)
                a = r["asalto"]
                if a and a["estado"] == "prepara" and a["dia"] <= p.dia:
                    total += 1
                    p._rec_empezar_asalto()
                    if rng.random() < 0.5:
                        p.rec_defendido("gente")
                    else:
                        p._rec_perdido()
                        j.territorios.append(a["barrio"])            # y lo recupera, para seguir midiendo con todo
                        j.barrios_banda.pop(a["barrio"], None)
                        p.reconquista_revisar()
                        r["calma"] = min(r["calma"], p.dia)          # sin calma nueva: lo peor posible
        cuentas[nivel] = total / 3.0
    print(f"\nRITMO SIN HACER NADA, asaltos en 60 días (media de 3): {cuentas}")
    RITMO["medias"] = cuentas
    assert cuentas["tranquilo"] < cuentas["normal"] < cuentas["duro"]
    assert 2 <= cuentas["tranquilo"] <= 6 and 4 <= cuentas["normal"] <= 10 and 7 <= cuentas["duro"] <= 16, cuentas


def test_veinte_dias_con_un_solo_barrio_no_cambian_nada(robot, datos_de_serie):
    """Quien tiene pocos barrios no nota la reconquista: ni estado, ni avisos, ni asaltos de este sistema."""
    p = _empezar(robot)
    j = p.j
    j.territorios = ["puerto"]
    n = len(robot_voz(p))
    for _ in range(20):
        p.pasar_horas(24)
        robot.frames(70)
    assert not j.reconquista.get("v") and "puerto" in j.territorios and "reconquist" not in _desde(p, n).lower() and "asalt" not in _desde(p, n).lower()


# ====================================================================== datos, editor, sonidos y documentación
def test_todas_las_cifras_estan_en_los_datos_y_el_editor_las_edita(datos_de_serie):
    from editor import modelo
    from editor.esquema import ESQUEMAS, SECCIONES
    datos = json.load(open(os.path.join(rutas.DATA, "datos", "vida.json"), encoding="utf-8"))
    sec = datos["reconquista"][0]
    assert set(sec) == set(AJ._n) | set(AJ._l) | {"id"}
    assert all(sec[k] == v for k, v in AJ._n.items()) and all(sec[k] == v for k, v in AJ._l.items())      # los datos dicen lo mismo que el valor de serie
    assert "reconquista" in M.SECCIONES_VIDA
    titulos = {clave: (titulo, esq) for clave, titulo, esq in SECCIONES}
    assert titulos["reconquista"][1] == "ajuste_reconquista"
    campos = {c["k"]: c for c in ESQUEMAS["ajuste_reconquista"]["campos"]}
    assert set(campos) == set(AJ._n) | set(AJ._l) | {"id"}, set(campos) ^ (set(AJ._n) | set(AJ._l) | {"id"})
    assert {c["k"] for c in ESQUEMAS["ajuste_pactos"]["campos"]} == set(PA.AJ._n) | set(PA.AJ._l) | {"id"}
    for k, c in campos.items():
        if k in AJ._n:
            assert c.get("defecto") == AJ._n[k], (k, c.get("defecto"), AJ._n[k])
    # un mod cambia los números y el juego los toma
    M.cargar_datos()
    AJ.configurar({"reconquista": [{"id": "general", "plazo_normal": 20, "crece_min": 0, "alianza_prob": 0, "forasteras": ["Los de Prueba"]}]})
    assert AJ("plazo_normal") == 20 and AJ("crece_min") == AJ._n["crece_min"] and AJ("alianza_prob") == 0 and AJ.lista("forasteras") == ["Los de Prueba"]
    cat = modelo.Catalogo()
    mod = modelo.Mod()
    mod.info = {"nombre": "Prueba", "autor": "Yo"}
    mod.secciones["reconquista"].append({"id": "general", "plazo_normal": 20, "forasteras": ["Los de Prueba"]})
    errores, avisos = modelo.comprobar(mod, cat)
    assert not errores, errores


def test_los_sonidos_nuevos_estan_en_todos_los_packs_y_en_la_guia():
    from juego import catalogo_sonidos
    assert sintesis.VERSION_CACHE >= 23
    S = sintesis.generar()
    assert len(S) >= 270
    for n in ("amenaza_barrio", "barrio_perdido", "barrio_defendido"):
        assert n in S and 0.6 < len(S[n]) / sintesis.SR < 2.0 and not sintesis.es_bucle(n)
        assert catalogo_sonidos.describir(n) != "Sonido del juego."
        for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
            carpeta = os.path.join(rutas.PACKS, pack)
            assert os.path.isdir(carpeta) and any(os.path.exists(os.path.join(carpeta, n + e)) for e in rutas.EXT_AUDIO), (pack, n)
    guia = open(os.path.join(rutas.DATA, "docs", "cambiar_sonidos_es.html"), encoding="utf-8").read()
    assert all(n in guia for n in ("amenaza_barrio", "barrio_perdido", "barrio_defendido"))


def test_el_manual_y_las_guias_lo_cuentan():
    manual = open(os.path.join(rutas.DATA, "docs", "manual_es.html"), encoding="utf-8").read()
    for frase in ("Las bandas intentan reconquistar tus barrios", "Defensa de tus barrios", "días de calma", "informantes", "Enviar a tu gente", "guardia fija", "lealtad",
                  "tregua", "golpe a su escondite", "banda forastera", "desmantelada", "tranquilo", "jugando con amigos", "nunca hay dos asaltos a la vez"):
        assert frase.lower() in manual.lower(), frase
    editor = open(os.path.join(rutas.DATA, "docs", "editor_mods_es.html"), encoding="utf-8").read()
    assert "Reconquista de barrios" in editor
    assert ".json" not in manual and ".py" not in manual
