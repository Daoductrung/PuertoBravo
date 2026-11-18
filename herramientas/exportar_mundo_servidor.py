"""Escribe servidor/mundo.json: lo que el servidor en línea necesita saber del mundo, sin cargar el juego.

De cada localidad: sus lugares con coordenadas (para las zonas seguras) y sus barrios (para los territorios).
De las armas: daño, alcance, cadencia y precisión (para decidir los disparos entre jugadores).
Y una huella de los datos: dice si el juego de quien entra y el servidor tienen el mismo mundo. Si no, juegan igual en lo común.

    .venv\\Scripts\\python.exe herramientas\\exportar_mundo_servidor.py

Con --catalogo no escribe nada: enseña la entrada de este mundo para servidor/compat.py (qué armas y vehículos conoce
esta versión), que se apunta allí al publicar la siguiente.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import VERSION, mundo, rutas          # noqa: E402
from juego.enlinea import mundo_canonico, mundo_servidor          # noqa: E402


def firmar(carpeta_datos):
    """Escribe mundo.firma en una carpeta data\\datos: la firma de quien publica el juego sobre el mundo de esta versión.
    Con ella, cualquier servidor acepta este mundo de cualquier jugador sin tener que fiarse de él.
    Hace falta la clave privada de publicar; si no está en este equipo, no se firma y no pasa nada."""
    from juego import ed25519
    clave = os.path.join(rutas.base(), "herramientas", "claves", "firma_ed25519.key")
    if not os.path.exists(clave):
        return False
    with open(clave, encoding="ascii") as f:
        semilla = bytes.fromhex(f.read().strip())
    d = mundo_servidor()
    firma = ed25519.firmar(semilla, mundo_canonico(d).encode("utf-8")).hex()
    with open(os.path.join(carpeta_datos, "mundo.firma"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"huella": d["huella"], "version": d["version"], "firma": firma}, f)
    return True


def exportar(destino=None):
    out = mundo_servidor()
    destino = destino or os.path.join(rutas.base(), "servidor", "mundo.json")
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    return out


def catalogo():
    """La entrada de este mundo para servidor/compat.py (CATALOGOS): qué armas y qué vehículos conoce el juego de esta
    versión. Se apunta al publicar la siguiente, para que los servidores nuevos conozcan esta sin tener que pedírsela."""
    from servidor import compat
    d = mundo_servidor()
    c = compat.catalogo_de(d)
    return '    "%s": {\n        "version": "%s",\n        "armas": %s,\n        "modelos": %s,\n    },' % (
        d["huella"], c["version"], json.dumps(c["armas"]), json.dumps(c["modelos"]))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--catalogo":
        print(catalogo())
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "--firmar":
        print("Mundo firmado para los servidores." if firmar(sys.argv[2]) else "No hay clave de publicar en este equipo: el mundo va sin firmar.")
        sys.exit(0)
    o = exportar()
    print(f"servidor/mundo.json: {len(o['mapas'])} localidades, {len(o['armas'])} armas, {len(o['misiones'])} misiones, huella {o['huella']}")
