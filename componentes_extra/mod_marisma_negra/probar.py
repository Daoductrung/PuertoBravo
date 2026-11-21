"""Comprueba que el juego carga el mod Marisma Negra tal como lo cargaría desde la carpeta de mods.

    set PUERTOBRAVO_IDIOMA=es
    .venv\\Scripts\\python.exe componentes_extra\\mod_marisma_negra\\probar.py

Copia marisma_negra.json a una carpeta de mods temporal, hace que el juego mire allí, carga los datos y construye
todos los mapas. Después comprueba que existen el mapa nuevo y sus lugares, la salida desde Puerto Bravo, el muelle
en el mar, las misiones, las armas, los vehículos, la carrera y el personaje, y que cada paso de cada misión apunta
a lugares que existen. Sale con código 1 al primer fallo. No toca la carpeta de mods del juego.
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
from juego import cifrado               # noqa: E402

ARCHIVO = os.path.join(AQUI, "marisma_negra.json")
MAPA = "marisma_negra"
MISIONES = ("mn01", "mn02", "mn03", "mn04", "mn05")
LUGARES = ("mn_salida", "mn_estacion", "mn_tren", "mn_taberna", "mn_tienda", "mn_banco", "mn_plaza", "mn_iglesia", "mn_casa", "mn_consultorio",
           "mn_armeria", "mn_farmacia", "mn_taller", "mn_ong", "mn_hostal", "mn_cooperativa", "mn_empleo", "mn_arroceria", "mn_circuito",
           "mn_arrozal", "mn_secadero", "mn_esclusa", "mn_aerodromo", "mn_embarcadero", "mn_nautica", "mn_lonja", "mn_barra", "mn_laguna",
           "mn_observatorio", "mn_salinas")


def comprobar(cond, texto):
    if not cond:
        raise AssertionError(texto)


def probar():
    comprobar(os.path.exists(ARCHIVO), f"No existe {ARCHIVO}. Ejecuta antes crear.py.")
    crudo = cifrado.leer_json(ARCHIVO)
    temporal = tempfile.mkdtemp(prefix="mods_marisma_")
    original = rutas.MODS
    try:
        shutil.copy(ARCHIVO, os.path.join(temporal, "marisma_negra.json"))
        rutas.MODS = temporal
        datos = mundo.cargar_datos()
        comprobar(not datos["errores_mods"], f"Errores al cargar el mod: {datos['errores_mods']}")
        mapas = mundo.crear_mapas(datos)
        comprobar(not datos["errores_mods"], f"Errores al construir los mapas: {datos['errores_mods']}")
    finally:
        rutas.MODS = original
        shutil.rmtree(temporal, ignore_errors=True)

    # el mapa y sus lugares
    comprobar(MAPA in mapas, "No se ha construido el mapa de Marisma Negra.")
    mn = mapas[MAPA]
    comprobar(mn.tipo == "pueblo" and mn.nombre == "Marisma Negra", f"El mapa no es el pueblo esperado: {mn.tipo}, {mn.nombre}.")
    comprobar(len(mn.barrios) == 3, f"Se esperaban tres barrios y hay {len(mn.barrios)}.")
    for ident in LUGARES:
        comprobar(ident in mn.lugares, f"Falta el lugar {ident} en Marisma Negra.")
        l = mn.lugares[ident]
        comprobar(l.nombre and l.desc and l.sonido, f"El lugar {ident} no tiene nombre, descripción o sonido.")
        comprobar(mn.transitable(l.x, l.y), f"El lugar {ident} cae dentro de un edificio.")
    tipos = {l.tipo for l in mn.lugares.values()}
    for t in ("salida", "taberna", "tienda", "casa", "taller", "embarcadero", "monumento", "hospital", "armeria", "ong", "nautica", "pesca", "tren", "aeropuerto"):
        comprobar(t in tipos, f"Marisma Negra no tiene ningún lugar de tipo {t}.")

    # las conexiones: carretera desde Puerto Bravo y muelle en el mar
    pb = mapas["puerto_bravo"]
    comprobar("mn_pb_salida" in pb.lugares, "Falta la salida de Puerto Bravo hacia Marisma Negra.")
    ida = pb.lugares["mn_pb_salida"]
    comprobar(ida.tipo == "salida" and ida.get("a_mapa") == MAPA and ida.get("a_lugar") == "mn_salida", "La salida de Puerto Bravo no lleva a Marisma Negra.")
    vuelta = mn.lugares["mn_salida"]
    comprobar(vuelta.get("a_mapa") == "puerto_bravo" and vuelta.get("a_lugar") == "mn_pb_salida", "La salida de Marisma Negra no vuelve a Puerto Bravo.")
    comprobar(pb.transitable(ida.x, ida.y), "La salida de Puerto Bravo cae dentro de un edificio.")
    mar = mapas["mar"]
    comprobar("mn_mar_muelle" in mar.lugares, "Falta el muelle de Marisma Negra en el mar.")
    comprobar(mar.transitable(mar.lugares["mn_mar_muelle"].x, mar.lugares["mn_mar_muelle"].y), "El muelle del mar no está en agua navegable.")
    comprobar(mn.lugares["mn_embarcadero"].get("a_lugar") == "mn_mar_muelle", "El embarcadero no lleva al muelle del mar.")

    # todo lo demás del mod, ya fusionado con el juego
    todos = {}
    for m in mapas.values():
        todos.update(m.lugares_todos)
    misiones = {m["id"]: m for m in datos["misiones"]}
    armas = {a["id"] for a in datos["armas"]}
    vehiculos = {v["id"]: v for v in datos["vehiculos"]}
    for ident in ("mn_escopeta", "mn_fisga"):
        comprobar(ident in armas, f"Falta el arma {ident}.")
    comprobar("mn_ranchera" in vehiculos and "mn_barca" in vehiculos, "Faltan los vehículos del mod.")
    comprobar(vehiculos["mn_barca"].get("barco"), "La barca de caños no es una embarcación.")
    comprobar(any(c["id"] == "mn_c1" and c["mapa"] == MAPA for c in datos["carreras"]), "Falta la carrera de los arrozales.")
    comprobar(any(p["id"] == "mn_jacinta" for p in datos["personajes"]), "Falta el personaje del mod.")
    nombres_peces = {p["nombre"] for p in datos["peces"]}
    comprobar(all(p["nombre"] in nombres_peces for p in crudo["peces"]), "Faltan los peces del mod.")
    nombres_comidas = {c["nombre"] for c in datos["comidas"]}
    comprobar(all(c["nombre"] in nombres_comidas for c in crudo["comidas"]), "Faltan las comidas del mod.")
    comprobar("47" in datos["capitulos"] and "48" in datos["capitulos"], "Faltan los capítulos del mod.")

    # las misiones: existen, empiezan después de la primera de la historia y sus pasos apuntan a lugares que existen
    frases = 0
    for ident in MISIONES:
        comprobar(ident in misiones, f"Falta la misión {ident}.")
        mi = misiones[ident]
        comprobar(mi["lugar"] in todos, f"{ident}: empieza en {mi['lugar']}, que no existe.")
        for req in mi.get("requiere", []):
            comprobar(req in misiones, f"{ident}: exige {req}, que no existe.")
        for n, p in enumerate(mi["pasos"], 1):
            for clave in ("lugar", "destino"):
                if p.get(clave):
                    comprobar(p[clave] in todos, f"{ident}, paso {n}: {clave} {p[clave]} no existe.")
            for punto in p.get("puntos", []):
                comprobar(punto in todos, f"{ident}, paso {n}: el punto {punto} no existe.")
            if p.get("arma") or p.get("balas_arma"):
                comprobar((p.get("arma") or p.get("balas_arma")) in armas, f"{ident}, paso {n}: el arma no existe.")
            for g in p.get("enemigos", []):
                comprobar(g.get("arma") in armas, f"{ident}, paso {n}: los enemigos llevan un arma que no existe.")
            if p.get("modelo"):
                comprobar(p["modelo"] in vehiculos, f"{ident}, paso {n}: el vehículo {p['modelo']} no existe.")
            if p["tipo"] == "dialogo":
                frases += len(p["lineas"])
        barco = (mi.get("recompensa") or {}).get("barco")
        if barco:
            comprobar(barco["modelo"] in vehiculos and barco["en"] in todos, f"{ident}: el barco de regalo no existe o no tiene dónde amarrar.")
    comprobar(set(misiones["mn01"]["requiere"]) == {"m01"} and set(misiones["mn05"]["requiere"]) == {"m01"}, "La historia no empieza tras la primera misión del juego.")
    return len(LUGARES), len(MISIONES), frases


if __name__ == "__main__":
    try:
        lugares, misiones, frases = probar()
    except AssertionError as e:
        print("FALLO:", e)
        sys.exit(1)
    print(f"Marisma Negra se carga bien: {lugares} lugares en el pueblo, {misiones} misiones y {frases} frases de diálogo.")
