"""El diálogo de configuración del servidor: una pestaña por grupo de opciones.

No hay ninguna opción escrita a mano aquí: las pestañas, las etiquetas, las ayudas, los rangos y los valores salen de
``servidor.opciones``, que es de donde salen también el ejemplo de servidor.conf, la comprobación y la documentación.
"""
import wx

from editor.accesibilidad.dialogos import crear_botonera, elegir_opcion, mostrar_error, preparar_dialogo
from editor.accesibilidad.nombres import crear_campo
from servidor import opciones

LETRAS = "abcdefghijklmnopqrstuvwxyz"
# Letras de los botones del diálogo, que se ven en todas las pestañas: Aceptar, Cancelar, Aplicar y Valores de fábrica.
RESERVADAS = "acpf"


def con_letra(etiqueta, usadas):
    """Pone la letra de acceso (&) en la primera letra libre de la etiqueta."""
    for i, ch in enumerate(etiqueta):
        b = ch.lower()
        if b in LETRAS and b not in usadas:
            usadas.add(b)
            return etiqueta[:i] + "&" + etiqueta[i:]
    return etiqueta


def ayuda_de(o):
    """Lo que dice Control+H en el control de una opción: qué es, qué admite y si pide reiniciar."""
    partes = [o.ayuda, o.descripcion_valores(), "De serie: %s." % (o.defecto if o.defecto != "" else "vacío")]
    partes.append("Para que este cambio valga hay que reiniciar el servidor." if o.reinicio else "Se aplica sin reiniciar el servidor.")
    partes.append("En servidor.conf se llama %s." % o.clave)
    return " ".join(partes)


class DialogoConfiguracion(wx.Dialog):
    """Edita todas las opciones del servidor. ``al_aplicar(valores)`` se llama con Aceptar y con Aplicar, y devuelve si ha ido bien."""

    def __init__(self, padre, cfg, al_aplicar=None, en_marcha=False):
        super().__init__(padre, title="Configuración del servidor", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, name="Configuración del servidor")
        self.al_aplicar = al_aplicar
        self.controles = {}                      # clave -> control
        self.paginas = {}                        # clave -> número de pestaña
        sizer = wx.BoxSizer(wx.VERTICAL)
        aviso = wx.StaticText(self, label=("El servidor está en marcha. " if en_marcha else "") +
                              "Las opciones que piden reiniciar lo dicen en su ayuda, con Control+H. Control+Tabulador cambia de pestaña.")
        aviso.Wrap(680)
        sizer.Add(aviso, 0, wx.ALL, 8)
        self.cuaderno = wx.Notebook(self, name="Grupos de opciones")
        for n, (ident, titulo, que) in enumerate(opciones.SECCIONES):
            pagina = wx.Panel(self.cuaderno, name=titulo)
            columna = wx.BoxSizer(wx.VERTICAL)
            usadas = set(RESERVADAS)
            for o in opciones.de_seccion(ident):
                self.controles[o.clave] = self._crear(pagina, o, usadas, columna)
                self.paginas[o.clave] = n
            pagina.SetSizer(columna)
            self.cuaderno.AddPage(pagina, titulo)
        sizer.Add(self.cuaderno, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.boton_fabrica = wx.Button(self, label="Valores de &fábrica...")
        self.boton_fabrica.SetHelpText("Deja las opciones como vienen de serie: las de esta pestaña o todas. No se guarda nada hasta que pulses Aceptar o Aplicar.")
        self.boton_fabrica.Bind(wx.EVT_BUTTON, lambda e: self.de_fabrica())
        fila.Add(self.boton_fabrica, 0, wx.ALL, 8)
        fila.AddStretchSpacer()
        fila.Add(crear_botonera(self, wx.OK | wx.CANCEL | wx.APPLY), 0, wx.ALL, 8)
        sizer.Add(fila, 0, wx.EXPAND)
        self.SetSizerAndFit(sizer)
        self.poner(cfg)
        self.Bind(wx.EVT_BUTTON, self._aceptar, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self._aplicar, id=wx.ID_APPLY)
        primero = self.controles[opciones.de_seccion(opciones.SECCIONES[0][0])[0].clave]
        preparar_dialogo(self, foco_inicial=primero)
        self.CentreOnParent()

    # ---------------------------------------------------------------- controles
    def _crear(self, pagina, o, usadas, columna):
        ayuda = ayuda_de(o)
        if o.tipo == opciones.SINO:
            control = wx.CheckBox(pagina, label=con_letra(o.etiqueta, usadas), name=o.etiqueta)
            control.SetHelpText(ayuda)
            columna.Add(control, 0, wx.ALL, 6)
            return control
        etiqueta = con_letra(o.etiqueta, usadas) + ":"
        if o.tipo == opciones.ENTERO:
            # SpinCtrl nativo: el lector dice su etiqueta y su valor. Nunca SpinCtrlDouble.
            _, control = crear_campo(pagina, etiqueta, wx.SpinCtrl, min=o.minimo, max=o.maximo, initial=o.defecto, size=(140, -1),
                                     ayuda=ayuda, sizer=columna, horizontal=True, expandir=False)
        elif o.tipo == opciones.ELECCION:
            _, control = crear_campo(pagina, etiqueta, wx.Choice, choices=["%s: %s" % (v, d) for v, d in o.valores], ayuda=ayuda, sizer=columna)
        else:
            estilo = wx.TE_PASSWORD if o.tipo == opciones.SECRETO else 0
            _, control = crear_campo(pagina, etiqueta, wx.TextCtrl, style=estilo, ayuda=ayuda, sizer=columna)
            control.SetMaxLength(o.largo)
        return control

    def poner(self, cfg, solo=None):
        """Lleva unos valores a los controles. Con ``solo``, únicamente las opciones de esas claves."""
        for o in opciones.OPCIONES:
            if solo is not None and o.clave not in solo:
                continue
            control, valor = self.controles[o.clave], cfg.get(o.clave, o.defecto)
            if o.tipo == opciones.SINO:
                control.SetValue(str(valor).strip().lower() in ("si", "sí", "1", "true", "yes"))
            elif o.tipo == opciones.ENTERO:
                try:
                    control.SetValue(max(o.minimo, min(o.maximo, int(valor))))
                except (TypeError, ValueError):
                    control.SetValue(o.defecto)
            elif o.tipo == opciones.ELECCION:
                permitidos = o.permitidos()
                control.SetSelection(permitidos.index(valor) if valor in permitidos else permitidos.index(o.defecto))
            else:
                control.SetValue(str(valor))

    def crudo(self):
        """Lo que hay ahora en los controles, sin comprobar."""
        out = {}
        for o in opciones.OPCIONES:
            control = self.controles[o.clave]
            if o.tipo == opciones.SINO:
                out[o.clave] = "si" if control.GetValue() else "no"
            elif o.tipo == opciones.ENTERO:
                out[o.clave] = control.GetValue()
            elif o.tipo == opciones.ELECCION:
                i = control.GetSelection()
                out[o.clave] = o.permitidos()[i] if i >= 0 else o.defecto
            else:
                out[o.clave] = control.GetValue()
        return out

    def valores(self):
        """Los valores ya comprobados, o None si alguno no vale: entonces lo dice y lleva el foco a ese control."""
        crudo, limpio = self.crudo(), {}
        for o in opciones.OPCIONES:
            valor, error = opciones.validar_valor(o.clave, crudo[o.clave])
            if error:
                self.ir_a(o.clave)
                mostrar_error(self, "%s: %s." % (o.etiqueta, error), "Hay un valor que no vale")
                self.ir_a(o.clave)
                return None
            limpio[o.clave] = valor
        if limpio["entrada"] == "clave" and not limpio["clave"]:
            self.ir_a("clave")
            mostrar_error(self, "Has elegido que para crear un personaje haga falta la contraseña de entrada, pero la contraseña está vacía. "
                                "Escribe una, o cambia quién puede crear un personaje.", "Falta la contraseña de entrada")
            self.ir_a("clave")
            return None
        return limpio

    def ir_a(self, clave):
        self.cuaderno.SetSelection(self.paginas[clave])
        self.controles[clave].SetFocus()

    # ----------------------------------------------------------------- acciones
    def de_fabrica(self):
        n = self.cuaderno.GetSelection()
        titulo = opciones.SECCIONES[n][1]
        r = elegir_opcion(self, "¿Qué opciones quieres dejar como vienen de serie? No se guarda nada hasta que pulses Aceptar o Aplicar.",
                          "Valores de fábrica", ["Solo las de «%s»" % titulo, "&Todas las opciones"])
        if r is None:
            return
        serie = opciones.valores_de_serie()
        self.poner(serie, solo=None if r == 1 else {o.clave for o in opciones.de_seccion(opciones.SECCIONES[n][0])})

    def _aplicar(self, evento):
        v = self.valores()
        if v is not None and self.al_aplicar is not None:
            self.al_aplicar(v)

    def _aceptar(self, evento):
        v = self.valores()
        if v is None:
            return
        if self.al_aplicar is None or self.al_aplicar(v) is not False:
            self.EndModal(wx.ID_OK)
