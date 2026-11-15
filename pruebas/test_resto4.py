"""Puerto automático del router, siete y media, nueva partida conservando lo ganado y modificadores."""
import http.server
import os
import random
import threading

import pygame

from juego.menus import Menu, Opcion


class RouterFalso(http.server.BaseHTTPRequestHandler):
    pedidos = []
    permite = True

    def log_message(self, *a):
        pass

    def do_GET(self):
        xml = ("<root><device><serviceList><service><serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>"
               "<controlURL>/ctl</controlURL></service></serviceList></device></root>") if self.permite else "<root></root>"
        datos = xml.encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)
        self.wfile.flush()

    def do_POST(self):
        cuerpo = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        RouterFalso.pedidos.append((self.headers.get("SOAPAction"), cuerpo))
        self.send_response(200)
        self.send_header("Content-Length", "5")
        self.end_headers()
        self.wfile.write(b"<ok/>")
        self.wfile.flush()


def test_abrir_el_puerto_del_router(robot):
    from juego import upnp
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RouterFalso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/desc.xml"
    try:
        RouterFalso.pedidos.clear()
        RouterFalso.permite = True
        ok, datos, motivo = upnp.abrir(47810, buscar=lambda: [url])
        assert ok and motivo == "" and datos["puerto"] == 47810 and datos["control"].endswith("/ctl")
        accion, cuerpo = RouterFalso.pedidos[-1]
        assert "AddPortMapping" in accion and "<NewExternalPort>47810</NewExternalPort>" in cuerpo and "<NewProtocol>TCP</NewProtocol>" in cuerpo
        assert "<NewInternalClient>127.0.0.1</NewInternalClient>" in cuerpo
        assert upnp.cerrar(datos) and "DeletePortMapping" in RouterFalso.pedidos[-1][0]
        # un router que no lo ofrece, y una red sin router que responda
        RouterFalso.permite = False
        assert upnp.abrir(47810, buscar=lambda: [url]) == (False, None, "no_permite")
        assert upnp.abrir(47810, buscar=lambda: []) == (False, None, "no_responde")
        assert upnp.abrir(47810, buscar=lambda: ["http://127.0.0.1:9/nada"])[0] is False
        assert not upnp.cerrar(None) and set(upnp.FRASES) == {"", "no_responde", "no_permite", "rechazado"}
        # en el juego: al abrir la partida lo intenta en segundo plano y lo dice; al cerrarla, cierra el puerto
        RouterFalso.permite = True
        RouterFalso.pedidos.clear()
        p = robot.nueva_partida()
        p.upnp_en_pruebas = lambda: [url]
        ok, texto = p.abrir_a_amigos(47990)
        assert ok
        p._upnp_hilo.join(8)
        robot.frames(3)
        assert "He abierto el puerto en tu router" in robot.dicho() and p._upnp["puerto"] == 47990
        p.desconectar_online()
        for _ in range(40):
            if any("DeletePortMapping" in a for a, _ in RouterFalso.pedidos):
                break
            threading.Event().wait(0.1)
        assert any("DeletePortMapping" in a for a, _ in RouterFalso.pedidos) and p._upnp is None
        # con la opción quitada no se toca el router
        RouterFalso.pedidos.clear()
        p.cfg["red_upnp"] = False
        ok, texto = p.abrir_a_amigos(47991)
        assert ok and not RouterFalso.pedidos
        p.desconectar_online()
        p.cfg["red_upnp"] = True
    finally:
        srv.shutdown()


class Puestas:
    """Un azar que deja las cartas en el orden que se le dice: la primera de la lista es la primera que sale."""

    def __init__(self, lista):
        self.lista = lista

    def shuffle(self, mazo):
        nombres = [n for n, _ in self.lista]
        mazo[:] = [c for c in mazo if c[0] not in nombres] + list(reversed(self.lista))


def test_siete_y_media(robot):
    from juego import menus_juego, sistemas
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    mazo = sistemas.baraja(random.Random(1))
    assert len(mazo) == 40 and len({n for n, _ in mazo}) == 40 and sum(v for _, v in mazo) == 4 * (28 + 1.5)
    assert sistemas._puntos_txt(7.5) == "7 y media" and sistemas._puntos_txt(0.5) == "media" and sistemas._puntos_txt(4.0) == "4"

    def jugar(lista, pulsaciones):
        j.dinero = 1000
        m, est = sistemas.siete_y_media(p, Menu, Opcion, azar=Puestas(lista))
        m.i = 1                                                               # apostar 50
        robot.tecla(pygame.K_RETURN)
        for i in pulsaciones:
            m.i = i
            robot.tecla(pygame.K_RETURN)
        fin = est["fin"]
        app.cerrar(m)
        return j.dinero, fin
    # 7 y luego una sota: siete y media. Te plantas. La banca saca 7 y un 2: se pasa. Triple.
    dinero, fin = jugar([("7 de oros", 7.0), ("sota de copas", 0.5), ("7 de copas", 7.0), ("2 de oros", 2.0)], [0, 1])
    assert fin and dinero == 1000 - 50 + 150 and "el doble por hacer siete y media" in " ".join(app.voz.registro[-3:])
    # te pasas: pierdes la apuesta
    dinero, fin = jugar([("7 de oros", 7.0), ("5 de copas", 5.0)], [0])
    assert fin and dinero == 950 and "te has pasado" in " ".join(app.voz.registro[-3:])
    # la banca te iguala: gana ella
    dinero, fin = jugar([("5 de oros", 5.0), ("5 de copas", 5.0)], [1])
    assert fin and dinero == 950 and "La banca gana" in " ".join(app.voz.registro[-3:])
    # ganar normal paga el doble
    dinero, fin = jugar([("6 de oros", 6.0), ("5 de copas", 5.0), ("4 de copas", 4.0)], [1])
    assert fin and dinero == 1050
    # está en el menú de los bares, una sola vez, junto con el recorrido
    bar = p.lugares["bar_gaviota"]
    p.teletransportar(bar.x, bar.y)
    menus_juego.lugar(p, bar)
    m = app.pila[-1]
    m.refrescar(False)
    textos = [o.texto for o in m.opciones]
    assert textos.count("Jugar a la siete y media") == 1 and textos.count("Recorrer el local por dentro") == 1


def test_nueva_partida_conservando_y_modificadores(robot):
    from juego import menus_juego
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    j.dinero, j.banco = 54321, 1000
    p.dar_arma("escopeta", 20)
    j.hab["punteria"] = 500.0
    j.territorios.append("x")
    p.completadas.append("m01")
    p.decisiones["a"] = {"opcion": 0}
    previos = {r: menus_juego.leer_ranura(r) is not None for r in menus_juego.RANURAS}
    assert not previos["5"], "la ranura 5 tiene una partida del usuario: la prueba no la toca"
    assert menus_juego.escribir_ranura(p, "5")
    try:
        menus_juego.partida_mas(app)
        m = app.pila[-1]
        m.i = len(m.opciones) - 2 if m.opciones[-1].texto == "Volver" else len(m.opciones) - 1       # la ranura 5 es la última
        robot.tecla(pygame.K_RETURN)
        robot.saltar_dialogos()
        q = app.partida
        assert q is not p and q.j.dinero == 54321 and q.j.banco == 1000 and "escopeta" in q.j.armas and q.j.hab["punteria"] == 500.0
        assert q.completadas == [] and q.j.territorios == [] and q.decisiones == {} and q.j.ciclo == 1 and "vuelta número 2" in robot.dicho()
        # los enemigos aguantan más en la segunda vuelta, y más aún con el modificador
        grupo = {"enemigos": [{"n": 1, "tipo": "Matón", "arma": "pistola", "salud": 100}]}
        l = q.lugares["plaza_vieja"]
        q.mision = {"enemigos": [], "generado": False, "quedan": None}
        q._generar_enemigos(grupo, l)
        assert abs(q.mision["enemigos"][0].salud - 115.0) < 0.01
        app.cfg["mod_enemigos"] = True
        q.mision = {"enemigos": [], "generado": False, "quedan": None}
        q._generar_enemigos(grupo, l)
        assert abs(q.mision["enemigos"][0].salud - 172.5) < 0.01
        q.personas[:] = [e for e in q.personas if e.tag != "mision"]
        q.mision = None
        # misiones peor pagadas y más experiencia
        app.cfg["mod_dinero"] = True
        dinero = q.j.dinero
        q.mision = {"def": {"id": "zz", "titulo": "Prueba", "pasos": [], "recompensa": {"dinero": 400}, "repetible": True}, "paso": 0, "enemigos": []}
        q._completar_mision()
        assert q.j.dinero == dinero + 200
        xp = q.j.hab["conduccion"]
        q.ganar_xp("conduccion", 10)
        assert abs(q.j.hab["conduccion"] - xp - 15.0) < 1e-6                  # dos modificadores: la mitad más
    finally:
        app.cfg["mod_enemigos"] = app.cfg["mod_dinero"] = False
        for r in menus_juego._archivos_validos("5"):
            os.remove(r)
