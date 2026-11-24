"""El mod El Diablo: viene con el juego desde la 1.7.4 (data/mods/el_diablo.json) y, para la 1.7.3, como componente
(componentes_extra/mod_el_diablo). Se carga, se juega entero, sus contratos solo cuelgan en su tablón, está traducido y
tiene voces en español y en inglés."""
import json
import os
import random
import re
import sys

import pytest

from juego import contratos as C

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(RAIZ, "componentes_extra", "mod_el_diablo")
MOD = os.path.join(RAIZ, "data", "mods", "el_diablo.json")


def _jugar(robot, p, nombre):
    """Pasa por todos los pasos de lo que está en marcha, comprobando que cada pelea y cada persecución se monta."""
    vistos = []
    for _ in range(30):
        if not p.mision:
            break
        paso = p.mision["def"]["pasos"][p.mision["paso"]]
        vistos.append(paso["tipo"])
        robot.frames(3)
        if paso["tipo"] == "eliminar":
            if not p.mision["enemigos"]:
                l = p._lugar_paso(paso)
                p.j.x, p.j.y = l.x, l.y
                robot.frames(40)
            assert p.mision["enemigos"], (nombre, "sin enemigos")
        elif paso["tipo"] == "perseguir":
            if p.mision.get("veh_objetivo") is None:
                l = p._lugar_paso(paso)
                p.j.x, p.j.y = l.x + 30, l.y
                robot.frames(40)
            assert p.mision.get("veh_objetivo") is not None, (nombre, "sin vehículo al que perseguir")
        elif paso["tipo"] == "dialogo":
            robot.saltar_dialogos()
        if p.mision and p.mision["def"]["pasos"][p.mision["paso"]] is paso:
            p._siguiente_paso()
    assert not p.mision, (nombre, vistos)
    return vistos


def test_el_diablo_se_juega_entero(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    agencia = p.lugares["di_agencia"]
    assert agencia.tipo == "taberna"                                    # con su tablón de encargos
    for ident in ("di01", "di02", "di03", "di04"):
        p.iniciar_mision(next(m for m in p.datos["misiones"] if m["id"] == ident))
        _jugar(robot, p, ident)
    assert "di_cuerno" in p.j.armas                                     # la recompensa de la última
    ids = [c["id"] for c in C.tipos(p)]
    assert "clasico" in ids                                             # se suman a los de serie
    p.j.stats["contratos"] = 5                                          # para que salgan también los que piden experiencia
    rng = random.Random(1)
    for c in C.tipos(p):
        if c["id"].startswith("di_"):
            assert c["situacion"] != "intimidar"
            o = p._oferta(c, agencia, rng)
            assert o and "{" not in o["resumen"], c["id"]
            p.empezar_contrato_de(agencia, o)
            _jugar(robot, p, c["id"])


@pytest.mark.parametrize("idioma", ["en", "pt", "vi"])
def test_el_diablo_esta_traducido_entero(idioma):
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "i18n"))
    import extraer
    assert os.path.exists(MOD)                                          # desde la 1.7.4 viene con el juego
    spec = json.load(open(os.path.join(BASE, "componente.json"), encoding="utf-8"))
    assert spec["tipo"] == "mod" and spec["nombres"][idioma] and spec["descripciones"][idioma]
    assert any(a.get("destino") == f"data/idiomas/{idioma}/mods/el_diablo.json" for a in spec["archivos"])
    cat = json.load(open(os.path.join(RAIZ, "traduccion", idioma, "mods", "el_diablo.json"), encoding="utf-8"))["textos"]
    textos = []

    def rec(o):
        if isinstance(o, str):
            if extraer.es_texto(o):
                textos.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)
    rec(json.load(open(MOD, encoding="utf-8")))
    assert len(textos) >= 60 and not [t for t in textos if not cat.get(t)]
    for es, otro in cat.items():                                        # los huecos de los contratos se quedan como están
        assert sorted(re.findall(r"\{\w+\}", es)) == sorted(re.findall(r"\{\w+\}", otro)), es


def test_los_contratos_de_el_diablo_solo_en_su_tablon(robot):
    p = robot.nueva_partida()
    p.j.stats["contratos"] = 5
    agencia = p.lugares["di_agencia"]
    otra = next(l for l in p.mundo.lugares.values() if l.tipo == "taberna" and l is not agencia)
    assert all(C.en_tablon(c, agencia) for c in C.tipos(p))               # en la suya, los suyos y los de siempre
    assert not [c for c in C.tipos(p) if c["id"].startswith("di_") and C.en_tablon(c, otra)]
    vistos_aqui, vistos_alli = set(), set()
    for dia in range(40):
        p.dia = dia
        vistos_aqui |= {o["tipo"]["id"] for o in p.ofertas_contrato(agencia)}
        vistos_alli |= {o["tipo"]["id"] for o in p.ofertas_contrato(otra)}
    assert any(i.startswith("di_") for i in vistos_aqui) and not any(i.startswith("di_") for i in vistos_alli)


def test_un_contrato_sin_tablones_cuelga_en_todos(robot):
    p = robot.nueva_partida()
    l = next(l for l in p.mundo.lugares.values() if l.tipo == "taberna")
    assert C.en_tablon({"id": "x"}, l) and C.en_tablon({"id": "x", "tablones": []}, l)
    assert C.en_tablon({"id": "x", "tablones": ["taberna"]}, l)               # también por tipo de lugar
    assert not C.en_tablon({"id": "x", "tablones": ["otro_sitio"]}, l)


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_el_diablo_tiene_voces(idioma):
    carpeta = os.path.join(RAIZ, "data", "voces", f"el_diablo_{idioma}")
    mod = json.load(open(MOD, encoding="utf-8"))
    faltan = []
    for m in mod["misiones"]:
        for k, paso in enumerate(m["pasos"]):
            if paso.get("tipo") == "dialogo":
                for n, _ in enumerate(paso["lineas"]):
                    if not os.path.exists(os.path.join(carpeta, f"{m['id']}_{k + 1}_{n + 1}.ogg")):
                        faltan.append(f"{m['id']}_{k + 1}_{n + 1}")
    assert not faltan, faltan
    spec = json.load(open(os.path.join(BASE, "componente.json"), encoding="utf-8"))
    assert {"carpeta": f"../../data/voces/el_diablo_{idioma}", "destino": f"data/voces/el_diablo_{idioma}"} in spec["archivos"]


def test_cada_mod_de_serie_esta_en_la_compilacion_y_en_su_comprobacion():
    """Al hacer de serie un mod hay que apuntarlo en compilar.bat, que lo copia, y en comprobar_limpio.py, que si no lo
    toma por un mod personal y la compilación falla al final (le pasó a El Diablo en la 1.7.4)."""
    sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
    import comprobar_limpio
    bat = open(os.path.join(RAIZ, "compilar.bat"), encoding="utf-8", errors="replace").read()
    for f in sorted(os.listdir(os.path.join(RAIZ, "data", "mods"))):
        if f.endswith(".json"):
            nombre = os.path.splitext(f)[0]
            assert nombre + ".pbm" in comprobar_limpio.MODS_DE_SERIE, nombre
            assert f'copy /y "data\mods\{f}"' in bat, nombre
