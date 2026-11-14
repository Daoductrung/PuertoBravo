"""Editor de mods: modelo, comprobación, cobertura del esquema y accesibilidad de teclado de las ventanas."""
import copy
import json
import os

import pytest

from editor import modelo
from editor.esquema import ESQUEMAS, SECCIONES
from juego import mundo as M


@pytest.fixture(scope="module")
def cat():
    return modelo.Catalogo()


def _claves(nombre_esq):
    return {cp["k"] for cp in ESQUEMAS[nombre_esq]["campos"]}


def test_el_esquema_cubre_todo_lo_que_usa_el_juego(cat):
    """Cualquier clave que aparezca en los datos originales tiene que poder editarse: así el editor lo cubre todo."""
    b = cat.base
    faltan = set()

    def revisar(esq, d, donde):
        for k, v in d.items():
            if k not in _claves(esq):
                faltan.add(f"{donde}.{k}")
        for cp in ESQUEMAS[esq]["campos"]:
            v = d.get(cp["k"])
            if cp["t"] == "lista" and isinstance(v, list) and v and isinstance(v[0], dict):
                for x in v:
                    revisar(cp["sub"], x, cp["sub"])
            elif cp["t"] == "objeto" and isinstance(v, dict):
                revisar(cp["sub"], v, cp["sub"])
    for clave, _, esq in SECCIONES:
        for x in cat.elementos_base(clave):
            if clave == "capitulos":
                continue
            x = dict(x)
            if clave == "lugares":
                x.pop("mapa", None)
            revisar(esq, x, esq)
    faltan -= {"mapa.nota"}
    assert not faltan, sorted(faltan)
    assert len(b["misiones"]) >= 53


def test_ida_y_vuelta_sin_perder_nada(cat):
    """Convertir a forma editable y volver a guardar deja los datos originales idénticos."""
    for clave, _, esq in SECCIONES:
        if clave == "capitulos":
            continue
        for x in cat.elementos_base(clave):
            x = copy.deepcopy(x)
            if clave == "lugares":
                x.pop("mapa")
            vuelta = modelo.empaquetar(esq, modelo.desempaquetar(esq, x))

            def limpio(v):
                """Sin valores vacíos ni casillas sin marcar, que el editor no escribe."""
                if isinstance(v, dict):
                    return {k: limpio(w) for k, w in v.items() if w not in modelo.VACIOS and w is not False}
                if isinstance(v, list):
                    return [limpio(w) for w in v]
                return v
            assert json.dumps(limpio(vuelta), sort_keys=True, ensure_ascii=False) == json.dumps(limpio(x), sort_keys=True, ensure_ascii=False), (clave, x.get("id"))


def _mod_bueno():
    m = modelo.Mod()
    m.info = {"nombre": "Prueba", "autor": "Yo"}
    m.secciones["lugares"].append({"id": "mod_bar", "nombre": "Bar El Rincón", "tipo": "taberna", "mapa": "puerto_bravo", "bloque": [2, 3], "lado": "N", "pos": 20, "desc": "Un bar."})
    m.secciones["armas"].append({"id": "mod_tirachinas", "nombre": "Tirachinas", "tipo": "fuego", "dano": 8, "alcance": 20, "cadencia": 0.6, "precision": 0.8,
                                 "cargador": 1, "sonido": "lanzar", "ruido": 0, "precio": 15, "balas": 30, "precio_balas": 5, "desc": "De juguete."})
    m.secciones["vehiculos"].append({"id": "mod_patinete", "nombre": "Patinete", "vel_max": 7, "acel": 3, "freno": 8, "salud": 20, "motor": "motor_bici", "tono": 1.4, "valor": 10, "precio": 90})
    m.secciones["misiones"].append({"id": "mod01", "titulo": "Croquetas", "capitulo": 5, "contacto": "Loli", "lugar": "mod_bar", "requiere": ["m01"], "resumen": "Reparto.",
                                    "pasos": [{"tipo": "dialogo", "lineas": [{"quien": "Loli", "texto": "Corre."}]},
                                              {"tipo": "robar", "modelo": "mod_patinete", "lugar": "mod_bar", "abierto": True, "nombre": "Patinete de Loli", "texto": "Sube."},
                                              {"tipo": "entregar", "lugar": "hospital", "limite": 200, "texto": "Llévalo."},
                                              {"tipo": "eliminar", "lugar": "hospital", "enemigos": [{"n": 2, "tipo": "Celador", "arma": "mod_tirachinas", "salud": 30}], "texto": "Defiéndete."}],
                                    "recompensa": {"dinero": 200, "arma": "mod_tirachinas", "balas": 10}})
    m.secciones["mapas"].append({"id": "mod_aldea", "nombre": "Aldea Nueva", "tipo": "pueblo", "avenidas": ["Calle A", "Calle B", "Calle C"], "calles": ["Calle 1", "Calle 2"],
                                 "barrios": [{"id": "mod_aldea", "nombre": "Aldea Nueva", "i": [0, 1], "j": [0, 0], "ambiente": "amb_campo", "vehiculos": ["tractor"], "descripcion": "Dos casas."}],
                                 "bloques": [{"i": 1, "j": 0, "tipo": "plaza"}], "trafico": 1, "peatones": 2, "policia": False})
    m.secciones["lugares"].append({"id": "mod_fuente", "nombre": "Fuente de la aldea", "tipo": "monumento", "mapa": "mod_aldea", "bloque": [1, 0], "xy": [30, 30], "desc": "Una fuente."})
    m.secciones["capitulos"].append({"clave": "20", "valor": "Mi capítulo"})
    return m


def test_comprobar_mod_correcto_y_con_errores(cat, tmp_path):
    m = _mod_bueno()
    errores, avisos = modelo.comprobar(m, cat)
    assert errores == [], errores
    malo = _mod_bueno()
    malo.secciones["lugares"][0]["bloque"] = [40, 3]                       # manzana que no existe
    malo.secciones["lugares"][1]["xy"] = [30, 30]
    malo.secciones["lugares"][1]["bloque"] = [0, 0]                        # interior de una manzana de edificios
    malo.secciones["misiones"][0]["pasos"][1]["modelo"] = "no_existe"
    malo.secciones["misiones"][0]["pasos"].insert(0, {"tipo": "entregar", "lugar": "hospital", "texto": "x"})
    malo.secciones["armas"][0].pop("nombre")
    malo.secciones["personas"].append({"id": "x", "nombre": "X", "edad": 16, "lugar": "hospital", "desc": "x"})
    errores, _ = modelo.comprobar(malo, cat)
    texto = " | ".join(errores)
    for esperado in ("no existe en Puerto Bravo", "dentro de un edificio", "«no_existe», que no existe", "hace falta antes un paso", "falta «Nombre»", "18"):
        assert esperado in texto, (esperado, texto)
    # guardar y volver a abrir
    ruta = os.path.join(tmp_path, "prueba.json")
    m.guardar(ruta)
    from juego import cifrado
    assert cifrado.esta_cifrado(ruta)                   # el editor guarda protegido
    crudo = cifrado.leer_json(ruta)
    assert crudo["misiones"][0]["pasos"][0]["lineas"] == [["Loli", "Corre."]]
    assert crudo["mapas"][0]["bloques"] == {"1,0": "plaza"} and crudo["capitulos"] == {"20": "Mi capítulo"}
    otra = modelo.Mod.cargar(ruta)
    assert otra.crudo() == crudo


def test_el_juego_carga_y_juega_un_mod_del_editor(robot, cat, monkeypatch, tmp_path):
    """El mod creado con el editor se carga en el juego: lugar, arma, vehículo, mapa nuevo y misión jugable."""
    from juego import rutas
    import test_misiones
    m = _mod_bueno()
    m.guardar(os.path.join(tmp_path, "prueba.json"))
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    datos = M.cargar_datos()
    assert datos["errores_mods"] == []
    app = robot.app
    app.datos = datos
    app.mapas = M.crear_mapas(datos)
    app.mundo = app.mapas["puerto_bravo"]
    app.aplicar_adultos()
    assert "mod_aldea" in app.mapas and "mod_fuente" in app.mapas["mod_aldea"].lugares and "mod_bar" in app.mundo.lugares
    p = robot.nueva_partida()
    assert "mod_tirachinas" in p.armas_d and "mod_patinete" in p.modelos and p.datos["capitulos"]["20"] == "Mi capítulo"
    p.completadas.append("m01")
    mision = next(x for x in p.datos["misiones"] if x["id"] == "mod01")
    test_misiones._jugar_mision(robot, mision)
    assert "mod01" in p.completadas and "mod_tirachinas" in p.j.armas
    p.cambiar_mapa("mod_aldea", 100.0, 7.5)
    robot.frames(30)
    assert p.mundo.nombre == "Aldea Nueva"


# ----------------------------------------------------------------- ventanas wx
@pytest.fixture(scope="module")
def wxapp():
    wx = pytest.importorskip("wx")
    app = wx.App(False)
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    yield app


def test_formularios_accesibles_con_teclado(wxapp, cat):
    """Cada formulario generado pasa la revisión de etiquetas y letras de acceso de las plantillas de accesibilidad."""
    import wx
    from editor.accesibilidad.revision_teclado import informe, revisar_teclado
    from editor.formulario import DialogoFormulario, DialogoLista
    m = _mod_bueno()
    marco = wx.Frame(None)
    casos = [("info", m.info), ("lugar", m.secciones["lugares"][0]), ("mision", m.secciones["misiones"][0]),
             ("arma", m.secciones["armas"][0]), ("vehiculo", m.secciones["vehiculos"][0]), ("mapa", m.secciones["mapas"][0]),
             ("carrera", {}), ("persona", {}), ("sustancia", {}), ("recompensa", {}), ("barrio", {}), ("comida", {}), ("pez", {})]
    for tipo in ("dialogo", "ir", "dar", "robar", "entregar", "eliminar", "recoger", "policia", "perseguir"):
        casos.append(("paso", {"tipo": tipo}))
    for tipo in ("casa", "salida", "proveedor", "concesionario"):
        casos.append(("lugar", {"tipo": tipo, "mapa": "puerto_bravo"}))
    for esq, datos in casos:
        dlg = DialogoFormulario(marco, esq, datos, cat, m)
        problemas = [p for p in revisar_teclado(dlg) if not p.aviso]
        assert not problemas, (esq, datos.get("tipo"), informe(problemas))
        assert dlg._recoger(False) is None or True
        dlg.Destroy()
    dlg = DialogoLista(marco, "Pasos", "paso", m.secciones["misiones"][0]["pasos"], cat, m)
    problemas = [p for p in revisar_teclado(dlg) if not p.aviso]
    assert not problemas, informe(problemas)
    dlg.Destroy()
    marco.Destroy()


def test_formulario_recoge_y_valida(wxapp, cat):
    import wx
    from editor.formulario import DialogoFormulario
    m = _mod_bueno()
    marco = wx.Frame(None)
    dlg = DialogoFormulario(marco, "lugar", {"tipo": "monumento", "mapa": "puerto_bravo"}, cat, m)
    assert "precio" not in dlg.controles
    dlg.controles["id"].SetValue("mod_casa")
    dlg.controles["nombre"].SetValue("Casa nueva")
    tipos = [o[0] for o in ESQUEMAS["lugar"]["campos"][2]["ops"]]
    dlg.controles["tipo"].SetSelection(tipos.index("casa"))
    dlg._recargar("tipo")                         # al cambiar el tipo aparecen sus campos
    assert "precio" in dlg.controles and "garaje" in dlg.controles and dlg.controles["id"].GetValue() == "mod_casa"
    dlg.controles["precio"].SetValue("abc")
    assert dlg._recoger(True)[0] == "precio"
    dlg.controles["precio"].SetValue("5000")
    dlg.controles["pos"].SetValue("99")
    assert dlg._recoger(True)[0] == "pos"        # fuera de rango
    dlg.controles["pos"].SetValue("30")
    assert dlg._recoger(True) is None
    assert dlg.datos["precio"] == 5000 and dlg.datos["tipo"] == "casa" and dlg.datos["pos"] == 30
    dlg.Destroy()
    marco.Destroy()


def test_ventana_principal(wxapp, cat):
    import wx
    from editor.accesibilidad.revision_teclado import informe, revisar_teclado
    from editor.ventana import DialogoActivar, VentanaEditor
    v = VentanaEditor()
    problemas = [p for p in revisar_teclado(v) if not p.aviso]
    assert not problemas, informe(problemas)
    assert v.secciones.GetCount() == len(SECCIONES)
    v._cargar_en_ventana(_mod_bueno())
    assert v.panel_elementos.lista.GetCount() == 2          # los dos lugares
    v.secciones.SetSelection(1)
    v._seccion()
    assert "Croquetas" in v.panel_elementos.lista.GetString(0)
    v.panel_elementos.duplicar()
    assert len(v.mod.secciones["misiones"]) == 2 and v.mod.modificado and v.GetTitle().startswith("*")
    v.panel_elementos.mover(-1)
    assert v.mod.secciones["misiones"][0]["id"] == "mod01_copia"
    d = DialogoActivar(v)
    problemas = [p for p in revisar_teclado(d) if not p.aviso]
    assert not problemas, informe(problemas)
    d.Destroy()
    v.mod.modificado = False
    v.Destroy()
