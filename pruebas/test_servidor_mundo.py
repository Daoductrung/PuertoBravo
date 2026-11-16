"""Lo que hace del servidor un mundo: los personajes que lleva la máquina y el mercado de casas y negocios."""
import time

from test_servidor import Banco, Cli, lejos_de_todo, mundo


def _bots(banco, n, clase=None, junto_a=None):
    """Hace aparecer n personajes del servidor, sin esperar al azar, y opcionalmente todos de una clase y junto a alguien."""
    def crear():
        srv = banco.srv
        out = []
        for _ in range(n):
            b = srv._bot_nuevo("puerto_bravo")
            if clase:
                from servidor import bots
                b.clase, b.arma = clase, bots.ARMA[clase]
            if junto_a is not None:
                j = srv.jugadores[junto_a]
                b.x, b.y = j.x + 3, j.y
            b.t_plan, b.t_frase, b.espera, b.destino = 0.0, 999.0, 999.0, None
            out.append(b.id)
        return out
    return banco.hacer(crear)


def _pensar(banco, veces=1):
    banco.hacer(lambda: [banco.srv.bots_pensar(1.0) for _ in range(veces)])


def test_los_personajes_del_servidor_salen_solos_se_mueven_y_se_van(tmp_path):
    banco = Banco(tmp_path, personajes=5)
    try:
        banco.hacer(lambda: setattr(banco.srv, "rng", __import__("random").Random(4)))
        _pensar(banco, 30)
        assert not banco.srv.bots                                # sin jugadores no hay nadie
        a = Cli(banco, "Ana")
        a.estado()
        time.sleep(0.2)
        _pensar(banco, 80)
        bots = list(banco.srv.bots)
        assert len(bots) == 5 and len({b.nombre for b in bots}) == 5 and len({b.clase for b in bots}) >= 2      # distintos, y de más de una clase
        entra = a.leer("entra", filtro=lambda m: m.get("ia"))
        assert entra["nombre"] in {b.nombre for b in bots}
        # se mueven por la localidad, y Ana los ve como ve a cualquiera
        antes = {b.id: (b.x, b.y) for b in bots}
        for b in bots:
            b.espera = 0
        _pensar(banco, 2)
        banco.hacer(lambda: [banco.srv.bots_mover(0.5) for _ in range(40)])
        assert sum(1 for b in bots if (b.x, b.y) != antes[b.id]) >= 3
        e = a.leer("estados", filtro=lambda m: any(str(b.id) in m["e"] for b in bots))["e"]
        assert all(v["m"] == "puerto_bravo" for v in e.values())
        # no ocupan sitio de jugador, ni salen en la lista de quien administra
        assert "Hay 1:" in banco.hacer(banco.srv.orden, "jugadores")
        # Ana se va a otra localidad: aquí no queda nadie, y allí aparecen otros
        a.estado(mapa="villaseca", x=50, y=50)
        time.sleep(0.2)
        _pensar(banco, 60)
        assert banco.srv.bots and all(b.mapa == "villaseca" for b in banco.srv.bots)
        a.cerrar()
        time.sleep(0.4)
        _pensar(banco, 3)
        assert not banco.srv.bots
    finally:
        banco.parar()


def test_cada_personaje_tiene_su_forma_de_ser(tmp_path):
    banco = Banco(tmp_path, personajes=0, robo_segundos=2)
    try:
        banco.hacer(lambda: setattr(banco.srv, "rng", __import__("random").Random(2)))
        x, y = lejos_de_todo()
        a = Cli(banco, "Ana")
        a.estado(x=x, y=y, di=1000, ar="pistola")
        time.sleep(0.2)
        banco.hacer(lambda: banco.srv.cfg.__setitem__("personajes", 9))
        # el ratero se acerca y atraca; luego sale corriendo
        (rid,) = _bots(banco, 1, "ratero", junto_a=a.id)
        _pensar(banco, 3)
        m = a.leer("atracado")
        ratero = banco.srv.jugadores[rid]
        assert m["pierde"] == 150 and m["nombre"] == ratero.nombre and ratero.huye > 0 and ratero.dinero >= 150
        # Ana le dispara: es el que empezó, así que tumbarle no le pone precio a su cabeza, y se queda lo que llevaba
        banco.hacer(lambda: (setattr(ratero, "x", x + 4), setattr(ratero, "y", y), setattr(ratero, "salud", 5.0), setattr(ratero, "destino", None)))
        baja = None
        for _ in range(12):
            a.enviar({"t": "ataque", "a": rid, "arma": "pistola"})
            time.sleep(0.45)
            try:
                baja = a.leer("baja", 0.1)
                break
            except AssertionError:
                pass
        assert baja and baja["nombre"] == ratero.nombre and baja["botin"] > 0 and a.nada("buscado", 0.3)
        assert a.leer("sale")["id"] == rid and rid not in banco.srv.jugadores
        # a un paseante que no ha hecho nada: unos huyen; y tumbarle sí tiene consecuencias
        (pid,) = _bots(banco, 1, "paseante", junto_a=a.id)
        paseante = banco.srv.jugadores[pid]
        banco.hacer(lambda: setattr(paseante, "salud", 4.0))
        for _ in range(12):
            a.enviar({"t": "ataque", "a": pid, "arma": "pistola"})
            time.sleep(0.45)
            if pid not in banco.srv.jugadores:
                break
        assert pid not in banco.srv.jugadores and a.leer("buscado")["recompensa"] == 500
        # el pistolero va a por quien tiene precio por su cabeza
        (gid,) = _bots(banco, 1, "pistolero", junto_a=a.id)
        a.cola.clear()
        _pensar(banco, 1)
        pistolero = banco.srv.jugadores[gid]
        assert pistolero.presa == a.id
        for _ in range(6):
            _pensar(banco, 1)
            time.sleep(0.45)
        assert a.leer(("herido", "silbido"))["nombre"] == pistolero.nombre
        banco.hacer(lambda: banco.srv._bot_fuera(pistolero))
        # el ladrón se lleva el coche que Ana ha dejado aparcado, y lo deja en otra parte
        a.estado(x=x, y=y, v="sedan", di=850)
        a.enviar({"t": "veh_tomar", "modelo": "sedan", "nombre": "Sedán de Ana", "ref": 1})
        vid = a.leer("veh_tuyo")["id"]
        a.estado(x=x, y=y, di=850)
        a.enviar({"t": "veh_dejar", "id": vid, "x": x, "y": y, "r": 0, "salud": 90})
        time.sleep(0.2)
        (lid,) = _bots(banco, 1, "ladron", junto_a=a.id)
        ladron = banco.srv.jugadores[lid]
        for _ in range(12):
            banco.hacer(lambda: setattr(ladron, "t_plan", 0.0))
            _pensar(banco, 1)
            if ladron.vid == vid:
                break
        assert ladron.vid == vid and a.leer("veh_ocupado")["por"] == lid and "se ha llevado tu" in a.leer("aviso", filtro=lambda m: "llevado" in m["texto"])["texto"]
        banco.hacer(lambda: [banco.srv.bots_mover(0.5) for _ in range(400)])
        libre = a.leer("veh_libre")["v"]
        assert (libre["x"], libre["y"]) != (x, y) and ladron.vid is None
        banco.hacer(lambda: banco.srv._bot_fuera(ladron))
        # el atracador le vacía la caja al negocio de Ana, y a ella le salta la alarma
        negocio = next(l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] == "negocio" and l["precio"] > 0 and l["ingresos"] > 0)
        a.enviar({"t": "prop_comprar", "lugar": negocio["id"]})
        a.leer("prop")
        (tid,) = _bots(banco, 1, "atracador")
        atracador = banco.srv.jugadores[tid]
        banco.hacer(lambda: (setattr(atracador, "x", negocio["x"] + 2), setattr(atracador, "y", negocio["y"])))
        _pensar(banco, 1)
        assert a.leer("robo_aviso")["nombre"] == atracador.nombre
        time.sleep(2.2)
        banco.hacer(banco.srv._robos_paso)
        assert "ha vaciado la caja" in a.leer("aviso", filtro=lambda m: "caja" in m["texto"])["texto"]
    finally:
        banco.parar()


def test_el_mercado_de_casas_y_negocios(tmp_path):
    banco = Banco(tmp_path)
    try:
        ls = [l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] in ("casa", "negocio") and l["precio"] > 0]
        casa, otra = ls[0], ls[1]
        a, b = Cli(banco, "Ana"), Cli(banco, "Blas")
        a.estado(di=50000)
        b.estado(di=4000)
        time.sleep(0.2)
        a.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        assert b.leer("prop")["oferta"] == 0
        b.enviar({"t": "prop_adquirir", "lugar": casa["id"]})
        assert "no está en venta" in b.leer("aviso", filtro=lambda m: "venta" in m["texto"])["texto"]
        # Ana la pone en venta a su precio; Blas no llega, y luego sí
        a.enviar({"t": "prop_oferta", "lugar": casa["id"], "precio": 9000})
        assert b.leer("prop", filtro=lambda m: m["oferta"])["oferta"] == 9000
        b.enviar({"t": "prop_adquirir", "lugar": casa["id"]})
        assert "No te llega" in b.leer("aviso", filtro=lambda m: "llega" in m["texto"])["texto"]
        a.enviar({"t": "prop_oferta", "lugar": casa["id"], "precio": 3000})
        b.leer("prop", filtro=lambda m: m["oferta"] == 3000)
        b.enviar({"t": "prop_adquirir", "lugar": casa["id"]})
        assert b.leer("cobro")["n"] == 3000 and a.leer("dinero")["n"] == 3000
        cambio = a.leer("prop", filtro=lambda m: m["nombre"] == "Blas")
        assert cambio["antes"] == a.ok["cuenta"] and cambio["oferta"] == 0
        # Blas la vende al mercado: recupera el setenta por ciento y vuelve a estar libre
        b.enviar({"t": "prop_soltar", "lugar": casa["id"]})
        assert b.leer("dinero")["n"] == casa["precio"] * 70 // 100
        assert a.leer("prop", filtro=lambda m: m["cuenta"] is None)["lugar"] == casa["id"]
        a.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        assert b.leer("prop", filtro=lambda m: m["nombre"] == "Ana")
        # Ana vende otra a Blas estando ella desconectada: el dinero la espera
        a.enviar({"t": "prop_comprar", "lugar": otra["id"]})
        a.enviar({"t": "prop_oferta", "lugar": otra["id"], "precio": 500})
        b.leer("prop", filtro=lambda m: m["lugar"] == otra["id"] and m["oferta"] == 500)
        a.cerrar()
        time.sleep(0.4)
        b.estado(di=4000)
        time.sleep(0.2)
        b.enviar({"t": "prop_adquirir", "lugar": otra["id"]})
        assert b.leer("cobro")["n"] == 500
        # y lleva tanto sin entrar que lo que le queda vuelve al mercado
        banco.hacer(lambda: (banco.srv.alm.poner(a.ok["cuenta"], visto=time.time() - 40 * 86400), banco.srv.alm.guardar()))
        banco.reloj.t = time.time()
        b.cola.clear()
        banco.hacer(lambda: setattr(banco.srv, "reloj", 1439.6))
        assert b.leer("prop", espera=6, filtro=lambda m: m["lugar"] == casa["id"] and m["cuenta"] is None)
        a2 = Cli(banco, "Ana", semilla=a.semilla)
        pend = {p["que"]: p for p in a2.ok["pendientes"]}
        assert pend["venta"]["n"] == 500 and pend["venta"]["por"] == "Blas" and pend["caducada"]["n"] == casa["precio"] * 70 // 100
        assert casa["id"] not in a2.ok["props"] and a2.ok["props"][otra["id"]]["nombre"] == "Blas"
    finally:
        banco.parar()
