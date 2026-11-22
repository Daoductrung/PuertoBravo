"""Partida en línea a ocho: ocho juegos completos en un servidor, en dos bandas de cuatro, y que gane la mejor.

Cada jugador hace lo suyo, como cuando juega solo: su misión, sus compras, sus objetos, sus opciones. Y a la vez hace
vida de banda: funda o entra, mete dinero en la caja, se pasa armas y dinero, hace una misión en grupo con los suyos,
le quita un coche a la otra banda, se queda con un barrio y lo defiende, o lo ataca, en una guerra con tiros de verdad.
Al final el barrio es de quien más puntos ha hecho, todos guardan, salen y vuelven a entrar.
"""
import hashlib
import random
import re
import time

import pygame
import pytest

from conftest import Robot
from juego import enlinea, menus_enlinea, menus_juego
from test_enlinea import entrar
from test_ronda import _coherente
from test_servidor import Banco, lejos_de_todo

N = 8
LINCES, ZORROS = range(0, 4), range(4, 8)


@pytest.fixture
def banco(tmp_path):
    b = Banco(tmp_path, max_jugadores=8)
    yield b
    b.parar()


@pytest.fixture
def ocho(app):
    from juego.app import App
    apps = [app] + [App(pruebas=True) for _ in range(N - 1)]
    yield [Robot(x) for x in apps]
    for x in apps:
        if x.partida is not None:
            x.partida.sv_salir()
            x.partida.desconectar_online()
    for x in apps[1:]:
        x.radio.cancelar()
        x.ambiente.cancelar()
        x.mez.cerrar()


def todos(robots, n=2):
    for _ in range(n):
        for r in robots:
            r.frames(1)


def hasta(cond, robots, segundos=12.0):
    fin = time.time() + segundos
    while time.time() < fin:
        todos(robots, 2)
        if cond():
            return True
        time.sleep(0.01)
    return False


def al_juego(robot):
    for _ in range(30):
        if robot.app.pila[-1] is robot.p:
            return
        robot.saltar_dialogos()
        if robot.app.pila[-1] is not robot.p:
            robot.tecla(pygame.K_ESCAPE)


class Acompanado:
    """Mientras un jugador hace lo suyo, los otros siete siguen conectados y atendiendo al servidor."""

    def __init__(self, robot, robots):
        self.robot, self.otros = robot, [r for r in robots if r is not robot]
        self._frames = robot.frames
        self.n = 0

    def __enter__(self):
        def frames(n=1, **kw):
            self._frames(n, **kw)
            self.n += n
            if self.n >= 8:
                self.n = 0
                for o in self.otros:
                    if o.app.partida is not None:
                        o.app.partida.red_paso(0.1)
        self.robot.frames = frames
        return self.robot

    def __exit__(self, *a):
        del self.robot.frames


def test_partida_en_linea_a_ocho_dos_bandas_y_que_gane_la_mejor(ocho, banco):
    import test_misiones
    robots = ocho
    ps = [entrar(r, banco, f"Jugador{k + 1}") for k, r in enumerate(robots)]
    for k, r in enumerate(robots):
        todos(robots, 1)
    assert hasta(lambda: all(len(p.remotos) == N - 1 for p in ps), robots), [len(p.remotos) for p in ps]
    assert len({p.j.semilla for p in ps}) == 1 and len({p.dia for p in ps}) == 1      # el mismo mundo para los ocho

    def ve(p, k):
        return next(x for x in p.remotos.values() if x.nombre == f"Jugador{k + 1}")

    # un noveno no cabe
    extra = enlinea.ClienteServidor()
    ok, motivo = extra.conectar_servidor("127.0.0.1", banco.puerto, "Noveno", hashlib.sha256(b"noveno").digest(), robots[0].app._huella_datos)
    assert not ok and "lleno" in motivo

    # ------------------------------------------ cada uno, lo suyo: su primera misión
    primera = next(m for m in ps[0].datos["misiones"] if m["id"] == "m01")
    for k, r in enumerate(robots):
        with Acompanado(r, robots):
            test_misiones._jugar_mision(r, primera)
        assert "m01" in ps[k].completadas and ps[k].en_servidor and ps[k].online_activo(), k
    todos(robots, 4)
    assert all(len(p.remotos) == N - 1 for p in ps)              # nadie se ha caído mientras los demás jugaban

    # --------------------------------------------------- opciones, compras y objetos
    for k, (r, p) in enumerate(zip(robots, ps)):
        p.cfg["sucesos"] = False
        p.cfg["fuego_amigo"] = bool(k % 2)                       # cada uno con sus opciones: no cambian lo de los demás
        p.cfg["mando_textos"] = not (k % 3)
        p.j.dinero = 30000
        tienda = next(l for l in p.mundo.lugares.values() if l.tipo == "tienda" and {"botiquin", "ganzua"} <= set(l.get("vende") or ["botiquin", "ganzua"]))
        p.teletransportar(tienda.x, tienda.y)
        menus_juego.lugar(p, tienda)
        m = r.app.pila[-1]
        m.refrescar(False)
        for texto in ("Botiquín", "Ganzúa"):
            m.i = next(i for i, o in enumerate(m.opciones) if texto.lower() in o.texto.lower() and o.accion)
            r.tecla(pygame.K_RETURN)
        al_juego(r)
        assert p.j.objetos["botiquin"] >= 2 and p.j.objetos["ganzua"] >= 1 and p.j.dinero < 30000
        p.j.salud = 30
        n = p.j.objetos["botiquin"]
        p.usar_botiquin()
        assert p.j.salud > 30 and p.j.objetos["botiquin"] == n - 1
        for arma in ("pistola", "escopeta", "bate", "navaja", "granada")[k % 2:][:4]:
            p.dar_arma(arma, 60)
        assert menus_juego.escribir_ranura(p, "1")               # guardar va al servidor
    todos(robots, 4)

    # ------------------------------------------------------------- dos bandas
    for jefe, nombre, gente in ((0, "Los Linces", LINCES), (4, "Los Zorros", ZORROS)):
        menus_enlinea.banda(ps[jefe])
        m = robots[jefe].app.pila[-1]
        m.i = next(i for i, o in enumerate(m.opciones) if o.texto.startswith("Fundar una banda"))
        robots[jefe].tecla(pygame.K_RETURN)
        robots[jefe].app.pila[-1].texto = nombre
        robots[jefe].tecla(pygame.K_RETURN)
        assert hasta(lambda: ps[jefe].sv["banda"] is not None, robots)
        al_juego(robots[jefe])
        for k in gente:
            if k == jefe:
                continue
            ps[jefe].red.enviar({"t": "banda_invitar", "a": ve(ps[jefe], k).id})
            assert hasta(lambda: ps[k].sv["inv_banda"] is not None, robots)
            menus_enlinea.banda(ps[k])
            robots[k].tecla(pygame.K_RETURN)                     # aceptar
            assert hasta(lambda: ps[k].sv["banda"] is not None, robots)
            al_juego(robots[k])
        assert hasta(lambda: all(len(ps[k].sv["banda"]["miembros"]) == 4 for k in gente), robots)
    assert all(ps[k].sv["banda"]["nombre"] == "Los Linces" for k in LINCES) and all(ps[k].sv["banda"]["nombre"] == "Los Zorros" for k in ZORROS)
    assert ps[1].sv_relacion(ve(ps[1], 2)) == "de tu banda" and ps[1].sv_relacion(ve(ps[1], 5)) == ""
    # el jefe nombra una mano derecha, que también puede sacar de la caja
    cuenta2 = next(q["cuenta"] for q in ps[0].sv["banda"]["miembros"] if q["nombre"] == "Jugador2")
    ps[0].red.enviar({"t": "banda_rango", "cuenta": cuenta2, "rango": "mano"})
    assert hasta(lambda: ps[1].sv["rango"] == "mano", robots)
    # todos atienden a la banda: cada uno mete en la caja
    for p in ps:
        p.red.enviar({"t": "banda_ingresar", "n": 2500})
    assert hasta(lambda: ps[0].sv["banda"]["caja"] == 10000 and ps[4].sv["banda"]["caja"] == 10000, robots)
    assert len(ps[3].sv["banda"]["apuntes"]) >= 4
    ps[1].red.enviar({"t": "banda_sacar", "n": 500})
    assert hasta(lambda: ps[0].sv["banda"]["caja"] == 9500, robots)
    # el chat de banda no lo oye la otra
    menus_enlinea.chat(ps[2], "banda", None, "x")
    robots[2].app.pila[-1].texto = "esta noche, al puerto"
    robots[2].tecla(pygame.K_RETURN)
    assert hasta(lambda: "Jugador3 dice a la banda: esta noche, al puerto" in robots[0].dicho(), robots)
    assert not any("esta noche, al puerto" in robots[k].dicho() for k in ZORROS)

    # ------------------------------------------- todos juntos, lejos de zonas seguras
    x, y = lejos_de_todo("puerto_bravo")
    for k, p in enumerate(ps):
        if p.mundo.id != "puerto_bravo":
            p.cambiar_mapa("puerto_bravo", x, y)
        p.teletransportar(x + 3 * (k % 4), y + (0 if k < 4 else 8))
        p.sv["protegido"] = 0
    banco.hacer(lambda: [setattr(q, "protegido", 0) for q in banco.srv.jugadores.values()])
    assert hasta(lambda: all(q.visto and q.mapa == "puerto_bravo" and q.dist(*p.pos()) < 40 for p in ps for q in p.remotos.values()), robots)
    barrio = ps[0].mundo.barrio(*ps[0].pos())["id"]
    assert all(p.mundo.barrio(*p.pos())["id"] == barrio for p in ps)

    # --------------------------------------- se pasan cosas entre los de la banda
    ps[0].dar_dinero_a(ve(ps[0], 3), 400)
    d3 = ps[3].j.dinero
    assert hasta(lambda: ps[3].j.dinero == d3 + 400, robots)
    ps[4].dar_arma("revolver", 12)
    del ps[4].j.armas["revolver"]
    ps[4].red.enviar({"t": "dar", "a": ve(ps[4], 6).id, "clase": "arma", "id": "revolver", "n": 1})
    assert hasta(lambda: "revolver" in ps[6].j.armas, robots)

    # --------------------------- un Zorro le quita el coche a un Lince, con ganzúa y todo
    vx, vy = ps[1].pos()
    coche = ps[1].crear_vehiculo("sedan", vx + 4, vy, 0, "aparcado")
    coche.cerrado = True
    ganzuas = ps[1].j.objetos["ganzua"]
    ps[1].j.x, ps[1].j.y = coche.x + 2, coche.y
    robots[1].tecla(pygame.K_f)                                  # cerrado: lo fuerza con la ganzúa
    assert hasta(lambda: ps[1].j.veh is coche, robots) and ps[1].j.objetos["ganzua"] == ganzuas - 1
    assert hasta(lambda: getattr(coche, "id_red", None) is not None, robots)
    ps[1].salir_vehiculo()
    assert hasta(lambda: any(getattr(q, "id_red", None) == coche.id_red for q in ps[5].vehiculos), robots)
    copia = next(q for q in ps[5].vehiculos if getattr(q, "id_red", None) == coche.id_red)
    ps[5].j.x, ps[5].j.y = copia.x + 2, copia.y
    todos(robots, 8)
    time.sleep(0.2)
    todos(robots, 4)
    robots[5].tecla(pygame.K_f)
    assert hasta(lambda: ps[5].j.veh is copia and coche.muerto, robots)
    assert "Jugador6 se ha llevado tu" in robots[1].dicho()
    ps[5].salir_vehiculo()
    ps[5].teletransportar(x + 3, y + 8)

    # ------------------------------ misión en grupo: cada banda, la suya, entre los cuatro
    morosos = next(m for m in ps[0].datos["misiones"] if m["id"] == "m04")
    pagas = {}
    for jefe, gente in ((0, LINCES), (4, ZORROS)):
        lider, rl = ps[jefe], robots[jefe]
        resto = [k for k in gente if k != jefe]
        for k in resto:
            lider.red.enviar({"t": "grupo_invitar", "a": ve(lider, k).id, "mision": "Morosos"})
            assert hasta(lambda: ps[k].sv["inv_grupo"] is not None, robots)
            ps[k].red.enviar({"t": "grupo_resp", "si": True})
            assert hasta(lambda: ps[k].sv["grupo"] == lider.red.id, robots)
        assert lider.sv_lidero() and len(lider.sv["miembros"]) == 4
        lider.completadas = [c for c in lider.completadas if c != "m04"]
        inicio = lider.lugares[morosos["lugar"]]
        lider.teletransportar(inicio.x, inicio.y)
        lider.iniciar_mision(morosos)
        rl.saltar_dialogos()
        todos(robots, 4)
        paso = lider.mision["def"]["pasos"][lider.mision["paso"]]
        assert paso["tipo"] == "eliminar"
        assert hasta(lambda: all(ps[k].sv["mision_grupo"] is not None for k in resto), robots)
        sitio = lider.lugares[paso["lugar"]]
        lider.teletransportar(sitio.x, sitio.y)
        for n, k in enumerate(resto):
            ps[k].teletransportar(sitio.x + 4 + 2 * n, sitio.y)
        assert hasta(lambda: lider.mision["generado"] and all(len(ps[k].sv["ecos"]) == len(lider.mision["enemigos"]) for k in resto), robots)
        dinero = {k: ps[k].j.dinero for k in resto}
        # cada uno de los tres le da al mismo enemigo: entre todos lo tumban
        primero = lider.mision["enemigos"][0]
        vida = primero.salud
        for k in resto:
            ps[k].danar_persona(ps[k].sv["ecos"][primero.eco_k], vida / 3 + 1)
        assert hasta(lambda: primero.muerto, robots)
        for e in lider.mision["enemigos"]:                       # del resto se encarga quien lleva la misión
            if not e.muerto:
                lider.danar_persona(e, 999)
        assert hasta(lambda: all(not ps[k].sv["ecos"] or all(e.muerto for e in ps[k].sv["ecos"].values()) for k in resto), robots)
        for _ in range(14):
            rl.saltar_dialogos()
            if lider.mision and rl.app.pila[-1] is lider:
                lider._paso_hecho()
            todos(robots, 2)
            if "m04" in lider.completadas:
                break
        assert "m04" in lider.completadas
        parte = morosos["recompensa"]["dinero"] // 2
        assert hasta(lambda: all(ps[k].j.dinero >= dinero[k] + parte for k in resto), robots), [(ps[k].j.dinero - dinero[k]) for k in resto]
        pagas[jefe] = parte
        lider.red.enviar({"t": "grupo_salir"})
        assert hasta(lambda: all(ps[k].sv["grupo"] is None for k in gente), robots)
        for r in robots:
            al_juego(r)

    # ------------------------------------------------ el barrio, y la guerra por él
    for k, p in enumerate(ps):
        if p.mundo.id != "puerto_bravo":
            p.cambiar_mapa("puerto_bravo", x, y)
        p.teletransportar(x + 3 * (k % 4), y + (0 if k < 4 else 8))
        p.j.salud = p.j.salud_max
        p.sv["protegido"] = 0
    assert hasta(lambda: all(q.dist(*p.pos()) < 40 for p in ps for q in p.remotos.values() if q.mapa == "puerto_bravo"), robots)
    todos(robots, 6)
    time.sleep(0.2)
    todos(robots, 4)
    ps[0].red.enviar({"t": "barrio_reclamar"})
    assert hasta(lambda: all(p.sv_dueno_barrio("puerto_bravo", barrio) is not None for p in ps), robots)
    assert ps[7].sv_dueno_barrio("puerto_bravo", barrio)["nombre"] == "Los Linces"
    ps[4].red.enviar({"t": "barrio_guerra"})
    assert hasta(lambda: "os declara la guerra" in robots[2].dicho() and "Guerra declarada" in robots[6].dicho(), robots)
    assert ps[0].sv["territorios"]["guerras"] or hasta(lambda: bool(ps[0].sv["territorios"]["guerras"]), robots)
    banco.reloj.t += 61
    assert hasta(lambda: all("¡Empieza la guerra" in r.dicho() for r in robots), robots, 15)
    banco.hacer(lambda: [setattr(q, "protegido", 0) for q in banco.srv.jugadores.values()])
    banco.hacer(lambda: setattr(banco.srv, "rng", random.Random(11)))

    # tiros de verdad: cada uno fija a un rival y dispara. Los Zorros van mejor armados
    for k in LINCES:
        ps[k].dar_arma("pistola", 300)
        ps[k].j.arma = "pistola"
    for k in ZORROS:
        ps[k].dar_arma("escopeta", 300)
        ps[k].j.arma = "escopeta"
    caidos = {"Los Linces": 0, "Los Zorros": 0}
    muertes = [p.j.stats["muertes"] for p in ps]
    for ronda in range(14):
        for k, p in enumerate(ps):
            if p.transicion or robots[k].app.pila[-1] is not p:
                continue
            rivales = [q for q in p.remotos.values() if q.mapa == p.mundo.id and (q.nombre in [f"Jugador{i + 1}" for i in (ZORROS if k < 4 else LINCES)]) and q.dist(*p.pos()) < 30]
            if not rivales:
                continue
            p.objetivo = min(rivales, key=lambda q: q.dist(*p.pos()))
            p.j.t_ataque = 0
            p.j.armas[p.j.arma]["cargador"] = 6
            p.j.salud = min(p.j.salud, 60)                       # nadie es de piedra
            p.atacar()
        todos(robots, 3)
        time.sleep(0.85)
        for k, r in enumerate(robots):
            if ps[k].j.stats["muertes"] > muertes[k]:
                muertes[k] = ps[k].j.stats["muertes"]
                caidos["Los Linces" if k < 4 else "Los Zorros"] += 1
            r.saltar_dialogos()
    todos(robots, 6)
    assert caidos["Los Linces"] + caidos["Los Zorros"] > 0, "en catorce rondas de tiros no ha caído nadie"
    assert any("Has tumbado a" in r.dicho() for r in robots) and any("Has caído ante" in r.dicho() for r in robots)
    assert not any("de tu banda" in r.dicho() and "fuego amigo" in r.dicho() for r in robots)       # nadie ha disparado a los suyos
    g = banco.hacer(lambda: dict(banco.srv.guerras[0]))
    assert g["pa"] > 0 and g["pd"] > 0                           # las dos bandas han puntuado: por estar y por tumbar

    # fin de la guerra: el barrio es de quien más puntos ha hecho
    banco.reloj.t += 61
    assert hasta(lambda: all("ha terminado" in r.dicho() for r in robots), robots, 15)
    final = next(t for t in reversed(robots[0].app.voz.registro) if "ha terminado" in t)
    pa, pd = [int(n) for n in re.search(r"(\d+) a (\d+)", final).groups()]
    mejor = "Los Zorros" if pa > pd else "Los Linces"            # atacaban los Zorros; el empate es de quien lo tenía
    assert hasta(lambda: all(p.sv_dueno_barrio("puerto_bravo", barrio)["nombre"] == mejor for p in ps), robots), (pa, pd, mejor)
    assert (f"pasa a {mejor}" if mejor == "Los Zorros" else f"{mejor} lo conserva") in final
    menus_enlinea.tablon(ps[3])
    assert hasta(lambda: (robots[3].app.pila[-1].refrescar(False), any(mejor in o.texto and "de " + mejor in o.texto for o in robots[3].app.pila[-1].opciones))[1], robots)
    al_juego(robots[3])

    # ---------------------------------- medianoche: la banda que tiene el barrio cobra su renta
    caja = {b: ps[k].sv["banda"]["caja"] for b, k in (("Los Linces", 0), ("Los Zorros", 4))}
    dia = ps[0].dia
    banco.hacer(lambda: setattr(banco.srv, "reloj", 1439.6))
    assert hasta(lambda: all(p.dia == dia + 1 for p in ps), robots, 15)
    k_mejor = 0 if mejor == "Los Linces" else 4
    assert hasta(lambda: ps[k_mejor].sv["banda"]["caja"] == caja[mejor] + 300, robots)
    assert ps[4 - k_mejor].sv["banda"]["caja"] == caja["Los Zorros" if mejor == "Los Linces" else "Los Linces"]

    # --------------------------------- todo sigue en su sitio, y cada uno vuelve a ser quien era
    for k, (r, p) in enumerate(zip(robots, ps)):
        al_juego(r)
        _coherente(p, f"jugador {k + 1} al final")
        assert p.en_servidor and len(p.remotos) == N - 1
    dinero = [p.j.dinero for p in ps]
    for p in ps:
        p.sv_salir()
    time.sleep(0.8)
    assert banco.hacer(lambda: sum(1 for q in banco.srv.jugadores.values() if q.dentro)) == 0
    for k in (2, 6):
        p = entrar(robots[k], banco, f"Jugador{k + 1}")
        assert p.j.dinero == dinero[k] and p.sv["banda"]["nombre"] == ("Los Linces" if k < 4 else "Los Zorros")
        assert "m01" in p.completadas and p.j.objetos["botiquin"] >= 1
