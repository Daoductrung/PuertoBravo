"""Jugar con amigos: servidor que monta el propio jugador y cliente para unirse.

No hay ningún servidor central. Quien quiere invitar abre su partida desde el móvil del juego: el propio
juego arranca un pequeño servidor en su ordenador y él sigue jugando con normalidad, conectado a su propio
servidor como uno más. A sus amigos les da una dirección, del tipo puertobravo://83.45.12.7:47810, y ellos
la escriben en «Unirme a la partida de un amigo».

El servidor puede dejarse abierto o protegerse con una contraseña, y el anfitrión puede expulsar a quien quiera.

Qué se comparte: dónde está cada jugador y en qué va, para oírle y encontrarle; los mensajes de texto, que se
leen en voz alta; el claxon; y el dinero que se envíen. Cada jugador conserva su propia partida y su progreso.

Protocolo: TCP, una línea de JSON por mensaje. La conexión no va cifrada: no escribas por el chat nada que
no dirías en voz alta. Usa solo la biblioteca estándar.
"""
from .i18n import tr
import hashlib
import hmac
import json
import queue
import socket
import threading
import time

PUERTO = 47810
VERSION_RED = 1
MAX_LINEA = 65536
PREFIJO = "puertobravo://"
AVISO_FILTROS = (tr("Si tú o tu amigo usáis AdGuard, un antivirus con protección de red o un cortafuegos, puede estar bloqueando la conexión: "
                 "añade Puerto Bravo a sus excepciones, o desactiva el filtrado para este programa, y prueba otra vez."))


def huella(clave):
    return hashlib.sha256(("puerto-bravo|" + (clave or "")).encode("utf-8")).hexdigest()


def direccion(host, puerto=PUERTO):
    return f"{PREFIJO}{host}:{puerto}"


def analizar_direccion(texto):
    """Devuelve (host, puerto) a partir de lo que escriba el jugador, o None si no se entiende."""
    t = (texto or "").strip().replace(" ", "")
    if t.lower().startswith(PREFIJO):
        t = t[len(PREFIJO):]
    t = t.strip("/")
    if not t:
        return None
    puerto = PUERTO
    if ":" in t:
        t, p = t.rsplit(":", 1)
        try:
            puerto = int(p)
        except ValueError:
            return None
    if not t or not (1 <= puerto <= 65535) or any(c in t for c in "/\\@ "):
        return None
    return t, puerto


def direcciones_locales():
    """Direcciones de este ordenador en la red de casa."""
    out = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))          # no envía nada: solo averigua por qué interfaz saldría
            out.append(s.getsockname()[0])
        finally:
            s.close()
    except OSError:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip not in out:
                out.append(ip)
    except OSError:
        pass
    return [ip for ip in out if not ip.startswith("127.")] or ["127.0.0.1"]


def direccion_publica(timeout=5):
    """Pregunta a un servicio de internet con qué dirección se ve este ordenador desde fuera.

    Solo se llama cuando el anfitrión lo pide en el menú. La consulta no lleva ningún dato del jugador.
    """
    import urllib.request
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=timeout) as r:
            ip = r.read(64).decode("ascii", "ignore").strip()
        socket.inet_aton(ip)
        return ip
    except Exception:
        return None


class _Lineas:
    """Lee de un socket mensajes JSON separados por saltos de línea."""

    def __init__(self, sock):
        self.sock = sock
        self.buf = b""

    def leer(self):
        while b"\n" not in self.buf:
            if len(self.buf) > MAX_LINEA:
                raise ValueError(tr("mensaje demasiado largo"))
            trozo = self.sock.recv(4096)
            if not trozo:
                return None
            self.buf += trozo
        linea, self.buf = self.buf.split(b"\n", 1)
        try:
            m = json.loads(linea.decode("utf-8"))
        except ValueError:
            return {}
        return m if isinstance(m, dict) else {}


def _enviar(sock, lock, obj):
    datos = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
    with lock:
        sock.sendall(datos)


def _cerrar_suave(conn):
    """Cierra dando tiempo a que el otro lado lea lo último que se le envió (un rechazo, por ejemplo)."""
    # No se corta primero: se espera a que el otro lado cierre, o a que pase un momento. En Windows, cerrar
    # nada más enviar puede hacer que el otro reciba un corte de conexión en lugar del mensaje.
    try:
        conn.settimeout(1.5)
        while conn.recv(256):
            pass
    except OSError:
        pass
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        conn.close()
    except OSError:
        pass


class Servidor:
    def __init__(self, puerto=PUERTO, clave="", max_jugadores=8):
        self.puerto = puerto
        self.huella = huella(clave) if clave else ""
        self.max = max_jugadores
        self.sock = None
        self.activo = False
        self.jugadores = {}        # id -> {"nombre", "sock", "lock", "estado", "ip"}
        self._lock = threading.Lock()
        self._sig = 1

    @property
    def protegido(self):
        return bool(self.huella)

    def iniciar(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.puerto))
        s.listen(8)
        s.settimeout(0.5)
        self.sock = s
        self.puerto = s.getsockname()[1]
        self.activo = True
        threading.Thread(target=self._aceptar, daemon=True).start()
        threading.Thread(target=self._difundir_estados, daemon=True).start()

    def _aceptar(self):
        while self.activo:
            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._atender, args=(conn, addr), daemon=True).start()

    def _a_todos(self, obj, menos=None):
        with self._lock:
            destinos = [(i, j) for i, j in self.jugadores.items() if i != menos]
        for i, j in destinos:
            try:
                _enviar(j["sock"], j["lock"], obj)
            except OSError:
                pass

    def _difundir_estados(self):
        while self.activo:
            time.sleep(0.1)
            with self._lock:
                estados = {str(i): j["estado"] for i, j in self.jugadores.items() if j["estado"]}
            if estados:
                self._a_todos({"t": "estados", "e": estados})

    def _atender(self, conn, addr):
        lock = threading.Lock()
        ident = None
        try:
            conn.settimeout(10)
            lineas = _Lineas(conn)
            hola = lineas.leer()
            if not hola or hola.get("t") != "hola":
                return
            motivo = None
            if hola.get("v") != VERSION_RED:
                motivo = tr("Tu versión del juego no es la misma que la del anfitrión.")
            elif self.huella and not hmac.compare_digest(str(hola.get("clave", "")), self.huella):
                motivo = tr("La contraseña no es correcta.")
            elif len(self.jugadores) >= self.max:
                motivo = tr("La partida está llena.")
            if motivo:
                _enviar(conn, lock, {"t": "rechazo", "motivo": motivo})
                return
            nombre = "".join(c for c in str(hola.get("nombre", "")) if c.isprintable())[:24].strip() or tr("Invitado")
            with self._lock:
                usados = {j["nombre"].lower() for j in self.jugadores.values()}
                base, n = nombre, 2
                while nombre.lower() in usados:
                    nombre = f"{base} {n}"
                    n += 1
                ident = self._sig
                self._sig += 1
                otros = [{"id": i, "nombre": j["nombre"]} for i, j in self.jugadores.items()]
                self.jugadores[ident] = {"nombre": nombre, "sock": conn, "lock": lock, "estado": None, "ip": addr[0]}
            _enviar(conn, lock, {"t": "ok", "id": ident, "nombre": nombre, "jugadores": otros, "protegido": self.protegido})
            self._a_todos({"t": "entra", "id": ident, "nombre": nombre}, menos=ident)
            conn.settimeout(45)
            while self.activo:
                m = lineas.leer()
                if m is None:
                    break
                t = m.get("t")
                if t == "estado":
                    e = m.get("e")
                    if isinstance(e, dict):
                        with self._lock:
                            if ident in self.jugadores:
                                self.jugadores[ident]["estado"] = {k: e.get(k) for k in ("m", "x", "y", "r", "v", "s")}
                elif t == "chat":
                    texto = "".join(c for c in str(m.get("texto", "")) if c.isprintable())[:300].strip()
                    if texto:
                        self._a_todos({"t": "chat", "de": ident, "nombre": nombre, "texto": texto}, menos=ident)
                elif t == "act":
                    # actividades conjuntas (carreras, repartos en equipo, subir al coche de otro): se reenvían tal cual
                    d = m.get("d")
                    if isinstance(d, dict) and len(json.dumps(d)) < 3000:
                        self._a_todos({"t": "act", "de": ident, "nombre": nombre, "d": d}, menos=ident)
                elif t == "evento":
                    self._a_todos({"t": "evento", "de": ident, "que": str(m.get("que", ""))[:20]}, menos=ident)
                elif t == "dinero":
                    try:
                        cantidad = max(1, min(100000, int(m.get("n", 0))))
                        destino = int(m.get("a", 0))
                    except (TypeError, ValueError):
                        continue
                    with self._lock:
                        j = self.jugadores.get(destino)
                    if j and destino != ident:
                        try:
                            _enviar(j["sock"], j["lock"], {"t": "dinero", "de": ident, "nombre": nombre, "n": cantidad})
                        except OSError:
                            pass
                elif t == "adios":
                    break
        except (OSError, ValueError):
            pass
        finally:
            if ident is not None:
                with self._lock:
                    fuera = self.jugadores.pop(ident, None)
                if fuera:
                    self._a_todos({"t": "sale", "id": ident, "nombre": fuera["nombre"]})
            _cerrar_suave(conn)

    def lista(self):
        with self._lock:
            return [(i, j["nombre"]) for i, j in sorted(self.jugadores.items())]

    def expulsar(self, ident):
        with self._lock:
            j = self.jugadores.get(ident)
        if not j:
            return False
        try:
            _enviar(j["sock"], j["lock"], {"t": "expulsado"})
        except OSError:
            pass

        def cortar():
            time.sleep(0.4)                      # se le da tiempo a recibir el aviso antes de cortar
            try:
                j["sock"].shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        threading.Thread(target=cortar, daemon=True).start()
        return True

    def detener(self):
        self.activo = False
        self._a_todos({"t": "cerrado"})
        time.sleep(0.2)                          # que llegue el aviso antes de cortar
        with self._lock:
            socks = [j["sock"] for j in self.jugadores.values()]
        for s in socks:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        try:
            self.sock.close()
        except OSError:
            pass


class Cliente:
    def __init__(self):
        self.sock = None
        self.lock = threading.Lock()
        self.entrantes = queue.Queue()
        self.conectado = False
        self.id = None
        self.nombre = ""
        self.host = ""
        self.puerto = PUERTO

    def conectar(self, host, puerto, nombre, clave="", timeout=6, intentos=3):
        """Devuelve (True, mensaje de bienvenida del servidor) o (False, motivo).

        Si la conexión se corta nada más abrirse se vuelve a intentar: los filtros de red (AdGuard, antivirus
        con protección web, cortafuegos) a veces interrumpen la primera conexión de un programa que no conocen.
        """
        cortada = False
        s = lineas = r = None
        for intento in range(max(1, intentos)):
            if intento:
                time.sleep(0.4 * intento)
            try:
                s = socket.create_connection((host, puerto), timeout=timeout)
            except OSError:
                if intento + 1 < intentos and cortada:
                    continue
                return False, (tr("No se pudo conectar. Comprueba la dirección, que tu amigo tenga la partida abierta y que su router deje pasar el puerto. ")
                               + AVISO_FILTROS)
            cortada = False
            try:
                s.settimeout(timeout)
                _enviar(s, self.lock, {"t": "hola", "v": VERSION_RED, "nombre": nombre, "clave": huella(clave) if clave else ""})
                lineas = _Lineas(s)
                r = lineas.leer()
            except (OSError, ValueError):
                r = None
                cortada = True
            if r is None:
                cortada = True
            if r and r.get("t") in ("ok", "rechazo"):
                break
            try:
                s.close()
            except OSError:
                pass
            if not cortada:
                return False, tr("Lo que hay en esa dirección no es una partida de Puerto Bravo.")
        else:
            return False, tr("La conexión se corta nada más empezar. ") + AVISO_FILTROS
        if not r or r.get("t") not in ("ok", "rechazo"):
            return False, tr("La conexión se corta nada más empezar. ") + AVISO_FILTROS
        if r["t"] == "rechazo":
            s.close()
            return False, str(r.get("motivo", tr("El anfitrión ha rechazado la conexión.")))
        s.settimeout(None)
        self.sock, self.conectado, self.id, self.nombre = s, True, r.get("id"), r.get("nombre", nombre)
        self.host, self.puerto = host, puerto
        threading.Thread(target=self._leer, args=(lineas,), daemon=True).start()
        return True, r

    def _leer(self, lineas):
        try:
            while self.conectado:
                m = lineas.leer()
                if m is None:
                    break
                if m:
                    self.entrantes.put(m)
        except (OSError, ValueError):
            pass
        if self.conectado:
            self.conectado = False
            self.entrantes.put({"t": "desconectado"})

    def enviar(self, obj):
        if not self.conectado:
            return False
        try:
            _enviar(self.sock, self.lock, obj)
            return True
        except OSError:
            if self.conectado:
                self.conectado = False
                self.entrantes.put({"t": "desconectado"})
            return False

    def cerrar(self):
        if self.conectado:
            try:
                _enviar(self.sock, self.lock, {"t": "adios"})
            except OSError:
                pass
        self.conectado = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except (OSError, AttributeError):
            pass
        try:
            self.sock.close()
        except (OSError, AttributeError):
            pass
