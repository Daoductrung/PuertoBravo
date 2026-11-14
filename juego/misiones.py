"""Motor de misiones. Las misiones se definen en datos/misiones.json (y en mods)."""
import copy
import math
import random

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
    def iniciar_mision(self, m, reintento=False):
        if self.trabajo:
            self.terminar_trabajo("Dejas el trabajo para empezar la misión.")
        self.cancelar_gps()
        self.mision = {"def": m, "paso": -1, "veh": None, "enemigos": [], "objeto": None, "limite": None,
                       "copia": copy.deepcopy(self.j.a_dict()), "reloj": self.reloj, "dia": self.dia,
                       "generado": False, "recogido": False, "restos": None, "avisos": set(), "quedan": None}
        self.app.son("notificacion")
        self.decir(f"Misión: {m['titulo']}.", True)
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
        if tipo == "ir":
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
        if m.get("territorio") and m["territorio"] not in self.j.territorios:
            self.j.territorios.append(m["territorio"])
            self.son("territorio", cat="interfaz")
            self.decir("El barrio es tuyo. Te pagará 300 euros cada medianoche.")
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
        self._limpiar_mision()
        self.app.son("mision_fallo")

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
            self.mision = {"def": m, "paso": control["paso"] - 1, "veh": None, "enemigos": [], "objeto": None, "limite": None,
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
            self.iniciar_mision(m, True)

        def abandonar():
            self.app.cerrar(menu)
            self.decir("Misión abandonada. Puedes volver a intentarla cuando quieras desde el mismo lugar.")

        extra = [Opcion("Reintentar desde el último punto de control", desde_control,
                        ayuda="Vuelves al momento en que empezó el último tramo que habías alcanzado, con lo que tenías entonces. No repites lo anterior.")] if control else []
        menu = Menu(self.app, f"Misión fallida: {m['titulo']}. {motivo}",
                    extra + [Opcion("Reintentar desde el principio de la misión", reintentar, ayuda="Vuelves al lugar donde empieza la misión, con el dinero, la salud y las armas que tenías al aceptarla."),
                     Opcion("Dejarlo por ahora", abandonar)], escapable=False)
        self.app.abrir(menu)

    def abandonar_mision(self):
        if not self.mision:
            return
        self._limpiar_mision()
        self.decir("Misión abandonada.", True)
