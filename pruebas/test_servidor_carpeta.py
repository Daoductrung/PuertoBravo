"""La carpeta del servidor que va dentro del juego compilado, las copias de seguridad y el servidor funcionando solo.

- La carpeta trae todo lo necesario para montar un servidor de cualquier manera, y nada de nadie.
- El código del servidor funciona con Python y nada más: sin el juego, sin wxPython, sin ninguna biblioteca.
- Las copias de seguridad se hacen, se podan y se restauran, también para llevar el servidor a otra carpeta.
"""
import os
import shutil
import subprocess
import sys
import time
import zipfile

import pytest

from herramientas import comprobar_limpio
from herramientas import preparar_carpeta_servidor as carpeta
from servidor import copias, nucleo, opciones
from test_servidor import Banco, Cli, mundo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def juego(tmp_path_factory):
    """Una carpeta que hace de juego compilado, con la guía en su sitio, y la carpeta del servidor ya preparada."""
    base = tmp_path_factory.mktemp("juego")
    os.makedirs(base / "data" / "docs")
    for cod, ruta in carpeta.guias().items():                 # la guía en cada idioma que haya
        shutil.copyfile(ruta, base / "data" / "docs" / ("servidor_%s.html" % cod))
    carpeta.preparar(str(base))
    return base


def _leer(ruta):
    with open(ruta, "rb") as f:
        return f.read()


def test_la_carpeta_del_servidor_trae_todo_y_nada_de_nadie(juego):
    s = juego / "servidor"
    assert carpeta.comprobar(str(juego)) == [] and comprobar_limpio.servidor_completo_y_limpio(str(juego)) == []
    # para Windows: los lanzadores, con finales de línea de Windows y sin letras que la consola estropee
    for nombre in carpeta.LANZADORES:
        datos = _leer(s / nombre)
        assert datos.count(b"\r\n") >= 5 and datos.count(b"\n") == datos.count(b"\r\n") and all(b < 128 for b in datos), nombre
        assert b"%~dp0" in datos or b"APPDATA" in datos, nombre
    assert b"PuertoBravoServidorPanel.exe" in _leer(s / "Panel del servidor.bat")
    assert b"PuertoBravoServidor.exe" in _leer(s / "Servidor por consola.bat") and b"--ejemplo" in _leer(s / "Servidor por consola.bat")
    assert b"--parar" in _leer(s / "Parar el servidor.bat")
    assert b"Startup" in _leer(s / "Arrancar con Windows - activar.bat") and b"schtasks" not in _leer(s / "Arrancar con Windows - activar.bat")
    # el ejemplo de configuración y la guía, al día
    assert (s / "servidor.conf.ejemplo").read_text(encoding="utf-8") == opciones.texto_conf() and b"\r\n" in _leer(s / "servidor.conf.ejemplo")
    for cod in carpeta.guias():
        guia = s / ("documentacion_%s.html" % cod)
        assert _leer(guia) == _leer(juego / "data" / "docs" / ("servidor_%s.html" % cod)) and carpeta.guia_al_dia(str(guia)), cod
    assert not (s / "documentacion.html").exists()
    assert "Panel del servidor" in (s / "LEEME.txt").read_text(encoding="utf-8")
    # para los demás sistemas: el código entero del servidor, igual que el del proyecto, y con finales de línea de Unix
    otros = s / "otros_sistemas"
    del_proyecto = sorted(n for n in os.listdir(os.path.join(RAIZ, "servidor")) if n.endswith(".py"))
    assert sorted(n for n in os.listdir(otros / "servidor")) == sorted(del_proyecto + ["mundo.json", "idiomas"])
    assert os.listdir(otros / "servidor" / "idiomas") == ["en.json"]           # el catálogo reducido: solo los textos del servidor
    for n in del_proyecto:
        copia = _leer(otros / "servidor" / n)
        assert b"\r" not in copia and copia == _leer(os.path.join(RAIZ, "servidor", n)).replace(b"\r\n", b"\n"), n
    for n in carpeta.GUIONES:
        datos = _leer(otros / n)
        assert datos.startswith(b"#!/bin/sh\n") and b"\r" not in datos, n
    assert b"python3 -m servidor" in _leer(otros / "arrancar.sh") and b"kill -TERM" in _leer(otros / "parar.sh")
    docker = (otros / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY servidor /app/servidor" in docker and "entrada_docker.sh" in docker and "EXPOSE 47820" in docker and "\r" not in docker
    compose = (otros / "docker-compose.yml").read_text(encoding="utf-8")
    assert "build: ." in compose and '"47820:47820"' in compose and "./datos:/datos" in compose and "\t" not in compose
    entrada = (otros / "entrada_docker.sh").read_text(encoding="utf-8")
    assert "python -m servidor servidor.conf" in entrada and "--ejemplo" in entrada and "setpriv" in entrada
    servicio = (otros / "puertobravo.service").read_text(encoding="utf-8")
    assert "ExecStart=/usr/bin/python3 -m servidor servidor.conf" in servicio and "WantedBy=multi-user.target" in servicio and "KillSignal=SIGTERM" in servicio
    assert (otros / "servidor.conf.ejemplo").read_text(encoding="utf-8") == opciones.texto_conf() and b"\r" not in _leer(otros / "servidor.conf.ejemplo")
    # nada personal: ni el nombre de usuario de este equipo, ni la carpeta del proyecto, ni claves, ni datos
    marcas = [m.encode("utf-8") for m in {os.path.expanduser("~"), RAIZ, os.path.basename(os.path.expanduser("~"))} if len(m) > 3]
    for base, dirs, archivos in os.walk(s):
        assert "__pycache__" not in dirs and "despliegue" not in dirs and "claves" not in dirs
        for a in archivos:
            assert not a.endswith((".db", ".pem", ".key", ".pyc", ".log")), a
            datos = _leer(os.path.join(base, a))
            assert not any(m in datos for m in marcas), a


def test_preparar_la_carpeta_no_toca_lo_que_ya_tenga_un_servidor(juego):
    s = juego / "servidor"
    try:
        (s / "servidor.conf").write_text("nombre = El mío\n", encoding="utf-8")
        os.makedirs(s / "datos_servidor" / "copias")
        (s / "datos_servidor" / "puertobravo.db").write_bytes(b"datos")
        carpeta.preparar(str(juego))
        assert (s / "servidor.conf").read_text(encoding="utf-8") == "nombre = El mío\n" and (s / "datos_servidor" / "puertobravo.db").read_bytes() == b"datos"
        # pero una carpeta así no se puede repartir, y la comprobación de la compilación lo dice
        problemas = " | ".join(comprobar_limpio.servidor_completo_y_limpio(str(juego)))
        assert "servidor.conf" in problemas and "datos_servidor" in problemas and "puertobravo.db" in problemas
    finally:
        os.remove(s / "servidor.conf")
        shutil.rmtree(s / "datos_servidor")
    assert comprobar_limpio.servidor_completo_y_limpio(str(juego)) == []
    # y si falta algo, también lo dice
    os.remove(s / "otros_sistemas" / "Dockerfile")
    os.remove(s / "Panel del servidor.bat")
    faltan = " | ".join(carpeta.comprobar(str(juego)))
    assert "Dockerfile" in faltan and "Panel del servidor.bat" in faltan
    carpeta.preparar(str(juego))
    assert carpeta.comprobar(str(juego)) == []


def test_la_compilacion_incluye_el_panel_y_la_carpeta_del_servidor():
    with open(os.path.join(RAIZ, "setup_cx.py"), encoding="utf-8") as f:
        setup = f.read()
    assert '"panel_servidor"' in setup and 'Executable("servidor_panel.py", base="gui", target_name="PuertoBravoServidorPanel.exe")' in setup
    assert 'Executable("servidor_main.py", base="console", target_name="PuertoBravoServidor.exe")' in setup and "servidor_despliegue" not in setup
    with open(os.path.join(RAIZ, "compilar.bat"), encoding="utf-8") as f:
        compilar = f.read()
    assert 'herramientas\\preparar_carpeta_servidor.py "%D%"' in compilar and "herramientas\\preparar_carpeta_servidor.py --guia" in compilar
    assert compilar.index("preparar_carpeta_servidor.py --guia") < compilar.index('xcopy /e /i /y /q "data\\docs"') < compilar.index('preparar_carpeta_servidor.py "%D%"')
    assert compilar.index('preparar_carpeta_servidor.py "%D%"') < compilar.index("comprobar_limpio.py")
    with open(os.path.join(RAIZ, "herramientas", "comprobar_limpio.py"), encoding="utf-8") as f:
        limpio = f.read()
    assert "PuertoBravoServidorPanel.exe" in limpio and "servidor_completo_y_limpio" in limpio
    for entrada in ("servidor_panel.py", "servidor_panel.bat", "servidor_main.py", "servidor.bat"):
        assert os.path.exists(os.path.join(RAIZ, entrada)), entrada


def test_el_servidor_funciona_solo_con_python_sin_el_juego(juego, tmp_path):
    """Se copia la carpeta para otros sistemas a un sitio aparte y se arranca desde ahí: no carga nada que no sea suyo
    o de la biblioteca de serie de Python."""
    destino = tmp_path / "puertobravo"
    shutil.copytree(juego / "servidor" / "otros_sistemas", destino)
    codigo = r'''
import os, sys, threading, time
antes = set(sys.modules)
sys.path.insert(0, os.getcwd())
import servidor.__main__ as arranque
assert os.path.dirname(os.path.abspath(arranque.__file__)).startswith(os.getcwd()), arranque.__file__
assert arranque.main(["--ejemplo"]) == 0 and arranque.main(["--comprobar"]) == 0
texto = open("servidor.conf", encoding="utf-8").read().replace("puerto = 47820", "puerto = 0").replace("interfaz = 0.0.0.0", "interfaz = 127.0.0.1")
open("servidor.conf", "w", encoding="utf-8").write(texto)
salida = []
hilo = threading.Thread(target=lambda: salida.append(arranque.main([])), daemon=True)
hilo.start()
fin = time.time() + 60
while time.time() < fin and not os.path.exists(os.path.join("datos_servidor", "certificado.pem")):
    time.sleep(0.2)
time.sleep(1.5)
assert hilo.is_alive(), "el servidor no ha arrancado"
assert arranque.main(["--parar"]) == 0
hilo.join(30)
assert salida == [0], salida
de_fuera = sorted(n for n, m in sys.modules.items() if n not in antes and getattr(m, "__file__", None) and ("site-packages" in m.__file__ or os.sep + "juego" + os.sep in m.__file__))
prohibidos = sorted(n for n in sys.modules if n.split(".")[0] in ("juego", "editor", "panel_servidor", "wx", "pygame", "numpy", "cryptography", "accessible_output2"))
print("DE_FUERA", de_fuera)
print("PROHIBIDOS", prohibidos)
print("CARGADOS", sorted(n for n in sys.modules if n.startswith("servidor")))
'''
    r = subprocess.run([sys.executable, "-I", "-c", codigo], cwd=str(destino), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-3000:]
    assert "DE_FUERA []" in r.stdout and "PROHIBIDOS []" in r.stdout, r.stdout[-2000:]
    assert "servidor.nucleo" in r.stdout and "servidor.opciones" in r.stdout and "servidor.copias" in r.stdout
    assert "con cifrado" in r.stdout and "Servidor parado. Todo guardado." in r.stdout
    # ha dejado su configuración, sus datos y su certificado, hecho por él mismo
    assert (destino / "servidor.conf").exists() and (destino / "datos_servidor" / "puertobravo.db").exists()
    assert (destino / "datos_servidor" / "certificado.pem").exists() and (destino / "datos_servidor" / "llave.pem").exists()
    # y su código vale para el Python más antiguo que se admite, el 3.8
    import ast
    for n in os.listdir(destino / "servidor"):
        if n.endswith(".py"):
            ast.parse((destino / "servidor" / n).read_text(encoding="utf-8"), n, feature_version=(3, 8))


def test_copias_de_seguridad_restaurar_y_mover_el_servidor(tmp_path):
    datos = tmp_path / "datos"
    conf = tmp_path / "servidor.conf"
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), nombre="El original", datos=str(datos)))
    banco = Banco(datos)
    try:
        banco.srv.ruta_conf = str(conf)
        banco.hacer(lambda: banco.srv._poner_mundo(mundo()))      # el mundo con el que trabaja queda en disco, como en un servidor de verdad
        a = Cli(banco, "Ana")
        a.estado(di=777)
        a.enviar({"t": "guardar", "p": {"nombre": "Ana", "dinero": 777}, "ya": True})
        a.leer("guardado")
        banco.hacer(banco.srv.orden, "invitar")
        (datos / "certificado.pem").write_text("CERTIFICADO DE PRUEBA", encoding="ascii")
        (datos / "llave.pem").write_text("LLAVE DE PRUEBA", encoding="ascii")
        ruta = banco.hacer(banco.srv.copia_seguridad)
        # en caliente, con el servidor en marcha, y con todo lo que hace falta para dejarlo como estaba
        assert os.path.dirname(ruta) == str(datos / "copias") and os.path.basename(ruta).startswith("copia_2")
        with zipfile.ZipFile(ruta) as z:
            assert sorted(z.namelist()) == ["certificado.pem", "llave.pem", "mundo_actual.json", "puertobravo.db", "servidor.conf"]
        assert copias.contenido(ruta) and copias.listar(str(datos))[0][0] == ruta and not copias.listar(str(datos))[0][3]
        # después de la copia pasan cosas que la copia no tiene
        b = Cli(banco, "Blas")
        assert b.ok
    finally:
        banco.parar()
    # las automáticas se podan; las hechas a mano no se tocan
    for n in range(5):
        r = copias.hacer(str(datos), automatica=True)
        os.utime(r, (time.time() + n, time.time() + n))
    assert copias.podar(str(datos), 2) == 3
    lista = copias.listar(str(datos))
    assert [c[3] for c in lista] == [True, True, False] and lista[2][0] == ruta
    assert not [n for n in os.listdir(datos / "copias") if n.endswith(".tmp")]
    # restaurar en el mismo sitio: vuelve a como estaba, y lo que había queda guardado por si acaso
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), nombre="Cambiado después", datos=str(datos)))
    previa, restaurados = copias.restaurar(ruta, str(datos), conf=str(conf))
    assert os.path.basename(previa).startswith("antes_de_restaurar_") and "puertobravo.db" in restaurados and "servidor.conf" not in restaurados
    assert opciones.leer(str(conf))[0]["nombre"] == "Cambiado después"          # la configuración solo se toca si se pide
    banco = Banco(datos, de_disco=True)
    try:
        nombres = [c["nombre"] for c in banco.hacer(banco.srv.lista_cuentas)]
        assert nombres == ["Ana"] and len(banco.hacer(banco.srv.lista_invitaciones)) == 1
        a2 = Cli(banco, "Ana")
        assert a2.ok["partida"] == {"nombre": "Ana", "dinero": 777} and a2.ok["admin"]
    finally:
        banco.parar()
    with zipfile.ZipFile(previa) as z:                           # en la copia de lo que había sí estaba Blas
        z.extract("puertobravo.db", str(tmp_path / "previa"))
    import sqlite3
    c = sqlite3.connect(str(tmp_path / "previa" / "puertobravo.db"))
    assert [f[0] for f in c.execute("SELECT nombre FROM cuentas ORDER BY nombre")] == ["Ana", "Blas"]
    c.close()
    # mover el servidor a otra carpeta, o a otra máquina: con la copia basta, configuración y certificado incluidos
    otra, otra_conf = tmp_path / "otra_maquina" / "datos_servidor", tmp_path / "otra_maquina" / "servidor.conf"
    previa2, restaurados = copias.restaurar(ruta, str(otra), conf=str(otra_conf), con_conf=True)
    assert previa2 is None and sorted(restaurados) == ["certificado.pem", "llave.pem", "mundo_actual.json", "puertobravo.db", "servidor.conf"]
    assert opciones.leer(str(otra_conf))[0]["nombre"] == "El original" and (otra / "llave.pem").read_text(encoding="ascii") == "LLAVE DE PRUEBA"
    banco = Banco(otra, de_disco=True)
    try:
        assert [c["nombre"] for c in banco.hacer(banco.srv.lista_cuentas)] == ["Ana"]
    finally:
        banco.parar()
    # lo que no es una copia se rechaza con un mensaje claro, y no se toca nada
    malo = tmp_path / "no_es_copia.zip"
    malo.write_bytes(b"esto no es un zip")
    with pytest.raises(ValueError, match="no es una copia de seguridad"):
        copias.restaurar(str(malo), str(otra))
    with zipfile.ZipFile(malo, "w") as z:
        z.writestr("otra_cosa.txt", "hola")
    with pytest.raises(ValueError, match="no trae la base de datos"):
        copias.restaurar(str(malo), str(otra))
    with zipfile.ZipFile(malo, "w") as z:
        z.writestr("puertobravo.db", "esto no es una base de datos")
        z.writestr("../fuera.txt", "no debe salir de la carpeta")
    with pytest.raises(ValueError, match="está dañada"):
        copias.restaurar(str(malo), str(otra))
    assert not (tmp_path / "otra_maquina" / "fuera.txt").exists() and not (otra / "puertobravo.db.restaurando").exists()
    banco = Banco(otra, de_disco=True)
    try:
        assert [c["nombre"] for c in banco.hacer(banco.srv.lista_cuentas)] == ["Ana"]
    finally:
        banco.parar()
