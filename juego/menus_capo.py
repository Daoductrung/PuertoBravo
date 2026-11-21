"""Menús de la vida del capo (capo.py): el cajero, blanquear en el casino y el gestor discreto."""
from .i18n import tr
from .menus import Menu, Opcion
from .capo import AJ


def _sacar(p, n):
    j = p.j
    n = j.banco if n is None else min(n, j.banco)
    if n <= 0:
        p.app.son("error")
        p.app.decir(tr("No tienes dinero en el banco."), True)
        return
    j.banco -= n
    j.dinero += n
    p.son("caja", cat="interfaz")
    p.app.decir(tr('El cajero te da {n} euros. Llevas {dinero} y en el banco quedan {banco}.').format(n=(n), dinero=(j.dinero), banco=(j.banco)), True)


def menu_cajero(p):
    app = p.app
    m = Menu(app, lambda: tr('Cajero automático. En el banco tienes {banco} euros y llevas {dinero}').format(banco=(p.j.banco), dinero=(p.j.dinero)),
             [Opcion(tr('Sacar {n} euros').format(n=(n)), (lambda n=n: _sacar(p, n)),
                     ayuda=tr("Pasan del banco a lo que llevas encima, sin comisión. Si en el banco tienes menos, sacas lo que haya.")) for n in (20, 50, 100, 200, 500)] + [Opcion(tr("Volver"), lambda: app.cerrar(m))],
             intro=tr("En el cajero solo se saca dinero. Para ingresar, ve a un banco"))
    app.abrir(m)


def menu_fichas(p):
    app = p.app

    def blanquear(cant):
        def f():
            n, texto = p.blanquear_casino(cant)
            if not n:
                app.son("error")
            else:
                p.son("dinero", cat="interfaz")
            app.decir(texto, True)
            m.refrescar(False)
        return f
    m = Menu(app, lambda: tr('Blanquear en fichas. Dinero sin justificar: {int} euros. Llevas {dinero}').format(int=(int(p.negro())), dinero=(p.j.dinero)),
             lambda: [Opcion(tr('Blanquear {n} euros').format(n=(n)), blanquear(n),
                             ayuda=tr('Usas ese efectivo, pierdes un {entero} por ciento y pasan dos horas. Si llevas menos, tienes menos sin justificar o llegas al tope del día, se blanquea solo lo que se pueda.').format(entero=(AJ.entero('casino_comision')))) for n in (500, 1000, 2500, 5000)] + [Opcion(tr("Volver"), lambda: app.cerrar(m))],
             intro=tr('Compras fichas con efectivo, juegas poco y cobras como premio. Se pierde un {entero} por ciento por el camino, y aquí no se blanquean más de {entero2} euros al día').format(entero=(AJ.entero('casino_comision')), entero2=(AJ.entero('casino_maximo'))))
    app.abrir(m)


def menu_gestor(p):
    app = p.app

    def dar(cant):
        def f():
            texto = p.blanquear_gestor(cant)
            app.decir(texto, True)
            m.refrescar(False)
        return f
    pend = sum(int(g["euros"]) for g in (getattr(p.j, "gestor_pend", None) or []))
    m = Menu(app, lambda: tr('El gestor. Dinero sin justificar: {int} euros. Llevas {dinero}').format(int=(int(p.negro())), dinero=(p.j.dinero)) + (tr('. Tiene tuyos {pend} euros en camino').format(pend=(pend)) if pend else ""),
             lambda: [Opcion(tr('Darle {n} euros en efectivo').format(n=(n)), dar(n),
                             ayuda=tr('Se lo lleva ahora y, a los {dias} días, te ingresa en el banco lo que quede tras su {comision} por ciento. Alguna vez desaparece con el dinero.').format(dias=(AJ.entero('gestor_dias')), comision=(AJ.entero('gestor_comision')))) for n in (AJ.entero("gestor_minimo"), AJ.entero("gestor_minimo") * 2, AJ.entero("gestor_minimo") * 5)]
             + [Opcion(tr("Volver"), lambda: app.cerrar(m))],
             intro=tr('Se queda un {entero} por ciento y, a los {entero2} días, te lo ingresa en el banco, limpio. No siempre es de fiar').format(entero=(AJ.entero('gestor_comision')), entero2=(AJ.entero('gestor_dias'))))
    app.abrir(m)


def opciones_lugar(p, l, menu):
    """Lo que añade la vida del capo al menú de un lugar: cajero, si lo tiene; y, para blanquear, fichas en el casino y el gestor."""
    if not isinstance(menu, Menu) or menu is p or not p.capo_activo():
        return
    extra = []
    if l.get("cajero"):
        extra.append(Opcion(tr("Cajero automático: sacar dinero del banco"), lambda: menu_cajero(p),
                            ayuda=tr("Lo que compras se paga con lo que llevas encima: el dinero del banco hay que sacarlo antes. En el cajero solo se saca.")))
    if p.blanqueo_activo():
        if l.tipo == "casino":
            extra.append(Opcion(tr("Blanquear dinero en fichas"), lambda: menu_fichas(p),
                                ayuda=tr("Para el dinero que no puedes justificar: compras fichas, juegas un poco y cobras como premio. Se pierde algo, y hay tope al día.")))
        if l.tipo in AJ.lista("lugares_gestor"):
            extra.append(Opcion(tr("Hablar con el gestor discreto"), lambda: menu_gestor(p),
                                ayuda=tr("Le das efectivo y te lo devuelve limpio en el banco a los pocos días, quedándose una buena parte. Alguna vez desaparece con el dinero.")))
    for o in extra:
        menu.opciones.insert(max(0, len(menu.opciones) - 1), o)
