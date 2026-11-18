"""Guerra de barrios en la calle (1.7.1). Es un modo opcional, apagado de serie: Opciones, La calle.

Con el modo apagado, los barrios se conquistan y se defienden desde el móvil, como siempre. Con el modo encendido:
- en los barrios de cada banda andan los suyos por la calle (del tipo de enemigo que diga la banda en los datos);
- un barrio se conquista yendo allí: al plantar cara a los suyos empieza la guerra, que son varias oleadas que vienen
  a por ti; tu banda acude a ayudarte, y no hay que salir del barrio;
- cuando una banda ataca un barrio tuyo, lo defiendes entrando en él: las oleadas empiezan al llegar.
En un servidor en línea los barrios son de las bandas de los jugadores y este modo no hace nada.

Los números y las frases salen de los datos (data/datos/vida.json, sección guerra_barrios).
"""
import random
import zlib

from . import gente as G

_AJUSTES = {"miembros_prob": 35, "bajas_para_empezar": 2, "ventana_bajas": 180, "oleadas": 3, "oleada_base": 3, "defensa_oleadas": 2,
            "pausa_min": 8, "pausa_max": 15, "fuera_max": 25, "premio_conquista": 2500, "premio_defensa": 800}
_LISTAS = {
    "frases_empieza": ["¡Has plantado cara a {banda} en su barrio! Empieza la guerra por {barrio}.", "{banda} sale a defender {barrio}: esto ya es una guerra.",
                       "Se corre la voz por {barrio}: {banda} viene a por ti con todo."],
    "frases_defensa": ["Entras en {barrio} y {banda} lo está atacando: ¡defiéndelo!", "{banda} anda por {barrio} como si fuera suyo. Échalos."],
    "frases_gana": ["Los de {banda} que quedan salen corriendo.", "{banda} se retira de {barrio} con el rabo entre las piernas.", "Nadie de {banda} vuelve a asomar por {barrio}."],
    "frases_retirada": ["Te retiras de {barrio}.", "Dejas {barrio} atrás: la pelea se acaba."],
}
AJUSTES = dict(_AJUSTES)
LISTAS = {k: list(v) for k, v in _LISTAS.items()}


def configurar(datos):
    c = next((x for x in datos.get("guerra_barrios", []) if isinstance(x, dict)), {})
    for k, serie in _AJUSTES.items():
        try:
            n = float(c.get(k, serie))
            AJUSTES[k] = n if n > 0 or (n == 0 and k in ("miembros_prob", "premio_conquista", "premio_defensa")) else serie
        except (TypeError, ValueError):
            AJUSTES[k] = serie
    for k, serie in _LISTAS.items():
        v = c.get(k)
        LISTAS[k] = [str(x) for x in v if str(x).strip()] if isinstance(v, list) and any(str(x).strip() for x in v) else list(serie)


def aj(k):
    return AJUSTES[k]


class Guerra:
    """Mixin de Partida."""

    def guerra_iniciar(self):
        self.guerra = None               # la guerra en curso: {"tipo", "barrio", "nombre", "banda", "oleada", "total", "vivos", ...}
        self._bajas_guerra = {}          # barrio -> momentos de las últimas bajas que le has hecho a su banda
        self.t_guerra_enfria = -99.0

    def guerra_activa(self):
        return bool(self.cfg["guerra_calle"]) and not getattr(self, "en_servidor", False)

    def banda_guerra(self, b):
        """Con el modo encendido, todo barrio de ciudad que no sea tuyo es de alguna banda: siempre la misma en cada partida."""
        if not self.guerra_activa() or b["id"] in self.j.territorios:
            return ""
        mapa = next((m for m in self.mapas.values() if any(x is b for x in m.barrios)), None)
        bandas = G.nombres_bandas()
        if mapa is None or mapa.tipo != "ciudad" or not bandas:
            return ""
        return bandas[zlib.crc32(f"{self.j.semilla}:{mapa.id}:{b['id']}".encode("utf-8")) % len(bandas)]

    def miembro_de_barrio(self, b):
        """Quién de una banda anda por la calle en ese barrio: (datos de la banda, tipo de enemigo, probabilidad), o None."""
        if b["id"] in self.j.territorios:
            return None
        bd = G.banda(self.banda_de_barrio(b))
        if not bd:
            return None
        calle = bd.get("callejero")
        if self.guerra_activa() and self.mundo.tipo == "ciudad":
            if calle not in G.TIPOS:
                calle = next(iter(G.tipos_de_banda(bd["nombre"])[0]), None)
            return (bd, calle, aj("miembros_prob") / 100.0) if calle else None
        # sin el modo: solo las bandas que tienen gente de calle en los datos; los del puerto, mientras dura su parte de la historia
        historia = ("m05" in self.completadas and "e05" not in self.completadas) if b["id"] == "puerto" else calle in G.TIPOS
        if historia and (calle in G.TIPOS or bd["nombre"] == "Los Calaveras"):
            return bd, calle, 0.3
        return None

    def guerra_txt(self):
        g = self.guerra
        if not g:
            return ""
        que = f"Defiendes {g['nombre']} de {g['banda']}" if g["tipo"] == "defensa" else f"Guerra por {g['nombre']} contra {g['banda']}"
        vivos = sum(1 for e in g["vivos"] if not e.muerto)
        if g["oleada"] == 0:
            return f"{que}. Vienen {g['total']} oleadas: la primera está al caer. No salgas del barrio."
        return f"{que}. Oleada {g['oleada']} de {g['total']}" + (f": quedan {vivos}." if vivos else ": superada.") + " No salgas del barrio."

    # ------------------------------------------------------------------ empezar
    def puede_guerra(self, forzar=False):
        """forzar: la defensa de un asalto de la reconquista se pelea en la calle aunque el modo esté apagado."""
        return (forzar or self.guerra_activa()) and not self.guerra and not self.mision and not self.trabajo and not self.transicion and self.mundo.tipo == "ciudad"

    def guerra_baja(self, p):
        """Has tumbado a uno de una banda en su barrio. A la segunda (lo dicen los datos), la banda entera sale a por ti."""
        banda = getattr(p, "banda", None)
        if p.tipo != "banda" or not banda or not self.puede_guerra():
            return
        b = self.mundo.barrio(p.x, p.y)
        if b["id"] in self.j.territorios or self.banda_de_barrio(b) != banda:
            return
        lista = [t for t in self._bajas_guerra.get(b["id"], []) if self.t - t < aj("ventana_bajas")] + [self.t]
        self._bajas_guerra[b["id"]] = lista
        falta = int(aj("bajas_para_empezar")) - len(lista)
        if falta > 0:
            self.decir(f"{banda} no perdona: {'una baja más' if falta == 1 else f'{falta} bajas más'} en {b['nombre']} y habrá guerra por el barrio.")
        else:
            self._bajas_guerra.pop(b["id"], None)
            self.empezar_guerra(b)

    def empezar_guerra(self, b, defensa=False, banda=None, rec=None):
        """rec: la defensa en persona de un asalto de la reconquista (reconquista.py), con sus oleadas, su tamaño y sus bandas."""
        if not self.puede_guerra(bool(rec)):
            return False
        banda = banda or self.banda_de_barrio(b) or random.choice(G.nombres_bandas())
        n = max(1, int(rec["oleadas"] if rec else aj("defensa_oleadas" if defensa else "oleadas")))
        self.guerra = {"tipo": "defensa" if defensa else "conquista", "barrio": b["id"], "nombre": b["nombre"], "banda": banda, "oleada": 0, "total": n,
                       "vivos": [], "veh": [], "t": random.uniform(3.0, 5.0), "fuera": 0.0, "quedan": None, "limpia": True, "avisado": False,
                       "rec": bool(rec), "base": int(rec["base"]) if rec else 0, "bandas": list(rec["bandas"]) if rec else [banda]}
        self.son("territorio", cat="interfaz")
        self.decir(random.choice(LISTAS["frases_defensa" if defensa else "frases_empieza"]).format(banda=banda, barrio=b["nombre"])
                   + f" Son {n} oleadas, cada una más dura. No salgas del barrio, o se dará la pelea por perdida. La tecla O te dice cómo va.")
        if self.j.banda:                                         # los tuyos acuden a pelear a tu lado
            from . import sistemas
            llegan, frase = sistemas.llamar(self)
            if llegan:
                self.decir(frase)
        return True

    # ------------------------------------------------------------------ oleadas
    def _grupo_guerra(self, clase, banda, k):
        t = G.tipo_enemigo(clase)
        if not t:
            return {"tipo": f"Pandillero de {banda}", "arma": random.choice(["pistola", "pistola", "subfusil", "bate"]), "salud": 70 + 8 * (k - 1)}
        return {"clase": clase, "tipo": f"{t.get('nombre', 'Pandillero')} de {banda}", "salud": float(t.get("salud", 70)) + 8 * (k - 1)}

    def _oleada(self):
        g = self.guerra
        g["oleada"] += 1
        g["limpia"] = False
        k = g["oleada"]
        banda = g["bandas"][(k - 1) % len(g["bandas"])]          # en una alianza, cada oleada es de una de las bandas
        tipos, refuerzo = G.tipos_de_banda(banda)
        tr = G.tipo_enemigo(refuerzo) if refuerzo else None
        if tr is None or tr.get("vehiculo") not in self.modelos:
            tr = None
        n = int(g["base"] or aj("oleada_base")) + k - 1
        llegan = min(max(0, n - 2), int(tr.get("ocupantes", 3) or 3)) if tr and k == g["total"] and g["total"] > 1 else 0
        x, y = self.pos()
        pos = self._punto_cercano(30, 55) or self.mundo.punto_libre(x + 35, y + 5)
        gente_ = []
        for i in range(n - llegan):
            clase = (tipos[-1] if i == 0 else tipos[0]) if tipos else ""          # uno de los duros en cada oleada
            e = self._crear_enemigo(self._grupo_guerra(clase, banda, k), *self.mundo.punto_libre(pos[0] + random.uniform(-5, 5), pos[1] + random.uniform(-5, 5)))
            self.personas.append(e)
            gente_.append(e)
        veh = None
        if llegan:
            ref = [self._crear_enemigo(self._grupo_guerra(refuerzo, banda, k), pos[0], pos[1]) for _ in range(llegan)]
            veh = self.llegar_en_vehiculo(tr["vehiculo"], ref)
            if veh is None:                                      # aquí no puede venir un vehículo: llegan a pie con los demás
                for e in ref:
                    e.x, e.y = self.mundo.punto_libre(pos[0] + random.uniform(-6, 6), pos[1] + random.uniform(-6, 6))
                    self.personas.append(e)
            else:
                g["veh"].append(veh)
            gente_ += ref
        for e in gente_:
            e.tag = "guerra"
            e.banda = banda
            e.activo = True
        g["vivos"] = gente_
        g["quedan"] = len(gente_)
        self.son("evento", cat="interfaz")
        self.decir(f"Oleada {k} de {g['total']}: {len(gente_)} de {banda}. {self.situar(pos[0], pos[1], 'Vienen')}."
                   + (f" {llegan} de ellos llegan en un vehículo: escucha el motor." if veh is not None else "") + " Pulsa Q para fijar al más cercano.")
        if self.cfg["punteria"] == "completa":
            self.fijar(callar=True)

    def actualizar_guerra(self, dt):
        g = self.guerra
        j = self.j
        if not g:
            a = j.amenaza                                        # defender en persona: basta con entrar en el barrio que te atacan
            if a and self.t > self.t_guerra_enfria and self.puede_guerra():
                b = self.mundo.barrio(*self.pos())
                if b["id"] == a.get("territorio") and b["id"] in j.territorios:
                    self.empezar_guerra(b, True, a.get("banda"))
            return
        if self.transicion:
            return
        if self.mundo.barrio(*self.pos())["id"] != g["barrio"]:
            g["fuera"] += dt
            if g["fuera"] > 3 and not g["avisado"]:
                g["avisado"] = True
                self.decir(f"Has salido de {g['nombre']}. Vuelve antes de {int(aj('fuera_max'))} segundos o la pelea se da por perdida.")
            if g["fuera"] > aj("fuera_max"):
                self.guerra_retirada()
                return
        else:
            g["fuera"], g["avisado"] = 0.0, False
        vivos = sum(1 for e in g["vivos"] if not e.muerto)
        if vivos:
            if vivos != g["quedan"]:
                g["quedan"] = vivos
                self.decir("Queda uno. Pulsa Q para fijarlo." if vivos == 1 else f"Quedan {vivos}.")
            return
        if not g["limpia"]:                                      # acaba de caer el último de la oleada
            g["limpia"] = True
            if g["oleada"] >= g["total"]:
                self._guerra_ganada()
                return
            g["t"] = random.uniform(aj("pausa_min"), max(aj("pausa_min"), aj("pausa_max")))
            self.app.son("llegada")
            self.decir(f"Oleada {g['oleada']} superada. Recarga y prepárate: viene otra.")
            return
        g["t"] -= dt
        if g["t"] <= 0:
            self._oleada()

    # ------------------------------------------------------------------ final
    def _guerra_ganada(self):
        g, j = self.guerra, self.j
        self.guerra = None
        if g["rec"]:                                             # era la defensa de un asalto de la reconquista: lo cuenta ella
            self.app.son("mision_ok")
            self.rec_defendido("persona", g=g)
            return
        paga = 0.5 if self.cfg["mod_dinero"] else 1.0
        frase = random.choice(LISTAS["frases_gana"]).format(banda=g["banda"], barrio=g["nombre"])
        self.son("territorio", cat="interfaz")
        self.app.son("mision_ok")
        if g["tipo"] == "conquista":
            if g["barrio"] not in j.territorios:
                j.territorios.append(g["barrio"])
            j.barrios_banda.pop(g["barrio"], None)
            j.stats["conquistas"] = j.stats.get("conquistas", 0) + 1
            premio = int(aj("premio_conquista") * paga)
            self.cambiar_reputacion(max(3, 15 - 3 * (len(j.territorios) - 1)))
            self.decir(f"{frase} {g['nombre']} es tuyo: te pagará {self.precio('tributo_territorio', 300)} euros cada medianoche.")
        else:
            if j.amenaza and j.amenaza.get("territorio") == g["barrio"]:
                j.amenaza = None
            j.stats["defensas"] = j.stats.get("defensas", 0) + 1
            premio = int(aj("premio_defensa") * paga)
            self.cambiar_reputacion(3)
            self.decir(f"{frase} {g['nombre']} sigue siendo tuyo.")
        if premio:
            self.dar_dinero(premio, "Lo que se han dejado en la huida")
        self.cambiar_animo(4)
        from . import menus_juego
        menus_juego.autoguardar(self)

    def guerra_retirada(self, texto=None, callar=False):
        """La guerra se acaba sin ganarla: te vas del barrio, caes, te detienen o te metes en otra cosa."""
        g = self.guerra
        if not g:
            return
        self.guerra = None
        self.t_guerra_enfria = self.t + 40.0
        for e in g["vivos"]:
            if e in self.personas and not e.muerto:
                self.personas.remove(e)
        for v in g["veh"]:
            if not v.muerto and not v.desplegado:
                self.quitar_vehiculo(v)
        if self.objetivo in g["vivos"]:
            self.objetivo = None
        if callar:
            return
        self.son("mision_fallo", cat="interfaz")
        base = texto or random.choice(LISTAS["frases_retirada"]).format(banda=g["banda"], barrio=g["nombre"])
        if g["rec"]:
            self.decir(f"{base} El asalto a {g['nombre']} sigue: vuelve y échalos, o envía a tu gente desde el móvil, en Territorios, antes de que se acabe el plazo.")
        elif g["tipo"] == "defensa":
            self.decir(f"{base} {g['banda']} sigue atacando {g['nombre']}: si no vuelves y los echas antes de medianoche, lo pierdes.")
        else:
            self.decir(f"{base} {g['nombre']} sigue siendo de {g['banda']}. Puedes volver a intentarlo cuando quieras.")

    def lugar_de_barrio(self, b, mapa=None):
        """Un lugar de ese barrio al que llevar el GPS: el más cercano si estás en su localidad."""
        mapa = mapa or self.mundo
        ls = [l for l in mapa.lugares.values() if mapa.barrio(l.x, l.y)["id"] == b["id"] and l.tipo not in ("salida", "embarcadero")]
        if not ls:
            return None
        x, y = self.pos()
        return min(ls, key=lambda l: (l.x - x) ** 2 + (l.y - y) ** 2)
