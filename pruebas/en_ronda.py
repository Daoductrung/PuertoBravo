"""La ronda de menús y lugares, jugando en inglés: todo lo que dice el juego tiene que estar en inglés.

No se recoge sola con las demás pruebas (el idioma se fija al arrancar el proceso y las demás van en español): la lanza
test_172_ingles.py en un proceso aparte, con PUERTOBRAVO_IDIOMA=en. Cada frase dicha que parezca española se apunta en
data/logs/fugas_en.txt, para revisarla, y la prueba falla si hay más de las que se toleran.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas", "i18n"))

import fugas  # noqa: E402
import test_ronda  # noqa: E402
from juego import i18n, rutas  # noqa: E402

# Lo que no se pulsa, también en inglés
test_ronda.PROHIBIDAS = test_ronda.PROHIBIDAS + ("exit", "new game", "load game", "continue", "open my game", "join a friend", "friends from outside",
                                                 "open the manual", "close my game", "disconnect", "leave the server")
TOLERADAS = 0


def _apuntar(app, nombre):
    dicho = [f for f in app.voz.registro if isinstance(f, str)]
    malas = []
    for frase in dicho:
        malas += fugas.fugas(frase)
    unicas = sorted(set(malas))
    ruta = rutas.data("logs", f"fugas_en_{nombre}.txt")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"{len(dicho)} frases dichas, {len(unicas)} sospechosas\n\n" + "\n".join(unicas))
    return unicas


def test_en_ingles_menus_opciones_y_movil(robot):
    assert i18n.actual() == "en"
    test_ronda.test_ronda_de_menus_opciones_y_movil(robot)
    malas = _apuntar(robot.app, "menus")
    assert len(malas) <= TOLERADAS, f"{len(malas)} frases en español: {malas[:15]}"


def test_en_ingles_todos_los_lugares(robot):
    assert i18n.actual() == "en"
    test_ronda.test_ronda_de_todos_los_lugares(robot)
    malas = _apuntar(robot.app, "lugares")
    assert len(malas) <= TOLERADAS, f"{len(malas)} frases en español: {malas[:15]}"


def test_en_ingles_partida_larga(robot):
    assert i18n.actual() == "en"
    test_ronda.test_partida_larga_con_el_tiempo_acelerado(robot)
    malas = _apuntar(robot.app, "partida")
    assert len(malas) <= TOLERADAS, f"{len(malas)} frases en español: {malas[:15]}"
