"""Vigilantes de los sonidos: todos los packs traen exactamente los mismos sonidos que los de serie, sus cuentas y sus
créditos cuadran con sus archivos, y todos los sonidos salen en Aprender los sonidos y en el volumen de cada sonido."""
import json
import os
import re

import numpy as np
import pygame
import pytest

from juego import audio, ayuda, catalogo_sonidos as cat, config, menus_juego, packs, rutas, sintesis

SERIE = os.path.join(rutas.PACKS, rutas.POR_DEFECTO)
# sonidos de la 1.7.1 que en los packs son grabaciones, y los que se quedan a propósito con el sonido del juego
GRABADOS_171 = ("megafono", "emisora", "timbre", "nevera", "cocina_cortar", "cocina_freir", "cocina_hervir", "plato_servido", "cesta",
                "amenaza_barrio", "barrio_perdido", "barrio_defendido")
TONOS_171 = ("chat_personaje", "chat_fuera", "chat_accion", "espera_servidor")


def _carpetas():
    return sorted(d for d in os.listdir(rutas.PACKS) if os.path.isdir(os.path.join(rutas.PACKS, d)) and not d.startswith("_"))


def _audios(carpeta):
    """[(nombre, archivo)] de una carpeta, sin pasar por el juego: lo que hay en el disco."""
    return sorted((os.path.splitext(f)[0], f) for f in os.listdir(os.path.join(rutas.PACKS, carpeta)) if f.lower().endswith(rutas.EXT_AUDIO))


def _serie():
    return sorted(n for n, _ in _audios(rutas.POR_DEFECTO))


def _igual_al_de_serie(carpeta, nombre):
    """El sonido del pack es el de serie (se admite la diferencia de redondeo de haberlo guardado dos veces)."""
    a = sintesis.leer_audio(os.path.join(SERIE, dict(_audios(rutas.POR_DEFECTO))[nombre]))
    b = sintesis.leer_audio(os.path.join(rutas.PACKS, carpeta, dict(_audios(carpeta))[nombre]))
    return len(a) == len(b) and float(np.max(np.abs(a - b))) < 3.0 / 32768


def _creditos(carpeta):
    with open(os.path.join(rutas.PACKS, carpeta, "CREDITOS.txt"), encoding="utf-8-sig") as f:
        return f.read()


def test_todos_los_packs_tienen_exactamente_los_mismos_sonidos():
    """Ni uno de más ni uno de menos, ni un sonido en dos formatos, en ninguna carpeta de data/sonidos."""
    serie = _serie()
    assert len(serie) >= 270 and len(serie) == len(set(serie))
    carpetas = _carpetas()
    assert {"por_defecto", "realista", "alternativo", "retro", "envolvente"} <= set(carpetas)
    for carpeta in carpetas:
        nombres = [n for n, _ in _audios(carpeta)]
        repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
        assert not repetidos, f"{carpeta}: en dos formatos: {repetidos}"
        faltan, sobran = sorted(set(serie) - set(nombres)), sorted(set(nombres) - set(serie))
        assert not faltan and not sobran, f"{carpeta}: faltan {faltan}; sobran {sobran}"
        assert len(nombres) == len(serie)
        for _, archivo in _audios(carpeta):
            assert os.path.getsize(os.path.join(rutas.PACKS, carpeta, archivo)) > 200, f"{carpeta}/{archivo} está vacío"
    # y el juego ve lo mismo que hay en el disco
    for pk in packs.listar():
        if not pk["id"].startswith("_"):
            assert pk["n"] == len(serie), f"{pk['id']}: el juego cuenta {pk['n']} sonidos"


def test_las_cuentas_y_los_creditos_de_cada_pack_cuadran_con_sus_archivos():
    serie = _serie()
    marca = sintesis.FORMATO + ": "
    for carpeta in _carpetas():
        if carpeta == rutas.POR_DEFECTO:
            continue
        with open(os.path.join(rutas.PACKS, carpeta, "pack.json"), encoding="utf-8") as f:
            meta = json.load(f)
        texto = _creditos(carpeta)
        assert meta.get("nombre") and meta.get("descripcion") and "CC0" in meta.get("licencia", "")
        if "grabaciones" not in meta:                       # el envolvente: cuenta sonidos y ambientes en estéreo
            assert meta["sonidos"] == len(serie)
            import soundfile as sf
            estereo = [n for n, a in _audios(carpeta) if sf.info(os.path.join(rutas.PACKS, carpeta, a)).channels == 2]
            assert meta["ambientes_en_estereo"] == len(estereo)
            for n in estereo:
                assert re.search(rf"^{n}: .+ Licencia CC0 .*https://", texto, re.M), f"{carpeta}: {n} sin crédito"
            for n in GRABADOS_171:
                assert re.search(rf"^{n}: .+Licencia CC0 \(dominio público\)\. https://bigsoundbank\.com/", texto, re.M), f"{carpeta}: {n} sin crédito"
            continue
        lineas = [x for x in texto.splitlines() if x.startswith("  ") and marca in x and " " not in x.strip().split(marca)[0]]
        nombres = [x.strip().split(marca)[0] for x in lineas]
        assert len(nombres) == len(set(nombres)), f"{carpeta}: sonidos con dos líneas de crédito"
        assert not [x for x in lineas if "original del juego" in x], f"{carpeta}: los originales van en su lista, no línea a línea"
        originales = texto.split("SONIDOS ORIGINALES DEL JUEGO")[1].splitlines()[2].strip().split(", ")
        assert sorted(nombres + originales) == serie, f"{carpeta}: los créditos no nombran todos los sonidos una vez"
        assert meta["grabaciones"] == len(nombres) and meta["originales_del_juego"] == len(originales)
        assert meta["grabaciones"] + meta["originales_del_juego"] == len(serie)
        assert f"Trae los {len(serie)} sonidos del juego: {len(nombres)} son grabaciones reales descargadas y {len(originales)} son el sonido" in texto
        assert "SONIDOS AÑADIDOS DESPUÉS" not in texto
        # lo que dicen los créditos es verdad: un «original» es el sonido de serie, y una grabación no lo es
        for n in originales:
            assert _igual_al_de_serie(carpeta, n), f"{carpeta}: {n} figura como original y no lo es"
        for n in GRABADOS_171:
            assert n in nombres and not _igual_al_de_serie(carpeta, n), f"{carpeta}: {n} debería ser una grabación"
        for n in TONOS_171:
            assert n in originales
        # las grabaciones sueltas dicen título, autor, licencia y página
        for x in lineas:
            if x.strip().split(marca)[0] in GRABADOS_171:
                assert re.search(r"«.+», de .+\. Licencia CC0 \(dominio público\)\. https://bigsoundbank\.com/\S+\.html\. Dura \d+,\d\d segundos\.$", x), x
        assert "https://bigsoundbank.com" in texto.split("QUÉ SONIDO SALE DE DÓNDE")[0]


def test_las_grabaciones_nuevas_tienen_duracion_y_nivel_razonables():
    """Sin oído, lo que se puede comprobar: ni largas ni mudas, sin silencio en los extremos, sin recorte, y en su sitio."""
    tope = {"cesta": 0.7, "emisora": 1.1, "plato_servido": 1.0, "megafono": 1.2, "nevera": 1.3, "cocina_cortar": 1.6, "cocina_freir": 2.5,
            "cocina_hervir": 2.5, "timbre": 2.7, "amenaza_barrio": 1.4, "barrio_perdido": 2.0, "barrio_defendido": 1.6}
    for carpeta in ("realista", "alternativo", "retro", "envolvente"):
        archivos = dict(_audios(carpeta))
        for n in GRABADOS_171:
            d = sintesis.leer_audio(os.path.join(rutas.PACKS, carpeta, archivos[n]))
            dur, pico = len(d) / sintesis.SR, float(np.max(np.abs(d)))
            assert 0.25 <= dur <= tope[n], f"{carpeta}/{n}: dura {dur:.2f}"
            assert 0.85 <= pico <= 0.91, f"{carpeta}/{n}: pico {pico:.2f}"
            assert packs.nivel(d) > 0.02, f"{carpeta}/{n}: apenas suena"
            oye = np.nonzero(np.abs(d) > 0.02 * pico)[0]
            assert oye[0] / sintesis.SR < 0.05 and (len(d) - oye[-1]) / sintesis.SR < 0.2, f"{carpeta}/{n}: silencio en los extremos"
            assert abs(float(d[0])) < 0.05 and abs(float(d[-1])) < 0.05, f"{carpeta}/{n}: empieza o acaba con chasquido"
    # el retro y el envolvente llevan aquí lo mismo que el realista
    for n in GRABADOS_171:
        a = open(os.path.join(rutas.PACKS, "realista", n + sintesis.FORMATO), "rb").read()
        for carpeta in ("retro", "envolvente"):
            assert open(os.path.join(rutas.PACKS, carpeta, n + sintesis.FORMATO), "rb").read() == a
    # cocinar: picar cabe antes de que entre el fuego, y el fuego antes del plato
    from juego import menus_cocina
    assert menus_cocina.Cocinando  # los tiempos de esa pantalla son 1,7 y 4,3 segundos
    assert tope["cocina_cortar"] <= 1.7 and tope["cocina_freir"] <= 4.3 - 1.7


def test_todos_los_sonidos_tienen_grupo_y_descripcion():
    """Ninguno cae en «Otros sonidos» ni se queda con la descripción genérica: así salen bien en la guía y en los menús."""
    for n in _serie():
        assert cat.grupo_de(n) < len(cat.GRUPOS), f"{n} no está en ningún grupo del catálogo"
        texto = cat.describir(n)
        assert texto != "Sonido del juego." and len(texto) >= 6 and texto.endswith("."), f"{n}: {texto!r}"
    titulos = [t for t, _ in menus_juego.grupos_de_sonidos(_serie())]
    assert "Otros sonidos" not in titulos and len(titulos) == len(set(titulos))
    assert sorted(s for _, lista in menus_juego.grupos_de_sonidos(_serie()) for s in lista) == _serie()
    # los de la radio y la música no son sonidos del juego
    assert menus_juego.grupos_de_sonidos(["radio_x", "musica_y"]) == [] and "radio_cambio" in _serie()


def test_aprender_los_sonidos_los_tiene_todos(app):
    """Todo archivo de los sonidos de serie sale en Aprender los sonidos, con nombre y explicación, y suena él solo."""
    serie = _serie()
    partes = menus_juego.sonidos_aprender(serie)
    assert partes[0][0] == "Los más importantes" and [s for s, _ in partes[0][1]] == [s for s, _, _ in ayuda.SONIDOS]
    vistos = {}
    for titulo, lista in partes[1:]:
        assert titulo != "Otros sonidos"
        for s, texto in lista:
            assert s not in vistos, f"{s} sale dos veces"
            vistos[s] = texto
            assert len(texto) >= 6 and texto.endswith(".") and texto != "Sonido del juego.", f"{s}: {texto!r}"
    assert sorted(vistos) == serie
    for s in GRABADOS_171 + TONOS_171:
        assert len(vistos[s]) > 20
    # el menú de verdad: grupos, y dentro cada sonido; Intro hace sonar ese y no el toque del menú
    menus_juego.sonidos(app)
    principal = app.pila[-1]
    assert principal.titulo == "Aprender los sonidos" and f"El juego tiene {len(serie)} sonidos" in app.voz.registro[-1]
    grupos = [o for o in principal.opciones if not o.texto.startswith("Volver")]
    assert len(grupos) == len(partes) and sum(int(o.texto.split(": ")[1].split()[0]) for o in grupos[1:]) == len(serie)
    sonados, original, total = [], app.mez.sonar, 0
    app.mez.sonar = lambda n, **k: (sonados.append((n, k.get("cat"))), original(n, **k))[1]
    try:
        for o in grupos[1:]:
            o.accion()
            m = app.pila[-1]
            assert m is not principal and m.opciones[-1].texto == "Volver"
            for op in m.opciones[:-1]:
                assert op.callado
                del sonados[:]
                op.accion()
                assert len(sonados) == 1 and sonados[0][1] == "interfaz" and vistos[sonados[0][0]] == op.texto
                total += 1
            app.cerrar(m)
    finally:
        app.mez.sonar = original
    assert total == len(serie)
    app.cerrar(principal)


def test_el_volumen_de_cada_sonido_los_tiene_todos(app):
    """En Opciones, Ajustar el volumen de cada sonido están todos, cada uno en su grupo, y se pueden oír y ajustar."""
    serie = _serie()
    assert set(serie) <= set(app.mez.sonidos)
    menus_juego.volumen_sonidos(app)
    principal = app.pila[-1]
    grupos = [o for o in principal.opciones if ": " in o.texto and o.texto.endswith(" sonidos")]
    assert not [o for o in grupos if o.texto.startswith("Otros sonidos")]
    assert sum(int(o.texto.split(": ")[1].split()[0]) for o in grupos) == len([s for s in app.mez.sonidos if s == "radio_cambio" or not s.startswith(("radio_", "musica_"))])
    archivos = set()
    for o in grupos:
        o.accion()
        m = app.pila[-1]
        for op in m.opciones[:-1]:
            assert op.ajuste is not None and op.accion is not None and "por ciento" in op.texto
            archivos.add(re.match(r"Archivo (\S+)\.", op.ayuda).group(1))
        app.cerrar(m)
    assert set(serie) <= archivos
    app.cerrar(principal)
    # cada sonido nuevo, en el grupo que le toca
    grupo = {s: t for t, lista in menus_juego.grupos_de_sonidos(serie) for s in lista}
    for s in ("cesta", "nevera", "cocina_cortar", "cocina_freir", "cocina_hervir", "plato_servido"):
        assert grupo[s] == "La compra y la cocina"
    for s in TONOS_171:
        assert grupo[s] == "Jugar con amigos y en un servidor"
    for s in ("megafono", "emisora"):
        assert grupo[s] == "Policía y búsqueda"
    for s in ("amenaza_barrio", "barrio_perdido", "barrio_defendido"):
        assert grupo[s].endswith("territorios")
    assert grupo["beber"] == grupo["comer"] and grupo["timbre"].startswith("Puertas")


def test_ningun_sonido_queda_fuera_de_los_volumenes_de_opciones(app):
    """Todo lo que suena pasa por una de las cuatro clases de volumen del mezclador, cada una con su control en Opciones
    (además del volumen general y del de las señales de ayuda), y no hay en el código ninguna clase que no exista."""
    clases = {"efectos", "ambiente", "musica", "interfaz"}
    assert clases | {"maestro", "senales"} == set(app.mez.vols)
    for clave in ("vol_maestro", "vol_efectos", "vol_ambiente", "vol_musica", "vol_interfaz", "vol_senales"):
        assert clave in config.POR_DEFECTO
    assert audio.Canal().cat in clases                      # la clase de quien no dice ninguna
    usadas = set()
    carpeta = os.path.dirname(audio.__file__)
    for f in os.listdir(carpeta):
        if f.endswith(".py"):
            with open(os.path.join(carpeta, f), encoding="utf-8") as fh:
                usadas |= set(re.findall(r'\bcat="([^"]*)"', fh.read()))
    assert usadas and usadas <= clases, usadas - clases
    # y Opciones, Sonido y música, tiene un control para cada una
    fuente = open(menus_juego.__file__, encoding="utf-8").read()
    for clave in ("vol_maestro", "vol_efectos", "vol_ambiente", "vol_musica", "vol_interfaz", "vol_senales"):
        assert f'vol("{clave}"' in fuente, clave
    assert "Ajustar el volumen de cada sonido" in fuente
    # un sonido ajustado por el jugador cambia de verdad, también uno de los nuevos
    antes = packs.nivel(app.mez.sonidos["timbre"])
    packs.ajustar(app.mez, app.cfg, "timbre", -1)
    assert packs.nivel(app.mez.sonidos["timbre"]) < antes
    app.cfg["vol_sonidos"].clear()
    app.recargar_sonidos()
    assert abs(packs.nivel(app.mez.sonidos["timbre"]) / antes - 1.0) < 0.02


def test_la_documentacion_cuenta_lo_de_los_sonidos():
    manual = open(rutas.data("docs", "manual.html"), encoding="utf-8").read()
    guia = open(rutas.data("docs", "cambiar_sonidos.html"), encoding="utf-8").read()
    assert "Aprender los sonidos" in manual and "Los más importantes" in manual
    assert "BigSoundBank" in guia or "bigsoundbank" in guia
    for n in _serie():
        assert f"<code>{n}</code>" in guia or f">{n}<" in guia or n in guia, f"la guía de sonidos no nombra {n}"
    assert "Otros sonidos" not in guia
