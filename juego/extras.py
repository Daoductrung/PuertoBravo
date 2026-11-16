"""Actividades libres: pesca, atracos a peatones, guardaespaldas, sirenas y lotería."""
import math
import random

from . import mundo as M
from .entidades import Persona


class Extras:
    # ------------------------------------------------------------------ pesca
    def empezar_pesca(self, desde_muelle=False):
        j = self.j
        if self.pesca:
            self.pesca = None
            self.son("carrete", vol=0.5)
            self.decir("Recoges el sedal.", True)
            return
        if j.veh and abs(j.veh.vel) > 1.5:
            self.decir("Detén el barco para pescar.", True)
            return
        self.pesca = {"fase": "espera", "t": random.uniform(3, 10) * (1 - 0.05 * self.nivel("pesca")), "muelle": desde_muelle, "x": self.pos()[0], "y": self.pos()[1]}
        self.son("pesca_lanzar", vol=0.7)
        self.decir("Lanzas el anzuelo. Cuando oigas que pican, pulsa Espacio enseguida. No te muevas.", True)

    def actualizar_pesca(self, dt):
        ps = self.pesca
        x, y = self.pos()
        if math.hypot(x - ps["x"], y - ps["y"]) > 4:
            self.pesca = None
            self.decir("Al moverte pierdes el sedal.")
            return
        ps["t"] -= dt
        if ps["t"] > 0:
            return
        if ps["fase"] == "espera":
            ps["fase"] = "pica"
            ps["t"] = 1.3
            self.son("pez_pica", vol=0.9, cat="interfaz")
            self.app.vibrar(0.3, 1.0, 500)
        else:
            self.pesca = None
            self.son("salpicadura", vol=0.5)
            self.decir("Se te ha escapado. Pulsa P para lanzar otra vez.")

    def tirar_pesca(self):
        ps = self.pesca
        if ps["fase"] != "pica":
            self.pesca = None
            self.son("carrete", vol=0.5)
            self.decir("Has tirado antes de tiempo y espantas a los peces.", True)
            return
        self.pesca = None
        peces = self.datos.get("peces") or [{"nombre": "Sardina", "valor": 5, "peso": 10}]
        if ps["muelle"]:
            peces = [p for p in peces if p.get("valor", 0) <= 40] or peces
        pez = random.choices(peces, weights=[p.get("peso", 1) for p in peces])[0]
        self.son("carrete", vol=0.6)
        self.son("salpicadura", vol=0.6)
        if pez.get("valor", 0) <= 0:
            self.decir(f"Sacas {pez['nombre']}. No vale nada.", True)
            return
        self.j.pescado.append({"nombre": pez["nombre"], "valor": int(pez["valor"] * random.uniform(0.8, 1.3) * (1 + 0.05 * self.nivel("pesca")))})
        self.ganar_xp("pesca", 25)
        self.j.stats["peces"] = self.j.stats.get("peces", 0) + 1
        self.decir(f"¡Has pescado {pez['nombre']}! Llevas {len(self.j.pescado)} capturas. Véndelas en una pescadería o en la lonja.", True)

    # ------------------------------------------------------ atracar peatones
    def atracar_peaton(self):
        j = self.j
        if j.veh:
            return
        if self.sv_atracar_cerca():                              # en un servidor: el que tienes al lado es otro jugador
            return
        cerca = [p for p in self.personas if p.tipo == "civil" and not p.muerto and p.dist(j.x, j.y) < 4.5]
        if self.modo_adulto() and self.arma()["id"] == "punos" and self.carga() > 0:
            self.ofrecer_mercancia()
            return
        if not cerca:
            self.decir("No hay ningún peatón a tu lado.", True)
            return
        if self.arma()["id"] == "punos":
            self.decir("Para atracar a alguien tienes que empuñar un arma.", True)
            return
        p = min(cerca, key=lambda p: p.dist(j.x, j.y))
        if getattr(p, "atracado", False):
            self.decir("A ese ya le has quitado todo.", True)
            return
        p.atracado = True
        p.estado = "huye"
        p.t_estado = 14
        self.son("grito", xy=(p.x, p.y), vol=0.6, tono=p.tono)
        if random.random() < 0.12:
            p.hostil = True
            p.estado = "ataca"
            p.arma = "navaja"
            p.tipo = "enemigo"
            p.nombre = "Peatón armado"
            self.decir("¡Este no se deja! Saca una navaja.", True)
            return
        botin = random.randint(5, 70)
        self.dar_dinero(botin)
        self.decir(f"El peatón te da la cartera: {botin} euros, y sale corriendo.", True)
        self.delito(2, "atraco", siempre=random.random() < 0.3)

    # ---------------------------------------------------------- guardaespaldas
    def crear_aliado(self):
        x, y = self.pos()
        px, py = self.mundo.punto_libre(x + random.uniform(-2, 2), y + random.uniform(-2, 2))
        a = Persona("aliado", px, py, "Guardaespaldas")
        a.salud = 140.0
        a.arma = "pistola"
        a.estado = "sigue"
        self.personas.append(a)
        return a

    def actualizar_aliado(self, a, dt):
        j = self.j
        px, py = self.pos()
        if j.veh:
            a.x, a.y = px, py           # va de copiloto
        else:
            d = a.dist(px, py)
            if d > 60:
                a.x, a.y = self.mundo.punto_libre(px - 2, py - 2)
            elif d > 3.5:
                self._andar_hacia(a, px, py, 5.6 if d > 10 else 3.0, dt)
                a.t_paso -= dt
                if a.t_paso <= 0:
                    a.t_paso = 0.4
                    self.son("paso_npc", xy=(a.x, a.y), ref=3, maxd=25, vol=0.6, tono=0.8)
        a.t_disparo -= dt
        if a.t_disparo > 0:
            return
        enemigos = [p for p in self.personas if p.hostil and not p.muerto and p.activo and p.dist(a.x, a.y) < 28
                    and (p.tipo != "banda" or p.avisado)]
        if not enemigos:
            a.t_disparo = 0.4
            return
        e = min(enemigos, key=lambda p: p.dist(a.x, a.y))
        a.t_disparo = random.uniform(0.9, 1.5)
        self.son("disparo_pistola", xy=(a.x, a.y), ref=10, maxd=150, vol=0.7)
        if random.random() < 0.5:
            self.danar_persona(e, 22)

    # ------------------------------------------------------------------ sirena
    def alternar_sirena(self):
        if self.sirena_propia:
            self.sirena_propia.parar()
            self.sirena_propia = None
            self.decir("Sirena apagada.", True)
        else:
            self.sirena_propia = self.son(self.j.veh.modelo.get("sirena"), bucle=True, vol=0.35)
            self.decir("Sirena encendida.", True)

    # ----------------------------------------------------------------- lotería
    def sorteo_loteria(self):
        """Celebra los sorteos de la lotería que toquen: uno cada día, a las nueve de la noche. Está en loteria.py."""
        from . import loteria
        loteria.al_dia(self)

    def cobrar_banco(self):
        j = self.j
        if j.banco > 0:
            interes = int(j.banco * (0.01 if j.ciudadania >= 75 else 0.005))
            if interes:
                j.banco += interes
