"""Comprar paseando por la tienda, despensa y nevera en casa, y cocinar (1.7.1).

Tres cosas que van juntas:

- La tienda se recorre por dentro, pasillo a pasillo. Cada pasillo tiene su clase de producto; lo que coges va a una
  cesta y se paga en la caja. El menú rápido de la tienda vende lo mismo, de uno en uno y pagando al momento.
- Lo comprado lo llevas encima, en la bolsa, hasta que lo guardas en la cocina de una casa tuya: lo fresco va a la
  nevera y lo demás a la despensa, cada casa la suya, con sitio limitado. Lo fresco caduca a los días del juego: lo
  caducado se tira solo al abrir, avisando. Lo que se come sin cocinar puede comerse en la calle, desde el móvil.
- En la cocina se preparan recetas con lo que hay en casa y lo que traes. Dan varias raciones: te comes una y el resto
  va a la nevera. A veces un plato sale especialmente bien o se quema un poco; con la práctica, mejor.

Todo está en los datos (vida.json: pasillos, productos, tipos_tienda, recetas y cocina) y un mod puede cambiarlo.
Depende solo del jugador, así que en un servidor en línea funciona igual.
"""
import random

import pygame

from . import sistemas
from .ajustes import Ajustes
from .menus import Menu, Opcion

AJ = Ajustes("cocina", {"capacidad_despensa": 30, "capacidad_nevera": 14, "nevera_grande": 10, "capacidad_encima": 20, "falta_prob": 10, "oferta_descuento": 25,
                        "prob_especial": 12, "prob_quemado": 14, "practica_plato": 5, "practica_especial": 15, "practica_quemado": 75, "bono_especial": 30,
                        "merma_quemado": 40, "equipada_salud": 100, "equipada_quemado": 50, "animo_especial": 4, "animo_quemado": 3,
                        "robo_visto": 50, "robo_visto_cosa": 4, "robo_puntos": 2, "robo_recuerdo": 2, "pareja_afinidad": 2, "aviso_caduca": 1},
             {"frases_caja": ["Son {total}. Aquí tiene su compra. Hasta otra.", "{total}, justos. ¿Le hace falta bolsa? Buen día.",
                              "A ver... {total}. Gracias, y que aproveche.", "Pues {total}. Vuelva cuando quiera."],
              "frases_no_llega": ["El tendero repasa la cuenta: son {total} y llevas {dinero}. Te faltan {falta}. Devuelve algo de la cesta.",
                                  "No te llega: la cesta sube a {total} y tienes {dinero}. Quita algo, que te faltan {falta}."],
              "frases_dejar": ["Dejas la cesta junto a la puerta, con todo dentro.", "Devuelves la cesta a su montón sin comprar nada.",
                               "Lo piensas mejor y dejas la cesta en el suelo, llena."],
              "frases_robo_limpio": ["Te metes la compra bajo la ropa y sales silbando. Nadie se ha fijado.", "Aprovechas que el tendero atiende el teléfono y sales con todo. No te ha visto.",
                                     "Sales despacio, como quien no ha encontrado lo que buscaba. Cuela."],
              "frases_robo_visto": ["¡Eh, que eso no lo has pagado! El tendero sale detrás de ti gritando y alguien llama a la policía.",
                                    "Suena el pitido de la puerta. ¡Al ladrón! Sales corriendo con la compra, y aquí ya te conocen.",
                                    "El tendero te ha visto por el espejo del techo. ¡Policía! Sales por piernas con todo."],
              "frases_normal": ["Te ha quedado bien.", "Huele a comida de casa.", "Sale como tenía que salir.", "Nada del otro mundo, pero está bueno."],
              "frases_especial": ["Te ha salido de categoría: mejor que en un restaurante.", "Hoy tenías la mano fina: está para chuparse los dedos.",
                                  "Te ha quedado redondo. Esto no se olvida.", "En su punto exacto. Te sientes orgullos[o|a]."],
              "frases_quemado": ["Se te ha pegado un poco al fondo. Se puede comer, pero no es lo mismo.", "Te has despistado y se ha quemado por un lado. Alimenta menos.",
                                 "Huele a chamusquina: se te ha pasado. Lo salvas como puedes."],
              "frases_pareja": ["{n} prueba un poco: «Oye, pues te ha quedado muy bien».", "Pones dos platos. {n} repite.", "{n} se sienta contigo a la mesa y no deja ni las migas.",
                                "«¿Has cocinado tú?», dice {n}, y te da un beso."],
              "frases_caducado": ["Tiras a la basura {cosas}: se ha echado a perder.", "{cosas}: caducado. Va a la basura.", "Huele raro: tiras {cosas}."]},
             cero=("nevera_grande", "falta_prob", "oferta_descuento", "prob_especial", "prob_quemado", "practica_plato", "practica_especial", "practica_quemado", "bono_especial",
                   "merma_quemado", "equipada_salud", "equipada_quemado", "animo_especial", "animo_quemado", "robo_visto", "robo_visto_cosa", "robo_puntos", "robo_recuerdo",
                   "pareja_afinidad", "aviso_caduca"))

# ------------------------------------------------------------------ lo de serie (lo mismo que traen los datos)
PASILLOS = [
    {"id": "fruteria", "nombre": "la frutería", "desc": "Cajas de fruta y de verdura. Huele a tierra mojada y a naranja."},
    {"id": "carniceria", "nombre": "la carnicería", "desc": "Un mostrador frío con bandejas. De fondo, la cortadora de fiambre."},
    {"id": "pescaderia", "nombre": "la pescadería", "desc": "Hielo picado y olor a mar."},
    {"id": "lacteos", "nombre": "los lácteos y los huevos", "desc": "Una nevera larga que zumba, con la puerta de cristal."},
    {"id": "panaderia", "nombre": "la panadería", "desc": "Cestos de pan. Todavía está caliente."},
    {"id": "despensa", "nombre": "las conservas y la despensa", "desc": "Latas, pasta, arroz y legumbres en estantes hasta el techo."},
    {"id": "bebidas", "nombre": "las bebidas", "desc": "Botellas y latas. Las de abajo, en una nevera."},
    {"id": "preparados", "nombre": "lo listo para comer", "desc": "Sándwiches, ensaladas envasadas y cosas de picar, para comer sin cocinar."},
]


def _pr(ident, nombre, pasillo, precio, caduca=0, sitio="despensa", hambre=0, sed=0, salud=0, animo=0, bebida=False, desc=""):
    d = {"id": ident, "nombre": nombre, "pasillo": pasillo, "precio": precio, "sitio": sitio}
    for k, v in (("caduca", caduca), ("hambre", hambre), ("sed", sed), ("salud", salud), ("animo", animo)):
        if v:
            d[k] = v
    if bebida:
        d["bebida"] = True
    if desc:
        d["desc"] = desc
    return d


PRODUCTOS = [
    _pr("tomates", "Tomates, un kilo", "fruteria", 2, 5, "nevera"),
    _pr("patatas", "Patatas, una malla", "fruteria", 2, 12),
    _pr("cebollas", "Cebollas, una ristra", "fruteria", 1, 14),
    _pr("pimientos", "Pimientos", "fruteria", 2, 6, "nevera"),
    _pr("ajos", "Ajos, una cabeza", "fruteria", 1, 20),
    _pr("lechuga", "Lechuga", "fruteria", 1, 4, "nevera"),
    _pr("limones", "Limones", "fruteria", 1, 10, "nevera"),
    _pr("manzanas", "Manzanas", "fruteria", 2, 8, "despensa", hambre=14, sed=8, salud=5, desc="Se comen tal cual, en casa o por la calle."),
    _pr("platanos", "Plátanos", "fruteria", 2, 5, "despensa", hambre=18, salud=5, desc="Se comen tal cual, en casa o por la calle."),
    _pr("pollo", "Pollo troceado", "carniceria", 5, 3, "nevera"),
    _pr("carne_picada", "Carne picada", "carniceria", 4, 3, "nevera"),
    _pr("chorizo", "Chorizo", "carniceria", 3, 15, "nevera"),
    _pr("merluza", "Merluza en rodajas", "pescaderia", 6, 2, "nevera"),
    _pr("gambas", "Gambas", "pescaderia", 7, 2, "nevera"),
    _pr("mejillones", "Mejillones", "pescaderia", 4, 2, "nevera"),
    _pr("huevos", "Huevos, media docena", "lacteos", 2, 10, "nevera"),
    _pr("leche", "Leche, un litro", "lacteos", 1, 6, "nevera", hambre=8, sed=35, salud=3, bebida=True, desc="Se bebe tal cual."),
    _pr("queso", "Queso, una cuña", "lacteos", 3, 12, "nevera", hambre=18, salud=4, desc="Se come tal cual, y entra en alguna receta."),
    _pr("yogur", "Yogures", "lacteos", 1, 8, "nevera", hambre=12, sed=5, salud=4, desc="Se comen tal cual."),
    _pr("pan", "Barra de pan", "panaderia", 1, 2, "despensa", hambre=15, desc="Se come tal cual, y entra en alguna receta. Mañana estará duro."),
    _pr("arroz", "Arroz, un paquete", "despensa", 1),
    _pr("macarrones", "Macarrones, un paquete", "despensa", 1),
    _pr("garbanzos", "Garbanzos, un bote", "despensa", 2),
    _pr("lentejas", "Lentejas, un paquete", "despensa", 2),
    _pr("tomate_frito", "Tomate frito, un bote", "despensa", 1),
    _pr("atun", "Atún, tres latas", "despensa", 2, hambre=18, salud=5, desc="Se come tal cual, y entra en alguna receta. No caduca."),
    _pr("caldo", "Caldo, un brik", "despensa", 2),
    _pr("agua_botella", "Botella de agua", "bebidas", 1, sed=70, bebida=True, desc="Para llevar encima y beber cuando haga falta."),
    _pr("refresco_lata", "Refresco de naranja", "bebidas", 2, sed=50, hambre=4, animo=1, bebida=True, desc="Quita la sed y anima un poco."),
    _pr("zumo", "Zumo, un brik", "bebidas", 2, 10, "nevera", sed=45, hambre=6, salud=4, bebida=True, desc="Quita la sed y da algo de salud."),
    _pr("sandwich", "Sándwich envasado", "preparados", 3, 3, "nevera", hambre=28, salud=6, desc="Para comer sin cocinar, en casa o por la calle."),
    _pr("ensalada_envasada", "Ensalada envasada", "preparados", 4, 2, "nevera", hambre=24, sed=10, salud=8, desc="Para comer sin cocinar, en casa o por la calle."),
    _pr("patatas_fritas", "Bolsa de patatas fritas", "preparados", 2, hambre=14, animo=1, desc="Para picar. Llena poco."),
    _pr("chocolatina", "Chocolatina", "preparados", 1, hambre=10, animo=2, desc="Un capricho: llena poco y anima."),
]

TIPOS_TIENDA = [
    {"id": "supermercado", "nombre": "Supermercado", "pasillos": ["fruteria", "carniceria", "pescaderia", "lacteos", "panaderia", "despensa", "bebidas", "preparados"],
     "palabras": ["súper", "super", "hipermercado"], "recargo": 100},
    {"id": "mercado", "nombre": "Mercado de abastos", "pasillos": ["fruteria", "carniceria", "pescaderia", "lacteos", "panaderia"], "palabras": ["mercado"], "recargo": 90},
    {"id": "gasolinera", "nombre": "Tienda de gasolinera", "pasillos": ["bebidas", "preparados"], "palabras": ["gasolinera"], "recargo": 130},
    {"id": "bazar", "nombre": "Bazar", "pasillos": ["bebidas", "preparados"], "palabras": ["bazar"], "recargo": 115},
    {"id": "sin_comida", "nombre": "Tienda que no vende comida para casa", "pasillos": [], "palabras": ["ferretería", "efectos navales"], "recargo": 100},
    {"id": "ultramarinos", "nombre": "Ultramarinos o tienda de barrio", "pasillos": ["fruteria", "lacteos", "panaderia", "despensa", "bebidas", "preparados"],
     "palabras": ["ultramarinos", "colmado", "economato"], "resto": True, "recargo": 110},
]


def _re(ident, nombre, ingredientes, minutos, raciones, hambre, sed, salud, animo, caduca, fuego, desc=""):
    d = {"id": ident, "nombre": nombre, "ingredientes": ingredientes, "minutos": minutos, "raciones": raciones, "hambre": hambre, "sed": sed, "salud": salud,
         "animo": animo, "caduca": caduca, "fuego": fuego}
    if desc:
        d["desc"] = desc
    return d


RECETAS = [
    _re("bocadillo_atun", "Bocadillo de atún con tomate", ["pan", "atun", "tomates"], 5, 2, 45, 5, 14, 1, 1, "no", "Lo más rápido que hay. No lleva fuego, así que no se quema."),
    _re("ensalada_mixta", "Ensalada mixta", ["lechuga", "tomates", "cebollas", "atun"], 10, 2, 45, 20, 22, 2, 2, "no", "Fresca y ligera. No lleva fuego, así que no se quema."),
    _re("huevos_patatas", "Huevos fritos con patatas", ["huevos", "patatas"], 15, 2, 62, 0, 20, 3, 1, "freir", "Dos ingredientes y una sartén."),
    _re("merluza_plancha", "Merluza a la plancha con limón", ["merluza", "limones", "ajos"], 15, 2, 65, 5, 40, 3, 1, "freir", "Poco tiempo y mucha salud. El pescado no espera: cocínalo pronto."),
    _re("macarrones", "Macarrones con chorizo", ["macarrones", "tomate_frito", "chorizo"], 20, 3, 75, 5, 28, 2, 3, "hervir", "Cunde mucho y aguanta bien en la nevera."),
    _re("hamburguesas", "Hamburguesas caseras", ["carne_picada", "pan", "cebollas", "queso"], 20, 3, 80, 0, 30, 5, 2, "freir", "Las de casa, con su queso fundido."),
    _re("tortilla", "Tortilla de patatas", ["huevos", "patatas", "cebollas"], 30, 4, 70, 5, 30, 3, 3, "freir", "Con cebolla. Cuatro raciones, y fría está igual de buena."),
    _re("arroz_pollo", "Arroz con pollo", ["arroz", "pollo", "pimientos", "tomates"], 40, 4, 85, 10, 38, 4, 3, "hervir", "Un plato completo para varios días."),
    _re("paella", "Paella marinera", ["arroz", "gambas", "mejillones", "pimientos", "tomates"], 50, 5, 95, 10, 45, 6, 2, "hervir",
        "El plato de los domingos. Lleva marisco fresco, que hay que comprar en un mercado o en un supermercado."),
    _re("potaje", "Potaje de garbanzos", ["garbanzos", "caldo", "patatas", "ajos"], 55, 4, 88, 15, 36, 3, 4, "hervir", "Todo sale de la despensa: nada de esto caduca pronto."),
    _re("lentejas", "Lentejas con chorizo", ["lentejas", "chorizo", "patatas", "cebollas"], 60, 5, 90, 15, 40, 4, 4, "hervir", "Una hora de olla, cinco raciones y cuatro días de nevera."),
]

FUEGOS = {"no": ("sin fuego", None), "freir": ("a la sartén", "cocina_freir"), "hervir": ("a la olla", "cocina_hervir")}


def _lista(p, clave, serie):
    lista = [x for x in p.datos.get(clave, []) if isinstance(x, dict) and x.get("id")]
    return lista or serie


def pasillos(p):
    return _lista(p, "pasillos", PASILLOS)


def productos(p):
    return [x for x in _lista(p, "productos", PRODUCTOS) if x.get("nombre")]


def tipos_tienda(p):
    return _lista(p, "tipos_tienda", TIPOS_TIENDA)


def recetas(p):
    return [x for x in _lista(p, "recetas", RECETAS) if x.get("nombre") and x.get("ingredientes")]


def _num(d, k, serie=0.0):
    try:
        return float(d.get(k, serie) or 0)
    except (TypeError, ValueError):
        return float(serie)


def comestible(prod):
    return any(_num(prod, k) > 0 for k in ("hambre", "sed", "salud", "animo"))


def _cuantos(n, uno, varios):
    return f"{n} {uno if n == 1 else varios}"


def _euros(n):
    return f"{int(n)} {'euro' if int(n) == 1 else 'euros'}"


def _junta(nombres):
    nombres = list(nombres)
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1] if nombres else "nada"


def efecto_txt(d, realista=True):
    """Lo que hace comerse algo, dicho con palabras."""
    partes = []
    h, s = _num(d, "hambre"), _num(d, "sed")
    if h:
        partes.append("quita un poco el hambre" if h < 25 else "quita el hambre" if h < 60 else "quita mucha hambre" if h < 85 else "te deja sin hambre")
    if s:
        partes.append("quita algo de sed" if s < 30 else "quita la sed")
    if _num(d, "salud"):
        partes.append(f"da {int(_num(d, 'salud'))} de salud")
    if _num(d, "animo") > 0:
        partes.append("sube el ánimo")
    elif _num(d, "animo") < 0:
        partes.append("baja el ánimo")
    return _junta(partes) if partes else "sin efecto"


def nivel_cocina(p):
    return min(10, int(float(getattr(p.j, "cocina_practica", 0.0) or 0.0) / 10.0))


class Compra:
    """Mixin de Partida."""

    # ================================================================== productos y tiendas
    def producto(self, ident):
        return next((x for x in productos(self) if x["id"] == ident), None)

    def tipo_tienda(self, l):
        """La clase de tienda que es un lugar (qué pasillos tiene y cómo de cara es), o None si allí no se vende comida para casa."""
        if l is None or l.tipo != "tienda":
            return None
        tipos = tipos_tienda(self)
        nombre = l.nombre.lower()
        t = next((x for x in tipos if x["id"] == l.get("surtido")), None) if l.get("surtido") else None
        t = t or next((x for x in tipos if l.id in (x.get("lugares") or [])), None)
        t = t or next((x for x in tipos if any(str(w).lower() in nombre for w in (x.get("palabras") or []) if str(w).strip())), None)
        t = t or next((x for x in tipos if x.get("resto")), None)
        return t if t and self.surtido(l, t) else None

    def surtido(self, l, tipo=None):
        """Los pasillos de una tienda, cada uno con sus productos: [(pasillo, [productos])]. Sin pasillos con género, lista vacía."""
        tipo = tipo or self.tipo_tienda(l)
        if not tipo:
            return []
        todos = productos(self)
        por_id = {x["id"]: x for x in pasillos(self)}
        out = []
        for pid in tipo.get("pasillos") or []:
            pa = por_id.get(pid)
            genero = [x for x in todos if x.get("pasillo") == pid]
            if pa and genero:
                out.append((pa, genero))
        return out

    def oferta_de(self, l):
        """El producto que esa tienda tiene hoy de oferta (su identificador), o None. Cambia cada día y en cada tienda."""
        if AJ("oferta_descuento") <= 0:
            return None
        genero = [x["id"] for _, lista in self.surtido(l) for x in lista]
        return random.Random(f"{self.j.semilla}-{self.dia}-oferta-{l.id}").choice(genero) if genero else None

    def agotado(self, l, prod):
        """Hoy no queda de eso en esa tienda. Cambia cada día y en cada tienda; lo que está de oferta no se agota."""
        if prod["id"] == self.oferta_de(l):
            return False
        return random.Random(f"{self.j.semilla}-{self.dia}-falta-{l.id}-{prod['id']}").random() * 100 < AJ("falta_prob")

    def precio_producto(self, l, prod):
        tipo = self.tipo_tienda(l) or {}
        f = self.mercado("comida", l.id) * (_num(tipo, "recargo", 100) or 100) / 100.0
        if prod["id"] == self.oferta_de(l):
            f *= 1.0 - AJ("oferta_descuento") / 100.0
        return max(1, int(round(_num(prod, "precio", 1) * f)))

    def donde_va(self, prod):
        return "nevera" if prod.get("sitio") == "nevera" else "despensa"

    def producto_ayuda(self, prod):
        """Lo que dice F1 sobre un producto: para qué sirve, dónde se guarda y cuánto aguanta."""
        partes = [prod.get("desc") or ""]
        usan = [r["nombre"].lower() for r in recetas(self) if prod["id"] in r["ingredientes"]]
        if comestible(prod):
            partes.append(f"{'Se bebe' if prod.get('bebida') else 'Se come'} sin cocinar: {efecto_txt(prod)}.")
        partes.append(f"Entra en: {_junta(usan)}." if usan else "No entra en ninguna receta.")
        dias = int(_num(prod, "caduca"))
        partes.append(f"En casa va a la {self.donde_va(prod)}." + (f" Caduca a los {_cuantos(dias, 'día', 'días')}." if dias else " No caduca."))
        return " ".join(x for x in partes if x)

    # ================================================================== lo que llevas encima
    def _lote_de(self, prod, n=1):
        dias = int(_num(prod, "caduca"))
        return {"id": prod["id"], "n": int(n), "cad": self.dia + dias if dias else 0}

    @staticmethod
    def _meter(lotes, lote):
        """Añade un lote a una lista, juntándolo con otro igual que caduque el mismo día."""
        claves = ("id", "plato", "cad", "nombre", "hambre", "sed", "salud", "animo")
        for x in lotes:
            if all(x.get(k) == lote.get(k) for k in claves):
                x["n"] = int(x.get("n", 0)) + int(lote["n"])
                return x
        lotes.append(dict(lote))
        return lotes[-1]

    @staticmethod
    def _total(lotes):
        return sum(int(x.get("n", 0)) for x in lotes)

    def lote_info(self, lote):
        """Lo que es un lote, de la despensa o de lo que llevas: nombre, dónde se guarda, si se come y lo que hace. None si ya no existe."""
        if lote.get("plato"):
            return {"nombre": lote.get("nombre") or "Un plato cocinado", "sitio": "nevera", "comestible": True, "bebida": False, "plato": True, "unidad": ("ración", "raciones"),
                    "hambre": _num(lote, "hambre"), "sed": _num(lote, "sed"), "salud": _num(lote, "salud"), "animo": _num(lote, "animo")}
        prod = self.producto(lote.get("id"))
        if prod is None:
            return None
        return {"nombre": prod["nombre"], "sitio": self.donde_va(prod), "comestible": comestible(prod), "bebida": bool(prod.get("bebida")), "plato": False, "unidad": ("unidad", "unidades"),
                "hambre": _num(prod, "hambre"), "sed": _num(prod, "sed"), "salud": _num(prod, "salud"), "animo": _num(prod, "animo")}

    def cad_txt(self, lote):
        cad = int(lote.get("cad") or 0)
        if not cad:
            return "no caduca"
        d = cad - self.dia
        return "caducado" if d < 0 else "caduca hoy" if d == 0 else "caduca mañana" if d == 1 else f"caduca en {d} días"

    def lote_txt(self, lote):
        info = self.lote_info(lote)
        n = int(lote.get("n", 0))
        return f"{info['nombre']}, {_cuantos(n, *info['unidad'])}, {self.cad_txt(lote)}"

    def _sanear(self, lotes):
        """Quita lo que ya no existe (un producto de un mod que no está) y lo que se ha quedado a cero."""
        lotes[:] = [x for x in lotes if isinstance(x, dict) and int(x.get("n", 0) or 0) > 0 and self.lote_info(x) is not None]
        return lotes

    def tirar_caducado(self, lotes):
        """Tira lo que ha caducado. Devuelve los nombres de lo tirado."""
        self._sanear(lotes)
        malos = [x for x in lotes if int(x.get("cad") or 0) and self.dia > int(x["cad"])]
        nombres = [self.lote_info(x)["nombre"].lower() for x in malos]
        lotes[:] = [x for x in lotes if x not in malos]
        if malos:
            self.j.stats["comida_tirada"] = self.j.stats.get("comida_tirada", 0) + sum(int(x["n"]) for x in malos)
        return nombres

    def pronto_caduca(self, lotes):
        """Los nombres de lo que caduca hoy o en los días de aviso que digan los datos."""
        margen = AJ.entero("aviso_caduca")
        return [self.lote_info(x)["nombre"].lower() + (" hoy" if int(x["cad"]) == self.dia else " mañana" if int(x["cad"]) == self.dia + 1 else f" en {int(x['cad']) - self.dia} días")
                for x in lotes if int(x.get("cad") or 0) and 0 <= int(x["cad"]) - self.dia <= margen]

    def aviso_caducidad(self, lotes):
        """Tira lo caducado y avisa de lo que está a punto. Devuelve la frase, o cadena vacía."""
        tirado = self.tirar_caducado(lotes)
        pronto = self.pronto_caduca(lotes)
        return " ".join(x for x in (AJ.frase("frases_caducado", cosas=_junta(tirado)) if tirado else "", f"Ojo: caduca {_junta(pronto)}" if pronto else "") if x)

    def encima(self):
        return self._sanear(self.j.encima)

    def encima_cabe(self):
        return max(0, AJ.entero("capacidad_encima") - self._total(self.encima()))

    def encima_txt(self):
        lotes = self.encima()
        if not lotes:
            return "No llevas comida ni compra encima."
        return f"Llevas encima {_cuantos(self._total(lotes), 'cosa', 'cosas')} de comida, de {AJ.entero('capacidad_encima')} que puedes cargar: " + "; ".join(self.lote_txt(x) for x in lotes) + "."

    def compra_total(self, l, cosas):
        return sum(self.precio_producto(l, self.producto(pid)) * n for pid, n in cosas.items() if self.producto(pid) is not None)

    def comprar_productos(self, l, cosas):
        """Paga unos productos ({identificador: cantidad}) y te los llevas encima. Devuelve True si se ha comprado."""
        cosas = {pid: int(n) for pid, n in cosas.items() if int(n) > 0 and self.producto(pid) is not None}
        if not cosas:
            return False
        n = sum(cosas.values())
        if n > self.encima_cabe():
            self.app.son("error")
            self.decir(f"No puedes cargar con tanto: llevas {self._total(self.encima())} cosas y caben {AJ.entero('capacidad_encima')}. Guarda antes la compra en la cocina de una casa tuya.", True)
            return False
        total = self.compra_total(l, cosas)
        if self.j.dinero < total:
            self.app.son("error")
            self.decir(AJ.frase("frases_no_llega", total=_euros(total), dinero=_euros(self.j.dinero), falta=_euros(total - self.j.dinero)), True)
            return False
        self.pagar(total)
        for pid, k in cosas.items():
            self._meter(self.j.encima, self._lote_de(self.producto(pid), k))
        self.j.stats["compras"] = self.j.stats.get("compras", 0) + 1
        self.j.stats["gastado_comida"] = self.j.stats.get("gastado_comida", 0) + total
        return True

    def robar_productos(self, l, cosas, rng=random):
        """Sales de la tienda con la cesta sin pasar por caja. Te lo llevas todo; si te ven, es un hurto: cae búsqueda,
        baja tu prestigio y la tienda te recuerda unos días. Devuelve (te_han_visto, frase)."""
        cosas = {pid: int(n) for pid, n in cosas.items() if int(n) > 0 and self.producto(pid) is not None}
        n = sum(cosas.values())
        quedan = self.encima_cabe()
        for pid, k in cosas.items():                             # lo que no puedes cargar se queda en la tienda
            k = min(k, quedan)
            quedan -= k
            if k:
                self._meter(self.j.encima, self._lote_de(self.producto(pid), k))
        visto = rng.random() * 100 < AJ("robo_visto") + AJ("robo_visto_cosa") * max(0, n - 1)
        self.j.stats["hurtos"] = self.j.stats.get("hurtos", 0) + 1
        if not visto:
            return False, AJ.frase("frases_robo_limpio", rng)
        if AJ("robo_recuerdo") >= 1:
            self.j.locales_vetados[l.id] = {"hasta": self.dia + AJ.entero("robo_recuerdo"), "modo": "cerrado"}
        self.son("grito", vol=0.5)
        if AJ("robo_puntos") > 0:
            self.delito(AJ("robo_puntos"), "hurto en una tienda", siempre=True)
        return True, AJ.frase("frases_robo_visto", rng)

    def _sin_ganas(self, info):
        """Por qué no te lo comes ahora, o cadena vacía."""
        j = self.j
        lleno = j.salud >= j.salud_max
        if self.vida_realista():
            if info["bebida"]:
                return "Ahora no tienes sed." if j.sed < 15 and lleno else ""
            return "Ahora no tienes hambre." if j.hambre < 15 and (j.sed < 15 or not info["sed"]) and lleno else ""
        return "No te hace falta: tu salud está al máximo." if lleno and info["animo"] <= 0 else ""

    def comer_lote(self, lotes, lote):
        """Te comes o te bebes una unidad de un lote. Devuelve la frase, o None si no se puede (y lo dice)."""
        info = self.lote_info(lote)
        j = self.j
        if info is None or lote not in lotes:
            return None
        motivo = "Eso es para cocinar: tal cual no se come." if not info["comestible"] else "Está caducado: mejor tirarlo." if int(lote.get("cad") or 0) and self.dia > int(lote["cad"]) \
            else self._sin_ganas(info)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return None
        lote["n"] = int(lote["n"]) - 1
        if lote["n"] <= 0:
            lotes.remove(lote)
        if info["hambre"]:
            self.ha_comido(info["hambre"])
        if info["sed"]:
            self.ha_bebido(info["sed"])
        j.salud = min(j.salud_max, j.salud + info["salud"])
        if info["animo"]:
            self.cambiar_animo(info["animo"])
        self.mez.sonar("beber" if info["bebida"] else "comer", cat="interfaz")
        j.stats["comidas_caseras" if info["plato"] else "tentempies"] = j.stats.get("comidas_caseras" if info["plato"] else "tentempies", 0) + 1
        return f"{'Te bebes' if info['bebida'] else 'Te comes'} {info['nombre'].lower()}. Salud {int(j.salud)}.{self.necesidades_txt()}"

    # ================================================================== la despensa y la nevera de cada casa
    def despensa(self, casa):
        """Lo que hay guardado en una casa tuya: la lista de lotes de su nevera y su despensa juntas."""
        return self._sanear(self.j.despensa.setdefault(casa.id, []))

    def de_sitio(self, casa, sitio):
        return [x for x in self.despensa(casa) if self.lote_info(x)["sitio"] == sitio]

    def sitio_capacidad(self, casa, sitio):
        if sitio == "nevera":
            return AJ.entero("capacidad_nevera") + (AJ.entero("nevera_grande") if "cocina" in sistemas.muebles_de(self.j, casa) else 0)
        return AJ.entero("capacidad_despensa")

    def sitio_cabe(self, casa, sitio):
        return max(0, self.sitio_capacidad(casa, sitio) - self._total(self.de_sitio(casa, sitio)))

    def cocina_txt(self, casa):
        return (f"Nevera: {self._total(self.de_sitio(casa, 'nevera'))} de {self.sitio_capacidad(casa, 'nevera')}. "
                f"Despensa: {self._total(self.de_sitio(casa, 'despensa'))} de {self.sitio_capacidad(casa, 'despensa')}")

    def hay_cocina(self, casa):
        """¿Hay algo con lo que usar la cocina de esta casa? Algo guardado en ella, o comida que traes encima."""
        return bool(self.despensa(casa) or self.encima())

    def limpiar_despensas(self):
        """Las casas que ya no son tuyas se llevan su despensa."""
        for cid in [c for c in self.j.despensa if c not in self.j.propiedades]:
            del self.j.despensa[cid]

    def pasar_lote(self, origen, destino, lote, n, tope):
        """Pasa hasta n unidades de un lote de una lista a otra, sin pasar del sitio que queda. Devuelve cuántas han pasado."""
        n = max(0, min(int(n), int(lote["n"]), int(tope)))
        if n <= 0 or lote not in origen:
            return 0
        self._meter(destino, dict(lote, n=n))
        lote["n"] = int(lote["n"]) - n
        if lote["n"] <= 0:
            origen.remove(lote)
        return n

    def guardar_compra(self, casa):
        """Guarda en la cocina lo que llevas encima: lo fresco a la nevera y lo demás a la despensa, hasta donde quepa.
        Devuelve (guardado, se_queda_encima)."""
        self.tirar_caducado(self.j.encima)
        casa_l = self.despensa(casa)
        guardado = 0
        for lote in list(self.j.encima):
            guardado += self.pasar_lote(self.j.encima, casa_l, lote, lote["n"], self.sitio_cabe(casa, self.lote_info(lote)["sitio"]))
        return guardado, self._total(self.j.encima)

    # ================================================================== cocinar
    def _lotes_buenos(self, casa):
        """Lo que se puede usar para cocinar en una casa: lo guardado en ella y lo que traes, sin lo caducado."""
        return [(lista, x) for lista in (self.despensa(casa), self.encima()) for x in lista if not x.get("plato") and not (int(x.get("cad") or 0) and self.dia > int(x["cad"]))]

    def receta_falta(self, casa, r):
        """Los nombres de los ingredientes que faltan para una receta. Lista vacía: se puede hacer."""
        tengo = {}
        for _, x in self._lotes_buenos(casa):
            tengo[x["id"]] = tengo.get(x["id"], 0) + int(x["n"])
        faltan = []
        for ing in r["ingredientes"]:
            if tengo.get(ing, 0) > 0:
                tengo[ing] -= 1
            else:
                prod = self.producto(ing)
                faltan.append((prod["nombre"] if prod else ing).lower())
        return faltan

    def receta_txt(self, r):
        nombres = [(self.producto(i) or {"nombre": i})["nombre"].lower() for i in r["ingredientes"]]
        plato = dict(r)
        return (f"Lleva {_junta(nombres)}. {int(_num(r, 'minutos', 20))} minutos, {FUEGOS.get(r.get('fuego'), FUEGOS['hervir'])[0]}. Salen {_cuantos(int(_num(r, 'raciones', 1)), 'ración', 'raciones')}, "
                f"que aguantan {_cuantos(int(_num(r, 'caduca', 2)), 'día', 'días')} en la nevera. Cada ración {efecto_txt(plato)}. {r.get('desc') or ''}").strip()

    def cocinar(self, casa, r, rng=random):
        """Cocina una receta en una casa tuya: gasta los ingredientes, pasa el tiempo, decide cómo sale, te sirve una ración
        y guarda las demás en la nevera. Devuelve la frase con lo que ha pasado, o None si falta algo (y lo dice)."""
        j = self.j
        faltan = self.receta_falta(casa, r)
        if faltan:
            self.app.son("error")
            self.decir(f"Para {r['nombre'].lower()} te falta {_junta(faltan)}.", True)
            return None
        for ing in r["ingredientes"]:                            # primero lo de casa que antes caduca; después, lo que traes
            cand = sorted((x for x in self._lotes_buenos(casa) if x[1]["id"] == ing), key=lambda e: (e[0] is j.encima, int(e[1].get("cad") or 10 ** 9)))
            lista, lote = cand[0]
            lote["n"] = int(lote["n"]) - 1
            if lote["n"] <= 0:
                lista.remove(lote)
        self.pasar_horas(_num(r, "minutos", 20) / 60.0)
        equipada = "cocina" in sistemas.muebles_de(j, casa)
        practica = max(0.0, min(100.0, float(j.cocina_practica or 0.0)))
        calidad = 0
        if r.get("fuego", "hervir") != "no":
            p_quemado = AJ("prob_quemado") * (1.0 - practica / 100.0 * AJ("practica_quemado") / 100.0) * (1.0 - AJ("equipada_quemado") / 100.0 if equipada else 1.0)
            if rng.random() * 100 < p_quemado:
                calidad = -1
        if calidad == 0 and rng.random() * 100 < AJ("prob_especial") + practica / 100.0 * AJ("practica_especial"):
            calidad = 1
        f = 1.0 + AJ("bono_especial") / 100.0 if calidad > 0 else 1.0 - AJ("merma_quemado") / 100.0 if calidad < 0 else 1.0
        nombre = r["nombre"] + (", que salió de categoría" if calidad > 0 else ", algo quemado" if calidad < 0 else "")
        plato = {"plato": r["id"], "nombre": nombre, "cad": self.dia + max(0, int(_num(r, "caduca", 2))),
                 "hambre": round(min(100.0, _num(r, "hambre") * f), 1), "sed": round(_num(r, "sed"), 1),
                 "salud": round(_num(r, "salud") * f * (1.0 + AJ("equipada_salud") / 100.0 if equipada else 1.0), 1),
                 "animo": round(_num(r, "animo") + (AJ("animo_especial") if calidad > 0 else -AJ("animo_quemado") if calidad < 0 else 0), 1)}
        raciones = max(1, int(_num(r, "raciones", 1)))
        nivel0 = nivel_cocina(self)
        j.cocina_practica = min(100.0, practica + AJ("practica_plato"))
        j.stats["platos_cocinados"] = j.stats.get("platos_cocinados", 0) + 1
        if calidad > 0:
            j.stats["platos_especiales"] = j.stats.get("platos_especiales", 0) + 1
        partes = [f"{r['nombre']}: {_cuantos(raciones, 'ración', 'raciones')}. " + AJ.frase("frases_especial" if calidad > 0 else "frases_quemado" if calidad < 0 else "frases_normal", rng)]
        # quien vive contigo come de lo que cocinas: una vez al día cuenta para la relación
        pers = self.conviviente() if casa.id == j.convive_casa else None
        if pers is not None and self.pareja_en_casa() and raciones > 1:
            raciones -= 1
            partes.append(AJ.frase("frases_pareja", rng, n=pers["nombre"]))
            if j.convive_hoy.get("cocinado") != self.dia and calidad >= 0:
                j.convive_hoy["cocinado"] = self.dia
                if AJ("pareja_afinidad") > 0:
                    self.sumar_afinidad(j.convive, AJ.entero("pareja_afinidad") * (2 if calidad > 0 else 1))
        # una ración para ti, si te apetece
        temporal = [dict(plato, n=1)]
        info = self.lote_info(temporal[0])
        if not self._sin_ganas(info):
            comido = self.comer_lote(temporal, temporal[0])
            raciones -= 1
            partes.append("Te sirves un plato. " + comido.split(". ", 1)[1])
        else:
            partes.append("Ahora no tienes hambre: lo guardas todo.")
        if raciones > 0:
            cabe = min(raciones, self.sitio_cabe(casa, "nevera"))
            if cabe:
                self._meter(self.despensa(casa), dict(plato, n=cabe))
                partes.append(f"Guardas {_cuantos(cabe, 'ración', 'raciones')} en la nevera: {self.cad_txt(plato)}.")
            resto = raciones - cabe
            if resto:
                llevo = min(resto, self.encima_cabe())
                if llevo:
                    self._meter(j.encima, dict(plato, n=llevo))
                    partes.append(f"En la nevera no cabe más: te llevas {_cuantos(llevo, 'ración', 'raciones')} encima, en una fiambrera.")
                if resto - llevo:
                    partes.append(f"No hay dónde guardar {_cuantos(resto - llevo, 'ración', 'raciones')}: se echa a perder.")
        if nivel_cocina(self) > nivel0:
            self.son("nivel", cat="interfaz")
            partes.append(f"Tu mano en la cocina sube al nivel {nivel_cocina(self)} de 10.")
        return " ".join(partes)


# ============================================================================ recorrer la tienda
class Tienda(sistemas.Local):
    """Una tienda de comida por dentro: los pasillos, cada uno con lo suyo, la cesta y la caja."""
    cerrado_al_final = True

    def __init__(self, p, lugar):
        super().__init__(p, lugar)
        self.cesta = {}                                          # identificador del producto -> cuántos llevas en la cesta
        self.despedida = None                                    # lo que se dice al salir, después del menú de debajo
        self.visto = False
        self.surtido = p.surtido(lugar)
        nuevas = []
        for nombre, desc, que in self.habitaciones:
            if que == "mostrador":
                nuevas.append(("la caja", "El tendero y la caja registradora. Aquí se paga la cesta; sin cesta, te atienden de lo demás.", "caja"))
            elif que == "mirar":
                nuevas += [(pa["nombre"], pa.get("desc", ""), ("pasillo", pa["id"])) for pa, _ in self.surtido]
            else:
                nuevas.append((nombre, desc, que))
        self.habitaciones = nuevas

    # ------------------------------------------------------------------ la cesta
    def n_cesta(self):
        return sum(self.cesta.values())

    def total(self):
        return self.p.compra_total(self.l, self.cesta)

    def cesta_txt(self):
        if not self.cesta:
            return "La cesta está vacía."
        p = self.p
        return (f"En la cesta, {_cuantos(self.n_cesta(), 'producto', 'productos')}: "
                + "; ".join(f"{p.producto(pid)['nombre'].lower()}, {n}" for pid, n in self.cesta.items()) + f". Total, {_euros(self.total())}. Tienes {p.j.dinero}.")

    def coger(self, prod, delta=1):
        """Coge un producto del estante (o lo devuelve, con delta negativo). Devuelve True si la cesta ha cambiado."""
        p, app = self.p, self.app
        pid = prod["id"]
        if delta > 0:
            if p.agotado(self.l, prod):
                app.son("error")
                app.decir(f"{prod['nombre']}: hoy no queda. El estante está vacío.", True)
                return False
            if self.n_cesta() + 1 > p.encima_cabe():
                app.son("error")
                app.decir(f"No puedes cargar con más: llevas encima {p._total(p.encima())} cosas, en la cesta {self.n_cesta()}, y caben {AJ.entero('capacidad_encima')}.", True)
                return False
            self.cesta[pid] = self.cesta.get(pid, 0) + 1
            app.son("cesta")
            app.decir(f"{prod['nombre']}, a la cesta. Llevas {self.cesta[pid]} de esto; en total {_cuantos(self.n_cesta(), 'producto', 'productos')}, {_euros(self.total())}.", True)
            return True
        if not self.cesta.get(pid):
            app.son("menu_borde")
            app.decir("De eso no llevas en la cesta.", True)
            return False
        self.cesta[pid] -= 1
        if self.cesta[pid] <= 0:
            del self.cesta[pid]
        app.son("cesta", tono=0.75, vol=0.7)
        app.decir(f"Devuelves {prod['nombre'].lower()} al estante. Te quedan {self.cesta.get(pid, 0)}; en total {_cuantos(self.n_cesta(), 'producto', 'productos')}, {_euros(self.total())}.", True)
        return True

    # ------------------------------------------------------------------ recorrido
    def ayuda(self):
        nombre, _, que = self.habitaciones[self.i]
        aqui = ("ves lo que hay en este pasillo y coges lo que quieras" if isinstance(que, tuple) and que[0] == "pasillo" else
                "pagas la cesta, o te atienden de lo demás si no llevas nada" if que == "caja" else "sales de la tienda" if que == "salir" else
                "te acercas a hablar" if isinstance(que, tuple) else sistemas.QUE_HACE.get(que, "te lo describe"))
        return (f"Estás recorriendo {self.l.nombre} por dentro. Flechas izquierda y derecha para ir de un pasillo a otro, Intro para usar el sitio donde estás, "
                f"{self._tecla_cesta()} para saber qué llevas en la cesta y Escape para salir. Ahora estás en {nombre}: con Intro, {aqui}. "
                "En cada pasillo, Intro o flecha derecha sobre un producto lo echa a la cesta, flecha izquierda lo devuelve y F1 te dice para qué sirve y cuánto aguanta. "
                "Se paga en la caja. Si sales con la cesta llena, te preguntan qué haces con ella.")

    def al_entrar(self):
        self.app.mez.entorno = "interior"
        nombre, desc, _ = self.habitaciones[self.i]
        if self.visto:                                           # al volver de un pasillo o de la caja: solo dónde estás y cómo va la cesta
            self.app.decir(f"{nombre.capitalize()}. " + (f"Cesta: {_cuantos(self.n_cesta(), 'producto', 'productos')}, {_euros(self.total())}." if self.cesta else "Cesta vacía."), True)
            return
        self.visto = True
        p = self.p
        of = p.producto(p.oferta_de(self.l)) if p.oferta_de(self.l) else None
        nombres = _junta(pa["nombre"] for pa, _ in self.surtido)
        self.app.decir(f"{self.l.nombre}, por dentro. Coges una cesta. Estás en {nombre}. {desc} Hay {_cuantos(len(self.surtido), 'pasillo', 'pasillos')}: {nombres}. "
                       + (f"Hoy, de oferta: {of['nombre'].lower()}. " if of else "")
                       + f"Flechas izquierda y derecha para moverte, Intro para mirar un pasillo o pagar en la caja, {self._tecla_cesta()} para la cesta, Escape para salir.", True)

    def _decir(self):
        nombre, desc, que = self.habitaciones[self.i]
        extra = ""
        if isinstance(que, tuple) and que[0] == "pasillo":
            genero = next(lista for pa, lista in self.surtido if pa["id"] == que[1])
            extra = f" {_cuantos(len(genero), 'producto', 'productos')}."
        elif que == "caja" and self.cesta:
            extra = f" Llevas {_cuantos(self.n_cesta(), 'producto', 'productos')}: {_euros(self.total())}."
        self.app.decir(f"{nombre.capitalize()}. {desc}{extra} {self.i + 1} de {len(self.habitaciones)}.", True)

    def _tecla_cesta(self):
        """Con qué se oye la cesta: la C o, jugando con mando, su botón (X o Cuadrado, que aquí llega como Tabulador)."""
        md = getattr(self.app, "mando", None)
        return md.boton_pantalla(pygame.K_TAB, "C") if md is not None else "C"

    def tecla(self, ev):
        if ev.key in (pygame.K_c, pygame.K_TAB):
            self.app.son("cesta", vol=0.5)
            self.app.decir(self.cesta_txt(), True)
        elif ev.key == pygame.K_ESCAPE:
            self._salir()
        else:
            super().tecla(ev)

    def _usar(self):
        nombre, desc, que = self.habitaciones[self.i]
        if isinstance(que, tuple) and que[0] == "pasillo":
            self._pasillo(que[1])
        elif que == "caja":
            self._caja()
        elif que == "salir":
            self._salir()
        else:
            super()._usar()

    def _pasillo(self, ident):
        p, app = self.p, self.app
        pa, genero = next((pa, lista) for pa, lista in self.surtido if pa["id"] == ident)
        oferta = p.oferta_de(self.l)

        def texto(prod):
            def f():
                t = f"{prod['nombre']}: {_euros(p.precio_producto(self.l, prod))}"
                if prod["id"] == oferta:
                    t += ", de oferta"
                if p.agotado(self.l, prod):
                    return f"{prod['nombre']}: hoy no queda"
                t += ". " + (("Para beber" if prod.get("bebida") else "Para comer") + " tal cual" if comestible(prod) else "Para cocinar")
                return t + (f". En la cesta: {self.cesta[prod['id']]}" if self.cesta.get(prod["id"]) else "")
            return f

        def mover(prod):
            def f(delta=1):
                self.coger(prod, delta)
            return f

        def ops():
            lista = [Opcion(texto(prod), mover(prod), ajuste=mover(prod), ayuda=p.producto_ayuda(prod) + " Intro o flecha derecha lo echa a la cesta; flecha izquierda lo devuelve.", callado=True)
                     for prod in genero]
            lista.append(Opcion(lambda: "La cesta: " + (f"{_cuantos(self.n_cesta(), 'producto', 'productos')}, {_euros(self.total())}" if self.cesta else "vacía"),
                                lambda: app.decir(self.cesta_txt(), True), ayuda="Dice lo que llevas en la cesta y lo que suma. Se paga en la caja."))
            return lista
        app.abrir(MenuCesta(app, lambda: f"{pa['nombre'].capitalize()}. Tienes {p.j.dinero} euros", ops, intro="Intro echa un producto a la cesta; flecha izquierda lo devuelve"))

    def _caja(self):
        p, app = self.p, self.app
        if not self.cesta:                                       # sin cesta, la caja es el mostrador de siempre: te atienden en el menú de la tienda
            self.habitaciones[self.i] = ("la caja", self.habitaciones[self.i][1], "mostrador")
            try:
                super()._usar()
            finally:
                if self in app.pila:
                    self.habitaciones[self.i] = ("la caja", self.habitaciones[self.i][1], "caja")
            return

        def cambiar(pid):
            def f(delta):
                self.coger(p.producto(pid), delta)
                if not self.cesta:
                    app.cerrar(m)
                    app.decir("Has devuelto todo. La cesta está vacía.", True)
                else:
                    m.refrescar(False)
            return f

        def pagar():
            total = self.total()
            if p.comprar_productos(self.l, self.cesta):
                n = self.n_cesta()
                self.cesta = {}
                app.cerrar(m)
                app.decir(AJ.frase("frases_caja", total=_euros(total)) + f" Llevas encima {_cuantos(p._total(p.encima()), 'cosa', 'cosas')}"
                          f"{', ' + str(n) + ' de ahora' if p._total(p.encima()) != n else ''}. Te quedan {_euros(p.j.dinero)}. Guárdalo en la cocina de una casa tuya.", True)

        def ops():
            lista = [Opcion(lambda pid=pid: f"{p.producto(pid)['nombre']}: {self.cesta.get(pid, 0)}, {_euros(p.precio_producto(self.l, p.producto(pid)) * self.cesta.get(pid, 0))}. Intro devuelve uno",
                            lambda pid=pid: cambiar(pid)(-1), ajuste=cambiar(pid), callado=True,
                            ayuda="Intro o flecha izquierda devuelve uno al estante; flecha derecha coge otro. " + p.producto_ayuda(p.producto(pid))) for pid in list(self.cesta)]
            lista.insert(0, Opcion(lambda: f"Pagar {_euros(self.total())} por {_cuantos(self.n_cesta(), 'producto', 'productos')}", pagar, callado=True,
                                   ayuda="Pagas la cesta entera y te lo llevas encima. Si no te llega el dinero, te dicen cuánto falta y puedes devolver algo aquí mismo."))
            return lista
        m = MenuCesta(app, lambda: f"La caja. Cesta: {_cuantos(self.n_cesta(), 'producto', 'productos')}, {_euros(self.total())}. Tienes {_euros(p.j.dinero)}", ops)
        app.abrir(m)

    def _salir(self):
        p, app = self.p, self.app
        if not self.cesta:
            app.son("menu_atras")
            app.cerrar(self)
            return

        def a_la_caja():
            app.cerrar(m)
            self.i = next(k for k, h in enumerate(self.habitaciones) if h[2] == "caja")
            self._caja()

        def dejar():
            self.cesta = {}
            k = app.pila.index(self) if self in app.pila else 0
            debajo = app.pila[k - 1] if k > 0 else None
            if debajo is not None and hasattr(debajo, "antes"):
                debajo.antes = AJ.frase("frases_dejar").rstrip(".")     # el menú de la tienda lo dice delante de su título
            else:
                self.despedida = AJ.frase("frases_dejar")
            app.cerrar(m)
            app.son("cesta", tono=0.75, vol=0.7)
            app.cerrar(self)

        def robar():
            visto, frase = p.robar_productos(self.l, self.cesta)
            self.cesta = {}
            while len(app.pila) > 1 and app.pila[-1] is not p:     # a la calle, sin pasar por el menú de la tienda
                app.pila.pop()
            app.teclas.clear()
            p.salir_interior(silencio=visto)
            p.decir(frase + f" Llevas encima {_cuantos(p._total(p.encima()), 'cosa', 'cosas')}.", True)
        m = Menu(app, f"Llevas {_cuantos(self.n_cesta(), 'producto', 'productos')} sin pagar, {_euros(self.total())}", [
            Opcion("Ir a la caja a pagar", a_la_caja),
            Opcion("Dejar la cesta y salir", dejar, callado=True, ayuda="La cesta se queda en la tienda con todo dentro. No pasa nada más."),
            Opcion("Salir sin pagar", robar, callado=True,
                   ayuda="Te lo llevas todo sin pasar por caja. Es un hurto: si te ven, y cuanto más lleves más fácil es, la policía te busca, baja tu prestigio entre los vecinos "
                         "y en esta tienda no te dejan entrar durante unos días. Si no te ven, no pasa nada."),
            Opcion("Seguir comprando", lambda: app.cerrar(m))])
        app.abrir(m)

    def cerrado(self):
        if self.despedida:
            self.app.decir(self.despedida)
            self.despedida = None


class MenuCesta(Menu):
    """Un menú de productos: con las flechas izquierda y derecha se coge o se devuelve, y lo que se oye es lo que dice la
    cesta, sin releer la opción encima."""

    def tecla(self, ev):
        if ev.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.opciones and self.opciones[self.i].ajuste:
            self.opciones[self.i].ajuste(1 if ev.key == pygame.K_RIGHT else -1)
        else:
            super().tecla(ev)
