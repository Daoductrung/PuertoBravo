"""Menús de la segunda ampliación: helipuertos, ruleta, marcadores, servicios, habilidades y logros."""
import math
import random

from . import mundo as M
from .extras2 import HABILIDADES, LOGROS
from .menus import Menu, Opcion

ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


# ==================================================================== helipuerto
def helipuerto(p, l):
    app = p.app
    j = p.j
    volando = j.veh is not None and j.veh.modelo.get("vuela")
    if j.veh and not volando:
        app.decir(f"{l.nombre}. Bájate del vehículo: aquí solo despegan helicópteros.", True)
        return
    if j.estrellas and not volando:
        app.son("error")
        app.decir("El piloto no despega con la policía buscándote.", True)
        return
    destinos = [h for h in p.lugares.values() if h.tipo in ("helipuerto", "aeropuerto") and h.id != l.id and h.mapa != p.mundo.id]
    if not volando:
        con_heli = {h.mapa for h in destinos if h.tipo == "helipuerto"}
        # de pasajero, el helicóptero va a los helipuertos y, donde no hay, a la pista del aeródromo del pueblo
        destinos = [h for h in destinos if h.tipo == "helipuerto" or (h.get("aerodromo") and h.mapa not in con_heli)]

    def volar(h):
        def f():
            precio = 0 if volando else int(h.get("precio", 150))
            if precio and not p.pagar(precio):
                return
            _volver_al_juego(p)

            def llegar():
                p.pasar_horas(0.4)
                p.son("motor_helicoptero", cat="interfaz", vol=0.6)
                p.cambiar_mapa(h.mapa, h.x, h.y, None,
                               f"{'Aterrizas' if not volando else 'Llegas volando'} en {h.nombre}, {p.mapas[h.mapa].nombre}. Son las {p.hora_txt()}.")
            if volando:
                llegar()                                 # pilotas tú: no hay trayecto de pasajero
            else:
                from .pantallas import viajar as trayecto
                trayecto(app, 35.0, llegar, destino=p.mapas[h.mapa].nombre, vuelo=True)
        return f
    ops = [Opcion(f"Volar a {h.nombre}, en {p.mapas[h.mapa].nombre}" + ("" if volando else f": {int(h.get('precio', 150))} euros"), volar(h),
                  ayuda=p.mapas[h.mapa].barrios[0].get("descripcion", "")) for h in destinos]
    intro = "Vas en tu helicóptero: el vuelo es gratis" if volando else "Vuelos en helicóptero con piloto"
    app.abrir(Menu(app, lambda: f"{l.nombre}. Tienes {j.dinero} euros", ops, intro=intro))


# ======================================================================== ruleta
def ruleta(p):
    app = p.app

    def jugar(nombre, gana, pago, apuesta):
        def f():
            if not p.pagar(apuesta):
                return
            n = random.randint(0, 36)
            p.son("ruleta", cat="interfaz")
            color = "verde" if n == 0 else "rojo" if n in ROJOS else "negro"
            txt = f"Sale el {n}, {color}. "
            if gana(n):
                premio = apuesta * (pago + 1)
                p.dar_dinero(premio)
                txt += f"¡Ganas {apuesta * pago} euros!"
            else:
                txt += f"Pierdes {apuesta} euros."
            app.decir(txt + f" Tienes {p.j.dinero}.", True)
        return f

    def mesa(apuesta):
        ops = [Opcion("Apostar al rojo, paga el doble", jugar("rojo", lambda n: n in ROJOS, 1, apuesta)),
               Opcion("Apostar al negro, paga el doble", jugar("negro", lambda n: n != 0 and n not in ROJOS, 1, apuesta)),
               Opcion("Apostar a par, paga el doble", jugar("par", lambda n: n != 0 and n % 2 == 0, 1, apuesta)),
               Opcion("Apostar a impar, paga el doble", jugar("impar", lambda n: n % 2 == 1, 1, apuesta)),
               Opcion("Apostar a la primera docena, paga el triple", jugar("d1", lambda n: 1 <= n <= 12, 2, apuesta)),
               Opcion("Apostar a la segunda docena, paga el triple", jugar("d2", lambda n: 13 <= n <= 24, 2, apuesta)),
               Opcion("Apostar a la tercera docena, paga el triple", jugar("d3", lambda n: 25 <= n <= 36, 2, apuesta)),
               Opcion("Pleno al 7, paga treinta y cinco a uno", jugar("7", lambda n: n == 7, 35, apuesta)),
               Opcion("Pleno al 17, paga treinta y cinco a uno", jugar("17", lambda n: n == 17, 35, apuesta)),
               Opcion("Pleno al 0, paga treinta y cinco a uno", jugar("0", lambda n: n == 0, 35, apuesta))]
        app.abrir(Menu(app, lambda: f"Ruleta, fichas de {apuesta} euros. Tienes {p.j.dinero}", ops))
    app.abrir(Menu(app, "Ruleta. Elige el valor de la ficha", [Opcion(f"Fichas de {a} euros", (lambda a=a: mesa(a))) for a in (10, 100, 1000)]))


# ==================================================================== marcadores
def marcadores(p):
    app = p.app
    j = p.j

    def guardar():
        x, y = p.pos()
        n = len(j.marcadores) + 1
        nombre = f"Marcador {n}: {p.mundo.describir(x, y)}"
        j.marcadores.append({"nombre": nombre, "mapa": p.mundo.id, "x": x, "y": y})
        app.son("guardado")
        m.refrescar(False)
        app.decir(f"Guardado: {nombre}.", True)

    def ir(k):
        def f():
            mk = j.marcadores[k]
            if mk["mapa"] != p.mundo.id:
                app.son("error")
                app.decir(f"Ese marcador está en {p.mapas[mk['mapa']].nombre}. Viaja primero allí.", True)
                return
            _volver_al_juego(p)
            p.fijar_gps(mk["x"], mk["y"], mk["nombre"], radio=6)
        return f

    def borrar():
        if not j.marcadores:
            app.decir("No hay marcadores.", True)
            return
        j.marcadores.pop()
        m.refrescar(False)
        app.decir("Último marcador borrado.", True)

    def ops():
        lista = [Opcion("Guardar un marcador en mi posición actual", guardar, ayuda="Recuerda este punto exacto para volver luego con el GPS.")]
        for k, mk in enumerate(j.marcadores):
            donde = "" if mk["mapa"] == p.mundo.id else f", en {p.mapas[mk['mapa']].nombre}"
            lista.append(Opcion(f"Ir a {mk['nombre']}{donde}", ir(k)))
        lista.append(Opcion("Borrar el último marcador", borrar))
        return lista
    m = Menu(app, "Marcadores personales", ops)
    app.abrir(m)


# ===================================================================== servicios
def servicios(p):
    app = p.app
    j = p.j

    def traer(pid, k):
        def f():
            if p.mundo.tipo in ("mar",):
                app.decir("En mitad del mar no te pueden traer un coche.", True)
                return
            if not p.pagar(150):
                return
            d = j.garajes[pid].pop(k)
            x, y, di = p.plaza_cercana()
            v = p.crear_vehiculo(d["modelo"], x, y, di, None, d.get("nombre"))
            from . import sistemas
            sistemas.poner(v, d.get("mejoras"))
            v.salud = min(v.salud_max, float(d.get("salud", v.salud_max)))
            v.propio = True
            _volver_al_juego(p)
            p.son("claxon", xy=(x, y))
            p.decir(f"Tu mecánico te deja {v.nombre} en la calle. {p.situar(x, y, 'Está')}.", True)
        return f

    def vehiculos():
        ops = []
        for pid, lista in j.garajes.items():
            l = p.lug(pid)
            for k, d in enumerate(lista):
                ops.append(Opcion(f"{d.get('nombre', d['modelo'])}, guardado en {p.nombre_lugar(l) if l else 'un garaje'}: 150 euros", traer(pid, k)))
        app.abrir(Menu(app, "Que te traigan un vehículo", ops or [Opcion("No tienes vehículos guardados en ningún garaje")]))

    def al_garaje():
        """Que se lleven a un garaje tuyo el vehículo que llevas o el que acabas de dejar."""
        v = j.veh or p.tu_vehiculo(120)
        if v is None:
            app.son("error")
            app.decir("No tienes ningún vehículo aquí. Tiene que ser el que llevas o el que acabas de dejar aparcado cerca.", True)
            return
        if v.tag or v.modelo.get("barco") or p.mundo.tipo == "mar":
            app.son("error")
            app.decir("Ese vehículo no se puede guardar en un garaje.", True)
            return

        def llevar(l):
            def f():
                g = j.garajes.setdefault(l.id, [])
                if len(g) >= int(l.get("garaje", 0)):
                    app.son("error")
                    app.decir("Ese garaje está lleno.", True)
                    return
                if v.muerto or not p.pagar(100):
                    return
                g.append({"modelo": v.modelo["id"], "salud": v.salud, "nombre": v.nombre, "mejoras": dict(getattr(v, "mejoras", {}))})
                if j.veh is v:
                    p.salir_vehiculo(forzado=True)
                p.quitar_vehiculo(v)
                p.ultimo_veh = None
                _volver_al_juego(p)
                p.son("arranque", vol=0.6)
                p.decir(f"Tu mecánico se lleva {v.nombre} al garaje de {p.nombre_lugar(l)}." + (" Te quedas a pie." if not j.veh else ""), True)
            return f
        casas = [l for l in (p.lug(pid) for pid in j.propiedades) if l is not None and int(l.get("garaje", 0)) > 0]
        ops = [Opcion(f"{p.nombre_lugar(l)}: {len(j.garajes.get(l.id, []))} de {l.get('garaje', 0)} plazas ocupadas", llevar(l)) for l in casas]
        app.abrir(Menu(app, f"Mandar {v.nombre} a un garaje: 100 euros", ops or [Opcion("No tienes ninguna casa con garaje")]))

    def guardaespaldas():
        n = sum(1 for e in p.personas if e.tipo == "aliado" and not e.muerto and not getattr(e, "de_banda", False))      # los de tu banda no cuentan
        if n >= 2:
            app.decir("Ya llevas dos guardaespaldas.", True)
        elif p.pagar(350):
            p.crear_aliado()
            app.decir("Un guardaespaldas llega en un minuto y se pone a tu lado. Cobra 200 euros cada medianoche.", True)

    def ambulancia():
        x, y = p.pos()
        if any(e.hostil and not e.muerto and e.activo and e.dist(x, y) < 45 for e in p.personas):
            app.son("error")
            app.decir("La ambulancia no entra mientras haya tiros. Aléjate de los enemigos.", True)
        elif j.salud >= j.salud_max:
            app.decir("No tienes heridas.", True)
        elif p.pagar(200):
            j.salud = j.salud_max
            p.son("sirena_ambulancia", cat="interfaz", vol=0.4)
            p.son("curar", cat="interfaz")
            app.decir("Los sanitarios te atienden en el sitio. Salud al máximo.", True)
    def taxi():
        from . import menus_juego
        if j.estrellas or p.mision:
            app.son("error")
            app.decir("Ahora mismo ningún taxista quiere llevarte.", True)
        else:
            _volver_al_juego(p)
            menus_juego.menu_viaje(p)
    def despedir():
        n = 0
        for e in list(p.personas):
            if e.tipo == "aliado" and not e.muerto and not getattr(e, "de_banda", False):
                p.personas.remove(e)
                n += 1
        app.decir(f"Despides a {'tu guardaespaldas' if n == 1 else f'tus {n} guardaespaldas'}. Ya no te cobrarán." if n else "No llevas guardaespaldas.", True)

    app.abrir(Menu(app, lambda: f"Servicios por teléfono. Tienes {j.dinero} euros", [
        Opcion("Que te traigan un vehículo de tus garajes: 150 euros", vehiculos),
        Opcion("Mandar tu vehículo a uno de tus garajes: 100 euros", al_garaje,
               ayuda="Tu mecánico se lleva el vehículo que llevas, o el que acabas de dejar aparcado cerca, al garaje de la casa que elijas. Vale para casas de cualquier localidad."),
        Opcion("Llamar a un guardaespaldas: 350 euros", guardaespaldas),
        Opcion(lambda: f"Despedir a tus guardaespaldas: llevas {sum(1 for e in p.personas if e.tipo == 'aliado' and not e.muerto and not getattr(e, 'de_banda', False))}", despedir,
               ayuda="Se marchan y dejan de cobrarte los 200 euros de cada medianoche."),
        Opcion("Pedir una ambulancia: 200 euros", ambulancia),
        Opcion("Pedir un taxi: viaje rápido", taxi)]))


# ========================================================= habilidades y logros
def progreso(p):
    app = p.app
    j = p.j

    def habilidades():
        ops = []
        for h, (nombre, desc) in HABILIDADES.items():
            ops.append(Opcion(f"{nombre}: nivel {p.nivel(h)} de 10", ayuda=desc))
        ops.append(Opcion(f"Salud máxima: {int(j.salud_max)} de 150. Se sube entrenando en un gimnasio"))
        app.abrir(Menu(app, "Habilidades", ops, intro="Mejoran solas con la práctica. F1 explica cada una"))

    def logros():
        ops = []
        for ident, nombre, desc, _ in LOGROS:
            ops.append(Opcion(f"{nombre}: {'conseguido' if ident in j.logros else 'pendiente'}. {desc}"))
        app.abrir(Menu(app, f"Logros: {len(j.logros)} de {len(LOGROS)}", ops))
    app.abrir(Menu(app, "Habilidades y logros", [Opcion("Habilidades", habilidades), Opcion(lambda: f"Logros: {len(j.logros)} de {len(LOGROS)}", logros)]))


# =================================================================== protectora
def protectora(p, l):
    from .extras3 import NOMBRES_PERRO
    app = p.app
    j = p.j

    def adoptar(nombre):
        def f():
            if p.pagar(200):
                j.perro = nombre
                j.perro_hambre, j.perro_confianza = 0.0, 100.0
                p.crear_perro()
                _volver_al_juego(p)
                p.son("ladrido")
                p.decir(f"{nombre} sale moviendo el rabo y ya no se separa de ti. Gruñe cuando hay peligro cerca y, a pie, con la tecla Y, "
                        "busca por el olfato el objeto más cercano y te marca el camino.", True)
        return f

    def dejar():
        d = p.perro()
        if d in p.personas:
            p.personas.remove(d)
        nombre = j.perro
        j.perro = ""
        j.perro_en_casa = False
        j.perro_hambre, j.perro_confianza = 0.0, 100.0
        app.cerrar()
        app.decir(f"Dejas a {nombre} en la protectora. Aquí lo cuidarán bien.", True)
    pienso = __import__("juego.menus_juego", fromlist=["x"])._comprar_objeto(p, "pienso")
    if j.perro:
        ops = [Opcion(lambda: p.perro_txt()), pienso, Opcion(f"Cómo está y qué necesita {j.perro}", lambda: menu_perro(p)), Opcion(f"Dejar a {j.perro} en la protectora", dejar)]
    else:
        ops = [Opcion(f"Adoptar a {n}: 200 euros de donativo", adoptar(n), ayuda="Un perro te acompaña a todas partes, avisa de los enemigos y encuentra objetos por el olfato.") for n in random.sample(NOMBRES_PERRO, 4)]
    app.abrir(Menu(app, lambda: f"{l.nombre}. Tienes {j.dinero} euros", ops))


def menu_perro(p):
    """Tu perro: cómo está, acariciarlo, darle de comer, mandarlo a casa o llamarlo. Se abre con Mayúsculas Y, o con Intro a su lado."""
    app = p.app
    j = p.j
    if not j.perro:
        app.decir("No tienes perro. Puedes adoptar uno en una protectora de animales.", True)
        return

    def volver_y(f):
        def g():
            if f():
                while app.pila and app.pila[-1] is not p:
                    app.cerrar(app.pila[-1])
        return g

    def buscar():
        while app.pila and app.pila[-1] is not p:
            app.cerrar(app.pila[-1])
        p.perro_busca()

    def ops():
        if j.perro_en_casa:
            return [Opcion(p.perro_txt()), Opcion(f"Llamar a {j.perro} para que vuelva contigo", volver_y(p.llamar_perro), ayuda="Llega corriendo desde casa. En mitad del mar no puede.")]
        if p.perro() is None:
            return [Opcion(f"{j.perro} no está aquí ahora mismo: vuelve contigo en cuanto pises tierra")]
        return [Opcion(p.perro_txt(), ayuda="Con hambre avisa gimiendo, y sin fuerzas no busca. Si te tiene miedo, te sigue de lejos y no avisa de los enemigos ni busca."),
                Opcion("Acariciar", lambda: (p.acariciar_perro(), m.refrescar(False)), ayuda="Le sube la confianza poco a poco. Si le has hecho daño, así hacéis las paces."),
                Opcion(lambda: f"Dar de comer: te quedan {j.objetos.get('pienso', 0)} raciones de pienso", lambda: (p.alimentar_perro(), m.refrescar(False)),
                       ayuda="Una ración le quita el hambre de casi un día y le sube mucho la confianza. El pienso se compra en la protectora de animales y en las tiendas."),
                Opcion("Buscar por el olfato el objeto más cercano", buscar, ayuda="Lo mismo que la tecla Y."),
                Opcion("Mandar a casa", volver_y(p.mandar_perro_a_casa), ayuda="Se va a tu vivienda y te espera allí, con comida y agua. Hace falta tener una casa. Para que vuelva, lo llamas desde este mismo menú.")]
    m = Menu(app, f"Tu perro, {j.perro}", ops)
    app.abrir(m)


# ======================================================================== feria
def feria(p, l):
    app = p.app

    def simon():
        if p.pagar(10):
            from .pantallas import SimonSonoro
            _volver_al_juego(p)
            app.abrir(SimonSonoro(app, p))

    def tiro():
        if p.pagar(20):
            from .pantallas import TiroAlBlanco
            _volver_al_juego(p)
            app.abrir(TiroAlBlanco(app, p))

    def algodon():
        if p.pagar(3):
            p.j.salud = min(p.j.salud_max, p.j.salud + 6)
            p.son("comer", cat="interfaz")
            app.decir(f"Algodón de azúcar. Salud {int(p.j.salud)}.", True)
    app.abrir(Menu(app, lambda: f"{l.nombre}. Tienes {p.j.dinero} euros", [
        Opcion("Máquina de memoria de sonidos: 10 euros", simon, ayuda="La máquina toca una secuencia de notas y tú la repites con las flechas. Con cinco rondas ya hay premio; con doce, mil euros."),
        Opcion("Caseta de tiro: 20 euros", tiro),
        Opcion("Algodón de azúcar: 3 euros", algodon),
        Opcion(lambda: f"Tu récord en la máquina de memoria: {p.j.stats.get('simon', 0)} rondas")]))


# ======================================================================= tesoro
def tesoro(p, l):
    app = p.app
    j = p.j
    buceo = p.mundo.tipo == "mar"
    if buceo and j.veh and abs(j.veh.vel) > 1.5:
        app.decir("Detén el barco antes de bucear.", True)
        return
    if not buceo and j.veh:
        app.decir(f"{l.nombre}. Bájate del vehículo.", True)
        return
    clave = "tesoro:" + l.id
    hechos = p.atracadas.get(clave, [0, 0])
    if hechos[0] != p.dia:
        hechos = [p.dia, 0]

    def buscar():
        if hechos[1] >= 3:
            app.son("error")
            app.decir("Hoy ya has removido todo esto tres veces. Vuelve mañana.", True)
            return
        if p.pagar(25):
            hechos[1] += 1
            p.atracadas[clave] = hechos
            from .pantallas import BuscaTesoro
            _volver_al_juego(p)
            app.abrir(BuscaTesoro(app, p, buceo))
    que = "Alquilar botellas y bucear: 25 euros" if buceo else "Alquilar un detector de metales: 25 euros"
    app.abrir(Menu(app, lambda: f"{l.nombre}. Tienes {j.dinero} euros", [
        Opcion(que, buscar, ayuda="Un juego de frío o caliente con el oído. El pitido se acelera y se agudiza al acercarte al tesoro. Tres búsquedas al día en cada sitio."),
        Opcion("Descripción", lambda: app.decir(l.desc, True)),
        Opcion(lambda: f"Tesoros encontrados: {j.stats.get('tesoros', 0)}")]))


# ======================================================================== bolsa
def bolsa(p):
    from .extras3 import EMPRESAS
    app = p.app
    j = p.j

    def operar(ident):
        nombre, _, desc = EMPRESAS[ident]

        def comprar(n):
            def f():
                precio = int(round(p.precio_accion(ident) * n))
                if p.pagar(precio):
                    j.acciones[ident] = j.acciones.get(ident, 0) + n
                    p.son("bolsa", cat="interfaz")
                    app.decir(f"Compras {n} acciones por {precio} euros. Tienes {j.acciones[ident]}.", True)
            return f

        def vender(n):
            def f():
                tengo = j.acciones.get(ident, 0)
                k = tengo if n is None else min(n, tengo)
                if k <= 0:
                    app.son("error")
                    app.decir("No tienes acciones de esta empresa.", True)
                    return
                cobro = int(p.precio_accion(ident) * k)
                j.acciones[ident] = tengo - k
                p.dar_dinero(cobro)
                app.decir(f"Vendes {k} acciones por {cobro} euros. Te quedan {j.acciones[ident]}.", True)
            return f
        app.abrir(Menu(app, lambda: f"{nombre}. Precio {p.precio_accion(ident):.2f} euros. Tienes {j.acciones.get(ident, 0)} acciones y {j.dinero} euros", [
            Opcion("Comprar 10 acciones", comprar(10)), Opcion("Comprar 100 acciones", comprar(100)),
            Opcion("Vender 10 acciones", vender(10)), Opcion("Vender todas", vender(None)),
            Opcion(desc)]))
    ops = [Opcion((lambda i=i: f"{EMPRESAS[i][0]}: {p.precio_accion(i):.2f} euros la acción. Tienes {j.acciones.get(i, 0)}"), (lambda i=i: operar(i)), ayuda=EMPRESAS[i][2]) for i in EMPRESAS]
    app.abrir(Menu(app, "Bolsa de la comarca", ops, intro="Los precios cambian cada medianoche, y algunos reaccionan a lo que pasa en la historia"))


# ================================================================== territorios
def territorios(p):
    app = p.app
    j = p.j

    def conquistar(b):
        def f():
            if p.mision or p.trabajo:
                app.son("error")
                app.decir("Termina antes lo que tienes entre manos.", True)
            elif j.estrellas:
                app.son("error")
                app.decir("Con la policía detrás no es momento de empezar una guerra.", True)
            else:
                p.empezar_conquista(b)
        return f
    ops = []
    for b in p.mundo.barrios if p.mundo.tipo == "ciudad" else []:
        if b["id"] in j.territorios:
            ops.append(Opcion(f"{b['nombre']}: es tuyo. Te da 300 euros al día"))
        else:
            ops.append(Opcion(f"Conquistar {b['nombre']}", conquistar(b), ayuda="Tres oleadas de pandilleros, cada una más dura. Si ganas, el barrio te paga 300 euros cada medianoche."))
    if not ops:
        ops = [Opcion("Aquí no hay barrios que conquistar. Las guerras de territorio son cosa de las ciudades: Puerto Bravo, San Lucero y Monteferro")]
    ops.append(Opcion(lambda: f"Territorios en tu poder: {len(j.territorios)}"))
    from . import sistemas
    ops[0:0] = sistemas.opciones_sucesos(p, Menu, Opcion)
    from .menus import EntradaTexto
    ops.append(Opcion(lambda: f"Tu banda: {j.banda_nombre or 'sin nombre'}, {j.banda} de {sistemas.cupo(j)}" if j.territorios else "Tu banda: necesitas un territorio para tenerla",
                      lambda: sistemas.menu_banda(p, Menu, Opcion, EntradaTexto),
                      ayuda="Con un territorio puedes reclutar gente. Te siguen, suben a tu vehículo y pelean a tu lado. Cada territorio te deja mantener a uno más."))
    app.abrir(Menu(app, f"Territorios de {p.mundo.nombre}", ops))


# ======================================================================== mando
def opciones_mando(app):
    from .mando import ACCIONES, ORDEN_BOTONES
    md = app.mando
    cfg = app.cfg

    def vib(d):
        cfg["mando_vibracion"] = not cfg["mando_vibracion"]
        if cfg["mando_vibracion"]:
            md.vibrar(0.7, 0.7, 300)

    def fuerza(d):
        cfg["vibracion_fuerza"] = round(max(0.2, min(1.0, cfg["vibracion_fuerza"] + 0.2 * (d or 1))), 1)
        md.vibrar(0.7, 0.7, 300)

    def probar():
        if not md.conectado:
            app.decir("No hay ningún mando conectado.", True)
        else:
            md.vibrar(1.0, 0.0, 350)
            app.decir("Vibración de prueba. Si no notas nada, tu mando no la admite o está desactivada.", True)

    def reasignar(ctx, titulo):
        def elegir(b):
            def f():
                def poner(a):
                    def g():
                        md.mapa[ctx][b] = a
                        md.guardar_mapa()
                        app.cerrar()
                        app.decir(f"{md.nombre_boton(b).capitalize()}: {ACCIONES[a][0]}.", True)
                    return g
                app.abrir(Menu(app, f"Acción para {md.nombre_boton(b)}", [Opcion(ACCIONES[a][0].capitalize(), poner(a)) for a in ACCIONES],
                               intro="Elige qué hará este botón"))
            return f
        app.abrir(Menu(app, titulo, lambda: [Opcion(f"{md.nombre_boton(b).capitalize()}: {ACCIONES[md.mapa[ctx].get(b, 'nada')][0]}", elegir(b)) for b in ORDEN_BOTONES],
                       intro="Pulsa Intro sobre un botón para cambiar lo que hace"))

    def restablecer():
        md.restablecer()
        app.decir("Botones restablecidos a su asignación original.", True)

    def ayuda_mando():
        app.abrir(Menu(app, "Qué hace cada botón del mando", [Opcion(t) for t in md.lineas_ayuda()]))

    def tipo(d):
        md.tipo = "ps" if md.tipo == "xbox" else "xbox"
    estado = (lambda: f"Mando conectado: {md.nombre}" if md.ctrl is not None else "No hay ningún mando conectado. Conéctalo por cable o Bluetooth y se detecta solo")
    app.abrir(Menu(app, "Mando", [
        Opcion(estado),
        Opcion("Qué hace cada botón", ayuda_mando),
        Opcion(lambda: f"Fuerza de la vibración: {int(cfg['vibracion_fuerza'] * 100)} por ciento", ajuste=fuerza,
               ayuda="Izquierda y derecha la bajan y la suben, del veinte al cien por cien. Cada cambio hace vibrar el mando para que la notes."),
        Opcion(lambda: f"Decir los botones del mando en lugar de las teclas: {'sí' if cfg['mando_textos'] else 'no'}",
               ajuste=lambda d: cfg.__setitem__("mando_textos", not cfg["mando_textos"]),
               ayuda="Con un mando conectado, lo que el juego cuenta mientras juegas y lo que explican los tutoriales y las escenas nombra el botón que hace cada cosa: "
                     "pulsa el gatillo izquierdo, en vez de pulsa Q. Lo que no tiene botón se sigue diciendo con su tecla. Sin mando conectado no cambia nada. "
                     "Las frases que cambian las lee tu lector de pantalla, no la voz grabada."),
        Opcion(lambda: f"Vibración: {'sí' if cfg['mando_vibracion'] else 'no'}", ajuste=vib, ayuda="El mando vibra con los golpes, los disparos que recibes, las explosiones y cuando pica un pez."),
        Opcion("Probar la vibración", probar),
        Opcion(lambda: f"Nombres de los botones: {'PlayStation' if md.tipo == 'ps' else 'Xbox'}", ajuste=tipo, ayuda="Se detecta solo al conectar el mando, pero puedes cambiarlo a mano."),
        Opcion("Reasignar los botones a pie", lambda: reasignar("pie", "Botones a pie")),
        Opcion("Reasignar los botones al volante", lambda: reasignar("coche", "Botones al volante")),
        Opcion("Restablecer los botones originales", restablecer)], al_cerrar=cfg.guardar))
