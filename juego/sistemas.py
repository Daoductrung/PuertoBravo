"""Tres sistemas de juego: mejoras de vehículos, banda propia e interior recorrible de las casas.

- Mejoras: en cualquier taller se mejora el vehículo que traigas, en motor, frenos y blindaje, con tres niveles
  cada una. Van con ese vehículo: se conservan al guardarlo en un garaje y al pedir que te lo traigan.
- Banda propia: quien tiene al menos un territorio puede ponerle nombre a su banda y reclutar gente. Cobran un
  sueldo cada medianoche y acuden cuando los llamas.
- Interior de las casas: en una casa tuya puedes recorrer las habitaciones y hacer en cada una lo suyo.
"""
import random

import pygame

from .entidades import Persona

# ============================================================ mejoras de vehículos
# Lo que puede hacer una mejora, y cuánto da cada nivel de serie, en tanto por ciento. Cada mejora de los datos dice cuál
# de estos efectos tiene, cuántos niveles y cuánto da cada uno: así un mod puede poner las suyas.
EFECTOS = {
    "motor": 7.0,          # más velocidad punta y más aceleración; el motor suena más agudo
    "frenos": 15.0,        # frena en menos metros
    "blindaje": 25.0,      # más resistencia
    "neumaticos": 25.0,    # frena mejor con lluvia, pincha menos y rueda con menos ruido
    "suspension": 15.0,    # los choques hacen menos daño
    "escape": 30.0,        # el motor suena más bajo y la policía te oye de menos lejos
    "deposito": 30.0,      # caben más litros
}
_SERIE = (("motor", "Motor", 900, "Más velocidad punta y más aceleración. Se oye: el motor suena más agudo."),
          ("frenos", "Frenos", 500, "Frena en menos metros."),
          ("blindaje", "Blindaje", 700, "Aguanta más golpes y más disparos."))
NIVEL_MAX = 3                     # los niveles de una mejora que no diga los suyos
MEJORAS = {}                      # identificador -> {"nombre", "precio", "desc", "efecto", "niveles", "por_nivel"}


def _mejora(ident, nombre, precio_, desc, efecto=None, niveles=None, por_nivel=None):
    efecto = efecto if efecto in EFECTOS else (ident if ident in EFECTOS else "")
    try:
        niveles = max(1, min(5, int(niveles or NIVEL_MAX)))
    except (TypeError, ValueError):
        niveles = NIVEL_MAX
    try:
        por_nivel = max(0.0, min(100.0, float(por_nivel if por_nivel not in (None, "") else EFECTOS.get(efecto, 0.0))))
    except (TypeError, ValueError):
        por_nivel = EFECTOS.get(efecto, 0.0)
    return {"nombre": str(nombre or ident), "precio": int(precio_ or 0), "desc": str(desc or ""), "efecto": efecto, "niveles": niveles, "por_nivel": por_nivel}


for _m in _SERIE:
    MEJORAS[_m[0]] = _mejora(*_m)


def configurar(datos):
    """Las mejoras del taller y los muebles de la casa salen de los datos del juego (vida.json), que un mod puede cambiar.
    Cada mejora dice su nombre, su precio, cuántos niveles tiene, qué efecto hace de los que el juego sabe hacer y cuánto
    da cada nivel. Una mejora sin efecto se puede comprar y se describe, pero no cambia nada. Lo que hace cada mueble lo
    decide su identificador, aquí en el código."""
    mej = [m for m in datos.get("mejoras", []) if isinstance(m, dict) and m.get("id")]
    MEJORAS.clear()
    for m in mej:
        serie = next((x for x in _SERIE if x[0] == m["id"]), (m["id"], m["id"], 0, ""))
        MEJORAS[str(m["id"])] = _mejora(m["id"], m.get("nombre") or serie[1], m.get("precio", serie[2]) or serie[2], m.get("desc") or serie[3],
                                         m.get("efecto"), m.get("niveles"), m.get("por_nivel"))
    for x in _SERIE:                                           # las tres de siempre no faltan nunca
        MEJORAS.setdefault(x[0], _mejora(*x))
    mue = [m for m in datos.get("muebles", []) if isinstance(m, dict) and m.get("id") and m.get("habitacion")]
    if mue:
        MUEBLES[:] = [(m["id"], m["habitacion"], str(m.get("nombre", m["id"])), int(m.get("precio", 0) or 0), str(m.get("desc", "")), str(m.get("efecto", "")))
                      for m in mue]


def nivel(v, cual):
    return int(getattr(v, "mejoras", {}).get(cual, 0))


def niveles(cual):
    """Cuántos niveles tiene una mejora."""
    return MEJORAS[cual]["niveles"] if cual in MEJORAS else NIVEL_MAX


def precio(v, cual):
    return MEJORAS[cual]["precio"] * (nivel(v, cual) + 1)


def efecto(v, cual):
    """Cuánto lleva ganado un vehículo en un efecto, en tanto por uno: la suma de sus mejoras con ese efecto."""
    return sum(n * MEJORAS[k]["por_nivel"] / 100.0 for k, n in getattr(v, "mejoras", {}).items() if n and k in MEJORAS and MEJORAS[k]["efecto"] == cual)


def factor_velocidad(v):
    return 1.0 + efecto(v, "motor")


def factor_aceleracion(v):
    return 1.0 + efecto(v, "motor") * 12.0 / 7.0


def factor_frenada(v):
    return 1.0 + efecto(v, "frenos")


def factor_tono(v):
    return 1.0 + efecto(v, "motor") * 4.0 / 7.0


def factor_blindaje(v):
    return 1.0 + efecto(v, "blindaje")


def factor_lluvia(v):
    """Lo que frena con lluvia respecto a en seco: 0,6 con ruedas corrientes; con neumáticos reforzados, casi como en seco."""
    return 0.6 + 0.4 * min(1.0, efecto(v, "neumaticos"))


def factor_pinchazo(v):
    """Cuánto pincha respecto a unas ruedas corrientes."""
    return max(0.1, 1.0 - efecto(v, "neumaticos"))


def factor_rodadura(v):
    """(volumen, tono) del ruido de las ruedas: unos neumáticos mejores ruedan más bajo y más graves."""
    e = min(1.0, efecto(v, "neumaticos"))
    return 1.0 - 0.45 * e, 1.0 - 0.18 * e


def factor_golpes(v):
    """El daño que le hace un choque respecto a un vehículo de serie."""
    return max(0.2, 1.0 - efecto(v, "suspension"))


def factor_motor_volumen(v):
    """A qué volumen suena el motor respecto a uno de serie."""
    return max(0.3, 1.0 - efecto(v, "escape"))


def factor_oido_policia(v):
    """Desde cuánto te oye la policía respecto a un vehículo de serie: con el escape silenciado, de menos lejos."""
    return max(0.6, 1.0 - 0.5 * efecto(v, "escape"))


def factor_deposito(v):
    return 1.0 + efecto(v, "deposito")


def poner(v, mejoras):
    """Deja el vehículo con las mejoras dadas (al comprarlas o al sacarlo de un garaje)."""
    mejoras = {k: max(0, min(niveles(k), int(n))) for k, n in dict(mejoras or {}).items() if k in MEJORAS}
    antes = factor_blindaje(v)
    v.mejoras = mejoras
    base = float(v.modelo["salud"])
    nueva = base * factor_blindaje(v)
    if nueva != v.salud_max:
        v.salud = min(nueva, v.salud + max(0.0, nueva - base * antes))
        v.salud_max = nueva


def resumen(v):
    partes = [f"{MEJORAS[k]['nombre'].lower()} nivel {n}" for k, n in getattr(v, "mejoras", {}).items() if n and k in MEJORAS]
    return "Mejoras: " + ", ".join(partes) if partes else "Sin mejoras"


def opciones_taller(p, v, Opcion):
    """Las opciones de mejora que se añaden al menú del taller."""
    app = p.app

    def comprar(cual):
        def f():
            n = nivel(v, cual)
            if v.tag:
                app.son("error")
                app.decir("Ese vehículo es de una misión: no se puede tocar.", True)
            elif n >= niveles(cual):
                app.decir(f"{MEJORAS[cual]['nombre']} ya está al máximo.", True)
            elif p.pagar(precio(v, cual)):
                m = dict(getattr(v, "mejoras", {}))
                m[cual] = n + 1
                poner(v, m)
                p.son("reparar", cat="interfaz")
                if v.canal and v is p.j.veh:                     # el escape nuevo se oye ya: el motor baja de volumen
                    v.canal.volumen(0.42 * factor_motor_volumen(v))
                app.decir(f"{MEJORAS[cual]['nombre']} mejorado al nivel {n + 1} de {niveles(cual)}. {resumen(v)}.", True)
        return f

    def texto(cual):
        def f():
            n = nivel(v, cual)
            return f"Mejorar {MEJORAS[cual]['nombre'].lower()}: nivel {n} de {niveles(cual)}" + (f". Subir cuesta {precio(v, cual)} euros" if n < niveles(cual) else ". Al máximo")
        return f
    return [Opcion(texto(k), comprar(k), ayuda=MEJORAS[k]["desc"] + " Las mejoras van con este vehículo: se conservan en el garaje.") for k in MEJORAS]


# ============================================================ banda propia
PRECIO_RECLUTA = 400
SUELDO = 60
TOPE_BANDA = 6


def cupo(j):
    """Cuánta gente puede tener la banda: uno más por cada territorio, hasta seis. Sin territorios, no hay banda."""
    return min(TOPE_BANDA, len(j.territorios) + 1) if j.territorios else 0


def miembros_presentes(p):
    return [e for e in p.personas if e.tipo == "aliado" and getattr(e, "de_banda", False) and not e.muerto]


def reclutar(p):
    j = p.j
    if not j.territorios:
        return False, "Para tener banda necesitas un territorio. Conquista un barrio primero."
    if j.banda >= cupo(j):
        return False, f"Con {len(j.territorios)} territorios no puedes mantener a más de {cupo(j)}. Conquista otro barrio."
    if not p.pagar(p.precio("recluta", PRECIO_RECLUTA)):
        return False, ""
    j.banda += 1
    if not j.banda_nombre:
        from . import gente
        j.banda_nombre = random.choice(gente.lista("bandas_propias"))
    p.son("pareja", cat="interfaz", vol=0.5)
    return True, f"Uno más en {j.banda_nombre}. Ya sois {j.banda} además de ti. Cada uno cobra {p.precio('sueldo_banda', SUELDO)} euros cada medianoche."


def llamar(p):
    """Acuden los de la banda que no estén ya contigo. Devuelve cuántos llegan y la frase."""
    j = p.j
    if not j.banda:
        return 0, "No tienes a nadie en la banda todavía."
    if j.veh and p.mundo.tipo == "mar":
        return 0, "En mitad del mar no pueden llegar hasta ti."
    faltan = j.banda - len(miembros_presentes(p))
    if faltan <= 0:
        return 0, "Ya está toda tu gente contigo."
    for _ in range(faltan):
        a = p.crear_aliado()
        a.nombre = f"Uno de {j.banda_nombre}"
        a.salud = 95.0
        a.arma = random.choice(["pistola", "pistola", "bate", "navaja"])
        a.de_banda = True
    p.son("notificacion", cat="interfaz", vol=0.5)
    return faltan, f"{'Llega' if faltan == 1 else 'Llegan'} {faltan} de {j.banda_nombre} y se {'pone' if faltan == 1 else 'ponen'} a tu lado."


def despedir(p):
    for a in miembros_presentes(p):
        p.personas.remove(a)
    return "Tu gente se dispersa. Vuelven cuando los llames."


def paga(p):
    """Cada medianoche: sueldo de la banda. Si no hay dinero, se va uno."""
    j = p.j
    if not j.banda:
        return
    if not j.territorios:
        j.banda = 0
        despedir(p)
        p.decir("Te has quedado sin territorios y tu banda se ha disuelto.")
        return
    j.banda = min(j.banda, cupo(j))
    total = p.precio("sueldo_banda", SUELDO) * j.banda
    if j.dinero >= total:
        j.dinero -= total
        p.decir(f"Pagas {total} euros a {j.banda_nombre}.")
    else:
        j.banda -= 1
        p.decir(f"No te llega para pagar a {j.banda_nombre}. Uno se marcha. Quedan {j.banda}.")


def menu_banda(p, Menu, Opcion, EntradaTexto):
    app = p.app
    j = p.j

    def nombrar():
        def hecho(t):
            t = " ".join(t.split())[:30]
            if t:
                j.banda_nombre = t
                app.decir(f"Tu banda se llama ahora {t}.", True)
        app.abrir(EntradaTexto(app, "Nombre de tu banda", hecho, maximo=30, ayuda="Así la llamarán en la calle."))

    def hacer(f):
        def g():
            r = f(p)
            texto = r[1] if isinstance(r, tuple) else r
            if isinstance(r, tuple) and r[0] is False and texto:
                app.son("error")
            if texto:
                app.decir(texto, True)
        return g
    m = Menu(app, lambda: f"Tu banda: {j.banda_nombre or 'sin nombre'}. {j.banda} de {cupo(j)}", [
        Opcion(lambda: f"Reclutar a alguien: {p.precio('recluta', PRECIO_RECLUTA)} euros. Tienes {j.dinero}", hacer(reclutar),
               ayuda=f"Cada territorio te deja mantener a uno más, hasta {TOPE_BANDA}. Cada miembro cobra {p.precio('sueldo_banda', SUELDO)} euros cada medianoche; si no puedes pagar, se va uno."),
        Opcion("Llamar a tu banda", hacer(llamar), ayuda="Acuden a donde estés, te siguen a pie, suben contigo al vehículo y pelean a tu lado."),
        Opcion("Mandarlos a casa", hacer(despedir)),
        Opcion("Cambiar el nombre de la banda", nombrar),
    ])
    app.abrir(m)


# ============================================================ interior de las casas
HABITACIONES = [
    ("la entrada", "Un perchero y las llaves colgadas. Por aquí se sale a la calle.", "salir"),
    ("el salón", "Un sofá, la tele y una ventana a la calle.", "salon"),
    ("la cocina", "La nevera zumba. Huele a café.", "cocina"),
    ("el baño", "Un espejo y una ducha.", "bano"),
    ("el dormitorio", "La cama está hecha. Aquí se duerme y se guarda la partida.", "dormitorio"),
]


# Amueblar la casa: cada mueble va a una habitación, cambia cómo es y mejora lo que se hace en ella.
# (id, habitación, nombre, precio, cómo queda la habitación, qué mejora)
MUEBLES = [
    ("recibidor", "salir", "Plantas, cuadros y una alfombra", 300, "Hay plantas, cuadros en las paredes y una alfombra que da gusto pisar.",
     "La casa es más acogedora: al dormir aquí te levantas con algo más de ánimo."),
    ("sofa", "salon", "Un sofá grande y una tele nueva", 600, "Un sofá en el que caben cuatro y una tele enorme.",
     "Ver la tele te sube el ánimo el doble."),
    ("cocina", "cocina", "Cocina equipada y nevera grande", 700, "Cocina nueva, con horno, y una nevera grande y llena.",
     "Lo que te preparas en casa te da el doble de salud."),
    ("banera", "bano", "Baño reformado, con bañera", 500, "Azulejos nuevos y una bañera en la que te puedes estirar.",
     "Un baño largo te sube más el ánimo y te quita algún golpe."),
    ("cama", "dormitorio", "Una cama de las buenas", 800, "Una cama ancha, con un colchón de los caros.",
     "Dormir aquí te sube bastante el ánimo."),
    ("taller", "garaje", "Un banco de herramientas", 900, "En la pared, un banco de herramientas bien surtido.",
     "Mientras duermes, los vehículos guardados en este garaje se quedan reparados."),
]


def muebles_de(j, lugar):
    return j.muebles.get(lugar.id, [])


def menu_muebles(p, lugar, Menu, Opcion):
    """Comprar muebles para una casa tuya."""
    app, j = p.app, p.j
    tengo = j.muebles.setdefault(lugar.id, [])

    def comprar(mueble):
        def f():
            if mueble[0] in tengo:
                return app.decir("Eso ya lo tienes puesto.", True)
            if not p.pagar(mueble[3]):
                return
            tengo.append(mueble[0])
            p.cambiar_animo(3)
            app.decir(f"Te lo traen y lo dejan puesto. {mueble[4]} {mueble[5]}", True)
            m.refrescar(False)
        return f

    def ops():
        lista = []
        for mu in MUEBLES:
            if mu[1] == "garaje" and not int(lugar.get("garaje", 0)):
                continue
            if mu[0] in tengo:
                lista.append(Opcion(f"{mu[2]}: ya lo tienes. {mu[5]}"))
            else:
                lista.append(Opcion(f"{mu[2]}: {mu[3]} euros", comprar(mu), ayuda=mu[5]))
        lista.append(Opcion("Volver", lambda: app.cerrar(m)))
        return lista
    m = Menu(app, lambda: f"Amueblar {lugar.nombre}. Tienes {j.dinero} euros", ops,
             intro="Cada mueble va a una habitación y mejora lo que haces en ella. Se quedan en esta casa")
    app.abrir(m)


def al_dormir_en_casa(p, lugar):
    """Lo que añaden los muebles a una noche en casa. Devuelve el texto que se suma al de haber dormido."""
    j = p.j
    tengo = muebles_de(j, lugar)
    texto = ""
    extra = (8 if "cama" in tengo else 0) + (3 if "recibidor" in tengo else 0)
    if extra:
        p.cambiar_animo(extra)
        texto += " Has dormido de maravilla."
    if "taller" in tengo:
        arreglados = 0
        for d in j.garajes.get(lugar.id, []):
            modelo = p.modelos.get(d.get("modelo"))
            if modelo and float(d.get("salud", 0)) < float(modelo["salud"]):
                d["salud"] = float(modelo["salud"])
                arreglados += 1
        if arreglados:
            texto += f" En el garaje, {arreglados} {'vehículo ha quedado reparado' if arreglados == 1 else 'vehículos han quedado reparados'}."
    return texto


class Interior:
    """Recorrer una casa tuya: flechas izquierda y derecha para ir de una habitación a otra, Intro para usarla."""
    pausa_mundo = True
    pared = "Pared. No hay más casa por ahí."

    def ayuda(self):
        return "Estás dentro de tu casa. Flechas izquierda y derecha para ir de una habitación a otra, Intro para usar la habitación en la que estás y Escape para salir."

    def __init__(self, p, lugar, acciones):
        self.p, self.app, self.l, self.acciones = p, p.app, lugar, acciones
        self.habitaciones = list(HABITACIONES)
        if int(lugar.get("garaje", 0)):
            self.habitaciones.append(("el garaje", f"Sitio para {int(lugar.get('garaje', 0))} vehículos. Huele a gasolina.", "garaje"))
        self.muebles = muebles_de(p.j, lugar)
        for mu in MUEBLES:                                # lo que has comprado se nota al entrar en cada habitación
            if mu[0] in self.muebles:
                self.habitaciones = [(n, d + " " + mu[4], q) if q == mu[1] else (n, d, q) for n, d, q in self.habitaciones]
        self.i = 0

    def al_entrar(self):
        self.app.mez.entorno = "interior"
        nombre, desc, _ = self.habitaciones[self.i]
        self.app.decir(f"{self.l.nombre}, por dentro. Estás en {nombre}. {desc} Flechas izquierda y derecha para moverte por la casa, Intro para usar la habitación, Escape para salir.", True)

    def _decir(self):
        nombre, desc, _ = self.habitaciones[self.i]
        self.app.decir(f"{nombre.capitalize()}. {desc} {self.i + 1} de {len(self.habitaciones)}.", True)

    def tecla(self, ev):
        k = ev.key
        if k in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT, pygame.K_UP):
            paso = 1 if k in (pygame.K_RIGHT, pygame.K_DOWN) else -1
            nuevo = self.i + paso
            if not 0 <= nuevo < len(self.habitaciones):
                self.app.son("menu_borde")
                self.app.decir(self.pared, True)
                return
            self.i = nuevo
            for n in range(3):                          # tres pasos sobre el suelo de casa
                self.app.son(("paso_acera0", "paso_acera1")[n % 2], vol=0.5, pan=0.5 * paso).eco = True
            self._decir()
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._usar()
        elif k == pygame.K_ESCAPE:
            self.app.son("puerta_entrar")
            self.app.cerrar(self)
        elif k == pygame.K_F1:
            self.app.decir(self.ayuda(), True)
        else:
            self._decir()

    def _usar(self):
        p, j, app = self.p, self.p.j, self.app
        que = self.habitaciones[self.i][2]
        if que == "salir":
            app.son("puerta_entrar")
            app.cerrar(self)
        elif que == "salon":
            p.pasar_horas(1)
            p.cambiar_animo(8 if "sofa" in self.muebles else 4)
            app.son("pasan_horas")
            app.decir(f"Te {'hundes en el sofá' if 'sofa' in self.muebles else 'sientas un rato'} a ver la tele. Te sube el ánimo. Son las {p.hora_txt()}.", True)
        elif que == "cocina":
            if getattr(j, "dia_nevera", -1) == p.dia:
                app.decir("Hoy ya te has comido lo que había en la nevera. Mañana habrá más.", True)
            else:
                j.dia_nevera = p.dia
                j.salud = min(j.salud_max, j.salud + (50 if "cocina" in self.muebles else 25))
                p.son("comer", cat="interfaz")
                p.ha_bebido(100)                                 # en casa, el agua del grifo no falta
                app.decir(f"Te preparas {'una buena comida en tu cocina nueva' if 'cocina' in self.muebles else 'algo con lo que hay en la nevera'}. Salud {int(j.salud)}.{p.necesidades_txt()}", True)
        elif que == "bano":
            app.son("salpicadura", vol=0.5)
            p.ha_duchado()
            p.ha_bebido(100)
            if "banera" in self.muebles:
                p.cambiar_animo(5)
                j.salud = min(j.salud_max, j.salud + 10)
                app.decir("Un baño largo, con el agua bien caliente. Sales como nuev[o|a].", True)
            else:
                p.cambiar_animo(2)
                app.decir("Una ducha caliente. Sales como nuev[o|a].", True)
        elif que == "dormitorio":
            self.acciones["descansar"]()
        elif que == "garaje":
            self.acciones["garaje"]()

    def actualizar(self, dt):
        pass

    def cerrado(self):
        pass


# ============================================================ interior del resto de lugares
# Cada sala: (nombre, descripción, qué hace Intro). Las acciones:
#   salir: a la calle del menú.  mostrador: vuelve al menú del lugar, que es donde se compra o se pide.
#   sentarse: pasa media hora y sube el ánimo.  escuchar: oyes una conversación.  aseo: te refrescas.  mirar: solo se describe.
#   tablon_policia, tablon_premios, tablon_ofertas: tablones que se leen, y dicen lo que hay hoy.
_PUERTA = ("la puerta", "Por aquí se sale.", "salir")
_ASEO = ("los aseos", "Un lavabo y un espejo.", "aseo")
SALAS = {
    "bar": [_PUERTA, ("la barra", "Tazas, botellas y la cafetera silbando. Aquí se pide.", "mostrador"), ("las mesas", "Cuatro mesas y gente hablando bajo.", "escuchar"),
            ("la máquina del rincón", "Una tragaperras que canta sola. Intro para echar unas monedas.", "tragaperras"), _ASEO],
    "taberna": [_PUERTA, ("la barra", "Madera vieja y barriles. Aquí se pide.", "mostrador"), ("las mesas del fondo", "Bancos corridos y partidas de cartas.", "escuchar"), _ASEO],
    "comida": [_PUERTA, ("el mostrador", "La carta colgada y la caja. Aquí se pide.", "mostrador"), ("el comedor", "Mesas con mantel de papel. Huele a fritura.", "sentarse"), _ASEO],
    "pizzeria": [_PUERTA, ("el mostrador", "El horno al fondo y la caja. Aquí se pide.", "mostrador"), ("el comedor", "Mesas pequeñas y una tele encendida.", "sentarse"), _ASEO],
    "tienda": [_PUERTA, ("el mostrador", "La caja y el tendero. Aquí se compra.", "mostrador"), ("los pasillos", "Estanterías hasta el techo, latas y cajas.", "mirar"), ("la trastienda", "Una cortina y cajas apiladas. No te dejan pasar.", "escuchar")],
    "farmacia": [_PUERTA, ("el mostrador", "Batas blancas y cajas de medicinas. Aquí se compra.", "mostrador"), ("la zona de espera", "Dos sillas y una báscula.", "sentarse")],
    "armeria": [_PUERTA, ("el mostrador", "Un cristal grueso y el armero detrás. Aquí se compra.", "mostrador"), ("las vitrinas", "Armas colgadas tras un cristal. Huele a aceite.", "mirar"),
                ("la galería de tiro", "Un pasillo largo con dianas al fondo.", "mirar")],
    "hospital": [_PUERTA, ("la recepción", "Un mostrador y gente esperando. Aquí te atienden.", "mostrador"), ("la sala de espera", "Sillas de plástico y una máquina de café.", "sentarse"),
                 ("el pasillo de consultas", "Puertas numeradas y pasos rápidos.", "escuchar"), _ASEO],
    "comisaria": [_PUERTA, ("el mostrador de guardia", "Un agente tras una mampara. Aquí te atienden.", "mostrador"), ("los bancos de espera", "Un banco atornillado al suelo.", "escuchar"),
                  ("el tablón", "Carteles de personas buscadas y avisos. Intro para leerlo.", "tablon_policia")],
    "taller": [_PUERTA, ("la oficina", "Un mostrador con facturas. Aquí se encarga el trabajo.", "mostrador"), ("el foso", "Un coche levantado y herramientas por el suelo.", "mirar"),
               ("el almacén de piezas", "Neumáticos apilados y cajas de recambios.", "escuchar")],
    "desguace": [_PUERTA, ("la caseta", "Una mesa y una báscula. Aquí se trata.", "mostrador"), ("el patio de chatarra", "Coches apilados de tres en tres.", "mirar")],
    "casino": [_PUERTA, ("las mesas de juego", "Fichas, cartas y la ruleta girando. Aquí se juega.", "mostrador"), ("la sala de máquinas", "Filas de tragaperras con sus musiquillas.", "mirar"),
               ("el bar del casino", "Sillones y copas. Aquí se habla de dinero.", "escuchar"), _ASEO],
    "negocio": [_PUERTA, ("el despacho", "Una mesa y los libros de cuentas. Aquí se trata.", "mostrador"), ("el local", "El negocio en marcha, con su gente.", "escuchar")],
    "periodico": [_PUERTA, ("la redacción", "Teclados, teléfonos y prisas. Aquí te atienden.", "mostrador"), ("la sala de rotativas", "Máquinas enormes y olor a tinta.", "mirar"),
                  ("el archivo", "Estanterías con periódicos viejos.", "escuchar")],
    "banco": [_PUERTA, ("la ventanilla", "Un cristal y un empleado. Aquí se opera.", "mostrador"), ("la cola", "Gente esperando con papeles en la mano.", "escuchar"),
              ("la puerta de la cámara", "Acero, y un guardia delante.", "mirar")],
    "loteria": [_PUERTA, ("la ventanilla", "Décimos colgados y un bombo pequeño. Aquí se compra.", "mostrador"), ("el tablón de premios", "Los números premiados de la semana. Intro para leerlo.", "tablon_premios")],
    "empenos": [_PUERTA, ("el mostrador", "Una reja y una lupa. Aquí se trata.", "mostrador"), ("las estanterías", "Relojes, guitarras y televisores de otros.", "mirar")],
    "pescaderia": [_PUERTA, ("el mostrador", "Hielo picado y pescado fresco. Aquí se vende y se compra.", "mostrador"), ("la cámara", "Frío y cajas de corcho.", "mirar")],
    "gimnasio": [_PUERTA, ("la recepción", "Un mostrador con toallas. Aquí te apuntas.", "mostrador"), ("la sala de pesas", "Hierros que suenan y gente resoplando.", "escuchar"),
                 ("el ring", "Lona, cuerdas y un saco colgado.", "mirar"), ("los vestuarios", "Bancos, taquillas y duchas.", "aseo")],
    "ropa": [_PUERTA, ("la caja", "El mostrador y las bolsas. Aquí se paga.", "mostrador"), ("los percheros", "Filas de ropa colgada.", "mirar"), ("los probadores", "Cortinas y espejos.", "mirar")],
    "cine": [_PUERTA, ("la taquilla", "La cartelera y las entradas. Aquí se compra.", "mostrador"), ("el vestíbulo", "Huele a palomitas. Hay gente esperando.", "escuchar"), _ASEO],
    "hotel": [_PUERTA, ("la recepción", "Un mostrador con campanilla. Aquí te atienden.", "mostrador"), ("el salón", "Sillones y un piano que nadie toca.", "sentarse"),
              ("el pasillo de habitaciones", "Moqueta y puertas numeradas.", "escuchar"), _ASEO],
    "concesionario": [_PUERTA, ("la mesa del vendedor", "Catálogos y un bolígrafo listo. Aquí se compra.", "mostrador"), ("la exposición", "Coches nuevos, brillantes, con olor a tapicería.", "mirar")],
    "nautica": [_PUERTA, ("el mostrador", "Cartas de navegación y cabos. Aquí se compra.", "mostrador"), ("la exposición", "Motores fueraborda y un velero pequeño en seco.", "mirar")],
    "club": [_PUERTA, ("la barra", "Luces bajas y música fuerte. Aquí te atienden.", "mostrador"), ("la pista", "Gente bailando apretada.", "escuchar"), _ASEO],
    "proveedor": [_PUERTA, ("la mesa", "Una mesa, una silla y pocas palabras. Aquí se trata.", "mostrador"), ("el cuarto de atrás", "Una puerta cerrada. Mejor no preguntar.", "mirar")],
    "empleo": [_PUERTA, ("la mesa de atención", "Un ordenador y un montón de impresos. Aquí te atienden.", "mostrador"), ("el tablón de ofertas", "Papeles con trabajos, sujetos con chinchetas. Intro para leerlo.", "tablon_ofertas"),
               ("la sala de espera", "Sillas en fila y gente con carpetas.", "escuchar")],
    "academia": [_PUERTA, ("la secretaría", "Matrículas y horarios. Aquí te apuntas.", "mostrador"), ("el aula", "Pupitres y una pizarra.", "sentarse"), ("el pasillo", "Alumnos comentando el examen.", "escuchar")],
    "ong": [_PUERTA, ("la mesa de acogida", "Una voluntaria con una lista. Aquí te atienden.", "mostrador"), ("el almacén", "Cajas de comida y ropa doblada.", "mirar")],
    "protectora": [_PUERTA, ("la oficina", "Fichas de animales y una mesa. Aquí te atienden.", "mostrador"), ("las jaulas", "Ladridos y rabos golpeando la reja.", "mirar")],
}
OIDO = [
    "Dos hombres discuten de fútbol sin escucharse.", "Una mujer cuenta que le han subido el alquiler otra vez.", "Alguien dice en voz baja que anoche hubo jaleo en el puerto.",
    "Hablan de un coche robado que apareció quemado en las afueras.", "Un viejo asegura que antes esto era otra cosa.", "Una pareja decide adónde ir de vacaciones, sin ponerse de acuerdo.",
    "Dicen que la policía anda preguntando por el barrio.", "Alguien cuenta que al del estanco le tocó un pellizco en la lotería.", "Dos chavales hablan de una carrera de coches de esta noche.",
    "Una señora se queja de que ya no se puede aparcar en ningún sitio.", "Comentan que va a llover toda la semana.", "Alguien busca trabajo y pregunta si saben de algo.",
    "Un hombre presume de lo que pescó el domingo. Nadie le cree.", "Hablan de un negocio que cambió de dueño de un día para otro.", "Dos amigas se ríen de algo que no llegas a oír.",
    "Alguien dice que no se fía de los bancos, que el dinero, en casa.",
]


QUE_HACE = {"salir": "sales del recorrido", "mostrador": "te atienden: vuelves al menú del lugar, donde están las opciones para comprar o pedir",
            "sentarse": "te sientas un rato", "escuchar": "pones el oído a lo que se habla", "aseo": "te refrescas", "tragaperras": "echas unas monedas",
            "mirar": "te lo describe", "tablon_policia": "lees los carteles y los avisos de hoy", "tablon_premios": "lees los números premiados",
            "tablon_ofertas": "lees las ofertas de trabajo"}
ACERCARSE = ("Te acercas a {}", "Vas hasta {}", "Te plantas ante {}", "Caminas hasta {}")
ATIENDEN = (": aquí te atienden", ". Te atienden", ": te toca")


def _con_a(frase):
    """«a el mostrador» se dice «al mostrador»."""
    return frase.replace(" a el ", " al ")


def tablon_policia(p):
    """Lo que dice hoy el tablón de la comisaría: si te buscan y lo que te costaría, las bandas de la ciudad y los sucesos del día."""
    j, s = p.j, p.j.stats
    if p.en_servidor and p.sv.get("recompensa"):
        yo = f"Hay un cartel con tu cara: ofrecen {p.sv['recompensa']} euros por tu cabeza."
    elif j.estrellas:
        yo = random.choice(["En el cartel más reciente reconoces tu cara", "Hay un cartel nuevo, y el del retrato eres tú", "Uno de los carteles lleva tu descripción"]) + \
            f": búsqueda de nivel {j.estrellas}. Si te cogen ahora, la multa rondaría los {p.coste_multa()} euros."
    else:
        yo = random.choice(["Repasas las caras de los carteles: ninguna es la tuya. No te busca nadie.", "Ningún cartel lleva tu cara: no te buscan.",
                            "Buscas tu nombre en la lista de personas buscadas y no está: no te buscan."])
    if s.get("detenciones"):
        yo += f" Tu ficha: {s['detenciones']} {'detención' if s['detenciones'] == 1 else 'detenciones'}."
    avisos = []
    if not p.en_servidor:
        for b in p.mundo.barrios:
            banda = b["id"] not in j.territorios and p.banda_de_barrio(b)
            if banda:
                avisos.append(f"Se busca a miembros de {banda}, que se mueven por {b['nombre']}.")
        if j.amenaza:
            avisos.append(f"Aviso de la jefatura: se esperan enfrentamientos entre bandas en {_nombre_barrio(p, j.amenaza['territorio'])[0]}.")
    ev = getattr(p, "evento", None)
    if ev:
        avisos.append({"atraco": "Aviso de última hora: están atracando a alguien cerca de aquí.", "banda": "Aviso de última hora: pandilleros alborotando en una calle cercana.",
                       "maletin": "Objetos perdidos: alguien ha denunciado hoy la pérdida de un maletín por esta zona."}.get(ev.get("tipo"), ""))
    if p.dia_txt():
        avisos.append("Parte del día: " + p.dia_txt())
    if s.get("vehiculos_robados", 0) > 2:
        avisos.append(f"Robos de vehículos sin resolver: {s['vehiculos_robados']}.")
    if s.get("atracos", 0):
        avisos.append("Se recuerda a los comercios que refuercen sus alarmas tras los últimos atracos.")
    avisos.append("Recorte del periódico: " + p.noticia())
    avisos.append(random.choice(["Recuerda: la multa, pagada en el acto, sale más barata que la de comisaría.", "Un aviso pide testigos de una carrera ilegal nocturna.",
                                 "Se han encontrado unas llaves: preguntar en el mostrador de guardia.", "La policía local busca voluntarios para la verbena. Nadie se ha apuntado.",
                                 "Campaña de tráfico: este mes, más controles de velocidad.", "Un cartel descolorido ofrece recompensa por un loro que sabe decir palabrotas."]))
    avisos = [a for a in avisos if a]
    random.shuffle(avisos)
    return yo + " " + " ".join(avisos[:2])


def tablon_premios(p):
    """El tablón de la administración de lotería: los números que han salido de verdad en los últimos sorteos, y el bote."""
    from . import loteria
    ult = loteria.ultimo_celebrado(p)
    salidos = [f"{'hoy' if d == p.dia else 'ayer' if d == p.dia - 1 else 'hace ' + str(p.dia - d) + ' días'}, el {loteria.cifras(loteria.premiado(p, d))}"
               for d in range(ult, max(0, ult - 3), -1)]
    return ("Números premiados: " + "; ".join(salidos) + ". " if salidos else "Todavía no se ha celebrado ningún sorteo. ") + loteria.estado_txt(p) + "."


def tablon_ofertas(p):
    """El tablón de la oficina de empleo: unas cuantas jornadas de las que hay, con su paga de verdad."""
    ofertas = [x for x in p.datos.get("jornadas", []) if x.get("nombre")]
    if not ofertas:
        return "Hoy el tablón está vacío."
    return ("Lees algunas ofertas. " + " ".join(f"{x['nombre']}: {int(x.get('paga', 0))} euros." for x in random.sample(ofertas, min(3, len(ofertas))))
            + " Para apuntarte, en la mesa de atención.")


TABLONES = {"tablon_policia": tablon_policia, "tablon_premios": tablon_premios, "tablon_ofertas": tablon_ofertas}


def salas_de(lugar):
    return SALAS.get(getattr(lugar, "tipo", ""))


class Local(Interior):
    """Recorrer por dentro una tienda, un bar, un banco o cualquier otro local: de sala en sala con las flechas."""

    def __init__(self, p, lugar):
        self.p, self.app, self.l, self.acciones = p, p.app, lugar, {}
        self.habitaciones = list(salas_de(lugar) or [_PUERTA])
        for pers in personas_aqui(p, lugar):                  # la gente de tu vida social está en su sitio, no solo en el móvil
            if not (p.acompanante and p.acompanante["pid"] == pers["id"]):
                self.habitaciones.insert(2, (f"donde está {pers['nombre']}", pers["desc"], ("persona", pers["id"])))
        self.i = 0
        self.oidas = 0
        self.pared = random.choice(("Pared. El local no sigue por ahí.", "Pared. No hay más local por ese lado.", "Pared. Por ahí no hay nada más."))

    def ayuda(self):
        nombre, _, que = self.habitaciones[self.i]
        aqui = "te acercas a hablar" if isinstance(que, tuple) else QUE_HACE.get(que, "te lo describe")
        atiende = next((n for n, _, q in self.habitaciones if q == "mostrador"), None)
        return (f"Estás recorriendo {self.l.nombre} por dentro. Flechas izquierda y derecha para ir de un sitio a otro, Intro para usar el sitio donde estás y Escape para volver al menú del lugar. "
                f"Ahora estás en {nombre}: con Intro, {aqui}."
                + (f" Para comprar, pedir o que te atiendan, ve a {atiende} y pulsa Intro, o sal con Escape: las opciones están en el menú del lugar." if atiende and que != "mostrador" else ""))

    def al_entrar(self):
        self.app.mez.entorno = "nave" if self.l.tipo in ("taller", "desguace", "concesionario", "nautica", "gimnasio") else "interior"
        nombre, desc, _ = self.habitaciones[self.i]
        self.app.decir(f"{self.l.nombre}, por dentro. Estás en {nombre}. {desc} Flechas izquierda y derecha para moverte, Intro para usar el sitio donde estás, Escape para volver.", True)

    def _usar(self):
        p, app = self.p, self.app
        nombre, desc, que = self.habitaciones[self.i]
        if isinstance(que, tuple):
            from . import menus_adultos
            menus_adultos.vida_social(p, directo=que[1])
        elif que == "mostrador":                                 # donde te atienden: se dice, y se vuelve al menú del lugar
            for n in range(2):
                app.son(("paso_acera0", "paso_acera1")[n % 2], vol=0.5).eco = True
            k = app.pila.index(self) if self in app.pila else 0
            debajo = app.pila[k - 1] if k > 0 else None
            frase = _con_a(random.choice(ACERCARSE).format(nombre)) + random.choice(ATIENDEN)
            if debajo is not None and hasattr(debajo, "antes"):
                debajo.antes = frase                              # el menú del lugar lo dice delante de su título
                app.cerrar(self)
            else:
                app.cerrar(self)
                app.decir(frase + ".")
        elif que == "salir":
            app.son("menu_atras")
            app.cerrar(self)
        elif que in TABLONES:
            app.son("cursor_mapa", vol=0.6)
            app.decir(TABLONES[que](p), True)
        elif que == "sentarse":
            p.pasar_horas(0.5)
            p.cambiar_animo(2)
            app.son("pasan_horas")
            app.decir(f"Te sientas un rato. Son las {p.hora_txt()}.", True)
        elif que == "escuchar":
            self.oidas += 1
            app.son("murmullo", vol=0.5)
            app.decir("Pones el oído. " + random.choice(OIDO), True)
        elif que == "aseo":
            p.cambiar_animo(1)
            app.son("salpicadura", vol=0.5)
            app.decir("Te lavas la cara. Mejor.", True)
        elif que == "tragaperras":
            from . import menus_juego
            menus_juego._tragaperras(p)
        else:
            app.decir(f"{nombre.capitalize()}. {desc}", True)


def con_recorrido(p, lugar, menu, Opcion):
    """Añade al menú de un local la opción de recorrerlo por dentro, antes de la de salir."""
    if not salas_de(lugar):
        return
    fuente = menu._fuente
    from .menus import SALIDAS

    def ops():
        lista = list(fuente() if callable(fuente) else fuente)
        if any(o.texto.startswith("Recorrer") for o in lista):
            return lista
        for pers in personas_aqui(p, lugar):
            if not (p.acompanante and p.acompanante["pid"] == pers["id"]):
                from . import menus_adultos
                lista.insert(0, Opcion(f"{pers['nombre']} está aquí: acercarte a hablar", lambda pid=pers["id"]: menus_adultos.vida_social(p, directo=pid),
                                       ayuda="Lo mismo que desde el móvil, pero en persona: charlar, quedar, hacerle un regalo o proponerle salir a dar una vuelta contigo."))
        o = Opcion("Recorrer el local por dentro", lambda: p.app.abrir(Local(p, lugar)),
                   ayuda="Entras y vas de una sala a otra con las flechas izquierda y derecha. En el mostrador te atienden: vuelves a este menú, que es donde se compra o se pide. Dentro, F1 te explica dónde estás.")
        lista.insert(len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista), o)
        return lista
    menu._fuente = ops
    menu.refrescar(False)


# ============================================================ sucesos de territorio
# Tener barrios llama la atención: otras bandas los quieren, alguna prefiere pactar, y la policía te pone en su lista.
def _nombre_barrio(p, ident):
    for m in p.mapas.values():
        for b in m.barrios:
            if b["id"] == ident:
                return b["nombre"], m
    return ident, None


def sucesos_territorio(p, azar=None):
    """Cada medianoche: se cumplen los plazos pendientes y, a veces, pasa algo nuevo."""
    import random
    from . import gente
    BANDAS = gente.nombres_bandas()
    azar = azar or random
    j = p.j
    # --- plazos que vencen
    a = j.amenaza
    if a and p.dia > a["dia"]:
        j.amenaza = None
        if a["territorio"] in j.territorios:
            j.territorios.remove(a["territorio"])
            j.barrios_banda[a["territorio"]] = a["banda"]          # desde ahora ese barrio es de ellos
            p.son("mision_fallo", cat="interfaz")
            p.decir(f"No defendiste {_nombre_barrio(p, a['territorio'])[0]} y {a['banda']} se lo ha quedado. Ya no te paga.")
            p.cambiar_reputacion(-4)
    r = j.redada
    if r and p.dia > r["dia"]:
        j.redada = None
        perdido = min(j.dinero, p.precio("redada_territorio", 300) * len(j.territorios))
        j.dinero -= perdido
        p.decir(f"No arreglaste lo de la policía: una redada en tus barrios te cuesta {perdido} euros.")
    o = j.oferta_pacto
    if o and p.dia > o["dia"]:
        j.oferta_pacto = None
    if not j.territorios or not p.cfg["sucesos"] or j.amenaza or j.redada or j.oferta_pacto:
        return
    n = len(j.territorios)
    if azar.random() > 0.12 + 0.05 * min(n, 5):
        return
    banda = azar.choice(BANDAS)
    tipo = azar.choice(["ataque", "ataque", "policia"] + (["pacto", "pacto"] if n >= 3 else []))
    if tipo == "ataque" and p.rep_banda(banda) >= 30:
        return                                                    # esa banda te respeta: no toca lo tuyo
    if tipo == "ataque" and p.dia <= j.pacto_hasta:
        return                                                    # hay un pacto en vigor: nadie ataca
    if tipo == "ataque":
        t = azar.choice(j.territorios)
        nombre = _nombre_barrio(p, t)[0]
        if j.banda >= 2 and azar.random() < min(0.9, 0.25 + 0.15 * j.banda):
            p.son("territorio", cat="interfaz")
            p.decir(f"{banda} ha intentado quedarse con {nombre}, pero {j.banda_nombre or 'tu banda'} los ha echado sin que tuvieras que ir.")
            p.cambiar_reputacion(2)
            return
        j.amenaza = {"territorio": t, "banda": banda, "dia": p.dia}
        p.son("notificacion", cat="interfaz")
        p.decir(f"{banda} está atacando {nombre}. Tienes hasta la próxima medianoche para defenderlo: en el móvil, Territorios. Si no vas, lo pierdes.")
    elif tipo == "pacto":
        j.oferta_pacto = {"banda": banda, "precio": p.precio("pacto_territorio", 500) * n, "dia": p.dia}
        p.son("notificacion", cat="interfaz")
        p.decir(f"{banda} te propone un pacto: te pagan {j.oferta_pacto['precio']} euros y durante una semana nadie toca los barrios de nadie. Contesta en el móvil, en Territorios, antes de medianoche.")
    else:
        j.redada = {"precio": p.precio("soborno_inspector", 250) * n, "dia": p.dia}
        p.son("notificacion", cat="interfaz")
        p.decir(f"Un inspector te hace saber que estás en su lista. Por {j.redada['precio']} euros mirará hacia otro lado. Si no, habrá redada. Arréglalo en el móvil, en Territorios, antes de medianoche.")


def defender(p):
    """Ir a defender el territorio atacado: dos grupos de la banda rival en ese barrio."""
    import random
    j = p.j
    a = j.amenaza
    if not a:
        return
    nombre, mapa = _nombre_barrio(p, a["territorio"])
    if mapa is None or mapa.id != p.mundo.id:
        p.app.son("error")
        p.decir(f"{nombre} está en {mapa.nombre if mapa else 'otra localidad'}. Tienes que ir allí para defenderlo.", True)
        return
    ls = [l for l in p.mundo.lugares.values() if p.mundo.barrio(l.x, l.y)["id"] == a["territorio"] and l.tipo not in ("salida", "embarcadero")]
    if len(ls) < 1:
        j.amenaza = None
        return
    random.shuffle(ls)
    pasos = []
    for k, n in enumerate((3, 4)):
        l = ls[k % len(ls)]
        pasos.append({"tipo": "eliminar", "lugar": l.id, "texto": f"{['Primer', 'Último'][k]} grupo de {a['banda']}: {n} pandilleros junto a {l.nombre}.",
                      "enemigos": [{"n": n, "tipo": f"Pandillero de {a['banda']}", "arma": random.choice(["pistola", "pistola", "subfusil"]), "salud": 70 + 8 * k}]})

    def hecho():
        j.amenaza = None
        p.cambiar_reputacion(3)
        p.decir(f"{nombre} sigue siendo tuyo.")
    p._empezar_repetible({"id": "defensa", "titulo": f"Defensa de {nombre}", "lugar": ls[0].id, "contador": "defensas", "pasos": pasos,
                          "recompensa": {"dinero": 800}, "al_completar": hecho})


def opciones_sucesos(p, Menu, Opcion):
    """Lo que hay pendiente en tus territorios, para el menú de Territorios."""
    j = p.j
    app = p.app
    ops = []

    def cerrar_menus():
        """Resuelto un asunto, se cierran su menú y el de Territorios, que se quedaba con la oferta escrita. Nada más que eso."""
        for _ in range(2):
            cima = app.pila[-1] if app.pila else None
            titulo = getattr(cima, "titulo", "")
            titulo = titulo() if callable(titulo) else str(titulo)
            if isinstance(cima, Menu) and (titulo.startswith("Territorios") or "propone un pacto" in titulo):
                app.cerrar(cima)
    if j.amenaza:
        a = j.amenaza

        def ir():
            if p.mision or p.trabajo:
                app.son("error")
                app.decir("Termina antes lo que tienes entre manos.", True)
                return
            while app.pila and app.pila[-1] is not p:
                app.cerrar(app.pila[-1])
            defender(p)
        ops.append(Opcion(f"Defender {_nombre_barrio(p, a['territorio'])[0]}: lo ataca {a['banda']}", ir,
                          ayuda="Dos grupos de pandilleros. Si los echas, el barrio sigue siendo tuyo. Si llega la medianoche sin haber ido, lo pierdes. Tu banda pelea a tu lado."))
    if j.oferta_pacto:
        o = j.oferta_pacto

        def resuelto():
            """El menú de Territorios sigue abierto con la oferta escrita: que no se pueda cobrar dos veces."""
            if j.oferta_pacto is o:
                return False
            app.son("error")
            app.decir("Eso ya está resuelto.", True)
            return True

        def aceptar():
            if resuelto():
                return app.cerrar()
            j.oferta_pacto = None
            j.pacto_hasta = p.dia + 7
            p.cambiar_rep_banda(o["banda"], 15)
            p.dar_dinero(o["precio"], "Cobras")
            app.decir(f"Pacto cerrado con {o['banda']}. Una semana sin ataques.", True)
            cerrar_menus()

        def rechazar():
            if resuelto():
                return app.cerrar()
            j.oferta_pacto = None
            p.cambiar_rep_banda(o["banda"], -8)
            p.cambiar_reputacion(1)
            app.decir(f"Le dices a {o['banda']} que no pactas con nadie. En la calle gusta, pero pueden volver.", True)
            cerrar_menus()
        ops.append(Opcion(f"Pacto con {o['banda']}: te pagan {o['precio']} euros por una semana de paz",
                          lambda: None if resuelto() else app.abrir(Menu(app, f"{o['banda']} propone un pacto", [Opcion("Aceptar el pacto", aceptar), Opcion("Rechazarlo", rechazar)])),
                          ayuda="Si aceptas, cobras y durante siete días nadie ataca tus barrios. Si lo rechazas, ganas algo de fama."))
    if j.redada:
        r = j.redada

        def pagar():
            if j.redada is not r:                        # ya se pagó: el menú seguía con la opción escrita
                app.son("error")
                return app.decir("Eso ya está resuelto.", True)
            if p.pagar(r["precio"]):
                j.redada = None
                app.decir("El inspector se guarda el sobre. Por ahora, no ha visto nada.", True)
                cerrar_menus()
        ops.append(Opcion(f"Arreglar lo de la policía: {r['precio']} euros", pagar,
                          ayuda="Si pagas, no hay redada. Si llega la medianoche sin pagar, una redada te cuesta el tributo de un día de todos tus barrios."))
    if p.dia <= j.pacto_hasta:
        ops.append(Opcion(f"Pacto en vigor: nadie ataca tus barrios hasta el día {j.pacto_hasta}"))
    conocidas = [(b, x) for b, x in sorted(j.rep_bandas.items()) if abs(x) >= 1]
    if conocidas:
        ops.append(Opcion("Cómo te llevas con las bandas: " + ". ".join(f"{b}, {p.rep_banda_txt(x)}" for b, x in conocidas),
                          ayuda="Con una banda que te respeta, sus pandilleros no te atacan por la calle y no intentan quitarte barrios. Con una que va a por ti, pasa lo contrario. "
                                "Cambia con las decisiones de la historia, con los pactos y cada vez que matas a uno de los suyos."))
    return ops


# ============================================================ salir a dar una vuelta con alguien de tu vida social
def personas_aqui(p, lugar):
    """La gente de tu vida social que suele estar en este lugar (solo con el contenido para adultos)."""
    if not p.modo_adulto():
        return []
    return [x for x in p.dato_adulto("personas") if x.get("lugar") == lugar.id]


def empezar_paseo(p, pers):
    j = p.j
    r = p.relacion(pers["id"])
    if p.acompanante:
        p.decir(f"Ya vas con {p.acompanante['nombre']}.", True)
        return False
    if p._hecho_hoy(r, "paseo"):
        p.decir(f"Hoy ya habéis salido. {pers['nombre']} tiene cosas que hacer.", True)
        return False
    x, y = p.pos()
    p.acompanante = {"pid": pers["id"], "nombre": pers["nombre"], "lugar": pers["lugar"], "x": x, "y": y, "t_paso": 0.0, "metros": 0.0, "puntos": 0,
                     "px": x, "py": y, "hasta": p.dia * 1440 + p.reloj + 180, "sitios": []}
    p.app.son("llegada")
    p.decir(f"{pers['nombre']} se viene contigo. Te sigue a pie y sube al vehículo que cojas. Llévale a dar una vuelta, a comer o al cine; "
            f"para despedirte, vuelve a dejarle donde estaba o díselo desde su ficha.", True)
    return True


def terminar_paseo(p, motivo=""):
    a = p.acompanante
    if not a:
        return
    p.acompanante = None
    if a["puntos"]:
        p.sumar_afinidad(a["pid"], a["puntos"])
        p.cambiar_animo(3)
    r = p.relacion(a["pid"])
    r["citas"] = r.get("citas", 0) + (1 if a["puntos"] >= 4 else 0)
    p.decir((motivo + " " if motivo else "") + (f"{a['nombre']} se despide. Lo ha pasado bien contigo." if a["puntos"] >= 4 else f"{a['nombre']} se despide."))


def paso_acompanante(p, dt):
    """Cada fotograma: te sigue, cuenta el paseo y reacciona a los sitios a los que le llevas."""
    import math
    a = p.acompanante
    j = p.j
    x, y = p.pos()
    d = math.hypot(a["x"] - x, a["y"] - y)
    if j.veh:
        a["x"], a["y"] = x, y
    elif d > 3.0:
        paso = min(d - 2.5, (6.5 if d > 12 else 4.0) * dt)
        a["x"] += (x - a["x"]) / d * paso
        a["y"] += (y - a["y"]) / d * paso
        a["t_paso"] -= dt
        if a["t_paso"] <= 0:
            a["t_paso"] = 0.45
            p.son("paso_npc", xy=(a["x"], a["y"]), ref=4, maxd=40, vol=0.8)
    a["metros"] += math.hypot(x - a["px"], y - a["py"]) if math.hypot(x - a["px"], y - a["py"]) < 30 else 0.0
    a["px"], a["py"] = x, y
    if a["metros"] >= 400 and a["puntos"] < 8:                       # el paseo en sí también cuenta
        a["metros"] = 0.0
        a["puntos"] += 1
    if j.estrellas >= 2 and "susto" not in a["sitios"]:
        a["sitios"].append("susto")
        a["puntos"] -= 3
        p.decir(f"{a['nombre']} se asusta con la policía detrás. No era el plan.")
    if p.dia * 1440 + p.reloj > a["hasta"]:
        terminar_paseo(p, "Se ha hecho tarde.")


def visita_con_acompanante(p, lugar):
    """Al entrar en un sitio con tu acompañante: si es un buen plan, le gusta. Si es donde estaba, se queda."""
    a = p.acompanante
    if not a:
        return
    if lugar.id == a["lugar"] and (a["puntos"] or a["metros"] > 60):
        terminar_paseo(p, f"Dejas a {a['nombre']} donde estaba.")
        return
    if lugar.tipo in ("comida", "pizzeria", "bar", "taberna", "cine", "feria", "casino", "hotel") and lugar.id not in a["sitios"] and lugar.id != a["lugar"]:
        a["sitios"].append(lugar.id)
        a["puntos"] += 4
        p.cambiar_animo(2)
        p.decir(f"A {a['nombre']} le gusta el plan: {lugar.nombre}.")


# ============================================================ la siete y media, en bares y tabernas
PALOS = ("oros", "copas", "espadas", "bastos")
FIGURAS = {10: "sota", 11: "caballo", 12: "rey"}


def baraja(azar):
    """Baraja española de cuarenta cartas, barajada: (nombre, valor). Las figuras valen medio punto."""
    cartas = [(f"{'as' if n == 1 else FIGURAS.get(n, str(n))} de {palo}", 0.5 if n >= 10 else float(n)) for palo in PALOS for n in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)]
    azar.shuffle(cartas)
    return cartas


def _puntos_txt(x):
    entero, medio = int(x), x - int(x) > 0.1
    return (f"{entero} y media" if entero else "media") if medio else str(entero)


def siete_y_media(p, Menu, Opcion, azar=None):
    """Una mano contra la banca: pedir cartas sin pasarse de siete y media. La banca gana los empates."""
    import random
    azar = azar or random
    app = p.app
    j = p.j
    est = {"apuesta": 0, "mazo": [], "mias": 0.0, "fin": True}

    def cerrar_mano(texto, gano):
        est["fin"] = True
        if gano > 0:
            p.dar_dinero(gano)
            app.son("dinero")
        else:
            app.son("error")
        app.decir(texto + f" Tienes {j.dinero} euros.", True)
        m.refrescar(False)

    def apostar(n):
        def f():
            if not est["fin"]:
                return
            if not p.pagar(n):
                return
            est.update({"apuesta": n, "mazo": baraja(azar), "mias": 0.0, "fin": False})
            carta()
        return f

    def carta():
        if est["fin"]:
            return
        nombre, valor = est["mazo"].pop()
        est["mias"] += valor
        app.son("menu_mover")
        if est["mias"] > 7.5:
            cerrar_mano(f"{nombre.capitalize()}. Llevas {_puntos_txt(est['mias'])}: te has pasado. Pierdes {est['apuesta']} euros.", 0)
        else:
            app.decir(f"{nombre.capitalize()}. Llevas {_puntos_txt(est['mias'])}.", True)
            m.refrescar(False)

    def plantarse():
        if est["fin"]:
            return
        banca, cartas = 0.0, []
        while banca < est["mias"] and banca <= 7.5:
            nombre, valor = est["mazo"].pop()
            banca += valor
            cartas.append(nombre)
        relato = f"Te plantas con {_puntos_txt(est['mias'])}. La banca saca {', '.join(cartas)}: {_puntos_txt(banca)}."
        if banca > 7.5:
            doble = est["mias"] == 7.5
            cerrar_mano(relato + f" Se pasa. Ganas {est['apuesta'] * (3 if doble else 2)} euros" + (", el doble por hacer siete y media." if doble else "."), est["apuesta"] * (3 if doble else 2))
        else:
            cerrar_mano(relato + f" La banca gana. Pierdes {est['apuesta']} euros.", 0)

    def ops():
        if est["fin"]:
            return [Opcion(f"Apostar {n} euros", apostar(n), ayuda="Te dan una carta. Pide más o plántate. Las figuras valen medio punto y las demás, su número. Si pasas de siete y media, pierdes. "
                           "Cuando te plantas, la banca saca cartas hasta igualarte o pasarse: si te iguala, gana ella. Ganar paga el doble de lo apostado; ganar con siete y media justas, el triple.")
                    for n in (10, 50, 200)] + [Opcion("Levantarte de la mesa", lambda: app.cerrar(m))]
        return [Opcion(lambda: f"Pedir carta. Llevas {_puntos_txt(est['mias'])}", carta), Opcion("Plantarte", plantarse)]
    m = Menu(app, lambda: f"Siete y media. Tienes {j.dinero} euros", ops, intro="Baraja española. Elige cuánto apuestas")
    app.abrir(m)
    return m, est


def con_cartas(p, menu, Menu, Opcion):
    """Añade la mesa de cartas al menú de un bar o una taberna."""
    fuente = menu._fuente
    from .menus import SALIDAS

    def ops():
        lista = list(fuente() if callable(fuente) else fuente)
        if any(o.texto.startswith("Jugar a la siete y media") for o in lista):
            return lista
        o = Opcion("Jugar a la siete y media", lambda: siete_y_media(p, Menu, Opcion),
                   ayuda="Un juego de cartas con baraja española contra la banca. Se apuestan diez, cincuenta o doscientos euros.")
        from . import menus_juego, mesa
        nuevas = [o,
                  Opcion("Jugar al dominó", lambda: mesa.domino(p, Menu, Opcion),
                         ayuda="Dominó de dos contra un parroquiano. Se apuestan veinte o cien euros."),
                  Opcion("Jugar a los chinos", lambda: mesa.chinos(p, Menu, Opcion),
                         ayuda="Cada uno esconde monedas en el puño y dice cuántas hay entre los dos. Se apuestan diez o cincuenta euros."),
                  Opcion("Echar unas monedas a la tragaperras", lambda: menus_juego._tragaperras(p),
                         ayuda="La máquina del rincón. La misma que hay en el casino.")]
        donde = len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista)
        lista[donde:donde] = nuevas
        return lista
    menu._fuente = ops
    menu.refrescar(False)
