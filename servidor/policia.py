"""La policía, común: la búsqueda, la persecución y la detención las lleva el servidor, y son las mismas para todos.

El juego de cada uno cuenta sus delitos; el servidor lleva la cuenta y decide el nivel de búsqueda. Manda patrullas
por las calles a por el buscado, que al alcanzarle paran y sueltan a dos agentes. Los agentes van a pie: con el
nivel más bajo intentan detenerle, y con más, disparan. Cualquier jugador ve y oye a esas patrullas y a esos agentes
donde están, y cualquiera puede herirlos. Quien se aleja lo bastante de todos ellos, los despista.
"""
import math
import time

from .trafico import B, DIRS

# Los mismos números que usa el juego cuando se juega solo.
UMBRAL = [1, 4, 8, 13, 20]                              # puntos de delito con los que empieza cada nivel de búsqueda
PATRULLAS = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4}              # cuántas patrullas persiguen como mucho con cada nivel
RITMO = {1: 9.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0}        # cada cuántos segundos sale una nueva
ACERA = 9.0
MEMORIA = 600.0                                         # segundos que la policía se acuerda de quien salió buscado


class Policia:
    """Mixin del servidor."""

    def policia_iniciar(self):
        self.agentes = {}
        self._na = 0
        self.buscados_fuera = {}                        # cuenta: (puntos, momento). Salir no borra la búsqueda
        self._abiertos = {}

    def _po_activo(self):
        return str(self.cfg["policia"]).strip().lower() in ("si", "sí", "1", "true", "yes")

    # ------------------------------------------------------------- la búsqueda
    def _po_nivel(self, j, motivo=None):
        n = sum(1 for u in UMBRAL if j.puntos >= u)
        if n == j.estrellas:
            return
        if j.estrellas == 0:
            j.t_poli = 3.0 if j.veh else 5.0            # la primera patrulla tarda en salir: da tiempo a reaccionar
            j.poli_enviada = False
            j.t_evasion = 0.0
        j.estrellas = n
        self._enviar(j, {"t": "nivel_busqueda", "es": n, "pu": round(j.puntos, 1), "motivo": motivo})

    def po_limpiar(self, j, motivo, quitar=False):
        """Deja de estar buscado. Con quitar, los que iban a por él desaparecen ya: le han cogido o ha caído."""
        j.puntos, j.t_evasion, j.detenido = 0.0, 0.0, 0.0
        if j.estrellas:
            j.estrellas = 0
            self._enviar(j, {"t": "nivel_busqueda", "es": 0, "pu": 0, "motivo": motivo})
        self._po_soltar(j.id, quitar)

    def _po_soltar(self, ident, quitar=False):
        ahora = time.monotonic()
        for c in [c for c in self.trafico.values() if c.get("obj") == ident]:
            if quitar:
                del self.trafico[c["id"]]
            else:
                c["obj"], c["sobra"] = None, ahora
        for a in [a for a in self.agentes.values() if a["obj"] == ident]:
            if quitar:
                del self.agentes[a["id"]]
            else:
                a["obj"], a["t_fuera"] = None, ahora

    def po_sale(self, j):
        """Se va del servidor: si iba buscado, la policía se acuerda de él un rato."""
        if j.estrellas and j.cuenta is not None and self._po_activo():
            self.buscados_fuera[j.cuenta] = (j.puntos, time.monotonic())
        self._po_soltar(j.id)

    def po_entra(self, j):
        puntos, cuando = self.buscados_fuera.pop(j.cuenta, (0.0, 0.0))
        if puntos and time.monotonic() - cuando < MEMORIA and self._po_activo():
            j.puntos = puntos
            self._po_nivel(j, "vuelve")

    def _m_delito(self, j, m):
        """El juego de un jugador cuenta un delito que alguien ha visto."""
        if not self._po_activo() or j.bot or j.mapa is None:
            return
        try:
            n = max(0.0, min(30.0, float(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        j.puntos = min(60.0, j.puntos + n)
        self._po_nivel(j, "delito")

    def _m_busqueda(self, j, m):
        """El juego pone un nivel de búsqueda (reventar un furgón blindado) o la da por terminada (pintar el coche,
        pagar la multa, acabar en comisaría o en el hospital)."""
        if not self._po_activo() or j.bot:
            return
        try:
            nivel = int(m.get("nivel", 0))
        except (TypeError, ValueError):
            return
        if nivel <= 0:
            self.po_limpiar(j, "limpia", quitar=bool(m.get("fin")))
        else:
            j.puntos = max(j.puntos, float(UMBRAL[max(0, min(4, nivel - 1))]))
            self._po_nivel(j, "delito")

    # ---------------------------------------------------------- una vez por segundo
    def policia_pensar(self):
        if not self._po_activo():
            if self.agentes:
                self.agentes.clear()
            return
        ahora = time.monotonic()
        dentro = [j for j in self.jugadores.values() if j.dentro and not j.bot and j.mapa is not None]
        for j in dentro:
            n = j.estrellas
            if n == 0:
                continue
            if j.detenido and ahora > j.detenido:
                j.detenido = 0.0
            r_p, r_v = (70.0, 80.0) if j.veh else (38.0, 45.0)      # a pie se le ve menos que en un coche
            cerca = any(a["m"] == j.mapa and math.hypot(a["x"] - j.x, a["y"] - j.y) < r_p for a in self.agentes.values())
            if not cerca:
                for c in self.trafico.values():
                    if c["m"] == j.mapa and c.get("poli"):
                        x, y, _ = self.tr_pos(c)
                        if math.hypot(x - j.x, y - j.y) < r_v:
                            cerca = True
                            break
            if cerca:
                j.t_evasion = 0.0
            else:
                if j.poli_enviada:
                    j.t_evasion += 1.0                              # solo cuenta cuando ya hay alguien buscándole
                if j.t_evasion >= ((9 + 4 * n) if j.veh else (7 + 3 * n)):
                    self.po_limpiar(j, "perdida")
                    continue
            j.t_poli -= 1.0
            if j.t_poli <= 0:
                j.t_poli = RITMO.get(n, 5.0)
                total = sum(1 for c in self.trafico.values() if c.get("obj") == j.id)
                if total < PATRULLAS.get(n, 4) and j.t_evasion < 6 and int(self.mundo["mapas"][j.mapa].get("policia", 1)):
                    self._po_llegar(j)
                j.poli_enviada = True
        # los agentes que se han quedado sin nadie a quien perseguir: o encuentran a otro buscado, o se van
        for a in list(self.agentes.values()):
            gente = [o for o in dentro if o.mapa == a["m"]]
            if not gente or all(math.hypot(o.x - a["x"], o.y - a["y"]) > 300 for o in gente):
                del self.agentes[a["id"]]
                continue
            if a["obj"] is not None:
                continue
            otros = [o for o in gente if o.estrellas > 0 and math.hypot(o.x - a["x"], o.y - a["y"]) < 60]
            if otros:
                a["obj"] = min(otros, key=lambda o: math.hypot(o.x - a["x"], o.y - a["y"])).id
            elif ahora - a.get("t_fuera", ahora) > 12 or all(math.hypot(o.x - a["x"], o.y - a["y"]) > 45 for o in gente):
                del self.agentes[a["id"]]

    def _po_llegar(self, j):
        """Sale una patrulla a por él: aparece a un par de manzanas, en su misma calle, y viene de frente."""
        m = self.mundo["mapas"][j.mapa]
        nx, ny = int(m.get("nx", 0)), int(m.get("ny", 0))
        if nx < 2 or ny < 2 or "patrulla" not in self.mundo["modelos"]:
            return None
        for _ in range(8):
            dist = self.rng.uniform(150, 230) * self.rng.choice([-1, 1])
            if self.rng.random() < 0.5:
                jj = max(0, min(ny - 1, int(round(j.y / B))))
                vx = j.x + dist
                if not (5 < vx < (nx - 1) * B - 5):
                    continue
                if dist > 0:
                    d, i = 3, int(math.ceil(vx / B))
                    s = i * B - vx
                else:
                    d, i = 1, int(math.floor(vx / B))
                    s = vx - i * B
            else:
                i = max(0, min(nx - 1, int(round(j.x / B))))
                vy = j.y + dist
                if not (5 < vy < (ny - 1) * B - 5):
                    continue
                if dist > 0:
                    d, jj = 2, int(math.ceil(vy / B))
                    s = jj * B - vy
                else:
                    d, jj = 0, int(math.floor(vy / B))
                    s = vy - jj * B
            if not (0 <= i < nx and 0 <= jj < ny and 0 <= i + DIRS[d][0] < nx and 0 <= jj + DIRS[d][1] < ny):
                continue
            self._nt += 1
            c = {"id": self._nt, "m": j.mapa, "i": i, "j": jj, "d": d, "s": s, "vel": 12.0, "vel_obj": 11.0, "modelo": "patrulla", "poli": True,
                 "salud": float(self.mundo["modelos"]["patrulla"]["salud"]), "obj": j.id, "t_giro": 0.0, "t_choque": 0.0}
            self.trafico[c["id"]] = c
            return c
        return None

    # --------------------------------------------------------- las patrullas
    def po_coche(self, c, dt):
        """Mueve una patrulla que persigue a alguien, o que ya ha soltado a sus agentes. Falso si solo está rondando."""
        if c.get("desp"):
            c["vel"] = 0.0
            o = self.jugadores.get(c.get("obj"))
            if o is None or not o.dentro or o.mapa != c["m"] or o.estrellas == 0 or o.detenido:
                return True
            x, y, _ = self.tr_pos(c)
            if math.hypot(o.x - x, o.y - y) > 70:                # se les escapa: los agentes que siguen junto al coche se suben y van tras él
                suyos = [a for a in self.agentes.values() if a.get("coche") == c["id"] and math.hypot(a["x"] - x, a["y"] - y) < 40]
                if suyos:
                    for a in suyos:
                        del self.agentes[a["id"]]
                    c["desp"] = False
            return True
        if c.get("obj") is None:
            return False
        o = self.jugadores.get(c["obj"])
        if o is None or not o.dentro or o.mapa != c["m"] or o.estrellas == 0:
            c["obj"], c["sobra"] = None, time.monotonic()
            return False
        ahora = self.t_luces                                     # el reloj de las calles: avanza con el tráfico
        modelo = self.mundo["modelos"][c["modelo"]]
        x, y, _ = self.tr_pos(c)
        d = math.hypot(o.x - x, o.y - y)
        vel_j = o.vel if o.veh else 0.0
        dx, dy = DIRS[c["d"]]
        if o.detenido:
            obj = 0.0
        elif d < 14 and vel_j < 4:
            obj = 0.0
            if c["vel"] < 1.0:                                   # le tiene al lado y parado: se bajan
                self._po_desplegar(c, o)
                return True
        else:
            delante = (o.x - x) * dx + (o.y - y) * dy
            lado = abs((o.x - x) * dy - (o.y - y) * dx)
            if delante < -15 and lado < 20 and ahora > c.get("t_giro", 0.0):      # lo tiene detrás: da la vuelta
                c["t_giro"] = ahora + 3
                c["i"], c["j"], c["s"], c["d"] = c["i"] + dx, c["j"] + dy, B - c["s"], (c["d"] + 2) % 4
                dx, dy = DIRS[c["d"]]
            vuela = bool(self.mundo["modelos"].get(o.veh, {}).get("vuela")) if o.veh else False
            if o.veh and d < 4.6 and ahora > c.get("t_choque", 0.0) and not vuela:   # le embiste
                c["t_choque"] = ahora + 2.5
                c["vel"] *= 0.5
                self._enviar(o, {"t": "po_embiste", "n": 7, "x": round(x, 1), "y": round(y, 1)})
            obj = float(modelo.get("vel_max", 33)) * (0.62 + 0.06 * o.estrellas)
            if d < 30:
                obj = min(obj, max(8.0, vel_j + 3))
        c["vel"] += max(-float(modelo.get("freno", 17)) * dt, min(float(modelo.get("acel", 9.5)) * dt, obj - c["vel"]))
        c["vel"] = max(0.0, c["vel"])
        c["s"] += c["vel"] * dt
        if c["s"] >= B:
            m = self.mundo["mapas"][c["m"]]
            nx, ny = int(m.get("nx", 0)), int(m.get("ny", 0))
            c["s"] -= B
            c["i"], c["j"] = c["i"] + dx, c["j"] + dy
            validas = self._tr_validas(c, nx, ny)
            ops = [q for q in (c["d"], (c["d"] + 1) % 4, (c["d"] - 1) % 4) if q in validas] or [(c["d"] + 2) % 4]
            c["d"] = min(ops, key=lambda q: abs((c["i"] + DIRS[q][0]) * B - o.x) + abs((c["j"] + DIRS[q][1]) * B - o.y) + self.rng.uniform(0, 20))
        return True

    def _po_desplegar(self, c, o):
        c["desp"], c["vel"] = True, 0.0
        x, y, _ = self.tr_pos(c)
        arma = "subfusil" if o.estrellas >= 4 and "subfusil" in self.mundo["armas"] else "pistola"
        for _ in range(2):
            ax, ay = x + self.rng.uniform(-3, 3), y + self.rng.uniform(-3, 3)
            if not self._po_transitable(c["m"], ax, ay):
                ax, ay = x, y
            self._na += 1
            self.agentes[self._na] = {"id": self._na, "m": c["m"], "x": ax, "y": ay, "obj": o.id, "salud": 80.0, "arma": arma,
                                      "t_disparo": 0.6 + self.rng.uniform(0, 0.6), "t_arresto": 0.0, "amart": False, "coche": c["id"]}

    # ------------------------------------------------------------ los agentes
    def _po_transitable(self, mapa, x, y):
        """Calzada, acera o una manzana abierta (un parque, una plaza). Lo mismo que mira el juego."""
        m = self.mundo["mapas"][mapa]
        nx, ny = int(m.get("nx", 0)), int(m.get("ny", 0))
        if nx < 2 or ny < 2:
            return True
        if x < -ACERA or y < -ACERA or x > (nx - 1) * B + ACERA or y > (ny - 1) * B + ACERA:
            return False
        if abs(x - max(0, min(nx - 1, int(round(x / B)))) * B) <= ACERA or abs(y - max(0, min(ny - 1, int(round(y / B)))) * B) <= ACERA:
            return True
        abiertos = self._abiertos.get(mapa)
        if abiertos is None:
            abiertos = self._abiertos[mapa] = {(int(b[0]), int(b[1])) for b in m.get("abiertos", []) if isinstance(b, list) and len(b) == 2}
        return (max(0, min(nx - 2, int(x // B))), max(0, min(ny - 2, int(y // B)))) in abiertos

    def _po_andar(self, a, tx, ty, vel, dt):
        """Un paso hacia su objetivo. Si se lo corta una manzana, la rodea por la esquina que más le acerca."""
        m, x, y = a["m"], a["x"], a["y"]
        paso = vel * dt
        via = a.get("via")
        if via is not None:
            if math.hypot(via[0] - x, via[1] - y) < 2.5 or math.hypot(tx - via[2], ty - via[3]) > 25:
                via = a["via"] = None                             # ha llegado a la esquina, o el otro ya está en otra parte
            else:
                d = math.hypot(via[0] - x, via[1] - y)
                a["x"], a["y"] = x + (via[0] - x) / d * paso, y + (via[1] - y) / d * paso
                return
        dx, dy = tx - x, ty - y
        d = math.hypot(dx, dy)
        if d < 0.1:
            return
        nx, ny = x + dx / d * paso, y + dy / d * paso
        if self._po_transitable(m, nx, ny):
            a["x"], a["y"] = nx, ny
            return
        mapa = self.mundo["mapas"][m]
        cx, cy = int(mapa.get("nx", 0)), int(mapa.get("ny", 0))
        i, j = max(0, min(cx - 1, int(round(x / B)))), max(0, min(cy - 1, int(round(y / B))))
        esquinas = []
        if abs(x - i * B) <= ACERA:                               # va por una avenida: las dos esquinas de su tramo
            k = max(0, min(cy - 2, int(y // B)))
            esquinas += [(i * B, k * B), (i * B, (k + 1) * B)]
        if abs(y - j * B) <= ACERA:                               # va por una calle
            k = max(0, min(cx - 2, int(x // B)))
            esquinas += [(k * B, j * B), ((k + 1) * B, j * B)]
        esquinas = [e for e in esquinas if math.hypot(e[0] - x, e[1] - y) >= 2.5]
        if esquinas:
            e = min(esquinas, key=lambda e: math.hypot(e[0] - x, e[1] - y) + abs(tx - e[0]) + abs(ty - e[1]))
            a["via"] = (e[0], e[1], tx, ty)
            return
        if abs(dx) > 0.2 and self._po_transitable(m, x + math.copysign(paso, dx), y):      # en un parque, pegado a una tapia
            a["x"] = x + math.copysign(paso, dx)
        elif abs(dy) > 0.2 and self._po_transitable(m, x, y + math.copysign(paso, dy)):
            a["y"] = y + math.copysign(paso, dy)

    def policia_mover(self, dt):
        if not self.agentes:
            return
        ahora = time.monotonic()
        for a in list(self.agentes.values()):
            o = self.jugadores.get(a["obj"]) if a["obj"] is not None else None
            if o is None or not o.dentro or o.mapa != a["m"] or o.estrellas == 0:
                if a["obj"] is not None:
                    a["obj"], a["t_fuera"] = None, ahora
                continue
            if o.detenido or o.interior:                         # ya le tienen, o se ha metido en un local: esperan
                continue
            d = math.hypot(o.x - a["x"], o.y - a["y"])
            arma = self.mundo["armas"].get(a["arma"]) or {"dano": 18, "alcance": 30, "cadencia": 0.5}
            alcance = min(float(arma.get("alcance", 30)), 30.0)
            arresto = o.estrellas == 1
            if d > (1.8 if arresto else alcance * 0.6):
                self._po_andar(a, o.x, o.y, 3.7, dt)
            vel_j = o.vel if o.veh else 0.0
            if arresto:                                          # con el nivel más bajo no disparan: le echan el guante
                if d < 3.0 and vel_j < 1.5:
                    a["t_arresto"] += dt
                    if a["t_arresto"] > 1.6:
                        a["t_arresto"] = 0.0
                        o.detenido = ahora + 45
                        self._enviar(o, {"t": "detenido"})
                else:
                    a["t_arresto"] = 0.0
                continue
            if d > alcance:
                a["t_disparo"] = max(a["t_disparo"], 0.6)
                continue
            a["t_disparo"] -= dt
            if a["t_disparo"] < 0.45 and not a["amart"]:         # se le oye amartillar antes de disparar
                a["amart"] = True
                self._enviar(o, {"t": "po_apunta", "k": a["id"], "x": round(a["x"], 1), "y": round(a["y"], 1)})
            if a["t_disparo"] > 0:
                continue
            a["amart"] = False
            auto = bool(arma.get("automatica", a["arma"] == "subfusil"))
            a["t_disparo"] = (0.45 if auto else max(1.2, float(arma.get("cadencia", 0.5)) * 2.5)) + self.rng.uniform(0, 0.6)
            prob = 0.42 * (1.0 - 0.6 * d / alcance)
            if o.agachado:
                prob *= 0.45
            if o.veh:
                prob *= 0.7
            da = round(float(arma.get("dano", 18)) * 0.4, 1) if self.rng.random() < prob else 0
            msg = {"t": "po_disparo", "k": a["id"], "x": round(a["x"], 1), "y": round(a["y"], 1), "arma": a["arma"], "a": o.id, "da": da}
            for q in self.jugadores.values():                    # el tiro lo oyen todos los que están cerca
                if q.dentro and not q.bot and q.mapa == a["m"] and math.hypot(q.x - a["x"], q.y - a["y"]) < 240:
                    self._enviar(q, msg)

    def agentes_para(self, j):
        out = []
        for a in self.agentes.values():
            if a["m"] == j.mapa and abs(a["x"] - j.x) < 200 and abs(a["y"] - j.y) < 200:
                out.append([a["id"], round(a["x"], 1), round(a["y"], 1), a["obj"], a["arma"]])
        return out

    def _m_po_dano(self, j, m):
        """Un jugador, el perseguido u otro cualquiera, le ha dado a un agente: lo que le pase, le pasa para todos."""
        a = self.agentes.get(m.get("id"))
        if a is None or a["m"] != j.mapa:
            return
        try:
            n = max(0.0, min(500.0, float(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        a["salud"] -= n
        if m.get("cae") or a["salud"] <= 0:
            del self.agentes[a["id"]]
            self._a_todos({"t": "po_cae", "id": a["id"], "x": round(a["x"], 1), "y": round(a["y"], 1)}, menos=j, mapa=a["m"])
