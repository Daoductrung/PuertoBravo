"""La gente de la calle, común: los peatones los lleva el servidor y son los mismos para todos los jugadores.

Andan por la acera alrededor de su manzana, igual que en el juego. Si alguien dispara o grita cerca, salen corriendo;
si se les atraca, también, y ya no llevan nada encima para el siguiente; si se les tumba, caen para todos.
Solo hay gente donde hay jugadores, y menos de noche y cuando llueve.
"""
import math

from .trafico import zonas_con_gente

B = 90.0
LADO = B - 15.0


def posicion(bi, bj, u):
    """Dónde está en la acera quien lleva recorridos u metros alrededor de la manzana (bi, bj). Lo mismo que hace el juego."""
    u = u % (4 * LADO)
    x0, y0 = bi * B + 7.5, bj * B + 7.5
    k = int(u // LADO)
    r = u - k * LADO
    if k == 0:
        return x0 + r, y0
    if k == 1:
        return x0 + LADO, y0 + r
    if k == 2:
        return x0 + LADO - r, y0 + LADO
    return x0, y0 + LADO - r


ZONA = 260.0                      # lado de cada zona, en metros: lo que alcanza a oír un jugador a pie a cada lado


class Peatones:
    """Mixin del servidor."""

    def peatones_iniciar(self):
        self.peatones = {}
        self._np = 0

    def _pe_activo(self):
        return str(self.cfg["peatones"]).strip().lower() in ("si", "sí", "1", "true", "yes")

    def _pe_nuevo(self, mapa, cerca_de):
        m = self.mundo["mapas"][mapa]
        nx, ny = int(m.get("nx", 0)), int(m.get("ny", 0))
        if nx < 2 or ny < 2:
            return None
        bi = max(0, min(nx - 2, int(cerca_de.x // B) + self.rng.choice([-1, 0, 0, 1])))
        bj = max(0, min(ny - 2, int(cerca_de.y // B) + self.rng.choice([-1, 0, 0, 1])))
        u = self.rng.uniform(0, 4 * LADO)
        x, y = posicion(bi, bj, u)
        if not (28 < math.hypot(x - cerca_de.x, y - cerca_de.y) < 110):       # ni encima de nadie, ni donde no lo oye nadie
            return None
        self._np += 1
        p = {"id": self._np, "m": mapa, "bi": bi, "bj": bj, "u": u, "s": self.rng.choice([-1, 1]), "vel": self.rng.uniform(1.1, 1.7),
             "huye": 0.0, "salud": 50.0, "atracado": False}
        self.peatones[p["id"]] = p
        return p

    def peatones_pensar(self):
        """Una vez por segundo: cuánta gente hay en cada localidad con jugadores, y fuera los que ya no ve nadie."""
        if not self._pe_activo():
            if self.peatones:
                self.peatones.clear()
            return
        gente = {}
        for j in self.jugadores.values():
            if j.dentro and not j.bot and j.mapa is not None:
                gente.setdefault(j.mapa, []).append(j)
        for ident, p in list(self.peatones.items()):
            x, y = posicion(p["bi"], p["bj"], p["u"])
            if p["m"] not in gente or all(math.hypot(o.x - x, o.y - y) > 240 for o in gente[p["m"]]):
                del self.peatones[ident]
        noche = self.reloj < 7 * 60 or self.reloj >= 22 * 60
        tope = int(self.cfg["peatones_max"])
        for mapa, lista in gente.items():
            n = int(self.mundo["mapas"][mapa].get("peatones", 0))
            quiere = min(tope, max(1, n // 3) if noche else n) if n else 0
            if self.lluvia:
                quiere = max(1, quiere // 2) if quiere else 0
            zonas = zonas_con_gente(lista, ZONA)                # como el tráfico: tantos por cada zona con jugadores
            base = quiere
            quiere = base * len(zonas)
            total = int(self.cfg.get("peatones_total", 0) or 0)
            if total > 0:
                quiere = min(quiere, max(base, total))
            hay = sum(1 for p in self.peatones.values() if p["m"] == mapa)
            if hay < quiere:
                if len(zonas) == 1:
                    self._pe_nuevo(mapa, self.rng.choice(lista))
                else:
                    cuenta = {}
                    for p in self.peatones.values():
                        if p["m"] == mapa:
                            x, y = posicion(p["bi"], p["bj"], p["u"])
                            z = (int(x // ZONA), int(y // ZONA))
                            cuenta[z] = cuenta.get(z, 0) + 1
                    for z in sorted(zonas, key=lambda z: cuenta.get(z, 0))[:max(1, min(quiere - hay, len(zonas)))]:
                        self._pe_nuevo(mapa, self.rng.choice(zonas[z]))

    def peatones_mover(self, dt):
        for p in self.peatones.values():
            vel = p["vel"]
            if p["huye"] > 0:
                p["huye"] -= dt
                vel = 4.6
            p["u"] = (p["u"] + p["s"] * vel * dt) % (4 * LADO)

    def peatones_susto(self, mapa, x, y, radio, segundos=10.0):
        """Un disparo, un grito, una explosión: los que están cerca salen corriendo hacia el lado contrario."""
        for p in self.peatones.values():
            if p["m"] != mapa:
                continue
            px, py = posicion(p["bi"], p["bj"], p["u"])
            if math.hypot(px - x, py - y) > radio:
                continue
            self._pe_huir(p, x, y, segundos)

    def _pe_huir(self, p, x, y, segundos=10.0):
        mejor = None
        for s in (-1, 1):                                     # por el lado de la acera que le aleja
            qx, qy = posicion(p["bi"], p["bj"], p["u"] + s * 3)
            d = math.hypot(qx - x, qy - y)
            if mejor is None or d > mejor[0]:
                mejor = (d, s)
        p["s"], p["huye"] = mejor[1], segundos

    def peatones_para(self, j):
        out = []
        for p in self.peatones.values():
            if p["m"] != j.mapa:
                continue
            x, y = posicion(p["bi"], p["bj"], p["u"])
            if abs(x - j.x) < 130 and abs(y - j.y) < 130:
                out.append([p["id"], p["bi"], p["bj"], round(p["u"], 1), p["s"], 1 if p["huye"] > 0 else 0, round(p["vel"], 2), 1 if p["atracado"] else 0])
        return out

    def _m_pe_dano(self, j, m):
        """Un jugador le ha dado a un peatón: si cae, cae para todos; si no, sale corriendo."""
        p = self.peatones.get(m.get("id"))
        if p is None or p["m"] != j.mapa:
            return
        try:
            n = max(0.0, min(500.0, float(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        p["salud"] -= n
        if m.get("cae") or p["salud"] <= 0:
            x, y = posicion(p["bi"], p["bj"], p["u"])
            del self.peatones[p["id"]]
            self._a_todos({"t": "pe_cae", "id": p["id"], "x": round(x, 1), "y": round(y, 1)}, menos=j, mapa=p["m"])
            self.peatones_susto(p["m"], x, y, 30, 12.0)
        else:
            self._pe_huir(p, j.x, j.y, 12.0)

    def _m_pe_atraco(self, j, m):
        p = self.peatones.get(m.get("id"))
        if p is not None and p["m"] == j.mapa:
            p["atracado"] = True
            self._pe_huir(p, j.x, j.y, 14.0)
