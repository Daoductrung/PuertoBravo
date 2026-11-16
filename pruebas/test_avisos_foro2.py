"""Lo último que contaron tras la 1.6.2: el pacto que se cobraba varias veces, oficios que no cuadran con la edad,
seguir algo con el radar sin perder el destino, hablar con quien ya conoces, amueblar la casa y la música del menú."""
import random
import time

import numpy as np
import pygame

from juego import charla, menus_extra, sintesis, sistemas
from juego.entidades import Objeto
from juego.menus import EntradaTexto, Menu, Opcion


def _partida(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.j.dinero = 5000
    robot.frames(2)
    return p, p.j


def _opcion(m, empieza):
    for k, o in enumerate(m.opciones):
        t = o.texto() if callable(o.texto) else o.texto
        if t.startswith(empieza):
            m.i = k
            return o
    raise AssertionError("no está la opción " + empieza)


def test_el_pacto_de_paz_no_se_cobra_dos_veces(robot):
    p, j = _partida(robot)
    app = robot.app
    j.territorios = ["a", "b", "c"]
    j.oferta_pacto = {"banda": "Los Lagartos", "precio": 1500, "dia": p.dia}
    menus_extra.territorios(p)
    terr = app.pila[-1]
    _opcion(terr, "Pacto con Los Lagartos")
    robot.tecla(pygame.K_RETURN)
    sub = app.pila[-1]
    assert sub is not terr
    # el fallo: el menú de Territorios seguía con la oferta escrita, y se podía entrar y aceptar una y otra vez
    aceptar = sub.opciones[0].accion
    robot.tecla(pygame.K_RETURN)
    assert j.dinero == 6500 and j.oferta_pacto is None and j.pacto_hasta == p.dia + 7
    assert terr not in app.pila and sub not in app.pila          # se cierran los dos: no queda la oferta a la vista
    aceptar()
    assert j.dinero == 6500 and "ya está resuelto" in robot.dicho()
    # lo mismo con el sobre del inspector
    j.redada = {"precio": 500, "dia": p.dia}
    menus_extra.territorios(p)
    terr = app.pila[-1]
    pagar = _opcion(terr, "Arreglar lo de la policía").accion
    robot.tecla(pygame.K_RETURN)
    assert j.dinero == 6000 and j.redada is None
    pagar()
    assert j.dinero == 6000


def test_el_oficio_cuadra_con_la_edad():
    rng = random.Random(3)
    for _ in range(3000):
        edad = rng.randint(19, 74)
        o = charla.oficio_para(edad, rng)
        assert not (o == "estudiante" and edad > 27) and not (o == "jubilado" and edad < 62) and not (edad >= 67 and o != "jubilado")
    vistos = {charla.oficio_para(e, rng) for e in range(19, 67) for _ in range(40)}
    assert {"estudiante", "jubilado", "camarero", "en paro"} <= vistos

    class Q:
        pass
    for _ in range(300):                                          # y en la ficha de la gente de la calle
        f = charla.ficha(Q(), rng)
        assert not (f["oficio"] == "estudiante" and f["edad"] > 27) and not (f["oficio"] in ("jubilado", "jubilada") and f["edad"] < 62)


def test_un_desvio_con_el_radar_no_pierde_el_destino(robot):
    p, j = _partida(robot)
    x, y = p.pos()
    lejos = next(l for l in p.mundo.lugares.values() if 150 < abs(l.x - x) + abs(l.y - y) < 500)
    p.gps_a_lugar(lejos)
    assert p.gps["nombre"] == lejos.nombre
    o = Objeto("dinero", "Billetes", *p.mundo.punto_libre(x + 20, y))
    o.valor = 50
    p.objetos.append(o)
    p.radar_lista = [("Billetes", o.x, o.y, o)]
    p.radar_idx = 0
    p.baliza_radar()
    assert p.gps["nombre"] == "Billetes" and p.gps["anterior"]["nombre"] == lejos.nombre
    assert f"Al llegar, el GPS vuelve a {lejos.nombre}" in robot.dicho()
    # llega a los billetes: el GPS vuelve solo a donde iba
    p.teletransportar(o.x, o.y)
    p.t_gps = 0.0
    robot.frames(3)
    assert p.gps is not None and p.gps["nombre"] == lejos.nombre and "anterior" not in p.gps
    assert f"El GPS vuelve a {lejos.nombre}" in robot.dicho()
    # otro desvío, y esta vez lo deja con Mayúsculas G: vuelve al destino, y con otra más, lo quita
    p.teletransportar(x, y)
    p.radar_lista = [("Billetes", o.x, o.y, o)]
    p.radar_idx = 0
    p.baliza_radar()
    assert p.gps["nombre"] == "Billetes"
    robot.tecla(pygame.K_g, pygame.KMOD_SHIFT)
    assert p.gps["nombre"] == lejos.nombre and "Dejas el desvío" in robot.dicho()
    robot.tecla(pygame.K_g, pygame.KMOD_SHIFT)
    assert p.gps is None
    # sin destino previo, marcar algo con el radar es lo de siempre
    p.radar_lista = [("Billetes", o.x, o.y, o)]
    p.radar_idx = 0
    p.baliza_radar()
    assert p.gps["nombre"] == "Billetes" and not p.gps.get("anterior")


def test_amueblar_la_casa(robot):
    p, j = _partida(robot)
    app = robot.app
    casa = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and int(l.get("garaje", 0)))
    j.propiedades.append(casa.id)
    j.dinero = 5000
    sistemas.menu_muebles(p, casa, Menu, Opcion)
    m = app.pila[-1]
    assert len([o for o in m.opciones if "euros" in (o.texto() if callable(o.texto) else o.texto)]) == 6
    _opcion(m, "Un sofá grande")
    robot.tecla(pygame.K_RETURN)
    assert j.dinero == 4400 and sistemas.muebles_de(j, casa) == ["sofa"]
    robot.tecla(pygame.K_RETURN)                                  # no se compra dos veces
    assert j.dinero == 4400
    for nombre in ("Una cama de las buenas", "Un banco de herramientas", "Plantas, cuadros", "Cocina equipada", "Baño reformado"):
        _opcion(m, nombre)
        robot.tecla(pygame.K_RETURN)
    assert j.dinero == 4400 - 800 - 900 - 300 - 700 - 500 and len(j.muebles[casa.id]) == 6
    app.cerrar(m)
    # se nota al recorrer la casa
    interior = sistemas.Interior(p, casa, {"descansar": lambda: None, "garaje": lambda: None})
    assert "sofá en el que caben cuatro" in next(d for n, d, q in interior.habitaciones if q == "salon")
    app.abrir(interior)
    j.animo = 40.0
    interior.i = next(k for k, h in enumerate(interior.habitaciones) if h[2] == "salon")
    robot.tecla(pygame.K_RETURN)
    assert j.animo == 48.0                                        # el doble que sin sofá
    j.salud = 20.0
    j.dia_nevera = -1
    interior.i = next(k for k, h in enumerate(interior.habitaciones) if h[2] == "cocina")
    robot.tecla(pygame.K_RETURN)
    assert j.salud == 70.0
    app.cerrar(interior)
    # al dormir: más ánimo, y el garaje repara lo guardado
    modelo = p.modelos["utilitario"]
    j.garajes[casa.id] = [{"modelo": "utilitario", "salud": 10.0, "nombre": "Utilitario"}]
    j.animo = 40.0
    texto = sistemas.al_dormir_en_casa(p, casa)
    assert j.animo == 51.0 and j.garajes[casa.id][0]["salud"] == float(modelo["salud"]) and "1 vehículo ha quedado reparado" in texto
    # y se guarda con la partida; otra casa empieza vacía
    assert p.a_dict()["jugador"]["muebles"][casa.id] == j.muebles[casa.id]
    otra = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and l.id != casa.id)
    assert sistemas.muebles_de(j, otra) == [] and sistemas.al_dormir_en_casa(p, otra) == ""


def test_hablar_con_tus_palabras_a_alguien_que_ya_conoces(robot):
    from juego import menus_adultos
    p, j = _partida(robot)
    app = robot.app
    p.cfg["adultos"] = True
    p.cfg["ia_activa"] = False
    pers = p.dato_adulto("personas")[0]
    p.relacion(pers["id"])["afinidad"] = 30
    menus_adultos.vida_social(p, directo=pers["id"])
    m = app.pila[-1]
    _opcion(m, "Hablarle con tus palabras")
    robot.tecla(pygame.K_RETURN)
    entrada = app.pila[-1]
    assert isinstance(entrada, EntradaTexto) and pers["nombre"] in entrada.titulo and "por teléfono" in entrada.titulo      # no estáis en el mismo sitio
    entrada.al_aceptar("Hola, ¿qué tal te ha ido el día?")
    assert robot.dicho().rsplit(" | ", 1)[-1].startswith(pers["nombre"] + ":")           # contesta esa persona, con su nombre
    assert p.relacion(pers["id"])["afinidad"] >= 30
    assert pers["nombre"] not in [q.nombre for q in p.personas]                           # no aparece nadie en la calle por hablarle
    entrada.al_aceptar("Me gustas mucho, ¿salimos esta noche?")                           # ligar por escrito lleva a proponer un plan
    assert pers["nombre"] + ":" in robot.dicho().rsplit(" | ", 1)[-1]
    # hablar acerca, pero solo una vez al día
    tope = p.relacion(pers["id"])["afinidad"]
    for _ in range(6):
        entrada.al_aceptar("Hola, buenos días, me alegro de verte.")
    assert p.relacion(pers["id"])["afinidad"] <= tope + 2


def test_la_musica_larga_se_convierte_por_tramos_y_suena_igual():
    """Las piezas del menú vienen a 48 kHz. Convertirlas de golpe costaba segundos: por eso tardaba la música del menú."""
    sr, seg = 48000, 60
    t = np.arange(sr * seg) / sr
    x = (0.4 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 3000 * t)).astype(np.float32)
    estereo = np.stack([x, x[::-1]], axis=1)
    t0 = time.time()
    y = sintesis._remuestrear(estereo, sr)
    tarda = time.time() - t0
    assert y.shape == (sintesis.SR * seg, 2) and y.dtype == np.float32
    n = np.arange(len(y)) / sintesis.SR
    ref = 0.4 * np.sin(2 * np.pi * 440 * n) + 0.2 * np.sin(2 * np.pi * 3000 * n)
    assert float(np.abs(y[4000:-4000, 0] - ref[4000:-4000]).max()) < 0.002          # ni chasquidos en las juntas ni agudos perdidos
    entero = sintesis._remuestrear_entero(estereo[:sr * 10], sr)
    assert float(np.abs(entero[4000:-4000] - y[4000:len(entero) - 4000]).max()) < 0.002
    assert tarda < 5.0
    # un sonido corto se sigue convirtiendo de una vez, y uno mono sale mono
    corto = sintesis._remuestrear(x[:20000], sr)
    assert corto.ndim == 1 and len(corto) == round(20000 * sintesis.SR / sr)
    largo_mono = sintesis._remuestrear(x, 22050)
    assert largo_mono.ndim == 1 and len(largo_mono) == len(x) * 2


def test_la_ia_local_encuentra_las_bibliotecas_del_juego(monkeypatch, tmp_path):
    """A quien no tiene instaladas las bibliotecas de Visual C++, el programa del modelo le daba error. Se le dice dónde están las del juego."""
    import os
    import sys

    from juego import ia
    exe = tmp_path / "llama-server.exe"
    exe.write_bytes(b"")
    visto = {}

    class Falso:
        _handle = 0

        def poll(self):
            return None

    def popen(orden, **kw):
        visto.update(kw, orden=orden)
        return Falso()
    monkeypatch.setattr(ia, "_archivos_locales", lambda: (str(exe), str(tmp_path / "m.gguf")))
    monkeypatch.setattr(ia.subprocess, "Popen", popen)
    monkeypatch.setattr(ia, "_atar_al_juego", lambda pr: False)
    monkeypatch.setattr(ia, "_proceso", [None])
    monkeypatch.setattr(ia.atexit, "register", lambda f: None)
    assert ia.arrancar_local(calentar=False)
    ruta = visto["env"]["PATH"].split(os.pathsep)
    assert ruta[0] == os.path.dirname(os.path.abspath(sys.executable)) and len(ruta) > 2
