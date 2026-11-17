"""Menús de la elección de personaje y de la vida honrada: oficina de empleo, academias y voluntariado."""
from . import genero
from .menus import EntradaTexto, Menu, Opcion
from .trabajos import NOMBRE_TRABAJO
from .vida import HAB_NOMBRE, MAX_NIVEL, MAX_NOMBRE, PUNTOS, RANGOS, VENTAJAS, limpiar_nombre, personaje_propio

DONDE = {"taxi": "un taxi", "ambulancia": "una ambulancia", "autobus": "un autobús", "vigilante": "un coche patrulla", "camion": "un camión",
         "helados": "una furgoneta de helados", "bomberos": "un camión de bomberos", "grua": "una grúa", "paqueteria": "una bicicleta, un scooter o una moto",
         "mensajeria": "cualquier barco, ya en el mar"}


TRATO = {"h": "en masculino", "m": "en femenino"}
AYUDA_TRATO = ("Cambia cómo te hablan los demás y cómo te habla el juego: bienvenido o bienvenida, el sobrino o la sobrina de Encarna. "
               "La historia y todo lo demás son iguales.")


def elegir_genero(app, al_elegir, quien=""):
    """Pregunta cómo hay que tratar al protagonista y llama a al_elegir con "h" o "m"."""
    def con(g):
        def f():
            app.cerrar(m)
            al_elegir(g)
        return f
    ops = [Opcion("En masculino", con("h"), ayuda="Te hablan como a un hombre: bienvenido, el sobrino de Encarna, hijo."),
           Opcion("En femenino", con("m"), ayuda="Te hablan como a una mujer: bienvenida, la sobrina de Encarna, hija."),
           Opcion("Volver", lambda: app.cerrar(m))]
    m = Menu(app, f"¿Cómo quieres que te hablen{' con ' + quien if quien else ''}?", ops, intro=AYUDA_TRATO)
    app.abrir(m)


def elegir_personaje(app):
    datos = app.datos.get("personajes", [])

    def con(pj):
        def f():
            if pj.get("genero") in genero.GENEROS:           # los personajes de algunos mods ya dicen si son él o ella
                app.empezar_partida(None, personaje=pj["id"])
            else:
                elegir_genero(app, lambda g: app.empezar_partida(None, personaje={"id": pj["id"], "genero": g}), pj["nombre"])
        return f
    ops = [Opcion(f"{pj['nombre']} {pj.get('apellido', '')}".strip() + f". {pj.get('desc', '')}", con(pj),
                  ayuda=None if pj.get("genero") in genero.GENEROS else "Después eliges si te hablan en masculino o en femenino.") for pj in datos]
    ops.append(Opcion("Crear tu propio personaje", lambda: crear_personaje(app),
                      ayuda="Le pones nombre y apellido, eliges si te hablan en masculino o en femenino, repartes ocho niveles entre las cuatro habilidades y escoges con qué empiezas."))
    ops.append(Opcion("Volver", lambda: app.cerrar(m)))
    m = Menu(app, "Elige tu personaje", ops, intro="La historia es la misma para todos; cambian las ventajas con las que empiezas. La última opción te deja crear el tuyo")
    app.abrir(m)


AYUDA_HAB = {"conduccion": "Con más nivel el vehículo corre algo más y se daña menos en los golpes.",
             "punteria": "Con más nivel aciertas más a menudo.",
             "resistencia": "Con más nivel corres más deprisa y te hacen algo menos de daño.",
             "pesca": "Con más nivel pican antes y el pescado vale más."}


def crear_personaje(app):
    """El jugador se hace su protagonista: nombre, apellido, cómo le hablan, las habilidades y con qué empieza."""
    from . import vozgen
    e = {"nombre": "", "apellido": "", "genero": "h", "niveles": {h: 0 for h in HAB_NOMBRE}, "ventaja": 0, "voz": 0, "dicho": ""}

    def voz(d):
        e["voz"] = (e["voz"] + d) % len(vozgen.VOCES_PROTA)

    def oir_nombre():
        if not e["nombre"]:
            app.son("error")
            return app.decir("Primero pon el nombre.", True)
        quien = vozgen.reparto()["personajes"].get("Encarna")
        pj = vozgen.Personaje(e["nombre"], e["apellido"], e["genero"], vozgen.VOCES_PROTA[e["voz"]], e["dicho"])
        vozgen.probar(app, quien, pj.texto("¡Dani! ¡Pero mírate! Te lo dije: Dani Roca siempre vuelve."))

    def oir_voz():
        pj = vozgen.Personaje(e["nombre"] or "Dani", e["apellido"], e["genero"], vozgen.VOCES_PROTA[e["voz"]], e["dicho"])
        archivo = vozgen.reparto()["protagonista"].get(f"{pj.voz}_{pj.genero}")
        vozgen.probar(app, archivo, pj.texto("Me llamo Dani Roca. He salido esta mañana y no tengo ni para un café."))

    def quedan():
        return PUNTOS - sum(e["niveles"].values())

    def pedir(campo, titulo):
        def hecho(t):
            limpio = limpiar_nombre(t)
            if t.strip() and not limpio:
                app.son("error")
                app.decir("Ahí solo valen letras, espacios y guiones.", True)
                return
            e[campo] = limpio
            m.refrescar(False)
            app.decir(f"{titulo}: {limpio or 'sin poner'}.", True)
        return lambda: app.abrir(EntradaTexto(app, titulo, hecho, inicial=e[campo], maximo=MAX_NOMBRE,
                                              ayuda=f"Hasta {MAX_NOMBRE} letras. Lo que escribas aquí no se anota en el registro del juego."))

    def trato(d):
        e["genero"] = "m" if e["genero"] == "h" else "h"

    def nivel(h):
        def f(d):
            n = e["niveles"][h] + d
            if n < 0 or n > MAX_NIVEL or (d > 0 and quedan() <= 0):
                app.son("menu_borde")
                return
            e["niveles"][h] = n
        return f

    def ventaja(d):
        e["ventaja"] = (e["ventaja"] + d) % len(VENTAJAS)

    def empezar():
        if not e["nombre"]:
            app.son("error")
            app.decir("Falta el nombre. Es la primera opción.", True)
            return
        aviso = quedan()
        pj = personaje_propio(e["nombre"], e["apellido"], e["genero"], e["niveles"], VENTAJAS[e["ventaja"]][0], vozgen.VOCES_PROTA[e["voz"]], e["dicho"])
        if aviso > 0 and not e.get("avisado"):
            e["avisado"] = True
            app.son("menu_borde")
            app.decir(f"Te quedan {aviso} niveles de habilidad sin repartir. Pulsa Intro otra vez para empezar así, o repártelos antes.", True)
            return
        if app.cfg["voces_grabadas"] and app.cfg["voces_propias"] and not app.pruebas and vozgen.disponible():
            quien = vozgen.Personaje(pj["nombre"], pj["apellido"], pj["genero"], pj["voz"], pj["dicho"])
            app.abrir(vozgen.Preparando(app, quien, app.datos.get("misiones", []), lambda: app.empezar_partida(None, personaje=pj)))
            return
        app.empezar_partida(None, personaje=pj)

    def ops():
        # los textos son funciones: cambian al tocar las flechas, sin rehacer el menú
        lista = [Opcion(lambda: f"Nombre: {e['nombre'] or 'sin poner'}", pedir("nombre", "Nombre"), ayuda="Intro para escribirlo. Así te llamarán en la historia."),
                 Opcion(lambda: f"Apellido: {e['apellido'] or 'sin poner'}", pedir("apellido", "Apellido"), ayuda="Intro para escribirlo. Puedes dejarlo vacío."),
                 Opcion(lambda: f"Te hablan {TRATO[e['genero']]}", ajuste=trato, ayuda=AYUDA_TRATO + " Izquierda, derecha o Intro para cambiar."),
                 Opcion(lambda: f"Tu voz en las escenas: {vozgen.NOMBRE_VOZ[vozgen.VOCES_PROTA[e['voz']]]}, {TRATO[e['genero']]}", ajuste=voz,
                        ayuda="La voz con la que hablas tú en las escenas de la historia. Hay cuatro de hombre y cuatro de mujer; suena la que corresponde a cómo te hablan. Izquierda y derecha para cambiar.")]
        if vozgen.disponible():
            lista += [Opcion(lambda: f"Cómo se pronuncia tu nombre: {e['dicho'] or 'igual que se escribe'}", pedir("dicho", "Cómo se pronuncia tu nombre"),
                             ayuda="Si al escuchar tu nombre no suena bien, escríbelo aquí como se pronuncia, por ejemplo Yónatan en vez de Jonathan. En pantalla y en braille sigue saliendo como lo escribiste arriba. Puedes dejarlo vacío."),
                      Opcion("Escuchar cómo te llamarán", oir_nombre, ayuda="Genera una frase con tu nombre, dicha por un personaje de la historia. Tarda un momento."),
                      Opcion("Escuchar tu voz", oir_voz, ayuda="Genera una frase dicha por ti, con la voz elegida. Tarda un momento.")]
        for h, nombre in HAB_NOMBRE.items():
            lista.append(Opcion((lambda h=h, nombre=nombre: f"{nombre.capitalize()}: nivel {e['niveles'][h]}. Quedan {quedan()} por repartir"), ajuste=nivel(h),
                                ayuda=f"{AYUDA_HAB.get(h, '')} Derecha sube e izquierda baja. Tienes {PUNTOS} niveles para repartir y como mucho {MAX_NIVEL} en cada habilidad. "
                                      "Después se sigue subiendo con la práctica y en las academias, hasta el diez."))
        lista.append(Opcion(lambda: f"Ventaja de salida: {VENTAJAS[e['ventaja']][1]}. {VENTAJAS[e['ventaja']][2]}", ajuste=ventaja, ayuda="Izquierda y derecha para ver las demás. Solo puedes llevarte una."))
        lista.append(Opcion("Empezar la partida", empezar, ayuda="Empieza la historia con el personaje tal como está."))
        lista.append(Opcion("Volver", lambda: app.cerrar(m)))
        return lista
    m = Menu(app, "Crea tu personaje", ops, intro="Arriba y abajo para recorrer los datos. Intro para escribir el nombre; izquierda y derecha para cambiar lo demás")
    app.abrir(m)


def _menu(p, l, ops, intro=None):
    m = Menu(p.app, lambda: f"{l.nombre}. Tienes {p.j.dinero} euros", ops + [Opcion("Volver", lambda: p.app.cerrar(m))], intro=intro)
    p.app.abrir(m)
    return m


def empleo(p, l):
    app = p.app

    def buscar(tipo):
        def f():
            if tipo == "mensajeria":
                app.decir("Para la mensajería del mar, zarpa en cualquier barco desde un embarcadero y pulsa J.", True)
                return
            donde = p.vehiculo_de_trabajo_cercano(tipo)
            if donde is None:
                app.decir(f"En esta localidad no hay ningún sitio fijo donde encontrar {DONDE[tipo]}. Tendrás que comprarlo, o tomarlo prestado.", True)
                return
            while len(app.pila) > 1 and app.pila[-1] is not p:
                app.pila.pop()
            app.teclas.clear()
            p.salir_interior()
            p.gps_a_lugar(donde)
            p.decir(f"Hay {DONDE[tipo]} aparcado junto a {donde.nombre}. Sube con F y pulsa J para empezar a trabajar.")
        return f
    ops = [Opcion(f"{nombre}: ocho horas, unos {int(paga * p.mult_trabajo('jornada'))} euros", (lambda c=clave, n=nombre, pg=paga, s=salud: p.jornada(c, n, pg, s)),
                  ayuda="Trabajo sin vehículo: pasan ocho horas y cobras. Una jornada al día. Sube tu prestigio entre los vecinos.") for clave, nombre, paga, salud in ((x["id"], x["nombre"], int(x.get("paga", 0)), float(x.get("salud", 0))) for x in p.datos.get("jornadas", []))]
    for tipo, nombre in NOMBRE_TRABAJO.items():
        ops.append(Opcion(f"Oficio de {nombre}: eres {RANGOS[p.rango(tipo)]}, con {p.servicios_de(tipo)} servicios. Se hace con {DONDE.get(tipo, 'su vehículo')}", buscar(tipo),
                          ayuda="Intro marca en el GPS dónde hay un vehículo de ese oficio. Cada ocho servicios asciendes y cobras un doce por ciento más."))
    ops.append(Opcion(lambda: f"En el barrio, {p.ciudadania_txt()}", ayuda="El prestigio sube con el trabajo honrado, los cursos, los donativos y ayudando en los sucesos. Baja con los delitos. Con buen prestigio cobras más y la policía es más comprensiva."))
    _menu(p, l, ops, "Aquí están todos los trabajos honrados del juego")


def academia(p, l):
    cursos = [h for h in (l.get("cursos") or list(HAB_NOMBRE)) if h in HAB_NOMBRE]
    ops = [Opcion((lambda h=h: f"Curso de {HAB_NOMBRE[h]}: {p.precio('curso', 250)} euros y cuatro horas. Tu nivel es {p.nivel(h)} de 10"), (lambda h=h: p.curso(h)),
                  ayuda="Sube la habilidad mucho más deprisa que la práctica. Un curso al día.") for h in cursos]
    if p.normas_activas():
        from . import realismo as R
        ops.append(Opcion(lambda: f"Curso de recuperación de puntos del carné: {int(R.aj('precio_carne'))} euros y cuatro horas." + p.carne_txt(), p.recuperar_carne,
                          ayuda=f"Devuelve {int(R.aj('puntos_curso'))} puntos, hasta el tope de {int(R.aj('puntos_carne'))}. Si te lo han retirado, con el curso vuelves a tenerlo."))
    _menu(p, l, ops)


def ong(p, l):
    ops = [Opcion("Donar 50 euros", lambda: p.donar(50)), Opcion("Donar 500 euros", lambda: p.donar(500)),
           Opcion("Hacer voluntariado cuatro horas", p.voluntariado, ayuda="No cobras nada, pero sube mucho tu ánimo y tu prestigio entre los vecinos. Una vez al día."),
           Opcion(lambda: f"En el barrio, {p.ciudadania_txt()}")]
    _menu(p, l, ops)


def carrera(p):
    """Resumen de tu vida: la honrada y la otra."""
    app = p.app
    j = p.j
    s = j.stats
    lineas = [f"{j.nombre} {j.apellido}".strip() + f". Día {p.dia}",
              f"Entre los vecinos, {p.ciudadania_txt()}. En la calle, {p.reputacion_txt()}. Tu ánimo es {p.animo_txt()}",
              f"Misiones completadas: {len(p.completadas)}. Dinero: {j.dinero} euros en mano y {j.banco} en el banco"]
    hechos = [(t, n) for t, n in NOMBRE_TRABAJO.items() if p.servicios_de(t)]
    for t, n in hechos:
        lineas.append(f"Vida honrada. {n.capitalize()} {RANGOS[p.rango(t)]}: {p.servicios_de(t)} servicios")
    lineas.append(f"Vida honrada. Jornadas trabajadas: {p.servicios_de('jornada')}. Voluntariado: {s.get('voluntariado', 0)} veces. Donado: {s.get('donado', 0)} euros. Sucesos resueltos: {s.get('eventos', 0)}")
    lineas.append(f"Vida delictiva. Vehículos robados: {s['vehiculos_robados']}. Contratos: {s.get('contratos', 0)}. Atracos a bancos: {s.get('atracos', 0)}. Territorios: {len(j.territorios)}. Detenciones: {s['detenciones']}")
    if p.modo_adulto():
        lineas.append(f"Vida delictiva. Mercancía vendida por valor de {s.get('vendido', 0)} euros")
    app.abrir(Menu(app, "Tu carrera", [Opcion(t) for t in lineas] + [Opcion("Volver", lambda: app.cerrar())]))
