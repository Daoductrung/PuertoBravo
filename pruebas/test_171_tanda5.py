"""Trabajo 1.7.1, tanda 5: comida a domicilio, atracos a cualquier local con caja, asaltos a proveedores, negociar con
las bandas, contratos variados, tutoriales que comprueban lo que haces, gente que actúa y se une a tu banda, vivir en
pareja y el oficio de policía."""
import json
import math
import os

import pygame
import pytest

from juego import agente as AG, ajustes, atracos as AT, config, contratos as CO, convivencia as CV, domicilio as DO, gente as G, mundo as M, pactos as PA, reacciones as RE, rutas, sintesis
from juego.charla import ficha
from juego.entidades import Persona
from juego.menus import Dialogo, Menu


@pytest.fixture
def datos_de_serie():
    """Deja los números y las frases como vienen en los datos, por si una prueba los ha cambiado."""
    yield
    M.cargar_datos()


def _empezar(robot, adultos=False, **opciones):
    """Una partida nueva con la calle vacía y sin nada que estorbe."""
    if adultos:
        robot.app.cfg["adultos"] = True
        robot.app.aplicar_adultos()
    p = robot.nueva_partida()
    for k, v in dict(sucesos=False, patrullas_calle=False, ambulancias=False, charla_peatones="nada", **opciones).items():
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


def _hasta(robot, condicion, segundos=60.0):
    for _ in range(int(segundos * 30)):
        if condicion():
            return True
        robot.frames(1)
    return bool(condicion())


def _todo(robot):
    return " | ".join(robot.app.voz.registro)


def _texto(o):
    return o.texto() if callable(o.texto) else o.texto


def _opcion(m, empieza):
    return next(o for o in m.opciones if _texto(o).startswith(empieza))


def _elegir(robot, empieza):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if _texto(o).startswith(empieza))
    robot.tecla(pygame.K_RETURN)
    return m


def _cerrar_menus(robot):
    p = robot.p
    while robot.app.pila[-1] is not p:
        robot.app.cerrar(robot.app.pila[-1])


def _a(p, l, dx=0.0):
    """Lleva al jugador, a pie, a la puerta de un lugar."""
    if p.j.veh:
        p.salir_vehiculo(forzado=True)
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + dx, l.y)


def _lugar(p, tipo, mapa=None):
    return next(l for l in (p.mapas[mapa] if mapa else p.mundo).lugares.values() if l.tipo == tipo)


def _armar(p, arma="pistola", balas=60):
    p.dar_arma(arma, balas)
    p.j.arma = arma


def _persona(p, tipo="civil", dx=3.0, nombre=None, **attrs):
    q = Persona(tipo, *p.mundo.punto_libre(p.pos()[0] + dx, p.pos()[1]), nombre)
    for k, v in attrs.items():
        setattr(q, k, v)
    p.personas.append(q)
    return q


def _acabar_enemigos(robot, p):
    """Tumba a los enemigos del paso «eliminar» en curso, estén donde estén (también los que aún vienen en un vehículo)."""
    ms = p.mision
    assert ms and ms["def"]["pasos"][ms["paso"]]["tipo"] == "eliminar", ms and ms["def"]["pasos"][ms["paso"]]
    if not ms["generado"]:
        l = p.lugares[ms["def"]["pasos"][ms["paso"]]["lugar"]]
        _a(p, l, 3.0)
        robot.frames(3)
    for v in list(ms.get("veh_enemigos", [])):
        if getattr(v, "pasajeros", None):
            p.bajar_enemigos(v)
    for e in list(ms["enemigos"]):
        p.danar_persona(e, 9999)
    robot.frames(3)
    robot.saltar_dialogos()


# ====================================================================== 1. comida a domicilio
def test_pedir_comida_a_domicilio_desde_casa(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    j = p.j
    casa = p.lugares["casa_abuela"]
    j.dinero = 200
    # lejos de casa no se puede, y el móvil no lo ofrece
    _a(p, _lugar(p, "banco"))
    assert p.casa_aqui() is None and "tienes que estar en una casa tuya" in p.domicilio_motivo()
    robot.tecla(pygame.K_m)
    assert not [o for o in robot.app.pila[-1].opciones if _texto(o).startswith("Pedir comida")]
    _cerrar_menus(robot)
    # en casa, sí: en el móvil y en el menú de la casa
    _a(p, casa, 4.0)
    assert p.casa_aqui() is casa and p.domicilio_motivo() == ""
    robot.tecla(pygame.K_m)
    o = _opcion(robot.app.pila[-1], "Pedir comida a domicilio")
    assert o.ayuda and "timbre" in o.ayuda
    _elegir(robot, "Pedir comida a domicilio")
    carta = robot.app.pila[-1]
    assert "Comida a domicilio en " + casa.nombre in carta.titulo
    textos = [_texto(x) for x in carta.opciones]
    assert any(t.startswith("Pizza familiar: 13 euros") for t in textos) and any("Botella grande de agua" in t for t in textos)
    assert len(textos) == len(DO.carta(p)) + 2                    # la carta, hacer el pedido y volver
    _elegir(robot, "Hacer el pedido")                             # sin elegir nada, no hay pedido
    assert j.pedido is None and "No has elegido nada" in robot.dicho()
    _elegir(robot, "Pizza familiar")
    _elegir(robot, "Botella grande de agua")
    assert "En el pedido" in _texto(_opcion(carta, "Pizza familiar"))
    envio = p.precio("domicilio_envio", 3)
    assert f"Hacer el pedido: 2 cosas, {13 + 2 + envio} euros con el envío" == _texto(_opcion(carta, "Hacer el pedido"))
    _elegir(robot, "Hacer el pedido")
    assert robot.app.pila[-1] is not carta and j.dinero == 200 - 15 - envio
    d = j.pedido
    assert d["casa"] == casa.id and d["estado"] == "camino" and [c["id"] for c in d["cosas"]] == ["pizza_casa", "agua_grande"]
    espera = d["llega"] - p._ahora()
    assert DO.AJ("espera_min") <= espera <= DO.AJ("espera_max") * 1.3      # alrededor de media hora del juego
    assert any(f in _todo(robot) for f in (d["local"],)) and "minutos" in robot.dicho()
    _cerrar_menus(robot)
    assert "Ya tienes un pedido en camino" in p.domicilio_motivo()         # no se piden dos a la vez
    # pasa el rato y llaman al timbre: te lo tomas, y quita hambre y sed
    j.hambre, j.sed, j.salud = 80.0, 90.0, 50.0
    son = _oir(p)
    robot.frames(10)
    assert j.pedido is not None and "timbre" not in son                    # todavía no
    d["llega"] = p._ahora() - 0.1
    robot.frames(3)
    assert j.pedido is None and "timbre" in son and "Llaman al timbre" in robot.dicho()
    assert j.hambre <= 80 - 70 + 1 and j.sed < 20 and j.salud == 75.0
    assert j.stats["pedidos"] == 1


def test_el_repartidor_espera_y_se_va_si_no_estas(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    casa = p.lugares["casa_abuela"]
    j.dinero = 100
    _a(p, casa, 3.0)
    assert p.pedir_domicilio([DO.carta(p)[0]])
    _a(p, _lugar(p, "banco"))
    j.pedido["llega"] = p._ahora() - 0.1
    robot.frames(3)
    assert j.pedido["estado"] == "puerta" and ("Te llama " in _todo(robot) or "Suena el móvil" in _todo(robot))      # te llama: está en la puerta
    # si vuelves a tiempo, te lo da
    _a(p, casa, 3.0)
    robot.frames(3)
    assert j.pedido is None and "Llaman al timbre" in robot.dicho()
    # y si no vuelves, se va con el pedido y no devuelven el dinero
    dinero = j.dinero
    assert p.pedir_domicilio([DO.carta(p)[1]])
    pagado = dinero - j.dinero
    assert pagado == 13 + p.precio("domicilio_envio", 3)
    _a(p, _lugar(p, "banco"))
    j.pedido["llega"] = p._ahora() - 0.1
    robot.frames(3)
    j.pedido["hasta"] = p._ahora() - 0.1
    robot.frames(3)
    assert j.pedido is None and j.dinero == dinero - pagado
    assert any(f.split("{")[0] in _todo(robot) or "pedido" in robot.dicho() for f in DO.AJ.lista("frases_se_va"))
    # con la policía buscándote, nadie sube
    _a(p, casa, 3.0)
    j.estrellas = 3
    assert "ningún repartidor" in p.domicilio_motivo()
    j.estrellas = 0
    # el pedido se guarda con la partida
    assert p.pedir_domicilio([DO.carta(p)[0]])
    guardado = json.loads(json.dumps(p.a_dict()))
    assert guardado["jugador"]["pedido"]["casa"] == casa.id
    from juego.entidades import Jugador
    otro = Jugador()
    otro.de_dict(guardado["jugador"])
    assert otro.pedido["local"] == j.pedido["local"]


def test_la_carta_y_los_tiempos_salen_de_los_datos(datos_de_serie):
    d = M.cargar_datos(con_mods=False)
    assert [c["id"] for c in d["carta_domicilio"]] == [c["id"] for c in DO.CARTA]
    assert any(t["id"] == "domicilio_envio" and t["precio"] == 3 for t in d["tarifas"])
    for modulo, seccion in ((DO, "domicilio"), (AT, "atracos"), (PA, "pactos"), (RE, "reacciones"), (CV, "convivencia"), (AG, "policia_oficio")):
        aj = modulo.AJ
        assert set(d[seccion][0]) == set(aj._n) | set(aj._l) | {"id"}, seccion
        for k, v in aj._n.items():
            assert aj(k) == d[seccion][0][k] == v, (seccion, k)       # lo de serie del código y lo de los datos dicen lo mismo
        for k, v in aj._l.items():
            assert aj.lista(k) == d[seccion][0][k] == v, (seccion, k)
    # un mod lo cambia, y lo que venga mal o vacío vale lo de serie
    ajustes.configurar_todos({"domicilio": [{"id": "general", "espera_min": 5, "espera_max": "mal", "locales": ["Casa Pepa"], "frases_llega": []}]})
    assert DO.AJ("espera_min") == 5 and DO.AJ("espera_max") == 40 and DO.AJ.lista("locales") == ["Casa Pepa"] and DO.AJ.lista("frases_llega") == DO.AJ._l["frases_llega"]
    ajustes.configurar_todos({})
    assert DO.AJ.n == DO.AJ._n and AT.AJ.n == AT.AJ._n
    assert [c["id"] for c in d["contratos"]] == [c["id"] for c in CO.CONTRATOS] and [a["id"] for a in d["avisos_policia"]] == [a["id"] for a in AG.AVISOS]
    assert [x["id"] for x in d["planes_pareja"]] == [x["id"] for x in CV.PLANES]


# ====================================================================== 2. atracar cualquier local con caja
def test_atracar_un_local_sin_guardia_y_que_te_recuerde(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot)
    j = p.j
    far = _lugar(p, "farmacia")
    _a(p, far)
    menus_juego.lugar(p, far)
    m = robot.app.pila[-1]
    o = _opcion(m, "Atracar este local")
    assert far.nombre in _texto(o) and "no hay guardia" in o.ayuda and "te recuerda" in o.ayuda
    _elegir(robot, "Atracar este local")                           # sin arma de fuego, no
    assert "arma de fuego" in robot.dicho() and far.id not in p.atracadas
    _armar(p)
    esperado = p.caja_de_local(far)["dinero"]
    dinero = j.dinero
    _elegir(robot, "Atracar este local")
    assert robot.app.pila[-1] is p and j.dinero == dinero + esperado and 200 <= esperado <= 650
    assert p.atracadas[far.id] == p.dia and j.puntos_busqueda > 0 and j.stats["atracos_locales"] == 1
    assert any(f.split("{")[0] in robot.dicho() for f in AT.AJ.lista("frases_atraco"))
    # el local te recuerda unos días: no te dejan entrar
    r = j.locales_vetados[far.id]
    assert AT.AJ("recuerdo_min") <= r["hasta"] - p.dia <= AT.AJ("recuerdo_max") and r["modo"] in ("cerrado", "hostil")
    p._fin_persecucion()
    r["modo"] = "cerrado"
    menus_juego.lugar(p, far)
    assert robot.app.pila[-1] is p and far.nombre in robot.dicho()
    assert any(f.split("{lugar}. ")[1].split("{")[0] in robot.dicho() for f in AT.AJ.lista("frases_cerrado"))
    # hostil: al verte llaman a la policía (otro día), y desde entonces cierran
    p.dia += 1
    r["modo"] = "hostil"
    menus_juego.lugar(p, far)
    assert robot.app.pila[-1] is p and j.puntos_busqueda > 0 and r["modo"] == "cerrado"
    p._fin_persecucion()
    # cuando se les pasa, vuelven a atenderte
    p.dia = r["hasta"] + 1
    menus_juego.lugar(p, far)
    assert isinstance(robot.app.pila[-1], Menu) and far.id not in j.locales_vetados
    _cerrar_menus(robot)
    # el banco no se atraca así (tiene el suyo), ni una casa
    assert not p.local_atracable(_lugar(p, "banco")) and not p.local_atracable(p.lugares["casa_abuela"])


def test_atracar_un_local_con_guardia(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot, invulnerable=True)
    j = p.j
    gim = _lugar(p, "gimnasio")
    _a(p, gim)
    _armar(p)
    menus_juego.lugar(p, gim)
    o = _opcion(robot.app.pila[-1], "Atracar este local")
    assert "La caja tiene guardia: 2 personas" in o.ayuda
    esperado = p.caja_de_local(gim)["dinero"]
    dinero = j.dinero
    _elegir(robot, "Atracar este local")
    ms = p.mision
    assert ms and ms["def"]["id"] == "atraco_local" and gim.nombre in ms["def"]["titulo"] and robot.app.pila[-1] is p
    assert len(ms["enemigos"]) == 2 and all(e.clase == "maton" for e in ms["enemigos"])       # la guardia que dicen los datos
    assert j.dinero == dinero                                       # todavía no hay botín
    _acabar_enemigos(robot, p)
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "recoger" and ms["objeto"] is not None
    p.recoger(ms["objeto"])
    robot.frames(3)
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "policia" and j.puntos_busqueda > 0
    p._fin_persecucion()
    robot.frames(3)
    assert p.mision is None and j.dinero >= dinero + esperado and j.stats["atracos_con_guardia"] == 1
    assert gim.id in j.locales_vetados
    # el taller, a pie, también tiene su menú para poder atracarlo; y la armería, y un bar
    for tipo in ("taller", "armeria", "bar"):
        l = _lugar(p, tipo)
        _a(p, l)
        menus_juego.lugar(p, l)
        assert isinstance(robot.app.pila[-1], Menu) and _opcion(robot.app.pila[-1], "Atracar este local"), tipo
        _cerrar_menus(robot)
    # con otra cosa entre manos, no se empieza un atraco con guardia
    p.trabajo = {"tipo": "pizza", "quedan": 1, "ganado": 0, "limite": None, "lugar": gim, "texto": ""}
    assert "Termina antes" in p.atraco_motivo(_lugar(p, "armeria"))
    p.trabajo = None


# ====================================================================== 3. asaltar a los proveedores
def test_asaltar_a_un_proveedor(robot, datos_de_serie):
    from juego import menus_adultos
    p = _empezar(robot, adultos=True, invulnerable=True)
    j = p.j
    prov = _lugar(p, "proveedor")
    _a(p, prov)
    menus_adultos.proveedor(p, prov)
    m = robot.app.pila[-1]
    o = _opcion(m, "Asaltar a este proveedor")
    assert "deja de venderte" in o.ayuda and "manda gente" in o.ayuda
    _elegir(robot, "Asaltar a este proveedor")
    assert "arma de fuego" in robot.dicho() and p.mision is None
    _armar(p)
    AT.AJ.n.update(peso_veto=100, peso_caro=0, peso_represalia=0)
    dinero = j.dinero
    esperado = p.caja_de_local(prov)["dinero"]
    _elegir(robot, "Asaltar a este proveedor")
    ms = p.mision
    assert ms and ms["def"]["id"] == "asalto_proveedor" and robot.app.pila[-1] is p
    guardia = [e for e in ms["enemigos"]] + [q for v in ms.get("veh_enemigos", []) for q in v.pasajeros]
    assert len({id(e) for e in guardia}) >= 3 and any(e.clase == "pandillero" for e in guardia)
    _acabar_enemigos(robot, p)
    p.recoger(p.mision["objeto"])
    robot.frames(3)
    assert p.mision is None and j.dinero >= dinero + esperado
    cogido = p.carga()
    assert AT.AJ("proveedor_mercancia_min") <= cogido <= AT.AJ("proveedor_mercancia_max") and "Te llevas la mercancía" in _todo(robot)
    # consecuencia: deja de venderte unos días
    dias = p.proveedor_vetado(prov)
    assert AT.AJ("proveedor_veto_min") <= dias - 1 <= AT.AJ("proveedor_veto_max") and j.proveedores[prov.id]["consecuencia"] == "veto"
    menus_adultos.proveedor(p, prov)
    textos = [_texto(x) for x in robot.app.pila[-1].opciones]
    assert any("no te venden nada" in t for t in textos) and not any("euros" in t and ":" in t and "Llevas" in t for t in textos)
    _cerrar_menus(robot)
    assert "no han vuelto a traer género" in p.asalto_motivo(prov)   # y no se le asalta otra vez enseguida
    p.dia += int(AT.AJ("proveedor_veto_max")) + 2
    assert p.proveedor_vetado(prov) == 0 and p.asalto_motivo(prov) == ""
    # consecuencia: precios más altos
    s = p.dato_adulto("sustancias")
    ident = next(x["id"] for x in s if not x.get("legal"))
    antes = p.precio_sustancia(ident, prov)[0]
    j.proveedores[prov.id]["caro"] = p.dia + 3
    assert p.factor_proveedor(prov) == 1.6 and p.precio_sustancia(ident, prov)[0] >= int(antes * 1.5)
    j.proveedores[prov.id]["caro"] = 0
    # consecuencia: mandan gente a por ti
    j.represalias.append({"cuando": p._ahora() - 1, "lugar": prov.nombre, "n": 3})
    _vaciar(p)
    assert _hasta(robot, lambda: not j.represalias, 6)
    vienen = [q for q in p.personas if q.tag == "represalia"] + [q for v in p.vehiculos for q in getattr(v, "pasajeros", [])]
    assert len(vienen) == 3 and all(q.agresor for q in vienen) and (f"Los de {prov.nombre}" in _todo(robot))


def test_el_asalto_es_solo_del_contenido_para_adultos_y_no_va_en_un_servidor(robot, datos_de_serie):
    p = _empezar(robot)
    _armar(p)
    assert not [l for l in p.lugares.values() if l.tipo == "proveedor"]      # sin el contenido para adultos, ni existen
    prov = type("Lugar", (), {"id": "prov_x", "tipo": "proveedor", "nombre": "La trastienda"})()
    assert "contenido para adultos" in p.asalto_motivo(prov) and not p.asaltar_proveedor(prov)
    p.cfg["adultos"] = True
    p.en_servidor = True
    try:
        assert "servidor" in p.asalto_motivo(prov)
        assert "servidor" in p.pactos_motivo() and "servidor" in p.recluta_motivo(_persona(p))[1]
        assert not p.policia_activa() and not p.convivencia_activa()
    finally:
        p.en_servidor = False
        p.cfg["adultos"] = False


# ====================================================================== 4. negociar con las bandas
class _Azar:
    """Un azar que no lo es: siempre lo primero y siempre cero."""

    def random(self):
        return 0.0

    def choice(self, lista):
        return lista[0]

    def uniform(self, a, b):
        return a

    def randint(self, a, b):
        return a


def test_comprar_y_devolver_un_barrio(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    j.dinero = 50000
    barrios = p.mundo.barrios
    b = next(x for x in barrios if x["id"] == "centro")
    banda = p.banda_interesada(b)
    assert banda in G.nombres_bandas() and p.banda_interesada(b) == banda        # siempre la misma en la partida
    assert p.banda_interesada(next(x for x in barrios if x["id"] == "puerto")) == "Los Calaveras"      # la que dicen los datos
    si, euros, frase = p.oferta_comprar(b)
    assert si and 100 <= euros <= PA.AJ("comprar_base") * 1.7 and banda in frase and str(euros) in frase and b["nombre"] in frase
    assert p.oferta_comprar(b)[1] == euros                         # el mismo día, la misma cifra
    cifras = set()
    for dia in range(1, 12):
        p.dia = dia
        cifras.add(p.oferta_comprar(b)[1])
    assert len(cifras) > 4                                         # y cada día, otra
    p.dia = 1
    assert p.comprar_barrio(b, euros) and b["id"] in j.territorios and j.dinero == 50000 - euros
    assert p.rep_banda(banda) == 5 and p.trato_espera(banda, "comprar", b["id"]) == PA.AJ("espera_dias")
    # con quien te la tiene jurada, y pesando poco, no hay venta
    b2 = next(x for x in barrios if x["id"] == "playa")
    banda2 = p.banda_interesada(b2)
    j.rep_bandas[banda2] = -80.0
    assert p.fuerza_propia() < 60 and p.oferta_comprar(b2)[0] is False
    j.rep_bandas[banda2] = 40.0                                    # y a quien te respeta se lo dejan más barato
    barato = p.oferta_comprar(b2)[1]
    j.rep_bandas[banda2] = -10.0
    assert p.oferta_comprar(b2)[1] > barato
    # devolver un barrio a cambio de dinero
    j.rep_bandas[banda] = 0.0
    si, paga, frase = p.oferta_devolver(b)
    assert si and paga >= 50 and str(paga) in frase
    dinero = j.dinero
    assert p.devolver_barrio(b, paga) and b["id"] not in j.territorios and j.barrios_banda[b["id"]] == banda and j.dinero == dinero + paga
    assert p.rep_banda(banda) == 12 and "de la banda de " + banda in p.barrio_dueno_txt(b)
    # si os lleváis a matar, ni eso
    j.territorios.append(b["id"])
    j.rep_bandas[banda] = -70.0
    assert p.oferta_devolver(b)[0] is False
    # regatear: sale o no sale, pero solo cambia la cifra o rompe el trato
    j.rep_bandas[banda] = 0.0
    r = p.regatear(banda, 1000, "devolver", "x")
    assert r is None or r == 1250
    r = p.regatear(banda, 1000, "comprar", "y")
    assert r is None or r == 800


def test_cobrar_un_tributo_a_una_banda(robot, datos_de_serie):
    from juego import sistemas
    p = _empezar(robot)
    j = p.j
    banda = "Los Calaveras"
    assert "Sin un solo barrio" in p.pedir_tributo(banda) and not j.tributos
    # con fuerza de sobra, pagan (el azar de cada día decide; se prueba hasta que sale)
    j.territorios = ["centro", "playa", "viejo"]
    j.banda, j.reputacion = 6, 100.0
    assert p.fuerza_propia() == 100
    for dia in range(1, 40):
        p.dia = dia
        j.tratos.clear()
        texto = p.pedir_tributo(banda)
        if banda in j.tributos:
            break
    t = j.tributos[banda]
    assert t["euros"] >= 10 and PA.AJ("tributo_dias_min") <= t["hasta"] - p.dia <= PA.AJ("tributo_dias_max") and str(t["euros"]) in texto
    assert "ya te paga" in p.pedir_tributo(banda)
    # cada medianoche, el sobre
    dinero = j.dinero
    PA.AJ.n["plante_prob"] = 0
    p.dia_pactos()
    assert j.dinero == dinero + t["euros"] and j.stats["tributos_cobrados"] == t["euros"]
    # mientras paga, esa banda no ataca tus barrios
    p.cfg["sucesos"] = True
    j.banda = 0
    sistemas.sucesos_territorio(p, _Azar())
    assert j.amenaza is None
    guardado = j.tributos.pop(banda)
    sistemas.sucesos_territorio(p, _Azar())
    assert j.amenaza and j.amenaza["banda"] == banda
    j.amenaza = None
    j.tributos[banda] = guardado
    # el trato se acaba el día acordado
    p.dia = t["hasta"]
    p.dia_pactos()
    assert banda not in j.tributos and any(f.split("{")[0] in _todo(robot) or banda in robot.dicho() for f in PA.AJ.lista("frases_tributo_fin"))
    # sin fuerza se ríen, y a veces mandan a alguien
    j.territorios, j.banda, j.reputacion = ["centro"], 0, 0.0
    PA.AJ.n["ofensa_ataque"] = 100
    negado = False
    for dia in range(100, 130):
        p.dia = dia
        j.tratos.clear()
        rep = p.rep_banda("Los Lagartos")
        p.pedir_tributo("Los Lagartos")
        if "Los Lagartos" not in j.tributos:
            negado = True
            assert p.rep_banda("Los Lagartos") == max(-100, rep - 10)
            break
        del j.tributos["Los Lagartos"]
    assert negado and any(r["lugar"] == "Los Lagartos" for r in j.represalias)
    assert p.trato_espera("Los Lagartos", "tributo") == PA.AJ("espera_dias")
    assert "ya te contestó" in p.pedir_tributo("Los Lagartos")


def test_el_menu_de_negociar_esta_en_territorios(robot, datos_de_serie):
    from juego import menus_extra
    p = _empezar(robot)
    j = p.j
    j.dinero = 90000
    j.territorios = ["centro"]
    menus_extra.territorios(p)
    o = _opcion(robot.app.pila[-1], "Negociar con las bandas")
    assert "devolverles un barrio" in o.ayuda and "tributo" in o.ayuda
    _elegir(robot, "Negociar con las bandas")
    m = robot.app.pila[-1]
    textos = [_texto(x) for x in m.opciones]
    assert sum(t.startswith("Devolver ") for t in textos) == 1 and sum(t.startswith("Comprar ") for t in textos) == len(p.mundo.barrios) - 1
    assert sum(t.startswith("Cobrar un tributo a ") for t in textos) == len(G.nombres_bandas()) and textos[0].startswith("Tu fuerza en la calle")
    assert all(x.ayuda for x in m.opciones[:-1])
    # comprar uno desde el menú: la mesa, con aceptar, regatear y dejarlo
    _elegir(robot, "Comprar Playa Dorada" if any(t.startswith("Comprar Playa Dorada") for t in textos) else "Comprar ")
    mesa = robot.app.pila[-1]
    if mesa is not m:                                              # han puesto precio
        assert [_texto(x).split(":")[0] for x in mesa.opciones] == ["Aceptar", "Pedir una rebaja", "Dejarlo"]
        antes = len(j.territorios)
        _elegir(robot, "Aceptar")
        assert len(j.territorios) == antes + 1
    _cerrar_menus(robot)
    # con la policía detrás, o fuera de una ciudad, no hay con quién hablar
    j.estrellas = 1
    assert "policía" in p.pactos_motivo()
    j.estrellas = 0


# ====================================================================== 5. contratos variados
def test_el_tablon_ofrece_contratos_distintos(robot, datos_de_serie):
    import random
    from juego import menus_lugares
    p = _empezar(robot, invulnerable=True)
    j = p.j
    taberna = p.lugares["taberna_puerto"]
    j.stats["contratos"] = 6
    ofertas = p.ofertas_contrato(taberna)
    assert len(ofertas) == 3 and len({o["tipo"]["id"] for o in ofertas}) == 3
    assert [o["resumen"] for o in p.ofertas_contrato(taberna)] == [o["resumen"] for o in ofertas]      # el tablón no cambia mientras lo miras
    vistos = set()
    for dia in range(1, 120):
        p.dia = dia
        vistos |= {o["tipo"]["situacion"] for o in p.ofertas_contrato(taberna)}
    assert vistos == set(CO.SITUACIONES)                           # con los días salen todas las situaciones
    p.dia = 1
    j.stats["contratos"] = 0                                       # al principio solo los que no piden experiencia
    assert all(int(o["tipo"].get("desde", 0)) == 0 for dia in range(1, 10) for o in (p.__setattr__("dia", dia), p.ofertas_contrato(taberna))[1])
    p.dia = 1
    j.stats["contratos"] = 6
    # el tablón de la taberna
    _a(p, taberna)
    menus_lugares.taberna(p, taberna)
    _elegir(robot, "Tablón de encargos")
    tablon = robot.app.pila[-1]
    assert len(tablon.opciones) == 4 and all("euros" in _texto(o) for o in tablon.opciones[:3])
    _elegir(robot, _texto(tablon.opciones[0])[:20])
    assert p.mision and p.mision["def"]["id"] == "contrato" and robot.app.pila[-1] is p
    p.abandonar_mision()
    # cada situación se monta con sus pasos
    pasos = {"eliminar": ["eliminar", "ir"], "escolta_vehiculo": ["eliminar", "ir"], "huye": ["perseguir", "ir"], "local": ["ir", "eliminar", "ir"],
             "seguir": ["seguir", "eliminar", "ir"], "intimidar": ["eliminar", "ir"], "recuperar": ["eliminar", "recoger", "ir"], "proteger": ["ir", "eliminar", "escoltar", "ir"]}
    for c in CO.tipos(p):
        o = p._oferta(c, taberna, random.Random(7))
        assert o and "{" not in o["resumen"] and o["paga"] == c["paga"] + c["paga_escolta"] * 4, c["id"]
        assert p.empezar_contrato_de(taberna, o)
        m = p.mision["def"]
        assert [x["tipo"] for x in m["pasos"]] == pasos[c["situacion"]], c["id"]
        assert all(x.get("lugar") in p.lugares for x in m["pasos"]) and m["recompensa"]["dinero"] == o["paga"]
        grupos = [g for x in m["pasos"] for g in x.get("enemigos", [])]
        if c["situacion"] == "escolta_vehiculo":
            assert any(g.get("clase") == "escolta_motorizada" for g in grupos)
        if c["situacion"] == "proteger":
            assert any(g.get("clase") == "pandillero_motorizado" for g in grupos)
        if c["situacion"] == "intimidar":
            assert sum(1 for g in grupos if g.get("intimidar")) == 1
        p.abandonar_mision()
    # y con el contrato clásico de siempre no ha cambiado nada
    p.empezar_contrato(taberna)
    assert [x["tipo"] for x in p.mision["def"]["pasos"]] == ["eliminar", "ir"]
    p.abandonar_mision()


def test_un_contrato_de_dar_un_escarmiento(robot, datos_de_serie):
    import random
    p = _empezar(robot, invulnerable=True)
    j = p.j
    taberna = p.lugares["taberna_puerto"]
    c = next(x for x in CO.tipos(p) if x["situacion"] == "intimidar")
    for intento in ("rendir", "matar"):
        o = p._oferta(c, taberna, random.Random(3))
        p.empezar_contrato_de(taberna, o)
        ms = p.mision
        _a(p, o["lugar"], 3.0)
        robot.frames(3)
        assert ms["generado"]
        moroso = next(e for e in ms["enemigos"] if e.intimidar)
        otros = [e for e in ms["enemigos"] if not e.intimidar]
        assert moroso.salud == 120 and moroso.nombre.startswith("Moroso, ") and len(otros) == o["n"]
        for e in otros:
            p.danar_persona(e, 9999)
        p.danar_persona(moroso, 30)                                # aún aguanta
        assert not moroso.muerto and not getattr(moroso, "rendido", False) and moroso.salud == 90
        p.danar_persona(moroso, 200)                               # un golpe que le dejaría seco: se rinde antes de caer
        assert moroso.rendido and not moroso.muerto and not moroso.hostil and "no le toques más" in robot.dicho()
        if intento == "rendir":
            robot.frames(3)
            assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "ir"      # ya está: a cobrar
            contratos, dinero = j.stats.get("contratos", 0), j.dinero
            _a(p, taberna, 2.0)
            robot.frames(3)
            assert p.mision is None and j.stats["contratos"] == contratos + 1 and j.dinero >= dinero + o["paga"]
        else:
            p.danar_persona(moroso, 9999)                          # rematarle es fallar el encargo
            robot.frames(3)
            assert p.mision is None and "asustado, no muerto" in _todo(robot)
            robot.saltar_dialogos()


def test_un_contrato_de_objetivo_a_la_fuga_y_otro_de_recuperar(robot, datos_de_serie):
    import random
    p = _empezar(robot, invulnerable=True)
    taberna = p.lugares["taberna_puerto"]
    c = next(x for x in CO.tipos(p) if x["situacion"] == "huye")
    o = p._oferta(c, taberna, random.Random(5))
    p.empezar_contrato_de(taberna, o)
    ms = p.mision
    _a(p, o["lugar"], 3.0)
    robot.frames(5)
    vo = ms["veh_objetivo"]
    assert vo is not None and vo.modelo["id"] == o["modelo"] and vo.ia == "huida" and vo.salud == 130
    p.danar_vehiculo(vo, 9999)
    assert _hasta(robot, lambda: ms["def"]["pasos"][ms["paso"]]["tipo"] == "ir", 10)
    p.abandonar_mision()
    c = next(x for x in CO.tipos(p) if x["situacion"] == "recuperar")
    o = p._oferta(c, taberna, random.Random(5))
    p.empezar_contrato_de(taberna, o)
    ms = p.mision
    _acabar_enemigos(robot, p)
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "recoger" and ms["objeto"].nombre.lower() == o["objeto"].lower()
    p.recoger(ms["objeto"])
    robot.frames(3)
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "ir" and "Llévalo a " + taberna.nombre in _todo(robot)
    p.abandonar_mision()


# ====================================================================== 6. tutoriales que comprueban lo que haces
def _tutorial(robot, ident):
    p = robot.p
    m = next(x for x in p.datos["misiones"] if x["id"] == ident)
    p.iniciar_mision(m)
    robot.saltar_dialogos()
    robot.frames(3)
    return m


def test_el_tutorial_de_navegar_exige_zarpar_llevar_el_timon_y_atracar(robot, datos_de_serie):
    from juego import menus_lugares
    p = _empezar(robot)
    j = p.j
    dinero = j.dinero
    _tutorial(robot, "tut04")
    emb = p.lugares["emb_puerto"]
    assert p.practica_de("zarpar") and math.hypot(emb.x - j.x, emb.y - j.y) < 30
    assert "lancha de prácticas" in robot.dicho()
    # ir andando a la lonja ya no sirve de nada
    _a(p, p.lugares["lonja"], 2.0)
    robot.frames(40)
    assert p.practica_de("zarpar")
    # el embarcadero presta una lancha para el tutorial
    _a(p, emb, 2.0)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and _texto(m.opciones[0]).startswith("Zarpar con la lancha de prácticas del tutorial: gratis")
    _elegir(robot, "Zarpar con la lancha de prácticas")
    assert p.mundo.id == "mar" and j.veh is not None and j.dinero == dinero
    _vaciar(p)                                                     # sin otros barcos que se crucen
    robot.frames(3)
    assert p.practica_de("timon") and "llevar el timón" in robot.dicho()
    # navegar recto no basta: hay que girar; y girar sin avanzar, tampoco
    assert not _hasta(robot, lambda: not p.practica_de("timon"), 0) and True
    for _ in range(900):
        robot.frames(1, mantener=(pygame.K_UP,))
        if p.mision["practica"]["metros"] >= 230:
            break
    pr = p.mision["practica"]
    assert pr["metros"] >= 200 and pr["giro"] < 90 and p.practica_de("timon")
    assert "Ahora lleva el timón" in _todo(robot)
    for _ in range(900):
        robot.frames(1, mantener=(pygame.K_UP, pygame.K_RIGHT))
        if not p.practica_de("timon"):
            break
    assert p.practica_de("atracar"), (pr, robot.dicho())
    # llegar a tierra de cualquier manera no vale: hay que atracar en un muelle
    mu = p.lugares["mar_playa"]
    j.veh.x, j.veh.y, j.veh.vel = mu.x, mu.y + 12, 0.0
    robot.frames(10)
    robot.tecla(pygame.K_RETURN)
    assert isinstance(robot.app.pila[-1], Menu), robot.dicho()
    _elegir(robot, "Atracar y desembarcar")
    assert p.mundo.id != "mar" and j.veh is None
    robot.frames(3)
    robot.saltar_dialogos()
    robot.frames(3)
    assert "tut04" in p.completadas and p.mision is None and j.dinero == dinero + 50


def test_naufragar_no_cuenta_como_atracar(robot, datos_de_serie):
    p = _empezar(robot)
    m = _tutorial(robot, "tut04")
    p.mision["paso"] = next(k for k, x in enumerate(m["pasos"]) if x.get("que") == "atracar") - 1
    p._siguiente_paso()
    assert p.practica_de("atracar")
    robot.frames(60)
    assert p.practica_de("atracar") and "tut04" not in p.completadas      # está en tierra, pero no ha atracado
    p.mision["practica"]["t"] = 100.0
    robot.frames(2)
    assert "hay que atracar" in robot.dicho()


def test_el_tutorial_de_trabajos_exige_hacer_un_servicio(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    m = _tutorial(robot, "tut03")
    taxi = p.mision["veh"]
    assert taxi is not None and m["pasos"][p.mision["paso"]]["tipo"] == "robar"
    _a(p, type("L", (), {"x": taxi.x, "y": taxi.y, "mapa": p.mundo.id})(), 2.0)
    p._subir(taxi, False, callar=True)
    robot.frames(3)
    assert p.practica_de("trabajar") and "pulsa la J" in robot.dicho()
    # llevar el taxi a la parada, como antes, ya no completa nada
    parada = p.lugares["parada_taxi"]
    taxi.x, taxi.y, taxi.vel = *p.mundo.punto_libre(parada.x + 4, parada.y), 0.0
    robot.frames(30)
    assert p.practica_de("trabajar") and "tut03" not in p.completadas
    # con la J empiezas a trabajar, aunque estés en una misión: es lo que enseña el tutorial
    robot.tecla(pygame.K_j)
    robot.frames(3)
    t = p.trabajo
    assert t and t["tipo"] == "taxi" and p.practica_de("servicio")
    assert p.gps is not None and p.gps["nombre"] == t["lugar"].nombre       # el GPS del trabajo sigue puesto: no lo quita el tutorial
    # y hay que hacer el servicio entero: recoger y llevar
    l = t["lugar"]
    taxi.x, taxi.y, taxi.vel = *p.mundo.punto_libre(l.x + 4, l.y), 0.0
    robot.frames(5)
    assert t["fase"] == "llevar" and p.practica_de("servicio")
    l = t["lugar"]
    taxi.x, taxi.y, taxi.vel = *p.mundo.punto_libre(l.x + 4, l.y), 0.0
    robot.frames(5)
    assert j.stats["servicios"] == 1
    robot.saltar_dialogos()
    robot.frames(3)
    assert "tut03" in p.completadas and p.mision is None
    assert p.trabajo is not None and j.veh is taxi and taxi.tag is None      # el taxi deja de ser de la misión y sigues trabajando con él
    assert p.gps is not None                                       # con el GPS del servicio siguiente


def test_el_ejercicio_del_radar_exige_usar_el_radar(robot, datos_de_serie):
    """El primer tutorial: el ejercicio del radar no se completa llegando a la tienda de cualquier manera."""
    p = _empezar(robot)
    m = _tutorial(robot, "tut01")
    assert m["pasos"][3].get("exige") == "radar" and not m["pasos"][1].get("exige")
    _a(p, p.lugares["farmacia"], 2.0)                              # el primer ejercicio sí es llegar
    robot.frames(3)
    robot.saltar_dialogos()
    robot.frames(3)
    assert p.mision["paso"] == 3
    _a(p, p.lugares["tienda_paco"], 2.0)                           # llegas sin haber tocado el radar
    robot.frames(10)
    assert p.mision["paso"] == 3 and "este ejercicio es para aprender el radar" in robot.dicho()
    n = sum("aprender el radar" in t for t in robot.app.voz.registro)
    robot.frames(60)
    assert sum("aprender el radar" in t for t in robot.app.voz.registro) == n      # lo dice una vez, no a cada momento
    robot.tecla(pygame.K_TAB)                                      # usas el radar: hecho
    robot.frames(3)
    assert p.mision["paso"] == 4
    p.abandonar_mision()
    robot.saltar_dialogos()
    _cerrar_menus(robot)


def test_jugar_con_amigos_es_una_explicacion_y_no_una_mision(robot, datos_de_serie):
    from juego import menus_online
    p = _empezar(robot)
    j = p.j
    p.completadas.append("tut01")
    tut = next(x for x in p.datos["misiones"] if x["id"] == "tut05")
    assert tut["explicacion"] and [x["tipo"] for x in tut["pasos"]] == ["dialogo"]
    assert p.mision_en_lugar(tut["lugar"]) is None or p.mision_en_lugar(tut["lugar"])["id"] != "tut05"
    assert "Bar La Gaviota" not in json.dumps(tut, ensure_ascii=False)        # ya no manda a ningún bar
    dinero, sitio = j.dinero, (j.x, j.y)
    menus_online.amigos(p)
    o = _opcion(robot.app.pila[-1], "Cómo se juega con amigos")
    assert o.ayuda and "no es una misión" in o.ayuda
    _elegir(robot, "Cómo se juega con amigos")
    d = robot.app.pila[-1]
    assert isinstance(d, Dialogo) and len(d.lineas) == 9 and p.mision is None
    robot.saltar_dialogos()
    assert "tut05" in p.completadas and j.dinero == dinero + 50 and (j.x, j.y) == sitio
    p.explicacion("tut05")                                         # se puede volver a leer, pero no paga dos veces
    robot.saltar_dialogos()
    assert j.dinero == dinero + 50 and p.completadas.count("tut05") == 1
    # y los demás tutoriales siguen haciendo lo que enseñan: ninguno se completa con solo llegar a un sitio sin más
    for ident in ("tut01", "tut02", "tut03", "tut04"):
        t = next(x for x in p.datos["misiones"] if x["id"] == ident)
        hacer = [x for x in t["pasos"] if x["tipo"] not in ("dialogo", "dar")]
        assert hacer and (ident == "tut01" or not any(x["tipo"] == "ir" for x in hacer)), ident


def test_las_voces_de_los_tutoriales_siguen_cuadrando_con_sus_frases(datos_de_serie):
    """Los tutoriales tocados conservan sus grabaciones solo donde la frase sigue siendo la misma, y no queda ninguna
    grabación de un tutorial apuntando a un paso que ya no es un diálogo o a una frase que no existe."""
    d = M.cargar_datos(con_mods=False)
    por_id = {m["id"]: m for m in d["misiones"]}
    carpeta = os.path.join(rutas.DATA, "voces", "historia_principal_es")
    if not os.path.isdir(carpeta):
        pytest.skip("sin voces grabadas")
    for f in os.listdir(carpeta):
        base = os.path.splitext(f)[0].split("@")[0]
        if not base.startswith(("tut03_", "tut04_", "tut05_")):
            continue
        ident, paso, frase = base.split("_")
        pasos = por_id[ident]["pasos"]
        assert int(paso) <= len(pasos) and pasos[int(paso) - 1]["tipo"] == "dialogo", f
        assert int(frase) <= len(pasos[int(paso) - 1]["lineas"]), f


# ====================================================================== 7. la gente actúa
def _vecino(p, caracter="hablador", confianza=60, edad=30, **attrs):
    q = _persona(p, "civil", 2.5, estado="quieto", **attrs)
    f = ficha(q)
    f.update(caracter=caracter, confianza=confianza, edad=edad, presentado=True)
    q.nombre = f["nombre"]
    return q, f


def test_alguien_a_quien_le_caes_bien_te_acompana_un_rato(robot, datos_de_serie):
    from juego import menus_charla
    p = _empezar(robot)
    RE.AJ.n.update(seguir_prob=1000, seguir_min=6, seguir_max=6)
    q, f = _vecino(p)
    menus_charla.conversar(p, q)
    m = robot.app.pila[-1]
    _elegir(robot, "Hacer un cumplido")
    assert robot.app.pila[-1] is p and q.estado == "sigue"           # echa a andar contigo: la conversación se acaba
    assert any(fr.replace("{nombre}", f["nombre"]) in robot.dicho() for fr in RE.AJ.lista("frases_sigue"))
    # camina a tu lado
    p.j.x, p.j.y = p.mundo.punto_libre(p.j.x + 14, p.j.y)
    d0 = q.dist(p.j.x, p.j.y)
    robot.frames(60)
    assert q.dist(p.j.x, p.j.y) < d0 - 3 and q.estado == "sigue"
    # y al rato se despide
    assert _hasta(robot, lambda: q.estado != "sigue", 12)
    assert any(fr.replace("{nombre}", f["nombre"]) in _todo(robot) for fr in RE.AJ.lista("frases_sigue_fin"))
    assert p.j.stats["acompanantes"] == 1 and f["ha_seguido"]
    assert p.reaccion_tras(q, "cumplido", 0) == ""                 # una vez por persona
    # con la opción apagada, la gente solo habla
    q2, f2 = _vecino(p)
    p.cfg["gente_actua"] = False
    assert p.reaccion_tras(q2, "cumplido", 0) == "" and q2.estado == "quieto"
    p.cfg["gente_actua"] = True
    # si te busca la policía, no va contigo
    assert p.reaccion_tras(q2, "cumplido", 0) != "" and q2.estado == "sigue"
    p.j.estrellas = 1
    robot.frames(3)
    assert q2.estado != "sigue"
    p.j.estrellas = 0


def test_insistir_a_quien_has_ofendido_puede_acabar_en_un_golpe_y_un_insulto_en_denuncia(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    RE.AJ.n.update(pegar_prob=1000, denuncia_prob=1000)
    # con carácter: te pega y se queda a pelear
    q, f = _vecino(p, "chulo", confianza=0)
    f["ofendido"] = True
    salud = j.salud
    robot.tecla(pygame.K_j)
    assert j.salud < salud and q.hostil and q.tipo == "enemigo" and q.agresor
    assert any(fr.replace("{nombre}", f["nombre"]) in robot.dicho() for fr in RE.AJ.lista("frases_pega"))
    assert any(fr.replace("{nombre}", f["nombre"]) in robot.dicho() for fr in RE.AJ.lista("frases_pelea"))
    p.personas.remove(q)
    # sin tanto carácter: te da uno y se va
    q, f = _vecino(p, "amable", confianza=0)
    f["ofendido"] = True
    salud = j.salud
    robot.tecla(pygame.K_j)
    assert j.salud < salud and not q.hostil and q.estado == "huye" and "Y se marcha" in robot.dicho()
    assert p.insistir(q) == ""                                     # una vez por persona
    p.personas.remove(q)
    # sin la opción, se limita a no hacerte caso
    q, f = _vecino(p, "chulo", confianza=0)
    f["ofendido"] = True
    p.cfg["gente_actua"] = False
    salud = j.salud
    robot.tecla(pygame.K_j)
    assert j.salud == salud and not q.hostil and "no quiere saber nada de ti" in robot.dicho()
    p.cfg["gente_actua"] = True
    p.personas.remove(q)
    # insultar a alguien que se marcha: te denuncia
    q, f = _vecino(p, "timido", confianza=0)
    q.estado, q.t_estado = "huye", 8
    assert j.puntos_busqueda == 0
    frase = p.reaccion_tras(q, "insultar", 0)
    assert any(fr.replace("{nombre}", f["nombre"]) == frase for fr in RE.AJ.lista("frases_denuncia")) and j.puntos_busqueda > 0 and j.stats["denuncias"] == 1


def test_pedir_un_favor(robot, datos_de_serie):
    from juego import menus_charla
    p = _empezar(robot)
    j = p.j
    q, f = _vecino(p, confianza=10)
    menus_charla.conversar(p, q)
    o = _opcion(robot.app.pila[-1], "Pedirle un favor")
    assert o.ayuda and "confianza" in o.ayuda
    _elegir(robot, "Pedirle un favor")
    assert any(fr.replace("{nombre}", f["nombre"]) in robot.dicho() for fr in RE.AJ.lista("frases_favor_no")) and f["confianza"] == 8
    _cerrar_menus(robot)
    # con confianza: si vienes tocado, te apaña
    f["confianza"] = 80
    j.salud = 30.0
    assert "Salud 55" in p.pedir_favor(q) and j.salud == 55.0
    assert any(fr.replace("{nombre}", f["nombre"]) == p.pedir_favor(q) for fr in RE.AJ.lista("frases_favor_hoy"))      # uno al día
    # si te busca la policía con poco nivel, te esconde
    p.dia += 1
    j.salud = j.salud_max
    j.puntos_busqueda, j.estrellas = 1.5, 1
    texto = p.pedir_favor(q)
    assert "ha dejado de buscarte" in texto and j.estrellas == 0 and j.puntos_busqueda == 0
    # si no te hace falta nada, te da una pista o habla bien de ti
    p.dia += 1
    for o_ in [o_ for o_ in p.objetos if o_.tipo == "casete"]:
        p.objetos.remove(o_)
    c = j.ciudadania
    texto = p.pedir_favor(q)
    assert any(fr.replace("{nombre}", f["nombre"]) == texto for fr in RE.AJ.lista("frases_favor_barrio")) and j.ciudadania == c + 2
    assert j.stats["favores"] == 3


def test_reclutar_a_alguien_de_la_calle(robot, datos_de_serie):
    from juego import menus_charla, sistemas
    p = _empezar(robot)
    j = p.j
    j.dinero = 5000
    q, f = _vecino(p, "chulo", confianza=70)
    prima = p.prima_recluta()
    assert prima == int(p.precio("recluta", sistemas.PRECIO_RECLUTA) * 0.6)
    # sin territorio no hay banda
    ok, frase = p.reclutar_persona(q)
    assert not ok and "necesitas un territorio" in frase and j.banda == 0
    j.territorios = ["centro"]
    # sin fama, no se fía
    j.reputacion = 0.0
    ok, frase = p.reclutar_persona(q)
    assert not ok and any(fr.replace("{nombre}", f["nombre"]) in frase for fr in RE.AJ.lista("frases_recluta_no_fama"))
    j.reputacion = 30.0
    # los muy tímidos, la gente mayor y quien no te conoce dicen que no
    for cambios, lista in (({"caracter": "timido"}, "frases_recluta_no_caracter"), ({"edad": 70}, "frases_recluta_no_edad"), ({"confianza": 10}, "frases_recluta_no_confianza")):
        q2, f2 = _vecino(p, "chulo", confianza=70)
        f2.update(cambios)
        ok, frase = p.reclutar_persona(q2)
        assert not ok and j.banda == 0 and q2.tipo == "civil", cambios
        assert any(ajustes.quien_es(fr).replace("{nombre}", f2["nombre"]) in ajustes.quien_es(frase) for fr in RE.AJ.lista(lista)), (cambios, frase)
        p.personas.remove(q2)
    # sin dinero para la prima, tampoco
    j.dinero = prima - 1
    ok, frase = p.reclutar_persona(q)
    assert not ok and "prima" in frase and j.banda == 0
    # y con todo en regla, desde la conversación
    j.dinero = 5000
    menus_charla.conversar(p, q)
    o = _opcion(robot.app.pila[-1], "Proponerle que se una a tu banda")
    assert f"prima de {prima} euros" in _texto(o) and "territorio" in o.ayuda
    _elegir(robot, "Proponerle que se una a tu banda")
    assert robot.app.pila[-1] is p and j.banda == 1 and j.dinero == 5000 - prima and j.banda_nombre
    assert q.tipo == "aliado" and q.de_banda and q.nombre == f"{f['nombre']}, de {j.banda_nombre}" and q in sistemas.miembros_presentes(p)
    assert j.stats["reclutados_calle"] == 1
    # con la banda llena, no cabe nadie más
    q3, f3 = _vecino(p, "chulo", confianza=70)
    j.banda = sistemas.cupo(j)
    ok, frase = p.reclutar_persona(q3)
    assert not ok and "no puedes mantener a más" in frase


def test_la_ia_solo_propone_y_el_juego_decide(robot, datos_de_serie, monkeypatch):
    from juego import ia
    p = _empezar(robot)
    j = p.j
    assert config.POR_DEFECTO["ia_acciones"] is False and config.POR_DEFECTO["gente_actua"] is True
    # la lista de acciones es cerrada: lo que no esté en ella es «nada»
    assert ia._leer('{"respuesta": "Vale", "confianza": 3, "accion": "se_une"}')["accion"] == "nada"            # sin la opción, solo irse o enfadarse
    assert ia._leer('{"respuesta": "Vale", "confianza": 3, "accion": "se_une"}', True, ia.ACCIONES_AMPLIADAS)["accion"] == "se_une"
    for invento in ("dar_dinero", "te_da_500_euros", "regalar_arma", "obedece"):
        assert ia._leer('{"respuesta": "Toma", "confianza": 15, "accion": "%s"}' % invento, True, ia.ACCIONES_AMPLIADAS)["accion"] == "nada"
    assert set(ia.ACCIONES_AMPLIADAS) == set(RE.ACCIONES_IA) and "Nunca des" in ia.FORMATO_JSON_ACCIONES and "el juego decide" in ia.FORMATO_JSON_ACCIONES
    # sin la opción, aunque el modelo proponga seguirte o unirse, no pasa nada
    q, f = _vecino(p, "chulo", confianza=80)
    j.territorios, j.reputacion, j.dinero = ["centro"], 50.0, 5000
    for accion in ("te_sigue", "se_une"):
        assert p.decidir_accion_ia(q, accion) == "" and q.estado == "quieto" and q.tipo == "civil" and j.banda == 0
    # con la opción, el juego aplica sus reglas de siempre
    p.cfg["ia_activa"], p.cfg["ia_acciones"] = True, True
    dinero = j.dinero
    assert p.decidir_accion_ia(q, "dame_todo_tu_dinero") == "" and j.dinero == dinero       # no existe: no hace nada
    q_poco, f_poco = _vecino(p, "chulo", confianza=5)
    assert p.decidir_accion_ia(q_poco, "te_sigue") == "" and q_poco.estado == "quieto"       # no le caes bien: no te sigue, diga lo que diga el modelo
    assert p.decidir_accion_ia(q_poco, "se_une") == "" and j.banda == 0 and q_poco.tipo == "civil"
    frase = p.decidir_accion_ia(q, "te_sigue")
    assert frase and q.estado == "sigue"
    q2, f2 = _vecino(p, "chulo", confianza=80)
    frase = p.decidir_accion_ia(q2, "se_une")
    assert j.banda == 1 and q2.tipo == "aliado" and j.dinero == dinero - p.prima_recluta()   # y se cobra la prima: nada es gratis por pedirlo
    j.territorios = []
    q3, f3 = _vecino(p, "chulo", confianza=80)
    assert p.decidir_accion_ia(q3, "se_une") == "" and q3.tipo == "civil"                    # sin territorio no hay banda, proponga lo que proponga
    assert p.decidir_accion_ia(q3, "se_va") == "" and q3.estado == "huye"
    # de punta a punta: la respuesta del modelo llega con su acción, y la frase cuenta lo que ha pasado
    q4, f4 = _vecino(p, "hablador", confianza=80)
    monkeypatch.setattr(type(p), "ia_disponible", lambda self: True)
    monkeypatch.setattr(ia, "responder", lambda p_, q_, texto: {"respuesta": "Pues te acompaño.", "confianza": 4, "accion": "te_sigue"})
    texto = p.responder_libre(q4, "ven conmigo y dame mil euros")
    assert texto.startswith(f"{f4['nombre']}: Pues te acompaño.") and q4.estado == "sigue" and j.dinero == dinero - p.prima_recluta()
    # la opción está en el menú de la IA, con su explicación
    from juego import menus_charla
    menus_charla.opciones_ia(robot.app)
    o = _opcion(robot.app.pila[-1], "La IA puede proponer acciones")
    assert "sí" in _texto(o) and "lista cerrada" in o.ayuda and "dinero ni objetos" in o.ayuda


# ====================================================================== 8. vivir en pareja y planes
def _pareja(p, pid="lucia", afinidad=95, citas=5):
    j = p.j
    pers = p.persona_social(pid)
    r = p.relacion(pid)
    r.update(estado="pareja", afinidad=afinidad, citas=citas, ultimo=p.dia)
    j.pareja = pid
    return pers, r


def test_pedirle_a_tu_pareja_que_se_venga_a_vivir_contigo(robot, datos_de_serie):
    from juego import menus_adultos, menus_juego
    p = _empezar(robot, adultos=True)
    j = p.j
    casa = p.lugares["casa_abuela"]
    pers, r = _pareja(p)
    n = pers["nombre"]
    assert config.POR_DEFECTO["pareja_convive"] is False
    # con la opción apagada, ni aparece
    assert not p.convivencia_activa() and "desactivado" in p.pedir_convivir(pers, casa)[1]
    _a(p, p.lugares[pers["lugar"]])
    menus_adultos.vida_social(p, directo=pers["id"])
    textos = [_texto(o) for o in robot.app.pila[-1].opciones]
    assert not any("vivir contigo" in t for t in textos) and "Hacer un plan juntos" in textos      # los planes sí están
    _cerrar_menus(robot)
    p.cfg["pareja_convive"] = True
    # cada persona decide: hay quien no deja su casa por nadie
    ok, frase = p.pedir_convivir(dict(pers, convivir="nunca"), casa)
    assert not ok and frase in [f.replace("{n}", n) for f in CV.AJ.lista("frases_no_nunca")] and j.convive == ""
    assert "ya te contestó hace poco" in p.pedir_convivir(dict(pers, convivir="si"), casa)[1]       # y no se insiste al día siguiente
    p.dia += int(CV.AJ("espera_dias"))
    r["afinidad"] = 40                                             # si la relación no está para eso, todavía no
    ok, frase = p.pedir_convivir(dict(pers, convivir="si"), casa)
    assert not ok and frase in [f.replace("{n}", n) for f in CV.AJ.lista("frases_no_pronto")]
    p.dia += int(CV.AJ("espera_dias"))
    r["afinidad"], r["citas"] = 95, 0                              # ni sin haber salido juntos
    assert not p.pedir_convivir(dict(pers, convivir="si"), casa)[0]
    p.dia += int(CV.AJ("espera_dias"))
    r["citas"] = 5
    # la disposición de cada cual es fija en la partida
    assert p._disposicion(pers) == p._disposicion(pers) and p._disposicion(dict(pers, convivir="nunca")) is None
    assert p._disposicion(dict(pers, convivir="facil")) == CV.AJ("afinidad_minima") - 8
    # desde su ficha, con todo a favor
    pers_si = dict(pers, convivir="si")
    ok, frase = p.pedir_convivir(pers_si, casa)
    assert ok and j.convive == pers["id"] and j.convive_casa == casa.id and casa.nombre in frase
    assert "ya vive contigo" in p.pedir_convivir(pers_si, casa)[1]
    menus_adultos.vida_social(p, directo=pers["id"])
    assert any(_texto(o).startswith("Vive contigo, en ") for o in robot.app.pila[-1].opciones)
    _cerrar_menus(robot)
    # te la encuentras en casa, de noche siempre
    p.reloj = 22 * 60.0
    assert p.pareja_en_casa()
    _a(p, casa, 2.0)
    menus_juego.lugar(p, casa)
    m = robot.app.pila[-1]
    assert any(f.replace("{n}", n) in robot.dicho() for f in CV.AJ.lista("frases_recibe")) and j.convive_hoy["visto"] == p.dia
    o = _opcion(m, f"{n} está en casa")
    assert o.ayuda
    _elegir(robot, f"{n} está en casa")
    en_casa = robot.app.pila[-1]
    assert [_texto(x).split(":")[0] for x in en_casa.opciones][:3] == ["Hablar un rato", "Comer juntos", "Hacer un plan juntos"]
    afinidad = r["afinidad"] = 80
    _elegir(robot, "Hablar un rato")
    assert r["afinidad"] == afinidad + 2
    _elegir(robot, "Hablar un rato")
    assert r["afinidad"] == afinidad + 2 and "Ya habéis hablado" in robot.dicho()      # una vez al día
    j.salud = 40.0
    _elegir(robot, "Comer juntos")
    assert j.salud == 70.0 and (any(f.replace("{n}", n) in robot.dicho() for f in CV.AJ.lista("frases_cocina") + CV.AJ.lista("frases_cocinas_tu")))
    _elegir(robot, "Comer juntos")
    assert j.salud == 70.0
    # y se le puede pedir que se vaya
    _elegir(robot, "Pedirle que se vaya de casa")
    _elegir(robot, "Sí, pedirle que se vaya")
    assert j.convive == "" and j.pareja == pers["id"] and r["afinidad"] < afinidad
    assert any(f.replace("{n}", n) in robot.dicho() for f in CV.AJ.lista("frases_se_va"))
    _cerrar_menus(robot)
    menus_juego.lugar(p, casa)
    assert not any("está en casa" in _texto(x) for x in robot.app.pila[-1].opciones)
    _cerrar_menus(robot)


def test_quien_vive_contigo_te_pide_cosas_y_nota_si_no_apareces(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot, adultos=True, pareja_convive=True)
    j = p.j
    casa = p.lugares["casa_abuela"]
    pers, r = _pareja(p, afinidad=80)
    n = pers["nombre"]
    j.convive, j.convive_casa, j.convive_desde = pers["id"], casa.id, p.dia
    j.dinero = 500
    p.reloj = 22 * 60.0
    # te pide algo al verte (se fuerza el azar): cada cosa, con su frase
    CV.AJ.n["peticion_prob"] = 100
    _a(p, casa, 2.0)
    saludo = p.saludo_de_casa(casa)
    pet = j.peticion_pareja
    assert pet and pet["que"] in ("cena", "plan", "dormir", "regalo", "mueble") and pet["hasta"] == p.dia + CV.AJ("peticion_dias")
    assert any(f.replace("{n}", n) in saludo for f in CV.AJ.lista("frases_peticion_" + pet["que"])) and n in p.peticion_txt()
    assert p.saludo_de_casa(casa) and j.peticion_pareja is pet       # no te pide dos cosas a la vez
    # una cena a domicilio, en casa: cumplido
    j.peticion_pareja = {"que": "cena", "dia": p.dia, "hasta": p.dia + 2, "muebles": 0}
    afinidad = r["afinidad"]
    assert p.pedir_domicilio([DO.carta(p)[1]])
    j.pedido["llega"] = p._ahora() - 1
    robot.frames(3)
    assert j.peticion_pareja is None and r["afinidad"] == afinidad + CV.AJ("peticion_premio")
    assert any(f.replace("{n}", n) in _todo(robot) for f in CV.AJ.lista("frases_peticion_ok"))
    # dormir en casa
    j.peticion_pareja = {"que": "dormir", "dia": p.dia, "hasta": p.dia + 2, "muebles": 0}
    afinidad = r["afinidad"]
    menus_juego.lugar(p, casa)
    _elegir(robot, "Descansar ocho horas")
    assert j.peticion_pareja is None and r["afinidad"] == afinidad + CV.AJ("peticion_premio")
    _cerrar_menus(robot)
    # lo que dejas pasar, lo apunta
    j.peticion_pareja = {"que": "regalo", "dia": p.dia, "hasta": p.dia, "muebles": 0}
    j.convive_hoy["visto"] = p.dia
    afinidad = r["afinidad"]
    p.dia += 1
    p.dia_convivencia()
    assert j.peticion_pareja is None and r["afinidad"] == afinidad - CV.AJ("peticion_castigo")
    assert any(f.replace("{n}", n) in _todo(robot) for f in CV.AJ.lista("frases_peticion_mal"))
    # y si pasan los días sin que aparezcas por casa, se resiente
    afinidad = r["afinidad"]
    j.convive_hoy["visto"] = p.dia - 3
    p.dia_convivencia()
    assert r["afinidad"] == afinidad - 2
    # traer a otra persona a esa casa, con tu pareja dentro, es el final
    assert p.aventura_en_casa(casa) and j.convive == "" and j.pareja == "" and r["estado"] == "ex"
    assert any(f.replace("{n}", n) in _todo(robot) for f in CV.AJ.lista("frases_celos_casa"))
    # romper también la saca de casa; y si la casa deja de ser tuya, se muda a otra o se va
    pers, r = _pareja(p, afinidad=90)
    j.convive, j.convive_casa = pers["id"], casa.id
    j.pareja = ""
    p.dia_convivencia()
    assert j.convive == ""


def test_planes_en_pareja_con_escenas_que_cambian(robot, datos_de_serie):
    from juego import menus_adultos
    p = _empezar(robot, adultos=True)
    j = p.j
    j.dinero = 2000
    pers, r = _pareja(p, afinidad=60)
    n = pers["nombre"]
    _a(p, p.lugares[pers["lugar"]])
    planes = p.planes_para(pers)
    ids = [pl["id"] for pl, _ in planes]
    assert {"paseo_barrio", "cine_juntos", "cena_fuera", "barco", "playa"} <= set(ids) and "noche_casa" not in ids      # el de casa, solo viviendo juntos y en casa
    assert all(len(pl["escenas"]) >= 4 for pl, _ in planes)
    menus_adultos.vida_social(p, directo=pers["id"])
    _elegir(robot, "Hacer un plan juntos")
    m = robot.app.pila[-1]
    assert "Planes con " + n in m.titulo and any(_texto(o).startswith("Una travesía en barco") for o in m.opciones)
    dinero, hora = j.dinero, p.reloj
    _elegir(robot, "Una travesía en barco")
    d = robot.app.pila[-1]
    assert isinstance(d, Dialogo) and len(d.lineas) == 4 and n in d.lineas[0][1] and j.dinero == dinero - 90
    barco = next(pl for pl, _ in planes if pl["id"] == "barco")
    primeras = [t for _, t in d.lineas[1:3]]
    assert all(t in [e.replace("{n}", n) for e in barco["escenas"]] for t in primeras) and "{n}" not in " ".join(primeras)
    robot.saltar_dialogos()
    assert r["afinidad"] == 60 + 12 and r["citas"] == 6 and j.stats["planes_pareja"] == 1 and p.reloj != hora
    # uno al día
    assert not p.hacer_plan(pers, barco) and "Hoy ya habéis hecho un plan" in robot.dicho()
    # al día siguiente, las otras dos escenas: no se repite ninguna hasta haberlas oído todas
    p.dia += 1
    assert p.hacer_plan(pers, barco)
    segundas = [t for _, t in robot.app.pila[-1].lineas[1:3]]
    assert not set(primeras) & set(segundas)
    robot.saltar_dialogos()
    # un plan que pide un sitio que aquí no hay, se dice
    p.cambiar_mapa("isla_tortuga", *p.mapas["isla_tortuga"].punto_libre(100, 100))
    assert any(motivo for pl, motivo in p.planes_para(pers) if pl.get("requiere") == "cine")
    # las escenas valen para cualquier pareja: no dan por hecho que es hombre o mujer
    for pl in CV.PLANES:
        for e in pl["escenas"]:
            assert not any(w in e.lower().split() for w in ("dormida", "dormido", "ella", "él", "guapa", "guapo", "novia", "novio")), e


# ====================================================================== 9. el oficio de policía
def _agente(robot, **opciones):
    p = _empezar(robot, oficio_policia=True, invulnerable=True, **opciones)
    j = p.j
    j.dinero, j.ciudadania = 2000, 50.0
    AG.AJ.n.update(espera_min=1, espera_max=1)
    return p


def _solo_avisos(p, tipo):
    p.datos["avisos_policia"] = [a for a in AG.AVISOS if a["tipo"] == tipo]


def _aviso(robot, p):
    """Espera al aviso siguiente de la emisora."""
    p.trabajo["espera"] = 0.0
    assert _hasta(robot, lambda: p.trabajo and p.trabajo.get("aviso") is not None, 5), robot.dicho()
    return p.trabajo["aviso"]


def test_ingresar_en_la_policia_y_empezar_el_turno(robot, datos_de_serie):
    from juego import menus_juego
    p = _empezar(robot)
    j = p.j
    com = p.lugares["comisaria"]
    assert config.POR_DEFECTO["oficio_policia"] is False
    # con el modo apagado, la comisaría es la de siempre
    _a(p, com)
    menus_juego.lugar(p, com)
    assert not any("policía:" in _texto(o).lower() or "turno" in _texto(o).lower() for o in robot.app.pila[-1].opciones)
    _cerrar_menus(robot)
    assert not p.policia_activa() and not p.es_agente() and "desactivado" in p.ingreso_motivo()
    p.cfg["oficio_policia"] = True
    j.dinero = 1000
    # hace falta que los vecinos te aprecien, y que no te busquen
    j.ciudadania = 5.0
    assert "vecinos" in p.ingreso_motivo() and not p.ingresar_policia()
    j.ciudadania = 50.0
    j.estrellas = 1
    assert "buscándote" in p.ingreso_motivo()
    j.estrellas = 0
    menus_juego.lugar(p, com)
    o = _opcion(robot.app.pila[-1], "Ingresar en la policía")
    assert "400 euros" in _texto(o) and "placa" in o.ayuda
    hora = p._ahora()
    _elegir(robot, "Ingresar en la policía")
    assert p.es_agente() and j.dinero == 600 and p._ahora() - hora == AG.AJ("curso_horas") * 60 and j.policia["alta"]
    assert p.rango_policia_txt() == "agente en prácticas"
    m = robot.app.pila[-1]
    assert _opcion(m, "Eres agente en prácticas") and _opcion(m, "Empezar el turno").ayuda
    son = _oir(p)
    _elegir(robot, "Empezar el turno")
    assert robot.app.pila[-1] is p and p.de_servicio() and "emisora" in son
    t = p.trabajo
    patrulla = t["patrulla"]
    assert patrulla is not None and patrulla.modelo["id"] == "patrulla" and patrulla.dist(*p.pos()) < 60 and patrulla.tag == "servicio"
    assert "coche patrulla" in robot.dicho() and p.objetivo_txt().startswith("Estás de servicio")
    # subes sin que sea un robo, y la J termina el turno y devuelve el coche
    p._subir(patrulla, False, callar=True)
    assert j.puntos_busqueda == 0
    robot.tecla(pygame.K_j)
    assert not p.de_servicio() and j.veh is None and patrulla not in p.vehiculos
    # en cualquier coche patrulla, con placa, la J empieza el turno (y no el trabajo de vigilante)
    otra = p.crear_vehiculo("patrulla", *p.mundo.punto_libre(j.x + 6, j.y), 0, "aparcado")
    p._subir(otra, False, callar=True)
    robot.tecla(pygame.K_j)
    assert p.de_servicio() and p.trabajo["patrulla"] is otra and not p.trabajo["prestada"]
    p.terminar_turno()
    assert otra in p.vehiculos                                      # ese no era prestado: se queda
    # sin placa, ese mismo coche sigue sirviendo para el trabajo de vigilante de siempre
    p.dejar_policia()
    assert not p.es_agente()
    robot.tecla(pygame.K_j)
    assert p.trabajo and p.trabajo["tipo"] == "vigilante"
    p.terminar_trabajo(None)


def test_un_aviso_de_robo_dar_el_alto_reducir_y_detener(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    _solo_avisos(p, "robo")
    son = _oir(p)
    a = _aviso(robot, p)
    assert a["tipo"] == "robo" and a["fase"] == "ir" and "emisora" in son and p.gps is not None
    assert G.caja_local(a["lugar"].tipo) is not None and a["lugar"].nombre in robot.dicho() and "segundos para llegar" in robot.dicho()
    _a(p, a["lugar"], 6.0)
    robot.frames(3)
    assert a["fase"] == "actuar" and 1 <= len(a["sospechosos"]) <= 2
    for s in a["sospechosos"]:                                     # para la prueba: todos plantan cara (alguno puede haberse entregado ya al verte)
        s.plan, s.hostil, s.estado, s.ha_resistido, s.rendido = "pelea", True, "ataca", True, False
    s = a["sospechosos"][0]
    # usar la fuerza contra el sospechoso de un aviso no es delito
    _armar(p)
    p._ruido_disparo(*p.pos())
    assert j.puntos_busqueda == 0 and j.policia.get("apercibimientos", 0) == 0
    # dar el alto con la H: aquí obedece
    AG.AJ.n["alto_prob"] = 100
    j.x, j.y = p.mundo.punto_libre(s.x + 3, s.y)
    robot.tecla(pygame.K_h)
    assert all(x.rendido and not x.hostil for x in a["sospechosos"] if x.dist(j.x, j.y) < 18)
    assert any(f in _todo(robot) for f in AG.AJ.lista("frases_alto"))
    for x in list(a["sospechosos"]):                               # y a quien no, se le reduce: se rinde en vez de caer
        if not getattr(x, "rendido", False):
            p.danar_persona(x, x.salud * 0.8)
            assert x.rendido and not x.muerto
    # Intro junto a cada uno: esposas
    dinero = j.dinero
    for x in list(a["sospechosos"]):
        j.x, j.y = x.x, x.y
        robot.tecla(pygame.K_RETURN)
        assert robot.app.pila[-1] is p
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.policia["detenciones"] >= 1 and j.stats["serv_policia"] == 1
    assert j.dinero > dinero and "Aviso resuelto" in _todo(robot) and j.puntos_busqueda == 0 and p.trabajo["hechas"] == 1
    # otro aviso: si no llegas a tiempo, otra unidad se hace cargo y no cobras
    a = _aviso(robot, p)
    dinero = j.dinero
    a["limite"] = 0.01
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.dinero == dinero and any(f in _todo(robot) for f in AG.AJ.lista("frases_tarde"))
    # y si llegas, empiezas y te marchas, también se da por perdido: la emisora no se queda esperándote para siempre
    a = _aviso(robot, p)
    _a(p, a["lugar"], 6.0)
    robot.frames(3)
    assert a["fase"] == "actuar"
    for s in a["sospechosos"]:
        s.rendido, s.hostil, s.estado = True, False, "quieto"       # se han rendido, pero te vas sin detenerlos
    sospechosos = list(a["sospechosos"])
    j.x, j.y = p.mundo.punto_libre(j.x + (-260 if j.x > p.mundo.ancho / 2 else 260), j.y)      # lejos, hacia el centro del mapa
    assert min(s.dist(j.x, j.y) for s in sospechosos) > AG.AJ("abandono_metros")
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.dinero == dinero and any(f in _todo(robot) for f in AG.AJ.lista("frases_abandono"))
    assert not any(s in p.personas for s in sospechosos)


def test_abatir_a_quien_se_ha_rendido_es_un_exceso(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    _solo_avisos(p, "robo")
    AG.AVISOS[0]["n_max"], guardado = 1, AG.AVISOS[0]["n_max"]
    try:
        a = _aviso(robot, p)
        _a(p, a["lugar"], 6.0)
        robot.frames(3)
        s = a["sospechosos"][0]
        s.plan = "entrega"
        j.x, j.y = p.mundo.punto_libre(s.x + 3, s.y)
        robot.frames(3)
        assert s.rendido                                           # al verte, tira lo que lleva
        dinero = j.dinero
        p.danar_persona(s, 9999)
        robot.frames(3)
        assert p.trabajo and p.trabajo["aviso"] is None and j.policia["apercibimientos"] == 1 and j.policia["bajas"] == 1
        assert any(f in _todo(robot) for f in AG.AJ.lista("frases_excesivo"))
        assert j.dinero <= dinero + int(160 * 0.5 * 1.1) + int(AG.AJ("bono_rapidez") * 1.1)      # y se paga peor
    finally:
        AG.AVISOS[0]["n_max"] = guardado


def test_una_pelea_se_separa_dando_el_alto(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    _solo_avisos(p, "pelea")
    a = _aviso(robot, p)
    _a(p, a["lugar"], 6.0)
    son = _oir(p)
    robot.frames(60)
    assert a["fase"] == "pelea" and len(a["sospechosos"]) == 2 and "golpe" in son and all(not s.hostil for s in a["sospechosos"])
    AG.AJ.n["pelea_alto_prob"] = 100
    dinero = j.dinero
    robot.tecla(pygame.K_h)
    assert p.trabajo["aviso"] is None and j.dinero > dinero and any(f in _todo(robot) for f in AG.AJ.lista("frases_pelea_calma"))
    # la otra manera: uno se revuelve, y hay que reducirle
    AG.AJ.n["pelea_alto_prob"] = 0
    a = _aviso(robot, p)
    _a(p, a["lugar"], 6.0)
    robot.frames(10)
    robot.tecla(pygame.K_h)
    assert a["fase"] == "pelea"                                    # dar voces seguidas no sirve: entre un alto y otro pasan unos segundos
    robot.frames(140)
    robot.tecla(pygame.K_h)
    assert a["fase"] == "actuar" and len(a["sospechosos"]) == 1 and a["sospechosos"][0].hostil
    s = a["sospechosos"][0]
    p.danar_persona(s, s.salud * 0.9)
    assert s.rendido
    j.x, j.y = s.x, s.y
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.policia["detenciones"] == 1 and j.puntos_busqueda == 0


def _detras(robot, p, v, segundos):
    """Mantiene el coche del jugador pegado detrás de otro vehículo durante un rato."""
    pv = p.j.veh
    for _ in range(int(segundos * 30)):
        pv.x, pv.y, pv.vel = v.x - 9 * math.sin(math.radians(v.rumbo)), v.y - 9 * math.cos(math.radians(v.rumbo)), 0.0
        robot.frames(1)


def test_un_conductor_temerario_se_para_con_la_sirena_y_se_multa(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    patrulla = p.trabajo["patrulla"]
    p._subir(patrulla, False, callar=True)
    _solo_avisos(p, "temerario")
    AG.AJ.n["temerario_obedece"] = 100
    a = _aviso(robot, p)
    v = a["veh"]
    assert a["fase"] == "seguir" and v is not None and v.ia == "huida" and v.tag == "objetivo" and "sirena" in robot.dicho()
    # sin sirena no para, por mucho que te pegues
    _detras(robot, p, v, 4)
    assert a["fase"] == "seguir" and "Enciende la sirena con la P" in _todo(robot)
    robot.tecla(pygame.K_p)
    assert p.sirena_propia is not None
    _detras(robot, p, v, 4)
    assert a["fase"] == "parado" and v.ia == "aparcado" and any(f in _todo(robot) for f in AG.AJ.lista("frases_para"))
    # Intro a su lado: multa, aviso o detención
    patrulla.x, patrulla.y, patrulla.vel = v.x, v.y - 7, 0.0
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and [_texto(o).split(" de ")[0] for o in m.opciones][:1] == ["Ponerle una multa"]
    assert _texto(m.opciones[-1]) == "Detener al conductor" and "pasarse" in m.opciones[-1].ayuda
    dinero = j.dinero
    _elegir(robot, "Ponerle una multa")
    assert robot.app.pila[-1] is p and p.trabajo["aviso"] is None and j.policia["multas"] == 1
    comision = int(AG.AJ("multa_importe") * AG.AJ("multa_comision") / 100)
    assert j.dinero >= dinero + 130 + comision and j.puntos_busqueda == 0
    # el que no obedece se convierte en persecución, y se le para a golpes
    AG.AJ.n["temerario_obedece"] = 0
    a = _aviso(robot, p)
    v = a["veh"]
    _detras(robot, p, v, 4)
    assert a.get("huyo") and a["fase"] == "seguir" and any(f in _todo(robot) for f in AG.AJ.lista("frases_no_para"))
    p.danar_vehiculo(v, v.salud_max * 0.6)
    robot.frames(3)
    assert a["fase"] in ("parado", "actuar")
    if a["fase"] == "parado":
        patrulla.x, patrulla.y, patrulla.vel = v.x, v.y - 7, 0.0
        robot.tecla(pygame.K_RETURN)
        assert _texto(robot.app.pila[-1].opciones[0]) == "Detener al conductor"       # ahora sí procede
        _elegir(robot, "Detener al conductor")
    else:
        s = a["sospechosos"][0]
        assert s.nombre == "Conductor fugado" and s.estado == "huye"
        p.salir_vehiculo(forzado=True)
        p.danar_persona(s, s.salud * 0.9)
        assert s.rendido
        j.x, j.y = s.x, s.y
        robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.policia["detenciones"] == 1 and j.policia.get("apercibimientos", 0) == 0


def test_una_persecucion(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    p._subir(p.trabajo["patrulla"], False, callar=True)
    _solo_avisos(p, "persecucion")
    a = _aviso(robot, p)
    v = a["veh"]
    assert v.hostil and v.vel_obj > 15 and "a la fuga" in v.nombre
    assert v.dist(*p.pos()) < 450                                 # sale lo bastante cerca como para alcanzarlo
    # si no le alcanzas a tiempo, se escapa
    a["limite"] = 0.01
    dinero = j.dinero
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.dinero == dinero and any(f in _todo(robot) for f in AG.AJ.lista("frases_escapa"))
    # si lo destrozas con el conductor dentro, se paga peor, pero no es un exceso: huía
    a = _aviso(robot, p)
    v = a["veh"]
    p.danar_vehiculo(v, 99999)
    assert _hasta(robot, lambda: p.trabajo["aviso"] is None, 12)
    assert j.policia["bajas"] == 1 and j.policia.get("apercibimientos", 0) == 0
    # al salir de la localidad se acaba el turno, como cualquier trabajo: el aviso se retira y el coche prestado se devuelve
    a = _aviso(robot, p)
    v, patrulla = a["veh"], p.trabajo["patrulla"]
    otro = next(m for m in p.mapas.values() if m.tipo == "ciudad" and m.id != p.mundo.id)
    p.cambiar_mapa(otro.id, *otro.punto_libre(otro.ancho / 2, otro.alto / 2))
    robot.frames(5)
    assert not p.de_servicio() and p.es_agente() and j.veh is None and v not in p.vehiculos and patrulla not in p.vehiculos


def test_delinquir_de_servicio_cuesta_la_placa(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    com = p.lugares["comisaria"]
    assert p.ingresar_policia() and p.empezar_turno(com)
    _persona(p, "civil", 6, estado="quieto")                       # un testigo
    # una falta pequeña: apercibimiento, y la policía no va a por ti
    p.delito(1.2, "robo de vehículo", siempre=True)
    assert j.policia["apercibimientos"] == 1 and j.puntos_busqueda == 0 and p.de_servicio()
    assert "Apercibimiento" in _todo(robot) or "toma nota" in _todo(robot)
    _armar(p)
    p._ruido_disparo(*p.pos())                                     # disparar sin un sospechoso delante, también
    assert j.policia["apercibimientos"] == 2 and j.puntos_busqueda == 0
    # a la tercera, fuera: y entonces sí cuenta
    p.delito(1.0, "amenazas", siempre=True)
    assert not p.es_agente() and not p.de_servicio() and j.puntos_busqueda > 0 and j.policia["expulsado"] == p.dia + AG.AJ("expulsion_dias")
    assert any(f.split("{")[0] in _todo(robot) for f in AG.AJ.lista("frases_expulsion"))
    assert "Te quitaron la placa" in p.ingreso_motivo()
    p._fin_persecucion()
    p.dia += int(AG.AJ("expulsion_dias")) + 1
    j.ciudadania = 60.0
    assert p.ingreso_motivo() == ""                                # pasado el plazo, se puede volver a ingresar
    # un delito serio no tiene apercibimiento que valga
    assert p.ingresar_policia() and p.empezar_turno(com)
    patrulla = p.trabajo["patrulla"]
    civil = _persona(p, "civil", 4, estado="quieto")
    p.danar_persona(civil, 9999)
    assert not p.es_agente() and not p.de_servicio() and j.puntos_busqueda >= 2 and patrulla not in p.vehiculos
    # y lo que nadie ve, no consta: sin testigos no hay apercibimiento ni delito
    p._fin_persecucion()
    p.dia += int(AG.AJ("expulsion_dias")) + 1
    p.personas = []
    assert p.ingresar_policia() and p.empezar_turno(com)
    p.delito(1.0, "robo de vehículo")
    assert j.policia.get("apercibimientos", 0) == 0 and j.puntos_busqueda == 0 and p.de_servicio()


def test_ascensos_y_rangos(robot, datos_de_serie):
    p = _agente(robot)
    j = p.j
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    cada = int(AG.AJ("ascenso_cada"))
    j.stats["serv_policia"] = cada - 1
    assert p.rango_policia() == 0
    _solo_avisos(p, "pelea")
    AG.AJ.n["pelea_alto_prob"] = 100
    a = _aviso(robot, p)
    _a(p, a["lugar"], 6.0)
    robot.frames(10)
    robot.tecla(pygame.K_h)
    assert j.stats["serv_policia"] == cada and p.rango_policia() == 1 and p.rango_policia_txt() == "agente de policía"
    assert "scenso" in _todo(robot) or "ascienden" in _todo(robot)
    from juego import menus_vida
    menus_vida.carrera(p)                                          # y consta en Tu carrera, en el móvil
    assert any("Policía: eres agente de policía. Avisos resueltos: %d" % cada in _texto(o) for o in robot.app.pila[-1].opciones)
    _cerrar_menus(robot)
    j.stats["serv_policia"] = 9999
    assert p.rango_policia() == len(AG.AJ.lista("rangos")) - 1     # el último rango es el tope
    # empezar una misión acaba el turno, y el aviso en curso se retira sin dejar nada en la calle
    a = _aviso(robot, p)
    _a(p, a["lugar"], 6.0)
    robot.frames(10)
    sospechosos = list(a["sospechosos"])
    assert sospechosos
    p.iniciar_mision(next(x for x in p.datos["misiones"] if x["id"] == "tut02"))
    assert not p.de_servicio() and not any(s in p.personas for s in sospechosos)
    robot.saltar_dialogos()
    p.abandonar_mision()


# ====================================================================== opciones, editor, sonidos y documentación
def test_las_opciones_nuevas_y_su_valor_de_serie(robot):
    from juego import menus_juego
    serie = {"gente_actua": True, "ia_acciones": False, "pareja_convive": False, "oficio_policia": False}
    for k, v in serie.items():
        assert config.POR_DEFECTO[k] is v, k
    menus_juego.opciones(robot.app)
    m = robot.app.pila[-1]
    _elegir(robot, "La calle")
    calle = robot.app.pila[-1]
    for empieza, valor in (("La gente con la que hablas también actúa", "sí"), ("Modo: poder trabajar de policía", "no")):
        o = _opcion(calle, empieza)
        assert _texto(o).endswith(": " + valor) and len(o.ayuda) > 120
    robot.app.cerrar(calle)
    _elegir(robot, "Contenido para adultos")
    o = _opcion(robot.app.pila[-1], "Vida en pareja")
    assert _texto(o).endswith(": no") and "Cada persona decide" in o.ayuda
    cfg = robot.app.cfg
    robot.app.pila[-1].i = robot.app.pila[-1].opciones.index(o)
    robot.tecla(pygame.K_RIGHT)
    assert cfg["pareja_convive"] is True
    robot.tecla(pygame.K_RIGHT)
    assert cfg["pareja_convive"] is False


def test_el_editor_edita_todo_lo_nuevo():
    from editor import modelo
    from editor.esquema import ESQUEMAS, SECCIONES, TIPOS_PASO
    titulos = {clave: (titulo, esq) for clave, titulo, esq in SECCIONES}
    for clave in ("carta_domicilio", "domicilio", "atracos", "pactos", "contratos", "reacciones", "planes_pareja", "convivencia", "policia_oficio", "avisos_policia"):
        assert clave in titulos and titulos[clave][1] in ESQUEMAS and clave in M.SECCIONES_VIDA, clave
    campos = {esq: {c["k"] for c in ESQUEMAS[esq]["campos"]} for esq in ESQUEMAS}
    for modulo, esq in ((DO, "ajuste_domicilio"), (AT, "ajuste_atracos"), (PA, "ajuste_pactos"), (RE, "ajuste_reacciones"), (CV, "ajuste_convivencia"), (AG, "ajuste_policia")):
        assert campos[esq] == set(modulo.AJ._n) | set(modulo.AJ._l) | {"id"}, (esq, campos[esq] ^ (set(modulo.AJ._n) | set(modulo.AJ._l) | {"id"}))
    assert {"situacion", "paga", "paga_escolta", "refuerzo", "modelos", "objetos", "personas", "locales", "desde", "peso"} <= campos["contrato"]
    assert {"escenas", "requiere", "en_casa", "afinidad", "animo"} <= campos["plan_pareja"] and {"tipo", "frases", "sospechoso", "modelos"} <= campos["aviso_policia"]
    assert {"que", "metros", "giro"} <= campos["paso"] and "explicacion" in campos["mision"] and "intimidar" in campos["enemigo"] and "convivir" in campos["persona"]
    assert "practica" in dict(TIPOS_PASO)
    situaciones = dict(next(c for c in ESQUEMAS["contrato"]["campos"] if c["k"] == "situacion")["ops"])
    assert set(situaciones) == set(CO.SITUACIONES)
    assert set(dict(next(c for c in ESQUEMAS["aviso_policia"]["campos"] if c["k"] == "tipo")["ops"])) == set(AG.TIPOS)
    # un mod con un contrato, un plato y un aviso propios pasa la comprobación del editor y el juego lo carga
    cat = modelo.Catalogo()
    mod = modelo.Mod()
    mod.info = {"nombre": "Prueba", "autor": "Yo"}
    mod.secciones["contratos"].append({"id": "mod_susto", "nombre": "Un susto", "situacion": "intimidar", "peso": 5, "paga": 300, "paga_escolta": 100, "objetivo": "maton", "escolta": "maton",
                                       "resumen": "{quien}, en {lugar}, con {n}."})
    mod.secciones["carta_domicilio"].append({"id": "mod_paella", "nombre": "Paella para dos", "tipo": "comida", "precio": 22, "hambre": 100, "sed": 0, "salud": 30})
    mod.secciones["avisos_policia"].append({"id": "mod_gamberros", "nombre": "Gamberros", "tipo": "pelea", "peso": 1, "paga": 90, "sospechoso": "maton", "frases": ["Central: gamberros en {lugar}."]})
    errores, avisos = modelo.comprobar(mod, cat)
    assert not errores, errores


def test_los_sonidos_nuevos_estan_en_todos_los_packs_y_en_la_guia():
    from juego import catalogo_sonidos
    assert sintesis.VERSION_CACHE >= 19
    S = sintesis.generar()
    for n in ("timbre", "emisora"):
        assert n in S and 0.4 < len(S[n]) / sintesis.SR < 2.0 and not sintesis.es_bucle(n)
        assert catalogo_sonidos.describir(n) != "Sonido del juego."
        for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
            carpeta = os.path.join(rutas.PACKS, pack)
            assert os.path.isdir(carpeta) and any(os.path.exists(os.path.join(carpeta, n + e)) for e in rutas.EXT_AUDIO), (pack, n)
    guia = open(os.path.join(rutas.DATA, "docs", "cambiar_sonidos_es.html"), encoding="utf-8").read()
    assert "timbre" in guia and "emisora" in guia


def test_el_manual_y_la_guia_del_editor_cuentan_lo_nuevo():
    manual = open(os.path.join(rutas.DATA, "docs", "manual_es.html"), encoding="utf-8").read()
    for frase in ("Comida a domicilio", "Atracar cualquier local", "Asaltar a un proveedor", "Negociar con las bandas", "El tablón de encargos", "Pedirle un favor",
                  "que se una a tu banda", "Vivir en pareja", "Planes en pareja", "Trabajar de policía", "dar el alto", "lancha de prácticas"):
        assert frase in manual, frase
    editor = open(os.path.join(rutas.DATA, "docs", "editor_mods_es.html"), encoding="utf-8").read()
    for frase in ("Contratos del tablón", "Comida a domicilio", "Avisos de la emisora", "Planes en pareja", "Negociar con las bandas", "Práctica de un tutorial"):
        assert frase in editor, frase
    assert ".json" not in manual and ".py" not in manual             # el manual es para quien juega: nada de programación
