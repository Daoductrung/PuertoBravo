"""Jugar juntos con versiones distintas del juego en el mismo servidor.

El servidor gestiona y el juego pone el contenido. Aquí se demuestra que un jugador con una versión y otro con una
versión más adelantada conviven: el protocolo se acuerda, lo que no se conoce se deja pasar en los dos sentidos, lo
que uno tiene y el otro no (una localidad, un arma, un vehículo) no rompe nada, y el servidor no echa a nadie por ir
por delante o por detrás.

Hay clientes de mentira, que mandan lo que mandaría un juego de otra versión, y el juego de verdad.
"""
import binascii
import copy
import hashlib
import json
import socket
import threading
import time

import pytest

from juego import ed25519, enlinea
from servidor import nucleo
from test_servidor import Banco, Cli, lejos_de_todo, mundo

EDITOR = hashlib.sha256(b"quien publica el juego, en las pruebas de versiones").digest()


def mundo_de(version, firmar=True, nuevo=True):
    """El mundo de otra versión del juego. Con ``nuevo``, trae una localidad, un arma, un vehículo y un negocio que el
    de ahora no tiene. Devuelve (texto, huella, firma)."""
    d = copy.deepcopy(mundo())
    d["version"] = version
    d["huella"] = hashlib.sha256(("mundo de la " + version).encode()).hexdigest()[:16]
    if nuevo:
        d["mapas"]["puerto_bravo"]["lugares"].append({"id": "local_" + version, "tipo": "negocio", "nombre": "Local nuevo", "x": 10.0, "y": 10.0,
                                                      "adultos": False, "precio": 1000, "ingresos": 50})
        isla = copy.deepcopy(d["mapas"]["puerto_bravo"])
        isla["nombre"] = "Isla Nueva"
        isla["lugares"] = [{"id": "faro_" + version, "tipo": "sitio", "nombre": "Faro", "x": 50.0, "y": 50.0, "adultos": False, "precio": 0, "ingresos": 0}]
        isla["barrios"] = [{"id": "isla_centro", "nombre": "Centro de la isla"}]
        d["mapas"]["isla_nueva"] = isla
        d["armas"]["laser"] = {"nombre": "Láser", "tipo": "fuego", "dano": 30, "alcance": 60, "cadencia": 0.2, "precision": 0.99, "radio": 0, "automatica": False}
        d["modelos"]["aerodeslizador"] = {"nombre": "Aerodeslizador", "salud": 120, "vel_max": 40, "acel": 8.0, "freno": 12, "vuela": False}
    texto = enlinea.mundo_canonico(d)
    firma_m = binascii.hexlify(ed25519.firmar(EDITOR, texto.encode("utf-8"))).decode() if firmar else ""
    return texto, d["huella"], firma_m


def servidor_de_pruebas(tmp_path, **cfg):
    banco = Banco(tmp_path, **cfg)
    banco.srv.claves_publicas = (binascii.hexlify(ed25519.publica(EDITOR)).decode(),)
    return banco


# ============================================================ el protocolo se acuerda
def test_la_version_del_protocolo_se_acuerda(tmp_path):
    banco = Banco(tmp_path)
    try:
        # el de siempre
        a = Cli(banco, "Ana")
        assert a.ok["protocolo"] == nucleo.VERSION_RED and "versiones" in a.ok["funciones"]
        assert a.ok["mundo"] == {"version": mundo()["version"], "huella": mundo()["huella"], "igual": True}
        # un juego más adelantado, que habla un protocolo más nuevo pero todavía se entiende con este: entra, y se usa el del servidor.
        # Trae además cosas en el saludo que este servidor no conoce: se dejan pasar.
        b = Cli(banco, "Berta", v=nucleo.VERSION_RED + 5, vmin=nucleo.PROTOCOLO_MIN, cosa_nueva={"a": [1, 2]}, idioma="es", juego="9.9.9")
        assert b.ok and b.ok["protocolo"] == nucleo.VERSION_RED
        # uno tan adelantado que ya no habla el protocolo de este servidor: se le dice claro qué pasa, y no es culpa suya
        c = Cli(banco, "Carlos", v=nucleo.VERSION_RED + 5, vmin=nucleo.VERSION_RED + 1)
        assert "Quien lleva el servidor tiene que actualizarlo" in c.rechazo
        # uno demasiado antiguo
        d = Cli(banco, "Dora", v=nucleo.PROTOCOLO_MIN - 1)
        assert "demasiado antiguo" in d.rechazo
        # y cosas raras en la versión no tumban nada
        for raro in ("2", None, True, 2.5, [2]):
            assert Cli(banco, "Raro", v=raro).rechazo
        # el reto dice qué habla el servidor, para que el juego pueda decidir
        e = Cli(banco, "Eva", entrar=False)
        reto = e.leer("reto")
        assert reto["v"] == nucleo.VERSION_RED and reto["vmin"] == nucleo.PROTOCOLO_MIN and reto["protocolo"] == nucleo.VERSION_RED
        jugadores = {j.nombre: j for j in banco.srv.jugadores.values()}
        assert jugadores["Berta"].juego == "9.9.9" and jugadores["Berta"].proto == nucleo.VERSION_RED
    finally:
        banco.parar()


def test_el_servidor_deja_pasar_los_mensajes_y_campos_que_no_conoce(tmp_path):
    banco = Banco(tmp_path)
    try:
        x, y = lejos_de_todo()
        a, b = Cli(banco, "Ana"), Cli(banco, "Berta")
        a.estado(x=x, y=y)
        b.estado(x=x + 5, y=y)
        time.sleep(0.2)
        antes = len(banco.lineas)
        # mensajes de una versión posterior: tipos que no existen, tipos raros y mensajes conocidos con campos de más
        for m in ({"t": "teletransporte_cuantico", "destino": [1, 2, 3]}, {"t": "veh_tomar_v2", "modelo": "x"}, {"t": 7}, {"t": None}, {"t": ["chat"]},
                  {"t": "_enviar"}, {"t": "orden"}, {"t": "__init__"}, {"sin_tipo": 1}, {"t": "chat", "texto": "hola", "canal": "holograma", "adjunto": {"k": 1}},
                  {"t": "estado", "e": {"m": "puerto_bravo", "x": x, "y": y, "r": 0, "v": None, "s": 0, "sa": 100, "di": 10, "ar": "punos", "b": None,
                                        "clima_local": "niebla", "mascota": {"id": 3}}, "extra": True},
                  {"t": "ping", "latencia": 12}):
            a.enviar(m)
        assert a.leer("pong")                                    # sigue atendiendo, y nada de eso ha hecho ruido en el registro
        assert b.leer("chat")["texto"] == "hola"                 # el canal desconocido cae en el de todos
        assert not [l for l in banco.lineas[antes:] if l.startswith("Error")]
        assert a.id in banco.srv.jugadores and banco.srv.jugadores[a.id].dentro
        # campos conocidos con una forma que no es la de ahora: no tumban al servidor ni echan a nadie
        for m in ({"t": "estado", "e": "donde siempre"}, {"t": "estado", "e": {"m": "puerto_bravo", "x": "norte", "y": []}}, {"t": "ataque", "a": "Berta", "arma": {"id": 1}},
                  {"t": "dinero", "a": b.id, "n": "mucho"}, {"t": "veh_tomar", "modelo": ["sedan"]}, {"t": "prop_comprar", "lugar": {"id": 1}},
                  {"t": "grupo_msg", "d": "texto"}, {"t": "banda_crear", "nombre": 12345}, {"t": "mision_ok"}, {"t": "guardar", "p": "no es un personaje"}):
            a.enviar(m)
        for _ in range(30):                                      # y repetirlos no llena el registro: cada rareza se apunta una vez
            a.enviar({"t": "veh_tomar", "modelo": ["sedan"]})
        a.enviar({"t": "ping"})
        assert a.leer("pong") and banco.srv.jugadores[a.id].dentro
        raros = [l for l in banco.lineas[antes:] if "se deja pasar" in l]
        assert 1 <= len(raros) <= 10 and sum(1 for l in raros if "veh_tomar" in l) == 1 and all("Ana" in l for l in raros)
        # un arma y un vehículo que el mundo del servidor no tiene: cuenta como ir con las manos y en un coche cualquiera, y se le dice una vez
        a.estado(x=x, y=y, ar="laser", v="aerodeslizador")
        aviso = a.leer("aviso", filtro=lambda m: "arma" in m["texto"])
        assert "no existe en la versión" in aviso["texto"]
        e = b.leer("estados", filtro=lambda m: str(a.id) in m["e"] and m["e"][str(a.id)]["v"])["e"][str(a.id)]
        assert e["v"] == "utilitario" and banco.srv.jugadores[a.id].arma == "punos"
        a.cola.clear()
        a.estado(x=x, y=y, ar="laser", v="aerodeslizador")
        assert a.nada("aviso", 0.6)                              # no se repite a cada momento
        # una localidad que el servidor no conoce: no se le echa; se le avisa, y a los demás les consta que anda por otra parte
        a.estado(mapa="isla_nueva", x=5.0, y=5.0)
        assert "localidad no existe" in a.leer("aviso", filtro=lambda m: "localidad" in m["texto"])["texto"]
        lejos = b.leer("estados", espera=6, filtro=lambda m: m["e"].get(str(a.id), {}).get("m") == "isla_nueva")
        assert lejos and banco.srv.jugadores[a.id].dentro and banco.srv.jugadores[a.id].mapa is None
        assert any(g["nombre"] == "Ana" and g["fuera"] for g in banco.hacer(banco.srv.resumen)["jugadores"])
        # los bucles del servidor siguen su curso con alguien en una localidad desconocida
        banco.hacer(lambda: [banco.srv._tic(1.0, k) for k in range(1, 70)])
        assert not [l for l in banco.lineas[antes:] if l.startswith("Error")], [l for l in banco.lineas[antes:] if l.startswith("Error")]
        # y al volver a una localidad común, vuelve a verse con los demás
        a.estado(x=x, y=y)
        assert b.leer("estados", filtro=lambda m: m["e"].get(str(a.id), {}).get("m") == "puerto_bravo")
        assert a.leer("estados", filtro=lambda m: str(b.id) in m["e"])
    finally:
        banco.parar()


# ================================================ dos versiones en el mismo servidor
def test_dos_jugadores_con_versiones_distintas_juegan_juntos(tmp_path):
    """Vieja tiene la versión de ahora; Nueva, una posterior con una localidad, un arma y un vehículo más."""
    banco = servidor_de_pruebas(tmp_path)
    try:
        v_vieja, h_vieja = mundo()["version"], mundo()["huella"]
        x, y = lejos_de_todo()
        vieja = Cli(banco, "Vieja", juego=v_vieja, firmado=True)
        assert vieja.ok and vieja.ok["mundo"]["igual"]
        vieja.estado(x=x, y=y, di=1000)
        # llega Nueva con la versión posterior: el servidor adopta su mundo, firmado, sin reiniciarse y SIN echar a Vieja
        texto, h_nueva, firma_m = mundo_de("9.0.0")
        banco.mundo_cliente = (texto, firma_m)
        nueva = Cli(banco, "Nueva", huella=h_nueva, juego="9.0.0", firmado=True)
        assert nueva.ok and nueva.pidio_mundo and nueva.ok["mundo"] == {"version": "9.0.0", "huella": h_nueva, "igual": True}
        assert banco.srv.mundo["version"] == "9.0.0" and "isla_nueva" in banco.srv.mundo["mapas"] and "laser" in banco.srv.mundo["armas"]
        aviso = vieja.leer("aviso", filtro=lambda m: "9.0.0" in m["texto"])
        assert "puede seguir jugando" in aviso["texto"]
        assert banco.srv.jugadores[vieja.id].dentro and vieja.nada(("expulsado", "cerrado"), 0.5)
        assert vieja.leer("entra")["nombre"] == "Nueva"
        # se ven y se hablan
        nueva.estado(x=x + 4, y=y, di=1000)
        assert vieja.leer("estados", filtro=lambda m: str(nueva.id) in m["e"])["e"][str(nueva.id)]["m"] == "puerto_bravo"
        assert nueva.leer("estados", filtro=lambda m: str(vieja.id) in m["e"])
        vieja.enviar({"t": "chat", "texto": "¿Qué tal la versión nueva?"})
        assert nueva.leer("chat")["nombre"] == "Vieja"
        nueva.enviar({"t": "chat", "texto": "Igual, con una isla más."})
        assert vieja.leer("chat")["nombre"] == "Nueva"
        # pelean con lo que las dos conocen: el servidor decide igual que siempre
        banco.hacer(lambda: setattr(banco.srv, "rng", __import__("random").Random(1)))
        golpe = None
        for _ in range(12):
            vieja.enviar({"t": "ataque", "a": nueva.id, "arma": "pistola"})
            time.sleep(0.45)
            try:
                golpe = nueva.leer(("herido", "silbido"), 0.1)
                break
            except AssertionError:
                pass
        assert golpe and golpe["nombre"] == "Vieja"
        # Nueva usa lo que solo tiene su versión: un arma nueva. El servidor la conoce (va con su mundo) y Vieja recibe
        # el golpe con el nombre de un arma que su juego no tiene: su juego lo deja pasar (se prueba más abajo con el juego de verdad).
        golpe = None
        for _ in range(12):
            nueva.estado(x=x + 4, y=y, ar="laser")
            nueva.enviar({"t": "ataque", "a": vieja.id, "arma": "laser"})
            time.sleep(0.3)
            try:
                golpe = vieja.leer("herido", 0.1)
                break
            except AssertionError:
                pass
        assert golpe and golpe["arma"] == "laser"
        assert nueva.nada("aviso", 0.3)                           # a Nueva nadie le dice que su arma no existe: aquí sí existe
        # Nueva coge un vehículo que Vieja no tiene y lo aparca: a Vieja le llega, y su juego no lo pone
        nueva.estado(x=x + 4, y=y, v="aerodeslizador")
        nueva.enviar({"t": "veh_tomar", "modelo": "aerodeslizador", "nombre": "Aero de Nueva", "ref": 1})
        vid = nueva.leer("veh_tuyo")["id"]
        assert vieja.leer("veh_ocupado")["v"]["modelo"] == "aerodeslizador"
        assert vieja.leer("estados", filtro=lambda m: m["e"].get(str(nueva.id), {}).get("v") == "aerodeslizador")
        nueva.estado(x=x + 4, y=y)
        nueva.enviar({"t": "veh_dejar", "id": vid, "x": x + 4, "y": y, "r": 0, "salud": 100})
        assert vieja.leer("veh_libre")["v"]["modelo"] == "aerodeslizador"
        # Nueva se va a la localidad nueva: Vieja sabe que anda por otra parte, y no pasa nada más
        nueva.estado(mapa="isla_nueva", x=50.0, y=50.0)
        assert vieja.leer("estados", espera=6, filtro=lambda m: m["e"].get(str(nueva.id), {}).get("m") == "isla_nueva")
        # Nueva compra el negocio que solo existe en su versión: a Vieja le llega el aviso de un lugar que no conoce
        nueva.estado(x=x + 4, y=y, di=5000)
        nueva.enviar({"t": "prop_comprar", "lugar": "local_9.0.0"})
        assert vieja.leer("prop")["lugar"] == "local_9.0.0"
        # Vieja intenta lo que su versión no puede saber que existe: nada se rompe
        vieja.enviar({"t": "prop_comprar", "lugar": "local_9.0.0"})
        assert vieja.leer("prop_no")["nombre"] == "Nueva"
        # Vieja sale y vuelve a entrar con su versión de siempre: entra, sin que se le pida nada, y sabe con qué va el servidor
        vieja.cerrar()
        time.sleep(0.4)
        banco.mundo_cliente = ("", "")
        vuelve = Cli(banco, "Vieja", semilla=vieja.semilla, juego=v_vieja, firmado=True)
        assert vuelve.ok and not vuelve.pidio_mundo and vuelve.ok["mundo"] == {"version": "9.0.0", "huella": h_nueva, "igual": False}
        assert vuelve.ok["props"]["local_9.0.0"]["nombre"] == "Nueva" and any(v["modelo"] == "aerodeslizador" for v in vuelve.ok["vehiculos"])
        assert banco.srv.mundo["version"] == "9.0.0"              # y no ha hecho retroceder al servidor
        # quien administra ve con qué versión va cada uno
        gente = {g["nombre"]: g for g in banco.hacer(banco.srv.resumen)["jugadores"]}
        assert gente["Vieja"]["juego"] == v_vieja and not gente["Vieja"]["mismo_mundo"] and gente["Nueva"]["juego"] == "9.0.0" and gente["Nueva"]["mismo_mundo"]
        assert not [l for l in banco.lineas if l.startswith("Error")], [l for l in banco.lineas if l.startswith("Error")]
    finally:
        banco.parar()
    # el servidor se apaga y vuelve: sigue con el mundo nuevo y sigue conociendo el anterior
    banco = Banco(tmp_path, de_disco=True)
    try:
        assert banco.srv.mundo["version"] == "9.0.0" and banco.srv.mundos_conocidos[h_vieja] == v_vieja
        otra = Cli(banco, "Otra vieja", juego=v_vieja)
        assert otra.ok and not otra.pidio_mundo and not otra.ok["mundo"]["igual"]
    finally:
        banco.parar()


def test_quien_va_por_delante_y_quien_va_por_detras_del_servidor(tmp_path):
    """Un servidor que no adopta mundos nuevos, y jugadores con versiones que nunca ha visto, anteriores y posteriores."""
    banco = servidor_de_pruebas(tmp_path, actualizar_mundo="no")
    try:
        h_servidor = banco.srv.mundo["huella"]
        # una versión posterior, firmada: el servidor no la adopta (así está configurado), pero comprueba la firma y le deja entrar
        texto, h_futura, firma_m = mundo_de("9.0.0")
        banco.mundo_cliente = (texto, firma_m)
        futura = Cli(banco, "Futura", huella=h_futura, juego="9.0.0", firmado=True)
        assert futura.ok and futura.pidio_mundo and futura.ok["mundo"]["igual"] is False and banco.srv.mundo["huella"] == h_servidor
        assert banco.srv.mundos_conocidos[h_futura] == "9.0.0"
        # la segunda vez ya la conoce: no hace falta traerle nada
        banco.mundo_cliente = ("", "")
        otra = Cli(banco, "Otra futura", huella=h_futura, juego="9.0.0", firmado=True)
        assert otra.ok and not otra.pidio_mundo
        # una versión anterior que el servidor no había visto nunca, firmada: igual
        texto, h_antigua, firma_m = mundo_de("0.9.0", nuevo=False)
        banco.mundo_cliente = (texto, firma_m)
        antigua = Cli(banco, "Antigua", huella=h_antigua, juego="0.9.0", firmado=True)
        assert antigua.ok and antigua.pidio_mundo and banco.srv.mundo["huella"] == h_servidor
        # lo que trae cada una y el servidor no tiene, no rompe nada
        x, y = lejos_de_todo()
        futura.estado(mapa="isla_nueva", x=5.0, y=5.0, ar="laser")
        assert "localidad no existe" in futura.leer("aviso", filtro=lambda m: "localidad" in m["texto"])["texto"]
        futura.enviar({"t": "veh_tomar", "modelo": "aerodeslizador", "nombre": "Aero", "ref": 1})
        futura.enviar({"t": "prop_comprar", "lugar": "local_9.0.0"})
        futura.enviar({"t": "mision_ok", "id": "mision_del_futuro"})
        futura.estado(x=x, y=y, ar="laser")
        antigua.estado(x=x + 3, y=y)
        assert antigua.leer("estados", filtro=lambda m: m["e"].get(str(futura.id), {}).get("m") == "puerto_bravo")
        futura.enviar({"t": "ataque", "a": antigua.id, "arma": "laser"})           # con un arma que aquí no existe: cuenta como las manos
        futura.enviar({"t": "ping"})
        assert futura.leer("pong") and all(banco.srv.jugadores[c.id].dentro for c in (futura, otra, antigua))
        assert not [l for l in banco.lineas if l.startswith("Error")], [l for l in banco.lineas if l.startswith("Error")]
        # sin firma no hay manera de saber que es una versión de verdad: no entra, vaya por delante o por detrás
        texto, h_mod, _ = mundo_de("9.5.0", firmar=False)
        banco.mundo_cliente = (texto, "")
        assert "no puede comprobar" in Cli(banco, "Con mods", huella=h_mod, juego="9.5.0").rechazo
        assert "no puede comprobar" in Cli(banco, "Con mods y cuento", huella=h_mod, juego="9.5.0", firmado=True).rechazo
        texto, h_vieja_mod, _ = mundo_de("0.5.0", firmar=False, nuevo=False)
        banco.mundo_cliente = (texto, "")
        assert "Actualiza el juego" in Cli(banco, "Vieja sin firma", huella=h_vieja_mod, juego="0.5.0").rechazo
        # un mundo firmado pero que no es el que dice la huella: tampoco
        texto, _, firma_m = mundo_de("9.0.0")
        banco.mundo_cliente = (texto, firma_m)
        assert Cli(banco, "Huella falsa", huella="0123456789abcdef", juego="9.0.0", firmado=True).rechazo
        # quien lleva el servidor puede pedir una versión mínima...
        banco.hacer(banco.srv.aplicar_config, {"version_minima": "1.0.0"})
        banco.mundo_cliente = ("", "")
        r = Cli(banco, "Antigua otra vez", huella=h_antigua, juego="0.9.0", firmado=True).rechazo
        assert "pide la versión 1.0.0" in r and "0.9.0" in r
        assert Cli(banco, "Futura otra vez", huella=h_futura, juego="9.0.0", firmado=True).ok
        # ...o pedir a todos exactamente los mismos datos
        banco.hacer(banco.srv.aplicar_config, {"version_minima": "", "versiones": "iguales"})
        assert Cli(banco, "Futura estricta", huella=h_futura, juego="9.0.0", firmado=True).rechazo
        assert "Actualiza el juego" in Cli(banco, "Antigua estricta", huella=h_antigua, juego="0.9.0", firmado=True).rechazo
        assert Cli(banco, "La de siempre", juego=mundo()["version"]).ok
        # ...o no comprobar nada
        banco.hacer(banco.srv.aplicar_config, {"comprobar_datos": "no"})
        assert Cli(banco, "Cualquiera", huella=h_mod, juego="9.5.0").ok
    finally:
        banco.parar()


# ==================================================== el juego de verdad, por su lado
class ServidorDeMentira:
    """Un servidor que contesta lo que contestaría uno de una versión posterior: con mensajes y campos que el juego de
    ahora no conoce. Sin cifrado."""

    def __init__(self, guion):
        self.guion = guion
        self.recibido = []
        self.s = socket.socket()
        self.s.bind(("127.0.0.1", 0))
        self.s.listen(8)
        self.puerto = self.s.getsockname()[1]
        self.vivo = True
        threading.Thread(target=self._aceptar, daemon=True).start()

    def _aceptar(self):
        while self.vivo:
            try:
                c, _ = self.s.accept()
            except OSError:
                return
            threading.Thread(target=self._atender, args=(c,), daemon=True).start()

    def _atender(self, c):
        try:
            c.settimeout(5)
            if c.recv(1, socket.MSG_PEEK) != b"{":               # el juego prueba primero con cifrado: este servidor no cifra
                c.close()
                return
            f = c.makefile("rb")
            primera = f.readline()
            self.recibido.append(json.loads(primera))
            for paso in self.guion:
                if paso == "LEE":
                    self.recibido.append(json.loads(f.readline()))
                else:
                    c.sendall(json.dumps(paso).encode("utf-8") + b"\n")
            time.sleep(0.3)
        except (OSError, ValueError):
            pass
        finally:
            try:
                c.close()
            except OSError:
                pass

    def cerrar(self):
        self.vivo = False
        self.s.close()


def test_el_juego_entra_en_un_servidor_mas_nuevo_que_dice_cosas_que_no_conoce():
    semilla = hashlib.sha256(b"un juego").digest()
    ok = {"t": "ok", "id": 7, "nombre": "Marina", "cuenta": 3, "protocolo": 9, "funciones": ["vehiculos", "teletransporte", 5], "novedad": {"a": 1},
          "mundo": {"version": "9.0.0", "huella": "f" * 16, "igual": False, "extra": 1}, "servidor": {"nombre": "Del futuro", "holograma": True}}
    srv = ServidorDeMentira([{"t": "anuncio_previo", "texto": "algo que este juego no entiende"}, {"t": "reto", "n": "abc", "servidor": "Del futuro", "v": 9, "vmin": 2, "calidad": "alta"},
                             "LEE", {"t": "cola_de_espera", "puesto": 1}, {"t": "otra_cosa"}, ok])
    try:
        cli = enlinea.ClienteServidor()
        bien, r = cli.conectar_servidor("127.0.0.1", srv.puerto, "Marina", semilla, "0" * 16, timeout=5)
        assert bien, r
        assert r["id"] == 7 and cli.protocolo == enlinea.VERSION_RED       # se queda con el protocolo que él habla
        hola = srv.recibido[0]
        assert hola["v"] == enlinea.VERSION_RED and hola["vmin"] == enlinea.PROTOCOLO_MIN and hola["juego"]
        assert srv.recibido[1]["t"] == "firma"
        cli.cerrar()
    finally:
        srv.cerrar()
    # un servidor que ya no habla con juegos como este: se dice claro, y no se queda colgado
    srv = ServidorDeMentira([{"t": "reto", "n": "abc", "v": 9, "vmin": enlinea.VERSION_RED + 1}])
    try:
        bien, motivo = enlinea.ClienteServidor().conectar_servidor("127.0.0.1", srv.puerto, "Marina", semilla, "0" * 16, timeout=5)
        assert not bien and "necesita una versión más nueva del juego" in motivo
    finally:
        srv.cerrar()
    # y lo que no es un servidor de Puerto Bravo sigue sin colar
    srv = ServidorDeMentira([{"t": "hola_soy_otra_cosa"}, {"t": "y_sigo"}, {"t": "y_sigo"}, {"t": "y_sigo"}])
    try:
        bien, motivo = enlinea.ClienteServidor().conectar_servidor("127.0.0.1", srv.puerto, "Marina", semilla, "0" * 16, timeout=3)
        assert not bien and "no es un servidor de Puerto Bravo" in motivo
    finally:
        srv.cerrar()


def test_el_juego_de_ahora_juega_en_un_servidor_con_el_mundo_de_una_version_posterior(robot, tmp_path):
    """El juego de verdad, con su versión, en un servidor que ya va con el mundo de una versión más adelantada, junto a
    una jugadora que tiene esa versión y usa lo que solo ella tiene. Nada se rompe y cada cual ve lo que conoce."""
    from juego import VERSION
    from test_enlinea import entrar
    banco = servidor_de_pruebas(tmp_path)
    try:
        texto, h_nueva, firma_m = mundo_de("99.0.0")
        banco.mundo_cliente = (texto, firma_m)
        nueva = Cli(banco, "Nueva", huella=h_nueva, juego="99.0.0", firmado=True)
        assert nueva.ok and banco.srv.mundo["version"] == "99.0.0"
        nueva.estado(mapa="isla_nueva", x=50.0, y=50.0, v="aerodeslizador", ar="laser")
        nueva.enviar({"t": "veh_tomar", "modelo": "aerodeslizador", "nombre": "Aero de Nueva", "ref": 1})
        vid = nueva.leer("veh_tuyo")["id"]
        nueva.enviar({"t": "prop_comprar", "lugar": "local_99.0.0"})
        time.sleep(0.3)
        # entra el juego de verdad, con la versión de ahora
        p = entrar(robot, banco, "Marina")
        assert p.sv["mundo"] == {"version": "99.0.0", "huella": h_nueva, "igual": False} and "versiones" in p.sv["funciones"]
        dicho = robot.dicho()
        assert "versión 99.0.0" in dicho and VERSION in dicho and "puedes jugar" in dicho
        # y lo tiene siempre a mano en el móvil: En línea, Datos y reglas de este servidor
        import pygame
        from juego import menus_enlinea
        menus_enlinea.menu(p)
        m = robot.app.pila[-1]
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Datos y reglas de este servidor")
        robot.tecla(pygame.K_RETURN)
        datos = robot.app.pila[-1]
        textos = [o.texto for o in datos.opciones]
        assert any("versión 99.0.0" in t and VERSION in t and "cada uno con lo que su versión conoce" in t for t in textos), textos
        assert any(t.startswith("Caben 32 jugadores") for t in textos), textos
        robot.app.cerrar(datos)
        robot.app.cerrar(m)
        # ve a Nueva, que está en una localidad que su juego no tiene, en un vehículo que tampoco tiene
        r = next(iter(p.remotos.values()))
        fin = time.time() + 8
        while time.time() < fin and r.mapa != "isla_nueva":
            robot.frames(3)
            time.sleep(0.05)
        assert r.nombre == "Nueva" and r.mapa == "isla_nueva" and r.veh == "utilitario"
        assert "otra localidad" in p.donde_esta(r)
        # el servidor le manda cosas que su versión no conoce: tipos nuevos, y tipos conocidos con otra forma
        def cosas_del_futuro():
            for m in ({"t": "teletransporte", "a": [1, 2]}, {"t": "entra"}, {"t": "estados", "e": {"x": 1, str(r.id): "aquí"}, "holograma": [1]},
                      {"t": "veh_libre", "v": {"id": 999, "modelo": "nave_espacial", "m": p.mundo.id, "x": p.j.x + 5, "y": p.j.y, "r": 0, "salud": 50, "por": None}},
                      {"t": "prop", "lugar": "sitio_que_no_existe", "cuenta": 77, "nombre": "Nueva", "oferta": "cara"}, {"t": "recibe", "nombre": "Nueva", "clase": "arma", "id": "laser", "n": 1},
                      {"t": "hora", "h": {"reloj": "mediodía"}}, {"t": "aviso", "texto": "Mensaje normal después de todo eso", "son": "sonido_que_no_existe"}):
                banco.srv._a_todos(m)
        banco.hacer(cosas_del_futuro)
        time.sleep(0.3)
        robot.frames(20)
        assert p.en_servidor and p.red.conectado
        dicho = robot.dicho()
        assert "Mensaje normal después de todo eso" in dicho and "no existe en tu versión del juego" in dicho
        # Nueva viene a su lado con el arma nueva y le da: el golpe llega aunque su juego no conozca el arma
        x, y = lejos_de_todo(p.mundo.id)
        p.teletransportar(x, y)
        robot.frames(10)
        time.sleep(0.3)
        nueva.estado(mapa=p.mundo.id, x=x + 4, y=y, ar="laser")
        fin = time.time() + 5
        while time.time() < fin and not (r.mapa == p.mundo.id and r.visto):
            robot.frames(3)
            time.sleep(0.02)
        assert r.mapa == p.mundo.id
        p.sv["protegido"] = 0
        banco.hacer(lambda: (setattr(banco.srv, "rng", __import__("random").Random(3)), setattr(banco.srv.jugadores[p.red.id], "protegido", 0), setattr(banco.srv.jugadores[nueva.id], "protegido", 0)))
        salud = p.j.salud
        for _ in range(15):
            nueva.estado(mapa=p.mundo.id, x=x + 4, y=y, ar="laser")
            nueva.enviar({"t": "evento", "que": "d:laser"})
            nueva.enviar({"t": "ataque", "a": p.red.id, "arma": "laser"})
            time.sleep(0.3)
            robot.frames(4)
            if p.j.salud < salud:
                break
        assert p.j.salud < salud and p.en_servidor
        # deja aparcado su vehículo nuevo aquí mismo: el juego de ahora no lo pone, y sigue
        nueva.estado(mapa=p.mundo.id, x=x + 4, y=y, v="aerodeslizador")
        nueva.enviar({"t": "veh_dejar", "id": vid, "x": x + 4, "y": y, "r": 0, "salud": 100})
        time.sleep(0.3)
        robot.frames(10)
        assert vid in p.sv["vehs"] and p._sv_copia(vid) is None
        # el personaje se guarda y el juego sale con normalidad
        assert p.sv_guardar(ya=True)
        p.sv_salir()
        assert not [l for l in banco.lineas if l.startswith("Error")], [l for l in banco.lineas if l.startswith("Error")]
    finally:
        banco.parar()


def test_el_juego_avisa_si_el_personaje_se_guardo_con_una_version_mas_nueva(robot, tmp_path):
    """El personaje vive en el servidor. Si alguien jugó con una versión más nueva y vuelve con una anterior, se le dice."""
    import pygame
    from juego import VERSION
    from juego import menus_enlinea
    from juego.menus import Menu
    from test_enlinea import entrar
    banco = Banco(tmp_path)
    try:
        app = robot.app
        p = entrar(robot, banco, "Marina")
        cuenta = p.sv["cuenta"]
        assert banco.hacer(lambda: banco.srv.alm.cuenta(cuenta)["juego"]) == enlinea.mundo_servidor()["version"]     # el servidor apunta con qué versión entró
        assert p.sv_guardar(ya=True)
        menus_enlinea.menu(p)
        m = app.pila[-1]
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Salir del servidor")
        robot.tecla(pygame.K_RETURN)
        app.pila[-1].i = 1
        robot.tecla(pygame.K_RETURN)
        assert app.partida is None and isinstance(app.pila[-1], Menu)
        time.sleep(0.5)
        # como si la última vez hubiera jugado con una versión posterior
        banco.hacer(lambda: (banco.srv.alm.poner(cuenta, juego="99.0.0"), banco.srv.alm.guardar()))
        app.cfg["servidores"] = [{"nombre": "Servidor de pruebas", "dir": f"puertobravo://127.0.0.1:{banco.puerto}", "cert": ""}]
        m = app.pila[-1]
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Jugar en un servidor")
        robot.tecla(pygame.K_RETURN)
        app.pila[-1].i = 0
        robot.tecla(pygame.K_RETURN)
        robot.saltar_dialogos()
        p2 = app.partida
        assert p2 is not None and p2.en_servidor
        assert "se guardó la última vez con la versión 99.0.0 del juego, más nueva que la tuya" in robot.dicho()
        p2.sv_salir()
    finally:
        banco.parar()


def test_lo_que_dice_el_juego_segun_la_version_del_servidor():
    from juego import VERSION

    class P(enlinea.EnLinea):
        sv = {}
    p = P()
    p.sv = {"mundo": {"version": VERSION, "igual": True}}
    assert p.sv_aviso_version() == ""
    p.sv = {}
    assert p.sv_aviso_version() == ""                            # un servidor anterior, que no dice con qué mundo va
    p.sv = {"mundo": {"version": "99.0.0", "igual": False}}
    assert "hasta que actualices" in p.sv_aviso_version()
    p.sv = {"mundo": {"version": "0.1.0", "igual": False}}
    assert "anterior a la tuya" in p.sv_aviso_version()
    p.sv = {"mundo": {"version": VERSION, "igual": False}}
    assert "no son exactamente" in p.sv_aviso_version()
    assert enlinea.version_tupla("1.10.0") > enlinea.version_tupla("1.7.0") and enlinea.version_tupla("1.7.0") == nucleo.version_tupla("1.7.0")
    # un mensaje conocido con una forma que no es la de esta versión no tumba el juego; uno desconocido se deja pasar
    p.en_servidor = True
    p.remotos = {}
    assert p.sv_mensaje({"t": "entra"}) is True
    assert p.sv_mensaje({"t": "veh_tuyo"}) is True
    assert p.sv_mensaje({"t": "mensaje_de_otra_version"}) is False
