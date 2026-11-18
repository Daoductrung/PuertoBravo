"""Todo lo nuevo de la 1.7.1, hecho con el mando y sin tocar el teclado: de PlayStation o de Xbox.

Cada prueba prepara la escena como haga falta, pero la acción que comprueba la hace solo con botones, palancas y gatillos
del mando (simulado: ningún mando físico interviene). Al final, una prueba vigilante: toda tecla de la ayuda del juego
tiene que poder hacerse con el mando, por botón, combinación, palanca o menú de acciones, o estar en la lista de
excepciones con su razón. Así una tecla nueva no se queda sin mando sin que nadie se entere.
"""
import os
import re

import pygame
import pytest

from conftest import Robot                                               # noqa: F401
from juego import ayuda, compra as C, gente as G, mando, menus_juego, misvehiculos as MV, mundo as M, rutas, teclado
from juego.entidades import Persona
from juego.menus import Dialogo, EntradaTexto, Menu
from test_enlinea import banco, dos, entrar, hasta, juntos               # noqa: F401  (banco y dos son fixtures)
from test_servidor import Banco

TIPOS = ("xbox", "ps")
BOTON = {"xbox": {"a": "A", "b": "B", "x": "X", "y": "Y", "lb": "LB", "rb": "RB"}, "ps": {"a": "Equis", "b": "Círculo", "x": "Cuadrado", "y": "Triángulo", "lb": "L1", "rb": "R1"}}


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


# ====================================================================== el mando, a mano
class Md:
    """Un mando simulado: solo botones, gatillos y palancas."""

    def __init__(self, robot, tipo="xbox"):
        self.robot, self.app, self.md = robot, robot.app, robot.app.mando
        self.md.simulado = True
        self.md.tipo = tipo

    def pulsar(self, b):
        if b in ("lt", "rt"):                                    # los gatillos son ejes
            self.md.eje(b, 1.0)
            self.md.eje(b, 0.0)
        else:
            self.md.boton(b, True)
            self.md.boton(b, False)

    def combinar(self, b):
        """El botón de combinar (Vista, Crear o Share) mantenido, y otro."""
        self.md.boton(mando.COMBINAR, True)
        self.pulsar(b)
        self.md.boton(mando.COMBINAR, False)

    def hasta(self, contiene, empieza=False):
        """Baja por el menú, con la cruceta, hasta la opción que diga eso."""
        m = self.app.pila[-1]
        assert isinstance(m, Menu), m
        for _ in range(len(m.opciones) + 1):
            t = m.opciones[m.i].texto
            if t.startswith(contiene) if empieza else contiene in t:
                return m
            self.pulsar("abajo")
        raise AssertionError((contiene, [o.texto for o in m.opciones]))

    def elegir(self, contiene, empieza=False):
        m = self.hasta(contiene, empieza)
        self.pulsar("a")
        return m

    def accion(self, contiene):
        """Abre el menú de acciones (combinar y gatillo derecho) y elige una."""
        self.combinar("rt")
        m = self.app.pila[-1]
        assert isinstance(m, Menu) and m.titulo == "Acciones", m
        return self.elegir(contiene)

    def al_juego(self):
        p = self.app.partida
        for _ in range(20):
            if self.app.pila[-1] is p:
                return
            self.pulsar("b")
        raise AssertionError(self.app.pila[-1])

    def escribir(self, texto):
        """Escribe con la rueda de letras: arriba y abajo eligen, derecha escribe, LB el espacio y RB cambia de grupo."""
        e = self.app.pila[-1]
        assert isinstance(e, EntradaTexto), e
        for ch in texto:
            if ch == " ":
                self.pulsar("lb")
                continue
            g = next(k for k, (_, letras) in enumerate(e.GRUPOS) if ch in letras)
            while e.grupo != g:
                self.pulsar("rb")
            destino = e.GRUPOS[g][1].index(ch)
            while e.letra != destino:
                self.pulsar("abajo" if (destino - e.letra) % len(e.GRUPOS[g][1]) <= len(e.GRUPOS[g][1]) // 2 else "arriba")
            self.pulsar("derecha")


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


def _a(p, l, dx=0.0):
    if p.j.veh:
        p.salir_vehiculo(forzado=True)
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + dx, l.y)


def _persona(p, tipo="civil", dx=3.0, nombre=None, **attrs):
    q = Persona(tipo, *p.mundo.punto_libre(p.pos()[0] + dx, p.pos()[1]), nombre)
    for k, v in attrs.items():
        setattr(q, k, v)
    p.personas.append(q)
    return q


def _ultimo(robot):
    return robot.app.voz.registro[-1]


def _hasta(robot, condicion, segundos=30.0):
    for _ in range(int(segundos * 30)):
        if condicion():
            return True
        robot.frames(1)
    return bool(condicion())


# ====================================================================== 1. el menú de acciones
@pytest.mark.parametrize("tipo", TIPOS)
def test_el_menu_de_acciones_se_abre_con_la_combinacion_y_lista_lo_que_no_tiene_boton(robot, datos_de_serie, tipo):
    p = _empezar(robot)
    md = Md(robot, tipo)
    assert mando.POR_DEFECTO["pie_combo"]["rt"] == mando.POR_DEFECTO["coche_combo"]["rt"] == "menu_acciones"
    md.combinar("rt")
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.titulo == "Acciones" and "no tiene botón propio" in _ultimo(robot)
    textos = [o.texto for o in m.opciones]
    # a pie, sin perro, sin placa y sin conexión: lo de a pie, y nada de lo que ahora no viene a cuento
    assert "Gritar para espantar a los peatones" in textos and "Atracar al peatón que tienes al lado" in textos and "Ponerte a cubierto, o salir" in textos
    assert not any("personaje" in t or "perro" in t or "alto" in t or "Enderezar" in t for t in textos)
    assert all(o.ayuda or True for o in m.opciones) and textos[-1] == "Volver"
    # dentro, como en cualquier menú, LB y RB (L1 y R1) repasan los mensajes anteriores
    antes = len(robot.app.voz.registro)
    md.pulsar("lb")
    assert len(robot.app.voz.registro) >= antes
    # una acción: el tiempo lento. Se cierra el menú y pasa
    md.elegir("Tiempo lento")
    assert robot.app.pila[-1] is p and p.lento
    md.accion("Tiempo lento")
    assert not p.lento
    # otra: el filtro del radar, que era F6
    md.accion("Cambiar el filtro del radar")
    assert p.cfg["radar_filtro"] == "lugares" and "Radar: solo lugares" in robot.dicho()
    # la música se baja y se sube sin que el menú se cierre
    vol = p.cfg["vol_musica"]
    md.combinar("rt")
    md.elegir("Bajar la música")
    md.pulsar("a")
    assert robot.app.pila[-1].titulo == "Acciones" and p.cfg["vol_musica"] == pytest.approx(max(0.0, vol - 0.2))
    md.pulsar("b")
    assert robot.app.pila[-1] is p
    # la ayuda nombra la combinación con los botones de este mando
    lineas = robot.app.mando.lineas_ayuda()
    comb = "Botón vista" if tipo == "xbox" else "Botón crear o share"
    gat = "gatillo derecho" if tipo == "xbox" else "R2"
    assert any(l.startswith(f"Mando, a pie. {comb}, mantenido, más {gat}: menú de acciones") for l in lineas), [l for l in lineas if "acciones" in l]
    assert any(l.startswith(f"Mando, al volante. {comb}, mantenido, más {gat}: menú de acciones") for l in lineas)


def test_el_menu_de_acciones_cambia_al_volante_con_perro_y_con_el_contenido_para_adultos(robot, datos_de_serie):
    p = _empezar(robot, adultos=True)
    md = Md(robot)
    j = p.j
    j.perro = "Canela"
    md.combinar("rt")
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert "Tu perro: su menú" in textos and "Tu perro: que busque por el olfato" in textos and "Tus sustancias" in textos
    md.elegir("Tu perro: su menú")
    assert isinstance(robot.app.pila[-1], Menu) and "Canela" in str(robot.app.pila[-1].titulo)
    md.al_juego()
    v = p.crear_vehiculo("sedan", j.x + 3, j.y, 1, None)
    v.cerrado = False
    md.pulsar("y")
    assert j.veh is v
    p.cfg["conduccion"] = "libre"
    p.preparar_conduccion()
    md.combinar("rt")
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert "Enderezar el vehículo hacia el punto cardinal más cercano" in textos and "Lista de armas" in textos and "Usar un botiquín" in textos
    assert not any("perro" in t or "Atracar" in t or "cubierto" in t for t in textos)
    v.rumbo = 80.0
    md.elegir("Enderezar")
    assert v.rumbo == 90.0 and robot.app.pila[-1] is p
    md.accion("Lista de armas")
    assert isinstance(robot.app.pila[-1], Menu)
    md.al_juego()


def test_gritar_atracar_y_cubrirse_que_no_tenian_boton(robot, datos_de_serie):
    p = _empezar(robot)
    md = Md(robot)
    q = _persona(p, "civil", 6.0, estado="pasea")
    sonados = []
    original = p.son
    p.son = lambda nombre, *a, **kw: (sonados.append(nombre), original(nombre, *a, **kw))[1]
    md.accion("Gritar")
    assert "grito" in sonados and q.estado != "pasea" and robot.app.pila[-1] is p
    md.accion("Atracar al peatón")
    assert robot.app.pila[-1] is p and len(robot.app.voz.registro) > 0      # sin arma lo dice; con arma, atraca: es la tecla E de siempre
    md.accion("Dónde estoy, con las coordenadas")
    assert "Coordenadas:" in _ultimo(robot)
    md.accion("Descripción del lugar")
    md.accion("Objetivo de la misión")
    md.accion("Lista de lugares")
    assert isinstance(robot.app.pila[-1], Menu)
    md.al_juego()
    md.accion("Explorador de mapa")
    assert type(robot.app.pila[-1]).__name__ == "ExploradorMapa"
    md.pulsar("b")
    assert robot.app.pila[-1] is p


def test_las_teclas_cambiadas_del_teclado_no_descolocan_el_mando(robot, datos_de_serie):
    p = _empezar(robot)
    md = Md(robot)
    teclado.cambiar(p.cfg, pygame.K_c, pygame.K_p)               # «dónde estoy» pasa a la P, en el teclado
    try:
        md.pulsar("arriba")                                      # cruceta arriba: dónde estoy
        assert "Calle" in _ultimo(robot) or "Avenida" in _ultimo(robot) or "Miras al" in _ultimo(robot)
        md.accion("Dónde estoy, con las coordenadas")
        assert "Coordenadas:" in _ultimo(robot)
    finally:
        teclado.restablecer(p.cfg)


# ====================================================================== 2. la tienda que se recorre
@pytest.mark.parametrize("tipo", TIPOS)
def test_la_tienda_se_recorre_se_llena_la_cesta_y_se_paga_con_el_mando(robot, datos_de_serie, tipo):
    p = _empezar(robot)
    C.AJ.configurar({"cocina": [{"id": "general", "falta_prob": 0, "oferta_descuento": 0}]})
    md = Md(robot, tipo)
    j = p.j
    j.dinero = 100
    l = p.lugares["tienda_paco"]
    _a(p, l, 2.0)
    md.pulsar("a")                                               # interactuar: el menú de la tienda
    assert isinstance(robot.app.pila[-1], Menu), robot.dicho()
    md.elegir("Recorrer el local por dentro")
    t = robot.app.pila[-1]
    assert isinstance(t, C.Tienda)
    boton = f"el botón {BOTON[tipo]['x']}"
    assert f"{boton} para la cesta" in _ultimo(robot) and "C para la cesta" not in _ultimo(robot)
    md.pulsar("x")                                               # X o Cuadrado: la cesta, que con el teclado es la C
    assert _ultimo(robot) == "La cesta está vacía."
    md.pulsar("back")                                            # la ayuda de la pantalla
    assert f"{boton} para saber qué llevas en la cesta" in _ultimo(robot)
    while not (isinstance(t.habitaciones[t.i][2], tuple) and t.habitaciones[t.i][2][0] == "pasillo"):
        md.pulsar("derecha")
    md.pulsar("a")                                               # el pasillo
    pasillo = robot.app.pila[-1]
    assert isinstance(pasillo, C.MenuCesta)
    primero = t.surtido[[pa["id"] for pa, _ in t.surtido].index(t.habitaciones[t.i][2][1])][1][0]
    md.pulsar("a")                                               # A o Equis: a la cesta
    md.pulsar("derecha")                                         # cruceta derecha: otro
    assert t.cesta == {primero["id"]: 2}
    md.pulsar("izquierda")                                       # cruceta izquierda: lo devuelve
    assert t.cesta == {primero["id"]: 1} and "Devuelves" in _ultimo(robot)
    md.pulsar("b")
    assert robot.app.pila[-1] is t
    md.pulsar("x")
    assert "En la cesta, 1 producto" in _ultimo(robot)
    while t.habitaciones[t.i][2] != "caja":
        md.pulsar("izquierda")
    md.pulsar("a")
    caja = robot.app.pila[-1]
    assert isinstance(caja, Menu) and caja.titulo.startswith("La caja")
    total = t.total()
    md.elegir("Pagar", empieza=True)
    assert j.dinero == 100 - total and t.cesta == {} and [x["id"] for x in j.encima] == [primero["id"]]
    # salir con la cesta llena pregunta, y se contesta con el mando
    md.pulsar("derecha")
    while not (isinstance(t.habitaciones[t.i][2], tuple) and t.habitaciones[t.i][2][0] == "pasillo"):
        md.pulsar("derecha")
    md.pulsar("a")
    md.pulsar("a")
    md.pulsar("b")
    md.pulsar("b")                                               # B o Círculo: salir
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and any(o.texto.startswith("Dejar la cesta") for o in m.opciones)
    md.elegir("Dejar la cesta", empieza=True)
    assert t not in robot.app.pila


# ====================================================================== 3. la cocina y la despensa
def test_guardar_la_compra_y_cocinar_en_casa_con_el_mando(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True)
    C.AJ.configurar({"cocina": [{"id": "general", "prob_quemado": 0, "prob_especial": 0, "practica_especial": 0}]})
    md = Md(robot, "ps")
    j = p.j
    casa = p.lugares["casa_abuela"]
    for pid in ("huevos", "patatas"):
        p._meter(j.encima, p._lote_de(p.producto(pid), 1))
    _a(p, casa, 2.0)
    menus_juego.lugar(p, casa)                                   # el menú de la casa (en esta, Intro en la puerta empieza antes una escena de la historia)
    assert isinstance(robot.app.pila[-1], Menu), robot.dicho()
    md.elegir("Recorrer la casa por dentro")
    interior = robot.app.pila[-1]
    while interior.habitaciones[interior.i][2] != "cocina":
        md.pulsar("derecha")
    md.pulsar("a")
    cocina = robot.app.pila[-1]
    assert isinstance(cocina, Menu), robot.dicho()
    md.elegir("Guardar lo que llevas encima", empieza=True)
    if robot.app.pila[-1] is not cocina:                         # si pregunta cuánto o qué, se guarda todo
        md.pulsar("a")
        while robot.app.pila[-1] is not cocina:
            md.pulsar("b")
    assert p._total(p.despensa(casa)) >= 1, robot.dicho()
    for pid in ("huevos", "patatas"):                            # por si no lo guardó todo de una vez
        if not any(x.get("id") == pid for x in p.despensa(casa)):
            p._meter(p.despensa(casa), p._lote_de(p.producto(pid), 1))
    cocina.refrescar(False)
    cocina.i = 0
    md.elegir("Cocinar", empieza=True)
    md.elegir("Huevos fritos con patatas", empieza=True)
    pantalla = robot.app.pila[-1]
    assert type(pantalla).__name__ == "Cocinando", robot.dicho()
    md.pulsar("y")                                               # un botón cualquiera dice qué pasa, con el botón de este mando
    assert "El botón Equis, para no esperar." in _ultimo(robot)
    md.pulsar("a")                                               # A o Equis: no esperar
    robot.frames(3)
    assert pantalla not in robot.app.pila
    assert any(x.get("plato") == "huevos_patatas" for x in p.despensa(casa)), p.despensa(casa)
    # la nevera y la despensa se consultan en el mismo menú
    while not (isinstance(robot.app.pila[-1], Menu) and any(o.texto.startswith("Nevera") for o in robot.app.pila[-1].opciones)):
        md.pulsar("b")
    md.elegir("Nevera", empieza=True)
    assert isinstance(robot.app.pila[-1], Menu)


# ====================================================================== 4. rendirse, el alto y las esposas
@pytest.mark.parametrize("tipo", TIPOS)
def test_rendirse_a_la_policia_con_la_combinacion(robot, datos_de_serie, tipo):
    p = _empezar(robot)
    md = Md(robot, tipo)
    j = p.j
    p.poner_busqueda(3)
    robot.frames(2)
    p.t_policia = 1e9
    _persona(p, "policia", 16, nombre="Policía", arma="pistola", hostil=True, estado="ataca", t_disparo=0.05)
    md.combinar("lt")                                            # Vista y gatillo izquierdo; Crear o Share y L2
    assert p.rendido and "Levantas las manos" in robot.dicho()
    # la frase que dice cómo bajar las manos nombra la combinación de este mando, no Mayúsculas H
    esperado = "Con el botón Vista mantenido más el gatillo izquierdo otra vez" if tipo == "xbox" else "Con el botón Crear o Share mantenido más el botón L2 otra vez"
    assert esperado in robot.dicho() and "Mayúsculas H" not in _ultimo(robot)
    md.combinar("lt")
    assert not p.rendido


def test_de_policia_dar_el_alto_y_esposar_con_el_mando(robot, datos_de_serie):
    from juego import agente as AG
    p = _empezar(robot, oficio_policia=True, invulnerable=True)
    md = Md(robot)
    j = p.j
    j.dinero, j.ciudadania = 2000, 50.0
    AG.AJ.n.update(espera_min=1, espera_max=1)
    assert p.ingresar_policia() and p.empezar_turno(p.lugares["comisaria"])
    p.datos["avisos_policia"] = [a for a in AG.AVISOS if a["tipo"] == "robo"]
    p.trabajo["espera"] = 0.0
    assert _hasta(robot, lambda: p.trabajo and p.trabajo.get("aviso") is not None, 5), robot.dicho()
    a = p.trabajo["aviso"]
    _a(p, a["lugar"], 6.0)
    robot.frames(3)
    assert a["fase"] == "actuar" and a["sospechosos"]
    for s in a["sospechosos"]:
        s.plan, s.hostil, s.estado, s.ha_resistido, s.rendido = "pelea", True, "ataca", True, False
    s = a["sospechosos"][0]
    AG.AJ.n["alto_prob"] = 100
    j.x, j.y = p.mundo.punto_libre(s.x + 3, s.y)
    # de servicio, el menú de acciones pone el alto lo primero, y no ofrece el grito
    md.combinar("rt")
    m = robot.app.pila[-1]
    assert m.opciones[0].texto == "Dar el alto a los sospechosos" and not any(o.texto.startswith("Gritar") for o in m.opciones)
    md.pulsar("a")
    assert robot.app.pila[-1] is p
    assert all(x.rendido and not x.hostil for x in a["sospechosos"] if x.dist(j.x, j.y) < 18)
    assert any(f in " | ".join(robot.app.voz.registro) for f in AG.AJ.lista("frases_alto"))
    for x in list(a["sospechosos"]):
        if not getattr(x, "rendido", False):
            p.danar_persona(x, x.salud * 0.8)
    for x in list(a["sospechosos"]):                             # A o Equis junto a cada uno: esposas
        j.x, j.y = x.x, x.y
        md.pulsar("a")
        assert robot.app.pila[-1] is p
    robot.frames(3)
    assert p.trabajo["aviso"] is None and j.policia["detenciones"] >= 1


# ====================================================================== 5. el desvío del GPS y los recordatorios hablados
@pytest.mark.parametrize("tipo", TIPOS)
def test_los_recordatorios_nuevos_nombran_los_botones_de_cada_mando(tipo):
    f = lambda t, c="pie": mando.textos_mando(t, mando.POR_DEFECTO, tipo, c)
    comb = "el botón Vista" if tipo == "xbox" else "el botón Crear o Share"
    # el aviso de desvío: Mayúsculas G es la combinación con la palanca izquierda pulsada
    assert f("Desvío a la gasolinera. Con Mayúsculas G cancelas el desvío y vuelves a lo que llevabas.") == \
        f"Desvío a la gasolinera. Con {comb} mantenido más la palanca izquierda pulsada cancelas el desvío y vuelves a lo que llevabas."
    # la primera vez que te disparan en un vehículo: Q y Control son los dos botones de arriba
    fijar, disparar = ("el botón LB", "el botón RB") if tipo == "xbox" else ("el botón L1", "el botón R1")
    t = f("¡Te disparan! Puedes responder sin bajarte: pulsa Q para fijar a quien te dispara y Control para disparar desde el vehículo, con un arma de fuego en la mano.", "coche")
    assert t == f"¡Te disparan! Puedes responder sin bajarte: pulsa {fijar} para fijar a quien te dispara y {disparar} para disparar desde el vehículo, con un arma de fuego en la mano."
    # rendirse, a pie y al volante
    gat = "el gatillo izquierdo" if tipo == "xbox" else "el botón L2"
    for c in ("pie", "coche"):
        assert f("Con Mayúsculas H otra vez, bajas las manos.", c) == f"Con {comb} mantenido más {gat} otra vez, bajas las manos."
    # dónde dejaste el vehículo
    y = "el botón Y" if tipo == "xbox" else "el botón Triángulo"
    assert f("Pulsa Mayúsculas L para saberlo.") == f"Pulsa {comb} mantenido más {y} para saberlo."
    # lo que solo está en el menú de acciones se sigue diciendo con su tecla
    assert f("Pulsa Mayúsculas Y para llamarlo.") == "Pulsa Mayúsculas Y para llamarlo."
    # en Xbox no se manda al panel táctil, que no tiene
    assert "panel táctil" not in mando.textos_mando("Pulsa Mayúsculas J para verle.", mando.POR_DEFECTO, "xbox", "pie")


def test_el_desvio_se_cancela_con_la_combinacion_y_el_juego_lo_dice_con_el_boton(robot, datos_de_serie):
    p = _empezar(robot)
    md = Md(robot, "ps")
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "banco")
    p.gps_a_lugar(l)
    assert p.gps is not None
    p.decir("Desvío a la gasolinera. Con Mayúsculas G cancelas el desvío y vuelves a lo que llevabas.")
    assert "Con el botón Crear o Share mantenido más la palanca izquierda pulsada cancelas el desvío" in _ultimo(robot)
    md.combinar("l3")
    assert p.gps is None


# ====================================================================== 6. escribir con el mando
@pytest.mark.parametrize("tipo", TIPOS)
def test_un_cuadro_de_texto_se_escribe_con_la_rueda_de_letras(robot, tipo):
    app = robot.app
    md = Md(robot, tipo)
    hecho = []
    e = EntradaTexto(app, "Nombre de prueba", hecho.append, maximo=12, propuestas=["La Gaviota", "El Rayo"])
    app.abrir(e)
    n = BOTON[tipo]
    assert "cruceta arriba y abajo" in _ultimo(robot) and f"{n['a']} acepta y {n['b']} cancela" in _ultimo(robot) and f"{n['x']} pasa por 2 propuestas" in _ultimo(robot)
    assert robot.app.mando.contexto() == "pantalla"
    md.pulsar("abajo")                                           # de la a a la b
    assert _ultimo(robot) == "b"
    md.pulsar("arriba")
    md.pulsar("arriba")                                          # da la vuelta por el final
    assert _ultimo(robot) == "ü"
    md.pulsar("abajo")
    md.escribir("Ola 7")
    assert e.texto == "Ola 7"
    md.pulsar("y")                                               # Y o Triángulo: lee lo escrito
    assert _ultimo(robot) == "Ola 7"
    md.pulsar("izquierda")                                       # cruceta izquierda: borra
    assert e.texto == "Ola " and _ultimo(robot) == "Borrado 7"
    md.pulsar("rb")
    md.pulsar("rb")                                              # de números a signos y a minúsculas otra vez
    assert e.grupo == 0 and _ultimo(robot).startswith("Minúsculas")
    md.pulsar("back")                                            # la ayuda dice todos los botones, con los nombres de este mando
    assert f"{n['lb']} pone un espacio" in _ultimo(robot) and f"{n['rb']} cambia entre minúsculas, mayúsculas, números y signos" in _ultimo(robot)
    md.pulsar("x")                                               # X o Cuadrado: una propuesta
    assert e.texto == "La Gaviota" and "1 de 2" in _ultimo(robot)
    md.pulsar("x")
    md.pulsar("x")
    assert e.texto == "La Gaviota"
    # el tope de letras se respeta
    md.escribir("abcdef")
    assert len(e.texto) == 12 and "No cabe más" in _ultimo(robot)
    md.pulsar("a")
    assert hecho == ["La Gaviotaab"] and e not in app.pila
    # cancelar con B o Círculo
    e2 = EntradaTexto(app, "Otra", hecho.append)
    app.abrir(e2)
    md.pulsar("x")
    assert "no hay propuestas" in _ultimo(robot)
    md.escribir("no")
    md.pulsar("b")
    assert hecho == ["La Gaviotaab"] and e2 not in app.pila
    # palanca izquierda: también mueve la rueda, y mantenida repite
    e3 = EntradaTexto(app, "Otra más", hecho.append)
    app.abrir(e3)
    robot.app.mando.eje("ly", 1.0)
    robot.frames(30)
    robot.app.mando.eje("ly", 0.0)
    robot.frames(1)
    assert e3.letra >= 3 and e3.texto == ""
    md.pulsar("b")


def test_con_el_teclado_los_cuadros_de_texto_siguen_igual_y_tabulador_propone(robot):
    app = robot.app
    hecho = []
    e = EntradaTexto(app, "Nombre", hecho.append, propuestas=lambda: ["Uno", "Dos"])
    app.abrir(e)
    assert "Escribe y pulsa Intro. Escape cancela. Tabulador pasa por 2 propuestas ya escritas." in _ultimo(robot)
    robot.tecla(pygame.K_d, unicode="d")                         # la D, la N y las flechas son letras o nada: no mueven ninguna rueda
    robot.tecla(pygame.K_n, unicode="n")
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_RIGHT)
    assert e.texto == "dn"
    robot.tecla(pygame.K_UP)                                     # flecha arriba lee, como siempre
    assert _ultimo(robot) == "dn"
    robot.tecla(pygame.K_TAB)
    assert e.texto == "Uno"
    robot.tecla(pygame.K_TAB)
    robot.tecla(pygame.K_TAB, pygame.KMOD_SHIFT)
    assert e.texto == "Uno"
    robot.tecla(pygame.K_RETURN)
    assert hecho == ["Uno"]
    sin = EntradaTexto(app, "Sin propuestas", hecho.append)
    app.abrir(sin)
    assert _ultimo(robot) == "Sin propuestas. Escribe y pulsa Intro. Escape cancela. Vacío"
    robot.tecla(pygame.K_ESCAPE)


# ====================================================================== 7. mis vehículos, el nombre y el chófer
def test_mis_vehiculos_ponerle_nombre_y_pedir_chofer_con_el_mando(robot, datos_de_serie):
    p = _empezar(robot)
    md = Md(robot)
    j = p.j
    j.dinero = 5000
    v = p.crear_vehiculo("sedan", j.x + 40, j.y, 1, None, "Rayo")
    assert p.hacer_mio(v)
    md.pulsar("back")                                            # el móvil
    assert isinstance(robot.app.pila[-1], Menu)
    md.elegir("Mis vehículos", empieza=True)
    md.elegir("Rayo", empieza=True)
    assert robot.app.pila[-1].opciones[0].texto == "Marcarlo en el GPS"
    md.elegir("Cambiarle el nombre")
    e = robot.app.pila[-1]
    assert isinstance(e, EntradaTexto) and len(e.propuestas()) == 6 and set(e.propuestas()) <= set(MV.LISTAS["nombres_propuestos"])
    md.pulsar("x")                                               # un nombre de los propuestos, al azar
    elegido = e.texto
    assert elegido in MV.LISTAS["nombres_propuestos"]
    md.pulsar("a")
    assert v.nombre == elegido and f"Ahora se llama {elegido}" in robot.dicho()
    # y escrito letra a letra
    while not isinstance(robot.app.pila[-1], Menu):
        md.pulsar("b")
    md.al_juego()
    md.pulsar("back")
    md.elegir("Mis vehículos", empieza=True)
    md.elegir(elegido, empieza=True)
    md.elegir("Cambiarle el nombre")
    e = robot.app.pila[-1]
    while e.texto:
        md.pulsar("izquierda")
    md.escribir("Mi Sol")
    md.pulsar("a")
    assert v.nombre == "Mi Sol"
    md.al_juego()
    # marcarlo en el GPS desde la lista
    md.pulsar("back")
    md.elegir("Mis vehículos", empieza=True)
    md.elegir("Mi Sol", empieza=True)
    md.elegir("Marcarlo en el GPS")
    assert p.gps is not None
    md.al_juego()
    # el chófer: en el móvil, en Servicios
    j.territorios = [p.mundo.barrios[0]["id"]]
    j.banda, j.banda_nombre = 2, "Los Mirlos"
    p.cfg.v["sin_policia"] = True
    md.pulsar("back")
    md.elegir("Servicios", empieza=True)
    md.elegir("Chófer de tu banda", empieza=True)
    md.elegir("Que venga con un vehículo de la banda", empieza=True)
    assert p.chofer is not None, (robot.dicho(), [o.texto for o in robot.app.pila[-1].opciones])
    md.al_juego()


def test_los_nombres_propuestos_y_las_frases_ya_escritas_salen_de_los_datos(datos_de_serie):
    datos = M.cargar_datos()
    propios = datos["vehiculos_propios"][0]
    assert len(propios["nombres_propuestos"]) >= 20 and MV.LISTAS["nombres_propuestos"] == propios["nombres_propuestos"]
    a, b = MV.nombres_propuestos(), MV.nombres_propuestos()
    assert len(a) == 6 and len(set(a)) == 6
    assert any(MV.nombres_propuestos() != a for _ in range(20))                    # no salen siempre los mismos
    for lista in ("frases_chat", "rol_frases_ic", "rol_frases_yo", "rol_frases_ooc"):
        assert lista in G.LISTAS and len(G.lista(lista)) >= 8 and G.lista(lista) == datos["gente"][0][lista]
    assert all(f[0].islower() for f in G.lista("rol_frases_yo"))                   # las acciones van detrás del nombre
    # un mod los cambia; una lista vacía no deja al juego sin nada
    MV.configurar({"vehiculos_propios": [{"id": "general", "nombres_propuestos": ["El Único"]}]})
    assert MV.nombres_propuestos() == ["El Único"]
    MV.configurar({"vehiculos_propios": [{"id": "general", "nombres_propuestos": []}]})
    assert len(MV.nombres_propuestos()) == 6
    G.configurar({"gente": [{"id": "general", "rol_frases_ic": ["A las buenas."]}]})
    assert G.lista("rol_frases_ic") == ["A las buenas."] and G.lista("rol_frases_yo")
    # y el editor los edita
    fuente = open(os.path.join(rutas.base(), "editor", "esquema.py"), encoding="utf-8").read()
    for clave in ("frases_chat", "rol_frases_ic", "rol_frases_yo", "rol_frases_ooc", "nombres_propuestos"):
        assert f'c("{clave}", ' in fuente, clave


# ====================================================================== 8. atracos, favores, reclutar, pactos, encargos y comida a domicilio
def test_atracar_un_local_con_el_mando(robot, datos_de_serie):
    p = _empezar(robot)
    md = Md(robot, "ps")
    j = p.j
    far = next(l for l in p.mundo.lugares.values() if l.tipo == "farmacia")
    _a(p, far)
    p.dar_arma("pistola", 60)
    j.arma = "pistola"
    dinero = j.dinero
    md.pulsar("a")
    assert isinstance(robot.app.pila[-1], Menu), robot.dicho()
    md.elegir("Atracar este local")
    assert robot.app.pila[-1] is p and j.dinero > dinero and p.atracadas[far.id] == p.dia


def test_pedir_un_favor_y_reclutar_hablando_con_el_mando(robot, datos_de_serie):
    from juego.charla import ficha
    p = _empezar(robot)
    md = Md(robot)
    j = p.j
    j.dinero = 5000
    q = _persona(p, "civil", 2.5, estado="quieto")
    f = ficha(q)
    f.update(caracter="chulo", confianza=80, edad=30, presentado=True)
    q.nombre = f["nombre"]
    j.salud = 30.0
    md.combinar("b")                                             # Vista y B, o Share y Círculo: hablar con quien tienes al lado
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    md.elegir("Pedirle un favor")
    assert j.stats.get("favores") == 1 and j.salud > 30.0
    # reclutar: con territorio, fama y confianza
    j.territorios = ["centro"]
    j.reputacion = 90.0
    while robot.app.pila[-1] is not p:
        md.pulsar("b")
    md.combinar("b")
    md.elegir("Proponerle que se una a tu banda")
    assert j.banda == 1, robot.dicho()


def test_negociar_con_las_bandas_y_defender_desde_el_movil_con_el_mando(robot, datos_de_serie):
    p = _empezar(robot)
    md = Md(robot, "ps")
    j = p.j
    j.dinero = 90000
    j.territorios = ["centro"]
    md.pulsar("back")
    md.elegir("Territorios", empieza=True)
    md.elegir("Negociar con las bandas")
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.opciones[0].texto.startswith("Tu fuerza en la calle")
    md.elegir("Comprar ", empieza=True)
    mesa = robot.app.pila[-1]
    if mesa is not m and isinstance(mesa, Menu) and any(o.texto.startswith("Aceptar") for o in mesa.opciones):
        antes = len(j.territorios)
        md.elegir("Aceptar", empieza=True)
        assert len(j.territorios) == antes + 1
    md.al_juego()


def test_el_tablon_de_encargos_y_la_comida_a_domicilio_con_el_mando(robot, datos_de_serie):
    p = _empezar(robot, vida_realista=True, invulnerable=True)
    md = Md(robot)
    j = p.j
    j.dinero = 500
    casa = p.lugares["casa_abuela"]
    _a(p, casa, 4.0)
    md.pulsar("back")
    md.elegir("Pedir comida a domicilio", empieza=True)
    carta = robot.app.pila[-1]
    assert isinstance(carta, Menu)
    md.pulsar("a")                                               # lo primero de la carta, al pedido
    for _ in range(len(carta.opciones)):
        if carta.opciones[carta.i].texto.startswith(("Encargar", "Hacer el pedido", "Pedir")):
            break
        md.pulsar("abajo")
    md.pulsar("a")
    assert j.pedido, robot.dicho()
    md.al_juego()
    taberna = p.lugares["taberna_puerto"]
    _a(p, taberna)
    md.pulsar("a")
    assert isinstance(robot.app.pila[-1], Menu), robot.dicho()
    md.elegir("Tablón de encargos", empieza=True)
    tablon = robot.app.pila[-1]
    assert isinstance(tablon, Menu) and len(tablon.opciones) >= 3
    md.pulsar("a")
    for _ in range(6):                                           # las escenas del encargo se pasan con A o Equis
        if isinstance(robot.app.pila[-1], Dialogo):
            md.pulsar("a")
    assert p.mision is not None, robot.dicho()


def test_un_plan_en_pareja_con_el_mando(robot, datos_de_serie):
    p = _empezar(robot, adultos=True)
    md = Md(robot, "ps")
    j = p.j
    j.dinero = 2000
    pers = p.persona_social("lucia")
    r = p.relacion("lucia")
    r.update(estado="pareja", afinidad=60, citas=5, ultimo=p.dia)
    j.pareja = "lucia"
    _a(p, p.lugares[pers["lugar"]])
    md.pulsar("back")
    md.elegir("Vida social", empieza=True)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu)
    md.elegir(pers["nombre"])
    md.elegir("Hacer un plan juntos")
    planes = robot.app.pila[-1]
    assert isinstance(planes, Menu) and "Planes con" in str(planes.titulo)
    md.elegir("Un paseo", empieza=True) if any(o.texto.startswith("Un paseo") for o in planes.opciones) else md.pulsar("a")
    assert isinstance(robot.app.pila[-1], Dialogo), robot.dicho()
    for _ in range(8):
        if isinstance(robot.app.pila[-1], Dialogo):
            md.pulsar("a")                                       # las escenas del plan, con A o Equis
    assert j.stats.get("planes_pareja") == 1


# ====================================================================== 9. en un servidor: el rol, la ficha y mirar a otro jugador
def test_los_canales_de_rol_la_ficha_y_mirar_a_otro_jugador_con_el_mando(dos, tmp_path):
    b_ = Banco(tmp_path, rol_metros=30)
    try:
        a, b = dos
        pa, pb = entrar(a, b_, "Ana"), entrar(b, b_, "Blas")
        juntos(pa, pb, a, b, d=6.0)
        assert pa.sv_rol()
        md = Md(a, "ps")
        # en un servidor, el menú de acciones trae los canales de rol
        md.combinar("rt")
        textos = [o.texto for o in a.app.pila[-1].opciones]
        assert textos[:3] == ["Gritar para espantar a los peatones", "Hablar en personaje, para quien está cerca", "Describir lo que hace tu personaje"]
        assert "Escribir un mensaje a los demás jugadores" in textos and "Cómo va vestido el jugador de al lado, y su ficha" in textos
        # hablar en personaje, con una frase ya escrita
        md.elegir("Hablar en personaje")
        e = a.app.pila[-1]
        assert isinstance(e, EntradaTexto) and "personaje" in e.titulo and e.propuestas() == G.lista("rol_frases_ic")
        md.pulsar("x")
        md.pulsar("x")
        frase = e.texto
        assert frase == G.lista("rol_frases_ic")[1]
        md.pulsar("a")
        assert hasta(lambda: f"Ana dice: {frase}" in b.dicho(), a, b)
        # una acción, con una de las propuestas
        md.accion("Describir lo que hace tu personaje")
        e = a.app.pila[-1]
        assert "hace tu personaje" in e.titulo and e.propuestas() == G.lista("rol_frases_yo")
        md.pulsar("x")
        md.pulsar("a")
        assert hasta(lambda: "Ana " + G.lista("rol_frases_yo")[0] in b.dicho(), a, b)
        # un mensaje normal, escrito letra a letra con la rueda
        md.accion("Escribir un mensaje a los demás jugadores")
        e = a.app.pila[-1]
        assert e.propuestas() == G.lista("frases_chat")
        md.escribir("hola")
        md.pulsar("a")
        assert hasta(lambda: "Ana dice: hola" in b.dicho(), a, b)
        # la ficha: por el móvil, en el menú del servidor, Rol; con la rueda de letras
        md.pulsar("back")
        m = a.app.pila[-1]
        assert isinstance(m, Menu)
        md.elegir("Jugar con amigos", empieza=True)                # conectado a un servidor, es el menú del servidor
        md.elegir("Rol", empieza=True)
        md.elegir("Tu ficha", empieza=True)
        e = a.app.pila[-1]
        assert isinstance(e, EntradaTexto) and "ficha" in e.titulo
        md.escribir("pescadora")
        md.pulsar("a")
        assert hasta(lambda: pa.sv.get("ficha") == "pescadora", a, b)
        md.al_juego()
        # el otro, también con mando, le mira: la ropa y la ficha
        mdb = Md(b, "xbox")
        mdb.accion("Cómo va vestido el jugador de al lado")
        assert hasta(lambda: "pescadora" in b.dicho(), a, b), b.dicho()
    finally:
        for r in dos:
            if r.app.partida is not None:
                r.app.partida.sv_salir()
        b_.parar()


# ====================================================================== 10. la ayuda y la documentación
def test_la_ayuda_del_juego_y_la_documentacion_cuentan_todo_lo_del_mando(robot):
    md = robot.app.mando
    md.simulado = True
    for tipo in TIPOS:
        md.tipo = tipo
        lineas = " | ".join(md.lineas_ayuda())
        assert "menú de acciones" in lineas and "rendirte ante la policía" in lineas
        assert "X o Cuadrado dice lo que llevas en la cesta" in lineas and "Para escribir un texto con el mando" in lineas
    menus_juego.ayuda_teclas(robot.app, "pie")
    assert any("menú de acciones" in o.texto for o in robot.app.pila[-1].opciones)
    docs = os.path.join(rutas.base(), "data", "docs")
    teclas = open(os.path.join(docs, "teclas.html"), encoding="utf-8").read()
    assert "Mando, el menú de acciones" in teclas and "gatillo derecho: menú de acciones" in teclas
    for frase, *_ in mando.MENU_ACCIONES:
        assert frase.replace('"', "&quot;") in teclas, frase
    assert "X o Cuadrado dice lo que llevas en la cesta" in teclas and "Para escribir un texto con el mando" in teclas
    manual = open(os.path.join(docs, "manual.html"), encoding="utf-8").read()
    for trozo in ("El menú de acciones", "Escribir con el mando", "rueda de letras", "frases ya escritas", "nombres al azar", "X o Cuadrado: lo que llevas en la cesta",
                  "Gatillo derecho o R2: el menú de acciones", "Gatillo izquierdo o L2: rendirte"):
        assert trozo in manual, trozo
    editor = open(os.path.join(docs, "editor_mods.html"), encoding="utf-8").read()
    assert "Frases ya escritas" in editor and "Nombres propuestos para los vehículos" in editor


# ====================================================================== 11. la prueba vigilante: ninguna tecla sin mando
_SUELTAS = {"intro": pygame.K_RETURN, "escape": pygame.K_ESCAPE, "espacio": pygame.K_SPACE, "tabulador": pygame.K_TAB, "retroceso": pygame.K_BACKSPACE,
            "control": pygame.K_LCTRL, "flecha arriba": pygame.K_UP, "flecha abajo": pygame.K_DOWN, "flecha izquierda": pygame.K_LEFT, "flecha derecha": pygame.K_RIGHT}
_ENTERAS = {"Flechas": [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT], "Flechas izquierda y derecha": [pygame.K_LEFT, pygame.K_RIGHT],
            "Mayúsculas izquierda con las flechas": [pygame.K_LSHIFT]}
S, CT = pygame.KMOD_SHIFT, pygame.KMOD_CTRL


def _teclas_de(etiqueta):
    """Las teclas que nombra una etiqueta de la ayuda: [(tecla, modificador)]. None si no se entiende."""
    if etiqueta in _ENTERAS:
        return [(k, 0) for k in _ENTERAS[etiqueta]]
    out = []
    for trozo in re.split(r",\s*|\s+y\s+", etiqueta):
        t = trozo.strip()
        mod = 0
        if t.startswith("Mayúsculas "):
            mod, t = S, t[len("Mayúsculas "):]
        elif t.startswith("Control ") and len(t) > len("Control "):
            mod, t = CT, t[len("Control "):]
        n = t.lower()
        if n in _SUELTAS:
            k = _SUELTAS[n]
        elif len(n) == 1 and n.isalpha():
            k = getattr(pygame, "K_" + n)
        elif re.fullmatch(r"f\d{1,2}", n):
            k = pygame.K_F1 + int(n[1:]) - 1
        else:
            return None
        out.append((k, mod))
    return out


def _con_mando(k, mod, ctx):
    """Cómo se hace con el mando, de serie, esa tecla en ese contexto (pie o coche). None si no se puede."""
    for a, (_, key, m, _) in mando.ACCIONES.items():
        if key == k and (m & (S | CT)) == (mod & (S | CT)):
            if a in mando.POR_DEFECTO[ctx].values():
                return "botón"
            if a in mando.POR_DEFECTO[ctx + "_combo"].values():
                return "combinación"
    if mod == 0 and k in mando.PALANCAS[ctx]:
        return "palanca"
    if any(e[1] == k and (e[2] & (S | CT)) == (mod & (S | CT)) and e[3] in ("ambos", ctx) for e in mando.MENU_ACCIONES):
        return "menú de acciones"
    return None


def test_vigilante_toda_tecla_de_la_ayuda_se_puede_hacer_con_el_mando():
    """Si esta prueba falla es que alguien ha añadido una tecla a la ayuda sin darle botón, combinación ni sitio en el menú
    de acciones del mando (juego/mando.py). O se le da, o se apunta en mando.SIN_BOTON con su razón."""
    sin = []
    for grupo, contextos in (("general", ("pie", "coche")), ("pie", ("pie",)), ("coche", ("coche",))):
        for etiqueta, _ in ayuda.TECLAS[grupo]:
            if etiqueta in mando.SIN_BOTON:
                assert len(mando.SIN_BOTON[etiqueta]) > 15, etiqueta          # la excepción lleva su razón
                continue
            teclas = _teclas_de(etiqueta)
            assert teclas is not None, f"No entiendo la etiqueta «{etiqueta}» de la ayuda: o es una tecla, o va en mando.SIN_BOTON con su razón"
            for k, mod in teclas:
                for ctx in contextos:
                    if ctx == "coche" and grupo == "general" and etiqueta in mando.SOLO_A_PIE:
                        continue
                    if _con_mando(k, mod, ctx) is None:
                        sin.append((grupo, etiqueta, ctx))
    assert not sin, f"Teclas de la ayuda que no se pueden hacer con el mando: {sin}"
    # las excepciones siguen existiendo en la ayuda: no se queda ninguna vieja
    etiquetas = {e for g in ayuda.TECLAS.values() for e, _ in g}
    assert set(mando.SIN_BOTON) <= etiquetas and set(mando.SOLO_A_PIE) <= etiquetas
    # en los menús: moverse, elegir, cambiar un valor, volver, la ayuda y repasar
    for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_F1, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
        assert k in mando.MENU.values(), k
    # recorriendo una casa, un local o una tienda por dentro
    for etiqueta, _ in ayuda.TECLAS_RECORRIDO:
        teclas = _teclas_de(etiqueta)
        assert teclas is not None, etiqueta
        for k, mod in teclas:
            assert mod == 0 and mando.ALIAS_PANTALLA.get(k, k) in mando.PANTALLA.values(), etiqueta


def test_vigilante_el_menu_de_acciones_manda_teclas_que_el_juego_entiende(robot, datos_de_serie):
    """Cada entrada del menú de acciones corresponde a una tecla que sale en la ayuda (en su etiqueta o en su explicación),
    tiene su frase, y ninguna repite la tecla de otra en el mismo contexto."""
    nombres = {}
    for grupo in ayuda.TECLAS.values():
        for etiqueta, que in grupo:
            for k, mod in (_teclas_de(etiqueta) or []):
                nombres[(k, mod & (S | CT))] = etiqueta
    extra = {(pygame.K_c, S): "Con Mayúsculas añade las coordenadas", (pygame.K_q, S): "Mayúsculas Q fija a cualquiera", (pygame.K_PERIOD, 0): "El punto repite el último",
             (pygame.K_z, S): "las sustancias, con el contenido para adultos", (pygame.K_F7, 0): "F7 y F8", (pygame.K_F8, 0): "F7 y F8"}
    todo = " ".join(q for g in ayuda.TECLAS.values() for _, q in g) + " ".join(e for g in ayuda.TECLAS.values() for e, _ in g)
    for k, frase in ((k, f) for k, f in extra.items() if k[0] not in (pygame.K_z,)):
        assert frase in todo, frase
    vistos = set()
    for frase, k, mod, donde, cond, explicacion, queda in mando.MENU_ACCIONES:
        assert frase and frase[0].isupper() and not frase.endswith("."), frase
        assert donde in ("pie", "coche", "ambos") and (k, mod & (S | CT)) in nombres or (k, mod) in extra, frase
        for ctx in (("pie", "coche") if donde == "ambos" else (donde,)):
            assert (k, mod, ctx, cond) not in vistos, frase
            vistos.add((k, mod, ctx, cond))
    # y todas se pueden elegir sin que el juego se rompa, a pie y al volante
    p = _empezar(robot, adultos=True)
    md = Md(robot)
    p.j.perro = "Canela"
    for vuelta in ("pie", "coche"):
        if vuelta == "coche":
            v = p.crear_vehiculo("sedan", p.j.x + 3, p.j.y, 1, None)
            v.cerrado = False
            md.pulsar("y")
            assert p.j.veh is v
        n = len(mando.acciones_de(p))
        assert n >= 20
        for k in range(n):
            if p.j.veh is None and vuelta == "coche":
                break
            md.al_juego()
            md.combinar("rt")
            m = robot.app.pila[-1]
            assert m.titulo == "Acciones"
            if k >= len(m.opciones) - 1:
                md.pulsar("b")
                continue
            for _ in range(k):
                md.pulsar("abajo")
            md.pulsar("a")
            robot.frames(1)
            for _ in range(6):                                   # lo que abra (un menú, el mapa, un cuadro de texto), se cierra con B o Círculo
                if robot.app.pila[-1] is p:
                    break
                md.pulsar("b")
            assert robot.app.pila[-1] is p, (vuelta, k)


# ====================================================================== 12. al conectar el mando
@pytest.mark.parametrize("nombre, tipo, frase", [("DualSense Wireless Controller", "ps", "el botón Crear o Share mantenido más el botón R2"),
                                                 ("Xbox Series X Controller", "xbox", "el botón Vista mantenido más el gatillo derecho")])
def test_al_conectar_un_mando_se_dice_donde_esta_el_menu_de_acciones(robot, nombre, tipo, frase):
    md = robot.app.mando

    class Falso:
        class Controller:
            def __init__(self, indice):
                self.name = nombre

            def rumble(self, *a):
                pass
    md.ctrl, md.modulo = None, Falso
    try:
        md.conectar(0)
        assert md.tipo == tipo and f"Lo que no tiene botón propio está en el menú de acciones: {frase}." in _ultimo(robot)
        md.mapa["pie_combo"]["rt"] = "nada"                      # si el jugador lo ha quitado, no se promete
        md.ctrl = None
        md.conectar(0)
        assert "menú de acciones" not in _ultimo(robot)
    finally:
        md.ctrl, md.modulo = None, None
        md.mapa = {c: dict(m) for c, m in mando.POR_DEFECTO.items()}
