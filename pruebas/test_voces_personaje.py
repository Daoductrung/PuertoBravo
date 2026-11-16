"""Las voces según el protagonista: una grabación por personaje y género, y las de un personaje propio, generadas."""
import os
import time

import numpy as np
import pygame
import pytest

from juego import voces, vozgen
from juego.menus import Dialogo, Menu
from test_voces import _grabar

LINEAS = [["Encarna", "¡Dani! Pasa."], ["Encarna", "Bienvenid[o|a] a casa."], ["Dani", "Gracias, tía."], ["Encarna", "Dani, [hijo|hija], siéntate."],
          ["Narrador", "El bar huele a café."], ["Dani", "Soy Dani Roca."]]


class J:
    def __init__(self, personaje="dani", genero="h", nombre="Dani", apellido="Roca", voz="dani", dicho=""):
        self.personaje, self.genero, self.nombre, self.apellido, self.voz, self.nombre_dicho = personaje, genero, nombre, apellido, voz, dicho


def test_cada_frase_tiene_la_forma_que_le_toca():
    f = voces.forma
    # la que no depende de nada vale para todos
    assert [f("Narrador", "El bar huele a café.", p, g) for p in voces.PERSONAJES for g in "hm"] == [""] * 8
    # le nombran: una por personaje
    assert [f("Encarna", "¡Dani! Pasa.", p, "m") for p in voces.PERSONAJES] == ["", "@alex", "@sam", "@cris"]
    # cambia con el género: una en femenino, la misma para todos
    assert f("Encarna", "Bienvenid[o|a].", "cris", "h") == "" and f("Encarna", "Bienvenid[o|a].", "cris", "m") == "@m"
    # las dos cosas, o la dice el protagonista: una por personaje y género
    assert f("Encarna", "Dani, [hijo|hija].", "alex", "m") == "@alex_m" and f("Encarna", "Dani, [hijo|hija].", "dani", "h") == ""
    assert f("Dani", "Gracias.", "sam", "h") == "@sam_h" and f("Dani", "Gracias.", "dani", "m") == "@dani_m"
    assert len(voces.formas("Dani", "Gracias.")) == 8 and len(voces.formas("Encarna", "¡Dani!")) == 4
    assert len(voces.formas("Encarna", "Bienvenid[o|a].")) == 2 and len(voces.formas("Narrador", "Nada.")) == 1
    # un personaje hecho por el jugador: lo que dice su nombre no viene grabado; lo demás, sí
    assert f("Encarna", "¡Dani! Pasa.", "propio", "h") is None and f("Dani", "Soy Dani.", "propio", "m", "sam") is None
    assert f("Dani", "Gracias.", "propio", "m", "sam") == "@sam_m" and f("Dani", "Gracias.", "propio", "h", "dani") == ""
    assert f("Encarna", "Bienvenid[o|a].", "propio", "m") == "@m" and f("Narrador", "Nada.", "propio", "m") == ""


def test_el_dialogo_coge_la_grabacion_de_tu_personaje(monkeypatch, tmp_path):
    carpeta = str(tmp_path / "voces")
    monkeypatch.setattr(voces, "carpeta", lambda: carpeta)
    monkeypatch.setattr(vozgen, "carpeta_generadas", lambda: str(tmp_path / "generadas"))
    for n in ("x_1_1", "x_1_1@alex", "x_1_2", "x_1_2@m", "x_1_3", "x_1_3@alex_m", "x_1_3@sam_h", "x_1_4", "x_1_4@alex_m", "x_1_5", "x_1_6"):
        _grabar(carpeta, n)
    base = lambda r: os.path.splitext(os.path.basename(r))[0] if r else None
    de = lambda j: [base(r) for r in (voces.de_dialogo("x", 0, LINEAS, j) or [])]
    assert de(J()) == ["x_1_1", "x_1_2", "x_1_3", "x_1_4", "x_1_5", "x_1_6"]
    assert de(J("alex", "m", "Álex", "Montes")) == ["x_1_1@alex", "x_1_2@m", "x_1_3@alex_m", "x_1_4@alex_m", "x_1_5", None]
    # a quien le falta su grabación no le suena la de otro: esa frase la dice el lector
    assert de(J("cris", "h", "Cris", "Navarro")) == [None, "x_1_2", None, None, "x_1_5", None]
    # el personaje propio: lo común, lo de su género, y su voz elegida para lo que dice él; su nombre, todavía sin generar
    propio = J("propio", "h", "Héctor", "Lázaro", "sam")
    assert de(propio) == [None, "x_1_2", "x_1_3@sam_h", None, "x_1_5", None]
    # cuando ya se le ha generado, suena lo suyo
    gen = vozgen.Personaje.de_jugador(propio).carpeta()
    _grabar(gen, "x_1_1")
    open(os.path.join(gen, "x_1_1.wav.txt"), "w").close()
    os.replace(os.path.join(gen, "x_1_1.wav"), os.path.join(gen, "x_1_1.ogg"))
    os.replace(os.path.join(gen, "x_1_1.wav.txt"), os.path.join(gen, "x_1_1.ogg.txt"))
    assert de(propio)[0] == "x_1_1" and voces.de_dialogo("x", 0, LINEAS, propio)[0].startswith(gen)
    # otro personaje propio, con otro nombre, no oye lo generado para el primero
    assert de(J("propio", "h", "Lucas", "", "sam"))[0] is None
    assert "Héctor" not in gen and "Lázaro" not in gen               # la carpeta no dice cómo se llama


def test_el_guion_de_un_mod_dice_las_formas_de_cada_frase(monkeypatch, tmp_path):
    carpeta = str(tmp_path / "voces")
    monkeypatch.setattr(voces, "carpeta", lambda: carpeta)
    _grabar(carpeta, "x_1_1@alex")
    g = voces.guion([{"id": "x", "titulo": "Prueba", "pasos": [{"tipo": "dialogo", "lineas": LINEAS}]}], "Mi mod")
    assert "x_1_1\nEncarna: ¡Dani! Pasa.\n  Esta frase cambia con el protagonista" in g
    assert "  x_1_1@alex  GRABADA: con Alex, en masculino" in g and "  x_1_1@cris: con Cris" in g
    assert "  x_1_2@m: con Dani, en femenino" in g and "x_1_5\nNarrador: El bar huele a café.\n\n" in g
    assert "Total: 6 frases" in g


def test_las_voces_que_trae_el_juego_cubren_a_los_cuatro_personajes():
    """Con las voces de esta versión, cada frase de la historia tiene su grabación para cada personaje y género."""
    voces.refrescar()
    if not voces.buscar("m01", 0, 0, "@alex"):
        pytest.skip("en esta copia no están las voces de la 1.6.3")
    from juego import mundo
    faltan, total = [], 0
    for m in mundo.cargar_datos()["misiones"]:
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            for n, (quien, texto) in enumerate(paso["lineas"]):
                for forma, pj, g in voces.formas(quien, texto):
                    total += 1
                    if not voces.buscar(m["id"], k, n, forma):
                        faltan.append(f"{m['id']}_{k + 1}_{n + 1}{forma}")
    assert total >= 1100 and len(faltan) <= total * 0.02, faltan[:20]          # alguna puede no haberse entendido y la dice el lector


def test_lo_que_hay_que_generar_a_un_personaje_propio():
    from juego import mundo
    datos = mundo.cargar_datos()
    rep = {"personajes": {"Encarna": "voz_e", "Marta": "voz_m"}, "protagonista": {"sam_m": "prota_sam_m"}}
    pj = vozgen.Personaje("Lía", "Del Mar", "m", "sam", "")
    ms = [{"id": "x", "pasos": [{"tipo": "ir"}, {"tipo": "dialogo", "lineas": LINEAS + [["Desconocido", "Hola, Dani."], ["Marta", "Dani Roca, [el|la] de siempre."]]}]}]
    p = vozgen.pendientes(pj, ms, rep)
    assert [(os.path.basename(a), v, t) for a, v, t, _ in p] == [
        ("x_2_1.ogg", "voz_e", "¡Lía! Pasa."), ("x_2_4.ogg", "voz_e", "Lía, hija, siéntate."), ("x_2_6.ogg", "prota_sam_m", "Soy Lía Del Mar."),
        ("x_2_8.ogg", "voz_m", "Lía Del Mar, la de siempre.")]                 # quien no tiene voz en el reparto no se genera
    # si el nombre se pronuncia de otra manera, eso es lo que se le da al motor
    assert vozgen.Personaje("Jonathan", "", "h", "dani", "Yónatan").texto("Hola, Dani.") == "Hola, Yónatan."
    # cambiar el nombre, la pronunciación o la voz es otra carpeta; el mismo personaje, la misma
    assert pj.clave() == vozgen.Personaje("Lía", "Del Mar", "m", "sam").clave() != vozgen.Personaje("Lía", "Del Mar", "m", "cris").clave()
    # con los datos de verdad: las frases de la historia que dicen su nombre
    reales = vozgen.pendientes(pj, datos["misiones"], vozgen.reparto())
    if vozgen.reparto()["personajes"]:
        assert 30 <= len(reales) <= 60 and all("Dani" not in t for _, _, t, _ in reales)


class GeneradorFalso(vozgen.Generador):
    """Como el de verdad, pero la «voz» es un pitido: para probar todo lo demás sin cargar el modelo."""

    def sintetizar(self, voz, texto):
        time.sleep(0.02)
        t = np.arange(int(24000 * 0.3)) / 24000
        return (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32), 24000


def test_generar_guardar_y_no_repetir(monkeypatch, tmp_path):
    monkeypatch.setattr(vozgen, "carpeta_generadas", lambda: str(tmp_path / "generadas"))
    monkeypatch.setattr(vozgen, "disponible", lambda: True)
    monkeypatch.setattr(vozgen, "reparto", lambda: {"personajes": {"Encarna": "voz_e"}, "protagonista": {"dani_h": "prota"}})
    ms = [{"id": "a", "pasos": [{"tipo": "dialogo", "lineas": LINEAS}]}, {"id": "b", "pasos": [{"tipo": "dialogo", "lineas": [["Encarna", "Adiós, Dani."]]}]}]
    pj = vozgen.Personaje("Héctor", "Lázaro", "h", "dani")
    g = GeneradorFalso()
    assert g.pedir(pj, ms, primero="b") == 4
    g.hilo.join(10)
    assert g.hechas == 4 and g.quedan() == 0 and not g.activo()
    archivos = sorted(os.listdir(pj.carpeta()))
    assert archivos == ["a_1_1.ogg", "a_1_1.ogg.txt", "a_1_4.ogg", "a_1_4.ogg.txt", "a_1_6.ogg", "a_1_6.ogg.txt", "b_1_1.ogg", "b_1_1.ogg.txt"]
    import soundfile as sf
    assert sf.info(os.path.join(pj.carpeta(), "a_1_1.ogg")).samplerate == 24000
    assert g.pedir(pj, ms) == 0                                      # ya está todo: no se repite
    ms[1]["pasos"][0]["lineas"][0][1] = "Hasta luego, Dani."         # un mod cambia una frase: solo esa se rehace
    assert g.pedir(pj, ms) == 1
    g.hilo.join(10)
    assert g.pedir(pj, ms) == 0
    # y el diálogo ya las encuentra
    j = J("propio", "h", "Héctor", "Lázaro", "dani")
    lista = voces.de_dialogo("a", 0, LINEAS, j)
    assert lista[0] and lista[3] and lista[5] and lista[0].startswith(pj.carpeta())


def test_la_pantalla_de_preparando_espera_a_las_primeras_y_se_puede_saltar(robot, monkeypatch, tmp_path):
    app = robot.app
    monkeypatch.setattr(vozgen, "carpeta_generadas", lambda: str(tmp_path / "generadas"))
    monkeypatch.setattr(vozgen, "disponible", lambda: True)
    monkeypatch.setattr(vozgen, "reparto", lambda: {"personajes": {"Encarna": "voz_e"}, "protagonista": {}})
    falso = GeneradorFalso()
    monkeypatch.setattr(vozgen, "generador", falso)
    ms = [{"id": "a", "pasos": [{"tipo": "dialogo", "lineas": [["Encarna", f"Dani, frase {k}."] for k in range(9)]}]}]
    hecho = []
    pj = vozgen.Personaje("Héctor", "", "h")
    app.abrir(vozgen.Preparando(app, pj, ms, lambda: hecho.append(1)))
    assert "Preparando las voces de tu personaje" in robot.dicho() and "Escape" in robot.dicho()
    fin = time.time() + 10
    while not hecho and time.time() < fin:
        robot.frames(2)
        time.sleep(0.02)
    assert hecho == [1] and falso.hechas >= vozgen.Preparando.PRIMERAS          # no espera a las nueve: sigue jugando mientras se hacen
    assert not any(isinstance(x, vozgen.Preparando) for x in app.pila)
    falso.hilo.join(10)
    assert falso.hechas == 9
    # con Escape se empieza ya
    pj2 = vozgen.Personaje("Lucas", "", "h")
    lento = GeneradorFalso()
    lento.sintetizar = lambda voz, texto: (time.sleep(0.5), GeneradorFalso.sintetizar(lento, voz, texto))[1]
    monkeypatch.setattr(vozgen, "generador", lento)
    hecho.clear()
    app.abrir(vozgen.Preparando(app, pj2, ms, lambda: hecho.append(2)))
    robot.frames(2)
    assert not hecho
    robot.tecla(pygame.K_ESCAPE)
    assert hecho == [2] and "Empiezas ya" in robot.dicho()
    lento.detener()
    lento.hilo.join(10)


def test_crear_un_personaje_con_voz_y_pronunciacion(robot, monkeypatch, tmp_path):
    from juego import menus_vida, vida
    app = robot.app
    monkeypatch.setattr(vozgen, "disponible", lambda: True)
    menus_vida.crear_personaje(app)
    m = app.pila[-1]
    textos = [o.texto() if callable(o.texto) else o.texto for o in m.opciones]
    assert any(t.startswith("Tu voz en las escenas: la de Dani, en masculino") for t in textos)
    assert any(t.startswith("Cómo se pronuncia tu nombre: igual que se escribe") for t in textos) and "Escuchar cómo te llamarán" in textos and "Escuchar tu voz" in textos
    m.i = next(k for k, t in enumerate(textos) if t.startswith("Tu voz"))
    robot.tecla(pygame.K_RIGHT)
    ahora = m.opciones[m.i].texto
    assert (ahora() if callable(ahora) else ahora).startswith("Tu voz en las escenas: la de Álex")
    # el personaje guarda su voz y cómo se pronuncia, y la partida también
    pj = vida.personaje_propio("Jonathan", "Smith", "h", voz="alex", dicho="Yónatan")
    assert pj["voz"] == "alex" and pj["dicho"] == "Yónatan"
    app.empezar_partida(None, personaje=pj)
    robot.saltar_dialogos()
    p = app.partida
    assert (p.j.voz, p.j.nombre_dicho, p.j.nombre) == ("alex", "Yónatan", "Jonathan")
    assert p.txt("Hola, Dani.") == "Hola, Jonathan."                            # en pantalla y en braille, como se escribe
    d = p.a_dict()
    assert d["jugador"]["voz"] == "alex" and d["jugador"]["nombre_dicho"] == "Yónatan"
    # uno de la lista no lleva nada de eso
    app.empezar_partida(None, personaje={"id": "sam", "genero": "m"})
    assert (app.partida.j.voz, app.partida.j.nombre_dicho) == ("dani", "")


def test_el_generador_de_verdad_dice_una_frase():
    """Con el modelo puesto en data/phonon y un procesador que pueda, el motor genera voz de verdad."""
    vozgen._estado.update(ok=None, motivo="")
    if not vozgen.disponible():
        pytest.skip("sin generador en esta copia: " + vozgen.motivo())
    rep = vozgen.reparto()
    assert len(rep["protagonista"]) == 8 and "Encarna" in rep["personajes"]
    for archivo in list(rep["personajes"].values()) + list(rep["protagonista"].values()):
        assert os.path.exists(os.path.join(vozgen.carpeta_motor(), "voces", archivo + ".safetensors"))
    g = vozgen.Generador()
    pcm, sr = g.sintetizar(rep["personajes"]["Encarna"], "¡Héctor! Pasa.")
    assert sr == 24000 and 0.5 < len(pcm) / sr < 6 and 0.5 < float(np.abs(pcm).max()) <= 1.0
    assert os.path.exists(os.path.join(vozgen.carpeta_motor(), "LICENCIA.txt"))


def test_si_se_quitan_las_voces_en_opciones_se_deja_de_generar(monkeypatch, tmp_path):
    """En un equipo modesto, si generar estorba, se quita en Opciones: no se genera nada más y lo dice el lector."""
    monkeypatch.setattr(vozgen, "carpeta_generadas", lambda: str(tmp_path / "generadas"))
    monkeypatch.setattr(vozgen, "disponible", lambda: True)
    monkeypatch.setattr(vozgen, "reparto", lambda: {"personajes": {"Encarna": "voz_e"}, "protagonista": {}})
    ms = [{"id": "a", "pasos": [{"tipo": "dialogo", "lineas": [["Encarna", f"Dani, frase {k}."] for k in range(40)]}]}]
    g = GeneradorFalso()
    monkeypatch.setattr(vozgen, "generador", g)
    cfg = {"voces_grabadas": True, "voces_propias": True}

    class App:
        pruebas = False

    class P:
        app, datos = App(), {"misiones": ms}
        j = J("propio", "h", "Héctor", "", "dani")
    P.cfg = cfg
    assert vozgen.al_jugar(P) == 40 and g.activo()
    time.sleep(0.15)
    cfg["voces_propias"] = False                         # el jugador lo quita con la partida en marcha
    g.hilo.join(5)
    assert not g.activo() and 0 < g.hechas < 40 and g.quedan() == 0
    hechas = g.hechas
    assert vozgen.al_jugar(P) == 0 and vozgen.al_jugar(P, "a") == 0 and not g.activo()      # y no vuelve a empezar sola
    # las que no se generaron no suenan: las dice el lector
    lista = voces.de_dialogo("a", 0, ms[0]["pasos"][0]["lineas"], P.j)
    assert lista is not None and sum(1 for r in lista if r) == hechas and lista[-1] is None
    # con las voces de las escenas quitadas del todo, tampoco
    cfg["voces_propias"], cfg["voces_grabadas"] = True, False
    assert vozgen.al_jugar(P) == 0 and not g.activo()
    # y si se vuelven a poner, sigue por donde iba
    cfg["voces_grabadas"] = True
    assert vozgen.al_jugar(P) == 40 - hechas
    g.hilo.join(10)
    assert g.quedan() == 0
