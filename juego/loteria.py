"""La Lotería de la Comarca: boletos con número, un sorteo cada día a las nueve de la noche, y a comprobar si ha tocado.

- Cada boleto lleva un número de cinco cifras. Se compran en las administraciones de lotería, donde además puedes pedir
  tu número, y en tiendas, bares y tabernas, que tienen tres números colgados cada día.
- El sorteo es a las nueve de la noche. Lo que compres antes juega esa noche; lo que compres después, la siguiente.
- El juego dice el número que ha salido, pero no si te ha tocado: los boletos se comprueban en el móvil o en cualquier
  sitio donde se vendan, y los premios se cobran allí. Los grandes, solo en una administración.
- Se premia por las últimas cifras: una, el reintegro; dos, tres y cuatro, cada vez más; las cinco, el bote, que crece
  cada día que nadie lo acierta.
"""
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
    return "esta noche a las nueve" if sorteo == p.dia else "mañana a las nueve de la noche" if sorteo == p.dia + 1 else f"el día {sorteo} a las nueve de la noche"


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
        return int(boleto.get("bote") or p.j.lot_botes.get(str(boleto["sorteo"]), BOTE_INICIAL)), "las cinco cifras: el bote"
    if a == 0:
        return 0, "sin premio"
    return PREMIOS[a], "la última cifra: el reintegro" if a == 1 else f"las {('dos', 'tres', 'cuatro')[a - 2]} últimas cifras"


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
        p.decir(f"Ya llevas {TOPE_BOLETOS} boletos para el sorteo de {cuando_txt(p)}. No se venden más por persona.", True)
        return False
    if any(b["n"] == numero for b in boletos_de(p, sorteo)):
        p.app.son("error")
        p.decir(f"Ese número ya lo llevas para ese sorteo: {cifras(numero)}.", True)
        return False
    if not p.pagar(PRECIO):
        return False
    j.boletos.append({"n": numero, "sorteo": sorteo, "donde": l.id if l is not None else ""})
    j.lot_bote += PRECIO // 2                                    # la mitad de lo que se juega va al bote
    p.son("caja", cat="interfaz")
    p.decir(f"Boleto comprado: el {cifras(numero)}. Juega en el sorteo de {cuando_txt(p, sorteo)}. Después compruébalo en el móvil, en Lotería, o donde vendan boletos.", True)
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
        frase = f"Sorteo de la lotería. Ha salido el {cifras(ganador)}."
        if cae is not None:
            frase += f" El bote, {j.lot_bote} euros, ha caído en {p.nombre_lugar(cae)}. Mañana empieza otra vez en {BOTE_INICIAL}."
        elif not acertado:
            frase += f" Nadie acierta las cinco cifras: el bote sube a {j.lot_bote + BOTE_CRECE} euros."
        if tuyos:
            frase += f" Llevabas {len(tuyos)} {'boleto' if len(tuyos) == 1 else 'boletos'}: compruébalos en el móvil, en Lotería."
        p.decir(frase)
    j.lot_bote = BOTE_INICIAL if (acertado or cae is not None) else j.lot_bote + BOTE_CRECE


def comprobar(p, l=None, hablar=True):
    """Mira los boletos ya sorteados. Los que no tienen premio se tiran; los premiados se cobran si estás donde se puede.

    Devuelve (cobrado, por_cobrar)."""
    j = p.j
    lista = pendientes(p)
    if not lista:
        if hablar:
            esperan = [b for b in j.boletos if b["sorteo"] > ultimo_celebrado(p)]
            p.decir("No tienes boletos por comprobar." + (f" Tienes {len(esperan)} esperando el sorteo de {cuando_txt(p, esperan[0]['sorteo'])}." if esperan else ""), True)
        return 0, 0
    frases, cobrado, por_cobrar = [], 0, 0
    for b in lista:
        euros, que = premio(p, b)
        ganador = premiado(p, b["sorteo"])
        if euros <= 0:
            j.boletos.remove(b)
            frases.append(f"El {cifras(b['n'])}, del día {b['sorteo']}: salió el {cifras(ganador)}. Sin premio")
            continue
        puede = l is not None and (l.tipo == "loteria" or euros <= PAGA_TIENDA)
        if puede:
            j.boletos.remove(b)
            cobrado += euros
            frases.append(f"El {cifras(b['n'])}, del día {b['sorteo']}: premiado con {euros} euros por {que}. Cobrado")
        else:
            por_cobrar += euros
            b["visto"] = True
            donde = "Se cobra en una administración de lotería" if euros > PAGA_TIENDA else "Se cobra en una administración de lotería, o en una tienda, un bar o una taberna"
            caduca = b["sorteo"] + CADUCA - p.dia
            frases.append(f"El {cifras(b['n'])}, del día {b['sorteo']}: premiado con {euros} euros por {que}. {donde}. Caduca en {caduca} {'día' if caduca == 1 else 'días'}")
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
        p.decir(". ".join(frases) + "." + (f" Te llevas {cobrado} euros. Tienes {j.dinero}." if cobrado else ""), True)
    return cobrado, por_cobrar


def estado_txt(p):
    j = p.j
    n = len(boletos_de(p, sorteo_abierto(p)))
    return f"Próximo sorteo, {cuando_txt(p)}. Bote: {j.lot_bote} euros. Llevas {n} {'boleto' if n == 1 else 'boletos'}"


AYUDA_PREMIOS = ("Se premia por las últimas cifras que coinciden con el número que sale: la última, el reintegro, 10 euros; las dos últimas, 60; las tres, 600; "
                 "las cuatro, 6000; y las cinco, el bote, que crece cada día que nadie lo acierta.")


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
                app.decir(f"Tiene que ser un número de hasta {CIFRAS} cifras.", True)
                return
            comprar(p, limpio, l)
            refrescar()
        app.abrir(EntradaTexto(app, f"Tu número, de hasta {CIFRAS} cifras", aceptar, maximo=CIFRAS,
                               ayuda="Escribe el número que quieres jugar y pulsa Intro. Si tiene menos de cinco cifras, se completa con ceros delante."))
    ops = [Opcion(lambda: "Lotería. " + estado_txt(p), ayuda=AYUDA_PREMIOS + f" Cada boleto cuesta {PRECIO} euros y puedes llevar hasta {TOPE_BOLETOS} por sorteo.")]
    if l.tipo == "loteria":
        ops += [Opcion(f"Comprar un boleto al azar: {PRECIO} euros", al_azar),
                Opcion(f"Comprar un boleto con el número que tú digas: {PRECIO} euros", pedir, ayuda="Solo en las administraciones de lotería se puede pedir un número.")]
    else:
        ops += [Opcion(f"Comprar el boleto {cifras(n)}: {PRECIO} euros", vender(n), ayuda="Uno de los tres números que tienen colgados hoy. Para pedir tu número, ve a una administración de lotería.")
                for n in colgados(p, l)]
    ops.append(Opcion(lambda: f"Comprobar y cobrar tus boletos: tienes {len(pendientes(p))} ya sorteados", lambda: (comprobar(p, l), refrescar()),
                      ayuda=f"Te dicen qué ha salido y te pagan los premios. Aquí pagan hasta {PAGA_TIENDA} euros; los mayores, en una administración de lotería."
                      if l.tipo != "loteria" else "Te dicen qué ha salido y te pagan cualquier premio, también el bote."))
    return ops


def menu_venta(p, l):
    """El menú de la lotería de una tienda, un bar o una taberna."""
    m = Menu(p.app, lambda: f"Lotería en {l.nombre}. Tienes {p.j.dinero} euros", lambda: opciones_venta(p, l, lambda: m.refrescar(False)))
    p.app.abrir(m)
    return m


def opcion_en_local(p, l):
    return Opcion(lambda: "Lotería: " + estado_txt(p).lower(), lambda: menu_venta(p, l), ayuda="Comprar boletos para el sorteo de las nueve de la noche, comprobarlos y cobrar los premios pequeños.")


def menu_movil(p):
    """En el móvil: el próximo sorteo, tus boletos, comprobarlos y los últimos números premiados."""
    j = p.j

    def ops():
        lista = [Opcion("Lotería de la Comarca. " + estado_txt(p), ayuda=AYUDA_PREMIOS + " Los boletos se compran en las administraciones de lotería, en tiendas, en bares y en tabernas.")]
        for b in sorted(j.boletos, key=lambda b: b["sorteo"]):
            if b["sorteo"] > ultimo_celebrado(p):
                lista.append(Opcion(f"Boleto {cifras(b['n'])}: juega {cuando_txt(p, b['sorteo'])}"))
            elif b.get("visto"):
                lista.append(Opcion(f"Boleto {cifras(b['n'])}, del día {b['sorteo']}: premiado con {premio(p, b)[0]} euros, por cobrar"))
            else:
                lista.append(Opcion(f"Boleto {cifras(b['n'])}, del día {b['sorteo']}: sorteado, sin comprobar"))
        lista.append(Opcion(lambda: f"Comprobar tus boletos: {len(pendientes(p))} ya sorteados", lambda: (comprobar(p), m.refrescar(False)),
                            ayuda="Te dice si ha tocado. Los premios se cobran donde venden boletos; los de más de 600 euros, en una administración de lotería."))
        for s in range(ultimo_celebrado(p), max(0, ultimo_celebrado(p) - HISTORIA), -1):
            if s >= 1 and s <= j.lot_ultimo:
                lista.append(Opcion(f"Sorteo del día {s}: salió el {cifras(premiado(p, s))}"))
        return lista
    m = Menu(p.app, "Lotería", ops)
    p.app.abrir(m)
    return m
