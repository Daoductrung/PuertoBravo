"""Prueba el servidor en línea de verdad: lo arranca como un programa aparte y le mete diez jugadores por la red.

    .venv\\Scripts\\python.exe herramientas\\prueba_servidor_real.py
    .venv\\Scripts\\python.exe herramientas\\prueba_servidor_real.py --exe dist\\PuertoBravo\\PuertoBravoServidor.exe

Sin opciones arranca el servidor del código fuente (python -m servidor). Con --exe arranca el ejecutable compilado. En
los dos casos trabaja en una carpeta temporal, con su propio servidor.conf, sus propios datos y un puerto libre: no
toca el servidor.conf ni los datos de nadie, y al terminar borra la carpeta y no deja ningún programa en marcha.

Lo que hace:
  1. Arranca el servidor y espera a que escuche, cifrando.
  2. Conecta diez jugadores, cada uno en su hilo y con la conexión cifrada, con el mismo código de red que usa el
     juego. Juegan un rato: se mueven, hablan por los canales, fundan dos bandas y entran en ellas, meten dinero en la
     caja, compran una casa o un negocio cada uno, cogen y dejan un vehículo, se pelean, guardan, salen y vuelven a entrar.
  3. Mientras tanto le da órdenes al servidor por su entrada, como quien lo lleva desde la consola: estado, jugadores,
     aviso, copia, cuentas, bandas y guardar.
  4. Lo apaga con orden (apagar) con los diez dentro y mira que sale con código 0 y que todo quedó guardado.
  5. Lo arranca otra vez sobre los mismos datos, los diez vuelven a entrar y comprueban que siguen siendo quienes eran,
     y lo para con la otra forma de parar: --parar.
  6. Repasa lo que ha dicho el servidor y su registro en disco: no puede haber ni un error.

Termina con un resumen y con código de salida 0 solo si todo ha ido bien.
"""
import argparse
import atexit
import hashlib
import json
import math
import os
import queue
import random
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

NOMBRES = ["Ana", "Blas", "Ciro", "Dora", "Eva", "Fede", "Gala", "Hugo", "Ines", "Juan"]
MALAS_SENALES = ("Error ", "Traceback", "no se ha podido atender", "No se ha podido", "no se le reconocen", "demasiados mensajes", "Exception")


class Informe:
    """Lo que se va comprobando, para decirlo todo junto al final."""

    def __init__(self):
        self.lineas = []
        self.fallos = 0
        self.candado = threading.Lock()

    def comprobar(self, bien, texto, detalle=""):
        with self.candado:
            if not bien:
                self.fallos += 1
            linea = "%s  %s%s" % ("BIEN" if bien else "MAL ", texto, (" -> " + str(detalle)[:400]) if (detalle and not bien) else "")
            self.lineas.append(linea)
            print(linea, flush=True)
        return bool(bien)

    def nota(self, texto):
        with self.candado:
            self.lineas.append("      " + texto)
            print("      " + texto, flush=True)


class ServidorReal:
    """El servidor, como programa aparte. Se le habla por su entrada y se lee lo que va diciendo."""

    def __init__(self, orden, carpeta, conf):
        self.orden_arranque, self.carpeta, self.conf = orden, carpeta, conf
        self.proceso = None
        self.dicho = []                                          # todo lo que ha dicho, línea a línea
        self.candado = threading.Lock()

    def arrancar(self):
        entorno = dict(os.environ, PYTHONPATH=RAIZ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.proceso = subprocess.Popen(self.orden_arranque + [self.conf], cwd=self.carpeta, env=entorno, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
        threading.Thread(target=self._leer, args=(self.proceso,), daemon=True).start()

    def _leer(self, proceso):
        for cruda in iter(proceso.stdout.readline, b""):
            try:
                linea = cruda.decode("utf-8")
            except UnicodeDecodeError:
                linea = cruda.decode("cp1252", "replace")
            with self.candado:
                self.dicho.append(linea.rstrip("\r\n"))

    def lineas(self, desde=0):
        with self.candado:
            return list(self.dicho[desde:])

    def esperar(self, trozo, segundos=30.0, desde=0):
        """La primera línea, de las dichas desde cierto punto, que contiene un texto. None si no llega a tiempo."""
        fin = time.time() + segundos
        while time.time() < fin:
            for linea in self.lineas(desde):
                if trozo in linea:
                    return linea
            if self.proceso.poll() is not None:
                break
            time.sleep(0.05)
        for linea in self.lineas(desde):
            if trozo in linea:
                return linea
        return None

    def orden(self, texto, espera, segundos=15.0):
        """Escribe una orden en la entrada del servidor y devuelve la línea de la respuesta que contiene lo esperado."""
        desde = len(self.lineas())
        try:
            self.proceso.stdin.write((texto + "\n").encode("utf-8"))
            self.proceso.stdin.flush()
        except OSError:
            return None
        return self.esperar(espera, segundos, desde)

    def esperar_salida(self, segundos=30.0):
        try:
            return self.proceso.wait(segundos)
        except subprocess.TimeoutExpired:
            return None

    def matar(self):
        if self.proceso is not None and self.proceso.poll() is None:
            try:
                self.proceso.kill()
                self.proceso.wait(10)
            except Exception:
                pass


class Jugador(threading.Thread):
    """Un jugador en su hilo, con la conexión del juego de verdad. Lleva sus cuentas como el juego: resta lo que el
    servidor le cobra y suma lo que le da."""

    def __init__(self, k, total, puerto, huella, mundo, sitio, segundos, cert, solo_volver=None):
        super().__init__(daemon=True, name="jugador-%d" % k)
        self.k, self.total, self.puerto, self.huella, self.sitio, self.segundos, self.cert = k, total, puerto, huella, sitio, segundos, cert
        self.nombre = NOMBRES[k % len(NOMBRES)] + ("" if k < len(NOMBRES) else str(k))
        self.semilla = hashlib.sha256(("identidad de la prueba del servidor real|" + self.nombre).encode("utf-8")).digest()
        self.rng = random.Random(1000 + k)
        self.cli = None
        self.ok = None
        self.error = None
        self.hechos = []                                         # (bien, texto, detalle)
        self.ids, self.vistos = {}, {}
        self.conocidos = set()                                   # los demás jugadores que ha tenido delante, se hayan ido o no
        self.situados = 0                                        # de cuántos de ellos le ha llegado la posición
        self.avisos, self.chats = [], {}
        self.banda = None
        self.dinero, self.dano, self.atacante = 80000, 0.0, None
        self.quitas = self.impactos = self.caidas = self.bajas = 0
        self.vid = self.veh = None
        self.guardado = self.cerrado = self.desconectado = self.expulsado = None
        self.rechazo_compra = False
        self.comprada = False                                    # si ha llegado a comprar su casa o su negocio
        self.x, self.y = sitio[0] + 3.0 * (k % 5), sitio[1] + 4.0 * (k // 5)
        self.rumbo = self.rng.uniform(0, 360)
        self.partida = solo_volver["partida"] if solo_volver else None
        self.saldo_final = solo_volver["saldo"] if solo_volver else None
        self.solo_volver = solo_volver is not None
        casas = sorted((l for l in mundo["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] in ("casa", "negocio") and l["precio"] > 0), key=lambda l: (l["precio"], l["id"]))
        self.casa = casas[k] if k < len(casas) else None
        self.jefe = k in (0, total // 2)
        self.equipo = 0 if k < total // 2 else 1
        self.dentro = threading.Event()
        self.fuera = threading.Event()
        self.vuelto = threading.Event()
        self.parar = threading.Event()

    # ------------------------------------------------------------------ red
    def conectar(self):
        from juego import enlinea
        self.cli = enlinea.ClienteServidor()
        ok, r = self.cli.conectar_servidor("127.0.0.1", self.puerto, self.nombre, self.semilla, self.huella, huella_cert=self.cert, timeout=15)
        if not ok:
            raise RuntimeError("no entra: %s" % r)
        self.ok = r
        self.ids = {q["nombre"]: q["id"] for q in r.get("jugadores", []) if not q.get("ia")}
        self.conocidos = set(self.ids.values())
        self.banda = r.get("banda")
        return r

    def estado(self, **mas):
        e = {"m": "puerto_bravo", "x": round(self.x, 1), "y": round(self.y, 1), "r": round(self.rumbo), "v": self.veh, "s": 8.0 if self.veh else 0.0,
             "sa": max(1, round(100 - self.dano, 1)), "di": int(self.dinero), "ba": 0, "ar": "pistola", "b": "puerto", "ag": 0, "in": 0, "es": 0, "po": [],
             "vi": self.vid}
        e.update(mas)
        self.cli.enviar({"t": "estado", "e": e})

    def atender(self):
        """Todo lo que ha llegado desde la última vez."""
        while True:
            try:
                m = self.cli.entrantes.get_nowait()
            except queue.Empty:
                return
            t = m.get("t")
            if t == "estados":
                for ident, e in (m.get("e") or {}).items():
                    self.vistos[int(ident)] = (e.get("m"), e.get("x"), e.get("y"))
            elif t == "entra":
                if not m.get("ia"):
                    self.ids[m["nombre"]] = m["id"]
                    self.conocidos.add(m["id"])
            elif t == "sale":
                self.ids = {n: i for n, i in self.ids.items() if i != m.get("id")}
            elif t == "aviso":
                self.avisos.append(str(m.get("texto", "")))
            elif t == "chat":
                self.chats[m.get("canal")] = self.chats.get(m.get("canal"), 0) + 1
            elif t == "banda_invita":
                self.cli.enviar({"t": "banda_resp", "si": True})
            elif t == "banda":
                self.banda = m.get("b")
            elif t == "cobro":
                self.dinero -= min(self.dinero, int(m.get("n", 0)))
            elif t in ("dinero", "paga_mision"):
                self.dinero += int(m.get("n", 0))
            elif t in ("baja", "atraco_ok", "robo_fin"):
                self.dinero += int(m.get("botin", 0))
                self.bajas += 1 if t == "baja" else 0
            elif t in ("caes", "atracado"):
                self.dinero -= min(self.dinero, int(m.get("pierde", 0)))
            elif t == "saldo":
                self.dinero -= min(self.dinero, int(m.get("quita", 0)))
                self.quitas += int(m.get("quita", 0))
            elif t == "herido":
                self.dano += float(m.get("dano", 0))
                self.atacante = m.get("de")
            elif t == "impacto":
                self.impactos += 1
            elif t == "prop_no":
                if self.casa is not None and m.get("lugar") == self.casa["id"] and not self.rechazo_compra:
                    self.rechazo_compra = True
                    self.dinero += self.casa["precio"]            # el juego devuelve lo pagado
            elif t == "veh_tuyo":
                self.vid = m.get("id")
            elif t == "sacado":
                self.vid = self.veh = None
            elif t == "guardado":
                self.guardado = True
            elif t == "cerrado":
                self.cerrado = str(m.get("motivo", ""))
            elif t == "expulsado":
                self.expulsado = str(m.get("motivo", ""))
            elif t == "desconectado":
                self.desconectado = True

    def sincronizar(self, segundos=8.0):
        """Espera a que el servidor haya atendido todo lo enviado: manda la posición y espera a que conteste a otra cosa."""
        self.estado()
        self.guardado = None
        self.cli.enviar({"t": "guardar", "p": self.partida, "ya": True}) if self.partida is not None else self.cli.enviar({"t": "ping"})
        fin = time.time() + segundos
        while time.time() < fin and self.partida is not None and not self.guardado and not self.desconectado:
            self.atender()
            time.sleep(0.02)
        self.atender()
        return bool(self.guardado) or self.partida is None

    # ---------------------------------------------------------------- la vida
    def run(self):
        try:
            if not self.solo_volver:
                self.conectar()
                self.dentro.set()
                self.jugar()
                self.guardar_y_salir()
                self.fuera.set()
                time.sleep(1.0)
            self.volver()
            self.vuelto.set()
            self.dentro.set()
            self.quedarse()
        except Exception:
            self.error = traceback.format_exc()
        finally:
            self.dentro.set()
            self.fuera.set()
            self.vuelto.set()
            try:
                if self.cli is not None:
                    self.cli.cerrar()
            except Exception:
                pass

    def andar(self, dt):
        vel = 8.0 if self.veh else 2.5
        if self.rng.random() < 0.05:
            self.rumbo = self.rng.uniform(0, 360)
        self.x += math.sin(math.radians(self.rumbo)) * vel * dt
        self.y += math.cos(math.radians(self.rumbo)) * vel * dt
        x0, y0 = self.sitio
        if not (x0 - 5 < self.x < x0 + 30 and y0 - 5 < self.y < y0 + 25):
            self.x, self.y = min(x0 + 30, max(x0 - 5, self.x)), min(y0 + 25, max(y0 - 5, self.y))
            self.rumbo = math.degrees(math.atan2(x0 + 12 - self.x, y0 + 10 - self.y)) % 360

    def jugar(self):
        hecho = set()
        inicio = time.time()
        t_ataque = t_invitar = t_ping = 0.0
        rival = NOMBRES[(self.k + self.total // 2) % self.total]
        mios = [NOMBRES[i] for i in range(self.total) if (0 if i < self.total // 2 else 1) == self.equipo and i != self.k]

        def una_vez(clave, cuando):
            if t >= cuando and clave not in hecho:
                hecho.add(clave)
                return True
            return False
        while True:
            t = time.time() - inicio
            if t >= self.segundos or self.desconectado or self.expulsado or self.cerrado:
                break
            self.atender()
            self.andar(0.1)
            self.estado()
            enviar = self.cli.enviar
            if una_vez("aspecto", 1.0):
                enviar({"t": "aspecto", "texto": "ropa de calle, con gafas de sol"})
            if una_vez("todos", 2.0):
                enviar({"t": "chat", "texto": "hola, soy %s" % self.nombre})
            if self.jefe and una_vez("fundar", 3.0):
                enviar({"t": "banda_crear", "nombre": "Los Linces" if self.equipo == 0 else "Los Zorros"})
            if self.jefe and self.banda and t - t_invitar > 1.0 and t < self.segundos - 4:      # invita a los suyos hasta que estén todos
                t_invitar = t
                dentro = {q["nombre"] for q in self.banda.get("miembros", [])}
                for n in mios:
                    if n not in dentro and n in self.ids:
                        enviar({"t": "banda_invitar", "a": self.ids[n]})
            if self.banda and una_vez("caja", 5.0):
                enviar({"t": "banda_ingresar", "n": 500})
                enviar({"t": "chat", "texto": "ya estoy en la banda", "canal": "banda"})
            if una_vez("cerca", 5.0):
                enviar({"t": "chat", "texto": "¿alguien por aquí?", "canal": "cerca"})
                otro = NOMBRES[(self.k + 1) % self.total]
                if otro in self.ids:
                    enviar({"t": "chat", "texto": "solo para ti", "canal": "priv", "a": self.ids[otro]})
            if self.casa is not None and una_vez("comprar", 6.0) and self.dinero >= self.casa["precio"] + 3000:
                self.dinero -= self.casa["precio"]               # el juego paga y se lo dice al servidor
                self.comprada = True
                enviar({"t": "prop_comprar", "lugar": self.casa["id"]})
            if una_vez("subir", 7.0):
                self.veh = "sedan"
                enviar({"t": "veh_tomar", "modelo": "sedan", "nombre": "Sedán de " + self.nombre, "ref": self.k})
            if una_vez("bajar", 12.0):
                if self.vid is not None:
                    enviar({"t": "veh_dejar", "id": self.vid, "x": round(self.x, 1), "y": round(self.y, 1), "r": 0, "salud": 80})
                self.vid = self.veh = None
            if 9.0 <= t < self.segundos - 4 and t - t_ataque >= 0.6 and rival in self.ids:        # la pelea, con el de la otra banda
                t_ataque = t
                enviar({"t": "ataque", "a": self.ids[rival], "arma": "pistola"})
                enviar({"t": "evento", "que": "d:pistola"})
            if self.dano >= 100:                                 # ha caído: lo dice y se levanta
                self.estado(sa=0)
                if self.atacante is not None:
                    enviar({"t": "caido", "por": self.atacante})
                self.dano, self.atacante = 0.0, None
                self.caidas += 1
            if t - t_ping > 5.0:
                t_ping = t
                enviar({"t": "ping"})
                enviar({"t": "quien"})
            time.sleep(0.1)
        self.situados = len(self.conocidos & set(self.vistos))

    def guardar_y_salir(self):
        if self.vid is not None:
            self.cli.enviar({"t": "veh_dejar", "id": self.vid, "x": round(self.x, 1), "y": round(self.y, 1), "r": 0, "salud": 80})
            self.vid = self.veh = None
        time.sleep(0.5)
        self.atender()
        self.dano = 0.0
        for intento in range(3):                                 # guarda cuando las cuentas están quietas
            antes = self.dinero
            self.partida = {"jugador": {"nombre": self.nombre, "dinero": int(self.dinero), "banco": 0, "ropa": "ropa de calle",
                                        "accesorios": {"gafas": "Gafas de sol"}, "propiedades": [self.casa["id"]] if self.casa and self.comprada and not self.rechazo_compra else []},
                            "dia": 1, "prueba": "servidor real, jugador %d" % self.k}
            llego = self.sincronizar()
            if llego and self.dinero == antes:
                break
        self.hechos.append((bool(self.guardado), "%s guarda y el servidor se lo confirma" % self.nombre, ""))
        self.saldo_final = int(self.dinero)
        self.cli.cerrar()

    def volver(self):
        r = self.conectar()
        n = self.nombre
        self.hechos.append((self.cli.cifrado, "%s vuelve a entrar, con la conexión cifrada" % n, ""))
        self.hechos.append((r.get("partida") == self.partida, "%s recupera su personaje tal como lo guardó" % n, (r.get("partida"), self.partida)))
        self.hechos.append((r.get("saldo") == self.saldo_final, "%s tiene el dinero que tenía: %s euros" % (n, self.saldo_final), (r.get("saldo"), self.saldo_final)))
        banda = (r.get("banda") or {}).get("nombre")
        self.hechos.append((banda == ("Los Linces" if self.equipo == 0 else "Los Zorros"), "%s sigue en su banda" % n, banda))
        if self.casa is not None and self.partida["jugador"]["propiedades"]:
            suya = (r.get("props") or {}).get(self.casa["id"]) or {}
            self.hechos.append((suya.get("cuenta") == r.get("cuenta"), "%s sigue siendo el dueño de %s" % (n, self.casa["nombre"]), suya))
        self.dinero = int(r.get("saldo") or self.dinero)

    def quedarse(self):
        """Dentro, sin hacer nada más que estar, hasta que el servidor se cierre o le digan que pare."""
        t_ping = time.time()
        while not self.parar.is_set() and not self.cerrado and not self.desconectado and not self.expulsado:
            self.atender()
            self.andar(0.1)
            self.estado()
            if time.time() - t_ping > 5:
                t_ping = time.time()
                self.cli.enviar({"t": "ping"})
            time.sleep(0.1)
        fin = time.time() + 2.0
        while time.time() < fin and not self.cerrado and not self.desconectado:
            self.atender()
            time.sleep(0.05)
        self.atender()


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def lejos_de_todo(mundo):
    """Un punto de Puerto Bravo fuera de las zonas seguras, para que las peleas cuenten."""
    seguras = [(l["x"], l["y"]) for l in mundo["mapas"]["puerto_bravo"]["lugares"] if l["tipo"] in ("hospital", "comisaria", "casa", "ong", "protectora")]
    for x in range(60, 800, 37):
        for y in range(60, 600, 41):
            if all((x - a) ** 2 + (y - b) ** 2 > 80 ** 2 for a, b in seguras):
                return float(x), float(y)
    return 100.0, 100.0


def escribir_conf(ruta, datos, puerto, jugadores):
    lineas = ["# servidor.conf de la prueba del servidor real: se borra al terminar",
              "nombre = Servidor de la prueba real", "puerto = %d" % puerto, "interfaz = 127.0.0.1", "datos = %s" % datos, "cifrado = si",
              "max_jugadores = %d" % jugadores, "registro_archivo = si", "saldo_inicial = 80000", "proteccion = 5", "bienvenida = Bienvenido a la prueba.",
              "mensaje_dia = Hoy se prueba el servidor."]
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")


def malas(lineas):
    return [l for l in lineas if any(s in l for s in MALAS_SENALES)]


def main():
    ap = argparse.ArgumentParser(description="Prueba el servidor en línea de verdad, como programa aparte, con diez jugadores por la red.")
    ap.add_argument("--exe", help="ruta de PuertoBravoServidor.exe; sin esto se prueba el servidor del código fuente")
    ap.add_argument("--python", help="el Python con el que arrancar el servidor del código fuente; de serie, el del entorno del proyecto")
    ap.add_argument("--jugadores", type=int, default=10, help="cuántos jugadores, de 4 a 10 (de serie, 10)")
    ap.add_argument("--segundos", type=float, default=24.0, help="cuánto juegan antes de guardar y salir (de serie, 24)")
    ap.add_argument("--conservar", action="store_true", help="no borra la carpeta temporal al terminar, para mirarla")
    args = ap.parse_args()
    n = max(4, min(10, args.jugadores))
    inf = Informe()
    if args.exe:
        exe = os.path.abspath(args.exe)
        if not os.path.isfile(exe):
            print("No existe el ejecutable %s" % exe)
            return 2
        orden = [exe]
        que = "el ejecutable %s" % exe
    else:
        py = args.python or os.path.join(RAIZ, ".venv", "Scripts", "python.exe")
        if not os.path.isfile(py):
            py = sys.executable
        orden = [py, "-m", "servidor"]
        que = "el servidor del código fuente, con %s" % py
    from juego import enlinea
    mundo = enlinea.mundo_servidor()
    huella = mundo["huella"]
    sitio = lejos_de_todo(mundo)
    carpeta = tempfile.mkdtemp(prefix="pb_servidor_real_")
    datos = os.path.join(carpeta, "datos")
    conf = os.path.join(carpeta, "servidor.conf")
    puerto = puerto_libre()
    escribir_conf(conf, datos, puerto, n)
    srv = ServidorReal(orden, carpeta, conf)
    atexit.register(srv.matar)
    jugadores = []
    print("Se prueba %s, en %s, puerto %d, con %d jugadores." % (que, carpeta, puerto, n), flush=True)
    try:
        # ------------------------------------------------------------ primer arranque
        srv.arrancar()
        escucha = srv.esperar("escuchando en el puerto", 90)
        if not inf.comprobar(escucha is not None, "El servidor arranca y escucha", srv.lineas()[-5:]):
            raise RuntimeError("el servidor no arranca")
        inf.comprobar("con cifrado" in escucha, "Cifra la conexión", escucha)
        del_mundo = srv.esperar("Datos del mundo", 10) or ""
        inf.comprobar("huella %s" % huella in del_mundo, "Trae el mundo de esta versión del juego", del_mundo)
        linea_cert = srv.esperar("Huella del certificado:", 10) or ""
        cert = linea_cert.split("Huella del certificado:")[-1].strip()
        inf.comprobar(len(cert) == 64, "Dice la huella de su certificado", linea_cert)
        inf.comprobar(srv.esperar("Escribe ayuda", 10) is not None, "Queda a la espera de órdenes")
        jugadores = [Jugador(k, n, puerto, huella, mundo, sitio, args.segundos, cert) for k in range(n)]
        t0 = time.time()
        for j in jugadores:
            j.start()
            time.sleep(0.15)
        for j in jugadores:
            j.dentro.wait(60)
        entrados = [j for j in jugadores if j.ok is not None and j.error is None]
        inf.comprobar(len(entrados) == n, "Entran los %d jugadores, cada uno en su hilo" % n, [j.error for j in jugadores if j.error])
        inf.comprobar(all(j.cli is not None and j.cli.cifrado and j.cli.huella_cert == cert for j in entrados), "Todos entran cifrados, con el certificado del servidor")
        inf.comprobar(all(j.ok["servidor"]["bienvenida"] == "Bienvenido a la prueba." for j in entrados), "A todos les llega la bienvenida de la configuración")
        r = srv.orden("estado", "en marcha desde hace")
        inf.comprobar(r is not None and "Hay %d jugadores de %d" % (n, n) in r, "Orden estado: dice que hay %d jugadores" % n, r)
        r = srv.orden("jugadores", "Hay ")
        inf.comprobar(r is not None and ("Hay %d:" % n) in r and all(j.nombre in r for j in jugadores), "Orden jugadores: los nombra a todos", r)
        time.sleep(max(0.0, 8.0 - (time.time() - t0)))
        r = srv.orden("aviso Prueba de diez jugadores en marcha", "Aviso enviado")
        inf.comprobar(r is not None, "Orden aviso: el servidor la acepta", r)
        time.sleep(1.0)
        r = srv.orden("copia", "Copia hecha en", 30)
        ruta_copia = r.split("Copia hecha en", 1)[1].strip() if r else ""
        inf.comprobar(bool(ruta_copia) and os.path.isfile(ruta_copia), "Orden copia: hace la copia de seguridad con todos jugando", r)
        for j in jugadores:
            j.fuera.wait(args.segundos + 60)
        inf.comprobar(all(any("Aviso del servidor: Prueba de diez jugadores en marcha" in a for a in j.avisos) for j in jugadores), "El aviso les llega a todos",
                      [j.nombre for j in jugadores if not any("Prueba de diez" in a for a in j.avisos)])
        inf.comprobar(all(any("Mensaje del día: Hoy se prueba el servidor." in a for a in j.avisos) for j in jugadores), "El mensaje del día les llega a todos")
        inf.comprobar(all(j.chats.get("todos", 0) >= n - 1 for j in jugadores), "El chat general llega de todos a todos", [(j.nombre, j.chats) for j in jugadores])
        inf.comprobar(all(j.chats.get("priv", 0) >= 1 and j.chats.get("cerca", 0) >= 1 and j.chats.get("banda", 0) >= 1 for j in jugadores),
                      "Llegan también los mensajes privados, los de cerca y los de la banda", [(j.nombre, j.chats) for j in jugadores])
        inf.comprobar(all(j.situados == n - 1 for j in jugadores), "A cada uno le llega la posición de los otros %d" % (n - 1), [(j.nombre, j.situados) for j in jugadores])
        inf.comprobar(sum(j.impactos for j in jugadores) > 0 and sum(j.caidas for j in jugadores) > 0, "Ha habido pelea: disparos que dan y jugadores que caen",
                      (sum(j.impactos for j in jugadores), sum(j.caidas for j in jugadores)))
        inf.nota("Disparos que dieron: %d. Caídas: %d. Bajas cobradas: %d." % (sum(j.impactos for j in jugadores), sum(j.caidas for j in jugadores), sum(j.bajas for j in jugadores)))
        inf.comprobar(sum(j.quitas for j in jugadores) == 0, "Jugando limpio, el servidor no le discute dinero a nadie", [(j.nombre, j.quitas) for j in jugadores if j.quitas])
        # ---------------------------------------------- todos han salido y vuelven a entrar
        for j in jugadores:
            j.vuelto.wait(60)
        inf.comprobar(all(j.error is None for j in jugadores), "Ningún jugador ha tenido un tropiezo", [j.error for j in jugadores if j.error])
        for j in jugadores:
            for bien, texto, detalle in j.hechos:
                inf.comprobar(bien, texto, detalle)
        r = srv.orden("estado", "en marcha desde hace")
        inf.comprobar(r is not None and "Hay %d jugadores de %d" % (n, n) in r, "Tras salir y volver, vuelven a estar los %d dentro" % n, r)
        r = srv.orden("cuentas", "Hay ")
        inf.comprobar(r is not None and ("Hay %d:" % n) in r and "Ana (administra)" in r, "Orden cuentas: hay %d, y la primera administra" % n, r)
        r = srv.orden("bandas", "miembros")
        medio = n // 2
        inf.comprobar(r is not None and "Los Linces, %d miembros, %d euros" % (medio, 500 * medio) in r and "Los Zorros, %d miembros, %d euros" % (n - medio, 500 * (n - medio)) in r,
                      "Orden bandas: dos bandas, con toda su gente y su caja", r)
        r = srv.orden("guardar", "Guardado.")
        inf.comprobar(r is not None, "Orden guardar", r)
        r = srv.orden("copias", "Hay ")
        inf.comprobar(r is not None and "Hay 1" in r, "Orden copias: está la copia hecha antes", r)
        # ------------------------------------------------ apagado con orden, con todos dentro
        desde = len(srv.lineas())
        try:
            srv.proceso.stdin.write(b"apagar\n")
            srv.proceso.stdin.flush()
        except OSError:
            pass
        codigo = srv.esperar_salida(40)
        inf.comprobar(codigo == 0, "Orden apagar: el servidor se para solo, con código de salida 0", codigo)
        inf.comprobar(srv.esperar("Servidor parado. Todo guardado.", 3, desde) is not None, "Al parar dice que lo ha guardado todo", srv.lineas(desde))
        for j in jugadores:
            j.join(15)
        avisados = [j for j in jugadores if j.cerrado]
        inf.comprobar(len(avisados) >= n - 1, "A los jugadores se les dice que el servidor se cierra (%d de %d lo han oído)" % (len(avisados), n),
                      [j.nombre for j in jugadores if not j.cerrado])
        inf.comprobar(all(j.cerrado == "Un administrador ha apagado el servidor." for j in avisados), "Y se les dice por qué", [j.cerrado for j in avisados][:2])
        # ---------------------------------------------------- lo que ha quedado en el disco
        base = os.path.join(datos, "puertobravo.db")
        inf.comprobar(os.path.isfile(base), "Los datos están en el disco")
        db = sqlite3.connect("file:%s?mode=ro" % base.replace("\\", "/"), uri=True)
        try:
            inf.comprobar(db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "La base de datos está entera")
            cuentas = {f[0]: f for f in db.execute("SELECT nombre, partida, saldo, admin FROM cuentas")}
            inf.comprobar(len(cuentas) == n, "Hay %d cuentas guardadas" % n, sorted(cuentas))
            for j in jugadores:
                f = cuentas.get(j.nombre)
                inf.comprobar(f is not None and json.loads(f[1] or "null") == j.partida and f[2] == j.saldo_final, "En el disco, %s tiene su personaje y su dinero" % j.nombre,
                              (f[2] if f else None, j.saldo_final))
            inf.comprobar(db.execute("SELECT COUNT(*) FROM bandas").fetchone()[0] == 2 and db.execute("SELECT COUNT(*) FROM miembros").fetchone()[0] == n,
                          "En el disco, las dos bandas con sus %d miembros" % n)
            compradas = db.execute("SELECT COUNT(*) FROM propiedades").fetchone()[0]
            inf.comprobar(compradas == sum(1 for j in jugadores if j.partida and j.partida["jugador"]["propiedades"]), "En el disco, las casas y negocios que han comprado: %d" % compradas)
            aparcados = db.execute("SELECT COUNT(*) FROM vehiculos").fetchone()[0]
            inf.comprobar(aparcados >= 1, "En el disco, los vehículos que dejaron en la calle: %d" % aparcados)
        finally:
            db.close()
        registro = os.path.join(datos, "registro.txt")
        en_disco = open(registro, encoding="utf-8").read().splitlines() if os.path.isfile(registro) else []
        inf.comprobar(len(en_disco) > n and any("Entra Ana" in l for l in en_disco), "El registro se ha escrito en el disco")
        # --------------------------------------------- segundo arranque, sobre los mismos datos
        primero = srv.lineas()
        srv2 = ServidorReal(orden, carpeta, conf)
        atexit.register(srv2.matar)
        srv2.arrancar()
        escucha = srv2.esperar("escuchando en el puerto", 90)
        inf.comprobar(escucha is not None and "con cifrado" in escucha, "El servidor vuelve a arrancar sobre los mismos datos", srv2.lineas()[-5:])
        cert2 = (srv2.esperar("Huella del certificado:", 10) or "").split("Huella del certificado:")[-1].strip()
        inf.comprobar(cert2 == cert, "Usa el mismo certificado: los jugadores no tienen que aceptar otro", (cert2, cert))
        srv2.esperar("Escribe ayuda", 10)
        segundos = [Jugador(k, n, puerto, huella, mundo, sitio, 0, cert, solo_volver={"partida": j.partida, "saldo": j.saldo_final}) for k, j in enumerate(jugadores)]
        for j, viejo in zip(segundos, jugadores):
            j.casa = viejo.casa
            j.start()
            time.sleep(0.1)
        for j in segundos:
            j.vuelto.wait(60)
        inf.comprobar(all(j.error is None and j.ok is not None for j in segundos), "Tras reiniciar, vuelven a entrar los %d" % n, [j.error for j in segundos if j.error])
        mal = [(texto, detalle) for j in segundos for bien, texto, detalle in j.hechos if not bien]
        inf.comprobar(not mal and all(len(j.hechos) >= 4 for j in segundos), "Tras reiniciar, cada uno conserva su personaje, su dinero, su banda y su casa", mal[:3])
        r = srv2.orden("estado", "en marcha desde hace")
        inf.comprobar(r is not None and "Hay %d jugadores de %d" % (n, n) in r, "Y el servidor los cuenta a todos", r)
        # la otra forma de parar: desde fuera, con --parar
        pide = subprocess.run(orden + [conf, "--parar"], cwd=carpeta, env=dict(os.environ, PYTHONPATH=RAIZ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        inf.comprobar(pide.returncode == 0, "Se le pide parar desde fuera, con --parar, y recoge la orden", pide.stdout.decode("utf-8", "replace")[-300:])
        codigo = srv2.esperar_salida(40)
        inf.comprobar(codigo == 0, "Y se para con código de salida 0", codigo)
        for j in segundos:
            j.join(15)
        inf.comprobar(sum(1 for j in segundos if j.cerrado) >= n - 1, "A los jugadores se les avisa también esta vez", [j.nombre for j in segundos if not j.cerrado])
        # ------------------------------------------------------- ni un error en lo que ha dicho
        todo = primero + srv2.lineas()
        inf.comprobar(not malas(todo), "El servidor no ha dicho ni un error por la consola", malas(todo)[:5])
        if malas(todo):                                          # con lo que tenía alrededor, para saber de dónde viene
            feas = [i for i, l in enumerate(todo) if any(x in l for x in MALAS_SENALES)]
            for i in sorted({q for i in feas[:6] for q in range(max(0, i - 2), min(len(todo), i + 14))}):
                inf.nota("servidor: " + todo[i])
        en_disco = open(registro, encoding="utf-8").read().splitlines() if os.path.isfile(registro) else []
        inf.comprobar(not malas(en_disco), "Ni lo hay en su registro del disco", malas(en_disco)[:5])
        inf.nota("El servidor ha dicho %d líneas por la consola y %d en su registro." % (len(todo), len(en_disco)))
    except Exception:
        inf.comprobar(False, "La prueba no ha podido terminar", traceback.format_exc())
        for l in srv.lineas()[-15:]:
            inf.nota("servidor: " + l)
    finally:
        for j in jugadores:
            j.parar.set()
        for s in [x for x in (srv, locals().get("srv2")) if x is not None]:
            s.matar()
        vivos = [s for s in (srv, locals().get("srv2")) if s is not None and s.proceso is not None and s.proceso.poll() is None]
        inf.comprobar(not vivos, "No queda ningún servidor en marcha")
        if args.conservar:
            with open(os.path.join(carpeta, "consola_del_servidor.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(srv.lineas() + (locals()["srv2"].lineas() if locals().get("srv2") else [])) + "\n")
            inf.nota("La carpeta de la prueba se conserva, con lo que ha dicho el servidor en consola_del_servidor.txt: %s" % carpeta)
        else:
            for _ in range(20):
                shutil.rmtree(carpeta, ignore_errors=True)
                if not os.path.exists(carpeta):
                    break
                time.sleep(0.3)
            inf.comprobar(not os.path.exists(carpeta), "La carpeta temporal queda borrada", carpeta)
    hechas = sum(1 for l in inf.lineas if l.startswith(("BIEN", "MAL ")))
    print()
    print("RESUMEN: %d comprobaciones, %d bien y %d mal." % (hechas, hechas - inf.fallos, inf.fallos))
    if inf.fallos:
        print("Lo que ha ido mal:")
        for l in inf.lineas:
            if l.startswith("MAL "):
                print("  " + l[4:].strip())
        print("RESULTADO: el servidor NO ha pasado la prueba.")
        return 1
    print("RESULTADO: todo bien. El servidor ha aguantado a los %d jugadores, ha guardado todo y se ha parado con orden." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
