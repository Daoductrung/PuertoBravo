"""El servidor en línea en la 1.7.1: los arreglos, lo nuevo y, sobre todo, que nada rompe la compatibilidad.

Primero el servidor solo, con clientes de mentira que mandan lo que mandaría un juego nuevo o uno de la 1.7.0. Después
el juego de verdad, dos a la vez, conectados a un servidor local: los canales de rol, la radio de los coches, el
copiloto, «Mis vehículos», y lo que trajeron las tandas anteriores al jugar conectado. No se toca ningún servidor real
ni se sale a la red: todo corre en este equipo.
"""
import ast
import glob
import json
import os
import time

import numpy as np
import pygame
import pytest

from conftest import Robot                                               # noqa: F401
from juego import enlinea, menus_enlinea, menus_online, misvehiculos, musica
from juego.menus import EntradaTexto, Menu
from servidor import almacen, bots, nucleo, opciones
from test_enlinea import ambos, banco, dos, entrar, hasta, juntos        # noqa: F401  (banco y dos son fixtures)
from test_servidor import Banco, Cli, lejos_de_todo, mundo

# Lo que decía saber hacer un servidor de la 1.7.0: con esto se simula uno anterior.
FUNCIONES_170 = ("vehiculos", "combate", "bandas", "barrios", "grupos", "propiedades", "robos", "personajes", "mundo", "versiones")


def _j(b, c):
    return b.srv.jugadores[c.id]


def _estados(c, de, espera=3.0):
    """La ficha de otro jugador tal como le llega a este cliente, al detalle."""
    fin = time.time() + espera
    while time.time() < fin:
        m = c.leer("estados", espera=1.0)
        f = (m.get("e") or {}).get(str(de))
        if f is not None and "vi" in f:
            return f
    raise AssertionError("no llega la ficha de %s" % de)


def _texto(o):
    return o.texto() if callable(o.texto) else o.texto


def _opcion(app, empieza):
    m = app.pila[-1]
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if _texto(o).startswith(empieza))
    return m


def _oir(robot):
    sonados = []
    original = robot.app.mez.sonar

    def sonar(nombre, *a, **kw):
        sonados.append(nombre)
        return original(nombre, *a, **kw)
    robot.app.mez.sonar = sonar
    return sonados


# ====================================================================== el servidor vale con Python 3.8
def test_el_servidor_se_escribe_con_la_gramatica_de_python_3_8_y_solo_con_la_biblioteca_de_serie():
    carpeta = os.path.dirname(nucleo.__file__)
    de_serie = {"asyncio", "binascii", "hashlib", "json", "math", "os", "random", "secrets", "time", "sqlite3", "html", "textwrap", "ssl", "shutil",
                "subprocess", "base64", "zlib", "sys", "signal", "threading", "datetime", "zipfile", "struct", "socket", "argparse", "tempfile", "glob",
                "io", "re", "traceback", "logging", "platform", "getpass", "collections", "functools", "itertools", "contextlib", "errno", "stat"}
    archivos = glob.glob(os.path.join(carpeta, "*.py"))
    assert len(archivos) >= 10
    for ruta in archivos:
        with open(ruta, encoding="utf-8") as f:
            arbol = ast.parse(f.read(), feature_version=(3, 8))
        opcionales = {id(n) for intento in ast.walk(arbol) if isinstance(intento, ast.Try) for n in ast.walk(intento)}
        for nodo in ast.walk(arbol):
            if id(nodo) in opcionales:                           # lo que se intenta y, si no está, se hace de otra manera
                continue
            if isinstance(nodo, ast.Import):
                for n in nodo.names:
                    assert n.name.split(".")[0] in de_serie, (ruta, n.name)
            elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
                assert (nodo.module or "").split(".")[0] in de_serie | {"servidor"}, (ruta, nodo.module)


def test_las_opciones_nuevas_estan_descritas_y_salen_en_el_panel_y_en_la_guia():
    for clave, serie in (("rol", "si"), ("rol_metros", 30), ("radio_coches", "si"), ("ganancia_acumula", 3), ("encargos_hora", 6), ("encargo_max", 15000)):
        assert opciones.POR_CLAVE[clave].defecto == serie and not opciones.POR_CLAVE[clave].reinicio, clave
    assert [o.clave for o in opciones.de_seccion("rol")] == ["rol", "rol_metros", "radio_coches"]
    # en el panel, las letras de acceso de cada pestaña salen de las etiquetas y no se repiten
    letras = "abcdefghijklmnopqrstuvwxyz"
    for ident, _, _ in opciones.SECCIONES:
        usadas = set("acpf")                                     # Aceptar, Cancelar, Aplicar y Valores de fábrica
        for o in opciones.de_seccion(ident):
            libre = next((ch.lower() for ch in o.etiqueta if ch.lower() in letras and ch.lower() not in usadas), None)
            assert libre is not None, (ident, o.clave)
            usadas.add(libre)
    with open(os.path.join(os.path.dirname(os.path.dirname(nucleo.__file__)), "data", "docs", "servidor_es.html"), encoding="utf-8") as f:
        guia = f.read()
    for palabra in ("<code>rol</code>", "<code>rol_metros</code>", "<code>radio_coches</code>", "<code>ganancia_acumula</code>", "<code>encargos_hora</code>",
                    "programa de voz", "barra yo", "encargos repetibles"):
        assert palabra in guia, palabra
    for marca in ("Discord", "TeamSpeak", "Mumble", "Skype", "WhatsApp"):      # no se recomienda ninguna marca
        assert marca.lower() not in guia.lower(), marca


# ====================================================================== 2.2: el copiloto
def test_al_copiloto_no_le_atropella_nadie_ni_con_un_juego_nuevo_ni_con_uno_anterior(banco):
    x, y = lejos_de_todo()
    a, c = Cli(banco, "Ana"), Cli(banco, "Ciro")
    a.estado(x=x, y=y, v="sedan", s=15.0)
    c.estado(x=x + 1, y=y)
    time.sleep(0.3)
    # a pie y delante del coche, sí le atropella: eso no ha cambiado
    a.enviar({"t": "atropello", "a": c.id})
    assert c.leer("herido")["arma"] == "atropello" and a.leer("impacto")["atropello"]
    # un juego de la 1.7.0 dice que sube con el mensaje de siempre: el servidor lo entiende
    c.enviar({"t": "act", "d": {"que": "sube", "a": a.id}})
    assert a.leer("act")["d"]["que"] == "sube"
    time.sleep(1.1)
    a.enviar({"t": "atropello", "a": c.id})
    assert c.nada("herido", 0.6) and a.nada("impacto", 0.2)
    assert _j(banco, c).pasajero_de == a.id and _estados(a, c.id)["pj"] == a.id      # y los demás saben que va de pasajero
    # tampoco se le atraca «a pie», y la chapa le cubre de los disparos como al conductor
    a.cola.clear()
    c.enviar({"t": "atraco", "a": a.id})
    assert "a pie" in c.leer("aviso")["texto"]
    # se baja: vuelve a estar en la calle
    c.enviar({"t": "act", "d": {"que": "baja", "a": a.id}})
    time.sleep(1.1)
    a.enviar({"t": "atropello", "a": c.id})
    assert c.leer("herido")["arma"] == "atropello"
    assert "pj" not in _estados(a, c.id)
    # un juego nuevo lo dice además con su posición
    c.estado(x=x + 1, y=y, pj=a.id)
    time.sleep(1.1)
    a.enviar({"t": "atropello", "a": c.id})
    assert c.nada("herido", 0.6)
    # y no sirve de escudo: si el vehículo que le lleva se va lejos, o su conductor se baja, deja de contar como pasajero
    d = Cli(banco, "Dora")
    d.estado(x=x + 2, y=y, v="sedan", s=15.0)
    a.estado(x=x + 300, y=y, v="sedan", s=15.0)
    time.sleep(0.4)
    d.enviar({"t": "atropello", "a": c.id})
    assert c.leer("herido")["de"] == d.id
    # un identificador que no existe, o el suyo propio, no cuela
    c.estado(x=x + 1, y=y, pj=c.id)
    time.sleep(0.2)
    assert _j(banco, c).pasajero_de is None
    c.estado(x=x + 1, y=y, pj="1; DROP")
    time.sleep(0.2)
    assert _j(banco, c).pasajero_de is None


# ====================================================================== 2.6: los topes de dinero
def test_el_tope_de_dinero_se_dice_con_cifras_y_el_margen_se_acumula(tmp_path):
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=500, ganancia_acumula=3)
    try:
        a = Cli(b, "Ana", sabe=["topes"])
        eco = a.ok["servidor"]["economia"]
        assert eco["tope"] == 3600 and eco["acumula"] == 10800 and eco["horas"] == 3 and eco["por_minuto"] == 60 and eco["encargos_hora"] == 6
        assert "topes" in a.ok["funciones"] and "encargos" in a.ok["funciones"]
        a.estado(di=300, ba=100)
        time.sleep(0.2)
        ja = _j(b, a)
        assert ja.saldo == 400 and abs(ja.margen - 900) < 5       # quien entra por primera vez, con un cuarto de hora
        # gana 2000 de golpe con 900 de margen: se le aceptan 900 y se le dice todo con cifras
        a.estado(di=2300, ba=100)
        q = a.leer("saldo")
        assert 1095 <= q["quita"] <= 1100 and q["ganado"] == 2000 and 900 <= q["aceptado"] <= 905 and q["tope"] == 3600 and q["acumula"] == 10800
        assert q["margen"] == 0 and q["por_minuto"] == 60 and q["saldo"] == ja.saldo
        assert any("el tope es de 3600 por hora" in t for t in b.lineas)
        a.estado(di=2300 - q["quita"], ba=100)
        # el margen que no se usa se guarda: diez horas después no tiene una hora, tiene las tres del tope
        b.hacer(lambda: (setattr(ja, "margen", 0.0), setattr(ja, "t_margen", time.monotonic() - 36000), setattr(ja, "t_saldo", 0.0)))
        a.enviar({"t": "economia"})
        e = a.leer("economia")["e"]
        assert 10795 <= e["margen"] <= 10800
        base = ja.saldo
        a.estado(di=base - 100 + 9000, ba=100)                   # una buena racha entera cabe
        time.sleep(0.3)
        assert ja.saldo == base + 9000 and a.nada("saldo", 0.3)
        # salir y volver a entrar no rellena el margen: se guarda con la cuenta, y lo de fuera se va sumando
        margen = ja.margen
        a.enviar({"t": "guardar", "p": {"jugador": {"dinero": base - 100 + 9000, "banco": 100}}, "ya": True})
        a.leer("guardado")
        a.enviar({"t": "adios"})
        a.cerrar()
        time.sleep(0.4)
        b.reloj.t += 1800                                         # media hora fuera
        a2 = Cli(b, "Ana", sabe=["topes"])
        assert abs(_j(b, a2).margen - (margen + 1800)) < 30 and abs(a2.ok["servidor"]["economia"]["margen"] - (margen + 1800)) < 30
        a2.cerrar()
    finally:
        b.parar()
    # con ganancia_acumula a 1, como en la 1.7.0, nunca hay más margen que el de una hora
    b = Banco(tmp_path / "uno", economia="si", ganancia_hora=3600, ganancia_acumula=1)
    try:
        a = Cli(b, "Ana")
        a.estado(di=300, ba=0)
        time.sleep(0.2)
        ja = _j(b, a)
        b.hacer(lambda: setattr(ja, "t_margen", time.monotonic() - 36000))
        a.estado(di=300 + 5000, ba=0)
        q = a.leer("saldo")
        assert 1395 <= q["quita"] <= 1400
    finally:
        b.parar()


def test_los_encargos_repetibles_se_reconocen_con_su_limite(tmp_path):
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=500, encargos_hora=2, encargo_max=5000)
    try:
        a = Cli(b, "Ana", sabe=["topes", "encargos"])
        a.estado(di=400, ba=0)
        time.sleep(0.2)
        ja = _j(b, a)
        sin_margen = lambda: b.hacer(lambda: (setattr(ja, "margen", 0.0), setattr(ja, "t_margen", time.monotonic()), setattr(ja, "t_saldo", 0.0)))
        di = 400
        # dos contratos: sus pagas no gastan la ganancia por hora
        for paga in (1900, 2500):
            sin_margen()
            a.enviar({"t": "mision_ok", "id": "contrato", "encargo": 1, "n": paga})
            di += paga
            a.estado(di=di, ba=0)
            time.sleep(0.3)
            assert ja.saldo == di and a.nada("saldo", 0.3)
        # el tercero de la hora ya no se reconoce: cuenta contra el margen, y se le explica
        sin_margen()
        a.cola.clear()
        a.enviar({"t": "mision_ok", "id": "contrato", "encargo": 1, "n": 2000})
        texto = a.leer("aviso")["texto"]
        assert "2 encargos de este tipo" in texto and "minutos" in texto
        a.estado(di=di + 2000, ba=0)
        assert 1990 <= a.leer("saldo")["quita"] <= 2000
        a.estado(di=di, ba=0)
        # otro tipo va por su cuenta, pero nunca por encima de lo que ese tipo puede pagar ni del máximo del servidor
        sin_margen()
        a.enviar({"t": "mision_ok", "id": "atraco_banco", "encargo": 1, "n": 900000})
        a.estado(di=di + 900000, ba=0)
        q = a.leer("saldo")
        assert q["aceptado"] == 5000 and q["quita"] == 895000     # encargo_max manda
        di += 5000
        a.estado(di=di, ba=0)
        # un tipo que nadie conoce no se reconoce, y un encargo sin paga tampoco
        sin_margen()
        a.enviar({"t": "mision_ok", "id": "me_lo_invento", "encargo": 1, "n": 3000})
        a.enviar({"t": "mision_ok", "id": "boxeo", "encargo": 1, "n": "mucho"})
        a.enviar({"t": "mision_ok", "id": ["contrato"], "encargo": 1, "n": 100})
        a.estado(di=di + 3000, ba=0)
        assert 2990 <= a.leer("saldo")["quita"] <= 3000
        a.estado(di=di, ba=0)
        # la paga reconocida vale para ese momento: no se queda guardada para justificar otra cosa más tarde
        sin_margen()
        a.enviar({"t": "mision_ok", "id": "boxeo", "encargo": 1, "n": 400})
        time.sleep(0.2)
        b.hacer(lambda: [f.__setitem__(0, f[0] - 60) for f in ja.fiado])
        a.estado(di=di + 400, ba=0)
        assert 395 <= a.leer("saldo")["quita"] <= 400
        a.estado(di=di, ba=0)
        # entrar otra vez no pone la cuenta de encargos a cero
        a.enviar({"t": "adios"})
        a.cerrar()
        time.sleep(0.4)
        a = Cli(b, "Ana", sabe=["topes", "encargos"])
        a.estado(di=di, ba=0)
        time.sleep(0.2)
        ja = _j(b, a)
        sin_margen()
        a.enviar({"t": "mision_ok", "id": "contrato", "encargo": 1, "n": 1000})
        assert "encargos de este tipo" in a.leer("aviso")["texto"]
        # un juego de la 1.7.0 no dice que sea un encargo: todo sigue como antes, contra el margen, sin romper nada
        v = Cli(b, "Viejo")
        v.estado(di=300, ba=0)
        time.sleep(0.2)
        jv = _j(b, v)
        b.hacer(lambda: (setattr(jv, "margen", 0.0), setattr(jv, "t_margen", time.monotonic())))
        v.enviar({"t": "mision_ok", "id": "contrato"})
        v.estado(di=1300, ba=0)
        q = v.leer("saldo")
        assert 995 <= q["quita"] <= 1000 and "saldo" in q         # las dos claves que ese juego mira siguen ahí
    finally:
        b.parar()
    # con encargos_hora a 0, ninguno se reconoce: como en la 1.7.0
    b = Banco(tmp_path / "cero", economia="si", ganancia_hora=3600, encargos_hora=0)
    try:
        a = Cli(b, "Ana")
        a.estado(di=400, ba=0)
        time.sleep(0.2)
        ja = _j(b, a)
        b.hacer(lambda: (setattr(ja, "margen", 0.0), setattr(ja, "t_margen", time.monotonic())))
        a.enviar({"t": "mision_ok", "id": "contrato", "encargo": 1, "n": 1000})
        a.estado(di=1400, ba=0)
        assert 995 <= a.leer("saldo")["quita"] <= 1000
    finally:
        b.parar()


def test_el_juego_dice_al_servidor_lo_que_puede_pagar_cada_encargo():
    encargos = mundo()["encargos"]
    for tipo in ("contrato", "boxeo", "mma", "atraco_banco", "atraco_local", "encargo_coche"):
        assert 500 <= encargos[tipo] <= 60000, (tipo, encargos[tipo])
    assert encargos["contrato"] >= 2500 and encargos["atraco_banco"] >= 13000
    with open(os.path.join(os.path.dirname(nucleo.__file__), "mundo.json"), encoding="utf-8") as f:
        guardado = json.load(f)
    assert guardado["encargos"] == encargos and guardado["huella"] == mundo()["huella"]       # el mundo que va con el servidor está al día
    # un mundo de la 1.7.0, que no lo trae: el servidor usa sus cifras
    srv = nucleo.Servidor.__new__(nucleo.Servidor)
    srv.mundo, srv.cfg = {"mapas": {}}, {"encargo_max": 15000}
    assert srv._encargo_tope("contrato") == nucleo.ENCARGOS_DE_SERIE["contrato"] and srv._encargo_tope("no_existe") is None
    srv.mundo = {"encargos": {"contrato": 99999, "velada_del_mod": 700}}
    assert srv._encargo_tope("contrato") == 15000 and srv._encargo_tope("velada_del_mod") == 700


# ====================================================================== la compra y la conexión que se corta
def test_lo_comprado_justo_antes_de_un_corte_no_se_pierde(tmp_path):
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000)
    try:
        def entra(nombre):
            c = Cli(b, nombre)
            return c

        def saldo_guardado(nombre):
            return b.hacer(lambda: b.srv.alm.cuenta_por_nombre(nombre)["saldo"])
        # Ana guarda con 1000, compra algo de 400 y se le corta la conexión antes del siguiente guardado
        a = entra("Ana")
        a.estado(di=1000, ba=0)
        time.sleep(0.2)
        a.enviar({"t": "guardar", "p": {"jugador": {"dinero": 1000, "banco": 0, "objetos": {}}}, "ya": True})
        a.leer("guardado")
        a.estado(di=600, ba=0)
        time.sleep(0.3)
        assert _j(b, a).gasto_pend == 400
        a.cerrar()                                               # sin despedirse y sin guardar
        assert hasta_que(lambda: saldo_guardado("Ana") == 1000)
        assert hasta_que(lambda: any("sin guardar su última compra" in t and "400" in t for t in list(b.lineas)))
        assert hasta_que(lambda: saldo_guardado("Ana") == 1000)
        a = entra("Ana")                                         # vuelve: su personaje tiene los 1000 y el servidor se los reconoce
        assert a.ok["saldo"] == 1000 and a.ok["partida"]["jugador"]["dinero"] == 1000
        # si el juego llegó a guardar después de comprar, no hay nada que devolver
        a.estado(di=1000, ba=0)
        time.sleep(0.2)
        a.estado(di=700, ba=0)
        time.sleep(0.2)
        a.enviar({"t": "guardar", "p": {"jugador": {"dinero": 700, "banco": 0, "objetos": {"botiquin": 3}}}, "ya": True})
        a.leer("guardado")
        a.cerrar()
        assert hasta_que(lambda: not any(j.cuenta == a.ok["cuenta"] for j in b.srv.jugadores.values()))
        assert saldo_guardado("Ana") == 700
        # no es una manera de fabricar dinero: lo que se le da a otro jugador no vuelve
        a, c = entra("Ana"), entra("Ciro")
        a.estado(di=700, ba=0)
        c.estado(di=0, ba=0)
        time.sleep(0.3)
        a.enviar({"t": "dinero", "a": c.id, "n": 500})
        assert c.leer("dinero")["n"] == 500
        a.estado(di=200, ba=0)
        time.sleep(0.3)
        assert _j(b, a).gasto_pend == 0
        a.cerrar()
        assert hasta_que(lambda: saldo_guardado("Ana") == 200)
        # ni lo que le quita un atracador: eso no es una compra suya
        c.estado(di=500, ba=0, ar="pistola")
        x, y = lejos_de_todo()
        d = entra("Dora")
        d.estado(x=x, y=y, di=1000, ba=0)
        time.sleep(0.2)
        d.enviar({"t": "guardar", "p": {"jugador": {"dinero": 1000, "banco": 0}}, "ya": True})
        d.leer("guardado")
        c.estado(x=x + 2, y=y, di=500, ba=0, ar="pistola")
        time.sleep(0.3)
        c.enviar({"t": "atraco", "a": d.id})
        pierde = d.leer("atracado")["pierde"]
        assert pierde > 0
        d.estado(x=x, y=y, di=1000 - pierde, ba=0)
        time.sleep(0.3)
        assert _j(b, d).gasto_pend == 0
        d.cerrar()
        assert hasta_que(lambda: saldo_guardado("Dora") == 1000 - pierde)
        # ni una casa, que ya es suya en el servidor
        casa = next(l for l in b.srv.lugares.values() if l["tipo"] == "casa" and l["precio"] <= 4000)
        e = entra("Eva")
        e.estado(di=5000, ba=0)
        time.sleep(0.2)
        e.enviar({"t": "guardar", "p": {"jugador": {"dinero": 5000, "banco": 0}}, "ya": True})
        e.leer("guardado")
        e.estado(di=5000 - casa["precio"], ba=0)
        e.enviar({"t": "prop_comprar", "lugar": casa["id"]})
        time.sleep(0.4)
        e.estado(di=5000 - casa["precio"], ba=0)
        time.sleep(0.3)
        assert _j(b, e).gasto_pend == 0 and b.hacer(lambda: b.srv.alm.propiedad(casa["id"])["pagada"]) == 1
        e.cerrar()
        assert hasta_que(lambda: saldo_guardado("Eva") == 5000 - casa["precio"])
    finally:
        b.parar()


def hasta_que(cond, segundos=6.0):
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            if cond():
                return True
        except Exception:
            pass
        time.sleep(0.05)
    return False


def test_el_personaje_guardado_vuelve_entero_con_su_despensa(banco):
    a = Cli(banco, "Ana")
    j = {"dinero": 250, "banco": 0, "despensa": {"casa_abuela": [{"id": "huevos", "n": 6, "dia": 4}, {"id": "huevos_patatas", "n": 2, "plato": True, "dia": 3}]},
         "encima": [{"id": "zumo", "n": 1, "dia": 9}], "cocina_practica": 35, "garajes": {"casa_abuela": [{"modelo": "sedan", "nombre": "La Bala", "mejoras": {"turbo": 2}}]},
         "armas": {"revolver": {"cargador": 6, "reserva": 30}}, "algo_que_el_servidor_no_conoce": {"ñ": [1, 2, 3]}}
    a.enviar({"t": "guardar", "p": {"version": 9, "jugador": j, "dia": 7}, "ya": True})
    a.leer("guardado")
    a.enviar({"t": "adios"})
    a.cerrar()
    time.sleep(0.4)
    a = Cli(banco, "Ana")
    assert a.ok["partida"]["jugador"] == j and a.ok["partida"]["dia"] == 7      # el servidor no filtra ni toca nada del personaje


# ====================================================================== los apuntes de la caja
def test_los_apuntes_de_la_caja_de_la_banda_tienen_tope(tmp_path):
    ruta = str(tmp_path / "a.db")
    alm = almacen.Almacen(ruta)
    c = alm.crear_cuenta("a" * 64, "Ana")
    banda = alm.crear_banda("Las Listas", c["id"])
    otra = alm.crear_banda("Los Otros", alm.crear_cuenta("b" * 64, "Blas")["id"])
    for k in range(almacen.MAX_APUNTES + 150):
        alm.apunte(banda, "Ana", 10, "ingreso %d" % k)
    alm.apunte(otra, "Blas", 7, "ingreso")
    cuantos = lambda bd: alm.db.execute("SELECT COUNT(*) AS n FROM apuntes WHERE banda=?", (bd,)).fetchone()["n"]
    assert cuantos(banda) == almacen.MAX_APUNTES and cuantos(otra) == 1
    assert alm.banda(banda)["caja"] == 10 * (almacen.MAX_APUNTES + 150)       # la caja no cambia: solo se olvidan los apuntes viejos
    assert alm.apuntes(banda, 1)[0]["motivo"] == "ingreso %d" % (almacen.MAX_APUNTES + 149)
    # una base de datos de antes, que ya había crecido: se poda al abrirla
    for k in range(500):
        alm.db.execute("INSERT INTO apuntes (banda, momento, nombre, cantidad, motivo) VALUES (?,?,?,?,?)", (otra, 0.0, "Blas", 1, "viejo"))
    alm.cerrar()
    alm = almacen.Almacen(ruta)
    assert alm.db.execute("SELECT COUNT(*) AS n FROM apuntes WHERE banda=?", (otra,)).fetchone()["n"] == almacen.MAX_APUNTES
    # y las columnas nuevas de las cuentas están, también en una base de datos de antes
    assert {"ficha", "margen", "t_margen"} <= set(alm.cuenta(c["id"]).keys())
    alm.cerrar()


# ====================================================================== rol por texto, en el servidor
def test_canales_de_rol_alcance_ordenes_y_ficha(tmp_path):
    b = Banco(tmp_path, rol_metros=25)
    try:
        x, y = lejos_de_todo()
        a = Cli(b, "Ana", sabe=["rol"])
        c = Cli(b, "Ciro", sabe=["rol"])
        lejos = Cli(b, "Lola", sabe=["rol"])
        viejo = Cli(b, "Viejo")                                  # un juego de la 1.7.0: no dice saber nada
        assert a.ok["servidor"]["rol"] is True and a.ok["servidor"]["rol_metros"] == 25 and "rol" in a.ok["funciones"] and a.ok["ficha"] == ""
        a.estado(x=x, y=y)
        c.estado(x=x + 10, y=y)
        viejo.estado(x=x, y=y + 12)
        lejos.estado(x=x + 26, y=y)                              # un metro más allá del alcance
        time.sleep(0.3)
        for q in (a, c, lejos, viejo):
            q.cola.clear()
        # en personaje: lo oye quien está cerca; al juego anterior le llega por el canal de cerca, con dos palabras delante
        a.enviar({"t": "chat", "texto": "¿Tienes fuego?", "canal": "ic"})
        m = c.leer("chat")
        assert (m["canal"], m["texto"], m["nombre"]) == ("ic", "¿Tienes fuego?", "Ana")
        m = viejo.leer("chat")
        assert (m["canal"], m["texto"]) == ("cerca", "(en personaje) ¿Tienes fuego?")
        assert lejos.nada("chat", 0.4)
        assert a.leer("rol_oido") == {"t": "rol_oido", "canal": "ic", "n": 2}
        # una acción: el nombre delante
        a.enviar({"t": "chat", "texto": "abre la puerta", "canal": "yo"})
        assert c.leer("chat")["canal"] == "yo" and viejo.leer("chat")["texto"] == "(acción) Ana abre la puerta"
        a.leer("rol_oido")
        # fuera de personaje: a todo el servidor
        a.enviar({"t": "chat", "texto": "¿quedamos a las diez?", "canal": "ooc"})
        assert c.leer("chat")["canal"] == "ooc" and lejos.leer("chat")["canal"] == "ooc"
        m = viejo.leer("chat")
        assert (m["canal"], m["texto"]) == ("todos", "(fuera de personaje) ¿quedamos a las diez?")
        assert a.leer("rol_oido")["n"] == 3
        # las órdenes con barra valen desde cualquier juego, también desde el anterior y por el chat de siempre
        viejo.enviar({"t": "chat", "texto": "/yo se enciende un cigarro"})
        m = c.leer("chat")
        assert (m["canal"], m["texto"], m["nombre"]) == ("yo", "se enciende un cigarro", "Viejo")
        assert viejo.nada("rol_oido", 0.3)                       # al juego anterior no se le manda nada que no conozca
        viejo.enviar({"t": "chat", "texto": "/ep buenas noches"})
        assert c.leer("chat")["canal"] == "ic"
        viejo.enviar({"t": "chat", "texto": "/fp vuelvo en cinco minutos"})
        assert lejos.leer("chat")["canal"] == "ooc"
        viejo.enviar({"t": "chat", "texto": "/yo"})
        assert "Detrás de esa orden" in viejo.leer("aviso")["texto"]
        # nadie cerca: al juego nuevo se le dice con cuántos; al anterior, con un aviso
        time.sleep(0.3)
        for q in (a, c, lejos, viejo):
            q.leer("pong", 0.3) if q.enviar({"t": "ping"}) is None else None      # vacía lo que tuviera pendiente de leer
            q.cola.clear()
        lejos.enviar({"t": "chat", "texto": "hola", "canal": "ic"})
        assert lejos.leer("rol_oido")["n"] == 1 and c.leer("chat")["nombre"] == "Lola"      # a Ciro sí le tiene a tiro; a Ana, no
        assert a.nada("chat", 0.3)
        lejos.estado(x=x + 500, y=y + 400)
        time.sleep(0.2)
        lejos.enviar({"t": "chat", "texto": "hola", "canal": "ic"})
        assert lejos.leer("rol_oido")["n"] == 0
        viejo.estado(x=x + 400, y=y + 300)
        time.sleep(0.2)
        viejo.enviar({"t": "chat", "texto": "/ep ¿hay alguien?"})
        assert "nadie lo bastante cerca" in viejo.leer("aviso")["texto"]
        # el chat de siempre no ha cambiado
        for q in (a, c, lejos, viejo):
            q.cola.clear()
        a.enviar({"t": "chat", "texto": "hola a todos"})
        assert c.leer("chat")["canal"] == "todos" and viejo.leer("chat")["canal"] == "todos"
        a.enviar({"t": "chat", "texto": "hola, vecinos", "canal": "cerca"})
        assert c.leer("chat")["canal"] == "cerca"
        # quien administra sigue dando sus órdenes con la barra, y las de rol son de todos
        assert a.ok["admin"]
        a.enviar({"t": "chat", "texto": "/jugadores"})
        assert "Hay 4" in a.leer("aviso")["texto"]
        a.enviar({"t": "chat", "texto": "/yo saluda con la mano"})
        assert c.leer("chat")["canal"] == "yo"
        c.enviar({"t": "chat", "texto": "/jugadores"})           # quien no administra no da órdenes: es un mensaje más
        assert a.leer("chat")["texto"] == "/jugadores"
        # la ficha: una frase, limpia y con tope; se lee pidiéndola
        a.enviar({"t": "ficha", "texto": "  Camarera del   bar La Gaviota.\x07 No se fía de nadie. " + "x" * 400})
        f = a.leer("ficha")
        assert f["tuya"] and f["texto"].startswith("Camarera del bar La Gaviota. No se fía de nadie.") and len(f["texto"]) == nucleo.MAX_FICHA
        c.enviar({"t": "ficha", "a": a.id})
        f2 = c.leer("ficha")
        assert f2["de"] == a.id and f2["nombre"] == "Ana" and f2["texto"] == f["texto"] and "tuya" not in f2
        viejo.enviar({"t": "chat", "texto": "/ficha Marinero retirado"})
        assert viejo.leer("aviso")["texto"] == "Tu ficha dice ahora: Marinero retirado"
        c.enviar({"t": "ficha", "a": viejo.id})
        assert c.leer("ficha")["texto"] == "Marinero retirado"
        c.enviar({"t": "ficha", "a": 99999})
        assert "ya no está" in c.leer("aviso")["texto"]
        # la ficha se guarda con la cuenta
        a.enviar({"t": "adios"})
        a.cerrar()
        time.sleep(0.4)
        a = Cli(b, "Ana", sabe=["rol"])
        assert a.ok["ficha"] == f["texto"]
        a.enviar({"t": "ficha", "texto": ""})
        assert a.leer("ficha")["texto"] == ""
        # quien lleva el servidor apaga los canales de rol sin reiniciar: se dice, y lo demás sigue igual
        a.estado(x=x, y=y)
        assert b.hacer(lambda: b.srv.aplicar_config({"rol": "no"})) == (["rol"], [])
        c.cola.clear()
        a.enviar({"t": "chat", "texto": "¿me oyes?", "canal": "ic"})
        assert "apagados" in a.leer("aviso")["texto"] and c.nada("chat", 0.3)
        a.enviar({"t": "chat", "texto": "/yo se va"})
        assert "apagados" in a.leer("aviso")["texto"]
        a.enviar({"t": "ficha", "texto": "Otra"})
        assert "apagados" in a.leer("aviso")["texto"]
        c.enviar({"t": "ficha", "a": viejo.id})
        assert c.leer("ficha")["texto"] == ""
        a.enviar({"t": "chat", "texto": "por aquí sí"})
        assert c.leer("chat")["texto"] == "por aquí sí"
        z = Cli(b, "Zoe", sabe=["rol"])
        assert z.ok["servidor"]["rol"] is False
    finally:
        b.parar()


# ====================================================================== la radio y los vehículos, en el servidor
def test_la_emisora_del_vehiculo_viaja_solo_si_es_un_nombre_corto_y_el_servidor_quiere(tmp_path):
    b = Banco(tmp_path)
    try:
        x, y = lejos_de_todo()
        a, c = Cli(b, "Ana"), Cli(b, "Ciro")
        assert a.ok["servidor"]["radio_coches"] is True and "radio" in a.ok["funciones"]
        c.estado(x=x + 5, y=y)
        a.estado(x=x, y=y, v="sedan", s=3.0, ra="bravo")
        assert hasta_que(lambda: _j(b, a).radio == "bravo")
        f = _estados(c, a.id)
        assert f["ra"] == "bravo" and f["v"] == "sedan"
        # lo que no es el nombre corto de una emisora no pasa: ni rutas, ni direcciones, ni textos largos, ni cosas raras
        for malo in ("http://mi.casa/radio.mp3", "C:\\musica\\a.mp3", "../x", "x" * 25, "", 7, ["bravo"], {"a": 1}, "bravo fm", "a.b"):
            a.estado(x=x, y=y, v="sedan", s=3.0, ra=malo)
            time.sleep(0.15)
            assert _j(b, a).radio == "", malo
        assert "ra" not in _estados(c, a.id)
        # a pie no hay radio de coche
        a.estado(x=x, y=y, ra="bravo")
        time.sleep(0.2)
        assert _j(b, a).radio == ""
        # y el servidor la puede apagar para todos, sin reiniciar
        a.estado(x=x, y=y, v="sedan", s=3.0, ra="bravo")
        assert hasta_que(lambda: _j(b, a).radio == "bravo")
        b.hacer(lambda: b.srv.aplicar_config({"radio_coches": "no"}))
        a.estado(x=x, y=y, v="sedan", s=3.0, ra="bravo")
        time.sleep(0.2)
        assert _j(b, a).radio == "" and "ra" not in _estados(c, a.id)
    finally:
        b.parar()


def test_renombrar_traer_y_mandar_al_garaje_un_vehiculo_aparcado(banco):
    x, y = lejos_de_todo()
    a, c = Cli(banco, "Ana"), Cli(banco, "Ciro")
    a.estado(x=x, y=y, v="sedan", s=5.0)
    c.estado(x=x + 30, y=y)
    time.sleep(0.2)
    a.enviar({"t": "veh_tomar", "modelo": "sedan", "nombre": "Sedán", "salud": 90, "ref": 1, "mejoras": {"turbo": 2, "blindaje": 1}})
    vid = a.leer("veh_tuyo")["id"]
    a.enviar({"t": "veh_dejar", "id": vid, "x": x, "y": y, "r": 0, "salud": 90})
    assert c.leer("veh_libre")["v"]["id"] == vid
    a.estado(x=x + 400, y=y + 200)                               # se aleja a pie
    time.sleep(0.2)
    c.cola.clear()
    # ponerle nombre desde lejos: lo guarda el servidor y lo ven los demás
    a.enviar({"t": "veh_nombre", "id": vid, "nombre": "  La <Bala>  de plata  "})
    m = a.leer("veh_mio")
    assert m["que"] == "nombre" and m["v"]["nombre"] == "La Bala de plata" and m["v"]["mejoras"] == {"turbo": 2, "blindaje": 1}
    assert c.leer("veh_libre")["v"]["nombre"] == "La Bala de plata"
    a.enviar({"t": "veh_nombre", "id": vid, "nombre": ""})       # vacío: el del modelo
    assert a.leer("veh_mio")["v"]["nombre"] == mundo()["modelos"]["sedan"]["nombre"]
    c.cola.clear()
    # que se lo traigan: desaparece de donde estaba y aparece a su lado, para todos
    a.enviar({"t": "veh_traer", "id": vid, "x": x + 404, "y": y + 200, "r": 90})
    m = a.leer("veh_mio")
    assert m["que"] == "traer" and (m["v"]["x"], m["v"]["y"], m["v"]["r"]) == (x + 404, y + 200, 90)
    assert c.leer("veh_fuera")["id"] == vid and c.leer("veh_libre", filtro=lambda q: q["v"]["x"] == x + 404)["v"]["id"] == vid
    a.enviar({"t": "veh_traer", "id": vid, "x": 99999, "y": float(-5000)})      # a su lado, no donde él diga
    m = a.leer("veh_mio")
    assert (m["v"]["x"], m["v"]["y"]) == (x + 400, y + 200)
    # lo de otro no es suyo, y el que lleva alguien tampoco se toca
    for orden in ("veh_nombre", "veh_traer", "veh_guardar"):
        c.enviar({"t": orden, "id": vid, "nombre": "Mío"})
        assert c.leer("veh_mio")["que"] == "no"
        c.enviar({"t": orden, "id": "x"})
        assert c.leer("veh_mio")["que"] == "no"
    assert banco.srv.vehiculos[vid]["dueno"] == a.ok["cuenta"]
    # al garaje: el servidor lo quita de la calle y le devuelve la ficha entera para que su juego la guarde
    c.cola.clear()
    a.cola.clear()
    a.enviar({"t": "veh_guardar", "id": vid, "ref": "casa_abuela"})
    m = a.leer("veh_mio")
    assert m["que"] == "garaje" and m["ref"] == "casa_abuela" and m["v"]["modelo"] == "sedan" and m["v"]["salud"] == 90 and m["v"]["mejoras"]["turbo"] == 2
    assert c.leer("veh_fuera")["id"] == vid and vid not in banco.srv.vehiculos
    a.enviar({"t": "veh_guardar", "id": vid})                    # dos veces no lo duplica
    assert a.leer("veh_mio")["que"] == "no"


def test_la_policia_del_servidor_dice_la_salud_de_sus_agentes_y_los_personajes_hablan_con_las_frases_del_juego(banco):
    srv = banco.srv
    x, y = lejos_de_todo()
    a = Cli(banco, "Ana")
    a.estado(x=x, y=y)
    time.sleep(0.2)
    def con_un_agente():                                         # todo de una vez, sin dar tiempo a que el servidor lo mueva o lo retire
        srv.agentes[901] = {"id": 901, "m": "puerto_bravo", "x": x + 5, "y": y, "obj": a.id, "salud": 133.4, "arma": "subfusil",
                            "t_disparo": 99.0, "t_arresto": 0.0, "amart": False, "coche": None}
        try:
            return [f for f in srv.agentes_para(_j(banco, a)) if f[0] == 901][0]
        finally:
            srv.agentes.pop(901, None)
    fila = banco.hacer(con_un_agente)
    assert fila[:5] == [901, x + 5, y, a.id, "subfusil"] and fila[5] == 133       # un juego anterior solo mira los cinco primeros
    # las frases de los personajes del servidor salen de los datos del juego; con un mundo anterior, las de siempre
    frases = mundo()["gente"]["frases"]
    assert set(frases) == {"paseante", "ratero", "pistolero", "ladron", "atracador"} and all(len(v) >= 2 for v in frases.values())
    assert bots.frases_del_mundo({"gente": {"frases": {"ratero": ["Dame eso.", "  ", 5]}}}, "ratero") == ["Dame eso."]
    assert bots.frases_del_mundo({"gente": {"nombres": ["x"]}}, "ratero") == bots.FRASES["ratero"]
    assert bots.frases_del_mundo({}, "paseante") == bots.FRASES["paseante"] and bots.frases_del_mundo(mundo(), "ladron") == frases["ladron"]


# ====================================================================== el juego de verdad, conectado
def _escribir(robot, texto):
    e = robot.app.pila[-1]
    assert isinstance(e, EntradaTexto), type(e)
    e.texto = texto
    robot.tecla(pygame.K_RETURN)


def _al_juego(robot):
    p = robot.app.partida
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)


def _pasar(robot, fotogramas):
    """Deja pasar el tiempo del juego sin ir más deprisa que el reloj de verdad: si no, el juego manda las posiciones tan
    seguidas que el servidor lo toma por alguien que le inunda a mensajes, y le echa."""
    for _ in range(0, fotogramas, 3):
        robot.frames(3)
        time.sleep(0.03)


def _espiar(p):
    """Los tipos de mensaje que manda este juego al servidor desde ahora."""
    enviados = []
    original = p.red.enviar
    p.red.enviar = lambda m: (enviados.append(m.get("t")), original(m))[1]
    return enviados


def _salir_todos(dos, b_):
    for r_ in dos:
        if r_.app.partida is not None:
            r_.app.partida.sv_salir()
    b_.parar()


def test_rol_en_el_juego_canales_sonidos_historial_y_ficha(dos, tmp_path):
    b_ = Banco(tmp_path, rol_metros=30)
    try:
        a, b = dos
        pa, pb = entrar(a, b_, "Ana"), entrar(b, b_, "Blas")
        rb, ra = juntos(pa, pb, a, b, d=6.0)
        assert pa.sv_rol() and pa.sv_sabe("rol") and b_.srv.jugadores[pa.red.id].sabe >= {"rol", "radio", "pasajeros"}
        sa, sb = _oir(a), _oir(b)
        # Mayúsculas F10: hablar en personaje
        a.tecla(pygame.K_F10, pygame.KMOD_SHIFT)
        assert "personaje" in a.app.pila[-1].titulo and "cerca" in a.app.pila[-1].titulo
        _escribir(a, "¿Tienes fuego?")
        assert hasta(lambda: "Ana dice: ¿Tienes fuego?" in b.dicho(), a, b)
        assert "chat_personaje" in sb and "chat_personaje" in sa and "chat" not in sb
        # Control F10: una acción. Se oye el nombre y lo que hace, también quien la escribe
        a.tecla(pygame.K_F10, pygame.KMOD_CTRL)
        assert "hace tu personaje" in a.app.pila[-1].titulo
        _escribir(a, "abre la puerta")
        assert hasta(lambda: "Ana abre la puerta" in b.dicho(), a, b) and "Ana abre la puerta" in a.dicho()
        assert "chat_accion" in sb and "chat_accion" in sa
        # F10 de siempre, con una orden delante: fuera de personaje
        a.tecla(pygame.K_F10)
        _escribir(a, "/fp vuelvo en cinco minutos")
        assert hasta(lambda: "Ana, fuera de personaje: vuelvo en cinco minutos" in b.dicho(), a, b) and "chat_fuera" in sb
        # y el mensaje normal sigue sonando como siempre
        a.tecla(pygame.K_F10)
        _escribir(a, "hola a todos")
        assert hasta(lambda: "Ana dice: hola a todos" in b.dicho(), a, b) and "chat" in sb
        # el historial, por canales, y el de siempre con todo
        assert [c for c, _ in pb.sv["historial"]] == ["ic", "yo", "ooc"] and [c for c, _ in pa.sv["historial"]] == ["ic", "yo", "ooc"]
        assert pb.chat[-4:] == ["Ana, en personaje: ¿Tienes fuego?", "Ana abre la puerta", "Ana, fuera de personaje: vuelvo en cinco minutos", "Ana: hola a todos"]
        menus_enlinea.menu(pb)
        _opcion(b.app, "Rol: hablar en personaje")
        b.tecla(pygame.K_RETURN)
        textos = [_texto(o) for o in b.app.pila[-1].opciones]
        assert textos[:3] == ["Hablar en personaje", "Describir lo que hace tu personaje", "Hablar fuera de personaje"] and textos[3] == "Tu ficha: sin escribir"
        assert all(o.ayuda for o in b.app.pila[-1].opciones[:4])
        _opcion(b.app, "Repasar lo dicho en personaje")
        b.tecla(pygame.K_RETURN)
        assert [_texto(o) for o in b.app.pila[-1].opciones][:2] == ["Ana abre la puerta", "Ana, en personaje: ¿Tienes fuego?"]      # lo último, primero
        assert not any("fuera de personaje" in _texto(o) for o in b.app.pila[-1].opciones)
        _al_juego(b)
        # lejos, lo dicho en personaje no llega, y a quien habla se le dice
        pb.teletransportar(pa.pos()[0] + 120, pa.pos()[1])
        assert hasta(lambda: rb.dist(*pa.pos()) > 100, a, b)
        n = len(pb.sv["historial"])
        pa.sv_enviar_chat("¿hay alguien?", "ic")
        assert hasta(lambda: "No hay nadie lo bastante cerca" in a.dicho(), a, b) and len(pb.sv["historial"]) == n
        pa.sv_enviar_chat("se oye en todo el servidor", "ooc")
        assert hasta(lambda: len(pb.sv["historial"]) == n + 1, a, b)
        # la ficha: se escribe en el menú de rol, y el otro la lee desde Quién hay o mirándole con Mayúsculas J
        menus_enlinea.ficha_propia(pa)
        _escribir(a, "Camarera de La Gaviota. No se fía de nadie.")
        assert hasta(lambda: pa.sv["ficha"] == "Camarera de La Gaviota. No se fía de nadie.", a, b) and "Tu ficha dice ahora" in a.dicho()
        menus_enlinea.jugador(pb, ra)
        _opcion(b.app, "Leer su ficha")
        b.tecla(pygame.K_RETURN)
        assert hasta(lambda: "Ficha de Ana: Camarera de La Gaviota. No se fía de nadie." in b.dicho(), a, b)
        _al_juego(b)
        pb.teletransportar(pa.pos()[0] + 5, pa.pos()[1])
        assert hasta(lambda: ra.dist(*pb.pos()) < 10 and rb.dist(*pa.pos()) < 10, a, b)
        b.app.voz.registro.clear()
        b.tecla(pygame.K_j, pygame.KMOD_SHIFT)
        assert hasta(lambda: "Ficha de Ana: Camarera" in b.dicho(), a, b)
        a.app.voz.registro.clear()
        a.tecla(pygame.K_j, pygame.KMOD_SHIFT)                   # Blas no ha escrito ficha: al mirarle no se dice nada de fichas
        ambos(a, b, 12)
        time.sleep(0.2)
        ambos(a, b, 6)
        assert "Blas" in a.dicho() and "ficha" not in a.dicho().lower()
        # se vuelve a entrar con la ficha puesta
        pa.sv_salir(al_menu=True)
        time.sleep(0.4)
        pa = entrar(a, b_, "Ana")
        assert pa.sv["ficha"].startswith("Camarera")
        # quien lleva el servidor apaga los canales: quien ya estaba dentro se entera al usarlos, y quien entra, antes
        b_.hacer(lambda: b_.srv.aplicar_config({"rol": "no"}))
        a.app.voz.registro.clear()
        pa.sv_enviar_chat("se va", "yo")
        assert hasta(lambda: "canales de rol están apagados" in a.dicho(), a, b)
        pa.sv_salir(al_menu=True)
        time.sleep(0.4)
        pa = entrar(a, b_, "Ana")
        assert not pa.sv_rol() and "apagados" in pa.sv_rol_motivo()
        enviados = _espiar(pa)
        a.app.voz.registro.clear()
        a.tecla(pygame.K_F10, pygame.KMOD_SHIFT)
        assert a.app.pila[-1] is pa and "apagados" in a.dicho()
        a.tecla(pygame.K_F10)
        _escribir(a, "/yo saluda")
        assert "chat" not in enviados and "ficha" not in enviados
        menus_enlinea.menu(pa)
        assert any(_texto(o) == "Rol: este servidor no tiene canales de rol" for o in a.app.pila[-1].opciones)
        _al_juego(a)
    finally:
        _salir_todos(dos, b_)


def test_la_radio_del_vehiculo_de_otro_jugador(dos, banco):
    from juego import config
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=8.0)
    assert config.POR_DEFECTO["radio_coches"] is True and pb.cfg["radio_coches"] is True
    x, y = pa.pos()
    v = pa.crear_vehiculo("sedan", x, y, 0, "aparcado")
    v.cerrado = False
    pa._subir(v, True)
    emisora = {"id": "bravo", "suena": True}
    ra_app, rb_app = a.app.radio, b.app.radio
    ra_app.comunes = lambda: {"bravo", "neon", "hierro"}
    ra_app.id_actual = lambda: emisora["id"]
    ra_app.sonando_ahora = lambda: emisora["suena"]
    pedidas = []
    suena_la_mia = {"si": False}
    rb_app.comunes = lambda: {"bravo", "neon"}
    rb_app.sonando_ahora = lambda: suena_la_mia["si"]
    rb_app.muestra = lambda ident, segundos=40.0: (pedidas.append(ident), np.full(44100, 0.1, dtype=np.float32))[1]
    assert pa.sv_emisora() == "bravo"
    suena = lambda: (pb.sv["radio_ajena"] or {}).get("canal") is not None
    # Blas, a pie y al lado: le llega qué emisora lleva Ana y la oye desde su vehículo
    assert hasta(lambda: getattr(ra, "radio", "") == "bravo" and suena(), a, b), (getattr(ra, "radio", None), pb.sv["radio_ajena"])
    canal = pb.sv["radio_ajena"]["canal"]
    assert pedidas == ["bravo"] and canal.nombre == enlinea.SON_RADIO_AJENA and canal.bucle and canal.xy is not None and canal.cat == "musica"
    assert abs(canal.xy[0] - ra.x) < 3 and canal.maxd == enlinea.RADIO_AJENA_M and canal.vol < 0.6
    assert "radio del vehículo de Ana" in b.dicho() and "Opciones" in b.dicho()
    assert banco.srv.jugadores[pa.red.id].radio == "bravo"
    # se aleja: se deja de oír. Vuelve: otra vez, y sin volver a leerla del disco ni repetir la explicación
    pb.teletransportar(x + 150, y)
    assert hasta(lambda: pb.sv["radio_ajena"] is None, a, b)
    b.app.voz.registro.clear()
    pb.teletransportar(x + 8, y)
    assert hasta(suena, a, b) and pedidas == ["bravo"] and "radio del vehículo" not in b.dicho()
    # Ana cambia de emisora: Blas pasa a oír la otra
    emisora["id"] = "neon"
    assert hasta(lambda: (pb.sv["radio_ajena"] or {}).get("emisora") == "neon" and suena(), a, b) and pedidas == ["bravo", "neon"]
    # una emisora que Blas no tiene lista en su juego: no suena nada
    emisora["id"] = "hierro"
    assert hasta(lambda: getattr(ra, "radio", "") == "hierro" and pb.sv["radio_ajena"] is None, a, b)
    # «Mi música» y las emisoras hechas con archivos propios no salen del ordenador de Ana: ni el nombre
    for propia in ("usuario", "extra_mi_cancion", "noticias", "apagada"):
        emisora["id"] = propia
        assert pa.sv_emisora() == "" and "ra" not in pa.sv_estado()
    assert hasta(lambda: getattr(ra, "radio", "x") == "" and banco.srv.jugadores[pa.red.id].radio == "", a, b)
    # con la radio de Ana apagada, tampoco
    emisora["id"], emisora["suena"] = "bravo", False
    assert pa.sv_emisora() == ""
    emisora["suena"] = True
    assert hasta(suena, a, b)
    # si Blas lleva su propia radio puesta, la de Ana no se le echa encima
    suena_la_mia["si"] = True
    assert hasta(lambda: pb.sv["radio_ajena"] is None, a, b)
    suena_la_mia["si"] = False
    assert hasta(suena, a, b)
    # la opción: con no, no se oye la radio de nadie
    pb.cfg["radio_coches"] = False
    assert hasta(lambda: pb.sv["radio_ajena"] is None, a, b)
    ambos(a, b, 20)
    assert pb.sv["radio_ajena"] is None
    pb.cfg["radio_coches"] = True
    assert hasta(suena, a, b)
    # en un servidor anterior, o en uno que lo tenga apagado, el juego no dice qué emisora lleva
    pa.sv["funciones"] = list(FUNCIONES_170)
    assert pa.sv_emisora() == "" and "ra" not in pa.sv_estado()
    pa.sv["funciones"] = list(nucleo.FUNCIONES)
    pa.sv["info"]["radio_coches"] = False
    assert pa.sv_emisora() == ""
    # al salir del servidor, la radio ajena calla
    pb.sv_salir()
    assert pb.sv["radio_ajena"] is None


def test_el_trozo_de_emisora_que_se_oye_desde_fuera(app, tmp_path):
    from juego import sintesis
    rng = np.random.default_rng(3)
    fijas = [e["id"] for e in musica.EMISORAS if "estilo" in e]
    for ident in fijas:                                          # una canción corta para cada emisora de serie: así no se compone ninguna
        sintesis.escribir_wav(str(tmp_path / (ident + ".wav")), (rng.standard_normal((44100 * 6, 2)) * 0.2).astype(np.float32))
    sintesis.escribir_wav(str(tmp_path / "mi_cancion.wav"), (rng.standard_normal((44100 * 3, 2)) * 0.2).astype(np.float32))
    radio = musica.Radio(app.mez, str(tmp_path))
    try:
        radio.esperar()
        assert radio.comunes() == set(fijas)                     # ni «Mi música», ni las noticias, ni la emisora hecha con un archivo propio
        assert any(e["id"] == "extra_mi_cancion" for e in radio.emisoras)
        d = radio.muestra("bravo", segundos=4.0)
        assert d is not None and d.ndim == 1 and d.dtype == np.float32 and 44100 * 3 <= len(d) <= 44100 * 4 + 10
        assert abs(float(d[0])) < 0.01 and abs(float(d[-1])) < 0.01 and float(np.abs(d).max()) <= 1.0        # entra y sale fundido, para repetirse
        claro = sintesis.leer_audio(str(tmp_path / "bravo.wav"), mono=True, maximo=4.0)
        agudos = lambda s: float(np.abs(np.fft.rfft(s))[len(s) // 4:].sum() / max(1e-9, np.abs(np.fft.rfft(s)).sum()))
        assert agudos(d) < agudos(claro) * 0.5                    # apagado, como se oye una radio desde fuera
        for propia in ("usuario", "extra_mi_cancion", "noticias", "apagada", "no_existe"):
            assert radio.muestra(propia) is None, propia
    finally:
        radio.cancelar()


def test_el_copiloto_en_el_juego_va_dentro_y_nadie_le_atropella(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=5.0)
    x, y = pa.pos()
    v = pa.crear_vehiculo("sedan", x, y, 0, "aparcado")
    v.cerrado = False
    pa._subir(v, True)
    assert hasta(lambda: ra.veh == "sedan" and ra.dist(*pb.pos()) < 8, a, b)
    assert pb.subir_con_amigo() and pb.pasajero == pa.red.id
    js = banco.srv.jugadores
    assert hasta(lambda: js[pb.red.id].pasajero_de == pa.red.id and rb.id in pa.sv["pasajeros"] and getattr(rb, "pasajero_de", None) == pa.red.id, a, b)
    assert pb.sv_estado()["pj"] == pa.red.id
    # Ana conduce, con Blas dentro: el juego de Ana no avisa de ningún atropello, y a Blas no le pasa nada
    enviados = _espiar(pa)
    salud = pb.j.salud
    for _ in range(40):
        v.vel = 12.0
        ambos(a, b, 2)
        time.sleep(0.02)
    assert "estado" in enviados and "atropello" not in enviados and pb.j.salud == salud and "Atropellas" not in a.dicho() and "atropellado" not in b.dicho()
    assert rb.dist(*pa.pos()) < 25                               # y va con ella
    # tampoco le atropella el tráfico del servidor mientras va dentro
    coche = pb.crear_vehiculo("sedan", pb.j.x + 1, pb.j.y, 0, "servidor")
    coche.vel, coche.t_choque = 9.0, 0.0
    pb.sv_trafico_paso(coche, 1.0, 0.03)
    assert pb.j.salud == salud and "atropellado" not in b.dicho()
    pb.quitar_vehiculo(coche)
    # con un servidor anterior tampoco: el juego de Ana lo sabe por el aviso de subir, que ya existía
    for r_ in pa.remotos.values():
        r_.pasajero_de = None
    v.vel = 12.0
    pa.sv["t_atropello"] = 0.0
    del enviados[:]
    pa.sv_paso(0.03)
    assert "atropello" not in enviados
    # se baja: vuelve a ser un peatón, para el servidor y para el juego de Ana
    v.vel = 0.0
    pb.bajar_de_amigo()
    assert hasta(lambda: js[pb.red.id].pasajero_de is None and rb.id not in pa.sv["pasajeros"] and getattr(rb, "pasajero_de", 1) is None, a, b)
    assert "pj" not in pb.sv_estado()
    pb.teletransportar(v.x + 1.0, v.y)
    assert hasta(lambda: rb.dist(v.x, v.y) < 3.0, a, b)
    v.vel = 12.0
    pa.sv["t_atropello"] = 0.0
    del enviados[:]
    pa.sv_paso(0.03)
    assert "atropello" in enviados


def test_mis_vehiculos_conectado_renombrar_traer_y_mandar_al_garaje_desde_la_lista(dos, banco):
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=8.0)
    x, y = pa.pos()
    v = pa.crear_vehiculo("sedan", x, y, 0, "aparcado")
    v.cerrado = False
    v.mejoras = {"motor": 2, "suspension": 1}                    # una mejora de siempre y otra de las nuevas de la 1.7.1
    pa._subir(v, True)
    assert hasta(lambda: getattr(v, "id_red", None) is not None, a, b)
    vid = v.id_red
    pa.salir_vehiculo()
    assert hasta(lambda: vid in banco.srv.vehiculos and banco.srv.vehiculos[vid]["por"] is None and any(getattr(q, "id_red", None) == vid for q in pb.vehiculos), a, b)
    assert banco.srv.vehiculos[vid]["mejoras"] == {"motor": 2, "suspension": 1}
    copia_b = next(q for q in pb.vehiculos if getattr(q, "id_red", None) == vid)
    assert dict(copia_b.mejoras) == {"motor": 2, "suspension": 1}
    assert not pa.hacer_mio(v)                                   # en un servidor, los de la calle los lleva el servidor
    pa.teletransportar(x + 220, y + 10)
    pa.j.dinero = 1000
    precio_traer, precio_garaje = pa.precio("traer_vehiculo", 150), pa.precio("mandar_vehiculo", 100)

    def abrir_ficha():
        _al_juego(a)
        misvehiculos.menu_mis_vehiculos(pa)
        m = a.app.pila[-1]
        m.refrescar(False)
        m.i = next(k for k, o in enumerate(m.opciones) if "En la calle" in _texto(o))
        a.tecla(pygame.K_RETURN)
        return [_texto(o) for o in a.app.pila[-1].opciones]
    textos = abrir_ficha()
    assert any(t.startswith("Pedir que te lo traigan") for t in textos) and any(t.startswith("Mandarlo a un garaje") for t in textos) and "Cambiarle el nombre" in textos
    # el nombre: lo guarda el servidor y lo ve también Blas
    _opcion(a.app, "Cambiarle el nombre")
    a.tecla(pygame.K_RETURN)
    _escribir(a, "La Bala")
    assert hasta(lambda: banco.srv.vehiculos[vid]["nombre"] == "La Bala" and v.nombre == "La Bala" and copia_b.nombre == "La Bala", a, b)
    assert "Ahora se llama La Bala" in a.dicho()
    # que se lo traigan: aparece a su lado en los dos juegos, y paga al mecánico
    abrir_ficha()
    _opcion(a.app, "Pedir que te lo traigan")
    a.tecla(pygame.K_RETURN)
    assert hasta(lambda: v.dist(*pa.pos()) < 60 and pa.j.dinero == 1000 - precio_traer, a, b), (v.dist(*pa.pos()), pa.j.dinero)
    assert "Tu mecánico te deja La Bala" in a.dicho() and a.app.pila[-1] is pa
    assert hasta(lambda: any(getattr(q, "id_red", None) == vid and not q.muerto and abs(q.x - v.x) < 2 for q in pb.vehiculos), a, b)
    assert vid in pa.sv["mios"] and abs(banco.srv.vehiculos[vid]["x"] - v.x) < 1
    # al garaje, desde la lista: sale de la calle del servidor y queda guardado con el personaje, con su nombre y sus mejoras
    casa = next(l for l in pa.lugares.values() if l.tipo == "casa" and int(l.get("garaje", 0)) > 0)
    pa.j.propiedades.append(casa.id)
    abrir_ficha()
    _opcion(a.app, "Mandarlo a un garaje")
    a.tecla(pygame.K_RETURN)
    assert str(precio_garaje) in a.app.pila[-1].titulo
    a.app.pila[-1].i = 0
    a.tecla(pygame.K_RETURN)
    assert hasta(lambda: vid not in banco.srv.vehiculos and pa.j.garajes.get(casa.id), a, b)
    ficha = pa.j.garajes[casa.id][-1]
    assert ficha["nombre"] == "La Bala" and ficha["modelo"] == "sedan" and ficha["mejoras"] == {"motor": 2, "suspension": 1}
    assert pa.j.dinero == 1000 - precio_traer - precio_garaje and v.muerto and vid not in pa.sv["mios"] and "al garaje de" in a.dicho()
    assert hasta(lambda: not any(getattr(q, "id_red", None) == vid and not q.muerto for q in pb.vehiculos), a, b)
    assert hasta(lambda: "La Bala" in (banco.hacer(lambda: banco.srv.alm.cuenta(pa.sv["cuenta"])["partida"]) or ""), a, b)      # y el personaje se guarda al momento
    # si otro se lo ha llevado, el servidor dice que no y no se cobra nada
    v2 = pa.crear_vehiculo("sedan", pa.j.x + 3, pa.j.y, 0, "aparcado")
    v2.cerrado = False
    pa._subir(v2, True)
    assert hasta(lambda: getattr(v2, "id_red", None) is not None, a, b)
    pa.salir_vehiculo()
    assert hasta(lambda: v2.id_red in banco.srv.vehiculos and banco.srv.vehiculos[v2.id_red]["por"] is None, a, b)
    banco.hacer(lambda: banco.srv.vehiculos[v2.id_red].__setitem__("dueno", 99999))
    dinero = pa.j.dinero
    a.app.voz.registro.clear()
    assert pa.sv_veh_orden("traer", {"id": v2.id_red}, x=pa.j.x, y=pa.j.y)
    pa.sv["veh_pend"][v2.id_red] = {"precio": precio_traer}
    assert hasta(lambda: "ya no está aparcado a tu nombre" in a.dicho(), a, b) and pa.j.dinero == dinero and v2.id_red not in pa.sv["mios"]
    # con un servidor anterior, las tres cosas se ofrecen igual, pero el juego dice con claridad que allí no se puede
    banco.hacer(lambda: banco.srv.vehiculos[v2.id_red].__setitem__("dueno", pa.sv["cuenta"]))
    pa.sv["mios"].add(v2.id_red)
    pa.sv["vehs"][v2.id_red] = dict(banco.srv.vehiculos[v2.id_red])
    pa.sv["funciones"] = list(FUNCIONES_170)
    enviados = _espiar(pa)
    pa.teletransportar(pa.j.x + 150, pa.j.y)
    for empieza in ("Pedir que te lo traigan", "Cambiarle el nombre"):
        abrir_ficha()
        m = _opcion(a.app, empieza)
        assert "versión anterior" in m.opciones[m.i].ayuda
        a.app.voz.registro.clear()
        a.tecla(pygame.K_RETURN)
        if empieza == "Cambiarle el nombre":
            _escribir(a, "Otra")
        assert "versión anterior" in a.dicho() and "Ve hasta él" in a.dicho()
    assert not [t for t in enviados if t.startswith("veh_")] and pa.j.dinero == dinero


def test_un_juego_nuevo_en_un_servidor_como_el_de_la_1_7_0(dos, tmp_path, monkeypatch):
    """Un servidor que no conoce nada de lo nuevo: ni lo anuncia, ni atiende los mensajes nuevos, ni manda las claves nuevas.
    Se simula quitándole al de ahora lo que no tenía el de la 1.7.0."""
    S = nucleo.Servidor
    monkeypatch.setattr(nucleo, "FUNCIONES", FUNCIONES_170)
    for nombre in ("_m_ficha", "_m_economia", "_m_veh_nombre", "_m_veh_traer", "_m_veh_guardar"):
        monkeypatch.delattr(S, nombre)
    enviar, estado, mision_ok = S._enviar, S._m_estado, S._m_mision_ok
    recibidos = []

    def enviar_170(self, j, obj, hecho=None):
        if obj.get("t") == "ok":
            obj = {k: v for k, v in obj.items() if k not in ("ficha", "mis_vehiculos")}
            obj["servidor"] = {k: v for k, v in obj["servidor"].items() if k not in ("rol", "rol_metros", "radio_coches", "economia")}
        elif obj.get("t") == "saldo":
            obj = {"t": "saldo", "quita": obj["quita"], "saldo": obj["saldo"]}
        return enviar(self, j, obj, hecho)

    def estado_170(self, j, m):
        e = m.get("e")
        if isinstance(e, dict):
            recibidos.append(set(e))
            m = dict(m, e={k: v for k, v in e.items() if k not in ("pj", "ra")})
        return estado(self, j, m)

    def mision_ok_170(self, j, m):
        recibidos.append(("mision_ok", m.get("id"), m.get("encargo")))
        return mision_ok(self, j, {"t": "mision_ok", "id": m.get("id")}) if m.get("id") in self.mundo["misiones"] else None

    def chat_170(self, j, m):                                    # el chat tal como era: lo que no conoce va a todos
        texto = str(m.get("texto", "")).strip()[:300]
        if not texto:
            return
        if texto.startswith("/") and j.admin:
            return self._aviso(j, self.orden(texto[1:], j.nombre))
        canal = m.get("canal") if m.get("canal") in ("todos", "cerca", "banda", "priv", "grupo") else "todos"
        obj = {"t": "chat", "de": j.id, "nombre": j.nombre, "texto": texto, "canal": canal}
        if canal == "cerca":
            for o in self.jugadores.values():
                if o.dentro and o is not j and o.mapa == j.mapa and j.dist(o) <= 80:
                    self._enviar(o, obj)
        elif canal == "priv":
            o = self.jugadores.get(m.get("a"))
            if o is not None and o.dentro:
                self._enviar(o, obj)
        else:
            self._a_todos(obj, menos=j)
    monkeypatch.setattr(S, "_enviar", enviar_170)
    monkeypatch.setattr(S, "_m_estado", estado_170)
    monkeypatch.setattr(S, "_m_mision_ok", mision_ok_170)
    monkeypatch.setattr(S, "_m_chat", chat_170)
    monkeypatch.setattr(S, "_va_con", lambda self, o: None)      # ni sabía de pasajeros
    b_ = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000)
    try:
        a, b = dos
        pb = entrar(b, b_, "Blas")                               # el primero administra: que sea Blas, y Ana una jugadora cualquiera
        pa = entrar(a, b_, "Ana")
        rb, ra = juntos(pa, pb, a, b, d=6.0)
        # entra y juega como siempre; lo nuevo no está, y el juego lo sabe
        assert pa.sv["funciones"] == list(FUNCIONES_170) and "Estás en" in a.dicho()
        assert not pa.sv_rol() and "versión anterior" in pa.sv_rol_motivo() and not pa.sv_sabe("mis_vehiculos") and pa.sv["economia"] is None and pa.sv["ficha"] == ""
        # el chat de siempre va; los canales de rol se dicen que no están, sin mandar nada raro
        a.tecla(pygame.K_F10)
        _escribir(a, "hola, Blas")
        assert hasta(lambda: "Ana dice: hola, Blas" in b.dicho(), a, b)
        a.app.voz.registro.clear()
        a.tecla(pygame.K_F10, pygame.KMOD_CTRL)
        assert a.app.pila[-1] is pa and "versión anterior" in a.dicho()
        n = len(pb.chat)
        a.tecla(pygame.K_F10)
        _escribir(a, "/yo abre la puerta")
        assert not pa.sv_poner_ficha("Hola") and not pa.sv_pedir_ficha(rb)
        a.app.voz.registro.clear()
        a.tecla(pygame.K_j, pygame.KMOD_SHIFT)                   # mirar a otro jugador sigue diciendo cómo va, sin pedir fichas
        ambos(a, b, 10)
        time.sleep(0.2)
        ambos(a, b, 6)
        assert len(pb.chat) == n and "Blas" in a.dicho()
        menus_enlinea.menu(pa)
        assert any(_texto(o) == "Rol: este servidor no tiene canales de rol" for o in a.app.pila[-1].opciones)
        _opcion(a.app, "Datos y reglas de este servidor")
        a.tecla(pygame.K_RETURN)
        textos = [_texto(o) for o in a.app.pila[-1].opciones]
        assert "Canales de rol: no" in textos and "Radio de los vehículos de otros jugadores: no" in textos and any("su versión no dice cuál" in t for t in textos)
        _al_juego(a)
        # el dinero: el aviso de siempre, porque ese servidor no manda cifras
        pa.j.dinero += 900000
        assert hasta(lambda: "no reconoce" in a.dicho() and "un tanto por hora" in a.dicho(), a, b)
        # un encargo repetible: se le dice como siempre, con dos datos de más que ese servidor no mira
        pa.sv_mision_ok({"id": "contrato", "repetible": True, "recompensa": {"dinero": 1900}})
        assert hasta(lambda: ("mision_ok", "contrato", 1) in recibidos, a, b)
        # el copiloto: el juego de quien conduce no avisa de atropello, aunque el servidor no sepa de pasajeros
        x, y = pa.pos()
        v = pa.crear_vehiculo("sedan", x, y, 0, "aparcado")
        v.cerrado = False
        pa._subir(v, True)
        assert hasta(lambda: ra.veh == "sedan" and ra.dist(*pb.pos()) < 8, a, b)
        a.app.radio.comunes, a.app.radio.id_actual, a.app.radio.sonando_ahora = (lambda: {"bravo"}), (lambda: "bravo"), (lambda: True)
        assert pb.subir_con_amigo()
        assert hasta(lambda: rb.id in pa.sv["pasajeros"], a, b)
        enviados = _espiar(pa)
        salud = pb.j.salud
        for _ in range(25):
            v.vel = 12.0
            ambos(a, b, 2)
            time.sleep(0.02)
        assert "atropello" not in enviados and pb.j.salud == salud
        assert any("pj" in e for e in recibidos if isinstance(e, set))      # lo dice, y a ese servidor le da igual
        assert not any("ra" in e for e in recibidos if isinstance(e, set))  # la emisora ni se manda: ese servidor no la reparte
        assert getattr(rb, "pasajero_de", None) is None and getattr(ra, "radio", "") == ""
        v.vel = 0.0
        pb.bajar_de_amigo()
        pa.salir_vehiculo()
        # lo comprado se guarda enseguida también allí: el guardado es el mensaje de siempre
        ambos(a, b, 5)
        del enviados[:]
        pa.j.dinero -= 50
        assert hasta(lambda: "guardar" in enviados, a, b, 6)
        # y el personaje vuelve entero
        pa.j.cocina_practica = 40.0
        pa.sv_salir(al_menu=True)
        time.sleep(0.4)
        pa = entrar(a, b_, "Ana")
        assert pa.j.cocina_practica == 40.0
    finally:
        _salir_todos(dos, b_)


def test_lo_nuevo_de_la_1_7_1_jugando_conectado_a_un_servidor(dos, tmp_path):
    """Armas, mejoras y vehículos nuevos, la calle, los atracos, los contratos, el domicilio y la despensa, con el juego
    conectado a un servidor de verdad que lleva la cuenta del dinero. Lo que allí no existe, se dice."""
    from juego import gente as G
    from juego.entidades import Persona
    b_ = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000, encargos_hora=3)
    try:
        a, b = dos
        pa, pb = entrar(a, b_, "Ana"), entrar(b, b_, "Blas")
        rb, ra = juntos(pa, pb, a, b, d=8.0)
        srv = b_.srv
        ja = srv.jugadores[pa.red.id]
        # ---- tanda 2: el servidor conoce todas las armas y todos los vehículos de esta versión, también los nuevos
        assert set(pa.armas_d) <= set(srv.mundo["armas"]) and set(pa.modelos) <= set(srv.mundo["modelos"])
        assert {"uzi", "carabina", "ballesta", "minigun", "hacha", "pistola_rafagas", "escopeta_corredera", "rifle_palanca", "fusil_semi", "lanzagranadas"} <= set(srv.mundo["armas"])
        assert "furgon_asalto" in srv.mundo["modelos"] and srv.mundo["huella"] == a.app._huella_datos and pa.sv["mundo"]["igual"]
        # con un arma nueva en la mano, el servidor la reconoce (no «cuenta como ir con las manos») y decide el disparo
        pa.dar_arma("fusil_semi", 60)
        pa.j.arma = "fusil_semi"
        assert hasta(lambda: ja.arma == "fusil_semi", a, b) and "no existe en la versión" not in a.dicho()
        salud = pb.j.salud
        b_.hacer(lambda: srv.rng.seed(5))
        pa.fijar(True, callar=True)
        for _ in range(30):
            pa.j.t_ataque = 0
            pa.j.armas["fusil_semi"]["cargador"] = 5
            pa.atacar()
            ambos(a, b, 2)
            time.sleep(0.3)
            if pb.j.salud < salud:
                break
        assert pb.j.salud < salud and "Ana te ataca" in b.dicho()
        pb.j.salud = 100.0
        pa.limpiar_busqueda(False)
        # ---- tanda 4: lo que es solo de un jugador no está en un servidor
        assert not pa.guerra_activa() and not pa.sv_policia_comun() and pa.patrullas_activas() == (bool(pa.cfg["patrullas_calle"]) and bool(pa.mundo.policia))
        # ---- tanda 5: lo que no existe en un servidor, se dice
        pa.cfg["adultos"] = True
        prov = type("Lugar", (), {"id": "prov_x", "tipo": "proveedor", "nombre": "La trastienda"})()
        q = Persona("civil", pa.j.x + 2, pa.j.y, "Paco")
        pa.personas.append(q)
        assert "servidor" in pa.asalto_motivo(prov) and "servidor" in pa.pactos_motivo() and "servidor" in pa.recluta_motivo(q)[1]
        assert not pa.policia_activa() and not pa.convivencia_activa()
        pa.cfg["adultos"] = False
        favores = pa.j.stats.get("favores", 0)
        dicho = pa.pedir_favor(q)                                 # pedir un favor a alguien de la calle va como en solitario
        assert isinstance(dicho, str) and dicho and pa.j.stats.get("favores", 0) in (favores, favores + 1)
        pa.personas.remove(q)
        # ---- los contratos del tablón: se juegan igual (los enemigos, a pie) y su paga no gasta la ganancia por hora
        sin_margen = lambda: b_.hacer(lambda: (setattr(ja, "margen", 0.0), setattr(ja, "t_margen", time.monotonic()), setattr(ja, "t_saldo", 0.0)))
        pa.dar_arma("pistola", 60)
        pa.j.arma = "pistola"
        taberna = next(l for l in pa.mundo.lugares.values() if l.tipo == "taberna")
        pa.teletransportar(taberna.x, taberna.y)
        ofertas = pa.ofertas_contrato(taberna)
        assert ofertas
        o = ofertas[0]
        assert pa.empezar_contrato_de(taberna, o) and pa.mision and pa.mision["def"]["id"] == "contrato" and pa.mision["def"]["repetible"]
        assert not pa.mision.get("veh_enemigos")                 # en un servidor, nadie llega en vehículo
        ambos(a, b, 6)
        time.sleep(0.2)
        ambos(a, b, 4)
        sin_margen()
        dinero = pa.j.dinero
        a.app.voz.registro.clear()
        pa._completar_mision()
        a.saltar_dialogos()
        assert pa.j.dinero == dinero + int(o["paga"])
        assert hasta(lambda: len(srv.encargos.get(pa.sv["cuenta"], {}).get("contrato", [])) == 1 and ja.saldo == pa.j.dinero + pa.j.banco, a, b)
        ambos(a, b, 10)
        time.sleep(0.3)
        ambos(a, b, 6)
        assert pa.j.dinero == dinero + int(o["paga"]) and "retira" not in a.dicho() and "no reconoce" not in a.dicho()
        # lo que pasa del tope, en cambio, se retira diciendo las cifras
        sin_margen()
        a.app.voz.registro.clear()
        pa.j.dinero += 5000
        assert hasta(lambda: "el servidor acepta 0 y retira 5000" in a.dicho(), a, b), a.dicho()[-400:]
        assert "hasta 3600 euros por hora" in a.dicho() and "se te guarda hasta 10800" in a.dicho() and "recuperas 60 euros de margen cada minuto" in a.dicho()
        assert "hasta 3 por hora de cada tipo" in a.dicho() and pa.j.dinero == dinero + int(o["paga"])
        menus_enlinea.menu(pa)
        _opcion(a.app, "Datos y reglas de este servidor")
        a.tecla(pygame.K_RETURN)
        assert hasta(lambda: any(_texto(o_).startswith("Ganancia por tu cuenta: hasta 3600 euros por hora, que se acumulan hasta 10800") for o_ in a.app.pila[-1].opciones), a, b)
        _al_juego(a)
        # ---- atracar un local sin guardia: el botín es un cobro de los que se repiten, y el servidor lo reconoce
        pa.j.arma = "pistola"
        tienda = next(l for l in pa.mundo.lugares.values() if pa.local_atracable(l) and not (G.caja_local(l.tipo) or {}).get("guardias"))
        pa.teletransportar(tienda.x, tienda.y)
        ambos(a, b, 4)
        sin_margen()
        dinero = pa.j.dinero
        a.app.voz.registro.clear()
        assert pa.atracar_local(tienda) and pa.j.dinero > dinero
        botin = pa.j.dinero - dinero
        assert hasta(lambda: len(srv.encargos[pa.sv["cuenta"]].get("atraco_local", [])) == 1 and ja.saldo == pa.j.dinero + pa.j.banco, a, b)
        ambos(a, b, 10)
        time.sleep(0.2)
        ambos(a, b, 4)
        assert pa.j.dinero == dinero + botin and "retira" not in a.dicho()
        pa.limpiar_busqueda(False)
        # ---- comida a domicilio, en tu casa: se paga y el repartidor queda en camino
        casa = next(l for l in pa.mundo.lugares.values() if l.tipo == "casa")
        if casa.id not in pa.j.propiedades:
            pa.j.propiedades.append(casa.id)
        pa.teletransportar(casa.x, casa.y)
        carta = pa.datos.get("carta_domicilio") or []
        assert carta and pa.domicilio_motivo() == ""
        dinero = pa.j.dinero
        assert pa.pedir_domicilio(carta[:1]) and pa.j.pedido and pa.j.dinero < dinero
        # ---- tanda 6: la despensa, lo que llevas encima y la práctica de cocina se guardan con el personaje y vuelven
        pa.j.encima = [{"id": "zumo", "n": 2, "dia": pa.dia + 5}]
        pa.j.despensa = {casa.id: [{"id": "huevos", "n": 6, "dia": pa.dia + 9}]}
        pa.j.cocina_practica = 35.0
        pedido, encima, despensa = dict(pa.j.pedido), list(pa.j.encima), dict(pa.j.despensa)
        assert pa.sv_guardar(ya=True)
        partida = lambda: b_.hacer(lambda: srv.alm.cuenta(pa.sv["cuenta"])["partida"]) or ""
        assert hasta(lambda: '"cocina_practica":35.0' in partida(), a, b)
        guardado = json.loads(partida())
        assert guardado["jugador"]["despensa"] == despensa and guardado["jugador"]["encima"] == encima and "mis_vehiculos" not in guardado
        pa.sv_salir(al_menu=True)
        time.sleep(0.4)
        pa = entrar(a, b_, "Ana")
        assert pa.j.despensa == despensa and pa.j.encima == encima and pa.j.cocina_practica == 35.0 and pa.j.pedido["casa"] == pedido["casa"]
        assert "fusil_semi" in pa.j.armas
    finally:
        _salir_todos(dos, b_)


def test_lo_comprado_se_guarda_a_los_pocos_segundos_y_un_corte_no_lo_pierde(dos, tmp_path):
    b_ = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000)
    try:
        a, b = dos
        pa = entrar(a, b_, "Ana")
        pa.j.dinero, pa.j.banco = 1000, 0
        a.frames(6)
        pa.sv_guardar(ya=True)
        srv = b_.srv
        ja = srv.jugadores[pa.red.id]
        assert hasta(lambda: ja.total_guardado == 1000 and ja.saldo == 1000, a, a)
        enviados = _espiar(pa)
        # compra algo: el personaje se guarda solo a los dos o tres segundos, no al cabo de tres cuartos de minuto
        assert pa.sv["t_guardar"] > 30
        assert pa.pagar(400)
        pa.j.objetos["botiquin"] = pa.j.objetos.get("botiquin", 0) + 4
        _pasar(a, 30)                                             # un segundo
        assert "guardar" not in enviados                         # todavía no: espera un momento por si compra más cosas
        _pasar(a, 70)
        assert enviados.count("guardar") == 1
        assert hasta(lambda: ja.total_guardado == 600 and ja.gasto_pend == 0, a, a, 6)
        guardado = json.loads(b_.hacer(lambda: srv.alm.cuenta(pa.sv["cuenta"])["partida"]))["jugador"]
        assert guardado["dinero"] == 600 and guardado["objetos"]["botiquin"] >= 4
        # si sigue gastando, no manda el personaje entero a cada compra: una vez cada doce segundos como mucho
        del enviados[:]
        assert pa.pagar(10)
        _pasar(a, 150)
        assert "guardar" not in enviados
        _pasar(a, 240)
        assert enviados.count("guardar") == 1
        # ganar dinero no fuerza un guardado: sigue el de siempre
        del enviados[:]
        pa.j.dinero += 50
        _pasar(a, 150)
        assert "guardar" not in enviados
        # y si la conexión se corta nada más comprar, antes incluso de ese guardado, el servidor devuelve lo gastado:
        # el personaje guardado no tiene la compra, pero tampoco ha perdido el dinero
        pa.sv_guardar(ya=True)
        assert hasta(lambda: ja.total_guardado == 640, a, a), (ja.total_guardado, pa.j.dinero, pa.j.banco, ja.saldo, a.dicho()[-300:])
        assert pa.pagar(300)
        assert hasta(lambda: ja.gasto_pend == 300, a, a, 2)
        pa.red.sock.close()                                      # el cable, de un tirón
        assert hasta_que(lambda: b_.hacer(lambda: srv.alm.cuenta(pa.sv["cuenta"])["saldo"]) == 640)
        a.frames(5)
        if a.app.partida is not None:
            a.app.partida.sv_salir(al_menu=True)
        pa = entrar(a, b_, "Ana")
        assert pa.j.dinero + pa.j.banco == 640 and "no reconoce" not in a.dicho()
    finally:
        _salir_todos(dos, b_)


def test_las_misiones_en_grupo_llevan_la_marca_de_deportivo_y_la_punteria(dos, banco):
    from juego.entidades import Persona
    a, b = dos
    pa, pb = entrar(a, banco, "Ana"), entrar(b, banco, "Blas")
    rb, ra = juntos(pa, pb, a, b, d=6.0)
    pa.red.enviar({"t": "grupo_invitar", "a": rb.id})
    assert hasta(lambda: pb.sv["inv_grupo"] is not None, a, b)
    pb.red.enviar({"t": "grupo_resp", "si": True})
    assert hasta(lambda: pa.sv_lidero() and pb.sv["grupo"] == pa.red.id, a, b)
    # un combate del gimnasio de Ana: su rival es «deportivo», y eso le llega a Blas
    x, y = pa.pos()
    rival = Persona("enemigo", x + 3, y, "El Martillo")
    rival.salud, rival.arma, rival.deportivo, rival.inofensivo, rival.punteria, rival.tono = 70.0, "punos", True, False, 0.77, 0.85
    maton = Persona("enemigo", x + 4, y, "Matón")
    maton.salud, maton.arma, maton.deportivo, maton.inofensivo = 60.0, "pistola", False, False
    pa.mision = {"def": {"id": "boxeo", "titulo": "Combate", "pasos": [{"tipo": "eliminar"}]}, "paso": 0, "enemigos": [rival, maton]}
    try:
        pa.sv_mision_enemigos()
        pa.mision = None                                         # solo hacía falta para contarlo: no es una misión de verdad
        assert hasta(lambda: len(pb.sv["ecos"]) == 2, a, b)
        eco, otro = pb.sv["ecos"][0], pb.sv["ecos"][1]
        assert eco.deportivo is True and eco.nombre == "El Martillo" and abs(eco.punteria - 0.77) < 0.01 and abs(eco.tono - 0.85) < 0.01
        assert otro.deportivo is False and not otro.inofensivo
        # tumbarlo ayudando no le cuenta a Blas como delito, aunque haya un testigo
        pb.j.puntos_busqueda, pb.j.estrellas = 0.0, 0
        pb.personas.append(Persona("civil", pb.j.x + 5, pb.j.y, "Testigo"))
        pb.danar_persona(eco, 500)
        assert eco.muerto and pb.j.puntos_busqueda == 0.0 and pb.j.estrellas == 0
        # un juego de la 1.7.0 no manda la marca: el eco se crea igual, como hasta ahora
        pb._sv_quitar_ecos()
        pb._svm_grupo_msg({"de": pa.red.id, "nombre": "Ana", "d": {"que": "enemigos", "mapa": pb.mundo.id,
                                                                   "e": [{"k": 0, "nombre": "Rival", "salud": 50, "arma": "punos", "x": pb.j.x, "y": pb.j.y, "inofensivo": False}]}})
        assert pb.sv["ecos"][0].deportivo is False and pb.sv["ecos"][0].salud == 50
    finally:
        pa.mision = None
        pb._sv_quitar_ecos()
