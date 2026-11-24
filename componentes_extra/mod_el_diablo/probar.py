"""Comprueba que el juego carga el mod El Diablo tal como lo cargaría desde la carpeta de mods.

    set PUERTOBRAVO_IDIOMA=es
    .venv\\Scripts\\python.exe componentes_extra\\mod_el_diablo\\probar.py

Copia el_diablo.json a una carpeta de mods temporal, hace que el juego mire allí, carga los datos y construye todos
los mapas. Después comprueba que existen El Purgatorio en Puerto Bravo, el revólver, los cinco contratos y las cuatro
misiones, y que cada paso de cada misión apunta a lugares, armas y vehículos que existen. Sale con código 1 al primer
fallo. No toca la carpeta de mods del juego. La prueba que juega las misiones y los contratos de verdad está en
pruebas\\test_174_el_diablo.py.
"""
import os
import shutil
import sys
import tempfile

os.environ.setdefault("PUERTOBRAVO_IDIOMA", "es")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

from juego import mundo, rutas          # noqa: E402
from juego import contratos             # noqa: E402

ARCHIVO = os.path.join(AQUI, "el_diablo.json")
MISIONES = ("di01", "di02", "di03", "di04")
CONTRATOS = ("di_sin_aviso", "di_caceria", "di_puerta", "di_rastro", "di_convoy")


def comprobar(cond, texto):
    if not cond:
        raise AssertionError(texto)


def probar():
    comprobar(os.path.exists(ARCHIVO), f"No existe {ARCHIVO}. Ejecuta antes crear.py.")
    temporal = tempfile.mkdtemp(prefix="mods_diablo_")
    original = rutas.MODS
    try:
        shutil.copy(ARCHIVO, os.path.join(temporal, "el_diablo.json"))
        rutas.MODS = temporal
        datos = mundo.cargar_datos()
        comprobar(not datos["errores_mods"], f"Errores al cargar el mod: {datos['errores_mods']}")
        mapas = mundo.crear_mapas(datos)
        comprobar(not datos["errores_mods"], f"Errores al construir los mapas: {datos['errores_mods']}")
    finally:
        rutas.MODS = original
        shutil.rmtree(temporal, ignore_errors=True)

    # la agencia, en Puerto Bravo, con su tablón
    pb = mapas["puerto_bravo"]
    comprobar("di_agencia" in pb.lugares, "Falta El Purgatorio en Puerto Bravo.")
    l = pb.lugares["di_agencia"]
    comprobar(l.tipo == "taberna" and l.nombre and l.desc and l.sonido, "El Purgatorio no es una taberna con nombre, descripción y sonido.")
    comprobar(pb.transitable(l.x, l.y), "El Purgatorio cae dentro de un edificio.")

    todos = {}
    for m in mapas.values():
        todos.update(m.lugares_todos)
    misiones = {m["id"]: m for m in datos["misiones"]}
    armas = {a["id"] for a in datos["armas"]}
    vehiculos = {v["id"] for v in datos["vehiculos"]}
    comprobar("di_cuerno" in armas, "Falta el Cuerno del Diablo.")
    comprobar("61" in datos["capitulos"], "Falta el capítulo del mod.")

    # los contratos: se suman a los de serie, ninguno es un escarmiento y sus vehículos existen
    tipos = {c["id"]: c for c in datos["contratos"]}
    for ident in CONTRATOS:
        comprobar(ident in tipos, f"Falta el contrato {ident}.")
        c = tipos[ident]
        comprobar(c["situacion"] in contratos.SITUACIONES and c["situacion"] != "intimidar", f"{ident}: situación {c['situacion']} no vale.")
        for modelo in c.get("modelos", []):
            comprobar(modelo in vehiculos, f"{ident}: el vehículo {modelo} no existe.")
    comprobar(len(tipos) > len(CONTRATOS), "Los contratos del mod han sustituido a los de serie.")

    # las misiones: existen, empiezan tras la primera de la historia y sus pasos apuntan a lo que existe
    frases = 0
    for ident in MISIONES:
        comprobar(ident in misiones, f"Falta la misión {ident}.")
        mi = misiones[ident]
        comprobar(mi["lugar"] in todos, f"{ident}: empieza en {mi['lugar']}, que no existe.")
        comprobar(not todos[mi["lugar"]].get("adultos"), f"{ident}: empieza en un lugar solo para adultos.")
        for req in mi.get("requiere", []):
            comprobar(req in misiones, f"{ident}: exige {req}, que no existe.")
        for n, p in enumerate(mi["pasos"], 1):
            if p.get("lugar"):
                comprobar(p["lugar"] in todos, f"{ident}, paso {n}: el lugar {p['lugar']} no existe.")
                comprobar(not todos[p["lugar"]].get("adultos"), f"{ident}, paso {n}: {p['lugar']} solo existe con el contenido para adultos.")
            for g in p.get("enemigos", []):
                comprobar(g.get("clase") or g.get("arma") in armas, f"{ident}, paso {n}: los enemigos llevan un arma que no existe.")
            if p.get("modelo"):
                comprobar(p["modelo"] in vehiculos, f"{ident}, paso {n}: el vehículo {p['modelo']} no existe.")
            if p["tipo"] == "dialogo":
                frases += len(p["lineas"])
        arma = (mi.get("recompensa") or {}).get("arma")
        if arma:
            comprobar(arma in armas, f"{ident}: la recompensa es un arma que no existe.")
    comprobar(set(misiones["di01"]["requiere"]) == {"m01"}, "La historia no empieza tras la primera misión del juego.")
    return len(MISIONES), len(CONTRATOS), frases


if __name__ == "__main__":
    try:
        misiones, contratos_, frases = probar()
    except AssertionError as e:
        print("FALLO:", e)
        sys.exit(1)
    print(f"El Diablo se carga bien: {misiones} misiones, {contratos_} contratos y {frases} frases de diálogo.")
