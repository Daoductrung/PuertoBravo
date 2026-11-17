"""Tarifas: los precios y las cantidades fijas del juego están en los datos (vida.json, tarifas), no escritos en el código."""
import glob
import importlib
import json
import os
import re

import pygame

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# p.precio("clave", defecto) o self.precio('clave', defecto): la clave y lo que vale si falta en los datos
USO = re.compile(r"""\.precio\(\s*(["'])([a-z0-9_]+)\1\s*,\s*([^()]+?)\s*\)""")
# claves que el código compone en vez de escribirlas enteras: módulo, clave y lo que vale por defecto
COMPUESTAS = [("loteria", f"loteria_premio_{n}", f"PREMIOS[{n}]") for n in (1, 2, 3, 4)] + \
             [("menus_lugares", "alquiler_" + m, f"ALQUILER['{m}']") for m in ("avioneta", "helicoptero")]


def _codigo():
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "juego", "*.py"))):
        with open(ruta, encoding="utf-8") as f:
            yield os.path.splitext(os.path.basename(ruta))[0], f.read()


def _tarifas():
    with open(os.path.join(RAIZ, "data", "datos", "vida.json"), encoding="utf-8") as f:
        return json.load(f)["tarifas"]


def _usos():
    """Cada uso de una tarifa en el código: (módulo, clave, valor por defecto ya calculado)."""
    usos = [(mod, clave, defecto) for mod, texto in _codigo() for _c, clave, defecto in USO.findall(texto)] + COMPUESTAS
    hechos = []
    for mod, clave, defecto in usos:
        if re.fullmatch(r"\d+", defecto):
            valor = int(defecto)
        else:                                                     # una constante del módulo, como PRECIO_TRANVIA o ALQUILER['avioneta']
            valor = eval(defecto, vars(importlib.import_module("juego." + mod)))
        hechos.append((mod, clave, valor))
    return hechos


def test_no_queda_ningun_pago_con_el_numero_escrito():
    malos = []
    for mod, texto in _codigo():
        for n, linea in enumerate(texto.splitlines(), 1):
            if re.search(r"\bpagar\(\s*\d", linea):
                malos.append(f"{mod}.py:{n}: {linea.strip()}")
    assert not malos, "\n".join(malos)


def test_las_tarifas_estan_bien_escritas():
    tarifas = _tarifas()
    ids = [t["id"] for t in tarifas]
    assert len(ids) == len(set(ids))                              # ninguna repetida
    for t in tarifas:
        assert set(t) == {"id", "nombre", "precio"}, t
        assert re.fullmatch(r"[a-z0-9_]+", t["id"]), t["id"]      # cortos, en minúsculas y sin tildes
        assert t["nombre"].strip() and isinstance(t["precio"], int) and t["precio"] >= 0, t


def test_cada_clave_del_codigo_esta_en_los_datos_con_el_mismo_valor():
    precios = {t["id"]: t["precio"] for t in _tarifas()}
    usos = _usos()
    assert len(usos) > 100
    for mod, clave, valor in usos:
        assert clave in precios, f"{mod}.py usa la tarifa {clave}, que no está en vida.json"
        assert precios[clave] == valor, f"{mod}.py: {clave} vale {valor} en el código y {precios[clave]} en vida.json"
    sin_uso = set(precios) - {clave for _m, clave, _v in usos}
    assert not sin_uso, f"tarifas de vida.json que no usa nadie: {sorted(sin_uso)}"


def test_precio_busca_en_los_datos_y_se_entera_de_los_cambios(robot):
    p = robot.nueva_partida()
    assert p.precio("cine", 12) == 12 and p.precio("no_existe", 7) == 7
    assert len(p.datos["tarifas"]) == len(_tarifas())
    next(t for t in p.datos["tarifas"] if t["id"] == "cine")["precio"] = 15       # cambia el precio de una
    assert p.precio("cine", 12) == 15
    p.datos["tarifas"].append({"id": "nueva", "nombre": "Nueva", "precio": 9})    # crece la lista
    assert p.precio("nueva", 1) == 9
    p.datos["tarifas"] = [{"id": "cine", "nombre": "Cine", "precio": 20}, {"id": "rota", "nombre": "Rota", "precio": "mucho"}, "basura"]
    assert p.precio("cine", 12) == 20 and p.precio("nueva", 1) == 1               # lista nueva: índice nuevo
    assert p.precio("rota", 5) == 5                                               # lo que no es un número no vale
    del p.datos["tarifas"]
    assert p.precio("cine", 12) == 12


def test_un_mod_cambia_una_tarifa_y_el_menu_dice_y_cobra_el_precio_nuevo(robot, tmp_path, monkeypatch):
    from juego import menus_extra, menus_juego, menus_lugares, mundo, rutas
    mod = {"info": {"nombre": "precios"},
           "tarifas": [{"id": "cine", "nombre": "Entrada de cine", "precio": 33},
                       {"id": "soborno_estrella", "nombre": "Soborno", "precio": 90},
                       {"id": "guardaespaldas_sueldo", "nombre": "Sueldo", "precio": 45},
                       {"id": "propina_mod", "nombre": "Una tarifa nueva, que no usa nadie", "precio": 1}]}
    (tmp_path / "precios.json").write_text(json.dumps(mod, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    try:
        robot.app.datos = mundo.cargar_datos()
        precios = {t["id"]: t["precio"] for t in robot.app.datos["tarifas"]}
        assert precios["cine"] == 33 and precios["propina_mod"] == 1 and precios["tranvia"] == 2      # sustituye, añade y deja las demás
        p = robot.nueva_partida()
        j = p.j
        # --- un precio fijo: lo dice la opción y es lo que cobra
        cine = next(l for l in p.lugares.values() if l.tipo == "cine")
        j.dinero = 100
        menus_lugares.cine(p, cine)
        m = robot.app.pila[-1]
        assert m.opciones[0].texto == "Ver la película de hoy: 33 euros"
        m.i = 0
        robot.tecla(pygame.K_RETURN)
        assert j.dinero == 67
        robot.app.cerrar(m)
        # --- un precio con fórmula: la tarifa es la base
        comisaria = next(l for l in p.lugares.values() if l.tipo == "comisaria")
        j.estrellas, j.dinero = 2, 500
        menus_juego._comisaria(p, comisaria)
        m = robot.app.pila[-1]
        assert m.opciones[0].texto == "Pagar un soborno para que dejen de buscarte: 180 euros"
        m.i = 0
        robot.tecla(pygame.K_RETURN)
        assert j.dinero == 320 and j.estrellas == 0
        robot.app.cerrar(m)
        # --- una cifra dicha en una ayuda y en lo que se oye al contratar
        j.dinero = 1000
        robot.app.voz.registro.clear()
        menus_extra.servicios(p)
        m = robot.app.pila[-1]
        assert any("dejan de cobrarte los 45 euros" in (o.ayuda or "") for o in m.opciones)
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto == "Llamar a un guardaespaldas: 350 euros")
        robot.tecla(pygame.K_RETURN)
        assert j.dinero == 650 and "Cobra 45 euros cada medianoche" in robot.dicho()
    finally:
        monkeypatch.undo()
        robot.app.datos = mundo.cargar_datos()


def test_el_editor_conoce_la_seccion_y_todos_sus_campos():
    from editor import esquema as E
    from juego import mundo
    assert "tarifas" in mundo.SECCIONES_VIDA
    seccion = next(s for s in E.SECCIONES if s[0] == "tarifas")
    assert seccion[1] == "Tarifas y precios" and seccion[2] in E.ESQUEMAS
    campos = {c["k"]: c for c in E.ESQUEMAS[seccion[2]]["campos"]}
    for t in _tarifas():
        assert set(t) <= set(campos), set(t) - set(campos)        # sabe editar cada campo de cada tarifa
    assert "no lo cambies" in campos["id"]["ayuda"]               # y avisa de que el identificador es del juego
    assert E.ESQUEMAS[seccion[2]]["resumen"]({"nombre": "Entrada de cine", "precio": 12}) == "Entrada de cine: 12 euros"
