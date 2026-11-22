"""Realismo opcional de la 1.7.0: sed e higiene, averías y pinchazos, y normas de tráfico con carné por puntos."""
import pygame

from juego import mundo as M
from juego import realismo as R


def _coche(p, modelo="sedan"):
    x, y, d = p.plaza_cercana()
    v = p.crear_vehiculo(modelo, x, y, d, None)
    p.j.x, p.j.y = x + 2, y
    p._subir(v, False, callar=True)
    return v


def _limpiar(robot):
    robot.app.voz.registro.clear()


# ------------------------------------------------------------------ sed e higiene
def test_sin_vida_realista_no_hay_sed_ni_suciedad(robot):
    p = robot.nueva_partida()
    p.pasar_necesidades(600)
    assert p.j.sed == 0 and p.j.suciedad == 0 and p.limpio() and p.necesidades_txt() == ""


def test_sed_e_higiene(robot):
    p = robot.nueva_partida()
    p.cfg["vida_realista"] = True
    try:
        p.pasar_necesidades(R.aj("sed_horas") * 60 * 0.62)
        assert 60 <= p.j.sed < 70 and "Tienes sed" in robot.dicho()
        assert "con sed" in p.necesidades_txt()
        p.ha_comido()                                           # con la comida se bebe algo
        antes = p.j.sed
        assert antes < 62
        p.son("beber", cat="interfaz")                          # beber quita la sed
        assert p.j.sed < antes - 40
        p.j.sed = 90
        assert p.mod_necesidades() < 1.0
        p.j.sed, salud = 100.0, p.j.salud
        p.pasar_necesidades(60)
        assert p.j.salud < salud
        # higiene
        p.j.suciedad = 89.0
        animo = p.j.animo
        _limpiar(robot)
        p.pasar_necesidades(60)
        assert p.j.suciedad >= 90 and "Hueles mal" in robot.dicho() and p.j.animo < animo and not p.limpio()
        assert "dúchate" in p.necesidades_txt()
        p.ha_duchado()
        assert p.j.suciedad == 0 and p.limpio()
    finally:
        p.cfg["vida_realista"] = False


# ------------------------------------------------------------------ averías
def test_las_averias_vienen_desactivadas(robot):
    p = robot.nueva_partida()
    assert p.cfg["averias"] is False and p.cfg["normas_trafico"] is False
    v = _coche(p)
    v.vel = 20.0
    p.rodar(v, 100.0)
    assert not getattr(v, "km", 0) and p.factor_averia_velocidad(v) == 1.0 and p.averias_txt(v) == ""


def test_kilometros_pinchazo_y_rueda_de_repuesto(robot, monkeypatch):
    p = robot.nueva_partida()
    p.cfg["averias"] = True
    try:
        v = _coche(p)
        v.vel = 20.0
        monkeypatch.setattr(R.random, "random", lambda: 1.0)       # sin suerte mala
        p.rodar(v, 50.0)
        assert abs(v.km - 1.0) < 0.001 and not getattr(v, "pinchada", False)
        monkeypatch.setattr(R.random, "random", lambda: 0.0)       # y ahora, con ella
        _limpiar(robot)
        p.rodar(v, 0.1)
        assert v.pinchada and "Has pinchado" in robot.dicho()
        assert p.factor_averia_velocidad(v) == 0.45 and p.factor_averia_frenos(v) < 1.0 and "rueda pinchada" in p.averias_txt(v)
        assert not p.cambiar_rueda()                               # en marcha no
        v.vel = 0.0
        _limpiar(robot)
        assert not p.cambiar_rueda() and "No llevas rueda de repuesto" in robot.dicho()
        p.j.objetos["rueda"] = 1
        assert p.cambiar_rueda() and not v.pinchada and p.j.objetos["rueda"] == 0
        assert p.factor_averia_velocidad(v) == 1.0
    finally:
        p.cfg["averias"] = False


def test_la_revision(robot, monkeypatch):
    p = robot.nueva_partida()
    p.cfg["averias"] = True
    monkeypatch.setattr(R.random, "random", lambda: 1.0)
    try:
        v = _coche(p)
        v.km = R.aj("revision_km") - 0.01
        v.vel = 20.0
        _limpiar(robot)
        p.rodar(v, 1.0)
        assert v.revision_debida and "le toca revisión" in robot.dicho()
        v.km += R.aj("revision_km") * 0.5
        assert 0.6 <= p.factor_averia_frenos(v) < 1.0
        p.pasar_revision(v)
        assert not v.revision_debida and p.factor_averia_frenos(v) == 1.0
        d = p.averias_a_dict(v, {})
        assert d["km"] > 0 and "pinchada" not in d
        v.pinchada = True
        d = p.averias_a_dict(v, {})
        w = p.crear_vehiculo("sedan", v.x + 10, v.y, 0, None)
        p.averias_de_dict(w, d)
        assert w.pinchada and w.km == d["km"]
    finally:
        p.cfg["averias"] = False


# ------------------------------------------------------------------ normas de tráfico
def _patrulla_cerca(p, v):
    pa = p.crear_vehiculo("patrulla", v.x + 20, v.y, 0, "policia")
    return pa


def test_multa_por_exceso_de_velocidad_solo_si_te_ven(robot):
    p = robot.nueva_partida()
    p.cfg["normas_trafico"] = True
    try:
        v = _coche(p, "deportivo")
        for o in list(p.vehiculos):
            if o is not v:
                p.quitar_vehiculo(o)
        p.personas[:] = [e for e in p.personas if e.tipo != "policia"]
        v.vel = 25.0                                              # 90 por hora: por encima del doble del límite, la multa es doble
        p.j.dinero = 1000
        dinero, puntos = p.j.dinero, p.j.carne_puntos
        for _ in range(60):
            p.vigilar_velocidad(v, 0.1)
        assert p.j.dinero == dinero and p.j.carne_puntos == puntos        # nadie mirando: no pasa nada
        _patrulla_cerca(p, v)
        _limpiar(robot)
        for _ in range(60):
            p.vigilar_velocidad(v, 0.1)
        assert p.j.dinero == dinero - R.aj("multa_velocidad") and p.j.carne_puntos == puntos - R.aj("puntos_velocidad")
        assert "exceso de velocidad" in robot.dicho() and "90" in robot.dicho()
        # dentro del margen, nada
        p.t += 100
        v.vel = 16.0                                              # 57 por hora: dentro del treinta por ciento
        for _ in range(80):
            p.vigilar_velocidad(v, 0.1)
        assert p.j.carne_puntos == puntos - R.aj("puntos_velocidad")
    finally:
        p.cfg["normas_trafico"] = False


def test_semaforo_en_rojo_y_retirada_del_carne(robot):
    p = robot.nueva_partida()
    p.cfg["normas_trafico"] = True
    try:
        v = _coche(p)
        _patrulla_cerca(p, v)
        i, jj = 3, 3
        verde_v = p.mundo.verde_vertical(i, jj, p.t)
        v.dir = 1 if verde_v else 0                              # la dirección para la que ahora está en rojo
        v.vel = 10.0
        p.j.dinero = 1000
        p.j.carne_puntos = 4
        _limpiar(robot)
        assert p.infraccion_semaforo(v, i, jj)
        assert p.j.carne_puntos == 0 and p.j.dinero == 1000 - R.aj("multa_semaforo") and "te retiran el carné" in robot.dicho()
        v.dir = 0 if verde_v else 1                              # en verde no hay multa
        p.t_multa = -99
        assert not p.infraccion_semaforo(v, i, jj)
        assert "retirado el carné" in p.carne_txt()
        # sin carné, delante de un agente: delito
        p.t_sin_carne = -99
        v.vel = 5.0
        p.vigilar_velocidad(v, 0.1)
        assert p.j.puntos_busqueda > 0 or p.j.estrellas > 0
        # el curso devuelve puntos
        p._fin_persecucion()
        p.j.dinero = 1000
        assert p.recuperar_carne() and p.j.carne_puntos == R.aj("puntos_curso") and p.j.dinero == 1000 - R.aj("precio_carne")
    finally:
        p.cfg["normas_trafico"] = False


def test_con_sirena_o_buscado_no_hay_multas(robot):
    p = robot.nueva_partida()
    p.cfg["normas_trafico"] = True
    try:
        v = _coche(p)
        _patrulla_cerca(p, v)
        v.vel = 30.0
        p.j.estrellas = 2
        puntos = p.j.carne_puntos
        for _ in range(80):
            p.vigilar_velocidad(v, 0.1)
        assert p.j.carne_puntos == puntos
        p.j.estrellas = 0
    finally:
        p.cfg["normas_trafico"] = False


def test_los_numeros_del_realismo_estan_en_los_datos(robot):
    from editor import esquema as E
    p = robot.nueva_partida()
    d = p.datos["realismo"][0]
    campos = {c["k"] for c in E.ESQUEMAS["ajuste_realismo"]["campos"]}
    assert set(d) <= campos and set(R.AJUSTES) <= set(d)
    assert all(R.aj(k) == d[k] for k in R.AJUSTES)
    assert M.SECCIONES_VIDA[-1] == "realismo" or "realismo" in M.SECCIONES_VIDA
    assert pygame is not None


# ------------------------------------------------------------------ en los menús
def _opciones(robot):
    m = robot.app.pila[-1]
    ops = m.opciones() if callable(getattr(m, "opciones", None)) else m.opciones
    return [o.texto for o in ops]


def test_el_taller_cambia_ruedas_y_pasa_revisiones(robot):
    from juego import menus_juego as mj
    p = robot.nueva_partida()
    p.cfg["averias"] = True
    try:
        p.j.dinero = 2000
        v = _coche(p)
        v.pinchada, v.km, v.revision_debida = True, 51.0, True
        l = next(x for x in p.mundo.lugares.values() if x.tipo == "taller")
        mj._taller(p, l)
        textos = _opciones(robot)
        assert any("Cambiar la rueda pinchada" in t for t in textos) and any("Pasar la revisión" in t and "Le toca" in t for t in textos)
        assert any("Rueda de repuesto" in t for t in textos)
        m = robot.app.pila[-1]
        ops = m.opciones() if callable(getattr(m, "opciones", None)) else m.opciones
        next(o for o in ops if "Pasar la revisión" in o.texto).accion()
        assert not v.pinchada and not v.revision_debida and p.j.dinero == 2000 - R.aj("precio_revision")
        next(o for o in ops if "Rueda de repuesto" in o.texto).accion()
        assert p.j.objetos["rueda"] == 1
    finally:
        p.cfg["averias"] = False


def test_agua_en_los_bares_y_curso_del_carne(robot):
    from juego import menus_juego as mj
    from juego import menus_vida as mv
    p = robot.nueva_partida()
    assert mj._agua(p) == []
    p.cfg["vida_realista"] = True
    p.cfg["normas_trafico"] = True
    try:
        p.j.dinero, p.j.sed = 100, 80.0
        op = mj._agua(p)[0]
        op.accion()
        assert p.j.sed < 20 and p.j.dinero == 99
        l = next(x for x in p.lugares.values() if x.tipo == "academia")
        p.j.carne_puntos = 2
        mv.academia(p, l)
        assert any("recuperación de puntos" in t for t in _opciones(robot))
    finally:
        p.cfg["vida_realista"] = False
        p.cfg["normas_trafico"] = False
