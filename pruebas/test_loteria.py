"""La lotería: boleto con número, sorteo a las nueve de la noche, comprobar y cobrar."""
import pygame

from juego import loteria, menus_juego
from juego.menus import EntradaTexto, Menu


def _partida(robot, hora=10):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.j.dinero = 1000
    p.reloj = hora * 60
    robot.frames(2)
    return p, p.j


def _lugar(p, tipo):
    return next(l for l in p.mundo.lugares.values() if l.tipo == tipo)


def _op(m, empieza):
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(empieza))


def test_los_premios_van_por_las_ultimas_cifras():
    assert loteria.aciertos("12345", "12345") == 5 and loteria.aciertos("02345", "12345") == 4 and loteria.aciertos("99945", "12345") == 2
    assert loteria.aciertos("12340", "12345") == 0 and loteria.aciertos("12355", "12345") == 1      # cuentan seguidas, desde el final
    assert loteria.cifras("4712") == "0 4 7 1 2"
    assert loteria.PREMIOS[1] == loteria.PRECIO                       # el reintegro devuelve lo jugado


def test_comprar_en_la_administracion_con_tu_numero(robot):
    p, j = _partida(robot)
    l = _lugar(p, "loteria")
    menus_juego.lugar(p, l)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and "esta noche a las nueve" in m.opciones[0].texto and "Bote: 20000" in m.opciones[0].texto
    _op(m, "Comprar un boleto con el número")
    robot.tecla(pygame.K_RETURN)
    assert isinstance(robot.app.pila[-1], EntradaTexto)
    for c in "4712":
        robot.tecla(getattr(pygame, "K_" + c), unicode=c)
    robot.tecla(pygame.K_RETURN)
    assert j.boletos == [{"n": "04712", "sorteo": p.dia, "donde": l.id}] and j.dinero == 990
    assert "Boleto comprado: el 0 4 7 1 2" in robot.dicho() and "esta noche a las nueve" in robot.dicho()
    # el mismo número no se vende dos veces, y hay un tope por sorteo
    assert not loteria.comprar(p, "4712", l) and j.dinero == 990
    _op(m, "Comprar un boleto al azar")
    for _ in range(6):
        robot.tecla(pygame.K_RETURN)
    assert len(j.boletos) == loteria.TOPE_BOLETOS and j.dinero == 1000 - 10 * loteria.TOPE_BOLETOS and "No se venden más" in robot.dicho()
    assert "Llevas 5 boletos" in m.opciones[0].texto
    # pasado el sorteo, lo que compres juega mañana
    p.reloj = 22 * 60
    assert loteria.sorteo_abierto(p) == p.dia + 1 and "mañana" in loteria.cuando_txt(p)


def test_las_tiendas_y_los_bares_venden_los_numeros_que_tienen_colgados(robot):
    p, j = _partida(robot)
    for tipo in ("tienda", "bar", "taberna"):
        l = _lugar(p, tipo)
        nums = loteria.colgados(p, l)
        assert len(nums) == 3 and nums == loteria.colgados(p, l) and all(len(n) == 5 for n in nums)
        menus_juego.lugar(p, l)
        base = robot.app.pila[-1]
        _op(base, "Lotería")
        robot.tecla(pygame.K_RETURN)
        m = robot.app.pila[-1]
        assert m is not base and "Lotería en" in m.titulo
        assert not any("número que tú digas" in o.texto for o in m.opciones)
        _op(m, "Comprar el boleto")
        robot.tecla(pygame.K_RETURN)
        assert j.boletos[-1]["n"] == nums[0] and j.boletos[-1]["donde"] == l.id
        while robot.app.pila[-1] is not p:
            robot.tecla(pygame.K_ESCAPE)
    assert len(j.boletos) == 3
    # el móvil lo enseña
    loteria.menu_movil(p)
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert sum(t.startswith("Boleto") and "juega esta noche" in t for t in textos) == 3


def test_el_sorteo_es_a_las_nueve_y_hay_que_comprobar(robot):
    p, j = _partida(robot, hora=20)
    hoy = p.dia
    ganador = loteria.premiado(p, hoy)
    assert ganador == loteria.premiado(p, hoy) and len(ganador) == 5
    tienda, admin = _lugar(p, "tienda"), _lugar(p, "loteria")
    otro = "".join(str((int(c) + 5) % 10) for c in ganador)
    for n in (otro, otro[:-1] + ganador[-1], otro[:-2] + ganador[-2:], otro[0] + ganador[1:]):
        assert loteria.comprar(p, n, tienda)
    dinero = j.dinero
    p.reloj = loteria.HORA_SORTEO - 0.2
    n0 = len(robot.app.voz.registro)
    robot.frames(30)
    oido = " ".join(robot.app.voz.registro[n0:])
    assert j.lot_ultimo == hoy and f"Ha salido el {loteria.cifras(ganador)}" in oido and "Llevabas 4 boletos" in oido
    if "ha caído en" in oido:                                         # de vez en cuando le toca a alguien de la comarca, y el bote empieza otra vez
        assert "El bote, 20020 euros" in oido and j.lot_bote == loteria.BOTE_INICIAL
    else:
        assert "bote sube a 22520" in oido and j.lot_bote == 22520    # 20000, más la mitad de lo jugado, más lo que crece
    assert j.dinero == dinero and len(j.boletos) == 4                 # el sorteo no paga solo: hay que comprobar
    # en el móvil: dice lo que ha tocado y dónde se cobra, y tira los que no tienen premio
    loteria.comprobar(p)
    dicho = robot.dicho()
    assert "Sin premio" in dicho and "la última cifra: el reintegro" in dicho and "las dos últimas cifras" in dicho and "las cuatro últimas cifras" in dicho
    assert j.dinero == dinero and len(j.boletos) == 3 and all(b.get("visto") for b in j.boletos)
    # en la tienda cobran los pequeños; el de 6000, solo en la administración
    cobrado, queda = loteria.comprobar(p, tienda)
    assert (cobrado, queda) == (70, 6000) and j.dinero == dinero + 70 and len(j.boletos) == 1
    menus_juego.lugar(p, admin)
    m = robot.app.pila[-1]
    _op(m, "Comprobar y cobrar")
    robot.tecla(pygame.K_RETURN)
    assert j.dinero == dinero + 6070 and not j.boletos and "Cobrado" in robot.dicho()
    robot.tecla(pygame.K_RETURN)
    assert "No tienes boletos por comprobar" in robot.dicho()
    # el tablón del móvil recuerda lo que salió
    loteria.menu_movil(p)
    assert any(o.texto == f"Sorteo del día {hoy}: salió el {loteria.cifras(ganador)}" for o in robot.app.pila[-1].opciones)


def test_el_bote_se_cobra_entero_y_vuelve_a_empezar(robot):
    p, j = _partida(robot, hora=12)
    hoy = p.dia
    admin = _lugar(p, "loteria")
    assert loteria.comprar(p, loteria.premiado(p, hoy), admin)
    bote = j.lot_bote
    p.pasar_horas(10)                                                 # durmiendo también se sortea
    robot.frames(3)
    assert j.lot_ultimo == hoy and j.lot_bote == loteria.BOTE_INICIAL
    dinero = j.dinero
    assert loteria.comprobar(p, _lugar(p, "bar")) == (0, bote)        # en un bar no pagan el bote
    assert loteria.comprobar(p, admin) == (bote, 0) and j.dinero == dinero + bote and "el bote" in robot.dicho()


def test_pasan_varios_dias_y_los_boletos_caducan(robot):
    p, j = _partida(robot, hora=12)
    hoy = p.dia
    ganador = loteria.premiado(p, hoy)
    assert loteria.comprar(p, ("8" if ganador[0] == "9" else "9") + ganador[1:], None)
    p.pasar_horas(24 * 3)
    robot.frames(3)
    assert j.lot_ultimo == p.dia - 1 and len(j.boletos) == 1 and str(hoy) in j.lot_botes
    assert loteria.comprobar(p, hablar=False) == (0, 6000)
    p.pasar_horas(24 * 6)
    robot.frames(3)
    assert not j.boletos                                              # siete días para cobrar
    # una partida guardada antigua no sortea hacia atrás
    j.lot_ultimo = -1
    n = len(robot.app.voz.registro)
    robot.frames(3)
    assert j.lot_ultimo == loteria.ultimo_celebrado(p) and not any("Sorteo de la lotería" in f for f in robot.app.voz.registro[n:])
    d = p.a_dict()["jugador"]
    assert "boletos" in d and "lot_bote" in d
