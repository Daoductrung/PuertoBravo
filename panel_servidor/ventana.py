"""La ventana del panel del servidor.

Todo lo que hace la consola, y más cómodo: arrancar y parar, ver el estado, la lista de jugadores con sus acciones,
las cuentas, las invitaciones, el registro, la configuración, las copias de seguridad y la guía.

Reglas de esta ventana:
- El servidor va en su propio hilo (``motor``). La ventana nunca espera por él: le pide las cosas y recibe la respuesta
  con ``wx.CallAfter``.
- Las listas y el estado se refrescan solos, pero sin molestar: solo se tocan cuando cambian, se conserva lo elegido y
  no se reescribe el texto que el lector de pantalla está leyendo.
- La voz directa se usa solo para lo que el lector no puede saber: que el servidor ha terminado de arrancar o de
  parar y el resultado de una orden que se da con un botón.
"""
from juego.i18n import tr
import os
import socket
import threading
import time

import wx

from editor.accesibilidad import voz
from editor.accesibilidad.ayuda import habilitar_ayuda_contextual
from editor.accesibilidad.dialogos import (confirmar, crear_botonera, elegir_opcion, mostrar_error, mostrar_mensaje, pedir_texto,
                                           preparar_dialogo)
from editor.accesibilidad.nombres import crear_campo
from editor.accesibilidad.teclado import vincular_menu_contextual
from servidor import copias, enmarcha, opciones
from servidor.idioma import es           # lo que oyen los jugadores va en español: lo traduce el juego de cada uno

from . import CONF, NOMBRE, abierto_sin_activar, carpeta_servidor, ruta_documentacion
from .configuracion import DialogoConfiguracion
from .motor import ARRANCANDO, EN_MARCHA, PARADO, PARANDO, Motor

MAX_REGISTRO = 4000                      # líneas que conserva la ventana; el archivo, si se pide, las guarda todas


def direccion_local():
    """La dirección de este ordenador en la red de casa. No se manda nada a ningún sitio: solo se pregunta al sistema
    por qué conexión saldría."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("192.0.2.1", 9))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return ""


def hace(momento):
    """«hace 3 minutos», para la última vez que se vio una cuenta."""
    if not momento:
        return "nunca"
    s = max(0, int(time.time() - float(momento)))
    for cuanto, uno, varios in ((86400, tr("día"), tr("días")), (3600, tr("hora"), tr("horas")), (60, tr("minuto"), tr("minutos"))):
        if s >= cuanto:
            n = s // cuanto
            return "hace %d %s" % (n, uno if n == 1 else varios)
    return tr("hace un momento")


def duracion(segundos):
    s = int(max(0, segundos))
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    partes = (["%d %s" % (d, "día" if d == 1 else "días")] if d else []) + (["%d %s" % (h, "hora" if h == 1 else "horas")] if h else [])
    return ", ".join(partes + ["%d %s" % (m, "minuto" if m == 1 else "minutos")])


def texto_jugador(g):
    partes = [g["nombre"], (tr("en ") + g["mapa"]) if g.get("mapa") else (tr("en una localidad que el servidor no conoce") if g.get("fuera") else tr("sin situar todavía"))]
    if g.get("admin"):
        partes.append("administra")
    if g.get("juego"):
        partes.append(tr("juego ") + g["juego"] + ("" if g.get("mismo_mundo", True) else tr(", con datos de otra versión")))
    if g.get("ip"):
        partes.append(tr("dirección ") + g["ip"])
    return ", ".join(partes)


def texto_cuenta(c):
    partes = [c["nombre"]]
    if c.get("dentro"):
        partes.append(tr("dentro ahora"))
    if c.get("admin"):
        partes.append("administra")
    if c.get("vetado"):
        partes.append("vetada")
    partes.append(tr("vista ") + hace(c.get("visto")))
    if c.get("juego"):
        partes.append(tr("juego ") + c["juego"])
    return ", ".join(partes)


def texto_invitacion(i):
    return "%s, %s" % (i["codigo"], (tr("usada por ") + (i["por"] or tr("una cuenta que ya no existe"))) if i["usada"] else "libre")


def texto_estado(estado, foto, cfg, local, ultimo_error=""):
    """El texto de la pestaña Estado: una cosa por línea, para recorrerlo con las flechas."""
    puerto = (foto or {}).get("puerto") or cfg.get("puerto")
    lineas = []
    if estado == EN_MARCHA and foto:
        gente, tope = foto["jugadores"], foto["max_jugadores"]
        lineas += [tr("Servidor en marcha desde hace %s.") % duracion(time.time() - (foto.get("inicio") or time.time())),
                   tr("Nombre: %s.") % foto["nombre"],
                   "Jugadores dentro: %d%s." % (len(gente), (" de %d" % tope) if tope > 0 else tr(", sin límite")),
                   tr("Personajes que lleva el servidor: %d.") % foto.get("personajes", 0),
                   tr("Puerto: %s.") % puerto,
                   (tr("Dirección para quien juegue en tu misma casa: %s:%s.") % (local, puerto)) if local else tr("No he podido saber la dirección de este ordenador en tu red."),
                   tr("Para quien juegue desde fuera: tu dirección pública o tu nombre de DNS dinámico, dos puntos y el puerto %s. "
                   "Hay que abrir ese puerto en el router; la guía lo explica paso a paso, con F1.") % puerto,
                   (tr("Conexión cifrada. Huella del certificado: %s.") % foto["huella_cert"]) if foto.get("cifrado") else tr("Conexión sin cifrar."),
                   tr("Mundo: versión %s del juego, huella %s, %d localidades.") % (foto.get("mundo_version"), foto.get("mundo_huella"), foto.get("localidades", 0)),
                   tr("Quién puede crear un personaje: %s.") % {"abierta": tr("cualquiera que tenga la dirección"), "clave": tr("quien sepa la contraseña de entrada"),
                                                             "invitacion": tr("quien tenga un código de invitación")}.get(foto.get("entrada"), foto.get("entrada"))]
    else:
        lineas += [{PARADO: tr("Servidor parado."), ARRANCANDO: tr("El servidor está arrancando. La primera vez tarda unos segundos, porque crea su certificado."),
                    PARANDO: tr("El servidor está parando y guardándolo todo.")}.get(estado, tr("Servidor parado.")),
                   tr("Nombre: %s.") % cfg.get("nombre", ""),
                   tr("Puerto: %s.") % puerto]
        if estado == PARADO:
            lineas.append(tr("Para arrancarlo pulsa F5 o el botón Arrancar."))
        if ultimo_error and estado == PARADO:
            lineas.append(tr("La última vez no arrancó: ") + ultimo_error)
    lineas.append(tr("Carpeta del servidor: %s.") % carpeta_servidor())
    return "\n".join(lineas)


class DialogoCopias(wx.Dialog):
    """Elige qué copia de seguridad restaurar."""

    def __init__(self, padre, lista):
        super().__init__(padre, title=tr("Restaurar una copia de seguridad"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, name=tr("Restaurar una copia de seguridad"))
        self.lista_copias = list(lista)
        self.otra = None
        sizer = wx.BoxSizer(wx.VERTICAL)
        textos = ["%s, del %s, %d KB%s" % (os.path.basename(r), time.strftime("%d/%m/%Y a las %H:%M", time.localtime(m)), max(1, t // 1024), tr(", automática") if auto else "")
                  for r, m, t, auto in self.lista_copias]
        _, self.lista = crear_campo(self, tr("Copias de &seguridad, la más nueva primero:"), wx.ListBox, choices=textos, style=wx.LB_SINGLE, size=(560, 220),
                                    ayuda=tr("Elige la copia que quieres restaurar. Antes de restaurar se guarda lo que hay ahora en otra copia, por si acaso."), sizer=sizer)
        if textos:
            self.lista.SetSelection(0)
        self.con_conf = wx.CheckBox(self, label=tr("Restaurar &también la configuración que va en la copia"), name=tr("Restaurar también la configuración"))
        self.con_conf.SetHelpText(tr("Si lo marcas, servidor.conf se cambia por el que se guardó en la copia. Si no, se queda la configuración de ahora."))
        sizer.Add(self.con_conf, 0, wx.ALL, 6)
        self.boton_otra = wx.Button(self, label=tr("Elegir &otro archivo..."))
        self.boton_otra.SetHelpText(tr("Para restaurar una copia que tienes guardada en otra carpeta o en otro disco."))
        self.boton_otra.Bind(wx.EVT_BUTTON, self._otra)
        sizer.Add(self.boton_otra, 0, wx.ALL, 6)
        sizer.Add(crear_botonera(self, wx.OK | wx.CANCEL, predeterminado=wx.ID_CANCEL), 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizerAndFit(sizer)
        preparar_dialogo(self, foco_inicial=self.lista)
        self.CentreOnParent()

    def _otra(self, evento):
        with wx.FileDialog(self, tr("Elegir una copia de seguridad"), wildcard=tr("Copias de seguridad (*.zip)|*.zip"), style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.otra = dlg.GetPath()
                self.EndModal(wx.ID_OK)

    def elegida(self):
        if self.otra:
            return self.otra
        i = self.lista.GetSelection()
        return self.lista_copias[i][0] if i >= 0 else None


class VentanaPanel(wx.Frame):
    def __init__(self, ruta_conf=None, hablar=True, sin_foco=False):
        super().__init__(None, title=NOMBRE, size=(860, 640), name=NOMBRE)
        self.hablar = hablar
        self._foco_pendiente = bool(sin_foco)    # abierta sin activar: el foco inicial se pone cuando su dueño venga a ella
        self.motor = Motor(ruta_conf or os.path.join(carpeta_servidor(), CONF), registrar=lambda t: wx.CallAfter(self._linea, t),
                           avisar=lambda que, dato: wx.CallAfter(self._aviso_motor, que, dato))
        self.cfg, avisos = self.motor.leer_config()
        self.local = direccion_local()
        self.jugadores, self.cuentas, self.invitaciones = [], [], []
        self.lineas = []
        self._cerrar_al_parar = False
        self._reiniciar_al_parar = False
        self._tras_parar = None
        self._ocupada = False
        self._arrancar_al_abrir = False          # se ha abierto con --arrancar: tras una actualización, el servidor vuelve solo
        self._router = None                      # el puerto abierto en el router con UPnP, para cerrarlo al parar
        self.buscar_router = None                # las pruebas ponen aquí un router de mentira
        self._menus()
        self._contenido()
        self.CreateStatusBar()
        habilitar_ayuda_contextual(self)
        self.Bind(wx.EVT_CLOSE, self._al_cerrar)
        self.reloj = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda e: self.refrescar(), self.reloj)
        self.reloj.Start(1000)
        for a in avisos:
            self._linea(tr("Configuración: ") + a)
        if not os.path.exists(self.motor.ruta_conf):
            self._linea(tr("Todavía no hay archivo de configuración: se usan los valores de serie. Se crea al guardar la configuración."))
        self.refrescar(todo=True)
        self.Centre()
        if self._foco_pendiente:
            # La ha abierto la actualización del juego, minimizada y sin activar: no se toca el foco, que es del juego. Se
            # pondrá en el estado, como siempre, la primera vez que se venga a esta ventana.
            self.Bind(wx.EVT_ACTIVATE, self._al_activar)
            self.Bind(wx.EVT_ICONIZE, self._al_activar)
        else:
            self.estado.SetFocus()
        self.motor.anotar()

    def _al_activar(self, evento):
        evento.Skip()
        if self._foco_pendiente:
            wx.CallAfter(self._foco_inicial)

    def _foco_inicial(self):
        """El foco con el que abre siempre el panel, puesto la primera vez que la ventana está activa y a la vista."""
        if self and self._foco_pendiente and self.IsActive() and not self.IsIconized():
            self._foco_pendiente = False
            self.estado.SetFocus()

    # ------------------------------------------------------------------- menús
    def _menus(self):
        barra = wx.MenuBar()
        m = wx.Menu()
        self.m_arrancar = self._item(m, tr("&Arrancar\tF5"), tr("Pone el servidor en marcha."), self.arrancar)
        self.m_parar = self._item(m, tr("&Parar\tShift+F5"), tr("Avisa a los jugadores, lo guarda todo y para el servidor."), self.parar)
        self.m_reiniciar = self._item(m, tr("&Reiniciar\tCtrl+F5"), tr("Para el servidor y lo vuelve a arrancar: así valen los cambios que piden reinicio."), self.reiniciar)
        m.AppendSeparator()
        self._item(m, tr("&Configuración...\tCtrl+P"), tr("Todas las opciones del servidor, por pestañas."), self.configurar)
        m.AppendSeparator()
        self._item(m, tr("&Salir\tCtrl+Q"), tr("Cierra el panel. Si el servidor está en marcha, lo para antes."), lambda: self.Close())
        barra.Append(m, tr("&Servidor"))
        m = wx.Menu()
        self.m_anuncio = self._item(m, tr("&Anuncio a todos...\tCtrl+N"), tr("Dice algo a todos los jugadores que están dentro."), self.anuncio)
        self.m_privado = self._item(m, tr("&Mensaje al jugador elegido...\tCtrl+M"), tr("Dice algo solo al jugador elegido en la lista de jugadores."), self.mensaje_privado)
        self.m_expulsar = self._item(m, tr("&Expulsar al jugador elegido...\tCtrl+E"), tr("Saca del servidor al jugador elegido. Puede volver a entrar."), self.expulsar)
        self.m_invitar = self._item(m, tr("Crear una &invitación\tCtrl+I"), tr("Crea un código de invitación de un solo uso y lo copia al portapapeles."), self.invitar)
        self.m_mensaje = self._item(m, tr("Mensaje del &día...\tCtrl+D"), tr("Cambia el aviso que oye cada jugador al entrar."), self.mensaje_dia)
        self.m_router = self._item(m, tr("Abrir el puerto en el &router con UPnP"), tr("Pide al router de tu casa que abra el puerto del servidor, para que entren desde fuera. "
                                   "Se cierra al parar el servidor. No todos los routers lo permiten."), self.abrir_router)
        self.m_orden = self._item(m, tr("Escribir una &orden...\tCtrl+O"), tr("Lleva el foco al campo de órdenes, en la pestaña Registro."), self.ir_a_orden)
        m.AppendSeparator()
        self._item(m, tr("Ac&tualizar las listas\tF6"), tr("Vuelve a leer el estado, los jugadores, las cuentas y las invitaciones."), lambda: self.refrescar(todo=True, forzar=True))
        barra.Append(m, tr("&Gestión"))
        m = wx.Menu()
        self.m_guardar = self._item(m, tr("&Guardar ahora\tCtrl+S"), tr("Guarda en disco todo lo del servidor."), self.guardar_ahora)
        self._item(m, tr("&Copia de seguridad ahora\tCtrl+B"), tr("Hace una copia de seguridad de los datos en la carpeta copias."), self.copia)
        self._item(m, tr("&Restaurar una copia...\tCtrl+R"), tr("Deja los datos como estaban en una copia de seguridad. Hay que parar el servidor."), self.restaurar)
        m.AppendSeparator()
        self._item(m, tr("Abrir la carpeta de &datos"), tr("Abre en el Explorador la carpeta donde se guarda todo."), self.abrir_datos)
        self._item(m, tr("Abrir la carpeta de las c&opias"), tr("Abre en el Explorador la carpeta de las copias de seguridad."), self.abrir_copias)
        self._item(m, tr("Guardar el registro en un arc&hivo...\tCtrl+G"), tr("Guarda en un archivo de texto lo que hay en el registro."), self.guardar_registro)
        barra.Append(m, tr("&Datos"))
        m = wx.Menu()
        self._item(m, tr("&Guía del servidor\tF1"), tr("Abre en el navegador la guía completa para montar y llevar un servidor."), self.guia)
        self._item(m, tr("&Teclas del panel"), tr("Dice los atajos de teclado de esta ventana."), self.teclas)
        self._item(m, tr("&Acerca de..."), tr("Qué es este programa."), self.acerca)
        barra.Append(m, tr("A&yuda"))
        self.SetMenuBar(barra)

    def _item(self, menu, texto, ayuda, accion):
        item = menu.Append(wx.ID_ANY, texto, ayuda)
        self.Bind(wx.EVT_MENU, lambda e: accion(), item)
        return item

    # --------------------------------------------------------------- contenido
    def _boton(self, padre, fila, etiqueta, ayuda, accion):
        b = wx.Button(padre, label=etiqueta)
        b.SetHelpText(ayuda)
        b.Bind(wx.EVT_BUTTON, lambda e: accion())
        fila.Add(b, 0, wx.ALL, 4)
        return b

    def _pagina(self, titulo):
        pagina = wx.Panel(self.cuaderno, name=titulo)
        columna = wx.BoxSizer(wx.VERTICAL)
        pagina.SetSizer(columna)
        self.cuaderno.AddPage(pagina, titulo)
        return pagina, columna

    def _contenido(self):
        marco = wx.Panel(self)
        exterior = wx.BoxSizer(wx.VERTICAL)
        self.cuaderno = wx.Notebook(marco, name=tr("Apartados del panel"))
        exterior.Add(self.cuaderno, 1, wx.EXPAND | wx.ALL, 6)
        marco.SetSizer(exterior)
        # Las letras de acceso de cada pestaña no se repiten dentro de ella ni chocan con las de los menús: S, G, D e Y.
        # ---- Estado
        p, col = self._pagina(tr("Estado"))
        _, self.estado = crear_campo(p, tr("&Estado del servidor:"), wx.TextCtrl, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(780, 300),
                                     ayuda=tr("Cómo está el servidor: si está en marcha, cuánta gente hay, el puerto, la dirección para tus amigos, el cifrado y "
                                           "el mundo con el que trabaja. Una cosa por línea. Se pone al día solo cuando cambia algo; F6 lo pone al día en el momento."), sizer=col)
        col.Detach(self.estado)
        col.Add(self.estado, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.b_arrancar = self._boton(p, fila, tr("&Arrancar"), tr("Pone el servidor en marcha. También con F5."), self.arrancar)
        self.b_parar = self._boton(p, fila, tr("&Parar"), tr("Avisa a los jugadores, lo guarda todo y para el servidor. También con Mayúsculas+F5."), self.parar)
        self.b_reiniciar = self._boton(p, fila, tr("&Reiniciar"), tr("Para el servidor y lo vuelve a arrancar. También con Control+F5."), self.reiniciar)
        self.b_copiar = self._boton(p, fila, tr("&Copiar la dirección"), tr("Copia al portapapeles la dirección de este servidor en tu red, para dársela a quien juegue en tu misma casa."), self.copiar_direccion)
        self.b_config = self._boton(p, fila, tr("Con&figuración..."), tr("Abre todas las opciones del servidor. También con Control+P."), self.configurar)
        col.Add(fila, 0, wx.ALL, 2)
        # ---- Jugadores
        p, col = self._pagina(tr("Jugadores"))
        _, self.lista_jugadores = crear_campo(p, tr("&Jugadores que están dentro:"), wx.ListBox, style=wx.LB_SINGLE, size=(780, 300),
                                              ayuda=tr("Quién está dentro ahora, dónde y con qué versión del juego. La tecla Aplicaciones abre las acciones sobre el jugador elegido."), sizer=col)
        col.Detach(self.lista_jugadores)
        col.Add(self.lista_jugadores, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.b_expulsar = self._boton(p, fila, tr("&Expulsar..."), tr("Saca del servidor al jugador elegido. Puede volver a entrar. También con Control+E."), self.expulsar)
        self.b_vetar = self._boton(p, fila, tr("&Vetar..."), tr("Saca al jugador elegido y no le deja volver a entrar."), self.vetar)
        self.b_admin = self._boton(p, fila, tr("Hacer &administrador"), tr("El jugador elegido pasa a administrar el servidor: puede dar órdenes desde el chat del juego."), self.hacer_admin)
        self.b_privado = self._boton(p, fila, tr("&Mensaje..."), tr("Dice algo solo al jugador elegido. También con Control+M."), self.mensaje_privado)
        self.b_anuncio = self._boton(p, fila, tr("A&nuncio a todos..."), tr("Dice algo a todos los que están dentro. También con Control+N."), self.anuncio)
        col.Add(fila, 0, wx.ALL, 2)
        vincular_menu_contextual(self.lista_jugadores, self._menu_jugador)
        # ---- Cuentas
        p, col = self._pagina(tr("Cuentas"))
        _, self.lista_cuentas = crear_campo(p, tr("&Cuentas del servidor:"), wx.ListBox, style=wx.LB_SINGLE, size=(780, 300),
                                            ayuda=tr("Todas las cuentas que han entrado alguna vez: si administran, si están vetadas y cuándo se las vio. "
                                                  "La tecla Aplicaciones abre las acciones sobre la cuenta elegida. Con el servidor parado no se pueden ver."), sizer=col)
        col.Detach(self.lista_cuentas)
        col.Add(self.lista_cuentas, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.b_c_vetar = self._boton(p, fila, tr("&Vetar..."), tr("La cuenta elegida no podrá volver a entrar. Si está dentro, se la saca."), lambda: self.vetar(de_cuentas=True))
        self.b_c_perdonar = self._boton(p, fila, tr("&Perdonar el veto"), tr("La cuenta elegida puede volver a entrar."), self.perdonar)
        self.b_c_admin = self._boton(p, fila, tr("Hacer &administrador"), tr("La cuenta elegida pasa a administrar el servidor."), lambda: self.hacer_admin(de_cuentas=True))
        self.b_c_quitar = self._boton(p, fila, tr("&Quitar la administración"), tr("La cuenta elegida deja de administrar el servidor."), self.quitar_admin)
        self.b_c_borrar = self._boton(p, fila, tr("&Borrar la cuenta..."), tr("Borra la cuenta elegida con su personaje, sus propiedades y su sitio en la banda. No se puede deshacer."), self.borrar_cuenta)
        self.b_c_actualizar = self._boton(p, fila, tr("Ac&tualizar"), tr("Vuelve a leer la lista de cuentas. También con F6."), lambda: self.refrescar(todo=True, forzar=True))
        col.Add(fila, 0, wx.ALL, 2)
        vincular_menu_contextual(self.lista_cuentas, self._menu_cuenta)
        self.cuaderno.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._cambio_pestana)
        # ---- Invitaciones
        p, col = self._pagina(tr("Invitaciones"))
        _, self.lista_invitaciones = crear_campo(p, tr("&Invitaciones:"), wx.ListBox, style=wx.LB_SINGLE, size=(780, 300),
                                                 ayuda=tr("Los códigos de invitación, los más nuevos primero: los libres y los que ya ha usado alguien. Sirven cuando la entrada "
                                                       "del servidor es por invitación. Cada código vale para crear un solo personaje."), sizer=col)
        col.Detach(self.lista_invitaciones)
        col.Add(self.lista_invitaciones, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.b_i_crear = self._boton(p, fila, tr("&Crear una invitación"), tr("Crea un código nuevo, de un solo uso, y lo copia al portapapeles. También con Control+I."), self.invitar)
        self.b_i_copiar = self._boton(p, fila, tr("Co&piar el código"), tr("Copia al portapapeles el código elegido, para mandárselo a quien quieras invitar."), self.copiar_invitacion)
        self.b_i_anular = self._boton(p, fila, tr("&Anular"), tr("Anula el código elegido, si todavía no lo ha usado nadie."), self.anular_invitacion)
        self.b_i_actualizar = self._boton(p, fila, tr("Ac&tualizar"), tr("Vuelve a leer la lista de invitaciones. También con F6."), lambda: self.refrescar(todo=True, forzar=True))
        col.Add(fila, 0, wx.ALL, 2)
        # ---- Registro
        p, col = self._pagina(tr("Registro"))
        _, self.registro = crear_campo(p, tr("&Registro de lo que pasa:"), wx.TextCtrl, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP, size=(780, 260),
                                       ayuda=tr("Lo que va diciendo el servidor: quién entra y sale, los avisos y las respuestas a tus órdenes. Lo más nuevo, al final."), sizer=col)
        col.Detach(self.registro)
        col.Add(self.registro, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        _, self.campo_orden = crear_campo(p, tr("&Orden para el servidor:"), wx.TextCtrl, style=wx.TE_PROCESS_ENTER,
                                          ayuda=tr("Escribe una orden de las de la consola y pulsa Intro: ayuda las dice todas. Por ejemplo jugadores, aviso y un texto, "
                                                "expulsar y un nombre, invitar, guardar o copia. La respuesta sale en el registro."), sizer=col)
        self.campo_orden.Bind(wx.EVT_TEXT_ENTER, lambda e: self.enviar_orden())
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.b_orden = self._boton(p, fila, tr("E&nviar la orden"), tr("Manda al servidor la orden escrita. Es lo mismo que pulsar Intro en el campo."), self.enviar_orden)
        self.b_vaciar = self._boton(p, fila, tr("&Vaciar el registro"), tr("Borra lo que hay en esta ventana. No borra nada del servidor."), self.vaciar_registro)
        self.b_guardar_reg = self._boton(p, fila, tr("Guardar en un arc&hivo..."), tr("Guarda en un archivo de texto lo que hay en el registro. También con Control+G."), self.guardar_registro)
        col.Add(fila, 0, wx.ALL, 2)

    # ---------------------------------------------------------------- registro
    def _linea(self, texto):
        if not self:                                           # una línea que llega cuando la ventana ya se ha cerrado
            return
        self.lineas.append(texto)
        if len(self.lineas) > MAX_REGISTRO:
            del self.lineas[:len(self.lineas) - MAX_REGISTRO]
            self.registro.SetValue("\r\n".join(self.lineas) + "\r\n")
            self.registro.SetInsertionPointEnd()
            return
        # Se añade al final sin mover al lector: si está leyendo más arriba, el cursor se queda donde lo tiene.
        leyendo = self.registro.HasFocus() and self.registro.GetInsertionPoint() < self.registro.GetLastPosition()
        donde = self.registro.GetInsertionPoint()
        self.registro.AppendText(texto + "\r\n")
        if leyendo:
            self.registro.SetInsertionPoint(donde)

    def decir(self, texto, voz_tambien=True):
        """Algo que ha pasado por una acción de la ventana: a la barra de estado, al registro y, si hace falta, a la voz."""
        self.SetStatusText(texto.split("\n")[0][:200])
        self._linea("%s  %s" % (time.strftime("%H:%M:%S"), texto))
        if voz_tambien and self.hablar:
            voz.hablar(texto, interrumpir=False)

    def anunciar(self, texto):
        """Algo que hay que saber y que no deja rastro en pantalla donde el lector lo vaya a leer: barra de estado y voz."""
        self.SetStatusText(texto)
        if self.hablar:
            voz.hablar(texto, interrumpir=False)

    # ----------------------------------------------------------------- refresco
    def _aviso_motor(self, que, dato):
        if not self:
            return
        if que == "error":
            self.refrescar(todo=True, forzar=True)
            mostrar_error(self, dato, tr("El servidor no ha arrancado"))
            return
        # Que ha terminado de arrancar o de parar no lo puede saber el lector de pantalla: se dice. Al registro ya lo
        # ha apuntado el propio servidor.
        if que == "estado":
            self.motor.anotar()                                # la ficha dice si el servidor está en marcha: al día
        if dato == PARADO and self.motor.causa_parada == "actualizacion" and not self._cerrar_al_parar:
            # Lo ha pedido la actualización del juego (o la orden actualizar): el panel se cierra para que se pueda
            # sustituir su programa. Al terminar, la actualización lo vuelve a abrir y el servidor arranca solo.
            self._linea(tr("%s  El panel se cierra para que el juego se pueda actualizar.") % time.strftime("%H:%M:%S"))
            self._cerrar_al_parar = True
        elif dato == PARADO and self.motor.causa_parada == "reinicio" and not self._cerrar_al_parar and not self._tras_parar:
            self._reiniciar_al_parar = True                    # reiniciar por mantenimiento: vuelve a arrancar solo
        if dato == EN_MARCHA:
            self.anunciar(tr("Servidor en marcha en el puerto %s.") % ((self.motor.foto or {}).get("puerto") or self.cfg.get("puerto")))
        elif dato == PARADO and not self.motor.ultimo_error and not self._cerrar_al_parar:
            self.anunciar(tr("Servidor parado. Todo guardado."))
        self.refrescar(todo=True, forzar=True)
        if dato == PARADO:
            self._cerrar_router(esperar=self._cerrar_al_parar)     # al cerrar el panel, antes de irse
            despues, self._tras_parar = self._tras_parar, None
            if self._cerrar_al_parar:
                self.reloj.Stop()
                enmarcha.quitar()
                self.Destroy()
            elif self._reiniciar_al_parar:
                self._reiniciar_al_parar = False
                self.arrancar()
            elif despues is not None:
                despues()

    def _cambio_pestana(self, evento):
        evento.Skip()
        if evento.GetSelection() in (2, 3):                    # cuentas e invitaciones: al entrar, al día
            wx.CallAfter(self.refrescar, True)

    def _poner_lista(self, lista, textos, claves, antes):
        """Cambia el contenido de una lista solo si ha cambiado, y deja elegido lo que estaba elegido."""
        if lista.GetStrings() == textos:
            return
        i = lista.GetSelection()
        elegida = antes[i] if 0 <= i < len(antes) else None
        lista.Set(textos)
        if textos:
            lista.SetSelection(claves.index(elegida) if elegida in claves else min(max(i, 0), len(textos) - 1))

    def refrescar(self, todo=False, forzar=False):
        """Pone al día lo que se ve. Cada segundo, lo que cambia solo; con ``todo``, también las cuentas y las invitaciones."""
        estado, foto = self.motor.estado, self.motor.foto
        en_marcha = estado == EN_MARCHA
        if estado == PARADO and not self._cerrar_al_parar and self.motor.orden_pendiente() == "actualizar":
            # La actualización del juego pide paso y el servidor está parado: el panel se cierra sin más.
            self._cerrar_al_parar = True
            self.reloj.Stop()
            enmarcha.quitar()
            self.Destroy()
            return
        texto = texto_estado(estado, foto, self.cfg, self.local, self.motor.ultimo_error)
        actual = self.estado.GetValue().replace("\r\n", "\n")
        if texto != actual:
            # Mientras se está leyendo el estado no se reescribe solo porque haya pasado otro minuto (la primera línea):
            # solo si ha cambiado algo de verdad, como la gente que hay dentro. Y el cursor se queda donde estaba.
            sin_reloj = lambda t: t.split("\n", 1)[-1]
            if forzar or not self.estado.HasFocus() or sin_reloj(texto) != sin_reloj(actual):
                donde = self.estado.GetInsertionPoint()
                self.estado.SetValue(texto)
                self.estado.SetInsertionPoint(min(donde, self.estado.GetLastPosition()))
        gente = (foto or {}).get("jugadores", []) if en_marcha else []
        antes = [g["cuenta"] for g in self.jugadores]
        self.jugadores = gente
        self._poner_lista(self.lista_jugadores, [texto_jugador(g) for g in gente], [g["cuenta"] for g in gente], antes)
        self.SetTitle("%s: %s" % (NOMBRE, {PARADO: "parado", ARRANCANDO: "arrancando", PARANDO: "parando"}.get(estado) or
                                  ("en marcha, %d %s" % (len(gente), "jugador" if len(gente) == 1 else "jugadores"))))
        for control, vale in ((self.m_arrancar, estado == PARADO), (self.m_parar, en_marcha), (self.m_reiniciar, en_marcha), (self.m_anuncio, en_marcha),
                              (self.m_privado, en_marcha), (self.m_expulsar, en_marcha), (self.m_invitar, en_marcha), (self.m_mensaje, en_marcha),
                              (self.m_guardar, en_marcha), (self.m_router, en_marcha)):
            control.Enable(vale)
        for boton, vale in ((self.b_arrancar, estado == PARADO), (self.b_parar, en_marcha), (self.b_reiniciar, en_marcha)):
            if boton.IsEnabled() != vale:
                if not vale and boton.HasFocus():              # el foco no se queda en un botón apagado
                    self.estado.SetFocus()
                boton.Enable(vale)
        if not en_marcha:
            self.cuentas, self.invitaciones = [], []
            self._poner_lista(self.lista_cuentas, [], [], [])
            self._poner_lista(self.lista_invitaciones, [], [], [])
        elif todo or antes != [g["cuenta"] for g in gente]:      # ha entrado o salido alguien: puede haber cuentas nuevas
            self.motor.pedir(lambda srv: (srv.lista_cuentas(), srv.lista_invitaciones()), lambda r, error: wx.CallAfter(self._poner_cuentas, r, error))

    def _poner_cuentas(self, r, error):
        if error or r is None or not self:
            return
        cuentas, invitaciones = r
        antes = [c["id"] for c in self.cuentas]
        self.cuentas = cuentas
        self._poner_lista(self.lista_cuentas, [texto_cuenta(c) for c in cuentas], [c["id"] for c in cuentas], antes)
        antes = [i["codigo"] for i in self.invitaciones]
        self.invitaciones = invitaciones
        self._poner_lista(self.lista_invitaciones, [texto_invitacion(i) for i in invitaciones], [i["codigo"] for i in invitaciones], antes)

    # --------------------------------------------------------- arrancar y parar
    def arrancar(self):
        if self.motor.estado != PARADO:
            return
        self.motor.ultimo_error = ""
        self.SetStatusText(tr("Arrancando el servidor..."))
        self.motor.arrancar()
        self.refrescar(forzar=True)

    def parar(self, preguntar=True, causa="apagado"):
        if self.motor.estado != EN_MARCHA:
            return False
        n = len(self.jugadores)
        if preguntar and n and confirmar(self, "Hay %d %s. Si paras el servidor se les avisa, se guarda todo y se les desconecta. ¿Lo paras?" % (
                n, tr("jugador dentro") if n == 1 else tr("jugadores dentro")), tr("Parar el servidor"), peligroso=True) != wx.ID_YES:
            return False
        self.SetStatusText(tr("Parando el servidor y guardándolo todo..."))
        self.motor.parar(causa=causa)
        self.refrescar(forzar=True)
        return True

    def reiniciar(self):
        # Se para diciendo que es un reinicio: los juegos esperan y vuelven a entrar solos en cuanto arranca otra vez.
        if self.motor.estado == EN_MARCHA and self.parar(causa="reinicio"):
            self._reiniciar_al_parar = True

    def _al_cerrar(self, evento):
        if self.motor.estado == PARADO:
            self.reloj.Stop()
            enmarcha.quitar()
            self.Destroy()
            return
        if evento.CanVeto() and not self._cerrar_al_parar:
            n = len(self.jugadores)
            pregunta = tr("El servidor está en marcha") + ((tr(", con %d %s") % (n, tr("jugador dentro") if n == 1 else tr("jugadores dentro"))) if n else "") + \
                tr(". Si cierras el panel, se avisa a los jugadores, se guarda todo y el servidor se para. ¿Cierras?")
            if confirmar(self, pregunta, tr("Cerrar el panel"), peligroso=True) != wx.ID_YES:
                evento.Veto()
                return
        self._cerrar_al_parar = True
        if self.motor.estado == EN_MARCHA:
            self.SetStatusText(tr("Parando el servidor y guardándolo todo antes de cerrar..."))
            self.motor.parar(es("Quien administra el servidor lo ha cerrado."))
        if evento.CanVeto():
            evento.Veto()                                      # se cierra sola en cuanto el servidor termina de guardar
        else:                                                  # Windows se apaga: no hay más remedio que esperar aquí
            self.motor.esperar_parado(15)
            enmarcha.quitar()
            self.Destroy()

    # ---------------------------------------------------------------- órdenes
    def _orden(self, texto, tras=None, callar=False):
        """Manda una orden al servidor. La respuesta llega luego: se dice y, si se pide, se hace algo con ella."""
        def al_terminar(r, error):
            wx.CallAfter(self._respuesta, texto, r, error, tras, callar)
        self.motor.orden(texto, al_terminar)                   # si está parado, la respuesta lo dice

    def _respuesta(self, texto, r, error, tras, callar):
        if not self:
            return
        if error == "parado":
            self.decir(tr("El servidor está parado: arráncalo con F5 para poder hacer eso."))
            return
        if error:
            self.decir(tr("No se ha podido hacer: ") + error)
            return
        if not callar:
            self.decir(str(r))
        if tras is not None:
            tras(str(r))
        self.refrescar(todo=True, forzar=True)

    def _necesita_marcha(self):
        if self.motor.estado == EN_MARCHA:
            return True
        self.decir(tr("El servidor está parado: arráncalo con F5 para poder hacer eso."))
        return False

    def _jugador(self):
        i = self.lista_jugadores.GetSelection()
        if 0 <= i < len(self.jugadores):
            return self.jugadores[i]
        self.decir(tr("Elige antes a un jugador en la lista de jugadores.") if self.jugadores else tr("No hay ningún jugador dentro."))
        return None

    def _cuenta(self):
        i = self.lista_cuentas.GetSelection()
        if 0 <= i < len(self.cuentas):
            return self.cuentas[i]
        self.decir(tr("Elige antes una cuenta en la lista de cuentas.") if self.cuentas else tr("No hay ninguna cuenta en la lista."))
        return None

    def _elegido(self, de_cuentas):
        return self._cuenta() if de_cuentas else self._jugador()

    def anuncio(self):
        if not self._necesita_marcha():
            return
        t = pedir_texto(self, tr("&Anuncio para todos los jugadores:"), tr("Anuncio a todos"), max_caracteres=300,
                        ayuda=tr("Lo oirán todos los que están dentro ahora mismo, con «Aviso del servidor» delante."))
        if t and t.strip():
            self._orden(tr("aviso ") + " ".join(t.split()))

    def mensaje_privado(self):
        if not self._necesita_marcha():
            return
        g = self._jugador()
        if g is None:
            return
        t = pedir_texto(self, tr("&Mensaje para %s:") % g["nombre"], tr("Mensaje a un jugador"), max_caracteres=300, ayuda=tr("Solo lo oirá ese jugador."))
        if t and t.strip():
            self._orden(tr("decir %s: %s") % (g["nombre"], " ".join(t.split())))

    def expulsar(self):
        if not self._necesita_marcha():
            return
        g = self._jugador()
        if g is None:
            return
        motivo = pedir_texto(self, tr("&Motivo que se le dirá a %s, si quieres decirle alguno:") % g["nombre"], tr("Expulsar a ") + g["nombre"], max_caracteres=200,
                             ayuda=tr("Se le saca del servidor, pero puede volver a entrar. Deja el motivo vacío si no quieres decirle nada. Cancelar no le expulsa."))
        if motivo is None:
            return
        motivo = " ".join(motivo.replace(":", ",").split())
        self._orden(tr("expulsar %s%s") % (g["nombre"], (": " + motivo) if motivo else ""))

    def vetar(self, de_cuentas=False):
        if not self._necesita_marcha():
            return
        g = self._elegido(de_cuentas)
        if g is None:
            return
        if elegir_opcion(self, tr("%s no podrá volver a entrar en este servidor hasta que le perdones el veto, en la pestaña Cuentas. Si está dentro, se le saca ahora.") % g["nombre"],
                         tr("Vetar a ") + g["nombre"], [tr("&Vetar"), tr("&No vetar")]) == 0:
            self._orden(tr("vetar ") + g["nombre"])

    def perdonar(self):
        if not self._necesita_marcha():
            return
        c = self._cuenta()
        if c is not None:
            self._orden(tr("perdonar ") + c["nombre"])

    def hacer_admin(self, de_cuentas=False):
        if not self._necesita_marcha():
            return
        g = self._elegido(de_cuentas)
        if g is None:
            return
        if elegir_opcion(self, tr("%s podrá dar órdenes al servidor desde el chat del juego: expulsar, vetar, avisar, crear invitaciones y apagarlo.") % g["nombre"],
                         tr("Hacer administrador a ") + g["nombre"], [tr("&Hacer administrador"), tr("&No hacerlo")]) == 0:
            self._orden(tr("admin ") + g["nombre"])

    def quitar_admin(self):
        if not self._necesita_marcha():
            return
        c = self._cuenta()
        if c is not None:
            self._orden(tr("quitaradmin ") + c["nombre"])

    def borrar_cuenta(self):
        if not self._necesita_marcha():
            return
        c = self._cuenta()
        if c is None:
            return
        if elegir_opcion(self, tr("Se va a borrar la cuenta de %s con su personaje, sus casas y negocios y su sitio en la banda. No se puede deshacer.\n\n"
                               "Si esa persona vuelve a entrar, empezará de cero. Para que no vuelva, lo que hay que hacer es vetarla.") % c["nombre"],
                         tr("Borrar la cuenta de ") + c["nombre"], [tr("&Borrar la cuenta"), tr("&No borrarla")]) == 0:
            self._orden(tr("borrarcuenta ") + c["nombre"])

    def invitar(self):
        if not self._necesita_marcha():
            return

        def tras(respuesta):
            codigo = respuesta.rsplit(":", 1)[-1].strip()
            self._al_portapapeles(codigo)
            mostrar_mensaje(self, tr("Código de invitación, de un solo uso:\n%s\n\nYa está copiado en el portapapeles: pégalo en un mensaje para quien quieras invitar.\n"
                                  "Solo hace falta si la entrada del servidor es por invitación; se elige en Configuración, pestaña Acceso y administración.") % codigo, tr("Invitación creada"))
        self._orden("invitar", tras=tras)

    def _invitacion(self):
        i = self.lista_invitaciones.GetSelection()
        if 0 <= i < len(self.invitaciones):
            return self.invitaciones[i]
        self.decir(tr("Elige antes una invitación en la lista.") if self.invitaciones else tr("No hay ninguna invitación. Crea una con Control+I."))
        return None

    def copiar_invitacion(self):
        i = self._invitacion()
        if i is not None:
            self._al_portapapeles(i["codigo"])
            self.decir(tr("Código %s copiado al portapapeles.") % i["codigo"])

    def anular_invitacion(self):
        if not self._necesita_marcha():
            return
        i = self._invitacion()
        if i is None:
            return
        if i["usada"]:
            self.decir(tr("Esa invitación ya la ha usado alguien: no hay nada que anular."))
            return
        self._orden(tr("anular ") + i["codigo"])

    def mensaje_dia(self):
        actual = str(self.cfg.get("mensaje_dia", ""))
        t = pedir_texto(self, tr("Mensaje del &día, el aviso que oye cada jugador al entrar. Vacío, ninguno:"), tr("Mensaje del día"), valor=actual, max_caracteres=300,
                        ayuda=tr("Se guarda en la configuración y, si el servidor está en marcha, lo oyen también los que están dentro."))
        if t is None:
            return
        valor, error = opciones.validar_valor("mensaje_dia", " ".join(t.split()))
        if error:
            mostrar_error(self, tr("El mensaje del día ") + error + ".")
            return
        self.cfg["mensaje_dia"] = valor
        self._guardar_config(self.cfg, preguntar_reinicio=False)
        if self.motor.estado == EN_MARCHA:
            self._orden(tr("mensaje ") + valor, callar=True)
        self.decir(tr("Mensaje del día cambiado y guardado.") if valor else tr("Mensaje del día quitado."))

    def ir_a_orden(self):
        self.cuaderno.SetSelection(4)
        self.campo_orden.SetFocus()

    def enviar_orden(self):
        texto = " ".join(self.campo_orden.GetValue().split())
        if not texto:
            self.decir(tr("Escribe antes una orden. La orden ayuda las dice todas."))
            return
        if not self._necesita_marcha():
            return
        from servidor.nucleo import orden_espanola
        que = orden_espanola(texto.split()[0])                   # en español o en inglés: apagar o shutdown, decir o tell
        if que == "apagar":
            self.parar()
        else:
            self._linea("%s  > %s" % (time.strftime("%H:%M:%S"), texto.split()[0] if que == "decir" else texto))
            self._orden(texto)
        self.campo_orden.SetValue("")

    def guardar_ahora(self):
        if self._necesita_marcha():
            self._orden("guardar")

    # ------------------------------------------------------------ portapapeles
    def _al_portapapeles(self, texto):
        try:
            if wx.TheClipboard.Open():
                try:
                    wx.TheClipboard.SetData(wx.TextDataObject(texto))
                    wx.TheClipboard.Flush()
                finally:
                    wx.TheClipboard.Close()
                return True
        except Exception:
            pass
        return False

    def copiar_direccion(self):
        puerto = (self.motor.foto or {}).get("puerto") or self.cfg.get("puerto")
        if not self.local:
            self.decir(tr("No he podido saber la dirección de este ordenador en tu red. Mírala en la configuración de red de Windows."))
            return
        direccion = "%s:%s" % (self.local, puerto)
        self._al_portapapeles(direccion)
        self.decir(tr("Copiada la dirección %s. Vale para quien juegue en tu misma casa; para quien juegue desde fuera, mira la guía con F1.") % direccion)

    # ------------------------------------------------------------------ router
    def abrir_router(self):
        """Pide al router que abra el puerto del servidor (UPnP). Solo si lo pide quien administra, y se cierra al parar."""
        if not self._necesita_marcha():
            return
        puerto = (self.motor.foto or {}).get("puerto") or self.cfg.get("puerto")
        if self._router:
            if elegir_opcion(self, tr("El puerto %s ya está abierto en tu router. Se cerrará solo al parar el servidor.") % puerto, tr("Puerto del router"),
                             [tr("&Cerrar el puerto ahora"), tr("&Dejarlo abierto")]) == 0:
                self._cerrar_router(decir=True)
            return

        def trabajo():
            from juego import upnp
            return upnp.abrir(puerto, tr("Servidor de Puerto Bravo"), buscar=self.buscar_router or upnp.descubrir)

        def hecho(r, error):
            if error or not r:
                self.decir(tr("No he podido hablar con el router: %s. La guía explica cómo abrir el puerto a mano, con F1.") % (error or tr("no ha contestado")))
                return
            conseguido, datos, motivo = r
            if conseguido:
                self._router = datos
                self.decir(tr("He abierto el puerto %s en tu router: quien juegue desde fuera de tu casa ya puede entrar con tu dirección pública. "
                           "Se cerrará al parar el servidor.") % puerto)
            else:
                self.decir(tr("No he podido abrir el puerto en el router: %s. La guía explica cómo abrirlo a mano, con F1.") % {
                    "no_responde": tr("el router no responde a la petición; puede que tenga UPnP desactivado"),
                    "no_permite": tr("tu router no lo permite")}.get(motivo, tr("el router ha rechazado la petición")))
        self.SetStatusText(tr("Pidiendo al router que abra el puerto..."))
        self._en_segundo_plano(trabajo, hecho)

    def _cerrar_router(self, decir=False, esperar=False):
        datos, self._router = self._router, None
        if not datos:
            return

        def cerrar():
            try:
                from juego import upnp
                upnp.cerrar(datos)
            except Exception:
                pass
        hilo = threading.Thread(target=cerrar, daemon=True)
        hilo.start()
        if esperar:
            hilo.join(5)
        if decir:
            self.decir(tr("He pedido al router que cierre el puerto."))

    # ---------------------------------------------------------- menús de lista
    def _menu_de(self, acciones):
        menu = wx.Menu()
        for texto, accion in acciones:
            item = menu.Append(wx.ID_ANY, texto)
            menu.Bind(wx.EVT_MENU, lambda e, a=accion: a(), item)
        return menu

    def _menu_jugador(self):
        if not self.jugadores:
            return None
        return self._menu_de(((tr("&Mensaje..."), self.mensaje_privado), (tr("&Expulsar..."), self.expulsar), (tr("&Vetar..."), self.vetar), (tr("Hacer &administrador"), self.hacer_admin)))

    def _menu_cuenta(self):
        if not self.cuentas:
            return None
        return self._menu_de(((tr("&Vetar..."), lambda: self.vetar(de_cuentas=True)), (tr("&Perdonar el veto"), self.perdonar),
                              (tr("Hacer &administrador"), lambda: self.hacer_admin(de_cuentas=True)), (tr("&Quitar la administración"), self.quitar_admin),
                              (tr("&Borrar la cuenta..."), self.borrar_cuenta)))

    # ----------------------------------------------------------- configuración
    def configurar(self):
        self.cfg, _ = self.motor.leer_config()
        dlg = DialogoConfiguracion(self, self.cfg, al_aplicar=self._guardar_config, en_marcha=self.motor.estado == EN_MARCHA)
        dlg.ShowModal()
        dlg.Destroy()
        self.refrescar(forzar=True)

    def _guardar_config(self, valores, preguntar_reinicio=True):
        """Escribe servidor.conf y, si el servidor está en marcha, le aplica lo que se puede cambiar sin reiniciar."""
        try:
            self.motor.guardar_config(valores)
        except OSError as e:
            mostrar_error(self, tr("No se ha podido guardar la configuración en %s.\n%s") % (self.motor.ruta_conf, e), tr("Error al guardar"))
            return False
        self.cfg = dict(valores)
        if self.motor.estado != EN_MARCHA:
            if preguntar_reinicio:
                self.decir(tr("Configuración guardada. Valdrá en cuanto arranques el servidor."))
            return True

        def al_terminar(r, error):
            wx.CallAfter(self._config_aplicada, r, error, preguntar_reinicio)
        self.motor.aplicar_config(valores, al_terminar)
        return True

    def _config_aplicada(self, r, error, preguntar_reinicio):
        if not self or error or r is None:
            return
        al_momento, con_reinicio = r
        nombres = lambda claves: ", ".join(opciones.POR_CLAVE[c].etiqueta for c in claves)
        if not preguntar_reinicio:
            return
        if not con_reinicio:
            self.decir(tr("Configuración guardada y aplicada.") + ((tr(" Ha cambiado: %s.") % nombres(al_momento)) if al_momento else tr(" No había nada que cambiar.")))
            return
        texto = (tr("Configuración guardada.\n") + ((tr("Ya se ha aplicado: %s.\n") % nombres(al_momento)) if al_momento else "") +
                 tr("\nEstos cambios no valen hasta que reinicies el servidor: %s.\n\nReiniciar desconecta un momento a los jugadores; su personaje queda guardado.") % nombres(con_reinicio))
        if elegir_opcion(wx.GetActiveWindow() or self, texto, tr("Hay cambios que piden reiniciar"), [tr("&Reiniciar ahora"), tr("&Más tarde")]) == 0:
            if self.motor.estado == EN_MARCHA:
                self._reiniciar_al_parar = True
                self.motor.parar(causa="reinicio")
                self.refrescar(forzar=True)

    # ------------------------------------------------------------------ copias
    def _en_segundo_plano(self, trabajo, al_terminar):
        """Hace algo lento fuera del hilo de la interfaz y vuelve con el resultado."""
        if self._ocupada:
            self.decir(tr("Espera a que termine lo que se está haciendo."))
            return

        def correr():
            try:
                r, error = trabajo(), None
            except Exception as e:
                r, error = None, (str(e) if isinstance(e, (ValueError, RuntimeError)) else "%s: %s" % (type(e).__name__, e))
            wx.CallAfter(terminar, r, error)

        def terminar(r, error):
            self._ocupada = False
            if self:
                al_terminar(r, error)
        self._ocupada = True
        threading.Thread(target=correr, daemon=True).start()

    def copia(self):
        if self.motor.estado == EN_MARCHA:
            self._orden("copia")
        elif self.motor.estado == PARADO:
            if not os.path.exists(os.path.join(self.motor.carpeta_datos(), copias.BASE)):
                self.decir(tr("Todavía no hay datos que copiar: el servidor no ha arrancado nunca con esta carpeta de datos."))
                return
            self.SetStatusText(tr("Haciendo la copia de seguridad..."))
            self._en_segundo_plano(self.motor.copia_parado, lambda r, error: self.decir((tr("No se ha podido hacer la copia: ") + error) if error else tr("Copia hecha en ") + r))
        else:
            self.decir(tr("Espera a que el servidor termine de arrancar o de parar."))

    def restaurar(self):
        if self.motor.estado in (ARRANCANDO, PARANDO):
            self.decir(tr("Espera a que el servidor termine de arrancar o de parar."))
            return
        lista = copias.listar(self.motor.carpeta_datos())
        dlg = DialogoCopias(self, lista)
        ruta = dlg.elegida() if dlg.ShowModal() == wx.ID_OK else None
        con_conf = dlg.con_conf.GetValue()
        dlg.Destroy()
        if not ruta:
            return
        en_marcha = self.motor.estado == EN_MARCHA
        aviso = (tr("Se van a cambiar los datos del servidor por los de la copia %s. Lo que hay ahora se guarda antes en otra copia, por si acaso.%s") % (
            os.path.basename(ruta), tr("\n\nEl servidor está en marcha: se parará, se restaurará la copia y tendrás que arrancarlo tú después.") if en_marcha else ""))
        if elegir_opcion(self, aviso, tr("Restaurar una copia de seguridad"), [tr("&Restaurar"), tr("&No restaurar")]) != 0:
            return

        def hacer():
            self.SetStatusText(tr("Restaurando la copia..."))
            self._en_segundo_plano(lambda: self.motor.restaurar(ruta, con_conf), hecho)

        def hecho(r, error):
            if error:
                self.decir(tr("No se ha podido restaurar: ") + error, voz_tambien=False)
                mostrar_error(self, error, tr("No se ha restaurado la copia"))
                return
            previa, restaurados = r
            self.cfg, _ = self.motor.leer_config()
            self.decir(tr("Copia restaurada: %s.") % ", ".join(restaurados) + ((tr(" Lo que había queda en %s.") % os.path.basename(previa)) if previa else "") +
                       tr(" Arranca el servidor con F5."))
            self.refrescar(forzar=True)
        if en_marcha:
            self._tras_parar = hacer
            self.motor.parar(es("El servidor se para un momento para restaurar una copia de seguridad."))
            self.refrescar(forzar=True)
        else:
            hacer()

    def abrir_datos(self):
        carpeta = self.motor.carpeta_datos()
        os.makedirs(carpeta, exist_ok=True)
        self._abrir(carpeta)

    def abrir_copias(self):
        carpeta = copias.carpeta_copias(self.motor.carpeta_datos())
        os.makedirs(carpeta, exist_ok=True)
        self._abrir(carpeta)

    def _abrir(self, ruta):
        try:
            os.startfile(ruta)
        except (OSError, AttributeError) as e:
            mostrar_error(self, tr("No se ha podido abrir %s.\n%s") % (ruta, e))

    def vaciar_registro(self):
        self.lineas = []
        self.registro.SetValue("")
        self.SetStatusText(tr("Registro vaciado."))

    def guardar_registro(self):
        with wx.FileDialog(self, tr("Guardar el registro"), defaultFile="registro_servidor_%s.txt" % time.strftime("%Y%m%d_%H%M"),
                           wildcard=tr("Texto (*.txt)|*.txt"), style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            ruta = dlg.GetPath()
        try:
            with open(ruta, "w", encoding="utf-8-sig", newline="\r\n") as f:
                f.write("\n".join(self.lineas) + "\n")
        except OSError as e:
            mostrar_error(self, tr("No se ha podido guardar el registro.\n%s") % e, tr("Error al guardar"))
            return
        self.decir(tr("Registro guardado en ") + ruta)

    # ------------------------------------------------------------------- ayuda
    def guia(self):
        ruta = ruta_documentacion()
        if ruta is None:
            mostrar_error(self, tr("No encuentro la guía del servidor. Debería estar en la carpeta servidor, con el nombre documentacion_es.html, "
                                "o en data, docs, servidor_es.html."))
            return
        self._abrir(ruta)

    def teclas(self):
        mostrar_mensaje(self, TECLAS, tr("Teclas del panel"))

    def acerca(self):
        mostrar_mensaje(self, tr("%s.\n\nPone en marcha y administra un servidor en línea de Puerto Bravo: Ley del Asfalto en este ordenador, sin usar la consola.\n\n"
                              "Es el mismo servidor que se arranca por consola, con la misma configuración (servidor.conf) y los mismos datos.\n\n"
                              "Software libre con licencia MIT. Control+H explica el control en el que estás. F1 abre la guía.") % NOMBRE, tr("Acerca del panel"))


TECLAS = tr("""Teclas del panel del servidor

F5: arrancar el servidor.
Mayúsculas+F5: parar el servidor.
Control+F5: reiniciar el servidor.
Control+P: configuración.
Control+Q: salir.

Control+N: anuncio a todos los jugadores.
Control+M: mensaje al jugador elegido.
Control+E: expulsar al jugador elegido.
Control+I: crear una invitación.
Control+D: mensaje del día.
Control+O: escribir una orden.
F6: actualizar las listas y el estado.

Control+S: guardar ahora.
Control+B: copia de seguridad ahora.
Control+R: restaurar una copia.
Control+G: guardar el registro en un archivo.

F1: guía del servidor.
Control+H: explica el control en el que estás.
Control+Tabulador y Control+Mayúsculas+Tabulador: cambiar de pestaña.
Alt más la letra subrayada: ir a un control de la pestaña o abrir un menú.
Tecla Aplicaciones o Mayúsculas+F10 en las listas de jugadores y de cuentas: acciones sobre lo elegido.""")


def ejecutar(ruta_conf=None, arrancar=False, sin_foco=None):
    """Abre el panel. ``sin_foco``: no activar la ventana ni tocar el foco; si no se dice, se hace caso a cómo lo haya
    arrancado Windows (la actualización del juego lo vuelve a abrir minimizado y sin activar)."""
    if sin_foco is None:
        sin_foco = abierto_sin_activar()
    app = wx.App(False)
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    try:
        from editor.accesibilidad import idioma
        app._idioma = idioma.fijar_idioma_espanol()
    except Exception:
        pass
    ventana = VentanaPanel(ruta_conf, sin_foco=sin_foco)
    if sin_foco:
        ventana.ShowWithoutActivating()          # a la vista en la barra de tareas, sin quitarle el foco a nadie
        if not ventana.IsIconized():
            ventana.Iconize(True)
    else:
        ventana.Show()
    if arrancar:                                 # --arrancar: lo pone la actualización del juego si el servidor estaba en marcha
        wx.CallAfter(ventana.arrancar)
    app.MainLoop()
