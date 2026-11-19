"""Menús de los lugares de la ampliación: viajes, barcos, banco, ocio y comercios."""
import math
import random

from . import mundo as M
from .menus import Menu, Opcion

PELICULAS = [
    "«El último tranvía»: un drama lentísimo en el que no pasa nada, pero pasa muy bien.",
    "«Tiburones en la Gran Vía»: tan mala que el público aplaude de pie.",
    "«Amor en el desguace»: lloras, y no sabes si de pena o de risa.",
    "«El comisario honrado»: ciencia ficción, según el señor de la butaca de al lado.",
    "«Rápidos y jubilados»: persecuciones en utilitario a cuarenta por hora. Una joya.",
    "«La venganza del boquerón»: cine de terror marinero. Sales con hambre.",
]
def _menu(p, l, ops, intro=None):
    m = Menu(p.app, lambda: f"{l.nombre}. Tienes {p.j.dinero} euros", ops, intro=intro)
    p.app.abrir(m)
    return m


def _policia_cerca(p, radio=60):
    x, y = p.pos()
    return any(e.tipo == "policia" and not e.muerto and e.dist(x, y) < radio for e in p.personas) or \
        any(p.es_patrulla(o) and o.dist(x, y) < radio for o in p.vehiculos)


# ======================================================================== viajes
def salida(p, l):
    app = p.app
    j = p.j
    dest = p.lug(l.get("a_lugar"))
    if dest is None:
        app.decir(f"{l.nombre}. La carretera está cortada.", True)
        return
    mapa = p.mapas[dest.mapa]
    horas = float(l.get("horas", 1))
    if not j.veh:
        final = p.lug(p.gps["final"]) if p.gps and p.gps.get("final") else None
        estacion_aqui = next((e for e in p.mundo.lugares.values() if e.tipo == "estacion"), None)
        texto = (f"{l.nombre}. Por aquí se va a {mapa.nombre}, pero solo en un vehículo: llega hasta aquí al volante, de cualquier coche o moto, "
                 "y pulsa Intro sin bajarte.")
        if estacion_aqui is None:
            app.decir(texto + " Aquí no hay estación de autobuses.", True)
        elif final is not None and p.conexion_hacia(final.mapa) is not l:        # ibas de viaje: a pie, el GPS te lleva al autobús
            app.decir(texto + " A pie se viaja en autobús.", True)
            p.gps_a_lugar(final, callar=True)
        else:
            app.decir(texto + f" A pie se viaja en autobús, desde {estacion_aqui.nombre}: márcala con la tecla L, en Viajes.", True)
        return
    if j.estrellas and _policia_cerca(p):
        app.son("error")
        app.decir("¡Con la policía pegada no puedes salir a la carretera! Despístalos primero.", True)
        return

    def ir():
        app.cerrar(m)
        x, y, d = mapa.plaza_junto_a(dest)
        x, y = (x, mapa.carril("H", mapa._idx(y, mapa.NY), d)) if d in (1, 3) else (mapa.carril("V", mapa._idx(x, mapa.NX), d), y)
        p.pasar_horas(horas)
        p.son("lugar_salida", cat="interfaz")
        p.cambiar_mapa(mapa.id, x, y, d * 90.0,
                       f"Tras {l.get('km', 20)} kilómetros de carretera llegas a {mapa.nombre}. Son las {p.hora_txt()}. Vas hacia el {M.NOMBRE_DIR[d]} por {mapa.describir(x, y)}.")
    m = _menu(p, l, [Opcion(f"Tomar la carretera hasta {mapa.nombre}, {l.get('km', 20)} kilómetros", ir, ayuda=p.desc_localidad(mapa))])


def estacion(p, l):
    app = p.app
    if p.j.veh:
        if p.trabajo and p.trabajo.get("tipo") == "camion" and p.trabajo.get("veh") is p.j.veh:
            app.decir(f"{l.nombre}. La carga no viaja en autobús: se lleva con el camión, por carretera. Pulsa G y el GPS te guía hasta la salida.", True)
            p.gps_a_lugar(p.trabajo["lugar"], auto=True, callar=True)
            return
        app.decir(f"{l.nombre}. Bájate del vehículo para coger el autobús.", True)
        return
    if p.j.estrellas:
        app.son("error")
        app.decir("El conductor te mira, mira el cartel de se busca y cierra la puerta.", True)
        return

    def viajar(dest):
        def f():
            precio = int(dest.get("precio", p.precio("autobus", 20)))
            if not p.pagar(precio):
                return
            app.cerrar(m)
            p.son("lugar_estacion", cat="interfaz")

            def llegar():
                p.pasar_horas(1.5)
                p.cambiar_mapa(dest.mapa, dest.x, dest.y, None,
                               f"El autobús te deja en {dest.nombre}, {p.mapas[dest.mapa].nombre}. Son las {p.hora_txt()}.")
            from .pantallas import viajar as trayecto
            trayecto(app, 50.0, llegar, autobus=True, destino=p.mapas[dest.mapa].nombre)
        return f
    ops = [Opcion(f"Autobús a {p.mapas[e.mapa].nombre}: {int(e.get('precio', p.precio('autobus', 20)))} euros", viajar(e), ayuda=p.desc_localidad(p.mapas[e.mapa]))
           for e in p.lugares.values() if e.tipo == "estacion" and e.mapa != p.mundo.id]
    m = _menu(p, l, ops or [Opcion("Hoy no sale ningún autobús")])


# ------------------------------------------------------------------ tranvía: para moverse dentro de la ciudad
PRECIO_TRANVIA = 2


def linea_tranvia(p, mapa=None):
    """Las paradas de tranvía de una ciudad, en el orden en que las recorre la línea: dando la vuelta a la ciudad."""
    m = p.mapas[mapa] if mapa else p.mundo
    return m.linea_tranvia() if hasattr(m, "linea_tranvia") else []


def recorrido_tranvia(p, origen, destino):
    """Las paradas por las que pasa el tranvía de una a otra, por el lado más corto de la línea, sin la de origen."""
    linea = linea_tranvia(p, origen.mapa)
    a, b = linea.index(origen), linea.index(destino)
    n = len(linea)
    adelante = [linea[(a + k) % n] for k in range(1, (b - a) % n + 1)]
    atras = [linea[(a - k) % n] for k in range(1, (a - b) % n + 1)]
    return adelante if len(adelante) <= len(atras) else atras


def tranvia(p, l):
    app = p.app
    if p.j.veh:
        app.decir(f"{l.nombre}. Bájate del vehículo para coger el tranvía.", True)
        return
    if p.j.estrellas:
        app.son("error")
        app.decir("El conductor del tranvía te reconoce y no abre las puertas.", True)
        return
    linea = linea_tranvia(p)
    corto = lambda x: x.nombre.replace("Parada de tranvía de ", "")           # noqa: E731

    def ir(dest):
        def f():
            if not p.pagar(p.precio("tranvia", PRECIO_TRANVIA)):
                return
            app.cerrar(m)
            paradas = recorrido_tranvia(p, l, dest)
            from . import transporte
            transporte.subir(p, l)                              # el tranvía que te recoge es uno de los que circulan por la línea

            def bajar(parada, cuantas):
                p.pasar_horas(0.05 * max(1, cuantas))
                p.teletransportar(parada.x, parada.y)
                transporte.bajar(p, parada)
                p.j.stats["tranvias"] = p.j.stats.get("tranvias", 0) + 1
                p.decir(f"Te bajas del tranvía en {corto(parada)}. {p.mundo.describir(parada.x, parada.y)}. Son las {p.hora_txt()}.")
            from . import pantallas
            if pantallas.con_trayecto(app):
                app.abrir(pantallas.LineaTranvia(app, paradas, bajar, corto))
            else:
                bajar(dest, len(paradas))
        return f
    otras = [x for x in linea if x is not l]
    otras.sort(key=lambda x: len(recorrido_tranvia(p, l, x)))
    ops = [Opcion(f"Ir a {corto(x)}: {len(recorrido_tranvia(p, l, x))} {'parada' if len(recorrido_tranvia(p, l, x)) == 1 else 'paradas'}, {p.precio('tranvia', PRECIO_TRANVIA)} euros", ir(x),
                  ayuda="El tranvía va parando en cada parada y la anuncia. Durante el viaje, con Intro te bajas en la próxima, aunque no sea la que habías elegido. "
                        + p.mundo.describir(x.x, x.y) + ".") for x in otras]
    m = _menu(p, l, ops or [Opcion("Esta es la única parada de la línea")],
              intro=f"El tranvía recorre {p.mundo.nombre}. Hay {len(linea)} paradas. Elige en cuál quieres bajarte")


# ------------------------------------------------------------------ tren: para ir a otras localidades por tierra
def tren(p, l):
    app = p.app
    if p.j.veh:
        app.decir(f"{l.nombre}. Bájate del vehículo para coger el tren.", True)
        return
    if p.j.estrellas:
        app.son("error")
        app.decir("En la taquilla hay un cartel con tu cara. Mejor no.", True)
        return

    def ir(dest, saltos):
        def f():
            if not p.pagar(precio(saltos)):
                return
            app.cerrar(m)

            def llegar():
                p.pasar_horas(0.5 * saltos)
                p.j.stats["trenes"] = p.j.stats.get("trenes", 0) + 1
                p.cambiar_mapa(dest.mapa, dest.x, dest.y, None, f"El tren te deja en {dest.nombre}. Son las {p.hora_txt()}.")
            from .pantallas import viajar as trayecto
            trayecto(app, min(60.0, 25.0 + 10.0 * saltos), llegar, destino=p.mapas[dest.mapa].nombre, medio="tren")
        return f

    def precio(saltos):
        return p.precio("tren_base", 10) + p.precio("tren_salto", 12) * saltos
    ops = []
    for e in sorted((x for x in p.lugares.values() if x.tipo == "tren" and x.mapa != p.mundo.id), key=lambda x: (p.saltos_por_tierra(p.mundo.id, x.mapa) or 99, x.mapa)):
        saltos = p.saltos_por_tierra(p.mundo.id, e.mapa)
        if saltos:
            ops.append(Opcion(f"Tren a {p.mapas[e.mapa].nombre}: {precio(saltos)} euros", ir(e, saltos),
                              ayuda=("Es la localidad vecina. " if saltos == 1 else f"Está a {saltos} localidades de aquí. ") + p.desc_localidad(p.mapas[e.mapa])))
    intro = "El tren llega a todas las localidades a las que se puede ir por tierra"
    if p.mundo.tren_donde():
        intro += f". La vía cruza {p.mundo.nombre} por {p.mundo.tren_donde()}: cada minuto y medio, más o menos, pasa un tren, y se le oye venir"
    m = _menu(p, l, ops or [Opcion("De esta estación no sale ningún tren")], intro=intro)


# ------------------------------------------------------------------ aeropuerto: trayectos largos, avionetas y helicópteros
ALQUILER = {"avioneta": 600, "helicoptero": 900}


def aeropuerto(p, l):
    app = p.app
    j = p.j
    if j.veh is not None and j.veh.modelo.get("vuela"):
        from . import menus_extra
        menus_extra.helipuerto(p, l)                        # llegas pilotando: vuelas tú adonde quieras
        return
    if j.veh:
        app.decir(f"{l.nombre}. Bájate del vehículo para entrar en la terminal.", True)
        return
    if j.estrellas:
        app.son("error")
        app.decir("En el control de seguridad hay dos agentes mirando una foto tuya. Vuelve cuando no te busquen.", True)
        return

    def volar(dest, medio):
        def f():
            precio = precio_de(dest, medio)
            if not p.pagar(precio):
                return
            app.cerrar(m)

            def llegar():
                p.pasar_horas({"avion": 1.0, "avioneta": 0.7, "helicoptero": 0.5}[medio])
                j.stats["vuelos"] = j.stats.get("vuelos", 0) + 1
                p.cambiar_mapa(dest.mapa, dest.x, dest.y, None, (f"Aterrizas en el {dest.nombre}." if dest.tipo == "aeropuerto" else f"Aterrizas en {dest.nombre}, {p.mapas[dest.mapa].nombre}.") + f" Son las {p.hora_txt()}.")
            from .pantallas import viajar as trayecto
            if medio == "helicoptero":
                trayecto(app, 35.0, llegar, destino=p.mapas[dest.mapa].nombre, vuelo=True)
            else:
                trayecto(app, 45.0 if medio == "avion" else 38.0, llegar, destino=p.mapas[dest.mapa].nombre, medio=medio)
        return f

    def precio_de(dest, medio):
        return int(dest.get("precio", p.precio("vuelo_avion", 180) if medio == "avion" else p.precio("vuelo_avioneta", 120) if medio == "avioneta" else p.precio("vuelo_helicoptero", 150)))

    def alquilar(modelo):
        def f():
            if any(v.modelo["id"] == modelo and not v.muerto and v.dist(l.x, l.y) < 40 and v is not j.veh for v in p.vehiculos):
                app.decir("Ya tienes uno esperando en la pista. Sal de la terminal y súbete con F.", True)
                return
            if not p.pagar(p.precio("alquiler_" + modelo, ALQUILER[modelo])):
                return
            x, y, d = p.mundo.plaza_junto_a(l)
            v = p.crear_vehiculo(modelo, x, y, d, "aparcado")
            v.cerrado = False
            v.propio = True
            p.son("llegada", cat="interfaz")
            app.cerrar(m)
            p.fijar_gps(x, y, v.nombre, auto=True, radio=4, callar=True)
            p.decir(f"Alquilado: {v.nombre}. Te espera en la pista, {p.situar(x, y, 'está')}. Súbete con F. Se pilota a mano y aterriza en cualquier aeropuerto, helipuerto o espacio abierto.")
        return f
    pequeno = bool(l.get("aerodromo"))
    ops = []
    con_pista = set()
    for a in sorted((x for x in p.lugares.values() if x.tipo == "aeropuerto" and x.mapa != p.mundo.id), key=lambda x: (bool(x.get("aerodromo")), x.mapa)):
        con_pista.add(a.mapa)
        # el avión grande solo va de aeropuerto a aeropuerto; a un aeródromo, o desde él, se va en avioneta de línea
        medio = "avioneta" if pequeno or a.get("aerodromo") else "avion"
        ops.append(Opcion(f"{'Vuelo' if medio == 'avion' else 'Avioneta de línea'} a {p.mapas[a.mapa].nombre}: {precio_de(a, medio)} euros", volar(a, medio),
                          ayuda=("Avión de pasajeros, para los trayectos largos entre ciudades. " if medio == "avion"
                                 else "Una avioneta de ocho plazas con piloto, que aterriza en las pistas cortas de los pueblos. ") + p.desc_localidad(p.mapas[a.mapa])))
    # a las islas, donde no cabe una pista, se llega en helicóptero de línea
    for h in sorted((x for x in p.lugares.values() if x.tipo == "helipuerto" and x.mapa != p.mundo.id and x.mapa not in con_pista), key=lambda x: x.mapa):
        ops.append(Opcion(f"Helicóptero de línea a {h.nombre}, en {p.mapas[h.mapa].nombre}: {precio_de(h, 'helicoptero')} euros", volar(h, "helicoptero"),
                          ayuda="Allí no hay pista: se llega en helicóptero con piloto. " + p.desc_localidad(p.mapas[h.mapa])))
    ops.append(Opcion(f"Alquilar una avioneta: {p.precio('alquiler_avioneta', ALQUILER['avioneta'])} euros", alquilar("avioneta"),
                      ayuda="Te la dejan en la pista y la pilotas tú. Más rápida que el helicóptero. Con ella puedes ir a cualquier aeropuerto, aeródromo o helipuerto pulsando Intro al llegar."))
    if not pequeno:
        ops.append(Opcion(f"Alquilar un helicóptero: {p.precio('alquiler_helicoptero', ALQUILER['helicoptero'])} euros", alquilar("helicoptero"),
                          ayuda="Te lo dejan en la pista y lo pilotas tú. Más lento que la avioneta, pero se detiene en el aire y aterriza en menos sitio."))
    from . import vuelo_pantalla
    ops += vuelo_pantalla.opciones_campo(p, l)
    m = _menu(p, l, ops, intro="Avionetas de línea a las ciudades, a los otros pueblos y helicópteros a las islas, y avionetas de alquiler" if pequeno
              else "Aviones de pasajeros a las otras ciudades, avionetas de línea a los pueblos, helicópteros a las islas, y avionetas y helicópteros de alquiler")


def _zarpar(p, l, modelo, salud=None, nombre=None, propio=None):
    j = p.j
    muelle = p.lug(l.get("a_lugar"))
    mar = p.mapas[muelle.mapa]
    x, y, d = mar.plaza_junto_a(muelle)
    p.cambiar_mapa(mar.id, x, y)
    v = p.crear_vehiculo(modelo, x, y, d, None, nombre)
    if salud is not None:
        v.salud = min(v.salud_max, float(salud))
    v.rumbo = M.rumbo_a(mar.ancho / 2 - x, mar.alto / 2 - y)
    v.propio = True
    j.barco_actual = propio
    p._subir(v, False, callar=True)
    p.son("sirena_barco", cat="interfaz", vol=0.5)
    p.decir(f"Sueltas amarras a bordo de {v.nombre} y sales a {mar.nombre}. Proa al {M.cardinal(v.rumbo)}. "
            "En el mar llevas el timón tú: izquierda y derecha giran, arriba acelera. Pulsa P para pescar, Tabulador para oír qué hay cerca y L para elegir un rumbo.")


def embarcadero(p, l):
    app = p.app
    j = p.j
    if j.veh:
        app.decir(f"{l.nombre}. Bájate del vehículo para subir a un barco.", True)
        return
    if not p.lug(l.get("a_lugar")):
        app.decir(f"{l.nombre}. {l.desc}", True)
        return

    def con_propio(k):
        def f():
            b = j.barcos.pop(k)
            app.cerrar(m)
            _zarpar(p, l, b["modelo"], b.get("salud"), b.get("nombre"), {"modelo": b["modelo"], "nombre": b.get("nombre")})
        return f

    def alquilar():
        if p.pagar(p.precio("alquiler_lancha", 60)):
            app.cerrar(m)
            _zarpar(p, l, "lancha", nombre="Lancha de alquiler")

    def robar():
        app.cerrar(m)
        p.son("ganzua", cat="interfaz")
        modelo = random.choice(["lancha", "lancha", "pesquero", "lancha_rapida"])
        if random.random() < 0.5:
            p.decir("¡Un marinero te ha visto y da la voz de alarma!")
            p.delito(2, "robo de una embarcación", siempre=True)
        p.j.stats["vehiculos_robados"] += 1
        _zarpar(p, l, modelo)

    def pescar():
        app.cerrar(m)
        p.empezar_pesca(desde_muelle=True)

    def practicas():
        app.cerrar(m)
        _zarpar(p, l, "lancha", nombre="Lancha de prácticas")

    def ops():
        lista = []
        if p.practica_de("zarpar", "timon", "atracar"):          # el tutorial de navegar presta una lancha
            lista.append(Opcion("Zarpar con la lancha de prácticas del tutorial: gratis", practicas, ayuda="Para los ejercicios del tutorial de navegar. Se devuelve sola al atracar en cualquier muelle."))
        for k, b in enumerate(j.barcos):
            if b.get("en") == l.id:
                lista.append(Opcion(f"Zarpar con tu barco: {b.get('nombre', b['modelo'])}", con_propio(k)))
        lista.append(Opcion(f"Alquilar una lancha: {p.precio('alquiler_lancha', 60)} euros", alquilar, ayuda="La lancha de alquiler se devuelve sola al atracar en cualquier muelle."))
        lista.append(Opcion("Robar una embarcación amarrada", robar, ayuda="Gratis, pero puede que te vean."))
        lista.append(Opcion("Pescar desde el muelle", pescar, ayuda="Desde tierra solo pican peces pequeños. Los grandes están mar adentro."))
        otros = [b for b in j.barcos if b.get("en") != l.id]
        for b in otros:
            e = p.lug(b.get("en"))
            lista.append(Opcion(f"Tu barco {b.get('nombre', b['modelo'])} está amarrado en {p.nombre_lugar(e) if e else 'otro puerto'}"))
        return lista
    m = _menu(p, l, ops)


def muelle(p, l):
    app = p.app
    j = p.j
    v = j.veh
    dest = p.lug(l.get("a_lugar"))
    if dest is None or v is None:
        app.decir(f"{l.nombre}. {l.desc}", True)
        return
    if abs(v.vel) > 3:
        app.decir("Reduce la velocidad para atracar.", True)
        return

    def atracar():
        app.cerrar(m)
        extra = ""
        if j.barco_actual:
            j.barcos.append({"modelo": j.barco_actual["modelo"], "nombre": j.barco_actual.get("nombre"), "salud": v.salud, "en": dest.id})
            extra = f" Tu barco queda amarrado en {dest.nombre}."
        j.barco_actual = None
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
        p.son("lugar_embarcadero", cat="interfaz")
        p.cambiar_mapa(dest.mapa, dest.x, dest.y, None, f"Atracas y saltas a tierra en {dest.nombre}, {p.mapas[dest.mapa].nombre}.{extra}")
        p.practica_evento("atracar")                             # el tutorial de navegar comprueba que has atracado de verdad
    m = _menu(p, l, [Opcion(f"Atracar y desembarcar en {p.mapas[dest.mapa].nombre}", atracar, ayuda=l.desc)])


def punto_pesca(p, l):
    if p.j.veh and p.mundo.tipo != "mar":
        p.app.decir(f"{l.nombre}. Bájate del vehículo para pescar.", True)
        return
    p.app.decir(f"{l.nombre}. {l.desc}", True)
    if not p.pesca:
        p.empezar_pesca(desde_muelle=p.mundo.tipo != "mar")


def nautica(p, l):
    app = p.app
    j = p.j
    emb = p.lug(l.get("embarcadero")) or next((e for e in p.mundo.lugares.values() if e.tipo == "embarcadero"), None)

    def comprar(mo):
        def f():
            if emb is None:
                app.decir("No hay amarre disponible.", True)
                return
            if p.pagar(int(mo["precio"])):
                j.barcos.append({"modelo": mo["id"], "nombre": mo["nombre"], "salud": mo["salud"], "en": emb.id})
                app.son("mision_ok")
                app.decir(f"¡{mo['nombre']} es tuyo! Te espera amarrado en {emb.nombre}.", True)
        return f
    ops = [Opcion(f"{mo['nombre']}: {mo['precio']} euros", comprar(mo), ayuda=mo.get("desc", "")) for mo in p.datos["vehiculos"] if mo.get("barco") and mo.get("precio")]
    _menu(p, l, ops, "F1 describe cada embarcación")


def concesionario(p, l):
    app = p.app

    def comprar(mo):
        def f():
            if p.pagar(int(mo["precio"])):
                x, y, d = p.mundo.plaza_junto_a(l)
                v = p.crear_vehiculo(mo["id"], x, y, d, None)
                v.propio = True
                app.cerrar(m)
                app.son("mision_ok")
                app.decir(f"¡{mo['nombre']} es tuyo, con papeles y todo! {p.situar(x, y, 'Te espera')}. " + ("Guárdalo en el garaje de una de tus casas." if p.en_servidor else
                          "No se pierde aunque lo dejes en la calle: lo tienes en el móvil, en Mis vehículos."), True)
                p.hacer_mio(v)
        return f
    def vender():
        app.cerrar(m)
        p.jornada_vendedor(l)

    def elegir_para_llevarse():
        """Antes te llevabas siempre el mismo, el de precio medio: ahora eliges cuál pides para «probarlo»."""
        caros = sorted((mo for mo in p.datos["vehiculos"] if mo.get("precio") and not mo.get("barco") and (not marcas or mo["id"] in marcas)), key=lambda mo: mo["precio"])
        if not caros:
            return
        if p.mision:
            app.son("error")
            app.decir("Durante una misión no te la juegas con esto.", True)
            return
        if len(caros) == 1:
            return llevarse(caros[0], caros)

        def con(mo):
            def f():
                app.cerrar(sub)
                llevarse(mo, caros)
            return f
        sub = Menu(app, "¿De cuál pides las llaves? Cuanto más caro, con más ganas te busca la policía",
                   [Opcion(f"{mo['nombre']}, que vale {mo['precio']} euros", con(mo), ayuda=mo.get("desc", "")) for mo in caros] + [Opcion("Dejarlo", lambda: app.cerrar(sub))])
        app.abrir(sub)

    def llevarse(mo, caros):
        x, y, d = p.mundo.plaza_junto_a(l)
        v = p.crear_vehiculo(mo["id"], x, y, d, None)
        app.cerrar(m)
        p.salir_interior()
        p.j.x, p.j.y = p.mundo.punto_libre(x + 3, y)
        p.son("cristal", xy=(x, y))
        puntos = 3 if caros.index(mo) <= len(caros) // 2 else 4          # los de la mitad cara del escaparate, un nivel más de búsqueda
        p.delito(puntos, f"Pides las llaves de un {mo['nombre']} para probarlo y sales con él sin pagar. Salta la alarma del concesionario.", siempre=True)
        p.j.stats["vehiculos_robados"] = p.j.stats.get("vehiculos_robados", 0) + 1
        p.cambiar_ciudadania(-2.0)
        app.decir(f"{p.situar(v.x, v.y, 'El coche está')}. Sube con F y sal de aquí.")
    marcas = l.get("modelos")
    ops = [Opcion(f"{mo['nombre']}: {mo['precio']} euros", comprar(mo), ayuda=mo.get("desc", ""))
           for mo in p.datos["vehiculos"] if mo.get("precio") and not mo.get("barco") and (not marcas or mo["id"] in marcas)]
    ops.append(Opcion(lambda: f"Trabajar aquí de vendedor[|a]: ocho horas, sueldo y comisión. Llevas {p.j.stats.get('coches_vendidos', 0)} coches vendidos", vender,
                      ayuda="Una jornada atendiendo clientes. Cobras un sueldo fijo y una comisión por cada coche que vendas: vendes más cuanto mejor sea tu labia y tu prestigio entre los vecinos. Una jornada al día."))
    ops.append(Opcion("Pedir las llaves para una prueba y no volver", elegir_para_llevarse,
                      ayuda="Te llevas un coche de exposición sin pagarlo: eliges cuál. Es un robo a la vista de todos: salta la alarma y la policía sale a por ti con fuerza, más cuanto más caro sea."))
    m = _menu(p, l, ops, "F1 describe cada vehículo")


# ======================================================================= dinero
def banco(p, l):
    app = p.app
    j = p.j

    def mover(n, ingresar):
        def f():
            cant = (j.dinero if ingresar else j.banco) if n is None else n
            if cant <= 0 or cant > (j.dinero if ingresar else j.banco):
                app.son("error")
                app.decir("No tienes tanto.", True)
                return
            if ingresar:
                j.dinero -= cant
                j.banco += cant
            else:
                j.dinero += cant
                j.banco -= cant
            p.son("caja", cat="interfaz")
            app.decir(f"Hecho. En la cuenta hay {j.banco} euros y llevas encima {j.dinero}.", True)
        return f
    def atracar(plan=None):
        if p.mision or p.trabajo:
            app.son("error")
            app.decir("Termina antes lo que tienes entre manos.", True)
        elif p.arma()["tipo"] not in ("fuego", "explosivo"):
            app.son("error")
            app.decir("Para atracar un banco tienes que empuñar un arma de fuego.", True)
        elif p.atracadas.get("banco:" + l.id) == p.dia:
            app.son("error")
            app.decir("La cámara acorazada está vacía y llena de policías: ya lo atracaste hoy.", True)
        else:
            p.empezar_atraco_banco(l, plan)
            return True
        return False

    def preparar_golpe():
        from . import golpes
        golpes.preparar(p, l, atracar, "el golpe al banco")
    ops = [Opcion(lambda: f"Saldo de tu cuenta: {j.banco} euros", ayuda="El dinero del banco no se pierde si te detienen o acabas en el hospital, y da un pequeño interés cada día."),
           Opcion("Ingresar todo el efectivo", mover(None, True)), Opcion("Ingresar 1000 euros", mover(1000, True)),
           Opcion("Retirar 1000 euros", mover(1000, False)), Opcion("Retirar todo", mover(None, False)),
           Opcion("Bolsa: comprar y vender acciones", lambda: __import__("juego.menus_extra", fromlist=["x"]).bolsa(p), ayuda="Cinco empresas de la comarca. Los precios cambian cada medianoche."),
           Opcion("Atracar el banco", lambda: atracar(), ayuda="Necesitas un arma de fuego. Cinco vigilantes, un botín enorme y cuatro niveles de búsqueda. Una vez al día por banco.")]
    if j.banda and not p.en_servidor:
        from .atracos import AYUDA_GOLPE, TEXTO_GOLPE
        ops.append(Opcion(TEXTO_GOLPE, preparar_golpe, ayuda=AYUDA_GOLPE))
    if not p.en_servidor:
        from . import menus_honrado as mh
        ops.insert(6, Opcion(lambda: "Créditos, hipotecas y obligaciones. " + mh.banco_txt(p), lambda: mh.menu_banco(p, l),
                             ayuda="Pedir un crédito personal, ver tus cuotas y liquidarlas, y consultar lo que te van a cobrar de facturas e impuestos. "
                                   "Lo que te prestan depende de tu prestigio, de tus ingresos estables y de tus antecedentes."))
    _menu(p, l, ops)


def loteria(p, l):
    from . import loteria as lot
    m = _menu(p, l, lambda: lot.opciones_venta(p, l, lambda: m.refrescar(False)),
              intro="Administración de lotería. El sorteo es cada día a las nueve de la noche")


def empenos(p, l):
    app = p.app
    j = p.j

    def vender(a):
        def f():
            precio = int(a["precio"] * 0.4)
            del j.armas[a["id"]]
            if j.arma == a["id"]:
                j.arma = "punos"
            p.dar_dinero(precio)
            m.refrescar(False)
            app.decir(f"Vendes {a['nombre']} por {precio} euros.", True)
        return f

    def ops():
        from .menus_juego import armas_en_venta
        lista = [Opcion(f"Vender {a['nombre']} por {int(a['precio'] * 0.4)} euros", vender(a)) for a in p.datos["armas"] if a["id"] in j.armas and a["precio"] > 0]
        venta = armas_en_venta(p, l)                              # lo que el prestamista tiene de segunda mano
        return venta + (lista or [Opcion("No tienes nada que le interese al prestamista")])
    m = _menu(p, l, ops)


def pescaderia(p, l):
    app = p.app
    j = p.j

    def vender():
        if not j.pescado:
            app.decir("No traes pescado. Sal al mar en barco y pulsa P para pescar.", True)
            return
        total = sum(x["valor"] for x in j.pescado)
        n = len(j.pescado)
        j.pescado = []
        p.dar_dinero(total)
        app.decir(f"Vendes {n} capturas por {total} euros.", True)
    _menu(p, l, [Opcion(lambda: f"Vender tu pesca: {len(j.pescado)} capturas por {sum(x['valor'] for x in j.pescado)} euros", vender),
                 Opcion(lambda: "Tus capturas: " + (", ".join(x["nombre"] for x in j.pescado) or "ninguna"))])


# ========================================================================= ocio
def gimnasio(p, l):
    j = p.j

    def entrenar():
        if j.gimnasio_dia == p.dia:
            p.app.decir("Ya has entrenado hoy. Tienes agujetas hasta en las pestañas.", True)
        elif j.salud_max >= 150:
            p.app.decir("Estás en tu mejor forma. Ya no puedes mejorar más.", True)
        elif p.pagar(p.precio("gimnasio", 60)):
            j.gimnasio_dia = p.dia
            j.salud_max = min(150.0, j.salud_max + 5)
            j.salud = j.salud_max
            p.pasar_horas(2)
            p.son("lugar_gimnasio", cat="interfaz")
            p.app.decir(f"Dos horas de pesas y saco. Tu salud máxima sube a {int(j.salud_max)}.", True)
    def combate(c):
        def f():
            if p.mision or p.trabajo:
                p.app.son("error")
                p.app.decir("Termina antes lo que tienes entre manos.", True)
            elif p.pagar(int(c.get("inscripcion", 0))):
                p.empezar_combate(l, c)
        return f
    _menu(p, l, [Opcion(lambda: f"Entrenar dos horas: {p.precio('gimnasio', 60)} euros. Salud máxima actual {int(j.salud_max)}", entrenar, ayuda="Cada entrenamiento sube cinco puntos tu salud máxima, hasta 150. Uno al día.")] +
          [Opcion((lambda c=c: f"{c['nombre']}: inscripción de {c.get('inscripcion', 0)} euros. Llevas {j.stats.get(c['id'], 0)} victorias"), combate(c), ayuda=c.get("ayuda", ""))
           for c in p.datos.get("combates", [])])


def ropa(p, l):
    j = p.j
    prendas = [(x["nombre"], int(x.get("precio", 0))) for x in p.datos.get("prendas", [])]
    blindajes = {x["nombre"]: int(x["blindaje"]) for x in p.datos.get("prendas", []) if x.get("blindaje")}

    def comprar(nombre, precio):
        def f():
            if not p.pagar(precio):
                return
            j.ropa = nombre.lower()
            p.son("caja", cat="interfaz")
            txt = f"Sales con {nombre.lower()}."
            tope = blindajes.get(nombre)
            if tope and j.blindaje < tope:
                j.blindaje = float(tope)
                txt += f" Lleva refuerzos: blindaje {tope}."
            if 0 < j.estrellas <= 2 and not _policia_cerca(p, 70):
                p._fin_persecucion()
                txt += " Con este aspecto nuevo, la policía ya no te reconoce."
            p.app.decir(txt, True)
        return f
    def complemento(clase, nombre, precio, animo):
        def f():
            if j.accesorios.get(clase) == nombre:
                p.app.decir(f"Ya llevas {nombre.lower()}.", True)
                return
            if not p.pagar(precio):
                return
            j.accesorios[clase] = nombre
            p.son("caja", cat="interfaz")
            p.cambiar_animo(animo)
            p.app.decir(f"Te pones {nombre.lower()}. Te sienta bien. {p.aspecto_txt()}", True)
        return f

    def quitar():
        if not j.accesorios:
            p.app.decir("No llevas ningún complemento.", True)
            return
        j.accesorios.clear()
        p.app.decir("Te quitas todos los complementos y los guardas en casa.", True)

    def complementos():
        ops2 = [Opcion((lambda c=c, n=n, pr=pr: f"{n}: {pr} euros" + (". Lo llevas puesto" if j.accesorios.get(c) == n else "")), complemento(c, n, pr, an),
                       ayuda="Se lleva encima además de la ropa. De cada clase llevas uno: si compras otro, sustituye al que tenías. "
                             "Estrenar algo sube el ánimo, más cuanto más caro, y la gente con la que hablas lo nota.")
                for c, n, pr, an in ((x.get("clase", "otros"), x["nombre"], int(x.get("precio", 0)), int(x.get("animo", 0))) for x in p.datos.get("complementos", []))]
        ops2.append(Opcion("Quitarte todos los complementos", quitar))
        ops2.append(Opcion(lambda: p.aspecto_txt()))
        _menu(p, l, ops2)

    ops = [Opcion(f"{n}: {pr} euros", comprar(n, pr), ayuda="Cambiarte de ropa despista a la policía si tienes uno o dos niveles de búsqueda y no hay agentes cerca."
                  + (f" Además lleva refuerzos: te deja el blindaje en {blindajes[n]} si llevabas menos." if n in blindajes else "")) for n, pr in prendas]
    ops.append(Opcion("Complementos: gafas, cadenas, anillos, relojes y gorras", complementos, ayuda="Para ir a la moda. Se llevan además de la ropa."))
    ops.append(Opcion(lambda: p.aspecto_txt()))
    _menu(p, l, ops)


def cine(p, l):
    def ver():
        if p.pagar(p.precio("cine", 12)):
            p.pasar_horas(2)
            p.j.salud = min(p.j.salud_max, p.j.salud + 10)
            p.son("lugar_cine", cat="interfaz")
            p.app.decir(f"Hoy ponen {random.choice(PELICULAS)} Sales dos horas después, a las {p.hora_txt()}.", True)
    _menu(p, l, [Opcion(f"Ver la película de hoy: {p.precio('cine', 12)} euros", ver)])


def hotel(p, l):
    j = p.j

    def dormir():
        if j.estrellas:
            p.app.son("error")
            p.app.decir("El recepcionista no admite huéspedes con la policía detrás.", True)
        elif p.pagar(int(l.get("precio_noche", p.precio("hotel_noche", 70)))):
            p.pasar_horas(8, dormir=True)
            j.salud = j.salud_max
            p.ha_duchado()                                       # la habitación tiene ducha
            p.ha_bebido(100)
            p.son("pasan_horas", cat="interfaz")
            p.app.decir(f"Duermes ocho horas en una cama estupenda. Salud al máximo. Son las {p.hora_txt()} del día {p.dia}.", True)
    _menu(p, l, [Opcion(f"Pasar la noche: {int(l.get('precio_noche', p.precio('hotel_noche', 70)))} euros", dormir)])


def taberna(p, l):
    app = p.app
    j = p.j

    def beber():
        if p.pagar(p.precio("cana_tapa", 4)):
            p.ha_bebido(50)
            j.salud = min(j.salud_max, j.salud + 10)
            p.son("comer", cat="interfaz")
            app.decir(f"Una caña y una tapa. Salud {int(j.salud)}.", True)

    def dados(apuesta):
        def f():
            if not p.pagar(apuesta):
                return
            p.son("dados", cat="interfaz")
            yo = random.randint(1, 6) + random.randint(1, 6)
            casa = random.randint(1, 6) + random.randint(1, 6)
            if yo > casa:
                p.dar_dinero(apuesta * 2)
                txt = f"Sacas {yo} contra {casa}. ¡Ganas {apuesta} euros!"
            elif yo == casa:
                j.dinero += apuesta
                txt = f"Empate a {yo}. Recuperas la apuesta."
            else:
                txt = f"Sacas {yo} contra {casa}. Pierdes {apuesta} euros."
            app.decir(txt + f" Tienes {j.dinero}.", True)
        return f

    def contratar():
        n = sum(1 for e in p.personas if e.tipo == "aliado" and not e.muerto)
        if n >= 2:
            app.decir("Ya llevas dos guardaespaldas. Más sería un desfile.", True)
        elif p.pagar(int(p.precio("guardaespaldas_taberna", 300) * p.hon_fama_factor())):
            p.crear_aliado()
            app.decir(f"Un tipo enorme deja la cerveza y se levanta. Desde ahora te sigue y dispara a quien te ataque. Cobra {p.precio('guardaespaldas_sueldo', 200)} euros cada medianoche.", True)

    def contrato():
        if p.mision or p.trabajo:
            app.son("error")
            app.decir("Termina antes lo que tienes entre manos.", True)
        else:
            from . import contratos
            contratos.menu_contratos(p, l)

    def despedir():
        n = sum(1 for e in p.personas if e.tipo == "aliado")
        p.personas = [e for e in p.personas if e.tipo != "aliado"]
        app.decir("Despides a tus guardaespaldas." if n else "No tienes guardaespaldas.", True)
    ops = ([Opcion(f"Tomar una copa: {p.precio('copa_bar', 6)} euros", lambda: p.consumir("alcohol", de_inventario=False) if p.pagar(p.precio("copa_bar", 6)) else None, ayuda="Alcohol: sube el ánimo, pero caminas torcido y apuntas peor.")] if p.modo_adulto() else []) + \
          [Opcion(f"Tomar una caña con tapa: {p.precio('cana_tapa', 4)} euros", beber), Opcion("Jugar a los dados: 20 euros", dados(20)), Opcion("Jugar a los dados: 200 euros", dados(200)),
           Opcion(lambda: f"Contratar un guardaespaldas: {int(p.precio('guardaespaldas_taberna', 300) * p.hon_fama_factor())} euros", contratar, ayuda="Te sigue a pie, sube contigo a los vehículos y dispara a tus enemigos. Máximo dos."),
           Opcion("Despedir a los guardaespaldas", despedir),
           Opcion("Tablón de encargos: ver los contratos de hoy", contrato, ayuda="Tres encargos para elegir, cada uno de una manera: quitar de en medio a alguien con sus guardaespaldas, cazar a uno que huye en coche, "
                  "entrar a buscarle a un local, seguir a su recadero hasta la guarida, dar un escarmiento sin matar, recuperar algo robado o proteger a alguien. Cada contrato cumplido hace los siguientes más difíciles y mejor pagados.")]
    from . import loteria as lot
    ops.append(lot.opcion_en_local(p, l))
    _menu(p, l, ops)
