"""Comunidad de jugadores, en el menú principal: grupos, foros, servidores y otros sitios que crean y llevan los propios
jugadores. No es oficial. Lo que se lista está en data/datos/comunidad.json; aquí solo está cómo se recorre."""
import copy
import json
import os

from . import i18n, rutas
from .i18n import tr

ARCHIVO = "comunidad.json"


def cargar():
    """Los datos de la sección, en el idioma del juego. Si el archivo falta o está roto, una sección vacía con los avisos."""
    try:
        with open(os.path.join(rutas.DATOS, ARCHIVO), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d = i18n.traducir_datos(copy.deepcopy(d))
    d.setdefault("titulo", tr("Comunidad de jugadores, sección no oficial"))
    d.setdefault("aviso", tr("Esta sección no es oficial."))
    d.setdefault("responsabilidad", "")
    d.setdefault("secciones", [])
    return d


def _abrir_url(app, url, que):
    try:
        os.startfile(url)
        app.decir(tr('Abriendo {que} en tu navegador.').format(que=que), True)
    except (OSError, AttributeError):
        app.son("error")
        app.decir(tr('No se pudo abrir el navegador. La dirección es {url}').format(url=url), True)


def anadir_servidor(app, nombre, direccion):
    """Lo añade a la lista de Jugar en un servidor, con su nombre. Devuelve si lo ha añadido (False si ya estaba)."""
    lista = list(app.cfg["servidores"])
    if any(str(x.get("dir", "")).lower() == direccion.lower() for x in lista):
        app.decir(tr('{nombre} ya está en tu lista de servidores. Entra desde el menú principal, Jugar en un servidor.').format(nombre=nombre), True)
        return False
    lista.append({"nombre": nombre, "dir": direccion, "cert": ""})
    app.cfg["servidores"] = lista
    app.cfg.guardar()
    app.son("menu_ok")
    app.decir(tr('{nombre} añadido a tu lista de servidores. Para entrar, en el menú principal, Jugar en un servidor.').format(nombre=nombre), True)
    return True


def _opcion_enlace(app, e, Opcion):
    nombre = e.get("nombre", "")
    idioma = e.get("idioma", "")
    texto = tr('{nombre}, en {idioma}').format(nombre=nombre, idioma=idioma) if idioma else nombre
    desc = e.get("desc", "")
    if e.get("servidor"):
        return Opcion(texto, lambda: anadir_servidor(app, nombre, e["servidor"]),
                      ayuda=(desc + " " if desc else "") + tr('La dirección es {dir}. Intro lo añade a tu lista de Jugar en un servidor.').format(dir=e["servidor"]))
    url = e.get("url", "")
    return Opcion(texto, lambda: _abrir_url(app, url, nombre), ayuda=(desc + " " if desc else "") + tr("Intro lo abre en tu navegador."))


def menu(app):
    from .menus import Menu, Opcion
    d = cargar()

    def seccion(s):
        def f():
            ops = [_opcion_enlace(app, e, Opcion) for e in s.get("enlaces", [])]
            if not ops:
                ops = [Opcion(tr("Todavía no hay nada aquí"), ayuda=d.get("apuntar") or tr("Si creas algo para los jugadores, avisa al autor para que salga aquí."))]
            app.abrir(Menu(app, s.get("nombre", ""), ops, intro=s.get("ayuda") or None))
        return f
    ops = [Opcion(d["aviso"], ayuda=d["responsabilidad"] or None)]
    if d["responsabilidad"]:
        ops.append(Opcion(d["responsabilidad"], ayuda=tr("Cada sitio tiene sus propias normas, que ponen quienes lo llevan.")))
    for s in d["secciones"]:
        n = len(s.get("enlaces", []))
        ops.append(Opcion(tr('{nombre}: {n}').format(nombre=s.get("nombre", ""), n=n), seccion(s), ayuda=s.get("ayuda") or None))
    if d.get("apuntar") and d.get("apuntar_url"):
        ops.append(Opcion(tr("Apuntar un grupo, un foro, un servidor o cualquier otro recurso"), lambda: _abrir_url(app, d["apuntar_url"], tr("la issue de la comunidad")),
                          ayuda=d["apuntar"]))
    app.abrir(Menu(app, d["titulo"], ops, intro=d["aviso"] + (" " + d["responsabilidad"] if d["responsabilidad"] else "")))
