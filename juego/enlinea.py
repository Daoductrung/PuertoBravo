"""Jugar en un servidor: el mismo juego de siempre, con jugadores de verdad alrededor.

Tu juego sigue llevando lo tuyo (tus misiones y tus trabajos), y el servidor lleva lo que es de todos: quién eres, tu
personaje guardado, los demás jugadores, los vehículos que dejáis en la calle, los disparos entre vosotros, las bandas,
los barrios, la hora y el tiempo, el tráfico, la gente de la calle y la policía.

Lo que decide el servidor no lo decide tu juego: si un disparo tuyo llega a otro jugador, de quién es un coche
aparcado, cuánto hay en la caja de la banda.
"""
import binascii
import hashlib
import json
import math
import os
import queue
import random
import socket
import sys
import threading
import time

from . import ed25519, red, registro, rutas
from . import mundo as M
from .entidades import Persona
from .online import Remoto

VERSION_RED = 2                   # la versión del protocolo que habla este juego
PROTOCOLO_MIN = 2                 # la más antigua con la que todavía se entiende
PUERTO = 47820
MAX_LINEA = 700 * 1024


# ------------------------------------------------------------------ identidad
def varias_instancias():
    """Solo en las copias de pruebas: permite abrir el juego varias veces, cada una con su identidad."""
    return os.path.exists(rutas.data("config", "varias_instancias.txt"))


def perfil():
    """El perfil con el que se ha abierto esta copia (--perfil=2). Fuera de las copias de pruebas no se hace caso."""
    if not varias_instancias():
        return ""
    for a in sys.argv[1:]:
        if a.startswith("--perfil="):
            return "".join(c for c in a[9:] if c.isalnum())[:12]
    return ""


def _archivo_identidad():
    p = perfil()
    return rutas.archivo_config("identidad" + ("_" + p if p else ""))


def identidad(crear=True):
    """La llave de este juego: 32 bytes que no salen nunca de tu ordenador. Con ella te reconoce cada servidor."""
    from . import cifrado
    ruta = _archivo_identidad()
    try:
        s = binascii.unhexlify(cifrado.leer_json(ruta)["semilla"])
        if len(s) == 32:
            return s
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if not crear:
        return None
    s = os.urandom(32)
    cifrado.escribir_json(ruta, {"semilla": binascii.hexlify(s).decode("ascii"), "aviso": "Esta es tu identidad en los servidores. No la compartas."})
    return s


def exportar_identidad():
    return "PB1-" + binascii.hexlify(identidad()).decode("ascii")


def importar_identidad(texto):
    from . import cifrado
    t = "".join((texto or "").split())
    if t.upper().startswith("PB1-"):
        t = t[4:]
    try:
        s = binascii.unhexlify(t)
    except (ValueError, binascii.Error):
        return False
    if len(s) != 32:
        return False
    cifrado.escribir_json(_archivo_identidad(), {"semilla": binascii.hexlify(s).decode("ascii"), "aviso": "Esta es tu identidad en los servidores. No la compartas."})
    return True


def huella_datos(datos):
    """Una huella de lo que tiene que ser igual en todos: localidades, lugares, barrios, armas, vehículos y misiones.
    Solo entra lo que no cambia mientras se juega: identificadores y las cifras de las armas."""
    partes = [["formato", 2]]                    # cambia cuando el juego le cuenta al servidor más cosas del mismo mundo
    for m in sorted(datos.get("mapas", []), key=lambda m: str(m.get("id"))):
        partes.append(["mapa", m.get("id"), sorted(str(l.get("id")) for l in m.get("lugares", [])), sorted(str(b.get("id")) for b in m.get("barrios", []))])
    for a in sorted(datos.get("armas", []), key=lambda a: str(a.get("id"))):
        partes.append(["arma", a.get("id"), a.get("dano"), a.get("alcance"), a.get("cadencia"), a.get("precision")])
    partes.append(["vehiculos", sorted(str(v.get("id")) for v in datos.get("vehiculos", []))])
    partes.append(["misiones", sorted(str(m.get("id")) for m in datos.get("misiones", []) if not callable(m.get("al_completar")) and not m.get("generada"))])
    return hashlib.sha256(json.dumps(partes, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def mundo_servidor():
    """Lo que un servidor necesita saber del mundo de esta versión del juego, sin tener el juego: los lugares de cada
    localidad con sus coordenadas, los barrios, las cifras de las armas, los modelos y lo que paga cada misión.

    El servidor no trae esto de fábrica atado a una versión: se lo da el juego. Así un mismo servidor vale para las
    versiones que vayan saliendo, sin tener que actualizarlo."""
    from . import VERSION
    datos = M.cargar_datos()
    mapas = M.crear_mapas(datos)
    out = {"version": VERSION, "huella": huella_datos(datos), "mapas": {}, "armas": {}, "modelos": {}, "misiones": {}}
    for ident, m in mapas.items():
        c = next(x for x in datos["mapas"] if x.get("id") == ident)
        out["mapas"][ident] = {
            "nombre": m.nombre, "tipo": m.tipo, "ancho": round(float(m.ancho), 1), "alto": round(float(m.alto), 1),
            "lugares": [{"id": l.id, "tipo": l.tipo, "nombre": l.nombre, "x": round(float(l.x), 1), "y": round(float(l.y), 1), "adultos": bool(l.get("adultos")),
                         "precio": int(l.get("precio", 0) or 0), "ingresos": int(l.get("ingresos", 0) or 0)}
                        for l in m.lugares.values()],
            # para el tráfico común: cuántas calles hay a lo largo y a lo ancho, cuánto tráfico y qué coches
            "nx": int(getattr(m, "NX", 0)) if m.tipo != "mar" else 0, "ny": int(getattr(m, "NY", 0)) if m.tipo != "mar" else 0,
            "trafico": int(getattr(m, "trafico", 0)) if m.tipo != "mar" else 0,
            "peatones": int(getattr(m, "peatones", 0)) if m.tipo != "mar" else 0, "policia": int(bool(getattr(m, "policia", True))),
            "coches": sorted({v for b in c.get("barrios", []) for v in b.get("vehiculos", [])}),
            # para los agentes a pie: las manzanas por las que se puede andar (parques, plazas, descampados)
            "abiertos": sorted([int(k[0]), int(k[1])] for k, v in getattr(m, "bloques", {}).items() if v != "pared") if m.tipo != "mar" else [],
            "barrios": [{"id": b["id"], "nombre": b.get("nombre", b["id"])} for b in c.get("barrios", [])]}
    for a in datos["armas"]:
        out["armas"][a["id"]] = {"nombre": a["nombre"], "tipo": a.get("tipo", "cuerpo"), "dano": a.get("dano", 0), "alcance": a.get("alcance", 2),
                                 "cadencia": a.get("cadencia", 0.5), "precision": a.get("precision", 0.8), "radio": a.get("radio", 0), "automatica": bool(a.get("automatica"))}
    for v in datos["vehiculos"]:
        out["modelos"][v["id"]] = {"nombre": v["nombre"], "salud": v.get("salud", 100), "vel_max": v.get("vel_max", 25), "acel": v.get("acel", 6.0),
                                   "freno": v.get("freno", 12), "vuela": bool(v.get("vuela"))}
    for mi in datos["misiones"]:
        r = mi.get("recompensa") or {}
        out["misiones"][mi["id"]] = {"titulo": mi["titulo"], "dinero": int(r.get("dinero", 0) or 0), "repetible": bool(mi.get("repetible"))}
    return out


def version_tupla(texto):
    """Una versión del juego, lista para compararla con otra: «1.7.0» va antes que «1.10.0»."""
    out = []
    for trozo in str(texto or "0").split("."):
        num = "".join(c for c in trozo if c.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out)


def mundo_canonico(d):
    """El texto exacto que se firma y se envía: el mismo mundo da siempre el mismo texto."""
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def firma_del_mundo(huella):
    """La firma con la que quien publica el juego avala el mundo de esta versión. Vacía si no la hay o no es de estos datos."""
    try:
        with open(rutas.data("datos", "mundo.firma"), encoding="utf-8") as f:
            d = json.load(f)
        return str(d["firma"]) if d.get("huella") == huella else ""
    except (OSError, ValueError, KeyError):
        return ""


# -------------------------------------------------------------------- conexión
class _Lineas:
    def __init__(self, sock):
        self.sock = sock
        self.buf = b""

    def leer(self):
        while b"\n" not in self.buf:
            if len(self.buf) > MAX_LINEA:
                raise ValueError("mensaje demasiado largo")
            trozo = self.sock.recv(65536)
            if not trozo:
                return None
            self.buf += trozo
        linea, self.buf = self.buf.split(b"\n", 1)
        try:
            m = json.loads(linea.decode("utf-8"))
        except ValueError:
            return {}
        return m if isinstance(m, dict) else {}


class ClienteServidor(red.Cliente):
    """La conexión con un servidor: cifrada si el servidor cifra, y con tu identidad demostrada con una firma."""

    def __init__(self):
        super().__init__()
        self.cifrado = False
        self.huella_cert = ""
        self.protocolo = VERSION_RED             # la versión del protocolo acordada con el servidor

    @staticmethod
    def _respuesta(lineas, esperados, tope=12):
        """El siguiente mensaje de los que se esperan en el saludo. Lo que no se conoce se deja pasar: un servidor de una
        versión posterior puede decir cosas que este juego no entiende, y eso no es motivo para no entrar."""
        for _ in range(tope):
            r = lineas.leer()
            if r is None:
                return None
            if r.get("t") in esperados:
                return r
        return None

    def _abrir(self, host, puerto, timeout, tls):
        s = socket.create_connection((host, puerto), timeout=timeout)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if not tls:
            return s, ""
        import ssl
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False               # el certificado es del propio servidor: lo que se comprueba es que no cambie
        ctx.verify_mode = ssl.CERT_NONE
        s.settimeout(4)
        try:
            ss = ctx.wrap_socket(s, server_hostname=None)
        except Exception:
            try:
                s.close()
            except OSError:
                pass
            raise
        ss.settimeout(timeout)
        return ss, hashlib.sha256(ss.getpeercert(True)).hexdigest()

    def conectar_servidor(self, host, puerto, nombre, semilla, huella, clave="", invitacion="", huella_cert="", timeout=10, mundo=None, firmado=False):
        """Devuelve (True, bienvenida) o (False, motivo). Si el certificado no es el de la otra vez, motivo empieza por «certificado»."""
        s = None
        aviso = ""
        enviado_mundo = False
        # Cifrado, y si el servidor no cifra, sin cifrar. Y todo ello dos veces: los filtros de red (AdGuard, antivirus con
        # protección web, cortafuegos) a veces se tragan la primera conexión de un programa que no conocen.
        for intento, tls in enumerate((True, False, True, False)):
            ultimo = intento == 3
            try:
                s, fp = self._abrir(host, puerto, timeout, tls)
            except (OSError, ValueError) as e:
                if isinstance(e, (socket.gaierror, ConnectionRefusedError)) or ultimo:
                    return False, ("No se pudo conectar con el servidor. Comprueba la dirección y que el servidor esté encendido. " + red.AVISO_FILTROS)
                continue                         # el servidor no cifra, o se ha cortado: se prueba de la otra forma
            except Exception:
                if ultimo:
                    return False, "No se pudo conectar con el servidor."
                continue
            if tls and huella_cert and fp != huella_cert:
                s.close()
                return False, "certificado: " + fp
            self.cifrado, self.huella_cert = tls, fp
            try:
                s.settimeout(timeout if intento >= 2 else min(timeout, 5))
                lineas = _Lineas(s)
                pub = binascii.hexlify(ed25519.publica(semilla)).decode("ascii")
                from . import VERSION
                # v es la versión más nueva del protocolo que habla este juego y vmin la más antigua con la que se entiende:
                # el servidor elige la más nueva que hablen los dos. Así se puede jugar con un servidor más nuevo o más antiguo.
                red._enviar(s, self.lock, {"t": "hola", "v": VERSION_RED, "vmin": PROTOCOLO_MIN, "nombre": nombre, "pub": pub, "huella": huella, "juego": VERSION,
                                           "firmado": bool(firmado), "clave": red.huella(clave) if clave else "", "invitacion": invitacion})
                r = self._respuesta(lineas, ("reto", "rechazo", "ok"), tope=3)
                if not tls and huella_cert and r and r.get("t") in ("reto", "rechazo", "ok"):
                    s.close()
                    return False, ("Este servidor cifraba la conexión y ahora no lo hace. Por seguridad no entro. "
                                   "Si lo ha cambiado quien lo lleva, bórralo de tu lista y añádelo otra vez.")
                if r and r.get("t") == "reto":
                    try:
                        minimo = int(r.get("vmin") or 0)
                    except (TypeError, ValueError):
                        minimo = 0
                    if minimo > VERSION_RED:                     # el servidor ya no habla con juegos como este
                        s.close()
                        return False, "Este servidor necesita una versión más nueva del juego. Actualiza el juego para entrar."
                    s.settimeout(timeout)
                    f = ed25519.firmar(semilla, ("puertobravo-entrada|" + str(r.get("n", ""))).encode("ascii"))
                    red._enviar(s, self.lock, {"t": "firma", "f": binascii.hexlify(f).decode("ascii")})
                    r = self._respuesta(lineas, ("ok", "rechazo", "pide_mundo"))
                    if r and r.get("t") == "pide_mundo":         # el servidor no conoce el mundo de esta versión: se lo damos
                        texto, firma_m = mundo() if mundo is not None else ("", "")
                        import base64
                        import zlib
                        red._enviar(s, self.lock, {"t": "mundo", "z": base64.b64encode(zlib.compress(texto.encode("utf-8"), 9)).decode("ascii"), "firma": firma_m})
                        enviado_mundo = True
                        s.settimeout(max(timeout, 30))
                        r = self._respuesta(lineas, ("ok", "rechazo"))
            except (OSError, ValueError):
                r = None
            if not r or r.get("t") not in ("ok", "rechazo"):
                try:
                    s.close()
                except OSError:
                    pass
                if enviado_mundo:
                    return False, "El servidor no ha aceptado los datos de tu versión del juego, o ha cortado la conexión al recibirlos. Prueba otra vez dentro de un momento."
                if not ultimo:
                    continue
                return False, "Lo que hay en esa dirección no es un servidor de Puerto Bravo, o no contesta. " + red.AVISO_FILTROS
            if r["t"] == "rechazo":
                s.close()
                return False, str(r.get("motivo", "El servidor no te deja entrar."))
            s.settimeout(None)
            self.sock, self.conectado, self.id, self.nombre = s, True, r.get("id"), r.get("nombre", nombre)
            self.host, self.puerto = host, puerto
            try:
                self.protocolo = max(PROTOCOLO_MIN, min(VERSION_RED, int(r.get("protocolo") or VERSION_RED)))
            except (TypeError, ValueError):
                self.protocolo = VERSION_RED
            threading.Thread(target=self._leer, args=(lineas,), daemon=True).start()
            return True, r
        return False, aviso or "No se pudo conectar con el servidor."


class Enlace:
    """Una conexión ya aceptada por un servidor, a la espera de que empiece la partida."""

    def __init__(self, cli, ok, servidor):
        self.cli, self.ok, self.servidor = cli, ok, servidor


def conectar(app, servidor, clave="", invitacion=""):
    """Conecta con un servidor de la lista. Devuelve (Enlace, texto) o (None, motivo)."""
    d = red.analizar_direccion(servidor.get("dir", ""))
    if d is None:
        return None, "No entiendo esa dirección."
    host, puerto = d
    if ":" not in servidor.get("dir", "").replace(red.PREFIJO, ""):
        puerto = PUERTO
    if not hasattr(app, "_huella_datos"):
        app._huella_datos = huella_datos(app.datos)
    nombre = (app.cfg["red_nombre"] or "Jugador")[:24]
    registro.ocultar(nombre)
    cli = ClienteServidor()
    semilla = getattr(app, "semilla_identidad", None)        # las pruebas automáticas traen la suya y no tocan la del jugador
    if semilla is None:
        semilla = hashlib.sha256(b"identidad de pruebas").digest() if app.pruebas else identidad()
    firma_m = firma_del_mundo(app._huella_datos)
    ok, r = cli.conectar_servidor(host, puerto, nombre, semilla, app._huella_datos, clave, invitacion, servidor.get("cert", ""),
                                  mundo=lambda: (mundo_canonico(mundo_servidor()), firma_m), firmado=bool(firma_m))
    registro.info("red", "Intenta entrar en un servidor", conseguido=ok, cifrado=cli.cifrado)
    if not ok:
        return None, r
    servidor["cert"] = cli.huella_cert
    servidor["nombre"] = str((r.get("servidor") or {}).get("nombre") or servidor.get("nombre") or "Servidor")[:60]
    return Enlace(cli, r, servidor), ""


# =========================================================== dentro de la partida
class EnLinea:
    """Mixin de Partida: lo que cambia cuando la partida es de un servidor."""

    en_servidor = False

    def sv_entrar(self, enlace):
        ok = enlace.ok
        self.red = enlace.cli
        self.en_servidor = True
        self.sv = {"info": ok.get("servidor") or {}, "admin": bool(ok.get("admin")), "pasivo": False, "banda": ok.get("banda"), "rango": None,
                   "territorios": ok.get("territorios") or {"barrios": [], "guerras": []}, "grupo": None, "miembros": [], "vehs": {},
                   "recompensa": int(ok.get("recompensa") or 0), "agresor": None, "t_agresor": -999.0, "t_guardar": 20.0, "inv_banda": None,
                   "inv_grupo": None, "segura": False, "protegido": time.time() + float((ok.get("servidor") or {}).get("proteccion", 0)),
                   "ecos": {}, "mision_grupo": None, "quien": [], "bandas": [], "nombre_servidor": enlace.servidor.get("nombre", "Servidor"),
                   "t_atropello": 0.0, "t_dicho": {}, "cifrado": enlace.cli.cifrado, "props": ok.get("props") or {}, "robo": None, "trafico": {}, "peatones": {},
                   "agentes": {}, "id": ok.get("id"), "t_desfase": None,
                   # con qué mundo trabaja el servidor y qué sabe hacer: puede ser de otra versión del juego que la tuya
                   "mundo": ok.get("mundo") if isinstance(ok.get("mundo"), dict) else {},
                   "funciones": [f for f in ok.get("funciones") or [] if isinstance(f, str)],
                   "protocolo": getattr(enlace.cli, "protocolo", VERSION_RED)}
        if self.sv["info"].get("policia") and self.cfg["sin_policia"]:      # aquí la policía es de todos: la asistencia no vale
            self._sv_sin_policia = True
            self.cfg.v["sin_policia"] = False
        self.j.puntos_busqueda, self.j.estrellas = 0.0, 0                    # si te buscaban al salir, el servidor te lo dirá
        if self.sv["banda"]:
            yo = next((m for m in self.sv["banda"]["miembros"] if m["cuenta"] == ok.get("cuenta")), None)
            self.sv["rango"] = yo["rango"] if yo else None
        self.sv["cuenta"] = ok.get("cuenta")
        self.remotos = {}
        for q in ok.get("jugadores", []):
            registro.ocultar(q["nombre"])
            r = Remoto(q["id"], q["nombre"])
            r.banda, r.ia = q.get("banda"), bool(q.get("ia"))
            self.remotos[q["id"]] = r
        h = ok.get("hora") or {}
        self.reloj, self.dia, self.lluvia = float(h.get("reloj", self.reloj)), int(h.get("dia", self.dia)), bool(h.get("lluvia"))
        for mapa in self.mapas.values():                         # los semáforos, iguales para todos
            mapa.desfase_luces = float(h.get("luces", 0.0)) - self.t
        self.j.semilla = int(ok.get("semilla") or self.j.semilla or 1)       # la misma suerte para todos: precios, sucesos y lotería
        try:
            self.sortear_dia(anunciar=False)
        except Exception:
            pass
        self.cfg.temporales = {"sin_policia": True} if getattr(self, "_sv_sin_policia", False) else {}
        if not self.sv["info"].get("adultos", True) and self.cfg["adultos"]:
            self._sv_adultos = True
            self.cfg.temporales["adultos"] = True
            self.cfg.v["adultos"] = False            # solo mientras dura la sesión: no se guarda
            self.app.aplicar_adultos()
        for v in ok.get("vehiculos", []):
            self.sv["vehs"][v["id"]] = v
        self.sv_poner_vehiculos()
        self.sv_al_dia(int(ok.get("dias_fuera") or 0))
        for cosa in ok.get("pendientes", []):                    # lo que pasó con tus propiedades mientras no estabas
            if cosa.get("que") in ("venta", "caducada"):
                l = self.lugares.get(cosa.get("lugar"))
                if l is not None and l.id in self.j.propiedades:
                    self.j.propiedades.remove(l.id)
                n = max(0, int(cosa.get("n", 0)))
                self.j.dinero += n
                nombre = l.nombre if l is not None else "una propiedad"
                self.decir(f"{cosa.get('por', 'Alguien')} te ha comprado {nombre} por {n} euros." if cosa["que"] == "venta" else
                           f"Llevabas tanto sin entrar que {nombre} ha vuelto al mercado. Te quedan {n} euros de su valor.")
        if ok.get("saldo") is not None:                          # el dinero lo lleva el servidor: manda lo que él tiene apuntado
            self._sv_ajustar_saldo(self.j.dinero + self.j.banco - int(ok["saldo"]), callar=True)
        self._sv_cuadrar_propiedades()
        self._sv_descontar_robos(int(ok.get("robos") or 0))
        for cosa in ok.get("pendientes", []):
            if cosa.get("que") == "coche":
                self.decir(f"Mientras no estabas, {cosa.get('por', 'alguien')} se llevó tu {cosa.get('nombre', 'vehículo')} de donde lo dejaste.")
            if cosa.get("que") == "caido":
                n = min(self.j.dinero, int(cosa.get("pierde", 0)))
                self.j.dinero -= n
                self.decir(f"Mientras te desconectabas en plena pelea, {cosa.get('por', 'alguien')} te tumbó. Has perdido {n} euros.")
        info = self.sv["info"]
        quienes = ", ".join(x.nombre for x in self.remotos.values())
        self.son("amigo_entra", cat="interfaz")
        self.decir(f"Estás en {self.sv['nombre_servidor']} como {self.red.nombre}. " + (str(info.get("bienvenida", "")) + " " if info.get("bienvenida") else "")
                   + (f"Están: {quienes}. " if quienes else "De momento no hay nadie más. ")
                   + ("La conexión va cifrada. " if self.sv["cifrado"] else "Este servidor no cifra la conexión. ")
                   + ("Hay combate entre jugadores" + (", con zonas seguras en hospitales, comisarías y casas. " if info.get("seguras") else ". ") if info.get("pvp") else "Aquí no hay combate entre jugadores. ")
                   + self.sv_aviso_version()
                   + "Abre el móvil con M y entra en En línea para verlo todo.")
        self.sv_guardar()

    def sv_aviso_version(self):
        """Lo que hay que saber cuando el servidor trabaja con los datos de otra versión del juego que la tuya.
        Se juega igual, cada uno con lo que su versión conoce; aquí se dice qué se va a notar. Vacío si es la misma."""
        from . import VERSION
        m = self.sv.get("mundo") or {}
        if not m or m.get("igual", True) or not m.get("version"):
            return ""
        suya, mia = version_tupla(m.get("version")), version_tupla(VERSION)
        if suya > mia:
            return (f"Este servidor va con los datos de la versión {m['version']} del juego y tú tienes la {VERSION}: puedes jugar, "
                    "pero no verás los lugares, vehículos y armas nuevos de otros jugadores hasta que actualices. ")
        if suya < mia:
            return (f"Este servidor va con los datos de la versión {m['version']} del juego, anterior a la tuya: puedes jugar, "
                    "pero lo nuevo de tu versión no lo verán los demás, y en las localidades nuevas no te verán a ti. ")
        return "Los datos de tu juego no son exactamente los de este servidor: puedes jugar, pero lo que tengas distinto no lo verán los demás. "

    def sv_al_dia(self, dias):
        """Has estado fuera: pasan las medianoches que te has perdido, con un tope de tres."""
        if dias <= 0:
            return
        n = min(3, dias)
        self.decir(f"Has estado {dias} {'día' if dias == 1 else 'días'} del servidor sin entrar." + (" Cuentan tres." if dias > 3 else ""))
        for _ in range(n):
            self._cobrar_negocios()
        self.pasar_perro(60.0 * 24 * n)

    def sv_salir(self, motivo=None, al_menu=False):
        if not self.en_servidor:
            return
        if self.red is not None and self.red.conectado:
            v = self.j.veh
            if v is not None and getattr(v, "red_mio", False):
                self.red.enviar({"t": "veh_dejar", "id": v.id_red, "x": round(v.x, 1), "y": round(v.y, 1), "r": round(v.rumbo), "salud": round(v.salud, 1)})
            self.sv_guardar(ya=True)
            time.sleep(0.15)
        self.en_servidor = False
        if getattr(self, "_sv_sin_policia", False):
            self._sv_sin_policia = False
            self.cfg.v["sin_policia"] = True
        if getattr(self, "_sv_adultos", False):
            self._sv_adultos = False
            self.cfg.v["adultos"] = True
            self.app.aplicar_adultos()
        self.cfg.temporales = {}
        for p in list(self.sv.get("agentes", {}).values()):
            if p in self.personas:
                self.personas.remove(p)
        self.sv["agentes"] = {}
        for e in list(self.sv.get("ecos", {}).values()):
            if e in self.personas:
                self.personas.remove(e)
        for r in self.remotos.values():
            if getattr(r, "sirena", None) is not None:
                r.sirena.parar()
        for mapa in self.mapas.values():
            mapa.desfase_luces = 0.0
        for r in self.remotos.values():
            self._sv_quitar_policia(r)
        for v in list(self.sv.get("trafico", {}).values()):
            if v is not self.j.veh and not v.muerto:
                self.quitar_vehiculo(v)
        self.sv["trafico"] = {}
        for p in list(self.sv.get("peatones", {}).values()):
            if p in self.personas:
                self.personas.remove(p)
        self.sv["peatones"] = {}
        self.desconectar_online(motivo)
        if al_menu:
            texto = motivo or "Has salido del servidor."
            self.app.volver_al_menu()
            self.app.decir(texto, True)

    def sv_guardar(self, ya=False):
        if self.en_servidor and self.red is not None and self.red.conectado:
            d = self.a_dict()
            d.pop("veh_fuera", None)                 # en un servidor, los vehículos de la calle los lleva el servidor
            self.red.enviar({"t": "guardar", "p": d, "ya": bool(ya)})
            self.sv["t_guardar"] = 45.0
            return True
        return False

    def sv_estado(self):
        """Lo que se añade a tu posición en cada envío: salud, dinero, arma, barrio y demás."""
        j = self.j
        x, y = self.pos()
        v = j.veh
        try:
            barrio = self.mundo.barrio(x, y)["id"]
        except Exception:
            barrio = None
        return {"sa": round(max(0.0, j.salud), 1), "di": int(j.dinero), "ba": int(j.banco), "ar": j.arma, "b": barrio, "ag": int(bool(j.agachado)),
                "in": int(getattr(self, "interior", None) is not None), "es": int(j.estrellas), "po": self._sv_mi_policia(), "vi": getattr(v, "id_red", None) if v is not None and getattr(v, "red_mio", False) else None}

    def sv_dicho(self, clave, texto, cada=4.0, interrumpir=False):
        """Dice algo, pero no la misma cosa a cada momento."""
        if self.t - self.sv["t_dicho"].get(clave, -999.0) >= cada:
            self.sv["t_dicho"][clave] = self.t
            self.decir(texto, interrumpir)

    def sv_segura(self):
        if not self.sv["info"].get("seguras"):
            return False
        if getattr(self, "interior", None) is not None:
            return True
        x, y = self.pos()
        return any(l.tipo in ("hospital", "comisaria", "casa", "ong", "protectora") and math.hypot(l.x - x, l.y - y) <= 16 for l in self.mundo.lugares.values())

    # ---------------------------------------------------------- cada fotograma
    def sv_paso(self, dt):
        if not self.en_servidor:
            return
        sv = self.sv
        sv["t_guardar"] -= dt
        if sv["t_guardar"] <= 0 and not self.transicion:
            self.sv_guardar()
        if sv["info"].get("pvp"):
            segura = self.sv_segura()
            if segura != sv["segura"]:
                sv["segura"] = segura
                self.son("llegada" if segura else "menu_atras", cat="interfaz", vol=0.5)
                self.sv_dicho("segura", "Zona segura: aquí nadie puede herir a nadie." if segura else "Sales de la zona segura.", 6.0)
            if sv["protegido"] and time.time() >= sv["protegido"]:
                sv["protegido"] = 0
                self.decir("Se acaba la protección de llegada.")
        x0, y0 = self.pos()
        for r in self.remotos.values():              # quien te atacó deja de contar como enemigo al cabo de un rato
            if r.hostil and self.t - getattr(r, "t_hostil", 0.0) > 90:
                r.hostil = False
            # a quien persigue la policía se le oye venir: las sirenas van con él
            perseguido = getattr(r, "estrellas", 0) > 0 and r.mapa == self.mundo.id and r.visto and r.dist(x0, y0) < 220 and not self.sv_policia_comun()
            sirena = getattr(r, "sirena", None)
            if perseguido and sirena is None:
                r.sirena = self.son("sirena_lejana", bucle=True, xy=(r.x, r.y), ref=12, maxd=220, vol=0.5)
            elif perseguido:
                sirena.mover(r.x, r.y)
            elif sirena is not None:
                sirena.parar()
                r.sirena = None
        # atropellar a otro jugador
        v = self.j.veh
        sv["t_atropello"] -= dt
        if v is not None and abs(v.vel) > 4 and sv["t_atropello"] <= 0 and sv["info"].get("pvp"):
            for r in self.remotos.values():
                if r.mapa == self.mundo.id and r.visto and not r.veh and r.dist(v.x, v.y) < 3.2:
                    sv["t_atropello"] = 1.2
                    self.red.enviar({"t": "atropello", "a": r.id})
                    break
        self._sv_grupo_paso(dt)

    # ----------------------------------------------------------------- mensajes
    def sv_mensaje(self, m):
        """Devuelve True si el mensaje era del servidor y ya está atendido."""
        if not self.en_servidor:
            return False
        f = getattr(self, "_svm_" + str(m.get("t")), None)
        if f is None:
            return False                         # un mensaje que este juego no conoce: quien lo recibe después lo deja pasar
        try:
            f(m)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            # Un servidor de otra versión puede mandar un mensaje conocido con otra forma. No es motivo para que el juego
            # se caiga: se anota y se sigue.
            registro.excepcion("red", "Un mensaje del servidor no tiene la forma que este juego espera", tipo=str(m.get("t"))[:30])
        return True

    def _svm_aviso(self, m):
        if m.get("son") and m["son"] in self.mez.sonidos:
            self.son(m["son"], cat="interfaz", vol=0.6)
        self.decir(str(m.get("texto", "")))

    def _svm_pong(self, m):
        pass

    def _svm_guardado(self, m):
        pass

    def _svm_hora(self, m):
        h = m.get("h") or {}
        try:
            reloj, dia = float(h.get("reloj", self.reloj)), int(h.get("dia", self.dia))
        except (TypeError, ValueError):
            return
        llueve = bool(h.get("lluvia"))
        if llueve != self.lluvia:
            self.lluvia = llueve
            self.son("trueno" if llueve else "pajaro", cat="ambiente")
            self.decir("Empieza a llover. El asfalto mojado alarga las frenadas." if llueve else "Deja de llover.")
        if dia != self.dia:
            self.dia = dia
            self.plazas_usadas.clear()
            self._cobrar_negocios()
            self.sortear_dia()
        self.reloj = reloj
        if "luces" in h:                                         # los semáforos, iguales para todos
            for mapa in self.mapas.values():
                mapa.desfase_luces = float(h["luces"]) - self.t

    def _svm_aspecto(self, m):
        self._aspecto_recibido(m.get("de"), m.get("texto"))

    def _svm_entra(self, m):
        self._aspecto_enviado = None                             # que el que llega sepa también cómo vas
        registro.ocultar(m.get("nombre"))
        r = Remoto(m["id"], str(m.get("nombre", "Alguien")))
        r.banda, r.ia = m.get("banda"), bool(m.get("ia"))
        self.remotos[m["id"]] = r
        if r.ia:
            return                               # los personajes del servidor van y vienen sin anunciarse
        self.son("amigo_entra", cat="interfaz")
        self.decir(f"{r.nombre} entra en el servidor.")

    def _svm_sale(self, m):
        r = self.remotos.pop(m.get("id"), None)
        if r:
            r.callar()
            self._sv_quitar_policia(r)
            if getattr(r, "sirena", None) is not None:
                r.sirena.parar()
            if self.objetivo is r:
                self.objetivo = None
            if getattr(r, "ia", False):
                return
            self.son("amigo_sale", cat="interfaz")
            self.decir(f"{r.nombre} sale del servidor.")

    def _svm_estados(self, m):
        if "tr" in m:
            self._sv_trafico(m.get("tr") or [])
        if "lu" in m:
            self.mundo.desfase_luces = float(m["lu"]) - self.t
        if "pe" in m:
            self._sv_peatones(m.get("pe") or [])
        if "po" in m:
            self._sv_agentes(m.get("po") or [])
        if "es" in m:
            self._sv_cuadrar_busqueda(m.get("es"))
        for clave, e in (m.get("e") or {}).items():
            try:
                ident = int(clave)
            except ValueError:
                continue
            r = self.remotos.get(ident)
            if r is None or not isinstance(e, dict):
                continue
            try:
                r.tx, r.ty = float(e.get("x") or 0), float(e.get("y") or 0)
                r.rumbo, r.vel = float(e.get("r") or 0), float(e.get("s") or 0)
            except (TypeError, ValueError):
                continue
            if e.get("m") != r.mapa or not r.visto:
                r.x, r.y = r.tx, r.ty
                r.visto = True
            r.mapa = e.get("m")
            r.veh = e.get("v") if e.get("v") in self.modelos else ("utilitario" if e.get("v") else None)
            if "vi" in e:
                r.vid, r.agachado, r.pasivo, r.segura, r.dentro = e.get("vi"), bool(e.get("ag")), bool(e.get("pa")), bool(e.get("sg")), bool(e.get("in"))
                r.estrellas = int(e.get("es") or 0)
                self._sv_policia_de(r, e.get("po") or [])

    # ------------------------------------------------------------ policía común
    def _sv_mi_policia(self):
        """La policía que te persigue en tu juego: se la cuentas al servidor para que la tengan también los que están cerca."""
        if not self.j.estrellas or self.sv_policia_comun():
            return []
        out = []
        for v in self.vehiculos:
            if v.ia == "policia" and not v.muerto and len(out) < 4:
                out.append(["v", v.id, v.modelo["id"], round(v.x, 1), round(v.y, 1), int(v.rumbo)])
        for p in self.personas:
            if p.tipo == "policia" and not p.muerto and len(out) < 9:
                out.append(["p", p.id, round(p.x, 1), round(p.y, 1)])
        return out

    def _sv_policia_de(self, r, lista):
        """Patrullas y agentes que persiguen a otro jugador, puestos en tu juego donde están en el suyo."""
        ecos = getattr(r, "poli", None)
        if ecos is None:
            ecos = r.poli = {}
        if not lista and not ecos:
            return
        vistos = set()
        for f in lista:
            try:
                clave = (f[0], int(f[1]))
                if f[0] == "v":
                    modelo, x, y, rumbo = f[2], float(f[3]), float(f[4]), float(f[5])
                else:
                    x, y = float(f[2]), float(f[3])
            except (TypeError, ValueError, IndexError):
                continue
            o = ecos.get(clave)
            if o is None or o.muerto:
                if f[0] == "v":
                    if modelo not in self.modelos:
                        continue
                    o = self.crear_vehiculo(modelo, x, y, M.dir_de_rumbo(rumbo), "servidor", "Coche patrulla")
                    o.eco_poli, o.ocupado = True, True
                    o.sirena = self.son("sirena", bucle=True, xy=(x, y), ref=14, maxd=260, vol=0.5)
                else:
                    o = Persona("civil", x, y, "Policía")
                    o.estado, o.tag, o.eco_poli, o.eco_de = "quieto", "eco", clave[1], r.id
                    self.personas.append(o)
                ecos[clave] = o
            if f[0] == "v":
                o.tx, o.ty, o.rumbo, o.vel = x, y, rumbo, 8.0
            else:
                o.x, o.y = x, y
            o.t_visto = self.t
            vistos.add(clave)
        for clave, o in list(ecos.items()):
            if clave not in vistos and self.t - getattr(o, "t_visto", 0.0) > 1.2:
                self._sv_quitar_eco_poli(o)
                del ecos[clave]

    def _sv_quitar_eco_poli(self, o):
        if isinstance(o, Persona):
            if o in self.personas:
                self.personas.remove(o)
            if self.objetivo is o:
                self.objetivo = None
        elif not o.muerto:
            self.quitar_vehiculo(o)

    def _sv_quitar_policia(self, r):
        for o in list(getattr(r, "poli", {}).values()):
            self._sv_quitar_eco_poli(o)
        r.poli = {}

    def sv_golpe_policia(self, p, dano):
        """Le has dado a un agente de los que persiguen a otro jugador: el golpe va también a su juego."""
        if self.en_servidor and getattr(p, "eco_de", None) is not None and not getattr(self, "_sv_aplicando", False):
            self.red.enviar({"t": "po_golpe", "a": p.eco_de, "k": p.eco_poli, "dano": round(float(dano), 1)})

    def _svm_po_golpe(self, m):
        p = next((q for q in self.personas if q.tipo == "policia" and q.id == m.get("k") and not q.muerto), None)
        if p is not None:
            self._sv_aplicando = True
            try:
                self.danar_persona(p, float(m.get("dano", 0)))
            finally:
                self._sv_aplicando = False

    def _svm_patrulla_llega(self, m):
        """Una patrulla del servidor que rondaba cerca viene a por ti: desde ahora es de las que te persiguen."""
        if m.get("ya"):                                          # la sigue llevando el servidor: solo te enteras
            self.sv_dicho("patrulla", "Una patrulla que rondaba por aquí viene a por ti.", 8.0)
            return
        if not self.j.estrellas or "patrulla" not in self.modelos:
            return
        v = self.crear_vehiculo("patrulla", float(m.get("x", 0)), float(m.get("y", 0)), int(m.get("d", 0)) % 4, "policia")
        v.ocupado, v.hostil, v.vel = True, True, 12.0
        self.sv_dicho("patrulla", "Una patrulla que rondaba por aquí viene a por ti.", 8.0)

    def _svm_visto(self, m):
        self.decir("Te ha visto una patrulla.")
        self.delito(2, "disparos delante de una patrulla", siempre=True)

    # --------------------------------------------- la policía que lleva el servidor
    def sv_policia_comun(self):
        """¿La búsqueda, la persecución y la detención las lleva el servidor? Entonces tu juego no pone su policía."""
        return self.en_servidor and bool(self.sv["info"].get("policia"))

    def sv_delito(self, puntos):
        if self.sv_policia_comun() and puntos > 0:
            self.red.enviar({"t": "delito", "n": round(float(puntos), 2)})

    def sv_busqueda(self, nivel, fin=False):
        """Tu juego pone un nivel de búsqueda, o la da por terminada: pintar el coche, pagar la multa, acabar en comisaría."""
        if self.sv_policia_comun() and not getattr(self, "_sv_busqueda_suya", False):
            self.red.enviar({"t": "busqueda", "nivel": int(nivel), "fin": bool(fin)})

    def _sv_limpiar_busqueda(self, hablar):
        self._sv_busqueda_suya = True                            # lo dice el servidor: no hace falta contárselo de vuelta
        try:
            self.limpiar_busqueda(hablar)
        finally:
            self._sv_busqueda_suya = False

    def _svm_nivel_busqueda(self, m):
        from .combate import UMBRAL
        try:
            es, pu = max(0, min(5, int(m.get("es") or 0))), float(m.get("pu") or 0)
        except (TypeError, ValueError):
            return
        self.sv["t_desfase"] = None
        if es == 0:
            if self.j.estrellas or self.j.puntos_busqueda:
                self._sv_limpiar_busqueda(m.get("motivo") == "perdida")
            return
        if m.get("motivo") == "vuelve":
            self.decir("La policía no se ha olvidado de ti: te siguen buscando.")
        self.j.puntos_busqueda = max(pu, float(UMBRAL[es - 1]))

    def _sv_cuadrar_busqueda(self, es):
        """El nivel de búsqueda que vale es el del servidor. Si el tuyo lleva unos segundos sin coincidir, se corrige."""
        from .combate import UMBRAL
        try:
            es = max(0, min(5, int(es or 0)))
        except (TypeError, ValueError):
            return
        mio = sum(1 for u in UMBRAL if self.j.puntos_busqueda >= u)
        if es == mio:
            self.sv["t_desfase"] = None
        elif self.sv["t_desfase"] is None:
            self.sv["t_desfase"] = self.t
        elif self.t - self.sv["t_desfase"] > 3.0:
            self.sv["t_desfase"] = None
            if es == 0:
                self._sv_limpiar_busqueda(False)
            else:
                self.j.puntos_busqueda = float(UMBRAL[es - 1])
                if es < self.j.estrellas:
                    self.j.estrellas = es

    def sv_buscando(self, dt):
        """Mientras te buscan: el tic de que no tienes a nadie cerca. Despistarlos lo decide el servidor."""
        j = self.j
        x, y = self.pos()
        r_p, r_v = (70, 80) if j.veh else (38, 45)
        cerca = any(p.tipo == "policia" and not p.muerto and p.dist(x, y) < r_p for p in self.personas) or \
            any(self.es_patrulla(v) and not v.muerto and v.dist(x, y) < r_v for v in self.vehiculos)
        if not cerca:
            self.t_buscando -= dt
            if self.t_buscando <= 0:
                self.t_buscando = 1.0
                self.son("buscando", vol=0.6, cat="interfaz")

    def es_patrulla(self, v):
        """Un coche de policía: de los de tu juego, o de los que lleva el servidor."""
        return v.ia == "policia" or bool(getattr(v, "tr_poli", False))

    def _sv_agentes(self, lista):
        """Los agentes a pie que lleva el servidor: están donde él dice, y van a por quien él dice."""
        gente = self.sv["agentes"]
        vistos = set()
        for f in lista:
            try:
                ident, x, y, obj, arma = f[0], float(f[1]), float(f[2]), f[3], str(f[4])
            except (TypeError, ValueError, IndexError):
                continue
            vistos.add(ident)
            p = gente.get(ident)
            if p is None:
                p = Persona("policia", x, y)
                p.po_id, p.tag, p.salud, p.estado, p.activo = ident, "comun", 80, "ataca", True
                self.personas.append(p)
                gente[ident] = p
            p.tx, p.ty, p.t_visto = x, y, self.t
            p.arma = arma if arma in self.armas_d else "pistola"
            p.hostil = obj == self.sv.get("id") and not p.muerto
        for ident, p in list(gente.items()):
            if ident not in vistos and self.t - getattr(p, "t_visto", 0.0) > 1.2:
                del gente[ident]
                if p.muerto:
                    p.tag = None                         # el caído se queda un rato y luego lo retira tu juego
                elif p in self.personas:
                    self.personas.remove(p)
                    if self.objetivo is p:
                        self.objetivo = None

    def sv_agente_paso(self, p, d, dt):
        """Un agente del servidor en tu juego: va hacia donde dice el servidor, y se le oye andar."""
        tx, ty = getattr(p, "tx", p.x), getattr(p, "ty", p.y)
        falta = math.hypot(tx - p.x, ty - p.y)
        f = min(1.0, dt * 10.0)
        p.x += (tx - p.x) * f
        p.y += (ty - p.y) * f
        if falta > 0.15 and d < 30:
            p.t_paso -= dt
            if p.t_paso <= 0:
                p.t_paso = 0.33
                self.son("paso_npc", xy=(p.x, p.y), ref=3, maxd=30, vol=0.9, tono=0.85)

    def sv_golpe_agente(self, p, dano):
        """Le has dado a un agente del servidor: lo que le pase, le pasa para todos."""
        if self.en_servidor and getattr(p, "po_id", None) is not None and not p.muerto:
            self.red.enviar({"t": "po_dano", "id": p.po_id, "n": round(float(dano), 1), "cae": p.salud - dano <= 0})

    def _svm_po_cae(self, m):
        p = self.sv["agentes"].get(m.get("id"))
        if p is not None and not p.muerto:
            p.muerto, p.hostil, p.t_estado = True, False, self.t
            self.son("muerte_npc", xy=(p.x, p.y), ref=6, tono=p.tono)
            if self.objetivo is p:
                self.objetivo = None

    def _svm_po_apunta(self, m):
        self.son("amartillar", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=5, maxd=50)

    def _svm_po_disparo(self, m):
        """Un agente dispara. Lo oyen todos los que están cerca; le da, si le da, a quien persigue."""
        try:
            x, y, da = float(m.get("x", 0)), float(m.get("y", 0)), float(m.get("da") or 0)
        except (TypeError, ValueError):
            return
        a = self.armas_d.get(m.get("arma")) or self.armas_d.get("pistola") or self.armas_d["punos"]
        self.son(a["sonido"], xy=(x, y), ref=14, maxd=220, vol=0.9)
        if m.get("a") != self.sv.get("id") or self.transicion:
            return
        j = self.j
        if da <= 0:
            self.son("bala_silbido", pan=random.uniform(-0.9, 0.9), vol=0.5)
        elif j.veh:
            self.son("bala_impacto", vol=0.6)
            self.danar_vehiculo(j.veh, da)
            if random.random() < 0.3:
                self.danar_jugador(da * 0.5, (x, y))
        else:
            self.danar_jugador(da, (x, y))

    def _svm_po_embiste(self, m):
        v = self.j.veh
        if v is None:
            return
        self.son("choque_leve")
        self.danar_vehiculo(v, float(m.get("n") or 7))
        v.vel *= 0.75

    def _svm_detenido(self, m):
        """Un agente te ha echado el guante. Lo que venga después (la multa, el soborno, el calabozo) es lo de siempre."""
        if self.j.estrellas == 0:
            self.j.estrellas = 1
        self.detener()

    # ------------------------------------------------------- gente de la calle
    def sv_peatones_comunes(self):
        """¿La gente de la calle la pone el servidor? Entonces tu juego no pone la suya."""
        return self.en_servidor and bool(self.sv["info"].get("peatones"))

    def _sv_peatones(self, lista):
        gente = self.sv["peatones"]
        vuelta = 4 * (M.B - 15)
        vistos = set()
        for f in lista:
            try:
                ident, bi, bj, u, s, huye, vel = f[0], int(f[1]), int(f[2]), float(f[3]), int(f[4]), bool(f[5]), float(f[6])
                atracado = bool(f[7]) if len(f) > 7 else False
            except (TypeError, ValueError, IndexError):
                continue
            vistos.add(ident)
            p = gente.get(ident)
            if p is None:
                p = Persona("civil", 0, 0)
                p.bloque, p.u, p.pe_id, p.tag = (bi, bj), u, ident, "comun"
                self._pos_perimetro(p)
                self.personas.append(p)
                gente[ident] = p
            p.t_visto = self.t
            if p.muerto:
                continue
            if abs(((p.u - u + vuelta / 2) % vuelta) - vuelta / 2) > 3:       # se ha desviado de donde dice el servidor
                p.u = u
            p.sentido, p.vel = s, vel
            if huye:
                p.estado, p.t_estado, p.t_voz = "huye", 3.0, 5.0
            elif p.estado == "huye" and getattr(p, "t_susto", -99) < self.t - 1.5:
                p.estado = "pasea"
            if atracado:
                p.atracado = True
        for ident, p in list(gente.items()):
            if ident not in vistos and self.t - getattr(p, "t_visto", 0.0) > 1.5:
                del gente[ident]
                if p.muerto:
                    p.tag = None                         # el caído se queda un rato y luego lo retira tu juego
                elif p in self.personas:
                    self.personas.remove(p)
                    if self.objetivo is p:
                        self.objetivo = None

    def sv_golpe_peaton(self, p, dano):
        """Le has dado a alguien de la calle que es de todos: lo que le pase, le pasa para todos."""
        if self.en_servidor and getattr(p, "pe_id", None) is not None and not p.muerto:
            p.t_susto = self.t
            self.red.enviar({"t": "pe_dano", "id": p.pe_id, "n": round(float(dano), 1), "cae": p.salud - dano <= 0})

    def sv_peaton_atracado(self, p):
        if self.en_servidor and getattr(p, "pe_id", None) is not None:
            p.t_susto = self.t
            self.red.enviar({"t": "pe_atraco", "id": p.pe_id})

    def _svm_pe_cae(self, m):
        p = self.sv["peatones"].get(m.get("id"))
        if p is not None and not p.muerto:
            p.muerto, p.t_estado = True, self.t
            self.son("muerte_npc", xy=(p.x, p.y), ref=6, tono=p.tono)
            if self.objetivo is p:
                self.objetivo = None

    # ------------------------------------------------------------ tráfico común
    def sv_trafico_comun(self):
        """¿Los coches que circulan los pone el servidor? Entonces tu juego no pone los suyos."""
        return self.en_servidor and bool(self.sv["info"].get("trafico"))

    def _sv_trafico(self, lista):
        vistos = set()
        for fila in lista:
            try:
                ident, modelo, x, y, rumbo, vel = fila[0], fila[1], float(fila[2]), float(fila[3]), float(fila[4]), float(fila[5])
                poli = int(fila[6]) if len(fila) > 6 else 0
            except (TypeError, ValueError, IndexError):
                continue
            v = self.sv["trafico"].get(ident)
            if v is None or v.muerto:
                if modelo not in self.modelos:
                    continue
                v = self.crear_vehiculo(modelo, x, y, M.dir_de_rumbo(rumbo), "servidor")
                v.tr_id, v.ocupado, v.cerrado, v.tr_poli = ident, True, False, bool(poli)
                if poli:
                    v.nombre = "Coche patrulla"
                self.sv["trafico"][ident] = v
            if poli >= 2 and v.sirena is None:                   # persigue a alguien: con la sirena puesta
                otras = sum(1 for o in self.vehiculos if o is not v and o.sirena is not None)
                v.sirena = self.son("sirena", bucle=True, xy=(x, y), ref=14, maxd=260, vol=0.8 / (1 + 0.6 * otras))
            elif poli < 2 and v.sirena is not None and v.tr_poli:
                v.sirena.parar()
                v.sirena = None
            if poli == 3 and not v.desplegado:                   # para y se bajan los agentes
                v.desplegado, v.ocupado = True, False
                self.son("puerta_coche", xy=(x, y))
            elif poli == 2 and v.desplegado:                     # se les escapa: se suben otra vez y siguen
                v.desplegado, v.ocupado = False, True
                self.son("puerta_coche", xy=(x, y))
            v.tx, v.ty, v.rumbo, v.vel, v.t_visto = x, y, rumbo, vel, self.t
            v.dir = M.dir_de_rumbo(rumbo)
            vistos.add(ident)
        for ident, v in list(self.sv["trafico"].items()):
            if ident not in vistos and self.t - getattr(v, "t_visto", 0.0) > 1.2:
                del self.sv["trafico"][ident]
                if v is not self.j.veh and not v.muerto:
                    self.quitar_vehiculo(v)

    def sv_trafico_paso(self, v, d, dt):
        """Un coche del tráfico común en tu juego: se mueve hacia donde dice el servidor y suena donde está."""
        f = min(1.0, dt * 10.0)
        v.x += (getattr(v, "tx", v.x) - v.x) * f
        v.y += (getattr(v, "ty", v.y) - v.y) * f
        if d < 100:
            self._motor(v, False)
            v.canal.mover(v.x, v.y)
            v.canal.tono(v.modelo["tono"] * (0.6 + 1.3 * abs(v.vel) / v.modelo["vel_max"]))
        elif v.canal:
            v.canal.parar()
            v.canal = None
        j = self.j
        if v.sirena:
            v.sirena.mover(v.x, v.y)
        if not j.veh and v.vel > 3 and d < 2.4 and self.t > v.t_choque and not getattr(v, "eco_poli", False):      # te atropella, como cualquier coche
            v.t_choque = self.t + 1.5
            self.son("golpe")
            self.danar_jugador(v.vel * 2.2, (v.x, v.y))
            self.decir("¡Te ha atropellado un vehículo!")

    def _svm_tr_revienta(self, m):
        v = self.sv["trafico"].pop(m.get("id"), None)
        if v is not None and not v.muerto and v is not self.j.veh:
            v.tr_id, v.ia = None, None
            self.explotar(v)
        elif m.get("m") == self.mundo.id:
            self.son("explosion", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=30, maxd=400)

    def _svm_chat(self, m):
        canal = {"cerca": " aquí cerca", "banda": " a la banda", "priv": " solo a ti", "grupo": " al grupo"}.get(m.get("canal"), "")
        linea = f"{m.get('nombre', 'Alguien')}{canal}: {m.get('texto', '')}"
        self.chat.append(linea)
        del self.chat[:-40]
        self.son("chat", cat="interfaz")
        with registro.privado():
            self.decir(f"{m.get('nombre', 'Alguien')} dice{canal}: {m.get('texto', '')}")

    def _svm_cobro(self, m):
        n = min(self.j.dinero, max(0, int(m.get("n", 0))))
        self.j.dinero -= n
        self.son("caja" if "caja" in self.mez.sonidos else "dinero", cat="interfaz", vol=0.6)
        self.decir(f"Pagas {n} euros: {m.get('motivo', '')}. Te quedan {self.j.dinero}.")

    def _svm_recibe(self, m):
        clase, ident, n = m.get("clase"), str(m.get("id", "")), max(1, int(m.get("n", 1)))
        nombre = m.get("nombre", "Alguien")
        if clase == "arma" and ident in self.armas_d:
            self.dar_arma(ident, 0)
            self.decir(f"{nombre} te da: {self.armas_d[ident]['nombre']}.")
        elif clase == "balas" and ident in self.j.armas:
            self.j.armas[ident]["reserva"] += n
            self.son("recarga", vol=0.6)
            self.decir(f"{nombre} te da {n} balas de {self.armas_d[ident]['nombre'].lower()}.")
        elif clase == "objeto" and ident in {o["id"] for o in self.datos["objetos"]}:
            self.j.objetos[ident] = self.j.objetos.get(ident, 0) + n
            self.son("recoger", cat="interfaz")
            self.decir(f"{nombre} te da {n} de {next(o['nombre'] for o in self.datos['objetos'] if o['id'] == ident).lower()}.")
        elif clase in ("arma", "objeto"):        # algo de otra versión del juego, o de un mod, que tu juego no tiene
            self.decir(f"{nombre} te quiere dar algo que no existe en tu versión del juego, y no lo puedes recibir.")

    def _svm_dado(self, m):
        self.son("recoger", cat="interfaz", vol=0.5)
        self.decir(f"Entregado a {m.get('nombre', 'tu compañero')}.")

    def _svm_quien(self, m):
        self.sv["quien"] = m.get("e") or []

    def _svm_pasivo(self, m):
        self.sv["pasivo"] = bool(m.get("si"))
        self.son("notificacion", cat="interfaz", vol=0.5)
        self.decir("Modo pasivo activado: no puedes herir a otros jugadores ni ellos a ti." if self.sv["pasivo"] else "Modo pasivo quitado: vuelves a estar expuesto.")

    def _svm_expulsado(self, m):
        self.sv_salir(str(m.get("motivo") or "Te han sacado del servidor."), al_menu=True)

    def _svm_cerrado(self, m):
        self.sv_salir(str(m.get("motivo") or "El servidor se ha cerrado.") + " Tu personaje está guardado.", al_menu=True)

    def _svm_desconectado(self, m):
        registro.aviso("red", "Se ha cortado la conexión con el servidor")
        self.sv_salir("Se ha perdido la conexión con el servidor. Tu personaje se guardó hace menos de un minuto: vuelve a entrar para seguir.", al_menu=True)

    # ----------------------------------------------------------------- economía
    def _sv_ajustar_saldo(self, sobra, callar=False):
        """Quita lo que el servidor no reconoce: primero del bolsillo y luego del banco."""
        if sobra <= 0:
            return
        j = self.j
        de_mano = min(j.dinero, sobra)
        j.dinero -= de_mano
        j.banco -= min(j.banco, sobra - de_mano)
        if not callar:
            self.app.son("error")
            self.decir(f"El servidor no reconoce {sobra} euros de lo que llevas, y se retiran. En un servidor no se puede ganar más de un tanto por hora "
                       "fuera de las misiones y de lo que te dan otros jugadores.")

    def _svm_saldo(self, m):
        self._sv_ajustar_saldo(max(0, int(m.get("quita", 0))))

    def sv_mision_ok(self, m):
        """Has completado una misión tuya: se lo dices al servidor para que dé por buena la recompensa."""
        if self.en_servidor and not m.get("generada"):
            self.red.enviar({"t": "mision_ok", "id": m["id"]})

    # -------------------------------------------------------------- propiedades
    def sv_dueno(self, l):
        """El nombre del jugador dueño de una casa o un negocio, si es de otro. None si es tuyo o de nadie."""
        if not self.en_servidor:
            return None
        d = self.sv["props"].get(l.id)
        return d["nombre"] if d is not None and d.get("cuenta") != self.sv.get("cuenta") else None

    def sv_comprado(self, l):
        """Has comprado una casa o un negocio: en un servidor queda a tu nombre para todos."""
        if self.en_servidor and int(l.get("precio", 0) or 0) > 0:
            self.sv["props"][l.id] = {"cuenta": self.sv.get("cuenta"), "nombre": self.red.nombre}
            self.red.enviar({"t": "prop_comprar", "lugar": l.id})

    def _sv_cuadrar_propiedades(self):
        """Al entrar: lo tuyo que el servidor aún no tiene apuntado se apunta, y lo que ya es de otro se te devuelve."""
        for pid in list(self.j.propiedades):
            l = self.lugares.get(pid)
            if l is None or int(l.get("precio", 0) or 0) <= 0 or l.tipo not in ("casa", "negocio"):
                continue
            d = self.sv["props"].get(pid)
            if d is None:
                self.sv_comprado(l)
            elif d.get("cuenta") != self.sv.get("cuenta"):
                self._sv_devolver(l, d.get("nombre", "otro jugador"))

    def _sv_devolver(self, l, nombre):
        if l.id in self.j.propiedades:
            self.j.propiedades.remove(l.id)
            precio = int(l.get("precio", 0) or 0)
            self.j.dinero += precio
            self.app.son("error")
            self.decir(f"{l.nombre} ya es de {nombre}: se te ha adelantado. Te devuelven los {precio} euros.")

    def _svm_prop(self, m):
        yo = self.sv.get("cuenta")
        l = self.lugares.get(m.get("lugar"))
        if m.get("cuenta") is None:
            self.sv["props"].pop(m.get("lugar"), None)
        else:
            self.sv["props"][m.get("lugar")] = {"cuenta": m.get("cuenta"), "nombre": str(m.get("nombre", "")), "oferta": int(m.get("oferta") or 0)}
        if l is None:
            return
        if m.get("antes") == yo and m.get("cuenta") != yo:       # era tuyo y lo has vendido: el dinero llega aparte
            if l.id in self.j.propiedades:
                self.j.propiedades.remove(l.id)
        elif m.get("cuenta") == yo:
            if l.id not in self.j.propiedades:                   # se lo has comprado a otro jugador
                self.j.propiedades.append(l.id)
                self.son("mision_ok", cat="interfaz")
                self.decir(f"¡{l.nombre} es tuyo!")
        elif m.get("cuenta") is not None:
            self._sv_devolver(l, str(m.get("nombre", "otro jugador")))

    def sv_oferta(self, l):
        """Por cuánto vende su dueño esta propiedad a otros jugadores. Cero si no la vende."""
        d = self.sv["props"].get(l.id) if self.en_servidor else None
        return int(d.get("oferta") or 0) if d else 0

    def _svm_prop_no(self, m):
        l = self.lugares.get(m.get("lugar"))
        if l is not None:
            self.sv["props"][l.id] = {"cuenta": -1, "nombre": str(m.get("nombre", ""))}
            self._sv_devolver(l, str(m.get("nombre", "otro jugador")))

    def sv_robar_negocio(self, l):
        self.red.enviar({"t": "robo", "lugar": l.id})

    def _svm_robo_empieza(self, m):
        l = self.lugares.get(m.get("lugar"))
        self.sv["robo"] = m.get("lugar")
        self.son("alarma", xy=(l.x, l.y) if l else None, vol=0.7)
        self.delito(3, "atraco a un negocio", siempre=True)
        self.decir(f"¡Atraco! Salta la alarma y a {m.get('nombre', 'su dueño')} le llega el aviso. Aguanta en la puerta {m.get('segundos', 20)} segundos, a pie, sin alejarte.", True)

    def _svm_robo_fin(self, m):
        self.sv["robo"] = None
        if m.get("ok"):
            n = max(0, int(m.get("botin", 0)))
            self.j.dinero += n
            self.j.stats["dinero_ganado"] += n
            self.son("dinero", cat="interfaz")
            self.decir(f"Caja vaciada: {n} euros. Lárgate antes de que llegue su dueño.", True)
        else:
            self.app.son("error")
            self.decir(str(m.get("motivo") or "El atraco ha fallado."), True)

    def _svm_robo_aviso(self, m):
        l = self.lugares.get(m.get("lugar"))
        r = self.remotos.get(m.get("de"))
        if r is not None:
            r.hostil, r.t_hostil = True, self.t           # quien te roba es enemigo: la Q le fija
        self.son("alarma", cat="interfaz", vol=0.7)
        self.app.vibrar(0.8, 0.8, 500)
        de_quien = "tu negocio" if m.get("tuyo") else "un negocio de tu banda"
        self.decir(f"¡{m.get('nombre', 'Alguien')} está atracando {de_quien}, {self.nombre_lugar(l) if l else ''}! Tienes {m.get('segundos', 20)} segundos para impedirlo.", True)
        if l is not None and not self.mision and self.gps is None:
            self.gps_a_lugar(l, callar=True)

    def _sv_descontar_robos(self, total):
        if total <= 0:
            return
        j = self.j
        de_mano = min(j.dinero, total)
        j.dinero -= de_mano
        del_banco = min(j.banco, total - de_mano)
        j.banco -= del_banco
        self.son("animo_baja", cat="interfaz")
        self.decir(f"A tus negocios les han robado {total} euros de la caja. Se te descuentan {de_mano + del_banco}.")

    def _svm_robos_dia(self, m):
        self._sv_descontar_robos(int(m.get("total") or 0))

    # ------------------------------------------------------------------ combate
    def sv_objetivos(self, todos):
        """Los otros jugadores a los que se puede apuntar: con la Q, los que te han atacado; con Mayúsculas, todos."""
        if not self.en_servidor or not self.sv["info"].get("pvp"):
            return []
        x, y = self.pos()
        return [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and (r.hostil or todos) and r.dist(x, y) < 90]

    def sv_atacar(self, o, arma):
        """Disparas o golpeas a otro jugador: el servidor dice si llega."""
        self.red.enviar({"t": "ataque", "a": o.id, "arma": arma["id"]})

    def _sv_jugador_al_lado(self, radio):
        x, y = self.pos()
        cerca = [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and not r.veh and r.dist(x, y) <= radio]
        return min(cerca, key=lambda r: r.dist(x, y)) if cerca else None

    def sv_atracar_cerca(self):
        """La E junto a otro jugador: le atracas, como a cualquiera. True si había alguien."""
        if not self.en_servidor or not self.sv["info"].get("pvp"):
            return False
        r = self._sv_jugador_al_lado(4.5)
        if r is None:
            return False
        if self.arma()["id"] == "punos":
            self.decir("Para atracar a alguien tienes que empuñar un arma.", True)
            return True
        self.son("grito", vol=0.5)
        self.red.enviar({"t": "atraco", "a": r.id})
        return True

    def sv_hablar_cerca(self):
        """La J junto a otro jugador, sin nadie más a quien hablar: le escribes a él. True si había alguien."""
        if not self.en_servidor:
            return False
        r = self._sv_jugador_al_lado(8.0)
        if r is None:
            return False
        from . import menus_enlinea
        menus_enlinea.chat(self, "priv", r.id, f"Qué le dices a {r.nombre}")
        return True

    def _svm_atracado(self, m):
        n = min(self.j.dinero, max(0, int(m.get("pierde", 0))))
        self.j.dinero -= n
        self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
        self.son("grito", vol=0.6)
        self.app.vibrar(0.6, 0.6, 300)
        self.decir(f"¡{m.get('nombre', 'Alguien')} te atraca a punta de arma! Te quita {n} euros. Pulsa Q para fijarle.", True)

    def _svm_atraco_ok(self, m):
        n = max(0, int(m.get("botin", 0)))
        self.j.dinero += n
        self.j.stats["dinero_ganado"] += n
        self.son("dinero", cat="interfaz")
        self.delito(1.5, "atraco")
        self.decir(f"Atracas a {m.get('nombre', 'otro jugador')}: {n} euros." if n else f"Atracas a {m.get('nombre', 'otro jugador')}, pero no lleva nada encima.", True)

    def sv_explosion(self, x, y, arma_id):
        if self.en_servidor and arma_id:
            self.red.enviar({"t": "explosion", "x": round(x, 1), "y": round(y, 1), "arma": arma_id})

    def _sv_agresor(self, ident, nombre):
        self.sv["agresor"], self.sv["t_agresor"] = ident, self.t
        r = self.remotos.get(ident)
        if r is not None:
            if not r.hostil:
                self.sv_dicho("ataca", f"¡{nombre} te ataca! Pulsa Q para fijarlo.", 5.0)
            r.hostil, r.t_hostil = True, self.t

    def _svm_herido(self, m):
        self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
        a = self.armas_d.get(m.get("arma"))
        ox, oy = float(m.get("x", self.j.x)), float(m.get("y", self.j.y))
        if a is not None:
            self.son(a["sonido"], xy=(ox, oy), ref=18 if a["tipo"] == "fuego" else 6, maxd=260)
        dano = float(m.get("dano", 0))
        if self.j.veh is not None:
            self.danar_vehiculo(self.j.veh, dano * 0.6)
        factor = self.dificultad() or 1.0        # entre jugadores no cuenta la dificultad que cada uno tenga puesta
        self.danar_jugador(dano / factor, (ox, oy))

    def _svm_silbido(self, m):
        self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
        self.son("bala_silbido", vol=0.8)

    def _svm_tiro(self, m):
        pass                                         # el disparo ya se oye por el aviso de ruido de quien dispara

    def sv_ruido(self, que):
        """Lo que haces y se oye: un disparo, un grito. Los demás jugadores de la localidad lo oyen donde estás."""
        if self.en_servidor:
            self.red.enviar({"t": "evento", "que": que[:20]})

    def _svm_evento(self, m):
        r = self.remotos.get(m.get("de"))
        if r is None or r.mapa != self.mundo.id:
            return
        que = str(m.get("que", ""))
        if que == "claxon":
            modelo = self.modelos.get(r.veh or "utilitario", {})
            self.son(modelo.get("claxon", "claxon"), xy=(r.x, r.y), ref=10, maxd=220, vol=0.8)
            return
        if que.startswith("d:"):
            a = self.armas_d.get(que[2:])
            if a is None:
                return
            self.son(a["sonido"], xy=(r.x, r.y), ref=18, maxd=260)
            radio = 40
        elif que == "grito":
            self.son("grito", xy=(r.x, r.y), ref=8, maxd=90, vol=0.7)
            radio = 15
        else:
            return
        for p in self.personas:                      # la gente de tu calle se asusta igual que si lo hubieras hecho tú
            if p.tipo == "civil" and not p.muerto and p.estado == "pasea" and p.dist(r.x, r.y) < radio:
                p.estado, p.t_estado = "huye", 8

    def _svm_estalla(self, m):
        self.son("explosion", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=30, maxd=400)

    def _svm_impacto(self, m):
        if self.cfg["aviso_acierto"]:
            self.son("tono_objetivo", cat="interfaz", vol=0.45, tono=2.0)
            self.app.vibrar(0.15, 0.8, 90)
        r = self.remotos.get(m.get("a"))
        if r is not None:
            self.son("dolor_npc", xy=(r.x, r.y), ref=6)
        self.sv_dicho("impacto", f"Atropellas a {m.get('nombre', 'alguien')}." if m.get("atropello") else f"Le das a {m.get('nombre', 'alguien')}.", 3.0)

    def _svm_fallo(self, m):
        if m.get("motivo"):
            self.sv_dicho("motivo", str(m["motivo"]), 3.0, True)
        elif m.get("lejos"):
            self.sv_dicho("lejos", "Fuera de alcance.", 2.5)

    def sv_al_morir(self):
        """Has caído. Si ha sido ante otro jugador, el servidor reparte el botín."""
        if self.en_servidor and self.sv["agresor"] is not None and self.t - self.sv["t_agresor"] < 15:
            self.red.enviar({"t": "caido", "por": self.sv["agresor"]})
        if self.en_servidor:
            self.sv["agresor"] = None
            self.sv["protegido"] = time.time() + float(self.sv["info"].get("proteccion", 0))

    def _svm_caes(self, m):
        n = min(self.j.dinero, max(0, int(m.get("pierde", 0))))
        self.j.dinero -= n
        self.decir(f"Has caído ante {m.get('nombre', 'otro jugador')}. Se lleva {n} euros de lo que llevabas encima.")

    def _svm_baja(self, m):
        n = max(0, int(m.get("botin", 0)))
        self.j.dinero += n
        self.j.stats["dinero_ganado"] += n
        r = self.remotos.get(m.get("a"))
        if r is not None:
            r.hostil = False
            if self.objetivo is r:
                self.objetivo = None
        self.son("mision_ok", cat="interfaz", vol=0.5)
        self.decir(f"Has tumbado a {m.get('nombre', 'otro jugador')}. Te llevas {n} euros.{m.get('texto', '')}")

    def _svm_buscado(self, m):
        self.sv["recompensa"] = int(m.get("recompensa", 0))
        self.decir(f"Has tumbado a alguien que no se defendía. Ofrecen {self.sv['recompensa']} euros por tu cabeza, y la policía te busca.")
        if self.mundo.policia:
            self.poner_busqueda(2)

    def _svm_muerte(self, m):
        self.sv_dicho("muerte", f"{m.get('por', 'Alguien')} ha tumbado a {m.get('quien', 'alguien')}.", 1.0)

    # ---------------------------------------------------------------- vehículos
    def sv_poner_vehiculos(self):
        """Pone en tu calle los vehículos que otros jugadores han dejado aparcados en esta localidad."""
        if not self.en_servidor:
            return
        self.sv["trafico"] = {k: v for k, v in self.sv["trafico"].items() if not v.muerto and v in self.vehiculos}
        for r in self.remotos.values():              # al cambiar de localidad, lo que había de otros ya no está
            r.poli = {}
        self.sv["peatones"] = {}
        presentes = {getattr(v, "id_red", None) for v in self.vehiculos if not v.muerto}
        for d in self.sv["vehs"].values():
            if d.get("por") is None and d.get("m") == self.mundo.id and d["id"] not in presentes:
                self._sv_crear_copia(d)

    def _sv_crear_copia(self, d):
        if d.get("modelo") not in self.modelos:
            return None
        v = self.crear_vehiculo(d["modelo"], float(d["x"]), float(d["y"]), M.dir_de_rumbo(float(d.get("r", 0))), None, d.get("nombre"))
        v.rumbo = float(d.get("r", 0))
        v.salud = min(v.salud_max, float(d.get("salud", v.salud_max)))
        v.id_red, v.red_mio, v.cerrado = d["id"], False, False
        if d.get("mejoras"):
            from . import sistemas
            sistemas.poner(v, d.get("mejoras"))
        return v

    def _sv_copia(self, ident):
        return next((v for v in self.vehiculos if getattr(v, "id_red", None) == ident and not v.muerto), None)

    def sv_subido(self, v):
        """Te has subido a un vehículo: si era de tu mundo, desde ahora es de todos."""
        if not self.en_servidor or v.tag or getattr(v, "id_red", None) is not None:
            return
        v.red_ref = v.id
        self.red.enviar({"t": "veh_tomar", "modelo": v.modelo["id"], "nombre": v.nombre, "salud": round(v.salud, 1), "ref": v.id,
                         "mejoras": dict(getattr(v, "mejoras", {}) or {})})

    def sv_bajado(self, v):
        if self.en_servidor and getattr(v, "red_mio", False) and not v.muerto:
            v.red_mio, v.red_dueno = False, True
            d = {"id": v.id_red, "modelo": v.modelo["id"], "nombre": v.nombre, "m": self.mundo.id, "x": round(v.x, 1), "y": round(v.y, 1),
                 "r": round(v.rumbo), "salud": round(v.salud, 1), "por": None}
            self.sv["vehs"][v.id_red] = d
            self.red.enviar(dict(d, t="veh_dejar"))

    def sv_quitado(self, v):
        """Un vehículo tuyo deja de existir: al garaje, vendido o reventado."""
        if self.en_servidor and getattr(v, "id_red", None) is not None and (getattr(v, "red_mio", False) or getattr(v, "red_dueno", False)):
            v.red_mio = v.red_dueno = False
            self.sv["vehs"].pop(v.id_red, None)
            self.red.enviar({"t": "veh_fin", "id": v.id_red})

    def sv_pedir_vehiculo(self, v):
        """F junto a un vehículo aparcado de otro jugador: se lo pides al servidor. True si hay que esperar la respuesta."""
        if self.en_servidor and (getattr(v, "eco_poli", False) or (getattr(v, "tr_poli", False) and not v.desplegado)):
            self.decir("Ese coche patrulla está lleno de policías.", True)
            return True
        if self.en_servidor and getattr(v, "tr_id", None) is not None and v.ia == "servidor":      # un coche del tráfico común
            if abs(v.vel) > 6:
                self.decir("Va demasiado rápido para abrir la puerta. Ponte delante: frenará.", True)
            else:
                self.red.enviar({"t": "tr_robar", "id": v.tr_id})
            return True
        if not self.en_servidor or getattr(v, "id_red", None) is None or getattr(v, "red_mio", False):
            return False
        self.red.enviar({"t": "veh_subir", "id": v.id_red})
        return True

    def sv_asaltar_cerca(self):
        """F junto al vehículo que conduce otro jugador: intentas sacarle. True si había alguien."""
        if not self.en_servidor:
            return False
        x, y = self.pos()
        cerca = [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and r.veh and getattr(r, "vid", None) and r.dist(x, y) <= 6]
        if not cerca:
            return False
        r = min(cerca, key=lambda r: r.dist(x, y))
        self.red.enviar({"t": "veh_asaltar", "id": r.vid})
        return True

    def sv_dano_copia(self, v, dano):
        """Le das a un vehículo aparcado de otro jugador: el daño lo lleva el servidor. True si era uno de esos."""
        if self.en_servidor and getattr(v, "eco_poli", False):
            return True                              # la patrulla de otro jugador: en tu juego es solo su presencia
        if self.en_servidor and getattr(v, "tr_id", None) is not None and v.ia == "servidor":
            self.red.enviar({"t": "tr_dano", "id": v.tr_id, "n": round(dano, 1)})
            return True
        if self.en_servidor and getattr(v, "id_red", None) is not None and not getattr(v, "red_mio", False):
            self.red.enviar({"t": "veh_dano", "id": v.id_red, "n": round(dano, 1)})
            return True
        return False

    def _svm_veh_tuyo(self, m):
        v = next((x for x in self.vehiculos if getattr(x, "red_ref", None) == m.get("ref") and getattr(x, "id_red", None) is None), None)
        if v is not None:
            v.id_red, v.red_mio = m["id"], self.j.veh is v
            if not v.red_mio:                        # ya se había bajado antes de que llegara la respuesta
                v.red_mio = True
                self.sv_bajado(v)

    def _svm_veh_ocupado(self, m):
        d = m.get("v") or {}
        if d.get("id") is not None:
            self.sv["vehs"][d["id"]] = d
        if m.get("tr") is not None:                              # otro jugador se ha quedado un coche del tráfico
            t = self.sv["trafico"].pop(m["tr"], None)
            if t is not None and not t.muerto and t is not self.j.veh:
                self.quitar_vehiculo(t)
        v = self._sv_copia(m.get("id"))
        if v is not None and v is not self.j.veh:
            v.red_dueno = False                      # ya no es tuyo: se lo ha llevado otro
            self.quitar_vehiculo(v)

    def _svm_veh_libre(self, m):
        d = m.get("v") or {}
        if d.get("id") is None:
            return
        self.sv["vehs"][d["id"]] = d
        if d.get("m") == self.mundo.id and self._sv_copia(d["id"]) is None:
            self._sv_crear_copia(d)

    def _svm_veh_ok(self, m):
        d = m.get("v") or {}
        if m.get("tr") is not None:                              # era un coche del tráfico: el conductor sale corriendo
            t = self.sv["trafico"].pop(m["tr"], None)
            if t is not None and not t.muerto:
                t.ia, t.ocupado, t.tr_id, t.id_red, t.red_mio = None, False, None, m["id"], False
                if getattr(t, "tr_poli", False):                 # una patrulla con los agentes fuera: nadie al volante
                    t.tr_poli, t.desplegado = False, False
                    if t.sirena is not None:
                        t.sirena.parar()
                        t.sirena = None
                    self.delito(3, "robo de un coche patrulla", siempre=True)
                else:
                    c = Persona("civil", *self.mundo.punto_libre(t.x + 2, t.y + 2), nombre="Conductor")
                    c.estado, c.t_estado = "huye", 12
                    self.personas.append(c)
                    self.son("grito", xy=(c.x, c.y), tono=c.tono)
                    self.delito(2, "robo de vehículo con violencia")
        v = self._sv_copia(m.get("id"))
        x, y = self.pos()
        if v is None:
            d = dict(d, x=x, y=y)
            v = self._sv_crear_copia(d)
            if v is None:
                return
        if m.get("asalto"):
            v.x, v.y = x, y
            self.son("grito", xy=(x, y), vol=0.6)
            self.decir(f"Sacas a {m['asalto']} del vehículo y te lo quedas.")
            self.delito(2, "robo de vehículo con violencia")
        elif m.get("robado"):
            self.delito(0.5, "robo de vehículo")
        v.red_mio = True
        self.sv["vehs"].pop(v.id_red, None)
        self._subir(v, bool(m.get("robado")))

    def _svm_veh_no(self, m):
        if m.get("motivo"):
            self.app.son("error")
            self.decir(str(m["motivo"]), True)

    def _svm_sacado(self, m):
        v = self.j.veh
        if v is not None:
            v.red_mio = v.red_dueno = False
            self.salir_vehiculo(forzado=True)
            v.red_dueno = False
            self.quitar_vehiculo(v)
        self._sv_agresor(m.get("por"), str(m.get("nombre", "Alguien")))
        self.son("puerta_coche")
        self.decir(f"¡{m.get('nombre', 'Alguien')} te saca del vehículo y se lo lleva!", True)

    def _svm_veh_golpe(self, m):
        if self.j.veh is not None and getattr(self.j.veh, "id_red", None) == m.get("id"):
            self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
            self.danar_vehiculo(self.j.veh, float(m.get("n", 0)))

    def _svm_veh_salud(self, m):
        d = self.sv["vehs"].get(m.get("id"))
        if d is not None:
            d["salud"] = m.get("salud")
        v = self._sv_copia(m.get("id"))
        if v is not None:
            v.salud = min(v.salud_max, float(m.get("salud", v.salud)))
            self.son("bala_impacto", xy=(v.x, v.y), ref=10, maxd=150)

    def _svm_veh_revienta(self, m):
        self.sv["vehs"].pop(m.get("id"), None)
        v = self._sv_copia(m.get("id"))
        if v is not None and v is not self.j.veh:
            v.id_red = None
            self.explotar(v)
        elif m.get("m") == self.mundo.id:
            self.son("explosion", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=30, maxd=400)

    def _svm_veh_fuera(self, m):
        self.sv["vehs"].pop(m.get("id"), None)
        v = self._sv_copia(m.get("id"))
        if v is not None and v is not self.j.veh:
            v.red_dueno = False
            self.quitar_vehiculo(v)

    # ------------------------------------------------------------------- bandas
    def _svm_banda(self, m):
        antes = self.sv["banda"]
        self.sv["banda"], self.sv["rango"] = m.get("b"), m.get("rango")
        if antes and not self.sv["banda"]:
            self.decir("Ya no estás en ninguna banda.")
        elif self.sv["banda"] and not antes:
            self.son("territorio", cat="interfaz", vol=0.6)
            self.decir(f"Estás en la banda {self.sv['banda']['nombre']}.")

    def _svm_banda_invita(self, m):
        self.sv["inv_banda"] = {"nombre": str(m.get("nombre", "")), "de": str(m.get("de", ""))}
        self.son("notificacion", cat="interfaz")
        self.decir(f"{m.get('de', 'Alguien')} te invita a la banda {m.get('nombre', '')}. Abre el móvil con M, En línea, para aceptar o rechazar.")

    def _svm_de_banda(self, m):
        r = self.remotos.get(m.get("id"))
        if r is not None:
            r.banda = m.get("banda")

    def _svm_territorios(self, m):
        self.sv["territorios"] = m.get("e") or {"barrios": [], "guerras": []}

    def _svm_bandas(self, m):
        self.sv["bandas"] = m.get("e") or []
        if m.get("territorios"):
            self.sv["territorios"] = m["territorios"]

    def sv_dueno_barrio(self, mapa, barrio):
        return next((t for t in self.sv["territorios"].get("barrios", []) if t["mapa"] == mapa and t["barrio"] == barrio), None)

    def sv_relacion(self, r):
        """Qué es para ti otro jugador: de tu banda, del grupo, o nada."""
        if self.sv["grupo"] is not None and any(q["id"] == r.id for q in self.sv["miembros"]):
            return "de tu grupo"
        b = self.sv["banda"]
        if b and getattr(r, "banda", None) == b["id"]:
            return "de tu banda"
        return ""

    # --------------------------------------------------------- misiones en grupo
    def _svm_grupo(self, m):
        antes = self.sv["grupo"]
        self.sv["grupo"], self.sv["miembros"] = m.get("lider"), m.get("miembros") or []
        if self.sv["grupo"] is None:
            self._sv_quitar_ecos()
            if antes is not None:
                self.decir("El grupo se ha deshecho.")
        else:
            nombres = ", ".join(q["nombre"] for q in self.sv["miembros"] if q["id"] != self.red.id)
            self.decir(f"Grupo de misión: vas con {nombres}." + (" Lo llevas tú: lo que consigas en tus misiones lo compartís." if self.sv["grupo"] == self.red.id else ""))
            if self.sv["grupo"] == self.red.id and self.mision:
                self.sv_mision_paso()
                self.sv_mision_enemigos()

    def _svm_grupo_invita(self, m):
        self.sv["inv_grupo"] = {"de": m.get("de"), "nombre": str(m.get("nombre", "")), "mision": str(m.get("mision", ""))}
        self.son("notificacion", cat="interfaz")
        self.decir(f"{m.get('nombre', 'Alguien')} te invita a su grupo" + (f" para la misión {m['mision']}" if m.get("mision") else "")
                   + ". Abre el móvil con M, En línea, para aceptar o rechazar.")

    def _svm_paga_mision(self, m):
        n = max(0, int(m.get("n", 0)))
        self.j.dinero += n
        self.j.stats["dinero_ganado"] += n
        self.son("mision_ok", cat="interfaz")
        self.decir(f"Misión completada con {m.get('de', 'tu grupo')}: {m.get('titulo', '')}. Tu parte: {n} euros.")
        self._sv_quitar_ecos()

    def sv_lidero(self):
        return self.en_servidor and self.sv["grupo"] is not None and self.sv["grupo"] == self.red.id

    def sv_mision_paso(self):
        """Quien lleva el grupo cuenta a los demás en qué paso está su misión y dónde es."""
        ms = self.mision
        if not self.sv_lidero() or not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return
        p = ms["def"]["pasos"][ms["paso"]]
        if p["tipo"] in ("dialogo", "dar", "decision"):
            return
        l = self.lugares.get(p.get("destino") or p.get("lugar") or "")
        self.red.enviar({"t": "grupo_msg", "d": {"que": "paso", "titulo": ms["def"]["titulo"], "texto": self.txt(p.get("texto", "")), "tipo": p["tipo"],
                                               "lugar": l.id if l else None}})

    def sv_mision_enemigos(self):
        """Los enemigos de tu misión pasan a ser de todo el grupo: lo que le quite uno, se lo quita para todos."""
        ms = self.mision
        if not self.sv_lidero() or not ms or not ms.get("enemigos"):
            return
        lista = []
        for k, e in enumerate(ms["enemigos"]):
            e.eco_k = k
            if not e.muerto:
                lista.append({"k": k, "nombre": e.nombre, "salud": round(e.salud, 1), "arma": e.arma, "x": round(e.x, 1), "y": round(e.y, 1),
                              "inofensivo": bool(getattr(e, "inofensivo", False))})
        self.red.enviar({"t": "grupo_msg", "d": {"que": "enemigos", "mapa": self.mundo.id, "e": lista}})

    def sv_mision_fin(self, hecha, m=None):
        if not self.sv_lidero():
            return
        self.red.enviar({"t": "grupo_msg", "d": {"que": "fin", "hecha": bool(hecha), "titulo": (m or {}).get("titulo", "")}})
        if hecha and m is not None:
            self.red.enviar({"t": "mision_hecha", "id": m["id"]})

    def sv_golpe_eco(self, p, dano):
        """Has dado a un enemigo que es de todo el grupo: se lo cuentas a los demás."""
        if self.en_servidor and self.sv["grupo"] is not None and getattr(p, "eco_k", None) is not None and not getattr(self, "_sv_aplicando", False):
            self.red.enviar({"t": "grupo_msg", "d": {"que": "golpe", "k": p.eco_k, "dano": round(float(dano), 1)}})

    def _sv_quitar_ecos(self):
        for e in list(self.sv["ecos"].values()):
            if e in self.personas:
                self.personas.remove(e)
            if self.objetivo is e:
                self.objetivo = None
        self.sv["ecos"] = {}
        self.sv["mision_grupo"] = None

    def _svm_grupo_msg(self, m):
        d = m.get("d") or {}
        que = d.get("que")
        nombre = str(m.get("nombre", "tu compañero"))
        if que == "paso":
            self.sv["mision_grupo"] = {"titulo": str(d.get("titulo", "")), "texto": str(d.get("texto", "")), "lugar": d.get("lugar")}
            self.son("notificacion", cat="interfaz", vol=0.6)
            self.decir(f"Misión de {nombre}, {d.get('titulo', '')}: {d.get('texto', '')}")
            l = self.lugares.get(d.get("lugar") or "")
            if l is not None and not self.mision and (self.gps is None or self.gps.get("grupo")):
                self.gps_a_lugar(l, callar=True)
                if self.gps:
                    self.gps["grupo"] = True
        elif que == "enemigos" and m.get("de") == self.sv["grupo"]:
            if d.get("mapa") != self.mundo.id:
                return
            nuevos = 0
            for q in d.get("e") or []:
                k = q.get("k")
                if k in self.sv["ecos"]:
                    continue
                x, y = self.mundo.punto_libre(float(q.get("x", self.j.x)), float(q.get("y", self.j.y)))
                e = Persona("enemigo", x, y, str(q.get("nombre", "Enemigo")))
                e.salud = float(q.get("salud", 60))
                e.arma = q.get("arma") if q.get("arma") in self.armas_d else "pistola"
                e.hostil, e.estado, e.tag = True, "ataca", "grupo"
                e.inofensivo = bool(q.get("inofensivo"))
                e.eco_k = k
                e.t_disparo = 2.5
                self.personas.append(e)
                self.sv["ecos"][k] = e
                nuevos += 1
            if nuevos:
                self.decir(f"Los enemigos de la misión de {nombre} son también tuyos: hay {nuevos}. Pulsa Q para fijar al más cercano.")
        elif que == "golpe":
            k = d.get("k")
            e = self.sv["ecos"].get(k)
            if e is None and self.mision:
                e = next((x for x in self.mision.get("enemigos", []) if getattr(x, "eco_k", None) == k), None)
            if e is not None and not e.muerto:
                self._sv_aplicando = True                # este golpe viene de otro: no se vuelve a contar
                try:
                    self.danar_persona(e, float(d.get("dano", 0)))
                finally:
                    self._sv_aplicando = False
        elif que == "fin":
            self._sv_quitar_ecos()
            if self.gps and self.gps.get("grupo"):
                self.cancelar_gps()
            if not d.get("hecha"):
                self.decir(f"La misión de {nombre} se ha quedado sin terminar.")

    def _sv_grupo_paso(self, dt):
        """Los enemigos del grupo que ya han caído se retiran de tu lista."""
        for k, e in list(self.sv["ecos"].items()):
            if e.muerto and self.t - e.t_estado > 20:
                if e in self.personas:
                    self.personas.remove(e)
                del self.sv["ecos"][k]
