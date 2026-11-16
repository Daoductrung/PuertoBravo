"""El tráfico común: los coches que circulan por las calles los lleva el servidor, y son los mismos para todos.

Van por su carril, de cruce en cruce, respetan los semáforos (que también son los mismos para todos), frenan si
tienen delante a un jugador o a otro coche, y en cada cruce deciden al azar por dónde siguen. Solo hay tráfico donde
hay jugadores. A un coche de estos se le puede parar poniéndose delante, sacar al conductor y llevárselo: desde ese
momento es un vehículo más de los jugadores. También se le puede destrozar.
"""
import math

B = 90.0            # separación entre calles, la misma del juego
CARRIL = 3.0
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]       # norte, este, sur, oeste


class Trafico:
    """Mixin del servidor."""

    def trafico_iniciar(self):
        self.trafico = {}
        self._nt = 0
        self.t_luces = 0.0

    def _tr_activo(self):
        return str(self.cfg["trafico"]).strip().lower() in ("si", "sí", "1", "true", "yes")

    @staticmethod
    def tr_pos(c):
        dx, dy = DIRS[c["d"]]
        if dx == 0:
            return c["i"] * B + CARRIL * (1 if c["d"] == 0 else -1), c["j"] * B + dy * c["s"], c["d"] * 90.0
        return c["i"] * B + dx * c["s"], c["j"] * B + CARRIL * (-1 if c["d"] == 1 else 1), c["d"] * 90.0

    def _tr_validas(self, c, nx, ny):
        out = []
        for d in range(4):
            if 0 <= c["i"] + DIRS[d][0] < nx and 0 <= c["j"] + DIRS[d][1] < ny:
                out.append(d)
        return out

    def _tr_elegir(self, c, nx, ny):
        validas = self._tr_validas(c, nx, ny)
        sin_vuelta = [d for d in validas if d != (c["d"] + 2) % 4] or validas
        pesos = [3 if d == c["d"] else 1 for d in sin_vuelta]
        c["d"] = self.rng.choices(sin_vuelta, pesos)[0]

    def _tr_nuevo(self, mapa, cerca_de=None):
        m = self.mundo["mapas"][mapa]
        nx, ny = int(m.get("nx", 0)), int(m.get("ny", 0))
        coches = [x for x in m.get("coches", []) if x in self.mundo["modelos"]] or ["utilitario"]
        if nx < 2 or ny < 2:
            return None
        for _ in range(12):
            if cerca_de is not None:                          # a un par de manzanas de alguien, no encima
                i = max(0, min(nx - 1, int(round(cerca_de.x / B)) + self.rng.choice([-3, -2, 2, 3])))
                j = max(0, min(ny - 1, int(round(cerca_de.y / B)) + self.rng.choice([-2, -1, 0, 1, 2])))
            else:
                i, j = self.rng.randrange(nx), self.rng.randrange(ny)
            c = {"m": mapa, "i": i, "j": j, "d": 0, "s": self.rng.uniform(20, 60), "vel": 0.0, "vel_obj": self.rng.uniform(8, 12),
                 "modelo": self.rng.choice(coches)}
            validas = self._tr_validas(c, nx, ny)
            if not validas:
                continue
            c["d"] = self.rng.choice(validas)
            x, y, _ = self.tr_pos(c)
            if all(math.hypot(o.x - x, o.y - y) > 60 for o in self.jugadores.values() if o.dentro and o.mapa == mapa):
                self._nt += 1
                c["id"] = self._nt
                c["salud"] = float(self.mundo["modelos"][c["modelo"]]["salud"])
                self.trafico[c["id"]] = c
                return c
        return None

    def trafico_pensar(self):
        """Una vez por segundo: cuántos coches hay en cada localidad con gente, y fuera los que ya no ve nadie."""
        if not self._tr_activo():
            if self.trafico:
                self.trafico.clear()
            return
        gente = {}
        for j in self.jugadores.values():
            if j.dentro and not j.bot and j.mapa is not None:
                gente.setdefault(j.mapa, []).append(j)
        for ident, c in list(self.trafico.items()):
            x, y, _ = self.tr_pos(c)
            if c["m"] not in gente or all(math.hypot(o.x - x, o.y - y) > 520 for o in gente[c["m"]]):
                del self.trafico[ident]
        tope = int(self.cfg["trafico_max"])
        for mapa, lista in gente.items():
            m = self.mundo["mapas"][mapa]
            quiere = min(tope, int(m.get("trafico", 0)))
            hay = sum(1 for c in self.trafico.values() if c["m"] == mapa)
            if hay < quiere:
                self._tr_nuevo(mapa, self.rng.choice(lista))

    def trafico_mover(self, dt):
        self.t_luces += dt
        if not self.trafico:
            return
        estorbos = {}
        for o in self.jugadores.values():
            if (o.dentro or o.bot) and o.mapa is not None:
                estorbos.setdefault(o.mapa, []).append((o.x, o.y))
        for c in self.trafico.values():
            x, y, _ = self.tr_pos(c)
            estorbos.setdefault(c["m"], []).append((x, y))
        fase = int(self.t_luces // 14)
        for c in self.trafico.values():
            m = self.mundo["mapas"][c["m"]]
            nx, ny = int(m.get("nx", 0)), int(m.get("ny", 0))
            dx, dy = DIRS[c["d"]]
            x, y, _ = self.tr_pos(c)
            obj = c["vel_obj"]
            falta = B - c["s"]
            ni, nj = c["i"] + dx, c["j"] + dy
            if 7.5 < falta < 17:                               # ante el cruce: mira el semáforo
                verde_vertical = (fase + ni + nj) % 2 == 0
                if (dx == 0) != verde_vertical:
                    obj = 0.0
            for ox, oy in estorbos.get(c["m"], ()):
                delante = (ox - x) * dx + (oy - y) * dy
                lado = abs((ox - x) * dy - (oy - y) * dx)
                if 0.5 < delante < 13 and lado < 2.6:          # alguien o algo en su carril, justo delante
                    obj = 0.0
                    break
            c["vel"] += max(-14.0 * dt, min(5.0 * dt, obj - c["vel"]))
            c["vel"] = max(0.0, c["vel"])
            c["s"] += c["vel"] * dt
            if c["s"] >= B:
                c["s"] -= B
                c["i"], c["j"] = ni, nj
                self._tr_elegir(c, nx, ny)

    def trafico_para(self, j):
        """Los coches que tiene cerca un jugador: los que su juego va a hacer sonar."""
        out = []
        for c in self.trafico.values():
            if c["m"] != j.mapa:
                continue
            x, y, rumbo = self.tr_pos(c)
            if abs(x - j.x) < 320 and abs(y - j.y) < 320:
                out.append([c["id"], c["modelo"], round(x, 1), round(y, 1), int(rumbo), round(c["vel"], 1)])
        return out

    def _m_tr_robar(self, j, m):
        """Sacar al conductor de un coche del tráfico y llevárselo: tiene que estar casi parado y al lado."""
        c = self.trafico.get(m.get("id"))
        if c is None or c["m"] != j.mapa or j.veh:
            return self._enviar(j, {"t": "veh_no", "id": m.get("id"), "motivo": "Ese vehículo ya no está."})
        x, y, rumbo = self.tr_pos(c)
        if math.hypot(x - j.x, y - j.y) > 9:
            return self._enviar(j, {"t": "veh_no", "id": c["id"], "motivo": "Estás demasiado lejos."})
        if c["vel"] > 6:
            return self._enviar(j, {"t": "veh_no", "id": c["id"], "motivo": "Va demasiado rápido para abrir la puerta."})
        del self.trafico[c["id"]]
        if j.vid is not None and j.vid in self.vehiculos:
            self._soltar_vehiculo(j, self.vehiculos[j.vid])
        self._nv += 1
        v = {"id": self._nv, "modelo": c["modelo"], "nombre": self.mundo["modelos"][c["modelo"]]["nombre"], "m": j.mapa, "x": x, "y": y, "r": rumbo,
             "salud": c["salud"], "por": j.id, "dueno": j.cuenta, "t": self.ahora(), "mejoras": {}}
        self.vehiculos[v["id"]] = v
        j.vid = v["id"]
        import time
        j.t_vid = time.monotonic()
        self._enviar(j, {"t": "veh_ok", "id": v["id"], "v": self._veh_publico(v), "robado": True, "tr": c["id"]})
        self._a_todos({"t": "veh_ocupado", "id": v["id"], "por": j.id, "v": self._veh_publico(v), "tr": c["id"]}, menos=j)

    def _m_tr_dano(self, j, m):
        c = self.trafico.get(m.get("id"))
        if c is None or c["m"] != j.mapa:
            return
        try:
            n = max(0.0, min(500.0, float(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        c["salud"] -= n
        c["vel"] *= 0.5
        if c["salud"] <= 0:
            x, y, _ = self.tr_pos(c)
            del self.trafico[c["id"]]
            self._a_todos({"t": "tr_revienta", "id": c["id"], "x": round(x, 1), "y": round(y, 1), "m": c["m"]}, mapa=c["m"])
