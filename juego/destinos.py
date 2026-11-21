"""El objetivo, el GPS y las persecuciones (1.7.1).

- La O dice primero dónde está el objetivo (nombre, metros, dirección, calle y, si se mueve, hacia dónde va) y después
  lo demás. Cuando el objetivo se mueve o hay prisa, una pulsación dice solo eso; dos seguidas, la explicación entera.
- Mayúsculas O vuelve al objetivo de la misión o del trabajo: deja cualquier desvío, lo marca en el GPS y, si está al
  alcance del radar, lo deja elegido en el radar.
- Mayúsculas G quita el destino (primero el desvío; a la siguiente, el destino) y Control G recupera el último quitado.
- «Ayuda en las persecuciones» (Opciones, Combate y dificultad): avisos más seguidos de por dónde va quien huye, cada
  giro dicho, y el que huye afloja antes si te quedas atrás. Los números, en los datos (vida.json, persecuciones).

El modelo de destinos del GPS (un destino y, debajo, el que espera) está en `Partida.fijar_gps`.
"""
from .i18n import tr
import math
import time

from . import mundo as M
from .ajustes import Ajustes
from .entidades import Objeto, Persona, Vehiculo

AJ = Ajustes("persecuciones", {
    # en vehículo: cada cuántos segundos se dice por dónde va, desde qué distancia, y cuánto afloja al quedarte atrás
    "canta_cada": 12, "canta_desde": 45, "afloja_medio": 90, "afloja_lejos": 150, "factor_medio": 80, "factor_lejos": 55,
    "ayuda_canta_cada": 7, "ayuda_canta_desde": 25, "ayuda_afloja_medio": 60, "ayuda_afloja_lejos": 110, "ayuda_factor_medio": 70, "ayuda_factor_lejos": 45,
    "ayuda_tiempo": 15, "ayuda_giros_cada": 3,
    # a pie, siguiendo a alguien: cada cuánto se avisa, a cuántos metros se le pierde y cuántos segundos se aguanta
    "seguir_aviso": 5, "seguir_lejos": 55, "ayuda_seguir_aviso": 3.5, "ayuda_seguir_lejos": 65, "ayuda_seguir_aguante": 5,
    "doble_o": 1.5,
}, {
    "frases_empieza": [tr("Es una persecución en vehículo: a pie no le alcanzas, y con un vehículo lento, tampoco. El GPS y la baliza le siguen a él. "
                       "La O te dice dónde está y hacia dónde va, y la Q lo fija para oírlo. Cada poco te digo por dónde va.")],
    "frases_a_pie": [tr("Vas a pie: sube cuanto antes a un vehículo rápido, con F junto a uno, o pide el tuyo en el móvil, en Mis vehículos.")],
}, cero=("ayuda_tiempo", "ayuda_seguir_aguante"))


class Destinos:
    """Mixin de Partida."""

    # ------------------------------------------------------------------ persecuciones
    def ayuda_persecucion(self):
        return bool(self.cfg["ayuda_persecucion"]) and not getattr(self, "en_servidor", False)

    def pers(self, k):
        """Un número de las persecuciones: el de la ayuda si está puesta y lo hay, o el de siempre."""
        if self.ayuda_persecucion() and ("ayuda_" + k) in AJ.n:
            return AJ("ayuda_" + k)
        return AJ(k)

    def pers_explicar(self, vo):
        """Al empezar una persecución en vehículo: qué hace falta y cómo se sigue a quien huye."""
        t = AJ.frase("frases_empieza")
        if not self.j.veh:
            t += " " + AJ.frase("frases_a_pie")
        if self.ayuda_persecucion():
            t += tr(" Llevas puesta la ayuda en las persecuciones: te digo cada giro, y si te quedas atrás afloja antes.")
        else:
            t += tr(" Si se te resisten, en Opciones, Combate y dificultad, está la ayuda en las persecuciones.")
        self.decir(t)

    def _calle_de(self, x, y):
        """La calle en la que está ese punto, o vacío si no se sabe (en el mar, por ejemplo)."""
        try:
            t, idx, _ = self.mundo.via_cercana(x, y)
            return self.mundo.nombre_via(t, idx)
        except Exception:
            return ""

    def pers_donde(self, vo):
        """Dónde está y hacia dónde va un vehículo: «a 80 metros, al norte, por Calle de la Sal, va hacia el este»."""
        x, y = self.pos()
        t = tr('a {int} metros, {direccion_txt}').format(int=(int(vo.dist(x, y))), direccion_txt=(self.direccion_txt(vo.x, vo.y)))
        calle = self._calle_de(vo.x, vo.y)
        if calle:
            t += tr(', por {calle}').format(calle=(calle))
        if abs(vo.vel) > 1.0:
            t += tr(', va hacia el {cardinal}').format(cardinal=(M.cardinal(vo.rumbo)))
        elif getattr(vo, "ia", None):
            t += tr(", parado")
        return t

    def pers_giros(self, ms, vo, dt):
        """Con la ayuda puesta: cada vez que quien huye cambia de calle, se dice hacia dónde tira."""
        if not self.ayuda_persecucion():
            return
        rumbo = M.cardinal(vo.rumbo)
        ms["t_giro"] = ms.get("t_giro", 0.0) - dt
        if ms.get("rumbo_obj") is None:
            ms["rumbo_obj"] = rumbo
        elif rumbo != ms["rumbo_obj"] and abs(vo.vel) > 2.0 and ms["t_giro"] <= 0:
            ms["rumbo_obj"] = rumbo
            ms["t_giro"] = AJ("ayuda_giros_cada")
            calle = self._calle_de(vo.x, vo.y)
            self.decir(tr('Gira hacia el {rumbo}').format(rumbo=(rumbo)) + (tr(' por {calle}').format(calle=(calle)) if calle else "") + tr('. A {int} metros, {direccion_txt}.').format(int=(int(vo.dist(*self.pos()))), direccion_txt=(self.direccion_txt(vo.x, vo.y))))
            ms["t_canta"] = max(ms.get("t_canta", 0.0), self.pers("canta_cada") * 0.6)

    # ------------------------------------------------------------------ dónde está el objetivo
    def _donde_lugar(self, q, pre=tr("Destino")):
        if q.mapa != self.mundo.id:
            con = self.conexion_hacia(q.mapa)
            t = tr('{pre}: {nombre}, en {nombre2}.').format(pre=(pre), nombre=(q.nombre), nombre2=(self.mapas[q.mapa].nombre))
            if con is not None:
                t += tr(' Para ir: {situar}.').format(situar=(self.situar(con.x, con.y, con.nombre)))
                return {"texto": t, "x": con.x, "y": con.y, "cosa": con}
            return {"texto": t, "x": None, "y": None, "cosa": None}
        calle = self._calle_de(q.x, q.y)
        return {"texto": f"{pre}: {self.situar(q.x, q.y, q.nombre)}" + (tr(', en {calle}').format(calle=(calle)) if calle and math.hypot(q.x - self.pos()[0], q.y - self.pos()[1]) > 25 else "") + ".",
                "x": q.x, "y": q.y, "cosa": q}

    def _donde_cosa(self, c, nombre=None, pre=""):
        calle = self._calle_de(c.x, c.y)
        lejos = math.hypot(c.x - self.pos()[0], c.y - self.pos()[1]) > 25
        return {"texto": f"{pre}{self.situar(c.x, c.y, nombre or c.nombre)}" + (tr(', en {calle}').format(calle=(calle)) if calle and lejos else "") + ".", "x": c.x, "y": c.y, "cosa": c}

    def objetivo_donde(self):
        """Dónde está ahora mismo lo que pide la misión: {"texto", "x", "y", "cosa", "urgente"}, o None si no hay nada
        que situar. `urgente` es que se mueve o que corre el tiempo: entonces la O dice solo esto."""
        ms = self.mision
        if not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return None
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        l = self._lugar_paso(p)
        x, y = self.pos()
        d = None
        urgente = ms.get("limite") is not None
        v = ms.get("veh")
        if tipo == "perseguir" and ms.get("veh_objetivo") is not None and not ms["veh_objetivo"].muerto:
            vo = ms["veh_objetivo"]
            d = {"texto": f"{vo.nombre}: {self.pers_donde(vo)}.", "x": vo.x, "y": vo.y, "cosa": vo}
            urgente = True
        elif tipo == "seguir" and ms.get("movil"):
            o = ms["movil"]
            nombre = o["nombre"].capitalize()
            if not o.get("visto", True) and l is not None:
                d = self._donde_lugar(l, tr('{nombre} te espera en').format(nombre=(nombre)))
            else:
                t = tr('{nombre} va a {int} metros, {direccion_txt}').format(nombre=(nombre), int=(int(math.hypot(o['x'] - x, o['y'] - y))), direccion_txt=(self.direccion_txt(o['x'], o['y'])))
                calle = self._calle_de(o["x"], o["y"])
                if calle:
                    t += tr(', por {calle}').format(calle=(calle))
                if o["espera"] > 0:
                    t += tr(", todavía parado")
                elif o["i"] < len(o["ruta"]):
                    tx, ty = o["ruta"][o["i"]]
                    if math.hypot(tx - o["x"], ty - o["y"]) > 1:
                        t += tr(', camina hacia el {cardinal}').format(cardinal=(M.cardinal(M.rumbo_a(tx - o['x'], ty - o['y']))))
                d = {"texto": t + ".", "x": o["x"], "y": o["y"], "cosa": None}
                urgente = True
        elif tipo == "escoltar" and ms.get("escolta"):
            e = ms["escolta"]
            nombre = e["nombre"].capitalize()
            if e["contigo"]:
                dest = self.lugares.get(p.get("destino", ""))
                d = self._donde_lugar(dest) if dest is not None else {"texto": "", "x": None, "y": None, "cosa": None}
                d["texto"] = (d["texto"] + tr(' {nombre} va contigo, a {int} metros, {direccion_txt}.').format(nombre=(nombre), int=(int(math.hypot(e['x'] - x, e['y'] - y))), direccion_txt=(self.direccion_txt(e['x'], e['y'])))).strip()
                urgente = True
            elif l is not None:
                d = self._donde_lugar(l, tr('{nombre} te espera en').format(nombre=(nombre)))
        elif tipo in ("robar", "entregar") and v is not None and not v.muerto and self.j.veh is not v:
            d = self._donde_cosa(v, pre=tr("El vehículo: "))
        elif tipo == "recoger" and ms.get("objeto") is not None and not ms["recogido"]:
            d = self._donde_cosa(ms["objeto"], self.txt(p.get("objeto") or ms["objeto"].nombre), pre=tr("Hay que recoger: "))
        elif tipo == "eliminar" and ms.get("generado"):
            vivos = [e for e in ms["enemigos"] if not e.muerto and not getattr(e, "rendido", False)]
            if vivos:
                e = min(vivos, key=lambda e: e.dist(x, y))
                d = self._donde_cosa(e, pre=tr("El más cercano: "))
            elif l is not None:
                d = self._donde_lugar(l)
        elif tipo == "sigilo" and l is not None:
            d = self._donde_lugar(l)
            gs = ms.get("guardias") or []
            if gs:
                g = min(gs, key=lambda g: math.hypot(g["x"] - x, g["y"] - y))
                d["texto"] += tr(' Hay {len} vigilantes; el más cercano, a {int} metros, {direccion_txt}.').format(len=(len(gs)), int=(int(math.hypot(g['x'] - x, g['y'] - y))), direccion_txt=(self.direccion_txt(g['x'], g['y'])))
        elif tipo == "ruta" or (tipo == "carrera" and (ms.get("carrera") or {}).get("fase") == "corre"):
            puntos = p.get("puntos", [])
            q = self.lugares.get(puntos[ms.get("ruta_i", 0)]) if ms.get("ruta_i", 0) < len(puntos) else None
            if q is not None:
                d = self._donde_lugar(q, tr('Punto {v} de {len}').format(v=(ms.get('ruta_i', 0) + 1), len=(len(puntos))))
            urgente = urgente or tipo == "carrera"
        elif tipo in ("ir", "entregar", "eliminar", "vigilar", "carrera", "robar") and l is not None:
            if not (tipo == "vigilar" and (ms.get("vigia") or {}).get("dentro")):
                d = self._donde_lugar(l)
        if d is None or not d["texto"]:
            return None
        d["urgente"] = urgente
        return d

    def _nota_gps(self, d):
        """Lo que hay que saber del GPS para que la O y la G no parezcan decir cosas distintas."""
        g = self.gps
        if d is None or d.get("x") is None:
            return ""
        if g is None:
            return tr(" El GPS no lo tiene marcado: con Mayúsculas O vuelves a él.")
        if not g["auto"]:
            return tr(' El GPS está en un desvío a {nombre}: con Mayúsculas O vuelves al objetivo.').format(nombre=(g['nombre']))
        return ""

    def objetivo_posicion_txt(self):
        d = self.objetivo_donde()
        return (d["texto"] + self._nota_gps(d)) if d else ""

    def decir_objetivo(self):
        """La tecla O. Con un objetivo que se mueve o con el tiempo corriendo, una pulsación dice dónde está y hacia
        dónde va, y lo que queda de tiempo; dos pulsaciones seguidas, la explicación entera. En lo demás, todo de una vez,
        con la posición por delante."""
        ahora = time.monotonic()
        ms = self.mision
        doble = ms is not None and getattr(self, "_o_ultima", None) is not None and self._o_ultima[1] is ms and ahora - self._o_ultima[0] <= AJ("doble_o")
        self._o_ultima = None if doble else (ahora, ms)
        d = self.objetivo_donde() if ms and not self.guerra else None
        if d is None or not d["urgente"] or doble:
            self.decir(self.objetivo_txt(), True)
            return
        t = d["texto"] + self._nota_gps(d)
        if ms.get("limite") is not None:
            t += tr(' Te quedan {int} segundos.').format(int=(int(ms['limite'])))
        if "o_doble" not in ms["avisos"]:
            ms["avisos"].add("o_doble")
            t += tr(" Pulsa O dos veces seguidas para oír la explicación de la misión.")
        self.decir(t, True)

    # ------------------------------------------------------------------ volver al objetivo
    def _radar_enfocar(self, cosa):
        """Deja elegido en el radar lo que se indica, si está a su alcance. True si lo está."""
        if cosa is None:
            return False
        filtro = self.cfg["radar_filtro"]
        self.cfg["radar_filtro"] = "todo"
        try:
            lista = self._radar_construir()
        finally:
            self.cfg["radar_filtro"] = filtro
        idx = next((k for k, e in enumerate(lista) if e[3] is cosa), None)
        if idx is None:
            return False
        if filtro != "todo":
            propia = self._radar_construir()
            idx2 = next((k for k, e in enumerate(propia) if e[3] is cosa), None)
            if idx2 is None:
                self.cfg["radar_filtro"] = "todo"                # con el filtro puesto no saldría: se quita, y se dice
                self.decir(tr("Radar: todo."))
            else:
                lista, idx = propia, idx2
        self.radar_lista, self.radar_idx = lista, idx
        return True

    def enfocar_objetivo(self):
        """Mayúsculas O: vuelve al objetivo de la misión o del trabajo, siempre igual. Deja el desvío que hubiera (se
        puede recuperar con Control G), lo marca en el GPS y, si está al alcance del radar, lo deja elegido en el radar."""
        ms = self.mision
        if not ms and not self.trabajo:
            self.app.son("error")
            self.decir(tr("No tienes ninguna misión ni ningún trabajo en curso. ") + self.objetivo_txt().replace("No tienes ninguna misión en curso. ", ""), True)
            return False
        g = self.gps
        if g is not None and not g["auto"]:                      # estabas en un desvío, o con un destino tuyo: se aparta
            self._recordar_cancelado(g)
            base = g.get("anterior")
            self.gps = base if base is not None and base["auto"] else None
            if self.gps is not None:
                self.gps["clave"] = None
                self._recalcular_gps()
        if ms:
            ms["gps_callado"] = False
            ms["t_sin_gps"] = 0.0
            if self.gps is None:
                self.gps_mision(hablar=False)
        elif self.gps is None and self.trabajo.get("lugar") is not None:
            self.gps_a_lugar(self.trabajo["lugar"], auto=True, callar=True)
        d = self.objetivo_donde()
        self.app.son("notificacion")
        if d is None:
            self.decir(tr("Vuelves al objetivo. ") + self.objetivo_txt() + ("" if self.gps else tr(" Ahora mismo no hay ningún sitio que marcar en el GPS.")), True)
            if self.gps:
                self.repetir_gps_suave()
            return bool(self.gps)
        en_radar = self._radar_enfocar(d.get("cosa"))
        self.decir(tr("Vuelves al objetivo. ") + d["texto"] + (tr(" Marcado en el GPS") + (tr(" y elegido en el radar.") if en_radar else ".") if self.gps else ""), True)
        if self.gps:
            self.repetir_gps_suave()
        return True

    # ------------------------------------------------------------------ quitar y recuperar
    def _recordar_cancelado(self, g):
        c = {k: g.get(k) for k in ("dest", "nombre", "sigue", "auto", "radio", "cosa", "final", "mapa")}
        l = self._lugar_del_gps() if g is self.gps else None
        c["lugar"] = g.get("final") or (l.id if l is not None else None)
        self.gps_cancelado = c

    def quitar_gps_jugador(self):
        """Mayúsculas G: quitas tú el destino. Si era un desvío, el GPS vuelve a lo que esperaba debajo; si no, se queda
        sin destino. Lo quitado se recuerda: Control G lo recupera."""
        g = self.gps
        if g is None:
            self.app.son("error")
            c = getattr(self, "gps_cancelado", None)
            self.decir(tr("No hay ningún destino marcado.") + (tr(' Con Control G recuperas el último que quitaste: {nombre}.').format(nombre=(c['nombre'])) if c else ""), True)
            return None
        self._recordar_cancelado(g)
        if g.get("anterior") is not None:
            self.app.son("menu_atras")
            self._volver_del_desvio(tr('Dejas el desvío a {nombre}.').format(nombre=(g['nombre'])))
            self.decir(tr("Con Control G lo recuperas."))
            return "desvio"
        self.gps = None
        self.app.son("menu_atras")
        t = tr('GPS cancelado: ya no te guía a {nombre}. Con Control G lo recuperas.').format(nombre=(g['nombre']))
        if self.mision and g["auto"]:
            self.mision["gps_callado"] = True                    # lo has quitado tú: la misión no lo vuelve a poner sola
            t = tr('GPS cancelado: ya no te guía a {nombre}. Con la G vuelves a marcar la misión.').format(nombre=(g['nombre']))
        self.decir(t, True)
        return "destino"

    def recuperar_gps(self):
        """Control G: vuelve a marcar el último destino que quitaste con Mayúsculas G. Si ahora vas a otro sitio, es un
        desvío: al acabarlo, el GPS vuelve a lo que llevas."""
        c = getattr(self, "gps_cancelado", None)
        if not c:
            self.app.son("error")
            self.decir(tr("No has quitado ningún destino que se pueda recuperar."), True)
            return False
        cosa = c.get("cosa") if c.get("cosa") is not None else c.get("sigue")
        if isinstance(cosa, Vehiculo) and (cosa.muerto or cosa not in self.vehiculos or cosa is self.j.veh) or \
                isinstance(cosa, Persona) and (cosa.muerto or cosa not in self.personas) or isinstance(cosa, Objeto) and cosa not in self.objetos:
            self.gps_cancelado = None
            self.app.son("error")
            self.decir(tr('{nombre} ya no está: no se puede recuperar ese destino.').format(nombre=(c['nombre'])), True)
            return False
        antes = self.gps
        if c.get("auto") and (self.mision or (self.trabajo and self.trabajo.get("lugar") is not None)):       # era lo de la misión o lo del trabajo: se vuelve a ello
            self.gps_cancelado = None
            return self.enfocar_objetivo()
        if c.get("auto") and not self.trabajo:                   # era de una misión o de un trabajo que ya se acabó
            self.gps_cancelado = None
            self.app.son("error")
            self.decir(tr('{nombre} era de una misión o de un trabajo que ya no tienes en curso.').format(nombre=(c['nombre'])), True)
            return False
        lugar = self.lug(c["lugar"]) if c.get("lugar") else None
        if lugar is not None:
            self.gps_a_lugar(lugar, auto=bool(c.get("auto")), callar=True, desvio=not c.get("auto"))
        elif c.get("mapa") != self.mundo.id:
            self.app.son("error")
            self.decir(tr('{nombre} quedó en {v}: márcalo de nuevo cuando vuelvas.').format(nombre=(c['nombre']), v=(self.mapas[c['mapa']].nombre if c.get('mapa') in self.mapas else tr('otra localidad'))), True)
            return False
        else:
            self.fijar_gps(c["dest"][0], c["dest"][1], c["nombre"], sigue=c.get("sigue"), auto=bool(c.get("auto")), radio=c.get("radio"), callar=True, desvio=not c.get("auto"), cosa=c.get("cosa"))
        if self.gps is None or self.gps is antes:
            self.app.son("error")
            self.decir(tr('No se ha podido recuperar {nombre}.').format(nombre=(c['nombre'])), True)
            return False
        self.gps_cancelado = None
        self.app.son("notificacion")
        base = self.gps.get("anterior")
        self.decir(tr('Recuperado: el GPS vuelve a guiarte a {nombre}.').format(nombre=(c['nombre'])) + (tr(' Al acabar, vuelve a {nombre}.').format(nombre=(base['nombre'])) if base is not None else ""), True)
        self.repetir_gps_suave()
        return True
