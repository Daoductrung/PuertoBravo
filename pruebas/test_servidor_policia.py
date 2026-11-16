"""La policía que lleva el servidor: la búsqueda, las patrullas que persiguen, los agentes a pie y la detención."""
import math
import time

import pygame

from servidor import nucleo
from test_enlinea import ambos, dos, entrar, hasta        # noqa: F401  (dos es una fixture)
from test_servidor import Banco, Cli, mundo


def en_calle(m="puerto_bravo"):
    """Un punto en mitad de una calle, lejos de cualquier zona segura."""
    d = mundo()["mapas"][m]
    seguras = [(l["x"], l["y"]) for l in d["lugares"] if l["tipo"] in nucleo.SEGURAS]
    for i in range(2, d["nx"] - 3):
        for j in range(2, d["ny"] - 3):
            x, y = i * 90.0 + 45.0, j * 90.0 + 7.5
            if all((x - a) ** 2 + (y - b) ** 2 > 70 ** 2 for a, b in seguras):
                return x, y
    raise AssertionError("no hay sitio")


def patrullas_de(b, ident):
    return [c for c in b.srv.trafico.values() if c.get("obj") == ident]


def acercar_patrulla(b, ident, vueltas=400):
    """Hace correr las calles del servidor hasta que la patrulla alcanza a su perseguido y suelta a los agentes."""
    def paso():
        for _ in range(50):
            b.srv.trafico_mover(0.1)
        return any(a["obj"] == ident for a in b.srv.agentes.values())
    for _ in range(vueltas):
        if b.hacer(paso):
            return True
    return False


def test_la_busqueda_la_persecucion_y_la_detencion_las_lleva_el_servidor(tmp_path):
    b = Banco(tmp_path, policia="si")
    try:
        b.hacer(lambda: setattr(b.srv, "rng", __import__("random").Random(11)))
        a = Cli(b, "Ana")
        assert a.ok["servidor"]["policia"]
        x, y = en_calle()
        a.estado(x=x, y=y)
        time.sleep(0.2)
        ja = b.srv.jugadores[a.id]
        # una falta pequeña no basta; un delito de verdad, sí
        a.enviar({"t": "delito", "n": 0.5})
        assert a.nada("nivel_busqueda", 0.4) and ja.estrellas == 0
        a.enviar({"t": "delito", "n": 4})
        assert a.leer("nivel_busqueda")["es"] == 2 and ja.estrellas == 2
        a.estado(x=x, y=y, es=0)                                 # decir que no te buscan no sirve de nada
        time.sleep(0.2)
        assert ja.estrellas == 2
        assert a.leer("estados", filtro=lambda m: "es" in m)["es"] == 2
        # la primera patrulla tarda unos segundos en salir, y aparece a un par de manzanas
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(2)])
        assert not patrullas_de(b, a.id)
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(4)])
        pat = patrullas_de(b, a.id)
        assert len(pat) == 1 and pat[0]["modelo"] == "patrulla"
        px, py, _ = b.srv.tr_pos(pat[0])
        assert 140 < math.hypot(px - x, py - y) < 240
        a.cola.clear()
        assert any(f[6] == 2 for f in a.leer("estados", filtro=lambda m: m.get("tr"))["tr"])       # su juego sabe que viene a por alguien
        # viene por las calles, llega, para y se bajan dos agentes
        assert acercar_patrulla(b, a.id)
        assert pat[0]["desp"] and len(b.srv.agentes) == 2
        cx, cy, _ = b.srv.tr_pos(pat[0])
        assert math.hypot(cx - x, cy - y) < 16
        a.cola.clear()
        m = a.leer("estados", filtro=lambda m: m.get("po"))
        assert len(m["po"]) == 2 and all(f[3] == a.id and f[4] == "pistola" for f in m["po"])
        assert any(f[6] == 3 for f in a.leer("estados", filtro=lambda m: m.get("tr"))["tr"])
        # se aleja más de la cuenta: los agentes se suben otra vez y la patrulla sigue tras ella; al alcanzarla, se bajan de nuevo
        a.estado(x=x + 180, y=y)
        time.sleep(0.2)
        b.hacer(lambda: b.srv.trafico_mover(0.1))
        assert not pat[0].get("desp") and not b.srv.agentes
        a.estado(x=x, y=y)
        time.sleep(0.2)
        assert acercar_patrulla(b, a.id) and len(b.srv.agentes) == 2
        cx, cy, _ = b.srv.tr_pos(pat[0])
        a.cola.clear()
        # con dos de búsqueda, disparan: se les oye amartillar, y unas veces dan y otras no
        b.hacer(lambda: [b.srv.policia_mover(0.1) for _ in range(300)])
        assert a.leer("po_apunta")
        tiros = []
        while True:
            try:
                tiros.append(a.leer("po_disparo", 0.3))
            except AssertionError:
                break
        assert len(tiros) >= 6 and all(t["a"] == a.id and t["arma"] == "pistola" for t in tiros)
        assert any(t["da"] > 0 for t in tiros) and any(t["da"] == 0 for t in tiros)
        assert a.nada("detenido", 0.2)
        # otro jugador que pasa por allí los ve, y puede darles: lo que le pase al agente, le pasa para todos
        c = Cli(b, "Ciro")
        c.estado(x=x + 5, y=y)
        time.sleep(0.2)
        fila = c.leer("estados", filtro=lambda m: m.get("po"))["po"][0]
        assert fila[3] == a.id
        c.enviar({"t": "po_dano", "id": fila[0], "n": 30, "cae": False})
        time.sleep(0.2)
        assert b.srv.agentes[fila[0]]["salud"] == 50
        c.enviar({"t": "po_dano", "id": fila[0], "n": 60, "cae": True})
        assert a.leer("po_cae")["id"] == fila[0] and len(b.srv.agentes) == 1
        # con los agentes fuera, la patrulla se puede robar
        c.estado(x=cx + 2, y=cy)
        time.sleep(0.2)
        c.enviar({"t": "tr_robar", "id": pat[0]["id"]})
        assert c.leer("veh_ok")["v"]["modelo"] == "patrulla" and pat[0]["id"] not in b.srv.trafico
        # paga la multa: ya no la buscan, y el agente que queda se desentiende
        a.enviar({"t": "busqueda", "nivel": 0})
        assert a.leer("nivel_busqueda", filtro=lambda m: m["es"] == 0)["motivo"] == "limpia"
        resto = next(iter(b.srv.agentes.values()))
        assert resto["obj"] is None and ja.estrellas == 0 and ja.puntos == 0
        # vuelve a hacer una, pequeña: el agente que quedaba va a por ella, y con uno de búsqueda no dispara, la detiene
        a.enviar({"t": "delito", "n": 1})
        assert a.leer("nivel_busqueda")["es"] == 1
        a.cola.clear()
        b.hacer(b.srv.policia_pensar)
        assert resto["obj"] == a.id
        b.hacer(lambda: [b.srv.policia_mover(0.1) for _ in range(150)])
        assert a.leer("detenido") and a.nada("po_disparo", 0.3)
        assert math.hypot(resto["x"] - x, resto["y"] - y) < 3.2 and ja.detenido
        b.hacer(lambda: [b.srv.policia_mover(0.1) for _ in range(60)])
        assert a.nada("detenido", 0.3)                           # ya la tienen: no se lo repiten
        a.enviar({"t": "busqueda", "nivel": 0, "fin": True})     # a comisaría: los que iban a por ella desaparecen
        a.leer("nivel_busqueda", filtro=lambda m: m["es"] == 0)
        assert not b.srv.agentes and not ja.detenido
        a.cerrar()
        c.cerrar()
    finally:
        b.parar()


def test_despistar_a_la_policia_lo_decide_el_servidor_y_salir_no_la_borra(tmp_path):
    b = Banco(tmp_path, policia="si")
    try:
        b.hacer(lambda: setattr(b.srv, "rng", __import__("random").Random(12)))
        a = Cli(b, "Ana")
        x, y = en_calle()
        a.estado(x=x, y=y)
        time.sleep(0.2)
        ja = b.srv.jugadores[a.id]
        a.enviar({"t": "busqueda", "nivel": 3})                  # revienta un furgón blindado: tres de golpe
        assert a.leer("nivel_busqueda")["es"] == 3
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(6)])
        assert len(patrullas_de(b, a.id)) == 1
        # mientras no hay nadie buscándola cerca, el tiempo corre; con una patrulla al lado, no
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(3)])
        assert 0 < ja.t_evasion <= 5
        pat = patrullas_de(b, a.id)[0]
        px, py, _ = b.srv.tr_pos(pat)
        a.estado(x=px + 20, y=py)
        time.sleep(0.2)
        b.hacer(b.srv.policia_pensar)
        assert ja.t_evasion == 0
        # con tres de búsqueda llegan hasta dos patrullas, no más
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(14)])
        assert len(patrullas_de(b, a.id)) == 2
        # sale del servidor con la policía encima y vuelve al momento: no se han olvidado de ella
        semilla = a.semilla
        a.cerrar()
        time.sleep(0.5)
        assert not patrullas_de(b, a.id)
        a = Cli(b, "Ana", semilla=semilla)
        assert a.leer("nivel_busqueda")["motivo"] == "vuelve"
        ja = b.srv.jugadores[a.id]
        assert ja.estrellas == 3
        # se va lejos de todos: a los pocos segundos la pierden, y las patrullas que la buscaban se retiran
        lx, ly = 3 * 90.0 + 45.0, 3 * 90.0 + 45.0
        a.estado(x=lx, y=ly)
        time.sleep(0.2)
        b.hacer(lambda: [b.srv.trafico.clear(), setattr(ja, "poli_enviada", True), setattr(ja, "t_poli", 99.0)])
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(15)])
        assert ja.estrellas == 3 and a.nada("nivel_busqueda", 0.2)       # a pie, con tres de búsqueda, dieciséis segundos
        b.hacer(lambda: [b.srv.policia_pensar() for _ in range(2)])
        assert a.leer("nivel_busqueda")["motivo"] == "perdida" and ja.estrellas == 0 and ja.puntos == 0
        a.cerrar()
    finally:
        b.parar()


def test_los_agentes_andan_por_la_calle_y_no_atraviesan_las_casas(tmp_path):
    b = Banco(tmp_path, policia="si")
    try:
        s = b.srv
        d = mundo()["mapas"]["puerto_bravo"]
        assert s._po_transitable("puerto_bravo", 180.0, 95.0) and s._po_transitable("puerto_bravo", 188.0, 300.0)      # calzada y acera
        cerrada = next((i, j) for i in range(d["nx"] - 1) for j in range(d["ny"] - 1) if [i, j] not in d["abiertos"])
        abierta = tuple(d["abiertos"][0])
        assert not s._po_transitable("puerto_bravo", cerrada[0] * 90.0 + 45, cerrada[1] * 90.0 + 45)
        assert s._po_transitable("puerto_bravo", abierta[0] * 90.0 + 45, abierta[1] * 90.0 + 45)
        assert not s._po_transitable("puerto_bravo", -30.0, 90.0)
        # un agente a un lado de una manzana cerrada y su objetivo al otro: llega rodeando, sin pisar la manzana
        i, j = cerrada
        a = {"id": 1, "m": "puerto_bravo", "x": i * 90.0 + 4, "y": j * 90.0 + 45}
        tx, ty = (i + 1) * 90.0 - 4, j * 90.0 + 50
        for _ in range(900):
            s._po_andar(a, tx, ty, 3.7, 0.1)
            assert s._po_transitable("puerto_bravo", a["x"], a["y"])
            if math.hypot(a["x"] - tx, a["y"] - ty) < 2:
                break
        assert math.hypot(a["x"] - tx, a["y"] - ty) < 2
    finally:
        b.parar()


def test_dos_juegos_viven_la_misma_persecucion(dos, tmp_path):
    a, b = dos
    bn = Banco(tmp_path, policia="si")
    try:
        bn.hacer(lambda: setattr(bn.srv, "rng", __import__("random").Random(13)))
        pa, pb = entrar(a, bn, "Ana"), entrar(b, bn, "Blas")
        assert pa.sv_policia_comun() and pb.sv_policia_comun()
        x, y = en_calle(pa.mundo.id)
        pa.teletransportar(x, y)
        pb.teletransportar(x + 6, y)
        assert hasta(lambda: pa.remotos and pb.remotos and all(r.visto for r in pa.remotos.values()) and all(r.visto for r in pb.remotos.values()), a, b)
        for p in (pa, pb):
            p.sv["protegido"] = 0
            p.j.salud = p.j.salud_max
        ja, jb = bn.srv.jugadores[pa.sv["id"]], bn.srv.jugadores[pb.sv["id"]]
        # Ana hace una gorda: el nivel de búsqueda se lo pone el servidor, y su juego lo dice
        pa.poner_busqueda(2)
        assert hasta(lambda: ja.estrellas == 2 and pa.j.estrellas == 2, a, b)
        assert "Nivel de búsqueda 2 de 5" in a.dicho()
        bn.hacer(lambda: [bn.srv.policia_pensar() for _ in range(6)])
        # la patrulla es del servidor: está en los dos juegos, con la sirena puesta, y ninguno pone policía por su cuenta
        con_sirena = lambda p: [v for v in p.sv["trafico"].values() if getattr(v, "tr_poli", False) and v.sirena is not None]
        assert hasta(lambda: con_sirena(pa) and con_sirena(pb), a, b)
        ambos(a, b, 40)
        assert not any(v.ia == "policia" for p in (pa, pb) for v in p.vehiculos)
        assert not any(q.tipo == "policia" and getattr(q, "po_id", None) is None for p in (pa, pb) for q in p.personas)
        # llega, para y se bajan los agentes: los mismos, en el mismo sitio, en los dos juegos. Van a por Ana, no a por Blas
        assert acercar_patrulla(bn, ja.id)
        assert hasta(lambda: len(pa.sv["agentes"]) == 2 and len(pb.sv["agentes"]) == 2, a, b)
        assert set(pa.sv["agentes"]) == set(pb.sv["agentes"])
        ident = next(iter(pa.sv["agentes"]))
        ea, eb = pa.sv["agentes"][ident], pb.sv["agentes"][ident]
        assert hasta(lambda: abs(ea.x - eb.x) < 1.5 and abs(ea.y - eb.y) < 1.5, a, b)
        assert all(q.hostil for q in pa.sv["agentes"].values()) and not any(q.hostil for q in pb.sv["agentes"].values())
        assert all(v.desplegado for v in con_sirena(pa))
        # le disparan: a Ana le baja la salud; a Blas, que lo oye todo, no
        s0, sb = pa.j.salud + pa.j.blindaje, pb.j.salud + pb.j.blindaje
        for _ in range(60):
            bn.hacer(lambda: [bn.srv.policia_mover(0.1) for _ in range(20)])
            ambos(a, b, 6)
            if pa.j.salud + pa.j.blindaje < s0:
                break
        assert pa.j.salud + pa.j.blindaje < s0 and pb.j.salud + pb.j.blindaje == sb
        # Blas tumba a uno de los agentes: cae también en el juego de Ana, y ahora a Blas también le buscan
        pb.danar_persona(eb, 500)
        assert eb.muerto and hasta(lambda: ea.muerto and jb.estrellas >= 2 and pb.j.estrellas >= 2, a, b)
        assert len(bn.srv.agentes) == 1
        # se arregla lo de los dos, y Ana hace una pequeña: con uno de búsqueda el agente que queda no dispara, la detiene
        pa.j.salud = pa.j.salud_max
        pa.limpiar_busqueda(False)
        pb.limpiar_busqueda(False)
        assert hasta(lambda: ja.estrellas == 0 and jb.estrellas == 0, a, b)
        pa.j.dinero = 0                                          # sin un euro no hay multa que pagar: al calabozo
        pa.poner_busqueda(1)
        assert hasta(lambda: ja.estrellas == 1 and pa.j.estrellas == 1, a, b)
        bn.hacer(bn.srv.policia_pensar)
        for _ in range(60):
            bn.hacer(lambda: [bn.srv.policia_mover(0.1) for _ in range(20)])
            ambos(a, b, 6)
            if pa.j.stats["detenciones"]:
                break
        assert pa.j.stats["detenciones"] == 1 and pa.j.estrellas == 0
        assert hasta(lambda: ja.estrellas == 0 and not bn.srv.agentes, a, b)
        a.saltar_dialogos()
        # Blas hace otra y se va lejos: quien decide que la ha despistado es el servidor
        pb.poner_busqueda(1)
        assert hasta(lambda: jb.estrellas == 1, a, b)
        pb.teletransportar(x + 400, y + 180)
        assert hasta(lambda: abs(jb.x - (x + 400)) < 2, a, b)
        bn.hacer(lambda: [setattr(jb, "poli_enviada", True), setattr(jb, "t_poli", 99.0)])
        bn.hacer(lambda: [bn.srv.policia_pensar() for _ in range(8)])
        ambos(a, b, 10)
        assert pb.j.estrellas == 1 and "Has despistado" not in b.dicho()
        bn.hacer(lambda: [bn.srv.policia_pensar() for _ in range(4)])
        assert hasta(lambda: pb.j.estrellas == 0 and "Has despistado a la policía" in b.dicho(), a, b)
        # y si el juego de alguien se da por buscado sin que el servidor lo sepa, a los pocos segundos se corrige
        pb.j.puntos_busqueda = 8.0
        ambos(a, b, 5)
        assert pb.j.estrellas == 3
        assert hasta(lambda: pb.j.estrellas == 0 and pb.j.puntos_busqueda == 0, a, b, 12.0)
    finally:
        for r in (a, b):
            if r.app.partida is not None:
                r.app.partida.sv_salir()
        bn.parar()
