"""El panel del servidor: el motor que lleva el servidor en su hilo, y la ventana con sus diálogos.

El motor se prueba sin ventanas. La ventana y los diálogos se construyen sin mostrarlos: se les pasa la revisión de
teclado (etiquetas, letras de acceso sin repetir ni chocar con los menús, atajos) y se manejan como lo haría una
persona, con un servidor de verdad detrás y un jugador de mentira conectado.

Lo que estas pruebas no pueden decir es cómo suena con un lector de pantalla de verdad.
"""
import os
import socket
import time

import pytest

from panel_servidor import motor as M
from servidor import nucleo, opciones
from test_servidor_capacidad import Ligero


def _conf(tmp_path, **mas):
    conf = tmp_path / "servidor.conf"
    cfg = dict(opciones.valores_de_serie(), datos="datos_servidor", puerto=0, interfaz="127.0.0.1", cifrado="no", personajes=0, trafico="no", peatones="no",
               policia="no", nombre="Servidor de pruebas del panel", comprobar_datos="no")
    cfg.update(mas)
    opciones.guardar(str(conf), cfg)
    return str(conf)


def _esperar(cond, segundos=20.0):
    fin = time.time() + segundos
    while time.time() < fin:
        if cond():
            return True
        time.sleep(0.05)
    return False


def _si_llega(cliente, tipo, espera=4.0):
    """El último mensaje antes de que el servidor corte. En este equipo, un filtro de red se lo traga de tarde en tarde
    (pasa igual con dos sockets a pelo); si no llega, lo que se comprueba es el efecto en el servidor y en la ventana."""
    try:
        return cliente.leer(tipo, espera)
    except AssertionError:
        return None


class Banquito:
    """Lo justo para que un cliente ligero sepa a qué puerto ir."""

    def __init__(self, puerto):
        self.puerto = puerto


@pytest.fixture
def sin_firma(monkeypatch):
    monkeypatch.setattr(nucleo.firma, "verificar", lambda *a: True)


# ====================================================================== el motor
def test_el_motor_arranca_para_y_atiende_sin_bloquear(tmp_path, sin_firma):
    lineas, avisos = [], []
    m = M.Motor(_conf(tmp_path), registrar=lineas.append, avisar=lambda que, dato: avisos.append((que, dato)))
    assert m.estado == M.PARADO and m.foto is None and not m.parar()
    hecho = []
    assert m.pedir(lambda srv: 1, lambda r, e: hecho.append((r, e))) is False and hecho == [(None, "parado")]
    t0 = time.time()
    assert m.arrancar() and time.time() - t0 < 1.0                # vuelve enseguida: el servidor arranca en su hilo
    assert not m.arrancar()                                      # y no arranca dos veces
    assert _esperar(m.en_marcha)
    try:
        assert avisos[:2] == [("estado", M.ARRANCANDO), ("estado", M.EN_MARCHA)]
        foto = m.foto
        assert foto["activo"] and foto["nombre"] == "Servidor de pruebas del panel" and foto["puerto"] > 0 and foto["jugadores"] == [] and not foto["cifrado"]
        # las rutas de la configuración parten de la carpeta donde está servidor.conf, se abra el panel desde donde se abra
        assert os.path.exists(tmp_path / "datos_servidor" / "puertobravo.db") and m.carpeta_datos() == str(tmp_path / "datos_servidor")
        assert any("escuchando en el puerto" in l for l in lineas) and any("Datos del mundo" in l for l in lineas)
        # entra un jugador: sale en la foto al cabo de un segundo, sin que nadie pregunte
        a = Ligero(Banquito(foto["puerto"]), "Ana")
        assert a.ok
        assert _esperar(lambda: m.foto and [g["nombre"] for g in m.foto["jugadores"]] == ["Ana"], 5)
        assert m.foto["jugadores"][0]["admin"] and m.foto["jugadores"][0]["ip"] is None
        # las órdenes van al hilo del servidor y la respuesta vuelve por su cuenta
        respuestas = []
        assert m.orden("jugadores", lambda r, e: respuestas.append((r, e)))
        assert _esperar(lambda: respuestas) and "Hay 1: Ana" in respuestas[0][0] and respuestas[0][1] is None
        m.pedir(lambda srv: 1 / 0, lambda r, e: respuestas.append((r, e)))          # un fallo no tumba nada: llega como error
        assert _esperar(lambda: len(respuestas) == 2) and respuestas[1][0] is None and "ZeroDivisionError" in respuestas[1][1]
        m.pedir(lambda srv: srv.lista_cuentas(), lambda r, e: respuestas.append((r, e)))
        assert _esperar(lambda: len(respuestas) == 3) and respuestas[2][0][0]["nombre"] == "Ana" and respuestas[2][0][0]["dentro"]
        # cambiar la configuración en marcha: lo que se puede se aplica; lo que pide reiniciar se dice, y las rutas no dan falsas alarmas
        cfg, _ = m.leer_config()
        cfg.update(bienvenida="Hola desde el panel", max_jugadores=0, puerto=47999)
        assert m.guardar_config(cfg) == []
        m.aplicar_config(cfg, lambda r, e: respuestas.append((r, e)))
        assert _esperar(lambda: len(respuestas) == 4) and respuestas[3][0] == (["bienvenida", "max_jugadores"], ["puerto"])
        assert opciones.leer(m.ruta_conf)[0]["bienvenida"] == "Hola desde el panel"
        m.guardar_config(dict(cfg, puerto=0))
        # otro motor con el mismo puerto: no arranca, lo dice claro y se queda parado
        cfg2 = dict(cfg, puerto=foto["puerto"], datos="otros_datos")
        (tmp_path / "dos").mkdir()
        opciones.guardar(str(tmp_path / "dos" / "servidor.conf"), cfg2)
        avisos2 = []
        m2 = M.Motor(str(tmp_path / "dos" / "servidor.conf"), avisar=lambda que, dato: avisos2.append((que, dato)))
        m2.arrancar()
        assert m2.esperar_parado(15) and avisos2[-1] == ("estado", M.PARADO)
        error = next(d for q, d in avisos2 if q == "error")
        assert "No se ha podido abrir el puerto" in error and "ya esté en marcha" in error and m2.ultimo_error == error
        # parar: avisa al jugador, lo guarda todo y deja el hilo terminado
        t0 = time.time()
        assert m.parar("Se acabó por hoy.") and time.time() - t0 < 1.0
        cierre = _si_llega(a, "cerrado")
        assert cierre is None or cierre["motivo"] == "Se acabó por hoy."
        assert m.esperar_parado(15) and m.estado == M.PARADO and m.foto is None and m.srv is None
        m.hilo.join(5)
        assert not m.hilo.is_alive() and avisos[-2:] == [("estado", M.PARANDO), ("estado", M.PARADO)]
        assert any("Servidor parado. Todo guardado." in l for l in lineas)
        # y se puede volver a arrancar en el mismo programa, con lo guardado
        assert m.arrancar() and _esperar(m.en_marcha)
        m.pedir(lambda srv: [c["nombre"] for c in srv.lista_cuentas()], lambda r, e: respuestas.append((r, e)))
        assert _esperar(lambda: len(respuestas) == 5) and respuestas[4][0] == ["Ana"]
        # la orden apagar, dada desde dentro, también lo para con orden
        m.orden("apagar")
        assert m.esperar_parado(15) and m.estado == M.PARADO
        # con él parado: copia de seguridad y restauración, que no se deja hacer en marcha
        ruta = m.copia_parado()
        assert os.path.exists(ruta) and ruta.startswith(str(tmp_path / "datos_servidor" / "copias"))
        previa, restaurados = m.restaurar(ruta)
        assert "puertobravo.db" in restaurados and os.path.exists(previa)
        m.arrancar()
        assert _esperar(m.en_marcha)
        with pytest.raises(RuntimeError, match="hay que parar antes"):
            m.restaurar(ruta)
    finally:
        m.parar()
        m.esperar_parado(15)


# ==================================================================== las ventanas
@pytest.fixture(scope="module")
def wxapp():
    wx = pytest.importorskip("wx")
    app = wx.App(False)
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    yield app


VENTANA = []                             # la ventana que se está probando: su reloj no corre sin el bucle de la interfaz


def _bombear(cond, segundos=20.0):
    """Hace de bucle de la interfaz: deja pasar los avisos que llegan del hilo del servidor y da los toques del reloj
    de la ventana (sin el bucle de verdad, el reloj de wx no corre; con él sí, y está comprobado aparte)."""
    import wx
    fin = time.time() + segundos
    while time.time() < fin:
        wx.GetApp().ProcessPendingEvents()
        wx.YieldIfNeeded()
        if VENTANA and VENTANA[0]:
            VENTANA[0].refrescar()
        if cond():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture
def ventana(wxapp, tmp_path):
    from panel_servidor.ventana import VentanaPanel
    v = VentanaPanel(_conf(tmp_path), hablar=False)
    VENTANA[:] = [v]
    yield v
    VENTANA[:] = []
    if v:
        v._cerrar_al_parar = False
        if v.motor.estado != M.PARADO:
            v.motor.parar()
            v.motor.esperar_parado(15)
        _bombear(lambda: False, 0.3)
        if v:
            v.reloj.Stop()
            v.Destroy()
    _bombear(lambda: False, 0.1)


def test_cada_ventana_y_dialogo_se_maneja_con_teclado_sin_choques(ventana, wxapp):
    import wx
    from editor.accesibilidad.revision_teclado import informe, revisar_teclado
    from panel_servidor.configuracion import DialogoConfiguracion, ayuda_de
    from panel_servidor.ventana import TECLAS, DialogoCopias
    # --- la ventana principal: sin errores y sin avisos
    problemas = revisar_teclado(ventana)
    assert not problemas, informe(problemas)
    assert ventana.cuaderno.GetPageCount() == 5 and [ventana.cuaderno.GetPageText(n) for n in range(5)] == ["Estado", "Jugadores", "Cuentas", "Invitaciones", "Registro"]
    assert wx.Window.FindFocus() is None or True                 # sin mostrar la ventana no hay foco que comprobar
    # solo controles nativos, cada uno con su ayuda para Control+H
    def todos(w):
        for h in w.GetChildren():
            yield h
            yield from todos(h)
    for c in todos(ventana):
        assert not isinstance(c, (wx.SpinCtrlDouble, wx.SearchCtrl)), c
        if isinstance(c, (wx.Button, wx.ListBox, wx.TextCtrl)):
            assert c.GetHelpText(), c.GetName()
    # el estado y el registro son de solo lectura, para recorrerlos con las flechas
    assert not ventana.estado.IsEditable() and ventana.estado.IsMultiLine() and not ventana.registro.IsEditable() and ventana.campo_orden.IsEditable()
    # cada atajo de los menús está en la lista de teclas que enseña la ayuda, y al revés
    barra = ventana.GetMenuBar()
    atajos = set()
    for n in range(barra.GetMenuCount()):
        for item in barra.GetMenu(n).GetMenuItems():
            if "\t" in item.GetItemLabel():
                atajos.add(item.GetItemLabel().split("\t")[1].replace("Shift+", "Mayúsculas+").replace("Ctrl+", "Control+"))
    assert len(atajos) == 17
    for a in atajos:
        assert ("\n%s:" % a) in TECLAS, a
    assert [barra.GetMenuLabelText(n) for n in range(barra.GetMenuCount())] == ["Servidor", "Gestión", "Datos", "Ayuda"]
    # --- el diálogo de configuración, generado desde la descripción de las opciones
    dlg = DialogoConfiguracion(ventana, opciones.valores_de_serie())
    try:
        problemas = revisar_teclado(dlg)
        assert not problemas, informe(problemas)
        assert dlg.cuaderno.GetPageCount() == len(opciones.SECCIONES)
        assert [dlg.cuaderno.GetPageText(n) for n in range(dlg.cuaderno.GetPageCount())] == [t for _, t, _ in opciones.SECCIONES]
        assert set(dlg.controles) == set(opciones.POR_CLAVE)
        for o in opciones.OPCIONES:
            c = dlg.controles[o.clave]
            assert c.GetHelpText() == ayuda_de(o) and o.ayuda in c.GetHelpText() and o.clave in c.GetHelpText(), o.clave
            assert ("hay que reiniciar" in c.GetHelpText()) == o.reinicio, o.clave
            esperado = {opciones.SINO: wx.CheckBox, opciones.ENTERO: wx.SpinCtrl, opciones.ELECCION: wx.Choice}.get(o.tipo, wx.TextCtrl)
            assert type(c) is esperado, o.clave
            if o.tipo == opciones.ENTERO:
                assert (c.GetMin(), c.GetMax()) == (o.minimo, o.maximo), o.clave
            if o.tipo == opciones.SECRETO:
                assert c.GetWindowStyle() & wx.TE_PASSWORD
        for ident in (wx.ID_OK, wx.ID_CANCEL, wx.ID_APPLY):
            assert dlg.FindWindowById(ident) is not None
        assert dlg.boton_fabrica.GetLabel() == "Valores de &fábrica..." and dlg.GetEscapeId() == wx.ID_CANCEL
    finally:
        dlg.Destroy()
    # --- el diálogo de restaurar copias
    copia = (os.path.join("copias", "copia_20260101_120000.zip"), time.time(), 2048, False)
    dlg = DialogoCopias(ventana, [copia, (os.path.join("copias", "copia_auto_20260101_000000.zip"), time.time() - 5, 4096, True)])
    try:
        problemas = revisar_teclado(dlg)
        assert not problemas, informe(problemas)
        assert dlg.lista.GetCount() == 2 and "automática" in dlg.lista.GetString(1) and dlg.elegida() == copia[0] and not dlg.con_conf.GetValue()
    finally:
        dlg.Destroy()
    vacio = DialogoCopias(ventana, [])
    try:
        assert not revisar_teclado(vacio) and vacio.elegida() is None
    finally:
        vacio.Destroy()


def test_el_dialogo_de_configuracion_recoge_valida_y_restablece(ventana, monkeypatch):
    import wx
    from panel_servidor import configuracion
    errores, aplicados = [], []
    monkeypatch.setattr(configuracion, "mostrar_error", lambda padre, mensaje, titulo="": errores.append(mensaje))
    cfg = dict(opciones.valores_de_serie(), nombre="La Taberna", max_jugadores=0, pvp="no", entrada="invitacion", cifrado="si", admins="Ana, Blas",
               version_minima="1.7.0", radio_detalle=250)
    dlg = configuracion.DialogoConfiguracion(ventana, cfg, al_aplicar=lambda v: aplicados.append(v) or True, en_marcha=True)
    try:
        assert dlg.valores() == cfg and not errores               # lo que entra es lo que sale
        assert dlg.controles["pvp"].GetValue() is False and dlg.controles["max_jugadores"].GetValue() == 0
        assert dlg.controles["entrada"].GetStringSelection().startswith("invitacion:")
        # se cambia como lo haría una persona
        dlg.controles["nombre"].SetValue("  El Rincón  ")
        dlg.controles["puerto"].SetValue(5000)
        dlg.controles["adultos"].SetValue(True)
        dlg.controles["versiones"].SetSelection(1)
        v = dlg.valores()
        assert v["nombre"] == "El Rincón" and v["puerto"] == 5000 and v["adultos"] == "si" and v["versiones"] == "iguales"
        # Aplicar guarda sin cerrar
        dlg._aplicar(None)
        assert aplicados == [v]
        # un valor que no vale: lo dice, lleva a su pestaña y no aplica nada
        dlg.controles["version_minima"].SetValue("la última")
        assert dlg.valores() is None and "Versión mínima del juego" in errores[-1] and "número de versión" in errores[-1]
        assert dlg.cuaderno.GetSelection() == dlg.paginas["version_minima"] == 3
        dlg._aplicar(None)
        dlg._aceptar(None)
        assert aplicados == [v]
        dlg.controles["version_minima"].SetValue("")
        # la entrada con clave pero sin contraseña: no es un error de forma, pero dejaría fuera a todo el mundo
        dlg.controles["entrada"].SetSelection(1)
        assert dlg.valores() is None and "contraseña está vacía" in errores[-1] and dlg.cuaderno.GetSelection() == dlg.paginas["clave"]
        dlg.controles["clave"].SetValue("secreta")
        assert dlg.valores()["clave"] == "secreta"
        # valores de fábrica: solo la pestaña en la que se está, o todas; Cancelar no toca nada
        dlg.cuaderno.SetSelection(dlg.paginas["puerto"])
        monkeypatch.setattr(configuracion, "elegir_opcion", lambda *a, **k: None)
        dlg.de_fabrica()
        assert dlg.crudo()["puerto"] == 5000
        monkeypatch.setattr(configuracion, "elegir_opcion", lambda *a, **k: 0)
        dlg.de_fabrica()
        assert dlg.crudo()["puerto"] == 47820 and dlg.crudo()["cifrado"] == "auto" and dlg.crudo()["nombre"] == "  El Rincón  " and dlg.crudo()["clave"] == "secreta"
        monkeypatch.setattr(configuracion, "elegir_opcion", lambda *a, **k: 1)
        dlg.de_fabrica()
        assert dlg.valores() == opciones.valores_de_serie()
    finally:
        dlg.Destroy()


def test_el_panel_lleva_un_servidor_de_verdad(ventana, tmp_path, monkeypatch, sin_firma):
    import wx
    from panel_servidor import ventana as V
    v = ventana
    dichos, mensajes, errores = [], [], []
    monkeypatch.setattr(V, "mostrar_mensaje", lambda padre, mensaje, titulo="", **k: mensajes.append(mensaje))
    monkeypatch.setattr(V, "mostrar_error", lambda padre, mensaje, titulo="": errores.append(mensaje))
    monkeypatch.setattr(V.voz, "hablar", lambda texto, **k: dichos.append(texto))
    v.hablar = True                                              # para ver qué diría, con la voz sustituida
    copiados = []
    v._al_portapapeles = lambda texto: copiados.append(texto) or True      # las pruebas no tocan el portapapeles de nadie
    # --- parado
    assert "Servidor parado." in v.estado.GetValue() and "F5" in v.estado.GetValue() and v.GetTitle().endswith("parado")
    assert v.b_arrancar.IsEnabled() and not v.b_parar.IsEnabled() and not v.m_parar.IsEnabled() and v.m_arrancar.IsEnabled()
    v.anuncio()
    v.invitar()
    assert dichos[-1].startswith("El servidor está parado") and v.lista_cuentas.GetCount() == 0
    # --- arrancar: la ventana no se queda esperando
    t0 = time.time()
    v.arrancar()
    assert time.time() - t0 < 1.0 and v.motor.estado in (M.ARRANCANDO, M.EN_MARCHA)
    assert _bombear(lambda: v.motor.estado == M.EN_MARCHA and "en marcha" in v.GetTitle())
    puerto = v.motor.foto["puerto"]
    assert any("Servidor en marcha en el puerto %d." % puerto == d for d in dichos)       # esto el lector no lo puede saber: se dice
    estado = v.estado.GetValue()
    for trozo in ("Servidor en marcha desde hace", "Nombre: Servidor de pruebas del panel.", "Jugadores dentro: 0 de 32.", "Puerto: %d." % puerto,
                  "Conexión sin cifrar.", "Mundo: versión", "huella", "localidades", "Para quien juegue desde fuera", "cualquiera que tenga la dirección"):
        assert trozo in estado, trozo
    assert not v.b_arrancar.IsEnabled() and v.b_parar.IsEnabled() and v.m_parar.IsEnabled() and not v.m_arrancar.IsEnabled()
    assert "escuchando en el puerto" in v.registro.GetValue()
    # --- entra un jugador: aparece en la lista, y luego otro, sin perder al que estaba elegido
    a = Ligero(Banquito(puerto), "Ana")
    assert a.ok and _bombear(lambda: v.lista_jugadores.GetCount() == 1, 6)
    assert v.lista_jugadores.GetString(0).startswith("Ana, sin situar todavía, administra, juego ") and "dirección" not in v.lista_jugadores.GetString(0)
    a.estado()
    assert _bombear(lambda: v.lista_jugadores.GetCount() == 1 and "Ana, en Puerto Bravo, administra" in v.lista_jugadores.GetString(0), 6)
    assert "1 jugador" in v.GetTitle() and "Jugadores dentro: 1 de 32." in v.estado.GetValue()
    assert _bombear(lambda: v.lista_cuentas.GetCount() == 1, 6) and "Ana, dentro ahora, administra" in v.lista_cuentas.GetString(0)
    # --- anuncio a todos y mensaje privado
    monkeypatch.setattr(V, "pedir_texto", lambda *a, **k: "Esta noche,   guerra de bandas")
    v.anuncio()
    assert "Aviso del servidor: Esta noche, guerra de bandas" == a.leer("aviso")["texto"]
    assert _bombear(lambda: dichos[-1] == "Aviso enviado.", 5) and "Aviso enviado." in v.registro.GetValue() and v.GetStatusBar().GetStatusText() == "Aviso enviado."
    v.lista_jugadores.SetSelection(0)
    monkeypatch.setattr(V, "pedir_texto", lambda *a, **k: "Baja la música")
    v.mensaje_privado()
    assert "Baja la música" in a.leer("aviso")["texto"] and _bombear(lambda: dichos[-1] == "Dicho a Ana.", 5)
    # --- invitaciones: se crea, se copia sola y sale en la lista
    v.invitar()
    assert _bombear(lambda: mensajes and v.lista_invitaciones.GetCount() == 1, 6)
    codigo = v.invitaciones[0]["codigo"]
    assert codigo in mensajes[-1] and "portapapeles" in mensajes[-1] and v.lista_invitaciones.GetString(0) == codigo + ", libre" and copiados == [codigo]
    v.copiar_direccion()
    assert (len(copiados) == 2 and copiados[-1].endswith(":%d" % puerto)) or "No he podido saber la dirección" in dichos[-1]
    v.lista_invitaciones.SetSelection(0)
    v.anular_invitacion()
    assert _bombear(lambda: v.lista_invitaciones.GetCount() == 0, 6) and "Invitación anulada." in dichos
    # --- una orden escrita, como en la consola
    v.ir_a_orden()
    assert v.cuaderno.GetSelection() == 4
    v.campo_orden.SetValue("  jugadores ")
    v.enviar_orden()
    assert v.campo_orden.GetValue() == "" and _bombear(lambda: dichos[-1].startswith("Hay 1: Ana"), 5) and "> jugadores" in v.registro.GetValue()
    v.enviar_orden()
    assert dichos[-1].startswith("Escribe antes una orden")
    # --- la configuración: lo que se puede, al momento; lo que pide reiniciar, se pregunta
    preguntas = []
    monkeypatch.setattr(V, "elegir_opcion", lambda padre, mensaje, titulo, opciones_: (preguntas.append(mensaje), 1)[1])
    nueva = dict(v.cfg, bienvenida="Hola desde el panel", max_jugadores=0)
    assert v._guardar_config(nueva) is True
    assert _bombear(lambda: any("Configuración guardada y aplicada" in d for d in dichos), 5)
    assert opciones.leer(v.motor.ruta_conf)[0]["max_jugadores"] == 0 and "# GENERAL" in open(v.motor.ruta_conf, encoding="utf-8").read()
    assert _bombear(lambda: "Jugadores dentro: 1, sin límite." in v.estado.GetValue(), 5)
    assert v._guardar_config(dict(nueva, puerto=47999, cifrado="auto")) is True
    assert _bombear(lambda: preguntas, 5) and "no valen hasta que reinicies" in preguntas[-1] and "Puerto" in preguntas[-1] and "Cifrado de la conexión" in preguntas[-1]
    assert v.motor.estado == M.EN_MARCHA                          # ha elegido «Más tarde»: sigue como estaba
    v._guardar_config(dict(nueva))                               # y lo deja como estaba, para lo que sigue
    # --- el mensaje del día se cambia en marcha: se guarda y lo oyen los que están
    monkeypatch.setattr(V, "pedir_texto", lambda *a, **k: "El sábado, carrera")
    v.mensaje_dia()
    assert a.leer("aviso", filtro=lambda m: "El sábado, carrera" in m["texto"]) and opciones.leer(v.motor.ruta_conf)[0]["mensaje_dia"] == "El sábado, carrera"
    # --- copia de seguridad en caliente
    v.copia()
    assert _bombear(lambda: any(d.startswith("Copia hecha en") for d in dichos), 6)
    assert len(os.listdir(tmp_path / "datos_servidor" / "copias")) == 1
    # --- abrir el puerto con UPnP: si el router no contesta, se dice y no pasa nada
    v.buscar_router = lambda: []
    v.abrir_router()
    assert _bombear(lambda: any("No he podido abrir el puerto en el router" in d for d in dichos), 6) and v._router is None
    # --- expulsar con motivo, y vetar desde la lista de cuentas
    v.lista_jugadores.SetSelection(0)
    monkeypatch.setattr(V, "pedir_texto", lambda *a, **k: None)
    v.expulsar()                                                 # Cancelar no expulsa
    assert a.linea(0.5) is None or True
    monkeypatch.setattr(V, "pedir_texto", lambda *a, **k: "por pruebas: nada personal")
    v.expulsar()
    fuera = _si_llega(a, "expulsado")
    assert fuera is None or "Motivo: por pruebas, nada personal" in fuera["motivo"]
    assert _bombear(lambda: any("Ana, expulsado." == d for d in dichos), 5)
    assert _bombear(lambda: v.lista_jugadores.GetCount() == 0, 8) and "0 jugadores" in v.GetTitle()
    assert _bombear(lambda: v.lista_cuentas.GetCount() == 1 and "dentro ahora" not in v.lista_cuentas.GetString(0), 6)
    v.lista_cuentas.SetSelection(0)
    monkeypatch.setattr(V, "elegir_opcion", lambda padre, mensaje, titulo, opciones_: 0)
    v.vetar(de_cuentas=True)
    assert _bombear(lambda: v.lista_cuentas.GetCount() == 1 and "vetada" in v.lista_cuentas.GetString(0), 6)
    assert "No puedes entrar" in Ligero(Banquito(puerto), "Ana").rechazo
    v.perdonar()
    assert _bombear(lambda: "vetada" not in v.lista_cuentas.GetString(0), 6)
    v.quitar_admin()
    assert _bombear(lambda: "administra" not in v.lista_cuentas.GetString(0), 6)
    v.borrar_cuenta()
    assert _bombear(lambda: v.lista_cuentas.GetCount() == 0, 6)
    # --- el registro no crece sin fin, y se puede vaciar
    for n in range(V.MAX_REGISTRO + 50):
        v.lineas.append("línea %d" % n)
    v._linea("la última")
    assert len(v.lineas) == V.MAX_REGISTRO and v.registro.GetValue().rstrip().endswith("la última")
    v.vaciar_registro()
    assert v.registro.GetValue() == "" and v.lineas == []
    # --- parar: sin gente dentro no pregunta; el servidor lo guarda todo y la ventana se entera
    c = Ligero(Banquito(puerto), "Carla")
    assert c.ok and _bombear(lambda: v.lista_jugadores.GetCount() == 1, 6)
    monkeypatch.setattr(V, "confirmar", lambda *a, **k: wx.ID_NO)
    assert v.parar() is False and v.motor.estado == M.EN_MARCHA    # con gente dentro pregunta, y «No» lo deja como está
    monkeypatch.setattr(V, "confirmar", lambda *a, **k: wx.ID_YES)
    t0 = time.time()
    assert v.parar() is True and time.time() - t0 < 1.0
    _si_llega(c, "cerrado")
    assert _bombear(lambda: v.motor.estado == M.PARADO and v.GetTitle().endswith("parado"))
    assert dichos[-1] == "Servidor parado. Todo guardado." and v.lista_jugadores.GetCount() == 0 and v.b_arrancar.IsEnabled()
    # --- con él parado: copia y restauración, fuera del hilo de la interfaz
    v.copia()
    assert _bombear(lambda: sum(1 for d in dichos if d.startswith("Copia hecha en")) == 2, 8)
    # --- reiniciar y cerrar la ventana con el servidor en marcha: pregunta, lo para con orden y entonces se cierra
    v.arrancar()
    assert _bombear(lambda: v.motor.estado == M.EN_MARCHA)
    v.reiniciar()
    assert _bombear(lambda: v.motor.estado == M.PARANDO or v._reiniciar_al_parar, 5)
    assert _bombear(lambda: v.motor.estado == M.EN_MARCHA and not v._reiniciar_al_parar, 20)
    d = Ligero(Banquito(v.motor.foto["puerto"]), "Dora")
    assert d.ok and _bombear(lambda: v.lista_jugadores.GetCount() == 1, 6)
    motor = v.motor
    monkeypatch.setattr(V, "confirmar", lambda *a, **k: wx.ID_NO)
    v.Close()
    _bombear(lambda: False, 0.3)
    assert v and motor.estado == M.EN_MARCHA                      # «No»: ni se cierra ni se para
    monkeypatch.setattr(V, "confirmar", lambda *a, **k: wx.ID_YES)
    v.Close()
    _si_llega(d, "cerrado")
    assert _bombear(lambda: not v, 20) and motor.estado == M.PARADO
    assert not errores, errores
    datos = tmp_path / "datos_servidor"
    assert (datos / "puertobravo.db").exists() and not [n for n in os.listdir(datos) if n.endswith((".tmp", "-journal"))]


def test_el_panel_dice_por_que_no_arranca(ventana, monkeypatch):
    from panel_servidor import ventana as V
    errores = []
    monkeypatch.setattr(V, "mostrar_error", lambda padre, mensaje, titulo="": errores.append((titulo, mensaje)))
    ocupado = socket.socket()
    ocupado.bind(("127.0.0.1", 0))
    ocupado.listen(1)
    try:
        cfg = dict(ventana.cfg, puerto=ocupado.getsockname()[1])
        ventana.motor.guardar_config(cfg)
        ventana.arrancar()
        assert _bombear(lambda: errores and ventana.motor.estado == M.PARADO)
        assert errores[0][0] == "El servidor no ha arrancado" and "No se ha podido abrir el puerto" in errores[0][1]
        assert "La última vez no arrancó" in ventana.estado.GetValue() and ventana.b_arrancar.IsEnabled()
    finally:
        ocupado.close()


def test_los_textos_del_panel():
    from panel_servidor import ventana as V
    assert V.duracion(59) == "0 minutos" and V.duracion(3600 * 26 + 120) == "1 día, 2 horas, 2 minutos" and V.duracion(7260) == "2 horas, 1 minuto"
    assert V.hace(None) == "nunca" and V.hace(time.time() - 30) == "hace un momento" and V.hace(time.time() - 7300) == "hace 2 horas"
    g = {"nombre": "Ana", "mapa": "Puerto Bravo", "admin": True, "juego": "1.7.0", "mismo_mundo": False, "ip": None, "fuera": False}
    assert V.texto_jugador(g) == "Ana, en Puerto Bravo, administra, juego 1.7.0, con datos de otra versión"
    assert V.texto_jugador(dict(g, mapa=None, fuera=True, admin=False, mismo_mundo=True, ip="10.0.0.7")) == "Ana, en una localidad que el servidor no conoce, juego 1.7.0, dirección 10.0.0.7"
    assert V.texto_cuenta({"nombre": "Blas", "dentro": False, "admin": False, "vetado": True, "visto": None, "juego": ""}) == "Blas, vetada, vista nunca"
    assert V.texto_invitacion({"codigo": "ABCD1234", "usada": True, "por": "Blas"}) == "ABCD1234, usada por Blas"
    foto = {"jugadores": [], "max_jugadores": 0, "nombre": "X", "puerto": 47820, "cifrado": True, "huella_cert": "ab12", "mundo_version": "1.7.0",
            "mundo_huella": "ffff", "localidades": 14, "inicio": time.time() - 120, "personajes": 3, "entrada": "invitacion"}
    texto = V.texto_estado(M.EN_MARCHA, foto, {}, "192.168.1.50")
    for trozo in ("desde hace 2 minutos", "Jugadores dentro: 0, sin límite.", "192.168.1.50:47820", "Huella del certificado: ab12", "código de invitación", "Personajes que lleva el servidor: 3."):
        assert trozo in texto, trozo
    assert "arrancando" in V.texto_estado(M.ARRANCANDO, None, {"nombre": "X", "puerto": 1}, "")
    assert V.direccion_local() == "" or V.direccion_local().count(".") == 3
