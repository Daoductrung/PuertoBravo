"""Actualizar con un servidor abierto, y jugar en un servidor que se reinicia.

Tres partes. El servidor solo, con clientes de mentira: la parada ordenada (aviso, espera de los guardados, saldos,
código de salida), la orden por archivo y por consola, y lo que oye un juego anterior. El juego de verdad contra un
servidor local que se va y vuelve: la pantalla de espera, la vuelta con la partida tal cual y sin duplicar dinero,
Escape, el tiempo máximo, la versión más nueva y el servidor antiguo que simplemente se cae. Y el actualizador: cómo
apunta lo que había abierto, cómo pide la parada y cómo lo vuelve a arrancar, con procesos de mentira.

Nada sale a la red ni toca un servidor real: todo corre en este equipo, y no se instala ni se descarga nada.
"""
import ast
import glob
import json
import os
import socket
import subprocess
import sys
import threading
import time

import pygame
import pytest

from conftest import Robot                                               # noqa: F401
from juego import actualizador as A
from juego import enlinea, menus_actualizar, reconexion
from juego.menus import Menu
from servidor import __main__ as arranque
from servidor import almacen, enmarcha, nucleo, opciones
from test_enlinea import ambos, dos, entrar, hasta, juntos               # noqa: F401  (dos es una fixture)
from test_servidor import Banco, Cli, lejos_de_todo, mundo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNCIONES_170 = ("vehiculos", "combate", "bandas", "barrios", "grupos", "propiedades", "robos", "personajes", "mundo", "versiones")


# ---------------------------------------------------------------------------------------- ayudantes
def _j(b, c):
    return b.srv.jugadores[c.id]


def _esperar(cond, segundos=10.0):
    fin = time.time() + segundos
    while time.time() < fin:
        if cond():
            return True
        time.sleep(0.05)
    return False


def _fin(b, segundos=20.0):
    """Espera a que el servidor del banco termine de pararse solo, y recoge su hilo."""
    assert _esperar(lambda: b.srv.detenido, segundos), "el servidor no termina de pararse"
    b.loop.call_soon_threadsafe(b.loop.stop)
    b.hilo.join(5)


def _parar_para(b, causa="actualizacion", aviso=0):
    b.hacer(lambda: b.srv.parar_para_volver(causa, aviso))


def _pasar(robot, fotogramas):
    """Deja pasar el tiempo del juego sin ir más deprisa que el reloj de verdad (si no, el servidor echa al juego)."""
    for _ in range(0, fotogramas, 3):
        robot.frames(3)
        time.sleep(0.03)


def _espera(robot, segundos=10.0):
    """Avanza el juego hasta que abre la pantalla de espera, y la devuelve."""
    fin = time.time() + segundos
    while time.time() < fin and not isinstance(robot.app.pila[-1], reconexion.Espera):
        _pasar(robot, 3)
    e = robot.app.pila[-1]
    assert isinstance(e, reconexion.Espera), robot.dicho()[-400:]
    return e


def _avanzar(e, robot, segundos, hasta_que=None):
    """Hace pasar el tiempo de la pantalla de espera, de segundo en segundo, sin esperar de verdad."""
    for _ in range(int(segundos)):
        if robot.app.pila[-1] is not e or (hasta_que is not None and hasta_que()):
            return
        e.actualizar(1.0)


def _oir(robot):
    sonados = []
    original = robot.app.mez.sonar

    def sonar(nombre, *a, **kw):
        sonados.append(nombre)
        return original(nombre, *a, **kw)
    robot.app.mez.sonar = sonar
    return sonados


def _cuenta(carpeta, nombre):
    """La fila de una cuenta, leída del disco con el servidor ya parado."""
    alm = almacen.Almacen(os.path.join(str(carpeta), "puertobravo.db"))
    try:
        return dict(alm.cuenta_por_nombre(nombre))
    finally:
        alm.cerrar()


def _puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


# ====================================================================== el servidor: la parada ordenada
def test_el_servidor_nuevo_sigue_escrito_para_python_3_8():
    for ruta in glob.glob(os.path.join(os.path.dirname(nucleo.__file__), "*.py")):
        with open(ruta, encoding="utf-8") as f:
            ast.parse(f.read(), feature_version=(3, 8))
    assert os.path.exists(os.path.join(os.path.dirname(nucleo.__file__), "enmarcha.py"))
    for clave, serie in (("parada_aviso", 20), ("parada_espera", 6)):
        assert opciones.POR_CLAVE[clave].defecto == serie and not opciones.POR_CLAVE[clave].reinicio
    assert "reconexion" in nucleo.FUNCIONES and "reconexion" in enlinea.SABE
    ordenes = [o for o, _ in nucleo.Servidor.AYUDA_ORDENES]
    assert "actualizar" in ordenes and "reiniciar" in ordenes and "apagar" in ordenes


def test_parada_para_actualizar_avisa_espera_los_guardados_guarda_saldos_y_sale_con_su_codigo(tmp_path):
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=500, parada_espera=8)
    x, y = lejos_de_todo()
    nuevo = Cli(b, "Nuria", sabe=["reconexion", "topes"])
    viejo = Cli(b, "Víctor")                                     # un juego de la 1.7.0: no dice que sepa nada
    assert "reconexion" in nuevo.ok["funciones"]
    nuevo.estado(x=x, y=y, di=400, ba=0, v="sedan", s=3.0)
    viejo.estado(x=x + 30, y=y, di=450, ba=0)
    time.sleep(0.3)
    nuevo.enviar({"t": "veh_tomar", "modelo": "sedan", "nombre": "Mi sedán", "salud": 90, "ref": 1})
    vid = nuevo.leer("veh_tuyo")["id"]
    # los dos guardan su personaje, y después gastan: Nuria vuelve a guardar al cerrarse el servidor; Víctor, no
    nuevo.enviar({"t": "guardar", "p": {"jugador": {"dinero": 400, "banco": 0}}, "ya": True})
    viejo.enviar({"t": "guardar", "p": {"jugador": {"dinero": 450, "banco": 0}}, "ya": True})
    nuevo.leer("guardado"), viejo.leer("guardado")
    nuevo.estado(x=x, y=y, di=300, ba=0, v="sedan", s=3.0)
    viejo.estado(x=x + 30, y=y, di=250, ba=0)
    time.sleep(0.3)
    jn, jv = _j(b, nuevo), _j(b, viejo)
    assert jn.saldo == 300 and jv.saldo == 250 and jv.gasto_pend == 200
    t0 = time.time()
    _parar_para(b, "actualizacion", 2)
    # el aviso: al juego nuevo, con cifras; al anterior, con un texto de los de siempre
    pa = nuevo.leer("parada")
    assert pa["causa"] == "actualizacion" and pa["en"] == 2 and pa["vuelve"] == 120
    av = viejo.leer("aviso")
    assert "2 segundos" in av["texto"] and "actualizarse" in av["texto"] and "vuelve a entrar" in av["texto"] and av["son"] == "notificacion"
    assert viejo.nada("parada", 0.2) and nuevo.nada("aviso", 0.2)
    # mientras dura la cuenta atrás se sigue jugando, y quien entra entonces se entera
    tardio = Cli(b, "Tere", sabe=["reconexion"])
    assert tardio.ok and tardio.leer("parada")["en"] <= 2
    # el cierre: dice por qué, y un juego anterior lo entiende porque lleva su texto de siempre
    cn, cv = nuevo.leer("cerrado"), viejo.leer("cerrado")
    assert 1.5 <= time.time() - t0 <= 8
    assert cn["causa"] == "actualizacion" and cn["vuelve"] == 120 and cv["motivo"] == nucleo.CAUSAS["actualizacion"] and "actualizarse" in cv["motivo"]
    # ya no entra nadie, y se le dice de una manera que el juego entiende
    fuera = Cli(b, "Zoe")
    assert fuera.ok is None and "reiniciando" in fuera.rechazo
    # Nuria manda su último guardado y el servidor la espera; a Víctor y a Tere los espera hasta el tope
    nuevo.enviar({"t": "guardar", "p": {"jugador": {"dinero": 300, "banco": 0, "marca": "al cerrar"}}, "ya": True})
    assert nuevo.leer("guardado")
    _fin(b)
    assert any("No ha llegado a tiempo el último guardado de 2 jugadores" in t for t in b.lineas)
    assert b.srv.codigo_salida == nucleo.CODIGO_VUELVE == 75 and b.srv.causa_parada == "actualizacion"
    # en el disco: el personaje de Nuria como lo mandó al cerrar, su saldo y su margen, y su vehículo aparcado donde estaba
    fila = _cuenta(tmp_path, "Nuria")
    assert json.loads(fila["partida"])["jugador"]["marca"] == "al cerrar" and fila["saldo"] == 300 and fila["margen"] is not None and fila["t_margen"]
    alm = almacen.Almacen(os.path.join(str(tmp_path), "puertobravo.db"))
    try:
        v = next(v for v in alm.vehiculos() if v["id"] == vid)
        assert v["por"] is None and abs(v["x"] - x) < 1 and v["m"] == "puerto_bravo"
    finally:
        alm.cerrar()
    # Víctor no llegó a guardar lo que compró: su personaje guardado no lo tiene, así que el dinero vuelve. Nada se duplica.
    fila = _cuenta(tmp_path, "Víctor")
    assert fila["saldo"] == 450 and json.loads(fila["partida"])["jugador"]["dinero"] == 450
    for c in (nuevo, viejo, tardio, fuera):
        c.cerrar()


def test_si_todos_guardan_enseguida_el_servidor_no_espera_mas_y_sin_nadie_no_hay_cuenta_atras(tmp_path):
    b = Banco(tmp_path, parada_espera=20)
    a = Cli(b, "Ana", sabe=["reconexion"])
    a.estado()
    t0 = time.time()
    _parar_para(b, "reinicio", 0)
    assert a.leer("cerrado")["causa"] == "reinicio"
    a.enviar({"t": "guardar", "p": {"jugador": {"dinero": 1}}, "ya": True})
    a.enviar({"t": "adios"})
    _fin(b)
    assert time.time() - t0 < 6 and not any("No ha llegado a tiempo" in t for t in b.lineas)
    a.cerrar()
    # sin nadie dentro, una parada con cuenta atrás larga no espera a nadie
    b = Banco(tmp_path / "vacio")
    t0 = time.time()
    _parar_para(b, "actualizacion", 60)
    _fin(b, 8)
    assert time.time() - t0 < 5 and b.srv.codigo_salida == 75


def test_parar_sin_mas_ya_guarda_el_saldo_y_el_margen_de_quien_esta_dentro(tmp_path):
    """Lo que pasaba antes: «detener» cortaba sin pasar por la salida de cada jugador, y su saldo y su margen se quedaban
    como en el último guardado."""
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=500)
    a = Cli(b, "Ana")
    a.estado(di=500, ba=0)
    time.sleep(0.2)
    a.estado(di=700, ba=0)                                       # gana 200 por su cuenta, dentro de su margen
    time.sleep(0.3)
    ja = _j(b, a)
    assert ja.saldo == 700
    margen = ja.margen
    hilo = threading.Thread(target=b.parar)
    hilo.start()
    m = a.leer("cerrado")
    hilo.join(15)
    assert m["causa"] == "apagado" and m["motivo"] == "El servidor se ha cerrado." and b.srv.codigo_salida == 0
    fila = _cuenta(tmp_path, "Ana")
    assert fila["saldo"] == 700 and abs(fila["margen"] - margen) < 5
    a.cerrar()


def test_las_ordenes_actualizar_y_reiniciar_de_la_consola(tmp_path):
    b = Banco(tmp_path)
    a = Cli(b, "Ana", sabe=["reconexion"])
    a.estado()
    assert "segundos de aviso" in b.hacer(lambda: b.srv.orden("actualizar pronto"))
    r = b.hacer(lambda: b.srv.orden("reiniciar 1"))
    assert "dentro de 1 segundos" in r and "volverán a entrar solos" in r
    assert a.leer("parada")["causa"] == "reinicio"
    assert "ya se está parando" in b.hacer(lambda: b.srv.orden("actualizar"))
    c = a.leer("cerrado")
    assert c["causa"] == "reinicio" and "mantenimiento" in c["motivo"]
    _fin(b)
    assert b.srv.codigo_salida == 75 and b.srv.causa_parada == "reinicio"
    a.cerrar()
    # sin número, la cuenta atrás es la de la configuración
    b = Banco(tmp_path / "dos", parada_aviso=1)
    a = Cli(b, "Ana", sabe=["reconexion"])
    a.estado()
    assert "dentro de 1 segundos" in b.hacer(lambda: b.srv.orden("actualizar"))
    assert a.leer("parada")["en"] == 1 and a.leer("cerrado")["causa"] == "actualizacion"
    _fin(b)
    a.cerrar()


def test_la_orden_por_archivo_para_un_servidor_de_verdad_y_el_programa_sale_con_el_codigo_75(tmp_path, capsys):
    conf, datos, puerto = tmp_path / "servidor.conf", tmp_path / "datos", _puerto_libre()
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), datos=str(datos), puerto=puerto, interfaz="127.0.0.1", cifrado="no", personajes=0,
                                     parada_aviso=1, parada_espera=1))
    salida = []
    hilo = threading.Thread(target=lambda: salida.append(arranque.main([str(conf)])), daemon=True)
    hilo.start()
    assert _esperar(lambda: (datos / "puertobravo.db").exists(), 15)
    time.sleep(1.0)

    class Donde:
        pass
    Donde.puerto = puerto
    a = Cli(Donde, "Ana", sabe=["reconexion"])
    assert a.ok
    a.estado()
    assert arranque.main([str(conf), "--actualizar"]) == 0       # deja el archivo de órdenes y espera a que lo recojan
    assert a.leer("parada")["causa"] == "actualizacion" and a.leer("cerrado")["causa"] == "actualizacion"
    hilo.join(20)
    assert not hilo.is_alive() and salida == [75]
    dicho = capsys.readouterr().out
    assert "Se ha pedido parar el servidor para actualizarlo" in dicho and "con una cuenta atrás" in dicho and "código 75" in dicho
    assert not (datos / nucleo.ARCHIVO_ORDEN).exists() and arranque.ARCHIVO_PARAR == nucleo.ARCHIVO_ORDEN == "parar.txt"
    a.cerrar()
    # un archivo de órdenes que quedó de otra vez no para al servidor nada más arrancar
    (datos / "parar.txt").write_text("actualizar\n", encoding="utf-8")
    b = Banco(datos)
    time.sleep(1.5)
    assert b.srv.activo and not b.srv.parando and not (datos / "parar.txt").exists()
    # y escrito a mano, con «reiniciar» y sus segundos, también vale: es lo que usa quien lo lleva en Linux o en un NAS
    c = Cli(b, "Ana", sabe=["reconexion"])
    c.estado()
    (datos / "parar.txt").write_text("reiniciar 1\n", encoding="utf-8")
    assert c.leer("parada")["causa"] == "reinicio" and c.leer("cerrado")["causa"] == "reinicio"
    _fin(b)
    assert any("por mantenimiento" in t for t in b.lineas) and b.srv.codigo_salida == 75
    c.cerrar()


def test_un_servidor_de_verdad_en_su_proceso_deja_ficha_obedece_la_orden_y_sale_con_75(tmp_path):
    """El caso entero con un proceso de verdad (uno nuestro, de pruebas): la ficha de «en marcha», la orden que deja el
    actualizador en la carpeta de datos y el código con el que termina."""
    conf, datos, fichas = tmp_path / "servidor.conf", tmp_path / "datos", tmp_path / "en_marcha"
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), datos=str(datos), puerto=_puerto_libre(), interfaz="127.0.0.1", cifrado="no",
                                     personajes=0, parada_aviso=0, parada_espera=0))
    entorno = dict(os.environ, PYTHONPATH=RAIZ, PYTHONUTF8="1", PUERTOBRAVO_EN_MARCHA=str(fichas))
    proc = subprocess.Popen([sys.executable, "-m", "servidor", str(conf)], cwd=str(tmp_path), env=entorno, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        assert _esperar(lambda: len(enmarcha.leer(str(fichas))) == 1, 30), "el servidor no deja su ficha"
        f = enmarcha.leer(str(fichas))[0]
        pid = f["pid"]                                           # el del servidor de verdad (el del entorno virtual es solo un lanzador)
        assert f["tipo"] == "consola" and f["args"] == [str(conf)] and f["activo"] is True
        assert os.path.samefile(f["datos"], str(datos)) and os.path.samefile(f["cwd"], str(tmp_path)) and os.path.samefile(f["conf"], str(conf))
        assert A.proceso_vivo(pid, f["exe"]) and not A.proceso_vivo(pid, "otro.exe")
        time.sleep(1.2)
        nota = A.pedir_parada_servidores([dict(f, servicio=False)], trabajo=str(tmp_path / "trabajo"))
        assert json.load(open(nota, encoding="utf-8"))["servidores"][0]["pid"] == pid
        assert proc.wait(30) == 75
        assert enmarcha.leer(str(fichas)) == [] and not A.proceso_vivo(pid)
        assert "para actualizarlo" in proc.stdout.read().decode("utf-8", "replace")
    finally:
        if proc.poll() is None:
            proc.kill()


def test_los_rechazos_llevan_un_codigo_que_el_juego_entiende(tmp_path):
    b = Banco(tmp_path, version_minima="9.9.9")
    s = socket.create_connection(("127.0.0.1", b.puerto), timeout=5)
    s.close()
    cli = enlinea.ClienteServidor()
    import hashlib
    ok, motivo = cli.conectar_servidor("127.0.0.1", b.puerto, "Ana", hashlib.sha256(b"x").digest(), mundo()["huella"])
    assert not ok and motivo.codigo == "version" and motivo.minima == "9.9.9" and "9.9.9" in motivo
    assert reconexion.codigo_de(motivo) == "version"
    b.parar()
    b = Banco(tmp_path / "lleno", max_jugadores=1, primer_admin="no")
    a = Cli(b, "Ana")
    ok, motivo = cli.conectar_servidor("127.0.0.1", b.puerto, "Blas", hashlib.sha256(b"y").digest(), mundo()["huella"])
    assert not ok and motivo.codigo == "lleno"
    a.cerrar()
    b.parar()
    # nadie escucha en ese puerto: «red», que es lo que hace que la espera siga probando
    ok, motivo = cli.conectar_servidor("127.0.0.1", _puerto_libre(), "Ana", hashlib.sha256(b"x").digest(), "h", timeout=2)
    assert not ok and motivo.codigo == "red"
    # con un servidor anterior no hay código: se deduce del texto, que es el de la 1.7.0
    for texto, codigo in (("El servidor está lleno.", "lleno"), ("Hay demasiadas conexiones desde tu dirección. Prueba dentro de un momento.", "lleno"),
                          ("Este servidor pide la versión 1.8.0 del juego o una posterior, y la tuya es la 1.7.0. Actualiza el juego para entrar.", "version"),
                          ("Tu juego es demasiado antiguo para este servidor. Actualiza el juego.", "version"),
                          ("No puedes entrar en este servidor.", ""), ("certificado: abcd", "certificado"),
                          ("No se pudo conectar con el servidor. Comprueba la dirección.", "red")):
        assert reconexion.codigo_de(texto) == codigo, texto


def test_quien_vuelve_en_plena_pelea_no_deja_dos_fichas_ni_estrena_proteccion(tmp_path):
    b = Banco(tmp_path, proteccion=20)
    x, y = lejos_de_todo()
    a, c = Cli(b, "Ana"), Cli(b, "Ciro")
    a.estado(x=x, y=y)
    c.estado(x=x + 3, y=y)
    time.sleep(0.3)
    ja = _j(b, a)
    b.hacer(lambda: ja.golpeado.__setitem__(c.id, time.monotonic()))      # está en plena pelea
    a.s.close()                                                  # se le corta la conexión
    assert _esperar(lambda: not ja.dentro and ja.fantasma, 5)
    assert a.id in b.srv.jugadores                               # sigue ahí quince segundos: cortar no es escapatoria
    a2 = Cli(b, "Ana")                                           # y vuelve antes de que pasen
    assert a2.ok and a.id not in b.srv.jugadores
    assert sum(1 for j in b.srv.jugadores.values() if j.nombre == "Ana") == 1
    j2 = _j(b, a2)
    assert j2.protegido == 0.0 and c.id in j2.golpeado           # hereda la pelea, sin protección de llegada
    assert c.leer("sale")["id"] == a.id
    for cli in (a2, c):
        cli.cerrar()
    b.parar()


def test_a_quien_buscaba_la_policia_le_sigue_buscando_tras_el_reinicio(tmp_path):
    b = Banco(tmp_path, policia="si")
    a = Cli(b, "Ana")
    cuenta = a.ok["cuenta"]
    b.hacer(lambda: b.srv.buscados_fuera.__setitem__(cuenta, (42.0, time.monotonic())))
    a.cerrar()
    _parar_para(b, "actualizacion", 0)
    _fin(b)
    b = Banco(tmp_path, policia="si")
    assert b.srv.buscados_fuera[cuenta][0] == 42.0
    b.parar()


# ====================================================================== el panel: la ficha y las órdenes
def test_el_panel_obedece_la_orden_de_actualizar_y_la_ve_tambien_con_el_servidor_parado(tmp_path, monkeypatch):
    from panel_servidor import motor as M_
    monkeypatch.setenv("PUERTOBRAVO_EN_MARCHA", str(tmp_path / "en_marcha"))
    conf, datos = tmp_path / "servidor.conf", tmp_path / "datos"
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), datos=str(datos), puerto=0, interfaz="127.0.0.1", cifrado="no", personajes=0,
                                     parada_aviso=0, parada_espera=0))
    m = M_.Motor(str(conf))
    try:
        # parado: la orden de actualizar la recoge el panel, que es quien tiene que cerrarse; cualquier otra se borra sin más
        os.makedirs(str(datos), exist_ok=True)
        assert m.orden_pendiente() == ""
        (datos / "parar.txt").write_text("parar\n", encoding="utf-8")
        assert m.orden_pendiente() == "" and not (datos / "parar.txt").exists()
        (datos / "parar.txt").write_text("actualizar\n", encoding="utf-8")
        assert m.orden_pendiente() == "actualizar" and not (datos / "parar.txt").exists()
        # la ficha dice que es el panel y si su servidor está en marcha
        ruta = m.anotar()
        f = json.load(open(ruta, encoding="utf-8"))
        assert f["tipo"] == "panel" and f["activo"] is False and os.path.samefile(f["datos"], str(datos)) and f["pid"] == os.getpid()
        assert m.arrancar() and _esperar(m.en_marcha, 20)
        assert json.load(open(m.anotar(), encoding="utf-8"))["activo"] is True
        assert m.orden_pendiente() == ""                          # en marcha, el archivo lo mira el servidor, no el panel
        (datos / "parar.txt").write_text("actualizar\n", encoding="utf-8")
        assert m.esperar_parado(20) and m.causa_parada == "actualizacion"      # con esto, la ventana se cierra sola
        # y un reinicio pedido desde el panel se dice como tal a los juegos, para que esperen
        assert m.arrancar() and _esperar(m.en_marcha, 20) and m.causa_parada is None
        assert m.parar(causa="reinicio") and m.esperar_parado(20) and m.causa_parada == "reinicio"
        assert m.arrancar() and _esperar(m.en_marcha, 20)
        assert m.parar() and m.esperar_parado(20) and m.causa_parada == "apagado"
    finally:
        if m.en_marcha():
            m.parar()
            m.esperar_parado(20)
        enmarcha.quitar()
    assert enmarcha.leer(str(tmp_path / "en_marcha")) == []
    with open(os.path.join(RAIZ, "panel_servidor", "ventana.py"), encoding="utf-8") as f:
        ventana = f.read()
    assert 'causa_parada == "actualizacion"' in ventana and "orden_pendiente()" in ventana and "--arrancar" in ventana


# ====================================================================== el juego: esperar y volver
def _preparar(robot, tmp_path, **cfg):
    """Un juego dentro de un servidor con economía, con dinero y posición ya asentados en el servidor."""
    b = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000, **cfg)
    p = entrar(robot, b, "Ana")
    p.j.dinero, p.j.banco = 3000, 500                            # antes de la primera posición: es con lo que empieza en el servidor
    x, y = lejos_de_todo(p.mundo.id)
    p.teletransportar(x, y)
    _pasar(robot, 30)
    return b, p


def test_el_servidor_se_actualiza_y_el_juego_espera_vuelve_solo_y_queda_tal_cual(robot, tmp_path):
    b, p = _preparar(robot, tmp_path, parada_espera=5)
    puerto = b.puerto
    sonados = _oir(robot)
    # lo que lleva el jugador: un vehículo del servidor, una misión a medias, menos salud, un arma, dinero y algo comprado
    x, y = p.pos()
    v = p.crear_vehiculo("sedan", x + 3, y, 0, "aparcado")
    p._subir(v, True)
    assert hasta(lambda: getattr(v, "id_red", None) is not None and v.red_mio, robot, robot)
    vid = v.id_red
    mis = next(m for m in p.datos["misiones"] if m["id"] == "m04")
    p.iniciar_mision(mis)
    robot.saltar_dialogos()
    paso = p.mision["paso"]
    p.j.salud = 61.0
    p.j.arma = "pistola"
    p.j.armas["pistola"] = 23 if isinstance(p.j.armas, dict) else p.j.armas
    p.j.objetos["botiquin"] = p.j.objetos.get("botiquin", 0) + 2
    assert p.pagar(250)
    _pasar(robot, 20)
    dinero, banco = p.j.dinero, p.j.banco
    ja = b.srv.jugadores[p.red.id]
    assert hasta(lambda: ja.saldo == dinero + banco, robot, robot)
    pos, hora_antes = p.pos(), p.reloj
    # el servidor avisa de que se reinicia para actualizarse: el juego lo dice a su manera
    _parar_para(b, "actualizacion", 2)
    assert hasta(lambda: "se reinicia para actualizarse" in robot.dicho(), robot, robot, 6)
    assert "dentro de 2 segundos" in robot.dicho() and "te reconecto y sigues donde estabas" in robot.dicho()
    e = _espera(robot, 12)
    assert e.causa == "actualizacion" and "El servidor se está actualizando" in robot.dicho() and "Te reconectaré en cuanto vuelva" in robot.dicho()
    assert "Escape deja de esperar" in robot.dicho() and e.pausa_mundo
    _fin(b)
    # el servidor esperó el último guardado del juego: en el disco está el personaje como estaba al cerrarse
    fila = _cuenta(tmp_path, "Ana")
    guardado = json.loads(fila["partida"])["jugador"]
    assert guardado["dinero"] == dinero and guardado["objetos"]["botiquin"] == p.j.objetos["botiquin"] and fila["saldo"] == dinero + banco
    assert not any("No ha llegado a tiempo" in t for t in b.lineas)
    # mientras espera: la partida sigue en memoria tal cual, suena el tono de espera, y dice cómo va sin agobiar
    assert robot.app.partida is p and p.en_servidor and not p.online_activo() and p.sv_espera["avisado"]
    del robot.app.voz.registro[:]
    _avanzar(e, robot, 29)
    assert "espera_servidor" in sonados and sonados.count("espera_servidor") <= 6 and e.n >= 3
    assert "Llevas esperando" not in robot.dicho()                # medio minuto callado, salvo el tono
    _avanzar(e, robot, 2)
    assert "Llevas esperando 30 segundos" in robot.dicho()
    robot.tecla(pygame.K_SPACE)                                  # cualquier tecla lo repite
    assert "Llevas esperando 30 segundos" in robot.dicho().split(" | ")[-1] and "todavía no contesta" in robot.dicho().split(" | ")[-1]
    robot.tecla(pygame.K_F1)
    assert "Pantalla de espera del servidor" in robot.dicho() and "Opciones, Jugar en línea" in robot.dicho()
    assert robot.app.pila[-1] is e and p.pos() == pos and p.j.veh is v and p.mision["paso"] == paso and p.j.salud == 61.0
    # las esperas entre intentos crecen hasta un tope: no se machaca al servidor
    assert reconexion.ESPERAS == tuple(sorted(reconexion.ESPERAS)) and reconexion.ESPERAS[-1] <= 20
    # el servidor vuelve, en el mismo sitio y con sus datos
    b2 = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000, puerto=puerto)
    try:
        _avanzar(e, robot, 40)
        assert robot.app.pila[-1] is p, robot.dicho()[-400:]
        assert "Reconectado a Servidor de Puerto Bravo. Sigues donde estabas, al volante de tu" in robot.dicho()
        # tal cual: sitio, vehículo, salud, arma, dinero, lo comprado y la misión con su paso
        assert p.pos() == pos and p.j.veh is v and p.j.salud == 61.0 and p.j.arma == "pistola" and (p.j.dinero, p.j.banco) == (dinero, banco)
        assert p.mision is not None and p.mision["def"]["id"] == "m04" and p.mision["paso"] == paso
        assert p.en_servidor and p.online_activo() and p.sv_espera is None
        assert abs(p.reloj - b2.srv.reloj) < 5 and abs(p.reloj - hora_antes) < 30      # la hora es la del servidor, que la guardó al pararse
        j2 = b2.srv.jugadores[p.red.id]
        assert hasta(lambda: j2.vid == vid and v.red_mio and v.id_red == vid and p.sv["reenganche"] is None, robot, robot, 8), (j2.vid, vid, p.sv["reenganche"])
        assert sum(1 for d in b2.srv.vehiculos.values() if d.get("dueno") == j2.cuenta) == 1      # un vehículo, no dos
        assert sum(1 for o in p.vehiculos if getattr(o, "id_red", None) == vid) == 1
        # el dinero no se duplica: el servidor reconoce justo lo que había, y el personaje que queda guardado es el de ahora
        assert hasta(lambda: j2.saldo == dinero + banco and j2.total_guardado == dinero + banco, robot, robot, 8)
        assert abs(j2.x - pos[0]) < 1 and abs(j2.y - pos[1]) < 1
        assert "retira" not in robot.dicho().split("Reconectado")[-1]
        # y se sigue jugando con normalidad: un gasto llega al servidor
        assert p.pagar(100)
        assert hasta(lambda: j2.saldo == dinero + banco - 100, robot, robot, 6)
    finally:
        p.sv_salir()
        b2.parar()


def test_volver_no_abre_un_agujero_para_fabricar_dinero(robot, tmp_path):
    b, p = _preparar(robot, tmp_path, parada_espera=5)
    puerto = b.puerto
    total = p.j.dinero + p.j.banco
    ja = b.srv.jugadores[p.red.id]
    assert hasta(lambda: ja.saldo == total, robot, robot)
    b.hacer(lambda: setattr(ja, "margen", 300.0))
    _parar_para(b, "actualizacion", 0)
    e = _espera(robot)
    _fin(b)
    # mientras espera, un juego trucado se pone veinte mil euros más
    p.j.dinero += 20000
    b2 = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000, puerto=puerto)
    try:
        _avanzar(e, robot, 40)
        assert robot.app.pila[-1] is p
        j2 = b2.srv.jugadores[p.red.id]
        # el servidor juzga ese dinero con sus reglas de siempre: reconoce lo que cabe en el margen de la cuenta y retira el resto
        assert hasta(lambda: p.j.dinero + p.j.banco == j2.saldo and j2.saldo <= total + 320, robot, robot, 10), (p.j.dinero, j2.saldo)
        assert j2.saldo >= total and "retira" in robot.dicho()
    finally:
        p.sv_salir()
        b2.parar()


def test_un_corte_de_conexion_tambien_se_espera_y_lo_comprado_justo_antes_no_se_pierde_ni_se_duplica(robot, tmp_path):
    b, p = _preparar(robot, tmp_path)
    try:
        ja = b.srv.jugadores[p.red.id]
        p.sv_guardar(ya=True)
        total = p.j.dinero + p.j.banco
        assert hasta(lambda: ja.total_guardado == total, robot, robot)
        botiquines = p.j.objetos.get("botiquin", 0)
        p.j.objetos["botiquin"] = botiquines + 3                 # compra, y el cable se va antes de que se guarde
        assert p.pagar(300)
        assert hasta(lambda: ja.gasto_pend == 300, robot, robot, 3)
        p.red.sock.close()
        e = _espera(robot)
        assert e.causa == "corte" and "Se ha cortado la conexión con el servidor" in robot.dicho() and "Voy a intentar volver a entrar yo solo" in robot.dicho()
        assert p.sv_espera["avisado"] is False and p.sv_espera["sin_guardar"] is not None
        # el servidor, al ver que se va sin guardar, le reconoce otra vez los 300: su personaje guardado no tiene la compra
        assert _esperar(lambda: _j_cuenta(b, "Ana") is None, 6)
        assert b.hacer(lambda: b.srv.alm.cuenta_por_nombre("Ana")["saldo"]) == total
        # el servidor sigue ahí: al primer intento entra, con su partida viva (la compra hecha y el dinero gastado)
        _avanzar(e, robot, 10)
        assert robot.app.pila[-1] is p and e.n == 1
        j2 = b.srv.jugadores[p.red.id]
        assert hasta(lambda: j2.saldo == total - 300 and j2.total_guardado == total - 300, robot, robot, 8), (j2.saldo, j2.total_guardado)
        assert p.j.objetos["botiquin"] == botiquines + 3 and p.j.dinero + p.j.banco == total - 300
        guardado = json.loads(b.hacer(lambda: b.srv.alm.cuenta_por_nombre("Ana")["partida"]))["jugador"]
        assert guardado["objetos"]["botiquin"] == botiquines + 3 and guardado["dinero"] + guardado.get("banco", 0) == total - 300
    finally:
        p.sv_salir()
        b.parar()


def _j_cuenta(b, nombre):
    return next((j for j in b.srv.jugadores.values() if j.nombre == nombre and j.dentro), None)


def test_escape_deja_de_esperar_y_sale_al_menu(robot, tmp_path):
    b, p = _preparar(robot, tmp_path)
    _parar_para(b, "actualizacion", 0)
    e = _espera(robot)
    _fin(b)
    _avanzar(e, robot, 8)
    robot.tecla(pygame.K_ESCAPE)
    app = robot.app
    assert app.partida is None and isinstance(app.pila[-1], Menu) and len(app.pila) == 1 and e.estado == "fin"
    dicho = robot.dicho().split(" | ")[-1]
    assert "Dejas de esperar" in dicho and "quedó guardado en el servidor justo antes de que se cerrara" in dicho and "Jugar en un servidor" in dicho
    assert not p.en_servidor and p.red is None and app.cfg.temporales == {}


def test_si_el_servidor_no_vuelve_en_el_tiempo_maximo_se_dice_y_se_sale_al_menu(robot, tmp_path):
    robot.app.cfg["reconectar_minutos"] = 1
    b, p = _preparar(robot, tmp_path)
    _parar_para(b, "reinicio", 0)
    e = _espera(robot)
    assert e.causa == "reinicio" and e.maximo == 60.0 and "mantenimiento" in robot.dicho()
    _fin(b)
    _avanzar(e, robot, 58)
    assert robot.app.pila[-1] is e
    _avanzar(e, robot, 4)
    assert robot.app.partida is None and isinstance(robot.app.pila[-1], Menu)
    dicho = robot.dicho().split(" | ")[-1]
    assert "no ha vuelto en 1 minuto" in dicho and "Opciones, Jugar en línea" in dicho and "guardado" in dicho
    assert 4 <= e.n <= 9                                         # ha probado unas cuantas veces, cada vez con más calma


def test_el_servidor_vuelve_pidiendo_una_version_mas_nueva(robot, tmp_path, monkeypatch):
    monkeypatch.setattr(reconexion, "_ruta_volver", lambda: str(tmp_path / "volver_servidor.json"))
    b, p = _preparar(robot, tmp_path)
    puerto = b.puerto
    _parar_para(b, "actualizacion", 0)
    e = _espera(robot)
    _fin(b)
    b2 = Banco(tmp_path, economia="si", puerto=puerto, version_minima="9.9.9")
    try:
        _avanzar(e, robot, 30, lambda: e.estado == "version")
        assert e.estado == "version" and robot.app.pila[-1] is e
        dicho = robot.dicho().split(" | ")[-1]
        assert "ahora pide la versión 9.9.9 del juego" in dicho and "Pulsa Intro para buscar la actualización" in dicho and "Escape para salir" in dicho
        n = e.n
        _avanzar(e, robot, 30)
        assert e.n == n                                          # ya no insiste: no va a entrar hasta que se actualice
        # Intro busca la actualización (aquí, sin red) y deja apuntado a qué servidor se quería volver
        robot.app.act_abrir = lambda url, tiempo=0, desde=0: (_ for _ in ()).throw(OSError("sin red"))
        robot.tecla(pygame.K_RETURN)
        robot.frames(3)
        assert "No se pudo conectar" in robot.dicho() or "No se pudo comprobar" in robot.dicho()
        nota = json.load(open(str(tmp_path / "volver_servidor.json"), encoding="utf-8"))
        assert nota["dir"] == p._sv_servidor["dir"] and set(nota) == {"dir", "nombre", "t"}      # ni identidad ni contraseñas
        assert robot.app.pila[-1] is e                           # no se pudo buscar: sigue en la pantalla, que lo vuelve a explicar
        robot.tecla(pygame.K_ESCAPE)
        assert robot.app.partida is None and "Dejas de esperar" in robot.dicho()
    finally:
        b2.parar()
    # tras actualizar, el juego ofrece volver a ese servidor, si sigue en la lista
    app = robot.app
    app.cfg["servidores"] = [{"nombre": "El de Ana", "dir": nota["dir"], "cert": ""}]
    leida = reconexion.leer_vuelta()
    assert leida["dir"] == nota["dir"] and not os.path.exists(str(tmp_path / "volver_servidor.json")) and reconexion.leer_vuelta() is None
    assert reconexion.ofrecer_vuelta(app, leida)
    m = app.pila[-1]
    assert isinstance(m, Menu) and "Antes de actualizar estabas en El de Ana" in m.titulo and m.opciones[0].texto == "Volver a entrar en El de Ana"
    robot.tecla(pygame.K_ESCAPE)
    assert not reconexion.ofrecer_vuelta(app, {"dir": "puertobravo://otro:1", "nombre": "x"})
    # una nota vieja no vale
    with open(str(tmp_path / "volver_servidor.json"), "w", encoding="utf-8") as f:
        json.dump({"dir": nota["dir"], "nombre": "x", "t": time.time() - 3 * 3600}, f)
    assert reconexion.leer_vuelta() is None


def test_si_al_volver_el_servidor_no_deja_entrar_se_explica_y_se_sale_al_menu(robot, tmp_path):
    b, p = _preparar(robot, tmp_path)
    puerto = b.puerto
    _parar_para(b, "actualizacion", 0)
    e = _espera(robot)
    _fin(b)
    b2 = Banco(tmp_path, economia="si", puerto=puerto, vetados="Ana")
    try:
        _avanzar(e, robot, 30)
        assert robot.app.partida is None and isinstance(robot.app.pila[-1], Menu)
        dicho = robot.dicho().split(" | ")[-1]
        assert "ha vuelto, pero no te deja entrar como antes" in dicho and "No puedes entrar en este servidor" in dicho and "guardado" in dicho
    finally:
        b2.parar()


def test_un_servidor_anterior_que_se_cierra_o_se_cae_tambien_se_espera(robot, tmp_path, monkeypatch):
    """Un servidor de la 1.7.0 no avisa ni dice por qué se cierra: el juego nuevo lo trata como un corte y lo reintenta igual."""
    monkeypatch.setattr(nucleo, "FUNCIONES", FUNCIONES_170)
    b, p = _preparar(robot, tmp_path)
    puerto = b.puerto
    assert not p.sv_sabe("reconexion")
    total = p.j.dinero + p.j.banco
    # el cierre de la 1.7.0: el mensaje de siempre, sin causa, y corta a las dos décimas
    j = b.srv.jugadores[p.red.id]
    b.hacer(lambda: b.srv._enviar(j, {"t": "cerrado", "motivo": "El servidor se ha cerrado."}))
    e = _espera(robot)
    assert e.causa == "cierre" and "El servidor se ha cerrado" in robot.dicho() and "Voy a intentar volver a entrar yo solo" in robot.dicho()
    b.parar()
    _avanzar(e, robot, 12)
    assert robot.app.pila[-1] is e and e.n >= 2
    b2 = Banco(tmp_path, economia="si", ganancia_hora=3600, saldo_inicial=5000, puerto=puerto)
    try:
        _avanzar(e, robot, 30)
        assert robot.app.pila[-1] is p and "Reconectado" in robot.dicho() and p.j.dinero + p.j.banco == total
        # y si simplemente se cae (el proceso muere, se va la luz), lo mismo
        j2 = b2.srv.jugadores[p.red.id]
        b2.hacer(lambda: b2.srv._cortar(j2))
        e = _espera(robot)
        assert e.causa == "corte"
        _avanzar(e, robot, 12)
        assert robot.app.pila[-1] is p and p.online_activo()
    finally:
        p.sv_salir()
        b2.parar()


def test_un_apagado_de_verdad_y_la_opcion_quitada_vuelven_al_menu_como_siempre(robot, tmp_path):
    b, p = _preparar(robot, tmp_path)
    b.hacer(lambda: b.srv.orden("apagar"))                       # quien lo lleva lo apaga: no va a volver
    assert hasta(lambda: robot.app.partida is None, robot, robot, 8)
    assert "Un administrador ha apagado el servidor. Tu personaje está guardado." in robot.dicho()
    assert not any(isinstance(x, reconexion.Espera) for x in robot.app.pila)
    _fin(b)
    # con la opción quitada, ni un reinicio avisado ni un corte abren la espera
    robot.app.cfg["reconectar"] = False
    b = Banco(tmp_path / "dos")
    p = entrar(robot, b, "Ana")
    _pasar(robot, 10)
    _parar_para(b, "actualizacion", 1)
    assert hasta(lambda: "entra otra vez desde Jugar en un servidor" in robot.dicho(), robot, robot, 6)      # el aviso no promete lo que no va a hacer
    assert hasta(lambda: robot.app.partida is None, robot, robot, 8)
    assert "se reinicia para actualizarse" in robot.dicho().split(" | ")[-1] and "Tu personaje está guardado" in robot.dicho().split(" | ")[-1]
    _fin(b)
    # la opción está en Opciones, Jugar en línea, con su ayuda
    from juego import menus_juego
    menus_juego.opciones(robot.app)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if (o.texto() if callable(o.texto) else o.texto) == "Jugar en línea")
    robot.tecla(pygame.K_RETURN)
    textos = [(o.texto() if callable(o.texto) else o.texto) for o in robot.app.pila[-1].opciones]
    assert textos[0].startswith("En un servidor, esperar y volver a entrar solo") and textos[0].endswith(": no")
    assert textos[1] == "Minutos que se espera como mucho a que vuelva el servidor: 10"
    from juego import config
    assert config.POR_DEFECTO["reconectar"] is True and config.POR_DEFECTO["reconectar_minutos"] == 10


def test_el_grupo_de_mision_se_rehace_solo_si_los_demas_tambien_vuelven(dos, tmp_path):
    a, c = dos
    b = Banco(tmp_path, parada_espera=5)
    puerto = b.puerto
    pa, pc = entrar(a, b, "Ana"), entrar(c, b, "Ciro")
    rc, ra = juntos(pa, pc, a, c)
    pa.red.enviar({"t": "grupo_invitar", "a": rc.id, "mision": "Morosos"})
    assert hasta(lambda: pc.sv["inv_grupo"] is not None, a, c)
    pc.red.enviar({"t": "grupo_resp", "si": True})
    assert hasta(lambda: pa.sv_lidero() and pc.sv["grupo"] == pa.red.id, a, c)
    _parar_para(b, "actualizacion", 0)
    fin = time.time() + 10
    while time.time() < fin and not all(isinstance(r.app.pila[-1], reconexion.Espera) for r in (a, c)):
        ambos(a, c, 2)
        time.sleep(0.02)
    ea, ec = a.app.pila[-1], c.app.pila[-1]
    assert isinstance(ea, reconexion.Espera) and isinstance(ec, reconexion.Espera)
    assert pa.sv_espera["grupo"] == {"lidero": True, "lider": "Ana", "otros": ["Ciro"]} and pc.sv_espera["grupo"]["lider"] == "Ana"
    assert rc.id is None                                         # quien tuviera un menú abierto con Ciro elegido ya no puede mandar nada a nadie
    _fin(b)
    b2 = Banco(tmp_path, puerto=puerto)
    try:
        for _ in range(40):
            if a.app.pila[-1] is pa and c.app.pila[-1] is pc:
                break
            for e, r in ((ea, a), (ec, c)):
                if r.app.pila[-1] is e:
                    e.actualizar(1.0)
        assert a.app.pila[-1] is pa and c.app.pila[-1] is pc
        assert "Ibas en un grupo de misión: lo rehago yo" in a.dicho() and "vuelves a él en cuanto Ana entre y lo rehaga" in c.dicho()
        # quien lo llevaba invita otra vez, por el nombre; el otro acepta sin que nadie toque nada
        assert hasta(lambda: pa.sv_lidero() and pc.sv["grupo"] == pa.red.id and pa.sv["regrupo"] is None, a, c, 10), (pa.sv["grupo"], pc.sv["grupo"])
        assert "Ana rehace el grupo de misión y vuelves a él" in c.dicho() and "El grupo de misión está otra vez completo" in a.dicho()
        assert pc.sv["inv_grupo"] is None
    finally:
        for p in (pa, pc):
            p.sv_salir()
        b2.parar()


def test_si_los_demas_no_vuelven_se_dice_con_claridad_y_lo_del_vehiculo_perdido_tambien(robot, tmp_path):
    b, p = _preparar(robot, tmp_path)
    try:
        # el grupo que no se puede rehacer: pasado el plazo, dice quién falta y qué hacer
        p.sv["regrupo"] = {"lidero": True, "lider": "Ana", "otros": ["Ciro", "Dora"], "hasta": p.t + 1.0, "invitados": set()}
        _pasar(robot, 60)
        assert p.sv["regrupo"] is None and "No se ha podido rehacer del todo el grupo de misión: Ciro y Dora no han vuelto al servidor a tiempo" in robot.dicho()
        # iba de pasajero: al cortarse, se queda a pie, y al volver se le dice
        x, y = p.pos()
        v = p.crear_vehiculo("sedan", x + 3, y, 0, "aparcado")
        p._subir(v, True)
        assert hasta(lambda: getattr(v, "id_red", None) is not None, robot, robot)
        # el vehículo en el que iba, si otro se lo ha llevado mientras el servidor volvía: se queda a pie y se le dice
        p.sv["reenganche"] = {"id": v.id_red, "pedido": True, "t": time.time()}
        p._svm_veh_no({"t": "veh_no", "id": v.id_red, "motivo": "Alguien se te ha adelantado.", "por": "ocupado"})
        assert p.j.veh is None and v not in p.vehiculos and "otro jugador se ha llevado el vehículo en el que ibas" in robot.dicho()
        # con un servidor anterior, que solo lo dice con palabras, se entiende igual; si ya no lo tiene, se da de alta otra vez
        v = p.crear_vehiculo("sedan", x + 3, y, 0, "aparcado")
        p._subir(v, True)
        assert hasta(lambda: getattr(v, "id_red", None) is not None, robot, robot)
        viejo = v.id_red
        p.sv["reenganche"] = {"id": viejo, "pedido": True, "t": time.time()}
        p._svm_veh_no({"t": "veh_no", "id": viejo, "motivo": "Ese vehículo ya no está."})
        assert p.j.veh is v and hasta(lambda: v.id_red not in (None, viejo) and v.red_mio, robot, robot, 6)
    finally:
        p.sv_salir()
        b.parar()


def test_un_juego_anterior_ante_el_cierre_nuevo_y_el_servidor_nuevo_ante_un_juego_anterior(tmp_path):
    """El juego de la 1.7.0, ante cualquier «cerrado», guarda, dice el motivo y vuelve al menú: lo que hace falta es que el
    mensaje siga siendo ese, con un texto que se entienda, y que el servidor le espere el guardado."""
    b = Banco(tmp_path, parada_espera=4)
    viejo = Cli(b, "Víctor")                                     # sin «sabe»: un juego anterior
    viejo.estado()
    _parar_para(b, "actualizacion", 1)
    aviso = viejo.leer("aviso")["texto"]
    assert aviso.startswith("Aviso del servidor: dentro de 1 segundos se reinicia para actualizarse")
    c = viejo.leer("cerrado")
    assert c["t"] == "cerrado" and isinstance(c["motivo"], str) and "Volverá en unos minutos: vuelve a entrar entonces" in c["motivo"]
    # lo que hace el juego de la 1.7.0 al recibirlo: guardar y despedirse. El servidor nuevo lo espera y lo guarda
    viejo.enviar({"t": "guardar", "p": {"jugador": {"dinero": 77, "banco": 0}}, "ya": True})
    viejo.enviar({"t": "adios"})
    _fin(b)
    assert json.loads(_cuenta(tmp_path, "Víctor")["partida"])["jugador"]["dinero"] == 77
    assert not any("No ha llegado a tiempo" in t for t in b.lineas)
    viejo.cerrar()


# ====================================================================== el actualizador
def _carpeta_juego(tmp_path):
    """Una carpeta de juego de mentira, con sus programas (vacíos) y la carpeta donde los servidores dejan su ficha."""
    programa = tmp_path / "Puerto Bravo"
    (programa / "servidor" / "en_marcha").mkdir(parents=True)
    (programa / "servidor" / "datos").mkdir()
    for n in ("PuertoBravo.exe", "EditorMods.exe", "PuertoBravoServidor.exe", "PuertoBravoServidorPanel.exe"):
        (programa / n).write_bytes(b"MZ")
    return programa


def _ficha(programa, pid, tipo="consola", activo=True, sesion=1, args=("servidor.conf",), exe=None):
    exe = exe or str(programa / ("PuertoBravoServidor.exe" if tipo == "consola" else "PuertoBravoServidorPanel.exe"))
    d = {"pid": pid, "tipo": tipo, "exe": exe, "args": list(args), "cwd": str(programa / "servidor"), "datos": str(programa / "servidor" / "datos"),
         "conf": str(programa / "servidor" / "servidor.conf"), "activo": activo, "sesion": sesion, "inicio": 1}
    with open(str(programa / "servidor" / "en_marcha" / ("%d.json" % pid)), "w", encoding="utf-8") as f:
        json.dump(d, f)
    return d


def test_el_actualizador_sabe_que_servidores_hay_abiertos_y_como_estaban(tmp_path):
    programa = _carpeta_juego(tmp_path)
    assert A.servidores_en_marcha(str(programa), vivo=lambda pid, exe: True, sesion=1) == []
    _ficha(programa, 101, "consola")
    _ficha(programa, 102, "panel", activo=False, args=())
    _ficha(programa, 103, "consola")                             # este ya se cerró y dejó su ficha
    _ficha(programa, 104, "consola", sesion=0)                   # este lo arranca un servicio de Windows
    _ficha(programa, 105, "consola", exe=str(tmp_path / "otra" / "PuertoBravoServidor.exe"))      # de otra carpeta: no se toca
    _ficha(programa, 106, "consola", exe=str(programa / "PuertoBravo.exe"))                      # no es un programa del servidor
    (programa / "servidor" / "en_marcha" / "roto.json").write_text("{", encoding="utf-8")
    fichas = A.servidores_en_marcha(str(programa), vivo=lambda pid, exe: pid != 103, sesion=1)
    assert [(f["pid"], f["tipo"], f["activo"], f["servicio"]) for f in fichas] == [(101, "consola", True, False), (102, "panel", False, False), (104, "consola", True, True)]
    assert fichas[0]["args"] == ["servidor.conf"] and fichas[0]["cwd"].endswith("servidor") and fichas[0]["datos"].endswith("datos")
    assert not (programa / "servidor" / "en_marcha" / "103.json").exists()      # la ficha de un proceso que ya no existe se borra
    assert A.texto_servidores(fichas[:1]) == "el servidor en línea"
    assert A.texto_servidores(fichas[:2]) == "el servidor en línea y el panel del servidor en línea, con el servidor parado"
    # con su ficha, un servidor abierto ya no impide actualizar; el editor de mods, sí, y un servidor sin ficha, también
    nueva = tmp_path / "nueva"
    nueva.mkdir()
    (nueva / "PuertoBravo.exe").write_bytes(b"MZ")
    tareas = {"PuertoBravoServidor.exe", "PuertoBravoServidorPanel.exe"}
    assert A.problemas_para_instalar(str(nueva), str(programa), libre=10 ** 12, tareas=tareas, servidores=fichas) == []
    p = A.problemas_para_instalar(str(nueva), str(programa), libre=10 ** 12, tareas=tareas | {"EditorMods.exe"}, servidores=fichas)
    assert len(p) == 1 and "el editor de mods" in p[0] and "servidor" not in p[0]
    p = A.problemas_para_instalar(str(nueva), str(programa), libre=10 ** 12, tareas=tareas, servidores=fichas[:1])
    assert len(p) == 1 and "el panel del servidor en línea" in p[0]


def test_pide_la_parada_dejando_la_orden_y_apunta_lo_que_habia(tmp_path):
    programa = _carpeta_juego(tmp_path)
    _ficha(programa, 101, "consola")
    _ficha(programa, 102, "panel", args=())
    fichas = A.servidores_en_marcha(str(programa), vivo=lambda pid, exe: True, sesion=1)
    trabajo = tmp_path / "trabajo"
    nota = A.pedir_parada_servidores(fichas, trabajo=str(trabajo))
    assert os.path.basename(nota) == A.NOTA_SERVIDORES and os.path.dirname(nota) == str(trabajo)
    apuntado = json.load(open(nota, encoding="utf-8"))
    assert [s["pid"] for s in apuntado["servidores"]] == [101, 102] and apuntado["servidores"][0]["args"] == ["servidor.conf"]
    orden = programa / "servidor" / "datos" / A.ORDEN_SERVIDOR
    assert A.ORDEN_SERVIDOR == nucleo.ARCHIVO_ORDEN and orden.read_text(encoding="utf-8").split()[0] == "actualizar"
    # si a alguno no se le puede dejar la orden, no se le deja a ninguno ni queda nota: no se para medio servidor
    orden.unlink()
    os.remove(nota)
    with pytest.raises(A.ErrorActualizacion) as e:
        A.pedir_parada_servidores(fichas + [dict(fichas[0], datos=str(tmp_path / "no_existe"))], trabajo=str(trabajo))
    assert "Ciérralo tú" in str(e.value) and not orden.exists() and not os.path.exists(nota)


def test_vuelve_a_arrancar_lo_que_habia_igual_que_estaba_y_lo_apunta_en_el_registro(tmp_path):
    programa = _carpeta_juego(tmp_path)
    fichas = [dict(_ficha(programa, 101, "consola"), servicio=False),
              dict(_ficha(programa, 102, "panel", activo=True, args=()), servicio=False),
              dict(_ficha(programa, 103, "panel", activo=False, args=("otro.conf", "--arrancar")), servicio=False),
              dict(_ficha(programa, 104, "consola", sesion=0), servicio=True),
              dict(_ficha(programa, 105, "consola"), servicio=False),                                   # no llegó a cerrarse
              dict(_ficha(programa, 106, "consola", exe=str(tmp_path / "ajeno" / "PuertoBravoServidor.exe")), servicio=False),
              dict(_ficha(programa, 107, "consola", exe=str(programa / "cmd.exe")), servicio=False)]    # no es un programa del servidor
    trabajo = tmp_path / "trabajo"
    trabajo.mkdir()
    nota = str(trabajo / A.NOTA_SERVIDORES)
    with open(nota, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "servidores": fichas}, f)
    lanzados = []
    registro = programa / "data" / "logs" / "actualizacion.log"
    registro.parent.mkdir(parents=True)
    registro.write_text("Instalador de Puerto Bravo. Actualizacion a la version 9.\nEMPIEZA\nTERMINADA bien\n", encoding="utf-8")
    hecho = A.relanzar_servidores(nota, programa=str(programa), lanzar=lambda orden, cwd, tipo: lanzados.append((orden, cwd, tipo)),
                                  vivo=lambda pid, exe: pid == 105)
    serv = str(programa / "servidor")
    assert lanzados == [([str(programa / "PuertoBravoServidor.exe"), "servidor.conf"], serv, "consola"),
                        ([str(programa / "PuertoBravoServidorPanel.exe"), "--arrancar"], serv, "panel"),      # su servidor estaba en marcha: vuelve solo
                        ([str(programa / "PuertoBravoServidorPanel.exe"), "otro.conf"], serv, "panel")]       # estaba parado: se abre parado
    assert hecho == [("consola", True, ""), ("panel", True, ""), ("panel", True, "parado"), ("consola", False, "servicio"), ("consola", False, "sigue_abierto"),
                     ("consola", False, "ajeno"), ("desconocido", False, "ajeno")]
    assert not os.path.exists(nota)
    texto = registro.read_text(encoding="utf-8")
    assert "SERVIDOR relanzado tipo=consola" in texto and "SERVIDOR sin_relanzar tipo=consola motivo=servicio" in texto
    assert texto.count("SERVIDOR relanzado tipo=panel\n") == 1 and "SERVIDOR relanzado tipo=panel estado=parado\n" in texto
    assert str(tmp_path) not in texto                            # ni una ruta: el registro se puede enviar
    r = A.leer_registro_instalador(str(registro))
    assert r["bien"] is True and r["relanzados"] == ["consola", "panel", "panel"] and ("consola", "servicio") in r["sin_relanzar"]
    dicho = A.texto_relanzados(r)
    assert "han vuelto a arrancar solo" in dicho and "un servicio o una tarea programada de Windows" in dicho and "no llegó a cerrarse" in dicho
    assert A.texto_relanzados(A.leer_registro_instalador(str(tmp_path / "no_hay.log"))) == ""
    # si el instalador falla, el servidor se vuelve a arrancar igual: el relanzado no depende de cómo haya ido
    registro.write_text("EMPIEZA\nFALLO paso=copiar_nueva codigo=8 motivo=copia\nTERMINADA mal\n", encoding="utf-8")
    with open(nota, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "servidores": fichas[:1]}, f)
    del lanzados[:]
    A.relanzar_servidores(nota, programa=str(programa), lanzar=lambda orden, cwd, tipo: lanzados.append(tipo), vivo=lambda pid, exe: False)
    r = A.leer_registro_instalador(str(registro))
    assert lanzados == ["consola"] and r["bien"] is False and r["relanzados"] == ["consola"] and r["paso"] == "copiar_nueva"
    # una nota que no existe o está rota no hace nada ni falla; y si el programa no se puede abrir, queda dicho
    assert A.relanzar_servidores(str(trabajo / "no_hay.json"), programa=str(programa), lanzar=None, vivo=lambda pid, exe: False) == []
    with open(nota, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "servidores": fichas[:1]}, f)

    def falla(orden, cwd, tipo):
        raise OSError("no se puede")
    assert A.relanzar_servidores(nota, programa=str(programa), lanzar=falla, vivo=lambda pid, exe: False) == [("consola", False, "error_OSError")]
    assert "ábrelo tú" in A.texto_relanzados(A.leer_registro_instalador(str(registro)))


def test_el_instalador_vuelve_a_arrancar_el_servidor_tanto_si_va_bien_como_si_falla(tmp_path):
    nueva = tmp_path / "act" / "nueva"
    nueva.mkdir(parents=True)
    bat = A.escribir_instalador(str(nueva), programa=str(tmp_path / "juego"), pid=4321, version="9.9.9")
    lineas = open(bat, encoding="utf-8").read().splitlines()
    relanzar = 'if exist "%NOTA%" start "" /wait "%APP%\\PuertoBravo.exe" --relanzar-servidores "%NOTA%"'
    assert lineas.count(relanzar) == 2
    assert any(l.startswith('set "NOTA=') and l.endswith(A.NOTA_SERVIDORES + '"') for l in lineas)
    bien, mal = lineas.index('start "" "%APP%\\PuertoBravo.exe" --tras-actualizar'), lineas.index('start "" "%APP%\\PuertoBravo.exe" --actualizacion-fallida')
    assert lineas[bien - 1] == relanzar and lineas[mal - 1] == relanzar      # antes de abrir el juego, en los dos finales
    assert lineas.index(":abrir") < mal and lineas.index(":fallo") < mal    # también cuando el juego o el servidor no llegan a cerrarse
    # sigue esperando a que el servidor y el panel se cierren antes de copiar nada
    assert any("PuertoBravoServidor.exe" in l and "tasklist" in l for l in lineas) and any("PuertoBravoServidorPanel.exe" in l for l in lineas)
    # el juego atiende esa llamada antes de abrir ventana, y no cuenta como «ya abierto»
    with open(os.path.join(RAIZ, "main.py"), encoding="utf-8") as f:
        principal = f.read()
    assert principal.index('"--relanzar-servidores"') < principal.index("if ya_abierto():") and A.ARG_RELANZAR == "--relanzar-servidores"


def test_el_juego_llamado_para_relanzar_no_abre_nada_y_termina(tmp_path):
    nota = tmp_path / "servidores_abiertos.json"
    nota.write_text(json.dumps({"version": 1, "servidores": []}), encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "main.py"), "--relanzar-servidores", str(nota)], cwd=RAIZ, timeout=120,
                       capture_output=True, env=dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy"))
    assert r.returncode == 0 and not nota.exists()


def _instalar_con(app, tmp_path, fichas, problemas=()):
    bat = tmp_path / "actualizacion" / "instalar_actualizacion.bat"
    bat.parent.mkdir(parents=True, exist_ok=True)
    bat.write_text("rem", encoding="utf-8")
    pedidas = []
    app.act_servidores = lambda: list(fichas)
    app.act_parar_servidores = lambda f: pedidas.append([x["pid"] for x in f])
    app.act_comprobar = lambda carpeta: list(problemas)
    app.act_version = "9.9.9"
    app.act_lista = None
    return str(bat), pedidas


def test_actualizar_con_un_servidor_abierto_lo_explica_pide_permiso_y_lo_para(robot, tmp_path):
    app = robot.app
    programa = _carpeta_juego(tmp_path)
    fichas = [dict(_ficha(programa, 101, "consola"), servicio=False)]
    bat, pedidas = _instalar_con(app, tmp_path, fichas)
    menus_actualizar._instalar(app, bat)
    m = app.pila[-1]
    assert isinstance(m, Menu) and m.titulo.startswith("Tienes abierto el servidor en línea") and app.activo and pedidas == []
    ayuda = m.opciones[0].ayuda
    for trozo in ("Se avisa a los jugadores", "cuenta atrás", "vuelve a arrancar solo", "vuelven a entrar solos", "Si la actualización fallara", "actualizacion punto log"):
        assert trozo in ayuda, trozo
    assert "servicio" not in ayuda
    # «Ahora no»: no se toca nada y la descarga se conserva
    m.i = 1
    robot.tecla(pygame.K_RETURN)
    assert pedidas == [] and app.activo and app.act_lista == (bat, "9.9.9") and "No se toca nada" in robot.dicho()
    # se acepta: se deja la orden al servidor, se dice lo que va a pasar y el juego se cierra para actualizarse
    menus_actualizar._instalar(app, bat)
    app.pila[-1].i = 0
    robot.tecla(pygame.K_RETURN)
    assert pedidas == [[101]] and not app.activo
    dicho = robot.dicho().split(" | ")[-1]
    assert "El servidor en línea avisa a los jugadores y se cierra" in dicho and "el servidor vuelve a arrancar con él" in dicho


def test_actualizar_con_un_servidor_montado_como_servicio_lo_avisa_y_los_demas_casos(robot, tmp_path):
    app = robot.app
    programa = _carpeta_juego(tmp_path)
    servicio = [dict(_ficha(programa, 104, "consola", sesion=0), servicio=True)]
    bat, pedidas = _instalar_con(app, tmp_path, servicio)
    menus_actualizar._instalar(app, bat)
    assert "un servicio o una tarea programada de Windows" in app.pila[-1].opciones[0].ayuda and "tendrás que arrancarlo" in app.pila[-1].opciones[0].ayuda
    robot.tecla(pygame.K_ESCAPE)
    # si hay además otro problema (el editor abierto), se dice eso primero y no se para el servidor
    bat, pedidas = _instalar_con(app, tmp_path, servicio, problemas=["Está abierto el editor de mods. Ciérralo antes de actualizar."])
    menus_actualizar._instalar(app, bat)
    assert pedidas == [] and app.activo and "Todavía no se puede instalar" in robot.dicho() and len(app.pila) == 1      # ni pregunta por el servidor
    # si no se le puede dejar la orden al servidor, se dice y no se cierra el juego
    bat, pedidas = _instalar_con(app, tmp_path, servicio)

    def no_puede(fichas):
        raise A.ErrorActualizacion("No se pudo dejar al servidor en línea la orden de cerrarse. Ciérralo tú y vuelve a intentarlo.")
    app.act_parar_servidores = no_puede
    menus_actualizar._instalar(app, bat, confirmado=True)
    assert app.activo and app.act_lista == (bat, "9.9.9") and "Ciérralo tú y vuelve a intentarlo. La descarga no se pierde." in robot.dicho()
    # sin ningún servidor abierto, como siempre: ni pregunta ni menciona servidores
    bat, pedidas = _instalar_con(app, tmp_path, [])
    menus_actualizar._instalar(app, bat)
    assert not app.activo and pedidas == [] and robot.dicho().split(" | ")[-1] == "Todo listo. El juego se cierra, se actualiza y vuelve a abrirse solo en unos segundos."


# ====================================================================== la documentación y el sonido
def test_el_sonido_de_espera_esta_en_todos_los_packs_y_todo_esta_documentado():
    from juego import ayuda, catalogo_sonidos, sintesis
    assert catalogo_sonidos.describir("espera_servidor") != "Sonido del juego." and "dos notas" in catalogo_sonidos.describir("espera_servidor").lower()
    assert any(s[0] == "espera_servidor" for s in ayuda.SONIDOS)
    assert "espera_servidor" in sintesis.generar()
    for pack in ("realista", "alternativo", "retro", "envolvente"):
        assert glob.glob(os.path.join(RAIZ, "data", "sonidos", pack, "espera_servidor.*")), pack
    docs = os.path.join(RAIZ, "data", "docs")
    with open(os.path.join(docs, "manual.html"), encoding="utf-8") as f:
        manual = f.read()
    for trozo in ("Si el servidor se reinicia o se corta la conexión", "pantalla de espera", "Jugar en línea", "Si tienes un servidor abierto", "vuelve a arrancar solo"):
        assert trozo in manual, trozo
    with open(os.path.join(docs, "servidor.html"), encoding="utf-8") as f:
        guia = f.read()
    for trozo in ("<code>parada_aviso</code>", "<code>parada_espera</code>", "<code>actualizar</code>", "<code>reiniciar</code>", "--actualizar", "parar.txt",
                  "código 75", "Actualizar el servidor", "esperan y vuelven a entrar solos"):
        assert trozo in guia, trozo
    with open(os.path.join(RAIZ, "servidor", "despliegue", "LEEME_otros_sistemas.txt"), encoding="utf-8") as f:
        leeme = f.read()
    assert "--actualizar" in leeme and "parar.txt" in leeme and "75" in leeme
    with open(os.path.join(RAIZ, "servidor", "despliegue", "LEEME_servidor.txt"), encoding="utf-8") as f:
        assert "vuelve a arrancar solo" in f.read()
    with open(os.path.join(RAIZ, "README.md"), encoding="utf-8") as f:
        readme = f.read()
    for trozo in ("reconexion", "`parada`", "en_marcha", "--relanzar-servidores", "parar.txt"):
        assert trozo in readme, trozo


# ====================================================================== con mando
def _boton(md, b):
    md.boton(b, True)
    md.boton(b, False)


def test_la_pantalla_de_espera_se_maneja_con_el_mando_y_dice_sus_botones(robot, tmp_path):
    app = robot.app
    md = app.mando
    md.simulado, md.tipo = True, "ps"
    b, p = _preparar(robot, tmp_path)
    _parar_para(b, "actualizacion", 0)
    e = _espera(robot)
    _fin(b)
    assert md.contexto() == "pantalla"
    entrada = next(t for t in reversed(app.voz.registro) if "El servidor se está actualizando" in t)
    assert "El botón Equis dice cómo va" in entrada and "El botón Triángulo lo explica" in entrada and "El botón Círculo deja de esperar" in entrada
    assert "Escape" not in entrada and "F1" not in entrada
    _avanzar(e, robot, 8)
    # A o Equis repite cómo va; X o Cuadrado, también
    for boton in ("a", "x"):
        del app.voz.registro[:]
        _boton(md, boton)
        assert "Llevas esperando" in robot.dicho() and "El botón Círculo deja de esperar" in robot.dicho() and app.pila[-1] is e
    # Y o Triángulo, y el botón Share, explican la pantalla
    for boton in ("y", "back"):
        del app.voz.registro[:]
        _boton(md, boton)
        assert "Pantalla de espera del servidor" in robot.dicho() and "Con mando: A o Equis repite cómo va, B o Círculo deja de esperar" in robot.dicho()
    assert any("pantalla de espera de un servidor" in t for t in md.lineas_ayuda())
    # con un mando de Xbox, los nombres son los suyos
    md.tipo = "xbox"
    del app.voz.registro[:]
    _boton(md, "a")
    assert "El botón B deja de esperar" in robot.dicho()
    # B o Círculo deja de esperar y sale al menú principal
    _boton(md, "b")
    assert app.partida is None and isinstance(app.pila[-1], Menu) and "Dejas de esperar" in robot.dicho()


def test_con_mando_el_aviso_de_version_y_la_confirmacion_de_actualizar_con_el_servidor_abierto(robot, tmp_path):
    app = robot.app
    md = app.mando
    md.simulado, md.tipo = True, "xbox"
    # la pantalla de espera, cuando el servidor vuelve pidiendo otra versión: dice el botón que busca la actualización y el que sale
    b, p = _preparar(robot, tmp_path)
    puerto = b.puerto
    _parar_para(b, "actualizacion", 0)
    e = _espera(robot)
    _fin(b)
    b2 = Banco(tmp_path, puerto=puerto, version_minima="9.9.9")
    try:
        _avanzar(e, robot, 30, lambda: e.estado == "version")
        dicho = robot.dicho().split(" | ")[-1]
        assert "Pulsa el botón A para buscar la actualización" in dicho and "o el botón B para salir al menú principal" in dicho
        _boton(md, "start")                                      # el botón Menú también sale
        assert app.partida is None
    finally:
        b2.parar()
    # la pregunta de actualizar con el servidor abierto es un menú: cruceta, A para aceptar, B para volver, Y para la explicación
    programa = _carpeta_juego(tmp_path)
    bat, pedidas = _instalar_con(app, tmp_path, [dict(_ficha(programa, 101, "consola"), servicio=False)])
    menus_actualizar._instalar(app, bat)
    m = app.pila[-1]
    assert isinstance(m, Menu) and md.contexto() == "menu" and m.i == 0
    del app.voz.registro[:]
    _boton(md, "y")
    assert "Se avisa a los jugadores" in robot.dicho() and "vuelve a arrancar solo" in robot.dicho()
    _boton(md, "abajo")
    assert m.i == 1
    _boton(md, "b")                                              # volver: no se toca nada
    assert app.pila[-1] is not m and pedidas == [] and app.activo and app.act_lista == (bat, "9.9.9")      # y la descarga se conserva
    menus_actualizar._instalar(app, bat)
    _boton(md, "a")                                              # aceptar: se pide la parada y el juego se cierra para actualizarse
    assert pedidas == [[101]] and not app.activo


# ====================================================================== el instalador y los datos vivos del servidor
def _arbol(raiz, archivos):
    for relativa, datos in archivos.items():
        ruta = os.path.join(str(raiz), *relativa.split("/"))
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "wb") as f:
            f.write(datos)


def _leer(raiz, relativa):
    with open(os.path.join(str(raiz), *relativa.split("/")), "rb") as f:
        return f.read()


def _todo(raiz):
    """Los archivos que hay bajo una carpeta, con la ruta relativa y barras normales."""
    return {os.path.relpath(os.path.join(base, n), str(raiz)).replace(os.sep, "/") for base, _, nombres in os.walk(str(raiz)) for n in nombres}


def _juego_con_servidor(tmp_path):
    """Un juego «instalado» con un servidor en línea que ya ha funcionado, y una versión nueva ya extraída. El dueño tiene
    la carpeta de datos de serie y otras dos puestas a su manera: una dentro de la carpeta servidor y otra junto al juego."""
    programa = tmp_path / "Puerto Bravo ñ"
    nueva = programa / "data" / "actualizacion" / "nueva"
    _arbol(programa, {
        "PuertoBravo.exe": b"viejo", "PuertoBravoServidor.exe": b"servidor viejo", "EditorMods.exe": b"editor viejo", "lib/juego/app.pyc": b"v1", "share/x.txt": b"s1",
        "data/datos/ciudad.pbd": b"datos v1", "data/docs/manual.html": b"manual v1", "data/mods/mio.pbm": b"mi mod", "data/partidas/mia.pbs": b"mi partida",
        "data/sonidos/por_defecto/paso.flac": b"sonido v1", "data/radio/bravo.mp3": b"radio v1", "data/musica/menu/tema.ogg": b"musica v1",
        "data/radio/mi_emisora.mp3": b"mi emisora", "data/radio/mi_musica/cancion.mp3": b"mi cancion", "data/musica/menu/la_mia.ogg": b"mi musica",
        "servidor/LEEME.txt": b"leeme v1", "servidor/Panel del servidor.bat": b"bat v1", "servidor/otros_sistemas/arrancar.sh": b"sh v1",
        "servidor/servidor.conf": b"puerto = 1", "servidor/datos_servidor/puertobravo.db": b"base antes", "servidor/datos_servidor/copias/copia.zip": b"una copia",
        "servidor/datos_servidor/registro.txt": b"registro", "servidor/en_marcha/111.json": b"{}",
        "servidor/mis datos/puertobravo.db": b"base antes", "servidor/otro.conf": b"datos = mis datos",
        "datos_fuera/puertobravo.db": b"base antes", "mi_servidor.conf": b"datos = datos_fuera"})
    _arbol(nueva, {
        "PuertoBravo.exe": b"nuevo", "PuertoBravoServidor.exe": b"servidor nuevo", "EditorMods.exe": b"editor nuevo", "lib/juego/app.pyc": b"v2", "share/x.txt": b"s2",
        "data/datos/ciudad.pbd": b"datos v2", "data/docs/manual.html": b"manual v2", "data/sonidos/por_defecto/paso.flac": b"sonido v2",
        "data/sonidos/por_defecto/estreno.flac": b"sonido nuevo", "data/radio/bravo.mp3": b"radio v2", "data/musica/menu/tema.ogg": b"musica v2",
        "servidor/LEEME.txt": b"leeme v2", "servidor/Panel del servidor.bat": b"bat v2", "servidor/otros_sistemas/arrancar.sh": b"sh v2",
        # una versión no trae nada de esto; si lo trajera, tampoco se copia
        "servidor/servidor.conf": b"de la version", "servidor/datos_servidor/puertobravo.db": b"de la version", "servidor/en_marcha/999.json": b"de la version"})
    return programa, nueva


VIVO = ("servidor/datos_servidor/puertobravo.db", "servidor/mis datos/puertobravo.db", "datos_fuera/puertobravo.db")
LO_MIO = {"data/partidas/mia.pbs": b"mi partida", "data/mods/mio.pbm": b"mi mod", "data/radio/mi_emisora.mp3": b"mi emisora",
          "data/radio/mi_musica/cancion.mp3": b"mi cancion", "data/musica/menu/la_mia.ogg": b"mi musica", "servidor/servidor.conf": b"puerto = 1",
          "servidor/otro.conf": b"datos = mis datos", "mi_servidor.conf": b"datos = datos_fuera", "servidor/datos_servidor/copias/copia.zip": b"una copia",
          "servidor/datos_servidor/registro.txt": b"registro"}


def _sin_programas_del_juego():
    if sys.platform != "win32":
        pytest.skip("el instalador es de Windows")
    abiertos = [exe for exe in list(A.OTROS_PROGRAMAS) + [A.EJECUTABLE] if exe.lower() in A._tareas()]
    if abiertos:
        pytest.skip("hay un programa del juego abierto en este equipo y el instalador lo esperaría: " + ", ".join(abiertos))


def _correr_instalador(bat, tras_la_copia=(), entorno=None):
    """Ejecuta el instalador de verdad sobre carpetas de pega, sin que abra el juego al terminar. ``tras_la_copia`` son
    líneas que se cuelan justo después de la copia de seguridad: lo que hace el servidor al cerrarse mientras se instala."""
    lineas = []
    with open(bat, encoding="utf-8") as f:
        for l in f.read().splitlines():
            lineas.append(('>>"%REG%" echo ABRIRIA ' + l.split('"')[-1].strip()) if l.startswith('start ""') else l)
            if l == '>>"%REG%" echo RESULTADO copia_seguridad codigo=%RC%':
                lineas += list(tras_la_copia)
    with open(bat, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    subprocess.run([A.de_windows("cmd.exe"), "/c", bat], cwd=os.path.dirname(bat), timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=entorno)


# Lo que hace un servidor al cerrarse para actualizar: guarda su base de datos y borra su ficha. Aquí pasa después de la
# copia de seguridad, que es el caso malo: si la instalación falla, restaurar no puede devolver la base a como estaba antes.
EL_SERVIDOR_GUARDA = tuple('>"%APP%\\' + v.replace("/", "\\") + '" echo guardado al cerrar' for v in VIVO) + ('del "%APP%\\servidor\\en_marcha\\111.json"',)


def test_la_copia_de_seguridad_es_solo_de_programa(tmp_path):
    programa, nueva = _juego_con_servidor(tmp_path)
    assert A.plan_copia(str(nueva)) == [("", ["EditorMods.exe", "PuertoBravo.exe", "PuertoBravoServidor.exe"]), ("lib", None),
                                        ("servidor", ["LEEME.txt", "Panel del servidor.bat"]), (os.path.join("servidor", "otros_sistemas"), None), ("share", None)]
    assert A.plan_copia(str(tmp_path / "no_hay")) == []
    bat = A.escribir_instalador(str(nueva), str(programa), pid=999999, version="99.0.0")
    texto = open(bat, encoding="utf-8").read()
    copia = texto.split("PASO copia_seguridad")[1].split("RESULTADO copia_seguridad")[0]
    for vivo in ("datos_servidor", "en_marcha", "servidor.conf", "mis datos", "datos_fuera", "otro.conf", "sonidos", "musica", "radio", "phonon", "partidas", "config"):
        assert vivo not in copia, vivo
    assert '"%APP%\\servidor" "%COPIA%\\servidor" "LEEME.txt" "Panel del servidor.bat" /r:2' in copia and '"%APP%\\servidor" "%COPIA%\\servidor" /e' not in copia
    assert '"%APP%" "%COPIA%" /e' not in texto                       # nunca la carpeta del juego entera
    principal = next(l for l in texto.splitlines() if '"%NUEVA%" "%APP%"' in l)
    assert "/xd" in principal and {"en_marcha", "datos_servidor"} <= set(principal.split("/xd")[1].split("/xf")[0].split())
    assert principal.split("/xf")[1].split()[:2] == ["servidor.conf", "parar.txt"]
    # el sitio que hace falta se calcula con lo que de verdad se guarda: los datos del servidor no cuentan, ocupen lo que ocupen
    guardado = sum(len(b) for b in (b"viejo", b"servidor viejo", b"editor viejo", b"v1", b"s1", b"leeme v1", b"bat v1", b"sh v1", b"datos v1", b"manual v1", b"mi mod"))
    assert A.tamano_copia(str(programa), str(nueva)) == guardado
    antes = A.tamano_copia(str(programa))                            # antes de descargar, sin saber qué trae la versión
    _arbol(programa, {"servidor/datos_servidor/copias/enorme.zip": b"x" * 500000, "servidor/mis datos/enorme.bin": b"x" * 500000})
    assert A.tamano_copia(str(programa), str(nueva)) == guardado and A.tamano_copia(str(programa)) == antes
    assert A.espacio_para_instalar(str(nueva), str(programa)) < 400000 + A.MARGEN_DISCO


def test_si_la_instalacion_falla_no_se_devuelve_la_base_de_datos_del_servidor_a_como_estaba_antes(tmp_path):
    _sin_programas_del_juego()
    import ctypes
    programa, nueva = _juego_con_servidor(tmp_path)
    k = ctypes.windll.kernel32
    k.CreateFileW.restype = ctypes.c_void_p
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    asa = k.CreateFileW(str(programa / "EditorMods.exe"), 0x80000000, 0, None, 3, 0, None)      # abierto sin compartir: no se puede sustituir
    assert asa not in (None, ctypes.c_void_p(-1).value)
    try:
        _correr_instalador(A.escribir_instalador(str(nueva), str(programa), pid=999999, version="99.0.0"), EL_SERVIDOR_GUARDA)
    finally:
        k.CloseHandle(asa)
    r = A.leer_registro_instalador(A.ruta_registro_instalador(str(programa)))
    registro = open(A.ruta_registro_instalador(str(programa)), encoding="utf-8", errors="replace").read()
    assert r["bien"] is False and r["paso"] == "copiar_nueva" and "RESULTADO restaurar" in registro, registro
    # lo que el servidor guardó al cerrarse sigue ahí, en las tres carpetas de datos; y la ficha que borró no ha vuelto
    for vivo in VIVO:
        assert _leer(programa, vivo).startswith(b"guardado al cerrar"), vivo
    assert not (programa / "servidor" / "en_marcha" / "111.json").exists() and not (programa / "servidor" / "en_marcha" / "999.json").exists()
    for ruta, contenido in LO_MIO.items():
        assert _leer(programa, ruta) == contenido, ruta
    # el programa sí ha vuelto a la versión anterior, también el del servidor
    for ruta, contenido in {"PuertoBravo.exe": b"viejo", "PuertoBravoServidor.exe": b"servidor viejo", "EditorMods.exe": b"editor viejo", "lib/juego/app.pyc": b"v1",
                            "share/x.txt": b"s1", "servidor/LEEME.txt": b"leeme v1", "servidor/Panel del servidor.bat": b"bat v1",
                            "servidor/otros_sistemas/arrancar.sh": b"sh v1", "data/datos/ciudad.pbd": b"datos v1", "data/docs/manual.html": b"manual v1"}.items():
        assert _leer(programa, ruta) == contenido, ruta
    # en la copia de seguridad no ha entrado nada más que programa (el editor estaba en uso y no se pudo copiar)
    assert _todo(programa / "data" / "actualizacion" / "anterior") == {
        "PuertoBravo.exe", "PuertoBravoServidor.exe", "lib/juego/app.pyc", "share/x.txt", "servidor/LEEME.txt", "servidor/Panel del servidor.bat",
        "servidor/otros_sistemas/arrancar.sh", "data/datos/ciudad.pbd", "data/docs/manual.html", "data/mods/mio.pbm"}
    # Lo que no se restaura, y es a propósito: los sonidos, la música y la radio de serie se quedan con lo que llegó a copiarse
    # de la versión nueva. Son audio que se carga por su nombre: la versión anterior funciona con ellos. Lo del jugador, intacto.
    assert _leer(programa, "data/sonidos/por_defecto/paso.flac") == b"sonido v2" and _leer(programa, "data/radio/bravo.mp3") == b"radio v2"
    assert _leer(programa, "data/musica/menu/tema.ogg") == b"musica v2"


def test_una_instalacion_que_sale_bien_no_pisa_ni_borra_nada_del_servidor(tmp_path):
    _sin_programas_del_juego()
    programa, nueva = _juego_con_servidor(tmp_path)
    antes = _todo(programa / "servidor") | {"datos_fuera/puertobravo.db", "mi_servidor.conf"}
    _correr_instalador(A.escribir_instalador(str(nueva), str(programa), pid=999999, version="99.0.0"), EL_SERVIDOR_GUARDA)
    r = A.leer_registro_instalador(A.ruta_registro_instalador(str(programa)))
    assert r["bien"] is True and not r["error"], open(A.ruta_registro_instalador(str(programa)), encoding="utf-8", errors="replace").read()
    for vivo in VIVO:
        assert _leer(programa, vivo).startswith(b"guardado al cerrar"), vivo
    for ruta, contenido in LO_MIO.items():
        assert _leer(programa, ruta) == contenido, ruta
    assert _todo(programa / "servidor") == antes - {"datos_fuera/puertobravo.db", "mi_servidor.conf", "en_marcha/111.json"}      # ni sobra ni falta nada
    assert _leer(programa, "datos_fuera/puertobravo.db").startswith(b"guardado") and (programa / "mi_servidor.conf").exists()
    for ruta, contenido in {"PuertoBravo.exe": b"nuevo", "PuertoBravoServidor.exe": b"servidor nuevo", "lib/juego/app.pyc": b"v2", "servidor/LEEME.txt": b"leeme v2",
                            "servidor/Panel del servidor.bat": b"bat v2", "servidor/otros_sistemas/arrancar.sh": b"sh v2", "data/datos/ciudad.pbd": b"datos v2",
                            "data/sonidos/por_defecto/estreno.flac": b"sonido nuevo"}.items():
        assert _leer(programa, ruta) == contenido, ruta
    assert not (programa / "data" / "actualizacion" / "anterior").exists() and not nueva.exists()


def test_una_version_no_trae_datos_de_servidor_y_no_se_instala_encima_de_los_que_estan_en_zona_de_programa(tmp_path):
    import io
    import zipfile
    paquete = tmp_path / "PuertoBravo.zip"
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for nombre in ("PuertoBravo.exe", "servidor/LEEME.txt", "servidor/servidor.conf.ejemplo", "servidor/servidor.conf", "servidor/parar.txt",
                       "servidor/datos_servidor/puertobravo.db", "servidor/en_marcha/1.json", "servidor/otros_sistemas/arrancar.sh"):
            z.writestr(nombre, b"x")
    paquete.write_bytes(b.getvalue())
    raiz = A.extraer(str(paquete), str(tmp_path / "extraida"))
    assert _todo(raiz) == {"PuertoBravo.exe", "servidor/LEEME.txt", "servidor/servidor.conf.ejemplo", "servidor/otros_sistemas/arrancar.sh"}
    # Las carpetas de datos que el dueño ponga donde quiera no se tocan. La única manera de perderlas sería tenerlas dentro de
    # una carpeta que la versión trae y sustituye: entonces el juego lo dice y no actualiza.
    programa, nueva = _juego_con_servidor(tmp_path)
    ficha = lambda *partes: dict(_ficha(programa, 101, "consola"), datos=os.path.join(str(programa), *partes), servicio=False)
    for partes in (("servidor", "datos_servidor"), ("servidor", "mis datos"), ("datos_fuera",), ("data", "mis_datos_del_servidor"), ("servidor",)):
        assert A.datos_en_zona_de_programa([ficha(*partes)], str(nueva), str(programa)) == "", partes
    assert A.datos_en_zona_de_programa([dict(ficha(), datos=str(tmp_path / "fuera_del_juego"))], str(nueva), str(programa)) == ""
    assert A.datos_en_zona_de_programa([dict(ficha(), datos="")], str(nueva), str(programa)) == "" and A.datos_en_zona_de_programa([], str(nueva), str(programa)) == ""
    for partes, zona in ((("lib", "mis_datos"), "lib"), (("data", "datos", "srv"), os.path.join("data", "datos")), (("share",), "share"),
                         (("servidor", "otros_sistemas", "datos"), os.path.join("servidor", "otros_sistemas"))):
        assert A.datos_en_zona_de_programa([ficha(*partes)], str(nueva), str(programa)).lower() == zona, partes
    tareas = {"PuertoBravoServidor.exe"}
    assert A.problemas_para_instalar(str(nueva), str(programa), libre=10 ** 12, tareas=tareas, servidores=[ficha("servidor", "mis datos")], copias=1) == []
    p = A.problemas_para_instalar(str(nueva), str(programa), libre=10 ** 12, tareas=tareas, servidores=[ficha("lib", "mis_datos")], copias=1)
    assert len(p) == 1 and "dentro de la carpeta lib" in p[0] and "mueve su carpeta de datos" in p[0]


# ====================================================================== el panel abierto sin haber arrancado nunca el servidor
def test_con_el_panel_abierto_sin_haber_arrancado_nunca_el_servidor_tambien_se_actualiza(tmp_path, monkeypatch):
    from panel_servidor import motor as M_
    monkeypatch.setenv("PUERTOBRAVO_EN_MARCHA", str(tmp_path / "en_marcha"))
    conf, datos = tmp_path / "servidor.conf", tmp_path / "datos_servidor"
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), datos="datos_servidor", puerto=0, interfaz="127.0.0.1", cifrado="no", personajes=0))
    m = M_.Motor(str(conf))
    try:
        with open(m.anotar(), encoding="utf-8") as f:
            ficha = dict(json.load(f), servicio=False)
        assert ficha["tipo"] == "panel" and ficha["activo"] is False and os.path.normcase(ficha["datos"]) == os.path.normcase(str(datos)) and not datos.exists()
        nota = A.pedir_parada_servidores([ficha], trabajo=str(tmp_path / "trabajo"))      # antes: «No encuentro la carpeta de datos de el panel...»
        assert datos.is_dir() and (datos / A.ORDEN_SERVIDOR).read_text(encoding="utf-8").split() == ["actualizar"]
        with open(nota, encoding="utf-8") as f:
            assert json.load(f)["servidores"][0]["activo"] is False
        assert m.orden_pendiente() == "actualizar" and os.listdir(str(datos)) == []      # el panel la ve, la recoge y se cierra
        assert "--arrancar" not in A.orden_de_arranque(ficha)[0]                         # y vuelve parado
    finally:
        enmarcha.quitar()
    # si de verdad no se le puede dejar la orden, se dice bien dicho: «del panel», «del servidor»
    (tmp_path / "estorbo").write_text("x", encoding="utf-8")
    for cambio, que in ((dict(datos=str(tmp_path / "estorbo" / "datos")), "del panel del servidor en línea"), (dict(datos=""), "del panel del servidor en línea"),
                        (dict(tipo="consola", datos=str(tmp_path / "no_existe")), "del servidor en línea")):
        with pytest.raises(A.ErrorActualizacion) as e:
            A.pedir_parada_servidores([dict(ficha, **cambio)], trabajo=str(tmp_path / "trabajo2"))
        assert ("No encuentro la carpeta de datos " + que + " para pedirle que se cierre. Ciérralo tú") in str(e.value) and " de el " not in str(e.value)
    assert not (tmp_path / "no_existe").exists()                     # a un servidor de consola no se le inventa la carpeta


# ====================================================================== el foco, tras actualizar
PANEL_SIN_FOCO = r"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
import wx
from panel_servidor import ventana as V
app = wx.App(False)
wx.HelpProvider.Set(wx.SimpleHelpProvider())
focos, alzadas = [], []
wx.Window.SetFocus = lambda self: focos.append(self.GetName())
wx.Window.Raise = lambda self: alzadas.append(self.GetName())
r = {}
v = V.VentanaPanel(sys.argv[2], hablar=False, sin_foco=True)
r["al_crearla_sin_foco"] = list(focos) + list(alzadas)
v._foco_inicial()                                # sigue sin estar activa: no se toca nada
r["sin_activar"] = [list(focos), v._foco_pendiente]
v.IsActive, v.IsIconized = (lambda: True), (lambda: True)
v._foco_inicial()                                # activa pero minimizada: todavia no
r["minimizada"] = [list(focos), v._foco_pendiente]
v.IsIconized = lambda: False
v._foco_inicial()
v._foco_inicial()
r["al_venir_a_ella"] = [[f == v.estado.GetName() for f in focos], v._foco_pendiente]
del focos[:]
v.reloj.Stop()
v.Destroy()
w = V.VentanaPanel(sys.argv[2], hablar=False)    # abierta a mano, como siempre: el foco va al estado desde el principio
r["a_mano"] = [[f == w.estado.GetName() for f in focos], w._foco_pendiente, alzadas]
w.reloj.Stop()
w.Destroy()
# y al abrir el programa: sin activar si asi lo pide quien lo arranca, y con Show de siempre si no
llamadas = []
class Falsa:
    def __init__(self, ruta, sin_foco=False): llamadas.append(("crear", sin_foco))
    def Show(self): llamadas.append("Show")
    def ShowWithoutActivating(self): llamadas.append("ShowWithoutActivating")
    def IsIconized(self): return False
    def Iconize(self, si): llamadas.append("Iconize")
    def arrancar(self): pass
V.VentanaPanel = Falsa
V.wx = type("W", (), {"App": lambda *a: type("A", (), {"MainLoop": lambda s: None})(), "HelpProvider": wx.HelpProvider, "SimpleHelpProvider": wx.SimpleHelpProvider, "CallAfter": lambda *a: None})
for pedido in (True, False):
    V.abierto_sin_activar = lambda: pedido
    V.ejecutar(sys.argv[2])
r["ejecutar"] = llamadas
print("RESULTADO " + json.dumps(r))
"""


def test_el_panel_que_vuelve_tras_actualizar_no_le_quita_el_foco_al_juego(tmp_path, monkeypatch):
    if sys.platform != "win32":
        pytest.skip("es cosa de Windows")
    # 1. el juego arranca el servidor y el panel minimizados y sin activar, y él se abre el último
    lanzados = []
    monkeypatch.setattr(A.subprocess, "Popen", lambda orden, **mas: lanzados.append((orden, mas)))
    A._lanzar_servidor(["PuertoBravoServidorPanel.exe", "--arrancar"], str(tmp_path), "panel")
    A._lanzar_servidor(["PuertoBravoServidor.exe"], str(tmp_path), "consola")
    monkeypatch.undo()
    for orden, mas in lanzados:
        assert mas["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW and mas["startupinfo"].wShowWindow == 7      # SW_SHOWMINNOACTIVE
    assert lanzados[0][1]["creationflags"] == 0 and lanzados[1][1]["creationflags"] == subprocess.CREATE_NEW_CONSOLE
    nueva = tmp_path / "act" / "nueva"
    nueva.mkdir(parents=True)
    lineas = open(A.escribir_instalador(str(nueva), programa=str(tmp_path / "juego"), pid=1, version="9"), encoding="utf-8").read().splitlines()
    for final in ("--tras-actualizar", "--actualizacion-fallida"):
        k = lineas.index('start "" "%APP%\\PuertoBravo.exe" ' + final)
        assert "--relanzar-servidores" in lineas[k - 1] and "/wait" in lineas[k - 1] and not any(l.startswith("start ") for l in lineas[k + 1:k + 3])
    # 2. el panel sabe, preguntando a Windows, que lo han abierto sin activar
    base = getattr(sys, "_base_executable", None) or sys.executable      # el lanzador del entorno virtual no pasa ese dato al programa de verdad
    orden = [base, "-c", "import sys; sys.path.insert(0, sys.argv[1]); from panel_servidor import abierto_sin_activar; print(abierto_sin_activar())", RAIZ]
    visto = {}
    for modo in (None, 1, 4, 7, 8, 3):
        info = subprocess.STARTUPINFO()
        if modo is not None:
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = modo
        visto[modo] = subprocess.run(orden, capture_output=True, timeout=60, startupinfo=info, creationflags=subprocess.CREATE_NO_WINDOW).stdout.decode().strip()
    assert visto == {None: "False", 1: "False", 4: "True", 7: "True", 8: "True", 3: "False"}
    # 3. y entonces ni pone el foco ni se trae al frente; el foco inicial de siempre se pone cuando su dueño viene a la ventana
    pytest.importorskip("wx")
    conf = tmp_path / "servidor.conf"
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), datos="datos_servidor", puerto=0, interfaz="127.0.0.1", cifrado="no", personajes=0))
    p = subprocess.run([sys.executable, "-c", PANEL_SIN_FOCO, RAIZ, str(conf)], capture_output=True, timeout=120, cwd=str(tmp_path),
                       env=dict(os.environ, PYTHONUTF8="1", PYTHONPATH=RAIZ))
    salida = p.stdout.decode("utf-8", "replace")
    assert "RESULTADO " in salida, salida + p.stderr.decode("utf-8", "replace")
    r = json.loads(salida.split("RESULTADO ", 1)[1])
    assert r["al_crearla_sin_foco"] == [] and r["sin_activar"] == [[], True] and r["minimizada"] == [[], True]
    assert r["al_venir_a_ella"] == [[True], False]                   # una sola vez, y en el estado del servidor
    assert r["a_mano"] == [[True], False, []]                        # abierto a mano no cambia nada: el foco, donde siempre
    assert r["ejecutar"] == [["crear", True], "ShowWithoutActivating", "Iconize", ["crear", False], "Show"]


# ====================================================================== el instalador no depende del PATH
def test_el_instalador_funciona_aunque_el_path_traiga_otro_find(tmp_path):
    _sin_programas_del_juego()
    trampa = tmp_path / "trampa"
    trampa.mkdir()
    for n in ("find", "tasklist", "robocopy", "ping", "chcp"):         # como el find de Git Bash o de Cygwin: se llaman igual y hacen otra cosa
        (trampa / (n + ".cmd")).write_text('@echo %s>>"%%~dp0usado.txt"\r\n@exit /b 0\r\n' % n, encoding="ascii", newline="")
    entorno = dict(os.environ, PATH=str(trampa) + os.pathsep + os.environ.get("PATH", ""))
    cmd = A.de_windows("cmd.exe")
    subprocess.run([cmd, "/c", "find /?"], cwd=str(tmp_path), env=entorno, capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    assert (trampa / "usado.txt").exists(), "la trampa no funciona: esta prueba no probaría nada"
    (trampa / "usado.txt").unlink()
    programa, nueva = _juego_con_servidor(tmp_path)
    t0 = time.time()
    _correr_instalador(A.escribir_instalador(str(nueva), str(programa), pid=999999, version="99.0.0"), entorno=entorno)
    assert not (trampa / "usado.txt").exists()                        # ni una sola vez se ha usado lo que había en el PATH
    r = A.leer_registro_instalador(A.ruta_registro_instalador(str(programa)))
    assert r["bien"] is True and _leer(programa, "PuertoBravo.exe") == b"nuevo" and time.time() - t0 < 60      # y no se ha quedado esperando a nadie


# ====================================================================== cosas menores
def test_con_el_panel_parado_no_se_habla_de_avisar_a_jugadores_que_no_hay(robot, tmp_path):
    app = robot.app
    programa = _carpeta_juego(tmp_path)
    parado = [dict(_ficha(programa, 102, "panel", activo=False, args=()), servicio=False)]
    assert A.sin_servidor_en_marcha(parado) and not A.sin_servidor_en_marcha([]) and not A.sin_servidor_en_marcha([dict(parado[0], activo=True)])
    assert not A.sin_servidor_en_marcha(parado + [dict(_ficha(programa, 101, "consola"), servicio=False)])
    bat, pedidas = _instalar_con(app, tmp_path, parado)
    menus_actualizar._instalar(app, bat)
    m = app.pila[-1]
    assert isinstance(m, Menu) and m.titulo == "Tienes abierto el panel del servidor en línea, con el servidor parado. Para actualizar hay que cerrarlo un momento"
    assert m.opciones[0].texto == "Actualizar ahora: cerrar el panel y volver a abrirlo al terminar" and "No se cierra el panel" in m.opciones[1].ayuda
    ayuda = m.opciones[0].ayuda
    assert "no hay jugadores a los que avisar" in ayuda and "vuelve a abrirse solo" in ayuda and "con el servidor parado, como estaba" in ayuda
    assert "Se avisa" not in ayuda and "cuenta atrás" not in ayuda and "vuelven a entrar" not in ayuda and "actualizacion punto log" in ayuda
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    dicho = robot.dicho().split(" | ")[-1]
    assert pedidas == [[102]] and not app.activo
    assert dicho == "Todo listo. El panel del servidor en línea se cierra. El juego se cierra, se actualiza y vuelve a abrirse solo en unos segundos, y el panel vuelve a abrirse con él."
    # y al volver: el panel ha vuelto, parado; nadie estaba esperando
    registro = tmp_path / "actualizacion.log"
    registro.write_text("EMPIEZA\nTERMINADA bien\nSERVIDOR relanzado tipo=panel estado=parado\n", encoding="utf-8")
    r = A.leer_registro_instalador(str(registro))
    assert r["relanzados"] == ["panel"] and r["parados"] == 1
    assert A.texto_relanzados(r) == "El panel del servidor en línea que tenías abierto ha vuelto a abrirse, con el servidor parado, como estaba."
    # con un servidor en marcha de por medio, se sigue diciendo lo de los jugadores
    registro.write_text("TERMINADA bien\nSERVIDOR relanzado tipo=panel estado=parado\nSERVIDOR relanzado tipo=consola\n", encoding="utf-8")
    assert "los jugadores que estaban esperando volverán a entrar" in A.texto_relanzados(A.leer_registro_instalador(str(registro)))
    registro.write_text("TERMINADA bien\nSERVIDOR relanzado tipo=panel\n", encoding="utf-8")
    assert "los jugadores que estaban esperando volverán a entrar" in A.texto_relanzados(A.leer_registro_instalador(str(registro)))


def test_el_registro_del_instalador_queda_sin_lineas_en_blanco_y_con_sus_letras(tmp_path):
    if sys.platform != "win32":
        pytest.skip("las páginas de códigos son las de Windows")
    # robocopy mezcla dos páginas de códigos en el mismo registro: el error de Windows en la de la consola, y su propio aviso en la de Windows
    ruta = tmp_path / "actualizacion.log"
    ruta.write_bytes(b"Instalador de Puerto Bravo.\r\nPASO copiar_nueva\r\n\r\n"
                     b"2026/11/19 05:15:01 ERROR 32 (0x00000020) Copiando archivo C:\\Juegos\\Puerto Bravo \xa4\\EditorMods.exe\r\n"
                     + "El proceso no tiene acceso al archivo porque está siendo utilizado por otro proceso.".encode("cp850") + b"\r\r\n\r\n"
                     + "ERROR: SE SUPERÓ EL LÍMITE DE REINTENTOS.".encode("cp1252") + b"\r\n\r\n\r\n"
                     b"RESULTADO copiar_nueva codigo=11\r\nFALLO paso=copiar_nueva codigo=11 motivo=copia\r\nPASO restaurar\r\n\r\nRESULTADO restaurar codigo=3\r\nTERMINADA mal\r\n")
    if "ñ".encode("oem", "replace") != b"\xa4" or "Ó".encode("mbcs", "replace") != b"\xd3":
        pytest.skip("este Windows no usa las páginas de códigos del español")
    r = A.leer_registro_instalador(str(ruta))
    assert (r["bien"], r["paso"], r["error"], r["archivo"]) == (False, "copiar_nueva", 32, "EditorMods.exe")
    A.limpiar_registro_instalador(str(ruta))
    limpio = ruta.read_text(encoding="utf-8")
    assert "está siendo utilizado" in limpio and "SE SUPERÓ EL LÍMITE DE REINTENTOS" in limpio and "Copiando archivo EditorMods.exe" in limpio
    assert not any(c in limpio for c in "Ë═\ufffd\xa0") and all(l.strip() for l in limpio.splitlines()) and len(limpio.splitlines()) == 10
    assert A.leer_registro_instalador(str(ruta))["archivo"] == "EditorMods.exe" and "otro programa" in A.motivo_del_fallo(str(ruta))


def test_al_parar_no_queda_ninguna_tarea_a_medias_aunque_el_juego_corte_nada_mas_recibir_el_cierre(tmp_path):
    """Era el «Task was destroyed but it is pending!» de la consola: la conexión de quien cortaba justo al recibir el cierre
    dejaba de contar antes de terminar su despedida, y el servidor se daba por parado con ella a medias."""
    import asyncio
    for vuelta in range(3):
        b = Banco(tmp_path / str(vuelta))
        clientes = [Cli(b, nombre, sabe=["reconexion"]) for nombre in ("Ana", "Blas")]      # con uno solo no pasaba
        for c in clientes:
            c.estado()
        _parar_para(b, "actualizacion", 0)
        for c in clientes:
            assert c.leer("cerrado")["causa"] == "actualizacion"
            c.s.close()                                          # lo que hace el juego: guarda, se despide y corta
        assert _esperar(lambda: b.srv.detenido, 20)
        pendientes = [t for t in asyncio.all_tasks(b.loop) if not t.done()]
        assert pendientes == [] and not b.srv.conexiones, pendientes
        _fin(b)
        assert not any("Error interno" in t or "Task was destroyed" in t for t in b.lineas), b.lineas
