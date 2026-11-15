"""El transporte público que se ve y se oye desde la calle: tranvías que recorren las vías, y los trenes y aviones
que entran y salen de la estación y del aeropuerto.

Las vías están en `Mundo` (por qué calles van y dónde paran). Aquí está lo que se mueve: uno o varios tranvías por
ciudad, que avanzan por la línea, paran en cada parada y tocan la campana. Se les oye venir desde donde están, y si
el jugador está en la vía por delante, el conductor toca la campana sin parar. Si aun así no se aparta, lo arrolla.
"""
import math
import random

VELOCIDAD = 8.5          # metros por segundo: un tranvía de ciudad
VEL_TREN = 17.0          # el tren cruza la localidad bastante más deprisa
PARADA_TREN = 9.0        # segundos parado en la estación
OIR_TREN = 280.0         # el tren se oye desde más lejos que el tranvía
LEJOS = 320.0            # de cuánto más allá del borde de la localidad viene, y hasta dónde se va
PARADA = 5.0             # segundos que se detiene en cada parada
OIR = 150.0              # desde qué distancia se crea el sonido del tranvía


def callar(p):
    for t in getattr(p, "tranvias", []):
        if t.get("canal") is not None:
            t["canal"].parar()
            t["canal"] = None
    for c, _ in getattr(p, "_sonidos_transporte", []):
        c.parar()
    p._sonidos_transporte = []
    t = getattr(p, "tren", None)
    if t and t.get("canal") is not None:
        t["canal"].parar()
    p.tren = None


def preparar(p):
    """Pone los tranvías de la localidad actual en sus vías, repartidos por la línea."""
    callar(p)
    m = p.mundo
    p._transporte_mapa = m.id
    p.tranvias = []
    p.t_tren = random.uniform(25, 60)
    p.t_avion = random.uniform(30, 70)
    largo = getattr(m, "via_largo", 0.0)
    if largo <= 0:
        return
    n = max(1, min(3, int(round(largo / 1600.0))))
    for k in range(n):
        p.tranvias.append({"s": largo * k / n, "espera": 0.0, "canal": None, "t_campana": 0.0, "a_bordo": False, "avisado": False, "numero": k + 1})


def _tranvia_mas_cercano(p, s):
    largo = p.mundo.via_largo
    return min(p.tranvias, key=lambda t: min((t["s"] - s) % largo, (s - t["s"]) % largo)) if p.tranvias else None


def subir(p, parada):
    """El jugador sube en una parada: el tranvía más cercano de la línea es el que le recoge, y se queda con él."""
    if getattr(p, "_transporte_mapa", None) != p.mundo.id:
        preparar(p)
    s = p.mundo.via_marca(parada)
    t = _tranvia_mas_cercano(p, s) if s is not None else None
    if t is not None:
        t["s"], t["espera"], t["a_bordo"] = s, 9999.0, True
    return t


def bajar(p, parada):
    """El jugador se baja: su tranvía queda en esa parada y sigue la línea enseguida."""
    s = p.mundo.via_marca(parada)
    for t in getattr(p, "tranvias", []):
        if t["a_bordo"]:
            t["a_bordo"] = False
            t["espera"] = 4.0
            if s is not None:
                t["s"] = s


def paso(p, dt):
    """Un fotograma del transporte de la localidad."""
    if getattr(p, "_transporte_mapa", None) != p.mundo.id:
        preparar(p)
    m = p.mundo
    j = p.j
    x, y = p.pos()
    # sonidos sueltos con caducidad (el tren que entra en la estación)
    vivos = []
    for c, hasta in p._sonidos_transporte:
        if p.t >= hasta:
            c.parar()
        else:
            vivos.append((c, hasta))
    p._sonidos_transporte = vivos
    largo = m.via_largo
    for t in p.tranvias:
        if t["a_bordo"]:
            continue
        tx, ty = m.via_punto(t["s"])
        d = math.hypot(tx - x, ty - y)
        andando = t["espera"] <= 0
        if not andando:
            t["espera"] -= dt
            if t["espera"] <= 0 and d < OIR:
                p.son("tranvia_campana", xy=(tx, ty), ref=10, maxd=120, vol=0.8)        # arranca
        else:
            antes = t["s"]
            t["s"] = (t["s"] + VELOCIDAD * dt) % largo
            for marca in m.via_marcas:                           # ¿ha llegado a una parada?
                if (marca - antes) % largo <= VELOCIDAD * dt + 1e-6 and (marca - antes) % largo >= 0 and marca != antes:
                    t["s"] = marca
                    t["espera"] = PARADA
                    if d < OIR:
                        p.son("tranvia_campana", xy=(tx, ty), ref=10, maxd=120, vol=0.8)
                    break
            tx, ty = m.via_punto(t["s"])
            d = math.hypot(tx - x, ty - y)
        # el sonido del tranvía, desde donde está
        if d < OIR:
            if t["canal"] is None:
                t["canal"] = p.son("tranvia", bucle=True, xy=(tx, ty), ref=9, maxd=OIR, vol=0.9)
            t["canal"].mover(tx, ty)
            t["canal"].tono(1.0 if andando else 0.55)
            t["canal"].volumen(0.9 if andando else 0.35)
        elif t["canal"] is not None:
            t["canal"].parar()
            t["canal"] = None
        if not andando:
            t["avisado"] = False
            continue
        # el jugador está en la vía, por delante: campana, y si no se aparta, golpe
        if d < 55 and m.en_via(x, y):
            delante = any(math.hypot(px - x, py - y) < 4.5 for px, py in (m.via_punto(t["s"] + k) for k in range(6, 56, 4)))
            if delante:
                t["t_campana"] -= dt
                if t["t_campana"] <= 0:
                    t["t_campana"] = 1.0
                    p.son("tranvia_campana", xy=(tx, ty), ref=14, maxd=140, vol=1.0)
                if not t["avisado"]:
                    t["avisado"] = True
                    p.decir(f"¡Viene el tranvía, {p.direccion_txt(tx, ty)}! Sal de las vías.")
        else:
            t["avisado"] = False
        if d < 3.2 and not p.transicion:
            t["espera"] = 4.0
            p.son("choque", xy=(tx, ty), vol=0.9)
            if j.veh:
                p.danar_vehiculo(j.veh, 45)
                j.veh.vel *= 0.2
                p.decir("¡El tranvía te embiste!")
            else:
                ax, ay = m.fuera_de_la_via(x, y)
                j.x, j.y = ax, ay
                p.danar_jugador(35, (tx, ty))
                p.app.vibrar(1.0, 1.0, 400)
                p.decir("¡Te ha arrollado el tranvía! Te aparta de las vías de un golpe.")
    _paso_tren(p, dt, x, y)
    p.t_avion -= dt
    if p.t_avion <= 0:
        p.t_avion = random.uniform(80, 130)
        aer = next((l for l in m.lugares.values() if l.tipo == "aeropuerto"), None)
        if aer is not None and math.hypot(aer.x - x, aer.y - y) < 420:
            c = p.son("avion_despegue", xy=(aer.x, aer.y), ref=40, maxd=450, vol=1.0)
            c.alto = 60.0                                        # con el motor envolvente, suena por encima


def lanzar_tren(p, sentido=None):
    """Hace entrar un tren en la localidad por un extremo de la vía. Devuelve el tren, o None si aquí no hay vía."""
    m = p.mundo
    if getattr(m, "tren_largo", 0.0) <= 0:
        return None
    sentido = sentido if sentido in (1, -1) else random.choice((1, -1))
    p.tren = {"s": -LEJOS if sentido > 0 else m.tren_largo + LEJOS, "sentido": sentido, "espera": 0.0, "parado": False, "ha_parado": False,
              "canal": None, "t_silbato": 0.0, "avisado": False}
    return p.tren


def _paso_tren(p, dt, x, y):
    """El tren: entra por un extremo de la vía, para en la estación, sigue y sale por el otro. Se le oye venir desde
    donde está; si el jugador está en la vía por delante, pita sin parar, y si no se aparta, lo arrolla."""
    m = p.mundo
    j = p.j
    t = p.tren
    if t is None:
        p.t_tren -= dt
        if p.t_tren <= 0:
            p.t_tren = random.uniform(75, 120)
            lanzar_tren(p)
        return
    tx, ty = m.tren_punto(t["s"])
    d = math.hypot(tx - x, ty - y)
    if t["parado"]:
        t["espera"] -= dt
        if t["espera"] <= 0:
            t["parado"] = False
            if d < OIR_TREN:
                p.son("tren_silbato", xy=(tx, ty), ref=25, maxd=OIR_TREN, vol=0.9)          # sale de la estación
    else:
        antes = t["s"]
        t["s"] += VEL_TREN * dt * t["sentido"]
        if not t["ha_parado"] and (antes - m.tren_parada) * (t["s"] - m.tren_parada) <= 0:      # llega al andén
            t["s"], t["parado"], t["ha_parado"], t["espera"] = m.tren_parada, True, True, PARADA_TREN
            if d < OIR_TREN:
                p.son("tren_silbato", xy=m.tren_punto(t["s"]), ref=25, maxd=OIR_TREN, vol=0.8)
        tx, ty = m.tren_punto(t["s"])
        d = math.hypot(tx - x, ty - y)
        if t["s"] < -LEJOS - 1 or t["s"] > m.tren_largo + LEJOS + 1:                            # ya se ha ido
            if t["canal"] is not None:
                t["canal"].parar()
            p.tren = None
            return
    if d < OIR_TREN:
        if t["canal"] is None:
            t["canal"] = p.son("tren", bucle=True, xy=(tx, ty), ref=16, maxd=OIR_TREN, vol=1.0)
        t["canal"].mover(tx, ty)
        t["canal"].tono(0.6 if t["parado"] else 1.0)
        t["canal"].volumen(0.3 if t["parado"] else 1.0)
    elif t["canal"] is not None:
        t["canal"].parar()
        t["canal"] = None
    if t["parado"]:
        t["avisado"] = False
        return
    # el jugador está en la vía, por delante: silbato, y si no se aparta, golpe
    por_delante = ((x if m.tren_eje == "H" else y) - t["s"]) * t["sentido"]
    if 0 < por_delante < 130 and m.en_via_tren(x, y):
        t["t_silbato"] -= dt
        if t["t_silbato"] <= 0:
            t["t_silbato"] = 1.6
            p.son("tren_silbato", xy=(tx, ty), ref=30, maxd=OIR_TREN, vol=1.0)
        if not t["avisado"]:
            t["avisado"] = True
            p.decir(f"¡Viene el tren, {p.direccion_txt(tx, ty)}! Sal de las vías.")
        if por_delante < 4.0 and not p.transicion:
            p.son("choque", xy=(tx, ty), vol=1.0)
            ax, ay = m.fuera_de_la_via(x, y)
            if j.veh:
                p.danar_vehiculo(j.veh, 90)
                j.veh.vel *= 0.1
                j.veh.x, j.veh.y = ax, ay
                p.decir("¡El tren embiste tu vehículo y lo saca de las vías!")
            else:
                j.x, j.y = ax, ay
                p.danar_jugador(60, (tx, ty))
                p.app.vibrar(1.0, 1.0, 500)
                p.decir("¡Te ha arrollado el tren! Sales despedido fuera de las vías.")
    else:
        t["avisado"] = False
