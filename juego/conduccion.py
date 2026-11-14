"""Vehículos: conducción del jugador (asistida o libre), tráfico, policía motorizada."""
import math
import random

import pygame

from . import mundo as M
from .entidades import Persona, Vehiculo


class Conduccion:
    # ------------------------------------------------------------- utilidades
    def modo_asistido(self):
        v = self.j.veh
        if v is not None and v.modelo.get("vuela"):
            return False
        return self.cfg["conduccion"] == "asistida" and not self.libre_temp and self.mundo.tipo != "mar"

    def _alinear(self, v):
        """Coloca el vehículo en el sentido de la vía más cercana. False si está fuera de la calzada."""
        t, idx, dist = self.mundo.via_cercana(v.x, v.y)
        if dist > M.ACERA + 1:
            return False
        r = v.rumbo % 360
        if t == "H":
            v.dir = 1 if 0 <= r < 180 else 3
        else:
            v.dir = 0 if (r < 90 or r >= 270) else 2
        v.rumbo = v.dir * 90.0
        return True

    def preparar_conduccion(self):
        v = self.j.veh
        if not v:
            return
        if self.mundo.tipo == "mar" or v.modelo.get("vuela"):
            self.libre_temp = False
        elif self.cfg["conduccion"] == "asistida":
            self.libre_temp = not self._alinear(v)
            if self.libre_temp:
                self.decir("Estás fuera de la calzada: conducción libre hasta que vuelvas a una calle.")
        else:
            self.libre_temp = False
        v.aviso_cruce = None

    def _motor(self, v, propio):
        if v.canal is None:
            if propio:
                v.canal = self.son(v.modelo["motor"], bucle=True, vol=0.42, tono=v.modelo["tono"] * 0.6)
            else:
                v.canal = self.son(v.modelo["motor"], bucle=True, xy=(v.x, v.y), ref=7, maxd=95, vol=0.85, tono=v.modelo["tono"] * 0.6)

    @staticmethod
    def _linea_cruzada(a0, a1):
        if a1 > a0:
            k = math.floor(a1 / M.B)
            return k if k > math.floor(a0 / M.B) or (a0 < k * M.B <= a1) else None
        if a1 < a0:
            k = math.ceil(a1 / M.B)
            return k if k < math.ceil(a0 / M.B) else None
        return None

    def _mover_via(self, v, dt, lat_obj, decidir):
        m = self.mundo
        dx, dy = M.DIRS[v.dir]
        if dx == 0:
            i = m._idx(v.x, m.NX)
            obj = m.carril("V", i, v.dir, lat_obj)
            v.x += max(-6 * dt, min(6 * dt, obj - v.x))
            a0 = v.y
            v.y += dy * v.vel * dt
            if v.vel > 0:
                linea = self._linea_cruzada(a0, v.y)
                if linea is not None and 0 <= linea < m.NY:
                    self._en_cruce(v, i, linea, decidir)
            if v.y < 0 or v.y > m.alto:
                v.y = max(0.0, min(m.alto, v.y))
                v.vel = 0.0
        else:
            jj = m._idx(v.y, m.NY)
            obj = m.carril("H", jj, v.dir, lat_obj)
            v.y += max(-6 * dt, min(6 * dt, obj - v.y))
            a0 = v.x
            v.x += dx * v.vel * dt
            if v.vel > 0:
                linea = self._linea_cruzada(a0, v.x)
                if linea is not None and 0 <= linea < m.NX:
                    self._en_cruce(v, linea, jj, decidir)
            if v.x < 0 or v.x > m.ancho:
                v.x = max(0.0, min(m.ancho, v.x))
                v.vel = 0.0
        v.rumbo = v.dir * 90.0

    def _en_cruce(self, v, i, j, decidir):
        nd = decidir(v, i, j)
        if nd != v.dir:
            v.dir = nd
            m = self.mundo
            if nd in (0, 2):
                v.x = m.carril("V", i, nd)
                v.y = j * M.B + M.DIRS[nd][1] * 1.0
            else:
                v.y = m.carril("H", j, nd)
                v.x = i * M.B + M.DIRS[nd][0] * 1.0
            v.rumbo = nd * 90.0

    def _validas(self, v, i, j, atras=False):
        ops = [d for d in (v.dir, (v.dir + 1) % 4, (v.dir - 1) % 4) if self.mundo.dir_valida(i, j, d)]
        if not ops or atras:
            ops.append((v.dir + 2) % 4)
        return ops

    def _decidir_trafico(self, v, i, j):
        ops = self._validas(v, i, j)
        if v.dir in ops and random.random() < 0.6:
            return v.dir
        return random.choice(ops)

    def _decidir_policia(self, v, i, j):
        px, py = self.pos()
        ops = self._validas(v, i, j)
        return min(ops, key=lambda d: abs((i + M.DIRS[d][0]) * M.B - px) + abs((j + M.DIRS[d][1]) * M.B - py) + random.uniform(0, 20))

    def _decidir_huida(self, v, i, j):
        px, py = self.pos()
        ops = self._validas(v, i, j)
        return max(ops, key=lambda d: math.hypot((i + M.DIRS[d][0]) * M.B - px, (j + M.DIRS[d][1]) * M.B - py) + random.uniform(0, 70))

    def _decidir_jugador(self, v, i, j):
        m = self.mundo
        g = v.giro
        if g == 0 and self.cfg["piloto_gps"]:
            g = self.giro_gps()
        cand = {-1: (v.dir - 1) % 4, 1: (v.dir + 1) % 4, 2: (v.dir + 2) % 4}.get(g, v.dir)
        forzado = False
        if not m.dir_valida(i, j, cand):
            forzado = True
            cand = next(d for d in (v.dir, (v.dir + 1) % 4, (v.dir - 1) % 4, (v.dir + 2) % 4) if m.dir_valida(i, j, d))
        v.giro = 0
        self._parar_intermitente()
        self.cruce_act = (i, j)
        if cand != v.dir:
            if abs(v.vel) > 15:
                self.son("frenazo", vol=0.6)
                if abs(v.vel) > 24:
                    self.danar_vehiculo(v, 6)
                    self.decir("¡Derrapas!")
                v.vel *= 0.6
            via = m.avenidas[i] if cand in (0, 2) else m.calles[j]
            self.decir(("Fin de la vía. " if forzado else "") + f"{via}, hacia el {M.NOMBRE_DIR[cand]}.")
        return cand

    def _parar_intermitente(self):
        c = getattr(self, "intermitente", None)
        if c:
            c.parar()
        self.intermitente = None

    # ---------------------------------------------------- entrar y salir
    def entrar_salir(self):
        if getattr(self, "pasajero", None) is not None:
            self.bajar_de_amigo()
            return
        if not self.j.veh and self.subir_con_amigo():
            return
        self._entrar_salir()

    def _entrar_salir(self):
        j = self.j
        if self.mundo.tipo == "mar":
            self.decir("No puedes bajarte en mitad del mar. Acércate a un muelle y pulsa Intro para atracar.", True)
            return
        if j.veh:
            if abs(j.veh.vel) > 3:
                self.decir("Frena antes de bajarte.", True)
                return
            if j.veh.modelo.get("vuela") and not self.mundo.transitable(j.veh.x, j.veh.y):
                self.decir("No puedes aterrizar aquí: debajo hay un edificio. Busca una calle o un espacio abierto; la tecla C te dice sobre qué estás.", True)
                return
            self.salir_vehiculo()
            return
        if self.forzando:
            self.forzando["canal"].parar()
            self.forzando = None
            self.decir("Dejas de forzar la cerradura.", True)
            return
        cerca = [v for v in self.vehiculos if not v.muerto and v.dist(j.x, j.y) <= 5.5]
        if not cerca:
            self.decir("No hay ningún vehículo a tu lado. Usa el radar con Tabulador para encontrar uno.", True)
            return
        v = min(cerca, key=lambda v: (v.tag != "mision", v.dist(j.x, j.y)))
        if v.ardiendo >= 0:
            self.decir("¡Ese vehículo está ardiendo!", True)
            return
        if v.ia == "policia" and not v.desplegado and v.ocupado:
            self.decir("Ese coche patrulla está lleno de policías.", True)
            return
        if v.ia in ("trafico", "huida") and v.ocupado:
            if abs(v.vel) > 6:
                self.decir("Va demasiado rápido para abrir la puerta.", True)
                return
            self.son("puerta_coche", xy=(v.x, v.y))
            p = Persona("civil", *self.mundo.punto_libre(v.x + 2, v.y + 2), nombre="Conductor")
            p.estado = "huye"
            p.t_estado = 12
            self.personas.append(p)
            self.son("grito", xy=(p.x, p.y))
            self.delito(2, "robo de vehículo con violencia")
            v.ocupado = False
            self._subir(v, True)
            return
        if v.cerrado:
            con_ganzua = j.objetos.get("ganzua", 0) > 0
            self.forzando = {"veh": v, "t": 1.5 if con_ganzua else 3.5, "ganzua": con_ganzua,
                             "canal": self.son("ganzua", bucle=True, vol=0.7)}
            self.decir(f"Fuerzas la cerradura de {v.nombre}" + (" con la ganzúa." if con_ganzua else ". No te muevas."), True)
            return
        self._subir(v, v.ia == "policia" or not getattr(v, "propio", False))

    def _forzar(self, dt):
        f = self.forzando
        v = f["veh"]
        if v.muerto or v.dist(self.j.x, self.j.y) > 6:
            f["canal"].parar()
            self.forzando = None
            return
        f["t"] -= dt
        if f["t"] <= 0:
            f["canal"].parar()
            self.forzando = None
            v.cerrado = False
            if f["ganzua"]:
                self.j.objetos["ganzua"] -= 1
            elif v.con_alarma:
                v.alarma = self.son("alarma", bucle=True, xy=(v.x, v.y), ref=8, maxd=110, vol=0.8)
                v.t_alarma = 18.0
                self.decir("¡Salta la alarma!")
                self.delito(1.2, "robo de vehículo", siempre=bool(v.tag))
            else:
                self.delito(0.5, "robo de vehículo")
            self._subir(v, True)

    def _subir(self, v, robado, callar=False):
        j = self.j
        if v.sirena:
            v.sirena.parar()
            v.sirena = None
        if v.canal:
            v.canal.parar()
            v.canal = None
        if v.plaza is not None:
            self.plazas_usadas.add(v.plaza)
            self.plazas_activas.pop(v.plaza, None)
            v.plaza = None
        if v.ia == "policia":
            self.delito(3, "robo de un coche patrulla", siempre=True)
        v.ia = None
        v.ocupado = False
        v.vel = 0.0
        if robado and not getattr(v, "propio", False):
            j.stats["vehiculos_robados"] += 1
        v.propio = True
        j.veh = v
        j.agachado = False
        self.oy_rumbo = v.rumbo
        self.son("puerta_coche")
        self.son("arranque", vol=0.6)
        self._motor(v, True)
        self.rodadura = self.son("rodadura", bucle=True, vol=0.0)
        self.preparar_conduccion()
        r = self.app.radio.sintonizar(self.cfg["emisora"])
        if callar:
            return
        txt = f"Subes a {v.nombre}. Estado {int(100 * v.salud / v.salud_max)} por ciento. Miras al {M.cardinal(v.rumbo)}."
        if v.modelo.get("trabajo"):
            txt += " Pulsa J para trabajar con este vehículo."
        if v.modelo.get("sirena"):
            txt += " La tecla P enciende la sirena."
        if v.modelo.get("vuela"):
            txt += " Vuelas por encima de todo: izquierda y derecha giran, arriba acelera. Para bajarte, detente sobre una calle o un espacio abierto."
        self.decir(txt, True)
        if self.app.radio.id_actual() != "apagada":
            self.decir(r)

    def salir_vehiculo(self, forzado=False):
        j = self.j
        v = j.veh
        if not v:
            return
        j.veh = None
        self._parar_intermitente()
        if v.canal:
            v.canal.parar()
            v.canal = None
        if getattr(self, "rodadura", None):
            self.rodadura.parar()
            self.rodadura = None
        self.app.radio.apagar()
        if self.sirena_propia:
            self.sirena_propia.parar()
            self.sirena_propia = None
        v.vel = 0.0
        v.ia = None
        rad = math.radians(v.rumbo + 90)
        for lado in (3.0, -3.0, 5.0, -5.0, 0.0):
            x, y = v.x + math.sin(rad) * lado, v.y + math.cos(rad) * lado
            if self.mundo.transitable(x, y):
                j.x, j.y = x, y
                break
        if not self.mundo.transitable(j.x, j.y):
            j.x, j.y = self.mundo.punto_libre(v.x, v.y)
        j.rumbo = v.rumbo
        self.libre_temp = False
        if self.trabajo and self.trabajo.get("veh") is v:
            self.terminar_trabajo("Dejas el vehículo de trabajo.")
        if not forzado:
            self.son("puerta_coche")
            self.decir(f"Te bajas. {self.mundo.describir(j.x, j.y)}.", True)

    # ------------------------------------------------------ teclas al volante
    def tecla_coche(self, ev, mayus):
        k = ev.key
        v = self.j.veh
        if k in (pygame.K_LEFT, pygame.K_RIGHT) and self.modo_asistido():
            g = 1 if k == pygame.K_RIGHT else -1
            self._parar_intermitente()
            if v.giro == g:
                v.giro = 0
                self.decir("Intermitente quitado. Seguirás recto.", True)
            else:
                v.giro = g
                self.intermitente = self.son("intermitente", bucle=True, pan=0.7 * g, vol=0.6)
                self.decir("Girarás a la " + ("derecha" if g > 0 else "izquierda") + " en el próximo cruce.", True)
        elif k == pygame.K_u:
            if abs(v.vel) > 6:
                self.decir("Frena para dar media vuelta.", True)
            elif self.modo_asistido():
                v.dir = (v.dir + 2) % 4
                v.rumbo = v.dir * 90.0
                v.aviso_cruce = None
                self.decir(f"Media vuelta. Ahora vas hacia el {M.NOMBRE_DIR[v.dir]}.", True)
            else:
                v.rumbo = (v.rumbo + 180) % 360
                self.decir(f"Media vuelta. Vas hacia el {M.cardinal(v.rumbo)}.", True)
        elif k == pygame.K_h:
            self.son(v.modelo.get("claxon", "claxon"), vol=0.8)
            self.enviar_evento("claxon")
            for p in self.personas:
                if p.tipo == "civil" and not p.muerto and p.dist(v.x, v.y) < 18 and p.estado == "pasea":
                    p.estado = "huye"
                    p.t_estado = 4
        elif k == pygame.K_r:
            self.son("radio_cambio", vol=0.5, cat="musica")
            if mayus:
                self.cfg["emisora"] = 0
            else:
                if self.app.radio.id_actual() == "usuario" and len(self.app.radio.pistas_usuario) > self.app.radio.pista_idx % max(1, len(self.app.radio.pistas_usuario)) + 1:
                    self.decir(self.app.radio.siguiente_pista(), True)       # dentro de «Mi música», R pasa de canción
                    return
                self.app.radio.pista_idx = 0
                self.cfg["emisora"] = (self.cfg["emisora"] + 1) % len(self.app.radio.emisoras)
            self.decir(self.app.radio.sintonizar(self.cfg["emisora"]), True)
        elif k == pygame.K_e:
            if not self.modo_asistido():
                v.rumbo = round(v.rumbo / 90.0) * 90 % 360
                self.decir(f"Enderezas hacia el {M.cardinal(v.rumbo)}.", True)
        elif k == pygame.K_j:
            self.alternar_trabajo()
        elif k == pygame.K_w:
            self.decir(f"{int(abs(v.vel) * 3.6)} kilómetros por hora.", True)
        elif k == pygame.K_y:
            self.cfg["piloto_gps"] = not self.cfg["piloto_gps"]
            if not self.cfg["piloto_gps"]:
                self.decir("Piloto del GPS desactivado.", True)
            elif not self.modo_asistido():
                self.decir("Piloto del GPS activado, pero solo funciona en conducción asistida. Cámbiala en Opciones, Movimiento y conducción.", True)
            elif not self.gps:
                self.decir("Piloto del GPS activado. Marca un destino en el GPS y el coche irá solo: acelera, frena, gira y para en los semáforos.", True)
            else:
                self.decir(f"Piloto del GPS activado: el coche va solo hasta {self.gps['nombre']}. Con cualquier flecha o el espacio mandas tú.", True)

    def piloto_completo(self):
        """¿Conduce el coche solo? Con el piloto del GPS activado, en conducción asistida, en tierra y con un destino marcado."""
        v = self.j.veh
        return bool(self.cfg["piloto_gps"] and self.gps and v and self.modo_asistido() and self.mundo.tipo != "mar"
                    and not v.modelo.get("barco") and not v.modelo.get("vuela"))

    def _pilotar(self, v, dt, freno):
        """El piloto lleva los pedales: velocidad de ciudad, despacio al llegar y parado en rojo o con algo delante."""
        mo = v.modelo
        dx, dy = self.gps["dest"]
        dist = math.hypot(dx - v.x, dy - v.y)
        objetivo = min(mo["vel_max"] * 0.6, 14.0)
        if dist < 45:
            objetivo = min(objetivo, max(3.0, dist * 0.3))
        if self._semaforo_rojo(v):
            objetivo = 0.0
            if self.t - getattr(self, "t_aviso_rojo", -99) > 20:
                self.t_aviso_rojo = self.t
                self.decir("Semáforo en rojo. El piloto espera.")
        if v.vel < objetivo:
            v.vel = min(objetivo, v.vel + mo["acel"] * 0.8 * dt)
        elif v.vel > objetivo:
            v.vel = max(objetivo, v.vel - freno * dt)

    # --------------------------------------------------------- conducir
    def conducir(self, dt):
        j = self.j
        v = j.veh
        t = self.app.teclas
        mo = v.modelo
        from . import sistemas                          # las mejoras del taller cambian cómo va el vehículo
        freno = mo["freno"] * (0.6 if self.lluvia else 1.0) * sistemas.factor_frenada(v)
        if v.ardiendo >= 0:
            v.vel -= math.copysign(min(abs(v.vel), 6 * dt), v.vel)
        elif pygame.K_UP in t:
            v.vel += mo["acel"] * sistemas.factor_aceleracion(v) * dt * (2.5 if v.vel < 0 else 1.0)
        elif pygame.K_DOWN in t:
            if v.vel > 0.3:
                v.vel = max(0.0, v.vel - freno * dt)
            else:
                v.vel = max(-6.0, v.vel - 4 * dt)
        elif self.piloto_completo() and pygame.K_SPACE not in t:
            self._pilotar(v, dt, freno)
        else:
            v.vel -= math.copysign(min(abs(v.vel), 1.8 * dt), v.vel)
        if pygame.K_SPACE in t and abs(v.vel) > 0:
            if abs(v.vel) > 9 and self.t - getattr(self, "t_frenazo", -9) > 1.2:
                self.t_frenazo = self.t
                self.son("frenazo", vol=0.5)
            v.vel -= math.copysign(min(abs(v.vel), freno * 1.7 * dt), v.vel)
        vmax = mo["vel_max"] * sistemas.factor_velocidad(v) * (0.55 + 0.45 * min(1.0, v.salud / (0.5 * v.salud_max))) * (1 + 0.01 * self.nivel("conduccion"))
        v.vel = min(v.vel, vmax)
        x0, y0 = v.x, v.y
        if self.modo_asistido():
            lat = -6.0 if pygame.K_a in t else 2.2 if pygame.K_d in t else 0.0
            if (self.cfg["frenada_auto"] or self.piloto_completo()) and v.vel > 0:
                self._frenada_auto(v, dt, freno)
            self._aviso_cruce(v)
            self._mover_via(v, dt, lat, self._decidir_jugador)
            if self.mundo.via_cercana(v.x, v.y)[2] > M.ACERA + 2:
                self.libre_temp = True
        else:
            self._conducir_libre(v, dt, t)
        j.stats["metros_coche"] += math.hypot(v.x - x0, v.y - y0)
        self.ganar_xp("conduccion", math.hypot(v.x - x0, v.y - y0) / 60.0)
        if v.canal:
            carga = 0.12 if pygame.K_UP in t else 0.0
            v.canal.tono(mo["tono"] * sistemas.factor_tono(v) * (0.6 + carga + 1.3 * abs(v.vel) / mo["vel_max"]))
        if getattr(self, "rodadura", None):
            self.rodadura.volumen(min(0.5, abs(v.vel) / 50.0))
            self.rodadura.tono(0.7 + abs(v.vel) / 40.0)
        self._choques_jugador(v)
        self._sonar(v, dt)
        if (pygame.K_LCTRL in t or pygame.K_RCTRL in t) and self.arma().get("automatica"):
            self.atacar()

    def _frenada_auto(self, v, dt, freno):
        """Asistente: frena solo para no embestir al vehículo que va delante en tu carril."""
        dx, dy = M.DIRS[v.dir]
        mejor = None
        for o in self.vehiculos:
            if o is v or o.muerto or o.tag == "objetivo" or o.ia in ("policia", "huida"):
                continue
            a = (o.x - v.x) * dx + (o.y - v.y) * dy
            lat = abs((o.x - v.x) * dy - (o.y - v.y) * dx)
            if 0 < a < 40 and lat < 2.3 and (mejor is None or a < mejor[0]):
                vel_o = o.vel * (1 if o.ia not in ("aparcado", None) and o.dir == v.dir else 0)
                mejor = (a, max(0.0, vel_o))
        if mejor is None:
            self.t_atasco = 0.0
            return
        a, vel_o = mejor
        hueco = a - 5.5
        seguro = vel_o + max(0.0, hueco) * 0.9
        if v.vel > seguro:
            v.vel = max(seguro if hueco > 0 else 0.0, v.vel - freno * 1.6 * dt)
        if v.vel < 0.5 and vel_o < 0.5:
            self.t_atasco = getattr(self, "t_atasco", 0.0) + dt
            if self.t_atasco > 2.5 and self.t - getattr(self, "t_aviso_atasco", -99) > 25:
                self.t_aviso_atasco = self.t
                self.decir("Tráfico detenido delante. Espera, o mantén pulsada la A para adelantar por la izquierda.")
        else:
            self.t_atasco = 0.0

    def _aviso_cruce(self, v):
        m = self.mundo
        dx, dy = M.DIRS[v.dir]
        a = v.y if dx == 0 else v.x
        s = dy if dx == 0 else dx
        idx = math.floor(a / M.B) + 1 if s > 0 else math.ceil(a / M.B) - 1
        tope = m.NY if dx == 0 else m.NX
        if not (0 <= idx < tope) or v.vel <= 0.5:
            return
        d = abs(idx * M.B - a)
        clave = (v.dir, idx)
        if d < max(32.0, v.vel * 3.2) and v.aviso_cruce != clave:
            v.aviso_cruce = clave
            if v.giro == 0 and self.cfg["piloto_gps"]:
                g = self.giro_gps()
                if g in (-1, 1):
                    v.giro = g
            if self.cfg["anunciar_cruces"]:
                via = m.calles[idx] if dx == 0 else m.avenidas[idx]
                i, jj = (m._idx(v.x, m.NX), idx) if dx == 0 else (idx, m._idx(v.y, m.NY))
                txt = f"Cruce con {via}"
                if v.giro:
                    txt += ", girarás a la " + ("derecha" if v.giro > 0 else "izquierda")
                elif not m.dir_valida(i, jj, v.dir):
                    txt += ", fin de la vía"
                self.son("cruce", cat="interfaz", vol=0.5)
                self.decir(txt + ".")

    def _conducir_libre(self, v, dt, t):
        giro = (1 if pygame.K_RIGHT in t else 0) - (1 if pygame.K_LEFT in t else 0)
        mar = self.mundo.tipo == "mar"
        if giro:
            antes = M.cardinal(v.rumbo)
            v.rumbo = (v.rumbo + giro * (55 if mar else 80) * dt * min(1.0, abs(v.vel) / 5.0 + (0.35 if mar else 0)) * (1 if v.vel >= 0 else -1)) % 360
            if M.cardinal(v.rumbo) != antes:
                self.decir(M.cardinal(v.rumbo).capitalize(), True)
        rad = math.radians(v.rumbo)
        sx, sy = math.sin(rad), math.cos(rad)
        nx, ny = v.x + sx * v.vel * dt, v.y + sy * v.vel * dt
        s = self.mundo.superficie(nx, ny)
        if v.modelo.get("vuela"):
            if s == "fuera" or (mar and not (0 <= nx <= self.mundo.ancho and 0 <= ny <= self.mundo.alto)):
                v.vel = 0.0
                self.decir("Fin del mapa. Da la vuelta, o usa un helipuerto para volar a otra localidad.")
                return
            v.x, v.y = nx, ny
            v.dir = M.dir_de_rumbo(v.rumbo)
            return
        if mar:
            if s != "agua":
                imp = abs(v.vel)
                if imp > 2:
                    self.son("choque" if imp > 8 else "choque_leve")
                    self.danar_vehiculo(v, imp * 1.2)
                    self.decir("¡Encallas en la arena de una isla!" if s == "arena" else "Fin del mapa: aquí empieza el océano abierto. Da la vuelta.")
                v.vel = -v.vel * 0.2
                return
            v.x, v.y = nx, ny
            v.dir = M.dir_de_rumbo(v.rumbo)
            return
        if s in ("pared", "fuera"):
            imp = abs(v.vel)
            if imp > 2:
                self.son("choque" if imp > 8 else "choque_leve")
                self.danar_vehiculo(v, imp * 1.3)
                if imp > 12:
                    self.danar_jugador(imp * 0.6, None)
                self.app.vibrar(min(1.0, imp / 12.0), 0.6, 350)
                self.decir("¡Te estrellas contra una pared!" if s == "pared" else "Fin de la ciudad.")
            v.vel = -v.vel * 0.25
            return
        v.x, v.y = nx, ny
        if s in ("hierba", "arena") and v.modelo["id"] != "todoterreno":
            v.vel *= max(0.0, 1.0 - 0.8 * dt)
        v.dir = M.dir_de_rumbo(v.rumbo)
        # aviso de bordillo: suena por el lado en el que se acaba la calzada
        self.t_bordillo -= dt
        if self.t_bordillo <= 0 and abs(v.vel) > 2:
            self.t_bordillo = 0.3
            for lado in (-1, 1):
                lx = v.x + sx * 4 + sy * 3.5 * lado
                ly = v.y + sy * 4 - sx * 3.5 * lado
                if self.mundo.superficie(lx, ly) != "calzada":
                    self.son("bordillo", pan=0.85 * lado, vol=0.6, cat="interfaz")
                    self.app.vibrar(0.5 if lado < 0 else 0.0, 0.0 if lado < 0 else 0.5, 120)
        if self.libre_temp and s == "calzada" and self.cfg["conduccion"] == "asistida":
            t_, idx, dist = self.mundo.via_cercana(v.x, v.y)
            eje = 90 if t_ == "H" else 0
            desv = abs(M.norm180(v.rumbo - eje))
            if min(desv, 180 - desv) < 35 and dist < M.CALZADA:
                self.libre_temp = False
                self._alinear(v)
                v.aviso_cruce = None
                self.decir(f"De nuevo en {self.mundo.nombre_via(t_, idx)}. Conducción asistida.")

    def _sonar(self, v, dt):
        """Sensor de proximidad: pita más rápido cuanto más cerca está el obstáculo de delante."""
        if not self.cfg["sonar"] or abs(v.vel) < 1 or v.modelo.get("vuela"):
            return
        self.t_sonar -= dt
        if self.t_sonar > 0:
            return
        rad = math.radians(v.rumbo)
        sx, sy = math.sin(rad), math.cos(rad)
        mejor = None
        for o in self.vehiculos:
            if o is v or o.muerto:
                continue
            a = (o.x - v.x) * sx + (o.y - v.y) * sy
            lat = (o.x - v.x) * sy - (o.y - v.y) * sx
            if 0 < a < 45 and abs(lat) < 2.6 and (mejor is None or a < mejor[0]):
                mejor = (a, lat)
        if mejor is None:
            self.t_sonar = 0.15
            return
        self.son("sonar", pan=max(-1, min(1, mejor[1] / 2.6)), vol=0.5, tono=1.0 + (45 - mejor[0]) / 90.0, cat="interfaz")
        self.t_sonar = max(0.08, mejor[0] / 45.0 * 0.8)

    def _choques_jugador(self, v):
        if v.t_choque > self.t or v.modelo.get("vuela"):
            return
        for o in self.vehiculos:
            if o is v or o.muerto:
                continue
            if abs(o.x - v.x) < 4 and abs(o.y - v.y) < 4 and o.dist(v.x, v.y) < 3.4:
                rad = math.radians(v.rumbo)
                rel = v.vel - (o.vel * math.cos(math.radians(o.rumbo - v.rumbo)) if o.ia not in ("aparcado", None) else 0.0)
                imp = abs(rel)
                if imp < 1.5:
                    continue
                v.t_choque = self.t + 0.6
                self.son("choque" if imp > 8 else "choque_leve", xy=(o.x, o.y), ref=10)
                self.app.vibrar(min(1.0, imp / 14.0), 0.5, 300)
                self.danar_vehiculo(v, imp * (0.4 if o.tag == "objetivo" else 0.6) * (1 - 0.03 * self.nivel("conduccion")))
                self.danar_vehiculo(o, imp * (2.2 if o.tag == "objetivo" else 1.4))
                if imp > 14:
                    self.danar_jugador(imp * 0.4, None)
                atras = -1 if v.vel > 0 else 1
                v.x += math.sin(rad) * 1.5 * atras
                v.y += math.cos(rad) * 1.5 * atras
                v.vel *= 0.35
                if o.ia in ("trafico", "huida", "policia"):
                    o.vel = max(o.vel, min(o.vel + imp * 0.4, 30)) if o.ia == "huida" else o.vel * 0.6
                if o.ia == "trafico":
                    self.son(o.modelo.get("claxon", "claxon"), xy=(o.x, o.y))
                if o.ia == "policia":
                    self.delito(1, None, siempre=True)
                return
        if abs(v.vel) > 3:
            for p in self.personas:
                if not p.muerto and p.tipo not in ("aliado", "perro") and abs(p.x - v.x) < 3 and abs(p.y - v.y) < 3 and p.dist(v.x, v.y) < 2.3:
                    self.son("golpe", xy=(p.x, p.y))
                    self.danar_persona(p, abs(v.vel) * 8, atropello=True)
                    v.vel *= 0.8

    # ------------------------------------------------- vehículos del mundo
    def _obstaculo(self, v, alcance=13.0):
        dx, dy = M.DIRS[v.dir]
        j = self.j
        px, py = self.pos()
        cand = [(px, py)] if (j.veh or self.mundo.superficie(px, py) == "calzada") else []
        for o in self.vehiculos:
            if o is not v and o is not j.veh and o.ia != "aparcado" and not o.muerto:
                cand.append((o.x, o.y))
        for cx, cy in cand:
            a = (cx - v.x) * dx + (cy - v.y) * dy
            lat = abs((cx - v.x) * dy - (cy - v.y) * dx)
            if 0.5 < a < alcance and lat < 2.4:
                return True
        return False

    def _semaforo_rojo(self, v):
        m = self.mundo
        dx, dy = M.DIRS[v.dir]
        a = v.y if dx == 0 else v.x
        s = dy if dx == 0 else dx
        idx = math.floor(a / M.B) + 1 if s > 0 else math.ceil(a / M.B) - 1
        d = abs(idx * M.B - a)
        if not (7.5 < d < 17):
            return False
        if dx == 0:
            return 0 <= idx < m.NY and not m.verde_vertical(m._idx(v.x, m.NX), idx, self.t)
        return 0 <= idx < m.NX and m.verde_vertical(idx, m._idx(v.y, m.NY), self.t)

    def actualizar_vehiculos(self, dt):
        j = self.j
        px, py = self.pos()
        for v in list(self.vehiculos):
            if v.muerto:
                continue
            if v.ardiendo >= 0:
                v.ardiendo -= dt
                if v.fuego:
                    v.fuego.mover(v.x, v.y)
                if v.ardiendo <= 0:
                    self.explotar(v)
                    continue
            if v.alarma is not None:
                v.t_alarma = getattr(v, "t_alarma", 0) - dt
                v.alarma.mover(v.x, v.y)
                if v.t_alarma <= 0:
                    v.alarma.parar()
                    v.alarma = None
            if v is j.veh:
                continue
            d = v.dist(px, py)
            if v.ia in ("aparcado", None):
                if v.sirena:
                    v.sirena.mover(v.x, v.y)
                continue
            if v.ia == "barco":
                tx, ty = v.destino
                if math.hypot(tx - v.x, ty - v.y) < 30:
                    v.destino = self.mundo.punto_libre(random.uniform(0, self.mundo.ancho), random.uniform(0, self.mundo.alto))
                desv = M.norm180(M.rumbo_a(tx - v.x, ty - v.y) - v.rumbo)
                v.rumbo = (v.rumbo + max(-30 * dt, min(30 * dt, desv))) % 360
                v.vel += max(-2 * dt, min(2 * dt, v.vel_obj - v.vel))
                rad = math.radians(v.rumbo)
                nx, ny = v.x + math.sin(rad) * v.vel * dt, v.y + math.cos(rad) * v.vel * dt
                if self.mundo.transitable(nx, ny):
                    v.x, v.y = nx, ny
                else:
                    v.rumbo = (v.rumbo + 90) % 360
                if d < 220:
                    if v.canal is None:
                        v.canal = self.son(v.modelo["motor"], bucle=True, xy=(v.x, v.y), ref=10, maxd=220, vol=0.8)
                    v.canal.mover(v.x, v.y)
                    v.canal.tono(v.modelo["tono"] * (0.7 + v.vel / 20.0))
                elif v.canal:
                    v.canal.parar()
                    v.canal = None
                continue
            obj = v.vel_obj
            decidir = self._decidir_trafico
            if v.ardiendo >= 0:
                obj = 0.0
            elif v.ia == "trafico":
                if self._obstaculo(v) or self._semaforo_rojo(v):
                    obj = 0.0
                    v.t_parado += dt
                    if v.t_parado > 3 and self.t > v.t_claxon and d < 30 and self._obstaculo(v, 9):
                        v.t_claxon = self.t + random.uniform(3, 6)
                        self.son(v.modelo.get("claxon", "claxon"), xy=(v.x, v.y), ref=8)
                else:
                    v.t_parado = 0.0
            elif v.ia == "huida":
                decidir = self._decidir_huida
                obj = v.vel_obj * (0.6 + 0.4 * max(0.0, v.salud / v.salud_max))
                if d > 160:
                    obj *= 0.55        # espera un poco al jugador para que la persecución no se pierda
            elif v.ia == "policia":
                obj, decidir = self._ia_patrulla(v, d, dt)
            v.vel += max(-v.modelo["freno"] * dt, min(v.modelo["acel"] * dt, obj - v.vel))
            if v.vel > 0.05:
                self._mover_via(v, dt, 0.0, decidir)
            if d < 100:
                self._motor(v, False)
                v.canal.mover(v.x, v.y)
                v.canal.tono(v.modelo["tono"] * (0.6 + 1.3 * abs(v.vel) / v.modelo["vel_max"]))
            elif v.canal:
                v.canal.parar()
                v.canal = None
            if v.sirena:
                v.sirena.mover(v.x, v.y)
            # atropello del jugador a pie
            if not j.veh and v.vel > 3 and d < 2.4 and self.t > v.t_choque:
                v.t_choque = self.t + 1.5
                self.son("golpe")
                self.danar_jugador(v.vel * 2.2, (v.x, v.y))
                self.decir("¡Te ha atropellado un vehículo!")
                v.vel *= 0.3

    def _ia_patrulla(self, v, d, dt):
        j = self.j
        if j.estrellas == 0:
            if v.sirena:
                v.sirena.parar()
                v.sirena = None
            if v.desplegado:
                return 0.0, self._decidir_trafico
            return 11.0, self._decidir_trafico
        if v.sirena is None:
            # Con varias patrullas, cada sirena suena más floja: juntas no deben tapar ni saturar todo lo demás.
            otras = sum(1 for o in self.vehiculos if o is not v and o.sirena is not None)
            v.sirena = self.son("sirena", bucle=True, xy=(v.x, v.y), ref=14, maxd=260, vol=0.8 / (1 + 0.6 * otras))
        if v.desplegado:
            return 0.0, self._decidir_policia
        vel_j = abs(j.veh.vel) if j.veh else 0.0
        px, py = self.pos()
        if d < 14 and vel_j < 4:
            if v.vel < 1.0:
                v.desplegado = True
                v.ocupado = False
                for k in range(2):
                    x, y = self.mundo.punto_libre(v.x + random.uniform(-3, 3), v.y + random.uniform(-3, 3))
                    p = Persona("policia", x, y)
                    p.salud = 80
                    p.hostil = True
                    p.arma = "subfusil" if j.estrellas >= 4 else "pistola"
                    p.estado = "ataca"
                    p.coche = v
                    self.personas.append(p)
                self.son("puerta_coche", xy=(v.x, v.y))
            return 0.0, self._decidir_policia
        dx, dy = M.DIRS[v.dir]
        a = (px - v.x) * dx + (py - v.y) * dy
        lat = abs((px - v.x) * dy - (py - v.y) * dx)
        if a < -15 and lat < 20 and self.t > v.t_giro:
            v.t_giro = self.t + 3
            v.dir = (v.dir + 2) % 4
        if j.veh and d < 4.6 and self.t > v.t_choque and not j.veh.modelo.get("vuela"):
            v.t_choque = self.t + 2.5
            self.son("choque_leve")
            self.danar_vehiculo(j.veh, 7)
            j.veh.vel *= 0.75
            v.vel *= 0.5
        lim = v.modelo["vel_max"] * (0.62 + 0.06 * j.estrellas)
        if d < 30:
            lim = min(lim, max(8.0, vel_j + 3))
        return lim, self._decidir_policia

    def crear_vehiculo(self, modelo_id, x, y, d, ia="aparcado", nombre=None, tag=None):
        v = Vehiculo(self.modelos.get(modelo_id, self.modelos["utilitario"]), x, y, d, ia)
        if nombre:
            v.nombre = nombre
        v.tag = tag
        self.vehiculos.append(v)
        return v
