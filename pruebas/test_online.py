"""Jugar con amigos: servidor propio, contraseña, presencia, mensajes, GPS, dinero y expulsión."""
import time

import pygame

from juego import red
from juego.menus import EntradaTexto, Menu


def _esperar(cond, robot=None, segundos=4.0):
    fin = time.time() + segundos
    while time.time() < fin:
        if robot is not None:
            robot.frames(2)
        if cond():
            return True
        time.sleep(0.02)
    return False


def _recibir(cli, tipo, segundos=4.0):
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            m = cli.entrantes.get(timeout=0.1)
        except Exception:
            continue
        if m.get("t") == tipo:
            return m
    return None


def test_direcciones():
    assert red.analizar_direccion("puertobravo://83.45.12.7:47810") == ("83.45.12.7", 47810)
    assert red.analizar_direccion("  PuertoBravo://casa.ejemplo.net  ") == ("casa.ejemplo.net", red.PUERTO)
    assert red.analizar_direccion("192.168.1.20:5000/") == ("192.168.1.20", 5000)
    for mala in ("", "puertobravo://", "host:abc", "host:99999", "a/b:1"):
        assert red.analizar_direccion(mala) is None, mala
    assert red.direccion("1.2.3.4", 5) == "puertobravo://1.2.3.4:5"
    assert red.direcciones_locales()


def test_servidor_con_contrasena_y_expulsion():
    srv = red.Servidor(0, "secreta")
    srv.iniciar()
    try:
        assert srv.protegido and srv.puerto > 0
        a = red.Cliente()
        ok, r = a.conectar("127.0.0.1", srv.puerto, "Ana", "secreta")
        assert ok and r["id"] and r["protegido"]
        mal = red.Cliente()
        ok, motivo = mal.conectar("127.0.0.1", srv.puerto, "Intruso", "otra")
        assert not ok and "contraseña" in motivo
        ok, motivo = red.Cliente().conectar("127.0.0.1", srv.puerto, "Sin clave", "")
        assert not ok
        b = red.Cliente()
        ok, r = b.conectar("127.0.0.1", srv.puerto, "Ana", "secreta")          # nombre repetido: se distingue
        assert ok and r["nombre"] == "Ana 2" and r["jugadores"] == [{"id": a.id, "nombre": "Ana"}]
        assert _recibir(a, "entra")["nombre"] == "Ana 2"
        b.enviar({"t": "chat", "texto": "hola  " + "x" * 500})
        m = _recibir(a, "chat")
        assert m["nombre"] == "Ana 2" and m["texto"].startswith("hola") and len(m["texto"]) <= 300
        b.enviar({"t": "estado", "e": {"m": "puerto_bravo", "x": 10.0, "y": 20.0, "r": 90, "v": "taxi", "s": 5, "basura": "no"}})
        e = None
        for _ in range(30):
            m = _recibir(a, "estados", 1.0)
            if m and str(b.id) in m["e"]:
                e = m["e"][str(b.id)]
                break
        assert e == {"m": "puerto_bravo", "x": 10.0, "y": 20.0, "r": 90, "v": "taxi", "s": 5}
        b.enviar({"t": "dinero", "a": a.id, "n": 10 ** 9})                   # la cantidad se acota
        assert _recibir(a, "dinero")["n"] == 100000
        assert srv.expulsar(b.id)
        assert _recibir(b, "expulsado") is not None
        assert _recibir(a, "sale")["nombre"] == "Ana 2"
        assert [n for _, n in srv.lista()] == ["Ana"]
    finally:
        srv.detener()
    assert _recibir(a, "cerrado") is not None or _recibir(a, "desconectado") is not None
    # sin contraseña, entra cualquiera; y lo que no es una partida se rechaza con un mensaje claro
    abierto = red.Servidor(0)
    abierto.iniciar()
    try:
        ok, _ = red.Cliente().conectar("127.0.0.1", abierto.puerto, "Libre")
        assert ok and not abierto.protegido
    finally:
        abierto.detener()
    ok, motivo = red.Cliente().conectar("127.0.0.1", 9, "Nadie", timeout=1)
    assert not ok and "No se pudo conectar" in motivo and "AdGuard" in motivo


def test_cortes_de_conexion_como_los_de_un_filtro_de_red(robot):
    """Un filtro (AdGuard, antivirus) que corta la primera conexión: se reintenta. Y un corte en mitad de la partida: se vuelve a entrar solo."""
    import socket
    import threading
    srv = red.Servidor(0)
    srv.iniciar()
    # un intermediario que corta en seco la primera conexión y deja pasar las siguientes
    escucha = socket.socket()
    escucha.bind(("127.0.0.1", 0))
    escucha.listen(8)
    puerto = escucha.getsockname()[1]
    vivos = []
    cuenta = {"n": 0}

    def puente(a, b):
        try:
            while True:
                d = a.recv(4096)
                if not d:
                    break
                b.sendall(d)
        except OSError:
            pass
        for x in (a, b):
            try:
                x.close()
            except OSError:
                pass

    def aceptar():
        while True:
            try:
                c, _ = escucha.accept()
            except OSError:
                return
            cuenta["n"] += 1
            if cuenta["n"] == 1:
                c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, __import__("struct").pack("hh", 1, 0))
                c.close()                                  # corte en seco, como haría un filtro
                continue
            s = socket.create_connection(("127.0.0.1", srv.puerto))
            vivos.append((c, s))
            threading.Thread(target=puente, args=(c, s), daemon=True).start()
            threading.Thread(target=puente, args=(s, c), daemon=True).start()
    threading.Thread(target=aceptar, daemon=True).start()
    p = robot.nueva_partida()
    try:
        ok, texto = p.unirse_a_amigo(f"127.0.0.1:{puerto}")
        assert ok and cuenta["n"] == 2, texto                   # el primer intento se cortó y el segundo entró
        # corte en mitad de la partida: vuelve a entrar sin intervención
        for c, s in vivos:
            c.close()
            s.close()
        del vivos[:]
        assert _esperar(lambda: "ya está recuperada" in robot.dicho(), robot, 8)
        assert p.online_activo() and cuenta["n"] == 3
        # si el anfitrión desaparece del todo, se avisa con la pista de los filtros y se sigue jugando
        escucha.close()
        for c, s in vivos:
            c.close()
            s.close()
        assert _esperar(lambda: not p.online_activo(), robot, 12)
        assert "Se ha perdido la conexión" in robot.dicho() and "AdGuard" in robot.dicho()
    finally:
        p.desconectar_online()
        srv.detener()
        try:
            escucha.close()
        except OSError:
            pass


def test_el_anfitrion_juega_y_un_amigo_entra(robot):
    p = robot.nueva_partida()
    j = p.j
    p.cfg["red_puerto"] = 0                                   # cualquier puerto libre
    ok, texto = p.abrir_a_amigos(0, "clave")
    assert ok and "protegida con contraseña" in texto and p.online_activo() and p.es_anfitrion()
    try:
        # el anfitrión sigue jugando con normalidad
        x0 = j.x
        robot.frames(40, mantener=(pygame.K_RIGHT,))
        assert j.x > x0 + 1
        amigo = red.Cliente()
        ok, r = amigo.conectar("127.0.0.1", p.servidor.puerto, "Marta", "clave")
        assert ok
        assert _esperar(lambda: len(p.remotos) == 1, robot)
        remoto = next(iter(p.remotos.values()))
        assert "Marta se ha unido" in robot.dicho()
        # el amigo se mueve en coche cerca: se le oye, sale en el radar y el GPS va hasta él
        amigo.enviar({"t": "estado", "e": {"m": p.mundo.id, "x": j.x + 30, "y": j.y, "r": 0, "v": "taxi", "s": 12}})
        assert _esperar(lambda: remoto.visto and remoto.canal is not None, robot)
        assert abs(remoto.x - (j.x + 30)) < 3 and remoto.veh == "taxi"
        assert any("Marta, tu amigo, al volante" in e[0] for e in p._radar_construir())
        assert "Marta, al volante" in p.donde_esta(remoto) and "este" in p.donde_esta(remoto)
        p.gps_a_amigo(remoto)
        assert p.gps and p.gps["nombre"] == "Marta"
        # a pie deja de sonar el motor
        amigo.enviar({"t": "estado", "e": {"m": p.mundo.id, "x": j.x + 31, "y": j.y, "r": 0, "v": None, "s": 0}})
        assert _esperar(lambda: remoto.veh is None and remoto.canal is None, robot)
        # en otra localidad: se dice dónde, y el GPS lleva hacia allí
        amigo.enviar({"t": "estado", "e": {"m": "villaseca", "x": 100, "y": 100, "r": 0, "v": None, "s": 0}})
        assert _esperar(lambda: remoto.mapa == "villaseca", robot)
        assert "en Villaseca" in p.donde_esta(remoto) and not any("Marta" in e[0] for e in p._radar_construir())
        p.gps_a_amigo(remoto)
        assert p.gps is not None
        # mensajes en los dos sentidos, también con un menú abierto
        from juego import menus_juego
        menus_juego.pausa(p)
        amigo.enviar({"t": "chat", "texto": "¿Dónde quedamos?"})
        assert _esperar(lambda: "Marta dice: ¿Dónde quedamos?" in robot.dicho(), robot)
        while robot.app.pila[-1] is not p:
            robot.tecla(pygame.K_ESCAPE)
        robot.tecla(pygame.K_F10)
        entrada = robot.app.pila[-1]
        assert isinstance(entrada, EntradaTexto)
        for letra in "En el bar":
            robot.tecla(pygame.K_a, unicode=letra)
        robot.tecla(pygame.K_BACKSPACE)
        robot.tecla(pygame.K_a, unicode="r")
        robot.tecla(pygame.K_RETURN)
        assert robot.app.pila[-1] is p
        assert _recibir(amigo, "chat")["texto"] == "En el bar"
        assert p.chat[-2:] == ["Marta: ¿Dónde quedamos?", "Tú: En el bar"]
        # dinero en los dos sentidos
        j.dinero = 1000
        assert p.dar_dinero_a(remoto, 500) and j.dinero == 500
        assert _recibir(amigo, "dinero")["n"] == 500
        amigo.enviar({"t": "dinero", "a": p.red.id, "n": 70})
        assert _esperar(lambda: j.dinero == 570, robot)
        j.dinero = 10
        assert not p.dar_dinero_a(remoto, 500) and j.dinero == 10
        # el menú del móvil lo muestra todo
        from juego import menus_online
        menus_online.amigos(p)
        m = robot.app.pila[-1]
        textos = [o.texto for o in m.opciones]
        assert isinstance(m, Menu) and "con contraseña" in textos[0] and "Jugadores: 2" in textos[0]
        assert any(t.startswith("Marta") for t in textos) and any("Cómo invitar" in t for t in textos) and textos[-1] == "Volver"
        # el anfitrión lo expulsa
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Marta"))
        robot.tecla(pygame.K_RETURN)
        sub = robot.app.pila[-1]
        sub.i = next(k for k, o in enumerate(sub.opciones) if "Expulsar" in o.texto)
        robot.tecla(pygame.K_RETURN)
        assert _recibir(amigo, "expulsado") is not None
        assert _esperar(lambda: not p.remotos, robot)
        while robot.app.pila[-1] is not p:
            robot.tecla(pygame.K_ESCAPE)
    finally:
        p.desconectar_online()
    assert not p.online_activo() and not p.es_anfitrion()
    robot.tecla(pygame.K_F10)
    assert "No estás jugando con nadie" in robot.dicho()


def test_unirse_a_la_partida_de_un_amigo(robot):
    p = robot.nueva_partida()
    srv = red.Servidor(0)
    srv.iniciar()
    otro = red.Cliente()
    otro.conectar("127.0.0.1", srv.puerto, "Hugo")
    try:
        ok, texto = p.unirse_a_amigo("no es una dirección://")
        assert not ok
        ok, texto = p.unirse_a_amigo(f"puertobravo://127.0.0.1:{srv.puerto}")
        assert ok and "Hugo" in texto and p.online_activo() and not p.es_anfitrion()
        assert p.cfg["red_ultima"] == f"puertobravo://127.0.0.1:{srv.puerto}"
        assert _recibir(otro, "entra") is not None
        otro.enviar({"t": "estado", "e": {"m": p.mundo.id, "x": p.j.x, "y": p.j.y + 20, "r": 0, "v": None, "s": 0}})
        otro.enviar({"t": "evento", "que": "claxon"})
        assert _esperar(lambda: next(iter(p.remotos.values())).visto, robot)
        # el anfitrión cierra: se avisa y se sigue jugando solo
        srv.detener()
        assert _esperar(lambda: not p.online_activo(), robot)
        assert "cerrado la partida" in robot.dicho() or "perdido la conexión" in robot.dicho()
        x0 = p.j.x
        robot.frames(30, mantener=(pygame.K_RIGHT,))
        assert p.j.x > x0
    finally:
        p.desconectar_online()
        srv.detener()


def test_entrada_de_texto_accesible(app):
    recibido = []
    e = EntradaTexto(app, "Tu nombre", recibido.append, inicial="Ab", maximo=5)
    app.abrir(e)
    assert "Tu nombre" in app.voz.registro[-1] and "Ab" in app.voz.registro[-1]
    app.inyectar(pygame.K_a, 0, "c")
    assert app.voz.registro[-1] == "c"
    app.inyectar(pygame.K_a, 0, "D")
    assert app.voz.registro[-1] == "D mayúscula"
    app.inyectar(pygame.K_SPACE, 0, " ")
    assert app.voz.registro[-1] == "espacio"
    app.inyectar(pygame.K_a, 0, "z")                           # ya no cabe
    assert e.texto == "AbcD "
    app.inyectar(pygame.K_BACKSPACE)
    assert app.voz.registro[-1] == "Borrado espacio"
    app.inyectar(pygame.K_UP)
    assert app.voz.registro[-1] == "AbcD"
    app.inyectar(pygame.K_RETURN)
    assert recibido == ["AbcD"] and app.pila[-1] is not e
    # una contraseña no se dice, y Escape no entrega nada
    s = EntradaTexto(app, "Contraseña", recibido.append, secreto=True)
    app.abrir(s)
    app.inyectar(pygame.K_a, 0, "x")
    assert app.voz.registro[-1] == "asterisco"
    app.inyectar(pygame.K_UP)
    assert "1 caracteres escritos" in app.voz.registro[-1] and "x" not in app.voz.registro[-1].replace("escritos", "")
    app.inyectar(pygame.K_ESCAPE)
    assert recibido == ["AbcD"]
