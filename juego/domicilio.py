"""Comida y bebida a domicilio (1.7.1): desde una casa tuya, por el móvil o en el menú de la casa.

Eliges de la carta, pagas el pedido y el envío, y al cabo de un rato, que cambia cada vez, llaman al timbre. Si estás en
casa, te lo dan y te lo tomas: quita el hambre y la sed de la vida realista y da algo de salud. Si no estás, el
repartidor te llama, espera un rato en la puerta y se va con el pedido.

La carta está en los datos (vida.json, carta_domicilio), los tiempos y las frases en la sección domicilio, y el envío
en las tarifas (domicilio_envio). Un mod puede cambiarlo todo.
"""
import math
import random

from . import gente as G
from .ajustes import Ajustes

AJ = Ajustes("domicilio", {"espera_min": 22, "espera_max": 40, "lluvia_extra": 25, "tope_cosas": 4, "espera_puerta": 20, "busqueda_max": 1, "radio_casa": 28},
             {"locales": ["Casa Paca", "El Fogón de Lola", "Bocatería La Esquina", "Asador El Puerto", "La Cazuela", "Pollos Remigio", "Wok del Muelle"],
              "frases_pedido": ["{local}, dígame. Apuntado: {cosas}. En unos {minutos} minutos lo tiene en {casa}.",
                                "{local}. Marchando: {cosas}. Tardamos unos {minutos} minutos, que hoy hay faena.",
                                "Ha llamado a {local}. Tomo nota: {cosas}. Sale para {casa} en cuanto esté; calcule {minutos} minutos."],
              "frases_llega": ["{nombre}, de {local}: su pedido. Que aproveche.", "Buenas, traigo lo de {local}. Aquí tiene. Hasta otra.",
                               "{nombre}, de {local}. Todavía quema, tenga cuidado. Buen provecho.", "Pedido de {local}. Perdone la espera, que estaba el tráfico imposible."],
              "frases_espera": ["Te llama {nombre}, de {local}: está en la puerta de {casa} con tu pedido y dice que te espera {minutos} minutos.",
                                "Suena el móvil: {nombre}, de {local}, ha llamado al timbre de {casa} y no abre nadie. Te espera {minutos} minutos."],
              "frases_se_va": ["{nombre}, de {local}, se ha cansado de esperar en la puerta de {casa} y se ha llevado el pedido. No te devuelven el dinero.",
                               "Nadie abrió en {casa}: {nombre} se ha vuelto a {local} con tu pedido. Lo pagado, pagado está."],
              "frases_come": ["Te lo tomas en la cocina, sin prisa.", "Cenas en el sofá, con la tele puesta.", "Te lo comes de pie, junto a la ventana.", "Pones la mesa para ti y das cuenta de todo."]},
             cero=("lluvia_extra", "busqueda_max"))

CARTA = [
    {"id": "bocadillo", "nombre": "Bocadillo de calamares", "tipo": "comida", "precio": 7, "hambre": 40, "sed": 0, "salud": 15},
    {"id": "pizza_casa", "nombre": "Pizza familiar", "tipo": "comida", "precio": 13, "hambre": 70, "sed": 0, "salud": 25},
    {"id": "menu_dia", "nombre": "Menú del día, dos platos y postre", "tipo": "comida", "precio": 16, "hambre": 100, "sed": 20, "salud": 40},
    {"id": "agua_grande", "nombre": "Botella grande de agua", "tipo": "bebida", "precio": 2, "hambre": 0, "sed": 80, "salud": 0},
    {"id": "refresco", "nombre": "Refresco de limón", "tipo": "bebida", "precio": 3, "hambre": 5, "sed": 60, "salud": 3},
]


def carta(p):
    lista = [c for c in p.datos.get("carta_domicilio", []) if isinstance(c, dict) and c.get("nombre")]
    return lista or CARTA


def efecto_txt(c):
    partes = []
    if c.get("hambre"):
        partes.append("quita hambre")
    if c.get("sed"):
        partes.append("quita sed")
    if c.get("salud"):
        partes.append(f"da {int(c['salud'])} de salud")
    return ", ".join(partes) or "sin efecto"


class Domicilio:
    """Mixin de Partida."""

    def _ahora(self):
        return self.dia * 1440.0 + self.reloj

    def casa_aqui(self, radio=None):
        """La casa tuya en la que estás o que tienes al lado, o None."""
        if self.mundo.tipo == "mar":
            return None
        x, y = self.pos()
        radio = AJ("radio_casa") if radio is None else radio
        casas = [l for l in self.mundo.lugares.values() if l.tipo == "casa" and l.id in self.j.propiedades and math.hypot(l.x - x, l.y - y) <= radio]
        return min(casas, key=lambda l: math.hypot(l.x - x, l.y - y)) if casas else None

    def domicilio_motivo(self):
        """Por qué no se puede pedir ahora, o cadena vacía si se puede."""
        j = self.j
        if self.casa_aqui() is None:
            return "Para pedir comida a domicilio tienes que estar en una casa tuya, o en su puerta."
        if j.pedido:
            return "Ya tienes un pedido en camino. " + self.pedido_txt()
        if j.estrellas > AJ("busqueda_max"):
            return "Con la policía buscándote así, ningún repartidor se acerca a tu puerta."
        return ""

    def pedido_txt(self):
        d = self.j.pedido
        if not d:
            return "No has pedido nada."
        casa = self.lug(d.get("casa"))
        donde = self.nombre_lugar(casa) if casa else "tu casa"
        if d.get("estado") == "puerta":
            return f"{d['nombre']}, de {d['local']}, espera en la puerta de {donde} con tu pedido."
        falta = max(1, int(round(d["llega"] - self._ahora())))
        return f"Tu pedido de {d['local']} llega a {donde} en unos {falta} minutos."

    def pedir_domicilio(self, cosas, rng=random):
        """Hace el pedido: lo cobra y deja en camino al repartidor. Devuelve True si se ha hecho."""
        j = self.j
        motivo = self.domicilio_motivo()
        if motivo or not cosas:
            self.app.son("error")
            self.decir(motivo or "No has elegido nada de la carta.", True)
            return False
        casa = self.casa_aqui()
        total = sum(int(c.get("precio", 0)) for c in cosas) + self.precio("domicilio_envio", 3)
        if not self.pagar(total):
            return False
        minutos = AJ.entre("espera_min", "espera_max", rng) * (1.0 + AJ("lluvia_extra") / 100.0 if self.lluvia else 1.0)
        local = rng.choice(AJ.lista("locales"))
        nombre = rng.choice(G.nombres(rng.choice("hm")))
        j.pedido = {"casa": casa.id, "cosas": [dict(c) for c in cosas], "llega": self._ahora() + minutos, "estado": "camino", "local": local, "nombre": nombre, "total": total}
        j.stats["pedidos"] = j.stats.get("pedidos", 0) + 1
        self.son("movil", cat="interfaz", vol=0.6)
        lista = ", ".join(c["nombre"].lower() for c in cosas)
        self.decir(AJ.frase("frases_pedido", rng, local=local, cosas=lista, minutos=int(round(minutos / 5.0)) * 5 or 5, casa=casa.nombre) + f" Pagas {total} euros, con el envío.", True)
        return True

    def _en_esa_casa(self, d):
        casa = self.lug(d.get("casa"))
        if casa is None or casa.mapa != self.mundo.id:
            return None
        x, y = self.pos()
        return casa if math.hypot(casa.x - x, casa.y - y) <= AJ("radio_casa") + 6 else None

    def actualizar_domicilio(self, dt):
        d = self.j.pedido
        if not d or self.transicion:
            return
        if self.lug(d.get("casa")) is None or d.get("casa") not in self.j.propiedades:      # la casa ya no es tuya, o era de un mod que no está
            self.j.pedido = None
            return
        ahora = self._ahora()
        if ahora < d["llega"]:
            return
        casa = self._en_esa_casa(d)
        if casa is not None:
            self._entregar_pedido(d, casa)
        elif d.get("estado") == "camino":
            d["estado"] = "puerta"
            d["hasta"] = ahora + AJ("espera_puerta")
            lugar = self.lug(d["casa"])
            self.son("movil", cat="interfaz")
            self.decir(AJ.frase("frases_espera", nombre=d["nombre"], local=d["local"], casa=self.nombre_lugar(lugar), minutos=AJ.entero("espera_puerta")))
        elif ahora > d.get("hasta", ahora):
            lugar = self.lug(d["casa"])
            self.j.pedido = None
            self.son("animo_baja", cat="interfaz", vol=0.6)
            self.decir(AJ.frase("frases_se_va", nombre=d["nombre"], local=d["local"], casa=self.nombre_lugar(lugar)))

    def _entregar_pedido(self, d, casa):
        j = self.j
        j.pedido = None
        self.son("timbre", xy=(casa.x, casa.y), ref=12, maxd=90)
        self.son("puerta_entrar", xy=(casa.x, casa.y), ref=8, maxd=60, vol=0.6)
        comida = sum(float(c.get("hambre", 0)) for c in d["cosas"])
        bebida = sum(float(c.get("sed", 0)) for c in d["cosas"])
        salud = sum(float(c.get("salud", 0)) for c in d["cosas"])
        if comida:
            self.ha_comido(comida)
            self.mez.sonar("comer", cat="interfaz")
        if bebida:
            self.ha_bebido(bebida)
            if not comida:
                self.mez.sonar("beber", cat="interfaz")
        j.salud = min(j.salud_max, j.salud + salud)
        self.cambiar_animo(2)
        if casa.id == j.convive_casa and j.convive:              # era lo que te había pedido quien vive contigo
            self.peticion_cumplida("cena")
        self.decir("Llaman al timbre. " + AJ.frase("frases_llega", nombre=d["nombre"], local=d["local"]) + " " + AJ.frase("frases_come")
                   + f" Salud {int(j.salud)}.{self.necesidades_txt()}")


def menu_domicilio(p):
    """La carta: Intro añade o quita cada cosa del pedido, y la última opción lo encarga."""
    from .menus import Menu, Opcion
    app = p.app
    motivo = p.domicilio_motivo()
    if motivo:
        app.son("error" if not p.j.pedido else "notificacion")
        app.decir(motivo, True)
        return
    casa = p.casa_aqui()
    elegidas = []
    tope = AJ.entero("tope_cosas")
    envio = p.precio("domicilio_envio", 3)

    def total():
        return sum(int(c.get("precio", 0)) for c in elegidas)

    def alternar(c):
        def f():
            if c in elegidas:
                elegidas.remove(c)
                app.decir(f"Quitas {c['nombre'].lower()} del pedido. Llevas {len(elegidas)}.", True)
            elif len(elegidas) >= tope:
                app.son("error")
                app.decir(f"En un pedido caben {tope} cosas como mucho.", True)
            else:
                elegidas.append(c)
                app.decir(f"Añades {c['nombre'].lower()}. Llevas {len(elegidas)}: {total()} euros, más {envio} de envío.", True)
            m.refrescar(False)
        return f

    def encargar():
        if p.pedir_domicilio(list(elegidas)):
            app.cerrar(m)

    def ops():
        lista = [Opcion((lambda c=c: f"{c['nombre']}: {int(c.get('precio', 0))} euros, {efecto_txt(c)}" + (". En el pedido" if c in elegidas else "")), alternar(c),
                        ayuda=(c.get("desc") or "") + " Intro lo añade al pedido, y otra vez lo quita. El hambre y la sed solo cuentan con la vida realista activada; la salud, siempre.")
                 for c in carta(p)]
        lista.append(Opcion(lambda: f"Hacer el pedido: {len(elegidas)} cosas, {total() + envio} euros con el envío" if elegidas else "Hacer el pedido: todavía no has elegido nada", encargar,
                            ayuda=f"Lo traen a {casa.nombre} en unos {AJ.entero('espera_min')} a {AJ.entero('espera_max')} minutos del juego, más si llueve. "
                                  "Cuando llegue, llaman al timbre: si estás en casa, te lo tomas en el acto. Si no estás, el repartidor te llama, espera un rato en la puerta y se va."))
        return lista
    m = Menu(app, lambda: f"Comida a domicilio en {casa.nombre}. Tienes {p.j.dinero} euros", ops, intro="Intro añade cada cosa al pedido. Al final, Hacer el pedido")
    app.abrir(m)
