"""Combate, daños, peatones, nivel de búsqueda y policía."""
import math
import random

import pygame

from . import mundo as M
from .entidades import Objeto, Persona, Vehiculo
from .menus import Dialogo

UMBRAL = [1, 4, 8, 13, 20]
# Cuántas patrullas persiguen como mucho con cada nivel de búsqueda, y cada cuántos segundos llega una nueva.
PATRULLAS = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}
RITMO_PATRULLAS = {1: 9.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0}


class Combate:
    # ------------------------------------------------------------------ armas
    def arma(self):
        return self.armas_d.get(self.j.arma, self.armas_d["punos"])

    def dar_arma(self, ident, balas=0):
        a = self.armas_d.get(ident)
        if not a:
            return
        j = self.j
        if ident not in j.armas:
            j.armas[ident] = {"cargador": a.get("cargador", 0), "reserva": 0}
            n = self.orden_armas.index(ident) + 1
            self.decir(f"Consigues: {a['nombre']}." + (f" Es el arma número {n}." if n <= 9 else " Elígela con la coma o con la tecla I."))
            j.arma = ident
        if a["tipo"] in ("fuego", "explosivo"):
            j.armas[ident]["reserva"] += balas

    def elegir_arma(self, idx, paso=1):
        j = self.j
        if isinstance(idx, str):
            j.arma = idx
        elif idx is None:
            mias = [a for a in self.orden_armas if a in j.armas]
            j.arma = mias[(mias.index(j.arma) + paso) % len(mias)]
        else:
            if idx >= len(self.orden_armas):
                return
            ident = self.orden_armas[idx]
            if ident not in j.armas:
                self.decir(f"No tienes {self.armas_d[ident]['nombre']}.", True)
                return
            j.arma = ident
        a = self.arma()
        self.son("amartillar", vol=0.4, cat="interfaz")
        t = a["nombre"]
        if a["tipo"] in ("fuego", "explosivo"):
            m = j.armas[j.arma]
            t += f", {m['cargador']} balas y {m['reserva']} de reserva"
        self.decir(t, True)

    def capacidad(self, ident):
        """Balas que caben en el cargador de un arma tuya: la mitad más si lleva el cargador ampliado."""
        a = self.armas_d.get(ident) or {}
        n = int(a.get("cargador", 0))
        return int(n * 1.5) if self.j.armas.get(ident, {}).get("ampliado") and a.get("tipo") == "fuego" else n

    def recargar(self):
        j = self.j
        a = self.arma()
        if a["tipo"] not in ("fuego", "explosivo"):
            return
        m = j.armas[j.arma]
        falta = self.capacidad(j.arma) - m["cargador"]
        if falta <= 0:
            self.decir("El cargador está lleno.", True)
        elif m["reserva"] <= 0:
            self.app.son("error")
            self.decir("No te queda munición de reserva.", True)
        else:
            n = min(falta, m["reserva"])
            m["cargador"] += n
            m["reserva"] -= n
            j.t_ataque = 0.9
            self.son("recarga", vol=0.7)

    # --------------------------------------------------------------- objetivos
    def _objetivos(self, todos=False):
        x, y = self.pos()
        lista = []
        for p in self.personas:
            if not p.muerto and (p.hostil or todos) and p.dist(x, y) < 90:
                lista.append(p)
        for v in self.vehiculos:
            if v.muerto or v is self.j.veh:
                continue
            if (v.hostil or v.tag == "objetivo" or (todos and v.ia != "aparcado")) and v.dist(x, y) < 250:
                lista.append(v)
        lista.sort(key=lambda e: e.dist(x, y))
        return lista

    def fijar(self, any_=False, callar=False):
        lista = self._objetivos(any_)
        if not lista:
            self.objetivo = None
            if not callar:
                self.decir("No hay enemigos cerca." if not any_ else "No hay nadie cerca.", True)
            return None
        if self.objetivo in lista:
            self.objetivo = lista[(lista.index(self.objetivo) + 1) % len(lista)]
        else:
            self.objetivo = lista[0]
        o = self.objetivo
        self.t_objetivo = 0.0
        if not callar:
            self.app.vibrar(0.0, 0.5, 60)                   # objetivo fijado
            self.decir("Fijado: " + self.situar(o.x, o.y, o.nombre) + f". {len(lista)} en total.", True)
        return o

    def atacar(self):
        j = self.j
        if j.t_ataque > 0 or self.transicion:
            return
        a = self.arma()
        x, y = self.pos()
        fuego = a["tipo"] == "fuego"
        if a["tipo"] == "explosivo":
            self._lanzar_explosivo(a, x, y)
            return
        if j.veh and not fuego:
            self.decir("Desde el vehículo solo puedes usar armas de fuego.", True)
            j.t_ataque = 0.5
            return
        if fuego:
            m = j.armas[j.arma]
            if m["cargador"] <= 0:
                self.son("sin_balas")
                j.t_ataque = 0.3
                if m["reserva"] > 0:
                    self.recargar()
                else:
                    self.decir("Sin munición.", True)
                return
            m["cargador"] -= 1
            if m.get("silenciador"):                             # con silenciador: un chasquido seco, y nadie se entera
                self.son(a["sonido"], vol=0.3, tono=random.uniform(1.5, 1.6))
            else:
                self.son(a["sonido"], vol=0.75, tono=random.uniform(0.96, 1.04))
                if a.get("ruido", 2) > 0:
                    self._ruido_disparo(x, y)
        else:
            self.son("golpe_aire", vol=0.5)
        j.t_ataque = a["cadencia"]
        o = self.objetivo
        if o is not None and (o.muerto or o.dist(x, y) > max(a["alcance"], 60) * 1.5):
            o = None
        if o is None or (not fuego and o.dist(x, y) > a["alcance"]):
            cand = [e for e in self._objetivos(False) if e.dist(x, y) <= a["alcance"]]
            if not cand and not fuego:
                cand = [p for p in self.personas if not p.muerto and p.tipo not in ("aliado", "perro") and p.dist(x, y) <= a["alcance"]]
            if cand and (self.cfg["punteria"] == "completa" or not fuego):
                o = cand[0]
                if fuego:
                    self.objetivo = o
            elif cand:
                # puntería manual: hay que estar encarado al enemigo
                frente = j.veh.rumbo if j.veh else j.rumbo
                enc = [e for e in cand if abs(M.norm180(M.rumbo_a(e.x - x, e.y - y) - frente)) < 25]
                o = enc[0] if enc else None
        if o is None:
            return
        d = o.dist(x, y)
        if d > a["alcance"]:
            if fuego and self.t - self.t_fuera_alcance > 2.5:
                self.t_fuera_alcance = self.t
                self.decir(f"Fuera de alcance: {M.metros(d)}.")
            return
        prob = a["precision"] * (1.0 - 0.5 * d / a["alcance"]) if fuego else a["precision"]
        if j.veh:
            prob *= 0.75
        if self.cfg["dificultad"] == "facil":
            prob = min(1.0, prob + 0.12)
        prob = max(0.05, min(1.0, prob + 0.012 * self.nivel("punteria") + self.mod_punteria()))
        if getattr(self, "cubierto", None):
            prob *= 0.85                                         # desde detrás de algo se apunta peor
        if random.random() > prob:
            if fuego:
                self.son("bala_impacto", xy=(o.x + random.uniform(-2, 2), o.y + random.uniform(-2, 2)), ref=8, maxd=120, vol=0.6)
            return
        if self.cfg["aviso_acierto"]:                        # has dado: un toque agudo y un golpe corto en el mando
            self.son("tono_objetivo", cat="interfaz", vol=0.45, tono=2.0)
            self.app.vibrar(0.15, 0.8, 90)
        if isinstance(o, Vehiculo):
            self.son("bala_impacto", xy=(o.x, o.y), ref=10, maxd=150)
            self.danar_vehiculo(o, a["dano"] * 0.55)
        else:
            if not fuego:
                self.son(a["sonido"], xy=(o.x, o.y), ref=6)
            self.ganar_xp("punteria", 4)
            self.danar_persona(o, a["dano"])

    def _lanzar_explosivo(self, a, x, y):
        j = self.j
        m = j.armas[j.arma]
        if m["cargador"] <= 0:
            if m["reserva"] > 0:
                m["reserva"] -= 1
                m["cargador"] = 1
            else:
                self.son("sin_balas")
                self.decir(f"No te quedan: {a['nombre']}.", True)
                j.t_ataque = 0.4
                return
        m["cargador"] -= 1
        if m["reserva"] > 0 and a.get("cargador", 1) == 1:
            m["reserva"] -= 1
            m["cargador"] = 1
        j.t_ataque = a["cadencia"]
        o = self.objetivo
        if o is None or o.muerto or o.dist(x, y) > a["alcance"]:
            cand = [e for e in self._objetivos(False) if e.dist(x, y) <= a["alcance"]]
            o = cand[0] if cand else None
        if o is not None:
            tx, ty = o.x, o.y
        else:
            rad = math.radians(j.veh.rumbo if j.veh else j.rumbo)
            tx, ty = x + math.sin(rad) * a["alcance"] * 0.6, y + math.cos(rad) * a["alcance"] * 0.6
        self.son(a["sonido"], vol=0.7)
        d = math.hypot(tx - x, ty - y)
        self.explosiones.append({"t": 0.35 + d / 45.0, "x": tx, "y": ty, "radio": a.get("radio", 8), "dano": a["dano"]})
        self.decir(f"Quedan {m['cargador'] + m['reserva']}.")

    def _estallar(self, e):
        j = self.j
        x, y, r = e["x"], e["y"], e["radio"]
        self.son("explosion", xy=(x, y), ref=30, maxd=400)
        self.delito(3, "uso de explosivos", siempre=self.mundo.policia and random.random() < 0.5)
        for p in list(self.personas):
            if not p.muerto and p.tipo not in ("aliado", "perro"):
                d = p.dist(x, y)
                if d < r:
                    self.danar_persona(p, e["dano"] * (1 - 0.6 * d / r))
                elif p.tipo == "civil" and d < 50:
                    p.estado = "huye"
                    p.t_estado = 12
        for v in list(self.vehiculos):
            d = v.dist(x, y)
            if not v.muerto and d < r + 2:
                self.danar_vehiculo(v, e["dano"] * 1.3 * (1 - 0.5 * d / (r + 2)))
        px, py = self.pos()
        d = math.hypot(px - x, py - y)
        if d < r and not j.veh:
            self.danar_jugador(e["dano"] * 0.5 * (1 - d / r), (x, y))

    def _trato_policia(self):
        """Te han cogido por algo menor: pagar la multa, intentar un soborno o dejarte detener."""
        from .menus import Menu, Opcion
        j = self.j
        app = self.app
        multa = self.coste_multa()
        soborno = int(multa * 0.6)
        prob = max(0.25, min(0.9, 0.45 + j.reputacion / 200.0))

        def fuera(texto):
            app.cerrar(menu)
            for p in self.personas:
                if p.tipo == "policia":
                    p.t_arresto = 0.0
            self.limpiar_busqueda(hablar=False)
            self.decir(texto)

        def pagar():
            j.dinero -= multa
            self.son("dinero", cat="interfaz")
            fuera(f"Pagas {multa} euros de multa. El agente te deja ir y ya no te buscan. Conservas tus armas.")

        def sobornar():
            j.dinero -= soborno
            if random.random() < prob:
                self.son("dinero", cat="interfaz")
                self.cambiar_reputacion(1)
                fuera(f"El agente mira a los lados, se guarda los {soborno} euros y se da la vuelta. Ya no te buscan.")
            else:
                app.cerrar(menu)
                app.son("error")
                self.decir(f"El agente se queda con los {soborno} euros y además te detiene por intento de soborno.")
                self.detener(sin_trato=True)

        def nada():
            app.cerrar(menu)
            self.detener(sin_trato=True)
        self.son("esposas", cat="interfaz", vol=0.5)
        menu = Menu(app, f"Un agente te ha cogido. Búsqueda de nivel {j.estrellas}. Tienes {j.dinero} euros",
                    [Opcion(f"Pagar la multa en el acto: {multa} euros", pagar, ayuda="Pagas, te quitan la búsqueda y te vas. Conservas las armas y no pasas por comisaría."),
                     Opcion(f"Intentar un soborno: {soborno} euros", sobornar,
                            ayuda=f"Más barato, pero puede salir mal: ahora mismo sale bien unas {int(prob * 100)} veces de cada cien, más cuanta más fama tengas. Si sale mal, pierdes ese dinero y te detienen."),
                     Opcion("Dejar que te detengan", nada, ayuda="Lo de siempre: comisaría, una multa mayor y pierdes las armas de fuego.")], escapable=False)
        app.abrir(menu)

    def _ruido_disparo(self, x, y):
        self.delito(0.4, "disparos en la vía pública")
        for p in self.personas:
            if p.tipo == "civil" and not p.muerto and p.estado == "pasea" and p.dist(x, y) < 40:
                p.estado = "huye"
                p.t_estado = 10
                if random.random() < 0.4:
                    self.son("grito", xy=(p.x, p.y), vol=0.6)

    # ------------------------------------------------------------------ daños
    def danar_persona(self, p, dano, atropello=False):
        if p.muerto:
            return
        j = self.j
        p.salud -= dano
        if p.salud <= 0:
            p.muerto = True
            p.t_estado = self.t
            self.son("muerte_npc", xy=(p.x, p.y), ref=6)
            if p.tipo == "civil":
                self.delito(3 if atropello else 4, "atropello" if atropello else "homicidio")
                self.decir("Has atropellado a un peatón." if atropello else f"{p.nombre} cae al suelo.")
            elif p.tipo == "policia":
                self.delito(6, "agresión a un agente", siempre=True)
                self.decir("Policía abatido.")
            else:
                j.stats["enemigos"] += 1
                if p.tag != "evento":
                    self.delito(0.6, None)
                self.decir(f"{p.nombre} abatido.")
            if p.tipo != "civil" and random.random() < 0.6 or random.random() < 0.2:
                o = Objeto("dinero", "Dinero en el suelo", p.x, p.y)
                o.valor = random.randint(20, 120) if p.tipo != "civil" else random.randint(5, 50)
                self.objetos.append(o)
            if self.objetivo is p:
                self.objetivo = None
                if self.cfg["punteria"] == "completa":
                    self.fijar(callar=True)
        else:
            self.son("dolor_npc", xy=(p.x, p.y), ref=6)
            if p.tipo == "civil":
                p.estado = "huye"
                p.t_estado = 12
                self.delito(2, "agresión")
            elif not p.hostil:
                p.hostil = True
                p.estado = "ataca"

    def danar_jugador(self, dano, origen):
        j = self.j
        if self.transicion or dano <= 0 or self.cfg["invulnerable"]:
            return
        dano *= self.dificultad() * (1 - 0.02 * self.nivel("resistencia")) * self.mod_dano()
        if getattr(self, "cubierto", None):
            dano *= 0.3                                          # a cubierto te llega mucho menos
        antes = j.salud
        if j.blindaje > 0:
            abs_ = min(j.blindaje, dano * 0.8)
            j.blindaje -= abs_
            dano -= abs_
            if j.blindaje <= 0:
                self.decir("El chaleco ya no aguanta más.")
        j.salud -= dano
        self.app.vibrar(min(1.0, 0.3 + dano / 40.0), 0.4, 220)
        if origen:
            self.son("dolor", vol=0.7)
        else:
            self.son("dolor", vol=0.5)
        if j.salud <= 0:
            self.morir()
            return
        for umbral in (75, 50, 25):
            if antes > umbral >= j.salud:
                extra = " Pulsa Z para usar un botiquín." if umbral <= 50 and j.objetos.get("botiquin", 0) > 0 else ""
                self.decir(f"Salud {int(j.salud)}.{extra}")
                break

    def danar_vehiculo(self, v, dano):
        if v.muerto or v.ardiendo >= 0:
            return
        antes = v.salud / v.salud_max
        v.salud -= dano
        ahora = v.salud / v.salud_max
        if v is self.j.veh:
            for u in (0.5, 0.25):
                if antes > u >= ahora > 0:
                    self.decir(f"Vehículo al {int(u * 100)} por ciento.")
        elif v.tag == "objetivo":
            for u in (0.75, 0.5, 0.25):
                if antes > u >= ahora > 0:
                    self.decir(f"{v.nombre} al {int(u * 100)} por ciento.")
        if v.salud <= 0:
            v.salud = 0
            v.ardiendo = 0.4 if v.tag == "objetivo" else 4.5
            v.fuego = self.son("fuego", bucle=True, xy=(v.x, v.y), ref=8, maxd=90)
            if v is self.j.veh:
                self.decir("¡El vehículo está ardiendo! ¡Pulsa F para salir, va a explotar!", True)

    def explotar(self, v):
        j = self.j
        x, y = v.x, v.y
        self.son("explosion", xy=(x, y), ref=30, maxd=400)
        self.app.vibrar(1.0, 1.0, 600)
        if v is j.veh:
            self.salir_vehiculo(forzado=True)
            self.danar_jugador(95, (x, y))
        else:
            d = math.hypot(j.x - x, j.y - y) if not j.veh else j.veh.dist(x, y)
            if d < 11:
                if j.veh:
                    self.danar_vehiculo(j.veh, 50 * (1 - d / 11))
                else:
                    self.danar_jugador(15 + 60 * (1 - d / 11), (x, y))
        for p in list(self.personas):
            if not p.muerto and p.dist(x, y) < 8:
                self.danar_persona(p, 300)
        if v.tag == "objetivo" and self.mision:
            self.mision["restos"] = (x, y)
        if v.modelo["id"] == "blindado" and not v.tag:
            o = Objeto("dinero", "Sacas de dinero del furgón", *self.mundo.punto_libre(x, y))
            o.valor = random.randint(3000, 6000)
            self.objetos.append(o)
            self.decir("¡El furgón blindado revienta y las sacas de dinero quedan en el suelo! Toda la policía viene hacia aquí.")
            if self.mundo.policia:
                self.poner_busqueda(3)
        self.quitar_vehiculo(v)

    # ---------------------------------------------------------------- delitos
    def delito(self, puntos, texto=None, siempre=False):
        j = self.j
        if self.cfg["sin_policia"]:
            return
        if self.mision and self.mision["def"].get("tutorial"):        # en un tutorial no viene la policía
            return
        if self.cfg["mod_policia"]:
            puntos *= 1.5
        x, y = self.pos()
        if not siempre:
            testigo = any((p.tipo == "civil" and not p.muerto and p.dist(x, y) < 35) or
                          (p.tipo == "policia" and not p.muerto and p.dist(x, y) < 80) for p in self.personas)
            testigo = testigo or any(v.ia == "policia" and v.dist(x, y) < 80 for v in self.vehiculos)
            if not testigo:
                return
        self.cambiar_ciudadania(-0.6 * puntos)
        if j.ciudadania >= 50:
            puntos *= 0.7            # a un buen vecino se le pasan por alto las faltas pequeñas
        if j.estrellas == 0 and j.puntos_busqueda + puntos >= UMBRAL[0] and texto:
            self.decir(f"Te han visto. Delito: {texto}.")
        j.puntos_busqueda += puntos

    def poner_busqueda(self, nivel):
        if self.cfg["sin_policia"]:
            return
        self.j.puntos_busqueda = max(self.j.puntos_busqueda, UMBRAL[max(0, min(4, nivel - 1))])

    def limpiar_busqueda(self, hablar=True):
        j = self.j
        if j.estrellas > 0 and hablar:
            self.son("policia_perdida", cat="interfaz")
            self.decir("Has despistado a la policía. Ya no te buscan.")
        j.puntos_busqueda = 0.0
        j.estrellas = 0
        self.t_evasion = 0.0
        for p in self.personas:
            if p.tipo == "policia":
                p.hostil = False
                p.estado = "quieto"
        for v in self.vehiculos:
            if v.ia == "policia":
                v.hostil = False
        if isinstance(self.objetivo, Persona) and self.objetivo.tipo == "policia":
            self.objetivo = None

    def actualizar_policia(self, dt):
        j = self.j
        n = sum(1 for u in UMBRAL if j.puntos_busqueda >= u)
        if n > j.estrellas:
            if j.estrellas == 0:
                self.t_policia = 5.0 if not j.veh else 3.0          # la primera patrulla tarda en salir: da tiempo a reaccionar
                self.patrulla_enviada = False
            self.son("estrella_sube", cat="interfaz")
            self.app.vibrar(0.5, 0.5, 250)
            pista = " Aléjate de las sirenas hasta que dejen de buscarte, o pinta el vehículo en un taller." if j.estrellas == 0 else ""
            self.decir(f"Nivel de búsqueda {n} de 5.{pista}")
        j.estrellas = n
        if n == 0:
            return
        x, y = self.pos()
        # A pie se te ve menos que en un coche: basta con alejarse media manzana para que te pierdan.
        r_p, r_v = (70, 80) if j.veh else (38, 45)
        cerca = any(p.tipo == "policia" and not p.muerto and p.dist(x, y) < r_p for p in self.personas) or \
            any(v.ia == "policia" and not v.muerto and v.dist(x, y) < r_v for v in self.vehiculos)
        if cerca:
            self.t_evasion = 0.0
        else:
            if getattr(self, "patrulla_enviada", True):
                self.t_evasion += dt                              # solo cuenta cuando ya hay alguien buscándote
            self.t_buscando -= dt
            if self.t_buscando <= 0:
                self.t_buscando = 1.0
                self.son("buscando", vol=0.6, cat="interfaz")
            if self.t_evasion >= (9 + 4 * n if j.veh else 7 + 3 * n):
                self.limpiar_busqueda()
                return
        self.t_policia -= dt
        if self.t_policia <= 0:
            self.t_policia = RITMO_PATRULLAS.get(n, 5.0)
            total = sum(1 for v in self.vehiculos if v.ia == "policia" and not v.muerto)
            tope = PATRULLAS.get(n, 4) - (1 if self.cfg["dificultad"] == "facil" and n >= 3 else 0)
            if total < tope and self.t_evasion < 6 and self.mundo.policia:
                self._llegar_patrulla(x, y)
            self.patrulla_enviada = True
        for v in self.vehiculos:
            if v.ia == "policia":
                v.hostil = True

    def _llegar_patrulla(self, x, y):
        m = self.mundo
        for _ in range(6):
            dist = random.uniform(150, 230) * random.choice([-1, 1])
            if random.random() < 0.5:
                jj = m._idx(y, m.NY)
                vx = x + dist
                if not (5 < vx < m.ancho - 5):
                    continue
                d = 3 if dist > 0 else 1
                pos = (vx, m.carril("H", jj, d))
            else:
                ii = m._idx(x, m.NX)
                vy = y + dist
                if not (5 < vy < m.alto - 5):
                    continue
                d = 2 if dist > 0 else 0
                pos = (m.carril("V", ii, d), vy)
            v = Vehiculo(self.modelos["patrulla"], pos[0], pos[1], d, "policia")
            v.ocupado = True
            v.hostil = True
            v.vel = 12.0
            self.vehiculos.append(v)
            return

    # ---------------------------------------------------------------- personas
    def _andar_hacia(self, p, tx, ty, vel, dt):
        dx, dy = tx - p.x, ty - p.y
        d = math.hypot(dx, dy)
        if d < 0.1:
            return
        paso = vel * dt
        nx, ny = p.x + dx / d * paso, p.y + dy / d * paso
        if self.mundo.transitable(nx, ny):
            p.x, p.y = nx, ny
        elif abs(dx) > 0.2 and self.mundo.transitable(p.x + math.copysign(paso, dx), p.y):
            p.x += math.copysign(paso, dx)
        elif abs(dy) > 0.2 and self.mundo.transitable(p.x, p.y + math.copysign(paso, dy)):
            p.y += math.copysign(paso, dy)
        else:
            # atascado contra una esquina: rodea por el eje más largo
            if abs(dx) < abs(dy) and self.mundo.transitable(p.x + paso, p.y):
                p.x += paso
            elif self.mundo.transitable(p.x, p.y + paso):
                p.y += paso

    def actualizar_personas(self, dt):
        j = self.j
        px, py = self.pos()
        vel_j = abs(j.veh.vel) if j.veh else 0.0
        for p in list(self.personas):
            if p.muerto:
                continue
            if p.tipo == "aliado":
                self.actualizar_aliado(p, dt)
                continue
            if p.tipo == "perro":
                self.actualizar_perro(p, dt)
                continue
            d = p.dist(px, py)
            if p.tipo == "policia" and j.estrellas == 0:
                p.hostil = False
                if d > 45:
                    self.personas.remove(p)
                continue
            if not p.hostil:
                if p.estado == "quieto" or p.bloque is None:
                    if p.estado == "huye":
                        self._andar_hacia(p, p.x + (p.x - px), p.y + (p.y - py), 4.5, dt)
                        p.t_estado -= dt
                        if p.t_estado <= 0:
                            p.estado = "quieto"
                    continue
                vel = p.vel
                if p.estado == "huye":
                    vel = 4.6
                    p.t_estado -= dt
                    p.t_voz -= dt
                    if p.t_voz <= 0:
                        p.t_voz = 1.0
                        u0 = p.u
                        mejor = None
                        for s in (-1, 1):
                            p.u = u0 + s * 3
                            self._pos_perimetro(p)
                            dd = p.dist(px, py)
                            if mejor is None or dd > mejor[0]:
                                mejor = (dd, s)
                        p.u = u0
                        p.sentido = mejor[1]
                    if p.t_estado <= 0:
                        p.estado = "pasea"
                p.u += p.sentido * vel * dt
                self._pos_perimetro(p)
                if d < 24:
                    p.t_paso -= dt
                    if p.t_paso <= 0:
                        p.t_paso = 0.3 if p.estado == "huye" else 0.55
                        self.son("paso_npc", xy=(p.x, p.y), ref=3, maxd=28, vol=0.7, tono=random.uniform(0.9, 1.1))
                continue
            # ------------------------------------------------------ hostiles
            if getattr(p, "inofensivo", False):
                continue
            if not p.activo:
                if d < 42:
                    p.activo = True
                else:
                    continue
            if p.tipo == "banda" and not p.avisado:
                if d > 26:
                    p.u += p.sentido * p.vel * dt
                    self._pos_perimetro(p)
                    continue
                p.avisado = True
                self.son("grito", xy=(p.x, p.y), vol=0.5, tono=0.8)
                self.decir(f"¡Un Calavera te ha visto! {self.situar(p.x, p.y, 'Está')}. Pulsa Q para fijarlo.")
            a = self.armas_d.get(p.arma or "punos", self.armas_d["punos"])
            cuerpo = a["tipo"] == "cuerpo"
            alcance = a["alcance"] if cuerpo else min(a["alcance"], 30.0)
            arresto = p.tipo == "policia" and j.estrellas == 1
            dist_obj = 1.8 if (cuerpo or arresto) else alcance * 0.6
            if d > dist_obj:
                self._andar_hacia(p, px, py, 3.7 if p.tipo == "policia" else 3.3, dt)
                p.t_paso -= dt
                if p.t_paso <= 0 and d < 30:
                    p.t_paso = 0.33
                    self.son("paso_npc", xy=(p.x, p.y), ref=3, maxd=30, vol=0.9, tono=0.85)
            if arresto:
                if d < 3.0 and vel_j < 1.5:
                    p.t_arresto += dt
                    if p.t_arresto > 1.6:
                        self.detener()
                        return
                else:
                    p.t_arresto = 0.0
                continue
            if d > alcance + (0.5 if cuerpo else 0):
                p.t_disparo = max(p.t_disparo, 0.6)
                continue
            p.t_disparo -= dt
            if not cuerpo and p.t_disparo < 0.45 and not getattr(p, "amartillado", False):
                p.amartillado = True
                self.son("amartillar", xy=(p.x, p.y), ref=5, maxd=50)
            if p.t_disparo > 0:
                continue
            p.amartillado = False
            p.t_disparo = (0.45 if a.get("automatica") else max(1.2, a["cadencia"] * 2.5)) + random.uniform(0, 0.6)
            if cuerpo:
                self.son(a["sonido"], xy=(p.x, p.y), ref=4)
                if random.random() < 0.7:
                    self.danar_jugador(a["dano"] * 0.5, (p.x, p.y))
                continue
            self.son(a["sonido"], xy=(p.x, p.y), ref=14, maxd=220, vol=0.9)
            prob = 0.42 * (1.0 - 0.6 * d / alcance)
            if j.agachado:
                prob *= 0.45
            if j.veh:
                prob *= 0.7
            if random.random() < prob:
                if j.veh:
                    self.son("bala_impacto", vol=0.6)
                    self.danar_vehiculo(j.veh, a["dano"] * 0.4)
                    if random.random() < 0.3:
                        self.danar_jugador(a["dano"] * 0.2, (p.x, p.y))
                else:
                    self.danar_jugador(a["dano"] * 0.4, (p.x, p.y))
            else:
                self.son("bala_silbido", pan=random.uniform(-0.9, 0.9), vol=0.5)

    def actualizar_combate(self, dt):
        j = self.j
        if j.t_ataque > 0:
            j.t_ataque -= dt
        for e in list(self.explosiones):
            e["t"] -= dt
            if e["t"] <= 0:
                self.explosiones.remove(e)
                self._estallar(e)
        t = self.app.teclas
        if not j.veh and pygame.K_SPACE in t and self.arma().get("automatica"):
            self.atacar()
        o = self.objetivo
        if o is not None:
            x, y = self.pos()
            if o.muerto or o.dist(x, y) > 260:
                self.objetivo = None
            else:
                self.t_objetivo -= dt
                if self.t_objetivo <= 0:
                    d = o.dist(x, y)
                    self.t_objetivo = max(0.25, min(1.0, d / 40.0))
                    f = min(d, 25) / d if d > 0.5 else 1.0
                    dentro = d <= self.arma()["alcance"]
                    self.son("tono_objetivo" if dentro else "tono_apuntado", xy=(x + (o.x - x) * f, y + (o.y - y) * f),
                             ref=8, maxd=80, vol=0.7, cat="interfaz")
        if j.salud < 30 and self.latido_canal is None:
            self.latido_canal = self.son("latido", bucle=True, vol=0.7)
        elif j.salud >= 30 and self.latido_canal is not None:
            self.latido_canal.parar()
            self.latido_canal = None

    # ------------------------------------------------------- muerte y arresto
    def _fin_persecucion(self):
        self.limpiar_busqueda(False)
        for p in [p for p in self.personas if p.tipo == "policia"]:
            self.personas.remove(p)
        for v in [v for v in self.vehiculos if v.ia == "policia"]:
            self.quitar_vehiculo(v)
        self.objetivo = None

    def morir(self):
        if self.transicion:
            return
        self.transicion = True
        j = self.j
        j.stats["muertes"] += 1
        self.son("mision_fallo", cat="interfaz")
        if j.veh:
            self.salir_vehiculo(forzado=True)
        self._fin_persecucion()
        if self.trabajo:
            self.terminar_trabajo(None)
        coste = min(j.dinero, 150)
        j.dinero -= coste
        j.animo = max(0.0, j.animo - 12)
        j.efectos = []
        self.perder_mercancia(todo=False)
        h = self._reaparecer("hospital")
        j.salud = j.salud_max
        j.blindaje = 0.0
        j.agachado = False
        self.pasar_horas(6)
        self.cancelar_gps()

        def fin():
            self.transicion = False
            if self.mision:
                self.fallar_mision("Has perdido el conocimiento.")
        self.son("hospital_despertar", cat="interfaz")
        self.app.abrir(Dialogo(self.app, [("Narrador", f"Todo se vuelve negro. Horas después despiertas en {h.nombre}, {self.mundo.nombre}, con un vendaje nuevo y {coste} euros menos. Son las {self.hora_txt()}.")], fin))

    def _reaparecer(self, tipo):
        """Te lleva al hospital o comisaría más cercano (de este mapa, o del principal)."""
        x, y = self.pos()
        aqui = [l for l in self.mundo.lugares.values() if l.tipo == tipo]
        if aqui:
            l = min(aqui, key=lambda l: math.hypot(l.x - x, l.y - y))
            self.teletransportar(l.x, l.y)
            return l
        todos = [l for l in self.lugares.values() if l.tipo == tipo]
        l = next((q for q in todos if q.mapa == "puerto_bravo"), todos[0])
        self.j.barco_actual = None
        if self.j.veh:
            v = self.j.veh
            self.j.veh = None
            self.quitar_vehiculo(v)
            self.app.radio.apagar()
        self.cambiar_mapa(l.mapa, l.x, l.y)
        return l

    def coste_multa(self):
        j = self.j
        return 150 * max(1, j.estrellas) + j.dinero // 20

    def detener(self, sin_trato=False):
        if self.transicion:
            return
        j = self.j
        if not sin_trato and self.cfg["multas"] and 1 <= j.estrellas <= 2 and j.dinero >= self.coste_multa() and not self.mision:
            self._trato_policia()                                # con poca búsqueda y dinero en el bolsillo, se puede arreglar
            return
        self.transicion = True
        j.stats["detenciones"] += 1
        self.son("esposas", cat="interfaz")
        if j.veh:
            self.salir_vehiculo(forzado=True)
        self._fin_persecucion()
        if self.trabajo:
            self.terminar_trabajo(None)
        multa = min(j.dinero, max(100, j.dinero // 10))
        j.dinero -= multa
        for ident in [a for a in j.armas if a in self.armas_d and self.armas_d[a]["tipo"] in ("fuego", "explosivo")]:
            del j.armas[ident]
        j.arma = "punos"
        j.animo = max(0.0, j.animo - 15)
        j.reputacion = max(0.0, j.reputacion - 3)
        j.efectos = []
        requisado = self.perder_mercancia()
        if requisado:
            multa_extra = min(j.dinero, requisado * 20)
            j.dinero -= multa_extra
            multa += multa_extra
        c = self._reaparecer("comisaria")
        j.agachado = False
        self.pasar_horas(8)
        self.cancelar_gps()

        def fin():
            self.transicion = False
            if self.mision:
                self.fallar_mision("Te han detenido.")
        self.son("celda", cat="interfaz")
        j.ciudadania = max(0.0, j.ciudadania - 5)
        self.app.abrir(Dialogo(self.app, [("Narrador", f"Te esposan y te llevan a {c.nombre}. Tras una noche en el calabozo sales con {multa} euros menos de multa y sin tus armas de fuego. Son las {self.hora_txt()}.")], fin))
