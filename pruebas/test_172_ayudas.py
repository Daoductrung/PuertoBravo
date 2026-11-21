"""Cada opción de menú tiene su ayuda propia de F1 (1.7.2). Si una opción no la tiene, F1 solo dice cómo moverse por los
menús, y eso no le sirve a nadie. Las de salir del menú («Volver», «Cancelar», «No»...) la tienen de serie."""
import ast
import glob
import os

import pygame

from juego import menus
from juego.menus import Menu, Opcion

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = ("Volver", "Salir", "Dejarlo", "Cancelar", "Seguir", "Cerrar", "No", "Despedirte", "Colgar", "Marcharte", "Irte", "Ahora no", "Más tarde",
          "Continuar", "Levantarte", "Plantarte", "Retirarte", "Terminar", "Reanudar")


def _texto_literal(n):
    """El texto español de la opción, si se ve en el código: «tr("Volver")» o «"Volver"»."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "tr" and n.args and isinstance(n.args[0], ast.Constant):
        return n.args[0].value
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "format":
        return _texto_literal(n.func.value)
    return None


def test_cada_opcion_de_menu_tiene_su_ayuda():
    sin = []
    for f in sorted(glob.glob(os.path.join(RAIZ, "juego", "*.py"))):
        arbol = ast.parse(open(f, encoding="utf-8").read())
        for n in ast.walk(arbol):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Opcion"):
                continue
            if any(k.arg == "ayuda" for k in n.keywords) or len(n.args) >= 4:
                continue
            t = _texto_literal(n.args[0]) if n.args else None
            if t is not None and t.startswith(SALIDA):
                continue
            sin.append(f"{os.path.basename(f)}:{n.lineno}: {ast.unparse(n.args[0])[:60] if n.args else ''}")
    assert not sin, f"{len(sin)} opciones sin ayuda de F1:\n" + "\n".join(sin[:40])


def test_f1_en_una_opcion_de_salir_dice_que_sale(robot):
    app = robot.app
    m = Menu(app, "Prueba", [Opcion("Algo", lambda: None, ayuda="La ayuda de algo."), Opcion(menus.tr("Volver"), lambda: app.cerrar(m))])
    app.abrir(m)
    m.i = 0
    robot.tecla(pygame.K_F1)
    assert robot.app.voz.registro[-1] == "La ayuda de algo."
    m.i = 1
    robot.tecla(pygame.K_F1)
    assert "Sale de este menú" in robot.app.voz.registro[-1]
