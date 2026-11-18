"""Vigilante de las voces que trae el juego: toda frase de una escena tiene su grabación, en todas las formas que
hacen falta para los cuatro personajes y los dos géneros; no hay grabaciones sueltas que ya no sean de ninguna frase;
todas tienen el mismo formato; y quien nombra al protagonista tiene voz en el generador, para el personaje propio.

El criterio: llevan voz grabada las frases de los pasos de diálogo de las misiones (historia, tutoriales, encargos y
las historias añadidas que trae el juego). Todo lo demás lo dice el lector de pantalla.
"""
import os

import pytest

from juego import mundo, rutas, voces, vozgen

SERIE = ("historia_principal", "bahia_del_ocaso", "costa_dorada", "isla_de_los_vientos", "motor_y_asfalto", "noches_de_neon",
         "oficios_y_recados", "penas_altas", "valdeolmos")


def _frases():
    """Cada frase de escena con sus formas: (archivo sin extensión, quién, texto para Dani en masculino)."""
    for m in mundo.cargar_datos()["misiones"]:
        if m.get("sin_voz"):                 # misiones que el juego trae sin grabar a propósito (el buen camino): las dice el lector
            continue
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            for n, linea in enumerate(paso.get("lineas", [])):
                quien, texto = (linea.get("quien"), linea.get("texto")) if isinstance(linea, dict) else (linea[0], linea[1])
                for forma, pj, g in voces.formas(quien, texto):
                    yield voces.nombre(m["id"], k, n) + forma, quien, texto


def _de_serie():
    """Las grabaciones que trae el juego: {nombre sin extensión, en minúsculas: ruta}. Las del jugador no cuentan."""
    out = {}
    for h in SERIE:
        d = os.path.join(rutas.DATA, "voces", h)
        if os.path.isdir(d):
            for n in os.listdir(d):
                if os.path.splitext(n)[1].lower() in voces.EXT:
                    out[os.path.splitext(n)[0].lower()] = os.path.join(d, n)
    return out


@pytest.fixture(scope="module")
def serie():
    s = _de_serie()
    if "m01_1_1@alex" not in s:
        pytest.skip("en esta copia no están las voces del juego")
    return s


def test_toda_frase_de_escena_tiene_su_voz_en_todas_sus_formas(serie):
    esperadas = [a for a, _, _ in _frases()]
    assert len(esperadas) >= 1100 and len(set(esperadas)) == len(esperadas)
    faltan = [a for a in esperadas if a.lower() not in serie]
    assert not faltan, f"frases sin voz grabada ({len(faltan)}): {faltan[:30]}"


def test_no_hay_voces_sin_frase(serie):
    """Una grabación que no es de ninguna frase de hoy: de un paso que ya no es diálogo, de una frase quitada o de una forma que ya no toca."""
    esperadas = {a.lower() for a, _, _ in _frases()}
    sobran = sorted(set(serie) - esperadas)
    assert not sobran, f"voces sin frase ({len(sobran)}): {sobran[:30]}"
    raiz = os.path.join(rutas.DATA, "voces")                     # y ninguna carpeta que no sea de una historia del juego o la del jugador
    assert {n for n in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, n))} - {voces.PROPIAS} <= set(SERIE)


def test_las_voces_tienen_todas_el_mismo_formato_y_una_duracion_creible(serie):
    """OGG, una pista, 24 kHz, y lo que dura cuadra con lo que dice: una voz de otra frase, cortada o con ruido de más, no cuadra."""
    sf = pytest.importorskip("soundfile")
    textos = {a.lower(): t for a, _, t in _frases()}
    raras = []
    for a, ruta in serie.items():
        i = sf.info(ruta)
        assert ruta.lower().endswith(".ogg") and i.channels == 1 and i.samplerate == 24000, ruta
        t = textos.get(a)
        if t is None:
            continue
        seg = i.frames / i.samplerate
        assert 0.25 <= seg <= 40, (a, seg)
        if len(t) >= 25 and not 7 <= len(t) / seg <= 26:           # letras por segundo: el mismo margen que se usa al generarlas
            raras.append((a, round(len(t) / seg, 1)))
    assert len(raras) <= len(serie) * 0.01, raras[:30]


def test_quien_nombra_al_protagonista_tiene_voz_en_el_generador():
    """Al personaje propio se le generan las frases que dicen su nombre: hace falta la voz de quien las dice."""
    rep = vozgen.reparto()
    if not rep["personajes"]:
        pytest.skip("en esta copia no está el reparto del generador de voces")
    quienes = {q for _, q, t in _frases() if vozgen.nombra(t) and q != vozgen.PROTA}
    assert quienes and not quienes - set(rep["personajes"]), sorted(quienes - set(rep["personajes"]))
    assert {f"{v}_{g}" for v in vozgen.VOCES_PROTA for g in "hm"} <= set(rep["protagonista"])
    for archivo in list(rep["personajes"].values()) + list(rep["protagonista"].values()):
        assert os.path.exists(os.path.join(vozgen.carpeta_motor(), "voces", archivo + ".safetensors")), archivo
