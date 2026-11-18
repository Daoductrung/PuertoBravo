"""Hablar con cualquiera: cada persona de la calle tiene nombre, edad, oficio, carácter y memoria.

Con la tecla J, a pie, hablas con quien tengas al lado. Puedes elegir qué decir en un menú o escribir lo
que quieras: el juego entiende la intención (saludar, preguntar por un sitio, pedir un favor, hacer un
cumplido, amenazar...) y la persona responde según su carácter, su humor y la confianza que te tenga.

Modo IA (opcional): si el jugador lo activa, lo que escriba se envía a una inteligencia artificial (local o
de internet) junto con la ficha de la persona, y la respuesta es libre. Sin eso, contesta el motor propio,
sin conexión: las intenciones de este archivo y la base de respuestas por temas de respuestas.py.
"""
import json
import math
import random

from . import gente as G
from . import mundo as M

# Los nombres, los apellidos, los oficios y los caracteres de la gente salen de los datos (data/datos/gente.json): los lleva gente.py.
CARACTERES = G.CARACTERES
SITIOS = {"comer": ("comida", "pizzeria", "taberna", "bar"), "curarme": ("hospital", "farmacia"), "dinero": ("banco", "empenos"), "armas": ("armeria",),
          "trabajo": ("empleo",), "dormir": ("hotel",), "taller": ("taller",), "policía": ("comisaria",), "comprar": ("tienda",), "fiesta": ("club", "casino", "bar")}
PALABRAS = [
    ("despedir", ("adiós", "adios", "hasta luego", "me voy", "chao", "nos vemos")),
    ("amenazar", ("dame", "la cartera", "te mato", "te voy a", "amenaz", "o te")),
    ("insultar", ("idiota", "imbécil", "imbecil", "gilipollas", "estúpid", "estupid", "cabr", "capull", "tont", "asco")),
    ("ligar", ("guap", "ligar", "me gustas", "tomar algo conmigo", "cita", "tu número", "tu numero", "teléfono", "telefono", "cena conmigo", "salir conmigo")),
    ("limosna", ("toma", "te doy", "quédate", "quedate", "para ti", "propina")),
    ("invitar", ("invito", "un café", "un cafe", "una caña", "una cana", "tomar algo")),
    ("chiste", ("chiste", "sabes aquel", "te cuento uno")),
    ("cumplido", ("qué bien", "que bien", "me encanta", "bonit", "eleg", "simpátic", "simpatic", "majo", "maja", "genial")),
    ("amistad", ("amigos", "amig", "quedar otro día", "quedar otro dia", "nos vemos más", "nos vemos mas")),
    ("rumor", ("qué se cuenta", "que se cuenta", "novedad", "noticias", "qué pasa", "que pasa", "cotilleo", "rumor")),
    ("barrio", ("barrio", "zona", "por aquí", "por aqui", "este sitio", "el pueblo", "la ciudad")),
    ("trabajo_npc", ("a qué te dedicas", "a que te dedicas", "trabajas", "tu trabajo", "oficio")),
    ("saludar", ("hola", "buenas", "buenos días", "buenos dias", "qué tal", "que tal", "saludos", "hey")),
]


def oficio_para(edad, rng=random, genero="h"):
    """Un oficio que cuadre con la edad: nadie estudia a los sesenta ni se jubila a los veinte."""
    return G.oficio_para(edad, genero, rng)


def ficha(persona, rng=random):
    """Da a una persona de la calle su identidad, la primera vez que hace falta."""
    if getattr(persona, "ficha", None):
        return persona.ficha
    g = rng.choice("hm")
    if hasattr(persona, "tono"):                                 # su voz ya se ha oído: que el nombre vaya con ella
        g = "m" if persona.tono > 1.1 else "h"
    edad = rng.randint(19, 74)
    f = {"nombre": rng.choice(G.nombres(g)), "apellido": rng.choice(G.lista("apellidos")), "genero": g, "edad": edad, "oficio": oficio_para(edad, rng, g),
         "caracter": rng.choice(list(CARACTERES)), "confianza": 0, "frases": 0, "disponible": rng.random() < 0.55,
         "le_atraen": rng.choice(["h", "m", "hm"]), "invitado": False, "limosna": False, "presentado": False, "ofendido": False}
    persona.ficha = f
    return f


def interpretar(texto):
    """Qué quiere decir el jugador con lo que ha escrito. Devuelve (intención, dato)."""
    t = " " + (texto or "").lower().strip() + " "
    if not t.strip():
        return "nada", None
    if any(x in t for x in ("dónde", "donde", "cómo llego", "como llego", "busco", "hay algún", "hay algun", "necesito")):
        for clave, tipos in SITIOS.items():
            if clave in t or any(tp in t for tp in tipos) or (clave == "comer" and any(x in t for x in ("restaurante", "hambre", "cenar", "bar"))) \
                    or (clave == "curarme" and any(x in t for x in ("médico", "medico", "herid"))) or (clave == "dinero" and "cajero" in t):
                return "sitio", clave
        return "sitio", None
    for intencion, claves in PALABRAS:
        if any(c in t for c in claves):
            return intencion, None
    return "otra", None


class Charla:
    """Mixin de Partida."""

    def persona_para_hablar(self):
        j = self.j
        if j.veh:
            return None
        cerca = [q for q in self.personas if q.tipo == "civil" and not q.muerto and not q.hostil and q.dist(j.x, j.y) < 5.0]
        return min(cerca, key=lambda q: q.dist(j.x, j.y)) if cerca else None

    def hablar(self):
        j = self.j
        if j.veh:
            return
        q = self.persona_para_hablar()
        if q is None and self.sv_hablar_cerca():                 # en un servidor: hablarle al jugador que tienes al lado
            return
        if q is None:
            self.decir("No tienes a nadie al lado para hablar. Acércate a alguien: el radar, con Tabulador, te dice quién hay cerca.", True)
            return
        f = ficha(q)
        if f["ofendido"]:
            self.son("rechazo", cat="interfaz")
            self.decir(f"{f['nombre'] if f['presentado'] else 'Esa persona'} no quiere saber nada de ti.", True)
            return
        if q.estado == "huye":
            self.decir("Está huyendo y no se para a hablar.", True)
            return
        from . import menus_charla
        menus_charla.conversar(self, q)

    def _trato(self, f, n):
        antes = f["confianza"]
        f["confianza"] = max(-100, min(100, f["confianza"] + n))
        if n and (f["confianza"] // 20) != (antes // 20):
            self.son("afinidad_sube" if n > 0 else "afinidad_baja", cat="interfaz", vol=0.6)

    def confianza_txt(self, f):
        c = f["confianza"]
        return ("te mira con desconfianza" if c < -10 else "apenas te conoce" if c < 15 else "le caes bien" if c < 40 else "te tiene confianza" if c < 70 else "te considera de los suyos")

    def presentacion(self, q):
        f = ficha(q)
        if not f["presentado"]:
            f["presentado"] = True
            q.nombre = f["nombre"]
            self.j.stats["charlas"] = self.j.stats.get("charlas", 0) + 1
        return f"{f['nombre']}{' ' + f['apellido'] if f.get('apellido') else ''}, {f['edad']} años, {f['oficio']}. Te habla {G.caracter(f['caracter'])['desc']}"

    def responder(self, q, intencion, dato=None):
        """Lo que contesta una persona a una intención. Devuelve el texto y aplica las consecuencias."""
        j = self.j
        f = ficha(q)
        c = G.caracter(f["caracter"])
        nombre = f["nombre"]
        f["frases"] += 1
        self.son("murmullo", xy=(q.x, q.y), vol=0.5)
        if intencion == "saludar":
            self._trato(f, c["saludo"] if f["frases"] <= 2 else 1)
            return random.choice([f"{nombre}: Hola, ¿qué tal? Aquí andamos.", f"{nombre}: Buenas. ¿Nos conocemos?", f"{nombre}: Hombre, muy buenas.", f"{nombre}: Hola. Soy {nombre}, {f['oficio']}."])
        if intencion == "trabajo_npc":
            self._trato(f, 2)
            return f"{nombre}: Soy {f['oficio']}. " + random.choice(["No me quejo.", "Se hace lo que se puede.", "Y con lo que pagan, ya ves.", "Me gusta, la verdad."])
        if intencion == "barrio":
            x, y = self.pos()
            b = self.mundo.barrio(x, y)
            self._trato(f, 3)
            return f"{nombre}: Esto es {b['nombre']}. {self.barrio_desc(b)}".strip()
        if intencion == "rumor":
            self._trato(f, 2)
            return f"{nombre}: " + self.rumor()
        if intencion == "sitio":
            tipos = SITIOS.get(dato) if dato else None
            if not tipos:
                return f"{nombre}: ¿Qué buscas exactamente? Dime si quieres comer, curarte, sacar dinero, trabajo, dormir, un taller, comprar o la policía."
            x, y = self.pos()
            cand = [l for l in self.mundo.lugares.values() if l.tipo in tipos]
            if not cand:
                return f"{nombre}: Aquí no hay nada de eso. Tendrás que ir a otra localidad."
            l = min(cand, key=lambda l: math.hypot(l.x - x, l.y - y))
            self.gps_a_lugar(l, callar=True)
            self._trato(f, 2)
            return f"{nombre}: Lo más cerca es {l.nombre}, {M.metros(math.hypot(l.x - x, l.y - y))}, {self.direccion_txt(l.x, l.y)}. Te lo marco en el GPS."
        if intencion == "cumplido":
            self._trato(f, c["cumplido"] if f["frases"] <= 6 else 1)
            self.cambiar_animo(1)
            return random.choice([f"{nombre}: Vaya, muchas gracias. No me lo esperaba.", f"{nombre}: Qué cosas dices. Gracias.", f"{nombre}: Se agradece, que hoy no era mi día."])
        if intencion == "chiste":
            gracia = random.random() < 0.6 + c["chiste"] / 40.0
            self._trato(f, c["chiste"] if gracia else -2)
            if gracia:
                self.cambiar_animo(2)
            return f"{nombre}: " + (random.choice(["¡Ja! Ese no me lo sabía.", "Qué malo eres, pero me he reído.", "Buenísimo. Se lo cuento a mi cuñado."]) if gracia
                                    else random.choice(["Ya. Muy gracioso.", "No lo pillo.", "Ese es más viejo que el puerto."]))
        if intencion == "invitar":
            if f["invitado"]:
                return f"{nombre}: Ya me has invitado antes. Otro día me toca a mí."
            if j.dinero < self.precio("cafe_invitar", 4):
                return f"{nombre}: Si no llevas ni para ti. Déjalo."
            j.dinero -= self.precio("cafe_invitar", 4)
            f["invitado"] = True
            self.son("caja", cat="interfaz", vol=0.5)
            self.pasar_horas(0.3)
            self._trato(f, 12)
            self.cambiar_animo(3)
            return f"Le invitas a un café por {self.precio('cafe_invitar', 4)} euros. {nombre}: Pues mira, te lo acepto. " + random.choice(["Me cuenta su vida durante un rato.", "Habláis de todo un poco.", "Resulta que conoce a media ciudad."])
        if intencion == "limosna":
            if j.dinero < self.precio("limosna", 10):
                return f"{nombre}: Guárdate eso, que te hace más falta a ti."
            j.dinero -= self.precio("limosna", 10)
            self.son("donativo", cat="interfaz", vol=0.6)
            self._trato(f, 10 if not f["limosna"] else 2)
            if not f["limosna"]:
                self.cambiar_ciudadania(1.5)
            f["limosna"] = True
            return f"Le das {self.precio('limosna', 10)} euros. {nombre}: " + random.choice(["Gracias, de verdad. No hay mucha gente así.", "No hacía falta, pero gracias.", "Que te lo paguen con salud."])
        if intencion == "amistad":
            if any(k["nombre"] == nombre and k["oficio"] == f["oficio"] for k in j.conocidos):
                return f"{nombre}: Si ya tienes mi número. Llámame cuando quieras."
            if f["confianza"] < 30:
                return f"{nombre}: Bueno, ya nos iremos viendo. Aún no te conozco tanto."
            j.conocidos.append({"nombre": nombre, "genero": f["genero"], "edad": f["edad"], "oficio": f["oficio"], "caracter": f["caracter"], "mapa": self.mundo.id, "dia": self.dia, "ultimo": 0})
            del j.conocidos[:-30]
            self.son("pareja", cat="interfaz", vol=0.5)
            self.cambiar_animo(4)
            return f"{nombre}: Venga, apunta mi número. Ya tienes a {nombre} entre tus conocidos, en el móvil."
        if intencion == "insultar":
            self._trato(f, c["insulto"])
            f["ofendido"] = True
            self.cambiar_ciudadania(-1.0)
            if random.random() < c["valor"] * 0.5:
                q.hostil, q.estado, q.tipo, q.arma = True, "ataca", "enemigo", None
                return f"{nombre}: ¿Qué me has llamado? ¡Te vas a enterar! Se te echa encima."
            q.estado, q.t_estado = "huye", 8
            return f"{nombre}: " + random.choice(["Menudo personaje. Ahí te quedas.", "No tengo por qué aguantar esto.", "Vete a paseo."]) + " Se marcha."
        if intencion == "amenazar":
            f["ofendido"] = True
            self._trato(f, -60)
            self.cambiar_ciudadania(-2.0)
            self.cambiar_reputacion(1)
            if random.random() < c["valor"]:
                self.delito(1, "amenazas")
                q.estado, q.t_estado = "huye", 12
                self.son("grito", xy=(q.x, q.y), vol=0.6, tono=getattr(q, "tono", 1.0))
                return f"{nombre}: ¡Socorro! ¡Policía! Sale corriendo dando voces."
            botin = random.randint(8, 45)
            j.dinero += botin
            q.atracado = True
            q.estado, q.t_estado = "huye", 12
            self.delito(1, "amenazas")
            return f"{nombre}, con miedo, te tira {botin} euros y echa a correr."
        if intencion == "despedir":
            return f"{nombre}: " + random.choice(["Hasta luego.", "Venga, que te vaya bien.", "Nos vemos.", "Cuídate."])
        return f"{nombre}: " + random.choice(["No sé qué decirte.", "Ya. Bueno.", "Puede ser, puede ser.", "Mira, de eso no entiendo.", "¿Tú crees?"])

    def rumor(self):
        """Algo que se cuenta por la calle: sale de lo que de verdad pasa en la partida."""
        j = self.j
        ops = ["Dicen que va a cambiar el tiempo." if not self.lluvia else "Con esta lluvia no hay quien salga.",
               f"Hoy es el día {self.dia} desde que volviste, que se dice pronto."]
        if self.dia_txt():
            ops += [self.dia_txt()] * 2
        if j.estrellas:
            ops.append("La policía anda buscando a alguien por aquí. Yo no he visto nada.")
        if len(self.completadas) >= 5:
            ops.append("Se oye que hay alguien moviendo los hilos en el puerto. Gente nueva.")
        if j.ciudadania >= 45:
            ops.append("Hablan bien de ti en el barrio. Dicen que eres de fiar.")
        if j.reputacion >= 40:
            ops.append("Contigo no quiero líos, que ya sé quién eres.")
        if j.territorios:
            ops.append("Desde que cambió de manos el barrio, la cosa está más tranquila.")
        disp = self.misiones_disponibles()
        if disp:
            l = self.lugares.get(disp[0]["lugar"])
            if l is not None:
                ops.append(f"En {self.nombre_lugar(l)} buscan a alguien para un trabajo. Yo no me metería.")
        return random.choice(ops)

    def llamar_conocido(self, k):
        """Un conocido te cuenta algo útil, una vez al día."""
        if k.get("ultimo") == self.dia:
            return f"{k['nombre']} ya te ha contado hoy todo lo que sabía."
        k["ultimo"] = self.dia
        self.cambiar_animo(2)
        return f"{k['nombre']}: {self.rumor()}"

    # ------------------------------------------------------------------ modo IA
    def ia_disponible(self):
        from . import ia
        return self.cfg["ia_activa"] and ia.disponible(self.cfg)

    def responder_libre(self, q, texto):
        """Respuesta a un texto libre: con el modo IA si está activo; si no, con el motor propio."""
        f = ficha(q)
        if self.ia_disponible():
            from . import ia
            r = ia.responder(self, q, texto)
            if r is not None:
                self.son("murmullo", xy=(q.x, q.y), vol=0.5)
                self._trato(f, max(-15, min(15, int(r.get("confianza", 0)))))
                if r.get("accion") == "se_va":
                    q.estado, q.t_estado = "huye", 6
                elif r.get("accion") == "se_enfada":
                    f["ofendido"] = True
                f.setdefault("memoria", []).append((texto, r["respuesta"]))
                del f["memoria"][:-6]
                return f"{f['nombre']}: {r['respuesta']}"
        intencion, dato = interpretar(texto)
        if intencion == "nada":
            return "No has dicho nada."
        if intencion in ("otra", "saludar", "cumplido", "barrio", "invitar", "limosna"):
            # Sin modo IA: la base de respuestas. Si lo escrito toca un tema conocido, manda el tema antes que una intención floja.
            from . import respuestas
            if intencion == "otra" or respuestas.tema_de(texto) is not None:
                x, y = self.pos()
                frase, cambio, _ = respuestas.responder(texto, f, {"barrio": self.mundo.barrio(x, y)["nombre"], "ciudad": self.mundo.nombre,
                                                                    "hora": self.hora_txt(), "tu": self.j.nombre})
                f["frases"] += 1
                self.son("murmullo", xy=(q.x, q.y), vol=0.5)
                if cambio:
                    self._trato(f, cambio if f["frases"] <= 12 else 0)
                return f"{f['nombre']}: {frase}"
        if intencion == "ligar":
            return self.ligar(q) if self.modo_adulto() else f"{f['nombre']}: " + random.choice(["Gracias, pero no.", "Qué cosas tienes."])
        return self.responder(q, intencion, dato)


def descripcion_json(f):
    return json.dumps({k: f[k] for k in ("nombre", "genero", "edad", "oficio", "caracter", "confianza")}, ensure_ascii=False)
