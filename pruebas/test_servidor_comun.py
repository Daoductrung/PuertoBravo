"""Lo que el servidor lleva por todos: el dinero de cada jugador y el tráfico de las calles."""
import time

import pygame

from test_enlinea import ambos, banco, dos, entrar, hasta, juntos        # noqa: F401  (banco y dos son fixtures)
from test_servidor import Banco, Cli, lejos_de_todo, mundo


# ------------------------------------------------------------------ economía
def test_el_dinero_lo_lleva_el_servidor(tmp_path):
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=500)
    try:
        a = Cli(b, "Ana")
        a.estado(di=300, ba=100)                                 # empieza con lo suyo
        time.sleep(0.2)
        ja = b.srv.jugadores[a.id]
        assert ja.saldo == 400
        a.estado(di=250, ba=100)                                 # gastar, siempre
        time.sleep(0.2)
        assert ja.saldo == 350
        # se da un millón a sí misma: el servidor no lo reconoce, y se lo dice
        a.estado(di=1000250, ba=100)
        quita = a.leer("saldo")
        assert quita["quita"] > 990000 and ja.saldo < 3000 and ja.dinero < 3000
        assert any("no se le reconocen" in t for t in b.lineas)
        # con ese dinero que no existe no se compra nada de lo que es de todos
        a.enviar({"t": "banda_crear", "nombre": "Las Listas"})
        assert "No te llega" in a.leer("aviso", filtro=lambda m: "llega" in m["texto"])["texto"]
        # lo ganado poco a poco, dentro del tanto por hora, sí vale
        b.hacer(lambda: (setattr(ja, "margen", 800.0), setattr(ja, "saldo", 350), setattr(ja, "t_saldo", 0.0)))
        a.cola.clear()
        a.estado(di=850, ba=100)
        time.sleep(0.3)
        assert ja.saldo == 950 and a.nada("saldo", 0.3)
        # una misión de la historia: su recompensa entera queda justificada, una sola vez
        paga = mundo()["misiones"]["m04"]["dinero"]
        b.hacer(lambda: setattr(ja, "margen", 0.0))
        a.enviar({"t": "mision_ok", "id": "m04"})
        a.estado(di=850 + paga, ba=100)
        time.sleep(0.3)
        assert ja.saldo == 950 + paga and a.nada("saldo", 0.3)
        a.enviar({"t": "mision_ok", "id": "m04"})                # decirlo dos veces no la paga dos veces
        b.hacer(lambda: setattr(ja, "margen", 0.0))
        a.estado(di=850 + 2 * paga, ba=100)
        assert a.leer("saldo")["quita"] >= paga - 5
        # lo que da otro jugador también está justificado
        c = Cli(b, "Ciro")
        c.estado(di=400, ba=0)
        time.sleep(0.2)
        b.hacer(lambda: (setattr(ja, "margen", 0.0), setattr(ja, "saldo", 1000), setattr(ja, "t_saldo", 0.0)))
        a.cola.clear()
        c.enviar({"t": "dinero", "a": a.id, "n": 300})
        assert a.leer("dinero")["n"] == 300
        a.estado(di=1200, ba=100)
        time.sleep(0.3)
        assert ja.saldo == 1300 and a.nada("saldo", 0.3)
        a.enviar({"t": "guardar", "p": {"jugador": {"dinero": 1200, "banco": 100}}, "ya": True})
        a.leer("guardado")
    finally:
        b.parar()
    b = Banco(tmp_path, economia="si")                           # y al volver, manda lo que el servidor tiene apuntado
    try:
        a2 = Cli(b, "Ana", semilla=a.semilla)
        assert a2.ok["saldo"] == 1300
    finally:
        b.parar()


def test_el_juego_obedece_al_saldo_del_servidor(robot, tmp_path):
    b = Banco(tmp_path, economia="si", ganancia_hora=3600)
    try:
        p = entrar(robot, b, "Ana")
        robot.frames(10)
        time.sleep(0.3)
        inicial = p.j.dinero + p.j.banco
        p.j.dinero += 500000                                     # dinero que no sale de ningún sitio
        fin = time.time() + 8
        while time.time() < fin and p.j.dinero + p.j.banco > inicial + 5000:
            robot.frames(3)
            time.sleep(0.02)
        assert p.j.dinero + p.j.banco <= inicial + 5000 and "El servidor no reconoce" in robot.dicho()
        # una misión de verdad sí se cobra entera
        import test_misiones
        m = next(x for x in p.datos["misiones"] if x["id"] == "m01")
        antes = p.j.dinero
        b.hacer(lambda: [setattr(q, "margen", 0.0) for q in b.srv.jugadores.values()])
        test_misiones._jugar_mision(robot, m)
        robot.frames(30)
        time.sleep(0.4)
        robot.frames(10)
        assert p.j.dinero >= antes + int(m["recompensa"].get("dinero", 0)) and "m01" in p.completadas
        p.sv_salir()
    finally:
        b.parar()


# ------------------------------------------------------------- tráfico común
def test_el_trafico_lo_lleva_el_servidor(tmp_path):
    b = Banco(tmp_path, trafico="si", trafico_max=6)
    try:
        b.hacer(lambda: setattr(b.srv, "rng", __import__("random").Random(8)))
        a = Cli(b, "Ana")
        assert a.ok["servidor"]["trafico"] and "luces" in a.ok["hora"]
        b.hacer(lambda: [b.srv.trafico_pensar() for _ in range(5)])
        assert not b.srv.trafico                                 # sin nadie situado, no hay coches
        x, y = lejos_de_todo()
        a.estado(x=x, y=y)
        time.sleep(0.2)
        b.hacer(lambda: [b.srv.trafico_pensar() for _ in range(30)])
        coches = list(b.srv.trafico.values())
        assert len(coches) == 6 and all(c["m"] == "puerto_bravo" for c in coches)
        tr = a.leer("estados", filtro=lambda m: m.get("tr"))["tr"]
        assert all(len(f) == 6 and f[1] in mundo()["modelos"] for f in tr)
        # circulan: por su carril, y cambian de calle en los cruces
        antes = {c["id"]: b.srv.tr_pos(c)[:2] for c in coches}
        cruces = {c["id"]: (c["i"], c["j"]) for c in coches}
        b.hacer(lambda: [b.srv.trafico_mover(0.1) for _ in range(900)])
        movidos = [c for c in coches if c["id"] in b.srv.trafico and b.srv.tr_pos(c)[:2] != antes[c["id"]]]
        assert len(movidos) >= 5 and any((c["i"], c["j"]) != cruces[c["id"]] for c in movidos)
        for c in movidos:
            px, py, _ = b.srv.tr_pos(c)
            assert min(abs(px % 90), 90 - abs(px % 90)) <= 3.01 or min(abs(py % 90), 90 - abs(py % 90)) <= 3.01      # siempre sobre una calle
        # frenan si tienen a alguien delante, y entonces se les puede quitar el coche
        c = movidos[0]
        cx, cy, _ = b.srv.tr_pos(c)
        dx, dy = __import__("servidor.trafico", fromlist=["x"]).DIRS[c["d"]]
        a.estado(x=cx + dx * 6, y=cy + dy * 6)                   # Ana se le planta delante
        time.sleep(0.2)
        b.hacer(lambda: [b.srv.trafico_mover(0.1) for _ in range(30)])
        assert c["vel"] == 0.0
        a.cola.clear()
        a.enviar({"t": "tr_robar", "id": c["id"]})
        ok = a.leer("veh_ok")
        assert ok["robado"] and ok["tr"] == c["id"] and c["id"] not in b.srv.trafico and ok["id"] in b.srv.vehiculos
        # y a otro se le destroza
        d = next(q for q in b.srv.trafico.values())
        a.enviar({"t": "tr_dano", "id": d["id"], "n": 5000})
        assert a.leer("tr_revienta")["id"] == d["id"] and d["id"] not in b.srv.trafico
        # si Ana se va de la localidad, aquí deja de haber coches
        a.estado(mapa="villaseca", x=50, y=50)
        time.sleep(0.2)
        b.hacer(lambda: [b.srv.trafico_pensar() for _ in range(3)])
        assert all(q["m"] == "villaseca" for q in b.srv.trafico.values())
    finally:
        b.parar()


def test_los_dos_jugadores_oyen_los_mismos_coches_y_uno_se_lleva_uno(dos, tmp_path):
    a, b = dos
    bn = Banco(tmp_path, trafico="si", trafico_max=5)
    try:
        bn.hacer(lambda: setattr(bn.srv, "rng", __import__("random").Random(3)))
        pa, pb = entrar(a, bn, "Ana"), entrar(b, bn, "Blas")
        rb, ra = juntos(pa, pb, a, b, d=8.0)
        assert pa.sv_trafico_comun()
        bn.hacer(lambda: [bn.srv.trafico_pensar() for _ in range(30)])
        assert hasta(lambda: len(set(pa.sv["trafico"]) & set(pb.sv["trafico"])) >= 3, a, b), (
            sorted(pa.sv["trafico"]), sorted(pb.sv["trafico"]), len(bn.srv.trafico), [bn.srv.tr_pos(c)[:2] for c in bn.srv.trafico.values()], pa.pos(), a.dicho()[-200:])
        # ninguno pone tráfico propio: todo lo que circula es del servidor
        for _ in range(40):
            pa._poblar()
            pb._poblar()
        assert not any(v.ia == "trafico" for v in pa.vehiculos + pb.vehiculos)
        # el mismo coche está en el mismo sitio en los dos juegos
        ident = min(set(pa.sv["trafico"]) & set(pb.sv["trafico"]), key=lambda k: pa.sv["trafico"][k].dist(*pa.pos()))
        assert hasta(lambda: ident in pb.sv["trafico"] and abs(pa.sv["trafico"][ident].x - pb.sv["trafico"][ident].x) < 6
                     and abs(pa.sv["trafico"][ident].y - pb.sv["trafico"][ident].y) < 6, a, b)
        # los semáforos son los mismos
        assert abs((pa.mundo.desfase_luces + pa.t) - (pb.mundo.desfase_luces + pb.t)) < 2.0
        # Ana se planta delante de uno, frena, y se lo lleva con la F: el conductor sale corriendo
        c = bn.srv.trafico[ident]
        cx, cy, _ = bn.srv.tr_pos(c)
        from servidor.trafico import DIRS
        dx, dy = DIRS[c["d"]]
        pa.j.x, pa.j.y = cx + dx * 5, cy + dy * 5
        assert hasta(lambda: c["vel"] == 0.0 and abs(pa.sv["trafico"][ident].x - cx) < 4 and abs(pa.sv["trafico"][ident].vel) < 1, a, b, 12)
        coche = pa.sv["trafico"][ident]
        pa.j.x, pa.j.y = coche.x + 2, coche.y + 1
        a.tecla(pygame.K_f)
        assert hasta(lambda: pa.j.veh is coche, a, b)
        assert ident not in pa.sv["trafico"] and getattr(coche, "id_red", None) is not None and any(q.nombre == "Conductor" for q in pa.personas)
        # para Blas deja de ser tráfico y pasa a ser el coche que conduce Ana
        assert hasta(lambda: ident not in pb.sv["trafico"] and ra.veh == coche.modelo["id"], a, b)
    finally:
        for r in (a, b):
            if r.app.partida is not None:
                r.app.partida.sv_salir()
        bn.parar()


# -------------------------------------------------------------- policía común
def test_la_policia_que_persigue_a_uno_esta_tambien_en_el_juego_del_otro(dos, banco):
    from juego.entidades import Persona
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=10.0)
    x, y = pa.pos()
    # a Ana la busca la policía: en su juego hay una patrulla y dos agentes
    pa.poner_busqueda(3)
    patrulla = pa.crear_vehiculo("patrulla", x + 30, y, 3, "policia")
    agentes = []
    for k in range(2):
        g = Persona("policia", x + 12 + 2 * k, y + 3)
        g.hostil, g.estado, g.arma = True, "ataca", "pistola"
        pa.personas.append(g)
        agentes.append(g)
    assert hasta(lambda: len(getattr(ra, "poli", {})) >= 3, a, b)
    ecos = ra.poli
    eco_v = ecos[("v", patrulla.id)]
    eco_p = ecos[("p", agentes[0].id)]
    assert eco_v in pb.vehiculos and eco_v.sirena is not None and eco_p in pb.personas and eco_p.nombre == "Policía"
    assert hasta(lambda: abs(eco_p.x - agentes[0].x) < 3 and abs(eco_v.x - patrulla.x) < 8, a, b)
    # Blas no puede llevarse esa patrulla, pero sí meterse con los agentes: lo que le haga a uno, le pasa en el juego de Ana
    pb.j.x, pb.j.y = eco_v.x + 2, eco_v.y + 1
    b.tecla(pygame.K_f)
    assert "lleno de policías" in b.dicho() and pb.j.veh is None
    salud = agentes[0].salud
    pb.danar_persona(eco_p, 20)
    assert hasta(lambda: agentes[0].salud <= salud - 20, a, b)
    pb.danar_persona(eco_p, 500)
    assert hasta(lambda: agentes[0].muerto, a, b)
    assert pb.j.estrellas >= 1                                   # y a Blas, por meterse, también le buscan
    # cuando a Ana dejan de buscarla, la policía desaparece también del juego de Blas
    pa._fin_persecucion()
    assert hasta(lambda: not ra.poli and eco_v.muerto and eco_p not in pb.personas, a, b)
