"""Personajes del servidor: gente que lleva la máquina y que es la misma para todos los jugadores.

No son los peatones de relleno, que esos los pone el juego de cada uno. Son pocos, tienen nombre, se mueven por la
localidad, y cada uno tiene su forma de ser: el que pasea y saluda, el ratero que atraca, el pistolero que va a por
quien tiene precio por su cabeza, el que se lleva los coches aparcados y el que atraca negocios de jugadores.
Se les puede hacer lo mismo que a un jugador: fijarlos, dispararles, atropellarlos, atracarlos. Y ellos, a ti.

Todo va con azar: ni salen siempre los mismos, ni hacen dos veces lo mismo.
"""
import math
import time

NOMBRES = ["el Chato", "la Rubia", "Manolo el Largo", "la Toñi", "el Pecas", "Charo", "el Legionario", "la Moños", "Paquito", "el Gallego",
           "la Chispa", "el Mudo", "Encarni", "el Niño", "la Gata", "Curro", "el Tieso", "la Seca", "Ramiro", "el Zurdo"]
CLASES = ("paseante", "paseante", "ratero", "pistolero", "ladron", "atracador")
FRASES = {
    "paseante": ["Buenas.", "Vaya día.", "¿Tienes hora?", "Hoy el puerto huele a tormenta.", "Cuidado por ahí, que andan robando.", "Hasta luego."],
    "ratero": ["¿Tienes fuego?", "Bonito reloj.", "No te había visto por aquí."],
    "pistolero": ["Tú y yo tenemos algo pendiente.", "Hay quien paga bien por algunos."],
    "ladron": ["Buen coche el de ahí.", "Yo no he visto nada."],
    "atracador": ["Hoy va a ser un buen día.", "¿Ese negocio de quién es?"],
}
ARMA = {"paseante": "punos", "ratero": "navaja", "pistolero": "pistola", "ladron": "bate", "atracador": "pistola"}


class Bots:
    """Mixin del servidor."""

    def bots_iniciar(self):
        self.bots = []
        self._t_bots = 0.0

    def _bot_nuevo(self, mapa):
        from .nucleo import Jugador
        self._n += 1
        b = Jugador(self._n, None)
        b.bot = True
        b.conectado = False                        # no hay nadie al otro lado: nada que enviarle
        b.dentro = True
        b.clase = self.rng.choice(CLASES)
        usados = {x.nombre for x in self.jugadores.values()}
        libres = [n for n in NOMBRES if n not in usados] or NOMBRES
        b.nombre = self.rng.choice(libres)
        b.arma = ARMA[b.clase]
        b.salud = float(self.rng.randint(60, 110))
        b.dinero = self.rng.randint(80, 1500)
        b.mapa = mapa
        l = self.rng.choice(self.mundo["mapas"][mapa]["lugares"])
        b.x, b.y = float(l["x"]), float(l["y"])
        b.destino = None
        b.espera = self.rng.uniform(2, 15)
        b.paso = 1.4
        b.presa = None                             # id de a quién va
        b.t_presa = 0.0
        b.huye = 0.0
        b.atracados = {}
        b.t_frase = self.rng.uniform(20, 90)
        b.t_plan = self.rng.uniform(30, 120)
        b.plan = None
        self.jugadores[b.id] = b
        self.bots.append(b)
        self._a_todos({"t": "entra", "id": b.id, "nombre": b.nombre, "banda": None, "ia": True})
        return b

    def _bot_fuera(self, b):
        if b in self.bots:
            self.bots.remove(b)
        if b.vid is not None and b.vid in self.vehiculos:
            self._soltar_vehiculo(b, self.vehiculos[b.vid])
        self.robos.pop(b.id, None)
        if self.jugadores.pop(b.id, None) is not None:
            self._a_todos({"t": "sale", "id": b.id})

    def bot_golpeado(self, b, por):
        """Un jugador le ha dado: cada cual reacciona a su manera."""
        if b.salud <= 0:
            self._caida(b, por)
            self._bot_fuera(b)
            return
        if b.clase in ("paseante", "ladron") and self.rng.random() < 0.8:
            b.huye, b.presa = 25.0, None
            b.destino = self._bot_lejos(b, por)
        else:
            b.presa, b.t_presa = por.id, 60.0      # se revuelve

    def _bot_lejos(self, b, de):
        ls = self.mundo["mapas"][b.mapa]["lugares"]
        l = max(self.rng.sample(ls, min(6, len(ls))), key=lambda l: math.hypot(l["x"] - de.x, l["y"] - de.y))
        return (float(l["x"]), float(l["y"]))

    def _bot_andar(self, b, dt):
        if b.destino is None:
            b.vel = 0.0
            b.espera -= dt
            if b.espera <= 0:
                l = self.rng.choice(self.mundo["mapas"][b.mapa]["lugares"])
                b.destino = (float(l["x"]), float(l["y"]))
            return
        paso = (9.0 if b.veh else 4.2 if (b.huye > 0 or b.presa is not None) else b.paso) * dt
        dx, dy = b.destino[0] - b.x, b.destino[1] - b.y
        # por las calles: primero a lo largo y luego a lo ancho, como quien dobla una esquina
        if abs(dx) > 0.5:
            b.x += math.copysign(min(abs(dx), paso), dx)
            b.rumbo = 90.0 if dx > 0 else 270.0
        elif abs(dy) > 0.5:
            b.y += math.copysign(min(abs(dy), paso), dy)
            b.rumbo = 0.0 if dy > 0 else 180.0
        else:
            b.destino = None
            b.espera = self.rng.uniform(4, 40)
            if b.plan == "llevarse" and b.vid is not None and b.vid in self.vehiculos:      # deja el coche donde ha llegado
                self._soltar_vehiculo(b, self.vehiculos[b.vid])
                b.veh, b.plan = None, None
        b.vel = paso / dt if b.destino is not None else 0.0
        if b.vid is not None and b.vid in self.vehiculos:
            self.vehiculos[b.vid].update(m=b.mapa, x=b.x, y=b.y, r=b.rumbo)

    def bots_mover(self, dt):
        for b in list(self.bots):
            self._bot_andar(b, dt)

    def bots_pensar(self, dt):
        """Una vez por segundo: cuántos hay, dónde, y qué se le ocurre a cada uno."""
        personas = [j for j in self.jugadores.values() if j.dentro and not getattr(j, "bot", False) and j.mapa is not None]
        quiere = int(self.cfg["personajes"]) if personas else 0
        mapas = sorted({j.mapa for j in personas if self.mundo["mapas"][j.mapa]["tipo"] != "mar"})
        for b in list(self.bots):                  # los que se han quedado en una localidad sin nadie se van
            if b.mapa not in mapas and b.id not in self.robos:
                self._bot_fuera(b)
        while len(self.bots) > quiere:
            self._bot_fuera(self.bots[-1])
        if mapas and len(self.bots) < quiere and self.rng.random() < 0.25:
            pocos = min(mapas, key=lambda m: sum(1 for b in self.bots if b.mapa == m))
            self._bot_nuevo(pocos)
        ahora = time.monotonic()
        for b in list(self.bots):
            cerca = sorted((j for j in personas if j.mapa == b.mapa), key=lambda j: b.dist(j))
            b.huye = max(0.0, b.huye - dt)
            b.t_frase -= dt
            if b.t_frase <= 0 and cerca and b.dist(cerca[0]) < 14 and b.presa is None:
                b.t_frase = self.rng.uniform(60, 240)
                self._enviar(cerca[0], {"t": "chat", "de": b.id, "nombre": b.nombre, "texto": self.rng.choice(FRASES[b.clase]), "canal": "cerca"})
            if b.huye > 0:
                continue
            presa = self.jugadores.get(b.presa) if b.presa is not None else None
            if presa is not None:
                b.t_presa -= dt
                if not presa.dentro or presa.mapa != b.mapa or b.t_presa <= 0 or presa.salud <= 0 or self.segura(presa):
                    b.presa, b.destino, b.espera = None, None, self.rng.uniform(3, 10)
                    continue
                d = b.dist(presa)
                if b.plan == "atracar":
                    b.destino = (presa.x, presa.y)
                    if d <= 4.5 and not presa.veh:
                        b.atracados[presa.cuenta] = ahora
                        self._m_atraco(b, {"a": presa.id})
                        b.plan, b.presa, b.huye = None, None, 30.0
                        b.destino = self._bot_lejos(b, presa)
                else:                              # pelea: se acerca hasta tenerle a tiro y dispara o golpea
                    alcance = float(self.mundo["armas"][b.arma]["alcance"])
                    b.destino = (presa.x, presa.y) if d > alcance * 0.6 else None
                    if d <= alcance:
                        self._m_ataque(b, {"a": presa.id, "arma": b.arma})
                continue
            b.t_plan -= dt
            if b.t_plan > 0 or not si_pvp(self):
                continue
            b.t_plan = self.rng.uniform(40, 160)
            if b.clase == "ratero":
                c = [j for j in cerca if b.dist(j) < 70 and not j.veh and not j.pasivo and not self.segura(j) and ahora - b.atracados.get(j.cuenta, -9999) > 600]
                if c and self.rng.random() < 0.6:
                    b.presa, b.t_presa, b.plan = c[0].id, 45.0, "atracar"
            elif b.clase == "pistolero":
                c = [j for j in cerca if b.dist(j) < 120 and not j.pasivo and self._recompensa(j) > 0]
                if c:
                    b.presa, b.t_presa, b.plan = c[0].id, 90.0, "cazar"
            elif b.clase == "ladron" and b.vid is None:
                c = [v for v in self.vehiculos.values() if v["por"] is None and v["m"] == b.mapa and math.hypot(v["x"] - b.x, v["y"] - b.y) < 12]
                if c and self.rng.random() < 0.5:
                    self._m_veh_subir(b, {"id": c[0]["id"]})
                    if b.vid is not None:
                        b.veh, b.plan = c[0]["modelo"], "llevarse"
                        b.destino = self._bot_lejos(b, b)
                else:
                    lejos = [v for v in self.vehiculos.values() if v["por"] is None and v["m"] == b.mapa]
                    if lejos:
                        v = self.rng.choice(lejos)
                        b.destino = (float(v["x"]), float(v["y"]))
                        b.t_plan = 15.0
            elif b.clase == "atracador" and b.id not in self.robos:
                c = [l for l in self.lugares.values() if l["mapa"] == b.mapa and l["tipo"] == "negocio"]
                c = [l for l in c if self.alm.propiedad(l["id"]) is not None and self.alm.propiedad(l["id"])["robado_dia"] != self.dia]
                if c:
                    l = min(c, key=lambda l: math.hypot(l["x"] - b.x, l["y"] - b.y))
                    if math.hypot(l["x"] - b.x, l["y"] - b.y) < 25:
                        self._m_robo(b, {"lugar": l["id"]})
                        b.destino, b.espera = None, float(self.cfg["robo_segundos"]) + 3
                    elif self.rng.random() < 0.5:
                        b.destino = (float(l["x"]), float(l["y"]))
                        b.t_plan = 20.0


def si_pvp(srv):
    return str(srv.cfg["pvp"]).strip().lower() in ("si", "sí", "1", "true", "yes")
