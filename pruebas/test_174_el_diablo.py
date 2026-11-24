"""El mod El Diablo (componentes_extra/mod_el_diablo): se carga, se juega entero y está traducido."""
import glob
import json
import os
import random
import re
import shutil
import sys

import pytest

from juego import contratos as C
from juego import rutas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(RAIZ, "componentes_extra", "mod_el_diablo")
MOD = os.path.join(BASE, "el_diablo.json")


@pytest.fixture
def _mods_con_el_diablo(tmp_path, monkeypatch):
    """Los mods de serie más El Diablo, en una carpeta aparte: no se toca data/mods."""
    for f in glob.glob(os.path.join(RAIZ, "data", "mods", "*.json")):
        shutil.copy(f, tmp_path)
    shutil.copy(MOD, tmp_path)
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))


@pytest.fixture
def app(_mods_con_el_diablo, app):
    return app


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
    assert not os.path.exists(os.path.join(RAIZ, "data", "mods", "el_diablo.json"))      # no viene con el juego: es un componente
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
