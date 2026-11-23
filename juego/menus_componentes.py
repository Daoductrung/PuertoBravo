"""Opciones, Actualizaciones, Componentes: idiomas, voces, documentación, packs de sonidos y mods sueltos.

Se buscan en la misma fuente que las versiones del juego (componentes.py) y se instalan sin cerrar el juego. La lista
solo trae lo que hay que hacer: los componentes que no tienes y los que tienen una versión nueva; lo que ya trae el juego
o ya instalaste, al día, no sale. Si no hay nada, se dice y no se abre ninguna lista. Intro instala o actualiza el elegido,
e «Instalar todo» los pone todos de una vez. Al arrancar, si está activado, se mira si hay componentes nuevos y se avisa.
"""
from .i18n import tr

from . import componentes as C, registro
from .menus import Menu, Opcion
from .menus_actualizar import TEXTO_FUENTE, Tarea, _abrir, texto_progreso


def tamano_txt(n):
    """Lo que ocupa una descarga, dicho con su unidad: «48 megas», «3,5 megas», «120 kilobytes»."""
    if n < 1024 ** 2:
        k = max(1, round(n / 1024))
        return tr("1 kilobyte") if k == 1 else tr("{n} kilobytes").format(n=k)
    m = n / 1024 ** 2
    coma = "," if tr("coma decimal") == "coma decimal" else "."      # la coma decimal del idioma
    t = f"{m:.1f}".replace(".", coma).replace(coma + "0", "") if m < 10 else str(round(m))
    return tr("{n} megas").format(n=t)


def _linea(c, hay):
    v = hay.get(c.id, 0)
    if v:
        return tr("{tipo}: {nombre}, actualización a la versión {version}, {tamano}").format(tipo=c.tipo_txt, nombre=c.nombre, version=c.version,
                                                                                          tamano=tamano_txt(c.tamano))
    return tr("{tipo}: {nombre}, nuevo, {tamano}").format(tipo=c.tipo_txt, nombre=c.nombre, tamano=tamano_txt(c.tamano))


def buscar(app):
    """Busca los componentes publicados y abre la lista."""
    cfg = app.cfg

    def trabajo(tarea):
        return C.consultar(cfg["act_fuente"], cfg["act_url"], abrir=_abrir(app), claves=getattr(app, "act_claves", None))

    def fin(publicados, error):
        registro.info("componentes", "Búsqueda de componentes", fuente=cfg["act_fuente"], hay=len(publicados or {}),
                      error=f"{type(error).__name__}: {error}" if error is not None else "ninguno")
        if error is not None:
            app.son("error")
            app.decir(str(error) if isinstance(error, C.A.ErrorActualizacion) else tr("No se pudo consultar la lista de componentes."), True)
            return
        if not lista(app, publicados or {}):
            app.son("guardado")
            app.decir(tr("Tienes todos los componentes al día: no hay nada que instalar ni que actualizar."), True)
    app.abrir(Tarea(app, tr("Buscando componentes en {v}").format(v=TEXTO_FUENTE[cfg["act_fuente"]]), trabajo, fin))


ORDEN = ("idioma", "voces", "documentacion", "sonidos", "mod", "musica", "radio")


def _orden(tipo):
    return ORDEN.index(tipo) if tipo in ORDEN else len(ORDEN)


def interesa(app, c):
    """¿Es de una categoría que quieres ver? Las que no (Categorías que te interesan) no salen ni te avisan."""
    return c.tipo not in (app.cfg["comp_sin_interes"] or [])


def pendientes(app, publicados):
    """Lo que puedes instalar o actualizar de las categorías que te interesan."""
    return [c for c, _ in C.novedades(publicados) if interesa(app, c)]      # novedades() ya deja fuera los que piden un juego más nuevo


def lista(app, publicados, antes=None):
    """Los componentes que hay que instalar o actualizar, por categorías: idiomas, voces, documentación, sonidos y mods. Cada
    categoría abre los suyos, con un Instalar todo solo de esa categoría. None, sin abrir nada, si no hay ninguno.
    `antes`: una frase que se dice delante del título, al abrir (lo que se acaba de instalar)."""
    todos = [c for c, _ in C.novedades(publicados)]
    if not todos:
        return None

    def ops():
        nuevos = pendientes(app, publicados)
        lista_ = []
        if len(nuevos) > 1:
            lista_.append(Opcion(tr("Instalar todo lo que te interesa: {n} componentes, {tamano}").format(n=len(nuevos), tamano=tamano_txt(sum(c.tamano for c in nuevos))),
                                 lambda: instalar(app, nuevos, publicados),
                                 ayuda=tr("Descarga e instala, uno tras otro, todos los componentes de las categorías que te interesan.")))
        for tipo in sorted({c.tipo for c in nuevos}, key=_orden):
            suyos = [c for c in nuevos if c.tipo == tipo]
            lista_.append(Opcion(tr("{tipo}: {n} para instalar o actualizar, {tamano}").format(tipo=suyos[0].tipo_txt, n=len(suyos), tamano=tamano_txt(sum(c.tamano for c in suyos))),
                                 lambda t=tipo: categoria(app, publicados, t),
                                 ayuda=tr("Intro abre los componentes de esta categoría: puedes instalar solo esos, todos o uno a uno.")))
        ocultos = len(todos) - len(nuevos)
        if ocultos:
            lista_.append(Opcion(tr("En las categorías que no te interesan hay {n} más").format(n=ocultos),
                                 ayuda=tr("No se muestran ni te avisan al arrancar. Cámbialo en Categorías que te interesan, aquí debajo.")))
        lista_.append(Opcion(lambda: tr("Categorías que te interesan: ") + categorias_txt(app), lambda: elegir_categorias(app, al_cambiar=lambda: m.refrescar(False)),
                             ayuda=tr("Marca qué clase de componentes quieres ver: si no quieres mods, quítalos; si solo quieres idiomas, deja solo los idiomas. "
                                   "Lo que no te interesa no sale aquí ni te avisa al arrancar el juego.")))
        lista_.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
        return lista_
    n = len(pendientes(app, publicados))
    titulo = tr("Componentes para instalar o actualizar: {n}").format(n=n)
    m = Menu(app, titulo, ops, intro=tr("Por categorías. Intro abre una y ves solo sus componentes. F1 dice qué hace cada opción"))
    m.es_componentes = True
    m.antes = antes
    app.abrir(m)
    return m


def categoria(app, publicados, tipo):
    """Los componentes de una sola categoría: así se pueden poner al día solo los idiomas, solo los packs..."""
    hay = C.instalados()
    suyos = sorted((c for c in pendientes(app, publicados) if c.tipo == tipo), key=lambda c: c.nombre)
    if not suyos:
        return
    ops = []
    if len(suyos) > 1:
        ops.append(Opcion(tr("Instalar todo en {tipo}: {n} componentes, {tamano}").format(tipo=suyos[0].tipo_txt, n=len(suyos), tamano=tamano_txt(sum(c.tamano for c in suyos))),
                          lambda: instalar(app, suyos, publicados),
                          ayuda=tr("Descarga e instala, uno tras otro, todos los de esta categoría, y nada más.")))
    for c in suyos:
        ops.append(Opcion(_linea(c, hay), lambda c=c: instalar(app, [c], publicados), ayuda=c.descripcion or tr("Intro lo instala o lo actualiza.")))
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, tr("{tipo} para instalar o actualizar: {n}").format(tipo=suyos[0].tipo_txt, n=len(suyos)), ops,
             intro=tr("Intro instala o actualiza el componente elegido. F1 dice qué trae"))
    m.es_componentes = True
    app.abrir(m)
    return m


def categorias_txt(app):
    fuera = app.cfg["comp_sin_interes"] or []
    dentro = [C.NOMBRE_TIPO[t] for t in ORDEN[:5] if t not in fuera]
    if len(dentro) == 5:
        return tr("todas")
    return ", ".join(tr(x) for x in dentro) if dentro else tr("ninguna")


def elegir_categorias(app, al_cambiar=None):
    """Sí o no por cada categoría de componentes. Se guarda al momento."""
    def cambiar(tipo):
        def f():
            fuera = list(app.cfg["comp_sin_interes"] or [])
            if tipo in fuera:
                fuera.remove(tipo)
            else:
                fuera.append(tipo)
            app.cfg["comp_sin_interes"] = fuera
            app.cfg.guardar()
            m.refrescar(False)
            app.decir((tr("{tipo}: sí") if tipo not in fuera else tr("{tipo}: no")).format(tipo=tr(C.NOMBRE_TIPO[tipo])), True)
            if al_cambiar:
                al_cambiar()
        return f

    def ops():
        fuera = app.cfg["comp_sin_interes"] or []
        return [Opcion(lambda t=t: (tr("{tipo}: sí") if t not in fuera else tr("{tipo}: no")).format(tipo=tr(C.NOMBRE_TIPO[t])), cambiar(t),
                       ayuda=tr("Intro cambia entre sí y no. Con no, esta clase de componentes no sale en la lista ni te avisa al arrancar."))
                for t in ORDEN[:5]] + [Opcion(tr("Volver"), lambda: app.cerrar(m))]
    m = Menu(app, tr("Categorías de componentes que te interesan"), ops, intro=tr("Intro cambia entre sí y no"))
    app.abrir(m)
    return m


def instalar(app, cuales, publicados=None):
    """Instala uno o varios componentes, uno tras otro, con su progreso. Al terminar dice qué ha quedado y si hay que reiniciar."""
    estado = {"hechos": [], "reiniciar": False}
    while publicados is not None and app.pila and getattr(app.pila[-1], "es_componentes", False):
        app.cerrar(app.pila[-1])          # la lista (y la categoría) se rehacen al terminar, con lo que quede: no se vuelve a leer la de antes

    def trabajo(tarea):
        for i, c in enumerate(cuales, 1):
            if tarea.cancelada:
                break

            def progreso(hecho, total, c=c, i=i):
                tarea.estado = (tr("{i} de {n}, {nombre}: ").format(i=i, n=len(cuales), nombre=c.nombre) if len(cuales) > 1 else "") + texto_progreso(hecho, total)
            frase = C.instalar(c, progreso=progreso, cancelado=lambda: tarea.cancelada, abrir=_abrir(app))
            registro.info("componentes", "Componente instalado", id=c.id, version=c.version)
            estado["hechos"].append(frase)
            estado["reiniciar"] = estado["reiniciar"] or C.reinicio_necesario(c)
            if c.tipo == "sonidos" and hasattr(app, "recargar_sonidos"):
                estado["sonidos"] = True
        return estado

    def fin(r, error):
        hechos = estado["hechos"]
        if estado.get("sonidos"):
            try:
                app.recargar_sonidos()
            except Exception:
                registro.excepcion("componentes", "No se pudieron recargar los sonidos tras instalar un pack")
        if error is not None:
            app.son("error")
            motivo = str(error) if isinstance(error, C.A.ErrorActualizacion) else tr("No se pudo instalar el componente.")
            app.decir(" ".join(hechos + [motivo]), True)
            return
        app.son("guardado")
        fin_txt = tr(" Se nota la próxima vez que abras el juego.") if estado["reiniciar"] else ""
        texto = " ".join(hechos) + fin_txt if hechos else tr("No se ha instalado nada.")
        if publicados is not None and lista(app, publicados, antes=texto) is not None:      # quedan más: la lista, con lo que queda
            return
        if publicados is not None:
            texto += " " + tr("Ya tienes todos los componentes al día.")
        app.decir(texto, True)
    nombre = cuales[0].nombre if len(cuales) == 1 else tr("{n} componentes").format(n=len(cuales))
    app.abrir(Tarea(app, tr("Instalando {nombre}").format(nombre=nombre), trabajo, fin))


def mirar_al_arrancar(app):
    """En el hilo de la comprobación del arranque: apunta cuántos componentes nuevos hay, para avisar luego."""
    try:
        app.comp_aviso = len(pendientes(app, C.consultar(app.cfg["act_fuente"], app.cfg["act_url"])))      # solo de las categorías que te interesan
        registro.info("componentes", "Comprobación al arrancar", nuevos=app.comp_aviso)
    except Exception as e:
        registro.info("componentes", "Comprobación de componentes al arrancar sin resultado", motivo=f"{type(e).__name__}: {e}")
        app.comp_aviso = 0


def paso(app):
    """El aviso de componentes nuevos, en el menú principal, cuando no hay otra cosa que decir."""
    n = getattr(app, "comp_aviso", 0)
    if not n or app.partida is not None or len(app.pila) != 1 or getattr(app, "act_aviso", None) is not None:
        return
    app.comp_aviso = 0
    app.son("evento")
    app.decir(tr("Hay componentes nuevos: {n}. Puede ser un idioma, unas voces o un pack de sonidos. Están en Opciones, Actualizaciones, Componentes.").format(n=n))
