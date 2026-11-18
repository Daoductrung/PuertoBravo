"""Trabajo 1.7.1, tanda 2: gente de la calle en los datos, tipos de enemigo, policía por nivel, enemigos en vehículo,
armas nuevas con su sonido, mejoras del taller nuevas y la caja de los locales."""
import ast
import json
import os
import random

import pygame
import pytest

from juego import charla, gente as G, mundo as M, rutas, sistemas


@pytest.fixture
def datos_de_serie():
    """Deja los datos del juego como estaban, por si una prueba los ha cambiado con un mod."""
    yield
    M.cargar_datos()


def _con_mod(monkeypatch, tmp_path, mod):
    with open(os.path.join(tmp_path, "prueba.json"), "w", encoding="utf-8") as f:
        json.dump(mod, f, ensure_ascii=False)
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    d = M.cargar_datos()
    assert d["errores_mods"] == [], d["errores_mods"]
    return d


def _mision(p, enemigos, lugar=None, ya=True):
    """Empieza una misión de un solo paso «eliminar» con esos grupos, junto al jugador."""
    l = lugar or min(p.mundo.lugares.values(), key=lambda l: (l.x - p.j.x) ** 2 + (l.y - p.j.y) ** 2)
    p.teletransportar(l.x, l.y)
    p._empezar_repetible({"id": "prueba_tipos", "titulo": "Prueba", "lugar": l.id, "pasos": [{"tipo": "eliminar", "lugar": l.id, "ya": ya, "texto": "A por ellos.", "enemigos": enemigos}],
                          "recompensa": {"dinero": 1}})
    return p.mision


# ------------------------------------------------------------------ gente de la calle
def test_la_gente_sale_de_los_datos_y_no_del_codigo():
    d = M.cargar_datos(con_mods=False)
    g = d["gente"][0]
    for lista in G.LISTAS:
        assert g[lista] and G.lista(lista) == g[lista], lista
    assert len(g["nombres_h"]) >= 16 and len(g["apellidos"]) >= 16 and len(g["oficios"]) >= 20 and len(d["caracteres"]) == 5
    # las listas ya no están escritas en los módulos del juego
    from juego import combate, extras2, extras3, misiones, partida
    for modulo, nombre in ((charla, "NOMBRES"), (charla, "OFICIOS"), (charla, "FEMENINO"), (extras2, "NOMBRES"), (extras3, "NOMBRES_PERRO"), (extras3, "BANDAS"),
                           (combate, "BANDAS_MUNDO"), (sistemas, "NOMBRES_BANDA"), (partida, "FRASES"), (misiones.Misiones, "NOMBRES_RIVALES")):
        assert not hasattr(modulo, nombre), (modulo, nombre)
    assert G.nombres_bandas() == ["Los Calaveras", "Los Lagartos", "Los Barrenos", "Los Tiburones", "Los Cuervos"]

    class Q:
        pass
    vistos = set()
    for semilla in range(60):
        f = charla.ficha(Q(), random.Random(semilla))
        assert f["nombre"] in G.nombres(f["genero"]) and f["apellido"] in g["apellidos"] and f["caracter"] in G.CARACTERES
        oficios = {(o.get("femenino") or o["nombre"]) if f["genero"] == "m" else o["nombre"] for o in g["oficios"]}
        assert f["oficio"] in oficios
        vistos.add(f["nombre"])
    assert len(vistos) > 15                                # variedad: no salen siempre los mismos
    for edad in range(19, 75):                             # los oficios cuadran con la edad, como dicen los datos
        for _ in range(8):
            o = G.oficio_para(edad, "h", random)
            assert not (o == "estudiante" and edad > 27) and not (o == "jubilado" and edad < 62) and (edad < 67 or o == "jubilado"), (edad, o)
    assert G.oficio_para(70, "m", random) == "jubilada"


def test_un_mod_anade_a_las_listas_o_las_sustituye(monkeypatch, tmp_path, datos_de_serie):
    serie = list(G.lista("nombres_h"))
    perros = list(G.lista("perros"))
    _con_mod(monkeypatch, tmp_path, {"gente": [{"id": "general", "nombres_h": ["Zacarías", serie[0]], "oficios": [{"nombre": "farero", "femenino": "farera", "edad_max": 66}]}]})
    assert G.lista("nombres_h") == serie + ["Zacarías"] and G.lista("perros") == perros          # se añade, sin repetir, y lo demás no cambia
    assert any(o["nombre"] == "farero" for o in G.OFICIOS) and any(o["nombre"] == "camarero" for o in G.OFICIOS)
    _con_mod(monkeypatch, tmp_path, {"gente": [{"id": "general", "sustituir": True, "nombres_h": ["Zacarías", "Abundio"], "perros": []}]})
    assert G.lista("nombres_h") == ["Zacarías", "Abundio"]                                       # con «sustituir», solo los del mod
    assert G.lista("nombres_m") and G.lista("perros")                                            # una lista vacía o que no viene no deja al juego sin nombres

    class Q:
        pass
    assert {charla.ficha(Q(), random.Random(s))["nombre"] for s in range(40) if charla.ficha(Q(), random.Random(s))["genero"] == "h"} <= {"Zacarías", "Abundio"}


def test_unos_datos_antiguos_sin_gente_usan_lo_de_serie(datos_de_serie):
    G.configurar({})                                       # como si no existiera gente.json
    for lista in G.LISTAS:
        assert G.lista(lista) or lista in G.SIN_SERIE, lista     # las del servidor pueden venir vacías: él trae las suyas
    assert G.OFICIOS and set(G.CARACTERES) == set(G.HABLAS) and len(G.nombres_bandas()) == 5
    assert G.enemigo({"n": 2, "tipo": "Matón", "arma": "bate", "salud": 33}) == {"nombre": "Matón", "arma": "bate", "salud": 33.0, "punteria": G.PUNTERIA, "vehiculo": "",
                                                                                 "ocupantes": 4, "frases": [], "voz": "", "clase": ""}
    assert G.enemigo({"clase": "no_existe"})["nombre"] == "Enemigo" and G.agentes_nivel(4)["arma"] == "subfusil" and G.agentes_nivel(1)["arma"] == "pistola"
    assert G.caja_local("tienda") is None and 150 <= G.botin_local("tienda", random, 150, 500) <= 500
    assert G.grupo("vigilante", 3, tipo="Vigilante", arma="pistola", salud=80) == {"n": 3, "tipo": "Vigilante", "arma": "pistola", "salud": 80}

    class Q:
        pass
    f = charla.ficha(Q(), random.Random(1))
    assert f["nombre"] and f["oficio"]


def test_caracter_nuevo_de_un_mod_y_caracter_que_ya_no_existe(robot, monkeypatch, tmp_path, datos_de_serie):
    from juego import respuestas
    _con_mod(monkeypatch, tmp_path, {"caracteres": [{"id": "grunon", "desc": "refunfuñando", "habla": "seco", "saludo": 1, "cumplido": 1, "chiste": -3, "insulto": -50, "valor": 0.9}]})
    assert "grunon" in G.CARACTERES and charla.CARACTERES is G.CARACTERES and G.habla_de("grunon") == "seco" and G.habla_de("chulo") == "chulo"
    f = {"nombre": "Lola", "genero": "m", "edad": 40, "oficio": "taxista", "caracter": "grunon", "confianza": 0, "frases": 0}
    frase, _, _ = respuestas.responder("¿qué tal el trabajo?", f, {"barrio": "El Puerto", "ciudad": "Puerto Bravo", "hora": "las diez", "tu": "Dani"})
    assert frase
    p = robot.nueva_partida()
    from juego.entidades import Persona
    q = Persona("civil", p.j.x + 2, p.j.y)
    q.ficha = dict(f, apellido="Mora", presentado=False, invitado=False, limosna=False, ofendido=False, disponible=True, le_atraen="hm")
    p.personas.append(q)
    assert "Lola Mora, 40 años, taxista. Te habla refunfuñando" in p.presentacion(q)
    q.ficha["caracter"] = "uno_de_un_mod_quitado"             # la partida guardó un carácter que ya no existe: no se rompe
    assert "Te habla" in p.presentacion(q) and p.responder(q, "saludar")


# ------------------------------------------------------------------ tipos de enemigo
def test_tipos_de_enemigo_en_los_pasos_eliminar(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    ms = _mision(p, [{"n": 2, "clase": "vigilante_armado"}, {"n": 1, "clase": "vigilante", "tipo": "Jefe de seguridad", "salud": 200, "punteria": 0.9, "arma": "revolver"},
                     {"n": 1, "tipo": "Matón de siempre", "arma": "bate", "salud": 44}])
    e = ms["enemigos"]
    assert len(e) == 4 and all(x in p.personas for x in e)
    tipo = G.tipo_enemigo("vigilante_armado")
    assert [x.nombre for x in e] == ["Vigilante de seguridad"] * 2 + ["Jefe de seguridad", "Matón de siempre"]
    assert e[0].arma == tipo["arma"] == "subfusil" and e[0].salud == tipo["salud"] and e[0].punteria == tipo["punteria"] and e[0].frases == tipo["frases"]
    assert e[0].tono < 0.95                                # voz grave, como dice el tipo
    assert (e[2].arma, e[2].salud, e[2].punteria) == ("revolver", 200.0, 0.9) and e[2].frases        # lo que dice el grupo manda sobre el tipo
    assert (e[3].arma, e[3].salud, e[3].punteria, e[3].frases) == ("bate", 44.0, G.PUNTERIA, [])     # la forma de siempre sigue valiendo
    # gritan su frase al verte, con su nombre delante
    for x in e:
        x.x, x.y = p.j.x + 8, p.j.y
    robot.frames(20)
    assert any(f"Vigilante de seguridad: {fr}" in robot.dicho() for fr in tipo["frases"]) or any(f"Jefe de seguridad: {fr}" in robot.dicho() for fr in e[2].frases)
    for x in list(e):
        p.danar_persona(x, 9999)
    robot.frames(5)
    assert p.mision is None or p.mision["def"]["id"] != "prueba_tipos"


def test_un_arma_al_azar_de_las_del_tipo():
    M.cargar_datos(con_mods=False)
    armas = {G.enemigo({"clase": "guardaespaldas"}, random.Random(s))["arma"] for s in range(60)}
    assert armas == set(G.tipo_enemigo("guardaespaldas")["armas"]) and len(armas) >= 3
    d = M.cargar_datos(con_mods=False)                                        # todo lo que citan el catálogo, las bandas, la policía y las cajas existe
    ids_armas, ids_veh, ids_tipos = {a["id"] for a in d["armas"]}, {v["id"] for v in d["vehiculos"]}, {t["id"] for t in d["tipos_enemigo"]}
    for t in d["tipos_enemigo"]:
        assert t["arma"] in ids_armas and set(t.get("armas", [])) <= ids_armas and (not t.get("vehiculo") or t["vehiculo"] in ids_veh) and t.get("frases"), t["id"]
    for b in d["bandas"]:
        assert set(b["tipos"]) <= ids_tipos and b.get("refuerzo", "pandillero") in ids_tipos and b.get("callejero", "calavera") in ids_tipos, b["id"]
    for n in d["policia_niveles"]:
        assert set(n["tipos"]) <= ids_tipos and 1 <= n["nivel"] <= 5
    assert sorted(n["nivel"] for n in d["policia_niveles"]) == [1, 2, 3, 4, 5]
    for c in d["cajas_locales"]:
        assert c["minimo"] <= c["maximo"] and (not c.get("guardia") or c["guardia"] in ids_tipos), c["id"]


def test_los_enemigos_llegan_en_un_vehiculo_y_se_bajan(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    ms = _mision(p, [{"n": 5, "clase": "pandillero_motorizado"}, {"n": 1, "clase": "pandillero"}])
    veh = ms["veh_enemigos"]
    tipo = G.tipo_enemigo("pandillero_motorizado")
    assert len(veh) == 2 and all(v.ia == "enemigos" and v.hostil and v.ocupado and v.modelo["id"] == tipo["vehiculo"] for v in veh)      # cinco, a tres por vehículo
    assert [len(v.pasajeros) for v in veh] == [3, 2] and len(ms["enemigos"]) == 6
    dentro = [q for v in veh for q in v.pasajeros]
    assert all(q not in p.personas for q in dentro) and sum(1 for e in ms["enemigos"] if e in p.personas) == 1
    assert "vienen en un vehículo" in robot.dicho() and all(140 < v.dist(p.j.x, p.j.y) < 240 for v in veh)
    assert veh[0] in p._objetivos()                         # se le puede fijar con Q
    # vienen hacia ti: se acercan solos
    d0 = veh[0].dist(p.j.x, p.j.y)
    robot.frames(90)
    assert veh[0].dist(p.j.x, p.j.y) < d0 - 10
    # al llegar, paran y se bajan
    v = veh[0]
    v.x, v.y, v.vel = p.j.x + 6, p.j.y, 0.5
    antes = list(v.pasajeros)
    for _ in range(60):
        robot.frames(1)
        if v.desplegado:
            break
    assert v.desplegado and v.ia == "aparcado" and not v.hostil and not v.pasajeros and v.tag is None
    assert all(q in p.personas and q.hostil and q.dist(v.x, v.y) < 20 for q in antes) and "Se bajan 3" in robot.dicho()
    # el otro, destruido antes de que se bajen: caen con él
    otro = veh[1]
    viajaban = list(otro.pasajeros)
    p.explotar(otro)
    assert all(q.muerto for q in viajaban) and otro.muerto
    for e in ms["enemigos"]:
        if not e.muerto:
            p.danar_persona(e, 9999)
    robot.frames(5)
    assert p.mision is None or p.mision["def"]["id"] != "prueba_tipos"      # el paso se cumple contando a los que venían en los vehículos


def test_el_vehiculo_de_los_enemigos_se_baja_solo_si_no_llega_y_se_limpia_al_fallar(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    ms = _mision(p, [{"n": 2, "clase": "escolta_motorizada"}])
    v = ms["veh_enemigos"][0]
    assert v.modelo["id"] == "todoterreno" and "Vienen en un vehículo" in robot.dicho()
    v.t_llegada = p.t                                       # ha pasado el plazo: se bajan donde estén
    v.vel = 0.0
    robot.frames(10)
    assert v.desplegado and all(e in p.personas for e in ms["enemigos"])
    # una misión que se falla con el vehículo aún en camino se lo lleva
    ms = _mision(p, [{"n": 2, "clase": "escolta_motorizada"}])
    v2 = ms["veh_enemigos"][0]
    assert v2 in p.vehiculos and not v2.desplegado
    p.fallar_mision("Prueba.")
    robot.saltar_dialogos()
    assert v2 not in p.vehiculos and v2.muerto
    # a pie si el grupo lo pide, y a pie en el mar o con un modelo que no es de tierra
    ms = _mision(p, [{"n": 2, "clase": "escolta_motorizada", "a_pie": True}])
    assert not ms.get("veh_enemigos") and all(e in p.personas for e in ms["enemigos"])
    p.fallar_mision("Prueba.")
    robot.saltar_dialogos()
    ms = _mision(p, [{"n": 2, "clase": "pandillero", "vehiculo": "lancha"}])
    assert not ms.get("veh_enemigos") and len(ms["enemigos"]) == 2 and all(e in p.personas for e in ms["enemigos"])


def test_no_se_puede_robar_un_vehiculo_lleno_de_enemigos(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    ms = _mision(p, [{"n": 2, "clase": "escolta_motorizada"}])
    v = ms["veh_enemigos"][0]
    v.x, v.y, v.vel = p.j.x + 3, p.j.y, 0.0
    robot.tecla(pygame.K_f)                                 # todavía no se han bajado
    assert p.j.veh is None and not v.desplegado and "lleno de enemigos" in robot.dicho()
    robot.frames(10)                                        # ya se han bajado: el vehículo se queda vacío y te lo puedes llevar
    assert v.desplegado and not v.ocupado
    p.j.x, p.j.y = v.x + 2, v.y
    robot.tecla(pygame.K_f)
    robot.frames(2)
    assert p.j.veh is v or p.forzando


# ------------------------------------------------------ policía por nivel de búsqueda
def test_la_policia_va_mejor_armada_con_mas_busqueda(robot):
    p = robot.nueva_partida()
    random.seed(11)
    por_nivel = {n: {G.agentes_nivel(n, random.Random(s))["clase"] for s in range(80)} for n in range(1, 6)}
    assert por_nivel[1] == por_nivel[2] == {"agente"} and por_nivel[3] == {"agente", "agente_subfusil"}
    assert por_nivel[4] == {"agente_subfusil", "agente_escopeta"} and por_nivel[5] == {"agente_subfusil", "agente_escopeta", "asalto"}
    armas4 = {G.agentes_nivel(4, random.Random(s))["arma"] for s in range(80)}
    assert armas4 == {"subfusil", "escopeta_combate"}                           # con mucha búsqueda ya no hay pistolas
    asalto = G.enemigo({"clase": "asalto"})
    assert asalto["vehiculo"] == "furgon_asalto" and asalto["ocupantes"] == 3 and asalto["salud"] > 100 and asalto["punteria"] > G.PUNTERIA and "furgon_asalto" in p.modelos
    # nivel 5: el juego avisa de la unidad de asalto, y sus furgones traen tres agentes con fusil
    p.poner_busqueda(5)
    robot.frames(3)
    assert p.j.estrellas == 5 and "Unidad Borrasca" in robot.dicho()
    modelos = set()
    for _ in range(40):
        for v in [v for v in p.vehiculos if v.ia == "policia"]:
            p.quitar_vehiculo(v)
        p._llegar_patrulla(*p.pos())
        modelos |= {v.modelo["id"] for v in p.vehiculos if v.ia == "policia"}
    assert modelos == {"patrulla", "furgon_asalto"}
    furgon = None
    while furgon is None:
        for v in [v for v in p.vehiculos if v.ia == "policia"]:
            p.quitar_vehiculo(v)
        p._llegar_patrulla(*p.pos())
        furgon = next((v for v in p.vehiculos if v.ia == "policia" and v.modelo["id"] == "furgon_asalto"), None)
    assert p.es_patrulla(furgon)
    for q in [q for q in p.personas if q.tipo == "policia"]:
        p.personas.remove(q)
    furgon.x, furgon.y, furgon.vel = p.j.x + 8, p.j.y, 0.0
    p.t_policia = 99.0
    p.cfg["invulnerable"] = True
    robot.frames(6)
    agentes = [q for q in p.personas if q.tipo == "policia"]
    assert furgon.desplegado and len(agentes) == 3 and all(q.nombre == "Agente de la Unidad Borrasca" and q.arma in ("fusil", "escopeta_combate") and q.salud == 140 and q.punteria == 0.55 for q in agentes)
    # nivel 1: dos agentes con pistola, en coche patrulla
    p._fin_persecucion()
    p.poner_busqueda(1)
    robot.frames(3)
    p._llegar_patrulla(*p.pos())
    pat = next(v for v in p.vehiculos if v.ia == "policia")
    assert pat.modelo["id"] == "patrulla" and pat.agentes["arma"] == "pistola" and pat.agentes["ocupantes"] == 2


def test_un_mod_cambia_la_policia_y_los_enemigos_de_serie(robot, monkeypatch, tmp_path, datos_de_serie):
    _con_mod(monkeypatch, tmp_path, {
        "tipos_enemigo": [{"id": "guardia_rural", "nombre": "Guardia rural", "arma": "revolver", "salud": 66, "punteria": 0.3, "vehiculo": "pickup", "ocupantes": 1, "frases": ["¡Alto ahí!"]},
                          {"id": "guardaespaldas", "nombre": "Gorila", "arma": "bate", "salud": 111}],
        "policia_niveles": [{"id": "nivel_1", "nivel": 1, "tipos": ["guardia_rural"]}]})
    e = G.agentes_nivel(1)
    assert (e["nombre"], e["arma"], e["vehiculo"], e["ocupantes"]) == ("Guardia rural", "revolver", "pickup", 1)
    assert G.agentes_nivel(4)["clase"] in ("agente_subfusil", "agente_escopeta")          # los demás niveles, los del juego
    assert G.enemigo({"clase": "guardaespaldas"})["nombre"] == "Gorila" and G.enemigo({"clase": "guardaespaldas"})["arma"] == "bate"      # un tipo del juego, cambiado


# -------------------------------------------------------- contratos, bandas y sucesos
def test_contratos_conquistas_y_bancos_usan_los_tipos(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.j.stats["contratos"] = 8                              # cinco guardaespaldas: a veces, parte en un vehículo
    taberna = next(l for l in p.mundo.lugares.values() if l.tipo == "taberna")
    visto_coche = visto_pie = False
    apodos = set()
    for _ in range(30):
        p.empezar_contrato(taberna)
        paso = p.mision["def"]["pasos"][0]
        grupos = paso["enemigos"]
        assert grupos[0]["clase"] == "objetivo_contrato" and grupos[0]["tipo"].startswith("Objetivo, ") and sum(g["n"] for g in grupos) == 6
        apodos.add(grupos[0]["tipo"][10:])
        en_coche = [g for g in grupos if g.get("clase") == "escolta_motorizada"]
        visto_coche |= bool(en_coche) and "en un vehículo" in paso["texto"]
        visto_pie |= not en_coche and "vehículo" not in paso["texto"]
        p.fallar_mision("Prueba.")
        robot.saltar_dialogos()
    assert visto_coche and visto_pie and len(apodos) > 5 and apodos <= set(G.lista("apodos"))
    # conquista: pelea contra los tipos de la banda del barrio, y el último grupo trae refuerzos en vehículo
    puerto = next(b for b in p.mundo.barrios if b["id"] == "puerto")
    p.empezar_conquista(puerto)
    pasos = p.mision["def"]["pasos"]
    assert [sum(g["n"] for g in x["enemigos"]) for x in pasos] == [3, 4, 5]
    assert all(g["clase"] in ("pandillero", "pandillero_duro", "pandillero_motorizado") and g["tipo"] == "Pandillero de Los Calaveras" for x in pasos for g in x["enemigos"])
    assert any(g["clase"] == "pandillero_motorizado" for g in pasos[2]["enemigos"]) and "refuerzo en un vehículo" in pasos[2]["texto"]
    assert not any(g["clase"] == "pandillero_motorizado" for x in pasos[:2] for g in x["enemigos"])
    assert pasos[1]["enemigos"][0]["salud"] == G.tipo_enemigo("pandillero")["salud"] + 8      # cada asalto, más duros
    p.fallar_mision("Prueba.")
    robot.saltar_dialogos()
    # banco: los vigilantes y el botín salen de la caja de los datos
    banco = next(l for l in p.mundo.lugares.values() if l.tipo == "banco")
    caja = p.caja_de_local(banco)
    p.empezar_atraco_banco(banco)
    d = p.mision["def"]
    assert [(g["n"], g["clase"]) for g in d["pasos"][0]["enemigos"]] == [(3, "vigilante"), (2, "vigilante_armado")]
    assert d["recompensa"]["dinero"] == caja["dinero"] and 7000 <= caja["dinero"] <= 13000 and d["pasos"][2]["nivel"] == 4
    assert [e.nombre for e in p.mision["enemigos"]] == ["Vigilante de seguridad"] * 5 and {e.arma for e in p.mision["enemigos"]} == {"pistola", "subfusil"}


def test_los_de_la_banda_por_la_calle_y_el_trato_con_ella(robot):
    from juego.entidades import Persona
    p = robot.nueva_partida()
    f = G.enemigo({"clase": "calavera"})
    q = G.vestir(Persona("banda", p.j.x + 6, p.j.y, f["nombre"]), f)
    q.banda, q.hostil, q.bloque = "Los Calaveras", True, (0, 0)
    p.personas.append(q)
    rep = p.rep_banda("Los Calaveras")
    p.danar_persona(q, 9999)
    assert p.rep_banda("Los Calaveras") == rep - 4          # matar a los suyos no se olvida
    otro = Persona("enemigo", p.j.x + 6, p.j.y, "Pandillero de Los Cuervos")
    otro.hostil = True
    p.personas.append(otro)
    rep = p.rep_banda("Los Cuervos")
    p.danar_persona(otro, 9999)
    assert p.rep_banda("Los Cuervos") == rep - 4
    assert G.banda("Los Lagartos")["id"] == "lagartos" and G.banda("lagartos")["nombre"] == "Los Lagartos" and G.banda("Los Nadie") is None
    assert G.tipos_de_banda("Los Barrenos") == (["pandillero", "pandillero_duro"], "dinamitero")


# ------------------------------------------------------------------------ armas nuevas
NUEVAS = {"hacha": "hacha", "pistola_rafagas": "disparo_rafaga", "escopeta_corredera": "disparo_corredera", "rifle_palanca": "disparo_palanca",
          "fusil_semi": "disparo_semiautomatico", "lanzagranadas": "lanzagranadas"}


def test_armas_nuevas_cada_una_con_su_sonido_en_todos_los_packs(app):
    from juego import catalogo_sonidos, packs, sintesis
    d = M.cargar_datos(con_mods=False)
    armas = {a["id"]: a for a in d["armas"]}
    usados = [a["sonido"] for a in d["armas"] if a["id"] not in NUEVAS]
    for ident, sonido in NUEVAS.items():
        a = armas[ident]
        assert a["sonido"] == sonido and sonido not in usados and a["precio"] > 0 and len(a["desc"]) > 40, ident      # su sonido es solo suyo
        assert sonido in app.mez.sonidos and catalogo_sonidos.describir(sonido) != "Sonido del juego." and catalogo_sonidos.grupo_de(sonido) == 4
        for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
            assert any(os.path.exists(os.path.join(rutas.PACKS, pack, sonido + e)) for e in rutas.EXT_AUDIO), (pack, sonido)
    assert {armas[i]["tipo"] for i in NUEVAS} == {"cuerpo", "fuego", "explosivo"} and armas["pistola_rafagas"]["automatica"]
    assert {armas[i].get("donde", "armeria") for i in NUEVAS} == {"armeria", "tienda", "empenos"}
    originales = sintesis.generar()
    assert all(s in originales for s in NUEVAS.values()) and all(len(originales[s]) > 2000 for s in NUEVAS.values())
    # todos los packs traen exactamente los mismos sonidos que los de serie
    serie = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(rutas.PACKS, "por_defecto")) if f.lower().endswith(rutas.EXT_AUDIO)}
    for pack in ("realista", "alternativo", "retro", "envolvente"):
        suyos = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(rutas.PACKS, pack)) if f.lower().endswith(rutas.EXT_AUDIO)}
        assert serie - suyos == set(), (pack, serie - suyos)
    assert set(NUEVAS.values()) <= set(packs.referencias(packs.carpeta_defecto()))


def test_donde_se_compra_cada_arma_y_se_dispara(robot):
    from juego import menus_juego, menus_lugares
    p = robot.nueva_partida()
    j = p.j
    j.dinero = 100000

    def textos():
        return [o.texto for o in robot.app.pila[-1].opciones]

    def elegir(trozo):
        m = robot.app.pila[-1]
        m.i = next(k for k, o in enumerate(m.opciones) if trozo in o.texto)
        robot.tecla(pygame.K_RETURN)
    armeria = next(l for l in p.mundo.lugares.values() if l.tipo == "armeria")
    menus_juego._armeria(p, armeria)
    t = textos()
    assert any(x.startswith("Pistola de ráfagas") for x in t) and any(x.startswith("Fusil semiautomático") for x in t) and any(x.startswith("Lanzagranadas") for x in t)
    assert not any("Hacha" in x or "Escopeta de corredera" in x or "Rifle de palanca" in x for x in t)        # esas se venden en otro sitio
    elegir("Lanzagranadas")
    elegir("Pistola de ráfagas")
    assert "lanzagranadas" in j.armas and "pistola_rafagas" in j.armas
    robot.tecla(pygame.K_ESCAPE)
    tienda = next(l for l in p.mundo.lugares.values() if l.tipo == "tienda")
    menus_juego._tienda(p, tienda)
    assert any(x.startswith("Hacha de bombero") and "cuerpo a cuerpo" in x for x in textos())
    elegir("Hacha de bombero")
    assert "hacha" in j.armas and any(x == "Hacha de bombero: ya la tienes" for x in textos())
    robot.tecla(pygame.K_ESCAPE)
    empenos = next(l for m in p.mapas.values() for l in m.lugares.values() if l.tipo == "empenos")
    if empenos.mapa != p.mundo.id:
        p.cambiar_mapa(empenos.mapa, empenos.x, empenos.y)
        robot.frames(5)
    menus_lugares.empenos(p, empenos)
    assert any(x.startswith("Escopeta de corredera") for x in textos()) and any(x.startswith("Rifle de palanca") for x in textos())
    elegir("Escopeta de corredera")
    elegir("Rifle de palanca")
    assert "escopeta_corredera" in j.armas and "rifle_palanca" in j.armas
    assert any(x.startswith("Munición para Escopeta de corredera") for x in textos())
    robot.tecla(pygame.K_ESCAPE)
    # su munición se compra también en la armería, y la de caza no admite silenciador
    armeria = next(l for l in p.mundo.lugares.values() if l.tipo == "armeria") if any(l.tipo == "armeria" for l in p.mundo.lugares.values()) else armeria
    menus_juego._armeria(p, armeria)
    t = textos()
    assert any(x.startswith("Munición para Escopeta de corredera") for x in t) and any(x.startswith("Munición para Rifle de palanca") for x in t)
    assert any(x.startswith("Silenciador para Rifle de palanca") for x in t) and not any(x.startswith("Silenciador para Escopeta de corredera") for x in t)
    robot.tecla(pygame.K_ESCAPE)
    # se disparan y suena lo suyo
    sonados = []
    son = p.son
    p.son = lambda nombre, *a, **k: (sonados.append(nombre), son(nombre, *a, **k))[1]
    for ident, sonido in NUEVAS.items():
        if ident not in j.armas:
            p.dar_arma(ident, 20)
        j.arma, j.t_ataque = ident, 0.0
        if p.armas_d[ident]["tipo"] != "cuerpo":
            j.armas[ident]["cargador"] = max(1, j.armas[ident]["cargador"])
        from juego.entidades import Persona
        q = Persona("enemigo", p.j.x + 2, p.j.y, "Diana")
        q.hostil, q.inofensivo, q.salud = True, True, 99999
        p.personas.append(q)
        p.objetivo = q
        p.atacar()
        p.personas.remove(q)
        assert sonido in sonados, (ident, sonados[-5:])
    assert p.explosiones and p.explosiones[-1]["arma"] == "lanzagranadas" and p.explosiones[-1]["radio"] == 7


# ----------------------------------------------------------------- mejoras del taller
def test_mejoras_nuevas_del_taller_con_efecto_de_verdad(robot):
    from juego import combustible as C, menus_juego
    p = robot.nueva_partida()
    j = p.j
    j.dinero = 100000
    p.cfg["sucesos"] = False
    assert list(sistemas.MEJORAS) == ["motor", "frenos", "blindaje", "neumaticos", "suspension", "escape", "deposito"]
    v = p.crear_vehiculo("utilitario", j.x, j.y, 0, None)
    p._subir(v, False, callar=True)
    assert sistemas.factor_lluvia(v) == 0.6 and sistemas.factor_golpes(v) == 1.0 and sistemas.factor_motor_volumen(v) == 1.0 and sistemas.factor_deposito(v) == 1.0
    cap = C.capacidad(v)
    taller = next(l for l in p.mundo.lugares.values() if l.tipo == "taller")
    menus_juego._taller(p, taller)
    m = robot.app.pila[-1]
    textos = [o.texto for o in m.opciones]
    assert any(t.startswith("Mejorar neumáticos reforzados: nivel 0 de 3. Subir cuesta 350") for t in textos)
    assert any(t.startswith("Mejorar silenciador de escape: nivel 0 de 2") for t in textos) and any(t.startswith("Mejorar depósito de combustible mayor: nivel 0 de 2") for t in textos)
    antes = j.dinero
    for nombre, veces in (("neumáticos", 4), ("suspensión", 4), ("silenciador de escape", 3), ("depósito", 3)):
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(f"Mejorar {nombre}"))
        for _ in range(veces):                              # una vez más que sus niveles: la última ya está al máximo
            robot.tecla(pygame.K_RETURN)
        assert "ya está al máximo" in robot.dicho()
    assert v.mejoras == {"neumaticos": 3, "suspension": 3, "escape": 2, "deposito": 2}
    assert antes - j.dinero == 350 * 6 + 600 * 6 + 450 * 3 + 400 * 3                      # cada nivel cuesta el precio por su número
    assert "silenciador de escape nivel 2" in sistemas.resumen(v)
    robot.tecla(pygame.K_ESCAPE)
    # neumáticos: con lluvia frena casi como en seco, pincha menos y rueda más bajo
    assert sistemas.factor_lluvia(v) > 0.85 and sistemas.factor_pinchazo(v) <= 0.25 and sistemas.factor_rodadura(v)[0] < 0.7 and sistemas.factor_rodadura(v)[1] < 0.9
    # suspensión: un choque le hace menos daño
    assert abs(sistemas.factor_golpes(v) - 0.55) < 1e-6
    otro = p.crear_vehiculo("utilitario", j.x + 40, j.y, 0, None)

    def golpe(veh):
        if j.veh:
            p.salir_vehiculo(forzado=True)
        p._subir(veh, False, callar=True)
        veh.salud = veh.salud_max
        p.cfg["conduccion"] = "libre"
        s0 = veh.salud
        bi, bj = p.mundo.bloque(veh.x, veh.y)
        veh.x, veh.y, veh.rumbo, veh.vel = bi * M.B + M.ACERA + 3, bj * M.B + 45, 90.0, 9.0      # contra la pared de la manzana
        for _ in range(60):
            robot.frames(1, mantener=(pygame.K_UP,))
            if veh.salud < s0:
                break
        return s0 - veh.salud
    con, sin = golpe(v), golpe(otro)
    assert sin > 0 and 0 < con < sin * 0.75, (con, sin)
    # escape: el motor suena más bajo y la policía te pierde antes
    assert abs(sistemas.factor_motor_volumen(v) - 0.4) < 1e-6 and abs(sistemas.factor_oido_policia(v) - 0.7) < 1e-6
    # depósito: caben más litros
    assert abs(C.capacidad(v) - cap * 1.6) < 1e-6 and C.capacidad(otro) == cap
    # los niveles de cada mejora se respetan al sacar el vehículo del garaje
    sistemas.poner(otro, {"escape": 9, "motor": 9, "neumaticos": 1})
    assert otro.mejoras == {"escape": 2, "motor": 3, "neumaticos": 1}


def test_un_mod_anade_mejoras_al_taller(monkeypatch, tmp_path, datos_de_serie):
    _con_mod(monkeypatch, tmp_path, {"mejoras": [{"id": "turbo", "nombre": "Turbo", "efecto": "motor", "niveles": 5, "por_nivel": 4, "precio": 1000, "desc": "Sopla."},
                                                 {"id": "pegatinas", "nombre": "Pegatinas", "precio": 50, "desc": "No corren más."},
                                                 {"id": "frenos", "nombre": "Frenos de carreras", "niveles": 1, "por_nivel": 50, "precio": 2000}]})
    assert sistemas.MEJORAS["turbo"]["niveles"] == 5 and sistemas.MEJORAS["pegatinas"]["efecto"] == "" and sistemas.MEJORAS["frenos"]["nombre"] == "Frenos de carreras"

    class V:
        modelo = {"salud": 100}
        salud = salud_max = 100.0
    v = V()
    sistemas.poner(v, {"turbo": 9, "motor": 3, "pegatinas": 3, "frenos": 3})
    assert v.mejoras == {"turbo": 5, "motor": 3, "pegatinas": 3, "frenos": 1}
    assert abs(sistemas.factor_velocidad(v) - (1 + 0.21 + 0.20)) < 1e-9 and abs(sistemas.factor_frenada(v) - 1.5) < 1e-9      # dos mejoras con el mismo efecto se suman
    assert sistemas.precio(v, "pegatinas") == 200


# ------------------------------------------------------------------ caja de los locales
def test_la_caja_de_cada_tipo_de_local(robot):
    p = robot.nueva_partida()
    for tipo in ("tienda", "banco", "taller", "gimnasio", "armeria"):
        c = G.caja_local(tipo)
        assert c and 0 < c["minimo"] <= c["maximo"] and 1 <= c["busqueda"] <= 5, tipo
    assert G.caja_local("taller")["guardias"] == 1 and G.caja_local("armeria")["guardia"] == "vigilante_armado" and G.caja_local("tienda")["guardias"] == 0
    assert G.caja_local("monumento") is None and G.caja_local("casa") is None
    taller = next(l for l in p.mundo.lugares.values() if l.tipo == "taller")
    c = p.caja_de_local(taller)
    assert c["minimo"] <= c["dinero"] <= c["maximo"] and c["enemigos"] == [{"n": 1, "clase": "maton"}] and c["busqueda"] == 2
    assert p.caja_de_local(taller)["dinero"] == c["dinero"]                 # la misma cifra todo el día
    cifras = set()
    for dia in range(1, 30):
        p.dia = dia
        cifras.add(p.caja_de_local(taller)["dinero"])
    assert len(cifras) > 10                                                 # y distinta cada día
    assert p.caja_de_local(next(l for l in p.mundo.lugares.values() if l.tipo == "casa")) is None
    assert p.caja_de_local("gimnasio")["guardias"] == 2                     # vale también con el tipo, sin un lugar concreto
    # los grupos de la guardia valen tal cual en un paso «eliminar»
    ms = _mision(p, p.caja_de_local("armeria")["enemigos"])
    assert len(ms["enemigos"]) == 2 and all(e.arma == "subfusil" for e in ms["enemigos"])
    p.fallar_mision("Prueba.")
    robot.saltar_dialogos()
    # el atraco a la tienda ya usa la caja de los datos
    from juego import menus_juego
    tienda = next(l for l in p.mundo.lugares.values() if l.tipo == "tienda")
    esperado = p.caja_de_local(tienda)["dinero"]
    p.dar_arma("pistola", 10)
    p.j.arma = "pistola"
    dinero = p.j.dinero
    menus_juego._tienda(p, tienda)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Atracar la tienda")
    robot.tecla(pygame.K_RETURN)
    assert p.j.dinero == dinero + esperado and 150 <= esperado <= 500


# ------------------------------------------------------------------------- el editor
def test_el_editor_tiene_las_secciones_nuevas_y_comprueba_los_tipos():
    from editor import modelo
    from editor.esquema import ESQUEMAS, SECCIONES
    titulos = {clave: titulo for clave, titulo, _ in SECCIONES}
    assert titulos["gente"] == "Gente de la calle" and titulos["tipos_enemigo"] == "Tipos de enemigo" and titulos["policia_niveles"] == "Policía por nivel de búsqueda"
    assert titulos["cajas_locales"] == "Caja de los locales" and "bandas" in titulos and "caracteres" in titulos
    campos = {esq: {c["k"] for c in ESQUEMAS[esq]["campos"]} for esq in ESQUEMAS}
    assert {"clase", "punteria", "vehiculo", "a_pie"} <= campos["enemigo"] and {"donde", "sin_silenciador"} <= campos["arma"] and {"efecto", "niveles", "por_nivel"} <= campos["mejora"]
    assert {"nombre", "arma", "armas", "salud", "punteria", "vehiculo", "ocupantes", "voz", "frases"} <= campos["tipo_enemigo"]
    cat = modelo.Catalogo()
    assert "asalto" in dict(cat.opciones("tipo_enemigo")) and len(cat.elementos_base("tipos_enemigo")) >= 15 and len(cat.elementos_base("gente")) == 1
    m = modelo.Mod()
    m.info = {"nombre": "Prueba"}
    m.secciones["tipos_enemigo"].append({"id": "mod_bruto", "nombre": "Bruto", "arma": "bate", "salud": 90, "punteria": 0.5, "vehiculo": "pickup", "ocupantes": 2, "frases": ["¡Eh!"]})
    m.secciones["bandas"].append({"id": "mod_banda", "nombre": "Los Brutos", "tipos": ["mod_bruto"], "refuerzo": "mod_bruto"})
    m.secciones["policia_niveles"].append({"id": "nivel_2", "nivel": 2, "tipos": ["agente", "mod_bruto"]})
    m.secciones["cajas_locales"].append({"id": "cine", "minimo": 10, "maximo": 20, "guardias": 1, "guardia": "mod_bruto", "busqueda": 1})
    m.secciones["gente"].append({"id": "general", "nombres_h": ["Zacarías"], "oficios": [{"nombre": "farero", "femenino": "farera"}]})
    m.secciones["caracteres"].append({"id": "grunon", "desc": "refunfuñando", "habla": "seco", "saludo": 1, "cumplido": 1, "chiste": 0, "insulto": -40, "valor": 0.8})
    m.secciones["mejoras"].append({"id": "turbo", "nombre": "Turbo", "efecto": "motor", "niveles": 4, "por_nivel": 5, "precio": 800})
    m.secciones["armas"].append({"id": "mod_hoz", "nombre": "Hoz", "tipo": "cuerpo", "dano": 30, "alcance": 2.5, "cadencia": 0.6, "precision": 0.9, "sonido": "hacha", "ruido": 0, "precio": 40, "donde": "tienda"})
    m.secciones["misiones"].append({"id": "mod_t1", "titulo": "Brutos", "lugar": "hospital", "pasos": [
        {"tipo": "eliminar", "lugar": "hospital", "texto": "A por ellos.", "enemigos": [{"n": 2, "clase": "mod_bruto"}, {"n": 1, "tipo": "Matón", "arma": "mod_hoz"}]}]})
    errores, _ = modelo.comprobar(m, cat)
    assert errores == [], errores
    crudo = m.crudo()
    assert crudo["gente"][0]["oficios"] == [{"nombre": "farero", "femenino": "farera"}] and crudo["misiones"][0]["pasos"][0]["enemigos"][0] == {"n": 2, "clase": "mod_bruto"}
    m.secciones["misiones"][0]["pasos"][0]["enemigos"].append({"n": 1})                    # ni tipo ni nombre y arma
    m.secciones["misiones"][0]["pasos"][0]["enemigos"].append({"n": 1, "clase": "no_existe"})
    m.secciones["policia_niveles"][0]["tipos"].append("tampoco")
    errores, _ = modelo.comprobar(m, cat)
    texto = " | ".join(errores)
    assert "elige un tipo de enemigo, o escribe su nombre y su arma" in texto and "«no_existe», que no existe" in texto and "«tampoco», que no existe" in texto


def test_el_juego_carga_un_mod_con_todo_lo_nuevo_hecho_con_el_editor(robot, monkeypatch, tmp_path, datos_de_serie):
    from editor import modelo
    m = modelo.Mod()
    m.info = {"nombre": "Prueba"}
    m.secciones["tipos_enemigo"].append({"id": "mod_bruto", "nombre": "Bruto", "arma": "bate", "salud": 90, "vehiculo": "pickup", "ocupantes": 2, "frases": ["¡Eh!"]})
    m.secciones["bandas"].append({"id": "mod_banda", "nombre": "Los Brutos", "tipos": ["mod_bruto"], "refuerzo": "mod_bruto"})
    m.secciones["cajas_locales"].append({"id": "cine", "minimo": 10, "maximo": 20, "guardias": 1, "guardia": "mod_bruto", "busqueda": 1})
    m.secciones["gente"].append({"id": "general", "perros": ["Zarpas"]})
    m.guardar(os.path.join(tmp_path, "prueba.json"))
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    datos = M.cargar_datos()
    assert datos["errores_mods"] == []
    assert "Zarpas" in G.lista("perros") and "Canela" in G.lista("perros") and "Los Brutos" in G.nombres_bandas() and G.caja_local("cine")["guardia"] == "mod_bruto"
    app = robot.app
    app.datos = datos
    p = robot.nueva_partida()
    ms = _mision(p, [{"n": 3, "clase": "mod_bruto"}])
    assert [len(v.pasajeros) for v in ms["veh_enemigos"]] == [2, 1] and all(e.nombre == "Bruto" and e.arma == "bate" for e in ms["enemigos"])


# ---------------------------------------------------------------- el servidor en línea
def test_el_servidor_toma_los_nombres_y_la_policia_del_mundo_si_vienen():
    from juego import enlinea
    from servidor import bots, policia
    mundo = enlinea.mundo_servidor()
    assert mundo["gente"]["nombres"] == G.lista("nombres_servidor") and len(mundo["gente"]["nombres"]) >= 10
    assert set(mundo["policia"]) == {"1", "2", "3", "4", "5"} and {d["arma"] for d in mundo["policia"]["5"]} == {"subfusil", "escopeta_combate", "fusil"}
    assert all(d["arma"] in mundo["armas"] for ops in mundo["policia"].values() for d in ops)
    for nueva in ("hacha", "lanzagranadas", "escopeta_corredera"):
        assert nueva in mundo["armas"]
    assert "furgon_asalto" in mundo["modelos"]
    json.loads(enlinea.mundo_canonico(mundo))
    # nombres: los del mundo; con un mundo de un juego anterior, que no los trae, los de siempre
    assert bots.nombres_del_mundo(mundo) == mundo["gente"]["nombres"]
    assert bots.nombres_del_mundo({"mapas": {}}) == bots.NOMBRES and bots.nombres_del_mundo({"gente": {"nombres": []}}) == bots.NOMBRES
    assert bots.nombres_del_mundo({"gente": {"nombres": ["la Faraona", 7, "  "]}}) == ["la Faraona"] and bots.nombres_del_mundo({"gente": "raro"}) == bots.NOMBRES

    class Falso(policia.Policia):
        def __init__(self, mundo):
            self.mundo, self.rng = mundo, random.Random(3)
    nuevo = Falso(mundo)
    assert {nuevo._po_dotacion(1) for _ in range(20)} == {("pistola", 80.0, 2)}
    assert {nuevo._po_dotacion(4)[0] for _ in range(60)} == {"subfusil", "escopeta_combate"}
    assert ("fusil", 140.0, 3) in {nuevo._po_dotacion(5) for _ in range(80)}
    viejo = Falso({"armas": {"pistola": {}, "subfusil": {}}, "mapas": {}})              # el mundo de un juego anterior
    assert viejo._po_dotacion(2) == ("pistola", 80.0, 2) and viejo._po_dotacion(5) == ("subfusil", 80.0, 2)
    roto = Falso({"armas": {"pistola": {}}, "policia": {"5": [{"arma": "no_existe"}, "x"], "3": "mal"}})
    assert roto._po_dotacion(5) == ("pistola", 80.0, 2) and roto._po_dotacion(3) == ("pistola", 80.0, 2)


def test_el_mundo_del_servidor_esta_al_dia_y_el_servidor_sigue_valiendo_para_python_38():
    from juego import enlinea
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(raiz, "servidor", "mundo.json"), encoding="utf-8") as f:
        guardado = json.load(f)
    datos = M.cargar_datos()                                                 # con los mods de serie, que es como se reparte el juego
    assert guardado["huella"] == enlinea.huella_datos(datos)                 # el mundo que va con el servidor es el de estos datos
    assert "lanzagranadas" in guardado["armas"] and "furgon_asalto" in guardado["modelos"] and guardado["gente"]["nombres"] and guardado["policia"]["5"]
    for nombre in os.listdir(os.path.join(raiz, "servidor")):
        if nombre.endswith(".py"):
            with open(os.path.join(raiz, "servidor", nombre), encoding="utf-8") as f:
                ast.parse(f.read(), feature_version=(3, 8))


def test_una_persecucion_de_nivel_5_y_una_conquista_enteras_no_se_rompen(robot):
    """Se deja correr el juego de verdad: patrullas y furgones que llegan y despliegan, y una conquista con refuerzos en vehículo."""
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.cfg["invulnerable"] = True
    random.seed(5)
    p.poner_busqueda(5)
    vistos = set()
    for _ in range(60):
        p.j.puntos_busqueda = 99.0                          # que no se le pase mientras dura la prueba
        robot.frames(30)
        vistos |= {(q.nombre, q.arma) for q in p.personas if q.tipo == "policia"}
        assert robot.app.pila[-1] is p, robot.dicho()
    assert len(vistos) >= 2 and not any(arma == "pistola" for _, arma in vistos), vistos      # con nivel 5 nadie viene con pistola
    assert all(v.modelo["id"] in ("patrulla", "furgon_asalto") for v in p.vehiculos if v.ia == "policia")
    p._fin_persecucion()
    p.j.puntos_busqueda = 0.0
    p.cfg["sin_policia"] = True
    puerto = next(b for b in p.mundo.barrios if b["id"] == "puerto")
    p.empezar_conquista(puerto)
    robot.saltar_dialogos()
    bajados = 0
    for _ in range(400):
        ms = p.mision
        if not ms or ms["def"]["id"] != "conquista":
            break
        paso = ms["def"]["pasos"][ms["paso"]]
        l = p.lugares[paso["lugar"]]
        if not ms["generado"]:
            p.teletransportar(l.x, l.y)
            robot.frames(3)
            continue
        for v in ms.get("veh_enemigos", []):
            if not v.desplegado and not v.muerto:
                v.x, v.y, v.vel = p.j.x + 7, p.j.y, 0.0      # ya ha llegado
                robot.frames(4)
                bajados += v.desplegado
        for e in ms["enemigos"]:
            if not e.muerto:
                assert e in p.personas                      # todos están ya en la calle
                p.danar_persona(e, 9999)
        robot.frames(3)
        robot.saltar_dialogos()
    assert "puerto" in p.j.territorios and bajados >= 1, (p.j.territorios, bajados, robot.dicho()[-300:])
