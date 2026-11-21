"""La bolsa de la comarca (1.7.2): que se note para qué sirve tener acciones.

En los bancos se compran y se venden acciones de las empresas de la comarca. Hasta ahora los precios se movían cada
medianoche, pero el juego no decía nada: quien compraba no sabía si ganaba o perdía. Ahora:
- Cada medianoche, si tienes acciones, el juego dice cuánto valen y cuánto ganas o pierdes desde que las compraste.
- Algunas empresas reparten dividendos cada pocos días: un tanto por ciento del precio por acción, que llega solo.
- Hay noticias: de vez en cuando una empresa da un salto, arriba o abajo, y se cuenta por qué. Si tienes acciones de
  ella, te enteras al momento; si no, está en el menú de la bolsa.
- El menú dice el precio, cuánto ha cambiado desde ayer, lo que tienes, lo que pagaste y lo que ganas o pierdes.

Las empresas, sus precios de partida, cuánto se mueven, sus dividendos y sus noticias están en los datos (vida.json,
secciones bolsa y bolsa_empresas). La historia sigue moviendo algunas, como antes.
"""
from .i18n import tr
import random

from .ajustes import Ajustes

AJ = Ajustes("bolsa", {
    "dividendo_dias": 7, "noticia_prob": 12, "noticia_min": 8, "noticia_max": 25, "vuelta_al_precio": 3, "aviso_diario": 1,
}, {
    "frases_informe": [tr("Bolsa: tus acciones valen {valor} euros, {cambio} que ayer. Desde que las compraste, {balance}."),
                       tr("Cierre de la bolsa: tu cartera vale {valor} euros, {cambio} que ayer. En total, {balance}.")],
    "frases_dividendo": [tr("{empresa} reparte dividendos: te llegan {euros} euros por tus {n} acciones."),
                         tr("Dividendos de {empresa}: {euros} euros por tus {n} acciones, ingresados en el banco.")],
}, cero=("noticia_prob", "dividendo_dias", "aviso_diario", "vuelta_al_precio"))

_SERIE = [
    {"id": "naviera", "nombre": tr("Naviera Poniente"), "base": 40, "volatilidad": 7, "dividendo": 2, "desc": tr("Barcos y mercancías. Estable y aburrida, pero reparte dividendos."),
     "sube": [tr("La Naviera Poniente cierra un contrato con un puerto del norte."), tr("Récord de mercancías en el puerto: la Naviera Poniente sube.")],
     "baja": [tr("Un temporal deja amarrados los barcos de la Naviera Poniente."), tr("La Naviera Poniente pierde a su mejor cliente.")]},
    {"id": "minas", "nombre": tr("Minas de Monteferro"), "base": 60, "volatilidad": 7, "dividendo": 1, "desc": tr("Sube y baja con la huelga minera."),
     "sube": [tr("Encuentran una veta nueva en Monteferro."), tr("Las Minas de Monteferro firman la paz con los mineros.")],
     "baja": [tr("Huelga en las Minas de Monteferro."), tr("Un derrumbe cierra una galería de Monteferro.")]},
    {"id": "belmonte", "nombre": tr("Grupo Belmonte"), "base": 120, "volatilidad": 7, "dividendo": 1, "desc": tr("El imperio de Octavio Belmonte. Cara mientras él mande."),
     "sube": [tr("El Grupo Belmonte compra otro hotel en la costa."), tr("Octavio Belmonte anuncia un puerto deportivo nuevo.")],
     "baja": [tr("Rumores de investigación sobre las cuentas del Grupo Belmonte."), tr("Un socio del Grupo Belmonte se va dando un portazo.")]},
    {"id": "conservas", "nombre": tr("Conservas Cala Brava"), "base": 15, "volatilidad": 22, "dividendo": 0, "desc": tr("Pequeña y muy volátil: puede doblar o hundirse en una semana. No reparte dividendos."),
     "sube": [tr("Las Conservas Cala Brava llegan a los supermercados de la capital."), tr("Una cadena de restaurantes se queda toda la producción de Conservas Cala Brava.")],
     "baja": [tr("Retiran un lote de Conservas Cala Brava por un problema en las latas."), tr("La sardina escasea y Conservas Cala Brava para la fábrica.")]},
    {"id": "lucero", "nombre": tr("Lucero Tecnología"), "base": 85, "volatilidad": 9, "dividendo": 0, "desc": tr("La empresa de moda de San Lucero. No reparte dividendos: lo reinvierte todo."),
     "sube": [tr("Lucero Tecnología presenta un invento que todo el mundo quiere."), tr("Una gran empresa extranjera invierte en Lucero Tecnología.")],
     "baja": [tr("Lucero Tecnología retrasa su producto estrella."), tr("Se va el fundador de Lucero Tecnología.")]},
]
EMPRESAS = {e["id"]: dict(e) for e in _SERIE}


def configurar(datos):
    lista = [e for e in datos.get("bolsa_empresas", []) if isinstance(e, dict) and e.get("id") and e.get("nombre")]
    EMPRESAS.clear()
    for e in (lista or _SERIE):
        try:
            EMPRESAS[str(e["id"])] = {"id": str(e["id"]), "nombre": str(e["nombre"]), "base": max(1.0, float(e.get("base", 50))),
                                      "volatilidad": max(0.0, float(e.get("volatilidad", 7))), "dividendo": max(0.0, float(e.get("dividendo", 0))),
                                      "desc": str(e.get("desc", "")), "sube": [str(x) for x in e.get("sube") or []], "baja": [str(x) for x in e.get("baja") or []]}
        except (TypeError, ValueError):
            continue
    if not EMPRESAS:
        EMPRESAS.update({e["id"]: dict(e) for e in _SERIE})


def _euros(n):
    return f"{int(round(n))}"


class Bolsa:
    """Mixin de Partida."""

    def precio_accion(self, ident):
        e = EMPRESAS.get(ident)
        return float(self.j.bolsa.get(ident, e["base"] if e else 1.0))

    def precio_ayer(self, ident):
        return float((getattr(self.j, "bolsa_ayer", None) or {}).get(ident, self.precio_accion(ident)))

    def cartera_valor(self, precios=None):
        return sum(n * (precios or {}).get(i, self.precio_accion(i)) for i, n in self.j.acciones.items() if n and i in EMPRESAS)

    def cartera_coste(self):
        j = self.j
        for i, n in j.acciones.items():                          # de una partida anterior no se sabe: cuenta lo que valen hoy
            if n and i not in j.coste_acciones:
                j.coste_acciones[i] = n * self.precio_accion(i)
        return sum(float(v) for i, v in j.coste_acciones.items() if j.acciones.get(i))

    def balance_txt(self, ganado):
        if abs(ganado) < 1:
            return tr("ni ganas ni pierdes")
        return tr('ganas {_euros} euros').format(_euros=(_euros(ganado))) if ganado > 0 else tr('pierdes {_euros} euros').format(_euros=(_euros(-ganado)))

    def comprar_acciones(self, ident, n):
        precio = int(round(self.precio_accion(ident) * n))
        if not self.pagar(precio):
            return False
        j = self.j
        j.acciones[ident] = j.acciones.get(ident, 0) + n
        j.coste_acciones[ident] = float(j.coste_acciones.get(ident, 0.0)) + precio
        return precio

    def vender_acciones(self, ident, n=None):
        j = self.j
        tengo = j.acciones.get(ident, 0)
        k = tengo if n is None else min(n, tengo)
        if k <= 0:
            return 0, 0
        cobro = int(self.precio_accion(ident) * k)
        coste = float(j.coste_acciones.get(ident, 0.0))
        parte = coste * k / tengo if tengo else 0.0
        j.coste_acciones[ident] = max(0.0, coste - parte)
        j.acciones[ident] = tengo - k
        self.dar_dinero(cobro)
        return k, cobro - parte

    def mover_bolsa(self):
        """Cada medianoche: los precios se mueven, alguna empresa tiene noticias, reparten dividendos y te cuenta cómo va lo tuyo."""
        j = self.j
        valor_ayer = self.cartera_valor()
        j.bolsa_ayer = {i: self.precio_accion(i) for i in EMPRESAS}
        avisos = []
        for ident, e in EMPRESAS.items():
            p = self.precio_accion(ident)
            vol = e["volatilidad"] / 100.0
            p *= 1 + random.uniform(-vol, vol) + (e["base"] - p) / e["base"] * AJ("vuelta_al_precio") / 100.0
            if random.random() * 100 < AJ("noticia_prob") and (e["sube"] or e["baja"]):
                sube = random.random() < 0.5 if (e["sube"] and e["baja"]) else bool(e["sube"])
                salto = random.uniform(AJ("noticia_min"), max(AJ("noticia_min"), AJ("noticia_max"))) / 100.0
                p *= (1 + salto) if sube else (1 - salto)
                texto = random.choice(e["sube"] if sube else e["baja"])
                j.bolsa_noticias = ([{"dia": self.dia, "id": ident, "texto": texto, "sube": sube}] + list(getattr(j, "bolsa_noticias", None) or []))[:8]
                if j.acciones.get(ident):
                    avisos.append(tr('{texto} {v} un {int} por ciento.').format(texto=(texto), v=(tr('Sube') if sube else tr('Baja')), int=(int(salto * 100))))
            # la historia sigue moviendo algunas, como siempre
            if ident == "belmonte":
                if "m20" in self.completadas:
                    p = min(p, random.uniform(3, 8))
                elif "m15" in self.completadas:
                    p = min(p, 70)
            if ident == "minas" and "t06" in self.completadas:
                p = max(p, 90 * random.uniform(0.95, 1.1))
            j.bolsa[ident] = round(max(1.0, p), 2)
        # dividendos
        dias = AJ.entero("dividendo_dias")
        if dias and self.dia % dias == 0:
            for ident, n in list(j.acciones.items()):
                e = EMPRESAS.get(ident)
                if not n or e is None or e["dividendo"] <= 0:
                    continue
                euros = int(n * self.precio_accion(ident) * e["dividendo"] / 100.0)
                if euros > 0:
                    j.banco += euros
                    j.stats["dividendos"] = j.stats.get("dividendos", 0) + euros
                    avisos.append(AJ.frase("frases_dividendo", empresa=e["nombre"], euros=euros, n=n))
        if any(j.acciones.values()):
            for t in avisos:
                self.decir(t)
            if AJ.entero("aviso_diario"):
                valor = self.cartera_valor()
                d = valor - valor_ayer
                cambio = tr("lo mismo") if abs(d) < 1 else (tr('{_euros} euros más').format(_euros=(_euros(d))) if d > 0 else tr('{_euros} euros menos').format(_euros=(_euros(-d))))
                self.decir(AJ.frase("frases_informe", valor=_euros(valor), cambio=cambio, balance=self.balance_txt(valor - self.cartera_coste())))


def como_funciona():
    return (tr('En la bolsa compras acciones de las empresas de la comarca. Ganas si las vendes más caras de lo que te costaron, y pierdes si las vendes más baratas. Los precios se mueven cada medianoche: unas empresas poco, otras mucho, y de vez en cuando una noticia las hace dar un salto. Algunas reparten dividendos cada {entero} días: un tanto por ciento de lo que vale cada acción, que te llega al banco sin vender nada. Lo que pasa en la historia también las mueve. Mientras tengas acciones, cada medianoche el juego te dice cuánto valen y cuánto ganas o pierdes.').format(entero=(AJ.entero('dividendo_dias'))))
