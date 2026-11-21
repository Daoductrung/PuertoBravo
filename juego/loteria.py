"""La Lotería de la Comarca: boletos con número, un sorteo cada día a las nueve de la noche, y a comprobar si ha tocado.

- Cada boleto lleva un número de cinco cifras. Se compran en las administraciones de lotería, donde además puedes pedir
  tu número, y en tiendas, bares y tabernas, que tienen tres números colgados cada día.
- El sorteo es a las nueve de la noche. Lo que compres antes juega esa noche; lo que compres después, la siguiente.
- El juego dice el número que ha salido, pero no si te ha tocado: los boletos se comprueban en el móvil o en cualquier
  sitio donde se vendan, y los premios se cobran allí. Los grandes, solo en una administración.
- Se premia por las últimas cifras: una, el reintegro; dos, tres y cuatro, cada vez más; las cinco, el bote, que crece
  cada día que nadie lo acierta.
"""
from .i18n import tr
import random

from .menus import EntradaTexto, Menu, Opcion

PRECIO = 10
HORA_SORTEO = 21 * 60            # minutos del día
CIFRAS = 5
TOPE_BOLETOS = 5                 # por sorteo
PREMIOS = {1: 10, 2: 60, 3: 600, 4: 6000}          # por cuántas cifras del final coinciden; las cinco son el bote
BOTE_INICIAL = 20000
BOTE_CRECE = 2500
CADUCA = 7                       # días para comprobar y cobrar un boleto
PAGA_TIENDA = 600                # lo más que paga una tienda o un bar; lo demás, en una administración
VENDEN = ("loteria", "tienda", "bar", "taberna")
HISTORIA = 7


def cifras(n):
    """El número, cifra a cifra, para que el lector no diga cuarenta y siete mil doce."""
    return " ".join(str(n).zfill(CIFRAS))


def sorteo_abierto(p):
    """El número del sorteo en el que entra un boleto comprado ahora: el de hoy, o el de mañana si ya se ha sorteado."""
    return p.dia if p.reloj < HORA_SORTEO else p.dia + 1


def ultimo_celebrado(p):
    return p.dia if p.reloj >= HORA_SORTEO else p.dia - 1


def cuando_txt(p, sorteo=None):
    sorteo = sorteo_abierto(p) if sorteo is None else sorteo
    return tr("esta noche a las nueve") if sorteo == p.dia else tr("mañana a las nueve de la noche") if sorteo == p.dia + 1 else tr('el día {sorteo} a las nueve de la noche').format(sorteo=(sorteo))


def _azar(p, *clave):
    return random.Random(f"{p.j.semilla}-loteria-" + "-".join(str(c) for c in clave))


def premiado(p, sorteo):
    """El número que sale en un sorteo. Es propio de cada partida y no cambia aunque cargues la partida otra vez."""
    return str(_azar(p, sorteo).randrange(10 ** CIFRAS)).zfill(CIFRAS)


def aciertos(numero, ganador):
    n = 0
    while n < CIFRAS and numero[-1 - n] == ganador[-1 - n]:
        n += 1
    return n


def premio(p, boleto):
    """Lo que vale un boleto ya sorteado: (euros, explicación)."""
    ganador = premiado(p, boleto["sorteo"])
    a = aciertos(boleto["n"], ganador)
    if a >= CIFRAS:
        return int(boleto.get("bote") or p.j.lot_botes.get(str(boleto["sorteo"]), p.precio("loteria_bote", BOTE_INICIAL))), tr("las cinco cifras: el bote")
    if a == 0:
        return 0, tr("sin premio")
    return p.precio(f"loteria_premio_{a}", PREMIOS[a]), tr("la última cifra: el reintegro") if a == 1 else tr('las {v} últimas cifras').format(v=(('dos', 'tres', 'cuatro')[a - 2]))


def colgados(p, l):
    """Los tres números que tiene hoy un vendedor. Cambian con cada sorteo."""
    r = _azar(p, "venta", l.id, sorteo_abierto(p))
    return [str(r.randrange(10 ** CIFRAS)).zfill(CIFRAS) for _ in range(3)]


def boletos_de(p, sorteo):
    return [b for b in p.j.boletos if b["sorteo"] == sorteo]


def pendientes(p):
    """Boletos de sorteos ya celebrados, sin comprobar o con premio por cobrar."""
    return [b for b in p.j.boletos if b["sorteo"] <= ultimo_celebrado(p)]


def comprar(p, numero, l=None):
    j = p.j
    sorteo = sorteo_abierto(p)
    numero = str(numero).zfill(CIFRAS)
    if len(boletos_de(p, sorteo)) >= TOPE_BOLETOS:
        p.app.son("error")
        p.decir(tr('Ya llevas {TOPE_BOLETOS} boletos para el sorteo de {cuando_txt}. No se venden más por persona.').format(TOPE_BOLETOS=(TOPE_BOLETOS), cuando_txt=(cuando_txt(p))), True)
        return False
    if any(b["n"] == numero for b in boletos_de(p, sorteo)):
        p.app.son("error")
        p.decir(tr('Ese número ya lo llevas para ese sorteo: {cifras}.').format(cifras=(cifras(numero))), True)
        return False
    coste = p.precio("boleto_loteria", PRECIO)
    if not p.pagar(coste):
        return False
    j.boletos.append({"n": numero, "sorteo": sorteo, "donde": l.id if l is not None else ""})
    j.lot_bote += coste // 2                                    # la mitad de lo que se juega va al bote
    p.son("caja", cat="interfaz")
    p.decir(tr('Boleto comprado: el {cifras}. Juega en el sorteo de {cuando_txt}. Después compruébalo en el móvil, en Lotería, o donde vendan boletos.').format(cifras=(cifras(numero)), cuando_txt=(cuando_txt(p, sorteo))), True)
    return True


def al_dia(p):
    """Celebra los sorteos que toquen. Se llama cada vez que avanza el reloj, también al dormir o al viajar."""
    j = p.j
    hasta = ultimo_celebrado(p)
    if j.lot_ultimo < 0 or j.lot_ultimo > hasta or hasta - j.lot_ultimo > 30:       # partida nueva o antigua: no se sortea hacia atrás
        j.lot_ultimo = hasta
        return
    while j.lot_ultimo < hasta:
        j.lot_ultimo += 1
        _sortear(p, j.lot_ultimo, callado=j.lot_ultimo < hasta)
    j.boletos = [b for b in j.boletos if b["sorteo"] + CADUCA >= p.dia]              # los boletos viejos caducan


def _sortear(p, sorteo, callado=False):
    j = p.j
    inicial, crece = p.precio("loteria_bote", BOTE_INICIAL), p.precio("loteria_bote_sube", BOTE_CRECE)
    ganador = premiado(p, sorteo)
    tuyos = boletos_de(p, sorteo)
    j.lot_botes[str(sorteo)] = j.lot_bote
    for viejo in [k for k in j.lot_botes if int(k) < sorteo - CADUCA - 1]:
        del j.lot_botes[viejo]
    acertado = any(aciertos(b["n"], ganador) >= CIFRAS for b in tuyos)
    r = _azar(p, "vecinos", sorteo)
    cae = None
    if not acertado and r.random() < 0.06:                       # de vez en cuando le toca a alguien de la comarca
        sitios = [l for l in p.lugares.values() if l.tipo in VENDEN]
        cae = r.choice(sitios) if sitios else None
    if not callado:
        p.son("ruleta", cat="interfaz", vol=0.5)
        p.son("campanadas", cat="interfaz", vol=0.35)
        frase = tr('Sorteo de la lotería. Ha salido el {cifras}.').format(cifras=(cifras(ganador)))
        if cae is not None:
            frase += tr(' El bote, {lot_bote} euros, ha caído en {nombre_lugar}. Mañana empieza otra vez en {inicial}.').format(lot_bote=(j.lot_bote), nombre_lugar=(p.nombre_lugar(cae)), inicial=(inicial))
        elif not acertado:
            frase += tr(' Nadie acierta las cinco cifras: el bote sube a {v} euros.').format(v=(j.lot_bote + crece))
        if tuyos:
            frase += tr(' Llevabas {len} {v}: compruébalos en el móvil, en Lotería.').format(len=(len(tuyos)), v=(tr('boleto') if len(tuyos) == 1 else tr('boletos')))
        p.decir(frase)
    j.lot_bote = inicial if (acertado or cae is not None) else j.lot_bote + crece


def comprobar(p, l=None, hablar=True):
    """Mira los boletos ya sorteados. Los que no tienen premio se tiran; los premiados se cobran si estás donde se puede.

    Devuelve (cobrado, por_cobrar)."""
    j = p.j
    lista = pendientes(p)
    if not lista:
        if hablar:
            esperan = [b for b in j.boletos if b["sorteo"] > ultimo_celebrado(p)]
            p.decir(tr("No tienes boletos por comprobar.") + (tr(' Tienes {len} esperando el sorteo de {cuando_txt}.').format(len=(len(esperan)), cuando_txt=(cuando_txt(p, esperan[0]['sorteo']))) if esperan else ""), True)
        return 0, 0
    frases, cobrado, por_cobrar = [], 0, 0
    tope = p.precio("loteria_paga_tienda", PAGA_TIENDA)
    for b in lista:
        euros, que = premio(p, b)
        ganador = premiado(p, b["sorteo"])
        if euros <= 0:
            j.boletos.remove(b)
            frases.append(tr('El {cifras}, del día {sorteo}: salió el {cifras2}. Sin premio').format(cifras=(cifras(b['n'])), sorteo=(b['sorteo']), cifras2=(cifras(ganador))))
            continue
        puede = l is not None and (l.tipo == "loteria" or euros <= tope)
        if puede:
            j.boletos.remove(b)
            cobrado += euros
            frases.append(tr('El {cifras}, del día {sorteo}: premiado con {euros} euros por {que}. Cobrado').format(cifras=(cifras(b['n'])), sorteo=(b['sorteo']), euros=(euros), que=(que)))
        else:
            por_cobrar += euros
            b["visto"] = True
            donde = tr("Se cobra en una administración de lotería") if euros > tope else tr("Se cobra en una administración de lotería, o en una tienda, un bar o una taberna")
            caduca = b["sorteo"] + CADUCA - p.dia
            frases.append(tr('El {cifras}, del día {sorteo}: premiado con {euros} euros por {que}. {donde}. Caduca en {caduca} {v}').format(cifras=(cifras(b['n'])), sorteo=(b['sorteo']), euros=(euros), que=(que), donde=(donde), caduca=(caduca), v=(tr('día') if caduca == 1 else tr('días'))))
    if cobrado:
        j.stats["loteria"] = j.stats.get("loteria", 0) + cobrado
        p.dar_dinero(cobrado)
        if cobrado >= 6000:
            p.son("mision_ok", cat="interfaz")
    elif not por_cobrar:
        p.app.son("error")
    else:
        p.son("notificacion", cat="interfaz", vol=0.6)
    if hablar:
        p.decir(". ".join(frases) + "." + (tr(' Te llevas {cobrado} euros. Tienes {dinero}.').format(cobrado=(cobrado), dinero=(j.dinero)) if cobrado else ""), True)
    return cobrado, por_cobrar


def estado_txt(p):
    j = p.j
    n = len(boletos_de(p, sorteo_abierto(p)))
    return tr('Próximo sorteo, {cuando_txt}. Bote: {lot_bote} euros. Llevas {n} {v}').format(cuando_txt=(cuando_txt(p)), lot_bote=(j.lot_bote), n=(n), v=(tr('boleto') if n == 1 else tr('boletos')))


def ayuda_premios(p):
    """Lo que se premia, con las cantidades que valen ahora mismo."""
    n = [p.precio(f"loteria_premio_{a}", PREMIOS[a]) for a in (1, 2, 3, 4)]
    return (tr('Se premia por las últimas cifras que coinciden con el número que sale: la última, el reintegro, {v} euros; las dos últimas, {v2}; las tres, {v3}; las cuatro, {v4}; y las cinco, el bote, que crece cada día que nadie lo acierta.').format(v=(n[0]), v2=(n[1]), v3=(n[2]), v4=(n[3])))


def opciones_venta(p, l, refrescar=lambda: None):
    """Lo que ofrece sobre la lotería un sitio donde se venden boletos."""
    app = p.app

    def vender(numero):
        return lambda: (comprar(p, numero, l), refrescar())

    def al_azar():
        llevo = {b["n"] for b in boletos_de(p, sorteo_abierto(p))}
        numero = next(n for n in (str(random.randrange(10 ** CIFRAS)).zfill(CIFRAS) for _ in range(50)) if n not in llevo)
        comprar(p, numero, l)
        refrescar()

    def pedir():
        def aceptar(texto):
            limpio = "".join(c for c in texto if c.isdigit())
            if not limpio or len(limpio) > CIFRAS:
                app.son("error")
                app.decir(tr('Tiene que ser un número de hasta {CIFRAS} cifras.').format(CIFRAS=(CIFRAS)), True)
                return
            comprar(p, limpio, l)
            refrescar()
        app.abrir(EntradaTexto(app, tr('Tu número, de hasta {CIFRAS} cifras').format(CIFRAS=(CIFRAS)), aceptar, maximo=CIFRAS,
                               ayuda=tr("Escribe el número que quieres jugar y pulsa Intro. Si tiene menos de cinco cifras, se completa con ceros delante.")))
    ops = [Opcion(lambda: tr("Lotería. ") + estado_txt(p), ayuda=ayuda_premios(p) + tr(' Cada boleto cuesta {precio} euros y puedes llevar hasta {TOPE_BOLETOS} por sorteo.').format(precio=(p.precio('boleto_loteria', PRECIO)), TOPE_BOLETOS=(TOPE_BOLETOS)))]
    if l.tipo == "loteria":
        ops += [Opcion(tr('Comprar un boleto al azar: {precio} euros').format(precio=(p.precio('boleto_loteria', PRECIO))), al_azar,
                       ayuda=tr('Te dan un número que no lleves ya para el próximo sorteo. Hasta {TOPE_BOLETOS} boletos por sorteo.').format(TOPE_BOLETOS=(TOPE_BOLETOS))),
                Opcion(tr('Comprar un boleto con el número que tú digas: {precio} euros').format(precio=(p.precio('boleto_loteria', PRECIO))), pedir, ayuda=tr("Solo en las administraciones de lotería se puede pedir un número."))]
    else:
        ops += [Opcion(tr('Comprar el boleto {cifras}: {precio} euros').format(cifras=(cifras(n)), precio=(p.precio('boleto_loteria', PRECIO))), vender(n), ayuda=tr("Uno de los tres números que tienen colgados hoy. Para pedir tu número, ve a una administración de lotería."))
                for n in colgados(p, l)]
    ops.append(Opcion(lambda: tr('Comprobar y cobrar tus boletos: tienes {len} ya sorteados').format(len=(len(pendientes(p)))), lambda: (comprobar(p, l), refrescar()),
                      ayuda=tr('Te dicen qué ha salido y te pagan los premios. Aquí pagan hasta {precio} euros; los mayores, en una administración de lotería.').format(precio=(p.precio('loteria_paga_tienda', PAGA_TIENDA)))
                      if l.tipo != "loteria" else tr("Te dicen qué ha salido y te pagan cualquier premio, también el bote.")))
    return ops


def menu_venta(p, l):
    """El menú de la lotería de una tienda, un bar o una taberna."""
    m = Menu(p.app, lambda: tr('Lotería en {nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(p.j.dinero)), lambda: opciones_venta(p, l, lambda: m.refrescar(False)))
    p.app.abrir(m)
    return m


def opcion_en_local(p, l):
    return Opcion(lambda: tr("Lotería: ") + estado_txt(p).lower(), lambda: menu_venta(p, l), ayuda=tr("Comprar boletos para el sorteo de las nueve de la noche, comprobarlos y cobrar los premios pequeños."))


def menu_movil(p):
    """En el móvil: el próximo sorteo, tus boletos, comprobarlos y los últimos números premiados."""
    j = p.j

    def ops():
        lista = [Opcion(tr("Lotería de la Comarca. ") + estado_txt(p), ayuda=ayuda_premios(p) + tr(" Los boletos se compran en las administraciones de lotería, en tiendas, en bares y en tabernas."))]
        for b in sorted(j.boletos, key=lambda b: b["sorteo"]):
            if b["sorteo"] > ultimo_celebrado(p):
                lista.append(Opcion(tr('Boleto {cifras}: juega {cuando_txt}').format(cifras=(cifras(b['n'])), cuando_txt=(cuando_txt(p, b['sorteo']))),
                                    ayuda=tr("Aún no se ha sorteado. El sorteo es a las nueve de la noche.")))
            elif b.get("visto"):
                lista.append(Opcion(tr('Boleto {cifras}, del día {sorteo}: premiado con {v} euros, por cobrar').format(cifras=(cifras(b['n'])), sorteo=(b['sorteo']), v=(premio(p, b)[0])),
                                    ayuda=tr('Cóbralo donde venden boletos antes de que caduque, a los {CADUCA} días del sorteo. Los premios grandes, solo en una administración de lotería.').format(CADUCA=(CADUCA))))
            else:
                lista.append(Opcion(tr('Boleto {cifras}, del día {sorteo}: sorteado, sin comprobar').format(cifras=(cifras(b['n'])), sorteo=(b['sorteo'])),
                                    ayuda=tr('Compruébalo para saber si tiene premio. Caduca a los {CADUCA} días del sorteo.').format(CADUCA=(CADUCA))))
        lista.append(Opcion(lambda: tr('Comprobar tus boletos: {len} ya sorteados').format(len=(len(pendientes(p)))), lambda: (comprobar(p), m.refrescar(False)),
                            ayuda=tr('Te dice si ha tocado. Los premios se cobran donde venden boletos; los de más de {precio} euros, en una administración de lotería.').format(precio=(p.precio('loteria_paga_tienda', PAGA_TIENDA)))))
        for s in range(ultimo_celebrado(p), max(0, ultimo_celebrado(p) - HISTORIA), -1):
            if s >= 1 and s <= j.lot_ultimo:
                lista.append(Opcion(tr('Sorteo del día {s}: salió el {cifras}').format(s=(s), cifras=(cifras(premiado(p, s)))),
                                    ayuda=tr("El número premiado de ese día. Se premian las últimas cifras que coinciden con él.")))
        return lista
    m = Menu(p.app, tr("Lotería"), ops)
    p.app.abrir(m)
    return m
