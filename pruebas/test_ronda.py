"""Ronda completa: se entra en todos los menús, opciones y lugares del juego y se pulsa todo,
y se juega una partida larga con el tiempo acelerado para comprobar que todo es coherente.

No sustituye a las demás pruebas (misiones, GPS, mando, red...): las completa pasando por lo que
ninguna otra toca, buscando errores, menús de los que no se puede salir y frases mal construidas.
"""
import math
import re

import pygame

from juego import menus_juego
from juego.menus import Dialogo, EntradaTexto, Menu

# Opciones que no se pulsan: salen del juego, cambian de partida, abren el navegador o usan la red.
PROHIBIDAS = ("salir", "nueva partida", "cargar partida", "continuar", "abrir mi partida", "unirme a la partida", "para amigos de fuera",
              "abrir el manual", "cerrar mi partida", "desconectarme")
BASURA = re.compile(r"\bNone\b|\bnan\b|[{}<>]|object at 0x|Traceback|\bTrue\b|\bFalse\b|\binf\b")


class Ronda:
    def __init__(self, robot):
        self.robot = robot
        self.app = robot.app
        self.pulsadas = 0
        self.menus = 0
        self.vistas = 0
        self.leido = 0

    def revisar_voz(self, donde):
        """Nada de lo que se ha dicho puede llevar restos de programación ni frases vacías."""
        reg = self.app.voz.registro
        for frase in reg[self.leido:]:
            assert isinstance(frase, str) and frase.strip(), f"frase vacía en {donde}"
            assert not BASURA.search(frase), f"frase rara en {donde}: {frase!r}"
        self.leido = len(reg)

    def sanear(self):
        """Deja al jugador en condiciones de seguir: vivo, con dinero y sin policía."""
        p = self.app.partida
        if p is None:
            return
        j = p.j
        j.salud = j.salud_max
        j.dinero = max(j.dinero, 60000)
        if j.estrellas:
            p._fin_persecucion()

    def volver_a(self, base):
        app = self.app
        for _ in range(40):
            if not app.pila or base not in app.pila:
                return False
            cima = app.pila[-1]
            if cima is base:
                return True
            if isinstance(cima, Menu) and not cima.escapable:
                cima.i = len(cima.opciones) - 1
                self.robot.tecla(pygame.K_RETURN)
            else:
                self.robot.tecla(pygame.K_ESCAPE)
            self.robot.frames(1)
        return app.pila and app.pila[-1] is base

    def recorrer_todo(self, abrir, donde, prof=2, tope=30):
        """Recorre un menú entero. Si una opción lo cierra, lo vuelve a abrir con abrir() y sigue por la siguiente."""
        i = 0
        for _ in range(tope + 2):
            abrir()
            self.robot.frames(1)
            base = self.app.pila[-1]
            if not isinstance(base, Menu):
                return
            i = self.recorrer(base, donde, prof, tope, inicio=i)
            if i is None:
                return

    def recorrer(self, base, donde, prof=2, tope=30, inicio=0):
        """Pasa por las opciones de un menú: ayuda, ajuste a los dos lados e Intro. Entra en los submenús.

        Devuelve None si ha llegado al final, o el índice por el que seguir si una opción ha cerrado el menú."""
        app, robot = self.app, self.robot
        assert isinstance(base, Menu), f"{donde}: no es un menú"
        self.menus += 1
        assert isinstance(base.titulo, str) and base.titulo.strip(), f"{donde}: menú sin título"
        i = inicio
        while i < min(len(base.opciones), tope):
            base.refrescar(False)
            if i >= len(base.opciones):
                break
            o = base.opciones[i]
            texto = o.texto
            assert isinstance(texto, str) and texto.strip(), f"{donde}: opción {i} sin texto"
            self.vistas += 1
            base.i = i
            robot.tecla(pygame.K_F1)
            i += 1
            if any(x in texto.lower() for x in PROHIBIDAS):
                continue
            if o.ajuste:
                robot.tecla(pygame.K_RIGHT)
                robot.tecla(pygame.K_LEFT)
                self.pulsadas += 2
            if o.accion:
                robot.tecla(pygame.K_RETURN)
                robot.frames(2)
                self.pulsadas += 1
                assert app.activo, f"{donde}: «{texto}» ha cerrado el juego"
                cima = app.pila[-1] if app.pila else None
                if cima is not base and base in app.pila:
                    if isinstance(cima, Menu) and prof > 1:
                        sigue = self.recorrer(cima, f"{donde} > {texto[:40]}", prof - 1, tope)
                        for _ in range(tope):            # si una opción del submenú lo cerró, se vuelve a entrar y se sigue
                            if sigue is None or base not in app.pila or not self.volver_a(base):
                                break
                            self.sanear()
                            base.refrescar(False)
                            if i - 1 >= len(base.opciones) or not base.opciones[i - 1].accion:
                                break
                            base.i = i - 1
                            robot.tecla(pygame.K_RETURN)
                            robot.frames(2)
                            cima = app.pila[-1] if app.pila else None
                            if cima is base or not isinstance(cima, Menu) or base not in app.pila:
                                break
                            sigue = self.recorrer(cima, f"{donde} > {texto[:40]}", prof - 1, tope, inicio=sigue)
                    elif isinstance(cima, EntradaTexto):
                        robot.tecla(pygame.K_a, unicode="a")
                    elif not isinstance(cima, (Menu, Dialogo)):
                        for k in (pygame.K_UP, pygame.K_RIGHT, pygame.K_SPACE, pygame.K_TAB, pygame.K_RETURN):      # minijuegos y pantallas especiales
                            if app.pila[-1] is cima:
                                robot.tecla(k)
                                robot.frames(3)
            self.sanear()
            self.revisar_voz(f"{donde} > {texto[:40]}")
            if base not in app.pila:
                return i if i < min(len(base.opciones), tope) else None      # la opción ha cerrado el menú: se sigue por la siguiente
            assert self.volver_a(base), f"{donde}: después de «{texto}» no se puede volver al menú"
        return None


def test_ronda_de_menus_opciones_y_movil(robot):
    """Menú principal, todas las secciones de Opciones, la pausa y el móvil entero."""
    app = robot.app
    r = Ronda(robot)
    r.recorrer(app.pila[-1], "Menú principal", prof=4)
    assert r.menus > 12, r.menus
    assert app.pila and isinstance(app.pila[0], Menu)
    # todas las opciones vuelven a su valor: se han pulsado derecha e izquierda
    p = robot.nueva_partida()
    r.leido = len(app.voz.registro)
    def al_juego():
        for _ in range(40):
            if app.pila and app.pila[-1] is app.partida:
                return
            cima = app.pila[-1]
            if isinstance(cima, Menu) and not cima.escapable:
                cima.i = len(cima.opciones) - 1
                robot.tecla(pygame.K_RETURN)
            else:
                robot.tecla(pygame.K_ESCAPE)
            robot.frames(1)

    r.recorrer_todo(lambda: (al_juego(), menus_juego.pausa(p)), "Pausa", prof=4)
    al_juego()
    for adultos in (False, True):
        app.cfg["adultos"] = adultos
        app.aplicar_adultos()
        for _ in range(2):                          # dos pasadas: lo que la primera cambia, la segunda lo encuentra cambiado
            r.recorrer_todo(lambda: (al_juego(), menus_juego.movil(p)), "Móvil" + (" adultos" if adultos else ""), prof=3)
            al_juego()
            assert app.partida is p and app.pila[-1] is p
    app.cfg["adultos"] = False
    app.aplicar_adultos()
    assert r.menus > 80 and r.vistas > 700 and r.pulsadas > 500, (r.menus, r.vistas, r.pulsadas)
    # y con todo lo pulsado se puede seguir jugando
    p.desconectar_online()
    x0, y0 = p.pos()
    robot.frames(30, mantener=(pygame.K_UP,))
    robot.frames(30, mantener=(pygame.K_RIGHT,))
    assert p.pos() != (x0, y0)


def test_ronda_de_todos_los_lugares(robot):
    """Se entra en todos los lugares de todas las localidades, y en uno de cada tipo se pulsa todo."""
    app = robot.app
    app.cfg["adultos"] = True
    app.aplicar_adultos()
    p = robot.nueva_partida()
    r = Ronda(robot)
    r.leido = len(app.voz.registro)
    entrados, a_fondo, tipos = 0, 0, set()
    for mapa in list(p.mapas.values()):
        for l in list(mapa.lugares.values()):
            p = app.partida
            assert p is not None, f"la partida se ha perdido antes de {l.id}"
            if p.j.veh:
                p.salir_vehiculo(forzado=True)
            if p.mundo.id != l.mapa:
                p.cambiar_mapa(l.mapa, l.x, l.y)
            p.j.x, p.j.y = l.x, l.y
            r.sanear()
            robot.frames(2)
            while app.pila[-1] is not p:
                robot.tecla(pygame.K_ESCAPE)
            menus_juego.lugar(p, l)
            entrados += 1
            robot.frames(1)
            cima = app.pila[-1]
            clave = (l.tipo, l.mapa == "mar")
            if isinstance(cima, Menu) and cima is not p:
                if clave not in tipos:
                    tipos.add(clave)
                    a_fondo += 1

                    def reabrir(l=l):
                        p = app.partida
                        for _ in range(40):
                            if app.pila and app.pila[-1] is p:
                                break
                            c = app.pila[-1]
                            if isinstance(c, Menu) and not c.escapable:
                                c.i = len(c.opciones) - 1
                                robot.tecla(pygame.K_RETURN)
                            else:
                                robot.tecla(pygame.K_ESCAPE)
                        if p.j.veh:
                            p.j.veh.vel = 0
                            p.salir_vehiculo(forzado=True)
                        if p.mundo.id != l.mapa:
                            p.cambiar_mapa(l.mapa, l.x, l.y)
                        p.j.x, p.j.y = l.x, l.y
                        r.sanear()
                        menus_juego.lugar(p, l)
                    resto = r.recorrer(cima, f"{l.nombre} ({l.tipo})", prof=3, tope=22)
                    if resto is not None:
                        i0 = resto
                        for _ in range(24):
                            reabrir()
                            robot.frames(1)
                            c = app.pila[-1]
                            if not isinstance(c, Menu) or c is app.partida:
                                break
                            i0 = r.recorrer(c, f"{l.nombre} ({l.tipo})", prof=3, tope=22, inicio=i0)
                            if i0 is None:
                                break
                else:
                    assert cima.titulo.strip() and all(o.texto.strip() for o in cima.opciones), l.id
            r.revisar_voz(f"lugar {l.id}")
            for _ in range(40):
                if app.pila and app.pila[-1] is app.partida:
                    break
                cima = app.pila[-1]
                if isinstance(cima, Menu) and not cima.escapable:
                    cima.i = len(cima.opciones) - 1
                    robot.tecla(pygame.K_RETURN)
                else:
                    robot.tecla(pygame.K_ESCAPE)
                robot.frames(1)
            assert app.pila and app.pila[-1] is app.partida, f"de {l.nombre} ({l.tipo}) no se puede salir"
            app.partida.salir_interior(silencio=True)
    app.cfg["adultos"] = False
    app.aplicar_adultos()
    assert entrados > 280 and a_fondo >= 30, (entrados, a_fondo)      # los monumentos y sitios sin servicios no abren menú
    assert r.vistas > 250 and r.pulsadas > 200, (r.vistas, r.pulsadas)


def _coherente(p, donde):
    j = p.j
    assert 0 <= j.salud <= j.salud_max + 0.01, f"{donde}: salud {j.salud}"
    assert j.dinero >= 0 and j.banco >= 0, f"{donde}: dinero {j.dinero}, banco {j.banco}"
    assert 0 <= j.estrellas <= 5, f"{donde}: búsqueda {j.estrellas}"
    assert 0 <= p.reloj < 24 * 60 + 0.01, f"{donde}: reloj {p.reloj}"
    x, y = p.pos()
    assert math.isfinite(x) and math.isfinite(y), f"{donde}: posición {x}, {y}"
    assert 0 <= j.animo <= 100 and 0 <= j.ciudadania <= 100, f"{donde}: ánimo {j.animo}, prestigio {j.ciudadania}"
    for hab in ("conduccion", "punteria", "resistencia", "pesca"):
        assert 0 <= p.nivel(hab) <= 10, f"{donde}: {hab} {p.nivel(hab)}"
    assert p.hora_txt() and p.objetivo_txt() and p.mundo.describir(x, y), donde


def test_partida_larga_con_el_tiempo_acelerado(robot):
    """Veinte días de juego: trabajo, comida, compras, misiones, conducir, pescar, dormir, guardar y cargar."""
    import test_misiones
    from test_vida import _elegir
    app = robot.app
    p = robot.nueva_partida()
    r = Ronda(robot)
    r.leido = len(app.voz.registro)
    dia0 = p.dia
    ganado_trabajando = 0
    for n in range(20):
        p = app.partida
        j = p.j
        donde = f"día {p.dia}"
        _coherente(p, donde + ", al despertar")
        if p.mundo.id != "puerto_bravo":
            l = p.mapas["puerto_bravo"].lugares["hospital"]
            p.cambiar_mapa("puerto_bravo", l.x, l.y)
        if j.veh:
            j.veh.vel = 0
            p.salir_vehiculo(forzado=True)
        # por la mañana, una jornada de trabajo honrado
        of = p.lugares["empleo_pb"]
        j.x, j.y = of.x, of.y
        robot.frames(8)
        antes = j.dinero
        robot.tecla(pygame.K_RETURN)
        if isinstance(app.pila[-1], Menu):
            _elegir(robot, "Jornada de")
            while app.pila[-1] is not p:
                robot.tecla(pygame.K_ESCAPE)
        assert j.dinero >= antes, f"{donde}: trabajar no puede costar dinero"
        ganado_trabajando += j.dinero - antes
        _coherente(p, donde + ", tras trabajar")
        # comer
        j.salud = max(20.0, j.salud - 30)
        sitio = next(l for l in p.mundo.lugares.values() if l.tipo == "comida")
        j.x, j.y = sitio.x, sitio.y
        robot.frames(8)
        robot.tecla(pygame.K_RETURN)
        if isinstance(app.pila[-1], Menu):
            salud = j.salud
            robot.tecla(pygame.K_RETURN)
            assert j.salud >= salud, f"{donde}: comer no puede quitar salud"
            while app.pila[-1] is not p:
                robot.tecla(pygame.K_ESCAPE)
        # cada dos días, la siguiente misión de la historia
        if n % 2 == 0:
            disp = [m for m in p.misiones_disponibles()]
            if disp:
                hechas = len(p.completadas)
                test_misiones._jugar_mision(robot, disp[0])
                robot.saltar_dialogos()
                assert len(p.completadas) == hechas + 1, f"{donde}: la misión {disp[0]['id']} no se completó"
                _coherente(p, donde + ", tras la misión")
        # cada tres días, un rato al volante con el piloto del GPS
        if n % 3 == 1:
            if p.mundo.id != "puerto_bravo":
                l = p.mapas["puerto_bravo"].lugares["hospital"]
                p.cambiar_mapa("puerto_bravo", l.x, l.y)
            p._fin_persecucion()
            x, y, d = p.mundo.plaza_junto_a(p.lugares["parada_taxi"])
            v = p.crear_vehiculo("taxi", x, y, d, None)
            j.x, j.y = p.mundo.punto_libre(x + 2, y + 2)
            p._subir(v, False, callar=True)
            p.cfg["piloto_gps"] = True
            metros = j.stats.get("metros_coche", 0)
            p.gps_a_lugar(p.lugares["hospital"])
            for _ in range(500):
                if not p.gps:
                    break
                v.salud = v.salud_max
                j.salud = j.salud_max
                robot.frames(5, mantener=(pygame.K_UP,) if v.vel < 14 else ())
            assert p.j.veh is v, f"{donde}: te has quedado sin coche conduciendo"
            v.vel = 0.0
            robot.frames(3)
            p.salir_vehiculo(forzado=True)
            p.quitar_vehiculo(v)
            p._fin_persecucion()
            _coherente(p, donde + ", tras conducir")
        # cada cuatro días: guardar, cargar y comprobar que la partida es la misma
        if n % 4 == 3:
            assert menus_juego.escribir_ranura(p, "3")
            foto = (j.dinero, j.banco, p.dia, sorted(p.completadas), round(j.ciudadania, 3), dict(j.objetos), sorted(j.armas), j.nombre)
            app.empezar_partida(menus_juego.leer_ranura("3"))
            robot.saltar_dialogos()
            p = app.partida
            j = p.j
            assert (j.dinero, j.banco, p.dia, sorted(p.completadas), round(j.ciudadania, 3), dict(j.objetos), sorted(j.armas), j.nombre) == foto, f"{donde}: al cargar no es la misma partida"
            _coherente(p, donde + ", tras cargar")
        # y a dormir hasta el día siguiente: el tiempo corre
        dia = p.dia
        horas = (24 * 60 - p.reloj) / 60 + 8
        p.pasar_horas(horas)
        robot.frames(5)
        robot.saltar_dialogos()
        assert p.dia == dia + 1, f"{donde}: tras dormir {horas:.1f} horas el día no avanza"
        assert abs(p.reloj - 8 * 60) < 2, f"{donde}: te despiertas a las {p.hora_txt()}"
        r.revisar_voz(donde)
    p = app.partida
    assert p.dia == dia0 + 20
    assert ganado_trabajando > 1500 and len(p.completadas) >= 9
    assert p.j.ciudadania > 20 and p.servicios_de("jornada") >= 18
    _coherente(p, "final")
