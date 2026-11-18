"""La partida en curso: movimiento a pie, orientación, GPS, radar y ambiente."""
import math
import random
import time

import pygame

from . import genero, gente, registro
from . import mundo as M
from .combate import Combate
from .conduccion import Conduccion
from .adultos import Adultos
from .azar import Azar
from .entidades import Jugador, Objeto, Persona, Vehiculo
from .extras import Extras
from .extras2 import Extras2
from .extras3 import Extras3
from .charla import Charla
from .intimidad import Intimidad
from .misiones import Misiones
from .necesidades import Necesidades
from .combustible import Combustible
from .realismo import Realismo
from .misvehiculos import MisVehiculos
from .calle import Calle
from .guerra import Guerra
from .domicilio import Domicilio
from .compra import Compra
from .atracos import Atracos
from .pactos import Pactos
from .reconquista import Reconquista
from .contratos import Contratos
from .reacciones import Reacciones
from .convivencia import Convivencia
from .agente import Agente
from .online import Online
from .enlinea import EnLinea
from .trabajos import Trabajos
from .vida import Vida

UMBRAL_ESTRELLAS = [1, 4, 8, 13, 20]

# ------------------------------------------------------------------ formato de las partidas guardadas
# Cada vez que cambia lo que se guarda, sube el número y se añade aquí cómo convertir una partida del formato anterior.
FORMATO = 3


def _a_formato_3(d):
    """La 1.6.2 añade las decisiones tomadas, los fallos por misión, las misiones saltadas y el momento del guardado."""
    d.setdefault("fallos", {})
    d.setdefault("decisiones", {})
    d.setdefault("saltadas", [])
    j = d.setdefault("jugador", {})
    j.setdefault("rep_bandas", {})
    return d


CONVERSIONES = {2: _a_formato_3}


class PartidaMasNueva(ValueError):
    """La partida se guardó con una versión del juego posterior a esta."""


def migrar(d):
    """Lleva una partida guardada al formato actual, paso a paso. Las anteriores a la 1.0 no llevaban número: cuentan como 2."""
    d = dict(d)
    try:
        v = int(d.get("version", 2))
    except (TypeError, ValueError):
        v = 2
    v = max(2, v)
    if v > FORMATO:
        raise PartidaMasNueva(f"Esta partida es de una versión más nueva del juego, formato {v}. Actualiza el juego para cargarla.")
    while v < FORMATO:
        d = CONVERSIONES[v](d)
        v += 1
    d["version"] = FORMATO
    return d


class Partida(Conduccion, Combate, Misiones, Trabajos, Extras, Extras2, Extras3, Adultos, Vida, Online, EnLinea, Charla, Intimidad, Necesidades, Azar, Combustible, Realismo, MisVehiculos, Calle, Guerra,
              Domicilio, Atracos, Pactos, Contratos, Reacciones, Convivencia, Agente, Compra, Reconquista):
    pausa_mundo = False

    def __init__(self, app, guardado=None, personaje=None):
        self.app = app
        self.cfg = app.cfg
        self.voz = app.voz
        self.mez = app.mez
        self.datos = app.datos
        self.mapas = app.mapas
        self.lugares = {l.id: l for m in self.mapas.values() for l in m.lugares.values()}
        self.mundo = app.mundo
        self.pesca = None
        self.interior = None
        self.explosiones = []
        self.evento = None
        self.t_evento = random.uniform(90, 180)
        self.t_noticia = 6.0
        self.t_logros = 5.0
        self.sirena_propia = None
        self.atracadas = {}
        self.modelos = {m["id"]: m for m in self.datos["vehiculos"]}
        self.armas_d = {a["id"]: a for a in self.datos["armas"]}
        self.orden_armas = [a["id"] for a in self.datos["armas"]]
        self.j = Jugador()
        self.t = 0.0
        self.reloj = 9 * 60.0
        self.dia = 1
        self.vehiculos = []
        self.personas = []
        self.objetos = []
        self.mision = None
        self.completadas = []
        self.fallos = {}                # cuántas veces has fallado cada misión
        self.decisiones = {}            # lo que has decidido en la historia: clave -> opción elegida
        self.saltadas = []              # misiones que te has saltado
        self.resumen_pendiente = False
        self.lento = False              # tiempo lento en marcha
        self.cubierto = None            # el punto donde estás a cubierto, o None
        self.tranvias = []              # los tranvías que circulan por la localidad actual
        self.tren = None                # el tren que cruza ahora la localidad, si pasa alguno
        self._sonidos_transporte = []
        self._transporte_mapa = None
        self.t_tren = 40.0              # cuánto falta para que se oiga un tren en la estación
        self.t_avion = 55.0             # y un avión despegando en el aeropuerto
        self.nadando = False            # estás en el agua, sin barco
        self.buceando = False
        self.aguante = 100.0            # fuerzas para nadar
        self.aire = 100.0               # aire que te queda buceando
        self.t_brazada = 0.0
        self.t_fondo = 0.0
        self.agua_canal = None
        self.acompanante = None         # alguien de tu vida social que va contigo a dar una vuelta
        self.trabajo = None
        self.gps = None
        self.objetivo = None
        self.radar_lista = []
        self.online_iniciar()
        self.en_servidor = False        # la partida es de un servidor en línea
        self.sv = {}
        self.radar_idx = -1
        self.barrio_act = None
        self.cruce_act = None
        self.sup_act = None
        self.lugar_act = None
        self.canales_lugar = {}
        self.amb_canal = None
        self.amb_nombre = None
        self.noche_canal = None
        self.lluvia_canal = None
        self.latido_canal = None
        self.lluvia = False
        self.plazas_activas = {}
        self.plazas_usadas = set()
        self.libre_temp = False
        self.oy_rumbo = 0.0
        self.forzando = None
        self.transicion = False
        self.t_poblar = 0.0
        self.t_lugares = 0.0
        self.t_pared = -9.0
        self.t_pared_voz = -9.0
        self.t_semaforo = 0.0
        self.t_baliza = 0.0
        self.t_gps = 0.0
        self.t_azar = 5.0
        self.t_sonar = 0.0
        self.t_bordillo = 0.0
        self.t_objetivo = 0.0
        self.t_evasion = 0.0
        self.t_buscando = 0.0
        self.t_policia = 0.0
        self.t_fuera_alcance = -9.0
        self.dist_paso = 0.0
        self.pie = 0
        self.hora_clima = -1
        self.intro_pendiente = guardado is None
        self.veh_guardado = None
        self.veh_fuera = None
        self.ultimo_veh = None           # el vehículo del que te acabas de bajar: no desaparece aunque te alejes
        self.mis_iniciar()               # tus vehículos: no desaparecen nunca (misvehiculos.py)
        self.calle_iniciar()             # patrullas, ambulancias, rendición y helicóptero (calle.py)
        self.guerra_iniciar()            # la guerra de barrios en la calle, si el modo está encendido (guerra.py)
        self.reconquista_iniciar()       # las bandas vencidas intentan recuperar tus barrios (reconquista.py)
        self.agente_iniciar()            # el oficio de policía, si el modo está encendido (agente.py)
        self.reacciones_iniciar()        # gente que te sigue o te la guarda (reacciones.py)
        if guardado:
            self.cargar_dict(guardado)
        else:
            casa = self.mundo.lugares["bar_gaviota"]
            self.j.x, self.j.y = casa.x - 25, casa.y
            self.aplicar_personaje(personaje)
        self.azar_iniciar()
        self._crear_casetes()
        self._hilo = False
        self.app.radio.pausa = bool(self.cfg["radio_pausa"])
        self.walkman_al_empezar()
        if self.veh_guardado:
            d = self.veh_guardado
            v = self._veh_de_dict(dict(d, modelo=d.get("modelo")), self.j.x, self.j.y)
            if d.get("mio"):
                v.mio, v.mio_n = True, int(d["mio"]) if isinstance(d["mio"], (int, float)) else 1
            elif any((d.get("mejoras") or {}).values()):         # el de una partida anterior, si lo habías mejorado, es tuyo
                self.hacer_mio(v, callar=True)
            self._subir(v, False, callar=True)
        elif self.mundo.tipo == "mar":
            self.naufragar(callar=True)
        self._reponer_veh_fuera()
        self._reponer_mis_vehiculos()
        for _ in range(int(self.j.guardaespaldas)):
            self.crear_aliado()
        if self.j.perro and self.mundo.tipo != "mar" and not self.j.perro_en_casa:
            self.crear_perro()

    def _reponer_veh_fuera(self):
        """Vuelve a poner en la calle el vehículo que dejaste aparcado en esta localidad, al cargar la partida o al volver a ella."""
        d = self.veh_fuera
        if not d or self.j.veh or d.get("mapa") != self.mundo.id or d.get("modelo") not in self.modelos:
            return None
        v = self._veh_de_dict(d)
        self.ultimo_veh = v
        self.veh_fuera = None
        return v

    def _veh_fuera_dict(self, u):
        d = {"modelo": u.modelo["id"], "salud": u.salud, "nombre": u.nombre, "rumbo": u.rumbo, "x": u.x, "y": u.y,
             "mapa": self.mundo.id, "mejoras": dict(getattr(u, "mejoras", {})), "donde": self.mundo.describir(u.x, u.y)}
        if getattr(u, "litros", None) is not None:
            d["litros"] = round(u.litros, 1)
        return self.averias_a_dict(u, d)

    def localizar_vehiculo(self):
        """Mayúsculas L, o desde el móvil: dónde está el vehículo del que te bajaste, y el GPS te lleva a él."""
        j = self.j
        if j.veh:
            self.decir(f"Vas en {j.veh.nombre}. Cuando te bajes, con Mayúsculas L sabrás dónde lo has dejado." + self.mas_vehiculos_txt(j.veh), True)
            return False
        u = self.tu_vehiculo()
        if u is None:
            d = self.veh_fuera or next((x for x in self.mis_lejos if x.get("ultimo")), None)
            if d and d.get("mapa") in self.mapas and d.get("mapa") != self.mundo.id:
                self.decir(f"Dejaste {d.get('nombre') or 'tu vehículo'} en {self.mapas[d['mapa']].nombre}, {d.get('donde') or 'en la calle'}. Te espera allí." + self.mas_vehiculos_txt(d), True)
            else:
                self.app.son("error")
                self.decir("No has dejado ningún vehículo aparcado, o ya no está donde lo dejaste." + self.mas_vehiculos_txt(), True)
            return False
        antes = self.gps.get("anterior") or self.gps if self.gps else None
        if antes is not None and math.hypot(antes["dest"][0] - u.x, antes["dest"][1] - u.y) < 3:
            antes = None
        self.fijar_gps(u.x, u.y, u.nombre)
        t = f"{self.situar(u.x, u.y, u.nombre)}. {self.mundo.describir(u.x, u.y)}. Marcado en el GPS."
        if antes is not None and self.gps:
            self.gps["anterior"] = antes
            t += f" Al llegar, el GPS vuelve a {antes['nombre']}."
        self.decir(t + self.mas_vehiculos_txt(u), True)
        return True

    def proximo_cruce(self):
        """Mayúsculas N: qué calle es la siguiente que te vas a cruzar y a cuántos metros está."""
        m = self.mundo
        if m.tipo == "mar" or self.interior:
            self.decir("Aquí no hay cruces.", True)
            return None
        x, y = self.pos()
        v = self.j.veh
        rumbo = (v.rumbo if v else self.j.rumbo) % 360
        d = int(((rumbo + 45) % 360) // 90)                     # 0 norte, 1 este, 2 sur, 3 oeste
        hacia = ("norte", "este", "sur", "oeste")[d]
        if d in (1, 3):                                          # vas de este a oeste o al revés: te cruzas con avenidas
            paso = 1 if d == 1 else -1
            i = int(math.floor(x / M.B)) + (1 if paso > 0 else 0)
            if abs(i * M.B - x) <= M.ACERA:
                i += paso
            if not 0 <= i < m.NX:
                self.decir(f"Hacia el {hacia} ya no hay más cruces: se acaba {m.nombre}.", True)
                return None
            dist, nombre, por = abs(i * M.B - x), m.avenidas[i], m.calles[m._idx(y, m.NY)]
        else:
            paso = 1 if d == 0 else -1
            jj = int(math.floor(y / M.B)) + (1 if paso > 0 else 0)
            if abs(jj * M.B - y) <= M.ACERA:
                jj += paso
            if not 0 <= jj < m.NY:
                self.decir(f"Hacia el {hacia} ya no hay más cruces: se acaba {m.nombre}.", True)
                return None
            dist, nombre, por = abs(jj * M.B - y), m.calles[jj], m.avenidas[m._idx(x, m.NX)]
        self.decir(f"Siguiente cruce, hacia el {hacia}: {nombre}, a {M.metros(dist)}. Vas por {por}.", True)
        return (nombre, dist)

    def lug(self, ident):
        return self.lugares.get(ident)

    def estado_registro(self):
        """Lo que se anota de la partida en el registro de la sesión. Nada personal."""
        j = self.j
        x, y = self.pos()
        v = j.veh
        m = self.mision
        d = {"partida": "sí", "mapa": self.mundo.id, "x": round(x, 1), "y": round(y, 1), "dia": self.dia, "hora": f"{int(self.reloj // 60) % 24:02d}:{int(self.reloj % 60):02d}",
             "llueve": bool(self.lluvia), "dia_tipo": getattr(self, "dia_azar", {}).get("id", "?"),
             "vehiculo": v.modelo["id"] if v else "a pie", "velocidad": round(abs(v.vel), 1) if v else 0, "salud": round(j.salud), "salud_max": round(j.salud_max),
             "dinero": j.dinero, "busqueda": j.estrellas, "arma": j.arma,
             "mision": f"{m['def']['id']} paso {m.get('paso')}" if m else "ninguna", "completadas": len(self.completadas),
             "trabajo": (self.trabajo.get("tipo", "sí") if isinstance(self.trabajo, dict) else "sí") if self.trabajo else "no",
             "interior": getattr(self.interior, "id", "sí") if self.interior else "no",
             "vehiculos": len(self.vehiculos), "personas": len(self.personas), "objetos": len(self.objetos),
             "gps": "sí" if self.gps else "no", "adultos": bool(self.cfg["adultos"]), "vida_realista": bool(self.cfg["vida_realista"]),
             "red": ("anfitrión" if self.es_anfitrion() else "invitado") + f" con {len(self.remotos)}" if self.online_activo() else "no",
             "actividad": (self.coop or {}).get("tipo", "no") if self.coop else "no"}
        return d

    def reconstruir_lugares(self):
        self.lugares = {l.id: l for m in self.mapas.values() for l in m.lugares.values()}
        for c in self.canales_lugar.values():
            c.parar()
        self.canales_lugar.clear()
        self.lugar_act = None
        self.radar_lista = []

    def total_casetes(self):
        return sum(len(m.casetes) for m in self.mapas.values())

    # ----------------------------------------------------------------- básicos
    def decir(self, texto, interrumpir=False):
        self.voz.detalle = self.cfg["detalle_voz"]
        self.voz.decir(self.app.mando.textos(texto), interrumpir)

    def son(self, nombre, xy=None, **kw):
        if nombre == "comer":
            self.ha_comido()             # comer en cualquier sitio quita el hambre (vida realista)
        elif nombre in ("beber", "trago"):
            self.ha_bebido()
        return self.mez.sonar(nombre, xy=xy, **kw)

    def pos(self):
        v = self.j.veh
        return (v.x, v.y) if v else (self.j.x, self.j.y)

    def frente(self):
        """Rumbo hacia el que mira el oyente."""
        if self.j.veh:
            return self.oy_rumbo
        if self.cfg["movimiento"] == "giro":
            return self.j.rumbo
        return 0.0

    def direccion_txt(self, x, y):
        px, py = self.pos()
        rumbo = M.rumbo_a(x - px, y - py)
        modo = self.cfg["direcciones"]
        if modo == "reloj":
            return M.texto_reloj(M.norm180(rumbo - self.frente()))
        if modo == "relativa" and (self.j.veh or self.cfg["movimiento"] == "giro"):
            return M.texto_relativo(M.norm180(rumbo - self.frente()))
        return "al " + M.cardinal(rumbo)

    def situar(self, x, y, nombre):
        px, py = self.pos()
        d = math.hypot(x - px, y - py)
        if d < 1.5:
            return f"{nombre}, aquí mismo"
        return f"{nombre}, {M.metros(d)}, {self.direccion_txt(x, y)}"

    def hora_txt(self):
        h = int(self.reloj // 60) % 24
        m = int(self.reloj % 60)
        franja = "de la madrugada" if h < 6 else "de la mañana" if h < 13 else "de la tarde" if h < 21 else "de la noche"
        h12 = h % 12 or 12
        return f"{h12} y {m:02d} {franja}" if m else f"{h12} en punto {franja}"

    def estado_musica(self):
        """Qué música de ambiente corresponde a la situación."""
        if self.j.estrellas:
            return "tension"
        x, y = self.pos()
        if any(e.hostil and not e.muerto and e.activo and e.tipo != "policia" and (e.tipo != "banda" or e.avisado) and e.dist(x, y) < 45 for e in self.personas):
            return "tension"
        if self.mundo.tipo == "mar":
            return "mar"
        return "noche" if self.es_noche() else "exploracion"

    def es_noche(self):
        h = (self.reloj // 60) % 24
        return h >= 21 or h < 6

    def dificultad(self):
        return {"facil": 0.6, "normal": 1.0, "dificil": 1.4}[self.cfg["dificultad"]]

    def lugar_cercano(self, radio):
        px, py = self.pos()
        mejor = None
        for l in self.mundo.lugares.values():
            d = math.hypot(l.x - px, l.y - py)
            if d <= radio and (mejor is None or d < mejor[0]):
                mejor = (d, l)
        return mejor[1] if mejor else None

    def dar_dinero(self, n, motivo=None):
        self.j.dinero += n
        if n > 0:
            self.j.stats["dinero_ganado"] += n
            self.son("dinero", cat="interfaz")
        if motivo:
            self.decir(f"{motivo}: {'más' if n >= 0 else 'menos'} {abs(n)} euros.")

    def pagar(self, n):
        if self.j.dinero < n:
            self.app.son("error")
            self.decir(f"No tienes suficiente dinero. Cuesta {n} euros y tienes {self.j.dinero}.", True)
            return False
        self.j.dinero -= n
        if n > 0:
            self.son("caja", cat="interfaz", vol=0.6)
        return True

    # ------------------------------------------------------------- guardado
    def a_dict(self):
        px, py = self.pos()
        j = self.j.a_dict()
        j["x"], j["y"] = px, py
        j["mapa"] = self.mundo.id
        j["guardaespaldas"] = sum(1 for p in self.personas if p.tipo == "aliado" and not p.muerto and not getattr(p, "de_banda", False))
        d = {"version": FORMATO, "jugador": j, "reloj": self.reloj, "dia": self.dia, "momento": time.time(),
             "fallos": dict(self.fallos), "decisiones": dict(self.decisiones), "saltadas": list(self.saltadas),
             "completadas": list(self.completadas), "lluvia": self.lluvia, "atracadas": self.atracadas,
             "lugar": f"{self.mundo.describir(px, py)}, {self.mundo.nombre}"}
        v = self.j.veh
        if v and not v.tag:
            d["veh"] = {"modelo": v.modelo["id"], "salud": v.salud, "nombre": v.nombre, "rumbo": v.rumbo, "mejoras": dict(getattr(v, "mejoras", {}))}
            if getattr(v, "litros", None) is not None:
                d["veh"]["litros"] = round(v.litros, 1)
            self.averias_a_dict(v, d["veh"])
            if self.es_mio(v):
                d["veh"]["mio"] = int(getattr(v, "mio_n", 0)) or 1
        u = self.tu_vehiculo()
        self.mis_a_dict(d, u)
        if not v and u is not None and not self.es_mio(u):
            d["veh_fuera"] = self._veh_fuera_dict(u)
        elif self.veh_fuera and self.veh_fuera.get("mapa") != self.mundo.id:
            d["veh_fuera"] = dict(self.veh_fuera)             # lo dejaste en otra localidad y allí sigue
        return d

    def tu_vehiculo(self, radio=None):
        """El vehículo del que te has bajado, si sigue entero y en esta localidad. Con `radio`, solo si está así de cerca."""
        u = getattr(self, "ultimo_veh", None)
        if u is None or u.muerto or u.tag or u.ardiendo >= 0 or u not in self.vehiculos or u is self.j.veh:
            return None
        if radio is not None and u.dist(*self.pos()) > radio:
            return None
        return u

    def cargar_dict(self, d):
        d = migrar(d)
        self.j.de_dict(d.get("jugador", {}))
        genero.poner(self.j.genero)
        if self.j.personaje == "propio":
            registro.ocultar(self.j.nombre)
            if self.j.apellido:
                registro.ocultar(self.j.apellido)
        self.fallos = {str(k): int(v) for k, v in dict(d.get("fallos", {})).items()}
        self.decisiones = dict(d.get("decisiones", {}))
        self.saltadas = list(d.get("saltadas", []))
        fecha = d.get("momento")
        # si hace días que no juegas, al volver se te recuerda por dónde ibas
        self.resumen_pendiente = isinstance(fecha, (int, float)) and time.time() - fecha > 2 * 86400
        self.mundo = self.mapas.get(self.j.mapa) or self.app.mundo
        self.j.mapa = self.mundo.id
        self.veh_guardado = d.get("veh")
        self.veh_fuera = d.get("veh_fuera")
        self.mis_cargar(d)
        self.atracadas = dict(d.get("atracadas", {}))
        self.reloj = float(d.get("reloj", 540))
        self.dia = int(d.get("dia", 1))
        self.completadas = list(d.get("completadas", []))
        self.lluvia = bool(d.get("lluvia", False))
        self.j.puntos_busqueda = 0.0
        self.j.estrellas = 0
        self.j.x, self.j.y = self.mundo.punto_libre(self.j.x, self.j.y)
        if self.j.arma not in self.j.armas:
            self.j.arma = "punos"
        # una partida anterior a la reconquista que ya tiene barrios bastantes: calma inicial y su aviso, una vez
        self._rec_cargada = not self.j.reconquista.get("v") and bool(self.rec_fase())

    def saltos_por_tierra(self, origen, destino):
        """Cuántas localidades hay que cruzar por carretera para ir de una a otra: 1 si son vecinas. None si hay mar por medio."""
        def vecinos(mid):
            m = self.mapas.get(mid)
            if m is None or m.tipo == "mar":
                return set()
            return {l.get("a_mapa") for l in m.lugares.values() if l.tipo == "salida" and l.get("a_mapa") in self.mapas and self.mapas[l.get("a_mapa")].tipo != "mar"}
        if origen == destino:
            return None
        nivel, vistos, n = {origen}, {origen}, 0
        while nivel:
            n += 1
            sig = set()
            for mid in nivel:
                for v in vecinos(mid):
                    if v == destino:
                        return n
                    if v not in vistos:
                        vistos.add(v)
                        sig.add(v)
            nivel = sig
        return None

    def medio_por_rail(self, origen, destino):
        """Cómo se va por raíl de una localidad a otra: «tranvia» si son vecinas por carretera, «tren» si se llega por tierra
        aunque sea dando un rodeo, y None si hay mar por medio."""
        def vecinos(mid):
            m = self.mapas.get(mid)
            if m is None or m.tipo == "mar":
                return set()
            return {l.get("a_mapa") for l in m.lugares.values() if l.tipo == "salida" and l.get("a_mapa") in self.mapas and self.mapas[l.get("a_mapa")].tipo != "mar"}
        if destino in vecinos(origen):
            return "tranvia"
        vistos, cola = {origen}, [origen]
        while cola:
            for v in vecinos(cola.pop()):
                if v == destino:
                    return "tren"
                if v not in vistos:
                    vistos.add(v)
                    cola.append(v)
        return None

    def resumen_historia(self):
        """Por dónde vas en la historia, en dos o tres frases."""
        por_id = {m["id"]: m for m in self.datos["misiones"]}
        hechas = [por_id[i] for i in self.completadas if i in por_id and not por_id[i].get("tutorial")]
        if not hechas:
            t = "Todavía no has hecho ninguna misión de la historia."
        else:
            u = hechas[-1]
            t = f"Llevas {len(hechas)} {'misión' if len(hechas) == 1 else 'misiones'} de la historia. La última fue {u['titulo']}: {self.txt(u.get('resumen', ''))}".rstrip()
        disp = [m for m in self.misiones_disponibles() if not m.get("tutorial")]
        if disp:
            m = disp[0]
            t += f" Lo siguiente: {m['titulo']}, en {self.nombre_lugar(self.lugares[m['lugar']])}. {self.txt(m.get('resumen', ''))}".rstrip()
        elif hechas:
            t += " No te queda ninguna misión pendiente."
        return t

    def _crear_casetes(self):
        for k, (x, y) in enumerate(self.mundo.casetes):
            clave = f"{self.mundo.id}:{k}"
            if clave in self.j.casetes:
                continue
            o = Objeto("casete", f"{self.mundo.nombre_objeto} número {k + 1}", x, y, "loc_casete")
            o.tag = clave
            self.objetos.append(o)

    # --------------------------------------------------------- cambio de mapa
    def conexion_hacia(self, mapa_dest):
        """Lugar del mapa actual por el que se empieza el viaje hacia otro mapa."""
        origen = self.mundo.id
        if mapa_dest == origen:
            return None
        en_coche = self.j.veh is not None and self.mundo.tipo != "mar"
        volando = self.j.veh is not None and bool(self.j.veh.modelo.get("vuela"))
        preferido = "helipuerto" if volando else "salida" if en_coche else "estacion"

        def aristas(mid):
            m = self.mapas[mid]
            out = []
            for l in m.lugares.values():
                if l.get("a_mapa") in self.mapas:
                    out.append((l, l.get("a_mapa")))
                elif l.tipo == "estacion" or (l.tipo == "helipuerto" and volando):
                    for otro in self.mapas.values():
                        if otro.id != mid and any(x.tipo == l.tipo for x in otro.lugares.values()):
                            out.append((l, otro.id))
            # al volante se prefieren las carreteras; a pie, el autobús; volando, los helipuertos
            out.sort(key=lambda e: (e[0].tipo != preferido, e[0].tipo == "embarcadero"))
            return out
        visto = {origen}
        cola = [(origen, None)]
        while cola:
            mid, primero = cola.pop(0)
            for l, dest in aristas(mid):
                if dest in visto:
                    continue
                p = primero or l
                if dest == mapa_dest:
                    return p
                visto.add(dest)
                cola.append((dest, p))
        return None

    def cambiar_mapa(self, mapa_id, x, y, rumbo=None, texto=None):
        j = self.j
        if self.trabajo and self.trabajo["tipo"] != "camion":
            self.terminar_trabajo("Al salir de la localidad se acaba el trabajo.")
        v = j.veh
        u = self.tu_vehiculo() if not v and not getattr(self, "en_servidor", False) else None
        if u is not None and not self.es_mio(u):
            self.veh_fuera = self._veh_fuera_dict(u)           # te vas a pie: el vehículo se queda aquí, y aquí estará cuando vuelvas
        self.mis_al_cambiar_mapa(u)                             # y los que son tuyos, todos: cada uno donde lo dejaste
        self.chofer_al_cambiar_mapa()
        self.ultimo_veh = None
        gps_final = self.gps.get("final") if self.gps else None
        gps_auto = self.gps.get("auto") if self.gps else False
        for o in self.vehiculos:
            if o is not v:
                o.callar()
                o.muerto = True
        self.vehiculos = [v] if v else []
        self.personas = [p for p in self.personas if p.tipo in ("aliado", "perro") and not p.muerto]
        for o in self.objetos:
            if o.canal:
                o.canal.parar()
        self.objetos = []
        for c in self.canales_lugar.values():
            c.parar()
        self.canales_lugar.clear()
        from . import transporte
        transporte.callar(self)                                 # los tranvías de la localidad que se deja
        self._transporte_mapa = None
        self.plazas_activas.clear()
        self.plazas_usadas.clear()
        self.objetivo = None
        self.pesca = None
        self.evento = None
        self.t_evento = random.uniform(90, 180)
        self.explosiones = []
        self.radar_lista = []
        if self.forzando:
            self.forzando["canal"].parar()
            self.forzando = None
        self.gps = None
        self.guerra_retirada(callar=True)                       # una guerra de barrio no sigue desde otra localidad
        self._fin_persecucion()
        self.calle_cambio_mapa()
        self.mundo = self.mapas[mapa_id]
        j.mapa = mapa_id
        if v:
            v.x, v.y = x, y
            v.vel = 0.0
            if rumbo is not None:
                v.rumbo = float(rumbo)
            v.dir = M.dir_de_rumbo(v.rumbo)
            self.oy_rumbo = v.rumbo
            self.preparar_conduccion()
        else:
            j.x, j.y = self.mundo.punto_libre(x, y)
        for p in self.personas:
            p.x, p.y = self.mundo.punto_libre(x + random.uniform(-3, 3), y + random.uniform(-3, 3))
        self._crear_casetes()
        if not getattr(self, "en_servidor", False):
            self._reponer_veh_fuera()
            self._reponer_mis_vehiculos()
        self.barrio_act = self.mundo.barrio(x, y)["id"]
        if self.barrio_act not in j.barrios_vistos:
            j.barrios_vistos.append(self.barrio_act)
        self.cruce_act = self.mundo.cruce(x, y)
        self.lugar_act = self.lugar_cercano(22)
        self.sup_act = None
        if texto:
            self.decir(texto)
        self.mision_cambio_mapa()
        self.sv_poner_vehiculos()
        if not self.gps and gps_final and self.lug(gps_final):
            self.gps_a_lugar(self.lug(gps_final), auto=gps_auto, callar=True)
            self.repetir_gps_suave()

    def repetir_gps_suave(self):
        if self.gps:
            clave, texto = self._instruccion()
            self.gps["clave"] = clave
            self.decir(texto)

    def naufragar(self, callar=False):
        """Te quedas sin barco en el mar: te rescatan y te dejan en el puerto más cercano."""
        j = self.j
        x, y = self.pos()
        muelles = [l for l in self.mundo.lugares.values() if l.get("a_mapa") in self.mapas and self.lug(l.get("a_lugar"))]
        if not muelles:
            dest = self.app.mundo.lugares.get("hospital") or next(iter(self.app.mundo.lugares.values()))
        else:
            m = min(muelles, key=lambda l: math.hypot(l.x - x, l.y - y))
            dest = self.lug(m.get("a_lugar"))
        j.barco_actual = None
        self.cambiar_mapa(dest.mapa, dest.x, dest.y)
        if not callar:
            j.salud = max(10.0, j.salud - 30)
            self.pasar_horas(2)
            self.decir(f"Te quedas a la deriva hasta que un pesquero te recoge medio ahogad[o|a] y te deja en {dest.nombre}. Salud {int(j.salud)}.")

    # --------------------------------------------------------------- entrada
    def al_entrar(self):
        self.salir_interior()
        if self.intro_pendiente:
            self.intro_pendiente = False
            from . import menus_juego
            menus_juego.intro(self)

    def tecla(self, ev):
        from . import menus_juego as mj
        k = ev.key
        mayus = bool(ev.mod & pygame.KMOD_SHIFT)
        ctrl = bool(ev.mod & pygame.KMOD_CTRL)
        if k != pygame.K_LSHIFT:
            self._mayus_sola = False                             # ha habido otra tecla: la Mayúsculas era para una combinación
        j = self.j
        if self.transicion:
            return
        if k == pygame.K_ESCAPE:
            mj.pausa(self)
        elif k == pygame.K_F1:
            mj.ayuda_teclas(self.app, "coche" if j.veh else "pie")
        elif k == pygame.K_c:
            self.donde(mayus)
        elif k == pygame.K_v:
            if mayus:                                            # solo el cuerpo: hambre y sueño
                self.decir(self.necesidades_txt().strip() or "La vida realista está desactivada: no pasas hambre, sed ni sueño. Se activa en Opciones, Combate y dificultad.", True)
            else:
                self.estado()
        elif k == pygame.K_t:
            self.decir(f"Son las {self.hora_txt()}, día {self.dia}. {'Llueve.' if self.lluvia else 'Cielo despejado.'} {self.dia_txt()}".strip(), True)
        elif k == pygame.K_o:
            self.decir(self.objetivo_txt(), True)
        elif k == pygame.K_n:
            if mayus:
                self.proximo_cruce()
            else:
                self.describir_aqui()
        elif k == pygame.K_k:
            x, y = self.pos()
            self.son("baliza_destino", xy=(x, y + 15), ref=8, maxd=60, cat="interfaz")     # un toque que suena desde el norte
            self.decir(self.rumbo_txt() + ". El tono suena desde el norte.", True)
        elif k == pygame.K_F10:
            from . import menus_online
            menus_online.escribir_mensaje(self, "ic" if mayus else "yo" if ctrl else None)      # en un servidor: en personaje, o una acción
        elif k == pygame.K_F9:
            from .pantallas import ExploradorMapa
            self.app.abrir(ExploradorMapa(self.app, self))
        elif k == pygame.K_m:
            self.app.son("movil")
            mj.movil(self)
        elif k == pygame.K_l:
            if mayus:
                self.localizar_vehiculo()
            else:
                mj.lista_lugares(self)
        elif k == pygame.K_g:
            if mayus:
                habia = self.gps is not None
                self.cancelar_gps(True)
                if self.mision:
                    self.mision["gps_callado"] = True            # lo has quitado tú: la misión no lo vuelve a poner sola
                    if habia:
                        self.decir("Con la G vuelves a marcar la misión.")
            elif not self.gps and self.mision and self.gps_mision(hablar=False):
                self.app.son("notificacion")
                self.repetir_gps()
            else:
                self.repetir_gps()
        elif k == pygame.K_TAB:
            self.radar(-1 if mayus else 1)
        elif k == pygame.K_b:
            self.baliza_radar()
        elif k == pygame.K_F6:
            ops = ["todo", "lugares", "vehiculos", "personas", "objetos"]
            self.cfg["radar_filtro"] = ops[(ops.index(self.cfg["radar_filtro"]) + 1) % len(ops)]
            self.radar_lista = []
            self.decir("Radar: " + {"todo": "todo", "lugares": "solo lugares", "vehiculos": "solo vehículos", "personas": "solo personas", "objetos": "solo objetos"}[self.cfg["radar_filtro"]], True)
        elif k == pygame.K_F2:
            self.cfg["conduccion"] = "libre" if self.cfg["conduccion"] == "asistida" else "asistida"
            self.decir("Conducción " + self.cfg["conduccion"], True)
            if j.veh:
                self.preparar_conduccion()
        elif k == pygame.K_F3:
            self.cfg["movimiento"] = "giro" if self.cfg["movimiento"] == "brujula" else "brujula"
            self.decir("Movimiento a pie: " + ("con giros. Izquierda y derecha giran 45 grados." if self.cfg["movimiento"] == "giro" else "brújula. Cada flecha camina hacia un punto cardinal."), True)
        elif k == pygame.K_F4:
            self.cfg["baliza"] = not self.cfg["baliza"]
            self.decir("Baliza sonora del GPS " + ("activada" if self.cfg["baliza"] else "desactivada"), True)
        elif k == pygame.K_F5:
            mj.guardado_rapido(self)
        elif k in (pygame.K_F7, pygame.K_F8):
            v = max(0.0, min(1.0, self.cfg["vol_musica"] + (0.1 if k == pygame.K_F8 else -0.1)))
            self.cfg["vol_musica"] = round(v, 1)
            self.app.aplicar_volumenes()
            self.decir(f"Música {int(v * 100)} por ciento", True)
        elif k == pygame.K_PAGEUP:
            self.voz.repasar(-1)
        elif k == pygame.K_PAGEDOWN:
            self.voz.repasar(1)
        elif k == pygame.K_PERIOD:
            self.voz.repasar(0)
        elif k == pygame.K_q:
            self.fijar(any_=mayus)
        elif k == pygame.K_SPACE:
            if self.pesca:
                self.tirar_pesca()
            elif not j.veh:         # al volante, Espacio es el freno de mano (tecla mantenida)
                self.atacar()
        elif k == pygame.K_p:
            if self.mundo.tipo == "mar":
                self.empezar_pesca()
            elif j.veh and j.veh.modelo.get("sirena"):
                self.alternar_sirena()
            else:
                self.decir("La tecla P pesca cuando estás en el mar y enciende la sirena en los vehículos de emergencias.", True)
        elif k == pygame.K_i:
            mj.menu_armas(self)
        elif k == pygame.K_LCTRL or k == pygame.K_RCTRL:
            if j.veh:
                self.atacar()
        elif k == pygame.K_z:
            if mayus and self.modo_adulto():
                from . import menus_adultos
                menus_adultos.menu_sustancias(self)
            else:
                self.usar_botiquin()
        elif k == pygame.K_BACKSPACE:
            self.alternar_lento()
        elif k == pygame.K_x and self.nadando:
            self.alternar_buceo()
        elif k == pygame.K_x and mayus:
            self.alternar_cobertura()
        elif k == pygame.K_x:
            if not j.veh:
                if self.cubierto:
                    self.dejar_cobertura()
                j.agachado = not j.agachado
                self.son("agacharse" if j.agachado else "levantarse")
                self.decir("Te agachas." if j.agachado else "Te levantas.", True)
        elif pygame.K_1 <= k <= pygame.K_9:
            self.elegir_arma(k - pygame.K_1)
        elif k == pygame.K_COMMA:
            self.elegir_arma(None, -1 if mayus else 1)
        elif k == pygame.K_f:
            if mayus and self.en_servidor and not self.j.veh:    # en un servidor: sacar a otro jugador de su vehículo
                if not self.sv_asaltar_cerca():
                    self.decir("No hay ningún jugador al volante a tu lado.", True)
            else:
                self.entrar_salir()
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.interactuar()
        elif k == pygame.K_h and mayus:
            self.rendirse()
        elif j.veh:
            self.tecla_coche(ev, mayus)
        else:
            self.tecla_pie(ev, mayus)

    # ------------------------------------------------------------------ nadar y bucear
    def empezar_a_nadar(self, antes=""):
        self.nadando = True
        self.buceando = False
        self.aguante = 100.0
        self.aire = 100.0
        self.j.agachado = False
        self.son("salpicadura", vol=0.8)
        self.decir((antes + " " if antes else "") + "Estás en el agua. Nadas con las flechas. La X te sumerge para bucear y te vuelve a sacar. "
                   "Para subir a un barco, acércate y pulsa F. Si llegas nadando a un muelle, sales a tierra. No te quedes sin fuerzas: la V te dice cuántas te quedan.")

    def _fin_agua(self):
        self.nadando = self.buceando = False
        if self.agua_canal is not None:
            self.agua_canal.parar()
            self.agua_canal = None

    def alternar_buceo(self):
        if self.buceando:
            self.buceando = False
            if self.agua_canal is not None:
                self.agua_canal.parar()
                self.agua_canal = None
            self.son("salpicadura", vol=0.7)
            self.decir(f"Sales a la superficie. Aire {int(self.aire)} por ciento, fuerzas {int(self.aguante)}.", True)
        elif self.aire < 20:
            self.app.son("error")
            self.decir("Aún no has recuperado el aliento.", True)
        else:
            self.buceando = True
            self.t_fondo = 5.0
            self.son("salpicadura", vol=0.6, tono=0.7)
            self.agua_canal = self.son("bajo_agua", bucle=True, vol=0.6, cat="ambiente")
            self.decir("Te sumerges. Aguantas la respiración una media hora de reloj de arena: unos treinta segundos. Con la X vuelves a subir.", True)

    def nadar(self, dt):
        """Un fotograma en el agua sin barco. Devuelve True si ha cambiado el mapa (te has ahogado o has llegado a tierra)."""
        j = self.j
        if not self.nadando:
            self.empezar_a_nadar()
        t = self.app.teclas
        dx = (pygame.K_RIGHT in t) - (pygame.K_LEFT in t)
        dy = (pygame.K_UP in t) - (pygame.K_DOWN in t)
        se_mueve = bool(dx or dy)
        if se_mueve:
            n = math.hypot(dx, dy)
            vel = 1.1 if self.buceando else 1.7
            nx, ny = j.x + dx / n * vel * dt, j.y + dy / n * vel * dt
            if self.mundo.transitable(nx, ny):
                j.x, j.y = nx, ny
            j.rumbo = M.rumbo_a(dx, dy)
            j.stats["metros_nadando"] = j.stats.get("metros_nadando", 0.0) + vel * dt
            self.t_brazada -= dt
            if self.t_brazada <= 0:
                self.t_brazada = 0.85
                self.son("brazada", vol=0.3 if self.buceando else 0.7, tono=(0.6 if self.buceando else 1.0) * random.uniform(0.93, 1.07),
                         pan=-0.3 if int(self.t / 0.85) % 2 else 0.3)
        self.aguante -= (1.1 if se_mueve else 0.35) * dt
        if self.buceando:
            self.aire -= dt * 100.0 / 30.0
            self.t_fondo -= dt
            if self.t_fondo <= 0:                                # mirando el fondo, a veces aparece algo
                self.t_fondo = 5.0
                if random.random() < 0.3:
                    que, valor = random.choice([("unas monedas antiguas", 60), ("un reloj de pulsera", 120), ("una caja de aparejos", 35), ("un doblón", 250)])
                    self.son("recoger", cat="interfaz")
                    self.dar_dinero(valor, f"En el fondo encuentras {que}. Vale")
                    j.stats["buceo"] = j.stats.get("buceo", 0) + 1
            if self.aire <= 25 and "aire" not in getattr(self, "_avisos_agua", set()):
                self._avisos_agua = {"aire"}
                self.decir("Te queda poco aire. Sube con la X.")
            if self.aire <= 0:
                self.aire = 0.0
                self.alternar_buceo()
                self.danar_jugador(15, None)
                self.decir("Subes a la superficie tragando agua.")
        else:
            self.aire = min(100.0, self.aire + 12.0 * dt)
            if self.aire > 60:
                self._avisos_agua = set()
        if self.aguante <= 25 and not getattr(self, "_aviso_fuerzas", False):
            self._aviso_fuerzas = True
            self.decir("Te estás quedando sin fuerzas. Busca un barco o un muelle.")
        if self.aguante > 40:
            self._aviso_fuerzas = False
        if self.aguante <= 0 or j.salud <= 0:
            self._fin_agua()
            self.naufragar()
            return True
        if not self.buceando:
            for l in self.mundo.lugares.values():               # llegar nadando a un muelle te saca a tierra
                dest = self.lug(l.get("a_lugar")) if l.get("a_mapa") in self.mapas else None
                if dest is not None and math.hypot(l.x - j.x, l.y - j.y) < 14:
                    self._fin_agua()
                    j.barco_actual = None
                    self.cambiar_mapa(dest.mapa, dest.x, dest.y, None, f"Llegas nadando a {l.nombre} y sales del agua, chorreando, en {dest.nombre}.")
                    return True
        return False

    # ------------------------------------------------------------------ tiempo lento
    def alternar_lento(self):
        j = self.j
        if self.lento:
            self.lento = False
            self.app.son("menu_atras")
            self.decir(f"Tiempo normal. Concentración {int(j.foco)} por ciento.", True)
        elif self.online_activo():
            self.decir("Con amigos conectados no se puede frenar el tiempo.", True)
        elif j.foco < 15:
            self.app.son("error")
            self.decir(f"Te falta concentración: {int(j.foco)} por ciento. Se recupera sola.", True)
        else:
            self.lento = True
            self.app.son("pasan_horas", vol=0.5, tono=0.6)
            self.decir(f"Tiempo lento. Concentración {int(j.foco)} por ciento.", True)

    def _paso_lento(self, dt):
        """Gasta o recupera la concentración. Devuelve el tiempo de mundo que corresponde a este fotograma."""
        j = self.j
        if not self.lento:
            j.foco = min(100.0, j.foco + 3.0 * dt)
            return dt
        j.foco -= 20.0 * dt
        if j.foco <= 0:
            j.foco = 0.0
            self.lento = False
            self.app.son("menu_atras")
            self.decir("Se te acaba la concentración. Tiempo normal.")
            return dt
        return dt * 0.4

    # ------------------------------------------------------------------ cobertura
    def _hay_parapeto(self):
        j = self.j
        for a in range(0, 360, 45):
            r = math.radians(a)
            if not self.mundo.transitable(j.x + math.sin(r) * 2.2, j.y + math.cos(r) * 2.2):
                return "una pared"
        for v in self.vehiculos:
            if not v.muerto and v.dist(j.x, j.y) < 3.5 and abs(v.vel) < 1:
                return v.nombre
        return None

    def alternar_cobertura(self):
        j = self.j
        if j.veh:
            self.decir("Dentro de un vehículo no puedes cubrirte.", True)
            return
        if self.cubierto:
            self.dejar_cobertura()
            return
        que = self._hay_parapeto()
        if not que:
            self.app.son("error")
            self.decir("Aquí no hay nada tras lo que cubrirte. Pégate a una pared o a un vehículo parado.", True)
            return
        self.cubierto = (j.x, j.y)
        j.agachado = True
        self.son("agacharse")
        self.decir(f"A cubierto tras {que}. Te alcanzan mucho menos, pero apuntas algo peor. Si te mueves, sales.", True)

    def dejar_cobertura(self, hablar=True):
        if self.cubierto:
            self.cubierto = None
            if hablar:
                self.decir("Sales de la cobertura.", True)

    def corriendo_ahora(self):
        """¿Corre? Con la tecla mantenida o, si el jugador lo prefiere, encendido con una pulsación."""
        t = self.app.teclas
        if self.j.agachado:
            return False
        if self.cfg["correr_alternar"]:
            return bool(getattr(self, "correr_fijo", False))
        return pygame.K_LSHIFT in t                              # solo la izquierda: la derecha queda para las combinaciones

    def tecla_pie(self, ev, mayus):
        k = ev.key
        j = self.j
        if k == pygame.K_LSHIFT and j.agachado and not self.cubierto and self.t - getattr(self, "t_aviso_agachado", -99) > 15:
            self.t_aviso_agachado = self.t
            self.decir("Estás agachad[o|a] y por eso vas despacio. Pulsa X para levantarte.")
        if k == pygame.K_LSHIFT and self.cfg["correr_alternar"]:
            # No se cambia al pulsarla sino al soltarla, y solo si entre medias no se ha pulsado nada más: así Mayúsculas
            # con una letra es una combinación y no te pone a correr ni te para.
            self._mayus_sola = True
            return
        if k == pygame.K_r:
            if mayus:
                self.walkman()
            else:
                self.recargar()
        elif k in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
            base = {pygame.K_w: 0, pygame.K_d: 90, pygame.K_s: 180, pygame.K_a: 270}[k]
            self.mirar((base + self.frente()) % 360)
        elif self.cfg["movimiento"] == "giro" and k in (pygame.K_LEFT, pygame.K_RIGHT):
            j.rumbo = (round(j.rumbo / 45.0) * 45 + (45 if k == pygame.K_RIGHT else -45)) % 360
            self.app.son("menu_mover")
            self.decir(M.cardinal(j.rumbo).capitalize(), True)
        elif k == pygame.K_e:
            self.atracar_peaton()
        elif k == pygame.K_y:
            if mayus:
                from . import menus_extra
                menus_extra.menu_perro(self)
            else:
                self.perro_busca()
        elif k == pygame.K_u:
            self.alternar_paseo()
        elif k == pygame.K_j:
            if mayus:
                self.mirar_jugador()
            else:
                self.hablar()
        elif k == pygame.K_h:
            self.son("grito", vol=0.5)
            self.sv_ruido("grito")
            if self.dar_alto():                                  # de servicio como policía, la H da el alto
                return
            for p in self.personas:
                if p.tipo == "civil" and not p.muerto and p.dist(j.x, j.y) < 15:
                    self.asustar(p, 6, grito=0.25)

    # ------------------------------------------------------------- información
    def rumbo_txt(self):
        v = self.j.veh
        if v:
            return f"Vas hacia el {M.cardinal(v.rumbo)}"
        return f"Miras al {M.cardinal(self.j.rumbo)}"

    def donde(self, detalle=False):
        x, y = self.pos()
        b = self.mundo.barrio(x, y)
        t = f"{self.mundo.describir(x, y)}. {b['nombre']}. {self.rumbo_txt()}."
        if detalle:
            t += f" Coordenadas: {int(x)} este, {int(y)} norte, en una ciudad de {int(self.mundo.ancho)} por {int(self.mundo.alto)} metros."
        l = self.lugar_cercano(16)
        if l:
            t += " " + self.situar(l.x, l.y, l.nombre) + "."
        self.decir(t, True)

    def estado(self):
        j = self.j
        a = self.arma()
        t = f"Salud {int(j.salud)}"
        if j.salud_max > 100:
            t += f" de {int(j.salud_max)}"
        if j.blindaje > 0:
            t += f", blindaje {int(j.blindaje)}"
        t += f". {j.dinero} euros" + (f" y {j.banco} en el banco. " if j.banco else ". ")
        if j.pescado:
            t += f"{len(j.pescado)} capturas de pesca. "
        if j.estrellas:
            t += f"Nivel de búsqueda {j.estrellas}. "
        if j.agachado and not j.veh:
            t += "Estás a cubierto. " if self.cubierto else "Estás agachad[o|a]: caminas despacio. "
        if j.foco < 99:
            t += f"Concentración {int(j.foco)} por ciento. "
        if self.nadando:
            t += f"Estás {'buceando' if self.buceando else 'nadando'}. Fuerzas {int(self.aguante)} por ciento, aire {int(self.aire)}. "
        t += "Arma: " + a["nombre"]
        if a["tipo"] in ("fuego", "explosivo"):
            m = j.armas[j.arma]
            t += f", {m['cargador']} balas en el cargador y {m['reserva']} de reserva"
        t += f". Botiquines: {j.objetos.get('botiquin', 0)}. Ánimo {self.animo_txt()}. Entre los vecinos, {self.ciudadania_txt()}. En la calle, {self.reputacion_txt()}."
        if j.efectos:
            t += " Bajo los efectos de: " + ", ".join(sorted({(self.sustancia(e["id"]) or {"nombre": e["id"]})["nombre"].lower() + (", con bajón" if e.get("bajon") else "") for e in j.efectos})) + "."
        if self._abstinencia():
            t += " Tienes síndrome de abstinencia."
        t += self.necesidades_txt()
        if self.modo_adulto() and self.estado_intimo_txt():
            t += " " + self.estado_intimo_txt()
        if j.veh:
            v = j.veh
            t += f" Conduces {v.nombre}, a {int(abs(v.vel) * 3.6)} kilómetros por hora, estado {int(100 * v.salud / v.salud_max)} por ciento."
            t += self.combustible_txt(v) + self.averias_txt(v)
        t += self.carne_txt()
        self.decir(t, True)

    def describir_aqui(self):
        x, y = self.pos()
        l = self.lugar_cercano(16)
        if l:
            self.decir(f"{l.nombre}. {l.desc}", True)
        else:
            b = self.mundo.barrio(x, y)
            self.decir(f"{b['nombre']}. {self.barrio_desc(b)}", True)

    def mirar(self, rumbo):
        """Escáner direccional: describe lo que hay en una dirección."""
        x, y = self.pos()
        rad = math.radians(rumbo)
        sx, sy = math.sin(rad), math.cos(rad)
        cosas = []
        cand = [(l.x, l.y, l.nombre) for l in self.mundo.lugares.values()]
        cand += [(p.x, p.y, p.nombre) for p in self.personas if not p.muerto]
        cand += [(v.x, v.y, v.nombre) for v in self.vehiculos if v is not self.j.veh and not v.muerto]
        cand += [(o.x, o.y, o.nombre) for o in self.objetos]
        for cx, cy, nom in cand:
            a = (cx - x) * sx + (cy - y) * sy
            lat = abs((cx - x) * sy - (cy - y) * sx)
            if 1.0 < a <= 60 and lat <= max(3.0, a * 0.2):
                cosas.append((a, nom))
        cosas.sort()
        partes = [f"{nom} a {M.metros(a)}" for a, nom in cosas[:3]]
        s0 = self.mundo.superficie(x, y)
        d = 0.5
        cambio = None
        pared = None
        ant = s0
        while d <= 60:
            s = self.mundo.superficie(x + sx * d, y + sy * d)
            if s in ("pared", "fuera"):
                pared = (d, s)
                break
            if s != ant and cambio is None and s != s0:
                cambio = (d, s, x + sx * d, y + sy * d)
            ant = s
            d += 0.5
        if cambio:
            txt = M.SUPERFICIE_TXT[cambio[1]]
            if cambio[1] == "calzada":
                t, idx, _ = self.mundo.via_cercana(cambio[2], cambio[3])
                txt += " de " + self.mundo.nombre_via(t, idx)
            partes.append(f"{txt} a {M.metros(cambio[0])}")
        if pared:
            partes.append(f"{M.SUPERFICIE_TXT[pared[1]]} a {M.metros(pared[0])}")
            dd = min(pared[0], 20)
            self.son("tono_pared", xy=(x + sx * dd, y + sy * dd), tono=max(0.6, 1.6 - pared[0] / 40), ref=6, maxd=60, cat="interfaz")
        else:
            partes.append("despejado más de 60 metros")
            self.son("tono_libre", xy=(x + sx * 15, y + sy * 15), ref=8, maxd=60, cat="interfaz")
        self.decir(f"Al {M.cardinal(rumbo)}: " + "; ".join(partes) + ".", True)

    # ------------------------------------------------------------------ radar
    def _radar_construir(self):
        x, y = self.pos()
        f = self.cfg["radar_filtro"]
        lista = []
        if f in ("todo", "lugares"):
            lista += [(l.nombre, l.x, l.y, l) for l in self.mundo.lugares.values() if math.hypot(l.x - x, l.y - y) <= 110]
        if f in ("todo", "vehiculos"):
            lista += [(v.nombre + (", vehículo aparcado" if v.ia == "aparcado" else ", policía" if v.ia == "policia" else ", en marcha" if v.ia else ", vehículo parado"), v.x, v.y, v)
                      for v in self.vehiculos if v is not self.j.veh and not v.muerto and v.dist(x, y) <= 70]
        if f in ("todo", "personas"):
            lista += [(p.nombre + (" hostil" if p.hostil else ""), p.x, p.y, p) for p in self.personas if not p.muerto and p.dist(x, y) <= 60]
            lista += [(r.nombre + (", tu amigo, al volante" if r.veh else ", tu amigo, a pie"), r.x, r.y, r) for r in getattr(self, "remotos", {}).values()
                      if r.mapa == self.mundo.id and r.visto and r.dist(x, y) <= 200]
        if f in ("todo", "objetos"):
            lista += [(o.nombre, o.x, o.y, o) for o in self.objetos if o.dist(x, y) <= 90]
        lista.sort(key=lambda e: math.hypot(e[1] - x, e[2] - y))
        return lista

    def radar(self, delta):
        x, y = self.pos()
        if self.mision:
            self.mision["radar_usado"] = True                    # hay ejercicios de tutorial que piden haberlo usado
        actual = self.radar_lista[self.radar_idx][3] if 0 <= self.radar_idx < len(self.radar_lista) else None
        self.radar_lista = self._radar_construir()
        if not self.radar_lista:
            self.radar_idx = -1
            self.app.son("error")
            self.decir("El radar no detecta nada cerca.", True)
            return
        idx = next((k for k, e in enumerate(self.radar_lista) if e[3] is actual), None)
        if idx is None:
            idx = 0 if delta > 0 else len(self.radar_lista) - 1
        else:
            idx = (idx + delta) % len(self.radar_lista)
        self.radar_idx = idx
        nom, ex, ey, _ = self.radar_lista[idx]
        d = math.hypot(ex - x, ey - y)
        if d > 0.5:
            f = min(d, 18) / d
            self.son("radar", xy=(x + (ex - x) * f, y + (ey - y) * f), ref=6, maxd=60, cat="interfaz")
        self.decir(f"{self.situar(ex, ey, nom)}. {idx + 1} de {len(self.radar_lista)}.", True)

    def baliza_radar(self):
        if not (0 <= self.radar_idx < len(self.radar_lista)):
            self.decir("Primero elige algo con el radar, pulsando Tabulador.", True)
            return
        nom, ex, ey, obj = self.radar_lista[self.radar_idx]
        sigue = obj if isinstance(obj, (Vehiculo, Persona)) else None
        # Si ya ibas a algún sitio, esto es un desvío: el destino de antes se guarda y vuelve solo al llegar a esto.
        antes = self.gps.get("anterior") or self.gps if self.gps else None
        if antes is not None and math.hypot(antes["dest"][0] - ex, antes["dest"][1] - ey) < 3:
            antes = None                                         # es el mismo sitio: no hay desvío que valga
        self.fijar_gps(ex, ey, nom, sigue=sigue)
        if antes is not None and self.gps:
            self.gps["anterior"] = antes
            self.decir(f"Desvío a {nom}. Al llegar, el GPS vuelve a {antes['nombre']}. Con Mayúsculas G cancelas el desvío y vuelves a lo que llevabas.")

    def _volver_del_desvio(self, texto=""):
        """Se acabó el desvío marcado con el radar: el GPS vuelve al destino que había. False si no había ninguno."""
        antes = (self.gps or {}).get("anterior")
        if antes is None:
            return False
        self.gps = antes
        antes["clave"] = None
        self.t_gps = 0.0
        self._recalcular_gps()
        self.app.son("notificacion")
        self.decir(f"{texto} El GPS vuelve a {antes['nombre']}.".strip())
        return True

    # -------------------------------------------------------------------- GPS
    def fijar_gps(self, x, y, nombre, sigue=None, auto=False, radio=None, callar=False):
        self.gps = {"dest": (x, y), "nombre": nombre, "ruta": [], "clave": None, "recordado": None,
                    "sigue": sigue, "auto": auto, "radio": radio}
        self.t_gps = 0.0
        self._recalcular_gps()
        if callar:
            self.gps["clave"] = self._instruccion()[0]
        else:
            self.app.son("notificacion")

    def gps_a_lugar(self, lugar, auto=False, callar=False):
        if lugar.mapa != self.mundo.id:
            con = self.conexion_hacia(lugar.mapa)
            destino = self.mapas[lugar.mapa].nombre
            if con is None:
                self.decir(f"{lugar.nombre} está en {destino}, pero no encuentro cómo llegar desde aquí.")
                return
            como = {"salida": "Coge la carretera en un vehículo", "estacion": "Toma el autobús", "embarcadero": "Zarpa en barco",
                    "muelle": "Atraca", "helipuerto": "Vuela"}.get(con.tipo, "Ve")
            self.fijar_gps(con.x, con.y, con.nombre, auto=auto, callar=True, radio=6 if con.tipo != "salida" else None)
            self.gps["final"] = lugar.id
            if not callar:
                self.app.son("notificacion")
            self.decir(f"{lugar.nombre} está en {destino}. {como}: te guío hasta {con.nombre}.")
            return
        self.fijar_gps(lugar.x, lugar.y, lugar.nombre, auto=auto, callar=callar)

    def cancelar_gps(self, hablar=False):
        if hablar and self._volver_del_desvio("Dejas el desvío."):       # lo quita el jugador: primero se deshace el desvío
            return
        if hablar:
            self.app.son("menu_atras" if self.gps else "error")
            self.decir("GPS cancelado." if self.gps else "No hay ningún destino marcado.", True)
        self.gps = None

    def repetir_gps(self):
        if not self.gps:
            self.decir("No hay destino marcado. Pulsa L para elegir un lugar o M para abrir el móvil.", True)
            return
        self._recalcular_gps()
        clave, texto = self._instruccion()
        self.gps["clave"] = clave
        self.decir(texto, True)

    def _recalcular_gps(self):
        g = self.gps
        if g["sigue"] is not None:
            s = g["sigue"]
            if getattr(s, "muerto", False):
                if not self._volver_del_desvio():
                    self.gps = None
                return
            g["dest"] = (s.x, s.y)
        x, y = self.pos()
        d = math.hypot(g["dest"][0] - x, g["dest"][1] - y)
        if not self.j.veh and (d < 6 or (d < 95 and self._linea_libre(x, y, g["dest"][0], g["dest"][1]))):       # recto solo si no hay un edificio en medio
            g["ruta"] = [g["dest"]]         # a pie y a la vista: directo al destino
        else:
            ruta = self.mundo.ruta(x, y, g["dest"][0], g["dest"][1])
            cerca = 12 if not self.j.veh else 8
            # un cruce cuenta como alcanzado al llegar a él (a pie, a su esquina)
            while len(ruta) > 1 and math.hypot(ruta[0][0] - x, ruta[0][1] - y) < cerca:
                ruta.pop(0)
            vieja = [p for p in g["ruta"]] if g["sigue"] is None else []
            while len(vieja) > 1 and math.hypot(vieja[0][0] - x, vieja[0][1] - y) < cerca:
                vieja.pop(0)
            if len(vieja) > 1 and (abs(vieja[0][0] - x) < 12 or abs(vieja[0][1] - y) < 12) and                     vieja[-1] == ruta[-1] and self._largo(x, y, vieja) <= self._largo(x, y, ruta) + 15:
                ruta = vieja            # entre rutas igual de cortas, no se cambia de idea
            g["ruta"] = ruta

    @staticmethod
    def _largo(x, y, ruta):
        d = math.hypot(ruta[0][0] - x, ruta[0][1] - y)
        return d + sum(math.hypot(ruta[k + 1][0] - ruta[k][0], ruta[k + 1][1] - ruta[k][1]) for k in range(len(ruta) - 1))

    def _linea_libre(self, x0, y0, x1, y1):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / 2.0))
        return all(self.mundo.transitable(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(1, n))

    def _instruccion(self):
        g = self.gps
        ruta = g["ruta"]
        x, y = self.pos()
        v = self.j.veh
        relativo = bool(v) or self.cfg["movimiento"] == "giro"
        if not ruta:
            return ("fin", f"{g['nombre']}: estás en el destino.")
        if len(ruta) == 1:
            p1 = ruta[0]
            return ("fin", f"Destino, {self.situar(p1[0], p1[1], g['nombre'])}.")
        # se saltan los cruces en los que solo hay que seguir recto
        k = 0
        ant = (x, y)
        d1 = 0.0
        while True:
            p1, p2 = ruta[k], ruta[k + 1]
            d1 += math.hypot(p1[0] - ant[0], p1[1] - ant[1])
            r1 = M.rumbo_a(p1[0] - ant[0], p1[1] - ant[1]) if math.hypot(p1[0] - ant[0], p1[1] - ant[1]) > 4 else M.rumbo_a(p2[0] - p1[0], p2[1] - p1[1])
            if k == 0:
                r_ini = r1
            r2 = M.rumbo_a(p2[0] - p1[0], p2[1] - p1[1])
            giro = M.norm180(r2 - r1)
            if abs(giro) >= 30 or k + 2 >= len(ruta):
                break
            ant = p1
            k += 1
        ruta = ruta[k:]
        r1 = r_ini
        ultimo = len(ruta) == 2 and math.hypot(p2[0] - p1[0], p2[1] - p1[1]) < 12
        via = self.mundo.nombre_tramo(p1, p2)
        clave = (int(p1[0]), int(p1[1]), len(ruta))
        total = d1 + sum(math.hypot(ruta[k + 1][0] - ruta[k][0], ruta[k + 1][1] - ruta[k][1]) for k in range(len(ruta) - 1))
        pre = ""
        if v and abs(M.norm180(r1 - v.rumbo)) > 120 and d1 > 8:
            pre = "Da media vuelta: frena y pulsa U. "
        elif not relativo:
            pre = f"Ve hacia el {M.cardinal(r1)}. "
        if ultimo:
            if relativo:
                lado = "a la derecha" if giro > 0 else "a la izquierda"
            else:
                lado = "al " + M.cardinal(r2)
            return (clave, f"{pre}En {M.metros(d1)}, tu destino, {g['nombre']}, queda {lado}.")
        if abs(giro) < 30:
            return (clave, f"{pre}Sigue recto {M.metros(total)} hasta {g['nombre']}.")
        elif relativo:
            accion = ("gira a la derecha" if giro > 0 else "gira a la izquierda") + f" por {via}"
        else:
            accion = f"gira hacia el {M.cardinal(r2)} por {via}"
        return (clave, f"{pre}En {M.metros(d1)}, {accion}. Faltan {M.metros(total)} hasta {g['nombre']}.")

    def giro_gps(self):
        """Giro que pide el GPS en el próximo cruce: -1, 0 o 1 (para el piloto del GPS)."""
        g = self.gps
        if not g or len(g["ruta"]) < 2 or not self.j.veh:
            return 0
        x, y = self.pos()
        p1, p2 = g["ruta"][0], g["ruta"][1]
        if math.hypot(p1[0] - x, p1[1] - y) > 70:
            return 0
        if len(g["ruta"]) == 2 and math.hypot(p2[0] - p1[0], p2[1] - p1[1]) < 15:
            return 0            # lo siguiente ya es la puerta del destino, no un giro
        giro = M.norm180(M.rumbo_a(p2[0] - p1[0], p2[1] - p1[1]) - self.j.veh.rumbo)
        if abs(giro) < 45:
            return 0
        if abs(giro) > 135:
            return 2
        return 1 if giro > 0 else -1

    def _gps(self, dt):
        g = self.gps
        if not g:
            return
        self.t_gps -= dt
        if self.t_gps <= 0:
            self.t_gps = 0.7
            self._recalcular_gps()
            g = self.gps
            if not g:
                return
            x, y = self.pos()
            d = math.hypot(g["dest"][0] - x, g["dest"][1] - y)
            radio = g["radio"] or (16 if self.j.veh else 5)
            # a pie no se da por llegado en mitad de la calzada: el aviso llega al pisar la acera, delante de la puerta
            llegado = d <= radio and (self.j.veh is not None or d < 1.5 or self.mundo.tipo == "mar" or self.mundo.superficie(x, y) != "calzada")
            if llegado and g.get("final"):
                if not g.get("avisado"):
                    g["avisado"] = True
                    self.app.son("llegada")
                    self.decir(f"{g['nombre']}. Pulsa Intro para continuar el viaje.")
            elif llegado and not g["auto"] and g["sigue"] is None:
                self.app.son("llegada")
                self.app.vibrar(0.2, 0.6, 150)
                if not self._volver_del_desvio(f"Has llegado a {g['nombre']}."):
                    self.decir(f"Has llegado a {g['nombre']}.")
                    self.gps = None
                return
            if self.cfg["gps_voz"]:
                clave, texto = self._instruccion()
                if clave != g["clave"]:
                    g["clave"] = clave
                    self.decir(texto)
                    if texto.startswith("En ") or " En " in texto:
                        try:
                            if int(texto.split("En ")[1].split(" ")[0]) < (60 if self.j.veh else 14):
                                g["recordado"] = clave
                        except ValueError:
                            pass
                elif clave != "fin" and g["recordado"] != clave and g["ruta"]:
                    p1 = (clave[0], clave[1])
                    if math.hypot(p1[0] - x, p1[1] - y) < (40 if self.j.veh else 10):
                        g["recordado"] = clave
                        self.decir(texto.split(". Faltan")[0].replace("Da media vuelta: frena y pulsa U. ", "").rstrip(".") + ".")
        # baliza sonora hacia el siguiente punto
        if not self.cfg["baliza"] or not g["ruta"]:
            return
        self.t_baliza -= dt
        if self.t_baliza <= 0:
            x, y = self.pos()
            bx, by = g["ruta"][0]
            final = len(g["ruta"]) == 1
            if not final and not self.j.veh:
                # a pie la baliza suena en la esquina de la acera, no en mitad del cruce
                bx += 7.5 if x >= bx else -7.5
                by += 7.5 if y >= by else -7.5
            d = math.hypot(bx - x, by - y)
            if d > 0.3:
                f = min(d, 22) / d
                self.son("baliza_destino" if final else "baliza", xy=(x + (bx - x) * f, y + (by - y) * f),
                         ref=8, maxd=70, vol=0.8, cat="interfaz")
            self.t_baliza = max(0.3, min(1.6, d / 45.0))

    # ----------------------------------------------------------------- a pie
    def alternar_paseo(self):
        """Caminar solo: el personaje sigue a pie la ruta del GPS sin que haya que llevarlo."""
        if getattr(self, "paseo_auto", False):
            self.parar_paseo("Dejas de caminar solo.")
        elif not self.gps:
            self.app.son("error")
            self.decir("Para caminar solo, marca antes un destino en el GPS con la tecla L.", True)
        else:
            self.paseo_auto = True
            self.t_paseo_atasco = 0.0
            self.app.son("menu_ok")
            self.decir(f"Caminas solo hacia {self.gps['nombre']}. Mantén Mayúsculas para correr. Cualquier flecha te detiene.", True)

    def parar_paseo(self, mensaje=None):
        if getattr(self, "paseo_auto", False):
            self.paseo_auto = False
            if mensaje:
                self.app.son("menu_atras")
                self.decir(mensaje, True)

    def caminar(self, dt):
        j = self.j
        t = self.app.teclas
        if self.forzando:
            self._forzar(dt)
        dx = dy = 0.0
        if self.cfg["movimiento"] == "brujula":
            dy += 1 if pygame.K_UP in t else 0
            dy -= 1 if pygame.K_DOWN in t else 0
            dx += 1 if pygame.K_RIGHT in t else 0
            dx -= 1 if pygame.K_LEFT in t else 0
        else:
            av = (1 if pygame.K_UP in t else 0) - (0.6 if pygame.K_DOWN in t else 0)
            rad = math.radians(j.rumbo)
            dx, dy = math.sin(rad) * av, math.cos(rad) * av
        solo = False
        if getattr(self, "paseo_auto", False):
            if dx or dy:
                self.parar_paseo("Dejas de caminar solo.")
            elif not self.gps:
                self.paseo_auto = False             # ha llegado: el GPS ya lo ha dicho
            else:
                ruta = self.gps["ruta"]
                bx, by = ruta[0]
                if len(ruta) > 1:                   # en los cruces intermedios va por la esquina de la acera, no por el centro
                    bx += 7.5 if j.x >= bx else -7.5
                    by += 7.5 if j.y >= by else -7.5
                ddx, ddy = bx - j.x, by - j.y
                n = math.hypot(ddx, ddy)
                if n > 0.3:
                    dx, dy = ddx / n, ddy / n
                    j.rumbo = M.rumbo_a(dx, dy)
                    solo = True
        if dx == 0 and dy == 0:
            return
        if self.forzando:
            self.forzando["canal"].parar()
            self.forzando = None
            self.decir("Dejas de forzar la cerradura.")
        correr = self.corriendo_ahora()
        vel = (1.3 if j.agachado else 6.0 * (1 + 0.015 * self.nivel("resistencia")) if correr else 2.6) * self.mod_velocidad() * self.mod_necesidades()
        n = math.hypot(dx, dy)
        if self.cfg["movimiento"] == "brujula" and not solo:
            j.rumbo = M.rumbo_a(dx, dy)
            dx, dy = dx / n, dy / n
        tambaleo = self.deriva()
        if tambaleo:
            ang = math.sin(self.t * 1.3) * tambaleo * 1.3
            dx, dy = dx * math.cos(ang) - dy * math.sin(ang), dx * math.sin(ang) + dy * math.cos(ang)
        paso = vel * dt
        nx, ny = j.x + dx * paso, j.y + dy * paso
        movido = 0.0
        if self.mundo.transitable(nx, ny):
            movido = paso
            j.x, j.y = nx, ny
        elif dx and self.mundo.transitable(nx, j.y):
            movido = abs(dx) * paso
            j.x = nx
        elif dy and self.mundo.transitable(j.x, ny):
            movido = abs(dy) * paso
            j.y = ny
        if solo and movido < paso * 0.5:
            # Caminando solo, si no se puede ir recto hacia el punto (al doblar una esquina se queda un palmo fuera de la acera),
            # se avanza a paso normal por el lado que esté libre, empezando por el que corrige el desvío.
            ejes = sorted((((math.copysign(paso, dx), 0.0), abs(dx)), ((0.0, math.copysign(paso, dy)), abs(dy))), key=lambda e: e[1])
            for (ax, ay), peso in ejes:
                if peso > 0.02 and self.mundo.transitable(j.x + ax, j.y + ay):
                    j.x, j.y = j.x + ax, j.y + ay
                    movido = paso
                    break
        if solo:
            self.t_paseo_atasco = self.t_paseo_atasco + dt if movido < paso * 0.5 else 0.0
            if self.t_paseo_atasco > 2.5:
                self.parar_paseo("Hay un obstáculo y no puedo seguir solo. Sigue tú con las flechas.")
        if movido < paso * 0.5:
            if self.t - self.t_pared > 0.7:
                self.t_pared = self.t
                self.son("choque_pared", vol=0.7)
                self.app.vibrar(0.4, 0.0, 90)
                if self.t - self.t_pared_voz > 3:
                    self.t_pared_voz = self.t
                    s = self.mundo.superficie(nx, ny)
                    self.decir("Fin de la ciudad. No puedes seguir por aquí." if s == "fuera" else "Pared.")
        if movido <= 0:
            return
        j.stats["metros_pie"] += movido
        if correr:
            self.ganar_xp("resistencia", movido / 25.0)
        self.dist_paso += movido
        if self.dist_paso >= (1.5 if correr else 0.85):
            self.dist_paso = 0.0
            self.pie ^= 1
            s = "via" if self.mundo.tipo != "mar" and self.mundo.sobre_vias(j.x, j.y) else self.mundo.superficie(j.x, j.y)      # sobre las vías se pisa distinto
            nombre = f"paso_{s}{self.pie}"
            if nombre not in self.mez.sonidos:
                nombre = f"paso_acera{self.pie}"
            self.son(nombre, vol=0.35 if j.agachado else 0.6, tono=random.uniform(0.93, 1.07), pan=-0.15 if self.pie else 0.15)

    def interactuar(self):
        from . import menus_juego as mj
        j = self.j
        x, y = self.pos()
        if self.agente_intro():                                  # de servicio: detener a quien se ha rendido, o tratar con el conductor que ha parado
            return
        mar = self.mundo.tipo == "mar"
        if not j.veh or mar:
            for o in sorted(self.objetos, key=lambda o: o.dist(x, y)):
                if o.dist(x, y) <= (10.0 if mar else 3.0):
                    self.recoger(o)
                    return
        l = self.lugar_cercano(26 if mar else 16 if j.veh else 7)
        if l:
            m = self.mision_en_lugar(l.id)
            if m and not self.mision:
                if j.veh and abs(j.veh.vel) > 2:
                    self.decir("Detén el vehículo primero.", True)
                    return
                self.iniciar_mision(m)
                return
            mj.lugar(self, l)
            return
        if not j.veh:
            cerca = [p for p in self.personas if not p.muerto and p.dist(x, y) < 3.5]
            if cerca:
                p = min(cerca, key=lambda p: (p.tipo in ("perro", "aliado"), p.tipo == "aliado", p.dist(x, y)))     # primero la gente de la calle; tu perro y los tuyos siempre están al lado
                if p.tipo == "perro":
                    from . import menus_extra
                    menus_extra.menu_perro(self)
                elif p.tipo == "aliado":
                    self.son("murmullo", xy=(p.x, p.y))
                    self.decir(f"{p.nombre}: " + random.choice(("Aquí estoy. Tú mandas.", "Todo tranquilo por ahora.", "Yo te cubro.", "Cuando quieras nos movemos.")), True)
                elif p.hostil:
                    self.decir(f"{p.nombre} no quiere hablar.", True)
                else:
                    self.son("murmullo", xy=(p.x, p.y))
                    self.decir(f"{p.nombre}: {random.choice(gente.lista('frases'))}", True)
                return
        self.decir("Aquí no hay nada con lo que interactuar. Pulsa Tabulador para explorar con el radar.", True)

    def recoger(self, o):
        j = self.j
        if o.canal:
            o.canal.parar()
        if o in self.objetos:
            self.objetos.remove(o)
        if o.tipo in ("municion", "arma"):                       # lo que suelta un enemigo caído
            self.recoger_botin(o)
            return
        self.son("recoger", cat="interfaz")
        if o.tipo == "dinero":
            self.dar_dinero(o.valor, "Recoges dinero")
        elif o.tipo == "casete":
            j.casetes.append(o.tag)
            n = len(j.casetes)
            total = self.total_casetes()
            premio = self.precio("casete_premio", 250)
            self.dar_dinero(premio)
            self.decir(f"Has encontrado un objeto de colección, {o.nombre}: llevas {n} de {total}. Premio de {premio} euros.")
            if n % 5 == 0 and n != total:                      # cada cinco, un premio y algo de fama
                self.dar_dinero(self.precio("casete_cinco", 1000))
                self.cambiar_reputacion(2)
                self.decir(f"Ya son {n}. Un coleccionista te adelanta {self.precio('casete_cinco', 1000)} euros y tu nombre empieza a sonar.")
            if n == total:
                self.cambiar_reputacion(5)
                self.dar_dinero(self.precio("casete_todos", 20000))
                self.decir(f"¡Has encontrado todos los objetos de colección! Un coleccionista te paga {self.precio('casete_todos', 20000)} euros por el lote completo.")
        elif o.tipo == "mision":
            self.decir(f"Tienes: {o.nombre}.")
            if self.mision and self.mision.get("objeto") is o:
                self.mision["objeto"] = None
                self.mision["recogido"] = True

    def usar_botiquin(self):
        j = self.j
        if j.objetos.get("botiquin", 0) <= 0:
            self.app.son("error")
            self.decir("No te quedan botiquines.", True)
        elif j.salud >= j.salud_max:
            self.decir("Tu salud ya está al máximo.", True)
        else:
            j.objetos["botiquin"] -= 1
            j.salud = min(j.salud_max, j.salud + 50)
            self.son("curar", cat="interfaz")
            self.decir(f"Usas un botiquín. Salud {int(j.salud)}. Te quedan {j.objetos['botiquin']}.", True)

    def teletransportar(self, x, y):
        j = self.j
        if j.veh:
            self.salir_vehiculo(forzado=True)
        j.x, j.y = self.mundo.punto_libre(x, y)
        self.cruce_act = self.mundo.cruce(j.x, j.y)
        self.lugar_act = self.lugar_cercano(7)

    # ------------------------------------------------------------ actualización
    def mayus_soltada(self):
        """Con «correr con una pulsación»: al soltar la Mayúsculas izquierda sin haber pulsado nada más, cambia entre andar y correr."""
        if getattr(self, "_mayus_sola", False) and pygame.K_LSHIFT not in self.app.teclas:
            self._mayus_sola = False
            if self.cfg["correr_alternar"] and not self.j.veh:
                self.correr_fijo = not getattr(self, "correr_fijo", False)
                self.app.son("menu_mover")
                self.decir("Correr." if self.correr_fijo else "Andar.", True)

    def actualizar(self, dt):
        dt = min(dt, 0.05)
        j = self.j
        self.t += dt
        self.mayus_soltada()
        if self.resumen_pendiente and self.t > 2.0 and not self.mision:
            self.resumen_pendiente = False
            self.decir("Hace días que no jugabas. " + self.resumen_historia() + " Lo tienes también en el móvil, en Diario.")
        if getattr(self, "_upnp_aviso", None):
            aviso, self._upnp_aviso = self._upnp_aviso, None
            self.decir(aviso)
        dt = self._paso_lento(dt)
        if self.cubierto and (j.veh or math.hypot(j.x - self.cubierto[0], j.y - self.cubierto[1]) > 0.8):
            self.dejar_cobertura()
        if self.acompanante:
            from . import sistemas
            sistemas.paso_acompanante(self, dt)
        if self.mundo.tipo != "mar":
            from . import transporte
            transporte.paso(self, dt)                           # tranvías por las vías, y los trenes y aviones que se oyen de lejos
        j.stats["tiempo"] += dt
        self._tiempo(dt)
        if j.veh:
            self.conducir(dt)
        elif self.mundo.tipo == "mar":
            if self.nadar(dt):
                return                                          # te has ahogado o has llegado a un muelle: ha cambiado el mapa
        else:
            self.caminar(dt)
        if self.pesca:
            self.actualizar_pesca(dt)
        self.actualizar_vehiculos(dt)
        self.actualizar_chofer(dt)
        self.actualizar_personas(dt)
        self.actualizar_policia(dt)
        self.actualizar_combate(dt)
        if self.transicion:
            return
        self.actualizar_mision(dt)
        self.actualizar_trabajo(dt)
        self.actualizar_extras(dt)
        self.actualizar_adultos(dt)
        self.actualizar_calle(dt)
        self.actualizar_reconquista(dt)
        self.actualizar_guerra(dt)
        self.actualizar_domicilio(dt)
        self.actualizar_atracos(dt)
        self.actualizar_reacciones(dt)
        self.actualizar_convivencia(dt)
        self.actualizar_agente(dt)
        self.t_poblar -= dt
        if self.t_poblar <= 0:
            self.t_poblar = 0.6
            self._poblar()
        self._avisos(dt)
        self._gps(dt)
        self._ambiente(dt)
        x, y = self.pos()
        if j.veh:
            self.oy_rumbo += M.norm180(j.veh.rumbo - self.oy_rumbo) * min(1.0, dt * 4)
        self.mez.situar_oyente(x, y, self.frente())
        # dónde suena todo: el eco del barrio, y la altura si vas volando (solo lo usa el motor envolvente)
        from .audio_al import entorno_de
        self.mez.entorno = entorno_de(self.mundo.barrio(x, y).get("ambiente", ""))
        self.mez.altura = 35.0 if (j.veh is not None and j.veh.modelo.get("vuela")) else 0.0

    def _tiempo(self, dt):
        antes = int(self.reloj // 60)
        self.reloj += dt / 2.0
        self.pasar_necesidades(dt / 2.0)
        self.pasar_perro(dt / 2.0)
        self.sorteo_loteria()
        if self.en_servidor:
            self.reloj = min(self.reloj, 1439.9)                 # en un servidor, el día lo cambia el servidor para todos a la vez
        elif self.reloj >= 1440:
            self.reloj -= 1440
            self.dia += 1
            self.plazas_usadas.clear()
            self._cobrar_negocios()
            self.sortear_dia()
        hora = int(self.reloj // 60)
        if hora != antes:
            r = 1.0 if self.en_servidor else random.random()     # y también si llueve
            if self.lluvia and r < 0.4:
                self.lluvia = False
                self.son("pajaro", cat="ambiente")
                self.decir("Deja de llover.")
            elif not self.lluvia and r < 0.08:
                self.lluvia = True
                self.son("trueno", cat="ambiente")
                self.decir("Empieza a llover. El asfalto mojado alarga las frenadas.")
            # las horas del día también se oyen
            h = hora % 24
            if h == 7:
                self.son("gallo" if self.mundo.tipo != "mar" else "gaviota", cat="ambiente", vol=0.6)
                self.decir("Amanece.")
            elif h == 21:
                self.son("buho" if self.mundo.tipo != "mar" else "sirena_barco", cat="ambiente", vol=0.5)
                self.decir("Anochece.")
            elif h == 0 and self.mundo.tipo != "mar":
                self.son("campanadas", cat="ambiente", vol=0.5)

    def _cobrar_negocios(self):
        total = 0
        for pid in self.j.propiedades:
            l = self.lugares.get(pid)
            if l and l.tipo == "negocio":
                total += int(l.get("ingresos", 0))
        self.repartir_ingresos_negocios(total)
        self.cobrar_banco()
        self.ingresos_territorios()
        from . import sistemas
        sistemas.paga(self)
        sistemas.sucesos_territorio(self)
        self.rentas_decisiones()
        self.mover_bolsa()
        self.dia_adultos()
        self.dia_intimidad()
        self.dia_convivencia()
        self.dia_pactos()
        self.dia_reconquista()
        n = sum(1 for p in self.personas if p.tipo == "aliado" and not p.muerto and not getattr(p, "de_banda", False))      # la banda cobra aparte
        if n:
            coste = self.precio("guardaespaldas_sueldo", 200) * n
            if self.j.dinero >= coste:
                self.j.dinero -= coste
                self.decir(f"Pagas {coste} euros de sueldo a tus guardaespaldas.")
            else:
                self.personas = [p for p in self.personas if p.tipo != "aliado" or getattr(p, "de_banda", False)]
                self.decir("No puedes pagar a tus guardaespaldas y se marchan.")

    def pasar_horas(self, horas, dormir=False):
        self.pasar_necesidades(horas * 60, durmiendo=dormir)
        self.pasar_perro(horas * 60)
        if self.en_servidor:
            return                                               # en un servidor el reloj es de todos: dormir no lo adelanta
        self.reloj += horas * 60
        while self.reloj >= 1440:
            self.reloj -= 1440
            self.dia += 1
            self.plazas_usadas.clear()
            self._cobrar_negocios()
            self.sortear_dia()
        self.rec_pasar_horas(horas)

    def _avisos(self, dt):
        j = self.j
        x, y = self.pos()
        b = self.mundo.barrio(x, y)
        if b["id"] != self.barrio_act:
            primera = self.barrio_act is None
            self.barrio_act = b["id"]
            nuevo = b["id"] not in j.barrios_vistos
            if nuevo:
                j.barrios_vistos.append(b["id"])
            if self.cfg["anunciar_barrios"] and not primera:
                # la primera vez que pisas un barrio, además del nombre, cómo es
                if nuevo and self.cfg["describir_zonas"] and b.get("descripcion"):
                    self.decir(f"Entras en {b['nombre']} por primera vez. {self.barrio_desc(b)}")
                else:
                    self.decir(f"Entras en {b['nombre']}.")
        if not j.veh or not self.modo_asistido():
            c = self.mundo.cruce(x, y)
            if c != self.cruce_act:
                self.cruce_act = c
                if c and self.cfg["anunciar_cruces"]:
                    self.son("cruce", cat="interfaz", vol=0.6)
                    self.decir(self.mundo.describir(x, y) + ".")
        s = self.mundo.superficie(x, y)
        if not j.veh and self.mundo.tipo != "mar":
            s = self.mundo.sobre_vias(x, y) or s                # a pie se avisa al pisar las vías, del tranvía o del tren, como con la acera o la calzada
        if s != self.sup_act:
            if self.cfg["anunciar_superficie"] and not j.veh and self.sup_act is not None:
                self.decir(M.SUPERFICIE_TXT[s].capitalize() + ".")
            self.sup_act = s
        self.t_lugares -= dt
        if self.t_lugares <= 0:
            self.t_lugares = 0.3
            self._lugares_cercanos(x, y)
        # semáforo acústico del cruce más cercano
        if self.cfg["semaforos"] and not j.veh and self.mundo.tipo != "mar":
            self.t_semaforo -= dt
            if self.t_semaforo <= 0:
                i = self.mundo._idx(x, self.mundo.NX)
                jj = self.mundo._idx(y, self.mundo.NY)
                cx, cy = i * M.B, jj * M.B
                if math.hypot(cx - x, cy - y) < 32:
                    if self.mundo.verde_vertical(i, jj, self.t):
                        self.son("semaforo_tic", xy=(cx, cy), ref=6, maxd=40, vol=0.5)
                        self.t_semaforo = 0.25
                    else:
                        self.son("semaforo_pio", xy=(cx, cy), ref=6, maxd=40, vol=0.5)
                        self.t_semaforo = 0.9
                else:
                    self.t_semaforo = 0.5

    def lugar_abierto(self, l):
        req = l.get("requiere")
        return not req or req in self.completadas

    def _lugares_cercanos(self, x, y):
        j = self.j
        radio = 26 if self.mundo.tipo == "mar" else 16 if j.veh else 7
        mejor = None
        activos = set()
        marcas = {m["lugar"] for m in self.misiones_disponibles() if not m.get("tutorial") or m["id"] == "tut01"} if not self.mision else set()
        for l in self.mundo.lugares.values():
            d = math.hypot(l.x - x, l.y - y)
            if d <= radio and (mejor is None or d < mejor[0]):
                mejor = (d, l)
            alc = 160 if self.mundo.tipo == "mar" else 48
            if d < alc + 7 and self.cfg["localizador"]:
                activos.add(l.id)
                if l.id not in self.canales_lugar:
                    self.canales_lugar[l.id] = self.son(l.sonido, xy=(l.x, l.y), bucle=True, ref=3 if alc < 100 else 12, maxd=alc, vol=0.7, cat="ambiente")
            if l.id in marcas and d < 80:
                clave = "m:" + l.id
                activos.add(clave)
                if clave not in self.canales_lugar:
                    self.canales_lugar[clave] = self.son("loc_mision", xy=(l.x, l.y), bucle=True, ref=6, maxd=80, vol=0.9, cat="ambiente")
        for k in [k for k in self.canales_lugar if k not in activos]:
            self.canales_lugar.pop(k).parar()
        nuevo = mejor[1] if mejor else None
        if nuevo is not self.lugar_act:
            self.lugar_act = nuevo
            if nuevo:
                if nuevo.id not in j.visitados:
                    j.visitados.append(nuevo.id)
                if self.cfg["anunciar_lugares"]:
                    extra = ""
                    if nuevo.id in marcas:
                        m = self.mision_en_lugar(nuevo.id)
                        extra = f" Misión disponible: {m['titulo']}. Pulsa Intro para empezarla."
                    elif j.veh and nuevo.tipo not in ("taller", "desguace", "casa", "carrera", "salida", "muelle"):
                        extra = ""
                    elif nuevo.tipo in ("muelle", "salida", "embarcadero", "estacion", "pesca"):
                        extra = " Pulsa Intro."
                    elif nuevo.tipo != "monumento":
                        extra = " Pulsa Intro para entrar."
                    self.decir(nuevo.nombre + "." + extra)
        # objetos: bucle localizador y recogida automática del dinero
        for o in list(self.objetos):
            d = o.dist(x, y)
            if d < 50 and o.canal is None:
                o.canal = self.son(o.sonido, xy=(o.x, o.y), bucle=True, ref=3, maxd=50, vol=0.8)
            elif d > 60 and o.canal is not None:
                o.canal.parar()
                o.canal = None
            if o.tipo in ("dinero", "municion", "arma") and d < 1.8 and not j.veh:
                self.recoger(o)

    def _ambiente(self, dt):
        x, y = self.pos()
        b = self.mundo.barrio(x, y)
        nombre = b["ambiente"]
        noche = self.es_noche()
        if nombre != self.amb_nombre and self.mez.pedir(nombre):      # los ambientes largos se cargan al entrar en el barrio
            if self.amb_canal:
                self.amb_canal.parar()
            self.amb_nombre = nombre
            self.amb_canal = self.son(nombre, bucle=True, cat="ambiente", vol=0.5)
            self.mez.soltar({nombre, "amb_noche", "lluvia"} if (noche or self.lluvia) else {nombre})
        if self.amb_canal:
            self.amb_canal.volumen(0.22 if noche else 0.5)
        if noche and self.noche_canal is None and self.mez.pedir("amb_noche"):
            self.noche_canal = self.son("amb_noche", bucle=True, cat="ambiente", vol=0.4)
        elif not noche and self.noche_canal is not None:
            self.noche_canal.parar()
            self.noche_canal = None
        if self.lluvia and self.lluvia_canal is None and self.mez.pedir("lluvia"):
            self.lluvia_canal = self.son("lluvia", bucle=True, cat="ambiente", vol=0.6)
        elif not self.lluvia and self.lluvia_canal is not None:
            self.lluvia_canal.parar()
            self.lluvia_canal = None
        self.t_azar -= dt
        if self.t_azar <= 0:
            self.t_azar = random.uniform(4, 11)
            a = random.uniform(0, 2 * math.pi)
            d = random.uniform(18, 45)
            pos = (x + math.sin(a) * d, y + math.cos(a) * d)
            if self.lluvia and random.random() < 0.35:
                self.son("trueno", xy=pos, ref=30, maxd=200, cat="ambiente")
                return
            ops = {"amb_puerto": ["gaviota", "gaviota", "martillo"], "amb_playa": ["gaviota", "pajaro"],
                   "amb_ciudad": ["claxon_lejano", "sirena_lejana", "claxon_lejano"], "amb_industrial": ["martillo", "claxon_lejano"],
                   "amb_parque": ["pajaro", "pajaro", "ladrido"], "amb_residencial": ["ladrido", "pajaro", "claxon_lejano"]}.get(nombre, ["pajaro"])
            if noche:
                ops = [o for o in ops if o not in ("pajaro", "gaviota", "martillo")] or ["ladrido"]
            s = random.choice(ops)
            self.son(s, xy=pos, ref=10, maxd=80, cat="ambiente", vol=0.7)

    # ---------------------------------------------------------------- poblar
    def _poblar(self):
        j = self.j
        x, y = self.pos()
        m = self.mundo
        noche = self.es_noche()
        for v in list(self.vehiculos):
            if v is j.veh or v.tag or v is self.ultimo_veh or getattr(v, "id_red", None) is not None or getattr(v, "mio", False) or getattr(v, "con_chofer", False):      # el tuyo te espera donde lo dejaste; los de otros jugadores, también
                continue
            d = v.dist(x, y)
            if (v.ia == "trafico" and d > 240) or (v.ia in ("aparcado", None) and d > 170) or \
               (v.ia == "policia" and (d > 330 or (j.estrellas == 0 and d > (260 if getattr(v, "ronda", False) or getattr(v, "auxilio", None) else 110)))) or (v.ia == "trafico" and v.t_parado > 15 and d > 50) or (v.ia == "trafico" and v.t_parado > 40):   # un atasco eterno se disuelve
                self.quitar_vehiculo(v)
        for p in list(self.personas):
            if p.tag and not p.muerto:
                continue
            d = p.dist(x, y)
            if p.tipo in ("aliado", "perro") and not p.muerto:
                continue
            if d > 110 or (p.muerto and (d > 50 or self.t - p.t_estado > 25)):
                self.personas.remove(p)
        if m.tipo == "mar":
            for v in list(self.vehiculos):
                if v.ia == "barco" and v.dist(x, y) > 500:
                    self.quitar_vehiculo(v)
            if sum(1 for v in self.vehiculos if v.ia == "barco") < m.trafico:
                a = random.uniform(0, 2 * math.pi)
                d = random.uniform(180, 380)
                bx, by = x + math.sin(a) * d, y + math.cos(a) * d
                if m.transitable(bx, by):
                    ids = [i for i in m.barrios[0]["vehiculos"] if i in self.modelos] or ["lancha"]
                    v = Vehiculo(self.modelos[random.choice(ids)], bx, by, 0, "barco")
                    v.ocupado = True
                    v.rumbo = random.uniform(0, 360)
                    v.destino = m.punto_libre(random.uniform(0, m.ancho), random.uniform(0, m.alto))
                    v.vel_obj = random.uniform(5, 10)
                    self.vehiculos.append(v)
            return
        # tráfico
        n = sum(1 for v in self.vehiculos if v.ia == "trafico")
        if not self.sv_trafico_comun() and n < max(1, round((max(1, m.trafico // 2) if noche else m.trafico) * self.azar_factor("trafico"))):
            horizontal = random.random() < 0.5
            dist = random.uniform(100, 180) * random.choice([-1, 1])
            if horizontal:
                jj = max(0, min(m.NY - 1, int(round(y / M.B)) + random.choice([-1, 0, 0, 1])))
                vx = max(5.0, min(m.ancho - 5, x + dist))
                d = random.choice([1, 3])
                pos = (vx, m.carril("H", jj, d))
            else:
                ii = max(0, min(m.NX - 1, int(round(x / M.B)) + random.choice([-1, 0, 0, 1])))
                vy = max(5.0, min(m.alto - 5, y + dist))
                d = random.choice([0, 2])
                pos = (m.carril("V", ii, d), vy)
            if math.hypot(pos[0] - x, pos[1] - y) > 90 and m.cruce(pos[0], pos[1], 14) is None and \
               all(o.dist(pos[0], pos[1]) > 25 for o in self.vehiculos):
                ids = [i for i in m.barrio(pos[0], pos[1])["vehiculos"] if i in self.modelos] or ["utilitario"]
                v = Vehiculo(self.modelos[random.choice(ids)], pos[0], pos[1], d, "trafico")
                v.ocupado = True
                v.vel = v.vel_obj = random.uniform(9, 13)
                self.vehiculos.append(v)
        # coches aparcados
        mios = [v for v in self.vehiculos if getattr(v, "mio", False)]
        for pl in m.aparcados:
            if pl["id"] in self.plazas_activas or pl["id"] in self.plazas_usadas:
                continue
            if abs(pl["x"] - x) < 130 and abs(pl["y"] - y) < 130:
                if any(o.dist(pl["x"], pl["y"]) < 5 for o in mios):      # en esa plaza hay aparcado un vehículo tuyo
                    continue
                ids = [i for i in m.barrio(pl["x"], pl["y"])["vehiculos"] if i in self.modelos] or ["utilitario"]
                v = Vehiculo(self.modelos[ids[int(pl["azar"] * len(ids)) % len(ids)]], pl["x"], pl["y"], pl["dir"], "aparcado")
                v.cerrado = True
                v.con_alarma = pl["azar"] < 0.35
                v.plaza = pl["id"]
                self.plazas_activas[pl["id"]] = v
                self.vehiculos.append(v)
        # vehículos de servicio aparcados ante su edificio (ambulancia, patrulla, taxi, autobús...)
        for l in m.lugares.values():
            mod = l.get("vehiculo")
            clave = "L:" + l.id
            if not mod or mod not in self.modelos or clave in self.plazas_activas or clave in self.plazas_usadas:
                continue
            if abs(l.x - x) < 130 and abs(l.y - y) < 130:
                vx, vy, vd = m.plaza_junto_a(l)
                v = Vehiculo(self.modelos[mod], vx, vy, vd, "aparcado")
                v.cerrado = True
                v.con_alarma = mod == "patrulla"
                v.plaza = clave
                self.plazas_activas[clave] = v
                self.vehiculos.append(v)
        # peatones
        n = sum(1 for p in self.personas if p.tipo in ("civil", "banda") and not p.tag and not p.muerto)
        tope = max(1, round((max(1, m.peatones // 3) if noche else m.peatones) * self.azar_factor("peatones")))
        if self.lluvia:
            tope = max(1, tope // 2)
        if n < tope and not self.sv_peatones_comunes():
            bi, bj = m.bloque(x, y)
            bi = max(0, min(m.NX - 2, bi + random.choice([-1, 0, 0, 1])))
            bj = max(0, min(m.NY - 2, bj + random.choice([-1, 0, 0, 1])))
            p = Persona("civil", 0, 0)
            p.bloque = (bi, bj)
            p.u = random.uniform(0, 4 * (M.B - 15))
            p.sentido = random.choice([-1, 1])
            p.vel = random.uniform(1.1, 1.7)
            self._pos_perimetro(p)
            if 28 < p.dist(x, y) < 95:
                # Por los barrios de una banda con gente en la calle andan los suyos. Los del puerto, solo mientras dura su parte de la historia.
                # Con la guerra de barrios en la calle encendida, los de cualquier barrio con banda.
                mb = self.miembro_de_barrio(m.barrio(p.x, p.y))
                if mb and random.random() < mb[2]:
                    bd, calle = mb[0], mb[1]
                    f = gente.enemigo(gente.grupo(calle, tipo="Calavera", arma=random.choice(["pistola", "navaja", "punos"]), salud=60))
                    p.tipo = "banda"
                    p.nombre = f["nombre"] if bd["nombre"] in f["nombre"] or calle == bd.get("callejero") else f"{f['nombre']} de {bd['nombre']}"
                    gente.vestir(p, f)
                    p.banda = bd["nombre"]
                    p.hostil = True
                self.personas.append(p)
                if p.tipo == "civil":
                    self.pareja_de_paseo(p)                      # a veces la gente pasea de dos en dos

    def _pos_perimetro(self, p):
        lado = M.B - 15
        u = p.u % (4 * lado)
        bi, bj = p.bloque
        x0, y0 = bi * M.B + 7.5, bj * M.B + 7.5
        k = int(u // lado)
        r = u - k * lado
        if k == 0:
            p.x, p.y = x0 + r, y0
        elif k == 1:
            p.x, p.y = x0 + lado, y0 + r
        elif k == 2:
            p.x, p.y = x0 + lado - r, y0 + lado
        else:
            p.x, p.y = x0, y0 + lado - r

    def quitar_vehiculo(self, v):
        self.sv_quitado(v)
        v.callar()
        v.muerto = True
        if v.plaza is not None:
            self.plazas_activas.pop(v.plaza, None)
        if v in self.vehiculos:
            self.vehiculos.remove(v)
        if self.objetivo is v:
            self.objetivo = None

    def silenciar(self):
        """Detiene todos los sonidos del mundo (al salir de la partida)."""
        self.desconectar_online()
        from . import transporte
        transporte.callar(self)
        for v in self.vehiculos:
            v.callar()
        for o in self.objetos:
            if o.canal:
                o.canal.parar()
                o.canal = None
        for c in self.canales_lugar.values():
            c.parar()
        self.canales_lugar.clear()
        for c in (self.amb_canal, self.noche_canal, self.lluvia_canal, self.latido_canal, getattr(self, "rodadura", None)):
            if c:
                c.parar()
        self.amb_canal = self.noche_canal = self.lluvia_canal = self.latido_canal = None
        self.amb_nombre = None
        self.rodadura = None
        if self.forzando:
            self.forzando["canal"].parar()
            self.forzando = None
        self.app.radio.apagar()
        self.mez.parar_todo()
