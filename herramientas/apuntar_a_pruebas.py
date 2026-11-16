"""Le dice a una copia del juego que busque las actualizaciones en la carpeta de pruebas del servidor.

    .venv\\Scripts\\python.exe herramientas\\apuntar_a_pruebas.py "carpeta de la copia del juego"
    .venv\\Scripts\\python.exe herramientas\\apuntar_a_pruebas.py "carpeta de la copia del juego" normal

Cambia solo dos opciones de esa copia, las mismas que se cambian a mano en Opciones, Actualizaciones: de dónde se
actualiza (una dirección personalizada) y cuál es esa dirección. El resto de sus opciones no se toca. Con la palabra
normal al final, la deja otra vez buscando en el servidor del juego.

Sirve para probar que una versión se actualiza bien antes de publicarla: se sube con
herramientas\\publicar.py prueba, y la copia apuntada aquí es la única que la ve.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from herramientas.publicar import SUB_PRUEBAS          # noqa: E402
from juego import actualizador as A, cifrado          # noqa: E402

URL = A.URL_SERVIDOR.rsplit("/", 1)[0] + "/" + SUB_PRUEBAS + "/version.json"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    carpeta = os.path.join(sys.argv[1], "data", "config")
    normal = len(sys.argv) > 2 and sys.argv[2].lower() == "normal"
    os.makedirs(carpeta, exist_ok=True)
    ruta = next((os.path.join(carpeta, n) for n in ("config.pbc", "config.json") if os.path.exists(os.path.join(carpeta, n))), os.path.join(carpeta, "config.pbc"))
    try:
        datos = cifrado.leer_json(ruta)
    except (OSError, ValueError):
        datos = {}
    datos["act_fuente"] = "servidor" if normal else "personalizada"
    datos["act_url"] = "" if normal else URL
    cifrado.escribir_json(ruta, datos, cifrado=ruta.endswith(".pbc"), sangria=2)
    vuelta = cifrado.leer_json(ruta)
    assert vuelta["act_fuente"] == datos["act_fuente"] and vuelta["act_url"] == datos["act_url"]
    print("Hecho en", ruta)
    print("Se actualiza desde:", "el servidor del juego" if normal else URL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
