"""Revisión del teclado de una pantalla: etiquetas, letras de acceso y atajos.

Recorre una ventana o diálogo YA CONSTRUIDO (no hace falta mostrarlo) y
comprueba que todo se puede manejar con teclado sin choques:

- Cada control que toma el nombre de su etiqueta (campo de texto, lista,
  desplegable, deslizador...) tiene una ``wx.StaticText`` creada justo antes,
  con el mismo padre, y esa etiqueta tiene letra de acceso (``&``).
- Botones, casillas y botones de opción tienen letra de acceso.
- Ninguna letra de acceso se repite en lo que se ve a la vez: la ventana y,
  si hay pestañas, cada página junto con lo que está fuera del cuaderno.
- Ninguna letra de acceso coincide con la de un menú de la barra de menús
  (Alt+A no puede abrir a la vez «&Archivo» y el campo «&Apellidos»).
- Dentro de cada menú y submenú las letras no se repiten y todos los
  elementos tienen la suya.
- Ningún atajo (``Ctrl+S``, ``F5``...) se repite entre menús, tablas de
  aceleradores (``instalar_atajos``) y teclas atendidas a mano.
- Ningún atajo usa teclas reservadas: Ctrl+H (ayuda contextual), F10 y
  Mayús+F10, Alt+F4, Alt+Espacio, Insert o Bloq Mayús (teclas del lector),
  Ctrl+Tab si hay pestañas y Ctrl+1 a Ctrl+0 si hay una ``ListaAccesible``.
- Cada botón de la barra de herramientas tiene un elemento de menú o un
  atajo con el mismo id (las barras de herramientas no están en el Tab).
- Aviso: Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+Z o Ctrl+Y en un menú se
  adelantan a los campos de texto; su acción debe pasarle la orden al campo
  enfocado.

Uso en una prueba del proyecto::

	from editor.accesibilidad.revision_teclado import afirmar_teclado_correcto

	def test_teclado_de_preferencias(app_wx):
		dialogo = DialogoPreferencias(None, configuracion)
		try:
			afirmar_teclado_correcto(dialogo, teclas_propias=["Ctrl+F"])
		finally:
			dialogo.Destroy()

``teclas_propias`` son las teclas que la ventana atiende a mano en
``EVT_CHAR_HOOK`` o ``EVT_KEY_DOWN`` (la revisión no puede deducirlas).

Lo que NO comprueba: el orden de Tab, lo que dice el lector de pantalla
(pruebas MSAA y comprobación con NVDA) ni las ventanas que se crean después.
Revise cada diálogo por separado.

PLANTILLA del agente «accesibilidad-wx».
"""

from __future__ import annotations

from juego.i18n import tr
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import wx

# Códigos de problema (estables: sirven para ``ignorar``).
SIN_ETIQUETA = "sin-etiqueta"
SIN_LETRA = "sin-letra"
LETRA_REPETIDA = "letra-repetida"
CHOCA_CON_MENU = "choca-con-menu"
LETRA_SIN_DESTINO = "letra-sin-destino"
LETRA_DIFICIL = "letra-dificil"
ATAJO_REPETIDO = "atajo-repetido"
ATAJO_RESERVADO = "atajo-reservado"
SIN_TECLADO = "sin-teclado"
ATAJO_EDICION = "atajo-edicion"

#: Controles que toman el nombre accesible de la ``wx.StaticText`` creada justo antes.
NECESITAN_ETIQUETA: tuple[type, ...] = (
	wx.TextCtrl, wx.Choice, wx.ComboBox, wx.ListBox, wx.ListCtrl, wx.TreeCtrl,
	wx.Slider, wx.SpinCtrl, wx.SpinCtrlDouble, wx.SearchCtrl, wx.PickerBase,
)
#: Controles con texto propio en el que va la letra de acceso.
CON_TEXTO_PROPIO: tuple[type, ...] = (wx.Button, wx.ToggleButton, wx.CheckBox, wx.RadioButton)
#: Ventanas que solo agrupan otras: se recorren por dentro.
CONTENEDORES: tuple[type, ...] = (wx.Panel, wx.StaticBox, wx.BookCtrlBase, wx.SplitterWindow, wx.CollapsiblePane)
#: Ventanas que nunca reciben el foco (una letra de acceso en ellas no lleva a ningún sitio).
SIN_FOCO: tuple[type, ...] = (wx.StaticText, wx.StaticLine, wx.StaticBitmap, wx.Gauge)

#: Letras que se pueden pulsar con Alt en un teclado español sin combinaciones raras.
LETRAS_FACILES = set("abcdefghijklmnopqrstuvwxyzñç0123456789")

_TECLAS_EDICION = {tr("Ctrl+A"), tr("Ctrl+C"), tr("Ctrl+V"), tr("Ctrl+X"), tr("Ctrl+Z"), tr("Ctrl+Y")}

_NOMBRES_TECLA = {
	wx.WXK_ESCAPE: tr("Escape"), wx.WXK_RETURN: tr("Intro"), wx.WXK_NUMPAD_ENTER: tr("Intro"),
	wx.WXK_DELETE: tr("Supr"), wx.WXK_INSERT: tr("Insert"), wx.WXK_SPACE: tr("Espacio"),
	wx.WXK_TAB: tr("Tab"), wx.WXK_BACK: tr("Retroceso"), wx.WXK_HOME: tr("Inicio"),
	wx.WXK_END: tr("Fin"), wx.WXK_PAGEUP: tr("Re Pág"), wx.WXK_PAGEDOWN: tr("Av Pág"),
	wx.WXK_UP: tr("Arriba"), wx.WXK_DOWN: tr("Abajo"), wx.WXK_LEFT: tr("Izquierda"),
	wx.WXK_RIGHT: tr("Derecha"), wx.WXK_CAPITAL: tr("Bloq Mayús"),
}
_NOMBRES_MODIFICADOR = {
	"ctrl": tr("Ctrl"), "control": tr("Ctrl"), "alt": tr("Alt"), "mayús": tr("Mayús"), "mayus": tr("Mayús"),
	"shift": tr("Mayús"), "mayúsculas": tr("Mayús"),
}
_ALIAS_TECLA = {
	"esc": tr("Escape"), "escape": tr("Escape"), "enter": tr("Intro"), "intro": tr("Intro"), "return": tr("Intro"),
	"del": tr("Supr"), "delete": tr("Supr"), "supr": tr("Supr"), "ins": tr("Insert"), "insert": tr("Insert"),
	"space": tr("Espacio"), "espacio": tr("Espacio"), "tab": tr("Tab"), "back": tr("Retroceso"),
	"retroceso": tr("Retroceso"), "home": tr("Inicio"), "inicio": tr("Inicio"), "end": tr("Fin"), "fin": tr("Fin"),
	"pgup": tr("Re Pág"), "re pág": tr("Re Pág"), "pgdn": tr("Av Pág"), "av pág": tr("Av Pág"),
	"up": tr("Arriba"), "arriba": tr("Arriba"), "down": tr("Abajo"), "abajo": tr("Abajo"),
	"left": tr("Izquierda"), "izquierda": tr("Izquierda"), "right": tr("Derecha"), "derecha": tr("Derecha"),
}

#: Atajo → (motivo, palabra que lo permite en la etiqueta del menú). Ctrl+H
#: puede estar en un elemento «Ayuda del control enfocado», que es esa misma acción.
_RESERVADAS: dict[str, tuple[str, str]] = {
	"Ctrl+H": (tr("ayuda contextual del control enfocado"), "ayuda"),
	"F10": (tr("Windows la usa para ir a la barra de menús"), ""),
	"Mayús+F10": (tr("abre el menú contextual"), "contextual"),
	"Alt+F4": (tr("Windows la usa para cerrar la ventana"), ""),
	"Alt+Espacio": (tr("abre el menú de sistema de la ventana"), ""),
}


@dataclass(frozen=True)
class Problema:
	"""Un problema de teclado encontrado en la ventana."""

	codigo: str
	mensaje: str
	aviso: bool = False

	def __str__(self) -> str:
		return f"{tr('Aviso') if self.aviso else tr('Error')} ({self.codigo}): {self.mensaje}"


@dataclass(frozen=True)
class _Letra:
	letra: str
	origen: str
	paginas: tuple[tuple[int, int], ...]


# --- Utilidades puras (sin ventanas) ---------------------------------------

def letra_de_acceso(etiqueta: str) -> str | None:
	"""Letra que sigue al primer ``&`` (``&&`` es un «&» literal), en minúscula.

	«&Guardar» → «g»; «A&plicar» → «p»; «Pan && vino» → None.
	"""
	etiqueta = etiqueta.split("\t", 1)[0]
	posicion = 0
	while True:
		posicion = etiqueta.find("&", posicion)
		if posicion < 0 or posicion + 1 >= len(etiqueta):
			return None
		siguiente = etiqueta[posicion + 1]
		if siguiente == "&":
			posicion += 2
			continue
		return None if siguiente.isspace() else siguiente.lower()


def texto_visible(etiqueta: str) -> str:
	"""«&Guardar como...\\tCtrl+Mayús+S» → «Guardar como...»."""
	etiqueta = etiqueta.split("\t", 1)[0]
	return etiqueta.replace("&&", "\0").replace("&", "").replace("\0", "&").strip()


def normalizar_atajo(texto: str) -> str:
	"""Forma única de escribir un atajo: «ctrl+shift+s» → «Ctrl+Mayús+S».

	Admite nombres en español y en inglés. Orden fijo: Ctrl, Alt, Mayús.
	"""
	partes = [p.strip() for p in texto.replace(" + ", "+").split("+")]
	if len(partes) > 1 and partes[-1] == "" and partes[-2] == "":
		partes = [*partes[:-2], "+"]  # «Ctrl++»
	modificadores = set()
	for parte in partes[:-1]:
		modificadores.add(_NOMBRES_MODIFICADOR.get(parte.lower(), parte))
	tecla = _ALIAS_TECLA.get(partes[-1].lower(), partes[-1])
	if len(tecla) == 1 or (tecla[:1] in "fF" and tecla[1:].isdigit()):
		tecla = tecla.upper()
	orden = [m for m in (tr("Ctrl"), tr("Alt"), tr("Mayús")) if m in modificadores]
	return "+".join([*orden, tecla])


def atajo_de_entrada(banderas: int, codigo: int) -> str:
	"""Texto normalizado de una ``wx.AcceleratorEntry`` (banderas ``wx.ACCEL_*``)."""
	modificadores = []
	if banderas & wx.ACCEL_CTRL:
		modificadores.append(tr("Ctrl"))
	if banderas & wx.ACCEL_ALT:
		modificadores.append(tr("Alt"))
	if banderas & wx.ACCEL_SHIFT:
		modificadores.append(tr("Mayús"))
	if codigo in _NOMBRES_TECLA:
		tecla = _NOMBRES_TECLA[codigo]
	elif wx.WXK_F1 <= codigo <= wx.WXK_F24:
		tecla = f"F{codigo - wx.WXK_F1 + 1}"
	elif 32 < codigo < 256:
		tecla = chr(codigo).upper()
	else:
		tecla = tr('tecla {codigo}').format(codigo=(codigo))
	return "+".join([*modificadores, tecla])


def _compatibles(a: _Letra, b: _Letra) -> bool:
	"""Dos letras chocan si pueden verse a la vez: misma página en cada cuaderno común."""
	paginas_a = dict(a.paginas)
	return all(paginas_a.get(libro, pagina) == pagina for libro, pagina in b.paginas)


def _letra_dificil(letra: str) -> bool:
	return letra not in LETRAS_FACILES and unicodedata.category(letra).startswith("L")


# --- Recorrido de la ventana -------------------------------------------------

def _describir(control: wx.Window) -> str:
	"""«el botón «Guardar»», «la lista «Elementos»» (nombre tomado de su etiqueta)."""
	tipos = (
		(wx.Button, tr("el botón")), (wx.ToggleButton, tr("el botón de alternar")), (wx.CheckBox, tr("la casilla")),
		(wx.RadioButton, tr("el botón de opción")), (wx.RadioBox, tr("el grupo de opciones")),
		(wx.StaticBox, tr("el grupo")), (wx.StaticText, tr("la etiqueta")), (wx.TextCtrl, tr("el campo de texto")),
		(wx.ComboBox, tr("el cuadro combinado")), (wx.Choice, tr("el desplegable")), (wx.ListBox, tr("la lista")),
		(wx.ListCtrl, tr("la lista")), (wx.TreeCtrl, tr("el árbol")), (wx.Slider, tr("el deslizador")),
		(wx.SpinCtrl, tr("el campo numérico")), (wx.SpinCtrlDouble, tr("el campo numérico")),
		(wx.SearchCtrl, tr("el campo de búsqueda")), (wx.PickerBase, tr("el selector")),
	)
	tipo = next((nombre for clase, nombre in tipos if isinstance(control, clase)), tr('el control {__name__}').format(__name__=(type(control).__name__)))
	texto = ""
	if isinstance(control, (*CON_TEXTO_PROPIO, wx.StaticText, wx.StaticBox, wx.RadioBox)):
		texto = texto_visible(control.GetLabel())
	elif control.GetParent() is not None:
		anterior = _hermano_anterior(control)
		if isinstance(anterior, wx.StaticText):
			texto = texto_visible(anterior.GetLabel())
	return f"{tipo} «{texto}»" if texto else tr('{tipo} sin texto (name={GetName!r})').format(tipo=(tipo), GetName=(control.GetName()))


def _frase(texto: str) -> str:
	"""Primera letra en mayúscula para empezar una frase."""
	return texto[:1].upper() + texto[1:]


def _hermanos(control: wx.Window) -> list[wx.Window]:
	padre = control.GetParent()
	if padre is None:
		return []
	return [h for h in padre.GetChildren() if not isinstance(h, wx.TopLevelWindow)]


def _hermano_anterior(control: wx.Window) -> wx.Window | None:
	hermanos = _hermanos(control)
	for posicion, hermano in enumerate(hermanos):
		if hermano is control:
			return hermanos[posicion - 1] if posicion > 0 else None
	return None


def _hermano_siguiente(control: wx.Window) -> wx.Window | None:
	hermanos = _hermanos(control)
	for posicion, hermano in enumerate(hermanos):
		if hermano is control:
			return hermanos[posicion + 1] if posicion + 1 < len(hermanos) else None
	return None


def _recorrer(
	ventana: wx.Window, paginas: tuple[tuple[int, int], ...], salida: list[tuple[wx.Window, tuple[tuple[int, int], ...]]],
) -> None:
	"""Controles visibles de la ventana; los de cada pestaña llevan su página."""
	es_libro = isinstance(ventana, wx.BookCtrlBase)
	paginas_libro = [ventana.GetPage(i) for i in range(ventana.GetPageCount())] if es_libro else []
	for hijo in ventana.GetChildren():
		if isinstance(hijo, (wx.TopLevelWindow, wx.StatusBar, wx.ToolBar)):
			continue
		propias = paginas
		if es_libro:
			indice = next((i for i, pagina in enumerate(paginas_libro) if pagina is hijo), -1)
			if indice < 0:
				continue  # piezas internas del cuaderno (pestañas, lista de un Listbook)
			propias = (*paginas, (id(ventana), indice))
		elif not hijo.IsShown():
			continue
		salida.append((hijo, propias))
		if isinstance(hijo, CONTENEDORES):
			_recorrer(hijo, propias, salida)


def _elementos_menu(menu: wx.Menu, ruta: str) -> Iterable[tuple[wx.MenuItem, str]]:
	for item in menu.GetMenuItems():
		if item.IsSeparator():
			continue
		texto = f"{ruta} > {texto_visible(item.GetItemLabel())}"
		yield item, texto
		if item.GetSubMenu() is not None:
			yield from _elementos_menu(item.GetSubMenu(), texto)


def _revisar_letras_menu(menu: wx.Menu, ruta: str, problemas: list[Problema]) -> None:
	vistas: dict[str, str] = {}
	for item in menu.GetMenuItems():
		if item.IsSeparator():
			continue
		texto = f"{ruta} > {texto_visible(item.GetItemLabel())}"
		letra = letra_de_acceso(item.GetItemLabel())
		if letra is None:
			problemas.append(Problema(SIN_LETRA, tr('El elemento de menú «{texto}» no tiene letra de acceso (&).').format(texto=(texto))))
		elif letra in vistas:
			problemas.append(Problema(
				LETRA_REPETIDA, tr('La letra «{upper}» se repite en el menú «{ruta}»: «{v}» y «{texto}».').format(upper=(letra.upper()), ruta=(ruta), v=(vistas[letra]), texto=(texto))))
		else:
			vistas[letra] = texto
			if _letra_dificil(letra):
				problemas.append(Problema(LETRA_DIFICIL, tr('«{texto}» usa la letra «{letra}», difícil de pulsar con Alt.').format(texto=(texto), letra=(letra)), aviso=True))
		if item.GetSubMenu() is not None:
			_revisar_letras_menu(item.GetSubMenu(), texto, problemas)


def revisar_teclado(
	ventana: wx.Window,
	teclas_propias: Iterable[str] = (),
	ignorar: Iterable[str] = (),
) -> list[Problema]:
	"""Revisa etiquetas, letras de acceso y atajos de una ventana ya construida.

	:param ventana: ``wx.Frame``, ``wx.Dialog`` o un panel. No hace falta mostrarla.
	:param teclas_propias: atajos que la ventana atiende a mano («Ctrl+F», «F5»).
	:param ignorar: códigos de problema que no se quieren comprobar (``ATAJO_EDICION``...).
	:return: problemas encontrados, en el orden del recorrido.
	"""
	problemas: list[Problema] = []
	controles: list[tuple[wx.Window, tuple[tuple[int, int], ...]]] = []
	_recorrer(ventana, (), controles)
	letras: list[_Letra] = []

	def anotar_letra(letra: str | None, origen: str, paginas: tuple[tuple[int, int], ...]) -> None:
		if letra is None:
			return
		letras.append(_Letra(letra, origen, paginas))
		if _letra_dificil(letra):
			problemas.append(Problema(LETRA_DIFICIL, tr('{_frase} usa la letra «{letra}», difícil de pulsar con Alt.').format(_frase=(_frase(origen)), letra=(letra)), aviso=True))

	for control, paginas in controles:
		descripcion = _describir(control)
		if isinstance(control, NECESITAN_ETIQUETA):
			anterior = _hermano_anterior(control)
			if not isinstance(anterior, wx.StaticText):
				problemas.append(Problema(
					SIN_ETIQUETA,
					tr('{_frase} no tiene una etiqueta (wx.StaticText) creada justo antes con el mismo padre: el lector no le da nombre y Alt+letra no lleva a él.').format(_frase=(_frase(descripcion)))))
			elif letra_de_acceso(anterior.GetLabel()) is None:
				problemas.append(Problema(
					SIN_LETRA, tr('La etiqueta «{texto_visible}» de {v} no tiene letra de acceso (&).').format(texto_visible=(texto_visible(anterior.GetLabel())), v=(descripcion.split(' «')[0]))))
		elif isinstance(control, CON_TEXTO_PROPIO):
			letra = letra_de_acceso(control.GetLabel())
			if letra is None:
				problemas.append(Problema(SIN_LETRA, tr('{_frase} no tiene letra de acceso (&).').format(_frase=(_frase(descripcion)))))
			anotar_letra(letra, descripcion, paginas)
		elif isinstance(control, wx.RadioBox):
			anotar_letra(letra_de_acceso(control.GetLabel()), descripcion, paginas)
			for indice in range(control.GetCount()):
				opcion = control.GetString(indice)
				letra = letra_de_acceso(opcion)
				if letra is None:
					problemas.append(Problema(SIN_LETRA, tr('La opción «{texto_visible}» de {descripcion} no tiene letra de acceso (&).').format(texto_visible=(texto_visible(opcion)), descripcion=(descripcion))))
				anotar_letra(letra, tr('la opción «{texto_visible}»').format(texto_visible=(texto_visible(opcion))), paginas)
		elif isinstance(control, (wx.StaticText, wx.StaticBox)):
			letra = letra_de_acceso(control.GetLabel())
			anotar_letra(letra, descripcion, paginas)
			if letra is not None and isinstance(control, wx.StaticText):
				siguiente = _hermano_siguiente(control)
				if siguiente is None or isinstance(siguiente, SIN_FOCO):
					problemas.append(Problema(
						LETRA_SIN_DESTINO,
						tr('{_frase} tiene letra de acceso pero no va seguida de un control que reciba el foco: créela justo antes de su control.').format(_frase=(_frase(descripcion)))))

	# Letras repetidas en lo que se ve a la vez.
	for posicion, primera in enumerate(letras):
		for segunda in letras[posicion + 1:]:
			if primera.letra == segunda.letra and _compatibles(primera, segunda):
				problemas.append(Problema(
					LETRA_REPETIDA,
					tr('Alt+{upper} está repetido: {origen} y {origen2}.').format(upper=(primera.letra.upper()), origen=(primera.origen), origen2=(segunda.origen))))

	# Barra de menús: letras de los títulos y de cada menú.
	barra = ventana.GetMenuBar() if isinstance(ventana, wx.Frame) else None
	titulos: dict[str, str] = {}
	if barra is not None:
		for indice in range(barra.GetMenuCount()):
			etiqueta = barra.GetMenuLabel(indice)
			titulo = texto_visible(etiqueta)
			letra = letra_de_acceso(etiqueta)
			if letra is None:
				problemas.append(Problema(SIN_LETRA, tr('El menú «{titulo}» de la barra de menús no tiene letra de acceso (&).').format(titulo=(titulo))))
			elif letra in titulos:
				problemas.append(Problema(
					LETRA_REPETIDA, tr('Alt+{upper} abre dos menús de la barra: «{v}» y «{titulo}».').format(upper=(letra.upper()), v=(titulos[letra]), titulo=(titulo))))
			else:
				titulos[letra] = titulo
			_revisar_letras_menu(barra.GetMenu(indice), titulo, problemas)
		vistos: set[tuple[str, str]] = set()
		for letra_control in letras:
			clave = (letra_control.letra, letra_control.origen)
			if letra_control.letra in titulos and clave not in vistos:
				vistos.add(clave)
				problemas.append(Problema(
					CHOCA_CON_MENU,
					tr('{_frase} usa Alt+{upper}, que también abre el menú «{v}»: uno de los dos queda inalcanzable con esa tecla.').format(_frase=(_frase(letra_control.origen)), upper=(letra_control.letra.upper()), v=(titulos[letra_control.letra]))))

	# Atajos: menús, tablas de aceleradores y teclas propias.
	atajos: list[tuple[str, str, int | None, str]] = []  # (atajo, origen, id, etiqueta del menú)
	if barra is not None:
		for indice in range(barra.GetMenuCount()):
			for item, texto in _elementos_menu(barra.GetMenu(indice), texto_visible(barra.GetMenuLabel(indice))):
				entrada = item.GetAccel()
				if entrada is not None and entrada.GetKeyCode():
					atajos.append((
						atajo_de_entrada(entrada.GetFlags(), entrada.GetKeyCode()), tr('el menú «{texto}»').format(texto=(texto)),
						item.GetId(), texto_visible(item.GetItemLabel()).lower()))
	for banderas, codigo, identificador in getattr(ventana, "_atajos_accesibles", ()):
		atajos.append((atajo_de_entrada(banderas, codigo), tr("la tabla de atajos (instalar_atajos)"), identificador, ""))
	for texto in teclas_propias:
		atajos.append((normalizar_atajo(texto), tr("una tecla atendida a mano"), None, ""))

	reservadas = dict(_RESERVADAS)
	if any(isinstance(c, wx.BookCtrlBase) for c, _p in controles):
		reservadas["Ctrl+Tab"] = reservadas["Ctrl+Mayús+Tab"] = (tr("cambia de pestaña"), "")
	if any(hasattr(c, "anunciar_celda") for c, _p in controles):  # ListaAccesible
		for numero in "1234567890":
			reservadas[f"Ctrl+{numero}"] = (tr("la lista la usa para leer una columna"), "")
	hay_campos_editables = any(
		isinstance(c, (wx.TextCtrl, wx.ComboBox)) and c.IsEditable() for c, _p in controles)

	por_atajo: dict[str, tuple[str, int | None]] = {}
	for atajo, origen, identificador, etiqueta_menu in atajos:
		if atajo in por_atajo:
			origen_previo, id_previo = por_atajo[atajo]
			if identificador is None or identificador != id_previo:
				problemas.append(Problema(ATAJO_REPETIDO, tr('{atajo} está en {origen_previo} y en {origen}: solo funcionará uno.').format(atajo=(atajo), origen_previo=(origen_previo), origen=(origen))))
			continue
		por_atajo[atajo] = (origen, identificador)
		motivo, permitida = reservadas.get(atajo, ("", ""))
		if motivo and not (permitida and permitida in etiqueta_menu):
			problemas.append(Problema(ATAJO_RESERVADO, tr('{atajo} ({origen}) está reservado: {motivo}.').format(atajo=(atajo), origen=(origen), motivo=(motivo))))
		elif "Insert" in atajo.split("+") or "Bloq Mayús" in atajo:
			problemas.append(Problema(ATAJO_RESERVADO, tr('{atajo} ({origen}) usa una tecla del lector de pantalla.').format(atajo=(atajo), origen=(origen))))
		modificadores = atajo.split("+")[:-1]
		tecla = atajo.split("+")[-1].lower()
		if modificadores == ["Alt"] and len(tecla) == 1:
			if tecla in titulos:
				problemas.append(Problema(CHOCA_CON_MENU, tr('{atajo} ({origen}) también abre el menú «{v}».').format(atajo=(atajo), origen=(origen), v=(titulos[tecla]))))
			for letra_control in letras:
				if letra_control.letra == tecla:
					problemas.append(Problema(
						LETRA_REPETIDA, tr('{atajo} ({origen}) coincide con la letra de acceso de {origen2}.').format(atajo=(atajo), origen=(origen), origen2=(letra_control.origen))))
		if atajo in _TECLAS_EDICION and hay_campos_editables and identificador is not None:
			problemas.append(Problema(
				ATAJO_EDICION,
				tr('{atajo} ({origen}) se adelanta a los campos de texto de la ventana: su acción debe copiar, pegar o deshacer en el campo enfocado cuando el foco esté en uno.').format(atajo=(atajo), origen=(origen)), aviso=True))

	# Barra de herramientas: cada botón con equivalente de teclado.
	if isinstance(ventana, wx.Frame) and ventana.GetToolBar() is not None:
		barra_herramientas = ventana.GetToolBar()
		ids_con_teclado = {i for _a, _o, i, _e in atajos if i is not None}
		for posicion in range(barra_herramientas.GetToolsCount()):
			herramienta = barra_herramientas.GetToolByPos(posicion)
			if herramienta is None or not herramienta.IsButton():
				continue
			identificador = herramienta.GetId()
			en_menu = barra is not None and barra.FindItemById(identificador) is not None
			if not en_menu and identificador not in ids_con_teclado:
				nombre = herramienta.GetShortHelp() or herramienta.GetLabel() or str(identificador)
				problemas.append(Problema(
					SIN_TECLADO, tr('El botón «{nombre}» de la barra de herramientas no tiene elemento de menú ni atajo con el mismo id.').format(nombre=(nombre))))

	descartados = set(ignorar)
	return [p for p in problemas if p.codigo not in descartados]


def informe(problemas: Sequence[Problema]) -> str:
	"""Texto plano, una línea por problema, que se lee bien con un lector de pantalla."""
	if not problemas:
		return tr("Sin problemas de teclado.")
	errores = sum(1 for p in problemas if not p.aviso)
	avisos = len(problemas) - errores
	lineas = [tr('{errores} errores y {avisos} avisos de teclado:').format(errores=(errores), avisos=(avisos))]
	lineas.extend(f"- {p}" for p in problemas)
	return "\n".join(lineas)


def afirmar_teclado_correcto(
	ventana: wx.Window,
	teclas_propias: Iterable[str] = (),
	ignorar: Iterable[str] = (),
	con_avisos: bool = False,
) -> None:
	"""Para pruebas: falla con el informe completo si hay errores (y avisos, si se pide)."""
	problemas = revisar_teclado(ventana, teclas_propias, ignorar)
	if any(con_avisos or not p.aviso for p in problemas):
		raise AssertionError(informe(problemas))
