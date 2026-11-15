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
MEJORAS = {
    "motor": ("Motor", 900, "Más velocidad punta y más aceleración. Se oye: el motor suena más agudo."),
    "frenos": ("Frenos", 500, "Frena en menos metros."),
    "blindaje": ("Blindaje", 700, "Aguanta más golpes y más disparos."),
}
NIVEL_MAX = 3


def nivel(v, cual):
    return int(getattr(v, "mejoras", {}).get(cual, 0))


def precio(v, cual):
    return MEJORAS[cual][1] * (nivel(v, cual) + 1)


def factor_velocidad(v):
    return 1.0 + 0.07 * nivel(v, "motor")


def factor_aceleracion(v):
    return 1.0 + 0.12 * nivel(v, "motor")


def factor_frenada(v):
    return 1.0 + 0.15 * nivel(v, "frenos")


def factor_tono(v):
    return 1.0 + 0.04 * nivel(v, "motor")


def poner(v, mejoras):
    """Deja el vehículo con las mejoras dadas (al comprarlas o al sacarlo de un garaje)."""
    mejoras = {k: max(0, min(NIVEL_MAX, int(n))) for k, n in dict(mejoras or {}).items() if k in MEJORAS}
    antes = nivel(v, "blindaje")
    v.mejoras = mejoras
    base = float(v.modelo["salud"])
    nueva = base * (1.0 + 0.25 * mejoras.get("blindaje", 0))
    if nueva != v.salud_max:
        v.salud = min(nueva, v.salud + max(0.0, nueva - base * (1.0 + 0.25 * antes)))
        v.salud_max = nueva


def resumen(v):
    partes = [f"{MEJORAS[k][0].lower()} nivel {n}" for k, n in getattr(v, "mejoras", {}).items() if n]
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
            elif n >= NIVEL_MAX:
                app.decir(f"{MEJORAS[cual][0]} ya está al máximo.", True)
            elif p.pagar(precio(v, cual)):
                m = dict(getattr(v, "mejoras", {}))
                m[cual] = n + 1
                poner(v, m)
                p.son("reparar", cat="interfaz")
                app.decir(f"{MEJORAS[cual][0]} mejorado al nivel {n + 1} de {NIVEL_MAX}. {resumen(v)}.", True)
        return f

    def texto(cual):
        def f():
            n = nivel(v, cual)
            return f"Mejorar {MEJORAS[cual][0].lower()}: nivel {n} de {NIVEL_MAX}" + (f". Subir cuesta {precio(v, cual)} euros" if n < NIVEL_MAX else ". Al máximo")
        return f
    return [Opcion(texto(k), comprar(k), ayuda=MEJORAS[k][2] + " Las mejoras van con este vehículo: se conservan en el garaje.") for k in MEJORAS]


# ============================================================ banda propia
PRECIO_RECLUTA = 400
SUELDO = 60
TOPE_BANDA = 6
NOMBRES_BANDA = ["Los del Puerto", "La Cuadrilla", "Los Mareas", "La Peña del Muelle", "Los Faroles"]


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
    if not p.pagar(PRECIO_RECLUTA):
        return False, ""
    j.banda += 1
    if not j.banda_nombre:
        j.banda_nombre = random.choice(NOMBRES_BANDA)
    p.son("pareja", cat="interfaz", vol=0.5)
    return True, f"Uno más en {j.banda_nombre}. Ya sois {j.banda} además de ti. Cada uno cobra {SUELDO} euros cada medianoche."


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
    total = SUELDO * j.banda
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
        Opcion(lambda: f"Reclutar a alguien: {PRECIO_RECLUTA} euros. Tienes {j.dinero}", hacer(reclutar),
               ayuda=f"Cada territorio te deja mantener a uno más, hasta {TOPE_BANDA}. Cada miembro cobra {SUELDO} euros cada medianoche; si no puedes pagar, se va uno."),
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


class Interior:
    """Recorrer una casa tuya: flechas izquierda y derecha para ir de una habitación a otra, Intro para usarla."""
    pausa_mundo = True

    def __init__(self, p, lugar, acciones):
        self.p, self.app, self.l, self.acciones = p, p.app, lugar, acciones
        self.habitaciones = list(HABITACIONES)
        if int(lugar.get("garaje", 0)):
            self.habitaciones.append(("el garaje", f"Sitio para {int(lugar.get('garaje', 0))} vehículos. Huele a gasolina.", "garaje"))
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
                self.app.decir("Pared. No hay más casa por ahí.", True)
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
            self.app.decir("Estás dentro de tu casa. Flechas izquierda y derecha para ir de una habitación a otra, Intro para usar la habitación en la que estás y Escape para salir.", True)
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
            p.cambiar_animo(4)
            app.son("pasan_horas")
            app.decir(f"Te sientas un rato a ver la tele. Te sube el ánimo. Son las {p.hora_txt()}.", True)
        elif que == "cocina":
            if getattr(j, "dia_nevera", -1) == p.dia:
                app.decir("Hoy ya te has comido lo que había en la nevera. Mañana habrá más.", True)
            else:
                j.dia_nevera = p.dia
                j.salud = min(j.salud_max, j.salud + 25)
                p.son("comer", cat="interfaz")
                app.decir(f"Te preparas algo con lo que hay en la nevera. Salud {int(j.salud)}.{p.necesidades_txt()}", True)
        elif que == "bano":
            p.cambiar_animo(2)
            app.son("salpicadura", vol=0.5)
            app.decir("Una ducha caliente. Sales como nuevo.", True)
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
_PUERTA = ("la puerta", "Por aquí se sale.", "salir")
_ASEO = ("los aseos", "Un lavabo y un espejo.", "aseo")
SALAS = {
    "bar": [_PUERTA, ("la barra", "Tazas, botellas y la cafetera silbando. Aquí se pide.", "mostrador"), ("las mesas", "Cuatro mesas y gente hablando bajo.", "escuchar"),
            ("la máquina del rincón", "Una tragaperras que canta sola.", "mirar"), _ASEO],
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
                  ("el tablón", "Carteles de personas buscadas y avisos.", "mirar")],
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
    "loteria": [_PUERTA, ("la ventanilla", "Décimos colgados y un bombo pequeño. Aquí se compra.", "mostrador"), ("el tablón de premios", "Los números premiados de la semana.", "mirar")],
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
    "empleo": [_PUERTA, ("la mesa de atención", "Un ordenador y un montón de impresos. Aquí te atienden.", "mostrador"), ("el tablón de ofertas", "Papeles con trabajos, sujetos con chinchetas.", "mirar"),
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


def salas_de(lugar):
    return SALAS.get(getattr(lugar, "tipo", ""))


class Local(Interior):
    """Recorrer por dentro una tienda, un bar, un banco o cualquier otro local: de sala en sala con las flechas."""

    def __init__(self, p, lugar):
        self.p, self.app, self.l, self.acciones = p, p.app, lugar, {}
        self.habitaciones = list(salas_de(lugar) or [_PUERTA])
        self.i = 0
        self.oidas = 0

    def al_entrar(self):
        self.app.mez.entorno = "nave" if self.l.tipo in ("taller", "desguace", "concesionario", "nautica", "gimnasio") else "interior"
        nombre, desc, _ = self.habitaciones[self.i]
        self.app.decir(f"{self.l.nombre}, por dentro. Estás en {nombre}. {desc} Flechas izquierda y derecha para moverte, Intro para usar el sitio donde estás, Escape para volver.", True)

    def _usar(self):
        p, app = self.p, self.app
        nombre, desc, que = self.habitaciones[self.i]
        if que in ("salir", "mostrador"):
            app.son("menu_atras")
            app.cerrar(self)
        elif que == "sentarse":
            p.pasar_horas(0.5)
            p.cambiar_animo(2)
            app.son("pasan_horas")
            app.decir(f"Te sientas un rato. Son las {p.hora_txt()}.", True)
        elif que == "escuchar":
            import random
            self.oidas += 1
            app.son("murmullo", vol=0.5)
            app.decir("Pones el oído. " + random.choice(OIDO), True)
        elif que == "aseo":
            p.cambiar_animo(1)
            app.son("salpicadura", vol=0.5)
            app.decir("Te lavas la cara. Mejor.", True)
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
        o = Opcion("Recorrer el local por dentro", lambda: p.app.abrir(Local(p, lugar)),
                   ayuda="Entras y vas de una sala a otra con las flechas izquierda y derecha. En el mostrador vuelves a este menú, que es donde se compra o se pide.")
        lista.insert(len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista), o)
        return lista
    menu._fuente = ops
    menu.refrescar(False)
