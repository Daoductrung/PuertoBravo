"""La configuración del servidor: una sola descripción de las opciones, de la que sale todo lo demás.

El ejemplo de servidor.conf, la comprobación de valores, el diálogo del panel y el apartado de opciones de la guía
salen de servidor/opciones.py. Aquí se comprueba que no se desajustan, que los valores se validan con mensajes claros
y que lo que se guarda se vuelve a leer igual.
"""
import glob
import os
import threading
import time

import pytest

from servidor import __main__ as arranque
from servidor import nucleo, opciones


def test_cada_opcion_esta_descrita_del_todo():
    secciones = [s[0] for s in opciones.SECCIONES]
    assert len({o.clave for o in opciones.OPCIONES}) == len(opciones.OPCIONES) >= 55
    for o in opciones.OPCIONES:
        assert o.seccion in secciones, o.clave
        assert len(o.etiqueta) >= 5 and not o.etiqueta.endswith((".", ":")), o.clave
        assert len(o.ayuda) >= 8 and o.ayuda.endswith("."), o.clave
        assert o.tipo in (opciones.TEXTO, opciones.SECRETO, opciones.ENTERO, opciones.ELECCION, opciones.SINO), o.clave
        valor, error = opciones.validar_valor(o.clave, o.defecto)
        assert error is None and valor == o.defecto, (o.clave, error)          # el valor de serie vale
        if o.tipo == opciones.ENTERO:
            assert isinstance(o.defecto, int) and o.minimo <= o.defecto <= o.maximo and o.maximo < 2 ** 31, o.clave
        if o.tipo == opciones.ELECCION:
            assert len(o.valores) >= 2 and o.defecto in o.permitidos() and all(d for _, d in o.valores), o.clave
        if o.tipo == opciones.SINO:
            assert o.defecto in ("si", "no"), o.clave
    for ident, titulo, que in opciones.SECCIONES:
        assert opciones.de_seccion(ident), ident                 # ninguna pestaña vacía
        assert len(opciones.de_seccion(ident)) <= 12, ident      # y ninguna tan larga que no quepa
    # el servidor arranca con estos valores, y no con otros apuntados en otra parte
    assert nucleo.CONFIG == opciones.valores_de_serie()
    # las que ya existían siguen, con su nombre de siempre
    for clave in ("nombre", "bienvenida", "puerto", "interfaz", "max_jugadores", "entrada", "clave", "datos", "cifrado", "certificado", "llave", "pvp",
                  "zonas_seguras", "modo_pasivo", "adultos", "botin", "botin_max", "atraco", "atraco_max", "robo_segundos", "trafico", "trafico_max",
                  "patrullas", "peatones", "policia", "peatones_max", "economia", "ganancia_hora", "saldo_inicial", "personajes", "venta_mercado",
                  "propiedad_dias", "recompensa", "proteccion", "precio_banda", "precio_barrio", "renta_barrio", "precio_guerra", "guerra_espera",
                  "guerra_dura", "vehiculos_horas", "vehiculos_por_jugador", "admins", "primer_admin", "registro_ip", "comprobar_datos",
                  "actualizar_mundo", "varias_sesiones"):
        assert clave in opciones.POR_CLAVE, clave
    # y las nuevas para quien administra
    for clave in ("mensaje_dia", "vetados", "copia_auto_horas", "copias_guardar", "guardado_minutos", "conexiones_por_ip", "inactividad_minutos",
                  "versiones", "version_minima", "radio_detalle", "trafico_total", "peatones_total", "registro_archivo"):
        assert clave in opciones.POR_CLAVE, clave
    assert opciones.POR_CLAVE["max_jugadores"].minimo == 0 and "0 no hay límite" in opciones.POR_CLAVE["max_jugadores"].ayuda


def test_ninguna_opcion_es_de_adorno():
    """Toda opción descrita la usa de verdad el servidor."""
    carpeta = os.path.dirname(nucleo.__file__)
    codigo = ""
    for ruta in glob.glob(os.path.join(carpeta, "*.py")):
        if os.path.basename(ruta) != "opciones.py":
            with open(ruta, encoding="utf-8") as f:
                codigo += f.read()
    sin_uso = [o.clave for o in opciones.OPCIONES if ('"%s"' % o.clave) not in codigo]
    assert not sin_uso, sin_uso


def test_el_ejemplo_trae_todas_las_opciones_comentadas(tmp_path, monkeypatch, capsys):
    texto = opciones.texto_conf()
    assert arranque.EJEMPLO == texto
    lineas = texto.split("\n")
    for o in opciones.OPCIONES:
        k = lineas.index(("%s = %s" % (o.clave, o.defecto)).rstrip())        # está, con su valor de serie...
        comentario = []
        while k > 0 and lineas[k - 1].startswith("#"):
            k -= 1
            comentario.append(lineas[k])
        junto = " ".join(c.lstrip("# ") for c in reversed(comentario))
        assert o.etiqueta in junto and "De serie" in junto, o.clave   # ...y explicada justo encima
        assert ("Necesita reiniciar" in junto) == o.reinicio, o.clave
        if o.tipo == opciones.ELECCION:
            assert all(v + ":" in junto for v in o.permitidos()), o.clave
    assert all(len(l) <= 112 for l in lineas if l.startswith("#")) and not any(l != l.rstrip() for l in lineas)
    for _, titulo, _ in opciones.SECCIONES:
        assert "# " + titulo.upper() in lineas
    # --ejemplo lo escribe, y no pisa uno que ya exista
    monkeypatch.chdir(tmp_path)
    assert arranque.main(["--ejemplo"]) == 0 and (tmp_path / "servidor.conf").read_text(encoding="utf-8") == texto
    assert arranque.main(["--ejemplo"]) == 1 and "No lo toco" in capsys.readouterr().out
    # lo que se lee de ahí es exactamente lo de serie, sin ningún aviso
    cfg, avisos = opciones.leer(str(tmp_path / "servidor.conf"))
    assert cfg == opciones.valores_de_serie() and not avisos
    assert arranque.main(["--comprobar"]) == 0 and "está bien" in capsys.readouterr().out
    assert arranque.main(["--opciones"]) == 0 and "max_jugadores = 32" in capsys.readouterr().out


def test_los_valores_se_comprueban_con_mensajes_claros(tmp_path, capsys):
    v = opciones.validar_valor
    # números: enteros y dentro de su rango
    assert v("puerto", "47821") == (47821, None) and v("puerto", " 80 ") == (80, None) and v("max_jugadores", "0") == (0, None)
    assert v("max_jugadores", 5000) == (5000, None)
    for malo in ("setenta", "", "12.5", "70000", "-1", None):
        valor, error = v("puerto", malo)
        assert valor is None and "entre 0 y 65535" in error, malo
    assert "entre 0 y 100" in v("botin", "150")[1] and "entre 1 y 120" in v("guardado_minutos", 0)[1]
    # sí o no, de las maneras en que la gente lo escribe
    for bueno in ("si", "sí", "SI", "Sí", "1", "true", "yes", True):
        assert v("pvp", bueno) == ("si", None), bueno
    for bueno in ("no", "NO", "0", "false", False):
        assert v("pvp", bueno) == ("no", None), bueno
    assert "si o no" in v("pvp", "quizá")[1] and "si o no" in v("pvp", "")[1]
    # elecciones: solo los valores permitidos, y se dice cuáles son
    assert v("entrada", "Invitación") == ("invitacion", None) and v("cifrado", "AUTO") == ("auto", None)
    assert "abierta, clave, invitacion" in v("entrada", "cerrada")[1] and "compatibles, iguales" in v("versiones", "todas")[1]
    # textos
    assert v("nombre", "  Mi servidor  ") == ("Mi servidor", None)
    assert "al menos dos letras" in v("nombre", "A")[1] and "más de 60 letras" in v("nombre", "x" * 61)[1]
    assert "saltos de línea" in v("bienvenida", "hola\nadiós")[1] and "no puede quedar vacía" in v("datos", " ")[1]
    assert v("version_minima", "") == ("", None) and v("version_minima", "1.7.0") == ("1.7.0", None) and "número de versión" in v("version_minima", "la última")[1]
    assert v("no_existe", 1)[1]
    # un archivo con de todo: lo que vale se usa, lo que no vuelve a su valor de serie, y cada cosa se dice con su línea o su nombre
    conf = tmp_path / "servidor.conf"
    conf.write_text("﻿# mi servidor\n\nnombre = La Taberna = el sitio # no es comentario\nPUERTO = 5000\nmax_jugadores = muchos\npvp = quizá\n"
                    "entrada = clave\nesto no es una opción\nopcion_del_futuro = 7\nbotin=101\n  trafico   =   no  \n", encoding="utf-8")
    cfg, avisos = opciones.leer(str(conf))
    assert cfg["nombre"] == "La Taberna = el sitio # no es comentario" and cfg["puerto"] == 5000 and cfg["trafico"] == "no"
    assert cfg["max_jugadores"] == 32 and cfg["pvp"] == "si" and cfg["botin"] == 10 and cfg["entrada"] == "clave"
    assert set(cfg) == set(opciones.valores_de_serie())           # lo desconocido no entra, y no falta nada
    texto = " | ".join(avisos)
    for trozo in ("Línea 8: no la entiendo", "Línea 9: no existe la opción opcion_del_futuro", "Máximo de jugadores a la vez (max_jugadores)",
                  "Combate entre jugadores (pvp): tiene que ser si o no", "(botin): tiene que estar entre 0 y 100", "la contraseña de entrada está vacía"):
        assert trozo in texto, trozo
    assert len(avisos) == 6
    # el servidor arranca igual con ese archivo (con lo de serie donde había errores), y --comprobar lo cuenta todo
    assert nucleo.leer_config(str(conf))["puerto"] == 5000
    avisos2 = []
    nucleo.leer_config(str(conf), avisos2)
    assert avisos2 == avisos
    assert arranque.main([str(conf), "--comprobar"]) == 1
    salida = capsys.readouterr().out
    assert "6 problemas" in salida and "opcion_del_futuro" in salida
    assert arranque.main([str(conf), "--comprobar", "--puerto=99999", "--inventada=1"]) == 1
    salida = capsys.readouterr().out
    assert "--puerto: tiene que estar entre 0 y 65535" in salida and "--inventada" in salida and "8 problemas" in salida
    assert arranque.main([str(tmp_path / "no_esta.conf"), "--comprobar"]) == 1 and "No hay ningún archivo" in capsys.readouterr().out
    # un archivo que no existe son los valores de serie
    assert opciones.leer(str(tmp_path / "no_esta.conf")) == (opciones.valores_de_serie(), [])


def test_un_conf_guardado_en_ansi_o_latin1_se_lee_igual_y_se_avisa(tmp_path):
    # Un servidor.conf guardado por un editor en ANSI de Windows o Latin-1 hacía caer el servidor al arrancar en Linux.
    conf = tmp_path / "servidor.conf"
    conf.write_bytes("# Servidor en línea\nnombre = La Peña\npuerto = 5000\n".encode("cp1252"))
    cfg, avisos = opciones.leer(str(conf))
    assert cfg["nombre"] == "La Peña" and cfg["puerto"] == 5000
    assert len(avisos) == 1 and "no está guardado en UTF-8" in avisos[0] and "servidor.conf" in avisos[0]
    assert nucleo.leer_config(str(conf))["puerto"] == 5000
    # un byte que el ANSI de Windows no define (0x81) tampoco tumba la lectura
    conf.write_bytes(b"nombre = Bar\x81\npuerto = 5001\n")
    cfg, avisos = opciones.leer(str(conf))
    assert cfg["puerto"] == 5001 and "no está guardado en UTF-8" in avisos[0]
    # y uno en UTF-8, con o sin marca, no avisa de nada
    conf.write_text("# Servidor en línea\nnombre = La Peña\n", encoding="utf-8-sig")
    assert opciones.leer(str(conf)) == (dict(opciones.valores_de_serie(), nombre="La Peña"), [])


def test_guardar_escribe_un_archivo_legible_que_se_lee_igual(tmp_path):
    conf = tmp_path / "sub" / "servidor.conf"
    cfg = dict(opciones.valores_de_serie(), nombre="El Rincón de Ñu = «café»", bienvenida="¡Hola! # todos", max_jugadores=0, puerto=5001, pvp="no",
               entrada="invitacion", admins="Ana, Blas el Largo", mensaje_dia="Mañana, 50% de descuento", version_minima="1.7.0", cifrado="si")
    assert opciones.guardar(str(conf), cfg) == []
    texto = conf.read_text(encoding="utf-8")
    assert "\r" not in texto and "nombre = El Rincón de Ñu = «café»" in texto and "# GENERAL" in texto and texto.count("\n# ") > 150
    leido, avisos = opciones.leer(str(conf))
    assert leido == cfg and not avisos
    assert not os.path.exists(str(conf) + ".nuevo")
    # guardar algo que no vale no estropea el archivo: se queda con lo de serie en eso, y lo cuenta
    problemas = opciones.guardar(str(conf), dict(cfg, puerto="abc", inventada=3))
    assert len(problemas) == 2 and opciones.leer(str(conf))[0]["puerto"] == 47820 and "inventada" not in conf.read_text(encoding="utf-8")
    # qué cambia al momento y qué pide reiniciar
    al_momento, con_reinicio = opciones.cambios(opciones.valores_de_serie(), dict(opciones.valores_de_serie(), puerto=1, bienvenida="x", cifrado="no", pvp="no"))
    assert al_momento == ["bienvenida", "pvp"] and con_reinicio == ["puerto", "cifrado"]
    assert {o.clave for o in opciones.OPCIONES if o.reinicio} == {"puerto", "interfaz", "cifrado", "certificado", "llave", "datos", "idioma"}


def test_la_guia_dice_lo_mismo_que_las_opciones_y_las_ordenes():
    from herramientas import preparar_carpeta_servidor as carpeta
    assert carpeta.guia_al_dia(), "La guía del servidor no está al día: ejecuta herramientas\\preparar_carpeta_servidor.py --guia"
    with open(carpeta.GUIA, encoding="utf-8") as f:
        guia = f.read()
    for o in opciones.OPCIONES:
        assert "<code>%s</code>" % o.clave in guia, o.clave
    for _, titulo, _ in opciones.SECCIONES:
        assert "<h3>%s</h3>" % titulo in guia
    for orden, _ in nucleo.Servidor.AYUDA_ORDENES:
        assert "<li><code>%s</code>" % orden in guia, orden
    # sin tablas, con los encabezados en orden y sin saltos de nivel
    assert "<table" not in guia and guia.count("<h1>") == 1
    import re
    niveles = [int(n) for n in re.findall(r"<h([1-6])[ >]", guia)]
    assert all(b - a <= 1 for a, b in zip(niveles, niveles[1:])), "hay un salto de nivel entre encabezados"
    ids = re.findall(r'<h2 id="([a-z]+)"', guia)
    assert len(ids) == len(set(ids)) >= 20 and all('href="#%s"' % i in guia for i in ids if i != "indice")
    # todas las maneras de montarlo tienen su apartado
    for trozo in ("con el panel", "por consola", "Que arranque solo con Windows", "servidor alquilado", "systemd", "Raspberry Pi", "Mac", "Docker",
                  "Synology", "Container Manager", "abrir el puerto en el router", "UPnP", "DNS dinámico", "Tailscale", "ZeroTier", "Cifrado y certificado",
                  "Copias de seguridad", "Mover el servidor", "Actualizar el servidor", "Solución de problemas", "versiones distintas"):
        assert trozo in guia, trozo
    # nada de nadie: ni direcciones de un equipo concreto, ni rutas de usuario
    import getpass
    for malo in ("Users\\", "/home/x", getpass.getuser()):       # el nombre de quien compila, sea quien sea
        assert malo not in guia, malo


def test_parar_con_orden_un_servidor_sin_consola(tmp_path, capsys):
    """Un servidor arrancado sin nadie delante (una tarea programada, un servicio) se para con --parar: lo guarda todo."""
    conf = tmp_path / "servidor.conf"
    datos = tmp_path / "datos"
    opciones.guardar(str(conf), dict(opciones.valores_de_serie(), datos=str(datos), puerto=0, interfaz="127.0.0.1", cifrado="no", personajes=0))
    assert arranque.main([str(conf), "--parar"]) == 1 and "no hay ningún servidor que parar" in capsys.readouterr().out
    salida = []
    hilo = threading.Thread(target=lambda: salida.append(arranque.main([str(conf)])), daemon=True)
    hilo.start()
    fin = time.time() + 15
    while time.time() < fin and not (datos / "puertobravo.db").exists():
        time.sleep(0.1)
    time.sleep(1.0)
    assert hilo.is_alive()
    assert arranque.main([str(conf), "--parar"]) == 0
    hilo.join(20)
    assert not hilo.is_alive() and salida == [0]
    dicho = capsys.readouterr().out
    assert "ha recogido la orden" in dicho and "Se ha pedido parar el servidor" in dicho and "Servidor parado. Todo guardado." in dicho
    assert "no hay límite" not in dicho and "Caben 32 jugadores" in dicho
    assert not (datos / arranque.ARCHIVO_PARAR).exists()
    # y con él ya parado, nadie recoge la orden
    assert arranque.pedir_parada({"datos": str(datos)}, espera=1.5) is False
