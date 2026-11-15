"""Menús del juego: principal, pausa, opciones, móvil, lugares, tiendas, casino y guardado."""
import json
import math
import os
import random
import time

import zlib

from . import NOMBRE, VERSION, ayuda, cifrado, packs, rutas
from . import mundo as M
from .config import OPCIONES
from .menus import Dialogo, Menu, Opcion

RANURAS = ["auto", "rapido", "1", "2", "3", "4", "5"]
NOMBRE_RANURA = {"auto": "Guardado automático", "rapido": "Guardado rápido"}


# ====================================================================== guardado
CARPETA = "partidas"


def _archivo(ranura, ext=None):
    """Archivo de una ranura. En el juego compilado las partidas van protegidas y con extensión propia."""
    ext = ext or (rutas.EXT_PARTIDA if cifrado.COMPILADO else ".json")
    return os.path.join(rutas.carpeta_data(CARPETA), f"partida_{ranura}{ext}")


def _archivos_validos(ranura):
    """Los archivos de una ranura que el juego acepta. En el juego compilado solo valen las partidas protegidas:
    una partida legible, escrita o retocada a mano, no se carga."""
    posibles = [r for r in (_archivo(ranura, rutas.EXT_PARTIDA), _archivo(ranura, ".json")) if os.path.exists(r)]
    if cifrado.COMPILADO:
        posibles = [r for r in posibles if cifrado.esta_cifrado(r)]
    return posibles


def leer_ranura(ranura):
    """Lee la ranura. En el código fuente, si hay una partida con cada extensión, vale la más reciente."""
    for ruta in sorted(_archivos_validos(ranura), key=os.path.getmtime, reverse=True):
        try:
            return cifrado.leer_json(ruta)
        except (OSError, ValueError, zlib.error):
            continue
    return None


def escribir_ranura(p, ranura):
    d = p.a_dict()
    d["fecha"] = time.strftime("%d/%m/%Y %H:%M")
    d["resumen"] = f"{len(p.completadas)} misiones, {p.j.dinero} euros, día {p.dia}"
    try:
        cifrado.escribir_json(_archivo(ranura), d)          # en el juego compilado la partida queda protegida
        return True
    except OSError:
        return False


def texto_ranura(ranura):
    d = leer_ranura(ranura)
    nombre = NOMBRE_RANURA.get(ranura, f"Ranura {ranura}")
    if not d:
        return f"{nombre}: vacía"
    return f"{nombre}: {d.get('resumen', '')}. {d.get('lugar', '')}. Guardada el {d.get('fecha', '')}"


def mas_reciente():
    mejor = None
    for r in RANURAS:
        tiempos = [os.path.getmtime(a) for a in _archivos_validos(r)]
        if not tiempos or leer_ranura(r) is None:      # una partida estropeada o manipulada no cuenta
            continue
        t = max(tiempos)
        if mejor is None or t > mejor[0]:
            mejor = (t, r)
    return mejor[1] if mejor else None


def autoguardar(p):
    if escribir_ranura(p, "auto"):
        p.decir("Partida guardada automáticamente.")


def guardado_rapido(p):
    if p.mision:
        p.app.son("error")
        p.decir("No se puede guardar durante una misión.", True)
    elif p.j.estrellas:
        p.app.son("error")
        p.decir("No se puede guardar mientras te busca la policía.", True)
    elif escribir_ranura(p, "rapido"):
        p.app.son("guardado")
        p.decir("Guardado rápido hecho.", True)


def menu_guardar(p):
    app = p.app
    if p.mision:
        app.son("error")
        p.decir("No se puede guardar durante una misión.", True)
        return

    def hacer(r):
        def f():
            if escribir_ranura(p, r):
                app.son("guardado")
                app.cerrar(m)
                app.decir(f"Partida guardada en la ranura {r}.", True)
            else:
                app.son("error")
                app.decir("No se pudo guardar la partida.", True)
        return f
    m = Menu(app, "Guardar partida. Elige una ranura", lambda: [Opcion(texto_ranura(r), hacer(r)) for r in RANURAS[2:]])
    app.abrir(m)


def menu_cargar(app):
    def hacer(r):
        def f():
            d = leer_ranura(r)
            if not d:
                app.son("error")
                app.decir("Esa ranura está vacía.", True)
                return
            app.empezar_partida(d)
        return f
    app.abrir(Menu(app, "Cargar partida", lambda: [Opcion(texto_ranura(r), hacer(r)) for r in RANURAS]))


# Lo que pasa de una partida a la siguiente al empezar de nuevo conservando lo ganado.
CONSERVA = ("dinero", "banco", "armas", "arma", "objetos", "hab", "logros", "propiedades", "garajes", "barcos", "salud_max", "ropa", "casetes", "stats",
            "bolsa", "negocios", "personaje", "nombre", "apellido", "genero", "perro", "conocidos")


def partida_mas(app):
    """Nueva partida conservando lo ganado en una partida guardada."""
    from .partida import PartidaMasNueva, migrar

    def empezar(r):
        def f():
            try:
                d = migrar(leer_ranura(r))
            except (PartidaMasNueva, TypeError):
                app.son("error")
                app.decir("Esa partida no se puede leer con esta versión del juego.", True)
                return
            viejo = d.get("jugador", {})
            app.empezar_partida(None, personaje=viejo.get("personaje"))
            p = app.partida
            for k in CONSERVA:
                if k in viejo and hasattr(p.j, k):
                    setattr(p.j, k, viejo[k])
            p.j.ciclo = int(viejo.get("ciclo", 0)) + 1
            __import__("juego.genero", fromlist=["x"]).poner(p.j.genero)
            if p.j.personaje == "propio":
                from . import registro
                registro.ocultar(p.j.nombre)
                registro.ocultar(p.j.apellido)
            p.j.salud = p.j.salud_max
            if p.j.arma not in p.j.armas:
                p.j.arma = "punos"
            app.decir(f"Empiezas de nuevo con lo que tenías: {p.j.dinero} euros, {len(p.j.armas)} armas y {len(p.j.propiedades)} propiedades. "
                      f"Es tu vuelta número {p.j.ciclo + 1}: los enemigos de las misiones aguantan algo más.")
        return f
    ops = [Opcion(texto_ranura(r), empezar(r)) for r in RANURAS if leer_ranura(r) is not None]
    app.abrir(Menu(app, "Nueva partida conservando lo ganado. Elige de qué partida guardada", ops or [Opcion("No hay ninguna partida guardada")]))


# ====================================================================== principal
def principal(app):
    def ops():
        lista = []
        r = mas_reciente()
        if r:
            lista.append(Opcion("Continuar", lambda: app.empezar_partida(leer_ranura(r)), ayuda="Carga la partida guardada más reciente."))
        lista += [
            Opcion("Nueva partida", lambda: __import__("juego.menus_vida", fromlist=["x"]).elegir_personaje(app)),
            Opcion("Cargar partida", lambda: menu_cargar(app)),
            Opcion("Nueva partida conservando lo ganado", lambda: partida_mas(app),
                   ayuda="Empiezas la historia desde el principio, pero con el dinero, las armas, las habilidades, las casas, los vehículos y los barcos de una partida guardada. "
                         "Los enemigos de las misiones aguantan algo más cada vez. La partida guardada no se toca."),
            Opcion("Jugar con amigos", lambda: app.decir("Para jugar con amigos, empieza o carga tu partida, abre el móvil con la tecla M y entra en Jugar con amigos. "
                                                        "Desde ahí puedes abrir tu partida, con o sin contraseña, y darles tu dirección, o unirte a la de un amigo.", True),
                   ayuda="El propio juego monta el servidor en tu ordenador. No hace falta ningún programa más."),
            Opcion("Aprender los sonidos del juego", lambda: sonidos(app)),
            Opcion("Opciones", lambda: opciones(app)),
            Opcion("Ayuda: lista de teclas", lambda: ayuda_teclas(app, "todo")),
            Opcion("Abrir el manual", lambda: abrir_manual(app)),
            Opcion("Acerca de", lambda: acerca(app), ayuda="La versión que tienes, quién ha hecho el juego, dónde avisar de un fallo y cómo invitarle a un café."),
            Opcion("Salir", app.salir),
        ]
        return lista
    app.abrir(Menu(app, f"{NOMBRE}. Menú principal", ops, escapable=False,
                   intro="Usa las flechas arriba y abajo para moverte y pulsa Intro para elegir"))


def acerca(app):
    """Versión, autor, licencia, enlaces y la invitación a un café."""
    from . import ANIO, AUTOR, CAFE, FALLOS, MASTODON, VERSION, WEB

    def abrir(url, que):
        def hacer():
            try:
                os.startfile(url)
                app.decir(f"Abriendo {que} en tu navegador.", True)
            except (OSError, AttributeError):
                app.son("error")
                app.decir(f"No se pudo abrir el navegador. La dirección es {url}", True)
        return hacer
    m = Menu(app, f"Acerca de {NOMBRE}", [
        Opcion(f"{NOMBRE}, versión {VERSION}"),
        Opcion(f"Hecho por {AUTOR}"),
        Opcion(f"Copyright {ANIO}, {AUTOR}. Software libre con licencia MIT: puedes usarlo, modificarlo y repartirlo",
               ayuda="El texto completo de la licencia está en la página del proyecto."),
        Opcion("Un audiojuego de mundo abierto, en español, pensado desde el principio para jugarse sin ver la pantalla"),
        Opcion("Invítame a un café si te gusta mi trabajo", abrir(CAFE, "la página de donaciones de PayPal"),
               ayuda="El juego es gratis y lo seguirá siendo. Si te ha hecho pasar un buen rato y quieres agradecerlo, Intro abre la página de donaciones en el navegador."),
        Opcion("Página del proyecto en GitHub", abrir(WEB, "la página del proyecto"), ayuda="La descripción completa, el código fuente y todas las versiones."),
        Opcion("Avisar de un fallo o proponer una mejora", abrir(FALLOS, "la página de incidencias"),
               ayuda="En Opciones, Registro para informar de fallos, se explica qué carpeta adjuntar."),
        Opcion("Mastodon del autor", abrir(MASTODON, "el perfil de Mastodon")),
        Opcion("Novedades de esta versión", abrir(rutas.data("docs", "novedades.html"), "las novedades")),
        Opcion("Agradecimientos: a quienes prueban el juego y avisan de los fallos. Los sonidos son mejorables y toda ayuda con ellos es bienvenida",
               ayuda="La guía cambiar sonidos, en la carpeta data, docs, explica cómo sustituir cualquier sonido o montar un pack completo."),
        Opcion("Componentes: las voces de las escenas de Bahía del Ocaso están generadas por ordenador con VibeVoice, de Microsoft. "
               "El modelo local de inteligencia artificial, si lo instalas, funciona con llama punto c p p"),
        Opcion("Volver", lambda: app.cerrar(m)),
    ])
    app.abrir(m)


def abrir_manual(app):
    ruta = rutas.data("docs", "manual.html")
    try:
        os.startfile(ruta)
        app.decir("Abriendo el manual en tu navegador.", True)
    except (OSError, AttributeError):
        app.son("error")
        app.decir("No se encontró el manual. Está en la carpeta data, docs.", True)


def sonidos(app):
    def tocar(s):
        return lambda: app.mez.sonar(s, cat="interfaz", vol=0.9)
    ops = [Opcion(f"{nom}. {exp}", tocar(s), callado=True) for s, nom, exp in ayuda.SONIDOS if s in app.mez.sonidos]      # solo suena el sonido que se está aprendiendo
    app.abrir(Menu(app, "Aprender los sonidos", ops, intro="Pulsa Intro sobre cada elemento para escuchar su sonido"))


def opciones_teclado(app):
    """Cambiar con qué tecla se hace cada función del juego."""
    from . import teclado
    cfg = app.cfg

    def cambiar(funcion, que):
        def abrir():
            def elegida(k):
                desplazada = teclado.cambiar(cfg, funcion, k)
                cfg.guardar()
                app.son("guardado")
                extra = f" Lo que hacía {teclado.nombre(k)} pasa a {teclado.nombre(teclado.tecla_de(cfg, desplazada))}." if desplazada is not None else ""
                app.decir(f"Hecho: {que.split(':')[0].split('.')[0]}, con {teclado.nombre(k)}.{extra}", True)
            app.abrir(teclado.Captura(app, f"Tecla nueva para: {que.split('.')[0]}", elegida))
        return abrir

    def restablecer():
        teclado.restablecer(cfg)
        cfg.guardar()
        app.decir("Teclas originales restablecidas.", True)

    def ops():
        def en_menus(_d=1):
            cfg["teclas_menus"] = not cfg["teclas_menus"]
            cfg.guardar()
        lista = [Opcion(lambda: f"Teclas cambiadas: {len(teclado.cambios(cfg))}"),
                 Opcion(lambda: f"Usar también las teclas cambiadas en los menús y los diálogos: {'sí' if cfg['teclas_menus'] else 'no'}", ajuste=en_menus,
                        ayuda="Con sí, si has puesto el movimiento en otras teclas, los menús también se recorren con ellas. Sirve, por ejemplo, si tu lector de pantalla se queda con las flechas. "
                              "Al escribir un texto las teclas son siempre las normales. Si te lías, Restablecer las teclas originales lo deja todo como estaba.")]
        for k, ctx, que in teclado.funciones():
            actual = teclado.tecla_de(cfg, k)
            marca = f", ahora con {teclado.nombre(actual)}" if actual != k else ""
            lista.append(Opcion(f"{ctx}. {teclado.nombre(k).capitalize()}{marca}: {que}", cambiar(k, que),
                                ayuda="Intro, y después pulsa la tecla que quieres usar. Las dos teclas se intercambian, así que ninguna función se queda sin tecla."))
        lista.append(Opcion("Restablecer las teclas originales", restablecer))
        return lista
    app.abrir(Menu(app, "Teclado: cambiar las teclas", ops, al_cerrar=cfg.guardar,
                   intro="Elige una función y pulsa Intro. No se pueden cambiar Escape, Intro, F1, F12, la Mayúsculas derecha ni las teclas de control y alt"))


def ayuda_teclas(app, contexto):
    grupos = {"pie": ["pie", "general"], "coche": ["coche", "general"], "todo": ["general", "pie", "coche"]}[contexto]
    titulos = {"general": "En cualquier momento", "pie": "A pie", "coche": "Al volante"}
    from . import teclado
    ops = [Opcion(f"Tecla cambiada. {c}.") for c in teclado.cambios(app.cfg)]
    for g in grupos:
        for tecla, que in ayuda.TECLAS[g]:
            k = teclado._codigo(tecla)
            if k is not None and teclado.tecla_de(app.cfg, k) != k:
                tecla = teclado.nombre(teclado.tecla_de(app.cfg, k)).capitalize()        # la ayuda dice la tecla que has puesto tú
            ops.append(Opcion(f"{titulos[g]}. {tecla}: {que}."))
    md = app.mando
    if md.conectado or contexto == "todo":
        lineas = [Opcion(t) for t in md.lineas_ayuda({"pie": ("pie", "menu"), "coche": ("coche", "menu"), "todo": ("pie", "coche", "menu")}[contexto])]
        ops = lineas + ops if md.conectado else ops + lineas
    app.abrir(Menu(app, "Ayuda de teclas y botones", ops, intro="Recorre la lista con las flechas. Escape para volver"))


def volumen_sonidos(app):
    """Todos los sonidos, por grupos: Intro escucha y las flechas ajustan ese sonido."""
    from . import catalogo_sonidos as cat
    cfg = app.cfg

    def grupo(k, nombres):
        def abrir():
            def op(s):
                def aj(d):
                    packs.ajustar(app.mez, cfg, s, d)
                    app.mez.sonar(s, cat="interfaz", vol=0.9)
                return Opcion(lambda: f"{cat.describir(s)} {int(round(float(cfg['vol_sonidos'].get(s, 1.0)) * 100))} por ciento", (lambda: app.mez.sonar(s, cat="interfaz", vol=0.9)), ajuste=aj,
                              ayuda=f"Archivo {s}. Intro lo hace sonar. Izquierda y derecha lo bajan o lo suben, del 30 al 200 por ciento.")
            m = Menu(app, cat.GRUPOS[k][0] if k < len(cat.GRUPOS) else "Otros sonidos", [op(s) for s in nombres] + [Opcion("Volver", lambda: app.cerrar(m))],
                     al_cerrar=cfg.guardar, intro="Intro para escuchar. Izquierda y derecha para ajustar")
            app.abrir(m)
        return abrir
    grupos = {}
    for s in sorted(app.mez.sonidos):
        if s.startswith(("radio_", "musica_")):
            continue
        grupos.setdefault(cat.grupo_de(s), []).append(s)

    def restablecer():
        cfg["vol_sonidos"].clear()
        cfg.guardar()
        app.recargar_sonidos()
        app.decir("Todos los sonidos vuelven a su volumen normal.", True)
    ops = [Opcion(f"{cat.GRUPOS[k][0] if k < len(cat.GRUPOS) else 'Otros sonidos'}: {len(v)} sonidos", grupo(k, v)) for k, v in sorted(grupos.items())]
    ops.append(Opcion(lambda: f"Restablecer todos. Tienes {len(cfg['vol_sonidos'])} sonidos ajustados", restablecer))
    principal_ = Menu(app, "Ajustar el volumen de cada sonido", ops + [Opcion("Volver", lambda: app.cerrar(principal_))], al_cerrar=cfg.guardar,
                      intro="Los sonidos están por grupos. Pulsa Intro para entrar en uno")
    app.abrir(principal_)


# ======================================================================= opciones
def opciones(app):
    """Opciones organizadas por secciones. Cada sección termina con «Volver»."""
    cfg = app.cfg
    nombres = {"brujula": "brújula, cada flecha va a un punto cardinal", "giro": "con giros, izquierda y derecha giran",
               "asistida": "asistida, el coche sigue el carril solo", "libre": "libre, tú llevas el volante",
               "completa": "completa, apunta sola al enemigo más cercano", "manual": "manual, hay que encararse al enemigo",
               "facil": "fácil", "normal": "normal", "dificil": "difícil",
               "cardinal": "puntos cardinales", "reloj": "horas del reloj", "relativa": "delante, derecha, detrás, izquierda",
               "todos": "todo el mundo", "mujeres": "las mujeres", "hombres": "los hombres", "x": "prefiero no decirlo", "h": "hombre", "m": "mujer"}
    OPCIONES.setdefault("detalle_voz", ["poco", "normal", "mucho"])
    nombres.update({"poco": "poco, sin recordar las teclas", "mucho": "mucho, con la explicación de cada opción"})

    def numero(clave, nombre, minimo, maximo, paso, ayuda_=None):
        def aj(d):
            cfg[clave] = max(minimo, min(maximo, cfg[clave] + paso * d))
            app.aplicar_volumenes()
            if cfg["voz_sapi"]:
                app.decir(f"{nombre}: {cfg[clave]}", True)
        return Opcion(lambda: f"{nombre}: {cfg[clave]}", ajuste=aj, ayuda=ayuda_)
    canal = {"vol_efectos": "efectos", "vol_ambiente": "ambiente", "vol_musica": "musica", "vol_interfaz": "interfaz", "vol_ambiente_musical": "musica"}

    def vol(clave, nombre, ayuda_="Cámbialo con las flechas izquierda y derecha."):
        def aj(d):
            cfg[clave] = round(max(0.0, min(1.0, cfg[clave] + 0.1 * d)), 1)
            app.aplicar_volumenes()
            app.mez.sonar("baliza" if clave not in ("vol_musica", "vol_ambiente_musical") else "menu_ok", cat=canal.get(clave, "interfaz"))
        return Opcion(lambda: f"{nombre}: {int(cfg[clave] * 100)} por ciento", ajuste=aj, ayuda=ayuda_)

    def lista(clave, nombre, ayuda_=None):
        def aj(d):
            ops = OPCIONES[clave]
            cfg[clave] = ops[(ops.index(cfg[clave]) + d) % len(ops)]
        return Opcion(lambda: f"{nombre}: {nombres[cfg[clave]]}", ajuste=aj, ayuda=ayuda_)

    def si_no(clave, nombre, ayuda_=None, al_cambiar=None):
        def aj(d):
            cfg[clave] = not cfg[clave]
            if al_cambiar:
                al_cambiar()
        return Opcion(lambda: f"{nombre}: {'sí' if cfg[clave] else 'no'}", ajuste=aj, ayuda=ayuda_)

    def seccion(titulo, ops, ayuda_=None):
        def abrir():
            m = Menu(app, titulo, ops + [Opcion("Volver", lambda: app.cerrar(m), ayuda="Vuelve al menú de opciones. También sirve Escape.")],
                     al_cerrar=cfg.guardar, intro="Cambia cada opción con las flechas izquierda y derecha. F1 explica la opción")
            app.abrir(m)
        return Opcion(titulo, abrir, ayuda=ayuda_)

    def nombre_pack():
        actual = cfg["pack_sonidos"]
        if not actual:
            return "por defecto"
        for pk in packs.listar():
            if pk["id"] == actual:
                return f"{pk['nombre']}, {pk['n']} sonidos"
        return f"{actual}, no instalado"

    def cambiar_pack(d):
        ids = [""] + [pk["id"] for pk in packs.listar()]
        actual = cfg["pack_sonidos"] if cfg["pack_sonidos"] in ids else ""
        cfg["pack_sonidos"] = ids[(ids.index(actual) + d) % len(ids)]
        app.recargar_sonidos()
        cfg.guardar()
        if len(ids) == 1:
            app.decir("No hay ningún pack instalado. Copia la carpeta de un pack dentro de data, sonidos.", True)
            return
        app.mez.sonar("puerta_coche", cat="interfaz", vol=0.8)          # una muestra, para oír el cambio

    def adultos(d):
        from . import menus_adultos
        menus_adultos.alternar_modo(app)

    def mando():
        from . import menus_extra
        menus_extra.opciones_mando(app)

    secciones = [
        seccion("Sonido y música", [
            vol("vol_maestro", "Volumen general"), vol("vol_efectos", "Volumen de efectos"), vol("vol_ambiente", "Volumen del ambiente"),
            vol("vol_interfaz", "Volumen de avisos y balizas"),
            vol("vol_senales", "Volumen de las señales de ayuda", "Baliza del GPS, radar, tono de puntería, sensor de proximidad, semáforos y el sonido propio de cada lugar. "
                "Se aplica además del volumen de su grupo: bájalo si las señales te tapan lo demás, o baja lo demás y deja este al máximo. Cámbialo con las flechas izquierda y derecha."),
            vol("vol_musica", "Volumen de la radio y la música"),
            si_no("musica_ambiente", "Música de ambiente", "Música de fondo que cambia con la situación. Se calla sola cuando pones la radio en un vehículo y vuelve cuando la apagas o te bajas."),
            vol("vol_ambiente_musical", "Volumen de la música de ambiente", "Respecto a la radio. Cámbialo con las flechas izquierda y derecha."),
            Opcion(lambda: f"Pack de sonidos: {nombre_pack()}", ajuste=cambiar_pack,
                   ayuda="Elige con las flechas izquierda y derecha entre los sonidos por defecto y los packs, que son las subcarpetas de data, sonidos. Se aplica al momento. Los sonidos que el pack no trae siguen sonando con el original."),
            Opcion(lambda: f"Motor de sonido: {'envolvente, binaural' if cfg['motor_sonido'] == 'envolvente' else 'clásico'}" +
                   (". Se aplicará al volver a abrir el juego" if (cfg["motor_sonido"] == "envolvente") != bool(getattr(app.mez, "envolvente", False)) else ""),
                   ajuste=lambda d: cfg.__setitem__("motor_sonido", "clasico" if cfg["motor_sonido"] == "envolvente" else "envolvente"),
                   ayuda="El motor envolvente usa sonido binaural: con auriculares se distingue si algo suena delante o detrás, y no solo a izquierda o derecha. "
                         "Además mezcla el sonido fuera del programa, así que no da tirones cuando hay muchos sonidos a la vez. El clásico es el de siempre. "
                         "El cambio se aplica al cerrar y volver a abrir el juego. En ordenadores con procesador antiguo, y con el sonido mono activado, se usa siempre el clásico."),
            si_no("eco_lugares", "Eco según el lugar, solo con el motor envolvente",
                  "Con el motor envolvente, los sonidos del mundo llevan el eco del sitio donde estás: poco en el campo y en la playa, algo en la calle, más entre naves, largo en la montaña y corto y cercano dentro de un local. "
                  "Además, lo que vuela suena por encima, y si vuelas tú, la ciudad suena por debajo. Con el motor clásico esta opción no hace nada.",
                  al_cambiar=app.aplicar_volumenes),
            si_no("sonido_mono", "Sonido mono, lo mismo por los dos oídos",
                  "Para quien oye por un solo oído o usa un solo auricular. Se pierde la sensación de izquierda y derecha: oriéntate con el radar, el escáner y el GPS hablado.",
                  al_cambiar=app.aplicar_volumenes),
            si_no("atenuar_al_hablar", "Bajar el ambiente y la música mientras habla la voz",
                  "Cada vez que el juego dice algo, el sonido de fondo y la música bajan un momento para que se entienda mejor. Los efectos importantes, como motores, pasos y disparos, no bajan.",
                  al_cambiar=app.aplicar_volumenes),
            si_no("igualar_volumen", "Igualar el volumen de los sonidos cambiados", "Lleva cada sonido de un pack, o que hayas sustituido a mano, al mismo nivel que tenía el original, para que ninguno quede demasiado fuerte ni demasiado flojo.", al_cambiar=app.recargar_sonidos),
            Opcion("Ajustar el volumen de cada sonido", lambda: volumen_sonidos(app), ayuda="Lista de todos los sonidos del juego. Intro los hace sonar y las flechas izquierda y derecha suben o bajan ese sonido en concreto."),
        ], "Volúmenes, música de ambiente y packs de sonidos."),
        seccion("Movimiento y conducción", [
            lista("movimiento", "Movimiento a pie", "En modo brújula el oído mira siempre al norte. Con giros, el sonido gira contigo."),
            lista("conduccion", "Conducción", "También se cambia durante el juego con F2."),
            si_no("correr_alternar", "Correr con una pulsación, sin mantener la tecla",
                  "Con sí, una pulsación de Mayúsculas te pone a correr y otra te devuelve al paso, sin tener que mantenerla. Con no, corres mientras la mantienes pulsada."),
            si_no("frenada_auto", "Frenada automática ante el tráfico", "En conducción asistida, el coche frena solo para no chocar con el vehículo de delante. Mantén A para adelantarlo."),
            si_no("viajes_trayecto", "Viajes en taxi y en autobús con trayecto",
                  "Con sí, al coger un taxi o un autobús se oye el viaje durante un rato: el motor, la calzada y la radio. Dura entre doce segundos y un minuto según la distancia, y con Intro llegas ya. Con no, llegas al momento."),
            si_no("piloto_gps", "Piloto del GPS, el coche va solo hasta el destino",
                  "Con un destino marcado en el GPS y en conducción asistida, el coche conduce solo: acelera, frena, gira, espera en los semáforos y se detiene al llegar. "
                  "Con cualquier flecha o el espacio mandas tú. Se activa también con la tecla Y al volante."),
            si_no("sonar", "Sensor de proximidad al volante", "Al volante, pita cuando tienes un obstáculo cerca: más agudo cuanto más cerca, y por el lado en que está. Al activarlo se oye una muestra.",
                  al_cambiar=lambda: cfg["sonar"] and app.mez.sonar("sonar", cat="interfaz", vol=0.6)),
        ], "Cómo caminas y cómo conduces."),
        seccion("Orientación y avisos", [
            lista("direcciones", "Formato de las direcciones", "Cómo se dicen las direcciones del radar y del GPS."),
            si_no("gps_voz", "Indicaciones habladas del GPS"),
            si_no("baliza", "Baliza sonora del GPS", "Un toque que suena desde la dirección que tienes que seguir. Al activarla se oye una muestra.",
                  al_cambiar=lambda: cfg["baliza"] and app.mez.sonar("baliza", cat="interfaz", vol=0.8)),
            si_no("anunciar_cruces", "Anunciar los cruces"),
            si_no("anunciar_lugares", "Anunciar los lugares al llegar a su puerta"),
            si_no("anunciar_barrios", "Anunciar los cambios de barrio"),
            si_no("describir_zonas", "Describir cada barrio la primera vez que entras",
                  "La primera vez que pisas un barrio, además de su nombre, el juego dice cómo es. Las demás veces solo dice el nombre. La tecla N lo repite cuando quieras."),
            si_no("anunciar_superficie", "Anunciar los cambios de suelo", "Dice acera, calzada, césped o arena cada vez que cambia el suelo que pisas."),
            si_no("localizador", "Sonido propio de cada lugar cercano", "Cada tipo de lugar suena de una manera cuando pasas cerca. Al activarlo se oye una muestra, la de un bar. En el menú principal, Aprender los sonidos los tiene todos.",
                  al_cambiar=lambda: cfg["localizador"] and app.mez.sonar("lugar_bar", cat="interfaz", vol=0.8)),
            si_no("semaforos", "Semáforos acústicos en los cruces", "En los cruces con semáforo se oye si puedes cruzar. Al activarlo se oye una muestra.",
                  al_cambiar=lambda: cfg["semaforos"] and app.mez.sonar("semaforo_pio", cat="interfaz", vol=0.8)),
        ], "GPS, baliza, anuncios y sonidos de orientación."),
        seccion("Combate y dificultad", [
            lista("dificultad", "Dificultad", "Cambia el daño que recibes."),
            lista("punteria", "Ayuda de puntería"),
            si_no("aviso_acierto", "Aviso al dar en el blanco", "Cada vez que aciertas a un enemigo o a un vehículo suena un toque agudo y el mando da un golpe corto. Al fijar un objetivo con la Q, el mando también avisa.",
                  al_cambiar=lambda: cfg["aviso_acierto"] and app.mez.sonar("tono_objetivo", cat="interfaz", vol=0.45, tono=2.0)),
            si_no("mod_enemigos", "Modificador: enemigos más duros", "Los enemigos de las misiones aguantan la mitad más. Cada modificador activo te hace ganar experiencia un veinticinco por ciento más deprisa."),
            si_no("mod_policia", "Modificador: policía más severa", "Cada delito cuenta la mitad más, así que la búsqueda sube antes. Cada modificador activo te hace ganar experiencia un veinticinco por ciento más deprisa."),
            si_no("mod_dinero", "Modificador: misiones peor pagadas", "Las misiones pagan la mitad. Cada modificador activo te hace ganar experiencia un veinticinco por ciento más deprisa."),
            si_no("multas", "Multa o soborno cuando te cogen por poco",
                  "Con uno o dos niveles de búsqueda y dinero suficiente, cuando un agente te coge puedes pagar la multa en el acto, intentar sobornarle o dejarte detener. Con no, te detienen siempre, como antes."),
            si_no("sucesos", "Sucesos callejeros al azar", "Atracos, pandilleros y maletines perdidos que aparecen de vez en cuando por la calle."),
            si_no("invulnerable", "Asistencia: no recibir daño", "Para explorar sin preocuparte de nada."),
            si_no("sin_policia", "Asistencia: sin policía", "Los delitos no cuentan y nadie te persigue."),
            si_no("vida_realista", "Vida realista: hambre y sueño", "Hay que comer y dormir. Con hambre o con sueño vas más despacio y apuntas peor, y si los ignoras pierdes salud. La tecla V te dice cómo estás."),
        ], "Dificultad, puntería y asistencias."),
        Opcion("Personas e inteligencia artificial", lambda: __import__("juego.menus_charla", fromlist=["x"]).opciones_ia(app),
               ayuda="Cómo contestan las personas de la calle cuando les escribes lo que quieres: con el motor del juego o con una inteligencia artificial."),
        Opcion("Teclado: cambiar las teclas", lambda: opciones_teclado(app),
               ayuda="Elige con qué tecla se hace cada cosa mientras juegas. Sirve si tu teclado es distinto, si juegas con una mano o si alguna tecla choca con tu lector de pantalla."),
        Opcion("Mando", mando, ayuda="Mandos de Xbox y PlayStation: ver qué hace cada botón, reasignarlos y activar la vibración."),
        seccion("Voz", [
            si_no("voz_sapi", "Usar la voz de Windows en lugar del lector de pantalla", al_cambiar=lambda: app.voz.cambiar(cfg["voz_sapi"])),
            numero("voz_velocidad", "Velocidad de la voz de Windows", -10, 10, 1, "De menos diez a diez. Solo afecta a la voz de Windows; si usas un lector de pantalla, la velocidad se cambia en el lector."),
            numero("voz_tono", "Tono de la voz de Windows", -10, 10, 1, "De menos diez, más grave, a diez, más agudo. Solo afecta a la voz de Windows."),
            numero("voz_volumen", "Volumen de la voz de Windows", 0, 100, 10, "De cero a cien. Solo afecta a la voz de Windows."),
            lista("detalle_voz", "Cuánto explica el juego al hablar",
                  "Con poco, se quitan las frases que solo recuerdan qué tecla pulsar. Con mucho, en los menús se lee además la explicación de cada opción, sin tener que pulsar F1. Normal es lo de siempre."),
            si_no("menu_posicion", "Decir la posición en los menús, por ejemplo 3 de 9",
                  "Al moverte por un menú, después de cada opción dice cuál es y cuántas hay."),
            si_no("voces_grabadas", "Voces grabadas en las escenas, solo con el personaje Dani en masculino",
                  ayuda_="Con sí, las escenas de las misiones que tengan grabaciones suenan con voces de actores, en lugar de leerlas tu lector de pantalla, y el texto sigue saliendo en braille. "
                         "Solo cuando juegas con Dani y has elegido que te hablen en masculino, porque las grabaciones le llaman por su nombre, le hablan así y su voz es la de un hombre. Con no, con otro personaje o en femenino, todo lo dice tu lector de pantalla o, si no usas lector, la voz de Windows."),
        ], "Con qué voz habla el juego."),
        Opcion("Registro para informar de fallos", lambda: __import__("juego.menus_registro", fromlist=["x"]).opciones(app),
               ayuda="El juego anota lo que pasa en cada sesión para poder encontrar los fallos. Aquí ves dónde está, qué contiene y cómo enviarlo."),
        Opcion("Actualizaciones", lambda: __import__("juego.menus_actualizar", fromlist=["x"]).opciones(app),
               ayuda="Buscar una versión nueva del juego e instalarla, y elegir de dónde se actualiza: el servidor del juego, GitHub, los dos o una dirección tuya."),
        seccion("Contenido para adultos", [
            Opcion(lambda: f"Contenido para mayores de 18 años: {'activado' if cfg['adultos'] else 'desactivado'}", ajuste=adultos,
                   ayuda="Añade relaciones sentimentales y sexuales, ligar con cualquiera, aventuras, compañía de pago, drogas y trapicheo, contado de forma sensual pero sin escenas explícitas. Todo tiene consecuencias en el ánimo, la salud, la reputación y las relaciones. Desactivado, nada de eso aparece en el juego."),
            lista("atraccion", "Me atraen", "Con quién puedes coquetear."),
            lista("mi_genero", "Soy", "Sirve para saber a quién le puedes gustar. Si prefieres no decirlo, le puedes gustar a cualquiera."),
            si_no("noche_por_pasos", "La noche con alguien, paso a paso",
                  "Con sí, cuando pasas la noche con alguien decides tú qué haces en cada momento y la otra persona responde. Fijarte en lo que quiere, y parar si te lo pide, es lo que hace que salga bien. "
                  "Se sigue contando de forma sensual, sin escenas explícitas. Con no, la noche se cuenta en un par de frases, como antes."),
        ], "Activa o desactiva los temas para mayores de 18 años."),
    ]
    principal_ = Menu(app, "Opciones", secciones + [Opcion("Volver", lambda: app.cerrar(principal_), ayuda="Cierra las opciones. También sirve Escape.")],
                      al_cerrar=cfg.guardar, intro="Las opciones están agrupadas por secciones. Pulsa Intro para entrar en una")
    app.abrir(principal_)


# ========================================================================== intro
def intro(p):
    app = p.app

    def empezar():
        bar = p.mundo.lugares["bar_gaviota"]
        p.decir(f"Estás en la {p.mundo.describir(p.j.x, p.j.y)}. {p.situar(bar.x, bar.y, bar.nombre)}. Camina con las flechas y pulsa Intro ante la puerta. Pulsa F1 para ver las teclas.")
        p.gps_a_lugar(bar, callar=True)

    def tras_intro():
        def con():
            app.cerrar(m)
            app.abrir(Dialogo(app, ayuda.TUTORIAL, empezar))

        def sin():
            app.cerrar(m)
            empezar()
        m = Menu(app, "¿Quieres escuchar el tutorial?", [Opcion("Sí, explícame cómo se juega", con), Opcion("No, ya sé jugar", sin)], escapable=False)
        app.abrir(m)
    app.abrir(Dialogo(app, [(q, p.txt(t)) for q, t in ayuda.INTRO], tras_intro))


# ========================================================================== pausa
def pausa(p):
    app = p.app

    def salir():
        def si():
            app.volver_al_menu()
        app.abrir(Menu(app, "¿Salir al menú principal? Se perderá lo que no hayas guardado", [Opcion("No, seguir jugando", lambda: app.cerrar()), Opcion("Sí, salir", si)]))
    ops = [
        Opcion("Reanudar", lambda: app.cerrar()),
        Opcion("Objetivo actual", lambda: app.decir(p.objetivo_txt(), True)),
        Opcion("Guardar partida", lambda: menu_guardar(p)),
        Opcion("Cargar partida", lambda: menu_cargar(app)),
        Opcion("Opciones", lambda: opciones(app)),
        Opcion("Ayuda de teclas", lambda: ayuda_teclas(app, "todo")),
        Opcion("Aprender los sonidos", lambda: sonidos(app)),
        Opcion("Abrir el manual", lambda: abrir_manual(app)),
        Opcion("Salir al menú principal", salir),
    ]
    app.abrir(Menu(app, "Pausa", ops))


# ========================================================================== móvil
GRUPOS = [("Todos los lugares", None), ("Mis casas y negocios", "propio"), ("Sin visitar", "nuevo"),
          ("Tiendas y comida", ("tienda", "comida", "pizzeria", "farmacia", "bar")), ("Armerías", ("armeria",)),
          ("Talleres y desguace", ("taller", "desguace")), ("Casas y negocios en venta", ("casa", "negocio")),
          ("Servicios: hospital, comisaría y taxi", ("hospital", "comisaria", "taxi", "periodico")),
          ("Ocio: casino y carreras", ("casino", "carrera")), ("Monumentos y sitios de interés", ("monumento",))]


GRUPOS += [("Viajes: carreteras, autobuses y embarcaderos", ("salida", "estacion", "embarcadero", "muelle", "nautica")),
           ("Bancos, gimnasios, cines y otros servicios", ("banco", "gimnasio", "cine", "hotel", "ropa", "loteria", "empenos", "concesionario", "pescaderia", "taberna", "pesca"))]


def lista_lugares(p, al_elegir=None, titulo=None, mapa=None, otras=True):
    app = p.app
    mundo = mapa or p.mundo
    titulo = titulo or f"Lugares de {mundo.nombre}"

    def otras_localidades():
        ops = [Opcion(f"{m.nombre}. {m.barrios[0].get('descripcion', '')}", (lambda m=m: lista_lugares(p, al_elegir, None, m, False)))
               for m in p.mapas.values() if m.id != p.mundo.id]
        app.abrir(Menu(app, "Otras localidades", ops, intro="El GPS te guiará hasta la carretera, la estación o el embarcadero que lleva allí"))

    def abrir_grupo(nombre, filtro):
        def ops():
            lista = []
            for l in sorted(mundo.lugares.values(), key=lambda l: l.nombre.lower()):
                if filtro == "propio" and l.id not in p.j.propiedades:
                    continue
                if filtro == "nuevo" and l.id in p.j.visitados:
                    continue
                if isinstance(filtro, tuple) and l.tipo not in filtro:
                    continue
                marca = "" if l.id in p.j.visitados else ", sin visitar"

                def ir(l=l):
                    while len(app.pila) > 1 and app.pila[-1] is not p:
                        app.pila.pop()
                    app.teclas.clear()
                    if al_elegir:
                        al_elegir(l)
                    else:
                        p.gps_a_lugar(l)
                texto = p.situar(l.x, l.y, l.nombre) if l.mapa == p.mundo.id else l.nombre
                lista.append(Opcion(texto + marca, ir, ayuda=l.desc))
            return lista or [Opcion("No hay ningún lugar en esta lista")]
        mg = Menu(app, nombre, ops, intro="En orden alfabético. Pulsa una letra para saltar, Intro para elegir y F1 para la descripción")
        app.abrir(mg)
    grupos = [Opcion(n, (lambda n=n, f=f: abrir_grupo(n, f))) for n, f in GRUPOS]
    if otras and len(p.mapas) > 1:
        grupos.append(Opcion("Otras localidades", otras_localidades))
    mp = Menu(app, titulo, grupos)
    app.abrir(mp)


def movil(p):
    app = p.app
    j = p.j

    def misiones():
        def ops():
            lista = []
            for m in p.misiones_disponibles():
                l = p.lugares[m["lugar"]]

                def ir(l=l):
                    app.cerrar(mm)
                    app.cerrar(menu)
                    p.gps_a_lugar(l)
                donde = p.situar(l.x, l.y, l.nombre) if l.mapa == p.mundo.id else p.nombre_lugar(l)
                if m.get("tutorial") and m["id"] != "tut01":
                    def empezar(m=m):
                        if p.mision:
                            app.son("error")
                            app.decir("Termina o abandona antes la misión que tienes en curso.", True)
                            return
                        while app.pila and app.pila[-1] is not p:
                            app.cerrar(app.pila[-1])
                        p.iniciar_mision(m)
                    lista.append(Opcion(f"Tutorial: {m['titulo']}. {p.txt(m['resumen'])}", empezar, ayuda="Pulsa Intro para empezarlo ahora, estés donde estés. Si estás lejos de donde se hace, el tutorial te lleva allí él mismo."))
                    continue
                lista.append(Opcion(f"{m['titulo']}. {p.txt(m['resumen'])} {donde}", ir, ayuda="Pulsa Intro para marcar el lugar en el GPS."))
            return lista or [Opcion("No hay misiones disponibles ahora mismo")]
        mm = Menu(app, "Misiones disponibles", ops, intro="Intro marca en el GPS el lugar donde empieza")
        app.abrir(mm)

    def abandonar():
        app.cerrar(menu)
        p.abandonar_mision()

    def taxi():
        if j.estrellas:
            app.son("error")
            app.decir("Ningún taxista te recoge mientras te busca la policía.", True)
            return
        if p.mision:
            app.son("error")
            app.decir("Durante una misión tienes que llegar por tus medios.", True)
            return
        app.cerrar(menu)
        menu_viaje(p)

    def propiedades():
        ops = []
        for pid in j.propiedades:
            l = p.lugares.get(pid)
            if not l:
                continue
            if l.tipo == "negocio":
                ops.append(Opcion(f"{p.nombre_lugar(l)}: negocio, {l.get('ingresos', 0)} euros al día"))
            else:
                g = j.garajes.get(pid, [])
                ops.append(Opcion(f"{p.nombre_lugar(l)}: casa, {len(g)} de {l.get('garaje', 0)} vehículos en el garaje"))
        for b in j.barcos:
            e = p.lug(b.get("en"))
            ops.append(Opcion(f"Barco {b.get('nombre', b['modelo'])}, amarrado en {p.nombre_lugar(e) if e else 'puerto'}"))
        ops.append(Opcion(f"Cuenta del banco: {j.banco} euros"))
        app.abrir(Menu(app, "Tus propiedades", ops))

    def estadisticas():
        s = j.stats
        h, mi = int(s["tiempo"] // 3600), int(s["tiempo"] % 3600 // 60)
        total = len(p.datos["misiones"])
        ops = [f"Misiones completadas: {len(p.completadas)} de {total}", f"Dinero: {j.dinero} euros. Ganado en total: {s['dinero_ganado']}",
               f"Tiempo jugado: {h} horas y {mi} minutos. Día {p.dia}", f"Lugares visitados: {len(j.visitados)} de {len(p.lugares)}",
               f"Barrios y localidades visitados: {len(j.barrios_vistos)} de {sum(len(m.barrios) for m in p.mapas.values())}",
               f"Objetos de colección: {len(j.casetes)} de {p.total_casetes()}",
               f"Peces pescados: {s.get('peces', 0)}. Servicios de trabajo: {s.get('servicios', 0)}",
               f"Vehículos robados: {s['vehiculos_robados']}. Vendidos al desguace: {s['vendidos']}", f"Enemigos abatidos: {s['enemigos']}",
               f"Carreras de taxi: {s['carreras_taxi']}. Pizzas entregadas: {s['pizzas']}", f"Carreras callejeras ganadas: {len(s['carreras'])} de {len(p.datos['carreras'])}",
               f"Distancia a pie: {int(s['metros_pie'])} metros. Al volante: {int(s['metros_coche'] / 1000)} kilómetros",
               f"Veces en el hospital: {s['muertes']}. Detenciones: {s['detenciones']}"]
        app.abrir(Menu(app, "Estadísticas", [Opcion(t) for t in ops]))

    def barrios():
        ops = [Opcion(f"{b['nombre']}{'' if m.nombre == b['nombre'] else ', ' + m.nombre}{'' if b['id'] in j.barrios_vistos else ', sin visitar'}. {b['descripcion']}")
               for m in p.mapas.values() for b in m.barrios]
        app.abrir(Menu(app, "Barrios y localidades", ops))

    def inventario():
        ops = []
        for ident in p.orden_armas:
            if ident in j.armas:
                a = p.armas_d[ident]
                t = f"{p.orden_armas.index(ident) + 1}: {a['nombre']}"
                if a["tipo"] in ("fuego", "explosivo"):
                    t += f", {j.armas[ident]['cargador']} balas y {j.armas[ident]['reserva']} de reserva"
                ops.append(Opcion(t, ayuda=a["desc"]))
        ops.append(Opcion(f"Botiquines: {j.objetos.get('botiquin', 0)}"))
        ops.append(Opcion(f"Ganzúas: {j.objetos.get('ganzua', 0)}"))
        ops.append(Opcion(f"Blindaje: {int(j.blindaje)}"))
        app.abrir(Menu(app, "Inventario", ops))

    def diario():
        """Lo que ha pasado en la historia, de lo último a lo primero. Desde aquí se repite cualquier misión ya hecha."""
        por_id = {m["id"]: m for m in p.datos["misiones"]}

        def repetir(m):
            def f():
                if p.mision:
                    app.son("error")
                    app.decir("Termina o abandona antes la misión que tienes en curso.", True)
                    return
                l = p.lugares.get(m["lugar"])
                if l is None:
                    app.son("error")
                    app.decir("Esa misión es de un mod que ahora no está cargado.", True)
                    return

                def si():
                    while app.pila and app.pila[-1] is not p:
                        app.cerrar(app.pila[-1])
                    if l.mapa != p.mundo.id:
                        if j.veh:
                            v = j.veh
                            p.salir_vehiculo(forzado=True)
                            p.quitar_vehiculo(v)
                        p.cambiar_mapa(l.mapa, l.x, l.y)
                    p.teletransportar(l.x, l.y)
                    p.iniciar_mision(m, repeticion=True)
                app.abrir(Menu(app, f"¿Repetir {m['titulo']}? Te lleva al lugar donde empieza. No cuenta ni da recompensa",
                               [Opcion("Sí, repetirla", si), Opcion("No", lambda: app.cerrar())]))
            return f

        def ops_d():
            lista = [Opcion(p.resumen_historia)]
            for clave, valor in p.decisiones.items():
                if isinstance(valor, dict) and valor.get("texto"):
                    renta = int(valor.get("renta", 0))
                    lista.append(Opcion(f"Decisión: {valor['texto']}" + (f". Te deja {renta} euros cada medianoche" if renta > 0 else f". Te cuesta {-renta} euros cada medianoche" if renta < 0 else "")))
            for ident in reversed(p.completadas):
                m = por_id.get(ident)
                if m is None or (m.get("adultos") and not app.cfg["adultos"]):
                    continue
                nota = ", saltada" if ident in p.saltadas else ""
                lista.append(Opcion(f"{m['titulo']}{nota}. {p.txt(m.get('resumen', ''))}", repetir(m), ayuda="Intro para volver a jugar esta misión. Repetirla no da recompensa ni cambia la historia."))
            return lista
        app.abrir(Menu(app, f"Diario. {len(p.completadas)} misiones hechas", ops_d, intro="Arriba, por dónde vas. Debajo, lo que has hecho, de lo último a lo primero. Intro repite una misión"))

    def ops():
        lista = [Opcion("Objetivo actual", lambda: app.decir(p.objetivo_txt(), True)),
                 Opcion("Misiones disponibles", misiones),
                 Opcion("Diario: lo que ha pasado y repetir misiones", diario,
                        ayuda="Un resumen de por dónde vas en la historia y la lista de las misiones que has hecho. Desde ahí puedes repetir cualquiera.")]
        if p.mision:
            lista.append(Opcion("Abandonar la misión en curso", abandonar))
        from . import menus_extra as mx
        from .pantallas import ExploradorMapa
        lista += [Opcion("Lugares y GPS", lambda: lista_lugares(p)),
                  Opcion("Explorar el mapa con el cursor", lambda: app.abrir(ExploradorMapa(app, p)), ayuda="Recorre la localidad cruce a cruce sin mover al personaje. También se abre con F9."),
                  Opcion("Marcadores personales", lambda: mx.marcadores(p)),
                  Opcion("Servicios: vehículo, guardaespaldas, ambulancia y taxi", lambda: mx.servicios(p)),
                  Opcion(lambda: "Jugar con amigos" + (f": conectado, {len(p.remotos) + 1} jugadores" if p.online_activo() else ""),
                         lambda: __import__("juego.menus_online", fromlist=["x"]).amigos(p),
                         ayuda="Abre tu partida para que entren tus amigos, o únete a la de uno. Tu propio juego hace de servidor: no hace falta nada más."),
                  Opcion(lambda: f"Tus conocidos: {len(j.conocidos)}", lambda: __import__("juego.menus_charla", fromlist=["x"]).conocidos(p),
                         ayuda="La gente de la calle que te ha dado su número. Hablas con cualquiera con la tecla J."),
                  Opcion("Tu carrera: vida honrada y vida delictiva", lambda: __import__("juego.menus_vida", fromlist=["x"]).carrera(p)),
                  Opcion("Habilidades y logros", lambda: mx.progreso(p)),
                  Opcion("Territorios: guerras de barrio", lambda: mx.territorios(p)),
                  ] + ([Opcion("Vida social: relaciones", lambda: __import__("juego.menus_adultos", fromlist=["x"]).vida_social(p)),
                        Opcion("Sustancias y mercancía", lambda: __import__("juego.menus_adultos", fromlist=["x"]).menu_sustancias(p))] if p.modo_adulto() else []) + [
                  Opcion("Inventario", inventario),
                  Opcion("Propiedades", propiedades),
                  Opcion("Barrios", barrios),
                  Opcion("Estadísticas", estadisticas)]
        return lista
    menu = Menu(app, lambda: f"Móvil. {p.hora_txt()}. {j.dinero} euros", ops)
    app.abrir(menu)


def menu_viaje(p):
    app = p.app

    def viajar(l):
        x, y = p.pos()
        d = math.hypot(l.x - x, l.y - y)
        coste = int(10 + d * 0.05)
        if not p.pagar(coste):
            return

        def llegar():
            p.teletransportar(l.x, l.y)
            p.pasar_horas(d / 600.0)
            p.app.son("puerta_coche")
            p.decir(f"El taxi te deja en {l.nombre} por {coste} euros. Son las {p.hora_txt()}.")
        from .pantallas import viajar as trayecto
        trayecto(p.app, max(12.0, min(45.0, d / 14.0)), llegar, destino=l.nombre)
    if p.mundo.tipo == "mar":
        p.app.decir("En mitad del mar no hay taxis.", True)
        return
    lista_lugares(p, viajar, "Taxi: ¿a dónde te llevo? El precio depende de la distancia", otras=False)


def menu_armas(p):
    app = p.app
    j = p.j

    def elegir(ident):
        def f():
            app.cerrar(m)
            p.elegir_arma(ident)
        return f
    ops = []
    for ident in p.orden_armas:
        if ident in j.armas:
            a = p.armas_d[ident]
            t = a["nombre"]
            if a["tipo"] in ("fuego", "explosivo"):
                t += f", {j.armas[ident]['cargador'] + j.armas[ident]['reserva']} disparos"
            ops.append(Opcion(t + (", en la mano" if ident == j.arma else ""), elegir(ident), ayuda=a["desc"]))
    m = Menu(app, "Tus armas", ops, intro="Intro para empuñar. F1 describe el arma")
    m.i = next((k for k, i in enumerate([i for i in p.orden_armas if i in j.armas]) if i == j.arma), 0)
    app.abrir(m)


# ========================================================================= lugares
def lugar(p, l):
    app = p.app
    j = p.j
    if not p.lugar_abierto(l):
        app.son("error")
        app.decir(f"{l.nombre}. Está cerrado: aquí todavía no te conocen.", True)
        return
    en_coche = j.veh is not None
    if en_coche and l.tipo not in ("taller", "desguace", "casa", "carrera", "salida", "muelle", "estacion", "embarcadero", "pesca", "monumento", "helipuerto", "tesoro", "aeropuerto", "tranvia", "tren"):
        app.decir(f"{l.nombre}. Bájate del vehículo con F para entrar.", True)
        return
    if en_coche and abs(j.veh.vel) > 3:
        app.decir("Detén el vehículo primero.", True)
        return
    from . import menus_lugares as ml
    f = {"casa": _casa, "armeria": _armeria, "tienda": _tienda, "farmacia": _farmacia, "comida": _comida,
         "pizzeria": _comida, "hospital": _hospital, "comisaria": _comisaria, "taller": _taller,
         "desguace": _desguace, "casino": _casino, "bar": _bar, "negocio": _negocio, "taxi": _taxi,
         "carrera": _carrera, "periodico": _periodico, "salida": ml.salida, "estacion": ml.estacion,
         "embarcadero": ml.embarcadero, "muelle": ml.muelle, "pesca": ml.punto_pesca, "nautica": ml.nautica,
         "concesionario": ml.concesionario, "banco": ml.banco, "loteria": ml.loteria, "empenos": ml.empenos,
         "pescaderia": ml.pescaderia, "gimnasio": ml.gimnasio, "ropa": ml.ropa, "cine": ml.cine,
         "hotel": ml.hotel, "taberna": ml.taberna, "tranvia": ml.tranvia, "tren": ml.tren, "aeropuerto": ml.aeropuerto}.get(l.tipo)
    if l.tipo in ("helipuerto", "protectora", "feria", "tesoro"):
        from . import menus_extra as mx
        f = {"helipuerto": mx.helipuerto, "protectora": mx.protectora, "feria": mx.feria, "tesoro": mx.tesoro}[l.tipo]
    if l.tipo in ("club", "proveedor"):
        from . import menus_adultos as ma
        f = {"club": ma.club, "proveedor": ma.proveedor}[l.tipo]
    if l.tipo in ("empleo", "academia", "ong"):
        from . import menus_vida as mv
        f = {"empleo": mv.empleo, "academia": mv.academia, "ong": mv.ong}[l.tipo]
    if f is None:
        app.decir(f"{l.nombre}. {l.desc}", True)
        return
    if not en_coche and l.tipo not in ("salida", "muelle", "embarcadero", "estacion", "pesca", "tesoro", "helipuerto", "carrera", "taxi", "tranvia", "tren", "aeropuerto"):
        p.entrar_interior(l)
    f(p, l)
    if app.pila and app.pila[-1] is p:
        p.salir_interior(silencio=True)
    elif not en_coche and app.pila and isinstance(app.pila[-1], Menu):
        from . import sistemas
        sistemas.con_recorrido(p, l, app.pila[-1], Opcion)
    if p.acompanante:
        from . import sistemas
        sistemas.visita_con_acompanante(p, l)
    if l.tipo in ("bar", "taberna") and not en_coche and app.pila and isinstance(app.pila[-1], Menu) and app.pila[-1] is not p:
        from . import sistemas
        sistemas.con_cartas(p, app.pila[-1], Menu, Opcion)


def _menu_lugar(p, l, ops, intro=None):
    m = Menu(p.app, lambda: f"{l.nombre}. Tienes {p.j.dinero} euros", ops, intro=intro)
    p.app.abrir(m)
    return m


def _comprar_comida(p, c, factor=1.0):
    def f():
        precio = int(c["precio"] * factor)
        con_hambre = p.vida_realista() and p.j.hambre >= 15           # con vida realista se come por hambre, aunque la salud esté entera
        if p.j.salud >= p.j.salud_max and not con_hambre:
            p.app.decir("No tienes hambre: tu salud está al máximo." if not p.vida_realista() else "Ahora no tienes hambre. La tecla V te dice cómo vas de hambre y de sueño.", True)
            return
        if p.pagar(precio):
            p.j.salud = min(p.j.salud_max, p.j.salud + c["salud"])
            p.son("comer", cat="interfaz")
            hambre = p.necesidades_txt()
            p.app.decir(f"{c['nombre']}. Salud {int(p.j.salud)}.{hambre}", True)
    return f


def _comprar_objeto(p, ident):
    o = next(x for x in p.datos["objetos"] if x["id"] == ident)

    def f():
        if ident == "chaleco":
            if p.j.blindaje >= 100:
                p.app.decir("Ya llevas un chaleco en perfecto estado.", True)
            elif p.pagar(o["precio"]):
                p.j.blindaje = 100.0
                p.son("dinero", cat="interfaz")
                p.app.decir("Chaleco puesto. Blindaje 100.", True)
        elif p.pagar(o["precio"]):
            p.j.objetos[ident] = p.j.objetos.get(ident, 0) + 1
            p.son("dinero", cat="interfaz")
            p.app.decir(f"{o['nombre']} comprado. Tienes {p.j.objetos[ident]}.", True)
    return Opcion(lambda: f"{o['nombre']}: {o['precio']} euros", f, ayuda=o["desc"])


def _casa(p, l):
    app = p.app
    j = p.j
    if l.id not in j.propiedades:
        precio = int(l.get("precio", 0))

        def comprar():
            if p.pagar(precio):
                j.propiedades.append(l.id)
                app.cerrar(m)
                app.son("mision_ok")
                app.decir(f"¡{l.nombre} es tuya! Aquí puedes guardar la partida, descansar y dejar {l.get('garaje', 0)} vehículos.", True)
        m = _menu_lugar(p, l, [Opcion(f"Comprar por {precio} euros", comprar, ayuda=l.desc), Opcion("Descripción", lambda: app.decir(l.desc, True))], "Esta vivienda está en venta")
        return
    garaje = j.garajes.setdefault(l.id, [])

    def descansar():
        if j.estrellas:
            app.son("error")
            app.decir("No puedes descansar con la policía en la puerta.", True)
            return
        p.pasar_horas(8, dormir=True)
        j.salud = j.salud_max
        p.son("pasan_horas", cat="interfaz")
        app.decir(f"Duermes ocho horas. Salud al máximo. Son las {p.hora_txt()} del día {p.dia}.", True)

    def esconderse():
        p.pasar_horas(3)
        p._fin_persecucion()
        p.son("pasan_horas", cat="interfaz")
        app.decir(f"Te quedas tres horas con las persianas bajadas. La policía deja de buscarte. Son las {p.hora_txt()}.", True)
        m.refrescar(False)

    def guardar_veh():
        v = j.veh
        if v.tag:
            app.son("error")
            app.decir("Ese vehículo es de una misión.", True)
            return
        if len(garaje) >= int(l.get("garaje", 0)):
            app.son("error")
            app.decir("El garaje está lleno.", True)
            return
        garaje.append({"modelo": v.modelo["id"], "salud": v.salud, "nombre": v.nombre, "mejoras": dict(getattr(v, "mejoras", {}))})
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
        j.x, j.y = l.x, l.y
        p.son("puerta_coche")
        app.decir(f"{v.nombre} guardado en el garaje.", True)
        m.refrescar(False)

    def sacar(k):
        def f():
            d = garaje.pop(k)
            x, y, di = p.mundo.plaza_junto_a(l)
            v = p.crear_vehiculo(d["modelo"], x, y, di, None, d.get("nombre"))
            from . import sistemas
            sistemas.poner(v, d.get("mejoras"))
            v.salud = min(v.salud_max, float(d.get("salud", v.salud_max)))
            v.propio = True
            app.cerrar(m)
            app.decir(f"{v.nombre} te espera en la calle. {p.situar(x, y, 'Está')}.", True)
        return f

    def ops():
        lista = []
        if not p.mision:
            lista.append(Opcion("Guardar la partida", lambda: menu_guardar(p)))
        if j.veh:
            lista.append(Opcion(f"Meter {j.veh.nombre} en el garaje", guardar_veh))
        else:
            lista.append(Opcion("Descansar ocho horas y recuperar la salud", descansar))
            if 0 < j.estrellas <= 2:
                lista.append(Opcion("Esconderte hasta que la policía deje de buscarte", esconderse))
        for k, d in enumerate(garaje):
            lista.append(Opcion(f"Sacar del garaje: {d.get('nombre', d['modelo'])}", sacar(k)))
        lista.append(Opcion(f"Garaje: {len(garaje)} de {l.get('garaje', 0)} plazas ocupadas"))
        from . import laboratorio
        lista += laboratorio.opciones_casa(p, l, Menu, Opcion)
        if not j.veh:
            lista.append(Opcion("Recorrer la casa por dentro", recorrer,
                                ayuda="Entras y vas de una habitación a otra con las flechas: salón, cocina, baño, dormitorio y garaje. En cada una, Intro hace lo suyo."))
        return lista

    def recorrer():
        from . import sistemas
        app.son("puerta_entrar")
        app.abrir(sistemas.Interior(p, l, {"descansar": descansar, "garaje": lambda: app.decir(
            f"Garaje: {len(garaje)} de {l.get('garaje', 0)} plazas ocupadas" + ("." if not garaje else ": " + ", ".join(d.get("nombre", d["modelo"]) for d in garaje) + ".") +
            " Para sacar un vehículo, usa el menú de la casa.", True)}))
    m = _menu_lugar(p, l, ops)


SIN_SILENCIADOR = ("escopeta", "escopeta_combate", "ametralladora", "minigun", "lanzacohetes", "ballesta")


def _armeria(p, l):
    app = p.app
    j = p.j
    factor = float(l.get("descuento", 1.0)) * p.mercado("armas", l.id)

    def comprar(a):
        def f():
            if a["id"] not in j.armas:
                if p.pagar(int(a["precio"] * factor)):
                    p.dar_arma(a["id"], a.get("balas", 0))
                    p.son("dinero", cat="interfaz")
                    m.refrescar(False)
            else:
                if p.pagar(int(a["precio_balas"] * factor)):
                    j.armas[a["id"]]["reserva"] += a["balas"]
                    p.son("recarga", cat="interfaz")
                    app.decir(f"Munición comprada. Reserva: {j.armas[a['id']]['reserva']} balas.", True)
        return f

    def mejorar(a, cual, precio):
        def f():
            if p.pagar(int(precio * factor)):
                j.armas[a["id"]][cual] = True
                p.son("recarga", cat="interfaz")
                app.decir(f"{'Silenciador' if cual == 'silenciador' else 'Cargador ampliado'} montado en {a['nombre']}.", True)
                m.refrescar(False)
        return f

    def ops():
        lista = []
        for a in p.datos["armas"]:
            if a["precio"] <= 0:
                continue
            if a["id"] not in j.armas:
                lista.append(Opcion(f"{a['nombre']}: {int(a['precio'] * factor)} euros", comprar(a), ayuda=a["desc"]))
            elif a["tipo"] in ("fuego", "explosivo"):
                lista.append(Opcion(f"Munición para {a['nombre']}, {a['balas']} balas: {int(a['precio_balas'] * factor)} euros. Tienes {j.armas[a['id']]['reserva']} de reserva", comprar(a), ayuda=a["desc"]))
        for a in p.datos["armas"]:                              # mejoras para las armas de fuego que ya tienes
            if a["id"] in j.armas and a["tipo"] == "fuego":
                mio = j.armas[a["id"]]
                if not mio.get("silenciador") and a.get("ruido", 2) > 0 and a["id"] not in SIN_SILENCIADOR:
                    lista.append(Opcion(f"Silenciador para {a['nombre']}: {int(900 * factor)} euros", mejorar(a, "silenciador", 900),
                                        ayuda="Los disparos dejan de oírse desde lejos: la gente no huye y nadie llama a la policía por el ruido. Lo que hagas a la vista de alguien se sigue viendo. Se pierde con el arma si te detienen."))
                if not mio.get("ampliado") and a.get("cargador", 0) > 1:
                    lista.append(Opcion(f"Cargador ampliado para {a['nombre']}, de {a['cargador']} a {int(a['cargador'] * 1.5)} balas: {int(600 * factor)} euros", mejorar(a, "ampliado", 600),
                                        ayuda="Caben la mitad más de balas, así que recargas menos veces. Se pierde con el arma si te detienen."))
        lista.append(_comprar_objeto(p, "chaleco"))
        lista.append(_comprar_objeto(p, "ganzua"))
        lista.append(Opcion("Galería de tiro: 20 euros la tanda", tiro, ayuda="Diez dianas que suenan a la izquierda, al centro o a la derecha. Mejora tu puntería y da premio con siete aciertos."))
        return lista

    def tiro():
        if p.pagar(20):
            from .pantallas import TiroAlBlanco
            while len(app.pila) > 1 and app.pila[-1] is not p:
                app.pila.pop()
            app.abrir(TiroAlBlanco(app, p))
    m = _menu_lugar(p, l, ops, "F1 describe cada arma")


def _tienda(p, l):
    app = p.app
    j = p.j
    atracadas = p.atracadas

    def atracar():
        if p.arma()["tipo"] != "fuego":
            app.son("error")
            app.decir("Para atracar la tienda tienes que empuñar un arma de fuego.", True)
            return
        if atracadas.get(l.id) == p.dia:
            app.son("error")
            app.decir("La caja está vacía: ya la atracaste hoy.", True)
            return
        atracadas[l.id] = p.dia
        botin = random.randint(150, 500)
        app.cerrar(m)
        p.son("grito", vol=0.5)
        p.dar_dinero(botin)
        p.decir(f"¡Manos arriba! El dependiente vacía la caja: {botin} euros. ¡Ha pulsado la alarma, lárgate!")
        p.poner_busqueda(2)
    factor = p.mercado("comida", l.id)
    ops = [Opcion(lambda c=c: f"{c['nombre']}, recupera {c['salud']} de salud: {int(c['precio'] * factor)} euros", _comprar_comida(p, c, factor)) for c in p.datos["comidas"][:3:2]]
    ops += [_comprar_objeto(p, "botiquin"), _comprar_objeto(p, "ganzua"), Opcion("Atracar la tienda", atracar, ayuda="Necesitas un arma de fuego en la mano. La policía te buscará.")]
    m = _menu_lugar(p, l, ops)


def _salud_intima(p):
    """Opciones de farmacias y hospitales del contenido para adultos."""
    if not p.modo_adulto():
        return []
    art = p.articulos_intimos()[0]
    return [Opcion(lambda: f"{art['nombre']}: {art['precio']} euros. Llevas {p.j.intimos.get('preservativos', 0)}", lambda: p.comprar_articulo(art), ayuda=art["desc"]),
            Opcion("Prueba de salud sexual, gratis. El tratamiento, si hace falta, 120 euros", p.prueba_y_tratamiento)]


def _farmacia(p, l):
    _menu_lugar(p, l, [_comprar_objeto(p, "botiquin")] + _salud_intima(p))


def _comida(p, l):
    factor = (3.0 if l.get("caro") else 1.0) * p.mercado("comida", l.id)
    ops = [Opcion(lambda c=c: f"{c['nombre']}, recupera {c['salud']} de salud: {int(c['precio'] * factor)} euros", _comprar_comida(p, c, factor)) for c in p.datos["comidas"]]
    if l.tipo == "pizzeria":
        def trabajar():
            p.app.cerrar(m)
            p.empezar_pizzas()
        ops.append(Opcion("Trabajar repartiendo pizzas", trabajar, ayuda="Cuatro entregas contrarreloj. Cuanto antes llegues, más propina."))
    m = _menu_lugar(p, l, ops)


def _hospital(p, l):
    j = p.j

    def curar():
        falta = int(j.salud_max - j.salud)
        if falta <= 0:
            p.app.decir("Estás como una rosa. No necesitas nada.", True)
        elif p.pagar(falta * 2):
            j.salud = j.salud_max
            p.son("curar", cat="interfaz")
            p.app.decir("Te curan. Salud al máximo.", True)
    ops = [Opcion(lambda: f"Que te curen: {max(0, int(j.salud_max - j.salud)) * 2} euros. Salud actual {int(j.salud)}", curar), _comprar_objeto(p, "botiquin")]
    if p.modo_adulto():
        from . import menus_adultos as ma
        ops.append(Opcion("Desintoxicación: 800 euros y dos días en la clínica", lambda: ma.desintoxicar(p), ayuda="Elimina todas tus dependencias."))
        ops += _salud_intima(p)
    _menu_lugar(p, l, ops)


def _comisaria(p, l):
    j = p.j

    def sobornar():
        if not j.estrellas:
            p.app.decir("No te busca nadie.", True)
            return
        if p.pagar(400 * j.estrellas):
            p._fin_persecucion()
            p.app.decir("Un sobre cambia de manos y tu expediente desaparece. Ya no te buscan.", True)
    _menu_lugar(p, l, [Opcion(lambda: f"Pagar un soborno para que dejen de buscarte: {400 * j.estrellas} euros", sobornar),
                       Opcion(lambda: f"Tu historial: {j.stats['detenciones']} detenciones")])


def _taller(p, l):
    app = p.app
    j = p.j
    if not j.veh:
        app.decir(f"{l.nombre}. Ven con un vehículo para repararlo o pintarlo.", True)
        return
    v = j.veh

    def coste():
        return int(40 + (1 - v.salud / v.salud_max) * max(300, v.modelo["valor"]) * 0.3)

    def reparar():
        if v.salud >= v.salud_max:
            app.decir("El vehículo está perfecto.", True)
        elif p.pagar(coste()):
            v.salud = v.salud_max
            p.son("reparar", cat="interfaz")
            app.decir("Vehículo reparado al 100 por ciento.", True)

    def pintar():
        x, y = p.pos()
        if any(e.tipo == "policia" and not e.muerto and e.dist(x, y) < 45 for e in p.personas) or any(o.ia == "policia" and o.dist(x, y) < 45 for o in p.vehiculos):
            app.son("error")
            app.decir("¡Tienes a la policía encima! Despístalos un poco antes de pintar.", True)
            return
        if p.pagar(300):
            p.son("pintura", cat="interfaz")
            p._fin_persecucion()
            app.decir("Pintura nueva y matrículas nuevas. La policía ya no busca este vehículo.", True)
    from . import sistemas
    _menu_lugar(p, l, [Opcion(lambda: f"Reparar {v.nombre}: {coste()} euros. Estado {int(100 * v.salud / v.salud_max)} por ciento", reparar),
                       Opcion("Pintar y cambiar matrículas: 300 euros. Elimina la búsqueda policial", pintar)] + sistemas.opciones_taller(p, v, Opcion) +
                [Opcion(lambda: sistemas.resumen(v))])


def _desguace(p, l):
    app = p.app
    j = p.j
    if not j.veh:
        def encargo():
            if p.mision or p.trabajo:
                app.son("error")
                app.decir("Termina antes lo que tienes entre manos.", True)
            else:
                p.empezar_encargo_coche(l)
        _menu_lugar(p, l, [Opcion("Pedir un encargo de coche", encargo, ayuda="Te piden un modelo concreto: róbalo donde te digan y tráelo en buen estado. Se puede repetir siempre que quieras."),
                           Opcion("Para vender un vehículo, ven montado en él")])
        return
    v = j.veh

    def precio():
        return int(v.modelo["valor"] * (0.3 + 0.7 * v.salud / v.salud_max))

    def vender():
        if v.tag:
            app.son("error")
            app.decir("Ese vehículo es de una misión. No se vende.", True)
            return
        n = precio()
        if n <= 0:
            app.son("error")
            app.decir("Eso no lo quieren ni regalado.", True)
            return
        app.cerrar(m)
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
        j.x, j.y = l.x, l.y
        j.stats["vendidos"] += 1
        p.dar_dinero(n, f"Vendes {v.nombre}")
    m = _menu_lugar(p, l, [Opcion(lambda: f"Vender {v.nombre} por {precio()} euros", vender)])


def _negocio(p, l):
    app = p.app
    j = p.j
    precio = int(l.get("precio", 0))
    ingresos = int(l.get("ingresos", 0))
    if l.id in j.propiedades:
        app.decir(f"{l.nombre} es tuyo. Te da {ingresos} euros cada día, a medianoche.", True)
        return

    def comprar():
        if p.pagar(precio):
            j.propiedades.append(l.id)
            app.cerrar(m)
            app.son("mision_ok")
            app.decir(f"¡{l.nombre} es tuyo! Ganarás {ingresos} euros cada día.", True)
    m = _menu_lugar(p, l, [Opcion(f"Comprar el negocio por {precio} euros. Da {ingresos} euros al día", comprar, ayuda=l.desc)])


def _taxi(p, l):
    app = p.app

    def alquilar():
        if p.pagar(40):
            x, y, d = p.mundo.plaza_junto_a(l)
            v = p.crear_vehiculo("taxi", x, y, d, None)
            v.propio = True
            app.cerrar(m)
            app.decir(f"Tienes un taxi en la calle. {p.situar(x, y, 'Está')}. Sube con F y pulsa J para empezar a hacer carreras.", True)

    def viajar():
        if p.j.estrellas or p.mision:
            app.son("error")
            app.decir("Ahora mismo ningún taxista quiere llevarte.", True)
            return
        app.cerrar(m)
        menu_viaje(p)
    m = _menu_lugar(p, l, [Opcion("Que te lleven a otro lugar", viajar), Opcion("Alquilar un taxi para trabajar de taxista: 40 euros", alquilar)])


def _carrera(p, l):
    app = p.app
    if not p.j.veh:
        app.decir(f"{l.nombre}. Ven con un vehículo si quieres correr.", True)
        return

    def correr(c):
        def f():
            app.cerrar(m)
            p.empezar_carrera(c)
        return f
    ops = [Opcion(f"{c['nombre']}: premio de {c['premio']} euros, {c['tiempo']} segundos" + (", ya ganada" if c["id"] in p.j.stats["carreras"] else ""), correr(c))
           for c in p.datos["carreras"] if c.get("mapa", "puerto_bravo") == p.mundo.id]
    m = _menu_lugar(p, l, ops or [Opcion("Hoy no hay carreras")])


def _periodico(p, l):
    n = len(p.completadas)
    titulares = ["Hoy en El Faro: el Ayuntamiento promete arreglar el reloj de la plaza por decimoquinta vez.",
                 "Hoy en El Faro: suben los robos de coches en el Barrio Viejo.",
                 "Hoy en El Faro: tiroteo en el puerto, la policía no encuentra testigos.",
                 "Hoy en El Faro: ¿quién paga a Los Calaveras? Una investigación de Marta Salgado.",
                 "Hoy en El Faro: el empresario Octavio Belmonte niega cualquier relación con el crimen organizado.",
                 "Hoy en El Faro: atraco millonario en el Casino Belmonte.",
                 "Hoy en El Faro: el comisario Varela, detenido. Las grabaciones que hunden a Belmonte.",
                 "Hoy en El Faro: Puerto Bravo respira. Belmonte, a disposición judicial."]
    p.app.decir(f"{l.nombre}. {titulares[min(len(titulares) - 1, n * len(titulares) // 21)]}", True)


def _bar(p, l):
    app = p.app
    j = p.j

    def beber():
        if p.pagar(4):
            j.salud = min(j.salud_max, j.salud + 10)
            p.son("comer", cat="interfaz")
            app.decir(f"Una caña y una tapa. Salud {int(j.salud)}.", True)

    def hablar():
        app.decir("Encarna: " + p.objetivo_txt().replace("No tienes ninguna misión en curso. Disponible:", "Deberías pasarte por:"), True)
    ops = [Opcion("Tomar una caña con tapa: 4 euros", beber), Opcion("Hablar con Encarna", hablar)]
    if p.modo_adulto():
        ops.insert(1, Opcion("Tomar una copa: 6 euros", lambda: p.consumir("alcohol", de_inventario=False) if p.pagar(6) else None, ayuda="Alcohol: sube el ánimo, pero caminas torcido y apuntas peor."))
    _menu_lugar(p, l, ops)


# ========================================================================== casino
def _casino(p, l):
    app = p.app
    from . import menus_extra as mx
    _menu_lugar(p, l, [Opcion("Máquina tragaperras", lambda: _tragaperras(p)), Opcion("Mesa de blackjack", lambda: _blackjack(p)),
                       Opcion("Ruleta", lambda: mx.ruleta(p))])


def _tragaperras(p):
    app = p.app
    simbolos = ["cereza", "limón", "campana", "herradura", "siete"]
    premios = {"cereza": 5, "limón": 8, "campana": 15, "herradura": 30, "siete": 100}

    def tirar(apuesta):
        def f():
            if not p.pagar(apuesta):
                return
            r = [random.choices(simbolos, weights=[30, 26, 20, 14, 10])[0] for _ in range(3)]
            p.son("lugar_casino", cat="interfaz", vol=0.5)
            txt = ", ".join(r) + ". "
            if r[0] == r[1] == r[2]:
                g = apuesta * premios[r[0]]
                p.dar_dinero(g)
                txt += f"¡Premio! Ganas {g} euros."
            elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
                g = apuesta * 2
                p.dar_dinero(g)
                txt += f"Pareja. Ganas {g} euros."
            else:
                txt += "Nada."
            app.decir(txt + f" Tienes {p.j.dinero} euros.", True)
        return f
    app.abrir(Menu(app, "Tragaperras. Elige la apuesta", [Opcion(f"Tirar por {a} euros", tirar(a)) for a in (5, 25, 100)]))


def _blackjack(p):
    app = p.app
    e = {"fase": "apuesta", "apuesta": 0, "yo": [], "banca": []}
    nombres = {1: "as", 11: "jota", 12: "reina", 13: "rey"}

    def carta():
        return random.randint(1, 13)

    def nom(c):
        return nombres.get(c, str(c))

    def total(mano):
        t = sum(min(c, 10) for c in mano)
        if 1 in mano and t + 10 <= 21:
            t += 10
        return t

    def fin(resultado):
        a = e["apuesta"]
        tb = total(e["banca"])
        txt = f"La banca tiene {', '.join(nom(c) for c in e['banca'])}: {tb}. "
        if resultado == "gana":
            p.dar_dinero(a * 2)
            txt += f"¡Ganas {a} euros!"
        elif resultado == "blackjack":
            p.dar_dinero(int(a * 2.5))
            txt += f"¡Blackjack! Ganas {int(a * 1.5)} euros."
        elif resultado == "empate":
            p.j.dinero += a
            txt += "Empate. Recuperas la apuesta."
        else:
            txt += f"Pierdes {a} euros."
        e["fase"] = "apuesta"
        m.i = 0
        m.refrescar(False)
        app.decir(txt + f" Tienes {p.j.dinero} euros.", True)

    def plantarse():
        while total(e["banca"]) < 17:
            e["banca"].append(carta())
        ty, tb = total(e["yo"]), total(e["banca"])
        fin("gana" if tb > 21 or ty > tb else "empate" if ty == tb else "pierde")

    def pedir():
        e["yo"].append(carta())
        t = total(e["yo"])
        if t > 21:
            app.decir(f"Sacas {nom(e['yo'][-1])}: {t}. Te pasas.", True)
            fin("pierde")
        elif t == 21:
            plantarse()
        else:
            app.decir(f"Sacas {nom(e['yo'][-1])}. Tienes {t}.", True)

    def apostar(a):
        def f():
            if not p.pagar(a):
                return
            e.update(fase="juego", apuesta=a, yo=[carta(), carta()], banca=[carta(), carta()])
            if total(e["yo"]) == 21:
                fin("blackjack" if total(e["banca"]) != 21 else "empate")
                return
            m.i = 0
            m.refrescar(False)
            app.decir(f"Tienes {nom(e['yo'][0])} y {nom(e['yo'][1])}: {total(e['yo'])}. La banca enseña {nom(e['banca'][0])}. Pedir carta.", True)
        return f

    def ops():
        if e["fase"] == "apuesta":
            return [Opcion(f"Apostar {a} euros", apostar(a)) for a in (20, 100, 500)]
        return [Opcion("Pedir carta", pedir), Opcion("Plantarse", plantarse),
                Opcion(lambda: f"Tu mano: {', '.join(nom(c) for c in e['yo'])}: {total(e['yo'])}. La banca enseña {nom(e['banca'][0])}")]
    m = Menu(app, "Blackjack. Gana quien se acerque más a 21 sin pasarse", ops)
    app.abrir(m)
