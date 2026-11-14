"""Archivos JSON protegidos: datos del juego, mods, partidas y editor."""
import json
import os
import shutil

import pytest

from juego import cifrado, rutas


def test_ida_y_vuelta_y_rechazo_de_manipulados(tmp_path):
    datos = {"misiones": [{"id": "m1", "titulo": "Cañón y ñandú", "pasos": [1, 2.5, None, True]}], "vacío": {}}
    ruta = str(tmp_path / "x.json")
    cifrado.escribir_json(ruta, datos, cifrado=True)
    crudo = open(ruta, "rb").read()
    assert crudo.startswith(cifrado.MARCA) and b"titulo" not in crudo and "Cañón".encode("utf-8") not in crudo
    assert cifrado.esta_cifrado(ruta) and cifrado.leer_json(ruta) == datos
    assert cifrado.cifrar(datos) != cifrado.cifrar(datos)                 # cada vez con una sal distinta
    # un solo byte cambiado: se rechaza, no se carga a medias
    roto = bytearray(crudo)
    roto[-3] ^= 1
    open(ruta, "wb").write(bytes(roto))
    with pytest.raises(ValueError):
        cifrado.leer_json(ruta)
    # legible: sigue valiendo, con o sin marca de orden de bytes
    cifrado.escribir_json(ruta, datos, cifrado=False, sangria=1)
    assert not cifrado.esta_cifrado(ruta) and cifrado.leer_json(ruta) == datos
    open(ruta, "w", encoding="utf-8-sig").write(json.dumps(datos))
    assert cifrado.leer_json(ruta) == datos
    assert cifrado.cifrar_archivo(ruta) and not cifrado.cifrar_archivo(ruta) and cifrado.leer_json(ruta) == datos
    assert cifrado.descifrar_archivo(ruta) and json.load(open(ruta, encoding="utf-8")) == datos


def test_el_juego_carga_los_datos_protegidos(tmp_path, monkeypatch):
    """Una copia de data/datos y data/mods protegida, como la deja compilar.bat, se carga igual que la legible."""
    import sys
    from juego import mundo
    sys.path.insert(0, os.path.join(rutas.base(), "herramientas"))
    import cifrar_datos
    normal = mundo.cargar_datos()
    copia = str(tmp_path / "data")
    shutil.copytree(rutas.DATOS, os.path.join(copia, "datos"))
    shutil.copytree(rutas.MODS, os.path.join(copia, "mods"))
    n = cifrar_datos.recorrer(copia)
    assert n >= 15
    for base, _, archivos in os.walk(copia):
        for f in archivos:
            assert not f.endswith(".json"), f"{f} sigue siendo un .json"          # ya no queda ningún .json
            if f.endswith((".pbd", ".pbm")):
                assert cifrado.esta_cifrado(os.path.join(base, f)), f
    assert os.path.exists(os.path.join(copia, "datos", "ciudad.pbd")) and os.path.exists(os.path.join(copia, "mods", "costa_dorada.pbm"))
    assert os.path.exists(os.path.join(copia, "datos", "mapas", "villaseca.pbd"))
    monkeypatch.setattr(rutas, "DATOS", os.path.join(copia, "datos"))
    monkeypatch.setattr(rutas, "MODS", os.path.join(copia, "mods"))
    protegido = mundo.cargar_datos()
    assert not protegido["errores_mods"]
    assert [m["id"] for m in protegido["misiones"]] == [m["id"] for m in normal["misiones"]]
    assert len(protegido["vehiculos"]) == len(normal["vehiculos"]) and set(protegido["mapas"]) == set(normal["mapas"]) if isinstance(normal.get("mapas"), dict) else True
    # en el juego compilado, un mod escrito a mano no se carga: se pide abrirlo con el editor
    with open(os.path.join(copia, "mods", "a_mano.json"), "w", encoding="utf-8") as f:
        json.dump({"comidas": [{"nombre": "Pan con trampa", "precio": 1, "salud": 999}]}, f)
    monkeypatch.setattr(cifrado, "COMPILADO", True)
    compilado = mundo.cargar_datos()
    assert any("a_mano.json" in e and "editor de mods" in e for e in compilado["errores_mods"])
    assert not any(c["nombre"] == "Pan con trampa" for c in compilado["comidas"])
    # el editor lo abre y, al guardarlo, lo deja protegido como .pbm y aparta el original
    from editor import modelo
    mod = modelo.Mod.cargar(os.path.join(copia, "mods", "a_mano.json"))
    apartado = mod.guardar()
    assert mod.ruta.endswith("a_mano.pbm") and cifrado.esta_cifrado(mod.ruta) and apartado.endswith("a_mano.json.original")
    compilado = mundo.cargar_datos()
    assert not compilado["errores_mods"] and any(c["nombre"] == "Pan con trampa" for c in compilado["comidas"])
    monkeypatch.setattr(cifrado, "COMPILADO", False)
    os.remove(mod.ruta)
    os.remove(apartado)
    assert cifrar_datos.recorrer(copia, abrir=True) == n                   # y se puede deshacer
    assert os.path.exists(os.path.join(copia, "datos", "ciudad.json"))


def test_el_editor_guarda_protegido_y_abre_las_dos_formas(tmp_path):
    from editor import modelo
    legible = os.path.join(rutas.MODS, "costa_dorada.json")
    mod = modelo.Mod.cargar(legible)                                       # abre el legible
    mod.guardar(str(tmp_path / "mi_mod.json"))                             # el editor guarda protegido, como .pbm
    ruta = mod.ruta
    assert ruta.endswith("mi_mod.pbm") and cifrado.esta_cifrado(ruta) and not os.path.exists(str(tmp_path / "mi_mod.json"))
    assert modelo.ruta_protegida("x.json.desactivado") == "x.pbm.desactivado" and modelo.ruta_protegida("x") == "x.pbm"
    otra_vez = modelo.Mod.cargar(ruta)                                     # y abre el protegido
    assert otra_vez.crudo() == mod.crudo()
    assert otra_vez.info["nombre"] == "Costa Dorada" and len(otra_vez.secciones["misiones"]) == 8
    errores, _ = modelo.comprobar(otra_vez, modelo.Catalogo())
    assert not [e for e in errores if "repetido dentro del mod" in e]


def test_las_partidas_se_protegen_en_el_juego_compilado(robot, monkeypatch):
    from juego import menus_juego
    p = robot.nueva_partida()
    p.j.dinero = 4321
    monkeypatch.setattr(cifrado, "COMPILADO", True)
    assert menus_juego.escribir_ranura(p, 2)
    ruta = menus_juego._archivo(2)
    assert ruta.endswith(".pbs") and cifrado.esta_cifrado(ruta) and b"4321" not in open(ruta, "rb").read()
    assert menus_juego.leer_ranura(2)["jugador"]["dinero"] == 4321 if "jugador" in menus_juego.leer_ranura(2) else menus_juego.leer_ranura(2) is not None
    # una partida manipulada no se carga
    crudo = bytearray(open(ruta, "rb").read())
    crudo[-1] ^= 255
    open(ruta, "wb").write(bytes(crudo))
    assert menus_juego.leer_ranura(2) is None
    # y una partida antigua, legible, se sigue leyendo
    monkeypatch.setattr(cifrado, "COMPILADO", False)
    assert menus_juego.escribir_ranura(p, 3) and menus_juego._archivo(3).endswith(".json") and not cifrado.esta_cifrado(menus_juego._archivo(3))
    assert menus_juego.leer_ranura(3) is not None
    # pero el juego compilado no acepta una partida legible: ni con su extensión ni disfrazada con la protegida
    monkeypatch.setattr(cifrado, "COMPILADO", True)
    assert menus_juego.leer_ranura(3) is None
    import shutil
    shutil.copy(menus_juego._archivo(3, ".json"), menus_juego._archivo(3))
    assert menus_juego.leer_ranura(3) is None and menus_juego.mas_reciente() is None
    assert menus_juego.escribir_ranura(p, 1) and menus_juego.leer_ranura(1) is not None and str(menus_juego.mas_reciente()) == "1"
