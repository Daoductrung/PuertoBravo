"""Trabajo 1.7.1, tanda 6: comprar paseando por la tienda (pasillos, cesta y caja), despensa y nevera en casa, y cocinar."""
import json
import os
import random

import pygame
import pytest

from juego import ajustes, compra as C, config, domicilio as DO, menus_cocina as MC, menus_juego, mundo as M, rutas, sintesis, sistemas
from juego.menus import Menu


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
    for v in [v for v in p.vehiculos if v is not p.j.veh]:
        p.quitar_vehiculo(v)
    p.personas = []
    p.t_poblar = 1e9
    return p


def _ajustar(**valores):
    """Cambia unos números de la sección cocina, como haría un mod."""
    base = {"id": "general"}
    base.update(valores)
    C.AJ.configurar({"cocina": [base]})


def _sin_azar(**mas):
    """Tiendas sin faltas ni ofertas, y platos que no se queman ni salen de categoría: para contar con números fijos."""
    _ajustar(falta_prob=0, oferta_descuento=0, prob_quemado=0, prob_especial=0, practica_especial=0, **mas)


def _oir(robot):
    sonados = []
    original = robot.app.mez.sonar

    def sonar(nombre, *a, **kw):
        sonados.append(nombre)
        return original(nombre, *a, **kw)
    robot.app.mez.sonar = sonar
    return sonados


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
    if p.j.veh:
        p.salir_vehiculo(forzado=True)
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + dx, l.y)


def _ultimo(robot):
    return robot.app.voz.registro[-1]


def _entrar_en_tienda(robot, p, l):
    """Entra en la tienda por su menú y la recorre por dentro. Devuelve (el menú de la tienda, el recorrido)."""
    _a(p, l, 2.0)
    menus_juego.lugar(p, l)
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu)
    _elegir(robot, "Recorrer el local por dentro")
    t = robot.app.pila[-1]
    assert isinstance(t, C.Tienda)
    return menu, t


def _ir(robot, t, que):
    """Camina por la tienda, con las flechas, hasta un sitio: 'caja', 'salir' o el identificador de un pasillo."""
    def es(h):
        return h[2] == que or (isinstance(h[2], tuple) and h[2] == ("pasillo", que))
    destino = next(k for k, h in enumerate(t.habitaciones) if es(h))
    while t.i != destino:
        robot.tecla(pygame.K_RIGHT if destino > t.i else pygame.K_LEFT)
    return t.habitaciones[t.i]


def _coger(robot, t, pasillo, *productos):
    """Abre un pasillo y echa a la cesta, con Intro, una unidad de cada producto."""
    _ir(robot, t, pasillo)
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, C.MenuCesta)
    for pid in productos:
        nombre = robot.p.producto(pid)["nombre"]
        m.i = next(k for k, o in enumerate(m.opciones) if _texto(o).startswith(nombre))
        robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is t


def _dar(p, casa, *ids, encima=False):
    """Pone productos en la cocina de una casa (o encima), como recién comprados hoy."""
    for pid in ids:
        lote = p._lote_de(p.producto(pid), 1)
        if encima:
            p._meter(p.j.encima, lote)
        else:
            p._meter(p.despensa(casa), lote)


def _receta(p, rid):
    return next(r for r in C.recetas(p) if r["id"] == rid)


class _Azar:
    """Un azar que no lo es: siempre lo primero y siempre el mismo número."""

    def __init__(self, valor=0.99):
        self.valor = valor

    def random(self):
        return self.valor

    def choice(self, lista):
        return lista[0]

    def uniform(self, a, b):
        return a


# ====================================================================== los datos
def test_los_datos_traen_pasillos_productos_tiendas_y_recetas(datos_de_serie):
    d = json.load(open(os.path.join(rutas.DATOS, "vida.json"), encoding="utf-8"))
    assert d["pasillos"] == C.PASILLOS and d["productos"] == C.PRODUCTOS and d["tipos_tienda"] == C.TIPOS_TIENDA and d["recetas"] == C.RECETAS
    general = d["cocina"][0]
    assert set(general) == set(C.AJ._n) | set(C.AJ._l) | {"id"}
    assert all(general[k] == v for k, v in C.AJ._n.items()) and all(general[k] == v for k, v in C.AJ._l.items())
    for clave in ("pasillos", "productos", "tipos_tienda", "recetas", "cocina"):
        assert clave in M.SECCIONES_VIDA
    pasillos = {x["id"] for x in C.PASILLOS}
    productos = {x["id"]: x for x in C.PRODUCTOS}
    assert len(productos) == len(C.PRODUCTOS) >= 30 and all(x["pasillo"] in pasillos for x in C.PRODUCTOS)
    assert all(pa in pasillos for t in C.TIPOS_TIENDA for pa in t["pasillos"]) and sum(1 for t in C.TIPOS_TIENDA if t.get("resto")) == 1
    assert len(C.RECETAS) >= 10
    for r in C.RECETAS:
        assert all(i in productos for i in r["ingredientes"]) and r["raciones"] >= 2 and r["minutos"] > 0 and r["fuego"] in C.FUEGOS, r["id"]
    # lo cocinado alimenta claramente más que lo envasado y que lo que se come tal cual
    envasado = max(x.get("hambre", 0) for x in C.PRODUCTOS)
    assert min(r["hambre"] for r in C.RECETAS) >= 1.5 * envasado
    assert sum(r["hambre"] for r in C.RECETAS) / len(C.RECETAS) >= 2.5 * envasado
    # y sale mucho más a cuenta que pedir a domicilio: una receta entera cuesta menos que un menú del día y da varias raciones
    menu_dia = next(c for c in DO.CARTA if c["id"] == "menu_dia")
    for r in C.RECETAS:
        assert sum(productos[i]["precio"] for i in r["ingredientes"]) <= menu_dia["precio"] + 3, r["id"]
    # los números se pueden cambiar en los datos, y lo que venga mal vale lo de serie
    ajustes.configurar_todos({"cocina": [{"id": "general", "capacidad_nevera": 3, "prob_quemado": 0, "capacidad_despensa": "mal", "frases_caja": ["Hala, {total}."], "frases_dejar": []}]})
    assert C.AJ("capacidad_nevera") == 3 and C.AJ("prob_quemado") == 0 and C.AJ("capacidad_despensa") == 30
    assert C.AJ.lista("frases_caja") == ["Hala, {total}."] and len(C.AJ.lista("frases_dejar")) == 3


def test_cada_tienda_es_de_su_clase_y_las_que_no_venden_comida_quedan_como_estaban(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    clases = {"tienda_paco": "ultramarinos", "tienda_centro": "supermercado", "mercado_pb": "mercado", "gasolinera": "gasolinera", "tienda_playa": "bazar"}
    for lid, clase in clases.items():
        assert p.tipo_tienda(p.lugares[lid])["id"] == clase, lid
    assert p.tipo_tienda(p.lugares["ferreteria"]) is None and p.surtido(p.lugares["ferreteria"]) == []
    assert p.tipo_tienda(p.lugares["casa_abuela"]) is None
    assert [pa["id"] for pa, _ in p.surtido(p.lugares["tienda_centro"])] == [x["id"] for x in C.PASILLOS]       # el súper lo tiene todo
    assert [pa["id"] for pa, _ in p.surtido(p.lugares["gasolinera"])] == ["bebidas", "preparados"]
    # el pescado y la carne, solo en el mercado y en el súper; el mercado es más barato y la gasolinera, más cara
    assert "pescaderia" not in [pa["id"] for pa, _ in p.surtido(p.lugares["tienda_paco"])]
    agua = p.producto("agua_botella")
    tomates = dict(p.producto("tomates"), precio=100)
    assert p.precio_producto(p.lugares["mercado_pb"], tomates) < p.precio_producto(p.lugares["tienda_centro"], tomates) < p.precio_producto(p.lugares["gasolinera"], dict(agua, precio=100))
    # el campo Surtido de un lugar manda sobre el nombre
    ferre = p.lugares["ferreteria"]
    ferre.d["surtido"] = "mercado"
    assert p.tipo_tienda(ferre)["id"] == "mercado"
    del ferre.d["surtido"]
    # la ferretería se recorre como siempre, y su menú no ofrece comida para casa
    _a(p, ferre, 2.0)
    menus_juego.lugar(p, ferre)
    m = robot.app.pila[-1]
    assert not [o for o in m.opciones if _texto(o).startswith("Comprar comida para llevar")]
    assert _texto(_opcion(m, "Recorrer")) == "Recorrer el local por dentro"
    _elegir(robot, "Recorrer")
    assert type(robot.app.pila[-1]) is sistemas.Local


# ====================================================================== recorrer la tienda
def test_recorrer_la_tienda_coger_devolver_y_pagar_en_la_caja(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    j = p.j
    j.dinero = 100
    l = p.lugares["tienda_paco"]
    son = _oir(robot)
    menu, t = _entrar_en_tienda(robot, p, l)
    assert "Coges una cesta" in _ultimo(robot) and "6 pasillos" in _ultimo(robot) and "la frutería" in _ultimo(robot)
    # el recorrido: la puerta, la caja, un pasillo por cada clase de producto y la trastienda
    assert [h[2] for h in t.habitaciones] == ["salir", "caja"] + [("pasillo", pa["id"]) for pa, _ in p.surtido(l)] + ["escuchar"]
    # cada paso se oye, y al llegar se dice qué pasillo es, cómo es y cuántos productos tiene
    son.clear()
    robot.tecla(pygame.K_RIGHT)
    robot.tecla(pygame.K_RIGHT)
    assert son.count("paso_acera0") + son.count("paso_acera1") == 6
    assert _ultimo(robot).startswith("La frutería. Cajas de fruta") and "9 productos" in _ultimo(robot) and "3 de 9" in _ultimo(robot)
    robot.tecla(pygame.K_F1)
    assert "C para saber qué llevas en la cesta" in _ultimo(robot) and "ves lo que hay en este pasillo" in _ultimo(robot)
    robot.tecla(pygame.K_c)
    assert _ultimo(robot) == "La cesta está vacía."
    # el pasillo: cada producto con su precio y para qué es; Intro lo echa a la cesta, con su sonido
    robot.tecla(pygame.K_RETURN)
    pasillo = robot.app.pila[-1]
    assert pasillo.titulo.startswith("La frutería") and len(pasillo.opciones) == 9 + 2            # los productos, la cesta y volver
    tomates = p.producto("tomates")
    precio_t = p.precio_producto(l, tomates)
    assert _texto(pasillo.opciones[0]) == f"Tomates, un kilo: {C._euros(precio_t)}. Para cocinar"
    assert "Para comer tal cual" in _texto(_opcion(pasillo, "Manzanas"))
    robot.tecla(pygame.K_F1)
    assert "arroz con pollo" in _ultimo(robot) and "nevera" in _ultimo(robot) and "Caduca a los 5 días" in _ultimo(robot)
    son.clear()
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RIGHT)                                    # con la flecha derecha, otro
    assert t.cesta == {"tomates": 2} and son.count("cesta") == 2 and "menu_ok" not in son
    assert "Llevas 2 de esto" in _ultimo(robot) and "En la cesta: 2" in _texto(pasillo.opciones[0])
    robot.tecla(pygame.K_LEFT)                                     # y con la izquierda se devuelve
    assert t.cesta == {"tomates": 1} and "Devuelves tomates" in _ultimo(robot)
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_LEFT)                                     # de lo que no llevas no se puede devolver
    assert "De eso no llevas" in _ultimo(robot) and t.cesta == {"tomates": 1}
    _elegir(robot, "La cesta")
    assert "tomates, un kilo, 1" in _ultimo(robot)
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is t and "Cesta: 1 producto" in _ultimo(robot)
    _coger(robot, t, "lacteos", "huevos", "huevos")
    _coger(robot, t, "despensa", "arroz")
    robot.tecla(pygame.K_c)
    assert "En la cesta, 4 productos" in _ultimo(robot) and "huevos, media docena, 2" in _ultimo(robot)
    total = precio_t + 2 * p.precio_producto(l, p.producto("huevos")) + p.precio_producto(l, p.producto("arroz"))
    assert t.total() == total and j.dinero == 100 and j.encima == []         # todavía no has pagado nada
    # la caja: la cesta, producto a producto, y pagar
    _ir(robot, t, "caja")
    assert f"Llevas 4 productos: {total} euros" in _ultimo(robot)
    robot.tecla(pygame.K_RETURN)
    caja = robot.app.pila[-1]
    assert caja.titulo.startswith("La caja. Cesta: 4 productos") and _texto(caja.opciones[0]) == f"Pagar {total} euros por 4 productos"
    _elegir(robot, "Huevos")                                       # Intro sobre un producto devuelve uno
    assert t.cesta["huevos"] == 1
    total -= p.precio_producto(l, p.producto("huevos"))
    son.clear()
    _elegir(robot, "Pagar")
    assert "caja" in son and j.dinero == 100 - total and t.cesta == {} and robot.app.pila[-1] is t
    assert any(f.replace("{total}", C._euros(total)) in _ultimo(robot) for f in C.AJ.lista("frases_caja")) and "Llevas encima 3 cosas" in _ultimo(robot)
    # lo comprado lo llevas encima, con su fecha: lo fresco caduca y el arroz no
    assert {x["id"]: (x["n"], x["cad"]) for x in j.encima} == {"tomates": (1, p.dia + 5), "huevos": (1, p.dia + 10), "arroz": (1, 0)}
    assert j.stats["compras"] == 1 and j.stats["gastado_comida"] == total
    # sin cesta, la caja es el mostrador de siempre: te atienden en el menú de la tienda
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is menu and any(x in _ultimo(robot) for x in ("Te atienden", "aquí te atienden", "te toca"))
    # y salir con la cesta vacía no pregunta nada
    _elegir(robot, "Recorrer el local por dentro")
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is menu


def test_si_no_llega_el_dinero_se_dice_y_se_puede_quitar_algo(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    j = p.j
    l = p.lugares["tienda_centro"]
    menu, t = _entrar_en_tienda(robot, p, l)
    _coger(robot, t, "pescaderia", "gambas", "merluza")
    _coger(robot, t, "despensa", "arroz")
    total = t.total()
    j.dinero = total - 3
    _ir(robot, t, "caja")
    robot.tecla(pygame.K_RETURN)
    caja = robot.app.pila[-1]
    son = _oir(robot)
    _elegir(robot, "Pagar")
    assert "error" in son and "caja" not in son and j.dinero == total - 3 and j.encima == [] and robot.app.pila[-1] is caja
    assert "Te faltan 3 euros" in _ultimo(robot) or "te faltan 3 euros" in _ultimo(robot)
    _elegir(robot, "Gambas")                                       # se devuelve algo allí mismo, y entonces sí
    assert "gambas" not in t.cesta and "Devuelves gambas" in _ultimo(robot)
    nuevo = t.total()
    _elegir(robot, "Pagar")
    assert j.dinero == total - 3 - nuevo and sorted(x["id"] for x in j.encima) == ["arroz", "merluza"]
    # si lo devuelves todo, la caja se cierra sola
    _coger(robot, t, "bebidas", "zumo")
    _ir(robot, t, "caja")
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Zumo")
    assert robot.app.pila[-1] is t and "La cesta está vacía" in _ultimo(robot)


def test_salir_con_la_cesta_llena_dejarla_o_llevarsela_sin_pagar(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    j.dinero = 50
    l = p.lugares["tienda_paco"]
    # dejar la cesta: no pasa nada
    _sin_azar()
    menu, t = _entrar_en_tienda(robot, p, l)
    _coger(robot, t, "bebidas", "agua_botella", "zumo")
    robot.tecla(pygame.K_ESCAPE)
    aviso = robot.app.pila[-1]
    assert isinstance(aviso, Menu) and aviso.titulo.startswith("Llevas 2 productos sin pagar")
    assert [_texto(o) for o in aviso.opciones] == ["Ir a la caja a pagar", "Dejar la cesta y salir", "Salir sin pagar", "Seguir comprando"]
    assert "hurto" in _opcion(aviso, "Salir sin pagar").ayuda
    _elegir(robot, "Seguir comprando")
    assert robot.app.pila[-1] is t and t.n_cesta() == 2
    _ir(robot, t, "salir")
    robot.tecla(pygame.K_RETURN)                                   # también por la puerta
    _elegir(robot, "Ir a la caja a pagar")
    assert robot.app.pila[-1].titulo.startswith("La caja")
    robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_ESCAPE)
    _elegir(robot, "Dejar la cesta y salir")
    assert robot.app.pila[-1] is menu and j.encima == [] and j.dinero == 50 and j.puntos_busqueda == 0
    assert any(f in robot.dicho() for f in C.AJ.lista("frases_dejar"))
    _cerrar_menus(robot)
    # llevársela sin que te vean: te lo llevas y no pasa nada
    _sin_azar(robo_visto=0, robo_visto_cosa=0)
    menu, t = _entrar_en_tienda(robot, p, l)
    _coger(robot, t, "bebidas", "agua_botella")
    robot.tecla(pygame.K_ESCAPE)
    _elegir(robot, "Salir sin pagar")
    assert robot.app.pila[-1] is p and p.interior is None                    # a la calle
    assert [x["id"] for x in j.encima] == ["agua_botella"] and j.dinero == 50 and j.puntos_busqueda == 0 and not p.local_te_recuerda(l)
    assert any(f in robot.dicho() for f in C.AJ.lista("frases_robo_limpio")) and j.stats["hurtos"] == 1
    # y si te ven: es un hurto. Te buscan, baja el prestigio y la tienda no te deja entrar unos días
    _sin_azar(robo_visto=100)
    prestigio = j.ciudadania
    menu, t = _entrar_en_tienda(robot, p, l)
    _coger(robot, t, "bebidas", "zumo", "zumo")
    robot.tecla(pygame.K_ESCAPE)
    _elegir(robot, "Salir sin pagar")
    assert robot.app.pila[-1] is p and j.dinero == 50
    assert {x["id"]: x["n"] for x in j.encima} == {"agua_botella": 1, "zumo": 2}
    assert j.puntos_busqueda > 0 and j.ciudadania < prestigio and any(f in robot.dicho() for f in C.AJ.lista("frases_robo_visto"))
    robot.frames(5)
    assert j.estrellas >= 1
    r = p.local_te_recuerda(l)
    assert r and r["hasta"] == p.dia + 2 and r["modo"] == "cerrado"
    j.puntos_busqueda, j.estrellas = 0, 0
    menus_juego.lugar(p, l)
    assert robot.app.pila[-1] is p                                  # no te abren
    p.dia += 3
    menus_juego.lugar(p, l)
    assert isinstance(robot.app.pila[-1], Menu)                     # ya se les ha pasado


def test_cada_dia_falta_algo_y_hay_una_oferta_y_no_se_carga_mas_de_la_cuenta(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    j.dinero = 500
    l = p.lugares["tienda_centro"]
    todos = [x for _, lista in p.surtido(l) for x in lista]
    # la oferta: un producto, el mismo todo el día, más barato; cambia con los días y de una tienda a otra
    _ajustar(falta_prob=0, oferta_descuento=50)
    of = p.oferta_de(l)
    assert of in [x["id"] for x in todos] and p.oferta_de(l) == of
    caro = dict(p.producto(of), precio=100)
    con = p.precio_producto(l, caro)
    _ajustar(falta_prob=0, oferta_descuento=0)
    assert p.oferta_de(l) is None and con == round(p.precio_producto(l, caro) / 2)
    _ajustar(falta_prob=0, oferta_descuento=50)
    dia = p.dia
    ofertas = set()
    for d in range(12):
        p.dia = dia + d
        ofertas.add(p.oferta_de(l))
    p.dia = dia
    assert len(ofertas) > 3
    # lo que falta: con la probabilidad de los datos; lo que está de oferta no falta nunca
    _ajustar(falta_prob=100, oferta_descuento=50)
    assert [x["id"] for x in todos if not p.agotado(l, x)] == [of]
    _ajustar(falta_prob=30, oferta_descuento=0)
    faltan = [x["id"] for x in todos if p.agotado(l, x)]
    assert 0 < len(faltan) < len(todos) and faltan == [x["id"] for x in todos if p.agotado(l, x)]
    menu, t = _entrar_en_tienda(robot, p, l)
    prod = p.producto(faltan[0])
    _ir(robot, t, prod["pasillo"])
    robot.tecla(pygame.K_RETURN)
    assert _texto(_opcion(robot.app.pila[-1], prod["nombre"])) == f"{prod['nombre']}: hoy no queda"
    _elegir(robot, prod["nombre"])
    assert t.cesta == {} and "hoy no queda" in _ultimo(robot)
    robot.tecla(pygame.K_ESCAPE)
    # no se puede cargar con más de lo que cabe encima
    _ajustar(falta_prob=0, oferta_descuento=0, capacidad_encima=3)
    j.encima = [{"id": "arroz", "n": 2, "cad": 0}]
    _coger(robot, t, "bebidas", "agua_botella", "agua_botella")
    assert t.cesta == {"agua_botella": 1} and p.encima_cabe() == 1
    robot.tecla(pygame.K_ESCAPE)
    _elegir(robot, "Dejar la cesta y salir")
    # y por el menú rápido, lo mismo
    _elegir(robot, "Comprar comida para llevar a casa")
    _elegir(robot, "Botella de agua")
    _elegir(robot, "Botella de agua")
    assert p._total(j.encima) == 3 and "No puedes cargar con tanto" in _ultimo(robot)


def test_el_menu_rapido_de_la_tienda_sigue_y_vende_lo_mismo(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    j = p.j
    j.dinero = 60
    l = p.lugares["tienda_paco"]
    _a(p, l, 2.0)
    menus_juego.lugar(p, l)
    menu = robot.app.pila[-1]
    textos = [_texto(o) for o in menu.opciones]
    # lo de siempre sigue en su sitio: comer algo en el acto, el botiquín, la ganzúa, atracar
    assert any(t.startswith("Botiquín") for t in textos) and any("anzúa" in t for t in textos) and "Atracar la tienda" in textos
    assert sum(1 for t in textos if "recupera" in t and "de salud" in t) == 2
    o = _opcion(menu, "Comprar comida para llevar a casa")
    assert "sin pasear" in o.ayuda and "Recorrer el local por dentro" in o.ayuda
    assert "cesta" in _opcion(menu, "Recorrer el local por dentro").ayuda
    _elegir(robot, "Comprar comida para llevar a casa")
    rapido = robot.app.pila[-1]
    genero = [x for _, lista in p.surtido(l) for x in lista]
    assert len(rapido.opciones) == len(genero) + 1                 # lo mismo que hay en los pasillos, y volver
    assert all(_texto(o).startswith(x["nombre"]) for o, x in zip(rapido.opciones, genero))
    son = _oir(robot)
    _elegir(robot, "Patatas")
    _elegir(robot, "Huevos")
    precio = p.precio_producto(l, p.producto("patatas")) + p.precio_producto(l, p.producto("huevos"))
    assert j.dinero == 60 - precio and son.count("caja") == 2 and sorted(x["id"] for x in j.encima) == ["huevos", "patatas"]
    assert "Llevas encima 2 cosas" in _ultimo(robot)
    j.dinero = 0
    _elegir(robot, "Patatas")
    assert p._total(j.encima) == 2 and ("No te llega" in _ultimo(robot) or "Te faltan" in _ultimo(robot))
    # comer algo en el acto, como siempre: no va a la despensa ni a la bolsa
    robot.app.cerrar(rapido)
    j.dinero, j.salud = 50, 40.0
    comida = next(o for o in menu.opciones if "recupera" in _texto(o))
    menu.i = menu.opciones.index(comida)
    robot.tecla(pygame.K_RETURN)
    assert j.salud > 40.0 and p._total(j.encima) == 2


# ====================================================================== despensa y nevera
def test_guardar_la_compra_cada_cosa_a_su_sitio_con_cantidades_y_capacidad(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar(capacidad_nevera=3, capacidad_despensa=4, nevera_grande=2)
    j = p.j
    casa = p.lugares["casa_abuela"]
    assert j.despensa == {} and j.encima == [] and not p.hay_cocina(casa)
    _dar(p, casa, "tomates", "tomates", "huevos", "pollo", "leche", "arroz", "arroz", "arroz", "patatas", "atun", "macarrones", encima=True)
    assert {x["id"]: x["n"] for x in j.encima} == {"tomates": 2, "huevos": 1, "pollo": 1, "leche": 1, "arroz": 3, "patatas": 1, "atun": 1, "macarrones": 1}
    assert p.hay_cocina(casa) and p.sitio_capacidad(casa, "nevera") == 3 and p.sitio_capacidad(casa, "despensa") == 4
    guardado, queda = p.guardar_compra(casa)
    # caben tres cosas frescas y cuatro de despensa: el resto se queda contigo
    assert (guardado, queda) == (7, 4)
    assert {x["id"]: x["n"] for x in p.de_sitio(casa, "nevera")} == {"tomates": 2, "huevos": 1}
    assert {x["id"]: x["n"] for x in p.de_sitio(casa, "despensa")} == {"arroz": 3, "patatas": 1}
    assert {x["id"]: x["n"] for x in j.encima} == {"pollo": 1, "leche": 1, "atun": 1, "macarrones": 1}
    assert p.cocina_txt(casa) == "Nevera: 3 de 3. Despensa: 4 de 4" and p.sitio_cabe(casa, "nevera") == 0
    # la cocina equipada trae la nevera grande
    j.muebles[casa.id] = ["cocina"]
    assert p.sitio_capacidad(casa, "nevera") == 5 and p.guardar_compra(casa) == (2, 2)
    # cada casa tiene su despensa
    otra = type("Casa", (), {"id": "otra_casa", "nombre": "Otra casa", "tipo": "casa"})()
    assert p.despensa(otra) == [] and p.guardar_compra(otra) == (2, 0) and len(p.despensa(casa)) == 6
    # y las de las casas que dejan de ser tuyas no se quedan en la partida
    p.limpiar_despensas()
    assert list(j.despensa) == [casa.id]
    # un producto de un mod que ya no está desaparece sin romper nada
    p.despensa(casa).append({"id": "ya_no_existe", "n": 2, "cad": 0})
    assert all(x["id"] != "ya_no_existe" for x in p.despensa(casa))


def test_la_cocina_de_casa_el_menu_la_nevera_y_la_despensa(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar()
    j = p.j
    casa = p.lugares["casa_abuela"]
    _a(p, casa, 2.0)
    menus_juego.lugar(p, casa)
    menu = robot.app.pila[-1]
    o = _opcion(menu, "Cocina. ")
    assert _texto(o) == "Cocina. Nevera: 0 de 14. Despensa: 0 de 30" and "Recorrer la casa por dentro" in o.ayuda
    # sin nada guardado ni comida encima, la cocina hace lo de siempre, y lo recuerda
    _elegir(robot, "Recorrer la casa por dentro")
    interior = robot.app.pila[-1]
    interior.i = next(k for k, h in enumerate(interior.habitaciones) if h[2] == "cocina")
    j.salud = 40.0
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is interior and j.salud == 65.0 and j.dia_nevera == p.dia
    assert "algo con lo que hay en la nevera" in _ultimo(robot) and "La despensa está vacía" in _ultimo(robot)
    # con la compra encima, se abre el menú de la cocina
    _dar(p, casa, "tomates", "huevos", "patatas", "sandwich", "agua_botella", "atun", encima=True)
    son = _oir(robot)
    robot.tecla(pygame.K_RETURN)
    cocina = robot.app.pila[-1]
    assert isinstance(cocina, Menu) and cocina.titulo == f"La cocina de {casa.nombre}. Nevera: 0 de 14. Despensa: 0 de 30"
    assert [_texto(x).split(":")[0] for x in cocina.opciones] == ["Cocinar", "Nevera", "Despensa", "Guardar lo que llevas encima", "Comer algo rápido de lo que haya por casa",
                                                                 "Beber agua del grifo", "Recetas y tu mano en la cocina", "Volver"]
    assert all(x.ayuda for x in cocina.opciones[:6])
    _elegir(robot, "Guardar lo que llevas encima")
    assert "nevera" in son and "Guardas 6 cosas" in _ultimo(robot) and j.encima == []
    assert cocina.titulo.endswith("Nevera: 3 de 14. Despensa: 3 de 30") and not any(_texto(x).startswith("Guardar") for x in cocina.opciones)
    # lo de siempre sigue ahí, una vez al día
    _elegir(robot, "Comer algo rápido")
    assert "Hoy ya te has comido" in _ultimo(robot)
    j.sed = 60.0
    _elegir(robot, "Beber agua del grifo")
    assert j.sed == 0.0
    # la nevera: lo que hay, cuánto y cuándo caduca; lo primero, lo que antes caduca
    son.clear()
    _elegir(robot, "Nevera")
    nevera = robot.app.pila[-1]
    assert "nevera" in son and nevera.titulo == "La nevera: 3 de 14"
    assert [_texto(x) for x in nevera.opciones[:3]] == ["Sándwich envasado, 1 unidad, caduca en 3 días", "Tomates, un kilo, 1 unidad, caduca en 5 días",
                                                        "Huevos, media docena, 1 unidad, caduca en 10 días"]
    # comer de la nevera: quita hambre, da salud y se gasta
    j.hambre, j.salud = 50.0, 50.0
    _elegir(robot, "Sándwich")
    sub = robot.app.pila[-1]
    assert [_texto(x) for x in sub.opciones] == ["Comer una unidad", "Llevarte una encima, para comer fuera", "Tirarlo todo a la basura", "Volver"]
    son.clear()
    _elegir(robot, "Comer una unidad")
    assert j.hambre == 22.0 and j.salud == 56.0 and "comer" in son and robot.app.pila[-1] is nevera and len(nevera.opciones) == 3
    assert "Te comes sándwich envasado" in _ultimo(robot)
    # lo que es para cocinar no se come tal cual
    _elegir(robot, "Huevos")
    assert _texto(robot.app.pila[-1].opciones[0]).startswith("Es para cocinar")
    robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_ESCAPE)
    # la despensa: llevarte algo encima, para comer fuera, y tirar
    _elegir(robot, "Despensa")
    despensa = robot.app.pila[-1]
    assert despensa.titulo == "La despensa: 3 de 30" and "no caduca" in _texto(_opcion(despensa, "Atún"))
    _elegir(robot, "Botella de agua")
    _elegir(robot, "Llevarte una encima")
    assert [x["id"] for x in j.encima] == ["agua_botella"] and robot.app.pila[-1] is despensa
    _elegir(robot, "Patatas")
    _elegir(robot, "Tirarlo todo")
    assert [x["id"] for x in p.de_sitio(casa, "despensa")] == ["atun"] and "Tiras patatas" in _ultimo(robot)
    _cerrar_menus(robot)
    # en la calle, desde el móvil: lo que llevas se come allí mismo
    _a(p, p.lugares["tienda_paco"], 3.0)
    j.sed = 80.0
    robot.tecla(pygame.K_m)
    _elegir(robot, "Inventario")
    inv = robot.app.pila[-1]
    assert _texto(_opcion(inv, "Comida y compra que llevas")) == "Comida y compra que llevas: 1 de 20"
    assert _texto(_opcion(inv, f"En {casa.nombre}")) == f"En {casa.nombre}. Nevera: 2 de 14. Despensa: 1 de 30"
    _elegir(robot, "Comida y compra que llevas")
    son.clear()
    _elegir(robot, "Botella de agua")
    assert j.sed == 10.0 and "beber" in son and j.encima == [] and "Te bebes botella de agua" in _ultimo(robot)
    assert _texto(robot.app.pila[-1].opciones[0]) == "No llevas comida ni compra encima"
    robot.tecla(pygame.K_ESCAPE)
    # y el resumen de la cocina de casa, desde el móvil, solo se lee
    _elegir(robot, f"En {casa.nombre}")
    resumen = robot.app.pila[-1]
    assert [_texto(x) for x in resumen.opciones[:3]] == ["Nevera: Tomates, un kilo, 1 unidad, caduca en 5 días", "Nevera: Huevos, media docena, 1 unidad, caduca en 10 días",
                                                         "Despensa: Atún, tres latas, 1 unidad, no caduca"]
    assert all(x.accion is None for x in resumen.opciones[:3])
    _elegir(robot, "Recetas que sabes hacer")
    assert len(robot.app.pila[-1].opciones) == len(C.RECETAS) + 2 and "Lleva huevos" in _texto(_opcion(robot.app.pila[-1], "Tortilla de patatas"))
    _cerrar_menus(robot)
    # la primera vez que aprieta el hambre, el juego recuerda que se puede cocinar; una sola vez por partida
    j.hambre = 59.0
    p.pasar_necesidades(60)
    assert "cocinar en casa" in robot.dicho() and j.recordado.count("comer_en_casa") == 1
    n = len(robot.app.voz.registro)
    j.hambre = 59.0
    p.pasar_necesidades(60)
    assert not any("cocinar en casa" in t for t in robot.app.voz.registro[n:])


def test_al_cerrar_el_menu_de_la_cocina_se_vuelve_a_la_cocina_sin_repetir_la_entrada(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    casa = p.lugares["casa_abuela"]
    _dar(p, casa, "arroz")
    interior = sistemas.Interior(p, casa, {"descansar": lambda: None, "garaje": lambda: None})
    robot.app.abrir(interior)
    assert "por dentro" in _ultimo(robot)
    interior.i = next(k for k, h in enumerate(interior.habitaciones) if h[2] == "cocina")
    robot.tecla(pygame.K_RETURN)
    assert isinstance(robot.app.pila[-1], Menu)
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is interior and _ultimo(robot) == "La cocina."
    robot.tecla(pygame.K_F1)
    assert "Estás dentro de tu casa" in _ultimo(robot)


def test_lo_fresco_caduca_se_avisa_y_lo_caducado_se_tira(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar()
    j = p.j
    casa = p.lugares["casa_abuela"]
    _dar(p, casa, "merluza", "tomates", "arroz", "pan")            # la merluza aguanta 2 días; el pan, 2; los tomates, 5; el arroz no caduca
    _dar(p, casa, "sandwich", encima=True)                        # 3 días
    hoy = p.dia
    assert p.cad_txt(p.despensa(casa)[0]) == "caduca en 2 días" and p.cad_txt({"id": "arroz", "n": 1, "cad": 0}) == "no caduca"
    assert p.pronto_caduca(p.despensa(casa)) == [] and p.tirar_caducado(p.despensa(casa)) == []
    p.dia = hoy + 1
    assert p.pronto_caduca(p.despensa(casa)) == ["merluza en rodajas mañana", "barra de pan mañana"]
    p.dia = hoy + 2                                                # el último día todavía vale
    assert p.cad_txt(p.despensa(casa)[0]) == "caduca hoy" and p.tirar_caducado(p.despensa(casa)) == []
    MC.menu_sitio(p, casa, "nevera")
    assert "Ojo: caduca merluza en rodajas hoy" in _ultimo(robot) and "pan" not in _ultimo(robot)        # el pan está en la despensa
    _cerrar_menus(robot)
    # al día siguiente, al entrar en la cocina se tira lo caducado, de casa y de lo que llevas, y se dice
    p.dia = hoy + 4
    interior = sistemas.Interior(p, casa, {"descansar": lambda: None, "garaje": lambda: None})
    robot.app.abrir(interior)
    interior.i = next(k for k, h in enumerate(interior.habitaciones) if h[2] == "cocina")
    robot.tecla(pygame.K_RETURN)
    dicho = _ultimo(robot)
    assert "merluza en rodajas" in dicho and "barra de pan" in dicho and "sándwich envasado" in dicho and "tomates" not in dicho
    assert any(f.split("{cosas}")[0] in dicho for f in C.AJ.lista("frases_caducado"))
    assert sorted(x["id"] for x in p.despensa(casa)) == ["arroz", "tomates"] and j.encima == [] and j.stats["comida_tirada"] == 3
    # lo caducado no se puede comer aunque no se haya tirado todavía
    lotes = [{"id": "sandwich", "n": 1, "cad": p.dia - 1}]
    j.hambre = 80.0
    assert p.comer_lote(lotes, lotes[0]) is None and "caducado" in _ultimo(robot) and j.hambre == 80.0
    # ni sirve para cocinar
    p.despensa(casa).append({"id": "huevos", "n": 1, "cad": p.dia - 1})
    _dar(p, casa, "patatas")
    assert p.receta_falta(casa, _receta(p, "huevos_patatas")) == ["huevos, media docena"]


# ====================================================================== cocinar
def test_cocinar_con_y_sin_ingredientes_raciones_y_efectos(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar()
    j = p.j
    casa = p.lugares["casa_abuela"]
    tortilla = _receta(p, "tortilla")
    # sin ingredientes no se cocina, y se dice qué falta
    _dar(p, casa, "huevos")
    assert p.receta_falta(casa, tortilla) == ["patatas, una malla", "cebollas, una ristra"]
    assert p.cocinar(casa, tortilla) is None and "te falta patatas, una malla y cebollas, una ristra" in _ultimo(robot)
    assert p._total(p.despensa(casa)) == 1 and j.stats.get("platos_cocinados", 0) == 0
    # con todo: lo de casa y lo que traes encima valen igual
    _dar(p, casa, "patatas")
    _dar(p, casa, "cebollas", "huevos", encima=True)
    assert p.receta_falta(casa, tortilla) == []
    j.hambre, j.sed, j.salud, j.animo = 90.0, 20.0, 40.0, 50.0
    reloj, dia = p.reloj, p.dia
    texto = p.cocinar(casa, tortilla, _Azar())
    # gasta una unidad de cada ingrediente: primero los de casa; los huevos que traías siguen contigo
    assert [x["id"] for x in p.despensa(casa) if not x.get("plato")] == [] and [x["id"] for x in j.encima] == ["huevos"]
    # tarda su tiempo del juego
    assert round((p.dia - dia) * 1440 + p.reloj - reloj) == 30
    # te comes una ración y las otras tres van a la nevera, y caducan
    platos = [x for x in p.despensa(casa) if x.get("plato")]
    assert len(platos) == 1 and platos[0]["n"] == 3 and platos[0]["cad"] == p.dia + 3 and platos[0]["nombre"] == "Tortilla de patatas"
    assert p.lote_info(platos[0])["sitio"] == "nevera" and p.lote_txt(platos[0]) == "Tortilla de patatas, 3 raciones, caduca en 3 días"
    assert "Tortilla de patatas: 4 raciones" in texto and "Te sirves un plato" in texto and "Guardas 3 raciones en la nevera" in texto
    assert any(f in texto for f in C.AJ.lista("frases_normal"))
    # los efectos de la ración: hambre, sed, salud y ánimo (el hambre ha subido un poco mientras cocinabas)
    assert 90.0 - 70.0 < j.hambre < 90.0 - 70.0 + 5 and j.salud == 70.0 and j.animo == 53.0 and j.sed < 20.0
    assert j.stats["platos_cocinados"] == 1 and j.cocina_practica == 5.0
    # comer otra ración de la nevera hace lo mismo
    j.hambre, j.salud = 80.0, 30.0
    assert "Te comes tortilla de patatas" in p.comer_lote(p.despensa(casa), platos[0])
    assert j.hambre == 10.0 and j.salud == 60.0 and platos[0]["n"] == 2
    # sin hambre y con la salud entera, no te la comes: no se desperdicia
    j.hambre, j.sed, j.salud = 0.0, 0.0, j.salud_max
    assert p.comer_lote(p.despensa(casa), platos[0]) is None and platos[0]["n"] == 2 and "no tienes hambre" in _ultimo(robot)
    # y si cocinas sin hambre, se guarda todo
    _dar(p, casa, "huevos", "patatas")
    texto = p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
    assert "lo guardas todo" in texto and sum(x["n"] for x in p.despensa(casa) if x.get("plato") == "huevos_patatas") == 2
    # si en la nevera no cabe, las raciones que sobran te las llevas; y si tampoco, se pierden
    _sin_azar(capacidad_nevera=5, capacidad_encima=3)
    j.encima = [{"id": "arroz", "n": 1, "cad": 0}]
    _dar(p, casa, "lentejas", "chorizo", "patatas", "cebollas")
    assert p.sitio_cabe(casa, "nevera") == 0                        # dos de tortilla, dos de huevos y el chorizo
    j.hambre = 90.0
    texto = p.cocinar(casa, _receta(p, "lentejas"), _Azar())      # cinco raciones: una te la comes, una cabe al gastar el chorizo, dos encima y una se pierde
    assert "Guardas 1 ración en la nevera" in texto and "te llevas 2 raciones encima" in texto and "No hay dónde guardar 1 ración" in texto
    assert sum(x["n"] for x in j.encima if x.get("plato")) == 2 and p.sitio_cabe(casa, "nevera") == 0


def test_a_veces_sale_de_categoria_o_se_quema_y_con_la_practica_mejora(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    j = p.j
    casa = p.lugares["casa_abuela"]
    tortilla = _receta(p, "tortilla")

    def cocina(receta=tortilla, azar=None):
        for x in list(p.despensa(casa)):
            p.despensa(casa).remove(x)
        _dar(p, casa, *receta["ingredientes"])
        j.hambre, j.salud, j.animo = 0.0, j.salud_max, 50.0         # sin hambre: todo va a la nevera, para mirarlo
        texto = p.cocinar(casa, receta, azar or _Azar(0.5))
        return texto, next(x for x in p.despensa(casa) if x.get("plato"))
    # quemado: alimenta menos y baja el ánimo
    _ajustar(prob_quemado=100, prob_especial=0, practica_especial=0, practica_quemado=0)
    texto, plato = cocina()
    assert any(f in texto for f in C.AJ.lista("frases_quemado")) and plato["nombre"] == "Tortilla de patatas, algo quemado"
    assert plato["hambre"] == 42.0 and plato["salud"] == 18.0 and plato["animo"] == 0.0
    # lo que no lleva fuego no se quema nunca
    texto, plato = cocina(_receta(p, "ensalada_mixta"))
    assert plato["nombre"] == "Ensalada mixta" and plato["hambre"] == 45.0
    # de categoría: alimenta más y anima más
    _ajustar(prob_quemado=0, prob_especial=100)
    texto, plato = cocina()
    assert any(f.replace("[o|a]", "o") in texto or f in texto for f in C.AJ.lista("frases_especial")) and plato["nombre"].endswith("de categoría")
    assert plato["hambre"] == 91.0 and plato["salud"] == 39.0 and plato["animo"] == 7.0 and j.stats["platos_especiales"] == 1
    # con la cocina equipada, el doble de salud
    j.muebles[casa.id] = ["cocina"]
    _ajustar(prob_quemado=0, prob_especial=0, practica_especial=0)
    assert cocina()[1]["salud"] == 60.0
    j.muebles[casa.id] = []
    # la práctica: cada plato suma, se guarda con la partida, sube de nivel y se dice
    j.cocina_practica = 5.0
    assert C.nivel_cocina(p) == 0
    texto, _ = cocina()
    assert j.cocina_practica == 10.0 and C.nivel_cocina(p) == 1 and "Tu mano en la cocina sube al nivel 1 de 10" in texto
    j.cocina_practica = 100.0
    cocina()
    assert j.cocina_practica == 100.0 and C.nivel_cocina(p) == 10
    # con práctica se quema menos: con la de serie, de 14 de cada 100 a 3,5; y sale de categoría más veces: de 12 a 27
    M.cargar_datos()

    def cuenta(practica, equipada=False):
        j.muebles[casa.id] = ["cocina"] if equipada else []
        rng = random.Random(7)
        quemados = especiales = 0
        for _ in range(400):
            j.cocina_practica = practica
            _, plato = cocina(azar=rng)
            quemados += plato["nombre"].endswith("quemado")
            especiales += plato["nombre"].endswith("categoría")
        return quemados, especiales
    q0, e0 = cuenta(0.0)
    q1, e1 = cuenta(100.0)
    q2, _ = cuenta(0.0, equipada=True)
    assert 30 < q0 < 85 and q1 < q0 / 2 and e1 > e0 * 1.5 and 25 < e0 < 75 and q2 < q0 * 0.75
    j.muebles[casa.id] = []


def test_cocinar_en_la_cocina_recorriendo_la_casa_con_sus_sonidos(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar()
    j = p.j
    casa = p.lugares["casa_abuela"]
    _dar(p, casa, "huevos", "patatas", "macarrones", "tomate_frito", "chorizo", "lechuga", "tomates", "cebollas", "atun")
    _a(p, casa, 2.0)
    menus_juego.lugar(p, casa)
    _elegir(robot, "Recorrer la casa por dentro")
    interior = robot.app.pila[-1]
    assert interior.habitaciones[interior.i][2] == "salir"         # se entra por la entrada: a la cocina hay que ir
    while interior.habitaciones[interior.i][2] != "cocina":
        robot.tecla(pygame.K_RIGHT)
    assert _ultimo(robot).startswith("La cocina.")
    robot.tecla(pygame.K_RETURN)
    cocina = robot.app.pila[-1]
    assert _texto(cocina.opciones[0]) == "Cocinar: puedes hacer 4 de 11 recetas"
    _elegir(robot, "Cocinar")
    recetas = robot.app.pila[-1]
    textos = [_texto(o) for o in recetas.opciones]
    # primero, las que se pueden hacer; de las demás se dice qué falta
    assert all("Tienes todo" in t for t in textos[:4]) and all("Te falta" in t for t in textos[4:11]) and len(textos) == 12
    assert _texto(_opcion(recetas, "Tortilla de patatas")) == "Tortilla de patatas: 4 raciones, 30 minutos. Tienes todo"
    assert _texto(_opcion(recetas, "Hamburguesas caseras")) == "Hamburguesas caseras: 3 raciones, 20 minutos. Te falta carne picada, barra de pan y queso, una cuña"
    assert "Lleva huevos, media docena y patatas, una malla" in _opcion(recetas, "Huevos fritos con patatas").ayuda and "a la sartén" in _opcion(recetas, "Huevos fritos").ayuda
    _elegir(robot, "Paella marinera")                              # una que no se puede: lo dice y no pasa nada
    assert robot.app.pila[-1] is recetas and "te falta" in _ultimo(robot)
    # a la sartén: se oye picar, freír y el plato en la mesa, por ese orden
    son = _oir(robot)
    j.hambre = 70.0
    _elegir(robot, "Huevos fritos con patatas")
    cocinando = robot.app.pila[-1]
    assert isinstance(cocinando, MC.Cocinando) and "Te pones a cocinar huevos fritos con patatas: 15 minutos" in _ultimo(robot)
    robot.frames(20)
    assert son == ["cocina_cortar"] and robot.app.pila[-1] is cocinando
    robot.tecla(pygame.K_a)
    assert "Estás cocinando" in _ultimo(robot)
    robot.frames(140)
    assert [s for s in son if s in ("cocina_cortar", "cocina_freir", "cocina_hervir", "plato_servido")] == ["cocina_cortar", "cocina_freir", "plato_servido"]
    assert "comer" in son and robot.app.pila[-1] is cocina          # de vuelta en el menú de la cocina
    assert "Huevos fritos con patatas: 2 raciones" in _ultimo(robot) and j.hambre < 15.0
    assert _texto(cocina.opciones[1]).startswith("Nevera: 4 de 14")   # la ración que sobra, con el chorizo, la lechuga y los tomates
    # a la olla, sin esperar: Intro lo acaba
    son.clear()
    j.hambre = 70.0
    _elegir(robot, "Cocinar")
    _elegir(robot, "Macarrones con chorizo")
    robot.frames(2)
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert "cocina_hervir" in son and "plato_servido" in son and robot.app.pila[-1] is cocina
    # sin fuego: solo se pica
    son.clear()
    j.hambre = 70.0
    _elegir(robot, "Cocinar")
    _elegir(robot, "Ensalada mixta")
    robot.frames(90)
    assert [s for s in son if s.startswith("cocina_") or s == "plato_servido"] == ["cocina_cortar", "plato_servido"]
    assert j.stats["platos_cocinados"] == 3


def test_sin_vida_realista_no_hay_obligacion_y_cocinar_sigue_valiendo(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    j = p.j
    casa = p.lugares["casa_abuela"]
    assert config.POR_DEFECTO["vida_realista"] is False and not p.vida_realista()
    for _ in range(3):
        p.pasar_horas(10)
    assert j.hambre == 0.0 and j.sed == 0.0                         # nada que atender
    # la cocina hace lo de siempre mientras no uses la despensa
    interior = sistemas.Interior(p, casa, {"descansar": lambda: None, "garaje": lambda: None})
    robot.app.abrir(interior)
    interior.i = next(k for k, h in enumerate(interior.habitaciones) if h[2] == "cocina")
    j.salud = 40.0
    robot.tecla(pygame.K_RETURN)
    assert j.salud == 65.0 and robot.app.pila[-1] is interior
    # cocinar da salud y ánimo aunque no haya hambre que quitar
    _dar(p, casa, "huevos", "patatas")
    j.salud, j.animo = 50.0, 50.0
    robot.tecla(pygame.K_RETURN)
    cocina = robot.app.pila[-1]
    assert not any(_texto(o).startswith("Beber agua") for o in cocina.opciones)       # la sed no existe
    texto = p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
    assert j.salud == 70.0 and j.animo == 53.0 and j.hambre == 0.0 and "Te sirves un plato" in texto
    # con la salud entera, un tentempié que no anima no se gasta; uno que anima, sí
    j.salud = j.salud_max
    lotes = [{"id": "sandwich", "n": 1, "cad": 0}, {"id": "chocolatina", "n": 1, "cad": 0}]
    assert p.comer_lote(lotes, lotes[0]) is None and "tu salud está al máximo" in _ultimo(robot)
    assert p.comer_lote(lotes, lotes[1]) and len(lotes) == 1


# ====================================================================== partidas guardadas
def test_la_despensa_se_guarda_con_la_partida_y_las_partidas_antiguas_cargan(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar()
    j = p.j
    casa = p.lugares["casa_abuela"]
    _dar(p, casa, "tomates", "arroz", "arroz")
    _dar(p, casa, "sandwich", encima=True)
    _dar(p, casa, "huevos", "patatas")
    j.hambre = 0.0
    j.salud = j.salud_max
    p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
    j.cocina_practica = 35.0
    d = json.loads(json.dumps(p.a_dict()))
    assert d["jugador"]["despensa"][casa.id] and d["jugador"]["encima"] == [{"id": "sandwich", "n": 1, "cad": p.dia + 3}]
    robot.app.empezar_partida(d)
    q = robot.p
    assert q is not p and q.j.cocina_practica == 35.0 and C.nivel_cocina(q) == 3
    casa2 = q.lugares["casa_abuela"]
    assert {x.get("id") or x.get("plato"): x["n"] for x in q.despensa(casa2)} == {"tomates": 1, "arroz": 2, "huevos_patatas": 2}
    assert q.lote_txt(next(x for x in q.despensa(casa2) if x.get("plato"))) == "Huevos fritos con patatas, 2 raciones, caduca mañana"
    assert [x["id"] for x in q.encima()] == ["sandwich"]
    q.j.hambre = 80.0
    assert q.comer_lote(q.despensa(casa2), next(x for x in q.despensa(casa2) if x.get("plato")))
    assert q.j.hambre == 18.0
    # una partida de antes de la 1.7.1, sin esos campos: carga, con la despensa vacía y sin práctica
    vieja = json.loads(json.dumps(d))
    for k in ("despensa", "encima", "cocina_practica"):
        del vieja["jugador"][k]
    for k in ("platos_cocinados", "compras", "comidas_caseras"):
        vieja["jugador"]["stats"].pop(k, None)
    robot.app.empezar_partida(vieja)
    v = robot.p
    assert v.j.despensa == {} and v.j.encima == [] and v.j.cocina_practica == 0.0 and not v.hay_cocina(v.lugares["casa_abuela"])
    assert v.encima_txt() == "No llevas comida ni compra encima." and v.cocina_txt(v.lugares["casa_abuela"]) == "Nevera: 0 de 14. Despensa: 0 de 30"
    _dar(v, v.lugares["casa_abuela"], "huevos", "patatas")
    v.j.salud = 50.0
    assert v.cocinar(v.lugares["casa_abuela"], _receta(v, "huevos_patatas"), _Azar()) and v.j.stats["platos_cocinados"] == 1
    # el formato de las partidas no ha subido
    from juego import partida
    assert partida.FORMATO == 3


# ====================================================================== en un servidor, a domicilio y en pareja
def test_conectado_a_un_servidor_funciona_igual(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar(robo_visto=100)
    j = p.j
    j.dinero = 100
    casa = p.lugares["casa_abuela"]
    l = p.lugares["tienda_paco"]
    enviados = []
    p.en_servidor = True
    p.sv_delito = lambda puntos: enviados.append(puntos)
    try:
        assert p.tipo_tienda(l)["id"] == "ultramarinos"
        menu, t = _entrar_en_tienda(robot, p, l)
        _coger(robot, t, "lacteos", "huevos")
        _coger(robot, t, "fruteria", "patatas")
        total = t.total()
        _ir(robot, t, "caja")
        robot.tecla(pygame.K_RETURN)
        _elegir(robot, "Pagar")
        assert j.dinero == 100 - total and p._total(j.encima) == 2
        _cerrar_menus(robot)
        assert p.guardar_compra(casa) == (2, 0)
        # cocinar: gasta, alimenta y guarda; el reloj del servidor es de todos y no se adelanta
        j.hambre = 80.0
        reloj, dia = p.reloj, p.dia
        texto = p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
        assert texto and (p.reloj, p.dia) == (reloj, dia) and j.hambre < 25.0
        assert sum(x["n"] for x in p.despensa(casa) if x.get("plato")) == 1
        # la caducidad va con el día del servidor
        p.dia += 5
        assert p.tirar_caducado(p.despensa(casa)) == ["huevos fritos con patatas"]
        # el hurto cuenta en el servidor como cualquier delito
        menu, t = _entrar_en_tienda(robot, p, l)
        _coger(robot, t, "bebidas", "zumo")
        robot.tecla(pygame.K_ESCAPE)
        _elegir(robot, "Salir sin pagar")
        assert enviados and [x["id"] for x in j.encima] == ["zumo"]
        # lo que se guarda en el servidor es el jugador entero: la despensa va dentro
        d = json.loads(json.dumps(p.a_dict()))
        assert "despensa" in d["jugador"] and d["jugador"]["encima"][0]["id"] == "zumo"
    finally:
        p.en_servidor = False


def test_convive_con_la_comida_a_domicilio(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    _sin_azar()
    j = p.j
    j.dinero = 200
    casa = p.lugares["casa_abuela"]
    _dar(p, casa, "huevos", "patatas", "arroz")
    _a(p, casa, 3.0)
    menus_juego.lugar(p, casa)
    menu = robot.app.pila[-1]
    textos = [_texto(o) for o in menu.opciones]
    assert any(t.startswith("Pedir comida a domicilio") for t in textos) and "Cocina. Nevera: 1 de 14. Despensa: 2 de 30" in textos
    _cerrar_menus(robot)
    # el pedido llega y te lo tomas: no pasa por la despensa ni por la bolsa
    j.hambre = 90.0
    antes = json.dumps(j.despensa, sort_keys=True)
    assert p.pedir_domicilio([DO.carta(p)[0]])
    j.pedido["llega"] = p._ahora() - 0.1
    robot.frames(3)
    assert j.pedido is None and abs(j.hambre - 50.0) < 0.1 and json.dumps(j.despensa, sort_keys=True) == antes and j.encima == []
    # y después se puede cocinar con lo que había
    j.hambre = 90.0
    assert p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar()) and j.hambre < 35.0
    # cocinar alimenta más que el bocadillo que traen, y la ración sale mucho más barata
    bocadillo = DO.carta(p)[0]
    receta = _receta(p, "huevos_patatas")
    coste = sum(p.producto(i)["precio"] for i in receta["ingredientes"])
    assert receta["hambre"] > bocadillo["hambre"] and coste / receta["raciones"] < bocadillo["precio"] / 2


def test_si_tu_pareja_vive_contigo_cocinar_cuenta_para_ella(robot, datos_de_serie):
    p = _empezar(robot, adultos=True, vida_realista=True, pareja_convive=True)
    _sin_azar()
    try:
        j = p.j
        casa = p.lugares["casa_abuela"]
        pers = p.persona_social("lucia")
        r = p.relacion("lucia")
        r.update(estado="pareja", afinidad=60, citas=5, ultimo=p.dia)
        j.pareja = j.convive = "lucia"
        j.convive_casa, j.convive_desde = casa.id, p.dia
        p.reloj = 21 * 60.0                                        # de noche está en casa
        assert p.pareja_en_casa()
        _dar(p, casa, "huevos", "patatas", "huevos", "patatas", "huevos", "patatas")
        j.hambre = 90.0
        texto = p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
        # come contigo: de las dos raciones no sobra ninguna, se dice y sube la afinidad
        assert any(f.replace("{n}", pers["nombre"]) in texto for f in C.AJ.lista("frases_pareja"))
        assert r["afinidad"] == 62 and not [x for x in p.despensa(casa) if x.get("plato")] and j.convive_hoy["cocinado"] == p.dia
        # una vez al día
        j.hambre = 90.0
        p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
        assert r["afinidad"] == 62
        # en otra casa, o si no está, cocinas para ti
        j.convive_casa = "otra"
        j.hambre = 90.0
        texto = p.cocinar(casa, _receta(p, "huevos_patatas"), _Azar())
        assert not any(f.replace("{n}", pers["nombre"]) in texto for f in C.AJ.lista("frases_pareja")) and sum(x["n"] for x in p.despensa(casa) if x.get("plato")) == 1
    finally:
        robot.app.cfg["adultos"] = False
        robot.app.cfg["pareja_convive"] = False
        robot.app.aplicar_adultos()


# ====================================================================== mods, editor, sonidos y documentación
def test_un_mod_anade_productos_pasillos_y_recetas(robot, datos_de_serie):
    p = _empezar(robot)
    _sin_azar()
    casa = p.lugares["casa_abuela"]
    p.datos["pasillos"] = list(p.datos["pasillos"]) + [{"id": "mod_congelados", "nombre": "los congelados", "desc": "Arcones que echan frío."}]
    p.datos["productos"] = list(p.datos["productos"]) + [{"id": "mod_croquetas", "nombre": "Croquetas congeladas", "pasillo": "mod_congelados", "precio": 3, "sitio": "nevera", "caduca": 30}]
    p.datos["tipos_tienda"] = [dict(t, pasillos=t["pasillos"] + ["mod_congelados"]) if t["id"] == "ultramarinos" else t for t in p.datos["tipos_tienda"]]
    p.datos["recetas"] = list(p.datos["recetas"]) + [{"id": "mod_croquetas_fritas", "nombre": "Croquetas con huevo", "ingredientes": ["mod_croquetas", "huevos"], "minutos": 10, "raciones": 2,
                                                      "hambre": 60, "sed": 0, "salud": 20, "animo": 2, "caduca": 1, "fuego": "freir"}]
    l = p.lugares["tienda_paco"]
    assert [pa["id"] for pa, _ in p.surtido(l)][-1] == "mod_congelados"
    p.j.dinero = 50
    menu, t = _entrar_en_tienda(robot, p, l)
    assert ("pasillo", "mod_congelados") in [h[2] for h in t.habitaciones]
    _coger(robot, t, "mod_congelados", "mod_croquetas")
    _coger(robot, t, "lacteos", "huevos")
    _ir(robot, t, "caja")
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Pagar")
    _cerrar_menus(robot)
    assert p.guardar_compra(casa) == (2, 0) and "croquetas con huevo" in p.producto_ayuda(p.producto("mod_croquetas"))
    p.j.salud = 50.0
    texto = p.cocinar(casa, _receta(p, "mod_croquetas_fritas"), _Azar())
    assert "Croquetas con huevo: 2 raciones" in texto and p.j.salud == 70.0


def test_el_editor_edita_todo_lo_nuevo(datos_de_serie):
    from editor import modelo
    from editor.esquema import ESQUEMAS, SECCIONES
    titulos = {clave: (titulo, esq) for clave, titulo, esq in SECCIONES}
    for clave in ("productos", "pasillos", "tipos_tienda", "recetas", "cocina"):
        assert clave in titulos and titulos[clave][1] in ESQUEMAS and clave in M.SECCIONES_VIDA, clave
    campos = {esq: {c["k"] for c in ESQUEMAS[esq]["campos"]} for esq in ESQUEMAS}
    assert campos["ajuste_cocina"] == set(C.AJ._n) | set(C.AJ._l) | {"id"}, campos["ajuste_cocina"] ^ (set(C.AJ._n) | set(C.AJ._l) | {"id"})
    assert {k for x in C.PRODUCTOS for k in x} <= campos["producto"] and {k for x in C.RECETAS for k in x} <= campos["receta"]
    assert {k for x in C.TIPOS_TIENDA for k in x} <= campos["tipo_tienda"] and {k for x in C.PASILLOS for k in x} <= campos["pasillo"] and "surtido" in campos["lugar"]
    assert set(dict(next(c for c in ESQUEMAS["receta"]["campos"] if c["k"] == "fuego")["ops"])) == set(C.FUEGOS)
    # los valores de serie que enseña el editor son los del juego
    for cp in ESQUEMAS["ajuste_cocina"]["campos"]:
        if cp["k"] in C.AJ._n:
            assert cp.get("defecto") == C.AJ._n[cp["k"]], cp["k"]
    cat = modelo.Catalogo()
    assert ("tomates", "Tomates, un kilo") in cat.opciones("producto") and ("fruteria", "la frutería") in cat.opciones("pasillo") and len(cat.opciones("tipo_tienda")) == len(C.TIPOS_TIENDA)
    # un mod con un pasillo, un producto, una receta y una tienda propios pasa la comprobación
    mod = modelo.Mod()
    mod.info = {"nombre": "Prueba", "autor": "Yo"}
    mod.secciones["pasillos"].append({"id": "mod_congelados", "nombre": "los congelados", "desc": "Arcones."})
    mod.secciones["productos"].append({"id": "mod_croquetas", "nombre": "Croquetas congeladas", "pasillo": "mod_congelados", "precio": 3, "sitio": "nevera", "caduca": 30})
    mod.secciones["recetas"].append({"id": "mod_croquetas_fritas", "nombre": "Croquetas con huevo", "ingredientes": ["mod_croquetas", "huevos"], "minutos": 10, "raciones": 2,
                                     "hambre": 60, "salud": 20, "fuego": "freir"})
    mod.secciones["tipos_tienda"].append({"id": "mod_congelados_tienda", "nombre": "Tienda de congelados", "pasillos": ["mod_congelados"], "palabras": ["congelados"], "recargo": 95})
    mod.secciones["lugares"].append({"id": "mod_frio", "nombre": "La Sirena Fría", "tipo": "tienda", "mapa": "puerto_bravo", "bloque": [2, 3], "lado": "N", "pos": 20, "desc": "Congelados.",
                                     "surtido": "mod_congelados_tienda"})
    errores, avisos = modelo.comprobar(mod, cat)
    assert not errores, errores
    # y una receta con un ingrediente que no existe, no
    mod.secciones["recetas"].append({"id": "mod_mala", "nombre": "Mala", "ingredientes": ["no_existe"], "minutos": 10, "raciones": 2, "fuego": "freir"})
    errores, _ = modelo.comprobar(mod, cat)
    assert errores


def test_los_sonidos_nuevos_estan_en_todos_los_packs_y_en_la_guia():
    from juego import catalogo_sonidos
    assert sintesis.VERSION_CACHE >= 20
    S = sintesis.generar()
    nuevos = ("cesta", "nevera", "cocina_cortar", "cocina_freir", "cocina_hervir", "plato_servido")
    assert len(S) >= 263
    for n in nuevos:
        assert n in S and 0.3 < len(S[n]) / sintesis.SR < 3.0 and not sintesis.es_bucle(n)
        assert catalogo_sonidos.describir(n) != "Sonido del juego." and catalogo_sonidos.titulo_de(n) == ("Tiendas, dinero y objetos" if n == "cesta" else "Casa, cocina y comida")
        for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
            carpeta = os.path.join(rutas.PACKS, pack)
            assert os.path.isdir(carpeta) and any(os.path.exists(os.path.join(carpeta, n + e)) for e in rutas.EXT_AUDIO), (pack, n)
    guia = open(os.path.join(rutas.DATA, "docs", "cambiar_sonidos.html"), encoding="utf-8").read()
    assert all(n in guia for n in nuevos) and "Casa, cocina y comida" in guia


def test_el_manual_las_teclas_y_la_guia_del_editor_cuentan_lo_nuevo():
    from juego import ayuda
    manual = open(os.path.join(rutas.DATA, "docs", "manual.html"), encoding="utf-8").read()
    for frase in ("Comprar paseando por la tienda", "La despensa y la nevera", "Cocinar en casa", "Salir sin pagar", "caduca", "mano en la cocina", "Tortilla de patatas"):
        assert frase in manual, frase
    assert ".json" not in manual and ".py" not in manual             # el manual es para quien juega: nada de programación
    editor = open(os.path.join(rutas.DATA, "docs", "editor_mods.html"), encoding="utf-8").read()
    for frase in ("Productos de las tiendas de comida", "Recetas de cocina", "Tipos de tienda de comida", "Pasillos de las tiendas"):
        assert frase in editor, frase
    teclas = open(os.path.join(rutas.DATA, "docs", "teclas.html"), encoding="utf-8").read()
    assert "qué llevas en la cesta" in teclas and "Recorriendo una casa" in teclas
    assert any("cesta" in d for _, d in ayuda.TECLAS_RECORRIDO)
    # la opción de la vida realista cuenta que se puede cocinar
    assert "cocinar" in open(os.path.join(rutas.base(), "juego", "menus_juego.py"), encoding="utf-8").read().split('si_no("vida_realista"')[1][:900]
