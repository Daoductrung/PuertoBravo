"""Los coches aparcados y el desguace (1.7.2): que la calle cambie cada día y que vender coches robados no sea una mina.

Cada plaza de aparcamiento de la calle tenía su número de la suerte fijo desde que se hacía el mapa: la misma plaza sacaba
siempre el mismo modelo, día tras día. Ahora el modelo de cada plaza se sortea cada día, con la semilla de la partida: los
coches caros salen bastante menos que los demás, y alguna plaza amanece vacía.

El desguace paga por lo que vale el vehículo y por cómo está, como siempre, pero:
- por un vehículo que no es tuyo, con papeles, paga menos: es mercancía que quema. Tuyo es el que compras y el que
  mejoras en un taller; el que robas, no (la marca «robado» se pone al subirte y se guarda con la partida). Uno
  alquilado no se vende;
- desde la 1.7.4, de un vehículo tuyo devuelve parte de lo que pagaste en mejoras, según cómo esté;
- un vehículo sin valor de mercado (el autobús, un barco, una aeronave) se paga como chatarra: una cantidad fija por
  modelo o una parte de su precio. Los oficiales (patrulla, ambulancia, bomberos...) no los compra nadie, y el menú
  dice por qué;
- si en los últimos días le han llegado vehículos del mismo modelo, paga cada vez menos: el mercado se llena;
- cada desguace compra unos pocos vehículos al día; el resto, vuelve mañana o prueba en otro.

Los números y las frases están en los datos (vida.json, sección desguace).
"""
from .i18n import tr
import random

from .ajustes import Ajustes

AJ = Ajustes("desguace", {
    "plaza_vacia_prob": 12, "caro_valor": 4000, "caro_peso": 20,
    "robado_pct": 60, "saturacion_pct": 25, "saturacion_min": 25, "saturacion_dias": 7, "cupo_dia": 3,
    "mejoras_pct": 35, "chatarra_precio_pct": 20,
}, {
    "chatarra": ["autobus=1800"],
    "oficiales": ["patrulla", "ambulancia", "bomberos", "furgon_asalto", "blindado"],
    "frases_oficial": [tr("Eso es un vehículo oficial: aquí no lo compra nadie, que se sabe de quién es y lo están buscando."),
                       tr("¿Un {modelo}? Ni loco. Eso lo reconoce cualquiera, y aquí no quiero problemas.")],
    "frases_alquilado": [tr("Ese vehículo es alquilado: no es tuyo para venderlo. Devuélvelo o déjalo donde te digan.")],
    "frases_lleno": [tr("Por hoy ya no compramos más. Vuelve mañana, o prueba en otro desguace."),
                     tr("Hoy ya tenemos el patio lleno. Mañana hablamos."),
                     tr("No me cabe ni un tornillo más hasta mañana.")],
    "frases_saturado": [tr("Otro {modelo}... Esta semana ya me han traído {n}. No me lo quitan de las manos, así que pago menos."),
                        tr("¿Otro {modelo}? Tengo {n} en el patio de estos días. Te doy lo que te doy.")],
}, cero=("plaza_vacia_prob", "caro_peso", "saturacion_pct", "saturacion_min", "mejoras_pct", "chatarra_precio_pct"))


def _caro(modelo):
    return int(modelo.get("valor", 0) or 0) >= AJ("caro_valor")


def modelo_de_plaza(p, plaza, ids, mapa_id):
    """El modelo aparcado hoy en esta plaza, o None si hoy está vacía. Cambia cada día y es el mismo todo el día."""
    rng = random.Random(f"{getattr(p.j, 'semilla', 0)}-{p.dia}-plaza-{mapa_id}-{plaza['id']}")
    if rng.random() * 100 < AJ("plaza_vacia_prob"):
        return None
    pesos = [AJ("caro_peso") / 100.0 if _caro(p.modelos[i]) else 1.0 for i in ids]
    if sum(pesos) <= 0:
        pesos = [1.0] * len(ids)
    return rng.choices(ids, weights=pesos)[0]


def _datos(j):
    d = getattr(j, "desguace", None)
    if not isinstance(d, dict):
        d = j.desguace = {}
    d.setdefault("ventas", [])                                   # [[día, modelo]] de los últimos días
    d.setdefault("hoy", {})                                      # {desguace: [día, vendidos ese día]}
    return d


def vendidos_recientes(p, modelo_id):
    d = _datos(p.j)
    desde = p.dia - AJ.entero("saturacion_dias")
    d["ventas"] = [x for x in d["ventas"] if x[0] > desde]
    return sum(1 for x in d["ventas"] if x[1] == modelo_id)


def cupo_lleno(p, l):
    dia, n = _datos(p.j)["hoy"].get(l.id, [p.dia, 0])
    return dia == p.dia and n >= AJ.entero("cupo_dia")


def robado(v):
    """Si el desguace lo paga como robado: el que no es tuyo, con papeles. Uno de una partida anterior a la 1.7.4 que ya
    tenías, sin la marca, cuenta como tuyo, que es como se pagaba."""
    return bool(getattr(v, "robado", False)) or not getattr(v, "propio", False)


def _chatarra():
    r = {}
    for linea in AJ.lista("chatarra"):
        k, _, n = str(linea).partition("=")
        try:
            r[k.strip()] = int(float(n))
        except ValueError:
            pass
    return r


def oficial(v):
    return v.modelo["id"] in {str(x).strip() for x in AJ.lista("oficiales")}


def valor(v):
    """Lo que vale el vehículo entero para el desguace: su valor de mercado o, sin él, lo que vale como chatarra."""
    n = int(v.modelo.get("valor", 0) or 0)
    if n > 0:
        return n
    if oficial(v):
        return 0
    fija = _chatarra().get(v.modelo["id"])
    if fija is not None:
        return max(0, fija)
    return int(int(v.modelo.get("precio", 0) or 0) * AJ("chatarra_precio_pct") / 100.0)


def gastado_en_mejoras(v):
    """Lo que costaron las mejoras que lleva: cada nivel se pagó al precio de su mejora por el nivel."""
    from . import sistemas
    total = 0
    for k, n in (getattr(v, "mejoras", None) or {}).items():
        if k in sistemas.MEJORAS and n:
            total += sistemas.MEJORAS[k]["precio"] * int(n) * (int(n) + 1) // 2
    return total


def precio(p, v):
    """Lo que paga el desguace por este vehículo, ahora."""
    if getattr(v, "alquilado", False):
        return 0
    estado = 0.3 + 0.7 * max(0.0, v.salud) / v.salud_max
    base = (valor(v) + gastado_en_mejoras(v) * AJ("mejoras_pct") / 100.0) * estado
    if robado(v):
        base *= AJ("robado_pct") / 100.0
    n = vendidos_recientes(p, v.modelo["id"])
    if n:
        base *= max(AJ("saturacion_min") / 100.0, 1.0 - n * AJ("saturacion_pct") / 100.0)
    return int(base)


def por_que_no(v):
    """Por qué no lo compran, cuando lo que pagan es cero."""
    if getattr(v, "alquilado", False):
        return AJ.frase("frases_alquilado", modelo=v.modelo["nombre"])
    if oficial(v):
        nombre = v.modelo["nombre"]
        return AJ.frase("frases_oficial", modelo=nombre[:1].lower() + nombre[1:])     # «¿Un coche patrulla?», a media frase
    return tr("Eso no lo quieren ni regalado.")


def comentario(p, v):
    """Lo que dice el del desguace si ya le han llegado otros iguales estos días; cadena vacía si no."""
    n = vendidos_recientes(p, v.modelo["id"])
    return AJ.frase("frases_saturado", modelo=v.modelo["nombre"], n=n) if n else ""


def apuntar_venta(p, l, v):
    d = _datos(p.j)
    d["ventas"].append([p.dia, v.modelo["id"]])
    dia, n = d["hoy"].get(l.id, [p.dia, 0])
    d["hoy"][l.id] = [p.dia, (n if dia == p.dia else 0) + 1]


def frase_lleno():
    return AJ.frase("frases_lleno")
