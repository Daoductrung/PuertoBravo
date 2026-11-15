"""Dos cosas del contenido para adultos que se juegan, en lugar de leerse: la noche con alguien, paso a paso,
y el laboratorio clandestino.

La noche: el jugador decide qué hace en cada momento y la otra persona responde. Sigue contándose de forma
sensual y sin escenas explícitas; lo que cambia es que ahora actúas tú, y que escuchar lo que la otra persona
quiere, y respetar un «espera», es lo que hace que la noche salga bien. Todas las personas son adultas.

El laboratorio: un oficio ilegal dentro del juego. Es un minijuego de oído, de mantener un tono en su sitio.
No describe ni se parece a ningún proceso real: las sustancias del juego son inventadas, como sus efectos.
"""
import random

import pygame

# ============================================================================ la noche, paso a paso
# Cada persona tiene un ritmo que le gusta. No se dice: se nota en cómo responde.
RITMOS = ("lento", "intenso", "jugando")
MOMENTOS = [
    ("Acabáis de entrar. {n} deja las llaves y te mira.", [
        ("Poner música bajita y servir dos copas", "lento", "{n} se quita los zapatos y se sienta muy cerca de ti."),
        ("Besarle antes de que diga nada", "intenso", "{n} te agarra de la camisa y no te suelta."),
        ("Hacerle una broma y perseguirle por el pasillo", "jugando", "{n} se escapa riéndose y se deja alcanzar.")]),
    ("Estáis muy cerca. Notas su respiración.", [
        ("Acariciarle despacio, sin prisa ninguna", "lento", "{n} cierra los ojos y apoya la frente en la tuya."),
        ("Abrazarle fuerte y dejar que hablen las manos", "intenso", "{n} te busca la boca con hambre."),
        ("Susurrarle una tontería al oído", "jugando", "{n} se ríe contra tu cuello.")]),
    ("{n} te mira a los ojos, esperando.", [
        ("Preguntarle qué le apetece", "pregunta", ""),
        ("Llevarle de la mano al dormitorio", "lento", "{n} te sigue sin soltarte."),
        ("Dejar que sea quien decida", "cede", "{n} sonríe y toma la iniciativa.")]),
    ("La ropa empieza a sobrar.", [
        ("Ir despacio, mirándole", "lento", "{n} te deja hacer y suspira."),
        ("Con prisa, sin pensar", "intenso", "{n} te ayuda, con las manos torpes de ganas."),
        ("Entre risas, enredándoos", "jugando", "Acabáis los dos riéndoos, hechos un lío.")]),
]
ESPERA = ["{n} te pone una mano en el pecho. «Espera. Más despacio.»", "{n} se aparta un poco. «Un momento. Así no.»"]
QUIERE = {"lento": "«Despacio. Hoy quiero que dure.»", "intenso": "«No pienses tanto. Ven aquí.»", "jugando": "«Sorpréndeme. Hazme reír.»"}


def ritmo_de(nombre, dia):
    """El ritmo que le apetece hoy a esta persona. Cambia de un día a otro, y no es el mismo para todos."""
    return RITMOS[(sum(ord(c) for c in nombre) + int(dia)) % 3]


class Noche:
    """Una noche con alguien, decidida paso a paso. Al terminar llama a al_acabar(sintonia), de 0 a 1."""

    def __init__(self, p, nombre, donde, al_acabar, azar=None):
        self.p, self.app, self.nombre, self.donde, self.al_acabar = p, p.app, nombre, donde, al_acabar
        self.azar = azar or random
        self.ritmo = ritmo_de(nombre, p.dia)
        self.paso = 0
        self.puntos = 0.0
        self.maximo = 0.0
        self.espera = False            # te ha pedido que pares: lo siguiente decide mucho
        self.menu = None

    def empezar(self):
        self._mostrar(f"{self.donde.capitalize()}. ")

    def _mostrar(self, antes=""):
        from .menus import Menu, Opcion
        n = self.nombre
        if self.menu is not None:
            self.app.cerrar(self.menu)
        if self.espera:
            titulo = antes + self.azar.choice(ESPERA).format(n=n)
            ops = [Opcion("Parar, y preguntarle si está bien", lambda: self._responde_espera(True), ayuda="Un espera se respeta. Parar y escuchar es lo que más os acerca."),
                   Opcion("Bajar el ritmo sin decir nada", lambda: self._responde_espera(False), ayuda="Aflojas, pero no preguntas.")]
        elif self.paso >= len(MOMENTOS):
            self._fin(antes)
            return
        else:
            texto, opciones = MOMENTOS[self.paso]
            titulo = antes + texto.format(n=n)
            ops = [Opcion(t, (lambda r=r, d=d: self._elegir(r, d)), ayuda="No hay una respuesta correcta para todo el mundo: fíjate en cómo responde.") for t, r, d in opciones]
        self.menu = Menu(self.app, titulo, ops, escapable=False)
        self.app.abrir(self.menu)

    def _elegir(self, ritmo, dice):
        n = self.nombre
        self.paso += 1
        self.maximo += 1.0
        if ritmo == "pregunta":                              # preguntar siempre acierta, y además te dice lo que quiere
            self.puntos += 1.0
            self._mostrar(f"{n} te lo dice al oído: {QUIERE[self.ritmo]} ")
            return
        if ritmo == "cede":
            self.puntos += 0.7
            self._mostrar(dice.format(n=n) + " ")
            return
        if ritmo == self.ritmo:
            self.puntos += 1.0
            self.app.son("afinidad_sube", vol=0.5)
            self._mostrar(dice.format(n=n) + " Es justo lo que quería. ")
        elif ritmo == "intenso" and self.ritmo == "lento":   # ir más deprisa de lo que quiere: te frena
            self.espera = True
            self._mostrar()
        else:
            self.puntos += 0.4
            self._mostrar(dice.format(n=n) + " Aunque notas que hoy le apetecía otra cosa. ")

    def _responde_espera(self, pregunta):
        n = self.nombre
        self.espera = False
        if pregunta:
            self.puntos += 1.0
            self.app.son("afinidad_sube", vol=0.5)
            self._mostrar(f"Paras. {n} respira, te sonríe y te lo dice: {QUIERE[self.ritmo]} ")
        else:
            self.puntos += 0.2
            self._mostrar(f"Aflojas. {n} no dice nada, pero tarda en volver a acercarse. ")

    def _fin(self, antes):
        from .menus import Dialogo
        s = self.puntos / self.maximo if self.maximo else 0.5
        como = ("Ha sido una de esas noches que se recuerdan: os habéis entendido sin palabras." if s >= 0.8 else
                "Ha estado bien. Os vais conociendo." if s >= 0.5 else "No habéis acabado de encontraros. Otra vez será mejor si le escuchas.")
        self.menu = None
        self.app.abrir(Dialogo(self.app, [("Narrador", antes + "Se apaga la luz. Lo que pasa después es solo vuestro."), ("Narrador", como)],
                               lambda: self.al_acabar(s)))


# ============================================================================ el laboratorio
PRECIO_LAB = 9000
PRECIO_MATERIAL = 180
PRODUCTOS = ("pastillas", "polvo", "cristal")
DURA = 24.0


def puede_montar(p, lugar):
    return p.modo_adulto() and lugar.tipo == "casa" and lugar.id in p.j.propiedades


def opciones_casa(p, lugar, Menu, Opcion):
    """Lo que añade el laboratorio al menú de una casa tuya."""
    if not puede_montar(p, lugar):
        return []
    j = p.j
    app = p.app
    if lugar.id not in j.laboratorios:
        def montar():
            if p.pagar(PRECIO_LAB):
                j.laboratorios.append(lugar.id)
                p.son("reparar", cat="interfaz")
                app.decir("Montas un laboratorio en el cuarto del fondo. Para trabajar en él hace falta material: lo vende cualquier proveedor.", True)
        return [Opcion(f"Montar un laboratorio clandestino aquí: {PRECIO_LAB} euros", montar,
                       ayuda="Un cuarto preparado para fabricar mercancía. Da mucho dinero y muchos problemas: los vecinos huelen cosas, la policía pregunta, y si te equivocas puede arder.")]

    def trabajar(s):
        def f():
            if j.material <= 0:
                app.son("error")
                app.decir("No te queda material. Lo vende cualquier proveedor.", True)
                return
            if p.carga() >= 100:
                app.son("error")
                app.decir("No te cabe más mercancía encima. Vende antes.", True)
                return
            j.material -= 1
            app.abrir(Coccion(p, lugar, s))
        return f
    ops = [Opcion(lambda: f"Laboratorio. Tienes material para {j.material} {'tanda' if j.material == 1 else 'tandas'}")]
    for s in p.dato_adulto("sustancias"):
        if s["id"] in PRODUCTOS:
            ops.append(Opcion(f"Fabricar {s['nombre'].lower()}", trabajar(s),
                              ayuda="Un minijuego de oído. Suenan dos tonos: uno fijo, que es el punto bueno, y otro que se te va. Con flecha arriba y flecha abajo llevas el tuyo "
                                    "hasta igualarlo al fijo, y lo mantienes ahí. Cuanto más tiempo estén iguales, mejor sale la tanda y más unidades sacas. "
                                    "Si lo dejas irse muy arriba mucho rato, puede arder."))
    return [Opcion("Entrar en el laboratorio", lambda: app.abrir(Menu(app, "Laboratorio", ops)),
                   ayuda="Fabricar mercancía para venderla después a los proveedores o por la calle.")]


def opcion_proveedor(p, Opcion):
    """En los proveedores se compra el material."""
    j = p.j

    def comprar():
        if p.pagar(PRECIO_MATERIAL):
            j.material += 1
            p.son("trato", cat="interfaz")
            p.app.decir(f"Material para una tanda. Tienes para {j.material}.", True)
    return Opcion(lambda: f"Material de laboratorio, una tanda: {PRECIO_MATERIAL} euros. Tienes {j.material}", comprar,
                  ayuda="Hace falta para trabajar en un laboratorio. El laboratorio se monta en una casa tuya, desde su menú.")


class Coccion:
    """El minijuego: mantener tu tono igual al tono fijo durante unos segundos."""
    pausa_mundo = True

    def __init__(self, p, lugar, sustancia, azar=None):
        self.p, self.app, self.l, self.s = p, p.app, lugar, sustancia
        self.azar = azar or random
        self.t = 0.0
        self.valor = 0.0               # dónde está tu tono: 0 es el punto bueno
        self.deriva = self.azar.choice((-1, 1)) * 0.25
        self.bien = 0.0                # segundos con el tono en su sitio
        self.alto = 0.0                # segundos muy por encima: peligro
        self.t_tono = 0.0
        self.hecho = False

    def al_entrar(self):
        self.app.decir(f"Empiezas una tanda de {self.s['nombre'].lower()}. Oirás un tono fijo y otro que se mueve. Con flecha arriba y flecha abajo, iguala el tuyo al fijo "
                       f"y mantenlo. Dura {int(DURA)} segundos. Escape lo deja a medias.", True)

    def tecla(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self._fin(abandonada=True)

    def actualizar(self, dt):
        if self.hecho:
            return
        self.t += dt
        t = self.app.teclas
        if pygame.K_UP in t:
            self.valor += 0.9 * dt
        if pygame.K_DOWN in t:
            self.valor -= 0.9 * dt
        if self.azar.random() < dt * 0.5:                    # de vez en cuando cambia hacia dónde se te va
            self.deriva = self.azar.choice((-1, 1)) * self.azar.uniform(0.15, 0.4)
        self.valor = max(-1.5, min(1.5, self.valor + self.deriva * dt))
        if abs(self.valor) < 0.18:
            self.bien += dt
        if self.valor > 0.9:
            self.alto += dt
        self.t_tono -= dt
        if self.t_tono <= 0:
            self.t_tono = 0.45
            self.app.son("tono_libre", vol=0.45, pan=-0.6)                                   # el fijo, a la izquierda
            self.app.son("tono_libre", vol=0.6, pan=0.6, tono=2.0 ** (self.valor * 0.6))     # el tuyo, a la derecha
        if self.t >= DURA:
            self._fin()

    def _fin(self, abandonada=False):
        if self.hecho:
            return
        self.hecho = True
        p, j, app = self.p, self.p.j, self.app
        app.cerrar(self)
        calidad = 0.0 if abandonada else self.bien / DURA
        if not abandonada and self.alto > 6.0 and self.azar.random() < 0.6:
            j.laboratorios.remove(self.l.id) if self.l.id in j.laboratorios else None
            p.son("explosion", cat="interfaz", vol=0.8)
            p.danar_jugador(45, None)
            p.delito(6, "incendio en un laboratorio", siempre=True)
            app.decir("Se te va de las manos y arde. Sales tosiendo, con quemaduras. El laboratorio se ha perdido, y medio barrio ha llamado a la policía.", True)
            return
        if abandonada:
            app.decir("Lo dejas a medias. La tanda se ha echado a perder.", True)
            return
        unidades = max(1, int(round(4 + 12 * calidad)))
        unidades = min(unidades, max(0, 100 - p.carga()))
        j.sustancias[self.s["id"]] = j.sustancias.get(self.s["id"], 0) + unidades
        j.stats["fabricado"] = j.stats.get("fabricado", 0) + unidades
        p.son("trato", cat="interfaz")
        nota = "Una tanda limpia" if calidad >= 0.6 else "Una tanda normal" if calidad >= 0.3 else "Una tanda floja"
        app.decir(f"{nota}: {unidades} de {self.s['nombre'].lower()}. Llevas {j.sustancias[self.s['id']]}. Véndelo a un proveedor o por la calle.", True)
        if self.azar.random() < 0.15:
            p.delito(3, "olores sospechosos", siempre=True)
            p.decir("Un vecino ha notado el olor y ha llamado a la policía.")

    def cerrado(self):
        pass
