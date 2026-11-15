"""Segunda ampliación: habilidades, logros, eventos callejeros, encargos repetibles y noticias."""
import math
import random

from . import mundo as M
from .entidades import Objeto, Persona

HABILIDADES = {
    "conduccion": ("Conducción", "Cada nivel sube un uno por ciento la velocidad máxima y reduce los daños de tu vehículo."),
    "punteria": ("Puntería", "Cada nivel sube tu probabilidad de acertar."),
    "resistencia": ("Resistencia", "Cada nivel te hace correr más y recibir menos daño."),
    "pesca": ("Pesca", "Cada nivel hace que piquen antes y que tus capturas valgan más."),
}

NOMBRES = ["el Chato", "la Culebra", "el Rubio", "la Tuerta", "el Mudo", "la Marquesa", "el Polaco", "la Zurda", "el Notario", "la Perla"]
MODELOS_ENCARGO = ["sedan", "deportivo", "todoterreno", "furgoneta", "moto", "descapotable", "pickup", "utilitario", "buggy", "limusina"]

LOGROS = [
    ("primera", "De vuelta a casa", "Completa tu primera misión.", lambda p: len(p.completadas) >= 1),
    ("historia", "Ley del asfalto", "Completa la historia principal.", lambda p: "m20" in p.completadas),
    ("todas", "Leyenda de la comarca", "Completa todas las misiones.", lambda p: len(p.completadas) >= len(p.datos["misiones"])),
    ("rico", "Primer millón de céntimos", "Reúne 10000 euros entre efectivo y banco.", lambda p: p.j.dinero + p.j.banco >= 10000),
    ("millonario", "Magnate", "Reúne 250000 euros entre efectivo y banco.", lambda p: p.j.dinero + p.j.banco >= 250000),
    ("casero", "Casero", "Ten tres viviendas.", lambda p: sum(1 for i in p.j.propiedades if p.lug(i) and p.lug(i).tipo == "casa") >= 3),
    ("empresario", "Empresario", "Ten tres negocios.", lambda p: sum(1 for i in p.j.propiedades if p.lug(i) and p.lug(i).tipo == "negocio") >= 3),
    ("viajero", "Trotamundos", "Visita todas las localidades.", lambda p: all(any(b["id"] in p.j.barrios_vistos for b in m.barrios) for m in p.mapas.values())),
    ("explorador", "Explorador", "Visita cien lugares.", lambda p: len(p.j.visitados) >= 100),
    ("cartografo", "Cartógrafo", "Visita todos los lugares del juego.", lambda p: len(p.j.visitados) >= len(p.lugares)),
    ("coleccionista", "Coleccionista", "Encuentra diez objetos de colección.", lambda p: len(p.j.casetes) >= 10),
    ("completista", "Lo tengo todo", "Encuentra todos los objetos de colección.", lambda p: len(p.j.casetes) >= p.total_casetes()),
    ("pescador", "Lobo de mar", "Pesca veinticinco peces.", lambda p: p.j.stats.get("peces", 0) >= 25),
    ("capitan", "Armador", "Ten dos barcos.", lambda p: len(p.j.barcos) >= 2),
    ("piloto", "Piloto", "Recorre cien kilómetros al volante.", lambda p: p.j.stats["metros_coche"] >= 100000),
    ("caminante", "Caminante", "Recorre diez kilómetros a pie.", lambda p: p.j.stats["metros_pie"] >= 10000),
    ("ladron", "Manos rápidas", "Roba veinticinco vehículos.", lambda p: p.j.stats["vehiculos_robados"] >= 25),
    ("taxista", "Taxista de toda la vida", "Completa veinte servicios de trabajo.", lambda p: p.j.stats.get("servicios", 0) >= 20),
    ("campeon", "Campeón", "Gana todas las carreras.", lambda p: len(p.j.stats["carreras"]) >= len(p.datos["carreras"])),
    ("boxeador", "Guantes de oro", "Gana cinco combates de boxeo.", lambda p: p.j.stats.get("boxeo", 0) >= 5),
    ("sicario", "Profesional", "Cumple cinco contratos del tablón.", lambda p: p.j.stats.get("contratos", 0) >= 5),
    ("butron", "Butronero", "Atraca un banco.", lambda p: p.j.stats.get("atracos", 0) >= 1),
    ("forzudo", "En plena forma", "Sube tu salud máxima a 150.", lambda p: p.j.salud_max >= 150),
    ("maestro", "Maestría", "Sube una habilidad al nivel diez.", lambda p: any(p.nivel(h) >= 10 for h in HABILIDADES)),
    ("heroe", "Buen vecino", "Resuelve diez sucesos callejeros.", lambda p: p.j.stats.get("eventos", 0) >= 10),
    ("arsenal", "Arsenal", "Ten quince armas distintas.", lambda p: len(p.j.armas) >= 15),
    ("amigo", "El mejor amigo", "Adopta un perro.", lambda p: bool(p.j.perro)),
    ("jefe", "Jefe de barrio", "Conquista tres territorios.", lambda p: len(p.j.territorios) >= 3),
    ("amo", "La comarca es tuya", "Conquista todos los barrios de las tres ciudades.", lambda p: len(p.j.territorios) >= sum(len(m.barrios) for m in p.mapas.values() if m.tipo == "ciudad")),
    ("buzo", "Cazatesoros", "Encuentra cinco tesoros buceando o con el detector.", lambda p: p.j.stats.get("tesoros", 0) >= 5),
    ("memoria", "Memoria de elefante", "Aguanta ocho rondas en la máquina de memoria de sonidos.", lambda p: p.j.stats.get("simon", 0) >= 8),
    ("inversor", "Lobo de la bolsa", "Ten acciones por valor de 20000 euros.", lambda p: sum(n * p.precio_accion(i) for i, n in p.j.acciones.items()) >= 20000),
]


class Extras2:
    # -------------------------------------------------------------- habilidades
    def nivel(self, hab):
        return min(10, int((self.j.hab.get(hab, 0.0) / 60.0) ** 0.5))

    def ganar_xp(self, hab, n):
        antes = self.nivel(hab)
        n *= 1.0 + 0.25 * sum(1 for k in ("mod_enemigos", "mod_policia", "mod_dinero") if self.cfg[k])      # jugar más difícil enseña más deprisa
        self.j.hab[hab] = self.j.hab.get(hab, 0.0) + n
        ahora = self.nivel(hab)
        if ahora > antes:
            self.son("nivel", cat="interfaz")
            self.decir(f"Tu habilidad de {HABILIDADES[hab][0].lower()} sube al nivel {ahora}.")

    # ------------------------------------------------------------------- logros
    def comprobar_logros(self):
        for ident, nombre, desc, cond in LOGROS:
            if ident in self.j.logros:
                continue
            try:
                ok = cond(self)
            except Exception:
                ok = False
            if ok:
                self.j.logros.append(ident)
                self.son("logro", cat="interfaz")
                self.decir(f"Logro conseguido: {nombre}. {desc}")

    # -------------------------------------------------------- actualización
    def actualizar_extras(self, dt):
        self.t_logros -= dt
        if self.t_logros <= 0:
            self.t_logros = 4.0
            self.comprobar_logros()
        self._noticias(dt)
        self._eventos(dt)

    # ----------------------------------------------------------------- noticias
    def _noticias(self, dt):
        if not self.j.veh or self.app.radio.id_actual() != "noticias":
            return
        self.t_noticia -= dt
        if self.t_noticia > 0:
            return
        self.t_noticia = random.uniform(18, 28)
        self.decir("El Faro Noticias. " + self.noticia())

    def noticia(self):
        j = self.j
        s = j.stats
        ops = [
            f"Son las {self.hora_txt()}. " + ("Llueve en toda la comarca: precaución en las carreteras." if self.lluvia else "Cielos despejados en toda la comarca.") + (" " + self.dia_txt() if self.dia_txt() else ""),
            "El Atlético Bravo empata a cero y sigue soñando con el ascenso.",
            "El Ayuntamiento de Puerto Bravo promete arreglar el reloj de la plaza. Otra vez.",
            "Los pescadores de Cala Brava denuncian que cada vez hay más botas viejas en el mar.",
            "El balneario de Fuentefría cuelga el cartel de completo.",
            "La Universidad de San Lucero investiga por qué los estudiantes duermen tan poco.",
        ]
        if s["vehiculos_robados"] > 5:
            ops.append(f"Ola de robos de vehículos: ya van {s['vehiculos_robados']} denuncias. La policía busca a un único sospechoso.")
        if s.get("atracos", 0):
            ops.append("Los bancos refuerzan su seguridad tras los últimos atracos.")
        if s.get("eventos", 0) > 2:
            ops.append("Vecinos de la comarca hablan de una persona misteriosa que aparece cuando hay problemas y se va sin decir su nombre.")
        if j.estrellas:
            ops.append("Última hora: la policía persigue a un individuo peligroso. Se recomienda no salir a la calle.")
        if "m20" in self.completadas:
            ops.append("Octavio Belmonte pasa su primera semana en prisión. Sus empresas, intervenidas por la jueza.")
        elif "m10" in self.completadas:
            ops.append("El empresario Octavio Belmonte niega cualquier relación con la banda de Los Calaveras.")
        if "t06" in self.completadas:
            ops.append("Monteferro celebra el fin de la huelga minera con una verbena en la plaza.")
        if "s06" in self.completadas:
            ops.append("San Lucero respira tranquila tras la caída de la banda de Los Lagartos.")
        if s.get("peces", 0) > 10:
            ops.append("La lonja registra capturas récord esta semana.")
        return random.choice(ops)

    # --------------------------------------------------------- sucesos callejeros
    def _punto_cercano(self, minimo, maximo, acera=True):
        x, y = self.pos()
        for _ in range(30):
            a = random.uniform(0, 2 * math.pi)
            d = random.uniform(minimo, maximo)
            px, py = x + math.sin(a) * d, y + math.cos(a) * d
            s = self.mundo.superficie(px, py)
            if s == "acera" or (not acera and s not in ("pared", "fuera", "calzada", "agua")):
                return px, py
        return None

    def _fin_evento(self, texto=None, premio=0):
        ev = self.evento
        self.evento = None
        self.t_evento = random.uniform(100, 220)
        if not ev:
            return
        for p in ev.get("personas", []):
            if p in self.personas and (not p.muerto or p.tipo == "civil"):
                p.tag = None
                if p.tipo != "civil":
                    self.personas.remove(p)
        o = ev.get("objeto")
        if o is not None and o in self.objetos:
            if o.canal:
                o.canal.parar()
            self.objetos.remove(o)
        if premio:
            self.j.stats["eventos"] = self.j.stats.get("eventos", 0) + 1
            self.dar_dinero(premio)
            self.cambiar_ciudadania(2.0)
        if texto:
            self.decir(texto)

    def _eventos(self, dt):
        j = self.j
        ev = self.evento
        if ev:
            ev["t"] -= dt
            malos = [p for p in ev.get("personas", []) if p.tipo == "enemigo"]
            if ev["tipo"] in ("atraco", "banda") and malos and all(p.muerto for p in malos):
                premio = ev["premio"]
                self._fin_evento("La víctima te da las gracias y una recompensa." if ev["tipo"] == "atraco" else "Los vecinos, agradecidos, hacen una colecta para ti.", premio)
            elif ev["tipo"] == "maletin" and ev["objeto"] not in self.objetos:
                self.j.stats["eventos"] = self.j.stats.get("eventos", 0) + 1
                self._fin_evento()
            elif ev["t"] <= 0:
                self._fin_evento({"atraco": "El atracador ha huido con el botín.", "banda": "Los pandilleros se han marchado.",
                                  "maletin": "Alguien ha encontrado el maletín antes que tú."}[ev["tipo"]])
            return
        if self.mision or self.trabajo or j.estrellas or self.mundo.tipo in ("mar", "isla") or self.transicion or not self.cfg["sucesos"]:
            return
        self.t_evento -= dt
        if self.t_evento > 0:
            return
        tipo = random.choice(["atraco", "banda", "maletin", "maletin"])
        pos = self._punto_cercano(45, 80)
        if pos is None:
            self.t_evento = 20
            return
        x, y = pos
        self.son("evento", cat="interfaz")
        if tipo == "maletin":
            o = Objeto("dinero", "Maletín perdido", x, y)
            o.valor = random.randint(150, 600)
            self.objetos.append(o)
            self.evento = {"tipo": tipo, "t": 150.0, "objeto": o}
            self.decir(f"Suceso: alguien ha perdido un maletín por aquí cerca. {self.situar(x, y, 'Está')}. Búscalo con el radar, pulsando Tabulador.")
            return
        personas = []
        if tipo == "atraco":
            v = Persona("civil", x, y, "Víctima del atraco")
            v.estado = "quieto"
            v.tag = "evento"
            personas.append(v)
            n = 1
            nombre = "Atracador"
        else:
            n = random.randint(2, 3)
            nombre = "Pandillero"
        for _ in range(n):
            e = Persona("enemigo", *self.mundo.punto_libre(x + random.uniform(-3, 3), y + random.uniform(-3, 3)), nombre)
            e.salud = 55.0
            e.arma = random.choice(["navaja", "pistola", "bate"])
            e.hostil = True
            e.estado = "ataca"
            e.activo = False
            e.tag = "evento"
            personas.append(e)
        self.personas += personas
        self.evento = {"tipo": tipo, "t": 110.0, "personas": personas, "premio": random.randint(150, 400) * n}
        if tipo == "atraco":
            self.son("grito", xy=(x, y), ref=10, maxd=120)
            self.decir(f"Suceso: están atracando a alguien. {self.situar(x, y, 'Ocurre')}. Si quieres ayudar, pulsa Q para fijar al atracador.")
        else:
            self.decir(f"Suceso: unos pandilleros tienen atemorizada la calle. {self.situar(x, y, 'Están')}. Si quieres echarlos, pulsa Q para fijarlos.")

    # ------------------------------------------------------ encargos repetibles
    def _empezar_repetible(self, m):
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        m["repetible"] = True
        m.setdefault("requiere", [])
        self.iniciar_mision(m)

    def empezar_contrato(self, l):
        dest = self._destino_azar(150, 900, l)
        n = min(5, 1 + self.j.stats.get("contratos", 0) // 2)
        quien = random.choice(NOMBRES)
        armas = ["pistola", "pistola", "subfusil", "escopeta", "navaja"]
        self._empezar_repetible({
            "id": "contrato", "titulo": f"Contrato: {quien}", "lugar": l.id, "contador": "contratos",
            "pasos": [
                {"tipo": "eliminar", "lugar": dest.id, "texto": f"El objetivo, {quien}, está en {dest.nombre} con {n} guardaespaldas. Ve allí y cumple el contrato.",
                 "enemigos": [{"n": 1, "tipo": f"Objetivo, {quien}", "arma": "pistola", "salud": 95}] + [{"n": 1, "tipo": "Guardaespaldas", "arma": random.choice(armas), "salud": 70} for _ in range(n)]},
                {"tipo": "ir", "lugar": l.id, "texto": f"Contrato cumplido. Vuelve a {l.nombre} a cobrar."}],
            "recompensa": {"dinero": 600 + 380 * n}})

    def empezar_atraco_banco(self, l):
        self.atracadas["banco:" + l.id] = self.dia
        self._empezar_repetible({
            "id": "atraco_banco", "titulo": f"Atraco a {l.nombre}", "lugar": l.id, "contador": "atracos",
            "pasos": [
                {"tipo": "eliminar", "lugar": l.id, "ya": True, "texto": "¡Esto es un atraco! Acaba con los vigilantes de seguridad.",
                 "enemigos": [{"n": 3, "tipo": "Vigilante de seguridad", "arma": "pistola", "salud": 80}, {"n": 2, "tipo": "Vigilante de seguridad", "arma": "subfusil", "salud": 85}]},
                {"tipo": "recoger", "lugar": l.id, "objeto": "Botín de la cámara acorazada", "texto": "La cámara acorazada está abierta. Recoge el botín."},
                {"tipo": "policia", "nivel": 4, "texto": "¡Ha saltado la alarma silenciosa! Despista a la policía para quedarte el botín."}],
            "recompensa": {"dinero": random.randint(7000, 13000)}})

    def empezar_encargo_coche(self, l):
        ids = [i for i in MODELOS_ENCARGO if i in self.modelos]
        mo = self.modelos[random.choice(ids)]
        donde = self._destino_azar(150, 800, l)
        self._empezar_repetible({
            "id": "encargo_coche", "titulo": f"Encargo: {mo['nombre']}", "lugar": l.id, "contador": "encargos",
            "pasos": [
                {"tipo": "robar", "modelo": mo["id"], "lugar": donde.id, "nombre": f"{mo['nombre']} de encargo", "busqueda": 1,
                 "texto": f"Un cliente quiere un {mo['nombre']}. Hay uno aparcado junto a {donde.nombre}. Róbalo."},
                {"tipo": "entregar", "lugar": l.id, "salud_min": 50, "texto": f"Lleva el vehículo a {l.nombre} en buen estado."}],
            "recompensa": {"dinero": int(mo["valor"] * 1.5) + 350}})

    def empezar_boxeo(self, l):
        g = self.j.stats.get("boxeo", 0)
        rival = random.choice(["el Martillo", "la Apisonadora", "Puños de Hierro", "el Yunque", "la Cobra", "Mandíbula de Cristal"])
        self.j.arma = "punos"
        self._empezar_repetible({
            "id": "boxeo", "titulo": f"Combate contra {rival}", "lugar": l.id, "contador": "boxeo",
            "pasos": [{"tipo": "eliminar", "lugar": l.id, "ya": True, "texto": f"¡Suena la campana! Tu rival es {rival}. Pulsa Q para fijarlo y Espacio para golpear.",
                       "enemigos": [{"n": 1, "tipo": rival.capitalize() if rival[0].islower() else rival, "arma": "punos", "salud": 60 + 22 * g}]}],
            "recompensa": {"dinero": 150 + 110 * g}})
        self.son("campana_ring", cat="interfaz")

    # --------------------------------------------------------------- servicios
    def plaza_cercana(self):
        """Hueco junto al bordillo de la calle más cercana al jugador."""
        x, y = self.pos()
        return self.mundo.plaza_en(x, y)
