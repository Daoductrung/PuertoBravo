"""Servidor en línea de Puerto Bravo.

Un solo hilo con asyncio. Cada jugador tiene su cola de salida: uno con mala conexión no frena a los demás.
Mensajes: una línea de JSON cada uno, igual que en Jugar con amigos, de modo que el juego habla el mismo idioma.

Lo que decide el servidor, y no el juego de cada cual:
- quién es quién (una clave pública por cuenta, y la firma de un reto al entrar);
- los disparos y golpes entre jugadores: alcance, cadencia, zonas seguras, modo pasivo, bandas y alianzas;
- de quién es cada vehículo dejado en la calle y quién lo conduce;
- las bandas, su caja, los territorios y las guerras;
- la hora, el día y el tiempo que hace, iguales para todos;
- el personaje de cada jugador, que se guarda aquí y se retoma al volver.

Funciona con Python 3.8 o posterior y solo usa la biblioteca de serie.
"""
import asyncio
import binascii
import hashlib
import json
import math
import os
import random
import secrets
import time

from . import copias, firma, opciones
from .almacen import Almacen
from .bots import Bots
from .trafico import Trafico
from .peatones import Peatones
from .policia import Policia

VERSION_RED = 2                   # la versión del protocolo que habla este servidor
PROTOCOLO_MIN = 2                 # la más antigua con la que todavía se entiende
# Lo que sabe hacer este servidor. El juego lo mira para no pedir lo que el servidor no tiene, sea cual sea su versión.
FUNCIONES = ("vehiculos", "combate", "bandas", "barrios", "grupos", "propiedades", "robos", "personajes", "mundo", "versiones")
# Claves públicas de quien publica el juego: con ellas se comprueba que el mundo que trae un jugador es el de una
# versión de verdad. Son las mismas con las que el juego comprueba sus actualizaciones.
CLAVES_PUBLICAS = ("2793c73fefcdb5518570569e41e9ae291373c41126b30d4b3fb99359b09ca23f",)
MUNDO_VACIO = {"version": "0", "huella": "", "mapas": {}, "armas": {}, "modelos": {}, "misiones": {}}


def version_tupla(t):
    out = []
    for trozo in str(t or "0").split("."):
        num = "".join(c for c in trozo if c.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out)



MAX_LINEA = 600 * 1024            # un personaje guardado cabe de sobra
# Mensajes que el juego manda solo, sin que el jugador haga nada: no cuentan como actividad.
PASIVOS = ("estado", "ping", "guardar", "quien", "banda_lista")
ESTADOS = {"t": "estados"}       # lo que se reparte diez veces por segundo va ya escrito: esto es solo su etiqueta
MAX_NORMAL = 16 * 1024            # cualquier otro mensaje
SEGURAS = ("hospital", "comisaria", "casa", "ong", "protectora")     # lugares donde nadie puede herir a nadie
RADIO_SEGURO = 16.0
RANGOS = ("jefe", "mano", "miembro")
RANGO_TXT = {"jefe": "jefe", "mano": "mano derecha", "miembro": "miembro"}

# Las opciones, con su valor de serie, su explicación y sus límites, están descritas una sola vez en opciones.py.
CONFIG = opciones.valores_de_serie()


def leer_config(ruta, avisos=None):
    """Archivo de texto, una opción por línea: nombre = valor. Las líneas que empiezan por almohadilla son comentarios.
    Lo que no vale se cambia por su valor de serie; si se pasa una lista en ``avisos``, ahí queda dicho qué y por qué."""
    c, problemas = opciones.leer(ruta)
    if avisos is not None:
        avisos.extend(problemas)
    return c


def si(v):
    return str(v).strip().lower() in ("si", "sí", "1", "true", "yes")


def finito(v):
    """Un número de verdad. Un juego trucado puede mandar un infinito o un «no es un número»: con eso dentro, las cuentas
    de distancias dejan de valer para todos, así que no se admite."""
    v = float(v)
    if not math.isfinite(v):
        raise ValueError("no es un número que valga")
    return v


def _constante_no_valida(nombre):
    raise ValueError("un mensaje no puede traer " + nombre)


def limpiar_nombre(t, tope=24):
    t = "".join(ch for ch in str(t or "") if ch.isprintable() and ch not in "\\/<>|\"").strip()
    return " ".join(t.split())[:tope]


class Jugador:
    def __init__(self, ident, escritor):
        self.id = ident
        self.escritor = escritor
        self.cola = asyncio.Queue()
        self.cuenta = None
        self.nombre = ""
        self.admin = False
        self.conectado = True
        self.dentro = False
        self.mapa = None
        self.x = self.y = 0.0
        self.rumbo = 0.0
        self.vel = 0.0
        self.veh = None            # modelo que conduce
        self.vid = None            # identificador del vehículo común que conduce
        self.salud = 100.0
        self.dinero = 0
        self.arma = "punos"
        self.barrio = None
        self.agachado = False
        self.interior = False
        self.estrellas = 0
        self.po = []
        self.puntos = 0.0          # puntos de delito: de ellos sale el nivel de búsqueda
        self.t_evasion = 0.0       # segundos sin ningún policía cerca
        self.t_poli = 0.0          # lo que falta para que salga otra patrulla
        self.poli_enviada = False
        self.detenido = 0.0        # le han echado el guante: hasta este momento le tienen cogido
        self.estado = {}
        self.t_ataque = 0.0
        self.golpeado = {}         # quién me ha dado: {id de sesión: momento}
        self.agredio = {}          # a quién he dado yo primero
        self.pasivo = False
        self.t_pasivo = 0.0
        self.protegido = 0.0
        self.banda = None
        self.rango = None
        self.grupo = None          # id del líder del grupo de misión
        self.fichas = 120.0        # para frenar a quien manda demasiado
        self.t_fichas = time.monotonic()
        self.t_ultimo = time.monotonic()
        self.fantasma = 0.0        # se ha ido en pleno combate: sigue ahí hasta este momento
        self.t_vid = 0.0           # cuándo cogió el vehículo que conduce
        self.atracos = {}          # a quién ha atracado y cuándo
        self.bot = False           # lo lleva el servidor, no una persona
        self.saldo = None          # lo que el servidor le reconoce: bolsillo más banco
        self.credito = 0           # dinero que le ha dado el propio servidor y aún no ha aparecido en su juego
        self.margen = 0.0          # lo que aún puede ganar por su cuenta sin que se le discuta
        self.t_margen = time.monotonic()
        self.t_saldo = 0.0
        self.banco = 0
        self.cobros = []           # lo que el servidor le ha cobrado y su juego puede no haber restado todavía, por orden
        self.t_cobros = 0.0        # cuándo fue el último de esos cobros
        self.gastos = []           # lo que se le ha visto gastar hace poco: [momento, euros]
        self.prop_pend = {}        # casas y negocios que acaba de apuntarse y aún no se le ha visto pagar: lugar -> [momento, precio]
        self.aspecto = ""          # lo que lleva puesto, como lo cuenta su juego
        self.misiones_pagadas = set()
        self.mapa_fuera = None     # la localidad en la que dice estar, si el mundo del servidor no la tiene
        self.ip = None             # de dónde viene la conexión: solo en memoria, para el límite por dirección
        self.juego = ""            # versión del juego con la que ha entrado
        self.huella = ""           # huella del mundo que trae su juego
        self.proto = VERSION_RED   # versión del protocolo acordada con su juego
        self.t_actividad = time.monotonic()      # la última vez que se movió o hizo algo
        self.avisado = set()       # avisos de compatibilidad que ya se le han dado: no se repiten
        self.raros = set()         # tipos de mensaje suyos que no se han podido atender: se apuntan una vez

    def dist(self, otro):
        return math.hypot(self.x - otro.x, self.y - otro.y)

    def publico(self):
        return {"id": self.id, "nombre": self.nombre, "banda": self.banda, "ia": self.bot}


class Servidor(Bots, Trafico, Peatones, Policia):
    def __init__(self, config=None, mundo=None, reloj_real=time.time):
        self.cfg = dict(CONFIG)
        self.cfg.update(config or {})
        self.ahora = reloj_real
        carpeta = self.cfg["datos"]
        os.makedirs(carpeta, exist_ok=True)
        self.alm = Almacen(os.path.join(carpeta, "puertobravo.db"))
        self.claves_publicas = CLAVES_PUBLICAS
        self.ruta_conf = None                                 # de qué archivo salió la configuración, si salió de alguno
        self.t_inicio = None                                  # cuándo empezó a escuchar
        self.por_ip = {}                                      # conexiones abiertas por dirección: solo en memoria
        self._t_guardado = self._t_copia = time.monotonic()
        # Los mundos que este servidor ha tenido o ha comprobado: {huella: versión}. Quien trae uno de estos puede
        # entrar aunque el servidor vaya ya con el de una versión más nueva.
        try:
            self.mundos_conocidos = {str(k): str(v) for k, v in dict(self.alm.meta("mundos", {})).items()}
        except (TypeError, ValueError):
            self.mundos_conocidos = {}
        if mundo is None:                                     # el último que trajo un jugador; si no, el que venga con el servidor; si no, ninguno
            for ruta in (os.path.join(carpeta, "mundo_actual.json"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "mundo.json")):
                try:
                    with open(ruta, encoding="utf-8") as f:
                        mundo = json.load(f)
                    break
                except (OSError, ValueError):
                    continue
        self._poner_mundo(mundo or dict(MUNDO_VACIO), guardar=False)
        self.robos = {}                                       # atracos a negocios en marcha: id de sesión -> datos
        self.jugadores = {}
        self._n = 0
        self.vehiculos = {v["id"]: v for v in self.alm.vehiculos()}
        self._nv = max(list(self.vehiculos) + [0])
        for v in self.vehiculos.values():
            v["por"] = None
        self.reloj = float(self.alm.meta("reloj", 540.0))
        self.dia = int(self.alm.meta("dia", 1))
        self.lluvia = bool(self.alm.meta("lluvia", False))
        self.semilla = int(self.alm.meta("semilla", 0)) or random.randrange(1, 10 ** 9)
        self.alm.poner_meta("semilla", self.semilla)
        self.guerras = self.alm.meta("guerras", [])          # [{mapa, barrio, ataca, defiende, inicio, fin, pa, pd}]
        self.ayudas = set(tuple(x) for x in self.alm.meta("ayudas", []))
        self.invitaciones_banda = {}                          # id de sesión -> {banda, de, hasta}
        self.invitaciones_grupo = {}
        self.propuestas_alianza = {}                          # banda destino -> banda que propone
        self.cifrado = False
        self.huella_cert = ""
        self.servidor = None
        self.activo = False
        self.detenido = False                                 # pasa a True cuando ha parado del todo y lo ha guardado todo
        self.tareas = []
        self.conexiones = set()
        self.log = print
        self.rng = random.Random()
        self.bots_iniciar()
        self.trafico_iniciar()
        self.peatones_iniciar()
        self.policia_iniciar()
        self.alm.guardar()

    # El registro: lo que va diciendo el servidor. Quien lo arranca dice adónde va (la consola, el panel, una lista en las
    # pruebas) con ``srv.log = función``; si la opción registro_archivo está puesta, va además a registro.txt.
    @property
    def log(self):
        return self._anotar

    @log.setter
    def log(self, salida):
        self._destino_registro = salida

    def _anotar(self, texto):
        if si(self.cfg.get("registro_archivo", "no")):
            try:
                ruta = os.path.join(self.cfg["datos"], "registro.txt")
                if os.path.exists(ruta) and os.path.getsize(ruta) > 2 * 1024 * 1024:      # no crece sin fin: se guarda el anterior
                    os.replace(ruta, os.path.join(self.cfg["datos"], "registro_anterior.txt"))
                with open(ruta, "a", encoding="utf-8", newline="\n") as f:
                    f.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), texto))
            except OSError:
                pass
        self._destino_registro(texto)

    def _poner_mundo(self, mundo, guardar=True):
        """El mundo del juego con el que trabaja el servidor. Lo trae el juego, no el servidor: así un mismo servidor
        sirve para las versiones que vayan saliendo."""
        self.mundo = mundo
        self.seguras = {}
        self.lugares = {}                                     # los que se pueden comprar: casas y negocios
        for mid, m in mundo["mapas"].items():
            self.seguras[mid] = [(l["x"], l["y"]) for l in m["lugares"] if l["tipo"] in SEGURAS]
            for l in m["lugares"]:
                if l["tipo"] in ("casa", "negocio") and l.get("precio", 0) > 0:
                    self.lugares[l["id"]] = dict(l, mapa=mid)
        if mundo.get("huella") and mundo["mapas"]:
            self._recordar_mundo(mundo["huella"], mundo.get("version"))
        # Si el mundo cambia con gente dentro, nada de lo que estaba en marcha puede apuntar a algo que ya no existe.
        for j in getattr(self, "jugadores", {}).values():
            if j.mapa is not None and j.mapa not in mundo["mapas"]:
                j.mapa = None
        for ident in [i for i, r in getattr(self, "robos", {}).items() if r["lugar"] not in self.lugares]:
            self.robos.pop(ident, None)
        if hasattr(self, "guerras"):
            self.guerras = [g for g in self.guerras if g["mapa"] in mundo["mapas"]]
        for nombre in ("trafico", "peatones", "agentes"):      # lo que lleva el servidor por las calles se vuelve a poner solo
            cosas = getattr(self, nombre, None)
            if isinstance(cosas, dict):
                for ident in [i for i, c in cosas.items() if c.get("m") not in mundo["mapas"]]:
                    del cosas[ident]
        self._abiertos = {}                                   # las manzanas por las que andan los agentes se calculan otra vez
        if guardar:
            ruta = os.path.join(self.cfg["datos"], "mundo_actual.json")
            with open(ruta + ".tmp", "w", encoding="utf-8", newline="\n") as f:
                json.dump(mundo, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(ruta + ".tmp", ruta)

    def _recordar_mundo(self, huella, version):
        """Apunta un mundo como conocido: el que tiene el servidor, o uno firmado por quien publica el juego."""
        huella = str(huella or "")
        if not huella or self.mundos_conocidos.get(huella) == str(version or ""):
            return
        self.mundos_conocidos[huella] = str(version or "")
        while len(self.mundos_conocidos) > 200:               # con el tiempo, los más antiguos dejan sitio
            self.mundos_conocidos.pop(next(iter(self.mundos_conocidos)))
        self.alm.poner_meta("mundos", self.mundos_conocidos)

    async def _recibir_mundo(self, j, lector, m):
        """Pide al juego de quien entra el mundo de su versión. Devuelve (texto, firmado), o (None, False) si no llega bien.
        Firmado quiere decir que lo avala quien publica el juego: es el de una versión de verdad, sin mods."""
        self._enviar(j, {"t": "pide_mundo"})
        r = await self._leer(lector, MAX_LINEA, 40)
        if not r or r.get("t") != "mundo":
            return None, False
        try:                                                  # viene comprimido: pesa la sexta parte
            import base64
            import zlib
            texto = zlib.decompressobj().decompress(base64.b64decode(r["z"]), 4 * 1024 * 1024).decode("utf-8") if r.get("z") else r.get("datos")
        except Exception:
            return None, False
        if not isinstance(texto, str) or not texto:
            return None, False
        firmado = False
        try:
            f = binascii.unhexlify(str(r.get("firma") or ""))
            for clave in self.claves_publicas:
                if f and await asyncio.get_event_loop().run_in_executor(None, firma.verificar, binascii.unhexlify(clave), texto.encode("utf-8"), f):
                    firmado = True
                    break
        except Exception:
            firmado = False
        return texto, firmado

    @staticmethod
    def _mundo_de_texto(texto, huella):
        """El mundo que viene en un texto, si está bien formado y su huella es la que dice el juego. Si no, None."""
        try:
            nuevo = json.loads(texto)
            assert isinstance(nuevo["mapas"], dict) and isinstance(nuevo["armas"], dict) and isinstance(nuevo["modelos"], dict) and isinstance(nuevo["misiones"], dict)
            assert nuevo["huella"] == huella and nuevo["mapas"]
            for mapa in nuevo["mapas"].values():
                assert isinstance(mapa["lugares"], list) and isinstance(mapa["barrios"], list)
            return nuevo
        except Exception:
            return None

    async def _admitir_mundo(self, j, lector, m, es_admin):
        """El juego de quien entra trae un mundo que no es el del servidor. Devuelve (True, "") si puede entrar, o
        (False, motivo). Por el camino, si procede, el servidor adopta ese mundo o lo apunta como conocido.

        El servidor trabaja con el mundo de la versión más nueva que ha visto, pero no echa a quien va con otra: basta
        con que su mundo sea uno que el servidor ya tuvo, o uno firmado por quien publica el juego. Cada cual juega con
        lo que su versión conoce."""
        huella, juego = str(m.get("huella") or ""), m.get("juego")
        modo = str(self.cfg["actualizar_mundo"]).lower()
        estricto = str(self.cfg["versiones"]).lower() == "iguales"
        vacio = not self.mundo["mapas"]
        mas_nuevo = version_tupla(juego) > version_tupla(self.mundo.get("version")) or vacio
        por_admin = modo == "admin" and es_admin
        puede_adoptar = modo != "no" and ((mas_nuevo and bool(m.get("firmado"))) or por_admin)
        conocido = huella in self.mundos_conocidos and not vacio
        texto, firmado = None, False
        if puede_adoptar or (not conocido and not estricto and not vacio and m.get("firmado")):
            texto, firmado = await self._recibir_mundo(j, lector, m)
        nuevo = self._mundo_de_texto(texto, huella) if texto else None
        if nuevo is not None and puede_adoptar and ((firmado and mas_nuevo) or por_admin):
            antes = self.mundo.get("version")
            self._poner_mundo(nuevo)
            self.log("El mundo pasa de la versión %s a la %s%s." % (antes, nuevo.get("version"), ", firmado por quien publica el juego" if firmado else ", traído por un administrador, sin firma"))
            self._a_todos({"t": "aviso", "texto": ("El servidor pasa a los datos de la versión %s del juego. " % nuevo.get("version"))
                           + ("Quien tenga otra versión tendrá que ponerse esta para volver a entrar." if estricto else
                              "Quien tenga una versión anterior puede seguir jugando, pero lo nuevo solo lo verá quien actualice."),
                           "son": "notificacion"})
            return True, ""
        if not vacio and not estricto:
            if nuevo is not None and firmado:                 # es de una versión de verdad: desde ahora, conocido
                self._recordar_mundo(huella, nuevo.get("version"))
                self.alm.guardar()
                conocido = True
            if conocido:
                return True, ""
        if version_tupla(juego) < version_tupla(self.mundo.get("version")) and (estricto or vacio or not m.get("firmado")):
            return False, "Este servidor va con la versión %s del juego y la tuya es anterior. Actualiza el juego para entrar." % self.mundo.get("version", "?")
        return False, ("Los datos de tu juego no son los de este servidor, que va con la versión %s: llevas mods que cambian el mundo, "
                       "o una versión que el servidor no puede comprobar." % self.mundo.get("version", "?"))
    # ================================================================ arranque
    def _contexto_tls(self):
        modo = str(self.cfg["cifrado"]).lower()
        if modo == "no":
            return None
        import ssl
        cert, llave = self.cfg["certificado"], self.cfg["llave"]
        if not cert:
            cert = os.path.join(self.cfg["datos"], "certificado.pem")
            llave = os.path.join(self.cfg["datos"], "llave.pem")
            if not (os.path.exists(cert) and os.path.exists(llave)):
                self._crear_certificado(cert, llave)
        if not (os.path.exists(cert) and os.path.exists(llave or cert)):
            if si(modo):
                raise RuntimeError("El cifrado es obligatorio pero no hay certificado y no se ha podido crear: hace falta el programa openssl.")
            return None
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, llave or None)
        try:
            pem = open(cert, encoding="ascii").read()
            der = ssl.PEM_cert_to_DER_cert(pem[pem.index("-----BEGIN CERTIFICATE-----"):pem.index("-----END CERTIFICATE-----") + 25])
            self.huella_cert = hashlib.sha256(der).hexdigest()
        except Exception:
            self.huella_cert = ""
        return ctx

    def _crear_certificado(self, cert, llave):
        """Un certificado propio, válido diez años. Con el programa openssl si está; si no, lo hace el propio servidor."""
        import shutil
        import subprocess
        exe = shutil.which("openssl")
        if not exe:
            return self._certificado_propio(cert, llave)
        try:
            subprocess.run([exe, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", llave, "-out", cert, "-days", "3650",
                            "-subj", "/CN=PuertoBravo"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            try:
                os.chmod(llave, 0o600)
            except OSError:
                pass
            return True
        except Exception:
            return self._certificado_propio(cert, llave)

    def _certificado_propio(self, cert, llave):
        try:
            from . import certificado
            self.log("Creando el certificado para cifrar la conexión. Tarda unos segundos y solo se hace la primera vez.")
            certificado.escribir(cert, llave)
            try:
                os.chmod(llave, 0o600)
            except OSError:
                pass
            return True
        except Exception as e:
            self.log("No se ha podido crear el certificado: %s: %s" % (type(e).__name__, e))
            return False

    async def iniciar(self):
        ctx = self._contexto_tls()
        self.cifrado = ctx is not None
        self.servidor = await asyncio.start_server(self._atender, self.cfg["interfaz"], int(self.cfg["puerto"]), ssl=ctx, limit=MAX_LINEA)
        self.puerto = self.servidor.sockets[0].getsockname()[1]
        self.activo = True
        self.t_inicio = time.time()
        self._t_guardado = self._t_copia = time.monotonic()
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self._error_del_bucle)
        self.tareas = [loop.create_task(self._bucle_estados()), loop.create_task(self._bucle_lento())]
        self.log("Servidor «%s» escuchando en el puerto %s, %s." % (self.cfg["nombre"], self.puerto, "con cifrado" if self.cifrado else "SIN cifrado"))

    def _error_del_bucle(self, loop, contexto):
        """Lo que falla por dentro sin que nadie lo recoja. Va al registro en una línea, no a la consola como un volcado.

        Hay un caso que no es un error de nadie y no se dice: en Windows, cuando un jugador corta la conexión justo cuando
        el servidor la está cerrando, Python se queja al cerrar un enchufe de red que ya está cerrado. Ahí solo se termina
        de cerrar lo que quedaba abierto."""
        exc = contexto.get("exception")
        asa = contexto.get("handle")
        if isinstance(exc, OSError) and "connection_lost" in str(asa or contexto.get("message") or ""):
            try:
                enchufe = getattr(getattr(getattr(asa, "_callback", None), "__self__", None), "_sock", None)
                if enchufe is not None:
                    enchufe.close()
            except Exception:
                pass
            return
        try:
            self.log("Error interno del servidor: %s%s" % (contexto.get("message") or "sin más datos", (": %s: %s" % (type(exc).__name__, exc)) if exc is not None else ""))
        except Exception:
            pass

    async def detener(self, motivo="El servidor se ha cerrado."):
        if not self.activo:
            return
        self.activo = False
        for j in list(self.jugadores.values()):
            self._enviar(j, {"t": "cerrado", "motivo": motivo})
        await asyncio.sleep(0.2)
        for t in self.tareas:
            t.cancel()
        self.servidor.close()
        for j in list(self.jugadores.values()):
            if j.dentro and j.vid is not None and j.vid in self.vehiculos:      # lo que conducían se queda aparcado
                self.vehiculos[j.vid].update(por=None, m=j.mapa, x=j.x, y=j.y, r=j.rumbo, t=self.ahora())
            if j.dentro and j.cuenta is not None:
                self.alm.poner(j.cuenta, visto=self.ahora(), dia_salida=self.dia)
            j.dentro = False
            self._cortar(j)
        self.guardar_todo()
        for t in list(self.conexiones):
            t.cancel()
        if self.conexiones:
            await asyncio.wait(list(self.conexiones), timeout=3)
        try:
            await asyncio.wait_for(self.servidor.wait_closed(), 3)
        except Exception:
            pass
        self.alm.cerrar()
        self.detenido = True                                  # ya está todo guardado y cerrado

    def guardar_todo(self):
        self.alm.poner_meta("reloj", self.reloj)
        self.alm.poner_meta("dia", self.dia)
        self.alm.poner_meta("lluvia", self.lluvia)
        self.alm.poner_meta("guerras", self.guerras)
        self.alm.poner_meta("ayudas", [list(x) for x in list(self.ayudas)[-4000:]])
        self.alm.guardar_vehiculos([dict(v, por=None) for v in self.vehiculos.values()])
        self.alm.guardar()

    # ================================================================== envío
    def _enviar(self, j, obj, hecho=None):
        """Pone un mensaje en la cola de un jugador. ``hecho`` es el mismo mensaje ya escrito, cuando va a muchos."""
        t = obj.get("t")
        if t in ("dinero", "paga_mision") and not j.bot:      # lo que da el servidor queda apuntado: es dinero justificado
            j.credito += max(0, int(obj.get("n", 0)))
        elif t in ("baja", "atraco_ok", "robo_fin") and not j.bot:
            j.credito += max(0, int(obj.get("botin", 0)))
        if j.conectado:
            j.cola.put_nowait(obj if hecho is None else hecho)
            if j.cola.qsize() > 600:                         # no lee: fuera, sin frenar a nadie
                self._cortar(j)

    @staticmethod
    def _codificar(obj):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"

    def _a_todos(self, obj, menos=None, mapa=None):
        """A todos los que están dentro, o a los de una localidad. El mensaje se escribe una sola vez, no una por jugador:
        con cien jugadores es cien veces menos trabajo."""
        hecho = None
        for j in self.jugadores.values():
            if j.dentro and j is not menos and (mapa is None or j.mapa == mapa):
                if hecho is None and not j.bot:
                    hecho = self._codificar(obj)
                self._enviar(j, obj, hecho)

    def _a_banda(self, banda, obj, menos=None):
        hecho = None
        for j in self.jugadores.values():
            if j.dentro and j.banda == banda and j is not menos:
                if hecho is None and not j.bot:
                    hecho = self._codificar(obj)
                self._enviar(j, obj, hecho)

    def _aviso(self, j, texto, sonido=None):
        self._enviar(j, {"t": "aviso", "texto": texto, "son": sonido})

    def _cortar(self, j):
        j.conectado = False
        try:
            j.escritor.close()
        except Exception:
            pass

    def _echar(self, j, motivo):
        """Le dice por qué se va y corta un momento después, para que le llegue el mensaje."""
        self._enviar(j, {"t": "expulsado", "motivo": motivo})
        j.cola.put_nowait(None)                  # quien escribe termina lo pendiente, espera un momento y corta

    async def _escribir(self, j):
        try:
            while j.conectado:
                obj = await j.cola.get()
                if obj is None:
                    break
                j.escritor.write(obj if isinstance(obj, bytes) else self._codificar(obj))
                await asyncio.wait_for(j.escritor.drain(), 20)
            # Despedida sin prisas: si se cierra nada más enviar, en Windows al otro lado le llega un corte en vez del
            # último mensaje (un rechazo, por ejemplo). Se avisa de que no hay más y se le da medio segundo para leer.
            try:
                if j.escritor.can_write_eof():
                    j.escritor.write_eof()
            except Exception:
                pass
            await asyncio.sleep(0.5)
        except Exception:
            pass
        self._cortar(j)

    # ============================================================== conexión
    async def _leer(self, lector, tope=MAX_NORMAL, espera=60):
        linea = await asyncio.wait_for(lector.readline(), espera)
        if not linea:
            return None
        if len(linea) > tope:
            raise ValueError("mensaje demasiado largo")
        try:
            m = json.loads(linea.decode("utf-8"), parse_constant=_constante_no_valida)      # ni NaN ni Infinity: no son JSON
        except ValueError:
            return {}
        return m if isinstance(m, dict) else {}

    async def _atender(self, lector, escritor):
        self._n += 1
        j = Jugador(self._n, escritor)
        tarea = asyncio.get_event_loop().create_task(self._escribir(j))
        yo = asyncio.current_task() if hasattr(asyncio, "current_task") else None
        if yo is not None:
            self.conexiones.add(yo)
        try:
            par = escritor.get_extra_info("peername")
            j.ip = str(par[0]) if isinstance(par, (tuple, list)) and par else None      # solo en memoria: no se guarda en ningún sitio
        except Exception:
            j.ip = None
        if j.ip is not None:
            self.por_ip[j.ip] = self.por_ip.get(j.ip, 0) + 1
        try:
            if si(self.cfg["registro_ip"]):
                self.log("Conexión desde %s" % (par,))
            tope_ip = int(self.cfg["conexiones_por_ip"])
            if tope_ip > 0 and j.ip is not None and self.por_ip.get(j.ip, 0) > tope_ip:
                self._rechazo(j, "Hay demasiadas conexiones desde tu dirección. Prueba dentro de un momento.")
            elif await self._entrada(j, lector):
                while j.conectado and self.activo:
                    m = await self._leer(lector, MAX_LINEA, 90)
                    if m is None:
                        break
                    if not m:
                        continue
                    if not self._ficha(j):
                        self._echar(j, "Tu juego manda demasiados mensajes.")
                        break
                    j.t_ultimo = time.monotonic()
                    if m.get("t") == "adios":
                        break
                    if m.get("t") not in PASIVOS:
                        j.t_actividad = j.t_ultimo           # ha hecho algo: no está parado
                    try:
                        self._mensaje(j, m)
                    except Exception as e:                    # un mensaje raro no tumba el servidor, ni echa a quien lo manda
                        # Puede venir de un juego de otra versión, con otra forma. Se deja pasar y se apunta una sola vez por
                        # jugador y tipo de mensaje: así nadie llena el registro a base de mandar cosas raras.
                        clave = str(m.get("t"))[:30]
                        if clave not in j.raros and len(j.raros) < 20:
                            j.raros.add(clave)
                            self.log("Un mensaje «%s» de %s no se ha podido atender y se deja pasar: %s: %s" % (clave, j.nombre, type(e).__name__, e))
        except (asyncio.TimeoutError, ConnectionError, OSError, ValueError, asyncio.IncompleteReadError):
            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:                                # nada de lo que mande un cliente debe tumbar al servidor
            self.log("Error atendiendo a un jugador: %s: %s" % (type(e).__name__, e))
        finally:
            self.conexiones.discard(yo)
            if j.ip is not None:
                quedan = self.por_ip.get(j.ip, 1) - 1
                if quedan > 0:
                    self.por_ip[j.ip] = quedan
                else:
                    self.por_ip.pop(j.ip, None)
            if self.activo:
                self._salida(j)
            j.cola.put_nowait(None)
            try:
                await asyncio.wait_for(tarea, 3)
            except Exception:
                tarea.cancel()
            try:
                escritor.close()
            except Exception:
                pass

    def _ficha(self, j):
        ahora = time.monotonic()
        j.fichas = min(160.0, j.fichas + (ahora - j.t_fichas) * 60.0)
        j.t_fichas = ahora
        j.fichas -= 1.0
        return j.fichas > 0

    def _rechazo(self, j, motivo):
        self._enviar(j, {"t": "rechazo", "motivo": motivo})
        return False

    def _nombres(self, opcion):
        """Una lista de nombres de jugador escrita en la configuración, separados por comas."""
        return {limpiar_nombre(x).lower() for x in str(self.cfg.get(opcion, "")).split(",") if x.strip()}

    def _cuantos(self):
        """Cuántas personas hay dentro. Los personajes que lleva el servidor no cuentan."""
        return sum(1 for o in self.jugadores.values() if o.dentro and not o.bot)

    async def _entrada(self, j, lector):
        """Saludo, reto firmado y, si todo va bien, la bienvenida con el personaje guardado."""
        m = await self._leer(lector, MAX_NORMAL, 15)
        if not m or m.get("t") != "hola":
            return False
        # La versión del protocolo se acuerda: el juego dice la más nueva que habla (v) y la más antigua con la que se
        # entiende (vmin); se usa la más nueva que hablen los dos. Así entra tanto quien va por delante como quien va por detrás.
        v = m.get("v")
        if not isinstance(v, int) or isinstance(v, bool) or v < PROTOCOLO_MIN:
            return self._rechazo(j, "Tu juego es demasiado antiguo para este servidor. Actualiza el juego.")
        vmin = m.get("vmin")
        if isinstance(vmin, int) and not isinstance(vmin, bool) and vmin > VERSION_RED:
            return self._rechazo(j, "Tu juego es más nuevo de lo que este servidor entiende. Quien lleva el servidor tiene que actualizarlo.")
        j.proto = min(v, VERSION_RED)
        j.juego = "".join(ch for ch in str(m.get("juego") or "") if ch.isalnum() or ch in ".-")[:20]
        j.huella = str(m.get("huella") or "")[:64]
        pub = str(m.get("pub", "")).lower()
        if len(pub) != 64 or any(ch not in "0123456789abcdef" for ch in pub):
            return self._rechazo(j, "Tu juego no ha enviado una identidad válida.")
        reto = secrets.token_hex(24)
        self._enviar(j, {"t": "reto", "n": reto, "servidor": self.cfg["nombre"], "protocolo": j.proto, "v": VERSION_RED, "vmin": PROTOCOLO_MIN})
        f = await self._leer(lector, MAX_NORMAL, 20)
        if not f or f.get("t") != "firma":
            return False
        try:
            # Comprobar la firma cuesta unas décimas de segundo en una máquina modesta: se hace aparte, sin parar a los que juegan.
            valida = await asyncio.get_event_loop().run_in_executor(
                None, firma.verificar, binascii.unhexlify(pub), ("puertobravo-entrada|" + reto).encode("ascii"), binascii.unhexlify(str(f.get("f", ""))))
        except Exception:
            valida = False
        if not valida:
            return self._rechazo(j, "No se ha podido comprobar tu identidad.")
        fila = self.alm.cuenta_por_pub(pub)
        vetados = self._nombres("vetados")
        if (fila is not None and (fila["vetado"] or fila["nombre"].lower() in vetados)) or (fila is None and limpiar_nombre(m.get("nombre")).lower() in vetados):
            return self._rechazo(j, "No puedes entrar en este servidor.")
        minima = str(self.cfg.get("version_minima", "")).strip()
        if minima and version_tupla(j.juego) < version_tupla(minima):
            return self._rechazo(j, "Este servidor pide la versión %s del juego o una posterior, y la tuya es la %s. Actualiza el juego para entrar." % (minima, j.juego or "desconocida"))
        admins = self._nombres("admins")
        es_admin = (fila is not None and (bool(fila["admin"]) or fila["nombre"].lower() in admins)) or (fila is None and si(self.cfg["primer_admin"]) and not self.alm.hay_cuentas())
        if j.huella != self.mundo["huella"] and (si(self.cfg["comprobar_datos"]) or not self.mundo["mapas"]):
            vale, motivo = await self._admitir_mundo(j, lector, m, es_admin)
            if not vale:
                return self._rechazo(j, motivo)
        tope = int(self.cfg["max_jugadores"])                 # con 0 no hay límite; quien administra entra siempre
        if tope > 0 and not es_admin and self._cuantos() >= tope:
            return self._rechazo(j, "El servidor está lleno.")
        if fila is None:                                      # cuenta nueva: aquí se mira quién puede entrar
            modo = str(self.cfg["entrada"]).lower()
            if modo == "clave" and not secrets.compare_digest(str(m.get("clave", "")), hashlib.sha256(("puerto-bravo|" + str(self.cfg["clave"])).encode("utf-8")).hexdigest()):
                return self._rechazo(j, "La contraseña de entrada no es correcta.")
            if modo == "invitacion" and not self.alm.invitacion_libre(str(m.get("invitacion", "")).strip().upper()):
                return self._rechazo(j, "Este servidor es solo para invitados, y ese código de invitación no vale o ya se ha usado.")
            nombre = limpiar_nombre(m.get("nombre")) or "Jugador"
            if len(nombre) < 2:
                return self._rechazo(j, "Ese nombre es demasiado corto.")
            base, k = nombre, 2
            while self.alm.cuenta_por_nombre(nombre) is not None:
                nombre = "%s %d" % (base[:21], k)
                k += 1
            primera = si(self.cfg["primer_admin"]) and not self.alm.hay_cuentas()
            fila = self.alm.crear_cuenta(pub, nombre, admin=primera)
            if modo == "invitacion":
                self.alm.usar_invitacion(str(m.get("invitacion", "")).strip().upper(), fila["id"])
        for o in list(self.jugadores.values()):               # una sola sesión por cuenta: la nueva echa a la vieja
            if o.cuenta == fila["id"] and o is not j and not si(self.cfg["varias_sesiones"]):
                self._salida(o, callar=True)
                self._echar(o, "Has entrado con tu personaje desde otro sitio.")
        j.cuenta, j.nombre = fila["id"], fila["nombre"]
        j.admin = bool(fila["admin"]) or j.nombre.lower() in admins
        mi = self.alm.miembro(j.cuenta)
        if mi is not None:
            j.banda, j.rango = mi["banda"], mi["rango"]
        j.protegido = time.monotonic() + float(self.cfg["proteccion"])
        j.saldo = fila["saldo"] if "saldo" in fila.keys() else None
        try:
            j.misiones_pagadas = set(json.loads(fila["misiones"] or "[]"))
        except (ValueError, TypeError, IndexError):
            j.misiones_pagadas = set()
        j.margen = float(self.cfg["ganancia_hora"]) / 4.0       # entra con un cuarto de hora de margen
        j.t_actividad = time.monotonic()
        j.dentro = True
        self.jugadores[j.id] = j
        partida = None
        if fila["partida"]:
            try:
                partida = json.loads(fila["partida"])
            except ValueError:
                partida = None
        dias_fuera = max(0, self.dia - int(fila["dia_salida"] or self.dia)) if fila["partida"] else 0
        pendientes = self.alm.pendientes(j.cuenta)
        if j.saldo is not None:
            # Lo que cobró estando fuera (le compraron una casa, o volvió al mercado) es dinero suyo: entra en su saldo.
            # Si no, su juego se lo daría y acto seguido se lo quitaría por no cuadrar con lo que el servidor tiene apuntado.
            try:
                cobrado = sum(max(0, int(c.get("n", 0) or 0)) for c in pendientes if isinstance(c, dict) and c.get("que") in ("venta", "caducada"))
            except (TypeError, ValueError):
                cobrado = 0
            if cobrado:
                j.saldo += cobrado
                self.alm.poner(j.cuenta, saldo=int(j.saldo))
        partida_de = (fila["juego"] if "juego" in fila.keys() else "") or ""      # con qué versión se guardó el personaje la última vez
        self.alm.poner(j.cuenta, visto=self.ahora(), juego=j.juego)
        self.alm.guardar()
        self._enviar(j, {
            "t": "ok", "id": j.id, "nombre": j.nombre, "cuenta": j.cuenta, "admin": j.admin, "protegido": False,
            "protocolo": j.proto, "funciones": list(FUNCIONES),
            # Con qué mundo trabaja el servidor, y si es el mismo que trae este juego. Si no lo es, juegan juntos igual:
            # cada uno con lo que su versión conoce.
            "mundo": {"version": self.mundo.get("version"), "huella": self.mundo.get("huella"), "igual": j.huella == self.mundo.get("huella")},
            "partida_de": partida_de,
            "jugadores": [o.publico() for o in self.jugadores.values() if o.dentro and o is not j],
            "servidor": {"nombre": self.cfg["nombre"], "bienvenida": self.cfg["bienvenida"], "pvp": si(self.cfg["pvp"]), "pasivo": si(self.cfg["modo_pasivo"]),
                         "seguras": si(self.cfg["zonas_seguras"]), "adultos": si(self.cfg["adultos"]), "trafico": self._tr_activo(), "peatones": self._pe_activo(), "policia": self._po_activo(), "proteccion": int(self.cfg["proteccion"]),
                         "max_jugadores": tope,
                         "precios": {k: int(self.cfg[k]) for k in ("precio_banda", "precio_barrio", "renta_barrio", "precio_guerra", "guerra_espera", "guerra_dura")}},
            "saldo": j.saldo if si(self.cfg["economia"]) else None,
            "partida": partida, "dias_fuera": dias_fuera, "hora": self._hora(), "semilla": self.semilla,
            "banda": self._banda_datos(j.banda), "territorios": self._territorios(), "recompensa": int(fila["recompensa"] or 0),
            "pendientes": pendientes,
            "props": self._props(), "robos": self.alm.cobrar_robos(j.cuenta),
            "vehiculos": [self._veh_publico(v) for v in self.vehiculos.values()]})
        dia = str(self.cfg.get("mensaje_dia", "")).strip()
        if dia:
            self._aviso(j, "Mensaje del día: " + dia[:300], "notificacion")
        self._a_todos({"t": "entra", "id": j.id, "nombre": j.nombre, "banda": j.banda}, menos=j)
        self.po_entra(j)
        self.log("Entra %s%s. Hay %d." % (j.nombre, (", con el juego %s" % j.juego) if j.juego else "", self._cuantos()))
        return True

    def _aviso_compat(self, j, clave, texto):
        """Un aviso de compatibilidad, una sola vez por sesión: algo de su versión del juego que aquí no existe."""
        if clave not in j.avisado and not j.bot:
            j.avisado.add(clave)
            self._aviso(j, texto, "notificacion")
    def _salida(self, j, callar=False):
        if not j.dentro:
            return
        j.dentro = False
        ahora = time.monotonic()
        en_combate = any(ahora - t < 15 for t in j.golpeado.values()) or any(ahora - t < 15 for t in j.agredio.values())
        if j.vid is not None and j.vid in self.vehiculos:      # lo que conducía se queda aparcado donde estaba
            v = self.vehiculos[j.vid]
            v.update(por=None, m=j.mapa, x=j.x, y=j.y, r=j.rumbo, t=self.ahora())
            self._a_todos({"t": "veh_libre", "v": self._veh_publico(v)}, menos=j)
            j.vid = None
        self._grupo_salir(j, callar=True)
        self.invitaciones_grupo.pop(j.id, None)                # ni la que le hicieron, ni las que hizo
        for ident in [i for i, lider in self.invitaciones_grupo.items() if lider == j.id]:
            self.invitaciones_grupo.pop(ident, None)
        self.po_sale(j)
        self._guardar_saldo(j)
        if j.cuenta is not None:
            self.alm.poner(j.cuenta, visto=self.ahora(), dia_salida=self.dia)
            self.alm.guardar()
        if en_combate and not callar and self.activo:
            j.fantasma = ahora + 15                            # salir no sirve de escapatoria: sigue ahí quince segundos
            j.conectado = False
            return
        self.jugadores.pop(j.id, None)
        if not callar:
            self._a_todos({"t": "sale", "id": j.id})
            self.log("Sale %s." % j.nombre)

    # ================================================================ mensajes
    def _mensaje(self, j, m):
        t = m.get("t")
        f = getattr(self, "_m_" + str(t), None) if isinstance(t, str) and t.replace("_", "").isalnum() else None
        if f is not None:
            f(j, m)

    def _m_ping(self, j, m):
        self._enviar(j, {"t": "pong"})

    def _m_estado(self, j, m):
        e = m.get("e")
        if not isinstance(e, dict):
            return
        try:
            mapa = e.get("m")
            if mapa not in self.mundo["mapas"]:
                # Una localidad que el mundo de este servidor no tiene: es de otra versión del juego, o de un mod. No se le
                # echa: sigue jugando allí por su cuenta, y a los demás les consta que anda por otra parte.
                if isinstance(mapa, str) and mapa and self.mundo["mapas"]:
                    j.mapa, j.mapa_fuera = None, mapa[:40]
                    j.t_actividad = time.monotonic()
                    self._aviso_compat(j, "mapa:" + mapa[:40], "Esta localidad no existe en la versión del juego con la que va este servidor, la %s. "
                                       "Puedes estar en ella, pero aquí no verás a los demás jugadores ni ellos a ti." % self.mundo.get("version", "?"))
                return
            cambio = mapa != j.mapa
            j.mapa, j.mapa_fuera = mapa, None
            x, y = finito(e.get("x") or 0), finito(e.get("y") or 0)
            rumbo, vel = finito(e.get("r") or 0), max(0.0, min(500.0, finito(e.get("s") or 0)))
            if cambio or abs(x - j.x) > 1.0 or abs(y - j.y) > 1.0:
                j.t_actividad = time.monotonic()               # se ha movido: no está parado
            j.x, j.y = x, y
            j.rumbo, j.vel = rumbo, vel
            j.veh = e.get("v") if e.get("v") in self.mundo["modelos"] else ("utilitario" if e.get("v") else None)
            j.salud = max(0.0, min(999.0, finito(e.get("sa", j.salud))))
            j.dinero = max(0, int(e.get("di", j.dinero)))
            j.banco = max(0, int(e.get("ba", j.banco)))
            self._cuadrar_saldo(j)
            j.arma = e.get("ar") if e.get("ar") in self.mundo["armas"] else "punos"
            if j.arma == "punos" and isinstance(e.get("ar"), str) and e.get("ar") not in ("", "punos") and self.mundo["armas"]:
                self._aviso_compat(j, "arma:" + e["ar"][:40], "El arma que llevas no existe en la versión del juego con la que va este servidor: "
                                   "contra otros jugadores cuenta como ir con las manos.")
            j.barrio = e.get("b") if isinstance(e.get("b"), str) else None
            j.agachado, j.interior = bool(e.get("ag")), bool(e.get("in"))
            if not self._po_activo():                         # sin policía del servidor, la búsqueda la lleva su juego
                j.estrellas = max(0, min(5, int(e.get("es") or 0)))
                po = e.get("po")                              # y la policía que le persigue la ven también los que están cerca
                j.po = [f for f in po[:10] if isinstance(f, list) and 4 <= len(f) <= 6] if isinstance(po, list) and j.estrellas else []
            else:
                j.po = []
        except (TypeError, ValueError):
            return
        if j.vid is not None and j.vid in self.vehiculos:
            v = self.vehiculos[j.vid]
            v.update(m=j.mapa, x=j.x, y=j.y, r=j.rumbo)
            if j.veh is None and time.monotonic() - j.t_vid > 3:   # va a pie y no avisó de que lo dejaba
                self._soltar_vehiculo(j, v)
        if cambio:
            self._enviar(j, {"t": "territorios", "e": self._territorios()})

    # ================================================================= economía
    def _cuadrar_saldo(self, j):
        """El dinero de cada jugador lo lleva el servidor. Gastar, siempre. Ganar, lo que el servidor ha dado (botines,
        ventas, pagas, misiones comprobadas) y, por su cuenta, hasta un tanto por hora. Lo que pase de ahí no se reconoce."""
        if not si(self.cfg["economia"]):
            return
        total = j.dinero + j.banco
        if j.saldo is None:                                   # personaje nuevo: con lo que empieza, sin pasarse
            j.saldo = min(total, int(self.cfg["saldo_inicial"]))
        ahora = time.monotonic()
        if j.cobros:
            # Lo que cobra el servidor (fundar una banda, ingresar en la caja, comprarle una casa a otro) se descuenta aquí
            # al momento, pero al juego le llega un instante después: las posiciones que mandó mientras tanto todavía
            # traen ese dinero. No es dinero de más ni hay que quitárselo otra vez: es el mismo cobro, que está de camino.
            if ahora - j.t_cobros > 15:
                j.cobros = []                                 # quien no hace caso de un cobro no se queda con el dinero
            else:
                falta = sum(j.cobros)
                while j.cobros and total - j.saldo < falta:   # los primeros ya los ha restado su juego
                    falta -= j.cobros.pop(0)
                if falta > 0:
                    j.dinero = max(0, j.dinero - falta)
                    total -= falta
        tope = float(self.cfg["ganancia_hora"])
        j.margen = min(tope, j.margen + (ahora - j.t_margen) * tope / 3600.0)
        j.t_margen = ahora
        delta = total - j.saldo
        if delta <= 0:
            if delta < 0:                                     # ha gastado: se apunta, por si su juego se lo tiene que devolver
                j.gastos.append([ahora, -delta])
                del j.gastos[:-8]
            j.saldo = total
            if j.prop_pend:
                self._ver_pagos(j)
            return
        de_credito = min(delta, j.credito)
        j.credito -= de_credito
        de_margen = min(delta - de_credito, int(j.margen))
        j.margen -= de_margen
        j.saldo += de_credito + de_margen
        sobra = total - j.saldo
        if sobra > 0:
            j.dinero = max(0, j.dinero - sobra)               # para el servidor, ese dinero no existe
            if ahora - j.t_saldo > 4:
                j.t_saldo = ahora
                self.log("A %s no se le reconocen %d euros." % (j.nombre, sobra))
                self._enviar(j, {"t": "saldo", "quita": sobra, "saldo": j.saldo})

    def _ver_pagos(self, j):
        """Casa cada compra de casa o negocio pendiente con un gasto que se le haya visto al jugador en esos segundos. La
        que casa queda como pagada; la que en veinte segundos no ha casado se queda sin pagar: suya, pero sin valor de venta."""
        ahora = time.monotonic()
        for lugar, (cuando, precio) in list(j.prop_pend.items()):
            falta = precio
            usados = []
            for g in j.gastos:
                if g[1] > 0 and cuando - 6 <= g[0] <= cuando + 20:
                    parte = min(falta, g[1])
                    usados.append((g, parte))
                    falta -= parte
                    if falta <= 0:
                        break
            if falta <= 0:
                for g, parte in usados:
                    g[1] -= parte                              # ese gasto ya ha servido para esto: no vale también para otra cosa
                self.alm.marcar_pagada(lugar, j.cuenta)
                del j.prop_pend[lugar]
            elif ahora - cuando > 20:
                del j.prop_pend[lugar]

    def _devolucion(self, j, n):
        """El juego de un jugador le devuelve lo que pagó por algo que al final no es suyo (una casa que otro compró un
        instante antes). Se da por bueno solo lo que el servidor le ha visto gastar hace un momento: quien no pagó nada
        no recibe nada por pedir casas ajenas."""
        if not si(self.cfg["economia"]) or j.bot:
            return
        ahora = time.monotonic()
        for g in reversed(j.gastos):
            if n <= 0:
                break
            if ahora - g[0] <= 20 and g[1] > 0:
                parte = min(n, g[1])
                g[1] -= parte
                n -= parte
                j.credito += parte

    def _m_mision_ok(self, j, m):
        """Ha completado una misión de su historia: su recompensa queda justificada, una vez."""
        mi = self.mundo["misiones"].get(m.get("id"))
        if mi is None or mi["dinero"] <= 0:
            return
        if not mi["repetible"]:
            if m["id"] in j.misiones_pagadas:
                return
            j.misiones_pagadas.add(m["id"])
            self.alm.poner(j.cuenta, misiones=json.dumps(sorted(j.misiones_pagadas)))
            j.credito += int(mi["dinero"])

    def _guardar_saldo(self, j):
        if j.cuenta is not None and j.saldo is not None and not j.bot:
            self.alm.poner(j.cuenta, saldo=int(j.saldo))

    def _m_guardar(self, j, m):
        self._guardar_saldo(j)
        p = m.get("p")
        if isinstance(p, dict):
            texto = json.dumps(p, ensure_ascii=False, separators=(",", ":"))
            if len(texto) <= MAX_LINEA:
                self.alm.poner(j.cuenta, partida=texto, dia_salida=self.dia)
                if m.get("ya"):
                    self.alm.guardar()
                    self._enviar(j, {"t": "guardado"})

    def _m_aspecto(self, j, m):
        """Lo que lleva puesto un jugador, como lo cuenta su juego: se reparte tal cual a los demás. El servidor no sabe de
        ropa ni tiene por qué: la da el juego de cada uno."""
        texto = "".join(c for c in str(m.get("texto", "")) if c.isprintable())[:200]
        j.aspecto = texto
        self._a_todos({"t": "aspecto", "de": j.id, "texto": texto}, menos=j)

    def _m_chat(self, j, m):
        texto = str(m.get("texto", "")).strip()[:300]
        if not texto:
            return
        if texto.startswith("/") and j.admin:
            self._aviso(j, self.orden(texto[1:], j.nombre))
            return
        canal = m.get("canal") if m.get("canal") in ("todos", "cerca", "banda", "priv", "grupo") else "todos"
        obj = {"t": "chat", "de": j.id, "nombre": j.nombre, "texto": texto, "canal": canal}
        if canal == "cerca":
            for o in self.jugadores.values():
                if o.dentro and o is not j and o.mapa == j.mapa and j.dist(o) <= 80:
                    self._enviar(o, obj)
        elif canal == "banda":
            if j.banda is None:
                return self._aviso(j, "No estás en ninguna banda.")
            self._a_banda(j.banda, obj, menos=j)
        elif canal == "grupo":
            for o in self._grupo(j):
                if o is not j:
                    self._enviar(o, obj)
        elif canal == "priv":
            o = self.jugadores.get(m.get("a"))
            if o is not None and o.dentro:
                self._enviar(o, obj)
        else:
            self._a_todos(obj, menos=j)

    def _m_act(self, j, m):
        d = m.get("d")
        if isinstance(d, dict) and len(json.dumps(d)) < 3000:
            self._a_todos({"t": "act", "de": j.id, "nombre": j.nombre, "d": d}, menos=j)

    def _m_evento(self, j, m):
        que = str(m.get("que", ""))[:20]
        self._a_todos({"t": "evento", "de": j.id, "que": que}, menos=j, mapa=j.mapa)
        if j.mapa is None:
            return
        if que.startswith("d:") or que == "grito":             # la gente de la calle se asusta, y si hay una patrulla cerca, lo ve
            self.peatones_susto(j.mapa, j.x, j.y, 40 if que.startswith("d:") else 15)
            if que.startswith("d:"):
                self.patrulla_ve(j)

    def _m_dinero(self, j, m):
        o = self.jugadores.get(m.get("a"))
        try:
            n = max(1, min(100000, int(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        if o is None or not o.dentro or o is j:
            return
        if si(self.cfg["economia"]) and not j.bot:
            # El dinero lo lleva el servidor: lo que uno da sale de su saldo, y tiene que llevarlo encima. Si no, quien
            # recibe tendría dinero que no ha salido de ningún bolsillo. Quien acaba de entrar y aún no ha dicho cuánto
            # lleva, no lleva nada.
            if j.saldo is None or j.dinero < n:
                self._aviso(j, "No llevas %d euros encima: no se entregan." % n, "error")
                self._enviar(j, {"t": "dinero", "nombre": "El servidor, de vuelta", "n": n})      # su juego ya los había restado
                j.credito = max(0, j.credito - n)             # una devolución no es dinero nuevo
                return
            j.dinero -= n
            j.saldo = max(0, j.saldo - n)
        self._enviar(o, {"t": "dinero", "de": j.id, "nombre": j.nombre, "n": n})

    def _m_dar(self, j, m):
        """Dar un arma, munición o un objeto a otro jugador que está al lado."""
        o = self.jugadores.get(m.get("a"))
        if o is None or not o.dentro or o is j or o.mapa != j.mapa or j.dist(o) > 12:
            return self._aviso(j, "Esa persona ya no está a tu lado.")
        try:
            n = max(1, min(999, int(m.get("n", 1))))
        except (TypeError, ValueError):
            return
        clase = m.get("clase") if m.get("clase") in ("arma", "balas", "objeto") else None
        ident = str(m.get("id", ""))[:40]
        if clase is None or not ident:
            return
        self._enviar(o, {"t": "recibe", "de": j.id, "nombre": j.nombre, "clase": clase, "id": ident, "n": n})
        self._enviar(j, {"t": "dado", "a": o.id, "nombre": o.nombre, "clase": clase, "id": ident, "n": n})

    def _m_quien(self, j, m):
        self._enviar(j, {"t": "quien", "e": [dict(o.publico(), mapa=o.mapa, pasivo=o.pasivo, recompensa=self._recompensa(o)) for o in self.jugadores.values() if o.dentro]})

    def _recompensa(self, j):
        f = self.alm.cuenta(j.cuenta)
        return int(f["recompensa"] or 0) if f else 0

    # ============================================================ hora y mundo
    def _hora(self):
        return {"reloj": round(self.reloj, 1), "dia": self.dia, "lluvia": self.lluvia, "luces": round(self.t_luces, 2)}

    def segura(self, j):
        if not si(self.cfg["zonas_seguras"]):
            return False
        if j.interior:
            return True
        return any(math.hypot(j.x - x, j.y - y) <= RADIO_SEGURO for x, y in self.seguras.get(j.mapa, ()))

    async def _bucle_estados(self):
        n = 0
        while self.activo:
            await asyncio.sleep(0.1)
            n += 1
            try:
                self.bots_mover(0.1)
                self.trafico_mover(0.1)
                self.peatones_mover(0.1)
                self.policia_mover(0.1)
            except Exception as e:
                self.log("Error moviendo a los personajes y el tráfico del servidor: %s: %s" % (type(e).__name__, e))
            try:
                self._repartir_estados(n)
            except Exception as e:
                self.log("Error repartiendo las posiciones: %s: %s" % (type(e).__name__, e))

    def _repartir_estados(self, n):
        """Diez veces por segundo: a cada jugador, dónde están los demás.

        Pensado para que valga igual con cuatro que con cuatrocientos, en procesador y en red:
        - La ficha de cada jugador se escribe una sola vez por vuelta, no una por cada uno que la recibe, y se agrupa por
          localidad y por zona. A los que están en la misma zona les llega el mismo texto, ya hecho.
        - A cada cual le llegan al detalle, diez veces por segundo, los que tiene cerca (su zona y las de alrededor).
        - De los demás de su localidad le llega una ficha corta, con dónde andan, una vez por segundo.
        - De los de las demás localidades, lo mismo cada dos segundos.
        - Si alrededor hay una multitud, las fichas al detalle se reparten menos veces por segundo.
        Con radio_detalle a 0 se reparte todo al detalle y siempre, como cuando hay poca gente."""
        todos = [j for j in self.jugadores.values() if j.dentro or j.fantasma]
        radio = float(self.cfg.get("radio_detalle", 0) or 0)
        medio = n % 10 == 0                                    # una vez por segundo, toda la localidad
        lejos = n % 20 == 0                                    # cada dos segundos, las demás localidades
        escribir = json.dumps
        zonas, cuantos = {}, {}                                # (localidad, zona) -> fichas al detalle, y cuántas son
        cortas = {}                                            # localidad -> fichas cortas
        mia, mia_corta = {}, {}                                # la de cada uno, para quitarla de lo que se le manda
        for o in todos:
            if o.mapa is None:
                if lejos and o.dentro and o.mapa_fuera:        # en una localidad que este servidor no conoce
                    f = '"%d":%s,' % (o.id, escribir({"m": o.mapa_fuera, "x": 0, "y": 0, "r": 0, "v": None, "s": 0}, separators=(",", ":")))
                    mia_corta[o.id] = f
                    cortas.setdefault(None, []).append(f)
                continue
            ficha = {"m": o.mapa, "x": round(o.x, 1), "y": round(o.y, 1), "r": round(o.rumbo), "v": o.veh, "s": round(o.vel, 1),
                     "vi": o.vid, "ag": int(o.agachado), "pa": int(o.pasivo), "sg": int(self.segura(o)), "in": int(o.interior), "es": o.estrellas}
            if o.po:
                ficha["po"] = o.po
            f = '"%d":%s,' % (o.id, escribir(ficha, separators=(",", ":")))
            mia[o.id] = f
            clave = (o.mapa, int(o.x // radio), int(o.y // radio)) if radio > 0 else (o.mapa, 0, 0)
            zonas.setdefault(clave, []).append(f)
            if (medio and radio > 0) or lejos:
                f = '"%d":%s,' % (o.id, escribir({"m": o.mapa, "x": round(o.x), "y": round(o.y), "r": 0, "v": o.veh, "s": 0}, separators=(",", ":")))
                mia_corta[o.id] = f
                cortas.setdefault(o.mapa, []).append(f)
        for clave, fichas in zonas.items():
            cuantos[clave] = len(fichas)
            zonas[clave] = "".join(fichas)
        cortas = {mapa: "".join(fichas) for mapa, fichas in cortas.items()}
        alrededor, de_fuera = {}, {}                           # lo que rodea a cada zona y lo de fuera de cada localidad: se hace una vez
        po_activo, pe_activo = self._po_activo(), self._pe_activo()
        tr_o_po = self._tr_activo() or po_activo
        for j in todos:
            if not j.dentro or j.bot:
                continue
            partes = ""
            if j.mapa is not None:
                clave = (j.mapa, int(j.x // radio), int(j.y // radio)) if radio > 0 else (j.mapa, 0, 0)
                cerca = alrededor.get(clave)
                if cerca is None:
                    if radio > 0:
                        trozos, gente = [], 0
                        for dx in (-1, 0, 1):
                            for dy in (-1, 0, 1):
                                otra = (clave[0], clave[1] + dx, clave[2] + dy)
                                if otra in zonas:
                                    trozos.append(zonas[otra])
                                    gente += cuantos[otra]
                        cerca = ("".join(trozos), gente)
                    else:
                        cerca = (zonas.get(clave, ""), 0)
                    alrededor[clave] = cerca
                texto, gente = cerca
                cada = 1 if gente <= 24 else 2 if gente <= 60 else 4      # entre una multitud, menos veces por segundo
                if radio > 0 and medio:
                    # primero las fichas cortas de toda la localidad y después las de detalle: si alguien sale dos veces, vale la última
                    partes = cortas.get(j.mapa, "").replace(mia_corta[j.id], "", 1) + texto.replace(mia[j.id], "", 1)
                elif n % cada == 0:
                    partes = texto.replace(mia[j.id], "", 1)
            if lejos:
                fuera = de_fuera.get(j.mapa)
                if fuera is None:
                    fuera = de_fuera[j.mapa] = "".join(t for mapa, t in cortas.items() if mapa != j.mapa or mapa is None)
                if j.mapa is None and j.id in mia_corta:
                    fuera = fuera.replace(mia_corta[j.id], "", 1)
                partes = fuera + partes
            mas = {}
            if j.mapa is not None and n % 2 == 0:
                if po_activo:
                    mas["es"] = j.estrellas                    # su nivel de búsqueda: el que vale es este
                    ag = self.agentes_para(j)                  # los agentes a pie que tiene cerca
                    if ag or getattr(j, "ve_agentes", False):
                        mas["po"] = ag
                    j.ve_agentes = bool(ag)
                if tr_o_po:                                    # el tráfico de su localidad, cinco veces por segundo
                    mas["tr"] = self.trafico_para(j)
                    mas["lu"] = round(self.t_luces, 2)         # y la hora de los semáforos, para que no se desajusten
                if pe_activo:
                    mas["pe"] = self.peatones_para(j)          # y la gente de la calle que tiene cerca
                    mas["lu"] = round(self.t_luces, 2)
            if partes or "tr" in mas or "pe" in mas or "po" in mas:
                cuerpo = '{"t":"estados","e":{' + partes[:-1] + "}"
                if mas:
                    cuerpo += "," + escribir(mas, separators=(",", ":"))[1:-1]
                self._enviar(j, ESTADOS, (cuerpo + "}\n").encode("utf-8"))

    async def _bucle_lento(self):
        """Cada segundo: el reloj, las guerras, los que se fueron en combate, los vehículos viejos y el guardado."""
        k = 0
        while self.activo:
            await asyncio.sleep(1.0)
            k += 1
            try:
                self._tic(1.0, k)
            except Exception as e:
                self.log("Error en el reloj del servidor: %s: %s" % (type(e).__name__, e))

    def _tic(self, dt, k):
        self.reloj += dt / 2.0                                 # un minuto del juego son dos segundos, como en el juego
        if self.reloj >= 1440:
            self.reloj -= 1440
            self.dia += 1
            self._medianoche()
        if k % 30 == 0:
            if self.rng.random() < 0.04:
                self.lluvia = not self.lluvia
            self._a_todos({"t": "hora", "h": self._hora()})
        ahora = time.monotonic()
        parado = 60.0 * int(self.cfg.get("inactividad_minutos", 0) or 0)
        for j in list(self.jugadores.values()):
            if not j.dentro and j.fantasma and ahora >= j.fantasma:
                self.jugadores.pop(j.id, None)
                self._a_todos({"t": "sale", "id": j.id})
            elif j.dentro and not j.bot and ahora - j.t_ultimo > 75:
                self._cortar(j)
            elif parado > 0 and j.dentro and not j.bot and not j.admin and ahora - j.t_actividad > parado:
                self.log("%s lleva %d minutos sin hacer nada: se le saca para dejar sitio." % (j.nombre, parado // 60))
                self._echar(j, "Llevas %d minutos sin hacer nada y el servidor te ha sacado para dejar sitio. Tu personaje está guardado: puedes volver a entrar." % (parado // 60))
                j.t_actividad = ahora
        self.bots_pensar(dt)
        self.trafico_pensar()
        self.peatones_pensar()
        self.policia_pensar()
        self._guerras_paso(dt)
        self._robos_paso()
        if k % 60 == 0:
            tope = self.ahora() - 3600.0 * int(self.cfg["vehiculos_horas"])
            for v in [v for v in self.vehiculos.values() if v["por"] is None and v.get("t", 0) < tope]:
                self._quitar_vehiculo(v["id"])
            for ident in [i for i, d in self.invitaciones_banda.items() if d["hasta"] < ahora]:
                self.invitaciones_banda.pop(ident, None)
        if ahora - self._t_guardado >= 60.0 * max(1, int(self.cfg.get("guardado_minutos", 1) or 1)):
            self._t_guardado = ahora
            self.guardar_todo()
        horas = int(self.cfg.get("copia_auto_horas", 0) or 0)
        if horas > 0 and ahora - self._t_copia >= 3600.0 * horas:
            self._t_copia = ahora
            try:
                self.log("Copia de seguridad automática hecha: %s" % os.path.basename(self.copia_seguridad(automatica=True)))
            except Exception as e:
                self.log("No se ha podido hacer la copia de seguridad automática: %s: %s" % (type(e).__name__, e))

    def copia_seguridad(self, automatica=False):
        """Guarda todo y hace una copia de seguridad en la carpeta copias, dentro de la de datos. Devuelve su ruta."""
        self.guardar_todo()
        ruta = copias.hacer(self.cfg["datos"], conexion=self.alm.db, conf=self.ruta_conf, automatica=automatica)
        if automatica:
            copias.podar(self.cfg["datos"], int(self.cfg.get("copias_guardar", 7) or 7))
        return ruta
    def _medianoche(self):
        renta = int(self.cfg["renta_barrio"])
        cuentas = {}
        for t in self.alm.territorios():
            cuentas[t["banda"]] = cuentas.get(t["banda"], 0) + renta
        for banda, total in cuentas.items():
            self.alm.apunte(banda, "Barrios", total, "renta de los barrios")
            self._a_banda(banda, {"t": "aviso", "texto": "Los barrios de tu banda dejan %d euros en la caja." % total, "son": "dinero"})
            self._banda_difundir(banda)
        self._a_todos({"t": "hora", "h": self._hora(), "medianoche": True})
        self._propiedades_abandonadas()
        for j in self.jugadores.values():                     # lo que les robaron ayer a sus negocios se descuenta ahora
            if j.dentro:
                total = self.alm.cobrar_robos(j.cuenta)
                if total:
                    self._enviar(j, {"t": "robos_dia", "total": total})

    # ================================================================ vehículos
    def _veh_publico(self, v):
        return {k: v.get(k) for k in ("id", "modelo", "nombre", "m", "x", "y", "r", "salud", "por", "mejoras")}

    def _m_veh_tomar(self, j, m):
        """El jugador se sube a un vehículo de su mundo: desde ahora es de todos, y cualquiera puede quitárselo."""
        modelo = m.get("modelo")
        if modelo not in self.mundo["modelos"] or j.mapa is None:
            return
        if j.vid is not None and j.vid in self.vehiculos:
            self._soltar_vehiculo(j, self.vehiculos[j.vid])
        self._nv += 1
        try:
            salud = max(1.0, min(2000.0, finito(m.get("salud", self.mundo["modelos"][modelo]["salud"]))))
        except (TypeError, ValueError):
            salud = float(self.mundo["modelos"][modelo]["salud"])
        mejoras = m.get("mejoras") if isinstance(m.get("mejoras"), dict) and len(json.dumps(m.get("mejoras"))) < 300 else {}
        v = {"id": self._nv, "modelo": modelo, "nombre": limpiar_nombre(m.get("nombre"), 40) or self.mundo["modelos"][modelo]["nombre"],
             "m": j.mapa, "x": j.x, "y": j.y, "r": j.rumbo, "salud": salud, "por": j.id, "dueno": j.cuenta, "t": self.ahora(), "mejoras": mejoras}
        self.vehiculos[v["id"]] = v
        j.vid = v["id"]
        j.t_vid = time.monotonic()
        self._enviar(j, {"t": "veh_tuyo", "id": v["id"], "ref": m.get("ref")})
        self._a_todos({"t": "veh_ocupado", "id": v["id"], "por": j.id, "v": self._veh_publico(v)}, menos=j)

    def _soltar_vehiculo(self, j, v, datos=None):
        datos = datos or {}
        try:
            v.update(m=j.mapa, x=finito(datos.get("x", j.x)), y=finito(datos.get("y", j.y)), r=finito(datos.get("r", j.rumbo)),
                     salud=max(0.0, min(2000.0, finito(datos.get("salud", v["salud"])))))
        except (TypeError, ValueError):
            pass
        v["por"] = None
        v["t"] = self.ahora()
        j.vid = None
        self._a_todos({"t": "veh_libre", "v": self._veh_publico(v)}, menos=j)
        mios = sorted((o for o in self.vehiculos.values() if o.get("dueno") == j.cuenta and o["por"] is None), key=lambda o: o.get("t", 0))
        for viejo in mios[:-int(self.cfg["vehiculos_por_jugador"])]:
            self._quitar_vehiculo(viejo["id"])

    def _m_veh_dejar(self, j, m):
        v = self.vehiculos.get(m.get("id"))
        if v is not None and v["por"] == j.id:
            self._soltar_vehiculo(j, v, m)

    def _m_veh_subir(self, j, m):
        """Subirse a un vehículo aparcado de otro jugador: el primero que lo pide se lo lleva."""
        v = self.vehiculos.get(m.get("id"))
        if v is None:
            return self._enviar(j, {"t": "veh_no", "id": m.get("id"), "motivo": "Ese vehículo ya no está."})
        if v["por"] is not None and v["por"] != j.id:
            return self._enviar(j, {"t": "veh_no", "id": v["id"], "motivo": "Alguien se te ha adelantado."})
        if v["m"] != j.mapa or math.hypot(v["x"] - j.x, v["y"] - j.y) > 14:
            return self._enviar(j, {"t": "veh_no", "id": v["id"], "motivo": "Estás demasiado lejos."})
        if j.vid is not None and j.vid in self.vehiculos and j.vid != v["id"]:
            self._soltar_vehiculo(j, self.vehiculos[j.vid])
        robo = v.get("dueno") not in (None, j.cuenta)
        antes = v.get("dueno")
        if robo and not any(o.dentro and o.cuenta == antes for o in self.jugadores.values()):
            self.alm.dejar_pendiente(antes, {"que": "coche", "nombre": v["nombre"], "por": j.nombre})      # se lo dirá al volver
        v.update(por=j.id, dueno=j.cuenta, t=self.ahora())
        j.vid = v["id"]
        j.t_vid = time.monotonic()
        self._enviar(j, {"t": "veh_ok", "id": v["id"], "v": self._veh_publico(v), "robado": robo})
        if robo:                                               # al dueño se le dice antes de que el coche desaparezca de su calle
            for o in self.jugadores.values():
                if o.dentro and o.cuenta == antes:
                    self._aviso(o, "%s se ha llevado tu %s." % (j.nombre, v["nombre"]), "alarma")
        self._a_todos({"t": "veh_ocupado", "id": v["id"], "por": j.id, "v": self._veh_publico(v)}, menos=j)

    def _m_veh_asaltar(self, j, m):
        """Sacar a otro jugador de su vehículo y quedárselo: tiene que ir despacio y tenerlo al lado."""
        v = self.vehiculos.get(m.get("id"))
        o = self.jugadores.get(v["por"]) if v is not None else None
        if v is None or o is None or o is j:
            return self._enviar(j, {"t": "veh_no", "id": m.get("id"), "motivo": "Ese vehículo ya no está."})
        if o.mapa != j.mapa or j.dist(o) > 9:
            return self._enviar(j, {"t": "veh_no", "id": v["id"], "motivo": "Estás demasiado lejos."})
        if o.vel > 6:
            return self._enviar(j, {"t": "veh_no", "id": v["id"], "motivo": "Va demasiado rápido para abrir la puerta."})
        if not self._puede_atacar(j, o, avisar=True):
            return self._enviar(j, {"t": "veh_no", "id": v["id"], "motivo": ""})
        self._marcar_agresion(j, o)
        self._enviar(o, {"t": "sacado", "por": j.id, "nombre": j.nombre, "id": v["id"]})
        o.vid = None
        v.update(por=j.id, dueno=j.cuenta, t=self.ahora(), m=j.mapa)
        j.vid = v["id"]
        j.t_vid = time.monotonic()
        self._enviar(j, {"t": "veh_ok", "id": v["id"], "v": self._veh_publico(v), "robado": True, "asalto": o.nombre})
        self._a_todos({"t": "veh_ocupado", "id": v["id"], "por": j.id, "v": self._veh_publico(v)}, menos=j)

    def _m_veh_dano(self, j, m):
        v = self.vehiculos.get(m.get("id"))
        if v is None or v["m"] != j.mapa:
            return
        try:
            n = max(0.0, min(500.0, float(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        if v["por"] is not None and v["por"] != j.id:           # va alguien dentro: el daño se lo aplica su juego
            o = self.jugadores.get(v["por"])
            if o is not None and self._puede_atacar(j, o, avisar=True):
                self._marcar_agresion(j, o)
                self._enviar(o, {"t": "veh_golpe", "id": v["id"], "n": n, "de": j.id, "nombre": j.nombre})
            return
        v["salud"] = max(0.0, v["salud"] - n)
        if v["salud"] <= 0:
            self._a_todos({"t": "veh_revienta", "id": v["id"], "x": v["x"], "y": v["y"], "m": v["m"]})
            self._quitar_vehiculo(v["id"], avisar=False)
        else:
            self._a_todos({"t": "veh_salud", "id": v["id"], "salud": v["salud"]}, mapa=v["m"])

    def _m_veh_fin(self, j, m):
        """El vehículo deja de existir: lo ha metido en su garaje, lo ha vendido o ha reventado."""
        v = self.vehiculos.get(m.get("id"))
        if v is not None and (v["por"] == j.id or (v["por"] is None and v.get("dueno") == j.cuenta)):
            if j.vid == v["id"]:
                j.vid = None
            self._quitar_vehiculo(v["id"])

    def _quitar_vehiculo(self, ident, avisar=True):
        v = self.vehiculos.pop(ident, None)
        if v is not None:
            o = self.jugadores.get(v.get("por"))
            if o is not None and o.vid == ident:
                o.vid = None
            if avisar:
                self._a_todos({"t": "veh_fuera", "id": ident})

    # ============================================================== propiedades
    def _props(self):
        return {f["lugar"]: {"cuenta": f["cuenta"], "nombre": f["nombre"], "oferta": int(f["oferta"] or 0)} for f in self.alm.propiedades()}

    def _prop_difundir(self, lugar, antes=None):
        f = self.alm.propiedad(lugar)
        self._a_todos({"t": "prop", "lugar": lugar, "cuenta": f["cuenta"] if f else None, "nombre": f["nombre"] if f else "",
                       "oferta": int(f["oferta"] or 0) if f else 0, "antes": antes})

    def _m_prop_soltar(self, j, m):
        """Vender tu casa o tu negocio al mercado: recuperas una parte y vuelve a estar en venta para cualquiera."""
        l = self.lugares.get(m.get("lugar"))
        f = self.alm.propiedad(l["id"]) if l is not None else None
        if f is None or f["cuenta"] != j.cuenta:
            return self._aviso(j, "Eso no es tuyo.")
        self._ver_pagos(j)
        f = self.alm.propiedad(l["id"])
        # Solo da dinero lo que el servidor vio pagar. Lo que se trajo de fuera, o se apuntó sin que saliera el dinero, se
        # puede tener y usar, pero al venderlo no devuelve nada: si no, bastaría apuntarse casas y venderlas para hacerse rico.
        pagada = bool(f["pagada"]) or not si(self.cfg["economia"])
        n = int(l["precio"]) * int(self.cfg["venta_mercado"]) // 100 if pagada else 0
        self.alm.quitar_propiedad(l["id"])
        j.prop_pend.pop(l["id"], None)
        self._prop_difundir(l["id"], antes=j.cuenta)
        if n:
            j.dinero += n
            self._enviar(j, {"t": "dinero", "nombre": "La venta de " + l["nombre"], "n": n})
        else:
            self._aviso(j, "%s vuelve al mercado, pero no te da dinero: a este servidor no le consta que la pagaras aquí." % l["nombre"])
        self._a_todos({"t": "aviso", "texto": "%s vuelve a estar en venta, en %s." % (l["nombre"], self.mundo["mapas"][l["mapa"]]["nombre"])}, menos=j)

    def _m_prop_oferta(self, j, m):
        """Poner tu propiedad en venta para otros jugadores, al precio que tú digas. Con cero, se retira."""
        l = self.lugares.get(m.get("lugar"))
        f = self.alm.propiedad(l["id"]) if l is not None else None
        if f is None or f["cuenta"] != j.cuenta:
            return self._aviso(j, "Eso no es tuyo.")
        try:
            precio = max(0, min(10 ** 8, int(m.get("precio", 0))))
        except (TypeError, ValueError):
            return
        self._ver_pagos(j)
        if precio and si(self.cfg["economia"]) and not self.alm.propiedad(l["id"])["pagada"]:
            return self._aviso(j, "No puedes vender %s a otro jugador: a este servidor no le consta que la pagaras aquí." % l["nombre"], "error")
        self.alm.poner_oferta(l["id"], precio)
        self._prop_difundir(l["id"])
        if precio:
            self._a_todos({"t": "aviso", "texto": "%s vende %s por %d euros." % (j.nombre, l["nombre"], precio)}, menos=j)

    def _m_prop_adquirir(self, j, m):
        """Comprarle a otro jugador la propiedad que tiene en venta."""
        l = self.lugares.get(m.get("lugar"))
        f = self.alm.propiedad(l["id"]) if l is not None else None
        if f is None or f["cuenta"] == j.cuenta or not f["oferta"]:
            return self._aviso(j, "Eso no está en venta.")
        precio = int(f["oferta"])
        if not self._cobrar(j, precio, "comprar " + l["nombre"]):
            return
        vendedor = f["cuenta"]
        self.alm.poner_propiedad(l["id"], j.cuenta, pagada=True)
        en_linea = next((o for o in self.jugadores.values() if o.dentro and o.cuenta == vendedor), None)
        if en_linea is not None:
            en_linea.dinero += precio
            self._enviar(en_linea, {"t": "dinero", "nombre": j.nombre + ", por " + l["nombre"], "n": precio})
        else:
            self.alm.dejar_pendiente(vendedor, {"que": "venta", "lugar": l["id"], "n": precio, "por": j.nombre})
        self._prop_difundir(l["id"], antes=vendedor)

    def _propiedades_abandonadas(self):
        """Lo de quien lleva mucho sin entrar vuelve al mercado, y a él se le guarda su parte para cuando vuelva."""
        tope = self.ahora() - 86400.0 * int(self.cfg["propiedad_dias"])
        en_linea = {o.cuenta for o in self.jugadores.values() if o.dentro}
        for f in self.alm.propiedades_abandonadas(tope):
            l = self.lugares.get(f["lugar"])
            if l is None or f["cuenta"] in en_linea:
                continue
            self.alm.quitar_propiedad(f["lugar"])
            self.alm.dejar_pendiente(f["cuenta"], {"que": "caducada", "lugar": f["lugar"],
                                                   "n": int(l["precio"]) * int(self.cfg["venta_mercado"]) // 100 if f["pagada"] or not si(self.cfg["economia"]) else 0})
            self._prop_difundir(f["lugar"], antes=f["cuenta"])

    def _m_prop_comprar(self, j, m):
        """Una casa o un negocio solo puede ser de un jugador. El primero que lo compra se lo queda."""
        l = self.lugares.get(m.get("lugar"))
        if l is None:
            return
        f = self.alm.propiedad(l["id"])
        if f is not None and f["cuenta"] != j.cuenta:
            self._devolucion(j, int(l.get("precio", 0)))       # su juego le devuelve lo pagado: es dinero que ya era suyo
            return self._enviar(j, {"t": "prop_no", "lugar": l["id"], "nombre": f["nombre"]})
        if f is None:
            self.alm.poner_propiedad(l["id"], j.cuenta, pagada=not si(self.cfg["economia"]) or j.bot)
            if si(self.cfg["economia"]) and not j.bot and int(l.get("precio", 0) or 0) > 0:
                j.prop_pend[l["id"]] = [time.monotonic(), int(l["precio"])]     # el juego la paga por su cuenta: hay que verlo
                self._ver_pagos(j)
            self._prop_difundir(l["id"])
            self._a_todos({"t": "aviso", "texto": "%s compra %s, en %s." % (j.nombre, l["nombre"], self.mundo["mapas"][l["mapa"]]["nombre"])}, menos=j)

    def _banda_de(self, cuenta):
        mi = self.alm.miembro(cuenta)
        return mi["banda"] if mi is not None else None

    def _m_robo(self, j, m):
        """Atracar el negocio de otro jugador: hay que aguantar dentro veinte segundos, y al dueño le salta el aviso."""
        l = self.lugares.get(m.get("lugar"))
        f = self.alm.propiedad(l["id"]) if l is not None and l["tipo"] == "negocio" else None
        if f is None or f["cuenta"] == j.cuenta:
            return self._aviso(j, "Este negocio no es de otro jugador.")
        if not si(self.cfg["pvp"]):
            return self._aviso(j, "En este servidor no se roba a otros jugadores.")
        if j.pasivo:
            return self._aviso(j, "En modo pasivo no puedes atracar a nadie.")
        if j.mapa != l["mapa"] or math.hypot(j.x - l["x"], j.y - l["y"]) > 30 or j.veh:
            return self._aviso(j, "Tienes que estar en la puerta, a pie.")
        if j.arma == "punos":
            return self._aviso(j, "Con las manos vacías no impones. Saca un arma.")
        banda = self._banda_de(f["cuenta"])
        if banda is not None and j.banda is not None and (banda == j.banda or banda in self.alm.aliadas(j.banda)):
            return self._aviso(j, "Ese negocio es de alguien de tu banda o de una banda aliada.")
        if f["robado_dia"] == self.dia:
            return self._aviso(j, "A este negocio ya le han vaciado la caja hoy. Vuelve otro día.")
        if j.id in self.robos or any(r["lugar"] == l["id"] for r in self.robos.values()):
            return self._aviso(j, "Ya hay un atraco en marcha.")
        segundos = int(self.cfg["robo_segundos"])
        self.robos[j.id] = {"lugar": l["id"], "fin": time.monotonic() + segundos, "dueno": f["cuenta"], "nombre_dueno": f["nombre"]}
        self._enviar(j, {"t": "robo_empieza", "lugar": l["id"], "segundos": segundos, "nombre": f["nombre"]})
        for o in self.jugadores.values():                     # salta la alarma: al dueño y a su banda
            if o.dentro and o is not j and (o.cuenta == f["cuenta"] or (banda is not None and o.banda == banda)):
                self._enviar(o, {"t": "robo_aviso", "lugar": l["id"], "de": j.id, "nombre": j.nombre, "segundos": segundos, "tuyo": o.cuenta == f["cuenta"]})

    def _robo_fin(self, j, ok, motivo=""):
        r = self.robos.pop(j.id, None)
        if r is None:
            return
        l = self.lugares[r["lugar"]]
        botin = 0
        if ok:
            botin = int(l.get("ingresos", 0))
            self.alm.robo_en(l["id"], self.dia, botin)
            j.dinero += botin
        if j.dentro:
            self._enviar(j, {"t": "robo_fin", "ok": bool(ok), "botin": botin, "motivo": motivo, "lugar": l["id"]})
        for o in self.jugadores.values():
            if o.dentro and o.cuenta == r["dueno"]:
                self._aviso(o, ("%s ha vaciado la caja de %s: %d euros. Se te descuentan a medianoche." % (j.nombre, l["nombre"], botin)) if ok
                            else ("%s no ha conseguido atracar %s." % (j.nombre, l["nombre"])), "alarma" if ok else "llegada")

    def _robos_paso(self):
        ahora = time.monotonic()
        for ident, r in list(self.robos.items()):
            j = self.jugadores.get(ident)
            l = self.lugares[r["lugar"]]
            if j is None or not j.dentro:
                self.robos.pop(ident, None)
                continue
            if j.salud <= 0:
                self._robo_fin(j, False, "Te han tumbado antes de vaciar la caja.")
            elif j.mapa != l["mapa"] or math.hypot(j.x - l["x"], j.y - l["y"]) > 35 or j.veh:
                self._robo_fin(j, False, "Te has ido antes de vaciar la caja.")
            elif ahora >= r["fin"]:
                self._robo_fin(j, True)

    # ================================================================== combate
    def _relacion(self, a, b):
        """amigos: misma banda sin fuego amigo, bandas aliadas o el mismo grupo de misión."""
        if a.grupo is not None and a.grupo == b.grupo:
            return "grupo"
        if a.banda is not None and b.banda is not None:
            if a.banda == b.banda:
                f = self.alm.banda(a.banda)
                return None if (f is not None and f["fuego"]) else "banda"
            if b.banda in self.alm.aliadas(a.banda):
                return "aliados"
        return None

    def _puede_atacar(self, a, o, avisar=False):
        ahora = time.monotonic()
        motivo = None
        if not si(self.cfg["pvp"]):
            motivo = "En este servidor no hay combate entre jugadores."
        elif a.mapa != o.mapa:
            motivo = "Ya no está aquí."
        elif a.pasivo:
            motivo = "Estás en modo pasivo: no puedes herir a nadie."
        elif o.pasivo:
            motivo = "%s está en modo pasivo: no se le puede herir." % o.nombre
        elif ahora < a.protegido:
            motivo = "Acabas de llegar: todavía no puedes atacar a nadie."
        elif ahora < o.protegido:
            motivo = "%s acaba de llegar y está protegido unos segundos." % o.nombre
        elif self.segura(a) or self.segura(o):
            motivo = "Zona segura: aquí nadie puede herir a nadie."
        else:
            rel = self._relacion(a, o)
            if rel == "banda":
                motivo = "%s es de tu banda, y el fuego amigo está quitado." % o.nombre
            elif rel == "aliados":
                motivo = "%s es de una banda aliada." % o.nombre
            elif rel == "grupo":
                motivo = "%s va contigo en la misión." % o.nombre
        if motivo and avisar and ahora - getattr(a, "_t_motivo", 0) > 3:
            a._t_motivo = ahora
            self._enviar(a, {"t": "fallo", "a": o.id, "motivo": motivo})
        return motivo is None

    def _marcar_agresion(self, a, o):
        ahora = time.monotonic()
        if ahora - a.golpeado.get(o.id, -999) > 60:             # él no me había tocado: el que empieza soy yo
            a.agredio[o.id] = ahora
        o.golpeado[a.id] = ahora

    def _m_ataque(self, j, m):
        """Un disparo o un golpe contra otro jugador. El servidor decide si llega y cuánto quita."""
        o = self.jugadores.get(m.get("a"))
        if o is None or o is j or (not o.dentro and not o.fantasma):
            return
        arma = self.mundo["armas"].get(m.get("arma") if m.get("arma") in self.mundo["armas"] else j.arma)
        if arma is None:
            return
        ahora = time.monotonic()
        if ahora - j.t_ataque < float(arma["cadencia"]) * 0.75:
            return                                             # más rápido de lo que dispara esa arma
        if not self._puede_atacar(j, o, avisar=True):
            return
        j.t_ataque = ahora
        d = j.dist(o)
        alcance = float(arma["alcance"])
        self._a_todos({"t": "tiro", "de": j.id, "arma": m.get("arma") or j.arma, "x": round(j.x, 1), "y": round(j.y, 1)}, menos=j, mapa=j.mapa)
        self._marcar_agresion(j, o)
        if d > alcance * 1.15 + 3.0:
            return self._enviar(j, {"t": "fallo", "a": o.id, "motivo": "", "lejos": True})
        prob = float(arma["precision"]) * (1.0 - 0.45 * min(1.0, d / max(1.0, alcance)))
        if o.agachado:
            prob *= 0.8
        if o.veh:
            prob *= 0.75
        if arma["tipo"] == "cuerpo":
            prob = max(prob, 0.85)
        if self.rng.random() > prob:
            self._enviar(j, {"t": "fallo", "a": o.id, "motivo": ""})
            self._enviar(o, {"t": "silbido", "de": j.id, "nombre": j.nombre, "x": round(j.x, 1), "y": round(j.y, 1)})
            return
        dano = float(arma["dano"]) * (1.0 - 0.4 * min(1.0, d / max(1.0, alcance))) * self.rng.uniform(0.85, 1.15)
        if o.veh:
            dano *= 0.5                                        # la chapa para parte
        dano = round(max(1.0, dano), 1)
        o.salud = max(0.0, o.salud - dano)
        self._enviar(j, {"t": "impacto", "a": o.id, "nombre": o.nombre, "dano": dano})
        if o.bot:
            return self.bot_golpeado(o, j)
        if o.dentro:
            self._enviar(o, {"t": "herido", "de": j.id, "nombre": j.nombre, "arma": m.get("arma") or j.arma, "dano": dano, "x": round(j.x, 1), "y": round(j.y, 1)})
        elif o.salud <= 0:                                     # se fue en pleno combate y ha caído igual
            self._caida(o, j, ausente=True)

    def _m_atropello(self, j, m):
        o = self.jugadores.get(m.get("a"))
        if o is None or o is j or not o.dentro or j.veh is None or o.veh is not None:
            return
        if o.mapa != j.mapa or j.dist(o) > 7 or not self._puede_atacar(j, o, avisar=True):
            return
        ahora = time.monotonic()
        if ahora - j.t_ataque < 1.0:
            return
        j.t_ataque = ahora
        self._marcar_agresion(j, o)
        dano = round(min(95.0, max(5.0, j.vel * 5.0)), 1)
        o.salud = max(0.0, o.salud - dano)
        self._enviar(j, {"t": "impacto", "a": o.id, "nombre": o.nombre, "dano": dano, "atropello": True})
        if o.bot:
            return self.bot_golpeado(o, j)
        self._enviar(o, {"t": "herido", "de": j.id, "nombre": j.nombre, "arma": "atropello", "dano": dano, "x": round(j.x, 1), "y": round(j.y, 1)})

    def _m_atraco(self, j, m):
        """Atracar a otro jugador, como a cualquiera de la calle: con un arma en la mano y a su lado."""
        o = self.jugadores.get(m.get("a"))
        if o is None or o is j or not o.dentro:
            return
        if o.mapa != j.mapa or j.dist(o) > 6 or j.veh or o.veh:
            return self._aviso(j, "Para atracar a alguien tenéis que estar los dos a pie y a un paso.")
        if j.arma == "punos":
            return self._aviso(j, "Con las manos vacías no impones. Saca un arma.")
        if not self._puede_atacar(j, o, avisar=True):
            return
        ahora = time.monotonic()
        if ahora - j.atracos.get(o.cuenta, -9999) < 300:
            return self._aviso(j, "A %s ya le has atracado hace un momento. No lleva más encima." % o.nombre)
        j.atracos[o.cuenta] = ahora
        botin = min(int(self.cfg["atraco_max"]), o.dinero * int(self.cfg["atraco"]) // 100)
        self._marcar_agresion(j, o)
        o.dinero = max(0, o.dinero - botin)
        j.dinero += botin
        self._enviar(o, {"t": "atracado", "de": j.id, "nombre": j.nombre, "pierde": botin})
        self._enviar(j, {"t": "atraco_ok", "a": o.id, "nombre": o.nombre, "botin": botin})
        if o.bot:
            self.bot_golpeado(o, j)

    def _m_po_golpe(self, j, m):
        """Le ha dado a un policía de los que persiguen a otro jugador: el golpe llega al juego de ese jugador."""
        o = self.jugadores.get(m.get("a"))
        if o is None or not o.dentro or o.mapa != j.mapa or o.bot:
            return
        try:
            dano = max(0.0, min(500.0, float(m.get("dano", 0))))
        except (TypeError, ValueError):
            return
        self._enviar(o, {"t": "po_golpe", "k": m.get("k"), "dano": dano, "de": j.id, "nombre": j.nombre})

    def _m_explosion(self, j, m):
        """Una granada, un cóctel o un cohete de un jugador: alcanza a los demás jugadores que estén dentro del radio."""
        arma = self.mundo["armas"].get(m.get("arma"))
        if arma is None or arma.get("tipo") != "explosivo":
            return
        ahora = time.monotonic()
        if ahora - j.t_ataque < float(arma["cadencia"]) * 0.75:
            return
        j.t_ataque = ahora
        try:
            x, y = finito(m.get("x")), finito(m.get("y"))
        except (TypeError, ValueError):
            return
        if math.hypot(x - j.x, y - j.y) > float(arma["alcance"]) * 1.3 + 6:
            return                                             # más lejos de lo que se puede lanzar
        radio = float(arma.get("radio") or 8.0)
        self._a_todos({"t": "estalla", "de": j.id, "x": round(x, 1), "y": round(y, 1)}, menos=j, mapa=j.mapa)
        self.peatones_susto(j.mapa, x, y, 60, 14.0)
        self.patrulla_ve(j)
        for o in list(self.jugadores.values()):
            if o is j or not o.dentro or o.mapa != j.mapa:
                continue
            d = math.hypot(o.x - x, o.y - y)
            if d > radio or not self._puede_atacar(j, o):
                continue
            self._marcar_agresion(j, o)
            dano = round(max(1.0, float(arma["dano"]) * (1.0 - 0.6 * d / radio) * (0.5 if o.veh else 1.0)), 1)
            o.salud = max(0.0, o.salud - dano)
            self._enviar(j, {"t": "impacto", "a": o.id, "nombre": o.nombre, "dano": dano})
            if o.bot:
                self.bot_golpeado(o, j)
                continue
            self._enviar(o, {"t": "herido", "de": j.id, "nombre": j.nombre, "arma": m.get("arma"), "dano": dano, "x": round(x, 1), "y": round(y, 1)})

    def _m_caido(self, j, m):
        """El juego de quien cae avisa de que ha caído ante otro jugador."""
        o = self.jugadores.get(m.get("por"))
        if o is None or time.monotonic() - j.golpeado.get(o.id, -999) > 20:
            j.golpeado.clear()
            return
        self._caida(j, o)

    def _caida(self, caido, por, ausente=False):
        ahora = time.monotonic()
        botin = min(int(self.cfg["botin_max"]), caido.dinero * int(self.cfg["botin"]) // 100)
        self.alm.sumar(por.cuenta, "bajas", 1)
        self.alm.sumar(caido.cuenta, "caidas", 1)
        recompensa = self._recompensa(caido)
        inocente = ahora - caido.agredio.get(por.id, -999) > 90 and ahora - por.agredio.get(caido.id, -999) <= 90 and recompensa == 0
        texto_extra = ""
        if recompensa > 0:
            self.alm.sumar(caido.cuenta, "recompensa", -recompensa)
            texto_extra = " Cobras además los %d euros que ofrecían por su cabeza." % recompensa
        if inocente:
            sube = int(self.cfg["recompensa"])
            self.alm.sumar(por.cuenta, "recompensa", sube)
            self._enviar(por, {"t": "buscado", "recompensa": self._recompensa(por), "sube": sube})
        por.dinero += botin
        if por.dentro:
            self._enviar(por, {"t": "baja", "a": caido.id, "nombre": caido.nombre, "botin": botin + recompensa, "texto": texto_extra})
        if ausente or not caido.dentro:
            self.alm.dejar_pendiente(caido.cuenta, {"que": "caido", "por": por.nombre, "pierde": botin})
            caido.fantasma = ahora                             # desaparece ya
        else:
            self._enviar(caido, {"t": "caes", "por": por.id, "nombre": por.nombre, "pierde": botin})
            caido.protegido = ahora + float(self.cfg["proteccion"])
            caido.dinero = max(0, caido.dinero - botin)
        caido.golpeado.clear()
        caido.agredio.clear()
        if caido.id in self.robos:
            self._robo_fin(caido, False, "Te han tumbado antes de vaciar la caja.")
        self._guerra_baja(por, caido)
        self._a_todos({"t": "muerte", "quien": caido.nombre, "por": por.nombre}, menos=por if por.dentro else None)
        self.alm.guardar()

    def _m_pasivo(self, j, m):
        if not si(self.cfg["modo_pasivo"]):
            return self._aviso(j, "En este servidor no hay modo pasivo.")
        ahora = time.monotonic()
        quiere = bool(m.get("si"))
        if quiere == j.pasivo:
            return
        if any(ahora - t < 60 for t in j.agredio.values()) or any(ahora - t < 30 for t in j.golpeado.values()):
            return self._aviso(j, "No puedes cambiar de modo en mitad de una pelea. Espera un minuto.")
        if ahora - j.t_pasivo < 120 and j.t_pasivo:
            return self._aviso(j, "Acabas de cambiar de modo. Espera dos minutos.")
        j.pasivo, j.t_pasivo = quiere, ahora
        self._enviar(j, {"t": "pasivo", "si": quiere})

    # =================================================================== bandas
    def _banda_datos(self, banda):
        if banda is None:
            return None
        f = self.alm.banda(banda)
        if f is None:
            return None
        en_linea = {o.cuenta for o in self.jugadores.values() if o.dentro}
        return {"id": f["id"], "nombre": f["nombre"], "caja": int(f["caja"]), "fuego": bool(f["fuego"]),
                "miembros": [{"cuenta": m["cuenta"], "nombre": m["nombre"], "rango": m["rango"], "en_linea": m["cuenta"] in en_linea} for m in self.alm.miembros(banda)],
                "aliadas": [self.alm.banda(a)["nombre"] for a in self.alm.aliadas(banda) if self.alm.banda(a) is not None],
                "apuntes": [{"nombre": a["nombre"], "cantidad": a["cantidad"], "motivo": a["motivo"]} for a in self.alm.apuntes(banda)],
                "barrios": [{"mapa": t["mapa"], "barrio": t["barrio"]} for t in self.alm.territorios() if t["banda"] == banda]}

    def _banda_difundir(self, banda):
        d = self._banda_datos(banda)
        for o in self.jugadores.values():
            if o.dentro and o.banda == banda:
                self._enviar(o, {"t": "banda", "b": d, "rango": o.rango})

    def _territorios(self):
        nombres = {b["id"]: b["nombre"] for b in self.alm.bandas()}
        return {"barrios": [{"mapa": t["mapa"], "barrio": t["barrio"], "banda": t["banda"], "nombre": nombres.get(t["banda"], "?")} for t in self.alm.territorios()],
                "guerras": [dict(g, ataca_n=nombres.get(g["ataca"], "?"), defiende_n=nombres.get(g["defiende"], "?"),
                                 falta=int(max(0, g["inicio"] - self.ahora())), queda=int(max(0, g["fin"] - self.ahora()))) for g in self.guerras]}

    def _difundir_territorios(self):
        self._a_todos({"t": "territorios", "e": self._territorios()})

    def _cobrar(self, j, n, motivo):
        """Lo que cuesta algo del servidor sale del bolsillo del jugador: su juego lo descuenta."""
        if j.dinero < n:
            self._aviso(j, "No te llega: hacen falta %d euros y llevas %d." % (n, j.dinero), "error")
            return False
        j.dinero -= n
        if j.saldo is not None:
            j.saldo = max(0, j.saldo - n)
            if si(self.cfg["economia"]) and not j.bot:        # su juego lo restará cuando le llegue el aviso
                j.cobros.append(n)
                j.t_cobros = time.monotonic()
        self._enviar(j, {"t": "cobro", "n": n, "motivo": motivo})
        return True

    def _m_banda_crear(self, j, m):
        nombre = limpiar_nombre(m.get("nombre"), 30)
        if j.banda is not None:
            return self._aviso(j, "Ya estás en una banda. Sal de ella antes de fundar otra.")
        if len(nombre) < 3:
            return self._aviso(j, "El nombre de la banda tiene que tener al menos tres letras.")
        if self.alm.banda_por_nombre(nombre) is not None:
            return self._aviso(j, "Ya hay una banda con ese nombre.")
        if not self._cobrar(j, int(self.cfg["precio_banda"]), "fundar la banda"):
            return
        j.banda, j.rango = self.alm.crear_banda(nombre, j.cuenta), "jefe"
        self._banda_difundir(j.banda)
        self._a_todos({"t": "aviso", "texto": "%s ha fundado la banda %s." % (j.nombre, nombre), "son": "territorio"}, menos=j)
        self._a_todos({"t": "de_banda", "id": j.id, "banda": j.banda})

    def _m_banda_invitar(self, j, m):
        o = self.jugadores.get(m.get("a"))
        if j.banda is None or j.rango not in ("jefe", "mano"):
            return self._aviso(j, "Solo el jefe y su mano derecha pueden invitar.")
        if o is None or not o.dentro or o.banda is not None:
            return self._aviso(j, "Esa persona no está, o ya tiene banda.")
        f = self.alm.banda(j.banda)
        self.invitaciones_banda[o.id] = {"banda": j.banda, "de": j.nombre, "hasta": time.monotonic() + 180}
        self._enviar(o, {"t": "banda_invita", "banda": j.banda, "nombre": f["nombre"], "de": j.nombre})
        self._aviso(j, "Invitación enviada a %s." % o.nombre)

    def _m_banda_resp(self, j, m):
        inv = self.invitaciones_banda.pop(j.id, None)
        if inv is None or j.banda is not None or self.alm.banda(inv["banda"]) is None:
            return self._aviso(j, "Esa invitación ya no vale.")
        if not m.get("si"):
            return
        self.alm.meter_miembro(j.cuenta, inv["banda"])
        j.banda, j.rango = inv["banda"], "miembro"
        self._banda_difundir(j.banda)
        self._a_banda(j.banda, {"t": "aviso", "texto": "%s entra en la banda." % j.nombre, "son": "pareja"}, menos=j)
        self._a_todos({"t": "de_banda", "id": j.id, "banda": j.banda})

    def _fuera_de_banda(self, cuenta):
        self.alm.sacar_miembro(cuenta)
        for o in self.jugadores.values():
            if o.cuenta == cuenta:
                o.banda = o.rango = None
                if o.dentro:
                    self._enviar(o, {"t": "banda", "b": None, "rango": None})
                    self._a_todos({"t": "de_banda", "id": o.id, "banda": None})

    def _m_banda_salir(self, j, m):
        if j.banda is None:
            return
        banda = j.banda
        era_jefe = j.rango == "jefe"
        nombre = j.nombre
        self._fuera_de_banda(j.cuenta)
        resto = self.alm.miembros(banda)
        if not resto:
            return self._disolver(banda)
        if era_jefe:                                           # hereda la mano derecha, o el más antiguo
            nuevo = resto[0]
            self.alm.meter_miembro(nuevo["cuenta"], banda, "jefe")
            self.alm.poner_banda(banda, jefe=nuevo["cuenta"])
            for o in self.jugadores.values():
                if o.cuenta == nuevo["cuenta"]:
                    o.rango = "jefe"
            self._a_banda(banda, {"t": "aviso", "texto": "%s deja la banda. Ahora manda %s." % (nombre, nuevo["nombre"])})
        else:
            self._a_banda(banda, {"t": "aviso", "texto": "%s deja la banda." % nombre})
        self._banda_difundir(banda)

    def _disolver(self, banda):
        f = self.alm.banda(banda)
        self.alm.borrar_banda(banda)
        self.guerras = [g for g in self.guerras if banda not in (g["ataca"], g["defiende"])]
        if f is not None:
            self._a_todos({"t": "aviso", "texto": "La banda %s se ha disuelto. Sus barrios quedan libres." % f["nombre"]})
        self._difundir_territorios()

    def _m_banda_expulsar(self, j, m):
        mi = self.alm.miembro(m.get("cuenta"))
        if j.banda is None or j.rango != "jefe" or mi is None or mi["banda"] != j.banda or mi["cuenta"] == j.cuenta:
            return self._aviso(j, "Solo el jefe puede echar a alguien de la banda.")
        self._fuera_de_banda(mi["cuenta"])
        self._a_banda(j.banda, {"t": "aviso", "texto": "El jefe ha echado a alguien de la banda."})
        self._banda_difundir(j.banda)

    def _m_banda_rango(self, j, m):
        mi = self.alm.miembro(m.get("cuenta"))
        rango = m.get("rango")
        if j.banda is None or j.rango != "jefe" or mi is None or mi["banda"] != j.banda or mi["cuenta"] == j.cuenta or rango not in RANGOS:
            return self._aviso(j, "Solo el jefe reparte los rangos.")
        self.alm.meter_miembro(mi["cuenta"], j.banda, rango)
        if rango == "jefe":                                    # ceder el mando
            self.alm.meter_miembro(j.cuenta, j.banda, "mano")
            self.alm.poner_banda(j.banda, jefe=mi["cuenta"])
            j.rango = "mano"
        for o in self.jugadores.values():
            if o.cuenta == mi["cuenta"]:
                o.rango = rango
        self._banda_difundir(j.banda)

    def _m_banda_ingresar(self, j, m):
        try:
            n = max(1, min(1000000, int(m.get("n", 0))))
        except (TypeError, ValueError):
            return
        if j.banda is None or not self._cobrar(j, n, "ingreso en la caja de la banda"):
            return
        self.alm.apunte(j.banda, j.nombre, n, "ingreso")
        self._banda_difundir(j.banda)

    def _m_banda_sacar(self, j, m):
        try:
            n = max(1, int(m.get("n", 0)))
        except (TypeError, ValueError):
            return
        f = self.alm.banda(j.banda) if j.banda is not None else None
        if f is None or j.rango not in ("jefe", "mano"):
            return self._aviso(j, "De la caja solo sacan el jefe y su mano derecha.")
        if n > f["caja"]:
            return self._aviso(j, "En la caja hay %d euros." % f["caja"])
        self.alm.apunte(j.banda, j.nombre, -n, "retirada")
        j.dinero += n
        self._enviar(j, {"t": "dinero", "nombre": "La caja de la banda", "n": n})
        self._banda_difundir(j.banda)

    def _m_banda_fuego(self, j, m):
        if j.banda is None or j.rango != "jefe":
            return self._aviso(j, "El fuego amigo lo decide el jefe.")
        self.alm.poner_banda(j.banda, fuego=int(bool(m.get("si"))))
        self.alm.guardar()
        self._a_banda(j.banda, {"t": "aviso", "texto": "Fuego amigo de la banda: %s." % ("sí, cuidado con los tuyos" if m.get("si") else "no")})
        self._banda_difundir(j.banda)

    def _m_banda_disolver(self, j, m):
        if j.banda is None or j.rango != "jefe":
            return self._aviso(j, "Solo el jefe puede disolver la banda.")
        banda = j.banda
        f = self.alm.banda(banda)
        if f is not None and f["caja"] > 0:                    # lo que queda en la caja se lo lleva el jefe
            j.dinero += int(f["caja"])
            self._enviar(j, {"t": "dinero", "nombre": "La caja de la banda", "n": int(f["caja"])})
        for mi in self.alm.miembros(banda):
            self._fuera_de_banda(mi["cuenta"])
        self._disolver(banda)

    def _m_banda_lista(self, j, m):
        out = []
        for b in self.alm.bandas():
            out.append({"id": b["id"], "nombre": b["nombre"], "miembros": len(self.alm.miembros(b["id"])),
                        "barrios": sum(1 for t in self.alm.territorios() if t["banda"] == b["id"])})
        self._enviar(j, {"t": "bandas", "e": out, "tuya": self._banda_datos(j.banda), "territorios": self._territorios()})

    def _m_alianza(self, j, m):
        otra = self.alm.banda_por_nombre(str(m.get("banda", "")))
        if j.banda is None or j.rango != "jefe" or otra is None or otra["id"] == j.banda:
            return self._aviso(j, "Las alianzas las propone el jefe, a otra banda que exista.")
        if m.get("romper"):
            self.alm.aliar(j.banda, otra["id"], False)
            self._a_banda(otra["id"], {"t": "aviso", "texto": "La banda %s rompe la alianza con la vuestra." % self.alm.banda(j.banda)["nombre"]})
            self._banda_difundir(j.banda)
            return self._banda_difundir(otra["id"])
        if self.propuestas_alianza.get(j.banda) == otra["id"]:   # ellos ya nos lo habían propuesto: hecho
            self.propuestas_alianza.pop(j.banda, None)
            self.alm.aliar(j.banda, otra["id"], True)
            for b in (j.banda, otra["id"]):
                self._a_banda(b, {"t": "aviso", "texto": "Alianza cerrada entre %s y %s." % (self.alm.banda(j.banda)["nombre"], otra["nombre"]), "son": "pareja"})
                self._banda_difundir(b)
            return
        self.propuestas_alianza[otra["id"]] = j.banda
        self._a_banda(otra["id"], {"t": "aviso", "texto": "La banda %s os propone una alianza. Si vuestro jefe se la propone a ellos, queda cerrada." % self.alm.banda(j.banda)["nombre"]})
        self._aviso(j, "Propuesta enviada a %s." % otra["nombre"])

    def _barrio_valido(self, mapa, barrio):
        return mapa in self.mundo["mapas"] and any(b["id"] == barrio for b in self.mundo["mapas"][mapa]["barrios"])

    def _m_barrio_reclamar(self, j, m):
        """Quedarse con el barrio en el que estás, si no es de nadie. Lo paga la caja."""
        if j.banda is None or j.rango not in ("jefe", "mano"):
            return self._aviso(j, "Los barrios los reclama el jefe o su mano derecha.")
        if not self._barrio_valido(j.mapa, j.barrio):
            return self._aviso(j, "Aquí no hay ningún barrio que reclamar.")
        if self.alm.territorio(j.mapa, j.barrio) is not None:
            return self._aviso(j, "Este barrio ya tiene dueño. Para quitárselo hay que declararle la guerra.")
        f = self.alm.banda(j.banda)
        mios = sum(1 for t in self.alm.territorios() if t["banda"] == j.banda)
        if mios >= len(self.alm.miembros(j.banda)) + 1:
            return self._aviso(j, "Con la gente que sois no podéis sostener más barrios. Hace falta más banda.")
        precio = int(self.cfg["precio_barrio"])
        if f["caja"] < precio:
            return self._aviso(j, "Reclamar un barrio cuesta %d euros de la caja, y hay %d." % (precio, f["caja"]))
        self.alm.apunte(j.banda, j.nombre, -precio, "reclamar un barrio")
        self.alm.poner_territorio(j.mapa, j.barrio, j.banda)
        self._a_todos({"t": "aviso", "texto": "La banda %s se queda con un barrio de %s." % (f["nombre"], self.mundo["mapas"][j.mapa]["nombre"]), "son": "territorio"})
        self._banda_difundir(j.banda)
        self._difundir_territorios()

    def _m_barrio_guerra(self, j, m):
        """Declarar la guerra por el barrio en el que estás. No empieza ya: se avisa y se pelea a una hora."""
        if j.banda is None or j.rango not in ("jefe", "mano"):
            return self._aviso(j, "La guerra la declara el jefe o su mano derecha.")
        t = self.alm.territorio(j.mapa, j.barrio) if self._barrio_valido(j.mapa, j.barrio) else None
        if t is None or t["banda"] == j.banda:
            return self._aviso(j, "Este barrio no es de otra banda.")
        if t["banda"] in self.alm.aliadas(j.banda):
            return self._aviso(j, "Ese barrio es de una banda aliada. Rompe antes la alianza.")
        if any(g["mapa"] == j.mapa and g["barrio"] == j.barrio for g in self.guerras):
            return self._aviso(j, "Ya hay una guerra declarada por este barrio.")
        f = self.alm.banda(j.banda)
        precio = int(self.cfg["precio_guerra"])
        if f["caja"] < precio:
            return self._aviso(j, "Declarar una guerra cuesta %d euros de la caja, y hay %d." % (precio, f["caja"]))
        self.alm.apunte(j.banda, j.nombre, -precio, "declarar una guerra")
        inicio = self.ahora() + 60 * int(self.cfg["guerra_espera"])
        g = {"mapa": j.mapa, "barrio": j.barrio, "ataca": j.banda, "defiende": t["banda"], "inicio": inicio,
             "fin": inicio + 60 * int(self.cfg["guerra_dura"]), "pa": 0, "pd": 0, "fase": "espera"}
        self.guerras.append(g)
        lugar = "%s, en %s" % (self._nombre_barrio(g), self.mundo["mapas"][g["mapa"]]["nombre"])
        for b, texto in ((g["defiende"], "¡%s os declara la guerra por %s! Empieza dentro de %d minutos y dura %d. Gana quien más gente tenga dentro del barrio y más rivales tumbe." % (f["nombre"], lugar, int(self.cfg["guerra_espera"]), int(self.cfg["guerra_dura"]))),
                         (g["ataca"], "Guerra declarada por %s. Empieza dentro de %d minutos y dura %d. Hay que estar dentro del barrio." % (lugar, int(self.cfg["guerra_espera"]), int(self.cfg["guerra_dura"])))):
            self._a_banda(b, {"t": "aviso", "texto": texto, "son": "sirena_lejana"})
        self._banda_difundir(j.banda)
        self._difundir_territorios()

    def _nombre_barrio(self, g):
        return next((b["nombre"] for b in self.mundo["mapas"][g["mapa"]]["barrios"] if b["id"] == g["barrio"]), g["barrio"])

    def _guerras_paso(self, dt):
        ahora = self.ahora()
        for g in list(self.guerras):
            if g["fase"] == "espera" and ahora >= g["inicio"]:
                g["fase"] = "lucha"
                for b in (g["ataca"], g["defiende"]):
                    self._a_banda(b, {"t": "aviso", "texto": "¡Empieza la guerra por %s! Todos al barrio." % self._nombre_barrio(g), "son": "sirena"})
                self._difundir_territorios()
            if g["fase"] != "lucha":
                continue
            for o in self.jugadores.values():                  # un punto por segundo y por cada uno que está dentro y en pie
                if o.dentro and o.mapa == g["mapa"] and o.barrio == g["barrio"] and o.salud > 0 and not o.pasivo:
                    if o.banda == g["ataca"]:
                        g["pa"] += dt
                    elif o.banda == g["defiende"]:
                        g["pd"] += dt
            if ahora >= g["fin"]:
                self._guerra_fin(g)
            elif int(g["fin"] - ahora) % 120 == 0:
                for b in (g["ataca"], g["defiende"]):
                    self._a_banda(b, {"t": "aviso", "texto": "Guerra por %s: atacantes %d puntos, defensores %d. Quedan %d minutos." % (
                        self._nombre_barrio(g), int(g["pa"]), int(g["pd"]), max(0, int((g["fin"] - ahora) // 60)))})

    def _guerra_baja(self, por, caido):
        for g in self.guerras:
            if g["fase"] == "lucha" and caido.mapa == g["mapa"] and caido.barrio == g["barrio"]:
                if por.banda == g["ataca"] and caido.banda == g["defiende"]:
                    g["pa"] += 30
                elif por.banda == g["defiende"] and caido.banda == g["ataca"]:
                    g["pd"] += 30

    def _guerra_fin(self, g):
        self.guerras.remove(g)
        ataca, defiende = self.alm.banda(g["ataca"]), self.alm.banda(g["defiende"])
        gana_ataque = g["pa"] > g["pd"] and ataca is not None
        nombre = self._nombre_barrio(g)
        if gana_ataque:
            self.alm.poner_territorio(g["mapa"], g["barrio"], g["ataca"])
        texto = "La guerra por %s ha terminado: %d a %d. %s" % (nombre, int(g["pa"]), int(g["pd"]),
                ("El barrio pasa a %s." % ataca["nombre"]) if gana_ataque else ("%s lo conserva." % (defiende["nombre"] if defiende else "Su dueño")))
        self._a_todos({"t": "aviso", "texto": texto, "son": "territorio"})
        for b in (g["ataca"], g["defiende"]):
            self._banda_difundir(b)
        self._difundir_territorios()

    # ========================================================= grupo de misión
    def _grupo(self, j):
        if j.grupo is None:
            return [j]
        return [o for o in self.jugadores.values() if o.dentro and o.grupo == j.grupo]

    def _grupo_difundir(self, lider):
        gente = [o for o in self.jugadores.values() if o.dentro and o.grupo == lider]
        if len(gente) < 2:
            for o in gente:
                o.grupo = None
                self._enviar(o, {"t": "grupo", "lider": None, "miembros": []})
            return
        for o in gente:
            self._enviar(o, {"t": "grupo", "lider": lider, "miembros": [{"id": x.id, "nombre": x.nombre} for x in gente]})

    def _m_grupo_invitar(self, j, m):
        o = self.jugadores.get(m.get("a"))
        if o is None or not o.dentro or o is j:
            return
        if j.grupo is not None and j.grupo != j.id:
            return self._aviso(j, "Vas en el grupo de otro: solo invita quien lo lleva.")
        if o.grupo is not None:
            return self._aviso(j, "%s ya va en un grupo." % o.nombre)
        if len(self._grupo(j)) >= 4:
            return self._aviso(j, "En un grupo caben cuatro.")
        self.invitaciones_grupo[o.id] = j.id
        self._enviar(o, {"t": "grupo_invita", "de": j.id, "nombre": j.nombre, "mision": str(m.get("mision", ""))[:80]})
        self._aviso(j, "Invitación enviada a %s." % o.nombre)

    def _m_grupo_resp(self, j, m):
        lider = self.jugadores.get(self.invitaciones_grupo.pop(j.id, None))
        if lider is None or not lider.dentro or j.grupo is not None or not m.get("si"):
            return
        lider.grupo = j.grupo = lider.id
        self._grupo_difundir(lider.id)
        for o in self._grupo(j):
            if o is not j:
                self._aviso(o, "%s se une al grupo." % j.nombre, "amigo_entra")

    def _grupo_salir(self, j, callar=False):
        lider = j.grupo
        if lider is None:
            return
        j.grupo = None
        if not callar and j.dentro:
            self._enviar(j, {"t": "grupo", "lider": None, "miembros": []})
        resto = [o for o in self.jugadores.values() if o.dentro and o.grupo == lider]
        if lider == j.id:                                      # se va quien lo llevaba: el grupo se deshace
            for o in resto:
                o.grupo = None
                self._enviar(o, {"t": "grupo", "lider": None, "miembros": []})
                self._aviso(o, "%s ha deshecho el grupo." % j.nombre)
        else:
            for o in resto:
                self._aviso(o, "%s deja el grupo." % j.nombre)
            self._grupo_difundir(lider)

    def _m_grupo_salir(self, j, m):
        self._grupo_salir(j)

    def _m_grupo_msg(self, j, m):
        """Lo que se cuentan entre sí los juegos de un grupo: los enemigos de la misión, los golpes y los pasos."""
        d = m.get("d")
        if j.grupo is None or not isinstance(d, dict) or len(json.dumps(d)) > 12000:
            return
        for o in self._grupo(j):
            if o is not j:
                self._enviar(o, {"t": "grupo_msg", "de": j.id, "nombre": j.nombre, "d": d})

    def _m_mision_hecha(self, j, m):
        """Quien lleva el grupo ha completado una misión: los que le ayudaban cobran su parte, una vez por misión."""
        mi = self.mundo["misiones"].get(m.get("id"))
        if mi is None or j.grupo != j.id:
            return
        parte = mi["dinero"] // 2
        for o in self._grupo(j):
            if o is j or o.mapa != j.mapa:
                continue
            clave = (j.cuenta, o.cuenta, m.get("id"))
            if clave in self.ayudas and not mi["repetible"]:
                self._aviso(o, "Misión completada: %s. Ya cobraste por ayudar en ella." % mi["titulo"], "mision_ok")
                continue
            self.ayudas.add(clave)
            self._enviar(o, {"t": "paga_mision", "titulo": mi["titulo"], "n": parte, "de": j.nombre})

    # ============================================================ administrar
    AYUDA_ORDENES = (
        ("ayuda", "dice todas las órdenes"),
        ("estado", "cómo está el servidor: puerto, cifrado, mundo, tiempo en marcha y cuánta gente hay"),
        ("jugadores", "quién está dentro y dónde"),
        ("cuentas", "todas las cuentas del servidor, con las vetadas y las que administran"),
        ("aviso texto", "dice algo a todos los que están dentro"),
        ("decir nombre: texto", "dice algo solo a un jugador"),
        ("expulsar nombre", "saca a un jugador; puede volver a entrar. Detrás de dos puntos se le puede decir el motivo"),
        ("vetar nombre", "saca a un jugador y no le deja volver"),
        ("perdonar nombre", "levanta el veto"),
        ("admin nombre", "hace administrador a un jugador"),
        ("quitaradmin nombre", "le quita la administración"),
        ("borrarcuenta nombre", "borra una cuenta con su personaje, sus propiedades y su sitio en la banda; no se puede deshacer"),
        ("invitar", "crea un código de invitación de un solo uso; con un número detrás, crea varios"),
        ("invitaciones", "las invitaciones que hay, libres y usadas"),
        ("anular código", "anula una invitación que aún no ha usado nadie"),
        ("mensaje texto", "cambia el mensaje del día; sin texto, lo quita"),
        ("hora número", "pone la hora del juego, de 0 a 23"),
        ("bandas", "las bandas, con su gente y su caja"),
        ("guardar", "guarda todo ahora"),
        ("copia", "hace una copia de seguridad"),
        ("copias", "las copias de seguridad que hay"),
        ("recargar", "vuelve a leer servidor.conf y aplica lo que se puede cambiar sin reiniciar"),
        ("apagar", "avisa a todos, lo guarda todo y para el servidor"),
    )

    def resumen(self):
        """Cómo está el servidor ahora mismo, para quien lo administra: el panel y la orden estado salen de aquí.
        No lleva nada personal: la dirección de cada jugador solo va si la opción registro_ip lo permite."""
        con_ip = si(self.cfg["registro_ip"])
        gente = []
        for j in self.jugadores.values():
            if j.dentro and not j.bot:
                gente.append({"id": j.id, "cuenta": j.cuenta, "nombre": j.nombre, "admin": bool(j.admin), "juego": j.juego,
                              "mapa": self.mundo["mapas"].get(j.mapa, {}).get("nombre") if j.mapa else None,
                              "fuera": bool(j.mapa is None and j.mapa_fuera), "mismo_mundo": j.huella == self.mundo.get("huella"),
                              "ip": j.ip if con_ip else None})
        return {"activo": self.activo, "nombre": self.cfg["nombre"], "puerto": getattr(self, "puerto", None), "cifrado": self.cifrado,
                "huella_cert": self.huella_cert, "mundo_version": self.mundo.get("version"), "mundo_huella": self.mundo.get("huella"),
                "localidades": len(self.mundo["mapas"]), "inicio": self.t_inicio, "max_jugadores": int(self.cfg["max_jugadores"]),
                "entrada": str(self.cfg["entrada"]), "personajes": len(self.bots), "protocolo": VERSION_RED,
                "jugadores": sorted(gente, key=lambda g: g["nombre"].lower())}

    def lista_cuentas(self):
        """Las cuentas, para administrarlas: nombre, si administra, si está vetada, cuándo se la vio y con qué versión."""
        dentro = {j.cuenta for j in self.jugadores.values() if j.dentro and not j.bot}
        return [{"id": f["id"], "nombre": f["nombre"], "admin": bool(f["admin"]), "vetado": bool(f["vetado"]), "visto": f["visto"], "creada": f["creada"],
                 "juego": f["juego"] or "", "dentro": f["id"] in dentro} for f in self.alm.lista_cuentas()]

    def lista_invitaciones(self):
        return [{"codigo": f["codigo"], "creada": f["creada"], "usada": f["usada_por"] is not None, "por": f["nombre"] or ""} for f in self.alm.invitaciones()]

    def aplicar_config(self, nueva):
        """Cambia la configuración con el servidor en marcha. Devuelve (opciones aplicadas, opciones que esperan al reinicio).
        Lo que no vale no se toca."""
        limpio, _ = opciones.validar(nueva, completar=False)
        al_momento, con_reinicio = opciones.cambios(self.cfg, dict(self.cfg, **limpio))
        for clave in al_momento:
            self.cfg[clave] = limpio[clave]
        if "admins" in al_momento:                             # quien administra por la lista, lo sabe ya
            admins = self._nombres("admins")
            for j in self.jugadores.values():
                if j.dentro and not j.bot and j.cuenta is not None:
                    fila = self.alm.cuenta(j.cuenta)
                    j.admin = bool(fila and fila["admin"]) or j.nombre.lower() in admins
        if "vetados" in al_momento:
            vetados = self._nombres("vetados")
            for j in list(self.jugadores.values()):
                if j.dentro and not j.bot and j.nombre.lower() in vetados:
                    self._echar(j, "Un administrador te ha sacado del servidor.")
        return al_momento, con_reinicio

    def _tiempo_en_marcha(self):
        if not self.t_inicio:
            return "parado"
        s = int(max(0, time.time() - self.t_inicio))
        d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
        partes = (["%d %s" % (d, "día" if d == 1 else "días")] if d else []) + (["%d %s" % (h, "hora" if h == 1 else "horas")] if h else [])
        return ", ".join(partes + ["%d %s" % (m, "minuto" if m == 1 else "minutos")])

    def orden(self, texto, quien="consola"):
        """Órdenes de administración: desde la consola del servidor, desde el panel, o desde el chat con una barra delante."""
        partes = texto.strip().split(None, 1)
        if not partes:
            return ""
        que, resto = partes[0].lower(), (partes[1].strip() if len(partes) > 1 else "")
        dentro = [j for j in self.jugadores.values() if j.dentro and not j.bot]

        def buscar(nombre):
            return next((j for j in dentro if j.nombre.lower() == nombre.lower()), None)
        if quien != "consola" and que not in ("ayuda", "?", "jugadores", "estado"):
            self.log("%s da la orden %s." % (quien, que))
        if que in ("ayuda", "?"):
            if quien != "consola":                              # por el chat, corto: se oye, no se lee
                return "Órdenes: " + ", ".join(o for o, _ in self.AYUDA_ORDENES) + "."
            return "Órdenes:\n" + "\n".join("  %s: %s." % o for o in self.AYUDA_ORDENES)
        if que == "estado":
            r = self.resumen()
            tope = r["max_jugadores"]
            return ("Servidor «%s», en marcha desde hace %s. Puerto %s, %s. Mundo de la versión %s, huella %s, con %d localidades. "
                    "Hay %d %s%s y %d personajes del servidor." % (
                        r["nombre"], self._tiempo_en_marcha(), r["puerto"], "con cifrado" if r["cifrado"] else "sin cifrado", r["mundo_version"],
                        r["mundo_huella"], r["localidades"], len(dentro), "jugador" if len(dentro) == 1 else "jugadores",
                        (" de %d" % tope) if tope > 0 else ", sin límite", r["personajes"]))
        if que == "jugadores":
            return ("Hay %d: " % len(dentro)) + ", ".join("%s en %s" % (j.nombre, self.mundo["mapas"].get(j.mapa, {}).get("nombre", "sin situar")) for j in dentro) if dentro else "No hay nadie."
        if que == "cuentas":
            cs = self.lista_cuentas()
            if not cs:
                return "Todavía no hay ninguna cuenta."
            return ("Hay %d: " % len(cs)) + ", ".join(c["nombre"] + (" (administra)" if c["admin"] else "") + (" (vetada)" if c["vetado"] else "")
                                                       + (" (dentro)" if c["dentro"] else "") for c in cs) + "."
        if que == "aviso" and resto:
            self._a_todos({"t": "aviso", "texto": "Aviso del servidor: " + resto[:300], "son": "notificacion"})
            return "Aviso enviado."
        if que == "decir" and resto:
            nombre, _, dicho = resto.partition(":")
            j = buscar(nombre.strip())
            if j is None or not dicho.strip():
                return "Escribe decir, el nombre de alguien que esté dentro, dos puntos y el mensaje."
            self._aviso(j, "Quien administra el servidor te dice: " + dicho.strip()[:300], "notificacion")
            return "Dicho a %s." % j.nombre
        if que in ("expulsar", "vetar") and resto:
            nombre, _, motivo = resto.partition(":")
            nombre = nombre.strip()
            j = buscar(nombre)
            fila = self.alm.cuenta_por_nombre(nombre)
            if fila is None:
                return "No hay nadie con ese nombre."
            if que == "vetar":
                self.alm.poner(fila["id"], vetado=1)
                self.alm.guardar()
            if j is not None:
                self._echar(j, "Un administrador te ha sacado del servidor." + ((" Motivo: " + motivo.strip()[:200]) if motivo.strip() else ""))
            elif que == "expulsar":
                return "%s no está dentro ahora mismo." % fila["nombre"]
            return "%s, %s." % (fila["nombre"], "vetado: no podrá volver a entrar" if que == "vetar" else "expulsado")
        if que == "perdonar" and resto:
            fila = self.alm.cuenta_por_nombre(resto)
            if fila is None:
                return "No hay nadie con ese nombre."
            self.alm.poner(fila["id"], vetado=0)
            self.alm.guardar()
            return "%s puede volver a entrar." % fila["nombre"]
        if que in ("admin", "quitaradmin") and resto:
            fila = self.alm.cuenta_por_nombre(resto)
            if fila is None:
                return "No hay nadie con ese nombre."
            pone = que == "admin"
            self.alm.poner(fila["id"], admin=int(pone))
            self.alm.guardar()
            j = buscar(resto)
            por_lista = fila["nombre"].lower() in self._nombres("admins")
            if j is not None:
                j.admin = pone or por_lista
            if not pone and por_lista:
                return "%s sigue administrando porque está en la lista de administradores de la configuración. Quítalo también de ahí." % fila["nombre"]
            return ("%s ya es administrador." if pone else "%s ya no administra.") % fila["nombre"]
        if que == "borrarcuenta" and resto:
            fila = self.alm.cuenta_por_nombre(resto)
            if fila is None:
                return "No hay nadie con ese nombre."
            mi = self.alm.miembro(fila["id"])
            if mi is not None and mi["rango"] == "jefe" and len(self.alm.miembros(mi["banda"])) > 1:
                return "%s es jefe de una banda con más gente. Antes tiene que ceder el mando o disolverla." % fila["nombre"]
            j = buscar(fila["nombre"])
            if j is not None:
                self._salida(j, callar=True)
                self._echar(j, "Un administrador ha borrado tu cuenta de este servidor.")
                self._a_todos({"t": "sale", "id": j.id})
            if mi is not None:                                 # era el único de su banda: la banda se va con él
                self._fuera_de_banda(fila["id"])
                if not self.alm.miembros(mi["banda"]):
                    self._disolver(mi["banda"])
                else:
                    self._banda_difundir(mi["banda"])
            suyas = [f["lugar"] for f in self.alm.propiedades() if f["cuenta"] == fila["id"]]
            for v in [v for v in self.vehiculos.values() if v.get("dueno") == fila["id"] and v["por"] is None]:
                self._quitar_vehiculo(v["id"])
            self.alm.borrar_cuenta(fila["id"])
            for lugar in suyas:                                # lo que tenía vuelve a estar en venta
                self._prop_difundir(lugar, antes=fila["id"])
            return "Cuenta de %s borrada, con su personaje y sus propiedades." % fila["nombre"]
        if que == "invitar":
            try:
                n = max(1, min(50, int(resto))) if resto else 1
            except ValueError:
                return "Detrás de invitar, si pones algo, tiene que ser cuántos códigos quieres: de 1 a 50."
            codigos = []
            for _ in range(n):
                codigo = secrets.token_hex(4).upper()
                self.alm.crear_invitacion(codigo)
                codigos.append(codigo)
            if n == 1:
                return "Código de invitación, de un solo uso: %s" % codigos[0]
            return "Códigos de invitación, de un solo uso cada uno: %s" % ", ".join(codigos)
        if que == "invitaciones":
            inv = self.lista_invitaciones()
            if not inv:
                return "No hay ninguna invitación. Se crean con la orden invitar."
            return "; ".join("%s, %s" % (i["codigo"], ("usada por " + (i["por"] or "una cuenta que ya no existe")) if i["usada"] else "libre") for i in inv) + "."
        if que == "anular" and resto:
            return "Invitación anulada." if self.alm.borrar_invitacion(resto.strip().upper()) else "No hay ninguna invitación libre con ese código."
        if que == "mensaje":
            valor, error = opciones.validar_valor("mensaje_dia", resto)
            if error:
                return "El mensaje del día " + error + "."
            self.cfg["mensaje_dia"] = valor
            if valor:
                self._a_todos({"t": "aviso", "texto": "Mensaje del día: " + valor, "son": "notificacion"})
                return "Mensaje del día cambiado, hasta que el servidor se reinicie. Para dejarlo fijo, ponlo en la configuración."
            return "Mensaje del día quitado."
        if que == "hora" and resto:
            try:
                self.reloj = (finito(resto.replace(",", ".")) % 24) * 60
            except ValueError:
                return "Dime la hora con un número, de 0 a 23."
            self._a_todos({"t": "hora", "h": self._hora()})
            return "Hora cambiada."
        if que == "bandas":
            bs = self.alm.bandas()
            return "; ".join("%s, %d miembros, %d euros" % (b["nombre"], len(self.alm.miembros(b["id"])), b["caja"]) for b in bs) if bs else "No hay bandas."
        if que == "guardar":
            self.guardar_todo()
            self._t_guardado = time.monotonic()
            return "Guardado."
        if que == "copia":
            try:
                return "Copia hecha en %s" % self.copia_seguridad()
            except Exception as e:
                return "No se ha podido hacer la copia: %s: %s" % (type(e).__name__, e)
        if que == "copias":
            lista = copias.listar(self.cfg["datos"])
            if not lista:
                return "No hay ninguna copia de seguridad."
            return ("Hay %d, la más nueva primero: " % len(lista)) + ", ".join(os.path.basename(c[0]) for c in lista[:30]) + "."
        if que == "recargar":
            if not self.ruta_conf or not os.path.exists(self.ruta_conf):
                return "Este servidor no se arrancó con un archivo de configuración: no hay nada que recargar."
            nueva, avisos = opciones.leer(self.ruta_conf)
            al_momento, con_reinicio = self.aplicar_config(nueva)
            nombre = lambda c: opciones.POR_CLAVE[c].etiqueta
            return " ".join(avisos + [
                ("Aplicado: %s." % ", ".join(nombre(c) for c in al_momento)) if al_momento else "No había nada que aplicar al momento.",
                ("Esperan a que reinicies el servidor: %s." % ", ".join(nombre(c) for c in con_reinicio)) if con_reinicio else ""]).strip()
        if que == "apagar":
            asyncio.get_event_loop().create_task(self.detener("Un administrador ha apagado el servidor."))
            return "Apagando."
        uso = next((o for o in self.AYUDA_ORDENES if o[0].split()[0] == que), None)
        if uso is not None:                                    # la orden existe, pero le falta el nombre, el texto o el número
            return "A esa orden le falta algo. Se escribe así: %s. Sirve para esto: %s." % uso
        return "No conozco esa orden. Escribe ayuda."
