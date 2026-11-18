"""1.7.0: la radio se pausa al bajarte y sigue donde quedó, el reproductor con auriculares, la música de los locales y
las combinaciones de botones del mando."""
import os
import time

import numpy as np
import pygame
import soundfile as sf

from juego import mando as MD
from juego import musica
from juego.audio import Mezclador
from juego.musica import Radio


def _grabar(ruta, minutos, hz=220.0, sr=44100):
    n = sr * 10
    with sf.SoundFile(ruta, "w", samplerate=sr, channels=2, format="OGG", subtype="VORBIS") as f:
        for k in range(int(minutos * 6)):
            t = (np.arange(n) + k * n) / sr
            f.write(np.stack([0.3 * np.sin(2 * np.pi * hz * t)] * 2, axis=1).astype(np.float32))


def _radio(tmp_path, archivos):
    carpeta = str(tmp_path / "radio")
    os.makedirs(os.path.join(carpeta, "mi_musica"))
    for nombre, minutos in archivos:
        _grabar(os.path.join(carpeta, "mi_musica", nombre), minutos)
    m = Mezclador(dispositivo=False)
    r = Radio(m, carpeta)
    r.esperar()
    return m, r, next(k for k, e in enumerate(r.emisoras) if e["id"] == "usuario")


def _cargada(r):
    for _ in range(600):
        r.actualizar(0.02)
        if r.canal is not None and not r.pendiente:
            return True
        time.sleep(0.01)
    return False


# ------------------------------------------------------------------ pausa y reanudación
def test_la_radio_se_pausa_y_sigue_justo_donde_quedo(tmp_path):
    m, r, usuario = _radio(tmp_path, [("programa.ogg", 6)])
    assert r.pausa is True
    r.sintonizar(usuario)
    assert _cargada(r) and r._larga is not None and r._larga.get("base", 0) == 0
    r._t_ini_larga = time.time() - 137.0                        # lleva dos minutos y diecisiete segundos sonando
    r.apagar()
    ruta, pos = r.recuerdo_de("usuario")
    assert ruta.endswith("programa.ogg") and 136.5 <= pos <= 138.5
    time.sleep(0.3)                                              # el tiempo que pasas fuera del vehículo no cuenta
    assert abs(r.recuerdo_de("usuario")[1] - pos) < 0.01
    r.sintonizar(usuario)
    assert _cargada(r)
    assert 136.5 <= r._larga["base"] <= 138.5                    # arranca en ese segundo, no en el minuto entero
    assert r._larga["total"] == int(np.ceil((360 - r._larga["base"]) / musica.TROZO))
    assert 136.0 <= time.time() - r._t_ini_larga <= 141.0        # y la cuenta sigue desde ahí
    r.apagar()


def test_sin_pausa_la_emisora_sigue_sonando_sin_ti(tmp_path):
    m, r, usuario = _radio(tmp_path, [("programa.ogg", 6)])
    r.pausa = False
    r.sintonizar(usuario)
    assert _cargada(r)
    r._t_ini_larga = time.time() - 100.0
    r.apagar()
    r._recuerdos["usuario"]["cuando"] -= 50.0                    # como si hubieran pasado cincuenta segundos
    r._recuerdo = r._recuerdos["usuario"]
    assert 149.0 <= r.recuerdo_de("usuario")[1] <= 152.0
    r._recuerdo["cuando"] -= 300.0                                # y da la vuelta al acabar
    assert r.recuerdo_de("usuario")[1] < 360


def test_cada_emisora_recuerda_su_cancion(tmp_path):
    m, r, usuario = _radio(tmp_path, [("a.ogg", 4)])
    r._recuerdos["bravo"] = {"ruta": "x:/rock.ogg", "pos": 61.0, "cuando": time.time(), "dur": 200.0}
    r._recuerdos["sol"] = {"ruta": "x:/pop.ogg", "pos": 12.0, "cuando": time.time(), "dur": 180.0}
    assert r.recuerdo_de("bravo") == ("x:/rock.ogg", 61.0) and r.recuerdo_de("sol") == ("x:/pop.ogg", 12.0)
    assert r.recuerdo_de("ninguna") is None
    r._recuerdos["sol"]["pos"] = 179.0                           # se quedó en el final: se elige otra
    assert r.recuerdo_de("sol") is None


def test_el_volumen_de_la_radio(tmp_path):
    m, r, usuario = _radio(tmp_path, [("a.ogg", 3)])
    r.poner_nivel(0.3)
    r.sintonizar(usuario)
    assert _cargada(r) and abs(r.canal.vol - 0.3) < 1e-6 and r.sonando_ahora()
    r.poner_nivel(1.0)
    assert abs(r.canal.vol - 1.0) < 1e-6
    assert all(r.emisoras[k]["id"] not in ("apagada", "noticias", "usuario") for k in r.musicales())
    r.apagar()
    assert not r.sonando_ahora()


# ------------------------------------------------------------------ reproductor con auriculares
def _tecla(robot, k, mod=0):
    robot.app.pila[-1].tecla(pygame.event.Event(pygame.KEYDOWN, key=k, mod=mod, unicode=""))


def test_el_reproductor_con_auriculares(robot):
    from juego import menus_juego as mj
    p = robot.nueva_partida()
    radio = robot.app.radio
    robot.app.voz.registro.clear()
    _tecla(robot, pygame.K_r, pygame.KMOD_LSHIFT)
    assert "No tienes reproductor" in robot.dicho() and not p.j.walkman
    assert any(o["id"] == "walkman" for o in p.datos["objetos"])
    p.j.dinero = 500
    mj._comprar_walkman(p).accion()
    assert p.j.objetos["walkman"] == 1 and p.j.dinero == 500 - next(o["precio"] for o in p.datos["objetos"] if o["id"] == "walkman")
    mj._comprar_walkman(p).accion()
    assert p.j.objetos["walkman"] == 1                           # no se compra dos veces
    p.cfg["emisora"] = 1
    robot.app.voz.registro.clear()
    _tecla(robot, pygame.K_r, pygame.KMOD_RSHIFT)                # vale con cualquiera de las dos Mayúsculas
    assert p.j.walkman and p.walkman_puesto() and "Auriculares puestos" in robot.dicho()
    assert radio.id_actual() != "apagada" and abs(radio.nivel - p.ambiente_cfg()["walkman"]) < 1e-6 and radio.sonando_ahora()
    # al subir a un vehículo no se corta ni cambia de emisora; al bajar, sigue
    pedidos = radio._pedido
    x, y, d = p.plaza_cercana()
    v = p.crear_vehiculo("sedan", x, y, d, None)
    p._subir(v, False, callar=True)
    assert radio._pedido == pedidos and radio.nivel == 1.0
    p.salir_vehiculo(forzado=True)
    assert radio._pedido == pedidos and radio.sonando_ahora() and abs(radio.nivel - p.ambiente_cfg()["walkman"]) < 1e-6
    # se apaga al llegar a la emisora «apagada»
    for _ in range(len(radio.emisoras) + 1):
        _tecla(robot, pygame.K_r, pygame.KMOD_LSHIFT)
        if not p.j.walkman:
            break
    assert not p.j.walkman and "Reproductor apagado" in robot.dicho() and not radio.sonando_ahora()
    # con el reproductor apagado, la radio del coche se apaga al bajarte, como siempre
    p._subir(v, False, callar=True)
    p.cfg["emisora"] = 1
    radio.sintonizar(1)
    p.salir_vehiculo(forzado=True)
    assert not radio.sonando_ahora()
    assert p.j.a_dict()["walkman"] is False


def test_la_R_sola_sigue_recargando(robot):
    p = robot.nueva_partida()
    p.j.objetos["walkman"] = 1
    _tecla(robot, pygame.K_r)
    assert not p.j.walkman


# ------------------------------------------------------------------ música en los locales
def test_hilo_musical_en_los_locales(robot):
    p = robot.nueva_partida()
    radio = robot.app.radio
    tienda = next(l for l in p.mundo.lugares.values() if l.tipo == "tienda")
    banco = next(l for l in p.lugares.values() if l.tipo == "banco")
    assert "tienda" in p.ambiente_cfg()["locales"] and "banco" not in p.ambiente_cfg()["locales"]
    p.entrar_interior(tienda)
    assert p._hilo and radio.sonando_ahora() and abs(radio.nivel - p.ambiente_cfg()["hilo"]) < 1e-6
    emisora = radio.actual
    assert emisora in radio.musicales()
    p.salir_interior()
    assert not p._hilo and not radio.sonando_ahora()
    p.entrar_interior(tienda)
    assert radio.actual == emisora                               # cada local, siempre la suya
    p.salir_interior()
    p.entrar_interior(banco)                                     # en un banco no hay música
    assert not p._hilo and not radio.sonando_ahora()
    p.salir_interior()
    banco.d["musica"] = True                                     # salvo que el mapa lo diga
    tienda.d["sin_musica"] = True
    try:
        p.entrar_interior(banco)
        assert p._hilo
        p.salir_interior()
        p.entrar_interior(tienda)
        assert not p._hilo
        p.salir_interior()
    finally:
        banco.d.pop("musica")
        tienda.d.pop("sin_musica")
    # con los auriculares puestos, sigues oyendo lo tuyo
    p.j.objetos["walkman"] = 1
    p.cfg["emisora"] = 1
    p.walkman()
    mia = radio.actual
    p.entrar_interior(tienda)
    assert not p._hilo and radio.actual == mia and radio.sonando_ahora()
    p.salir_interior()
    assert radio.sonando_ahora()
    p.j.walkman = False
    radio.apagar()


def test_el_editor_edita_el_ambiente_y_la_musica_de_cada_lugar(robot):
    from editor import esquema as E
    p = robot.nueva_partida()
    campos = {c["k"] for c in E.ESQUEMAS["ajuste_ambiente"]["campos"]}
    assert set(p.datos["ambiente"][0]) <= campos
    assert {"musica", "sin_musica"} <= {c["k"] for c in E.ESQUEMAS["lugar"]["campos"]}
    assert ("ambiente", "Radio a pie y en los locales", "ajuste_ambiente") in E.SECCIONES


# ------------------------------------------------------------------ combinaciones del mando
def _mando(robot):
    md = robot.app.mando
    md.simulado = True
    md.mapa = {c: dict(m) for c, m in MD.POR_DEFECTO.items()}
    return md


def test_combinaciones_del_mando_a_pie(robot):
    from juego.menus import Menu
    p = robot.nueva_partida()
    md = _mando(robot)
    assert md.contexto() == "pie"
    # Vista sola: al soltarla abre el móvil, como siempre
    md.boton("back", True)
    assert robot.app.pila[-1] is p                              # todavía no: puede ser una combinación
    md.boton("back", False)
    assert isinstance(robot.app.pila[-1], Menu)
    while robot.app.pila[-1] is not p:
        robot.app.cerrar(robot.app.pila[-1])
    # Vista mantenida más cruceta arriba: el siguiente cruce, y el móvil no se abre
    robot.app.voz.registro.clear()
    md.boton("back", True)
    md.boton("arriba", True)
    md.boton("arriba", False)
    md.boton("back", False)
    assert "ruce" in robot.dicho() and robot.app.pila[-1] is p
    # más Y: dónde está mi vehículo
    robot.app.voz.registro.clear()
    md.boton("back", True)
    md.boton("y", True)
    md.boton("y", False)
    md.boton("back", False)
    assert "vehículo" in robot.dicho() and robot.app.pila[-1] is p and p.j.veh is None      # y no ha intentado subirse a nada
    # mientras se mantiene Vista, el gatillo no dispara
    md.boton("back", True)
    md.boton("rt", True)
    md.actualizar(0.02)
    assert pygame.K_SPACE not in robot.app.teclas
    md.boton("rt", False)
    md.boton("back", False)
    assert robot.app.pila[-1].titulo == "Acciones"               # desde la 1.7.1, esa combinación abre el menú de acciones
    robot.app.cerrar(robot.app.pila[-1])
    md.boton("rt", True)
    md.actualizar(0.02)
    assert pygame.K_SPACE in robot.app.teclas                    # sin Vista, sí
    md.boton("rt", False)
    md.actualizar(0.02)
    while robot.app.pila[-1] is not p:
        robot.app.cerrar(robot.app.pila[-1])


def test_combinaciones_del_mando_al_volante(robot):
    p = robot.nueva_partida()
    md = _mando(robot)
    x, y, d = p.plaza_cercana()
    v = p.crear_vehiculo("sedan", x, y, d, None)
    p._subir(v, False, callar=True)
    assert md.contexto() == "coche"
    p.cfg["piloto_gps"] = False
    md.boton("back", True)
    md.boton("a", True)
    md.boton("a", False)
    md.boton("back", False)
    assert p.cfg["piloto_gps"] is True and "Piloto del GPS" in robot.dicho()       # el piloto, que con mando no se podía
    l = next(q for q in p.mundo.lugares.values() if q.tipo == "hospital")
    p.gps_a_lugar(l)
    robot.app.voz.registro.clear()
    md.boton("back", True)
    md.boton("x", True)
    md.boton("x", False)
    md.boton("back", False)
    assert "metros" in robot.dicho() or "Faltan" in robot.dicho()                   # cuánto falta para llegar
    md.boton("back", True)
    md.boton("l3", True)
    md.boton("l3", False)
    md.boton("back", False)
    assert p.gps is None and v.dir == d                                             # cancela el GPS y no da media vuelta
    # B con Vista dice la velocidad y no echa el freno de mano
    md.boton("back", True)
    md.boton("b", True)
    md.actualizar(0.02)
    assert pygame.K_SPACE not in robot.app.teclas
    md.boton("b", False)
    md.boton("back", False)
    p.cfg["piloto_gps"] = False
    p.salir_vehiculo(forzado=True)


def test_las_combinaciones_salen_en_la_ayuda_y_se_guardan(robot):
    md = _mando(robot)
    lineas = md.lineas_ayuda()
    assert any("mantenido, más" in t and "piloto del GPS" in t for t in lineas)
    assert any("mantenido, más" in t and "siguiente cruce" in t for t in lineas)
    for ctx in ("pie_combo", "coche_combo"):
        assert all(a in MD.ACCIONES for a in MD.POR_DEFECTO[ctx].values())
        assert MD.COMBINAR not in MD.POR_DEFECTO[ctx]
        for b, a in MD.POR_DEFECTO[ctx].items():
            assert not MD.ACCIONES[a][3], (ctx, b, a)            # ninguna segunda función es de mantener pulsado
    assert "pie_combo" in md.mapa and "coche_combo" in md.mapa
