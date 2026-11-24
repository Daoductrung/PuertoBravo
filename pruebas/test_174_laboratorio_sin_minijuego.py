"""El laboratorio sin su minijuego (opción minijuego_laboratorio): la tanda sale al momento, normal y sin arder."""
from juego import config, laboratorio as L, menus_juego
from juego.menus import Menu


class _Fijo:
    """Un azar que nunca saca al vecino del olor."""
    def random(self):
        return 0.99

    def choice(self, s):
        return s[0]


def _laboratorio(robot):
    p = robot.nueva_partida()
    app, j = robot.app, p.j
    casa = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and l.id != "casa_abuela")
    j.propiedades.append(casa.id)
    j.laboratorios.append(casa.id)
    app.cfg["adultos"] = True
    app.aplicar_adultos()
    return p, app, j, casa


def test_viene_con_el_minijuego_puesto():
    assert config.POR_DEFECTO["minijuego_laboratorio"] is True


def test_sin_minijuego_la_tanda_sale_al_momento_normal_y_sin_arder(robot):
    p, app, j, casa = _laboratorio(robot)
    try:
        app.cfg["minijuego_laboratorio"] = False
        cristal = next(s for s in p.dato_adulto("sustancias") if s["id"] == "cristal")
        j.material = 2
        antes = j.sustancias.get("cristal", 0)
        c = L.Coccion(p, casa, cristal, azar=_Fijo())
        c.sin_minijuego()
        esperadas = int(round(4 + 12 * L.CALIDAD_SIN_MINIJUEGO))
        assert c.hecho and j.sustancias.get("cristal", 0) == antes + esperadas and "Una tanda normal" in robot.dicho()
        assert casa.id in j.laboratorios and app.pila[-1] is p                 # no arde, y no queda ninguna pantalla abierta
        # desde el menú del laboratorio: gasta el material y no abre el minijuego
        ops = L.opciones_casa(p, casa, Menu, menus_juego.Opcion)
        ops[0].accion()
        fabricar = next(o for o in app.pila[-1].opciones if o.texto.startswith("Fabricar cristal"))
        assert "al momento" in fabricar.ayuda
        fabricar.accion()
        assert j.material == 1 and not isinstance(app.pila[-1], L.Coccion)
        assert j.sustancias.get("cristal", 0) == antes + 2 * esperadas
    finally:
        app.cfg["minijuego_laboratorio"] = True
        app.cfg["adultos"] = False
        app.aplicar_adultos()


def test_con_minijuego_se_abre_como_siempre(robot):
    p, app, j, casa = _laboratorio(robot)
    try:
        j.material = 1
        ops = L.opciones_casa(p, casa, Menu, menus_juego.Opcion)
        ops[0].accion()
        fabricar = next(o for o in app.pila[-1].opciones if o.texto.startswith("Fabricar cristal"))
        assert "minijuego" in fabricar.ayuda
        fabricar.accion()
        assert isinstance(app.pila[-1], L.Coccion) and j.material == 0
    finally:
        app.cfg["adultos"] = False
        app.aplicar_adultos()
