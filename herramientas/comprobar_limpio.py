"""Comprueba que una carpeta compilada está lista para distribuir: completa y sin nada personal.

    .venv\\Scripts\\python.exe herramientas\\comprobar_limpio.py dist\\PuertoBravo

Sale con código 1 si encuentra partidas, opciones, registros, música personal o si falta algo necesario.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


MODS_DE_SERIE = ("costa_dorada.pbm", "oficios_y_recados.pbm", "valdeolmos.pbm", "motor_y_asfalto.pbm",
                 "penas_altas.pbm", "isla_de_los_vientos.pbm", "noches_de_neon.pbm")
# La documentación que se reparte es para quien juega: nada de programación.
SOLO_DESARROLLO = (("data", "docs", "crear_mods.html"), ("data", "actualizacion"), ("data", "logs"), ("data", "error.log"), ("herramientas",), ("pruebas",))


def comprobar(raiz):
    problemas = []
    data = os.path.join(raiz, "data")

    def hay(*partes):
        return os.path.exists(os.path.join(raiz, *partes))

    for necesario in (("PuertoBravo.exe",), ("EditorMods.exe",), ("data", "datos", "ciudad.pbd"), ("data", "docs", "manual.html"),
                      ("data", "docs", "teclas.html"), ("data", "docs", "cambiar_sonidos.html"), ("data", "docs", "editor_mods.html"),
                      ("data", "docs", "novedades.html"), ("data", "sonidos", "por_defecto"), ("data", "sonidos", "realista"), ("data", "sonidos", "alternativo"), ("data", "sonidos", "retro"),
                      ("data", "radio"), ("data", "musica")) + tuple(("data", "mods", m) for m in MODS_DE_SERIE):
        if not hay(*necesario):
            problemas.append("Falta " + os.path.join(*necesario))
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
