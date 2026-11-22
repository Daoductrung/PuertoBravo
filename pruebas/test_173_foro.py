"""Versión 1.7.3: lo que se pidió en GitHub y en el foro tras la 1.7.2."""
import math

import pygame
import pytest

from juego import menus_juego


def _al_volante(robot, modelo="utilitario"):
    p = robot.p
    j = p.j
    x, y, rumbo = p.mundo.plaza_aparcamiento(j.x, j.y) if hasattr(p.mundo, "plaza_aparcamiento") else (j.x, j.y, 0)
    v = p.crear_vehiculo(modelo, x, y, rumbo, None)
    p._subir(v, False, callar=True)
    return v


def _viaje(robot, estilo):
    """Un viaje del piloto a un sitio lejano, con el estilo dado: (llegó, velocidad máxima, multas, rojos saltados)."""
    p = robot.nueva_partida()
    p.cfg["conduccion"] = "asistida"
    p.cfg["piloto_gps"] = True
    p.cfg["sucesos"] = False
    p.cfg["piloto_estilo"] = estilo
    v = _al_volante(robot, "deportivo")
    robot.frames(10)
    x0, y0 = v.x, v.y
    destino = max((l for l in p.mundo.lugares.values() if l.tipo in ("banco", "hospital", "taller", "tienda", "farmacia")),
                  key=lambda l: math.hypot(l.x - x0, l.y - y0))
    p.gps_a_lugar(destino, callar=True)
    maxima = 0.0
    for _ in range(500):
        robot.frames(15)
        maxima = max(maxima, v.vel)
        if not p.gps:
            break
    return not p.gps, maxima, v


@pytest.mark.parametrize("estilo,minima,tope", [("normal", 8, 14.5), ("prisa", 14.5, 21.5), ("mucha_prisa", 25, 99)])
def test_estilos_del_piloto(robot, estilo, minima, tope):
    llega, maxima, v = _viaje(robot, estilo)
    assert llega and minima < maxima <= tope, (estilo, maxima)
    assert v.salud > v.salud_max * 0.7                               # toma las curvas sin estrellarse


def test_mayusculas_y_cambia_el_estilo_y_se_dice(robot):
    p = robot.nueva_partida()
    p.cfg["conduccion"] = "asistida"
    p.cfg["piloto_estilo"] = "normal"
    _al_volante(robot)
    robot.tecla(pygame.K_y, pygame.KMOD_SHIFT)
    assert p.cfg["piloto_estilo"] == "prisa" and "con prisa" in robot.dicho().lower()
    robot.tecla(pygame.K_y, pygame.KMOD_SHIFT)
    assert p.cfg["piloto_estilo"] == "mucha_prisa" and "semáforos" in robot.dicho()
    robot.tecla(pygame.K_y, pygame.KMOD_SHIFT)
    assert p.cfg["piloto_estilo"] == "normal"
    assert not p.cfg["piloto_gps"]                                   # Mayúsculas Y no enciende ni apaga el piloto


def test_semaforo_al_conducir_a_mano(robot):
    """Conduciendo tú, se dice el semáforo del próximo cruce, en rojo o en verde, y cuándo cambia."""
    from juego import mundo as M
    p = robot.nueva_partida()
    p.cfg["conduccion"] = "asistida"
    p.cfg["piloto_gps"] = False
    p.cfg["sucesos"] = False
    p.cfg["semaforos_coche"] = True
    v = _al_volante(robot)
    robot.frames(10)
    for o in list(p.vehiculos):
        if o is not v:
            p.quitar_vehiculo(o)
    m = p.mundo
    i, jj = m.NX // 2, m.NY // 2
    v.dir, v.rumbo = 1, 90.0                                         # hacia el este, por una calle, a 30 metros del cruce
    v.x, v.y = i * M.B - 30, jj * M.B - 2
    v.vel = 6.0
    v.aviso_semaforo = None
    dicho = []
    sonidos = []
    original = p.son
    p.son = lambda nombre, *a, **k: (sonidos.append(nombre), original(nombre, *a, **k))[1]
    for _ in range(40):                                              # de rojo a verde y otra vez a rojo: hasta 14 segundos
        p._aviso_semaforo(v)
        p.t += 0.5
        dicho.append(robot.dicho())
    texto = " ".join(dicho)
    assert "Semáforo en" in texto
    assert "semaforo_rojo" in sonidos or "semaforo_verde" in sonidos
    assert "Se pone en" in texto                                     # el cambio, mientras esperas
    p.cfg["semaforos_coche"] = False
    v.aviso_semaforo = None
    sonidos.clear()
    for _ in range(10):
        p._aviso_semaforo(v)
        p.t += 0.5
    assert not any(s.startswith("semaforo_") for s in sonidos)


def test_opciones_del_piloto_y_del_semaforo(robot):
    robot.nueva_partida()
    menus_juego.opciones(robot.app)
    textos = robot.textos_menus() if hasattr(robot, "textos_menus") else None
    from juego.config import OPCIONES, POR_DEFECTO
    assert POR_DEFECTO["piloto_estilo"] == "normal" and OPCIONES["piloto_estilo"] == ["normal", "prisa", "mucha_prisa"]
    assert POR_DEFECTO["semaforos_coche"] is True
