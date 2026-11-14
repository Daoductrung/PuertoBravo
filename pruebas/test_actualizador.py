"""El actualizador: firma, fuentes, descarga comprobada, extracción segura, instalador y menú. Nunca sale a internet."""
import base64
import hashlib
import io
import json
import os
import zipfile

import pygame
import pytest

from juego import VERSION, actualizador as A, ed25519
from juego.menus import Menu

SEMILLA = bytes(range(32))
PUBLICA = ed25519.publica(SEMILLA).hex()


def _zip(extra=None, con_exe=True):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        if con_exe:
            z.writestr(A.EJECUTABLE, b"MZ falso")
        z.writestr("data/datos/ciudad.pbd", b"datos")
        z.writestr("data/partidas/intruso.pbs", b"no debe llegar")
        for nombre, datos in (extra or {}).items():
            z.writestr(nombre, datos)
    return b.getvalue()


def _manifiesto(version="99.0.0", datos=None, semilla=SEMILLA, **cambios):
    datos = _zip() if datos is None else datos
    m = {"version": version, "file": f"PuertoBravo_v{version}.zip", "sha256": hashlib.sha256(datos).hexdigest(), "size": len(datos),
         "url": f"https://servidor.example/PuertoBravo/PuertoBravo_v{version}.zip",
         "espejos": {"github": f"https://github.com/x/y/releases/download/v{version}/PuertoBravo_v{version}.zip"}, "novedades": "Cosas nuevas."}
    m.update(cambios)
    m[A.CAMPO_FIRMA] = base64.b64encode(ed25519.firmar(semilla, A.serializar_canonico(m))).decode()
    return m


def _red(tabla):
    """Una red de mentira: dirección -> bytes, o una excepción que lanzar."""
    pedidas = []

    def abrir(url, tiempo=0):
        A.comprobar_url(url)
        pedidas.append(url)
        v = tabla.get(url)
        if v is None:
            raise OSError("no existe " + url)
        if isinstance(v, Exception):
            raise v
        return io.BytesIO(v)
    abrir.pedidas = pedidas
    return abrir


def test_ed25519_vectores_del_rfc():
    """Los tres primeros vectores oficiales del RFC 8032, y que cualquier cambio invalida la firma."""
    casos = [("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60", "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
              "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
             ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb", "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
              "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
             ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7", "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
              "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a")]
    for semilla, pub, msg, firma in casos:
        s, m = bytes.fromhex(semilla), bytes.fromhex(msg)
        assert ed25519.publica(s).hex() == pub
        assert ed25519.firmar(s, m).hex() == firma
        assert ed25519._verificar(bytes.fromhex(pub), m, bytes.fromhex(firma))
        assert ed25519.verificar(bytes.fromhex(pub), m, bytes.fromhex(firma))
        assert not ed25519._verificar(bytes.fromhex(pub), m + b"x", bytes.fromhex(firma))
        mala = bytearray(bytes.fromhex(firma))
        mala[5] ^= 1
        assert not ed25519._verificar(bytes.fromhex(pub), m, bytes(mala))
    assert not ed25519._verificar(b"\x00" * 31, b"", b"\x00" * 64)


def test_la_clave_del_juego_es_una_clave_valida():
    assert len(A.CLAVES_PUBLICAS) >= 1
    for c in A.CLAVES_PUBLICAS:
        assert len(bytes.fromhex(c)) == 32 and ed25519._descomprimir(bytes.fromhex(c)) is not None
    assert A.URL_SERVIDOR.startswith("https://") and A.URL_GITHUB.startswith("https://github.com/")
    A.clave_version(VERSION)


def test_versiones():
    assert A.es_mas_nueva("1.4.1", "1.4.0") and A.es_mas_nueva("1.10", "1.9.9") and A.es_mas_nueva("v2", "1.99.99")
    assert not A.es_mas_nueva("1.4.0", "1.4.0") and not A.es_mas_nueva("1.3.9", "1.4")
    with pytest.raises(ValueError):
        A.clave_version("la última")


def test_firma_del_manifiesto():
    m = _manifiesto()
    A.verificar_firma(m, (PUBLICA,))
    for campo, valor in (("version", "100.0.0"), ("sha256", "0" * 64), ("size", 1), ("url", "https://malo.example/x.zip"), ("novedades", "otra cosa")):
        tocado = dict(m)
        tocado[campo] = valor
        with pytest.raises(A.ErrorFirma):
            A.verificar_firma(tocado, (PUBLICA,))
    sin = dict(m)
    del sin[A.CAMPO_FIRMA]
    with pytest.raises(A.ErrorFirma):
        A.verificar_firma(sin, (PUBLICA,))
    with pytest.raises(A.ErrorFirma):                       # firmado por otro
        A.verificar_firma(_manifiesto(semilla=b"\x07" * 32), (PUBLICA,))
    with pytest.raises(A.ErrorFirma):                       # y con la clave real del juego, uno de pruebas no vale
        A.verificar_firma(m)


def test_solo_https():
    for mala in ("http://servidor.example/version.json", "ftp://x/y", "file:///c:/version.json", "servidor.example/version.json", "https://usuario:clave@servidor.example/v.json"):
        with pytest.raises(A.ErrorActualizacion):
            A.comprobar_url(mala)
    A.comprobar_url("https://servidor.example/version.json")
    with pytest.raises(A.ErrorActualizacion):
        A.fuentes_a_consultar("personalizada", "")
    with pytest.raises(A.ErrorActualizacion):
        A.fuentes_a_consultar("personalizada", "http://inseguro.example/version.json")
    assert [n for n, _ in A.fuentes_a_consultar("ambas")] == ["servidor", "github"]


def test_comprobar_en_cada_fuente():
    nuevo = json.dumps(_manifiesto("99.0.0")).encode()
    viejo = json.dumps(_manifiesto("0.0.1")).encode()
    mas = json.dumps(_manifiesto("99.5.0")).encode()
    # servidor
    red = _red({A.URL_SERVIDOR: nuevo})
    info = A.comprobar("servidor", abrir=red, claves=(PUBLICA,))
    assert info.version == "99.0.0" and info.fuente == "servidor" and info.urls == ["https://servidor.example/PuertoBravo/PuertoBravo_v99.0.0.zip"]
    assert red.pedidas == [A.URL_SERVIDOR] and info.novedades == "Cosas nuevas."
    # ya tienes la última
    assert A.comprobar("servidor", abrir=_red({A.URL_SERVIDOR: viejo}), claves=(PUBLICA,)) is None
    assert A.comprobar("servidor", abrir=_red({A.URL_SERVIDOR: nuevo}), claves=(PUBLICA,), version_actual="99.0.0") is None
    # github: se descarga de la release
    info = A.comprobar("github", abrir=_red({A.URL_GITHUB: nuevo}), claves=(PUBLICA,))
    assert info.fuente == "github" and info.urls == ["https://github.com/x/y/releases/download/v99.0.0/PuertoBravo_v99.0.0.zip"]
    # ambas: gana la más nueva y quedan las dos direcciones de descarga
    info = A.comprobar("ambas", abrir=_red({A.URL_SERVIDOR: nuevo, A.URL_GITHUB: mas}), claves=(PUBLICA,))
    assert info.version == "99.5.0" and info.fuente == "github" and len(info.urls) == 2
    # ambas, con una caída: se usa la otra
    info = A.comprobar("ambas", abrir=_red({A.URL_GITHUB: nuevo}), claves=(PUBLICA,))
    assert info.version == "99.0.0"
    # personalizada: el ZIP se busca junto al version.json
    propia = "https://mi.example/juegos/pb/version.json"
    info = A.comprobar("personalizada", propia, abrir=_red({propia: nuevo}), claves=(PUBLICA,))
    assert info.urls[0] == "https://mi.example/juegos/pb/PuertoBravo_v99.0.0.zip" and info.fuente == "personalizada"
    # errores
    with pytest.raises(A.ErrorRed):
        A.comprobar("servidor", abrir=_red({}), claves=(PUBLICA,))
    with pytest.raises(A.ErrorActualizacion, match="ninguna de las dos"):
        A.comprobar("ambas", abrir=_red({}), claves=(PUBLICA,))
    with pytest.raises(A.ErrorFirma):
        A.comprobar("servidor", abrir=_red({A.URL_SERVIDOR: b"<html>no soy json</html>"}), claves=(PUBLICA,))
    falso = json.dumps(_manifiesto("99.0.0", semilla=b"\x09" * 32)).encode()
    with pytest.raises(A.ErrorFirma):                       # alguien ha entrado en el servidor: sin la clave privada no cuela
        A.comprobar("servidor", abrir=_red({A.URL_SERVIDOR: falso}), claves=(PUBLICA,))
    raro = json.dumps(_manifiesto("99.0.0", file="..\\..\\malo.zip")).encode()
    with pytest.raises(A.ErrorFirma):
        A.comprobar("servidor", abrir=_red({A.URL_SERVIDOR: raro}), claves=(PUBLICA,))


def test_descarga_comprobada(tmp_path):
    datos = _zip()
    m = _manifiesto(datos=datos)
    info = A.comprobar("ambas", abrir=_red({A.URL_SERVIDOR: json.dumps(m).encode()}), claves=(PUBLICA,))
    pasos = []
    ruta = A.descargar(info, str(tmp_path), progreso=lambda h, t: pasos.append((h, t)), abrir=_red({info.urls[0]: datos}))
    assert open(ruta, "rb").read() == datos and pasos[-1] == (len(datos), len(datos))
    # el servidor falla y GitHub responde: se descarga del espejo
    ruta = A.descargar(info, str(tmp_path), abrir=_red({info.urls[1]: datos}))
    assert os.path.getsize(ruta) == len(datos)
    # archivo cambiado, cortado o demasiado largo: no se acepta y no queda nada a medias
    for malo in (datos[:-1] + bytes([datos[-1] ^ 1]), datos[:-10], datos + b"de mas"):
        if os.path.exists(ruta):
            os.remove(ruta)
        with pytest.raises(A.ErrorActualizacion):
            A.descargar(info, str(tmp_path), abrir=_red({info.urls[0]: malo, info.urls[1]: malo}))
        assert os.listdir(tmp_path) == []
    with pytest.raises(A.Cancelado):
        A.descargar(info, str(tmp_path), cancelado=lambda: True, abrir=_red({info.urls[0]: datos}))
    assert os.listdir(tmp_path) == []


def test_extraccion_segura(tmp_path):
    bueno = tmp_path / "bueno.zip"
    bueno.write_bytes(_zip({"lib/modulo.pyc": b"x", "data/radio/mi_musica/cancion.mp3": b"y"}))
    raiz = A.extraer(str(bueno), str(tmp_path / "nueva"))
    assert os.path.isfile(os.path.join(raiz, A.EJECUTABLE)) and os.path.isfile(os.path.join(raiz, "lib", "modulo.pyc"))
    assert not os.path.exists(os.path.join(raiz, "data", "partidas"))          # lo personal no viaja en una versión
    assert not os.path.exists(os.path.join(raiz, "data", "radio", "mi_musica"))
    for nombre in ("../fuera.txt", "data/../../fuera.txt", "/absoluto.txt", "c:/windows/fuera.txt"):
        malo = tmp_path / "malo.zip"
        malo.write_bytes(_zip({nombre: b"malo"}))
        with pytest.raises(A.ErrorFirma):
            A.extraer(str(malo), str(tmp_path / "nueva2"))
        assert not (tmp_path / "fuera.txt").exists()
    sin = tmp_path / "sin.zip"
    sin.write_bytes(_zip(con_exe=False))
    with pytest.raises(A.ErrorFirma):
        A.extraer(str(sin), str(tmp_path / "nueva3"))
    roto = tmp_path / "roto.zip"
    roto.write_bytes(b"esto no es un zip")
    with pytest.raises(A.ErrorFirma):
        A.extraer(str(roto), str(tmp_path / "nueva4"))


def test_instalador(tmp_path):
    nueva = tmp_path / "actualizacion" / "nueva"
    nueva.mkdir(parents=True)
    programa = tmp_path / "Puerto Bravo"
    programa.mkdir()
    bat = A.escribir_instalador(str(nueva), str(programa), pid=4321, version="99.0.0")
    crudo = open(bat, "rb").read()
    texto = crudo.decode("utf-8")
    assert b"\r\n" in crudo and b"\n" not in crudo.replace(b"\r\n", b"")
    assert "PID eq 4321" in texto and str(programa) in texto and A.ARG_TRAS_ACTUALIZAR in texto
    principal = next(l for l in texto.splitlines() if l.startswith('robocopy "%NUEVA%" "%APP%"'))
    for intocable in ("partidas", "config", "mi_musica"):
        assert intocable in principal.split("/xd")[1]                 # nunca se pisan
    assert "/mir" not in principal and ":fallo" in texto and 'robocopy "%COPIA%" "%APP%"' in texto
    assert not any("/mir" in l and ("mods" in l or "partidas" in l or "config" in l or "radio" in l) for l in texto.splitlines())
    with pytest.raises(A.ErrorActualizacion):
        A.escribir_instalador(str(nueva), str(tmp_path / "100% mío"), pid=1)


def test_publicar_firma_lo_que_el_juego_acepta(tmp_path):
    from herramientas import publicar
    m = publicar.firmar({"version": "99.0.0", "file": "x.zip", "sha256": "a" * 64, "size": 5}, SEMILLA)
    A.verificar_firma(m, (PUBLICA,))
    assert "herramientas/claves/" in open(".gitignore", encoding="utf-8").read()
    assert "publicar_destino.txt" in open(".gitignore", encoding="utf-8").read()
    notas = publicar.novedades()
    assert notas and "<" not in notas


def _elegir(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if texto.lower() in o.texto.lower())
    robot.tecla(pygame.K_RETURN)


def test_menu_de_actualizaciones(robot):
    app = robot.app
    cfg = app.cfg
    assert cfg["act_fuente"] == "servidor" and cfg["act_auto"] is True
    _elegir(robot, "Opciones")
    _elegir(robot, "Actualizaciones")
    m = app.pila[-1]
    assert m.titulo == "Actualizaciones" and VERSION in m.opciones[0].texto
    # elegir la fuente con las flechas: las cuatro
    m.i = next(k for k, o in enumerate(m.opciones) if "Actualizar desde" in o.texto)
    vistas = []
    for _ in range(4):
        robot.tecla(pygame.K_RIGHT)
        vistas.append(cfg["act_fuente"])
    assert vistas == ["github", "ambas", "personalizada", "servidor"]
    # dirección personalizada: solo https
    _elegir(robot, "Dirección personalizada")
    for c in "http://x.example/version.json":
        robot.tecla(0, unicode=c)
    robot.tecla(pygame.K_RETURN)
    assert cfg["act_url"] == "" and "https" in robot.dicho()
    _elegir(robot, "Dirección personalizada")
    for c in "https://mi.example/pb/version.json":
        robot.tecla(0, unicode=c)
    robot.tecla(pygame.K_RETURN)
    assert cfg["act_url"] == "https://mi.example/pb/version.json"
    # sin red: se dice claro y el juego sigue
    _elegir(robot, "Buscar actualizaciones ahora")
    robot.frames(3)
    assert app.pila[-1] is m and "No se pudo conectar" in robot.dicho()
    # ya tienes la última
    app.act_claves = (PUBLICA,)
    app.act_abrir = _red({A.URL_SERVIDOR: json.dumps(_manifiesto("0.0.1")).encode()})
    _elegir(robot, "Buscar actualizaciones ahora")
    robot.frames(3)
    assert "Tienes la última versión" in robot.dicho()
    # hay una nueva: se ofrece, se leen las novedades y, desde el código fuente, no se instala sola
    app.act_abrir = _red({A.URL_SERVIDOR: json.dumps(_manifiesto("99.0.0")).encode()})
    _elegir(robot, "Buscar actualizaciones ahora")
    robot.frames(3)
    oferta = app.pila[-1]
    assert "versión nueva, la 99.0.0" in oferta.titulo
    _elegir(robot, "Leer las novedades")
    assert "Cosas nuevas." in robot.dicho()
    _elegir(robot, "Descargar e instalar")
    assert app.pila[-1] is oferta and "código fuente" in robot.dicho()
    _elegir(robot, "Ahora no")
    assert app.pila[-1] is m


def test_descargar_e_instalar_de_principio_a_fin(robot, tmp_path, monkeypatch):
    """Como en el juego compilado: descarga, comprueba, extrae, escribe el instalador y se cierra. Sin tocar nada real."""
    from juego import menus_actualizar
    app = robot.app
    datos = _zip()
    m = _manifiesto(datos=datos)
    info = A.comprobar("servidor", abrir=_red({A.URL_SERVIDOR: json.dumps(m).encode()}), claves=(PUBLICA,))
    trabajo = tmp_path / "data" / "actualizacion"
    programa = tmp_path / "PuertoBravo"
    programa.mkdir()
    monkeypatch.setattr(A, "carpeta_trabajo", lambda: str(trabajo))
    monkeypatch.setattr(A, "puede_instalar", lambda: True)
    monkeypatch.setattr(A, "carpeta_programa", lambda: str(programa))
    lanzados = []
    monkeypatch.setattr(A, "lanzar_instalador", lambda bat: lanzados.append(bat))
    app.act_abrir = _red({info.urls[0]: datos})
    menus_actualizar.ofrecer(app, info)
    _elegir(robot, "Descargar e instalar")
    robot.frames(3)
    assert app.activo is False and "se actualiza y vuelve a abrirse" in robot.dicho()
    assert os.path.isfile(trabajo / "instalar_actualizacion.bat") and os.path.isfile(trabajo / "nueva" / A.EJECUTABLE)
    assert not os.path.exists(trabajo / m["file"])                    # el ZIP ya no hace falta
    assert lanzados == []                                             # en las pruebas no se lanza nada
    # una descarga manipulada no llega a instalarse
    app.activo = True
    app.act_abrir = _red({info.urls[0]: datos[:-1] + b"X"})
    menus_actualizar.descargar(app, info)
    robot.frames(3)
    assert app.activo is True and "no coincide" in robot.dicho() and not os.path.exists(trabajo)
