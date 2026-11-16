"""El juego conectado a un servidor de verdad: dos juegos completos, cada uno con su mundo, y lo que comparten.

Entrar y retomar el personaje, verse y hablarse, darse cosas, quitarse los vehículos, pelear, las bandas y los barrios,
las misiones en grupo y el reloj común.
"""
import hashlib
import time

import pygame
import pytest

from conftest import Robot
from juego import enlinea, menus_enlinea, menus_juego
from juego.menus import Dialogo, EntradaTexto, Menu
from test_servidor import Banco, lejos_de_todo


@pytest.fixture
def banco(tmp_path):
    b = Banco(tmp_path)
    yield b
    b.parar()


@pytest.fixture
def dos(app):
    from juego.app import App
    otro = App(pruebas=True)
    yield Robot(app), Robot(otro)
    for a in (app, otro):
        if a.partida is not None:
            a.partida.sv_salir()
            a.partida.desconectar_online()
    otro.radio.cancelar()
    otro.ambiente.cancelar()
    otro.mez.cerrar()


def entrar(robot, banco, nombre):
    """Entra en el servidor con una identidad propia, por el mismo camino que el menú."""
    app = robot.app
    app.cfg["red_nombre"] = nombre
    app.semilla_identidad = hashlib.sha256(("juego-" + nombre).encode()).digest()
    s = {"nombre": "", "dir": f"puertobravo://127.0.0.1:{banco.puerto}", "cert": ""}
    enlace, motivo = enlinea.conectar(app, s)
    assert enlace is not None, motivo
    app.enlace = enlace
    if enlace.ok.get("partida"):
        app.empezar_partida(enlace.ok["partida"])
    else:
        app.empezar_partida(None, personaje={"id": app.datos["personajes"][0]["id"], "genero": "h"})
    robot.saltar_dialogos()
    p = app.partida
    assert p.en_servidor and p.online_activo()
    p.cfg["sucesos"] = False
    return p


def ambos(a, b, n=3):
    for _ in range(n):
        a.frames(1)
        b.frames(1)


def hasta(cond, a, b, segundos=8.0):
    fin = time.time() + segundos
    while time.time() < fin:
        ambos(a, b, 2)
        if cond():
            return True
        time.sleep(0.01)
    return False


def juntos(pa, pb, a, b, d=6.0):
    """Los dos en el mismo sitio, lejos de cualquier zona segura, y viéndose."""
    x, y = lejos_de_todo(pa.mundo.id)
    pa.teletransportar(x, y)
    pb.teletransportar(x + d, y)
    ra = lambda: next(iter(pb.remotos.values()))
    rb = lambda: next(iter(pa.remotos.values()))
    assert hasta(lambda: pa.remotos and pb.remotos and rb().visto and ra().visto and rb().dist(*pb.pos()) < 2 and ra().dist(*pa.pos()) < 2, a, b)
    for p in (pa, pb):
        p.sv["protegido"] = 0
    return rb(), ra()


def test_entrar_desde_el_menu_jugar_y_retomar_el_personaje(robot, banco):
    app = robot.app
    app.semilla_identidad = hashlib.sha256(b"menu").digest()
    app.cfg["red_nombre"] = "Marina"
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Jugar en un servidor")
    robot.tecla(pygame.K_RETURN)
    lista = app.pila[-1]
    assert "Todavía no tienes ningún servidor" in lista.opciones[0].texto
    lista.i = next(k for k, o in enumerate(lista.opciones) if o.texto == "Añadir un servidor")
    robot.tecla(pygame.K_RETURN)
    assert isinstance(app.pila[-1], EntradaTexto)
    app.pila[-1].texto = f"127.0.0.1:{banco.puerto}"
    robot.tecla(pygame.K_RETURN)
    assert app.cfg["servidores"][0]["dir"] == f"puertobravo://127.0.0.1:{banco.puerto}"
    lista.refrescar(False)
    lista.i = 0
    robot.tecla(pygame.K_RETURN)                                 # entrar: es la primera vez, pide personaje
    elegir = app.pila[-1]
    assert isinstance(elegir, Menu) and "personaje" in elegir.titulo
    elegir.i = 0
    robot.tecla(pygame.K_RETURN)
    c = app.pila[-1]
    if isinstance(c, Menu) and "te hablen" in c.titulo:
        robot.tecla(pygame.K_RETURN)
    robot.saltar_dialogos()
    p = app.partida
    assert p is not None and p.en_servidor and "Marina" in robot.dicho() and "no cifra" in robot.dicho()
    assert app.cfg["servidores"][0]["nombre"] == "Servidor de Puerto Bravo"
    # juega: gana dinero, se mueve, y el reloj es el del servidor
    p.j.dinero = 4321
    bar = p.mundo.lugares["bar_gaviota"]
    p.teletransportar(bar.x, bar.y)
    dia = p.dia
    p.pasar_horas(30)                                            # dormir no adelanta el reloj de todos
    assert p.dia == dia
    # guardar en una casa o con F5 lo manda al servidor, no al disco
    assert menus_juego.escribir_ranura(p, "1") and menus_juego.leer_ranura("1") is None
    # el menú En línea del móvil es el del servidor
    menus_enlinea.menu(p)
    textos = [o.texto for o in app.pila[-1].opciones]
    assert any(t.startswith("Estás en Servidor de Puerto Bravo") for t in textos) and "Quién hay" in textos and any(t.startswith("Tu banda") for t in textos)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Salir del servidor")
    robot.tecla(pygame.K_RETURN)
    app.pila[-1].i = 1
    robot.tecla(pygame.K_RETURN)
    assert app.partida is None and isinstance(app.pila[-1], Menu) and "Menú principal" in app.pila[-1].titulo
    time.sleep(0.4)
    # vuelve a entrar: mismo personaje, mismo dinero, mismo sitio
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Jugar en un servidor")
    robot.tecla(pygame.K_RETURN)
    app.pila[-1].i = 0
    robot.tecla(pygame.K_RETURN)
    robot.saltar_dialogos()
    p2 = app.partida
    assert p2 is not None and p2 is not p and p2.en_servidor and p2.j.dinero == 4321
    assert abs(p2.j.x - bar.x) < 30 and abs(p2.j.y - bar.y) < 30


def test_dos_jugadores_se_ven_se_hablan_y_se_dan_cosas(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b)
    assert rb.nombre == "Blas" and ra.nombre == "Ana" and "Ana" in pb.donde_esta(ra)
    assert abs(pa.reloj - pb.reloj) < 3 and pa.dia == pb.dia and pa.j.semilla == pb.j.semilla      # misma hora y misma suerte
    menus_enlinea.chat(pa, "cerca", None, "x")
    a.app.pila[-1].texto = "hola, Blas"
    a.tecla(pygame.K_RETURN)
    assert hasta(lambda: "Ana dice aquí cerca: hola, Blas" in b.dicho(), a, b)
    # dinero: sale de un bolsillo y entra en el otro
    pa.j.dinero, pb.j.dinero = 1000, 0
    assert pa.dar_dinero_a(rb, 300)
    assert hasta(lambda: pb.j.dinero == 300, a, b) and pa.j.dinero == 700
    # un arma, en mano
    pa.dar_arma("pistola", 24)
    menus_enlinea.jugador(pa, rb)
    m = a.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Darle un arma"))
    a.tecla(pygame.K_RETURN)
    md = a.app.pila[-1]
    md.i = next(k for k, o in enumerate(md.opciones) if o.texto.startswith("El arma: Pistola"))
    a.tecla(pygame.K_RETURN)
    assert "pistola" not in pa.j.armas
    assert hasta(lambda: "pistola" in pb.j.armas, a, b) and "Ana te da" in b.dicho()


def test_el_coche_que_robas_te_lo_puede_quitar_otro_jugador(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=8.0)
    # Ana roba un coche de su mundo: Blas la oye conducirlo
    x, y = pa.pos()
    v = pa.crear_vehiculo("sedan", x, y, 0, "aparcado")
    v.cerrado = False
    pa._subir(v, True)
    assert hasta(lambda: getattr(v, "id_red", None) is not None and ra.veh == "sedan" and getattr(ra, "vid", None) == v.id_red, a, b)
    # Blas la saca del coche y se lo queda
    pb.teletransportar(x + 3, y)
    assert hasta(lambda: ra.dist(*pb.pos()) < 6, a, b)
    b.tecla(pygame.K_f, pygame.KMOD_SHIFT)                       # Mayúsculas F: sacar al conductor
    assert hasta(lambda: pb.j.veh is not None and pa.j.veh is None, a, b), (b.dicho()[-300:], a.dicho()[-200:], pb.j.veh, pa.j.veh, ra.vel)
    assert "te saca del vehículo" in a.dicho() and "Sacas a Ana" in b.dicho() and pb.j.veh.modelo["id"] == "sedan"
    assert rb.hostil                                             # y Ana ya sabe quién ha sido: la Q le fija
    # Blas lo deja aparcado más allá; en el mundo de Ana aparece ahí
    pb.j.veh.x, pb.j.veh.y = x + 60, y
    vb = pb.j.veh
    pb.salir_vehiculo()
    assert hasta(lambda: any(getattr(q, "id_red", None) == vb.id_red and abs(q.x - (x + 60)) < 2 for q in pa.vehiculos), a, b), (
        vb.id_red, x + 60, [(getattr(q, "id_red", None), round(q.x), q.muerto) for q in pa.vehiculos if getattr(q, "id_red", None)], dict(banco.srv.vehiculos), pa.sv["vehs"])
    copia = next(q for q in pa.vehiculos if getattr(q, "id_red", None) == vb.id_red)
    # Ana va a por él y lo recupera con la F; del mundo de Blas desaparece
    pa.teletransportar(copia.x + 2, copia.y)
    ambos(a, b, 8)
    time.sleep(0.2)
    ambos(a, b, 4)
    pa.entrar_salir()
    assert hasta(lambda: pa.j.veh is copia, a, b)
    assert hasta(lambda: vb.muerto and "se ha llevado tu" in b.dicho(), a, b)
    # lo mete en su garaje: deja de estar en la calle para todos
    pa.salir_vehiculo(forzado=True)
    pa.quitar_vehiculo(copia)
    assert hasta(lambda: not banco.srv.vehiculos, a, b)


def test_pelea_entre_jugadores(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=8.0)
    pa.dar_arma("pistola", 200)
    pa.j.arma = "pistola"
    pa.j.armas["pistola"]["cargador"] = 12
    pb.j.dinero = 1000
    # con la Q no sale: Blas no le ha hecho nada. Con Mayúsculas Q, sí
    assert pa.fijar(callar=True) is None
    assert pa.fijar(True, callar=True) is rb
    salud = pb.j.salud
    banco.hacer(lambda: setattr(banco.srv, "rng", __import__("random").Random(5)))
    for _ in range(40):
        pa.j.t_ataque = 0
        pa.j.armas["pistola"]["cargador"] = 12
        pa.atacar()
        ambos(a, b, 2)
        time.sleep(0.42)
        if pb.j.salud < salud:
            break
    assert pb.j.salud < salud and "Ana te ataca" in b.dicho() and ra.hostil
    assert pb.fijar(callar=True) is ra                           # a Blas, la Q ya le fija a quien le dispara
    assert hasta(lambda: "Le das a Blas" in a.dicho(), a, b)
    # Blas cae: va al hospital, pierde el diez por ciento, y Ana lo cobra y queda buscada
    dinero_a = pa.j.dinero
    pb.j.salud = 1
    for _ in range(60):
        pa.j.t_ataque = 0
        pa.j.armas["pistola"]["cargador"] = 12
        pa.atacar()
        ambos(a, b, 2)
        time.sleep(0.42)
        if pb.transicion or pb.j.stats["muertes"]:
            break
    assert pb.j.stats["muertes"] == 1
    b.saltar_dialogos()
    assert hasta(lambda: pa.j.dinero == dinero_a + 100 and pb.j.dinero == 1000 - 150 - 100, a, b), (pa.j.dinero - dinero_a, pb.j.dinero)      # el hospital cobra lo suyo, aparte
    assert "Has tumbado a Blas" in a.dicho() and "por tu cabeza" in a.dicho() and "Has caído ante Ana" in b.dicho()
    # en la puerta del hospital no se le puede rematar
    hosp = min((l for l in pb.mundo.lugares.values() if l.tipo == "hospital"), key=lambda l: l.dist(*pb.pos()) if hasattr(l, "dist") else abs(l.x - pb.j.x))
    pa.teletransportar(hosp.x + 6, hosp.y)
    pb.teletransportar(hosp.x, hosp.y)
    ambos(a, b, 10)
    time.sleep(0.3)
    ambos(a, b, 6)
    for p in (pa, pb):
        p.sv["protegido"] = 0
    banco.hacer(lambda: [setattr(q, "protegido", 0) for q in banco.srv.jugadores.values()])
    assert pa.sv_segura() and pa.sv["segura"]
    pa.objetivo = rb
    pa.j.t_ataque = 0
    pa.atacar()
    assert hasta(lambda: "Zona segura" in a.dicho(), a, b)


def test_banda_barrio_y_mision_en_grupo(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b)
    pa.j.dinero = pb.j.dinero = 20000
    ambos(a, b, 6)
    time.sleep(0.2)
    # Ana funda una banda desde el menú
    menus_enlinea.banda(pa)
    m = a.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Fundar una banda"))
    a.tecla(pygame.K_RETURN)
    a.app.pila[-1].texto = "Los Linces"
    a.tecla(pygame.K_RETURN)
    assert hasta(lambda: pa.sv["banda"] is not None, a, b)
    assert pa.j.dinero == 18000 and pa.sv["rango"] == "jefe" and "Ana ha fundado la banda Los Linces" in b.dicho()
    while a.app.pila[-1] is not pa:
        a.tecla(pygame.K_ESCAPE)
    # invita a Blas, que acepta desde su móvil
    pa.red.enviar({"t": "banda_invitar", "a": rb.id})
    assert hasta(lambda: pb.sv["inv_banda"] is not None, a, b) and "te invita a la banda Los Linces" in b.dicho()
    menus_enlinea.banda(pb)
    b.tecla(pygame.K_RETURN)
    assert hasta(lambda: pb.sv["banda"] is not None and len(pa.sv["banda"]["miembros"]) == 2, a, b)
    while b.app.pila[-1] is not pb:
        b.tecla(pygame.K_ESCAPE)
    assert hasta(lambda: pa.sv_relacion(rb) == "de tu banda", a, b)
    # caja y barrio
    pb.red.enviar({"t": "banda_ingresar", "n": 5000})
    assert hasta(lambda: pa.sv["banda"]["caja"] == 5000 and pb.j.dinero == 15000, a, b)
    menus_enlinea.banda(pa)
    m = a.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Reclamar este barrio"))
    a.tecla(pygame.K_RETURN)
    barrio = pa.mundo.barrio(*pa.pos())["id"]
    assert hasta(lambda: pa.sv_dueno_barrio(pa.mundo.id, barrio) is not None and pb.sv_dueno_barrio(pb.mundo.id, barrio) is not None, a, b)
    assert pa.sv["banda"]["caja"] == 2000
    while a.app.pila[-1] is not pa:
        a.tecla(pygame.K_ESCAPE)
    menus_enlinea.tablon(pb)
    assert hasta(lambda: any("Los Linces: 2 miembros, 1 barrios" in o.texto for o in (b.app.pila[-1].refrescar(False), b.app.pila[-1].opciones)[1]), a, b)
    b.tecla(pygame.K_ESCAPE)
    # misión en grupo: Ana lleva Morosos, Blas va con ella
    pa.red.enviar({"t": "grupo_invitar", "a": rb.id, "mision": "Morosos"})
    assert hasta(lambda: pb.sv["inv_grupo"] is not None, a, b)
    pb.red.enviar({"t": "grupo_resp", "si": True})
    assert hasta(lambda: pa.sv_lidero() and pb.sv["grupo"] == pa.red.id, a, b)
    mis = next(x for x in pa.datos["misiones"] if x["id"] == "m04")
    l = pa.lugares[mis["lugar"]]
    pa.teletransportar(l.x, l.y)
    pa.iniciar_mision(mis)
    a.saltar_dialogos()
    ambos(a, b, 4)
    paso = pa.mision["def"]["pasos"][pa.mision["paso"]]
    assert paso["tipo"] == "eliminar"
    assert hasta(lambda: pb.sv["mision_grupo"] is not None, a, b) and "Misión de Ana, Morosos" in b.dicho()
    assert pb.gps is not None                                    # a Blas el GPS le lleva al sitio
    lugar = pa.lugares[paso["lugar"]]
    pa.teletransportar(lugar.x, lugar.y)
    pb.teletransportar(lugar.x + 4, lugar.y)
    assert hasta(lambda: pa.mision["generado"] and len(pb.sv["ecos"]) == len(pa.mision["enemigos"]) > 0, a, b)
    assert "son también tuyos" in b.dicho()
    # lo que Blas le quita a un enemigo, se lo quita también en el juego de Ana
    k, eco = next(iter(pb.sv["ecos"].items()))
    suyo = next(e for e in pa.mision["enemigos"] if e.eco_k == k)
    antes = suyo.salud
    pb.danar_persona(eco, 20)
    assert hasta(lambda: suyo.salud == antes - 20, a, b)
    # entre los dos acaban con todos; al completarla, Blas cobra la mitad
    for e in list(pb.sv["ecos"].values()):
        pb.danar_persona(e, 500)
    assert hasta(lambda: pa.mision is None or all(e.muerto for e in pa.mision["enemigos"]) or not pa.mision["enemigos"], a, b)
    dinero_b = pb.j.dinero
    for _ in range(12):
        a.saltar_dialogos()
        if pa.mision and a.app.pila[-1] is pa:
            pa._paso_hecho()
        ambos(a, b, 2)
        if "m04" in pa.completadas:
            break
    assert "m04" in pa.completadas
    assert hasta(lambda: pb.j.dinero == dinero_b + mis["recompensa"]["dinero"] // 2, a, b)
    assert "Tu parte" in b.dicho() and not pb.sv["ecos"]


def test_el_dia_lo_cambia_el_servidor_para_todos(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    dia = pa.dia
    pa.reloj = 1439.95
    a.frames(30)
    assert pa.dia == dia and pa.reloj < 1440                     # el juego de Ana no pasa de día por su cuenta
    banco.hacer(lambda: setattr(banco.srv, "reloj", 1439.7))
    assert hasta(lambda: pa.dia == dia + 1 and pb.dia == dia + 1, a, b, 10)
    assert pa.reloj < 30 and pb.reloj < 30
    # si el servidor se apaga, cada uno vuelve al menú con su personaje guardado
    banco.hacer(banco.srv.orden, "aviso cerramos en un minuto")
    assert hasta(lambda: "cerramos en un minuto" in a.dicho(), a, b)


def test_atracar_y_hablar_con_otro_jugador_como_con_cualquiera(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=3.0)
    pa.j.dinero, pb.j.dinero = 0, 1000
    ambos(a, b, 6)
    time.sleep(0.2)
    ambos(a, b, 4)
    # la J, sin nadie más al lado, es para hablarle a él
    pa.personas[:] = [q for q in pa.personas if q.tipo != "civil"]
    a.tecla(pygame.K_j)
    assert isinstance(a.app.pila[-1], EntradaTexto) and "Blas" in a.app.pila[-1].titulo
    a.app.pila[-1].texto = "la bolsa o la vida"
    a.tecla(pygame.K_RETURN)
    assert hasta(lambda: "Ana dice solo a ti: la bolsa o la vida" in b.dicho(), a, b)
    # la E le atraca, pero hay que ir armado
    a.tecla(pygame.K_e)
    assert "empuñar un arma" in a.dicho() and pb.j.dinero == 1000
    pa.dar_arma("navaja", 0)
    pa.j.arma = "navaja"
    ambos(a, b, 6)
    time.sleep(0.2)
    ambos(a, b, 4)
    a.tecla(pygame.K_e)
    assert hasta(lambda: pa.j.dinero == 150 and pb.j.dinero == 850, a, b)
    assert "Atracas a Blas: 150 euros" in a.dicho() and "Ana te atraca" in b.dicho() and ra.hostil


def test_lo_que_hace_uno_lo_oye_el_otro(dos, banco):
    """Disparos, gritos y la sirena de quien va buscado se oyen en el juego del que está cerca, donde está el otro."""
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=20.0)
    oido = []
    real = pb.son
    pb.son = lambda nombre, **kw: (oido.append((nombre, kw.get("xy"))), real(nombre, **kw))[1]
    # un peatón del mundo de Blas, junto a Ana
    from juego.entidades import Persona
    civil = Persona("civil", ra.x + 3, ra.y)
    pb.personas.append(civil)
    a.tecla(pygame.K_h)                                          # Ana grita
    assert hasta(lambda: any(n == "grito" for n, _ in oido), a, b)
    assert civil.estado == "huye"
    civil.estado = "pasea"
    pa.dar_arma("pistola", 30)
    pa.j.arma = "pistola"
    pa.j.armas["pistola"]["cargador"] = 6
    pa.objetivo = None
    pa.j.t_ataque = 0
    pa.atacar()                                                  # un tiro al aire: no va contra nadie
    sonido = pa.armas_d["pistola"]["sonido"]
    assert hasta(lambda: any(n == sonido and xy is not None and abs(xy[0] - ra.x) < 3 for n, xy in oido), a, b)
    assert civil.estado == "huye" and pb.j.salud == pb.j.salud_max
    # a Ana la busca la policía: Blas oye las sirenas ir con ella
    pa.poner_busqueda(2)
    assert hasta(lambda: getattr(ra, "sirena", None) is not None, a, b)
    pa._fin_persecucion()
    assert hasta(lambda: getattr(ra, "sirena", None) is None, a, b)


def test_comprar_un_negocio_y_que_otro_jugador_lo_atraque(dos, banco):
    a, b = dos
    banco.hacer(lambda: banco.srv.cfg.__setitem__("robo_segundos", 2))
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    negocio = next(l for l in pa.mundo.lugares.values() if l.tipo == "negocio" and int(l.get("precio", 0)) > 0 and int(l.get("ingresos", 0)) > 0)
    precio, ingresos = int(negocio.get("precio")), int(negocio.get("ingresos"))
    for p in (pa, pb):
        p.teletransportar(negocio.x, negocio.y)
        p.j.dinero = precio + 500
        p.sv["protegido"] = 0
    ambos(a, b, 6)
    # Ana lo compra en su menú de siempre
    menus_juego.lugar(pa, negocio)
    m = a.app.pila[-1]
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Comprar el negocio"))
    a.tecla(pygame.K_RETURN)
    assert negocio.id in pa.j.propiedades and pa.j.dinero == 500
    assert hasta(lambda: pb.sv_dueno(pb.lugares[negocio.id]) == "Ana", a, b) and "Ana compra" in b.dicho()
    while a.app.pila[-1] is not pa:
        a.tecla(pygame.K_ESCAPE)
    # Blas ya no lo puede comprar: su menú dice de quién es y le deja atracarlo
    menus_juego.lugar(pb, pb.lugares[negocio.id])
    m = b.app.pila[-1]
    m.refrescar(False)
    textos = [o.texto for o in m.opciones]
    assert any("es de Ana" in t for t in textos) and not any(t.startswith("Comprar") for t in textos)
    pb.dar_arma("pistola", 20)
    pb.j.arma = "pistola"
    ambos(a, b, 6)
    time.sleep(0.2)
    ambos(a, b, 4)
    dinero_b = pb.j.dinero
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Atracar el negocio")
    b.tecla(pygame.K_RETURN)
    assert hasta(lambda: "¡Atraco!" in b.dicho() and "Blas está atracando tu negocio" in a.dicho(), a, b)
    assert next(iter(pa.remotos.values())).hostil and pb.j.estrellas >= 1      # Ana ya puede fijarle, y a Blas le busca la policía
    assert hasta(lambda: pb.j.dinero == dinero_b + ingresos, a, b, 10) and "Caja vaciada" in b.dicho()
    assert hasta(lambda: "Blas ha vaciado la caja" in a.dicho(), a, b)
    # a medianoche Ana cobra su negocio, y se le descuenta lo robado
    antes = pa.j.dinero
    banco.hacer(lambda: setattr(banco.srv, "reloj", 1439.7))
    assert hasta(lambda: "les han robado" in a.dicho(), a, b, 12)
    assert pa.j.dinero <= antes + ingresos - ingresos + 400      # lo ganado ese día menos lo robado, más lo demás de la medianoche
    # si los dos lo compran a la vez en sus mundos, se lo queda el primero y al otro se le devuelve el dinero
    otro = next(l for l in pa.mundo.lugares.values() if l.tipo == "negocio" and int(l.get("precio", 0)) > 0 and l.id != negocio.id)
    for p in (pa, pb):
        p.j.dinero = int(otro.get("precio")) + 100
        p.pagar(int(otro.get("precio")))
        p.j.propiedades.append(otro.id)
    pa.sv_comprado(pa.lugares[otro.id])
    pb.sv_comprado(pb.lugares[otro.id])
    assert hasta(lambda: (otro.id in pa.j.propiedades) != (otro.id in pb.j.propiedades), a, b)
    perdedor, rp = (pb, b) if otro.id in pa.j.propiedades else (pa, a)
    assert perdedor.j.dinero == int(otro.get("precio")) + 100 and "se te ha adelantado" in rp.dicho()


def test_el_juego_le_trae_el_mundo_a_un_servidor_que_no_lo_conoce(robot, tmp_path):
    """Un servidor con el mundo de una versión anterior, y con la opción para mods: el juego del administrador se lo pone al día al entrar."""
    import copy
    from test_servidor import mundo
    viejo = copy.deepcopy(mundo())
    viejo["version"], viejo["huella"] = "1.0.0", "0000000000000000"
    viejo["mapas"] = {"puerto_bravo": viejo["mapas"]["puerto_bravo"]}
    b = Banco(tmp_path, actualizar_mundo="admin")
    try:
        b.hacer(lambda: b.srv._poner_mundo(viejo, guardar=False))
        p = entrar(robot, b, "Jefa")
        assert p.en_servidor and b.srv.mundo["huella"] == robot.app._huella_datos and len(b.srv.mundo["mapas"]) > 1
        assert any("El mundo pasa de la versión 1.0.0" in t for t in b.lineas)
        p.sv_salir()
    finally:
        b.parar()
