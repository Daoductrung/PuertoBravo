import math
import random

import numpy as np
import pygame


def test_arranque_y_caminar(robot):
    p = robot.nueva_partida()
    x0 = p.j.x
    robot.frames(60, mantener=(pygame.K_RIGHT,))
    assert p.j.x > x0 + 3
    for k in (pygame.K_c, pygame.K_v, pygame.K_t, pygame.K_o, pygame.K_n, pygame.K_k, pygame.K_TAB, pygame.K_b,
              pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_g, pygame.K_q, pygame.K_SPACE, pygame.K_x,
              pygame.K_x, pygame.K_z, pygame.K_F6, pygame.K_F3, pygame.K_F3, pygame.K_F4, pygame.K_F4):
        robot.tecla(k)
        robot.frames(3)
    assert "Calle Mayor" in robot.dicho()


def test_mezcla_sin_errores(robot):
    p = robot.nueva_partida()
    for _ in range(200):
        robot.app.paso(1 / 30)
        o = robot.app.mez.render(1024)
        assert np.isfinite(o).all() and np.abs(o).max() <= 1.0


def test_rutas(app):
    m = app.mundo
    ls = list(m.lugares.values())
    rng = random.Random(3)
    for _ in range(300):
        a, b = rng.choice(ls), rng.choice(ls)
        r = m.ruta(a.x, a.y, b.x, b.y)
        assert r, (a.id, b.id)
        assert math.hypot(r[-1][0] - b.x, r[-1][1] - b.y) < 1.5
        largo = sum(math.hypot(r[k + 1][0] - r[k][0], r[k + 1][1] - r[k][1]) for k in range(len(r) - 1))
        assert largo < abs(a.x - b.x) + abs(a.y - b.y) + 400
    for l in ls:
        assert m.transitable(l.x, l.y), l.id


def test_mono(robot):
    """Pulsa teclas al azar durante mucho rato: nada debe romperse."""
    p = robot.nueva_partida()
    rng = random.Random(5)
    teclas = [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_f, pygame.K_RETURN, pygame.K_SPACE,
              pygame.K_q, pygame.K_TAB, pygame.K_b, pygame.K_c, pygame.K_m, pygame.K_l, pygame.K_ESCAPE, pygame.K_r,
              pygame.K_u, pygame.K_h, pygame.K_j, pygame.K_1, pygame.K_2, pygame.K_4, pygame.K_z, pygame.K_x, pygame.K_g,
              pygame.K_F2, pygame.K_F5, pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_y, pygame.K_e, pygame.K_o,
              pygame.K_n, pygame.K_HOME, pygame.K_END, pygame.K_PAGEUP, pygame.K_COMMA, pygame.K_LCTRL, pygame.K_v]
    robot.app.partida.j.dinero = 5000
    for n in range(6000):
        if not robot.app.pila or not robot.app.activo:
            break
        k = rng.choice(teclas)
        if rng.random() < 0.5:
            robot.tecla(k, mod=pygame.KMOD_SHIFT if rng.random() < 0.1 else 0)
            robot.frames(2)
        else:
            robot.frames(rng.randint(5, 40), mantener=(k, rng.choice(teclas)))
        if n % 500 == 0 and robot.app.partida:
            robot.app.partida.poner_busqueda(rng.randint(1, 5))
    assert robot.app.activo
