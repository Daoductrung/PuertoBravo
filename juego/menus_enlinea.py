"""Menús para jugar en un servidor: la lista de servidores, y dentro de la partida, todo lo que se hace con los demás."""
from . import enlinea, red
from . import mundo as M
from .menus import EntradaTexto, Menu, Opcion
from .menus_online import deletrear


def _copiar(texto):
    """Copia un texto al portapapeles. Devuelve si se ha podido."""
    try:
        import pygame
        pygame.scrap.put_text(texto)
        return True
    except Exception:
        pass
    try:
        import subprocess
        subprocess.run("clip", input=texto.encode("utf-16-le"), shell=True, timeout=5, check=True)
        return True
    except Exception:
        return False


# ================================================================ antes de entrar
def servidores(app):
    cfg = app.cfg
    if not cfg["red_nombre"] and enlinea.perfil():           # en las copias de pruebas, cada instancia con su nombre
        cfg["red_nombre"] = "Jugador " + enlinea.perfil()

    def entrar(s, clave="", invitacion=""):
        def f():
            app.decir(f"Conectando con {s.get('nombre') or 'el servidor'}.", True)
            enlace, motivo = enlinea.conectar(app, s, clave, invitacion)
            if enlace is None:
                if motivo.startswith("certificado: "):
                    return cambio_certificado(s, motivo[13:])
                if "contraseña" in motivo and not clave:
                    return app.abrir(EntradaTexto(app, "Contraseña de entrada del servidor", lambda t: entrar(s, clave=t)(), secreto=True, maximo=60))
                if "invitación" in motivo and not invitacion:
                    return app.abrir(EntradaTexto(app, "Código de invitación que te ha dado quien lleva el servidor", lambda t: entrar(s, invitacion=t)(), maximo=20))
                app.son("error")
                app.decir(motivo, True)
                return
            cfg.guardar()
            app.enlace = enlace
            if enlace.ok.get("partida"):
                # El personaje vive en el servidor. Si la última vez se guardó con una versión del juego más nueva que esta,
                # puede traer cosas que esta no conoce: se avisa, por si algo no va como se espera.
                from . import VERSION
                de = str(enlace.ok.get("partida_de") or "")
                if de and enlinea.version_tupla(de) > enlinea.version_tupla(VERSION):
                    app.decir(f"Aviso: este personaje se guardó la última vez con la versión {de} del juego, más nueva que la tuya. "
                              "Si notas algo raro, actualiza el juego.", True)
                app.empezar_partida(enlace.ok["partida"])
            else:
                app.decir(f"Entras por primera vez en {s.get('nombre')}. Elige con qué personaje vas a jugar aquí.", True)
                from . import menus_vida
                menus_vida.elegir_personaje(app)
        return f

    def cambio_certificado(s, nueva):
        def aceptar():
            s["cert"] = ""
            app.cerrar(mm)
            entrar(s)()
        mm = Menu(app, "El servidor no presenta el mismo certificado que la otra vez", [
            Opcion("No entrar", lambda: app.cerrar(mm), ayuda="Es lo prudente si no sabes por qué ha cambiado."),
            Opcion("Quien lleva el servidor me ha dicho que lo ha cambiado: entrar y recordar el nuevo", aceptar,
                   ayuda="El certificado cambia si reinstalan el servidor. Si nadie te ha avisado, puede que alguien se esté haciendo pasar por él.")])
        app.son("error")
        app.abrir(mm)

    def anadir():
        def hecho(t):
            if red.analizar_direccion(t) is None:
                app.son("error")
                app.decir("No entiendo esa dirección. Tiene que ser como puertobravo, dos puntos, barra, barra, el sitio, dos puntos y el puerto.", True)
                return
            d = t.strip()
            if not d.lower().startswith(red.PREFIJO):
                d = red.PREFIJO + d
            if ":" not in d[len(red.PREFIJO):]:
                d += f":{enlinea.PUERTO}"
            lista = list(cfg["servidores"])
            if not any(x.get("dir") == d for x in lista):
                lista.append({"nombre": "Servidor nuevo", "dir": d, "cert": ""})
            cfg["servidores"] = lista
            cfg.guardar()
            app.decir("Servidor añadido a tu lista. Pulsa Intro sobre él para entrar.", True)
            m.refrescar(False)
        app.abrir(EntradaTexto(app, "Dirección del servidor", hecho, maximo=90,
                               ayuda="Te la da quien lleva el servidor. Puedes pegarla con Control V. Si no lleva puerto, se usa el de serie."))

    def quitar():
        def borrar(s):
            def f():
                cfg["servidores"] = [x for x in cfg["servidores"] if x is not s]
                cfg.guardar()
                app.cerrar(mq)
                app.decir("Quitado de tu lista. Tu personaje sigue guardado en ese servidor.", True)
                m.refrescar(False)
            return f
        mq = Menu(app, "Qué servidor quitas de la lista", [Opcion(f"{s.get('nombre')}, {deletrear(s.get('dir', ''))}", borrar(s)) for s in cfg["servidores"]]
                  or [Opcion("No hay ninguno")])
        app.abrir(mq)

    def nombre():
        def hecho(t):
            cfg["red_nombre"] = t.strip()[:24]
            cfg.guardar()
            app.decir(f"En los servidores en los que entres por primera vez te llamarás {cfg['red_nombre'] or 'Jugador'}.", True)
        app.abrir(EntradaTexto(app, "Tu nombre de jugador", hecho, inicial=cfg["red_nombre"], maximo=24,
                               ayuda="Es el nombre con el que te ven los demás. En un servidor donde ya tienes personaje no cambia."))

    def identidad():
        def exportar():
            ok = _copiar(enlinea.exportar_identidad())
            app.son("menu_ok" if ok else "error")
            app.decir("Tu identidad está copiada en el portapapeles. Pégala en un archivo y guárdalo donde nadie más lo vea. Quien la tenga puede entrar como tú." if ok
                      else "No se pudo copiar al portapapeles.", True)

        def importar():
            def hecho(t):
                if enlinea.importar_identidad(t):
                    app.son("guardado")
                    app.decir("Identidad cambiada. En los servidores donde jugabas con ella, vuelves a ser tú.", True)
                else:
                    app.son("error")
                    app.decir("Eso no es una identidad de Puerto Bravo. Empieza por P B uno y un guion.", True)
            app.abrir(EntradaTexto(app, "Pega aquí la identidad que guardaste", hecho, maximo=90, secreto=True, ayuda="Control V pega."))
        enlinea.identidad()
        app.abrir(Menu(app, "Tu identidad en los servidores", [
            Opcion("Qué es", ayuda="Sin contraseñas ni correo: la primera vez, el juego crea una llave y la guarda en tu carpeta de datos. Cada servidor te reconoce por ella. "
                                   "Si borras la carpeta de datos o cambias de ordenador, la pierdes, y con ella tus personajes, salvo que la hayas guardado antes."),
            Opcion("Copiar mi identidad para guardarla", exportar, ayuda="La copia al portapapeles. Es como una contraseña larga: no se la des a nadie."),
            Opcion("Recuperar una identidad guardada", importar, ayuda="Sustituye la de este ordenador por la que pegues."),
        ], intro="F1 explica cada opción"))

    def ops():
        lista = [Opcion(lambda s=s: f"{s.get('nombre')}, {deletrear(s.get('dir', ''))}", entrar(s), ayuda="Intro entra. Si ya tienes personaje en este servidor, sigues donde lo dejaste.")
                 for s in cfg["servidores"]]
        if not lista:
            lista.append(Opcion("Todavía no tienes ningún servidor en la lista", ayuda="Añade uno con la dirección que te dé quien lo lleva."))
        lista += [Opcion("Añadir un servidor", anadir),
                  Opcion("Quitar un servidor de la lista", quitar),
                  Opcion(lambda: f"Tu nombre de jugador: {cfg['red_nombre'] or 'sin poner'}", nombre),
                  Opcion("Tu identidad", identidad, ayuda="Cómo te reconoce cada servidor, y cómo guardar tu identidad para no perder tus personajes."),
                  Opcion("Qué es jugar en un servidor",
                         ayuda="El mismo juego, con todo lo que haces por tu cuenta, misiones, trabajos, casas y negocios, y además jugadores de verdad: se les oye, se habla con ellos, "
                               "se les da o se les quita dinero, armas y vehículos, se forman bandas, se pelea por los barrios y se hacen misiones en grupo. "
                               "Tu personaje en línea es distinto de tus partidas de un jugador y se guarda en el servidor. La hora es la del servidor y no se para.")]
        return lista
    try:                                                     # las copias de pruebas traen su servidor apuntado
        from . import rutas
        with open(rutas.data("config", "servidor_pruebas.txt"), encoding="utf-8") as f:
            for linea in f:
                if "|" in linea:
                    n, d = [t.strip() for t in linea.split("|", 1)]
                    if d and not any(x.get("dir") == d for x in cfg["servidores"]):
                        cfg["servidores"] = list(cfg["servidores"]) + [{"nombre": n, "dir": d, "cert": ""}]
    except OSError:
        pass
    if getattr(app, "enlace", None) is not None:             # una entrada que se quedó a medias
        app.enlace.cli.cerrar()
        app.enlace = None
    m = Menu(app, "Jugar en un servidor", ops, intro="Elige un servidor y pulsa Intro. F1 explica cada opción")
    app.abrir(m)


# ============================================================== dentro de la partida
def _al_juego(p):
    app = p.app
    while len(app.pila) > 1 and app.pila[-1] is not p:
        app.pila.pop()
    app.teclas.clear()


def _numero(app, titulo, hecho, tope=10 ** 7):
    def f(t):
        try:
            n = int("".join(c for c in t if c.isdigit()) or "0")
        except ValueError:
            n = 0
        if n <= 0 or n > tope:
            app.son("error")
            app.decir("Esa cantidad no vale.", True)
            return
        hecho(n)
    app.abrir(EntradaTexto(app, titulo, f, maximo=9))


TITULOS_ROL = {"ic": "Qué dice tu personaje. Lo oye quien esté cerca", "yo": "Qué hace tu personaje. Por ejemplo: abre la puerta",
               "ooc": "Mensaje fuera de personaje, para todo el servidor"}


def chat(p, canal="todos", a=None, titulo="Mensaje para todo el servidor"):
    app = p.app
    if canal in TITULOS_ROL:
        if not p.sv_rol():
            app.son("error")
            return app.decir(p.sv_rol_motivo(), True)
        titulo = TITULOS_ROL[canal]
    ayuda = None
    if p.sv_rol():
        ayuda = ("Escribe y pulsa Intro. En cualquier mensaje, si empiezas por barra yo y un espacio, cuentas lo que hace tu personaje; con barra ep hablas en personaje, "
                 "para los que están cerca; y con barra fp, fuera de personaje, para todo el servidor.")
    app.abrir(EntradaTexto(app, titulo, lambda t: p.sv_enviar_chat(t, canal, a), maximo=300, ayuda=ayuda))


def ficha_propia(p):
    """Escribir tu frase de ficha: lo que los demás leen de tu personaje."""
    app = p.app
    if not p.sv_rol():
        app.son("error")
        return app.decir(p.sv_rol_motivo(), True)
    app.abrir(EntradaTexto(app, "Tu ficha: una frase sobre tu personaje", p.sv_poner_ficha, inicial=p.sv.get("ficha", ""), maximo=enlinea.MAX_FICHA,
                           ayuda="Quién es tu personaje, cómo es o a qué se dedica, en una frase de hasta doscientas letras. La puede leer cualquier jugador del servidor. "
                                 "Si la dejas vacía, se quita. Lo que escribas no se anota en el registro del juego."))


def rol(p):
    """El menú de rol: hablar en personaje, describir una acción, hablar fuera de personaje, la ficha y lo dicho."""
    app, sv = p.app, p.sv

    def repasar(canales, titulo):
        def abrir():
            lineas = [t for c, t in reversed(sv["historial"]) if c in canales]
            app.abrir(Menu(app, titulo, [Opcion(t) for t in lineas] or [Opcion("Todavía no hay nada")], intro="Lo último, primero"))
        return abrir

    def ops():
        if not p.sv_rol():
            return [Opcion(p.sv_rol_motivo())]
        metros = sv["info"].get("rol_metros", 30)
        return [Opcion("Hablar en personaje", lambda: chat(p, "ic"),
                       ayuda=f"Lo que dice tu personaje. Lo oye quien esté a menos de {metros} metros. También con Mayúsculas F10 durante el juego."),
                Opcion("Describir lo que hace tu personaje", lambda: chat(p, "yo"),
                       ayuda=f"Escribes, por ejemplo, abre la puerta, y los que están a menos de {metros} metros oyen tu nombre y abre la puerta. También con Control F10."),
                Opcion("Hablar fuera de personaje", lambda: chat(p, "ooc"),
                       ayuda="Para hablar como jugador y no como tu personaje: dudas, avisos, quedar. Lo oye todo el servidor."),
                Opcion(lambda: "Tu ficha: " + (sv.get("ficha") or "sin escribir"), lambda: ficha_propia(p),
                       ayuda="Una frase sobre tu personaje que cualquier jugador puede leer: en Quién hay, eligiéndote, o con Mayúsculas J si te tiene cerca."),
                Opcion("Repasar lo dicho en personaje y las acciones", repasar(("ic", "yo"), "En personaje y acciones")),
                Opcion("Repasar lo dicho fuera de personaje", repasar(("ooc",), "Fuera de personaje")),
                Opcion("Cómo se rolea aquí",
                       ayuda=f"Hay tres canales, cada uno con su sonido. En personaje: habla tu personaje, y lo oye quien esté a menos de {metros} metros. Acción: cuentas lo que hace, "
                             "y se oye tu nombre seguido de lo que escribas. Fuera de personaje: hablas tú, y lo oye todo el servidor. En cualquier mensaje puedes empezar por "
                             "barra yo, barra ep o barra fp para elegir el canal, y barra ficha y una frase cambia tu ficha. Para hablar de viva voz, usad un programa de voz aparte.")]

    app.abrir(Menu(app, "Rol", ops, intro="F1 explica cada opción"))


def jugador(p, r):
    """Lo que puedes hacer con otro jugador."""
    app, j, sv = p.app, p.j, p.sv

    def dinero():
        def hecho(n):
            if p.dar_dinero_a(r, n):
                app.cerrar(m)
        _numero(app, f"Cuánto dinero le das a {r.nombre}. Tienes {j.dinero}", hecho, tope=max(1, j.dinero))

    def dar():
        def arma(ident):
            def f():
                if r.mapa != p.mundo.id or r.dist(*p.pos()) > 12:
                    app.son("error")
                    return app.decir(f"Para darle algo en mano, {r.nombre} tiene que estar a tu lado.", True)
                if ident == j.arma:
                    j.arma = "punos"
                del j.armas[ident]
                p.red.enviar({"t": "dar", "a": r.id, "clase": "arma", "id": ident, "n": 1})
                app.cerrar(md)
            return f

        def balas(ident):
            def f():
                def hecho(n):
                    n = min(n, j.armas[ident]["reserva"])
                    if n <= 0 or r.mapa != p.mundo.id or r.dist(*p.pos()) > 12:
                        app.son("error")
                        return app.decir(f"Para darle algo en mano, {r.nombre} tiene que estar a tu lado.", True)
                    j.armas[ident]["reserva"] -= n
                    p.red.enviar({"t": "dar", "a": r.id, "clase": "balas", "id": ident, "n": n})
                    app.cerrar(md)
                _numero(app, f"Cuántas balas de reserva le das. Tienes {j.armas[ident]['reserva']}", hecho, tope=max(1, j.armas[ident]["reserva"]))
            return f

        def objeto(ident):
            def f():
                if j.objetos.get(ident, 0) <= 0 or r.mapa != p.mundo.id or r.dist(*p.pos()) > 12:
                    app.son("error")
                    return app.decir(f"Para darle algo en mano, {r.nombre} tiene que estar a tu lado.", True)
                j.objetos[ident] -= 1
                p.red.enviar({"t": "dar", "a": r.id, "clase": "objeto", "id": ident, "n": 1})
                md.refrescar(False)
            return f

        def lista():
            out = []
            for ident, d in j.armas.items():
                if ident == "punos" or ident not in p.armas_d:
                    continue
                out.append(Opcion(f"El arma: {p.armas_d[ident]['nombre']}", arma(ident)))
                if d.get("reserva", 0) > 0:
                    out.append(Opcion(lambda ident=ident: f"Balas de {p.armas_d[ident]['nombre'].lower()}: tienes {j.armas[ident]['reserva']} de reserva", balas(ident)))
            nombres = {o["id"]: o["nombre"] for o in p.datos["objetos"]}
            for ident, n in j.objetos.items():
                if n > 0 and ident in nombres:
                    out.append(Opcion(lambda ident=ident: f"{nombres[ident]}: tienes {j.objetos.get(ident, 0)}", objeto(ident)))
            return out or [Opcion("No llevas nada que dar")]
        md = Menu(app, f"Qué le das a {r.nombre}. Tiene que estar a tu lado", lista)
        app.abrir(md)

    def ops():
        rel = p.sv_relacion(r)
        out = [Opcion(lambda: p.donde_esta(r) + (f", {rel}" if rel else "") + (", en modo pasivo" if getattr(r, "pasivo", False) else "")
                      + (", en zona segura" if getattr(r, "segura", False) else "")),
               Opcion("Marcarle en el GPS", lambda: (_al_juego(p), p.gps_a_amigo(r)))]
        if p.sv_rol() and not getattr(r, "ia", False):
            out.append(Opcion("Leer su ficha", lambda: p.sv_pedir_ficha(r), ayuda="La frase que ha escrito sobre su personaje."))
        out += [
               Opcion("Mensaje solo para él o ella", lambda: chat(p, "priv", r.id, f"Mensaje privado para {r.nombre}")),
               Opcion("Darle dinero", dinero),
               Opcion("Darle un arma, balas o un objeto", dar, ayuda="En mano: tiene que estar a tu lado.")]
        if sv["info"].get("pvp"):
            out.append(Opcion("Fijarle como objetivo", lambda: (_al_juego(p), setattr(p, "objetivo", r), p.decir(f"Fijado: {p.donde_esta(r)}.", True)),
                              ayuda="Durante el juego, la Q fija a quien te ha atacado, y Mayúsculas Q recorre a todos los que hay cerca, también a los demás jugadores."))
        if sv["banda"] and sv["rango"] in ("jefe", "mano") and getattr(r, "banda", None) is None:
            out.append(Opcion(f"Invitarle a tu banda, {sv['banda']['nombre']}", lambda: p.red.enviar({"t": "banda_invitar", "a": r.id})))
        if sv["grupo"] in (None, p.red.id):
            out.append(Opcion("Invitarle a tu grupo de misión", lambda: p.red.enviar({"t": "grupo_invitar", "a": r.id, "mision": p.mision["def"]["titulo"] if p.mision else ""}),
                              ayuda="En grupo, los enemigos de tus misiones son de todos, no os podéis herir entre vosotros, y quien te ayuda cobra la mitad de la recompensa."))
        return out
    m = Menu(app, f"{r.nombre}", ops)
    app.abrir(m)


def banda(p):
    app, j, sv = p.app, p.j, p.sv
    env = p.red.enviar

    def crear():
        precio = sv["info"].get("precios", {}).get("precio_banda", 2000)

        def hecho(t):
            env({"t": "banda_crear", "nombre": t.strip()[:30]})
            app.cerrar(m)
        app.abrir(EntradaTexto(app, f"Nombre de tu banda. Fundarla cuesta {precio} euros", hecho, maximo=30))

    def miembro(q):
        def f():
            def rango(r):
                return lambda: (env({"t": "banda_rango", "cuenta": q["cuenta"], "rango": r}), app.cerrar(mm))
            mm = Menu(app, f"{q['nombre']}, {q['rango']}", [
                Opcion("Hacerle mano derecha", rango("mano"), ayuda="Puede invitar, sacar de la caja, reclamar barrios y declarar guerras."),
                Opcion("Dejarle de miembro", rango("miembro")),
                Opcion("Cederle el mando de la banda", rango("jefe"), ayuda="Pasa a ser el jefe y tú quedas de mano derecha."),
                Opcion("Echarle de la banda", lambda: (env({"t": "banda_expulsar", "cuenta": q["cuenta"]}), app.cerrar(mm)))])
            app.abrir(mm)
        return f

    def ver_gente():
        b = sv["banda"]
        jefe = sv["rango"] == "jefe"
        nombres = {"jefe": "jefe", "mano": "mano derecha", "miembro": "miembro"}
        app.abrir(Menu(app, f"Gente de {b['nombre']}", lambda: [
            Opcion(f"{q['nombre']}, {nombres.get(q['rango'], q['rango'])}, {'en línea' if q['en_linea'] else 'fuera'}",
                   miembro(q) if jefe and q["cuenta"] != sv.get("cuenta") else None) for q in sv["banda"]["miembros"]] if sv["banda"] else [Opcion("Ya no estás en la banda")]))

    def caja():
        def ops():
            b = sv["banda"]
            if not b:
                return [Opcion("Ya no estás en la banda")]
            out = [Opcion(f"En la caja hay {b['caja']} euros"),
                   Opcion("Ingresar dinero", lambda: _numero(app, f"Cuánto ingresas. Llevas {j.dinero}", lambda n: env({"t": "banda_ingresar", "n": n}), tope=max(1, j.dinero)))]
            if sv["rango"] in ("jefe", "mano"):
                out.append(Opcion("Sacar dinero", lambda: _numero(app, f"Cuánto sacas. Hay {b['caja']}", lambda n: env({"t": "banda_sacar", "n": n}), tope=max(1, b["caja"]))))
            out += [Opcion(f"{a['nombre']}: {'más' if a['cantidad'] >= 0 else 'menos'} {abs(a['cantidad'])} euros, {a['motivo']}") for a in b["apuntes"]]
            return out
        app.abrir(Menu(app, "La caja de la banda", ops, intro="Debajo están los últimos apuntes"))

    def alianza():
        def con(nombre, romper=False):
            return lambda: (env({"t": "alianza", "banda": nombre, "romper": romper}), app.cerrar(ma))
        b = sv["banda"]
        otras = [x for x in sv["bandas"] if x["nombre"] != b["nombre"]]
        ma = Menu(app, "Alianzas", [Opcion(f"Romper la alianza con {n}", con(n, True)) for n in b["aliadas"]]
                  + [Opcion(f"Proponer una alianza a {x['nombre']}", con(x["nombre"])) for x in otras if x["nombre"] not in b["aliadas"]]
                  or [Opcion("No hay más bandas en el servidor")],
                  intro="Una alianza se cierra cuando los dos jefes se la proponen el uno al otro. Los aliados no se pueden herir")
        app.abrir(ma)

    def salir():
        mm = Menu(app, "¿Seguro que dejas la banda?", [Opcion("No", lambda: app.cerrar(mm)), Opcion("Sí, la dejo", lambda: (env({"t": "banda_salir"}), app.cerrar(mm), app.cerrar(m)))])
        app.abrir(mm)

    def disolver():
        mm = Menu(app, "¿Seguro que disuelves la banda? Los barrios quedan libres y la caja te la llevas tú",
                  [Opcion("No", lambda: app.cerrar(mm)), Opcion("Sí, se acabó", lambda: (env({"t": "banda_disolver"}), app.cerrar(mm), app.cerrar(m)))])
        app.abrir(mm)

    def responder(si):
        def f():
            env({"t": "banda_resp", "si": si})
            sv["inv_banda"] = None
            m.refrescar(False)
        return f

    def ops():
        b = sv["banda"]
        pr = sv["info"].get("precios", {})
        if not b:
            out = []
            if sv["inv_banda"]:
                out += [Opcion(f"{sv['inv_banda']['de']} te invita a la banda {sv['inv_banda']['nombre']}: aceptar", responder(True)),
                        Opcion("Rechazar la invitación", responder(False))]
            out += [Opcion("No estás en ninguna banda"),
                    Opcion(f"Fundar una banda: {pr.get('precio_banda', 2000)} euros", crear,
                           ayuda="Eres el jefe. Puedes invitar a otros jugadores, llevar una caja común, quedaros con barrios, que dejan dinero en la caja cada medianoche, y declarar guerras.")]
            return out
        x, y = p.pos()
        try:
            barrio = p.mundo.barrio(x, y)
        except Exception:
            barrio = None
        dueno = p.sv_dueno_barrio(p.mundo.id, barrio["id"]) if barrio else None
        out = [Opcion(f"{b['nombre']}. Eres {({'jefe': 'el jefe', 'mano': 'la mano derecha'}).get(sv['rango'], 'miembro')}. "
                      f"Sois {len(b['miembros'])}, con {len(b['barrios'])} barrios y {b['caja']} euros en la caja"),
               Opcion("La gente de la banda", ver_gente),
               Opcion(f"La caja: {b['caja']} euros", caja),
               Opcion("Mensaje para la banda", lambda: chat(p, "banda", None, "Mensaje para tu banda"))]
        if barrio and sv["rango"] in ("jefe", "mano"):
            nombre_b = barrio.get("nombre", barrio["id"])
            if dueno is None:
                out.append(Opcion(f"Reclamar este barrio, {nombre_b}: {pr.get('precio_barrio', 3000)} euros de la caja", lambda: env({"t": "barrio_reclamar"}),
                                  ayuda=f"No es de nadie. Dejará {pr.get('renta_barrio', 300)} euros en la caja cada medianoche del servidor. Podéis tener un barrio más que miembros sois."))
            elif dueno["banda"] != b["id"]:
                out.append(Opcion(f"Declarar la guerra por {nombre_b}, que es de {dueno['nombre']}: {pr.get('precio_guerra', 1000)} euros de la caja",
                                  lambda: env({"t": "barrio_guerra"}),
                                  ayuda=f"No empieza ya: empieza a los {pr.get('guerra_espera', 20)} minutos, para que a nadie le quiten un barrio mientras duerme, y dura {pr.get('guerra_dura', 10)}. "
                                        "Gana la banda que más gente tenga dentro del barrio y más rivales tumbe. Si empatáis, se lo queda quien lo tenía."))
            else:
                out.append(Opcion(f"Este barrio, {nombre_b}, es vuestro"))
        if sv["rango"] == "jefe":
            out += [Opcion(lambda: f"Fuego amigo dentro de la banda: {'sí' if sv['banda'] and sv['banda']['fuego'] else 'no'}",
                           lambda: env({"t": "banda_fuego", "si": not sv["banda"]["fuego"]}), ayuda="Con no, los de la banda no os podéis herir entre vosotros."),
                    Opcion("Alianzas con otras bandas", lambda: (env({"t": "banda_lista"}), alianza())),
                    Opcion("Disolver la banda", disolver)]
        out.append(Opcion("Dejar la banda", salir))
        return out
    m = Menu(app, "Tu banda", ops)
    app.abrir(m)


def opciones_propiedad(p, l):
    """En un servidor, lo que el dueño puede hacer con su casa o su negocio: venderlo al mercado o a otros jugadores."""
    if not getattr(p, "en_servidor", False) or int(l.get("precio", 0) or 0) <= 0:
        return []
    app = p.app
    pct = 70

    def al_mercado():
        mm = Menu(app, f"¿Vendes {l.nombre} al mercado por {int(l.get('precio', 0)) * pct // 100} euros? Vuelve a estar en venta para cualquiera", [
            Opcion("No", lambda: app.cerrar(mm)),
            Opcion("Sí, vender", lambda: (p.red.enviar({"t": "prop_soltar", "lugar": l.id}), _al_juego(p)))])
        app.abrir(mm)

    def a_jugadores():
        def hecho(t):
            n = int("".join(c for c in t if c.isdigit()) or "0")
            p.red.enviar({"t": "prop_oferta", "lugar": l.id, "precio": n})
            app.decir(f"En venta por {n} euros. Quien lo quiera, lo compra en la puerta." if n else "Retirado de la venta.", True)
        app.abrir(EntradaTexto(app, "Precio para otros jugadores. Cero para no venderlo", hecho, maximo=9))
    return [Opcion(lambda: "En venta para otros jugadores: " + (f"{p.sv_oferta(l)} euros" if p.sv_oferta(l) else "no"), a_jugadores,
                   ayuda="Pones tu precio. Otro jugador lo compra en la puerta y el dinero te llega a ti, estés conectado o no."),
            Opcion(f"Vender al mercado por {int(l.get('precio', 0)) * pct // 100} euros", al_mercado,
                   ayuda="Recuperas una parte de lo que costó y la propiedad vuelve a estar en venta para cualquiera. Saca antes los vehículos del garaje.")]


def en_venta(p):
    """Casas y negocios de esta localidad: los que están libres, los que vende un jugador y de quién es cada uno."""
    app = p.app

    def ops():
        libres, ofertas, ocupados = [], [], []
        for l in p.mundo.lugares.values():
            if l.tipo not in ("casa", "negocio") or int(l.get("precio", 0) or 0) <= 0:
                continue
            ir = (lambda l=l: (_al_juego(p), p.gps_a_lugar(l)))
            que = "Casa" if l.tipo == "casa" else "Negocio"
            d = p.sv["props"].get(l.id)
            if d is None:
                libres.append(Opcion(f"{que} en venta: {l.nombre}, {int(l.get('precio'))} euros" + (f", da {int(l.get('ingresos', 0))} al día" if l.tipo == "negocio" else ""), ir))
            elif d.get("cuenta") == p.sv.get("cuenta"):
                ocupados.append(Opcion(f"{que} tuyo: {l.nombre}", ir))
            elif d.get("oferta"):
                ofertas.append(Opcion(f"{que} que vende {d['nombre']}: {l.nombre}, {d['oferta']} euros", ir))
            else:
                ocupados.append(Opcion(f"{que} de {d['nombre']}: {l.nombre}", ir))
        return (libres + ofertas + ocupados) or [Opcion("En esta localidad no hay casas ni negocios que se puedan comprar")]
    app.abrir(Menu(app, f"Casas y negocios de {p.mundo.nombre}", ops, intro="Primero lo que está en venta. Intro marca el sitio en el GPS"))


def tablon(p):
    """Bandas, barrios y guerras del servidor."""
    app, sv = p.app, p.sv
    p.red.enviar({"t": "banda_lista"})

    def ops():
        out = []
        for g in sv["territorios"].get("guerras", []):
            mapa = p.mapas.get(g["mapa"])
            barrio = next((b.get("nombre", b["id"]) for b in getattr(mapa, "barrios", []) if b["id"] == g["barrio"]), g["barrio"]) if mapa else g["barrio"]
            cuando = f"empieza en {max(1, g.get('falta', 0) // 60)} minutos" if g.get("fase") == "espera" else f"en marcha, {int(g.get('pa', 0))} a {int(g.get('pd', 0))}, quedan {max(1, g.get('queda', 0) // 60)} minutos"
            out.append(Opcion(f"Guerra: {g.get('ataca_n')} contra {g.get('defiende_n')} por {barrio}, en {mapa.nombre if mapa else g['mapa']}: {cuando}"))
        for b in sv["bandas"]:
            out.append(Opcion(f"{b['nombre']}: {b['miembros']} miembros, {b['barrios']} barrios"))
        for t in sv["territorios"].get("barrios", []):
            mapa = p.mapas.get(t["mapa"])
            barrio = next((b.get("nombre", b["id"]) for b in getattr(mapa, "barrios", []) if b["id"] == t["barrio"]), t["barrio"]) if mapa else t["barrio"]
            out.append(Opcion(f"{barrio}, en {mapa.nombre if mapa else t['mapa']}: de {t['nombre']}"))
        return out or [Opcion("Todavía no hay bandas en este servidor")]
    app.abrir(Menu(app, "Bandas, barrios y guerras", ops, intro="Primero las guerras, luego las bandas y luego de quién es cada barrio"))


def grupo(p):
    app, sv = p.app, p.sv

    def responder(si):
        def f():
            p.red.enviar({"t": "grupo_resp", "si": si})
            sv["inv_grupo"] = None
            m.refrescar(False)
        return f

    def ops():
        out = []
        if sv["inv_grupo"]:
            inv = sv["inv_grupo"]
            out += [Opcion(f"{inv['nombre']} te invita a su grupo" + (f" para la misión {inv['mision']}" if inv["mision"] else "") + ": aceptar", responder(True)),
                    Opcion("Rechazar la invitación", responder(False))]
        if sv["grupo"] is None:
            out.append(Opcion("No vas en ningún grupo", ayuda="Para formar uno, abre En línea, Quién hay, elige a alguien e invítale a tu grupo de misión. Caben cuatro."))
        else:
            lider = next((q["nombre"] for q in sv["miembros"] if q["id"] == sv["grupo"]), "alguien")
            out.append(Opcion("Vas en un grupo. Lo lleva " + ("tú" if sv["grupo"] == p.red.id else lider) + ". Sois: " + ", ".join(q["nombre"] for q in sv["miembros"])))
            if sv["mision_grupo"]:
                out.append(Opcion(f"Misión del grupo, {sv['mision_grupo']['titulo']}: {sv['mision_grupo']['texto']}",
                                  lambda: (_al_juego(p), p.gps_a_lugar(p.lugares[sv["mision_grupo"]["lugar"]])) if p.lugares.get(sv["mision_grupo"].get("lugar") or "") else None,
                                  ayuda="Intro marca en el GPS el sitio de la misión."))
            out += [Opcion("Mensaje para el grupo", lambda: chat(p, "grupo", None, "Mensaje para tu grupo")),
                    Opcion("Dejar el grupo" if sv["grupo"] != p.red.id else "Deshacer el grupo", lambda: (p.red.enviar({"t": "grupo_salir"}), app.cerrar(m)))]
        out.append(Opcion("Cómo funcionan las misiones en grupo",
                          ayuda="Quien lleva el grupo empieza una misión suya, de las de siempre. Los demás oís qué pide cada paso y el GPS os lleva al sitio. "
                                "Los enemigos de la misión aparecen también en vuestro juego, y lo que le quitáis a uno se lo quitáis para todos. "
                                "Entre los del grupo no os podéis herir. Al completarla, quien la llevaba cobra su recompensa y cada uno de los demás, la mitad, una vez por misión."))
        return out
    m = Menu(app, "Grupo de misión", ops, intro="F1 explica cada opción")
    app.abrir(m)


def actividades(p):
    """Carrera con apuesta y reparto en equipo: lo mismo que en Jugar con amigos."""
    app = p.app

    def hecho(resultado, salir=False):
        ok, texto = resultado
        if texto:
            app.son("menu_ok" if ok else "error")
            app.decir(texto, True)
        m.refrescar(False)
        if ok and salir:
            _al_juego(p)

    def carrera():
        from . import menus_juego
        menus_juego.lista_lugares(p, al_elegir=lambda l: hecho(p.proponer_carrera(l)), titulo="Destino de la carrera", otras=False)

    def ops():
        out = [Opcion(lambda: p.coop_txt(), ayuda="Además, a pie junto al vehículo parado de otro jugador, Intro te sube de pasajero.")]
        c = p.coop
        if c is None:
            out += [Opcion("Proponer una carrera hasta un lugar: 100 euros de apuesta", carrera, ayuda="Eliges el destino. Quien llega primero se lleva las apuestas."),
                    Opcion("Proponer un reparto en equipo", lambda: hecho(p.proponer_reparto()), ayuda="Cuatro entregas por esta localidad en seis minutos. Si las hacéis entre todos, cobráis todos.")]
        else:
            if c["estado"] == "propuesta" and c["de"] == p.red.id:
                out.append(Opcion("Empezar ya", lambda: hecho(p.empezar_coop(), True)))
            elif c["estado"] == "propuesta" and p.red.id not in c["participantes"]:
                out.append(Opcion("Aceptar y participar", lambda: hecho(p.aceptar_coop())))
            if c["de"] == p.red.id:
                out.append(Opcion("Cancelar la actividad", lambda: (p.cancelar_coop(), m.refrescar(False))))
        return out
    m = Menu(app, "Actividades en común", ops)
    app.abrir(m)


def menu(p):
    """El menú En línea del móvil, cuando la partida es de un servidor."""
    app, sv = p.app, p.sv

    def quien():
        def ops():
            x, y = p.pos()
            gente = sorted(p.remotos.values(), key=lambda r: (r.mapa != p.mundo.id, r.dist(x, y)))
            return [Opcion(lambda r=r: p.donde_esta(r) + (f", {p.sv_relacion(r)}" if p.sv_relacion(r) else "") + (", personaje del servidor" if getattr(r, "ia", False) else ""),
                           lambda r=r: jugador(p, r)) for r in gente] \
                or [Opcion("No hay nadie más en el servidor ahora mismo")]
        app.abrir(Menu(app, "Quién hay", ops, intro="Intro sobre alguien abre lo que puedes hacer con él o con ella"))

    def repasar():
        app.abrir(Menu(app, "Últimos mensajes", [Opcion(t) for t in reversed(p.chat)] or [Opcion("No hay mensajes")]))

    def pasivo():
        p.red.enviar({"t": "pasivo", "si": not sv["pasivo"]})

    def guardar():
        p.sv_guardar(ya=True)
        app.son("guardado")
        app.decir("Personaje guardado en el servidor.", True)

    def salir():
        mm = Menu(app, "¿Sales del servidor? Tu personaje queda guardado", [
            Opcion("No, sigo jugando", lambda: app.cerrar(mm)),
            Opcion("Sí, salir al menú principal", lambda: p.sv_salir(al_menu=True))])
        app.abrir(mm)

    def version_servidor():
        from . import VERSION
        m = sv.get("mundo") or {}
        if not m.get("version"):
            return f"Tu juego es la versión {VERSION}"
        if m.get("igual", True):
            return f"El servidor va con los datos de la versión {m['version']} del juego, los mismos que tienes tú"
        return f"El servidor va con los datos de la versión {m['version']} del juego y tú tienes la {VERSION}: jugáis juntos, cada uno con lo que su versión conoce"

    def info():
        i = sv["info"]
        pr = i.get("precios", {})
        if p.sv_sabe("topes"):
            p.red.enviar({"t": "economia"})                      # cómo vas de margen ahora mismo
        app.abrir(Menu(app, f"Servidor {sv['nombre_servidor']}", [
            Opcion(f"Te llamas {p.red.nombre}" + (". Eres administrador" if sv["admin"] else "")),
            Opcion("La conexión va cifrada" if sv["cifrado"] else "La conexión no va cifrada"),
            Opcion(version_servidor(), ayuda="En un mismo servidor pueden jugar juntos jugadores con versiones distintas del juego. Cada uno ve y usa "
                                             "lo que su versión conoce: lo que solo tiene una versión más nueva no lo ven quienes van con una anterior."),
            Opcion("Caben " + (f"{i.get('max_jugadores')} jugadores a la vez" if i.get("max_jugadores") else "todos los jugadores que entren: no hay límite")),
            Opcion("Combate entre jugadores: " + ("sí" if i.get("pvp") else "no")),
            Opcion("Zonas seguras en hospitales, comisarías, casas y dentro de los locales: " + ("sí" if i.get("seguras") else "no")),
            Opcion("Modo pasivo permitido: " + ("sí" if i.get("pasivo") else "no")),
            Opcion("Contenido para adultos: " + ("sí" if i.get("adultos") else "no")),
            Opcion(f"Al llegar y al reaparecer, {i.get('proteccion', 0)} segundos de protección"),
            Opcion(f"Fundar una banda: {pr.get('precio_banda')} euros. Reclamar un barrio: {pr.get('precio_barrio')}. Declarar una guerra: {pr.get('precio_guerra')}"),
            Opcion(f"Una guerra empieza a los {pr.get('guerra_espera')} minutos de declararla y dura {pr.get('guerra_dura')}"),
            Opcion(f"Ofrecen {sv['recompensa']} euros por tu cabeza" if sv["recompensa"] else "Nadie ofrece nada por tu cabeza"),
            Opcion(lambda: p.sv_economia_txt(),
                   ayuda="En un servidor que lleva la cuenta del dinero, lo que ganas por tu cuenta tiene un tope por hora. No cuentan contra él las misiones de la historia, "
                         "lo que te da el servidor o te dan otros jugadores, ni los encargos repetibles que el servidor reconoce. Lo que pase del tope se retira, y el juego te dice cuánto."),
            Opcion("Canales de rol: " + ((f"sí; lo dicho en personaje llega a {i.get('rol_metros', 30)} metros") if p.sv_rol() else "no")),
            Opcion("Radio de los vehículos de otros jugadores: " + ("sí, la de las emisoras del juego" if p.sv_sabe("radio") and i.get("radio_coches") else "no")),
        ] + ([Opcion("Órdenes de administrador", ayuda="Escríbelas en el chat general con una barra delante: barra ayuda las dice todas. Por ejemplo, barra jugadores, barra aviso y el texto, "
                                                         "barra expulsar y el nombre, barra vetar y el nombre, barra invitar, barra guardar.")] if sv["admin"] else [])))

    def ops():
        out = [Opcion(lambda: f"Estás en {sv['nombre_servidor']}. Hay {sum(1 for r in p.remotos.values() if not getattr(r, 'ia', False))} jugadores además de ti"
                      + (f" y {sum(1 for r in p.remotos.values() if getattr(r, 'ia', False))} personajes del servidor" if any(getattr(r, 'ia', False) for r in p.remotos.values()) else "")
                      + (". Estás en modo pasivo" if sv["pasivo"] else "") + (". Estás en zona segura" if sv["segura"] else "")),
               Opcion("Quién hay", quien, ayuda="Dónde está cada uno y todo lo que puedes hacer con él: marcarle en el GPS, escribirle, darle dinero o cosas, invitarle a tu banda o a tu grupo."),
               Opcion("Mensaje para todos", lambda: chat(p), ayuda="También con F10 durante el juego."),
               Opcion("Mensaje para los que están cerca", lambda: chat(p, "cerca", None, "Mensaje para quien esté a menos de ochenta metros")),
               Opcion("Rol: hablar en personaje, acciones y tu ficha" if p.sv_rol() else "Rol: este servidor no tiene canales de rol", lambda: rol(p),
                      ayuda="Un canal para hablar como tu personaje, que oye quien está cerca; otro para hablar fuera de personaje, que oye todo el servidor; "
                            "una orden para contar lo que hace tu personaje; y una frase de ficha que los demás pueden leer. Depende de que el servidor los tenga."),
               Opcion("Repasar los últimos mensajes", repasar)]
        if sv["inv_banda"] or sv["inv_grupo"]:
            out.insert(1, Opcion("Tienes invitaciones pendientes: están en Tu banda y en Grupo de misión"))
        out += [Opcion(lambda: "Tu banda: " + (sv["banda"]["nombre"] if sv["banda"] else "ninguna"), lambda: banda(p)),
                Opcion("Bandas, barrios y guerras del servidor", lambda: tablon(p)),
                Opcion("Casas y negocios: en venta y de quién son", lambda: en_venta(p),
                       ayuda="En un servidor, cada casa y cada negocio es de un solo jugador. Aquí está lo que queda libre, lo que vende otro jugador a su precio y de quién es lo demás."),
                Opcion(lambda: "Grupo de misión: " + ("sí" if sv["grupo"] is not None else "no"), lambda: grupo(p))]
        if sv["info"].get("pvp") and sv["info"].get("pasivo"):
            out.append(Opcion(lambda: f"Modo pasivo: {'sí' if sv['pasivo'] else 'no'}", pasivo,
                              ayuda="En modo pasivo no puedes herir a otros jugadores ni ellos a ti. No se puede cambiar en mitad de una pelea, ni más de una vez cada dos minutos."))
        out += [Opcion("Actividades en común: carrera y reparto en equipo", lambda: actividades(p)),
                Opcion("Guardar ahora", guardar, ayuda="El personaje se guarda solo cada minuto y al salir. Esto lo guarda ya."),
                Opcion("Datos y reglas de este servidor", info),
                Opcion("Salir del servidor", salir)]
        return out
    app.abrir(Menu(app, "En línea", ops, intro="F1 explica cada opción"))
