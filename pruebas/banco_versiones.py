"""Banco para poner a jugar juntas dos versiones del juego: la publicada de la 1.7.0, con su código real, y la de ahora.

El código de la 1.7.0 se saca del repositorio con ``git archive`` a una carpeta temporal de fuera del proyecto (una sola
vez; se reutiliza). Cada juego y cada servidor corre en su propio proceso, con su carpeta de datos temporal: nunca se
mezclan módulos de las dos versiones. Desde la prueba se les manda código de Python en texto (``agente_versiones.py``).

No es una prueba: la usa ``test_171_versiones.py``.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMIT_170 = "d01b518"                           # la 1.7.0 tal como se publicó
# Lo justo para que el juego y el servidor de entonces arranquen sin ventana: ni música, ni voces, ni packs de sonido.
RUTAS_170 = ("juego", "servidor", "data/datos", "data/sonidos/por_defecto", "data/mods", "main.py")
AGENTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agente_versiones.py")


class SinBanco(Exception):
    """No se ha podido sacar el código de la 1.7.0: la prueba se salta, diciendo por qué."""


def carpeta_170():
    """La carpeta con el código publicado de la 1.7.0. La saca del repositorio si aún no está."""
    destino = os.path.join(tempfile.gettempdir(), "puertobravo_banco_versiones", "1.7.0_" + COMMIT_170)
    marca = os.path.join(destino, "_completo.txt")
    if os.path.exists(marca):
        return destino
    try:
        r = subprocess.run(["git", "archive", "--format=tar", COMMIT_170] + list(RUTAS_170), cwd=RAIZ, capture_output=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as e:
        raise SinBanco("no se puede ejecutar git para sacar el código de la 1.7.0: %s" % e)
    if r.returncode != 0 or not r.stdout:
        raise SinBanco("git no tiene la versión 1.7.0 (%s) en este repositorio: %s" % (COMMIT_170, r.stderr.decode("utf-8", "replace").strip()[:200]))
    shutil.rmtree(destino, ignore_errors=True)
    os.makedirs(destino, exist_ok=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
            base = os.path.abspath(destino)
            for m in t.getmembers():                         # nada fuera de la carpeta
                if not os.path.abspath(os.path.join(base, m.name)).startswith(base) or m.issym() or m.islnk():
                    raise SinBanco("el archivo de la 1.7.0 trae rutas que no se esperan")
            t.extractall(destino)
    except (tarfile.TarError, OSError) as e:
        raise SinBanco("no se puede desempaquetar el código de la 1.7.0: %s" % e)
    with open(marca, "w", encoding="utf-8") as f:
        f.write(COMMIT_170)
    return destino


class Proceso:
    """Un juego o un servidor de una versión, en su proceso. ``raiz`` es la carpeta de su código."""

    def __init__(self, raiz, datos, modo, **opc):
        self.raiz, self.datos, self.modo = raiz, str(datos), modo
        os.makedirs(self.datos, exist_ok=True)
        entorno = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        entorno.pop("PYTHONPATH", None)
        self.errores = open(os.path.join(self.datos, "_salida.txt"), "w", encoding="utf-8", errors="replace")
        self.p = subprocess.Popen([sys.executable, AGENTE, raiz, self.datos, modo, json.dumps(opc)], cwd=self.datos, env=entorno,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.errores)
        self.info = self._leer(240)              # la primera vez, un juego puede tener que preparar sus sonidos

    def _leer(self, espera):
        caja = {}

        def leer():
            caja["linea"] = self.p.stdout.readline()
        h = threading.Thread(target=leer, daemon=True)
        h.start()
        h.join(espera)
        if h.is_alive() or not caja.get("linea"):
            cola = self.cola_errores()
            self.matar()
            raise AssertionError("el proceso %s de %s no contesta. Lo último que dijo:\n%s" % (self.modo, self.raiz, cola))
        r = json.loads(caja["linea"].decode("utf-8"))
        if not r.get("ok"):
            raise AssertionError("en el proceso %s de %s:\n%s" % (self.modo, os.path.basename(self.raiz), r.get("error")))
        return r.get("r")

    def cola_errores(self, n=3000):
        try:
            self.errores.flush()
            with open(self.errores.name, encoding="utf-8", errors="replace") as f:
                return f.read()[-n:]
        except OSError:
            return ""

    def __call__(self, codigo, espera=90):
        """Ejecuta ese código en el proceso y devuelve lo que deje en ``_r``."""
        self.p.stdin.write((json.dumps(codigo) + "\n").encode("ascii"))
        self.p.stdin.flush()
        return self._leer(espera)

    def ev(self, expresion, espera=90):
        return self("_r = (%s)" % expresion, espera)

    def vivo(self):
        return self.p.poll() is None

    def cerrar(self):
        if self.vivo():
            try:
                self.p.stdin.write((json.dumps("__fin__") + "\n").encode("ascii"))
                self.p.stdin.flush()
                self.p.wait(20)
            except Exception:
                pass
        self.matar()

    def matar(self):
        if self.vivo():
            try:
                self.p.kill()
                self.p.wait(10)
            except Exception:
                pass
        try:
            self.errores.close()
        except Exception:
            pass


class Banco:
    """Lleva la cuenta de los procesos abiertos y los cierra todos al acabar."""

    def __init__(self, carpeta):
        self.carpeta = str(carpeta)
        self.vieja = carpeta_170()
        self.nueva = RAIZ
        self.procesos = []
        self._n = 0

    def _datos(self, nombre):
        self._n += 1
        return os.path.join(self.carpeta, "%02d_%s" % (self._n, nombre))

    def servidor(self, version="nueva", mundo="propio", datos=None, **cfg):
        """Un servidor de la versión «nueva» o «vieja». ``mundo``: «propio» (el mundo.json que trae) o «vacio»."""
        s = Proceso(self.vieja if version == "vieja" else self.nueva, datos or self._datos("servidor_" + version), "servidor", mundo=mundo, cfg=cfg)
        s.puerto = s.info["puerto"]
        self.procesos.append(s)
        return s

    def juego(self, version="nueva", datos=None, firmar=True):
        g = Proceso(self.vieja if version == "vieja" else self.nueva, datos or self._datos("juego_" + version), "juego", firmar=firmar)
        g.version = g.info["version"]
        self.procesos.append(g)
        return g

    def cerrar(self):
        for p in reversed(self.procesos):
            p.cerrar()
        self.procesos = []
