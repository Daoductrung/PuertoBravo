"""Jugar con amigos, dentro de la partida: oír y encontrar a los demás, hablar por texto y enviarse dinero."""
import math

from . import mundo as M
from . import red
from . import registro


class Remoto:
    """Otro jugador conectado. Se comporta como algo más del mundo: el radar lo anuncia y el GPS puede ir hasta él."""
    tipo = "jugador"
    muerto = False
    hostil = False

    def __init__(self, ident, nombre):
        self.id = ident
        self.nombre = nombre
        self.mapa = None
        self.x = self.y = 0.0
        self.tx = self.ty = 0.0
        self.rumbo = 0.0
        self.veh = None            # identificador del modelo que conduce, o None si va a pie
        self.vel = 0.0
        self.canal = None
        self.t_paso = 0.0
        self.visto = False
        self.aspecto = ""          # lo que lleva puesto, como lo cuenta su juego
        self.pasajero_de = None    # en un servidor: id del jugador en cuyo vehículo va de pasajero
        self.radio = ""            # en un servidor: la emisora del juego que lleva puesta en su vehículo
        self.ficha = ""            # en un servidor: su frase de rol, cuando la has pedido

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def callar(self):
        if self.canal is not None:
            self.canal.parar()
            self.canal = None


class Online:
    """Mixin de Partida."""

    def online_iniciar(self):
        self._red_union = None
        self._red_reintentando = False
        self.red = None
        self.servidor = None
        self.remotos = {}
        self.t_red = 0.0
        self.chat = []             # últimos mensajes, para repasarlos
        self.coop = None           # actividad conjunta propuesta o en marcha
        self.pasajero = None       # id del amigo en cuyo vehículo vas

    def online_activo(self):
        return getattr(self, "red", None) is not None and self.red.conectado

    def es_anfitrion(self):
        return getattr(self, "servidor", None) is not None

    def nombre_online(self):
        return (self.cfg["red_nombre"] or self.j.nombre)[:24]

    # ------------------------------------------------------------ conectar
    def abrir_a_amigos(self, puerto=None, clave=""):
        """Arranca el servidor en este ordenador y entra en él como un jugador más."""
        if self.online_activo():
            return False, "Ya tienes una conexión abierta."
        puerto = puerto or self.cfg["red_puerto"]
        srv = red.Servidor(puerto, clave)
        try:
            srv.iniciar()
        except OSError:
            return False, f"No se pudo abrir el puerto {puerto}. Puede que lo esté usando otro programa: prueba con otro número."
        cli = red.Cliente()
        ok, r = cli.conectar("127.0.0.1", srv.puerto, self.nombre_online(), clave)
        if not ok:
            srv.detener()
            return False, r
        self.servidor, self.red = srv, cli
        self.remotos = {}
        if self.cfg["red_nombre"]:
            registro.ocultar(self.cfg["red_nombre"])
        registro.info("red", "Abre su partida a los amigos", con_clave=bool(clave), puerto=srv.puerto)
        self.son("amigo_entra", cat="interfaz")
        self._upnp = None
        self._upnp_aviso = None
        if self.cfg["red_upnp"] and (not self.app.pruebas or getattr(self, "upnp_en_pruebas", None)):
            # en segundo plano: preguntar al router tarda un par de segundos y el juego no debe pararse
            import threading

            def intentar(puerto=srv.puerto):
                from . import upnp
                ok, datos, motivo = upnp.abrir(puerto, buscar=getattr(self, "upnp_en_pruebas", None) or upnp.descubrir)
                self._upnp = datos
                self._upnp_aviso = upnp.FRASES.get(motivo, upnp.FRASES["rechazado"])
                registro.info("red", "Apertura automática del puerto", conseguido=ok, motivo=motivo)
            self._upnp_hilo = threading.Thread(target=intentar, daemon=True)
            self._upnp_hilo.start()
        return True, ("Partida abierta a tus amigos, " + ("protegida con contraseña" if clave else "sin contraseña") + f", en el puerto {srv.puerto}.")

    def unirse_a_amigo(self, texto, clave=""):
        if self.online_activo():
            return False, "Ya tienes una conexión abierta."
        d = red.analizar_direccion(texto)
        if d is None:
            return False, "No entiendo esa dirección. Tiene que ser como puertobravo, dos puntos, barra, barra, el número de tu amigo, dos puntos y el puerto."
        if self.cfg["red_nombre"]:
            registro.ocultar(self.cfg["red_nombre"])
        cli = red.Cliente()
        ok, r = cli.conectar(d[0], d[1], self.nombre_online(), clave)
        registro.info("red", "Intenta unirse a una partida", conseguido=ok, con_clave=bool(clave), motivo="" if ok else r)
        if not ok:
            return False, r
        self.red = cli
        self._red_union = (d[0], d[1], clave)        # para volver a entrar solo si se corta
        self.remotos = {}
        for j in r.get("jugadores", []):
            registro.ocultar(j["nombre"])
            self.remotos[j["id"]] = Remoto(j["id"], j["nombre"])
        self.cfg["red_ultima"] = red.direccion(d[0], d[1])
        self.son("amigo_entra", cat="interfaz")
        quienes = ", ".join(x.nombre for x in self.remotos.values())
        return True, f"Conectado como {cli.nombre}. " + (f"Están: {quienes}." if quienes else "De momento no hay nadie más.")

    def desconectar_online(self, motivo=None):
        for r in getattr(self, "remotos", {}).values():
            r.callar()
        self.remotos = {}
        self.coop = None
        self.pasajero = None
        era = getattr(self, "red", None) is not None or self.es_anfitrion()
        if getattr(self, "red", None) is not None:
            self.red.cerrar()
            self.red = None
        if getattr(self, "servidor", None) is not None:
            self.servidor.detener()
            self.servidor = None
            datos, self._upnp = getattr(self, "_upnp", None), None
            if datos:                                        # el puerto que se abrió en el router se vuelve a cerrar
                import threading
                from . import upnp
                threading.Thread(target=upnp.cerrar, args=(datos,), daemon=True).start()
        if era:
            registro.info("red", "Se desconecta de la partida en red", motivo=motivo or "a petición propia")
        if era and motivo:
            self.son("amigo_sale", cat="interfaz")
            self.decir(motivo)

    # ------------------------------------------------------------ acciones
    def enviar_chat(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return
        if not self.online_activo():
            self.app.son("error")
            self.decir("No tienes conexión con nadie.", True)
            return
        self.red.enviar({"t": "chat", "texto": texto[:300]})
        self.chat.append(f"Tú: {texto}")
        del self.chat[:-30]
        self.son("chat", cat="interfaz", vol=0.6)
        self.decir("Enviado.", True)

    def enviar_evento(self, que):
        if self.online_activo():
            self.red.enviar({"t": "evento", "que": que})

    def dar_dinero_a(self, remoto, n):
        if not self.online_activo() or remoto.id not in self.remotos:
            return False
        if not self.pagar(n):
            return False
        self.red.enviar({"t": "dinero", "a": remoto.id, "n": n})
        self.decir(f"Envías {n} euros a {remoto.nombre}. Te quedan {self.j.dinero}.", True)
        return True

    def donde_esta(self, r):
        """Texto con dónde está otro jugador respecto a ti."""
        if r.mapa is None:
            return f"{r.nombre}, todavía sin situar"
        como = "al volante" if r.veh else "a pie"
        if r.mapa != self.mundo.id:
            m = self.mapas.get(r.mapa)
            return f"{r.nombre}, {como}, en {m.nombre if m else 'otra localidad'}"
        x, y = self.pos()
        return f"{r.nombre}, {como}, {M.metros(r.dist(x, y))}, {self.direccion_txt(r.x, r.y)}"

    def gps_a_amigo(self, r):
        if r.mapa is None:
            self.decir(f"Aún no sé dónde está {r.nombre}.", True)
        elif r.mapa == self.mundo.id:
            self.fijar_gps(r.x, r.y, r.nombre)
            self.decir(f"GPS hacia {r.nombre}. Si se mueve, vuelve a marcarlo.")
        else:
            m = self.mapas.get(r.mapa)
            cerca = min(m.lugares.values(), key=lambda l: math.hypot(l.x - r.x, l.y - r.y), default=None) if m else None
            if cerca is None:
                self.decir(f"{r.nombre} está en una localidad que no tienes en tu juego.", True)
            else:
                self.gps_a_lugar(cerca)

    # ---------------------------------------------------------- cada fotograma
    # ------------------------------------------------------- cómo va vestido cada uno
    def aspecto_corto(self):
        """Lo que llevas puesto, para contárselo a los demás: «cazadora de cuero, con gafas de sol y cadena de oro»."""
        t = self.aspecto_txt()
        return t.split(": ", 1)[-1].rstrip(".")[:200]

    def _contar_aspecto(self, dt):
        """Tu juego cuenta lo que llevas solo al entrar, cuando te cambias y cuando llega alguien nuevo: no en cada envío."""
        self._t_aspecto = getattr(self, "_t_aspecto", 0.0) - 0.1
        if self._t_aspecto > 0:
            return
        self._t_aspecto = 3.0
        texto = self.aspecto_corto()
        if texto == getattr(self, "_aspecto_enviado", None):
            return
        self._aspecto_enviado = texto
        if getattr(self, "en_servidor", False):
            self.red.enviar({"t": "aspecto", "texto": texto})
        else:
            self.red.enviar({"t": "act", "d": {"que": "aspecto", "texto": texto}})

    def _aspecto_recibido(self, ident, texto):
        r = self.remotos.get(ident)
        if r is not None:
            r.aspecto = "".join(c for c in str(texto or "") if c.isprintable())[:200]

    def mirar_jugador(self):
        """Mayúsculas J: cómo va vestido el jugador que tienes más cerca. Solo cuando lo pides."""
        if not self.online_activo():
            self.decir("Esto dice cómo va vestido otro jugador, cuando juegas con amigos o en un servidor.", True)
            return None
        x, y = self.pos()
        cerca = [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and not getattr(r, "ia", False) and r.dist(x, y) <= 25]
        if not cerca:
            self.decir("No tienes a ningún jugador cerca.", True)
            return None
        r = min(cerca, key=lambda o: o.dist(x, y))
        donde = f", a {M.metros(r.dist(x, y))}"
        if r.veh:
            self.decir(f"{r.nombre}{donde}, va en un vehículo." + (f" Lleva {r.aspecto}." if r.aspecto else ""), True)
        elif r.aspecto:
            self.decir(f"{r.nombre}{donde}, lleva {r.aspecto}.", True)
        else:
            self.decir(f"{r.nombre}{donde}. Su juego no ha dicho cómo va vestido.", True)
        if getattr(self, "en_servidor", False):                 # y si el servidor tiene fichas de rol, la suya, a continuación
            self.sv_pedir_ficha(r, de_paso=True)
        return r

    def red_paso(self, dt):
        """Se llama siempre, también con un menú abierto: los amigos no se quedan esperando."""
        if getattr(self, "red", None) is None:
            return
        cli = self.red
        self.t_red += dt
        if self.t_red >= 0.1 and cli.conectado:
            self.t_red = 0.0
            x, y = self.pos()
            v = self.j.veh
            e = {"m": self.mundo.id, "x": round(x, 1), "y": round(y, 1), "r": round(v.rumbo if v else self.j.rumbo, 0),
                 "v": v.modelo["id"] if v else None, "s": round(abs(v.vel), 1) if v else 0.0}
            if getattr(self, "en_servidor", False):
                e.update(self.sv_estado())
            self._contar_aspecto(dt)
            cli.enviar({"t": "estado", "e": e})
        for _ in range(60):
            if getattr(self, "red", None) is not cli:
                break                              # un mensaje anterior nos ha desconectado
            try:
                m = cli.entrantes.get_nowait()
            except Exception:
                break
            self._red_mensaje(m)
        if getattr(self, "red", None) is not None:
            self.sv_paso(dt)
            self._red_sonidos(dt)
            self._coop_paso()
            self._pasajero_paso()

    def _red_mensaje(self, m):
        if self.sv_mensaje(m):                 # en un servidor, casi todo lo atiende el modo en línea
            return
        t = m.get("t")
        if t == "estados":
            for clave, e in (m.get("e") or {}).items():
                try:
                    ident = int(clave)
                except ValueError:
                    continue
                if ident == self.red.id or not isinstance(e, dict):
                    continue
                r = self.remotos.get(ident)
                if r is None:
                    continue
                try:
                    r.tx, r.ty = float(e.get("x") or 0), float(e.get("y") or 0)
                    r.rumbo, r.vel = float(e.get("r") or 0), float(e.get("s") or 0)
                except (TypeError, ValueError):
                    continue
                if e.get("m") != r.mapa or not r.visto:
                    r.x, r.y = r.tx, r.ty          # primera vez o cambio de localidad: sin deslizamiento
                    r.visto = True
                r.mapa = e.get("m")
                r.veh = e.get("v") if e.get("v") in self.modelos else ("utilitario" if e.get("v") else None)
        elif t == "entra":
            registro.ocultar(m.get("nombre"))
            self.remotos[m["id"]] = Remoto(m["id"], str(m.get("nombre", "Invitado")))
            registro.info("red", "Entra un jugador", ahora=len(self.remotos) + 1)
            self._aspecto_enviado = None                        # que el que llega sepa también cómo vas
            self.son("amigo_entra", cat="interfaz")
            self.decir(f"{m.get('nombre', 'Alguien')} se ha unido a la partida.")
        elif t == "sale":
            r = self.remotos.pop(m.get("id"), None)
            if r:
                r.callar()
                self.son("amigo_sale", cat="interfaz")
                self.decir(f"{r.nombre} se ha ido.")
        elif t == "chat":
            linea = f"{m.get('nombre', 'Alguien')}: {m.get('texto', '')}"
            self.chat.append(linea)
            del self.chat[:-30]
            self.son("chat", cat="interfaz")
            with registro.privado():           # los mensajes del chat no se registran
                self.decir(f"{m.get('nombre', 'Alguien')} dice: {m.get('texto', '')}")
            registro.info("red", "Llega un mensaje de chat", letras=len(str(m.get("texto", ""))))
        elif t == "act" and (m.get("d") or {}).get("que") == "aspecto":
            self._aspecto_recibido(m.get("de"), (m.get("d") or {}).get("texto"))
        elif t == "act":
            self._coop_mensaje(m.get("de"), str(m.get("nombre", "Alguien")), m.get("d") or {})
        elif t == "evento":
            r = self.remotos.get(m.get("de"))
            if r and r.mapa == self.mundo.id and m.get("que") == "claxon":
                modelo = self.modelos.get(r.veh or "utilitario", {})
                self.son(modelo.get("claxon", "claxon"), xy=(r.x, r.y), ref=10, maxd=220, vol=0.8)
        elif t == "dinero":
            try:
                n = max(0, int(m.get("n", 0)))
            except (TypeError, ValueError):
                n = 0
            if n:
                self.j.dinero += n
                self.son("dinero", cat="interfaz")
                self.decir(f"{m.get('nombre', 'Alguien')} te envía {n} euros. Tienes {self.j.dinero}.")
        elif t == "expulsado":
            self._red_union = None
            self.desconectar_online("El anfitrión te ha sacado de la partida.")
        elif t == "cerrado":
            self._red_union = None
            self.desconectar_online("El anfitrión ha cerrado la partida.")
        elif t == "desconectado":
            registro.aviso("red", "Se ha cortado la conexión", anfitrion=self.es_anfitrion())
            union = getattr(self, "_red_union", None)
            if union and not self.es_anfitrion() and not getattr(self, "_red_reintentando", False):
                # un corte suelto (wifi, un filtro de red): se intenta volver a entrar una vez, sin molestar
                self._red_reintentando = True
                self.desconectar_online()
                ok, _ = self.unirse_a_amigo(red.direccion(union[0], union[1]), union[2])
                self._red_reintentando = False
                if ok:
                    self.decir("La conexión con tu amigo se cortó un momento y ya está recuperada.")
                    return
            self._red_union = None
            self.son("amigo_sale", cat="interfaz")
            self.decir("Se ha perdido la conexión con la partida de tu amigo. " + red.AVISO_FILTROS)
            self.desconectar_online()

    def _red_sonidos(self, dt):
        """Los demás suenan en su sitio: el motor de lo que conducen, o sus pasos."""
        x, y = self.pos()
        for r in self.remotos.values():
            f = min(1.0, dt * 8.0)
            r.x += (r.tx - r.x) * f
            r.y += (r.ty - r.y) * f
            cerca = r.mapa == self.mundo.id and r.visto and r.dist(x, y) < 160
            if not cerca or not r.veh:
                r.callar()
            if not cerca:
                continue
            if r.veh:
                modelo = self.modelos[r.veh]
                if r.canal is None:
                    r.canal = self.son(modelo.get("motor", "motor_coche"), bucle=True, xy=(r.x, r.y), ref=7, maxd=160, vol=0.6)
                r.canal.mover(r.x, r.y)
                r.canal.tono(modelo.get("tono", 1.0) * (0.6 + 1.3 * min(1.0, r.vel / max(1.0, modelo.get("vel_max", 25)))))
            elif math.hypot(r.tx - r.x, r.ty - r.y) > 0.25 and getattr(r, "pasajero_de", None) is None:      # quien va de pasajero no da pasos
                r.t_paso -= dt
                if r.t_paso <= 0:
                    r.t_paso = 0.45
                    self.son("paso_npc", xy=(r.x, r.y), ref=4, maxd=40, vol=0.7)

    # ------------------------------------------------------ actividades conjuntas
    def _act(self, **d):
        if self.online_activo():
            self.red.enviar({"t": "act", "d": d})

    def coop_txt(self):
        c = self.coop
        if not c:
            return "No hay ninguna actividad conjunta"
        que = f"Carrera hasta {c['destino']} con {c['apuesta']} euros de apuesta" if c["tipo"] == "carrera" else f"Reparto en equipo: quedan {len(c['restantes'])} entregas"
        fase = {"propuesta": "propuesta por " + c["nombre"], "marcha": "en marcha"}[c["estado"]]
        return f"{que}, {fase}. Participantes: {len(c['participantes'])}"

    def proponer_carrera(self, lugar, apuesta=100):
        """Una carrera entre amigos hasta un lugar: quien llega primero se lleva las apuestas."""
        if not self.online_activo() or not self.remotos:
            return False, "Necesitas al menos un amigo conectado."
        if self.coop:
            return False, "Ya hay una actividad propuesta o en marcha."
        if self.j.dinero < apuesta:
            return False, f"No tienes los {apuesta} euros de la apuesta."
        self.coop = {"tipo": "carrera", "de": self.red.id, "nombre": "ti", "lugar": lugar.id, "mapa": lugar.mapa, "destino": self.nombre_lugar(lugar),
                     "apuesta": apuesta, "estado": "propuesta", "participantes": {self.red.id}, "restantes": []}
        self._act(que="propuesta", tipo="carrera", lugar=lugar.id, mapa=lugar.mapa, apuesta=apuesta)
        return True, f"Propones una carrera hasta {lugar.nombre} con {apuesta} euros de apuesta. Cuando tus amigos acepten, dale a Empezar."

    def proponer_reparto(self):
        """Reparto en equipo: cuatro entregas por la localidad. Entre todos, contrarreloj; si se completa, cobran todos."""
        import random
        if not self.online_activo() or not self.remotos:
            return False, "Necesitas al menos un amigo conectado."
        if self.coop:
            return False, "Ya hay una actividad propuesta o en marcha."
        cand = [l for l in self.mundo.lugares.values() if l.tipo in ("tienda", "comida", "taberna", "farmacia", "banco", "hotel", "gimnasio", "armeria", "taller")]
        if len(cand) < 4:
            return False, "En esta localidad no hay sitios suficientes para un reparto."
        elegidos = [l.id for l in random.sample(cand, 4)]
        self.coop = {"tipo": "reparto", "de": self.red.id, "nombre": "ti", "mapa": self.mundo.id, "destino": self.mundo.nombre, "apuesta": 0,
                     "estado": "propuesta", "participantes": {self.red.id}, "restantes": elegidos, "lugar": None}
        self._act(que="propuesta", tipo="reparto", lugares=elegidos, mapa=self.mundo.id)
        return True, f"Propones un reparto en equipo en {self.mundo.nombre}: cuatro entregas en seis minutos. Cuando tus amigos acepten, dale a Empezar."

    def aceptar_coop(self):
        c = self.coop
        if not c or c["estado"] != "propuesta" or self.red.id in c["participantes"]:
            return False, "No hay nada que aceptar."
        if c["apuesta"] and self.j.dinero < c["apuesta"]:
            return False, f"No tienes los {c['apuesta']} euros de la apuesta."
        c["participantes"].add(self.red.id)
        self._act(que="acepto")
        return True, "Aceptado. Empezará cuando lo diga quien lo ha propuesto."

    def empezar_coop(self):
        c = self.coop
        if not c or c["de"] != self.red.id or c["estado"] != "propuesta":
            return False, "Solo puede empezarla quien la ha propuesto."
        if len(c["participantes"]) < 2:
            return False, "Todavía no ha aceptado nadie."
        self._act(que="salida", participantes=sorted(c["participantes"]))
        self._coop_salida(sorted(c["participantes"]))
        return True, ""

    def cancelar_coop(self):
        if self.coop:
            self._act(que="cancelada")
            self.coop = None
            self.cancelar_gps()
            self.decir("Actividad cancelada.", True)

    def _coop_salida(self, participantes):
        c = self.coop
        c["participantes"] = set(participantes)
        if self.red.id not in c["participantes"]:
            self.coop = None
            return
        c["estado"] = "marcha"
        c["t0"] = self.t
        self.son("mision_ok", cat="interfaz", vol=0.5)
        if c["tipo"] == "carrera":
            self.j.dinero -= min(self.j.dinero, c["apuesta"])
            l = self.lugares.get(c["lugar"])
            if l is not None:
                self.gps_a_lugar(l, callar=True)
            self.decir(f"¡Salida! Carrera hasta {c['destino']}. Hay {c['apuesta'] * len(c['participantes'])} euros en juego.", True)
        else:
            self._coop_gps_reparto()
            self.decir(f"¡En marcha! Cuatro entregas en {c['destino']} en seis minutos. Repartíos: cada uno a la que tenga más cerca.", True)

    def _coop_gps_reparto(self):
        import math
        c = self.coop
        x, y = self.pos()
        aqui = [self.lugares[i] for i in c["restantes"] if i in self.lugares and self.lugares[i].mapa == self.mundo.id]
        if aqui:
            self.gps_a_lugar(min(aqui, key=lambda l: math.hypot(l.x - x, l.y - y)), callar=True)

    def _coop_mensaje(self, de, nombre, d):
        que = d.get("que")
        c = self.coop
        if que == "propuesta" and c is None:
            if d.get("tipo") == "carrera":
                l = self.lugares.get(d.get("lugar"))
                if l is None:
                    return
                try:
                    apuesta = max(0, min(5000, int(d.get("apuesta", 0))))
                except (TypeError, ValueError):
                    return
                self.coop = {"tipo": "carrera", "de": de, "nombre": nombre, "lugar": l.id, "mapa": l.mapa, "destino": self.nombre_lugar(l), "apuesta": apuesta,
                             "estado": "propuesta", "participantes": {de}, "restantes": []}
                texto = f"{nombre} propone una carrera hasta {self.nombre_lugar(l)} con {apuesta} euros de apuesta."
            elif d.get("tipo") == "reparto":
                lugares = [i for i in (d.get("lugares") or []) if i in self.lugares][:8]
                if not lugares:
                    return
                mapa = self.mapas.get(d.get("mapa"))
                self.coop = {"tipo": "reparto", "de": de, "nombre": nombre, "mapa": d.get("mapa"), "destino": mapa.nombre if mapa else "otra localidad", "apuesta": 0,
                             "estado": "propuesta", "participantes": {de}, "restantes": lugares, "lugar": None}
                texto = f"{nombre} propone un reparto en equipo en {self.coop['destino']}."
            else:
                return
            self.son("evento", cat="interfaz")
            self.decir(texto + " Para aceptar, abre el móvil con M y entra en Jugar con amigos.")
        elif que in ("sube", "baja"):
            if d.get("a") == self.red.id and getattr(self, "en_servidor", False):      # quién va contigo: a tus pasajeros no los atropellas
                (self.sv["pasajeros"].add if que == "sube" else self.sv["pasajeros"].discard)(de)
            if d.get("a") == self.red.id:
                self.son("puerta_coche", vol=0.7)
                self.decir(f"{nombre} {'sube a tu vehículo' if que == 'sube' else 'se baja de tu vehículo'}.")
        elif que == "regalo":
            if d.get("a") == self.red.id and d.get("cosa") == "botiquin":
                self.j.objetos["botiquin"] = self.j.objetos.get("botiquin", 0) + 1
                self.son("recoger", cat="interfaz")
                self.decir(f"{nombre} te da un botiquín. Tienes {self.j.objetos['botiquin']}.")
        elif c is None:
            return
        elif que == "acepto" and c["estado"] == "propuesta":
            c["participantes"].add(de)
            self.son("chat", cat="interfaz")
            self.decir(f"{nombre} acepta. Ya sois {len(c['participantes'])}.")
        elif que == "salida" and de == c["de"] and c["estado"] == "propuesta":
            try:
                participantes = [int(x) for x in d.get("participantes") or []]
            except (TypeError, ValueError):
                participantes = list(c["participantes"])
            self._coop_salida(participantes)
        elif que == "meta" and c["estado"] == "marcha" and c["tipo"] == "carrera":
            self.coop = None
            self.cancelar_gps()
            self.son("mision_fallo", cat="interfaz", vol=0.5)
            self.decir(f"{nombre} ha llegado primero y se lleva las apuestas.")
        elif que == "punto" and c["estado"] == "marcha" and c["tipo"] == "reparto":
            self._coop_punto(d.get("lugar"), nombre)
        elif que == "cancelada" and de == c["de"]:
            self.coop = None
            self.cancelar_gps()
            self.decir(f"{nombre} ha cancelado la actividad.")

    def _coop_punto(self, lugar_id, quien):
        c = self.coop
        if lugar_id not in c["restantes"]:
            return
        c["restantes"].remove(lugar_id)
        l = self.lugares.get(lugar_id)
        self.son("llegada", cat="interfaz")
        if c["restantes"]:
            self.decir(f"{quien} entrega en {l.nombre if l else 'un punto'}. Quedan {len(c['restantes'])}.")
            if self.red.id in c["participantes"]:
                self._coop_gps_reparto()
            return
        premio = self.precio("reparto_equipo", 250) + self.precio("reparto_equipo_jugador", 50) * len(c["participantes"])
        self.coop = None
        self.cancelar_gps()
        self.son("mision_ok", cat="interfaz")
        self.dar_dinero(premio)
        self.cambiar_ciudadania(2.0)
        self.j.stats["coop"] = self.j.stats.get("coop", 0) + 1
        self.decir(f"¡Reparto completado entre todos! Cobráis {premio} euros cada uno.")

    def _coop_paso(self):
        import math
        c = self.coop
        if not c or c["estado"] != "marcha" or self.red.id not in c["participantes"]:
            return
        x, y = self.pos()
        if c["tipo"] == "carrera":
            l = self.lugares.get(c["lugar"])
            if l is not None and l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) < 25:
                bote = c["apuesta"] * len(c["participantes"])
                self._act(que="meta")
                self.coop = None
                self.cancelar_gps()
                self.son("mision_ok", cat="interfaz")
                self.dar_dinero(bote)
                self.j.stats["coop"] = self.j.stats.get("coop", 0) + 1
                self.decir(f"¡Has ganado la carrera! Te llevas {bote} euros.")
        else:
            if self.t - c.get("t0", self.t) > 360:
                self._act(que="cancelada") if c["de"] == self.red.id else None
                self.coop = None
                self.cancelar_gps()
                self.son("mision_fallo", cat="interfaz")
                self.decir("Se acabó el tiempo del reparto. Otra vez será.")
                return
            for i in list(c["restantes"]):
                l = self.lugares.get(i)
                if l is not None and l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) < 20:
                    self._act(que="punto", lugar=i)
                    self._coop_punto(i, "Tú")
                    break

    # ------------------------------------------------------------- ir de pasajero
    def subir_con_amigo(self):
        """A pie, junto al vehículo parado de un amigo: subes de pasajero y él te lleva."""
        if not self.online_activo() or self.j.veh:
            return False
        x, y = self.pos()
        cerca = [r for r in self.remotos.values() if r.veh and r.visto and r.mapa == self.mundo.id and r.dist(x, y) < 8 and r.vel < 3]
        if not cerca:
            return False
        r = min(cerca, key=lambda r: r.dist(x, y))
        self.pasajero = r.id
        self.parar_paseo()
        self.son("puerta_coche", vol=0.8)
        self._act(que="sube", a=r.id)
        self.decir(f"Subes de pasajero con {r.nombre}. Pulsa F para bajarte cuando pare.", True)
        return True

    def bajar_de_amigo(self, motivo=None):
        r = self.remotos.get(self.pasajero)
        self.pasajero = None
        self.j.x, self.j.y = self.mundo.punto_libre(self.j.x + 2, self.j.y + 2)
        self.son("puerta_coche", vol=0.8)
        if r is not None:
            self._act(que="baja", a=r.id)
        self.decir(motivo or "Te bajas.", True)

    def _pasajero_paso(self):
        if self.pasajero is None:
            return
        r = self.remotos.get(self.pasajero)
        if r is None or not r.veh:
            self.bajar_de_amigo("Tu amigo ha dejado el vehículo y te bajas.")
            return
        if r.mapa != self.mundo.id and r.mapa in self.mapas:
            self.cambiar_mapa(r.mapa, r.tx, r.ty)
        self.j.x, self.j.y = r.x, r.y

    def dar_botiquin_a(self, remoto):
        j = self.j
        if j.objetos.get("botiquin", 0) < 1:
            self.app.son("error")
            self.decir("No te queda ningún botiquín.", True)
            return False
        j.objetos["botiquin"] -= 1
        self._act(que="regalo", a=remoto.id, cosa="botiquin")
        self.decir(f"Le das un botiquín a {remoto.nombre}. Te quedan {j.objetos['botiquin']}.", True)
        return True
