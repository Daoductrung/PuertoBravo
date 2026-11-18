"""Mis vehículos y el chófer de la banda.

- Mis vehículos: los vehículos tuyos (comprados, mejorados en el taller, sacados de un garaje o con nombre puesto por ti)
  no desaparecen al alejarte ni al coger otro. Los que están en la calle de la localidad en la que estás son vehículos
  de verdad, marcados con `v.mio`; los de las demás localidades esperan en `Partida.mis_lejos`, como datos, hasta que
  vuelves. Todos se guardan con la partida. Hay un tope en la calle (en los datos): al pasarse, el más antiguo va solo
  a un garaje con sitio, y si no lo hay, se avisa.
- En un servidor en línea los vehículos de la calle los lleva el servidor, con su propio máximo por jugador: aquí no
  se marca ni se guarda nada, y la lista del móvil enseña lo que el servidor reconoce como tuyo.
- Chófer: alguien de tu banda viene con un vehículo de tu garaje o con uno de la banda, y conduce él hasta el destino
  que marques en el GPS, con el piloto que ya existe. Tú vas de pasajero.
"""
import math
import random

from . import mundo as M
from . import registro
from .menus import EntradaTexto, Menu, Opcion

AJUSTES = {"tope_calle": 6, "chofer_espera_min": 25, "chofer_espera_max": 75, "chofer_busqueda_max": 2}
_LISTAS = {
    "chofer_modelos": ["sedan", "todoterreno", "utilitario"],
    "chofer_frases_sale": ["Voy para allá. Dame un minuto.", "Arranco ahora mismo. No te muevas de ahí.", "Hecho. Salgo ya.", "Cojo las llaves y voy."],
    "chofer_frases_llega": ["Ya estoy aquí. Sube cuando quieras.", "Tu coche, jef[e|a]. Sube.", "Aquí me tienes. ¿Nos vamos?"],
    "chofer_frases_destino": ["¿A dónde vamos? Márcame el sitio.", "Tú dirás a dónde.", "Dime dónde y te llevo."],
    "chofer_frases_marcha": ["Marchando.", "Vamos para allá.", "Agárrate, que salimos.", "Eso está hecho."],
    "chofer_frases_llegada": ["Hemos llegado.", "Ya estamos.", "Aquí es."],
    "chofer_frases_espera": ["Te espero aquí.", "Aquí me quedo, con el motor a punto.", "No me muevo de aquí."],
    "chofer_frases_adios": ["Hasta luego, jef[e|a].", "Cuando me necesites, llama.", "Me vuelvo con los demás."],
    "nombres_propuestos": ["La Gaviota", "El Rayo", "La Tormenta", "El Tiburón", "La Centella", "El Viejo", "La Fiera", "El Fantasma"],
}
LISTAS = {k: list(v) for k, v in _LISTAS.items()}
NOMBRE_MAX = 30


def configurar(datos):
    """El tope de vehículos en la calle y lo del chófer salen de los datos (vida.json, vehiculos_propios), que un mod puede cambiar."""
    c = next((x for x in datos.get("vehiculos_propios", []) if isinstance(x, dict)), {})
    for k, serie in (("tope_calle", 6), ("chofer_espera_min", 25), ("chofer_espera_max", 75), ("chofer_busqueda_max", 2)):
        try:
            AJUSTES[k] = max(0 if k == "chofer_busqueda_max" else 1, int(c.get(k, serie)))
        except (TypeError, ValueError):
            AJUSTES[k] = serie
    for k, serie in _LISTAS.items():
        v = c.get(k)
        LISTAS[k] = [str(x) for x in v if str(x).strip()] if isinstance(v, list) and any(str(x).strip() for x in v) else list(serie)


def tope():
    return AJUSTES["tope_calle"]


def nombres_propuestos(n=6, rng=random):
    """Unos cuantos nombres al azar para un vehículo: para quien no quiere, o no puede, escribirlo (con mando, por ejemplo)."""
    lista = list(dict.fromkeys(LISTAS["nombres_propuestos"]))
    return rng.sample(lista, min(n, len(lista)))


def _modelo_nombre(p, ident):
    mo = p.modelos.get(ident)
    return mo["nombre"] if mo else str(ident)


def nombre_completo(p, nombre, modelo_id):
    """«Rayo, Deportivo Centella» si le has puesto nombre; si no, solo el modelo."""
    mod = _modelo_nombre(p, modelo_id)
    return f"{nombre}, {mod}" if nombre and nombre != mod else mod


def _mejoras_txt(mejoras):
    from . import sistemas

    class _V:
        pass
    v = _V()
    v.mejoras = dict(mejoras or {})
    return sistemas.resumen(v)


class MisVehiculos:
    """Mixin de Partida."""

    def mis_iniciar(self):
        self.mis_lejos = []              # tus vehículos aparcados en otras localidades: datos, hasta que vuelves
        self.mio_sec = 0                 # para saber cuál es el más antiguo
        self.chofer = None

    # ------------------------------------------------------------------ cuáles son tuyos
    def es_mio(self, v):
        return v is not None and bool(getattr(v, "mio", False))

    def puede_ser_mio(self, v):
        """¿Se puede quedar el jugador con este vehículo? No los de una misión o de la banda, ni los barcos (van por su lado)."""
        return v is not None and not v.muerto and not v.tag and not v.modelo.get("barco") and self.mundo.tipo != "mar"

    def hacer_mio(self, v, callar=False):
        """Desde ahora este vehículo es tuyo: no desaparece, se guarda con la partida y sale en Mis vehículos."""
        if getattr(self, "en_servidor", False) or not self.puede_ser_mio(v):
            return False
        if self.es_mio(v):
            return True
        self.mio_sec += 1
        v.mio, v.mio_n, v.propio = True, self.mio_sec, True
        v.cerrado = False
        if v.plaza is not None:                                  # deja de ser un coche de esa plaza: no vuelve a salir otro encima
            self.plazas_usadas.add(v.plaza)
            self.plazas_activas.pop(v.plaza, None)
            v.plaza = None
        self._tope_mis_vehiculos(v, callar)
        return True

    def mis_vivos(self):
        """Tus vehículos que están en la calle de esta localidad (también el que llevas)."""
        return sorted((v for v in self.vehiculos if self.es_mio(v) and not v.muerto), key=lambda v: getattr(v, "mio_n", 0))

    def mis_en_calle(self):
        """Cuántos vehículos tuyos hay fuera de los garajes, en todas las localidades."""
        return len(self.mis_vivos()) + len(self.mis_lejos)

    def mis_en_garajes(self):
        return sum(len(g) for g in self.j.garajes.values())

    def garaje_con_sitio(self):
        """Una casa tuya con plaza libre; antes, las de esta localidad."""
        casas = [l for l in (self.lug(pid) for pid in self.j.propiedades) if l is not None and int(l.get("garaje", 0)) > len(self.j.garajes.get(l.id, []))]
        casas.sort(key=lambda l: l.mapa != self.mundo.id)
        return casas[0] if casas else None

    def _ficha_garaje(self, v):
        d = {"modelo": v.modelo["id"], "salud": v.salud, "nombre": v.nombre, "mejoras": dict(getattr(v, "mejoras", {}))}
        if getattr(v, "litros", None) is not None:
            d["litros"] = round(v.litros, 1)
        return self.averias_a_dict(v, d)

    def _tope_mis_vehiculos(self, nuevo, callar=False):
        """Con más vehículos en la calle que el tope, el más antiguo va solo a un garaje con sitio. Sin sitio, se avisa."""
        n = self.mis_en_calle()
        if n <= tope():
            return
        viejos = sorted([(getattr(v, "mio_n", 0), v) for v in self.mis_vivos() if v is not nuevo and v is not self.j.veh and not getattr(v, "con_chofer", False)]
                        + [(int(d.get("n", 0)), d) for d in self.mis_lejos], key=lambda e: e[0])
        casa = self.garaje_con_sitio()
        if not viejos or casa is None:
            if not callar:
                self.son("notificacion", cat="interfaz", vol=0.5)
                self.decir(f"Tienes {n} vehículos en la calle y lo razonable son {tope()}. No queda sitio en tus garajes: siguen todos a salvo, "
                           "pero vende alguno o compra una casa con garaje. Los tienes en el móvil, en Mis vehículos.")
            return
        viejo = viejos[0][1]
        if isinstance(viejo, dict):
            self.mis_lejos.remove(viejo)
            ficha = {k: viejo[k] for k in ("modelo", "salud", "nombre", "mejoras", "litros", "km", "pinchada", "revision") if k in viejo}
            nombre = viejo.get("nombre") or _modelo_nombre(self, viejo["modelo"])
        else:
            ficha, nombre = self._ficha_garaje(viejo), viejo.nombre
            if self.ultimo_veh is viejo:
                self.ultimo_veh = None
            self.quitar_vehiculo(viejo)
        self.j.garajes.setdefault(casa.id, []).append(ficha)
        if not callar:
            self.son("notificacion", cat="interfaz", vol=0.5)
            self.decir(f"Tienes más de {tope()} vehículos en la calle: tu mecánico se lleva {nombre}, el que más tiempo llevaba aparcado, al garaje de {self.nombre_lugar(casa)}.")

    # ------------------------------------------------------------------ guardar y cargar
    def _veh_de_dict(self, d, x=None, y=None):
        """Pone en la calle un vehículo guardado como datos, con su estado, sus mejoras, su combustible y su desgaste."""
        from . import sistemas
        v = self.crear_vehiculo(d["modelo"], float(d.get("x", self.j.x)) if x is None else x, float(d.get("y", self.j.y)) if y is None else y,
                                M.dir_de_rumbo(d.get("rumbo", 0)), None, d.get("nombre"))
        sistemas.poner(v, d.get("mejoras"))
        v.salud = min(v.salud_max, float(d.get("salud", v.salud_max)))
        v.rumbo = float(d.get("rumbo", 0))
        v.propio = True
        if v.nombre != v.modelo["nombre"]:
            registro.ocultar(v.nombre)                           # un nombre escrito por el jugador no se anota en el registro
        if "litros" in d:
            v.litros = float(d["litros"])
        self.averias_de_dict(v, d)
        return v

    def mis_a_dict(self, d, ultimo=None):
        """Añade a la partida que se guarda tus vehículos de la calle, de esta localidad y de las demás."""
        if getattr(self, "en_servidor", False):
            return
        lista = []
        for v in self.mis_vivos():
            if v is self.j.veh:
                continue
            f = dict(self._veh_fuera_dict(v), n=int(getattr(v, "mio_n", 0)))
            if v is ultimo:
                f["ultimo"] = True
            lista.append(f)
        lista += [dict(x) for x in self.mis_lejos]
        if lista:
            d["mis_vehiculos"] = lista
        if self.mio_sec:
            d["mio_sec"] = self.mio_sec

    def mis_cargar(self, d):
        """Lee tus vehículos de una partida guardada. Las partidas anteriores no traen la lista: el vehículo que tenían
        guardado, si llevaba mejoras del taller, pasa a ser tuyo, que para eso las pagaste."""
        self.mis_lejos = [dict(x) for x in (d.get("mis_vehiculos") or []) if isinstance(x, dict) and x.get("modelo")]
        try:
            self.mio_sec = max([int(d.get("mio_sec", 0) or 0)] + [int(x.get("n", 0) or 0) for x in self.mis_lejos])
        except (TypeError, ValueError):
            self.mio_sec = len(self.mis_lejos)
        f = self.veh_fuera
        if isinstance(f, dict) and f.get("modelo") and any((f.get("mejoras") or {}).values()) and "mis_vehiculos" not in d:
            self.mio_sec += 1
            self.mis_lejos.append(dict(f, n=self.mio_sec, ultimo=True))
            self.veh_fuera = None

    def _reponer_mis_vehiculos(self):
        """Vuelve a poner en la calle tus vehículos aparcados en esta localidad, al cargar la partida o al volver a ella."""
        if getattr(self, "en_servidor", False):
            return []
        puestos = []
        for d in list(self.mis_lejos):
            if d.get("mapa") != self.mundo.id or d.get("modelo") not in self.modelos:
                continue
            self.mis_lejos.remove(d)
            v = self._veh_de_dict(d)
            v.mio, v.mio_n = True, int(d.get("n", 0) or 0)
            if d.get("ultimo") and not self.j.veh and self.ultimo_veh is None:
                self.ultimo_veh = v
            puestos.append(v)
        return puestos

    def mis_al_cambiar_mapa(self, ultimo=None):
        """Antes de dejar una localidad: tus vehículos aparcados en ella se quedan apuntados, y allí estarán al volver."""
        if getattr(self, "en_servidor", False):
            return
        if ultimo is not None:                                   # el último que has usado es uno de aquí: los de antes ya no lo son
            for d in self.mis_lejos:
                d.pop("ultimo", None)
        for v in self.mis_vivos():
            if v is self.j.veh:
                continue
            f = dict(self._veh_fuera_dict(v), n=int(getattr(v, "mio_n", 0)))
            if v is ultimo:
                f["ultimo"] = True
            self.mis_lejos.append(f)

    def mis_al_servidor(self):
        """Al entrar en un servidor: allí los vehículos de la calle los lleva el servidor."""
        self.mis_lejos = []
        for v in self.vehiculos:
            if getattr(v, "mio", False):
                v.mio = False

    def dejar_o_quitar(self, v):
        """Te quedas sin el vehículo que llevas porque el juego te lleva a otro sitio: si es tuyo, se queda aparcado donde
        estaba; si no, desaparece, como siempre."""
        if v is None:
            return
        if self.j.veh is v:
            self.salir_vehiculo(forzado=True)
        if not self.es_mio(v):
            self.quitar_vehiculo(v)

    # ------------------------------------------------------------------ cuando el juego te lleva a otro sitio
    def vehiculo_para_llevar(self):
        """El vehículo que va contigo cuando el juego te devuelve a otro sitio: el que conduces o el que acabas de dejar
        al lado, si es de calle (ni de una misión ni de la banda, ni un barco, ni algo que vuela, ni con chófer)."""
        v = self.j.veh or self.tu_vehiculo(120)
        if v is None or v.muerto or v.tag or v.ardiendo >= 0 or v.modelo.get("barco") or v.modelo.get("vuela") or self.mundo.tipo == "mar" \
                or getattr(v, "con_chofer", False) or getattr(self, "en_servidor", False):
            return None
        return v

    def _plaza_al_lado(self, x, y):
        """Un hueco junto al bordillo cerca de ese punto, sin nada aparcado encima y sin tapar la puerta (ahí aparca el
        vehículo que dé la misión)."""
        px, py, _ = self.mundo.plaza_en(x, y)
        for dx, dy in ((13, 0), (-13, 0), (0, 13), (0, -13), (26, 0), (-26, 0), (0, 26), (0, -26), (39, 0), (-39, 0), (0, 39), (0, -39)):
            qx, qy, d = self.mundo.plaza_en(x + dx, y + dy)
            if math.hypot(qx - px, qy - py) >= 8 and all(o.muerto or o.dist(qx, qy) > 7 for o in self.vehiculos):
                return qx, qy, d
        return self.mundo.plaza_en(x + 13, y)

    def preparar_traslado(self, mapa):
        """Antes de que el juego te lleve a otro sitio (y antes de rebobinar al jugador, que le quita el vehículo de las
        manos): qué vehículo va contigo, y tu barco, si ibas en él, a un amarre. Devuelve {"veh": vehículo o None}."""
        j = self.j
        u = j.veh
        if j.barco_actual and u is not None and u.modelo.get("barco"):      # ibas en tu barco: no se pierde, vuelve a puerto
            emb = next((l for l in self.mapas[mapa].lugares.values() if l.tipo == "embarcadero"), None) or \
                next((l for m in self.mapas.values() for l in m.lugares.values() if l.tipo == "embarcadero"), None)
            if emb is not None:
                j.barcos.append({"modelo": j.barco_actual["modelo"], "nombre": j.barco_actual.get("nombre"), "salud": u.salud, "en": emb.id})
                self.decir(f"Tu barco, {u.nombre}, queda amarrado en {self.nombre_lugar(emb)}.")
            j.barco_actual = None
            self.salir_vehiculo(forzado=True)
            self.quitar_vehiculo(u)
            return {"veh": None}
        v = self.vehiculo_para_llevar()
        if v is not None and self.mapas[mapa].tipo == "mar":
            v = None
        if u is not None:
            self.salir_vehiculo(forzado=True)
            if u is not v and mapa != self.mundo.id and not self.es_mio(u):
                self.quitar_vehiculo(u)                          # el que no es tuyo y no puede venir desaparece, como siempre
        return {"veh": v}

    def llevarte_a(self, mapa, x, y, lleva=None):
        """El juego te devuelve a un sitio: al reintentar o repetir una misión, o al volver a un punto de control. Tu
        vehículo, el que llevabas o el que acababas de dejar al lado, va contigo y queda aparcado junto a ti, que es donde
        estaba cuando empezaste. Si no puede ir (uno de misión, un barco, algo que vuela), el tuyo se queda donde estaba y
        sale en Mis vehículos. Un barco tuyo vuelve a un amarre. `lleva` es lo que devolvió `preparar_traslado`, si hubo
        que llamarlo antes. Devuelve el vehículo que ha venido contigo, o None."""
        if lleva is None:
            lleva = self.preparar_traslado(mapa)
        v = lleva.get("veh")
        if v is not None and (v.muerto or v not in self.vehiculos):
            v = None
        if v is None:
            if mapa != self.mundo.id:
                self.cambiar_mapa(mapa, x, y)
            self.teletransportar(x, y)
            return None
        if mapa != self.mundo.id:                                # a otra localidad: viaja como datos y vuelve a la calle allí
            ficha = dict(self._veh_fuera_dict(v), n=int(getattr(v, "mio_n", 0)))
            mio = self.es_mio(v)
            self.quitar_vehiculo(v)
            self.ultimo_veh = None
            self.cambiar_mapa(mapa, x, y)
            px, py, d = self._plaza_al_lado(x, y)
            v = self._veh_de_dict(ficha, px, py)
            if mio:
                v.mio, v.mio_n = True, ficha["n"]
        else:
            px, py, d = self._plaza_al_lado(x, y)
            v.x, v.y = px, py
        v.dir, v.rumbo, v.vel, v.ia = d, d * 90.0, 0.0, None
        self.ultimo_veh = v
        self.teletransportar(x, y)
        self.decir(f"{v.nombre} viene contigo: queda aparcado a tu lado, {self.direccion_txt(v.x, v.y)}.")
        return v

    def ficha_a_la_calle(self, ficha, casa=None):
        """Saca a la calle, a tu nombre, un vehículo guardado como ficha de garaje: delante de esa casa, o junto a ti.
        En otra localidad queda apuntado y allí estará cuando vuelvas."""
        self.mio_sec += 1
        mapa = casa.mapa if casa is not None else self.mundo.id
        x, y = (casa.x, casa.y) if casa is not None else self.pos()
        if mapa == self.mundo.id and self.mundo.tipo != "mar":
            px, py, d = self._plaza_al_lado(x, y)
            v = self._veh_de_dict(dict(ficha, rumbo=d * 90.0), px, py)
            v.mio, v.mio_n = True, self.mio_sec
            return v
        px, py, d = self.mapas[mapa].plaza_en(x, y)
        self.mis_lejos.append(dict(ficha, x=px, y=py, rumbo=d * 90.0, mapa=mapa, n=self.mio_sec, donde=self.mapas[mapa].describir(px, py)))
        return None

    def vehiculos_tras_reintento_txt(self):
        """Tras reintentar: dónde están tus vehículos, en una frase, para que no parezca que falta ninguno."""
        if getattr(self, "en_servidor", False):
            return ""
        calle = self.mis_en_calle() - (1 if self.es_mio(self.tu_vehiculo(60)) else 0)
        garaje = self.mis_en_garajes()
        if calle <= 0 and garaje <= 0:
            return ""
        partes = []
        if garaje:
            partes.append(f"{garaje} en {'tu garaje' if len([g for g in self.j.garajes.values() if g]) == 1 else 'tus garajes'}")
        if calle > 0:
            partes.append(f"{calle} en la calle")
        return "Tus vehículos siguen donde estaban: " + " y ".join(partes) + ". Los tienes en el móvil, en Mis vehículos."

    def mas_vehiculos_txt(self, menos=None):
        """Lo que añade Mayúsculas L: cuántos vehículos más tienes y dónde mirarlos."""
        if getattr(self, "en_servidor", False):
            n = len(self.sv_mis_vehiculos()) - (1 if menos is not None else 0)
        else:
            n = self.mis_en_calle() - (1 if menos is not None and self.es_mio(menos) else 0) - (1 if self.es_mio(self.j.veh) else 0)
        n += self.mis_en_garajes()
        if n <= 0:
            return ""
        return f" Tienes {'otro vehículo' if n == 1 else f'otros {n} vehículos'}: {'está' if n == 1 else 'están'} en el móvil, en Mis vehículos."

    # ------------------------------------------------------------------ en un servidor
    def sv_mis_vehiculos(self):
        """Los vehículos de la calle que el servidor reconoce como tuyos: [(datos del servidor, vehículo de tu juego o None)]."""
        if not getattr(self, "en_servidor", False):
            return []
        mios = self.sv.setdefault("mios", set())
        fuera = []
        vistos = set()
        for v in self.vehiculos:
            ident = getattr(v, "id_red", None)
            if ident is None or v.muerto:
                continue
            if getattr(v, "red_mio", False) or getattr(v, "red_dueno", False) or ident in mios:
                vistos.add(ident)
                d = self.sv["vehs"].get(ident) or {"id": ident, "modelo": v.modelo["id"], "nombre": v.nombre, "m": self.mundo.id, "x": v.x, "y": v.y, "salud": v.salud}
                fuera.append((d, v))
        for ident in sorted(mios - vistos):
            d = self.sv["vehs"].get(ident)
            if d is not None and d.get("por") is None:
                fuera.append((d, None))
        return fuera

    # ------------------------------------------------------------------ nombre propio
    def renombrar_vehiculo(self, cosa, al_terminar=None):
        """Le pone nombre a un vehículo tuyo. «cosa» es un vehículo de la calle o la ficha de uno guardado."""
        app = self.app
        es_ficha = isinstance(cosa, dict)
        modelo = cosa["modelo"] if es_ficha else cosa.modelo["id"]
        actual = (cosa.get("nombre") if es_ficha else cosa.nombre) or _modelo_nombre(self, modelo)

        def hecho(t):
            t = " ".join(str(t).split())[:NOMBRE_MAX] or _modelo_nombre(self, modelo)
            if t != _modelo_nombre(self, modelo):
                registro.ocultar(t)                              # lo que escribes no se anota en el registro del juego
            if es_ficha:
                cosa["nombre"] = t
            else:
                cosa.nombre = t
                self.hacer_mio(cosa)
            app.son("menu_ok")
            app.decir(f"Ahora se llama {t}." if t != _modelo_nombre(self, modelo) else f"Vuelve a llamarse {t}, como el modelo.", True)
            if al_terminar:
                al_terminar()
        app.abrir(EntradaTexto(app, f"Nombre para {actual}", hecho, inicial="" if actual == _modelo_nombre(self, modelo) else actual, maximo=NOMBRE_MAX,
                               ayuda=f"Hasta {NOMBRE_MAX} letras. El juego lo dirá al subir, al localizarlo y en las listas. Si lo dejas vacío, vuelve a llamarse como el modelo. "
                                     "Tabulador propone nombres al azar. Lo que escribas aquí no se anota en el registro del juego.", propuestas=nombres_propuestos()))

    # ------------------------------------------------------------------ que te lo traigan, o al garaje
    def traer_mi_vehiculo(self, cosa, garaje=None):
        """Tu mecánico te trae un vehículo tuyo: de la calle (de esta localidad o de otra) o de un garaje. Devuelve el vehículo."""
        if self.mundo.tipo == "mar":
            self.app.son("error")
            self.decir("En mitad del mar no te pueden traer un vehículo.", True)
            return None
        if self.j.estrellas > AJUSTES["chofer_busqueda_max"]:
            self.app.son("error")
            self.decir("Con tanta policía buscándote, tu mecánico no se acerca.", True)
            return None
        if isinstance(cosa, dict):
            if garaje is not None and cosa not in self.j.garajes.get(garaje, []):
                return None
            if garaje is None and cosa not in self.mis_lejos:
                return None
        elif cosa.muerto or cosa is self.j.veh:
            return None
        if not self.pagar(self.precio("traer_vehiculo", 150)):
            return None
        x, y, di = self.plaza_cercana()
        if isinstance(cosa, dict):
            (self.j.garajes[garaje] if garaje is not None else self.mis_lejos).remove(cosa)
            v = self._veh_de_dict(dict(cosa, rumbo=di * 90.0), x, y)
            if garaje is None:
                v.mio, v.mio_n = True, int(cosa.get("n", 0) or 0)
            else:
                self.hacer_mio(v)
        else:
            v = cosa
            v.x, v.y, v.dir, v.rumbo, v.vel = x, y, di, di * 90.0, 0.0
        self.son(v.modelo.get("claxon", "claxon"), xy=(x, y))
        self.decir(f"Tu mecánico te deja {v.nombre} en la calle. {self.situar(x, y, 'Está')}.", True)
        return v

    def mandar_al_garaje(self, cosa, casa, cobrar=True):
        """Tu mecánico se lleva a un garaje tuyo un vehículo de la calle. True si se lo ha llevado."""
        g = self.j.garajes.setdefault(casa.id, [])
        if len(g) >= int(casa.get("garaje", 0)):
            self.app.son("error")
            self.decir("Ese garaje está lleno.", True)
            return False
        es_ficha = isinstance(cosa, dict)
        if es_ficha and cosa not in self.mis_lejos:
            return False
        if not es_ficha and (cosa.muerto or cosa.tag or cosa.modelo.get("barco")):
            self.app.son("error")
            self.decir(self.motivo_ajeno(cosa) if not es_ficha and cosa.tag else "Ese vehículo no se puede guardar en un garaje.", True)
            return False
        if cobrar and not self.pagar(self.precio("mandar_vehiculo", 100)):
            return False
        if es_ficha:
            self.mis_lejos.remove(cosa)
            g.append({k: cosa[k] for k in ("modelo", "salud", "nombre", "mejoras", "litros", "km", "pinchada", "revision") if k in cosa})
            nombre = cosa.get("nombre") or _modelo_nombre(self, cosa["modelo"])
        else:
            g.append(self._ficha_garaje(cosa))
            nombre = cosa.nombre
            if self.chofer and self.chofer.get("veh") is cosa:
                self.despedir_chofer(callar=True)
            if self.j.veh is cosa:
                self.salir_vehiculo(forzado=True)
            if self.ultimo_veh is cosa:
                self.ultimo_veh = None
            self.quitar_vehiculo(cosa)
        self.son("arranque", vol=0.6)
        self.decir(f"Tu mecánico se lleva {nombre} al garaje de {self.nombre_lugar(casa)}." + (" Te quedas a pie." if not es_ficha and not self.j.veh else ""), True)
        return True

    def motivo_ajeno(self, v):
        """Por qué no se puede guardar, vender ni mejorar un vehículo que no puede ser tuyo."""
        if v.tag == "banda":
            return "Ese vehículo es de tu banda, y lo lleva tu chófer: no se puede guardar, vender ni mejorar."
        return "Ese vehículo es de una misión: no te lo puedes quedar, ni guardarlo, venderlo o mejorarlo."

    # ------------------------------------------------------------------ misiones
    def mision_vehiculo(self, m):
        """Qué pasa con el vehículo en una misión: (None, None) si no lleva ninguno; si no, («da», «roba», «tuyo» o
        «trae», nombre del vehículo). «da»: te dejan uno. «roba»: hay que llevarse uno concreto. «tuyo»: te dejan uno,
        pero vale el tuyo. «trae»: tienes que venir con uno."""
        for q in m.get("pasos", []):
            if q.get("tipo") == "robar":
                nombre = q.get("nombre") or _modelo_nombre(self, q.get("modelo"))
                if m.get("vehiculo_libre"):
                    return "tuyo", nombre
                return ("da" if q.get("abierto") else "roba"), nombre
            if q.get("tipo") == "carrera":
                return "trae", None
            if q.get("tipo") == "perseguir":                      # hay que alcanzar a un vehículo: sin uno no hay nada que hacer
                return "persigue", q.get("nombre") or _modelo_nombre(self, q.get("modelo"))
        return None, None

    def mision_vehiculo_txt(self, m):
        """La frase que se añade al resumen de una misión, antes de aceptarla."""
        que, nombre = self.mision_vehiculo(m)
        if que == "da":
            return f"Te dan vehículo: {nombre}. El tuyo se queda aparcado y a salvo."
        if que == "roba":
            return f"Hay que llevarse un vehículo concreto: {nombre}. El tuyo se queda aparcado y a salvo."
        if que == "tuyo":
            return f"Te dejan un vehículo, {nombre}, pero puedes hacerla con el tuyo: tú eliges."
        if que == "trae":
            return "Tienes que ir con un vehículo: vale el tuyo."
        if que == "persigue":
            return "Hay una persecución en vehículo: ve con uno rápido, el que tú quieras."
        return ""

    def vale_para_mision(self, v, paso):
        """¿Sirve tu vehículo para una misión que no exige el suyo? Tiene que ser de la misma clase: si el de la misión vuela, el tuyo también."""
        mo = self.modelos.get(paso.get("modelo")) or {}
        return (v is not None and not v.tag and not v.muerto and bool(v.modelo.get("vuela")) == bool(mo.get("vuela"))
                and bool(v.modelo.get("barco")) == bool(mo.get("barco")) and v.modelo.get("motor") != "motor_bici")

    def aviso_vehiculo_mision(self, m, paso):
        """Al empezar el paso en el que la misión te da vehículo: qué pasa con el tuyo. Si llevas uno, o lo acabas de dejar,
        queda a tu nombre para que no se pierda al coger el de la misión."""
        x, y = self.pos()
        v = self.j.veh or self.tu_vehiculo(150) or min((o for o in self.mis_vivos() if o.dist(x, y) < 150), key=lambda o: o.dist(x, y), default=None)
        if m.get("vehiculo_libre") and v is not None and not v.tag and self.vale_para_mision(v, paso):
            self.decir(f"Esta misión se puede hacer con tu vehículo: tú eliges. {'Sigue en' if self.j.veh is v else 'Sube a'} {v.nombre} y detente junto al que te dejan, o coge el que te dejan. "
                       "También vale otro de los tuyos: pídelo en el móvil, en Mis vehículos.")
            return
        if m.get("vehiculo_libre") and not getattr(self, "en_servidor", False) and (self.mis_vivos() or self.mis_en_garajes()):
            self.decir("Esta misión se puede hacer con el vehículo que te dejan o con uno de los tuyos: tú eliges. Para ir con uno tuyo, pídelo en el móvil, en Mis vehículos, y detente con él junto al que te dejan.")
        if v is None or v.tag:
            return
        if getattr(self, "en_servidor", False):
            return
        if self.hacer_mio(v, callar=True):
            self.decir(f"{v.nombre} se queda aparcado y a salvo: lo tienes en el móvil, en Mis vehículos, y desde ahí lo puedes mandar al garaje.")

    # ------------------------------------------------------------------ chófer de la banda
    def chofer_conduce(self):
        c = getattr(self, "chofer", None)
        return bool(c and c["estado"] == "contigo" and self.j.veh is c.get("veh"))

    def chofer_nombre(self):
        return self.chofer["nombre"] if self.chofer else ""

    def _chofer_dice(self, cual, despues=""):
        c = self.chofer
        self.decir(f"{c['nombre']}: {random.choice(LISTAS[cual])}" + (" " + despues if despues else ""))

    def chofer_modelos(self):
        """Los vehículos de la banda con los que puede venir tu chófer, los que digan los datos."""
        return [x for x in LISTAS["chofer_modelos"] if x in self.modelos and not self.modelos[x].get("barco") and not self.modelos[x].get("vuela")] or ["utilitario"]

    def pedir_chofer(self, garaje=None, ficha=None, modelo=None):
        """Pides que alguien de la banda venga a recogerte: con un vehículo de tu garaje (garaje y ficha) o con uno de la
        banda, el que elijas (modelo) o el que tengan a mano."""
        from . import gente
        j = self.j
        motivo = ""
        if not j.banda:
            motivo = "Para tener chófer necesitas a alguien reclutado en tu banda. Se recluta en el móvil, en Territorios, Tu banda."
        elif self.chofer:
            motivo = f"{self.chofer['nombre']} ya está en ello. Si quieres otro, despídelo antes."
        elif self.mundo.tipo == "mar":
            motivo = "En mitad del mar no puede venir nadie a recogerte."
        elif j.estrellas > AJUSTES["chofer_busqueda_max"]:
            motivo = "Con tanta policía buscándote, nadie de la banda se acerca. Despístalos antes."
        elif getattr(self, "pasajero", None) is not None:
            motivo = "Ya vas de pasajero con otro jugador."
        elif ficha is not None and ficha not in j.garajes.get(garaje, []):
            motivo = "Ese vehículo ya no está en el garaje."
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        if not self.pagar(self.precio("chofer", 80)):
            return False
        a, b = sorted((AJUSTES["chofer_espera_min"], AJUSTES["chofer_espera_max"]))
        espera = random.uniform(a, b) * (1.25 if self.lluvia else 1.0) * (0.85 if self.es_noche() else 1.0)      # con lluvia tarda más; de noche hay menos tráfico
        modelos = self.chofer_modelos()
        genero = random.choice("hm")
        self.chofer = {"estado": "espera", "t": espera, "garaje": garaje, "ficha": ficha, "modelo": modelo if modelo in modelos else random.choice(modelos), "veh": None, "propio": False,
                       "nombre": f"{random.choice(gente.nombres(genero))}, de {j.banda_nombre or 'tu banda'}", "intentos": 0, "sin_destino": 0.0}
        cuanto = "menos de un minuto" if espera < 45 else "cosa de un minuto" if espera < 80 else "un par de minutos"
        self.son("movil", cat="interfaz", vol=0.5)
        self._chofer_dice("chofer_frases_sale", f"Tardará {cuanto}. Cuando llegue, oirás el claxon.")
        return True

    def _chofer_sale(self):
        """Se acabó la espera: el vehículo aparece a un par de manzanas y viene hacia ti por la calle."""
        c = self.chofer
        x, y = self.pos()
        pos = self._punto_llegada(x, y)
        if pos is None:
            c["intentos"] += 1
            c["t"] = 6.0
            if c["intentos"] >= 5:
                self.chofer = None
                self.j.dinero += self.precio("chofer", 80)
                self.decir("Tu chófer no encuentra cómo llegar hasta aquí. Te devuelven el dinero.")
            return
        ficha = c["ficha"]
        if ficha is not None and ficha in self.j.garajes.get(c["garaje"], []):
            self.j.garajes[c["garaje"]].remove(ficha)
            v = self._veh_de_dict(dict(ficha, rumbo=pos[2] * 90.0), pos[0], pos[1])
            v.dir = pos[2]
            c["propio"] = True
            self.hacer_mio(v, callar=True)
        else:
            if ficha is not None:
                self.decir(f"{c['nombre']} no ha encontrado ese vehículo en el garaje: viene con uno de la banda.")
            v = self.crear_vehiculo(c["modelo"], pos[0], pos[1], pos[2], None, f"{_modelo_nombre(self, c['modelo'])} de {self.j.banda_nombre or 'tu banda'}", "banda")
            v.propio = True
        v.ia, v.ocupado, v.vel, v.con_chofer = "chofer", True, 9.0, True
        c.update(estado="viene", veh=v, t_limite=self.t + 75.0)
        self.decir(f"{c['nombre']} ya viene con {v.nombre}. {self.situar(v.x, v.y, 'Está')}.")

    def _ia_chofer(self, v, d, dt):
        """El chófer viene a por ti como cualquiera que conoce la ciudad: sin correr, y parando a tu lado."""
        j = self.j
        vel_j = abs(j.veh.vel) if j.veh else 0.0
        if d < 15 and vel_j < 4:
            if v.vel < 1.0:
                self._chofer_llega(v)
            return 0.0, self._decidir_policia
        px, py = self.pos()
        dx, dy = M.DIRS[v.dir]
        a = (px - v.x) * dx + (py - v.y) * dy
        lat = abs((px - v.x) * dy - (py - v.y) * dx)
        if a < -15 and lat < 20 and self.t > v.t_giro:           # te ha pasado de largo: da la vuelta
            v.t_giro = self.t + 3
            v.dir = (v.dir + 2) % 4
        lim = min(v.modelo["vel_max"] * 0.6, 14.0)
        if d < 40:
            lim = min(lim, max(4.0, d * 0.3))
        return lim, self._decidir_policia

    def _chofer_llega(self, v):
        c = self.chofer
        v.ia, v.ocupado, v.vel = None, False, 0.0
        if v.canal:
            v.canal.parar()
            v.canal = None
        c["estado"] = "aqui"
        claxon = v.modelo.get("claxon", "claxon")
        self.son(claxon, xy=(v.x, v.y), ref=8, maxd=120)
        self.son(claxon, xy=(v.x, v.y), ref=8, maxd=120, tono=1.04, vol=0.8)
        if v.sirena is None:
            v.sirena = self.son("loc_vehiculo", bucle=True, xy=(v.x, v.y), ref=5, maxd=70)      # se le oye, para encontrarlo
        self._chofer_dice("chofer_frases_llega", f"{self.situar(v.x, v.y, v.nombre)}. Sube con F.")

    def chofer_al_subir(self, v):
        """Te subes al vehículo que trae el chófer: vas de pasajero. Se llama desde _subir, antes de preparar la conducción."""
        c = self.chofer
        if c and c.get("veh") is v and c["estado"] in ("aqui", "viene"):
            c["estado"] = "contigo"
            c["sin_destino"] = 0.0
            c["tenia_gps"] = None
            return True
        return False

    def chofer_texto_subir(self, v):
        c = self.chofer
        return (f"Subes a {v.nombre} de pasajero: conduce {c['nombre']}. Marca un destino con la L y te lleva. Con Q fijas y con Control disparas. "
                "Con F te bajas, y te espera. Para despedirlo, el móvil, en Servicios.")

    def chofer_tecla(self, k):
        """Las teclas de conducir, cuando conduce el chófer. True si la tecla era de esas."""
        import pygame
        if not self.chofer_conduce() or k not in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_u, pygame.K_y, pygame.K_j, pygame.K_e):
            return False
        self.decir(f"Conduce {self.chofer['nombre']}: tú vas de pasajero. " + (f"Vais a {self.gps['nombre']}." if self.gps else "Marca un destino con la L."), True)
        return True

    def actualizar_chofer(self, dt):
        c = getattr(self, "chofer", None)
        if not c:
            return
        v = c.get("veh")
        if c["estado"] == "espera":
            c["t"] -= dt
            if c["t"] <= 0:
                if not self.j.banda:
                    self.chofer = None
                    self.decir("Ya no queda nadie en tu banda para venir a recogerte.")
                else:
                    self._chofer_sale()
            return
        if v is None or v.muerto or v not in self.vehiculos:
            self.chofer = None
            self.son("notificacion", cat="interfaz", vol=0.5)
            self.decir(f"Te has quedado sin chófer: {c['nombre'].split(',')[0]} y el vehículo ya no están.")
            return
        if c["estado"] == "viene":
            if self.t > c["t_limite"]:                           # se ha liado con el tráfico: aparece en la calle más cercana
                x, y, di = self.plaza_cercana()
                v.x, v.y, v.dir, v.rumbo, v.vel = x, y, di, di * 90.0, 0.0
                self._chofer_llega(v)
        elif c["estado"] == "contigo":
            if self.j.veh is not v:
                c["estado"] = "aqui"
                if v.sirena is None:
                    v.sirena = self.son("loc_vehiculo", bucle=True, xy=(v.x, v.y), ref=5, maxd=70)
                self._chofer_dice("chofer_frases_espera")
                return
            dest = self.gps["dest"] if self.gps else None
            antes = c.get("tenia_gps")
            if dest != antes:
                c["tenia_gps"] = dest
                c["sin_destino"] = 0.0
                if dest is not None:
                    self._chofer_dice("chofer_frases_marcha")
                elif antes is not None and math.hypot(antes[0] - v.x, antes[1] - v.y) < 45:      # el GPS se ha apagado porque habéis llegado
                    self._chofer_dice("chofer_frases_llegada", "Con F te bajas, y te espera.")
                    c["sin_destino"] = 45.0
            if dest is None:
                c["sin_destino"] -= dt
                if c["sin_destino"] <= 0:
                    c["sin_destino"] = 40.0
                    self._chofer_dice("chofer_frases_destino", "La L abre la lista de lugares.")

    def despedir_chofer(self, callar=False):
        """Despides al chófer en cualquier momento. Si el vehículo es tuyo, se queda contigo; si es de la banda, se lo lleva."""
        c = getattr(self, "chofer", None)
        if not c:
            if not callar:
                self.decir("No tienes chófer ahora mismo.", True)
            return False
        self.chofer = None
        v = c.get("veh")
        frase = f"{c['nombre']}: {random.choice(LISTAS['chofer_frases_adios'])} "
        if c["estado"] == "espera" or v is None or v.muerto:
            if not callar:
                self.decir(frase + "Se da la vuelta antes de llegar.", True)
            return True
        v.con_chofer = False
        dentro = self.j.veh is v
        if v.sirena is not None:
            v.sirena.parar()
            v.sirena = None
        if c.get("propio"):
            if not dentro:
                v.ia, v.ocupado, v.vel = None, False, 0.0
                if v.canal:
                    v.canal.parar()
                    v.canal = None
            if not callar:
                self.son("puerta_coche", xy=(v.x, v.y))
                self.decir(frase + (f"Se baja y te deja {v.nombre}: ahora conduces tú." if dentro else f"{v.nombre} se queda aparcado. {self.situar(v.x, v.y, 'Está')}."), True)
            return True
        if dentro:
            self.salir_vehiculo(forzado=True)
        x, y = v.x, v.y
        if self.ultimo_veh is v:
            self.ultimo_veh = None
        self.quitar_vehiculo(v)
        if not callar:
            self.son("arranque", xy=(x, y), vol=0.6)
            self.decir(frase + ("Te deja en la acera y se lleva el vehículo. Te quedas a pie." if dentro else "Se lleva el vehículo."), True)
        return True

    def chofer_al_cambiar_mapa(self):
        """Cambias de localidad: si vas con él, sigue contigo; si no, se vuelve."""
        c = getattr(self, "chofer", None)
        if not c or c["estado"] == "espera" or self.chofer_conduce():
            return
        self.chofer = None
        v = c.get("veh")
        if v is not None:
            v.con_chofer = False
        self.decir(f"{c['nombre'].split(',')[0]} no te sigue a otra localidad" + (f": deja {v.nombre} aparcado donde estaba." if c.get("propio") and v is not None else " y se vuelve con los demás."))


# ====================================================================== menús
def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


def _estado_txt(salud, salud_max):
    return f"estado {int(100 * max(0.0, float(salud)) / max(1.0, float(salud_max)))} por ciento"


def _salud_max(p, modelo_id, mejoras):
    from . import sistemas

    class _V:
        pass
    v = _V()
    v.mejoras = {k: n for k, n in dict(mejoras or {}).items() if k in sistemas.MEJORAS}
    mo = p.modelos.get(modelo_id) or {"salud": 100}
    return float(mo["salud"]) * sistemas.factor_blindaje(v)


def lista_mis_vehiculos(p):
    """Todos tus vehículos, como fichas para el menú: [{"texto", "tipo", ...}]. Tipos: llevas, calle, lejos, garaje, ultimo, servidor."""
    j = p.j
    fichas = []

    def ficha_v(v, tipo, donde, **kw):
        fichas.append(dict(kw, tipo=tipo, veh=v, nombre=v.nombre,
                           texto=f"{nombre_completo(p, v.nombre, v.modelo['id'])}. {donde}. {_estado_txt(v.salud, v.salud_max).capitalize()}. {_mejoras_txt(getattr(v, 'mejoras', {}))}"))

    def ficha_d(d, tipo, donde, **kw):
        nombre = d.get("nombre") or _modelo_nombre(p, d["modelo"])
        smax = _salud_max(p, d["modelo"], d.get("mejoras"))
        fichas.append(dict(kw, tipo=tipo, datos=d, nombre=nombre,
                           texto=f"{nombre_completo(p, nombre, d['modelo'])}. {donde}. {_estado_txt(d.get('salud', smax), smax).capitalize()}. {_mejoras_txt(d.get('mejoras'))}"))

    def en_calle(v):
        return f"En la calle: {p.mundo.describir(v.x, v.y)}, {p.situar(v.x, v.y, 'está').split(', ', 1)[-1]}"

    if getattr(p, "en_servidor", False):
        for d, v in p.sv_mis_vehiculos():
            if v is not None and v is j.veh:
                ficha_v(v, "llevas", "Vas en él")
            elif v is not None:
                ficha_v(v, "servidor", en_calle(v))
            elif d.get("modelo") in p.modelos:
                mapa = p.mapas.get(d.get("m"))
                ficha_d(d, "servidor", f"En la calle, en {mapa.nombre if mapa else 'otra localidad'}")
    else:
        v = j.veh
        if v is not None and not v.tag and not v.modelo.get("barco"):
            ficha_v(v, "llevas", "Vas en él" + ("" if p.es_mio(v) else ", pero todavía no está a tu nombre"))
        for o in p.mis_vivos():
            if o is not v:
                ficha_v(o, "calle", en_calle(o))
        for d in sorted(p.mis_lejos, key=lambda d: int(d.get("n", 0) or 0)):
            if d.get("modelo") in p.modelos:
                mapa = p.mapas.get(d.get("mapa"))
                ficha_d(d, "lejos", f"En la calle, en {mapa.nombre if mapa else 'otra localidad'}: {d.get('donde') or 'donde lo dejaste'}")
        u = p.tu_vehiculo()
        if u is not None and not p.es_mio(u):
            ficha_v(u, "ultimo", en_calle(u) + ". Es el último que has usado y no está a tu nombre: si coges otro, se pierde")
    for pid, lista in j.garajes.items():
        l = p.lug(pid)
        for d in lista:
            if d.get("modelo") in p.modelos:
                ficha_d(d, "garaje", f"En el garaje de {p.nombre_lugar(l) if l else 'una casa'}", garaje=pid)
    return fichas


def menu_mis_vehiculos(p):
    """Móvil, Mis vehículos: todos, dónde está cada uno y qué se puede hacer con él."""
    app, j = p.app, p.j
    servidor = getattr(p, "en_servidor", False)

    def casas():
        return [l for l in (p.lug(pid) for pid in j.propiedades) if l is not None and int(l.get("garaje", 0)) > 0]

    def acciones(f):
        def abrir():
            v, d, tipo = f.get("veh"), f.get("datos"), f["tipo"]
            cosa = v if v is not None else d

            def gps():
                _volver_al_juego(p)
                p.fijar_gps(v.x, v.y, v.nombre)
                p.decir(f"{p.situar(v.x, v.y, v.nombre)}. {p.mundo.describir(v.x, v.y)}. Marcado en el GPS.", True)

            def gps_casa():
                l = p.lug(f["garaje"])
                if l is not None:
                    _volver_al_juego(p)
                    p.gps_a_lugar(l)

            def gps_lejos():
                mapa = p.mapas.get(d.get("mapa"))
                if mapa is None or not mapa.lugares:
                    return
                l = min(mapa.lugares.values(), key=lambda q: math.hypot(q.x - float(d.get("x", 0)), q.y - float(d.get("y", 0))))
                _volver_al_juego(p)
                p.gps_a_lugar(l)                                 # el GPS dice cómo se llega a esa localidad; allí, Mayúsculas L o esta lista

            def traer():
                if p.traer_mi_vehiculo(cosa, f.get("garaje")) is not None:
                    _volver_al_juego(p)

            def al_garaje():
                def llevar(l):
                    def g():
                        if p.mandar_al_garaje(cosa, l):
                            _volver_al_juego(p)
                    return g
                ops = [Opcion(f"{p.nombre_lugar(l)}: {len(j.garajes.get(l.id, []))} de {l.get('garaje', 0)} plazas ocupadas", llevar(l)) for l in casas()]
                app.abrir(Menu(app, f"Mandar {f['nombre']} a un garaje: {p.precio('mandar_vehiculo', 100)} euros", ops or [Opcion("No tienes ninguna casa con garaje")]))

            def renombrar():
                p.renombrar_vehiculo(cosa, lambda: (app.cerrar(mm), m.refrescar(False)))

            def quedar():
                if p.hacer_mio(v):
                    app.son("menu_ok")
                    app.decir(f"{v.nombre} queda a tu nombre: ya no se pierde aunque cojas otro.", True)
                    app.cerrar(mm)
                    m.refrescar(False)

            def chofer():
                if p.pedir_chofer(f["garaje"], d):
                    _volver_al_juego(p)

            # En un servidor, un vehículo tuyo aparcado en la calle lo guarda el servidor: estas tres cosas se le piden a él.
            def sv_datos():
                if d is not None:
                    return d
                return p.sv["vehs"].get(v.id_red) or {"id": v.id_red, "modelo": v.modelo["id"], "nombre": v.nombre, "salud": v.salud, "mejoras": dict(getattr(v, "mejoras", {}) or {})}

            def sv_traer():
                if p.mundo.tipo == "mar":
                    app.son("error")
                    return p.decir("En mitad del mar no te pueden traer un vehículo.", True)
                if j.estrellas > AJUSTES["chofer_busqueda_max"]:
                    app.son("error")
                    return p.decir("Con tanta policía buscándote, tu mecánico no se acerca.", True)
                precio = p.precio("traer_vehiculo", 150)
                if j.dinero < precio:
                    app.son("error")
                    return p.decir(f"No tienes suficiente dinero. Cuesta {precio} euros y tienes {j.dinero}.", True)
                x, y, di = p.plaza_cercana()
                dd = sv_datos()
                if p.sv_veh_orden("traer", dd, x=round(x, 1), y=round(y, 1), r=di * 90):
                    p.sv["veh_pend"][dd["id"]] = {"precio": precio}
                    _volver_al_juego(p)

            def sv_al_garaje():
                dd = sv_datos()
                precio = p.precio("mandar_vehiculo", 100)

                def llevar(l):
                    def g():
                        if len(j.garajes.get(l.id, [])) >= int(l.get("garaje", 0)):
                            app.son("error")
                            return p.decir("Ese garaje está lleno.", True)
                        if j.dinero < precio:
                            app.son("error")
                            return p.decir(f"No tienes suficiente dinero. Cuesta {precio} euros y tienes {j.dinero}.", True)
                        if p.sv_veh_orden("guardar", dd, ref=l.id):
                            p.sv["veh_pend"][dd["id"]] = {"precio": precio, "casa": l.id}
                            _volver_al_juego(p)
                    return g
                if (p.modelos.get(dd.get("modelo")) or {}).get("barco"):
                    app.son("error")
                    return p.decir("Ese vehículo no se puede guardar en un garaje.", True)
                lista = [Opcion(f"{p.nombre_lugar(l)}: {len(j.garajes.get(l.id, []))} de {l.get('garaje', 0)} plazas ocupadas", llevar(l)) for l in casas()]
                app.abrir(Menu(app, f"Mandar {f['nombre']} a un garaje: {precio} euros", lista or [Opcion("No tienes ninguna casa con garaje")]))

            def sv_renombrar():
                dd = sv_datos()

                def hecho(t):
                    t = " ".join(str(t).split())[:NOMBRE_MAX] or _modelo_nombre(p, dd["modelo"])
                    if t != _modelo_nombre(p, dd["modelo"]):
                        registro.ocultar(t)
                    if p.sv_veh_orden("nombre", dd, nombre=t):
                        app.cerrar(mm)
                        m.refrescar(False)
                app.abrir(EntradaTexto(app, f"Nombre para {f['nombre']}", hecho, inicial="" if f["nombre"] == _modelo_nombre(p, dd["modelo"]) else f["nombre"], maximo=NOMBRE_MAX,
                                       ayuda=f"Hasta {NOMBRE_MAX} letras. Lo guarda el servidor y lo ven también los demás jugadores. Si lo dejas vacío, vuelve a llamarse como el modelo. "
                                             "Tabulador propone nombres al azar.", propuestas=nombres_propuestos()))
            ops = []
            if tipo in ("calle", "ultimo") or (tipo == "servidor" and v is not None):
                ops.append(Opcion("Marcarlo en el GPS", gps, ayuda="El GPS te lleva hasta él. Sin abrir el móvil, Mayúsculas L hace lo mismo con el último que has usado."))
            if tipo == "garaje":
                ops.append(Opcion("Marcar en el GPS la casa donde está", gps_casa))
            if tipo == "lejos":
                ops.append(Opcion("Marcar en el GPS el camino hasta su localidad", gps_lejos,
                                  ayuda="El GPS te guía hasta el sitio más cercano a donde lo dejaste. Cuando estés en esa localidad, márcalo otra vez desde esta lista y te lleva hasta el vehículo."))
            if tipo in ("calle", "lejos", "garaje"):
                ops.append(Opcion(f"Pedir que te lo traigan: {p.precio('traer_vehiculo', 150)} euros", traer,
                                  ayuda="Tu mecánico lo deja aparcado en la calle, a tu lado, esté donde esté. No viene si te busca mucho la policía."))
            if tipo == "garaje" and j.banda and not servidor:
                ops.append(Opcion(f"Que venga un chófer de tu banda con él: {p.precio('chofer', 80)} euros", chofer,
                                  ayuda="Alguien de tu banda lo saca del garaje, viene a recogerte y conduce él hasta donde marques en el GPS."))
            if tipo in ("calle", "lejos", "ultimo", "llevas") and not servidor:
                ops.append(Opcion(f"Mandarlo a un garaje: {p.precio('mandar_vehiculo', 100)} euros", al_garaje,
                                  ayuda="Tu mecánico se lo lleva al garaje de la casa que elijas, esté donde esté el vehículo."))
            if tipo == "ultimo" or (tipo == "llevas" and not servidor and not p.es_mio(v)):
                ops.append(Opcion("Ponerlo a tu nombre", quedar, ayuda="Desde ese momento es tuyo: no desaparece al alejarte ni al coger otro, y se guarda con la partida."))
            if not servidor or tipo in ("llevas", "garaje"):
                ops.append(Opcion("Cambiarle el nombre", renombrar, ayuda="El juego dirá ese nombre al subir, al localizarlo y en las listas."))
            if tipo == "servidor":
                viejo = "" if p.sv_sabe("mis_vehiculos") else " Este servidor va con una versión anterior y todavía no sabe hacerlo: al pulsar, el juego te dice qué puedes hacer en su lugar."
                ops += [Opcion(f"Pedir que te lo traigan: {p.precio('traer_vehiculo', 150)} euros", sv_traer,
                               ayuda="Tu mecánico lo deja aparcado en la calle, a tu lado, esté donde esté, también si está en otra localidad. No viene si te busca mucho la policía." + viejo),
                        Opcion(f"Mandarlo a un garaje: {p.precio('mandar_vehiculo', 100)} euros", sv_al_garaje,
                               ayuda="Tu mecánico se lo lleva al garaje de la casa que elijas, y deja de estar en la calle del servidor: ya no caduca ni se lo puede llevar nadie." + viejo),
                        Opcion("Cambiarle el nombre", sv_renombrar, ayuda="El nombre lo guarda el servidor, y lo ven también los demás jugadores." + viejo)]
            ops.append(Opcion(f["texto"]))
            mm = Menu(app, f["nombre"], ops)
            app.abrir(mm)
        return abrir

    def ops():
        fichas = lista_mis_vehiculos(p)
        lista = [Opcion(f["texto"], acciones(f), ayuda="Intro abre lo que puedes hacer con él: marcarlo en el GPS, que te lo traigan, mandarlo a un garaje o cambiarle el nombre.") for f in fichas]
        if not lista:
            lista.append(Opcion("No tienes ningún vehículo. Son tuyos los que compras, los que mejoras en un taller, los que sacas de un garaje y los que bautizas con un nombre"))
        if servidor:
            lista.append(Opcion("En un servidor, los vehículos de la calle los guarda el servidor",
                                ayuda="El servidor recuerda los últimos vehículos que has dejado en la calle, hasta el máximo por jugador que tenga puesto, y durante las horas que tenga puestas. "
                                      "Otro jugador puede llevárselos. Lo que quieras conservar, mételo en un garaje."))
        return lista

    def titulo():
        if servidor:
            return f"Mis vehículos: {len(p.sv_mis_vehiculos())} en la calle del servidor y {p.mis_en_garajes()} en garajes"
        return f"Mis vehículos: {p.mis_en_calle()} en la calle, de {tope()}, y {p.mis_en_garajes()} en garajes"
    m = Menu(app, titulo, ops, intro="Intro sobre un vehículo abre lo que puedes hacer con él")
    app.abrir(m)


def menu_chofer(p):
    """Pedir un chófer de la banda, o despedirlo."""
    app, j = p.app, p.j

    def pedir(garaje=None, ficha=None, modelo=None):
        def f():
            if p.pedir_chofer(garaje, ficha, modelo):
                _volver_al_juego(p)
        return f

    def despedir():
        p.despedir_chofer()
        _volver_al_juego(p)

    def ops():
        c = p.chofer
        if c:
            estado = {"espera": "está en camino", "viene": "está llegando", "aqui": "te espera con el vehículo", "contigo": "va al volante"}[c["estado"]]
            return [Opcion(f"{c['nombre']} {estado}"), Opcion("Despedir al chófer", despedir,
                                                             ayuda="Si el vehículo es tuyo, se queda contigo. Si es de la banda, se lo lleva, y si ibas dentro te deja en la acera.")]
        lista = [Opcion(f"Que venga con un vehículo de la banda: {p.precio('chofer', 80)} euros", pedir(),
                        ayuda="Viene con un coche de la banda, el que tengan a mano. Cuando lo despidas, se lo lleva. Más abajo puedes elegir cuál.")]
        if len(p.chofer_modelos()) > 1:                          # y si quieres uno en concreto de los de la banda, lo eliges
            for mid in p.chofer_modelos():
                lista.append(Opcion(f"Que venga con el {p.modelos[mid]['nombre']} de la banda: {p.precio('chofer', 80)} euros", pedir(modelo=mid),
                                    ayuda=(p.modelos[mid].get("desc", "") + " Cuando despidas al chófer, se lo lleva.").strip()))
        for pid, fichas in j.garajes.items():
            l = p.lug(pid)
            for d in fichas:
                if d.get("modelo") in p.modelos and not p.modelos[d["modelo"]].get("barco") and not p.modelos[d["modelo"]].get("vuela"):
                    lista.append(Opcion(f"Que venga con {nombre_completo(p, d.get('nombre'), d['modelo'])}, del garaje de {p.nombre_lugar(l) if l else 'una casa'}: {p.precio('chofer', 80)} euros",
                                        pedir(pid, d), ayuda="Lo saca de tu garaje. Cuando despidas al chófer, el vehículo se queda contigo, en la calle."))
        return lista
    if not j.banda and not p.chofer:
        app.son("error")
        app.decir("Para tener chófer necesitas a alguien reclutado en tu banda. Se recluta en el móvil, en Territorios, Tu banda.", True)
        return
    app.abrir(Menu(app, "Chófer de tu banda", ops,
                   intro="Viene a recogerte, tú subes de pasajero y él conduce hasta el destino que marques en el GPS. Tarda en llegar según el tráfico"))
