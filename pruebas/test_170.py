"""Lo nuevo de la 1.7.0 en el juego: vehículo aparcado, próximo cruce, necesidades, Mayúsculas derecha, descargas,
artes marciales mixtas, complementos y protecciones, oficios, ayudas en las misiones, Mi música y combustible."""
import math

import pygame

from juego import combustible as C
from juego import mundo as M


def _tecla(robot, k, mod=0):
    robot.app.pila[-1].tecla(pygame.event.Event(pygame.KEYDOWN, key=k, mod=mod, unicode=""))


def _coche(p, modelo="sedan"):
    x, y, d = p.plaza_cercana()
    v = p.crear_vehiculo(modelo, x, y, d, None)
    p.j.x, p.j.y = x + 2, y
    p._subir(v, False, callar=True)
    return v


# ------------------------------------------------------------------ vehículo aparcado
def test_localizar_el_vehiculo_aparcado(robot):
    p = robot.nueva_partida()
    p.localizar_vehiculo()
    assert "No has dejado ningún vehículo" in robot.dicho()
    v = _coche(p)
    p.salir_vehiculo(forzado=True)
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 150, v.y + 150)
    robot.app.voz.registro.clear()
    _tecla(robot, pygame.K_l, pygame.KMOD_LSHIFT)
    assert "Marcado en el GPS" in robot.dicho() and v.nombre in robot.dicho()
    assert p.gps and math.hypot(p.gps["dest"][0] - v.x, p.gps["dest"][1] - v.y) < 1


def test_el_gps_vuelve_a_donde_ibas_tras_ir_al_vehiculo(robot):
    p = robot.nueva_partida()
    v = _coche(p)
    p.salir_vehiculo(forzado=True)
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 150, v.y + 150)
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "hospital")
    p.gps_a_lugar(l)
    p.localizar_vehiculo()
    assert p.gps["anterior"]["nombre"] == l.nombre and "el GPS vuelve a" in robot.dicho()


def test_el_vehiculo_espera_en_la_localidad_donde_lo_dejaste(robot):
    p = robot.nueva_partida()
    v = _coche(p)
    nombre, origen = v.nombre, p.mundo.id
    p.salir_vehiculo(forzado=True)
    otro = next(m for m in p.mapas.values() if m.id != origen and m.tipo != "mar")
    p.cambiar_mapa(otro.id, 100, 100)
    assert p.veh_fuera and p.veh_fuera["mapa"] == origen and p.tu_vehiculo() is None
    robot.app.voz.registro.clear()
    p.localizar_vehiculo()
    assert p.mapas[origen].nombre in robot.dicho()
    d = p.a_dict() if hasattr(p, "a_dict") else None
    p.cambiar_mapa(origen, v.x + 20, v.y)
    u = p.tu_vehiculo()
    assert u is not None and u.nombre == nombre and p.veh_fuera is None
    assert d is None or d.get("veh_fuera", {}).get("mapa") == origen


# ------------------------------------------------------------------ teclas
def test_proximo_cruce(robot):
    p = robot.nueva_partida()
    m = p.mundo
    p.j.x, p.j.y = 2 * M.B + 30.0, 3 * M.B + 2.0            # en una calle, entre dos avenidas
    p.j.rumbo = 90
    nombre, dist = p.proximo_cruce()
    assert nombre == m.avenidas[3] and abs(dist - (M.B - 30)) < 0.01
    assert "Siguiente cruce, hacia el este" in robot.dicho() and m.calles[3] in robot.dicho()
    p.j.rumbo = 270
    assert p.proximo_cruce()[0] == m.avenidas[2]
    p.j.x = 3 * M.B                                           # justo en un cruce: dice el siguiente, no el que pisas
    p.j.rumbo = 90
    assert p.proximo_cruce()[0] == m.avenidas[4]
    p.j.x, p.j.rumbo = 5.0, 270
    p.j.x = 0.0
    assert p.proximo_cruce() is None and "no hay más cruces" in robot.dicho()
    robot.app.voz.registro.clear()
    p.j.x, p.j.rumbo = 2 * M.B + 30.0, 0
    _tecla(robot, pygame.K_n, pygame.KMOD_LSHIFT)
    assert "Siguiente cruce, hacia el norte" in robot.dicho()


def test_mayusculas_v_dice_solo_hambre_y_sueno(robot):
    p = robot.nueva_partida()
    _tecla(robot, pygame.K_v, pygame.KMOD_LSHIFT)
    assert "vida realista está desactivada" in robot.dicho() and "Salud" not in robot.dicho().split("Menú")[-1][-200:]
    p.cfg["vida_realista"] = True
    p.j.hambre = 70
    robot.app.voz.registro.clear()
    _tecla(robot, pygame.K_v, pygame.KMOD_LSHIFT)
    assert "con hambre" in robot.dicho() and "euros" not in robot.dicho()
    p.cfg["vida_realista"] = False


def test_la_mayusculas_derecha_no_cambia_entre_andar_y_correr(robot):
    p = robot.nueva_partida()
    p.cfg["correr_alternar"] = True
    p.correr_fijo = False
    _tecla(robot, pygame.K_RSHIFT)
    p.mayus_soltada()
    assert not p.correr_fijo                                   # la derecha, nunca
    robot.app.teclas.add(pygame.K_LSHIFT)                      # la izquierda sola: al soltarla, cambia
    _tecla(robot, pygame.K_LSHIFT)
    p.mayus_soltada()
    assert not p.correr_fijo                                   # mientras sigue pulsada, todavía no
    robot.app.teclas.discard(pygame.K_LSHIFT)
    p.mayus_soltada()
    assert p.correr_fijo
    robot.app.teclas.add(pygame.K_LSHIFT)                      # la izquierda con una letra: es una combinación, no cambia nada
    _tecla(robot, pygame.K_LSHIFT)
    _tecla(robot, pygame.K_n, pygame.KMOD_LSHIFT)
    robot.app.teclas.discard(pygame.K_LSHIFT)
    p.mayus_soltada()
    assert p.correr_fijo and "Siguiente cruce" in robot.dicho()
    for tecla, mod in ((pygame.K_n, pygame.KMOD_RSHIFT), (pygame.K_v, pygame.KMOD_RSHIFT), (pygame.K_l, pygame.KMOD_RSHIFT)):
        robot.app.voz.registro.clear()                         # y las combinaciones valen con cualquiera de las dos
        _tecla(robot, tecla, mod)
        assert robot.dicho() and "Lugares" not in robot.dicho()
    while robot.app.pila[-1] is not p:
        robot.app.cerrar(robot.app.pila[-1])
    p.correr_fijo = True
    p.cfg["correr_alternar"] = False
    robot.app.teclas.clear()
    robot.app.teclas.add(pygame.K_RSHIFT)
    assert not p.corriendo_ahora()
    robot.app.teclas.add(pygame.K_LSHIFT)
    assert p.corriendo_ahora()
    robot.app.teclas.clear()


# ------------------------------------------------------------------ descargas
def test_progreso_de_la_descarga_al_pulsar_una_tecla(robot):
    from juego import menus_actualizar as ma
    assert ma.texto_progreso(180 * 2 ** 20, 430 * 2 ** 20) == "41 por ciento: 180 de 430 megas."
    assert ma.texto_progreso(5 * 2 ** 20, 0) == "5 megas descargados."
    t = ma.Tarea(robot.app, "Descargando la versión 9", lambda tarea: 1, lambda r, e: None)
    t.fondo = True
    t.estado = "41 por ciento: 180 de 430 megas."
    robot.app.voz.registro.clear()
    t.tecla(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=" "))
    assert "41 por ciento" in robot.dicho()
    # en segundo plano: termina sola y avisa
    hecho = []
    t2 = ma.Tarea(robot.app, "Descarga", lambda tarea: 7, lambda r, e: hecho.append((r, e)))
    assert not t2.paso_fondo()
    t2._correr()
    assert t2.paso_fondo() and hecho == [(7, None)]


# ------------------------------------------------------------------ gimnasio, ropa y armería
def test_velada_de_artes_marciales_mixtas(robot):
    p = robot.nueva_partida()
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "gimnasio")
    p.j.x, p.j.y = l.x, l.y
    p.empezar_mma(l)
    ms = p.mision
    assert ms and ms["def"]["id"] == "mma" and len(ms["def"]["pasos"]) == 3
    saludes = [paso["enemigos"][0]["salud"] for paso in ms["def"]["pasos"]]
    assert saludes == sorted(saludes) and saludes[0] < saludes[2] and p.j.arma == "punos"
    p.abandonar_mision() if hasattr(p, "abandonar_mision") else None


def test_complementos_y_ropa_con_refuerzos(robot):
    from juego import menus_lugares as ml
    p = robot.nueva_partida()
    assert p.aspecto_txt() == "Llevas puesto: ropa de calle."
    p.j.accesorios["gafas"] = "Gafas de sol"
    p.j.accesorios["cadena"] = "Cadena de oro"
    assert p.aspecto_txt() == "Llevas puesto: ropa de calle, con gafas de sol y cadena de oro."
    d = p.j.a_dict()
    assert d["accesorios"] == {"gafas": "Gafas de sol", "cadena": "Cadena de oro"}
    clases = {c["clase"] for c in p.datos["complementos"]}
    assert {"gafas", "cadena", "anillo"} <= clases and any(x.get("blindaje") for x in p.datos["prendas"])
    assert not hasattr(ml, "PRENDAS") and not hasattr(ml, "COMPLEMENTOS")       # están en los datos, no en el código


def test_protecciones_de_la_armeria(robot):
    from juego import menus_juego as mj
    p = robot.nueva_partida()
    p.j.dinero = 10000
    pr = p.datos["protecciones"][0]
    nombre, precio, tope = pr["nombre"], pr["precio"], pr["blindaje"]
    mj._proteccion(p, nombre, precio, tope)
    assert p.j.blindaje == tope == 150 and p.j.dinero == 10000 - precio and "Pechera táctica puesta" in robot.dicho()
    mj._proteccion(p, nombre, precio, tope)
    assert p.j.dinero == 10000 - precio                        # ya la llevas: no se cobra dos veces


def test_oficios_nuevos_y_vendedor_de_coches(robot):
    from juego import vida
    p = robot.nueva_partida()
    claves = {c["id"] for c in p.datos["jornadas"]}
    assert {"carpintero", "soldador", "camarero"} <= claves and not hasattr(vida, "JORNADAS")
    l = next(x for x in p.lugares.values() if x.tipo == "concesionario")
    antes = p.j.dinero
    p.jornada_vendedor(l)
    assert p.j.dinero > antes and p.j.jornada_dia == p.dia and "exposición" in robot.dicho()
    robot.app.voz.registro.clear()
    p.jornada_vendedor(l)
    assert "ya has trabajado" in robot.dicho()


def test_todo_lo_nuevo_esta_en_los_datos_y_el_editor_lo_edita(robot):
    from editor import esquema as E
    from juego import mundo
    p = robot.nueva_partida()
    secciones = {s: e for s, _t, e in E.SECCIONES}
    for clave in mundo.SECCIONES_VIDA:
        assert p.datos[clave], clave                              # el juego trae contenido en cada una
        assert clave in secciones, clave                          # y el editor tiene su sección
        campos = {c["k"] for c in E.ESQUEMAS[secciones[clave]]["campos"]}
        for d in p.datos[clave]:
            assert set(d) <= campos, (clave, set(d) - campos)     # y sabe editar cada campo
    lugar = {c["k"] for c in E.ESQUEMAS["lugar"]["campos"]}
    veh = {c["k"] for c in E.ESQUEMAS["vehiculo"]["campos"]}
    assert {"surtidor", "precio_litro"} <= lugar and {"deposito", "sin_motor"} <= veh


def test_un_mod_cambia_ropa_combates_y_combustible(robot, tmp_path, monkeypatch):
    import json

    from juego import mundo, rutas
    mod = {"info": {"nombre": "prueba"},
           "prendas": [{"id": "poncho", "nombre": "Poncho", "precio": 33}, {"id": "chandal", "nombre": "Chándal de marca", "precio": 300}],
           "combates": [{"id": "lucha", "nombre": "Lucha canaria", "inscripcion": 10, "asaltos": 2, "rivales": ["el Pollo", "el Roble"], "salud": 40, "premio": 90}],
           "combustible": [{"id": "general", "precio_litro": 2.5, "depositos": {"motor_moto": 20}}]}
    (tmp_path / "prueba.json").write_text(json.dumps(mod, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    try:
        d = mundo.cargar_datos()
        nombres = {x["id"]: x["nombre"] for x in d["prendas"]}
        assert nombres["poncho"] == "Poncho" and nombres["chandal"] == "Chándal de marca"
        assert any(c["id"] == "lucha" for c in d["combates"]) and any(c["id"] == "boxeo" for c in d["combates"])
        assert C.PRECIO_LITRO == 2.5 and C.deposito({"id": "moto", "motor": "motor_moto"}) == 20
        p = robot.nueva_partida()
        l = next(x for x in p.mundo.lugares.values() if x.tipo == "gimnasio")
        p.empezar_combate(l, next(c for c in d["combates"] if c["id"] == "lucha"))
        assert p.mision["def"]["id"] == "lucha" and len(p.mision["def"]["pasos"]) == 2
        p.abandonar_mision()
    finally:
        monkeypatch.undo()
        mundo.cargar_datos()                                      # los ajustes del combustible vuelven a ser los del juego
    assert C.PRECIO_LITRO == 1.6 and C.deposito({"id": "moto", "motor": "motor_moto"}) == 14


def test_cada_gasolinera_puede_tener_su_precio(robot):
    p = robot.nueva_partida()
    l = next(x for x in p.mundo.lugares.values() if C.tiene_surtidor(x))
    assert C.precio_litro(l) == C.PRECIO_LITRO and C.precio_litro(None) == C.PRECIO_LITRO
    l.d["precio_litro"] = 2.0
    try:
        assert C.precio_litro(l) == 2.0
    finally:
        l.d.pop("precio_litro")


# ------------------------------------------------------------------ ayudas en las misiones
def _mision_seguir(p):
    return next(m for m in p.datos["misiones"] if any(paso["tipo"] == "seguir" for paso in m["pasos"]))


def test_a_quien_sigues_a_pie_te_espera_hasta_que_das_con_el(robot):
    p = robot.nueva_partida()
    m = _mision_seguir(p)
    n = next(i for i, paso in enumerate(m["pasos"]) if paso["tipo"] == "seguir")
    paso = m["pasos"][n]
    l = p.lugares[paso["lugar"]]
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x + 250, l.y)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + 300, l.y)        # la misión te pilla lejos
    p.iniciar_mision(dict(m, pasos=[paso], requiere=[]))
    robot.frames(30)
    o = p.mision["movil"]
    assert not o["visto"] and p.gps is not None
    x0, y0 = o["x"], o["y"]
    for _ in range(40):                                        # veinte segundos largos: sigue donde estaba y no has fallado
        p._paso_seguir(p.mision, paso, p.j.x, p.j.y, 0.5)
    assert p.mision is not None and (o["x"], o["y"]) == (x0, y0)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + 25, l.y)
    robot.app.voz.registro.clear()
    p._paso_seguir(p.mision, paso, p.j.x, p.j.y, 0.5)
    assert o["visto"] and "Ahí está" in robot.dicho()


def test_la_persecucion_afloja_si_ya_se_te_escapo(robot):
    p = robot.nueva_partida()
    m = next(x for x in p.datos["misiones"] if any(paso["tipo"] == "perseguir" and paso.get("limite") for paso in x["pasos"]))
    paso = next(q for q in m["pasos"] if q["tipo"] == "perseguir")
    l = p.lugares[paso["lugar"]]
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x + 30, l.y)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + 30, l.y)
    p.iniciar_mision(dict(m, pasos=[paso], requiere=[]))
    robot.frames(10)
    v0, t0 = p.mision["vel_huida"], p.mision["limite"]
    p.abandonar_mision()
    p.fallos[m["id"]] = 2
    p.iniciar_mision(dict(m, pasos=[paso], requiere=[]))
    robot.frames(10)
    assert p.mision["vel_huida"] < v0 * 0.85 and p.mision["limite"] > t0 * 1.2 and "va más nervioso" in robot.dicho()
    p.abandonar_mision()


def test_el_piloto_da_media_vuelta_solo(robot):
    p = robot.nueva_partida()
    p.cfg["piloto_gps"] = True
    p.cfg["conduccion"] = "asistida"
    v = _coche(p)
    v.x, v.y = 3 * M.B + 40.0, p.mundo.carril("H", 3, 1)
    v.dir, v.rumbo, v.vel = 1, 90.0, 4.0
    p.fijar_gps(2 * M.B + 10.0, 3 * M.B, "atrás")           # el destino queda a la espalda
    p.gps["ruta"] = [(2 * M.B + 10.0, 3 * M.B)]
    p._pilotar(v, 0.05, v.modelo["freno"])
    assert v.dir == 3 and "El piloto da media vuelta" in robot.dicho()
    p.cfg["piloto_gps"] = False


def test_media_vuelta_dice_la_tecla():
    import inspect

    from juego import partida
    assert "Da media vuelta: frena y pulsa U. " in inspect.getsource(partida)


# ------------------------------------------------------------------ Mi música
def test_mi_musica_sigue_por_donde_iba(robot):
    import time

    from juego import musica
    r = robot.app.radio
    ruta = "x:/cancion.mp3"
    pausa = r.pausa
    try:
        r._recuerdo = {"ruta": ruta, "pos": 130.0, "cuando": time.time() - 65.0, "dur": 600.0}
        r.pausa = True                                            # de serie: en pausa, sigue justo donde quedó
        assert r._desde_recuerdo(ruta) == 130.0
        assert r._desde_recuerdo("x:/otra.mp3") == 0.0
        r.pausa = False                                           # como una emisora de verdad: sigue sonando sin ti
        assert 194.0 <= r._desde_recuerdo(ruta) <= 197.0
        r._recuerdo = {"ruta": ruta, "pos": 590.0, "cuando": time.time() - 30.0, "dur": 600.0}
        assert 19.0 <= r._desde_recuerdo(ruta) <= 22.0            # da la vuelta
        assert musica.TROZO == 60.0
    finally:
        r.pausa = pausa
        r._recuerdo = None
        r._recuerdos.pop("usuario", None)


# ------------------------------------------------------------------ combustible
def test_depositos():
    assert C.deposito({"id": "bici"}) == 0 and C.deposito({"id": "lancha", "barco": True}) == 0
    assert C.deposito({"id": "moto", "motor": "motor_moto"}) == 14 and C.deposito({"id": "sedan", "motor": "motor_coche"}) == 45
    assert C.deposito({"id": "raro", "deposito": 90}) == 90


def test_el_combustible_viene_desactivado(robot):
    p = robot.nueva_partida()
    assert p.cfg["combustible"] is False
    v = _coche(p)
    v.vel = 20.0
    assert p.gastar_combustible(v, 10.0) and getattr(v, "litros", None) is None and p.combustible_txt(v) == ""


def test_gastar_reserva_y_quedarse_seco(robot):
    p = robot.nueva_partida()
    p.cfg["combustible"] = True
    v = _coche(p)
    v.propio = True
    assert p.litros(v) == 45
    v.vel = 20.0
    assert p.gastar_combustible(v, 1.0) and 44.5 < v.litros < 45
    rapido = 45 - v.litros
    v.litros, v.vel = 45.0, 8.0
    p.gastar_combustible(v, 2.5)                              # los mismos metros, más despacio: gasta menos
    assert 45 - v.litros < rapido
    v.litros, v.vel = 45 * 0.151, 20.0
    robot.app.voz.registro.clear()
    for _ in range(40):
        p.gastar_combustible(v, 0.1)
    assert "Entras en reserva" in robot.dicho() and "asolinera" in robot.dicho()
    v.litros = 0.01
    robot.app.voz.registro.clear()
    assert not p.gastar_combustible(v, 1.0) and v.seco and "sin combustible" in robot.dicho()
    v.vel = 10.0
    robot.app.teclas.add(pygame.K_UP)
    for _ in range(20):
        p.conducir(0.1)
    robot.app.teclas.clear()
    assert v.vel < 10.0                                        # el motor no empuja
    assert "Depósito al 0 por ciento" in p.combustible_txt(v)
    p.cfg["combustible"] = False


def test_repostar_bidon_y_asistencia(robot):
    p = robot.nueva_partida()
    p.cfg["combustible"] = True
    p.j.dinero = 1000
    v = _coche(p)
    v.litros = 5.0
    n = p.repostar(v, 10)
    assert n == 10 and v.litros == 15 and p.j.dinero == 1000 - 16
    n = p.repostar(v)
    assert v.litros == 45 and p.j.dinero == 1000 - 16 - 48 and p.repostar(v) == 0
    v.litros = 0.0
    v.seco = True
    p.usar_bidon()
    assert "No llevas ningún bidón" in robot.dicho()
    p.j.objetos["bidon"] = 1
    p.usar_bidon()
    assert v.litros == C.LITROS_BIDON and p.j.objetos["bidon"] == 0 and not v.seco
    antes = p.j.dinero
    assert p.asistencia_carretera() and v.litros == C.LITROS_BIDON + C.LITROS_ASISTENCIA and p.j.dinero == antes - C.PRECIO_ASISTENCIA
    p.cfg["combustible"] = False


def test_hay_gasolinera_en_cada_localidad_con_trafico(robot):
    p = robot.nueva_partida()
    for m in p.mapas.values():
        if m.tipo == "mar" or not getattr(m, "trafico", 1):
            continue
        if m.id in ("isla_tortuga", "plataforma"):
            continue
        if any(l.id.startswith(("cd_", "vo_", "pa_", "oc_", "iv_", "nn_", "ma_")) for l in m.lugares.values()):
            continue                                           # las de los mods traen las suyas, o tiran de asistencia
        assert any(C.tiene_surtidor(l) for l in m.lugares.values()), m.id


def test_el_surtidor_sale_en_la_tienda_y_se_reposta_sin_bajarse(robot):
    from juego import menus_juego as mj
    p = robot.nueva_partida()
    l = next(x for x in p.mundo.lugares.values() if C.tiene_surtidor(x))
    assert mj._surtidor(p, l) == []                            # con la opción quitada, es una tienda sin más
    p.cfg["combustible"] = True
    p.j.dinero = 500
    v = _coche(p)
    v.litros = 10.0
    ops = mj._surtidor(p, l)
    assert len(ops) == 3 and "Llenar el depósito de" in ops[0].texto
    ops[0].accion()
    assert v.litros == 45 and "litros a" in robot.dicho()
    p.cfg["combustible"] = False


def test_el_deposito_se_guarda_con_la_partida(robot):
    p = robot.nueva_partida()
    p.cfg["combustible"] = True
    v = _coche(p)
    v.litros = 12.3
    p.salir_vehiculo(forzado=True)
    assert p._veh_fuera_dict(v)["litros"] == 12.3
    p.cfg["combustible"] = False


# ------------------------------------------------------------------ cómo va vestido otro jugador
def test_mayusculas_j_dice_como_va_vestido_otro_jugador(robot):
    from juego.online import Remoto
    p = robot.nueva_partida()
    robot.app.voz.registro.clear()
    p.mirar_jugador()
    assert "cuando juegas con amigos o en un servidor" in robot.dicho()
    p.j.accesorios["gafas"] = "Gafas de sol"
    assert p.aspecto_corto() == "ropa de calle, con gafas de sol"
    enviados = []

    class Red:
        conectado = True
        id = 1

        def enviar(self, m):
            enviados.append(m)
    p.red = Red()
    p.online_activo = lambda: True
    try:
        p._t_aspecto = 0.0
        p._contar_aspecto(0.1)
        assert enviados == [{"t": "act", "d": {"que": "aspecto", "texto": "ropa de calle, con gafas de sol"}}]
        p._t_aspecto = 0.0
        p._contar_aspecto(0.1)
        assert len(enviados) == 1                                 # no se repite si no te cambias
        r = Remoto(7, "Vera")
        r.mapa, r.visto = p.mundo.id, True
        r.x, r.y = p.j.x + 6, p.j.y
        p.remotos[7] = r
        p._red_mensaje({"t": "act", "de": 7, "nombre": "Vera", "d": {"que": "aspecto", "texto": "traje elegante, con reloj de oro"}})
        robot.app.voz.registro.clear()
        _tecla(robot, pygame.K_j, pygame.KMOD_RSHIFT)
        assert "Vera, a 6 metros, lleva traje elegante, con reloj de oro." in robot.dicho()
        r.x = p.j.x + 200
        robot.app.voz.registro.clear()
        p.mirar_jugador()
        assert "No tienes a ningún jugador cerca" in robot.dicho()
    finally:
        p.remotos.pop(7, None)
        p.red = None
        del p.online_activo
