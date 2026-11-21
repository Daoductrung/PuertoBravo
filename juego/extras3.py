"""Tercera ampliación: perro compañero, guerras de territorio y bolsa."""
from .i18n import tr
import math
import random

from . import gente as G
from . import mundo as M
from .entidades import Persona

from .bolsa import EMPRESAS                                   # noqa: E402,F401  (la bolsa vive en bolsa.py desde la 1.7.2)


# Cómo cobras lo que dan tus negocios cada medianoche.
COBROS = {
    "mano": (tr("Te lo traen en mano"), tr("Cada medianoche te llega el dinero al bolsillo, estés donde estés.")),
    "banco": (tr("Te lo ingresan en el banco"), tr("Cada medianoche va a tu cuenta del banco, donde además da intereses. Para gastarlo, lo sacas en un banco.")),
    "recoger": (tr("Vas tú a recogerlo"), tr("Se queda en la caja de cada negocio hasta que pases a por él. Yendo en persona te llevas un diez por ciento más. En cada caja caben siete días: lo que pase de ahí se pierde.")),
}
DIAS_CAJA = 7

CONFIANZA_MINIMA = 40.0           # por debajo, el perro te tiene miedo y no trabaja para ti
HAMBRE_AVISO = 70.0
HAMBRE_PERRO_MINUTO = 100.0 / (30 * 60)       # de saciado a sin fuerzas, treinta horas de juego


class Extras3:
    # -------------------------------------------------------------------- perro
    def crear_perro(self):
        x, y = self.pos()
        px, py = self.mundo.punto_libre(x + random.uniform(-2, 2), y + random.uniform(-2, 2))
        self.j.perro_en_casa = False
        d = Persona("perro", px, py, self.j.perro or tr("Perro"))
        d.salud = 9999.0
        d.estado = "sigue"
        d.avisados = set()
        self.personas.append(d)
        return d

    def perro(self):
        return next((p for p in self.personas if p.tipo == "perro"), None)

    # Lo que hace falta saber del perro: hambre de 0 a 100 y confianza de 0 a 100. Con poca confianza no trabaja para ti.
    def perro_asustado(self):
        return self.j.perro_confianza < CONFIANZA_MINIMA

    def perro_txt(self):
        j = self.j
        if not j.perro:
            return tr("No tienes perro.")
        h = tr("con el hambre saciada") if j.perro_hambre < 35 else tr("con algo de hambre") if j.perro_hambre < HAMBRE_AVISO else tr("con mucha hambre") if j.perro_hambre < 100 else tr("sin fuerzas de hambre")
        c = tr("confía en ti del todo") if j.perro_confianza >= 80 else tr("confía en ti") if j.perro_confianza >= CONFIANZA_MINIMA else tr("te tiene miedo") if j.perro_confianza >= 15 else tr("te tiene mucho miedo")
        donde = tr("Está en casa") if j.perro_en_casa else tr("Está contigo")
        return tr('{perro}: {donde}, {h}, y {c}.').format(perro=(j.perro), donde=(donde), h=(h), c=(c))

    def pasar_perro(self, minutos):
        """El tiempo del juego para el perro: le entra hambre, y el miedo se le va pasando."""
        j = self.j
        if not j.perro or minutos <= 0:
            return
        if j.perro_en_casa:                                      # en casa tiene su comida y está tranquilo
            j.perro_hambre = max(0.0, j.perro_hambre - minutos * 0.5)
            j.perro_confianza = min(100.0, j.perro_confianza + minutos * 10.0 / 60)
            return
        antes = j.perro_hambre
        j.perro_hambre = min(100.0, j.perro_hambre + minutos * HAMBRE_PERRO_MINUTO)
        if j.perro_hambre < 100:
            j.perro_confianza = min(100.0, j.perro_confianza + minutos * 3.0 / 60)
        for umbral, texto in ((HAMBRE_AVISO, tr("tiene hambre. Dale de comer: Mayúsculas Y.")), (100, tr("lleva demasiado sin comer y ya no tiene fuerzas para buscar. Dale de comer."))):
            if antes < umbral <= j.perro_hambre:
                d = self.perro()
                if d is not None:
                    self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.5, tono=1.7)
                self.decir(f"{j.perro} {texto}")

    def herir_amigo(self, p, dano):
        """Le has dado a tu perro o a uno de los tuyos. Con el fuego amigo quitado, no pasa nada."""
        j = self.j
        if not self.cfg["fuego_amigo"]:
            return
        if self.objetivo is p:
            self.objetivo = None
        if p.tipo == "perro":
            j.perro_confianza = max(0.0, j.perro_confianza - 35.0)
            self.son("ladrido", xy=(p.x, p.y), ref=5, maxd=50, vol=0.9, tono=1.8)       # un gañido agudo
            self.app.vibrar(0.5, 0.5, 250)
            if self.perro_asustado():
                self.decir(tr('¡Le has dado a {nombre}! Gañe y se aparta de ti. Ya no se fía: no te avisará ni buscará nada hasta que hagáis las paces. Con caricias, comida y tiempo se le pasa: Mayúsculas Y.').format(nombre=(p.nombre)), True)
            else:
                self.decir(tr('¡Le has dado a {nombre}! Gañe y se encoge. Ten cuidado: si le das otra vez, dejará de fiarse de ti.').format(nombre=(p.nombre)), True)
            return
        if self.t - getattr(p, "t_agravio", -999.0) > 120:        # con el tiempo se olvida
            p.agravios = 0
        p.agravios = getattr(p, "agravios", 0) + 1
        p.t_agravio = self.t
        p.salud -= dano
        de_banda = getattr(p, "de_banda", False)
        if p.salud <= 0:
            p.muerto = True
            p.t_estado = self.t
            self.son("muerte_npc", xy=(p.x, p.y), ref=6, tono=p.tono)
            if de_banda:
                j.banda = max(0, j.banda - 1)
                self.banda_quitar_ficha(getattr(p, "bid", None))
                self.decir(tr('Has matado a uno de {banda_nombre}, de los tuyos. Quedan {banda}.').format(banda_nombre=(j.banda_nombre), banda=(j.banda)), True)
            else:
                self.decir(tr("Has matado a tu guardaespaldas."), True)
            self.delito(4, "homicidio")
            return
        self.son("dolor_npc", xy=(p.x, p.y), ref=6, tono=p.tono)
        if p.agravios >= 3:                                      # tres veces ya no es un accidente
            p.tipo = "enemigo"
            p.hostil = True
            p.activo = True
            p.provocado = True
            p.estado = "ataca"
            if de_banda:
                p.de_banda = False
                j.banda = max(0, j.banda - 1)
                self.banda_quitar_ficha(getattr(p, "bid", None))
                p.nombre = tr('Desertor de {banda_nombre}').format(banda_nombre=(j.banda_nombre))
                self.decir(tr('Se acabó: uno de {banda_nombre} se harta de tus balas y se vuelve contra ti. Quedan {banda} en la banda.').format(banda_nombre=(j.banda_nombre), banda=(j.banda)), True)
            else:
                p.nombre = tr("Guardaespaldas rebotado")
                self.decir(tr("Se acabó: tu guardaespaldas se harta de tus balas y se vuelve contra ti."), True)
        else:
            self.decir(f"{p.nombre}: " + (tr("¡Eh, cuidado, que soy de los tuyos!") if p.agravios == 1 else tr("¡Otra vez! Una más y no respondo.")), True)

    def acariciar_perro(self):
        j = self.j
        d = self.perro()
        if d is None:
            return
        if self.t - getattr(d, "t_caricia", -999.0) < 12:
            self.decir(tr('{perro} sigue a gusto con la caricia de antes. Dale un momento.').format(perro=(j.perro)), True)
            return
        d.t_caricia = self.t
        antes = self.perro_asustado()
        j.perro_confianza = min(100.0, j.perro_confianza + 9.0)
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.45, tono=1.35)
        if antes and not self.perro_asustado():
            self.decir(tr('{perro} te lame la mano y mueve el rabo. Habéis hecho las paces: vuelve a ir a tu lado.').format(perro=(j.perro)), True)
        elif antes:
            self.decir(tr('{perro} se deja tocar, con las orejas gachas. Todavía te tiene miedo. Sigue con calma, o dale de comer.').format(perro=(j.perro)), True)
        else:
            self.decir(tr('{perro} mueve el rabo y se aprieta contra tu pierna.').format(perro=(j.perro)), True)

    def alimentar_perro(self):
        j = self.j
        d = self.perro()
        if d is None:
            return
        if j.objetos.get("pienso", 0) <= 0:
            self.app.son("error")
            self.decir(tr("No te queda pienso. Lo venden en la protectora de animales y en las tiendas."), True)
            return
        if j.perro_hambre < 15:
            self.decir(tr('{perro} huele el pienso y no lo quiere: no tiene hambre.').format(perro=(j.perro)), True)
            return
        j.objetos["pienso"] -= 1
        antes = self.perro_asustado()
        j.perro_hambre = max(0.0, j.perro_hambre - 60.0)
        j.perro_confianza = min(100.0, j.perro_confianza + 25.0)
        self.son("perro_olfatea", xy=(d.x, d.y), ref=4, maxd=40)
        paces = tr(" Habéis hecho las paces.") if antes and not self.perro_asustado() else ""
        self.decir(tr('{perro} se come la ración con ganas.{paces} Te quedan {pienso} raciones de pienso.').format(perro=(j.perro), paces=(paces), pienso=(j.objetos['pienso'])), True)

    def casa_del_perro(self):
        """La vivienda tuya adonde va el perro: la de esta localidad si la hay, o la primera que tengas."""
        casas = [l for l in (self.lugares.get(pid) for pid in self.j.propiedades) if l is not None and l.tipo == "casa"]
        return next((l for l in casas if l.mapa == self.mundo.id), casas[0] if casas else None)

    def mandar_perro_a_casa(self, casa=None):
        j = self.j
        d = self.perro()
        aqui = casa is not None
        casa = casa or self.casa_del_perro()
        if d is None:
            return False
        if casa is None:
            self.app.son("error")
            self.decir(tr("No tienes casa adonde mandarlo. Compra una vivienda, o déjalo en la protectora de animales."), True)
            return False
        self.personas.remove(d)
        if self.objetivo is d:
            self.objetivo = None
        j.perro_en_casa = True
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.6, tono=1.1)
        self.decir((tr('{perro} se queda en casa. Aquí').format(perro=(j.perro)) if aqui else tr('{perro} se va trotando a {nombre_lugar}. Allí').format(perro=(j.perro), nombre_lugar=(self.nombre_lugar(casa)))) + tr(" tiene comida y agua, y se le pasan los sustos. "
                   "Para que vuelva, llama desde el móvil, en Tu perro, o pulsa Mayúsculas Y."), True)
        return True

    def llamar_perro(self):
        j = self.j
        if not j.perro or not j.perro_en_casa:
            return False
        if self.mundo.tipo == "mar":
            self.app.son("error")
            self.decir(tr('En mitad del mar, {perro} no puede llegar hasta ti.').format(perro=(j.perro)), True)
            return False
        d = self.crear_perro()
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40)
        self.decir(tr('{perro} llega corriendo y se pone a tu lado.').format(perro=(j.perro)), True)
        return True

    def actualizar_perro(self, d, dt):
        j = self.j
        px, py = self.pos()
        asustado = self.perro_asustado()
        if j.veh:
            d.x, d.y = px, py
        else:
            dist = d.dist(px, py)
            if dist > 50:
                d.x, d.y = self.mundo.punto_libre(px - 1.5, py - 1.5)
            elif asustado:                                       # con miedo te sigue de lejos, sin arrimarse
                if dist > 14:
                    self._andar_hacia(d, px, py, 5.0, dt)
            elif dist > 2.5:
                self._andar_hacia(d, px, py, 6.5 if dist > 8 else 3.2, dt)
                d.t_paso -= dt
                if d.t_paso <= 0:
                    d.t_paso = 0.22
                    self.son("paso_hierba0", xy=(d.x, d.y), ref=2, maxd=18, vol=0.5, tono=1.5)
        d.t_voz -= dt
        if d.t_voz > 0:
            return
        d.t_voz = 0.6
        if asustado:
            return
        for e in self.personas:
            if e.hostil and not e.muerto and e.id not in d.avisados and e.dist(px, py) < 32 and (e.activo or e.dist(px, py) < 20):
                d.avisados.add(e.id)
                self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, tono=0.85)
                self.decir(tr('{nombre} gruñe: {situar}.').format(nombre=(d.nombre), situar=(self.situar(e.x, e.y, 'peligro'))))
                self.app.vibrar(0.3, 0.6, 200)
                return

    def perro_busca(self):
        d = self.perro()
        if d is None:
            if self.j.perro and self.j.perro_en_casa:
                self.decir(tr('{perro} está en casa. Pulsa Mayúsculas Y para llamarlo.').format(perro=(self.j.perro)), True)
            else:
                self.decir(tr("No tienes perro. Puedes adoptar uno en una protectora de animales."), True)
            return
        if self.perro_asustado():
            self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.4, tono=1.8)
            self.decir(tr('{nombre} no se acerca: te tiene miedo. Haz las paces con caricias o comida, con Mayúsculas Y.').format(nombre=(d.nombre)), True)
            return
        if self.j.perro_hambre >= 100:
            self.decir(tr('{nombre} no tiene fuerzas para buscar. Dale de comer, con Mayúsculas Y.').format(nombre=(d.nombre)), True)
            return
        x, y = self.pos()
        cosas = [o for o in self.objetos if o.dist(x, y) < 600]
        self.son("perro_olfatea", xy=(d.x, d.y), ref=4, maxd=40)
        if not cosas:
            self.decir(tr('{nombre} olfatea el aire y no encuentra nada por aquí.').format(nombre=(d.nombre)), True)
            return
        o = min(cosas, key=lambda o: o.dist(x, y))
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, tono=1.2)
        self.fijar_gps(o.x, o.y, o.nombre, radio=3)
        self.decir(tr('{nombre} ha olfateado algo: {situar}. Te marca el camino.').format(nombre=(d.nombre), situar=(self.situar(o.x, o.y, o.nombre))), True)

    # -------------------------------------------------------------- territorios
    def barrios_conquistables(self):
        if self.mundo.tipo != "ciudad":
            return []
        return [b for b in self.mundo.barrios if b["id"] not in self.j.territorios]

    def banda_de_barrio(self, b):
        """La banda que manda en un barrio que no es tuyo: la que te lo quitó, o la que dicen los datos del mapa. Puede no haber ninguna."""
        return self.j.barrios_banda.get(b["id"]) or b.get("banda") or self.banda_guerra(b)     # con la guerra en la calle, todos tienen una

    def barrio_dueno_txt(self, b, mapa=None):
        """De quién es un barrio ahora mismo, en una frase: tuyo, de una banda o en guerra. Vacío si no es de nadie."""
        j = self.j
        mapa = mapa or self.mundo
        if self.en_servidor:                                     # en un servidor, los barrios son de las bandas de los jugadores
            g = next((g for g in self.sv["territorios"].get("guerras", []) if g.get("mapa") == mapa.id and g.get("barrio") == b["id"]), None)
            if g:
                return tr('En guerra: {get} se lo disputa a {get2}.').format(get=(g.get('ataca_n', tr('una banda'))), get2=(g.get('defiende_n', 'otra')))
            t = self.sv_dueno_barrio(mapa.id, b["id"])
            if not t:
                return ""
            mia = self.sv.get("banda")
            return tr("Territorio de tu banda.") if mia and mia.get("nombre") == t.get("nombre") else tr('Territorio de la banda {get}.').format(get=(t.get('nombre', '')))
        ms = self.mision
        if b["id"] in j.territorios:
            if j.amenaza and j.amenaza.get("territorio") == b["id"]:
                return tr('En guerra: es territorio tuyo, pero {banda} lo está atacando.').format(banda=(j.amenaza['banda']))
            a = j.reconquista.get("asalto")
            if a and a["barrio"] == b["id"] and a["estado"] == "en_curso":
                return tr('En guerra: es territorio tuyo, pero {v} lo está asaltando.').format(v=(a['bandas'][0]))
            return tr('Territorio tuyo: aquí manda {banda_nombre}.').format(banda_nombre=(j.banda_nombre)) if j.banda_nombre else tr("Territorio tuyo.")
        banda = self.banda_de_barrio(b)
        if ms and ms["def"].get("territorio") == b["id"]:
            return tr('En guerra: se lo estás disputando a {v}.').format(v=(ms['def'].get('banda') or banda or tr('una banda')))
        return tr('Territorio de la banda de {banda}.').format(banda=(banda)) if banda else ""

    def barrio_cambiado(self, bid):
        """¿Ha dejado ese barrio de ser de quien era al empezar la partida? Es tuyo, o de una banda de jugadores, o de otra
        banda que se lo ha quedado. Lo consultan los textos fijos que nombran a la banda de siempre (descripciones del
        barrio y de sus lugares) para no seguir diciendo que manda quien ya no manda."""
        j = self.j
        if self.en_servidor:
            return any(t.get("barrio") == bid for t in self.sv["territorios"].get("barrios", []))
        if bid in j.territorios:
            return True
        ahora = j.barrios_banda.get(bid)
        if not ahora:
            return False
        if not hasattr(self, "_banda_de_serie"):
            self._banda_de_serie = {b["id"]: b.get("banda") for m in self.mapas.values() for b in m.barrios}
        return ahora != self._banda_de_serie.get(bid)

    def desc_localidad(self, mapa):
        """Cómo es una localidad, en una frase: la descripción de su primer barrio, la que toque según quién mande en él ahora."""
        b = mapa.barrios[0]
        return str(b.get("descripcion_conquistado") if b.get("descripcion_conquistado") and self.barrio_cambiado(b["id"]) else b.get("descripcion", ""))

    def barrio_desc(self, b, mapa=None):
        """La descripción de un barrio, con la frase de quién es ahora."""
        desc = b.get("descripcion_conquistado") if b.get("descripcion_conquistado") and self.barrio_cambiado(b["id"]) else b.get("descripcion", "")
        return " ".join(t for t in (str(desc).strip(), self.barrio_dueno_txt(b, mapa)) if t)

    def empezar_conquista(self, b):
        banda = self.banda_de_barrio(b) or random.choice(G.nombres_bandas())
        tipos, refuerzo = G.tipos_de_banda(banda)
        if refuerzo and (self.en_servidor or G.tipo_enemigo(refuerzo).get("vehiculo") not in self.modelos):
            refuerzo = None

        def grupo(clase, n, k, mas, **serie):
            """n pandilleros de un tipo de la banda, más duros en cada asalto. Sin tipos en los datos, los de siempre."""
            t = G.tipo_enemigo(clase)
            if not t:
                return dict(serie, n=n, tipo=tr('Pandillero de {banda}').format(banda=banda), salud=70 + mas + 8 * k)
            return {"n": n, "clase": clase, "tipo": tr('{get} de {banda}').format(get=(t.get('nombre', tr('Pandillero'))), banda=(banda)), "salud": float(t.get("salud", 70)) + 8 * k}
        ls = [l for l in self.mundo.lugares.values() if self.mundo.barrio(l.x, l.y)["id"] == b["id"] and l.tipo not in ("salida", "embarcadero")]
        if len(ls) < 2:
            self.decir(tr("En ese barrio no hay dónde pelear."), True)
            return
        random.shuffle(ls)
        pasos = []
        for k, n in enumerate((3, 4, 5)):
            l = ls[k % len(ls)]
            base, duro = (tipos[0], tipos[-1]) if tipos else ("", "")
            llegan = min(n - 2, int(G.tipo_enemigo(refuerzo).get("ocupantes", 3) or 3)) if refuerzo and k == 2 else 0      # los últimos traen refuerzos en un vehículo
            grupos = [grupo(base, n - 1 - llegan, k, 0, arma=random.choice(["pistola", "pistola", "subfusil"])),
                      grupo(duro, 1, k, 10, arma=random.choice(["escopeta", "bate", "navaja"]))]
            if llegan:
                grupos.append(grupo(refuerzo, llegan, k, 5))
            pasos.append({"tipo": "eliminar", "lugar": l.id,
                          "texto": tr('{v} grupo de {banda}: {n} pandilleros junto a {nombre}.').format(v=([tr('Primer'), tr('Segundo'), tr('Último')][k]), banda=(banda), n=(n), nombre=(l.nombre)) + (tr(" Algunos llegan de refuerzo en un vehículo.") if llegan else ""),
                          "enemigos": [g for g in grupos if g["n"] > 0]})
        self._empezar_repetible({"id": "conquista", "titulo": tr('Conquista de {nombre}').format(nombre=(b['nombre'])), "lugar": ls[0].id, "territorio": b["id"], "banda": banda,
                                 "contador": "conquistas", "pasos": pasos, "recompensa": {"dinero": 2500}})

    # ---------------------------------------------------------------- negocios
    def negocios_tuyos(self):
        return [l for l in (self.lugares.get(pid) for pid in self.j.propiedades) if l is not None and l.tipo == "negocio"]

    def cobro_txt(self):
        return COBROS[self.j.cobro_negocios if self.j.cobro_negocios in COBROS else "mano"][0]

    def repartir_ingresos_negocios(self, total):
        """A medianoche: lo que han dado tus negocios, cobrado como hayas elegido."""
        j = self.j
        if total <= 0:
            return
        embargado = 0
        if not self.en_servidor:                                 # lo que dan cuenta para el impuesto del periodo, y un embargo se queda su parte
            self.hon()["caja"] = self.hon().get("caja", 0) + total
            embargado = self._hon_embargar(total)
            total -= embargado
            if total <= 0:
                return
        modo = j.cobro_negocios
        if modo == "banco":
            j.banco += total
            j.stats["dinero_ganado"] += total
            self.son("dinero", cat="interfaz", vol=0.6)
            self.decir(tr('Tus negocios ingresan {total} euros en tu cuenta del banco. Saldo: {banco} euros.').format(total=(total), banco=(j.banco)))
        elif modo == "recoger":
            llenas = 0
            for l in self.negocios_tuyos():
                tope = max(int(l.get("ingresos", 0)), self.ingreso_negocio(l)) * DIAS_CAJA
                quita = min(embargado, self.ingreso_negocio(l))  # lo embargado no llega a la caja
                embargado -= quita
                j.cajas[l.id] = min(tope, int(j.cajas.get(l.id, 0)) + self.ingreso_negocio(l) - quita)
                llenas += j.cajas[l.id] >= tope
            en_caja = sum(int(v) for v in j.cajas.values())
            self.decir(tr('Tus negocios han hecho {total} euros de caja. Te esperan {en_caja} euros por recoger.').format(total=(total), en_caja=(en_caja))
                       + (tr(' Hay {llenas} con la caja llena: no les cabe más hasta que pases.').format(llenas=(llenas)) if llenas else ""))
        else:
            self.dar_dinero(total, tr("Ingresos de tus negocios"))

    def recoger_caja(self, l):
        """Vas tú al negocio: te llevas lo de la caja, con un diez por ciento más por no pagar a quien lo lleva."""
        j = self.j
        n = int(j.cajas.get(l.id, 0))
        if n <= 0:
            self.decir(tr("La caja está vacía. Se llena cada medianoche."), True)
            return 0
        j.cajas[l.id] = 0
        n += n // 10
        self.dar_dinero(n)
        self.decir(tr('Recoges la caja de {nombre}: {n} euros, con el diez por ciento de más por venir en persona. Tienes {dinero}.').format(nombre=(l.nombre), n=(n), dinero=(j.dinero)), True)
        return n

    def cambiar_cobro(self):
        j = self.j
        orden = list(COBROS)
        j.cobro_negocios = orden[(orden.index(j.cobro_negocios) + 1) % len(orden)] if j.cobro_negocios in orden else "mano"
        if j.cobro_negocios != "recoger":                        # lo que quedaba en las cajas no se pierde
            resto = sum(int(v) for v in j.cajas.values())
            j.cajas = {}
            if resto:
                if j.cobro_negocios == "banco":
                    j.banco += resto
                else:
                    j.dinero += resto
                self.son("dinero", cat="interfaz")
                self.decir(tr('Lo que quedaba en las cajas, {resto} euros, te llega {v}.').format(resto=(resto), v=(tr('a la cuenta') if j.cobro_negocios == 'banco' else tr('en mano'))))
        self.decir(f"{COBROS[j.cobro_negocios][0]}. {COBROS[j.cobro_negocios][1]}", True)

    def ingresos_territorios(self):
        n = len(self.j.territorios)
        if n:
            self.hon_negro(self.precio("tributo_territorio", 300) * n)
            self.dar_dinero(self.precio("tributo_territorio", 300) * n, tr('Tus {n} territorios te pagan tributo').format(n=(n)) if n > 1 else tr("Tu territorio te paga tributo"))

