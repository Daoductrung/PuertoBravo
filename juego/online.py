"""Jugar con amigos, dentro de la partida: oír y encontrar a los demás, hablar por texto y enviarse dinero."""
import math

from . import mundo as M
from . import red


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
            return False, "Ya estás conectado."
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
        self.son("amigo_entra", cat="interfaz")
        return True, ("Partida abierta a tus amigos, " + ("protegida con contraseña" if clave else "sin contraseña") + f", en el puerto {srv.puerto}.")

    def unirse_a_amigo(self, texto, clave=""):
        if self.online_activo():
            return False, "Ya estás conectado."
        d = red.analizar_direccion(texto)
        if d is None:
            return False, "No entiendo esa dirección. Tiene que ser como puertobravo, dos puntos, barra, barra, el número de tu amigo, dos puntos y el puerto."
        cli = red.Cliente()
        ok, r = cli.conectar(d[0], d[1], self.nombre_online(), clave)
        if not ok:
            return False, r
        self.red = cli
        self._red_union = (d[0], d[1], clave)        # para volver a entrar solo si se corta
        self.remotos = {}
        for j in r.get("jugadores", []):
            self.remotos[j["id"]] = Remoto(j["id"], j["nombre"])
        self.cfg["red_ultima"] = red.direccion(d[0], d[1])
        self.son("amigo_entra", cat="interfaz")
        quienes = ", ".join(x.nombre for x in self.remotos.values())
        return True, f"Conectado como {cli.nombre}. " + (f"Están: {quienes}." if quienes else "De momento no hay nadie más.")

    def desconectar_online(self, motivo=None):
        for r in getattr(self, "remotos", {}).values():
            r.callar()
        self.remotos = {}
        era = getattr(self, "red", None) is not None or self.es_anfitrion()
        if getattr(self, "red", None) is not None:
            self.red.cerrar()
            self.red = None
        if getattr(self, "servidor", None) is not None:
            self.servidor.detener()
            self.servidor = None
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
            self.decir("No estás conectado con nadie.", True)
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
            cli.enviar({"t": "estado", "e": {"m": self.mundo.id, "x": round(x, 1), "y": round(y, 1), "r": round(v.rumbo if v else self.j.rumbo, 0),
                                               "v": v.modelo["id"] if v else None, "s": round(abs(v.vel), 1) if v else 0.0}})
        for _ in range(60):
            if getattr(self, "red", None) is not cli:
                break                              # un mensaje anterior nos ha desconectado
            try:
                m = cli.entrantes.get_nowait()
            except Exception:
                break
            self._red_mensaje(m)
        if getattr(self, "red", None) is not None:
            self._red_sonidos(dt)

    def _red_mensaje(self, m):
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
            self.remotos[m["id"]] = Remoto(m["id"], str(m.get("nombre", "Invitado")))
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
            self.decir(f"{m.get('nombre', 'Alguien')} dice: {m.get('texto', '')}")
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
            elif math.hypot(r.tx - r.x, r.ty - r.y) > 0.25:
                r.t_paso -= dt
                if r.t_paso <= 0:
                    r.t_paso = 0.45
                    self.son("paso_npc", xy=(r.x, r.y), ref=4, maxd=40, vol=0.7)
