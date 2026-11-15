"""Motor de misiones. Las misiones se definen en datos/misiones.json (y en mods)."""
import copy
import math
import random

import pygame

from . import mundo as M
from .entidades import Objeto, Persona
from .menus import Dialogo, Menu, Opcion


def paso_seguro(pasos, k):
    """¿Se puede poner un punto de control al empezar el paso k? No, si a esas alturas llevas un vehículo de la misión
    que todavía hay que entregar: al volver, ese vehículo ya no existiría."""
    pendiente = False
    for p in pasos[:k]:
        if p["tipo"] == "robar":
            pendiente = True
        elif p["tipo"] == "entregar":
            pendiente = False
    return not pendiente


class Misiones:
    def misiones_disponibles(self):
        hechas = set(self.completadas)
        return [m for m in self.datos["misiones"]
                if m["id"] not in hechas and (self.cfg["adultos"] or not m.get("adultos")) and all(r in hechas for r in m.get("requiere", []))
                and m.get("lugar") in self.lugares]

    def mision_en_lugar(self, lugar_id):
        for m in self.misiones_disponibles():
            if m["lugar"] == lugar_id:
                return m
        return None

    def objetivo_txt(self):
        if self.mision:
            p = self.mision["def"]["pasos"][self.mision["paso"]]
            t = f"Misión {self.mision['def']['titulo']}. {p.get('texto', '')}"
            if self.mision.get("limite") is not None:
                t += f" Te quedan {int(self.mision['limite'])} segundos."
            x, y = self.pos()
            o = self.mision.get("movil")
            if p["tipo"] == "seguir" and o:
                t += f" {o['nombre'].capitalize()} va a {int(math.hypot(o['x'] - x, o['y'] - y))} metros, {self.direccion_txt(o['x'], o['y'])}. Síguele por el sonido de sus pasos, sin acercarte a menos de seis metros."
            e = self.mision.get("escolta")
            if p["tipo"] == "escoltar" and e:
                t += f" {e['nombre'].capitalize()} " + (f"está a {int(math.hypot(e['x'] - x, e['y'] - y))} metros de ti." if e["contigo"] else "te espera en el punto de recogida.")
            if p["tipo"] == "sigilo" and self.mision.get("guardias"):
                cerca = min(math.hypot(g["x"] - x, g["y"] - y) for g in self.mision["guardias"])
                t += f" Hay {len(self.mision['guardias'])} vigilantes; el más cercano, a {int(cerca)} metros. Agachado, con la X, te oyen mucho menos. No corras."
            vg = self.mision.get("vigia")
            if p["tipo"] == "vigilar" and vg:
                t += (f" Estás en tu puesto. Te quedan {max(0, int(float(p.get('segundos', 45)) - vg['t']))} segundos. Si oyes pasos que se acercan, quédate quieto o agáchate con la X."
                      if vg["dentro"] else " Todavía no has llegado al puesto.")
            ca = self.mision.get("carrera")
            if p["tipo"] == "carrera" and ca:
                if ca["fase"] == "corre":
                    t += f" Vas por el punto {self.mision.get('ruta_i', 0) + 1} de {len(p.get('puntos', []))}. {self._carrera_puesto_txt(ca)}"
                else:
                    t += " Ve a la salida con un vehículo y detente allí."
            if p["tipo"] == "ruta":
                t += f" Vas por el punto {self.mision.get('ruta_i', 0) + 1} de {len(p.get('puntos', []))}."
            if p["tipo"] == "eliminar" and self.mision.get("generado"):
                t += f" Quedan {sum(1 for e in self.mision['enemigos'] if not e.muerto)} enemigos."
            return t
        if self.trabajo:
            return self.trabajo.get("texto", "Estás trabajando.")
        disp = self.misiones_disponibles()
        if disp:
            m = disp[0]
            l = self.lugares[m["lugar"]]
            return f"No tienes ninguna misión en curso. Disponible: {m['titulo']}, en {self.nombre_lugar(l)}. Abre el móvil con M para marcarla en el GPS."
        return "Has completado todas las misiones de la historia. La ciudad es tuya."

    # ----------------------------------------------------------------- inicio
    def iniciar_mision(self, m, reintento=False, repeticion=False):
        if self.trabajo:
            self.terminar_trabajo("Dejas el trabajo para empezar la misión.")
        self.cancelar_gps()
        self.mision = {"def": m, "paso": -1, "veh": None, "enemigos": [], "objeto": None, "limite": None,
                       "copia": copy.deepcopy(self.j.a_dict()), "reloj": self.reloj, "dia": self.dia,
                       "generado": False, "recogido": False, "restos": None, "avisos": set(), "quedan": None, "repeticion": bool(repeticion)}
        self.app.son("notificacion")
        self.decir(f"Misión: {m['titulo']}." + (" La repites: no cuenta ni da recompensa." if repeticion else ""), True)
        self._siguiente_paso()

    def _lugar_paso(self, p):
        return self.lugares.get(p.get("lugar", ""))

    def nombre_lugar(self, l):
        """Nombre del lugar, añadiendo la localidad si está en otro mapa."""
        if l.mapa != self.mundo.id:
            return f"{l.nombre}, en {self.mapas[l.mapa].nombre}"
        return l.nombre

    def mision_cambio_mapa(self):
        ms = self.mision
        if not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        if tipo == "perseguir" and ms.get("veh_objetivo") is not None:
            self.fallar_mision("Has dejado escapar al objetivo.")
            return
        if tipo == "carrera" and (ms.get("carrera") or {}).get("fase") in ("cuenta", "corre"):
            self.fallar_mision("Has abandonado la carrera.")
            return
        v = ms.get("veh")
        if v is not None and v is not self.j.veh:
            if tipo == "entregar":
                self.fallar_mision("Has dejado atrás el vehículo de la misión.")
                return
            ms["veh"] = None
        ms["enemigos"] = []
        ms["generado"] = False
        if not ms["recogido"]:
            ms["objeto"] = None
        if tipo in ("dialogo", "dar", "policia"):
            return
        ms["pendiente"] = True
        self._materializar()

    def voces_activas(self):
        """Las voces grabadas solo suenan si el jugador las quiere y juega con Dani: las grabaciones le llaman por ese nombre."""
        return bool(self.cfg["voces_grabadas"]) and self.j.personaje == "dani"

    def _siguiente_paso(self):
        ms = self.mision
        if not ms:
            return
        ms["paso"] += 1
        pasos = ms["def"]["pasos"]
        if ms["paso"] >= len(pasos):
            self._completar_mision()
            return
        p = pasos[ms["paso"]]
        ms["limite"] = p.get("limite")
        ms["avisos"] = set()
        ms["generado"] = False
        ms["recogido"] = False
        tipo = p["tipo"]
        l = self._lugar_paso(p)
        if (tipo not in ("dialogo", "dar") and not ms.get("reanudando") and paso_seguro(pasos, ms["paso"])
                and any(q["tipo"] not in ("dialogo", "dar") for q in pasos[:ms["paso"]])):          # con algo ya hecho: si no, es el principio
            # Punto de control: si fallas más adelante, puedes volver aquí en lugar de al principio.
            x, y = self.pos()
            ms["control"] = {"paso": ms["paso"], "copia": copy.deepcopy(self.j.a_dict()), "reloj": self.reloj, "dia": self.dia,
                             "mapa": self.mundo.id, "x": x, "y": y}
        ms["reanudando"] = False
        if tipo == "dialogo":
            from . import voces
            self.app.abrir(Dialogo(self.app, [(self.txt(q), self.txt(tx)) for q, tx in p["lineas"]], self._siguiente_paso,
                                   voces=voces.de_paso(ms["def"]["id"], ms["paso"], len(p["lineas"])) if self.voces_activas() else None))
            return
        if tipo == "dar":
            if "arma" in p:
                self.dar_arma(p["arma"], p.get("balas", 0))
            if "balas_arma" in p and p["balas_arma"] in self.j.armas:
                self.j.armas[p["balas_arma"]]["reserva"] += p.get("balas", 0)
                self.decir(f"Recibes {p.get('balas', 0)} balas.")
            if "dinero" in p:
                self.dar_dinero(p["dinero"], "Recibes")
            if "sustancia" in p and self.sustancia(p["sustancia"]):
                self.j.sustancias[p["sustancia"]] = self.j.sustancias.get(p["sustancia"], 0) + int(p.get("cantidad", 1))
                self.decir(f"Recibes {p.get('cantidad', 1)} de {self.sustancia(p['sustancia'])['nombre'].lower()}.")
            self._siguiente_paso()
            return
        if p.get("texto"):
            self.decir(self.txt(p["texto"]))
        ms["pendiente"] = True
        self._materializar()

    def _materializar(self):
        """Crea lo que necesita el paso actual (vehículos, enemigos, objetos) y orienta el GPS."""
        ms = self.mision
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        l = self._lugar_paso(p)
        if tipo == "policia":
            ms["pendiente"] = False
            self.poner_busqueda(p.get("nivel", 2))
            self.cancelar_gps()
            return
        if tipo == "entregar" and ms.get("veh") is not None and self.j.veh is not ms["veh"] and not ms["veh"].muerto:
            ms["pendiente"] = False
            return
        if l and l.mapa != self.mundo.id and not p.get("aqui"):
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        ms["pendiente"] = False
        if tipo == "seguir" and l:
            d = self.lugares.get(p.get("destino", ""))
            ruta = self.mundo.ruta(l.x, l.y, d.x, d.y) if d is not None and d.mapa == l.mapa else [(l.x, l.y)]
            ms["movil"] = {"x": l.x, "y": l.y, "ruta": list(ruta), "i": 0, "t_paso": 0.0, "cerca": 0.0, "lejos": 0.0, "t_aviso": 0.0,
                           "vel": float(p.get("velocidad", 2.3)), "nombre": self.txt(p.get("persona") or "tu objetivo"), "espera": 6.0}
            self.cancelar_gps()
            return
        if tipo == "escoltar" and l:
            ms["escolta"] = {"x": l.x, "y": l.y, "t_paso": 0.0, "t_aviso": 0.0, "nombre": self.txt(p.get("persona") or "tu acompañante"), "contigo": False}
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo == "sigilo" and l:
            n = max(1, int(p.get("guardias", 3)))
            guardias = []
            for k in range(n):
                a = 2 * math.pi * k / n + 0.6
                r = 9.0 + 3.0 * (k % 2)
                gx, gy = l.x + math.sin(a) * r, l.y + math.cos(a) * r
                if not self.mundo.transitable(gx, gy):
                    gx, gy = self.mundo.punto_libre(gx, gy)
                guardias.append({"x": gx, "y": gy, "x0": gx, "y0": gy, "a": a + math.pi / 2, "fase": k * 1.7, "t_paso": 0.3 * k})
            ms["guardias"] = guardias
            ms["t_aviso"] = 0.0
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo == "ruta":
            ms["ruta_i"] = 0
            self._ruta_siguiente(p, primero=True)
            return
        if tipo == "vigilar" and l:
            ms["vigia"] = {"t": 0.0, "dentro": False, "fuera": 0.0, "t_aviso": 0.0, "ronda": None, "t_ronda": 9.0, "rondas": 0,
                           "t_suceso": 5.0, "sucesos": 0, "visto": 0.0}
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo == "carrera" and l:
            self._parar_rivales(ms)
            ms["carrera"] = {"fase": "ir", "t": 0.0, "rivales": [], "puesto": 0}
            ms["ruta_i"] = 0
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo in ("ir", "entregar") and l:
            self.gps_a_lugar(l, auto=True)
        elif tipo == "robar" and l:
            if ms.get("veh") is not None and not ms["veh"].muerto:
                return
            x, y, d = self.mundo.plaza_junto_a(l)
            self._despejar_plaza(x, y)
            v = self.crear_vehiculo(p["modelo"], x, y, d, "aparcado", p.get("nombre"), "mision")
            v.cerrado = not p.get("abierto", False)
            v.con_alarma = bool(p.get("busqueda"))
            v.sirena = self.son("loc_vehiculo", bucle=True, xy=(x, y), ref=5, maxd=70)
            ms["veh"] = v
            self.fijar_gps(x, y, v.nombre, auto=True, radio=4)
        elif tipo == "eliminar" and l:
            self.gps_a_lugar(l, auto=True)
            if p.get("ya"):
                self._generar_enemigos(p, l)
        elif tipo == "recoger":
            if ms["recogido"]:
                return
            if p.get("aqui") or not l:
                x, y = ms["restos"] or self.pos()
                x, y = self.mundo.punto_libre(x, y)
            else:
                x, y = l.x, l.y
            o = Objeto("mision", p["objeto"], x, y, "loc_objeto")
            self.objetos.append(o)
            ms["objeto"] = o
            self.fijar_gps(x, y, p["objeto"], auto=True, radio=2)
        elif tipo == "perseguir" and l:
            x, y, d = self.mundo.plaza_junto_a(l)
            x, y = (x, self.mundo.carril("H", self.mundo._idx(y, self.mundo.NY), d)) if d in (1, 3) else (self.mundo.carril("V", self.mundo._idx(x, self.mundo.NX), d), y)
            v = self.crear_vehiculo(p["modelo"], x, y, d, "huida", p.get("nombre"), "objetivo")
            v.salud = v.salud_max = float(p.get("salud", 120))
            v.ocupado = True
            v.hostil = True
            v.vel_obj = min(v.modelo["vel_max"] * 0.62, 21.0)
            ms["veh_objetivo"] = v
            self.objetivo = v
            self.fijar_gps(x, y, v.nombre, sigue=v, auto=True)

    def _despejar_plaza(self, x, y):
        """Quita los vehículos aparcados que estorban donde va a aparecer uno de misión."""
        for o in list(self.vehiculos):
            if o.ia == "aparcado" and not o.tag and o is not self.j.veh and o.dist(x, y) < 9:
                if o.plaza is not None:
                    self.plazas_usadas.add(o.plaza)
                self.quitar_vehiculo(o)
        for l in self.mundo.lugares.values():
            if l.get("vehiculo"):
                px, py, _ = self.mundo.plaza_junto_a(l)
                if math.hypot(px - x, py - y) < 9:
                    self.plazas_usadas.add("L:" + l.id)

    def _generar_enemigos(self, p, l):
        ms = self.mision
        ms["generado"] = True
        for grupo in p["enemigos"]:
            for _ in range(grupo.get("n", 1)):
                for _ in range(20):
                    a = random.uniform(0, 2 * math.pi)
                    r = random.uniform(5, 16)
                    x, y = l.x + math.sin(a) * r, l.y + math.cos(a) * r
                    if self.mundo.transitable(x, y):
                        break
                else:
                    x, y = l.x, l.y
                e = Persona("enemigo", x, y, grupo.get("tipo", "Enemigo"))
                e.salud = float(grupo.get("salud", 60))
                e.arma = grupo.get("arma", "pistola")
                e.hostil = True
                e.estado = "ataca"
                e.inofensivo = bool(grupo.get("inofensivo"))          # un muñeco de prácticas: se le puede fijar, pero no ataca
                e.tag = "mision"
                e.t_disparo = random.uniform(1.5, 3.0)
                self.personas.append(e)
                ms["enemigos"].append(e)
        ms["quedan"] = len(ms["enemigos"])
        self.decir(f"Hay {ms['quedan']} enemigos. Pulsa Q para fijar al más cercano.")
        if self.cfg["punteria"] == "completa":
            self.fijar(callar=True)

    # ------------------------------------------------------------ actualización
    def actualizar_mision(self, dt):
        ms = self.mision
        if not ms or ms["paso"] < 0 or ms["paso"] >= len(ms["def"]["pasos"]):
            return
        j = self.j
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        if tipo in ("dialogo", "dar"):
            return
        x, y = self.pos()
        if ms["limite"] is not None:
            antes = ms["limite"]
            ms["limite"] -= dt
            for marca in (120, 60, 30, 10):
                if antes > marca >= ms["limite"]:
                    self.decir(f"Quedan {marca} segundos.")
            if ms["limite"] < 10 and int(antes) != int(ms["limite"]):
                self.son("reloj", cat="interfaz")
            if ms["limite"] <= 0:
                self.fallar_mision("Se ha acabado el tiempo.")
                return
        v = ms.get("veh")
        if v is not None and tipo in ("robar", "entregar"):
            if v.muerto or v.ardiendo >= 0:
                self.fallar_mision("El vehículo ha quedado destruido.")
                return
            if tipo == "entregar" and 100.0 * v.salud / v.salud_max < p.get("salud_min", 0):
                self.fallar_mision("El vehículo ha sufrido demasiados daños.")
                return
        l = self._lugar_paso(p)
        if ms.get("pendiente"):
            if tipo != "policia" and (l is None or l.mapa == self.mundo.id):
                self._materializar()
            if ms.get("pendiente"):
                if tipo == "robar" and j.veh is not None and j.veh is ms.get("veh"):
                    self._paso_hecho()
                return
        if tipo == "seguir":
            self._paso_seguir(ms, p, x, y, dt)
        elif tipo == "escoltar":
            self._paso_escoltar(ms, p, x, y, dt)
        elif tipo == "sigilo":
            self._paso_sigilo(ms, p, l, x, y, dt)
        elif tipo == "vigilar":
            self._paso_vigilar(ms, p, l, x, y, dt)
        elif tipo == "carrera":
            self._paso_carrera(ms, p, l, x, y, dt)
        elif tipo == "ruta":
            punto = self.lugares.get(p.get("puntos", [""])[min(ms.get("ruta_i", 0), len(p.get("puntos", [""])) - 1)])
            if punto and punto.mapa == self.mundo.id and math.hypot(punto.x - x, punto.y - y) <= (20 if j.veh else 10):
                ms["ruta_i"] += 1
                if ms["ruta_i"] >= len(p["puntos"]):
                    self._paso_hecho()
                else:
                    self.app.son("llegada")
                    self._ruta_siguiente(p)
        elif tipo == "ir":
            radio = 28 if self.mundo.tipo == "mar" else 17 if j.veh else p.get("radio", 8)
            if l and math.hypot(l.x - x, l.y - y) <= radio and (not j.veh or abs(j.veh.vel) < 3):
                self._paso_hecho()
        elif tipo == "robar":
            if j.veh is v:
                if p.get("busqueda"):
                    self.poner_busqueda(p["busqueda"])
                self._paso_hecho()
        elif tipo == "entregar":
            if j.veh is v:
                cerca = 32 if v.modelo.get("vuela") else 18
                if l and l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) <= cerca and abs(v.vel) < 2.5:
                    self.salir_vehiculo(forzado=True)
                    self.j.x, self.j.y = l.x, l.y
                    self.quitar_vehiculo(v)
                    ms["veh"] = None
                    self.son("puerta_coche")
                    self._paso_hecho()
                elif l and l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) <= cerca and "frena" not in ms["avisos"]:
                    ms["avisos"].add("frena")
                    self.decir("Has llegado. Detén el vehículo.")
            elif "fuera" not in ms["avisos"] and v is not None and v.dist(x, y) > 30:
                ms["avisos"].add("fuera")
                self.fijar_gps(v.x, v.y, v.nombre, auto=True, radio=4, callar=True)
                self.decir(f"Has dejado atrás {v.nombre}. Vuelve a por él.")
            elif j.veh is None and v is not None and "fuera" in ms["avisos"] and v.dist(x, y) < 6:
                ms["avisos"].discard("fuera")
        elif tipo == "eliminar":
            if not ms["generado"]:
                if l and math.hypot(l.x - x, l.y - y) < 45:
                    self._generar_enemigos(p, l)
            else:
                vivos = sum(1 for e in ms["enemigos"] if not e.muerto)
                if vivos != ms["quedan"]:
                    ms["quedan"] = vivos
                    if vivos > 0:
                        self.decir(f"Quedan {vivos}.")
                if vivos == 0:
                    ms["enemigos"] = []
                    self._paso_hecho()
        elif tipo == "recoger":
            if ms["recogido"]:
                self._paso_hecho()
        elif tipo == "policia":
            if j.estrellas == 0 and j.puntos_busqueda < 1:
                self._paso_hecho()
        elif tipo == "perseguir":
            vo = ms.get("veh_objetivo")
            if vo is None or vo.muerto:
                if ms["restos"] is None and vo is not None:
                    ms["restos"] = (vo.x, vo.y)
                self.decir(f"¡{p.get('nombre', 'El objetivo')} destruido!")
                ms["veh_objetivo"] = None
                self._paso_hecho()
            elif j.veh and self.gps is None:
                self.fijar_gps(vo.x, vo.y, vo.nombre, sigue=vo, auto=True, callar=True)

    # ------------------------------------------------- pasos de oído: seguir, escoltar, sigilo y ruta
    def _ruta_siguiente(self, p, primero=False):
        ms = self.mision
        puntos = p.get("puntos", [])
        l = self.lugares.get(puntos[ms["ruta_i"]]) if ms["ruta_i"] < len(puntos) else None
        if l is None:
            return
        self.gps_a_lugar(l, auto=True, callar=True)
        self.decir(f"Punto {ms['ruta_i'] + 1} de {len(puntos)}: {self.nombre_lugar(l)}." if not primero else
                   f"Son {len(puntos)} puntos. El primero: {self.nombre_lugar(l)}.")

    def _paso_seguir(self, ms, p, x, y, dt):
        """Seguir a alguien de oído: ni tan cerca que te vea, ni tan lejos que lo pierdas."""
        o = ms.get("movil")
        if o is None:
            return
        j = self.j
        d = math.hypot(o["x"] - x, o["y"] - y)
        if o["espera"] > 0:                                   # al principio se queda quieto un momento: te da tiempo a localizarlo
            o["espera"] -= dt
        elif o["i"] < len(o["ruta"]):
            tx, ty = o["ruta"][o["i"]]
            r = math.hypot(tx - o["x"], ty - o["y"])
            paso = o["vel"] * dt
            if r <= paso:
                o["x"], o["y"] = tx, ty
                o["i"] += 1
            else:
                o["x"] += (tx - o["x"]) / r * paso
                o["y"] += (ty - o["y"]) / r * paso
        o["t_paso"] -= dt
        if o["t_paso"] <= 0:
            o["t_paso"] = 0.55
            self.son("paso_npc", xy=(o["x"], o["y"]), ref=5, maxd=75, vol=1.0)
        limite_cerca = 12.0 if j.veh else 3.5 if j.agachado else 6.0
        o["cerca"] = o["cerca"] + dt if d < limite_cerca else 0.0
        o["lejos"] = o["lejos"] + dt if d > 55 else 0.0
        o["t_aviso"] -= dt
        if o["t_aviso"] <= 0 and (d < limite_cerca + 4 or d > 40):
            o["t_aviso"] = 5.0
            self.decir("Estás demasiado cerca. Quédate atrás." if d < limite_cerca + 4 else f"Se te aleja: va a {int(d)} metros, {self.direccion_txt(o['x'], o['y'])}.")
        if o["cerca"] > 1.5:
            self.fallar_mision(f"{o['nombre'].capitalize()} se ha dado cuenta de que le seguías.")
        elif o["lejos"] > 9:
            self.fallar_mision(f"Has perdido de vista a {o['nombre']}.")
        elif o["i"] >= len(o["ruta"]) and d < 55:
            self._paso_hecho()

    def _paso_escoltar(self, ms, p, x, y, dt):
        """Llevar a alguien hasta un sitio: te sigue a pie y sube contigo si coges un vehículo."""
        e = ms.get("escolta")
        if e is None:
            return
        j = self.j
        d = math.hypot(e["x"] - x, e["y"] - y)
        dest = self.lugares.get(p.get("destino", ""))
        if not e["contigo"]:
            if d < 6:
                e["contigo"] = True
                self.app.son("llegada")
                self.decir(f"{e['nombre'].capitalize()} va contigo. Te sigue a pie y sube al vehículo que cojas." +
                           (f" Llévale a {self.nombre_lugar(dest)}." if dest else ""))
                if dest:
                    self.gps_a_lugar(dest, auto=True, callar=True)
            return
        if j.veh:
            e["x"], e["y"] = x, y                             # va de pasajero
        elif d > 3.0:
            paso = min(d - 2.5, (6.5 if d > 12 else 4.0) * dt)
            e["x"] += (x - e["x"]) / d * paso
            e["y"] += (y - e["y"]) / d * paso
            e["t_paso"] -= dt
            if e["t_paso"] <= 0:
                e["t_paso"] = 0.45
                self.son("paso_npc", xy=(e["x"], e["y"]), ref=4, maxd=40, vol=0.8)
        if dest and dest.mapa == self.mundo.id and math.hypot(dest.x - x, dest.y - y) <= (17 if j.veh else p.get("radio", 9)) \
                and (not j.veh or abs(j.veh.vel) < 3) and math.hypot(e["x"] - x, e["y"] - y) < 15:
            self._paso_hecho()

    def _paso_sigilo(self, ms, p, l, x, y, dt):
        """Llegar a un punto vigilado sin que te oigan: agachado se te oye menos; corriendo, mucho más."""
        j = self.j
        t = self.app.teclas
        corriendo = self.corriendo_ahora()
        oido = 22.0 if j.veh else 2.6 if j.agachado else 11.0 if corriendo else 6.0
        cerca = 999.0
        for g in ms.get("guardias", []):
            g["fase"] += dt * 0.35                             # cada guardia pasea de un lado a otro de su puesto
            k = math.sin(g["fase"]) * 5.0
            nx, ny = g["x0"] + math.sin(g["a"]) * k, g["y0"] + math.cos(g["a"]) * k
            if self.mundo.transitable(nx, ny):
                g["x"], g["y"] = nx, ny
            g["t_paso"] -= dt
            if g["t_paso"] <= 0:
                g["t_paso"] = 0.8
                self.son("paso_npc", xy=(g["x"], g["y"]), ref=3, maxd=35, vol=1.0)
            cerca = min(cerca, math.hypot(g["x"] - x, g["y"] - y))
        ms["t_aviso"] = ms.get("t_aviso", 0.0) - dt
        if cerca <= oido:
            self.son("grito", xy=(x, y), vol=0.6)
            self.fallar_mision("Un vigilante te ha oído.")
            return
        if cerca < oido + 4 and ms["t_aviso"] <= 0:
            ms["t_aviso"] = 4.0
            self.son("buscando", cat="interfaz", vol=0.6)
            self.decir(f"Tienes un vigilante a {int(cerca)} metros. " + ("Agáchate con la X." if not j.agachado else "No te muevas hacia él."))
        if l and math.hypot(l.x - x, l.y - y) <= 2.5 and not j.veh:
            if p.get("objeto"):
                self.son("recoger", cat="interfaz")
                self.decir(f"Tienes {self.txt(p['objeto'])}.")
            self._paso_hecho()

    def _paso_vigilar(self, ms, p, l, x, y, dt):
        """Vigilar un sitio sin que te vean: quedarte cerca un rato y no moverte cuando pasa la ronda."""
        vg = ms.get("vigia")
        if vg is None or l is None:
            return
        j = self.j
        radio = float(p.get("radio", 25))
        d = math.hypot(l.x - x, l.y - y)
        if not vg["dentro"]:
            if d <= radio and (not j.veh or abs(j.veh.vel) < 2):
                vg["dentro"] = True
                if self.gps and self.gps.get("auto"):
                    self.cancelar_gps()
                self.app.son("llegada")
                self.decir(f"Estás en tu puesto. Quédate a menos de {int(radio)} metros durante {int(float(p.get('segundos', 45)))} segundos y escucha. "
                           "Cuando oigas pasos que se acercan, quédate quieto o agáchate con la X.")
            return
        vg["t"] += dt
        if d > radio:
            vg["fuera"] += dt
            vg["t_aviso"] -= dt
            if vg["t_aviso"] <= 0:
                vg["t_aviso"] = 3.0
                self.decir(f"Te alejas del puesto. Vuelve: está a {int(d)} metros, {self.direccion_txt(l.x, l.y)}.")
            if vg["fuera"] > 7:
                self.fallar_mision("Has dejado el puesto de vigilancia.")
                return
        else:
            vg["fuera"] = 0.0
        vg["t_suceso"] -= dt
        if vg["t_suceso"] <= 0:                                   # lo que pasa en el sitio vigilado se oye desde él
            vg["t_suceso"] = 6.5
            vg["sucesos"] += 1
            self.son(("puerta_entrar", "puerta_coche", "paso_npc")[vg["sucesos"] % 3], xy=(l.x, l.y), ref=6, maxd=80, vol=1.0)
        r = vg["ronda"]
        if r is None:
            vg["t_ronda"] -= dt
            if vg["t_ronda"] <= 0:
                vg["rondas"] += 1
                vg["ronda"] = {"t": 0.0, "x": l.x, "y": l.y, "t_paso": 0.0}
                self.son("buscando", cat="interfaz", vol=0.5)
                if vg["rondas"] == 1:
                    self.decir("Sale alguien a dar una vuelta. Quédate quieto o agáchate hasta que se vaya.")
        else:
            r["t"] += dt
            f = min(1.0, r["t"] / 4.0) if r["t"] < 7.0 else max(0.0, 1.0 - (r["t"] - 7.0) / 3.0)     # se acerca, se para y se va
            dx, dy = x - l.x, y - l.y
            k = f * max(0.0, 1.0 - 5.0 / max(5.0, math.hypot(dx, dy)))                              # se queda a cinco metros de ti
            r["x"], r["y"] = l.x + dx * k, l.y + dy * k
            r["t_paso"] -= dt
            if r["t_paso"] <= 0:
                r["t_paso"] = 0.6
                self.son("paso_npc", xy=(r["x"], r["y"]), ref=3, maxd=45, vol=1.0)
            cerca = math.hypot(r["x"] - x, r["y"] - y) < 12
            t = self.app.teclas
            moviendote = (abs(j.veh.vel) > 1.0) if j.veh else (not j.agachado and any(k2 in t for k2 in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)))
            vg["visto"] = vg["visto"] + dt if cerca and moviendote else 0.0
            if vg["visto"] > 0.6:
                self.son("grito", xy=(r["x"], r["y"]), vol=0.6)
                self.fallar_mision("Te han visto moverte.")
                return
            if r["t"] >= 10.0:
                vg["ronda"] = None
                vg["t_ronda"] = 11.0
        if vg["t"] >= float(p.get("segundos", 45)):
            if p.get("resultado"):
                self.decir(self.txt(p["resultado"]))
            self._paso_hecho()

    NOMBRES_RIVALES = ("el coche rojo", "el coche negro", "la furgoneta blanca", "el deportivo amarillo")

    def _parar_rivales(self, ms):
        for r in (ms.get("carrera") or {}).get("rivales", []):
            if r.get("canal") is not None:
                r["canal"].parar()
                r["canal"] = None

    def _carrera_puesto_txt(self, ca):
        orden = ("primero", "segundo", "tercero", "cuarto", "quinto")
        return f"Vas {orden[max(0, min(ca['puesto'], 4))]} de {len(ca['rivales']) + 1}."

    def _carrera_punto_en(self, ca, s):
        """El punto del recorrido que está a s metros de la salida."""
        pts, cum = ca["pts"], ca["cum"]
        s = max(0.0, min(s, cum[-1]))
        for n in range(1, len(pts)):
            if s <= cum[n] or n == len(pts) - 1:
                tramo = cum[n] - cum[n - 1]
                f = (s - cum[n - 1]) / tramo if tramo > 0 else 0.0
                return pts[n - 1][0] + (pts[n][0] - pts[n - 1][0]) * f, pts[n - 1][1] + (pts[n][1] - pts[n - 1][1]) * f
        return pts[-1]

    def _paso_carrera(self, ms, p, l, x, y, dt):
        """Carrera con rivales: llegar al último punto antes que ellos. Se les oye el motor desde donde van."""
        ca = ms.get("carrera")
        if ca is None or l is None:
            return
        j = self.j
        puntos = [self.lugares.get(q) for q in p.get("puntos", [])]
        puntos = [q for q in puntos if q is not None]
        if not puntos:
            self._paso_hecho()
            return
        if ca["fase"] == "ir":
            if math.hypot(l.x - x, l.y - y) <= 17:
                if not j.veh:
                    if "sin_coche" not in ms["avisos"]:
                        ms["avisos"].add("sin_coche")
                        self.decir("Estás en la salida, pero para correr necesitas un vehículo. Consigue uno y vuelve.")
                elif abs(j.veh.vel) < 3:
                    pts = [(l.x, l.y)]
                    marcas = []                                    # a cuántos metros de la salida queda cada punto de control
                    largo = 0.0
                    for q in puntos:
                        for pt in self.mundo.ruta(pts[-1][0], pts[-1][1], q.x, q.y):
                            largo += math.hypot(pt[0] - pts[-1][0], pt[1] - pts[-1][1])
                            pts.append((float(pt[0]), float(pt[1])))
                        marcas.append(largo)
                    rectos, antes = [], (l.x, l.y)                 # la distancia en línea recta de cada tramo, para saber cuánto llevas
                    for q in puntos:
                        rectos.append(max(1.0, math.hypot(q.x - antes[0], q.y - antes[1])))
                        antes = (q.x, q.y)
                    cum = [0.0]
                    for n in range(1, len(pts)):
                        cum.append(cum[-1] + math.hypot(pts[n][0] - pts[n - 1][0], pts[n][1] - pts[n - 1][1]))
                    n_riv = max(1, min(4, int(p.get("rivales", 2))))
                    base = float(p.get("velocidad", 10))
                    ca.update({"fase": "cuenta", "t": 3.0, "pts": pts, "cum": cum, "marcas": marcas, "rectos": rectos, "puesto": -1,
                               "rivales": [{"s": 5.0 + 5.0 * k, "vel": base * (1.0 - 0.07 * k), "nombre": self.NOMBRES_RIVALES[k], "canal": None, "k": k} for k in range(n_riv)]})
                    if self.gps and self.gps.get("auto"):
                        self.cancelar_gps()
                    self.app.son("reloj", cat="interfaz")
                    self.decir(f"En la salida, con {n_riv} {'rival' if n_riv == 1 else 'rivales'}. Son {len(puntos)} puntos. Preparado.")
            return
        if ca["fase"] == "cuenta":
            antes = ca["t"]
            ca["t"] -= dt
            if int(antes) != int(ca["t"]) and ca["t"] > 0:
                self.app.son("reloj", cat="interfaz")
            if ca["t"] <= 0:
                ca["fase"] = "corre"
                ca["t"] = 0.0
                self.son("claxon", vol=0.6)
                for r in ca["rivales"]:
                    rx, ry = self._carrera_punto_en(ca, r["s"])
                    r["canal"] = self.son("motor_coche", bucle=True, xy=(rx, ry), ref=8, maxd=110, vol=0.8, tono=1.0 + 0.08 * r["k"])
                self.decir("¡Ya!", True)
                self._ruta_siguiente(p, primero=True)
            return
        # en carrera
        ca["t"] += dt
        i = min(ms.get("ruta_i", 0), len(puntos) - 1)
        punto = puntos[i]
        d = math.hypot(punto.x - x, punto.y - y)
        if punto.mapa == self.mundo.id and d <= 20:
            ms["ruta_i"] = i + 1
            if ms["ruta_i"] >= len(puntos):
                self._parar_rivales(ms)
                self.decir("¡Has ganado la carrera!")
                self._paso_hecho()
                return
            self.app.son("llegada")
            self._ruta_siguiente(p)
            i, punto = ms["ruta_i"], puntos[ms["ruta_i"]]
            d = math.hypot(punto.x - x, punto.y - y)
        previo = ca["marcas"][i - 1] if i else 0.0                               # cuánto llevas recorrido, más o menos
        mio = previo + (ca["marcas"][i] - previo) * max(0.0, 1.0 - d / ca["rectos"][i])
        delante = 0
        for r in ca["rivales"]:
            r["s"] += r["vel"] * (1.0 + 0.1 * math.sin(ca["t"] * 0.35 + 2.0 * r["k"])) * dt
            rx, ry = self._carrera_punto_en(ca, r["s"])
            if r["canal"] is not None:
                r["canal"].mover(rx, ry)
            if r["s"] >= ca["cum"][-1]:
                self._parar_rivales(ms)
                self.fallar_mision(f"Ha ganado {r['nombre']}.")
                return
            if r["s"] > mio:
                delante += 1
        if delante != ca["puesto"]:
            ca["puesto"] = delante
            self.decir(self._carrera_puesto_txt(ca))

    def _paso_hecho(self):
        if self.gps and self.gps.get("auto"):
            self.cancelar_gps()
        self.app.son("llegada")
        self._siguiente_paso()

    # ------------------------------------------------------------------- final
    def _limpiar_mision(self):
        ms = self.mision
        if not ms:
            return
        v = ms.get("veh")
        if v is not None and not v.muerto:
            if self.j.veh is v:
                self.salir_vehiculo(forzado=True)
            self.quitar_vehiculo(v)
        vo = ms.get("veh_objetivo")
        if vo is not None and not vo.muerto:
            self.quitar_vehiculo(vo)
        self._parar_rivales(ms)
        for e in ms["enemigos"]:
            if e in self.personas:
                self.personas.remove(e)
        o = ms.get("objeto")
        if o is not None and o in self.objetos:
            if o.canal:
                o.canal.parar()
            self.objetos.remove(o)
        if self.gps and self.gps.get("auto"):
            self.cancelar_gps()
        self.objetivo = None
        self.mision = None

    def _completar_mision(self):
        ms = self.mision
        m = ms["def"]
        antes = {x["id"] for x in self.misiones_disponibles()}
        self.mision = None
        if self.gps and self.gps.get("auto"):
            self.cancelar_gps()
        if ms.get("repeticion"):                               # repetir una misión ya hecha es por gusto: no cambia nada
            self.app.son("mision_ok")
            self.decir(f"Has repetido {m['titulo']}.")
            return
        self.fallos.pop(m["id"], None)
        if m.get("territorio") and m["territorio"] not in self.j.territorios:
            self.j.territorios.append(m["territorio"])
            self.son("territorio", cat="interfaz")
            self.decir("El barrio es tuyo. Te pagará 300 euros cada medianoche.")
            # quedarse con un barrio se sabe en toda la ciudad: el primero da mucha fama; los siguientes, cada vez menos
            self.cambiar_reputacion(max(3, 15 - 3 * (len(self.j.territorios) - 1)))
        if callable(m.get("al_completar")):
            m["al_completar"]()
        if m.get("repetible"):
            if m.get("contador"):
                self.j.stats[m["contador"]] = self.j.stats.get(m["contador"], 0) + 1
        else:
            self.completadas.append(m["id"])
            self.j.stats["misiones"] += 1
        r = m.get("recompensa", {})
        self.app.son("mision_ok")
        txt = f"{'Encargo cumplido' if m.get('repetible') else 'Misión completada'}: {m['titulo']}."
        if r.get("dinero"):
            self.j.dinero += r["dinero"]
            self.j.stats["dinero_ganado"] += r["dinero"]
            txt += f" Recompensa: {r['dinero']} euros."
        self.decir(txt)
        if r.get("arma"):
            self.dar_arma(r["arma"], r.get("balas", 0))
        self.cambiar_animo(4 if m.get("repetible") else 8)
        self.cambiar_reputacion(1 if m.get("repetible") else 2)
        for pid, n in (r.get("afinidad") or {}).items():
            if self.persona_social(pid):
                self.sumar_afinidad(pid, n)
        if r.get("chaleco"):
            self.j.blindaje = 100.0
            self.decir("Te pones un chaleco antibalas.")
        if r.get("barco"):
            b = r["barco"]
            mo = self.modelos.get(b["modelo"])
            e = self.lug(b.get("en"))
            if mo and e:
                self.j.barcos.append({"modelo": mo["id"], "nombre": mo["nombre"], "salud": mo["salud"], "en": e.id})
                self.decir(f"Ahora es tuyo: {mo['nombre']}. Está amarrado en {self.nombre_lugar(e)}.")
        nuevas = [x for x in self.misiones_disponibles() if x["id"] not in antes]
        if len(nuevas) > 3:
            self.decir(f"Hay {len(nuevas)} misiones nuevas disponibles, algunas en otras localidades. Míralas en el móvil con M.")
        else:
            for x in nuevas:
                self.decir(f"Nueva misión disponible: {x['titulo']}, en {self.nombre_lugar(self.lugares[x['lugar']])}. Abre el móvil con M para marcarla en el GPS.")
        from . import menus_juego
        menus_juego.autoguardar(self)

    def fallar_mision(self, motivo):
        ms = self.mision
        if not ms:
            return
        m = ms["def"]
        copia = ms["copia"]
        reloj, dia = ms["reloj"], ms["dia"]
        control = ms.get("control")
        repeticion = bool(ms.get("repeticion"))
        self._limpiar_mision()
        self.app.son("mision_fallo")
        if not repeticion:
            self.fallos[m["id"]] = self.fallos.get(m["id"], 0) + 1

        def saltar():
            self.app.cerrar(menu)
            antes = {x["id"] for x in self.misiones_disponibles()}
            self.completadas.append(m["id"])
            self.saltadas.append(m["id"])
            self.fallos.pop(m["id"], None)
            self.app.son("notificacion")
            self.decir(f"Te saltas {m['titulo']}. Cuenta como hecha, sin recompensa. Puedes repetirla cuando quieras desde el diario del móvil.")
            for x in [x for x in self.misiones_disponibles() if x["id"] not in antes][:3]:
                self.decir(f"Nueva misión disponible: {x['titulo']}, en {self.nombre_lugar(self.lugares[x['lugar']])}.")
            from . import menus_juego
            menus_juego.autoguardar(self)

        def desde_control():
            self.app.cerrar(menu)
            stats = dict(self.j.stats)
            self.j.de_dict(copy.deepcopy(control["copia"]))
            self.j.stats.update({k: stats[k] for k in ("muertes", "detenciones", "tiempo")})
            self.reloj, self.dia = control["reloj"], control["dia"]
            self._fin_persecucion()
            if self.j.veh:
                v = self.j.veh
                self.salir_vehiculo(forzado=True)
                self.quitar_vehiculo(v)
            if control["mapa"] != self.mundo.id:
                self.cambiar_mapa(control["mapa"], control["x"], control["y"])
            self.teletransportar(control["x"], control["y"])
            if self.trabajo:
                self.terminar_trabajo("")
            self.cancelar_gps()
            self.mision = {"def": m, "paso": control["paso"] - 1, "veh": None, "enemigos": [], "objeto": None, "limite": None, "repeticion": repeticion,
                           "copia": copia, "reloj": reloj, "dia": dia, "generado": False, "recogido": False, "restos": None,
                           "avisos": set(), "quedan": None, "control": control, "reanudando": True}
            self.app.son("notificacion")
            self.decir(f"Vuelves al último punto de control de {m['titulo']}.", True)
            self._siguiente_paso()

        def reintentar():
            self.app.cerrar(menu)
            stats = dict(self.j.stats)
            self.j.de_dict(copy.deepcopy(copia))
            self.j.stats.update({k: stats[k] for k in ("muertes", "detenciones", "tiempo")})
            self.reloj, self.dia = reloj, dia
            self._fin_persecucion()
            l = self.lugares[m["lugar"]]
            if l.mapa != self.mundo.id:
                if self.j.veh:
                    v = self.j.veh
                    self.salir_vehiculo(forzado=True)
                    self.quitar_vehiculo(v)
                self.cambiar_mapa(l.mapa, l.x, l.y)
            self.teletransportar(l.x, l.y)
            self.iniciar_mision(m, True, repeticion)

        def abandonar():
            self.app.cerrar(menu)
            self.decir("Misión abandonada. Puedes volver a intentarla cuando quieras desde el mismo lugar.")

        extra = [Opcion("Reintentar desde el último punto de control", desde_control,
                        ayuda="Vuelves al momento en que empezó el último tramo que habías alcanzado, con lo que tenías entonces. No repites lo anterior.")] if control else []
        if not repeticion and not m.get("repetible") and self.fallos.get(m["id"], 0) >= 3:
            extra.append(Opcion("Saltarte esta misión", saltar,
                                ayuda="La has fallado tres veces o más. Si te la saltas, cuenta como hecha y la historia sigue, pero no cobras la recompensa. Luego puedes repetirla desde el diario del móvil."))
        menu = Menu(self.app, f"Misión fallida: {m['titulo']}. {motivo}",
                    extra + [Opcion("Reintentar desde el principio de la misión", reintentar, ayuda="Vuelves al lugar donde empieza la misión, con el dinero, la salud y las armas que tenías al aceptarla."),
                     Opcion("Dejarlo por ahora", abandonar)], escapable=False)
        self.app.abrir(menu)

    def abandonar_mision(self):
        if not self.mision:
            return
        self._limpiar_mision()
        self.decir("Misión abandonada.", True)
