"""Las ramas de la historia se cruzan: lo que decides en Puerto Bravo, en Villaseca y en San Lucero se junta.

Cada rama recuerda lo decidido en las otras, una misión las reúne cuando has cerrado las tres, y hay tres finales más
según lo que suman tus decisiones.
"""
import json
import os

import pytest

import test_misiones
from juego import rutas
from juego.misiones import grupos_alguna, pares_cruce

CRUCES = ("cz2", "cz3", "cz4")


def _dialogos(p, mision):
    """Las frases de los pasos de diálogo de una misión que valen con lo decidido hasta ahora."""
    return [f for paso in mision["pasos"] if paso["tipo"] == "dialogo" and p.cumple_decision(paso) for _, f in paso["lineas"]]


def _decidido(p, **opciones):
    p.decisiones = {k: {"opcion": v, "texto": "prueba"} for k, v in opciones.items()}


def test_las_condiciones_se_escriben_como_texto_o_como_lista():
    assert pares_cruce("concejal:1, trono:3") == [("concejal", 1), ("trono", 3)]
    assert pares_cruce(["concejal:2", "cooperativa:2"]) == [("concejal", 2), ("cooperativa", 2)]
    assert pares_cruce("concejal:1; mal; trono:x; :2,  cooperativa : 2 ") == [("concejal", 1), ("cooperativa", 2)]      # lo que no se entiende se salta
    assert pares_cruce("") == [] and pares_cruce(None) == []
    assert grupos_alguna("fd2 fd3 fd4; vd2 vd3") == [["fd2", "fd3", "fd4"], ["vd2", "vd3"]]
    assert grupos_alguna([["a", "b"], "c d"]) == [["a", "b"], ["c", "d"]] and grupos_alguna(None) == [] and grupos_alguna(" ; ") == []


def test_cruzar_decisiones(robot):
    p = robot.nueva_partida()
    _decidido(p, concejal=1, trono=3)
    assert p.cumple_decision({"si_cruce": "concejal:1, trono:3"}) and not p.cumple_decision({"si_cruce": "concejal:1, trono:2"})
    assert not p.cumple_decision({"si_cruce": "concejal:1, cooperativa:1"})                 # la que no se ha tomado no cuenta
    assert p.cumple_decision({"si_cruce": "concejal:1, cooperativa:1", "si_cruce_min": 1})
    assert p.cumple_decision({"si_cruce": "concejal:2, cooperativa:1", "si_cruce_max": 0}) and not p.cumple_decision({"si_cruce": "concejal:1", "si_cruce_max": 0})
    assert p.cumple_decision({"si_cruce": "concejal:1, cooperativa:1, trono:1, trono:3", "si_cruce_min": 1, "si_cruce_max": 2})
    # se combina con la condición de siempre: hacen falta las dos
    assert p.cumple_decision({"si_clave": "concejal", "si_opcion": 1, "si_cruce": "trono:3"})
    assert not p.cumple_decision({"si_clave": "concejal", "si_opcion": 2, "si_cruce": "trono:3"})
    assert not p.cumple_decision({"si_clave": "concejal", "si_opcion": 1, "si_cruce": "trono:1"})
    assert p.cumple_decision({}) and p.cumple_decision({"si_cruce": ""})


def test_cada_rama_recuerda_las_otras(robot):
    p = robot.nueva_partida()
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    ecos = 0
    for ident in ("fd2", "fd3", "fd4", "vd2", "vd3", "sd2", "sd3", "sd4"):
        m = por_id[ident]
        extra = [paso for paso in m["pasos"] if paso.get("si_cruce")]
        assert extra and all(paso["tipo"] == "dialogo" for paso in extra), ident
        assert m["pasos"][-len(extra):] == extra, ident                 # van al final: no mueven de sitio los pasos que ya tenían voz grabada
        propia = m["si_clave"]
        assert all(c != propia for paso in extra for c, _ in pares_cruce(paso["si_cruce"])), ident       # hablan de otra rama, no de la suya
        ecos += len(extra)
    assert ecos >= 16
    # sin haber decidido nada en otros sitios, la misión se oye como siempre
    _decidido(p, concejal=1)
    base = _dialogos(p, por_id["fd2"])
    assert not any("inspectora de San Lucero" in f or "Villaseca" in f for f in base)
    _decidido(p, concejal=1, trono=3, cooperativa=2)
    con = _dialogos(p, por_id["fd2"])
    assert con[:len(base)] == base and len(con) == len(base) + 2
    assert any("inspectora de San Lucero" in f for f in con) and any("cobraste por la firma" in f for f in con) and not any("fotógrafo" in f for f in con)
    # y jugada de verdad, la frase se oye
    p.cfg["sucesos"] = False
    p.completadas += ["eo6", "fd1"]
    p.dar_arma("fusil", 300)
    n = len(robot.app.voz.registro)
    test_misiones._jugar_mision(robot, por_id["fd2"])
    oido = " ".join(robot.app.voz.registro[n:])
    assert "fd2" in p.completadas and "nombra también a nuestro concejal" in oido and "fotógrafo" not in oido


def test_la_mision_que_junta_las_ramas(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    cz1 = por_id["cz1"]
    disponibles = lambda: {m["id"] for m in p.misiones_disponibles()}
    p.completadas += ["fd1", "vd1", "sd1", "fd2", "vd2"]
    _decidido(p, concejal=1, cooperativa=1, trono=3)
    assert "cz1" not in disponibles()                                # falta cerrar la rama de San Lucero
    p.completadas.append("sd4")
    assert "cz1" in disponibles() and not (disponibles() & set(CRUCES))
    # las cartas dicen lo que toca, y solo eso
    frases = _dialogos(p, cz1)
    juntas = " ".join(frases)
    assert "el juicio del concejal empieza" in juntas and "caja de vino con tu nombre" in juntas and "una inspectora" in juntas
    assert "La redactora y la inspectora se llaman cada semana" in juntas                   # el cruce de dos ramas
    assert "sobre con billetes" not in juntas and "recaudación de la semana" not in juntas and "es una soga" not in juntas
    n = len(robot.app.voz.registro)
    test_misiones._jugar_mision(robot, cz1)
    assert "cz1" in p.completadas and "se llaman cada semana" in " ".join(robot.app.voz.registro[n:])
    # todo limpio: el final de la comarca
    assert disponibles() & set(CRUCES) == {"cz2"}
    p.dar_arma("fusil", 300)
    test_misiones._jugar_mision(robot, por_id["cz2"])
    assert "cz2" in p.completadas and p.decisiones["_final"]["texto"] == "Final de la comarca: en pie y en paz"


@pytest.mark.parametrize("decidido, toca", [
    ({"concejal": 1, "cooperativa": 1, "trono": 1}, "cz2"),
    ({"concejal": 1, "cooperativa": 1, "trono": 3}, "cz2"),
    ({"concejal": 1, "cooperativa": 2, "trono": 2}, "cz3"),
    ({"concejal": 3, "cooperativa": 1, "trono": 3}, "cz3"),
    ({"concejal": 2, "cooperativa": 2, "trono": 1}, "cz3"),
    ({"concejal": 2, "cooperativa": 2, "trono": 2}, "cz4"),
    ({"concejal": 3, "cooperativa": 2, "trono": 2}, "cz4"),
])
def test_el_final_depende_de_lo_que_suman_tus_decisiones(robot, decidido, toca):
    p = robot.nueva_partida()
    p.completadas += ["fd1", "vd1", "sd1", "fd2", "vd2", "sd2", "cz1"]
    _decidido(p, **decidido)
    assert {m["id"] for m in p.misiones_disponibles()} & set(CRUCES) == {toca}


def test_las_dieciocho_combinaciones_tienen_un_final_y_solo_uno(robot):
    p = robot.nueva_partida()
    p.completadas += ["fd1", "vd1", "sd1", "fd2", "vd2", "sd2", "cz1"]
    vistos = set()
    for a in (1, 2, 3):
        for b in (1, 2):
            for c in (1, 2, 3):
                _decidido(p, concejal=a, cooperativa=b, trono=c)
                finales = {m["id"] for m in p.misiones_disponibles()} & set(CRUCES)
                assert len(finales) == 1, (a, b, c, finales)
                vistos |= finales
                frases = _dialogos(p, next(m for m in p.datos["misiones"] if m["id"] == "cz1"))
                assert 6 <= len(frases) <= 7, (a, b, c, len(frases))             # tres de marco, una carta por sitio y, como mucho, un cruce
    assert vistos == set(CRUCES)


def test_el_final_del_poder_se_juega_entero(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    p.completadas += ["fd1", "vd1", "sd1", "fd3", "vd3", "sd3", "cz1"]
    _decidido(p, concejal=2, cooperativa=2, trono=2)
    p.dar_arma("fusil", 300)
    test_misiones._jugar_mision(robot, por_id["cz4"])                # el robot elige la última opción: quedarse con todo
    assert "cz4" in p.completadas and p.decisiones["reparto"]["opcion"] == 2 and p.decisiones["reparto"]["renta"] == 600
    assert p.decisiones["_final"]["texto"] == "Final del poder: la comarca tiene dueño"
    # repartiendo, no hay tiroteo: ese paso es solo de la otra opción
    _decidido(p, concejal=2, cooperativa=2, trono=2, reparto=1)
    tiroteo = next(paso for paso in por_id["cz4"]["pasos"] if paso["tipo"] == "eliminar")
    assert not p.cumple_decision(tiroteo)


def test_los_datos_y_el_editor(robot):
    d = json.load(open(os.path.join(rutas.DATOS, "misiones_extra2.json"), encoding="utf-8"))
    assert d["capitulos"]["14"] == "Cuentas cruzadas"
    por_id = {m["id"]: m for m in d["misiones"]}
    assert por_id["cz1"]["requiere_alguna"] == "fd2 fd3 fd4; vd2 vd3; sd2 sd3 sd4"
    for ident in CRUCES:
        m = por_id[ident]
        assert m["requiere"] == ["cz1"] and len(m["final"]) > 120 and m["final_titulo"].startswith("Final") and m["capitulo"] == 14
    lugares = robot.nueva_partida().lugares
    for ident in ("cz1",) + CRUCES:
        for paso in por_id[ident]["pasos"]:
            for l in [paso.get("lugar")] + list(paso.get("puntos", [])):
                assert l is None or l in lugares, (ident, l)
    from editor import esquema
    mision = {c["k"] for c in esquema.ESQUEMAS["mision"]["campos"]}
    paso = {c["k"] for c in esquema.ESQUEMAS["paso"]["campos"]}
    assert {"requiere_alguna", "si_cruce", "si_cruce_min", "si_cruce_max"} <= mision and {"si_cruce", "si_cruce_min", "si_cruce_max"} <= paso
    # el editor da por bueno el juego base con las misiones nuevas
    from editor import modelo
    cat = modelo.Catalogo()
    assert {"cz1", "cz2", "cz3", "cz4"} <= {m["id"] for m in cat.base["misiones"]}
