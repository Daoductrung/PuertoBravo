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
                self.app.son(("paso_acera0", "paso_acera1")[n % 2], vol=0.5, pan=0.5 * paso)
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
