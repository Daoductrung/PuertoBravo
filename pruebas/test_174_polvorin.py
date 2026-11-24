"""Issue 20: la llave del polvorín (Peñas Altas) queda hecha con cualquiera de las dos opciones de su decisión."""
import pygame
from juego.menus import Dialogo, Menu
import test_misiones as TM


def test_polvorin_con_cada_opcion(robot):
    p = robot.nueva_partida()
    m = next(x for x in p.datos["misiones"] if x["id"] == "pao1")
    for opcion in (0, 1):
        p.completadas = [x for x in p.completadas if x != "pao1"] + (["m01"] if "m01" not in p.completadas else [])
        original = robot.saltar_dialogos

        def saltar(tope=40, original=original):
            for _ in range(tope):
                cima = robot.app.pila[-1]
                if isinstance(cima, Dialogo):
                    robot.tecla(pygame.K_ESCAPE)
                elif isinstance(cima, Menu) and not cima.escapable and cima is not robot.app.pila[0]:
                    cima.i = opcion if len(cima.opciones) > 1 and "polvor" not in cima.titulo.lower() else len(cima.opciones) - 1
                    robot.tecla(pygame.K_RETURN)
                else:
                    return
        robot.saltar_dialogos = saltar
        TM._jugar_mision(robot, m)
        robot.saltar_dialogos = original
        assert "pao1" in p.completadas, (opcion, robot.dicho()[-600:])
        assert p.decisiones["pa_albaran"]["opcion"] == opcion + 1 and "pao1" not in [x["id"] for x in p.misiones_disponibles()]
