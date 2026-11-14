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


class Extras3:
    # -------------------------------------------------------------------- perro
    def crear_perro(self):
        x, y = self.pos()
        px, py = self.mundo.punto_libre(x + random.uniform(-2, 2), y + random.uniform(-2, 2))
        d = Persona("perro", px, py, self.j.perro or "Perro")
        d.salud = 9999.0
        d.estado = "sigue"
        d.avisados = set()
        self.personas.append(d)
        return d

    def perro(self):
        return next((p for p in self.personas if p.tipo == "perro"), None)

    def actualizar_perro(self, d, dt):
        j = self.j
        px, py = self.pos()
        if j.veh:
            d.x, d.y = px, py
        else:
            dist = d.dist(px, py)
            if dist > 50:
                d.x, d.y = self.mundo.punto_libre(px - 1.5, py - 1.5)
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
            self.decir("No tienes perro. Puedes adoptar uno en una protectora de animales.", True)
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
