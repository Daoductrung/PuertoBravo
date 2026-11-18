"""1.7.1: el actualizador deja rastro y comprueba antes de cerrar, y el motor de voz se prueba aparte para no tumbar el juego.
Todo con carpetas de pega en local: aquí no se descarga ni se actualiza nada de verdad."""
import ctypes
import json
import os
import subprocess
import sys
import threading
import time

import pygame
import pytest

from juego import VERSION, actualizador as A, vozgen
from juego.menus import Menu


# ====================================================================== actualizador
def _arbol(raiz, archivos):
    for relativa, datos in archivos.items():
        ruta = os.path.join(raiz, *relativa.split("/"))
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "wb") as f:
            f.write(datos)


def _instalacion(tmp_path, nombre="Puerto Bravo ñ"):
    """Un juego «instalado» y una versión nueva ya extraída, en una carpeta con espacios y eñe."""
    programa = tmp_path / nombre
    nueva = tmp_path / nombre / "data" / "actualizacion" / "nueva"
    _arbol(str(programa), {"PuertoBravo.exe": b"viejo" * 100, "EditorMods.exe": b"editor viejo", "lib/juego/app.pyc": b"v1", "lib/sobra.pyc": b"sobra",
                           "data/datos/ciudad.pbd": b"datos v1", "data/partidas/mia.pbs": b"mi partida", "data/config/config.pbc": b"mis opciones",
                           "data/docs/manual.html": b"manual v1", "data/mods/mio.pbm": b"mi mod"})
    _arbol(str(nueva), {"PuertoBravo.exe": b"nuevo" * 300, "EditorMods.exe": b"editor nuevo", "lib/juego/app.pyc": b"v2 mas largo", "data/datos/ciudad.pbd": b"datos v2",
                        "data/docs/manual.html": b"manual v2"})
    return str(programa), str(nueva)


def test_el_instalador_apunta_cada_paso_en_su_registro(tmp_path):
    programa, nueva = _instalacion(tmp_path)
    bat = A.escribir_instalador(nueva, programa, pid=4321, version="99.0.0")
    texto = open(bat, encoding="utf-8").read()
    assert A.ruta_registro_instalador(programa) == os.path.join(programa, "data", "logs", "actualizacion.log")
    assert 'set "REG=%APP%\\data\\logs\\actualizacion.log"' in texto and "logs" in A.INTOCABLES
    for paso in ("esperar_cierre", "esperar_programas", "copia_seguridad", "copiar_nueva", "copiar_lib", "copiar_datos", "restaurar"):
        assert f"PASO {paso}" in texto and paso in A.PASOS
    assert texto.count('/log+:"%REG%"') >= 8 and ">nul" not in "".join(l for l in texto.splitlines() if l.startswith("robocopy"))
    assert "FALLO paso=%PASO% codigo=%RC% motivo=copia" in texto and "TERMINADA bien" in texto and "TERMINADA mal" in texto
    for exe in ("EditorMods.exe", "PuertoBravoServidor.exe", "PuertoBravoServidorPanel.exe"):          # espera también al editor de mods
        assert f'IMAGENAME eq {exe}' in texto
    # ninguna línea que escribe en el registro deja un número pegado a la redirección
    assert all(l.startswith('>>"%REG%" echo ') or l.startswith('>"%REG%" echo ') for l in texto.splitlines() if "echo" in l and "%REG%" in l)


def _correr_bat(bat):
    """Ejecuta el instalador de verdad, sobre carpetas de pega, sin que abra el juego al terminar."""
    texto = open(bat, encoding="utf-8").read()
    lineas = [('>>"%REG%" echo ABRIRIA ' + l.split('"')[-1].strip()) if l.startswith('start ""') else l for l in texto.splitlines()]
    with open(bat, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    subprocess.run(["cmd.exe", "/c", bat], cwd=os.path.dirname(bat), timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _sin_programas_del_juego():
    if sys.platform != "win32":
        pytest.skip("el instalador es de Windows")
    abiertos = [exe for exe in A.OTROS_PROGRAMAS if exe.lower() in A._tareas()]
    if abiertos:
        pytest.skip("hay un programa del juego abierto en este equipo y el instalador lo esperaría: " + ", ".join(abiertos))


def test_instalacion_de_verdad_en_local_deja_registro_y_no_toca_lo_tuyo(tmp_path):
    _sin_programas_del_juego()
    programa, nueva = _instalacion(tmp_path)
    _correr_bat(A.escribir_instalador(nueva, programa, pid=999999, version="99.0.0"))
    leer = lambda r: open(os.path.join(programa, *r.split("/")), "rb").read()
    assert leer("PuertoBravo.exe") == b"nuevo" * 300 and leer("lib/juego/app.pyc") == b"v2 mas largo" and leer("data/datos/ciudad.pbd") == b"datos v2"
    assert leer("data/partidas/mia.pbs") == b"mi partida" and leer("data/config/config.pbc") == b"mis opciones" and leer("data/mods/mio.pbm") == b"mi mod"
    assert not os.path.exists(os.path.join(programa, "lib", "sobra.pyc")) and not os.path.exists(nueva)
    r = A.leer_registro_instalador(A.ruta_registro_instalador(programa))
    assert r["existe"] and r["bien"] is True and not r["paso"] and not r["error"]
    registro = open(A.ruta_registro_instalador(programa), encoding="utf-8", errors="replace").read()
    assert "version 99.0.0" in registro and "RESULTADO copiar_nueva codigo=" in registro and "ABRIRIA " + A.ARG_TRAS_ACTUALIZAR in registro


def test_si_un_archivo_esta_en_uso_el_registro_dice_cual_y_el_juego_lo_cuenta(tmp_path):
    _sin_programas_del_juego()
    programa, nueva = _instalacion(tmp_path)
    editor = os.path.join(programa, "EditorMods.exe")
    k = ctypes.windll.kernel32
    k.CreateFileW.restype = ctypes.c_void_p
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    asa = k.CreateFileW(editor, 0x80000000, 0, None, 3, 0, None)          # abierto sin compartir: como un programa en marcha
    assert asa not in (None, ctypes.c_void_p(-1).value)
    try:
        assert A.programas_abiertos(programa, tareas=set()) == ["el editor de mods"]      # y el juego lo ve antes de cerrar
        _correr_bat(A.escribir_instalador(nueva, programa, pid=999999, version="99.0.0"))
    finally:
        k.CloseHandle(asa)
    ruta = A.ruta_registro_instalador(programa)
    r = A.leer_registro_instalador(ruta)
    assert r["existe"] and r["bien"] is False and r["paso"] == "copiar_nueva" and r["codigo"] >= 8
    assert r["error"] == 32 and r["archivo"] == "EditorMods.exe", open(ruta, encoding="utf-8", errors="replace").read()
    motivo = A.motivo_del_fallo(ruta)
    assert "EditorMods.exe" in motivo and "otro programa" in motivo and "editor de mods" in motivo and "copiar la versión nueva" in motivo
    # se restauró la versión anterior, y lo personal sigue ahí
    assert open(os.path.join(programa, "PuertoBravo.exe"), "rb").read() == b"viejo" * 100
    assert open(os.path.join(programa, "data", "partidas", "mia.pbs"), "rb").read() == b"mi partida"
    registro = open(ruta, encoding="utf-8", errors="replace").read()
    assert "RESULTADO restaurar" in registro and "ABRIRIA --actualizacion-fallida" in registro
    # tras limpiarlo de rutas, como hace el juego al reabrirse, el motivo se sigue sabiendo leer
    A.limpiar_registro_instalador(ruta)
    limpio = open(ruta, encoding="utf-8").read()
    assert "Puerto Bravo" not in limpio.split("\n", 1)[1] and "\\" not in limpio and os.path.basename(str(tmp_path)) not in limpio
    assert "Copiando archivo EditorMods.exe" in limpio or "Copying File EditorMods.exe" in limpio
    assert "está siendo utilizado" in limpio or "being used" in limpio            # y las tildes de Windows se leen bien
    r2 = A.leer_registro_instalador(ruta)
    assert (r2["archivo"], r2["error"], r2["paso"], r2["bien"]) == ("EditorMods.exe", 32, "copiar_nueva", False)


def test_el_motivo_del_fallo_segun_lo_apuntado(tmp_path):
    ruta = str(tmp_path / "actualizacion.log")
    assert "no dejó apuntado" in A.motivo_del_fallo(ruta)

    def con(*lineas):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("Instalador de Puerto Bravo.\n" + "\n".join(lineas) + "\n")
        return A.motivo_del_fallo(ruta)
    t = con("PASO esperar_cierre", "FALLO paso=esperar_cierre codigo=0 motivo=sigue_abierto", "TERMINADA mal")
    assert "no terminó de cerrarse" in t
    t = con("PASO esperar_cierre", "PASO esperar_programas", "FALLO paso=esperar_programas codigo=0 motivo=sigue_abierto", "TERMINADA mal")
    assert "editor de mods" in t and "Ciérralos" in t
    copia = ["PASO copia_seguridad", "2026/11/18 10:00:00 ERROR 5 (0x00000005) Copiando archivo C:\\Juegos\\PB\\raro.dll", "RESULTADO copia_seguridad codigo=8"]
    t = con(*copia, "PASO copiar_lib", "2026/11/18 10:00:01 ERROR 5 (0x00000005) Copiando archivo C:\\Program Files\\Puerto Bravo\\lib\\juego\\app.pyc",
            "Acceso denegado.", "RESULTADO copiar_lib codigo=8", "FALLO paso=copiar_lib codigo=8 motivo=copia", "TERMINADA mal")
    assert "app.pyc" in t and "raro.dll" not in t and "acceso denegado" in t and "Archivos de programa" in t and "antivirus" in t
    t = con("PASO copiar_nueva", "2026/11/18 10:00:01 ERROR 112 (0x00000070) Copying File D:\\PB\\data\\voces\\a.ogg", "FALLO paso=copiar_nueva codigo=8 motivo=copia")
    assert "sitio suficiente en el disco" in t
    t = con("PASO copiar_nueva", "2026/11/18 10:00:01 ERROR 225 (0x000000E1) Copying File D:\\PB\\PuertoBravoServidor.exe", "FALLO paso=copiar_nueva codigo=8 motivo=copia")
    assert "antivirus bloqueó el archivo PuertoBravoServidor.exe" in t
    t = con("PASO copiar_nueva", "2026/11/18 10:00:01 ERROR 1392 (0x00000570) Copying File D:\\PB\\x.bin", "FALLO paso=copiar_nueva codigo=16 motivo=copia")
    assert "error 1392" in t and "x.bin" in t
    t = con("PASO copiar_datos", "FALLO paso=copiar_datos codigo=16 motivo=copia")
    assert "copiar los datos nuevos" in t
    assert A.leer_registro_instalador(ruta)["bien"] is None
    with open(ruta, "wb") as f:                                   # un registro ilegible no rompe nada
        f.write(b"\xff\xfe\x00ERROR")
    assert A.motivo_del_fallo(ruta)


def test_el_sitio_en_disco_se_calcula_y_se_dice_con_claridad(tmp_path):
    programa, nueva = _instalacion(tmp_path)
    # la copia de seguridad: el programa sin data, más datos, mods y manuales; nunca las partidas ni las opciones
    copia = len(b"viejo" * 100) + len(b"editor viejo") + len(b"v1") + len(b"sobra") + len(b"datos v1") + len(b"manual v1") + len(b"mi mod")
    assert A.tamano_copia(programa) == copia
    # lo que crece: cada archivo nuevo menos el que sustituye; y un margen del tamaño del archivo mayor
    crece = (1500 - 500) + (len(b"v2 mas largo") - 2)
    assert A.espacio_para_instalar(nueva, programa) == copia + crece + 1500 + A.MARGEN_DISCO
    hace_falta = A.espacio_para_instalar(nueva, programa)
    assert A.problemas_para_instalar(nueva, programa, libre=hace_falta, tareas=set()) == []
    p = A.problemas_para_instalar(nueva, programa, libre=10 * 1024 ** 2, tareas=set())
    assert len(p) == 1 and "No hay sitio suficiente en el disco" in p[0] and "hay 10 megas" in p[0] and "Libera al menos" in p[0]
    assert A.megas_txt(1717986918) == "1,6 gigas" and A.megas_txt(300 * 1024 ** 2) == "300 megas"

    class Info:
        tamano = 600 * 1024 ** 2
    antes = A.espacio_para_descargar(Info, programa)
    assert antes >= Info.tamano + int(Info.tamano * 1.15)          # el ZIP y la versión extraída, a la vez
    assert A.problema_para_descargar(Info, programa, libre=antes) == ""
    assert "hacen falta 1,3 gigas" in A.problema_para_descargar(Info, programa, libre=5 * 1024 ** 2)
    # con una instalación grande, lo que manda es lo que ya ocupa el programa
    _arbol(programa, {"lib/grande.bin": b"x" * (3 * 1024 ** 2)})
    Info.tamano = 1024 ** 2
    assert A.espacio_para_descargar(Info, programa) > 3 * 1024 ** 2 + A.MARGEN_DISCO


def test_programas_abiertos_y_carpeta_protegida(tmp_path, monkeypatch):
    programa, nueva = _instalacion(tmp_path)
    assert A.programas_abiertos(programa, tareas={"notepad.exe"}) == []
    assert A.programas_abiertos(programa, tareas={"editormods.exe", "puertobravoservidorpanel.exe"}) == ["el editor de mods", "el panel del servidor en línea"]
    p = A.problemas_para_instalar(nueva, programa, libre=10 ** 12, tareas={"EditorMods.exe"})
    assert len(p) == 1 and "Está abierto el editor de mods" in p[0] and "ciérralo" in p[0]
    p = A.problemas_para_instalar(nueva, programa, libre=10 ** 12, tareas={"EditorMods.exe", "PuertoBravoServidor.exe"})
    assert "Están abiertos el editor de mods y el servidor en línea" in p[0]
    assert A.carpeta_escribible(programa) and not A.carpeta_escribible(str(tmp_path / "no existe"))
    monkeypatch.setattr(A, "carpeta_escribible", lambda c: False)
    p = A.problemas_para_instalar(nueva, programa, libre=10 ** 12, tareas=set())
    assert len(p) == 1 and "no deja escribir en la carpeta del juego" in p[0]
    monkeypatch.setattr(A, "_tareas", lambda: {"puertobravoservidor.exe"})
    assert A.servidor_abierto()


def test_el_juego_no_se_cierra_si_la_instalacion_iba_a_fallar(robot, tmp_path):
    from juego import menus_actualizar
    app = robot.app
    programa, nueva = _instalacion(tmp_path)
    bat = A.escribir_instalador(nueva, programa, pid=1, version="99.0.0")
    app.act_version = "99.0.0"
    vistos = []

    def comprobar(carpeta):
        vistos.append(carpeta)
        return A.problemas_para_instalar(carpeta, programa, libre=1024, tareas={"EditorMods.exe"})
    app.act_comprobar = comprobar
    menus_actualizar._instalar(app, bat)
    dicho = robot.app.voz.registro[-1]
    assert app.activo is not False and vistos == [nueva]
    assert "Todavía no se puede instalar" in dicho and "editor de mods" in dicho and "No hay sitio suficiente" in dicho and "La descarga no se pierde" in dicho
    assert app.act_lista == (bat, "99.0.0")                       # queda guardada para instalarla después
    menus_actualizar.opciones(app)
    m = app.pila[-1]
    assert m.opciones[0].texto.startswith("Instalar la versión descargada, la 99.0.0")
    # arreglado: ahora sí se cierra para actualizar
    app.act_comprobar = lambda carpeta: []
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    assert app.activo is False and "se actualiza y vuelve a abrirse" in robot.dicho()


def test_antes_de_descargar_se_mira_si_cabe(robot, tmp_path, monkeypatch):
    from juego import menus_actualizar
    app = robot.app
    programa, _ = _instalacion(tmp_path)
    monkeypatch.setattr(A, "puede_instalar", lambda: True)
    monkeypatch.setattr(A, "carpeta_programa", lambda: programa)
    info = A.Info("99.0.0", "PuertoBravo.zip", "0" * 64, 500 * 1024 ** 2, ["https://ejemplo.invalid/x.zip"], "", "servidor")
    app.act_libre = 20 * 1024 ** 2
    menus_actualizar.ofrecer(app, info)
    oferta = app.pila[-1]
    oferta.i = next(k for k, o in enumerate(oferta.opciones) if o.texto.startswith("Descargar e instalar"))
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is oferta and "No hay sitio suficiente en el disco" in robot.app.voz.registro[-1] and "hay 20 megas" in robot.app.voz.registro[-1]


def test_al_reabrirse_tras_un_fallo_dice_el_motivo(robot, tmp_path, monkeypatch):
    from juego import menus_actualizar, rutas
    app = robot.app
    monkeypatch.setattr(rutas, "DATA", str(tmp_path / "data"))
    monkeypatch.setattr(A, "carpeta_trabajo", lambda: str(tmp_path / "data" / "actualizacion"))
    ruta = A.ruta_registro_instalador()
    os.makedirs(os.path.dirname(ruta))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("Instalador\nPASO copiar_nueva\n2026/11/18 10:00:01 ERROR 32 (0x00000020) Copiando archivo C:\\Users\\alguien\\Juegos\\EditorMods.exe\n"
                "FALLO paso=copiar_nueva codigo=8 motivo=copia\nTERMINADA mal\n")
    monkeypatch.setattr(sys, "argv", ["PuertoBravo.exe", "--actualizacion-fallida"])
    menus_actualizar.al_arrancar(app)
    dicho = robot.app.voz.registro[-1]
    assert "no se pudo instalar" in dicho and VERSION in dicho and "EditorMods.exe" in dicho and "otro programa" in dicho and "actualizacion punto log" in dicho
    assert "alguien" not in open(ruta, encoding="utf-8").read()   # el registro del instalador queda sin rutas personales
    # y se puede volver a oír en Opciones, Actualizaciones
    menus_actualizar.opciones(app)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Por qué falló"))
    robot.tecla(pygame.K_RETURN)
    assert "EditorMods.exe" in robot.app.voz.registro[-1]
    # tras una actualización que sale bien no hay nada que contar
    app.act_fallo = None
    monkeypatch.setattr(sys, "argv", ["PuertoBravo.exe", A.ARG_TRAS_ACTUALIZAR])
    menus_actualizar.al_arrancar(app)
    assert "Juego actualizado" in robot.app.voz.registro[-1] and not app.act_fallo


# ====================================================================== motor de voz
@pytest.fixture
def motor(tmp_path, monkeypatch):
    """Un equipo con el motor puesto y un procesador capaz, con el recuerdo de la prueba en una carpeta de pega."""
    carpeta = tmp_path / "phonon"
    carpeta.mkdir()
    for n in vozgen.ARCHIVOS_MOTOR:
        (carpeta / n).write_bytes(b"{}")
    monkeypatch.setattr(vozgen, "carpeta_motor", lambda: str(carpeta))
    monkeypatch.setattr(vozgen, "carpeta_generadas", lambda: str(tmp_path / "generadas"))
    monkeypatch.setattr(vozgen, "capacidades", lambda: {"AVX2": True, "FMA": True, "F16C": True})
    monkeypatch.setattr(vozgen, "_estado", {"ok": None, "motivo": ""})
    monkeypatch.setattr(vozgen, "_prueba", {"hilo": None, "proc": None, "al_saber": []})
    return carpeta


def _olvidar():
    vozgen._estado.update(ok=None, motivo="")


def test_las_tres_capacidades_del_procesador(motor, monkeypatch):
    monkeypatch.undo()
    caps = vozgen.capacidades()
    assert set(caps) == {"AVX2", "FMA", "F16C"} == set(vozgen.NECESARIAS) and all(v in (True, False, None) for v in caps.values())


@pytest.mark.parametrize("faltan", [("FMA",), ("F16C",), ("AVX2", "F16C")])
def test_sin_una_capacidad_no_se_intenta_cargar(motor, monkeypatch, faltan):
    monkeypatch.setattr(vozgen, "capacidades", lambda: {n: n not in faltan for n in vozgen.NECESARIAS})
    lanzados = []
    assert vozgen.disponible(esperar=True, ejecutar=lambda o, t: lanzados.append(o) or 0) is False
    assert lanzados == [] and not vozgen.probando()               # ni siquiera se prueba: se sabe de antemano
    assert all(n in vozgen.motivo() for n in faltan) and "le falta" in vozgen.motivo()
    # si una capacidad no se puede consultar, no se da por perdida: decide la prueba
    _olvidar()
    monkeypatch.setattr(vozgen, "capacidades", lambda: {"AVX2": True, "FMA": None, "F16C": None})
    assert vozgen.disponible(esperar=True, ejecutar=lambda o, t: 0) is True


def test_la_primera_vez_se_prueba_aparte_y_se_recuerda(motor):
    lanzados = []

    def ejecutar(orden, tiempo):
        lanzados.append(orden)
        return 0
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) is True and vozgen.motivo() == ""
    assert len(lanzados) == 1 and vozgen.ARG_PRUEBA in lanzados[0] and lanzados[0][-1] == str(motor)
    rec = json.load(open(vozgen.ruta_recuerdo(), encoding="utf-8"))
    assert rec["ok"] is True and rec["juego"] == VERSION and rec["motor"] == vozgen.firma_motor()
    # otra sesión: no se vuelve a probar
    _olvidar()
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) is True and len(lanzados) == 1


def test_se_vuelve_a_probar_si_cambia_la_version_del_juego_o_el_motor(motor, monkeypatch):
    import juego
    lanzados = []
    ejecutar = lambda o, t: lanzados.append(1) or 0
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) and len(lanzados) == 1
    _olvidar()
    monkeypatch.setattr(juego, "VERSION", "99.9.9")
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) and len(lanzados) == 2
    _olvidar()
    (motor / "model.q8.gguf").write_bytes(b"otro modelo, de otro tamano")
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) and len(lanzados) == 3
    _olvidar()
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) and len(lanzados) == 3


@pytest.mark.parametrize("codigo, texto", [(0xC000001D, "se ha cerrado de golpe"), (0xC0000005, "se ha cerrado de golpe"), (10, "no se ha podido cargar"),
                                           (11, "no ha conseguido generar"), (None, "tarda demasiado")])
def test_si_la_prueba_sale_mal_el_juego_sigue_y_lo_recuerda(motor, codigo, texto):
    lanzados = []
    ejecutar = lambda o, t: lanzados.append(1) or codigo
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) is False
    assert texto in vozgen.motivo() and "lector de pantalla" in vozgen.motivo() and "cuando actualices" in vozgen.motivo()
    _olvidar()
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) is False and len(lanzados) == 1       # no se insiste en cada arranque
    assert texto in vozgen.motivo()
    # y nada se genera: las frases las dice el lector
    g = vozgen.Generador()
    assert g.pedir(vozgen.Personaje("Lía"), [{"id": "a", "pasos": [{"tipo": "dialogo", "lineas": [["Encarna", "Hola, Dani."]]}]}]) == 0 and not g.activo()


def test_si_no_se_puede_ni_lanzar_la_prueba_no_se_da_por_perdido(motor):
    def ejecutar(orden, tiempo):
        raise OSError("no se puede lanzar")
    assert vozgen.disponible(esperar=True, ejecutar=ejecutar) is False and "no se ha podido probar" in vozgen.motivo()
    assert not os.path.exists(vozgen.ruta_recuerdo())             # no se apunta: la próxima vez se prueba otra vez
    _olvidar()
    assert vozgen.disponible(esperar=True, ejecutar=lambda o, t: 0) is True


def test_mientras_se_prueba_el_juego_no_espera(motor):
    soltar = threading.Event()

    def ejecutar(orden, tiempo):
        soltar.wait(10)
        return 0
    t0 = time.time()
    assert vozgen.disponible(ejecutar=ejecutar) is False and vozgen.probando() and time.time() - t0 < 1
    assert vozgen.motivo() == vozgen.PROBANDO
    avisados = []
    vozgen.cuando_se_sepa(avisados.append)
    assert avisados == []
    soltar.set()
    vozgen._prueba["hilo"] and vozgen._prueba["hilo"].join(5)
    for _ in range(50):
        if avisados:
            break
        time.sleep(0.02)
    assert avisados == [True] and vozgen.disponible() is True and not vozgen.probando()
    vozgen.cuando_se_sepa(avisados.append)                        # ya se sabe: contesta al momento
    assert avisados == [True, True]


def test_las_voces_empiezan_solas_en_cuanto_la_prueba_sale_bien(motor, monkeypatch):
    soltar = threading.Event()
    monkeypatch.setattr(vozgen, "_ejecutar_prueba", lambda o, t: (soltar.wait(10), 0)[1])
    monkeypatch.setattr(vozgen, "reparto", lambda: {"personajes": {"Encarna": "voz_e"}, "protagonista": {}})
    hechas = []

    class Falso(vozgen.Generador):
        def _guardar(self, f):
            hechas.append(f[2])
    g = Falso()
    monkeypatch.setattr(vozgen, "generador", g)

    class J:
        personaje, nombre, apellido, genero, voz, nombre_dicho = "propio", "Héctor", "", "h", "dani", ""

    class App:
        pruebas = False

    class P:
        app, j, datos = App(), J(), {"misiones": [{"id": "a", "pasos": [{"tipo": "dialogo", "lineas": [["Encarna", "Hola, Dani."], ["Encarna", "Adiós, Dani."]]}]}]}
        cfg = {"voces_grabadas": True, "voces_propias": True}
    assert vozgen.al_jugar(P) == 0 and vozgen.probando() and hechas == []       # el juego arranca sin esperar a nadie
    soltar.set()
    for _ in range(100):
        if len(hechas) == 2:
            break
        time.sleep(0.02)
    assert hechas == ["Hola, Héctor.", "Adiós, Héctor."]


def test_si_el_juego_se_cierra_dos_veces_cargando_el_motor_deja_de_intentarlo(motor):
    assert vozgen.disponible(esperar=True, ejecutar=lambda o, t: 0)
    vozgen._carga_a_medias(1)                                     # va a cargar... y el juego se cierra de golpe
    _olvidar()
    assert vozgen.disponible(esperar=True) is True                # una vez puede ser casualidad
    vozgen._carga_a_medias(1)                                     # segunda vez
    _olvidar()
    assert vozgen.disponible(esperar=True) is False and "se cerró mientras cargaba" in vozgen.motivo()
    # si carga y genera, la cuenta vuelve a cero
    vozgen._carga_a_medias(0)
    _olvidar()
    assert vozgen.disponible(esperar=True) is True
    assert json.load(open(vozgen.ruta_recuerdo(), encoding="utf-8"))["a_medias"] == 0


def test_un_proceso_de_prueba_que_se_cae_de_verdad_no_tumba_el_juego(motor, monkeypatch):
    """Un proceso aparte que muere como muere un programa con una instrucción que el procesador no tiene."""
    caida = [sys.executable, "-c", "import os; os._exit(0xC000001D & 0x7FFFFFFF)"]
    monkeypatch.setattr(vozgen, "orden_prueba", lambda: caida)
    assert vozgen._ejecutar_prueba(caida, 60) not in (0, None)
    assert vozgen.disponible(esperar=True) is False and "se ha cerrado de golpe" in vozgen.motivo()
    # y uno que no termina nunca se corta
    _olvidar()
    os.remove(vozgen.ruta_recuerdo())
    eterno = [sys.executable, "-c", "import time; time.sleep(60)"]
    t0 = time.time()
    assert vozgen._ejecutar_prueba(eterno, 1) is None and time.time() - t0 < 20
    # parar_prueba lo mata al cerrar el juego: el proceso es el propio programa y no puede quedarse abierto
    hilo = threading.Thread(target=lambda: vozgen._ejecutar_prueba(eterno, 60), daemon=True)
    hilo.start()
    for _ in range(100):
        if vozgen._prueba["proc"] is not None:
            break
        time.sleep(0.05)
    t0 = time.time()
    vozgen.parar_prueba()
    hilo.join(15)
    assert not hilo.is_alive() and time.time() - t0 < 15


def test_el_proceso_de_prueba_es_el_propio_juego(monkeypatch, tmp_path):
    assert vozgen.orden_prueba()[-2:] == [vozgen.ARG_PRUEBA, vozgen.carpeta_motor()] and vozgen.orden_prueba()[1].endswith("main.py")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "PuertoBravo.exe"))
    assert vozgen.orden_prueba() == [str(tmp_path / "PuertoBravo.exe"), vozgen.ARG_PRUEBA, vozgen.carpeta_motor()]      # compilado: el mismo programa
    monkeypatch.undo()
    texto = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py"), encoding="utf-8").read()
    assert texto.index(vozgen.ARG_PRUEBA) < texto.index("if ya_abierto()") < texto.index("registro.iniciar")       # antes del cerrojo y del registro


def test_el_motor_de_verdad_pasa_la_prueba_en_un_proceso_aparte():
    """Con el modelo en data/phonon: el juego, lanzado como proceso de prueba, carga el motor, dice una frase y termina con un cero."""
    if any(not os.path.exists(os.path.join(vozgen.carpeta_motor(), n)) for n in vozgen.ARCHIVOS_MOTOR):
        pytest.skip("esta copia no trae el generador de voces")
    try:
        import ptts  # noqa: F401
    except Exception:
        pytest.skip("el motor de voz no está instalado en este entorno")
    assert vozgen._ejecutar_prueba(vozgen.orden_prueba(), vozgen.TIEMPO_PRUEBA) == 0
    # con el modelo en otro sitio no carga, y lo dice con su código en vez de caerse
    mala = vozgen.orden_prueba()[:-1] + [os.path.join(vozgen.carpeta_motor(), "no_esta")]
    assert vozgen._ejecutar_prueba(mala, vozgen.TIEMPO_PRUEBA) == 11
