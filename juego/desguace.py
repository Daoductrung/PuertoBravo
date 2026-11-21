"""Los coches aparcados y el desguace (1.7.2): que la calle cambie cada día y que vender coches robados no sea una mina.

Cada plaza de aparcamiento de la calle tenía su número de la suerte fijo desde que se hacía el mapa: la misma plaza sacaba
siempre el mismo modelo, día tras día. Ahora el modelo de cada plaza se sortea cada día, con la semilla de la partida: los
coches caros salen bastante menos que los demás, y alguna plaza amanece vacía.

El desguace paga por lo que vale el vehículo y por cómo está, como siempre, pero:
- por un vehículo que no es tuyo, con papeles, paga menos: es mercancía que quema;
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
}, {
    "frases_lleno": [tr("Por hoy ya no compramos más. Vuelve mañana, o prueba en otro desguace."),
                     tr("Hoy ya tenemos el patio lleno. Mañana hablamos."),
                     tr("No me cabe ni un tornillo más hasta mañana.")],
    "frases_saturado": [tr("Otro {modelo}... Esta semana ya me han traído {n}. No me lo quitan de las manos, así que pago menos."),
                        tr("¿Otro {modelo}? Tengo {n} en el patio de estos días. Te doy lo que te doy.")],
}, cero=("plaza_vacia_prob", "caro_peso", "saturacion_pct", "saturacion_min"))


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


def precio(p, v):
    """Lo que paga el desguace por este vehículo, ahora."""
    base = v.modelo["valor"] * (0.3 + 0.7 * max(0.0, v.salud) / v.salud_max)
    if not getattr(v, "propio", False):
        base *= AJ("robado_pct") / 100.0
    n = vendidos_recientes(p, v.modelo["id"])
    if n:
        base *= max(AJ("saturacion_min") / 100.0, 1.0 - n * AJ("saturacion_pct") / 100.0)
    return int(base)


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
