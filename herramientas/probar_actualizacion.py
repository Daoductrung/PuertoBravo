"""Prueba de verdad una actualización, de principio a fin, sobre una copia del juego, sin tocar la copia original.

    .venv\\Scripts\\python.exe herramientas\\probar_actualizacion.py "carpeta de una copia del juego" [opciones]

Qué hace:
  1. Duplica esa copia en una carpeta temporal y trabaja sobre el duplicado.
  2. Deja en el duplicado unos testigos: una partida, unas opciones, una canción, una voz propia y un mod.
  3. Con el código del actualizador que se le diga (el de este proyecto, o el de una versión anterior sacada de git con
     --codigo ETIQUETA, que es el mismo que lleva el juego compilado de esa versión), busca la versión nueva en la
     dirección de pruebas, la descarga, comprueba su firma, la extrae, escribe el instalador y lo lanza, igual que
     hace el juego al elegir Descargar e instalar.
  4. Espera a que el instalador termine y a que el juego actualizado se abra solo, lo deja unos segundos en marcha y
     lo cierra.
  5. Comprueba el resultado: la versión instalada, que los testigos siguen intactos, que están las voces, el generador
     de voces, la carpeta del servidor y los cuatro programas, que no quedan restos de la actualización y que el juego
     nuevo arrancó sin errores.

Opciones:
  --url DIRECCION       dirección del version.json. De serie, la de la subcarpeta de pruebas del servidor.
  --codigo ETIQUETA     usa el actualizador de esa etiqueta de git (por ejemplo v1.6.3) en lugar del actual.
  --desde VERSION       la versión que se supone instalada. De serie, la que diga el LEEME del duplicado.
  --conservar           no borra el duplicado al terminar, para mirarlo a mano.

Termina con un resumen y con código de salida 0 solo si todo fue bien. Abre el juego unos segundos: se oirá.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONDUCTOR = r'''
import json, os, subprocess, sys, time
arbol, copia, url, desde = sys.argv[1:5]
sys.path.insert(0, arbol)
from juego import rutas
rutas.base = lambda: copia
rutas.DATA = os.path.join(copia, "data")
from juego import actualizador as A
A.carpeta_programa = lambda: copia
info = A.comprobar("personalizada", url, version_actual=desde)
if info is None:
    print(json.dumps({"error": "no hay versión más nueva que la " + desde}))
    sys.exit(3)
t0 = time.time()
marcas = []
def progreso(hecho, total):
    c = int(10 * hecho / max(1, total))
    if c not in marcas:
        marcas.append(c)
ruta = A.descargar(info, progreso=progreso)
t_descarga = time.time() - t0
nueva = A.extraer(ruta, os.path.join(A.carpeta_trabajo(), "nueva"))
try:
    os.remove(ruta)
except OSError:
    pass
# el instalador espera a que se cierre «el juego»: aquí hace ese papel un proceso que dura unos segundos
falso = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(4)"])
bat = A.escribir_instalador(nueva, programa=copia, pid=falso.pid, version=info.version)
texto = open(bat, encoding="utf-8").read()
A.lanzar_instalador(bat)
print(json.dumps({"version": info.version, "megas": info.tamano // 2 ** 20, "segundos_descarga": round(t_descarga, 1), "trabajo": A.carpeta_trabajo(),
                  "progreso": len(marcas), "bat_con_timeout": "timeout /t" in texto, "bat_espera_servidor": "PuertoBravoServidor" in texto}))
'''


def sha(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def version_de(carpeta):
    try:
        m = re.search(r"Versi[oó]n (\d+\.\d+\.\d+)", open(os.path.join(carpeta, "LEEME.txt"), encoding="utf-8").read())
        return m.group(1) if m else "?"
    except OSError:
        return "?"


def procesos_de(carpeta):
    """PID de los PuertoBravo*.exe que se han abierto desde esa carpeta, y solo esos."""
    guion = ("Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith('%s', 'OrdinalIgnoreCase') } "
             "| ForEach-Object { '{0};{1}' -f $_.ProcessId, $_.Name }") % carpeta.replace("'", "''")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", guion], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    out = []
    for linea in r.stdout.splitlines():
        if ";" in linea:
            pid, nombre = linea.strip().split(";", 1)
            out.append((int(pid), nombre))
    return out


def consolas_visibles():
    """Cuántas ventanas de consola visibles hay con el título del instalador. Para comprobar que ya no se ve ninguna."""
    guion = ("$n = 0; Get-CimInstance Win32_Process -Filter \"Name = 'cmd.exe'\" | Where-Object { $_.CommandLine -match 'instalar_actualizacion' } | "
             "ForEach-Object { $p = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue; if ($p -and $p.MainWindowHandle -ne 0) { $n++ } }; $n")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", guion], capture_output=True, text=True, timeout=30)
        return int((r.stdout.strip() or "0").splitlines()[-1])
    except (OSError, ValueError, subprocess.SubprocessError):
        return -1


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__)
        return 1
    origen = os.path.abspath(args[0])
    opciones = {"--url": None, "--codigo": None, "--desde": None}
    conservar = "--conservar" in args
    for k in list(opciones):
        if k in args:
            opciones[k] = args[args.index(k) + 1]
    if opciones["--url"] is None:
        sys.path.insert(0, RAIZ)
        from herramientas.publicar import SUB_PRUEBAS
        from juego import actualizador as A
        opciones["--url"] = A.URL_SERVIDOR.rsplit("/", 1)[0] + "/" + SUB_PRUEBAS + "/version.json"
    fallos, avisos = [], []
    temporal = tempfile.mkdtemp(prefix="pb_act_")
    copia = os.path.join(temporal, "PuertoBravo")
    print("Duplicando la copia en", copia, "...")
    shutil.copytree(origen, copia)
    desde = opciones["--desde"] or version_de(copia)
    print("Versión de partida:", desde)

    # ---------------------------------------------------------------- testigos
    testigos = {}
    for relativa, contenido in (("data/partidas/testigo_prueba.json", b'{"testigo": "partida"}'), ("data/config/testigo_prueba.txt", b"opciones"),
                                ("data/radio/mi_musica/testigo_prueba.txt", b"cancion"), ("data/voces/propias/testigo_prueba.txt", b"voz propia"),
                                ("data/mods/testigo_prueba.txt", b"mod del jugador")):
        ruta = os.path.join(copia, *relativa.split("/"))
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "wb") as f:
            f.write(contenido)
        testigos[relativa] = sha(ruta)
    existentes = {}
    for carpeta in ("data/partidas", "data/config"):
        base = os.path.join(copia, *carpeta.split("/"))
        for f in os.listdir(base) if os.path.isdir(base) else []:
            if os.path.isfile(os.path.join(base, f)):
                existentes[carpeta + "/" + f] = sha(os.path.join(base, f))

    # ---------------------------------------------------------------- el código del actualizador
    arbol = RAIZ
    if opciones["--codigo"]:
        arbol = os.path.join(temporal, "codigo")
        os.makedirs(arbol)
        tar = os.path.join(temporal, "codigo.tar")
        subprocess.run(["git", "-C", RAIZ, "archive", "-o", tar, opciones["--codigo"], "juego"], check=True)
        subprocess.run(["tar", "-xf", tar, "-C", arbol], check=True)
        print("Actualizador de", opciones["--codigo"])
    conductor = os.path.join(temporal, "conductor.py")
    with open(conductor, "w", encoding="utf-8") as f:
        f.write(CONDUCTOR)
    t0 = time.time()
    r = subprocess.run([sys.executable, conductor, arbol, copia, opciones["--url"], desde], capture_output=True, text=True, cwd=temporal)
    linea = next((x for x in reversed(r.stdout.splitlines()) if x.startswith("{")), "")
    if r.returncode != 0 or not linea:
        print(r.stdout[-2000:], r.stderr[-3000:])
        print("FALLO: no se pudo buscar, descargar o preparar la actualización.")
        if not conservar:
            shutil.rmtree(temporal, ignore_errors=True)
        return 2
    datos = json.loads(linea)
    print("Descargada y comprobada la versión %(version)s: %(megas)s megas en %(segundos_descarga)s segundos. Instalador lanzado." % datos)
    if datos["progreso"] < 5:
        avisos.append("el progreso de la descarga se avisó pocas veces (%d)" % datos["progreso"])

    # ---------------------------------------------------------------- esperar al instalador y al juego nuevo
    bat = os.path.join(datos["trabajo"], "instalar_actualizacion.bat")
    consolas = 0
    abierto = None
    limite = time.time() + 420
    while time.time() < limite:
        consolas = max(consolas, consolas_visibles())
        juego = [p for p in procesos_de(copia) if p[1].lower() == "puertobravo.exe"]
        if juego and not os.path.exists(bat):
            abierto = juego[0][0]
            break
        time.sleep(2)
    t_total = time.time() - t0
    if abierto is None:
        fallos.append("el juego actualizado no se abrió solo en siete minutos")
    else:
        print("El juego actualizado se ha abierto solo a los %d segundos. Se deja doce segundos en marcha." % t_total)
        time.sleep(12)
        vivo = any(p[0] == abierto for p in procesos_de(copia))
        if not vivo:
            fallos.append("el juego actualizado se cerró solo a los pocos segundos de abrirse")
    for pid, nombre in procesos_de(copia):
        subprocess.run(["taskkill", "/pid", str(pid), "/f"], capture_output=True)
    time.sleep(2)

    # ---------------------------------------------------------------- comprobaciones
    ahora = version_de(copia)
    if ahora != datos["version"]:
        fallos.append("la versión instalada es la %s y debía ser la %s" % (ahora, datos["version"]))
    for relativa, huella in list(testigos.items()) + list(existentes.items()):
        ruta = os.path.join(copia, *relativa.split("/"))
        if not os.path.exists(ruta):
            # las opciones cambian de forma al abrir el juego: el archivo puede haberse vuelto a escribir, pero no desaparecer
            fallos.append("ha desaparecido " + relativa)
        elif sha(ruta) != huella and relativa in testigos:
            fallos.append("ha cambiado " + relativa)
    for nombre in ("PuertoBravo.exe", "EditorMods.exe", "PuertoBravoServidor.exe", "PuertoBravoServidorPanel.exe"):
        if not os.path.exists(os.path.join(copia, nombre)):
            fallos.append("falta " + nombre)
    for relativa in ("servidor/documentacion.html", "servidor/servidor.conf.ejemplo", "servidor/otros_sistemas", "data/phonon/model.q8.gguf",
                     "data/docs/manual.html", "data/docs/servidor.html", "data/datos", "lib/juego", "lib/servidor", "lib/panel_servidor"):
        if not os.path.exists(os.path.join(copia, *relativa.split("/"))):
            fallos.append("falta " + relativa)
    voces = sum(len([f for f in fs if f.lower().endswith(".ogg")]) for _r, _d, fs in os.walk(os.path.join(copia, "data", "voces")))
    if voces < 1000:
        fallos.append("solo hay %d voces en data\\voces" % voces)
    if os.path.isdir(os.path.join(copia, "data", "datos", "voces_puente")):
        fallos.append("el puente de voces no se ha recogido")
    restos = os.path.join(copia, "data", "actualizacion")
    if os.path.isdir(restos) and any(os.scandir(restos)):
        avisos.append("quedan archivos en data\\actualizacion: " + ", ".join(sorted(os.listdir(restos))[:6]))
    # el registro de la sesión del juego nuevo, si lo hay: que no tenga errores
    logs = os.path.join(copia, "data", "logs")
    textos = []
    for raiz, _d, fs in os.walk(logs) if os.path.isdir(logs) else []:
        for f in fs:
            if f.lower().endswith((".txt", ".log")) and os.path.getmtime(os.path.join(raiz, f)) >= t0:
                try:
                    textos.append(open(os.path.join(raiz, f), encoding="utf-8", errors="replace").read())
                except OSError:
                    pass
    registro = "\n".join(textos)
    if registro:
        if "Traceback" in registro or "[error]" in registro.lower():
            fallos.append("el registro del juego actualizado tiene errores")
        if datos["version"] not in registro:
            avisos.append("el registro de la sesión no menciona la versión nueva")
    else:
        avisos.append("el juego actualizado no dejó registro de sesión en doce segundos")
    if opciones["--codigo"] is None:
        if consolas > 0:
            fallos.append("se ha visto una ventana de consola durante la instalación")
        if datos["bat_con_timeout"]:
            fallos.append("el instalador sigue usando timeout, que necesita ventana")
        if not datos["bat_espera_servidor"]:
            fallos.append("el instalador no espera a que se cierre el servidor")
        # el instalador deja su propio registro, con cada paso y cómo terminó
        propio = os.path.join(logs, "actualizacion.log")
        try:
            apuntado = open(propio, encoding="utf-8", errors="replace").read()
        except OSError:
            apuntado = ""
        if "TERMINADA bien" not in apuntado:
            fallos.append("el instalador no ha dejado su registro, o no dice que terminó bien: " + (apuntado[-300:].replace("\n", " | ") or "no existe data\\logs\\actualizacion.log"))
        elif "RESULTADO copiar_nueva" not in apuntado:
            fallos.append("el registro del instalador no apunta los pasos")

    print()
    print("RESUMEN: de la %s a la %s con el actualizador %s." % (desde, ahora, opciones["--codigo"] or "de este proyecto"))
    print("  Tiempo total, de buscar a tener el juego nuevo abierto: %d segundos." % t_total)
    print("  Voces en data\\voces: %d. Ventanas de consola vistas: %s." % (voces, consolas if consolas >= 0 else "no se pudo mirar"))
    for a in avisos:
        print("  AVISO:", a)
    for f in fallos:
        print("  FALLO:", f)
    print("  TODO BIEN." if not fallos else "  HAY %d FALLOS." % len(fallos))
    if conservar:
        print("  El duplicado se conserva en", copia)
    else:
        shutil.rmtree(temporal, ignore_errors=True)
    return 0 if not fallos else 1


if __name__ == "__main__":
    sys.exit(main())
