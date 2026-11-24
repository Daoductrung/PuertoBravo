"""1.7.4: lo pedido en el hilo tras la 1.7.3."""
import numpy as np
import pygame

from juego import sintesis, sistemas
from juego.menus import Menu


def test_con_un_rifle_se_ve_y_se_fija_mas_lejos(robot):
    p = robot.nueva_partida()
    j = p.j
    j.armas["rifle"] = 10
    j.arma = "pistola" if "pistola" in p.armas_d else "punos"
    corto = p.alcance_avistar()
    j.arma = "rifle"
    assert p.alcance_avistar() >= p.armas_d["rifle"]["alcance"] and p.alcance_avistar() > corto
    x, y = p.pos()
    from juego.entidades import Persona
    e = Persona("enemigo", x + 95, y, "Vigía")
    e.hostil = True
    p.personas.append(e)
    assert e in p._objetivos()                               # a 95 metros, con el rifle en la mano
    j.arma = "punos"
    assert e not in p._objetivos()
    # quien espera quieto despierta al recibir un disparo
    e.activo = False
    p.danar_persona(e, 1)
    assert e.activo


def test_el_taller_atiende_al_vehiculo_aparcado_al_lado(robot):
    p = robot.nueva_partida()
    l = next(l for l in p.mundo.lugares.values() if l.tipo == "taller")
    v = p.crear_vehiculo(next(m["id"] for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela")), l.x + 8, l.y, 0, None)
    v.salud = v.salud_max * 0.5
    p.ultimo_veh = v
    p.j.veh = None
    p.j.x, p.j.y = l.x + 2, l.y
    p.app.cfg["detalle_voz"] = "normal"
    from juego import menus_juego
    menus_juego._taller(p, l)
    m = p.app.pila[-1]
    assert isinstance(m, Menu) and "aparcado aquí al lado" in m.opciones[0].texto and "Reparar" in m.opciones[0].texto


def test_el_garaje_repara_hasta_el_maximo_con_blindaje(robot):
    p = robot.nueva_partida()
    casa = next(p.lug(i) for i in p.j.propiedades if p.lug(i) is not None and p.lug(i).tipo == "casa") if p.j.propiedades else next(l for l in p.mundo.lugares.values() if l.tipo == "casa")
    modelo = next(m for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela"))
    blindaje = next(k for k, m in sistemas.MEJORAS.items() if m["efecto"] == "blindaje")
    d = {"modelo": modelo["id"], "salud": 10.0, "nombre": modelo["nombre"], "mejoras": {blindaje: 2}}
    p.j.garajes[casa.id] = [d]
    sistemas.muebles_de(p.j, casa)                          # que exista su lista de muebles
    p.j.muebles = getattr(p.j, "muebles", {}) or {}
    orig = sistemas.muebles_de
    sistemas.muebles_de = lambda j, l: ["taller"]
    try:
        sistemas.al_dormir_en_casa(p, casa)
    finally:
        sistemas.muebles_de = orig
    from types import SimpleNamespace
    assert d["salud"] == float(modelo["salud"]) * sistemas.factor_blindaje(SimpleNamespace(mejoras={blindaje: 2})) > float(modelo["salud"])


def test_la_ambulancia_no_recoge_en_un_hospital(robot):
    p = robot.nueva_partida()
    for _ in range(60):
        assert p._destino_azar(0, 9999, sin_tipos=("hospital",)).tipo != "hospital"


def test_la_banda_dice_su_salud_y_se_cura_con_la_z(robot):
    p = robot.nueva_partida()
    a = p.crear_aliado()
    a.salud, a.salud_max = 40.0, 95.0
    a.x, a.y = p.pos()
    assert "42 por ciento" in p.salud_aliado_txt(a)
    p.j.salud = p.j.salud_max
    p.j.objetos["botiquin"] = 2
    p.usar_botiquin()
    assert a.salud == 90.0 and p.j.objetos["botiquin"] == 1 and "Curas a" in robot.dicho()
    p.j.salud = p.j.salud_max - 30                            # si el herido eres tú, primero tú
    p.usar_botiquin()
    assert p.j.salud == p.j.salud_max and a.salud == 90.0


def test_los_combates_del_gimnasio_tienen_tope_y_son_a_punos(robot):
    p = robot.nueva_partida()
    c = p.combate_def("mma")
    assert c and int(c.get("victorias_tope", 0)) == 10
    p.j.stats["mma"] = 30
    l = next(l for l in p.mundo.lugares.values() if l.tipo in ("gimnasio",)) if any(l.tipo == "gimnasio" for l in p.mundo.lugares.values()) else next(iter(p.mundo.lugares.values()))
    p.empezar_combate(l, c)
    assert p.mision["def"]["recompensa"]["dinero"] == int(c["premio"]) + int(c["premio_victoria"]) * 10
    assert p.mision["def"].get("solo_punos")
    p.j.armas["navaja"] = 1
    p.elegir_arma("navaja")
    assert p.j.arma == "punos" and "solo valen los puños" in robot.dicho()


def test_andar_o_correr_se_guarda_y_los_dias_con_nombre(robot):
    p = robot.nueva_partida()
    p.correr_fijo = True
    d = p.a_dict()
    assert d["correr_fijo"] is True
    p.correr_fijo = False
    p.cargar_dict(d)
    assert p.correr_fijo is True
    p.dia = 3
    for modo, esperado in (("ambos", "miércoles, día 3"), ("numero", "día 3"), ("nombre", "miércoles")):
        p.cfg["dia_semana"] = modo
        assert p.fecha_txt() == esperado
    p.cfg["dia_semana"] = "ambos"


def test_mayusculas_w_dice_el_estado_del_vehiculo(robot):
    p = robot.nueva_partida()
    m = next(m for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela"))
    v = p.crear_vehiculo(m["id"], *p.pos(), 0, None)
    v.salud = v.salud_max / 2
    t = p.vehiculo_estado_txt(v)
    assert v.nombre in t and "50 por ciento" in t and ("Mejoras" in t or "Sin mejoras" in t)


def test_en_segundo_plano_no_habla_pero_lo_guarda(robot):
    app = robot.app
    dichos = []

    class Salida:
        def speak(self, t, interrupt=False):
            dichos.append(t)

        def braille(self, t):
            pass
    voz = app.voz
    antes = (voz.salida, voz.muda)
    voz.salida, voz.muda = Salida(), False
    try:
        app.con_foco = False
        app.cfg["callar_sin_foco"] = True
        app.decir("Mensaje en segundo plano.")
        assert not dichos and voz.historial[-1] == "Mensaje en segundo plano."
        app.cfg["callar_sin_foco"] = False
        app.decir("Ahora sí.")
        assert dichos == ["Ahora sí."]
    finally:
        voz.salida, voz.muda = antes
        app.con_foco = True
        app.cfg["callar_sin_foco"] = True


def test_el_estereo_de_verdad_no_se_anula_al_pasar_a_mono():
    t = np.linspace(0, 1, 44100, dtype=np.float32)
    s = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    contrafase = np.stack([s, -s * 0.9], axis=1)              # dos micrófonos casi en contrafase: la media casi desaparece
    m = sintesis.a_mono(contrafase)
    assert np.sqrt(np.mean(m ** 2)) > 0.6
    normal = np.stack([s, s * 0.8], axis=1)
    assert np.allclose(sintesis.a_mono(normal), normal.mean(axis=1))


def test_los_componentes_se_instalan_solos_si_se_pide(robot, monkeypatch):
    from juego import componentes as C, menus_componentes as MC
    app = robot.app
    d = {"id": "idioma-it", "tipo": "idioma", "nombre": "Italiano", "version": 2, "file": "idioma-it_2.zip", "sha256": "a" * 64, "size": 1024,
         "url": "https://ejemplo.invalid/idioma-it_2.zip", "requiere_juego": "1.0"}
    c = C.Componente(d, "https://ejemplo.invalid/componentes/componentes.json", "servidor")
    c2 = C.Componente(dict(d, id="mod-y", tipo="mod", nombre="Mod Y", file="mod-y_1.zip", version=1), "https://ejemplo.invalid/componentes/componentes.json", "servidor")
    monkeypatch.setattr(C, "instalados", lambda: {})
    hechos = []
    monkeypatch.setattr(MC, "instalar", lambda app, cuales, publicados=None: hechos.extend(x.id for x in cuales))
    while len(app.pila) > 1:
        app.cerrar(app.pila[-1])
    app.comp_publicados = {c.id: c, c2.id: c2}
    app.cfg["comp_sin_interes"] = ["mod"]
    app.cfg["comp_instalar_solo"] = True
    app.comp_aviso = 1
    MC.paso(app)
    assert hechos == ["idioma-it"] and "Se instalan solos" in robot.dicho()      # solo lo que te interesa
    app.cfg["comp_instalar_solo"], app.cfg["comp_sin_interes"] = False, []


def test_repasar_el_historial_aunque_lleguen_mensajes(robot):
    """Con el GPS o el parte del día hablando, Re Pág se quedaba siempre en el mismo mensaje: cada mensaje nuevo te
    llevaba al final. Mientras repasas, ya no."""
    p = robot.nueva_partida()
    voz = robot.app.voz
    for k in range(6):
        p.decir(f"Mensaje {k}.")
    oidos = []
    for k in range(4):
        robot.tecla(pygame.K_PAGEUP)
        oidos.append(voz.registro[-1])
        p.decir(f"Llega otro {k}.")                         # entre pulsación y pulsación
    assert oidos == ["Mensaje 4.", "Mensaje 3.", "Mensaje 2.", "Mensaje 1."]
    robot.tecla(pygame.K_PAGEUP, pygame.KMOD_CTRL)
    robot.tecla(pygame.K_PAGEUP)
    assert voz.registro[-1] == "Primero. " + voz.historial[0]                   # en el borde, lo dice
    robot.tecla(pygame.K_PAGEDOWN, pygame.KMOD_CTRL)                           # al último: vuelves a seguir lo nuevo
    p.decir("Lo más nuevo.")
    assert voz.cursor == len(voz.historial) - 1
    robot.tecla(pygame.K_PAGEDOWN)
    assert voz.registro[-1] == "Último. Lo más nuevo."


def test_el_cocinero_avisa_si_ya_no_hay_laboratorio(robot):
    p = robot.nueva_partida()
    p.cfg["adultos"] = True
    j = p.j
    j.territorios = ["t1"]
    j.banda = 1
    if not j.propiedades:
        j.propiedades.append(next(l.id for l in p.mundo.lugares.values() if l.tipo == "casa"))
    casa = j.propiedades[0]
    j.laboratorios = []                                      # se lo llevó la policía
    f = p.banda_fichas()[0]
    f.update(tarea="cocinar:" + casa, lealtad=80)
    t = p._cocinar_cocinero(f, casa)
    assert "ya no tienes laboratorio" in t or "ya no hay laboratorio" in t
    assert f["tarea"] == ""


def test_el_piloto_temerario_usa_toda_la_velocidad_con_las_mejoras(robot):
    """En el foro: un coche mejorado llegaba a 206 km/h a mano y el piloto temerario se quedaba en 154."""
    from juego import conduccion
    p = robot.nueva_partida()
    m = next(m for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela"))
    v = p.crear_vehiculo(m["id"], *p.pos(), 0, None)
    motor = next(k for k, x in sistemas.MEJORAS.items() if x["efecto"] == "motor")
    sistemas.poner(v, {motor: sistemas.niveles(motor)})
    p.j.veh = v
    p.cfg["piloto_estilo"] = "temerario"
    p.gps = {"dest": (v.x + 5000, v.y), "ruta": [], "sigue": None, "nombre": "lejos", "clave": None, "auto": True}
    p._piloto_curva = lambda v, freno: 999.0                 # en recta
    v.vel = 0.0
    for _ in range(4000):
        p._pilotar(v, 0.05, 10.0)
    assert v.vel > m["vel_max"] * 1.05                       # pasa de la velocidad de fábrica: cuentan las mejoras
    assert abs(v.vel - m["vel_max"] * sistemas.factor_velocidad(v) * (1 + 0.01 * p.nivel("conduccion"))) < 0.5


def test_el_coche_arrimado_a_la_acera_no_para_el_trafico(robot):
    """En el foro: sin conexión, el coche que dejas pegado a la acera paraba a los demás como si estuviera en medio."""
    from juego import mundo as M
    p = robot.nueva_partida()
    m = next(m for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela"))
    x, y = p.pos()
    trafico = p.crear_vehiculo(m["id"], x, y, 1, "trafico")      # mirando al este
    trafico.dir = 1
    dejado = p.crear_vehiculo(m["id"], x + 8, y + 2.2, 1, None)   # dos metros y pico a un lado, como con la D
    dejado.ia, dejado.vel = None, 0.0
    p.j.veh = None
    p.j.x, p.j.y = x - 200, y - 200
    assert not p._obstaculo(trafico)
    dejado.y = y + 0.3                                            # en medio del carril, sí estorba
    assert p._obstaculo(trafico)


def test_un_asunto_sin_contestar_lo_arregla_el_abogado_si_lo_tienes(robot):
    """En el foro: con abogado, una inspección que se dejaba pasar se cobraba entera, sin decir cuál era."""
    p = robot.nueva_partida()
    h = p.hon()
    neg = next(l for l in p.mundo.lugares.values() if l.tipo == "negocio")
    p.j.propiedades.append(neg.id)
    h["abogado"] = p.dia + 7
    p.j.banco, p.j.dinero = 100000, 0
    h["asuntos"].append({"tipo": "inspeccion", "lugar": neg.id, "dia": p.dia - 5, "plazo": p.dia - 1, "euros": 800})
    p._hon_dia_asuntos()
    assert not h["asuntos"] and p.j.banco == 100000 - 400
    assert neg.nombre in robot.dicho() and "abogado" in robot.dicho()
    h["abogado"] = 0                                              # sin abogado, la sanción entera
    h["asuntos"].append({"tipo": "inspeccion", "lugar": neg.id, "dia": p.dia - 5, "plazo": p.dia - 1, "euros": 800})
    p._hon_dia_asuntos()
    assert p.j.banco == 100000 - 400 - 800
