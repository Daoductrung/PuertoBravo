"""Un juego o un servidor de la versión que sea, en su propio proceso, manejado desde fuera por órdenes de texto.

No es una prueba: lo arranca ``banco_versiones.py``. Sirve para poner a jugar juntos, de verdad, el código publicado de
una versión anterior y el de ahora, sin mezclar sus módulos en un mismo proceso.

    python agente_versiones.py <raíz del código> <carpeta de datos temporal> juego|servidor [opciones en JSON]

Por la entrada le llega, en cada línea, un texto JSON con código de Python; lo ejecuta en un espacio de nombres que se
conserva y contesta con otra línea JSON: {"ok": true, "r": valor de _r} o {"ok": false, "error": traza}.
Todo lo que usa de cada versión existe en las dos (la 1.7.0 y la actual): por eso es tan poco.
"""
import json
import os
import sys
import time
import traceback

RAIZ, DATOS, MODO = sys.argv[1], sys.argv[2], sys.argv[3]
OPC = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != AQUI]      # ni las pruebas ni el juego de ahora, si la raíz es otra
sys.path.insert(0, RAIZ)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

SALIDA = os.fdopen(os.dup(1), "w", encoding="utf-8", newline="\n")           # la línea de respuestas; lo demás, al canal de errores
os.dup2(2, 1)
sys.stdout = sys.stderr

# Quien firma los mundos en este banco: una clave de pruebas, la misma para todos los procesos.
import hashlib      # noqa: E402
EDITOR = hashlib.sha256(b"quien publica el juego, en el banco de versiones").digest()
N = {"time": time, "json": json, "os": os, "RAIZ": RAIZ, "DATOS": DATOS}


def _sencillo(v, hondo=0):
    """Lo que se devuelve tiene que caber en JSON: lo que no, como texto."""
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if hondo > 6:
        return repr(v)[:200]
    if isinstance(v, dict):
        return {str(k): _sencillo(x, hondo + 1) for k, x in v.items()}
    if isinstance(v, (list, tuple, set, frozenset)):
        return [_sencillo(x, hondo + 1) for x in v]
    return repr(v)[:200]


def preparar_juego():
    from juego import rutas
    rutas.DATA = DATOS                           # opciones, identidad, partidas y registros, en la carpeta temporal de este proceso
    os.makedirs(os.path.join(DATOS, "datos"), exist_ok=True)
    os.startfile = lambda *a, **k: None
    import pygame
    from juego import ed25519, enlinea, menus_juego
    from juego.app import App
    menus_juego.CARPETA = "partidas_pruebas"
    if OPC.get("firmar", True):                  # el mundo de esta versión, avalado por «quien publica» en este banco
        d = enlinea.mundo_servidor()
        with open(os.path.join(DATOS, "datos", "mundo.firma"), "w", encoding="utf-8") as f:
            json.dump({"huella": d["huella"], "version": d["version"],
                       "firma": ed25519.firmar(EDITOR, enlinea.mundo_canonico(d).encode("utf-8")).hex()}, f)
    app = App(pruebas=True)
    from juego import VERSION

    def frames(n=1, dt=1 / 30, pausa=0.012, mantener=()):
        for _ in range(n):
            for k in mantener:
                app.teclas.add(k)
            app.paso(dt)
            app.mez.render(256)
            if pausa:
                time.sleep(pausa)                # sin pausas, el juego manda más mensajes de los que el servidor admite
        for k in mantener:
            app.teclas.discard(k)

    def tecla(k, mod=0, unicode=""):
        app.inyectar(k, mod, unicode)

    def saltar_dialogos(tope=40):
        from juego.menus import Dialogo, Menu
        for _ in range(tope):
            cima = app.pila[-1]
            if isinstance(cima, Dialogo):
                tecla(pygame.K_ESCAPE)
            elif isinstance(cima, Menu) and not cima.escapable and cima is not app.pila[0]:
                cima.i = len(cima.opciones) - 1
                tecla(pygame.K_RETURN)
            else:
                return

    def dicho(n=60):
        return " | ".join(app.voz.registro[-n:])

    def entrar(puerto, nombre, vuelve=True):
        """Entra en un servidor local por el mismo camino que el menú. Devuelve lo esencial de la bienvenida, o el rechazo."""
        app.cfg["red_nombre"] = nombre
        app.semilla_identidad = hashlib.sha256(("juego-" + nombre).encode()).digest()
        s = {"nombre": "", "dir": "puertobravo://127.0.0.1:%d" % puerto, "cert": ""}
        enlace, motivo = enlinea.conectar(app, s)
        if enlace is None:
            return {"entra": False, "motivo": str(motivo), "codigo": getattr(motivo, "codigo", "")}
        app.enlace = enlace
        ok = enlace.ok
        if ok.get("partida"):
            app.empezar_partida(ok["partida"])
        else:
            app.empezar_partida(None, personaje={"id": app.datos["personajes"][0]["id"], "genero": "h"})
        saltar_dialogos()
        p = app.partida
        p.cfg["sucesos"] = False
        return {"entra": bool(p.en_servidor), "id": ok.get("id"), "cuenta": ok.get("cuenta"), "admin": ok.get("admin"), "mundo": ok.get("mundo"),
                "funciones": ok.get("funciones"), "partida_de": ok.get("partida_de"), "tenia_partida": bool(ok.get("partida")),
                "saldo": ok.get("saldo"), "claves": sorted(ok)}

    def hasta(cond, segundos=8.0):
        """Avanza el juego hasta que se cumpla una condición (un texto de Python o una función)."""
        f = (lambda: eval(cond, N)) if isinstance(cond, str) else cond
        fin = time.time() + segundos
        while time.time() < fin:
            frames(2)
            if f():
                return True
        return False

    def salir():
        p = app.partida
        if p is not None:
            p.sv_salir()
            p.desconectar_online()
            app.partida = None
        time.sleep(0.3)

    def cerrar():
        try:
            salir()
        except Exception:
            pass
        for cosa in ("radio", "ambiente"):
            try:
                getattr(app, cosa).cancelar()
            except Exception:
                pass
        try:
            app.mez.cerrar()
        except Exception:
            pass

    N.update(app=app, pygame=pygame, enlinea=enlinea, VERSION=VERSION, frames=frames, tecla=tecla, saltar_dialogos=saltar_dialogos, dicho=dicho,
             entrar=entrar, hasta=hasta, salir=salir, cerrar=cerrar, P=lambda: app.partida)
    return {"version": VERSION, "huella": enlinea.huella_datos(app.datos)}


def preparar_servidor():
    import asyncio
    import binascii
    import threading
    from juego import ed25519
    from servidor import nucleo
    cfg = {"datos": DATOS, "puerto": 0, "interfaz": "127.0.0.1", "cifrado": "no", "proteccion": 0, "personajes": 0, "economia": "no",
           "trafico": "no", "peatones": "no", "patrullas": 0, "policia": "no", "parada_espera": 3}
    cfg.update(OPC.get("cfg") or {})
    cfg = {k: v for k, v in cfg.items() if k in nucleo.CONFIG}      # una versión anterior no conoce las opciones nuevas
    mundo = dict(nucleo.MUNDO_VACIO) if OPC.get("mundo") == "vacio" else None      # None: el mundo.json que trae ese servidor
    loop = asyncio.new_event_loop()
    listo = threading.Event()
    caja = {}

    def correr():
        asyncio.set_event_loop(loop)
        srv = nucleo.Servidor(cfg, mundo)
        srv.claves_publicas = (binascii.hexlify(ed25519.publica(EDITOR)).decode(),)
        caja["lineas"] = []
        srv.log = caja["lineas"].append
        caja["srv"] = srv
        loop.run_until_complete(srv.iniciar())
        listo.set()
        loop.run_forever()
    hilo = threading.Thread(target=correr, daemon=True)
    hilo.start()
    assert listo.wait(15), "el servidor no arranca"
    srv = caja["srv"]

    def hacer(f, *a):
        async def envolver():
            r = f(*a)
            if asyncio.iscoroutine(r):
                r = await r
            return r
        return asyncio.run_coroutine_threadsafe(envolver(), loop).result(40)

    def parar(**k):
        hacer(lambda: srv.detener(**k))
        loop.call_soon_threadsafe(loop.stop)
        hilo.join(5)

    def cerrar():
        try:
            if srv.activo:
                parar()
        except Exception:
            pass

    N.update(srv=srv, nucleo=nucleo, hacer=hacer, parar=parar, cerrar=cerrar, lineas=caja["lineas"], J=lambda nombre: next(j for j in srv.jugadores.values() if j.nombre == nombre))
    return {"puerto": srv.puerto, "version": srv.mundo.get("version"), "huella": srv.mundo.get("huella"), "funciones": list(getattr(nucleo, "FUNCIONES", ()))}


def responder(obj):
    SALIDA.write(json.dumps(obj, ensure_ascii=False) + "\n")
    SALIDA.flush()


def principal():
    try:
        responder({"ok": True, "r": preparar_juego() if MODO == "juego" else preparar_servidor()})
    except Exception:
        responder({"ok": False, "error": traceback.format_exc()})
        return
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        codigo = json.loads(linea)
        if codigo == "__fin__":
            break
        N.pop("_r", None)
        try:
            exec(codigo, N)
            responder({"ok": True, "r": _sencillo(N.get("_r"))})
        except Exception:
            responder({"ok": False, "error": traceback.format_exc()})
    try:
        N["cerrar"]()
    except Exception:
        pass
    responder({"ok": True, "r": "fin"})
    sys.stdout.flush()
    os._exit(0)                                  # sin esperar a hilos de sonido o de red de la versión que sea


if __name__ == "__main__":
    principal()
