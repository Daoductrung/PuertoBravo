"""El juego jugado en inglés: la ronda de menús, opciones y móvil en un proceso con PUERTOBRAVO_IDIOMA=en (en_ronda.py).

Todo lo que dice tiene que estar en inglés: las frases que parecen españolas quedan en data/logs/fugas_en_menus.txt.
La ronda de lugares y la partida larga en inglés se lanzan a mano, porque tardan:
    set PUERTOBRAVO_IDIOMA=en && .venv\\Scripts\\python.exe -m pytest pruebas\\en_ronda.py
"""
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_la_ronda_de_menus_en_ingles_no_dice_nada_en_espanol():
    env = dict(os.environ, PUERTOBRAVO_IDIOMA="en", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "pytest", os.path.join("pruebas", "en_ronda.py"), "-q", "-p", "no:cacheprovider", "-k", "menus"],
                       cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", timeout=1800)
    assert r.returncode == 0, r.stdout[-4000:]
