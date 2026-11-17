"""El servidor no tiene un tope fijo de jugadores: lo mismo vale para dos que para cientos.

Los clientes de aquí son muy ligeros (solo saludan y mandan su posición) y no firman de verdad, para poder meter
cientos en unos segundos: lo que se prueba es que el servidor no tiene límites escondidos ni se viene abajo con mucha
gente, no la identidad, que se prueba en test_servidor.py.
"""
import functools
import hashlib
import json
import os
import socket
import time

import pytest

from servidor import nucleo, trafico
from test_servidor import Banco, Cli, mundo


def con_reintento(prueba):
    """En este equipo, un filtro de red se traga de tarde en tarde lo último que se manda por una conexión local antes de
    cerrarla: ni llega el mensaje ni llega el cierre (pasa igual con dos sockets a pelo, sin el servidor de por medio).
    Las pruebas que esperan el mensaje de una expulsión se repiten una vez si ese mensaje no llega; cualquier otro
    fallo es un fallo."""
    @functools.wraps(prueba)
    def envoltura(tmp_path, **mas):
        os.makedirs(tmp_path / "a", exist_ok=True)
        try:
            return prueba(tmp_path / "a", **mas)
        except AssertionError as e:
            if "no llega" not in str(e):
                raise
        os.makedirs(tmp_path / "b", exist_ok=True)
        return prueba(tmp_path / "b", **mas)
    return envoltura


class Ligero:
    """Un cliente mínimo: saluda sin firmar de verdad (la comprobación está anulada en estas pruebas)."""

    def __init__(self, banco, nombre, **hola):
        self.nombre = nombre
        d = {"t": "hola", "v": nucleo.VERSION_RED, "nombre": nombre, "pub": hashlib.sha256(nombre.encode()).hexdigest(),
             "huella": mundo()["huella"], "juego": mundo()["version"]}
        d.update(hola)
        # El juego de verdad reintenta si la conexión se queda muda nada más abrirla (un filtro de red, en este equipo, se
        # traga a veces lo último antes de un cierre, como el motivo de un rechazo). Este cliente, también.
        for intento in range(3):
            self.ok = self.rechazo = None
            self.buf = b""
            self.s = socket.create_connection(("127.0.0.1", banco.puerto), timeout=10)
            try:
                self.enviar(d)
            except OSError:
                pass                                              # el servidor ya ha rechazado y cortado: el motivo, si llega, está por leer
            r = self.linea(4.0 if intento < 2 else 10.0)
            if r and r["t"] == "reto":
                self.enviar({"t": "firma", "f": "00"})
                r = self.linea(4.0 if intento < 2 else 10.0)
            if r and r["t"] == "ok":
                self.ok, self.id = r, r["id"]
                return
            if r:
                self.rechazo = r.get("motivo")
                return
            self.cerrar()

    def enviar(self, obj):
        self.s.sendall(json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n")

    def linea(self, espera=10.0):
        fin = time.time() + espera
        while b"\n" not in self.buf:
            self.s.settimeout(max(0.01, fin - time.time()))
            try:
                trozo = self.s.recv(262144)
            except (socket.timeout, OSError):
                return None
            if not trozo:
                return None
            self.buf += trozo
        linea, self.buf = self.buf.split(b"\n", 1)
        return json.loads(linea.decode("utf-8"))

    def leer(self, tipo, espera=8.0, filtro=None):
        fin = time.time() + espera
        while time.time() < fin:
            m = self.linea(fin - time.time())
            if m is None:
                break
            if m["t"] == tipo and (filtro is None or filtro(m)):
                return m
        raise AssertionError("no llega " + tipo)

    def estado(self, x=100.0, y=100.0, mapa="puerto_bravo", **mas):
        e = {"m": mapa, "x": x, "y": y, "r": 0, "v": None, "s": 0, "sa": 100, "di": 100, "ar": "punos", "b": None}
        e.update(mas)
        self.enviar({"t": "estado", "e": e})

    def cerrar(self):
        try:
            self.s.close()
        except OSError:
            pass


@pytest.fixture
def sin_firma(monkeypatch):
    monkeypatch.setattr(nucleo.firma, "verificar", lambda *a: True)


def _dentro(banco):
    return banco.hacer(banco.srv._cuantos)


def test_con_cero_no_hay_limite_y_caben_cientos(tmp_path, sin_firma):
    """max_jugadores = 0 quiere decir sin límite. Entran 250 a la vez, todos en la misma localidad, y el servidor sigue atendiendo."""
    banco = Banco(tmp_path, max_jugadores=0, radio_detalle=400)
    gente = []
    try:
        t0 = time.time()
        for n in range(250):
            c = Ligero(banco, "Jugador %03d" % n)
            assert c.ok, (n, c.rechazo)
            gente.append(c)
        assert _dentro(banco) == 250
        assert gente[-1].ok["servidor"]["max_jugadores"] == 0 and len(gente[-1].ok["jugadores"]) == 249
        # repartidos por la localidad, de 20 en 20 metros en una rejilla
        for n, c in enumerate(gente):
            c.estado(x=40.0 + 60.0 * (n % 16), y=40.0 + 60.0 * (n // 16))
        time.sleep(1.5)
        ultimo = gente[-1]
        # al detalle le llegan los que tiene cerca; una vez por segundo, todos los de la localidad
        cerca = ultimo.leer("estados", filtro=lambda m: 0 < len(m["e"]) < 249)
        todos = ultimo.leer("estados", espera=4, filtro=lambda m: len(m["e"]) == 249)
        assert str(ultimo.id) not in todos["e"] and str(ultimo.id) not in cerca["e"]
        # y el servidor sigue contestando a todo con normalidad
        t1 = time.time()
        ultimo.enviar({"t": "quien"})
        assert len(ultimo.leer("quien")["e"]) == 250 and time.time() - t1 < 5
        assert "Hay 250" in banco.hacer(banco.srv.orden, "jugadores")
        assert "sin límite" in banco.hacer(banco.srv.orden, "estado")
        # un aviso a todos se escribe una sola vez, no una por jugador
        escritos = []
        original = nucleo.Servidor._codificar
        banco.srv._codificar = lambda obj: (escritos.append(obj.get("t")), original(obj))[1]
        banco.hacer(banco.srv.orden, "aviso Probando con mucha gente")
        assert escritos.count("aviso") == 1
        assert "Probando" in gente[3].leer("aviso")["texto"]
        assert time.time() - t0 < 90
    finally:
        for c in gente:
            c.cerrar()
        banco.parar()


def test_el_tope_se_respeta_con_valores_pequenos_y_grandes(tmp_path, sin_firma):
    banco = Banco(tmp_path, max_jugadores=2)
    gente = []
    try:
        jefa = Ligero(banco, "Jefa")                           # la primera cuenta administra
        gente.append(jefa)
        gente.append(Ligero(banco, "Dos"))
        tres = Ligero(banco, "Tres")
        assert jefa.ok["admin"] and "lleno" in tres.rechazo and _dentro(banco) == 2
        # quien administra entra aunque esté lleno: si no, no podría poner orden
        jefa.cerrar()
        time.sleep(0.4)
        gente.append(Ligero(banco, "Tres"))
        assert gente[-1].ok and _dentro(banco) == 2
        vuelve = Ligero(banco, "Jefa")
        assert vuelve.ok and _dentro(banco) == 3
        gente.append(vuelve)
        # se sube el tope con el servidor en marcha, a un valor grande: entran los que antes no cabían
        aplicadas, reinicio = banco.hacer(banco.srv.aplicar_config, {"max_jugadores": 120})
        assert aplicadas == ["max_jugadores"] and not reinicio
        for n in range(117):
            c = Ligero(banco, "Extra %03d" % n)
            assert c.ok, (n, c.rechazo)
            gente.append(c)
        assert _dentro(banco) == 120 and "lleno" in Ligero(banco, "Sobra").rechazo
        assert "de 120" in banco.hacer(banco.srv.orden, "estado")
    finally:
        for c in gente:
            c.cerrar()
        banco.parar()


def test_limite_de_conexiones_por_direccion(tmp_path, sin_firma):
    banco = Banco(tmp_path, conexiones_por_ip=3)
    gente = []
    try:
        gente = [Ligero(banco, "Uno"), Ligero(banco, "Dos"), Ligero(banco, "Tres")]
        assert all(c.ok for c in gente)
        cuarto = Ligero(banco, "Cuatro")
        assert "demasiadas conexiones" in cuarto.rechazo
        gente[0].cerrar()                                       # en cuanto uno se va, vuelve a haber sitio
        time.sleep(0.5)
        gente.append(Ligero(banco, "Cuatro"))
        assert gente[-1].ok
        assert banco.hacer(lambda: dict(banco.srv.por_ip)) == {"127.0.0.1": 3}
        # la dirección no se apunta en ningún sitio: ni en el registro, ni en lo que ve quien administra
        assert not any("127.0.0.1" in l for l in banco.lineas)
        assert all(g["ip"] is None for g in banco.hacer(banco.srv.resumen)["jugadores"])
        banco.hacer(lambda: banco.srv.cfg.__setitem__("registro_ip", "si"))
        assert all(g["ip"] == "127.0.0.1" for g in banco.hacer(banco.srv.resumen)["jugadores"])
    finally:
        for c in gente:
            c.cerrar()
        banco.parar()
    assert not banco.srv.por_ip or all(v >= 0 for v in banco.srv.por_ip.values())


@con_reintento
def test_mensaje_del_dia_vetados_e_inactividad(tmp_path, sin_firma):
    banco = Banco(tmp_path, mensaje_dia="El sábado, carrera en el puerto.", vetados="Pesado, Otro Pesado", inactividad_minutos=1)
    try:
        a = Ligero(banco, "Ana")
        assert "Mensaje del día: El sábado" in a.leer("aviso")["texto"]
        assert "No puedes entrar" in Ligero(banco, "pesado").rechazo           # por nombre, sin mirar mayúsculas
        b = Ligero(banco, "Blas")
        a.estado()
        b.estado(x=200.0)
        time.sleep(0.3)
        # el mensaje del día se cambia con el servidor en marcha, y lo oyen los que están
        assert "cambiado" in banco.hacer(banco.srv.orden, "mensaje Hoy se cierra a las doce.")
        assert b.leer("aviso", filtro=lambda m: "Hoy se cierra" in m["texto"])
        # Blas lleva más de un minuto sin hacer nada: fuera. Ana administra y a ella no se la saca. Mandar la posición
        # sin moverse no cuenta como actividad: lo hace el juego solo.
        def envejecer():
            for j in banco.srv.jugadores.values():
                j.t_actividad -= 70
        banco.hacer(envejecer)
        b.estado(x=200.0)
        fuera = b.leer("expulsado", espera=6)
        assert "sin hacer nada" in fuera["motivo"]
        a.enviar({"t": "ping"})
        assert a.leer("pong")
        assert any("sin hacer nada" in l for l in banco.lineas)
        # quien se mueve no está parado
        c = Ligero(banco, "Ciro")
        c.estado(x=10.0)
        time.sleep(0.3)

        def parado_y_se_mueve():
            j = next(j for j in banco.srv.jugadores.values() if j.nombre == "Ciro")
            j.t_actividad -= 70
            banco.srv._m_estado(j, {"e": {"m": "puerto_bravo", "x": 40.0, "y": 100.0}})
            return time.monotonic() - j.t_actividad
        assert banco.hacer(parado_y_se_mueve) < 5
        time.sleep(1.6)
        c.enviar({"t": "ping"})
        assert c.leer("pong")
        # vetar un nombre desde la configuración, con el servidor en marcha, saca a quien esté dentro
        banco.hacer(banco.srv.aplicar_config, {"vetados": "Ciro"})
        assert "sacado" in c.leer("expulsado")["motivo"]
    finally:
        banco.parar()


def test_el_trafico_y_los_peatones_crecen_con_las_zonas_ocupadas(tmp_path, sin_firma):
    """Con jugadores repartidos por toda una localidad hay tráfico y gente donde está cada uno, hasta el tope por localidad."""
    banco = Banco(tmp_path, max_jugadores=0, trafico="si", trafico_max=4, trafico_total=10, peatones="si", peatones_max=3, peatones_total=7)
    gente = []
    try:
        m = banco.srv.mundo["mapas"]["puerto_bravo"]
        assert int(m["trafico"]) >= 4 and int(m["peatones"]) >= 3
        banco.hacer(lambda: (setattr(banco.srv, "reloj", 12 * 60.0), setattr(banco.srv, "lluvia", False)))
        uno = Ligero(banco, "Uno")
        gente.append(uno)
        uno.estado(x=90.0, y=90.0)
        time.sleep(0.3)
        banco.hacer(lambda: [banco.srv.trafico_pensar() or banco.srv.peatones_pensar() for _ in range(30)])
        solo = banco.hacer(lambda: (sum(1 for c in banco.srv.trafico.values() if not c.get("poli")), len(banco.srv.peatones)))
        assert solo[0] <= 4 and solo[1] <= 3 and solo[0] >= 3   # un jugador, una zona: lo de siempre, sin pasar de lo configurado
        # otros tres, cada uno en una punta: cuatro zonas de tráfico
        ancho, alto = (int(m["nx"]) - 1) * trafico.B, (int(m["ny"]) - 1) * trafico.B
        puntos = [(ancho - 30.0, 90.0), (90.0, alto - 30.0), (ancho - 30.0, alto - 30.0)]
        if min(ancho, alto) < trafico.ZONA + 40:
            pytest.skip("la localidad es demasiado pequeña para tener varias zonas de tráfico")
        for n, (x, y) in enumerate(puntos):
            c = Ligero(banco, "Lejos %d" % n)
            gente.append(c)
            c.estado(x=x, y=y)
        time.sleep(0.3)
        banco.hacer(lambda: [banco.srv.trafico_pensar() or banco.srv.peatones_pensar() for _ in range(40)])
        coches, peatones = banco.hacer(lambda: (sum(1 for c in banco.srv.trafico.values() if not c.get("poli")), len(banco.srv.peatones)))
        assert 4 < coches <= 10 and 3 < peatones <= 7           # más que para uno solo, sin pasar del tope de la localidad
        # y cada uno recibe los suyos
        assert gente[-1].leer("estados", filtro=lambda m: m.get("tr"))["tr"]
        # sin tope por localidad, tantos como zonas
        banco.hacer(banco.srv.aplicar_config, {"trafico_total": 0})
        banco.hacer(lambda: [banco.srv.trafico_pensar() for _ in range(40)])
        assert banco.hacer(lambda: sum(1 for c in banco.srv.trafico.values() if not c.get("poli"))) > 10
    finally:
        for c in gente:
            c.cerrar()
        banco.parar()


def test_guardado_y_copias_automaticas(tmp_path, sin_firma):
    banco = Banco(tmp_path, guardado_minutos=2, copia_auto_horas=1, copias_guardar=2)
    try:
        a = Ligero(banco, "Ana")
        a.estado()
        guardados = []
        original = banco.srv.guardar_todo
        banco.srv.guardar_todo = lambda: (guardados.append(1), original())[1]
        banco.hacer(lambda: banco.srv._tic(1.0, 60))
        assert not guardados                                    # todavía no han pasado los dos minutos
        banco.hacer(lambda: setattr(banco.srv, "_t_guardado", time.monotonic() - 121))
        banco.hacer(lambda: banco.srv._tic(1.0, 61))
        assert len(guardados) == 1
        # cada hora, una copia; solo se conservan las dos últimas automáticas, y las hechas a mano no se tocan
        manual = banco.hacer(banco.srv.orden, "copia")
        assert "Copia hecha en" in manual and manual.strip().endswith(".zip")
        for n in range(3):
            banco.hacer(lambda: setattr(banco.srv, "_t_copia", time.monotonic() - 3601))
            banco.hacer(lambda: banco.srv._tic(1.0, 100 + n))
        from servidor import copias
        lista = copias.listar(str(tmp_path))
        assert sum(1 for c in lista if c[3]) == 2 and sum(1 for c in lista if not c[3]) == 1
        assert "Hay 3" in banco.hacer(banco.srv.orden, "copias")
        assert sum(1 for l in banco.lineas if "Copia de seguridad automática hecha" in l) == 3
    finally:
        banco.parar()


@con_reintento
def test_ordenes_nuevas_de_administracion(tmp_path, sin_firma):
    banco = Banco(tmp_path)
    try:
        a, b = Ligero(banco, "Ana"), Ligero(banco, "Blas el Largo")
        o = lambda t: banco.hacer(banco.srv.orden, t)
        ayuda = o("ayuda")
        for orden, _ in nucleo.Servidor.AYUDA_ORDENES:           # la ayuda dice todas, y todas existen
            assert orden in ayuda
            assert "No conozco esa orden" not in o(orden.split()[0] if orden.split()[0] != "apagar" else "estado")
        assert "Ana (administra) (dentro)" in o("cuentas") and "Blas el Largo (dentro)" in o("cuentas")
        # mensaje privado: solo le llega a él, con nombres con espacios
        assert "Dicho a Blas el Largo" in o("decir Blas el Largo: baja la música")
        assert "baja la música" in b.leer("aviso")["texto"]
        assert "dos puntos" in o("decir Nadie: hola")
        # dar y quitar la administración
        assert "ya es administrador" in o("admin Blas el Largo") and banco.hacer(lambda: banco.srv.alm.cuenta_por_nombre("Blas el Largo")["admin"]) == 1
        assert "ya no administra" in o("quitaradmin Blas el Largo") and not next(j for j in banco.srv.jugadores.values() if j.nombre == "Blas el Largo").admin
        banco.hacer(banco.srv.aplicar_config, {"admins": "blas el largo"})
        assert next(j for j in banco.srv.jugadores.values() if j.nombre == "Blas el Largo").admin
        assert "sigue administrando" in o("quitaradmin Blas el Largo")
        # invitaciones: varias de golpe, la lista y anular
        antes = o("invitaciones").count("libre")
        varios = o("invitar 3")
        codigos = [c.strip() for c in varios.split(":")[1].split(",")]
        assert len(codigos) == 3 and all(len(c) == 8 for c in codigos)
        assert o("invitaciones").count("libre") == antes + 3
        assert "anulada" in o("anular " + codigos[0].lower()) and o("invitaciones").count("libre") == antes + 2
        assert "No hay ninguna invitación libre" in o("anular " + codigos[0])
        # expulsar con motivo
        assert "expulsado" in o("expulsar Blas el Largo: por pesado")
        assert "por pesado" in b.leer("expulsado")["motivo"]
        time.sleep(1.5)
        assert "no está dentro" in o("expulsar Blas el Largo")
        assert "le falta algo" in o("expulsar") and "expulsar nombre" in o("expulsar") and "No conozco esa orden" in o("bailar")
        # borrar una cuenta: con su personaje y sus propiedades
        casa = next(l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] == "casa" and l["precio"] > 0)
        a.estado()
        a.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        a.leer("prop")
        assert "borrada" in o("borrarcuenta Ana")
        assert "borrado tu cuenta" in a.leer("expulsado")["motivo"]
        assert banco.hacer(lambda: banco.srv.alm.cuenta_por_nombre("Ana")) is None and casa["id"] not in banco.hacer(banco.srv._props)
        assert "No hay nadie" in o("borrarcuenta Ana")
        # un administrador da órdenes desde el chat del juego, y queda apuntado quién ha sido
        c = Ligero(banco, "Carla")
        banco.hacer(banco.srv.orden, "admin Carla")
        c.enviar({"t": "chat", "texto": "/estado"})
        assert "en marcha" in c.leer("aviso")["texto"]
        c.enviar({"t": "chat", "texto": "/invitar"})
        assert "Código de invitación" in c.leer("aviso")["texto"]
        assert any("Carla da la orden invitar" in l for l in banco.lineas)
    finally:
        banco.parar()


def test_recargar_la_configuracion_con_el_servidor_en_marcha(tmp_path, sin_firma):
    from servidor import opciones
    conf = tmp_path / "servidor.conf"
    banco = Banco(tmp_path / "datos")
    try:
        assert "no hay nada que recargar" in banco.hacer(banco.srv.orden, "recargar")
        cfg = dict(opciones.valores_de_serie(), datos=str(tmp_path / "datos"), puerto=banco.puerto, interfaz="127.0.0.1", cifrado="no",
                   bienvenida="Hola a todos", max_jugadores=0, pvp="no")
        opciones.guardar(str(conf), cfg)
        banco.srv.ruta_conf = str(conf)
        r = banco.hacer(banco.srv.orden, "recargar")
        assert "Aplicado" in r and "Bienvenida" in r and banco.srv.cfg["bienvenida"] == "Hola a todos" and banco.srv.cfg["pvp"] == "no"
        # lo que pide reiniciar no se toca, y se dice
        cfg["puerto"] = 47999
        opciones.guardar(str(conf), cfg)
        r = banco.hacer(banco.srv.orden, "recargar")
        assert "Esperan a que reinicies" in r and "Puerto" in r and banco.srv.cfg["puerto"] == 0 and banco.srv.puerto == banco.puerto
        a = Ligero(banco, "Ana")
        assert a.ok["servidor"]["bienvenida"] == "Hola a todos" and a.ok["servidor"]["pvp"] is False
    finally:
        banco.parar()
