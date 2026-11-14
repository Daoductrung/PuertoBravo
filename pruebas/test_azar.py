"""El azar de cada día: ninguna partida es igual a otra, ni un día igual al anterior."""
import pygame

from juego import azar
from juego.menus import Menu


def test_cada_partida_tiene_su_suerte(robot):
    p = robot.nueva_partida()
    assert p.j.semilla > 0
    assert p.a_dict()["jugador"]["semilla"] == p.j.semilla          # se guarda con la partida
    # en las pruebas el azar está apagado para que las cuentas salgan exactas
    assert p.mercado("armas", "armeria_centro") == 1.0 and p.azar_factor("trafico") == 1.0 and p.dia_txt() == ""


def test_los_dias_son_distintos_y_repetibles(robot):
    p = robot.nueva_partida()
    p.azar_forzado = True
    p.j.semilla = 12345
    vistos = {}
    for dia in range(1, 201):
        p.dia = dia
        p.sortear_dia(anunciar=False)
        vistos[p.dia_azar["id"]] = vistos.get(p.dia_azar["id"], 0) + 1
    assert set(vistos) == {d[0] for d in azar.DIAS}                  # en doscientos días salen todos los tipos
    assert vistos["normal"] > 50                                    # y lo normal es lo normal
    # el mismo día de la misma partida es siempre igual (al cargar no cambia)
    p.dia = 7
    p.sortear_dia(anunciar=False)
    uno = (p.dia_azar["id"], p.mercado("comida", "asador"), p.mercado("armas", "armeria_centro"))
    p.sortear_dia(anunciar=False)
    assert uno == (p.dia_azar["id"], p.mercado("comida", "asador"), p.mercado("armas", "armeria_centro"))
    # otra partida, otra suerte: los mismos días no salen igual
    serie = []
    for semilla in (12345, 67890):
        p.j.semilla = semilla
        fila = []
        for dia in range(1, 41):
            p.dia = dia
            p.sortear_dia(anunciar=False)
            fila.append((p.dia_azar["id"], p.mercado("comida", "asador")))
        serie.append(fila)
    assert serie[0] != serie[1]


def test_precios_que_suben_y_bajan(robot):
    p = robot.nueva_partida()
    p.azar_forzado = True
    precios_tienda = set()
    for dia in range(1, 31):
        p.dia = dia
        p.sortear_dia(anunciar=False)
        f = p.mercado("comida", "asador")
        assert 0.6 <= f <= 1.45
        precios_tienda.add(f)
    assert len(precios_tienda) > 20                                 # cada día un precio
    p.dia = 3
    p.sortear_dia(anunciar=False)
    assert p.mercado("comida", "asador") != p.mercado("comida", "chiringuito")      # y cada comercio el suyo
    # se ve en el menú del comercio, y se cobra lo que se dice
    p.dia_azar = {"id": "escasez", "texto": "x", "efectos": {"comida": 2.0, "armas": 2.0}, "dia": 3}
    from juego import menus_juego
    l = p.lugares["asador"]
    menus_juego._comida(p, l)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu)
    m.refrescar(False)
    c = p.datos["comidas"][0]
    factor = p.mercado("comida", "asador") * (3.0 if l.get("caro") else 1.0)
    esperado = int(c["precio"] * factor)
    assert esperado > c["precio"] and f"{esperado} euros" in m.opciones[0].texto
    p.j.salud, p.j.dinero = 20, 1000
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    assert p.j.dinero == 1000 - esperado


def test_el_dia_cambia_la_calle(robot):
    p = robot.nueva_partida()
    p.azar_forzado = True
    p.reloj = 12 * 60

    def gente_y_coches(efectos):
        p.dia_azar = {"id": "x", "texto": "", "efectos": efectos, "dia": p.dia}
        p.personas = [q for q in p.personas if q.tag]
        p.vehiculos = [v for v in p.vehiculos if v.ia != "trafico"]
        for _ in range(400):
            p._poblar()
        return (sum(1 for q in p.personas if q.tipo in ("civil", "banda") and not q.tag),
                sum(1 for v in p.vehiculos if v.ia == "trafico"))
    normal = gente_y_coches({})
    vacio = gente_y_coches({"peatones": 0.3, "trafico": 0.3})
    lleno = gente_y_coches({"peatones": 1.8, "trafico": 1.8})
    assert vacio[0] < normal[0] < lleno[0], (vacio, normal, lleno)
    assert vacio[1] <= normal[1] <= lleno[1] and vacio[1] < lleno[1], (vacio, normal, lleno)


def test_el_dia_se_anuncia_y_se_comenta(robot):
    p = robot.nueva_partida()
    p.azar_forzado = True
    p.j.semilla = 4
    # se busca un día que no sea normal y se llega a él pasando la medianoche
    for dia in range(2, 80):
        p.dia = dia
        p.sortear_dia(anunciar=False)
        if p.dia_azar["texto"]:
            break
    texto = p.dia_azar["texto"]
    p.dia = dia - 1
    p.reloj = 23 * 60 + 59
    robot.app.voz.registro.clear()
    p.pasar_horas(0.1)
    assert p.dia == dia and texto in robot.dicho()
    robot.app.voz.registro.clear()
    robot.tecla(pygame.K_t)
    assert texto in robot.dicho()                                   # la tecla T lo recuerda
    assert any(p.rumor() == texto for _ in range(200))              # y la gente lo comenta
