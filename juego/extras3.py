"""Tercera ampliación: perro compañero, guerras de territorio y bolsa."""
import math
import random

from . import mundo as M
from .entidades import Persona

NOMBRES_PERRO = ["Canela", "Trufa", "Rayo", "Luna", "Chispa", "Coco", "Nube", "Toby"]
BANDAS = ["Los Calaveras", "Los Lagartos", "Los Barrenos", "Los Tiburones", "Los Cuervos"]
EMPRESAS = {
    "naviera": ("Naviera Poniente", 40, "Barcos y mercancías. Estable y aburrida."),
    "minas": ("Minas de Monteferro", 60, "Sube y baja con la huelga minera."),
    "belmonte": ("Grupo Belmonte", 120, "El imperio de Octavio Belmonte. Cara mientras él mande."),
    "conservas": ("Conservas Cala Brava", 15, "Pequeña y muy volátil: puede doblar o hundirse en una semana."),
    "lucero": ("Lucero Tecnología", 85, "La empresa de moda de San Lucero."),
}


# Cómo cobras lo que dan tus negocios cada medianoche.
COBROS = {
    "mano": ("Te lo traen en mano", "Cada medianoche te llega el dinero al bolsillo, estés donde estés."),
    "banco": ("Te lo ingresan en el banco", "Cada medianoche va a tu cuenta del banco, donde además da intereses. Para gastarlo, lo sacas en un banco."),
    "recoger": ("Vas tú a recogerlo", "Se queda en la caja de cada negocio hasta que pases a por él. Yendo en persona te llevas un diez por ciento más. En cada caja caben siete días: lo que pase de ahí se pierde."),
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
        d = Persona("perro", px, py, self.j.perro or "Perro")
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
            return "No tienes perro."
        h = "con el hambre saciada" if j.perro_hambre < 35 else "con algo de hambre" if j.perro_hambre < HAMBRE_AVISO else "con mucha hambre" if j.perro_hambre < 100 else "sin fuerzas de hambre"
        c = "confía en ti del todo" if j.perro_confianza >= 80 else "confía en ti" if j.perro_confianza >= CONFIANZA_MINIMA else "te tiene miedo" if j.perro_confianza >= 15 else "te tiene mucho miedo"
        donde = "Está en casa" if j.perro_en_casa else "Está contigo"
        return f"{j.perro}: {donde}, {h}, y {c}."

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
        for umbral, texto in ((HAMBRE_AVISO, "tiene hambre. Dale de comer: Mayúsculas Y."), (100, "lleva demasiado sin comer y ya no tiene fuerzas para buscar. Dale de comer.")):
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
                self.decir(f"¡Le has dado a {p.nombre}! Gañe y se aparta de ti. Ya no se fía: no te avisará ni buscará nada hasta que hagáis las paces. "
                           "Con caricias, comida y tiempo se le pasa: Mayúsculas Y.", True)
            else:
                self.decir(f"¡Le has dado a {p.nombre}! Gañe y se encoge. Ten cuidado: si le das otra vez, dejará de fiarse de ti.", True)
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
            self.son("muerte_npc", xy=(p.x, p.y), ref=6)
            if de_banda:
                j.banda = max(0, j.banda - 1)
                self.decir(f"Has matado a uno de {j.banda_nombre}, de los tuyos. Quedan {j.banda}.", True)
            else:
                self.decir("Has matado a tu guardaespaldas.", True)
            self.delito(4, "homicidio")
            return
        self.son("dolor_npc", xy=(p.x, p.y), ref=6)
        if p.agravios >= 3:                                      # tres veces ya no es un accidente
            p.tipo = "enemigo"
            p.hostil = True
            p.activo = True
            p.provocado = True
            p.estado = "ataca"
            if de_banda:
                p.de_banda = False
                j.banda = max(0, j.banda - 1)
                p.nombre = f"Desertor de {j.banda_nombre}"
                self.decir(f"Se acabó: uno de {j.banda_nombre} se harta de tus balas y se vuelve contra ti. Quedan {j.banda} en la banda.", True)
            else:
                p.nombre = "Guardaespaldas rebotado"
                self.decir("Se acabó: tu guardaespaldas se harta de tus balas y se vuelve contra ti.", True)
        else:
            self.decir(f"{p.nombre}: " + ("¡Eh, cuidado, que soy de los tuyos!" if p.agravios == 1 else "¡Otra vez! Una más y no respondo."), True)

    def acariciar_perro(self):
        j = self.j
        d = self.perro()
        if d is None:
            return
        if self.t - getattr(d, "t_caricia", -999.0) < 12:
            self.decir(f"{j.perro} sigue a gusto con la caricia de antes. Dale un momento.", True)
            return
        d.t_caricia = self.t
        antes = self.perro_asustado()
        j.perro_confianza = min(100.0, j.perro_confianza + 9.0)
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.45, tono=1.35)
        if antes and not self.perro_asustado():
            self.decir(f"{j.perro} te lame la mano y mueve el rabo. Habéis hecho las paces: vuelve a ir a tu lado.", True)
        elif antes:
            self.decir(f"{j.perro} se deja tocar, con las orejas gachas. Todavía te tiene miedo. Sigue con calma, o dale de comer.", True)
        else:
            self.decir(f"{j.perro} mueve el rabo y se aprieta contra tu pierna.", True)

    def alimentar_perro(self):
        j = self.j
        d = self.perro()
        if d is None:
            return
        if j.objetos.get("pienso", 0) <= 0:
            self.app.son("error")
            self.decir("No te queda pienso. Lo venden en la protectora de animales y en las tiendas.", True)
            return
        if j.perro_hambre < 15:
            self.decir(f"{j.perro} huele el pienso y no lo quiere: no tiene hambre.", True)
            return
        j.objetos["pienso"] -= 1
        antes = self.perro_asustado()
        j.perro_hambre = max(0.0, j.perro_hambre - 60.0)
        j.perro_confianza = min(100.0, j.perro_confianza + 25.0)
        self.son("perro_olfatea", xy=(d.x, d.y), ref=4, maxd=40)
        paces = " Habéis hecho las paces." if antes and not self.perro_asustado() else ""
        self.decir(f"{j.perro} se come la ración con ganas.{paces} Te quedan {j.objetos['pienso']} raciones de pienso.", True)

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
            self.decir("No tienes casa adonde mandarlo. Compra una vivienda, o déjalo en la protectora de animales.", True)
            return False
        self.personas.remove(d)
        if self.objetivo is d:
            self.objetivo = None
        j.perro_en_casa = True
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.6, tono=1.1)
        self.decir((f"{j.perro} se queda en casa. Aquí" if aqui else f"{j.perro} se va trotando a {self.nombre_lugar(casa)}. Allí") + " tiene comida y agua, y se le pasan los sustos. "
                   "Para que vuelva, llama desde el móvil, en Tu perro, o pulsa Mayúsculas Y.", True)
        return True

    def llamar_perro(self):
        j = self.j
        if not j.perro or not j.perro_en_casa:
            return False
        if self.mundo.tipo == "mar":
            self.app.son("error")
            self.decir(f"En mitad del mar, {j.perro} no puede llegar hasta ti.", True)
            return False
        d = self.crear_perro()
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40)
        self.decir(f"{j.perro} llega corriendo y se pone a tu lado.", True)
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
                self.decir(f"{d.nombre} gruñe: {self.situar(e.x, e.y, 'peligro')}.")
                self.app.vibrar(0.3, 0.6, 200)
                return

    def perro_busca(self):
        d = self.perro()
        if d is None:
            if self.j.perro and self.j.perro_en_casa:
                self.decir(f"{self.j.perro} está en casa. Pulsa Mayúsculas Y para llamarlo.", True)
            else:
                self.decir("No tienes perro. Puedes adoptar uno en una protectora de animales.", True)
            return
        if self.perro_asustado():
            self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, vol=0.4, tono=1.8)
            self.decir(f"{d.nombre} no se acerca: te tiene miedo. Haz las paces con caricias o comida, con Mayúsculas Y.", True)
            return
        if self.j.perro_hambre >= 100:
            self.decir(f"{d.nombre} no tiene fuerzas para buscar. Dale de comer, con Mayúsculas Y.", True)
            return
        x, y = self.pos()
        cosas = [o for o in self.objetos if o.dist(x, y) < 600]
        self.son("perro_olfatea", xy=(d.x, d.y), ref=4, maxd=40)
        if not cosas:
            self.decir(f"{d.nombre} olfatea el aire y no encuentra nada por aquí.", True)
            return
        o = min(cosas, key=lambda o: o.dist(x, y))
        self.son("ladrido", xy=(d.x, d.y), ref=4, maxd=40, tono=1.2)
        self.fijar_gps(o.x, o.y, o.nombre, radio=3)
        self.decir(f"{d.nombre} ha olfateado algo: {self.situar(o.x, o.y, o.nombre)}. Te marca el camino.", True)

    # -------------------------------------------------------------- territorios
    def barrios_conquistables(self):
        if self.mundo.tipo != "ciudad":
            return []
        return [b for b in self.mundo.barrios if b["id"] not in self.j.territorios]

    def empezar_conquista(self, b):
        banda = random.choice(BANDAS)
        ls = [l for l in self.mundo.lugares.values() if self.mundo.barrio(l.x, l.y)["id"] == b["id"] and l.tipo not in ("salida", "embarcadero")]
        if len(ls) < 2:
            self.decir("En ese barrio no hay dónde pelear.", True)
            return
        random.shuffle(ls)
        pasos = []
        for k, n in enumerate((3, 4, 5)):
            l = ls[k % len(ls)]
            pasos.append({"tipo": "eliminar", "lugar": l.id,
                          "texto": f"{['Primer', 'Segundo', 'Último'][k]} grupo de {banda}: {n} pandilleros junto a {l.nombre}.",
                          "enemigos": [{"n": n - 1, "tipo": f"Pandillero de {banda}", "arma": random.choice(["pistola", "pistola", "subfusil"]), "salud": 70 + 8 * k},
                                       {"n": 1, "tipo": f"Pandillero de {banda}", "arma": random.choice(["escopeta", "bate", "navaja"]), "salud": 80 + 8 * k}]})
        self._empezar_repetible({"id": "conquista", "titulo": f"Conquista de {b['nombre']}", "lugar": ls[0].id, "territorio": b["id"],
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
        modo = j.cobro_negocios
        if modo == "banco":
            j.banco += total
            j.stats["dinero_ganado"] += total
            self.son("dinero", cat="interfaz", vol=0.6)
            self.decir(f"Tus negocios ingresan {total} euros en tu cuenta del banco. Saldo: {j.banco} euros.")
        elif modo == "recoger":
            llenas = 0
            for l in self.negocios_tuyos():
                tope = int(l.get("ingresos", 0)) * DIAS_CAJA
                j.cajas[l.id] = min(tope, int(j.cajas.get(l.id, 0)) + int(l.get("ingresos", 0)))
                llenas += j.cajas[l.id] >= tope
            en_caja = sum(int(v) for v in j.cajas.values())
            self.decir(f"Tus negocios han hecho {total} euros de caja. Te esperan {en_caja} euros por recoger."
                       + (f" Hay {llenas} con la caja llena: no les cabe más hasta que pases." if llenas else ""))
        else:
            self.dar_dinero(total, "Ingresos de tus negocios")

    def recoger_caja(self, l):
        """Vas tú al negocio: te llevas lo de la caja, con un diez por ciento más por no pagar a quien lo lleva."""
        j = self.j
        n = int(j.cajas.get(l.id, 0))
        if n <= 0:
            self.decir("La caja está vacía. Se llena cada medianoche.", True)
            return 0
        j.cajas[l.id] = 0
        n += n // 10
        self.dar_dinero(n)
        self.decir(f"Recoges la caja de {l.nombre}: {n} euros, con el diez por ciento de más por venir en persona. Tienes {j.dinero}.", True)
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
                self.decir(f"Lo que quedaba en las cajas, {resto} euros, te llega {'a la cuenta' if j.cobro_negocios == 'banco' else 'en mano'}.")
        self.decir(f"{COBROS[j.cobro_negocios][0]}. {COBROS[j.cobro_negocios][1]}", True)

    def ingresos_territorios(self):
        n = len(self.j.territorios)
        if n:
            self.dar_dinero(300 * n, f"Tus {n} territorios te pagan tributo" if n > 1 else "Tu territorio te paga tributo")

    # -------------------------------------------------------------------- bolsa
    def precio_accion(self, ident):
        return float(self.j.bolsa.get(ident, EMPRESAS[ident][1]))

    def mover_bolsa(self):
        j = self.j
        for ident, (nombre, base, _) in EMPRESAS.items():
            p = self.precio_accion(ident)
            vol = 0.22 if ident == "conservas" else 0.07
            p *= 1 + random.uniform(-vol, vol) + (base - p) / base * 0.03
            if ident == "belmonte":
                if "m20" in self.completadas:
                    p = min(p, random.uniform(3, 8))
                elif "m15" in self.completadas:
                    p = min(p, 70)
            if ident == "minas" and "t06" in self.completadas:
                p = max(p, 90 * random.uniform(0.95, 1.1))
            j.bolsa[ident] = round(max(1.0, p), 2)
