"""Idiomas (1.7.2): el juego en inglés, el catálogo completo, las partidas entre idiomas, las voces y las guías por idioma,
la opción de idioma y los componentes.

Las pruebas van en español, como todas. Lo que hay que ver en inglés se lanza en un proceso aparte con
PUERTOBRAVO_IDIOMA=en, porque el idioma se fija al arrancar y los textos se traducen al cargarse los módulos.
"""
import json
import os
import subprocess
import sys

import pygame

from juego import config, i18n, rutas, voces, vozgen

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _en_ingles(codigo):
    """Ejecuta código Python en un proceso con el juego en inglés y devuelve lo que imprime."""
    env = dict(os.environ, PUERTOBRAVO_IDIOMA="en", PYTHONIOENCODING="utf-8", SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
               PYGAME_HIDE_SUPPORT_PROMPT="1")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, r.stderr[-3000:]
    return r.stdout


def test_el_catalogo_ingles_esta_completo_y_sin_huecos_rotos():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "i18n"))
    import fusionar
    cat = json.load(open(os.path.join(RAIZ, "data", "idiomas", "en", "textos.json"), encoding="utf-8"))["textos"]
    origen = json.load(open(os.path.join(RAIZ, "traduccion", "origen.json"), encoding="utf-8"))
    faltan = [k for k in origen if not cat.get(k)]
    assert not faltan, f"{len(faltan)} textos sin traducir: {faltan[:10]}"
    assert len(cat) > 16000
    malos = [k for k, v in cat.items() if fusionar.problema(k, v)]
    assert not malos, malos[:10]


def test_el_idioma_se_elige_por_el_sistema_y_la_opcion_manda(monkeypatch):
    monkeypatch.delenv("PUERTOBRAVO_IDIOMA", raising=False)
    monkeypatch.setattr(i18n, "_de_la_configuracion", lambda: "auto")
    for sistema, sale in (("es", "es"), ("en", "en"), ("de", "en"), ("", "es")):
        monkeypatch.setattr(i18n, "idioma_del_sistema", lambda s=sistema: s)
        assert i18n.elegir() == sale, sistema
    monkeypatch.setattr(i18n, "idioma_del_sistema", lambda: "es")
    assert i18n.elegir("en") == "en"                       # la opción manda sobre el sistema
    assert i18n.elegir("xx") == "es"                       # un idioma que no está: el de origen
    assert "en" in i18n.disponibles() and i18n.nombre_de("en") == "English" and i18n.nombre_de("it") == "Italiano"
    assert config.POR_DEFECTO["idioma"] == "auto"


def test_un_idioma_nuevo_se_reconoce_por_su_carpeta(monkeypatch, tmp_path):
    (tmp_path / "it").mkdir()
    (tmp_path / "it" / "textos.json").write_text(json.dumps({"textos": {"Opciones": "Opzioni"}}), encoding="utf-8")
    monkeypatch.setattr(i18n, "carpeta", lambda cod=None: str(tmp_path / cod) if cod else str(tmp_path))
    assert i18n.disponibles()["it"] == "Italiano"
    monkeypatch.setattr(i18n, "idioma_del_sistema", lambda: "it")
    monkeypatch.setattr(i18n, "_de_la_configuracion", lambda: "auto")
    monkeypatch.delenv("PUERTOBRAVO_IDIOMA", raising=False)
    assert i18n.elegir() == "it"


def test_el_juego_en_ingles_traduce_menus_datos_y_guias():
    out = _en_ingles(
        "from juego import i18n, mundo, voces, vozgen\n"
        "d = mundo.cargar_datos()\n"
        "print(i18n.actual())\n"
        "print(i18n.tr('Opciones'))\n"
        "print(d['ciudad']['lugares'][0]['nombre'])\n"
        "print(mundo.cargar_datos(traducir=False)['ciudad']['lugares'][0]['nombre'])\n"
        "print(i18n.doc('manual').endswith('manual_en.html'), i18n.doc('teclas').endswith('teclas_en.html'))\n"
        "print(vozgen.idioma(), vozgen.carpeta_voces_motor().endswith('voces_en'), vozgen.reparto()['protagonista'].get('dani_h'))\n")
    lineas = out.strip().splitlines()
    assert lineas[0] == "en" and lineas[1] == "Options"
    assert lineas[2] == "Grandma's Apartment" and lineas[3] == "Piso de la abuela"      # el editor y el servidor, los datos tal cual
    assert lineas[4] == "True True"
    assert lineas[5].startswith("en True prota_dani_h")


def test_una_partida_guardada_en_un_idioma_se_carga_en_otro(monkeypatch):
    cat = json.load(open(os.path.join(RAIZ, "data", "idiomas", "en", "textos.json"), encoding="utf-8"))["textos"]
    prenda = next(k for k in ("Vaqueros", "Camiseta blanca", "Sudadera") if k in cat) if any(k in cat for k in ("Vaqueros", "Camiseta blanca", "Sudadera")) else "Opciones"
    guardada_en_ingles = {"vestuario": {"prendas": [cat[prenda]]}, "nombre": cat["Opciones"], "notas": ["texto libre del jugador"]}
    i18n._inverso.clear()
    r = i18n.al_idioma_de_ahora(guardada_en_ingles, respetar=("nombre",))          # este proceso va en español
    assert r["vestuario"]["prendas"] == [prenda]
    assert r["nombre"] == cat["Opciones"]                                          # lo que se respeta, tal cual
    assert r["notas"] == ["texto libre del jugador"]
    assert i18n.original("Grandma's Apartment") == "Piso de la abuela"


def test_las_voces_van_por_carpeta_de_historia_e_idioma(monkeypatch, tmp_path):
    raiz = tmp_path / "voces"
    for carpeta, archivo in (("historia_principal_es", "m01_1_1.ogg"), ("historia_principal_en", "m01_1_1.ogg"), ("mi_mod", "mm_1_1.ogg")):
        (raiz / carpeta).mkdir(parents=True)
        (raiz / carpeta / archivo).write_bytes(b"x")
    monkeypatch.setattr(voces, "carpeta", lambda: str(raiz))
    for cod in ("es", "en"):
        monkeypatch.setattr(i18n, "actual", lambda c=cod: c)
        voces.refrescar()
        assert voces.buscar("m01", 0, 0).endswith(os.path.join(f"historia_principal_{cod}", "m01_1_1.ogg"))
        assert voces.buscar("mm", 0, 0)                     # una carpeta sin idioma vale para todos
    monkeypatch.setattr(i18n, "actual", lambda: "fr")
    voces.refrescar()
    assert voces.buscar("m01", 0, 0) is None               # en un idioma sin grabaciones, las dice el lector
    voces.refrescar()
    # las carpetas viejas sin idioma, si ya está la española, se quitan al arrancar
    (raiz / "historia_principal").mkdir()
    (raiz / "historia_principal" / "m01_1_1.ogg").write_bytes(b"vieja")
    (raiz / "propias").mkdir()
    assert voces.quitar_sin_idioma() == 1
    assert not (raiz / "historia_principal").exists() and (raiz / "propias").exists() and (raiz / "mi_mod").exists()
    assert voces.idioma_de_carpeta("bahia_del_ocaso_en") == "en" and voces.idioma_de_carpeta("mi_mod") is None


def test_las_voces_inglesas_estan_y_cuadran_con_las_espanolas():
    raiz = rutas.data("voces")
    es = {(h[:-3], f) for h in os.listdir(raiz) if h.endswith("_es") for f in os.listdir(os.path.join(raiz, h))}
    en = {(h[:-3], f) for h in os.listdir(raiz) if h.endswith("_en") for f in os.listdir(os.path.join(raiz, h))}
    assert len(es) > 1000
    assert len(en) > 1000, "faltan las voces inglesas de las escenas"
    historias_es = {h for h, _ in es}
    assert {h for h, _ in en} <= historias_es
    assert os.path.exists(os.path.join(vozgen.carpeta_motor(), "reparto_en.json"))
    assert os.path.isdir(os.path.join(vozgen.carpeta_motor(), "voces_en"))


def test_las_guias_van_por_idioma_y_las_viejas_se_quitan(monkeypatch, tmp_path):
    docs = rutas.data("docs")
    for g in ("manual", "teclas", "novedades", "cambiar_sonidos", "editor_mods", "servidor"):
        assert os.path.exists(os.path.join(docs, f"{g}_es.html")), g
        assert not os.path.exists(os.path.join(docs, f"{g}.html")), g
    for g in ("manual", "teclas", "novedades", "cambiar_sonidos", "editor_mods"):
        assert os.path.exists(os.path.join(docs, f"{g}_en.html")), f"falta {g}_en.html"
    d = tmp_path / "docs"
    d.mkdir()
    for n in ("manual.html", "manual_es.html", "propio.html"):
        (d / n).write_text("x", encoding="utf-8")
    monkeypatch.setattr(rutas, "data", lambda *p: str(tmp_path.joinpath(*p)))
    assert i18n.quitar_docs_sin_idioma() == 1
    assert sorted(os.listdir(d)) == ["manual_es.html", "propio.html"]


def test_las_guias_inglesas_no_tienen_espanol_colado():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "i18n"))
    import fugas
    for g in ("teclas", "cambiar_sonidos", "manual", "novedades", "editor_mods"):
        ruta = rutas.data("docs", f"{g}_en.html")
        malas = fugas.fugas(open(ruta, encoding="utf-8").read(), es_html=True)
        assert len(malas) <= 25, f"{g}_en.html: {len(malas)} frases que parecen españolas: {malas[:10]}"


def test_la_opcion_de_idioma_es_la_primera_de_opciones(robot):
    from juego import menus_juego
    app = robot.app
    menus_juego.opciones(app)
    m = app.pila[-1]
    assert m.opciones[0].texto.startswith("Idioma: automático")
    antes = app.cfg["idioma"]
    m.i = 0
    robot.tecla(pygame.K_RIGHT)
    assert app.cfg["idioma"] != antes and m.opciones[0].texto.startswith("Idioma: ")
    assert "Se aplica al volver a abrir el juego" in m.opciones[0].texto or app.cfg["idioma"] == "es"
    app.cfg["idioma"] = "auto"


def test_la_pantalla_de_componentes(robot, monkeypatch):
    from juego import componentes as C, menus_componentes as MC
    app = robot.app
    d = {"id": "idioma-it", "tipo": "idioma", "nombre": "Italiano", "version": 2, "file": "idioma-it_2.zip", "sha256": "a" * 64, "size": 3 * 1024 * 1024,
         "url": "https://ejemplo.invalid/idioma-it_2.zip", "requiere_juego": "1.0"}
    c = C.Componente(d, "https://ejemplo.invalid/componentes/componentes.json", "servidor")
    c2 = C.Componente(dict(d, id="sonidos-x", tipo="sonidos", nombre="Pack X", file="sonidos-x_1.zip", version=1, size=200 * 1024), "https://ejemplo.invalid/componentes/componentes.json", "servidor")
    c3 = C.Componente(dict(d, id="mod-y", tipo="mod", nombre="Mod Y", file="mod-y_3.zip", version=3, size=200 * 1024), "https://ejemplo.invalid/componentes/componentes.json", "servidor")
    publicados = {c.id: c, c2.id: c2, c3.id: c3}
    monkeypatch.setattr(C, "instalados", lambda: {"sonidos-x": 1, "mod-y": 2})
    app.cfg["comp_sin_interes"] = []
    m = MC.lista(app, publicados)
    textos = [o.texto for o in m.opciones]
    # primero las categorías: cada una con cuántos tiene; lo que ya está al día no cuenta
    assert textos[0].startswith("Instalar todo lo que te interesa: 2 componentes") and textos[-1] == "Volver", textos
    assert any(t.startswith("Idiomas: 1 para instalar o actualizar, 3 megas") for t in textos), textos
    assert any(t.startswith("Mods: 1 para instalar o actualizar") for t in textos), textos
    assert not any(t.startswith("Packs de sonidos") for t in textos), textos
    assert any(t.startswith("Categorías que te interesan: todas") for t in textos), textos
    # dentro de una categoría, solo los suyos
    mi = MC.categoria(app, publicados, "mod")
    ti = [o.texto for o in mi.opciones]
    assert any("Mod Y" in t and "actualización a la versión 3" in t and "200 kilobytes" in t for t in ti) and not any("Italiano" in t for t in ti), ti
    app.cerrar(mi)
    mi = MC.categoria(app, publicados, "idioma")
    assert any("Italiano" in o.texto and "nuevo" in o.texto and "3 megas" in o.texto for o in mi.opciones)
    app.cerrar(mi)
    # quien no quiere mods: no los ve, no cuentan en el aviso al arrancar, y se le dice que hay más en lo que no le interesa
    app.cfg["comp_sin_interes"] = ["mod"]
    assert [c.id for c in MC.pendientes(app, publicados)] == ["idioma-it"]
    m.refrescar(False)
    textos2 = [o.texto for o in m.opciones]
    assert not any(t.startswith("Mods") for t in textos2) and any("no te interesan hay 1 más" in t for t in textos2), textos2
    assert any(t.startswith("Categorías que te interesan: Idiomas, Voces, Documentación, Packs de sonidos") for t in textos2), textos2
    app.cfg["comp_sin_interes"] = []
    m.refrescar(False)
    textos = [o.texto for o in m.opciones]
    # con todo al día, no se abre ninguna lista: se dice
    monkeypatch.setattr(C, "instalados", lambda: {"sonidos-x": 1, "mod-y": 3, "idioma-it": 2})
    cima = app.pila[-1]
    assert MC.lista(app, publicados) is None and app.pila[-1] is cima
    monkeypatch.setattr(C, "instalados", lambda: {"sonidos-x": 1, "mod-y": 2})
    hechos, hay = [], {"sonidos-x": 1, "mod-y": 2}
    monkeypatch.setattr(C, "instalados", lambda: dict(hay))

    def instalar(comp, **k):
        hechos.append(comp.id)
        hay[comp.id] = comp.version
        return f"{comp.nombre} instalado, versión {comp.version}."
    monkeypatch.setattr(C, "instalar", instalar)
    m.i = next(k for k, t in enumerate(textos) if t.startswith("Idiomas"))
    robot.tecla(pygame.K_RETURN)                         # abre la categoría de los idiomas
    mc = app.pila[-1]
    mc.i = next(k for k, o in enumerate(mc.opciones) if "Italiano" in o.texto)
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert hechos == ["idioma-it"]
    assert "Se nota la próxima vez que abras el juego" in robot.dicho()
    m2 = app.pila[-1]                                    # la lista se rehace con lo que queda: solo los mods
    assert getattr(m2, "es_componentes", False) and m2 is not m and [o.texto for o in m2.opciones][0].startswith("Mods: 1 para instalar")
    assert m not in app.pila and mc not in app.pila
    m2.i = 0
    robot.tecla(pygame.K_RETURN)
    mc = app.pila[-1]
    mc.i = next(k for k, o in enumerate(mc.opciones) if "Mod Y" in o.texto)
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert hechos == ["idioma-it", "mod-y"]
    assert "Ya tienes todos los componentes al día" in robot.app.voz.registro[-1]            # y, sin nada más, lo dice
    assert not any(getattr(x, "es_componentes", False) for x in app.pila)
    # al arrancar se avisa en el menú principal
    while len(app.pila) > 1:
        app.cerrar(app.pila[-1])
    app.comp_aviso = 2
    MC.paso(app)
    assert "Hay componentes nuevos: 2" in robot.dicho()
    assert config.POR_DEFECTO["comp_auto"] is True


def test_en_ingles_esta_cada_voz_que_el_juego_va_a_buscar():
    """Cada frase de escena, en cada forma que el juego en inglés pide (personaje y género), tiene su grabación inglesa.
    En español hay más archivos: las frases que cambian con el género o el nombre en español y en inglés no, en inglés
    llevan uno solo."""
    out = _en_ingles(
        "from juego import mundo, voces\n"
        "d = mundo.cargar_datos()\n"
        "voces.refrescar()\n"
        "faltan, total = [], 0\n"
        "for m in d['misiones']:\n"
        "    for k, paso in enumerate(m.get('pasos', [])):\n"
        "        if paso.get('tipo') != 'dialogo':\n"
        "            continue\n"
        "        for n, linea in enumerate(paso.get('lineas', [])):\n"
        "            quien, texto = (linea.get('quien'), linea.get('texto')) if isinstance(linea, dict) else (linea[0], linea[1])\n"
        "            for forma, pj, g in voces.formas(quien, texto):\n"
        "                total += 1\n"
        "                if not voces.buscar(m['id'], k, n, forma):\n"
        "                    faltan.append(voces.nombre(m['id'], k, n) + forma)\n"
        "print(total, len(faltan), faltan[:20])\n")
    total, n, lista = out.strip().splitlines()[-1].split(" ", 2)
    assert int(total) > 1000
    assert int(n) == 0, f"faltan {n} voces inglesas: {lista}"


def test_los_componentes_que_trae_el_juego_no_se_anuncian_como_nuevos(monkeypatch, tmp_path):
    from juego import componentes as C
    (tmp_path / C.ARCHIVO_SERIE).write_text(json.dumps({"de_serie": {"idioma-en": 2, "mod-x": 1}}), encoding="utf-8")
    (tmp_path / C.ARCHIVO).write_text(json.dumps({"instalados": {"mod-x": 3, "voces-fr": 1}}), encoding="utf-8")
    monkeypatch.setattr(rutas, "data", lambda *p: str(tmp_path.joinpath(*p)))
    assert C.instalados() == {"idioma-en": 2, "mod-x": 3, "voces-fr": 1}          # lo de serie y lo instalado, lo más nuevo
    assert C.instalados(solo_propios=True) == {"mod-x": 3, "voces-fr": 1}
    C._apuntar("idioma-en", 4)
    assert json.load(open(tmp_path / C.ARCHIVO, encoding="utf-8"))["instalados"] == {"mod-x": 3, "voces-fr": 1, "idioma-en": 4}


def test_un_mod_que_llega_como_componente_trae_su_traduccion(monkeypatch, tmp_path):
    (tmp_path / "en" / "mods").mkdir(parents=True)
    (tmp_path / "en" / "textos.json").write_text(json.dumps({"textos": {"Opciones": "Options"}}), encoding="utf-8")
    (tmp_path / "en" / "mods" / "mi_mod.json").write_text(json.dumps({"textos": {"La laguna": "The lagoon", "Opciones": "NO"}}), encoding="utf-8")
    monkeypatch.setattr(i18n, "carpeta", lambda cod=None: str(tmp_path / cod) if cod else str(tmp_path))
    monkeypatch.delenv("PUERTOBRAVO_IDIOMA", raising=False)          # las pruebas van en español: aquí se pide el inglés
    antes = dict(i18n._estado)
    try:
        i18n.cargar("en")
        assert i18n.tr("La laguna") == "The lagoon" and i18n.tr("Opciones") == "Options"      # el del mod no pisa el del juego
    finally:
        i18n._estado.update(antes)


def test_el_mod_marisma_negra_no_viene_con_el_juego_y_su_componente_esta_completo():
    assert not os.path.exists(os.path.join(RAIZ, "data", "mods", "marisma_negra.json"))
    base = os.path.join(RAIZ, "componentes_extra", "mod_marisma_negra")
    spec = json.load(open(os.path.join(base, "componente.json"), encoding="utf-8"))
    assert spec["tipo"] == "mod" and spec["nombres"]["en"] and spec["descripciones"]["en"]
    mod = json.load(open(os.path.join(base, "marisma_negra.json"), encoding="utf-8"))
    cat = json.load(open(os.path.join(RAIZ, "traduccion", "en", "mods", "marisma_negra.json"), encoding="utf-8"))["textos"]
    lineas = [(l["texto"] if isinstance(l, dict) else l[1]) for m in mod["misiones"] for p in m["pasos"] if p["tipo"] == "dialogo" for l in p["lineas"]]
    assert len(lineas) >= 40 and all(t in cat for t in lineas)
