"""Versión 1.7.3: los fallos y lo que se pidió tras la 1.7.2, cada cosa con su prueba."""
import json
import os

import pytest

from juego import mundo as M
from juego.entidades import Persona
from juego.menus import Menu


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


def _empezar(robot, adultos=False, **opciones):
    if adultos:
        robot.app.cfg["adultos"] = True
        robot.app.aplicar_adultos()
    p = robot.nueva_partida()
    for k, v in dict(sucesos=False, patrullas_calle=False, ambulancias=False, charla_peatones="nada", **opciones).items():
        p.cfg[k] = v
    p.t_evento = 1e9
    for v in [v for v in p.vehiculos if v is not p.j.veh]:
        p.quitar_vehiculo(v)
    p.personas = []
    p.j.dinero = 5000
    return p


def _opcion(robot, trozo):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    o = next(o for o in m.opciones if trozo in o.texto)
    o.accion()
    return o


def _cerrar(robot):
    while robot.app.pila and robot.app.pila[-1] is not robot.p:
        robot.app.cerrar(robot.app.pila[-1])


# ------------------------------------------------------------------ la pareja y el mueble
def test_comprar_un_mueble_cumple_lo_que_te_pidio_al_momento(robot, datos_de_serie):
    from juego import convivencia as CV, sistemas
    p = _empezar(robot, adultos=True)
    j = p.j
    casa = p.lugares["casa_abuela"]
    if casa.id not in j.propiedades:
        j.propiedades.append(casa.id)
    pers = p.persona_social("lucia")
    p.relacion("lucia").update(estado="pareja", afinidad=80, citas=5, ultimo=p.dia)
    j.pareja = "lucia"
    j.convive, j.convive_casa, j.convive_desde = "lucia", casa.id, p.dia
    j.peticion_pareja = {"que": "mueble", "dia": p.dia, "hasta": p.dia + 2, "muebles": len(sistemas.muebles_de(j, casa))}
    assert p.nombre_lugar(casa) in p.peticion_txt()                 # dice para qué casa
    sistemas.menu_muebles(p, casa, Menu, __import__("juego.menus", fromlist=["x"]).Opcion)
    nombre = next(m[2] for m in sistemas.MUEBLES if m[0] not in sistemas.muebles_de(j, casa))
    _opcion(robot, nombre)
    assert j.peticion_pareja is None                                  # antes esperaba a la medianoche
    assert any(f.replace("{n}", pers["nombre"]) in robot.dicho() for f in CV.AJ.lista("frases_peticion_ok"))
    _cerrar(robot)
    # y lo que le acabas de hacer no te lo vuelve a pedir enseguida
    CV.AJ.n["peticion_prob"] = 100
    for _ in range(30):
        j.peticion_pareja = None
        p._peticion_nueva(pers)
        assert j.peticion_pareja["que"] != "mueble"


# ------------------------------------------------------------------ el plantón se recuerda
def test_tras_un_planton_no_quiere_quedar_unos_dias(robot, datos_de_serie):
    from juego import encuentros as EN
    p = _empezar(robot, adultos=True)
    pers = p.persona_social("lucia")
    l = p.lug(pers["lugar"])
    r = p.relacion("lucia")
    r["afinidad"] = 40
    EN.quedar(p, "lucia", pers["nombre"], l, EN.ahora(p) + 60, "paseo")
    p.reloj += 60 + EN.AJ.entero("espera_minutos") + 5
    EN.actualizar(p, 2.0)
    assert r["planton"] == p.dia and r["plantones"] == 1
    _cerrar(robot)
    EN.menu_quedar(p, pers)
    assert robot.app.pila[-1] is p                                    # no abre el menú: lo dice
    assert any(f.replace("{n}", pers["nombre"]).split("{d}")[0] in robot.dicho() for f in EN.AJ.lista("frases_planton_no"))
    p.dia += EN.AJ.entero("planton_dias")
    EN.menu_quedar(p, pers)
    assert isinstance(robot.app.pila[-1], Menu)                       # pasados los días, ya sí
    _cerrar(robot)
    # con un conocido de la calle, igual, y además pierde amistad
    c = {"nombre": "Ramiro", "amistad": 50, "mapa": p.mundo.id}
    p.j.conocidos.append(c)
    EN.quedar(p, "c:Ramiro", "Ramiro", l, EN.ahora(p) + 60)
    p.reloj += 60 + EN.AJ.entero("espera_minutos") + 5
    EN.actualizar(p, 2.0)
    assert c["planton"] == p.dia and c["amistad"] == 50 - EN.AJ.entero("planton_amistad")
    _cerrar(robot)
    EN.menu_quedar_conocido(p, c)
    assert robot.app.pila[-1] is p


# ------------------------------------------------------------------ los peatones huyen de verdad
def test_quien_huye_se_aleja_de_verdad_y_no_se_para_a_charlar(robot):
    p = _empezar(robot)
    x, y = p.pos()
    q = Persona("civil", *p.mundo.punto_libre(x + 6, y), "Paco")
    q.bloque = (int(q.x // M.B), int(q.y // M.B))
    q.u = 0.0
    p.personas.append(q)
    p.asustar(q, 10)
    d0 = q.dist(x, y)
    for _ in range(90):                                               # tres segundos
        p.actualizar_personas(1 / 30)
    assert q.bloque is None and (q not in p.personas or q.dist(x, y) > d0 + 5), q.dist(x, y)
    # Intro junto a alguien que huye: no suelta una frase de paseo
    q2 = Persona("civil", x + 1, y, "Paca")
    q2.estado, q2.t_estado = "huye", 5
    p.personas.append(q2)
    p.interactuar()
    assert "no se para" in robot.dicho()


def test_los_tiros_asustan_tambien_a_quien_esta_parado_y_se_oye_el_panico(robot):
    p = _empezar(robot)
    x, y = p.pos()
    gente = []
    for k in range(4):
        q = Persona("civil", x + 4 + k, y + 3, f"P{k}")
        q.estado = "quieto"
        gente.append(q)
    p.personas.extend(gente)
    sonidos = []
    original = p.son
    p.son = lambda nombre, *a, **k: (sonidos.append(nombre), original(nombre, *a, **k))[1]
    p.susto_por_tiros(x, y)
    assert all(q.estado == "huye" for q in gente)
    assert "panico" in sonidos


# ------------------------------------------------------------------ las treguas
def test_una_banda_en_tregua_no_ataca_tus_barrios_y_atacarla_la_rompe(robot, datos_de_serie):
    from juego import gente as G, pactos as PA, sistemas
    p = _empezar(robot, reconquista="normal")
    p.cfg["sucesos"] = True
    banda = G.nombres_bandas()[0]
    p.j.territorios = [p.mundo.barrios[0]["id"]]
    p.rec_banda(banda)["tregua"] = p.dia + 5
    assert p.en_tregua(banda)

    class Azar:
        def random(self):
            return 0.0

        def choice(self, lista):
            return banda if banda in lista else ("ataque" if "ataque" in lista else lista[0])
    for _ in range(5):
        p.j.amenaza = None
        sistemas.sucesos_territorio(p, Azar())
        assert not p.j.amenaza
    assert p.romper_tregua(banda) and not p.en_tregua(banda)
    assert any(f.replace("{banda}", banda) in robot.dicho() for f in __import__("juego.reconquista", fromlist=["x"]).AJ.lista("frases_tregua_rompes"))


def test_buscar_pelea_a_una_banda_en_tregua_la_rompe(robot, datos_de_serie):
    from juego import gente as G
    p = _empezar(robot, reconquista="normal")
    banda = G.nombres_bandas()[1]
    p.rec_banda(banda)["tregua"] = p.dia + 5
    assert p.buscar_pelea(banda)
    assert not p.en_tregua(banda)


# ------------------------------------------------------------------ el barco no se pierde
def test_tu_barco_no_se_pierde_si_llegas_nadando_o_te_rescatan(robot):
    from juego import menus_lugares
    p = _empezar(robot)
    emb = p.lugares["emb_puerto"]
    menus_lugares._zarpar(p, emb, "lancha", 90, "La Gaviota", {"modelo": "lancha", "nombre": "La Gaviota"})
    robot.frames(3)
    assert p.mundo.tipo == "mar" and p.j.barco_actual
    p.salir_vehiculo(forzado=True)                                    # se tira al agua y lo dejan atrás
    p.naufragar()
    assert p.mundo.tipo != "mar" and p.j.barco_actual is None
    assert [(b["modelo"], b["nombre"]) for b in p.j.barcos] == [("lancha", "La Gaviota")]
    assert "remolcan" in robot.dicho()


# ------------------------------------------------------------------ las cartas de los locales
def test_cada_local_sirve_su_carta(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot, vida_realista=True)
    hel = p.lugares["heladeria"]
    menus_juego.lugar(p, hel)
    textos = " ".join(o.texto for o in robot.app.pila[-1].opciones)
    assert "Horchata" in textos and "Helado" in textos and "Banquete" not in textos
    _cerrar(robot)
    menus_juego.lugar(p, p.lugares["pizzeria"])
    assert "Pizza margarita" in " ".join(o.texto for o in robot.app.pila[-1].opciones)
    _cerrar(robot)
    # lo de la carta quita el hambre y la sed que dicen los datos
    p.j.hambre, p.j.sed = 60.0, 60.0
    menus_juego.lugar(p, hel)
    _opcion(robot, "Horchata")
    assert p.j.sed == pytest.approx(60.0 - 65) or p.j.sed == 0.0
    assert p.j.hambre == pytest.approx(55.0)
    _cerrar(robot)
    # sin sed, una bebida no se toma
    p.j.sed, p.j.salud = 0.0, p.j.salud_max
    menus_juego.lugar(p, hel)
    dinero = p.j.dinero
    _opcion(robot, "Granizado")
    assert p.j.dinero == dinero and "sed" in robot.dicho()
    _cerrar(robot)


def test_las_tabernas_y_el_bar_tienen_carta(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot)
    menus_juego.lugar(p, p.lugares["bar_gaviota"])
    _opcion(robot, "Pedir de la carta")
    assert "Patatas bravas" in " ".join(o.texto for o in robot.app.pila[-1].opciones) or "patatas bravas" in " ".join(o.texto for o in robot.app.pila[-1].opciones)
    _cerrar(robot)
    menus_juego.lugar(p, p.lugares["bodega"])
    _opcion(robot, "Pedir de la carta")
    assert "calamares" in " ".join(o.texto for o in robot.app.pila[-1].opciones)
    _cerrar(robot)


def test_cada_tienda_vende_lo_suyo(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot)
    p.j.perro = "Canela"
    menus_juego.lugar(p, p.lugares["mercado_pb"])
    textos = " ".join(o.texto for o in robot.app.pila[-1].opciones)
    assert "ganzúas" not in textos.lower() and "auriculares" not in textos.lower()
    _cerrar(robot)
    menus_juego.lugar(p, p.lugares["ferreteria"])
    textos = " ".join(o.texto for o in robot.app.pila[-1].opciones).lower()
    assert "ganzúas" in textos
    _cerrar(robot)


def test_todos_los_locales_de_comida_de_serie_tienen_carta():
    d = M.cargar_datos(con_mods=False)
    cartas = {c["id"] for c in d["cartas"]}
    for m in [d["ciudad"]] + d["mapas"]:
        for l in m.get("lugares", []):
            if l.get("tipo") in ("comida", "pizzeria"):
                assert l.get("carta") in cartas, l["id"]
            if l.get("carta"):
                assert l["carta"] in cartas, l["id"]


# ------------------------------------------------------------------ el perro, el alias y el cajero
def test_ponerle_nombre_al_perro(robot):
    from juego import menus_extra
    from juego.menus import EntradaTexto
    p = _empezar(robot)
    p.j.perro = "Canela"
    p.crear_perro()
    menus_extra.poner_nombre_perro(p)
    e = robot.app.pila[-1]
    assert isinstance(e, EntradaTexto)
    e.al_aceptar("Trueno")
    assert p.j.perro == "Trueno" and p.perro().nombre == "Trueno"


def test_el_alias_del_jefe_lo_usa_tu_gente():
    from juego import golpes, reacciones, sistemas
    from juego.entidades import Jugador
    j = Jugador()
    j.nombre = "Dani"
    assert sistemas.alias_de(j) == "Dani"
    j.alias = "el Notario"
    assert sistemas.alias_de(j) == "el Notario"
    assert any("{alias}" in f for f in golpes.AJ.lista("frases_charla_banda"))
    assert any("{alias}" in f for f in reacciones.AJ.lista("frases_recluta_si"))


def test_en_el_cajero_se_ingresa_poco_al_dia(robot):
    from juego import capo, menus_capo
    p = _empezar(robot)
    p.j.dinero, p.j.banco = 2000, 0
    tope = capo.AJ.entero("cajero_ingreso_max")
    menus_capo._ingresar(p, 500)
    menus_capo._ingresar(p, 500)
    assert p.j.banco == tope and p.j.dinero == 2000 - tope
    assert "no admite más" in robot.dicho() or menus_capo.queda_cajero(p) == 0
    p.dia += 1
    menus_capo._ingresar(p, 100)
    assert p.j.banco == tope + 100


# ------------------------------------------------------------------ el servidor
def test_ordenes_en_ingles_y_renombrar(tmp_path):
    from test_servidor import Banco, Cli
    b = Banco(tmp_path / "s")
    try:
        assert "Órdenes" in b.hacer(b.srv.orden, "help")
        assert b.hacer(b.srv.orden, "players") == b.hacer(b.srv.orden, "jugadores")
        uno = Cli(b, "Alfonso")
        assert uno.ok
        r = b.hacer(b.srv.orden, "rename Alfonso: Alfonsina")
        assert "Alfonsina" in r and b.hacer(lambda: b.srv.alm.cuenta_por_nombre("Alfonsina")) is not None
        sin = Cli(b, "")                                              # sin nombre no se crea la cuenta
        assert sin.rechazo and "nombre de jugador" in sin.rechazo
        viejo = Cli(b, "Jugador")                                     # lo que mandaba un juego anterior sin nombre
        assert viejo.rechazo
    finally:
        b.parar()


def test_el_chat_tiene_su_historial_aparte(robot):
    import pygame
    p = _empezar(robot)
    p.voz.apuntar_mensaje("Ana dice: hola")
    p.decir("Mensaje cualquiera del juego.")
    robot.tecla(pygame.K_PAGEUP, pygame.KMOD_SHIFT)
    assert "Ana dice: hola" in robot.dicho()


# ------------------------------------------------------------------ los mods
def test_activar_y_desactivar_mods_desde_el_juego(tmp_path, monkeypatch):
    from juego import gestor_mods, rutas
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    (tmp_path / "mio.json").write_text(json.dumps({"info": {"nombre": "Mi pueblo", "descripcion": "Un pueblo."}}), encoding="utf-8")
    assert gestor_mods.listar() == [("mio.json", True)]
    assert gestor_mods.ficha("mio.json") == ("Mi pueblo", "Un pueblo.")
    nuevo = gestor_mods.activar("mio.json", False)
    assert nuevo == "mio.json.desactivado" and gestor_mods.listar() == [(nuevo, False)]
    assert gestor_mods.activar(nuevo, True) == "mio.json"


def test_el_editor_explica_por_que_no_encuentra_una_localidad_y_sigue_un_cambio_de_identificador():
    from editor import modelo
    mod = modelo.Mod()
    mod.secciones.setdefault("mapas", []).append({"id": "villa_sol", "nombre": "Villa Sol", "lugares": []})
    mod.secciones.setdefault("lugares", []).append({"id": "bar_sol", "nombre": "Bar", "tipo": "bar", "mapa": "Villa Sol"})
    assert "nombre de tu localidad" in modelo.pista_mapa("Villa Sol", mod)
    mod.secciones["lugares"][0]["mapa"] = "villa_sol"
    assert modelo.renombrar_referencias_mapa(mod, "villa_sol", "villasol") == 1
    assert mod.secciones["lugares"][0]["mapa"] == "villasol"


def test_un_lugar_de_mod_encuentra_su_localidad_aunque_venga_en_otro_mod(tmp_path, monkeypatch):
    from juego import cifrado, rutas
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    monkeypatch.setattr(cifrado, "COMPILADO", False)
    (tmp_path / "a_lugares.json").write_text(json.dumps({"lugares": [{"id": "bar_sol", "nombre": "Bar del Sol", "tipo": "bar", "mapa": "villa_sol", "bloque": [0, 0], "lado": "N", "pos": 10}]}), encoding="utf-8")
    base = M.cargar_datos(con_mods=False)
    mapa = dict(next(m for m in base["mapas"] if m.get("tipo") == "ciudad" or m.get("barrios")))
    mapa.update(id="villa_sol", nombre="Villa Sol", lugares=[])
    (tmp_path / "b_pueblo.json").write_text(json.dumps({"mapas": [mapa]}), encoding="utf-8")
    d = M.cargar_datos()
    villa = next(m for m in d["mapas"] if m["id"] == "villa_sol")
    assert any(l["id"] == "bar_sol" for l in villa["lugares"])
    M.cargar_datos()


def test_los_sonidos_propios_de_un_mod(tmp_path, monkeypatch):
    from editor import modelo
    from juego import rutas, sintesis
    monkeypatch.setattr(rutas, "SONIDOS_MODS", str(tmp_path / "sonidos"))
    origen = tmp_path / "Mi Disparo Atómico.wav"
    sintesis.escribir_wav(str(origen), sintesis.generar()["cruce"])
    nombre = modelo.anadir_sonido(str(origen), {"cruce"})
    assert nombre == "mi_disparo_atomico" and nombre in modelo.sonidos_de_mods()
    assert modelo.anadir_sonido(str(tmp_path / "Mi Disparo Atómico.wav"), {"mi_disparo_atomico"}) == "mod_mi_disparo_atomico"


# ------------------------------------------------------------------ las novedades y los LEEME en inglés
def test_las_novedades_van_en_el_idioma_del_juego():
    from herramientas import publicar
    from juego import actualizador, i18n
    assert set(publicar.idiomas_con_novedades()) >= {"es", "en"}
    es, en = publicar.novedades("es"), publicar.novedades("en")
    assert es and en and es != en
    m = {"novedades": es, "novedades_por_idioma": {"es": es, "en": en}}
    original = i18n.actual
    try:
        i18n.actual = lambda: "en"
        assert actualizador.notas_en_mi_idioma(m) == en
        i18n.actual = lambda: "vi"                                       # sin las suyas, las inglesas
        assert actualizador.notas_en_mi_idioma(m) == en
        i18n.actual = lambda: "pt"                                       # y desde la 1.7.3, aunque las tuviera: solo español e inglés
        assert actualizador.notas_en_mi_idioma(dict(m, novedades_por_idioma={"es": es, "en": en, "pt": "novidades"})) == en
        assert i18n.doc("novedades").endswith("novedades_en.html") and i18n.doc("manual").endswith("manual_pt.html")
        i18n.actual = lambda: "es"
        assert i18n.doc("novedades").endswith("novedades_es.html")
    finally:
        i18n.actual = original
    assert actualizador.notas_en_mi_idioma({"novedades": es}) == es            # una versión anterior, en español
    notas = publicar.notas_github()
    assert "## Novedades (español)" in notas and "## What's new (English)" in notas


def test_los_leeme_viejos_se_quitan_al_actualizar(tmp_path, monkeypatch):
    from juego import i18n, rutas
    monkeypatch.setattr(rutas, "base", lambda: str(tmp_path))
    monkeypatch.setattr(rutas, "data", lambda *p: os.path.join(str(tmp_path), "data", *p))
    os.makedirs(tmp_path / "data" / "mods")
    for f in ("LEEME.txt", "LEEME_en.txt", "README_en.txt", "data/mods/LEEME_mods_en.txt", "data/mods/README_mods_en.txt", "LEEME_vi.txt"):
        (tmp_path / f).write_text("x", encoding="utf-8")
    assert i18n.quitar_leemes_viejos() == 2
    assert (tmp_path / "LEEME.txt").exists() and (tmp_path / "LEEME_vi.txt").exists()             # sin su README, se queda
    assert not (tmp_path / "LEEME_en.txt").exists() and not (tmp_path / "data/mods/LEEME_mods_en.txt").exists()


def test_quien_huye_no_se_mete_en_la_calzada(robot):
    """Huye por la acera: bajar a la calzada solo si no le queda otra, porque ahí lo atropellan."""
    p = _empezar(robot)
    x, y = p.pos()
    q = Persona("civil", *p.mundo.punto_libre(x + 6, y), "Paco")
    p.personas.append(q)
    p.asustar(q, 10)
    pisa = []
    for _ in range(150):
        p.actualizar_personas(1 / 30)
        if q in p.personas:
            pisa.append(p.mundo.superficie(q.x, q.y))
    if pisa and pisa[0] != "calzada":
        assert pisa.count("calzada") <= len(pisa) // 4, pisa.count("calzada")
