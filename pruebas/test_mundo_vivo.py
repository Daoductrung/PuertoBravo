"""Hablar con cualquiera, modo IA, vida realista, vida íntima del modo adulto, actividades conjuntas y cifrado de la configuración."""
import json
import os
import random
import time
import types

import pygame

from juego import charla, cifrado, ia, red, rutas
from juego.entidades import Persona
from juego.menus import Dialogo, EntradaTexto, Menu


def _vecino(p, **cambios):
    """Pone a una persona al lado del jugador, con la ficha que se indique."""
    q = Persona("civil", p.j.x + 1.5, p.j.y)
    q.estado = "quieto"
    f = charla.ficha(q, random.Random(3))
    f.update({"nombre": "Maite", "genero": "m", "edad": 34, "oficio": "panadera", "caracter": "amable", "disponible": True, "le_atraen": "hm"})
    f.update(cambios)
    p.personas.append(q)
    return q, f


def _elegir(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    m.refrescar(False)
    for k, o in enumerate(m.opciones):
        if texto.lower() in o.texto.lower():
            m.i = k
            robot.tecla(pygame.K_RETURN)
            return
    raise AssertionError(f"no hay opción «{texto}» en {[o.texto for o in m.opciones]}")


def _al_juego(robot):
    p = robot.p
    for _ in range(30):
        if robot.app.pila[-1] is p:
            return
        cima = robot.app.pila[-1]
        if isinstance(cima, Menu) and not cima.escapable:
            cima.i = len(cima.opciones) - 1
            robot.tecla(pygame.K_RETURN)
        else:
            robot.tecla(pygame.K_ESCAPE)


# ===================================================================== hablar con cualquiera
def test_hablar_con_cualquiera(robot):
    p = robot.nueva_partida()
    j = p.j
    p.personas = [x for x in p.personas if x.dist(j.x, j.y) > 12]
    robot.tecla(pygame.K_j)
    assert "No tienes a nadie al lado" in robot.dicho()
    q, f = _vecino(p)
    robot.tecla(pygame.K_j)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and "Hablas con Maite" in m.titulo and "Maite, 34 años, panadera" in robot.dicho()
    assert q.nombre == "Maite"                                   # desde ahora el radar la llama por su nombre
    assert not any("Coquetear" in o.texto for o in m.opciones)   # sin el modo adulto no existe
    _elegir(robot, "Saludar")
    assert "Maite:" in robot.app.voz.registro[-1] and f["confianza"] > 0
    _elegir(robot, "Preguntar por el barrio")
    assert "Esto es" in robot.app.voz.registro[-1]
    _elegir(robot, "Preguntar qué se cuenta")
    assert robot.app.voz.registro[-1].startswith("Maite:")
    p.cancelar_gps()
    _elegir(robot, "Preguntar por un sitio")
    _elegir(robot, "curarme")
    assert p.gps is not None and "Te lo marco en el GPS" in robot.app.voz.registro[-1]
    _elegir(robot, "Pedirle el número")
    assert "Aún no te conozco" in robot.app.voz.registro[-1] and not j.conocidos
    dinero = j.dinero = 100
    _elegir(robot, "Invitar a un café")
    _elegir(robot, "Darle 10 euros")
    _elegir(robot, "Hacer un cumplido")
    assert j.dinero == dinero - 14 and f["confianza"] >= 30
    _elegir(robot, "Invitar a un café")                           # solo una vez
    assert "Ya me has invitado" in robot.app.voz.registro[-1] and j.dinero == dinero - 14
    _elegir(robot, "Pedirle el número")
    assert len(j.conocidos) == 1 and j.conocidos[0]["nombre"] == "Maite"
    _elegir(robot, "Despedirte")
    assert robot.app.pila[-1] is p
    # los conocidos están en el móvil y cuentan algo cada día
    from juego import menus_charla
    menus_charla.conocidos(p)
    _elegir(robot, "Maite, panadera")
    assert robot.app.voz.registro[-1].startswith("Maite:")
    _elegir(robot, "Maite, panadera")
    assert "ya te ha contado hoy" in robot.app.voz.registro[-1]
    _al_juego(robot)
    # la identidad se guarda con la partida
    from juego import menus_juego
    menus_juego.escribir_ranura(p, "3")
    assert menus_juego.leer_ranura("3")["jugador"]["conocidos"][0]["nombre"] == "Maite"
    # insultar: se ofende y ya no quiere hablar; amenazar es delito
    robot.tecla(pygame.K_j)
    c0 = j.ciudadania
    _elegir(robot, "Insultar")
    assert robot.app.pila[-1] is p and f["ofendido"] and j.ciudadania < c0
    q.hostil, q.estado, q.tipo = False, "quieto", "civil"
    robot.tecla(pygame.K_j)
    assert "no quiere saber nada de ti" in robot.dicho() and robot.app.pila[-1] is p
    q2, f2 = _vecino(p, nombre="Paco", genero="h", caracter="timido")
    q.x += 40
    robot.tecla(pygame.K_j)
    _elegir(robot, "Amenazar")
    assert f2["ofendido"] and q2.estado == "huye"


def test_texto_libre_e_intenciones(robot):
    for texto, esperado in (("Hola, buenas tardes", "saludar"), ("¿Dónde puedo comer algo?", "sitio"), ("busco un médico", "sitio"), ("eres un idiota", "insultar"),
                            ("dame la cartera", "amenazar"), ("qué se cuenta por aquí", "rumor"), ("te invito a un café", "invitar"), ("¿a qué te dedicas?", "trabajo_npc"),
                            ("me gustas mucho", "ligar"), ("adiós", "despedir"), ("", "nada"), ("el cielo es azul", "otra")):
        assert charla.interpretar(texto)[0] == esperado, texto
    assert charla.interpretar("¿dónde hay un taller?") == ("sitio", "taller")
    p = robot.nueva_partida()
    p.personas = [x for x in p.personas if x.dist(p.j.x, p.j.y) > 12]
    q, f = _vecino(p)
    robot.tecla(pygame.K_j)
    _elegir(robot, "Escribir lo que quieras")
    assert isinstance(robot.app.pila[-1], EntradaTexto)
    for letra in "Hola":
        robot.tecla(pygame.K_a, unicode=letra)
    robot.tecla(pygame.K_RETURN)
    assert robot.app.voz.registro[-1].startswith("Maite:") and f["confianza"] > 0
    for _ in range(8):                                           # sin el modo adulto, coquetear no lleva a nada
        r = p.responder_libre(q, "me gustas, guapa")
        assert "Gracias, pero no" in r or "Qué cosas tienes" in r


# ============================================================================ vida realista
def test_vida_realista_hambre_y_sueno(robot):
    p = robot.nueva_partida()
    j = p.j
    p.pasar_horas(10)
    assert j.hambre == 0 and j.sueno == 0 and p.necesidades_txt() == "" and p.mod_necesidades() == 1.0      # apagada, no existe
    p.cfg["vida_realista"] = True
    p.pasar_horas(9)
    assert 60 < j.hambre < 70 and 40 < j.sueno < 50 and "Empiezas a tener hambre." in robot.dicho()
    assert "con hambre" in p.necesidades_txt()
    p.son("comer")                                               # comer en cualquier sitio quita el hambre
    assert j.hambre < 25
    p.pasar_horas(9)
    assert j.sueno > 85 and "Se te cierran los ojos" in robot.dicho() and p.mod_necesidades() < 1.0
    salud = j.salud
    p.pasar_horas(8)
    assert j.hambre == 100 and j.salud < salud and j.salud >= 10
    p.pasar_horas(8, dormir=True)                                # dormir repara
    assert j.sueno == 0
    robot.tecla(pygame.K_v)
    assert "Estás" in robot.dicho()
    robot.frames(30)                                             # y el tiempo normal también cuenta
    p.cfg["vida_realista"] = False


# ====================================================================== modo adulto, a fondo
def _adulto(robot):
    robot.app.cfg["adultos"] = True
    robot.app.aplicar_adultos()


def test_adultos_ligar_aventura_y_proteccion(robot, monkeypatch):
    p = robot.nueva_partida()
    _adulto(robot)
    j = p.j
    j.dinero = 5000
    j.animo = 70.0
    p.personas = [x for x in p.personas if x.dist(j.x, j.y) > 12]
    # a quien no le interesa, no le interesa: se respeta y no se puede insistir
    q0, f0 = _vecino(p, nombre="Olga", disponible=False)
    assert p.ligar(q0).startswith("Olga: ") and f0["calabazas"] and not f0.get("interes")
    assert "ya te dijo que no" in p.ligar(q0) and not p.puede_proponer(q0)
    assert p.proponer_aventura(q0) is False and q0 in p.personas
    q0.x += 50
    # preferencias: si no es tu tipo, no hay coqueteo
    q, f = _vecino(p)
    p.cfg["atraccion"] = "hombres"
    assert "no es tu tipo" in p.ligar(q)
    p.cfg["atraccion"] = "todos"
    # sin confianza, calabazas suaves; con confianza, interés
    monkeypatch.setattr(random, "uniform", lambda a, b: 0.0)
    f["confianza"] = 0
    j.animo = 50.0
    assert "Le gustas" not in p.ligar(q)
    f["confianza"] = 40
    assert "Le gustas" in p.ligar(q) and p.puede_proponer(q)
    robot.tecla(pygame.K_j)
    m = robot.app.pila[-1]
    assert any("Coquetear" in o.texto for o in m.opciones) and any("Proponerle ir a un hotel" in o.texto for o in m.opciones)
    # aventura sin protección y con mala suerte
    monkeypatch.setattr(random, "random", lambda: 0.01)
    f["confianza"] = 80
    dia = p.dia
    _elegir(robot, "Proponerle ir a un hotel")
    assert isinstance(robot.app.pila[-1], Dialogo) and "con Maite, en un hotel" in robot.dicho()
    robot.tecla(pygame.K_RETURN)
    assert "No habéis usado protección" in robot.dicho()
    robot.saltar_dialogos()
    assert q not in p.personas and j.stats["aventuras"] == 1 and j.stats["noches"] == 1 and j.dinero == 4930 and j.its == dia
    assert robot.app.pila[-1] is p
    # la infección se nota, y se cura en la farmacia
    for _ in range(3):
        p.dia += 1
        p.dia_intimidad()
    assert "Notas molestias" in robot.dicho() and "molestias" in p.estado_intimo_txt()
    from juego import menus_juego
    farmacia = next(l for l in p.mundo.lugares.values() if l.tipo == "farmacia")
    j.x, j.y = farmacia.x, farmacia.y
    menus_juego.lugar(p, farmacia)
    _elegir(robot, "Caja de preservativos")
    assert j.intimos["preservativos"] == 6
    _elegir(robot, "Prueba de salud sexual")
    assert j.its == 0 and "positivo" in robot.dicho()
    _elegir(robot, "Prueba de salud sexual")
    assert "Todo está bien" in robot.dicho()
    _al_juego(robot)
    # con protección no hay riesgo
    q2, f2 = _vecino(p, nombre="Lola", confianza=80)
    f2["interes"] = True
    assert p.proponer_aventura(q2, en_hotel=True)
    robot.tecla(pygame.K_RETURN)
    assert "Habéis tenido cuidado" in robot.dicho() and j.intimos["preservativos"] == 5 and j.its == 0
    robot.saltar_dialogos()
    # sin el modo adulto, nada de esto aparece
    robot.app.cfg["adultos"] = False
    robot.app.aplicar_adultos()
    menus_juego.lugar(p, farmacia)
    assert not any("preservativos" in o.texto.lower() or "sexual" in o.texto.lower() for o in robot.app.pila[-1].opciones)
    _al_juego(robot)
    q3, _ = _vecino(p, nombre="Sara")
    robot.tecla(pygame.K_j)
    assert not any("Coquetear" in o.texto for o in robot.app.pila[-1].opciones)


def test_adultos_pareja_gestos_noches_y_club(robot, monkeypatch):
    from juego import intimidad, menus_adultos
    p = robot.nueva_partida()
    _adulto(robot)
    j = p.j
    j.dinero = 100000
    l = p.lugares["chiringuito"]
    j.x, j.y = l.x, l.y
    robot.frames(10)
    menus_adultos.vida_social(p)
    _elegir(robot, "Presentarte a Lucía")
    r = p.relacion("lucia")
    # los gestos piden confianza y se hacen una vez al día
    _elegir(robot, "Darle un beso")
    assert "Todavía es pronto" in robot.dicho()
    r["afinidad"] = 70
    for texto in ("Darle un beso", "Bailar juntos", "Darle un masaje", "Decirle algo al oído"):
        antes = r["afinidad"]
        _elegir(robot, texto)
        assert r["afinidad"] > antes, texto
        _elegir(robot, texto)
        assert "ya lo habéis hecho hoy" in robot.dicho(), texto
    # las cuatro maneras de pasar la noche, y lo comprado se nota
    for a in p.articulos_intimos():
        assert p.comprar_articulo(a)
    assert j.intimos == {"preservativos": 6, "lenceria": 1, "aceite": 1, "velas": 1, "juguete": 1}
    vistos = set()
    for tipo, (titulo, frases, animo, horas) in intimidad.ENCUENTROS.items():
        p.dia += 1
        j.animo = 40.0
        menus_adultos.vida_social(p)
        _elegir(robot, "Lucía")
        _elegir(robot, "Pasar la noche juntos")
        _elegir(robot, titulo)
        assert isinstance(robot.app.pila[-1], Dialogo) and f"{titulo} con Lucía" in robot.dicho(), tipo
        texto = robot.dicho()
        vistos.add(tipo)
        robot.saltar_dialogos()
        assert robot.app.pila[-1] is p and j.animo > 40 and j.salud == j.salud_max, tipo
        # sensual, pero sin nada explícito
        for palabra in ("pene", "vagina", "follar", "polla", "coño", "orgasmo", "desnud"):
            assert palabra not in texto.lower(), (tipo, palabra)
    assert vistos == set(intimidad.ENCUENTROS) and j.stats["noches"] == 4
    assert j.intimos["lenceria"] == 0 and j.intimos["aceite"] == 0 and j.intimos["velas"] == 0 and j.intimos["juguete"] == 0
    assert j.intimos["preservativos"] == 2                         # uno por noche
    # el club: bailar (y conocer a alguien), pase privado, tienda y compañía
    club = p.lugares["club_paraiso"]
    j.x, j.y = club.x, club.y
    monkeypatch.setattr(random, "random", lambda: 0.2)
    menus_adultos.club(p, club)
    n = len(p.personas)
    _elegir(robot, "Bailar en la pista")
    assert len(p.personas) == n + 1 and "Háblale con la tecla J" in robot.dicho()
    animo = j.animo = 30.0
    _elegir(robot, "Pase privado")
    assert j.animo > animo and "sin tocar" in robot.dicho()
    _elegir(robot, "Tienda discreta")
    _elegir(robot, "Velas aromáticas")
    assert j.intimos["velas"] == 1
    robot.tecla(pygame.K_ESCAPE)
    _elegir(robot, "Pagar por compañía")
    robot.saltar_dialogos()
    assert j.stats["pagos"] == 1 and j.intimos["preservativos"] == 1
    _al_juego(robot)
    robot.tecla(pygame.K_v)
    assert "preservativos" in robot.dicho()


# ====================================================================== actividades conjuntas
def _esperar(cond, robot, segundos=4.0):
    fin = time.time() + segundos
    while time.time() < fin:
        robot.frames(2)
        if cond():
            return True
        time.sleep(0.02)
    return False


def _acto(cli, que, segundos=4.0):
    fin = time.time() + segundos
    while time.time() < fin:
        try:
            m = cli.entrantes.get(timeout=0.1)
        except Exception:
            continue
        if m.get("t") == "act" and m["d"].get("que") == que:
            return m
    return None


def test_carrera_reparto_y_pasajero_con_un_amigo(robot):
    p = robot.nueva_partida()
    j = p.j
    ok, _ = p.abrir_a_amigos(0, "")
    assert ok
    amigo = red.Cliente()
    try:
        assert amigo.conectar("127.0.0.1", p.servidor.puerto, "Marta")[0]
        assert _esperar(lambda: len(p.remotos) == 1, robot)
        remoto = next(iter(p.remotos.values()))
        # carrera con apuesta: propongo, acepta, empiezo y gano
        j.dinero = 1000
        destino = p.lugares["hospital"]
        ok, texto = p.proponer_carrera(destino, 100)
        assert ok and "Propones una carrera" in texto and p.proponer_reparto()[0] is False
        m = _acto(amigo, "propuesta")
        assert m["d"]["tipo"] == "carrera" and m["d"]["lugar"] == "hospital" and m["d"]["apuesta"] == 100
        assert p.empezar_coop()[0] is False                         # nadie ha aceptado aún
        amigo.enviar({"t": "act", "d": {"que": "acepto"}})
        assert _esperar(lambda: len(p.coop["participantes"]) == 2, robot)
        assert p.empezar_coop()[0] and p.coop["estado"] == "marcha" and j.dinero == 900 and p.gps is not None
        assert _acto(amigo, "salida")["d"]["participantes"] == sorted(p.coop["participantes"])
        j.x, j.y = destino.x, destino.y
        assert _esperar(lambda: p.coop is None, robot)
        assert j.dinero == 1100 and "Has ganado la carrera" in robot.dicho() and _acto(amigo, "meta") is not None
        # si gana el otro, pierdo la apuesta
        p.proponer_carrera(destino, 100)
        amigo.enviar({"t": "act", "d": {"que": "acepto"}})
        _esperar(lambda: len(p.coop["participantes"]) == 2, robot)
        j.x, j.y = destino.x + 300, destino.y
        p.empezar_coop()
        amigo.enviar({"t": "act", "d": {"que": "meta"}})
        assert _esperar(lambda: p.coop is None, robot) and j.dinero == 1000 and "Marta ha llegado primero" in robot.dicho()
        # reparto en equipo propuesto por el amigo: acepto, él entrega tres y yo la última; cobramos
        lugares = [l.id for l in p.mundo.lugares.values() if l.tipo in ("tienda", "comida", "farmacia", "banco")][:4]
        amigo.enviar({"t": "act", "d": {"que": "propuesta", "tipo": "reparto", "lugares": lugares, "mapa": p.mundo.id}})
        assert _esperar(lambda: p.coop is not None, robot) and "Marta propone un reparto en equipo" in robot.dicho()
        assert p.aceptar_coop()[0] and _acto(amigo, "acepto") is not None
        amigo.enviar({"t": "act", "d": {"que": "salida", "participantes": [amigo.id, p.red.id]}})
        assert _esperar(lambda: p.coop and p.coop["estado"] == "marcha", robot) and p.gps is not None
        for i in lugares[:3]:
            amigo.enviar({"t": "act", "d": {"que": "punto", "lugar": i}})
        assert _esperar(lambda: p.coop and len(p.coop["restantes"]) == 1, robot)
        ultimo = p.lugares[lugares[3]]
        dinero = j.dinero
        j.x, j.y = ultimo.x, ultimo.y
        assert _esperar(lambda: p.coop is None, robot)
        assert j.dinero == dinero + 350 and "Reparto completado entre todos" in robot.dicho() and _acto(amigo, "punto")["d"]["lugar"] == lugares[3]
        # de pasajero en el coche de un amigo
        amigo.enviar({"t": "estado", "e": {"m": p.mundo.id, "x": j.x + 4, "y": j.y, "r": 0, "v": "taxi", "s": 0}})
        assert _esperar(lambda: remoto.veh == "taxi" and remoto.dist(j.x, j.y) < 8, robot)
        robot.tecla(pygame.K_f)
        assert p.pasajero == remoto.id and "Subes de pasajero con Marta" in robot.dicho() and _acto(amigo, "sube")["d"]["a"] == amigo.id
        amigo.enviar({"t": "estado", "e": {"m": p.mundo.id, "x": j.x + 120, "y": j.y + 90, "r": 0, "v": "taxi", "s": 14}})
        x0 = j.x
        assert _esperar(lambda: j.x > x0 + 80, robot)                  # me lleva
        robot.tecla(pygame.K_f)
        assert p.pasajero is None and _acto(amigo, "baja") is not None
        x1 = j.x
        amigo.enviar({"t": "estado", "e": {"m": p.mundo.id, "x": x1 + 200, "y": j.y, "r": 0, "v": "taxi", "s": 14}})
        robot.frames(20)
        assert abs(j.x - x1) < 5                                       # ya no
        # botiquines en los dos sentidos
        j.objetos["botiquin"] = 1
        assert p.dar_botiquin_a(remoto) and j.objetos["botiquin"] == 0 and _acto(amigo, "regalo")["d"]["cosa"] == "botiquin"
        assert not p.dar_botiquin_a(remoto)
        amigo.enviar({"t": "act", "d": {"que": "regalo", "a": p.red.id, "cosa": "botiquin"}})
        assert _esperar(lambda: j.objetos["botiquin"] == 1, robot)
        # el menú lo ofrece todo
        from juego import menus_online
        menus_online.amigos(p)
        textos = [o.texto for o in robot.app.pila[-1].opciones]
        assert any("Proponer una carrera" in t for t in textos) and any("Proponer un reparto" in t for t in textos)
    finally:
        p.desconectar_online()
        amigo.cerrar()


# ============================================================================== cifrado
def test_opciones_botones_y_packs_protegidos_al_compilar(tmp_path, monkeypatch):
    from juego import config, packs
    monkeypatch.setattr(rutas, "DATA", str(tmp_path))
    monkeypatch.setattr(rutas, "data", lambda *a: os.path.join(str(tmp_path), *a))
    c = config.Config()
    assert c.archivo.endswith("config.json")
    c["vol_maestro"] = 0.3
    c.guardar()
    assert json.load(open(c.archivo, encoding="utf-8"))["vol_maestro"] == 0.3
    # compilado: extensión propia, cifrado, y se heredan las opciones que había en claro
    monkeypatch.setattr(cifrado, "COMPILADO", True)
    c2 = config.Config()
    assert c2.archivo.endswith("config.pbc") and c2["vol_maestro"] == 0.3
    c2["vol_maestro"] = 0.7
    c2.guardar()
    assert cifrado.esta_cifrado(c2.archivo) and config.Config()["vol_maestro"] == 0.7
    # los JSON de apoyo de los packs: se leen en claro o protegidos
    carpeta = os.path.join(str(tmp_path), "sonidos", "mi_pack")
    os.makedirs(carpeta)
    cifrado.escribir_json(os.path.join(carpeta, "pack.pbd"), {"nombre": "Protegido"}, cifrado=True)
    assert packs._meta(carpeta)["nombre"] == "Protegido"
    os.remove(os.path.join(carpeta, "pack.pbd"))
    cifrado.escribir_json(os.path.join(carpeta, "pack.json"), {"nombre": "En claro"}, cifrado=False)
    assert packs._meta(carpeta)["nombre"] == "En claro"
    # y la herramienta de compilación los convierte
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "herramientas"))
    import cifrar_datos
    os.makedirs(os.path.join(str(tmp_path), "datos"))
    os.makedirs(os.path.join(str(tmp_path), "mods"))
    assert cifrar_datos.recorrer(str(tmp_path)) == 1
    assert os.path.exists(os.path.join(carpeta, "pack.pbd")) and not os.path.exists(os.path.join(carpeta, "pack.json"))
    assert packs._meta(carpeta)["nombre"] == "En claro"
