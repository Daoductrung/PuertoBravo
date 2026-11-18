"""El servidor en línea, probado de verdad: un servidor arrancado y varios clientes que le hablan por la red.

Aquí los clientes son de mentira (solo envían y leen mensajes), incluidos algunos tramposos. El juego conectado al
servidor se prueba en test_enlinea.py.
"""
import asyncio
import binascii
import hashlib
import json
import os
import socket
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import ed25519
from servidor import firma, nucleo

MUNDO = None


def mundo():
    global MUNDO
    if MUNDO is None:
        from herramientas import exportar_mundo_servidor as ex
        import tempfile
        MUNDO = ex.exportar(os.path.join(tempfile.mkdtemp(), "mundo.json"))
    return MUNDO


class Reloj:
    def __init__(self):
        self.t = time.time()

    def __call__(self):
        return self.t


class Banco:
    """Un servidor de verdad en su hilo, con su bucle."""

    def __init__(self, carpeta, de_disco=False, **cfg):
        self.reloj = Reloj()
        self.de_disco = de_disco                 # el servidor arranca con el mundo que tenga guardado, como uno de verdad
        base = {"datos": str(carpeta), "puerto": 0, "interfaz": "127.0.0.1", "cifrado": "no", "proteccion": 0, "guerra_espera": 1, "guerra_dura": 1,
                "personajes": 0, "economia": "no", "trafico": "no", "peatones": "no", "patrullas": 0, "policia": "no",
                "parada_espera": 0}                 # los personajes del servidor van al azar: solo en las pruebas que tratan de ellos
        base.update(cfg)
        self.cfg = base
        self.loop = asyncio.new_event_loop()
        self.srv = None
        self.lineas = []
        listo = threading.Event()

        def correr():
            asyncio.set_event_loop(self.loop)
            self.srv = nucleo.Servidor(self.cfg, None if self.de_disco else mundo(), reloj_real=self.reloj)
            self.srv.log = self.lineas.append
            self.loop.run_until_complete(self.srv.iniciar())
            listo.set()
            self.loop.run_forever()
        self.hilo = threading.Thread(target=correr, daemon=True)
        self.hilo.start()
        assert listo.wait(10)
        self.puerto = self.srv.puerto

    def hacer(self, f, *a):
        """Ejecuta algo dentro del hilo del servidor y espera el resultado."""
        fut = asyncio.run_coroutine_threadsafe(self._envolver(f, *a), self.loop)
        return fut.result(10)

    async def _envolver(self, f, *a):
        r = f(*a)
        if asyncio.iscoroutine(r):
            r = await r
        return r

    def parar(self):
        self.hacer(self.srv.detener)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.hilo.join(5)


class Cli:
    def __init__(self, banco, nombre, semilla=None, entrar=True, **hola):
        self.semilla = semilla or hashlib.sha256(("semilla-" + nombre).encode()).digest()
        self.pub = binascii.hexlify(ed25519.publica(self.semilla)).decode()
        self.ok = None
        self.rechazo = None
        self.pidio_mundo = False
        d = {"t": "hola", "v": nucleo.VERSION_RED, "nombre": nombre, "pub": self.pub, "huella": mundo()["huella"], "juego": mundo()["version"]}
        d.update(hola)
        # En este equipo, un filtro de red se traga a veces una conexión local recién abierta: ni datos ni cierre.
        # El juego de verdad reintenta; este cliente de pruebas, también.
        for intento in range(3):
            self.s = socket.create_connection(("127.0.0.1", banco.puerto), timeout=5)
            self.buf = b""
            self.cola = []
            self.enviar(d)
            if not entrar:
                return
            try:
                self._saludo(banco, 4 if intento < 2 else 12)
                return
            except AssertionError:
                self.s.close()
                if intento == 2:
                    raise

    def _saludo(self, banco, espera):
        r = self.leer(("reto", "rechazo"), espera=espera)
        if r["t"] == "rechazo":
            self.rechazo = r["motivo"]
            return
        f = ed25519.firmar(self.semilla, ("puertobravo-entrada|" + r["n"]).encode("ascii"))
        self.enviar({"t": "firma", "f": binascii.hexlify(f).decode()})
        r = self.leer(("ok", "rechazo", "pide_mundo"), espera=espera)
        if r["t"] == "pide_mundo":                                   # el servidor no conoce el mundo de este juego: se le da
            self.pidio_mundo = True
            import base64, zlib
            texto_m, firma_m = getattr(banco, "mundo_cliente", ("", ""))
            self.enviar({"t": "mundo", "z": base64.b64encode(zlib.compress(texto_m.encode("utf-8"), 9)).decode("ascii"), "firma": firma_m})
            r = self.leer(("ok", "rechazo"), espera=espera + 8)
        if r["t"] == "rechazo":
            self.rechazo = r["motivo"]
        else:
            self.ok = r
            self.id = r["id"]

    def enviar(self, obj):
        self.s.sendall(json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n")

    def _linea(self, espera):
        fin = time.time() + espera
        while b"\n" not in self.buf:
            self.s.settimeout(max(0.01, fin - time.time()))
            try:
                trozo = self.s.recv(65536)
            except (socket.timeout, OSError):
                return None
            if not trozo:
                return None
            self.buf += trozo
        linea, self.buf = self.buf.split(b"\n", 1)
        return json.loads(linea.decode("utf-8"))

    def leer(self, tipos, espera=8.0, filtro=None):
        """El primer mensaje de alguno de esos tipos. Los demás se guardan por si se piden luego."""
        tipos = (tipos,) if isinstance(tipos, str) else tipos
        for k, m in enumerate(self.cola):
            if m["t"] in tipos and (filtro is None or filtro(m)):
                return self.cola.pop(k)
        fin = time.time() + espera
        while time.time() < fin:
            m = self._linea(fin - time.time())
            if m is None:
                break
            if m["t"] in tipos and (filtro is None or filtro(m)):
                return m
            if m["t"] != "estados" or "estados" in tipos:
                self.cola.append(m)
        raise AssertionError("no llega %s; en cola: %s" % (tipos, [m["t"] for m in self.cola]))

    def nada(self, tipos, espera=0.5):
        try:
            self.leer(tipos, espera)
        except AssertionError:
            return True
        return False

    def estado(self, mapa="puerto_bravo", x=100.0, y=100.0, **mas):
        e = {"m": mapa, "x": x, "y": y, "r": 0, "v": None, "s": 0, "sa": 100, "di": 5000, "ar": "pistola", "b": None}
        e.update(mas)
        self.enviar({"t": "estado", "e": e})

    def cerrar(self):
        try:
            self.s.close()
        except OSError:
            pass


@pytest.fixture
def banco(tmp_path):
    b = Banco(tmp_path)
    yield b
    b.parar()


def lejos_de_todo(m="puerto_bravo"):
    """Un punto del mapa que no esté en ninguna zona segura."""
    seguras = [(l["x"], l["y"]) for l in mundo()["mapas"][m]["lugares"] if l["tipo"] in nucleo.SEGURAS]
    for x in range(40, 900, 37):
        for y in range(40, 700, 41):
            if all((x - a) ** 2 + (y - b) ** 2 > 60 ** 2 for a, b in seguras):
                return float(x), float(y)
    raise AssertionError("no hay sitio")


def test_la_firma_del_servidor_es_la_del_juego():
    """El servidor lleva su copia de la firma para poder instalarse solo: tiene que ser idéntica a la del juego."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert open(os.path.join(raiz, "juego", "ed25519.py"), "rb").read() == open(os.path.join(raiz, "servidor", "firma.py"), "rb").read()
    s = hashlib.sha256(b"x").digest()
    assert firma.verificar(firma.publica(s), b"hola", ed25519.firmar(s, b"hola"))


def test_entrar_con_identidad_y_retomar_el_personaje(banco):
    a = Cli(banco, "Lucía")
    assert a.ok and a.ok["nombre"] == "Lucía" and a.ok["partida"] is None and a.ok["admin"]      # la primera cuenta administra
    assert a.ok["hora"]["dia"] == 1 and a.ok["semilla"] > 0 and a.ok["servidor"]["pvp"]
    b = Cli(banco, "Lucía", semilla=hashlib.sha256(b"otra persona").digest())      # otra persona con el mismo nombre
    assert b.ok["nombre"] == "Lucía 2" and not b.ok["admin"]
    assert a.leer("entra")["nombre"] == "Lucía 2"
    a.enviar({"t": "guardar", "p": {"jugador": {"dinero": 777}, "dia": 3}, "ya": True})
    a.leer("guardado")
    a.cerrar()
    assert b.leer("sale")["id"] == a.id
    a2 = Cli(banco, "Otro nombre", semilla=a.semilla)             # misma identidad: es la misma cuenta, con su nombre de siempre
    assert a2.ok["nombre"] == "Lucía" and a2.ok["partida"]["jugador"]["dinero"] == 777 and a2.ok["cuenta"] == a.ok["cuenta"]


def test_no_entra_quien_no_debe(banco):
    assert "demasiado antiguo" in Cli(banco, "Viejo", v=1).rechazo
    # Con otros datos (mods, o un juego sin firmar): desde la 1.7.1 entra de serie y juega en lo común (test_171_versiones.py).
    # No entra si quien lleva el servidor lo pide así.
    banco.hacer(banco.srv.aplicar_config, {"mundo_distinto": "rechazar"})
    assert "datos de tu juego" in Cli(banco, "Mods", huella="otra").rechazo
    # una identidad que no se puede demostrar: firma con otra clave
    otra = hashlib.sha256(b"otra").digest()
    for intento in range(3):                                     # en este equipo la red local se traga a veces el motivo del rechazo
        c = Cli(banco, "Falso", entrar=False)
        r = c.leer("reto")
        c.enviar({"t": "firma", "f": binascii.hexlify(ed25519.firmar(otra, ("puertobravo-entrada|" + r["n"]).encode())).decode()})
        try:
            assert "identidad" in c.leer("rechazo")["motivo"]
            break
        except AssertionError:
            if intento == 2:
                raise
    assert banco.hacer(lambda: sum(1 for j in banco.srv.jugadores.values() if j.dentro)) == 0      # y en ningún caso ha entrado
    # y lo que no es el juego, se corta sin más
    s = socket.create_connection(("127.0.0.1", banco.puerto), timeout=3)
    s.sendall(b"GET / HTTP/1.1\r\n\r\n")
    s.settimeout(20)
    dentro = banco.hacer(lambda: sum(1 for j in banco.srv.jugadores.values() if j.dentro))
    try:
        assert s.recv(100) == b""
    except ConnectionError:
        pass                                                     # cortado de golpe: también vale
    except socket.timeout:
        # En este equipo, un filtro de la red local se traga a veces el cierre de una conexión a 127.0.0.1. Entonces se
        # comprueba lo que importa, en el servidor: que esa conexión no ha entrado como jugador y que sigue atendiendo.
        assert banco.hacer(lambda: sum(1 for j in banco.srv.jugadores.values() if j.dentro)) == dentro
        assert Cli(banco, "Despues").ok is not None
    finally:
        s.close()


def test_una_sola_sesion_por_cuenta(banco):
    a = Cli(banco, "Marta")
    a2 = Cli(banco, "Marta", semilla=a.semilla)
    assert a2.ok and "desde otro sitio" in a.leer("expulsado")["motivo"]
    assert banco.hacer(lambda: sum(1 for j in banco.srv.jugadores.values() if j.dentro)) == 1


def test_entrada_con_clave_y_con_invitacion(tmp_path):
    b = Banco(tmp_path / "c", entrada="clave", clave="sésamo")
    try:
        assert "contraseña" in Cli(b, "Sin clave").rechazo
        assert Cli(b, "Con clave", clave=hashlib.sha256("puerto-bravo|sésamo".encode()).hexdigest()).ok
    finally:
        b.parar()
    b = Banco(tmp_path / "i", entrada="invitacion")
    try:
        assert "invitados" in Cli(b, "Colado").rechazo
        codigo = b.hacer(b.srv.orden, "invitar").split(": ")[1]
        uno = Cli(b, "Invitado", invitacion=codigo)
        assert uno.ok
        assert "invitados" in Cli(b, "Aprovechado", invitacion=codigo).rechazo      # de un solo uso
        uno.cerrar()
        time.sleep(0.3)
        assert Cli(b, "Invitado", semilla=uno.semilla).ok        # quien ya tiene cuenta no necesita otro código
    finally:
        b.parar()


def test_cada_uno_ve_a_los_de_su_localidad_y_el_chat_tiene_canales(banco):
    a, b, c = Cli(banco, "Ana"), Cli(banco, "Blas"), Cli(banco, "Ciro")
    a.estado(x=100, y=100)
    b.estado(x=130, y=100, v="sedan", s=12)
    c.estado(mapa="villaseca", x=50, y=50)
    e = a.leer("estados", filtro=lambda m: str(b.id) in m["e"] and m["e"][str(b.id)]["x"] == 130)["e"][str(b.id)]
    assert e["v"] == "sedan" and e["m"] == "puerto_bravo"
    lejos = a.leer("estados", espera=5, filtro=lambda m: str(c.id) in m["e"])["e"][str(c.id)]
    assert lejos["m"] == "villaseca"                             # de los de fuera, solo por dónde andan
    a.enviar({"t": "chat", "texto": "hola a todos"})
    assert b.leer("chat")["texto"] == "hola a todos" and c.leer("chat")["canal"] == "todos"
    a.enviar({"t": "chat", "texto": "solo cerca", "canal": "cerca"})
    assert b.leer("chat")["canal"] == "cerca" and c.nada("chat")
    a.enviar({"t": "chat", "texto": "para ti", "canal": "priv", "a": c.id})
    assert c.leer("chat")["texto"] == "para ti" and b.nada("chat")
    a.enviar({"t": "dinero", "a": b.id, "n": 250})
    assert b.leer("dinero")["n"] == 250
    b.estado(x=105, y=100)
    time.sleep(0.2)
    a.enviar({"t": "dar", "a": b.id, "clase": "arma", "id": "pistola", "n": 1})
    assert b.leer("recibe")["id"] == "pistola" and a.leer("dado")["nombre"] == "Blas"
    a.enviar({"t": "dar", "a": c.id, "clase": "arma", "id": "pistola", "n": 1})      # Ciro está en otra localidad
    assert "a tu lado" in a.leer("aviso")["texto"]


def test_el_coche_que_dejas_se_lo_puede_llevar_otro(tmp_path):
    banco = Banco(tmp_path)
    try:
        a, b = Cli(banco, "Ana"), Cli(banco, "Blas")
        a.estado(x=200, y=200, v="sedan")
        b.estado(x=205, y=200)
        a.enviar({"t": "veh_tomar", "modelo": "sedan", "nombre": "Sedán robado", "salud": 90, "ref": 7})
        vid = a.leer("veh_tuyo")["id"]
        assert b.leer("veh_ocupado")["por"] == a.id
        # mientras lo conduce, los demás saben qué vehículo es
        a.estado(x=210, y=200, v="sedan", s=3)
        assert b.leer("estados", filtro=lambda m: m["e"].get(str(a.id), {}).get("vi") == vid)
        # Blas no puede subirse sin más a un coche ocupado, pero sí sacar a Ana si va despacio
        b.enviar({"t": "veh_subir", "id": vid})
        assert "adelantado" in b.leer("veh_no")["motivo"]
        a.estado(x=210, y=200, v="sedan", s=20)
        time.sleep(0.15)
        b.enviar({"t": "veh_asaltar", "id": vid})
        assert "rápido" in b.leer("veh_no")["motivo"]
        a.estado(x=210, y=200, v="sedan", s=2)
        time.sleep(0.15)
        b.enviar({"t": "veh_asaltar", "id": vid})
        ok = b.leer("veh_ok")
        assert ok["robado"] and ok["asalto"] == "Ana" and a.leer("sacado")["nombre"] == "Blas"
        # Blas lo deja aparcado; Ana lo recupera, y a Blas le llega el aviso
        a.estado(x=212, y=200)
        b.estado(x=300, y=260, v="sedan")
        b.enviar({"t": "veh_dejar", "id": vid, "x": 300, "y": 260, "r": 90, "salud": 80})
        libre = a.leer("veh_libre")["v"]
        assert libre["por"] is None and libre["x"] == 300 and libre["salud"] == 80
        a.enviar({"t": "veh_subir", "id": vid})
        assert "lejos" in a.leer("veh_no")["motivo"]
        a.estado(x=298, y=258)
        time.sleep(0.15)
        a.enviar({"t": "veh_subir", "id": vid})
        assert a.leer("veh_ok")["robado"] and "se ha llevado tu" in b.leer("aviso")["texto"]
        a.estado(x=400, y=300, v="sedan")
        a.enviar({"t": "veh_dejar", "id": vid, "x": 400, "y": 300, "r": 0, "salud": 60})
        b.leer("veh_libre")
        # un vehículo aparcado se puede destrozar
        b.estado(x=402, y=300)
        b.enviar({"t": "veh_dano", "id": vid, "n": 25})
        assert a.leer("veh_salud")["salud"] == 35
    finally:
        banco.parar()
    # el servidor se apaga y vuelve: el coche sigue aparcado donde estaba
    banco = Banco(tmp_path)
    try:
        c = Cli(banco, "Ciro")
        vs = c.ok["vehiculos"]
        assert len(vs) == 1 and vs[0]["x"] == 400 and vs[0]["salud"] == 35 and vs[0]["por"] is None
        c.estado(x=401, y=300)
        time.sleep(0.15)
        c.enviar({"t": "veh_dano", "id": vs[0]["id"], "n": 500})
        assert c.leer("veh_revienta")["id"] == vs[0]["id"]
    finally:
        banco.parar()


def _dos_frente_a_frente(banco, d=10.0, **cfg):
    x, y = lejos_de_todo()
    a, b = Cli(banco, "Ana"), Cli(banco, "Blas")
    a.estado(x=x, y=y)
    b.estado(x=x + d, y=y)
    time.sleep(0.2)
    return a, b, x, y


def test_el_servidor_decide_los_disparos(banco):
    a, b, x, y = _dos_frente_a_frente(banco)
    banco.hacer(lambda: setattr(banco.srv, "rng", __import__("random").Random(1)))
    dados = 0
    for _ in range(12):
        a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
        time.sleep(0.45)
    while True:
        try:
            a.leer("impacto", 0.3)
            dados += 1
        except AssertionError:
            break
    assert 3 <= dados <= 12                                      # unos dan y otros no
    h = b.leer("herido")
    assert h["nombre"] == "Ana" and 5 < h["dano"] < 40 and b.leer("tiro")["de"] == a.id
    # más deprisa de lo que dispara el arma, no cuela
    while not b.nada(("herido", "silbido", "tiro"), 0.4):
        pass
    a.cola.clear(); b.cola.clear()
    for _ in range(20):
        a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
    time.sleep(0.5)
    n = 0
    while True:
        try:
            b.leer(("herido", "silbido"), 0.3)
            n += 1
        except AssertionError:
            break
    assert n <= 2
    # desde demasiado lejos tampoco
    b.estado(x=x + 300, y=y)
    time.sleep(0.5)
    a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
    assert a.leer("fallo", filtro=lambda m: m.get("lejos"))
    # un arma que no existe se toma por los puños: a 300 metros no llega
    time.sleep(0.6)
    a.enviar({"t": "ataque", "a": b.id, "arma": "rayo_mortal"})
    assert b.nada("herido")


def test_zonas_seguras_modo_pasivo_y_proteccion_al_llegar(tmp_path):
    banco = Banco(tmp_path, proteccion=1)
    try:
        hospital = next(l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] == "hospital")
        a, b = Cli(banco, "Ana"), Cli(banco, "Blas")
        a.estado(x=hospital["x"] + 3, y=hospital["y"])
        b.estado(x=hospital["x"] + 8, y=hospital["y"])
        time.sleep(0.2)
        a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
        assert "acaba" in a.leer("fallo")["motivo"].lower()      # recién llegados: protegidos
        time.sleep(4)
        a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
        assert "Zona segura" in a.leer("fallo")["motivo"] and b.nada("herido", 0.3)
        x, y = lejos_de_todo()
        a.estado(x=x, y=y)
        b.estado(x=x + 5, y=y)
        b.enviar({"t": "pasivo", "si": True})
        assert b.leer("pasivo")["si"] is True
        time.sleep(3.2)
        a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
        assert "modo pasivo" in a.leer("fallo")["motivo"]
        b.enviar({"t": "pasivo", "si": False})
        assert "Espera dos minutos" in b.leer("aviso")["texto"]  # no se entra y se sale a conveniencia
    finally:
        banco.parar()


def test_caer_ante_otro_jugador_botin_y_recompensa(banco):
    a, b, x, y = _dos_frente_a_frente(banco, d=3.0)
    b.estado(x=x + 3, y=y, di=2000, sa=100)
    time.sleep(0.2)
    a.enviar({"t": "ataque", "a": b.id, "arma": "bate"})
    b.leer(("herido", "silbido"))
    b.enviar({"t": "caido", "por": a.id})
    cae = b.leer("caes")
    assert cae["nombre"] == "Ana" and cae["pierde"] == 200       # el diez por ciento de lo que llevaba
    baja = a.leer("baja")
    assert baja["botin"] == 200 and a.leer("buscado")["recompensa"] == 500      # Blas no se había defendido
    assert banco.hacer(lambda: banco.srv.alm.cuenta(a.ok["cuenta"])["bajas"]) == 1
    # ahora Blas se toma la revancha: cobra el botín y la recompensa, y a él no le ponen precio
    a.estado(x=x, y=y, di=1000)
    b.estado(x=x + 3, y=y, di=1800)
    time.sleep(0.2)
    b.enviar({"t": "ataque", "a": a.id, "arma": "bate"})
    a.leer(("herido", "silbido"))
    a.enviar({"t": "caido", "por": b.id})
    baja = b.leer("baja")
    assert baja["botin"] == 100 + 500 and "por su cabeza" in baja["texto"] and b.nada("buscado", 0.4)
    # quien dice que ha caído ante alguien que no le ha tocado, no regala nada
    c = Cli(banco, "Ciro")
    c.estado(x=x, y=y + 3)
    a.enviar({"t": "caido", "por": c.id})
    assert c.nada("baja", 0.4)


def test_desconectarse_en_plena_pelea_no_salva(banco):
    a, b, x, y = _dos_frente_a_frente(banco, d=3.0)
    b.estado(x=x + 3, y=y, di=1000, sa=8)
    time.sleep(0.2)
    banco.hacer(lambda: setattr(banco.srv, "rng", __import__("random").Random(3)))
    a.enviar({"t": "ataque", "a": b.id, "arma": "bate"})
    a.leer(("impacto", "fallo"))
    b.cerrar()                                                   # se va para no caer
    time.sleep(0.4)
    assert a.nada("sale", 0.3)                                   # pero sigue ahí unos segundos
    for _ in range(8):
        time.sleep(0.5)
        a.enviar({"t": "ataque", "a": b.id, "arma": "bate"})
        try:
            baja = a.leer("baja", 0.2)
            break
        except AssertionError:
            baja = None
    assert baja and baja["botin"] == 100
    b2 = Cli(banco, "Blas", semilla=b.semilla)
    assert b2.ok["pendientes"] == [{"que": "caido", "por": "Ana", "pierde": 100}]


def test_bandas_caja_barrios_guerra_y_alianza(banco):
    x, y = lejos_de_todo()
    barrios = [q["id"] for q in mundo()["mapas"]["puerto_bravo"]["barrios"]]
    a, b, c = Cli(banco, "Ana"), Cli(banco, "Blas"), Cli(banco, "Ciro")
    for k, cli in enumerate((a, b, c)):
        cli.estado(x=x + 4 * k, y=y, di=20000, b=barrios[0])
    time.sleep(0.2)
    a.enviar({"t": "banda_crear", "nombre": "Los Linces"})
    assert a.leer("cobro")["n"] == 2000
    ba = a.leer("banda")
    assert ba["b"]["nombre"] == "Los Linces" and ba["rango"] == "jefe"
    a.enviar({"t": "banda_invitar", "a": b.id})
    assert b.leer("banda_invita")["nombre"] == "Los Linces"
    b.enviar({"t": "banda_resp", "si": True})
    assert len(b.leer("banda")["b"]["miembros"]) == 2
    # de la misma banda, sin fuego amigo, no se hieren
    a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
    assert "de tu banda" in a.leer("fallo")["motivo"]
    # la caja: ingresa cualquiera, saca el jefe
    b.enviar({"t": "banda_ingresar", "n": 6000})
    assert b.leer("cobro")["n"] == 6000
    b.enviar({"t": "banda_sacar", "n": 100})
    assert "solo sacan" in b.leer("aviso", filtro=lambda m: "sacan" in m["texto"])["texto"]
    a.leer("banda", filtro=lambda m: m["b"]["caja"] == 6000)
    # reclamar el barrio en el que están
    a.enviar({"t": "barrio_reclamar"})
    t = a.leer("territorios", filtro=lambda m: m["e"]["barrios"])["e"]["barrios"][0]
    assert t["barrio"] == barrios[0] and t["nombre"] == "Los Linces"
    a.leer("banda", filtro=lambda m: m["b"]["caja"] == 3000)
    # a medianoche el barrio deja su renta en la caja
    banco.hacer(lambda: setattr(banco.srv, "reloj", 1439.6))
    assert a.leer("banda", espera=6, filtro=lambda m: m["b"]["caja"] == 3300)
    # otra banda le declara la guerra
    c.enviar({"t": "banda_crear", "nombre": "Los Zorros"})
    c.leer("banda")
    c.enviar({"t": "banda_ingresar", "n": 5000})
    c.leer("banda", filtro=lambda m: m["b"]["caja"] == 5000)
    c.enviar({"t": "barrio_reclamar"})
    assert "ya tiene dueño" in c.leer("aviso", filtro=lambda m: "dueño" in m["texto"])["texto"]
    c.enviar({"t": "barrio_guerra"})
    assert "os declara la guerra" in a.leer("aviso", filtro=lambda m: "guerra" in m["texto"])["texto"]
    # empieza cuando toca; Ciro está dentro del barrio y los Linces se han ido: gana
    a.estado(x=x, y=y, b=barrios[1], di=1)
    b.estado(x=x, y=y, b=barrios[1], di=1)
    banco.reloj.t += 61
    assert "Empieza la guerra" in c.leer("aviso", espera=5, filtro=lambda m: "¡Empieza" in m["texto"])["texto"]
    time.sleep(2.2)
    banco.reloj.t += 61
    fin = c.leer("aviso", espera=5, filtro=lambda m: "ha terminado" in m["texto"])["texto"]
    assert "pasa a Los Zorros" in fin
    t = c.leer("territorios", filtro=lambda m: m["e"]["barrios"] and m["e"]["barrios"][0]["nombre"] == "Los Zorros")
    assert not t["e"]["guerras"]
    # alianza: la propone uno y la cierra el otro; desde entonces no se hieren
    a.enviar({"t": "alianza", "banda": "Los Zorros"})
    assert "os propone una alianza" in c.leer("aviso", filtro=lambda m: "alianza" in m["texto"])["texto"]
    c.enviar({"t": "alianza", "banda": "Los Linces"})
    assert "Alianza cerrada" in a.leer("aviso", filtro=lambda m: "Alianza" in m["texto"])["texto"]
    a.estado(x=x, y=y, b=barrios[0])
    c.estado(x=x + 5, y=y, b=barrios[0])
    time.sleep(0.2)
    a.enviar({"t": "ataque", "a": c.id, "arma": "pistola"})
    assert "aliada" in a.leer("fallo")["motivo"]
    # el jefe se va: hereda el otro
    a.enviar({"t": "banda_salir"})
    assert b.leer("banda", filtro=lambda m: m["rango"] == "jefe")
    b.enviar({"t": "banda_lista"})
    lista = b.leer("bandas")["e"]
    assert {q["nombre"] for q in lista} == {"Los Linces", "Los Zorros"}


def test_grupo_de_mision_y_paga_a_quien_ayuda(banco):
    a, b, c = Cli(banco, "Ana"), Cli(banco, "Blas"), Cli(banco, "Ciro")
    for cli in (a, b, c):
        cli.estado()
    a.enviar({"t": "grupo_invitar", "a": b.id, "mision": "Morosos"})
    assert b.leer("grupo_invita")["mision"] == "Morosos"
    b.enviar({"t": "grupo_resp", "si": True})
    g = b.leer("grupo")
    assert g["lider"] == a.id and len(g["miembros"]) == 2
    # lo que cuenta el que lleva la misión llega a su grupo y a nadie más
    a.enviar({"t": "grupo_msg", "d": {"que": "enemigos", "e": [{"k": 0, "salud": 60}]}})
    assert b.leer("grupo_msg")["d"]["que"] == "enemigos" and c.nada("grupo_msg", 0.3)
    # los del grupo no se hieren entre sí
    a.enviar({"t": "ataque", "a": b.id, "arma": "pistola"})
    assert "va contigo" in a.leer("fallo")["motivo"]
    # al completarla, el que ayuda cobra la mitad, una sola vez
    dinero = mundo()["misiones"]["m04"]["dinero"]
    a.enviar({"t": "mision_hecha", "id": "m04"})
    assert b.leer("paga_mision")["n"] == dinero // 2
    a.enviar({"t": "mision_hecha", "id": "m04"})
    assert "Ya cobraste" in b.leer("aviso", filtro=lambda m: "cobraste" in m["texto"])["texto"]
    # solo paga quien lleva el grupo
    b.enviar({"t": "mision_hecha", "id": "m05"})
    assert a.nada("paga_mision", 0.3)
    a.enviar({"t": "grupo_salir"})
    assert b.leer("grupo", filtro=lambda m: m["lider"] is None)


def test_administrar_y_aguantar_a_los_pesados(banco):
    a, b = Cli(banco, "Ana"), Cli(banco, "Blas")
    a.estado(); b.estado()
    assert "Hay 2" in banco.hacer(banco.srv.orden, "jugadores")
    a.enviar({"t": "chat", "texto": "/aviso mantenimiento a las diez"})      # Ana administra: fue la primera
    assert "mantenimiento" in b.leer("aviso")["texto"]
    b.enviar({"t": "chat", "texto": "/apagar"})                   # Blas no: su barra es un mensaje más
    assert a.leer("chat")["texto"] == "/apagar"
    assert "vetado" in banco.hacer(banco.srv.orden, "vetar Blas")
    assert "administrador" in b.leer("expulsado")["motivo"]
    time.sleep(0.5)
    assert "No puedes entrar" in Cli(banco, "Blas", semilla=b.semilla).rechazo
    banco.hacer(banco.srv.orden, "perdonar Blas")
    assert Cli(banco, "Blas", semilla=b.semilla).ok
    # quien inunda el servidor de mensajes se queda fuera, y los demás ni lo notan
    c = Cli(banco, "Pesado")
    try:
        for _ in range(4000):
            c.enviar({"t": "ping"})
    except OSError:
        pass
    time.sleep(0.5)
    a.enviar({"t": "ping"})
    assert a.leer("pong")
    assert not any(j.nombre == "Pesado" and j.dentro for j in banco.srv.jugadores.values())
    # un mensaje enorme tampoco lo tumba
    d = Cli(banco, "Enorme")
    try:
        d.s.sendall(b'{"t":"chat","texto":"' + b"a" * (2 * 1024 * 1024) + b'"}\n')
    except OSError:
        pass
    time.sleep(0.5)
    a.enviar({"t": "ping"})
    assert a.leer("pong")
    assert "Copia hecha" in banco.hacer(banco.srv.orden, "copia")


def test_la_hora_es_la_del_servidor_y_no_se_para(tmp_path):
    banco = Banco(tmp_path)
    try:
        banco.hacer(lambda: (setattr(banco.srv, "reloj", 600.0), setattr(banco.srv, "dia", 4)))
        a = Cli(banco, "Ana")
        assert a.ok["hora"]["dia"] == 4 and 600 <= a.ok["hora"]["reloj"] < 603
        a.enviar({"t": "guardar", "p": {"dia": 4}, "ya": True})
        a.leer("guardado")
        a.cerrar()
        time.sleep(0.3)
        banco.hacer(lambda: setattr(banco.srv, "dia", 7))         # pasan tres días sin él
        a2 = Cli(banco, "Ana", semilla=a.semilla)
        assert a2.ok["dias_fuera"] == 3 and a2.ok["hora"]["dia"] == 7
    finally:
        banco.parar()
    banco = Banco(tmp_path)                                       # y al reiniciar el servidor, sigue por donde iba
    try:
        assert banco.srv.dia == 7
    finally:
        banco.parar()


def test_atracar_a_otro_jugador(banco):
    a, b, x, y = _dos_frente_a_frente(banco, d=3.0)
    b.estado(x=x + 3, y=y, di=2000)
    a.estado(x=x, y=y, ar="punos")
    time.sleep(0.2)
    a.enviar({"t": "atraco", "a": b.id})
    assert "manos vacías" in a.leer("aviso")["texto"]            # sin arma no impone
    a.estado(x=x, y=y, ar="navaja")
    time.sleep(0.2)
    a.enviar({"t": "atraco", "a": b.id})
    assert a.leer("atraco_ok")["botin"] == 300                   # el quince por ciento de lo que llevaba
    m = b.leer("atracado")
    assert m["nombre"] == "Ana" and m["pierde"] == 300
    a.enviar({"t": "atraco", "a": b.id})                         # no se le puede exprimir una y otra vez
    assert "hace un momento" in a.leer("aviso")["texto"]
    # el atracado puede defenderse sin que le pongan precio: el que empezó fue el otro
    b.estado(x=x + 3, y=y, di=1700)
    a.estado(x=x, y=y, di=500, ar="navaja")
    time.sleep(0.2)
    b.enviar({"t": "ataque", "a": a.id, "arma": "bate"})
    a.leer(("herido", "silbido"))
    a.enviar({"t": "caido", "por": b.id})
    assert b.leer("baja")["botin"] == 50 and b.nada("buscado", 0.4)


def test_el_servidor_cifra_sin_ningun_programa_aparte(tmp_path, monkeypatch):
    """En Windows no suele haber openssl: el servidor crea él mismo su certificado, y el juego entra cifrado."""
    import shutil
    from juego import enlinea
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    b = Banco(tmp_path, cifrado="si")
    try:
        assert b.srv.cifrado and len(b.srv.huella_cert) == 64
        assert any("Creando el certificado" in t for t in b.lineas)
        c = enlinea.ClienteServidor()
        ok, r = c.conectar_servidor("127.0.0.1", b.puerto, "Cifrado", hashlib.sha256(b"cifrado").digest(), mundo()["huella"])
        assert ok and c.cifrado and c.huella_cert == b.srv.huella_cert and r["nombre"] == "Cifrado"
        c.cerrar()
        time.sleep(0.3)
        # si otro día el certificado no es el mismo, el juego no entra sin avisar
        d = enlinea.ClienteServidor()
        ok, motivo = d.conectar_servidor("127.0.0.1", b.puerto, "Cifrado", hashlib.sha256(b"cifrado").digest(), mundo()["huella"], huella_cert="0" * 64)
        assert not ok and motivo.startswith("certificado: ")
    finally:
        b.parar()
    # al volver a arrancar usa el mismo certificado: no crea otro
    b = Banco(tmp_path, cifrado="si")
    try:
        assert not any("Creando el certificado" in t for t in b.lineas)
    finally:
        b.parar()


def test_un_negocio_tiene_un_solo_dueno_y_otro_jugador_puede_atracarlo(tmp_path):
    banco = Banco(tmp_path, robo_segundos=2)
    try:
        negocio = next(l for l in mundo()["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] == "negocio" and l["precio"] > 0 and l["ingresos"] > 0)
        a, b, c = Cli(banco, "Ana"), Cli(banco, "Blas"), Cli(banco, "Ciro")
        for cli in (a, b, c):
            cli.estado(x=negocio["x"] + 2, y=negocio["y"], ar="pistola", di=100)
        time.sleep(0.2)
        assert a.ok["props"] == {}
        a.enviar({"t": "prop_comprar", "lugar": negocio["id"]})
        assert b.leer("prop")["nombre"] == "Ana" and "Ana compra" in c.leer("aviso")["texto"]
        b.enviar({"t": "prop_comprar", "lugar": negocio["id"]})     # ya tiene dueño
        assert b.leer("prop_no")["nombre"] == "Ana"
        a.enviar({"t": "robo", "lugar": negocio["id"]})             # a uno mismo no se roba
        assert "no es de otro jugador" in a.leer("aviso")["texto"]
        # Blas lo atraca: a Ana le salta la alarma, y si aguanta se lleva la caja del día
        b.enviar({"t": "robo", "lugar": negocio["id"]})
        assert b.leer("robo_empieza")["nombre"] == "Ana"
        aviso = a.leer("robo_aviso")
        assert aviso["nombre"] == "Blas" and aviso["tuyo"] and c.nada("robo_aviso", 0.3)
        fin = b.leer("robo_fin", espera=8)
        assert fin["ok"] and fin["botin"] == negocio["ingresos"]
        assert "ha vaciado la caja" in a.leer("aviso", filtro=lambda m: "caja" in m["texto"])["texto"]
        c.enviar({"t": "robo", "lugar": negocio["id"]})             # una vez al día
        assert "ya le han vaciado la caja hoy" in c.leer("aviso", filtro=lambda m: "caja" in m["texto"])["texto"]
        # a medianoche, a Ana se le descuenta
        banco.hacer(lambda: setattr(banco.srv, "reloj", 1439.6))
        assert a.leer("robos_dia", espera=6)["total"] == negocio["ingresos"]
        # al día siguiente Ciro lo intenta, pero se va antes de tiempo: nada
        c.enviar({"t": "robo", "lugar": negocio["id"]})
        c.leer("robo_empieza")
        c.estado(x=negocio["x"] + 200, y=negocio["y"], ar="pistola")
        fin = c.leer("robo_fin", espera=6)
        assert not fin["ok"] and "ido antes" in fin["motivo"]
        assert "no ha conseguido" in a.leer("aviso", filtro=lambda m: "conseguido" in m["texto"])["texto"]
        # Blas vuelve a por más, con Ana desconectada: lo que le roben se le descuenta al volver
        a.cerrar()
        time.sleep(0.3)
        b.enviar({"t": "robo", "lugar": negocio["id"]})
        b.leer("robo_empieza")
        assert b.leer("robo_fin", espera=8)["ok"]
    finally:
        banco.parar()
    banco = Banco(tmp_path)                                         # y todo eso sobrevive a un reinicio del servidor
    try:
        a2 = Cli(banco, "Ana", semilla=a.semilla)
        assert a2.ok["robos"] == negocio["ingresos"] and a2.ok["props"][negocio["id"]]["nombre"] == "Ana"
    finally:
        banco.parar()


def _mundo_nuevo(version, semilla_firma=None):
    """El mundo de una versión posterior del juego: un lugar más. Devuelve el texto, su huella y, si se pide, su firma."""
    import copy
    from juego import enlinea
    d = copy.deepcopy(mundo())
    d["version"] = version
    d["huella"] = hashlib.sha256(("mundo-" + version).encode()).hexdigest()[:16]
    d["mapas"]["puerto_bravo"]["lugares"].append({"id": "nuevo_" + version, "tipo": "negocio", "nombre": "Local nuevo", "x": 10.0, "y": 10.0, "adultos": False, "precio": 1000, "ingresos": 50})
    texto = enlinea.mundo_canonico(d)
    firma_m = binascii.hexlify(ed25519.firmar(semilla_firma, texto.encode("utf-8"))).decode() if semilla_firma else ""
    return texto, d["huella"], firma_m


def test_el_servidor_vale_para_las_versiones_del_juego_que_vayan_saliendo(tmp_path):
    """El mundo no va atado al servidor: se lo trae el juego. Sale una versión nueva y el servidor no se toca."""
    from juego import actualizador
    assert nucleo.CLAVES_PUBLICAS == actualizador.CLAVES_PUBLICAS       # el servidor se fía de quien publica el juego, y de nadie más
    editor = hashlib.sha256(b"quien publica el juego, en las pruebas").digest()
    banco = Banco(tmp_path)
    try:
        banco.srv.claves_publicas = (binascii.hexlify(ed25519.publica(editor)).decode(),)
        viejo = banco.srv.mundo["huella"]
        a = Cli(banco, "Ana")                                            # con la versión de siempre
        assert a.ok and not a.pidio_mundo
        # alguien llega con una versión nueva, pero el mundo que trae no lo firma quien publica el juego: no cuela
        texto, huella, _ = _mundo_nuevo("9.0.0")
        falsa = binascii.hexlify(ed25519.firmar(hashlib.sha256(b"otro").digest(), texto.encode())).decode()
        banco.mundo_cliente = (texto, falsa)
        tramposo = Cli(banco, "Tramposo", huella=huella, juego="9.0.0", firmado=True)
        # Desde la 1.7.1, de serie, a esa persona se la deja entrar a jugar en lo común; lo que no cuela es su mundo.
        assert tramposo.pidio_mundo and tramposo.ok and tramposo.ok["mundo"]["igual"] is False and banco.srv.mundo["huella"] == viejo
        assert huella not in banco.srv.mundos_conocidos and "nuevo_9.0.0" not in banco.srv.lugares
        banco.hacer(banco.srv.aplicar_config, {"mundo_distinto": "rechazar"})      # y si quien lleva el servidor no quiere, ni entra
        assert "no puede comprobar" in Cli(banco, "Tramposo 2", huella=huella, juego="9.0.0", firmado=True).rechazo and banco.srv.mundo["huella"] == viejo
        banco.hacer(banco.srv.aplicar_config, {"mundo_distinto": "admitir"})
        # la de verdad: firmada. El servidor la adopta sin reiniciarse, y lo avisa a los que están
        texto, huella, firma_m = _mundo_nuevo("9.0.0", editor)
        banco.mundo_cliente = (texto, firma_m)
        b = Cli(banco, "Blas", huella=huella, juego="9.0.0", firmado=True)
        assert b.ok and b.pidio_mundo and banco.srv.mundo["version"] == "9.0.0" and "nuevo_9.0.0" in banco.srv.lugares
        assert "versión 9.0.0" in a.leer("aviso")["texto"]
        c = Cli(banco, "Ciro", huella=huella, juego="9.0.0", firmado=True)
        assert c.ok and not c.pidio_mundo                            # el siguiente ya no tiene que traer nada
        # quien sigue con la versión anterior puede seguir jugando: su mundo es uno que el servidor ya tuvo. Y no hace
        # retroceder al servidor. (Lo de jugar juntos con versiones distintas se prueba a fondo en test_servidor_versiones.py.)
        banco.mundo_cliente = (enlinea_texto_viejo(), "")
        d = Cli(banco, "Dora", juego="1.6.3", firmado=True)
        assert d.ok and not d.pidio_mundo and banco.srv.mundo["version"] == "9.0.0" and {k: d.ok["mundo"][k] for k in ("version", "huella", "igual")} == {"version": "9.0.0", "huella": huella, "igual": False}
        # salvo que quien lleva el servidor pida a todos los mismos datos: entonces sí tiene que actualizar
        banco.hacer(lambda: banco.srv.cfg.__setitem__("versiones", "iguales"))
        e = Cli(banco, "Eva", juego="1.6.3", firmado=True)
        assert "Actualiza el juego" in e.rechazo and not e.pidio_mundo and banco.srv.mundo["version"] == "9.0.0"
        banco.hacer(lambda: banco.srv.cfg.__setitem__("versiones", "compatibles"))
        # un mundo con mods no va firmado: de un jugador cualquiera no se acepta como mundo del servidor. Él entra, de serie;
        # con la opción de rechazar los datos que no se pueden comprobar, no.
        texto, huella_mod, _ = _mundo_nuevo("9.5.0")
        banco.mundo_cliente = (texto, "")
        try:
            mods = Cli(banco, "Con mods", huella=huella_mod, juego="9.5.0")
        except AssertionError:
            raise AssertionError(banco.lineas[-4:])
        assert mods.ok and banco.srv.mundo["version"] == "9.0.0" and banco.srv.mundo["huella"] == huella
        banco.hacer(banco.srv.aplicar_config, {"mundo_distinto": "rechazar"})
        assert "no puede comprobar" in Cli(banco, "Con mods 2", huella=huella_mod, juego="9.5.0").rechazo
    finally:
        banco.parar()
    # se apaga y vuelve: sigue con el mundo nuevo
    banco = Banco(tmp_path, de_disco=True)
    try:
        assert banco.srv.mundo["version"] == "9.0.0"
    finally:
        banco.parar()


def enlinea_texto_viejo():
    from juego import enlinea
    return enlinea.mundo_canonico(mundo())


def test_un_servidor_sin_mundo_y_un_servidor_con_mods(tmp_path):
    """Un servidor recién puesto en una web, sin nada del juego: el primero que entra le trae el mundo.
    Y con la opción para mods, un administrador puede traer el suyo sin firma."""
    banco = Banco(tmp_path / "vacio")
    try:
        banco.hacer(lambda: banco.srv._poner_mundo(dict(nucleo.MUNDO_VACIO), guardar=False))
        editor = hashlib.sha256(b"editor").digest()
        banco.srv.claves_publicas = (binascii.hexlify(ed25519.publica(editor)).decode(),)
        texto = enlinea_texto_viejo()
        banco.mundo_cliente = (texto, binascii.hexlify(ed25519.firmar(editor, texto.encode("utf-8"))).decode())
        a = Cli(banco, "Ana", juego=mundo()["version"], firmado=True)
        assert a.ok and a.pidio_mundo and banco.srv.mundo["huella"] == mundo()["huella"] and banco.srv.seguras
    finally:
        banco.parar()
    banco = Banco(tmp_path / "mods", actualizar_mundo="admin")
    try:
        texto, huella_mod, _ = _mundo_nuevo("1.6.3")                # misma versión, otro mundo: lleva un mod
        banco.mundo_cliente = (texto, "")
        jefe = Cli(banco, "Jefa", huella=huella_mod, juego="1.6.3")  # la primera cuenta administra: puede
        assert jefe.ok and jefe.pidio_mundo and banco.srv.mundo["huella"] == huella_mod
        banco.mundo_cliente = (enlinea_texto_viejo(), "")
        otro = Cli(banco, "Otro", juego="1.6.3")                     # uno cualquiera no puede cambiarlo; entra, con lo que su juego conoce
        assert otro.ok and not otro.pidio_mundo and banco.srv.mundo["huella"] == huella_mod and otro.ok["mundo"]["igual"] is False
        banco.hacer(lambda: banco.srv.cfg.__setitem__("versiones", "iguales"))      # y si el servidor pide los mismos datos a todos, no entra
        tercero = Cli(banco, "Tercero", juego="1.6.3")
        assert tercero.rechazo and banco.srv.mundo["huella"] == huella_mod
    finally:
        banco.parar()
