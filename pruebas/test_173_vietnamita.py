"""Idiomas (1.7.3): el vietnamita, que llega primero como componente para la 1.7.2 y viene de serie desde la 1.7.3.

El catálogo tiene que valer tal cual con el juego 1.7.2, que es el que lo instala como componente: los mismos huecos que el
español, las marcas de género que entiende la 1.7.2 y la clave de delante del «=» intacta. Lo que hay que ver en otro
idioma se lanza en un proceso aparte, porque el idioma se fija al arrancar.
"""
import json
import os
import re
import string
import subprocess
import sys

from juego import genero, i18n

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCA_172 = re.compile(r"\[([^\[\]|]*)\|([^\[\]|]*)\]")         # la marca de género tal como la lee el juego 1.7.2
GENERO_ES = {"o", "a", "e", "os", "as"}


def _catalogo(cod):
    return json.load(open(os.path.join(RAIZ, "data", "idiomas", cod, "textos.json"), encoding="utf-8"))["textos"]


def _en(cod, codigo):
    env = dict(os.environ, PUERTOBRAVO_IDIOMA=cod, PYTHONIOENCODING="utf-8", SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
               PYGAME_HIDE_SUPPORT_PROMPT="1")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, r.stderr[-3000:]
    return r.stdout


def _huecos(t):
    return {f for _, f, _, _ in string.Formatter().parse(t) if f is not None}


def test_el_vietnamita_esta_completo_y_se_reconoce():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "i18n"))
    import fusionar
    cat = _catalogo("vi")
    origen = json.load(open(os.path.join(RAIZ, "traduccion", "origen.json"), encoding="utf-8"))
    faltan = [k for k in origen if not cat.get(k)]
    assert not faltan, f"{len(faltan)} textos sin traducir: {faltan[:10]}"
    assert not [k for k, v in cat.items() if fusionar.problema(k, v)]
    assert i18n.disponibles().get("vi") == "Tiếng Việt"


def test_cada_traduccion_vale_en_el_juego_1_7_2():
    """Cada idioma: ni un hueco que el código no rellene, los %s en el mismo orden, la clave de delante del «=» y las
    marcas de género con dos formas, que son las que entiende la 1.7.2."""
    for cod in ("vi", "en"):
        malos = []
        for k, v in _catalogo(cod).items():
            if _huecos(v) - _huecos(k) - GENERO_ES:
                malos.append(("hueco", k, v))
            if ("%s" in k or "%d" in k) and re.findall(r"%[sd]", k.replace("%%", "")) != re.findall(r"%[sd]", v.replace("%%", "")):
                malos.append(("%", k, v))
            m = re.match(r"^([a-z_0-9]+)=", k)
            if m and not v.startswith(m.group(1) + "="):
                malos.append(("clave", k, v))
            if any("|" in b and not MARCA_172.fullmatch(b) for b in re.findall(r"\[[^\[\]]*\]", v)):
                malos.append(("género", k, v))
        assert not malos, (cod, malos[:10])


def test_en_vietnamita_las_guias_son_las_inglesas_mientras_no_esten_traducidas():
    out = _en("vi", "from juego import i18n\nprint(i18n.actual(), i18n.tr('Opciones'), i18n.doc('manual').replace(chr(92), '/').rsplit('/', 1)[-1])\n")
    cod, opciones, manual = out.split()[0], out.split()[1:-1], out.split()[-1]
    assert cod == "vi" and " ".join(opciones) == _catalogo("vi")["Opciones"]
    assert manual in ("manual_vi.html", "manual_en.html")


def test_los_estilos_de_ropa_traducidos_conservan_su_clave():
    out = _en("en", "from juego import vestuario\nprint(sorted(vestuario.ESTILOS))\nprint(vestuario.ESTILOS['abrigo'])\n")
    claves, abrigo = out.strip().splitlines()
    assert eval(claves) == sorted(["abrigo", "calle", "deporte", "elegante", "fiesta", "playa", "tactica", "trabajo"])
    assert abrigo == "warm"


def test_en_ingles_las_palabras_inglesas_no_se_tocan():
    out = _en("en", "from juego import palabras\nprint(palabras.pulir('social media, shark fin. Head este.'))\n")
    assert out.strip() == "social media, shark fin. Head east."


def test_marcas_de_genero_con_mas_de_dos_formas():
    assert genero.resolver("Bienvenid[o|a]", "m") == "Bienvenida"
    assert genero.resolver("[anh|chị|bạn]", "h") == "anh" and genero.resolver("[anh|chị|bạn]", "m") == "bạn"
    assert genero.resolver("[sin barra] y [o|a]", "h") == "[sin barra] y o"


def test_cada_idioma_se_dice_en_el_tuyo_y_en_el_suyo():
    assert i18n.nombre_en("vi", "es") == "vietnamita (Tiếng Việt)"
    assert i18n.nombre_en("en", "es") == "inglés (English)"
    assert i18n.nombre_en("vi", "en") == "Vietnamese (Tiếng Việt)"
    assert i18n.nombre_en("en", "en") == "English" and i18n.nombre_en("vi", "vi") == "Tiếng Việt"
    assert i18n.nombre_en("es", "vi") == "tiếng Tây Ban Nha (Español)"
    assert i18n.idioma_en("vi", "es") == "vietnamita" and i18n.idioma_en("es", "en") == "Spanish"


def test_los_identificadores_de_los_datos_no_se_traducen():
    """«pesca», «puerto», «agente» o «radar» son palabras del catálogo y también identificadores: traducidos, el código no
    encontraría los puntos de pesca, el barrio del puerto, la policía ni el ejercicio del radar."""
    codigo = ("from juego import mundo\nd = mundo.cargar_datos()\n"
              "print(sorted({l.get('tipo') for l in d['ciudad']['lugares'] if l.get('tipo') == 'pesca'}))\n"
              "print([b['id'] for b in d['ciudad']['barrios'] if b['id'] == 'puerto'])\n"
              "print([t['id'] for t in d['tipos_enemigo'] if t['id'] == 'agente'])\n"
              "print([p['exige'] for m in d['misiones'] for p in m.get('pasos', []) if p.get('exige')])\n"
              "print(d['ciudad']['lugares'][0]['nombre'])\n")
    for cod in ("en", "vi"):
        lineas = _en(cod, codigo).strip().splitlines()
        assert lineas[:4] == ["['pesca']", "['puerto']", "['agente']", "['radar']"], (cod, lineas)
        assert lineas[4] == _catalogo(cod)["Piso de la abuela"]            # los nombres sí se traducen


def test_una_partida_inglesa_de_antes_recupera_sus_identificadores():
    out = _en("en", "from juego import i18n\n"
                    "g = {'barrios': ['port'], 'prendas': ['Jeans'], 'pescado': [{'nombre': 'x', 'tipo': 'fishing'}], 'nombre': 'port'}\n"
                    "i18n.al_idioma_de_ahora(g, respetar=('nombre',))\nprint(g['barrios'], g['pescado'][0]['tipo'], g['nombre'])\n")
    assert out.strip() == "['puerto'] pesca port"


def test_cada_componente_dice_que_es_en_cada_idioma():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
    import publicar_componentes as P
    d = P.presentar("idioma-vi", "idioma", RAIZ)
    assert d["nombres"]["es"] == "vietnamita (Tiếng Việt)" and d["nombres"]["en"] == "Vietnamese (Tiếng Việt)" and d["nombres"]["vi"] == "Tiếng Việt"
    assert d["descripcion"].startswith("El juego entero en vietnamita") and "Opciones, Idioma" in d["descripcion"]
    assert d["descripciones"]["en"].startswith("The whole game in Vietnamese")
    pack = P.presentar("sonidos-retro", "sonidos", RAIZ)
    assert pack["nombres"]["en"] == "Retro" and "Pack de sonidos" in pack["descripcion"] and pack["descripciones"]["en"].startswith("Old console sounds")
    mod = P.presentar("mod-motor_y_asfalto", "mod", RAIZ)
    assert mod["nombre"] == "Motor y asfalto" and mod["nombres"]["en"] == "Engine and Asphalt" and "Control M" in mod["descripcion"]


def test_el_mod_marisma_negra_tiene_traduccion_vietnamita_completa():
    base = os.path.join(RAIZ, "componentes_extra", "mod_marisma_negra")
    spec = json.load(open(os.path.join(base, "componente.json"), encoding="utf-8"))
    assert spec["nombres"].get("vi") and spec["descripciones"].get("vi")
    mod = json.load(open(os.path.join(base, "marisma_negra.json"), encoding="utf-8"))
    cat_vi = json.load(open(os.path.join(RAIZ, "traduccion", "vi", "mods", "marisma_negra.json"), encoding="utf-8"))["textos"]
    lineas = [(l["texto"] if isinstance(l, dict) else l[1]) for m in mod["misiones"] for p in m["pasos"] if p["tipo"] == "dialogo" for l in p["lineas"]]
    assert len(lineas) >= 40 and all(t in cat_vi for t in lineas)
    assert any(a.get("destino") == "data/idiomas/vi/mods/marisma_negra.json" for a in spec.get("archivos", []))
