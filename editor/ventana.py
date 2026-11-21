"""Ventana principal del editor de mods."""
from juego.i18n import tr
import copy
import os
import subprocess
import sys

import wx

from juego import NOMBRE, VERSION, rutas

from . import modelo
from .accesibilidad.ayuda import habilitar_ayuda_contextual
from .accesibilidad.dialogos import confirmar, crear_botonera, mostrar_error, mostrar_mensaje, preparar_dialogo
from .accesibilidad.nombres import crear_campo
from .esquema import ESQUEMAS, SECCIONES
from .formulario import DialogoFormulario, PanelElementos, con_letra


class DialogoActivar(wx.Dialog):
    """Activa o desactiva los mods de la carpeta data/mods."""

    def __init__(self, padre):
        super().__init__(padre, title=tr("Activar o desactivar mods"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, name=tr("Activar o desactivar mods"))
        self.mods = modelo.listar_mods()
        sizer = wx.BoxSizer(wx.VERTICAL)
        _, self.lista = crear_campo(self, tr("&Mods de la carpeta data, mods:"), wx.CheckListBox, choices=[m[0] for m in self.mods], size=(480, 220),
                                    ayuda=tr("Marca los mods que quieres que cargue el juego. Los desmarcados se conservan, pero el juego no los lee."), sizer=sizer)
        self.lista.SetCheckedItems([i for i, m in enumerate(self.mods) if m[1]])
        if self.mods:
            self.lista.SetSelection(0)
        sizer.Add(crear_botonera(self, wx.OK | wx.CANCEL), 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizerAndFit(sizer)
        preparar_dialogo(self, foco_inicial=self.lista)
        self.CentreOnParent()

    def aplicar(self):
        marcados = set(self.lista.GetCheckedItems())
        for i, (nombre, activo) in enumerate(self.mods):
            if (i in marcados) != activo:
                modelo.activar_mod(nombre, i in marcados)


class VentanaEditor(wx.Frame):
    def __init__(self):
        super().__init__(None, title=tr("Editor de mods"), size=(760, 620), name=tr("Editor de mods"))
        self.cat = modelo.Catalogo()
        self.mod = modelo.Mod()
        self._menus()
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        from .formulario import letra_de
        usadas = {letra_de(tr(t)) for t in (tr("&Archivo"), tr("&Mod"), tr("A&yuda"))}     # letras de los menús Archivo, Mod y Ayuda, en el idioma que sea
        _, self.secciones = crear_campo(panel, con_letra(tr("Secciones"), usadas) + ":", wx.ListBox, choices=[t for _, t, _ in SECCIONES], style=wx.LB_SINGLE, size=(700, 150),
                                        ayuda=tr("Elige qué parte del mod quieres editar. Al cambiar de sección cambia la lista de elementos de abajo."), sizer=sizer)
        self.secciones.SetSelection(0)
        clave, _, esq = SECCIONES[0]
        self.panel_elementos = PanelElementos(panel, esq, self.mod.secciones[clave], self.cat, self.mod, al_cambiar=self._cambiado, usadas=usadas,
                                              etiqueta=tr("Elementos de la sección"),
                                              extra=(("original", tr("Copiar del juego original"), tr("Copia al mod un elemento del juego para modificarlo. Con el mismo identificador, sustituye al original.")),))
        self.panel_elementos.botones["original"].Bind(wx.EVT_BUTTON, lambda e: self.copiar_original())
        sizer.Add(self.panel_elementos, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        self.CreateStatusBar()
        self.secciones.Bind(wx.EVT_LISTBOX, lambda e: self._seccion())
        self.Bind(wx.EVT_CLOSE, self._cerrar)
        habilitar_ayuda_contextual(self)
        self._titulo()
        self.Centre()
        self.secciones.SetFocus()

    # ------------------------------------------------------------------ menús
    def _menus(self):
        barra = wx.MenuBar()
        archivo = wx.Menu()
        self._item(archivo, tr("&Nuevo mod\tCtrl+N"), tr("Empieza un mod vacío."), self.nuevo)
        self._item(archivo, tr("&Abrir mod...\tCtrl+O"), tr("Abre un mod de la carpeta de mods."), self.abrir)
        self._item(archivo, tr("&Guardar\tCtrl+S"), tr("Guarda el mod."), self.guardar)
        self._item(archivo, tr("Guardar &como...\tCtrl+Shift+S"), tr("Guarda el mod con otro nombre."), self.guardar_como)
        archivo.AppendSeparator()
        self._item(archivo, tr("&Salir\tCtrl+Q"), tr("Cierra el editor."), lambda: self.Close())
        barra.Append(archivo, tr("&Archivo"))
        mod = wx.Menu()
        self._item(mod, tr("&Datos del mod...\tCtrl+D"), tr("Nombre, autor, versión y descripción."), self.datos_mod)
        self._item(mod, tr("&Comprobar el mod\tF5"), tr("Busca errores: referencias que no existen, posiciones imposibles, pasos incoherentes."), self.comprobar)
        self._item(mod, tr("&Activar o desactivar mods...\tCtrl+M"), tr("Elige qué mods carga el juego."), self.activar)
        self._item(mod, tr("A&brir la carpeta de mods\tCtrl+B"), tr("Abre la carpeta en el Explorador."), self.carpeta)
        self._item(mod, tr("&Guion de voces para grabar\tCtrl+G"), tr("Escribe un texto con todas las frases de las misiones y el nombre de archivo de cada grabación."), self.guion_voces)
        self._item(mod, tr("Abrir la carpeta de &voces\tCtrl+Shift+V"), tr("Abre la carpeta donde se dejan las grabaciones."), self.carpeta_voces)
        self._item(mod, tr("&Probar en el juego\tF9"), tr("Guarda el mod y abre el juego."), self.probar)
        barra.Append(mod, tr("&Mod"))
        ayuda = wx.Menu()
        self._item(ayuda, tr("&Manual del editor\tF1"), tr("Abre el manual en el navegador."), self.manual)
        self._item(ayuda, tr("&Invítame a un café si te gusta mi trabajo"), tr("Abre la página de donaciones de PayPal en el navegador."), self.cafe)
        self._item(ayuda, tr("&Acerca de..."), tr("Versión del editor, autor y licencia."), self.acerca)
        barra.Append(ayuda, tr("A&yuda"))
        self.SetMenuBar(barra)

    def _item(self, menu, texto, ayuda, accion):
        item = menu.Append(wx.ID_ANY, texto, ayuda)
        self.Bind(wx.EVT_MENU, lambda e: accion(), item)

    # ----------------------------------------------------------------- estado
    def _titulo(self):
        nombre = os.path.basename(self.mod.ruta) if self.mod.ruta else tr("mod sin guardar")
        self.SetTitle(tr('{v}{get} ({nombre}) - Editor de mods').format(v=('* ' if self.mod.modificado else ''), get=(self.mod.info.get('nombre', tr('Mod'))), nombre=(nombre)))
        total = sum(len(v) for v in self.mod.secciones.values())
        self.SetStatusText(tr('{total} elementos en el mod').format(total=(total)) + (tr(". Hay cambios sin guardar") if self.mod.modificado else ""))

    def _cambiado(self):
        self.mod.modificado = True
        self._titulo()

    def _seccion(self):
        i = self.secciones.GetSelection()
        if i < 0:
            return
        clave, _, esq = SECCIONES[i]
        self.panel_elementos.fijar(esq, self.mod.secciones[clave])

    def _descartar(self):
        """True si se puede seguir (no hay cambios, o se han guardado o descartado)."""
        if not self.mod.modificado:
            return True
        r = confirmar(self, tr("Hay cambios sin guardar. ¿Quieres guardarlos?"), tr("Cambios sin guardar"), con_cancelar=True)
        if r == wx.ID_YES:
            return self.guardar()
        return r == wx.ID_NO

    def _cargar_en_ventana(self, mod):
        self.mod = mod
        self.panel_elementos.mod = mod
        self._seccion()
        self._titulo()

    # ---------------------------------------------------------------- archivo
    def nuevo(self):
        if self._descartar():
            self._cargar_en_ventana(modelo.Mod())

    def abrir(self):
        if not self._descartar():
            return
        os.makedirs(rutas.MODS, exist_ok=True)
        with wx.FileDialog(self, tr("Abrir mod"), defaultDir=rutas.MODS, wildcard=tr("Mods (*.pbm;*.json;*.desactivado)|*.pbm;*.json;*.desactivado|Todos los archivos|*.*"),
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            ruta = dlg.GetPath()
        try:
            self._cargar_en_ventana(modelo.Mod.cargar(ruta))
        except Exception as e:
            mostrar_error(self, tr('No se pudo abrir el mod.\n{e}').format(e=(e)), tr("Error al abrir"))

    def guardar(self):
        if not self.mod.ruta:
            return self.guardar_como()
        try:
            apartado = self.mod.guardar()
        except OSError as e:
            mostrar_error(self, tr('No se pudo guardar.\n{e}').format(e=(e)), tr("Error al guardar"))
            return False
        self._titulo()
        self.SetStatusText(tr("Mod guardado y protegido en ") + self.mod.ruta)
        if apartado:
            mostrar_mensaje(self, tr('El mod se ha guardado protegido, con extensión pbm, que es la que usa el juego.\n\nEl archivo escrito a mano se conserva como {basename} y el juego ya no lo carga.').format(basename=(os.path.basename(apartado))), tr("Mod protegido"))
        return True

    def guardar_como(self):
        os.makedirs(rutas.MODS, exist_ok=True)
        propuesto = "".join(ch if ch.isalnum() else "_" for ch in self.mod.info.get("nombre", "mi_mod").lower()).strip("_") or "mi_mod"
        with wx.FileDialog(self, tr("Guardar mod"), defaultDir=rutas.MODS, defaultFile=propuesto + rutas.EXT_MOD, wildcard=tr("Mods protegidos (*.pbm)|*.pbm"),
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return False
            ruta = dlg.GetPath()
        self.mod.ruta = modelo.ruta_protegida(ruta)
        return self.guardar()

    def _cerrar(self, evento):
        if evento.CanVeto() and not self._descartar():
            evento.Veto()
            return
        self.Destroy()

    # -------------------------------------------------------------------- mod
    def datos_mod(self):
        dlg = DialogoFormulario(self, "info", self.mod.info, self.cat, self.mod)
        if dlg.ShowModal() == wx.ID_OK:
            self.mod.info = dlg.datos
            self._cambiado()
        dlg.Destroy()

    def comprobar(self):
        errores, avisos = modelo.comprobar(self.mod, self.cat)
        if not errores and not avisos:
            mostrar_mensaje(self, tr("No se ha encontrado ningún problema. El mod está listo para probarlo en el juego."), tr("Comprobación"))
            return True
        texto = []
        if errores:
            texto.append(tr('{len} errores que hay que corregir:').format(len=(len(errores))))
            texto += [f"{n}. {e}" for n, e in enumerate(errores, 1)]
        if avisos:
            texto.append("")
            texto.append(tr('{len} avisos, que conviene revisar:').format(len=(len(avisos))))
            texto += [f"{n}. {e}" for n, e in enumerate(avisos, 1)]
        mostrar_mensaje(self, "\n".join(texto), tr("Comprobación"), icono=wx.ICON_WARNING)
        return not errores

    def activar(self):
        dlg = DialogoActivar(self)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                dlg.aplicar()
            except OSError as e:
                mostrar_error(self, tr('No se pudo cambiar el estado de un mod.\n{e}').format(e=(e)))
        dlg.Destroy()

    def carpeta(self):
        os.makedirs(rutas.MODS, exist_ok=True)
        os.startfile(rutas.MODS)

    def guion_voces(self):
        from juego import voces
        misiones = self.mod.crudo().get("misiones", [])
        if not any(p.get("tipo") == "dialogo" for m in misiones for p in m.get("pasos", [])):
            mostrar_mensaje(self, tr("Este mod no tiene misiones con diálogos, así que no hay nada que grabar."), tr("Guion de voces"))
            return
        os.makedirs(voces.carpeta(), exist_ok=True)
        voces.refrescar()
        nombre = "guion_" + (os.path.splitext(os.path.basename(self.mod.ruta))[0] if self.mod.ruta else "mod_sin_guardar") + ".txt"
        ruta = os.path.join(voces.carpeta(), nombre)
        try:
            with open(ruta, "w", encoding="utf-8-sig", newline="\r\n") as f:
                f.write(voces.guion(misiones, self.mod.info.get("nombre", "")))
        except OSError as e:
            mostrar_error(self, tr('No se pudo escribir el guion.\n{e}').format(e=(e)))
            return
        mostrar_mensaje(self, tr('Guion escrito en la carpeta de voces, con el nombre {nombre}. Se abre ahora en el Bloc de notas.\n\nCada frase lleva encima el nombre que debe tener su grabación. Deja las grabaciones en esa misma carpeta.').format(nombre=(nombre)), tr("Guion de voces"))
        os.startfile(ruta)

    def carpeta_voces(self):
        from juego import voces
        os.makedirs(voces.carpeta(), exist_ok=True)
        os.startfile(voces.carpeta())

    def probar(self):
        if not self.guardar():
            return
        if not self.comprobar():
            return
        exe = os.path.join(rutas.base(), "PuertoBravo.exe")
        try:
            if getattr(sys, "frozen", False) and os.path.exists(exe):
                subprocess.Popen([exe], cwd=rutas.base())
            else:
                subprocess.Popen([sys.executable.replace("python.exe", "pythonw.exe"), os.path.join(rutas.base(), "main.py")], cwd=rutas.base())
        except OSError as e:
            mostrar_error(self, tr('No se pudo abrir el juego.\n{e}').format(e=(e)))

    def copiar_original(self):
        i = self.secciones.GetSelection()
        clave, titulo, esq = SECCIONES[i]
        originales = self.cat.elementos_base(clave)
        if not originales:
            mostrar_mensaje(self, tr("El juego original no tiene elementos en esta sección."), tr("Copiar del juego original"))
            return
        editables = [x if clave == "capitulos" else modelo.desempaquetar(esq, x) for x in originales]
        textos = [modelo.resumen(esq, d) for d in editables]
        orden = sorted(range(len(textos)), key=lambda n: textos[n].lower())
        with wx.SingleChoiceDialog(self, tr('Elige qué copiar de {lower}. Con el mismo identificador, tu versión sustituirá a la original.').format(lower=(titulo.lower())),
                                   tr("Copiar del juego original"), [textos[n] for n in orden]) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            elegido = editables[orden[dlg.GetSelection()]]
        self.mod.secciones[clave].append(copy.deepcopy(elegido))
        self._cambiado()
        self.panel_elementos.refrescar(len(self.mod.secciones[clave]) - 1)
        self.panel_elementos.lista.SetFocus()

    # ------------------------------------------------------------------ ayuda
    def manual(self):
        from juego import i18n
        ruta = i18n.doc("editor_mods")
        try:
            os.startfile(ruta)
        except OSError:
            mostrar_error(self, tr("No se encontró el manual del editor. Debería estar en data, docs, editor_mods_es.html."))

    def cafe(self):
        from juego import CAFE
        os.startfile(CAFE)

    def acerca(self):
        from juego import ANIO, AUTOR
        mostrar_mensaje(self, tr('Editor de mods de {NOMBRE}, versión {VERSION}.\n\nHecho por {AUTOR}.\nCopyright {ANIO}, {AUTOR}. Software libre con licencia MIT.\n\nCrea lugares, misiones, armas, vehículos, carreras, localidades enteras y todo el contenido del juego sin escribir código.\n\nCtrl+H explica el control en el que estás. F5 comprueba el mod. F9 lo prueba en el juego.').format(NOMBRE=(NOMBRE), VERSION=(VERSION), AUTOR=(AUTOR), ANIO=(ANIO)), tr("Acerca del editor"))


def ejecutar():
    app = wx.App(False)
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    try:
        from .accesibilidad import idioma
        app._idioma = idioma.fijar_idioma_espanol()
    except Exception:
        pass
    ventana = VentanaEditor()
    ventana.Show()
    app.MainLoop()
