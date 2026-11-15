"""Comprueba que una carpeta compilada está lista para distribuir: completa y sin nada personal.

    .venv\\Scripts\\python.exe herramientas\\comprobar_limpio.py dist\\PuertoBravo

Sale con código 1 si encuentra partidas, opciones, registros, música personal o si falta algo necesario.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


MODS_DE_SERIE = ("costa_dorada.pbm", "oficios_y_recados.pbm", "valdeolmos.pbm", "motor_y_asfalto.pbm",
                 "penas_altas.pbm", "isla_de_los_vientos.pbm", "noches_de_neon.pbm", "bahia_del_ocaso.pbm")
# La documentación que se reparte es para quien juega: nada de programación.
SOLO_DESARROLLO = (("data", "docs", "crear_mods.html"), ("data", "actualizacion"), ("data", "logs"), ("data", "error.log"), ("herramientas",), ("pruebas",))


def rutas_de_este_equipo(raiz):
    """Ningún módulo compilado debe llevar dentro la ruta del equipo donde se compiló: saldría en los registros de los jugadores."""
    proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    marcas = [m.encode("utf-8") for m in {proyecto, proyecto.replace("\\", "/"), os.path.expanduser("~")} if len(m) > 3]
    marcas += [m.lower() for m in marcas]
    malos = []
    for base, _, archivos in os.walk(raiz):
        for a in archivos:
            if a.endswith((".pyc", ".zip")):
                try:
                    with open(os.path.join(base, a), "rb") as f:
                        datos = f.read()
                except OSError:
                    continue
                if any(m in datos or m in datos.lower() for m in marcas):
                    malos.append(os.path.relpath(os.path.join(base, a), raiz))
    if malos:
        return [f"{len(malos)} módulos llevan dentro rutas de este equipo, por ejemplo {malos[0]}"]
    return []


def comprobar(raiz):
    problemas = []
    data = os.path.join(raiz, "data")

    def hay(*partes):
        return os.path.exists(os.path.join(raiz, *partes))

    for necesario in (("PuertoBravo.exe",), ("EditorMods.exe",), ("data", "datos", "ciudad.pbd"), ("data", "docs", "manual.html"),
                      ("data", "docs", "teclas.html"), ("data", "docs", "cambiar_sonidos.html"), ("data", "docs", "editor_mods.html"),
                      ("data", "docs", "novedades.html"), ("data", "sonidos", "por_defecto"), ("data", "sonidos", "realista"), ("data", "sonidos", "alternativo"), ("data", "sonidos", "retro"),
                      ("data", "radio"), ("data", "musica"), ("lib", "numpy"), ("lib_antiguo", "numpy"), ("lib", "soft_oal.dll"), ("LICENCIA_OpenAL_Soft.txt",)) + tuple(("data", "mods", m) for m in MODS_DE_SERIE):
        if not hay(*necesario):
            problemas.append("Falta " + os.path.join(*necesario))
    problemas += rutas_de_este_equipo(raiz)
    for sobra in SOLO_DESARROLLO:
        if hay(*sobra):
            problemas.append("Es solo para desarrollo y no debe repartirse: " + os.path.join(*sobra))
    for carpeta in ("partidas", "config", os.path.join("radio", "mi_musica")):
        ruta = os.path.join(data, carpeta)
        if os.path.isdir(ruta):
            for base, _, archivos in os.walk(ruta):
                for f in archivos:
                    problemas.append("Dato personal: " + os.path.relpath(os.path.join(base, f), raiz))
    for base, dirs, archivos in os.walk(raiz):
        for d in dirs:
            if d in ("partidas_pruebas", "__pycache__") and base.startswith(data):
                problemas.append("Sobra la carpeta " + os.path.relpath(os.path.join(base, d), raiz))
        for f in archivos:
            if f.lower().endswith((".log", ".bak", ".tmp")):
                problemas.append("Sobra " + os.path.relpath(os.path.join(base, f), raiz))
    # sonidos en FLAC (sin pérdida) y voces en data\voces, por historias: nada de los formatos y carpetas anteriores
    for base, _, archivos in os.walk(os.path.join(data, "sonidos")):
        for f in archivos:
            if f.lower().endswith(".wav"):
                problemas.append("Sonido en el formato anterior, debería ser FLAC: " + os.path.relpath(os.path.join(base, f), raiz))
    if os.path.isdir(os.path.join(data, "voces_serie")):
        problemas.append("Sobra la carpeta de voces de versiones anteriores: " + os.path.join("data", "voces_serie"))
    if os.path.isdir(os.path.join(data, "voces", "propias")):
        problemas.append("Voces personales: " + os.path.join("data", "voces", "propias"))
    if not os.path.isdir(os.path.join(data, "voces", "historia_principal")):
        problemas.append("Faltan las voces de la historia principal: " + os.path.join("data", "voces", "historia_principal"))
    for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
        ruta = os.path.join(data, "sonidos", pack)
        if os.path.isdir(ruta):
            n = len({os.path.splitext(f)[0] for f in os.listdir(ruta) if f.lower().endswith((".flac", ".ogg", ".wav", ".mp3"))})
            if n != 237:
                problemas.append(f"El pack {pack} tiene {n} sonidos y deberían ser 237")
    mods = os.path.join(data, "mods")
    if os.path.isdir(mods):
        for f in os.listdir(mods):
            if not (f.upper().startswith("LEEME") or f in MODS_DE_SERIE):
                problemas.append("Mod personal: " + os.path.join("data", "mods", f))
    # los datos del juego y los mods deben ir protegidos
    from juego import cifrado
    for sub in ("datos", "mods", "sonidos", "radio", "musica", "docs"):
        for base, _, archivos in os.walk(os.path.join(data, sub)):
            for f in archivos:
                ruta = os.path.join(base, f)
                if f.lower().endswith((".json", ".json.desactivado")):
                    problemas.append("Sin proteger, sigue siendo un .json: " + os.path.relpath(ruta, raiz))
                elif f.lower().endswith((".pbd", ".pbm")):
                    if not cifrado.esta_cifrado(ruta):
                        problemas.append("Sin proteger: " + os.path.relpath(ruta, raiz))
                    else:
                        try:
                            cifrado.leer_json(ruta)
                        except Exception as e:
                            problemas.append(f"No se puede leer {os.path.relpath(ruta, raiz)}: {e}")
    return problemas


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.join("dist", "PuertoBravo")
    fallos = comprobar(carpeta)
    for p in fallos:
        print("  " + p)
    if fallos:
        sys.exit(1)
    print("  Compilacion limpia y completa.")
