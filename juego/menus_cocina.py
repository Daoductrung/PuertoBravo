"""Los menús de la compra, la despensa y la cocina (1.7.1): la cocina de casa, la nevera, la despensa, lo que llevas
encima y la compra rápida en el menú de la tienda. Las reglas están en compra.py."""
from .i18n import tr
import random

import pygame

from . import compra as C
from .compra import AJ, _cuantos, _junta
from .menus import Menu, Opcion


# ============================================================================ en la tienda, sin pasear
def opcion_rapida(p, l):
    """La opción del menú de la tienda para comprar comida para casa sin recorrer los pasillos. Lista vacía si allí no se vende."""
    if not p.surtido(l):
        return []
    nombres = _junta(pa["nombre"] for pa, _ in p.surtido(l))
    return [Opcion(tr("Comprar comida para llevar a casa"), lambda: menu_rapido(p, l),
                   ayuda=tr('Lo mismo que hay en los pasillos, sin pasear: {nombres}. Cada cosa se paga al cogerla y te la llevas encima; después se guarda en la cocina de una casa tuya, y lo que es para cocinar se cocina allí. Lo que se come tal cual puedes comértelo por la calle, desde el móvil, en Inventario. Si prefieres pasear por la tienda con una cesta y pagar al final en la caja, elige Recorrer el local por dentro.').format(nombres=(nombres)))]


def menu_rapido(p, l):
    app = p.app

    def comprar(prod):
        def f():
            if p.agotado(l, prod):
                app.son("error")
                app.decir(tr('{nombre}: hoy no queda.').format(nombre=(prod['nombre'])), True)
            elif p.comprar_productos(l, {prod["id"]: 1}):
                app.decir(tr('{nombre}, comprado. Llevas encima {_cuantos} de {entero}. Te quedan {dinero} euros.').format(nombre=(prod['nombre']), _cuantos=(_cuantos(p._total(p.encima()), 'cosa', 'cosas')), entero=(AJ.entero('capacidad_encima')), dinero=(p.j.dinero)), True)
        return f

    def ops():
        oferta = p.oferta_de(l)
        lista = []
        for pa, genero in p.surtido(l):
            for prod in genero:
                def texto(prod=prod, pa=pa):
                    if p.agotado(l, prod):
                        return tr('{nombre}: hoy no queda').format(nombre=(prod['nombre']))
                    return (f"{prod['nombre']}: {C._euros(p.precio_producto(l, prod))}" + (tr(", de oferta") if prod["id"] == oferta else "") + tr('. De {nombre}, ').format(nombre=(pa['nombre']))
                            + ((tr("para beber") if prod.get("bebida") else tr("para comer")) + tr(" tal cual") if C.comestible(prod) else tr("para cocinar")))
                lista.append(Opcion(texto, comprar(prod), ayuda=p.producto_ayuda(prod), callado=True))
        return lista
    app.abrir(Menu(app, lambda: tr('Comida para llevar a casa, en {nombre}. Tienes {dinero} euros. Llevas encima {_total} cosas de {entero}').format(nombre=(l.nombre), dinero=(p.j.dinero), _total=(p._total(p.encima())), entero=(AJ.entero('capacidad_encima'))),
                   ops, intro=tr("Intro compra una unidad y te la llevas encima")))


# ============================================================================ lo que llevas encima
def menu_encima(p):
    """La comida y la compra que llevas: lo que se come tal cual, te lo comes aquí; lo de cocinar espera a que llegues a casa."""
    app = p.app
    aviso = p.aviso_caducidad(p.j.encima)

    def usar(lote):
        def f():
            info = p.lote_info(lote)
            if info is None or lote not in p.j.encima:
                return m.refrescar()
            if not info["comestible"]:
                app.decir(tr('{nombre}: es para cocinar. Guárdalo en la cocina de una casa tuya.').format(nombre=(info['nombre'])), True)
                return
            t = p.comer_lote(p.j.encima, lote)
            if t:
                m.refrescar(False)
                app.decir(t, True)
        return f

    def ops():
        lista = []
        for lote in p.encima():
            info = p.lote_info(lote)
            lista.append(Opcion(lambda lote=lote, info=info: p.lote_txt(lote) + (tr(". Intro para ") + ("beber" if info["bebida"] else "comer") if info["comestible"] else tr(". Para cocinar")),
                                usar(lote), ayuda=((tr('Una unidad {efecto_txt}. ').format(efecto_txt=(C.efecto_txt(info))) if info["comestible"] else tr("No se come tal cual: es un ingrediente. "))
                                                   + tr("El hambre y la sed solo cuentan con la vida realista activada; la salud y el ánimo, siempre.")),
                                callado=True))
        return lista or [Opcion(tr("No llevas comida ni compra encima"), ayuda=tr("Lo que compras en una tienda de comida lo llevas encima hasta que lo guardas en la cocina de una casa tuya."))]
    m = Menu(app, lambda: tr('Comida y compra que llevas: {_total} cosas de {entero}').format(_total=(p._total(p.encima())), entero=(AJ.entero('capacidad_encima'))), ops, intro=aviso or None)
    app.abrir(m)


def opciones_movil(p):
    """Lo que añade al inventario del móvil: lo que llevas encima y, resumido, lo que hay en la cocina de cada casa tuya."""
    j = p.j
    p.limpiar_despensas()
    p.limpiar_almacenes()
    lista = [Opcion(lambda: tr('Comida y compra que llevas: {_total} de {entero}').format(_total=(p._total(p.encima())), entero=(AJ.entero('capacidad_encima'))), lambda: menu_encima(p),
                    ayuda=tr("Lo que has comprado en las tiendas de comida y todavía no has guardado en casa. Lo que se come tal cual, te lo comes desde aquí, estés donde estés. "
                          "Lo de cocinar se guarda en la cocina de una casa tuya."))]
    for cid in j.propiedades:
        casa = p.lug(cid)
        if casa is not None and j.despensa.get(cid):
            lista.append(Opcion(lambda casa=casa: tr('En {nombre}. {cocina_txt}').format(nombre=(casa.nombre), cocina_txt=(p.cocina_txt(casa))), lambda casa=casa: menu_resumen(p, casa),
                                ayuda=tr("Lo que tienes guardado en la cocina de esa casa. Para cocinar, comer o guardar la compra hay que ir allí.")))
    return lista


def menu_resumen(p, casa):
    """Lo que hay en la cocina de una casa, para consultarlo desde el menú de la casa o desde el móvil. Solo se lee."""
    app = p.app
    lotes = p.despensa(casa)
    ops = [Opcion((tr("Nevera: ") if p.lote_info(x)["sitio"] == "nevera" else tr("Despensa: ")) + p.lote_txt(x),
                  ayuda=tr("Algo guardado en esta cocina, con lo que queda y cuándo caduca. Aquí solo se consulta: para comerlo o llevártelo, ve a la cocina de la casa.")) for x in sorted(lotes, key=lambda x: p.lote_info(x)["sitio"] != "nevera")]
    ops = ops or [Opcion(tr("No hay nada guardado"), ayuda=tr("Lo que compres para casa en una tienda de comida se guarda en la cocina, con Guardar lo que llevas encima."))]
    posibles = [r["nombre"] for r in C.recetas(p) if not p.receta_falta(casa, r)]
    ops.append(Opcion(tr('Con esto y lo que llevas puedes cocinar: {lower}').format(lower=(_junta(posibles).lower())) if posibles else tr("Con lo que hay no sale ninguna receta"),
                      ayuda=tr("Las recetas se cocinan en la cocina, recorriendo la casa por dentro.")))
    ops.append(Opcion(lambda: tr('Recetas que sabes hacer: {len}').format(len=(len(C.recetas(p)))), lambda: menu_recetario(p), ayuda=tr("Qué lleva cada una, cuánto tarda y cuánto alimenta.")))
    app.abrir(Menu(app, tr('Cocina de {nombre}. {cocina_txt}').format(nombre=(casa.nombre), cocina_txt=(p.cocina_txt(casa))), ops, intro=tr("Para cocinar, comer de la nevera o guardar la compra, recorre la casa por dentro hasta la cocina")))


def menu_recetario(p):
    app = p.app
    ops = [Opcion(f"{r['nombre']}. {p.receta_txt(r)}", ayuda=tr("Una receta que sabes hacer, con lo que lleva. Se cocina en la cocina de una casa tuya, en Cocinar.")) for r in C.recetas(p)]
    ops.append(Opcion(lambda: tr('Tu mano en la cocina: nivel {nivel_cocina} de 10. Platos cocinados: {get}').format(nivel_cocina=(C.nivel_cocina(p)), get=(p.j.stats.get('platos_cocinados', 0))),
                      ayuda=tr("Sube con cada plato que cocinas. Con más nivel se te quema menos la comida y te sale de categoría más veces.")))
    app.abrir(Menu(app, tr("Recetas"), ops))


def opcion_casa(p, casa):
    """La opción del menú de la casa: un resumen de la cocina."""
    return [Opcion(lambda: tr('Cocina. {cocina_txt}').format(cocina_txt=(p.cocina_txt(casa))) + (tr('. Llevas encima {_cuantos} sin guardar').format(_cuantos=(_cuantos(p._total(p.encima()), 'cosa', 'cosas'))) if p.encima() else ""),
                   lambda: menu_resumen(p, casa),
                   ayuda=tr("Lo que hay en la nevera y en la despensa de esta casa, y las recetas que sabes hacer. Para cocinar, comer de lo guardado o guardar la compra "
                         "hay que ir a la cocina: Recorrer la casa por dentro, y con las flechas hasta la cocina. Lo fresco caduca a los días."))]


# ============================================================================ la cocina de casa
def usar_cocina(p, casa, de_siempre):
    """Intro en la cocina de casa. Si no hay nada guardado ni traes comida, hace lo de siempre (comer algo de lo que haya,
    una vez al día) y recuerda que existe la despensa; si lo hay, abre el menú de la cocina."""
    if p.hay_cocina(casa):
        menu_cocina(p, casa, de_siempre)
    else:
        de_siempre(tr(" La despensa está vacía: lo que compres para casa en una tienda de comida podrás guardarlo y cocinarlo aquí."))


def menu_cocina(p, casa, de_siempre=None):
    app, j = p.app, p.j
    tirado = p.tirar_caducado(p.despensa(casa)) + p.tirar_caducado(j.encima)       # al entrar en la cocina se tira lo que se ha echado a perder
    aviso = AJ.frase("frases_caducado", cosas=_junta(tirado)) if tirado else ""

    def guardar():
        guardado, queda = p.guardar_compra(casa)
        if guardado:
            app.son("nevera")
        else:
            app.son("error")
        m.refrescar(False)
        app.decir((tr('Guardas {_cuantos}: lo fresco a la nevera y lo demás a la despensa. ').format(_cuantos=(_cuantos(guardado, 'cosa', 'cosas'))) if guardado else tr("No cabe nada más. "))
                  + (tr('Se quedan contigo {_cuantos}, que no caben. ').format(_cuantos=(_cuantos(queda, 'cosa', 'cosas'))) if queda else "") + p.cocina_txt(casa) + ".", True)

    def grifo():
        if j.sed < 15:
            app.decir(tr("Ahora no tienes sed."), True)
        else:
            p.ha_bebido(100)
            p.mez.sonar("beber", cat="interfaz")
            app.decir(tr("Un vaso de agua del grifo.") + p.necesidades_txt(), True)

    def ops():
        recs = C.recetas(p)
        posibles = sum(1 for r in recs if not p.receta_falta(casa, r))
        lista = [Opcion(lambda: tr('Cocinar: puedes hacer {posibles} de {_cuantos}').format(posibles=(posibles), _cuantos=(_cuantos(len(recs), 'receta', 'recetas'))), lambda: menu_recetas(p, casa),
                        ayuda=tr("Elige una receta. Gasta sus ingredientes, de lo guardado aquí o de lo que traes, y tarda su tiempo del juego. Salen varias raciones: te comes una "
                              "y las demás van a la nevera. Lo cocinado alimenta mucho más que lo envasado, y con la práctica sale mejor.")),
                 Opcion(lambda: tr('Nevera: {_total} de {sitio_capacidad}').format(_total=(p._total(p.de_sitio(casa, 'nevera'))), sitio_capacidad=(p.sitio_capacidad(casa, 'nevera'))), lambda: menu_sitio(p, casa, "nevera"),
                        ayuda=tr("Lo fresco y lo que has cocinado. Desde aquí comes, te llevas algo encima o tiras lo que sobre. Lo caducado se tira solo al abrirla, avisando.")),
                 Opcion(lambda: tr('Despensa: {_total} de {sitio_capacidad}').format(_total=(p._total(p.de_sitio(casa, 'despensa'))), sitio_capacidad=(p.sitio_capacidad(casa, 'despensa'))), lambda: menu_sitio(p, casa, "despensa"),
                        ayuda=tr("Lo que no necesita frío: latas, pasta, arroz, legumbres, patatas, pan y fruta."))]
        if p.encima():
            lista.append(Opcion(lambda: tr('Guardar lo que llevas encima: {_cuantos}').format(_cuantos=(_cuantos(p._total(p.encima()), 'cosa', 'cosas'))), guardar, callado=True,
                                ayuda=tr("Lo fresco va a la nevera y lo demás a la despensa, hasta donde quepa. Lo que no quepa se queda contigo.")))
        if de_siempre is not None:
            lista.append(Opcion(tr("Comer algo rápido de lo que haya por casa"), lambda: de_siempre(""), callado=True,
                                ayuda=tr("Lo de siempre: una vez al día, te preparas cualquier cosa y recuperas salud. No gasta nada de la despensa.")))
        if p.vida_realista():
            lista.append(Opcion(tr("Beber agua del grifo"), grifo, callado=True, ayuda=tr("En casa, el agua no falta: quita toda la sed.")))
        lista.append(Opcion(lambda: tr('Recetas y tu mano en la cocina: nivel {nivel_cocina} de 10').format(nivel_cocina=(C.nivel_cocina(p))), lambda: menu_recetario(p),
                            ayuda=tr("Qué lleva cada receta, cuánto tarda y cuánto alimenta, y cuántos platos llevas cocinados. Tu nivel sube con cada plato.")))
        return lista
    m = Menu(app, lambda: tr('La cocina de {nombre}. {cocina_txt}').format(nombre=(casa.nombre), cocina_txt=(p.cocina_txt(casa))), ops, intro=aviso or None)
    app.abrir(m)
    return m


def menu_sitio(p, casa, sitio):
    """La nevera o la despensa de una casa: cada cosa, con lo que queda y cuándo caduca."""
    app, j = p.app, p.j
    nombre = tr("La nevera") if sitio == "nevera" else tr("La despensa")
    tirado = p.tirar_caducado(p.despensa(casa))
    pronto = p.pronto_caduca(p.de_sitio(casa, sitio))
    aviso = " ".join(x for x in (AJ.frase("frases_caducado", cosas=_junta(tirado)) if tirado else "", tr('Ojo: caduca {_junta}').format(_junta=(_junta(pronto))) if pronto else "") if x)
    if sitio == "nevera":
        app.son("nevera")

    def acciones(lote):
        def abrir():
            info = p.lote_info(lote)
            lotes = p.despensa(casa)

            def comer():
                t = p.comer_lote(lotes, lote)
                if t:
                    if lote not in lotes:
                        app.cerrar(sub)
                    app.decir(t, True)

            def llevar():
                n = p.pasar_lote(lotes, j.encima, lote, 1, p.encima_cabe())
                if not n:
                    app.son("error")
                    app.decir(tr('No puedes cargar con más: llevas {_total} cosas y caben {entero}.').format(_total=(p._total(p.encima())), entero=(AJ.entero('capacidad_encima'))), True)
                    return
                app.son("cesta", vol=0.7)
                if lote not in lotes:
                    app.cerrar(sub)
                app.decir(tr('Te llevas {v}{lower}').format(v=(tr('una ración de ') if info['plato'] else ''), lower=(info['nombre'].lower())) + (tr(", en una fiambrera") if info["plato"] else "")
                          + tr('. Aquí quedan {v}. Llevas encima {_total}.').format(v=(lote['n'] if lote in lotes else 0), _total=(p._total(p.encima()))), True)

            def tirar():
                if lote in lotes:
                    lotes.remove(lote)
                app.son("cesta", tono=0.75, vol=0.6)
                app.cerrar(sub)
                app.decir(tr('Tiras {lower} a la basura.').format(lower=(info['nombre'].lower())), True)
            ops = []
            if info["comestible"]:
                ops.append(Opcion((tr("Beber") if info["bebida"] else tr("Comer")) + (tr(" una ración") if info["plato"] else tr(" una unidad")), comer, callado=True,
                                  ayuda=tr('{capitalize}. El hambre y la sed solo cuentan con la vida realista activada; la salud y el ánimo, siempre.').format(capitalize=(C.efecto_txt(info).capitalize()))))
                ops.append(Opcion(tr("Llevarte una encima, para comer fuera"), llevar, callado=True, ayuda=tr("Se sigue caducando el mismo día. Se come desde el móvil, en Inventario.")))
            else:
                ops.append(Opcion(tr("Es para cocinar: se usa en las recetas"), ayuda=p.producto_ayuda(p.producto(lote["id"]))))
                ops.append(Opcion(tr("Llevarte una unidad encima"), llevar, callado=True, ayuda=tr("Para llevarla a la cocina de otra casa tuya.")))
            ops.append(Opcion(tr("Tirarlo todo a la basura"), tirar, callado=True, ayuda=tr("Tiras todo lo que queda de esto, de una vez y sin preguntar. No se puede deshacer.")))
            sub = Menu(app, lambda: p.lote_txt(lote) if lote in lotes else info["nombre"], ops)
            app.abrir(sub)
        return abrir

    def ops():
        lista = [Opcion(lambda lote=lote: p.lote_txt(lote), acciones(lote),
                        ayuda=tr("Con Intro eliges qué hacer con ello: comerlo, si se come tal cual, llevarte una encima o tirarlo.")) for lote in sorted(p.de_sitio(casa, sitio), key=lambda x: (int(x.get("cad") or 10 ** 9), p.lote_info(x)["nombre"]))]
        return lista or [Opcion(tr('{nombre} está vacía').format(nombre=(nombre)), ayuda=tr("Lo que compres para casa en una tienda de comida se guarda desde el menú de la cocina, con Guardar lo que llevas encima."))]
    app.abrir(Menu(app, lambda: tr('{nombre}: {_total} de {sitio_capacidad}').format(nombre=(nombre), _total=(p._total(p.de_sitio(casa, sitio))), sitio_capacidad=(p.sitio_capacidad(casa, sitio))), ops, intro=aviso or None))


def menu_recetas(p, casa):
    app = p.app

    def hacer(r):
        def f():
            faltan = p.receta_falta(casa, r)
            if faltan:
                app.son("error")
                app.decir(tr('Para {lower} te falta {_junta}.').format(lower=(r['nombre'].lower()), _junta=(_junta(faltan))), True)
                return
            app.cerrar(m)
            app.abrir(Cocinando(p, casa, r))
        return f

    def ops():
        lista = []
        for r in sorted(C.recetas(p), key=lambda r: bool(p.receta_falta(casa, r))):
            faltan = p.receta_falta(casa, r)
            lista.append(Opcion(tr('{nombre}: {_cuantos}, {int} minutos. ').format(nombre=(r['nombre']), _cuantos=(_cuantos(int(C._num(r, 'raciones', 1)), 'ración', 'raciones')), int=(int(C._num(r, 'minutos', 20))))
                                + (tr("Tienes todo") if not faltan else tr('Te falta {_junta}').format(_junta=(_junta(faltan)))), hacer(r), ayuda=p.receta_txt(r), callado=True))
        return lista
    m = Menu(app, tr('Qué cocinas. Mano en la cocina: nivel {nivel_cocina} de 10').format(nivel_cocina=(C.nivel_cocina(p))), ops, intro=tr("Primero, las que puedes hacer ahora"))
    app.abrir(m)


class Cocinando:
    """Mientras cocinas: se oye picar, la sartén o la olla, y el plato en la mesa. Dura unos segundos; lo que tarda de verdad
    es tiempo del juego, que pasa al terminar."""
    pausa_mundo = True
    cerrado_al_final = True

    def __init__(self, p, casa, receta, rng=None):
        self.p, self.app, self.casa, self.r = p, p.app, casa, receta
        self.rng = rng or random
        fuego = C.FUEGOS.get(receta.get("fuego"), C.FUEGOS["hervir"])[1]
        self.pasos = [(0.0, "cocina_cortar")] + ([(1.7, fuego)] if fuego else [])
        self.dura = 4.3 if fuego else 1.9
        self.t = 0.0
        self.hecho = False
        self.texto = None

    def al_entrar(self):
        self.app.decir(tr('Te pones a cocinar {lower}: {int} minutos.').format(lower=(self.r['nombre'].lower()), int=(int(C._num(self.r, 'minutos', 20)))), True)

    def tecla(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
            self.t = self.dura                                   # quien no quiera esperar lo oye de corrido
        else:
            md = getattr(self.app, "mando", None)                # con mando se dice su botón: A o Equis
            intro = md.boton_pantalla(pygame.K_RETURN, tr("Intro")) if md is not None else tr("Intro")
            self.app.decir(tr('Estás cocinando {lower}. {v}, para no esperar.').format(lower=(self.r['nombre'].lower()), v=(intro[0].upper() + intro[1:])), True)

    def actualizar(self, dt):
        if self.hecho:
            return
        while self.pasos and self.t >= self.pasos[0][0]:
            self.app.son(self.pasos.pop(0)[1], vol=0.8)
        self.t += dt
        if self.t >= self.dura:
            self.hecho = True
            self.texto = self.p.cocinar(self.casa, self.r, self.rng)
            if self.texto:
                self.app.son("plato_servido")
            self.app.cerrar(self)

    def cerrado(self):
        if self.texto:
            self.app.decir(self.texto, True)
