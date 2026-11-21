"""Formularios accesibles generados a partir del esquema.

Se siguen las pautas de accesibilidad para wxPython: cada etiqueta se crea justo antes de su control
y con el mismo padre, todos los controles son nativos, cada campo tiene letra de acceso sin repetir,
los botones dicen su acción en español y Ctrl+H explica el campo enfocado.
"""
from juego.i18n import tr
import copy

import wx

from . import modelo
from .accesibilidad.dialogos import confirmar, crear_botonera, enfocar, mostrar_error, preparar_dialogo
from .accesibilidad.nombres import crear_campo
from .esquema import ESQUEMAS

SIN_VALOR = tr("(sin valor)")
LETRAS = "abcdefghijklmnopqrstuvwxyz"


def letra_de(etiqueta):
    """La letra de acceso de una etiqueta con «&»: «&Aceptar» da «a»."""
    i = etiqueta.find("&")
    return etiqueta[i + 1].lower() if 0 <= i < len(etiqueta) - 1 else ""


def con_letra(etiqueta, usadas):
    """Pone la letra de acceso (&) en la primera letra libre de la etiqueta."""
    for i, ch in enumerate(etiqueta):
        b = ch.lower()
        if b in LETRAS and b not in usadas:
            usadas.add(b)
            return etiqueta[:i] + "&" + etiqueta[i:]
    return etiqueta


def _numero(texto, decimal):
    texto = texto.strip().replace(",", ".")
    if not texto:
        return None
    valor = float(texto)
    if not decimal:
        if valor != int(valor):
            raise ValueError
        return int(valor)
    return int(valor) if valor == int(valor) else valor


def _texto_numero(v):
    if v is None or v == "":
        return ""
    return str(v).replace(".", ",") if isinstance(v, float) else str(v)


class PanelElementos(wx.Panel):
    """Lista de elementos con sus botones: añadir, editar, duplicar, borrar, subir y bajar."""

    def __init__(self, padre, nombre_esq, elementos, cat, mod, al_cambiar=None, usadas=None, etiqueta=tr("Lista"), extra=()):
        super().__init__(padre)
        self.nombre_esq = nombre_esq
        self.elementos = elementos
        self.cat = cat
        self.mod = mod
        self.al_cambiar = al_cambiar
        usadas = usadas if usadas is not None else set()
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.etiqueta, self.lista = crear_campo(self, con_letra(etiqueta, usadas) + ":", wx.ListBox, style=wx.LB_SINGLE, size=(520, 200),
                                                ayuda=tr("Flechas para recorrer la lista. Intro edita el elemento y Suprimir lo borra."), sizer=sizer)
        fila = wx.BoxSizer(wx.HORIZONTAL)
        self.botones = {}
        for clave, texto, ayuda in (("anadir", tr("Añadir"), tr("Crea un elemento nuevo al final de la lista.")), ("editar", tr("Editar"), tr("Abre el formulario del elemento elegido.")),
                                    ("duplicar", tr("Duplicar"), tr("Crea una copia del elemento elegido.")), ("borrar", tr("Borrar"), tr("Borra el elemento elegido.")),
                                    ("subir", tr("Subir"), tr("Mueve el elemento un puesto hacia arriba.")), ("bajar", tr("Bajar"), tr("Mueve el elemento un puesto hacia abajo."))) + tuple(extra):
            b = wx.Button(self, label=con_letra(texto, usadas))
            b.SetHelpText(ayuda)
            self.botones[clave] = b
            fila.Add(b, 0, wx.RIGHT, 6)
        sizer.Add(fila, 0, wx.ALL, 5)
        self.SetSizer(sizer)
        self.botones["anadir"].Bind(wx.EVT_BUTTON, lambda e: self.anadir())
        self.botones["editar"].Bind(wx.EVT_BUTTON, lambda e: self.editar())
        self.botones["duplicar"].Bind(wx.EVT_BUTTON, lambda e: self.duplicar())
        self.botones["borrar"].Bind(wx.EVT_BUTTON, lambda e: self.borrar())
        self.botones["subir"].Bind(wx.EVT_BUTTON, lambda e: self.mover(-1))
        self.botones["bajar"].Bind(wx.EVT_BUTTON, lambda e: self.mover(1))
        self.lista.Bind(wx.EVT_LISTBOX_DCLICK, lambda e: self.editar())
        self.lista.Bind(wx.EVT_KEY_DOWN, self._tecla)
        self.refrescar()

    def _tecla(self, ev):
        k = ev.GetKeyCode()
        if k in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and ev.GetModifiers() == wx.MOD_NONE:
            self.editar()
        elif k == wx.WXK_DELETE:
            self.borrar()
        else:
            ev.Skip()

    def fijar(self, nombre_esq, elementos):
        self.nombre_esq = nombre_esq
        self.elementos = elementos
        self.refrescar()

    def refrescar(self, seleccion=None):
        textos = [modelo.resumen(self.nombre_esq, d) for d in self.elementos]
        self.lista.Set(textos or [])
        if textos:
            sel = 0 if seleccion is None else max(0, min(len(textos) - 1, seleccion))
            self.lista.SetSelection(sel)
        hay = bool(textos)
        for clave in ("editar", "duplicar", "borrar", "subir", "bajar"):
            self.botones[clave].Enable(hay)

    def _sel(self):
        s = self.lista.GetSelection()
        return s if 0 <= s < len(self.elementos) else None

    def _cambio(self, seleccion):
        self.refrescar(seleccion)
        self.lista.SetFocus()
        if self.al_cambiar:
            self.al_cambiar()

    def _formulario(self, datos, titulo):
        dlg = DialogoFormulario(wx.GetTopLevelParent(self), self.nombre_esq, datos, self.cat, self.mod, titulo)
        try:
            return dlg.datos if dlg.ShowModal() == wx.ID_OK else None
        finally:
            dlg.Destroy()

    def anadir(self):
        nuevo = self._formulario(modelo.nuevo_elemento(self.nombre_esq), tr("Nuevo: ") + ESQUEMAS[self.nombre_esq]["titulo"].lower())
        if nuevo is not None:
            self.elementos.append(nuevo)
            self._cambio(len(self.elementos) - 1)
        else:
            self.lista.SetFocus()

    def editar(self):
        s = self._sel()
        if s is None:
            return
        cambiado = self._formulario(self.elementos[s], tr("Editar: ") + modelo.resumen(self.nombre_esq, self.elementos[s]))
        if cambiado is not None:
            self.elementos[s] = cambiado
            self._cambio(s)
        else:
            self.lista.SetFocus()

    def duplicar(self):
        s = self._sel()
        if s is None:
            return
        copia = copy.deepcopy(self.elementos[s])
        if copia.get("id"):
            copia["id"] = str(copia["id"]) + "_copia"
        self.elementos.insert(s + 1, copia)
        self._cambio(s + 1)

    def borrar(self):
        s = self._sel()
        if s is None:
            return
        if confirmar(wx.GetTopLevelParent(self), tr('¿Borrar «{resumen}»?').format(resumen=(modelo.resumen(self.nombre_esq, self.elementos[s]))), tr("Borrar"), peligroso=True) == wx.ID_YES:
            del self.elementos[s]
            self._cambio(s)
        else:
            self.lista.SetFocus()

    def mover(self, delta):
        s = self._sel()
        if s is None or not (0 <= s + delta < len(self.elementos)):
            return
        self.elementos[s], self.elementos[s + delta] = self.elementos[s + delta], self.elementos[s]
        self._cambio(s + delta)


class DialogoLista(wx.Dialog):
    """Edita una lista anidada (pasos de una misión, frases de un diálogo, enemigos...)."""

    def __init__(self, padre, titulo, nombre_esq, elementos, cat, mod):
        super().__init__(padre, title=titulo, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, name=titulo)
        self.elementos = copy.deepcopy(elementos)
        usadas = {letra_de(tr("&Aceptar")), letra_de(tr("&Cancelar"))}
        marco = wx.BoxSizer(wx.VERTICAL)
        self.panel = PanelElementos(self, nombre_esq, self.elementos, cat, mod, usadas=usadas)
        marco.Add(self.panel, 1, wx.EXPAND | wx.ALL, 5)
        marco.Add(crear_botonera(self, wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizerAndFit(marco)
        preparar_dialogo(self, foco_inicial=self.panel.lista)
        self.CentreOnParent()


class DialogoFormulario(wx.Dialog):
    """Formulario de un elemento, construido a partir de su esquema."""

    def __init__(self, padre, nombre_esq, datos, cat, mod, titulo=None):
        esq = ESQUEMAS[nombre_esq]
        super().__init__(padre, title=titulo or esq["titulo"], style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, name=titulo or esq["titulo"])
        self.nombre_esq = nombre_esq
        self.esq = esq
        self.datos = copy.deepcopy(datos)
        self.cat = cat
        self.mod = mod
        self.lectores = {}
        self.controles = {}
        self.cuerpo = None
        self.marco = wx.BoxSizer(wx.VERTICAL)
        self.zona = wx.BoxSizer(wx.VERTICAL)
        self.marco.Add(self.zona, 1, wx.EXPAND)
        self.marco.Add(crear_botonera(self, wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizer(self.marco)
        self._construir()
        self.Bind(wx.EVT_BUTTON, self._aceptar, id=wx.ID_OK)
        preparar_dialogo(self)
        self.CentreOnParent()

    # ------------------------------------------------------------ construcción
    def _visibles(self):
        return [cp for cp in self.esq["campos"] if cp.get("si") is None or cp["si"](self.datos)]

    def _construir(self, foco=None):
        self.Freeze()
        try:
            if self.cuerpo is not None:
                self.zona.Detach(self.cuerpo)
                self.cuerpo.Destroy()
            self.lectores = {}
            self.controles = {}
            visibles = self._visibles()
            grupos = []
            for cp in visibles:
                g = cp.get("grupo", tr("General"))
                if g not in grupos:
                    grupos.append(g)
            reparto = [(g, [cp for cp in visibles if cp.get("grupo", tr("General")) == g]) for g in grupos]
            if len(grupos) == 1 and len(visibles) > 11:
                # formulario largo sin pestañas definidas: se reparte para que cada página tenga pocas letras de acceso
                reparto = [(tr("General") if n == 0 else tr("Más datos") if n == 10 else tr('Más datos, {v}').format(v=(n // 10)), visibles[n:n + 10]) for n in range(0, len(visibles), 10)]
            if len(reparto) > 1:
                self.cuerpo = wx.Notebook(self)
                for g, campos in reparto:
                    self.cuerpo.AddPage(self._pagina(self.cuerpo, campos), g)
            else:
                self.cuerpo = self._pagina(self, visibles)
            self.zona.Add(self.cuerpo, 1, wx.EXPAND | wx.ALL, 5)
            # la botonera tiene que ir detrás de los campos en el orden de tabulación
            for hijo in self.GetChildren():
                if isinstance(hijo, wx.Button):
                    hijo.MoveAfterInTabOrder(self.cuerpo)
            self.Layout()
            alto = min(720, self.marco.GetMinSize().height + 60)
            self.SetSize((640, max(260, alto)))
        finally:
            self.Thaw()
        destino = self.controles.get(foco) if foco else None
        if destino is None and self.controles:
            destino = next(iter(self.controles.values()))
        if destino is not None:
            wx.CallAfter(self._enfocar, destino)

    def _enfocar(self, control):
        try:
            enfocar(control)
        except RuntimeError:
            pass

    def _pagina(self, padre, campos):
        panel = wx.ScrolledWindow(padre, style=wx.TAB_TRAVERSAL)
        panel.SetScrollRate(0, 20)
        sizer = wx.BoxSizer(wx.VERTICAL)
        usadas = {letra_de(tr("&Aceptar")), letra_de(tr("&Cancelar"))}       # las de Aceptar y Cancelar, en el idioma que sea
        for cp in campos:
            self._campo(panel, sizer, cp, usadas)
        panel.SetSizer(sizer)
        return panel

    def _opciones(self, cp):
        if cp["t"] in ("opcion",):
            return list(cp["ops"])
        return self.cat.opciones(cp["ref"], self.mod)

    def _campo(self, panel, sizer, cp, usadas):
        k, t = cp["k"], cp["t"]
        v = self.datos.get(k)
        ayuda = cp.get("ayuda") or ""
        if cp.get("req"):
            ayuda = (ayuda + tr(" Obligatorio.")).strip()
        etq = con_letra(cp["e"], usadas)
        if t in ("texto", "largo", "textos", "entero", "decimal"):
            if t == "textos":
                valor = "\n".join(str(x) for x in (v or []))
            elif t in ("entero", "decimal"):
                valor = _texto_numero(v)
            else:
                valor = "" if v is None else str(v)
            estilo = wx.TE_MULTILINE if t in ("largo", "textos") else 0
            _, ctrl = crear_campo(panel, etq + ":", wx.TextCtrl, value=valor, style=estilo, size=(560, 90 if estilo else -1), ayuda=ayuda, sizer=sizer)
            if t == "textos":
                self.lectores[k] = lambda c=ctrl: [x.strip() for x in c.GetValue().splitlines() if x.strip()]
            elif t in ("entero", "decimal"):
                self.lectores[k] = lambda c=ctrl, dec=(t == "decimal"): _numero(c.GetValue(), dec)
            else:
                self.lectores[k] = lambda c=ctrl: c.GetValue().strip()
        elif t == "si_no":
            ctrl = wx.CheckBox(panel, label=etq)
            ctrl.SetValue(bool(v) if v is not None else bool(cp.get("defecto", False)))
            ctrl.SetHelpText(ayuda or tr("Casilla de verificación. Espacio la marca o la desmarca."))
            sizer.Add(ctrl, 0, wx.ALL, 5)
            self.lectores[k] = lambda c=ctrl: bool(c.GetValue())
        elif t in ("opcion", "ref"):
            ops = self._opciones(cp)
            valores = [o[0] for o in ops]
            textos = [o[1] for o in ops]
            if not cp.get("req"):
                valores.insert(0, None)
                textos.insert(0, SIN_VALOR)
            if v not in (None, "") and v not in valores:
                valores.append(v)
                textos.append(tr('{v}, no existe').format(v=(v)))
            _, ctrl = crear_campo(panel, etq + ":", wx.Choice, choices=textos, ayuda=ayuda, sizer=sizer)
            ctrl.SetSelection(valores.index(v) if v in valores else 0)
            self.lectores[k] = lambda c=ctrl, vs=valores: vs[c.GetSelection()] if 0 <= c.GetSelection() < len(vs) else None
            if cp.get("recarga"):
                ctrl.Bind(wx.EVT_CHOICE, lambda e, clave=k: wx.CallAfter(self._recargar, clave))
        elif t == "refs":
            ops = self._opciones(cp)
            valores = [o[0] for o in ops]
            _, ctrl = crear_campo(panel, etq + ":", wx.CheckListBox, choices=[o[1] for o in ops], size=(560, 110),
                                  ayuda=(ayuda + tr(" Lista de casillas: Espacio marca o desmarca cada una.")).strip(), sizer=sizer)
            ctrl.SetCheckedItems([valores.index(x) for x in (v or []) if x in valores])
            if valores:
                ctrl.SetSelection(0)
            self.lectores[k] = lambda c=ctrl, vs=valores: [vs[i] for i in c.GetCheckedItems()]
        elif t == "par":
            par = v if isinstance(v, (list, tuple)) and len(v) == 2 else (None, None)
            nombres = cp.get("etiquetas", (cp["e"] + tr(", primero"), cp["e"] + tr(", segundo")))
            ctrls = []
            for n, nombre in enumerate(nombres):
                _, c1 = crear_campo(panel, con_letra(nombre, usadas) + ":", wx.TextCtrl, value=_texto_numero(par[n]), ayuda=ayuda, sizer=sizer)
                ctrls.append(c1)
            ctrl = ctrls[0]
            dec = bool(cp.get("decimal"))

            def leer(cs=ctrls, dec=dec):
                a, b = _numero(cs[0].GetValue(), dec), _numero(cs[1].GetValue(), dec)
                if a is None and b is None:
                    return None
                if a is None or b is None:
                    raise ValueError
                return [a, b]
            self.lectores[k] = leer
        elif t in ("lista", "objeto"):
            ctrl = wx.Button(panel, label=self._texto_boton(cp, etq))
            ctrl.SetHelpText((ayuda + tr(" Pulsa Intro para abrirlo.")).strip())
            ctrl.Bind(wx.EVT_BUTTON, lambda e, c=cp, b=ctrl, et=etq: self._abrir(c, b, et))
            sizer.Add(ctrl, 0, wx.ALL, 5)
            self.lectores[k] = lambda clave=k: self.datos.get(clave)
        else:
            return
        self.controles[k] = ctrl

    def _texto_boton(self, cp, etq):
        v = self.datos.get(cp["k"])
        if cp["t"] == "lista":
            n = len(v or [])
            return f"{etq}: {tr('vacío') if n == 0 else tr('1 elemento') if n == 1 else tr('{n} elementos').format(n=(n))}..."
        return f"{etq}: {tr('sin definir') if not v else 'definido'}..."

    def _abrir(self, cp, boton, etq):
        k = cp["k"]
        if cp["t"] == "lista":
            dlg = DialogoLista(self, cp["e"], cp["sub"], self.datos.get(k) or [], self.cat, self.mod)
            if dlg.ShowModal() == wx.ID_OK:
                self.datos[k] = dlg.elementos
            dlg.Destroy()
        else:
            dlg = DialogoFormulario(self, cp["sub"], self.datos.get(k) or modelo.nuevo_elemento(cp["sub"]), self.cat, self.mod, cp["e"])
            if dlg.ShowModal() == wx.ID_OK:
                self.datos[k] = dlg.datos
            dlg.Destroy()
        boton.SetLabel(self._texto_boton(cp, etq))
        boton.SetFocus()

    # ------------------------------------------------------------------ datos
    def _recoger(self, estricto):
        """Pasa los controles a self.datos. Devuelve (clave, mensaje) del primer error, o None."""
        error = None
        for cp in self._visibles():
            k = cp["k"]
            if k not in self.lectores:
                continue
            try:
                v = self.lectores[k]()
            except ValueError:
                if error is None:
                    error = (k, tr('«{e}» tiene que ser un número').format(e=(cp['e'])) + ("." if cp["t"] != "par" else tr(", y hay que rellenar los dos valores o ninguno.")))
                continue
            if v in modelo.VACIOS:
                self.datos.pop(k, None)
                if estricto and cp.get("req") and error is None:
                    error = (k, tr('Falta «{e}».').format(e=(cp['e'])))
            else:
                self.datos[k] = v
                if estricto and isinstance(v, (int, float)) and not isinstance(v, bool) and error is None:
                    if "minimo" in cp and v < cp["minimo"]:
                        error = (k, tr('«{e}» no puede ser menor que {minimo}.').format(e=(cp['e']), minimo=(cp['minimo'])))
                    elif "maximo" in cp and v > cp["maximo"]:
                        error = (k, tr('«{e}» no puede ser mayor que {maximo}.').format(e=(cp['e']), maximo=(cp['maximo'])))
        return error

    def _recargar(self, clave):
        """Al cambiar un campo del que dependen otros (el tipo), se reconstruye el formulario."""
        self._recoger(False)
        self._construir(foco=clave)

    def _aceptar(self, evento):
        error = self._recoger(True)
        if error:
            k, mensaje = error
            mostrar_error(self, mensaje, tr("Revisa el formulario"))
            ctrl = self.controles.get(k)
            if ctrl is not None:
                if isinstance(self.cuerpo, wx.Notebook):
                    for n in range(self.cuerpo.GetPageCount()):
                        if ctrl.GetParent() is self.cuerpo.GetPage(n):
                            self.cuerpo.SetSelection(n)
                enfocar(ctrl)
            return
        visibles = {cp["k"] for cp in self._visibles()}
        for cp in self.esq["campos"]:
            if cp["k"] not in visibles:
                self.datos.pop(cp["k"], None)       # campos de otro tipo que ya no proceden
        self.EndModal(wx.ID_OK)
