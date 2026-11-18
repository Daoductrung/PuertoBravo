"""Pantallas especiales: explorador de mapa con cursor virtual y galería de tiro."""
import math
import random

import pygame

from . import mundo as M


class ExploradorMapa:
    """Recorre el mapa con un cursor, sin mover al personaje: para aprenderse la ciudad."""
    pausa_mundo = True

    def __init__(self, app, p):
        self.app = app
        self.p = p
        self.m = p.mundo
        x, y = p.pos()
        self.mar = self.m.tipo == "mar"
        if self.mar:
            self.x, self.y = round(x / 100.0) * 100.0, round(y / 100.0) * 100.0
        else:
            self.i = self.m._idx(x, self.m.NX)
            self.j = self.m._idx(y, self.m.NY)
        self.cerca = []
        self.k = -1
        self.foco = None

    def _xy(self):
        return (self.x, self.y) if self.mar else (self.i * M.B, self.j * M.B)

    def _describir(self):
        x, y = self._xy()
        self.cerca = sorted((l for l in self.m.lugares.values() if math.hypot(l.x - x, l.y - y) <= (260 if self.mar else 72)),
                            key=lambda l: math.hypot(l.x - x, l.y - y))
        self.k = -1
        self.foco = None
        px, py = self.p.pos()
        aqui = " Estás aquí." if math.hypot(px - x, py - y) < (60 if self.mar else 46) else ""
        n = len(self.cerca)
        lug = "ningún lugar cerca" if n == 0 else "1 lugar cerca" if n == 1 else f"{n} lugares cerca"
        if self.mar:
            return f"{self.m.describir(x, y)}. {lug}.{aqui}"
        b = self.m.barrio(min(max(x, 1), self.m.ancho - 1), min(max(y, 1), self.m.alto - 1))
        return f"Cruce de {self.m.calles[self.j]} con {self.m.avenidas[self.i]}. {b['nombre']}. {lug}.{aqui}"

    def al_entrar(self):
        self.app.decir("Explorador de mapa. Las flechas mueven el cursor de cruce en cruce. Tabulador recorre los lugares cercanos. "
                       "Intro marca el destino en el GPS. D dice la distancia desde donde estás. Escape sale. " + self._describir(), True)

    def tecla(self, ev):
        k = ev.key
        mov = {pygame.K_UP: (0, 1), pygame.K_DOWN: (0, -1), pygame.K_RIGHT: (1, 0), pygame.K_LEFT: (-1, 0)}.get(k)
        if mov:
            if self.mar:
                nx, ny = self.x + mov[0] * 100, self.y + mov[1] * 100
                if 0 <= nx <= self.m.ancho and 0 <= ny <= self.m.alto:
                    self.x, self.y = nx, ny
                    self.app.son("cursor_mapa", pan=mov[0] * 0.7)
                    self.app.decir(self._describir(), True)
                else:
                    self.app.son("menu_borde")
                    self.app.decir("Fin del mapa.", True)
            else:
                ni, nj = self.i + mov[0], self.j + mov[1]
                if 0 <= ni < self.m.NX and 0 <= nj < self.m.NY:
                    self.i, self.j = ni, nj
                    self.app.son("cursor_mapa", pan=mov[0] * 0.7)
                    self.app.decir(self._describir(), True)
                else:
                    self.app.son("menu_borde")
                    self.app.decir("Fin de la localidad.", True)
        elif k == pygame.K_TAB:
            if not self.cerca:
                self.app.decir("No hay lugares junto a este punto.", True)
                return
            paso = -1 if ev.mod & pygame.KMOD_SHIFT else 1
            self.k = (self.k + paso) % len(self.cerca)
            l = self.cerca[self.k]
            self.foco = l
            x, y = self._xy()
            d = math.hypot(l.x - x, l.y - y)
            visto = "" if l.id in self.p.j.visitados else ", sin visitar"
            self.app.son("menu_mover")
            self.app.decir(f"{l.nombre}, {M.metros(d)} al {M.cardinal(M.rumbo_a(l.x - x, l.y - y))} del cursor{visto}. {self.k + 1} de {len(self.cerca)}.", True)
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.app.son("menu_ok")
            self.app.cerrar(self)
            if self.foco:
                self.p.gps_a_lugar(self.foco)
            else:
                x, y = self._xy()
                nombre = "el punto marcado" if self.mar else f"el cruce de {self.m.calles[self.j]} con {self.m.avenidas[self.i]}"
                self.p.fijar_gps(x, y, nombre, radio=30 if self.mar else 12)
        elif k == pygame.K_d:
            x, y = self._xy()
            self.app.decir("El cursor está: " + self.p.situar(x, y, "este punto") + ".", True)
        elif k == pygame.K_n:
            if self.foco:
                self.app.decir(f"{self.foco.nombre}. {self.foco.desc}", True)
            elif not self.mar:
                x, y = self._xy()
                b = self.m.barrio(min(max(x, 1), self.m.ancho - 1), min(max(y, 1), self.m.alto - 1))
                self.app.decir(f"{b['nombre']}. {self.p.barrio_desc(b, self.m)}", True)
        elif k == pygame.K_HOME:
            px, py = self.p.pos()
            if self.mar:
                self.x, self.y = round(px / 100.0) * 100.0, round(py / 100.0) * 100.0
            else:
                self.i, self.j = self.m._idx(px, self.m.NX), self.m._idx(py, self.m.NY)
            self.app.decir("Cursor en tu posición. " + self._describir(), True)
        elif k == pygame.K_F1:
            self.app.decir("Flechas: mover el cursor. Tabulador: lugares cercanos al cursor. N: descripción. D: distancia desde tu posición. "
                           "Inicio: volver a donde estás. Intro: marcar en el GPS. Escape: salir.", True)
        elif k == pygame.K_ESCAPE:
            self.app.son("menu_atras")
            self.app.cerrar(self)

    def actualizar(self, dt):
        pass


class TiroAlBlanco:
    """Galería de tiro: suena una diana a la izquierda, al centro o a la derecha y hay que pulsar esa flecha."""
    pausa_mundo = True
    RONDAS = 10

    def __init__(self, app, p):
        self.app = app
        self.p = p
        self.ronda = 0
        self.aciertos = 0
        self.estado = "intro"
        self.t = 2.5
        self.dir = 0

    def al_entrar(self):
        self.app.decir("Galería de tiro. Sonarán diez dianas: a la izquierda, al centro o a la derecha. "
                       "Pulsa enseguida flecha izquierda, flecha arriba o flecha derecha según de dónde venga el sonido. Preparados.", True)
        self.t = 9.0

    def _siguiente(self):
        self.ronda += 1
        if self.ronda > self.RONDAS:
            self._fin()
            return
        self.estado = "espera"
        self.t = random.uniform(0.9, 2.0)

    def _fin(self):
        p = self.p
        n = self.aciertos
        premio = p.precio("tiro_premio_9", 200) if n >= 9 else p.precio("tiro_premio_7", 80) if n >= 7 else 0
        self.app.cerrar(self)
        p.ganar_xp("punteria", n * 6)
        txt = f"Fin de la tanda: {n} dianas de {self.RONDAS}."
        if premio:
            p.dar_dinero(premio)
            txt += f" Premio de {premio} euros."
        else:
            txt += " Con siete o más hay premio."
        p.decir(txt, True)

    def actualizar(self, dt):
        self.t -= dt
        if self.t > 0:
            return
        if self.estado == "intro":
            self._siguiente()
        elif self.estado == "espera":
            self.estado = "diana"
            self.dir = random.choice([-1, 0, 1])
            self.t = max(0.75, 1.3 - 0.04 * self.ronda)
            self.app.son("diana", pan=self.dir * 0.95, vol=0.9)
            self.app.vibrar(0.8 if self.dir <= 0 else 0.0, 0.8 if self.dir >= 0 else 0.0, 150)
        elif self.estado == "diana":
            self.app.son("error", vol=0.5)
            self._siguiente()

    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            self.app.cerrar(self)
            self.p.decir("Dejas la galería de tiro.", True)
            return
        d = {pygame.K_LEFT: -1, pygame.K_UP: 0, pygame.K_RIGHT: 1}.get(k)
        if d is None:
            return
        if self.estado == "intro":
            self.app.voz.callar()
            self.t = 0.3
        elif self.estado == "diana":
            if d == self.dir:
                self.aciertos += 1
                self.p.son("disparo_pistola", cat="interfaz", vol=0.4, pan=d * 0.8)
                self.app.son("diana_ok", pan=d * 0.9)
            else:
                self.app.son("error", vol=0.5)
            self._siguiente()
        elif self.estado == "espera":
            self.app.son("error", vol=0.5)
            self.t = random.uniform(0.9, 1.8)


class SimonSonoro:
    """Memoria de sonidos: la máquina toca una secuencia de cuatro notas y hay que repetirla con las flechas."""
    pausa_mundo = True
    TECLAS = {pygame.K_UP: 0, pygame.K_RIGHT: 1, pygame.K_DOWN: 2, pygame.K_LEFT: 3}
    PAN = {0: 0.0, 1: 0.9, 2: 0.0, 3: -0.9}

    def __init__(self, app, p):
        self.app = app
        self.p = p
        self.sec = []
        self.pos = 0
        self.estado = "intro"
        self.t = 9.0
        self.k = 0

    def al_entrar(self):
        self.app.decir("Memoria de sonidos. Cada flecha tiene su nota: arriba la más aguda, abajo la más grave, derecha e izquierda suenan por su lado. "
                       "Escucha la secuencia y repítela. Cada ronda añade una nota. Pulsa una flecha para probarlas, y empezamos.", True)

    def _tocar(self, n):
        self.app.son(f"simon_{n}", pan=self.PAN[n], vol=0.9)

    def _nueva_ronda(self):
        self.sec.append(random.randrange(4))
        self.estado = "muestra"
        self.k = 0
        self.t = 0.9

    def _fin(self):
        p = self.p
        rondas = len(self.sec) - 1
        premio = p.precio("memoria_premio_12", 1000) if rondas >= 12 else p.precio("memoria_premio_8", 250) if rondas >= 8 else p.precio("memoria_premio_5", 60) if rondas >= 5 else 0
        self.app.cerrar(self)
        p.j.stats["simon"] = max(p.j.stats.get("simon", 0), rondas)
        txt = f"Fallo. Has aguantado {rondas} rondas."
        if premio:
            p.dar_dinero(premio)
            txt += f" Premio de {premio} euros."
        else:
            txt += " Con cinco rondas hay premio."
        p.decir(txt, True)

    def actualizar(self, dt):
        self.t -= dt
        if self.t > 0:
            return
        if self.estado == "intro":
            self._nueva_ronda()
        elif self.estado == "muestra":
            if self.k < len(self.sec):
                self._tocar(self.sec[self.k])
                self.k += 1
                self.t = max(0.3, 0.6 - 0.02 * len(self.sec))
            else:
                self.estado = "turno"
                self.pos = 0
                self.t = 6.0
        elif self.estado == "turno":
            self.app.son("error", vol=0.5)
            self._fin()

    def tecla(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self.app.cerrar(self)
            self.p.decir("Dejas la máquina.", True)
            return
        n = self.TECLAS.get(ev.key)
        if n is None:
            return
        if self.estado == "intro":
            self.app.voz.callar()
            self._tocar(n)
            self.t = 1.5
        elif self.estado == "turno":
            self._tocar(n)
            if n != self.sec[self.pos]:
                self.app.son("error", vol=0.5)
                self._fin()
                return
            self.pos += 1
            self.t = 6.0
            if self.pos >= len(self.sec):
                self.estado = "pausa"
                self.t = 0.8
        elif self.estado == "pausa":
            pass

    def _despues_pausa(self):
        self._nueva_ronda()


# la pausa entre rondas reutiliza el temporizador
_act_simon = SimonSonoro.actualizar


def _act(self, dt):
    if self.estado == "pausa":
        self.t -= dt
        if self.t <= 0:
            self.app.son("diana_ok", vol=0.5)
            self._nueva_ronda()
        return
    _act_simon(self, dt)


SimonSonoro.actualizar = _act


class BuscaTesoro:
    """Frío o caliente con el oído: un pitido se acelera y se agudiza al acercarte al tesoro."""
    pausa_mundo = True
    N = 9

    def __init__(self, app, p, buceo):
        self.app = app
        self.p = p
        self.buceo = buceo
        self.x = self.y = self.N // 2
        while True:
            self.tx, self.ty = random.randrange(self.N), random.randrange(self.N)
            if abs(self.tx - self.x) + abs(self.ty - self.y) >= 4:
                break
        self.tiempo = 45.0
        self.intentos = 3
        self.t_ping = 1.0
        self.empezado = False

    def al_entrar(self):
        que = "Buceas hasta el fondo" if self.buceo else "Enciendes el detector de metales"
        self.app.decir(f"{que}. Muévete con las flechas: el pitido suena más rápido y más agudo cuanto más cerca estás del tesoro, y sale del lado donde está. "
                       f"Cuando creas que estás encima, pulsa Intro para {'buscar entre la arena' if self.buceo else 'cavar'}. Tienes 45 segundos y tres intentos.", True)

    def _dist(self):
        return math.hypot(self.tx - self.x, self.ty - self.y)

    def actualizar(self, dt):
        if not self.empezado:
            return
        self.tiempo -= dt
        if self.tiempo <= 0:
            self._fin(False, "Se acabó el aire. Subes con las manos vacías." if self.buceo else "Se acabó la batería del detector.")
            return
        self.t_ping -= dt
        if self.t_ping <= 0:
            d = self._dist()
            pan = max(-1.0, min(1.0, (self.tx - self.x) / 3.0))
            self.app.son("sonar", pan=pan, tono=max(0.5, 1.9 - d * 0.16), vol=0.8)
            self.t_ping = 0.12 + d * 0.11

    def _fin(self, ok, texto):
        p = self.p
        self.app.cerrar(self)
        if ok:
            premio = random.choice([120, 180, 250, 250, 400, 400, 700, 1500])
            p.j.stats["tesoros"] = p.j.stats.get("tesoros", 0) + 1
            p.son("recoger", cat="interfaz")
            p.dar_dinero(premio)
            p.app.vibrar(0.6, 1.0, 400)
            cosa = random.choice(["un cofre pequeño", "un collar de perlas", "unas monedas antiguas", "un reloj de oro", "una figura de plata"])
            p.decir(f"¡Encuentras {cosa}! Vale {premio} euros.", True)
        else:
            p.decir(texto, True)

    def tecla(self, ev):
        k = ev.key
        mov = {pygame.K_UP: (0, 1), pygame.K_DOWN: (0, -1), pygame.K_RIGHT: (1, 0), pygame.K_LEFT: (-1, 0)}.get(k)
        if mov:
            self.empezado = True
            nx, ny = self.x + mov[0], self.y + mov[1]
            if 0 <= nx < self.N and 0 <= ny < self.N:
                self.x, self.y = nx, ny
                self.app.son("cursor_mapa", pan=mov[0] * 0.6, vol=0.5)
                self.t_ping = min(self.t_ping, 0.15)
            else:
                self.app.son("menu_borde")
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.empezado = True
            if self.x == self.tx and self.y == self.ty:
                self._fin(True, "")
            else:
                self.intentos -= 1
                self.app.son("error", vol=0.5)
                if self.intentos <= 0:
                    self._fin(False, "Nada. Te has quedado sin intentos.")
                else:
                    d = self._dist()
                    pista = "Estás al lado." if d < 1.6 else "Estás cerca." if d < 3 else "Estás lejos."
                    self.app.decir(f"Aquí no hay nada. {pista} Te quedan {self.intentos} intentos y {int(self.tiempo)} segundos.", True)
        elif k == pygame.K_ESCAPE:
            self._fin(False, "Lo dejas.")
        elif k == pygame.K_F1:
            self.app.decir(f"Flechas para moverte, Intro para buscar. Te quedan {self.intentos} intentos y {int(self.tiempo)} segundos.", True)


class Viaje:
    """El trayecto de un taxi o de un autobús: se oye el motor, la calzada y la radio durante un rato, y luego llegas.

    Intro o Escape llegan ya. Cualquier otra tecla dice cuánto falta.
    """
    pausa_mundo = True

    def __init__(self, app, segundos, al_llegar, autobus=False, destino="", vuelo=False, medio=None):
        self.app, self.total, self.al_llegar, self.autobus, self.destino = app, max(4.0, float(segundos)), al_llegar, autobus, destino
        self.vuelo = vuelo
        self.medio = medio              # "tren" o "tranvia"; None para taxi, autobús y vuelo
        self.t = 0.0
        self.canales = []
        self.motor = None
        self.t_suceso = random.uniform(5, 9)
        self.avisado = False
        self.hecho = False
        self.con_tren = bool(autobus) and random.random() < 0.75      # en autobús, entre localidades: si en este trayecto pasa un tren junto a la carretera
        self.tren_en = random.uniform(0.25, 0.55)       # y en qué momento
        self.tren_paso = None

    def al_entrar(self):
        app = self.app
        if self.motor is not None:
            return
        if self.medio in ("tren", "tranvia", "avion", "avioneta"):
            app.son({"tren": "tren_silbato", "tranvia": "tranvia_campana", "avion": "avion_despegue", "avioneta": "puerta_coche"}[self.medio], vol=0.7)
            self.motor = app.son("motor_avioneta" if self.medio == "avioneta" else self.medio, bucle=True, vol=0.45)
            self.canales = [self.motor]
            app.decir({"tren": "El tren sale de la estación", "tranvia": "El tranvía arranca", "avion": "El avión acelera por la pista y despega",
                       "avioneta": "La avioneta carretea por la pista y despega"}[self.medio] +
                      f", camino de {self.destino}. Pulsa Intro si quieres llegar ya.", True)
            return
        app.son("puerta_coche")
        if self.vuelo:
            self.motor = app.son("motor_helicoptero", bucle=True, vol=0.4)
            self.canales = [self.motor, app.son("viento_playa", bucle=True, vol=0.15)]
        else:
            self.motor = app.son("motor_camion" if self.autobus else "motor_coche", bucle=True, vol=0.32)
            self.canales = [self.motor, app.son("rodadura", bucle=True, vol=0.18)]
        emisora = ""
        try:
            n = len(app.radio.emisoras)
            emisora = app.radio.sintonizar(random.randrange(1, n)) if n > 1 else ""
        except Exception:
            emisora = ""
        quien = "El helicóptero despega" if self.vuelo else "El autobús arranca" if self.autobus else "Subes al taxi"
        radio = f" En la radio, {emisora}." if emisora else ""
        app.decir(f"{quien}, camino de {self.destino}.{radio} Pulsa Intro si quieres llegar ya.", True)

    def _fin(self):
        if self.hecho:
            return
        self.hecho = True
        for c in self.canales:
            c.parar()
        try:
            self.app.radio.apagar()
        except Exception:
            pass
        self.app.cerrar(self)
        self.app.son("puerta_coche")
        self.al_llegar()

    def tecla(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self._fin()
        else:
            self.app.decir(f"Vas de camino a {self.destino}. Quedan unos {max(1, int(self.total - self.t))} segundos. Intro para llegar ya.", True)

    def actualizar(self, dt):
        if self.hecho:
            return
        self.t += dt
        f = self.t / self.total
        # el motor sube al arrancar, se mantiene y baja al llegar
        tono = 0.75 + 0.55 * min(1.0, f / 0.15) if f < 0.8 else 0.75 + 0.55 * max(0.0, (1.0 - f) / 0.2)
        if self.motor is not None:
            self.motor.tono(tono + 0.04 * math.sin(self.t * 1.7))
        self.t_suceso -= dt
        if self.t_suceso <= 0 and f < 0.85 and not self.vuelo and not self.medio:
            self.t_suceso = random.uniform(6, 11)
            self.app.son(random.choice(["claxon_lejano", "intermitente", "cruce", "claxon_lejano"]), vol=0.35, pan=random.uniform(-0.8, 0.8))
        self._tren_al_lado(dt, f)
        if not self.avisado and f >= 0.8:
            self.avisado = True
            self.app.decir("El avión empieza a bajar." if self.medio == "avion" else "La avioneta empieza a bajar hacia la pista." if self.medio == "avioneta" else "Próxima estación." if self.medio == "tren" else "Próxima parada." if self.medio else "Empezáis a bajar." if self.vuelo else "Ya casi estás." if not self.autobus else "Próxima parada.")
        if self.t >= self.total:
            self._fin()

    def _tren_al_lado(self, dt, f):
        """Por carretera, entre una localidad y otra, la vía del tren va junto a la calzada: en casi todos los trayectos
        un tren te alcanza, pasa a tu lado de un oído al otro y se pierde por delante."""
        if self.vuelo or self.medio or not self.con_tren:
            return
        t = self.tren_paso
        if t is None:
            if f >= self.tren_en and self.total - self.t > 9.0:
                lado = random.choice((-1.0, 1.0))
                self.app.son("tren_silbato", vol=0.45, pan=-0.8 * lado)
                c = self.app.son("tren", bucle=True, vol=0.05, pan=-0.9 * lado)
                self.canales.append(c)
                self.tren_paso = {"t": 0.0, "canal": c, "lado": lado}
                self.app.decir("Un tren alcanza al autobús por la vía que va junto a la carretera.")
            return
        if t["canal"] is None:
            return
        t["t"] += dt
        k = t["t"] / 8.0                                     # ocho segundos de un lado al otro
        if k >= 1.0:
            t["canal"].parar()
            t["canal"] = None
            return
        t["canal"].volumen(0.05 + 0.6 * math.sin(math.pi * k))
        t["canal"].pan = t["lado"] * (-0.9 + 1.8 * k)

    def cerrado(self):
        if not self.hecho:                      # si algo cierra la pantalla por fuera, se llega igual
            self._fin()


class LineaTranvia:
    """Un viaje en el tranvía de la ciudad: va de parada en parada, las anuncia, y te bajas donde quieras.

    Intro o Escape: te bajas en la próxima parada. Cualquier otra tecla dice por dónde vas.
    """
    pausa_mundo = True

    def __init__(self, app, paradas, al_bajar, nombre=lambda l: l.nombre):
        self.app, self.paradas, self.al_bajar, self.nombre = app, list(paradas), al_bajar, nombre
        self.i = 0                      # la parada a la que se está llegando
        self.t = 0.0
        self.bajar = False
        self.hecho = False
        self.motor = None
        self.pasadas = 0
        self.tramo = self._duracion(0)

    def _duracion(self, k):
        if k == 0:
            return 7.0
        a, b = self.paradas[k - 1], self.paradas[k]
        return max(5.0, min(14.0, math.hypot(a.x - b.x, a.y - b.y) / 22.0))

    def al_entrar(self):
        if self.motor is not None:
            return
        app = self.app
        app.son("tranvia_campana", vol=0.7)
        self.motor = app.son("tranvia", bucle=True, vol=0.45)
        final = self.paradas[-1]
        app.decir(f"Subes al tranvía. Vas hasta {self.nombre(final)}, {len(self.paradas)} {'parada' if len(self.paradas) == 1 else 'paradas'}. "
                  f"La primera: {self.nombre(self.paradas[0])}. Pulsa Intro cuando quieras bajarte en la próxima.", True)

    def tecla(self, ev):
        if self.hecho:
            return
        prox = self.paradas[self.i]
        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self.bajar = True
            self.app.son("menu_ok")
            self.app.decir(f"Te bajas en la próxima: {self.nombre(prox)}.", True)
        else:
            self.app.decir(f"Vas en el tranvía. Próxima parada: {self.nombre(prox)}, en unos {max(1, int(self.tramo - self.t))} segundos. "
                           f"{'Te bajas en ella.' if self.bajar or self.i == len(self.paradas) - 1 else 'Intro para bajarte en ella.'}", True)

    def actualizar(self, dt):
        if self.hecho:
            return
        self.t += dt
        f = self.t / self.tramo
        if self.motor is not None:                       # arranca, rueda y frena en cada tramo
            self.motor.tono(0.7 + 0.5 * min(1.0, f / 0.25) if f < 0.75 else 0.7 + 0.5 * max(0.0, (1.0 - f) / 0.25))
        if self.t < self.tramo:
            return
        parada = self.paradas[self.i]
        self.pasadas += 1
        if self.bajar or self.i == len(self.paradas) - 1:
            self._fin(parada)
            return
        self.i += 1
        self.t = 0.0
        self.tramo = self._duracion(self.i)
        self.app.son("tranvia_campana", vol=0.6)
        self.app.decir(f"{self.nombre(parada)}. Próxima parada: {self.nombre(self.paradas[self.i])}.")

    def _fin(self, parada):
        if self.hecho:
            return
        self.hecho = True
        if self.motor is not None:
            self.motor.parar()
        self.app.cerrar(self)
        self.app.son("tranvia_campana", vol=0.6)
        self.al_bajar(parada, self.pasadas)

    def cerrado(self):
        if not self.hecho:                               # si algo cierra la pantalla por fuera, te bajas en la próxima
            self._fin(self.paradas[self.i])


def con_trayecto(app):
    """¿Se hace el trayecto o se llega al momento?"""
    return bool(app.cfg["viajes_trayecto"]) and (not app.pruebas or getattr(app, "viajes_en_pruebas", False))


def viajar(app, segundos, al_llegar, autobus=False, destino="", vuelo=False, medio=None):
    """Hace el trayecto si el jugador lo quiere; si no, llega al momento, como antes."""
    if not app.cfg["viajes_trayecto"] or (app.pruebas and not getattr(app, "viajes_en_pruebas", False)):
        al_llegar()
        return
    app.abrir(Viaje(app, segundos, al_llegar, autobus, destino, vuelo, medio))
