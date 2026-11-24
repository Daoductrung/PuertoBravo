"""Jugar juntos con versiones distintas del juego, probado con el código REAL de la 1.7.0 publicada y el de ahora.

No es una simulación: el juego y el servidor de la 1.7.0 se sacan del repositorio (``git archive``) a una carpeta
temporal y corren en procesos aparte, cada uno con su carpeta de datos (``banco_versiones.py``). Las cuatro
combinaciones: servidor nuevo vacío en el que entra primero el juego antiguo, el mismo en el que entra primero el
nuevo, servidor nuevo con su mundo, y servidor antiguo con juego nuevo. En cada una, lo mismo: entrar, verse, hablar,
moverse, vehículos, pelear con armas de antes y con las seis nuevas, policía, comprar, guardar y volver, misión en
grupo, corte y reconexión, y parada del servidor.

Después, las reglas una a una: el personaje que pasa por una versión anterior sin perder nada, quien trae datos que
no se pueden comprobar, las nóminas de los contratos fijos y sus trampas, y lo que no existe conectado.

Si no se puede sacar la 1.7.0 (no hay git, o falta ese commit), las pruebas que la necesitan se saltan diciendo por qué.
Todo corre en este equipo: no se toca ningún servidor real ni se sale a la red.
"""
import copy
import hashlib
import json
import os
import sqlite3
import time

import pytest

import banco_versiones as bv
from juego import VERSION, enlinea
from servidor import compat, nucleo, opciones
from test_servidor import Banco, Cli, lejos_de_todo, mundo

ARMAS_NUEVAS = ("escopeta_corredera", "fusil_semi", "hacha", "lanzagranadas", "pistola_rafagas", "rifle_palanca")
H170 = "180125344b7496ff"                        # la huella del mundo de la 1.7.0 publicada
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================================ el taller: procesos de las dos versiones
class Taller:
    """Un juego de cada versión, que se reutilizan de prueba en prueba (arrancarlos cuesta), y los servidores de cada una."""

    def __init__(self, carpeta):
        self.banco = bv.Banco(carpeta)
        self._juegos = {}
        self.servidores = []

    def juego(self, version):
        g = self._juegos.get(version)
        if g is None or not g.vivo():
            g = self._juegos[version] = self.banco.juego(version)
            g.nombre = None
        return g

    def servidor(self, version="nueva", mundo="propio", **cfg):
        s = self.banco.servidor(version, mundo, **cfg)
        s.version = version
        self.servidores.append(s)
        return s

    def recoger(self):
        """Al acabar una prueba: los juegos salen del servidor en el que estén y los servidores se cierran."""
        for g in self._juegos.values():
            if g.vivo():
                try:
                    g("salir()")
                except AssertionError:
                    g.matar()
        for s in self.servidores:
            s.cerrar()
        self.servidores = []


@pytest.fixture(scope="module")
def taller_mod(tmp_path_factory):
    try:
        t = Taller(tmp_path_factory.mktemp("versiones"))
    except bv.SinBanco as e:
        pytest.skip("No se puede montar el banco con la 1.7.0 real: %s" % e)
    yield t
    t.banco.cerrar()


@pytest.fixture
def taller(taller_mod):
    yield taller_mod
    taller_mod.recoger()


def entrar(g, s, nombre):
    r = g.ev("entrar(%d, %r)" % (s.puerto, nombre))
    g.nombre = nombre
    assert r["entra"], r
    g("p = P()\nro = None")
    return r


def ambos(a, b, cond_a="True", cond_b="True", seg=10.0):
    """Hace avanzar los dos juegos hasta que cada uno cumple su condición."""
    fin = time.time() + seg
    while time.time() < fin:
        ra = a("frames(3)\n_r = bool(%s)" % cond_a)
        rb = b("frames(3)\n_r = bool(%s)" % cond_b)
        if ra and rb:
            return True
    return False


def mirar(g):
    """Vuelve a coger la partida y al otro jugador: cambian al reentrar."""
    g("p = P()\nro = next(iter(p.remotos.values()), None) if p is not None else None")


def espiar(s, nombres):
    """Apunta, en el servidor, lo que de verdad se le pone en la cola a cada jugador (ya adaptado a su versión)."""
    s("""
enviados = []
def espiar(nombre):
    j = J(nombre)
    viejo = j.cola.put_nowait
    def put(o):
        m = o
        if isinstance(o, bytes) and not o.startswith(b'{"t":"estados"'):
            try:
                m = json.loads(o.decode("utf-8"))
            except ValueError:
                m = None
        if isinstance(m, dict) and m.get("t") in ("herido", "tiro", "evento", "veh_libre", "veh_ocupado", "recibe", "cerrado", "parada", "aviso"):
            enviados.append([nombre, m])
        return viejo(o)
    j.cola.put_nowait = put
for n in %r:
    hacer(espiar, n)
""" % (list(nombres),))


def partida_guardada(datos, nombre):
    """El personaje de un jugador, leído del archivo del servidor cuando ya está parado."""
    db = sqlite3.connect(os.path.join(datos, "puertobravo.db"))
    try:
        fila = db.execute("SELECT partida FROM cuentas WHERE nombre=?", (nombre,)).fetchone()
        return json.loads(fila[0]) if fila and fila[0] else None
    finally:
        db.close()


# ============================================================================ lo mismo en las cuatro combinaciones
def jugar_juntos(taller, s, a, b):
    """Dos juegos, de la versión que sean, ya dentro del mismo servidor: todo lo que se hace jugando juntos.
    Devuelve una lista de lo comprobado, para que el fallo diga hasta dónde llegó."""
    na, nb = a.nombre, b.nombre
    nuevo_s = s.version == "nueva"
    hecho = []
    mundo_s = s.ev("{'version': srv.mundo.get('version'), 'armas': srv.mundo['armas'], 'modelos': sorted(srv.mundo['modelos'])}")
    armas_s = mundo_s["armas"]
    X, Y = s("seg = [(l['x'], l['y']) for l in srv.mundo['mapas']['puerto_bravo']['lugares'] if l['tipo'] in nucleo.SEGURAS]\n"
             "_r = next([float(x), float(y)] for x in range(40, 900, 37) for y in range(40, 700, 41) if all((x - p) ** 2 + (y - q) ** 2 > 60 ** 2 for p, q in seg))")
    VE = "len(p.remotos) == 1 and next(iter(p.remotos.values())).visto and next(iter(p.remotos.values())).mapa == p.mundo.id"

    def colocar(d=6.0):
        a("p.sv['protegido'] = 0; p.objetivo = None; p.teletransportar(%r, %r)" % (X, Y))
        b("p.sv['protegido'] = 0; p.objetivo = None; p.teletransportar(%r, %r)" % (X + d, Y))
        # Con el servidor de la 1.7.0, quien sale en plena pelea queda quince segundos como «fantasma» y al volver hay un
        # momento con dos fichas suyas (en el de ahora, quien vuelve sustituye a la anterior): ahí se espera a que se vaya.
        assert ambos(a, b, VE, VE, 10 if nuevo_s else 30), (a.ev("[[(r.nombre, r.visto, r.mapa) for r in p.remotos.values()], p.mundo.id, p.en_servidor, dicho(9)]"),
                                     b.ev("[[(r.nombre, r.visto, r.mapa) for r in p.remotos.values()], p.mundo.id, p.en_servidor, dicho(9)]"), s.ev("lineas"))
        mirar(a), mirar(b)
        assert ambos(a, b, "abs(ro.tx - %r) < 1.5" % (X + d), "abs(ro.tx - %r) < 1.5" % X)
        s("hacer(lambda: [setattr(q, 'protegido', 0) for q in srv.jugadores.values()])")

    # ---- entrar y verse
    colocar()
    assert a.ev("ro.nombre") == nb and b.ev("ro.nombre") == na
    hecho.append("verse")
    # ---- chat, en los dos sentidos, y los canales de rol escritos como órdenes (valen con cualquier versión)
    a("p.red.enviar({'t': 'chat', 'texto': 'hola desde %s', 'canal': 'todos'})" % na)
    assert ambos(a, b, "True", "'hola desde %s' in dicho(8)" % na)
    b("p.red.enviar({'t': 'chat', 'texto': 'hola desde %s', 'canal': 'cerca'})" % nb)
    assert ambos(a, b, "'hola desde %s' in dicho(8)" % nb)
    if nuevo_s:
        for x, q in ((a, b), (b, a)):
            x("p.red.enviar({'t': 'chat', 'texto': '/yo saluda con la mano', 'canal': 'todos'})")
            assert ambos(a, b, "True", "True", 0.3) or True
            assert ambos(q, x, "'saluda con la mano' in dicho(8)"), q.ev("dicho(4)")
            oido = q.ev("[t for t in app.voz.registro[-8:] if 'saluda con la mano' in t][-1]")
            # quien no conoce los canales de rol lo recibe por el chat de cerca, con una marca; quien los conoce, como acción
            assert ("(acción)" in oido) == (q.version == "1.7.0"), oido
            assert x.nombre in oido
    hecho.append("chat")
    # ---- moverse
    a("p.teletransportar(%r, %r)" % (X + 2, Y + 3))
    assert ambos(a, b, "True", "abs(ro.tx - %r) < 1.5 and abs(ro.ty - %r) < 1.5" % (X + 2, Y + 3))
    hecho.append("moverse")
    # ---- vehículos: subir, que el otro lo oiga conducir, ir de pasajero, aparcar, y que el otro se lo lleve
    for x, q in ((a, b), (b, a)):
        colocar()
        x("x0, y0 = p.pos(); v = p.crear_vehiculo('sedan', x0, y0, 0, 'aparcado'); v.cerrado = False; p._subir(v, True)")
        assert ambos(x, q, "getattr(v, 'id_red', None) is not None", "ro.veh == 'sedan'"), (x.nombre, q.ev("ro.veh"))
        q("p.teletransportar(ro.x + 1.5, ro.y)")
        ambos(a, b, seg=0.6)
        q("p.entrar_salir()")
        assert ambos(x, q, "True", "getattr(p, 'pasajero', None) is not None", 5), q.ev("dicho(3)")
        assert "Subes de pasajero con %s" % x.nombre in q.ev("dicho(6)") and "%s sube a tu vehículo" % q.nombre in x.ev("(frames(6), dicho(6))[1]")
        q("p.entrar_salir()")
        assert ambos(x, q, "True", "getattr(p, 'pasajero', None) is None", 5)
        vid = x.ev("v.id_red")
        x("p.salir_vehiculo()")
        assert ambos(x, q, "p.j.veh is None", "not ro.veh and any(getattr(w, 'id_red', None) == %d and not w.muerto for w in p.vehiculos)" % vid), q.ev("p.sv['vehs']")
        assert s.ev("[srv.vehiculos[%d]['modelo'], srv.vehiculos[%d]['por']]" % (vid, vid)) == ["sedan", None]
        # el otro va hasta él y se lo lleva: del mundo del primero desaparece
        q("w = next(w for w in p.vehiculos if getattr(w, 'id_red', None) == %d); p.teletransportar(w.x + 2, w.y)" % vid)
        ambos(a, b, seg=0.8)
        q("p.entrar_salir()")
        assert ambos(x, q, "True", "p.j.veh is w", 6), q.ev("dicho(3)")
        assert ambos(x, q, "'se ha llevado tu' in dicho(8)"), x.ev("dicho(4)")
        q("p.salir_vehiculo(forzado=True); p.quitar_vehiculo(w)")
        assert ambos(x, q, seg=1.0) or True
    hecho.append("vehiculos")
    # ---- combate: el daño lo pone el servidor con las cifras de SU mundo, las mismas para quien dispara con una versión y
    # para quien dispara con otra. Con la pistola en los dos sentidos, y con las seis armas nuevas de quien las tiene.
    espiar(s, [na, nb])
    for g in (a, b):
        g("sonados = []\n_son = p.son\ndef _oir(nombre, *c, **k):\n    sonados.append(nombre)\n    return _son(nombre, *c, **k)\np.son = _oir")
    golpes = {}
    for x, q in ((a, b), (b, a)):
        suyas = ["pistola"] + (list(ARMAS_NUEVAS) if x.version != "1.7.0" else [])
        for arma in suyas:
            if arma == "lanzagranadas":
                continue                                   # los explosivos van aparte, justo debajo
            d = 2.0 if arma == "hacha" else 6.0
            colocar(d) if x is a else (colocar(d))
            x("p.sv['protegido'] = 0"), q("p.sv['protegido'] = 0")
            q("p.j.salud_max = 600.0; p.j.salud = 600.0; frames(4)")
            x("p.dar_arma(%r, 200); p.j.arma = %r\nif 'cargador' in p.j.armas[%r]: p.j.armas[%r]['cargador'] = 12\nfj = p.fijar(True, callar=True)" % (arma, arma, arma, arma))
            ambos(a, b, seg=0.5)
            s("del enviados[:]")
            q("del sonados[:]")
            quita = 0.0
            for _ in range(30):
                x("p.j.t_ataque = 0\nif 'cargador' in p.j.armas[%r]: p.j.armas[%r]['cargador'] = 12\np.objetivo = fj\np.atacar()\nframes(3)" % (arma, arma))
                time.sleep(max(0.45, float((armas_s.get(arma) or {}).get("cadencia", 0.5)) * 0.8))
                quita = q("frames(3)\n_r = round(600.0 - p.j.salud, 1)")
                if quita > 0:
                    break
            en_mundo = arma in armas_s
            if not en_mundo:
                # el mundo del servidor no conoce esa arma: contra otros jugadores cuenta como las manos, y se le dice
                assert quita == 0 or quita <= 12, (arma, quita)
                assert "no existe en la versión del juego con la que va este servidor" in x.ev("(frames(10), dicho(12))[1]"), x.ev("dicho(6)")
                golpes[(x.version, arma)] = "manos"
                continue
            assert quita > 0, (x.nombre, arma, x.ev("dicho(4)"), s.ev("lineas[-3:]"))
            llegado = [m for n, m in s.ev("enviados") if n == q.nombre and m["t"] == "herido"]
            assert llegado, (arma, s.ev("enviados"))
            cifra = armas_s[arma]
            minimo = max(1.0, cifra["dano"] * (1.0 - 0.4 * min(1.0, d / max(1.0, cifra["alcance"]))) * 0.85) - 0.3
            maximo = cifra["dano"] * 1.15 + 0.3
            assert minimo <= llegado[0]["dano"] <= maximo, (arma, llegado[0], minimo, maximo)      # las cifras del servidor, y nada más
            assert abs(quita - sum(m["dano"] for m in llegado)) < 0.6, (arma, quita, llegado)       # y eso es lo que pierde, ni más ni menos
            golpes[(x.version, arma)] = llegado[0]["dano"]
            if q.version == "1.7.0" and arma in ARMAS_NUEVAS:
                conocidas = q.ev("sorted(p.armas_d)")
                assert arma not in conocidas
                if nuevo_s:
                    # al juego antiguo le llega el arma más parecida de las que conoce, y la oye; nunca un arma que no tiene
                    eq = llegado[0]["arma"]
                    assert eq in conocidas and eq == compat.arma_equivalente(arma, armas_s, set(conocidas)), (arma, eq)
                    ruidos = [m["que"] for n, m in s.ev("enviados") if n == q.nombre and m["t"] == "evento" and str(m.get("que", "")).startswith("d:")]
                    if armas_s[arma]["tipo"] == "fuego":
                        assert ruidos and all(r[2:] in conocidas for r in ruidos), (arma, ruidos)
                        assert q.ev("p.armas_d[%r]['sonido'] in sonados" % eq), (arma, eq, q.ev("sonados[-8:]"))
                else:
                    assert llegado[0]["arma"] == arma        # un servidor de la 1.7.0 no sabe adaptarlo: llega tal cual, y su juego lo aguanta
            assert q.ev("app.partida is not None and p.en_servidor")
    # la misma arma hace el mismo daño venga de la versión que venga: mismas cifras, mismo intervalo
    assert isinstance(golpes[(a.version, "pistola")], float) and isinstance(golpes[(b.version, "pistola")], float)
    hecho.append("combate")
    # el explosivo nuevo: lo lanza quien lo tiene; el servidor reparte el daño si lo conoce
    lanza, recibe = (a, b) if a.version != "1.7.0" else (b, a)
    if lanza.version != "1.7.0":
        colocar(9.0)
        recibe("p.j.salud_max = 600.0; p.j.salud = 600.0; frames(4)")
        s("del enviados[:]")
        lanza("p.sv['protegido'] = 0")
        time.sleep(1.6)                                    # la cadencia la vigila el servidor, y acaba de disparar otra arma
        lanza("p.red.enviar({'t': 'explosion', 'arma': 'lanzagranadas', 'x': ro.tx, 'y': ro.ty})")
        ambos(a, b, seg=1.5)
        quita = recibe("frames(3)\n_r = round(600.0 - p.j.salud, 1)")
        if "lanzagranadas" in armas_s:
            assert 20 < quita <= armas_s["lanzagranadas"]["dano"] + 1, quita
            llegado = [m for n, m in s.ev("enviados") if n == recibe.nombre and m["t"] == "herido"]
            if nuevo_s and recibe.version == "1.7.0":
                assert llegado and llegado[0]["arma"] in recibe.ev("sorted(p.armas_d)") and armas_s[llegado[0]["arma"]]["tipo"] == "explosivo", llegado
        else:
            assert quita == 0
        hecho.append("explosivo")
    for g in (a, b):
        g("p.j.salud_max = 100.0; p.j.salud = 100.0")
    # ---- policía común: el delito de uno lo lleva el servidor, y el otro lo ve buscado
    colocar()
    a("p.sv_delito(6)")
    assert ambos(a, b, "p.j.estrellas >= 1", "ro.estrellas >= 1", 12), (a.ev("[p.j.estrellas, p.sv_policia_comun()]"), b.ev("ro.estrellas"))
    s("hacer(lambda: srv.po_limpiar(J(%r), 'prueba', True))" % na)
    assert ambos(a, b, "p.j.estrellas == 0", "ro.estrellas == 0", 12)
    hecho.append("policia")
    # ---- comprar: un negocio. El otro deja de poder comprarlo y sabe de quién es
    neg = a("neg = next(l for l in p.mundo.lugares.values() if l.tipo == 'negocio' and int(l.get('precio', 0)) > 0 and int(l.get('ingresos', 0)) > 0)\n"
            "precio = int(neg.get('precio')); p.j.dinero = precio + 4321; p.j.banco = 0; ok_pago = p.pagar(precio); p.j.propiedades.append(neg.id); p.sv_comprado(neg)\n_r = neg.id")
    assert a.ev("ok_pago and p.j.dinero == 4321")
    assert ambos(a, b, "True", "p.sv_dueno(p.lugares[%r]) == %r" % (neg, na)), b.ev("p.sv['props']")
    hecho.append("comprar")
    # ---- guardar y volver a entrar: el personaje es el mismo, con su dinero, su sitio y su negocio
    b("p.j.dinero = 2468; p.j.banco = 0")
    for g, dinero in ((a, 4321), (b, 2468)):
        g("x9, y9 = p.pos(); p.sv_guardar(ya=True); frames(12)")
        g("salir()")
        r = g.ev("entrar(%d, %r)" % (s.puerto, g.nombre))
        assert r["entra"] and r["tenia_partida"], r
        mirar(g)
        assert g.ev("p.j.dinero") == dinero and g.ev("abs(p.j.x - x9) < 30 and abs(p.j.y - y9) < 30"), (g.nombre, g.ev("[p.j.dinero, p.j.x, p.j.y]"))
    assert a.ev("%r in p.j.propiedades" % neg)
    colocar()
    hecho.append("guardar y volver")
    # ---- grupo y misión en grupo: la lleva el primero, el otro va con él, y cobra su parte
    a("p.red.enviar({'t': 'grupo_invitar', 'a': ro.id, 'mision': 'Morosos'})")
    assert ambos(a, b, "True", "p.sv['inv_grupo'] is not None")
    b("p.red.enviar({'t': 'grupo_resp', 'si': True})")
    assert ambos(a, b, "p.sv_lidero()", "p.sv['grupo'] == ro.id")
    lx, ly = a("mis = next(x for x in p.datos['misiones'] if x['id'] == 'm04'); l = p.lugares[mis['lugar']]; p.teletransportar(l.x, l.y); p.iniciar_mision(mis); saltar_dialogos(); frames(4)\n"
               "paso = p.mision['def']['pasos'][p.mision['paso']]; lugar = p.lugares[paso['lugar']]; p.teletransportar(lugar.x, lugar.y)\n_r = [lugar.x, lugar.y]")
    assert ambos(a, b, "True", "p.sv['mision_grupo'] is not None"), b.ev("dicho(4)")
    assert "Misión de %s, Morosos" % na in b.ev("dicho(10)")
    b("p.teletransportar(%r, %r); d0 = p.j.dinero" % (lx + 4, ly))
    assert ambos(a, b, "p.mision['generado'] and len(p.mision['enemigos']) > 0", "len(p.sv['ecos']) > 0", 15), (a.ev("p.mision and p.mision['generado']"), b.ev("len(p.sv['ecos'])"))
    b("[p.danar_persona(e, 500) for e in list(p.sv['ecos'].values())]")
    assert ambos(a, b, "p.mision is None or all(e.muerto for e in p.mision['enemigos']) or not p.mision['enemigos']", "True", 12)
    for _ in range(14):
        a("saltar_dialogos()\nif p.mision and app.pila[-1] is p: p._paso_hecho()\nframes(2)")
        b("frames(2)")
        if a.ev("'m04' in p.completadas"):
            break
    assert a.ev("'m04' in p.completadas")
    mitad = a.ev("mis['recompensa']['dinero'] // 2")
    # su parte, la mitad; puede llevar además lo que haya recogido del suelo
    assert ambos(a, b, "True", "p.j.dinero >= d0 + %d and 'Tu parte: %d euros' in dicho(12)" % (mitad, mitad), 10), b.ev("[p.j.dinero, d0, dicho(4)]")
    a("saltar_dialogos()"), b("saltar_dialogos()")
    s("hacer(lambda: [srv.po_limpiar(q, 'prueba', True) for q in list(srv.jugadores.values()) if not q.bot])")
    for g in (a, b):
        g("p.red.enviar({'t': 'grupo_salir'}); frames(4)")
    hecho.append("mision en grupo")
    # ---- corte de conexión: el juego nuevo espera y vuelve solo; el de la 1.7.0 vuelve al menú con un texto claro y entra otra vez
    colocar()
    for g in (a, b):
        g("p.j.dinero = 1357; p.j.banco = 0; p.sv_guardar(ya=True); frames(12)")
        s("hacer(lambda: srv._cortar(J(%r)))" % g.nombre)
        if g.version == "1.7.0":
            assert g.ev("hasta('app.partida is None', 12)"), g.ev("dicho(3)")
            assert "Se ha perdido la conexión con el servidor" in g.ev("dicho(4)")
            time.sleep(0.5)
            r = g.ev("entrar(%d, %r)" % (s.puerto, g.nombre))
            assert r["entra"] and r["tenia_partida"]
        else:
            assert g.ev("hasta('P() is not None and P().sv_espera is not None', 12)"), g.ev("dicho(3)")
            assert "Se ha cortado la conexión con el servidor" in g.ev("dicho(6)")
            assert g.ev("hasta('P() is not None and P().sv_espera is None and P().online_activo() and app.pila[-1] is P()', 40)"), g.ev("dicho(4)")
        mirar(g)
        assert g.ev("p.en_servidor and p.j.dinero") == 1357
    colocar()
    hecho.append("corte y reconexion")
    return hecho


def parar_y_volver(taller, s, a, b, cfg):
    """La parada del servidor con los dos dentro, y su vuelta en el mismo puerto y con los mismos datos."""
    na, nb = a.nombre, b.nombre
    nuevo_s = s.version == "nueva"
    a("p.j.dinero = 7001; p.j.banco = 0; frames(3)"), b("p.j.dinero = 8002; p.j.banco = 0; frames(3)")
    if not nuevo_s:                                       # el de la 1.7.0 no espera el último guardado: lo que vale es el que ya tenga
        a("p.sv_guardar(ya=True); frames(12)"), b("p.sv_guardar(ya=True); frames(12)")
    espiar(s, [na, nb])
    if nuevo_s:
        s("import threading\nh_parar = threading.Thread(target=lambda: parar(causa='reinicio', aviso=0), daemon=True)\nh_parar.start()")
    else:
        s("import threading\nh_parar = threading.Thread(target=parar, daemon=True)\nh_parar.start()")
    fin = time.time() + 20
    while time.time() < fin:
        a("frames(3)"), b("frames(3)")
        if not s.ev("h_parar.is_alive()"):
            break
    assert not s.ev("h_parar.is_alive()")
    cierres = {n: m for n, m in s.ev("enviados") if m["t"] == "cerrado"}
    assert set(cierres) == {na, nb}, cierres
    if nuevo_s:
        assert cierres[na]["causa"] == "reinicio" and "mantenimiento" in cierres[na]["motivo"]
        assert not [l for l in s.ev("lineas") if "No ha llegado a tiempo" in l], s.ev("lineas[-6:]")      # los dos juegos, también el antiguo, guardaron a tiempo
    for g in (a, b):
        if g.version == "1.7.0":
            # el juego antiguo oye el texto del cierre, que entiende, y vuelve al menú con su personaje guardado
            assert g.ev("hasta('app.partida is None', 12)"), g.ev("dicho(3)")
            dicho = g.ev("dicho(4)")
            assert "Tu personaje está guardado" in dicho and (("mantenimiento" in dicho) if nuevo_s else ("El servidor se ha cerrado" in dicho)), dicho
        else:
            # el nuevo se queda esperando: sabe que vuelve (o, con un servidor antiguo, lo trata como un corte)
            assert g.ev("hasta('P() is not None and P().sv_espera is not None', 12)"), g.ev("dicho(3)")
    datos = s.datos
    s.cerrar()
    for g, dinero in ((a, 7001), (b, 8002)):
        guardado = partida_guardada(datos, g.nombre)
        assert guardado is not None and guardado["jugador"]["dinero"] == dinero, (g.nombre, guardado["jugador"]["dinero"])
    # el servidor vuelve, en el mismo puerto y con sus datos
    s2 = taller.banco.servidor(s.version, "propio", datos=datos, **dict(cfg, puerto=s.puerto))
    s2.version = s.version
    taller.servidores.append(s2)
    assert s2.puerto == s.puerto
    for g, dinero in ((a, 7001), (b, 8002)):
        if g.version == "1.7.0":
            r = g.ev("entrar(%d, %r)" % (s2.puerto, g.nombre))
            assert r["entra"] and r["tenia_partida"]
        else:
            assert g.ev("hasta('P() is not None and P().sv_espera is None and P().online_activo() and app.pila[-1] is P()', 60)"), g.ev("dicho(4)")
            assert "Reconectado" in g.ev("dicho(8)") or "vuelto" in g.ev("dicho(8)"), g.ev("dicho(8)")
        mirar(g)
        assert g.ev("p.en_servidor and p.j.dinero") == dinero
    VE = "len(p.remotos) == 1 and next(iter(p.remotos.values())).visto"
    assert ambos(a, b, VE, VE, 15)
    return s2


CFG_JUNTOS = {"policia": "si", "patrullas": 0}


def test_1_servidor_nuevo_vacio_entra_primero_el_juego_de_la_1_7_0_y_luego_el_de_ahora(taller):
    """El primero que entra le da su mundo al servidor: aquí, el de la 1.7.0. Al llegar el de la 1.7.1, firmado, el
    servidor pasa a su mundo sin echar a nadie, y desde ahí juegan juntos con las mismas cifras."""
    s = taller.servidor("nueva", "vacio", **CFG_JUNTOS)
    assert s.info["version"] == "0" and s.info["huella"] == ""
    vieja, nueva = taller.juego("vieja"), taller.juego("nueva")
    r = entrar(vieja, s, "Vera")
    assert r["mundo"] == {"version": "1.7.0", "huella": H170, "igual": True} and r["admin"]
    assert s.ev("[srv.mundo['version'], len(srv.mundo['armas']), bool(srv.mundo.get('provisional'))]") == ["1.7.0", 37, False]
    assert s.ev("srv._nominas() is None")                  # el mundo de la 1.7.0 no trae contratos fijos: no hay nóminas
    r = entrar(nueva, s, "Nico")
    assert r["mundo"]["version"] == VERSION and r["mundo"]["igual"] and r["mundo"]["huella"] != H170
    assert s.ev("[srv.mundo['version'], len(srv.mundo['armas'])]") == [VERSION, 44] and s.ev("srv._nominas() is not None")
    assert any(f"El mundo pasa de la versión 1.7.0 a la {VERSION}" in l for l in s.ev("lineas"))
    # a la jugadora de la 1.7.0 no se la echa: se le dice que el servidor cambia de datos y sigue jugando
    assert vieja.ev(f"hasta(\"'pasa a los datos de la versión {VERSION}' in dicho(8)\", 8)"), vieja.ev("dicho(4)")
    assert "puede seguir jugando" in vieja.ev("dicho(8)") and vieja.ev("P().en_servidor")
    hecho = jugar_juntos(taller, s, vieja, nueva)
    assert hecho[-1] == "corte y reconexion" and "explosivo" in hecho, hecho
    parar_y_volver(taller, s, vieja, nueva, CFG_JUNTOS)


def test_2_servidor_nuevo_vacio_entra_primero_el_juego_de_ahora_y_luego_el_de_la_1_7_0(taller):
    """Al revés: el mundo lo trae el de la 1.7.1 y el servidor lo conserva. El de la 1.7.0 entra sin que se le pida nada
    (su mundo es el de una versión publicada) y se le dice, con nombres, qué tiene el servidor que su juego no tiene."""
    s = taller.servidor("nueva", "vacio", **CFG_JUNTOS)
    nueva, vieja = taller.juego("nueva"), taller.juego("vieja")
    r = entrar(nueva, s, "Nora")
    assert r["mundo"]["version"] == VERSION and r["mundo"]["igual"] and r["admin"]
    r = entrar(vieja, s, "Vito")
    assert r["mundo"]["version"] == VERSION and r["mundo"]["igual"] is False
    assert s.ev("[srv.mundo['version'], len(srv.mundo['armas'])]") == [VERSION, 44]      # el servidor no retrocede
    assert vieja.ev("hasta(\"'cosas que tu versión del juego no tiene' in dicho(10)\", 8)"), vieja.ev("dicho(5)")
    dicho = vieja.ev("dicho(10)")
    assert "7 armas" in dicho and "Escopeta de corredera" in dicho and "Un vehículo" in dicho and "el mismo para todos" in dicho, dicho
    hecho = jugar_juntos(taller, s, nueva, vieja)
    assert hecho[-1] == "corte y reconexion" and "explosivo" in hecho, hecho
    parar_y_volver(taller, s, nueva, vieja, CFG_JUNTOS)


def test_3_servidor_nuevo_con_su_mundo_y_los_dos_juegos(taller):
    """El servidor de ahora tal como se reparte, con su mundo.json: entran los dos, en cualquier orden."""
    s = taller.servidor("nueva", "propio", **CFG_JUNTOS)
    assert s.info["version"] == VERSION and "equivalencias" in s.info["funciones"] and "nominas" in s.info["funciones"]
    vieja, nueva = taller.juego("vieja"), taller.juego("nueva")
    r = entrar(vieja, s, "Vega")
    assert r["mundo"]["version"] == VERSION and r["mundo"]["igual"] is False and r["entra"]
    assert not s.ev("[l for l in lineas if 'El mundo pasa' in l]")
    r = entrar(nueva, s, "Nilo")
    assert r["mundo"]["igual"] is True
    hecho = jugar_juntos(taller, s, vieja, nueva)
    assert hecho[-1] == "corte y reconexion", hecho
    parar_y_volver(taller, s, vieja, nueva, CFG_JUNTOS)


def test_4_servidor_de_la_1_7_0_con_el_juego_de_ahora_y_el_de_la_1_7_0_a_la_vez(taller):
    """El servidor publicado de la 1.7.0, con su código: el juego de ahora entra, le trae su mundo firmado y juega con uno
    de la 1.7.0. Lo que ese servidor no sabe hacer, el juego nuevo lo dice en vez de fallar."""
    s = taller.servidor("vieja", "propio", **CFG_JUNTOS)
    assert s.info["version"] == "1.7.0" and "rol" not in s.info["funciones"]
    nueva, vieja = taller.juego("nueva"), taller.juego("vieja")
    r = entrar(nueva, s, "Nuria")
    assert r["entra"] and "equivalencias" not in r["funciones"] and "nominas" not in r["funciones"]
    assert s.ev("srv.mundo['version']") == VERSION         # el servidor antiguo adopta el mundo nuevo, firmado
    r = entrar(vieja, s, "Vasco")
    assert r["entra"] and r["mundo"]["igual"] is False
    # lo que no existe en ese servidor: el juego nuevo lo sabe y lo dice
    assert nueva.ev("[p.sv_sabe('rol'), p.sv_sabe('nominas'), p.sv_honrado('nominas'), p.sv_honrado('trato_prestigio')]") == [False, False, False, False]
    assert nueva.ev("p.hon_bloqueo('contrato')").startswith("En un servidor en línea no hay contratos fijos")
    hecho = jugar_juntos(taller, s, nueva, vieja)
    assert hecho[-1] == "corte y reconexion", hecho
    parar_y_volver(taller, s, nueva, vieja, CFG_JUNTOS)


def test_un_arma_que_el_mundo_del_servidor_no_conoce_cuenta_como_las_manos_para_todos(taller):
    """Si quien lleva el servidor no quiere mundos nuevos y el suyo es el de la 1.7.0, las armas de la 1.7.1 no existen
    allí: contra otros jugadores cuentan como ir con las manos, se le dice a quien las lleva, y nadie se cae."""
    for version in ("nueva", "vieja"):                     # con el servidor de ahora y con el de la 1.7.0, la misma regla
        s = taller.servidor(version, "vacio" if version == "nueva" else "propio", actualizar_mundo="no" if version == "vieja" else "firmado")
        vieja, nueva = taller.juego("vieja"), taller.juego("nueva")
        entrar(vieja, s, "Vera")
        s("hacer(lambda: srv.aplicar_config(dict(srv.cfg, actualizar_mundo='no')))") if version == "nueva" else None
        r = entrar(nueva, s, "Nico")
        assert r["entra"] and r["mundo"]["version"] == "1.7.0" and r["mundo"]["igual"] is False
        assert s.ev("srv.mundo['version']") == "1.7.0"
        assert "anterior a la tuya" in nueva.ev("dicho(8)")
        X, Y = 77.0, 81.0
        vieja("p.sv['protegido'] = 0; p.teletransportar(%r, %r); p.j.salud_max = 600.0; p.j.salud = 600.0" % (X, Y))
        nueva("p.sv['protegido'] = 0; p.teletransportar(%r, %r)" % (X + 8, Y))
        VE = "len(p.remotos) == 1 and next(iter(p.remotos.values())).visto and next(iter(p.remotos.values())).mapa == p.mundo.id"
        assert ambos(vieja, nueva, VE, VE)
        mirar(vieja), mirar(nueva)
        s("hacer(lambda: [setattr(q, 'protegido', 0) for q in srv.jugadores.values()])")
        nueva("p.dar_arma('fusil_semi', 200); p.j.arma = 'fusil_semi'; p.j.armas['fusil_semi']['cargador'] = 12; fj = p.fijar(True, callar=True)")
        for _ in range(8):
            nueva("p.j.t_ataque = 0; p.j.armas['fusil_semi']['cargador'] = 12; p.objetivo = fj; p.atacar(); frames(3)")
            time.sleep(0.4)
            vieja("frames(3)")
        assert vieja.ev("p.j.salud") == 600.0              # a ocho metros, con las manos no se llega: el fusil nuevo allí no existe
        assert nueva.ev("hasta(\"'no existe en la versión del juego con la que va este servidor' in dicho(12)\", 6)"), nueva.ev("dicho(6)")
        assert s.ev("J('Nico').arma") == "punos" and vieja.ev("app.partida is not None") and nueva.ev("app.partida is not None")
        taller.recoger()


def test_el_tope_de_dinero_es_el_mismo_para_las_dos_versiones(taller):
    """Con la cuenta del dinero puesta, lo que no se puede justificar se le retira igual a quien juega con la 1.7.0 que a
    quien juega con la 1.7.1: la cifra la pone el servidor, y cada juego la obedece y lo dice a su manera."""
    s = taller.servidor("nueva", "propio", economia="si", ganancia_hora=1200, ganancia_acumula=1, saldo_inicial=5000)
    vieja, nueva = taller.juego("vieja"), taller.juego("nueva")
    entrar(vieja, s, "Vera"), entrar(nueva, s, "Nico")
    quedan = {}
    for g in (vieja, nueva):
        g("frames(30)")
        s("hacer(lambda: setattr(J(%r), 'margen', 100000.0))" % g.nombre)
        g("p.j.dinero = 1000; p.j.banco = 0; frames(45)")
        assert s.ev("J(%r).saldo" % g.nombre) == 1000, s.ev("[J(%r).saldo, J(%r).dinero]" % (g.nombre, g.nombre))
        s("hacer(lambda: setattr(J(%r), 'margen', 300.0))" % g.nombre)      # le quedan 300 euros de margen
        g("p.j.dinero += 5000")
        assert g.ev("hasta('p.j.dinero < 6000', 10)"), g.ev("dicho(3)")
        g("frames(20)")
        quedan[g.version] = g.ev("p.j.dinero")
        assert 1300 <= quedan[g.version] <= 1320, quedan     # los 300 del margen, y lo poco que se recupera mientras tanto
        assert "retira" in g.ev("dicho(6)"), g.ev("dicho(4)")
        assert abs(s.ev("J(%r).saldo" % g.nombre) - quedan[g.version]) <= 2
    assert abs(quedan["1.7.0"] - quedan[VERSION]) <= 20, quedan


# ============================================================================ el personaje, de una versión a otra
def test_el_personaje_pasa_por_la_1_7_0_y_vuelve_a_la_1_7_1_sin_perder_nada(taller):
    """El mismo jugador entra con la 1.7.1, luego con la 1.7.0 y luego con la 1.7.1. El juego antiguo no conoce las armas
    nuevas (y fallaría con una en la mano) ni sabe guardar los campos nuevos: el servidor se lo da sin lo que no conoce y,
    cuando guarda, repone lo que faltaba. Lo que el jugador hace con la versión antigua, vale."""
    s = taller.servidor("nueva", "propio")
    nueva, vieja = taller.juego("nueva"), taller.juego("vieja")
    entrar(nueva, s, "Sara")
    nueva("""
for a in %r + ('pistola', 'escopeta'):
    p.dar_arma(a, 50)
p.j.arma = 'fusil_semi'
p.j.dinero, p.j.banco = 3210, 100
p.j.antecedentes = [{'d': 1, 'g': 2, 't': 'prueba', 'c': 999}]
p.j.titulos = {'oficios': {'s': 3, 'ok': 2}}
p.j.contrato = {}
p.j.creditos = [{'tipo': 'personal', 'lugar': '', 'cuota': 100, 'quedan': 5, 'prox': 9, 'impagos': 0, 'atraso': 0}]
p.j.empresa = {'bar_gaviota': {'nivel': 2, 'emp': 1, 'rep': 60.0}}
p.hon()['sospecha'] = 12.0
p.j.despensa = {'piso_centro': [{'id': 'pan', 'n': 2, 'cad': 0}]}
p.j.encima = [{'id': 'leche', 'n': 1, 'cad': 0}]
p.j.cocina_practica = {'tortilla': 3}
p.j.reconquista = {'marca': 1}
p.j.stats['turnos_contrato'] = 7
p.j.garajes['piso_centro'] = [{'modelo': 'furgon_asalto', 'salud': 100, 'nombre': 'Furgón nuevo'}, {'modelo': 'sedan', 'salud': 90, 'nombre': 'Sedán viejo'}]
p.j.campo_del_futuro = {'algo': [1, 2, 3]}
""" % (ARMAS_NUEVAS,))
    nueva("p.sv_guardar(ya=True); frames(12)")
    nueva("salir()")
    time.sleep(0.4)
    antes = json.loads(s.ev("hacer(lambda: srv.alm.cuenta_por_nombre('Sara')['partida'])"))
    assert s.ev("hacer(lambda: srv.alm.cuenta_por_nombre('Sara')['partida_juego'])") == VERSION
    assert antes["jugador"]["campo_del_futuro"] == {"algo": [1, 2, 3]}      # el servidor guarda también lo que no conoce
    nuevos = ("antecedentes", "titulos", "creditos", "empresa", "honra", "despensa", "encima", "cocina_practica", "reconquista", "contrato", "campo_del_futuro")
    assert all(k in antes["jugador"] for k in nuevos)
    # ---- entra con la 1.7.0: mismo personaje, sin lo que su juego no conoce, y avisado
    r = entrar(vieja, s, "Sara")
    assert r["tenia_partida"] and r["partida_de"] == VERSION
    assert vieja.ev("[p.j.arma, sorted(p.j.armas), p.j.dinero, p.j.banco]") == ["punos", ["escopeta", "pistola", "punos"], 3210, 100]
    assert vieja.ev("p.j.garajes") == {"piso_centro": [{"modelo": "sedan", "salud": 90, "nombre": "Sedán viejo"}]}
    assert vieja.ev("hasta(\"'no los pierdes' in dicho(10)\", 8)"), vieja.ev("dicho(5)")
    # cambiar de arma con la coma, que con un arma desconocida en la mano hacía fallar al juego de la 1.7.0, va bien
    vieja("for _ in range(5):\n    tecla(pygame.K_COMMA); frames(2)")
    assert vieja.ev("p.j.arma in ('punos', 'pistola', 'escopeta') and app.partida is p")
    # juega con la versión antigua: gasta, vende la escopeta, consigue un arma de las suyas, y guarda
    vieja("p.pagar(210); del p.j.armas['escopeta']; p.dar_arma('revolver', 12); p.j.arma = 'revolver'; p.j.garajes['piso_centro'].append({'modelo': 'moto', 'salud': 80, 'nombre': 'Moto'})")
    vieja("p.sv_guardar(ya=True); frames(12)")
    vieja("salir()")
    time.sleep(0.4)
    despues = json.loads(s.ev("hacer(lambda: srv.alm.cuenta_por_nombre('Sara')['partida'])"))
    jd = despues["jugador"]
    assert s.ev("hacer(lambda: srv.alm.cuenta_por_nombre('Sara')['partida_juego'])") == VERSION      # sigue siendo un personaje de la 1.7.1
    for k in nuevos:                                       # ni un campo nuevo perdido, y tal como estaban
        assert jd[k] == antes["jugador"][k], k
    assert jd["dinero"] == 3000 and jd["arma"] == "revolver"
    assert sorted(jd["armas"]) == sorted(ARMAS_NUEVAS + ("pistola", "punos", "revolver"))        # vuelven las seis nuevas; la escopeta vendida, no
    assert jd["armas"]["fusil_semi"] == antes["jugador"]["armas"]["fusil_semi"]
    assert [f["modelo"] for f in jd["garajes"]["piso_centro"]] == ["sedan", "moto", "furgon_asalto"]
    assert jd["stats"]["turnos_contrato"] == 7
    # ---- y vuelve con la 1.7.1: lo tiene todo, lo de antes y lo que hizo con la antigua
    r = entrar(nueva, s, "Sara")
    assert r["tenia_partida"]
    assert nueva.ev("[p.j.dinero, p.j.arma, sorted(p.j.armas) == sorted(%r + ('pistola', 'punos', 'revolver'))]" % (ARMAS_NUEVAS,)) == [3000, "revolver", True]
    assert nueva.ev("[p.j.antecedentes[0]['t'], p.j.titulos['oficios']['s'], p.j.creditos[0]['quedan'], p.j.empresa['bar_gaviota']['nivel'], p.j.honra['sospecha'], p.j.despensa['piso_centro'][0]['id'], "
                    "p.j.encima[0]['id'], p.j.cocina_practica['tortilla'], p.j.reconquista['marca']]") == ["prueba", 3, 5, 2, 12.0, "pan", "leche", 3, 1]
    assert nueva.ev("[f['modelo'] for f in p.j.garajes['piso_centro']]") == ["sedan", "moto", "furgon_asalto"]
    assert not [l for l in s.ev("lineas") if l.startswith("Error") or "no se ha podido atender" in l], s.ev("lineas[-5:]")


def test_el_personaje_tampoco_pierde_nada_en_un_servidor_de_la_1_7_0(taller):
    """Un servidor publicado de la 1.7.0 guarda el personaje tal cual llega, con los campos nuevos de la 1.7.1 dentro, y lo
    devuelve igual: lo que no conoce no lo toca."""
    s = taller.servidor("vieja", "propio")
    nueva = taller.juego("nueva")
    entrar(nueva, s, "Sole")
    nueva("p.j.dinero = 2222; p.j.titulos = {'oficios': {'s': 2, 'ok': 0}}; p.j.antecedentes = [{'d': 1, 'g': 1, 't': 'multa', 'c': 99}]; p.j.despensa = {'piso_centro': [{'id': 'pan', 'n': 1, 'cad': 0}]}\n"
          "p.dar_arma('rifle_palanca', 20)")
    nueva("p.sv_guardar(ya=True); frames(12)")
    nueva("salir()")
    time.sleep(0.4)
    r = entrar(nueva, s, "Sole")
    assert r["tenia_partida"]
    assert nueva.ev("[p.j.dinero, p.j.titulos, p.j.antecedentes[0]['t'], p.j.despensa['piso_centro'][0]['id'], 'rifle_palanca' in p.j.armas]") == [2222, {"oficios": {"s": 2, "ok": 0}}, "multa", "pan", True]


def test_dar_un_arma_nueva_a_quien_juega_con_la_1_7_0_no_la_pierde_nadie(taller):
    s = taller.servidor("nueva", "propio")
    nueva, vieja = taller.juego("nueva"), taller.juego("vieja")
    entrar(nueva, s, "Nora"), entrar(vieja, s, "Vito")
    for g, dx in ((nueva, 0), (vieja, 3)):
        g("p.sv['protegido'] = 0; p.teletransportar(%r, 90.0)" % (120.0 + dx))
    VE = "len(p.remotos) == 1 and next(iter(p.remotos.values())).visto"
    assert ambos(nueva, vieja, VE, VE)
    mirar(nueva), mirar(vieja)
    assert ambos(nueva, vieja, "abs(ro.tx - 123.0) < 1.5", "abs(ro.tx - 120.0) < 1.5")
    nueva("p.dar_arma('hacha', 0); del p.j.armas['hacha']; p.red.enviar({'t': 'dar', 'a': ro.id, 'clase': 'arma', 'id': 'hacha', 'n': 1})")
    assert ambos(nueva, vieja, "'hacha' in p.j.armas", "True", 8), nueva.ev("dicho(4)")       # el servidor se la devuelve
    assert "no tiene esa arma" in nueva.ev("dicho(8)") and "hacha" not in vieja.ev("sorted(p.j.armas)")
    # un arma que los dos conocen se da como siempre
    nueva("p.dar_arma('pistola', 0); del p.j.armas['pistola']; p.red.enviar({'t': 'dar', 'a': ro.id, 'clase': 'arma', 'id': 'pistola', 'n': 1})")
    assert ambos(nueva, vieja, "True", "'pistola' in p.j.armas", 8)


def test_el_vehiculo_nuevo_le_llega_al_juego_de_la_1_7_0_como_el_mas_parecido(taller):
    """Quien juega con la 1.7.0 no tiene el furgón nuevo: lo oye pasar y lo ve aparcado como el vehículo más parecido de
    los suyos, con su nombre, en vez de no ver nada. En el servidor sigue siendo lo que es."""
    s = taller.servidor("nueva", "propio")
    nueva, vieja = taller.juego("nueva"), taller.juego("vieja")
    entrar(nueva, s, "Nora"), entrar(vieja, s, "Vito")
    nueva("p.sv['protegido'] = 0; p.teletransportar(200.0, 130.0)"), vieja("p.sv['protegido'] = 0; p.teletransportar(206.0, 130.0)")
    VE = "len(p.remotos) == 1 and next(iter(p.remotos.values())).visto"
    assert ambos(nueva, vieja, VE, VE)
    mirar(nueva), mirar(vieja)
    eq = compat.modelo_equivalente("furgon_asalto", mundo()["modelos"], set(compat.CATALOGOS[H170]["modelos"]))
    assert eq in compat.CATALOGOS[H170]["modelos"]
    nueva("x0, y0 = p.pos(); v = p.crear_vehiculo('furgon_asalto', x0, y0, 0, 'aparcado'); v.cerrado = False; p._subir(v, True)")
    assert ambos(nueva, vieja, "getattr(v, 'id_red', None) is not None", "ro.veh == %r" % eq), vieja.ev("ro.veh")
    vid = nueva.ev("v.id_red")
    nueva("p.salir_vehiculo()")
    assert ambos(nueva, vieja, "p.j.veh is None", "any(getattr(w, 'id_red', None) == %d and w.modelo['id'] == %r for w in p.vehiculos)" % (vid, eq)), vieja.ev("p.sv['vehs']")
    assert s.ev("srv.vehiculos[%d]['modelo']" % vid) == "furgon_asalto"
    assert vieja.ev("frames(20) or app.partida is not None")


# ============================================================================ lo que sigue va con el servidor de ahora, en este proceso
@pytest.fixture
def banco(tmp_path):
    b = Banco(tmp_path)
    yield b
    b.parar()


def _mundo_con_mods():
    """El mundo de alguien que juega con mods: le falta un arma del servidor, y trae un arma y un vehículo propios."""
    d = copy.deepcopy(mundo())
    d["huella"] = hashlib.sha256(b"un mundo con mods").hexdigest()[:16]
    del d["armas"]["katana"]
    d["armas"]["tirachinas"] = {"nombre": "Tirachinas", "tipo": "fuego", "dano": 999, "alcance": 999, "cadencia": 0.01, "precision": 1, "radio": 0, "automatica": True}
    d["modelos"]["cohete"] = {"nombre": "Coche cohete", "salud": 9999, "vel_max": 500, "acel": 99, "freno": 12, "vuela": False}
    return d


def test_quien_trae_datos_que_no_se_pueden_comprobar_entra_y_se_le_dice_que_no_coincide(banco):
    """De serie no se rechaza a nadie por sus datos: quien lleva mods juega en lo común. El servidor arbitra con su mundo,
    así que lo que el mod cambia o añade no le da ventaja, y se le dice con nombres qué no coincide."""
    d = _mundo_con_mods()
    banco.mundo_cliente = (enlinea.mundo_canonico(d), "")
    assert opciones.POR_CLAVE["mundo_distinto"].defecto == "admitir"
    c = Cli(banco, "Con mods", huella=d["huella"], juego=mundo()["version"])
    assert c.ok and c.pidio_mundo and c.ok["mundo"]["igual"] is False
    assert c.ok["mundo"]["distinto"] == {"faltan": {"armas": ["Katana"], "vehiculos": []}, "sobran": {"armas": ["Tirachinas"], "vehiculos": ["Coche cohete"]}}
    aviso = c.leer("aviso", filtro=lambda m: "no coincide" in m["texto"] or "no conoce" in m["texto"])["texto"]
    assert "Katana" in aviso and "Tirachinas" in aviso and "Coche cohete" in aviso and "como ir con las manos" in aviso
    assert banco.srv.mundo["huella"] == mundo()["huella"]      # el servidor no toma el mundo de nadie sin firma
    assert d["huella"] not in banco.srv.mundos_conocidos and d["huella"] not in banco.srv.catalogos      # ni lo recuerda: vale para esa sesión
    # su arma de mod, que hace 999 de daño en su juego, contra otro jugador son las manos; y su coche, un utilitario
    x, y = lejos_de_todo()
    o = Cli(banco, "Otra")
    c.estado(x=x, y=y, ar="tirachinas", v="cohete")
    o.estado(x=x + 30, y=y)
    time.sleep(0.3)
    j = next(q for q in banco.srv.jugadores.values() if q.nombre == "Con mods")
    assert j.arma == "punos" and j.veh == "utilitario"
    assert o.leer("estados", filtro=lambda m: str(c.id) in m["e"] and "vi" in m["e"][str(c.id)])["e"][str(c.id)]["v"] == "utilitario"
    c.estado(x=x, y=y, ar="tirachinas")
    c.enviar({"t": "ataque", "a": o.id, "arma": "tirachinas"})
    assert c.leer("fallo")["lejos"] and o.nada("herido", 0.4)          # a treinta metros, con las manos no llega
    # y al revés: Otra le pega con la katana, que su juego no tiene: le llega con un arma que sí conoce, cuerpo a cuerpo
    o.estado(x=x + 1.5, y=y, ar="katana")
    banco.hacer(lambda: [setattr(q, "protegido", 0) for q in banco.srv.jugadores.values()])
    golpe = None
    for _ in range(12):
        o.enviar({"t": "ataque", "a": c.id, "arma": "katana"})
        time.sleep(0.6)
        try:
            golpe = c.leer("herido", 0.2)
            break
        except AssertionError:
            pass
    assert golpe and golpe["arma"] != "katana" and golpe["arma"] in d["armas"] and d["armas"][golpe["arma"]]["tipo"] == "cuerpo"
    # la segunda vez se le pide otra vez su mundo (no se guardó nada de él), y si no lo manda, entra igual
    banco.mundo_cliente = ("", "")
    otra_vez = Cli(banco, "Con mods 2", huella=d["huella"], juego=mundo()["version"])
    assert otra_vez.ok and otra_vez.pidio_mundo and "distinto" not in otra_vez.ok["mundo"]
    assert not [l for l in banco.lineas if l.startswith("Error")], banco.lineas[-5:]


def test_los_enemigos_de_una_mision_en_grupo_y_los_tiros_de_la_policia_llegan_con_armas_que_cada_juego_conoce(banco):
    x, y = lejos_de_todo()
    nueva = Cli(banco, "Nueva")
    vieja = Cli(banco, "Vieja", huella=H170, juego="1.7.0")
    conocidas = compat.CATALOGOS[H170]["armas"]
    nueva.estado(x=x, y=y)
    vieja.estado(x=x + 3, y=y)
    nueva.enviar({"t": "grupo_invitar", "a": vieja.id, "mision": "Prueba"})
    assert vieja.leer("grupo_invita")
    vieja.enviar({"t": "grupo_resp", "si": True})
    assert nueva.leer("grupo")
    lista = [{"k": 0, "nombre": "Uno", "salud": 60, "arma": "fusil_semi", "x": x, "y": y}, {"k": 1, "nombre": "Dos", "salud": 60, "arma": "pistola", "x": x, "y": y},
             {"k": 2, "nombre": "Tres", "salud": 60, "arma": ["rara"], "x": x, "y": y}, "basura"]
    nueva.enviar({"t": "grupo_msg", "d": {"que": "enemigos", "mapa": "puerto_bravo", "e": lista}})
    llega = vieja.leer("grupo_msg")["d"]["e"]
    assert llega[0]["arma"] in conocidas and llega[0]["arma"] != "fusil_semi" and llega[0]["nombre"] == "Uno"      # el enemigo, con un arma que su juego conoce
    assert llega[1] == lista[1] and llega[2] == lista[2] and llega[3] == "basura"                                # lo demás, tal cual, sin romperse con cosas raras
    nueva.enviar({"t": "grupo_msg", "d": {"que": "golpe", "k": 0, "n": 5}})
    assert vieja.leer("grupo_msg", filtro=lambda m: m["d"].get("que") == "golpe")["d"] == {"que": "golpe", "k": 0, "n": 5}
    # al revés no se cambia nada: quien tiene la versión del servidor recibe lo que es
    vieja.enviar({"t": "grupo_msg", "d": {"que": "enemigos", "mapa": "puerto_bravo", "e": lista[:1]}})
    assert nueva.leer("grupo_msg")["d"]["e"][0]["arma"] == "fusil_semi"
    # un agente de la policía del servidor que dispara con un arma nueva: cada uno la oye como un arma que tiene
    tiro = {"t": "po_disparo", "arma": "fusil_semi", "x": x, "y": y, "da": 0, "a": 0}
    banco.hacer(lambda: [banco.srv._enviar(banco.srv.jugadores[c.id], dict(tiro)) for c in (vieja, nueva)])
    assert vieja.leer("po_disparo")["arma"] in conocidas and nueva.leer("po_disparo")["arma"] == "fusil_semi"
    assert not [l for l in banco.lineas if l.startswith("Error") or "no se ha podido atender" in l], banco.lineas[-4:]


def test_quien_lleva_el_servidor_puede_pedir_solo_datos_de_verdad_o_una_version_minima(tmp_path):
    d = _mundo_con_mods()
    b = Banco(tmp_path, mundo_distinto="rechazar")
    try:
        b.mundo_cliente = (enlinea.mundo_canonico(d), "")
        assert "no puede comprobar" in Cli(b, "Con mods", huella=d["huella"], juego=mundo()["version"]).rechazo
        # el mundo de la 1.7.0 publicada lo conoce de fábrica: entra aunque no venga firmado, también con «rechazar»
        b.mundo_cliente = ("", "")
        v = Cli(b, "De la 1.7.0", huella=H170, juego="1.7.0")
        assert v.ok and not v.pidio_mundo and v.ok["mundo"]["distinto"]["faltan"]["armas"] and len(v.ok["mundo"]["distinto"]["faltan"]["armas"]) == 7
        # con la versión mínima, y solo con ella, se rechaza por versión, y se dice cuál hace falta
        b.hacer(b.srv.aplicar_config, dict(b.srv.cfg, version_minima="1.7.1"))
        from juego import ed25519
        import binascii
        for intento in range(3):                               # en este equipo la red local se traga a veces una conexión recién abierta
            c = Cli(b, "Otra de la 1.7.0", huella=H170, juego="1.7.0", entrar=False)
            try:
                r = c.leer(("reto", "rechazo"))
                if r["t"] == "reto":
                    c.enviar({"t": "firma", "f": binascii.hexlify(ed25519.firmar(c.semilla, ("puertobravo-entrada|" + r["n"]).encode("ascii"))).decode()})
                    r = c.leer("rechazo")
                break
            except AssertionError:
                if intento == 2:
                    raise
        assert r["codigo"] == "version" and r["minima"] == "1.7.1" and "1.7.0" in r["motivo"]
    finally:
        b.parar()


def test_un_servidor_sin_mundo_toma_de_momento_el_del_primero_aunque_no_venga_firmado(tmp_path):
    """El primero que entra le pasa el juego al servidor. Si lleva mods (o juega desde el código) su mundo no viene firmado:
    el servidor lo usa mientras no haya otro, lo dice en su registro y lo cambia por el primero firmado que llegue."""
    from test_servidor_versiones import EDITOR, mundo_de
    from juego import ed25519
    import binascii
    b = Banco(tmp_path, de_disco=False)
    try:
        b.hacer(lambda: b.srv._poner_mundo(dict(nucleo.MUNDO_VACIO), guardar=False))
        b.srv.claves_publicas = (binascii.hexlify(ed25519.publica(EDITOR)).decode(),)
        d = _mundo_con_mods()
        b.mundo_cliente = (enlinea.mundo_canonico(d), "")
        c = Cli(b, "Primero", huella=d["huella"], juego=mundo()["version"])
        assert c.ok and c.pidio_mundo and c.ok["mundo"]["igual"] and b.srv.mundo["huella"] == d["huella"] and b.srv.mundo["provisional"] is True
        assert any("no viene firmado" in l for l in b.lineas)
        assert d["huella"] not in b.srv.catalogos              # de un mundo sin firma no se guarda nada para otras veces
        # llega alguien con un mundo firmado, aunque sea de una versión anterior: desde ahora manda ese
        texto, h_firmado, firma_m = mundo_de("0.9.0", nuevo=False)
        b.mundo_cliente = (texto, firma_m)
        f = Cli(b, "Firmado", huella=h_firmado, juego="0.9.0", firmado=True)
        assert f.ok and f.ok["mundo"]["igual"] and b.srv.mundo["huella"] == h_firmado and not b.srv.mundo.get("provisional")
        assert "pasa a los datos de la versión 0.9.0" in c.leer("aviso", filtro=lambda m: "0.9.0" in m["texto"])["texto"]
        assert b.srv.jugadores[c.id].dentro                    # y al primero no se le echa
        # quien llega primero no puede dejar un mundo trucado diciendo que es el de una versión de verdad: si después entra
        # alguien con ese mismo mundo, firmado, el provisional se cambia por el firmado aunque digan la misma huella
        b.hacer(lambda: b.srv._poner_mundo(dict(nucleo.MUNDO_VACIO), guardar=False))
        trucado = json.loads(texto)
        trucado["armas"]["pistola"]["dano"] = 9999
        b.mundo_cliente = (enlinea.mundo_canonico(trucado), "")
        t = Cli(b, "Tramposo", huella=h_firmado, juego="0.9.0")
        assert t.ok and b.srv.mundo["provisional"] is True and b.srv.mundo["armas"]["pistola"]["dano"] == 9999
        b.mundo_cliente = (texto, firma_m)
        g = Cli(b, "De verdad", huella=h_firmado, juego="0.9.0", firmado=True)
        assert g.ok and g.pidio_mundo and not b.srv.mundo.get("provisional") and b.srv.mundo["armas"]["pistola"]["dano"] == mundo()["armas"]["pistola"]["dano"]
        # con la opción de no aceptar mundos, un servidor vacío no toma ninguno y lo dice claro
        b.hacer(lambda: b.srv._poner_mundo(dict(nucleo.MUNDO_VACIO), guardar=False))
        b.hacer(b.srv.aplicar_config, dict(b.srv.cfg, actualizar_mundo="no"))
        b.mundo_cliente = (enlinea.mundo_canonico(d), "")
        assert "todavía no tiene los datos del juego" in Cli(b, "Tercero", huella=d["huella"], juego=mundo()["version"]).rechazo
    finally:
        b.parar()


def test_los_equivalentes_se_eligen_por_clase_y_por_parecido_y_el_catalogo_de_la_1_7_0_es_el_publicado():
    m = mundo()
    cat = compat.en_uso(compat.CATALOGOS[H170])
    assert len(cat["armas"]) == 37 and len(cat["modelos"]) == 63
    try:                                                   # si el banco está, que el catálogo escrito sea el del mundo.json publicado
        with open(os.path.join(bv.carpeta_170(), "servidor", "mundo.json"), encoding="utf-8") as f:
            publicado = json.load(f)
        assert publicado["huella"] == H170 and compat.catalogo_de(publicado) == dict(compat.CATALOGOS[H170])
    except bv.SinBanco:
        pass
    for arma in ARMAS_NUEVAS:
        eq = compat.arma_equivalente(arma, m["armas"], cat["armas"])
        assert eq in cat["armas"] and m["armas"][eq]["tipo"] == m["armas"][arma]["tipo"], (arma, eq)
    assert compat.arma_equivalente("escopeta_corredera", m["armas"], cat["armas"]) in ("escopeta", "escopeta_combate", "vo_escopeta")
    assert compat.arma_equivalente("lanzagranadas", m["armas"], cat["armas"]) in ("lanzacohetes", "granada")
    assert compat.arma_equivalente("no_existe", m["armas"], cat["armas"]) == "punos"
    eq = compat.modelo_equivalente("furgon_asalto", m["modelos"], cat["modelos"])
    assert eq in cat["modelos"] and not m["modelos"][eq]["vuela"]
    assert compat.modelo_equivalente("no_existe", m["modelos"], cat["modelos"]) == "utilitario"
    # lo que se dice al jugador no lleva palabras de programador
    le_falta, sobra = compat.diferencias(m, cat)
    texto = compat.texto_diferencias(le_falta, sobra)
    assert len(le_falta["armas"]) == 7 and le_falta["vehiculos"] and not sobra["armas"] and "7 armas" in texto and "y 3 más" in texto
    for palabra in ("huella", "protocolo", "json", "catálogo", "id ", "versión del protocolo"):
        assert palabra not in texto.lower(), palabra
    assert compat.texto_diferencias({"armas": [], "vehiculos": []}, {"armas": [], "vehiculos": []}) == ""


def test_fundir_y_adaptar_el_personaje_no_inventan_ni_pierden_nada():
    cat = compat.en_uso(compat.CATALOGOS[H170])
    vieja = {"version": 3, "veh": {"modelo": "furgon_asalto"}, "extra_raiz": [1], "momento": 5,
             "jugador": {"dinero": 10, "arma": "hacha", "armas": {"hacha": {"c": 1}, "pistola": {"c": 2}, "bate": {}}, "titulos": {"a": 1},
                         "garajes": {"g1": [{"modelo": "furgon_asalto"}, {"modelo": "sedan"}], "g2": [{"modelo": "furgon_asalto"}]}}}
    copia = copy.deepcopy(vieja)
    dada = compat.adaptar_partida(vieja, cat)
    assert vieja == copia                                  # el guardado no se toca
    assert dada["jugador"]["arma"] == "bate" and sorted(dada["jugador"]["armas"]) == ["bate", "pistola"] and "veh" not in dada      # en la mano, un arma que sí tiene
    assert dada["jugador"]["garajes"] == {"g1": [{"modelo": "sedan"}], "g2": []} and dada["jugador"]["titulos"] == {"a": 1}
    assert compat.adaptar_partida(vieja, None) is vieja and compat.adaptar_partida(None, cat) is None
    limpia = {"jugador": {"arma": "pistola", "armas": {"pistola": {}}}}
    assert compat.adaptar_partida(limpia, cat) is limpia   # si no hay nada que apartar, ni se copia
    # el juego antiguo guarda: sin los campos nuevos, sin el bate (lo vendió) y con un arma suya nueva
    nueva = {"version": 3, "momento": 9, "jugador": {"dinero": 4, "arma": "navaja", "armas": {"pistola": {"c": 9}, "navaja": {}}, "garajes": {"g1": [{"modelo": "sedan"}, {"modelo": "moto"}]}}}
    f = compat.fundir_partida(nueva, vieja, cat)
    assert f["jugador"]["dinero"] == 4 and f["jugador"]["titulos"] == {"a": 1} and f["extra_raiz"] == [1] and f["momento"] == 9 and "veh" not in f
    assert sorted(f["jugador"]["armas"]) == ["hacha", "navaja", "pistola"] and f["jugador"]["armas"]["pistola"] == {"c": 9} and f["jugador"]["arma"] == "navaja"
    assert f["jugador"]["garajes"] == {"g1": [{"modelo": "sedan"}, {"modelo": "moto"}, {"modelo": "furgon_asalto"}]}      # el garaje g2 ya no lo tiene
    assert compat.fundir_partida({"jugador": "raro"}, vieja, cat)["jugador"] == "raro" and compat.fundir_partida("x", vieja, cat) == "x"


def test_el_servidor_guarda_campos_que_no_conoce_y_tiene_un_tope_de_tamano(banco):
    a = Cli(banco, "Ana")
    a.estado()
    p = {"version": 3, "jugador": {"dinero": 5, "banco": 0, "cosa_que_no_existe": {"a": [1, {"b": None}]}, "honra": {"v": 1}}, "raiz_rara": "x"}
    a.enviar({"t": "guardar", "p": p, "ya": True})
    assert a.leer("guardado")
    guardada = json.loads(banco.hacer(lambda: banco.srv.alm.cuenta_por_nombre("Ana")["partida"]))
    assert guardada == p
    # un personaje descomunal no se guarda, se dice, y queda el anterior
    gordo = {"version": 3, "jugador": {"dinero": 5, "relleno": "x" * (nucleo.MAX_LINEA - 2000)}, "mas": "y" * 4000}
    a.enviar({"t": "guardar", "p": gordo, "ya": True})
    try:
        assert "ocupa demasiado" in a.leer("aviso", espera=4)["texto"]
        assert json.loads(banco.hacer(lambda: banco.srv.alm.cuenta_por_nombre("Ana")["partida"])) == p
    except AssertionError:
        # si el mensaje entero pasa del tamaño de línea, el servidor corta antes de leerlo: tampoco se guarda
        assert json.loads(banco.hacer(lambda: banco.srv.alm.cuenta_por_nombre("Ana")["partida"])) == p
    a.cerrar()
    time.sleep(0.3)
    de_vuelta = Cli(banco, "Ana", semilla=a.semilla)
    assert de_vuelta.ok["partida"] == p


def test_una_base_de_datos_anterior_gana_sola_las_columnas_nuevas(tmp_path):
    ruta = str(tmp_path / "puertobravo.db")
    db = sqlite3.connect(ruta)
    db.executescript("CREATE TABLE cuentas (id INTEGER PRIMARY KEY AUTOINCREMENT, pub TEXT UNIQUE NOT NULL, nombre TEXT UNIQUE NOT NULL, creada REAL, visto REAL, "
                     "partida TEXT, recompensa INTEGER DEFAULT 0, bajas INTEGER DEFAULT 0, caidas INTEGER DEFAULT 0, vetado INTEGER DEFAULT 0, admin INTEGER DEFAULT 0, "
                     "pendiente TEXT DEFAULT '[]', dia_salida INTEGER DEFAULT 0, saldo INTEGER, misiones TEXT DEFAULT '[]', juego TEXT DEFAULT '');")
    from juego import ed25519                              # la clave pública de «Ana», como la saca el cliente de pruebas
    import binascii
    semilla = hashlib.sha256(b"semilla-Ana").digest()
    pub = binascii.hexlify(ed25519.publica(semilla)).decode()
    vieja = {"version": 3, "jugador": {"dinero": 9, "banco": 0, "arma": "fusil_semi", "armas": {"fusil_semi": {"cargador": 1, "reserva": 2}, "punos": {}}, "titulos": {"x": 1}}}
    db.execute("INSERT INTO cuentas (pub, nombre, creada, visto, partida, juego) VALUES (?,?,?,?,?,?)", (pub, "Ana", 1.0, 1.0, json.dumps(vieja), "1.7.1"))
    db.commit()
    db.close()
    b = Banco(tmp_path)
    try:
        columnas = b.hacer(lambda: [f[1] for f in b.srv.alm.db.execute("PRAGMA table_info(cuentas)").fetchall()])
        assert "partida_juego" in columnas and "contrato" in columnas
        # entra con la 1.7.0 un personaje que se guardó con la 1.7.1 antes de que el servidor lo apuntara: lo deduce de su última entrada
        a = Cli(b, "Ana", huella=H170, juego="1.7.0")
        assert a.ok and a.ok["partida"]["jugador"]["arma"] == "punos" and sorted(a.ok["partida"]["jugador"]["armas"]) == ["punos"] and a.ok["partida_de"] == "1.7.1"
        a.estado()
        a.enviar({"t": "guardar", "p": {"version": 3, "jugador": {"dinero": 3, "banco": 0, "arma": "punos", "armas": {"punos": {}}}}, "ya": True})
        assert a.leer("guardado")
        g = json.loads(b.hacer(lambda: b.srv.alm.cuenta_por_nombre("Ana")["partida"]))
        assert g["jugador"]["titulos"] == {"x": 1} and "fusil_semi" in g["jugador"]["armas"] and g["jugador"]["dinero"] == 3
    finally:
        b.parar()


# ============================================================================ nóminas: paga el servidor, y no se deja engañar
def _con_nominas(tmp_path, **cfg):
    base = {"economia": "si", "ganancia_hora": 0, "saldo_inicial": 1000}      # sin margen por hora: solo vale lo que justifica el servidor
    base.update(cfg)
    return Banco(tmp_path, **base)


def _dia(b, n):
    b.hacer(lambda: setattr(b.srv, "dia", b.srv.dia + n))


def test_la_nomina_la_paga_el_servidor_con_sus_cifras_y_no_se_puede_fabricar_dinero(tmp_path):
    b = _con_nominas(tmp_path)
    try:
        emp = b.srv.empleos
        assert emp["periodo"] == 7 and emp["prima"] == 10 and emp["puestos"]["hosteleria"][0] == [3, 220]
        a = Cli(b, "Ana")
        assert a.ok["servidor"]["nominas"] is True and a.ok["contrato"] == {"periodo": 7, "tope": 1500, "turnos_dia": 3}
        a.estado(di=1000, ba=0)
        j = b.srv.jugadores[a.id]
        dia0 = b.srv.dia
        # un empleo que no existe, no
        a.enviar({"t": "contrato", "que": "firmar", "empleo": "ministro"})
        assert a.leer("contrato")["que"] == "no"
        # firma mintiendo sobre el puesto: se entra por abajo (o un escalón más, con carta), nunca por arriba
        a.enviar({"t": "contrato", "que": "firmar", "empleo": "hosteleria", "puesto": 3})
        c = a.leer("contrato")
        assert c["que"] == "firmado" and c["c"]["puesto"] == 0 and c["c"]["fin"] == dia0 + 7 and c["c"]["turnos"] == 0
        # cobrar antes de tiempo, las veces que sea: nada
        for _ in range(3):
            a.enviar({"t": "contrato", "que": "cobrar", "buena": True, "n": 999999})
            r = a.leer("nomina")
            assert r["n"] == 0 and r["faltan"] == 7
        # turnos: no más de tres al día, mande los que mande
        for _ in range(10):
            a.enviar({"t": "contrato", "que": "turno"})
        time.sleep(0.3)
        assert j.contrato["t"] == 3
        _dia(b, 1)
        a.enviar({"t": "contrato", "que": "turno"})
        time.sleep(0.2)
        assert j.contrato["t"] == 4
        # llega el día de cobro: paga el servidor, su cifra más la prima del mundo, diga lo que diga el juego
        _dia(b, 6)
        a.enviar({"t": "contrato", "que": "cobrar", "buena": True, "n": 999999, "sueldo": 50000})
        r = a.leer("nomina")
        assert r["n"] == 220 + 22 and r["turnos"] == 4 and r["cupo"] == 3 and r["c"]["fin"] == b.srv.dia + 7 and r["c"]["turnos"] == 0
        assert any("Nómina de Ana: 242 euros" in l for l in b.lineas)
        # ese dinero queda justificado: aparece en su juego y el servidor lo reconoce, sin tope por hora
        a.estado(di=1000, ba=242)
        time.sleep(0.2)
        assert j.saldo == 1242 and a.nada("saldo", 0.3)
        # repetir el cobro no da nada
        a.enviar({"t": "contrato", "que": "cobrar", "buena": True})
        assert a.leer("nomina")["n"] == 0
        # y decir que has cobrado más de lo que te han pagado, tampoco: el servidor lo retira
        a.estado(di=1000, ba=5242)
        r = a.leer("saldo")
        assert r["quita"] == 5000 and j.saldo == 1242
        a.estado(di=1000, ba=242)
        # salir y volver a entrar no reinicia nada: el contrato y su fecha de cobro siguen en el servidor
        a.cerrar()
        time.sleep(0.4)
        a2 = Cli(b, "Ana", semilla=a.semilla)
        assert a2.ok["contrato"]["empleo"] == "hosteleria" and a2.ok["contrato"]["fin"] == b.srv.dia + 7 and a2.ok["contrato"]["turnos"] == 0
        a2.estado(di=1000, ba=242)
        a2.enviar({"t": "contrato", "que": "cobrar", "buena": True})
        assert a2.leer("nomina")["n"] == 0
        # firmar otra vez el mismo empleo no empieza un periodo nuevo
        a2.enviar({"t": "contrato", "que": "firmar", "empleo": "hosteleria"})
        assert a2.leer("contrato", filtro=lambda m: m["que"] == "firmado")["c"]["fin"] == b.srv.dia + 7
        # un periodo a medias cobra la parte que toca; sin turnos, nada; y un mal periodo que el propio juego da por perdido, nada
        a2.enviar({"t": "contrato", "que": "turno"})
        time.sleep(0.25)
        _dia(b, 7)
        a2.enviar({"t": "contrato", "que": "cobrar"})
        assert a2.leer("nomina")["n"] == 220 // 3
        _dia(b, 7)
        a2.enviar({"t": "contrato", "que": "cobrar", "buena": True})
        assert a2.leer("nomina")["n"] == 0
        for _ in range(3):
            a2.enviar({"t": "contrato", "que": "turno"})
        time.sleep(0.25)
        _dia(b, 7)
        a2.enviar({"t": "contrato", "que": "cobrar", "mala": True})
        assert a2.leer("nomina")["n"] == 0
        # ascensos: de uno en uno, y solo tras un periodo cobrado con el cupo cumplido
        j2 = b.srv.jugadores[a2.id]
        a2.enviar({"t": "contrato", "que": "ascenso"})
        assert a2.leer("contrato", filtro=lambda m: m["que"] == "puesto")["c"]["puesto"] == 1      # el periodo anterior tenía el cupo
        for _ in range(4):
            a2.enviar({"t": "contrato", "que": "ascenso"})
            assert a2.leer("contrato", filtro=lambda m: m["que"] == "puesto")["c"]["puesto"] == 1  # y no sube más por pedirlo
        assert j2.contrato["p"] == 1
        # dejarlo lo borra
        a2.enviar({"t": "contrato", "que": "dejar"})
        time.sleep(0.2)
        assert j2.contrato == {} and b.hacer(lambda: b.srv.alm.cuenta_por_nombre("Ana")["contrato"]) == ""
        a2.enviar({"t": "contrato", "que": "cobrar"})
        assert a2.leer("contrato", filtro=lambda m: m["que"] == "no")
        assert not [l for l in b.lineas if l.startswith("Error") or "no se ha podido atender" in l], b.lineas[-5:]
    finally:
        b.parar()


def test_el_dueno_pone_el_tope_de_la_nomina_o_las_quita_y_un_mundo_anterior_no_las_tiene(tmp_path):
    b = _con_nominas(tmp_path, nomina_max=100, nomina_turnos_dia=1)
    try:
        a = Cli(b, "Ana")
        a.estado(di=1000, ba=0)
        a.enviar({"t": "contrato", "que": "firmar", "empleo": "emergencias"})
        assert a.leer("contrato")["c"]["tope"] == 100
        for _ in range(3):
            a.enviar({"t": "contrato", "que": "turno"})
            a.enviar({"t": "contrato", "que": "turno"})
            time.sleep(0.25)
            _dia(b, 1)
        _dia(b, 7)
        a.enviar({"t": "contrato", "que": "cobrar", "buena": True})
        r = a.leer("nomina")
        assert r["turnos"] == 3 and r["n"] == 100           # un turno por día, y la paga, la del tope
        # sin nóminas: no hay contratos, y el juego lo sabrá al entrar
        b.hacer(b.srv.aplicar_config, dict(b.srv.cfg, nominas="no"))
        a.enviar({"t": "contrato", "que": "cobrar"})
        assert a.leer("contrato", filtro=lambda m: m["que"] == "no")
        o = Cli(b, "Otro")
        assert o.ok["servidor"]["nominas"] is False and o.ok["contrato"] is None
        # con el mundo de una versión que no trae contratos (la 1.7.0), tampoco
        b.hacer(b.srv.aplicar_config, dict(b.srv.cfg, nominas="si"))
        viejo = {k: v for k, v in mundo().items() if k != "empleos"}
        b.hacer(lambda: b.srv._poner_mundo(viejo, guardar=False))
        assert b.srv.empleos is None and Cli(b, "Tercero").ok["servidor"]["nominas"] is False
        # un mundo que mienta con sueldos enormes o con basura no rompe nada ni paga más que el tope
        assert compat.empleos_validos({"empleos": {"periodo": 0, "prima": 900, "puestos": {"x": [[0, 10 ** 12]]}}}) == {"periodo": 1, "prima": 100, "puestos": {"x": [[1, 10 ** 12]]}}
        for basura in ({}, {"empleos": 3}, {"empleos": {"periodo": "x", "puestos": {}}}, {"empleos": {"periodo": 7, "puestos": {"x": "no"}}}):
            assert compat.empleos_validos(basura) is None
    finally:
        b.parar()


def test_el_juego_exporta_los_contratos_y_el_mundo_del_servidor_esta_al_dia():
    m = enlinea.mundo_servidor()
    assert m["empleos"]["periodo"] == 7 and m["empleos"]["prima"] == 10 and len(m["empleos"]["puestos"]) == 5
    assert compat.empleos_validos(m) == m["empleos"]
    assert max(s for lista in m["empleos"]["puestos"].values() for _, s in lista) * 1.1 <= opciones.POR_CLAVE["nomina_max"].defecto      # el tope de serie no recorta ninguna nómina del juego
    with open(os.path.join(RAIZ, "servidor", "mundo.json"), encoding="utf-8") as f:
        assert json.load(f) == m, "servidor/mundo.json no está al día: ejecuta herramientas/exportar_mundo_servidor.py"


# ============================================================================ el juego de ahora, conectado: la vida honrada
@pytest.fixture
def conectado(robot, tmp_path):
    from test_enlinea import entrar as entrar_juego
    b = _con_nominas(tmp_path, ganancia_hora=30000)
    p = entrar_juego(robot, b, "Ana")
    yield robot, b, p
    if robot.app.partida is not None:
        robot.app.partida.sv_salir()
        robot.app.partida.desconectar_online()
    b.parar()


def _pasar(robot, n=12):
    for _ in range(0, n, 3):
        robot.frames(3)
        time.sleep(0.03)


def _hasta(cond, robot, seg=8.0):
    fin = time.time() + seg
    while time.time() < fin:
        _pasar(robot, 3)
        if cond():
            return True
    return False


def test_contrato_fijo_conectado_el_servidor_cuenta_los_turnos_y_paga_la_nomina(conectado):
    robot, b, p = conectado
    j = p.j
    sj = b.srv.jugadores[p.red.id]
    assert p.sv_honrado("nominas") and p.sv_honrado("trato_prestigio") and p.hon_bloqueo("contrato") == ""
    assert "no hay créditos" in p.hon_bloqueo() and p.hon_credito_motivo() == p.hon_bloqueo() and not p.hon_pedir_credito(500)      # lo demás sigue sin existir
    c = next(x for x in p.hon_empleos() if x["id"] == "hosteleria")
    assert p.hon_firma_motivo(c) == "" and p.hon_firmar(c)
    assert _hasta(lambda: sj.contrato.get("e") == "hosteleria", robot)
    assert j.contrato["fin"] == b.srv.dia + 7 == sj.contrato["fin"]
    # tres turnos de su contrato: los cuenta el servidor
    for _ in range(3):
        p.hon_turno("jornada:camarero")
    assert _hasta(lambda: sj.contrato["t"] == 3, robot) and j.contrato["turnos"] == 3
    p.hon_turno("jornada:soldador")                        # una jornada que no es de su contrato no cuenta
    _pasar(robot)
    assert sj.contrato["t"] == 3
    # pasa el periodo: el día lo cambia el servidor, la evaluación la hace el juego y la nómina la paga el servidor
    banco0, margen = j.banco, sj.margen
    b.hacer(lambda: (setattr(b.srv, "dia", b.srv.dia + 6), setattr(b.srv, "reloj", 1439.7)))
    assert _hasta(lambda: p.dia == b.srv.dia and j.banco > banco0, robot, 14), (p.dia, b.srv.dia, robot.dicho()[-300:])
    cobrado = j.banco - banco0
    assert cobrado in (220, 242) and "El servidor te ingresa la nómina en el banco: %d euros" % cobrado in robot.dicho()
    assert j.contrato["turnos"] == 0 and j.contrato["fin"] == b.srv.dia + 7 and j.contrato["periodos"] == 1
    # el servidor lo da por bueno sin tocar el margen por hora, y no retira nada
    assert _hasta(lambda: sj.saldo == j.dinero + j.banco and sj.credito == 0, robot), (sj.saldo, j.dinero + j.banco, sj.credito)
    assert sj.margen >= margen - 1 and j.banco - banco0 == cobrado and "retira" not in robot.dicho()[-400:]
    # guardar, salir y volver: el contrato sigue, en el juego y en el servidor
    p.sv_guardar(ya=True)
    _pasar(robot)
    p.sv_salir()
    time.sleep(0.4)
    from test_enlinea import entrar as entrar_juego
    p2 = entrar_juego(robot, b, "Ana")
    assert p2.j.contrato["empleo"] == "hosteleria" and p2.j.contrato["fin"] == b.srv.dia + 7 and p2.j.contrato["periodos"] == 1
    # dimitir lo borra también en el servidor
    p2.hon_dimitir()
    sj2 = b.srv.jugadores[p2.red.id]
    assert _hasta(lambda: sj2.contrato == {}, robot) and not p2.j.contrato


def test_conectado_las_tiendas_tratan_segun_el_prestigio_si_el_servidor_quiere_y_hay_antecedentes(conectado):
    robot, b, p = conectado
    j = p.j
    p.cfg["consecuencias"] = "exigente"                    # la opción de cada uno no cuenta en un servidor: decide el servidor
    assert p.hon_nivel() == 0
    j.ciudadania = 90
    assert p.hon_trato() == 0.9
    j.ciudadania = 50
    assert p.hon_trato() == 0.95
    j.ciudadania = 2
    assert p.hon_trato() == round(1 + 12 * 0.6 / 100, 3)   # el recargo, como en suave, tenga cada uno el nivel que tenga
    p.sv["info"]["trato_prestigio"] = False
    assert p.hon_trato() == 1.0
    # los antecedentes se apuntan y cuentan para los empleos de confianza; lo demás del sistema sigue apagado
    assert p.hon_con_antecedentes() and p.hon_antecedente(3, "Detención de prueba") is not None and p.hon_graves()
    conf = next(x for x in p.hon_empleos() if x.get("confianza"))
    j.ciudadania = 90
    assert "antecedentes" in p.hon_firma_motivo(conf)
    h = p.hon()
    assert not p.hon_impuestos() and h.get("sospecha", 0) == 0 and h.get("negro", 0) == 0
    p.hon_negro(5000)
    p.t_honrado = 0.0
    p.actualizar_honrado(1.0)
    assert p.hon().get("negro", 0) == 0 and not p.hon_fiar(99999)
    from juego import menus_honrado as MH
    assert MH.opciones_negocio(p, next(l for l in p.mundo.lugares.values() if l.tipo == "negocio"), lambda: None) == []
    MH.menu_vida(p)
    textos = " ".join(o.texto() if callable(o.texto) else o.texto for o in robot.app.pila[-1].opciones)
    assert "lo decide el servidor, igual para todos" in textos and "El buen camino: es una historia para jugar sin conexión" in textos
    robot.app.cerrar(robot.app.pila[-1])


def test_al_salir_del_servidor_no_queda_rastro_al_jugar_solo(conectado):
    """Lo que el servidor apaga o cambia mientras estás dentro vuelve a su sitio al salir: opciones, niveles y avisos."""
    robot, b, p = conectado
    app = robot.app
    app.cfg["consecuencias"] = "normal"
    assert p.hon_nivel() == 0 and p.en_servidor
    p.sv_salir()
    assert not p.en_servidor and app.cfg.temporales == {} and p.red is None
    assert p.hon_nivel() == 2 and p.hon_bloqueo() == "" and p.hon_bloqueo("contrato") == "" and not p.sv_honrado("nominas") and p.hon_impuestos()
    # un contrato firmado ahora, sin conexión, no manda nada a ningún sitio ni falla
    c = next(x for x in p.hon_empleos() if x["id"] == "comercio")
    assert p.hon_firmar(c) and p.j.contrato["empleo"] == "comercio"
    p.hon_turno("jornada:reponedor")
    assert p.j.contrato["turnos"] == 1
    assert p._hon_nomina(100) == 100                       # sin conexión, la nómina la ingresa el juego


def test_con_un_servidor_que_no_lleva_nominas_el_juego_lo_dice_y_no_envia_nada(conectado):
    """Como un servidor de la 1.7.0, o uno cuyo dueño las ha quitado: no hay contratos fijos, y el juego lo explica."""
    robot, b, p = conectado
    p.sv["info"]["nominas"] = False
    p.sv["info"]["trato_prestigio"] = False
    enviados = []
    real = p.red.enviar
    p.red.enviar = lambda m: (enviados.append(m), real(m))[1]
    c = next(x for x in p.hon_empleos() if x["id"] == "hosteleria")
    assert p.hon_bloqueo("contrato").startswith("En un servidor en línea no hay contratos fijos") and not p.hon_firmar(c)
    p.j.contrato = {"empleo": "hosteleria", "puesto": 0, "jefe": "X", "caracter": "justo", "desde": 1, "fin": 1, "turnos": 0, "calidad": [], "avisos": 0, "meritos": 0, "periodos": 0}
    p.hon_turno("jornada:camarero")
    p.dia_honrado()
    p.hon_sv_al_entrar(None)
    assert p.j.contrato["turnos"] == 0 and not [m for m in enviados if m.get("t") == "contrato"]      # el contrato que traiga queda como está
    assert not p.hon_con_antecedentes() and p.hon_antecedente(2, "x") is None and p.hon_trato() == 1.0


# ============================================================================ opciones, panel y documentación
def test_las_opciones_nuevas_estan_en_el_servidor_en_el_panel_y_en_la_guia():
    for clave, serie in (("mundo_distinto", "admitir"), ("nominas", "si"), ("nomina_max", 1500), ("nomina_turnos_dia", 3), ("trato_prestigio", "si")):
        assert opciones.POR_CLAVE[clave].defecto == serie and not opciones.POR_CLAVE[clave].reinicio, clave
    assert [o.clave for o in opciones.de_seccion("vida")] == ["nominas", "nomina_max", "nomina_turnos_dia", "trato_prestigio"]
    assert [o.clave for o in opciones.de_seccion("versiones")] == ["comprobar_datos", "mundo_distinto", "versiones", "version_minima", "actualizar_mundo"]
    letras = "abcdefghijklmnopqrstuvwxyz"
    for ident, _, _ in opciones.SECCIONES:                 # en el panel, las letras de acceso salen de las etiquetas y no se repiten
        usadas = set("acpf")
        for o in opciones.de_seccion(ident):
            libre = next((ch.lower() for ch in o.etiqueta if ch.lower() in letras and ch.lower() not in usadas), None)
            assert libre is not None, (ident, o.clave)
            usadas.add(libre)
    conf = opciones.texto_conf()
    assert "mundo_distinto = admitir" in conf and "nomina_max = 1500" in conf and "VIDA HONRADA" in conf
    limpio, problemas = opciones.validar({"mundo_distinto": "Rechazar", "nominas": "no", "nomina_max": "-3"})
    assert limpio["mundo_distinto"] == "rechazar" and limpio["nominas"] == "no" and limpio["nomina_max"] == 1500 and len(problemas) == 1
    with open(os.path.join(RAIZ, "data", "docs", "servidor_es.html"), encoding="utf-8") as f:
        guia = f.read()
    for palabra in ("<code>mundo_distinto</code>", "<code>nominas</code>", "<code>nomina_max</code>", "<code>nomina_turnos_dia</code>", "<code>trato_prestigio</code>",
                    "Jugar con versiones distintas", "lo más parecido", "el primero que entra", "versión mínima"):
        assert palabra in guia, palabra
    with open(os.path.join(RAIZ, "data", "docs", "manual_es.html"), encoding="utf-8") as f:
        manual = f.read()
    for palabra in ("Jugar con gente que tiene otra versión", "la nómina la paga el servidor"):
        assert palabra in manual, palabra
    with open(os.path.join(RAIZ, "README.md"), encoding="utf-8") as f:
        leeme = f.read()
    for palabra in ("equivalencias", "partida_juego", "mundo_distinto", "test_171_versiones"):
        assert palabra in leeme, palabra
    for nombre in ("LEEME_servidor.txt", "LEEME_otros_sistemas.txt"):
        with open(os.path.join(RAIZ, "servidor", "despliegue", nombre), encoding="utf-8") as f:
            assert "versiones distintas" in f.read(), nombre


def test_el_servidor_anuncia_lo_que_sabe_y_el_modulo_nuevo_viaja_con_el():
    assert "equivalencias" in nucleo.FUNCIONES and "nominas" in nucleo.FUNCIONES
    assert nucleo.VERSION_RED == 2 and nucleo.PROTOCOLO_MIN == 2      # el protocolo no cambia: un juego de la 1.7.0 sigue entrando
    from herramientas import preparar_carpeta_servidor as carpeta
    assert carpeta.guia_al_dia()
    assert os.path.exists(os.path.join(RAIZ, "servidor", "compat.py"))
