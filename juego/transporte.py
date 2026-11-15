"""El transporte público que se ve y se oye desde la calle: tranvías que recorren las vías, y los trenes y aviones
que entran y salen de la estación y del aeropuerto.

Las vías están en `Mundo` (por qué calles van y dónde paran). Aquí está lo que se mueve: uno o varios tranvías por
ciudad, que avanzan por la línea, paran en cada parada y tocan la campana. Se les oye venir desde donde están, y si
el jugador está en la vía por delante, el conductor toca la campana sin parar. Si aun así no se aparta, lo arrolla.
"""
import math
import random

VELOCIDAD = 8.5          # metros por segundo: un tranvía de ciudad
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
    # la estación de tren y el aeropuerto también se oyen desde la calle
    p.t_tren -= dt
    if p.t_tren <= 0:
        p.t_tren = random.uniform(70, 110)
        est = next((l for l in m.lugares.values() if l.tipo == "tren"), None)
        if est is not None and math.hypot(est.x - x, est.y - y) < 260:
            p.son("tren_silbato", xy=(est.x, est.y), ref=25, maxd=280, vol=0.9)
            p._sonidos_transporte.append((p.son("tren", bucle=True, xy=(est.x, est.y), ref=18, maxd=220, vol=0.8), p.t + 9.0))
    p.t_avion -= dt
    if p.t_avion <= 0:
        p.t_avion = random.uniform(80, 130)
        aer = next((l for l in m.lugares.values() if l.tipo == "aeropuerto"), None)
        if aer is not None and math.hypot(aer.x - x, aer.y - y) < 420:
            c = p.son("avion_despegue", xy=(aer.x, aer.y), ref=40, maxd=450, vol=1.0)
            c.alto = 60.0                                        # con el motor envolvente, suena por encima
