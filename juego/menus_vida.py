"""Menús de la elección de personaje y de la vida honrada: oficina de empleo, academias y voluntariado."""
from .menus import Menu, Opcion
from .trabajos import NOMBRE_TRABAJO
from .vida import HAB_NOMBRE, JORNADAS, RANGOS

DONDE = {"taxi": "un taxi", "ambulancia": "una ambulancia", "autobus": "un autobús", "vigilante": "un coche patrulla", "camion": "un camión",
         "helados": "una furgoneta de helados", "bomberos": "un camión de bomberos", "grua": "una grúa", "paqueteria": "una bicicleta, un scooter o una moto",
         "mensajeria": "cualquier barco, ya en el mar"}


def elegir_personaje(app):
    datos = app.datos.get("personajes", [])
    if len(datos) <= 1:
        app.empezar_partida(None, personaje=datos[0]["id"] if datos else None)
        return
    ops = [Opcion(f"{pj['nombre']} {pj['apellido']}. {pj['desc']}", (lambda pj=pj: app.empezar_partida(None, personaje=pj["id"]))) for pj in datos]
    ops.append(Opcion("Volver", lambda: app.cerrar(m)))
    m = Menu(app, "Elige tu personaje", ops, intro="La historia es la misma para todos; cambian las ventajas con las que empiezas")
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
                  ayuda="Trabajo sin vehículo: pasan ocho horas y cobras. Una jornada al día. Sube tu prestigio entre los vecinos.") for clave, nombre, paga, salud in JORNADAS]
    for tipo, nombre in NOMBRE_TRABAJO.items():
        ops.append(Opcion(f"Oficio de {nombre}: eres {RANGOS[p.rango(tipo)]}, con {p.servicios_de(tipo)} servicios. Se hace con {DONDE.get(tipo, 'su vehículo')}", buscar(tipo),
                          ayuda="Intro marca en el GPS dónde hay un vehículo de ese oficio. Cada ocho servicios asciendes y cobras un doce por ciento más."))
    ops.append(Opcion(lambda: f"En el barrio, {p.ciudadania_txt()}", ayuda="El prestigio sube con el trabajo honrado, los cursos, los donativos y ayudando en los sucesos. Baja con los delitos. Con buen prestigio cobras más y la policía es más comprensiva."))
    _menu(p, l, ops, "Aquí están todos los trabajos honrados del juego")


def academia(p, l):
    cursos = [h for h in (l.get("cursos") or list(HAB_NOMBRE)) if h in HAB_NOMBRE]
    ops = [Opcion((lambda h=h: f"Curso de {HAB_NOMBRE[h]}: 250 euros y cuatro horas. Tu nivel es {p.nivel(h)} de 10"), (lambda h=h: p.curso(h)),
                  ayuda="Sube la habilidad mucho más deprisa que la práctica. Un curso al día.") for h in cursos]
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
    lineas = [f"{j.nombre} {j.apellido}. Día {p.dia}",
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
