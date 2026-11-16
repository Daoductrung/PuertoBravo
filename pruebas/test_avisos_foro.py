"""Lo que contaron al probar la 1.6.2: reintentar una misión tras una detención, el GPS que vuelve a la misión,
los botones del mando en lugar de las teclas, el piloto que se detiene al llegar, el vehículo que te espera y el garaje."""
import io

import pygame
import pytest

from juego import actualizador as A
from juego import mando, menus_extra, menus_juego
from juego.menus import Dialogo, Menu


def _partida(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.j.dinero = 5000
    robot.frames(2)
    return p, p.j


def _mision(p, mid):
    m = next(x for x in p.datos["misiones"] if x["id"] == mid)
    l = p.lugares[m["lugar"]]
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.teletransportar(l.x, l.y)
    p.iniciar_mision(m)
    return m


def _pasar_escenas(robot, tope=30):
    for _ in range(tope):
        c = robot.app.pila[-1]
        if isinstance(c, Dialogo):
            robot.tecla(pygame.K_ESCAPE)
        else:
            return


def _op(m, trozo):
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if trozo in o.texto)


# ------------------------------------------------------------------ misiones
def test_detenido_justo_al_acabar_no_falla_ni_regala_la_mision(robot):
    """Cae el objetivo y, en el mismo instante, te detienen: la escena final quedaba abierta debajo del menú de fallo y,
    al reintentar, hacía avanzar la misión nueva hasta darla por completada sin jugarla."""
    p, j = _partida(robot)
    m = _mision(p, "v04")                                        # El capataz, en la bodega de Villaseca: una persecución
    _pasar_escenas(robot)
    robot.frames(3)
    ms = p.mision
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "perseguir" and ms["veh_objetivo"] is not None
    p.quitar_vehiculo(ms["veh_objetivo"])                        # destruido
    p.actualizar_mision(0.03)
    assert isinstance(robot.app.pila[-1], Dialogo) and p.mision_en_escena()
    j.estrellas = 3
    p.detener(True)                                              # y en ese instante, la policía
    robot.tecla(pygame.K_ESCAPE)                                 # la escena del calabozo
    # lo que había que hacer estaba hecho: la misión no se falla, y su escena final sigue ahí
    assert p.mision is ms and isinstance(robot.app.pila[-1], Dialogo) and "fallida" not in robot.dicho()
    _pasar_escenas(robot)
    assert "v04" in p.completadas and p.mision is None


def test_una_escena_vieja_no_hace_avanzar_la_mision_reintentada(robot):
    p, j = _partida(robot)
    m = _mision(p, "v04")
    _pasar_escenas(robot)
    robot.frames(3)
    ms = p.mision
    p.quitar_vehiculo(ms["veh_objetivo"])
    p.actualizar_mision(0.03)
    vieja = robot.app.pila[-1]
    assert isinstance(vieja, Dialogo)
    p.fallar_mision("Prueba.")                                   # por lo que sea, la misión se falla con su escena abierta
    assert vieja not in robot.app.pila                           # la escena se va con la misión
    menu = robot.app.pila[-1]
    _op(menu, "Reintentar desde el principio")
    robot.tecla(pygame.K_RETURN)
    _pasar_escenas(robot)
    robot.frames(5)
    nueva = p.mision
    assert nueva is not None and nueva is not ms and "v04" not in p.completadas
    assert nueva["def"]["pasos"][nueva["paso"]]["tipo"] == "perseguir" and nueva["veh_objetivo"] is not None
    # y aunque la escena vieja terminara ahora, no movería la misión nueva
    paso = nueva["paso"]
    if vieja.al_terminar:
        vieja.al_terminar()
    assert p.mision is nueva and nueva["paso"] == paso


def test_detenido_en_mitad_de_la_mision_se_falla_y_se_reintenta_bien(robot):
    p, j = _partida(robot)
    _mision(p, "m04")                                            # Morosos: los guardaespaldas del chiringuito
    _pasar_escenas(robot)
    robot.frames(3)
    ms = p.mision
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "eliminar"
    j.estrellas = 3
    p.detener(True)
    robot.tecla(pygame.K_ESCAPE)
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu) and "Te han detenido" in menu.titulo
    _op(menu, "Reintentar desde el principio")
    robot.tecla(pygame.K_RETURN)
    _pasar_escenas(robot)
    robot.frames(30)
    assert p.mision is not None and "m04" not in p.completadas
    assert p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "eliminar"


def test_dejar_atras_el_vehiculo_de_la_mision_mientras_te_busca_la_policia(robot):
    """Robar, despistar a la policía y entregar: si en el paso de la policía cambias de localidad sin el vehículo,
    la misión se falla con su motivo en vez de quedarse colgada."""
    p, j = _partida(robot)
    _mision(p, "m08")
    _pasar_escenas(robot)
    robot.frames(3)
    ms = p.mision
    v = ms["veh"]
    assert v is not None
    p._subir(v, True)
    robot.frames(3)
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "policia"
    p.salir_vehiculo(forzado=True)
    otro = next(k for k in p.mapas if k != p.mundo.id and p.mapas[k].tipo != "mar")
    p.cambiar_mapa(otro, 100, 100)
    assert p.mision is None and "Has dejado atrás el vehículo" in robot.app.pila[-1].titulo


def test_el_gps_vuelve_a_la_mision_despues_de_un_desvio(robot):
    p, j = _partida(robot)
    _mision(p, "m02")                                            # El recado: ir a un sitio
    _pasar_escenas(robot)
    robot.frames(3)
    ms = p.mision
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "ir" and p.gps and p.gps["auto"]
    destino = p.gps["nombre"]
    # te desvías: marcas otro sitio, llegas, y el GPS se queda sin destino
    otro = next(l for l in p.mundo.lugares.values() if l.tipo == "tienda")
    p.gps_a_lugar(otro)
    assert not p.gps["auto"]
    p.gps = None
    robot.frames(80)
    assert p.gps is not None and p.gps["auto"] and p.gps["nombre"] == destino
    assert "El GPS vuelve a la misión" in robot.dicho()
    # si lo quitas tú con Mayúsculas G, no vuelve solo; con la G lo recuperas
    robot.tecla(pygame.K_g, pygame.KMOD_SHIFT)
    assert p.gps is None and "Con la G vuelves a marcar la misión" in robot.dicho()
    robot.frames(120)
    assert p.gps is None
    robot.tecla(pygame.K_g)
    assert p.gps is not None and p.gps["nombre"] == destino


def test_la_persecucion_afloja_si_el_objetivo_se_escapa(robot):
    p, j = _partida(robot)
    p.cfg["dificultad"] = "normal"
    _mision(p, "m10")
    _pasar_escenas(robot)
    robot.frames(3)
    ms = p.mision
    vo = ms["veh_objetivo"]
    base = ms["vel_huida"]
    assert base == pytest.approx(min(vo.modelo["vel_max"] * 0.54, 21.0))
    x, y = p.pos()
    vo.x, vo.y = x + 200, y
    p.actualizar_mision(0.03)
    assert vo.vel_obj == pytest.approx(base * 0.55) and "se confía y afloja" in robot.dicho()
    vo.x, vo.y = x + 30, y
    p.actualizar_mision(0.03)
    assert vo.vel_obj == pytest.approx(base)


# --------------------------------------------------------------------- mando
def test_con_mando_las_teclas_se_dicen_como_botones():
    f = lambda t, c="pie", tipo="xbox": mando.textos_mando(t, mando.POR_DEFECTO, tipo, c)
    assert f("Hay 3 enemigos. Pulsa Q para fijar al más cercano.") == "Hay 3 enemigos. Pulsa el gatillo izquierdo para fijar al más cercano."
    assert f("Pulsa Q para fijarlo.", tipo="ps") == "Pulsa el botón L2 para fijarlo."
    assert f("Te subes con la F.") == "Te subes con el botón Y."
    assert f("Pulsa Espacio para disparar y R para recargar.") == "Pulsa el gatillo derecho para disparar y el botón X para recargar."
    assert f("El freno de mano va con Espacio.") == "El freno de mano va con el botón B."
    assert f("Muévete con las flechas. Mantén Mayúsculas para correr.") == "Muévete con la palanca izquierda. Empuja a fondo la palanca izquierda para correr."
    assert f("Arrancas con flecha arriba para acelerar.") == "Arrancas con el gatillo derecho para acelerar."
    assert f("La tecla M abre el móvil.") == "El botón Vista abre el móvil."
    # lo que no tiene botón se queda con su tecla, y una Y que no es una tecla no se toca
    assert f("Pulsa Mayúsculas Y para el menú del perro.") == "Pulsa Mayúsculas Y para el menú del perro."
    assert f("Con la tecla J hablas con la gente. Y si te aburres, vuelve.") == "Con la tecla J hablas con la gente. Y si te aburres, vuelve."
    # si cambias la asignación, el texto la sigue
    mapa = {c: dict(m) for c, m in mando.POR_DEFECTO.items()}
    mapa["pie"]["lt"], mapa["pie"]["rb"] = "nada", "fijar"
    assert mando.textos_mando("Pulsa Q para fijarlo.", mapa, "xbox", "pie") == "Pulsa el botón RB para fijarlo."


def test_el_juego_habla_con_botones_solo_si_hay_mando_y_la_opcion_esta_puesta(robot):
    p, j = _partida(robot)
    md = robot.app.mando
    p.decir("Pulsa Q para fijarlo.")
    assert robot.app.voz.registro[-1] == "Pulsa Q para fijarlo."
    md.simulado = True
    p.decir("Pulsa Q para fijarlo.")
    assert robot.app.voz.registro[-1] == "Pulsa el gatillo izquierdo para fijarlo."
    robot.app.abrir(Dialogo(robot.app, [("Narrador", "Abre el móvil con M.")]))
    assert "Abre el móvil con el botón Vista." in robot.app.voz.registro[-1]
    robot.tecla(pygame.K_ESCAPE)
    robot.app.cfg["mando_textos"] = False
    p.decir("Pulsa Q para fijarlo.")
    assert robot.app.voz.registro[-1] == "Pulsa Q para fijarlo."
    robot.app.cfg["mando_textos"] = True
    menus_extra.opciones_mando(robot.app)
    assert any("Decir los botones del mando" in o.texto for o in robot.app.pila[-1].opciones)
    md.simulado = False


# ---------------------------------------------------------- piloto y vehículos
def test_el_piloto_se_detiene_al_llegar(robot):
    p, j = _partida(robot)
    p.cfg["piloto_gps"] = True
    p.cfg["conduccion"] = "asistida"
    l =next(q for q in p.mundo.lugares.values() if q.tipo == "tienda")
    x, y, d = p.mundo.plaza_junto_a(l)
    v = p.crear_vehiculo("sedan", x, y, d)
    p._subir(v, False)
    otro = max((q for q in p.mundo.lugares.values() if q.tipo in ("bar", "tienda", "banco")), key=lambda q: abs(q.x - l.x) + abs(q.y - l.y))
    p.gps_a_lugar(otro)
    assert p.piloto_completo()
    llegado = False
    for _ in range(6000):
        robot.frames(1)
        if p.gps is None or (v.dist(otro.x, otro.y) < 16 and abs(v.vel) < 0.1):
            llegado = True
            break
    robot.frames(60)                                             # al llegar frena del todo: no deja el coche rodando
    assert llegado and abs(v.vel) < 0.1 and v.dist(otro.x, otro.y) < 30


def test_el_vehiculo_que_dejas_te_espera_y_se_guarda_con_la_partida(robot):
    p, j = _partida(robot)
    x, y, d = p.plaza_cercana()
    v = p.crear_vehiculo("furgoneta", x, y, d)
    p._subir(v, True)
    p.salir_vehiculo()
    assert p.ultimo_veh is v and p.tu_vehiculo() is v
    j.x, j.y = p.mundo.punto_libre(v.x + 400, v.y + 300)        # te vas lejos, a hacer otra cosa
    for _ in range(5):
        p._poblar()
    assert v in p.vehiculos and not v.muerto                     # antes desaparecía a los 170 metros
    d = p.a_dict()
    assert d["veh_fuera"]["modelo"] == "furgoneta" and d["veh_fuera"]["mapa"] == p.mundo.id
    # al subir a otro, el de antes vuelve a ser un coche cualquiera
    w = p.crear_vehiculo("sedan", *p.plaza_cercana())
    p._subir(w, True)
    assert p.ultimo_veh is None and "veh_fuera" not in p.a_dict()


def test_meter_en_el_garaje_el_coche_aparcado_cerca_y_mandarlo_desde_el_movil(robot):
    p, j = _partida(robot)
    casa = p.lugares["casa_abuela"]
    if casa.id not in j.propiedades:
        j.propiedades.append(casa.id)
    p.teletransportar(casa.x, casa.y)
    x, y, d = p.mundo.plaza_junto_a(casa)
    v = p.crear_vehiculo("sedan", x, y, d)
    p._subir(v, True)
    p.salir_vehiculo()
    p.teletransportar(casa.x, casa.y)
    menus_juego.lugar(p, casa)
    m = robot.app.pila[-1]
    _op(m, "Meter en el garaje")
    robot.tecla(pygame.K_RETURN)
    assert len(j.garajes[casa.id]) == 1 and v.muerto and "guardado en el garaje" in robot.dicho()
    assert any(o.texto.startswith("Garaje: 1 de") and o.ayuda and "sin bajarte" in o.ayuda for o in m.opciones)
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    # desde el móvil: el mecánico se lleva el que llevas
    w = p.crear_vehiculo("moto", x, y, d)
    p._subir(w, True)
    dinero = j.dinero
    menus_extra.servicios(p)
    _op(robot.app.pila[-1], "Mandar tu vehículo")
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)                                 # la primera casa con garaje
    assert j.veh is None and w.muerto and j.dinero == dinero - 100 and len(j.garajes[casa.id]) == 2
    assert "Tu mecánico se lleva" in robot.dicho()


def test_cada_vehiculo_suena_a_lo_suyo_al_subir(robot):
    p, j = _partida(robot)
    oido = []
    real = p.son
    p.son = lambda nombre, **kw: (oido.append((nombre, kw.get("tono", 1.0))), real(nombre, **kw))[1]
    x, y, d = p.plaza_cercana()
    for modelo in ("sedan", "moto", "camion", "deportivo"):
        v = p.crear_vehiculo(modelo, x, y, d)
        oido.clear()
        p.son_puerta(v)
        assert len(oido) == 1
    vistos = {}
    for modelo in ("sedan", "moto", "camion", "deportivo", "bici"):
        oido.clear()
        p.son_puerta(p.crear_vehiculo(modelo, x, y, d))
        vistos[modelo] = oido[0]
    assert vistos["sedan"] == ("puerta_coche", 1.0) and vistos["moto"][0] != "puerta_coche" and vistos["bici"][0] != "puerta_coche"
    assert vistos["camion"][1] < 1.0 < vistos["deportivo"][1]
    # y la gente no tiene toda la misma voz
    from juego.entidades import Persona
    tonos = {round(Persona("civil", 0, 0).tono, 2) for _ in range(30)}
    assert len(tonos) > 10 and min(tonos) < 1.0 < max(tonos)


# -------------------------------------------------------------- actualizador
def test_una_descarga_cortada_se_retoma_por_donde_iba(tmp_path):
    import hashlib
    datos = bytes(range(256)) * 4000
    info = A.Info("9.9.9", "nuevo.zip", hashlib.sha256(datos).hexdigest(), len(datos), ["https://uno.example/nuevo.zip"], "", "servidor")
    pedidas = []

    class Corte(io.BytesIO):
        """Entrega solo un trozo y la conexión se cae."""
        status = 200

        def __init__(self, d, tope, status):
            super().__init__(d)
            self.tope, self.status = tope, status

        def read(self, n=-1):
            if self.tell() >= self.tope:
                if self.tope < len(self.getvalue()):
                    raise OSError("conexión cortada")
                return b""
            return super().read(min(n, self.tope - self.tell()))

    def abrir(url, tiempo=0, desde=0):
        pedidas.append(desde)
        resto = datos[desde:]
        return Corte(resto, len(resto) if len(pedidas) >= 3 else 300000, 206 if desde else 200)

    ruta = A.descargar(info, str(tmp_path), abrir=abrir)
    assert open(ruta, "rb").read() == datos
    assert pedidas == [0, 300000, 600000]                        # tres conexiones, cada una desde donde se quedó la anterior
    # si no hay manera, el aviso lo dice claro
    pedidas.clear()

    def siempre_cortada(url, tiempo=0, desde=0):
        pedidas.append(desde)
        return Corte(datos[desde:], 0, 206 if desde else 200)
    with pytest.raises(A.ErrorRed):
        A.descargar(info, str(tmp_path), abrir=siempre_cortada)
    assert len(pedidas) <= A.REINTENTOS + 1
