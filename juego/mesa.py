"""Juegos de mesa de bares y tabernas: el dominó y los chinos. La siete y media está en sistemas.py.

Todo se juega con menús: cada opción es una jugada posible, y el juego cuenta en voz alta lo que hay en la mesa.
"""
from .i18n import tr
import random


def _fichas():
    return [(a, b) for a in range(7) for b in range(a, 7)]


def _nombre(f):
    return tr('{v} doble').format(v=(f[0])) if f[0] == f[1] else f"{f[1]} {f[0]}"


def _puntos(mano):
    return sum(a + b for a, b in mano)


def domino(p, Menu, Opcion, azar=None):
    """Una mano de dominó contra un rival. Gana quien se queda sin fichas; si se cierra, quien tenga menos puntos."""
    azar = azar or random
    app = p.app
    j = p.j
    est = {"fin": True, "apuesta": 0, "yo": [], "rival": [], "pozo": [], "izq": None, "der": None}

    def mesa_txt():
        if est["izq"] is None:
            return tr("La mesa está vacía.")
        return tr('En la mesa, los extremos son {izq} y {der}. Te quedan {len} fichas; a tu rival, {len2}; en el pozo, {len3}.').format(izq=(est['izq']), der=(est['der']), len=(len(est['yo'])), len2=(len(est['rival'])), len3=(len(est['pozo'])))

    def jugables(mano):
        if est["izq"] is None:
            return [(f, "der") for f in mano]
        lista = []
        for f in mano:
            if est["izq"] in f:
                lista.append((f, "izq"))
            if est["der"] in f and est["der"] != est["izq"]:
                lista.append((f, "der"))
        return lista

    def poner(mano, f, lado):
        mano.remove(f)
        if est["izq"] is None:
            est["izq"], est["der"] = f
        elif lado == "izq":
            est["izq"] = f[0] if f[1] == est["izq"] else f[1]
        else:
            est["der"] = f[0] if f[1] == est["der"] else f[1]

    def acabar(gano, texto):
        est["fin"] = True
        if gano is None:
            p.dar_dinero(est["apuesta"])
            app.decir(texto + tr(' Empate: recuperas tus {apuesta} euros.').format(apuesta=(est['apuesta'])), True)
        elif gano:
            p.dar_dinero(est["apuesta"] * 2)
            app.son("dinero")
            app.decir(texto + tr(' Ganas {v} euros. Tienes {dinero}.').format(v=(est['apuesta'] * 2), dinero=(j.dinero)), True)
        else:
            app.son("error")
            app.decir(texto + tr(' Pierdes {apuesta} euros. Tienes {dinero}.').format(apuesta=(est['apuesta']), dinero=(j.dinero)), True)
        m.refrescar(False)

    def cierre():
        mios, suyos = _puntos(est["yo"]), _puntos(est["rival"])
        acabar(None if mios == suyos else mios < suyos, tr('La partida se cierra: nadie puede poner. Tú te quedas con {mios} puntos y tu rival con {suyos}.').format(mios=(mios), suyos=(suyos)))

    def turno_rival(antes):
        """Juega el rival hasta que le toque al jugador. Devuelve lo que ha pasado, para decirlo."""
        relato = antes
        while True:
            jug = jugables(est["rival"])
            while not jug and est["pozo"]:
                est["rival"].append(est["pozo"].pop())
                relato += tr(" Tu rival roba.")
                jug = jugables(est["rival"])
            if jug:
                f, lado = max(jug, key=lambda x: x[0][0] + x[0][1])          # suelta primero las que más pesan
                poner(est["rival"], f, lado)
                app.son("menu_mover")
                relato += tr(' Tu rival pone el {_nombre}.').format(_nombre=(_nombre(f)))
                if not est["rival"]:
                    acabar(False, relato + tr(" Se queda sin fichas."))
                    return
            else:
                relato += tr(" Tu rival pasa.")
            if jugables(est["yo"]) or est["pozo"]:
                break
            if not jug:                                                       # ninguno de los dos puede: cierre
                app.decir(relato, True)
                cierre()
                return
            relato += tr(" Tú no puedes poner y no queda pozo: pasas.")
        app.decir(relato + " " + mesa_txt(), True)
        m.refrescar(False)

    def jugar(f, lado):
        def fn():
            if est["fin"]:
                return
            poner(est["yo"], f, lado)
            app.son("menu_mover")
            if not est["yo"]:
                acabar(True, tr('Pones el {_nombre} y te quedas sin fichas.').format(_nombre=(_nombre(f))))
                return
            turno_rival(tr('Pones el {_nombre}.').format(_nombre=(_nombre(f))))
        return fn

    def robar():
        if est["fin"] or not est["pozo"]:
            return
        f = est["pozo"].pop()
        est["yo"].append(f)
        app.son("recoger")
        if jugables(est["yo"]) or est["pozo"]:
            app.decir(tr('Robas el {_nombre}.').format(_nombre=(_nombre(f))) + ("" if jugables(est["yo"]) else tr(" Sigue sin valerte.")), True)
            m.refrescar(False)
        else:
            turno_rival(tr('Robas el {_nombre}, no te vale y no queda pozo: pasas.').format(_nombre=(_nombre(f))))

    def apostar(n):
        def fn():
            if not est["fin"] or not p.pagar(n):
                return
            fichas = _fichas()
            azar.shuffle(fichas)
            est.update({"fin": False, "apuesta": n, "yo": sorted(fichas[:7]), "rival": fichas[7:14], "pozo": fichas[14:], "izq": None, "der": None})
            app.decir(tr("Repartidas siete fichas a cada uno. Empiezas tú. Tus fichas: ") + ", ".join(_nombre(f) for f in est["yo"]) + ".", True)
            m.refrescar(False)
        return fn

    def ops():
        if est["fin"]:
            return [Opcion(tr('Jugar una mano por {n} euros').format(n=(n)), apostar(n),
                           ayuda=tr("Dominó de dos, con las veintiocho fichas. Cada uno pone por turno una ficha que case con uno de los dos extremos de la mesa. "
                                 "Si no tienes ninguna, robas del pozo hasta que te valga una. Gana quien se queda sin fichas; si nadie puede poner, quien tenga menos puntos en la mano."))
                    for n in (20, 100)] + [Opcion(tr("Levantarte de la mesa"), lambda: app.cerrar(m))]
        lista = [Opcion(mesa_txt, ayuda=tr("Los dos números a los que se puede casar una ficha, y cuántas fichas quedan a cada uno."))]
        for f, lado in jugables(est["yo"]):
            donde = "" if est["izq"] is None else tr(', junto al {v}').format(v=(est['izq'] if lado == 'izq' else est['der']))
            lista.append(Opcion(tr('Poner el {_nombre}{donde}').format(_nombre=(_nombre(f)), donde=(donde)), jugar(f, lado),
                                ayuda=tr("La pones en ese extremo de la mesa y juega tu rival. Si te quedas sin fichas, ganas el doble de lo apostado.")))
        if not jugables(est["yo"]) and est["pozo"]:
            lista.append(Opcion(tr("Robar una ficha del pozo"), robar, ayuda=tr("No tienes ninguna que case. Coges una del pozo; si tampoco vale, vuelve a robar.")))
        lista.append(Opcion(lambda: tr("Tus fichas: ") + ", ".join(_nombre(f) for f in est["yo"]),
                            ayuda=tr("Las que te quedan en la mano. Al cerrarse la partida, gana quien sume menos puntos en ellas.")))
        return lista
    m = Menu(app, lambda: tr('Dominó. Tienes {dinero} euros').format(dinero=(j.dinero)), ops, intro=tr("Elige cuánto os jugáis"))
    app.abrir(m)
    return m, est


def chinos(p, Menu, Opcion, azar=None):
    """Los chinos: cada uno esconde de cero a tres monedas en el puño y dice cuántas hay entre los dos."""
    azar = azar or random
    app = p.app
    j = p.j
    est = {"fase": "apuesta", "apuesta": 0, "mias": 0}

    def apostar(n):
        def fn():
            if p.pagar(n):
                est.update({"fase": "esconder", "apuesta": n})
                app.decir(tr("Cierra el puño. ¿Cuántas monedas escondes?"), True)
                m.refrescar(False)
        return fn

    def esconder(n):
        def fn():
            est.update({"fase": "decir", "mias": n})
            app.son("menu_mover")
            app.decir(tr('Escondes {n}. Ahora di cuántas hay entre los dos puños.').format(n=(n)), True)
            m.i = 0
            m.refrescar(False)
        return fn

    def decir(total):
        def fn():
            suyas = azar.randint(0, 3)
            suyo = azar.choice([x for x in range(suyas, suyas + 4) if x != total])     # el rival nunca repite tu número
            real = est["mias"] + suyas
            relato = tr('Dices {total}. Tu rival dice {suyo}. Abrís los puños: tú {mias}, tu rival {suyas}. Son {real}.').format(total=(total), suyo=(suyo), mias=(est['mias']), suyas=(suyas), real=(real))
            if total == real:
                p.dar_dinero(est["apuesta"] * 2)
                app.son("dinero")
                app.decir(relato + tr(' Aciertas y ganas {v} euros. Tienes {dinero}.').format(v=(est['apuesta'] * 2), dinero=(j.dinero)), True)
                est["fase"] = "apuesta"
            elif suyo == real:
                app.son("error")
                app.decir(relato + tr(' Acierta tu rival. Pierdes {apuesta} euros. Tienes {dinero}.').format(apuesta=(est['apuesta']), dinero=(j.dinero)), True)
                est["fase"] = "apuesta"
            else:
                app.decir(relato + tr(" No acierta nadie: otra ronda con la misma apuesta. ¿Cuántas escondes?"), True)
                est["fase"] = "esconder"
            m.i = 0
            m.refrescar(False)
        return fn

    def ops():
        if est["fase"] == "apuesta":
            return [Opcion(tr('Jugar por {n} euros').format(n=(n)), apostar(n), ayuda=tr("Cada uno esconde en el puño de cero a tres monedas y dice cuántas cree que hay entre los dos. "
                           "Quien acierta el total se lleva la apuesta. Si no acierta nadie, se repite.")) for n in (10, 50)] + [Opcion(tr("Levantarte de la mesa"), lambda: app.cerrar(m))]
        if est["fase"] == "esconder":
            return [Opcion(tr('Esconder {n} {v}').format(n=(n), v=(tr('moneda') if n == 1 else tr('monedas'))), esconder(n),
                           ayuda=tr("Las que guardas en el puño. Tu rival no las ve. Después dices cuántas hay entre los dos.")) for n in range(4)]
        return [Opcion(tr('Decir {t}').format(t=(t)), decir(t), ayuda=tr("Tu apuesta por el total de los dos puños. Si aciertas, ganas el doble de lo apostado; si acierta tu rival, lo pierdes; si nadie, se repite."))
                for t in range(est["mias"], est["mias"] + 4)]
    m = Menu(app, lambda: tr('Los chinos. Tienes {dinero} euros').format(dinero=(j.dinero)), ops, intro=tr("Elige cuánto os jugáis"))
    app.abrir(m)
    return m, est
